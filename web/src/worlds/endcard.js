// 场景 endcard：落版。只有你的头像和「虚空造物」。红蓝光圈为三维着色器光环：倾斜翻转、前后起伏、呼吸缩放、流动光带。
import * as THREE from 'three';
import { PAL, col, JP_FONT, makeStars, makeGrid, glowSprite, textMesh, smooth, clamp } from '../lib.js';

// 三维光圈着色器：边缘菲涅尔发光 + 沿圆周流动的光带 + 扫描亮点（加法混合，不写深度）
const ringMat = (c, a) => new THREE.ShaderMaterial({
  uniforms: { uT: { value: 0 }, uA: { value: a }, uC: { value: col(c).multiplyScalar(1.5) }, uK: { value: 0 } },
  vertexShader: 'varying vec2 vUv;varying vec3 vN;void main(){vUv=uv;vN=normalize(normalMatrix*normal);gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
  fragmentShader: `uniform float uT,uA,uK;uniform vec3 uC;varying vec2 vUv;varying vec3 vN;
    void main(){
      float fres=pow(clamp(1.0-abs(vN.z),0.0,1.0),1.5);
      float flow=0.5+0.5*sin(vUv.x*84.0-uT*3.2+sin(vUv.x*9.0+uT)*2.0);
      float spark=smoothstep(0.92,1.0,0.5+0.5*sin(vUv.x*36.0-uT*5.5));
      vec3 c=uC*((0.5+0.5*fres)*(0.55+0.45*flow)+spark*0.9+uK*0.7);
      gl_FragColor=vec4(c,uA*(0.3+0.7*fres)*(0.85+0.15*flow));
    }`,
  transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false,
});

