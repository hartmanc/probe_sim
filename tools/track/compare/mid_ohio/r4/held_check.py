"""Mid-Ohio round 4, the held course against round 3: the round-4 geometry differs from round 3 only by the config's
T4 profile_bank rule (and the length gate, which changes no geometry). Exact comparison of the two packages:
1. track.json: n, spacing, length, every centre / left / right plan position (x, y), every corner, the frame boxes;
2. the profile (track.json profile.z and the stored z of centre / left / right): the stations that differ, and the
   largest difference outside the rule's interval (must be 0);
3. heightfield.bin: the cells that differ, their extent (ENU box), their foot station on the centre (the rule's
   fractional projection) and the largest |dz| outside the interval (must be 0).
Prints markdown; writes nothing."""
import argparse, json, os, sys
import numpy as np
from scipy.spatial import cKDTree
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
ap = argparse.ArgumentParser()
ap.add_argument('--ref', default='tools/track/out/mid_ohio_r3'); ap.add_argument('--cand', default='tools/track/out/mid_ohio_r4')
a = ap.parse_args()
R = json.load(open(os.path.join(ROOT, a.ref, 'track.json'))); Q = json.load(open(os.path.join(ROOT, a.cand, 'track.json')))
rep = json.load(open(os.path.join(ROOT, a.cand, 'work', 'geometry_report.json')))['profile_bank']
pb = rep['profile'][0]; lo, hi = pb['interval_stations']; n = Q['n']
inside = lambda k: ((np.asarray(k) - lo) % n) <= ((hi - lo) % n)  # noqa
print(f"| item | round 3 | round 4 | identical |\n|---|---|---|---|")
for k in ('n', 'spacing_m', 'length_m', 'z0_navd88', 'direction'):
    print(f"| {k} | {R[k]} | {Q[k]} | {R[k] == Q[k]} |")
for k in ('heightfield', 'ortho', 'start_finish', 'corners', 'origin'):
    print(f"| {k} | | | {R[k] == Q[k]} |")
for k in ('center', 'left', 'right'):
    A, B = np.array(R[k]), np.array(Q[k])
    print(f"| {k} plan x, y ({len(A)} points) | | | {np.array_equal(A[:, :2], B[:, :2])} (max {np.abs(A[:, :2] - B[:, :2]).max():.4f} m) |")
zA, zB = np.array(R['profile']['z']), np.array(Q['profile']['z'])
d = np.abs(zA - zB).max(1)
ch = np.nonzero(d > 0)[0]
print(f"\nProfile: {len(ch)} stations differ, {ch.min()}..{ch.max()} (the rule's interval {lo}..{hi}); outside the interval "
      f"max |dz| {d[~inside(np.arange(n))].max():.4f} m; inside max {d.max():.3f} m")
for k, col in (('center', 3), ('left', 0), ('right', 6)):
    A, B = np.array(R[k])[:, 2], np.array(Q[k])[:, 2]
    dd = np.abs(A - B)
    print(f"- stored {k} z: {np.count_nonzero(dd)} stations differ, max {dd.max():.3f} m; outside the interval max "
          f"{dd[~inside(np.arange(n))].max():.4f} m")
hA = np.fromfile(os.path.join(ROOT, a.ref, 'heightfield.bin'), '<f4'); hB = np.fromfile(os.path.join(ROOT, a.cand, 'heightfield.bin'), '<f4')
H = Q['heightfield']; nx, ny = H['nx'], H['ny']; dx = H.get('dx', 2.0)
hA = hA.reshape(ny, nx); hB = hB.reshape(ny, nx)
diff = hB.astype(float) - hA.astype(float)
iy, ix = np.nonzero(diff)
x0, y0 = H['x0'], H['y0']
X = x0 + ix * dx; Y = y0 + iy * dx
C = np.array(Q['center'])[:, :2]
_, st = cKDTree(C).query(np.c_[X, Y])
print(f"\nHeightfield: {len(ix)} of {nx * ny} cells differ (round 4 - round 3: min {diff.min():+.3f} m, max {diff.max():+.3f} m); "
      f"extent x {X.min():.0f}..{X.max():.0f} m, y {Y.min():.0f}..{Y.max():.0f} m (ENU); nearest centre station of the "
      f"changed cells {st.min()}..{st.max()}; changed cells whose nearest station is outside the interval: "
      f"{int((~inside(st)).sum())}; the rule's own count {rep['heightfield']['total_cells']}")
