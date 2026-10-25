"""Stage 3 of the track pipeline: scenery.json, far_heightfield.bin, far_ortho.jpg and the regraded ortho.jpg of a track
package (run through tools/track/build_track.py --stage scenery; the per-circuit constants are in the track config's
`scenery` block).

Reads track.json / heightfield.bin of the package being built. Format: CONTRACTS.md section 2b and
tools/track/README.md. Downloads are cached in the track's cache folder. The post steps that were separate scripts on
18 Oct 2026 (paved aprons, the shoulder zone, pit-wall end / set-back / straightening, edge-line runs, kerb extents,
the pit-exit cone start) run afterwards from scenery_post.py.
"""

import io
import json
import math
import os
import sys
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo as bl  # noqa: E402  (frames, DEM window, NAIP helpers, grade_ortho)
import barrier_rules as BR  # noqa: E402  (round 12: wall tops across hollows, tyre rows off the road)

CACHE = OUT = PREVIEWS = None   # set by configure()
STRUCT_CFG = None   # config `structures` (top level), set by configure()
PITWALL_EDGE = None  # optional per-station lateral (+left, m) of the left edge the pit wall stands 0.6 m off
SC_CFG = {}
HOLLOWS = dict(BR.HOLLOW_DEFAULTS)   # config scenery.barrier_hollows {span, slope} (False: None, off), set by configure()
CFG_ALL = None
PIT_CFG = {}   # the track config's pit_lane section (trackcfg.py; walls with latlon get geometry here, 21 Oct 2026)
PIT_EXIT = {}  # the track config's centre.pit_exit (stage 1's measured pit-exit blend line / wall end; trackcfg.py)
UA = {"User-Agent": "probe-sim/0.1"}
EPT = DEM13 = PIT_WAY = None   # from the track config (lidar_ept, dem13, pit_lane_way)
FAR_HALF, FAR_DX, FAR_ORTHO_PX = 2500.0, 10.0, 5.0  # far terrain: 5 x 5 km at 10 m, image at 5 m/px
CELL = 1.0  # canopy grid, m
log = bl.log


def rnd(v, d=2):
    return float(round(float(v), d))


def configure(cfg, out_dir):
    """Point the module at one track's config and package directory (call geo.configure(cfg) first)."""
    global CACHE, OUT, PREVIEWS, EPT, DEM13, PIT_WAY, SC_CFG, PIT_CFG, TYRE_CORNERS, PAVED_RUNOFF, BANNER_BOARDS, BANNERS, BRIDGE_STYLE, HANGARS, CFG_ALL
    CFG_ALL = cfg
    CACHE, OUT, PREVIEWS = cfg.cache, out_dir, out_dir
    EPT, DEM13, PIT_WAY = cfg.get("lidar_ept"), cfg.get("dem13"), cfg["pit_lane_way"]
    SC_CFG = cfg["scenery"]
    global HOLLOWS
    hc = SC_CFG.get("barrier_hollows", {})
    HOLLOWS = None if hc is False else dict(BR.HOLLOW_DEFAULTS, **(hc or {}))
    PIT_CFG = cfg.get("pit_lane") or {}
    TYRE_CORNERS = [tuple(x) for x in SC_CFG.get("tyre_corners", [])]
    PAVED_RUNOFF = [tuple(x) for x in SC_CFG.get("paved_runoff", [])]
    BANNER_BOARDS = [tuple(x) for x in SC_CFG.get("banner_boards", [])]
    BANNERS = dict(SC_CFG.get("bridge_banners", {}))
    BRIDGE_STYLE = dict(SC_CFG.get("bridge_style", {}))
    HANGARS = dict(SC_CFG.get("hangars", {}))
    global STRUCT_CFG, PIT_EXIT
    STRUCT_CFG = cfg.get("structures")   # parametric structures (build_structures.py, 21 Oct 2026); absent: none
    PIT_EXIT = dict((cfg.get("centre") or {}).get("pit_exit") or {})   # stage-1 key: the cone objects may take its line


def configure_geometry(cfg, out_dir):
    """Stage 1's view of this module (20 Oct 2026): the cache, the package directory, the lidar survey and the OSM
    pit-lane way name, all stage-1 keys. The scenery and pit_lane sections are left EMPTY, so nothing stage 1 calls here
    (pit_lane, pit_exit_line, pit_wall_line, bridge_stations, lidar_points) can read a stage-3 key: stage 1 used to take
    the pit merge from barriers() / pit_exit_cones(), which read scenery and pit_lane, while config_id('geometry') does
    not hash them."""
    global CACHE, OUT, PREVIEWS, EPT, DEM13, PIT_WAY, SC_CFG, PIT_CFG, TYRE_CORNERS, PAVED_RUNOFF, BANNER_BOARDS, BANNERS, BRIDGE_STYLE, HANGARS
    global STRUCT_CFG, PIT_EXIT
    CACHE, OUT, PREVIEWS = cfg.cache, out_dir, out_dir
    EPT, DEM13, PIT_WAY = cfg.get("lidar_ept"), cfg.get("dem13"), cfg["pit_lane_way"]
    SC_CFG, PIT_CFG, STRUCT_CFG, PIT_EXIT = {}, {}, None, {}
    TYRE_CORNERS, PAVED_RUNOFF, BANNER_BOARDS = [], [], []
    BANNERS, BRIDGE_STYLE, HANGARS = {}, {}, {}


def cache_file(name, box):
    """A box-keyed cache file: the plain name when absent or holding this box, else a name with the box in it (an
    existing cache file of another box is never overwritten)."""
    p = os.path.join(CACHE, name)
    if not os.path.exists(p):
        return p
    try:
        if np.allclose(np.load(p)["box"], box):
            return p
    except Exception:  # noqa: BLE001
        pass
    stem, ext = os.path.splitext(name)
    return os.path.join(CACHE, f"{stem}_{'_'.join(str(int(v)) for v in box)}{ext}")


# ---------------------------------------------------------------- track
class Track:
    def __init__(self, t=None, hf=None):
        if t is None:
            with open(os.path.join(OUT, "track.json")) as fh:
                t = json.load(fh)
        # corner s is metres along the lap (station * spacing_m); placements here work in stations
        self.sp = float(t.get("spacing_m", 1.0))
        t = dict(t, corners=[dict(c, s=int(round(c["s"] / self.sp)) % t["n"]) for c in t["corners"]])
        self.t = t
        self.C = np.array(t["center"])
        self.L = np.array(t["left"])
        self.R = np.array(t["right"])
        self.n = t["n"]
        h = t["heightfield"]
        self.hf = hf if hf is not None else np.fromfile(os.path.join(OUT, h["file"]), np.float32).reshape(h["ny"], h["nx"])
        self.h = h
        o = t["ortho"]
        self.box = (o["x0"], o["y0"], o["x1"], o["y1"])
        d = np.roll(self.C[:, :2], -1, 0) - np.roll(self.C[:, :2], 1, 0)
        self.T = d / np.linalg.norm(d, axis=1, keepdims=True)
        self.N = np.c_[-self.T[:, 1], self.T[:, 0]]  # left normal
        # per-side half-widths (v2 track: left and right differ)
        self.hl = np.linalg.norm(self.L[:, :2] - self.C[:, :2], axis=1)
        self.hr = np.linalg.norm(self.R[:, :2] - self.C[:, :2], axis=1)
        from scipy.spatial import cKDTree

        self.kd = cKDTree(self.C[:, :2])

    def ground(self, x, y):
        h = self.h
        c = (np.asarray(x, float) - h["x0"]) / h["dx"]
        r = (np.asarray(y, float) - h["y0"]) / h["dx"]
        return ndi.map_coordinates(self.hf, [np.atleast_1d(r), np.atleast_1d(c)], order=1, mode="nearest")

    def project(self, P):
        """Station index, signed lateral offset (+left) and distance outside the edge (negative = on track)."""
        P = np.atleast_2d(P)[:, :2]
        _, i = self.kd.query(P)
        lat = ((P - self.C[i, :2]) * self.N[i]).sum(1)
        return i, lat, np.abs(lat) - np.where(lat > 0, self.hl[i], self.hr[i])

    def hw(self, i, side):
        """Half-width on `side` (+1 left, -1 right; scalar or array) at station(s) i."""
        return np.where(np.asarray(side) > 0, self.hl[i], self.hr[i])

    def edge_point(self, i, side, extra):
        """Point `extra` m outside the edge on `side` (+1 left, -1 right) at station i."""
        i = np.asarray(i) % self.n
        off = side * (self.hw(i, side) + extra)
        xy = self.C[i, :2] + self.N[i] * off[..., None] if np.ndim(i) else self.C[i, :2] + self.N[i] * off
        return xy


# ---------------------------------------------------------------- lidar (Entwine point tiles on AWS)
def merc(x, y):
    """ENU -> EPSG:3857."""
    lon, lat = bl.lonlat(x, y)
    return np.radians(lon) * bl.R, bl.R * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2))


def merc_to_enu(mx, my):
    lon = np.degrees(mx / bl.R)
    lat = np.degrees(2 * np.arctan(np.exp(my / bl.R)) - np.pi / 2)
    return bl.enu(lat, lon)


def get(url, path=None, timeout=120):
    if path and os.path.exists(path):
        with open(path, "rb") as fh:
            return fh.read()
    for attempt in range(6):
        try:
            r = requests.get(url, timeout=timeout, headers=UA)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            if path:
                with open(path + ".part", "wb") as fh:
                    fh.write(r.content)
                os.replace(path + ".part", path)
            return r.content
        except Exception as e:  # noqa: BLE001
            log("  retry", url.rsplit("/", 1)[-1], str(e)[:60])
            import time

            time.sleep(3 * (attempt + 1))
    raise RuntimeError("download failed: " + url)


def lidar_points(box):
    """All points of the EPT dataset inside the ENU box: (x, y, z_navd88, class, return_no, n_returns)."""
    cache = cache_file("lidar_points.npz", box)
    if os.path.exists(cache):
        d = np.load(cache)
        if np.allclose(d["box"], box):
            return d["x"], d["y"], d["z"], d["c"], d["rn"], d["nr"]
    import laspy

    meta = json.loads(get(EPT + "ept.json", os.path.join(CACHE, "ept.json")))
    b = meta["bounds"]
    mx0, my0 = merc(box[0], box[1])
    mx1, my1 = merc(box[2], box[3])
    edir = os.path.join(CACHE, "ept")
    os.makedirs(edir, exist_ok=True)

    def node_box(d, x, y):
        s = (b[3] - b[0]) / 2 ** d
        return b[0] + x * s, b[1] + y * s, b[0] + (x + 1) * s, b[1] + (y + 1) * s

    def hits(key):
        d, x, y, _ = map(int, key.split("-"))
        a = node_box(d, x, y)
        return a[0] < mx1 and a[2] > mx0 and a[1] < my1 and a[3] > my0

    keys, todo = [], ["0-0-0-0"]
    while todo:
        hk = todo.pop()
        h = json.loads(get(EPT + f"ept-hierarchy/{hk}.json", os.path.join(edir, f"h_{hk}.json")))
        for k, cnt in h.items():
            if not hits(k):
                continue
            if cnt == -1:
                todo.append(k)
            elif cnt > 0:
                keys.append(k)
    log(f"lidar: {len(keys)} EPT nodes intersect the box")

    def fetch(k):
        data = get(EPT + f"ept-data/{k}.laz", os.path.join(edir, f"{k}.laz"))
        las = laspy.read(io.BytesIO(data))
        m = (las.x >= mx0) & (las.x <= mx1) & (las.y >= my0) & (las.y <= my1)
        return (np.asarray(las.x)[m], np.asarray(las.y)[m], np.asarray(las.z)[m].astype(np.float32),
                np.asarray(las.classification)[m].astype(np.uint8), np.asarray(las.return_number)[m].astype(np.uint8),
                np.asarray(las.number_of_returns)[m].astype(np.uint8))

    parts = []
    with ThreadPoolExecutor(16) as ex:
        for i, p in enumerate(ex.map(fetch, keys)):
            parts.append(p)
            if i % 200 == 0:
                log(f"  {i}/{len(keys)} nodes")
    mx, my, z, c, rn, nr = (np.concatenate([p[j] for p in parts]) for j in range(6))
    x, y = merc_to_enu(mx, my)
    x, y = x.astype(np.float32), y.astype(np.float32)
    np.savez(cache, box=np.array(box), x=x, y=y, z=z, c=c, rn=rn, nr=nr)
    return x, y, z, c, rn, nr


def lidar_grids(trk):
    """1 m grids over the ortho box: DEM (bare earth, ENU z), DSM of all non-noise points, vegetation DSM,
    building-class DSM. Row 0 = y0 (south), like heightfield.bin."""
    box = trk.box
    cache = cache_file("lidar_grids.npz", box)
    if os.path.exists(cache):
        d = np.load(cache)
        if np.allclose(d["box"], box):
            return {k: d[k] for k in d.files}
    x, y, z, c, rn, nr = lidar_points(box)
    log(f"lidar: {len(x) / 1e6:.1f} M points; classes {dict(zip(*np.unique(c, return_counts=True)))}")
    z0 = trk.t["z0_navd88"]
    nx = int((box[2] - box[0]) / CELL)
    ny = int((box[3] - box[1]) / CELL)
    dem = bl.Dem(box)
    gx = box[0] + (np.arange(nx) + 0.5) * CELL
    gy = box[1] + (np.arange(ny) + 0.5) * CELL
    GX, GY = np.meshgrid(gx, gy)
    DEM = (dem(GX.ravel(), GY.ravel()).reshape(ny, nx) - z0).astype(np.float32)
    ci = ((x - box[0]) / CELL).astype(np.int64)
    ri = ((y - box[1]) / CELL).astype(np.int64)
    ok = (ci >= 0) & (ci < nx) & (ri >= 0) & (ri < ny) & (c != 7) & (c != 18)
    zz = z - z0
    # vertical datum check against the bare-earth DEM
    g = ok & (c == 2)
    dz = np.median(zz[g] - DEM[ri[g], ci[g]]) if g.any() else 0.0
    log(f"lidar ground minus DEM: median {dz:+.3f} m (removed)")
    zz = zz - dz

    def dsm(mask):
        out = np.full(ny * nx, -1e9, np.float32)
        np.maximum.at(out, ri[mask] * nx + ci[mask], zz[mask])
        out = out.reshape(ny, nx)
        out[out < -1e8] = np.nan
        return out

    DSM = dsm(ok)
    VEG = dsm(ok & np.isin(c, (3, 4, 5)))
    BLD = dsm(ok & (c == 6))
    UNC = dsm(ok & (c == 1))
    BRG = dsm(ok & (c == 17))
    # fraction of above-ground returns that are part of a multi-return pulse: high for tree canopy, ~0 for roofs
    above = ok & (c == 1)
    idx = ri[above] * nx + ci[above]
    cnt = np.bincount(idx, minlength=nx * ny).reshape(ny, nx).astype(np.float32)
    mul = np.bincount(idx, weights=(nr[above] > 1).astype(np.float32), minlength=nx * ny).reshape(ny, nx)
    MULTI = (ndi.uniform_filter(mul.astype(np.float32), 3) / np.maximum(ndi.uniform_filter(cnt, 3), 1e-3)).astype(np.float32)
    out = {"box": np.array(box), "DEM": DEM, "DSM": DSM, "VEG": VEG, "BLD": BLD, "UNC": UNC, "BRG": BRG, "MULTI": MULTI}
    np.savez_compressed(cache, **out)
    return out




# ---------------------------------------------------------------- OSM
class Osm:
    def __init__(self):
        root = ET.parse(bl.OSM_FILE).getroot()
        self.nodes = {n.get("id"): (float(n.get("lat")), float(n.get("lon"))) for n in root.iter("node")}
        self.ways = []
        for w in root.iter("way"):
            tags = {t.get("k"): t.get("v") for t in w.findall("tag")}
            ll = [self.nodes[nd.get("ref")] for nd in w.findall("nd") if nd.get("ref") in self.nodes]
            if len(ll) < 2:
                continue
            a = np.array(ll)
            x, y = bl.enu(a[:, 0], a[:, 1])
            self.ways.append({"id": w.get("id"), "tags": tags, "xy": np.c_[x, y]})

    def select(self, pred, box):
        out = []
        for w in self.ways:
            c = w["xy"].mean(0)
            if box[0] <= c[0] <= box[2] and box[1] <= c[1] <= box[3] and pred(w["tags"]):
                out.append(w)
        return out


def resample_line(xy, step):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(xy, axis=0), axis=1))]
    if d[-1] < 1e-6:
        return xy[:1]
    s = np.linspace(0, d[-1], max(2, int(math.ceil(d[-1] / step)) + 1))
    return np.c_[np.interp(s, d, xy[:, 0]), np.interp(s, d, xy[:, 1])]


def seam_far(P, j, name="ring"):
    """A closed ring (first point IDENTICAL to the last) restarted at its vertex j: the same closed point list rotated, so
    every vertex and every segment, the closing one included, is unchanged (Buttonwillow round 12, declared_walls
    seam='far'). A ring whose ends are not identical is refused: dropping or snapping a point would change its closing
    segment (GPT 6 Astra review of round 12)."""
    P = np.asarray(P)
    if len(P) < 4 or not np.array_equal(P[0], P[-1]):
        raise SystemExit(f"declared wall {name}: seam='far' needs a closed ring whose first point is identical to its last "
                         f"(ends {P[0].tolist()} / {P[-1].tolist()})")
    Q = P[:-1]
    j = int(j) % len(Q)
    return np.vstack([np.roll(Q, -j, axis=0), Q[j:j + 1]])


def grid_index(G, x, y):
    box = G["box"]
    c = np.clip(((np.asarray(x) - box[0]) / CELL).astype(int), 0, G["DEM"].shape[1] - 1)
    r = np.clip(((np.asarray(y) - box[1]) / CELL).astype(int), 0, G["DEM"].shape[0] - 1)
    return r, c


def poly_mask(G, xy):
    """Boolean grid mask of a polygon (ENU)."""
    from PIL import Image, ImageDraw

    box = G["box"]
    ny, nx = G["DEM"].shape
    im = Image.new("L", (nx, ny), 0)
    pts = [((x - box[0]) / CELL, (y - box[1]) / CELL) for x, y in xy]
    ImageDraw.Draw(im).polygon(pts, fill=1)
    return np.asarray(im).astype(bool)


# ---------------------------------------------------------------- buildings
BUILDING_KIND = {"grandstand": "grandstand", "garage": "garage", "terrace": "tower"}


TERRACE_FOOTPRINTS = {}   # OSM id -> ENU footprint of a grandstand built as a terrace (config scenery.terraces)
_OVERRIDES_USED = set()


def building_override(w, xy):
    """Evidence-declared building override (config scenery.building_overrides, 20 Oct 2026), used only where a newer
    source than the 2022-24 lidar contradicts it (source precedence: recent onboard > 2026 satellite > NAIP > OSM >
    lidar). Each entry: {osm: way id | contains: (lat, lon) inside the footprint, h: metres | drop: True, src: the
    evidence, naming the newer source}. Returns the matching entry or None."""
    from shapely.geometry import Point, Polygon
    for k, ov in enumerate(SC_CFG.get("building_overrides", [])):
        if not ov.get("src"):
            raise SystemExit(f"building_overrides[{k}]: no evidence (src) given")
        if ("h" in ov) == bool(ov.get("drop")) and not (ov.get("plain") and not ov.get("drop")):
            raise SystemExit(f"building_overrides[{k}]: give exactly one of h or drop (or plain=True)")
        hit = ov.get("osm") is not None and str(ov["osm"]) == str(w["id"])
        if not hit and ov.get("contains") is not None:
            p = bl.enu(*ov["contains"])
            hit = bool(Polygon(xy).buffer(0).contains(Point(float(p[0]), float(p[1]))))
        if hit:
            _OVERRIDES_USED.add(k)
            return ov
    return None


def buildings(trk, G, osm):
    CHM = np.nan_to_num(G["DSM"] - G["DEM"], nan=0.0)
    out, taken = [], np.zeros_like(CHM, bool)
    terr_ids = {str(t["osm"]) for t in SC_CFG.get("terraces", []) if t.get("osm")}
    TERRACE_FOOTPRINTS.clear(); _OVERRIDES_USED.clear()
    for w in osm.select(lambda t: "building" in t, trk.box):
        xy = w["xy"]
        if np.linalg.norm(xy[0] - xy[-1]) < 0.5:
            xy = xy[:-1]
        if len(xy) < 3:
            continue
        m = poly_mask(G, xy)
        if m.sum() < 4:
            continue
        taken |= ndi.binary_dilation(m, iterations=2)
        if w["id"] in terr_ids:
            TERRACE_FOOTPRINTS[w["id"]] = xy   # stepped rows on the hillside instead of a slab (terraces())
            continue
        hv = CHM[m]
        if SC_CFG.get("building_height_robust"):
            # robust height (config scenery.building_height_robust, 20 Oct 2026; Sonoma: the p85 rule made a 25.6 m block of
            # the 2-3 storey suites at the line, from the timing tower, light masts and the hillside in the footprint): the
            # 60th percentile of the lidar surface above the footprint's ground; where the lidar is inconsistent (p90 - p50
            # over 6 m: a mast, a tower or a slope inside the outline) the p50; no structure above 2.5 m (p90 under 2.5 m):
            # the footprint is dropped (an outline OSM keeps of something no longer standing, or flat pavement)
            p50, p60, p90 = (float(v) for v in np.percentile(hv, [50, 60, 90]))
            if p90 < 2.5:
                log(f"building {w['id']} ({w['tags'].get('name', '')}): no lidar structure above 2.5 m (p90 {p90:.1f} m), dropped")
                continue
            h = p60
            if p90 - p50 > 6.0:
                log(f"building {w['id']} ({w['tags'].get('name', '')}): lidar inconsistent (p50 {p50:.1f}, p90 {p90:.1f} m), "
                    f"height capped at the p50")
                h = p50
            h = min(max(h, 2.5), 30.0)
        else:
            h = float(np.percentile(hv, 85)) if (hv > 2).mean() > 0.3 else 0.0
            lv = w["tags"].get("building:levels")
            if h < 2.5:
                h = float(lv) * 3.2 if lv else 4.0
            h = min(max(h, 2.5), 30.0)
        ov = building_override(w, xy)
        if ov is not None:
            # a newer source contradicts the lidar (config scenery.building_overrides): its height, or no building
            p50_, p90_ = (float(v) for v in np.percentile(hv, [50, 90]))
            if ov.get("drop"):
                log(f"building {w['id']} ({w['tags'].get('name', '')}): DROPPED by evidence override (lidar 2022-24 p50 "
                    f"{p50_:.1f} / p90 {p90_:.1f} m, would have been {h:.1f} m): {ov['src']}")
                continue
            if "h" in ov:
                log(f"building {w['id']} ({w['tags'].get('name', '')}): height {h:.1f} -> {float(ov['h']):.1f} m by evidence "
                    f"override (lidar 2022-24 p50 {p50_:.1f} / p90 {p90_:.1f} m): {ov['src']}")
                h = float(ov["h"])
            if ov.get("plain"):
                log(f"building {w['id']} ({w['tags'].get('name', '')}): plain walls (no window / door facade) by evidence override: {ov['src']}")
        kind = BUILDING_KIND.get(w["tags"]["building"], "building")
        if w["id"] in HANGARS:
            kind = "hangar"
        if w["tags"].get("name") == "Tower":
            kind = "tower"
        zb = float(np.min(trk.ground(xy[:, 0], xy[:, 1])))
        if kind == "grandstand" and SC_CFG.get("grandstand_on_terrain"):
            # hillside stands (Sonoma, 20 Oct 2026): the seating lies on the slope, so the bare-earth DEM already holds
            # most of the rise and the lidar height above it is small; the stand spans the terrain rise across its
            # footprint plus its own structure (config scenery.grandstand_on_terrain; off for Laguna's package)
            gz = trk.ground(xy[:, 0], xy[:, 1])
            h = float(gz.max() - gz.min()) + max(float(np.percentile(hv, 85)), 2.0)
            h = min(h, 40.0)
        out.append({"kind": kind, "name": HANGARS.get(w["id"], w["tags"].get("name", "")), "z": rnd(zb, 2), "h": rnd(h, 1),
                    "footprint": [[rnd(x, 1), rnd(y, 1)] for x, y in xy], "src": "osm",
                    **({"plain": True} if ov is not None and ov.get("plain") else {})})
    n_osm = len(out)
    unused = [k for k in range(len(SC_CFG.get("building_overrides", []))) if k not in _OVERRIDES_USED]
    if unused:
        raise SystemExit(f"building_overrides {unused}: matched no OSM building footprint")
    # unmapped structures: tall, single-return (roof-like), compact blobs away from the track
    flat = (CHM > 2.5) & (G["MULTI"] < 0.12) & ~taken
    flat = ndi.binary_opening(flat, iterations=1)
    lab, nl = ndi.label(flat)
    from shapely.geometry import MultiPoint

    box = G["box"]
    for k, sl in enumerate(ndi.find_objects(lab), 1):
        m = lab[sl] == k
        area = m.sum() * CELL * CELL
        if area < 45 or area > 6000:
            continue
        rr, cc = np.nonzero(m)
        x = box[0] + (cc + sl[1].start + 0.5) * CELL
        y = box[1] + (rr + sl[0].start + 0.5) * CELL
        _, _, dout = trk.project(np.c_[x, y])
        if dout.min() < 3:  # bridges, gantries
            continue
        rect = MultiPoint(np.c_[x, y]).minimum_rotated_rectangle
        if area / max(rect.area, 1) < 0.6:  # irregular blob: tree clump or clutter
            continue
        h = float(np.percentile(CHM[sl][m], 80))
        rough = float(np.std(CHM[sl][m]))
        if rough > 2.5:
            continue
        xy = np.array(rect.exterior.coords)[:-1]
        zb = float(np.min(trk.ground(xy[:, 0], xy[:, 1])))
        out.append({"kind": "building", "name": "", "z": rnd(zb, 2), "h": rnd(min(h, 15), 1),
                    "footprint": [[rnd(a, 1), rnd(b, 1)] for a, b in xy], "src": "lidar"})
        taken[sl] |= ndi.binary_dilation(m, iterations=2)
    log(f"buildings: {n_osm} from OSM footprints, {len(out) - n_osm} unmapped structures from the lidar")
    # the evidence of each building the coverage gate checks (config scenery.building_evidence, 21 Oct 2026): {contains:
    # (lat, lon) inside the footprint, src: the capture / onboard evidence | drop: True with src: why there is none}; a
    # building with no source in the 2026 evidence is removed (no object without a cited source); an entry that
    # matches no footprint fails the stage
    from shapely.geometry import Point, Polygon
    for k, ev in enumerate(SC_CFG.get("building_evidence", [])):
        if not ev.get("src"):
            raise SystemExit(f"building_evidence[{k}]: no src")
        p = Point(*bl.enu(*ev["contains"]))
        hit = [j for j, b_ in enumerate(out) if b_ is not None and Polygon(b_["footprint"]).buffer(0).contains(p)]
        if len(hit) != 1:
            raise SystemExit(f"building_evidence[{k}] at {ev['contains']}: {len(hit)} footprints contain it")
        b_ = out[hit[0]]
        if ev.get("drop"):
            log(f"building ({b_['src']}, {b_['h']} m) at {ev['contains']}: removed, no 2026 evidence: {ev['src']}")
            out[hit[0]] = None
        else:
            b_["src"] = f"{b_['src']} ({ev['src']})"
    out = [b_ for b_ in out if b_ is not None]
    return out, taken


def terraces(trk):
    """Grandstands built into a hillside as stepped concrete rows (config scenery.terraces, 20 Oct 2026; Sonoma's stands
    are terraces cut into the hills, not slabs): each {name, osm (way id) | footprint [(lat, lon), ...], run (m, default
    0.9), fence (top fence, default True), src}. The rows run along the contour: their direction is perpendicular to the
    uphill direction of a plane fitted to the DEM over the footprint (away from the track where the ground is flat);
    row r's tread is the median ground along its centre line, at least 0.15 m above the row below; the riser of row 0
    starts on the ground. Returns (terraces for scenery.json, fence barrier runs)."""
    from shapely.geometry import LineString, Polygon
    out, fences = [], []
    for tc in SC_CFG.get("terraces", []):
        if tc.get("front"):
            t_, f_ = terrace_measured(trk, tc)
            if t_:
                out.append(t_); fences.extend(f_)
            continue
        if tc.get("osm"):
            xy = TERRACE_FOOTPRINTS.get(str(tc["osm"]))
            if xy is None:
                log(f"terrace {tc['name']}: OSM way {tc['osm']} not found"); continue
        else:
            ll = np.array(tc["footprint"], float); xy = np.c_[bl.enu(ll[:, 0], ll[:, 1])]
        poly = Polygon(xy)
        if not poly.is_valid:
            poly = poly.buffer(0)
        # uphill direction from a plane fit to the DEM inside the footprint
        mn = np.array(poly.bounds[:2]); mx = np.array(poly.bounds[2:])
        gx, gy = np.meshgrid(np.arange(mn[0], mx[0], 2.0), np.arange(mn[1], mx[1], 2.0))
        from shapely import contains_xy
        inside = contains_xy(poly, gx.ravel(), gy.ravel())
        X, Y = gx.ravel()[inside], gy.ravel()[inside]
        Z = trk.ground(X, Y)
        A = np.c_[X - X.mean(), Y - Y.mean(), np.ones(len(X))]
        (ax, ay, _), *_ = np.linalg.lstsq(A, Z, rcond=None)
        slope = math.hypot(ax, ay)
        c = np.array(poly.centroid.coords[0])
        if slope > 0.05:
            u = np.array([ax, ay]) / slope
        else:
            i_, _, _ = trk.project(c[None]); u = c - trk.C[i_[0], :2]; u /= np.linalg.norm(u)
        v = np.array([-u[1], u[0]])
        P = np.asarray(poly.exterior.coords)
        t = (P - c) @ u
        run = tc.get("run", 0.9)
        rows, zprev = [], None
        nrow = int((t.max() - t.min()) / run)
        L = 2 * float(np.abs((P - c) @ v).max()) + 10
        for r in range(nrow):
            tm = t.min() + (r + 0.5) * run
            seg = poly.intersection(LineString([c + u * tm - v * L, c + u * tm + v * L]))
            if seg.is_empty:
                continue
            if seg.geom_type != "LineString":
                seg = max(getattr(seg, "geoms", [seg]), key=lambda g: g.length)
            a, b = np.array(seg.coords[0]), np.array(seg.coords[-1])
            if np.linalg.norm(b - a) < 2:
                continue
            q = a[None] + (b - a)[None] * np.linspace(0, 1, 9)[:, None]
            z = float(np.median(trk.ground(q[:, 0], q[:, 1])))
            z0 = z if zprev is None else max(z, zprev + 0.15)
            rows.append({"a": [rnd(a[0], 2), rnd(a[1], 2)], "b": [rnd(b[0], 2), rnd(b[1], 2)], "z": rnd(z0, 2)})
            zprev = z0
        if not rows:
            continue
        rise = np.diff([r_["z"] for r_ in rows])
        f = rows[0]
        zg0 = float(np.min(trk.ground(np.array([f["a"][0], f["b"][0]]), np.array([f["a"][1], f["b"][1]]))))
        out.append({"name": tc["name"], "src": tc["src"], "run": run, "dir": [rnd(u[0], 4), rnd(u[1], 4)],
                    "z_ground_front": rnd(zg0, 2), "rows": rows})
        if tc.get("fence", True):
            top = rows[-1]
            Pf = np.array([top["a"], top["b"]], float) + u * run / 2
            Pf = resample_line(Pf, 3.0)
            fences.append({"kind": "fence", "h": 0.0, "fence": 1.8, "pts": with_z(trk, Pf),
                           "src": f"terrace {tc['name']} top fence ({tc.get('fence_src', tc['src'])})"})
        log(f"terrace {tc['name']}: {len(rows)} rows of {run} m, rise p50 {np.median(rise) if len(rise) else 0:.2f} m "
            f"(p10 {np.percentile(rise, 10) if len(rise) else 0:.2f}, p90 {np.percentile(rise, 90) if len(rise) else 0:.2f}), "
            f"hillside slope {slope:.2f}, total rise {rows[-1]['z'] - rows[0]['z']:.1f} m")
    return out, fences


