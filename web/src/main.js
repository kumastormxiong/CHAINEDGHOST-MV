import * as THREE from 'three';
import { loadFonts, makeAtlas, KANA, makeEnv } from './lib.js';
import { Features } from './features.js';
import { Timeline } from './timeline.js';
import { createPost } from './post.js';
import { createWorlds } from './worlds/index.js';
import { loadEyeTextures, makeEyeField } from './eyes.js';

const q = new URLSearchParams(location.search);
const W = +q.get('w') || 1920, H = +q.get('h') || 1080;
const STILL = q.has('t');
document.body.classList.toggle('still', STILL);
const $ = (id) => document.getElementById(id);

const renderer = new THREE.WebGLRenderer({ antialias: false, powerPreference: 'high-performance', preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H, false); renderer.setClearColor(0x06010d);
renderer.toneMapping = THREE.NoToneMapping;
$('stage').appendChild(renderer.domElement);
{ const gl = renderer.getContext(), e = gl.getExtension('WEBGL_debug_renderer_info'); window.__gl = e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : 'unknown'; }

await loadFonts();
const [feat, tl] = await Promise.all([Features.load('./data/features.json'), Timeline.load()]);
const loader = new THREE.TextureLoader();
const ld = (u) => new Promise((res) => loader.load(u, (t) => { t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; res(t); }));
const [ghostTex, avatarTex, girlTex, eyeT] = await Promise.all([ld('assets/avatar_ghost.png'), ld('assets/avatar_full.png'), ld('assets/girl_ghost.png'), loadEyeTextures()]);
const ctx = {
  renderer, W, H, THREE, ghostTex, avatarTex, girlTex, eyeT, tl, feat,
  makeEyeField: (specs) => makeEyeField(eyeT, specs),
  env: makeEnv(renderer),
  atlasF: makeAtlas(KANA, 'filled'), atlasO: makeAtlas(KANA, 'outline')
};
const post = createPost(renderer, W, H);
const worlds = createWorlds(ctx);

function frame(t) {
  const f = feat.at(t), S = tl.at(t), k = tl.kana(t);
  const w = worlds[S.sec.world] || worlds.void;
  post.reset();
  w.update({ t, f, S, k, tl, post, sec: S.sec, ctx });
  if (S.lt < 0.3 && S.index > 0) post.s.glitch = Math.max(post.s.glitch, 1 - S.lt / 0.3);   // 段落切换：硬切 + 故障冲击
  post.render(w.scene, w.camera, t);
  return S;
}

// ---------- 单帧模式（出样片 / 逐帧渲染都走这里）----------
window.__shot = (t) => { frame(t); return true; };
if (STILL) {
  const t0 = parseFloat(q.get('t')) || 0;
  frame(t0); frame(t0);
  window.__ready = true;
} else {
  initPlayer();
}

// ---------- 实时播放 + 录制 ----------
function initPlayer() {
  const audio = new Audio('audio/GhostChain.wav'); audio.preload = 'auto';
  let hud = true, tapMode = false, taps = [], rec = null;
  const seek = $('seek'), info = $('info'), ui = $('ui');
  seek.max = tl.duration;
  const fmt = (t) => `${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}`;
  tl.sections.forEach((s) => {
    const b = document.createElement('button'); b.textContent = `${s.name} ${s.start}s`;
    b.onclick = () => { audio.currentTime = s.start; }; $('secs').appendChild(b);
  });
  let frames = 0, last = performance.now(), fps = 0, idle = 0;
  function loop() {
    requestAnimationFrame(loop);
    const t = audio.currentTime || 0; const S = frame(t);
    seek.value = t; frames++; const now = performance.now();
    if (now - last > 500) { fps = frames * 1000 / (now - last); frames = 0; last = now; }
    info.textContent = `${fmt(t)} / ${fmt(tl.duration)}  ${S.sec.name}  ${fps.toFixed(0)}fps${rec ? '  ● REC' : ''}`;
    if (++idle > 240 && !ui.matches(':hover')) ui.classList.add('hide');
  }
  loop();
  const toggle = () => { audio.paused ? audio.play() : audio.pause(); };
  $('start').onclick = () => { $('start').remove(); audio.play(); ui.classList.remove('hide'); };
  $('bPlay').onclick = toggle; $('bHud').onclick = () => { hud = !hud; ui.classList.add('hide'); };
  seek.oninput = () => { audio.currentTime = +seek.value; };
  addEventListener('mousemove', () => { idle = 0; ui.classList.remove('hide'); });
  $('bTap').onclick = () => { tapMode = !tapMode; taps = []; $('bTap').textContent = tapMode ? '打点中：播放时按 Enter 标记下一段起点' : '打点模式'; };
  addEventListener('keydown', (e) => {
    if (e.code === 'Space') { e.preventDefault(); toggle(); }
    else if (e.code === 'ArrowRight') audio.currentTime += 5; else if (e.code === 'ArrowLeft') audio.currentTime -= 5;
    else if (e.code === 'KeyR') $('bRec').click();
    else if (e.code === 'Enter' && tapMode) {
      taps.push(+audio.currentTime.toFixed(2)); console.log('段落起点', taps.length, taps[taps.length - 1]);
      if (taps.length === tl.sections.length) { const out = tl.sections.map((s, i) => ({ id: s.id, start: taps[i] })); navigator.clipboard?.writeText(JSON.stringify(out)); alert('已复制各段起点 JSON，发给 Claude 或粘贴进 timing.json\n' + JSON.stringify(out)); }
    }
  });
  // 录制：把画布 + 音频一起录成 mp4（Chrome 支持时）或 webm
  $('bRec').onclick = async () => {
    if (rec) { rec.stop(); return; }
    const stream = renderer.domElement.captureStream(60);
    const ac = new (window.AudioContext || window.webkitAudioContext)();
    if (!audio._src) { audio._src = ac.createMediaElementSource(audio); audio._dst = ac.createMediaStreamDestination(); audio._src.connect(audio._dst); audio._src.connect(ac.destination); }
    audio._dst.stream.getAudioTracks().forEach((tr) => stream.addTrack(tr));
    const types = ['video/mp4;codecs=avc1.640033,mp4a.40.2', 'video/mp4', 'video/webm;codecs=vp9,opus', 'video/webm'];
    const mime = types.find((m) => MediaRecorder.isTypeSupported(m));
    const chunks = [];
    rec = new MediaRecorder(stream, { mimeType: mime, videoBitsPerSecond: 45e6, audioBitsPerSecond: 320e3 });
    rec.ondataavailable = (e) => e.data.size && chunks.push(e.data);
    rec.onstop = () => {
      const blob = new Blob(chunks, { type: mime }); const a = document.createElement('a');
      a.href = URL.createObjectURL(blob); a.download = 'CHAINEDGHOST_recorded' + (mime.includes('mp4') ? '.mp4' : '.webm'); a.click(); rec = null;
    };
    audio.pause(); audio.currentTime = 0; await new Promise((r) => setTimeout(r, 300));
    rec.start(1000); audio.play(); audio.onended = () => rec && rec.stop();
  };
  window.__audio = audio;
}
