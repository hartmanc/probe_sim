"""Mid-Ohio round 3: the checkpoint page's frames.json round-trips through the importer. For every window, the round-3
left and right edge points inside it are written as image-pixel strokes the way review_windows.py drew them (capwin's
px = ((x - (cx - half)) / mpp, ((cy + half) - y) / mpp)), read back by compare/owner_edges.py --by-stroke
--vector-origin continuous --frames <page frames.json> on the round-3 package, and compared with the edge they came
from (distance of each read-back point to the edge polyline). Prints the worst per window in metres and pixels."""
import json, os, subprocess, sys, tempfile
import numpy as np
from scipy.spatial import cKDTree
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
FR = os.path.join(ROOT, 'tools/track/compare/mid_ohio/owner_review_r3/page/frames.json')
PKG = os.path.join(ROOT, 'tools/track/out/mid_ohio_r3')
F = json.load(open(FR)); T = json.load(open(os.path.join(PKG, 'track.json')))
E = {s: np.array(T[s])[:, :2] for s in ('left', 'right')}
worst = 0.0
with tempfile.TemporaryDirectory() as td:
    for win, fr in F.items():
        cx, cy = fr['centre_enu']; h = fr['half']; m = fr['mpp']
        strokes = []
        for side in ('left', 'right'):
            P = E[side][(np.abs(E[side][:, 0] - cx) < h - 2) & (np.abs(E[side][:, 1] - cy) < h - 2)]
            if len(P) > 2:
                strokes.append({'c': 'red', 'kind': 'free', 'pts': np.c_[(P[:, 0] - (cx - h)) / m, ((cy + h) - P[:, 1]) / m].tolist()})
        sj = os.path.join(td, 's.json'); json.dump({win: {'strokes': strokes}}, open(sj, 'w'))
        out = os.path.join(td, 'o.json')
        subprocess.run([sys.executable, '-I', os.path.join(ROOT, 'tools/track/compare/owner_edges.py'), '--track', 'mid_ohio', '--by-stroke',
                        '--vector-origin', 'continuous', '--frames', FR, '--window', win, '--strokes', sj, '--pkg', PKG, '--out', out],
                       check=True, capture_output=True)
        J = json.load(open(out))
        d = []
        for side in ('left', 'right'):
            Q = np.array([[x, y] for x, y, *_ in J[side + '_enu_xys']])
            if len(Q):
                # distance to the densified edge polyline (2 mm)
                A = E[side]; seg = np.roll(A, -1, 0) - A; k = 20
                D = (A[:, None, :] + seg[:, None, :] * (np.arange(k)[None, :, None] / k)).reshape(-1, 2)
                d.append(cKDTree(D).query(Q)[0])
        d = np.concatenate(d); worst = max(worst, d.max())
        print(f"{win}: {len(d)} read-back points, max {d.max():.4f} m = {d.max() / m:.2f} px, median {np.median(d):.4f} m")
print(f"worst {worst:.4f} m")
