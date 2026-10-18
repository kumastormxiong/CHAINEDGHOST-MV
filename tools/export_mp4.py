#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CHAINEDGHOST MV 离线逐帧导出：输出 1920x1080 / 60fps / H.264 + AAC 的 MP4。

原理
- web/src 里的画面只由时间 t 决定（音频特征、歌词时间轴都是预先算好的 JSON），
  不依赖实时播放。所以对每一帧直接调用 window.__shot(t)，t = 帧号 / FPS。
- 同时开 N 个无头 Chrome 进程并行渲染不同的帧（默认 4），每个进程都强制使用独立显卡。
- 渲染好的像素按帧号顺序写入 ffmpeg，帧序和总时长都是精确的（不丢帧、不重复）。
- ffmpeg 优先用 NVIDIA NVENC 硬件编码（同样在独立显卡上完成），没有则退回 libx264。
- 音频直接取 web/audio/GhostChain.wav。

用法（在项目根目录 GhostChain_MV 下运行）：
  python tools\\export_mp4.py                          全曲 -> output\\CHAINEDGHOST_1080p60.mp4
  python tools\\export_mp4.py --start 0 --end 600      只导出前 10 秒（先试跑，检查画面和速度）
  python tools\\export_mp4.py --workers 3              显存或内存紧张时减少并行进程数

依赖：Python 3.10+；pip install playwright；python -m playwright install chromium
      ffmpeg：项目 _bin\\ffmpeg.exe，或 PATH 里的 ffmpeg