def terrace_measured(trk, tc):
    """A terrace declared by its measured footprint (config scenery.terraces `front` / `back`, Sonoma round 6, 21 Oct 2026):
    two lat/lon polylines of equal length, matched by index: the lower edge of the seating field and its upper edge on the
    same measurement ray (compare/terrace_measure.py: the row texture on the 2026 captures, the DEM crest less 3 m where
    the captures end). The rows follow the stand: row k is the curve at (k + 0.5) * run up each ray, present where the
    ray's depth holds the whole tread; each vertex's tread sits on the ground at the tread's back (uphill) edge, at least
    0.15 m above the row below; its riser runs down to the row below (row 0: to the ground at the tread's front edge).
    The OSM way (`osm`) only marks the slab the terrace replaces. Rows carry `pts` [x, y, z, z_low, m] (m: metres along
    the front line) and `nrm` (the uphill unit vector per vertex) besides the a / b / z of the straight rows."""
    F = np.array([bl.enu(la, lo) for la, lo in tc["front"]], float)
    B = np.array([bl.enu(la, lo) for la, lo in tc["back"]], float)
    if len(F) != len(B) or len(F) < 2:
        raise SystemExit(f"terrace {tc['name']}: front and back need the same number (>= 2) of points")
    D = B - F
    depth = np.linalg.norm(D, axis=1)
    U = D / np.maximum(depth, 1e-6)[:, None]
    M = np.r_[0, np.cumsum(np.linalg.norm(np.diff(F, axis=0), axis=1))]
    run = float(tc.get("run", 0.9)); h = run / 2
    nrow = int(depth.max() / run)
    rows, zprev = [], np.full(len(F), np.nan)
    for k in range(nrow):
        d = (k + 0.5) * run
        present = d + h <= depth + 0.3
        V = F + U * d
        zb = trk.ground(V[:, 0] + U[:, 0] * h, V[:, 1] + U[:, 1] * h)
        zf = trk.ground(V[:, 0] - U[:, 0] * h, V[:, 1] - U[:, 1] * h)
        zb = np.maximum(zb, ndi.median_filter(zb, 3, mode="nearest"))
        zlow = np.where(np.isfinite(zprev), zprev, zf)
        z = np.maximum(zb, zlow + 0.15)
        znew = np.full(len(F), np.nan)
        lab, nl = ndi.label(present)
        for j in range(1, nl + 1):
            ii = np.where(lab == j)[0]
            if len(ii) < 2:
                continue
            znew[ii] = z[ii]
            pts = [[rnd(V[i, 0], 2), rnd(V[i, 1], 2), rnd(z[i], 2), rnd(zlow[i], 2), rnd(M[i], 2)] for i in ii]
            rows.append({"a": pts[0][:2], "b": pts[-1][:2], "z": rnd(float(z[ii].min()), 2), "k": k, "pts": pts,
                         "nrm": [[rnd(U[i, 0], 4), rnd(U[i, 1], 4)] for i in ii]})
        zprev = znew
    if not rows:
        log(f"terrace {tc['name']}: no rows (depth {depth.max():.1f} m < run {run} m)")
        return None, []
    u = U.mean(0); u /= np.linalg.norm(u)
    zg0 = min(min(p[3] for p in r["pts"]) for r in rows if r["k"] == 0) if any(r["k"] == 0 for r in rows) else rows[0]["z"]
    t_ = {"name": tc["name"], "src": tc["src"], "run": run, "dir": [rnd(u[0], 4), rnd(u[1], 4)], "z_ground_front": rnd(zg0, 2),
          "rows": rows}
    fences = []
    if tc.get("fence", True):
        Pf = resample_line(B, 3.0)
        fences.append({"kind": "fence", "h": 0.0, "fence": 1.8, "pts": with_z(trk, Pf),
                       "src": f"terrace {tc['name']} top fence ({tc.get('fence_src', tc['src'])})"})
    area = float(np.sum((depth[1:] + depth[:-1]) / 2 * np.diff(M)))
    log(f"terrace {tc['name']}: measured footprint, {len(F)} rays over {M[-1]:.0f} m, depth {depth.min():.1f}-{depth.max():.1f} m "
        f"({area:.0f} m2), {nrow} rows of {run} m in {len(rows)} pieces, rise {rows[-1]['z'] - rows[0]['z']:.1f} m")
    return t_, fences


# ---------------------------------------------------------------- trees
def trees(trk, G, taken):
    CHM = np.nan_to_num(G["UNC"] - G["DEM"], nan=0.0)
    CHM[CHM < 0] = 0
    box = G["box"]
    ny, nx = CHM.shape
    gx = box[0] + (np.arange(nx) + 0.5) * CELL
    gy = box[1] + (np.arange(ny) + 0.5) * CELL
    # keep away from the track surface (bridges, gantries) and from buildings
    GX, GY = np.meshgrid(gx[::2], gy[::2])
    _, _, dout = trk.project(np.c_[GX.ravel(), GY.ravel()])
    near = np.repeat(np.repeat((dout < 1.5).reshape(GX.shape), 2, 0), 2, 1)[:ny, :nx]
    veg = (CHM > 2.0) & (G["MULTI"] > 0.18) & ~taken & ~near
    veg = ndi.binary_opening(veg, iterations=1)
    S = ndi.gaussian_filter(np.where(veg, CHM, 0), 1.0)
    peaks = (S == ndi.maximum_filter(S, size=9)) & (S > 3.0) & veg
    pr, pc = np.nonzero(peaks)
    log(f"trees: {len(pr)} crown maxima above 3 m")
    # crowns: canopy pixels assigned to the nearest maximum (within 12 m)
    marker = np.zeros_like(CHM, np.int32)
    marker[pr, pc] = np.arange(1, len(pr) + 1)
    dist, (ir, ic) = ndi.distance_transform_edt(marker == 0, return_indices=True)
    owner = marker[ir, ic]
    canopy = (CHM > 2.0) & (G["MULTI"] > 0.1) & (dist < 12) & ~taken
    area = np.bincount(owner[canopy], minlength=len(pr) + 1)[1:] * CELL * CELL
    hmax = ndi.maximum_filter(CHM, size=5)[pr, pc]
    rad = np.clip(np.sqrt(area / np.pi), 1.2, 11.0)
    x = gx[pc]
    y = gy[pr]
    z = trk.ground(x, y)
    keep = hmax > 3.0
    canopy_ok = canopy_check(trk, x, y, rad)
    log(f"trees: imagery check (a dark canopy blob in the NAIP image under the crown) rejects {int((keep & ~canopy_ok).sum())} "
        f"of {int(keep.sum())} lidar crowns (poles, towers, fences, light masts)"
        + ("" if SC_CFG.get("tree_imagery_check", True) else "; NOT applied (config scenery.tree_imagery_check False)"))
    if SC_CFG.get("tree_imagery_check", True):
        keep &= canopy_ok
    tm = SC_CFG.get("tree_min")
    if tm:
        # round 8 (Buttonwillow owner lap 2 note 16): with the NAIP check off (it rejected 243 of 273 lidar crowns, the
        # infield's willow / eucalyptus rows among them), poles, masts and fence posts are kept out by their crown: a
        # crown at least `radius` m and `height` m
        small = (rad < tm.get("radius", 3.0)) | (hmax < tm.get("height", 6.0))
        log(f"trees: tree_min drops {int((keep & small).sum())} small crowns (radius < {tm.get('radius', 3.0)} m or height < {tm.get('height', 6.0)} m)")
        keep &= ~small
    mc = SC_CFG.get("tree_mast_clear")
    if mc:
        # round 11 (Buttonwillow judge r10 fwd_10 / fwd_11 / back_05: the 49.5 m lattice mast at s 3445 L read as a solid
        # green column): a lattice tower's lidar returns are multi-return like a crown, so the rule made a 49.8 m tree on
        # the mast; no crown within `radius` m of a declared light mast (scenery.light_masts)
        M_ = np.array([bl.enu(*lm["latlon"]) for lm in SC_CFG.get("light_masts", [])], float).reshape(-1, 2)
        if len(M_):
            dm = np.min(np.hypot(x[:, None] - M_[None, :, 0], y[:, None] - M_[None, :, 1]), 1)
            on = keep & (dm < float(mc.get("radius", 6.0)))
            for k_ in np.flatnonzero(on):
                log(f"trees: crown on a light mast dropped at ({x[k_]:.1f}, {y[k_]:.1f}), {hmax[k_]:.1f} m high, {dm[k_]:.1f} m from the mast")
            keep &= ~on
    T = np.c_[x, y, z, hmax, rad][keep]
    log(f"trees: {len(T)} crowns; height p10/p50/p90 {np.percentile(T[:, 3], [10, 50, 90]).round(1)} m, "
        f"radius p50 {np.median(T[:, 4]):.1f} m")
    return T


def canopy_check(trk, x, y, rad):
    """True where a tree is visible in the image (20 Oct 2026: the lidar rule alone, class-1 height over 2 m with a
    multi-return share over 0.18, made trees of light masts, towers and fences on Sonoma's infield and drag strip): at
    least 30 % of the NAIP pixels within 0.6 crown radius (at least 1.5 m) are canopy, i.e. darker than the ground around
    the image's 35th percentile and green."""
    from PIL import Image
    o = trk.t["ortho"]
    raw = os.path.join(CACHE, f"naip_{int(o['x0'])}_{int(o['y0'])}_{int(o['x1'])}_{int(o['y1'])}_{o['width_px']}x{o['height_px']}.png")
    im = np.asarray(Image.open(raw).convert("RGB")).astype(float)
    H, W, _ = im.shape
    lum = im.mean(2)
    sx = (o["x1"] - o["x0"]) / W
    # canopy: darker than the image's 35th percentile (trees are among the darkest cover in a summer NAIP frame; a LOCAL
    # reference failed in dense oak stands, where the neighbourhood is canopy too) and green rather than the neutral grey
    # of asphalt. Masts, towers and fences are thin and stand on pavement or dry grass: under 30 % of the crown disc.
    p35, p15 = np.percentile(lum, [35, 15])
    green = im[..., 1] - np.maximum(im[..., 0], im[..., 2]) > 2    # not the neutral grey of asphalt or concrete
    canopy = (lum < p35) & green
    del p15
    ok = np.zeros(len(x), bool)
    for k, (xx, yy, rr) in enumerate(zip(x, y, rad)):
        r_px = max(1.5, 0.6 * rr) / sx
        c = (xx - o["x0"]) / sx; r = (o["y1"] - yy) / sx
        c0, c1 = int(max(0, c - r_px)), int(min(W, c + r_px + 1)); r0, r1 = int(max(0, r - r_px)), int(min(H, r + r_px + 1))
        if c1 <= c0 or r1 <= r0: continue
        yy_, xx_ = np.mgrid[r0:r1, c0:c1]
        m = (yy_ - r) ** 2 + (xx_ - c) ** 2 <= r_px ** 2
        ok[k] = canopy[r0:r1, c0:c1][m].mean() >= 0.3 if m.any() else False
    return ok


# ---------------------------------------------------------------- bridges
def bridge_stations(trk, osm):
    """Stations where OSM bridge=yes ways cross the circuit (the crossing logic of bridges(), without the lidar)."""
    out = []
    for w in osm.select(lambda t: t.get("bridge") == "yes", trk.box):
        xy = resample_line(w["xy"], 0.5)
        i, lat, dout = trk.project(xy)
        on = dout < 0
        if not on.any():
            continue
        out.append(int(i[np.argmin(np.abs(lat) + 1000 * ~on)]))
    return sorted(out)


def bridges(trk, G, osm):
    out = []
    BRG = G["BRG"]
    DSM = G["DSM"]
    for w in osm.select(lambda t: t.get("bridge") == "yes", trk.box):
        xy = resample_line(w["xy"], 0.5)
        i, lat, dout = trk.project(xy)
        on = dout < 0
        if not on.any():
            continue  # bridge not over the circuit
        # crossing station and the span over the track (+ margins)
        k = np.argmin(np.abs(lat) + 1000 * ~on)
        st = int(i[k])
        r, c = grid_index(G, xy[:, 0], xy[:, 1])
        zt = float(trk.C[st, 2])
        cand = BRG[r, c]
        cand = cand[np.isfinite(cand) & (cand > zt + 3)]
        if len(cand) < 3:
            cand = DSM[r[on], c[on]]
            cand = cand[np.isfinite(cand) & (cand > zt + 3.5) & (cand < zt + 12)]
        deck = float(np.median(cand)) if len(cand) >= 3 else zt + 6.0
        src = "lidar" if len(cand) >= 3 else "default"
        # span: the part of the OSM way within 25 m of the track edge (covers the pit lane at S/F), at least 5 m
        # beyond each edge
        near = np.nonzero(dout < 25)[0]
        p0, p1 = xy[near[0]], xy[near[-1]]
        d = (p1 - p0) / max(np.linalg.norm(p1 - p0), 1e-6)
        _, _, d0 = trk.project(p0[None])
        _, _, d1 = trk.project(p1[None])
        p0 = p0 - d * max(0.0, 5 - d0[0])
        p1 = p1 + d * max(0.0, 5 - d1[0])
        name = w["tags"].get("name", "")
        kind = "road" if w["tags"].get("highway") not in ("footway", "path") else "foot"
        rec = {"id": w["id"], "kind": kind, "name": name, "s": st, "deck_z": rnd(deck, 2),
               "a": [rnd(p0[0], 1), rnd(p0[1], 1)], "b": [rnd(p1[0], 1), rnd(p1[1], 1)],
               "width": 3.0 if kind == "foot" else 8.0, "deck_src": src}
        if SC_CFG.get("bridge_stairs"):
            # the deck meets the banks (config scenery.bridge_stairs, 20 Oct 2026; Sonoma owner note 29: "a walk way
            # suspended in air"): at each end of the span an abutment from the ground (DEM) up to the deck, and a stair
            # flight on along the OSM way down to the ground at 30 degrees (Street View owner_28: piers and stairs
            # into the banks at both ends)
            ends = []
            for pe, dirn in ((p0, -d), (p1, d)):
                zg = float(trk.ground(*pe)[0])
                rise = deck - zg
                q = pe.copy()
                for _ in range(3):
                    q = pe + dirn * max(rise, 0.0) * 1.73
                    rise = deck - float(trk.ground(*q)[0])
                zq = float(trk.ground(*q)[0])
                ends.append({"at": [rnd(pe[0], 1), rnd(pe[1], 1)], "z_ground": rnd(zg, 2),
                             "to": [rnd(q[0], 1), rnd(q[1], 1)], "z_to": rnd(zq, 2)})
                log(f"bridge {w['id']}: end at ({pe[0]:.0f}, {pe[1]:.0f}) {deck - zg:.1f} m above the ground, stairs "
                    f"{np.linalg.norm(q - pe):.1f} m on along the way")
            rec["ends"] = ends
        out.append(rec)
    out.sort(key=lambda b: b["s"])
    for b in out:
        log(f"bridge {b['id']} {b['kind']} over s={b['s']} deck {b['deck_z'] - trk.C[b['s'], 2]:.1f} m above track ({b['deck_src']})")
    return out


# ---------------------------------------------------------------- barriers
# Tyre walls on the outside of the big stops: config scenery.tyre_corners = (turn in track.json corners, metres before,
# metres after the corner's s). Side is derived from the corner direction (outside = right for a left-hander), so the
# placement follows a rebuilt track.
TYRE_CORNERS = []


def polyline_runs(trk, xy, step=2.0, min_out=2.0, max_out=70.0, min_len=6.0):
    """Resample, push points that sit closer than min_out to the edge out to min_out, drop points on the
    track or far away, and split into continuous runs."""
    P = resample_line(xy, step)
    i, lat, dout = trk.project(P)
    keep = (dout > -1.0) & (dout < max_out)
    push = keep & (dout < min_out)
    side = np.sign(lat)
    P[push] = trk.C[i[push], :2] + trk.N[i[push]] * (side[push] * (trk.hw(i[push], side[push]) + min_out))[:, None]
    runs, cur = [], []
    for k in range(len(P)):
        if keep[k]:
            cur.append(P[k])
        elif cur:
            runs.append(np.array(cur))
            cur = []
    if cur:
        runs.append(np.array(cur))
    return [r for r in runs if len(r) >= 2 and np.linalg.norm(np.diff(r, axis=0), axis=1).sum() >= min_len]


def with_z(trk, P, dz=0.0):
    z = trk.ground(P[:, 0], P[:, 1]) + dz
    return [[rnd(a, 2), rnd(b, 2), rnd(c, 2)] for (a, b), c in zip(P, z)]


def edge_line(trk, s0, s1, side, extra, step=2):
    st = np.arange(s0, s1 + 1, step) % trk.n
    ex = np.broadcast_to(np.asarray(extra, float), st.shape)
    return trk.C[st, :2] + trk.N[st] * (side * (trk.hw(st, side) + ex))[:, None]


def _runs(mask):
    """(start, end) index pairs of the True runs of a boolean array"""
    out, a = [], None
    for i, v in enumerate(mask):
        if v and a is None: a = i
        if not v and a is not None: out.append((a, i - 1)); a = None
    if a is not None: out.append((a, len(mask) - 1))
    return out


def _pit_wall_rule(trk, way, pwc, edge=None):
    """The rule-placed pit wall (was inline in barriers()): left of the front straight wherever the OSM pit-lane `way`
    runs alongside, 0.6 m off the left edge (off `edge`, a per-station lateral, with pit_wall.at 'first_edge'), fenced
    to fence_until_m past the line. pwc = config scenery.pit_wall ({}: the defaults, stage 1's pit_wall_line)."""
    out = []
    PL = resample_line(way["xy"], 2.0)
    i, lat, dout = trk.project(PL)
    m = (lat > 0) & (dout > 2) & (dout < 25)
    ss = np.sort(i[m])
    # the pit lane straddles s = 0: take the contiguous wrap-around range
    gaps = np.diff(ss)
    if len(ss):
        if gaps.max(initial=0) > 500:
            cut = np.argmax(gaps)
            s0, s1 = int(ss[cut + 1]), int(ss[cut]) + trk.n
        else:
            s0, s1 = int(ss[0]), int(ss[-1])
        s0, s1 = s0 + 15, s1 - 10
        # Laguna: the real pit wall ends at the T1 kink; the pit-exit lane down to the Andretti hairpin has no wall
        if pwc.get("end_after_line_m") is not None:
            s1 = min(s1, trk.n + int(pwc["end_after_line_m"]))
        # catch fence on the front straight only (to ~120 m past the line at Laguna); the rest of the wall is bare
        mid = min(max(trk.n + int(pwc.get("fence_until_m", 120)), s0 + 2), s1)
        at = pwc.get("at")
        if at == "midway":
            # 20 Oct 2026 (Sonoma: a wall 0.6 m off the outside edge of the T11 hairpin, where the pit road runs
            # round the outside 10-15 m away, put the hot-lap launch into it): the wall stands halfway between the
            # track edge and the pit lane's near edge, and only where the centre radius is over min_radius (the pit
            # lane runs alongside a straight), never 0.6 m off a corner's outside edge
            dist = np.full(trk.n, np.nan)
            ii_, ll_, dd_ = trk.project(PL)
            for k_, d_ in zip(ii_[ll_ > 0], dd_[ll_ > 0]):
                if 2 < d_ < 25: dist[k_] = d_ if np.isnan(dist[k_]) else min(dist[k_], d_)
            idx_ = np.arange(trk.n); okd = np.isfinite(dist)
            dist = np.interp(idx_, idx_[okd], dist[okd], period=trk.n)
            lane_half = PIT_HALF_DEFAULT
            kap_ = np.abs(bl.curvature(trk.C[:, :2], sigma=5))
            straightish = (1 / np.maximum(kap_, 1e-6)) > pwc.get("min_radius", 150.0)
        for a, b_, fence in ((s0, mid, 3.5), (mid, s1, 0.0)):
            if b_ - a >= 4 and at == "midway":
                st_all = np.arange(a, b_ + 1) % trk.n
                for ra, rb in [(r0, r1) for r0, r1 in _runs(straightish[st_all])]:
                    if rb - ra < 8: continue
                    st_ = st_all[ra:rb + 1]
                    ex = np.maximum((dist[st_] - lane_half) / 2.0, 0.6)
                    exs = np.interp(np.arange(a + ra, a + rb + 1, 2), np.arange(a + ra, a + rb + 1), ex)
                    P = edge_line(trk, int(a + ra), int(a + rb), +1, exs)
                    out.append({"kind": "pitwall", "h": 1.1, "fence": fence, "pts": with_z(trk, P),
                                "src": "OSM pit lane extent, halfway to the pit lane, straights only"})
                continue
            if b_ - a >= 4:
                ex = 0.6
                if edge is not None:
                    # the wall stays 0.6 m off the first build's NAIP asphalt edge (the asphalt runs to the wall),
                    # not off the painted edge (config pit_wall.at = 'first_edge')
                    st_ = np.arange(a, b_ + 1, 2) % trk.n
                    ex = np.maximum(edge[st_] - trk.hl[st_], 0.0) + 0.6
                P = edge_line(trk, a, b_, +1, ex)
                out.append({"kind": "pitwall", "h": 1.1, "fence": fence, "pts": with_z(trk, P),
                            "src": "OSM pit lane extent"})
        log(f"pit wall: s {s0 % trk.n}..{s1 % trk.n} ({s1 - s0} m)")
    return out


def pit_wall_line(trk, osm):
    """Stage 1's pit-wall polyline (straights fit 'pitwall', Laguna's front straight): the OSM rule wall with the default
    parameters, reading no scenery key (20 Oct 2026; it was barriers()' pitwall runs, which read scenery.pit_wall,
    declared_walls and pit_lane.walls). (k, 2) ENU points, or None without a pit-lane way."""
    pit = [w for w in osm.ways if w["tags"].get("name") == PIT_WAY]
    recs = _pit_wall_rule(trk, pit[0], {}) if pit else []
    return np.array([q[:2] for b in recs for q in b["pts"]]) if recs else None


DECLARED_WALLS = {}   # declared wall name -> [(ENU polyline, wall height)], for the boards and nose objects on them


def barriers(trk, osm):
    out = []
    DECLARED_WALLS.clear()
    walls = osm.select(lambda t: t.get("barrier") == "wall", trk.box)
    wall_pts = []
    # evidence overrides of OSM walls (config scenery.osm_barrier_overrides {way id: {kind, h, fence, color | drop,
    # src}}, 21 Oct 2026): OSM tags a tyre barrier as barrier=wall (note 'tire barrier'), or maps a line the captures show
    # as a duplicate of a measured declared wall; each use is logged, an unmatched id fails the stage
    ovr = {str(k): v for k, v in SC_CFG.get("osm_barrier_overrides", {}).items()}
    used = set()
    for w in walls:
        ov = ovr.get(str(w["id"]))
        if ov is not None:
            used.add(str(w["id"]))
            if not ov.get("src"):
                raise SystemExit(f"osm_barrier_overrides[{w['id']}]: no evidence (src) given")
            if ov.get("drop"):
                log(f"OSM wall {w['id']}: DROPPED by evidence override: {ov['src']}")
                continue
        for run in polyline_runs(trk, w["xy"]):
            i, lat, dout = trk.project(run)
            d = float(np.median(dout))
            # Close to the edge: concrete wall with catch fence (spectator banks, photo 01). Further out, behind
            # run-off: Armco on posts.
            kind = "concrete" if d < 14 else "armco"
            rec = {"kind": kind, "h": 1.0 if kind == "concrete" else 0.75,
                   "fence": 3.0 if kind == "concrete" else 0.0, "pts": with_z(trk, run), "src": f"osm:{w['id']}"}
            if ov is not None:
                rec.update({k: ov[k] for k in ("kind", "h", "fence", "color") if k in ov})
                rec["src"] = f"osm:{w['id']} ({ov['src']})"
                log(f"OSM wall {w['id']}: {kind} -> {rec['kind']} h {rec['h']} fence {rec['fence']} by evidence override")
            out.append(rec)
            wall_pts.append(np.c_[run, i, lat, dout])
    for k in set(ovr) - used:
        raise SystemExit(f"osm_barrier_overrides: OSM wall {k} not found in the box")
    W = np.concatenate(wall_pts) if wall_pts else np.zeros((0, 5))
    # tyre walls in front of the outside barrier of the big stops
    corners = {c["turn"]: c for c in trk.t["corners"] if c.get("turn")}
    for name, before, after in TYRE_CORNERS:
        c = corners[name]
        s0, s1 = c["s"] - before, c["s"] + after
        side = -1 if c["dir"] == "left" else 1
        st = np.arange(s0, s1 + 1, 2)
        d = np.full(len(st), np.nan)
        for k, s in enumerate(st):
            m = (np.abs(((W[:, 2] - s + trk.n / 2) % trk.n) - trk.n / 2) < 4) & (np.sign(W[:, 3]) == side) & \
                (W[:, 4] > 3.5) & (W[:, 4] < 45)
            if m.any():
                d[k] = W[m, 4].min() - 1.0
        if np.isfinite(d).sum() >= 3:
            ok = np.isfinite(d)
            d = np.interp(np.arange(len(d)), np.nonzero(ok)[0], d[ok])
            src = "in front of OSM wall"
        else:
            d = np.full(len(st), 12.0)
            src = "hand-placed 12 m outside the edge"
        d = ndi.median_filter(d, 5, mode="nearest")
        d = np.maximum(ndi.gaussian_filter1d(d, 2, mode="nearest"), 2.5)
        P = edge_line(trk, s0, s1, side, d)
        out.append({"kind": "tyres", "h": 1.0, "fence": 0.0, "pts": with_z(trk, P), "src": f"{name}: {src}"})
        log(f"tyre wall {name}: s {s0}-{s1}, {np.median(d):.1f} m outside the edge ({src})")
    # pit wall: left of the front straight wherever the pit lane runs alongside
    pit = [w for w in osm.ways if w["tags"].get("name") == PIT_WAY]
    if pit and SC_CFG.get("pit_wall", {}).get("rule", True) is False:
        log("pit wall: rule off (config scenery.pit_wall.rule False): every pit-side wall is declared from the evidence")
        pit = []
    if pit:
        out += _pit_wall_rule(trk, pit[0], SC_CFG.get("pit_wall", {}), PITWALL_EDGE)
    # declared walls (config scenery.declared_walls, 20 Oct 2026): runs OSM does not map, measured on the z20 captures as
    # lat/lon polylines (a declared fact like a corner anchor, not a geometry edit). A rule-placed pit wall within 3 m of
    # a declared wall is dropped there (the declared one is the measured position of the same wall).
    decl = []
    split = []
    work = []
    for dw in SC_CFG.get("declared_walls", []):
        validate_declared_wall(dw)
        if dw.get("w"):
            # round 14D: a thick wall is its two faces (thick_wall_faces); the app draws the box between them from the
            # front run (`box`), the back run draws no body (`hidden`) but carries the fence; both collide
            ll = np.array(dw["latlon"], float)
            x, y = bl.enu(ll[:, 0], ll[:, 1])
            Pc = resample_line(np.c_[x, y], 2.0)
            m_ = len(Pc) // 2
            t_ = Pc[min(m_ + 1, len(Pc) - 1)] - Pc[max(m_ - 1, 0)]
            n_ = np.array([-t_[1], t_[0]])
            i_, _, _ = trk.project(Pc[m_:m_ + 1])
            toward = 1 if float((trk.C[i_[0], :2] - Pc[m_]) @ n_) > 0 else -1
            Pf, Pb, side = thick_wall_faces(Pc, toward, float(dw["w"]))
            base = {k: v for k, v in dw.items() if k not in ("w", "latlon")}
            work.append((dict(base, name=dw["name"] + " (front face)", fence=0.0, fence_arm=None, _box=dict(w=float(dw["w"]), side=side), _wall_id=dw["name"][:80]), Pf))
            work.append((dict(base, _hidden=True, _wall_id=dw["name"][:80]), Pb))
            log(f"declared wall {dw['name']}: thick wall {dw['w']} m as two faces (front 'box', back 'hidden')")
        else:
            work.append((dw, None))
    # pit-lane walls with their own measured geometry (config pit_lane.walls[] with latlon, 21 Oct 2026); a pit-lane
    # wall that is one of the declared walls names it (`declared`) and adds no geometry
    PIT_MAT = {"pitbox_wall": ("concrete", "#e6e4de"), "jersey": ("concrete", "#e6e4de"), "board_wall": ("concrete", "#a9c9dd"),
               "concrete": ("concrete", "#a9c9dd"), "armco": ("armco", None), "fence": ("fence", None)}
    names = {dw["name"] for dw in SC_CFG.get("declared_walls", [])}
    for k, pw in enumerate(PIT_CFG.get("walls", [])):
        if pw.get("declared"):
            if pw["declared"] not in names:
                raise SystemExit(f"pit_lane.walls[{k}]: declared wall {pw['declared']!r} not in scenery.declared_walls")
            continue
        if not pw.get("latlon"):
            continue
        kind, col = PIT_MAT[pw.get("material", "concrete")]
        dw = {"name": pw.get("name", f"pit lane wall {k} ({pw['side']})"), "kind": kind, "h": pw.get("h", 1.0),
              "fence": pw.get("fence", 0.0), "latlon": pw["latlon"], "src": "pit lane: " + pw["src"]}
        if pw.get("color", col):
            dw["color"] = pw.get("color", col)
        work.append((dw, None))
    k_ = 0
    while k_ < len(work) or split:
        if k_ >= len(work):
            work += split; split = []
            continue
        dw, pre = work[k_]; k_ += 1
        if pre is not None:
            dw = dict(dw, drop_within=None, _pre=pre)
        if dw.get("_pre") is not None:
            x, y = dw["_pre"][:, 0], dw["_pre"][:, 1]
        else:
            ll = np.array(dw["latlon"], float)
            x, y = bl.enu(ll[:, 0], ll[:, 1])
        P = resample_line(np.c_[x, y], 2.0) if dw.get("_pre") is None else np.c_[x, y]
        if dw.get("drop_within") is not None:
            # a wall that the track itself crosses or runs on (Sonoma's drag-strip walls where the course uses the drag
            # strip): points within drop_within m of the track's paved width are not this wall; the rest is kept in runs
            _, _, dd = trk.project(P)
            runs_ = [P[a_:b_ + 1] for a_, b_ in _runs(dd >= dw["drop_within"]) if b_ - a_ >= 2]
            for extra in runs_[1:]:
                split.append((dw, extra))
            if not runs_:
                continue
            P = runs_[0]
        if dw.get("at_edge"):
            P = wall_at_edge(trk, P, dw["at_edge"], dw["name"])
        # the fitted edge wins: a declared point closer than 0.5 m to the road (or on it) is moved out along the
        # normal to 0.55 m outside the edge, and the shift is reported (the measurement and the fit disagree there)
        # round 7f (Sonoma owner note 56): a declared pit wall (kind 'pitwall') uses the barrier-gap gate's pit-wall minimum,
        # 0.3 m, with the same 0.05 m margin (moved to 0.35 m), and every moved point is logged with its measured gap
        gmin = 0.3 if dw.get("kind") == "pitwall" else 0.5
        # a declared run's own minimum (gap_min; Sonoma round 14B part 1b: a tyre wall whose stacks' track-side face must stay
        # 0.2 m beyond an edge his red moved out to it); absent: as before
        gmin = max(gmin, float(dw.get("gap_min", 0.0)))
        i, lat, dout = trk.project(P)
        # scenery.wall_gap_margin (Sonoma round 14B part 1b; absent 0): a point measured just outside the minimum (by less
        # than the margin) is moved too, since the package rounds coordinates to 1 cm and the gate measures the rounded
        # point (T7 approach left read 0.4995 m once his red brought the edge to the wall)
        close = dout < gmin + float(SC_CFG.get("wall_gap_margin", 0.0))
        if close.any():
            sd = np.sign(lat[close]); P[close] = trk.edge_point(i[close], sd, gmin + 0.05)
            log(f"declared wall {dw['name']}: {int(close.sum())} points within {gmin} m of the fitted edge moved out "
                f"(max {gmin - dout[close].min():.2f} m, stations {int(i[close].min())}..{int(i[close].max())})")
            if dw.get("kind") == "pitwall":
                for i_, d_ in zip(i[close], dout[close]):
                    log(f"  pit wall point at station {int(i_)}: measured {d_:+.2f} m from the edge -> {gmin + 0.05:.2f} m")
        if dw.get("seam") == "far":
            # Buttonwillow round 12 (the wall-ends gate on the station surrounds): a CLOSED ring (a station's tyre surround,
            # closed all round on the captures) has no end; its polyline's seam (first = last point) is a modelling
            # artefact that the gate reads as a run head. seam='far' starts the ring at its point farthest from the track
            # (the side away from the road); config-gated (absent: as before)
            _, _, dq = trk.project(P[:-1])
            j_ = int(np.argmax(dq))
            log(f"declared wall {dw['name']}: closed ring, seam moved to its far side ({float(dq[j_]):.1f} m beyond the edge; "
                f"was {float(dq[0]):.1f} m)")
            P = seam_far(P, j_, dw["name"])
        decl.append(P)
        rec = {"kind": dw.get("kind", "concrete"), "h": dw.get("h", 1.0), "fence": dw.get("fence", 3.0),
               "pts": with_z(trk, P), "src": f"declared: {dw['name']}" + (f" ({dw['src']})" if dw.get("src") else "")}
        if dw.get("gap_min"):
            rec["_gap_min"] = float(dw["gap_min"])   # read (and dropped) by tyre_facings
        # round 12: the lift that puts the wall's top level across a hollow (barrier_rules.py rule 1; the same rule as the
        # final top_z pass in scenery_post.py on the same points), for the boards standing on the wall
        lift = (BR.run_lift(rec["pts"], **HOLLOWS) if HOLLOWS is not None and rec["kind"] in BR.HOLLOW_KINDS
                else np.zeros(len(P)))
        DECLARED_WALLS.setdefault(dw["name"], []).append((P.copy(), float(dw.get("h", 1.0)), lift))
        if dw.get("color"):
            rec["color"] = dw["color"]
        for key_ in ("pattern", "sections"):   # colour sections along the run (Buttonwillow, 20 Oct 2026); absent: one colour
            if dw.get(key_):
                rec[key_] = dw[key_]
        if dw.get("stack"):
            rec["stack"] = int(dw["stack"])   # tyres per stack (round 7), from the evidence
        # round 14D (Sonoma T11, owner 25 Oct 2026): a deep tyre wall's rows (the app draws row k k x 0.6 m to the
        # polyline's left; absent: 2) and a thick wall's drawn width (absent: the app's 0.36 m); both from the evidence
        if dw.get("rows"):
            rec["rows"] = int(dw["rows"])
        if dw.get("_box"):
            rec["box"] = {"w": round(dw["_box"]["w"], 3), "side": int(dw["_box"]["side"])}   # the app draws the thick wall from here
            rec["wall_id"] = dw["_wall_id"]; rec["face"] = "front"   # review (B / C): the two faces of one wall, tagged
        if dw.get("_hidden"):
            rec["hidden"] = True   # a thick wall's back face: collides, draws no body (its fence is drawn)
            rec["wall_id"] = dw["_wall_id"]; rec["face"] = "back"
        if dw.get("fence_arm"):
            # round 10 (Sonoma pit-out catch fence): angled arms on the fence posts, leaning toward the track (the side of
            # the polyline the nearest track centre lies on; +1 = left, the app's offsetLine convention)
            m_ = len(P) // 2
            t_ = P[min(m_ + 1, len(P) - 1)] - P[max(m_ - 1, 0)]
            n_ = np.array([-t_[1], t_[0]])
            i_, _, _ = trk.project(P[m_:m_ + 1])
            side_ = 1 if float((trk.C[i_[0], :2] - P[m_]) @ n_) > 0 else -1
            rec["arm"] = {"len": float(dw["fence_arm"]["len"]), "deg": float(dw["fence_arm"]["deg"]), "side": side_}
        if rec["kind"] == "tyres" and int(dw.get("rows") or 2) > 2:
            mem = stacked_tyre_runs(rec, int(dw["rows"]), ground=trk.ground)
            out += mem
            log(f"declared wall {dw['name']}: {dw['rows']} rows as {len(mem)} stacked 2-row runs")
        else:
            out.append(rec)
        log(f"declared wall {dw['name']}: {len(P) * 2} m ({dw.get('kind', 'concrete')}, fence {dw.get('fence', 3.0)} m)")
    if decl:
        from scipy.spatial import cKDTree
        kd = cKDTree(np.concatenate(decl))
        kept = []
        for b in out:
            if b["kind"] != "pitwall" or str(b.get("src", "")).startswith("declared"):
                kept.append(b); continue
            P = np.array(b["pts"]); far = kd.query(P[:, :2])[0] > 3.0
            for a_, b2 in _runs(far):
                if b2 - a_ >= 3:
                    kept.append(dict(b, pts=[list(map(float, q)) for q in P[a_:b2 + 1]]))
        out[:] = kept
    # catch fence round the paddock
    for w in osm.select(lambda t: t.get("barrier") == "fence", trk.box):
        for run in polyline_runs(trk, w["xy"], step=3.0, max_out=400):
            out.append({"kind": "fence", "h": 0.0, "fence": 2.4, "pts": with_z(trk, run), "src": f"osm:{w['id']}"})
    tot = {}
    for b in out:
        P = np.array(b["pts"])
        tot[b["kind"]] = tot.get(b["kind"], 0) + float(np.linalg.norm(np.diff(P[:, :2], axis=0), axis=1).sum())
    log("barriers (m): " + ", ".join(f"{k} {v:.0f}" for k, v in tot.items()))
    return out, tot


