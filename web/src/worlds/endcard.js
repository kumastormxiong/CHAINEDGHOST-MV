
// 场景 endcard：落版。只有你的头像和「虚空造物」。红蓝光圈为平面光环：不倾斜、不前后翻转，只转动、呼吸缩放与流动光带，全部在头像外侧。拖影为连续的梦幻渐变。
import * as THREE from 'three';
import { PAL, col, JP_FONT, makeStars, makeGrid, glowSprite, textMesh, smooth, clamp } from '../lib.js';

// 平面光圈着色器：圆环形光带（中心半径 uR，宽度 uW）+ 沿圆周流动的光带 + 扫描亮点（加法混合，不写深度）
const ringMat = (c, a, R) => new THREE.ShaderMaterial({
  uniforms: { uT: { value: 0 }, uA: { value: a }, uC: { value: col(c).multiplyScalar(0.85) }, uK: { value: 0 }, uR: { value: R }, uW: { value: 0.09 } },
  vertexShader: 'varying vec2 vP;varying vec3 vW;void main(){vP=position.xy;vW=(modelMatrix*vec4(position,1.0)).xyz;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
  fragmentShader: `uniform float uT,uA,uK,uR,uW;uniform vec3 uC;varying vec2 vP;varying vec3 vW;
    void main(){
      if(length(vW.xy-vec2(0.0,2.6))<3.3) discard;   // 头像范围内不画光圈，只在头像外侧动画
      float d=abs(length(vP)-uR);
      float band=exp(-d*d/(uW*uW*2.0))+0.22*exp(-d*d/0.6);
      float ang=atan(vP.y,vP.x);
      float flow=0.5+0.5*sin(ang*84.0-uT*3.2+sin(ang*9.0+uT)*2.0);
      float spark=smoothstep(0.92,1.0,0.5+0.5*sin(ang*36.0-uT*5.5));
      vec3 c=uC*band*((0.5+0.35*flow)+spark*0.35+uK*0.3);
      gl_FragColor=vec4(c,uA*band*(0.85+0.15*flow));
    }`,
  transparent: true, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false,
});

