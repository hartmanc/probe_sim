"""Build the Laguna Seca scenery package: public/tracks/laguna_seca/{scenery.json, far_heightfield.bin, far_ortho.jpg}
and regrade ortho.jpg.

    uv run --python 3.12 --with numpy,scipy,rasterio,pyproj,shapely,pillow,requests,laspy[lazrs] \
        python tools/track/build_scenery.py

Reads track.json / heightfield.bin written by build_laguna.py. Format: CONTRACTS.md section 2b and
tools/track/README.md. Downloads are cached in tools/track/cache/.
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
import build_laguna as bl  # noqa: E402  (frames, DEM window, NAIP helpers, grade_ortho)

CACHE, OUT, PREVIEWS = bl.CACHE, bl.OUT, bl.PREVIEWS
UA = {"User-Agent": "probe-sim/0.1"}
EPT = "https://s3-us-west-2.amazonaws.com/usgs-lidar-public/CA_FEMA_Z4_B1_2018/"  # same 2017 FEMA R9 project as the DEM
DEM13 = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n37w122/USGS_13_n37w122.tif"
FAR_HALF, FAR_DX, FAR_ORTHO_PX = 2500.0, 10.0, 5.0  # far terrain: 5 x 5 km at 10 m, image at 5 m/px
CELL = 1.0  # canopy grid, m
log = bl.log


def rnd(v, d=2):
    return float(round(float(v), d))


# ---------------------------------------------------------------- track
class Track:
    def __init__(self):
        with open(os.path.join(OUT, "track.json")) as fh:
            t = json.load(fh)
        self.t = t
        self.C = np.array(t["center"])
        self.L = np.array(t["left"])
        self.R = np.array(t["right"])
        self.n = t["n"]
        h = t["heightfield"]
        self.hf = np.fromfile(os.path.join(OUT, h["file"]), np.float32).reshape(h["ny"], h["nx"])
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
    cache = os.path.join(CACHE, "lidar_points.npz")
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
    cache = os.path.join(CACHE, "lidar_grids.npz")
    box = trk.box
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
        root = ET.parse(os.path.join(CACHE, "laguna_osm.xml")).getroot()
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


def buildings(trk, G, osm):
    CHM = np.nan_to_num(G["DSM"] - G["DEM"], nan=0.0)
    out, taken = [], np.zeros_like(CHM, bool)
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
        hv = CHM[m]
        h = float(np.percentile(hv, 85)) if (hv > 2).mean() > 0.3 else 0.0
        lv = w["tags"].get("building:levels")
        if h < 2.5:
            h = float(lv) * 3.2 if lv else 4.0
        h = min(max(h, 2.5), 30.0)
        kind = BUILDING_KIND.get(w["tags"]["building"], "building")
        if w["id"] in HANGARS:
            kind = "hangar"
        if w["tags"].get("name") == "Tower":
            kind = "tower"
        zb = float(np.min(trk.ground(xy[:, 0], xy[:, 1])))
        out.append({"kind": kind, "name": HANGARS.get(w["id"], w["tags"].get("name", "")), "z": rnd(zb, 2), "h": rnd(h, 1),
                    "footprint": [[rnd(x, 1), rnd(y, 1)] for x, y in xy], "src": "osm"})
    n_osm = len(out)
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
    return out, taken


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
    T = np.c_[x, y, z, hmax, rad][keep]
    log(f"trees: {len(T)} crowns; height p10/p50/p90 {np.percentile(T[:, 3], [10, 50, 90]).round(1)} m, "
        f"radius p50 {np.median(T[:, 4]):.1f} m")
    return T


# ---------------------------------------------------------------- bridges
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
        out.append({"id": w["id"], "kind": kind, "name": name, "s": st, "deck_z": rnd(deck, 2),
                    "a": [rnd(p0[0], 1), rnd(p0[1], 1)], "b": [rnd(p1[0], 1), rnd(p1[1], 1)],
                    "width": 3.0 if kind == "foot" else 8.0, "deck_src": src})
    out.sort(key=lambda b: b["s"])
    for b in out:
        log(f"bridge {b['id']} {b['kind']} over s={b['s']} deck {b['deck_z'] - trk.C[b['s'], 2]:.1f} m above track ({b['deck_src']})")
    return out


# ---------------------------------------------------------------- barriers
# Tyre walls on the outside of the big stops: (turn in track.json corners, metres before, metres after the corner's s).
# Side is derived from the corner direction (outside = right for a left-hander), so the script follows a rebuilt track.
TYRE_CORNERS = [("T2", 48, 62), ("T5", 44, 56), ("T8", 39, 21), ("T8A", 15, 55), ("T9", 45, 65), ("T11", 45, 50)]


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


def barriers(trk, osm):
    out = []
    walls = osm.select(lambda t: t.get("barrier") == "wall", trk.box)
    wall_pts = []
    for w in walls:
        for run in polyline_runs(trk, w["xy"]):
            i, lat, dout = trk.project(run)
            d = float(np.median(dout))
            # Close to the edge: concrete wall with catch fence (spectator banks, photo 01). Further out, behind
            # run-off: Armco on posts.
            kind = "concrete" if d < 14 else "armco"
            out.append({"kind": kind, "h": 1.0 if kind == "concrete" else 0.75,
                        "fence": 3.0 if kind == "concrete" else 0.0, "pts": with_z(trk, run), "src": f"osm:{w['id']}"})
            wall_pts.append(np.c_[run, i, lat, dout])
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
    pit = [w for w in osm.ways if w["tags"].get("name") == "Pit Lane"]
    if pit:
        PL = resample_line(pit[0]["xy"], 2.0)
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
            # the real pit wall ends at the T1 kink; the pit-exit lane down to the Andretti hairpin has no wall
            s1 = min(s1, trk.n + 260)
            # catch fence on the front straight only (to ~120 m past the line); the rest of the wall is bare
            mid = min(max(trk.n + 120, s0 + 2), s1)
            for a, b_, fence in ((s0, mid, 3.5), (mid, s1, 0.0)):
                if b_ - a >= 4:
                    P = edge_line(trk, a, b_, +1, 0.6)
                    out.append({"kind": "pitwall", "h": 1.1, "fence": fence, "pts": with_z(trk, P),
                                "src": "OSM pit lane extent"})
            log(f"pit wall: s {s0 % trk.n}..{s1 % trk.n} ({s1 - s0} m)")
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
def kerbs(trk):
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
        if c["turn"] != "T8":  # the Corkscrew's T8 exit is T8A's entry
            out.append({"side": -side, "s0": s + 15, "s1": s + 15 + int(min(max(rad, 45), 70)), "kind": "exit",
                        "paint": 1.5})
    for k in out:
        k["s0"] %= trk.n
        k["s1"] = k["s0"] + ((k["s1"] - k["s0"]) % trk.n)
    log(f"kerbs: {len(out)} strips, {sum(k['s1'] - k['s0'] for k in out)} m")
    return out


KERB_W = 0.9  # m; v2 track edges include the kerbs, so kerbs lie inside the edge (edge - KERB_W .. edge)


PIT_HALF_DEFAULT = 4.0  # m (8 m paved width) when the image gives no edge


def pit_lane(trk, osm):
    """Paved pit lane from the OSM "Pit Lane" way: 1 m stations, half-widths from the NAIP asphalt extent
    (build_laguna.detect_edges, clamped 3-6 m, fallback 4 m), and the track-facing edge clamped to the track edge so
    the two surfaces meet without overlapping. Where the pit lane runs inside the track's own paved width (the
    pit-exit apron through T1 is part of the v2 track) it is dropped, so it comes as separate parts. Heights: DEM
    across the section, corrected linearly so a clamped edge matches the track's edge height (smooth merges)."""
    from PIL import Image
    from scipy.ndimage import gaussian_filter1d

    w = [w for w in osm.ways if w["tags"].get("name") == "Pit Lane"]
    if not w:
        return None
    P = resample_line(w[0]["xy"], 1.0)
    P = np.c_[gaussian_filter1d(P[:, 0], 2, mode="nearest"), gaussian_filter1d(P[:, 1], 2, mode="nearest")]
    n = len(P)
    d = np.gradient(P, axis=0)
    T = d / np.linalg.norm(d, axis=1, keepdims=True)
    Np = np.c_[-T[:, 1], T[:, 0]]
    # width from the image
    o = trk.t["ortho"]
    raw = os.path.join(CACHE, f"naip_{int(o['x0'])}_{int(o['y0'])}_{int(o['x1'])}_{int(o['y1'])}_{o['width_px']}x{o['height_px']}.png")
    half = np.full((n, 2), PIT_HALF_DEFAULT)
    src = "default 4 m"
    if os.path.exists(raw):
        ortho = bl.Ortho(np.asarray(Image.open(raw).convert("RGB")), trk.box)
        try:
            h, stats, ok = bl.detect_edges(P, ortho, reach=9.0)
            for k in range(2):
                if np.isfinite(h[:, k]).all():
                    half[:, k] = np.clip(h[:, k], 3.0, 6.0)
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
    log(f"pit lane: {len(parts)} parts, {tot} m paved (OSM way {n} m), width {src}, "
        f"half-widths p50 {np.median(half, 0).round(1)} m; parts at track s " + ", ".join(f"{p['track_s'][0]}-{p['track_s'][1]}" for p in parts))
    return {"spacing_m": 1.0, "fractions": fr, "open": True, "parts": parts}