# ---------------------------------------------------------------- kerbs, boards, landmarks
def kerbs_declared(trk):
    """Kerb strips from the evidence (config scenery.kerbs_declared, 20 Oct 2026; Sonoma): each {side, a, b (lat, lon of
    the strip's ends on the edge), colors (stripe, base) or a palette name of scenery.kerb.palettes, off (m, the kerb
    band's centre beyond the edge; absent = the package's inside convention), kind, src}. No rule-placed kerbs, no
    green verge unless declared (paint).
    Round 7e (Sonoma owner note 58): each strip's colour and pattern are read from footage at that strip, never a
    track-wide default: `pattern` 'blocks' (stripe / base alternating, the default) or 'plain' (one colour: the
    stripe colour on the whole strip, e.g. a plain yellow kerb), and `colour_src` (the frame that shows it, or
    'colour unverified: ...'). With scenery.kerb.require_colour_src every kind 'kerb' strip must carry one."""
    out = []
    kc_ = SC_CFG.get("kerb", {})
    pal = kc_.get("palettes", {})
    max_step = float(kc_.get("run_max_step", 0.1))
    for k in SC_CFG["kerbs_declared"]:
        if kc_.get("require_colour_src") and k.get("kind", "kerb") == "kerb" and not k.get("colour_src"):
            raise SystemExit(f"kerbs_declared '{k.get('name')}': no colour_src (scenery.kerb.require_colour_src; SKILL 3.3)")
        if k.get("line_latlon"):
            out.append(kerb_run(trk, k, pal, max_step))
            continue
        if k.get("zone"):
            out.append(kerb_zone_strip(trk, k, pal))
            continue
        side = 1 if k["side"] == "left" else -1
        P = np.array([bl.enu(*k["a"]), bl.enu(*k["b"])], float)
        i, lat, _ = trk.project(P)
        s0, s1 = int(i[0]), int(i[1])
        if (s1 - s0) % trk.n > trk.n / 2:
            s0, s1 = s1, s0
        rec = {"side": side, "s0": s0, "s1": s0 + (s1 - s0) % trk.n, "kind": k.get("kind", "kerb")}
        c = k.get("colors")
        if isinstance(c, str):
            c = pal[c]
        if c:
            rec["colors"] = list(c)
        if k.get("pattern", "blocks") == "plain":
            if not c:
                raise SystemExit(f"kerbs_declared '{k.get('name')}': pattern 'plain' needs colors")
            rec["colors"] = [c[0], c[0]]
        elif k.get("pattern", "blocks") != "blocks":
            raise SystemExit(f"kerbs_declared '{k.get('name')}': unknown pattern {k['pattern']!r} (blocks | plain)")
        if k.get("off") is not None:
            rec["off"] = float(k["off"])
        if k.get("paint"):
            rec["paint"] = float(k["paint"])
        rec["src"] = (f"{k['name']}: " if k.get("name") else "") + k["src"] + (f"; colour: {k['colour_src']}" if k.get("colour_src") else "")
        out.append(rec)
    log(f"kerbs: {len(out)} declared strips (config scenery.kerbs_declared), {sum(k['s1'] - k['s0'] for k in out)} m; no rule kerbs")
    for r in KERB_RUN_REPORT:
        log(f"   kerb run {r['name']}: {r['side']} s {r['s0']}-{r['s1']}, offset {r['off_min']:+.2f}..{r['off_max']:+.2f} m, max step {r['max_step']:.3f} m"
            + (f", raised {r['profile']}" if r.get("profile") else ""))
    far = [k for k in out if abs(k.get("off", 0.0)) > 1.2]
    if far:
        # report (judge r2, Buttonwillow): strips standing more than 1.2 m off the fitted edge, each with its evidence: a
        # block line the edge should reach (a stage-1 kerb zone) or a false detection to drop
        log(f"kerbs: {len(far)} strips more than 1.2 m off the edge (report):")
        for k in far:
            log(f"   {'left' if k['side'] > 0 else 'right'} s {k['s0']:.0f}-{k['s1']:.0f} off {k['off']:+.2f} m: {k['src'][:140]}")
    return out


KERB_RUN_REPORT = []


def kerb_run(trk, k, pal, max_step=0.1):
    """One kerb RUN along its block line (config kerbs_declared entry with `line_latlon`, Buttonwillow 21 Oct 2026, the
    owner's "weird, disjointed kerbs"): the band centre's measured world line projected on the track every build, its
    offset from the edge per station robust-smoothed over ~10 m (median 9, Gaussian 4: the band reader alternates between
    a block's inner and outer limit on some lines, right 3888-3930), published as one strip with
    `offs` per station (no steps between pieces) and `off` (the median, for the physics' band); optional `profile` (a
    raised run). The run's largest station-to-station offset change is reported and must stay <= max_step."""
    from scipy.ndimage import gaussian_filter1d, median_filter
    side = 1 if k["side"] == "left" else -1
    P = _ll_line(k["line_latlon"], 1.0)
    i_, lat_, _ = trk.project(P)
    o_ = np.argsort(i_); i_, lat_ = np.asarray(i_)[o_], np.asarray(lat_)[o_]
    if i_[-1] - i_[0] > trk.n / 2:            # wraps the start line
        i_ = np.where(i_ < trk.n / 2, i_ + trk.n, i_); o_ = np.argsort(i_); i_, lat_ = i_[o_], lat_[o_]
    s0, s1 = int(np.ceil(i_[0])), int(np.floor(i_[-1]))
    if k.get("extent") is not None:
        # Buttonwillow round 13 (the owner's decision of 25 Oct 2026, point 2: each run's extent measured from dense
        # onboard frames): the run's start and end, metres along the lap of this package, replace the block line's ends;
        # the line still names the run. Only with flush_runs (the strip's offset is then the constant flush one, so the
        # line's lateral offsets are not used) and with its evidence (extent_src)
        if not SC_CFG.get("kerb", {}).get("flush_runs"):
            raise SystemExit(f"kerb run '{k.get('name')}': extent needs scenery.kerb.flush_runs")
        if not k.get("extent_src"):
            raise SystemExit(f"kerb run '{k.get('name')}': extent without extent_src")
        e0, e1 = (float(v) / trk.sp for v in k["extent"])
        if not (0 < e1 - e0 < trk.n / 2):
            raise SystemExit(f"kerb run '{k.get('name')}': extent {k['extent']} is not a run")
        n0, n1 = int(round(e0)), int(round(e1))
        log(f"   kerb run {k.get('name')}: extent stations {s0}-{s1} (block line) -> {n0}-{n1} ({k['extent_src'][:100]})")
        s0, s1 = n0, n1
    st = np.arange(s0, s1 + 1)
    lat = np.interp(st, i_, lat_)
    hw = trk.hw(st % trk.n, side)
    off = side * lat - hw
    if SC_CFG.get("kerb", {}).get("flush_runs"):
        # round 10 (Buttonwillow, owner's decisions of 23 Oct 2026): every run is a stage-1 kerb zone, the edge at the band's
        # outer limit and his red at its inner limit, so the strip lies flush inside the edge (off = -width / 2); the
        # measured line gives the run's extent (s0..s1) only. Against the round-10 edges the round-5 block-line offsets
        # ran up to 3.4 m outside the edge (left 1089-1116)
        w_ = float(k.get("width") or SC_CFG.get("kerb", {}).get("width", 0.9))
        off = np.full(len(off), -w_ / 2)
    if len(off) < 12:
        # a short run (under 12 m, round 8): one offset, its median (a 9 m block line set at an angle to an edge that bends
        # there read as a 0.7 m ramp the smoothing cannot hold under the step gate; the band is short enough to be one line)
        off = np.full(len(off), float(np.median(off)))
    elif len(off) >= 3:
        mw = min(9, len(off) - (1 - len(off) % 2))   # odd, at most the run's length (a 6 m run: 5)
        off = gaussian_filter1d(median_filter(off, mw, mode="nearest"), 4, mode="nearest")
    step = float(np.abs(np.diff(off)).max()) if len(off) > 1 else 0.0
    rec = {"side": side, "s0": int(s0), "s1": int(s1), "kind": k.get("kind", "kerb"), "off": rnd(float(np.median(off)), 2),
           "offs": [rnd(float(v), 2) for v in off]}
    c = k.get("colors")
    if isinstance(c, str):
        c = pal[c]
    if c:
        rec["colors"] = list(c)
    if k.get("profile"):
        rec["profile"] = dict(k["profile"])
    if k.get("width"):
        rec["width"] = float(k["width"])   # the run's own band width (round 8, measured on the captures)
    rec["src"] = (f"{k['name']}: " if k.get("name") else "") + k["src"] + (f"; colour: {k['colour_src']}" if k.get("colour_src") else "")
    KERB_RUN_REPORT.append({"name": k.get("name", ""), "side": k["side"], "s0": int(s0), "s1": int(s1), "max_step": round(step, 3),
                            "off_min": rnd(float(off.min()), 2), "off_max": rnd(float(off.max()), 2), "profile": k.get("profile")})
    if step > max_step:
        raise SystemExit(f"kerb run '{k.get('name')}': offset step {step:.3f} m between stations (> {max_step} m)")
    return rec


def kerb_zone_strip(trk, k, pal):
    """A kerb strip over a stage-1 kerb zone (kerbs_declared entry with `zone` (lo, hi), stations of stations_ref,
    mapped by world position; Buttonwillow round 10, the owner's decision of 23 Oct 2026 point 4, "the onboard wins"):
    where the onboard shows a kerb run but the captures show no band beside his red, stage 1 moved the edge out by the
    track's standard kerb width (spline.owner_edges kerb_inside); the strip fills that width, from the edge inward to
    his red: `off` = -width / 2 (the band centre half a width inside the edge), width = scenery.kerb width unless the
    entry sets one. No measured line: the strip follows the fitted edge."""
    side = 1 if k["side"] == "left" else -1
    lo, hi = (int(v) for v in k["zone"])
    w = float(k.get("width") or SC_CFG.get("kerb", {}).get("width", 0.9))
    rec = {"side": side, "s0": lo, "s1": lo + (hi - lo) % trk.n, "kind": k.get("kind", "kerb"), "off": rnd(-w / 2, 2), "width": w}
    c = k.get("colors")
    if isinstance(c, str):
        c = pal[c]
    if c:
        rec["colors"] = list(c)
    if k.get("profile"):
        rec["profile"] = dict(k["profile"])
    rec["src"] = (f"{k['name']}: " if k.get("name") else "") + k["src"] + (f"; colour: {k['colour_src']}" if k.get("colour_src") else "")
    KERB_RUN_REPORT.append({"name": k.get("name", ""), "side": k["side"], "s0": lo, "s1": hi, "max_step": 0.0,
                            "off_min": rec["off"], "off_max": rec["off"], "profile": k.get("profile")})
    return rec


def kerbs(trk):
    if SC_CFG.get("kerbs_declared") is not None:
        return kerbs_declared(trk)
    out = []
    for c in trk.t["corners"]:
        if not c.get("dir"):
            continue
        side = 1 if c["dir"] == "left" else -1
        s, rad = c["s"], c.get("radius_m") or 60
        if rad > 120:  # fast kinks (T1, T7): short apex kerb only
            out.append({"side": side, "s0": s - 25, "s1": s + 25, "kind": "apex"})
            continue
        half = int(min(max(rad * 0.9, 28), 45))
        out.append({"side": side, "s0": s - half, "s1": s + half, "kind": "apex"})
        if c["turn"] not in SC_CFG.get("no_exit_kerb", []):  # Laguna: the Corkscrew's T8 exit is T8A's entry
            out.append({"side": -side, "s0": s + 15, "s1": s + 15 + int(min(max(rad, 45), 70)), "kind": "exit",
                        "paint": 1.5})
    for k in out:
        k["s0"] %= trk.n
        k["s1"] = k["s0"] + ((k["s1"] - k["s0"]) % trk.n)
    log(f"kerbs: {len(out)} strips, {sum(k['s1'] - k['s0'] for k in out)} m")
    return out


KERB_W = 0.9  # m; v2 track edges include the kerbs, so kerbs lie inside the edge (edge - KERB_W .. edge)


PIT_HALF_DEFAULT = 4.0  # m (8 m paved width) when the image gives no edge


_MOUTHS_USED = set()
_NO_PAINT = set()


def closed_roads(trk, osm):
    """Paved roads of the circuit that the loop does not use (config scenery.closed_roads: [{name, ways: [OSM way id or
    'way:from:to', ...], half_width}], 20 Oct 2026): driveable pavement in the sim (paved_zones parts, the pit-lane
    strip layout: the half-width from the NAIP asphalt extent, else half_width; edges inside the track clamped onto
    its edge, stretches inside the track dropped), and a cone line across each mouth where a part meets the track."""
    import geo as G_
    out_parts, lines = [], []
    nodes = {}
    root = ET.parse(os.path.join(CACHE, G_.CFG["osm_file"])).getroot()
    nodes = {n.get("id"): (float(n.get("lat")), float(n.get("lon"))) for n in root.iter("node")}
    ways = {w.get("id"): [x.get("ref") for x in w.iter("nd")] for w in root.iter("way")}
    for road in SC_CFG.get("closed_roads", []):
        for e in road["ways"]:
            if isinstance(e, dict):
                # a road with no OSM way (Sonoma round 14B: the owner's straight-on escape road at T9A): its centre line
                # declared from the evidence ({latlon: [...], src}), built like a way
                if not e.get("src"):
                    raise SystemExit(f"closed road {road['name']}: a declared centre line needs its src")
                ll = np.array(e["latlon"], float)
                halves = e.get("halves")
                if halves is not None and len(halves) != len(ll):
                    raise SystemExit(f"closed road {road['name']}: halves has {len(halves)} values for {len(ll)} points")
                e = "declared"
            else:
                wid, *rng = str(e).split(":")
                nd = ways[wid]
                if rng:
                    a, b = nd.index(rng[0]), nd.index(rng[1]); nd = nd[min(a, b):max(a, b) + 1]
                ll = np.array([nodes[i] for i in nd if i in nodes])
                halves = None
            x, y = bl.enu(ll[:, 0], ll[:, 1])
            res = lane_parts(trk, np.c_[x, y], road.get("half_width", 5.0), f"{road['name']} ({e})",
                             clip=(road.get("min_half", 2.5), road.get("max_half", 12.0)),   # min_half (round 12): = max_half for a measured fixed width
                             halves=halves)
            if not res:
                continue
            if road.get("edges_from_green") and SC_CFG.get("owner_green"):
                for part in res["parts"]:
                    edges_from_green(trk, part, road["name"], SC_CFG["owner_green"])
            for part in res["parts"]:
                part["turn"] = road["name"]
                if road.get("surface"):
                    # its material in the app (asphalt = the circuit's road look, concrete = pale concrete); absent:
                    # the aerial photo's own colour, as before (20 Oct 2026, owner: "it's usable track, just not in use")
                    part["surface"] = road["surface"]
                # per-part overrides (config closed_roads[].part_overrides: [{near: (lat, lon), surface, src}], round 11):
                # the part whose centre line passes within 25 m of `near` takes that surface (it was read nowhere until
                # 22 Oct 2026, so the round-7e override was a no-op); an entry matching no part fails the stage
                for ov in road.get("part_overrides", []):
                    q = np.array(bl.enu(*ov["near"]))
                    if np.min(np.hypot(*(np.array(part["center"])[:, :2] - q).T)) < 25.0:
                        if not ov.get("src"):
                            raise SystemExit(f"closed road {road['name']}: part_overrides entry near {ov['near']} has no src")
                        if ov.get("surface"):
                            part["surface"] = ov["surface"]
                        if ov.get("paint") is False:
                            # round 13 part B (Sonoma owner note 135): no painted edge lines measured along this part
                            # (an open junction or a parked-vehicle row gives paint.measure nothing to find)
                            _NO_PAINT.add(id(part))
                        _MOUTHS_USED.add(id(ov))
                        log(f"closed road {road['name']}: part at ({part['center'][0][0]:.0f}, {part['center'][0][1]:.0f}) "
                            f"surface {part.get('surface')} (part_overrides near {ov['near']})")
                # 20 Oct 2026: a closed road is other pavement for the containment gate (an inside runoff the cars may
                # use, cones False, is not: it is runoff)
                part["kind"] = "closed_road" if road.get("cones", True) else "runoff"
                out_parts.append(part)
                # cone line across each end that touches the track: from one lane edge to the other, 1 m off the edge
                for end in ((0, -1) if road.get("cones", True) else ()):
                    gl, gr = part["gap_left"][end], part["gap_right"][end]
                    if min(gl, gr) <= 0.5:
                        L = np.array(part["left"][end][:2]); R = np.array(part["right"][end][:2])
                        P = np.array([L + (R - L) * t for t in np.linspace(0, 1, max(2, int(np.hypot(*(R - L)) / 2) + 1))])
                        src = f"closed road {road['name']} mouth"
                        if "mouth_cones" in road:
                            # cones only at the mouths the evidence shows coned (config closed_roads[].mouth_cones:
                            # [{near: (lat, lon), src}], 21 Oct 2026); the other mouths are left open or walled
                            mid = (L + R) / 2
                            hit = [m for m in road["mouth_cones"] if np.hypot(*(np.array(bl.enu(*m["near"])) - mid)) < 20]
                            if not hit:
                                log(f"closed road {road['name']}: mouth at ({mid[0]:.0f}, {mid[1]:.0f}) left without cones (no evidence of cones)")
                                continue
                            src += f" ({hit[0]['src']})"
                            _MOUTHS_USED.add(id(hit[0]))
                        lines.append({"spacing_m": 2.0, "pts": with_z(trk, P), "src": src})
    for road in SC_CFG.get("closed_roads", []):
        for m in road.get("mouth_cones", []):
            if id(m) not in _MOUTHS_USED:
                raise SystemExit(f"closed road {road['name']}: mouth_cones entry near {m['near']} matches no mouth")
        for m in road.get("part_overrides", []):
            if id(m) not in _MOUTHS_USED:
                raise SystemExit(f"closed road {road['name']}: part_overrides entry near {m['near']} matches no part")
    log(f"closed roads: {len(out_parts)} paved parts, {len(lines)} cone lines")
    return out_parts, lines


_GREEN = {}


def edges_from_green(trk, part, name, og):
    """A closed road's paving edges on the owner's green lines (config scenery.owner_green {file, reach, along}, roads
    with edges_from_green=True; Buttonwillow round 10): he drew green on the outline windows along the edges of the
    paved roads and paddock the course does not use (owner/r10/merged.json green_enu_xy). At each centre point of the
    part, his green points within `along` m along it on each side, the one group nearest the current (NAIP / OSM)
    edge within `reach` m, median lateral; a 9-sample median and a 3 m Gaussian over runs of >= 10 stations; points on
    the circuit's paved width are not his road edge and are skipped. Stations with no green keep their edge."""
    from scipy.ndimage import gaussian_filter1d, median_filter
    from scipy.spatial import cKDTree
    f = og["file"]
    if f not in _GREEN:
        d = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracks", CFG_ALL["id"], f)))
        G = np.array(d["green_enu_xy"], float)[:, :2]
        _, _, outside = trk.project(G)
        G = G[outside > 0.3]                       # his green on the circuit's own paving is a mouth contact, not a road edge
        _GREEN[f] = (G, cKDTree(G))
    G, kd = _GREEN[f]
    reach, along = float(og.get("reach", 4.0)), float(og.get("along", 1.0))
    C = np.array(part["center"])[:, :2]
    if len(C) < 12:
        return
    tg = np.gradient(C, axis=0); tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-9); NL = np.c_[-tg[:, 1], tg[:, 0]]
    for side, key in ((1, "left"), (-1, "right")):
        E = np.array(part[key], float)
        cur = side * ((E[:, :2] - C) * NL).sum(1)
        v = np.full(len(C), np.nan)
        for i in range(len(C)):
            idx = kd.query_ball_point(C[i], cur[i] + reach + 1.0)
            if not idx:
                continue
            Q = G[idx] - C[i]; at = (Q * tg[i]).sum(1); lat = side * (Q * NL[i]).sum(1)
            m = (np.abs(at) <= along) & (lat > 0.5) & (np.abs(lat - cur[i]) <= reach)
            if m.sum():
                v[i] = float(np.median(lat[m]))
        ok = np.isfinite(v); runs = [(a, b) for a, b in _runs(ok) if b - a >= 9]
        n_set = 0
        for a, b in runs:
            st = np.arange(a, b + 1)
            vs = gaussian_filter1d(median_filter(v[st], min(9, len(st) - (1 - len(st) % 2)), mode="nearest"), 3, mode="nearest")
            E[st, :2] = C[st] + NL[st] * (side * vs)[:, None]
            n_set += len(st)
        if n_set:
            part[key] = [[rnd(x, 2), rnd(y, 2), rnd(z, 3)] for x, y, z in E]
        log(f"closed road {name}: {key} paving edge on the owner's green at {n_set} of {len(C)} points")


def closed_road_paint(trk, parts):
    """Painted edge lines along the closed roads (config scenery.closed_roads entries with paint=True, 20 Oct 2026):
    the stage-1 painted-edge detector (paint.measure: walk from the centre outward over the asphalt to the white line
    or the road's end, on every clean capture, median over captures) run along each closed-road part's centre, then
    fitted the stage-1 way for a part without logger laps: a 9-sample median and a 3 m Gaussian of each side's
    lateral over the measured stations, gaps up to 8 m interpolated; a line is drawn only along runs of 10 m or more
    where the captures show it. Returns paint_lines entries {width, side, pts, src} (0.12 m white, 0.15 m inside the
    measured edge)."""
    import captures as CAP_
    import geo as G_
    import paint as PAINT
    from PIL import Image as Img
    from scipy.ndimage import gaussian_filter1d, median_filter
    names = {r["name"] for r in SC_CFG.get("closed_roads", []) if r.get("paint")}
    seam_names = {r["name"] for r in SC_CFG.get("closed_roads", []) if r.get("edges_from_paint")}
    if not names:
        return []
    cfg = G_.CFG
    caps = CAP_.capture_list(cfg, cfg["centre_captures"])
    caps = [t for t in caps if t["name"] not in cfg["captures"].get("exclude", [])]
    ortho = Img.open(os.path.join(OUT, "ortho.jpg"))
    out = []
    for p in parts:
        if p.get("turn") not in names or id(p) in _NO_PAINT:
            continue
        C = np.array(p["center"])[:, :2]
        if len(C) < 12:
            continue
        Pm = PAINT.measure(C, np.zeros(len(C)), caps, ortho, trk.t["ortho"], cfg["captures"]["mpp"],
                           cfg["centre_registration"], log=lambda *a: None)
        tg = np.gradient(C, axis=0); tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-9)
        NL = np.c_[-tg[:, 1], tg[:, 0]]
        Z = np.array(p["center"])[:, 2]
        for side, key in ((1, "lat_left"), (-1, "lat_right")):
            v = Pm[key].copy()
            v[~np.isfinite(NL).all(1) | (np.linalg.norm(NL, axis=1) < 0.5)] = np.nan   # repeated centre points (round 7b)
            ok = np.isfinite(v)
            if ok.sum() < 10:
                log(f"closed road {p['turn']}: {side > 0 and 'left' or 'right'} painted edge not found ({int(ok.sum())} stations)")
                continue
            idx = np.nonzero(ok)[0]
            vs = gaussian_filter1d(median_filter(v[ok], 9, mode="nearest"), 3, mode="nearest")
            full = np.interp(np.arange(len(C)), idx, vs)
            # keep stations within 8 m of a measured one
            near = np.zeros(len(C), bool)
            for i in idx:
                near[max(0, i - 4):i + 5] = True
            if p.get("turn") in seam_names:
                # round 7c (Sonoma owner note 45): the paving's edge is the measured painted edge (+0.3 m outward), so the
                # seam between this road and the ground / the next surface lies on a measured material boundary, not on
                # the NAIP half-width; the stations without paint nearby keep their edge
                E = np.array(p["left" if side > 0 else "right"], float)
                st_ = np.nonzero(near)[0]
                E[st_, :2] = C[st_] + NL[st_] * (full[st_] + side * 0.3)[:, None]
                p["left" if side > 0 else "right"] = [[rnd(x, 2), rnd(y, 2), rnd(z, 3)] for x, y, z in E]
                log(f"closed road {p['turn']}: {'left' if side > 0 else 'right'} paving edge set on the measured paint at {len(st_)} stations")
            for a_, b_ in _runs(near):
                if b_ - a_ < 10:
                    continue
                st = np.arange(a_, b_ + 1)
                lat = full[st] - side * 0.15
                P = C[st] + NL[st] * lat[:, None]
                # round 6 (orchestrator F5): a closed road's edge line stops at the circuit's own paved width (+0.3 m): the
                # line at the 2020 bypass mouth was drawn on across the track at s ~2800
                ti, tl, _ = trk.project(P)
                on_track = (tl <= trk.hl[ti] + 0.3) & (tl >= -trk.hr[ti] - 0.3)
                if on_track.any():
                    log(f"closed road {p['turn']}: {int(on_track.sum())} edge-line samples on the circuit's paved width dropped")
                for c_, d_ in _runs(~on_track):
                    if d_ - c_ < 10:
                        continue
                    q = np.arange(c_, d_ + 1)
                    out.append({"width": 0.12, "side": side, "pts": [[rnd(x, 2), rnd(y, 2), rnd(z + 0.02, 3)] for (x, y), z in zip(P[q], Z[st][q])],
                                "src": f"closed road {p['turn']}: painted edge on the 2026 captures (paint.measure, {int(ok[st].sum())} of {len(st)} stations measured)"})
            log(f"closed road {p['turn']}: {'left' if side > 0 else 'right'} painted edge measured at {int(ok.sum())} of {len(C)} stations, "
                f"lateral p50 {np.nanmedian(v):+.1f} m")
    return out


TYRE_ROWS_MAX = 8


