"""一次性补丁（第三轮）：魂字过曝改为普通混合；歌词层亮度降低；城市/隧道的泛光略降。"""
import io, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'web', 'src')
EDITS = [
 (os.path.join(W, 'cyber.js'), [
   ("const hero = makeGlyphBank(ctx.atlasF, heroColor, 1, 0.95);", "const hero = makeGlyphBank(ctx.atlasF, heroColor, 1, 0.8);"),
   ("const heroO = makeGlyphBank(ctx.atlasO, outline, 1, 0.85);", "const heroO = makeGlyphBank(ctx.atlasO, outline, 1, 0.7);"),
 ]),
 (os.path.join(W, 'worlds', 'soul.js'), [
   ("const main = textMesh('魂', 7, { ...O, chrome: true, glow: '#ff4fd8' }, true);",
    "const main = textMesh('魂', 7, { ...O, chrome: true, glow: '#ff4fd8' }, false);"),
   ("const cy = textMesh('魂', 7, { ...O, fill: '#3ff6ff' }, true); cy.material.opacity = 0.5;",
    "const cy = textMesh('魂', 7, { ...O, fill: '#3ff6ff' }, true); cy.material.opacity = 0.35;"),
   ("const pk = textMesh('魂', 7, { ...O, fill: '#ff2f8f' }, true); pk.material.opacity = 0.5;",
    "const pk = textMesh('魂', 7, { ...O, fill: '#ff2f8f' }, true); pk.material.opacity = 0.35;"),
   ("s.bloom = 0.5 + imp * 0.4 + f.kick * 0.1;", "s.bloom = 0.32 + imp * 0.2 + f.kick * 0.08;"),
 ]),
 (os.path.join(W, 'worlds', 'city.js'), [
   ("s.bloom = 0.5 + f.kick * 0.15;", "s.bloom = 0.4 + f.kick * 0.12;"),
 ]),
]
for path, pairs in EDITS:
    s = io.open(path, encoding='utf-8').read()
    for old, new in pairs:
        n = s.count(old)
        assert n == 1, (os.path.basename(path), n, old[:70])
        s = s.replace(old, new)
    io.open(path, 'w', encoding='utf-8', newline='\n').write(s)
    print('patched', os.path.basename(path))