# Paved runoff seen in the team's onboard video (2026-10-12, GL030045; tools/track/compare/), newer than the 2017
# lidar and the NAIP image: (turn, metres before, metres after the corner's s). Always on the outside of the corner.
PAVED_RUNOFF = [("T6", 15, 80), ("T9", 30, 75), ("T10", 20, 75)]


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
    from PIL import Image

    if not pit or len(pit["parts"]) < 2:
        return None
    n = trk.n
    a, b = pit["parts"][0], pit["parts"][1]
    # start: last stretch of part 0 that touches the track edge; end: part 1 until it pulls away (gap > 0.5 m)
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
    for w in barriers or []:
        if w["kind"] != "pitwall" or not w.get("fence"):
            continue
        i, lat, out = trk.project(np.array(w["pts"])[:, :2])
        near = (lat > 0) & (np.abs(out) < 2.0) & (((i - s0) % n) < 200)
        if near.any():
            s0 = max(s0, int(((i[near] - s0) % n).max() + s0) + 2)
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
        log(f"paved runoff {turn}: s {st[0]}-{st[-1]}, {'left' if side > 0 else 'right'} side, width p50 {np.median(width):.1f} m "
            f"({np.isfinite(wd).mean():.0%} of stations bounded by an OSM wall)")
    return {"spacing_m": 1.0, "fractions": fr, "open": True, "parts": parts}


