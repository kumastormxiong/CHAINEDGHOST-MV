// 锁链双螺旋（DNA 式结构）：两根真锁链互相缠绕成双螺旋，抽象地表达"灵魂与结构缠绕在一起"。
// 不含任何区块链符号或文字。只用于中间的 CPU 场景，作为意向。
import * as THREE from 'three';
import { makeChain, lerp, clamp } from './lib.js';

export function makeDNA(env, { height = 14, radius = 3.4, turns = 2.5, links = 110, spin = 0.5, scale = 0.6 } = {}) {
  const A = makeChain(links, env), B = makeChain(links, env);
  A.mesh.frustumCulled = false; B.mesh.frustumCulled = false;
  const group = new THREE.Group(); group.add(A.mesh, B.mesh);
  const point = (u, phase, t) => {
    const a = u * turns * Math.PI * 2 + phase + t * spin;
    return new THREE.Vector3(Math.cos(a) * radius, lerp(0, height, u), Math.sin(a) * radius);
  };
  // prog：0..1 生长进度（锁链从下往上长出来）
  function update(t, f = {}, prog = 1) {
    const p = clamp(prog, 0, 1);
    A.layout((u) => point(u, 0, t), { frac: p, scale, samples: 500 });
    B.layout((u) => point(u, Math.PI, t), { frac: p, scale, samples: 500 });
  }
  return { group, update };
}
