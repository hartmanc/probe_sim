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
  scenery   (stage 3) build_scenery.py then scenery_post.py, then the edge gate with the walls and bridges, then the
            containment, pit-connectivity and sign-placement gates (gates/sceneryGates.ts), then the coverage and
            pit-lane gates against the eye-level inventory (gates/coverageGate.ts, compare/<id>/inventory.json).
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


INPUTS = {}   # provenance of the stage's inputs (file sizes and hashes), written into its stage record


def file_id(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return {"path": os.path.relpath(path, ROOT), "bytes": os.path.getsize(path), "sha256": h.hexdigest()[:16]}


STAGE_FILES = {"geometry": ["track.json", "heightfield.bin", "ortho.jpg"], "ghosts": ["ghosts.json"],
               "scenery": ["scenery.json", "far_heightfield.bin", "far_ortho.jpg", "ortho.jpg"]}
STAGE_NEEDS = {"geometry": [], "ghosts": ["track.json"], "scenery": ["track.json", "heightfield.bin"]}


STAGE_KEYS = {"ghosts": ("ghosts",), "scenery": ("scenery", "gate", "pit_lane")}


def config_id(cfg, stage="geometry"):
    """hash of the config keys a stage reads (geometry: everything but the ghosts, scenery, pit_lane and app blocks), so
    a scenery edit does not invalidate a passed geometry stage (pit_lane, 21 Oct 2026, is read by stage 3 only)"""
    import hashlib
    if stage == "geometry":
        d = {k: v for k, v in cfg.items() if k not in ("ghosts", "scenery", "pit_lane", "app")}
    else:
        d = {k: cfg.get(k) for k in STAGE_KEYS[stage]}
    return hashlib.sha256(json.dumps(d, sort_keys=True, default=str).encode()).hexdigest()[:16]


def write_record(cfg, out, stage, passed, no_logger, inputs_of=None):
    """work/stage_<stage>.json: whether the stage's gates passed, the config hash, the hashes of the package files it
    consumed and wrote. --publish trusts only records that are current (every hash still matches)."""
    rec = {"stage": stage, "passed": bool(passed), "config": config_id(cfg, stage), "no_logger": bool(no_logger),
           "time": time.strftime("%Y-%m-%d %H:%M:%S"),
           "consumed": {f: file_id(os.path.join(out, f))["sha256"] for f in (inputs_of or STAGE_NEEDS[stage])},
           "wrote": {f: file_id(os.path.join(out, f))["sha256"] for f in STAGE_FILES[stage] if os.path.exists(os.path.join(out, f))},
           "inputs": dict(INPUTS)}
    json.dump(rec, open(os.path.join(out, "work", f"stage_{stage}.json"), "w"), indent=1)


def record_ok(cfg, out, stage, no_logger):
    """(ok, why): the stage passed with this config and its outputs and consumed inputs are unchanged since."""
    p = os.path.join(out, "work", f"stage_{stage}.json")
    if not os.path.exists(p):
        return False, f"no record of stage {stage}"
    rec = json.load(open(p))
    if not rec["passed"]:
        return False, f"stage {stage} failed its gates ({rec['time']})"
    if rec["config"] != config_id(cfg, stage) or rec.get("no_logger") != bool(no_logger):
        return False, f"stage {stage} was built with another config"
    for f in STAGE_FILES[stage]:
        fp = os.path.join(out, f)
        if not os.path.exists(fp) or rec["wrote"].get(f) != file_id(fp)["sha256"]:
            if not (stage == "geometry" and f == "ortho.jpg"):   # the scenery stage regrades ortho.jpg
                return False, f"{f} changed or missing since stage {stage}"
    for f, h in rec["consumed"].items():
        fp = os.path.join(out, f)
        if not os.path.exists(fp) or file_id(fp)["sha256"] != h:
            return False, f"stage {stage} consumed another {f} than the current one (stale)"
    return True, ""


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
    cfg_raw = cfg
    cfg2 = trackcfg.remap_stations(cfg, n) if cfg.logger else trackcfg.remap_stations(cfg, n, C=C)
    if cfg2 is not cfg:
        log(f"config stations mapped from {cfg['stations_ref'][0]} to {n} stations (fraction of the lap)")
        cfg = cfg2
        cen["extra_shadow_stations"] = cfg["centre"]["extra_shadow_stations"]
    hl, hr, st, raw_ok = V2.naip_edges(C, ortho)
    log("NAIP edges:", {k: round(v, 3) for k, v in st.items() if isinstance(v, float)})
    # lidar ground returns for the profile: fetched here (stage 1), never left to whether the scenery stage ran before
    import build_scenery as BS
    BS.configure(cfg, work)
    if not cfg.get("lidar_ept"):
        raise SystemExit("config lidar_ept missing: the profile needs the survey's point cloud")
    BS.lidar_points(box)
    V2.LIDAR_POINTS = BS.cache_file("lidar_points.npz", box)
    INPUTS["lidar_points"] = file_id(V2.LIDAR_POINTS)
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
            if c["turn"] is None or c["turn"] in cfg.get("radius_check_skip", []) or not c.get("radius_m") or c["radius_m"] > 150:
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
                         e_gps, pfa, pfb, cen["bridge_win"], cen["gps_margin"], cen["min_width"], merge=merge,
                         width_cap=cen.get("width_cap", 16.0))
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
    if REPRO:
        # LEGACY: how the accepted Laguna package was built on 17-18 Oct 2026 (paint-step prior, measured shapes,
        # open spline runs, declared straights overwritten after the fit with blends). Kept only to reproduce that
        # package (config `reproduce`); every other build takes the fitted method below.
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
            for k_old in BS.bridge_stations(trk, osm) + list(pcfg.get("extra_bridges", [])):
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
            if shp.get("fitted_only"):
                continue
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
    else:
        C1, hl1, hr1, hl3, hr3, sp, L1, fit, corners, prof0, resurface, prof, spline_rep, str_rep, cfg = fitted_method(
            cfg_raw, cfg, C, hl, hr, C1, hl1, hr1, fit, trk, osm, bar, merge, pfa, pfb, cen, cc, dem_s, z0, rep)
        n = len(C1)
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
            if c["turn"] is None or c["turn"] in cfg.get("radius_check_skip", []) or not c.get("radius_m") or c["radius_m"] > 150:
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
    met, gf = edge_gate.gate(T, None, cfg["gate"], log=log, world=not REPRO)
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


