"""Contact sheets of inventory frames for reading (reference only, local): rows = times, columns = views.
    python -I sheet.py --dir <frames> --times 0:144:2 --views left,ahead,right,back --per 6 --w 400 --out <dir> [--pattern t{t:03d}_{v}.jpg]"""
import argparse, os
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser()
ap.add_argument('--dir', required=True); ap.add_argument('--out', required=True); ap.add_argument('--times', required=True)
ap.add_argument('--views', default='left,ahead,right,back'); ap.add_argument('--per', type=int, default=6)
ap.add_argument('--w', type=int, default=400); ap.add_argument('--pattern', default='t{t:03d}_{v}.jpg'); ap.add_argument('--tag', default='sheet')
a = ap.parse_args()
if ':' in a.times:
    t0, t1, st = (float(x) for x in a.times.split(':')); ts = []
    t = t0
    while t <= t1 + 1e-9: ts.append(t); t += st
else:
    ts = [float(x) for x in a.times.split(',')]
vs = a.views.split(','); os.makedirs(a.out, exist_ok=True)
for k in range(0, len(ts), a.per):
    chunk = ts[k:k + a.per]; cells = []
    for t in chunk:
        row = []
        for v in vs:
            fp = os.path.join(a.dir, a.pattern.format(t=int(round(t)), v=v, ms=int(round(t * 1000))))
            im = Image.open(fp).convert('RGB') if os.path.exists(fp) else Image.new('RGB', (16, 10))
            im = im.resize((a.w, int(a.w * im.height / im.width)))
            ImageDraw.Draw(im).text((4, 4), f't{t:g} {v}', fill=(255, 255, 0))
            row.append(im)
        cells.append(row)
    h = max(im.height for r in cells for im in r)
    S = Image.new('RGB', (a.w * len(vs), h * len(cells)))
    for i, r in enumerate(cells):
        for j, im in enumerate(r):
            S.paste(im, (j * a.w, i * h))
    S.save(os.path.join(a.out, f'{a.tag}_{int(chunk[0]):03d}.jpg'), quality=85)
print('ok')
