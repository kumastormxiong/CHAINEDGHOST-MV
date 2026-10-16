// 场景 cpu（Break 1 后半段）：超级复杂的 CPU 电路板。镜头绕着板子缓慢俯冲，掠过密集走线、焊盘、过孔、
// 芯片、引脚与电容；信号脉冲沿走线奔跑，中央处理器的引脚随鼓点闪亮。全部确定性（固定种子），录制与逐帧渲染一致。
import * as THREE from 'three';
import { PAL, col, glowSprite, rng, smooth, lerp, clamp } from '../lib.js';
import { makeDNA } from '../dna.js';

const HALF = 60, GRID = 1.2;
const snap = (v) => Math.round(v / GRID) * GRID;
const clampH = (v) => Math.max(-HALF, Math.min(HALF, v));
const dummy = new THREE.Object3D();

function boardTexture() {
  const S = 1024, cv = document.createElement('canvas'); cv.width = cv.height = S; const g = cv.getContext('2d');
  g.fillStyle = '#04150c'; g.fillRect(0, 0, S, S);
  g.strokeStyle = 'rgba(80,255,170,0.09)'; g.lineWidth = 2;
  for (let i = 0; i <= S; i += S / 40) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, S); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(S, i); g.stroke(); }
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.repeat.set(4, 4);
  return tex;
}

function dieTexture() {
  const S = 512, cv = document.createElement('canvas'); cv.width = cv.height = S; const g = cv.getContext('2d');
  g.fillStyle = '#0a0e14'; g.fillRect(0, 0, S, S);
  g.strokeStyle = 'rgba(63,246,255,0.35)'; g.lineWidth = 2;
  for (let i = 0; i <= S; i += 16) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, S); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(S, i); g.stroke(); }
  g.strokeStyle = '#ff2f8f'; g.lineWidth = 8; g.strokeRect(24, 24, S - 48, S - 48);
  g.fillStyle = '#7ff9ff'; g.font = '700 46px Consolas, "Courier New", monospace'; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.fillText('CORE', S / 2, S / 2);
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; return tex;
}

