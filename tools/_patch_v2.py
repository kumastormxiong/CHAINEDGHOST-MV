"""一次性补丁：把 city / dream / highway / matrix / void 里的锁链换成数据包串，并给城市、高速、梦境补上背景元素与歌词层。"""
import io, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'web', 'src', 'worlds')

EDITS = [
 (os.path.join(W, 'city.js'), [
   ("import { PAL, col, KANA, makeGhost, makeGrid, makeSun, makeStars, makeChain, makeSky, glyphMesh, glowSprite, smooth, clamp, lerp, rng, hash } from '../lib.js';",
    "import { PAL, col, KANA, makeGrid, makeSun, makeStars, makeSky, glyphMesh, glowSprite, smooth, clamp, lerp, rng, hash } from '../lib.js';\nimport { makeCableSet as makeChain, makeLyricLayer, makeCyberField } from '../cyber.js';"),
   ("  const girl = makeGhost(ctx.girlTex, 34); girl.position.set(0, 23, -64); girl.visible = false; scene.add(girl);",
    "  const lyr = makeLyricLayer(ctx, camera, scene, { heroColor: 0xffd6ef, outline: PAL.cyan });\n  const cf = makeCyberField({ n: 26, codes: 8, box: [40, 30, 200], seed: 21 }); scene.add(cf.group);"),
   ("    const gu = girl.material.uniforms; gu.uTime.value = t; gu.uGlitch.value = f.hit * 0.3 + 0.05; gu.uFade.value = smooth(1, 5, S.lt) * (pre ? 1 : 0.85); gu.uBright.value = 1.0;",
    "    lyr.update(k, t, f); cf.update(t, f);"),
   ("    girl.position.y = 23 + Math.sin(t * 0.7) * 0.9; girl.rotation.z = Math.sin(t * 0.4) * 0.05;", ""),
 ]),
 (os.path.join(W, 'dream.js'), [
   ("import { PAL, col, KANA, JP_FONT, makeSun, makeSky, makeChain, makeGhost, glyphMesh, glowSprite, smooth, clamp, lerp, rng, makeStars } from '../lib.js';",
    "import { PAL, col, KANA, JP_FONT, makeSun, makeSky, makeGhost, glyphMesh, glowSprite, smooth, clamp, lerp, rng, makeStars } from '../lib.js';\nimport { makeCableSet as makeChain, makeCyberField } from '../cyber.js';"),
   ("  scene.add(new THREE.AmbientLight(0xffddee, 0.6));",
    "  const cf = makeCyberField({ n: 30, codes: 6, box: [50, 30, 160], seed: 31 }); scene.add(cf.group);\n  scene.add(new THREE.AmbientLight(0xffddee, 0.6));"),
   ("    eyesF.update(t, camera, { opacity: 0.8, appear: smooth(1.5, 9, S.lt), kick: f.kick * 0.5 });",
    "    cf.update(t, f);\n    eyesF.update(t, camera, { opacity: 0.8, appear: smooth(1.5, 9, S.lt), kick: f.kick * 0.5 });"),
 ]),
 (os.path.join(W, 'highway.js'), [
   ("import { PAL, col, makeGrid, makeSun, makeStars, makeChain, makeRidge, makeSky, makeGlyphBank, glowSprite, smooth, clamp, lerp } from '../lib.js';",
    "import { PAL, col, makeGrid, makeSun, makeStars, makeRidge, makeSky, makeGlyphBank, glowSprite, smooth, clamp, lerp } from '../lib.js';\nimport { makeCableSet as makeChain, makeCyberField } from '../cyber.js';"),
   ("  scene.add(new THREE.AmbientLight(0x553355, 0.6));",
    "  const cf = makeCyberField({ n: 34, codes: 10, box: [70, 36, 240], seed: 41 }); scene.add(cf.group);\n  scene.add(new THREE.AmbientLight(0x553355, 0.6));"),
   ("    // 相机",
    "    cf.update(t, f);\n    // 相机"),
 ]),
 (os.path.join(W, 'matrix.js'), [
   ("import { PAL, col, KANA, makeGrid, makeStars, makeChain, glyphMesh, glowSprite, smooth, clamp, rng, hash } from '../lib.js';",
    "import { PAL, col, KANA, makeGrid, makeStars, glyphMesh, glowSprite, smooth, clamp, rng, hash } from '../lib.js';\nimport { makeCableSet as makeChain } from '../cyber.js';"),
 ]),
 (os.path.join(W, 'void.js'), [
   ("import { PAL, col, JP_FONT, makeStars, makeGrid, makeGhost, makeChain, glowSprite, textMesh, smooth, clamp, rng } from '../lib.js';",
    "import { PAL, col, JP_FONT, makeStars, makeGrid, makeGhost, glowSprite, textMesh, smooth, clamp, rng } from '../lib.js';\nimport { makeCableSet as makeChain } from '../cyber.js';"),
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
