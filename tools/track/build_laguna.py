"""Build the Laguna Seca track package: public/tracks/laguna_seca/{track.json, heightfield.bin, ortho.jpg} and tools/track/previews/preview.png.

    uv run --python 3.12 --with numpy,scipy,rasterio,pyproj,shapely,pillow,requests,pandas,matplotlib \
        python tools/track/build_laguna.py

Frames and file formats follow CONTRACTS.md sections 1 and 2. Downloads are cached in tools/track/cache/.
See tools/track/README.md for sources and method.
"""

import io
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
from scipy.interpolate import splev, splprep
from scipy.ndimage import binary_closing, gaussian_filter, gaussian_filter1d, map_coordinates, median_filter
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CACHE = os.path.join(HERE, "cache")
OUT = os.path.join(ROOT, "public", "tracks", "laguna_seca")
PREVIEWS = os.path.join(ROOT, "tools", "track", "previews")
LAPS = "/Users/cobyhartman/projects/starlink-go-pro/laps"  # read-only race-logger analysis
GPS_CENTRELINE = os.path.join(LAPS, "centreline.npy")

LAT0, LON0, R = 36.5843, -121.7535, 6378137.0
COSL = math.cos(math.radians(LAT0))
OSM_BBOX = (-121.775, 36.572, -121.735, 36.598)
DEM_TILES = [
    "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/CA_AZ_FEMA_R9_Lidar_2017_D18/TIFF/"
    f"USGS_1M_10_{t}_CA_AZ_FEMA_R9_Lidar_2017_D18.tif"
    for t in ("x61y405", "x61y406")
]
NAIP = "https://imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/exportImage"

MARGIN = 200.0  # m around the track bounding box for heightfield and ortho
HF_DX = 2.0
ORTHO_PX = 0.6  # m per pixel requested
HALF_MIN, HALF_MAX, HALF_FALLBACK = 4.5, 8.5, 6.5
FRACTIONS = [-1, -0.6667, -0.3333, 0, 0.3333, 0.6667, 1]

# Cross slope limits. The lidar shows real, planar banking of 12-15 % (always toward the inside) at T5, the
# Corkscrew (T8/T8A) and Rainey Curve, so the hard limit is 16 %; anything over 12 % is reported with its corner
# and must be near-planar (the four inner segment slopes within 7 points of each other), which DEM noise would not
# be. (Rainey's inside quarter flattens out by ~6 points, a gutter/kerb zone.)
CROSS_HARD, CROSS_SOFT, CROSS_PLANAR = 0.16, 0.12, 0.07

# Standard Laguna turns. s_laps = position in the race-logger frame (length 3558, from traces2.ANCH /
# corners.CORN), sign = +1 left-hander, -1 right-hander (driving counter-clockwise).
TURNS = [
    ("T1", None, 240, +1), ("T2", "Andretti Hairpin", 520, +1), ("T3", None, 790, -1), ("T4", None, 1060, -1),
    ("T5", None, 1530, +1), ("T6", None, 1940, +1), ("T7", None, 2360, -1), ("T8", "The Corkscrew", 2440, +1),
    ("T8A", "The Corkscrew", 2490, -1), ("T9", "Rainey Curve", 2690, +1), ("T10", None, 2950, -1),
    ("T11", None, 3240, +1),
]