def fitted_method(cfg_raw, cfg, C0, hl0, hr0, C1, hl1, hr1, fit, trk, osm, bar, merge, pfa, pfb, cen, cc, dem_s, z0, rep):
    """The fitted method (20 Oct 2026, owner's rule: edges FITTED, never traced or patched): one periodic robust spline
    per side over the whole lap with the declared straights and measured shapes as constraints INSIDE the fit; config
    stations mapped onto each centre by world position; without logger laps the centre is refitted to the midpoint of
    the fitted edges and the edges refitted on the new normals until the centre moves less than 5 cm. The fit's
    acceptance numbers are gates (edge_gate.FITTED), not printouts."""
    import build_scenery as BS
    sp_cfg = dict(cfg_raw["spline"])
    tiles = CAP.capture_list(cfg_raw, sp_cfg["captures"])
    n = len(C1)
    nl0 = B.left_normals(C0)
    bridges_world = [C0[k % len(C0)] for k in BS.bridge_stations(trk, osm)]   # OSM crossings, first-centre stations
    pw = np.array([q[:2] for b in bar if b["kind"] == "pitwall" for q in b["pts"]]) if bar else None
    Ccur, hlp, hrp = C1, hl1.copy(), hr1.copy()
    fit_last = fit
    for it in range(40):
        cfgw = trackcfg.remap_stations(cfg_raw, n, float(np.linalg.norm(np.roll(Ccur, -1, 0) - Ccur, axis=1).sum()), C=Ccur)
        NL = B.left_normals(Ccur)
        pcfg = cfgw.get("prior", {})
        # prior adjustments (the prior is only the fit's weak fallback where there is no evidence)
        if pcfg.get("bridge_win") and it == 0:
            wn = pcfg["bridge_win"]
            kb = [int(B.project(Ccur, p[None])[0][0]) for p in bridges_world] + list(pcfg.get("extra_bridges", []))
            for k0 in kb:
                if any(abs(k0 - sk) <= 3 for sk in pcfg.get("bridge_skip", [])):
                    continue
                lo, hi = k0 - wn, k0 + wn
                for arr in (hlp, hrp):
                    a0, a1 = arr[lo % n], arr[hi % n]
                    for k in range(lo, hi + 1):
                        arr[k % n] = a0 + (k - lo) / (hi - lo) * (a1 - a0)
                log(f"prior: bridge at station {k0}: interpolated over +-{wn}")
        if it == 0:
            for side, lo, hi, why in pcfg.get("first_edge", []):
                src = hl0 if side == "left" else hr0; sg = 1 if side == "left" else -1
                sq, lq = B.project(Ccur, C0 + sg * src[:, None] * nl0); o_ = np.argsort(sq)
                on_new = sg * np.interp(np.arange(n), sq[o_], lq[o_], period=n)
                arr = hlp if side == "left" else hrp
                for k in range(lo, hi + 1):
                    arr[k % n] = on_new[k % n]
                log(f"prior: {side} {lo}..{hi} from the first-centre NAIP edge ({why})")
            for side, lo, hi, why in pcfg.get("interp", []):
                arr = hlp if side == "left" else hrp
                a0, a1 = arr[lo % n], arr[hi % n]
                for k in range(lo, hi + 1):
                    arr[k % n] = a0 + (k - lo) / ((hi - lo) % n) * (a1 - a0)
                log(f"prior: {side} {lo}..{hi} interpolated ({why})")
        # constraints inside the fit: declared straights, measured shapes (world-mapped knots)
        anchors = {"left": ([], [], []), "right": ([], [], [])}
        aw = sp_cfg.get("anchor_w", 20.0)
        if cfgw["straights"]:
            tg, str_rep = straights.targets(Ccur, NL, hlp, hrp, cfgw["straights"], tiles, cc["mpp"], pitwall=pw)
            for side in ("left", "right"):
                anchors[side][0].extend(tg[side][0]); anchors[side][1].extend(tg[side][1]); anchors[side][2].extend([aw] * len(tg[side][0]))
        else:
            str_rep = []
        for shp in cfgw["shapes"]:
            xs = [k for k, _ in shp["knots"]]; f = edges_spline.pchip(xs, [v for _, v in shp["knots"]])
            # a declared straight takes precedence where both cover a station (two constraints must not disagree)
            taken = {k % n for k in anchors[shp["side"]][0]}
            ks = [k for k in range(xs[0], xs[-1] + 1) if k % n not in taken]
            anchors[shp["side"]][0].extend(ks); anchors[shp["side"]][1].extend([f(k) for k in ks]); anchors[shp["side"]][2].extend([aw] * len(ks))
            log(f"shape {shp['side']} {xs[0]}..{xs[-1]}: constraint inside the fit ({shp.get('why', '')[:60]})")
        # taper each constraint run's weight over its first and last `anchor_ramp` stations (20 Oct 2026: a full-weight
        # constraint starting abruptly made a 0.04 m rolling wave where the free fit hands over, at Sonoma's front
        # straight start and the T7 road)
        ramp = int(sp_cfg.get("anchor_ramp", 10))
        for side in ("left", "right"):
            ks_, _, ws_ = anchors[side]
            if not ks_ or ramp <= 0:
                continue
            kk = np.array(ks_) % n
            have = set(kk.tolist())
            for j, k in enumerate(kk):
                d = min(next((m for m in range(1, ramp + 1) if (k - m) % n not in have), ramp + 1),
                        next((m for m in range(1, ramp + 1) if (k + m) % n not in have), ramp + 1))
                if d <= ramp:
                    ws_[j] = ws_[j] * d / (ramp + 1)
        keeps = [f for f in cfgw["features"] if f[3] == "keep"]
        if keeps:
            log(f"features: {len(keeps)} 'keep' zones are not part of the fitted method and are ignored: "
                + ", ".join(f"{f[0]} {f[1]}..{f[2]}" for f in keeps))
        features = [tuple(f[:4]) for f in cfgw["features"] if f[3] != "keep"]
        log(f"fitted method, iteration {it + 1}: periodic spline per side on {len(tiles)} captures")
        hl3, hr3, frep = edges_spline.fit_periodic(Ccur, NL, hlp, hrp, tiles, features, sp_cfg, cc["mpp"],
                                                   {k: v for k, v in anchors.items() if v[0]})
        if cfg_raw.logger:
            break
        P2 = {"lat_left": hl3, "lat_right": -hr3}
        fit2 = recentre.refit(Ccur, hlp, hrp, P2, [], [], None, None, pfa, pfb, 0, cen["gps_margin"], cen["min_width"],
                              merge=merge, width_cap=cen.get("width_cap", 16.0))
        Cn = fit2["C"]
        if it >= 2:
            # under-relaxation from the third refit on, step 1/it (Sonoma's T7 hairpin centre kept swinging 0.3-0.6 m
            # between full refits: a limit cycle of the edge association there); the converged centre is the average
            alpha = 1.0 / it
            _, latc = B.project(Cn, Ccur)
            Cd = Ccur - alpha * latc[:, None] * B.left_normals(Ccur)
            Cn, _ = B.resample_closed(Cd, n=n, smooth=0.0)
        _, lat = B.project(Cn, Ccur)
        move = float(np.abs(lat).max()); move_at = int(np.argmax(np.abs(lat)))
        # the fitted edges' WORLD points re-expressed on the new centre's normals are the next prior
        for side, hw in (("left", hl3), ("right", hr3)):
            sg = 1 if side == "left" else -1
            sq, lq = B.project(Cn, Ccur + sg * hw[:, None] * NL); o_ = np.argsort(sq)
            v = sg * np.interp(np.arange(n), sq[o_], lq[o_], period=n)
            if side == "left": hlp = v
            else: hrp = v
        fit_last = fit2
        log(f"centre refit to the midpoint of the fitted edges: max move {move:.3f} m at station {move_at}; residual "
            f"{fit2['report']['residual_mid_m']['before_rms']:.3f} -> {fit2['report']['residual_mid_m']['after_rms']:.3f} m rms")
        Ccur = Cn
        if move < 0.05 and it >= 1:
            NL = B.left_normals(Ccur)
            cfgw = trackcfg.remap_stations(cfg_raw, n, fit2["L"], C=Ccur)
            hl3, hr3, frep = edges_spline.fit_periodic(Ccur, NL, hlp, hrp, tiles, features, sp_cfg, cc["mpp"],
                                                       {k: v for k, v in anchors.items() if v[0]})
            log(f"converged after {it + 1} centre refits")
            break
    else:
        rep.check("centre convergence", False, f"centre still moving {move:.3f} m after 40 refits")
    seg = np.linalg.norm(np.roll(Ccur, -1, 0) - Ccur, axis=1); L = float(seg.sum()); sp = L / n
    # -- gates of the fitted method (edge_gate.FITTED; a config may tighten them, never loosen)
    G = edge_gate.fitted_thresholds(cfg_raw["gate"])
    for side in ("left", "right"):
        r = frep[side]
        # the declared junctions (config gate.exempt, pit-lane joins) are excluded from the waviness and kink metrics as
        # from the step metric; observation share, coverage and gaps count everywhere
        for sd, lo, hi, *_ in cfgw["gate"].get("exempt", []):
            if sd == side:
                r["loose"][np.array([k % n for k in range(lo, hi + (n if hi < lo else 0) + 1)])] = False
        rep.check(f"fit {side}: observations within 0.25 m", r["within_gated"] >= G["within"] and r["assoc_share"] >= G["assoc"],
                  f"{r['within_gated'] * 100:.1f} % of the associated observations (>= {G['within'] * 100:.0f} %, the skill's measure); "
                  f"{r['assoc_share'] * 100:.0f} % of capture rows have a band within 1.2 m (>= {G['assoc'] * 100:.0f} %); of those "
                  f"{r['within'] * 100:.1f} % within 0.25 m, the rest at 0.25-0.4/0.4-0.6/0.6-0.8/0.8-1.0/1.0-1.2 m: {r['off_hist']}; "
                  f"{r['within_all'] * 100:.0f} % of all rows")
        lo_ = r["loose"]
        # rolling waviness over the loose stations only (a junction or tight corner inside a 100-station window is left
        # out of that window's rms, not only the windows centred on it)
        roll = np.zeros(n)
        for k in range(n):
            w_ = np.arange(k - 50, k + 50) % n; m_ = lo_[w_]
            roll[k] = np.sqrt(np.mean(r["qq"][w_][m_] ** 2)) if m_.sum() >= 50 else 0.0
        r["roll"] = roll
        r["wave_rms"] = float(roll[lo_].max()); r["wave_peak"] = float(np.abs(r["qq"])[lo_].max()); r["kink"] = float(r["kinkv"][lo_].max())
        rep.check(f"fit {side}: coverage", r["covered"] >= G["covered"],
                  f"{r['covered'] * 100:.0f} % of stations (>= {G['covered'] * 100:.0f} %)")
        bad = [f"{a}..{b} ({ln} st)" for (a, b), ln in r["gaps"] if ln > G["gap"]]
        rep.check(f"fit {side}: longest gap", not bad, f"{r['longest_gap']} st at {r['gap_at']} (<= {G['gap']})"
                  + (f"; over: {', '.join(bad)}" if bad else ""))
        wr = edges_spline.ranges(r["loose"] & (r["roll"] > G["wave_rms"]), n)
        rep.check(f"fit {side}: waviness", not wr and r["wave_peak"] <= G["wave_peak"],
                  f"rolling-100 rms max {r['wave_rms']:.3f} m (<= {G['wave_rms']}), peak {r['wave_peak']:.3f} m (<= {G['wave_peak']}) "
                  f"outside tight corners" + (f"; over at {wr[:8]}" if wr else ""))
        kr = edges_spline.ranges(r["loose"] & (r["kinkv"] > G["kink"]), n)
        rep.check(f"fit {side}: kink", not kr, f"max {r['kink']:.2f} deg/station (<= {G['kink']}) outside tight corners; "
                  f"station 0 {r['seam_kink']:.2f}" + (f"; over at {kr[:8]}" if kr else ""))
    rep.check("painted-midpoint residual", fit_last["report"]["residual_mid_m"]["after_rms"] <= 0.6,
              f"rms {fit_last['report']['residual_mid_m']['before_rms']:.2f} -> {fit_last['report']['residual_mid_m']['after_rms']:.2f} m (final refit)")
    # -- corners on the final centre
    # corner anchors: the configured lat/lon of each corner, projected on the final centre
    pts = np.array([cfg_raw.enu(c[4], c[5]) for c in cfg_raw["corners"]])
    corners, _, cf = V2.corners(Ccur, cfg_raw, list(B.project(Ccur, pts)[0]))
    for c in corners:
        c["s"] = round(c["s"] * sp, 1)
    for f in cf:
        rep.check(f, False, "no curvature peak of the corner's direction near its anchor")
    prof0, resurface = V2.profile(Ccur, hlp, hrp, dem_s, z0, cfgw["repave_fixes"])
    prof = V2.reprofile(prof0, hlp, hrp, hl3, hr3)
    spline_rep = [{k: v for k, v in frep[s_].items() if k not in ("roll", "qq", "kinkv", "loose")} | {"side": s_} for s_ in ("left", "right")]
    return Ccur, hlp, hrp, hl3, hr3, sp, L, fit_last, corners, prof0, resurface, prof, spline_rep, str_rep, cfgw


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
    cfg = (trackcfg.remap_stations(cfg, Tt0["n"], Tt0["length_m"]) if (cfg.logger and not no_logger)
           else trackcfg.remap_stations(cfg, Tt0["n"], Tt0["length_m"], C=np.array(Tt0["center"])[:, :2]))
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
    _, gf = edge_gate.gate(T, SC, cfg["gate"], log=log, world=not REPRO)
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
    # the three scenery gates of 20 Oct 2026 (tools/track/gates/sceneryGates.ts): containment, pit connectivity, sign
    # placement, on the scenery just built; config scenery.gates {allowed: [{target, side, a, b (lat, lon on the track),
    # why}], paddock: [{name, latlon: [...]}], pit_box_latlon, reach, step}
    rep.fails += scenery_gates(cfg, T, SC, tmp, trk)
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
    if os.path.exists(os.path.join(tmp, "gates_report.json")):
        shutil.copyfile(os.path.join(tmp, "gates_report.json"), os.path.join(work, "gates_report.json"))
    if os.path.exists(os.path.join(tmp, "coverage_report.json")):
        shutil.copyfile(os.path.join(tmp, "coverage_report.json"), os.path.join(work, "coverage_report.json"))
    log(f"wrote {out}: scenery.json, far_heightfield.bin, far_ortho.jpg, regraded ortho.jpg")
    if rep.fails:
        log("\nSCENERY STAGE FAILED:", rep.fails, "(written anyway: --write-on-fail, for diagnosis only)")
        return 1
    return 0


