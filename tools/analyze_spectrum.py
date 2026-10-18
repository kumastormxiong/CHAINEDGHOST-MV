"""生成 web/data/spectrum.json：每 1/60 秒一帧，32 个对数频段的响度（0–255）。结束页的频谱光圈使用。
用法：python tools/analyze_spectrum.py
只依赖 numpy / scipy（与 analyze_audio.py 相同）。
"""
import os, json
import numpy as np
from scipy.io import wavfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wav = os.path.join(ROOT, 'web', 'audio', 'GhostChain.wav')
out = os.path.join(ROOT, 'web', 'data', 'spectrum.json')
BANDS = 32
FPS = 60
N_FFT = 2048

sr, x = wavfile.read(wav)
x = x.astype(np.float32) / 32768.0
m = x.mean(axis=1) if x.ndim == 2 else x
hop = sr // FPS
n = len(m) // hop
win = np.hanning(N_FFT).astype(np.float32)
freqs = np.fft.rfftfreq(N_FFT, 1.0 / sr)
edges = np.geomspace(35.0, min(16000.0, sr / 2 - 100), BANDS + 1)
bins_per_band = []
for i in range(BANDS):
    idx = np.where((freqs >= edges[i]) & (freqs < edges[i + 1]))[0]
    if len(idx) == 0:                      # 低频窄带：取最近的一个频点
        idx = np.array([int(np.argmin(np.abs(freqs - np.sqrt(edges[i] * edges[i + 1]))))])
    bins_per_band.append(idx)

pad = np.pad(m, (N_FFT // 2, N_FFT))
db = np.zeros((n, BANDS), np.float32)
for i in range(n):
    seg = pad[i * hop: i * hop + N_FFT] * win
    p = np.abs(np.fft.rfft(seg)) ** 2
    db[i] = [10 * np.log10(p[idx].mean() + 1e-12) for idx in bins_per_band]

lo = np.percentile(db, 3, axis=0)
hi = np.percentile(db, 99.5, axis=0)
v = np.clip((db - lo) / (hi - lo + 1e-6), 0, 1) ** 1.3
q = (v * 255).astype(int)

os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w') as f:
    json.dump({'fps': FPS, 'bands': BANDS, 'n': int(n), 'data': q.tolist()}, f, separators=(',', ':'))
print('frames', n, 'bands', BANDS, '->', out)
