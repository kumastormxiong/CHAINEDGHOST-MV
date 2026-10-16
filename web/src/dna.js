// 锁链双螺旋（DNA 式结构）：两根真锁链互相缠绕成双螺旋。每一圈的宽度都不一样，
// 并且有一道收缩/扩散的波从下往上传。另外用着色器画流动的光点，用横档表示碱基对。
// 不含任何区块链符号或文字。
import * as THREE from 'three';
import { makeChain, lerp, clamp } from './lib.js';

const turnWidth = (i) => 0.78 + 0.28 * Math.sin(i * 2.37 + 0.8);   // 每一圈的基础宽度各不相同

export function makeDNA(env, { height = 14, radius = 3.4, turns = 2.5, links = 110, spin = 0.5, scale = 0.6, rungs = 18, glowN = 700 } = {}) {
  const A = makeChain(links, env), B = makeChain(links, env);
  A.mesh.frustumCulled = false; B.mesh.frustumCulled = false;
  const group = new THREE.Group(); group.add(A.mesh, B.mesh);

  // 螺旋上一点的位置：半径随圈数变化，并且随时间收缩、扩散
  const point = (u, phase, t, out) => {
    const turnF = u * turns, turn = Math.floor(turnF);
    const breathe = 1 + 0.16 * Math.sin(t * 1.4 - u * 7.0 + turn * 0.9);
    const r = radius * turnWidth(turn) * breathe;
    const a = turnF * Math.PI * 2 + phase + t * spin;
    return (out || new THREE.Vector3()).set(Math.cos(a) * r, lerp(0, height, u), Math.sin(a) * r);
  };

  // 流动光点：沿两根螺旋各布一串点，着色器里做亮度脉冲从下往上传
  const NG = glowN;
  const gpos = new Float32Array(NG * 2 * 3), gu = new Float32Array(NG * 2), gs = new Float32Array(NG * 2);
  for (let i = 0; i < NG; i++) for (let s = 0; s < 2; s++) { const k = i * 2 + s; gu[k] = i / (NG - 1); gs[k] = s; }
  const gGeo = new THREE.BufferGeometry();
  const gPosAttr = new THREE.BufferAttribute(gpos, 3);
  gGeo.setAttribute('position', gPosAttr);
  gGeo.setAttribute('aU', new THREE.BufferAttribute(gu, 1));
  gGeo.setAttribute('aS', new THREE.BufferAttribute(gs, 1));
  const gMat = new THREE.ShaderMaterial({
    uniforms: { uT: { value: 0 }, uP: { value: 1 }, uSize: { value: 70 } },
    transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
    vertexShader: `attribute float aU; attribute float aS; uniform float uT; uniform float uP; uniform float uSize; varying float vA; varying float vS;
      void main(){
        vec4 mv = modelViewMatrix * vec4(position, 1.0);
        float pulse = 0.5 + 0.5 * sin(uT * 3.0 - aU * 16.0 + aS * 3.1416);
        float on = step(aU, uP);
        gl_PointSize = on * (6.0 + 9.0 * pulse) * (uSize / -mv.z);
        vA = (0.3 + 0.7 * pulse) * on; vS = aS;
        gl_Position = projectionMatrix * mv;
      }`,
    fragmentShader: `varying float vA; varying float vS;
      void main(){
        float d = length(gl_PointCoord - 0.5);
        float a = smoothstep(0.5, 0.0, d); a *= a;
        vec3 c = mix(vec3(1.0, 0.3, 0.7), vec3(0.3, 0.95, 1.0), vS);
        gl_FragColor = vec4(c * a * vA * 1.8, a * vA);
      }`
  });
  const glow = new THREE.Points(gGeo, gMat); glow.frustumCulled = false; group.add(glow);

  // 碱基对横档：两根螺旋之间的连线
  const rPos = new Float32Array(rungs * 2 * 3);
  const rAttr = new THREE.BufferAttribute(rPos, 3);
  const rGeo = new THREE.BufferGeometry(); rGeo.setAttribute('position', rAttr);
  const rMat = new THREE.LineBasicMaterial({ color: 0xbff9ff, transparent: true, opacity: 0.5, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
  const rungLines = new THREE.LineSegments(rGeo, rMat); rungLines.frustumCulled = false; group.add(rungLines);
  const pa = new THREE.Vector3(), pb = new THREE.Vector3();

  // prog：0..1 生长进度（锁链从下往上长出来）
  function update(t, f = {}, prog = 1) {
    const p = clamp(prog, 0, 1);
    A.layout((u) => point(u, 0, t), { frac: p, scale, samples: 500 });
    B.layout((u) => point(u, Math.PI, t), { frac: p, scale, samples: 500 });
    gMat.uniforms.uT.value = t; gMat.uniforms.uP.value = p;
    for (let i = 0; i < NG; i++) for (let s = 0; s < 2; s++) {
      const k = i * 2 + s; point(gu[k], s ? Math.PI : 0, t, pa);
      gpos[k * 3] = pa.x; gpos[k * 3 + 1] = pa.y; gpos[k * 3 + 2] = pa.z;
    }
    gPosAttr.needsUpdate = true;
    for (let j = 0; j < rungs; j++) {
      const u = (j + 0.5) / rungs;
      if (u <= p) { point(u, 0, t, pa); point(u, Math.PI, t, pb); } else { pa.set(0, 0, 0); pb.set(0, 0, 0); }
      rPos.set([pa.x, pa.y, pa.z, pb.x, pb.y, pb.z], j * 6);
    }
    rAttr.needsUpdate = true;
    rMat.opacity = 0.3 + 0.2 * Math.sin(t * 2.2) + 0.25 * (f.kick || 0);
  }
  return { group, update };
}
