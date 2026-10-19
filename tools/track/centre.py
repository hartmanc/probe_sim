"""Centreline, NAIP edges, profile and corners of the track pipeline (tools/track/build_track.py, stage 1 geometry).

Was build_laguna_v2.py (17 Oct 2026). The v2 centreline takes its shape from the race logger's GPS-driven line
(centreline.npy, whose curvature matches the IMU's alat/v^2 to r = 0.98) and moves it toward the imagery track centre
with a penalised least-squares fit (smooth_fit):

    minimise  sum (e - d)^2 + A * sum (D2 e)^2 + B * |D3 (G + e n)|^2

e = lateral move along the line's normals, d = offset of the imagery midpoint, D2 e keeps the move slowly varying so
the curvature profile stays the driven line's, D3 penalises curvature change (no kinks). Two passes: the second uses
edges re-detected along the pass-1 normals. Without logger laps the same fit starts from the OSM loop instead
(osm_centre), softly, and the painted-road midpoint decides the shape later (recentre.py).

Why not v1 (a spline through the coarse OSM nodes, recentred along its own normals): it kinked at OSM way junctions and
corner nodes, so corner radii came out 20-70 % too tight (T6 28 m vs 87 m driven) and ghost speeds implied 1.5-2.2 g.

Also here: the profile (DEM sigma 0.7 m, lidar_correct onto the ground returns, clean_profile, repave crest fixes),
the heightfield with the repave change carried in, and the corners (signed-curvature peaks near the anchors).
"""

import math
import os

import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.sparse import csr_matrix, diags, identity
from scipy.sparse.linalg import spsolve

import geo as B

WIDTH_MIN, WIDTH_MAX = 2 * B.HALF_MIN, 2 * B.HALF_MAX  # total paved width clamp of the NAIP edges (9-17 m)
SIDE_MIN = 3.0  # neither side closer than this to the centre
RADIUS_TOL = 0.25  # corner min radius within 25 % of centreline.npy's
EDGE_JUMP = 0.5  # m, max lateral edge change between adjacent stations
KAPPA_SIGMA = 7.5  # m, Gaussian smoothing for radius comparisons ("over 15 m")
CORNER_WIN = 60
CROSS_HARD_V2 = 0.18  # the Corkscrew's T8->T8A transition reaches 17 % on the v2 cross-sections (lidar, planar)
EDGE_SEG_MAX = 0.20  # outermost profile segments may meet a kerb or verge lip (Rainey inside, T8 exit)


def diffop(m, coefs):
    i = np.arange(m)
    r, c, v = [], [], []
    for k, w in coefs:
        r.append(i)
        c.append((i + k) % m)
        v.append(np.full(m, float(w)))
    return csr_matrix((np.concatenate(v), (np.concatenate(r), np.concatenate(c))), shape=(m, m))


