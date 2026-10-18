"""逐字打点页面的性能测试：模拟连续按 Enter 打点，统计每次打点的耗时，并看内存和帧间隔是否随时间变差。
用法：python tools/perf_timing_test.py http://localhost:8801/timing.html
测试时屏蔽了 POST /api/timing，不会改动你的打点文件。
"""
import sys, statistics
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8801/timing.html'

TAP_JS = """(n) => {
  const out = [];
  for (let i = 0; i < n; i++) {
    const t0 = performance.now();
    window.dispatchEvent(new KeyboardEvent('keydown', { code: 'Enter' }));
    document.body.offsetHeight;            // 强制完成样式与布局，计入耗时
    out.push(performance.now() - t0);
  }
  return out;
}"""

FRAME_JS = """() => new Promise((res) => {
  const gaps = []; let last = performance.now(); let n = 0;
  function f() { const now = performance.now(); gaps.push(now - last); last = now; if (++n < 120) requestAnimationFrame(f); else res(gaps); }
  requestAnimationFrame(f);
})"""

HEAP_JS = "() => (performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1e6) : -1)"


def summary(xs):
    xs = sorted(xs)
    return f"median {statistics.median(xs):7.2f} ms   p90 {xs[int(len(xs) * 0.9)]:7.2f} ms   max {xs[-1]:7.2f} ms"


with sync_playwright() as p:
    b = p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required', '--enable-precise-memory-info'])
    pg = b.new_page()

    def only_get(route):
        if route.request.method == 'GET':
            route.continue_()
        else:
            route.abort()          # 测试期间不保存

    pg.route('**/api/timing', only_get)
    pg.goto(URL)
    pg.wait_for_selector('.ch')
    pg.evaluate("() => document.getElementById('au').play()")
    pg.wait_for_timeout(800)

    print('== 每次打点耗时（每 50 次一组）==')
    for batch in range(6):
        ts = pg.evaluate(TAP_JS, 50)
        print(f"第 {batch + 1} 组  {summary(ts)}   堆内存 {pg.evaluate(HEAP_JS)} MB")

    print('== 页面帧间隔（播放中，约 2 秒）==')
    gaps = pg.evaluate(FRAME_JS)
    print(summary(gaps))
    b.close()
