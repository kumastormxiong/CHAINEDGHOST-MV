// 场景 endcard：落版。只有你的头像和「虚空造物」。
import * as THREE from 'three';
import { PAL, col, JP_FONT, makeStars, makeGrid, glowSprite, textMesh, smooth, clamp } from '../lib.js';

export function create(ctx) {
  const scene = new THREE.Scene(); scene.background = col(0x03000a);
  const camera = new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 300); camera.position.set(0, 1.4, 17);
  scene.add(makeStars(1400, 240, 1.4, 99));
  const grid = makeGrid({ y: -6.5, speed: 3, scale: 3, colA: PAL.magenta, colB: PAL.cyan }); grid.material.uniforms.uFog.value = 0.035; scene.add(grid);
  const hz = glowSprite('255,47,143', 120, 0.3); hz.scale.set(1.8, 0.2, 1); hz.position.set(0, -5.2, -40); scene.add(hz);

  const halo = glowSprite('255,70,170', 20, 0.55); halo.position.set(0, 2.6, -1); scene.add(halo);
  const haloC = glowSprite('63,246,255', 15, 0.3); haloC.position.set(1.2, 2.2, -1.2); scene.add(haloC);
  const avatar = new THREE.Mesh(new THREE.PlaneGeometry(7.2, 7.2), new THREE.MeshBasicMaterial({ map: ctx.avatarTex, transparent: true, toneMapped: false, color: 0x8c88a8 })); avatar.position.set(0, 2.6, 0); scene.add(avatar);
  const mkRing = (r, c, o) => { const m = new THREE.Mesh(new THREE.TorusGeometry(r, 0.035, 8, 200), new THREE.MeshBasicMaterial({ color: c, transparent: true, opacity: o, blending: THREE.AdditiveBlending, toneMapped: false })); m.position.copy(avatar.position); scene.add(m); return m; };
  const ringP = mkRing(4.05, PAL.pink, 0.9), ringC = mkRing(4.35, PAL.cyan, 0.55);
  const name = textMesh('虚空造物', 1.9, { font: JP_FONT, weight: '900', chrome: true, size: 220, glow: '#ff2f8f', stroke: '#ff2f8f', strokeW: 4, spacing: 36 }, false);
  name.position.set(0, -2.7, 0); scene.add(name);
  const nameG = name.clone(); nameG.material = name.material.clone(); nameG.material.blending = THREE.AdditiveBlending; nameG.scale.setScalar(1.012); nameG.position.set(0.05, -2.7, -0.05); scene.add(nameG);
  const veil = new THREE.Mesh(new THREE.PlaneGeometry(14, 8), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0, depthTest: false })); veil.position.set(0, 1.4, 14); veil.renderOrder = 99; scene.add(veil);

  function update({ t, f, S, post, sec }) {
    const lt = S.lt, end = sec.end - sec.start;
    const aA = smooth(0.2, 1.8, lt), aN = smooth(1.4, 2.8, lt);
    avatar.material.opacity = aA; avatar.scale.setScalar(0.94 + 0.06 * smooth(0.2, 2.4, lt) + f.kick * 0.012);
    halo.material.opacity = 0.3 * aA + f.kick * 0.06; haloC.material.opacity = 0.18 * aA;
    ringP.material.opacity = 0.9 * aA; ringC.material.opacity = 0.55 * aA; ringP.rotation.set(Math.sin(t * 0.5) * 0.12, 0, t * 0.2); ringC.rotation.set(0, Math.sin(t * 0.4) * 0.15, -t * 0.15);
    ringP.scale.setScalar(1 + f.kick * 0.015);
    name.material.opacity = aN; nameG.material.opacity = aN * 0.3; name.position.y = -2.7 + Math.sin(t * 0.9) * 0.04; nameG.position.y = name.position.y;
    veil.material.opacity = smooth(end - 1.4, end - 0.05, lt);
    grid.material.uniforms.uTime.value = t; grid.material.uniforms.uCam.value.copy(camera.position); grid.material.uniforms.uPulse.value = f.kick * 0.3;
    camera.position.x = Math.sin(t * 0.18) * 0.7; camera.lookAt(0, 0.6, 0);
    const s = post.s; s.bloom = 0.5 + f.kick * 0.08; s.bloomT = 0.75; s.glitch = Math.max(s.glitch, (lt < 2.2 ? (1 - smooth(0.2, 2.2, lt)) * 0.35 : 0) + f.hit * 0.05); s.ab = 0.0022; s.track = 0.25; s.scan = 0.11; s.grain = 0.05;
  }
  return { scene, camera, update };
}
