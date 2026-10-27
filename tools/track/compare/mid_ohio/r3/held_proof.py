"""Mid-Ohio round 3, the held-course proof (replaces held_edges.py's one-way table after the Astra review):
1. bidirectional point-to-SEGMENT distances between the round-2 and round-3 polylines (left, right, centre), each
   direction restricted to points outside the local window (+ blend) of its own package's stations;
2. the station correspondence round 2 -> round 3: each round-2 centre station's foot on the round-3 centre as a
   fractional round-3 station u(k); monotone check; u(k) - k in stations and the along-track metres it means; and the
   same-index displacement |P3[k] - P2[k]| it explains;
3. world anchors: the frame (origin, heightfield / ortho boxes) and the config's fixed lat/lon points (timing line,
   corner anchors, the footbridge) projected on both centres (station s and lateral offset), and the heightfield bytes
   outside the window's footprint.
Prints markdown; writes nothing."""
import argparse, json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, os.path.join(ROOT, 'tools/track'))
import trackcfg  # noqa
ap = argparse.ArgumentParser()
ap.add_argument('--ref', default='tools/track/out/mid_ohio_r2'); ap.add_argument('--cand', default='tools/track/out/mid_ohio_r3')
ap.add_argument('--window', default='3395,610')
a = ap.parse_args()
cfg = trackcfg.load('mid_ohio')
A = json.load(open(os.path.join(ROOT, a.ref, 'track.json'))); B = json.load(open(os.path.join(ROOT, a.cand, 'track.json')))
lo, hi = map(int, a.window.split(',')); n = A['n']; span = (hi - lo) % n
inwin = lambda k: ((np.asarray(k) - lo) % n) <= span  # noqa


def seg_dist(P, Q):
    """distance of each point P to the closed polyline Q (exact point-to-segment), and the fractional index of the foot"""
    from scipy.spatial import cKDTree
    Q2 = np.r_[Q, Q[:1]]; S0 = Q2[:-1]; D = Q2[1:] - S0; L2 = (D ** 2).sum(1)
    _, i = cKDTree(Q).query(P, k=4)
    best = np.full(len(P), np.inf); foot = np.zeros(len(P))
    for c in range(i.shape[1]):
        for j in (i[:, c], (i[:, c] - 1) % len(Q)):
            t = np.clip(((P - S0[j]) * D[j]).sum(1) / L2[j], 0, 1)
            d = np.linalg.norm(S0[j] + t[:, None] * D[j] - P, axis=1)
            m = d < best; best[m] = d[m]; foot[m] = (j + t)[m]
    return best, foot


print('### 1. Bidirectional point-to-segment distance, outside the window (stations of each package)\n')
print('| polyline | direction | points | max (mm) | RMS (mm) | p99 (mm) |\n|---|---|---|---|---|---|')
for key in ('left', 'right', 'center'):
    Pa = np.array(A[key])[:, :2]; Pb = np.array(B[key])[:, :2]
    for nm, P, Q in (('r3 -> r2', Pb, Pa), ('r2 -> r3', Pa, Pb)):
        m = ~inwin(np.arange(n))
        d, _ = seg_dist(P[m], Q)
        print(f"| {key} | {nm} | {m.sum()} | {d.max() * 1e3:.1f} | {np.sqrt((d ** 2).mean()) * 1e3:.1f} | {np.percentile(d, 99) * 1e3:.1f} |")