def log(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------- frames
def enu(lat, lon):
    return np.radians(np.asarray(lon) - LON0) * R * COSL, np.radians(np.asarray(lat) - LAT0) * R


def lonlat(x, y):
    return LON0 + np.degrees(np.asarray(x) / (R * COSL)), LAT0 + np.degrees(np.asarray(y) / R)


def grade_ortho(img):
    """Dehaze the NAIP mosaic for display: a black point common to all channels (keeps the hue;
    no warm shift), a common white point, a gentle S-curve and +6 % saturation. Edge detection runs on the
    ungraded image."""
    a = np.asarray(img).astype(np.float32) / 255.0
    flat = a.reshape(-1, 3)
    pc = np.percentile(flat, 0.5, axis=0)
    black = np.full(3, pc.min() * 0.9, np.float32)
    white = np.percentile(flat.mean(1), 99.8)
    a = np.clip((a - black) / (white - black.mean()), 0, 1) ** 1.25  # keep mid-tones near the original value
    s = 3 * a ** 2 - 2 * a ** 3                       # smoothstep S-curve, blended 25 %
    a = 0.75 * a + 0.25 * s
    luma = (a * np.array([0.299, 0.587, 0.114], np.float32)).sum(-1, keepdims=True)
    a = np.clip(luma + (a - luma) * 1.06, 0, 1)
    return (a * 255 + 0.5).astype(np.uint8)


# ---------------------------------------------------------------- geometry helpers
def tangents(P):
    t = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    return t / np.linalg.norm(t, axis=1)[:, None]


def left_normals(P):
    t = tangents(P)
    return np.c_[-t[:, 1], t[:, 0]]


def curvature(P, sigma=4.0):
    """Signed curvature (+ = turning left) of a closed 1 m polyline, Gaussian-smoothed over sigma metres."""
    t = tangents(P)
    psi = np.arctan2(t[:, 1], t[:, 0])
    dpsi = np.angle(np.exp(1j * (np.roll(psi, -1) - psi)))  # wrapped per-step heading change
    seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
    k = dpsi / np.maximum(seg, 1e-6)
    return gaussian_filter1d(k, sigma, mode="wrap") if sigma else k


def resample_closed(P, n=None, smooth=0.0, k=3):
    """Periodic spline through closed polyline P (no repeated end point); return n points equally spaced in arc length
    starting at P[0], plus the loop length."""
    d = np.linalg.norm(np.diff(np.r_[P, P[:1]], axis=0), axis=1)
    keep = np.r_[True, d[:-1] > 1e-3]
    P = P[keep]
    Q = np.r_[P, P[:1]]
    u = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Q, axis=0), axis=1))]
    tck, _ = splprep([Q[:, 0], Q[:, 1]], u=u, s=smooth, per=1, k=k)
    # arc length of the spline itself, by dense sampling
    uu = np.linspace(0, u[-1], int(u[-1] * 10) + 1)
    xx, yy = splev(uu, tck)
    arc = np.r_[0, np.cumsum(np.hypot(np.diff(xx), np.diff(yy)))]
    L = arc[-1]
    if n is None:
        n = int(round(L))
    ui = np.interp(np.arange(n) * L / n, arc, uu)
    x, y = splev(ui, tck)
    return np.c_[x, y], L


def project(P, Q):
    """Project points Q onto closed polyline P (1 m-ish). Returns fractional index and signed lateral (+left)."""
    tree = cKDTree(P)
    _, i = tree.query(Q)
    n = len(P)
    t = tangents(P)
    nl = np.c_[-t[:, 1], t[:, 0]]
    rel = Q - P[i]
    seg = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
    along = (rel * t[i]).sum(1) / seg[i]
    return (i + along) % n, (rel * nl[i]).sum(1)


# ---------------------------------------------------------------- 1. OSM centreline
def osm_loop():
    path = os.path.join(CACHE, "laguna_osm.xml")
    if not os.path.exists(path):
        import requests

        log("fetching OSM map", OSM_BBOX)
        r = requests.get("https://api.openstreetmap.org/api/0.6/map",
                         params={"bbox": ",".join(map(str, OSM_BBOX))}, headers={"User-Agent": "probe-sim/0.1"},
                         timeout=120)
        r.raise_for_status()
        open(path, "wb").write(r.content)
    root = ET.parse(path).getroot()
    nodes = {n.get("id"): (float(n.get("lat")), float(n.get("lon"))) for n in root.iter("node")}
    ways = {}
    for w in root.iter("way"):
        tags = {t.get("k"): t.get("v") for t in w.iter("tag")}
        if tags.get("highway") == "raceway" and "pit" not in tags.get("name", "").lower():
            ways[w.get("id")] = ([nd.get("ref") for nd in w.iter("nd")], tags.get("name", ""))
    log(f"OSM: {len(ways)} circuit ways:", sorted({n for _, n in ways.values()}))
    by_start = {nd[0]: wid for wid, (nd, _) in ways.items()}
    if len(by_start) != len(ways):
        raise SystemExit("OSM: two circuit ways start at the same node, cannot stitch")
    first = next(iter(ways))
    seq, names, wid = [], [], first
    for _ in range(len(ways)):
        nd, name = ways[wid]
        seq += nd[:-1]
        names += [name] * (len(nd) - 1)
        nxt = by_start.get(nd[-1])
        if nxt is None:
            raise SystemExit(f"OSM: way {wid} ends at node {nd[-1]} which starts no other circuit way")
        wid = nxt
    if wid != first:
        raise SystemExit("OSM: circuit ways do not close into a single loop")
    ll = np.array([nodes[i] for i in seq])
    x, y = enu(ll[:, 0], ll[:, 1])
    return np.c_[x, y], names