def edge_lines(trk, kerb, osm, gap=3, min_run=10):
    """Painted white edge lines along both edges, except through kerbs (plus `gap` m) and where the pit lane merges
    with the left edge. The NAIP image cannot show them: at 0.6 m/px the 0.12 m line is blurred, and asphalt and dry
    dirt have nearly the same luminance there (they differ in hue), so lines are assumed everywhere else."""
    n = trk.n
    runs = []
    pit = [w for w in osm.ways if w["tags"].get("name") == "Pit Lane"]
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


# (turn, s offset from its apex, side +1 left/-1 right, text, board width m, distance beyond the edge m or None = at
# the outside wall) - from the onboard frames
BANNER_BOARDS = [
    ("T1", -70, -1, "PORSCHE", 10.0, 14.0),
    ("T6", 10, -1, "PORSCHE", 8.0, None),
    ("T7", 10, -1, "WEATHERTECH", 10.0, None),
    ("T11", -80, -1, "MOTUL", 6.0, None), ("T11", -72, -1, "LAGUNA SECA", 6.0, None),
    ("T11", -64, -1, "MICHELIN", 6.0, None), ("T11", -56, -1, "TIRE RACK", 6.0, None),
]


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


def landmarks(trk, T, brg):
    out = []
    corners = {c["turn"]: c for c in trk.t["corners"] if c.get("turn")}
    # brake marker boards 3-2-1 (100 ft steps are 30 m; the circuit uses 3/2/1 at roughly 150/100/50 m)
    for t in ("T2", "T5", "T8", "T11"):
        c = corners[t]
        side = -1 if c["dir"] == "left" else 1
        for k, dist in ((3, 150), (2, 100), (1, 50)):
            out.append(board(trk, c["s"] - dist, side, 3.0, "brake", str(k), h=1.6, w=1.0))
    # corner-number boards at turn-in, outside
    for t, c in corners.items():
        side = -1 if c["dir"] == "left" else 1
        num = t[1:]
        out.append(board(trk, c["s"] - 75, side, 5.0, "corner", num, h=2.2, w=1.4))
    # starter's flag stand on the pit wall, just before the S/F bridge
    sf = next((b for b in brg if b["s"] < 120 or b["s"] > trk.n - 60), None)
    s_flag = (sf["s"] - 8) if sf else 30
    st = s_flag % trk.n
    p = trk.C[st, :2] + trk.N[st] * (trk.hw(st, 1) + 1.0)
    out.append({"kind": "flagstand", "text": "", "x": rnd(p[0], 2), "y": rnd(p[1], 2),
                "z": rnd(float(trk.ground(p[0], p[1])[0]), 2), "heading": rnd(math.atan2(-trk.T[st, 1], -trk.T[st, 0]), 3),
                "h": 7.5, "w": 2.6})
    # the Corkscrew oak: biggest crown on the inside (left) of T8
    c8 = corners["T8"]
    i, lat, dout = trk.project(T[:, :2])
    near = (np.abs(i - c8["s"]) < 40) & (lat > 0) & (dout > 2) & (dout < 45)
    if near.any():
        k = np.nonzero(near)[0][np.argmax(T[near, 3] * T[near, 4])]
        T[k, 3] = max(T[k, 3], 13.0)
        T[k, 4] = max(T[k, 4], 8.0)
        out.append({"kind": "oak", "text": "Corkscrew oak", "x": rnd(T[k, 0], 1), "y": rnd(T[k, 1], 1),
                    "z": rnd(T[k, 2], 2), "heading": 0, "h": rnd(T[k, 3], 1), "w": rnd(T[k, 4], 1)})
        log(f"Corkscrew oak: lidar crown at ({T[k, 0]:.0f}, {T[k, 1]:.0f}), {T[k, 3]:.1f} m tall, r {T[k, 4]:.1f} m")
    # advertising boards and the Rahal cable gantry seen in the onboard video (tools/track/compare/): placed against
    # the outside wall (OSM) or at a fixed distance; (turn or None, s offset or absolute s, side, text, width)
    corners_all = corners
    for turn, ds, side, text, width, dist in BANNER_BOARDS:
        s0 = corners_all[turn]["s"] + ds if turn else ds
        st = int(s0) % trk.n
        out.append(fence_board(trk, st, side, dist, text, width))
    s_g = (corners_all["T7"]["s"] - 150) % trk.n
    a_ = trk.C[s_g, :2] + trk.N[s_g] * (trk.hw(s_g, 1) + 9)
    b_ = trk.C[s_g, :2] - trk.N[s_g] * (trk.hw(s_g, -1) + 9)
    out.append({"kind": "gantry", "text": "", "x": rnd(a_[0], 2), "y": rnd(a_[1], 2), "z": rnd(float(trk.ground(*a_)[0]), 2),
                "x2": rnd(b_[0], 2), "y2": rnd(b_[1], 2), "z2": rnd(float(trk.ground(*b_)[0]), 2), "heading": 0, "h": 17.0, "w": 2.2})
    return out


