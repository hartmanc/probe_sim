"""Rebuild the centre line and edges from the painted road (Google z20, tools/track/measure_paint.py), 18 Oct 2026.

    uv run --offline --python 3.12 --with numpy,scipy,rasterio,pyproj,shapely,pillow,requests,pandas,matplotlib \
        python tools/track/rebuild_from_paint.py [--fit-a 3e3] [--write]

Why: the v2 centre line keeps the shape of the logged GPS line (stiff fit), and the logged line cuts every corner:
the painted road midpoint is 2.5-5.6 m outside it at the apexes, so the driveable ribbon spilled onto the inside paint
and verges. A global datum shift does not explain it (best rigid fit changes the residual from 2.12 to 2.13 m rms).

Steps:
 1. target = painted midpoint offset per station (median 9, gaps interpolated, weight 0 where unmeasured);
 2. weighted smooth fit (build_laguna_v2.smooth_fit's operators, FIT_A lowered): each station moves along its own
    normal only, so station numbering and every scenery/ghost station range keep their cross-section;
 3. edges = painted edges re-expressed on the new normals; where unmeasured the old edges' world positions; where a
    pit-lane part touches the track edge the old world edge is kept (merge/split stays connected); median 9,
    Gaussian 2 m, slope <= 0.25 m per station, side >= 3 m, width cap 16 m;
 4. racing line (ghosts.json offset_m): moves with the centre (the logged line shares the centre's corner cut), then
    kept 0.9 m inside the new edges, smoothed;
 5. profile from DEM + lidar returns exactly as build_laguna_v2.py (lidar_correct, clean_profile, T6 repave crest).
Corners are re-detected (same anchors) only for radius_m; their station s is kept.
"""
import argparse, json, math, os, sys
import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.sparse import diags, identity
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import build_laguna as B  # noqa: E402
import build_laguna_v2 as V2  # noqa: E402

