import json, numpy as np, sys
d = json.load(open(r'D:\AI\GhostChain MV\GhostChain_MV\web\data\features.json'))
fps = d['fps']
def per_sec(k):
    a = np.array(d[k])/255.0; n = len(a)//fps
    return a[:n*fps].reshape(n, fps).mean(1)
for k in ['vox', 'low', 'high']:
    s = per_sec(k)
    print(k)
    for r in range(0, len(s), 30):
        row = s[r:r+30]
        print('%3d-%3d ' % (r, r+len(row)-1) + ''.join(str(min(9, int(v*10))) for v in row))
# vox activity spans, 0.25 s resolution
a = np.array(d['vox'])/255.0; w = fps//4
b = a[:len(a)//w*w].reshape(-1, w).mean(1)
thr = float(sys.argv[1]) if len(sys.argv) > 1 else 0.35
on = b > thr
spans = []; st = None
for i, v in enumerate(on):
    if v and st is None: st = i
    if not v and st is not None:
        spans.append((st*0.25, i*0.25)); st = None
if st is not None: spans.append((st*0.25, len(on)*0.25))
# merge gaps < 0.75s
m = []
for s_, e_ in spans:
    if m and s_ - m[-1][1] < 0.75: m[-1] = (m[-1][0], e_)
    else: m.append((s_, e_))
print('spans', [(round(s_, 2), round(e_, 2)) for s_, e_ in m if e_-s_ >= 0.75])
