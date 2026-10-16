"""分析音频，生成 web/data/features.json（60Hz 响度包络 + 鼓点/重音时间）。
用法：python tools/analyze_audio.py
只依赖 numpy / scipy。画面里的闪光、故障、镜头冲击都由这些数据驱动。
"""
import os, json
import numpy as np
from scipy import signal
from scipy.io import wavfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
wav = os.path.join(ROOT, 'web', 'audio', 'GhostChain.wav')
out = os.path.join(ROOT, 'web', 'data', 'features.json')

sr, x = wavfile.read(wav)
x = x.astype(np.float32) / 32768.0
m = x.mean(axis=1) if x.ndim == 2 else x
FPS = 60
hop = sr // FPS
n = len(m) // hop


def band(lo, hi):
    sos = signal.butter(4, [lo, hi], 'band', fs=sr, output='sos')
    return signal.sosfilt(sos, m)


def env(y):
    e = np.sqrt((y[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12)
    return e


def norm(e):
    lo, hi = np.percentile(e, 5), np.percentile(e, 98)
    return np.clip((e - lo) / (hi - lo + 1e-9), 0, 1)


low = norm(env(band(30, 150)))
mid = norm(env(band(200, 2000)))
vox = norm(env(band(300, 3400)))
high = norm(env(band(4500, 14000)))

# 低频起音（鼓点）与全频起音（重音）
def flux_of(y, nper=1024):
    f, t, Z = signal.stft(y, sr, nperseg=nper, noverlap=nper - hop)
    S = np.log1p(np.abs(Z) * 40)
    fl = np.maximum(0, np.diff(S, axis=1)).sum(0)
    fl = np.concatenate([[0], fl])[:n]
    fl = fl - signal.medfilt(fl, 21)
    return np.maximum(fl, 0)


def peaks(fl, thr_pct, dist_s):
    thr = np.percentile(fl, thr_pct)
    pk, _ = signal.find_peaks(fl, height=thr, distance=int(dist_s * FPS))
    return (pk / FPS).round(3).tolist()


fl_low = flux_of(band(30, 180))
fl_all = flux_of(m)
kicks = peaks(fl_low, 88, 0.18)
hits = peaks(fl_all, 90, 0.10)
flux = norm(fl_all)


def q(a):
    return (np.clip(a, 0, 1) * 255).astype(int).tolist()

data = {'fps': FPS, 'n': int(n), 'duration': round(len(m) / sr, 3),
        'low': q(low), 'mid': q(mid), 'vox': q(vox), 'high': q(high), 'flux': q(flux),
        'kicks': kicks, 'hits': hits}
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, 'w') as f:
    json.dump(data, f, separators=(',', ':'))
print('frames', n, 'kicks', len(kicks), 'hits', len(hits), '->', out)
