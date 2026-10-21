"""Per-track configuration for the track pipeline (tools/track/build_track.py).

A track config is `tools/track/tracks/<id>/config.py` defining one dict, CONFIG. It is data only: build_track.py reads it
with `load(id)` and never executes anything else from the track folder. tracks/laguna_seca/config.py is the worked
example; the keys, their meaning and their defaults:

Identity and sources (Stage 0)
  id, name, direction ('ccw' | 'cw')        track id (= public/tracks/<id>/), display name, driving direction from above
  origin (lat, lon)                          origin of the local ENU frame (CONTRACTS section 1)
  osm_bbox (W, S, E, N)                      OSM API map call box
  cache_dir                                  download cache, relative to tools/track (default 'cache/<id>')
  osm_file                                   cached OSM XML in cache_dir (default 'osm.xml')
  loop_ways [way id, ...]                    the OSM highway=raceway ways forming the Lemons loop, stitched by shared end
                                             nodes starting at the first; the loop is then turned to `direction`. An
                                             entry 'way:from_node:to_node' takes the part of a way between two of its
                                             nodes (a loop that leaves a long way for a bypass and rejoins it); with
                                             from_node after to_node the part is driven against the way's node order
  pit_lane_way                               OSM name of the pit-lane way (scenery: pit lane, pit wall, edge lines)
  dem_tiles [url, ...]                       USGS 3DEP 1 m DEM tiles (read as windows over HTTP, cached)
  lidar_ept, lidar_survey                    Entwine point tiles of the same survey; survey name for notes
  dem13                                      1/3 arc-second DEM tile (far terrain)
Logger laps (optional)
  logger_dir                                 the team's logger analysis (centreline.npy, traces_warped.pkl, sections.pkl,
                                             official.pkl); None = the no-logger path
  logger_drivers, logger_sections, logger_bad_gps_files
  start_finish_latlon                        the timing line, used when there is no logger (station 0 = its projection)
Corners
  corners [(turn, name, dir, logger_s, lat, lon[, window_m])]   anchor per corner: logger frame s (logger path) or lat/lon; the
                                             corner is the signed-curvature peak within +-45 m of it
  named_straights [(name, from turn, to turn)]
Geometry (Stage 1)
  loop_check {n_min, n_max, official_m, elev_min, elev_max}
  centre {naip_fit_a, naip_fit_b (logger: driven line -> NAIP midpoint), osm_fit_a, osm_fit_b (no logger: OSM loop ->
          NAIP midpoint), paint_fit_a, paint_fit_b, bridge_win, gps_margin, min_width, extra_shadow_stations,
          pit_merge (default True: through the pit merges the midpoint target takes the circuit's own edge, the cone
          line or the painted edge interpolated across the join; off while reproducing an accepted build), pit_merge_gap
          (m, default 0.3: a pit-lane part this close to the track edge counts as joined)}
  reproduce {...}                            build artefacts of an accepted package (logger path only; see Laguna's)
  centre_captures ('z20' | 'clean'), centre_registration ('per_capture' | 'common')
  repave_fixes [(a, b, crest from, crest to, why)]
  captures {z20_dir, z20_index, z20_mask, clean_dir, clean_index, mpp, common_shift, exclude, cursor_boxes}
  spline {runs [(lo, hi)], knot, lam, huber, line_off, prior, init_stiff, captures, asphalt_end {jump, sat_max, lo, hi},
          warm_thr, mask [(side, lo, hi, src)]}   (asphalt_end / warm_thr: detector parameters of those features;
          absent = the defaults; mask: stations whose capture readings are dropped, an object beside the edge, with its capture)
  features [(side, lo, hi, 'keep' | 'asphalt_end' | 'warm_end' | 'kerb' | 'kerb_band', why)]   keep: the prior is held (legacy reproduction
                                             only; the fitted method ignores it); asphalt_end: where the dark asphalt
                                             ends; kerb: red-band (kerb outer limit) candidates only; warm_end: where
                                             grey asphalt meets warm dirt (the warmth step, spline.warm_thr); kerb_band:
                                             a kerb whose blocks are not red on the captures, every 0.3-2.6 m band by
                                             its outer limit (Buttonwillow, 20 Oct 2026)
  prior {bridge_win, bridge_skip [first-centre stations], extra_bridges [first-centre stations of bridges OSM does not
         map], first_edge [(side, lo, hi, why)], interp [(side, lo, hi, why)]}
  shapes [{side, knots [(station, half-width)], blend, why, fitted_only}]   measured half-widths; in the fitted method
                                             a constraint inside the fit (fitted_only: not in the legacy reproduction)
  straights [{side, fit 'paint' | 'parallel', lo, hi, join (a, b), end, blend, tol | ref_side/ref_lo/ref_hi, why}]
  gate {straight_rms, step, profile_step, spline_obs_within}
Ghosts (Stage 2): ghosts {margin, kerb_margin, nudge, jerk_w}
Scenery (Stage 3): scenery {...}, see build_scenery.py and scenery_post.py. Evidence keys added in the Sonoma scenery
  round 5 (21 Oct 2026), all optional (absent = the earlier behaviour, Laguna's package unchanged):
    osm_barrier_overrides {OSM way id: {kind, h, fence, color | drop: True, src}}   re-kind or drop an OSM wall on evidence
    building_evidence [{contains (lat, lon), src | drop: True, src}]   the source of a building the coverage gate checks,
                                             or its removal where the 2026 evidence does not show it
    tyre_stacks [{latlon, h, w, style 'tyres'|'blocks', color, src}]   free-standing stacks ('tyres' landmarks, drawn only)
    light_masts [{latlon, h, src}]           masts ('mast' landmarks)
    closed_roads[].mouth_cones [{near (lat, lon), src}]   cones only at the mouths the evidence shows coned
    wall_boards[]: a panel with no `base` stands on its wall; its top counts toward the wall's height in the coverage gate
Pit lane (first-class, 21 Oct 2026; read by the pit-lane gate, tools/track/gates/coverageGate.ts, and by the scenery
  builder as it learns each part). Sides are as driven down the lane (the lap's direction); stations are the lap s
  abeam (the lane part's track_s), or lat/lon ends projected onto the track by build_track.py. Every entry carries `src`
  (an inventory frame, a capture, a panorama id). Nothing here is a default: an empty list means "not surveyed".
  pit_lane {
    lane       {source: 'osm' (pit_lane_way) | 'declared', latlon: [(lat, lon), ...] (declared centre line), width_m,
                match_track_tone {k, paint} (one road material: the ortho inside the lane mapped onto the track's tone)}
    walls      [{side 'left'|'right', s0, s1 | a (lat, lon), b (lat, lon), h (m, HEIGHTS.md), material
                 ('concrete'|'jersey'|'board_wall'|'pitbox_wall'), fence (m, catch fence on top), src,
                 latlon [(lat, lon), ...] (measured geometry, built as a barrier) | declared (the name of the
                 scenery.declared_walls entry that is this wall)}]
    boxes      {n, first (lat, lon), last (lat, lon), wall_h, numbered: bool, src}
    buildings  [{name, osm (way id) | footprint [(lat, lon), ...], h, roof ('flat'|'gable'), colours {wall, roof}, src}]
    furniture  [{kind ('fuel'|'light_mast'|'cone_line'|'water_barrier'|'tyre_stack'|'gate'|'sign'), latlon | s, side, src}]
  }
App: app {short, pace}
"""
import importlib.util
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
TRACKS = os.path.join(HERE, 'tracks')

