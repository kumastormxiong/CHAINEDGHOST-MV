"""给实时播放加入画质档位（高 / 中 / 低）。只改 web/ 下三个文件，每处替换都要求唯一匹配。"""
import io, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'web')

def patch(path, pairs):
    with io.open(path, 'r', encoding='utf-8') as f:
        s = f.read()
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, f'{os.path.basename(path)}: match count {n} for {old[:50]!r}'
        s = s.replace(old, new)
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(s)
    print('patched', os.path.basename(path))

# ---------- post.js：createPost 整段替换为可重建的后期管线 ----------
POST_PATH = os.path.join(ROOT, 'src', 'post.js')
with io.open(POST_PATH, 'r', encoding='utf-8') as f:
    src = f.read()
idx = src.index('export function createPost')
NEW_POST = '''// 画质档位：高 = 原画；中 = 0.75 倍分辨率、2x 抗锯齿；低 = 半分辨率、无抗锯齿、关闭泛光（优先保证帧率）
export const QUALITY = {
  high:   { scale: 1.0,  samples: 4, bloom: true,  name: '高' },
  medium: { scale: 0.75, samples: 2, bloom: true,  name: '中' },
  low:    { scale: 0.5,  samples: 0, bloom: false, name: '低' }
};

export function createPost(renderer, W, H, quality = 'high') {
  let composer = null, rp = null, bloom = null, fx = null;
  // 切换画质时重建后期管线（分辨率、抗锯齿、泛光）；场景本身不变
  function build(name) {
    const q = QUALITY[name] || QUALITY.high;
    if (composer) { composer.renderTarget1.dispose(); composer.renderTarget2.dispose(); bloom.dispose(); fx.dispose && fx.dispose(); }
    const w = Math.max(2, Math.round(W * q.scale)), h = Math.max(2, Math.round(H * q.scale));
    const rt = new THREE.WebGLRenderTarget(w, h, { type: THREE.HalfFloatType, samples: q.samples });
    composer = new EffectComposer(renderer, rt); composer.setSize(w, h);
    rp = new RenderPass(new THREE.Scene(), new THREE.PerspectiveCamera());
    bloom = new UnrealBloomPass(new THREE.Vector2(w, h), 0.9, 0.55, 0.12); bloom.enabled = q.bloom;
    fx = new ShaderPass(FX); fx.uniforms.uRes.value.set(w, h);
    composer.addPass(rp); composer.addPass(bloom); composer.addPass(fx); composer.addPass(new OutputPass());
    renderer.setSize(w, h, false);
    Object.assign(post, { quality: name, composer, bloom, fx });
  }
  const post = {
    quality: 'high', composer: null, bloom: null, fx: null,
    // 每帧由场景写入的状态（reset() 恢复默认）
    s: {},
    reset() {
      this.s = { bloom: 0.6, bloomR: 0.45, bloomT: 0.6, ab: 0.0022, glitch: 0, scan: 0.1, grain: 0.04, vig: 0.4, flash: [0, 0, 0], track: 0, warp: 0, pix: 0 };
    },
    setQuality(name) { if (QUALITY[name] && name !== this.quality) build(name); },
    render(scene, camera, t) {
      const s = this.s; rp.scene = scene; rp.camera = camera;
      if (bloom.enabled) { bloom.strength = s.bloom; bloom.radius = s.bloomR; bloom.threshold = s.bloomT; }
      const u = fx.uniforms; u.uTime.value = t; u.uAb.value = s.ab; u.uGlitch.value = s.glitch; u.uScan.value = s.scan; u.uGrain.value = s.grain;
      u.uVig.value = s.vig; u.uFlash.value.setRGB(s.flash[0], s.flash[1], s.flash[2]); u.uTrack.value = s.track; u.uWarp.value = s.warp; u.uPix.value = s.pix;
      composer.render();
    }
  };
  build(quality);
  post.reset();
  return post;
}
'''
with io.open(POST_PATH, 'w', encoding='utf-8', newline='\n') as f:
    f.write(src[:idx] + NEW_POST)
print('patched post.js')

# ---------- main.js：读取画质设置，接入下拉框 ----------
patch(os.path.join(ROOT, 'src', 'main.js'), [
    ("import { createPost } from './post.js';",
     "import { createPost, QUALITY } from './post.js';"),
    ("const post = createPost(renderer, W, H);",
     "const savedQ = (() => { try { return localStorage.getItem('ghostchain_quality'); } catch (e) { return null; } })();\n"
     "const post = createPost(renderer, W, H, STILL ? 'high' : (QUALITY[savedQ] ? savedQ : 'high'));   // 单帧出片永远用高画质"),
    ("$('bHud').onclick = () => { hud = !hud; ui.classList.add('hide'); };",
     "$('bHud').onclick = () => { hud = !hud; ui.classList.add('hide'); };\n"
     "  const qSel = $('quality'); qSel.value = post.quality;\n"
     "  qSel.onchange = () => { post.setQuality(qSel.value); try { localStorage.setItem('ghostchain_quality', qSel.value); } catch (e) {} };"),
])

# ---------- index.html：控制栏加入画质下拉框 ----------
patch(os.path.join(ROOT, 'index.html'), [
    ('  <button id="bHud">HUD</button>',
     '  <button id="bHud">HUD</button>\n'
     '  <label>画质 <select id="quality" title="低画质优先保证帧率；录制请用高">'
     '<option value="high">高</option><option value="medium">中</option><option value="low">低</option></select></label>'),
    ('  #info{opacity:.75;font-variant-numeric:tabular-nums}',
     '  #info{opacity:.75;font-variant-numeric:tabular-nums}\n'
     '  #ui select{background:#150826;color:#8ff;border:1px solid #3ff6ff88;border-radius:3px;padding:3px 6px}'),
])
print('done')
