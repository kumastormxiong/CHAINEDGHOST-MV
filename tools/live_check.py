"""Headless live-playback check: console errors + FPS while the audio plays and sections are seeked."""
import os, sys, threading, time, functools
from http.server import ThreadingHTTPServer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import serve
from playwright.sync_api import sync_playwright

H = functools.partial(serve.H, directory=serve.ROOT)
srv = ThreadingHTTPServer(('127.0.0.1', 8899), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()

errs = []
with sync_playwright() as p:
    b = p.chromium.launch(args=['--ignore-gpu-blocklist', '--enable-gpu-rasterization', '--use-angle=d3d11', '--autoplay-policy=no-user-gesture-required'])
    pg = b.new_page(viewport={'width': 1280, 'height': 720})
    pg.on('console', lambda m: errs.append(f'[{m.type}] {m.text}') if m.type in ('error', 'warning') else None)
    pg.on('pageerror', lambda e: errs.append('[pageerror] ' + str(e)))
    pg.goto('http://127.0.0.1:8899/index.html')
    try:
        pg.wait_for_function('!!window.__audio', timeout=25000)
    except Exception as ex:
        print('NOT READY'); print('\n'.join(errs[:20]))
        pg.screenshot(path='render/live_notready.png'); print(pg.evaluate('document.body.innerText.slice(0,300)')); b.close(); srv.shutdown(); sys.exit(1)
    print('gl:', pg.evaluate('window.__gl'))
    pg.mouse.click(640, 360)
    pg.evaluate('window.__n=0; (function c(){window.__n++; requestAnimationFrame(c)})()')
    time.sleep(1)
    for target in (5, 30, 60, 90, 110, 140, 160, 205, 230):
        pg.evaluate(f'window.__audio.currentTime={target}')
        pg.evaluate('window.__n=0')
        time.sleep(4)
        n = pg.evaluate('window.__n'); t = pg.evaluate('window.__audio.currentTime'); paused = pg.evaluate('window.__audio.paused')
        print(f'seek {target:>3}: t={t:.1f} paused={paused} fps~{n/4:.0f}')
    b.close()
print('ERRORS:', len(errs))
for e in errs[:20]:
    print(e)
srv.shutdown()
