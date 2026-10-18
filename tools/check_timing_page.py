"""逐字打点页面自检：有无 JS 报错、播放时高亮数量、打点是否前进、单次打点耗时。测试时屏蔽 POST，不改动打点文件。"""
import sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8801/timing.html'

with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
    pg = b.new_page()
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('console', lambda m: errors.append('console: ' + m.text) if m.type == 'error' else None)
    pg.route('**/api/timing', lambda r: r.continue_() if r.request.method == 'GET' else r.abort())
    pg.goto(URL)
    pg.wait_for_selector('.ch')
    print('字数:', pg.evaluate("() => document.querySelectorAll('.ch').length"))
    pg.evaluate("() => { const a = document.getElementById('au'); a.currentTime = 45; a.play(); }")
    pg.wait_for_timeout(1500)
    print('播放中高亮数量(应为 1):', pg.evaluate("() => document.querySelectorAll('.ch.play').length"))
    print('高亮字:', pg.evaluate("() => (document.querySelector('.ch.play') || {}).textContent"))
    print('正在播放提示:', pg.evaluate("() => document.getElementById('now').textContent"))
    before = pg.evaluate("() => document.getElementById('cur').textContent")
    ts = pg.evaluate("""() => { const out = []; for (let i = 0; i < 40; i++) {
        const t0 = performance.now();
        window.dispatchEvent(new KeyboardEvent('keydown', { code: 'Enter' }));
        document.body.offsetHeight; out.push(performance.now() - t0); } return out; }""")
    print('打点后光标:', before[:6], '->', pg.evaluate("() => document.getElementById('cur').textContent")[:6])
    print('已打点(应为 40 的增量):', pg.evaluate("() => document.querySelectorAll('.ch.done').length"))
    print('单次打点最大耗时 ms:', round(max(ts), 2), ' 平均:', round(sum(ts) / len(ts), 2))
    print('撤销后已打点:', end=' ')
    pg.evaluate("() => window.dispatchEvent(new KeyboardEvent('keydown', { code: 'Backspace' }))")
    print(pg.evaluate("() => document.querySelectorAll('.ch.done').length"))
    print('JS 错误:', errors if errors else '无')
    b.close()