# ---------------------------------------------------------------- 3. DEM
def dem_window(box):
    """Merge the two 3DEP 1 m tiles over the ENU box into one UTM 10N grid (cached). Returns (Z, transform, crs)."""
    cache = os.path.join(CACHE, "dem_window.npz")
    if os.path.exists(cache):
        d = np.load(cache, allow_pickle=False)
        if np.allclose(d["box"], box):
            return d["Z"], tuple(d["T"]), str(d["crs"])
    import rasterio
    from pyproj import Transformer
    from rasterio.windows import from_bounds

    with rasterio.open("/vsicurl/" + DEM_TILES[0]) as ds:
        crs = ds.crs.to_string()
    tr = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    cx = np.linspace(box[0], box[2], 50)
    cy = np.linspace(box[1], box[3], 50)
    gx, gy = np.meshgrid(cx, cy)
    lon, lat = lonlat(gx, gy)
    E, N = tr.transform(lon, lat)
    e0, e1 = math.floor(E.min()) - 20, math.ceil(E.max()) + 20
    n0, n1 = math.floor(N.min()) - 20, math.ceil(N.max()) + 20
    Z = np.full((n1 - n0, e1 - e0), np.nan, np.float32)  # row 0 = northing n1 (cell centres at +0.5)
    for url in DEM_TILES:
        with rasterio.open("/vsicurl/" + url) as ds:
            log("DEM: reading window from", url.rsplit("/", 1)[1], ds.crs, ds.res)
            b = ds.bounds
            le, be, re, te = max(e0, b.left), max(n0, b.bottom), min(e1, b.right), min(n1, b.top)
            if le >= re or be >= te:
                continue
            win = from_bounds(le, be, re, te, ds.transform).round_offsets().round_lengths()
            a = ds.read(1, window=win).astype(np.float32)
            a[(a == ds.nodata) | (a < -1000)] = np.nan
            wt = ds.window_transform(win)
            # place into the merged grid (both tiles share the integer-metre grid offset by .0000067)
            c0 = int(round(wt.c - e0))
            r0 = int(round(n1 - wt.f))
            rr = slice(max(r0, 0), min(r0 + a.shape[0], Z.shape[0]))
            cc = slice(max(c0, 0), min(c0 + a.shape[1], Z.shape[1]))
            sub = a[rr.start - r0: rr.stop - r0, cc.start - c0: cc.stop - c0]
            tgt = Z[rr, cc]
            Z[rr, cc] = np.where(np.isfinite(sub), sub, tgt)
    T = (float(e0), float(n1))
    np.savez_compressed(cache, Z=Z, T=np.array(T), crs=crs, box=np.array(box))
    return Z, T, crs


class Dem:
    def __init__(self, box, sigma=0.0):
        Z, T, crs = dem_window(box)
        nan = ~np.isfinite(Z)
        log(f"DEM window {Z.shape}, {nan.mean() * 100:.3f}% holes")
        if nan.any():  # fill holes by nearest
            from scipy.ndimage import distance_transform_edt

            idx = distance_transform_edt(nan, return_distances=False, return_indices=True)
            Z = Z[tuple(idx)]
        if sigma:
            Z = gaussian_filter(Z, sigma)
        self.Z, self.e0, self.n1 = Z, T[0], T[1]
        from pyproj import Transformer

        self.tr = Transformer.from_crs("EPSG:4326", crs, always_xy=True)

    def __call__(self, x, y):
        x, y = np.asarray(x, float), np.asarray(y, float)
        lon, lat = lonlat(x.ravel(), y.ravel())
        E, N = self.tr.transform(lon, lat)
        col = E - self.e0 - 0.5
        row = self.n1 - N - 0.5
        z = map_coordinates(self.Z, [row, col], order=1, mode="nearest")
        return z.reshape(x.shape)


