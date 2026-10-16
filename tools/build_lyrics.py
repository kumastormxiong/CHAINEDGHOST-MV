"""读取原歌词卡 txt，生成 web/data/lyrics.json（按段落拆成 4 行×10 个假名）。
按你的修改：间奏「喔喔喔」= オ オ オ；结尾「魂」= タマシイ；歌词全部当作日文。
用法：python tools/build_lyrics.py
"""
import os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(ROOT, 'timing', 'original_lyrics_card.txt')
out = os.path.join(ROOT, 'web', 'data', 'lyrics.json')

text = open(src, encoding='utf-8').read()
body = text.split('【完整歌词 / Lyrics】:')[1].split('=====')[0]
body = body.replace('喔喔喔！', 'オ オ オ').replace('喔喔喔', 'オ オ オ').replace('魂……', 'タマシイ')

ids = {'Intro': 'intro', 'Verse 1': 'verse1', 'Verse 2': 'verse2', 'Bridge': 'bridge', 'Outro': 'outro'}
count = {'Pre-Chorus': 0, 'Chorus': 0, 'interlude': 0}
blocks, cur = [], None
for raw in body.splitlines():
    line = raw.strip()
    if not line:
        continue
    mh = re.match(r'^[\(\[](.+?)[\)\]]$', line)
    if mh:
        name = mh.group(1)
        if name in count:
            count[name] += 1
            bid = {'Pre-Chorus': 'pre', 'Chorus': 'chorus', 'interlude': 'interlude'}[name] + str(count[name])
        else:
            bid = ids.get(name, name.lower())
        cur = {'id': bid, 'tag': name, 'rows': []}
        blocks.append(cur)
    elif cur is not None:
        cur['rows'].append(line.replace('（choir）', '(choir)').split(' ') if ' ' in line else [line])

json.dump({'blocks': blocks}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for b in blocks:
    print(b['id'], [len(r) for r in b['rows']], b['rows'][:1])
