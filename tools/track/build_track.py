"""Build a circuit package for the Probe sim from a track config, stage by stage (the build-track skill drives this).

    uv run --python 3.12 --with numpy,scipy,rasterio,pyproj,shapely,pillow,requests,pandas,matplotlib,laspy[lazrs] \
        python -I tools/track/build_track.py --track <id> [--stage geometry|ghosts|scenery|all] [--no-logger]
        [--out tools/track/out/<id>] [--publish]

Config: tools/track/tracks/<id>/config.py (format in tools/track/trackcfg.py; Laguna Seca is the worked example).
Output: a candidate package in --out (default tools/track/out/<id>/): track.json, heightfield.bin, ortho.jpg,
ghosts.json, scenery.json, far_heightfield.bin, far_ortho.jpg, plus work/ (reports, previews, intermediate arrays).
--publish copies the package to public/tracks/<id>/ after every stage passed; it refuses to overwrite an existing
package unless --overwrite-package is given (a rebuilt track also needs a PHYSICS_VERSION bump and the derived data
rebuilt: record_onpave.ts, calibrate_field.ts, self-play; see the skill).

Stages, each with a printed validation report; a failed check exits 1 without writing that stage's outputs:
  geometry  (stage 1) OSM loop -> centre (logger: the driven line moved toward the NAIP midpoint; no logger: the OSM
            loop) -> painted midpoint on the captures -> centre refit and uniform stations -> edges: paint-step prior,
            measured shapes, ONE robust penalised spline per side through the painted-line / kerb candidates (keep and
            asphalt_end features from the config), declared straights -> profile (DEM, lidar returns, clean-up, repave
            crests) re-evaluated at the fitted edges -> heightfield, ortho, corners -> gates.
            Without logger laps the centre is the painted-road midpoint after the spline fit (one more refit).
  ghosts    (stage 2) tools/ghosts/build_ghosts.py: ghost laps, optimal lap, racing line (no logger: the pure
            minimum-curvature line only, no laps, implied-g checks skipped; validate with tools/calibrate/drive.ts).
  scenery   (stage 3) build_scenery.py then scenery_post.py, then the edge gate with the walls and bridges.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import trackcfg  # noqa: E402
import geo as B  # noqa: E402
import centre as V2  # noqa: E402
import captures as CAP  # noqa: E402
import paint  # noqa: E402
import recentre  # noqa: E402
import edges_spline  # noqa: E402
import straights  # noqa: E402
import edge_gate  # noqa: E402

ROOT = trackcfg.ROOT
log = B.log
WRITE_ON_FAIL = False
REPRO = {}   # config `reproduce`, on the logger path only


class Report:
    def __init__(self, title):
        self.fails = []
        log(f"\n================ {title} ================")

    def check(self, label, ok, msg):
        log(f"[{'ok' if ok else 'FAIL'}] {label}: {msg}")
        if not ok:
            self.fails.append(label)


def r3(a):
    return np.round(a, 3).tolist()


def track_dict(cfg, C, hl, hr, prof, z0, sp, L, corners, box, W, H, nx, ny, notes):
    nl = B.left_normals(C)
    Lp = C + hl[:, None] * nl
    Rp = C - hr[:, None] * nl
    return {
        "name": cfg["name"], "origin": {"lat": cfg["origin"][0], "lon": cfg["origin"][1]},
        "z0_navd88": round(float(z0), 3), "direction": cfg["direction"], "spacing_m": round(float(sp), 6),
        "n": int(len(C)), "length_m": round(float(L), 3),
        "center": r3(np.c_[C, prof[:, 3]]), "left": r3(np.c_[Lp, prof[:, 0]]), "right": r3(np.c_[Rp, prof[:, -1]]),
        "profile": {"fractions": B.FRACTIONS, "z": r3(prof)}, "start_finish": {"index": 0}, "corners": corners,
        "heightfield": {"file": "heightfield.bin", "x0": box[0], "y0": box[1], "dx": B.HF_DX, "nx": nx, "ny": ny},
        "ortho": {"file": "ortho.jpg", "x0": box[0], "y0": box[1], "x1": box[2], "y1": box[3], "width_px": W, "height_px": H},
        "sources": "OpenStreetMap (ODbL), USGS 3DEP 1 m DEM (public domain), USGS NAIP imagery (public domain)"
                   + (", team race-logger GPS centreline" if cfg.logger else ""),
        "notes": notes,
    }


def run_ghosts(cfg, pkg, work, no_logger, write_on_fail=False, quiet=False):
    cmd = [sys.executable, "-I", os.path.join(ROOT, "tools", "ghosts", "build_ghosts.py"), "--config", cfg["id"],
           "--track-dir", pkg, "--preview-dir", work, "--debug-out", os.path.join(work, "ghost_line_debug.npz")]
    if no_logger:
        cmd.append("--no-logger")
    if write_on_fail:
        cmd.append("--write-on-fail")
    r = subprocess.run(cmd, capture_output=quiet, text=True)
    return r.returncode


# ---------------------------------------------------------------- stage 1
def stage_geometry(cfg, out, no_logger):
    t0 = time.time()
    work = os.path.join(out, "work")
    os.makedirs(work, exist_ok=True)
    rep = Report(f"STAGE 1 GEOMETRY: {cfg['id']} ({'logger laps' if cfg.logger else 'no logger'})")
    cc, cen = cfg["captures"], dict(cfg["centre"])
    if REPRO.get("centre_bridge_win") is not None:
        cen["bridge_win"] = REPRO["centre_bridge_win"]
    if REPRO:
        log(f"reproducing the accepted package's build artefacts (config reproduce): {REPRO}")
    # -- loop and box
    P, _ = B.osm_loop()
    G = np.load(os.path.join(cfg["logger_dir"], "centreline.npy")) if cfg.logger else None
    P = V2.orient(P, G, cfg["direction"])
    box, C0box = V2.osm_box(P)
    img, W, H = B.fetch_ortho(box)
    ortho = B.Ortho(img, box)
    log("ENU box", box, f"ortho {W}x{H}")
    # graded ortho (the scenery stage regrades it identically: one black point, gamma 1.25, S-curve, +6 % saturation)
    ortho_path = os.path.join(work, "ortho.jpg")
    Image.fromarray(B.grade_ortho(img)).save(ortho_path, quality=84, optimize=True)
    O = {"x0": box[0], "y0": box[1], "x1": box[2], "y1": box[3], "width_px": W, "height_px": H}
    # -- first centre
    if cfg.logger:
        C, L, LG = V2.logger_centre(G, ortho, cen["naip_fit_a"], cen["naip_fit_b"])
    else:
        sf = cfg.enu(*cfg["start_finish_latlon"])
        C, L = V2.osm_centre(C0box, ortho, sf, cen["osm_fit_a"], cen["osm_fit_b"])
    n = len(C)
    log(f"first centre: n={n}, spline length {L:.2f} m")
    cfg2 = trackcfg.remap_stations(cfg, n)
    if cfg2 is not cfg:
        log(f"config stations mapped from {cfg['stations_ref'][0]} to {n} stations (fraction of the lap)")
        cfg = cfg2
        cen["extra_shadow_stations"] = cfg["centre"]["extra_shadow_stations"]
    hl, hr, st, raw_ok = V2.naip_edges(C, ortho)
    log("NAIP edges:", {k: round(v, 3) for k, v in st.items() if isinstance(v, float)})
    dem = B.Dem(box)
    dem_s = B.Dem(box, sigma=0.7)
    z0 = float(dem(C[:1, 0], C[:1, 1])[0])
    # -- corner anchors on the first centre (logger: its corner anchors in the logger frame; else lat/lon)
    if cfg.logger:
        sG, _ = B.project(C, G)
        Gu = np.unwrap(sG * 2 * np.pi / n) * n / (2 * np.pi)
        anchors = [float(np.interp(c[3], np.arange(len(G)), Gu) % n) for c in cfg["corners"]]
    else:
        pts = np.array([cfg.enu(c[4], c[5]) for c in cfg["corners"]])
        anchors = list(B.project(C, pts)[0])
    corners0, _, cf = V2.corners(C, cfg, anchors)
    if cfg.logger:
        # the driven line's corner radii, kept by the first centre (v2 acceptance; the painted-midpoint refit then
        # tightens the apexes the logged line cut, so this is not a check on the final centre)
        kC, kG = V2.kappa(C), V2.kappa(G)
        worst, rows = 0.0, []
        for c in corners0:
            if c["turn"] in (None, "T1", "T7") or not c.get("radius_m") or c["radius_m"] > 150:
                continue
            s = c["s"]
            iG = int(np.argmin(np.abs((sG - s + n / 2) % n - n / 2)))
            rG = 1 / np.abs(kG[np.arange(iG - V2.CORNER_WIN, iG + V2.CORNER_WIN + 1) % len(G)]).max()
            rC = 1 / np.abs(kC[np.arange(s - V2.CORNER_WIN, s + V2.CORNER_WIN + 1) % n]).max()
            worst = max(worst, abs(rC / rG - 1))
            rows.append(f"{c['turn']} {rC:.0f}/{rG:.0f}")
        rep.check("first centre: corner radii vs the driven line", worst <= V2.RADIUS_TOL,
                  f"worst {worst * 100:.0f} % (limit {V2.RADIUS_TOL * 100:.0f} %): " + ", ".join(rows))
    for f in cf:
        rep.check(f, False, "no curvature peak of the corner's direction near its anchor")
    # -- provisional package on the first centre: racing line (start of the paint walk, logged line) and the pit lane
    v2dir = os.path.join(work, "v2")
    os.makedirs(v2dir, exist_ok=True)
    prof_v2, res_v2 = V2.profile(C, hl, hr, dem_s, z0, cfg["repave_fixes"])
    hf_v2, nx, ny = V2.heightfield(box, dem, z0, C, hl, hr, res_v2)
    T_v2 = track_dict(cfg, C, hl, hr, prof_v2, z0, 1.0, n, corners0, box, W, H, nx, ny, {"stage": "provisional"})
    T_v2["length_m"] = float(n)
    json.dump(T_v2, open(os.path.join(v2dir, "track.json"), "w"), separators=(",", ":"))
    hf_v2.tofile(os.path.join(v2dir, "heightfield.bin"))
    shutil.copyfile(ortho_path, os.path.join(v2dir, "ortho.jpg"))
    # the refit works on the provisional package as written (mm-rounded), as the 18 Oct 2026 rebuild read its track.json
    C = np.array(T_v2["center"])[:, :2]
    nl_ = B.left_normals(C)
    hl = ((np.array(T_v2["left"])[:, :2] - C) * nl_).sum(1)
    hr = -((np.array(T_v2["right"])[:, :2] - C) * nl_).sum(1)
    line = np.zeros(n)
    e_gps = None
    if cfg.logger:
        log("provisional racing line on the first centre (build_ghosts.py)")
        run_ghosts(cfg, v2dir, v2dir, False, write_on_fail=True, quiet=True)
        g = json.load(open(os.path.join(v2dir, "ghosts.json")))
        line = np.interp(np.arange(n), np.arange(len(g["line"]["offset_m"])) * g["s_grid_m"], g["line"]["offset_m"], period=n)
        dbg = np.load(os.path.join(v2dir, "ghost_line_debug.npz"))
        e_gps = np.interp(np.arange(n), dbg["grid"], dbg["e_gps"], period=n)
    import build_scenery as BS
    BS.configure(cfg, v2dir)
    trk = BS.Track(T_v2, hf_v2)
    osm = BS.Osm()
    pit = BS.pit_lane(trk, osm)
    bar, _ = BS.barriers(trk, osm)
    cones = BS.pit_exit_cones(trk, pit, bar)
    shadow = BS.bridge_stations(trk, osm) + list(cen.get("extra_shadow_stations", []))
    # -- painted midpoint and the centre refit
    caps = CAP.capture_list(cfg, cfg["centre_captures"])
    log(f"painted edges on {len(caps)} {cfg['centre_captures']} captures ({cfg['centre_registration']} registration)")
    Pm = paint.measure(C, line, caps, Image.open(ortho_path), O, cc["mpp"], cfg["centre_registration"], log=log)
    json.dump(Pm["regs"], open(os.path.join(work, "paint_regs.json"), "w"))
    # logger path: fit_a keeps the driven line's curvature while the centre moves to the paint; no logger: the base is
    # the OSM loop, whose curvature is not to be kept (v1's kinks), so the move is soft and the positions are smoothed
    pfa, pfb = (cen["paint_fit_a"], cen["paint_fit_b"]) if cfg.logger else (cen["nologger_fit_a"], cen["nologger_fit_b"])
    # pit merges: the midpoint target takes the circuit's own edge where the pit lane joins (the cone line through the
    # pit-exit blend lane, else the painted edge interpolated across the join); config centre.pit_merge (default on;
    # off when reproducing an accepted package's build)
    merge = ({"parts": (pit or {}).get("parts", []), "cones": cones["pts"] if cones else None, "gap": cen.get("pit_merge_gap", 0.3)}
             if cen.get("pit_merge", True) and not REPRO and pit else None)
    fit = recentre.refit(C, hl, hr, Pm, shadow, (pit or {}).get("parts", []), (cones["s0"], cones["s1"]) if cones else None,
                         e_gps, pfa, pfb, cen["bridge_win"], cen["gps_margin"], cen["min_width"], merge=merge)
    C1, hl1, hr1, u, sp, L1 = fit["C"], fit["hl"], fit["hr"], fit["u"], fit["sp"], fit["L"]
    if REPRO.get("gps_margin_line") == "stale_refit_index":
        # Reproduces the accepted Laguna package only: on 18 Oct 2026 the GPS-margin step read a logged line measured on
        # the REFITTED centre (a ghost_line_debug.npz cache) as if it were on the first centre, index for index. The
        # centre is unaffected; the paint-step prior widens by up to ~4 m at a few apexes. Default: the first centre.
        rdir = os.path.join(work, "refit1")
        os.makedirs(rdir, exist_ok=True)
        T_r = track_dict(cfg, C1, hl1, hr1, np.zeros((n, 7)), z0, sp, L1, [], box, W, H, nx, ny, {"stage": "provisional"})
        json.dump(T_r, open(os.path.join(rdir, "track.json"), "w"), separators=(",", ":"))
        shutil.copyfile(ortho_path, os.path.join(rdir, "ortho.jpg"))
        run_ghosts(cfg, rdir, rdir, False, write_on_fail=True, quiet=True)
        dbg = np.load(os.path.join(rdir, "ghost_line_debug.npz"))
        e_stale = np.interp(np.arange(n), dbg["grid"], dbg["e_gps"], period=n)
        fit = recentre.refit(C, hl, hr, Pm, shadow, (pit or {}).get("parts", []), (cones["s0"], cones["s1"]) if cones else None,
                             e_stale, cen["paint_fit_a"], cen["paint_fit_b"], cen["bridge_win"], cen["gps_margin"], cen["min_width"])
        C1, hl1, hr1, u, sp, L1 = fit["C"], fit["hl"], fit["hr"], fit["u"], fit["sp"], fit["L"]
        log("paint-step prior: GPS margin from the logged line measured on the refitted centre (gps_margin_line stale_refit_index)")
    tiles = CAP.capture_list(cfg, cfg["spline"]["captures"])
    sp_cfg = dict(cfg["spline"])
    runs = sp_cfg["runs"] or [(0, n - 1)]
    features = [tuple(f[:4]) for f in cfg["features"]]
    if not cfg.logger:
        # no logger: the centre is the painted-road midpoint after the spline fit (one more refit on the fitted edges)
        NL1 = B.left_normals(C1)
        hs, rs = hl1.copy(), hr1.copy()
        for run in runs:
            hs, rs, _ = edges_spline.fit_run(C1, NL1, hs, rs, run[0], run[1], tiles, features, sp_cfg, cc["mpp"])
        P2 = {"lat_left": hs, "lat_right": -rs}
        fit2 = recentre.refit(C1, hl1, hr1, P2, [], [], None, None, pfa, pfb, 0,
                              cen["gps_margin"], cen["min_width"], merge=merge)
        C1, hl1, hr1, sp, L1 = fit2["C"], fit2["hl"], fit2["hr"], fit2["sp"], fit2["L"]
        fit["report"]["second_refit"] = fit2["report"]
    rep.check("painted-midpoint residual", fit["report"]["residual_mid_m"]["after_rms"] <= 0.6,
              f"rms {fit['report']['residual_mid_m']['before_rms']:.2f} -> {fit['report']['residual_mid_m']['after_rms']:.2f} m "
              f"({fit['report']['fit']['measured_stations']} stations measured)")
    NL = B.left_normals(C1)
    # -- corners on the final centre
    kap1 = B.curvature(C1, sigma=6)
    if cfg.logger:
        # the corners found on the first centre, carried to the new stations (old station k -> u[k]); radius re-measured
        corners = []
        for c in corners0:
            s = int(round(float(np.interp(c["s"], np.arange(n + 1), np.r_[u, n])))) % n
            c = dict(c, s=round(s * sp, 1))
            if c.get("radius_m"):
                c["radius_m"] = round(float(1 / max(abs(kap1[s]), 1e-6)), 1)
            corners.append(c)
    else:
        pts = np.array([cfg.enu(c[4], c[5]) for c in cfg["corners"]])
        corners, _, cf = V2.corners(C1, cfg, list(B.project(C1, pts)[0]))
        for c in corners:
            c["s"] = round(c["s"] * sp, 1)
    # -- profile at the paint-step edges (the spline and the straights re-evaluate it from each section's quadratic)
    prof0, resurface = V2.profile(C1, hl1, hr1, dem_s, z0, cfg["repave_fixes"])
    # -- edges: prior adjustments, shapes, spline runs, declared straights
    hl2, hr2 = hl1.copy(), hr1.copy()
    pcfg = cfg.get("prior", {})
    # bridge shadows in the prior: half-widths linearly interpolated across +-win stations of each crossing (the road
    # is straight under every bridge; was fix_bridge_edges.py), except the configured crossings (first-centre stations)
    if pcfg.get("bridge_win"):
        wn = pcfg["bridge_win"]
        for k_old in BS.bridge_stations(trk, osm):
            if any(abs(k_old - sk) <= 3 for sk in pcfg.get("bridge_skip", [])):
                continue
            k0 = int(round(float(np.interp(k_old, np.arange(n + 1), np.r_[u, n]))))
            lo, hi = k0 - wn, k0 + wn
            for arr in (hl2, hr2):
                a0, a1 = arr[lo % n], arr[hi % n]
                for k in range(lo, hi + 1):
                    arr[k % n] = a0 + (k - lo) / (hi - lo) * (a1 - a0)
            log(f"prior: bridge at first-centre station {k_old} (now {k0}): edges interpolated over +-{wn}")
    # stretches where the prior is the first centre's NAIP edge (on the white line where the paint step read an apron)
    for side, lo, hi, why in pcfg.get("first_edge", []):
        src = hl if side == "left" else hr
        sg = 1 if side == "left" else -1
        nl0 = B.left_normals(C)
        Wp = C + sg * src[:, None] * nl0                      # first-centre edge points, old stations
        sq, lq = B.project(C1, Wp); o_ = np.argsort(sq)
        on_new = sg * np.interp(np.arange(n), sq[o_], lq[o_], period=n)
        arr = hl2 if side == "left" else hr2
        bl = 10
        for k in range(lo, hi + 1):
            d = min(k - lo, hi - k); t = 1.0 if d >= bl else d / bl
            arr[k % n] = (1 - t) * arr[k % n] + t * on_new[k % n]
        log(f"prior: {side} {lo}..{hi} from the first-centre NAIP edge ({why})")
    for shp in cfg["shapes"]:
        side = shp["side"]
        if side == "left":
            hl2 = edges_spline.apply_shape(hl2, shp["knots"], shp.get("blend", 2), n)
        else:
            hr2 = edges_spline.apply_shape(hr2, shp["knots"], shp.get("blend", 2), n)
        log(f"shape {side} {shp['knots'][0][0]}..{shp['knots'][-1][0]}: {shp.get('why', '')}")
    pw = np.array([q[:2] for b in bar if b["kind"] == "pitwall" for q in b["pts"]]) if bar else None
    if cfg["straights"]:
        # the declared straights are known before the fit: put them in the prior too, so a 'keep' feature over a
        # straight holds the line, not the paint step's reading (re-applied after the fit)
        log("declared straights in the prior:")
        hl2, hr2, _ = straights.apply(C1, NL, hl2, hr2, cfg["straights"], tiles, cc["mpp"], pitwall=pw)
    # stretches where the prior is interpolated linearly between its end values (a junction the paint step misread)
    for side, lo, hi, why in pcfg.get("interp", []):
        arr = hl2 if side == "left" else hr2
        a0, a1 = arr[lo % n], arr[hi % n]
        for k in range(lo, hi + 1):
            arr[k % n] = a0 + (k - lo) / (hi - lo) * (a1 - a0)
        log(f"prior: {side} {lo}..{hi} interpolated ({why})")
    spline_rep = []
    for run in runs:
        lo, hi = run[0], run[1]
        tl = tiles
        if len(run) > 2 and run[2]:
            # captures available to this run (by name prefix), e.g. Laguna's T2 run had only the c20_a / c20_s clean captures
            tl = [t for t in tiles if t["kind"] == "z20" or any(t["name"].startswith(pf) for pf in run[2])]
        log(f"spline run {lo}..{hi} ({len(tl)} captures)")
        hl2, hr2, sr = edges_spline.fit_run(C1, NL, hl2, hr2, lo, hi, tl, features, sp_cfg, cc["mpp"])
        spline_rep.append(dict(lo=lo, hi=hi, **{k: v for k, v in sr.items()}))
        for side in ("left", "right"):
            if side in sr and isinstance(sr[side], dict) and "within" in sr[side]:
                rep.check(f"spline {lo}..{hi} {side} observations", sr[side]["within"] >= cfg["gate"]["spline_obs_within"],
                          f"{sr[side]['within'] * 100:.0f} % within 0.25 m of the curve, rms {sr[side]['rms']:.3f} m, "
                          f"{sr[side]['covered'] * 100:.0f} % of stations covered, longest gap {sr[side]['longest_gap']} st")
    hl3, hr3, str_rep = straights.apply(C1, NL, hl2, hr2, cfg["straights"], tiles, cc["mpp"], pitwall=pw)
    prof = V2.reprofile(prof0, hl1, hr1, hl3, hr3)
    # -- heightfield with the repave change carried in
    if REPRO.get("heightfield_centre") == "first":
        # reproduces the accepted Laguna package: its heightfield was built once on the first centre (the repave change
        # carried in along the first centre's stations) and not rebuilt after the refit
        hf = hf_v2
        log("heightfield: the first build's (heightfield_centre first)")
    else:
        hf, nx, ny = V2.heightfield(box, dem, z0, C1, hl3, hr3, resurface)
    notes = {
        "version": 3, "built_by": f"tools/track/build_track.py --track {cfg['id']}" + (" --no-logger" if no_logger else ""),
        "config": f"tools/track/tracks/{cfg['id']}/config.py",
        "centre": ("logger GPS-driven line moved toward the NAIP midpoint, then refitted to the painted-road midpoint "
                   "(centre.py, recentre.py)" if cfg.logger else
                   "OSM loop moved toward the NAIP midpoint, then refitted twice to the painted-road midpoint (the second "
                   "time to the spline-fitted edges)") + "; uniform stations (spacing L/n)",
        "edges": "one robust penalised cubic spline per side through the painted-line / kerb candidates of every capture "
                 "(edges_spline.py), config features and shapes, declared straights (straights.py)",
        "profile": "DEM sigma 0.7 m + lidar ground returns + clean_profile + repave fixes at the paint-step edges, "
                   "re-evaluated at the fitted edges from each section's quadratic",
    }
    T = track_dict(cfg, C1, hl3, hr3, prof, z0, sp, L1, corners, box, W, H, nx, ny, notes)
    # -- validation
    lc = cfg["loop_check"]
    rep.check("loop stations", lc["n_min"] <= n <= lc["n_max"], f"n = {n}")
    if lc.get("official_m"):
        rep.check("lap length", abs(L1 - lc["official_m"]) <= 0.01 * lc["official_m"],
                  f"{L1:.2f} m (official {lc['official_m']}; spacing {sp:.6f})")
    zc = prof[:, 3]
    rep.check("elevation range", lc["elev_min"] <= zc.max() - zc.min() <= lc["elev_max"], f"{zc.max() - zc.min():.1f} m (z0 {z0:.2f} NAVD88)")
    area = 0.5 * np.sum(C1[:, 0] * np.roll(C1[:, 1], -1) - np.roll(C1[:, 0], -1) * C1[:, 1])
    rep.check("direction", (area > 0) == (cfg["direction"] == "ccw"), f"signed area {area:.0f} m^2, config {cfg['direction']}")
    if cfg.logger:
        d0 = float(np.linalg.norm(C1[0] - G[0]))
        rep.check("start/finish", d0 <= 15, f"station 0 is {d0:.2f} m from centreline.npy[0]")
        # final corner radii against the driven line: advisory (the refit tightens the apexes the logged line cut)
        kC, kG = V2.kappa(C1), V2.kappa(G)
        sG1, _ = B.project(C1, G)
        rows = []
        for c in corners:
            if c["turn"] in (None, "T1", "T7") or not c.get("radius_m") or c["radius_m"] > 150:
                continue
            s = int(round(c["s"] / sp)) % n
            iG = int(np.argmin(np.abs((sG1 - s + n / 2) % n - n / 2)))
            rG = 1 / np.abs(kG[np.arange(iG - 60, iG + 61) % len(G)]).max()
            rC = 1 / np.abs(kC[np.arange(s - 60, s + 61) % n]).max()
            rows.append(f"{c['turn']} {rC:.0f}/{rG:.0f}")
        log("     final corner radii centre/driven line (advisory): " + ", ".join(rows))
    else:
        sf = np.array(cfg.enu(*cfg["start_finish_latlon"]))
        rep.check("start/finish", np.linalg.norm(C1[0] - sf) <= 5, f"station 0 is {np.linalg.norm(C1[0] - sf):.2f} m from the configured timing line")
    dl = np.abs(np.diff(np.r_[hl3, hl3[:1]]))
    dr = np.abs(np.diff(np.r_[hr3, hr3[:1]]))
    rep.check("edge jumps", max(dl.max(), dr.max()) <= V2.EDGE_JUMP, f"max lateral change between stations: left {dl.max():.3f} m, right {dr.max():.3f} m")
    fr = np.array(B.FRACTIONS)
    seg = np.diff(fr) * np.where(fr[1:] <= 0, hl3[:, None], hr3[:, None])
    cs = np.abs(np.diff(prof, axis=1)) / seg
    inner, outer = cs[:, 1:-1].max(1), np.maximum(cs[:, 0], cs[:, -1])
    rep.check("cross slope (inner 2/3)", inner.max() < V2.CROSS_HARD_V2,
              f"max {inner.max() * 100:.1f}% at s={int(inner.argmax())}; {np.sum(cs.max(1) > B.CROSS_SOFT)} stations over 12 % (listed in work/report.json)")
    rep.check("cross slope (edge thirds)", outer.max() < V2.EDGE_SEG_MAX, f"max {outer.max() * 100:.1f}% at s={int(outer.argmax())}")
    rep.check("no NaN", all(np.isfinite(a).all() for a in (C1, hl3, hr3, prof, hf)), "")
    # heightfield vs profile on the centreline
    gx = (C1[:, 0] - box[0]) / B.HF_DX
    gy = (C1[:, 1] - box[1]) / B.HF_DX
    from scipy.ndimage import map_coordinates
    zhf = map_coordinates(hf.astype(float), [gy, gx], order=1)
    dzc = np.abs(zhf - prof[:, 3])
    log(f"     heightfield vs profile on the centre: median {np.median(dzc):.3f} m, p95 {np.percentile(dzc, 95):.3f} m (the profile carries the lidar correction)")
    met, gf = edge_gate.gate(T, None, cfg["gate"], log=log)
    rep.fails += gf
    w = hl3 + hr3
    log(f"     width: median {np.median(w):.1f} m (p5 {np.percentile(w, 5):.1f}, p95 {np.percentile(w, 95):.1f}); corners: "
        + ", ".join(f"{c['turn'] or c['name']} s={c['s']} R={c['radius_m']}" for c in corners))
    report = {"provisional": {"shadow_stations": [int(v) for v in shadow], "cones": [cones["s0"], cones["s1"]] if cones else None,
                              "pit_parts": [p["track_s"] for p in (pit or {}).get("parts", [])]},
              "recentre": fit["report"], "spline": spline_rep, "straights": str_rep, "gate": met,
              "over_12pct": [int(i) for i in np.nonzero(cs.max(1) > B.CROSS_SOFT)[0]], "fails": rep.fails,
              "seconds": round(time.time() - t0, 1)}
    json.dump(report, open(os.path.join(work, "geometry_report.json"), "w"), indent=1, default=float)
    np.savez(os.path.join(work, "geometry_arrays.npz"), C_first=C, hl_first=hl, hr_first=hr, C=C1, hl_paint=hl1,
             hr_paint=hr1, hl=hl3, hr=hr3, u=u, prof0=prof0, prof=prof, line_first=line,
             paint_left=Pm["lat_left"], paint_right=Pm["lat_right"], paint_count=Pm["count"], C_refit=C1)
    nlf = B.left_normals(C1)
    B.preview(img, box, C1, C1 + hl3[:, None] * nlf, C1 - hr3[:, None] * nlf, prof[:, 3],
              [dict(c, s=int(round(c["s"] / sp)) % n) for c in corners], os.path.join(work, "preview.png"))
    if rep.fails and not WRITE_ON_FAIL:
        log("\nGEOMETRY STAGE FAILED:", rep.fails, "(nothing written to the package)")
        return 1
    json.dump(T, open(os.path.join(out, "track.json"), "w"), separators=(",", ":"))
    hf.tofile(os.path.join(out, "heightfield.bin"))
    shutil.copyfile(ortho_path, os.path.join(out, "ortho.jpg"))
    log(f"wrote {out}: track.json, heightfield.bin, ortho.jpg ({time.time() - t0:.0f} s)")
    if rep.fails:
        log("\nGEOMETRY STAGE FAILED:", rep.fails, "(written anyway: --write-on-fail, for diagnosis only)")
        return 1
    return 0


# ---------------------------------------------------------------- stage 2
def stage_ghosts(cfg, out, no_logger):
    work = os.path.join(out, "work")
    os.makedirs(work, exist_ok=True)
    log(f"\n================ STAGE 2 GHOSTS: {cfg['id']} ================")
    return run_ghosts(cfg, out, work, no_logger or not cfg.logger)


# ---------------------------------------------------------------- stage 3
def stage_scenery(cfg, out, no_logger):
    import build_scenery as BS
    import scenery_post

    work = os.path.join(out, "work")
    tmp = os.path.join(work, "scenery_tmp")
    os.makedirs(tmp, exist_ok=True)
    for f in ("track.json", "heightfield.bin", "ortho.jpg"):
        shutil.copyfile(os.path.join(out, f), os.path.join(tmp, f))
    log(f"\n================ STAGE 3 SCENERY: {cfg['id']} ================")
    Tt0 = json.load(open(os.path.join(out, "track.json")))
    cfg = trackcfg.remap_stations(cfg, Tt0["n"], Tt0["length_m"])
    BS.PITWALL_EDGE = None
    if cfg["scenery"].get("pit_wall", {}).get("at") == "first_edge":
        G_ = np.load(os.path.join(work, "geometry_arrays.npz"))
        Tt = json.load(open(os.path.join(out, "track.json")))
        Cf = np.array(Tt["center"])[:, :2]
        Wp = G_["C_first"] + G_["hl_first"][:, None] * B.left_normals(G_["C_first"])
        sq, lq = B.project(Cf, Wp); o_ = np.argsort(sq)
        BS.PITWALL_EDGE = np.interp(np.arange(len(Cf)), sq[o_], lq[o_], period=len(Cf))
        log("pit wall 0.6 m off the first build's NAIP left edge (pit_wall.at = first_edge)")
    BS.main(cfg, tmp)
    T = json.load(open(os.path.join(tmp, "track.json")))
    SC = json.load(open(os.path.join(tmp, "scenery.json")))
    scfg = cfg["scenery"]
    tiles = CAP.capture_list(cfg, scfg.get("apron_captures", "clean"))
    tiles = [t for t in tiles if t["name"] not in cfg["captures"].get("exclude", [])]
    regs = None
    if scfg.get("apron_registration") == "per_capture":
        rp = os.path.join(work, "paint_regs.json")
        regs = {r[0]: r for r in json.load(open(rp))} if os.path.exists(rp) else None
    log("post steps:")
    scenery_post.run(T, SC, scfg, tiles, cfg["captures"]["mpp"], regs)
    rep = Report("SCENERY VALIDATION")
    _, gf = edge_gate.gate(T, SC, cfg["gate"], log=log)
    rep.fails += gf
    # barriers never on the road: every barrier point at least 0.5 m outside the edge (pit wall 0.3 m)
    trk = BS.Track(T, np.fromfile(os.path.join(tmp, "heightfield.bin"), np.float32).reshape(T["heightfield"]["ny"], T["heightfield"]["nx"]))
    worst = []
    for b in SC["barriers"]:
        _, _, dout = trk.project(np.array(b["pts"])[:, :2])
        worst.append((float(dout.min()), b["kind"]))
    bad = [w for w in worst if w[0] < (0.3 if w[1] == "pitwall" else 0.5)]
    rep.check("barrier gaps", not bad, f"min gap to the edge {min(w[0] for w in worst):.2f} m over {len(worst)} runs"
              + (f"; {len(bad)} runs closer than 0.5 m (pit wall 0.3 m)" if bad else ""))
    counts = {k: (len(v) if isinstance(v, list) else len(v.get("parts", v.get("strips", v.get("runs", v.get("pts", []))))))
              for k, v in SC.items() if isinstance(v, (list, dict)) and k not in ("far", "notes")}
    counts["trees"] = len(SC["trees"]["data"]) // 5
    counts["far_trees"] = len(SC["far_trees"]["data"]) // 5
    log("     counts: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    if rep.fails and not WRITE_ON_FAIL:
        log("\nSCENERY STAGE FAILED:", rep.fails, "(nothing written to the package)")
        return 1
    json.dump(SC, open(os.path.join(out, "scenery.json"), "w"), separators=(",", ":"))
    for f in ("far_heightfield.bin", "far_ortho.jpg", "ortho.jpg"):
        shutil.copyfile(os.path.join(tmp, f), os.path.join(out, f))
    shutil.copyfile(os.path.join(tmp, "scenery_preview.png"), os.path.join(work, "scenery_preview.png"))
    log(f"wrote {out}: scenery.json, far_heightfield.bin, far_ortho.jpg, regraded ortho.jpg")
    if rep.fails:
        log("\nSCENERY STAGE FAILED:", rep.fails, "(written anyway: --write-on-fail, for diagnosis only)")
        return 1
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--track", required=True, help="track id: tools/track/tracks/<id>/config.py")
    ap.add_argument("--stage", default="all", choices=["geometry", "ghosts", "scenery", "all"])
    ap.add_argument("--no-logger", action="store_true", help="build as if the config had no logger_dir")
    ap.add_argument("--out", default=None, help="candidate package directory (default tools/track/out/<id>)")
    ap.add_argument("--no-reproduce", action="store_true", help="ignore the config's `reproduce` block (build artefacts of an accepted package)")
    ap.add_argument("--write-on-fail", action="store_true", help="write a failed stage's outputs anyway (diagnosis only; still exits 1)")
    ap.add_argument("--publish", action="store_true", help="copy the package to public/tracks/<id>/ when every stage passed")
    ap.add_argument("--overwrite-package", action="store_true", help="with --publish: replace an existing public/tracks/<id>/")
    a = ap.parse_args()
    global WRITE_ON_FAIL, REPRO
    WRITE_ON_FAIL = a.write_on_fail
    cfg = trackcfg.load(a.track, no_logger=a.no_logger)
    REPRO = dict(cfg.get("reproduce") or {}) if cfg.logger and not a.no_reproduce else {}
    B.configure(cfg)
    out = os.path.abspath(a.out or os.path.join(HERE, "out", cfg["id"] + ("_nologger" if a.no_logger else "")))
    pub = os.path.join(ROOT, "public", "tracks", cfg["id"])
    if os.path.realpath(out) == os.path.realpath(pub):
        raise SystemExit("--out must not be the published package; use --publish")
    os.makedirs(out, exist_ok=True)
    stages = ["geometry", "ghosts", "scenery"] if a.stage == "all" else [a.stage]
    failed = []
    for st in stages:
        rc = {"geometry": stage_geometry, "ghosts": stage_ghosts, "scenery": stage_scenery}[st](cfg, out, a.no_logger)
        if rc:
            failed.append(st)
            if not WRITE_ON_FAIL:
                return rc
    if failed:
        log(f"\nFAILED stages: {failed} (outputs written for diagnosis only: --write-on-fail; not publishable)")
        return 1
    if a.publish:
        if os.path.exists(os.path.join(pub, "track.json")) and not a.overwrite_package:
            raise SystemExit(f"{pub} exists: pass --overwrite-package to replace it")
        os.makedirs(pub, exist_ok=True)
        for f in ("track.json", "heightfield.bin", "ortho.jpg", "ghosts.json", "scenery.json", "far_heightfield.bin", "far_ortho.jpg"):
            if os.path.exists(os.path.join(out, f)):
                shutil.copyfile(os.path.join(out, f), os.path.join(pub, f))
        log(f"published {pub}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
