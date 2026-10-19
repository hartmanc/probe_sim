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
                                             nodes starting at the first; the loop is then turned to `direction`
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
  corners [(turn, name, dir, logger_s, lat, lon)]   anchor per corner: logger frame s (logger path) or lat/lon; the
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
  spline {runs [(lo, hi)], knot, lam, huber, line_off, prior, init_stiff, captures}
  features [(side, lo, hi, 'keep' | 'asphalt_end' | 'kerb', why)]   keep: the prior is held; asphalt_end: where the
                                             dark asphalt ends; kerb: red-band (kerb outer limit) candidates only
  shapes [{side, knots [(station, half-width)], blend, why}]
  straights [{side, fit 'paint' | 'parallel', lo, hi, join (a, b), end, blend, tol | ref_side/ref_lo/ref_hi, why}]
  gate {straight_rms, step, profile_step, spline_obs_within}
Ghosts (Stage 2): ghosts {margin, kerb_margin, nudge, jerk_w}
Scenery (Stage 3): scenery {...}, see build_scenery.py and scenery_post.py
App: app {short, pace}
"""
import importlib.util
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


def remap_stations(cfg, n, length_m=None):
    """Config station numbers are those of the geometry the config was written for (`stations_ref` = (n, length_m)).
    A build with another station count (Laguna without logger laps: the OSM loop gives 3600 stations, the logger 3560)
    maps them by the fraction of the lap: station k -> round(k * n / n_ref); metres s -> s * length / length_ref.
    Returns a new Config (the same object when nothing changes)."""
    ref = cfg.get('stations_ref')
    if not ref or (ref[0] == n and (length_m is None or abs(ref[1] - length_m) < 1e-6)):
        return cfg
    import copy
    c = copy.deepcopy(cfg)
    f = n / ref[0]
    fm = (length_m / ref[1]) if length_m else f
    st = lambda k: int(round(k * f))  # noqa: E731
    c['features'] = [(a, st(lo), st(hi)) + tuple(rest) for a, lo, hi, *rest in c['features']]
    for shp in c['shapes']:
        shp['knots'] = [(st(k), v) for k, v in shp['knots']]
    for s in c['straights']:
        for k in ('lo', 'hi', 'end', 'ref_lo', 'ref_hi'):
            if k in s: s[k] = st(s[k])
        s['join'] = (st(s['join'][0]), st(s['join'][1]))
    p = c.get('prior', {})
    if p:
        p['bridge_skip'] = [st(k) for k in p.get('bridge_skip', [])]
        for key in ('first_edge', 'interp'):
            p[key] = [(a, st(lo), st(hi)) + tuple(rest) for a, lo, hi, *rest in p.get(key, [])]
    sp = c['spline']
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
        for k in ('near', 's0', 's1'): e[k] = round(e[k] * fm, 1)
    for e in s.get('edge_line_runs', []):
        for k in ('s0', 's1'): e[k] = round(e[k] * fm, 1)
    if s.get('pit_exit_cones', {}).get('s0') is not None:
        s['pit_exit_cones']['s0'] = round(s['pit_exit_cones']['s0'] * fm, 1)
    return c
