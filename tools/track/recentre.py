"""Centre refit to the painted-road midpoint, uniform stations, paint-step edges (stage 1 geometry; was
rebuild_from_paint.py, 18 Oct 2026).

Why: the v2 centre keeps the shape of the logged GPS line (stiff fit), and the logged line cuts every corner: at Laguna
the painted road midpoint was 2.5-5.6 m outside it at the apexes, so the driveable ribbon spilled onto the inside paint
and verges. A global datum shift does not explain it (best rigid fit changed the residual from 2.12 to 2.13 m rms), so
the fix is in the shape, not the frame.

Steps:
 1. target = painted midpoint offset per station (paint.measure on the current centre; bridge-shadow stations masked;
    single-station outliers over 1 m from a 9-station median dropped; median 15, Gaussian 5 m; weight 0 where
    unmeasured);
 2. weighted smooth fit (centre.smooth_fit's operators with fit_a / fit_b): each station moves along its own normal;
 3. edges = painted edges re-expressed on the new normals; where unmeasured the old edges' world positions; where a
    pit-lane part touches the track edge (or along the pit-exit blend lane) the old world edge is kept; median 15,
    Gaussian 4, side >= 3 m, a width floor (min_width) given back toward the old edges, where the team's logged line ran
    past the paint the edge follows it plus gps_margin (never past the old edge), width cap 16 m, slope <= 0.25 m per
    station. These edges are the prior of the spline fit (edges_spline.py), which replaces them almost everywhere;
 4. uniform stations: same start point, spacing L/n; old station k sits at new fractional station u[k].
Without logger laps the same fit runs on the OSM-based centre (no gps_margin term).
"""
import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve
from scipy.spatial import cKDTree

import centre as V2
import geo as B


def slope_limit(v, lim, n):
    v = v.copy()
    for _ in range(3):
        for i in range(1, 2 * n):
            j = i % n; v[j] = max(v[j], v[(j - 1) % n] - lim)
        for i in range(2 * n - 2, -1, -1):
            j = i % n; v[j] = max(v[j], v[(j + 1) % n] - lim)
    return v


def touch_mask(C0, nl0, pit_parts, dilate=21, gap=0.3):
    """(n, 2) bool: stations where a pit-lane part comes within `gap` m of the track edge (0.3: touches), left / right,
    dilated by `dilate` stations."""
    n = len(C0)
    keep = np.zeros((n, 2), bool); kd = cKDTree(C0)
    for part in pit_parts or []:
        for E, gp in ((part['left'], part['gap_left']), (part['right'], part['gap_right'])):
            E = np.array(E)[:, :2]; _, ii = kd.query(E); le = ((E - C0[ii]) * nl0[ii]).sum(1)
            for i, l_, g in zip(ii, le, gp):
                if g <= gap: keep[i, 0 if l_ > 0 else 1] = True
    for k in range(2): keep[:, k] = np.convolve(keep[:, k].astype(int), np.ones(dilate, int), 'same') > 0
    return keep