def validate_declared_wall(dw):
    """Round 14D (review of the Sonoma round-14D diff): the keys the app and the gates must read as the same numbers.
    `rows` (a tyre run's drawn rows) must be an integer 1..TYRE_ROWS_MAX on a tyre run; `w` (a thick wall's width) is
    only for a concrete run and must be > 0. Anything else fails the build with the wall's name."""
    name = dw.get("name", "?")
    if "rows" in dw:
        r = dw["rows"]
        if dw.get("kind") != "tyres":
            raise SystemExit(f"declared wall {name!r}: `rows` is for a tyre run, not kind {dw.get('kind')!r}")
        if isinstance(r, bool) or not isinstance(r, int) or not 1 <= r <= TYRE_ROWS_MAX:
            raise SystemExit(f"declared wall {name!r}: `rows` must be an integer 1..{TYRE_ROWS_MAX}, got {r!r}")
        if r % 2:
            # round 14D review (A): the physics collides every tyre run as two rows (src/physics/collision.ts TYRE_WALL);
            # a deeper wall is emitted as 2-row runs back to back (stacked_tyre_runs), so an odd count cannot be honoured
            raise SystemExit(f"declared wall {name!r}: `rows` must be even (2, 4, 6, 8: emitted as 2-row runs, each collided as two rows), got {r!r}")
    if "w" in dw:
        w = dw["w"]
        if dw.get("kind", "concrete") != "concrete":
            raise SystemExit(f"declared wall {name!r}: `w` (a thick wall's width) is only for a concrete run, not kind {dw.get('kind')!r}")
        if isinstance(w, bool) or not isinstance(w, (int, float)) or not w > 0:
            raise SystemExit(f"declared wall {name!r}: `w` must be a width > 0 m, got {w!r}")
        if dw.get("sections") or dw.get("pattern"):
            # round 14D review (E): the app draws colour sections as 0.36 m wall bodies; on a thick wall's box they are not drawn
            raise SystemExit(f"declared wall {name!r}: colour `sections` / `pattern` are not supported on a thick wall (`w`)")


def stacked_tyre_runs(rec, rows, ground=None):
    """Round 14D review (A): a declared tyre run `rows` deep (even, > 2) as rows / 2 runs of two rows back to back, each
    drawn and collided as the physics already does a tyre run (two rows: row 0 on its line, row 1 0.6 m to its left;
    src/physics/collision.ts collides both faces and the end stacks). Member k stands k x 1.2 m to the polyline's left
    of the declared line; every member carries rows 2 and the tag `stack_of` {id, k, n} (`stack` is tyres per stack) (the gates and tyre_facings read the
    group as one wall: the rear member is the one facing a wall behind it). Colour sections are carried over by their
    share of the member's length. Pure."""
    n = rows // 2
    P = np.array(rec["pts"], float)
    T = np.gradient(P[:, :2], axis=0); T /= np.maximum(np.linalg.norm(T, axis=1), 1e-9)[:, None]
    NL = np.c_[-T[:, 1], T[:, 0]]
    L0 = float(np.linalg.norm(np.diff(P[:, :2], axis=0), axis=1).sum())
    out = []
    for k in range(n):
        Q = P.copy(); Q[:, :2] = P[:, :2] + NL * (k * 2 * BR.TYRE_ROW)
        if ground is not None and k:
            Q[:, 2] = ground(Q[:, 0], Q[:, 1])
        m = dict(rec, pts=[[rnd(x, 2), rnd(y, 2), rnd(z, 2)] for x, y, z in Q], rows=2,
                 stack_of={"id": rec["src"][:80], "k": k, "n": n})
        if k:
            m["src"] = rec["src"] + f" (rows {2 * k + 1}-{2 * k + 2})"
        Lk = float(np.linalg.norm(np.diff(Q[:, :2], axis=0), axis=1).sum())
        if rec.get("sections") and L0 > 0:
            m["sections"] = [dict(q, from_m=rnd(q["from_m"] * Lk / L0, 2), to_m=rnd(q["to_m"] * Lk / L0, 2)) for q in rec["sections"]]
        out.append(m)
    return out


def thick_wall_faces(P, toward, w):
    """Round 14D (review: the collision keeps a wall's centreline + 0.10 m skin and ignores a drawn width): a declared
    concrete wall `w` m thick becomes its two FACES, each a concrete run the physics already collides with: the front
    face w / 2 toward the track from the measured centre line, the back face w / 2 away from it. `toward` is +1 when the
    track lies to the polyline's left, -1 when to its right. Returns (front, back, side): `side` is where the back face
    lies from the front polyline (+1 its left, -1 its right), the side the app draws the box toward. Pure."""
    P = np.asarray(P, float)
    T = np.gradient(P, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1), 1e-9)[:, None]
    NL = np.c_[-T[:, 1], T[:, 0]]
    front = P + NL * (toward * w / 2.0)
    back = P - NL * (toward * w / 2.0)
    return front, back, -int(toward)


def wall_at_edge(trk, P, ae, name):
    """A declared wall that stands AT the painted edge line over a stretch (config declared_walls[].at_edge, round 13,
    Sonoma owner note 136: "the wall should stand right against the painted edge line"): {side: 'left' | 'right',
    off (m beyond the edge; the barrier-gap minimum plus its margin, 0.55), a, b, c: (lat, lon) on the track}. Between a
    and b the wall's measured offset from the edge blends (smoothstep) to `off`; from b to c it is the edge plus `off`
    exactly, so it follows the fitted edge with no joggle; outside a..c the measured points are kept. The edge itself
    does not move."""
    sg = 1 if ae["side"] == "left" else -1
    n = trk.n
    ia, ib, ic = (int(trk.project(np.array([bl.enu(*ae[k])]))[0][0]) for k in ("a", "b", "c"))
    i, lat, dout = trk.project(P)
    u = (i - ia) % n                     # stations past a, in driving order
    span_ab, span_ac = (ib - ia) % n, (ic - ia) % n
    if span_ab > span_ac:
        raise SystemExit(f"declared wall {name}: at_edge points not in driving order a -> b -> c")
    inside = (u <= span_ac) & (np.sign(lat) == sg)
    if not inside.any():
        raise SystemExit(f"declared wall {name}: at_edge stretch {ia}..{ic} holds none of its points")
    o_a = float(dout[inside][np.argmin(u[inside])])   # the measured offset where the blend starts
    Q = P.copy()
    for j in np.where(inside)[0]:
        if u[j] >= span_ab:
            o = ae["off"]
        else:
            t = u[j] / span_ab
            o = o_a + (ae["off"] - o_a) * t * t * (3 - 2 * t)
        Q[j] = trk.edge_point(i[j], sg, o)
    log(f"declared wall {name}: at the {ae['side']} edge + {ae['off']} m over stations {ia}..{ic} (blend {ia}..{ib} from "
        f"{o_a:.2f} m): {int(inside.sum())} points; their measured offsets were p50 {np.median(dout[inside]):.2f}, "
        f"min {dout[inside].min():.2f}, max {dout[inside].max():.2f} m")
    return Q


def paved_areas(trk, osm):
    """Paved ground that is not a driven strip (config scenery.paved_areas, 20 Oct 2026: the paddock behind the pit
    lane, where the NAIP ortho shows parked trailers and cars as ground): each {osm: area way id, surface: 'asphalt' |
    'concrete', src}. The OSM outline, drawn by the app as plain paving over the terrain (no physics change)."""
    out = []
    for pa in SC_CFG.get("paved_areas", []):
        if pa.get("latlon"):
            # an outline measured on the captures (Buttonwillow, 20 Oct 2026: the paved patch inside the T2 hairpin)
            ll_ = np.array(pa["latlon"], float); xx, yy = bl.enu(ll_[:, 0], ll_[:, 1]); xy = np.c_[xx, yy]
            extra = {}
            if pa["surface"] == "apron" and SC_CFG.get("aprons_meet_road"):
                xy, extra = _apron_meet_road(trk, xy)
            out.append({"name": pa.get("name", "paved area"), "surface": pa["surface"], "src": pa["src"],
                        "poly": [[rnd(x, 1), rnd(y, 1)] for x, y in xy], **({"color": pa["color"]} if pa.get("color") else {}), **({"look": pa["look"]} if pa.get("look") else {}), **extra})
            log(f"paved area {pa.get('name', '')}: {len(xy)} vertices, {pa['surface']} (measured outline)")
            continue
        w = next((w for w in osm.ways if w["id"] == str(pa["osm"])), None)
        if w is None:
            raise SystemExit(f"paved_areas: OSM way {pa['osm']} not found")
        xy = w["xy"][:-1] if np.linalg.norm(w["xy"][0] - w["xy"][-1]) < 0.5 else w["xy"]
        out.append({"name": pa.get("name", f"osm {pa['osm']}"), "surface": pa["surface"], "src": pa["src"],
                    "poly": [[rnd(x, 1), rnd(y, 1)] for x, y in xy]})
        log(f"paved area {pa.get('name', pa['osm'])}: {len(xy)} vertices, {pa['surface']}")
    return out


_ROAD_POLY = None


def _apron_meet_road(trk, xy):
    """An apron outline clipped to the road (config scenery.aprons_meet_road, Buttonwillow judge r6: the outline's own
    steps along the track edge read as tan bites between the apron and the road): the outline minus the road polygon
    (the largest piece, simplified 0.05 m), so the apron meets the fitted edge along it; `feather` per segment (poly[i]
    -> poly[i+1]): False on the road edge (no fade there: the app draws it over the track's shoulder), True elsewhere."""
    global _ROAD_POLY
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    if _ROAD_POLY is None:
        L, R, n = trk.L[:, :2], trk.R[:, :2], trk.n
        _ROAD_POLY = unary_union([Polygon([L[i], L[(i + 1) % n], R[(i + 1) % n], R[i]]).buffer(0) for i in range(n)])
    g = Polygon(xy).buffer(0).difference(_ROAD_POLY)
    if g.geom_type == "MultiPolygon":
        g = max(g.geoms, key=lambda q: q.area)
    g = g.simplify(0.05)
    P = np.array(g.exterior.coords)[:-1]
    fe = [bool(_ROAD_POLY.distance(Point((P[i] + P[(i + 1) % len(P)]) / 2)) > 0.2) for i in range(len(P))]
    log(f"   apron meets the road: {len(P)} vertices, {sum(not f for f in fe)} segments on the road edge")
    return P, {"feather": fe}


def tyre_facings(trk, bar, reach=2.5, off=0.55):
    """A tyre run in front of a rigid wall is a FACING of it (config scenery.tyre_facings, round 7b; Sonoma owner note
    48): every tyre point within `reach` m of a concrete / pitwall / Armco line and on its track side is moved onto that
    line, `off` m toward the track (the stacks stand against the wall), so the two never stand side by side at an offset;
    points further off are kept, so a run that angles in meets the facing as a taper; a point read just behind the wall
    line (the dark band beside the bright top) joins the facing too; a point the move would bring within 0.55 m of the
    fitted edge stays. Logged per run.
    Round 14C (Sonoma issue #12): a tyre point whose nearest wall point is a wall's FREE END, lying beyond that end (past
    the run's first point on its first segment, or its last point on its last segment), goes onto the wall's line
    EXTENDED past that end (the same `off` in front), so it keeps its place along the line. Before, every such point
    went onto the end point itself: the 2 m "tyre bundle at the far wall's head" (s ~2347) collapsed to three coincident
    points and drew nothing. An end is FREE only when no other rigid run comes within `join` m (1.5, the wall-ends
    gate's join) of it, and the extension is taken only when the stacks' footprint over it (the polygon wall end ->
    wall-line point -> placed point, widened by the drawn row extent TYRE_ROW + TYRE_R, 0.91 m) crosses no other barrier
    polyline; otherwise the point goes onto the end point as before (a joined corner keeps the clamp)."""
    from shapely.geometry import LineString, Polygon
    rig, head, tail, wid = [], [], [], []
    for bi, b in enumerate(bar):
        if b["kind"] in ("concrete", "pitwall", "armco"):
            P = np.array(b["pts"])[:, :2]
            if len(P) >= 2:
                rig.append(np.c_[P[:-1], P[1:]])
                m_ = len(P) - 1
                head.append(np.arange(m_) == 0); tail.append(np.arange(m_) == m_ - 1)
                wid.append(np.full(m_, bi))
    if not rig:
        return
    S = np.concatenate(rig)
    head, tail, wid = np.concatenate(head), np.concatenate(tail), np.concatenate(wid)
    join_ = 1.5
    rigid_ = {bi: np.array(b["pts"], float)[:, :2] for bi, b in enumerate(bar)
              if b["kind"] in ("concrete", "pitwall", "armco") and len(b["pts"]) >= 2}

    def free_end(bi, E):
        """no other rigid run within join_ m of this wall end"""
        return not any(o != bi and np.hypot(*(Q - E).T).min() <= join_ for o, Q in rigid_.items())

    def footprint_clear(bi, ti, E, c, p_new):
        """the stacks over the extension cross no other barrier polyline (the wall itself and this tyre run excepted)"""
        fp = Polygon([tuple(E), tuple(c), tuple(p_new)]).buffer(BR.TYRE_ROW + BR.TYRE_R) if np.hypot(*(c - E)) > 1e-6 \
            else LineString([tuple(E), tuple(p_new)]).buffer(BR.TYRE_ROW + BR.TYRE_R)
        for o, b in enumerate(bar):
            if o in (bi, ti) or len(b["pts"]) < 2:
                continue
            if fp.intersects(LineString([tuple(q[:2]) for q in b["pts"]])):
                return False
        return True
    a, d = S[:, :2], S[:, 2:] - S[:, :2]
    L2 = np.maximum((d ** 2).sum(1), 1e-9)
    for ti, b in enumerate(bar):
        if b["kind"] != "tyres":
            continue
        so = b.get("stack_of")
        if so and so["k"] < so["n"] - 1:
            # round 14D third review (2): a stacked deep tyre wall is placed as ONE wall: its rear member faces the wall
            # behind (below) and the members in front follow it at the row spacing; they are not placed on their own
            continue
        # the group's row 0 lies (n - 1) x 1.2 m before the rear member's polyline (0 for a run on its own)
        grp_ext = (so["n"] - 1) * 2 * BR.TYRE_ROW if so else 0.0
        P = np.array(b["pts"], float)
        P_old = P.copy()
        moved = []
        gmin_ = max(0.55, b.pop("_gap_min", 0.0) + 0.05)   # a declared run's own minimum (gap_min) holds here too
        # round 14D: a run that declares its `rows` (row k drawn k x 0.6 m to the polyline's left) faces a wall with its
        # LAST row: that row's line is tested and placed `off` in front of the wall, the polyline (row 0) kept that far in
        # front of it; a run without `rows` is placed by its polyline as before
        ext = (int(b["rows"]) - 1) * BR.TYRE_ROW if b.get("rows") else 0.0
        if ext or grp_ext:
            Tq = np.gradient(P[:, :2], axis=0); Tq /= np.maximum(np.linalg.norm(Tq, axis=1), 1e-9)[:, None]
            NLq = np.c_[-Tq[:, 1], Tq[:, 0]]
        for j in range(len(P)):
            q = P[j, :2] + (NLq[j] * ext if ext else 0.0)
            t0 = ((q - a) * d).sum(1) / L2
            t = np.clip(t0, 0, 1)
            C = a + d * t[:, None]
            dist = np.linalg.norm(C - q, axis=1)
            k = int(np.argmin(dist))
            if dist[k] > reach:
                continue
            c = C[k]
            i_, lat_, _ = trk.project(np.array([q, c]))
            # in front of the wall or just behind it (the dark band read beside the bright wall top): one facing, in front
            toward = -np.sign(lat_[1]) * trk.N[int(i_[1]) % trk.n]
            p_new = c + toward * off
            if (head[k] and t0[k] < 0) or (tail[k] and t0[k] > 1):
                # beyond a wall's end (round 14C): onto the wall's line extended, if the end is free and the stacks
                # over the extension cross no other barrier; else onto the end point (the clamp) as before
                E = C[k]
                c2 = a[k] + d[k] * t0[k]
                i3, lat3, _ = trk.project(np.array([q, c2]))
                p2 = c2 + (-np.sign(lat3[1]) * trk.N[int(i3[1]) % trk.n]) * off
                if free_end(int(wid[k]), E) and footprint_clear(int(wid[k]), ti, E, c2, p2):
                    c, i_, p_new = c2, i3, p2
            if ext:
                p_new = p_new - NLq[j] * ext   # back to the polyline (row 0)
            # never closer than 0.55 m to the fitted edge (the barrier-gap gate): for a stack, its front member's row 0
            i2, lat2, dout2 = trk.project((p_new - NLq[j] * grp_ext if grp_ext else p_new)[None])
            if dout2[0] < gmin_:
                continue
            P[j, :2] = p_new
            moved.append(int(i_[0]))
        if moved and so:
            # the members in front follow the rear member point by point (same declared points, row spacing kept). Fourth
            # review (2): the ACTUAL translated members, rounded as stored, are checked against the edge minimum (on a bend
            # the rear member's normal is not theirs); any point whose translated row 0 would come inside it is held at its
            # declared place in every member, until the whole group passes
            mems = [m for m in bar if m is not b and (m.get("stack_of") or {}).get("id") == so["id"]]
            for m in mems:
                if len(m["pts"]) != len(P):
                    raise SystemExit(f"tyre facing: stack {so['id']!r}: members of unequal length ({len(m['pts'])} / {len(P)} points)")
            olds = [np.array(m["pts"], float) for m in mems]
            for _ in range(len(P) + 1):
                disp = P[:, :2] - P_old[:, :2]
                bad = set()
                for Q0 in olds + [P_old]:
                    Qr = np.round(Q0[:, :2] + disp, 2)
                    _, _, dq = trk.project(Qr)
                    bad |= {int(j) for j in np.nonzero((dq < gmin_ - 1e-9) & (np.hypot(*disp.T) > 0))[0]}
                if not bad:
                    break
                for j in bad:
                    P[j, :2] = P_old[j, :2]
                log(f"tyre facing: stack {so['id'][:50]!r}: {len(bad)} points held where a translated member would come inside {gmin_} m of the edge")
            moved = [i for i in moved] if np.hypot(*(P[:, :2] - P_old[:, :2]).T).max() > 0 else []
            for m, Q0 in zip(mems, olds):
                Q = Q0.copy(); Q[:, :2] += P[:, :2] - P_old[:, :2]
                Q[:, 2] = trk.ground(Q[:, 0], Q[:, 1])
                m["pts"] = [[rnd(x, 2), rnd(y, 2), rnd(z, 2)] for x, y, z in Q]
        if moved:
            P[:, 2] = trk.ground(P[:, 0], P[:, 1])
            b["pts"] = [[rnd(x, 2), rnd(y, 2), rnd(z, 2)] for x, y, z in P]
            log(f"tyre facing: {str(b.get('src', ''))[:70]}: {len(moved)} points onto the wall line ({off} m in front), stations {min(moved)}..{max(moved)}"
                + (f" (stack {so['id'][:40]!r}: its members in front follow)" if so else ""))


def tyre_rows_outside(trk, bar, face_min=0.5, wall_reach=1.5):
    """Round 12 (Sonoma judge r11 N67; barrier_rules.py rule 2): a tyre run whose drawn track-side face (row 1 is drawn
    0.6 m to the polyline's left) would stand closer than `face_min` m to the fitted edge is reversed so its second row
    lies behind the line, unless a rigid wall stands within `wall_reach` m behind it over 3 points or more (a facing: its
    rows belong in front of the wall). Config scenery.tyre_rows_outside {face_min, wall_reach} (absent: these defaults;
    False: off). Logged per run."""
    rig = [np.array(b["pts"], float)[:, :2] for b in bar if b["kind"] in BR.RIGID and len(b["pts"]) >= 2]
    R = np.concatenate(rig) if rig else np.zeros((0, 2))
    Rout = trk.project(R)[2] if len(R) else np.zeros(0)
    for b in bar:
        if b["kind"] != "tyres" or len(b["pts"]) < 2:
            continue
        P = np.array(b["pts"], float)
        i, _, dout = trk.project(P[:, :2])
        T = np.gradient(P[:, :2], axis=0)
        T /= np.maximum(np.linalg.norm(T, axis=1), 1e-9)[:, None]
        NL = np.c_[-T[:, 1], T[:, 0]]
        left = ((trk.C[i, :2] - P[:, :2]) * NL).sum(1) > 0
        face = BR.tyre_face_out(P, left, dout)
        if face.min() >= face_min or not left.any():
            continue
        flip = BR.tyre_face_out(P, ~left, dout)
        if flip.min() <= face.min():
            continue
        behind = 0
        if len(R):
            for q, dq in zip(P[:, :2], dout):
                m = np.hypot(*(R - q).T) <= wall_reach
                behind += bool((Rout[m] > dq + 0.3).any())
        if behind >= 3:
            log(f"tyre rows: {str(b.get('src', ''))[:70]}: face {face.min():+.2f} m from the edge but a facing ({behind} points with a wall behind): kept")
            continue
        b["pts"] = b["pts"][::-1]
        log(f"tyre rows: {str(b.get('src', ''))[:70]}: drawn face {face.min():+.2f} m from the edge with row 1 toward the track "
            f"(stations {int(i.min())}..{int(i.max())}): reversed, rows behind the line, face now {flip.min():+.2f} m")


def extend_parts_to_walls(parts, bar, reach=4.0, margin=0.3, label="pit lane", across=None):
    """The lane's paving out to its walls (config pit_lane.lane.to_walls {reach}, Buttonwillow judge r3: the footage has
    pavement from the lane to the K-rails where the NAIP half-width left a pale verge): an edge point whose ray from the
    part's centre, continued up to `reach` m past the edge, meets a wall run is moved to `margin` m short of it.
    `across` (Buttonwillow round 12, to_walls.across: [((lat, lon), (lat, lon)), ...], the two run ends of a wall's
    opening): the paving runs through the opening on the captures, so the edge in it goes out to the wall's line between
    the ends (no margin: the paved zone beyond starts on that line); not a barrier. Absent: as before."""
    S = [np.c_[np.array(b["pts"])[:-1, :2], np.array(b["pts"])[1:, :2]] for b in bar if b["kind"] in ("concrete", "pitwall")]
    M = [np.full(len(x), float(margin)) for x in S]
    for a_, b_ in (across or []):
        A_ = np.array(bl.enu(*a_), float); B_ = np.array(bl.enu(*b_), float)
        S.append(np.r_[A_, B_][None, :]); M.append(np.zeros(1))
    if not S:
        return
    S = np.concatenate(S); M = np.concatenate(M); a0, a1 = S[:, :2], S[:, 2:]
    moved = 0
    for part in parts:
        C = np.array(part["center"])[:, :2]
        for side in ("left", "right"):
            E = part[side]
            for j in range(len(E)):
                p, q = C[j], np.array(E[j][:2], float)
                d = q - p; L0 = float(np.linalg.norm(d))
                if L0 < 1e-6:
                    continue
                r = d / L0 * (L0 + reach); s_ = a1 - a0
                den = r[0] * s_[:, 1] - r[1] * s_[:, 0]; ok = np.abs(den) > 1e-9; qp = a0 - p
                t = np.where(ok, (qp[:, 0] * s_[:, 1] - qp[:, 1] * s_[:, 0]) / np.where(ok, den, 1), 9)
                u = np.where(ok, (qp[:, 0] * r[1] - qp[:, 1] * r[0]) / np.where(ok, den, 1), 9)
                hit = ok & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
                if hit.any():
                    k_ = np.nonzero(hit)[0][np.argmin(t[hit])]
                    tw = float(t[k_]) * float(np.linalg.norm(r)) - float(M[k_])
                    if tw > L0 + 0.05:
                        nq = p + d / L0 * tw
                        E[j] = [rnd(nq[0], 2), rnd(nq[1], 2)] + list(E[j][2:])
                        moved += 1
    log(f"{label}: {moved} edge points extended to the walls (pit_lane.lane.to_walls)")


def clip_parts_at_walls(parts, bar, margin=0.3, label="closed roads", heads=False):
    """A closed road's paving stops at a wall (config scenery.closed_roads_clip_walls, 20 Oct 2026: the NAIP half-width
    of Sonoma's drag strip reached under the pit-straight wall): an edge point whose segment from the part's centre crosses
    a wall, tyre wall or Armco run is moved back to 0.3 m short of the crossing. Heights are kept (the profile is linear
    across, the clipped side keeps its own row value)."""
    S = []
    for b in bar:
        if b["kind"] in ("concrete", "pitwall", "tyres", "armco"):
            P = np.array(b["pts"])[:, :2]
            S.append(np.c_[P[:-1], P[1:]])
    if not S:
        return
    S = np.concatenate(S)
    a0, a1 = S[:, :2], S[:, 2:]
    moved = 0
    for part in parts:
        C = np.array(part["center"])[:, :2]
        for side in ("left", "right"):
            E = np.array(part[side])
            for j in range(len(E)):
                p, q = C[j], E[j, :2]
                r = q - p; s_ = a1 - a0
                den = r[0] * s_[:, 1] - r[1] * s_[:, 0]
                ok = np.abs(den) > 1e-9
                qp = a0 - p
                t = np.where(ok, (qp[:, 0] * s_[:, 1] - qp[:, 1] * s_[:, 0]) / np.where(ok, den, 1), 9)
                u = np.where(ok, (qp[:, 0] * r[1] - qp[:, 1] * r[0]) / np.where(ok, den, 1), 9)
                hit = ok & (t >= 0) & (t <= 1) & (u >= 0) & (u <= 1)
                if hit.any():
                    tt = float(t[hit].min()); L = float(np.linalg.norm(r))
                    tt = max(0.0, tt - margin / max(L, 1e-6))
                    E[j, :2] = p + r * tt; moved += 1
            if heads:
                # round 14D (config scenery.pit_lane_clip_heads; Sonoma's T11 thick wall): a wall's END between two edge rows
                # (the row before it misses the wall, the row after it is clipped) lies inside the strip between them; both
                # rows are brought in to `margin` m short of the end along their own rays. Absent: as before
                V = np.concatenate([np.array(b["pts"])[[0, -1], :2] for b in bar if b["kind"] in ("concrete", "pitwall", "tyres", "armco") and len(b["pts"]) >= 2])
                for j in range(len(E) - 1):
                    quad = np.array([C[j], E[j, :2], E[j + 1, :2], C[j + 1]])
                    for v in V:
                        if not _in_poly(v, quad):
                            continue
                        for k in (j, j + 1):
                            r = E[k, :2] - C[k]; L = float(np.linalg.norm(r))
                            if L < 1e-6:
                                continue
                            tv = float((v - C[k]) @ (r / L)) - margin
                            if 0 < tv < L:
                                E[k, :2] = C[k] + r / L * tv; moved += 1
            if heads:
                # round 14D review (D, third review 3): `margin` holds as a segment-to-segment clearance on the ROUNDED edges,
                # crossings included, against EVERY barrier run passed in: an edge segment nearer a run than `margin` has both
                # its rows moved along the perpendicular from the run's nearest point by the deficit (+ 0.011 m), which
                # converges where a ray-wise move does not (a wall almost parallel to the rays); a residual violation after
                # 50 passes fails the build (and clearance_report is checked again after the clip, a postcondition)
                from shapely.geometry import LineString
                from shapely.ops import nearest_points
                from shapely.strtree import STRtree
                W_ = [LineString(np.array(b_["pts"])[:, :2]) for b_ in bar
                      if b_["kind"] in ("concrete", "pitwall", "tyres", "armco") and len(b_["pts"]) >= 2]
                tree = STRtree(W_) if W_ else None
                for _ in range(50):
                    fixed = 0
                    for j in range(len(E) - 1):
                        if tree is None:
                            break
                        Er = np.round(E[:, :2], 2)
                        seg = LineString([tuple(Er[j]), tuple(Er[j + 1])])
                        near_ = [W_[k] for k in tree.query(seg.buffer(margin + 0.02))]
                        if not near_:
                            continue
                        w_ = min(near_, key=seg.distance)
                        dmin = seg.distance(w_)
                        if dmin >= margin - 1e-6:
                            continue
                        ps, pw = nearest_points(seg, w_)
                        u = np.array([ps.x - pw.x, ps.y - pw.y])
                        cm = (C[j] + C[j + 1]) / 2 - np.array([pw.x, pw.y])    # from the wall toward the lane's centre line
                        step = margin - dmin + 0.011
                        if np.linalg.norm(u) < 1e-9:
                            u = cm                                              # crossing: toward the centre line
                        elif float(u @ cm) < 0:
                            # the edge lies BEYOND the run (the lane reaches over it): back across it, toward the centre line
                            u, step = -u, margin + dmin + 0.011
                        u /= max(np.linalg.norm(u), 1e-9)
                        for k in (j, j + 1):
                            E[k, :2] = E[k, :2] + u * step
                        fixed += 1
                    moved += fixed
                    if not fixed:
                        break
                Er = np.round(E[:, :2], 2)
                res_ = [(j, LineString([tuple(Er[j]), tuple(Er[j + 1])]).distance(w_)) for j in range(len(E) - 1) for w_ in W_]
                bad_ = [(j, d_) for j, d_ in res_ if d_ < margin - 1e-6]
                if bad_:
                    j_, d_ = min(bad_, key=lambda x: x[1])
                    raise SystemExit(f"{label}: edge clearance {d_:.3f} m < {margin} m at {side} rows {j_}-{j_ + 1} after the clip (review D)")
            part[side] = [[rnd(x, 2), rnd(y, 2), rnd(z, 3)] for x, y, z in E]
    log(f"{label}: {moved} edge points clipped at walls")


def clearance_report(parts, bar):
    """Round 14D review (D): the smallest segment-to-segment distance between the parts' edges (as stored) and the wall,
    tyre and Armco runs (crossing = 0), with where it is. Pure."""
    from shapely.geometry import LineString
    W_ = [LineString(np.array(b["pts"])[:, :2]) for b in bar if b["kind"] in ("concrete", "pitwall", "tyres", "armco") and len(b["pts"]) >= 2]
    best = (np.inf, None)
    for part in parts:
        for side in ("left", "right"):
            E = LineString(np.array(part[side])[:, :2])
            for w_ in W_:
                d = E.distance(w_)
                if d < best[0]:
                    best = (d, side)
    return best