DEFAULTS = dict(
    direction='ccw', osm_file='osm.xml', pit_lane_way='Pit Lane', logger_dir=None, logger_drivers=[],
    logger_sections=None, logger_bad_gps_files=[], start_finish_latlon=None, named_straights=[],
    loop_check=dict(n_min=500, n_max=10000, official_m=None, elev_min=0, elev_max=500),
    centre=dict(naip_fit_a=1e6, naip_fit_b=1e3, osm_fit_a=1e3, osm_fit_b=1e3, paint_fit_a=1e4, paint_fit_b=1e2,
                nologger_fit_a=1e1, nologger_fit_b=1e5, pit_merge=True, pit_merge_gap=0.3,
                bridge_win=25, gps_margin=1.0, min_width=10.0, extra_shadow_stations=[]),
    centre_captures='clean', centre_registration='common', repave_fixes=[],
    captures=dict(z20_dir=None, z20_index='z20_tiles.json', z20_mask=None, clean_dir=None, clean_index='tiles.json',
                  mpp=0.11992, common_shift=None, exclude=[], clean_mask='clean'),
    spline=dict(runs=None, knot=6, lam=30.0, huber=0.25, line_off=0.26, prior=0.03, init_stiff=30.0, captures='clean'),
    features=[], shapes=[], straights=[],
    gate=dict(straight_rms=0.10, step=0.10, profile_step=0.10, spline_obs_within=0.85),
    ghosts=dict(margin=1.0, kerb_margin=1.0, nudge=0.3, jerk_w=3),
    scenery={}, app={},
    pit_lane=dict(lane=dict(source='osm'), walls=[], boxes=None, buildings=[], furniture=[]),
)


