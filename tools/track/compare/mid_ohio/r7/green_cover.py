"""Mid-Ohio round 7, step 2: the owner's GREEN strokes (round-2 review: the extra paved boundaries) against the paved
boundaries the package models. For every green point (tracks/mid_ohio/owner/r2/merged.json green_enu_xy, the 13 windows'
strokes merged), the distance to the nearest modelled paved boundary: the course edges (track.json), the pit lane's
edges and the closed roads' edges (scenery.json pit_lane / paved_zones parts). Prints the share within 0.5 / 1.0 / 2.0 m
and every run of green points farther than 2.0 m (what the package does not pave where he drew), with the nearest part.

    uv run --python 3.12 --with numpy,scipy python -I tools/track/compare/mid_ohio/r7/green_cover.py <package dir> [--json out]
"""
import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
TT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def dens(P, step=0.25):
    P = np.asarray(P, float)[:, :2]
    out = [P[0]]
    for a, b in zip(P[:-1], P[1:]):
        n = max(1, int(np.ceil(np.linalg.norm(b - a) / step)))
        out += [a + (b - a) * (k / n) for k in range(1, n + 1)]
    return np.array(out)


def main():
    pkg = sys.argv[1]
    T = json.load(open(os.path.join(pkg, 'track.json')))
    S = json.load(open(os.path.join(pkg, 'scenery.json')))
    G = np.array(json.load(open(os.path.join(TT, 'tracks/mid_ohio/owner/r2/merged.json')))['green_enu_xy'], float)[:, :2]
    B, lab = [], []
    for side in ('left', 'right'):
        L = np.array(T[side])[:, :2]
        B.append(dens(np.r_[L, L[:1]])); lab += [f'course {side} edge'] * len(B[-1])
    for grp, nm in ((S.get('pit_lane') or {}, 'pit lane'), (S.get('paved_zones') or {}, None)):
        for p in grp.get('parts', []):
            for side in ('left', 'right'):
                B.append(dens(p[side])); lab += [f"{nm or p.get('turn', 'zone')} {side} edge"] * len(B[-1])
            for end in (0, -1):   # the part's ends (a mouth on the course is the course edge)
                B.append(dens([p['left'][end], p['right'][end]])); lab += [f"{nm or p.get('turn', 'zone')} end"] * len(B[-1])
    B = np.concatenate(B)
    d, k = cKDTree(B).query(G)
    res = dict(points=len(G), within_0_5=float((d <= 0.5).mean()), within_1_0=float((d <= 1.0).mean()),
               within_2_0=float((d <= 2.0).mean()), p50=float(np.median(d)), p90=float(np.percentile(d, 90)), runs=[])
    far = d > 2.0
    # runs of consecutive far points (the merged list keeps each stroke's order)
    i = 0
    while i < len(G):
        if not far[i]:
            i += 1
            continue
        j = i
        while j + 1 < len(G) and far[j + 1] and np.linalg.norm(G[j + 1] - G[j]) < 3.0:
            j += 1
        res['runs'].append(dict(n=int(j - i + 1), x=round(float(G[i:j + 1, 0].mean()), 1), y=round(float(G[i:j + 1, 1].mean()), 1),
                                d_max=round(float(d[i:j + 1].max()), 2), nearest=lab[k[i]]))
        i = j + 1
    print(f"green points {res['points']}: within 0.5 m {res['within_0_5']:.1%}, 1.0 m {res['within_1_0']:.1%}, 2.0 m {res['within_2_0']:.1%}; "
          f"p50 {res['p50']:.2f} m, p90 {res['p90']:.2f} m")
    for r in res['runs']:
        print(f"   beyond 2 m: {r['n']} points at ({r['x']}, {r['y']}), up to {r['d_max']} m, nearest {r['nearest']}")
    if '--json' in sys.argv:
        json.dump(res, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)


if __name__ == '__main__':
    main()
