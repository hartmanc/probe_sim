"""Mid-Ohio round 3: the held course outside the local window. Every round-3 edge / centre point is projected (foot of
normal) on the round-2 centre; its distance to the round-2 polyline of the same kind (densified to 2 cm) is tabulated by
region of the round-2 station frame: outside the window, the blend bands (window ends + blend), the window interior.
Prints a markdown table; writes nothing."""
import argparse, json, os, sys
import numpy as np
from scipy.spatial import cKDTree
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, os.path.join(ROOT, 'tools/track'))
import edges_spline as ES  # noqa
ap = argparse.ArgumentParser()
ap.add_argument('--ref', default='tools/track/out/mid_ohio_r2'); ap.add_argument('--cand', default='tools/track/out/mid_ohio_r3')
ap.add_argument('--window', default='3395,610'); ap.add_argument('--blend', type=int, default=15)
a = ap.parse_args()
A = json.load(open(os.path.join(ROOT, a.ref, 'track.json'))); B = json.load(open(os.path.join(ROOT, a.cand, 'track.json')))
lo, hi = map(int, a.window.split(','))
Ca = np.array(A['center'])[:, :2]; n = len(Ca)
t = np.roll(Ca, -1, 0) - np.roll(Ca, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NL = np.c_[-t[:, 1], t[:, 0]]
span = (hi - lo) % n


def dense(P):
    P = np.r_[P, P[:1]]; seg = np.diff(P, axis=0); m = np.maximum(1, np.ceil(np.linalg.norm(seg, axis=1) / 0.02)).astype(int)
    return np.concatenate([P[i] + seg[i] * (np.arange(m[i])[:, None] / m[i]) for i in range(len(seg))])


rows = []
print(f"| polyline | region (round-2 stations) | points | max (m) | RMS (m) | p99 (m) |\n|---|---|---|---|---|---|")
for key in ('left', 'right', 'center'):
    Pa = np.array(A[key])[:, :2]; Pb = np.array(B[key])[:, :2]
    d = cKDTree(dense(Pa)).query(Pb)[0]
    s, _ = ES.foot_project(Ca, NL, Pb if key == 'center' else Pb)
    j = (np.round(s).astype(int) - lo) % n
    inside = j <= span
    blend = inside & ((j < a.blend) | (j > span - a.blend))
    core = inside & ~blend
    for name, m in ((f'outside {hi + 1}..{lo - 1}', ~inside), (f'blend {lo}..{lo + a.blend - 1}, {hi - a.blend + 1}..{hi}', blend),
                    (f'window interior {lo + a.blend}..{hi - a.blend}', core)):
        if m.any():
            print(f"| {key} | {name} | {m.sum()} | {d[m].max():.4f} | {np.sqrt((d[m] ** 2).mean()):.4f} | {np.percentile(d[m], 99):.4f} |")
print(f"\nlength {A['length_m']} -> {B['length_m']} m; n {A['n']} -> {B['n']}")
