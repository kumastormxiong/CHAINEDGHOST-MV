"""程序化绘制"眼睛"素材（参考图的漂浮大眼睛）：巩膜 + 眼线/睫毛/滴漆 + 多种虹膜。输出到 web/assets/eyes/。
three.js 里用 makeEye() 把三张图合成：虹膜可以转动（看向镜头）、可以眨眼。
用法：python tools/make_eyes.py [输出目录]
"""
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'web', 'assets', 'eyes')
os.makedirs(out, exist_ok=True)
W, H = 1024, 512
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
cx, cy = W / 2, H / 2
X = (xx - cx) / 440.0                # 归一化到 [-1,1]
Y = (yy - cy) / 170.0


def lid_top(x):   # 上眼睑曲线（稍饱满，外眼角略高）
    return -(1 - np.clip(x, -1, 1) ** 2) ** 0.85 * 1.0 - 0.10 * x


def lid_bot(x):
    return (1 - np.clip(x, -1, 1) ** 2) ** 0.9 * 0.82 - 0.10 * x


inside = (np.abs(X) < 1) & (Y > lid_top(X)) & (Y < lid_bot(X))
ins_f = ndi.gaussian_filter(inside.astype(np.float32), 1.2)


def save(arr, name):
    Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8), 'RGBA').save(os.path.join(out, name))


# ---------- 巩膜：偏冷的白，靠近上眼睑有阴影，眼角微粉 ----------
t = np.clip((Y - lid_top(X)) / (lid_bot(X) - lid_top(X) + 1e-3), 0, 1)
shade = 0.62 + 0.38 * np.clip(np.sin(t * math.pi), 0, 1) ** 0.6
sc = np.zeros((H, W, 4), np.float32)
base = np.array([0.93, 0.95, 1.0], np.float32)
corner = np.clip((np.abs(X) - 0.65) * 2.2, 0, 1)[..., None] * np.array([0.35, -0.05, -0.02], np.float32)
sc[..., :3] = (base * shade[..., None] + corner) * ins_f[..., None]
# 细小血丝/涂抹噪点
rng = np.random.default_rng(3)
nz = ndi.gaussian_filter(rng.random((H, W)).astype(np.float32), 5); nz = (nz - nz.mean()) * 6
sc[..., :3] += (nz[..., None] * np.array([0.25, 0.0, 0.1], np.float32)) * ins_f[..., None] * 0.5
sc[..., 3] = ins_f
save(sc, 'eye_sclera.png')

# ---------- 眼线 / 睫毛 / 滴漆（霓虹外发光烘焙进去）----------
def line_layer(neon, name):
    big = Image.new('L', (W * 2, H * 2), 0); d = ImageDraw.Draw(big)
    xs = np.linspace(-1.0, 1.0, 160)
    top = [(cx * 2 + x * 440 * 2, cy * 2 + lid_top(x) * 170 * 2) for x in xs]
    bot = [(cx * 2 + x * 440 * 2, cy * 2 + lid_bot(x) * 170 * 2) for x in xs]
    d.line(top, fill=255, width=34, joint='curve')           # 上眼线：粗
    d.line(bot, fill=170, width=14, joint='curve')           # 下眼线：细
    for i in range(15):                                       # 睫毛
        x = -0.85 + i * 0.125; lx = cx * 2 + x * 880; ly = cy * 2 + lid_top(x) * 340
        ang = math.radians(-100 + x * 38 - 6 * math.sin(i)); ln = 70 + 40 * math.sin(i * 1.7) ** 2
        d.line([(lx, ly), (lx + math.cos(ang) * ln, ly + math.sin(ang) * ln)], fill=255, width=12)
    for x0 in (-0.55, -0.1, 0.45):                            # 下眼睑滴漆
        lx = cx * 2 + x0 * 880; ly = cy * 2 + lid_bot(x0) * 340
        ln = 90 + 90 * abs(math.sin(x0 * 9)); d.line([(lx, ly), (lx, ly + ln)], fill=255, width=14)
        d.ellipse([lx - 14, ly + ln - 10, lx + 14, ly + ln + 18], fill=255)
    m = np.array(big.resize((W, H), Image.LANCZOS)).astype(np.float32) / 255
    glow = ndi.gaussian_filter(m, 9) * 1.6
    glow2 = ndi.gaussian_filter(m, 22) * 1.2
    dark = np.array([0.04, 0.0, 0.1], np.float32)
    nc = np.array(neon, np.float32)
    rgb = dark * m[..., None] + nc * np.clip(glow + glow2 - m * 1.2, 0, 1)[..., None]
    a = np.clip(m + np.clip(glow + glow2 - m, 0, 1) * 0.95, 0, 1)
    arr = np.dstack([rgb / np.maximum(a[..., None], 1e-3), a]); arr[..., :3] = np.clip(arr[..., :3], 0, 1)
    save(arr, name)

