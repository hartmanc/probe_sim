"""Merge the owner's per-window edge digitisations (compare/owner_edges.py, one JSON per outline window) into one lap of
evidence (Buttonwillow round 10, 23 Oct 2026: the owner drew red on both sides of all 41 round-9 outline windows).

    uv run --python 3.12 --with numpy,scipy python -I tools/track/compare/owner_merge.py \
        --dir tools/track/tracks/buttonwillow/owner/r10 --pkg tools/track/out/bw_r9e \
        --out tools/track/tracks/buttonwillow/owner/r10/merged.json

Every window's per-station red points are projected on the package's centre (the one the windows were cut from); a
station seen by several windows (the 150 m windows overlap by 25 m, a window also shows other legs of the lap, and the
close-ups repeat three stretches) gets one point per side: the weighted mean of the windows' readings, each weighted by
the point's distance from its frame's border (m, at least 0.5; a stroke near the border is a clipped or extrapolated end
of a line drawn for the middle of that frame) times the frame's resolution (0.12 / mpp: the 0.06 m/px close-ups count
double), so adjacent windows cross-fade over their overlap instead of stepping; every station where the readings
spread more than --tol (0.3 m) is listed with each window's reading. Points farther than --max-lat from the centre are no edge of
this road (another road in the frame) and are dropped. The green points (connector roads, paddock lanes, paved loops:
scenery extents, not the raced edge) are pooled and thinned to one per 1 m cell. Output: the owner_edges.py format
({left,right}_enu_xys [[x, y, s_m]], green_enu_xy) plus per station the windows that saw it and the disagreements.
"""
import argparse
import json
import os

import numpy as np


def normals(C):
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True)
    return np.c_[-t[:, 1], t[:, 0]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True); ap.add_argument('--pkg', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--fill', action='append', default=[], help="file:side:lo:hi (stations of --pkg): an earlier owner drawing "
                    "(owner_edges.py JSON) fills that side's stations lo..hi where no window has red (the owner's word that the line there stands)")
    ap.add_argument('--tol', type=float, default=0.3); ap.add_argument('--max-lat', type=float, default=20.0)
    a = ap.parse_args()
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C = np.array(T['center'])[:, :2]; n = len(C); sp = T['spacing_m']; L = n * sp; NL = normals(C)
    ob = os.path.basename(a.out)
    files = sorted(f for f in os.listdir(a.dir) if f.endswith('.json') and f not in (ob, ob.replace('.json', '_report.json'))
                   and 'half' in (json.load(open(os.path.join(a.dir, f))).get('frame') or {}))   # owner_edges.py window files only
    per = {'left': {}, 'right': {}}
    G = []
    dropped = 0
    for f in files:
        J = json.load(open(os.path.join(a.dir, f)))
        name = f[:-5]; s0 = J['frame']['s']; half = J['frame']['half']; cx, cy = J['frame']['centre_enu']; res = 0.12 / J['frame']['mpp']
        for side, sg in (('left', 1), ('right', -1)):
            for x, y, s_m in J[side + '_enu_xys']:
                k = int(round(s_m / sp)) % n
                lat = sg * float(((np.array([x, y]) - C[k]) * NL[k]).sum())
                if abs(lat) > a.max_lat:
                    dropped += 1; continue
                ds = abs(((k * sp - s0 + L / 2) % L) - L / 2)
                wb = max(half - max(abs(x - cx), abs(y - cy)), 0.5) * res
                per[side].setdefault(k, []).append((name, lat, ds, ds <= half, x, y, wb))
        G.extend(J['green_enu_xy'])
    fills = []; filled = {'left': [], 'right': []}
    for fz in a.fill:
        fpath, side, lo, hi = fz.split(':'); lo, hi = int(lo), int(hi); sg = 1 if side == 'left' else -1
        J = json.load(open(fpath)); got = 0
        P = np.array([[x, y] for x, y, *_ in J[side + '_enu_xys']], float)
        from scipy.spatial import cKDTree
        _, kk = cKDTree(C).query(P)
        for (x, y), k in zip(P, kk):
            k = int(k)
            if (k - lo) % n <= (hi - lo) % n and k not in per[side]:
                lat = sg * float(((np.array([x, y]) - C[k]) * NL[k]).sum())
                per[side].setdefault(('fill', k), []).append((os.path.basename(fpath), lat, 0.0, True, x, y, 1.0))
        for key in [q for q in per[side] if isinstance(q, tuple)]:
            k = key[1]; R = per[side].pop(key)
            per[side][k] = [(R[0][0], float(np.median([r[1] for r in R])), 0.0, True, 0, 0, 1.0)]; got += 1; filled[side].append(int(k))
        fills.append(dict(file=fpath, side=side, lo=lo, hi=hi, stations=got))
        print(f"fill {side} {lo}..{hi} from {fpath}: {got} stations")
    out = {'track': T.get('id', ''), 'src': f'owner_merge.py over {len(files)} windows of {a.dir} on {a.pkg}', 'frame': {'pkg': a.pkg, 'n': n, 'spacing_m': sp}}
    rep = {'windows': files, 'dropped_far': dropped, 'tol': a.tol, 'fills': fills}
    for side, sg in (('left', 1), ('right', -1)):
        pts, dis, nwin = [], [], {}
        for k in sorted(per[side]):
            R = per[side][k]
            v = np.array([r[1] for r in R])
            wt = np.array([r[6] for r in R])
            lat = float((v * wt).sum() / wt.sum())
            if len(R) > 1 and v.max() - v.min() > a.tol:
                dis.append(dict(k=k, s=round(k * sp, 1), spread=round(float(v.max() - v.min()), 3), merged=round(lat, 3),
                                readings={r[0]: [round(r[1], 3), round(r[6], 1)] for r in R}))
            q = C[k] + sg * NL[k] * lat
            pts.append([round(float(q[0]), 3), round(float(q[1]), 3), int(round(k * sp))])
            nwin[len(R)] = nwin.get(len(R), 0) + 1
        out[side + '_enu_xys'] = pts
        miss = np.ones(n, bool); miss[list(per[side])] = False
        runs = []
        k = 0
        while k < n:
            if miss[k]:
                j = k
                while j + 1 < n and miss[j + 1]: j += 1
                runs.append((k, j)); k = j + 1
            else:
                k += 1
        rep[side] = dict(stations=len(pts), of=n, by_window_count=nwin, disagreements=len(dis), missing_runs=[(a_, b_) for a_, b_ in runs if b_ - a_ >= 2],
                         disagree=dis)
    if G:
        Gp = np.array(G); cell = np.floor(Gp).astype(int); _, idx = np.unique(cell, axis=0, return_index=True); Gp = Gp[np.sort(idx)]
        out['green_enu_xy'] = [[round(float(x), 3), round(float(y), 3)] for x, y in Gp]
    else:
        out['green_enu_xy'] = []
    out['report'] = {s: {k: v for k, v in rep[s].items() if k != 'disagree'} for s in ('left', 'right')}
    out['report']['fills'] = fills
    out['filled'] = filled
    json.dump(out, open(a.out, 'w'), indent=0)
    json.dump(rep, open(a.out.replace('.json', '_report.json'), 'w'), indent=1)
    for side in ('left', 'right'):
        r = rep[side]
        print(f"{side}: {r['stations']} of {n} stations, seen by {r['by_window_count']} windows; {r['disagreements']} stations where windows differ by more than {a.tol} m; missing runs (>= 3 st): {r['missing_runs']}")
    print(f"green: {len(out['green_enu_xy'])} points; dropped {dropped} red points farther than {a.max_lat} m from the centre")


if __name__ == '__main__':
    main()
