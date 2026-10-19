"""Build a track package's ghosts.json: each driver's best lap, the optimal lap and a racing line (stage 2 of
tools/track/build_track.py, which runs it; directly:)

    uv run --python 3.12 --with numpy,scipy,pandas,matplotlib,pillow python -I tools/ghosts/build_ghosts.py \
        [--config <track id>] [--track-dir <package>] [--no-logger]

Reads the package's track.json and ortho.jpg. The track config (tools/track/tracks/<id>/config.py, default
laguna_seca) names the logger directory, drivers and sections; with --no-logger, or a config without logger_dir,
ghosts.json carries only the racing line, the pure bounded minimum-curvature solve (no nudge, no kerb relaxation), and
an empty laps list; the implied-g checks are skipped (the autopilot lap, tools/calibrate/drive.ts, validates instead).

Source: the team's race-logger analysis (Laguna: /Users/cobyhartman/projects/starlink-go-pro/laps, read-only). The lap
selection, official-time scaling and optimal-lap stitching reproduce that analysis's export_dashboard.py (whose
helper modules write to their own folder on import, so the few functions needed are copied here, not imported):
  * laps are scaled so each adds up to its official MyLaps time (official.pkl),
  * a driver's ghost is their best clean lap by official time,
  * the optimal lap is optimal.solve() over clean laps from the good-GPS files (all but 0e98), stitched section by
    section with each piece's time and speed, throttle and rpm from the lap each piece came from.
The logger's distance frame (GPS centreline, 3558 m) is mapped onto the track's s by projecting the GPS centreline
onto the track centre.
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d
from scipy.optimize import lsq_linear
from scipy.sparse import diags, csr_matrix, vstack
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "track"))
import trackcfg  # noqa: E402

TRACK_ID = "laguna_seca"   # set by configure()
TRACK_DIR = None
LAPS = None

DS = 2.0  # output grid
MARGIN = 1.0  # racing line keeps this far inside the edges
LINE_JERK_W = 3  # curvature-change weight in the line solve
BOUND_SMOOTH_M = 10.0  # the line's edge bounds are a smoothed lower envelope of the edges (edge noise -> no kinks)
KERB_MARGIN = 1.0  # closest the line may come to an edge, only where the measured line went that close
NUDGE_W = 0.1  # weight of the nudge target in the final line solve
NUDGE = 0.3  # weight of the drivers' measured line vs the minimum-curvature line
DRIVERS = []  # race order (config logger_drivers)
SECTIONS = None  # logger section joins (config logger_sections, defs.J; None = the lap end)
BAD_GPS = []
NS = 8
IMPLIED_G_TURNS = None   # corners checked for implied g (config ghosts.implied_g_turns; default every corner under R 150)
IMPLIED_G_EXEMPT = []    # flat-out kinks: tabled, not checked
KAPPA_DRIVERS = []       # drivers whose fastest good-GPS laps give the IMU curvature check (config ghosts.kappa_drivers)


def configure(cfg, no_logger=False):
    global TRACK_ID, TRACK_DIR, LAPS, DRIVERS, SECTIONS, BAD_GPS, NS, MARGIN, KERB_MARGIN, NUDGE, LINE_JERK_W
    global IMPLIED_G_TURNS, IMPLIED_G_EXEMPT
    TRACK_ID = cfg["id"]
    TRACK_DIR = os.path.join(ROOT, "public", "tracks", cfg["id"])
    LAPS = None if no_logger else cfg["logger_dir"]
    DRIVERS = list(cfg["logger_drivers"])
    SECTIONS = cfg["logger_sections"]
    BAD_GPS = list(cfg["logger_bad_gps_files"])
    if SECTIONS:
        NS = len(SECTIONS) - 1
    g = cfg["ghosts"]
    MARGIN, KERB_MARGIN, NUDGE, LINE_JERK_W = g["margin"], g["kerb_margin"], g["nudge"], g["jerk_w"]
    IMPLIED_G_TURNS = g.get("implied_g_turns")
    IMPLIED_G_EXEMPT = list(g.get("implied_g_exempt", []))
    global KAPPA_DRIVERS
    KAPPA_DRIVERS = list(g.get("kappa_drivers", []))


def log(*a):
    print(*a, flush=True)


# ------------------------------------------------------------------ logger analysis (copied logic)
def solve(C, vtol=0.6, ltol=2.5, thrmin=80, use_lat=True):
    """optimal.py solve(): pick one lap per section so joins are compatible (speed, throttle, lateral position)."""
    idx = C.index.values
    n = len(idx)
    T = C[[f"sec{j + 1}" for j in range(NS)]].values
    V = C[[f"v{j}" for j in range(NS + 1)]].values
    La = C[[f"lat{j}" for j in range(NS + 1)]].values
    Th = C[[f"thr{j}" for j in range(NS + 1)]].values
    good = C.gps_good.values

    def compat(j):
        va = V[:, j][:, None]
        vb = V[:, j % NS][None, :]
        ok = np.abs(va - vb) <= vtol
        ok &= (Th[:, j][:, None] >= thrmin) & (Th[:, j % NS][None, :] >= thrmin)
        if use_lat:
            both = good[:, None] & good[None, :]
            ok &= ~both | (np.abs(La[:, j][:, None] - La[:, j % NS][None, :]) <= ltol)
        return ok

    CM = [compat(j) for j in range(1, NS + 1)]
    best = (np.inf, None)
    for s0 in range(n):
        cost = np.full(n, np.inf)
        cost[s0] = T[s0, 0]
        back = []
        for j in range(1, NS):
            M = np.where(CM[j - 1], cost[:, None], np.inf)
            arg = np.argmin(M, axis=0)
            c = M[arg, np.arange(n)] + T[:, j]
            back.append(arg)
            cost = c
        cl = np.where(CM[NS - 1][:, s0], cost, np.inf)
        e = np.argmin(cl)
        if cl[e] < best[0]:
            path = [e]
            for b in back[::-1]:
                path.append(b[path[-1]])
            path = path[::-1]
            path[0] = s0
            best = (cl[e], [idx[p] for p in path])
    return best


def load_logger():
    G = np.load(os.path.join(LAPS, "centreline.npy"))
    L = float(len(G))
    SE = np.arange(-450, L + 450, 2.0)
    J = [L if j is None else j for j in SECTIONS]  # defs.J
    TW, _ = pd.read_pickle(os.path.join(LAPS, "traces_warped.pkl"))
    X = pd.read_pickle(os.path.join(LAPS, "sections.pkl"))
    X["driver"] = X["driver"].replace({"16d7 pre-stop": "driver A"})
    _, OFFICIAL, MATCH = pd.read_pickle(os.path.join(LAPS, "official.pkl"))
    X = X.join(MATCH[["n", "official_s"]])
    X["logger_lapw"] = X.lapw
    FAC = X.official_s / X.lapw
    SECS = [f"sec{k}" for k in range(1, NS + 1)]
    X[SECS] = X[SECS].mul(FAC, axis=0)
    X["lapw"] = X.official_s
    X["gps_good"] = ~X.file.isin(BAD_GPS)
    return G, L, SE, J, TW, X, FAC, OFFICIAL


# ------------------------------------------------------------------ geometry
def left_normals(P):
    t = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    t /= np.linalg.norm(t, axis=1)[:, None]
    return np.c_[-t[:, 1], t[:, 0]], t


def project(P, Q):
    """Project Q onto closed polyline P: fractional station and signed lateral offset (+left)."""
    nl, t = left_normals(P)
    _, i = cKDTree(P).query(Q)
    rel = Q - P[i]
    seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
    return (i + (rel * t[i]).sum(1) / seg[i]) % len(P), (rel * nl[i]).sum(1)


def min_curvature_offsets(P, nl, lo, hi, smooth_w=1e-3, jerk_w=None, target=None):
    """Offsets e (along nl) minimising the squared second differences (curvature) of P + e*nl, plus jerk_w times
    the squared third differences (curvature change, keeps the line from kinking where it rides a bound), with
    lo <= e <= hi (linearised minimum-curvature line; bounded linear least squares)."""
    m = len(P)
    I = np.arange(m)
    if jerk_w is None:
        jerk_w = LINE_JERK_W

    def op(coefs):
        rows, cols, vals = [], [], []
        for k, w in coefs:
            rows.append(I)
            cols.append((I + k) % m)
            vals.append(np.full(m, float(w)))
        return csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(m, m))

    D2 = op([(-1, 1), (0, -2), (1, 1)])
    D3 = op([(-1, -1), (0, 3), (1, -3), (2, 1)]) * jerk_w
    Nx, Ny = diags(nl[:, 0]), diags(nl[:, 1])
    A = vstack([D2 @ Nx, D2 @ Ny, D3 @ Nx, D3 @ Ny, smooth_w * diags(np.ones(m))]).tocsr()
    b = -np.r_[D2 @ P[:, 0], D2 @ P[:, 1], D3 @ P[:, 0], D3 @ P[:, 1], np.zeros(m)]
    if target is not None:  # second objective: stay near target offsets (measured from P's normals)
        A = vstack([A, NUDGE_W * diags(np.ones(m))]).tocsr()
        b = np.r_[b, NUDGE_W * target]
    return bounded_lsq(A, b, lo, hi)


def bounded_lsq(A, b, lo, hi, iters=3000):
    """min |A e - b|^2 subject to lo <= e <= hi: primal active-set method on the sparse normal equations (each step
    goes from the current feasible point toward the subproblem optimum and stops at the first bound it meets, so
    the objective never increases)."""
    from scipy.sparse.linalg import spsolve

    H = (A.T @ A).tocsr()
    g = A.T @ b
    e = np.clip(np.zeros(len(lo)), lo, hi)
    alo = e <= lo
    ahi = e >= hi
    for _ in range(iters):
        free = ~(alo | ahi)
        fixed = np.where(alo, lo, np.where(ahi, hi, 0.0))
        p = fixed.copy()
        if free.any():
            Hf = H[free]
            p[free] = spsolve(Hf[:, free].tocsc(), g[free] - Hf[:, ~free] @ fixed[~free])
        step = p - e
        with np.errstate(divide="ignore", invalid="ignore"):
            a_lo = np.where(free & (p < lo), (lo - e) / step, np.inf)
            a_hi = np.where(free & (p > hi), (hi - e) / step, np.inf)
        alpha = min(1.0, a_lo.min(), a_hi.min())
        e = np.clip(e + alpha * step, lo, hi)
        if alpha < 1.0:
            alo |= free & (e <= lo + 1e-12)
            ahi |= free & (e >= hi - 1e-12)
            continue
        grad = H @ e - g  # multipliers: at lo the gradient must be >= 0, at hi <= 0
        viol = np.where(alo, -grad, 0.0) + np.where(ahi, grad, 0.0)
        j = int(np.argmax(viol))
        if viol[j] <= 1e-10:
            return e
        alo[j] = ahi[j] = False  # release the bound with the worst multiplier (one at a time: no cycling)
    raise RuntimeError("bounded least squares did not converge")


def main():
    global TRACK_DIR
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="laguna_seca", help="track id: tools/track/tracks/<id>/config.py")
    ap.add_argument("--no-logger", action="store_true", help="racing line only (pure minimum curvature), no ghost laps")
    ap.add_argument("--track-dir", default=None, help="track package to read track.json from and write ghosts.json to (default public/tracks/<id>)")
    ap.add_argument("--write-on-fail", action="store_true", help="write ghosts.json even if validation fails")
    ap.add_argument("--preview-dir", default=None, help="where preview_ghosts.png goes (default tools/track/previews)")
    ap.add_argument("--kerb-margin", type=float, default=None,
                    help="line bound (m from the edge) along the red/white kerb strips of scenery.json (apex / exit kerbs, "
                         "pavement inside the edge); default: MARGIN everywhere")
    ap.add_argument("--jerk-w", type=float, default=None, help="curvature-change weight (default LINE_JERK_W)")
    ap.add_argument("--debug-out", default=None, help="where ghost_line_debug.npz goes (default the preview directory)")
    args = ap.parse_args()
    configure(trackcfg.load(args.config, no_logger=args.no_logger), no_logger=args.no_logger)
    global LINE_JERK_W
    if args.jerk_w is not None:
        LINE_JERK_W = args.jerk_w
    TRACK_DIR = os.path.abspath(args.track_dir or TRACK_DIR)
    preview_dir = args.preview_dir or os.path.join(HERE, "..", "track", "previews")
    track = json.load(open(os.path.join(TRACK_DIR, "track.json")))
    n = track["n"]
    C = np.array(track["center"])[:, :2]
    Lp = np.array(track["left"])[:, :2]
    hw_full = np.linalg.norm(Lp - C, axis=1)  # left half-width
    hr_full = np.linalg.norm(np.array(track["right"])[:, :2] - C, axis=1)  # right half-width
    grid = np.arange(0, n, DS)
    gi = grid.astype(int)
    m = len(grid)
    fails = []

    if LAPS is None:
        return no_logger_line(track, C, hw_full, hr_full, grid, gi, m, preview_dir, args)
    G, L, SE, J, TW, X, FAC, OFFICIAL = load_logger()

    # ---- s mapping: logger distance (index into G) -> track s
    sG, latG = project(C, G)
    u = np.unwrap(sG * 2 * np.pi / n) * n / (2 * np.pi)
    u -= np.round((u[0] - sG[0]) / n) * n
    if u[0] > n / 2:
        u -= n
    # smooth the GPS jitter out of the mapping, as a deviation from a uniform stretch
    lin = u[0] + np.arange(len(G)) * n / L
    dev = gaussian_filter1d(u - lin, 15, mode="wrap")
    u = np.maximum.accumulate(lin + dev)
    ii = np.r_[np.arange(-200, 0), np.arange(len(G)), len(G) + np.arange(201)].astype(float)
    uu = np.r_[u[-200:] - n, u, u[:201] + n]
    if np.any(np.diff(uu) <= 0):
        uu = uu + np.arange(len(uu)) * 1e-6
    s_laps = np.interp(grid, uu, ii)  # logger s at each track grid point
    s_laps_end = np.interp(float(n), uu, ii)
    log(f"s mapping: track s=0 -> logger s={np.interp(0.0, uu, ii):.2f}; track n={n} -> logger {s_laps_end:.2f} "
        f"(stretch {n / L:.4f}); GPS line vs track centre: median |lat| {np.median(np.abs(latG)):.2f} m")

    def on_grid(tr, col):
        return np.interp(s_laps, SE, tr[col].to_numpy())

    laps = []
    # ---- real laps
    for name in DRIVERS:
        c = X[(X.driver == name) & X.clean]
        if not len(c):
            log(f"{name}: no clean lap, skipped")
            continue
        best = c.lapw.idxmin()
        stint = OFFICIAL[OFFICIAL.driver == name]
        ob = stint.loc[stint.lap_s.idxmin()]
        same = ob.n == X.loc[best, "n"]
        tr = TW[best]
        t_raw = tr.t.to_numpy()
        t0 = np.interp(0.0, SE, t_raw)
        t = (on_grid(tr, "t") - t0) * FAC[best]
        lap_time = float(X.loc[best, "official_s"])
        t_end = (np.interp(L, SE, t_raw) - t0) * FAC[best]
        laps.append({
            "id": f"{name.lower()}_best", "driver": name, "kind": "real", "lap_time_s": round(lap_time, 3),
            "t": t, "v": on_grid(tr, "v"), "rpm": on_grid(tr, "rpm"), "thr": on_grid(tr, "thr"),
            "lat": on_grid(tr, "lat"), "t_end": t_end, "file": X.loc[best, "file"], "official_lap": int(X.loc[best, "n"]),
            "is_official_best": bool(same), "src": best,
        })
        log(f"{name}: lap idx {best} file {X.loc[best, 'file']} official lap {X.loc[best, 'n']} "
            f"{lap_time:.3f} s (official stint best {ob.lap_s:.3f}{'' if same else ' - NOT logged cleanly'})")

    # ---- optimal lap (export_dashboard.stitch)
    tot, path = solve(X[X.clean & X.gps_good])
    log(f"optimal: {tot:.3f} s from", [(X.loc[p, "driver"], int(X.loc[p, "n"])) for p in path])
    sec_of = np.clip(np.searchsorted(J, s_laps, side="right") - 1, 0, NS - 1)
    t = np.zeros(m)
    v, rpm, thr, lat = (np.zeros(m) for _ in range(4))
    toff = 0.0
    tj_end = None
    for j, p in enumerate(path):
        seg = sec_of == j
        tr = TW[p]
        tt = tr.t.to_numpy() * FAC[p]
        t[seg] = np.interp(s_laps[seg], SE, tt) - np.interp(J[j], SE, tt) + toff
        for arr, col in ((v, "v"), (rpm, "rpm"), (thr, "thr"), (lat, "lat")):
            arr[seg] = np.interp(s_laps[seg], SE, tr[col].to_numpy())
        toff += X.loc[p, f"sec{j + 1}"]
    laps.append({"id": "optimal", "driver": "Optimal", "kind": "optimal", "lap_time_s": round(float(toff), 3),
                 "t": t, "v": v, "rpm": rpm, "thr": thr, "lat": lat, "t_end": float(toff), "file": None,
                 "pieces": [{"section": j + 1, "logger_s": [J[j], J[j + 1]],
                             "s": [round(float(np.interp(J[j], ii, uu)), 1), round(float(np.interp(J[j + 1], ii, uu)), 1)],
                             "driver": X.loc[p, "driver"], "official_lap": int(X.loc[p, "n"]),
                             "time_s": round(float(X.loc[p, f"sec{j + 1}"]), 3)} for j, p in enumerate(path)],
                 "src_files": sorted({X.loc[p, "file"] for p in path})})

    # ---- racing line
    hw = hw_full[gi]
    hwr = hr_full[gi]
    P = C[gi]
    nlg, _ = left_normals(P)
    # per-side margin: MARGIN, or --kerb-margin along the kerb strips (the kerbs are pavement inside the painted edge,
    # so the line may put the outside wheels on them; 18 Oct 2026 rebuild to the painted road width)
    mL = np.full(m, MARGIN)
    mR = np.full(m, MARGIN)
    if args.kerb_margin is not None:
        sc_path = os.path.join(TRACK_DIR, "scenery.json")
        strips = json.load(open(sc_path)).get("kerbs", {}).get("strips", []) if os.path.exists(sc_path) else []
        s_m = grid * float(track.get("spacing_m", 1.0))
        nk = 0
        for st in strips:
            if st.get("kind") not in ("apex", "exit"):
                continue
            on = (s_m >= st["s0"] - 2) & (s_m <= st["s1"] + 2)
            (mL if st["side"] > 0 else mR)[on] = min(MARGIN, args.kerb_margin)
            nk += 1
        log(f"     kerb margin {args.kerb_margin} m along {nk} kerb strips ({np.sum(mL < MARGIN) + np.sum(mR < MARGIN)} side-points)")
    # (the kerb relaxation is added after the edge envelope, ramped in over ~4 m, never past edge - kerb margin)
    # floors: a 0.5 m corridor measured from the OTHER side's bound, not from the centre line. Since the 18 Oct 2026
    # apex-kerb re-trace the centre can lie within 0.6 m of an edge (Corkscrew apex: left half-width 0.62 m), and a
    # +-0.5 m floor about the centre let the line run 0.25 m from that edge.
    fl_l = 0.5 - (hwr - MARGIN)
    fl_r = 0.5 - (hw - MARGIN)
    lim = smooth_bound(np.maximum(hw - MARGIN, fl_l))  # left bound (+)
    limr = smooth_bound(np.maximum(hwr - MARGIN, fl_r))  # right bound (-)
    if (mL < MARGIN).any() or (mR < MARGIN).any():
        lim = np.minimum(lim + gaussian_filter1d(MARGIN - mL, 1.0, mode="wrap"), np.maximum(hw - mL, fl_l))
        limr = np.minimum(limr + gaussian_filter1d(MARGIN - mR, 1.0, mode="wrap"), np.maximum(hwr - mR, fl_r))
    # the drivers' measured line: fastest real laps from good-GPS files, plus the optimal pieces (all good-GPS)
    meas = []
    for lp in laps:
        if lp["kind"] == "real" and lp["file"] == "0e98":
            continue
        # driver position = GPS centreline point + lat * GPS left normal, re-projected on the track centre
        tG = np.roll(G, -1, 0) - np.roll(G, 1, 0)
        tG /= np.linalg.norm(tG, axis=1)[:, None]
        nG = np.c_[-tG[:, 1], tG[:, 0]]
        k = np.mod(s_laps, L)
        gx = np.interp(k, np.arange(L), G[:, 0], period=L) + lp["lat"] * np.interp(k, np.arange(L), nG[:, 0], period=L)
        gy = np.interp(k, np.arange(L), G[:, 1], period=L) + lp["lat"] * np.interp(k, np.arange(L), nG[:, 1], period=L)
        sq, eq = project(C, np.c_[gx, gy])
        # re-grid the measured offsets by their projected station
        order = np.argsort(sq)
        meas.append(np.interp(grid, sq[order], eq[order], period=n))
    meas = np.array(meas)
    e_gps = gaussian_filter1d(np.median(meas, 0), 5, mode="wrap")  # ~10 m smoothing
    # Where the drivers' measured line ran closer than MARGIN to an edge (kerb use, e.g. T5 exit), the bound follows
    # it out to at most KERB_MARGIN from the edge; everywhere else the line keeps MARGIN.
    lim_n, limr_n = lim, limr
    lim = np.maximum(lim_n, np.minimum(e_gps, hw - np.minimum(KERB_MARGIN, mL)))
    limr = np.maximum(limr_n, np.minimum(-e_gps, hwr - np.minimum(KERB_MARGIN, mR)))
    relaxed = (lim > lim_n + 0.05) | (limr > limr_n + 0.05)
    e_mc = min_curvature_line(P, nlg, -limr, lim)
    log(f"     bounds relaxed toward the measured line at {relaxed.sum()} of {m} grid points "
        f"({relaxed.sum() * DS:.0f} m), never closer than {KERB_MARGIN} m to an edge")
    log(f"racing line: {len(meas)} measured lines; min-curvature vs measured: median |diff| "
        f"{np.median(np.abs(e_mc - e_gps)):.2f} m, p95 {np.percentile(np.abs(e_mc - e_gps), 95):.2f} m")
    # nudge: one more bounded solve, curvature + staying near the nudged target (a plain blend then clip would put
    # kinks wherever the measured line lies beyond the bounds)
    target = e_mc + NUDGE * (e_gps - e_mc)
    e = min_curvature_offsets(P, nlg, -limr, lim, target=target)
    log(f"     nudged line vs target: median |diff| {np.median(np.abs(e - target)):.2f} m, max {np.abs(e - target).max():.2f} m")

    # ---- validation
    log("\n================ GHOST VALIDATION ================")

    def check(label, ok, msg):
        log(f"[{'ok' if ok else 'FAIL'}] {label}: {msg}")
        if not ok:
            fails.append(label)

    out_laps = []
    for lp in laps:
        # the track's s=0 sits a fraction of a metre from the logger's lap line: re-zero there
        t = lp["t"] - lp["t"][0]
        # time to cover the last stretch, from the last grid point to the line, at the local speed
        t_close = t[-1] + (n - grid[-1]) / max(lp["v"][-1], 1.0)
        thr = np.clip(lp["thr"] / 95.0, 0, 1)
        ok_mono = np.all(np.diff(t) > 0) and t[0] == 0
        check(f"{lp['id']} t", ok_mono and np.isfinite(t).all(),
              f"t[0]={t[0]:.3f}, monotonic={bool(np.all(np.diff(t) > 0))}, finite={bool(np.isfinite(t).all())}")
        check(f"{lp['id']} lap time", abs(t_close - lp["lap_time_s"]) < 0.5 and abs(lp["t_end"] - lp["lap_time_s"]) < 0.5,
              f"lap_time_s {lp['lap_time_s']:.3f}, trace end {lp['t_end']:.3f}, last t + close {t_close:.3f}")
        check(f"{lp['id']} speed", lp["v"].min() >= 10 and lp["v"].max() <= 45,
              f"{lp['v'].min():.1f}..{lp['v'].max():.1f} m/s")
        check(f"{lp['id']} finite", all(np.isfinite(lp[k]).all() for k in ("v", "rpm", "thr")), "v/rpm/throttle")
        mm, ss = divmod(lp["lap_time_s"], 60)
        out = {"id": lp["id"], "driver": lp["driver"], "label": f"{lp['driver']} {int(mm)}:{ss:06.3f}"[:-1],
               "kind": lp["kind"], "lap_time_s": lp["lap_time_s"],
               "t": np.round(t, 3).tolist(), "v_mps": np.round(lp["v"], 2).tolist(),
               "rpm": np.round(lp["rpm"]).astype(int).tolist(), "throttle": np.round(thr, 3).tolist()}
        if lp["kind"] == "real":
            out.update({"logger_file": lp["file"], "official_lap": lp["official_lap"]})
        else:
            out.update({"pieces": lp["pieces"]})
        out_laps.append(out)
    clear = np.minimum(hw - e, hwr + e)
    kmin = min(KERB_MARGIN, float(np.minimum(mL, mR).min()))
    check("line inside edges", clear.min() >= kmin - 1e-6 and (np.minimum(hw - e - mL, hwr + e - mR)[~relaxed] >= -1e-6).all(),
          f"min clearance to edge {clear.min():.2f} m; {MARGIN} m kept except {np.sum(clear < MARGIN - 1e-6) * DS:.0f} m "
          f"of track where the drivers ran closer (>= {KERB_MARGIN} m)")
    g_rows = implied_g(track, grid, P + e[:, None] * nlg, e, laps, check)
    kappa_plot(track, grid, P + e[:, None] * nlg, s_laps, L, X, TW, SE, os.path.join(preview_dir, "kappa_check.png"))
    kap_line = curvature_of(P + e[:, None] * nlg)
    kap_c = curvature_of(P)
    log(f"     line curvature: sum k^2 {np.sum(kap_line ** 2):.4f} vs centre {np.sum(kap_c ** 2):.4f}; "
        f"offset range {e.min():+.2f}..{e.max():+.2f} m")

    # entries sit every DS stations; consumers index by metres (s = station * spacing_m), so the grid step is in metres
    ghosts = {"track": TRACK_ID, "s_grid_m": round(DS * float(track.get("spacing_m", 1.0)), 6),
              "line": {"offset_m": np.round(e, 3).tolist(),
                       "method": f"min-curvature within edges less {MARGIN} m, nudged {NUDGE:.0%} toward measured lines"},
              "laps": out_laps}
    np.savez(args.debug_out or os.path.join(preview_dir, "ghost_line_debug.npz"), e=e, e_mc=e_mc, e_gps=e_gps,
             lim=lim, limr=limr, grid=grid)
    if fails:
        log("\nGHOST VALIDATION FAILED:", fails)
        if not args.write_on_fail:
            sys.exit(1)
    path_out = os.path.join(TRACK_DIR, "ghosts.json")
    with open(path_out, "w") as fh:
        json.dump(ghosts, fh, separators=(",", ":"))
    log(f"wrote ghosts.json: {os.path.getsize(path_out) / 1e6:.2f} MB, {len(out_laps)} laps x {m} points")
    preview(track, grid, P, nlg, hw, e, e_mc, e_gps, laps, os.path.join(preview_dir, "preview_ghosts.png"))


def no_logger_line(track, C, hw_full, hr_full, grid, gi, m, preview_dir, args):
    """No logger laps: the racing line is the pure bounded minimum-curvature line (MARGIN inside the smoothed edge
    envelope, the same floors), there are no ghost laps and no implied-g checks."""
    fails = []
    hw, hwr = hw_full[gi], hr_full[gi]
    P = C[gi]
    nlg, _ = left_normals(P)
    fl_l = 0.5 - (hwr - MARGIN)
    fl_r = 0.5 - (hw - MARGIN)
    lim = smooth_bound(np.maximum(hw - MARGIN, fl_l))
    limr = smooth_bound(np.maximum(hwr - MARGIN, fl_r))
    e = min_curvature_line(P, nlg, -limr, lim)
    log("racing line: no logger laps, pure minimum-curvature line within the edges less "
        f"{MARGIN} m (offset range {e.min():+.2f}..{e.max():+.2f} m)")
    log("\n================ GHOST VALIDATION (no logger) ================")
    clear = np.minimum(hw - e, hwr + e)
    ok = clear.min() >= min(MARGIN, 0.5) - 0.05
    log(f"[{'ok' if ok else 'FAIL'}] line inside edges: min clearance to edge {clear.min():.2f} m")
    if not ok:
        fails.append("line inside edges")
    kap_line = curvature_of(P + e[:, None] * nlg)
    kap_c = curvature_of(P)
    log(f"     line curvature: sum k^2 {np.sum(kap_line ** 2):.4f} vs centre {np.sum(kap_c ** 2):.4f}")
    log("     implied-g checks skipped (no ghost laps): validate with tools/calibrate/drive.ts --track <dir>")
    ghosts = {"track": TRACK_ID, "s_grid_m": round(DS * float(track.get("spacing_m", 1.0)), 6),
              "line": {"offset_m": np.round(e, 3).tolist(),
                       "method": f"min-curvature within edges less {MARGIN} m (no logger laps)"},
              "laps": []}
    np.savez(args.debug_out or os.path.join(preview_dir, "ghost_line_debug.npz"), e=e, e_mc=e, e_gps=np.full(m, np.nan),
             lim=lim, limr=limr, grid=grid)
    if fails and not args.write_on_fail:
        log("\nGHOST VALIDATION FAILED:", fails)
        sys.exit(1)
    path_out = os.path.join(TRACK_DIR, "ghosts.json")
    with open(path_out, "w") as fh:
        json.dump(ghosts, fh, separators=(",", ":"))
    log(f"wrote ghosts.json: {os.path.getsize(path_out) / 1e6:.2f} MB, racing line only ({m} points)")
    preview(track, grid, P, nlg, hw, e, e, np.full(m, np.nan), [], os.path.join(preview_dir, "preview_ghosts.png"))


def curvature_of(P):
    d1 = (np.roll(P, -1, 0) - np.roll(P, 1, 0)) / 2
    d2 = np.roll(P, -1, 0) - 2 * P + np.roll(P, 1, 0)
    return (d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]) / np.linalg.norm(d1, axis=1) ** 3


def smooth_bound(b):
    """Smooth lower envelope: a rolling minimum then a Gaussian, never above the original bound."""
    from scipy.ndimage import minimum_filter1d

    k = int(round(BOUND_SMOOTH_M / DS))
    sm = gaussian_filter1d(minimum_filter1d(b, 2 * k + 1, mode="wrap"), k / 2, mode="wrap")
    return np.minimum(sm, b)


def min_curvature_line(P, nl, lo, hi, iters=4):
    """Minimum-curvature lateral offsets within [lo, hi]: bounded least squares on the second differences of the
    line points, re-linearised about the previous solution (new base points and normals) a few times."""
    e = np.zeros(len(P))
    for _ in range(iters):
        base = P + e[:, None] * nl
        # offsets stay along the centre's normals; solve for the step about the current line
        de = min_curvature_offsets(base, nl, lo - e, hi - e)
        e = np.clip(e + de, lo, hi)
        if np.abs(de).max() < 0.01:
            break
    return e


G_ACC = 9.81


def profile_z(track, i, lat):
    """Road z at station i, lateral offset lat (+left), with the piecewise profile convention of src/physics."""
    c = np.array(track["center"][i][:2])
    hl = np.hypot(*(np.array(track["left"][i][:2]) - c))
    hr = np.hypot(*(np.array(track["right"][i][:2]) - c))
    f = -lat / (hl if lat > 0 else hr)
    return np.interp(np.clip(f, -1, 1), track["profile"]["fractions"], track["profile"]["z"][i])


def implied_g(track, grid, R, e, laps, check, sigma_m=4.0):
    """Lateral grip the ghosts' speeds need on the racing line.

    plain:  a = v^2 * kappa_line / g, kappa from the line heading Gaussian-smoothed over 4 m (as the autopilot).
    tyre:   the friction ratio the tyres must supply once the road's banking at the line is counted,
            mu = (a - tan b) / (1 + a tan b), b = bank toward the inside of the turn (from the lidar profile).
    T5 and Rainey are banked ~13 % (7.5 deg), worth ~0.3 g there, so the plain figure exceeds the car's ~1.15 g
    while the tyre figure does not. Checks use the tyre figure; per-corner peak within +-40 m of the corner."""
    k = gaussian_filter1d(curvature_of(R), sigma_m / DS, mode="wrap")
    gi = grid.astype(int)
    # road bank = median slope of the four inner profile segments (the outer thirds can hold kerb/verge lips in the
    # lidar, e.g. Rainey's raised inside edge), dz/dlat with + = left side higher
    fr = np.array(track["profile"]["fractions"])
    Cc = np.array(track["center"])[:, :2]
    hl = np.linalg.norm(np.array(track["left"])[:, :2] - Cc, axis=1)
    hr = np.linalg.norm(np.array(track["right"])[:, :2] - Cc, axis=1)
    latp = np.where(fr[None, :] < 0, -fr[None, :] * hl[:, None], -fr[None, :] * hr[:, None])  # +left
    pz = np.array(track["profile"]["z"])
    seg_slope = np.diff(pz, axis=1) / np.diff(latp, axis=1)
    slope = gaussian_filter1d(np.median(seg_slope[:, 1:5], axis=1)[gi], 2, mode="wrap")
    tb = -np.sign(k) * slope  # tan(bank) toward the turn centre (left turn: left side lower helps)
    byid = {lp["id"]: lp for lp in laps}
    ref = [byid[i] for i in ("driver_a_best", "optimal") if i in byid]
    for lp in ref:
        a = lp["v"] ** 2 * np.abs(k) / G_ACC
        lp["g_plain"] = a
        lp["g_tyre"] = (a - tb) / (1 + a * tb)
    log("     implied lateral g on the racing line (peak within +-40 m of each corner); plain = v^2 k / g, "
        "tyre = after banking")
    log("     corner  s     R_line  bank%   driver A plain/tyre   optimal plain/tyre")
    bad, rows = [], []
    turns = IMPLIED_G_TURNS if IMPLIED_G_TURNS is not None else [
        c["turn"] for c in track["corners"] if c.get("turn") and c.get("radius_m") is not None and c["radius_m"] < 150]
    for c in track["corners"]:
        if c.get("turn") not in turns:
            continue
        cs = c["s"] / float(track.get("spacing_m", 1.0))  # corner s is metres; grid is stations
        w = np.abs((grid - cs + track["n"] / 2) % track["n"] - track["n"] / 2) <= 40
        j = np.where(w)[0][np.argmax(ref[0]["g_tyre"][w])]
        vals = [(lp["g_plain"][w].max(), lp["g_tyre"][w].max()) for lp in ref]
        r = 1 / np.abs(k[w]).max()
        rows.append({"turn": c["turn"], "s": c["s"], "R_line": round(float(r), 1), "bank_pct": round(float(tb[j] * 100), 1),
                     **{f"{lp['id']}_{kind}": round(float(v[q]), 2) for lp, v in zip(ref, vals)
                        for q, kind in ((0, "plain"), (1, "tyre"))}})
        log(f"     {c['turn']:6s} {c['s']:7.1f} {r:6.1f}  {tb[j] * 100:+5.1f}   " +
            "   ".join(f"{p:5.2f} / {t:4.2f}     " for p, t in vals))
        # too tight: the tyres would need > 1.3 g after banking; too straight: v^2 k / g < 0.9 at a real corner
        if c["turn"] not in IMPLIED_G_EXEMPT and not all(t <= 1.3 and p >= 0.9 for p, t in vals):  # flat-out kinks (Laguna T7)
            bad.append(c["turn"])
    gmax = max(lp["g_tyre"].max() for lp in ref)
    pmax = max(lp["g_plain"].max() for lp in ref)
    check("implied g max", gmax <= 1.35, f"tyre {gmax:.2f} g anywhere (plain v^2k/g max {pmax:.2f})")
    check("implied g at apexes", not bad, "every corner: tyre <= 1.3 g and plain >= 0.9 g" if not bad else f"outside: {bad}")
    return rows


def kappa_plot(track, grid, R, s_laps, L, X, TW, SE, path):
    """Measured path curvature (alat / v^2, IMU, median of good-GPS fast laps) vs the track centre and line."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sel = X[X.clean & X.gps_good & X.driver.isin(KAPPA_DRIVERS or DRIVERS)].sort_values("lapw").groupby("driver").head(5)
    K = [np.interp(s_laps, SE, TW[i].alat.to_numpy() / np.maximum(TW[i].v.to_numpy(), 5) ** 2) for i in sel.index]
    km = gaussian_filter1d(np.median(K, 0), 2, mode="wrap")
    C = np.array(track["center"])[:, :2][grid.astype(int)]
    kc = gaussian_filter1d(curvature_of(C), 2, mode="wrap")
    kl = gaussian_filter1d(curvature_of(R), 2, mode="wrap")
    G = np.load(os.path.join(LAPS, "centreline.npy"))
    kg = gaussian_filter1d(curvature_of(G), 4, mode="wrap")
    kg = np.interp(s_laps % L, np.arange(L), kg, period=L)
    log(f"     curvature check vs measured (IMU) over {len(K)} laps: corr centre {np.corrcoef(km, kc)[0, 1]:.3f}, "
        f"line {np.corrcoef(km, kl)[0, 1]:.3f}; peak |k| ratio line/measured at corners shown in {os.path.basename(path)}")
    fig, ax = plt.subplots(figsize=(16, 6))
    ax.plot(grid, km * 1000, color="k", lw=1.5, label=f"measured alat/v^2 (median, {'/'.join(KAPPA_DRIVERS or DRIVERS)})")
    ax.plot(grid, kg * 1000, color="0.6", lw=1, label="centreline.npy (GPS driven)")
    ax.plot(grid, kc * 1000, color="#0a84ff", lw=0.8, label="track centre")
    ax.plot(grid, kl * 1000, color="#d4a000", lw=1.2, label="racing line")
    for c in track["corners"]:
        ax.axvline(c["s"], color="0.85", lw=0.5)
        ax.text(c["s"], ax.get_ylim()[1] if False else 62, c.get("turn") or "Rahal", fontsize=7, ha="center")
    ax.set_ylim(-45, 66)
    ax.set_xlim(0, track["n"])
    ax.set_xlabel("s (m)")
    ax.set_ylabel("curvature (1/km, + left)")
    ax.legend(fontsize=8, loc="lower left")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    plt.close(fig)


