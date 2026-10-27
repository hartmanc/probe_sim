"""Mid-Ohio round 8, owner note "some grass is missing or is inexplicably dark or gray": the package ortho's ground
pixels 3-40 m beyond each edge (outside the course, the pit lane and the paved zones), per 100 m band and side, classed
as green grass (G over R and B by 3+, saturation >= 0.12), grey (saturation < 0.12: gravel, concrete, washed-out or
shadowed grass), brown / dry (R >= G), dark (luminance under 70: shadow, tree canopy); with the median RGB of the band.
Reference: the in-season frames' grass (360 lap Jul 2025, N837 Apr 2026), sampled in the frames named on the command line.

    uv run --python 3.12 --with numpy,pillow python -I tools/track/compare/mid_ohio/r8/ground_classes.py <package dir> [--json out]
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw
pkg = sys.argv[1]
T = json.load(open(os.path.join(pkg, 'track.json'))); S = json.load(open(os.path.join(pkg, 'scenery.json')))
o = T['ortho']; im = np.asarray(Image.open(os.path.join(pkg, 'ortho.jpg')).convert('RGB')).astype(float); H, W, _ = im.shape
sx = (o['x1'] - o['x0']) / W
paved = Image.new('L', (W, H), 0); d = ImageDraw.Draw(paved)
px = lambda P: [((p[0] - o['x0']) / sx, (o['y1'] - p[1]) / sx) for p in P]
L, R = np.array(T['left'])[:, :2], np.array(T['right'])[:, :2]
d.polygon(px(L), fill=1); d.polygon(px(R), fill=0)
for grp in (S.get('pit_lane') or {}, S.get('paved_zones') or {}):
    for p in grp.get('parts', []):
        d.polygon(px([q[:2] for q in p['left']] + [q[:2] for q in p['right']][::-1]), fill=1)
paved = np.asarray(paved, bool)
C = np.array(T['center'])[:, :2]; n = len(C)
out = []
for side, E in (('left', L), ('right', R)):
    for b0 in range(0, n, 100):
        rows = []
        for i in range(b0, min(n, b0 + 100), 2):
            nrm = (E[i] - C[i]); nrm /= np.linalg.norm(nrm)
            for off in np.arange(3, 41, 1.0):
                p = E[i] + nrm * off; c, r = int((p[0] - o['x0']) / sx), int((o['y1'] - p[1]) / sx)
                if 0 <= r < H and 0 <= c < W and not paved[r, c]: rows.append(im[r, c])
        A = np.array(rows); mx = A.max(1); mn = A.min(1); sat = (mx - mn) / np.maximum(mx, 1); lum = A @ [0.299, 0.587, 0.114]
        green = (A[:, 1] > A[:, 0] + 3) & (A[:, 1] > A[:, 2] + 3) & (sat >= 0.12) & (lum >= 70)
        dark = lum < 70; grey = (sat < 0.12) & ~dark; brown = (A[:, 0] >= A[:, 1]) & ~grey & ~dark
        out.append(dict(side=side, s0=b0, s1=min(n, b0 + 100), green=round(float(green.mean()), 2), grey=round(float(grey.mean()), 2),
                        brown=round(float(brown.mean()), 2), dark=round(float(dark.mean()), 2), rgb=[int(v) for v in np.median(A, 0)]))
for r in out:
    print(f"{r['side']:5s} {r['s0']:4d}-{r['s1']:4d} green {r['green']:.2f} grey {r['grey']:.2f} brown {r['brown']:.2f} dark {r['dark']:.2f} median {r['rgb']}")
if '--json' in sys.argv: json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