def raw_edges(C, ortho, reach=13.0, step=0.3):
    """Per-side half-widths along C's normals, robust-smoothed, not clamped.

    v1's classifier (build_laguna.detect_edges) plus kerbs: at 0.6 m/px the red-and-white kerbs blur to a bright
    pink (R > G ~ B), which v1 counted as dirt, so its edges stopped at the white line and the kerbs (driveable,
    and used by the drivers, see the GPS lines at T5 exit) fell outside the track. Kerbs now count like paint:
    bright runs up to 1.5 m wide are kept. Median filter 25 m (v1 41 m) so short kerbs survive."""
    if not hasattr(ortho, "gb"):
        ortho.gb = ortho.img[..., 1] - ortho.img[..., 2]
        ortho.rg = ortho.img[..., 0] - ortho.img[..., 1]
    n = len(C)
    nl = B.left_normals(C)
    offs = np.arange(-reach, reach + 1e-9, step)
    X = C[:, 0:1] + offs[None, :] * nl[:, 0:1]
    Y = C[:, 1:2] + offs[None, :] * nl[:, 1:2]
    val = ortho.sample(ortho.mean, X, Y)
    warm = ortho.sample(ortho.warm, X, Y)
    gb = ortho.sample(ortho.gb, X, Y)
    rg = ortho.sample(ortho.rg, X, Y)
    mid = np.abs(offs) <= 2.5
    vref = gaussian_filter1d(np.median(val[:, mid], 1), 15, mode="wrap")[:, None]
    wref = gaussian_filter1d(np.median(warm[:, mid], 1), 15, mode="wrap")[:, None]
    road = (warm < wref + 0.035) & (val < vref + 0.085) & (val > vref - 0.12)
    paint = (val >= vref + 0.085) & (warm < wref + 0.05)
    kerb = (val >= vref + 0.04) & (rg >= 0.02) & (gb <= 0.025) & (warm <= wref + 0.14) & ~road
    cls = np.where(road, 1, np.where(paint | kerb, 2, 0))
    gap = int(round(1.8 / step))
    c = len(offs) // 2
    half = np.full((n, 2), np.nan)
    ok = (cls[:, c - 3:c + 4] > 0).mean(1) >= 0.6
    pmax = int(round(1.5 / step))
    for side, sgn in ((0, +1), (1, -1)):
        for i in range(n):
            if not ok[i]:
                continue
            run, prun, last, found = 0, 0, 0, False
            for k in range(1, c + 1):
                v = cls[i, c + sgn * k]
                if v == 1:
                    last, run, prun = k, 0, 0
                elif v == 2:
                    prun += 1
                    run = 0
                    if prun > pmax:
                        last = k - prun + int(round(0.6 / step))
                        found = True
                        break
                    last = k
                else:
                    run += 1
                    prun = 0
                    if run >= gap:
                        found = True
                        break
            if found:
                half[i, side] = (last + 0.5) * step
    raw_ok = np.isfinite(half)
    stats = {"centre_on_asphalt": float(ok.mean()), "left_found": float(raw_ok[:, 0].mean()),
             "right_found": float(raw_ok[:, 1].mean()), "kerb_px": float(kerb.mean())}
    out = np.empty_like(half)
    idx = np.arange(n)
    for side in range(2):
        h = half[:, side]
        good = np.isfinite(h) & (h >= 2.0)
        h = np.interp(idx, idx[good], h[good], period=n)
        h = median_filter(h, size=25, mode="wrap")
        out[:, side] = np.clip(gaussian_filter1d(h, 8, mode="wrap"), 2.0, 12.0)
    return out, stats, raw_ok


def smooth_fit(P, d, fit_a, fit_b):
    """Move closed 1 m polyline P laterally toward offsets d, keeping its curvature profile and removing kinks:
    minimise sum (e - d)^2 + fit_a * sum (D2 e)^2 + fit_b * |D3 (P + e n)|^2."""
    m = len(P)
    nl = B.left_normals(P)
    D2 = diffop(m, [(-1, 1), (0, -2), (1, 1)])
    D3 = diffop(m, [(-1, -1), (0, 3), (1, -3), (2, 1)])
    Ax = D3 @ diags(nl[:, 0])
    Ay = D3 @ diags(nl[:, 1])
    H = identity(m) + fit_a * (D2.T @ D2) + fit_b * (Ax.T @ Ax + Ay.T @ Ay)
    rhs = d - fit_b * (Ax.T @ (D3 @ P[:, 0]) + Ay.T @ (D3 @ P[:, 1]))
    e = spsolve(H.tocsc(), rhs)
    return P + e[:, None] * nl, e


CORR_SIGMA = 4.0  # m, along-s smoothing of the lidar correction
XS_TOL = 0.04  # m, how far the edge points may leave the fitted cross-section
XS_RES = 0.02  # m, how far any point may leave the section's quadratic (banking + crown)
LONG_MEDIAN, LONG_SIGMA = 5, 1.5  # stations / m: final along-s clean-up of every profile column