def slope_limit(v, lim, n):
    v = v.copy()
    for _ in range(3):
        for i in range(1, 2 * n):
            j = i % n; v[j] = max(v[j], v[(j - 1) % n] - lim)
        for i in range(2 * n - 2, -1, -1):
            j = i % n; v[j] = max(v[j], v[(j + 1) % n] - lim)
    return v

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--fit-a', type=float, default=1e4); ap.add_argument('--fit-b', type=float, default=1e2)
    ap.add_argument('--write', action='store_true')
    ap.add_argument('--bridge-win', type=int, default=25, help='stations each side of a bridge crossing whose paint measurements are discarded (shadows)')
    args = ap.parse_args()
    tp = os.path.join(B.OUT, 'track.json'); T = json.load(open(tp))
    gp = os.path.join(B.OUT, 'ghosts.json'); G = json.load(open(gp))
    SC = json.load(open(os.path.join(B.OUT, 'scenery.json')))
    C0 = np.array(T['center'])[:, :2]; n = len(C0)
    nl0 = B.left_normals(C0)
    Lw0 = np.array(T['left'])[:, :2]; Rw0 = np.array(T['right'])[:, :2]
    hl0 = ((Lw0 - C0) * nl0).sum(1); hr0 = -((Rw0 - C0) * nl0).sum(1)
    P = np.load(os.path.join(HERE, 'out', 'paint_edges.npz'))
    el, er = P['lat_left'], P['lat_right']
    ok = np.isfinite(el) & np.isfinite(er)
    # bridge shadows: the detector reads the shadow's edge as a painted line under every bridge (owner, 18 Oct 2026:
    # "There is no little kink here. This is straight underneath the bridge in real life"), so measurements within
    # +-bridge_win stations of each crossing are discarded and the edges interpolated across from the clean stations.
    shadow = np.zeros(n, bool)
    for b_ in SC.get('bridges', []):
        k0 = int(round(float(b_['s'])))
        for dd in range(-args.bridge_win, args.bridge_win + 1): shadow[(k0 + dd) % n] = True
    ok &= ~shadow
    print(f'bridge shadow mask: {int(shadow.sum())} stations at {[round(float(b_["s"])) for b_ in SC.get("bridges", [])]}')
    # drop single-station outliers against a 9-station median of the measured values
    idx = np.arange(n)
    def fill(a):
        return np.interp(idx, idx[ok], a[ok], period=n)
    elf, erf = median_filter(fill(el), 9, mode='wrap'), median_filter(fill(er), 9, mode='wrap')
    good = ok & (np.abs(el - elf) < 1.0) & (np.abs(er - erf) < 1.0)
    mid = (el + er) / 2
    # the fit target: the painted midpoint, de-noised along s (median 15, Gaussian 5 m over measured stations) so the
    # centre does not pick up the detector's station-to-station jitter
    midf = np.interp(idx, idx[good], mid[good], period=n)
    midf = gaussian_filter1d(median_filter(midf, 15, mode='wrap'), 5, mode='wrap')
    d = np.where(good, midf, 0.0)
    w = good.astype(float)
    # 2. weighted smooth fit
    D2 = V2.diffop(n, [(-1, 1), (0, -2), (1, 1)])
    D3 = V2.diffop(n, [(-1, -1), (0, 3), (1, -3), (2, 1)])
    Ax = D3 @ diags(nl0[:, 0]); Ay = D3 @ diags(nl0[:, 1])
    H = diags(w + 1e-3) + args.fit_a * (D2.T @ D2) + args.fit_b * (Ax.T @ Ax + Ay.T @ Ay)
    rhs = w * d - args.fit_b * (Ax.T @ (D3 @ C0[:, 0]) + Ay.T @ (D3 @ C0[:, 1]))
    e = spsolve(H.tocsc(), rhs)
    C = C0 + e[:, None] * nl0
    nl = B.left_normals(C)
    seg = np.linalg.norm(np.roll(C, -1, 0) - C, axis=1)
    # 3. edges on the new normals
    def lat_of(Wpts):  # signed lateral of world points (one per station) on the new frame
        return ((Wpts - C) * nl).sum(1)
    # bridge measurement gaps up to 40 stations by interpolating the painted edges (relative to the old frame)
    gidx = idx[good]
    nxt = np.searchsorted(gidx, idx) % len(gidx); prv = nxt - 1
    gap = (gidx[nxt] - gidx[prv]) % n
    usable = good | (gap <= max(40, 2 * args.bridge_win + 12))
    eli = np.interp(idx, gidx, el[good], period=n); eri = np.interp(idx, gidx, er[good], period=n)
    eli = np.where(good, el, eli); eri = np.where(good, er, eri)
    pl = lat_of(C0 + eli[:, None] * nl0)
    pr = lat_of(C0 + eri[:, None] * nl0)
    ol, orr = lat_of(Lw0), -lat_of(Rw0)
    hl = np.where(usable, pl, ol); hr = np.where(usable, -pr, orr)
    keep = np.zeros((n, 2), bool); kd = cKDTree(C0)
    for part in (SC.get('pit_lane') or {}).get('parts', []):
        for E, gap in ((part['left'], part['gap_left']), (part['right'], part['gap_right'])):
            E = np.array(E)[:, :2]; _, ii = kd.query(E); le = ((E - C0[ii]) * nl0[ii]).sum(1)
            for i, l_, g in zip(ii, le, gap):
                if g <= 0.3: keep[i, 0 if l_ > 0 else 1] = True
    for k in range(2): keep[:, k] = np.convolve(keep[:, k].astype(int), np.ones(21, int), 'same') > 0
    # pit-out blend lane (cones s 122-375 on the left): the paved exit lane stays driveable track, the cones police it
    pc = SC.get('pit_exit_cones') or {}
    if pc: keep[int(pc['s0']) - 40:int(pc['s1']) + 1, 0] = True
    hl = np.where(keep[:, 0], ol, hl); hr = np.where(keep[:, 1], orr, hr)
    new = np.c_[hl, hr]
    for k in range(2):
        new[:, k] = gaussian_filter1d(median_filter(new[:, k], 15, mode='wrap'), 4, mode='wrap')
    new = np.maximum(new, 3.0)
    # sanity floor (Laguna's road is ~10-15 m): where the traced road is narrower than MIN_W (a repave seam or an inner
    # painted line read as the edge) give the width back toward the old NAIP edges, never past them
    MIN_W = 10.0
    oldw = np.c_[ol, orr]
    short = np.maximum(MIN_W - new.sum(1), 0.0)
    room = np.maximum(oldw - new, 0.0); rs = room.sum(1)
    give = np.where(rs > 1e-6, np.minimum(short, rs) / np.maximum(rs, 1e-6), 0.0)
    new = new + room * give[:, None]
    for k in range(2): new[:, k] = gaussian_filter1d(new[:, k], 2, mode='wrap')
    # where the team's logged line (good-GPS laps, ghost_line_debug e_gps) ran past the paint - the green-painted
    # aprons inside T5/T6/T9/T11 and similar, which the drivers used (the IMU curvature confirms the radius) - the
    # driveable edge follows that line plus GPS_MARGIN, never past the old NAIP edge
    GPS_MARGIN = 1.0
    dbg0 = np.load(os.path.join(HERE, 'cache', 'ghost_line_debug.npz'))
    eg = np.interp(idx, dbg0['grid'], dbg0['e_gps'], period=n)            # old frame, per old station
    egn = lat_of(C0 + eg[:, None] * nl0)                                  # on the refitted frame
    egn = gaussian_filter1d(egn, 2, mode='wrap')
    needL = np.minimum(egn + GPS_MARGIN, ol); needR = np.minimum(-egn + GPS_MARGIN, orr)
    new[:, 0] = np.maximum(new[:, 0], needL); new[:, 1] = np.maximum(new[:, 1], needR)
    wd = new.sum(1); new *= (np.minimum(wd, 16.0) / wd)[:, None]
    for k in range(2):
        new[:, k] = np.where(keep[:, k], np.maximum(new[:, k], np.where(k == 0, ol, orr)), new[:, k])
        new[:, k] = slope_limit(new[:, k], 0.25, n)
    hl, hr = new[:, 0], new[:, 1]
    # 3b. uniform stations: same start point, spacing L/n; old station k sits at arc station u[k] on the new curve
    C1 = C
    seg1 = np.linalg.norm(np.roll(C1, -1, 0) - C1, axis=1)
    Ltot = float(seg1.sum()); sp = Ltot / n
    acc = np.r_[0, np.cumsum(seg1)]                      # arc length at old station k (k = 0..n)
    u = acc[:n] / sp                                    # new (fractional) station of old station k
    jj = np.arange(n) * sp
    C = np.c_[np.interp(jj, acc, np.r_[C1[:, 0], C1[0, 0]]), np.interp(jj, acc, np.r_[C1[:, 1], C1[0, 1]])]
    nl = B.left_normals(C)
    def to_new(a):  # per-old-station value -> per-new-station value
        return np.interp(np.arange(n), u, a, period=n)
    hl, hr = to_new(hl), to_new(hr)
    hl0n, hr0n = to_new(hl0), to_new(hr0)
    e_new = to_new(e)
    # 4. racing line: keep its world position, then build_ghosts' bounded solve against the new edges
    sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'ghosts')); import build_ghosts as BG
    sg = G['s_grid_m']; off = np.array(G['line']['offset_m'], float); m = len(off)
    dbg = np.load(os.path.join(HERE, 'cache', 'ghost_line_debug.npz'))
    gi_old = np.arange(m) * sg
    def world_line(eo):  # offsets on the old grid -> world points
        k = gi_old.astype(int) % n
        return C0[k] + eo[:, None] * nl0[k]
    Wl, Wg = world_line(off), world_line(dbg['e_gps'])
    sq, lq = B.project(C, Wl); o_ = np.argsort(sq)
    grid = np.arange(m) * sg
    off_kept = np.interp(grid, sq[o_], lq[o_], period=n)
    sq, lq = B.project(C, Wg); o_ = np.argsort(sq)
    e_gps = np.interp(grid, sq[o_], lq[o_], period=n)
    gi = grid.astype(int)
    Pg = C[gi]; nlg, _ = BG.left_normals(Pg)
    hwg, hwrg = hl[gi], hr[gi]
    lim = BG.smooth_bound(np.maximum(hwg - BG.MARGIN, 0.5)); limr = BG.smooth_bound(np.maximum(hwrg - BG.MARGIN, 0.5))
    lim_n, limr_n = lim, limr
    lim = np.maximum(lim_n, np.minimum(e_gps, hwg - BG.KERB_MARGIN)); limr = np.maximum(limr_n, np.minimum(-e_gps, hwrg - BG.KERB_MARGIN))
    e_mc = BG.min_curvature_line(Pg, nlg, -limr, lim)
    target = e_mc + BG.NUDGE * (e_gps - e_mc)
    eline = BG.min_curvature_offsets(Pg, nlg, -limr, lim, target=target)
    off_grid = eline
    newoff = np.interp(np.arange(n), grid, eline, period=n)
    offs = np.interp(np.arange(n), grid, off_kept, period=n)
    # 5. profile
    box = (T['heightfield']['x0'], T['heightfield']['y0'], T['ortho']['x1'], T['ortho']['y1'])
    dem_s = B.Dem(box, sigma=0.7); z0 = T['z0_navd88']
    fr = np.array(B.FRACTIONS)
    lat = np.where(fr[None, :] < 0, -fr[None, :] * hl[:, None], -fr[None, :] * hr[:, None])
    PX = C[:, 0:1] + lat * nl[:, 0:1]; PY = C[:, 1:2] + lat * nl[:, 1:2]
    prof = gaussian_filter1d(dem_s(PX, PY) - z0, 1.5, axis=0, mode='wrap')
    prof = V2.lidar_correct(PX, PY, prof, z0)
    prof = V2.clean_profile(prof, lat)
    for a, b, c0, c1, why in V2.REPAVE_FIXES:
        zn, cv, rb, ra = V2.crest_fix(prof[:, 3], a, b, c0, c1)
        prof[a:b + 1] += (zn - prof[a:b + 1, 3])[:, None]
    Lp = C + hl[:, None] * nl; Rp = C - hr[:, None] * nl
    # checks
    oldprof = np.array(T['profile']['z'])
    kap = B.curvature(C, sigma=6); kap0 = B.curvature(C0, sigma=6)
    kap0n = to_new(kap0)
    seg_cs = np.diff(fr) * np.where(fr[1:] <= 0, hl[:, None], hr[:, None])
    cs = np.abs(np.diff(prof, axis=1)) / seg_cs
    rep = {
        'fit': {'A': args.fit_a, 'B': args.fit_b, 'measured_stations': int(good.sum()), 'covered_after_gap_fill': int(0)},
        'move_m': {'p50': float(np.median(np.abs(e))), 'p90': float(np.percentile(np.abs(e), 90)), 'max': float(np.abs(e).max())},
        'residual_mid_m': {'before_rms': float(np.sqrt((d[good] ** 2).mean())), 'after_rms': float(np.sqrt(((d - e)[good] ** 2).mean())),
                           'after_p90': float(np.percentile(np.abs(d - e)[good], 90))},
        'length_m': {'old': float(np.linalg.norm(np.roll(C0, -1, 0) - C0, axis=1).sum()), 'new': float(seg.sum()),
                     'seg_min': float(seg.min()), 'seg_max': float(seg.max())},
        'width_m': {'old_p50': float(np.median(hl0 + hr0)), 'new_p5': float(np.percentile(hl + hr, 5)), 'new_p50': float(np.median(hl + hr)),
                    'new_p95': float(np.percentile(hl + hr, 95))},
        'max_edge_step': float(np.abs(np.diff(np.c_[hl, hr], axis=0)).max()),
        'spacing_m': sp, 'old_station_shift_max_m': float(np.abs(u - np.arange(n)).max() * sp),
        'line_resolve_vs_kept_world': {'p50': float(np.median(np.abs(newoff - offs))), 'max': float(np.abs(newoff - offs).max())},
        'line_min_margin': float(min((hl - newoff).min(), (hr + newoff).min())),
        'centre_z_change_max': float(np.abs(prof[:, 3] - oldprof[:, 3]).max()),
        'cross_slope_max': float(cs.max()), 'cross_slope_inner_max': float(cs[:, 1:-1].max()),
        'curv_max_old_new': [float(np.abs(kap0).max()), float(np.abs(kap).max())],
        'flag_world_edge_move_gt4m': [int(i) for i in np.where((np.abs(hl - to_new(ol)) > 4) | (np.abs(hr - to_new(orr)) > 4))[0]],
        'world_edge_move_p50_p95_max': [float(np.median(np.abs(np.r_[hl - to_new(ol), hr - to_new(orr)]))),
                                         float(np.percentile(np.abs(np.r_[hl - to_new(ol), hr - to_new(orr)]), 95)),
                                         float(np.abs(np.r_[hl - to_new(ol), hr - to_new(orr)]).max())],
        'world_edge_inward_p50': [float(np.median(to_new(ol) - hl)), float(np.median(to_new(orr) - hr))],
    }
    table = {}
    smap = lambda s_old: float(np.interp(s_old, np.arange(n + 1), np.r_[u, n]))
    for c in T['corners'] + [{'turn': 'front straight', 's': 3500}]:
        so = c['s']; s = int(round(smap(so))) % n; nm = c.get('turn') or c['name']
        d_ = c.get('dir')
        inner = (hl[s] - newoff[s]) if d_ == 'left' else (hr[s] + newoff[s]) if d_ == 'right' else None
        table[nm] = {'s_old': so, 's_new': s, 'centre_move': round(float(e[so]), 2), 'left_old': round(float(hl0[so]), 2), 'left_new': round(float(hl[s]), 2),
                     'right_old': round(float(hr0[so]), 2), 'right_new': round(float(hr[s]), 2),
                     'line_old_vs_old_centre': round(float(off[int(so // sg)] if so // sg < m else 0), 2), 'line_new': round(float(newoff[s]), 2),
                     'line_to_inner_edge': None if inner is None else round(float(inner), 2),
                     'R_old': round(float(1 / max(abs(kap0[so]), 1e-6)), 1), 'R_new': round(float(1 / max(abs(kap[s]), 1e-6)), 1)}
    rep['table'] = table
    mv = np.c_[hl - to_new(ol), hr - to_new(orr)]
    rep['flag_detail'] = {int(i): [round(float(mv[i, 0]), 1), round(float(mv[i, 1]), 1)] for i in np.where(np.abs(mv).max(1) > 4)[0][::3]}
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    json.dump(rep, open(os.path.join(HERE, 'out', 'paint_rebuild_report.json'), 'w'), indent=1)
    np.savez(os.path.join(HERE, 'out', 'paint_rebuild.npz'), C0=C0, C=C, e=e, hl=hl, hr=hr, hl0=hl0, hr0=hr0, off=newoff, off0=offs, u=u, sp=sp)
    print(json.dumps({k: v for k, v in rep.items() if k != 'table'}, indent=1))
    for k, v in table.items(): print(k, v)
    if args.write:
        r3 = lambda a: np.round(a, 3).tolist()
        T['center'] = r3(np.c_[C, prof[:, 3]]); T['left'] = r3(np.c_[Lp, prof[:, 0]]); T['right'] = r3(np.c_[Rp, prof[:, -1]])
        T['profile']['z'] = r3(prof)
        T['spacing_m'] = round(sp, 6); T['length_m'] = round(Ltot, 3)
        for c in T['corners']:
            nm = c.get('turn') or c['name']
            c['s'] = round(table[nm]['s_new'] * sp, 1)   # s fields are metres (station * spacing_m)
            if c.get('radius_m'): c['radius_m'] = table[nm]['R_new']
        T['notes']['centre'] = (T['notes'].get('centre', '') + '; 18 Oct 2026: moved along its normals toward the painted road '
                                'midpoint traced on Google z20 imagery (tools/track/rebuild_from_paint.py; the logged GPS line cut every '
                                'corner by 2.5-5.6 m), then resampled to n equal stations (spacing L/n)')
        T['notes']['edges'] = ('painted road edge (white line / kerb / verge / dirt boundary) traced on Google z20 imagery, 18 Oct 2026; '
                               'unmeasured stations keep the NAIP edge; pit-lane joins keep the old edge; profile re-sampled from DEM + lidar')
        json.dump(T, open(tp, 'w'), separators=(',', ':'))
        G['line']['offset_m'] = [round(float(v), 3) for v in off_grid]
        G['line']['method'] = (G['line'].get('method', '') + '; 18 Oct 2026: re-solved on the painted-road track '
                               '(world position kept, then build_ghosts bounded solve)')
        json.dump(G, open(gp, 'w'), separators=(',', ':'))
        np.save(os.path.join(HERE, 'out', 'station_map_u.npy'), u)
        print('wrote', tp, gp, 'spacing', sp, 'length', Ltot)

if __name__ == '__main__':
    main()
