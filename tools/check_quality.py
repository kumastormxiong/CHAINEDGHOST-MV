"""画质切换自检：有无报错、三档下画布分辨率、切换后能否继续渲染。结果写入 tools/quality_check.txt。"""
import io, os
from playwright.sync_api import sync_playwright

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'quality_check.txt')
lines = []
def log(*a):
    lines.append(' '.join(str(x) for x in a))
    with io.open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'])
    pg = b.new_page(viewport={'width': 1280, 'height': 720})
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('console', lambda m: errors.append('console: ' + m.text) if m.type == 'error' else None)
    pg.goto('http://localhost:8801/index.html')
    pg.wait_for_selector('#quality', state='attached', timeout=180000)
    pg.wait_for_timeout(3000)
    for q in ['high', 'medium', 'low', 'high']:
        pg.select_option('#quality', q)
        pg.wait_for_timeout(2500)
        size = pg.evaluate("() => { const c = document.querySelector('#stage canvas'); return c ? [c.width, c.height] : null; }")
        log('画质', q, '画布分辨率', size, '错误数', len(errors))
    log('JS 错误:', errors if errors else '无')
    b.close()
log('done')