// 拖影着色器：在光圈内侧拉出一段连续渐变的光带（粉 ↔ 青 沿圆周与时间平滑混合，亮度沿长度渐隐），无分层边界
const trailMat = (c1, c2, a, R, L) => new THREE.ShaderMaterial({
  uniforms: { uT: { value: 0 }, uK: { value: 0 }, uA: { value: a }, uC1: { value: col(c1).multiplyScalar(0.8) }, uC2: { value: col(c2).multiplyScalar(0.8) }, uR: { value: R }, uL: { value: L } },
  vertexShader: 'varying vec2 vP;varying vec3 vW;void main(){vP=position.xy;vW=(modelMatrix*vec4(position,1.0)).xyz;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}',
  fragmentShader: `uniform float uT,uA,uR,uL;uniform vec3 uC1,uC2;varying vec2 vP;varying vec3 vW;
    void main(){
      if(length(vW.xy-vec2(0.0,2.6))<3.3) discard;   // 头像范围内不画
      float d=length(vP)-uR;                            // 负值为光圈内侧
      float x=clamp(-d/uL,0.0,1.0);                     // 0 贴近光圈，1 为拖影末端
      float ang=atan(vP.y,vP.x);
      float inside=step(d,0.0)*(1.0-x)*(1.0-x);
      float edge=exp(-d*d*60.0)*0.6;
      float band=inside+edge;
      float m=0.5+0.5*sin(ang*2.0+uT*0.9+x*3.0);        // 连续的梦幻色相过渡
      vec3 c=mix(uC1,uC2,m)*band*(0.75+0.25*sin(x*9.0-uT*2.0));
      gl_FragColor=vec4(c,uA*band);
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
  // 头像不写深度：光圈从它旁边经过时不会被方形边缘切掉
  const avatar = new THREE.Mesh(new THREE.PlaneGeometry(7.2, 7.2), new THREE.MeshBasicMaterial({ map: ctx.avatarTex, transparent: true, toneMapped: false, color: 0x8c88a8, depthWrite: false })); avatar.position.set(0, 2.6, 0); scene.add(avatar);

  // 平面光圈：与头像同一平面（z=0），只做转动与小幅呼吸缩放；缩放后的内圈始终大于头像圆盘半径
  const RING = { P: { r: 4.05, c: PAL.pink, a: 0.95 }, C: { r: 4.35, c: PAL.cyan, a: 0.6 } };
  const ringState = (kind, tt) => kind === 'P'
    ? { rot: [0, 0, tt * 0.22], sc: 1 + 0.035 * Math.sin(tt * 1.1) }
    : { rot: [0, 0, -tt * 0.26], sc: 1 + 0.03 * Math.sin(tt * 1.3 + 1.7) };
  // 同一套状态函数驱动光圈本体与拖影（拖影按 lag 滞后）
  const place = (m, kind, tt, alpha, kick) => {
    const st = ringState(kind, tt);
    m.rotation.set(st.rot[0], st.rot[1], st.rot[2]);
    m.position.set(0, 2.6, 0);
    m.scale.setScalar(st.sc * (1 + kick * 0.02));
    m.material.uniforms.uT.value = tt; m.material.uniforms.uA.value = alpha; m.material.uniforms.uK.value = kick;
  };
  const ringGeo = new THREE.PlaneGeometry(11.6, 11.6);
  const ringP = new THREE.Mesh(ringGeo, ringMat(RING.P.c, RING.P.a, RING.P.r)); scene.add(ringP);
  const ringC = new THREE.Mesh(ringGeo, ringMat(RING.C.c, RING.C.a, RING.C.r)); scene.add(ringC);
  // 连续梦幻渐变拖影：每个光圈两层，长度与滞后不同，颜色在粉青之间过渡
  const trails = [
    { m: new THREE.Mesh(ringGeo, trailMat(PAL.pink, PAL.cyan, 0.4, RING.P.r, 0.6)), kind: 'P', lag: 0.25, a: 0.4 },
    { m: new THREE.Mesh(ringGeo, trailMat(PAL.pink, PAL.cyan, 0.22, RING.P.r, 0.45)), kind: 'P', lag: 0.6, a: 0.22 },
    { m: new THREE.Mesh(ringGeo, trailMat(PAL.cyan, PAL.pink, 0.3, RING.C.r, 0.7)), kind: 'C', lag: 0.25, a: 0.3 },
    { m: new THREE.Mesh(ringGeo, trailMat(PAL.cyan, PAL.pink, 0.16, RING.C.r, 0.5)), kind: 'C', lag: 0.6, a: 0.16 },
  ];
  trails.forEach((tr) => scene.add(tr.m));
  const name = textMesh('虚空造物', 1.9, { font: JP_FONT, weight: '900', chrome: true, size: 220, glow: '#ff2f8f', stroke: '#ff2f8f', strokeW: 4, spacing: 36 }, false);
  name.position.set(0, -2.7, 0); scene.add(name);
  const nameG = name.clone(); nameG.material = name.material.clone(); nameG.material.blending = THREE.AdditiveBlending; nameG.scale.setScalar(1.012); nameG.position.set(0.05, -2.7, -0.05); scene.add(nameG);
  const veil = new THREE.Mesh(new THREE.PlaneGeometry(14, 8), new THREE.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0, depthTest: false })); veil.position.set(0, 1.4, 14); veil.renderOrder = 99; scene.add(veil);

  function update({ t, f, S, post, sec }) {
    const lt = S.lt, end = sec.end - sec.start;
    const aA = smooth(0.2, 1.8, lt), aN = smooth(1.4, 2.8, lt);
    avatar.material.opacity = aA; avatar.scale.setScalar(0.94 + 0.06 * smooth(0.2, 2.4, lt) + f.kick * 0.012);
    halo.material.opacity = 0.3 * aA + f.kick * 0.06; haloC.material.opacity = 0.18 * aA;
    place(ringP, 'P', t, 0.95 * aA, f.kick);
    place(ringC, 'C', t, 0.6 * aA, f.kick);
    trails.forEach((tr) => place(tr.m, tr.kind, t - tr.lag, tr.a * aA, f.kick));
    name.material.opacity = aN; nameG.material.opacity = aN * 0.3; name.position.y = -2.7 + Math.sin(t * 0.9) * 0.04; nameG.position.y = name.position.y;
    veil.material.opacity = smooth(end - 1.4, end - 0.05, lt);
    grid.material.uniforms.uTime.value = t; grid.material.uniforms.uCam.value.copy(camera.position); grid.material.uniforms.uPulse.value = f.kick * 0.3;
    camera.position.x = Math.sin(t * 0.18) * 0.7; camera.lookAt(0, 0.6, 0);
    const s = post.s; s.bloom = 0.8 + f.kick * 0.15; s.bloomR = 0.7; s.bloomT = 0.75; s.glitch = Math.max(s.glitch, (lt < 2.2 ? (1 - smooth(0.2, 2.2, lt)) * 0.35 : 0) + f.hit * 0.05); s.ab = 0.0022; s.track = 0.25; s.scan = 0.11; s.grain = 0.05;
  }
  return { scene, camera, update };
}
