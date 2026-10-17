// 场景 dna（170–185 秒）：分子造型的锁链双螺旋。深色空间里，双螺旋从地面生长、缓慢自转，镜头环绕穿行；歌词悬在镜头前。
import * as THREE from 'three';
import { PAL, col, makeGrid, makeStars, glowSprite, smooth } from '../lib.js';
import { makeLyricLayer, makeCyberField } from '../cyber.js';
import { makeDNA } from '../dna.js';

export function create(ctx) {
  const scene = new THREE.Scene(); scene.background = col(0x02000a); scene.fog = new THREE.FogExp2(0x02000a, 0.012);
  const camera = new THREE.PerspectiveCamera(50, 16 / 9, 0.1, 400);
  scene.add(makeStars(1400, 240, 1.3, 61));
  scene.add(new THREE.AmbientLight(0x443355, 1.0));

  const grid = makeGrid({ y: -12, speed: 6, scale: 3, colA: PAL.cyan, colB: PAL.magenta }); grid.material.uniforms.uFog.value = 0.02; scene.add(grid);
  const dna = makeDNA(ctx.env, { height: 36, radius: 6.6, turns: 3.2, links: 240, spin: 0.25, scale: 0.7, wide: true });
  dna.group.position.set(0, -12, 0); scene.add(dna.group);
  const halo = glowSprite('63,246,255', 60, 0.25); halo.position.set(0, 2, -12); scene.add(halo);
  const cf = makeCyberField({ n: 0, codes: 6, box: [60, 30, 200], seed: 88 }); scene.add(cf.group);
  const lyr = makeLyricLayer(ctx, camera, scene, { heroColor: 0xffd6ef, outline: PAL.cyan, heroY: -0.3 });

  function update({ t, f, S, k, post }) {
    dna.update(t, f, smooth(0.0, 0.25, S.p));
    // 镜头绕着双螺旋缓慢升降
    const a = t * 0.16;
    camera.position.set(Math.cos(a) * 34, 6 + Math.sin(t * 0.3) * 6 + f.kick * 0.3, Math.sin(a) * 34);
    camera.lookAt(0, 4, 0);
    camera.fov = 50 + f.kick * 2; camera.updateProjectionMatrix();
    grid.material.uniforms.uTime.value = t; grid.material.uniforms.uCam.value.copy(camera.position); grid.material.uniforms.uPulse.value = f.kick * 0.5;
    halo.material.opacity = 0.18 + f.kick * 0.1;
    cf.update(t, f);
    lyr.update(k, t, f);
    const s = post.s; s.bloom = 0.6 + f.kick * 0.18; s.bloomR = 0.6; s.glitch = Math.max(s.glitch, f.hit * 0.2); s.ab = 0.002 + f.hit * 0.002; s.track = 0.3; s.scan = 0.1;
  }
  return { scene, camera, update };
}
