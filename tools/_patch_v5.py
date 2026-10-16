import pathlib, re

ROOT = pathlib.Path(r'D:\AI\GhostChain MV\GhostChain_MV')
WEB = ROOT / 'web'

def patch(path, pairs):
    s = path.read_text(encoding='utf-8')
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, (path.name, n, old[:70])
        s = s.replace(old, new)
    path.write_text(s, encoding='utf-8')
    print('ok', path.relative_to(ROOT))

# 1) dna.js 补 THREE 导入
patch(WEB / 'src' / 'dna.js', [
    ("import { makeChain, lerp, clamp } from './lib.js';",
     "import * as THREE from 'three';\nimport { makeChain, lerp, clamp } from './lib.js';"),
])

# 2) 芯片平面：从 makeCyberField 中删除（保留代码面板）
p = WEB / 'src' / 'cyber.js'
s = p.read_text(encoding='utf-8')
old_a = "  const chips = [0, 1, 2, 3].map(chipTexture), ctex = [0, 1, 2, 3, 4].map((i) => codeTexture(seed + i));"
assert s.count(old_a) == 1, 'chips line'
s = s.replace(old_a, "  const ctex = [0, 1, 2, 3, 4].map((i) => codeTexture(seed + i));")
a = s.index("  const pg = new THREE.PlaneGeometry(1, 1);")
b = s.index("  const cw = 15")
s = s[:a] + s[b:]
p.write_text(s, encoding='utf-8'); print('ok chips removed')

# 3) void：恢复锁链螺旋，去掉 DNA
patch(WEB / 'src' / 'worlds' / 'void.js', [
    ("// 场景 void：Intro。虚空里浮出幽灵剪影，被一条双螺旋的数据结构（DNA 式）缠绕，标题 CHAINEDGHOST 故障闪现。",
     "// 场景 void：Intro。虚空里浮出幽灵剪影，被铬金属锁链螺旋缠绕，标题 CHAINEDGHOST 故障闪现。"),
    ("import { makeDNA } from '../dna.js';", "import { makeChain } from '../lib.js';"),
    ("  // 双螺旋：灵魂与数据结构缠绕，随时间从下往上生长\n  const dna = makeDNA(ctx.env, { height: 12, radius: 4.4, turns: 3, rungs: 44, beads: 380, spin: 0.35 });\n  dna.group.position.set(0, -0.2, -0.5); scene.add(dna.group);",
     "  const chain = makeChain(260, ctx.env); scene.add(chain.mesh);"),
    ("chain: dna.group", "chain: chain.mesh"),
    ("    // 双螺旋随时间生长，横向节点随鼓点闪亮\n    dna.update(t, f, smooth(1.5, 12, lt), f.kick * 0.5);",
     "    // 锁链螺旋：随时间长出来\n    const grow = smooth(1.5, 12, lt);\n    chain.layout((x) => { const a = x * Math.PI * 2 * 3.2 + t * 0.55, r = 3.9 + 0.5 * Math.sin(x * 7 + t * 0.9) + f.kick * 0.15; return new THREE.Vector3(Math.cos(a) * r, 0.0 + x * 11.0, Math.sin(a) * r * 0.75 - 0.5); }, { frac: 0.12 + 0.88 * grow, scale: 0.62 });\n    chain.mesh.position.set(0, 0, 0);"),
])

# 4) soul：去掉背后的 DNA（soul 的锁链螺旋保留）
patch(WEB / 'src' / 'worlds' / 'soul.js', [
    ("import { makeCyberField } from '../cyber.js';\nimport { makeDNA } from '../dna.js';", "import { makeCyberField } from '../cyber.js';"),
    ("  // 背后的双螺旋（DNA 式结构）：灵魂的骨架，203 秒后慢慢生长出来\n  const dna = makeDNA(ctx.env, { height: 18, radius: 9, turns: 2.2, rungs: 30, beads: 300, spin: 0.25 }); dna.group.position.set(0, -4.5, -9); dna.group.visible = false; scene.add(dna.group);", ""),
    ("    const dprog = smooth(203, 209, t); dna.group.visible = dprog > 0.001; dna.update(t, f, dprog, imp * 0.8);\n", ""),
])