def merge_edges(C0, el, er, merge, log=B.log):
    """The circuit's own painted edge through the pit merges (19 Oct 2026; no-logger Laguna had the centre 2.6-3.0 m
    off at T1 because the pit-out merge was read as road). Where a pit-lane part comes within merge['gap'] m of the
    track edge (default 0.3: it touches; 3 m was tried on Laguna's T11 exit and spread the zone over the whole front
    straight), or along the pit-exit blend lane, the pit-side edge of the midpoint target is the blend boundary (the cone line's
    lateral where the cones run) or else the circuit's painted edge interpolated across the merge from the measured
    stations either side (relative to C0, linear in station). merge = {'parts': pit_lane parts, 'cones': [[x, y, z],
    ...] or None}. Returns el, er (copies) and the (n, 2) merge mask."""
    n = len(C0)
    nl0 = B.left_normals(C0)
    el, er = el.copy(), er.copy()
    mask = touch_mask(C0, nl0, merge.get('parts'), gap=merge.get('gap', 0.3))
    idx = np.arange(n)
    cone_lat = np.full(n, np.nan)
    pts = merge.get('cones')
    if pts is not None and len(pts) >= 2:
        q = np.array(pts)[:, :2]
        sq, lq = B.project(C0, q)
        sq_u = np.unwrap(sq * 2 * np.pi / n) * n / (2 * np.pi)
        o = np.argsort(sq_u)
        a, b = sq_u[o][0], sq_u[o][-1]
        ks = np.arange(int(np.ceil(a)), int(np.floor(b)) + 1)
        cone_lat[ks % n] = np.interp(ks, sq_u[o], lq[o])
        side = 0 if np.median(lq) > 0 else 1
        mask[ks % n, side] = True
        log(f"pit merges: cone line {int(np.ceil(a)) % n}..{int(np.floor(b)) % n} on the {'left' if side == 0 else 'right'} "
            f"is the blend boundary (lateral {np.nanmin(cone_lat):+.1f}..{np.nanmax(cone_lat):+.1f} m)")
    for k, (arr, sg) in enumerate(((el, 1), (er, -1))):
        m = mask[:, k]
        if not m.any():
            continue
        has_cone = m & np.isfinite(cone_lat) & (np.sign(np.nan_to_num(cone_lat)) == sg)
        arr[has_cone] = cone_lat[has_cone]
        rest = m & ~has_cone
        src = ~m & np.isfinite(arr)
        if rest.any() and src.sum() > 10:
            arr[rest] = np.interp(idx[rest], idx[src], arr[src], period=n)
        runs = np.flatnonzero(np.diff(np.r_[0, m.astype(int), 0]))
        rr = [f"{int(runs[j]) % n}..{int(runs[j + 1] - 1) % n}" for j in range(0, len(runs) - 1, 2)]
        log(f"pit merges, {'left' if k == 0 else 'right'}: {int(m.sum())} stations in {', '.join(rr)} ({int(has_cone.sum())} on "
            f"the cone line, {int(rest.sum())} interpolated from the painted edge either side)")
    return el, er, mask