def preview(track, grid, P, nlg, hw, e, e_mc, e_gps, laps, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image

    o = track["ortho"]
    img = np.asarray(Image.open(os.path.join(TRACK_DIR, o["file"])))
    fig = plt.figure(figsize=(14, 19))
    ax = fig.add_axes([0.04, 0.33, 0.92, 0.65])
    ax.imshow(img, extent=(o["x0"], o["x1"], o["y0"], o["y1"]), origin="upper")
    loop = lambda a: np.r_[a, a[:1]]  # noqa: E731
    hwr = np.linalg.norm(np.array(track["right"])[:, :2] - np.array(track["center"])[:, :2], axis=1)[grid.astype(int)]
    for sgn, col, h in ((1, "#ff3b30", hw), (-1, "#0a84ff", hwr)):
        E = P + sgn * h[:, None] * nlg
        ax.plot(loop(E)[:, 0], loop(E)[:, 1], color=col, lw=0.6)
    R = P + e[:, None] * nlg
    ax.plot(loop(R)[:, 0], loop(R)[:, 1], color="#ffd60a", lw=1.4, label="racing line")
    M = P + e_gps[:, None] * nlg
    ax.plot(loop(M)[:, 0], loop(M)[:, 1], color="#30d158", lw=0.6, ls="--", label="measured (good-GPS laps)")
    for c in track["corners"]:
        ax.annotate(c.get("turn") or c["name"], np.array(track["center"][int(round(c["s"] / float(track.get("spacing_m", 1.0)))) % track["n"]][:2]), color="white", fontsize=8,
                    xytext=(8, -10), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.6, lw=0))
    lo, hi = P.min(0) - 40, P.max(0) + 40
    ax.set_xlim(lo[0], hi[0])
    ax.set_ylim(lo[1], hi[1])
    ax.set_aspect("equal")
    ax.legend(loc="lower right")
    ax.set_title("Racing line (min-curvature, 1 m margin, nudged toward measured)")
    bx = fig.add_axes([0.06, 0.17, 0.9, 0.13])
    for lp in laps:
        bx.plot(grid, lp["v"] * 3.6, lw=1.6 if lp["kind"] == "optimal" else 0.8,
                color="k" if lp["kind"] == "optimal" else None, label=f"{lp['driver']} {lp['lap_time_s']:.2f}")
    for c in track["corners"]:
        bx.axvline(c["s"], color="0.8", lw=0.5)
        bx.text(c["s"], 5, c.get("turn") or "Rahal", fontsize=7, ha="center")
    bx.set_ylabel("speed (km/h)")
    bx.set_xlim(0, track["n"])
    bx.legend(ncol=6, fontsize=8, loc="lower right")
    bx.grid(alpha=0.3)
    cx = fig.add_axes([0.06, 0.03, 0.9, 0.11])
    cx.fill_between(grid, -hwr, hw, color="0.9")
    cx.plot(grid, e_mc, color="0.5", lw=0.7, label="min-curvature")
    cx.plot(grid, e_gps, color="#30d158", lw=0.7, label="measured")
    cx.plot(grid, e, color="#d4a000", lw=1.2, label="final")
    cx.set_xlim(0, track["n"])
    cx.set_ylabel("offset (m, +left)")
    cx.set_xlabel("s (m)")
    cx.legend(ncol=3, fontsize=8)
    fig.savefig(path, dpi=100)
    plt.close(fig)


if __name__ == "__main__":
    main()