"""
import argparse
import base64
import functools
import hashlib
import json
import math
import multiprocessing as mp
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import traceback
from http.server import ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # GhostChain_MV
WEB = os.path.join(ROOT, 'web')
TOOLS = os.path.join(ROOT, 'tools')

# 与 shot.py 一致；--force_high_performance_gpu 让混合显卡笔记本上的 Chrome 使用独立显卡
CHROME_ARGS = [
    '--ignore-gpu-blocklist',
    '--enable-gpu-rasterization',
    '--force_high_performance_gpu',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-background-timer-throttling',
]
if sys.platform == 'win32':
    CHROME_ARGS.append('--use-angle=d3d11')

# 注入页面的函数：渲染第 t 秒并把像素读回（RGBA，OpenGL 原点在左下，编码时用 vflip 翻正）
GRAB_JS = """
window.__grabFrame = (t) => {
  window.__shot(t);
  const c = document.querySelector('canvas');
  const gl = c.getContext('webgl2') || c.getContext('webgl');
  const w = c.width, h = c.height;
  const px = new Uint8Array(w * h * 4);
  gl.readPixels(0, 0, w, h, gl.RGBA, gl.UNSIGNED_BYTE, px);
  let s = '';
  for (let i = 0; i < px.length; i += 0x8000) s += String.fromCharCode.apply(null, px.subarray(i, i + 0x8000));
  return btoa(s);
};
"""


def _worker(wid, cfg, job_q, res_q):
    """一个渲染进程：启动独立 Chrome，接收帧号，返回该帧的 RGBA 字节。"""
    from playwright.sync_api import sync_playwright

    def grab(pg, t):
        return base64.b64decode(pg.evaluate('t => window.__grabFrame(t)', t))

    try:
        with sync_playwright() as p:
            b = p.chromium.launch(channel=cfg['channel'], args=CHROME_ARGS)
            pg = b.new_page(viewport={'width': cfg['W'], 'height': cfg['H']})
            pg.on('pageerror', lambda e: print(f'[渲染进程{wid}] 页面错误: {e}', flush=True))
            pg.goto(f"http://127.0.0.1:{cfg['port']}/index.html?t={cfg['t0']}&w={cfg['W']}&h={cfg['H']}")
            pg.wait_for_function('window.__ready === true', timeout=cfg['timeout'] * 1000)
            pg.evaluate(GRAB_JS)
            res_q.put(('ready', wid, {'gl': str(pg.evaluate('window.__gl')),
                                      'exe': p.chromium.executable_path}))
            grab(pg, cfg['t0'])                       # 预热：纹理、环境贴图等首次使用时才生成
            if cfg['selfcheck'] and wid == 0:         # 自检：同一时刻渲染两次，结果必须一致
                h1 = hashlib.md5(grab(pg, cfg['t0'])).hexdigest()
                grab(pg, cfg['t0'] + 11.37)
                grab(pg, cfg['t0'] + 3.3)
                h2 = hashlib.md5(grab(pg, cfg['t0'])).hexdigest()
                res_q.put(('check', 0, h1 == h2))
            while True:
                idx = job_q.get()
                if idx is None:
                    break
                res_q.put(('frame', idx, grab(pg, idx / cfg['fps'])))
            b.close()
        res_q.put(('done', wid, None))
    except Exception:
        res_q.put(('error', wid, traceback.format_exc()))


def looks_discrete(gl):
    """根据渲染器名字判断是不是独立显卡（NVIDIA / AMD Radeon RX / Intel Arc）。"""
    s = gl.lower()
    if 'swiftshader' in s or 'llvmpipe' in s or 'software' in s:
        return False
    if 'intel' in s and 'arc' not in s:
        return False
    return any(k in s for k in ('nvidia', 'geforce', 'rtx', 'gtx', 'radeon rx', 'amd', 'arc'))


def find_ffmpeg(explicit):
    for c in (explicit, os.path.join(ROOT, '_bin', 'ffmpeg.exe'), os.path.join(ROOT, '_bin', 'ffmpeg'), shutil.which('ffmpeg')):
        if c and os.path.isfile(c):
            return c
    sys.exit('找不到 ffmpeg：请把 ffmpeg.exe 放到 _bin 目录，或用 --ffmpeg 指定路径。')


def pick_encoder(ffmpeg, want):
    if want == 'libx264':
        return 'libx264'
    r = subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
                        'color=c=black:s=640x360:d=0.2', '-frames:v', '2',
                        '-c:v', 'h264_nvenc', '-f', 'null', '-'], capture_output=True)
    ok = r.returncode == 0
    if want == 'nvenc' and not ok:
        sys.exit('当前 ffmpeg 无法使用 NVENC（需要 NVIDIA 独显和较新的驱动）。请改用 --encoder libx264。')
    if ok:
        return 'nvenc'
    print('未检测到可用的 NVENC，改用 libx264（CPU 编码，较慢但画质同样好）。')
    return 'libx264'


def build_ffmpeg_cmd(ffmpeg, kind, a, start, n, wav, out):
    if kind == 'nvenc':
        enc = ['-c:v', 'h264_nvenc', '-preset', 'p6', '-tune', 'hq', '-rc', 'vbr', '-cq', '18',
               '-b:v', a.bitrate, '-maxrate', '40M', '-bufsize', '60M']
    else:
        enc = ['-c:v', 'libx264', '-preset', 'medium', '-crf', str(a.crf)]
    return [ffmpeg, '-hide_banner', '-loglevel', 'warning', '-y',
            '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{a.width}x{a.height}',
            '-framerate', str(a.fps), '-i', 'pipe:0',
            '-ss', f'{start / a.fps:.6f}', '-i', wav,
            '-map', '0:v:0', '-map', '1:a:0',
            '-vf', 'vflip,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p',
            *enc,
            '-profile:v', 'high', '-level', '4.2', '-g', str(2 * a.fps),
            '-r', str(a.fps),
            '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
            '-c:a', 'aac', '-b:a', '320k',
            '-t', f'{n / a.fps:.6f}', '-movflags', '+faststart',
            out]


def main():
    sys.path.insert(0, TOOLS)
    import serve   # 复用 tools/serve.py 的静态服务（已修正 .js 的 MIME，ES 模块需要）

    ap = argparse.ArgumentParser(description='CHAINEDGHOST MV 逐帧导出 MP4（1080p60，多进程并行渲染）')
    ap.add_argument('--width', type=int, default=1920)
    ap.add_argument('--height', type=int, default=1080)
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--duration', type=float, default=None, help='默认读取 web/data/timing.json 的 duration')
    ap.add_argument('--start', type=int, default=0, help='起始帧号（含）')
    ap.add_argument('--end', type=int, default=None, help='结束帧号（不含），默认到全曲末尾')
    ap.add_argument('--workers', type=int, default=4, help='并行渲染的 Chrome 进程数（默认 4）')
    ap.add_argument('--out', default=os.path.join(ROOT, 'output', 'CHAINEDGHOST_1080p60.mp4'))
    ap.add_argument('--encoder', choices=['auto', 'nvenc', 'libx264'], default='auto')
    ap.add_argument('--bitrate', default='25M', help='NVENC 目标码率，默认 25M')
    ap.add_argument('--crf', type=int, default=16, help='libx264 质量，越小越好，默认 16')
    ap.add_argument('--ffmpeg', default=None, help='ffmpeg 路径')
    ap.add_argument('--channel', default='chromium', help='chromium（默认，Playwright 自带）或 chrome（已安装的 Google Chrome）')
    ap.add_argument('--allow-any-gpu', action='store_true', help='不检查渲染器是否为独立显卡（会很慢，仅用于调试）')
    ap.add_argument('--no-selfcheck', action='store_true', help='跳过确定性自检')
    ap.add_argument('--timeout', type=int, default=240, help='页面加载超时（秒）')
    a = ap.parse_args()

    if a.duration is None:
        with open(os.path.join(WEB, 'data', 'timing.json'), encoding='utf-8') as f:
            a.duration = float(json.load(f)['duration'])
    total = math.ceil(round(a.duration * a.fps, 6))
    end = min(a.end if a.end is not None else total, total)
    start = a.start
    if not (0 <= start < end):
        sys.exit(f'帧范围无效：start={start} end={end} 全曲共 {total} 帧')
    n = end - start

    wav = os.path.join(WEB, 'audio', 'GhostChain.wav')
    if not os.path.isfile(wav):
        sys.exit('缺少音频文件：请把歌曲放到 web\\audio\\GhostChain.wav')
    ffmpeg = find_ffmpeg(a.ffmpeg)
    kind = pick_encoder(ffmpeg, a.encoder)
    out = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)

    print(f'导出范围：帧 {start} ~ {end - 1}，共 {n} 帧，约 {n / a.fps:.2f} 秒，{a.width}x{a.height} @ {a.fps}fps')
    print(f'编码器：{kind}    并行进程：{a.workers}    输出：{out}')

    class Server(ThreadingHTTPServer):
        request_queue_size = 128

    srv = Server(('127.0.0.1', 0), functools.partial(serve.H, directory=WEB))
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    ctx = mp.get_context('spawn')
    job_q, res_q = ctx.Queue(), ctx.Queue()
    cfg = dict(port=port, W=a.width, H=a.height, fps=a.fps, t0=start / a.fps,
               channel=a.channel, timeout=a.timeout, selfcheck=not a.no_selfcheck)
    nw = max(1, min(a.workers, n))
    procs = [ctx.Process(target=_worker, args=(i, cfg, job_q, res_q), daemon=True) for i in range(nw)]
    ff = None
    t_begin = time.time()
    try:
        for p_ in procs:
            p_.start()
            time.sleep(0.3)

        def get(timeout):
            try:
                return res_q.get(timeout=timeout)
            except queue.Empty:
                sys.exit('等待渲染进程超时，请检查 Chrome 或 Playwright 是否正常。')

        ready = {}
        early_check = None
        while len(ready) < nw:
            kind_, wid, data = get(a.timeout + 120)
            if kind_ == 'error':
                sys.exit(f'渲染进程 {wid} 启动失败:\n{data}')
            if kind_ == 'ready':
                ready[wid] = data
            elif kind_ == 'check':
                early_check = data
        gl = ready[0]['gl']
        print(f'渲染器：{gl}')
        print(f'Chrome 路径（如需手动设置显卡偏好，请把它加进 Windows 图形设置，选择“高性能”）：\n  {ready[0]["exe"]}')
        if early_check is not None:
            print('确定性自检（同一时刻渲染两次结果一致）：' + ('通过' if early_check else '未通过！并行结果可能不一致，请加 --workers 1 重跑'))
        if not a.allow_any_gpu and not looks_discrete(gl):
            sys.exit('当前渲染器不是独立显卡，已停止。请按 README 设置 Windows 图形偏好，或加 --allow-any-gpu 强行继续（会非常慢）。')

        ff = subprocess.Popen(build_ffmpeg_cmd(ffmpeg, kind, a, start, n, wav, out), stdin=subprocess.PIPE)

        window = max(8, nw * 6)          # 同时在途的帧数上限，控制内存
        sub, written, pending = start, start, {}
        for _ in range(min(window, n)):
            job_q.put(sub)
            sub += 1

        t0 = time.time()
        last = t0
        while written < end:
            k, x, data = get(a.timeout + 300)
            if k == 'frame':
                pending[x] = data
            elif k == 'check':
                print('确定性自检（同一时刻渲染两次结果一致）：' + ('通过' if data else '未通过！并行结果可能不一致，请加 --workers 1 重跑'))
            elif k == 'error':
                sys.exit(f'渲染进程 {x} 出错:\n{data}')
            while written in pending:
                chunk = pending.pop(written)
                try:
                    ff.stdin.write(chunk)
                except OSError:
                    sys.exit('ffmpeg 提前退出，请看上面的 ffmpeg 输出。')
                written += 1
                if sub < end:
                    job_q.put(sub)
                    sub += 1
            now = time.time()
            if now - last >= 3 or written == end:
                last = now
                done = written - start
                rate = done / max(now - t0, 1e-6)
                eta = (end - written) / rate if rate > 0 else 0
                print(f'\r进度 {done}/{n} 帧  {rate:5.1f} 帧/秒  预计剩余 {eta / 60:4.1f} 分钟    ', end='', flush=True)
        print()

        ff.stdin.close()
        rc = ff.wait()
        if rc != 0:
            sys.exit(f'ffmpeg 返回错误码 {rc}')
        for _ in range(nw):
            job_q.put(None)
    finally:
        for p_ in procs:
            if p_.is_alive():
                p_.terminate()
        if ff is not None and ff.poll() is None:
            ff.kill()
        srv.shutdown()

    size_mb = os.path.getsize(out) / 1e6
    print(f'完成：{out}（{size_mb:.1f} MB），用时 {(time.time() - t_begin) / 60:.1f} 分钟')
    info = subprocess.run([ffmpeg, '-hide_banner', '-i', out], capture_output=True, text=True,
                          encoding='utf-8', errors='replace')
    for line in info.stderr.splitlines():
        if 'Duration' in line or 'Stream #' in line:
            print('  ' + line.strip())


if __name__ == '__main__':
    mp.freeze_support()
    main()
