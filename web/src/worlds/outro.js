// 场景 outro（157–200 秒）：数据雨越下越密，歌词假名在镜头前逐个点亮，电路网格在脚下延伸，数据线像柱子一样升起。
// 之后的 200–226 秒由 soul / flash / soulvoid 三个场景接手（魂字与锁链都在那里）。
import * as THREE from 'three';
import { PAL, col, KANA, JP_FONT, makeGrid, makeStars, hash, smooth, lerp } from '../lib.js';
import { makeChain } from '../lib.js';
import { makeLyricLayer, makeCyberField } from '../cyber.js';

const RW = 1280, RH = 720, CW = 18, CH = 20, NC = Math.floor(RW / CW), TAIL = 16;

export function create(ctx) {
  const scene = new THREE.Scene(); scene.background = col(0x03000a);
  const camera = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 400);
  scene.add(makeStars(1200, 260, 1.4, 40)); scene.add(new THREE.AmbientLight(0x553355, 0.8));

  const rcv = document.createElement('canvas'); rcv.width = RW; rcv.height = RH; const rg = rcv.getContext('2d');
  const rtex = new THREE.CanvasTexture(rcv); rtex.colorSpace = THREE.SRGBColorSpace;
  const rain = new THREE.Mesh(new THREE.PlaneGeometry(89.5, 50.4), new THREE.MeshBasicMaterial({ map: rtex, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  rain.position.z = -40; scene.add(rain);
  function drawRain(t, inten) {
    rg.clearRect(0, 0, RW, RH); rg.font = `700 ${CH - 3}px ${JP_FONT}`; rg.textAlign = 'center'; rg.textBaseline = 'middle';
    for (let c = 0; c < NC; c++) {
      if (hash(c * 1.7) > inten) continue;
      const sp = 0.45 + hash(c * 3.1) * 0.9, head = ((t * sp * 11 + hash(c * 5.3) * (RH + TAIL * CH))) % (RH + TAIL * CH);
      const warm = hash(c * 9.7) > 0.5;
      for (let r = 0; r < TAIL; r++) {
        const y = head - r * CH; if (y < -CH || y > RH + CH) continue;
        const a = Math.pow(1 - r / TAIL, 1.6) * (r === 0 ? 1 : 0.8);
        const ch = KANA[Math.floor(hash(c * 13.1 + r * 7.7 + Math.floor(t * 5 + c % 5) * 1.3) * KANA.length)];
        rg.fillStyle = r === 0 ? `rgba(255,255,255,${a})` : warm ? `rgba(255,70,160,${a * 0.9})` : `rgba(70,240,255,${a * 0.9})`;
        rg.fillText(ch, c * CW + CW / 2, y);
      }
    }
    rtex.needsUpdate = true;
  }

  const grid = makeGrid({ y: -9, speed: 8, scale: 3, colA: PAL.magenta, colB: PAL.cyan }); grid.material.uniforms.uFog.value = 0.02; scene.add(grid);
  const strands = makeChain(240, ctx.env); strands.mesh.frustumCulled = false; scene.add(strands.mesh);
  const cf = makeCyberField({ n: 18, codes: 6, box: [45, 30, 160], seed: 61 }); scene.add(cf.group);
  const eyesF = ctx.makeEyeField([
    { pos: [-24, 10, -26], w: 12, iris: 'blue', line: 'pink' }, { pos: [24, 15, -30], w: 13, iris: 'red', line: 'cyan' }, { pos: [-9, 17, -34], w: 11, iris: 'ring_cyan', line: 'pink' },
    { pos: [-27, -2, -24], w: 10, iris: 'orange', line: 'cyan' }, { pos: [8, 20, -38], w: 15, iris: 'ring_pink', line: 'cyan' }
  ]); scene.add(eyesF.group);
  const lyr = makeLyricLayer(ctx, camera, scene, { heroColor: 0xffd6ef, outline: PAL.cyan });

  function update({ t, f, S, k, post }) {
    const lt = S.lt;
    drawRain(t, lerp(0.25, 1.0, smooth(0, 28, lt)));
    rain.material.opacity = 0.6 + f.kick * 0.2;
    strands.layout((u) => {
      const a = u * Math.PI * 6 + t * 0.4;
      return new THREE.Vector3(Math.cos(a) * (7 + 3 * Math.sin(u * 9 + t)), -9 + u * 26, -18 + Math.sin(a) * 6);
    }, { frac: smooth(0, 6, lt), scale: 1, twist: t * 0.3, samples: 500 });
    grid.material.uniforms.uTime.value = t; grid.material.uniforms.uCam.value.copy(camera.position); grid.material.uniforms.uPulse.value = f.kick * 0.5;
    cf.update(t, f);
    eyesF.update(t, camera, { opacity: 0.85, appear: smooth(0, 10, lt), kick: f.kick });
    lyr.update(k, t, f);
    camera.position.set(Math.sin(t * 0.2) * 2.2, 3.6 + Math.sin(t * 0.33) * 0.4, 18 - smooth(0, 42, lt) * 4);
    camera.lookAt(0, 2.4, 0);
    const s = post.s; s.bloom = 0.3 + f.kick * 0.08; s.glitch = Math.max(s.glitch, f.hit * 0.2); s.ab = 0.0015 + f.hit * 0.002; s.track = 0.4; s.scan = 0.13;
  }
  return { scene, camera, update };
}