export function create(ctx) {
  const scene = new THREE.Scene(); scene.background = col(0x010a06); scene.fog = new THREE.FogExp2(0x010a06, 0.006);
  const camera = new THREE.PerspectiveCamera(55, 16 / 9, 0.1, 400);
  const R = rng(404);

  // 板子（深绿基材 + 网格纹理）
  const board = new THREE.Mesh(new THREE.PlaneGeometry(HALF * 2 + 30, HALF * 2 + 30), new THREE.MeshBasicMaterial({ map: boardTexture(), toneMapped: false }));
  board.rotation.x = -Math.PI / 2; board.position.y = -0.5; scene.add(board);

  // 走线：正交折线（曼哈顿路由）
  const traces = [];
  for (let i = 0; i < 260; i++) {
    let x = snap((R() - 0.5) * 2 * HALF), z = snap((R() - 0.5) * 2 * HALF);
    const pts = [[x, z]]; let horiz = R() < 0.5;
    const steps = 3 + Math.floor(R() * 6);
    for (let s = 0; s < steps; s++) {
      const len = snap((R() - 0.5) * 36);
      if (horiz) x = clampH(x + len); else z = clampH(z + len);
      pts.push([x, z]); horiz = !horiz;
    }
    traces.push(pts);
  }
  const TR = traces.map((pts) => {
    const segs = []; let total = 0;
    for (let j = 0; j < pts.length - 1; j++) {
      const [x0, z0] = pts[j], [x1, z1] = pts[j + 1];
      const len = Math.hypot(x1 - x0, z1 - z0); if (len < 1e-3) continue;
      segs.push({ x0, z0, x1, z1, len, start: total, rotY: Math.abs(x1 - x0) > 1e-3 ? 0 : Math.PI / 2 });
      total += len;
    }
    return { segs, total };
  }).filter((tr) => tr.segs.length);
  const allSegs = TR.flatMap((tr) => tr.segs);

  const traceMesh = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 0.05, 0.14), new THREE.MeshBasicMaterial({ toneMapped: false }), allSegs.length);
  allSegs.forEach((s, i) => {
    dummy.position.set((s.x0 + s.x1) / 2, 0.02, (s.z0 + s.z1) / 2); dummy.rotation.set(0, s.rotY, 0); dummy.scale.set(s.len, 1, 1); dummy.updateMatrix(); traceMesh.setMatrixAt(i, dummy.matrix);
    const cyan = i % 3 === 0;
    traceMesh.setColorAt(i, new THREE.Color(cyan ? PAL.cyan : 0xd9a441).multiplyScalar(cyan ? 0.55 : 0.85));
  });
  scene.add(traceMesh);

  // 焊盘与过孔
  const padGeo = new THREE.CircleGeometry(0.2, 10); padGeo.rotateX(-Math.PI / 2);
  const pads = new THREE.InstancedMesh(padGeo, new THREE.MeshBasicMaterial({ color: 0xffd98a, toneMapped: false }), allSegs.length);
  allSegs.forEach((s, i) => { dummy.position.set(s.x0, 0.05, s.z0); dummy.rotation.set(0, 0, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix(); pads.setMatrixAt(i, dummy.matrix); });
  scene.add(pads);
  const viaSegs = allSegs.filter((_, i) => i % 3 === 0);
  const viaGeo = new THREE.RingGeometry(0.1, 0.22, 10); viaGeo.rotateX(-Math.PI / 2);
  const vias = new THREE.InstancedMesh(viaGeo, new THREE.MeshBasicMaterial({ color: PAL.cyan, toneMapped: false }), viaSegs.length);
  viaSegs.forEach((s, i) => { dummy.position.set(s.x1, 0.06, s.z1); dummy.rotation.set(0, 0, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix(); vias.setMatrixAt(i, dummy.matrix); });
  scene.add(vias);

  // 芯片与引脚
  const CHIPS = [];
  for (let i = 0; i < 46; i++) {
    const cx = snap((R() - 0.5) * 2 * (HALF - 6)), cz = snap((R() - 0.5) * 2 * (HALF - 6));
    if (Math.abs(cx) < 12 && Math.abs(cz) < 12) continue;
    CHIPS.push({ cx, cz, w: 2.4 + Math.floor(R() * 4) * 1.2, d: 1.8 + Math.floor(R() * 3) * 1.2, pins: 4 + Math.floor(R() * 5) * 2 });
  }
  const chipBody = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 0.5, 1), new THREE.MeshBasicMaterial({ color: 0x0b0f0d, toneMapped: false }), CHIPS.length);
  CHIPS.forEach((c, i) => { dummy.position.set(c.cx, 0.25, c.cz); dummy.rotation.set(0, 0, 0); dummy.scale.set(c.w, 1, c.d); dummy.updateMatrix(); chipBody.setMatrixAt(i, dummy.matrix); });
  scene.add(chipBody);
  const chipPins = [];
  CHIPS.forEach((c) => {
    const half = c.pins / 2;
    for (let j = 0; j < half; j++) {
      const x = c.cx - c.w / 2 + (j + 0.5) * (c.w / half);
      chipPins.push([x, c.cz - c.d / 2 - 0.1]); chipPins.push([x, c.cz + c.d / 2 + 0.1]);
    }
  });
  const pinMesh = new THREE.InstancedMesh(new THREE.BoxGeometry(0.12, 0.08, 0.5), new THREE.MeshBasicMaterial({ color: 0xd9b25a, toneMapped: false }), chipPins.length);
  chipPins.forEach(([x, z], i) => { dummy.position.set(x, 0.1, z); dummy.rotation.set(0, 0, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix(); pinMesh.setMatrixAt(i, dummy.matrix); });
  scene.add(pinMesh);

  // 电容（银色小圆柱）
  const CAPS = [];
  for (let i = 0; i < 90; i++) CAPS.push([snap((R() - 0.5) * 2 * (HALF - 3)), snap((R() - 0.5) * 2 * (HALF - 3)), R() < 0.5 ? 0 : Math.PI / 2]);
  const capGeo = new THREE.CylinderGeometry(0.16, 0.16, 0.42, 8); capGeo.rotateZ(Math.PI / 2);
  const caps = new THREE.InstancedMesh(capGeo, new THREE.MeshBasicMaterial({ color: 0xbfd0d8, toneMapped: false }), CAPS.length);
  CAPS.forEach(([x, z, ry], i) => { dummy.position.set(x, 0.16, z); dummy.rotation.set(0, ry, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix(); caps.setMatrixAt(i, dummy.matrix); });
  scene.add(caps);

  // 中央处理器：封装 + 顶盖（纹理）+ 四圈引脚（随鼓点闪亮）
  const die = new THREE.Group(); scene.add(die);
  const pkg = new THREE.Mesh(new THREE.BoxGeometry(16, 0.9, 16), new THREE.MeshBasicMaterial({ color: 0x07090c, toneMapped: false })); pkg.position.y = 0.45; die.add(pkg);
  const lid = new THREE.Mesh(new THREE.BoxGeometry(11, 0.25, 11), new THREE.MeshBasicMaterial({ map: dieTexture(), toneMapped: false })); lid.position.y = 1.02; die.add(lid);
  const DP = [];
  for (let s = 0; s < 4; s++) for (let j = 0; j < 24; j++) {
    const u = -7.5 + (j + 0.5) * (15 / 24);
    const onZ = s < 2;
    DP.push({ x: onZ ? u : (s === 2 ? -8.6 : 8.6), z: onZ ? (s === 0 ? -8.6 : 8.6) : u, rotY: onZ ? 0 : Math.PI / 2, ph: j * 0.4 + s * 1.3 });
  }
  const dpMesh = new THREE.InstancedMesh(new THREE.BoxGeometry(0.22, 0.12, 0.7), new THREE.MeshBasicMaterial({ color: 0xffd98a, toneMapped: false }), DP.length);
  scene.add(dpMesh);
  const core = glowSprite('63,246,255', 34, 0.3); core.position.set(0, 1.6, 0); scene.add(core);
  // 从处理器中央升起的锁链双螺旋（DNA 式意向）：灵魂与结构缠绕
  const dna = makeDNA(ctx.env, { height: 14, radius: 3.4, turns: 2.5, links: 110, scale: 0.6 }); dna.group.position.set(0, 1.6, 0); scene.add(dna.group);

  // 信号脉冲：沿走线奔跑
  const P = 180;
  const pulses = []; for (let i = 0; i < P; i++) pulses.push({ tr: Math.floor(R() * TR.length), ph: R(), sp: 8 + R() * 16 });
  const pulseMesh = new THREE.InstancedMesh(new THREE.BoxGeometry(0.9, 0.14, 0.14), new THREE.MeshBasicMaterial({ toneMapped: false, blending: THREE.AdditiveBlending, depthWrite: false }), P);
  for (let i = 0; i < P; i++) pulseMesh.setColorAt(i, new THREE.Color(i % 2 ? PAL.cyan : PAL.pink).multiplyScalar(2.2));
  scene.add(pulseMesh);

  function update({ t, f, S, post }) {
    const e = smooth(0, 1, S.p || 0);
    const ang = t * 0.09, Rr = lerp(46, 26, e), H = lerp(58, 24, e);
    camera.position.set(Math.cos(ang) * Rr, H + Math.sin(t * 0.4) * 0.6 + f.kick * 0.4, Math.sin(ang) * Rr);
    camera.lookAt(Math.cos(ang + 0.6) * 4, 0, Math.sin(ang + 0.6) * 4);
    camera.fov = 55 + f.kick * 2; camera.updateProjectionMatrix();

    for (let i = 0; i < P; i++) {
      const p = pulses[i], tr = TR[p.tr];
      const s = (((p.ph * tr.total + t * p.sp) % tr.total) + tr.total) % tr.total;
      let seg = tr.segs[0];
      for (const sg of tr.segs) { if (s <= sg.start + sg.len) { seg = sg; break; } }
      const u = clamp((s - seg.start) / seg.len, 0, 1);
      dummy.position.set(seg.x0 + (seg.x1 - seg.x0) * u, 0.1, seg.z0 + (seg.z1 - seg.z0) * u); dummy.rotation.set(0, seg.rotY, 0); dummy.scale.set(1, 1, 1); dummy.updateMatrix();
      pulseMesh.setMatrixAt(i, dummy.matrix);
    }
    pulseMesh.instanceMatrix.needsUpdate = true;

    DP.forEach((d, i) => {
      const k = 1 + f.kick * 1.6 * (0.5 + 0.5 * Math.sin(t * 7 + d.ph));
      dummy.position.set(d.x, 0.2, d.z); dummy.rotation.set(0, d.rotY, 0); dummy.scale.set(1, k, 1); dummy.updateMatrix(); dpMesh.setMatrixAt(i, dummy.matrix);
    });
    dpMesh.instanceMatrix.needsUpdate = true;
    core.material.opacity = 0.25 + f.kick * 0.25;
    dna.update(t, f, smooth(0.12, 0.6, S.p || 0));

    const s = post.s; s.bloom = 0.45 + f.kick * 0.25; s.glitch = Math.max(s.glitch, f.hit * 0.3); s.ab = 0.002 + f.hit * 0.004; s.scan = 0.1; s.track = 0.2;
  }
  return { scene, camera, update };
}
