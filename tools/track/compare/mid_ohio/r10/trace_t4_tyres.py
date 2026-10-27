"""Mid-Ohio round 10 (owner drive of round 9: "a tire wall at the far end of China Beach ... I see the tell-tale black line on
the ground"): trace the black-and-white tyre wall that stands along the far (north-east) edge of the T4 sand trap in the
2022 NAIP ortho. A coarse guide (read off the ortho, ENU) is densified to 1 m; at each point the wall centre is the darkest
smoothed (1.5 m) ortho luminance within +-3 m of the guide along its normal (the wall is the dark band between the bright
sand and the track-side gravel path); the points are median-filtered (9) and thinned to 4 m. Prints the lat/lon list.
    uv run --python 3.12 --with numpy,scipy,pillow python -I trace_t4_tyres.py <package dir> [--png out.png]"""
import json, math, sys, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
pkg = sys.argv[1]
T = json.load(open(os.path.join(pkg, 'track.json'))); o = T['ortho']
im = np.asarray(Image.open(os.path.join(pkg, 'ortho.jpg')).convert('L')).astype(np.float32); H, W = im.shape
sm = ndi.gaussian_filter(im, 1.5 / ((o['x1'] - o['x0']) / W))
def px(x, y): return (x - o['x0']) / (o['x1'] - o['x0']) * W - 0.5, (o['y1'] - y) / (o['y1'] - o['y0']) * H - 0.5
THR = 95.0   # luminance below which the ortho is tyre / soil, not sand (the sand reads 130-170)
GUIDE = [(-171.8, 469.4), (-147.5, 471.9), (-125.9, 466.1), (-109.7, 453.5), (-99.8, 440.9), (-95.3, 429.2)]   # ENU read off the ortho
G = np.array(GUIDE); seg = np.hypot(*np.diff(G, axis=0).T); L = np.r_[0, np.cumsum(seg)]
t = np.arange(0, L[-1], 1.0); P = np.c_[np.interp(t, L, G[:, 0]), np.interp(t, L, G[:, 1])]
d = np.gradient(P, axis=0); d /= np.linalg.norm(d, axis=1)[:, None]; N = np.c_[-d[:, 1], d[:, 0]]
C0 = np.array([-140.0, 425.0]); sgn = np.sign(((P - C0) * N).sum(1)); N = N * sgn[:, None]    # normals point out of the trap
sm = ndi.gaussian_filter(im, 0.8 / ((o['x1'] - o['x0']) / W))
off = np.arange(-4, 4.01, 0.2); best = []
for p, n in zip(P, N):
    q = p[None] + off[:, None] * n[None]; c, r = px(q[:, 0], q[:, 1])
    v = ndi.map_coordinates(sm, [r, c], order=1)
    k = np.flatnonzero(v < THR); best.append(off[k[0]] + 1.0 if len(k) else 0.0)   # the sand's edge (first dark pixel going out) + half the wall
best = ndi.median_filter(np.array(best), 9, mode='nearest'); Q = P + best[:, None] * N
Q = Q[::4]
R_E = 6378137.0; LAT0, LON0 = T['origin']['lat'], T['origin']['lon']
ll = [(round(LAT0 + math.degrees(y / R_E), 7), round(LON0 + math.degrees(x / (R_E * math.cos(math.radians(LAT0)))), 7)) for x, y in Q]
print('length', round(float(np.hypot(*np.diff(Q, axis=0).T).sum()), 1), 'm; offset from the guide median', round(float(np.median(best)), 2), 'm, max', round(float(np.abs(best).max()), 2))
print(ll)
if '--png' in sys.argv:
    a = px(-230, 520); b = px(-60, 400); im0 = Image.open(os.path.join(pkg, 'ortho.jpg')).convert('RGB').crop((int(a[0]), int(a[1]), int(b[0]), int(b[1])))
    sc = 1200 / im0.width; im0 = im0.resize((1200, int(im0.height * sc)), Image.LANCZOS); dr = ImageDraw.Draw(im0)
    dr.line([((px(*q)[0] - a[0]) * sc, (px(*q)[1] - a[1]) * sc) for q in Q], fill=(255, 0, 255), width=2); im0.save(sys.argv[sys.argv.index('--png') + 1])
