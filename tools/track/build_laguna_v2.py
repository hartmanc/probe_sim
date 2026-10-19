"""Laguna Seca track package, v2 centreline: smooth, corner radii consistent with the driven line.

    uv run --python 3.12 --with numpy,scipy,rasterio,pyproj,shapely,pillow,requests,pandas,matplotlib \
        python tools/track/build_laguna_v2.py [--out tools/track/out/laguna_v2]

Why v2: v1 fitted a spline through the coarse OSM nodes and recentred it along its own normals; the spline kinked at
OSM way junctions and corner nodes, so corner radii came out 20-70 % too tight (T6 28 m vs 87 m driven), which made
the ghost speeds imply 1.5-2.2 g. v2 takes its shape from the race logger's GPS-driven centreline (centreline.npy,
whose curvature matches the IMU's alat/v^2 to r = 0.98) and moves it toward the imagery track centre with a
penalised least-squares fit:

    minimise  sum (e - d)^2 + A * sum (D2 e)^2 + B * |D3 (G + e n)|^2

e = lateral move along the line's normals, d = offset of the imagery midpoint (edge detection as v1), D2 e keeps the
move slowly varying so the curvature profile stays the driven line's, D3 penalises curvature change (no kinks).
Edges are then re-detected along the new normals, the fit is repeated once on them (the recentre), and the final
edges are detected along the final normals and stored per side (left/right half-widths differ by up to ~1.5 m:
the centre follows the midpoint only as closely as a smooth, driveable shape allows).

Uses the helpers of build_laguna.py (frames, DEM, NAIP, edge detection). Heightfield and ortho box are v1's.
"""

import argparse
import json
import math
import os
import shutil
import sys

import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.sparse import csr_matrix, diags, identity
from scipy.sparse.linalg import spsolve

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_laguna as B  # noqa: E402

FIT_A = 1e6  # stiffness of the lateral move (curvature stays the driven line's)
FIT_B = 1e3  # curvature-change penalty
WIDTH_MIN, WIDTH_MAX = 2 * B.HALF_MIN, 2 * B.HALF_MAX  # total paved width clamp (9-17 m, as v1's half-width clamp)
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


def smooth_fit(P, d):
    """Move closed 1 m polyline P laterally toward offsets d, keeping its curvature profile and removing kinks."""
    m = len(P)
    nl = B.left_normals(P)
    D2 = diffop(m, [(-1, 1), (0, -2), (1, 1)])
    D3 = diffop(m, [(-1, -1), (0, 3), (1, -3), (2, 1)])
    Ax = D3 @ diags(nl[:, 0])
    Ay = D3 @ diags(nl[:, 1])
    H = identity(m) + FIT_A * (D2.T @ D2) + FIT_B * (Ax.T @ Ax + Ay.T @ Ay)
    rhs = d - FIT_B * (Ax.T @ (D3 @ P[:, 0]) + Ay.T @ (D3 @ P[:, 1]))
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


def lidar_correct(PX, PY, prof, z0, radius=1.0, max_corr=1.0):
    """Pull the DEM profile onto the lidar point cloud's ground returns (class 2), median within 1 m of each
    profile point. The DEM is the same 2017 lidar, gridded and smoothed; at a few places it departs from the
    returns on the road: 0.2 m low over s~150-185 (the T1 footbridge), 0.45 m high at Rainey's inside edge
    (a barrier/berm bleeding into the smoothed grid). Gaps are filled along s, outliers median-filtered and the
    correction smoothed with a CORR_SIGMA Gaussian. Differences over 1 m are bridge decks classed as ground
    (s~1835-1846) and are ignored. 
    Uses build_scenery.py's point cache (tools/track/cache/lidar_points.npz); skipped with a warning if absent."""
    path = os.path.join(B.CACHE, "lidar_points.npz")
    if not os.path.exists(path):
        B.log("WARNING: no lidar point cache, profile left on the DEM (run build_scenery.py once to fetch points)")
        return prof
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


