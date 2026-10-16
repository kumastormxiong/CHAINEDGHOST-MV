"""程序化绘制"女孩剪影"（全年龄：长外套 + 长裙，不画面部细节），输出 RGBA 到 web/assets/girl_ghost.png
轮廓 = 样条曲线；内部填充 = 星云渐变 + 青色网格（参考图 2 的"网格皮肤"）+ 橙色流动描边（参考图 2）。
用法：python tools/make_girl.py [输出路径]
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

W, H, SS = 900, 1300, 3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'web', 'assets', 'girl_ghost.png')


def cr(points, closed=True, n=14):
    """Catmull-Rom 样条，返回密集折线"""
    P = list(points)
    if closed:
        P = [P[-1]] + P + [P[0], P[1]]
    else:
        P = [P[0]] + P + [P[-1]]
    res = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = [np.array(p, float) for p in P[i - 1:i + 3]]
        for k in range(n):
            t = k / n
            res.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    if not closed:
        res.append(np.array(P[-2], float))
    return [tuple(p * SS) for p in res]


mask = Image.new('L', (W * SS, H * SS), 0)
d = ImageDraw.Draw(mask)


def poly(pts, closed=True):
    d.polygon(cr(pts, closed), fill=255)


def stroke(pts, width, closed=False):
    c = cr(pts, closed)
    d.line(c, fill=255, width=int(width * SS), joint='curve')
    r = width * SS / 2
    for q in (c[0], c[-1]):
        d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=255)


# ---------- 躯干（oversized 外套）----------
poly([(372, 372), (430, 352), (500, 372), (520, 470), (528, 600), (545, 700), (330, 700), (338, 590), (350, 470)])
# ---------- 裙摆（长裙，波浪下摆）----------
poly([(335, 690), (545, 690), (610, 820), (650, 950), (600, 1010), (560, 985), (520, 1040), (470, 1000), (430, 1050), (380, 1000), (330, 1030), (290, 960), (270, 900), (300, 790)])
# ---------- 腿（长裙下露出的小腿，穿长靴 -> 全包裹）----------
poly([(420, 1000), (470, 1000), (500, 1110), (520, 1215), (535, 1250), (470, 1262), (450, 1240), (445, 1120)])
poly([(360, 1005), (410, 1000), (400, 1090), (350, 1175), (330, 1225), (270, 1215), (275, 1190), (320, 1130), (345, 1070)])
# ---------- 脖子、头 ----------
poly([(412, 300), (452, 300), (458, 372), (418, 380)])
poly([(352, 250), (360, 190), (402, 150), (456, 150), (500, 190), (508, 250), (490, 300), (452, 326), (412, 322), (385, 305), (366, 285)])
# 侧脸小鼻子（朝左）
poly([(356, 262), (338, 276), (350, 286), (362, 284)])
# ---------- 前伸的手臂（朝左上）----------
poly([(372, 392), (330, 372), (250, 330), (180, 288), (150, 268), (132, 276), (140, 300), (150, 322), (210, 356), (262, 410), (318, 470), (368, 490)])
# 手：五指分开（简化为扇形细指）
for ang, ln in [(-40, 60), (-20, 70), (0, 74), (20, 66), (42, 50)]:
    a = math.radians(ang - 150)
    bx, by = 138, 284
    stroke([(bx, by), (bx + math.cos(a) * ln, by + math.sin(a) * ln)], 11)
# ---------- 后方手臂（垂向后下）----------
poly([(508, 392), (560, 430), (590, 520), (600, 610), (586, 640), (556, 620), (540, 540), (520, 470)])
# ---------- 衣领与外套下摆飘带 ----------
poly([(360, 650), (330, 760), (250, 850), (200, 940), (232, 930), (300, 880), (350, 820), (380, 700)])
poly([(540, 640), (590, 760), (700, 860), (760, 980), (720, 975), (640, 920), (580, 820), (520, 700)])

# ---------- 长发（多股，向右后方飘）----------
poly([(358, 214), (380, 150), (440, 120), (510, 140), (560, 190), (600, 250), (640, 330), (700, 420), (760, 540), (790, 660), (770, 700), (730, 640), (690, 560), (640, 500), (590, 470), (540, 400), (505, 340), (498, 270)])
poly([(500, 200), (560, 190), (640, 230), (720, 310), (800, 420), (850, 540), (860, 640), (830, 650), (800, 580), (750, 500), (680, 420), (610, 340), (540, 290)])
poly([(520, 330), (580, 380), (640, 470), (700, 600), (730, 740), (710, 780), (680, 700), (620, 600), (560, 520), (520, 440)])
poly([(520, 380), (560, 470), (590, 620), (580, 760), (540, 820), (524, 700), (520, 560)])
# 前额刘海
poly([(358, 214), (370, 170), (410, 150), (440, 190), (420, 240), (392, 250)])
# 两缕贴着发梢的飘发（短而粗，避免孤立细线）
stroke([(560, 230), (700, 215), (800, 250)], 14)
stroke([(600, 330), (740, 380), (815, 470)], 12)

mask = mask.resize((W, H), Image.LANCZOS)
m = np.array(mask).astype(np.float32) / 255.0

# ---------- 内部填充：星云 + 网格 ----------
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
def fbm(scale, octv=5, seed=0):
    r = np.random.default_rng(seed); acc = np.zeros((H, W), np.float32); amp = 1.0; tot = 0
    for o in range(octv):
        s = max(2, int(min(H, W) / (scale / (2 ** o))))
        g = r.random((s, int(s * W / H) + 2)).astype(np.float32)
        z = ndi.zoom(g, (H / g.shape[0], W / g.shape[1]), order=3)[:H, :W]
        acc += z * amp; tot += amp; amp *= 0.5
    return acc / tot
n1, n2 = fbm(220, 5, 1), fbm(120, 5, 2)
def lerp3(a, b, t): return a + (b - a) * t[..., None]
base = np.zeros((H, W, 3), np.float32) + np.array([0.04, 0.02, 0.16], np.float32)
c_pink = np.array([1.0, 0.18, 0.62], np.float32); c_cyan = np.array([0.1, 0.85, 1.0], np.float32); c_orange = np.array([1.0, 0.5, 0.12], np.float32); c_vio = np.array([0.35, 0.1, 0.8], np.float32)
col = lerp3(base, c_vio, np.clip((n1 - 0.35) * 2.2, 0, 1))
col = lerp3(col, c_pink, np.clip((n2 - 0.52) * 3.0, 0, 1) * 0.85)
col = lerp3(col, c_cyan, np.clip((fbm(160, 4, 5) - 0.55) * 3.2, 0, 1) * 0.8)
col = lerp3(col, c_orange, np.clip((fbm(260, 3, 9) - 0.62) * 4.0, 0, 1) * 0.7)
# 星点
st = (rng.random((H, W)) > 0.9992).astype(np.float32); st = ndi.gaussian_filter(st, 0.8) * 6
col += st[..., None]
# 网格皮肤（沿着人体做轻微弯曲）
gx = np.abs(((xx + 22 * np.sin(yy * 0.012)) % 46) - 23); gy = np.abs(((yy + 14 * np.sin(xx * 0.015)) % 46) - 23)
grid = np.clip(1.4 - np.minimum(gx, gy) / 1.6, 0, 1)
col = col + grid[..., None] * np.array([0.1, 0.9, 1.0], np.float32) * 0.5
col = np.clip(col, 0, 1.4)

# ---------- 描边：橙色流动线 + 青色内描边 ----------
dist_in = ndi.distance_transform_edt(m > 0.5)
rim_o = np.clip(1 - np.abs(dist_in - 3.0) / 2.2, 0, 1) * (m > 0.5)
rim_c = np.clip(1 - np.abs(dist_in - 11.0) / 1.6, 0, 1) * (m > 0.5) * (0.5 + 0.5 * np.sin(xx * 0.03 + yy * 0.045))
col = col * (1 - rim_o[..., None] * 0.9) + rim_o[..., None] * np.array([1.0, 0.55, 0.15], np.float32) * 1.2
col = col + rim_c[..., None] * np.array([0.1, 0.9, 1.0], np.float32) * 0.7
# 颜料滴落：沿下边缘向下的细滴
alpha = ndi.gaussian_filter(m, 0.8)
drip_src = (m > 0.5) & (rng.random((H, W)) > 0.9996)
alpha_img = alpha.copy()
ys, xs = np.where(drip_src & (dist_in < 4))
for y0, x0 in zip(ys, xs):
    ln = int(rng.integers(18, 70)); w = int(rng.integers(3, 6))
    y1 = min(H - 1, y0 + ln)
    alpha_img[y0:y1, max(0, x0 - w // 2):x0 + w // 2 + 1] = 1.0
    col[y0:y1, max(0, x0 - w // 2):x0 + w // 2 + 1] = np.array([1.0, 0.5, 0.15], np.float32)
a8 = (np.clip(alpha_img, 0, 1) * 255).astype(np.uint8)
rgb = (np.clip(col, 0, 1) * 255).astype(np.uint8)
ys, xs = np.where(a8 > 8)
y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
img = Image.fromarray(np.dstack([rgb, a8])[y0:y1, x0:x1], 'RGBA')
img.save(out)
print('saved', out, img.size)
