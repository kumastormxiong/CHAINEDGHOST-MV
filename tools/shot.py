"""网页单帧截图工具：在无头 Chromium 里打开 web/index.html?t=秒 并保存 PNG。
用法：
  python tools/shot.py --times 6,28,52 --out render/samples [--prefix s] [--size 1920x1080]
也可作为"逐帧离线渲染"的基础：每帧调用 window.__shot(t) 再截图。
"""
import argparse, os, sys, threading, http.server, socketserver, functools, json
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('--times', required=True)
ap.add_argument('--out', default=os.path.join(ROOT, 'render', 'samples'))
ap.add_argument('--prefix', default='t')
ap.add_argument('--size', default='1920x1080')
ap.add_argument('--port', type=int, default=8765)
ap.add_argument('--gpu', default='d3d11', help='d3d11 / swiftshader')
ap.add_argument('--timeout', type=int, default=120)
ap.add_argument('--q', default='', help='额外 URL 参数，如 hide=ghost,chain')
a = ap.parse_args()
W, H = map(int, a.size.lower().split('x'))
times = [float(x) for x in a.times.split(',')]
os.makedirs(a.out, exist_ok=True)

Handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=os.path.join(ROOT, 'web'))
Handler.log_message = lambda *args, **kw: None
class Quiet(socketserver.ThreadingTCPServer):
    allow_reuse_address = False
srv = Quiet(('127.0.0.1', 0), Handler)      # 0 = 系统分配空闲端口（避免撞到你机器上已有的服务）
a.port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

args = ['--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--enable-unsafe-swiftshader']
if a.gpu == 'd3d11':
    args += ['--use-angle=d3d11']
with sync_playwright() as p:
    b = p.chromium.launch(args=args)
    pg = b.new_page(viewport={'width': W, 'height': H})
    logs = []
    pg.on('console', lambda m: logs.append(f'[{m.type}] {m.text}') if m.type in ('error', 'warning') else None)
    pg.on('pageerror', lambda e: logs.append(f'[pageerror] {e}'))
    url = f'http://127.0.0.1:{a.port}/index.html?t={times[0]}&w={W}&h={H}' + ('&' + a.q if a.q else '')
    pg.goto(url)
    try:
        pg.wait_for_function('window.__ready === true', timeout=a.timeout * 1000)
    except Exception as e:
        print('NOT READY', str(e)[:80]); print('GL:', pg.evaluate('window.__gl')); print('\n'.join(logs[:30]))
        pg.screenshot(path=os.path.join(a.out, 'debug_fail.png')); b.close(); sys.exit(1)
    print('GL:', pg.evaluate('window.__gl'))
    for t in times:
        pg.evaluate('t => window.__shot(t)', t)
        pg.evaluate('t => window.__shot(t)', t)
        fn = os.path.join(a.out, f'{a.prefix}_{t:07.2f}.png')
        pg.locator('canvas').screenshot(path=fn)
        print('saved', fn)
    if logs:
        print('--- console'); print('\n'.join(logs[:40]))
    b.close()
srv.shutdown()