export function create(ctx) {
  const scene = new THREE.Scene(); scene.background = col(0x03000a);
  const camera = new THREE.PerspectiveCamera(45, 16 / 9, 0.1, 300); camera.position.set(0, 1.4, 17);
  scene.add(makeStars(1400, 240, 1.4, 99));
  const grid = makeGrid({ y: -6.5, speed: 3, scale: 3, colA: PAL.magenta, colB: PAL.cyan }); grid.material.uniforms.uFog.value = 0.035; scene.add(grid);
  const hz = glowSprite('255,47,143', 120, 0.3); hz.scale.set(1.8, 0.2, 1); hz.position.set(0, -5.2, -40); scene.add(hz);

  const halo = glowSprite('255,70,170', 20, 0.55); halo.position.set(0, 2.6, -1); scene.add(halo);
  const haloC = glowSprite('63,246,255', 15, 0.3); haloC.position.set(1.2, 2.2, -1.2); scene.add(haloC);
  // 头像不写深度：光圈从它前后穿过时不会被方形边缘切掉
  const avatar = new THREE.Mesh(new THREE.PlaneGeometry(7.2, 7.2), new THREE.MeshBasicMaterial({ map: ctx.avatarTex, transparent: true, toneMapped: false, color: 0x8c88a8, depthWrite: false })); avatar.position.set(0, 2.6, 0); scene.add(avatar);

  // 三维光圈：各自倾角、转动、前后起伏、呼吸缩放
  const RING = { P: { r: 4.05, c: PAL.pink, a: 0.95 }, C: { r: 4.35, c: PAL.cyan, a: 0.6 } };
  const ringState = (kind, tt) => kind === 'P'
    ? { rot: [0.3 + Math.sin(tt * 0.5) * 0.4, Math.sin(tt * 0.37) * 0.6, tt * 0.22], sc: 1 + 0.07 * Math.sin(tt * 1.1), z: Math.sin(tt * 0.7) * 0.55 }
    : { rot: [-0.35 + Math.sin(tt * 0.42) * 0.35, tt * 0.26, Math.sin(tt * 0.5) * 0.25], sc: 1 + 0.06 * Math.sin(tt * 1.3 + 1.7), z: -Math.sin(tt * 0.7) * 0.55 };
  // 同一套状态函数驱动光圈本体与拖影（拖影按 lag 滞后、按 shrink 收小）
  const place = (m, kind, tt, lag, shrink, alpha, kick) => {
    const tl = tt - lag, st = ringState(kind, tl);
    m.rotation.set(st.rot[0], st.rot[1], st.rot[2]);
    m.position.set(0, 2.6, st.z);
    m.scale.setScalar(st.sc * (1 + kick * 0.02) * (1 - shrink));
    m.material.uniforms.uT.value = tl; m.material.uniforms.uA.value = alpha; m.material.uniforms.uK.value = kick;
  };
  const ringP = new THREE.Mesh(new THREE.TorusGeometry(RING.P.r, 0.09, 14, 240), ringMat(RING.P.c, RING.P.a)); scene.add(ringP);
  const ringC = new THREE.Mesh(new THREE.TorusGeometry(RING.C.r, 0.09, 14, 240), ringMat(RING.C.c, RING.C.a)); scene.add(ringC);
  // 拖影：几层渐淡的副本，共用几何体
  const trails = [];
  [['P', ringP], ['C', ringC]].forEach(([kind, src]) => {
    for (let i = 1; i <= 4; i++) {
      const m = new THREE.Mesh(src.geometry, ringMat(RING[kind].c, 0.3 / i)); scene.add(m); trails.push({ m, kind, i });
    }
  });
  const name = textMesh('虚空造物', 1.9, { font: JP_FONT, weight: '900', chrome: true, size: 220, glow: '#ff2f8f', stroke: '#ff2f8f', strokeW: 4, spacing: 36 }, false);
  name.position.set(0, -2.7, 0); scene.add(name);
  const nameG = name.clone(); nameG.material = name.material.clone(); nameG.material.blending = THREE.AdditiveBlending; nameG.scale.setScalar(1.012); nameG.position.set(0.05, -2.7, -0.05); scene.add(nameG);
  const veil = new THREE.Mesh(new THREE.PlaneGeometry(14, 8), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0, depthTest: false })); veil.position.set(0, 1.4, 14); veil.renderOrder = 99; scene.add(veil);

  function update({ t, f, S, post, sec }) {
    const lt = S.lt, end = sec.end - sec.start;
    const aA = smooth(0.2, 1.8, lt), aN = smooth(1.4, 2.8, lt);
    avatar.material.opacity = aA; avatar.scale.setScalar(0.94 + 0.06 * smooth(0.2, 2.4, lt) + f.kick * 0.012);
    halo.material.opacity = 0.3 * aA + f.kick * 0.06; haloC.material.opacity = 0.18 * aA;
    place(ringP, 'P', t, 0, 0, 0.95 * aA, f.kick);
    place(ringC, 'C', t, 0, 0, 0.6 * aA, f.kick);
    trails.forEach(({ m, kind, i }) => place(m, kind, t, i * 0.08, i * 0.012, (kind === 'P' ? 0.3 : 0.2) / i * aA, f.kick));
    name.material.opacity = aN; nameG.material.opacity = aN * 0.3; name.position.y = -2.7 + Math.sin(t * 0.9) * 0.04; nameG.position.y = name.position.y;
    veil.material.opacity = smooth(end - 1.4, end - 0.05, lt);
    grid.material.uniforms.uTime.value = t; grid.material.uniforms.uCam.value.copy(camera.position); grid.material.uniforms.uPulse.value = f.kick * 0.3;
    camera.position.x = Math.sin(t * 0.18) * 0.7; camera.lookAt(0, 0.6, 0);
    const s = post.s; s.bloom = 0.8 + f.kick * 0.15; s.bloomR = 0.7; s.bloomT = 0.75; s.glitch = Math.max(s.glitch, (lt < 2.2 ? (1 - smooth(0.2, 2.2, lt)) * 0.35 : 0) + f.hit * 0.05); s.ab = 0.0022; s.track = 0.25; s.scan = 0.11; s.grain = 0.05;
  }
  return { scene, camera, update };
}