# ---------------------------------------------------------------- 4. NAIP ortho
def fetch_ortho(box):
    """North-up RGB image of the ENU box from the NAIP image service, stitched from tiles (cached)."""
    x0, y0, x1, y1 = box
    W = int(math.ceil((x1 - x0) / ORTHO_PX))
    H = int(math.ceil((y1 - y0) / ORTHO_PX))
    scale = min(1.0, 4096 / max(W, H))
    W, H = int(round(W * scale)), int(round(H * scale))
    cache = os.path.join(CACHE, f"naip_{int(x0)}_{int(y0)}_{int(x1)}_{int(y1)}_{W}x{H}.png")
    from PIL import Image

    if os.path.exists(cache):
        return np.asarray(Image.open(cache).convert("RGB")), W, H

    import time

    import requests

    tdir = os.path.join(CACHE, "naip_tiles")
    os.makedirs(tdir, exist_ok=True)
    TS = 1024
    img = np.zeros((H, W, 3), np.uint8)
    for r0 in range(0, H, TS):
        for c0 in range(0, W, TS):
            h, w = min(TS, H - r0), min(TS, W - c0)
            # tile pixel edges in ENU (row 0 = north)
            tx0 = x0 + c0 * (x1 - x0) / W
            tx1 = x0 + (c0 + w) * (x1 - x0) / W
            ty1 = y1 - r0 * (y1 - y0) / H
            ty0 = y1 - (r0 + h) * (y1 - y0) / H
            lo0, la0 = lonlat(tx0, ty0)
            lo1, la1 = lonlat(tx1, ty1)
            bbox = f"{lo0:.8f},{la0:.8f},{lo1:.8f},{la1:.8f}"
            tpath = os.path.join(tdir, f"{bbox}_{w}x{h}.png")
            if os.path.exists(tpath):
                img[r0:r0 + h, c0:c0 + w] = np.asarray(Image.open(tpath).convert("RGB"))
                continue
            # The server keeps pixels square in degrees and widens the bbox to fit, so ask for square-degree
            # pixels, read back the extent it actually used, and resample onto our ENU-linear grid.
            wr = w
            hr = max(1, int(round(w * (la1 - la0) / (lo1 - lo0))))
            params = {"bbox": bbox, "bboxSR": 4326, "imageSR": 4326, "size": f"{wr},{hr}", "format": "png",
                      "f": "json"}
            log(f"NAIP tile r{r0} c{c0} {w}x{h} (requested {wr}x{hr})")
            for attempt in range(8):
                try:
                    r = requests.get(NAIP, params=params, timeout=180, headers={"User-Agent": "probe-sim/0.1"})
                    r.raise_for_status()
                    meta = r.json()
                    r2 = requests.get(meta["href"], timeout=180, headers={"User-Agent": "probe-sim/0.1"})
                    r2.raise_for_status()
                    src = np.asarray(Image.open(io.BytesIO(r2.content)).convert("RGB")).astype(np.float32)
                    break
                except Exception as e:  # noqa: BLE001
                    log("  retry:", str(e)[:80])
                    if attempt == 7:
                        raise
                    time.sleep(5 * (attempt + 1))
            ex = meta["extent"]
            Hs, Ws = src.shape[:2]
            # target pixel centres -> lon/lat -> source pixel coordinates
            cx = tx0 + (np.arange(w) + 0.5) * (tx1 - tx0) / w
            cy = ty1 - (np.arange(h) + 0.5) * (ty1 - ty0) / h
            lon, _ = lonlat(cx, 0 * cx)
            _, lat = lonlat(0 * cy, cy)
            sc = (lon - ex["xmin"]) / (ex["xmax"] - ex["xmin"]) * Ws - 0.5
            sr = (ex["ymax"] - lat) / (ex["ymax"] - ex["ymin"]) * Hs - 0.5
            RR, CCo = np.meshgrid(sr, sc, indexing="ij")
            out = np.stack([map_coordinates(src[..., k], [RR, CCo], order=1, mode="nearest") for k in range(3)], -1)
            t = Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8))
            t.save(tpath)
            img[r0:r0 + h, c0:c0 + w] = np.asarray(t)
    Image.fromarray(img).save(cache)
    return img, W, H


class Ortho:
    def __init__(self, img, box):
        self.img = img.astype(np.float32) / 255.0
        self.box = box
        self.H, self.W = img.shape[:2]
        rgb = self.img
        self.mean = rgb.mean(2)
        self.warm = rgb[..., 0] - rgb[..., 2]

    def rc(self, x, y):
        x0, y0, x1, y1 = self.box
        col = (np.asarray(x) - x0) / (x1 - x0) * self.W - 0.5
        row = (y1 - np.asarray(y)) / (y1 - y0) * self.H - 0.5
        return row, col

    def sample(self, arr, x, y):
        row, col = self.rc(x, y)
        return map_coordinates(arr, [row.ravel(), col.ravel()], order=1, mode="nearest").reshape(np.shape(x))


