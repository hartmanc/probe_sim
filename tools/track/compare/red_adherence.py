"""The package's race edges against the owner's merged red (Buttonwillow round 15, 26 Oct 2026).

For every point of his red (owner/r10/merged.json left_enu_xys / right_enu_xys: [x, y, station]) the signed distance to
the package's edge polyline of the same side (track.json left / right): + where the package edge lies OUTSIDE his red
(farther from the centre), - inside. Points are split by the package's kerb strips (scenery.json kerbs, the strip's
stations +-3 on its side) and his red-across mouths (owner/r10/mouths.json, by world position: within 12 m of the
mouth's line) are reported apart. Prints median / p90 / max of |d| per side and set, and the worst places.

usage: python -I red_adherence.py --pkg <package dir> [--merged ...] [--mouths ...] [--worst 10] [--json out.json]
"""
import argparse
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OWN = os.path.join(HERE, '..', 'tracks', 'buttonwillow', 'owner', 'r10')


def seg_dist(P, E):
    """Distance from each point of P (m x 2) to the closed polyline E (n x 2), and the nearest segment index."""
    A = E
    B = np.roll(E, -1, axis=0)
    AB = B - A
    L2 = np.maximum((AB ** 2).sum(1), 1e-12)
    out = np.empty(len(P))
    idx = np.empty(len(P), int)
    for k, p in enumerate(P):
        t = np.clip(((p - A) * AB).sum(1) / L2, 0, 1)
        Q = A + t[:, None] * AB
        d = np.hypot(*(Q - p).T)
        j = int(np.argmin(d))
        out[k], idx[k] = d[j], j
    return out, idx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pkg', required=True)
    ap.add_argument('--merged', default=os.path.join(OWN, 'merged.json'))
    ap.add_argument('--mouths', default=os.path.join(OWN, 'mouths.json'))
    ap.add_argument('--worst', type=int, default=10)
    ap.add_argument('--json', default=None)
    a = ap.parse_args()
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    S = json.load(open(os.path.join(a.pkg, 'scenery.json')))
    M = json.load(open(a.merged))
    mouths = json.load(open(a.mouths))['mouths']
    C = np.array(T['center'])[:, :2]
    n = len(C)
    kerbs = S.get('kerbs', {}).get('strips', [])
    res = {}
    worst = []
    for side, key, sg in (('left', 'left_enu_xys', 1), ('right', 'right_enu_xys', -1)):
        E = np.array(T[side])[:, :2]
        R = np.array(M[key], float)
        P = R[:, :2]
        d, j = seg_dist(P, E)
        # sign: + when the package edge lies outside his red (the red nearer the centre than the edge)
        rc = np.hypot(*(P - C[j]).T)
        ec = np.hypot(*(E[j] - C[j]).T)
        sgn = np.where(ec >= rc, 1.0, -1.0)
        ds = d * sgn
        on_k = np.zeros(len(P), bool)
        for k in kerbs:
            if (k['side'] > 0) != (side == 'left') or k.get('kind') in ('verge', 'blocks'):
                continue
            s0, s1 = int(k['s0']) - 3, int(k['s1']) + 3
            jj = np.where(j < s0, j + n, j)
            on_k |= (jj >= s0) & (jj <= s1)
        in_m = np.zeros(len(P), bool)
        for m in mouths:
            if m['side'] != side or m.get('kind') != 'red across':
                continue
            Lm = np.array(m['line_enu'], float)
            dm = np.min(np.hypot(P[:, None, 0] - Lm[None, :, 0], P[:, None, 1] - Lm[None, :, 1]), axis=1)
            in_m |= dm < 12.0
        sets = {'all': np.ones(len(P), bool), 'away from kerbs and mouths': ~on_k & ~in_m,
                'along kerb strips': on_k & ~in_m, 'mouths': in_m}
        res[side] = {}
        for name, msk in sets.items():
            v = np.abs(ds[msk])
            if not len(v):
                continue
            res[side][name] = dict(n=int(msk.sum()), median=round(float(np.median(v)), 3),
                                   p90=round(float(np.percentile(v, 90)), 3), max=round(float(v.max()), 3),
                                   signed_median=round(float(np.median(ds[msk])), 3))
        for k in np.argsort(-np.abs(ds) * ~in_m)[: 3 * a.worst]:
            worst.append(dict(side=side, s=int(j[k]), x=round(float(P[k, 0]), 1), y=round(float(P[k, 1]), 1),
                              d=round(float(ds[k]), 3), kerb=bool(on_k[k])))
    worst.sort(key=lambda w: -abs(w['d']))
    # one row per place (20 m apart)
    places = []
    for w in worst:
        if all(not (p['side'] == w['side'] and abs(p['s'] - w['s']) < 20) for p in places):
            places.append(w)
        if len(places) >= a.worst:
            break
    for side in ('left', 'right'):
        for name, r in res[side].items():
            print(f"{side:5s} {name:28s} n {r['n']:5d}  median {r['median']:.3f}  p90 {r['p90']:.3f}  max {r['max']:.3f}  (signed median {r['signed_median']:+.3f})")
    print(f"worst {a.worst} places outside the mouths (+ = package edge outside his red):")
    for w in places:
        print(f"   {w['side']:5s} s {w['s']:5d}  ({w['x']:8.1f}, {w['y']:8.1f})  {w['d']:+.3f} m{'  kerb' if w['kerb'] else ''}")
    if a.json:
        json.dump(dict(pkg=a.pkg, sets=res, worst=places), open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