BANNERS = {  # text on the faces of each bridge, by OSM id; [face toward oncoming cars, face away] (from the onboard video)
    "60116334": [["MISSION", "WEATHERTECH", "MISSION", "PORSCHE"], ["WEATHERTECH", "LAGUNA SECA"]],  # S/F bridge
    "60116327": [["TIRE RACK"], ["TIRE RACK"]],                                                      # T3-T4 arch
    "459576002": [["WEATHERTECH", "AUTO. HOME. PET. FIND YOUR FIT."], ["WEATHERTECH"]],              # after T8A
}
BRIDGE_STYLE = {"60116327": "arch"}  # the T3-T4 bridge is the TIRE RACK arch (curved truss), not a flat deck
HANGARS = {"639859964": "kinetic"}  # OSM building id -> sign on the gabled hangar seen ahead-left on the T3 approach


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
        st = np.arange(k["s0"], k["s1"]) % trk.n
        P = trk.C[st, :2] + trk.N[st] * (k["side"] * trk.hw(st, k["side"]))[:, None]
        d.line([px(x, y) for x, y in P], fill=(255, 0, 0), width=4)
    for g in brg:
        d.line([px(*g["a"]), px(*g["b"])], fill=(255, 255, 0), width=6)
    for m in marks:
        p = px(m["x"], m["y"])
        d.rectangle([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=(0, 0, 0), outline=(255, 255, 0))
    im.save(path)


def main():
    from PIL import Image

    trk = Track()
    # 1. regrade the near ortho from the cached NAIP mosaic
    o = trk.t["ortho"]
    raw = os.path.join(CACHE, f"naip_{int(o['x0'])}_{int(o['y0'])}_{int(o['x1'])}_{int(o['y1'])}_{o['width_px']}x{o['height_px']}.png")
    if os.path.exists(raw):
        Image.fromarray(bl.grade_ortho(np.asarray(Image.open(raw).convert("RGB")))).save(
            os.path.join(OUT, "ortho.jpg"), quality=84, optimize=True)
        log(f"ortho.jpg regraded: {os.path.getsize(os.path.join(OUT, 'ortho.jpg')) / 1e6:.2f} MB")
    else:
        log("WARNING: cached NAIP mosaic missing, ortho.jpg left as is (run build_laguna.py)")
    G = lidar_grids(trk)
    osm = Osm()
    bld, taken = buildings(trk, G, osm)
    T = trees(trk, G, taken)
    brg = bridges(trk, G, osm)
    for b in brg:
        b["banners"] = BANNERS.get(b["id"], [["LAGUNA SECA"], ["LAGUNA SECA"]])
        b["style"] = BRIDGE_STYLE.get(b["id"], "deck")
    bar, bar_tot = barriers(trk, osm)
    for b_ in bar:
        if b_["kind"] in ("concrete", "armco", "pitwall"):
            P_ = np.array(b_["pts"])[:, :2]
            _WALL_CACHE.append(trk.project(P_))
    kerb = kerbs(trk)
    lines = edge_lines(trk, kerb, osm)
    pit = pit_lane(trk, osm)
    zones = paved_zones(trk, osm)
    cones = pit_exit_cones(trk, pit, bar)
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
        "kerbs": {"width": KERB_W, "inside": True, "stripe_m": 2.0, "strips": kerb},
        "edge_lines": {"width": 0.12, "inset": 0.15, "runs": lines},
        "pit_lane": pit,
        "paved_zones": zones,
        "pit_exit_cones": cones,
        "landmarks": marks,
    }
    with open(os.path.join(OUT, "scenery.json"), "w") as fh:
        json.dump(sc, fh, separators=(",", ":"))
    preview(trk, T, Tf, bld, bar, kerb, brg, marks, os.path.join(PREVIEWS, "scenery.png"))
    tot = 0
    for f in ("scenery.json", "far_heightfield.bin", "far_ortho.jpg", "ortho.jpg"):
        sz = os.path.getsize(os.path.join(OUT, f))
        tot += sz if f != "ortho.jpg" else 0
        log(f"wrote {f}: {sz / 1e6:.2f} MB")
    log(f"new payload (excluding the regraded ortho.jpg): {tot / 1e6:.2f} MB")
    log(f"summary: {len(T)} trees (lidar) + {len(Tf)} far trees (NAIP), {len(bld)} buildings, {len(brg)} bridges, "
        f"{len(bar)} barrier runs ({sum(bar_tot.values()):.0f} m), {len(kerb)} kerbs, {len(marks)} landmarks")
    if os.path.getsize(os.path.join(OUT, "ortho.jpg")) > 1.5e6:
        log("WARNING: ortho.jpg over 1.5 MB")


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
    if sys.argv[1:3] == ["--only", "pit_exit_cones"]:
        only_pit_exit_cones()
    else:
        main()