# ---------------------------------------------------------------- edges from imagery
def detect_edges(C, ortho, reach=13.0, step=0.3):
    """Half-widths (left, right) per station from the asphalt extent across the cross-section."""
    n = len(C)
    nl = left_normals(C)
    offs = np.arange(-reach, reach + 1e-9, step)
    X = C[:, 0:1] + offs[None, :] * nl[:, 0:1]
    Y = C[:, 1:2] + offs[None, :] * nl[:, 1:2]
    val = ortho.sample(ortho.mean, X, Y)
    warm = ortho.sample(ortho.warm, X, Y)
    # Track asphalt in NAIP is a cool, neutral grey (R <= G ~ B); dirt and dry grass are warm (R > B), concrete
    # run-off and paint are brighter, trees/shadows/barriers darker. Reference colour per station = median of the
    # central +-2.5 m, smoothed along s.
    mid = np.abs(offs) <= 2.5
    vref = gaussian_filter1d(np.median(val[:, mid], 1), 15, mode="wrap")
    wref = gaussian_filter1d(np.median(warm[:, mid], 1), 15, mode="wrap")
    road = (warm < wref[:, None] + 0.035) & (val < vref[:, None] + 0.085) & (val > vref[:, None] - 0.12)
    paint = (val >= vref[:, None] + 0.085) & (warm < wref[:, None] + 0.05)  # lines, kerbs: short runs allowed
    cls = np.where(road, 1, np.where(paint, 2, 0))  # 1 asphalt, 2 bright neutral (paint or concrete), 0 other
    gap = int(round(1.8 / step))  # this much non-road ends the road
    c = len(offs) // 2
    half = np.full((n, 2), np.nan)
    ok = (cls[:, c - 3:c + 4] > 0).mean(1) >= 0.6
    pmax = int(round(1.5 / step))  # a bright run longer than this is concrete run-off, not a painted line
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
                        last = k - prun + int(round(0.6 / step))  # keep about one line width of the bright run
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
    stats = {"stations": n, "centre_on_asphalt": float(ok.mean()), "left_found": float(raw_ok[:, 0].mean()),
             "right_found": float(raw_ok[:, 1].mean())}
    out = np.empty_like(half)
    for side in range(2):
        h = half[:, side].copy()
        good = np.isfinite(h) & (h >= 3.0)
        stats[f"side{side}_valid"] = float(good.mean())
        if good.mean() < 0.5:
            out[:, side] = np.nan
            continue
        idx = np.arange(n)
        h = np.interp(idx, idx[good], h[good], period=n)
        h = median_filter(h, size=41, mode="wrap")  # robust: kill short spikes (kerb shadows, run-off)
        h = gaussian_filter1d(h, 8, mode="wrap")
        out[:, side] = np.clip(h, HALF_MIN, HALF_MAX)
    return out, stats, raw_ok


