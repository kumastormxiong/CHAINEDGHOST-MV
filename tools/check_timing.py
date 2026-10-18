"""检查逐字打点：每个段落的每个假名是否都打了点；假名时间是否落在该段的起止时间之内。
用法：python tools/check_timing.py
注意：歌词只在"当前所在段落"内显示，所以假名时间超出段落范围时，这一行不会出现。
"""
import os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.join(ROOT, 'web', 'data')
ly = json.load(open(os.path.join(W, 'lyrics.json'), encoding='utf-8'))
tm = json.load(open(os.path.join(W, 'timing.json'), encoding='utf-8'))
ct = json.load(open(os.path.join(W, 'char_times.json'), encoding='utf-8')).get('times', {})
blocks = {b['id']: b for b in ly['blocks']}
total, problems = 0, []
for s in tm['sections']:
    blk = blocks.get(s.get('lyric'))
    if not blk:
        print(f"{s['id']:<12} {s['start']:>8} - {s['end']:<8} (no lyric)")
        continue
    rows = [r for r in blk['rows'] if len(r) >= 3 and all(len(x) == 1 for x in r)]
    if s.get('lines'):
        o = s.get('rowOffset', 0)
        rows = rows[o:o + len(s['lines'])]
    timed, outside, missing = 0, 0, 0
    for ri, r in enumerate(rows):
        row_t = []
        for ci in range(len(r)):
            k = f"{s['id']}:{ri}:{ci}"
            total += 1
            if k not in ct:
                missing += 1
                continue
            timed += 1
            row_t.append(ct[k])
            if ct[k] < s['start'] or ct[k] > s['end']:
                outside += 1
        if row_t:
            print(f"  {s['id']:<12} row {ri}: {min(row_t):8.3f} - {max(row_t):8.3f}")
    print(f"{s['id']:<12} {s['start']:>8} - {s['end']:<8} kana timed {timed}/{timed + missing}  outside section {outside}")
    if missing or outside:
        problems.append(s['id'])
print('total kana', total, '| sections with problems:', problems or 'none')