def scenery_gates(cfg, T, SC, tmp, trk):
    """Run the TypeScript scenery gates on scenery.json in `tmp` (written first) and print their report; returns the
    failed gate labels."""
    g = dict(cfg["scenery"].get("gates", {}))
    out = {k: g[k] for k in ("reach", "step") if k in g}
    sp = T["spacing_m"]
    al = []
    for a in g.get("allowed", []):
        P = np.array([cfg.enu(*a["a"]), cfg.enu(*a["b"])], float)
        i, _, _ = trk.project(P)
        al.append({"target": a["target"], **({"side": a["side"]} if a.get("side") else {}), "s0": round(float(i[0]) * sp, 1),
                   "s1": round(float(i[1]) * sp, 1), "why": a["why"]})
    out["allowed"] = al
    out["paddock"] = [{"name": p["name"], "poly": [list(cfg.enu(*q)) for q in p["latlon"]]} for p in g.get("paddock", [])]
    if g.get("pit_box_latlon"):
        i, _, _ = trk.project(np.array([cfg.enu(*g["pit_box_latlon"])]))
        out["pit_box_s"] = round(float(i[0]) * sp, 1)
    json.dump(SC, open(os.path.join(tmp, "scenery.json"), "w"), separators=(",", ":"))
    cp = os.path.join(tmp, "gates_config.json")
    json.dump(out, open(cp, "w"))
    r = subprocess.run(["npx", "tsx", os.path.join(HERE, "gates", "run_gates.ts"), tmp, cp], cwd=ROOT, capture_output=True, text=True)
    fails = []
    for line in r.stdout.splitlines():
        if line.startswith("GATES_JSON "):
            json.dump(json.loads(line[11:]), open(os.path.join(tmp, "gates_report.json"), "w"), indent=1)
            continue
        log(line)
        if line.startswith("[FAIL]"):
            fails.append(line[7:].split(":")[0])
    if r.returncode not in (0, 1) or (r.returncode == 1 and not fails):
        log(r.stderr[-2000:])
        fails.append("scenery gates did not run")
    fails += coverage_gates(cfg, tmp, trk, sp)
    return fails


