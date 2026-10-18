"""渲染 MV 指定时间的一帧（单帧模式），用 canvas.toDataURL 直接保存 PNG，避免元素截图超时。
用法：python tools/shot_canvas.py 71.2 render/break1/now_71.png [宽] [高]"""
import base64, io, os, sys
from playwright.sync_api import sync_playwright

t = float(sys.argv[1]) if len(sys.argv) > 1 else 71.0
out = sys.argv[2] if len(sys.argv) > 2 else 'render/shot.png'
W = int(sys.argv[3]) if len(sys.argv) > 3 else 1280
H = int(sys.argv[4]) if len(sys.argv) > 4 else 720
os.makedirs(os.path.dirname(out) or '.', exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': W, 'height': H})
    pg.goto(f'http://localhost:8801/index.html?w={W}&h={H}&t={t}', timeout=300000)
    pg.wait_for_function('window.__ready === true', timeout=300000)
    data = pg.evaluate("() => document.querySelector('#stage canvas').toDataURL('image/png')")
    with io.open(out, 'wb') as f:
        f.write(base64.b64decode(data.split(',', 1)[1]))
    b.close()
print('saved', out)