def _in_poly(p, P):
    """Point in polygon (even-odd). Pure."""
    x, y = float(p[0]), float(p[1]); inside = False
    for i in range(len(P)):
        x1, y1 = P[i]; x2, y2 = P[(i + 1) % len(P)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def ortho_paint_over(trk, img, items, ring=3.0, lift=18.0):
    """NAIP marks painted over (config scenery.ortho_paint_over, Buttonwillow judge r5: white kerb blocks of the 2022
    NAIP that now lie on the fitted road read as white smears on the asphalt): each {latlon: outline, src}; inside the
    outline, the pixels ON THE ROAD (between the fitted edges) brighter than the road's own median there by `lift`
    (luminance, 0-255) take the median colour of the road pixels of the outline grown by `ring` m."""
    from PIL import Image, ImageDraw
    o = trk.t["ortho"]
    H, W = img.shape[:2]
    sx, sy = W / (o["x1"] - o["x0"]), H / (o["y1"] - o["y0"])
    px = lambda P: [((x - o["x0"]) * sx, (o["y1"] - y) * sy) for x, y in P]  # noqa: E731
    road = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(road)
    Lq, Rq = trk.L[:, :2], trk.R[:, :2]
    for i in range(trk.n):
        j = (i + 1) % trk.n
        dr.polygon(px([Lq[i], Lq[j], Rq[j], Rq[i]]), fill=1)
    road = np.asarray(road, bool)
    out = img.copy()
    lum = img.astype(float) @ np.array([0.2126, 0.7152, 0.0722])
    for it in items:
        P = np.array([bl.enu(*q) for q in it["latlon"]], float)
        # `on`: 'road' (default: only pixels between the fitted edges) or 'any' (judge r6: the NAIP hatch in the pit-entry
        # gore, the drag-strip chevrons off the road; there the yellow cast counts as a mark too)
        area = road if it.get("on", "road") == "road" else np.ones_like(road)
        m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(px(P), fill=1); m = np.asarray(m, bool) & area
        c = P.mean(0); Pg = c + (P - c) * (1 + ring / max(1e-6, float(np.linalg.norm(P - c, axis=1).mean())))
        g = Image.new("L", (W, H), 0); ImageDraw.Draw(g).polygon(px(Pg), fill=1); g = np.asarray(g, bool) & area
        yel = img[..., 0].astype(float) - img[..., 2].astype(float)
        mark = (lum > np.median(lum[g]) + lift) if not it.get("dark") else (lum < np.median(lum[g]) - lift)   # dark: a dark NAIP mark (round 8, the ~1100 stripe)
        if it.get("on") == "any":
            mark |= yel > np.median(yel[g]) + 25
        ref = g & ~mark
        med = np.median(img[ref], axis=0)
        if it.get("tone") == "road":
            # round 8 (owner lap 2 note 7): the pit-in gore is paved; the ring's median came out tan (dirt in the ring):
            # the road's own median colour within 15 m of the outline instead
            Pr = c + (P - c) * (1 + 15.0 / max(1e-6, float(np.linalg.norm(P - c, axis=1).mean())))
            r_ = Image.new("L", (W, H), 0); ImageDraw.Draw(r_).polygon(px(Pr), fill=1); r_ = np.asarray(r_, bool) & road
            med = np.median(img[r_ & (lum < np.median(lum[r_]) + lift)], axis=0)
        if it.get("all"):
            # recolour the whole outline to the ring's median (a tone patch, e.g. green-toned ground: round 8 cp5)
            ref = g & ~m; med = np.median(img[ref], axis=0); mark = np.ones_like(mark)
        hit = m & mark
        out[hit] = med.astype(np.uint8)
        log(f"ortho paint-over: {int(hit.sum())} px ({hit.sum() * 0.36:.0f} m2) {"on the road" if it.get("on", "road") == "road" else "in the outline"} -> {med.astype(int).tolist()} ({it['src'][:60]})")
    return out


def pit_tone_match(trk, pit, img, opt):
    """One road material for the pit lane (config pit_lane.lane.match_track_tone {k, paint}, 21 Oct 2026; Sonoma owner
    notes 17, 24-26): the NAIP ortho shows the pit lane's lighter paving and its paint smears at 0.6 m/px, so the lane's
    ribbon read as a second, lighter, mottled road beside the track. Inside the pit-lane polygon (outside the track's own
    paved width) every pixel's luminance is mapped onto the track asphalt's: l' = m_track + k (l - m_pit), the medians
    taken over each polygon, the colour kept by a per-pixel gain; pixels brighter than the pit's `paint` quantile
    (painted lines) keep k = 1 relative to the new median. The seam is the lane polygon's edge, which is the measured
    lane boundary (clipped at the track edge and the lane's walls)."""
    from PIL import Image, ImageDraw
    o = trk.t["ortho"]
    H, W = img.shape[:2]
    sx, sy = W / (o["x1"] - o["x0"]), H / (o["y1"] - o["y0"])
    px = lambda P: [((x - o["x0"]) * sx, (o["y1"] - y) * sy) for x, y in P]  # noqa: E731
    # the track's paved area as quads station by station (the loop is not one simple polygon)
    mt = Image.new("L", (W, H), 0)
    dt = ImageDraw.Draw(mt)
    Lp, Rp = trk.L[:, :2], trk.R[:, :2]
    for i in range(trk.n):
        j = (i + 1) % trk.n
        dt.polygon(px([Lp[i], Lp[j], Rp[j], Rp[i]]), fill=1)
    mp = Image.new("L", (W, H), 0)
    dp = ImageDraw.Draw(mp)
    for part in pit["parts"]:
        Lq, Rq = np.array(part["left"])[:, :2], np.array(part["right"])[:, :2]
        for i in range(len(Lq) - 1):
            dp.polygon(px([Lq[i], Lq[i + 1], Rq[i + 1], Rq[i]]), fill=1)
    T_ = np.asarray(mt).astype(bool)
    P_ = np.asarray(mp).astype(bool) & ~T_
    f = img.astype(np.float32)
    lum = f @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    m_t, m_p = float(np.median(lum[T_])), float(np.median(lum[P_]))
    k, q = float(opt.get("k", 0.5)), float(opt.get("paint", 0.97))
    lp = lum[P_]
    thr = float(np.quantile(lp, q))
    new = np.where(lp > thr, m_t + (lp - m_p), m_t + k * (lp - m_p))
    gain = np.clip(new / np.maximum(lp, 1.0), 0.2, 1.5)
    out = f.copy()
    out[P_] = np.clip(f[P_] * gain[:, None], 0, 255)
    log(f"pit lane tone: {int(P_.sum())} ortho px, median luminance {m_p:.1f} -> track's {m_t:.1f} (k {k}, paint above "
        f"the {q:.2f} quantile {thr:.1f} kept)")
    return out.astype(np.uint8)


def pit_lane(trk, osm):
    """Paved pit lane from the OSM "Pit Lane" way: 1 m stations, half-widths from the NAIP asphalt extent
    (build_laguna.detect_edges, clamped 3-6 m, fallback 4 m), and the track-facing edge clamped to the track edge so
    the two surfaces meet without overlapping. Where the pit lane runs inside the track's own paved width (the
    pit-exit apron through T1 is part of the v2 track) it is dropped, so it comes as separate parts. Heights: DEM
    across the section, corrected linearly so a clamped edge matches the track's edge height (smooth merges)."""
    from PIL import Image
    from scipy.ndimage import gaussian_filter1d

    w = [w for w in osm.ways if w["tags"].get("name") == PIT_WAY]
    if not w:
        return None
    return lane_parts(trk, w[0]["xy"], PIT_HALF_DEFAULT, "pit lane")


def lane_parts(trk, xy, half_default, label, clip=(3.0, 6.0), halves=None):
    """A paved lane along polyline xy as parts in the pit-lane strip layout (pit_lane's method; closed_roads too).
    halves (Buttonwillow round 13, the paddock bands): one half-width per point of xy (the same both sides) in place of the
    image's width; the points are then used as given (no resampling or smoothing; ~1 m apart), so the bands' centre lines
    and widths are exactly the declared ones."""
    from PIL import Image
    from scipy.ndimage import gaussian_filter1d

    if halves is None:
        P = resample_line(xy, 1.0)
        P = np.c_[gaussian_filter1d(P[:, 0], 2, mode="nearest"), gaussian_filter1d(P[:, 1], 2, mode="nearest")]
    else:
        # the declared points as given (one per metre): neighbouring bands declared on the same stations keep their
        # points on common normals, so their ends line up and the nearest-centre choice between them is the perpendicular one
        P = np.asarray(xy, float)
        sp_ = np.hypot(*np.diff(P, axis=0).T)
        if sp_.min() < 0.5 or sp_.max() > 1.5:
            raise SystemExit(f"{label}: declared points with halves must be ~1 m apart ({sp_.min():.2f}-{sp_.max():.2f} m)")
    n = len(P)
    d = np.gradient(P, axis=0)
    T = d / np.linalg.norm(d, axis=1, keepdims=True)
    Np = np.c_[-T[:, 1], T[:, 0]]
    # width from the image
    o = trk.t["ortho"]
    raw = os.path.join(CACHE, f"naip_{int(o['x0'])}_{int(o['y0'])}_{int(o['x1'])}_{int(o['y1'])}_{o['width_px']}x{o['height_px']}.png")
    half = np.full((n, 2), float(half_default))
    src = f"default {half_default} m"
    if halves is not None:
        h_ = np.asarray(halves, float)
        half = np.c_[h_, h_]
        src = f"declared per point ({h_.min():.2f}-{h_.max():.2f} m)"
    elif os.path.exists(raw):
        ortho = bl.Ortho(np.asarray(Image.open(raw).convert("RGB")), trk.box)
        try:
            h, stats, ok = bl.detect_edges(P, ortho, reach=9.0)
            for k in range(2):
                if np.isfinite(h[:, k]).all():
                    half[:, k] = np.clip(h[:, k], clip[0], clip[1])
            src = f"NAIP (left found {stats['left_found']:.0%}, right {stats['right_found']:.0%})"
        except Exception as e:  # noqa: BLE001
            log("pit lane: edge detection failed, using default width:", str(e)[:80])
    Lp = P + Np * half[:, :1]
    Rp = P - Np * half[:, 1:]
    zc = trk.ground(P[:, 0], P[:, 1])
    zL = trk.ground(Lp[:, 0], Lp[:, 1])
    zR = trk.ground(Rp[:, 0], Rp[:, 1])
    corrL = np.zeros(n)
    corrR = np.zeros(n)
    # clamp edges that fall inside the track onto the track edge (and take the track's edge height there)
    for E, corr, zE in ((Lp, corrL, zL), (Rp, corrR, zR)):
        i, lat, dout = trk.project(E)
        inside = dout < 0
        side = np.sign(lat[inside])
        ii = i[inside]
        E[inside] = trk.C[ii, :2] + trk.N[ii] * (side * trk.hw(ii, side))[:, None]
        tz = np.where(side > 0, trk.L[ii, 2], trk.R[ii, 2])
        corr[inside] = tz - trk.ground(E[inside, 0], E[inside, 1])
    # recentre on the clamped edges; width collapses where the lane runs inside the track
    width = np.linalg.norm(Lp - Rp, axis=1)
    keep = width > 1.0
    # a part must also have its centre outside the track
    _, _, dcen = trk.project((Lp + Rp) / 2)
    keep &= dcen > -0.5
    keep = ndi.binary_opening(keep, iterations=2)
    lab, nl = ndi.label(keep)
    fr = trk.t["profile"]["fractions"]
    parts = []
    for k in range(1, nl + 1):
        idx = np.nonzero(lab == k)[0]
        if len(idx) < 15:
            continue
        L, R = Lp[idx], Rp[idx]
        C = (L + R) / 2
        # pit lanes are flat across: fit a straight line to 9 DEM samples per section (kills lips from walls and
        # garages in the DEM), then add the clamped-edge correction, then smooth along the lane
        A9 = np.linspace(0, 1, 9)
        prof = []
        for j in range(len(idx)):
            X = L[j] + (R[j] - L[j]) * A9[:, None]
            zs = trk.ground(X[:, 0], X[:, 1])
            m, b0 = np.polyfit(A9, zs, 1)
            row = []
            for f in fr:
                a = (f + 1) / 2  # 0 left .. 1 right
                row.append(b0 + m * a + corrL[idx[j]] * (1 - a) + corrR[idx[j]] * a)
            prof.append(row)
        prof = gaussian_filter1d(np.array(prof), 3, axis=0, mode="nearest")
        # smoothing moves clamped edges off the track's edge height: put them back exactly (linear across)
        for E, col in ((L, 0), (R, -1)):
            ii, lat, dout = trk.project(E)
            touch = dout < 0.3
            if touch.any():
                tz = np.where(lat > 0, trk.L[ii, 2], trk.R[ii, 2])
                delta = np.where(touch, tz - prof[:, col], 0.0)
                a = (np.array(fr) + 1) / 2
                wgt = (1 - a) if col == 0 else a
                prof += delta[:, None] * wgt[None, :]
        # track-facing side and gap to the track edge, per station (for lines and shoulders in the app)
        _, _, dL = trk.project(L)
        _, _, dR = trk.project(R)
        cz = prof[:, len(fr) // 2]
        parts.append({
            "n": int(len(idx)),
            "center": [[rnd(a, 2), rnd(b, 2), rnd(c, 3)] for (a, b), c in zip(C, cz)],
            "left": [[rnd(a, 2), rnd(b, 2), rnd(c, 3)] for (a, b), c in zip(L, prof[:, 0])],
            "right": [[rnd(a, 2), rnd(b, 2), rnd(c, 3)] for (a, b), c in zip(R, prof[:, -1])],
            "profile_z": [[rnd(v, 3) for v in r] for r in prof],
            "gap_left": [rnd(v, 2) for v in dL], "gap_right": [rnd(v, 2) for v in dR],
            "track_s": [int(v) for v in trk.project(C)[0][[0, -1]]],
        })
    tot = sum(p["n"] for p in parts)
    log(f"{label}: {len(parts)} parts, {tot} m paved (OSM way {n} m), width {src}, "
        f"half-widths p50 {np.median(half, 0).round(1)} m; parts at track s " + ", ".join(f"{p['track_s'][0]}-{p['track_s'][1]}" for p in parts))
    return {"spacing_m": 1.0, "fractions": fr, "open": True, "parts": parts}


# Paved runoff seen in the footage (Laguna: the team's onboard 2026-10-12, GL030045), newer than the lidar and the NAIP
# image: config scenery.paved_runoff = (turn, metres before, metres after the corner's s). Outside of the corner.
PAVED_RUNOFF = []


def pit_exit_cones(trk, pit, barriers=None, spacing=16.0):
    """Cone line between the pit-exit lane and the race track (CONTRACTS section 2b `pit_exit_cones`).

    At Laguna the pit exit leaves the pit wall at the end of the front straight, runs on the driver's left through T1
    on pavement shared with the track (the v2 track's left edge includes that apron), and splits off as its own road
    inside T2 (rejoining after the hairpin). The boundary on the shared pavement is a painted blend line with orange
    cones on it (onboard GL030045 795-800 s, GL020045 2357-2375 s). Extent: from where the first pit_lane part abuts
    the track edge (pit wall ends) to where the second part leaves it. Position: the painted line in the NAIP image,
    which shows as the most blue-green (G+B)/2 - R strip across the left side, tracked station by station and
    smoothed (sigma 6 m). The line starts no earlier than the end of the fenced pit wall along the left edge (the
    barriers list), so no cone stands beside the wall. Cone spacing: the footage shows about 8 m, but the owner
    (who drove the real race) remembers far fewer cones, so the sim draws one every 16 m (17 Oct 2026)."""
    if not pit or not pit["parts"]:
        return None
    n = trk.n
    if len(pit["parts"]) == 1:
        return _pit_exit_cones_one_part(trk, pit["parts"][0], barriers, spacing)
    s0, s1 = _two_part_stretch(trk, pit)
    for w in barriers or []:
        if w["kind"] != "pitwall" or not w.get("fence"):
            continue
        i, lat, out = trk.project(np.array(w["pts"])[:, :2])
        near = (lat > 0) & (np.abs(out) < 2.0) & (((i - s0) % n) < 200)
        if near.any():
            s0 = max(s0, int(((i[near] - s0) % n).max() + s0) + 2)
    return _two_part_line(trk, s0, s1, spacing)


def _two_part_stretch(trk, pit):
    """(s0, s1): from where pit_lane part 0 last touches the track edge to where part 1 pulls away (gap > 0.5 m)."""
    a, b = pit["parts"][0], pit["parts"][1]
    ga = np.array(a["gap_right"])
    k0 = len(ga) - 1
    while k0 > 0 and ga[k0 - 1] < 0.5:
        k0 -= 1
    gb = np.array(b["gap_right"])
    k1 = 0
    while k1 < len(gb) - 1 and gb[k1 + 1] < 0.5:
        k1 += 1
    s0 = int(trk.project(np.array(a["center"])[k0:k0 + 1, :2])[0][0])
    s1 = int(trk.project(np.array(b["center"])[k1:k1 + 1, :2])[0][0])
    return s0, s1


def _two_part_line(trk, s0, s1, spacing):
    """The painted blend line between two pit-lane parts over stations s0..s1, tracked on the NAIP (pit_exit_cones)."""
    from PIL import Image

    n = trk.n
    st = np.arange(s0, s1 + (n if s1 < s0 else 0) + 1) % n
    o = trk.t["ortho"]
    raw = os.path.join(CACHE, f"naip_{int(o['x0'])}_{int(o['y0'])}_{int(o['x1'])}_{int(o['y1'])}_{o['width_px']}x{o['height_px']}.png")
    im = np.asarray(Image.open(raw).convert("RGB")).astype(float)
    H, W, _ = im.shape

    def samp(xy):
        px = (xy[:, 0] - o["x0"]) / (o["x1"] - o["x0"]) * (W - 1)
        py = (o["y1"] - xy[:, 1]) / (o["y1"] - o["y0"]) * (H - 1)
        return np.stack([ndi.map_coordinates(im[..., c], [py, px], order=1, mode="nearest") for c in range(3)], 1)

    D = np.arange(-10.0, 2.01, 0.25)  # m from the left edge (+ outside)
    lat = np.zeros(len(st))
    prev = None
    for j, i in enumerate(st):
        cand = trk.hl[i] + D
        A = samp(trk.C[i, :2] + trk.N[i] * cand[:, None])
        teal = (A[:, 1] + A[:, 2]) / 2 - A[:, 0]
        # first station: strongest line within 6 m of the edge; then track it (within 1.5 m of the previous pick)
        teal = np.where(D >= -6.0 if prev is None else np.abs(cand - prev) <= 1.5, teal, -1e9)
        prev = float(cand[int(np.argmax(teal))])
        lat[j] = prev
    lat = ndi.gaussian_filter1d(lat, 6, mode="nearest")
    P = trk.C[st, :2] + trk.N[st] * lat[:, None]
    P = resample_line(P, 2.0)
    log(f"pit-exit cones: s {s0}-{s1}, {len(P) * 2} m, lateral {lat.min():.1f}..{lat.max():.1f} m left of centre")
    return {"spacing_m": spacing, "s0": s0, "s1": s1, "pts": with_z(trk, P),
            "src": "NAIP painted blend line between pit_lane parts 0 and 1; spacing from onboard GL030045/GL020045"}


def _pit_exit_cones_one_part(trk, part, barriers, spacing):
    """One pit-lane part (Sonoma: pit-in before T11, round the outside, behind the wall, out after T1): the pit exit is
    the part's END. Where its track-facing edge lies on the track edge (gap under 0.5 m) up to that end, the lane
    merges on shared pavement: the cone line is that edge (the blend boundary), from the end of the pit wall on.
    The side comes from the part's lateral, not an assumption (20 Oct 2026)."""
    stretch = _one_part_stretch(trk, part)
    if stretch is None:
        return None
    side, s0, s1 = stretch
    for w in barriers or []:
        if w["kind"] != "pitwall" and not str(w.get("src", "")).startswith("declared"): continue
        i, lat, out = trk.project(np.array(w["pts"])[:, :2])
        # a wall AT the lane's track-facing edge (a pit wall, 2 m off the edge) ends the shared stretch; a wall on the
        # lane's far side (Sonoma's pit-out lane, 20 Oct 2026) does not
        near = (np.sign(lat) == side) & (out < (3.0 if SC_CFG.get("pit_exit_near_wall_only") else 6.0)) & (((i - s0) % trk.n) < ((s1 - s0) % trk.n))
        if near.any():
            s0 = max(s0, int(((i[near] - s0) % trk.n).max() + s0) + 2) % trk.n
    return _one_part_line(trk, side, s0, s1, spacing)


def _one_part_stretch(trk, part):
    """(side, s0, s1) of a one-part pit lane's shared stretch at its end (gap under 0.5 m), or None if under 10 m."""
    Cp = np.array(part["center"])[:, :2]
    _, latc, _ = trk.project(Cp[-20:])
    side = 1 if np.median(latc) > 0 else -1
    E = np.array(part["right"] if side > 0 else part["left"])[:, :2]   # the edge facing the track
    gap = np.array(part["gap_right"] if side > 0 else part["gap_left"])
    k1 = len(gap) - 1
    while k1 > 0 and gap[k1] >= 0.5: k1 -= 1
    k0 = k1
    while k0 > 0 and gap[k0 - 1] < 0.5: k0 -= 1
    if k1 - k0 < 10:
        return None
    s0 = int(trk.project(E[k0:k0 + 1])[0][0]); s1 = int(trk.project(E[k1:k1 + 1])[0][0])
    return side, s0, s1


def _one_part_line(trk, side, s0, s1, spacing):
    """The track edge on `side` over stations s0..s1 (the blend boundary of a one-part pit lane)."""
    st = np.arange(s0, s1 + (trk.n if s1 < s0 else 0) + 1) % trk.n
    if len(st) < 10:
        return None
    P = trk.C[st, :2] + trk.N[st] * (side * trk.hw(st, side))[:, None]
    P = resample_line(P, 2.0)
    log(f"pit-exit cones (one pit-lane part): s {s0}-{s1} on the {'left' if side > 0 else 'right'} edge, {len(P) * 2} m")
    return {"spacing_m": spacing, "s0": int(s0), "s1": int(s1), "pts": with_z(trk, P),
            "src": "the pit lane's track-facing edge where it merges at its end (one-part pit lane)"}


def pit_exit_line(trk, pit, pe, spacing=16.0):
    """Stage 1's pit-exit blend line (20 Oct 2026), from config centre.pit_exit `pe` and stage-1 evidence only; it reads
    no scenery or pit_lane key (stage 1 used to take it from pit_exit_cones() on barriers(), both stage-3 readers that
    config_id('geometry') does not hash, so a scenery edit moved a passed centre).
      pe.line_latlon      the measured blend line [(lat, lon), ...] (cm-rounded ENU, as every cone line), used as given;
      else detected as pit_exit_cones() does (two parts: the painted line on the NAIP between them; one part: the
      lane's track-facing edge where it merges at its end), starting after the measured wall end:
      pe.wall_end_latlon  (lat, lon) of the end of the pit wall at the edge; the line starts 2 stations past its station
                          when that lies in the shared stretch (the measured fact pit_exit_cones() gets from barriers).
    Returns {spacing_m, s0, s1, pts, src} or None."""
    pe = pe or {}
    if pe.get("line_latlon"):
        ll = np.array(pe["line_latlon"], float)
        x, y = bl.enu(ll[:, 0], ll[:, 1])
        P = np.c_[x, y]
        i_, _, _ = trk.project(P[[0, -1]])
        log(f"pit-exit line (centre.pit_exit.line_latlon): stations {int(i_[0])}-{int(i_[1])}, {len(P)} points")
        return {"spacing_m": spacing, "s0": int(i_[0]), "s1": int(i_[1]), "pts": with_z(trk, P), "src": pe.get("src", "")}
    if not pit or not pit["parts"]:
        return None
    n = trk.n
    we = None
    if pe.get("wall_end_latlon"):
        x, y = bl.enu(*pe["wall_end_latlon"])
        we = int(trk.project(np.array([[float(x), float(y)]]))[0][0])
    if len(pit["parts"]) == 1:
        stretch = _one_part_stretch(trk, pit["parts"][0])
        if stretch is None:
            return None
        side, s0, s1 = stretch
        if we is not None:
            if ((we - s0) % n) < ((s1 - s0) % n):
                s0 = (((we - s0) % n) + s0 + 2) % n
                log(f"pit-exit line: the pit wall ends at station {we} (centre.pit_exit.wall_end_latlon)")
            else:
                log(f"pit-exit line: wall end station {we} outside the merge stretch {s0}..{s1}: not applied")
        else:
            log("pit-exit line: NO wall end given (centre.pit_exit.wall_end_latlon): the line starts where the lane joins")
        return _one_part_line(trk, side, s0, s1, spacing)
    s0, s1 = _two_part_stretch(trk, pit)
    if we is not None:
        if ((we - s0) % n) < 200:
            s0 = max(s0, ((we - s0) % n) + s0 + 2)
            log(f"pit-exit line: the pit wall ends at station {we} (wall_end_latlon)")
        else:
            log(f"pit-exit line: wall end station {we} not within 200 stations after {s0}: not applied")
    else:
        log("pit-exit line: NO wall end given (centre.pit_exit.wall_end_latlon): the line starts where the lane joins")
    return _two_part_line(trk, s0, s1, spacing)


def paved_zones(trk, osm):
    """Paved runoff areas as open strips in the pit_lane part layout (same physics/rendering path). Inner edge = the
    track edge on the outside of the corner; width = distance to the nearest outside wall minus 1.5 m (6-25 m, 12 m
    if there is no wall), tapered over 15 m at both ends; heights = the surface the car would drive on there anyway
    (shoulder blend + heightfield), so a zone never adds a crease."""
    from scipy.ndimage import gaussian_filter1d

    corners = {c["turn"]: c for c in trk.t["corners"] if c.get("turn")}
    walls = []
    for w in osm.select(lambda t: t.get("barrier") == "wall", trk.box):
        P = resample_line(w["xy"], 2.0)
        i, lat, dout = trk.project(P)
        walls.append(np.c_[i, lat, dout])
    W = np.concatenate(walls) if walls else np.zeros((0, 3))
    fr = trk.t["profile"]["fractions"]
    parts = []

    def make_part(turn, st, side, width):
        inner = trk.C[st, :2] + trk.N[st] * (side * trk.hw(st, side))[:, None]
        outer = inner + trk.N[st] * (side * width)[:, None]
        # smooth centreline with perpendicular edges: the track's station normals carry noise, and a wobbly zone
        # tangent makes the physics' lateral -> profile mapping jump between segments
        C0 = gaussian_filter1d((inner + outer) / 2, 4, axis=0, mode="nearest")
        Tz = np.gradient(C0, axis=0)
        Tz /= np.linalg.norm(Tz, axis=1, keepdims=True)
        Nz = np.c_[-Tz[:, 1], Tz[:, 0]]
        Lr, Rr = (outer, inner) if side > 0 else (inner, outer)
        hl = gaussian_filter1d(((Lr - C0) * Nz).sum(1), 2, mode="nearest")
        hr = gaussian_filter1d(-((Rr - C0) * Nz).sum(1), 2, mode="nearest")
        L = C0 + Nz * hl[:, None]
        R = C0 - Nz * hr[:, None]
        # Heights: exactly what the driven surface would be there without the zone (the track's edge height blending to
        # the heightfield over the 5 m shoulder, then the heightfield), lightly smoothed along s. Paving changes the
        # grip and the look, not the shape, so the zone's edges and tapered ends meet the track shoulder and the
        # terrain with no crease (a flat fit to the DEM did not).
        SHOULDER = 5.0
        prof = []
        for j in range(len(st)):
            pts = np.array([L[j] + (R[j] - L[j]) * (f + 1) / 2 for f in fr])
            ii, lat, dout = trk.project(pts)
            ez = np.where(lat > 0, trk.L[ii, 2], trk.R[ii, 2])  # track edge height abeam each point
            h = trk.ground(pts[:, 0], pts[:, 1])
            d = np.maximum(dout, 0.0)
            u = np.minimum(d / SHOULDER, 1.0)
            prof.append(ez + u * u * (3 - 2 * u) * (h - ez))  # same smoothstep shoulder as src/physics/track.ts
        prof = gaussian_filter1d(np.array(prof), 1.5, axis=0, mode="nearest")
        C = (L + R) / 2
        cz = prof[:, len(fr) // 2]
        gap_in, gap_out = np.zeros(len(st)), np.full(len(st), 99.0)
        parts.append({
            "n": int(len(st)), "turn": turn,
            "center": [[rnd(x, 2), rnd(y, 2), rnd(z, 3)] for (x, y), z in zip(C, cz)],
            "left": [[rnd(x, 2), rnd(y, 2), rnd(z, 3)] for (x, y), z in zip(L, prof[:, 0])],
            "right": [[rnd(x, 2), rnd(y, 2), rnd(z, 3)] for (x, y), z in zip(R, prof[:, -1])],
            "profile_z": [[rnd(v, 3) for v in r] for r in prof],
            "gap_left": [rnd(v, 2) for v in (gap_out if side > 0 else gap_in)],
            "gap_right": [rnd(v, 2) for v in (gap_in if side > 0 else gap_out)],
            "track_s": [int(st[0]), int(st[-1])],
        })

    for turn, before, after in PAVED_RUNOFF:
        c = corners.get(turn)
        if not c:
            continue
        side = -1 if c["dir"] == "left" else 1
        st = np.arange(c["s"] - before, c["s"] + after + 1) % trk.n
        wd = np.full(len(st), np.nan)
        for k, sv in enumerate(st):
            m = (np.abs(((W[:, 0] - sv + trk.n / 2) % trk.n) - trk.n / 2) < 4) & (np.sign(W[:, 1]) == side) & (W[:, 2] > 3) & (W[:, 2] < 40)
            if m.any():
                wd[k] = W[m, 2].min()
        width = np.where(np.isfinite(wd), wd - 1.5, 12.0)
        width = gaussian_filter1d(np.clip(ndi.median_filter(width, 9, mode="nearest"), 6, 25), 3, mode="nearest")
        ramp = np.clip(np.minimum(np.arange(len(st)), np.arange(len(st))[::-1]) / 15.0, 0, 1)
        width = np.maximum(width * (0.5 - 0.5 * np.cos(np.pi * ramp)), 0.4)
        make_part(turn, st, side, width)
        log(f"paved runoff {turn}: s {st[0]}-{st[-1]}, {'left' if side > 0 else 'right'} side, width p50 {np.median(width):.1f} m "
            f"({np.isfinite(wd).mean():.0%} of stations bounded by an OSM wall)")
    # drivable runoff zones bounded by measured lines (config scenery.runoff_zones, Buttonwillow 21 Oct 2026: the T2
    # runoff the owner marked, from the track edge out to the outer-loop block line): {name, side, s: (s0, s1) track
    # metres, outer_latlon, src}; the width per station is the outer line's distance beyond the edge, square ends
    for z in SC_CFG.get("runoff_zones", []):
        sd = 1 if z["side"] == "left" else -1
        a_, b_ = (int(round(v / trk.sp)) for v in z["s"])
        st = np.arange(a_, b_ + 1) % trk.n
        O = _ll_line(z["outer_latlon"], 1.0)
        i_, lat_, dout_ = trk.project(O)
        wz = np.interp(np.arange(a_, b_ + 1), np.sort(i_), dout_[np.argsort(i_)])
        make_part(z["name"], st, sd, np.clip(wz, 0.5, 60.0))
        if z.get("surface"):
            parts[-1]["surface"] = z["surface"]   # absent: the aerial photo's own colour (paved runoff)
        log(f"runoff zone {z['name']}: s {a_}-{b_} {z['side']}, width {np.min(wz):.1f}-{np.max(wz):.1f} m ({z['src'][:60]})")
    return {"spacing_m": 1.0, "fractions": fr, "open": True, "parts": parts}


def edge_lines(trk, kerb, osm, gap=3, min_run=10):
    """Painted white edge lines along both edges, except through kerbs (plus `gap` m) and where the pit lane merges
    with the left edge. The NAIP image cannot show them: at 0.6 m/px the 0.12 m line is blurred, and asphalt and dry
    dirt have nearly the same luminance there (they differ in hue), so lines are assumed everywhere else."""
    n = trk.n
    runs = []
    pit = [w for w in osm.ways if w["tags"].get("name") == PIT_WAY]
    merge = np.zeros(n, bool)
    if pit:
        i, lat, dout = trk.project(resample_line(pit[0]["xy"], 1.0))
        for k in np.nonzero((lat > 0) & (dout < 1.5))[0]:
            merge[(np.arange(i[k] - 6, i[k] + 7)) % n] = True
    for side in (1, -1):
        on = np.ones(n, bool)
        for k in kerb:
            if k["side"] == side:
                on[np.arange(k["s0"] - gap, k["s1"] + gap) % n] = False
        # (pit-lane merges keep the line: it is the painted blend line between pit exit and track)
        # contiguous runs on the closed loop
        if on.all():
            runs.append({"side": side, "s0": 0, "s1": n})
            continue
        start = int(np.argmin(on))  # begin scanning at a gap
        s = None
        for j in range(start, start + n + 1):
            v = on[j % n]
            if v and s is None:
                s = j
            elif not v and s is not None:
                if j - s >= min_run:
                    runs.append({"side": side, "s0": s % n, "s1": s % n + (j - s)})
                s = None
    tot = {sd: sum(r["s1"] - r["s0"] for r in runs if r["side"] == sd) for sd in (1, -1)}
    log(f"edge lines: {len(runs)} runs, left {tot[1]} m, right {tot[-1]} m of {n} m (lines kept through the {merge.sum()} m of pit-lane merges as blend lines)")
    return runs


def board(trk, s, side, extra, kind, text, h=1.8, w=1.2, face=0.0):
    st = int(s) % trk.n
    p = trk.C[st, :2] + trk.N[st] * side * (trk.hw(st, side) + extra)
    z = float(trk.ground(p[0], p[1])[0])
    tx, ty = trk.T[st]
    # boards face oncoming traffic: their normal points against the driving direction
    heading = math.atan2(-ty, -tx) + face
    return {"kind": kind, "text": text, "x": rnd(p[0], 2), "y": rnd(p[1], 2), "z": rnd(z, 2),
            "heading": rnd(heading, 3), "h": h, "w": w}


# config scenery.banner_boards: (turn, s offset from its apex, side +1 left/-1 right, text, board width m, distance
# beyond the edge m or None = at the outside wall), from the onboard frames
BANNER_BOARDS = []


def fence_board(trk, st, side, dist, text, width):
    """A banner board standing just in front of the outside wall (or `dist` m beyond the edge), facing the track."""
    if dist is None:
        # just in front of the nearest outside wall within 3 m along the track, else 8 m out
        best = None
        for i, lat, dout in _WALL_CACHE:
            m = (np.abs(((i - st + trk.n / 2) % trk.n) - trk.n / 2) < 3) & (np.sign(lat) == side) & (dout > 2) & (dout < 40)
            if m.any():
                d = float(dout[m].min())
                best = d if best is None else min(best, d)
        dist = best - 0.4 if best is not None else 8.0
    p = trk.C[st, :2] + trk.N[st] * side * (trk.hw(st, side) + dist)
    heading = math.atan2(-side * trk.N[st, 1], -side * trk.N[st, 0])  # face the track
    return {"kind": "banner", "text": text, "x": rnd(p[0], 2), "y": rnd(p[1], 2), "z": rnd(float(trk.ground(*p)[0]), 2),
            "heading": rnd(heading, 3), "h": 1.4, "w": width}


_WALL_CACHE = []


def _wall_stretch(trk, name, s0, s1):
    """The declared wall `name` (config scenery.declared_walls) between track s0 and s1 (metres, s0 < s1 or wrapping),
    as one ENU polyline in its own order, its height and the lift of its top across hollows per point (round 12)."""
    if name not in DECLARED_WALLS:
        raise SystemExit(f"no declared wall named {name!r}")
    a, b = int(round(s0 / trk.sp)) % trk.n, int(round(s1 / trk.sp)) % trk.n
    best = None
    for P, h, lift in DECLARED_WALLS[name]:
        i, _, _ = trk.project(P)
        m = ((i - a) % trk.n) <= ((b - a) % trk.n)
        if m.sum() >= 2 and (best is None or m.sum() > best[0].shape[0]):
            best = (P[m], h, lift[m])
    if best is None:
        raise SystemExit(f"declared wall {name!r} does not reach s {s0}-{s1}")
    return best


def wall_boards(trk):
    """Advertising boards on a declared wall as plain coloured panels, no logos (config scenery.wall_boards, 20 Oct
    2026): each {wall: declared wall name, s: (s0, s1) track metres, h: panel height (m), colors: [hex, ...] taken in
    turn, panel: panel length (m, default 6), base: height of the panel's bottom above the ground (default the wall's
    top), names: [(text, background, text colour), ...] in turn instead of colors (round 6: the sponsor names the footage
    shows typed as plain text in the observed colours, no logo artwork), src}. Panels stand on the wall line, facing the track ('sign' landmarks with no text)."""
    out = []
    for wb in SC_CFG.get("wall_boards", []):
        P, wh, lift = _wall_stretch(trk, wb["wall"], *wb["s"])
        L = resample_line(P, wb.get("panel", 6.0))
        names = wb.get("names")           # round 6: [(text, background, text colour), ...] in turn (typed names, no logos)
        cols = [n_[1] for n_ in names] if names else wb["colors"]
        for k in range(len(L) - 1):
            a, b = L[k], L[k + 1]
            m = (a + b) / 2
            w = float(np.linalg.norm(b - a))
            if w < 1.0:
                continue
            i_, lat_, _ = trk.project(m[None])
            to = trk.C[i_[0], :2] - m
            n_ = np.array([-(b - a)[1], (b - a)[0]]) / w
            if n_ @ to < 0:
                n_ = -n_
            p = m + n_ * float(wb.get("off", 0.12))  # on the wall's track face (round 10 `off`: further out, e.g. on a tyre facing's front)
            # round 12 (Sonoma judge r11 N65): a panel on a wall that is level across a hollow stands on the wall's top,
            # the bridged ground interpolated along the wall at the panel (the wall's top_z less h), not in the hollow
            j = int(np.argmin(np.hypot(*(P - m).T)))
            if lift[max(j - 1, 0):j + 2].any():
                zb = np.round(trk.ground(P[:, 0], P[:, 1]), 2) + lift
                k_ = min(max(j, 1), len(P) - 1)
                cands = []
                for a_ in (k_ - 1, k_):
                    if a_ + 1 >= len(P):
                        continue
                    d_ = P[a_ + 1] - P[a_]
                    u_ = float(np.clip((m - P[a_]) @ d_ / max(d_ @ d_, 1e-9), 0, 1))
                    cands.append((float(np.linalg.norm(P[a_] + d_ * u_ - m)), zb[a_] + (zb[a_ + 1] - zb[a_]) * u_))
                z = float(min(cands)[1]) + wb.get("base", wh)
            else:
                z = float(trk.ground(*p)[0]) + wb.get("base", wh)
            out.append({"kind": "sign", "text": names[k % len(names)][0] if names else "", "x": rnd(p[0], 2), "y": rnd(p[1], 2), "z": rnd(z, 2),
                        "heading": rnd(math.atan2(n_[1], n_[0]), 3), "h": wb["h"], "w": rnd(w + 0.02, 2),
                        "color": cols[k % len(cols)], **({"fg": names[k % len(names)][2]} if names else {}),
                        "src": f"wall board on {wb['wall']} ({wb['src']})",
                        # the top of a panel standing ON the wall (no `base`: boards on posts behind a wall are not
                        # part of its face), above the ground, for the coverage gate's wall heights (21 Oct 2026)
                        **({} if "base" in wb else {"top": rnd(wh + wb["h"], 2)})})
        log(f"wall boards on {wb['wall']} s {wb['s'][0]}-{wb['s'][1]}: {len(L) - 1} panels, {wb['h']} m tall")
    return out


def impact_barriers(trk):
    """Impact barriers (water-filled / foam blocks) at the nose of a declared wall (config scenery.impact_barriers,
    20 Oct 2026): each {wall: declared wall name, end: 'start' | 'end' of its polyline, w, d, h (m, across / along /
    tall), color, src}. A plain block in front of the wall's end, along the wall's direction ('impact' landmark)."""
    out = []
    for ib in SC_CFG.get("impact_barriers", []):
        P = max(DECLARED_WALLS[ib["wall"]], key=lambda q: len(q[0]))[0]
        a, b = (P[0], P[1]) if ib.get("end", "start") == "start" else (P[-1], P[-2])
        u = (a - b) / np.linalg.norm(a - b)        # pointing out of the wall's end
        d = ib.get("d", 2.0)
        # `overlap` (m, Buttonwillow judge r5): the block wraps the wall's square end by that much (one continuous nose)
        p = a + u * (d / 2 + 0.05 - ib.get("overlap", 0.0))
        out.append({"kind": "impact", "text": "", "x": rnd(p[0], 2), "y": rnd(p[1], 2), "z": rnd(float(trk.ground(*p)[0]), 2),
                    "heading": rnd(math.atan2(u[1], u[0]), 3), "h": ib.get("h", 1.0), "w": ib.get("w", 1.0), "d": d,
                    "color": ib.get("color", "#e8c21c"), **({"style": ib["style"]} if ib.get("style") else {}), "src": ib["src"]})
        log(f"impact barrier at the {ib.get('end', 'start')} of {ib['wall']}")
    return out


def _ll_line(latlon, step=1.0):
    ll = np.array(latlon, float)
    x, y = bl.enu(ll[:, 0], ll[:, 1])
    return resample_line(np.c_[x, y], step)


def _cone_style(cl):
    """Per-declaration cone colour and height (round 7, Sonoma owner note 42: small yellow cones on the pit-out blend
    line, the orange 0.7 m traffic cone stays the default)."""
    return {**({"color": cl["color"]} if cl.get("color") else {}), **({"size": float(cl["size"])} if cl.get("size") else {}),
            # round 7e (Sonoma owner note 57): 'delineator' = a tall orange pylon post with white bands (app), else a cone
            **({"style": cl["style"]} if cl.get("style") else {})}


def join_lane(lane_parts_, parts, fractions, near=0.6, ramp=4):
    """Buttonwillow round 12 (config closed_roads[].join_lane {reach}): where a closed road's paving meets the pit lane's
    paving edge to edge (the paddock strip in the paddock-side K-rail's openings: its right edge within `near` m of the
    lane's edge), the two separate DEM fits left a lip (0.075 m in the west opening). The road's profile takes the lane's
    edge height at the join, the correction fading linearly across the road to 0 at `reach` m from that edge and along it
    over `ramp` stations either side of the join; the lane is unchanged. Absent: as before."""
    from scipy.spatial import cKDTree
    names = {r_["name"]: r_["join_lane"] for r_ in SC_CFG.get("closed_roads", []) if r_.get("join_lane")}
    E, Z = [], []
    for lp in lane_parts_:
        for side, col in (("left", 0), ("right", -1)):
            for e_, pz in zip(lp[side], lp["profile_z"]):
                E.append(e_[:2]); Z.append(pz[col])
    kd = cKDTree(np.array(E, float)); Z = np.array(Z, float)
    fr = np.array(fractions, float)
    for part in parts:
        cfg_ = names.get(part.get("turn"))
        if not cfg_:
            continue
        reach = float(cfg_["reach"])
        prof = np.array(part["profile_z"], float); n = len(prof)
        # the edge that meets the lane: whichever of left / right lies nearer to it
        best = None
        for side, col in (("right", -1), ("left", 0)):
            d_, k_ = kd.query(np.array(part[side], float)[:, :2])
            if best is None or np.sum(d_ < near) > np.sum(best[0] < near):
                best = (d_, k_, side, col)
        d_, k_, side, col = best
        dz = np.where(d_ < near, Z[k_] - prof[:, col], 0.0)
        hit = d_ < near
        if not hit.any():
            log(f"join lane: {part['turn']}: no station meets the lane"); continue
        # ramp along the road beside each join run
        dz_r = dz.copy()
        idx = np.nonzero(hit)[0]
        for a_, b_ in _runs(hit):
            for k in range(1, ramp + 1):
                w = 1 - k / (ramp + 1)
                if a_ - k >= 0 and not hit[a_ - k]: dz_r[a_ - k] = dz[a_] * w
                if b_ + k < n and not hit[b_ + k]: dz_r[b_ + k] = dz[b_] * w
        width = np.linalg.norm(np.array(part["left"], float)[:, :2] - np.array(part["right"], float)[:, :2], axis=1)
        dist = ((1 - fr) / 2 if side == "right" else (1 + fr) / 2)[None, :] * width[:, None]   # m from the joining edge
        wcol = np.clip(1 - dist / reach, 0, 1)
        prof = prof + dz_r[:, None] * wcol
        part["profile_z"] = [[rnd(v, 3) for v in row] for row in prof]
        log(f"join lane: {part['turn']}: {int(hit.sum())} stations meet the lane's edge ({side} edge), lip "
            f"{float(np.abs(dz[hit]).max()):.3f} m closed (mean {float(dz[hit].mean()):+.3f} m), faded to 0 at {reach} m across")


def zones_meet_edge(trk, parts, reach=8.0, near=1.5, overlap=0.3):
    """Zone ends meeting the track at an angle leave a dirt wedge between the far end corner and the edge (Buttonwillow
    judge r5: tan strips at the crossover mouths). config scenery.zones_meet_edge: at an end whose nearest corner lies
    within `near` m of the road, each end point (left, centre, right) is moved along the part's direction toward the
    track until it lies `overlap` m inside the road (at most `reach` m); heights kept."""
    from shapely.geometry import Point, Polygon
    from shapely.ops import unary_union
    L, R, n = trk.L[:, :2], trk.R[:, :2], trk.n
    road = unary_union([Polygon([L[i], L[(i + 1) % n], R[(i + 1) % n], R[i]]).buffer(0) for i in range(n)])
    inner = road.buffer(-overlap)
    moved = 0
    for p in parts:
        C = np.array(p["center"])[:, :2]
        if len(C) < 3:
            continue
        for end in (0, -1):
            k, k2 = (0, 1) if end == 0 else (len(C) - 1, len(C) - 2)
            ds = [road.distance(Point(np.array(p[sd][k][:2]))) for sd in ("left", "center", "right")]
            if min(ds) > near or max(ds) < 0.05:
                continue
            t = C[k] - C[k2]; t /= np.linalg.norm(t)
            for sd in ("left", "center", "right"):
                q = np.array(p[sd][k][:2], float)
                if inner.contains(Point(q)):
                    continue
                for step in np.arange(0.1, reach + 1e-6, 0.1):
                    if inner.contains(Point(q + t * step)):
                        nq = q + t * step
                        p[sd][k] = [rnd(nq[0], 2), rnd(nq[1], 2)] + list(p[sd][k][2:])
                        moved += 1
                        break
    log(f"zones meet the edge: {moved} end points moved onto the road (scenery.zones_meet_edge)")


def declared_cone_lines(trk):
    """Cone lines along a stretch of the track edge (config scenery.cone_lines_declared, 20 Oct 2026): each {side:
    'left' | 'right', s: (s0, s1) track metres, off: metres outside the edge, spacing (m, default 4), src}; or (round 7)
    {latlon: the line measured on the captures (the painted line the cones stand on), spacing, src}; optional color and
    size (m) from the evidence."""
    out = []
    for cl in SC_CFG.get("cone_lines_declared", []):
        if cl.get("latlon"):
            P = _ll_line(cl["latlon"])
            out.append({"spacing_m": cl.get("spacing", 4.0), "pts": with_z(trk, P), "src": cl["src"], **_cone_style(cl)})
            log(f"cone line on a measured line, {len(P)} m")
            continue
        sd = 1 if cl["side"] == "left" else -1
        a, b = (int(round(v / trk.sp)) for v in cl["s"])
        st = np.arange(a, b + 1) % trk.n
        P = trk.edge_point(st, sd, cl.get("off", 0.5))
        out.append({"spacing_m": cl.get("spacing", 4.0), "pts": with_z(trk, P), "src": cl["src"], **_cone_style(cl)})
        log(f"cone line {cl['side']} s {cl['s'][0]}-{cl['s'][1]} ({cl.get('off', 0.5)} m outside the edge)")
    return out


_CAPS = []


def _clean_captures():
    """the clean z20 captures (name, centre x, y), for naming the capture under an owner stroke"""
    if not _CAPS:
        import captures as CAP_
        _CAPS.extend(CAP_.capture_list(CFG_ALL, "clean"))
    return _CAPS


def owner_mouth_cones(trk):
    """Cone lines ON the owner's red across each junction mouth (config scenery.owner_mouth_cones {from: the key holding
    the mouths (owner_mouths_r10), spacing, size, color, style_src, clip_out, label (the src's lead words; absent: "owner
    round-10 mouth"; Sonoma round 14C)}; Buttonwillow round 10, the owner's decision of 23 Oct
    2026 point 2): every mouth with cones=True gets one line on its line_latlon (his red, world points); cones=False
    (the pit entry) gets none. The closed roads' rule cones at the same mouths are switched off in the config
    (closed_roads[].mouth_cones); the cone_lines_declared rows stay (each is an onboard observation, not a rule).
    Returns (lines, mouth station ranges {side: [(lo, hi)]} on this package)."""
    oc = SC_CFG.get("owner_mouth_cones")
    if not oc:
        return [], {}
    out, ranges = [], {1: [], -1: []}
    for m in SC_CFG.get(oc.get("from", "owner_mouths_r10"), []):
        P = _ll_line(m["line_latlon"], 0.5)
        i, _, _ = trk.project(P)
        i = np.sort(np.asarray(i))
        if i[-1] - i[0] > trk.n / 2:
            i = np.sort(np.where(i < trk.n / 2, i + trk.n, i))
        sd = 1 if m["side"] == "left" else -1
        if not m.get("cones", True):
            log(f"owner mouth {m['side']} {m['lo']}-{m['hi']} ({m['kind']}): no cones ({m['src'][-120:]})")
            continue
        ranges[sd].append((int(i[0]), int(i[-1])))
        if oc.get("clip_out") is not None:
            # round 11 (judge r10: the Atlantic mouth cones stood up to 1.24 m inside the right edge, the crossover's
            # 0.74 m): where his red crosses onto the course (his red bulges past the fitted edge at the mouth corners,
            # which the owner-reference gates leave out +-12 stations), the line is clipped to the fitted edge: every
            # point less than clip_out m outside the edge on the mouth's side moves out along the station normal to
            # clip_out m beyond it; the line keeps its shape where it lies off the course
            j_, lat_, dout_ = trk.project(P)
            cut = dout_ < float(oc["clip_out"])
            if cut.any():
                P = P.copy()
                P[cut] = trk.edge_point(j_[cut], sd, float(oc["clip_out"]))
                log(f"owner mouth {m['side']} {m['lo']}-{m['hi']}: {int(cut.sum())} of {len(P)} points clipped to {oc['clip_out']} m "
                    f"outside the edge (deepest {max(0.0, -float(dout_[cut].min())):.2f} m inside)")
        mid = P[len(P) // 2]
        caps = sorted(_clean_captures(), key=lambda t: np.hypot(t["x"] - mid[0], t["y"] - mid[1]))[:2]
        out.append({"spacing_m": float(oc.get("spacing", 2.0)), "pts": with_z(trk, P),
                    "src": f"{oc.get('label', 'owner round-10 mouth')} {m['side']} {m['lo']}-{m['hi']} ({m['kind']}): cones on his red, drawn on the outline window over "
                           f"{' / '.join(t['name'] for t in caps)} ({m['src'][:120]}); style: {oc['style_src']}",
                    **_cone_style(oc)})
        log(f"owner mouth cones {m['side']} stations {int(i[0]) % trk.n}-{int(i[-1]) % trk.n}: {len(P) * 0.5:.0f} m on his red")
    log(f"owner mouth cones: {len(out)} lines")
    return out, ranges


def surface_marks(trk):
    """Crack-seal lines measured on the clean captures (config scenery.surface_marks {max, min_len, contrast}, Buttonwillow
    owner lap 2 note 18): inside the track polygon, pixels darker than the road's local median by `contrast` that are
    also a thin dark ridge (black-hat over 0.7 m); connected components elongated (length >= min_len m, length / width
    >= 6) become one straight segment each (principal axis); the strongest `max` kept; published as paint_lines (dark,
    0.1 m). Round 11 options (Buttonwillow, the owner's "Redraw"): polyline (each mark on its own measured line, `step` m
    bins), width, color, gloss (the paint line's specular sheen, 0-1), drop (measured reasons). The captures are the
    measurement, never a texture."""
    cfgm = SC_CFG.get("surface_marks")
    if not cfgm:
        return []
    import captures as CAP_
    from PIL import Image as Img, ImageDraw as IDraw
    tiles = CAP_.capture_list(CFG_ALL, "clean")
    mpp = (CFG_ALL["captures"]["mpp"])
    L, R, n = trk.L[:, :2], trk.R[:, :2], trk.n
    segs = []
    for t in tiles:
        im = np.asarray(Img.open(t["path"]).convert("L")).astype(np.float32); H, W = im.shape
        m = t["mask"](H, W)
        px = lambda P: [((x + t["dx"] - t["x"]) / mpp + W / 2, H / 2 - (y + t["dy"] - t["y"]) / mpp) for x, y in P]  # noqa: E731
        road = Img.new("L", (W, H), 0); dr = IDraw.Draw(road)
        near = np.hypot(trk.C[:, 0] - t["x"], trk.C[:, 1] - t["y"]) < 90
        for i in np.nonzero(near)[0]:
            j = (i + 1) % n
            dr.polygon(px([L[i], L[j], R[j], R[i]]), fill=1)
        road = ndi.binary_erosion(np.asarray(road, bool) & m, iterations=3)
        if road.sum() < 2000:
            continue
        med = ndi.median_filter(im, size=31)
        bh = ndi.grey_closing(im, size=(6, 6)) - im
        mark = road & (bh > cfgm.get("contrast", 14)) & (im < med - cfgm.get("contrast", 14) * 0.6)
        lab, k = ndi.label(mark, structure=np.ones((3, 3)))
        for c in range(1, k + 1):
            ys, xs = np.nonzero(lab == c)
            if len(xs) < 15:
                continue
            Q = np.c_[xs, ys].astype(float); mu = Q.mean(0); u, sv, vt = np.linalg.svd(Q - mu, full_matrices=False)
            ln = (sv[0] / math.sqrt(len(Q))) * math.sqrt(12) * mpp; wd = (sv[1] / math.sqrt(len(Q))) * math.sqrt(12) * mpp
            if ln < cfgm.get("min_len", 3.0) or ln / max(wd, 0.05) < 6:
                continue
            a = mu - vt[0] * ln / mpp / 2; b = mu + vt[0] * ln / mpp / 2
            wpt = lambda q: (t["x"] + (q[0] - W / 2) * mpp - t["dx"], t["y"] - (q[1] - H / 2) * mpp - t["dy"])  # noqa: E731
            wa, wb = wpt(a), wpt(b)
            line = None
            if cfgm.get("polyline"):
                # round 11 (the owner, 23 Oct 2026, "Redraw"): the mark's own wavy line, not the straight segment between
                # its ends: its pixels binned along the principal axis every `step` m (0.4), the median offset across it
                # per bin (median of 3 along), so the drawn line follows the seal as the capture shows it
                tq = (Q - mu) @ vt[0]; oq = (Q - mu) @ vt[1]
                bw = cfgm.get("step", 0.4) / mpp
                edges_ = np.arange(tq.min(), tq.max() + bw, bw)
                pts_ = []
                for b0 in edges_[:-1]:
                    sel = (tq >= b0) & (tq < b0 + bw)
                    if sel.any():
                        pts_.append((float(np.median(tq[sel])), float(np.median(oq[sel]))))
                if len(pts_) >= 2:
                    o_ = np.array([q[1] for q in pts_])
                    if len(o_) >= 3:
                        o_ = ndi.median_filter(o_, 3, mode="nearest")
                    line = [wpt(mu + vt[0] * q[0] + vt[1] * oo) for q, oo in zip(pts_, o_)]
            segs.append((float(bh[ys, xs].mean() * len(xs)), wa, wb, t["name"], line))
    # one per place: drop a segment whose midpoint lies within 1 m of a stronger one's (captures overlap)
    segs.sort(key=lambda q: -q[0]); kept = []
    for sc, a, b, nm, line in segs:
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        if any(math.dist(mid, ((k[1][0] + k[2][0]) / 2, (k[1][1] + k[2][1]) / 2)) < 1.0 for k in kept):
            continue
        kept.append((sc, a, b, nm, line))
        if len(kept) >= cfgm.get("max", 1500):
            break
    # round 11 (the owner, "Redraw"): marks dropped by a measured reason (surface_marks.drop [{a, b (lat, lon on the
    # track), lengthwise (deg), why}]): a mark whose midpoint projects between a and b and that runs within `lengthwise`
    # degrees of the track's direction (the pit-entry straight's centreline marks read as a dashed centre line)
    drops = []
    for d_ in cfgm.get("drop", []):
        ia, _, _ = trk.project(np.array([bl.enu(*d_["a"]), bl.enu(*d_["b"])], float))
        drops.append((int(ia[0]), int(ia[1]), float(d_.get("lengthwise", 30)), d_["why"]))
    if drops:
        keep2 = []
        for q in kept:
            a, b = np.array(q[1]), np.array(q[2]); mid = (a + b) / 2
            i_, lat_, _ = trk.project(mid[None])
            i_ = int(i_[0]); ang = math.degrees(math.acos(min(1.0, abs(float(((b - a) / (np.linalg.norm(b - a) or 1)) @ trk.T[i_])))))
            hit = [d for d in drops if (d[0] <= i_ <= d[1]) and ang <= d[2]]
            if hit:
                log(f"   surface mark dropped: s {i_ * trk.sp:.0f}, lateral {float(lat_[0]):+.1f} m, {np.linalg.norm(b - a):.1f} m long, "
                    f"{ang:.0f} deg to the track ({q[3]}): {hit[0][3][:100]}")
                continue
            keep2.append(q)
        log(f"surface marks: {len(kept) - len(keep2)} dropped (surface_marks.drop)")
        kept = keep2
    style = {"width": float(cfgm.get("width", 0.1)), "color": cfgm.get("color", "#2a2a2a")}
    if cfgm.get("gloss") is not None:
        style["gloss"] = float(cfgm["gloss"])
    out = [{**style, "pts": with_z(trk, np.array(line if (line and cfgm.get("polyline")) else [a, b]), 0.008),
            "src": f"surface mark (crack seal) measured on {nm}" + (" (its measured line)" if line and cfgm.get("polyline") else "")}
           for _, a, b, nm, line in kept]
    log(f"surface marks: {len(segs)} candidate segments on the clean captures, {len(out)} kept (max {cfgm.get('max', 1500)})"
        + (f"; drawn {style['width']} m {style['color']}" + (f", gloss {style['gloss']}" if 'gloss' in style else '') + ", each on its measured line" if cfgm.get("polyline") else ""))
    return out


def declared_paint_lines(trk):
    """Painted lines measured on the captures (config scenery.paint_lines_declared, round 7): each {latlon, width (m),
    color, double: gap between the two lines' centres (m, optional), src}. Drawn only."""
    out = []
    for pl in SC_CFG.get("paint_lines_declared", []):
        P = _ll_line(pl["latlon"], 1.0)
        offs = [0.0] if not pl.get("double") else [-pl["double"] / 2, pl["double"] / 2]
        for o in offs:
            Q = P.copy()
            if o:
                t = np.gradient(P, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True)
                Q = P + np.c_[-t[:, 1], t[:, 0]] * o
            out.append({"width": pl.get("width", 0.12), "pts": with_z(trk, Q, 0.01), "src": pl["src"],
                        **({"color": pl["color"]} if pl.get("color") else {})})
        log(f"paint line {pl.get('color', 'white')} {'double ' if pl.get('double') else ''}{len(P)} m")
    return out


def kerb_lines(trk):
    """Raised kerb strips off the lap (config scenery.kerb_lines, round 7b, Sonoma owner note 45): the painted kerbs round
    the closed roads' islands, measured on the captures as lat/lon lines (the kerb's centre); {latlon, width, colors
    (stripe, base) or a palette name, src}; the track's kerb profile height and stripe length; drawn so the ortho's
    flat kerb paint is covered by geometry (closed roads are not driven at race pace; not in the physics)."""
    out = []
    kc = SC_CFG.get("kerb", {})
    pal = kc.get("palettes", {})
    for k in SC_CFG.get("kerb_lines", []):
        P = _ll_line(k["latlon"], 0.5)
        c = k.get("colors", kc.get("colors", ["#b8433a", "#dedbd2"]))
        if isinstance(c, str):
            c = pal[c]
        out.append({"pts": with_z(trk, P), "width": k.get("width", 0.9), "height": (kc.get("profile") or {}).get("height", 0.08),
                    "stripe_m": kc.get("stripe_m", 1.0), "colors": list(c), "src": k["src"]})
        log(f"kerb line {len(P) * 0.5:.0f} m")
    return out


def ground_signs(trk):
    """Painted ground logos as typed text (config scenery.ground_signs, round 7b, Sonoma owner note 46): {latlon (centre),
    length (m, along the text), height (m, across), heading (deg, ENU, the text's reading direction), text, fg, bg (None =
    no panel), src}; the boards' rule: the name as text in the observed colours, no logo artwork. Drawn on the ground."""
    out = []
    for g in SC_CFG.get("ground_signs", []):
        xy = np.array(bl.enu(*g["latlon"]), float)
        out.append({"x": rnd(xy[0], 2), "y": rnd(xy[1], 2), "z": rnd(float(trk.ground(*xy)[0]), 2),
                    "heading": rnd(math.radians(g["heading"]), 3), "length": g["length"], "height": g.get("height", g["length"] / 4),
                    "text": g["text"], "fg": g.get("fg", "#ffffff"), **({"bg": g["bg"]} if g.get("bg") else {}), "src": g["src"]})
        log(f"ground sign '{g['text']}' {g['length']} m")
    return out


def landmarks(trk, T, brg):
    out = []
    corners = {c["turn"]: c for c in trk.t["corners"] if c.get("turn")}
    # brake marker boards 3-2-1 (100 ft steps are 30 m; the circuit uses 3/2/1 at roughly 150/100/50 m)
    for t in SC_CFG.get("brake_board_corners", []):
        c = corners[t]
        side = -1 if c["dir"] == "left" else 1
        for k, dist in ((3, 150), (2, 100), (1, 50)):
            out.append(board(trk, c["s"] - dist, side, 3.0, "brake", str(k), h=1.6, w=1.0))
    # corner-number boards at turn-in, outside (config scenery.corner_boards False: none, e.g. Sonoma, where the 2026
    # onboard shows no turn boards)
    for t, c in (corners.items() if SC_CFG.get("corner_boards", True) else []):
        side = -1 if c["dir"] == "left" else 1
        num = t[1:]
        out.append(board(trk, c["s"] - 75, side, 5.0, "corner", num, h=2.2, w=1.4))
    # starter's flag stand on the pit wall, just before the S/F bridge
    sf = next((b for b in brg if b["s"] < 120 or b["s"] > trk.n - 60), None)
    s_flag = (sf["s"] - 8) if sf else 30
    st = s_flag % trk.n
    p = trk.C[st, :2] + trk.N[st] * (trk.hw(st, 1) + 1.0)
    if SC_CFG.get("flagstand", True):
        out.append({"kind": "flagstand", "text": "", "x": rnd(p[0], 2), "y": rnd(p[1], 2),
                    "z": rnd(float(trk.ground(p[0], p[1])[0]), 2), "heading": rnd(math.atan2(-trk.T[st, 1], -trk.T[st, 0]), 3),
                    "h": 7.5, "w": 2.6})
    # corner-worker (marshal) posts and light masts from the evidence (config scenery.marshal_posts / light_masts,
    # 20 Oct 2026): lat/lon measured on the captures; a post faces the nearest track point
    # Round 8 (Sonoma owner note 61): a post with a measured footprint and heading (an owner-marked or capture-measured
    # outline) carries `heading_deg` (the bearing its open front faces, degrees clockwise from north), `d` (the depth
    # along that heading; `w` is the width across it) and `roof` (the roof colour); absent, the post faces the nearest
    # track point, is w x w and has the white roof, as before (every other post's record is unchanged)
    for mp in SC_CFG.get("marshal_posts", []):
        xy = np.array(bl.enu(*mp["latlon"]), float)
        if mp.get("heading_deg") is not None:
            b_ = math.radians(float(mp["heading_deg"]))
            hd = math.atan2(math.cos(b_), math.sin(b_))
        else:
            i_, _, _ = trk.project(xy[None])
            to = trk.C[i_[0], :2] - xy
            hd = math.atan2(to[1], to[0])
        out.append({"kind": "marshal", "text": mp.get("name", ""), "x": rnd(xy[0], 2), "y": rnd(xy[1], 2),
                    "z": rnd(float(trk.ground(*xy)[0]), 2), "heading": rnd(hd, 3),
                    "h": mp.get("h", 3.0), "w": mp.get("w", 2.4), "style": mp.get("style", "tower"),
                    **({"d": mp["d"]} if mp.get("d") else {}), **({"roof": mp["roof"]} if mp.get("roof") else {}),
                    **({"color": mp["color"]} if mp.get("color") else {}),
                    **{k: mp[k] for k in ("mound_h", "railing", "stair", "base_color", "body_h", "body_color", "pole", "roof", "fine") if k in mp and not (k == "roof" and mp.get("roof"))},
                    "src": mp["src"]})
    # free-standing tyre stacks and barrier blocks (config scenery.tyre_stacks, 21 Oct 2026): {latlon, h, w, style
    # 'tyres' | 'blocks', color, src}; drawn only (not in the collision world)
    for ts in SC_CFG.get("tyre_stacks", []):
        xy = np.array(bl.enu(*ts["latlon"]), float)
        i_, _, _ = trk.project(xy[None])
        to = trk.C[i_[0], :2] - xy
        out.append({"kind": "tyres", "text": "", "x": rnd(xy[0], 2), "y": rnd(xy[1], 2), "z": rnd(float(trk.ground(*xy)[0]), 2),
                    "heading": rnd(math.atan2(to[1], to[0]), 3), "h": ts.get("h", 0.84), "w": ts.get("w", 0.62),
                    "style": ts.get("style", "tyres"), **({"color": ts["color"]} if ts.get("color") else {}), "src": ts["src"]})
    # free-standing concrete blocks (config scenery.blocks, round 7, Sonoma owner note 38): {latlon, w (across), d (along
    # the track), h, style 'striped' | 'plain', color, src}, or a run {latlon: [a, b], every: m, ...} of blocks between two
    # measured ends; aligned with the track tangent; drawn only (landmark kind 'block')
    for bk in SC_CFG.get("blocks", []):
        pts = [np.array(bl.enu(*bk["latlon"]), float)] if not isinstance(bk["latlon"][0], (list, tuple)) else None
        if pts is None:
            P = _ll_line(bk["latlon"], 0.25)
            L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
            pts = [P[int(np.argmin(np.abs(L - d)))] for d in np.arange(0, L[-1] + 1e-6, bk.get("every", 2.0))]
        for xy in pts:
            i_, _, _ = trk.project(xy[None])
            tg_ = trk.T[i_[0]]
            out.append({"kind": "block", "text": "", "x": rnd(xy[0], 2), "y": rnd(xy[1], 2), "z": rnd(float(trk.ground(*xy)[0]), 2),
                        "heading": rnd(math.atan2(tg_[1], tg_[0]), 3), "h": bk.get("h", 1.0), "w": bk.get("w", 1.0), "d": bk.get("d", 1.5),
                        "style": bk.get("style", "plain"), **({"color": bk["color"]} if bk.get("color") else {}), "src": bk["src"]})
    for lm in SC_CFG.get("light_masts", []):
        xy = np.array(bl.enu(*lm["latlon"]), float)
        out.append({"kind": "mast", "text": "", "x": rnd(xy[0], 2), "y": rnd(xy[1], 2), "z": rnd(float(trk.ground(*xy)[0]), 2),
                    "heading": 0, "h": lm.get("h", 18.0), "w": 1.2, **({"style": lm["style"]} if lm.get("style") else {}), "src": lm["src"]})
    # a landmark tree (Laguna: the Corkscrew oak, the biggest crown on the inside (left) of T8)
    oak = SC_CFG.get("oak")
    near = np.zeros(len(T), bool)
    if oak:
        c8 = corners[oak["corner"]]
        i, lat, dout = trk.project(T[:, :2])
        near = (np.abs(i - c8["s"]) < 40) & ((lat > 0) if oak.get("side", "left") == "left" else (lat < 0)) & (dout > 2) & (dout < 45)
    if near.any():
        k = np.nonzero(near)[0][np.argmax(T[near, 3] * T[near, 4])]
        T[k, 3] = max(T[k, 3], 13.0)
        T[k, 4] = max(T[k, 4], 8.0)
        out.append({"kind": "oak", "text": oak.get("text", "oak"), "x": rnd(T[k, 0], 1), "y": rnd(T[k, 1], 1),
                    "z": rnd(T[k, 2], 2), "heading": 0, "h": rnd(T[k, 3], 1), "w": rnd(T[k, 4], 1)})
        log(f"{oak.get('text', 'oak')}: lidar crown at ({T[k, 0]:.0f}, {T[k, 1]:.0f}), {T[k, 3]:.1f} m tall, r {T[k, 4]:.1f} m")
    # advertising boards and the Rahal cable gantry seen in the onboard video (tools/track/compare/): placed against
    # the outside wall (OSM) or at a fixed distance; (turn or None, s offset or absolute s, side, text, width)
    corners_all = corners
    for turn, ds, side, text, width, dist in BANNER_BOARDS:
        s0 = corners_all[turn]["s"] + ds if turn else ds
        st = int(s0) % trk.n
        out.append(fence_board(trk, st, side, dist, text, width))
    out += wall_boards(trk) + impact_barriers(trk)
    gy = SC_CFG.get("gantry")
    if not gy:
        return out
    s_g = (corners_all[gy["corner"]]["s"] - gy["before_m"]) % trk.n
    a_ = trk.C[s_g, :2] + trk.N[s_g] * (trk.hw(s_g, 1) + 9)
    b_ = trk.C[s_g, :2] - trk.N[s_g] * (trk.hw(s_g, -1) + 9)
    out.append({"kind": "gantry", "text": "", "x": rnd(a_[0], 2), "y": rnd(a_[1], 2), "z": rnd(float(trk.ground(*a_)[0]), 2),
                "x2": rnd(b_[0], 2), "y2": rnd(b_[1], 2), "z2": rnd(float(trk.ground(*b_)[0]), 2), "heading": 0, "h": 17.0, "w": 2.2})
    return out


# config scenery: bridge_banners (text on the faces of each bridge, by OSM id; [face toward oncoming cars, face away],
# from the onboard video), bridge_style (OSM id -> 'arch' | 'deck'), hangars (OSM building id -> sign on the hangar)
BANNERS, BRIDGE_STYLE, HANGARS = {}, {}, {}


def far_terrain(trk):
    """5 x 5 km at 10 m from the USGS 1/3 arc-second DEM (NAVD88), with the near lidar DEM blended in."""
    import rasterio
    from rasterio.windows import from_bounds

    x0 = y0 = -FAR_HALF
    n = int(2 * FAR_HALF / FAR_DX) + 1
    gx = x0 + np.arange(n) * FAR_DX
    gy = y0 + np.arange(n) * FAR_DX
    lon0, lat0 = bl.lonlat(gx[0] - 100, gy[0] - 100)
    lon1, lat1 = bl.lonlat(gx[-1] + 100, gy[-1] + 100)
    cache = os.path.join(CACHE, "dem13_window.npz")
    if os.path.exists(cache):
        d = np.load(cache)
        A, tr = d["A"], tuple(d["tr"])
    else:
        with rasterio.open("/vsicurl/" + DEM13) as ds:
            win = from_bounds(lon0, lat0, lon1, lat1, ds.transform).round_offsets().round_lengths()
            A = ds.read(1, window=win).astype(np.float32)
            wt = ds.window_transform(win)
            tr = (wt.c, wt.a, wt.f, wt.e)
        np.savez_compressed(cache, A=A, tr=np.array(tr))
    GX, GY = np.meshgrid(gx, gy)
    lon, lat = bl.lonlat(GX, GY)
    col = (lon - tr[0]) / tr[1] - 0.5
    row = (lat - tr[2]) / tr[3] - 0.5
    Z = ndi.map_coordinates(A, [row, col], order=1, mode="nearest") - trk.t["z0_navd88"]
    # inside the near box use the near heightfield so the seam matches
    h = trk.h
    inb = (GX >= h["x0"]) & (GX <= h["x0"] + (h["nx"] - 1) * h["dx"]) & (GY >= h["y0"]) & (GY <= h["y0"] + (h["ny"] - 1) * h["dx"])
    Z[inb] = trk.ground(GX[inb], GY[inb])
    log(f"far terrain {n}x{n} at {FAR_DX} m: z {Z.min():.0f}..{Z.max():.0f} m")
    return Z.astype(np.float32), {"x0": x0, "y0": y0, "dx": FAR_DX, "nx": n, "ny": n}


def far_ortho():
    """NAIP over the far box at FAR_ORTHO_PX, north up, ENU-linear (one request, cached)."""
    from PIL import Image

    W = int(2 * FAR_HALF / FAR_ORTHO_PX)
    cache = os.path.join(CACHE, f"naip_far_{int(FAR_HALF)}_{W}.png")
    if os.path.exists(cache):
        return np.asarray(Image.open(cache).convert("RGB"))
    x0 = y0 = -FAR_HALF
    x1 = y1 = FAR_HALF
    lo0, la0 = bl.lonlat(x0, y0)
    lo1, la1 = bl.lonlat(x1, y1)
    hr = int(round(W * (la1 - la0) / (lo1 - lo0)))
    params = {"bbox": f"{lo0:.8f},{la0:.8f},{lo1:.8f},{la1:.8f}", "bboxSR": 4326, "imageSR": 4326,
              "size": f"{W},{hr}", "format": "jpg", "f": "json"}
    meta = requests.get(bl.NAIP, params=params, timeout=300, headers=UA).json()
    src = np.asarray(Image.open(io.BytesIO(get(meta["href"], timeout=300))).convert("RGB")).astype(np.float32)
    ex = meta["extent"]
    Hs, Ws = src.shape[:2]
    cx = x0 + (np.arange(W) + 0.5) * (x1 - x0) / W
    cy = y1 - (np.arange(W) + 0.5) * (y1 - y0) / W
    lon, _ = bl.lonlat(cx, 0 * cx)
    _, lat = bl.lonlat(0 * cy, cy)
    sc = (lon - ex["xmin"]) / (ex["xmax"] - ex["xmin"]) * Ws - 0.5
    sr = (ex["ymax"] - lat) / (ex["ymax"] - ex["ymin"]) * Hs - 0.5
    RR, CC = np.meshgrid(sr, sc, indexing="ij")
    out = np.stack([ndi.map_coordinates(src[..., k], [RR, CC], order=1, mode="nearest") for k in range(3)], -1)
    img = np.clip(out + 0.5, 0, 255).astype(np.uint8)
    Image.fromarray(img).save(cache)
    return img


def far_trees(trk, img, Zf, fmeta, n_max=7000):
    """Oaks outside the lidar box, from dark green blobs in the far NAIP image (5 m/px), deterministic thinning."""
    a = img.astype(np.float32)
    lum = a.mean(-1)
    bg = ndi.uniform_filter(lum, 25)
    green = a[..., 1] - a[..., 0]
    dark = (lum < bg - 18) & (lum < 95) & (green > -6)
    S = ndi.gaussian_filter(np.where(dark, bg - lum, 0), 1.0)
    pk = (S == ndi.maximum_filter(S, size=3)) & (S > 8) & dark
    r, c = np.nonzero(pk)
    W = img.shape[0]
    x = -FAR_HALF + (c + 0.5) * (2 * FAR_HALF / W)
    y = FAR_HALF - (r + 0.5) * (2 * FAR_HALF / W)
    b = trk.box
    out = ~((x > b[0] + 10) & (x < b[2] - 10) & (y > b[1] + 10) & (y < b[3] - 10))
    x, y, strength = x[out], y[out], S[r, c][out]
    lab, _ = ndi.label(dark)
    size = np.bincount(lab.ravel())[lab[r, c][out]] * (2 * FAR_HALF / W) ** 2
    rad = np.clip(np.sqrt(np.minimum(size, 120) / np.pi) * 1.1, 2.0, 7.0)
    hgt = np.clip(rad * 1.35 + 2.0, 4.5, 12.0)
    zc = ndi.map_coordinates(Zf, [(y - fmeta["y0"]) / FAR_DX, (x - fmeta["x0"]) / FAR_DX], order=1, mode="nearest")
    order = np.argsort(-strength)[:n_max]
    T = np.c_[x, y, zc, hgt, rad][order]
    log(f"far trees: {len(T)} from far NAIP dark-canopy blobs (of {out.sum()} candidates)")
    return T


def preview(trk, T, Tf, bld, bar, kerb, brg, marks, path):
    from PIL import Image, ImageDraw

    im = Image.open(os.path.join(OUT, "ortho.jpg")).convert("RGB")
    W, H = im.size
    b = trk.box

    def px(x, y):
        return ((x - b[0]) / (b[2] - b[0]) * W, (b[3] - y) / (b[3] - b[1]) * H)

    d = ImageDraw.Draw(im)
    for x, y, _, h, r in T:
        p = px(x, y)
        rr = r / (b[2] - b[0]) * W
        d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], outline=(40, 255, 60))
    for bb in bld:
        d.polygon([px(x, y) for x, y in bb["footprint"]], outline=(255, 0, 255) if bb["src"] == "osm" else (0, 255, 255))
    col = {"concrete": (255, 255, 255), "armco": (120, 160, 255), "tyres": (255, 40, 40), "pitwall": (255, 200, 0),
           "fence": (255, 140, 0)}
    for br in bar:
        d.line([px(p[0], p[1]) for p in br["pts"]], fill=col[br["kind"]], width=3)
    for k in kerb:
        st = (np.arange(k["s0"], k["s1"]) / trk.sp).astype(int) % trk.n
        P = trk.C[st, :2] + trk.N[st] * (k["side"] * trk.hw(st, k["side"]))[:, None]
        d.line([px(x, y) for x, y in P], fill=(255, 0, 0), width=4)
    for g in brg:
        d.line([px(*g["a"]), px(*g["b"])], fill=(255, 255, 0), width=6)
    for m in marks:
        p = px(m["x"], m["y"])
        d.rectangle([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=(0, 0, 0), outline=(255, 255, 0))
    im.save(path)


def main(cfg=None, out_dir=None):
    """Build the scenery of the package in out_dir (configure() first, or pass cfg and out_dir)."""
    from PIL import Image

    if cfg is not None:
        bl.configure(cfg)
        configure(cfg, out_dir)
    trk = Track()
    # 1. regrade the near ortho from the cached NAIP mosaic
    o = trk.t["ortho"]
    raw = os.path.join(CACHE, f"naip_{int(o['x0'])}_{int(o['y0'])}_{int(o['x1'])}_{int(o['y1'])}_{o['width_px']}x{o['height_px']}.png")
    ortho_arr = None
    if os.path.exists(raw):
        ortho_arr = bl.grade_ortho(np.asarray(Image.open(raw).convert("RGB")))
        Image.fromarray(ortho_arr).save(os.path.join(OUT, "ortho.jpg"), quality=84, optimize=True)
        log(f"ortho.jpg regraded: {os.path.getsize(os.path.join(OUT, 'ortho.jpg')) / 1e6:.2f} MB")
    else:
        log("WARNING: cached NAIP mosaic missing, ortho.jpg left as is (run the geometry stage)")
    G = lidar_grids(trk)
    osm = Osm()
    bld, taken = buildings(trk, G, osm)
    T = trees(trk, G, taken)
    brg = bridges(trk, G, osm)
    for b in brg:
        dflt = SC_CFG.get("bridge_default_banner", "")
        b["banners"] = BANNERS.get(b["id"], [[dflt], [dflt]] if dflt else [[], []])
        b["style"] = BRIDGE_STYLE.get(b["id"], "deck")
    bar, bar_tot = barriers(trk, osm)
    terr, terr_fences = terraces(trk)
    bar += terr_fences
    if SC_CFG.get("tyre_facings"):
        tyre_facings(trk, bar, **SC_CFG["tyre_facings"])
    if SC_CFG.get("tyre_rows_outside", {}) is not False:
        tyre_rows_outside(trk, bar, **(SC_CFG.get("tyre_rows_outside") or {}))
    for b_ in bar:
        if b_["kind"] in ("concrete", "armco", "pitwall"):
            P_ = np.array(b_["pts"])[:, :2]
            _WALL_CACHE.append(trk.project(P_))
    kerb = kerbs(trk)
    lines = edge_lines(trk, kerb, osm)
    # round 7 (Sonoma owner notes 42-43): stretches where the painted edge is not the white line but a declared paint
    # line (the pit-out blend line is double yellow): config scenery.edge_line_cut [{side, s: (s0, s1) m, why}]
    for cut in SC_CFG.get("edge_line_cut", []):
        sd = 1 if cut["side"] == "left" else -1
        a, b = (v / trk.sp for v in cut["s"])
        kept = []
        for r_ in lines:
            if r_["side"] != sd:
                kept.append(r_); continue
            lo, hi = r_["s0"], r_["s1"]
            for off in (0, trk.n, -trk.n):   # runs may wrap past the line
                A, B = a + off, b + off
                if hi <= A or lo >= B:
                    continue
                if lo < A: kept.append(dict(r_, s0=lo, s1=A))
                lo = max(lo, B)
            if lo < hi: kept.append(dict(r_, s0=lo, s1=hi))
        lines = kept
        log(f"edge lines cut on the {cut['side']} s {cut['s'][0]}-{cut['s'][1]} ({cut['why'][:60]})")
    pit = pit_lane(trk, osm)
    if pit and SC_CFG.get("pit_lane_clip_walls"):
        # the lane's real width: its paving stops at the walls that bound it (config scenery.pit_lane_clip_walls,
        # 20 Oct 2026; Sonoma's OSM-width lane reached through the pit-in Jersey and the outer wall)
        # round 7 (owner note 37): and at the declared cone lines along it (the pit-in separation line before the nose)
        clip_parts_at_walls(pit["parts"], bar + [{"kind": "tyres", "pts": c_["pts"]} for c_ in declared_cone_lines(trk)], label="pit lane",
                            heads=bool(SC_CFG.get("pit_lane_clip_heads")))
        if SC_CFG.get("pit_lane_clip_heads"):
            # postcondition (round 14D third review 3): the stored lane edges clear every barrier run by the margin
            d_, side_ = clearance_report(pit["parts"], bar + [{"kind": "tyres", "pts": c_["pts"]} for c_ in declared_cone_lines(trk)])
            if d_ < 0.3 - 1e-6:
                raise SystemExit(f"pit lane: edge clearance {d_:.3f} m < 0.3 m ({side_} edge) after the clip")
            log(f"pit lane: edge clearance to every barrier run {d_:.3f} m (>= 0.3, a postcondition)")
    if pit and (PIT_CFG.get("lane") or {}).get("to_walls"):
        extend_parts_to_walls(pit["parts"], bar, **PIT_CFG["lane"]["to_walls"])
    if pit and (PIT_CFG.get("lane") or {}).get("boxes") is not None:
        pit["boxes"] = [list(map(float, r)) for r in PIT_CFG["lane"]["boxes"]]   # pit-box line ranges (m along part 0); [] = none
    if pit and (PIT_CFG.get("lane") or {}).get("no_edge_line"):
        pit["no_edge_line"] = list(PIT_CFG["lane"]["no_edge_line"])   # the app draws no white edge line on these sides
    if pit and ortho_arr is not None and (PIT_CFG.get("lane") or {}).get("match_track_tone"):
        ortho_arr = pit_tone_match(trk, pit, ortho_arr, PIT_CFG["lane"]["match_track_tone"])
        Image.fromarray(ortho_arr).save(os.path.join(OUT, "ortho.jpg"), quality=84, optimize=True)
    if ortho_arr is not None and SC_CFG.get("ortho_paint_over"):
        ortho_arr = ortho_paint_over(trk, ortho_arr, SC_CFG["ortho_paint_over"])
        Image.fromarray(ortho_arr).save(os.path.join(OUT, "ortho.jpg"), quality=84, optimize=True)
    zones = paved_zones(trk, osm)
    cr_parts, cone_lines = closed_roads(trk, osm) if SC_CFG.get("closed_roads") else ([], [])
    if cr_parts and SC_CFG.get("closed_roads_clip_walls"):
        clip_parts_at_walls(cr_parts, bar)
    if cr_parts:
        zones["parts"] += cr_parts
    if cr_parts and pit and any(r_.get("join_lane") for r_ in SC_CFG.get("closed_roads", [])):
        join_lane(pit["parts"], cr_parts, zones.get("fractions") or trk.t["profile"]["fractions"])
    if SC_CFG.get("zones_meet_edge"):
        zones_meet_edge(trk, zones["parts"])
    if SC_CFG.get("zone_end_feather"):
        # judge r8 (cp6): a zone end more than 2 m from the road (on the dirt) is feathered by the app
        from shapely.geometry import Point, Polygon
        from shapely.ops import unary_union
        L_, R_, n_ = trk.L[:, :2], trk.R[:, :2], trk.n
        road_ = unary_union([Polygon([L_[i], L_[(i + 1) % n_], R_[(i + 1) % n_], R_[i]]).buffer(0) for i in range(n_)])
        nf = 0
        for p_ in zones["parts"]:
            fe = [bool(road_.distance(Point(p_["center"][e][:2])) > 2.0) for e in (0, -1)]
            if any(fe):
                p_["feather_ends"] = fe; nf += sum(fe)
        log(f"zone ends feathered: {nf} (scenery.zone_end_feather)")
    if SC_CFG.get("paved_zones_over"):
        # texture pass (Buttonwillow owner lap 1, 21 Oct 2026): every zone's road surface draws in front of the track's
        # and the other zones' shoulders, its own shoulder behind them (the app's `over`); drawn only, no physics change
        # (closed roads 2 in front of runoff zones 1: the T2 runoff reaches the outer-loop road's block line)
        for p_ in zones["parts"]:
            p_["over"] = 2 if p_.get("kind") == "closed_road" else 1
        log(f"paved zones: {len(zones['parts'])} parts drawn over the neighbouring shoulders (scenery.paved_zones_over)")
    om_lines, om_ranges = owner_mouth_cones(trk)
    cone_lines += om_lines + declared_cone_lines(trk)
    plines = closed_road_paint(trk, cr_parts) + declared_paint_lines(trk) + surface_marks(trk)
    pareas = paved_areas(trk, osm)
    cones = pit_exit_cones(trk, pit, bar)
    pc_ = SC_CFG.get("pit_exit_cones") or {}
    if pc_.get("draw") is False:
        # no cones where the footage shows none (Buttonwillow's pit-out merge, onboard 0:18-0:22): no cone line at all
        log(f"pit-exit cones: none (config scenery.pit_exit_cones.draw False: {pc_.get('src', '')})")
        cones = None
    # the measured blend line: scenery.pit_exit_cones.latlon, else stage 1's centre.pit_exit.line_latlon (one
    # measurement serves both; scenery.pit_exit_cones keeps the colour, size and spacing)
    ll_, src_ = (pc_.get("latlon"), pc_.get("src")) if pc_.get("latlon") else (PIT_EXIT.get("line_latlon"), PIT_EXIT.get("src", ""))
    if ll_ and pc_.get("draw") is not False:
        # round 7 (Sonoma owner notes 42-43): the cones stand ON the painted blend line measured on the captures, from
        # the pit-wall nose to the merge, in the colour, size and spacing of the footage
        P_ = _ll_line(ll_, 2.0)
        i_, _, _ = trk.project(P_[[0, -1]])
        cones = {"spacing_m": pc_.get("spacing", 16.0), "s0": int(i_[0]), "s1": int(i_[1]), "pts": with_z(trk, P_),
                 "src": src_, **_cone_style(pc_)}
        log(f"pit-exit cones on the measured blend line: stations {int(i_[0])}-{int(i_[1])}, every {cones['spacing_m']} m")
    marks = landmarks(trk, T, brg)
    for b_ in bld:
        if b_["kind"] == "hangar":
            F = np.array(b_["footprint"])
            c_ = F.mean(0)
            i_, lat_, _ = trk.project(c_[None])
            to = trk.C[i_[0], :2] - c_
            to /= np.linalg.norm(to)
            # sign on the gable facing the track, high on the wall
            half = 0.5 * float(np.max(np.abs((F - c_) @ to)))
            p_ = c_ + to * (half + 0.3)
            marks.append({"kind": "sign", "text": b_["name"], "x": rnd(p_[0], 2), "y": rnd(p_[1], 2),
                          "z": rnd(b_["z"] + b_["h"] * 0.55, 2), "heading": rnd(math.atan2(to[1], to[0]), 3), "h": 2.4, "w": 10.0})
    Zf, fmeta = far_terrain(trk)
    fimg = far_ortho()
    Tf = far_trees(trk, fimg, Zf, fmeta)
    Image.fromarray(bl.grade_ortho(fimg)).save(os.path.join(OUT, "far_ortho.jpg"), quality=78, optimize=True)
    Zf.tofile(os.path.join(OUT, "far_heightfield.bin"))

    def pack(A):
        return [int(round(v * 10)) for v in A.ravel()]

    # station ranges -> metres along the lap (CONTRACTS 2b: s = station * spacing_m)
    to_m = lambda v: round(float(v) * trk.sp, 1)  # noqa: E731
    for k_ in kerb:
        k_["s0"], k_["s1"] = to_m(k_["s0"]), to_m(k_["s1"])
    for r_ in lines:
        r_["s0"], r_["s1"] = to_m(r_["s0"]), to_m(r_["s1"])
    for b_ in brg:
        b_["s"] = to_m(b_["s"])
    if cones:
        cones["s0"], cones["s1"] = to_m(cones["s0"]), to_m(cones["s1"])
    # round 9 (Sonoma judge r9): the app draws rule pit-box lines across the longest pit-lane part every 10 lane stations;
    # pit_lane.lane.no_box_lines [{s: (s0, s1) track metres, why}] lists stretches where the footage shows no box lines
    # (the pit-out lane past the boxes), written as lane station ranges `no_boxes` on part 0 (absent: as before)
    nb_ = (PIT_CFG.get("lane") or {}).get("no_box_lines") or []
    if pit and pit.get("parts") and nb_:
        p0_ = pit["parts"][0]
        si_ = trk.project(np.array(p0_["center"])[:, :2])[0] * trk.sp
        rngs = []
        for f_ in nb_:
            a_, b_ = f_["s"]
            m_ = ((si_ - a_) % (trk.n * trk.sp)) <= ((b_ - a_) % (trk.n * trk.sp))
            idx_ = np.nonzero(m_)[0]
            if len(idx_):
                rngs.append([int(idx_.min()), int(idx_.max())])
        p0_["no_boxes"] = rngs
        log(f"pit lane: no rule box lines at lane stations {rngs} (track s {[f_['s'] for f_ in nb_]})")
    for grp in (pit, zones):
        for p_ in (grp or {}).get("parts", []):
            p_["track_s"] = [to_m(v) for v in p_["track_s"]]
    sc = {
        "version": 1,
        "units": "ENU metres (CONTRACTS section 1); z relative to z0_navd88 of track.json",
        "sources": "OpenStreetMap (ODbL); USGS 3DEP lidar point cloud CA_AZ_FEMA_R9_Lidar_2017_D18 via the Entwine "
                   "point tiles on AWS (public domain); USGS 1/3 arc-second DEM (public domain); USGS NAIP (public "
                   "domain); hand-placed items noted in each entry's src",
        "far": {"heightfield": {"file": "far_heightfield.bin", **fmeta},
                "ortho": {"file": "far_ortho.jpg", "x0": -FAR_HALF, "y0": -FAR_HALF, "x1": FAR_HALF, "y1": FAR_HALF},
                "ground_color": "#b59a6a"},
        "trees": {"stride": 5, "fields": ["x", "y", "z", "height", "crown_radius"], "scale": 0.1, "data": pack(T)},
        "far_trees": {"stride": 5, "fields": ["x", "y", "z", "height", "crown_radius"], "scale": 0.1, "data": pack(Tf)},
        "buildings": bld,
        "bridges": brg,
        "barriers": bar,
        "kerbs": {"width": SC_CFG.get("kerb", {}).get("width", KERB_W), "inside": True,
                  "stripe_m": SC_CFG.get("kerb", {}).get("stripe_m", 2.0), "strips": kerb,
                  # per-track paint (config scenery.kerb.colors = [stripe, base]); absent: the app's red / white (Laguna)
                  **({"colors": SC_CFG["kerb"]["colors"]} if SC_CFG.get("kerb", {}).get("colors") else {}),
                  # raised kerb profile (config scenery.kerb.profile, 20 Oct 2026; absent = flat paint, Laguna)
                  **({"profile": SC_CFG["kerb"]["profile"]} if SC_CFG.get("kerb", {}).get("profile") else {})},
        "edge_lines": {"width": 0.12, "inset": 0.15, "runs": lines},
        "pit_lane": pit,
        "paved_zones": zones,
        "pit_exit_cones": cones,
        **({"cone_lines": cone_lines} if cone_lines else {}),
        **({"paint_lines": plines} if plines else {}),
        **({"paved_areas": pareas} if pareas else {}),
        **({"ground_signs": ground_signs(trk)} if SC_CFG.get("ground_signs") else {}),
        **({"kerb_lines": kerb_lines(trk)} if SC_CFG.get("kerb_lines") else {}),
        "landmarks": marks,
        **({"terraces": terr} if terr else {}),
        # round 10 (Sonoma judge r9, the pit-out lane surface): stretches where the track ribbon draws no shoulder because a
        # paved lane runs right against the edge there; the shoulder rows rose through the lane and showed as pale patches
        # (config scenery.track_shoulder_cut [{side, s: (s0, s1) m, why}]; absent: every station keeps its shoulder)
        **({"track_shoulder_cut": [{"side": 1 if c_["side"] == "left" else -1, "s0": float(c_["s"][0]), "s1": float(c_["s"][1]),
                                    "why": c_["why"]} for c_ in SC_CFG["track_shoulder_cut"]]} if SC_CFG.get("track_shoulder_cut") else {}),
    }
    if STRUCT_CFG:
        # the buildings round (21 Oct 2026): grandstands, garages, blocks, fuel island, masts, pit-box paint, boards
        import build_structures
        build_structures.apply(trk, osm, sc, STRUCT_CFG)
        bld = sc["buildings"]
    if SC_CFG.get("ortho_inpaint"):
        # round 13 (Sonoma owner note 130): the ortho under every modelled structure's footprint is filled from the ground
        # around it, so the satellite's image of the bridge deck, a roof or a stand does not show through as a ground band
        op_ = os.path.join(OUT, "ortho.jpg")
        img_ = np.asarray(Image.open(op_).convert("RGB"))
        fp_ = structure_footprints(sc, SC_CFG["ortho_inpaint"], img_, trk.t["ortho"])
        for k_, _ in fp_:
            if "shadow (" in k_:
                log(f"ortho inpaint: {k_}")
        for l_ in STRUCT_LOG:
            log(f"ortho inpaint: {l_}")
        STRUCT_LOG.clear()
        fp_ = [(k_, P_) for k_, P_ in fp_ if len(P_) >= 3]
        arr_, npx_ = inpaint_ortho(img_, fp_, trk.t["ortho"])
        Image.fromarray(arr_).save(op_, quality=84, optimize=True)
        px_m2 = ((trk.t["ortho"]["x1"] - trk.t["ortho"]["x0"]) / arr_.shape[1]) ** 2
        log(f"ortho inpainted under {len(fp_)} structure footprints ({sum(1 for k, _ in fp_ if k.startswith('bridge'))} bridge "
            f"parts, {sum(1 for k, _ in fp_ if k.startswith('barrier'))} barrier segments, margin {SC_CFG['ortho_inpaint'].get('margin', 1.5)} m, bridge decks "
            f"{SC_CFG['ortho_inpaint'].get('bridge_margin', 3.0)} m): {npx_} px, {npx_ * px_m2:.0f} m2")
    with open(os.path.join(OUT, "scenery.json"), "w") as fh:
        json.dump(sc, fh, separators=(",", ":"))
    preview(trk, T, Tf, bld, bar, kerb, brg, marks, os.path.join(PREVIEWS, "scenery_preview.png"))
    tot = 0
    for f in ("scenery.json", "far_heightfield.bin", "far_ortho.jpg", "ortho.jpg"):
        sz = os.path.getsize(os.path.join(OUT, f))
        tot += sz if f != "ortho.jpg" else 0
        log(f"wrote {f}: {sz / 1e6:.2f} MB")
    log(f"new payload (excluding the regraded ortho.jpg): {tot / 1e6:.2f} MB")
    log(f"summary: {len(T)} trees (lidar) + {len(Tf)} far trees (NAIP), {len(bld)} buildings, {len(brg)} bridges, "
        f"{len(bar)} barrier runs ({sum(bar_tot.values()):.0f} m), {len(kerb)} kerbs, {len(marks)} landmarks")
    st_cfg = SC_CFG.get("season_tint")
    if st_cfg and st_cfg.get("enabled", True):
        # the LAST step of the stage, on the published ground images only: the cached NAIP (stage 1's paint detector,
        # the canopy tests, far trees) and every step above read the untinted images
        for f, q in (("ortho.jpg", 84), ("far_ortho.jpg", 78)):
            fp = os.path.join(OUT, f)
            src_img = np.asarray(Image.open(fp).convert("RGB"))
            zone = season_zone_mask(Track(), st_cfg, src_img.shape) if (f == "ortho.jpg" and st_cfg.get("zones")) else None
            arr, share = season_tint(src_img, st_cfg, zone)
            Image.fromarray(arr).save(fp, quality=q, optimize=True)
            log(f"season tint on {f}: {share * 100:.1f} % of the pixels (mask mean), green {tuple(st_cfg.get('green', (0.38, 0.47, 0.24)))}")
    if os.path.getsize(os.path.join(OUT, "ortho.jpg")) > 1.5e6:
        log("WARNING: ortho.jpg over 1.5 MB")


STRUCT_LOG = []


def deck_shadow(img, o, b, half, reach=15.0, need=30.0):
    """((dx, dy) m, contrast) of a bridge deck's shadow in the ortho: the deck strip (a -> b, half-width `half`) shifted
    by every offset within `reach` m on a 0.5 m grid, scored by its mean luminance against the ground 3 m either side
    of the shifted strip; the darkest offset at least 4 m off the deck (outside its own footprint) wins when it is
    `need` grey levels darker. None when the image shows no such shadow."""
    from scipy import ndimage as ndi_
    H, W = img.shape[:2]
    lum = ndi_.gaussian_filter(img.astype(np.float32).mean(-1), 1.0)
    a, c = np.asarray(b["a"], float), np.asarray(b["b"], float)
    t = c - a; L = np.linalg.norm(t)
    if L < 5:
        return None
    t /= L; nrm = np.array([-t[1], t[0]])
    u = np.linspace(0.1, 0.9, 40) * L
    v = np.linspace(-half, half, 5)
    U, V = np.meshgrid(u, v)
    base = a + U.ravel()[:, None] * t + V.ravel()[:, None] * nrm
    side = np.r_[a + U.ravel()[:, None] * t + (V.ravel()[:, None] * 0 + half + 3.0) * nrm,
                 a + U.ravel()[:, None] * t - (V.ravel()[:, None] * 0 + half + 3.0) * nrm]

    def mean_at(P):
        px = (P[:, 0] - o["x0"]) / (o["x1"] - o["x0"]) * W - 0.5
        py = (o["y1"] - P[:, 1]) / (o["y1"] - o["y0"]) * H - 0.5
        return float(ndi_.map_coordinates(lum, [py, px], order=1, mode="nearest").mean())
    best = None
    for dx in np.arange(-reach, reach + 1e-9, 0.5):
        for dy in np.arange(-reach, reach + 1e-9, 0.5):
            if math.hypot(dx, dy) > reach or abs(dx * nrm[0] + dy * nrm[1]) < 4.0:
                continue
            d = np.array([dx, dy])
            ctr = mean_at(side + d) - mean_at(base + d)
            if best is None or ctr > best[1]:
                best = ((round(float(dx), 1), round(float(dy), 1)), ctr)
    return best if best and best[1] >= need else None


def structure_footprints(sc, opt, img=None, o=None):
    """World polygons (ENU) of every modelled structure that stands over the ground, each grown by its margin, for
    inpaint_ortho: bridge decks (the a -> b span, `width` wide, grown by opt.bridge_margin: a raised deck's image in a
    non-true ortho also leans away from the nadir by about height x tan(view angle)) and their stair ends, buildings,
    and the structure kit's collision footprints (grandstands, garages, blocks, the fuel island); with the ortho (img, o)
    also each deck's shadow, found in the image (deck_shadow; opt.bridge_shadow, default on). Returns [(label, poly)]."""
    m, mb = float(opt.get("margin", 1.5)), float(opt.get("bridge_margin", 3.0))
    out = []

    def strip(a, b, half):
        a, b = np.asarray(a, float), np.asarray(b, float)
        t = b - a; L = np.linalg.norm(t)
        if L < 1e-6:
            return None
        t /= L; nrm = np.array([-t[1], t[0]])
        a, b = a - t * half, b + t * half
        return [a + nrm * half, b + nrm * half, b - nrm * half, a - nrm * half]

    def grow(P, d):
        P = np.asarray(P, float)[:, :2]
        c = P.mean(0)
        r = np.linalg.norm(P - c, axis=1, keepdims=True)
        return c + (P - c) * (r + d) / np.maximum(r, 1e-6)

    for b in sc.get("bridges", []):
        p = strip(b["a"], b["b"], b.get("width", 3.0) / 2 + mb)
        if p is not None:
            out.append((f"bridge {b['id']} deck", p))
        if opt.get("bridge_shadow", True) and img is not None:
            # the deck's shadow in the image lies off its footprint (a raised deck): the footprint strip shifted by the
            # offset (within 15 m) that is darkest against the ground beside it, when it is a shadow (30 grey levels)
            sh = deck_shadow(img, o, b, b.get("width", 3.0) / 2 + 1.0)
            if sh is not None:
                (dx, dy), ctr = sh
                p = strip(np.asarray(b["a"]) + (dx, dy), np.asarray(b["b"]) + (dx, dy), b.get("width", 3.0) / 2 + m)
                out.append((f"bridge {b['id']} shadow (offset {dx:+.1f}, {dy:+.1f} m, {ctr:.0f} grey levels darker)", p))
        for e in b.get("ends", []):
            p = strip(e["at"], e["to"], 1.0 + m)
            if p is not None:
                out.append((f"bridge {b['id']} stairs", p))
    bo = opt.get("barriers")
    if bo:
        # round 13A fix (judge r13a N127 / N130 / N131): the satellite's image of a barrier itself (a pale gravel-looking
        # ribbon under a tyre wall, a wall's lit top and its shadow) stayed in the ground under the modelled run. Each run of
        # the listed kinds masks a band `half` m either side of its line, swept along the sun's shadow vector over its
        # height (the vector per metre of height from the bridge deck's measured shadow, else bo.shadow_per_m)
        sv = np.asarray(bo.get("shadow_per_m", (0.0, 0.0)), float)
        if img is not None:
            for b in sc.get("bridges", []):
                sh = deck_shadow(img, o, b, b.get("width", 3.0) / 2 + 1.0)
                hz = [e_["z_ground"] for e_ in b.get("ends", []) if "z_ground" in e_]
                if sh is not None and hz and b.get("deck_z") is not None and b["deck_z"] - np.mean(hz) > 2.0:
                    sv = np.asarray(sh[0], float) / (b["deck_z"] - float(np.mean(hz)))
                    break
        half = float(bo.get("half", 1.5))
        from scipy.spatial import ConvexHull
        nb = 0
        for b in sc.get("barriers", []):
            if b["kind"] not in bo.get("kinds", ("tyres", "concrete", "pitwall", "armco")):
                continue
            P = np.asarray(b["pts"], float)[:, :2]
            S = sv * float(b.get("h", 1.0))
            for p0, p1 in zip(P[:-1], P[1:]):
                t = p1 - p0; L = np.linalg.norm(t)
                if L < 1e-6:
                    continue
                t /= L; nrm = np.array([-t[1], t[0]])
                q = np.array([p0 - t * half + nrm * half, p0 - t * half - nrm * half, p1 + t * half + nrm * half, p1 + t * half - nrm * half])
                q = np.r_[q, q + S]
                out.append((f"barrier {b['kind']} band", [tuple(v) for v in q[ConvexHull(q).vertices]]))
            nb += 1
        out.append(("barrier summary", []))
        STRUCT_LOG.append(f"{nb} barrier runs banded (half {half} m, shadow {sv[0]:+.2f}, {sv[1]:+.2f} m per m of height)")
    for b in sc.get("buildings", []):
        out.append((f"building {b.get('name') or b.get('kind')}", list(grow(b["footprint"], m))))
    for s in sc.get("structures", []):
        for c in s.get("collide") or []:
            out.append((f"{s['type']} {s.get('name', '')}", list(grow(c["footprint"], m))))
    return out


def inpaint_ortho(img, polys, o, seed=13):
    """Fill the ortho under the footprint polygons from the surrounding ground (config scenery.ortho_inpaint, round 13,
    Sonoma owner note 130: the satellite's image of the footbridge deck was baked into the ground under the modelled
    bridge). Low frequencies by a mask-weighted pyramid fill (normalized convolution: each level averages the known
    pixels, holes take the next coarser level), plus a high-frequency grain drawn from the ring of known ground around
    each hole (its residual's per-channel standard deviation), so the patch reads as ground rather than a smooth blot.
    No hand painting: the mask is the footprints, the fill is the ground around them. Returns (image, pixels filled)."""
    from PIL import Image, ImageDraw
    from scipy import ndimage as ndi_
    H, W = img.shape[:2]
    mk = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(mk)
    tox = lambda P: [((p[0] - o["x0"]) / (o["x1"] - o["x0"]) * W, (o["y1"] - p[1]) / (o["y1"] - o["y0"]) * H) for p in P]  # noqa: E731
    for _, P in polys:
        dr.polygon(tox(P), fill=255)
    hole = np.asarray(mk) > 0
    if not hole.any():
        return img, 0
    f = img.astype(np.float32)
    known = (~hole).astype(np.float32)
    # pyramid of mask-weighted averages
    levels = [(f * known[..., None], known)]
    while levels[-1][1].shape[0] > 8 and (levels[-1][1] == 0).any():
        a, w = levels[-1]
        h2, w2 = a.shape[0] // 2 * 2, a.shape[1] // 2 * 2
        a = a[:h2, :w2].reshape(h2 // 2, 2, w2 // 2, 2, 3).sum((1, 3))
        w = w[:h2, :w2].reshape(h2 // 2, 2, w2 // 2, 2).sum((1, 3))
        levels.append((a, w))
    fill = levels[-1][0] / np.maximum(levels[-1][1], 1e-6)[..., None]
    for a, w in reversed(levels[:-1]):
        up = np.repeat(np.repeat(fill, 2, 0), 2, 1)
        up = np.pad(up, ((0, a.shape[0] - up.shape[0]), (0, a.shape[1] - up.shape[1]), (0, 0)), mode="edge")
        up = ndi_.gaussian_filter(up, (1.0, 1.0, 0))
        own = a / np.maximum(w, 1e-6)[..., None]
        fill = np.where((w > 0)[..., None], own, up)
    # grain: the ring of known ground (3-8 px beyond each hole) gives the residual's standard deviation
    ring = ndi_.binary_dilation(hole, iterations=8) & ~ndi_.binary_dilation(hole, iterations=3)
    # robust (median absolute deviation) and capped: a ring round a roof or a stand holds its hard edges too
    resid = (f - ndi_.gaussian_filter(f, (2.0, 2.0, 0))).mean(-1)
    sd = min(6.0, 1.4826 * float(np.median(np.abs(resid[ring])))) if ring.any() else 0.0
    rng = np.random.default_rng(seed)
    grain = ndi_.gaussian_filter(rng.normal(0.0, 1.0, (H, W)), 0.7).astype(np.float32)
    grain = (grain / (grain.std() or 1.0) * sd)[..., None]
    out = f.copy()
    out[hole] = (fill + grain)[hole]
    return out.clip(0, 255).astype(np.uint8), int(hole.sum())


def ortho_pave(T, SC, opt, img, tiles, mpp, enu, log=print, seed=17):
    """The ground under a complex's paving, retextured (config scenery.ortho_pave, round 13 part B, Sonoma owner note 135:
    "This T7 complex with un-used track looks very bad ... Not a mismatch of textures and geometries"). The NAIP ortho is
    of another year: its paint (arrows, junction lines), pale patches, parked trailers' shadows and a red island showed
    through the closed paved surfaces, and paving left as ground read lighter than the same paving drawn as a zone.
    opt: {regions: [{name, latlon: [(lat, lon), ...] (the region's outline; or zone: a paved zone's turn name), mask: 'captures' | 'all', src, fill?: '#rrggbb' |
    'paving' (the default),
    close: m, min_area: m2, exclude_track: m, feather: m, clip_zones: bool}], terrain_gain: (r, g, b), track_shoulder: m}. Per region:
    - mask 'captures': the paving read on the 2026 clean captures at 0.2 m (dark unsaturated asphalt, its white paint and
      red / white kerb blocks), the NAIP pavement rule (blue >= green - 6, bright > 45, saturation < 70) where no capture
      covers; at the ortho's pixels by majority, closed by `close` m (parked vehicles, paint) and components under
      `min_area` m2 dropped (asphalt brightness 20 to `asphalt_max`: deeper shadow is under trees); mask 'all': the whole
      outline (an island's painted surface); clip_zones: the closed-road zones inside the outline are brought in to where
      that paving ends (an island, a verge);
    - the raced track's own paved width (+ `exclude_track` m) is never changed;
    - fill: under the paved zones and pit-lane parts (drawn with the road shader) the median ortho colour of the track's
      own paving nearby; under paving left as ground that colour times `terrain_gain` (the road shader's grade, so the
      two read as one surface); a fixed colour with `fill`. A fine grain (the track paving's own residual, capped 4) is
      added; no paint is kept: the 2026 lines are drawn as geometry. Returns (image, pixels changed)."""
    import importlib.util
    from PIL import Image, ImageDraw
    from scipy import ndimage as ndi_
    from scipy.ndimage import gaussian_filter1d, median_filter
    spec = importlib.util.spec_from_file_location("capwin_", os.path.join(os.path.dirname(os.path.abspath(__file__)), "compare", "capwin.py"))
    capwin = importlib.util.module_from_spec(spec); spec.loader.exec_module(capwin)
    o = T["ortho"]; H, W = img.shape[:2]
    pxm = (o["x1"] - o["x0"]) / W
    tox = lambda P: [((p[0] - o["x0"]) / (o["x1"] - o["x0"]) * W, (o["y1"] - p[1]) / (o["y1"] - o["y0"]) * H) for p in P]  # noqa: E731

    def raster(polys):
        mk = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(mk)
        for P in polys:
            if len(P) >= 3:
                dr.polygon(tox(P), fill=255)
        return np.asarray(mk) > 0
    Lp, Rp = np.array(T["left"])[:, :2], np.array(T["right"])[:, :2]
    n = len(Lp)
    track = raster([[Lp[i], Lp[(i + 1) % n], Rp[(i + 1) % n], Rp[i]] for i in range(n)])
    f = img.astype(np.float32)
    out = f.copy()
    rng = np.random.default_rng(seed)
    gain = np.array(opt.get("terrain_gain", (1.0, 1.0, 1.0)), np.float32)
    changed = np.zeros((H, W), bool)
    masks = []
    for r in opt["regions"]:
        if not r.get("src"):
            raise SystemExit(f"ortho_pave region {r.get('name')}: no src")
        if r.get("zone"):
            # round 13A fix (Sonoma T1 runoff): the outline is a paved zone's own (an apron), so its ground image is repainted
            # as one surface (the NAIP year's slivers, seams and old paint gone) exactly where the zone is drawn
            zp = [p_ for p_ in (SC.get("paved_zones") or {}).get("parts", []) if p_.get("turn") == r["zone"]]
            if not zp:
                raise SystemExit(f"ortho_pave region {r.get('name')}: no paved zone {r['zone']!r}")
            poly = [q[:2] for q in zp[0]["left"]] + [q[:2] for q in zp[0]["right"]][::-1]
        else:
            poly = [enu(*q) for q in r["latlon"]]
        reg = raster([poly])
        ys, xs = np.nonzero(reg)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        if r.get("mask", "captures") == "all":
            pave = reg.copy()
        else:
            k = max(1, int(round(pxm / 0.2)))
            st = pxm / k
            wx0 = o["x0"] + x0 * pxm; wy1 = o["y1"] - y0 * pxm
            Wf, Hf = (x1 - x0) * k, (y1 - y0) * k
            cap, _ = capwin.mosaic(tiles, mpp, wx0, wy1, Wf, Hf, st)
            c = cap.astype(np.float32)
            br = c.mean(-1); sat = c.max(-1) - c.min(-1)
            cov = c.sum(-1) > 0
            # asphalt: dark to mid grey, unsaturated, neither green (trees, grass) nor warm (dirt, its shadows); white paint;
            # red kerb blocks
            asph = (br >= 20) & (br < r.get("asphalt_max", 140)) & (sat < 30) & (c[..., 1] - c[..., 0] < 6) & (c[..., 0] - c[..., 2] < 14)
            fine = asph | ((br > 165) & (sat < 40)) | ((c[..., 0] - c[..., 1] > 40) & (c[..., 0] > 90))
            frac = (fine & cov).reshape(y1 - y0, k, x1 - x0, k).mean((1, 3))
            covf = cov.reshape(y1 - y0, k, x1 - x0, k).mean((1, 3))
            sub = f[y0:y1, x0:x1]
            nb = sub.mean(-1); ns = sub.max(-1) - sub.min(-1)
            naip = (sub[..., 2] - sub[..., 1] >= -6) & (nb > 45) & (ns < 70)
            pv = np.where(covf >= 0.5, frac >= 0.5, naip)
            if r.get("mask") == "not_ground":
                # round 13B second pass (judge r13b): the whole region but its 2026 ground is paving (whatever stands on it:
                # trailers, a tent, their shadows), so one synthesised surface replaces the NAIP year's patches; ground =
                # warm (dirt) or green (grass, trees) or tree-dark (under 20)
                gnd_ = (((c[..., 0] - c[..., 2] >= 30) | (c[..., 1] - c[..., 0] >= 6)) & (br >= 20)) | (br < 20)
                gf_ = (gnd_ & cov).reshape(y1 - y0, k, x1 - x0, k).mean((1, 3)) / np.maximum(covf, 1e-6)
                pv = np.where(covf >= 0.5, gf_ < 0.4, naip)
            rad = max(1, int(round(r.get("close", 2.5) / pxm)))
            yy, xx = np.mgrid[-rad:rad + 1, -rad:rad + 1]
            disk = xx ** 2 + yy ** 2 <= rad ** 2
            pv = ndi_.binary_closing(np.pad(pv, rad, mode="edge"), disk)[rad:-rad, rad:-rad]
            lab, nl = ndi_.label(pv)
            if nl:
                area = ndi_.sum(np.ones_like(lab), lab, np.arange(1, nl + 1)) * pxm * pxm
                keep = np.r_[False, area >= r.get("min_area", 150.0)]
                pv = keep[lab]
            # 2026 ground (dirt, grass: warm or green) is never filled as paving: the islands stay islands
            gnd = (((c[..., 0] - c[..., 2] >= 30) | (c[..., 1] - c[..., 0] >= 6)) & (br >= 20) & cov)
            notg = gnd.reshape(y1 - y0, k, x1 - x0, k).mean((1, 3)) < 0.4
            if r.get("fill_holes") or r.get("close_big"):
                # round 13B second pass (judge r13b): what the 2026 mask skips inside the paving (parked trailers, a tent,
                # their shadows; the NAIP year's patches under them) is paving too: holes up to `fill_holes` m2, and what a
                # `close_big` m closing adds where the NAIP ground is paving-like (grey / pale, unsaturated; not grass)
                if r.get("close_big"):
                    rb = max(1, int(round(r["close_big"] / pxm)))
                    yy, xx = np.mgrid[-rb:rb + 1, -rb:rb + 1]
                    big = ndi_.binary_closing(np.pad(pv, rb, mode="edge"), xx ** 2 + yy ** 2 <= rb ** 2)[rb:-rb, rb:-rb]
                    pv = pv | (big & (ns < 45) & (nb > 60) & (sub[..., 1] - sub[..., 0] < 12) & notg)
                if r.get("fill_holes"):
                    hl_ = ndi_.binary_fill_holes(pv) & ~pv
                    lab_, nl_ = ndi_.label(hl_)
                    if nl_:
                        ar_ = ndi_.sum(np.ones_like(lab_), lab_, np.arange(1, nl_ + 1)) * pxm * pxm
                        pv = pv | (np.r_[False, ar_ <= r["fill_holes"]][lab_] & notg)
            pave = np.zeros((H, W), bool); pave[y0:y1, x0:x1] = pv
            pave &= reg
        masks.append((r, reg, pave))
    # islands given a colour of their own (fill '#rrggbb') are never paving for the zones
    fixed = np.zeros((H, W), bool)
    for r, reg, pave in masks:
        if r.get("fill") and r["fill"] != "paving":
            fixed |= pave
    for r, reg, pave in [m_ for m_ in masks if m_[0].get("clip_zones")]:
        # the closed-road zones inside the region stop where the 2026 paving stops (an island, a verge): each edge point
        # is brought in to the first 1.2 m of non-paving met walking out from the part's centre (at least 1 m from it)
        pm = (pave & ~fixed) | track
        ins = lambda P: pm[np.clip(((o["y1"] - P[:, 1]) / pxm).astype(int), 0, H - 1),  # noqa: E731
                           np.clip(((P[:, 0] - o["x0"]) / pxm).astype(int), 0, W - 1)]
        for part in (SC.get("paved_zones") or {}).get("parts", []):
            Cq = np.array(part["center"], float)
            if not reg[np.clip(((o["y1"] - Cq[:, 1]) / pxm).astype(int), 0, H - 1),
                       np.clip(((Cq[:, 0] - o["x0"]) / pxm).astype(int), 0, W - 1)].mean() > 0.5:
                continue
            moved = 0
            for side in ("left", "right"):
                E = np.array(part[side], float)
                d0 = np.hypot(*(E[:, :2] - Cq[:, :2]).T)
                dn = d0.copy()
                for i in range(len(Cq)):
                    d = float(d0[i])
                    if d < 1.0:
                        continue
                    u = (E[i, :2] - Cq[i, :2]) / d
                    t = np.arange(0.0, d + 1e-6, 0.3)
                    ok = ins(Cq[i, :2] + t[:, None] * u)
                    bad = np.convolve(~ok, np.ones(4), "same") >= 4
                    bad[t < 1.0] = False
                    if bad.any():
                        dn[i] = min(d, max(1.0, float(t[int(np.argmax(bad))]) - 0.45))
                if (dn < d0 - 0.05).any():
                    # a smooth edge along the part (the 0.6 m mask steps), never more than 0.3 m beyond the walked limit
                    sm = gaussian_filter1d(median_filter(dn, 5, mode="nearest"), 1.5, mode="nearest")
                    dn = np.minimum(np.minimum(sm, dn + 0.3), d0)
                    for i in np.nonzero(dn < d0 - 0.05)[0]:
                        E[i] = Cq[i] + (E[i] - Cq[i]) * (dn[i] / d0[i]); moved += 1
                part[side] = [[rnd(x, 2), rnd(y, 2), rnd(z, 3)] for x, y, z in E]
            if moved:
                log(f"ortho pave {r['name']}: zone {part.get('turn')}: {moved} edge points brought in to the 2026 paving's end")
    zq = []
    for grp in ("paved_zones", "pit_lane"):
        for part in (SC.get(grp) or {}).get("parts", []):
            Lq, Rq = np.array(part["left"])[:, :2], np.array(part["right"])[:, :2]
            zq += [[Lq[i], Lq[i + 1], Rq[i + 1], Rq[i]] for i in range(len(Lq) - 1)]
    zone = raster(zq)
    union = np.zeros((H, W), bool)
    for _, reg_, _ in masks:
        union |= reg_
    for r, reg, pave in masks:
        ex = max(0, int(round(r.get("exclude_track", 0.3) / pxm)))
        tr = ndi_.binary_dilation(track, iterations=ex) if ex else track
        pave &= ~tr
        # the track's own paving near the complex (all regions): its tone and its grain
        near = ndi_.binary_dilation(union, iterations=int(60 / pxm)) & track
        tv = f[near]
        base = np.median(tv, 0)
        resid = (f - ndi_.gaussian_filter(f, (2.0, 2.0, 0))).mean(-1)
        sd = min(4.0, 1.4826 * float(np.median(np.abs(resid[near])))) if r.get("grain") is None else float(r["grain"])
        grain = ndi_.gaussian_filter(rng.normal(0.0, 1.0, (H, W)), 0.7).astype(np.float32)
        grain = grain / (grain.std() or 1.0) * sd
        if r.get("fill") and r["fill"] != "paving":
            h_ = r["fill"].lstrip("#"); col = np.array([int(h_[i:i + 2], 16) for i in (0, 2, 4)], np.float32)
            colz = colt = col
        else:
            colz, colt = base, base * (np.array(r["ground_gain"], np.float32) if r.get("ground_gain") else gain)
        # the track ribbon's own shoulder rows (drawn over the ground up to `track_shoulder` m beyond its edges) show the ortho
        # as ground does, so the paving under them takes the ground tone even where a zone lies beneath
        shb = (ndi_.binary_dilation(track, iterations=int(round(opt.get("track_shoulder", 0.0) / pxm))) & ~track
               if opt.get("track_shoulder") else np.zeros_like(zone))
        if r.get("shoulder_keep"):
            # round 13B second pass: the first `shoulder_keep` m beyond the edge, where a closed road's ribbon meets the track at a
            # mouth (the track shoulder's first rows sample the road itself), keeps the zone tone: no dark seam along the mouth
            shb &= ~ndi_.binary_dilation(track, iterations=max(1, int(round(r["shoulder_keep"] / pxm))))
        zt = zone & ~shb
        tgt = np.where(zt[..., None], colz, colt)[pave] + grain[pave][:, None]
        if r.get("feather"):
            # fade the change in over `feather` m inside the outline where it cuts across paving (the paddock lot's far end)
            w = np.clip(ndi_.distance_transform_edt(reg) * pxm / r["feather"], 0, 1)[pave][:, None]
            tgt = f[pave] + w * (tgt - f[pave])
        out[pave] = tgt
        changed |= pave
        log(f"ortho pave {r['name']}: {int(pave.sum())} px ({pave.sum() * pxm * pxm:.0f} m2; {int((pave & zone).sum())} under "
            f"paved zones), track tone {base.round(0).tolist()}, ground tone {colt.round(0).tolist()}, grain {sd:.1f}")
    # soften the outline by one pixel so the 0.6 m pixels do not stair-step
    if changed.any():
        soft = ndi_.gaussian_filter(changed.astype(np.float32), 0.6)
        edge = (soft > 0.02) & (soft < 0.98)
        blur = ndi_.gaussian_filter(out, (0.6, 0.6, 0))
        out[edge] = blur[edge]
    return out.clip(0, 255).astype(np.uint8), int(changed.sum())


def season_zone_mask(trk, opt, shape):
    """Ground colour zones of the season tint (config scenery.season_tint.zones [{side, s: (s0, s1) m, off: (a, b) m beyond
    the edge, src}], round 11, Sonoma owner note 65): where the onboard shows green grass the summer NAIP's dry ground
    reads tan; inside a zone the tint applies at full strength to the ground pixels. Returns a float mask over ortho.jpg."""
    from PIL import Image, ImageDraw
    o = trk.t["ortho"]; H, W = shape[:2]
    C = np.array(trk.t["center"])[:, :2]; sp = trk.t["spacing_m"]; n = len(C)
    img = Image.new("L", (W, H), 0); dr = ImageDraw.Draw(img)
    tox = lambda P: [((p[0] - o["x0"]) / (o["x1"] - o["x0"]) * W, (o["y1"] - p[1]) / (o["y1"] - o["y0"]) * H) for p in P]  # noqa: E731
    for z in opt.get("zones", []):
        if not z.get("src"):
            raise SystemExit("season_tint.zones: every zone needs its src")
        E = np.array(trk.t[z["side"]])[:, :2]
        ks = [k % n for k in range(int(round(z["s"][0] / sp)), int(round(z["s"][1] / sp)) + 1)]
        nrm = np.array([(E[k] - C[k]) / max(np.linalg.norm(E[k] - C[k]), 1e-6) for k in ks])
        a, b = z["off"]
        poly = [E[k] + nrm[i] * a for i, k in enumerate(ks)] + [E[k] + nrm[i] * b for i, k in reversed(list(enumerate(ks)))]
        dr.polygon(tox(poly), fill=255)
        log(f"season tint zone {z['side']} s {z['s'][0]}-{z['s'][1]} m, {a}-{b} m beyond the edge: {z['src'][:90]}")
    return np.asarray(img, np.float32) / 255.0


def season_tint(img, opt, zone=None):
    """Procedural season tint of a ground image (config scenery.season_tint, Sonoma round 6, owner-approved quick version
    of the mock-up compare/sonoma/season_tint_mockup.py): the dry-grass class of the summer NAIP shifted to March green.
    Per pixel, mask = warm ramp (R - B over warm0..warm1) x brightness ramp (max channel over v0..v1) x low-saturation
    ramp (saturation under sat_max, soft over sat_soft) x not-already-green (G - R under 0.02, soft over 0.08); masked
    pixels take the green (r, g, b) scaled to keep the pixel's luminance, times `dark`, blended by the mask. Known limits:
    ploughed fields go green too, and the green is uniform (an NIR mask + slope version is a later option). Returns the
    tinted uint8 image and the mask's mean."""
    im = img.astype(np.float32) / 255.0
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    v = im.max(-1); mn = im.min(-1)
    sat = np.where(v > 0, (v - mn) / np.maximum(v, 1e-6), 0)
    w0, w1 = opt.get("warm", (0.06, 0.20)); v0, v1 = opt.get("bright", (0.25, 0.45))
    smax, ssoft = opt.get("sat_max", 0.55), opt.get("sat_soft", 0.25)
    m = np.clip((r - b - w0) / (w1 - w0), 0, 1) * np.clip((v - v0) / (v1 - v0), 0, 1) * np.clip((smax - sat) / ssoft, 0, 1)
    m = m * np.clip(1 - (g - r - 0.02) / 0.08, 0, 1)
    if zone is not None:
        # declared grass zones: every ground pixel (not grey asphalt or pale concrete: saturation over ~0.08; not a red
        # kerb; not dark) takes the green fully
        ground = np.clip((sat - 0.06) / 0.05, 0, 1) * np.clip((v - 0.2) / 0.1, 0, 1) * np.clip(1 - (r - g - 0.08) / 0.07, 0, 1)
        m = np.maximum(m, zone * ground)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    tr, tg, tb = opt.get("green", (0.38, 0.47, 0.24))
    k = lum / (0.299 * tr + 0.587 * tg + 0.114 * tb)
    green = np.clip(np.stack([tr * k, tg * k, tb * k], -1) * opt.get("dark", 0.88), 0, 1)
    out = im * (1 - m[..., None]) + green * m[..., None]
    return (np.clip(out, 0, 1) * 255).astype(np.uint8), float(m.mean())


def only_pit_exit_cones():
    """`--only pit_exit_cones`: recompute that one section from the existing scenery.json's pit_lane and write the
    file back with every other section unchanged (no downloads, no ortho regrade)."""
    path = os.path.join(OUT, "scenery.json")
    with open(path) as fh:
        sc = json.load(fh)
    out = {}
    for k, v in sc.items():
        if k == "pit_exit_cones":
            continue
        out[k] = v
        if k == "paved_zones":
            out["pit_exit_cones"] = pit_exit_cones(Track(), sc.get("pit_lane"), sc.get("barriers"))
    with open(path, "w") as fh:
        json.dump(out, fh, separators=(",", ":"))
    log(f"wrote {path} (pit_exit_cones only)")


if __name__ == "__main__":
    # normally run as `build_track.py --track <id> --stage scenery`; directly: --track <id> --dir <package dir>
    import argparse

    import trackcfg

    ap = argparse.ArgumentParser()
    ap.add_argument("--track", required=True)
    ap.add_argument("--dir", required=True, help="package directory holding track.json / heightfield.bin")
    ap.add_argument("--only", choices=["pit_exit_cones"])
    a = ap.parse_args()
    cfg_ = trackcfg.load(a.track)
    bl.configure(cfg_)
    configure(cfg_, os.path.abspath(a.dir))
    only_pit_exit_cones() if a.only else main()
