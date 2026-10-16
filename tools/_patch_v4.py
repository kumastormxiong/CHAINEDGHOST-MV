import pathlib

ROOT = pathlib.Path(r'D:\AI\GhostChain MV\GhostChain_MV\web')

BLOCK = '''// ---------- 数据方块场：无文字的抽象立方体阵列，缓慢升降、闪烁，给背景加一层高科技纹理 ----------
export function makeBlockField({ n = 200, box = [60, 30, 200], colors = [PAL.cyan, PAL.pink, PAL.yellow], seed = 21 } = {}) {
  const mesh = new THREE.InstancedMesh(new THREE.BoxGeometry(1, 1, 1), new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }), n);
  mesh.frustumCulled = false;
  const r = rng(seed), cells = [];
  for (let i = 0; i < n; i++) {
    const base = new THREE.Vector3((r() - 0.5) * box[0] * 2, r() * box[1] - box[1] * 0.25, -8 - r() * box[2]);
    cells.push({ base, sz: 0.25 + r() * 0.9, ph: r() * 6.28, sp: 0.3 + r() * 0.8 });
    mesh.setColorAt(i, new THREE.Color(colors[i % colors.length]).multiplyScalar(0.9));
  }
  const M = new THREE.Matrix4(), P = new THREE.Vector3(), S = new THREE.Vector3(), Q = new THREE.Quaternion();
  function update(t, f) {
    for (let i = 0; i < n; i++) {
      const c = cells[i];
      const y = c.base.y + Math.sin(t * c.sp + c.ph) * 0.9 + f.kick * 0.3;
      const flick = 0.5 + 0.5 * Math.sin(t * c.sp * 5 + c.ph);
      const s = c.sz * (0.4 + 0.6 * flick) * (1 + f.hit * 0.2);
      P.set(c.base.x, y, c.base.z); S.set(s, s, s);
      M.compose(P, Q, S); mesh.setMatrixAt(i, M);
    }
    mesh.instanceMatrix.needsUpdate = true;
  }
  return { mesh, update };
}

// ---------- 歌词层：挂在镜头上，任何场景都可以用 ----------'''

def patch(rel, pairs):
    p = ROOT / rel
    s = p.read_text(encoding='utf-8')
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, (rel, n, old[:70])
        s = s.replace(old, new)
    p.write_text(s, encoding='utf-8')
    print('ok', rel)

patch('src/cyber.js', [
    ("//  makeFlashCards 闪回卡片：记忆碎片一闪而过\n",
     "//  makeFlashCards 闪回卡片：记忆碎片一闪而过\n//  makeBlockField 抽象数据方块场：无文字的立方体阵列\n"),
    ("'return NULL;'];", "'return NULL;', 'helix.encode(soul, key);', 'dna[i] ^= chain[i];'];"),
    ("// ---------- 歌词层：挂在镜头上，任何场景都可以用 ----------", BLOCK),
])

patch('src/worlds/soul.js', [
    ("import { makeCyberField } from '../cyber.js';",
     "import { makeCyberField } from '../cyber.js';\nimport { makeDNA } from '../dna.js';"),
    ("  const chain = makeChain(300, ctx.env); chain.mesh.frustumCulled = false; chain.mesh.count = 0; scene.add(chain.mesh);",
     "  const chain = makeChain(300, ctx.env); chain.mesh.frustumCulled = false; chain.mesh.count = 0; scene.add(chain.mesh);\n"
     "  // 背后的双螺旋（DNA 式结构）：灵魂的骨架，203 秒后慢慢生长出来\n"
     "  const dna = makeDNA(ctx.env, { height: 18, radius: 9, turns: 2.2, rungs: 30, beads: 300, spin: 0.25 }); dna.group.position.set(0, -4.5, -9); dna.group.visible = false; scene.add(dna.group);"),
    ("    cf.update(t, f);\n",
     "    cf.update(t, f);\n    const dprog = smooth(203, 209, t); dna.group.visible = dprog > 0.001; dna.update(t, f, dprog, imp * 0.8);\n"),
])

patch('src/worlds/city.js', [
    ("import { makeCableSet as makeChain, makeLyricLayer, makeCyberField } from '../cyber.js';",
     "import { makeCableSet as makeChain, makeLyricLayer, makeCyberField, makeBlockField } from '../cyber.js';"),
    ("  const cf = makeCyberField({ n: 26, codes: 8, box: [40, 30, 200], seed: 21 }); scene.add(cf.group);",
     "  const cf = makeCyberField({ n: 26, codes: 8, box: [40, 30, 200], seed: 21 }); scene.add(cf.group);\n"
     "  const bf = makeBlockField({ n: 150, box: [46, 30, 200], seed: 61 }); scene.add(bf.mesh);"),
    ("    lyr.update(k, t, f); cf.update(t, f);",
     "    lyr.update(k, t, f); cf.update(t, f); bf.update(t, f);"),
])

patch('src/worlds/highway.js', [
    ("import { makeCableSet as makeChain, makeCyberField } from '../cyber.js';",
     "import { makeCableSet as makeChain, makeCyberField, makeBlockField } from '../cyber.js';"),
    ("  const cf = makeCyberField({ n: 34, codes: 10, box: [70, 36, 240], seed: 41 }); scene.add(cf.group);",
     "  const cf = makeCyberField({ n: 34, codes: 10, box: [70, 36, 240], seed: 41 }); scene.add(cf.group);\n"
     "  const bf = makeBlockField({ n: 120, box: [60, 30, 240], seed: 62 }); scene.add(bf.mesh);"),
    ("    cf.update(t, f);\n",
     "    cf.update(t, f); bf.update(t, f);\n"),
])

patch('src/worlds/wasteland.js', [
    ("import { makeCableSet, makeCyberField, makeLyricLayer, makeFlashCards } from '../cyber.js';",
     "import { makeCableSet, makeCyberField, makeLyricLayer, makeFlashCards, makeBlockField } from '../cyber.js';"),
    ("  const cf = makeCyberField({ n: 24, codes: 8, box: [60, 32, 220], seed: 51 }); scene.add(cf.group);",
     "  const cf = makeCyberField({ n: 24, codes: 8, box: [60, 32, 220], seed: 51 }); scene.add(cf.group);\n"
     "  const bf = makeBlockField({ n: 110, box: [60, 30, 300], seed: 71 }); scene.add(bf.mesh);"),
    ("    cf.update(t, f);\n",
     "    cf.update(t, f); bf.update(t, f);\n"),
])

patch('src/worlds/flash.js', [
    ("const TERM_TEXT = '> GHOSTCHAIN.EXE ... OK';", "const TERM_TEXT = '> CHAINEDGHOST.EXE ... OK';"),
])

patch('index.html', [
    ("<title>GHOSTCHAIN</title>", "<title>CHAINEDGHOST</title>"),
])

patch('src/main.js', [
    ("'GhostChain_recorded'", "'CHAINEDGHOST_recorded'"),
])
print('all done')
