"""把头像抠成"幽灵剪影"（透明背景），供 three.js 场景使用。
用法：python tools/make_ghost.py
输入：web/assets/avatar_full.png（原头像）
输出：web/assets/avatar_ghost.png（只保留剪影+星云，去掉白底和蓝环）
"""
import os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(ROOT, 'web', 'assets', 'avatar_full.png')
dst = os.path.join(ROOT, 'web', 'assets', 'avatar_ghost.png')

im = Image.open(src).convert('RGBA')
a = np.array(im).astype(np.float32)
H, W = a.shape[:2]
yy, xx = np.mgrid[0:H, 0:W]
r = np.hypot(yy - H / 2, xx - W / 2) / W
rgb = a[..., :3]

inside = r < 0.372                       # 白色内圆
white = rgb.min(axis=2) > 225            # 近白像素
cand = white & inside
lab, n = ndi.label(cand)
edge = (r > 0.345) & (r < 0.372)         # 白底一定会碰到内圆边缘
ids = np.unique(lab[edge & cand])
ids = ids[ids > 0]
bg = np.isin(lab, ids)                   # 和边缘相连的白 = 背景；内部的白(音符、星点)保留
alpha = np.where(inside & ~bg, 1.0, 0.0)
alpha = ndi.gaussian_filter(alpha, 1.3)
alpha = np.clip((alpha - 0.4) / 0.45, 0, 1)

ys, xs = np.where(alpha > 0.05)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
out = np.dstack([rgb, alpha * 255]).astype(np.uint8)[y0:y1, x0:x1]
img = Image.fromarray(out, 'RGBA')
scale = 1100 / img.height
img = img.resize((int(img.width * scale), 1100), Image.LANCZOS)
img.save(dst)
print('saved', dst, img.size)
