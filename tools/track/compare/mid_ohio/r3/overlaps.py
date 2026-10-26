"""Mid-Ohio round 3: where two of the owner's round-2 windows both carry red on the same station and side, their
readings (half-width on the round-2 centre, foot of normal, interpolated to integer stations along each window's line,
as edges_spline.owner_readings project='foot') and the difference. Writes compare/mid_ohio/r3/overlaps.json and prints
the runs where they differ by more than --tol."""
import argparse, json, os, sys
import numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..'))
sys.path.insert(0, os.path.join(ROOT, 'tools/track'))
import edges_spline as ES  # noqa
ap = argparse.ArgumentParser(); ap.add_argument('--tol', type=float, default=0.3)
ap.add_argument('--pkg', default='tools/track/out/mid_ohio_r2'); ap.add_argument('--dir', default='tools/track/tracks/mid_ohio/owner/r2')
ap.add_argument('--out', default='tools/track/compare/mid_ohio/r3/overlaps.json')
a = ap.parse_args()
T = json.load(open(os.path.join(ROOT, a.pkg, 'track.json')))
C = np.array(T['center'])[:, :2]; L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]; n = len(C)
t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NL = np.c_[-t[:, 1], t[:, 0]]
hw = {'left': ((L - C) * NL).sum(1), 'right': -((R - C) * NL).sum(1)}
rd = {'left': {}, 'right': {}}
d = os.path.join(ROOT, a.dir)
for f in sorted(os.listdir(d)):
    if not f.endswith('.json') or f.startswith('merged'):
        continue
    J = json.load(open(os.path.join(d, f)))
    for side in ('left', 'right'):
        P = [[x, y] for x, y, *_ in J[side + '_enu_xys']]
        if len(P) < 2:
            continue
        r = ES.owner_readings(C, NL, {'side': side, 'pts': np.array(P), 'project': 'foot'}, n)
        for k, v in r.items():
            rd[side].setdefault(k, {})[f[:-5]] = round(v, 3)
# the round-2 fit's capture readings (work/fit_assoc_<side>.json: station x, kind, residual = reading - fit): the
# current paint / kerb evidence the overlaps are judged against (owner rows excluded)
cap = {}
for side in ('left', 'right'):
    A = json.load(open(os.path.join(ROOT, a.pkg, 'work', f'fit_assoc_{side}.json')))
    per = {}
    for x, kd, ow, r in zip(A['x'], A['kind'], A['owner'], A['res']):
        if not ow:
            per.setdefault(int(x), []).append((kd, float(hw[side][int(x)]) + r))
    cap[side] = {k: (sorted({q[0] for q in v}), float(np.median([q[1] for q in v]))) for k, v in per.items()}
rows = []
for side in ('left', 'right'):
    for k in sorted(rd[side]):
        w = rd[side][k]
        if len(w) > 1:
            vals = list(w.values())
            c_ = cap[side].get(k)
            rows.append({'side': side, 'k': k, 'fit_r2': round(float(hw[side][k]), 3), 'readings': w,
                         'spread': round(max(vals) - min(vals), 3),
                         'capture': None if c_ is None else {'kinds': c_[0], 'half': round(c_[1], 3)}})
json.dump({'pkg': a.pkg, 'tol': a.tol, 'rows': rows}, open(os.path.join(ROOT, a.out), 'w'), indent=1)
# runs per side and window pair
pairs = {}
for r in rows:
    names = sorted(r['readings'])
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            key = (r['side'], names[i], names[j])
            cv = r['capture']['half'] if r['capture'] else np.nan
            pairs.setdefault(key, []).append((r['k'], r['readings'][names[i]] - r['readings'][names[j]],
                                              r['readings'][names[i]] - cv, r['readings'][names[j]] - cv,
                                              tuple(r['capture']['kinds']) if r['capture'] else ()))
for (side, A, Bn), v in sorted(pairs.items()):
    ks = np.array([q[0] for q in v]); dd = np.array([q[1] for q in v])
    ea = np.array([q[2] for q in v]); eb = np.array([q[3] for q in v])
    big = np.abs(dd) > a.tol
    kinds = sorted({k_ for q in v for k_ in q[4]})
    print(f"{side:5s} {A:12s} - {Bn:12s}: {len(v):3d} stations {ks.min()}..{ks.max()}, diff median {np.median(dd):+.3f}, "
          f"max |diff| {np.abs(dd).max():.3f} at {ks[np.argmax(np.abs(dd))]}, > {a.tol}: {big.sum()}"
          + (f" ({ks[big].min()}..{ks[big].max()})" if big.any() else '')
          + (f"; vs capture readings ({','.join(kinds)}; {np.isfinite(ea[big]).sum()} of the > tol stations): median |{A}-cap| "
             f"{np.nanmedian(np.abs(ea[big])):.3f}, |{Bn}-cap| {np.nanmedian(np.abs(eb[big])):.3f}" if big.any() and np.isfinite(ea[big]).any() else ''))
