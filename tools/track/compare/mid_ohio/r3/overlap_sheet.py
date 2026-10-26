"""Mid-Ohio round 3: close-ups of the stations where two of the owner's round-2 windows disagree (r3/overlaps.json),
over the clean captures (reference only, local): the round-2 fitted edge (white), each window's red as the half-width
reading it gives on the round-2 centre (one colour per window, legend), the round-2 fit's capture readings (cyan dots:
painted / kerb readings) and station ticks every 5 m. Output PNGs stay local (ignored)."""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, os.path.join(ROOT, 'tools/track')); sys.path.insert(0, os.path.join(ROOT, 'tools/track/compare'))
import trackcfg, captures as CAP  # noqa
from capwin import mosaic  # noqa
COL = {'w_s0000': (255, 60, 60), 'w_s0125': (255, 160, 0), 'w_s0250': (255, 0, 255), 'w_s0375': (60, 160, 255),
       'w_s0500': (160, 255, 60), 'w_s3375': (255, 255, 0), 'w_s3500': (255, 60, 60), 'close_s0220': (0, 255, 160),
       'close_s0320': (0, 255, 160)}
ap = argparse.ArgumentParser()
ap.add_argument('--region', action='append', required=True, help='name:side:lo:hi')
ap.add_argument('--mpp', type=float, default=0.04); ap.add_argument('--out', default='tools/track/compare/mid_ohio/r3/overlap_png')
a = ap.parse_args()
cfg = trackcfg.load('mid_ohio')
T = json.load(open(os.path.join(ROOT, 'tools/track/out/mid_ohio_r2/track.json')))
C = np.array(T['center'])[:, :2]; n = len(C)
t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NL = np.c_[-t[:, 1], t[:, 0]]
E = {'left': np.array(T['left'])[:, :2], 'right': np.array(T['right'])[:, :2]}
O = json.load(open(os.path.join(ROOT, 'tools/track/compare/mid_ohio/r3/overlaps.json')))
cap = {}
for side in ('left', 'right'):
    A = json.load(open(os.path.join(ROOT, 'tools/track/out/mid_ohio_r2/work', f'fit_assoc_{side}.json')))
    cap[side] = (A['x'], A['res'], A['owner'], A['kind'])
hw = {'left': ((E['left'] - C) * NL).sum(1), 'right': -((E['right'] - C) * NL).sum(1)}
tiles = CAP.capture_list(cfg, 'clean')
os.makedirs(os.path.join(ROOT, a.out), exist_ok=True)
for reg in a.region:
    name, side, lo, hi = reg.split(':'); lo, hi = int(lo), int(hi)
    sg = 1 if side == 'left' else -1
    span = (hi - lo) % n; mid = (lo + span // 2) % n
    edge_mid = C[mid] + sg * hw[side][mid] * NL[mid]
    half = max(8.0, span / 2 + 4)
    cx, cy = edge_mid
    Wp = int(2 * half / a.mpp)
    img, used = mosaic(tiles, cfg['captures']['mpp'], cx - half, cy + half, Wp, Wp, a.mpp)
    im = Image.fromarray(img); d = ImageDraw.Draw(im)
    px = lambda p: ((p[0] - (cx - half)) / a.mpp, ((cy + half) - p[1]) / a.mpp)  # noqa
    ks = np.arange(lo - 10, lo + span + 11) % n
    d.line([px(E[side][k]) for k in ks], fill=(255, 255, 255), width=1)
    for k in ks:
        if k % 5 == 0:
            p = px(C[k] + sg * (hw[side][k] - 1.2) * NL[k]); q = px(C[k] + sg * (hw[side][k] - 0.6) * NL[k])
            d.line([p, q], fill=(255, 230, 0), width=2); d.text((p[0] + 3, p[1]), str(k), fill=(255, 255, 0))
    x, res, ow, kd = cap[side]
    for xi, r, o in zip(x, res, ow):
        if not o and (xi - lo + 10) % n <= span + 20:
            q = px(C[xi] + sg * (hw[side][xi] + r) * NL[xi]); d.ellipse([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], fill=(0, 230, 255))
    per = {}
    for row in O['rows']:
        pass
    # each window's readings (all its stations in range, not only the overlap)
    import edges_spline as ES
    leg = []
    for f in sorted(os.listdir(os.path.join(ROOT, 'tools/track/tracks/mid_ohio/owner/r2'))):
        if not f.endswith('.json') or f.startswith('merged'):
            continue
        J = json.load(open(os.path.join(ROOT, 'tools/track/tracks/mid_ohio/owner/r2', f)))
        P = [[x_, y_] for x_, y_, *_ in J[side + '_enu_xys']]
        if len(P) < 2:
            continue
        r = ES.owner_readings(C, NL, {'side': side, 'pts': np.array(P), 'project': 'foot'}, n)
        kk = [k for k in sorted(r) if (k - lo + 10) % n <= span + 20]
        if not kk:
            continue
        col = COL.get(f[:-5], (255, 255, 255))
        segs = np.split(np.array(kk), np.flatnonzero(np.diff(kk) > 1) + 1)
        for sgm in segs:
            pts = [px(C[k] + sg * r[k] * NL[k]) for k in sgm]
            if len(pts) > 1:
                d.line(pts, fill=col, width=2)
        leg.append((f[:-5], col))
    for i, (nm, col) in enumerate(leg):
        d.rectangle([8, 8 + 16 * i, 20, 20 + 16 * i], fill=col); d.text((26, 8 + 16 * i), nm, fill=(255, 255, 255))
    d.text((8, Wp - 16), f'{name} {side} {lo}-{hi}, {a.mpp} m/px, white r2 fit, cyan capture readings', fill=(255, 255, 255))
    o = os.path.join(ROOT, a.out, f'{name}_{side}_{lo}_{hi}.png'); im.save(o); print(o, Wp, 'px', used)
