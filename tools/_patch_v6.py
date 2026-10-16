import pathlib

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

# 1) outro：红蓝数据珠 -> 真锁链；泛光与色散降低
patch(WEB / 'src' / 'worlds' / 'outro.js', [
    ("import { makeCableSet, makeLyricLayer, makeCyberField } from '../cyber.js';",
     "import { makeChain } from '../lib.js';\nimport { makeLyricLayer, makeCyberField } from '../cyber.js';"),
    ("  const strands = makeCableSet(420, ctx.env, { colors: [PAL.cyan, PAL.pink] }); scene.add(strands.mesh);",
     "  const strands = makeChain(240, ctx.env); strands.mesh.frustumCulled = false; scene.add(strands.mesh);"),
    ("    const s = post.s; s.bloom = 0.5 + f.kick * 0.1; s.glitch = Math.max(s.glitch, f.hit * 0.2); s.ab = 0.003 + f.hit * 0.002; s.track = 0.4; s.scan = 0.13;",
     "    const s = post.s; s.bloom = 0.3 + f.kick * 0.08; s.glitch = Math.max(s.glitch, f.hit * 0.2); s.ab = 0.0015 + f.hit * 0.002; s.track = 0.4; s.scan = 0.13;"),
])

# 2) 歌词层：假名的亮度与泛光整体降低（之前过曝，字形看不清）
patch(WEB / 'src' / 'cyber.js', [
    ("      const a = hero.show(ch, 0.95); a.position.set(0, halfH * heroY, 0); a.scale.setScalar(sc);",
     "      const a = hero.show(ch, 0.55); a.position.set(0, halfH * heroY, 0); a.scale.setScalar(sc);"),
    ("      const b = heroO.show(ch, 0.85); b.position.set(halfH * 0.01, halfH * heroY - halfH * 0.01, -0.02); b.scale.setScalar(sc * 1.04);",
     "      const b = heroO.show(ch, 0.45); b.position.set(halfH * 0.01, halfH * heroY - halfH * 0.01, -0.02); b.scale.setScalar(sc * 1.04);"),
])
print('v6 done')