def clean_profile(prof, lat):
    """Remove short-wavelength artefacts while keeping banking, crown and real crests/sags (>~10 m long).

    Cross-section: a line in lateral offset (the banking plane) is fitted to the five inner points; the inner
    points keep their own values, the two edge points may differ from the fit by at most XS_TOL (they otherwise
    land on kerb faces, berms or verge drops; Rainey's inside edge was 0.6 m up a berm).
    Along s: a 5-station median then a 1.5 m Gaussian on every column, which removes the 1 m noise of the
    DEM/lidar (it implied vertical radii of 20-150 m everywhere) and leaves the Corkscrew crest (~20 m long)."""
    out = prof.copy()
    for i in range(len(prof)):
        x = lat[i, 1:6]
        cf = np.polyfit(x, prof[i, 1:6], 1)
        for k in (0, 6):
            fit = np.polyval(cf, lat[i, k])
            out[i, k] = fit + np.clip(prof[i, k] - fit, -XS_TOL, XS_TOL)
        # whole section: banking + crown as a quadratic; the points keep at most XS_RES of their own wiggle
        # (the Corkscrew and Rainey sections zig-zagged by +-0.13 m column to column)
        q = np.polyfit(lat[i], out[i], 2)
        fitq = np.polyval(q, lat[i])
        out[i] = fitq + np.clip(out[i] - fitq, -XS_RES, XS_RES)
    out = median_filter(out, size=(LONG_MEDIAN, 1), mode="wrap")
    return gaussian_filter1d(out, LONG_SIGMA, axis=0, mode="wrap")


LIDAR_POINTS = None   # path of the box's lidar point cache (build_track.py stage 1)


def lidar_correct(PX, PY, prof, z0, radius=1.0, max_corr=1.0):
    """Pull the DEM profile onto the lidar point cloud's ground returns (class 2), median within 1 m of each
    profile point. The DEM is the same 2017 lidar, gridded and smoothed; at a few places it departs from the
    returns on the road: 0.2 m low over s~150-185 (the T1 footbridge), 0.45 m high at Rainey's inside edge
    (a barrier/berm bleeding into the smoothed grid). Gaps are filled along s, outliers median-filtered and the
    correction smoothed with a CORR_SIGMA Gaussian. Differences over 1 m are bridge decks classed as ground
    (s~1835-1846) and are ignored. 
    Reads the box-keyed point cache that stage 1 fetches before the profile (LIDAR_POINTS, set by build_track.py);
    a missing cache is an error, never a silent fallback to the DEM (geometry would depend on whether the scenery
    stage had run before)."""
    path = LIDAR_POINTS
    if not path or not os.path.exists(path):
        raise SystemExit(f"lidar_correct: no lidar point cache ({path}); stage 1 fetches it from the config's lidar_ept "
                         "before the profile")
    from scipy.spatial import cKDTree

    P = np.load(path)
    m = P["c"] == 2
    tree = cKDTree(np.c_[P["x"][m], P["y"][m]])
    z = P["z"][m].astype(float) - z0
    corr = np.zeros_like(prof)
    have = np.zeros(prof.shape, bool)
    for k in range(prof.shape[1]):
        for i, idx in enumerate(tree.query_ball_point(np.c_[PX[:, k], PY[:, k]], radius)):
            if len(idx) >= 3:
                d = np.median(z[idx]) - prof[i, k]
                if abs(d) <= max_corr:
                    corr[i, k], have[i, k] = d, True
    before = np.abs(corr[have])
    # per column: fill stations without returns from their neighbours (zeros there made steps), drop single-station
    # outliers (3-5 returns per median are noisy), then smooth over a few metres: the correction is meant to
    # remove the DEM's metre-scale offsets, not to add the returns' centimetre noise
    idx = np.arange(len(corr))
    for k in range(corr.shape[1]):
        h = have[:, k]
        if h.sum() > 10:
            corr[:, k] = np.interp(idx, idx[h], corr[h, k], period=len(corr))
    corr = median_filter(corr, size=(7, 1), mode="wrap")
    corr = gaussian_filter1d(corr, CORR_SIGMA, axis=0, mode="wrap")
    B.log(f"lidar correction of the profile: {have.mean() * 100:.1f}% of points covered; |DEM - returns| median "
          f"{np.median(before):.3f} m, p99 {np.percentile(before, 99):.2f} m, max {before.max():.2f} m; "
          f"applied max {np.abs(corr).max():.2f} m")
    return prof + corr


def vertical_radius(z, i, sigma=3.0):
    zs = gaussian_filter1d(z, sigma, mode="wrap")
    k = np.gradient(np.gradient(zs))
    return 1 / k[i] if abs(k[i]) > 1e-9 else np.inf