print('\n### 2. Station correspondence round 2 -> round 3\n')
Ca = np.array(A['center'])[:, :2]; Cb = np.array(B['center'])[:, :2]
_, u = seg_dist(Ca, Cb)
k = np.arange(n)
du = ((u - k + n / 2) % n) - n / 2           # round-3 fractional station minus round-2 index
unw = k + du
mono = bool(np.all(np.diff(np.r_[unw, unw[0] + n]) > 0))
out = ~inwin(k)
spB = B['spacing_m']
print(f"monotone: {mono} (every round-2 station maps to a later round-3 station than the one before, all {n})")
print(f"spacing {A['spacing_m']:.6f} -> {spB:.6f} m; lap {A['length_m']} -> {B['length_m']} m")
print('\n| region (r2 stations) | u(k) - k, stations: min / median / max | along-track (m) min / max | same-index |P3[k]-P2[k]| centre max (m) | left max | right max |\n|---|---|---|---|---|---|---|')
for nm, m in (('outside 611..3394', out), ('window 3395..610', ~out)):
    dd = {key: np.linalg.norm(np.array(B[key])[:, :2] - np.array(A[key])[:, :2], axis=1)[m] for key in ('center', 'left', 'right')}
    print(f"| {nm} | {du[m].min():+.4f} / {np.median(du[m]):+.4f} / {du[m].max():+.4f} | {du[m].min() * spB:+.3f} / {du[m].max() * spB:+.3f} | "
          f"{dd['center'].max():.3f} | {dd['left'].max():.3f} | {dd['right'].max():.3f} |")
# where along the outside the shift is largest, in blocks
blk = [(b, float(np.abs(du[(k >= b) & (k < b + 300) & out]).max() * spB)) for b in range(0, n, 300) if ((k >= b) & (k < b + 300) & out).any()]
print('\nlargest along-track station shift per 300-station block outside the window (m): ' + ', '.join(f"{b}: {v:.3f}" for b, v in blk))
print('\n### 3. World anchors\n')
same = {f: A[f] == B[f] for f in ('origin', 'heightfield', 'ortho', 'z0_navd88', 'direction', 'n')}
print('frame fields identical (origin, heightfield box, ortho box, z0, direction, n): ' + ', '.join(f"{k_} {v}" for k_, v in same.items()))
pts = [('timing line', cfg['start_finish_latlon'])] + [(c[0] + ' anchor', (c[4], c[5])) for c in cfg['corners']] + \
      [('T1 footbridge', cfg['profile_gaps'][0]['latlon'])]
print('\n| anchor (config lat/lon) | ENU (m) | r2 s / lateral (m) | r3 s / lateral (m) | delta lateral (mm) | inside window |\n|---|---|---|---|---|---|')
for nm, (la, lo_) in pts:
    p = np.array(cfg.enu(la, lo_), float)[None]
    rows = []
    for T_ in (A, B):
        C_ = np.array(T_['center'])[:, :2]
        d, f = seg_dist(p, C_)
        i0 = int(np.floor(f[0])) % n; t = np.roll(C_, -1, 0) - C_; t /= np.linalg.norm(t, axis=1, keepdims=True)
        lat = float(((p[0] - C_[i0]) * np.r_[-t[i0, 1], t[i0, 0]]).sum())
        rows.append((f[0] * T_['spacing_m'], lat))
    print(f"| {nm} | {p[0, 0]:.2f}, {p[0, 1]:.2f} | {rows[0][0]:.2f} / {rows[0][1]:+.3f} | {rows[1][0]:.2f} / {rows[1][1]:+.3f} | "
          f"{(rows[1][1] - rows[0][1]) * 1e3:+.1f} | {bool(inwin(int(round(rows[0][0] / A['spacing_m'])) % n))} |")
# heightfield cells
hf = A['heightfield']; nx, ny, x0, y0, dx = hf['nx'], hf['ny'], hf['x0'], hf['y0'], hf['dx']
Ha = np.fromfile(os.path.join(ROOT, a.ref, 'heightfield.bin'), '<f4').reshape(ny, nx)
Hb = np.fromfile(os.path.join(ROOT, a.cand, 'heightfield.bin'), '<f4').reshape(ny, nx)
diff = np.abs(Hb - Ha) > 0
from scipy.spatial import cKDTree
jj, ii = np.nonzero(diff)
if len(jj):
    X = np.c_[x0 + ii * dx, y0 + jj * dx]
    _, kk = cKDTree(Ca).query(X)
    far = ~inwin(kk)
    print(f"\nheightfield: {diff.sum()} of {diff.size} cells differ (max |dz| {np.abs(Hb - Ha).max():.4f} m); "
          f"cells nearest a round-2 station outside the window: {far.sum()} (max |dz| there {np.abs(Hb - Ha)[jj[far], ii[far]].max() if far.any() else 0:.4f} m)")
else:
    print('\nheightfield: byte-identical')
