"""Time-to-station evidence from a Garmin Catalyst onboard (build-track stage 0.7): the overlay's minimap is the GPS trace
of the driven lap and its red dot is the car's GPS position at that frame. Fit the minimap trace to the package's
centreline (one affine, north-up), map every frame's dot to world (x, y) and to the lap station s.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/inventory/catalyst_dots.py \
        --pkg tools/track/out/<id> --frames tools/track/compare/<id>/inventory/frames --fit t100.jpg [--out dots.json]

Frames are the 1280 x 720 captures of headless_capture.ts (t###.jpg or t######.jpg = ms); the minimap sits in the
top-right box --crop (default 1030,10,1275,270). Prints the fit residuals (trace -> centre and centre -> trace), then
one line per frame: t, x, y, s, and the dot's distance from the centre (a dot more than 15 m off is flagged). The dots
are evidence for anchors with an explicit s (source.json anchors {name, t, s, how: 'Catalyst GPS dot ...'}): use them
where the onboard gives no sharper landmark, never as more than +-10 m.
Reads reference imagery, writes numbers only.
"""
import argparse
import glob
import json
import os
import re

import numpy as np
from PIL import Image
from scipy.spatial import cKDTree


def trace_and_dot(path, crop):
    im = np.asarray(Image.open(path).convert('RGB')).astype(int)
    x0, y0, x1, y1 = crop
    c = im[y0:y1, x0:x1]
    white = c.min(2) > 200
    red = (c[..., 0] > 190) & (c[..., 1] < 90) & (c[..., 2] < 90)
    ys, xs = np.nonzero(white)
    tr = np.c_[xs, -ys].astype(float)
    ry, rx = np.nonzero(red)
    dot = np.array([rx.mean(), -ry.mean()]) if len(rx) >= 15 else None
    return tr, dot


def fit_affine(pts, Q, iters=80):
    s = np.ptp(Q[:, 1]) / np.ptp(pts[:, 1]); t = Q.mean(0) - s * pts.mean(0); A = np.eye(2) * s
    kd = cKDTree(Q)
    for _ in range(iters):
        P = pts @ A.T + t; d, i = kd.query(P); keep = d < np.percentile(d, 85)
        X = np.c_[pts[keep], np.ones(keep.sum())]
        sol = np.linalg.lstsq(X, Q[i[keep]], rcond=None)[0]; A = sol[:2].T; t = sol[2]
    P = pts @ A.T + t
    d1, _ = kd.query(P); d2, _ = cKDTree(P).query(Q)
    return A, t, d1, d2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pkg', required=True); ap.add_argument('--frames', required=True); ap.add_argument('--fit', required=True)
    ap.add_argument('--crop', default='1030,10,1275,270'); ap.add_argument('--out', default=None)
    a = ap.parse_args()
    crop = tuple(int(v) for v in a.crop.split(','))
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C = np.array(T['center'])[:, :2]; sp = T.get('spacing_m', 1.0)
    tr, _ = trace_and_dot(os.path.join(a.frames, a.fit), crop)
    A, t, d1, d2 = fit_affine(tr, C)
    print(f'fit on {a.fit}: affine {np.round(A, 3).tolist()} t {np.round(t, 1).tolist()}; trace -> centre median '
          f'{np.median(d1):.1f} m p95 {np.percentile(d1, 95):.1f}; centre -> trace median {np.median(d2):.1f} p95 '
          f'{np.percentile(d2, 95):.1f} max {d2.max():.1f}')
    kd = cKDTree(C); rows = []
    for f in sorted(glob.glob(os.path.join(a.frames, 't*.jpg'))):
        m = re.match(r't(\d+)\.jpg$', os.path.basename(f))
        if not m: continue
        ts = m.group(1); tsec = int(ts) / 1000 if len(ts) >= 6 else float(int(ts))
        _, dot = trace_and_dot(f, crop)
        if dot is None:
            print(f'{os.path.basename(f)}: no dot'); continue
        w = dot @ A.T + t; d, i = kd.query(w)
        rows.append({'frame': os.path.basename(f), 't': tsec, 'x': round(float(w[0]), 1), 'y': round(float(w[1]), 1),
                     's': round(float(i * sp), 1), 'off_m': round(float(d), 1)})
        print(f"{rows[-1]['frame']:>14} t {tsec:8.2f}  s {rows[-1]['s']:7.1f}  off {d:5.1f} m{'  FLAG' if d > 15 else ''}")
    if a.out:
        json.dump({'fit': {'frame': a.fit, 'A': A.tolist(), 't': t.tolist(), 'trace_to_centre_p95': float(np.percentile(d1, 95)),
                           'centre_to_trace_p95': float(np.percentile(d2, 95))}, 'dots': rows}, open(a.out, 'w'), indent=0)


if __name__ == '__main__':
    main()
