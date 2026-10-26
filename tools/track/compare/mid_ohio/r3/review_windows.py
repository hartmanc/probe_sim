"""Mid-Ohio round 3 owner checkpoint, changed region only: windows over the clean captures (reference only, local PNGs,
never committed) with the round-3 fitted edges (left red, right magenta), the owner's round-2 red strokes as applied
(a cyan band under the fit; read from owner_review_r2/edge-marks.json through each round-2 window's frame, continuous canvas
coordinates), the local window's limits and blend ends (white bars across the road, labelled), and station ticks every
10 m (yellow, labelled every 50 m). Writes <out>/<name>.png, <out>/index.html (figcaptions for edge_draw_page.py) and
<out>/frames.json ({name: {s, half, mpp, centre_enu, image_px}}).

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/mid_ohio/r3/review_windows.py
"""
import argparse, html, json, os, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, os.path.join(ROOT, 'tools/track')); sys.path.insert(0, os.path.join(ROOT, 'tools/track/compare'))
import trackcfg, captures as CAP  # noqa
from capwin import mosaic  # noqa
ap = argparse.ArgumentParser()
ap.add_argument('--pkg', default='tools/track/out/mid_ohio_r3')
ap.add_argument('--out', default='tools/track/compare/mid_ohio/owner_review_r3/src')
ap.add_argument('--stations', default='3400,3470,3540,0,70,140,210,280,350,420,490,560,620')
ap.add_argument('--half', type=float, default=40.0); ap.add_argument('--mpp', type=float, default=0.06)
a = ap.parse_args()
cfg = trackcfg.load('mid_ohio')
T = json.load(open(os.path.join(ROOT, a.pkg, 'track.json')))
C = np.array(T['center'])[:, :2]; Lf = np.array(T['left'])[:, :2]; Rt = np.array(T['right'])[:, :2]; n = T['n']; sp = T['spacing_m']
t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NL = np.c_[-t[:, 1], t[:, 0]]
loc = cfg['centre']['local']; wlo, whi = loc['window']; bl = loc.get('blend', 15)
limits = [(wlo, 'window start'), ((wlo + bl) % n, 'full weight'), ((whi - bl) % n, 'full weight'), (whi, 'window end')]
D = json.load(open(os.path.join(ROOT, 'tools/track/compare/mid_ohio/owner_review_r2/edge-marks.json')))
F = json.load(open(os.path.join(ROOT, 'tools/track/compare/mid_ohio/owner_review_r2/frames.json')))
strokes = []
for win, doc in D.items():
    fr = F[win]; cx, cy = fr['center_enu']; h = fr['half']; m = fr['mpp']
    for st in doc['strokes']:
        if st['c'] == 'red':
            P = np.array(st['pts'], float); strokes.append(np.c_[cx - h + P[:, 0] * m, cy + h - P[:, 1] * m])
tiles = CAP.capture_list(cfg, 'clean')
os.makedirs(os.path.join(ROOT, a.out), exist_ok=True)
frames, figs = {}, []
for s in [int(x) for x in a.stations.split(',')]:
    k = int(round(s / sp)) % n; cx, cy = C[k]; half, mpp = a.half, a.mpp; Wp = int(2 * half / mpp)
    img, used = mosaic(tiles, cfg['captures']['mpp'], cx - half, cy + half, Wp, Wp, mpp)
    im = Image.fromarray(img); d = ImageDraw.Draw(im)
    px = lambda p: ((p[0] - (cx - half)) / mpp, ((cy + half) - p[1]) / mpp)  # noqa
    inw = lambda q: -100 < q[0] < Wp + 100 and -100 < q[1] < Wp + 100  # noqa

    def line(P, col, w, halo=1):
        Q = [px(p) for p in P]
        segs = [(Q[i], Q[i + 1]) for i in range(len(Q) - 1) if inw(Q[i]) or inw(Q[i + 1])]
        for p, q in segs:
            d.line([p, q], fill=(15, 15, 15), width=w + 2 * halo)
        for p, q in segs:
            d.line([p, q], fill=col, width=w)
    for P in strokes:   # under the fit: a cyan band where his line and the fit coincide, a separate cyan line where not
        line(P, (0, 225, 255), 7, 0)
    for E, col in ((Lf, (255, 55, 55)), (Rt, (255, 60, 220))):
        line(np.r_[E, E[:1]], col, 3)
    for kk in range(0, n, max(1, int(round(10 / sp)))):
        p = px(Lf[kk]); q = px(Lf[kk] + NL[kk] * 1.2)
        if 0 <= p[0] < Wp and 0 <= p[1] < Wp:
            d.line([p, q], fill=(255, 230, 0), width=2)
            if abs(kk * sp / 50 - round(kk * sp / 50)) < 0.11:
                d.text((q[0] + 3, q[1] - 6), f'{kk * sp:.0f}', fill=(255, 255, 0))
    for kk, lab in limits:
        p = px(Lf[kk] + NL[kk] * 2.0); q = px(Rt[kk] - NL[kk] * 2.0)
        if inw(p) and inw(q):
            d.line([p, q], fill=(15, 15, 15), width=5); d.line([p, q], fill=(255, 255, 255), width=3)
            d.text((p[0] + 4, p[1] + 4), f'{lab} {kk * sp:.0f}', fill=(255, 255, 255))
    name = f'r3_s{len(frames) + 1:02d}_at{s:04d}'   # edge_draw_page sorts by the first s<digits>: driving order
    im.save(os.path.join(ROOT, a.out, name + '.png'))
    frames[name] = dict(s=round(k * sp, 1), station=k, half=half, mpp=mpp, centre_enu=[round(float(cx), 3), round(float(cy), 3)],
                        image_px=[Wp, Wp], pkg=a.pkg)
    w_ = np.linalg.norm(Lf - Rt, axis=1); ii = np.arange(k - int(half / sp), k + int(half / sp) + 1) % n
    q = np.percentile(w_[ii], [5, 50, 95])
    inwin = (k - wlo) % n <= (whi - wlo) % n
    cap = (f's {(k * sp - half) % T["length_m"]:.0f} to {(k * sp + half) % T["length_m"]:.0f} m (round-3 stations, lap {T["length_m"]:.1f} m); '
           f'width p5 / median / p95 {q[0]:.2f} / {q[1]:.2f} / {q[2]:.2f} m; {mpp} m/px, north up. '
           f'Red: round-3 left edge; magenta: round-3 right edge; cyan band: your round-2 red strokes as applied (under the fitted lines); '
           f'white bars: refit window {wlo}-{whi} and its {bl}-station blend ends; yellow: station ticks. '
           + ('Inside the refitted region.' if inwin else 'Held from round 2 (outside the refit window).'))
    figs.append(f'<figure id="{name}"><img src="{name}.png" alt="{name}"><figcaption>{html.escape(cap)}</figcaption></figure>')
    print(name, Wp, 'px', sorted(used.items(), key=lambda kv: -kv[1])[:2])
open(os.path.join(ROOT, a.out, 'index.html'), 'w').write(
    '<!doctype html><html lang="en"><meta charset="utf-8"><title>Mid-Ohio edge review round 3</title>' + ''.join(figs) + '</html>\n')
json.dump(frames, open(os.path.join(ROOT, a.out, 'frames.json'), 'w'), indent=1)
