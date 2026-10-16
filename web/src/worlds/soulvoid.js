// 场景 soulvoid（Outro C，218–226 秒）：数据从虚空深处升起，缠成一根数据柱；"魂"字缩成一个光点消散，画面慢慢退出。
import * as THREE from 'three';
import { PAL, col, JP_FONT, makeGrid, makeStars, textMesh, smooth, lerp } from '../lib.js';
import { makeCableSet, makeCyberField } from '../cyber.js';

export function create(ctx) {
  const scene = new THREE.Scene(); scene.background = col(0x010006);
  const camera = new THREE.PerspectiveCamera(55, 16 / 9, 0.1, 400);
  scene.add(makeStars(1000, 260, 1.2, 99));
  const grid = makeGrid({ y: -8, speed: 4, scale: 3, colA: PAL.cyan, colB: PAL.magenta }); scene.add(grid);
  const cab = makeCableSet(520, ctx.env, { colors: [PAL.cyan, PAL.pink, PAL.yellow] }); scene.add(cab.mesh);
  const cf = makeCyberField({ n: 14, codes: 4, box: [40, 26, 120], seed: 88 }); scene.add(cf.group);
  const soul = textMesh('魂', 3, { size: 260, weight: '900', font: JP_FONT, chrome: true, glow: '#ffd6ef' }, true);
  soul.position.set(0, 2.6, 0); scene.add(soul);

  function update({ t, f, S, post }) {
    const lt = S.lt;
    const rise = smooth(0, 3, lt);
    cab.layout((u) => {
      const a = u * 26 + t * 0.6, rr = 4 + u * 5;
      return new THREE.Vector3(Math.cos(a) * rr, -8 + u * 22, Math.sin(a) * rr - 4);
    }, { frac: rise, scale: 1, twist: t, samples: 600 });
    const sc = Math.max(0.001, lerp(1, 0.02, smooth(3, 7, lt)) * (1 + f.kick * 0.04));
    soul.scale.setScalar(sc); soul.visible = sc > 0.03;
    grid.material.uniforms.uTime.value = t; grid.material.uniforms.uCam.value.copy(camera.position); grid.material.uniforms.uPulse.value = f.kick * 0.4;
    cf.update(t, f);
    camera.position.set(Math.sin(t * 0.25) * 2, 3 + lt * 0.05, 14 + lt * 0.3);
    camera.lookAt(0, 2.6, 0);
    const s = post.s; s.glitch = Math.max(s.glitch, 0.12 * (1 - smooth(4, 8, lt)) + f.hit * 0.2); s.ab = 0.004 + f.hit * 0.006; s.bloom = 0.5 + f.kick * 0.1; s.scan = 0.12; s.track = 0.3;
  }
  return { scene, camera, update };
}
