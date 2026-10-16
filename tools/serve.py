"""启动本地网页服务并打开浏览器播放 MV。双击上一级目录的 play_MV.bat 即可。
用法：python tools/serve.py [端口]      默认从 8800 起找一个空闲端口；支持 Range（音频拖动进度需要）。
打点工具：http://localhost:端口/timing.html
接口：GET /api/timing 读取逐字时间；POST /api/timing 保存（写入 web/data/char_times.json，并备份到 timing/char_times.json）。
"""
import os, sys, re, socket, threading, webbrowser, functools, json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PROJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(PROJ, 'web')
DATA_FILE = os.path.join(ROOT, 'data', 'char_times.json')
BACKUP_FILE = os.path.join(PROJ, 'timing', 'char_times.json')


class H(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json', '.wav': 'audio/wav', '.woff': 'font/woff', '.png': 'image/png'}

    def log_message(self, *a):          # 安静一点
        pass

    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def send_head(self):
        rng = self.headers.get('Range')
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path):
            return super().send_head()
        m = re.match(r'bytes=(\d*)-(\d*)', rng)
        size = os.path.getsize(path)
        if not m:
            return super().send_head()
        a = int(m.group(1)) if m.group(1) else 0
        b = int(m.group(2)) if m.group(2) else size - 1
        b = min(b, size - 1)
        if a > b:
            self.send_error(416); return None
        f = open(path, 'rb'); f.seek(a)
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path))
        self.send_header('Content-Range', f'bytes {a}-{b}/{size}')
        self.send_header('Content-Length', str(b - a + 1))
        self.end_headers()
        self._remain = b - a + 1
        return f

    def copyfile(self, source, outputfile):
        n = getattr(self, '_remain', None)
        if n is None:
            return super().copyfile(source, outputfile)
        while n > 0:
            buf = source.read(min(65536, n))
            if not buf: break
            try: outputfile.write(buf)
            except (BrokenPipeError, ConnectionResetError): break
            n -= len(buf)
        self._remain = None

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split('?')[0] == '/api/timing':
            obj = {'times': {}}
            if os.path.isfile(DATA_FILE):
                with open(DATA_FILE, encoding='utf-8') as f:
                    obj = json.load(f)
            return self._json(200, obj)
        return super().do_GET()

    def do_POST(self):
        if self.path.split('?')[0] == '/api/timing':
            n = int(self.headers.get('Content-Length') or 0)
            try:
                obj = json.loads(self.rfile.read(n).decode('utf-8'))
                assert isinstance(obj.get('times'), dict), 'times 必须是对象'
            except Exception as e:
                return self._json(400, {'ok': False, 'error': str(e)})
            text = json.dumps(obj, ensure_ascii=False, indent=1)
            os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                f.write(text)
            os.makedirs(os.path.dirname(BACKUP_FILE), exist_ok=True)
            with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
                f.write(text)
            return self._json(200, {'ok': True, 'count': len(obj['times'])})
        self.send_error(404)


def free_port(start):
    for p in range(start, start + 40):
        with socket.socket() as s:
            try: s.bind(('127.0.0.1', p)); return p
            except OSError: continue
    raise SystemExit('找不到空闲端口')


if __name__ == '__main__':
    port = free_port(int(sys.argv[1]) if len(sys.argv) > 1 else 8800)
    handler = functools.partial(H, directory=ROOT)
    srv = ThreadingHTTPServer(('127.0.0.1', port), handler)
    url = f'http://localhost:{port}/index.html'
    print('GhostChain MV 服务运行中：', url)
    print('逐字打点工具：', f'http://localhost:{port}/timing.html')
    print('关闭这个窗口即停止服务。')
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