class Config(dict):
    """CONFIG with defaults filled in, plus derived paths."""

    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e

    @property
    def cache(self):
        return os.path.join(HERE, self['cache_dir'])

    @property
    def logger(self):
        return self['logger_dir'] is not None

    def path(self, p):
        return p if p is None or os.path.isabs(p) else os.path.join(HERE, p)

    def enu(self, lat, lon):
        lat0, lon0 = self['origin']
        R = 6378137.0
        return math.radians(lon - lon0) * R * math.cos(math.radians(lat0)), math.radians(lat - lat0) * R


def load(track_id, no_logger=False):
    path = os.path.join(TRACKS, track_id, 'config.py')
    if not os.path.exists(path):
        raise SystemExit(f'no track config {path} (see tools/track/trackcfg.py for the format)')
    spec = importlib.util.spec_from_file_location(f'trackcfg_{track_id}', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    raw = dict(mod.CONFIG)
    if raw.get('id') != track_id:
        raise SystemExit(f'{path}: CONFIG id {raw.get("id")!r} is not {track_id!r}')
    cfg = Config()
    for k, v in DEFAULTS.items():
        if isinstance(v, dict):
            cfg[k] = {**v, **raw.get(k, {})}
        else:
            cfg[k] = raw.get(k, v)
    for k, v in raw.items():
        if k not in cfg:
            cfg[k] = v
    cfg.setdefault('cache_dir', os.path.join('cache', track_id))
    if no_logger:
        cfg['logger_dir'] = None
    for k in ('id', 'name', 'origin', 'osm_bbox', 'loop_ways', 'dem_tiles', 'corners'):
        if not cfg.get(k):
            raise SystemExit(f'{path}: CONFIG needs {k!r}')
    if not cfg.logger and not cfg['start_finish_latlon']:
        raise SystemExit(f'{path}: without logger laps the config needs start_finish_latlon')
    return cfg


PIT_WALL_MATERIALS = ('concrete', 'jersey', 'board_wall', 'pitbox_wall', 'armco', 'fence')
PIT_FURNITURE = ('fuel', 'light_mast', 'cone_line', 'water_barrier', 'tyre_stack', 'gate', 'sign')


def check_pit_lane(cfg):
    """Schema check of the pit_lane section: returns a list of error strings (empty when valid)."""
    p = cfg.get('pit_lane') or {}
    errs = []
    lane = p.get('lane', {})
    if lane.get('source', 'osm') not in ('osm', 'declared'):
        errs.append(f"pit_lane.lane.source {lane.get('source')!r} not 'osm' | 'declared'")
    if lane.get('source') == 'declared' and len(lane.get('latlon', [])) < 2:
        errs.append('pit_lane.lane: a declared lane needs latlon (two or more points)')
    for k, w in enumerate(p.get('walls', [])):
        where = f'pit_lane.walls[{k}]'
        if w.get('side') not in ('left', 'right'):
            errs.append(f"{where}: side {w.get('side')!r} not left | right")
        if not (('s0' in w and 's1' in w) or ('a' in w and 'b' in w)):
            errs.append(f'{where}: needs s0, s1 (lap stations) or a, b (lat, lon)')
        if 'h' in w and not (isinstance(w['h'], (int, float)) and 0 < w['h'] < 15):
            errs.append(f"{where}: h {w['h']!r} out of range")
        if w.get('material', 'concrete') not in PIT_WALL_MATERIALS:
            errs.append(f"{where}: material {w.get('material')!r} not in {PIT_WALL_MATERIALS}")
        if not w.get('src'):
            errs.append(f'{where}: needs src (no object without a cited source)')
    b = p.get('boxes')
    if b is not None and not (isinstance(b, dict) and b.get('src')):
        errs.append('pit_lane.boxes: needs src')
    for k, b in enumerate(p.get('buildings', [])):
        if not b.get('src') or not (b.get('osm') or b.get('footprint')):
            errs.append(f'pit_lane.buildings[{k}]: needs osm or footprint, and src')
    for k, f in enumerate(p.get('furniture', [])):
        if f.get('kind') not in PIT_FURNITURE or not f.get('src') or not ('latlon' in f or 's' in f):
            errs.append(f'pit_lane.furniture[{k}]: needs kind in {PIT_FURNITURE}, latlon or s, and src')
    return errs


def pit_walls_for_gate(cfg, project=None):
    """The declared pit-lane walls as [{side, s0, s1, h, src}] in lap stations for the pit-lane gate; `project` maps
    (lat, lon) -> lap s for walls given by their ends."""
    out = []
    for w in (cfg.get('pit_lane') or {}).get('walls', []):
        if 's0' in w:
            s0, s1 = w['s0'], w['s1']
        elif project is not None:
            s0, s1 = project(w['a']), project(w['b'])
        else:
            continue
        out.append({'side': w['side'], 's0': s0, 's1': s1, 'h': w.get('h'), 'src': w.get('src', '')})
    return out


def _ref_polyline(cfg):
    p = os.path.join(TRACKS, cfg['id'], 'stations_ref.json')
    return json.load(open(p)) if os.path.exists(p) else None


def remap_stations(cfg, n, length_m=None, C=None):
    """Config station numbers are those of the geometry the config was written for (`stations_ref` = (n, length_m),
    whose centre polyline is frozen in tracks/<id>/stations_ref.json). With a built centre C (n, 2) they are mapped by
    WORLD POSITION: reference station k -> its reference centre point -> the nearest station of C; a measured shape's
    knot (station, half-width) -> its reference edge point -> station and half-width on C. Without C (or without the
    frozen polyline) by the fraction of the lap: k -> round(k * n / n_ref), metres s -> s * length / length_ref.
    Returns a new Config (the same object when nothing changes)."""
    import copy
    ref = cfg.get('stations_ref')
    if not ref or (ref[0] == n and (length_m is None or abs(ref[1] - length_m) < 1e-6)):
        return cfg
    c = copy.deepcopy(cfg)
    R = _ref_polyline(cfg) if C is not None else None
    if R is not None:
        import numpy as np
        Cr = np.array(R['center']); nr = len(Cr)
        t = np.roll(Cr, -1, 0) - np.roll(Cr, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NLr = np.c_[-t[:, 1], t[:, 0]]
        C = np.asarray(C, float); tc = np.roll(C, -1, 0) - np.roll(C, 1, 0); tc /= np.linalg.norm(tc, axis=1, keepdims=True)
        NLc = np.c_[-tc[:, 1], tc[:, 0]]
        from scipy.spatial import cKDTree
        kd = cKDTree(C)

        def proj(P):
            _, i = kd.query(P); return i, ((P - C[i]) * NLc[i]).sum(-1)

        def st(k):
            k = int(round(k)); i, _ = proj(Cr[k % nr]); off = (k - (k % nr))   # keep wrap-around ranges (k >= nr)
            return int(i) + (len(C) if off else 0)
        sp_ref = ref[1] / ref[0]; sp_new = (length_m / n) if length_m else 1.0
        fm_s = lambda s_m: round(st(s_m / sp_ref) * sp_new, 1)  # noqa: E731
        for shp in c['shapes']:
            sg = 1 if shp['side'] == 'left' else -1; kn = []
            for k, hw in shp['knots']:
                i, lat = proj(Cr[k % nr] + sg * hw * NLr[k % nr]); kn.append((int(i), round(float(abs(lat)), 3)))
            shp['knots'] = kn
    else:
        f = n / ref[0]
        fm = (length_m / ref[1]) if length_m else f
        st = lambda k: int(round(k * f))  # noqa: E731
        fm_s = lambda s_m: round(s_m * fm, 1)  # noqa: E731
        for shp in c['shapes']:
            shp['knots'] = [(st(k), v) for k, v in shp['knots']]
    c['features'] = [(a, st(lo), st(hi)) + tuple(rest) for a, lo, hi, *rest in c['features']]
    for s in c['straights']:
        for k in ('lo', 'hi', 'end', 'ref_lo', 'ref_hi'):
            if k in s: s[k] = st(s[k])
        s['join'] = (st(s['join'][0]), st(s['join'][1]))
    p = c.get('prior', {})
    if p:
        p['bridge_skip'] = [st(k) for k in p.get('bridge_skip', [])]
        p['extra_bridges'] = [st(k) for k in p.get('extra_bridges', [])]
        for key in ('first_edge', 'interp'):
            p[key] = [(a, st(lo), st(hi)) + tuple(rest) for a, lo, hi, *rest in p.get(key, [])]
    sp = c['spline']
    # stations of the edge fit's masks and kerb-search zones (Buttonwillow, 20 Oct 2026; no other circuit has them)
    if sp.get('mask'):
        sp['mask'] = [(a, st(lo), st(hi)) + tuple(rest) for a, lo, hi, *rest in sp['mask']]
    if sp.get('kerb_search'):
        sp['kerb_search'] = [(a, st(lo), st(hi)) + tuple(rest) for a, lo, hi, *rest in sp['kerb_search']]
    if sp.get('runs'):
        sp['runs'] = [(st(r[0]), st(r[1])) + tuple(r[2:]) for r in sp['runs']]
    c['repave_fixes'] = [(st(a), st(b), st(c0), st(c1), why) for a, b, c0, c1, why in c['repave_fixes']]
    c['centre']['extra_shadow_stations'] = [st(k) for k in c['centre'].get('extra_shadow_stations', [])]
    g = c['gate']
    g['exempt'] = [(a, st(lo), st(hi)) + tuple(rest) for a, lo, hi, *rest in g.get('exempt', [])]
    g['wall_gaps'] = [(a, b, st(lo), st(hi)) for a, b, lo, hi in g.get('wall_gaps', [])]
    s = c['scenery']
    s['aprons'] = [(t, side, st(lo), st(hi), why) for t, side, lo, hi, why in s.get('aprons', [])]
    for z in s.get('shoulder_zones', []):
        z['lo'], z['hi'] = st(z['lo']), st(z['hi'])
    for key in ('pitwall_end', 'pitwall_setback', 'pitwall_straight'):
        if s.get(key):
            for k in ('lo', 'hi', 'fit_lo', 'fit_hi'):
                if k in s[key]: s[key][k] = st(s[key][k])
    for e in s.get('kerb_extents', []):
        for k in ('near', 's0', 's1'): e[k] = fm_s(e[k])
    for e in s.get('edge_line_runs', []):
        for k in ('s0', 's1'): e[k] = fm_s(e[k])
    if (s.get('pit_exit_cones') or {}).get('s0') is not None:
        s['pit_exit_cones']['s0'] = fm_s(s['pit_exit_cones']['s0'])
    return c