def crest_fix(z, a, b, c0, c1, sag_r=1500.0, crest_r=300.0, w_fit=0.05):
    """Rebuild z[a..b] from its second differences c (bounded least squares): smooth c, end height and slope at b
    matched, c <= 0 in [c0, c1), -1/crest_r <= c <= 1/sag_r elsewhere, loose fidelity to z outside [c0, c1)."""
    from scipy.optimize import lsq_linear

    zs = gaussian_filter1d(z, 1.5, mode="wrap")
    L = b - a
    za, zb = zs[a], zs[b]
    ma, mb = (zs[a + 1] - zs[a - 1]) / 2, (zs[b + 1] - zs[b - 1]) / 2
    K = np.arange(L + 1)
    M = np.maximum(0, K[:, None] - np.arange(L)[None, :]).astype(float)
    D = (np.eye(L, k=1) - np.eye(L))[:-1]
    zone = (np.arange(a, b) >= c0) & (np.arange(a, b) < c1)
    fit = np.r_[~zone, True].astype(float)[:, None]
    A = np.vstack([D, 1e3 * np.ones((1, L)), 1e3 * M[-1:], w_fit * fit * M])
    rhs = np.r_[np.zeros(L - 1), 1e3 * (mb - ma), 1e3 * (zb - za - L * ma), w_fit * fit[:, 0] * (zs[a:b + 1] - za - K * ma)]
    c = lsq_linear(A, rhs, bounds=(np.full(L, -1 / crest_r), np.where(zone, 0.0, 1 / sag_r))).x
    zn = za + K * ma + M @ c
    zn += (z[a] - zn[0]) + (np.arange(L + 1) / L) * ((z[b] - zn[-1]) - (z[a] - zn[0]))  # exact end heights
    apex = int(np.argmax(gaussian_filter1d(np.gradient(np.gradient(gaussian_filter1d(z, 3, mode="wrap"))), 2)[c0:c1])) + c0
    znew = z.copy()
    znew[a:b + 1] = zn
    return zn, c, vertical_radius(z, apex), vertical_radius(znew, apex)


def kappa(P, sigma=KAPPA_SIGMA):
    return gaussian_filter1d(B.curvature(P, 0), sigma, mode="wrap")




# ---------------------------------------------------------------- stage 1 building blocks
def osm_box(P):
    """Heightfield / ortho box from the stitched OSM loop (v1's box, kept by every later build)."""
    D, _ = B.resample_closed(P, n=None, smooth=0.0, k=1)
    C0, _ = B.resample_closed(D[::5], smooth=len(D[::5]) * 0.25 ** 2)
    lo = C0.min(0) - B.MARGIN - 20
    hi = C0.max(0) + B.MARGIN + 20
    box = tuple(float(v) for v in (math.floor(lo[0] / 10) * 10, math.floor(lo[1] / 10) * 10,
                                   math.ceil(hi[0] / 10) * 10, math.ceil(hi[1] / 10) * 10))
    return box, C0


def orient(P, ref=None, direction="ccw"):
    """Turn the OSM loop to the driving order: the logger's (ref = centreline.npy) or the configured direction."""
    if ref is not None:
        gi, _ = B.project(ref, P)
        if np.angle(np.exp(1j * 2 * np.pi * np.diff(np.r_[gi, gi[:1]]) / len(ref))).sum() < 0:
            P = P[::-1].copy()
        return P
    area = 0.5 * np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1])
    if (area > 0) != (direction == "ccw"):
        P = P[::-1].copy()
    return P


def roll_to(C, p0):
    """Roll closed 1 m loop C so station 0 is the projection of point p0, exact whole-metre resample."""
    s0, _ = B.project(C, np.asarray(p0, float)[None])
    m = len(C)
    idx = np.arange(m)
    k = (float(s0[0]) + idx) % m
    C2 = np.c_[np.interp(k, idx, C[:, 0], period=m), np.interp(k, idx, C[:, 1], period=m)]
    return B.resample_closed(C2, smooth=0.0)


