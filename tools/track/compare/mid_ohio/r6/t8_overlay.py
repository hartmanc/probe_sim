"""Mid-Ohio round 6, T8: the centre, the solver's line and the real cars' positions (r6/t8_observed.json) over the clean
2026 capture (capwin.py --raw), with the race edges; and the radius of a smooth line through the real positions.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/mid_ohio/r6/t8_overlay.py <package dir> <out.png> <out.json>
"""
import json
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.interpolate import UnivariateSpline

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
pkg, out_png, out_json = sys.argv[1:4]
T = json.load(open(os.path.join(pkg, 'track.json')))
G = json.load(open(os.path.join(pkg, 'ghosts.json')))
OBS = json.load(open(os.path.join(HERE, 't8_observed.json')))
C = np.array(T['center'])[:, :2]; Lf = np.array(T['left'])[:, :2]; Rt = np.array(T['right'])[:, :2]
n, sp = T['n'], T['spacing_m']
off = np.array(G['line']['offset_m']); ds = G['s_grid_m']; m = len(off)
S0, HALF, MPP = 2515, 85.0, 0.1
raw = '/tmp/mo_r6_t8_raw.png'
subprocess.run(['uv', 'run', '--python', '3.12', '--with', 'numpy,scipy,pillow', 'python', '-I',
                os.path.join(ROOT, 'tools/track/compare/capwin.py'), '--track', 'mid_ohio', '--pkg', pkg, '--s', str(S0),
                '--half', str(HALF), '--mpp', str(MPP), '--raw', '--out', raw], check=True, cwd=ROOT)
im = Image.open(raw).convert('RGB'); d = ImageDraw.Draw(im)
cx, cy = C[int(round(S0 / sp)) % n]
px = lambda x, y: ((x - (cx - HALF)) / MPP, ((cy + HALF) - y) / MPP)  # noqa: E731
tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
NL = np.c_[-tg[:, 1], tg[:, 0]]


def line_off(s):
    u = s / ds; i = int(math.floor(u)) % m; f = u - math.floor(u)
    return (1 - f) * off[i] + f * off[(i + 1) % m]


def at(s, e):
    i = int(round(s / sp)) % n
    return C[i] + e * NL[i]


S = np.arange(2380, 2700, 1.0)
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 22) if os.path.exists('/System/Library/Fonts/Supplemental/Arial.ttf') else None
for E, col in ((Lf, (255, 40, 40)), (Rt, (255, 40, 40))):
    P = [px(*E[int(round(s / sp)) % n]) for s in S]
    d.line(P, fill=col, width=3)
P = [px(*at(s, 0)) for s in S]
for k in range(0, len(P) - 1, 6):
    d.line(P[k:k + 4], fill=(255, 255, 255), width=3)
P = [px(*at(s, line_off(s))) for s in S]
d.line(P, fill=(0, 230, 255), width=4)
# the smooth line through the real positions (360 lap + N837 + IndyCar pooled), anchored at the solver's T7 and T9 apexes
pts = [(o['s'], o['offset_m']) for o in OBS['observations'] if o['s'] is not None]
anch = [(s, line_off(s)) for s in (2380, 2390, 2400, 2640, 2650, 2660)]
xs = np.array([p[0] for p in pts + anch]); ys = np.array([p[1] for p in pts + anch]); o = np.argsort(xs)
w = np.array([1.0] * len(pts) + [3.0] * len(anch))[o]
spl = UnivariateSpline(xs[o], ys[o], w=w, k=3, s=len(xs) * 1.0)
Q = [px(*at(s, float(spl(s)))) for s in S]
d.line(Q, fill=(255, 140, 0), width=4)
col = {'N837': (255, 230, 0), '360': (255, 0, 255), 'Indy': (0, 255, 0)}
for ob in OBS['observations']:
    if ob['s'] is None:
        continue
    c = next(v for k, v in col.items() if ob['car'].startswith(k))
    x, y = px(*at(ob['s'], ob['offset_m']))
    d.ellipse((x - 9, y - 9, x + 9, y + 9), outline=(0, 0, 0), fill=c, width=2)


def radius_series(eofs):
    Pt = np.array([at(s, e) for s, e in zip(S, eofs)])
    R = []
    for k in range(10, len(S) - 10):
        a, b, c_ = Pt[k - 10], Pt[k], Pt[k + 10]
        ab, bc, ac = np.linalg.norm(b - a), np.linalg.norm(c_ - b), np.linalg.norm(c_ - a)
        cr = (b[0] - a[0]) * (c_[1] - a[1]) - (b[1] - a[1]) * (c_[0] - a[0])
        R.append((S[k], ab * bc * ac / (2 * cr) if abs(cr) > 1e-9 else 1e9))
    return R


Rs = radius_series([line_off(s) for s in S]); Ro = radius_series([float(spl(s)) for s in S]); Rc = radius_series([0.0] * len(S))
t8 = lambda R: min((r for r in R if 2480 <= r[0] <= 2580 and r[1] < 0), key=lambda r: -r[1])  # noqa: E731 (right turn: R < 0; tightest)
res = dict(window=dict(s=S0, half_m=HALF, mpp=MPP), legend=dict(red='race edges (track.json)', white_dashed='centre',
           cyan="solver's line (ghosts.json)", orange='smooth line through the real positions (360 lap, N837, IndyCar), held to the solver at T7 and T9',
           dots='yellow N837, magenta 360 lap, green IndyCar'),
           t8_min_radius_m=dict(centre=dict(s=t8(Rc)[0], R=round(-t8(Rc)[1], 1)), solver=dict(s=t8(Rs)[0], R=round(-t8(Rs)[1], 1)),
                                real_fit=dict(s=t8(Ro)[0], R=round(-t8(Ro)[1], 1))),
           offsets=[dict(s=int(s), solver=round(line_off(s), 2), real_fit=round(float(spl(s)), 2)) for s in range(2420, 2621, 10)])
lg = ["T8 (s 2440-2600): race edges red, centre white dashed, solver's line cyan, smooth real line orange",
      'dots: N837 Apr 2026 yellow, 360 lap 2025 magenta, IndyCar Jul 2026 green; north up, 0.1 m/px',
      f"tightest radius at T8: centre {res['t8_min_radius_m']['centre']['R']} m, solver {res['t8_min_radius_m']['solver']['R']} m, real fit {res['t8_min_radius_m']['real_fit']['R']} m"]
for k, t in enumerate(lg):
    d.rectangle((8, 8 + 30 * k, 16 + 12.5 * len(t), 34 + 30 * k), fill=(0, 0, 0))
    d.text((12, 10 + 30 * k), t, fill=(255, 255, 255), font=font)
im.save(out_png)
json.dump(res, open(out_json, 'w'), indent=1)
print(json.dumps(res['t8_min_radius_m']))
for r in res['offsets']:
    print(r)