# ---------------------------------------------------------------- main
def main():
    os.makedirs(CACHE, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PREVIEWS, exist_ok=True)
    fails = []

    # -- OSM loop, oriented and smoothed
    P, names = osm_loop()
    G = np.load(GPS_CENTRELINE)
    log(f"OSM loop: {len(P)} nodes; GPS centreline: {len(G)} pts")
    # direction: GPS order must increase along the OSM loop
    gi, _ = project(G, P)
    step = np.angle(np.exp(1j * 2 * np.pi * np.diff(np.r_[gi, gi[:1]]) / len(G)))
    if step.sum() < 0:
        P, names = P[::-1].copy(), names[::-1]
        log("OSM loop reversed to match the driving direction")
    # densify the coarse OSM polyline at 5 m first so the periodic smoothing spline sees uniform support
    D, _ = resample_closed(P, n=None, smooth=0.0, k=1)
    D = D[::5]
    C0, L0 = resample_closed(D, smooth=len(D) * 0.25 ** 2)
    log(f"OSM spline loop length {L0:.1f} m")

    # -- compare with GPS
    _, lat = project(C0, G)
    log(f"GPS vs OSM lateral: median |d| {np.median(np.abs(lat)):.2f} m, p95 {np.percentile(np.abs(lat), 95):.2f} m, "
        f"max {np.abs(lat).max():.2f} m, mean signed {lat.mean():+.2f} m")
    if np.percentile(np.abs(lat), 95) > 10:
        fails.append("GPS and OSM centrelines disagree by > 10 m (p95)")

    # -- bounding box (ortho and heightfield share it)
    lo = C0.min(0) - MARGIN - 20
    hi = C0.max(0) + MARGIN + 20
    box = (math.floor(lo[0] / 10) * 10, math.floor(lo[1] / 10) * 10, math.ceil(hi[0] / 10) * 10,
           math.ceil(hi[1] / 10) * 10)
    box = tuple(float(v) for v in box)
    log("ENU box", box)

    img, W, H = fetch_ortho(box)
    ortho = Ortho(img, box)
    log(f"ortho {W}x{H} px, {(box[2] - box[0]) / W:.3f} x {(box[3] - box[1]) / H:.3f} m/px")

    # -- edges, iterate twice (detect, recentre, detect again on the recentred line)
    C = C0
    edge_fallback = False
    for it in range(2):
        half, stats, raw_ok = detect_edges(C, ortho)
        log(f"edges pass {it + 1}:", {k: round(v, 3) if isinstance(v, float) else v for k, v in stats.items()})
        if not np.isfinite(half).all():
            edge_fallback = True
            log("EDGE DETECTION FAILED broadly: falling back to a constant", HALF_FALLBACK, "m half-width")
            half = np.full((len(C), 2), HALF_FALLBACK)
            break
        nl = left_normals(C)
        Lp = C + half[:, :1] * nl
        Rp = C - half[:, 1:] * nl
        mid = 0.5 * (Lp + Rp)
        # recentre gently: the midpoint shift is smoothed along s so the centreline stays fair
        shift = ((mid - C) * nl).sum(1)
        shift = gaussian_filter1d(shift, 10, mode="wrap")
        Cn = C + shift[:, None] * nl
        C, _ = resample_closed(Cn[::4], smooth=len(Cn[::4]) * 0.1 ** 2)
        log(f"  recentre shift: mean {shift.mean():+.2f} m, max |{np.abs(shift).max():.2f}| m")
    width_full = None
    if not edge_fallback:
        half, stats, raw_ok = detect_edges(C, ortho)
        if not np.isfinite(half).all():
            edge_fallback = True
            half = np.full((len(C), 2), HALF_FALLBACK)
        else:
            width_full = half.sum(1)
    hw = 0.5 * half.sum(1) if not edge_fallback else np.full(len(C), HALF_FALLBACK)

    # -- station 0 at start/finish, exact 1 m resample
    s0, _ = project(C, G[:1])
    s0 = float(s0[0])
    Lc = len(C)
    idx_f = np.arange(Lc)
    Cr = np.c_[np.interp((s0 + idx_f) % Lc, idx_f, C[:, 0], period=Lc),
               np.interp((s0 + idx_f) % Lc, idx_f, C[:, 1], period=Lc)]
    hw = np.interp((s0 + idx_f) % Lc, idx_f, hw, period=Lc)
    C, L = resample_closed(Cr, smooth=0.0)
    n = len(C)
    hw = np.interp(np.arange(n) * Lc / n, idx_f, hw, period=Lc)
    hw = np.clip(hw, HALF_MIN, HALF_MAX)
    log(f"final loop: n={n}, spline length {L:.2f} m, spacing {L / n:.4f} m")
    nl = left_normals(C)
    Lp = C + hw[:, None] * nl
    Rp = C - hw[:, None] * nl

    # -- elevation
    dem = Dem(box)
    dem_s = Dem(box, sigma=0.7)  # light smoothing for the road surface (lidar noise, paint, cars)
    z0 = float(dem(C[:1, 0], C[:1, 1])[0])
    fr = np.array(FRACTIONS)
    # fraction -1 = left edge = centre + hw * left normal
    PX = C[:, 0:1] - (fr[None, :] * hw[:, None]) * nl[:, 0:1]
    PY = C[:, 1:2] - (fr[None, :] * hw[:, None]) * nl[:, 1:2]
    prof = dem_s(PX, PY) - z0
    prof = gaussian_filter1d(prof, 1.5, axis=0, mode="wrap")
    zc = prof[:, 3]
    zl, zr = prof[:, 0], prof[:, -1]

    # heightfield
    nx = int(round((box[2] - box[0]) / HF_DX)) + 1
    ny = int(round((box[3] - box[1]) / HF_DX)) + 1
    gx, gy = np.meshgrid(box[0] + np.arange(nx) * HF_DX, box[1] + np.arange(ny) * HF_DX)
    hf = (dem(gx, gy) - z0).astype("<f4")

    # -- corners from curvature peaks, seeded from the logger frame
    Gs, _ = project(C, G)  # logger index -> new station (fractional)
    Gs_u = np.unwrap(Gs * 2 * np.pi / n) * n / (2 * np.pi)
    Gs_u -= Gs_u[0] - Gs[0]
    kap = curvature(C, sigma=6)
    corners = []
    for turn, name, s_laps, sgn in TURNS:
        guess = np.interp(s_laps, np.arange(len(G)), Gs_u) % n
        win = (np.arange(n) - guess + n / 2) % n - n / 2
        m = np.abs(win) <= 45
        cand = np.where(m, sgn * kap, -np.inf)
        i = int(np.argmax(cand))
        if sgn * kap[i] <= 0:
            fails.append(f"corner {turn}: no curvature peak of the right sign near s={guess:.0f}")
        corners.append({"name": name or turn, "turn": turn, "s": int(i), "radius_m": round(float(1 / abs(kap[i])), 1),
                        "dir": "left" if sgn > 0 else "right"})
    t6 = next(c["s"] for c in corners if c["turn"] == "T6")
    t7 = next(c["s"] for c in corners if c["turn"] == "T7")
    corners.append({"name": "Rahal Straight", "turn": None, "s": int((t6 + t7) // 2), "radius_m": None, "dir": None})
    corners.sort(key=lambda c: c["s"])

    # -- validation
    log("\n================ VALIDATION ================")
    def check(label, ok, msg):
        log(f"[{'ok' if ok else 'FAIL'}] {label}: {msg}")
        if not ok:
            fails.append(label)

    check("loop length", 3480 <= n <= 3680, f"{n} m (official 3602)")
    zr_ = float(zc.max() - zc.min())
    check("elevation range", 45 <= zr_ <= 65, f"{zr_:.1f} m (centre z {zc.min():.1f}..{zc.max():.1f}, z0 {z0:.2f} NAVD88)")
    d0 = float(np.linalg.norm(C[0] - G[0]))
    check("start/finish", d0 <= 15, f"station 0 is {d0:.2f} m from centreline.npy[0]")
    gs_new, glat = project(C, G)
    adv = np.angle(np.exp(1j * 2 * np.pi * np.diff(gs_new) / n)) * n / (2 * np.pi)
    check("direction", (adv > 0).mean() > 0.98, f"{(adv > 0).mean() * 100:.1f}% of GPS steps advance s")
    area = 0.5 * np.sum(C[:, 0] * np.roll(C[:, 1], -1) - np.roll(C[:, 0], -1) * C[:, 1])
    check("ccw", area > 0, f"signed area {area:.0f} m^2 ({'ccw' if area > 0 else 'cw'})")
    check("GPS agreement", np.percentile(np.abs(glat), 95) < 8,
          f"GPS line vs final centre: median |lat| {np.median(np.abs(glat)):.2f} m, p95 {np.percentile(np.abs(glat), 95):.2f} m")
    lat_d = np.diff(fr) * hw[:, None]
    cs = np.abs(np.diff(prof, axis=1)) / lat_d
    csm = cs.max(1)
    check("cross slope", csm.max() < CROSS_HARD,
          f"max {csm.max() * 100:.1f}% at s={int(csm.argmax())}; {np.sum(csm > CROSS_SOFT)} stations over "
          f"{CROSS_SOFT * 100:.0f}% (p99 {np.percentile(csm, 99) * 100:.1f}%)")
    signed = np.diff(prof, axis=1) / lat_d  # + = right side higher
    steep = np.where(csm > CROSS_SOFT)[0]
    if len(steep):
        spread = np.ptp(signed[steep][:, 1:5], axis=1)  # inner four segments; edge segments may meet kerbs/gutters
        check("steep banking is planar", spread.max() < CROSS_PLANAR,
              f"max spread of segment slopes over steep stations {spread.max() * 100:.1f} points")
        runs = np.split(steep, np.where(np.diff(steep) > 3)[0] + 1)
        for r in runs:
            near = min(corners, key=lambda c: min(abs(c["s"] - r[0]), abs(c["s"] - r[-1])))
            i = r[csm[r].argmax()]
            bank = "toward inside" if np.sign(-signed[i].mean()) == -np.sign(kap[i]) or abs(kap[i]) < 2e-3 else "OFF-CAMBER"
            log(f"     banking >12%: s={r[0]}..{r[-1]} (near {near['turn'] or near['name']}), max {csm[i] * 100:.1f}%, "
                f"{'right' if signed[i].mean() > 0 else 'left'} side higher, curvature {kap[i] * 1000:+.1f}/km -> {bank}")
    long_g = np.abs(np.diff(np.r_[zc, zc[:1]]))
    log(f"     longitudinal grade: max {long_g.max() * 100:.1f}% at s={int(long_g.argmax())}")
    allarr = [C, Lp, Rp, prof, hf, hw]
    check("no NaN", all(np.isfinite(a).all() for a in allarr), "centre/edges/profile/heightfield finite")
    if width_full is not None:
        log(f"     paved width (detected, before clamp/symmetrise): median {np.median(width_full):.1f} m, "
            f"p5 {np.percentile(width_full, 5):.1f}, p95 {np.percentile(width_full, 95):.1f}")
    log(f"     half-width used: min {hw.min():.2f} median {np.median(hw):.2f} max {hw.max():.2f} m; "
        f"clamped low {np.mean(hw <= HALF_MIN + 1e-6) * 100:.1f}%, high {np.mean(hw >= HALF_MAX - 1e-6) * 100:.1f}%")
    log(f"     edge detection raw success: left {raw_ok[:, 0].mean() * 100:.1f}%, right {raw_ok[:, 1].mean() * 100:.1f}%"
        + ("  (FALLBACK constant width)" if edge_fallback else ""))
    for c in corners:
        log(f"     {c['turn'] or '':4s} {c['name']:18s} s={c['s']:5d}  R={c['radius_m']}")

    # -- write
    r3 = lambda a: np.round(a, 3).tolist()  # noqa: E731
    track = {
        "name": "WeatherTech Raceway Laguna Seca",
        "origin": {"lat": LAT0, "lon": LON0},
        "z0_navd88": round(z0, 3),
        "direction": "ccw" if area > 0 else "cw",
        "spacing_m": 1.0,
        "n": n,
        "length_m": float(n),
        "center": r3(np.c_[C, zc]),
        "left": r3(np.c_[Lp, zl]),
        "right": r3(np.c_[Rp, zr]),
        "profile": {"fractions": FRACTIONS, "z": r3(prof)},
        "start_finish": {"index": 0},
        "corners": corners,
        "heightfield": {"file": "heightfield.bin", "x0": box[0], "y0": box[1], "dx": HF_DX, "nx": nx, "ny": ny},
        "ortho": {"file": "ortho.jpg", "x0": box[0], "y0": box[1], "x1": box[2], "y1": box[3], "width_px": W,
                  "height_px": H},
        "sources": "OpenStreetMap (ODbL), USGS 3DEP 1 m DEM 2017 (public domain), USGS NAIP imagery (public domain)",
        "notes": {
            "edges": "constant 6.5 m half-width fallback" if edge_fallback else
            "edges from NAIP asphalt extent, robust-smoothed, symmetrised about the recentred centre",
            "spline_length_m": round(L, 2),
        },
    }
    np.savez(os.path.join(CACHE, "track_arrays.npz"), C=C, Lp=Lp, Rp=Rp, hw=hw, zc=zc, prof=prof, kap=kap)
    if fails:
        preview(img, box, C, Lp, Rp, zc, corners, os.path.join(CACHE, "preview_failed.png"))
        log("\nVALIDATION FAILED:", fails)
        sys.exit(1)
    with open(os.path.join(OUT, "track.json"), "w") as fh:
        json.dump(track, fh, separators=(",", ":"))
    hf.tofile(os.path.join(OUT, "heightfield.bin"))
    from PIL import Image

    Image.fromarray(grade_ortho(img)).save(os.path.join(OUT, "ortho.jpg"), quality=85, optimize=True)
    preview(img, box, C, Lp, Rp, zc, corners, os.path.join(PREVIEWS, "preview.png"))
    for f in ("track.json", "heightfield.bin", "ortho.jpg"):
        log(f"wrote {f}: {os.path.getsize(os.path.join(OUT, f)) / 1e6:.2f} MB")


def preview(img, box, C, Lp, Rp, zc, corners, path):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure(figsize=(14, 18))
    ax = fig.add_axes([0.04, 0.27, 0.92, 0.71])
    ax.imshow(img, extent=(box[0], box[2], box[1], box[3]), origin="upper")
    loop = lambda a: np.r_[a, a[:1]]  # noqa: E731
    ax.plot(loop(Lp)[:, 0], loop(Lp)[:, 1], "-", color="#ff3b30", lw=0.7, label="left edge")
    ax.plot(loop(Rp)[:, 0], loop(Rp)[:, 1], "-", color="#0a84ff", lw=0.7, label="right edge")
    ax.plot(loop(C)[:, 0], loop(C)[:, 1], "--", color="yellow", lw=0.5, label="centre")
    ax.plot(*C[0], "o", color="white", ms=7, mec="black")
    ax.annotate("S/F", C[0], xytext=(8, 8), textcoords="offset points", color="white", weight="bold")
    for c in corners:
        p = C[c["s"]]
        ax.annotate(f"{c['turn'] or ''} {c['name'] if c['name'] != c['turn'] else ''}".strip(), p, xytext=(10, -12),
                    textcoords="offset points", color="white", fontsize=8,
                    bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.6, lw=0))
    lo, hi = C.min(0) - 60, C.max(0) + 60
    ax.set_xlim(lo[0], hi[0])
    ax.set_ylim(lo[1], hi[1])
    ax.set_aspect("equal")
    ax.legend(loc="lower right")
    ax.set_title("Laguna Seca: centre and edges on NAIP ortho (ENU m)")
    bx = fig.add_axes([0.06, 0.04, 0.9, 0.18])
    s = np.arange(len(zc))
    bx.plot(s, zc, color="k", lw=1)
    for c in corners:
        bx.axvline(c["s"], color="0.7", lw=0.5)
        bx.text(c["s"], zc.max() + 1, c["turn"] or "Rahal", fontsize=7, ha="center")
    bx.set_xlabel("s (m from start/finish)")
    bx.set_ylabel("z (m, rel. start/finish)")
    bx.set_xlim(0, len(zc))
    bx.grid(alpha=0.3)
    fig.savefig(path, dpi=110)
    plt.close(fig)


if __name__ == "__main__":
    main()