def logger_centre(G, ortho, fit_a, fit_b, log=B.log):
    """v2 centre: the GPS-driven line (index 0 = start/finish, driving order) toward the NAIP midpoint, two passes."""
    Gs, LG = B.resample_closed(G, n=len(G), smooth=0.0)  # uniform 1 m, starts at G[0]
    half, st, _ = raw_edges(Gs, ortho)
    log("edges along GPS line:", {k: round(v, 3) for k, v in st.items() if isinstance(v, float)})
    d = (half[:, 0] - half[:, 1]) / 2
    C1, e1 = smooth_fit(Gs, d, fit_a, fit_b)
    log(f"pass 1: midpoint offset |d| median {np.median(np.abs(d)):.2f} max {np.abs(d).max():.2f} m; "
        f"fit residual |e-d| p95 {np.percentile(np.abs(e1 - d), 95):.2f} max {np.abs(e1 - d).max():.2f} m")
    C1, _ = B.resample_closed(C1, smooth=0.0)
    # pass 2 (the recentre): edges along the pass-1 normals give midpoint positions; the fit is redone from the GPS
    # line toward them, so the stiffness bounds the total move from the driven shape
    half, st, _ = raw_edges(C1, ortho)
    log("edges along pass-1 centre:", {k: round(v, 3) for k, v in st.items() if isinstance(v, float)})
    M = C1 + ((half[:, 0] - half[:, 1]) / 2)[:, None] * B.left_normals(C1)
    sq, lq = B.project(Gs, M)
    o = np.argsort(sq)
    d = np.interp(np.arange(len(Gs)), sq[o], lq[o], period=len(Gs))
    C2, e2 = smooth_fit(Gs, d, fit_a, fit_b)
    log(f"pass 2: midpoint offset from GPS line |d| median {np.median(np.abs(d)):.2f} max {np.abs(d).max():.2f} m; "
        f"residual |e-d| p95 {np.percentile(np.abs(e2 - d), 95):.2f} max {np.abs(e2 - d).max():.2f} m")
    C2, _ = B.resample_closed(C2, smooth=0.0)
    C, L = roll_to(C2, G[0])
    return C, L, LG


def osm_centre(C0, ortho, sf, fit_a, fit_b, log=B.log):
    """No-logger start: the smoothed OSM loop moved toward the NAIP midpoint (same fit, two passes), station 0 at the
    timing line sf. Only a starting point: the painted-road midpoint sets the final shape (recentre.py)."""
    P, _ = B.resample_closed(C0, smooth=0.0)
    for k in range(2):
        half, st, _ = raw_edges(P, ortho)
        d = (half[:, 0] - half[:, 1]) / 2
        P, e = smooth_fit(P, d, fit_a, fit_b)
        log(f"OSM centre pass {k + 1}: NAIP midpoint offset |d| median {np.median(np.abs(d)):.2f} max {np.abs(d).max():.2f} m; "
            f"move p95 {np.percentile(np.abs(e), 95):.2f} m")
        P, _ = B.resample_closed(P, smooth=0.0)
    C, L = roll_to(P, sf)
    return C, L


def naip_edges(C, ortho):
    """v2 edges: NAIP asphalt extent per side along C's normals, width clamped 9-17 m, sides at least SIDE_MIN."""
    half, st, raw_ok = raw_edges(C, ortho)
    width = np.clip(half.sum(1), WIDTH_MIN, WIDTH_MAX)
    off = (half[:, 0] - half[:, 1]) / 2  # midpoint offset (+left) from the centre
    hl = np.maximum(width / 2 + off, SIDE_MIN)
    hr = np.maximum(width / 2 - off, SIDE_MIN)
    return hl, hr, st, raw_ok


def lateral(hl, hr):
    fr = np.array(B.FRACTIONS)
    return np.where(fr[None, :] < 0, -fr[None, :] * hl[:, None], -fr[None, :] * hr[:, None])  # +left


def profile(C, hl, hr, dem_s, z0, repave_fixes, log=B.log):
    """Cross-section heights (profile fractions piecewise: f<0 scales the left half-width, f>0 the right, as
    src/physics/track.ts reads them): DEM smoothed sigma 0.7 m, 1.5 m Gaussian along s, lidar_correct, clean_profile,
    then the repave crest fixes (same height change across the section, banking kept). Returns prof and the centre
    height change of the repave fixes (for the heightfield)."""
    n = len(C)
    nl = B.left_normals(C)
    lat = lateral(hl, hr)
    PX = C[:, 0:1] + lat * nl[:, 0:1]
    PY = C[:, 1:2] + lat * nl[:, 1:2]
    prof = gaussian_filter1d(dem_s(PX, PY) - z0, 1.5, axis=0, mode="wrap")
    prof = lidar_correct(PX, PY, prof, z0)
    prof = clean_profile(prof, lat)
    resurface = np.zeros(n)
    for a, b, c0, c1, why in repave_fixes:
        zn, cv, rb, ra = crest_fix(prof[:, 3], a, b, c0, c1)
        resurface[a:b + 1] = zn - prof[a:b + 1, 3]
        log(f"repave fix {why}: s={a}..{b}, crest zone {c0}..{c1}; max height change {np.abs(resurface).max():.2f} m; "
            f"vertical radius at the apex before {rb:+.0f} m, after {ra:+.0f} m (+ sag, - crest); gentlest sag left "
            f"in the window R {1 / max(cv.max(), 1e-9):.0f} m")
    return prof + resurface[:, None], resurface


