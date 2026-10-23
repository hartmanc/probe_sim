"""A window of a package's own ground ortho (ortho.jpg, what the sim drapes on the terrain) with the package's edges and
barriers drawn over it: the view of "a long line in the ground texture" (Sonoma round 13, owner 23 Oct 2026). capwin.py
shows the z20 captures; this shows the 0.6 m/px ortho the driver actually sees, where a dark or pale band with no barrier
on it is a missing or misplaced feature.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/orthowin.py --pkg public/tracks/sonoma \
        --s 410 [--half 60] [--mpp 0.15] [--raw] [--lines lines.json] --out x.png

Overlay: edges white, ticks every 10 m with s every 50 m (yellow), barriers (concrete white, pitwall orange, tyres red,
armco blue, fence orange thin), kerb strips magenta, paved parts cyan; --lines draws the ground-lines gate's findings
(a json list of {pts: [[x, y], ...]}) in green.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import map_coordinates


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pkg', required=True)
    ap.add_argument('--s', type=float)
    ap.add_argument('--xy')
    ap.add_argument('--half', type=float, default=60.0)
    ap.add_argument('--mpp', type=float, default=0.15)
    ap.add_argument('--raw', action='store_true')
    ap.add_argument('--lines')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    SC = json.load(open(os.path.join(a.pkg, 'scenery.json'))) if not a.raw else None
    o = T['ortho']
    im = np.asarray(Image.open(os.path.join(a.pkg, o['file'])).convert('RGB')).astype(np.float32)
    C = np.array(T['center'])[:, :2]; L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]
    n, sp = T['n'], T['spacing_m']
    if a.s is not None:
        cx, cy = C[int(round(a.s / sp)) % n]
    else:
        cx, cy = map(float, a.xy.split(','))
    W = int(2 * a.half / a.mpp)
    gx = cx - a.half + (np.arange(W) + 0.5) * a.mpp
    gy = cy + a.half - (np.arange(W) + 0.5) * a.mpp
    X, Y = np.meshgrid(gx, gy)
    px = (X - o['x0']) / (o['x1'] - o['x0']) * o['width_px'] - 0.5
    py = (o['y1'] - Y) / (o['y1'] - o['y0']) * o['height_px'] - 0.5
    out = np.stack([map_coordinates(im[..., c], [py, px], order=1, mode='nearest') for c in range(3)], -1)
    img = Image.fromarray(out.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    P = lambda x, y: ((x - (cx - a.half)) / a.mpp, ((cy + a.half) - y) / a.mpp)  # noqa: E731
    if not a.raw:
        for E in (L, R):
            pts = [P(*p) for p in E]
            for i in range(n):
                p, q = pts[i], pts[(i + 1) % n]
                if -50 < p[0] < W + 50 and -50 < p[1] < W + 50:
                    d.line([p, q], fill=(255, 255, 255), width=1)
        tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
        NL = np.c_[-tg[:, 1], tg[:, 0]]
        for i in range(0, n, max(1, int(round(10 / sp)))):
            p = P(*L[i]); q = P(*(L[i] + NL[i] * 1.5))
            if 0 <= p[0] < W and 0 <= p[1] < W:
                d.line([p, q], fill=(255, 230, 0), width=2)
                s = i * sp
                if abs(s / 50 - round(s / 50)) < 0.11:
                    d.text((q[0] + 2, q[1] - 6), f'{s:.0f}', fill=(255, 255, 0))
        col = {'concrete': (255, 255, 255), 'pitwall': (255, 160, 0), 'tyres': (255, 40, 40), 'armco': (90, 140, 255), 'fence': (255, 120, 0)}
        for b in SC.get('barriers', []):
            d.line([P(p[0], p[1]) for p in b['pts']], fill=col.get(b['kind'], (255, 0, 255)), width=3 if b['kind'] != 'fence' else 1)
        for grp in ('pit_lane', 'paved_zones', 'paved_areas', 'closed_roads'):
            g = SC.get(grp) or {}
            for part in (g.get('parts', []) if isinstance(g, dict) else g):
                for side in ('left', 'right'):
                    if part.get(side):
                        d.line([P(p[0], p[1]) for p in part[side]], fill=(0, 230, 230), width=1)
    if a.lines:
        for ln in json.load(open(a.lines)):
            d.line([P(p[0], p[1]) for p in ln['pts']], fill=(0, 255, 0), width=2)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    img.save(a.out)
    print(f'{a.out}: centre ({cx:.1f}, {cy:.1f}), {W} px at {a.mpp} m/px (ortho {((o["x1"] - o["x0"]) / o["width_px"]):.3f} m/px)')


if __name__ == '__main__':
    main()