# 2017 lidar, 2023 repave. The circuit was fully repaved in 2023; the 2017 survey shows a 0.4 m sag at the T6
# apex that the drivers (Coby, October 2026) say is now a crest. Between a and b the centre height is rebuilt from
# the vertical curvature: crest or flat (z'' <= 0) inside c0..c1, at most a gentle sag (R >= 1500 m) elsewhere,
# heights and slopes matched at a and b, as smooth as possible; the same change is applied across the section.
# A pure crest between s=1910 and 1970 cannot meet both ends (the grade is +1.8 % at both and the road climbs
# into Rahal), so the window is 1895..2000 and the grade increase toward Rahal is moved past the apex.
REPAVE_FIXES = [(1895, 2000, 1905, 1965, "T6 sag (2017 lidar) -> crest (2023 repave)")]


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(B.HERE, "out", "laguna_v2"))
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    fails = []

    def check(label, ok, msg):
        B.log(f"[{'ok' if ok else 'FAIL'}] {label}: {msg}")
        if not ok:
            fails.append(label)

    # -- box exactly as v1 (from the OSM spline), so heightfield and ortho are v1's
    P, _ = B.osm_loop()
    G = np.load(B.GPS_CENTRELINE)
    gi, _ = B.project(G, P)
    if np.angle(np.exp(1j * 2 * np.pi * np.diff(np.r_[gi, gi[:1]]) / len(G))).sum() < 0:
        P = P[::-1].copy()
    D, _ = B.resample_closed(P, n=None, smooth=0.0, k=1)
    C0, _ = B.resample_closed(D[::5], smooth=len(D[::5]) * 0.25 ** 2)
    lo = C0.min(0) - B.MARGIN - 20
    hi = C0.max(0) + B.MARGIN + 20
    box = tuple(float(v) for v in (math.floor(lo[0] / 10) * 10, math.floor(lo[1] / 10) * 10,
                                   math.ceil(hi[0] / 10) * 10, math.ceil(hi[1] / 10) * 10))
    img, W, H = B.fetch_ortho(box)
    ortho = B.Ortho(img, box)
    B.log("ENU box", box, f"ortho {W}x{H}")

    # -- pass 1: GPS-driven line (index 0 = start/finish, driving order) toward the imagery midpoint
    Gs, LG = B.resample_closed(G, n=len(G), smooth=0.0)  # uniform 1 m, starts at G[0]
    half, st, _ = raw_edges(Gs, ortho)
    B.log("edges along GPS line:", {k: round(v, 3) for k, v in st.items() if isinstance(v, float)})
    d = (half[:, 0] - half[:, 1]) / 2
    C1, e1 = smooth_fit(Gs, d)
    B.log(f"pass 1: midpoint offset |d| median {np.median(np.abs(d)):.2f} max {np.abs(d).max():.2f} m; "
          f"fit residual |e-d| p95 {np.percentile(np.abs(e1 - d), 95):.2f} max {np.abs(e1 - d).max():.2f} m")
    C1, _ = B.resample_closed(C1, smooth=0.0)

    # -- pass 2 (the recentre): edges along the pass-1 normals give midpoint positions; the fit is redone from the
    #    GPS line toward them, so the stiffness bounds the total move from the driven shape
    half, st, _ = raw_edges(C1, ortho)
    B.log("edges along pass-1 centre:", {k: round(v, 3) for k, v in st.items() if isinstance(v, float)})
    M = C1 + ((half[:, 0] - half[:, 1]) / 2)[:, None] * B.left_normals(C1)
    sq, lq = B.project(Gs, M)
    o = np.argsort(sq)
    d = np.interp(np.arange(len(Gs)), sq[o], lq[o], period=len(Gs))
    C2, e2 = smooth_fit(Gs, d)
    B.log(f"pass 2: midpoint offset from GPS line |d| median {np.median(np.abs(d)):.2f} max {np.abs(d).max():.2f} m; "
          f"residual |e-d| p95 {np.percentile(np.abs(e2 - d), 95):.2f} max {np.abs(e2 - d).max():.2f} m")
    C2, _ = B.resample_closed(C2, smooth=0.0)
    # station 0 = projection of the logger's start/finish; exact whole-metre resample
    s0, _ = B.project(C2, G[:1])
    m2 = len(C2)
    idx = np.arange(m2)
    k = (float(s0[0]) + idx) % m2
    C2 = np.c_[np.interp(k, idx, C2[:, 0], period=m2), np.interp(k, idx, C2[:, 1], period=m2)]
    C, L = B.resample_closed(C2, smooth=0.0)
    n = len(C)
    nl = B.left_normals(C)
    B.log(f"final loop: n={n}, spline length {L:.2f} m")

    # -- final edges along the final normals, per side
    half, st, raw_ok = raw_edges(C, ortho)
    B.log("final edges:", {k: round(v, 3) for k, v in st.items() if isinstance(v, float)})
    width = np.clip(half.sum(1), WIDTH_MIN, WIDTH_MAX)
    off = (half[:, 0] - half[:, 1]) / 2  # midpoint offset (+left) from the centre
    hl = np.maximum(width / 2 + off, SIDE_MIN)
    hr = np.maximum(width / 2 - off, SIDE_MIN)
    Lp = C + hl[:, None] * nl
    Rp = C - hr[:, None] * nl

    # -- elevation (profile piecewise: fraction f<0 toward the left edge by |f|*hl, f>0 toward the right by f*hr,
    #    the convention src/physics/track.ts uses)
    dem = B.Dem(box)
    dem_s = B.Dem(box, sigma=0.7)
    z0 = float(dem(C[:1, 0], C[:1, 1])[0])
    fr = np.array(B.FRACTIONS)
    lat = np.where(fr[None, :] < 0, -fr[None, :] * hl[:, None], -fr[None, :] * hr[:, None])  # +left
    PX = C[:, 0:1] + lat * nl[:, 0:1]
    PY = C[:, 1:2] + lat * nl[:, 1:2]
    prof = gaussian_filter1d(dem_s(PX, PY) - z0, 1.5, axis=0, mode="wrap")
    prof = lidar_correct(PX, PY, prof, z0)
    prof = clean_profile(prof, lat)
    # 2017 lidar vs the 2023 repave: replace the T6 sag with a crest (see REPAVE_FIXES)
    resurface = np.zeros(n)
    for a, b, c0, c1, why in REPAVE_FIXES:
        zn, cv, rb, ra = crest_fix(prof[:, 3], a, b, c0, c1)
        resurface[a:b + 1] = zn - prof[a:b + 1, 3]
        B.log(f"repave fix {why}: s={a}..{b}, crest zone {c0}..{c1}; max height change {np.abs(resurface).max():.2f} m; "
              f"vertical radius at the apex before {rb:+.0f} m, after {ra:+.0f} m (+ sag, - crest); gentlest sag left "
              f"in the window R {1 / max(cv.max(), 1e-9):.0f} m")
    prof = prof + resurface[:, None]  # same height change across the section: banking kept
    zc, zl, zr = prof[:, 3], prof[:, 0], prof[:, -1]
    nx = int(round((box[2] - box[0]) / B.HF_DX)) + 1
    ny = int(round((box[3] - box[1]) / B.HF_DX)) + 1
    gx, gy = np.meshgrid(box[0] + np.arange(nx) * B.HF_DX, box[1] + np.arange(ny) * B.HF_DX)
    hf = (dem(gx, gy) - z0).astype("<f4")
    if np.any(resurface):  # carry the repave change into the heightfield under and just beside the road
        from scipy.spatial import cKDTree

        idx = np.where(resurface != 0)[0]
        tree = cKDTree(C[idx])
        dist, j = tree.query(np.c_[gx.ravel(), gy.ravel()], distance_upper_bound=40)
        ok = np.isfinite(dist)
        st = idx[np.minimum(j, len(idx) - 1)]
        half = np.maximum(hl[st], hr[st])
        w = np.clip(1 - (dist - half - 2.0) / 10.0, 0, 1) * ok
        hf = (hf.ravel() + (w * resurface[st]).astype("<f4")).reshape(hf.shape).astype("<f4")

    # -- corners: curvature peaks near the logger anchors (the logger frame is now ~ the track frame)
    sG, _ = B.project(C, G)
    Gu = np.unwrap(sG * 2 * np.pi / n) * n / (2 * np.pi)
    kap = B.curvature(C, sigma=6)
    corners = []
    for turn, name, s_laps, sgn in B.TURNS:
        guess = np.interp(s_laps, np.arange(len(G)), Gu) % n
        w = (np.arange(n) - guess + n / 2) % n - n / 2
        cand = np.where(np.abs(w) <= 45, sgn * kap, -np.inf)
        i = int(np.argmax(cand))
        if sgn * kap[i] <= 0:
            fails.append(f"corner {turn}")
        corners.append({"name": name or turn, "turn": turn, "s": i, "radius_m": round(float(1 / abs(kap[i])), 1),
                        "dir": "left" if sgn > 0 else "right"})
    t6 = next(c["s"] for c in corners if c["turn"] == "T6")
    t7 = next(c["s"] for c in corners if c["turn"] == "T7")
    corners.append({"name": "Rahal Straight", "turn": None, "s": (t6 + t7) // 2, "radius_m": None, "dir": None})
    corners.sort(key=lambda c: c["s"])

    # -- validation
    B.log("\n================ VALIDATION (v2) ================")
    check("loop length", 3480 <= n <= 3680, f"{n} m (official 3602; GPS line {LG:.0f} m)")
    zr_ = float(zc.max() - zc.min())
    check("elevation range", 45 <= zr_ <= 65, f"{zr_:.1f} m (z0 {z0:.2f} NAVD88)")
    d0 = float(np.linalg.norm(C[0] - G[0]))
    check("start/finish", d0 <= 15, f"station 0 is {d0:.2f} m from centreline.npy[0]")
    adv = np.angle(np.exp(1j * 2 * np.pi * np.diff(sG) / n)) * n / (2 * np.pi)
    check("direction", (adv > 0).mean() > 0.98, f"{(adv > 0).mean() * 100:.1f}% of GPS steps advance s")
    area = 0.5 * np.sum(C[:, 0] * np.roll(C[:, 1], -1) - np.roll(C[:, 0], -1) * C[:, 1])
    check("ccw", area > 0, f"signed area {area:.0f} m^2")
    # corner radii vs the driven line and vs v1
    kC, kG = kappa(C), kappa(G)
    try:
        v1 = json.load(open(os.path.join(B.OUT, "track.json")))
        C_v1 = np.array(v1["center"])[:, :2]
        kV1, sV1 = kappa(C_v1), B.project(C_v1, G)[0]
    except Exception:  # noqa: BLE001
        C_v1 = None
    rows = []
    B.log(f"     corner radii, min within +-{CORNER_WIN} m, curvature smoothed sigma {KAPPA_SIGMA} m:")
    B.log("     turn   s    R_v1   R_v2   R_gps   v2/gps")
    worst = 0.0
    for c in corners:
        if c["turn"] in (None, "T1", "T7"):
            continue
        s = c["s"]
        iG = int(np.argmin(np.abs((sG - s + n / 2) % n - n / 2)))
        rG = 1 / np.abs(kG[np.arange(iG - CORNER_WIN, iG + CORNER_WIN + 1) % len(G)]).max()
        rC = 1 / np.abs(kC[np.arange(s - CORNER_WIN, s + CORNER_WIN + 1) % n]).max()
        r1 = np.nan
        if C_v1 is not None:
            j = int(np.round(sV1[iG])) % len(C_v1)
            r1 = 1 / np.abs(kV1[np.arange(j - CORNER_WIN, j + CORNER_WIN + 1) % len(C_v1)]).max()
        worst = max(worst, abs(rC / rG - 1))
        rows.append((c["turn"], s, r1, rC, rG))
        B.log(f"     {c['turn']:5s} {s:5d} {r1:6.1f} {rC:6.1f} {rG:7.1f}   {rC / rG:5.2f}")
    check("corner radii vs GPS line", worst <= RADIUS_TOL, f"worst {worst * 100:.0f}% (limit {RADIUS_TOL * 100:.0f}%)")
    dl = np.abs(np.diff(np.r_[hl, hl[:1]]))
    dr = np.abs(np.diff(np.r_[hr, hr[:1]]))
    check("edge jumps", max(dl.max(), dr.max()) <= EDGE_JUMP,
          f"max lateral change between stations: left {dl.max():.3f} m, right {dr.max():.3f} m")
    kraw = B.curvature(C, 0)
    dk = np.abs(np.diff(np.r_[kraw, kraw[:1]]))
    B.log(f"     curvature change: max {dk.max() * 1e3:.2f} /km per m (raw, unsmoothed)")
    seg = np.diff(fr) * np.where(fr[1:] <= 0, hl[:, None], hr[:, None])
    cs = np.abs(np.diff(prof, axis=1)) / seg
    inner = cs[:, 1:-1].max(1)
    outer = np.maximum(cs[:, 0], cs[:, -1])
    check("cross slope (inner 2/3)", inner.max() < CROSS_HARD_V2,
          f"max {inner.max() * 100:.1f}% at s={int(inner.argmax())}; {np.sum(cs.max(1) > B.CROSS_SOFT)} stations "
          f"over 12 % (real banking at T5, T8/T8A, Rainey, as v1)")
    lip = np.where(outer >= B.CROSS_HARD)[0]
    check("cross slope (edge thirds)", outer.max() < EDGE_SEG_MAX,
          f"max {outer.max() * 100:.1f}% at s={int(outer.argmax())}; {len(lip)} stations over 16 % "
          f"(kerb/verge lip in the lidar at the very edge): s={', '.join(map(str, lip[:: max(1, len(lip) // 8)]))}")
    check("no NaN", all(np.isfinite(a).all() for a in (C, Lp, Rp, prof, hf)), "")
    B.log(f"     width: median {np.median(hl + hr):.1f} m (p5 {np.percentile(hl + hr, 5):.1f}, p95 "
          f"{np.percentile(hl + hr, 95):.1f}); centre offset from midpoint |off| median {np.median(np.abs(off)):.2f}, "
          f"max {np.abs(off).max():.2f} m; raw edge success left {raw_ok[:, 0].mean() * 100:.0f}% right "
          f"{raw_ok[:, 1].mean() * 100:.0f}%")
    for c in corners:
        B.log(f"     {c['turn'] or '':4s} {c['name']:18s} s={c['s']:5d}  R={c['radius_m']}")

    r3 = lambda a: np.round(a, 3).tolist()  # noqa: E731
    track = {
        "name": "WeatherTech Raceway Laguna Seca",
        "origin": {"lat": B.LAT0, "lon": B.LON0},
        "z0_navd88": round(z0, 3),
        "direction": "ccw",
        "spacing_m": 1.0,
        "n": n,
        "length_m": float(n),
        "center": r3(np.c_[C, zc]),
        "left": r3(np.c_[Lp, zl]),
        "right": r3(np.c_[Rp, zr]),
        "profile": {"fractions": B.FRACTIONS, "z": r3(prof)},
        "start_finish": {"index": 0},
        "corners": corners,
        "heightfield": {"file": "heightfield.bin", "x0": box[0], "y0": box[1], "dx": B.HF_DX, "nx": nx, "ny": ny},
        "ortho": {"file": "ortho.jpg", "x0": box[0], "y0": box[1], "x1": box[2], "y1": box[3], "width_px": W,
                  "height_px": H},
        "sources": "OpenStreetMap (ODbL), USGS 3DEP 1 m DEM 2017 (public domain), USGS NAIP imagery (public domain), "
                   "team race-logger GPS centreline",
        "notes": {
            "version": 2,
            "centre": "GPS-driven line moved toward the imagery midpoint by a smooth penalised fit; corner radii "
                      "within 25 % of the driven line",
            "edges": "NAIP asphalt extent per side along the final normals; left/right half-widths differ; profile "
                     "fractions are piecewise (f<0 scales the left half-width, f>0 the right)",
            "spline_length_m": round(L, 2),
        },
    }
    np.savez(os.path.join(B.CACHE, "track_arrays_v2.npz"), C=C, Lp=Lp, Rp=Rp, hl=hl, hr=hr, zc=zc, prof=prof,
             kap=kap, kC=kC)
    if fails:
        B.preview(img, box, C, Lp, Rp, zc, corners, os.path.join(out, "preview_failed.png"))
        B.log("\nVALIDATION FAILED:", fails)
        sys.exit(1)
    with open(os.path.join(out, "track.json"), "w") as fh:
        json.dump(track, fh, separators=(",", ":"))
    hf.tofile(os.path.join(out, "heightfield.bin"))
    # ortho: same box and pixel grid as v1, so the published (colour-graded) image is reused when it matches
    pub = os.path.join(B.OUT, "ortho.jpg")
    if C_v1 is not None and v1["ortho"]["x0"] == box[0] and v1["ortho"]["width_px"] == W and os.path.exists(pub):
        shutil.copyfile(pub, os.path.join(out, "ortho.jpg"))
    else:
        from PIL import Image

        Image.fromarray(B.grade_ortho(img)).save(os.path.join(out, "ortho.jpg"), quality=85, optimize=True)
    B.preview(img, box, C, Lp, Rp, zc, corners, os.path.join(out, "preview.png"))
    for f in ("track.json", "heightfield.bin", "ortho.jpg", "preview.png"):
        B.log(f"wrote {os.path.join(out, f)}: {os.path.getsize(os.path.join(out, f)) / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
