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
# stage 3 also reads terrain_override (the regions it writes to scenery.json and drapes the paved parts on); hashed only
# when present, so every other track's scenery hash is unchanged


def config_id(cfg, stage="geometry"):
    """hash of the config keys a stage reads (geometry: everything but the ghosts, scenery, pit_lane and app blocks), so
    a scenery edit does not invalidate a passed geometry stage (pit_lane, 21 Oct 2026, is read by stage 3 only). Stage 1
    reads none of the left-out keys: since 20 Oct 2026 its pit merge takes centre.pit_exit, not the scenery builder's
    barriers / pit-exit cones (test_pit_merge.py)"""
    import hashlib
    if stage == "geometry":
        d = {k: v for k, v in cfg.items() if k not in ("ghosts", "scenery", "pit_lane", "app", "structures")}
        if (cfg.get("spline") or {}).get("owner_edges"):
            # the owner's traced edge files are stage-1 evidence: their content enters the hash (absent: hash unchanged)
            d["_owner_files"] = {w["file"]: hashlib.sha256(open(os.path.join(HERE, "tracks", cfg["id"], w["file"]), "rb").read()).hexdigest()
                                 for w in cfg["spline"]["owner_edges"]}
            if cfg["spline"].get("owner_mouths"):   # the mouth segments the owner gates leave out
                mf = cfg["spline"]["owner_mouths"]
                d["_owner_files"][mf] = hashlib.sha256(open(os.path.join(HERE, "tracks", cfg["id"], mf), "rb").read()).hexdigest()
    else:
        d = {k: cfg.get(k) for k in STAGE_KEYS[stage]}
        if stage == "scenery" and cfg.get("structures"):   # the buildings round's section (absent: hash unchanged)
            d["structures"] = cfg["structures"]
        if stage == "scenery" and cfg.get("terrain_override"):   # round 14A (absent: hash unchanged)
            d["terrain_override"] = cfg["terrain_override"]
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
FIT_DUMP_DIR = '.'
OWNER_REPORT = []
OWNER_REF_REPORT = {}
_OWNER_CACHE = {}


def _overlaps(a, b, n):
    """two station ranges (lo, hi) on a loop of n stations share a station"""
    sa = {k % n for k in range(a[0], a[1] + (n if a[1] < a[0] else 0) + 1)}
    return any(k % n in sa for k in range(b[0], b[1] + (n if b[1] < b[0] else 0) + 1))


def owner_windows(cfg_raw, cfgw, window=None, phase=None, n=None, measure=False):
    """spline.owner_edges on this centre's stations (cfgw remapped): per window and side {side, lo, hi, pts (world xy),
    chains, kerb_inside [(lo, hi[, shift])], kerb_w, file}; the JSON (compare/owner_edges.py / owner_merge.py) is read
    from tracks/<id>/ (Buttonwillow 21 Oct 2026). Sonoma round 14B: an entry with local=True is used only in the local
    refits (phase 'local') whose `window` (remapped stations) it overlaps; phase 'global' leaves it out; phase None
    (the gates) takes every entry."""
    out = []
    kw = float((cfg_raw["scenery"].get("kerb") or {}).get("width", 0.9))
    for w in cfgw["spline"].get("owner_edges") or []:
        if phase == "global" and w.get("local"):
            continue
        if phase == "local" and w.get("local") and not _overlaps((int(w["lo"]), int(w["hi"])), tuple(window), n):
            continue
        path = os.path.join(HERE, "tracks", cfg_raw["id"], w["file"])
        if path not in _OWNER_CACHE:
            _OWNER_CACHE[path] = json.load(open(path))
        d = _OWNER_CACHE[path]
        # chains (Buttonwillow): his lines re-assigned to the current centre's side; chains=False (Sonoma round 14B part
        # 1b, the merged file's sides read on the 14B centre): the file's side labels as they are (at T9A his two lines
        # came within the 3 m link of each other and one chain took both sides)
        chains = (edges_spline.owner_chains([[x, y] for side in ("left", "right") for x, y, *_ in d[side + "_enu_xys"]])
                  if w.get("chains", True) else None)
        for side in ("left", "right"):
            pts = np.array([[x, y] for x, y, *_ in d[side + "_enu_xys"]], float)
            out.append({"side": side, "lo": int(w["lo"]), "hi": int(w["hi"]), "pts": pts, "chains": chains, "file": w["file"], "kerb_w": kw,
                        "kerb_inside": [(lo, hi) + tuple(rest[:1]) for sd, lo, hi, *rest in w.get("kerb_inside", []) if sd == side],
                        "windows": w.get("windows") or [], "kerb_ramp": cfgw["spline"].get("kerb_ramp"),
                        "reach": w.get("reach"),
                        # measure=True (the gates): spline.owner_measure 'foot' reads every window's line at the foot of
                        # its normals (edges_spline.foot_project), so re-stationing the lap cannot move the owner statistics
                        # (Sonoma round 14B part 1b: T1's edges within 3 mm of part 1 read 0.285 / 0.369 m by station)
                        "project": "foot" if (measure and cfgw["spline"].get("owner_measure") == "foot") else w.get("project")})
    return out


def refine_zones(cfgw, window, n, C=None):
    """spline.refine on this centre's stations (cfgw remapped): the zones overlapping a local refit's window.
    (lo, hi, knot[, mult[, side[, [(enu_a, enu_b, mult_in), ...]]]]): mult scales the zone's fine-layer penalty, side
    limits it to one edge, and each sub-range (two world points on the centre, resolved here on C as the nearest stations:
    config stations map poorly where the centre has moved metres, as at T9A) takes the penalty mult_in"""
    from scipy.spatial import cKDTree
    out = []
    for lo, hi, h, *rest in (cfgw["spline"].get("refine") or []):
        if window is None or not _overlaps((int(lo), int(hi)), tuple(window), n):
            continue
        r_ = [v if isinstance(v, str) else float(v) for v in rest[:2]]
        if len(rest) > 2 and C is not None:
            kd = cKDTree(np.asarray(C)[:, :2])
            r_.append([(int(kd.query(a)[1]), int(kd.query(b)[1]), float(m)) for a, b, m in rest[2]])
        out.append((int(lo), int(hi), float(h)) + tuple(r_))
    return out


def owner_ref(cfg_raw, cfgw, C, n):
    """The owner's reference on centre C (edge_gate.owner_reference; Buttonwillow round 10): his readings per side
    over every spline.owner_edges window (kerb shifts included, as the fit takes them), and his red across the mouths
    of spline.owner_mouths (the 'red across' segments of compare/owner_mouths.py's file, world points)."""
    C = np.asarray(C, float)[:, :2]
    NL = B.left_normals(C)
    rd = {"left": {}, "right": {}}
    for w in owner_windows(cfg_raw, cfgw, measure=True):
        r = edges_spline.owner_readings(C, NL, w, n)
        for k, v in r.items():
            if (k - w["lo"]) % n <= (w["hi"] - w["lo"]) % n:
                rd[w["side"]][k] = v
    lines = []
    mf = cfg_raw["spline"].get("owner_mouths")
    if mf:
        M = json.load(open(os.path.join(HERE, "tracks", cfg_raw["id"], mf)))
        # his red across a mouth, and (Sonoma round 14B) a junction step: his red ending on one line and resuming on
        # another where a lane joins (the pit-exit mouth); both left out of the station gates +-corner
        lines = [(m["side"], np.array(m["line_enu"], float)) for m in M["mouths"]
                 if (m.get("kind") == "red across" and m.get("red_drawn", True)) or m.get("kind") == "junction step"]
    return edge_gate.owner_reference(C, rd, lines, n)


def pit_merge_inputs(cfg, trk, osm):
    """The pit merge's inputs on the provisional track `trk` from stage-1 keys and evidence only (20 Oct 2026): the
    pit-lane parts from the OSM pit_lane_way and the NAIP (build_scenery.pit_lane), and the pit-exit blend line from
    config centre.pit_exit (build_scenery.pit_exit_line: its measured line, or the detected one after its measured
    wall end). No scenery or pit_lane key is read, so config_id('geometry') covers them (test_pit_merge.py). Under
    `reproduce`, pit_exit_wall_end_latlon replaces the wall end (Laguna's accepted build took it from the stage-3
    pit-wall rule). Returns (pit, line)."""
    import build_scenery as BS
    pe = dict(cfg["centre"].get("pit_exit") or {})
    if REPRO.get("pit_exit_wall_end_latlon") is not None:
        pe["wall_end_latlon"] = REPRO["pit_exit_wall_end_latlon"]
        log(f"pit-exit wall end from config reproduce: {pe['wall_end_latlon']}")
    pit = BS.pit_lane(trk, osm)
    return pit, BS.pit_exit_line(trk, pit, pe)


