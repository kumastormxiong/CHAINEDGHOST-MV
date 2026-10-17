// 场景 tunnel：Chorus 2。数据隧道：由数据包环和假名环组成，向镜头飞来（已放慢），尽头是白热的门；歌词悬在镜头前。
import * as THREE from 'three';
import { PAL, col, glyphMesh, glyphGeo, glowSprite, makeStars, smooth, clamp, rng } from '../lib.js';
import { makeChain } from '../lib.js';
import { makeLyricLayer } from '../cyber.js';

export function create(ctx) {
  const scene = new THREE.Scene(); scene.background = col(0x04000a); scene.fog = new THREE.Fog(0x7a0f55, 20, 190);
  const camera = new THREE.PerspectiveCamera(72, 16 / 9, 0.1, 400);
  scene.add(new THREE.AmbientLight(0x664466, 0.8));

  const NR = 26, SP = 9, LEN = NR * SP, RAD = 8.2;
  const rings = [];
  for (let i = 0; i < NR; i++) {
    const g = new THREE.Group();
    const c = makeChain(72, ctx.env);
    c.layout((u) => { const a = u * Math.PI * 2; return new THREE.Vector3(Math.cos(a) * RAD, Math.sin(a) * RAD, 0); }, { frac: 1, scale: 1.1, samples: 240 });
    g.add(c.mesh);
    const glyphs = [];
    if (i % 2 === 0) for (let j = 0; j < 14; j++) {
      const a = (j / 14) * Math.PI * 2, m = glyphMesh(ctx.atlasF, 'ア', i % 4 === 0 ? PAL.pink : PAL.cyan, 2.1, 0.95);
      m.position.set(Math.cos(a) * (RAD + 3.2), Math.sin(a) * (RAD + 3.2), 0); m.rotation.z = a - Math.PI / 2; g.add(m); glyphs.push(m);
    }
    const ring = new THREE.Mesh(new THREE.TorusGeometry(RAD + 1.6, 0.04, 6, 120), new THREE.MeshBasicMaterial({ color: i % 2 ? PAL.cyan : PAL.magenta, transparent: true, opacity: 0.75, blending: THREE.AdditiveBlending, toneMapped: false }));
    g.add(ring);
    scene.add(g); rings.push({ g, glyphs, i, ring });
  }

  // 速度线
  const R = rng(12), LN = 520, lp = new Float32Array(LN * 6), la = new Float32Array(LN * 2), lc = new Float32Array(LN * 6);
  for (let i = 0; i < LN; i++) {
    const a = R() * Math.PI * 2, r = 3 + R() * 20, x = Math.cos(a) * r, y = Math.sin(a) * r, z = -R() * 220;
    lp.set([x, y, z, x, y, z], i * 6); la[i * 2] = 0; la[i * 2 + 1] = 1;
    const cc = R() < 0.5 ? [1, 0.2, 0.6] : R() < 0.5 ? [0.2, 0.95, 1] : [1, 1, 1]; lc.set([...cc, ...cc], i * 6);
  }
  const lg = new THREE.BufferGeometry(); lg.setAttribute('position', new THREE.BufferAttribute(lp, 3)); lg.setAttribute('aEnd', new THREE.BufferAttribute(la, 1)); lg.setAttribute('color', new THREE.BufferAttribute(lc, 3));
  const lines = new THREE.LineSegments(lg, new THREE.ShaderMaterial({
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, vertexColors: true, uniforms: { uT: { value: 0 }, uSpeed: { value: 60 }, uLen: { value: 6 } },
    vertexShader: 'attribute float aEnd;uniform float uT,uSpeed,uLen;varying vec3 vC;varying float vA;void main(){vec3 p=position;p.z=mod(p.z+uT*uSpeed,220.0)-210.0+aEnd*uLen;vC=color;vA=1.0-aEnd*0.9;gl_Position=projectionMatrix*modelViewMatrix*vec4(p,1.0);}',
    fragmentShader: 'varying vec3 vC;varying float vA;void main(){gl_FragColor=vec4(vC,0.55*vA);}'
  })); lines.frustumCulled = false; scene.add(lines);

  // 尽头的门
  const portal = glowSprite('255,235,235', 90, 1); portal.position.set(0, 0, -205); scene.add(portal);
  const portal2 = glowSprite('255,70,150', 220, 0.8); portal2.position.set(0, 0, -208); scene.add(portal2);
  scene.add(makeStars(600, 220, 1.2, 3).translateZ(-100));
  const lyr = makeLyricLayer(ctx, camera, scene, { heroColor: 0xffd6ef, outline: PAL.cyan, heroY: -0.3, hold: true, disperseAt: 125 });

  const geoC = {}; const getG = (ch) => geoC[ch] || (geoC[ch] = glyphGeo(ctx.atlasF, ch, 2.1, 2.1));
  const SPEED = 24;   // 原来是 42，放慢到约一半
  function update({ t, f, S, k, post, sec }) {
    const flat = k.flat.length ? k.flat : ['ア'];
    const dist = t * SPEED, off = dist % LEN;
    rings.forEach((r) => {
      const z = -(((r.i * SP) - off + LEN) % LEN) + 6;
      const lap = Math.floor((dist - r.i * SP + 6) / LEN);
      r.g.position.z = z;
      r.g.rotation.z = t * (r.i % 2 ? 0.35 : -0.28) + r.i * 0.5;
      const near = clamp(1 - Math.abs(z + 12) / 40);
      r.ring.material.opacity = 0.35 + 0.55 * f.kick * near + 0.2;
      r.glyphs.forEach((m, j) => {
        const ch = flat[Math.abs((lap * NR + r.i) * 14 + j) % flat.length]; if (ch in ctx.atlasF.idx) m.geometry = getG(ch);
      });
    });
    lines.material.uniforms.uT.value = t; lines.material.uniforms.uSpeed.value = SPEED * 1.8; lines.material.uniforms.uLen.value = 5 + f.low * 8;
    portal.material.opacity = 0.8 + f.kick * 0.2; portal.scale.setScalar(1 + f.kick * 0.1 + Math.sin(t * 3) * 0.03);
    lyr.update(k, t, f);
    if (sec && sec.mode === 'apex') {
      // 副歌 3：镜头在锁链之间左右晃动、向前穿行
      camera.position.set(Math.sin(t * 0.9) * 3.0, Math.cos(t * 0.7) * 2.2, 4 + Math.sin(t * 0.5) * 2);
      camera.lookAt(Math.sin(t * 0.9 + 1.2) * 2.2, Math.cos(t * 0.7 + 0.6) * 1.6, -50);
      camera.rotation.z += Math.sin(t * 1.1) * 0.16 + f.kick * 0.02;
    } else {
      camera.position.set(Math.sin(t * 0.4) * 0.6, Math.cos(t * 0.3) * 0.5, 4);
      camera.lookAt(0, 0, -50); camera.rotation.z = Math.sin(t * 0.45) * 0.12 + f.kick * 0.02;
    }
    camera.fov = 72 + f.kick * 7; camera.updateProjectionMatrix();
    const s = post.s; s.bloom = 1.0 + f.kick * 0.4; s.bloomR = 0.6; s.glitch = Math.max(s.glitch, f.hit * 0.38); s.ab = 0.0045 + f.hit * 0.003 + f.kick * 0.0015; s.warp = 0.1; s.track = 0.2;
    s.flash = [f.kick * 0.05, f.kick * 0.015, f.kick * 0.04];
  }
  return { scene, camera, update };
}