# 5) 锁链恢复：matrix / dream / highway / city / tunnel 改回真锁链（lib.js 的 makeChain）
patch(WEB / 'src' / 'worlds' / 'matrix.js', [
    ("import { makeCableSet as makeChain } from '../cyber.js';", "import { makeChain } from '../lib.js';"),
])
patch(WEB / 'src' / 'worlds' / 'dream.js', [
    ("import { makeCableSet as makeChain, makeCyberField } from '../cyber.js';",
     "import { makeChain } from '../lib.js';\nimport { makeCyberField } from '../cyber.js';"),
])
patch(WEB / 'src' / 'worlds' / 'highway.js', [
    ("import { makeCableSet as makeChain, makeCyberField, makeBlockField } from '../cyber.js';",
     "import { makeChain } from '../lib.js';\nimport { makeCyberField, makeBlockField } from '../cyber.js';"),
])
patch(WEB / 'src' / 'worlds' / 'city.js', [
    ("import { makeCableSet as makeChain, makeLyricLayer, makeCyberField, makeBlockField } from '../cyber.js';",
     "import { makeChain } from '../lib.js';\nimport { makeLyricLayer, makeCyberField, makeBlockField } from '../cyber.js';"),
])
patch(WEB / 'src' / 'worlds' / 'tunnel.js', [
    ("import { makeCableSet, makeLyricLayer } from '../cyber.js';",
     "import { makeChain } from '../lib.js';\nimport { makeLyricLayer } from '../cyber.js';"),
    ("makeCableSet(72, ctx.env, { colors: i % 2 ? [PAL.cyan] : [PAL.pink, PAL.yellow] })", "makeChain(72, ctx.env)"),
])

# 6) 注册 cpu 场景
patch(WEB / 'src' / 'worlds' / 'index.js', [
    ("import * as endcard from './endcard.js';",
     "import * as endcard from './endcard.js';\nimport * as cpu from './cpu.js';"),
    ("soulvoid, endcard };", "soulvoid, endcard, cpu };"),
])

# 7) cpu 场景：中央处理器升起锁链双螺旋（DNA 式意向）
patch(WEB / 'src' / 'worlds' / 'cpu.js', [
    ("import { PAL, col, glowSprite, rng, smooth, lerp, clamp } from '../lib.js';",
     "import { PAL, col, glowSprite, rng, smooth, lerp, clamp } from '../lib.js';\nimport { makeDNA } from '../dna.js';"),
    ("  const core = glowSprite('63,246,255', 34, 0.3); core.position.set(0, 1.6, 0); scene.add(core);",
     "  const core = glowSprite('63,246,255', 34, 0.3); core.position.set(0, 1.6, 0); scene.add(core);\n"
     "  // 从处理器中央升起的锁链双螺旋（DNA 式意向）：灵魂与结构缠绕\n"
     "  const dna = makeDNA(ctx.env, { height: 14, radius: 3.4, turns: 2.5, links: 110, scale: 0.6 }); dna.group.position.set(0, 1.6, 0); scene.add(dna.group);"),
    ("    core.material.opacity = 0.25 + f.kick * 0.25;",
     "    core.material.opacity = 0.25 + f.kick * 0.25;\n    dna.update(t, f, smooth(0.12, 0.6, S.p || 0));"),
])

# 8) 时间轴：Break 1 拆成 dream（前半）+ cpu（后半）
p = ROOT / 'tools' / 'build_timing.py'
patch(p, [
    ("    dict(id='break1',     name='Break 1',      start=63.3,   end=79.4,   world='dream'),",
     "    dict(id='break1',     name='Break 1',      start=63.3,   end=71.5,   world='dream'),\n"
     "    dict(id='cpu',        name='CPU',          start=71.5,   end=79.4,   world='cpu'),"),
])
print('all v5 done')
