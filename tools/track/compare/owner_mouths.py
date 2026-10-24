"""Junction mouths the owner closed with red (Buttonwillow round 10, 23 Oct 2026): "A red line or arc across a junction
mouth is the course boundary there, and that's where a few cones should be placed to signal that part of the track is
blocked off." His green lines (the connector roads' pavement edges) end on his red; two such contacts on one side with
his red drawn between them are a mouth, and the red between them is the cone line for stage 3.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/owner_mouths.py --track buttonwillow \
        --owner tools/track/tracks/buttonwillow/owner/r10/merged.json --pkg tools/track/out/bw_r9e \
        --out tools/track/tracks/buttonwillow/owner/r10/mouths.json [--kink left:625:660] [--open left:4270:4330:why]

Contacts: green points within --touch (1.5 m) of his red on that side (the red interpolated along s where he drew
none), clustered along s (gaps <= 4 stations). Consecutive contacts at most --max-gap (60) stations apart with his own
red (not a --fill from an earlier drawing) over >= 90 % of the stations between are a mouth; the cone line is his red
between the two contacts (world ENU and lat / lon, one point per 2 m). --kink side:lo:hi: a mouth he left open with
no red across (a runoff the drivers use) whose cone line goes only across the side road at the kink of his green in
that range (the contact there), to the nearest point of another green line beyond it. --open side:lo:hi:why: a mouth
that keeps no cones (the pit entry the cars drive through), listed with its stations and its red line, cones False.
--across side:lo:hi:why (Sonoma round 14B): a mouth the owner named in words whose red arc meets only one green line (the
paddock-side mouth at T1, s ~166-179: his green ends on the arc at one end, the arc rejoins his edge line at the
other), declared by its stations on --pkg: a 'red across' mouth with cones on his red between them.
--step side:lo:hi:why (Sonoma round 14B): a junction where his red ENDS at one edge line and resumes on another (the
pit-exit lane's mouth after T1: his red along the blend line ends at s 222, resumes on the merged lane's outer edge at
s 229 where his green, the pit-lane edge, meets it): kind 'junction step', no cones (the cars drive through), its line
his red interpolated across the gap; the owner-reference gates leave it out like a mouth (edge_gate.OWNER_REF).
Each mouth is matched to the config's width-model junction it falls in (kind and source) for the record.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import trackcfg  # noqa: E402
from owner_kerbs import red_frame  # noqa: E402


def lonlat(cfg, x, y):
    lat0, lon0 = cfg['origin']; R = 6378137.0
    return round(lat0 + math.degrees(y / R), 7), round(lon0 + math.degrees(x / (R * math.cos(math.radians(lat0)))), 7)


def green_chains(G, link=1.5):
    from scipy.spatial import cKDTree
    par = list(range(len(G)))
    def f(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    for i, j in cKDTree(G).query_pairs(link):
        par[f(i)] = f(j)
    return np.array([f(i) for i in range(len(G))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True); ap.add_argument('--owner', required=True); ap.add_argument('--pkg', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--touch', type=float, default=1.5); ap.add_argument('--max-gap', type=int, default=60)
    ap.add_argument('--kink', action='append', default=[]); ap.add_argument('--open', action='append', default=[])
    ap.add_argument('--across', action='append', default=[])
    ap.add_argument('--step', action='append', default=[])
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json'))); n = T['n']; sp = T['spacing_m']
    M = json.load(open(a.owner))
    C, NL, hw = red_frame(T, M)
    from scipy.spatial import cKDTree
    G = np.array(M['green_enu_xy']); _, kg = cKDTree(C).query(G); latg = ((G - C[kg]) * NL[kg]).sum(1)
    gch = green_chains(G)
    # the width model's junction ranges, for the record (a circuit without a width model, Sonoma round 14B: none)
    J = (trackcfg.remap_stations(cfg, n, n * sp, C=C)['spline'].get('width_model') or {}).get('junctions', [])
    kinks = [(s.split(':')[0], int(s.split(':')[1]), int(s.split(':')[2])) for s in a.kink]
    opens = [(s.split(':')[0], int(s.split(':')[1]), int(s.split(':')[2]), s.split(':', 3)[3] if s.count(':') >= 3 else '') for s in a.open]
    inr = lambda k, lo, hi: (k - lo) % n <= (hi - lo) % n  # noqa: E731
    mouths, singles = [], []
    for side, sg in (('left', 1), ('right', -1)):
        drawn = hw[side + '_drawn'].copy()
        for k in (M.get('filled') or {}).get(side, []):
            drawn[k] = False
        d = sg * latg - hw[side][kg]
        ks = np.unique(kg[np.abs(d) <= a.touch])
        cl = []
        for k in ks:
            if cl and k - cl[-1][1] <= 4: cl[-1][1] = int(k)
            else: cl.append([int(k), int(k)])
        if len(cl) > 1 and cl[0][0] == 0 and cl[-1][1] == n - 1:
            cl[0][0] = cl[-1][0] - n; cl.pop()
        used = set()
        for i in range(len(cl)):
            if i in used:
                continue
            kk = next(((sd, lo, hi) for sd, lo, hi in kinks if sd == side and inr(cl[i][1] % n, lo, hi)), None)
            if kk:
                # the alternative section's mouth at the kink of his green: from the contact point across to the nearest
                # point of another green line
                sel = np.flatnonzero((np.abs(d) <= a.touch) & np.array([inr(int(k), kk[1], kk[2]) for k in kg]))
                if len(sel):
                    p0 = G[sel[np.argmin(np.abs(d[sel]))]]; c0 = gch[sel[0]]
                    other = np.flatnonzero(gch != gch[sel[np.argmin(np.abs(d[sel]))]])
                    q = G[other[np.argmin(np.linalg.norm(G[other] - p0, axis=1))]]
                    L = max(2, int(np.linalg.norm(q - p0) // 2) + 1)
                    line = [p0 + (q - p0) * t for t in np.linspace(0, 1, L)]
                    mouths.append(dict(side=side, lo=cl[i][0] % n, hi=cl[i][1] % n, kind='kink', cones=True, red_drawn=False,
                                       width_m=round(float(np.linalg.norm(q - p0)), 2),
                                       line_enu=[[round(float(x), 2), round(float(y), 2)] for x, y in line],
                                       line_latlon=[list(lonlat(cfg, x, y)) for x, y in line]))
                    used.add(i)
                    continue
            if i + 1 < len(cl):
                a0, b0 = cl[i][1], cl[i + 1][0]
                gap = b0 - a0
                between = np.arange(a0, b0 + 1) % n
                if 0 < gap <= a.max_gap and drawn[between].mean() >= 0.9:
                    ks_ = np.arange(cl[i][0], cl[i + 1][1] + 1) % n
                    lo_, hi_ = int(round((cl[i][0] + cl[i][1]) / 2)) % n, int(round((cl[i + 1][0] + cl[i + 1][1]) / 2)) % n
                    kl = np.arange(lo_, lo_ + (hi_ - lo_) % n + 1) % n
                    P = C[kl] + sg * hw[side][kl][:, None] * NL[kl]
                    P = P[::2] if len(P) > 3 else P
                    op = next((o for o in opens if o[0] == side and inr(lo_, o[1], o[2])), None)
                    jn = [j for j in J if j[0] in (side, 'both') and (inr(lo_, j[1], j[2]) or inr(hi_, j[1], j[2]))]
                    mouths.append(dict(side=side, lo=lo_, hi=hi_, s0=round(lo_ * sp, 1), s1=round(hi_ * sp, 1), kind='red across',
                                       cones=op is None, note=(op[3] if op else ''), red_drawn=True,
                                       width_m=round(float(np.linalg.norm(P[-1] - P[0])), 2),
                                       junction=[list(j[:5]) for j in jn],
                                       line_enu=[[round(float(x), 2), round(float(y), 2)] for x, y in P],
                                       line_latlon=[list(lonlat(cfg, x, y)) for x, y in P]))
                    used |= {i, i + 1}
                    continue
            singles.append(dict(side=side, lo=cl[i][0] % n, hi=cl[i][1] % n))
    for spec in a.across:
        side, lo_, hi_, why = spec.split(':', 3); lo_, hi_ = int(lo_), int(hi_); sg = 1 if side == 'left' else -1
        kl = np.arange(lo_, lo_ + (hi_ - lo_) % n + 1) % n
        if not hw[side + '_drawn'][kl].mean() >= 0.9:
            raise SystemExit(f'--across {spec}: his red is not drawn over {lo_}-{hi_}')
        P = C[kl] + sg * hw[side][kl][:, None] * NL[kl]
        P = P[::2] if len(P) > 3 else P
        if len(kl) % 2 == 0:
            P = np.r_[P, (C[kl[-1]] + sg * hw[side][kl[-1]] * NL[kl[-1]])[None]]
        mouths.append(dict(side=side, lo=lo_, hi=hi_, s0=round(lo_ * sp, 1), s1=round(hi_ * sp, 1), kind='red across', cones=True,
                           note=why, red_drawn=True, declared=True, width_m=round(float(np.linalg.norm(P[-1] - P[0])), 2), junction=[],
                           line_enu=[[round(float(x), 2), round(float(y), 2)] for x, y in P],
                           line_latlon=[list(lonlat(cfg, x, y)) for x, y in P]))
    for spec in a.step:
        side, lo_, hi_, why = spec.split(':', 3); lo_, hi_ = int(lo_), int(hi_); sg = 1 if side == 'left' else -1
        kl = np.arange(lo_, lo_ + (hi_ - lo_) % n + 1) % n
        if not (hw[side + '_drawn'][kl[0]] and hw[side + '_drawn'][kl[-1]]):
            raise SystemExit(f'--step {spec}: his red must be drawn at both ends')
        P = C[kl] + sg * hw[side][kl][:, None] * NL[kl]
        mouths.append(dict(side=side, lo=lo_, hi=hi_, s0=round(lo_ * sp, 1), s1=round(hi_ * sp, 1), kind='junction step', cones=False,
                           note=why, red_drawn=False, declared=True, width_m=round(float(np.linalg.norm(P[-1] - P[0])), 2), junction=[],
                           step_m=round(float(hw[side][kl[-1]] - hw[side][kl[0]]), 2),
                           line_enu=[[round(float(x), 2), round(float(y), 2)] for x, y in P],
                           line_latlon=[list(lonlat(cfg, x, y)) for x, y in P]))
    for m in mouths:
        print(f"{m['side']:5s} {m['lo']:5d}-{m['hi']:5d} {m['kind']:10s} {m['width_m']:6.1f} m cones {m['cones']} "
              f"{'; '.join(f'{j[3]} {j[1]}-{j[2]}' for j in m.get('junction', []))} {m.get('note', '')}")
    print('single contacts (no mouth):', [(s['side'], s['lo'], s['hi']) for s in singles])
    json.dump(dict(src=f"owner_mouths.py --owner {a.owner} --pkg {a.pkg} (stations of that package)", mouths=mouths, singles=singles), open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
