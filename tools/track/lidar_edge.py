"""Road edges from the lidar point cloud (stage 1 evidence for circuits without a painted edge line; Buttonwillow, 20 Oct
2026). The EPT tiles of the track's survey (cache/<id>/ept/*.laz, fetched by build_scenery.lidar_points) are re-read for
Intensity; the points within a corridor of the centre are cached as cache/<id>/lidar_corridor.npz (x, y ENU, z, intensity,
class, return number). Per station, the points within +-W m along the track are binned across the normal (0.1 m bins,
measured outward from the current edge) and averaged: an elevation cross-profile and an intensity cross-profile.

    uv run --python 3.12 --with 'numpy,scipy,pyproj,laspy[lazrs]' python -I tools/track/lidar_edge.py --track <id> \
        --pkg tools/track/out/<id> [--extract] [--win 5]

Reads downloaded data only as numbers (python -I); writes the corridor cache and numbers.
"""
import argparse
import glob
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import trackcfg  # noqa: E402

R = 6378137.0


def frame(T):
    C = np.array(T['center'])[:, :2]; L = np.array(T['left'])[:, :2]; Rr = np.array(T['right'])[:, :2]
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    NL = np.c_[-tg[:, 1], tg[:, 0]]
    return C, tg, NL, ((L - C) * NL).sum(1), -((Rr - C) * NL).sum(1)


def extract(cfg, C, reach=25.0):
    """All points of the cached EPT tiles within `reach` m of the centre polyline, with intensity."""
    import laspy
    from scipy.spatial import cKDTree
    lat0, lon0 = cfg['origin']; cl = math.cos(math.radians(lat0))
    edir = os.path.join(cfg.cache, 'ept')
    # the corridor's EPSG:3857 box
    lon = lon0 + np.degrees(C[:, 0] / (R * cl)); lat = lat0 + np.degrees(C[:, 1] / R)
    mx = np.radians(lon) * R; my = R * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))
    bx0, bx1, by0, by1 = mx.min() - 60, mx.max() + 60, my.min() - 60, my.max() + 60
    kd = cKDTree(C); parts = []
    files = sorted(glob.glob(os.path.join(edir, '*.laz')))
    for k, f in enumerate(files):
        with laspy.open(f) as fh:
            h = fh.header
            if h.maxs[0] < bx0 or h.mins[0] > bx1 or h.maxs[1] < by0 or h.mins[1] > by1:
                continue
            p = fh.read()
        X = np.asarray(p.x); Y = np.asarray(p.y)
        lo = np.degrees(X / R); la = np.degrees(2 * np.arctan(np.exp(Y / R)) - np.pi / 2)
        x = np.radians(lo - lon0) * R * cl; y = np.radians(la - lat0) * R
        d, _ = kd.query(np.c_[x, y], distance_upper_bound=reach)
        m = np.isfinite(d)
        if m.any():
            parts.append(np.c_[x[m], y[m], np.asarray(p.z)[m], np.asarray(p.intensity)[m],
                               np.asarray(p.classification)[m], np.asarray(p.return_number)[m]].astype(np.float64))
        if k % 200 == 0:
            print(f'  {k}/{len(files)} tiles, {sum(len(q) for q in parts) / 1e6:.2f} M points', flush=True)
    P = np.vstack(parts)
    out = os.path.join(cfg.cache, 'lidar_corridor.npz')
    np.savez(out, x=P[:, 0].astype(np.float32), y=P[:, 1].astype(np.float32), z=P[:, 2].astype(np.float32),
             i=P[:, 3].astype(np.uint16), c=P[:, 4].astype(np.uint8), rn=P[:, 5].astype(np.uint8), C=C)
    print(f'corridor: {len(P) / 1e6:.2f} M points within {reach} m -> {out}')
    return out


def load(cfg):
    d = np.load(os.path.join(cfg.cache, 'lidar_corridor.npz'))
    return {k: d[k] for k in d.files}


U = np.round(np.arange(-4.5, 4.0001, 0.1), 2)   # bins across the normal, outward from the current edge (as edges_spline.U)


def profiles(D, C, tg, NL, hw, side, stations, win=5.0, ground_only=True, first_only=True):
    """Averaged cross-profiles at `stations` on `side`: (z, intensity, count) arrays of shape (len(stations), len(U)),
    bins outward from the current edge (u = 0 at the edge, + outside). Points within +-win m along the track."""
    from scipy.spatial import cKDTree
    sel = np.ones(len(D['x']), bool)
    if ground_only: sel &= D['c'] == 2
    if first_only: sel &= D['rn'] == 1
    x, y, z, I = D['x'][sel].astype(float), D['y'][sel].astype(float), D['z'][sel].astype(float), D['i'][sel].astype(float)
    kd = cKDTree(np.c_[x, y]); sg = 1 if side == 'left' else -1
    Z = np.full((len(stations), len(U)), np.nan); In = Z.copy(); N = np.zeros_like(Z)
    for r, s in enumerate(stations):
        E = C[s] + sg * hw[s] * NL[s]
        idx = kd.query_ball_point(E, math.hypot(win, 5.0))
        if not idx: continue
        idx = np.array(idx); dx = x[idx] - E[0]; dy = y[idx] - E[1]
        along = dx * tg[s, 0] + dy * tg[s, 1]; across = sg * (dx * NL[s, 0] + dy * NL[s, 1])
        m = (np.abs(along) <= win) & (across >= U[0] - 0.05) & (across <= U[-1] + 0.05)
        b = np.clip(np.round((across[m] - U[0]) / 0.1).astype(int), 0, len(U) - 1)
        n = np.bincount(b, minlength=len(U)).astype(float)
        zs = np.bincount(b, z[idx][m], minlength=len(U)); Is = np.bincount(b, I[idx][m], minlength=len(U))
        with np.errstate(invalid='ignore', divide='ignore'):
            Z[r] = np.where(n > 0, zs / n, np.nan); In[r] = np.where(n > 0, Is / n, np.nan)
        N[r] = n
    return Z, In, N


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--track', required=True); ap.add_argument('--pkg', required=True)
    ap.add_argument('--extract', action='store_true'); ap.add_argument('--reach', type=float, default=25.0)
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C, tg, NL, hl, hr = frame(T)
    if a.extract:
        extract(cfg, C, a.reach)


if __name__ == '__main__':
    main()