line_layer([1.0, 0.18, 0.65], 'eye_line_pink.png')
line_layer([0.1, 0.9, 1.0], 'eye_line_cyan.png')


# ---------- 虹膜（整张 1024x512，中心在画面中心；着色器里按 uv 平移）----------
def iris(kind, name):
    R = 168.0
    r = np.hypot(xx - cx, yy - cy) / R
    ang = np.arctan2(yy - cy, xx - cx)
    nz1 = ndi.gaussian_filter(rng.random((H, W)).astype(np.float32), 2); nz1 = (nz1 - 0.5) * 3
    fib = 0.5 + 0.5 * np.sin(ang * 48 + nz1 * 3)
    rgb = np.zeros((H, W, 3), np.float32)
    if kind in ('blue', 'red', 'orange'):
        pal = {'blue': ([0.05, 0.12, 0.55], [0.1, 0.55, 1.0], [0.8, 0.95, 1.0]),
               'red': ([0.35, 0.02, 0.08], [0.95, 0.2, 0.15], [1.0, 0.75, 0.4]),
               'orange': ([0.35, 0.08, 0.02], [1.0, 0.45, 0.1], [1.0, 0.9, 0.5])}[kind]
        c0, c1, c2 = [np.array(p, np.float32) for p in pal]
        g = np.clip(r, 0, 1)[..., None]
        rgb = c0 * (1 - g) ** 0.4 * 0.0 + (c1 * (0.35 + 0.65 * fib[..., None]) * (1 - np.clip((g - 0.55) / 0.45, 0, 1)) + c0 * np.clip((g - 0.55) / 0.45, 0, 1) * 1.0)
        rgb += c2 * np.exp(-((r - 0.42) / 0.12) ** 2)[..., None] * 0.7                     # 瞳孔外亮环
        if kind == 'red':   # 参考图 1：红色放射星
            rgb += np.array([1.0, 0.25, 0.1], np.float32) * (np.clip(np.abs(np.sin(ang * 6)) ** 8 * (1 - r / 0.6), 0, 1))[..., None] * (r < 0.6)[..., None]
    else:               # 参考图 2：同心圆 / 迷宫环
        c_a = np.array([0.1, 0.9, 1.0], np.float32) if kind == 'ring_cyan' else np.array([1.0, 0.25, 0.7], np.float32)
        c_b = np.array([1.0, 0.55, 0.15], np.float32)
        k = np.sin(r * 28 + nz1 * 0.4) * 0.5 + 0.5
        ringmask = np.clip((k - 0.45) * 5, 0, 1)
        rgb = (np.array([0.03, 0.0, 0.12], np.float32) + c_a * ringmask[..., None] * 0.95 + c_b * (np.clip(np.sin(ang * 5 + r * 6) * 0.5 + 0.5 - 0.7, 0, 1) * 2.2)[..., None] * 0.6)
    pupil = r < 0.32
    rgb[pupil] = np.array([0.01, 0.0, 0.03], np.float32)
    rgb *= (1 - 0.35 * np.clip((r - 0.85) / 0.15, 0, 1))[..., None]
    # 高光
    for hx, hy, hr in [(-0.38, -0.40, 0.2), (0.28, 0.32, 0.09)]:
        hl = np.exp(-(np.hypot(xx - cx - hx * R, yy - cy - hy * R) / (hr * R)) ** 4)
        rgb = rgb * (1 - hl[..., None]) + hl[..., None]
    a = ndi.gaussian_filter((r < 1.0).astype(np.float32), 1.0)
    # 虹膜外缘暗描边
    edge = np.clip(1 - np.abs(r - 0.97) / 0.05, 0, 1)
    rgb = rgb * (1 - edge[..., None] * 0.8)
    save(np.dstack([np.clip(rgb, 0, 1), a]), name)

for k in ('blue', 'red', 'orange', 'ring_cyan', 'ring_pink'):
    iris(k, f'iris_{k}.png')
print('eyes ->', os.listdir(out))