def quad_eval(xs, ys, x):
    """value at x of the least-squares quadratic through (xs, ys) (a station's cross-section)."""
    q = np.polyfit(np.asarray(xs, float), np.asarray(ys, float), 2)
    return float(np.polyval(q, x))


def reprofile(prof, hl_old, hr_old, hl_new, hr_new):
    """Profile columns at moved edges, re-evaluated from each station's cross-section quadratic; the centre column is
    kept (the method of every edge step since 18 Oct 2026: fit_edges_spline.py, the declared straights)."""
    lo, ln = lateral(hl_old, hr_old), lateral(hl_new, hr_new)
    out = prof.copy()
    ci = B.FRACTIONS.index(0)
    for k in np.nonzero((np.abs(hl_new - hl_old) > 1e-9) | (np.abs(hr_new - hr_old) > 1e-9))[0]:
        q = np.polyfit(lo[k], prof[k], 2)
        out[k] = np.polyval(q, ln[k])
        out[k, ci] = prof[k, ci]
    return out


def heightfield(box, dem, z0, C, hl, hr, resurface):
    """Unsmoothed DEM on a 2 m grid over the box, minus z0; the repave change carried in under and just beside the road
    (full to 2 m beyond the edge, fading out by 12 m)."""
    nx = int(round((box[2] - box[0]) / B.HF_DX)) + 1
    ny = int(round((box[3] - box[1]) / B.HF_DX)) + 1
    gx, gy = np.meshgrid(box[0] + np.arange(nx) * B.HF_DX, box[1] + np.arange(ny) * B.HF_DX)
    hf = (dem(gx, gy) - z0).astype("<f4")
    if np.any(resurface):
        from scipy.spatial import cKDTree

        idx = np.where(resurface != 0)[0]
        tree = cKDTree(C[idx])
        dist, j = tree.query(np.c_[gx.ravel(), gy.ravel()], distance_upper_bound=40)
        ok = np.isfinite(dist)
        st = idx[np.minimum(j, len(idx) - 1)]
        half = np.maximum(hl[st], hr[st])
        w = np.clip(1 - (dist - half - 2.0) / 10.0, 0, 1) * ok
        hf = (hf.ravel() + (w * resurface[st]).astype("<f4")).reshape(hf.shape).astype("<f4")
    return hf, nx, ny


def corners(C, cfg, anchors_s, log=B.log):
    """Signed-curvature peaks within +-45 m of each anchor (track s), named straights halfway between corners."""
    n = len(C)
    kap = B.curvature(C, sigma=6)
    out, fails = [], []
    for (turn, name, dirn, _, _, _), guess in zip(cfg["corners"], anchors_s):
        sgn = 1 if dirn == "left" else -1
        w = (np.arange(n) - guess + n / 2) % n - n / 2
        cand = np.where(np.abs(w) <= 45, sgn * kap, -np.inf)
        i = int(np.argmax(cand))
        if sgn * kap[i] <= 0:
            fails.append(f"corner {turn}")
        out.append({"name": name or turn, "turn": turn, "s": i, "radius_m": round(float(1 / abs(kap[i])), 1), "dir": dirn})
    for name, a, b in cfg["named_straights"]:
        sa = next(c["s"] for c in out if c["turn"] == a)
        sb = next(c["s"] for c in out if c["turn"] == b)
        out.append({"name": name, "turn": None, "s": (sa + sb) // 2, "radius_m": None, "dir": None})
    out.sort(key=lambda c: c["s"])
    return out, kap, fails
