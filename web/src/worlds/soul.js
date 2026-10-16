// 场景 soul（Outro A，200–210 秒）：黑色虚空里，"魂"字随鼓点剧烈震动、红蓝错位；
// 一根锁链从一条开始，慢慢绕着它缠成好几层。这是唯一保留真锁链的地方。
import * as THREE from 'three';
import { PAL, col, JP_FONT, makeChain, makeGrid, makeStars, textMesh, smooth, lerp } from '../lib.js';
import { makeCyberField } from '../cyber.js';

const ROUNDS = [200.826, 203.634, 206.18, 208.422];

export function create(ctx) {
  const scene = new THREE.Scene(); scene.background = col(0x02000a); scene.fog = new THREE.FogExp2(0x02000a, 0.02);
  const camera = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 400);
  scene.add(makeStars(1200, 260, 1.3, 40)); scene.add(new THREE.AmbientLight(0x553355, 0.8));
  const cf = makeCyberField({ n: 16, codes: 6, box: [50, 30, 160], seed: 14 }); scene.add(cf.group);
  const grid = makeGrid({ y: -7, speed: 6, scale: 3, colA: PAL.magenta, colB: PAL.cyan }); grid.material.uniforms.uFog.value = 0.02; scene.add(grid);

  const O = { size: 300, weight: '900', font: JP_FONT };
  const main = textMesh('魂', 7, { ...O, chrome: true, glow: '#ff4fd8' }, false);
  const cy = textMesh('魂', 7, { ...O, fill: '#3ff6ff' }, true); cy.material.opacity = 0.35; cy.position.z = -0.1;
  const pk = textMesh('魂', 7, { ...O, fill: '#ff2f8f' }, true); pk.material.opacity = 0.35; pk.position.z = -0.2;
  const soul = new THREE.Group(); soul.add(pk, cy, main); soul.position.set(0, 2.6, 0); scene.add(soul);

  const chain = makeChain(300, ctx.env); chain.mesh.frustumCulled = false; chain.mesh.count = 0; scene.add(chain.mesh);


  function update({ t, f, sec, post }) {
    const rounds = sec.rounds || ROUNDS, t0 = sec.start;
    let imp = 0; for (const r of rounds) if (t >= r) imp = Math.max(imp, Math.exp(-(t - r) * 3.2));
    const A = 0.04 + imp * 0.5 + smooth(t0, t0 + 8, t) * 0.1 + f.hit * 0.05;
    const jx = (Math.sin(t * 47.3) + 0.5 * Math.sin(t * 23.7 + 1.1)) * A;
    const jy = (Math.cos(t * 41.1) + 0.5 * Math.sin(t * 29.9)) * A;
    soul.position.set(jx, 2.6 + jy, 0); soul.scale.setScalar(1 + imp * 0.08 + f.kick * 0.03);
    pk.position.x = -0.12 - imp * 0.1; cy.position.x = 0.12 + imp * 0.1;

    // 锁链：202 秒开始从一条线慢慢变成螺旋，圈数逐步增加到约六层
    const prog = smooth(202, 210, t);
    if (t >= 202) {
      const N = lerp(0.6, 6, prog);
      chain.layout((u) => {
        const th = u * Math.PI * 2 * N + t * 0.4;
        return new THREE.Vector3(Math.cos(th) * 6.2, 2.6 + lerp(-4.6, 4.6, u), Math.sin(th) * 6.2);
      }, { frac: lerp(0.02, 1, prog), scale: 1.0, twist: t * 0.3, samples: 600 });
    } else chain.mesh.count = 0;

    camera.position.set(Math.sin(t * 0.3) * 0.8, 2.2 + Math.sin(t * 0.5) * 0.2, 16 - prog * 1.5);
    camera.lookAt(0, 2.6, 0);
    grid.material.uniforms.uTime.value = t; grid.material.uniforms.uCam.value.copy(camera.position); grid.material.uniforms.uPulse.value = f.kick * 0.5 + imp * 0.5;
    cf.update(t, f);
    const s = post.s; s.glitch = Math.max(s.glitch, 0.12 + imp * 0.5 + f.hit * 0.3); s.ab = 0.004 + imp * 0.012; s.bloom = 0.32 + imp * 0.2 + f.kick * 0.08; s.scan = 0.15; s.track = 0.5; s.bloomT = 0.6;
  }
  return { scene, camera, update };
}