def manifest_assignments(cfg):
    """MISSING inventory rows the evidence manifest (tools/track/compare/<id>/manifest.md) hands to another round: every
    markdown table row whose last cell reads 'assigned: <round>', its first three cells kind | side | s (m). The coverage
    gate accepts them for kind building only and lists them as ASSIGNED (21 Oct 2026); any other kind is REJECTED."""
    import re
    path = os.path.join(HERE, "compare", cfg["id"], "manifest.md")
    out = []
    if not os.path.exists(path):
        return out
    for line in open(path):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or not line.lstrip().startswith("|"):
            continue
        m = re.match(r"assigned:\s*(.+)$", cells[-1])
        if not m:
            continue
        try:
            out.append({"kind": cells[0], "side": cells[1], "s": float(cells[2]), "to": m.group(1).strip(), "what": cells[3]})
        except ValueError:
            continue
    return out


def coverage_gates(cfg, tmp, trk, sp):
    """The coverage and pit-lane gates of 21 Oct 2026 (tools/track/gates/coverageGate.ts, CLI run_coverage.ts): the
    scenery in `tmp` against the eye-level inventory tools/track/compare/<id>/inventory.json (inventory/inventory.py)
    and the config's pit_lane walls. Every circuit needs the inventory: without one both gates fail."""
    fails = [f"pit_lane config: {e}" for e in trackcfg.check_pit_lane(cfg)]
    for e in fails:
        log(f"[FAIL] {e}")
    inv = os.path.join(HERE, "compare", cfg["id"], "inventory.json")
    if not os.path.exists(inv):
        log(f"[FAIL] coverage: no inventory ({os.path.relpath(inv, ROOT)}); the inventory stage is required before scenery (build-track skill)")
        return fails + ["coverage", "pit lane"]
    proj = lambda ll: round(float(trk.project(np.array([cfg.enu(*ll)]))[0][0]) * sp, 1)  # noqa: E731
    cp = os.path.join(tmp, "coverage_config.json")
    json.dump({"tol": cfg["scenery"].get("gates", {}).get("coverage_tol", 15), "pit_walls": trackcfg.pit_walls_for_gate(cfg, proj),
               "assigned": manifest_assignments(cfg)}, open(cp, "w"))
    r = subprocess.run(["npx", "tsx", os.path.join(HERE, "gates", "run_coverage.ts"), tmp, inv, cp, "--json",
                        os.path.join(tmp, "coverage_report.json")], cwd=ROOT, capture_output=True, text=True)
    for line in r.stdout.splitlines():
        if line.startswith("COVERAGE_JSON "):
            continue
        log(line)
        if line.startswith("[FAIL]"):
            fails.append(line[7:].split(":")[0])
    if r.returncode not in (0, 1) or (r.returncode == 1 and not fails):
        log(r.stderr[-2000:])
        fails.append("coverage gate did not run")
    return fails


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
        INPUTS.clear()
        if st != "geometry":
            ok, why = record_ok(cfg, out, "geometry", a.no_logger)
            if not ok and not WRITE_ON_FAIL:
                raise SystemExit(f"stage {st}: the geometry in {out} is not a current, passed stage 1 ({why}); run --stage geometry")
        before = {f: os.path.getmtime(os.path.join(out, f)) if os.path.exists(os.path.join(out, f)) else None for f in STAGE_FILES[st]}
        rc = {"geometry": stage_geometry, "ghosts": stage_ghosts, "scenery": stage_scenery}[st](cfg, out, a.no_logger)
        wrote = any(os.path.exists(os.path.join(out, f)) and os.path.getmtime(os.path.join(out, f)) != before[f] for f in STAGE_FILES[st])
        if wrote or rc == 0:
            write_record(cfg, out, st, rc == 0, a.no_logger)
        if rc:
            failed.append(st)
            if not WRITE_ON_FAIL:
                return rc
    if failed:
        log(f"\nFAILED stages: {failed} (outputs written for diagnosis only: --write-on-fail; not publishable)")
        return 1
    if a.publish:
        # only a complete package whose three stage records passed with this config and are current (no output changed
        # since, every stage consumed the current geometry); copied to a temporary folder, then swapped in
        for st in ("geometry", "ghosts", "scenery"):
            ok, why = record_ok(cfg, out, st, a.no_logger)
            if not ok:
                raise SystemExit(f"--publish refused: {why}")
        files = ("track.json", "heightfield.bin", "ortho.jpg", "ghosts.json", "scenery.json", "far_heightfield.bin", "far_ortho.jpg")
        missing = [f for f in files if not os.path.exists(os.path.join(out, f))]
        if missing:
            raise SystemExit(f"--publish refused: package incomplete, missing {missing}")
        if os.path.exists(os.path.join(pub, "track.json")) and not a.overwrite_package:
            raise SystemExit(f"{pub} exists: pass --overwrite-package to replace it")
        tmp = pub + ".publishing"
        shutil.rmtree(tmp, ignore_errors=True)
        os.makedirs(tmp)
        for f in files:
            shutil.copyfile(os.path.join(out, f), os.path.join(tmp, f))
        old_dir = pub + ".previous"
        shutil.rmtree(old_dir, ignore_errors=True)
        if os.path.exists(pub):
            os.rename(pub, old_dir)
        os.rename(tmp, pub)
        shutil.rmtree(old_dir, ignore_errors=True)
        log(f"published {pub}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