def refit(C0, hl0, hr0, P, shadow_s, pit_parts, cones, e_gps, fit_a, fit_b, bridge_win=25, gps_margin=1.0,
          min_width=10.0, log=B.log, merge=None, width_cap=16.0):
    """C0 (n, 2) current centre with half-widths hl0/hr0; P = paint.measure(...) on C0; shadow_s = stations of bridge
    crossings (shadows); pit_parts = scenery pit_lane parts on C0 (their touch zones keep the old edges);
    cones = (s0, s1) of the pit-exit blend lane or None; e_gps = the logged racing line's lateral on C0 per station
    (None without logger); merge = {'parts', 'cones'} (merge_edges): the midpoint target takes the circuit's own edge
    through the pit merges (None = the measured edges as they are, how Laguna's logger build ran). Returns a dict."""
    n = len(C0)
    nl0 = B.left_normals(C0)
    Lw0 = C0 + hl0[:, None] * nl0; Rw0 = C0 - hr0[:, None] * nl0
    el, er = P['lat_left'], P['lat_right']
    # the midpoint target's edges: through the pit merges the circuit's own edge (the edges written out are unchanged)
    elm, erm = merge_edges(C0, el, er, merge, log=log)[:2] if merge else (el, er)
    ok = np.isfinite(el) & np.isfinite(er)
    # bridge shadows: the detector reads the shadow's edge as a painted line under every bridge (owner, 18 Oct 2026:
    # "There is no little kink here. This is straight underneath the bridge in real life"), so measurements within
    # +-bridge_win stations of each crossing are discarded and the edges interpolated across from the clean stations.
    shadow = np.zeros(n, bool)
    for k0 in shadow_s:
        for dd in range(-bridge_win, bridge_win + 1): shadow[(int(round(k0)) + dd) % n] = True
    ok &= ~shadow
    log(f'bridge shadow mask: {int(shadow.sum())} stations at {[int(round(s)) for s in shadow_s]}')
    idx = np.arange(n)

    def fill(a):
        return np.interp(idx, idx[ok], a[ok], period=n)
    elf, erf = median_filter(fill(el), 9, mode='wrap'), median_filter(fill(er), 9, mode='wrap')
    good = ok & (np.abs(el - elf) < 1.0) & (np.abs(er - erf) < 1.0)
    if merge:
        okm = np.isfinite(elm) & np.isfinite(erm) & ~shadow

        def fillm(a):
            return np.interp(idx, idx[okm], a[okm], period=n)
        elmf, ermf = median_filter(fillm(elm), 9, mode='wrap'), median_filter(fillm(erm), 9, mode='wrap')
        goodm = okm & (np.abs(elm - elmf) < 1.0) & (np.abs(erm - ermf) < 1.0)
    else:
        goodm = good
    mid = (elm + erm) / 2
    # the fit target: the painted midpoint, de-noised along s (median 15, Gaussian 5 m over measured stations) so the
    # centre does not pick up the detector's station-to-station jitter
    midf = np.interp(idx, idx[goodm], mid[goodm], period=n)
    midf = gaussian_filter1d(median_filter(midf, 15, mode='wrap'), 5, mode='wrap')
    d = np.where(goodm, midf, 0.0)
    w = goodm.astype(float)
    D2 = V2.diffop(n, [(-1, 1), (0, -2), (1, 1)])
    D3 = V2.diffop(n, [(-1, -1), (0, 3), (1, -3), (2, 1)])
    Ax = D3 @ diags(nl0[:, 0]); Ay = D3 @ diags(nl0[:, 1])
    H = diags(w + 1e-3) + fit_a * (D2.T @ D2) + fit_b * (Ax.T @ Ax + Ay.T @ Ay)
    rhs = w * d - fit_b * (Ax.T @ (D3 @ C0[:, 0]) + Ay.T @ (D3 @ C0[:, 1]))
    e = spsolve(H.tocsc(), rhs)
    C = C0 + e[:, None] * nl0
    nl = B.left_normals(C)

    def lat_of(Wpts):  # signed lateral of world points (one per station) on the new frame
        return ((Wpts - C) * nl).sum(1)
    # bridge measurement gaps up to 40 stations by interpolating the painted edges (relative to the old frame)
    gidx = idx[good]
    nxt = np.searchsorted(gidx, idx) % len(gidx); prv = nxt - 1
    gap = (gidx[nxt] - gidx[prv]) % n
    usable = good | (gap <= max(40, 2 * bridge_win + 12))
    eli = np.interp(idx, gidx, el[good], period=n); eri = np.interp(idx, gidx, er[good], period=n)
    eli = np.where(good, el, eli); eri = np.where(good, er, eri)
    pl = lat_of(C0 + eli[:, None] * nl0)
    pr = lat_of(C0 + eri[:, None] * nl0)
    ol, orr = lat_of(Lw0), -lat_of(Rw0)
    hl = np.where(usable, pl, ol); hr = np.where(usable, -pr, orr)
    keep = touch_mask(C0, nl0, pit_parts)
    # pit-out blend lane (cones on the left): the paved exit lane stays driveable track, the cones police it
    if cones: keep[int(cones[0]) - 40:int(cones[1]) + 1, 0] = True
    hl = np.where(keep[:, 0], ol, hl); hr = np.where(keep[:, 1], orr, hr)
    new = np.c_[hl, hr]
    for k in range(2):
        new[:, k] = gaussian_filter1d(median_filter(new[:, k], 15, mode='wrap'), 4, mode='wrap')
    new = np.maximum(new, 3.0)
    # sanity floor: where the traced road is narrower than min_width (a repave seam or an inner painted line read as the
    # edge) give the width back toward the old NAIP edges, never past them
    oldw = np.c_[ol, orr]
    short = np.maximum(min_width - new.sum(1), 0.0)
    room = np.maximum(oldw - new, 0.0); rs = room.sum(1)
    give = np.where(rs > 1e-6, np.minimum(short, rs) / np.maximum(rs, 1e-6), 0.0)
    new = new + room * give[:, None]
    for k in range(2): new[:, k] = gaussian_filter1d(new[:, k], 2, mode='wrap')
    # where the team's logged line (good-GPS laps) ran past the paint - the green-painted aprons inside T5/T6/T9/T11 and
    # similar, which the drivers used (the IMU curvature confirms the radius) - the driveable edge follows that line
    # plus gps_margin, never past the old NAIP edge
    if e_gps is not None:
        egn = lat_of(C0 + e_gps[:, None] * nl0)
        egn = gaussian_filter1d(egn, 2, mode='wrap')
        needL = np.minimum(egn + gps_margin, ol); needR = np.minimum(-egn + gps_margin, orr)
        new[:, 0] = np.maximum(new[:, 0], needL); new[:, 1] = np.maximum(new[:, 1], needR)
    wd = new.sum(1); new *= (np.minimum(wd, width_cap) / wd)[:, None]   # config centre.width_cap (Laguna 16 m)
    for k in range(2):
        new[:, k] = np.where(keep[:, k], np.maximum(new[:, k], np.where(k == 0, ol, orr)), new[:, k])
        new[:, k] = slope_limit(new[:, k], 0.25, n)
    hl, hr = new[:, 0], new[:, 1]
    # uniform stations: same start point, spacing L/n; old station k sits at arc station u[k] on the new curve
    seg1 = np.linalg.norm(np.roll(C, -1, 0) - C, axis=1)
    Ltot = float(seg1.sum()); sp = Ltot / n
    acc = np.r_[0, np.cumsum(seg1)]
    u = acc[:n] / sp
    jj = np.arange(n) * sp
    Cn = np.c_[np.interp(jj, acc, np.r_[C[:, 0], C[0, 0]]), np.interp(jj, acc, np.r_[C[:, 1], C[0, 1]])]

    def to_new(a):
        return np.interp(np.arange(n), u, a, period=n)
    rep = {
        'fit': {'A': fit_a, 'B': fit_b, 'measured_stations': int(good.sum())},
        'move_m': {'p50': float(np.median(np.abs(e))), 'p90': float(np.percentile(np.abs(e), 90)), 'max': float(np.abs(e).max())},
        'residual_mid_m': {'before_rms': float(np.sqrt((d[goodm] ** 2).mean())), 'after_rms': float(np.sqrt(((d - e)[goodm] ** 2).mean())),
                           'after_p90': float(np.percentile(np.abs(d - e)[goodm], 90))},
        'length_m': {'old': float(np.linalg.norm(np.roll(C0, -1, 0) - C0, axis=1).sum()), 'new': Ltot},
        'spacing_m': sp, 'old_station_shift_max_m': float(np.abs(u - np.arange(n)).max() * sp),
        'width_m': {'p5': float(np.percentile(hl + hr, 5)), 'p50': float(np.median(hl + hr)), 'p95': float(np.percentile(hl + hr, 95))},
    }
    log(f"recentre: move p50 {rep['move_m']['p50']:.2f} p90 {rep['move_m']['p90']:.2f} max {rep['move_m']['max']:.2f} m; painted-midpoint "
        f"residual rms {rep['residual_mid_m']['before_rms']:.2f} -> {rep['residual_mid_m']['after_rms']:.2f} m; length "
        f"{rep['length_m']['old']:.2f} -> {Ltot:.2f} m, spacing {sp:.6f}")
    return dict(C=Cn, hl=to_new(hl), hr=to_new(hr), u=u, sp=sp, L=Ltot, e=e, report=rep, keep=keep)
