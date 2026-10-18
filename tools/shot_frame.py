"""渲染 MV 指定时间的一帧并保存 PNG。用法：python tools/shot_frame.py 71.0 out.png"""
import sys
from playwright.sync_api import sync_playwright

t = float(sys.argv[1]) if len(sys.argv) > 1 else 71.0
out = sys.argv[2] if len(sys.argv) > 2 else 'render/shot.png'

with sync_playwright() as p:
    b = p.chromium.launch(args=['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 1280, 'height': 720})
    pg.goto('http://localhost:8801/index.html?w=1280&h=720')
    pg.wait_for_function('window.__ready === true', timeout=120000)
    pg.evaluate(f'() => window.__shot({t})')
    pg.wait_for_timeout(300)
    pg.locator('canvas').first.screenshot(path=out)
    b.close()
print('saved', out)
