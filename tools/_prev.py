import os, sys, glob
from PIL import Image
src = sys.argv[1]; dst = sys.argv[2]
os.makedirs(dst, exist_ok=True)
for p in sorted(glob.glob(os.path.join(src, '*.png'))):
    im = Image.open(p).convert('RGB').resize((960, 540), Image.LANCZOS)
    im.save(os.path.join(dst, os.path.basename(p)[:-4] + '.jpg'), quality=82)
    print('ok', os.path.basename(p))
