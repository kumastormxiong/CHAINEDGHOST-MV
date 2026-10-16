"""根据 timing/lyrics_timed.lrc 生成 web/data/timing.json 的 sections。
用法：python tools/build_timing.py
LRC 里每个"整行假名"的时间戳 = 这一行开始唱的时间；行结束时间 = 下一行开始 - 0.12 秒（段尾最后一行取 2.4~4.4 秒）。
逐字的精确时间不在这里改：用 web/timing.html 打点工具打点，结果存到 web/data/char_times.json，播放时优先使用它。
"""
import re, json, io, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
lrc = io.open(os.path.join(ROOT, 'timing', 'lyrics_timed.lrc'), encoding='utf-8-sig').read().splitlines()
lines = []
for ln in lrc:
    m = re.match(r'\[(\d+):(\d+\.\d+)\]\s*(.*)$', ln)
    if not m: continue
    t = int(m.group(1)) * 60 + float(m.group(2)); txt = m.group(3).strip()
    toks = txt.split()
    if len(toks) >= 9 and all(len(x) == 1 for x in toks):
        lines.append((t, len(toks)))
print('kana lines found:', len(lines))
assert len(lines) == 36, '期望 36 行假名（9 段 × 4 行）'

def ends(group_idx):
    out = []
    for gi in group_idx:
        s = lines[gi][0]
        nxt = lines[gi + 1][0] if gi + 1 < len(lines) else None
        prev_dur = (s - lines[gi - 1][0]) if gi > 0 else 3.0
        if nxt is not None and nxt - s <= 5.5 and (gi + 1) in group_idx:
            e = nxt - 0.12
        else:
            e = s + max(2.4, min(4.4, prev_dur - 0.12))
        out.append([round(s, 3), round(e, 3)])
    return out

names = ['verse1', 'pre1', 'chorus1', 'verse2', 'pre2', 'chorus2', 'bridge', 'chorus3', 'outro']
L = {n: ends(list(range(i * 4, i * 4 + 4))) for i, n in enumerate(names)}
CAP = {'chorus1': 58.45, 'chorus2': 127.9}        # 段尾最后一行不能压到后面的 オオオ
for n, c in CAP.items(): L[n][-1][1] = min(L[n][-1][1], c)

# 200 秒之后不再是歌词段：soul（魂 + 锁链）/ flash（闪回）/ soulvoid（数据柱消散）
S = [
    dict(id='intro',      name='Intro',        start=0,      end=19.46,  world='void', lyric='intro'),
    dict(id='verse1',     name='Verse 1',      start=19.46,  end=31.54,  world='matrix', lyric='verse1', lines=L['verse1']),
    dict(id='pre1',       name='Pre-Chorus 1', start=31.54,  end=41.0,   world='highway', mode='pre', lyric='pre1', lines=L['pre1']),
    dict(id='chorus1',    name='Chorus 1',     start=41.0,   end=58.55,  world='highway', mode='chorus', lyric='chorus1', lines=L['chorus1']),
    dict(id='interlude1', name='オオオ 1',      start=58.55,  end=63.3,   world='hit', lyric='interlude1', pulses=[0.1, 1.3, 2.5]),
    dict(id='break1',     name='Break 1',      start=63.3,   end=71.5,   world='dream'),
    dict(id='cpu',        name='CPU',          start=71.5,   end=79.4,   world='cpu'),
    dict(id='verse2',     name='Verse 2',      start=79.4,   end=89.5,   world='city', mode='verse', lyric='verse2', lines=L['verse2']),
    dict(id='pre2',       name='Pre-Chorus 2', start=89.5,   end=99.15,  world='city', mode='pre', lyric='pre2', lines=L['pre2']),
    dict(id='chorus2',    name='Chorus 2',     start=99.15,  end=128.1,  world='tunnel', lyric='chorus2', lines=L['chorus2']),
    dict(id='interlude2', name='オオオ 2',      start=128.1,  end=132.5,  world='hit', lyric='interlude2', pulses=[0.1, 1.3, 2.5]),
    dict(id='break2',     name='Break 2',      start=132.5,  end=138.5,  world='city', mode='pre'),
    dict(id='bridge',     name='Bridge',       start=138.5,  end=147.75, world='wasteland', lyric='bridge', lines=L['bridge']),
    dict(id='chorus3',    name='Chorus 3',     start=147.75, end=157.5,  world='highway', mode='apex', lyric='chorus3', lines=L['chorus3']),
    dict(id='outro',      name='Outro',        start=157.5,  end=200.0,  world='outro', lyric='outro', lines=L['outro']),
    dict(id='soul',       name='魂 A',          start=200.0,  end=210.0,  world='soul', rounds=[200.826, 203.634, 206.18, 208.422]),
    dict(id='flash',      name='魂 B',          start=210.0,  end=218.0,  world='flash', term=214.85),
    dict(id='soulvoid',   name='魂 C',          start=218.0,  end=226.0,  world='soulvoid'),
    dict(id='endcard',    name='End',          start=226.0,  end=239.72, world='endcard'),
]
p = os.path.join(ROOT, 'web', 'data', 'timing.json')
old = json.load(io.open(p, encoding='utf-8'))
old['sections'] = S
io.open(p, 'w', encoding='utf-8').write(json.dumps(old, ensure_ascii=False, indent=1))
for s in S: print(s['id'], s['start'], s['end'], s.get('lines', ''))