def stage_geometry(cfg, out, no_logger):
    t0 = time.time()
    work = os.path.join(out, "work")
    os.makedirs(work, exist_ok=True)
    global FIT_DUMP_DIR
    FIT_DUMP_DIR = work
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
        if cen.get("prior_shift"):
            # where the OSM way runs on a paved apron, the first centre is moved onto the circuit's pavement by the
            # shift measured on the captures (config centre.prior_shift; SKILL 1.2), before the NAIP edges and the fit
            C, L = B.prior_shift(C, cen["prior_shift"], cfg.enu, log)
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
    BS.configure_geometry(cfg, work)   # stage-1 keys only: nothing here reads the scenery or pit_lane sections
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
    prof_v2, res_v2 = V2.profile(C, hl, hr, dem_s, z0, cfg["repave_fixes"], profile_gaps=cfg.get("profile_gaps"))
    hf_v2, nx, ny = V2.heightfield(box, dem, z0, C, hl, hr, res_v2)
    if cfg.get("profile_gaps"):
        import profile_gap
        gap_wins = profile_gap.windows(C, cfg["profile_gaps"], cfg.enu)
        hf_v2 = profile_gap.heightfield(hf_v2, box, B.HF_DX, C, hl, hr, prof_v2, gap_wins)
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
    BS.configure_geometry(cfg, v2dir)
    trk = BS.Track(T_v2, hf_v2)
    osm = BS.Osm()
    pit, cones = pit_merge_inputs(cfg, trk, osm)
    # the pit-wall polyline of a straight fitted to the pit wall (fit 'pitwall'): the OSM rule wall, no scenery key
    pw = BS.pit_wall_line(trk, osm) if any(s_.get("fit") == "pitwall" for s_ in cfg["straights"]) else None
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
        prof0, resurface = V2.profile(C1, hl1, hr1, dem_s, z0, cfg["repave_fixes"], profile_gaps=cfg.get("profile_gaps"))
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
            cfg_raw, cfg, C, hl, hr, C1, hl1, hr1, fit, trk, osm, pw, merge, pfa, pfb, cen, cc, dem_s, z0, rep)
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
    if cfg.get("profile_gaps"):
        import profile_gap
        wins = profile_gap.windows(C1, cfg["profile_gaps"], cfg.enu)
        hf = profile_gap.heightfield(hf, box, B.HF_DX, C1, hl3, hr3, prof, wins)
        notes["profile_gaps"] = cfg["profile_gaps"]
    # -- terrain override (config terrain_override, round 14A): inside a declared region the heightfield is one smooth
    # surface continuing the course as written to track.json (the physics' own arrays), robust to the lidar beyond it;
    # absent (every other track): the heightfield untouched. track.json is not changed by it.
    over_rep = []
    if cfg.get("terrain_override"):
        import terrain_override as TOV
        Ct, Lt, Rt = (np.array(T[k])[:, :2] for k in ("center", "left", "right"))
        hlt = np.maximum(np.linalg.norm(Lt - Ct, axis=1), 0.5)
        hrt = np.maximum(np.linalg.norm(Rt - Ct, axis=1), 0.5)
        hf, over_rep = TOV.apply(hf, box, B.HF_DX, cfg["terrain_override"], cfg.enu, Ct, hlt, hrt, np.array(T["profile"]["z"]),
                                 T["profile"]["fractions"], log=log, points=V2.LIDAR_POINTS, z0=z0,
                                 track=(T["center"], T["left"], T["right"]))
        hf = hf.astype("<f4")
    # -- validation
    lc = cfg["loop_check"]
    rep.check("loop stations", lc["n_min"] <= n <= lc["n_max"], f"n = {n}")
    if not lc.get("official_m"):
        log(f"     lap length: {L1:.2f} m (no official figure in the config: loop_check.official_m is None)")
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
    # declared junction corners (gate.continuity_exemptions, Sonoma round 14B part 1b): left out here and reported with
    # the world-continuity gate as "exempt (junction corner)" with their measured values (edge_gate); absent: unchanged
    exl = np.array(sorted(edge_gate.exempt_stations(cfg["gate"], "left", n, C1, (1, 0))), int)
    exr = np.array(sorted(edge_gate.exempt_stations(cfg["gate"], "right", n, C1, (1, 0))), int)
    if len(exl) or len(exr):
        log(f"     edge jumps: declared junction corners left out (left {len(exl)}, right {len(exr)} stations): there left "
            f"{(dl[exl].max() if len(exl) else 0):.3f} m, right {(dr[exr].max() if len(exr) else 0):.3f} m (exempt, reported)")
        dl = dl.copy(); dr = dr.copy(); dl[exl] = 0.0; dr[exr] = 0.0
    rep.check("edge jumps", max(dl.max(), dr.max()) <= V2.EDGE_JUMP, f"max lateral change between stations: left {dl.max():.3f} m, right {dr.max():.3f} m"
              + (" outside the declared junction corners" if len(exl) or len(exr) else ""))
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
    if cfg_raw["spline"].get("width_model"):
        # the width gates (Buttonwillow round 9, REQUIRED with a width model): one width per section, no 20-80 m wave
        cw_ = trackcfg.remap_stations(cfg_raw, n, L1, C=C1)
        oref = owner_ref(cfg_raw, cw_, C1, n) if (cfg_raw["spline"].get("owner_edges") and cfg_raw["spline"].get("owner_mouths")) else None
        met["width"], gf = edge_gate.width_gates(T, cw_["spline"]["width_model"]["junctions"], cfg_raw["gate"], log=log, owner=oref)
        if oref is not None:
            met["owner_reference"] = OWNER_REF_REPORT
        rep.fails += gf
        json.dump(WIDTH_REPORT, open(os.path.join(work, "width_model_report.json"), "w"), default=float)
    elif cfg_raw["spline"].get("owner_edges") and cfg_raw["spline"].get("owner_mouths"):
        # no width model: the owner's reference gates on the package as written (Sonoma round 14B, decision d14; edge_gate.owner_gates):
        # the width against the width between his lines, the 20-80 m band of (fit - his red)
        Ct_ = np.array(T["center"])[:, :2]
        cw_ = trackcfg.remap_stations(cfg_raw, n, L1, C=Ct_)
        met["owner"], gf = edge_gate.owner_gates(T, owner_ref(cfg_raw, cw_, Ct_, n), cfg_raw["gate"], log=log)
        met["owner_reference"] = dict(OWNER_REF_REPORT)
        rep.fails += gf
    w = hl3 + hr3
    log(f"     width: median {np.median(w):.1f} m (p5 {np.percentile(w, 5):.1f}, p95 {np.percentile(w, 95):.1f}); corners: "
        + ", ".join(f"{c['turn'] or c['name']} s={c['s']} R={c['radius_m']}" for c in corners))
    if cfg["spline"].get("report_by_kind"):
        # report only (no gate): the width against the operator's figure (config spline.report_width = (lo, hi) m)
        lo_w, hi_w = cfg["spline"].get("report_width", (0.0, 1e9)); k0 = int(np.argmin(w))
        log(f"     report width: median {np.median(w):.2f} m, p10 {np.percentile(w, 10):.2f}, p90 {np.percentile(w, 90):.2f}, "
            f"min {w[k0]:.2f} m at station {k0}, max {w.max():.2f} m at station {int(np.argmax(w))}; "
            f"{np.mean(w < lo_w) * 100:.1f} % of stations under {lo_w} m, {np.mean(w > hi_w) * 100:.1f} % over {hi_w} m")
    report = {"provisional": {"shadow_stations": [int(v) for v in shadow], "cones": [cones["s0"], cones["s1"]] if cones else None,
                              "pit_parts": [p["track_s"] for p in (pit or {}).get("parts", [])]},
              "recentre": fit["report"], "spline": spline_rep, "straights": str_rep, "gate": met,
              "over_12pct": [int(i) for i in np.nonzero(cs.max(1) > B.CROSS_SOFT)[0]], "fails": rep.fails,
              **({"terrain_override": over_rep} if over_rep else {}),
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


WIDTH_REPORT = {}


def width_model_pass(cfg_raw, Ccur, hl1, hr1, tiles, features, sp_cfg, cc, pfa, pfb, cen, merge, fit_last, rep):
    """The width-prior edge model (width_model.py, config spline.width_model; Buttonwillow round 9): the evidence is
    gathered once around the converged fitted-method edges, in world coordinates; then, on every centre, the bias and
    the section widths are estimated, the edges placed (one width per section, the weaker side from the stronger) and
    fitted (edges_spline.fit_periodic with the corrected evidence as observations and the placement as constraints),
    and the centre refitted to their midpoint until it moves less than 5 cm."""
    import width_model as WM
    n = len(Ccur)
    spm = dict(sp_cfg, kerb_search=[])      # the evidence is the model's; no search zone reaches across it
    L0 = float(np.linalg.norm(np.roll(Ccur, -1, 0) - Ccur, axis=1).sum())
    cfgw = trackcfg.remap_stations(cfg_raw, n, L0, C=Ccur)
    wm = cfgw["spline"]["width_model"]
    hlp, hrp, hl3, hr3 = hl1.copy(), hr1.copy(), hl1.copy(), hr1.copy()
    # evidence passes (spline.width_model.evidence_passes): the detector's window follows the edge it searches around,
    # so after the first pass the evidence is read again around the placed edges and the model re-run on it
    for ep in range(int(wm.get("evidence_passes", 1))):
      ke = wm.get("kerb_expect", -0.45)
      wm_ep = dict(wm, kerb_expect=ke[min(ep, len(ke) - 1)] if isinstance(ke, (list, tuple)) else ke)   # where the band sits from the edge searched around
      ev = WM.gather_world(cfg_raw, Ccur, B.left_normals(Ccur), hl3, hr3, tiles, cc["mpp"], wm_ep, mask=cfgw["spline"].get("mask") or [], log=log)
      move = 1e9
      for it in range(40):
          L_ = float(np.linalg.norm(np.roll(Ccur, -1, 0) - Ccur, axis=1).sum())
          cfgw = trackcfg.remap_stations(cfg_raw, n, L_, C=Ccur)
          wm = cfgw["spline"]["width_model"]; J = wm["junctions"]
          NL = B.left_normals(Ccur)
          owner = owner_windows(cfg_raw, cfgw) if cfgw["spline"].get("owner_edges") else []
          spm["_owner"] = owner
          if cfgw["spline"].get("mask"):
              spm["mask"] = cfgw["spline"]["mask"]
          feats = [tuple(f[:4]) for f in cfgw["features"] if f[3] != "keep"]
          E = WM.station_evidence(Ccur, NL, ev, n, owner)
          jm, secs = WM.sections(n, J)
          est = WM.estimate(E, n, secs, jm, int(wm.get("min_obs", 15)), log=log, agree=float(wm.get("agree_conf", 0.6)))
          Ev = WM.corrected(E, est["bias"])
          w = WM.width_function(n, secs, est["W"], J, Ev, int(wm.get("local_half", 15)), int(wm.get("blend", 15)))
          mid, tl, tr, src = WM.targets(n, Ev, w, wm, WM.junction_side(n, J))
          obs = WM.observations(E, est["bias"], n)
          aw = float(wm.get("anchor_w", 20.0))
          anchors = {"left": (np.arange(n), tl, np.full(n, aw)), "right": (np.arange(n), tr, np.full(n, aw))}
          log(f"width model, evidence pass {ep + 1}, iteration {it + 1}: {len(secs)} sections, widths " + ", ".join(f"{a}-{b}: {W:.2f}" for (a, b), W in zip(secs, est["W"])))
          hl3, hr3, frep = edges_spline.fit_periodic(Ccur, NL, hlp, hrp, tiles, feats, spm, cc["mpp"], anchors, obs=obs, anchors_cover=False)
          if it >= 1 and move < 0.05:
              break
          P2 = {"lat_left": hl3, "lat_right": -hr3}
          fit2 = recentre.refit(Ccur, hlp, hrp, P2, [], [], None, None, pfa, pfb, 0, cen["gps_margin"], cen["min_width"],
                                merge=merge, width_cap=cen.get("width_cap", 16.0))
          Cn = fit2["C"]
          if it >= 2:
              alpha = 1.0 / it
              _, latc = B.project(Cn, Ccur)
              Cd = Ccur - alpha * latc[:, None] * B.left_normals(Ccur)
              Cn, _ = B.resample_closed(Cd, n=n, smooth=0.0)
          _, lat = B.project(Cn, Ccur)
          move = float(np.abs(lat).max())
          for side, hw in (("left", hl3), ("right", hr3)):
              sg = 1 if side == "left" else -1
              sq, lq = B.project(Cn, Ccur + sg * hw[:, None] * NL); o_ = np.argsort(sq)
              v = sg * np.interp(np.arange(n), sq[o_], lq[o_], period=n)
              if side == "left": hlp = v
              else: hrp = v
          fit_last = fit2
          log(f"width model: centre refit to the midpoint of the placed edges: max move {move:.3f} m at station {int(np.argmax(np.abs(lat)))}")
          Ccur = Cn
      else:
          rep.check("width model convergence", False, f"evidence pass {ep + 1}: centre still moving {move:.3f} m after 40 refits")
    # report (work/width_model_report.json; the outline page and the round's record read it)
    kd = {}
    for side, hw in (("left", hl3), ("right", hr3)):
        kb = E[side]["kerb"]; m = ~np.isnan(kb); d = np.where(m, hw - kb, np.nan)
        kd[side] = dict(stations=int(m.sum()), within_03=float(np.mean(np.abs(d[m]) <= 0.3)) if m.any() else None,
                        over=[(a, b) for a, b in edges_spline.ranges(m & (np.abs(np.nan_to_num(d)) > 0.3), n)],
                        max=float(np.nanmax(np.abs(d))) if m.any() else None)
    from collections import Counter
    WIDTH_REPORT.update(dict(bias=est["bias"], at_kerb=est["at_kerb"], kinds=est["kinds"], fallback=est["fallback"], lapW=est["lapW"],
                             sections=[dict(lo=int(a), hi=int(b), W=round(float(W), 2), obs=int(c), kinds=kk_)
                                       for (a, b), W, c, kk_ in zip(secs, est["W"], est["cnt"], est["kinds_by_sec"])],
                             junctions=[list(j[:4]) for j in J], src=dict(Counter(src.tolist())), kerb_disagree=kd,
                             width=[round(float(v), 3) for v in w], src_per_station=src.tolist(),
                             per_station={sd: dict(val=[None if np.isnan(v) else round(float(v), 3) for v in Ev[sd][0]], kind=Ev[sd][1].tolist(),
                                                   conf=[round(float(v), 2) for v in Ev[sd][2]]) for sd in ("left", "right")}))
    for side in ("left", "right"):
        log(f"width model: {side} edge vs the kerb anchors: {kd[side]['stations']} stations, {kd[side]['within_03'] * 100:.1f} % within 0.3 m, "
            f"max {kd[side]['max']:.2f} m; over 0.3 m at {kd[side]['over'][:12]}")
    log("width model: the stronger side per station: " + ", ".join(f"{k or 'none'} {v}" for k, v in sorted(WIDTH_REPORT["src"].items())))
    return Ccur, hlp, hrp, hl3, hr3, frep, fit_last, cfgw


def fitted_method(cfg_raw, cfg, C0, hl0, hr0, C1, hl1, hr1, fit, trk, osm, pw, merge, pfa, pfb, cen, cc, dem_s, z0, rep):
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
    def build_anchors(cfgw, Ccur, NL, hlp, hrp):
        """The constraints inside the fit (declared straights, measured shapes) and the fit's features."""
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
        return anchors, str_rep, features

    # centre.local (Sonoma round 11): converge first without the straights marked `local` (the accepted geometry), then
    # refit inside the window only (local_refit below)
    loc = cfg_raw["centre"].get("local")
    cfg_fit = cfg_raw
    if loc:
        import copy
        cfg_fit = copy.deepcopy(cfg_raw)
        cfg_fit["straights"] = [s_ for s_ in cfg_raw["straights"] if not s_.get("local")]
        # features carry an optional 6th element {local: True} (only in the local refit) or {replaced_by_local: True}
        # (only before it); the local refit's config has every straight and its own feature list
        fflag = lambda f, k: len(f) > 5 and isinstance(f[5], dict) and bool(f[5].get(k))  # noqa: E731
        cfg_fit["features"] = [f for f in cfg_raw["features"] if not fflag(f, "local")]
        cfg_loc = copy.deepcopy(cfg_raw)
        cfg_loc["features"] = [f for f in cfg_raw["features"] if not fflag(f, "replaced_by_local")]
    Ccur, hlp, hrp = C1, hl1.copy(), hr1.copy()
    fit_last = fit
    for it in range(40):
        cfgw = trackcfg.remap_stations(cfg_fit, n, float(np.linalg.norm(np.roll(Ccur, -1, 0) - Ccur, axis=1).sum()), C=Ccur)
        # the edge fit's masks and kerb-search zones on this centre's stations, as the features (Buttonwillow; absent: unchanged)
        for key_ in ("mask", "kerb_search"):
            if cfgw["spline"].get(key_):
                sp_cfg[key_] = cfgw["spline"][key_]
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
        anchors, str_rep, features = build_anchors(cfgw, Ccur, NL, hlp, hrp)
        if cfgw["spline"].get("owner_edges"):
            sp_cfg["_owner"] = owner_windows(cfg_raw, cfgw, phase="global" if loc else None, n=n)
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
            cfgw = trackcfg.remap_stations(cfg_fit, n, fit2["L"], C=Ccur)
            for key_ in ("mask", "kerb_search"):
                if cfgw["spline"].get(key_):
                    sp_cfg[key_] = cfgw["spline"][key_]
            ow_ = owner_windows(cfg_raw, cfgw, phase="global" if loc else None, n=n) if cfgw["spline"].get("owner_edges") else []
            if cfgw["spline"].get("kerb_search") or ow_:
                # the features on the same remap as the search zones (Buttonwillow round 5: with the T2 / T4 owner edges
                # the stations moved ~9 m and the loop's earlier features no longer matched the zone ends at 1921-1939);
                # owner windows used only in a local refit (Sonoma round 14B) do not count here
                features = [tuple(f[:4]) for f in cfgw["features"] if f[3] != "keep"]
            if cfgw["spline"].get("owner_edges"):
                sp_cfg["_owner"] = ow_
            hl3, hr3, frep = edges_spline.fit_periodic(Ccur, NL, hlp, hrp, tiles, features, sp_cfg, cc["mpp"],
                                                       {k: v for k, v in anchors.items() if v[0]})
            log(f"converged after {it + 1} centre refits")
            break
    else:
        rep.check("centre convergence", False, f"centre still moving {move:.3f} m after 40 refits")
    if sp_cfg.get("width_model") and not cfg_raw.logger:
        Ccur, hlp, hrp, hl3, hr3, frep, fit_last, cfgw = width_model_pass(cfg_raw, Ccur, hl3, hr3, tiles, features, sp_cfg, cc,
                                                                          pfa, pfb, cen, merge, fit_last, rep)
    if loc:
        # -- the local refit (config centre.local): every straight (the `local` ones too) inside the window, the converged
        # geometry above held outside it in WORLD position. The centre moves only by the window weight (no re-stationing
        # inside the loop, so stations outside the window stay put); the edges are the fit inside, the held edges
        # outside, smoothstep-blended over `blend` stations inside each window end; the gates measure the returned edges.
        # A list of windows (Sonoma round 14B) runs one local refit per window in order, each holding everything outside
        # its window at the result of the one before; the first is exactly the single-window refit.
        locs = loc if isinstance(loc, list) else [loc]

        def on_centre(Cx, Wp, sg):
            sq, lq = B.project(Cx, Wp); o_ = np.argsort(sq)
            return sg * np.interp(np.arange(len(Cx)), sq[o_], lq[o_], period=len(Cx))

        def lwin(cfgw, li):
            lc_ = cfgw["centre"]["local"]
            return (lc_[li] if isinstance(lc_, list) else lc_)["window"]

        def weights(cfgw, li):
            lo, hi = lwin(cfgw, li); bl = int(locs[li].get("blend", 15)); span = (hi - lo) % n
            w = np.zeros(n)
            for j in range(span + 1):
                t = min(1.0, min(j, span - j) / bl); w[(lo + j) % n] = t * t * (3 - 2 * t)
            return w

        def set_owner(cfgw, li):
            for key_ in ("mask", "kerb_search"):   # Buttonwillow's keys, on this centre's stations (absent: unchanged)
                if cfgw["spline"].get(key_):
                    sp_cfg[key_] = cfgw["spline"][key_]
            if cfgw["spline"].get("owner_edges"):
                sp_cfg["_owner"] = owner_windows(cfg_raw, cfgw, window=lwin(cfgw, li), phase="local", n=n)
            if cfgw["spline"].get("refine"):
                sp_cfg["_refine"] = refine_zones(cfgw, lwin(cfgw, li), n, Ccur)
            if cfgw["gate"].get("continuity_exemptions"):
                # the declared steps in his red (kind 'step') inside this local window (edges_spline.step_profile)
                sp_cfg["_steps"] = [(e["side"], e["lo"], e["hi"]) for e in edge_gate.exemptions(cfgw["gate"], Ccur)
                                    if e.get("kind") == "step" and _overlaps((e["lo"], e["hi"]), tuple(lwin(cfgw, li)), n)]
        for li, lc in enumerate(locs):
            NLa = B.left_normals(Ccur)
            held = {"left": (Ccur + hl3[:, None] * NLa, 1), "right": (Ccur - hr3[:, None] * NLa, -1)}
            held_prior = {"left": (Ccur + hlp[:, None] * NLa, 1), "right": (Ccur - hrp[:, None] * NLa, -1)}   # the profile's edges
            Ca = Ccur.copy()

            hl_a, hr_a = hl3.copy(), hr3.copy()

            def hold_for(Cx, cfgw):
                w_ = weights(cfgw, li)
                hl_, hr_ = on_centre(Cx, *held["left"]), on_centre(Cx, *held["right"])
                if cen.get("restation") == "index":
                    # Sonoma round 14B part 1b: outside the window (weight 0) the loop never moves the centre or its stations,
                    # so the held edges there ARE the half-widths the window started with; re-projecting their world points
                    # moved the T9A arc 0.15-0.24 m during the next window's refit (10 m out on a tight corner)
                    hl_ = np.where(w_ > 0, hl_, hl_a); hr_ = np.where(w_ > 0, hr_, hr_a)
                return {"w": w_, "left": hl_, "right": hr_}
            log(f"local refit (centre.local, {lc.get('why', '')[:80]}): window {lc['window']} "
                f"(config stations), blend {lc.get('blend', 15)}")
            for jt in range(40):
                Lc = float(np.linalg.norm(np.roll(Ccur, -1, 0) - Ccur, axis=1).sum())
                cfgw = trackcfg.remap_stations(cfg_loc, n, Lc, C=Ccur)
                NL = B.left_normals(Ccur)
                hold = hold_for(Ccur, cfgw)
                anchors, str_rep, features = build_anchors(cfgw, Ccur, NL, hlp, hrp)
                set_owner(cfgw, li)
                hl3, hr3, frep = edges_spline.fit_periodic(Ccur, NL, hlp, hrp, tiles, features, sp_cfg, cc["mpp"],
                                                           {k: v for k, v in anchors.items() if v[0]}, hold=hold)
                fit2 = recentre.refit(Ccur, hlp, hrp, {"lat_left": hl3, "lat_right": -hr3}, [], [], None, None, pfa, pfb, 0,
                                      cen["gps_margin"], cen["min_width"], merge=merge, width_cap=cen.get("width_cap", 16.0))
                alpha = 1.0 if jt < 2 else 1.0 / jt
                _, latc = B.project(fit2["C"], Ccur)
                dm = alpha * hold["w"] * latc
                Cn = Ccur - dm[:, None] * NL
                move = float(np.abs(dm).max()); move_at = int(np.argmax(np.abs(dm)))
                hlp = on_centre(Cn, Ccur + hl3[:, None] * NL, 1); hrp = on_centre(Cn, Ccur - hr3[:, None] * NL, -1)
                fit_last = fit2; Ccur = Cn
                log(f"local refit {jt + 1}: centre max move {move:.3f} m at station {move_at}")
                if move < 0.05 and jt >= 1:
                    break
            else:
                rep.check("local refit convergence", False, f"window {lc['window']}: centre still moving {move:.3f} m after 40 local refits")
            # the final fit on the loop's own stations (outside the window they are the converged stations above, so the
            # held edges there are measured on exactly the observations the converged fit had); its metrics are the gates
            cfgw = trackcfg.remap_stations(cfg_loc, n, float(np.linalg.norm(np.roll(Ccur, -1, 0) - Ccur, axis=1).sum()), C=Ccur)
            NL = B.left_normals(Ccur)
            anchors, str_rep, features = build_anchors(cfgw, Ccur, NL, hlp, hrp)
            set_owner(cfgw, li)
            hl3, hr3, frep = edges_spline.fit_periodic(Ccur, NL, hlp, hrp, tiles, features, sp_cfg, cc["mpp"],
                                                       {k: v for k, v in anchors.items() if v[0]}, hold=hold_for(Ccur, cfgw))
            wf = weights(cfgw, li)
            hlp = wf * hlp + (1 - wf) * on_centre(Ccur, *held_prior["left"])
            hrp = wf * hrp + (1 - wf) * on_centre(Ccur, *held_prior["right"])
            # then uniform stations again (the contract's spacing L / n): the same centre curve and the same world edges,
            # re-expressed on the new stations (no refit)
            if lc.get("centre_smooth"):
                # Sonoma round 14B part 1b (centre.local window centre_smooth = sigma, stations): the window's centre
                # Gaussian-smoothed (inside the window by its weights) before the uniform re-stationing. The refit loop
                # leaves station-scale jitter in the centre's curvature (its own third difference 0.003 m) that the
                # normals carry 10-12 m out to the edge on the outside of T7a and T9A (0.03-0.04 m there); sigma 1 moves
                # the centre <= 0.03 m and takes it out. The edges are refitted on the result (refit_final); absent: unchanged
                from scipy.ndimage import gaussian_filter1d
                wsm = weights(cfgw, li)[:, None]
                Csm = np.c_[gaussian_filter1d(Ccur[:, 0], float(lc["centre_smooth"]), mode="wrap"),
                            gaussian_filter1d(Ccur[:, 1], float(lc["centre_smooth"]), mode="wrap")]
                Cs_ = Ccur + wsm * (Csm - Ccur)
                # outside the window (weight 0) the centre is unchanged and so are the half-widths (no re-projection)
                in_ = wsm[:, 0] > 0
                hl3, hr3, hlp, hrp = (np.where(in_, on_centre(Cs_, Ccur + sg_ * a_[:, None] * NL, sg_), a_)
                                      for a_, sg_ in ((hl3, 1), (hr3, -1), (hlp, 1), (hrp, -1)))
                Ccur = Cs_; NL = B.left_normals(Ccur)
            Cu, _ = B.resample_closed(Ccur, n=n, smooth=0.0)
            if cen.get("restation") == "index":
                # Sonoma round 14B part 1b (centre.restation 'index'): the uniform stations lie on the same centre curve, so
                # each new station takes the edge point at its own fractional OLD station (the edge polylines interpolated
                # along the station index), not the projection of the old edge points onto the new centre: 10 m out on
                # the outside of T9A that projection misplaces a point by up to a quarter station and, re-done by every
                # later window's re-stationing, put 0.2-0.5 m lags and kinks into the arc his red draws; absent: unchanged
                uq, _ = B.project(Ccur, Cu); NLu = B.left_normals(Cu)

                def at_u(a_, sg_):
                    W_ = Ccur + sg_ * a_[:, None] * NL; i0 = np.floor(uq).astype(int) % n; f_ = (uq - np.floor(uq))[:, None]
                    return sg_ * (((1 - f_) * W_[i0] + f_ * W_[(i0 + 1) % n] - Cu) * NLu).sum(1)
                hl3, hr3, hlp, hrp = (at_u(a_, sg_) for a_, sg_ in ((hl3, 1), (hr3, -1), (hlp, 1), (hrp, -1)))
            else:
                hl3, hr3, hlp, hrp = (on_centre(Cu, Ccur + sg_ * a_[:, None] * NL, sg_) for a_, sg_ in ((hl3, 1), (hr3, -1), (hlp, 1), (hrp, -1)))
            Ccur = Cu
            cfgw = trackcfg.remap_stations(cfg_loc, n, float(np.linalg.norm(np.roll(Ccur, -1, 0) - Ccur, axis=1).sum()), C=Ccur)
            if lc.get("refit_final"):
                # Sonoma round 14B part 1b (centre.local window refit_final=True): the window's last fit on the uniform
                # stations themselves. Re-expressing the fitted edge on the re-spaced stations (linear in the projected
                # station) spread his hairpin jog over two stations and, 10 m out on the outside of T9A, put kinks of
                # 0.1-0.2 m into the arc across the escape road's mouth; absent: unchanged
                NL = B.left_normals(Ccur)
                anchors, str_rep, features = build_anchors(cfgw, Ccur, NL, hlp, hrp)
                set_owner(cfgw, li)
                hold_f = {"w": weights(cfgw, li), "left": on_centre(Ccur, *held["left"]), "right": on_centre(Ccur, *held["right"])}
                if cen.get("restation") == "index":
                    # outside the window: the held edges re-stationed along the index with the rest (hl3 / hr3 here)
                    hold_f["left"] = np.where(hold_f["w"] > 0, hold_f["left"], hl3); hold_f["right"] = np.where(hold_f["w"] > 0, hold_f["right"], hr3)
                hl3, hr3, frep = edges_spline.fit_periodic(Ccur, NL, hlp, hrp, tiles, features, sp_cfg, cc["mpp"],
                                                           {k: v for k, v in anchors.items() if v[0]}, hold=hold_f)
                log("     final fit on the uniform stations (refit_final)")
            _, dC = B.project(Ca, Ccur)
            log(f"local refit done after {jt + 1} refits: centre moved up to {np.abs(dC).max():.3f} m (station {int(np.argmax(np.abs(dC)))})")
        if cfg_raw["spline"].get("owner_edges"):
            # Sonoma round 14B part 1b: the fit gates' MEASUREMENT on the returned edges with the whole evidence. The last
            # local refit's metrics held only its own window's owner lines (set_owner), so the capture rows inside the
            # other owner windows were measured against his red there (the T7 road left read 50 %); and they were taken
            # before the final re-stationing. Here one more fit_periodic pass with hold weight 0 everywhere (it returns
            # the held edges exactly; its fit is discarded) measures the published edges on the published stations with
            # every owner window in place: his reading replaces the capture rows where he drew, as in the single-window
            # refit of part 1. The geometry is not touched (hl3 / hr3 stay as they are).
            cfgm = trackcfg.remap_stations(cfg_loc, n, float(np.linalg.norm(np.roll(Ccur, -1, 0) - Ccur, axis=1).sum()), C=Ccur)
            NLm = B.left_normals(Ccur)
            am_, _, fm_ = build_anchors(cfgm, Ccur, NLm, hlp, hrp)
            sp_cfg["_owner"] = owner_windows(cfg_raw, cfgm, n=n)
            sp_cfg["_refine"] = []
            sp_cfg["_steps"] = []
            _, _, frep = edges_spline.fit_periodic(Ccur, NLm, hlp, hrp, tiles, fm_, sp_cfg, cc["mpp"],
                                                   {k: v for k, v in am_.items() if v[0]},
                                                   hold={"w": np.zeros(n), "left": hl3, "right": hr3})
            log("fit gates measured on the returned edges with every owner window (hold weight 0; geometry unchanged)")
    seg = np.linalg.norm(np.roll(Ccur, -1, 0) - Ccur, axis=1); L = float(seg.sum()); sp = L / n
    # -- gates of the fitted method (edge_gate.FITTED; a config may tighten them, never loosen)
    G = edge_gate.fitted_thresholds(cfg_raw["gate"])
    # the owner's traced edges (spline.owner_edges): the fitted edge follows his reading in every window (Buttonwillow
    # 21 Oct 2026); with spline.owner_mouths, his reference (edge_gate.OWNER_REF, Buttonwillow round 10, Sonoma round 14B
    # decision d14): the max per station taken outside his mouth segments +-12, the 0.40 m station gate, the width and
    # the 20-80 m band of (fit - red) against his lines, the rolling waviness held to his red's own
    OREF = None
    if cfg_raw["spline"].get("owner_edges"):
        NLf = B.left_normals(Ccur)
        cfg_o = trackcfg.remap_stations(cfg_raw, n, float(np.linalg.norm(np.roll(Ccur, -1, 0) - Ccur, axis=1).sum()), C=Ccur)
        if cfg_raw["spline"].get("owner_mouths"):
            OREF = owner_ref(cfg_raw, cfg_o, Ccur, n)
        for w in owner_windows(cfg_raw, cfg_o, n=n, measure=True):
            r = edges_spline.owner_readings(Ccur, NLf, w, n)
            hw = hl3 if w["side"] == "left" else hr3
            ks_ = [k for k in r if (k - w["lo"]) % n <= (w["hi"] - w["lo"]) % n]
            if not ks_:
                # round 14B part 1b: he drew only the other side in this window (w_s0500: the right edge): no owner edge on
                # this side here, the detected edge stands and its gates are the ordinary ones
                log(f"     owner edge {w['side']} {w['lo']}-{w['hi']}: none drawn on this side (the detected edge stands)"); continue
            res = np.array([hw[k] - r[k] for k in ks_])
            a_st = np.abs(res); share_st = float(np.mean(a_st <= G["owner_tol"]))
            # round 14B part 1b: the SHARE is measured geometrically: each fitted edge point's distance to his line (his
            # readings, kerb shifts included, as one world polyline densified to 0.1 m, broken where his readings are more
            # than 3 stations apart), so re-stationing the lap cannot move it (station-based it read 92.3 % on T1 in part 1
            # and 89.8 % in 6784bcc on T1 edges that had not moved). Over every station of the window, his mouth segments
            # included, as before. The max (and edge_gate.owner_station_gate's 0.40 m cap) stay station-based; the
            # geometric max is printed beside them.
            sg_ = 1 if w["side"] == "left" else -1
            kk_ = np.array(sorted(r))
            Rw = Ccur[kk_] + sg_ * np.array([r[k] for k in kk_])[:, None] * NLf[kk_]
            segs_ = np.split(np.arange(len(kk_)), np.flatnonzero(np.diff(kk_) > 3) + 1)
            tt_ = np.linspace(0, 1, 10, endpoint=False)[None, :, None]
            dens = np.concatenate([(Rw[g_][:-1, None, :] + (Rw[g_][1:] - Rw[g_][:-1])[:, None, :] * tt_).reshape(-1, 2)
                                   for g_ in segs_ if len(g_) > 1] + [Rw])
            from scipy.spatial import cKDTree as _KD
            Fw = Ccur[np.array(ks_)] + sg_ * np.array([hw[k] for k in ks_])[:, None] * NLf[np.array(ks_)]
            a_geo = _KD(dens).query(Fw)[0]
            share = float(np.mean(a_geo <= G["owner_tol"]))
            a_ = a_st
            OWNER_REPORT.append({"side": w["side"], "lo": w["lo"], "hi": w["hi"], "file": w["file"], "k": ks_, "owner": [r[k] for k in ks_],
                                 "fit": [float(hw[k]) for k in ks_], "dist_geo": [round(float(v), 4) for v in a_geo]})
            if OREF is not None:
                keep = np.array([not OREF["excl"][w["side"]][k] for k in ks_])
                amax = float(a_[keep].max()) if keep.any() else 0.0
                gmax = float(a_geo[keep].max()) if keep.any() else 0.0
                # coordinator decision 1 (24 Oct 2026): the accepted gate design is Buttonwillow round 10's
                # (owner_station_gate on that branch): the cap AND the 0.25 m count are taken on the stations outside his
                # mouth segments +-corner; the all-stations share is printed beside it
                share_all = share
                share = float(np.mean(a_geo[keep] <= G["owner_tol"])) if keep.any() else share
                txt = (f" (share and max outside his {int((~keep).sum())} mouth-segment stations +-{edge_gate.OWNER_REF['corner']}; with them "
                       f"{share_all * 100:.1f} % / {a_.max():.3f}; station-based share {share_st * 100:.1f} %; geometric max {gmax:.3f})")
            else:
                amax, txt = float(a_.max()), f" (station-based share {share_st * 100:.1f} %; geometric max {a_geo.max():.3f})"
            rep.check(f"owner edge {w['side']} {w['lo']}-{w['hi']}", share >= G["owner_within"] and amax <= G["owner_max"],
                      f"{len(ks_)} stations ({w['file']}): {share * 100:.1f} % within {G['owner_tol']} m of the owner's line (>= {G['owner_within'] * 100:.0f} %), "
                      f"|residual| p50 {np.median(a_):.3f} / p90 {np.percentile(a_, 90):.3f} / max {amax:.3f} m (<= {G['owner_max']}){txt}")
            # per drawing window (Sonoma round 14B; printed, not gated: the gate is the config window above, as Buttonwillow
            # round 10's): the stations each of his drawn windows covered (its own owner_edges.py JSON, on this centre)
            for wf_ in w["windows"]:
                J_ = json.load(open(os.path.join(HERE, "tracks", cfg_raw["id"], wf_)))
                P_ = np.array([[x, y] for x, y, *_ in J_[w["side"] + "_enu_xys"]], float)
                if not len(P_):
                    continue
                kk_ = sorted({int(k) for k in B.project(Ccur, P_)[0].round().astype(int) % n} & set(ks_))
                if not kk_:
                    continue
                aw_ = np.abs(np.array([hw[k] - r[k] for k in kk_])); sh_ = float(np.mean(aw_ <= G["owner_tol"]))
                gi_ = {k: i for i, k in enumerate(ks_)}; ag_ = a_geo[[gi_[k] for k in kk_]]
                xm_ = np.array([bool(OREF["excl"][w["side"]][k]) for k in kk_]) if OREF is not None else np.zeros(len(kk_), bool)
                sh2_ = float(np.mean(aw_[~xm_] <= G["owner_tol"])) if (~xm_).any() else float("nan")
                log(f"     report owner edge {w['side']} window {os.path.basename(wf_)[:-5]} (not gated; the gate is the config window): "
                    f"{len(kk_)} stations {kk_[0]}-{kk_[-1]}: {sh_ * 100:.1f} % within {G['owner_tol']} m of his line, max {aw_.max():.3f} m; "
                    f"geometric {np.mean(ag_ <= G['owner_tol']) * 100:.1f} %, max {ag_.max():.3f} m; outside his mouth segments +-{edge_gate.OWNER_REF['corner']} ({int((~xm_).sum())} stations) {sh2_ * 100:.1f} %")
        json.dump(OWNER_REPORT, open(os.path.join(FIT_DUMP_DIR, "owner_edges_report.json"), "w"))
        if OREF is not None:
            om, of_ = edge_gate.owner_station_gate(hl3, hr3, OREF, cfg_raw["gate"], log=log)
            for f_ in of_:
                rep.check(f_, False, "see the line above")
            OWNER_REF_REPORT.update(om)
    for side in ("left", "right"):
        r = frep[side]
        # the declared junctions (config gate.exempt, pit-lane joins) are excluded from the waviness and kink metrics as
        # from the step metric; observation share, coverage and gaps count everywhere
        for sd, lo, hi, *_ in cfgw["gate"].get("exempt", []):
            if sd == side:
                r["loose"][np.array([k % n for k in range(lo, hi + (n if hi < lo else 0) + 1)])] = False
        Gs = edge_gate.unpainted_thresholds(cfg_raw["gate"]) if r.get("unpainted") else G
        if r.get("unpainted"):
            # the owner's decision of 20 Oct 2026 (edge_gate.UNPAINTED; a side whose associated readings are mostly
            # asphalt_end): a bias gate over all its readings instead of the 0.25 m share
            bg = edge_gate.side_within_gate(r, n, G)["bias"]
            U_ = edge_gate.UNPAINTED; wb = bg["worst"]
            worst_txt = f"worst {wb[0]:+.3f} m at {wb[1]} ({wb[2]}..{wb[3]})" if wb else "no window"
            share_ae = sum(k == "asphalt_end" for k in r["assoc_kind"]) / max(1, len(r["assoc_kind"]))
            rep.check(f"fit {side}: unpainted bias", bg["ok"] and r["assoc_share"] >= G["assoc"],
                      f"unpainted side ({share_ae * 100:.0f} % of {len(r['assoc_kind'])} associated readings from asphalt_end, a majority); "
                      f"{bg['share'] * 100:.1f} % of {bg['windows']} {U_['window']}-station windows have a median residual within "
                      f"+-{U_['bias']} m (>= {U_['bias_windows'] * 100:.0f} %); {worst_txt}; "
                      f"{r['assoc_share'] * 100:.0f} % of capture rows have a band within 1.2 m (>= {G['assoc'] * 100:.0f} %); "
                      f"spread (printed, not gated): |residual| p10/p50/p90 {bg['spread']} m, {r['within_gated'] * 100:.1f} % within 0.25 m")
        else:
          rep.check(f"fit {side}: observations within 0.25 m", r["within_gated"] >= G["within"] and r["assoc_share"] >= G["assoc"],
                    f"{r['within_gated'] * 100:.1f} % of the associated observations (>= {G['within'] * 100:.0f} %, the skill's measure); "
                    f"{r['assoc_share'] * 100:.0f} % of capture rows have a band within 1.2 m (>= {G['assoc'] * 100:.0f} %); of those "
                    f"{r['within'] * 100:.1f} % within 0.25 m, the rest at 0.25-0.4/0.4-0.6/0.6-0.8/0.8-1.0/1.0-1.2 m: {r['off_hist']}; "
                    f"{r['within_all'] * 100:.0f} % of all rows")
        if r.get("unpainted") or cfg_raw["spline"].get("report_by_kind"):
            pk_ = edge_gate.per_kind_report(r["assoc_kind"], r["assoc_res"])
            log(f"     report {side} per evidence kind (not gated): " + "; ".join(
                f"{k_} {v['n']} readings ({v['share'] * 100:.0f} %), {v['within'] * 100:.1f} % within 0.25 m" for k_, v in pk_.items()))
        lo_ = r["loose"]
        # rolling waviness over the loose stations only (a junction or tight corner inside a 100-station window is left
        # out of that window's rms, not only the windows centred on it)
        roll = np.zeros(n)
        for k in range(n):
            w_ = np.arange(k - 50, k + 50) % n; m_ = lo_[w_]
            roll[k] = np.sqrt(np.mean(r["qq"][w_][m_] ** 2)) if m_.sum() >= 50 else 0.0
        r["roll"] = roll
        r["wave_rms"] = float(roll[lo_].max()); r["wave_peak"] = float(np.abs(r["qq"])[lo_].max()); r["kink"] = float(r["kinkv"][lo_].max())
        rep.check(f"fit {side}: coverage", r["covered"] >= Gs["covered"],
                  f"{r['covered'] * 100:.0f} % of stations (>= {Gs['covered'] * 100:.0f} %" + (", unpainted side)" if r.get("unpainted") else ")"))
        bad = [f"{a}..{b} ({ln} st)" for (a, b), ln in r["gaps"] if ln > G["gap"]]
        rep.check(f"fit {side}: longest gap", not bad, f"{r['longest_gap']} st at {r['gap_at']} (<= {G['gap']})"
                  + (f"; over: {', '.join(bad)}" if bad else ""))
        if OREF is not None and OREF["edge"][side].any():
            # Buttonwillow round 10 / Sonoma round 14B: on the stations of his edge the fit's waviness is held to his red's
            # own (edge_gate.owner_waviness); on the other stations exactly as before
            mo = OREF["edge"][side]
            ow = edge_gate.owner_waviness(r["qq"], roll, lo_, OREF[side], mo, n)
            wr = edges_spline.ranges(lo_ & ~mo & (roll > G["wave_rms"]), n) + edges_spline.ranges(ow["bad_roll"], n)
            pk = lo_ & ~mo & (np.abs(r["qq"]) > G["wave_peak"])
            pr = edges_spline.ranges(pk | ow["bad_peak"], n)
            el = lo_ & ~mo
            om_ = lo_ & mo
            rep.check(f"fit {side}: waviness", not wr and not pr,
                      f"on his {int(om_.sum())} loose stations of this edge: rolling-100 rms max {(roll[om_].max() if om_.any() else 0):.3f} m against his red's own "
                      f"(max {ow['red_roll_max']:.3f}; limit max({G['wave_rms']}, his)), peak {(np.abs(r['qq'])[om_].max() if om_.any() else 0):.3f} m (limit max({G['wave_peak']}, his)); "
                      f"elsewhere rms max {(roll[el].max() if el.any() else 0):.3f} m (<= {G['wave_rms']}), peak {(np.abs(r['qq'])[el].max() if el.any() else 0):.3f} m (<= {G['wave_peak']})"
                      + (f"; over at {(wr + pr)[:8]}: " + ", ".join(f"{a}: rms {roll[a]:.3f}/{ow['roll_limit'][a]:.3f} peak {abs(r['qq'][a]):.3f}/{ow['peak_limit'][a]:.3f}" for a, _ in (wr + pr)[:4]) if wr or pr else ""))
        else:
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
    prof0, resurface = V2.profile(Ccur, hlp, hrp, dem_s, z0, cfgw["repave_fixes"], profile_gaps=cfgw.get("profile_gaps"))
    prof = V2.reprofile(prof0, hlp, hrp, hl3, hr3)
    for s_ in ("left", "right"):
        # the associated readings (station, owner reading or capture, residual) for diagnosis (work/, not the package)
        json.dump({"n": n, "x": [int(v) for v in frep[s_]["assoc_x"]], "kind": [k_ or "painted" for k_ in frep[s_]["assoc_kind"]],
                   "owner": [bool(v) for v in frep[s_]["assoc_owner"]],
                   "res": [round(float(v), 3) for v in frep[s_]["assoc_res"]]}, open(os.path.join(FIT_DUMP_DIR, f"fit_assoc_{s_}.json"), "w"))
    spline_rep = [{k: v for k, v in frep[s_].items() if k not in ("roll", "qq", "kinkv", "loose", "assoc_x", "assoc_res", "assoc_kind", "assoc_owner")} | {"side": s_}
                  for s_ in ("left", "right")]
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
    cfg_raw = cfg   # the owner gates remap the raw config themselves (round 14B: remapping the remapped one moved them)
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
    ortho_ = (np.asarray(Image.open(os.path.join(tmp, "ortho.jpg")).convert("RGB")).astype(np.float32), T["ortho"])
    hm_ = T["heightfield"]
    hf_ = np.fromfile(os.path.join(tmp, "heightfield.bin"), np.float32).reshape(hm_["ny"], hm_["nx"])

    def ground_(x, y):   # bilinear on the heightfield (the lidar ground), for aprons that follow it
        gx = min(max((x - hm_["x0"]) / hm_["dx"], 0.0), hm_["nx"] - 1.001); gy = min(max((y - hm_["y0"]) / hm_["dx"], 0.0), hm_["ny"] - 1.001)
        i_, j_ = int(gx), int(gy); fx, fy = gx - i_, gy - j_
        return (hf_[j_, i_] * (1 - fx) * (1 - fy) + hf_[j_, i_ + 1] * fx * (1 - fy) + hf_[j_ + 1, i_] * (1 - fx) * fy
                + hf_[j_ + 1, i_ + 1] * fx * fy)
    scenery_post.run(T, SC, scfg, tiles, cfg["captures"]["mpp"], regs, ortho=ortho_, ground=ground_)
    if scfg.get("ortho_pave"):
        # round 13 part B (Sonoma owner note 135): the ground under a complex's paving retextured from the 2026 paving
        # mask, after the post steps so every paved zone is known (config-gated: other tracks unchanged)
        ctiles = [t for t in CAP.capture_list(cfg, "clean") if t["name"] not in cfg["captures"].get("exclude", [])]
        op_ = os.path.join(tmp, "ortho.jpg")
        arr_, npx_ = BS.ortho_pave(T, SC, scfg["ortho_pave"], np.asarray(Image.open(op_).convert("RGB")), ctiles,
                                   cfg["captures"]["mpp"], cfg.enu, log=log)
        Image.fromarray(arr_).save(op_, quality=84, optimize=True)
        log(f"ortho pave: {npx_} px retextured")
    if cfg.get("terrain_override"):
        # round 14A: the override regions go to scenery.json (the physics drops its shoulder blend there and puts the
        # paved parts on the heightfield) and the paved parts inside them are draped on it (config-gated)
        import terrain_override as TOV
        SC["terrain_override"] = TOV.scenery_regions(cfg["terrain_override"], cfg.enu, (T["center"], T["left"], T["right"]))
        TOV.drape_parts(SC, T, hf_, SC["terrain_override"], log=log)
    off_names = {r["name"] for r in scfg.get("closed_roads", []) if r.get("off_course")}
    if off_names:
        # round 14B (owner on T9A: "on the other side of its entry is an escape road ... If you go off, you get black
        # flagged"): a closed road marked off_course is paved and drivable (the physics keeps it paved) but not course:
        # its parts carry off_course, and the lap-validity checks count a car on it as off (src/physics/track.ts)
        nmark = 0
        for p_ in (SC.get("paved_zones") or {}).get("parts", []):
            if p_.get("turn") in off_names:
                p_["off_course"] = True; nmark += 1
        log(f"off-course paved parts: {nmark} ({', '.join(sorted(off_names))})")
    if scfg.get("marks_on_surface"):
        # round 14B (judge r14a: a closed road's painted edge buried under its draped zone): every ground mark's stored
        # height on the package's own driven surface (tools/track/gates/groundMarks.ts drapeMarks: paint lines `lift` m
        # up, cones, kerb lines and ground signs on it), after the terrain-override drape; config-gated (absent: unchanged)
        json.dump(SC, open(os.path.join(tmp, "scenery.json"), "w"), separators=(",", ":"))
        r_ = subprocess.run(["npx", "tsx", os.path.join(HERE, "drape_marks.ts"), tmp, str(scfg["marks_on_surface"].get("lift", 0.008))],
                            cwd=ROOT, capture_output=True, text=True)
        if r_.returncode != 0:
            raise SystemExit("drape_marks.ts failed: " + r_.stderr[-2000:])
        log(r_.stdout.strip())
        SC = json.load(open(os.path.join(tmp, "scenery.json")))
    rep = Report("SCENERY VALIDATION")
    _, gf = edge_gate.gate(T, SC, cfg["gate"], log=log, world=not REPRO)
    rep.fails += gf
    if cfg["spline"].get("owner_edges") and cfg["spline"].get("owner_mouths"):
        # the owner's reference gates with the edge gate (Sonoma round 14B; track.json as stage 1 wrote it)
        Ct_ = np.array(T["center"])[:, :2]
        cw_ = trackcfg.remap_stations(cfg_raw, T["n"], T["n"] * T["spacing_m"], C=Ct_)
        oref_ = owner_ref(cfg_raw, cw_, Ct_, T["n"])
        _, gf = edge_gate.owner_station_gate(*edge_gate.half_widths(T), oref_, cfg["gate"], log=log)
        rep.fails += gf
        _, gf = edge_gate.owner_gates(T, oref_, cfg["gate"], log=log)
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
    out = {k: g[k] for k in ("reach", "step", "cones_exempt") if k in g}
    sp = T["spacing_m"]
    al = []
    for a in g.get("allowed", []):
        P = np.array([cfg.enu(*a["a"]), cfg.enu(*a["b"])], float)
        i, _, _ = trk.project(P)
        al.append({"target": a["target"], **({"side": a["side"]} if a.get("side") else {}), "s0": round(float(i[0]) * sp, 1),
                   "s1": round(float(i[1]) * sp, 1), "why": a["why"]})
    out["allowed"] = al
    out["paddock"] = [{"name": p["name"], "poly": [list(cfg.enu(*q)) for q in p["latlon"]]} for p in g.get("paddock", [])]
    # round 13: declared openings in a barrier line (the run-gaps gate): [{latlon, why}] -> ENU
    out["openings"] = [{"x": round(float(cfg.enu(*o_["latlon"])[0]), 1), "y": round(float(cfg.enu(*o_["latlon"])[1]), 1), "why": o_["why"]}
                       for o_ in g.get("openings", [])]
    # round 14B part 2: wall heads the evidence shows bare (gates.known_exposures [{side, latlon, reason, evidence}]): the
    # wall-ends gate lists an exposed head within 10 m of one as a known exposure for the owner (never as joined / ok)
    out["known_exposures"] = []
    for k_ in g.get("known_exposures", []):
        i, _, _ = trk.project(np.array([cfg.enu(*k_["latlon"])]))
        out["known_exposures"].append({"side": k_["side"], "s": round(float(i[0]) * sp, 1), "reason": k_["reason"], "evidence": k_["evidence"]})
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
    fails += ground_lines_gate(cfg, tmp)
    return fails


def ground_lines_gate(cfg, tmp):
    """The unmodelled-ground-lines gate of round 13 (tools/track/gates/ground_lines.py; Sonoma owner, 23 Oct 2026: "if we
    are modeling textures in a long line on the ground, it's likely we are missing a feature"): long thin dark or pale
    lines in the package ortho 2-60 m beyond the edge with no modelled feature on them. Strict (fails on an open finding)
    when the config has scenery.ground_lines (options and dispositions); otherwise printed as advisory."""
    sys.path.insert(0, os.path.join(HERE, "gates"))
    import ground_lines
    gl = cfg["scenery"].get("ground_lines")
    rep = ground_lines.scan(tmp, gl or {})
    json.dump(rep, open(os.path.join(tmp, "ground_lines_report.json"), "w"), indent=1)
    for line in ground_lines.report_lines(rep, strict=gl is not None):
        log(line if gl is not None or not line.startswith("[") else line + " (no config scenery.ground_lines: advisory)")
    no = len(rep["open"])
    return ["ground lines"] if (gl is not None and no) else []


def manifest_dispositions(cfg):
    """The disposition lines of tools/track/compare/<id>/manifest.md (manifest.parse_dispositions); [] without one."""
    import manifest
    return manifest.manifest_dispositions(cfg["id"])


def coverage_gates(cfg, tmp, trk, sp):
    """The coverage and pit-lane gates of 21 Oct 2026 (tools/track/gates/coverageGate.ts, CLI run_coverage.ts): the
    scenery in `tmp` against the eye-level inventory tools/track/compare/<id>/inventory.json (inventory/inventory.py)
    and the config's pit_lane walls. Every circuit needs the inventory: without one both gates fail. MISSING rows pass only
    with a disposition line in the evidence manifest (manifest_dispositions)."""
    fails = [f"pit_lane config: {e}" for e in trackcfg.check_pit_lane(cfg)]
    for e in fails:
        log(f"[FAIL] {e}")
    inv = os.path.join(HERE, "compare", cfg["id"], "inventory.json")
    if not os.path.exists(inv):
        log(f"[FAIL] coverage: no inventory ({os.path.relpath(inv, ROOT)}); the inventory stage is required before scenery (build-track skill)")
        return fails + ["coverage", "pit lane"]
    proj = lambda ll: round(float(trk.project(np.array([cfg.enu(*ll)]))[0][0]) * sp, 1)  # noqa: E731
    disp = manifest_dispositions(cfg)
    Iv = json.load(open(inv)); L_ = trk.n * sp
    il_ = (cfg["scenery"].get("gates") or {}).get("inventory_lap")
    R_ = json.load(open(os.path.join(HERE, il_))) if il_ else None
    if R_ is not None and Iv.get("length_m") and abs(Iv["length_m"] - L_) > 1.0:
        # Sonoma round 14B part 1b: the inventory's stations are on the lap it was measured on (inv length_m); where this
        # package's lap differs by more than 1 m (T9A as he drew it: +6.5 m) each row's s is carried over by WORLD
        # position: as the same fraction of the frozen lap the inventory was taken on (scenery.gates.inventory_lap: round
        # 14A's centre, compare/<id>/inventory_lap.json), its point there, then the foot
        # of its normal on this package's centre (edges_spline.foot_project; monotonic, unlike the nearest point at T9A).
        # The manifest's dispositions (keyed by the row's s) move with their rows. Equal laps: unchanged
        Cr = np.array(R_["center"], float)[:, :2]; nr = len(Cr); Lr = float(np.linalg.norm(np.roll(Cr, -1, 0) - Cr, axis=1).sum())
        Cc = np.asarray(trk.C, float)[:, :2]; NLc = B.left_normals(Cc)
        su, _ = edges_spline.foot_project(Cc, NLc, Cr)
        su = np.unwrap(su * 2 * np.pi / trk.n) * trk.n / (2 * np.pi)

        def remap_s(s_):
            x = (float(s_) / Iv["length_m"]) * nr
            return round(float(np.interp(x % nr, np.arange(nr), su, period=nr) % trk.n) * sp, 1)
        for r_ in Iv["rows"]:
            r_["s"] = remap_s(r_["s"])
        for d_ in disp:
            d_["s"] = remap_s(d_["s"])
        Iv["length_m"] = round(L_, 2)
        inv = os.path.join(tmp, "inventory_remapped.json")
        json.dump(Iv, open(inv, "w"))
        log(f"     coverage: inventory rows carried from its {Iv.get('track', '')} lap by world position onto this {L_:.1f} m lap")
    cp = os.path.join(tmp, "coverage_config.json")
    json.dump({"tol": cfg["scenery"].get("gates", {}).get("coverage_tol", 15), "pit_walls": trackcfg.pit_walls_for_gate(cfg, proj),
               "dispositions": disp}, open(cp, "w"))
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
    ap.add_argument("--partial", action="store_true", help="with --publish: publish a package through its last passed stage "
                    "(geometry, or geometry + ghosts) before stage 3 has run (a new circuit's 1.10 review); never over a "
                    "package that has scenery")
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
        through = ("geometry", "ghosts", "scenery")
        if a.partial:
            # the stages before scenery whose records are current, in order; the package carries their files only
            through = tuple(st for i, st in enumerate(("geometry", "ghosts"))
                            if all(record_ok(cfg, out, s_, a.no_logger)[0] for s_ in ("geometry", "ghosts")[:i + 1]))
            if not through:
                raise SystemExit(f"--publish --partial refused: {record_ok(cfg, out, 'geometry', a.no_logger)[1]}")
            if os.path.exists(os.path.join(pub, "scenery.json")):
                raise SystemExit(f"--publish --partial refused: {pub} has scenery (a complete package); publish it whole")
        for st in through:
            ok, why = record_ok(cfg, out, st, a.no_logger)
            if not ok:
                raise SystemExit(f"--publish refused: {why}")
        files = ("track.json", "heightfield.bin", "ortho.jpg", "ghosts.json", "scenery.json", "far_heightfield.bin", "far_ortho.jpg")
        if a.partial:
            files = ("track.json", "heightfield.bin", "ortho.jpg") + (("ghosts.json",) if "ghosts" in through else ())
            log(f"partial publish through stage {through[-1]}: {', '.join(files)}")
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
