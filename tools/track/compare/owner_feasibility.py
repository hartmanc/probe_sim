"""How closely CAN an edge follow the owner's red and still pass the world-continuity gate? (Sonoma round 14B part 1b,
24 Oct 2026.) For each spline.owner_edges window and side: his red as the fit takes it (his readings on the package's
centre, kerb shifts included: build_track.owner_windows / edges_spline.owner_readings) as one world polyline per stretch
(broken where his readings are more than 3 stations apart: the fit is free there); the smoothest polyline at a uniform
spacing s along it (a least-squares fit to his points with a penalty on the third difference, the penalty raised until
the edge gate's world continuity holds: max |third difference| <= edge_gate.FITTED['world_d3']); printed: the largest
distance from his red to that curve and the share within 0.25 m, for s = 1.0 m (an edge whose stations are 1 m apart)
and for the package's own edge spacing over the stretch (on the outside of a tight corner the edge's stations spread to
1.3-2 m and the same third-difference limit is harder). A lower bound on what any station-indexed edge can reach: the
real edge is tied to the centre's normals as well. Writes --json.

    uv run --python 3.12 --with numpy,scipy python -I tools/track/compare/owner_feasibility.py --track sonoma \
        --pkg tools/track/out/sonoma_r14b [--zones 2990-3200,3600-3780] --json tools/track/compare/sonoma/round14b/owner_feasibility.json
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy.sparse import csr_matrix, diags
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import trackcfg  # noqa: E402
import edge_gate  # noqa: E402
import edges_spline  # noqa: E402


def dense(P, k=10):
    if len(P) < 2:
        return P
    t = np.linspace(0, 1, k, endpoint=False)[None, :, None]
    return np.vstack([(P[:-1, None, :] + (P[1:] - P[:-1])[:, None, :] * t).reshape(-1, 2), P[-1:]])


def smoothest(P, s, d3max):
    """the polyline at spacing s along P (arc length, no data across a gap) with max |d3| <= d3max closest to P"""
    u = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    m = int(u[-1] / s) + 2; x = u / s; i = np.minimum(x.astype(int), m - 2); f = x - i
    A = csr_matrix((np.r_[1 - f, f], (np.r_[np.arange(len(x)), np.arange(len(x))], np.r_[i, i + 1])), shape=(len(x), m))
    D = diags([-1., 3., -3., 1.], [0, 1, 2, 3], shape=(m - 3, m))
    for mu in np.geomspace(1, 1e7, 71):
        H = (A.T @ A + mu * D.T @ D + diags(np.full(m, 1e-9))).tocsc()
        E = np.c_[spsolve(H, A.T @ P[:, 0]), spsolve(H, A.T @ P[:, 1])]
        d3 = np.linalg.norm(E[3:] - 3 * E[2:-1] + 3 * E[1:-2] - E[:-3], axis=1)
        if d3[1:-1].max() <= d3max:
            dist = cKDTree(dense(E)).query(P)[0]
            return dict(mu=float(mu), max=float(dist.max()), at=int(np.argmax(dist)), share=float(np.mean(dist <= 0.25)), d3=float(d3[1:-1].max()))
    return None


def main():
    import build_track as BT
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True); ap.add_argument('--pkg', required=True)
    ap.add_argument('--zones', help='station ranges lo-hi[,lo-hi] (default: every owner window)')
    ap.add_argument('--json')
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C = np.array(T['center'])[:, :2]; n = len(C)
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NL = np.c_[-t[:, 1], t[:, 0]]
    cw = trackcfg.remap_stations(cfg, n, float(np.linalg.norm(np.roll(C, -1, 0) - C, axis=1).sum()), C=C)
    d3max = edge_gate.FITTED['world_d3']
    zones = [tuple(int(v) for v in z.split('-')) for z in a.zones.split(',')] if a.zones else None
    out = []
    for w in BT.owner_windows(cfg, cw, n=n):
        r = edges_spline.owner_readings(C, NL, w, n); sg = 1 if w['side'] == 'left' else -1
        for lo, hi in (zones or [(w['lo'], w['hi'])]):
            if not (w['lo'] <= lo and hi <= w['hi']):
                continue
            ks = np.array(sorted(k for k in r if lo <= k <= hi))
            if len(ks) < 8:
                continue
            P = C[ks] + sg * np.array([r[k] for k in ks])[:, None] * NL[ks]
            E = np.array(T[w['side']])[:, :2]
            sp_pkg = float(np.median(np.linalg.norm(E[ks[0] + 1:ks[-1] + 1] - E[ks[0]:ks[-1]], axis=1)))
            sp_max = float(np.percentile(np.linalg.norm(E[ks[0] + 1:ks[-1] + 1] - E[ks[0]:ks[-1]], axis=1), 95))
            gap = np.r_[False, np.diff(ks) > 3]
            row = dict(side=w['side'], lo=int(lo), hi=int(hi), stations=int(len(ks)), gaps=[(int(ks[j - 1]), int(ks[j])) for j in np.flatnonzero(gap)],
                       spacing_pkg_median=round(sp_pkg, 3), spacing_pkg_p95=round(sp_max, 3))
            for lab, s in (('s1.0', 1.0), ('pkg_median', sp_pkg), ('pkg_p95', sp_max)):
                row[lab] = smoothest(P, s, d3max)
            out.append(row)
            f = lambda v: f"max {v['max']:.3f} m, {v['share'] * 100:.1f} % within 0.25" if v else 'none'
            print(f"{w['side']:5s} {lo}-{hi} ({len(ks)} st, gaps {row['gaps']}): at d3 <= {d3max}: spacing 1.0 -> {f(row['s1.0'])}; "
                  f"package spacing {sp_pkg:.2f} -> {f(row['pkg_median'])}; p95 spacing {sp_max:.2f} -> {f(row['pkg_p95'])}")
    if a.json:
        json.dump(dict(pkg=a.pkg, world_d3=d3max, rows=out), open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
