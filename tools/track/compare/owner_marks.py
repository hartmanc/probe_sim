"""Owner-drawn marks on a capwin frame (the owner-traced evidence, SKILL 1.5 / 1.9; Sonoma 8a, 21 Oct 2026): read the
RED strokes (wall / barrier lines) and the GREEN strokes (a structure's footprint outline) the owner drew on a capwin
frame of the 2026 captures and write them as world measurements: each red stroke as a fitted line with ENU + lat/lon
endpoints, length, bearing and its station / lateral range on the package's centreline; each green stroke as an
oriented rectangle (centre, size, heading, corners).

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/owner_marks.py --track sonoma \
        --png tools/track/compare/sonoma/owner_drive_r2/owner_61_8a_tower_marked.png --s 2600 --half 90 --mpp 0.12 \
        --pkg public/tracks/sonoma --out tools/track/tracks/sonoma/owner/t8a_station.json [--poly /tmp/x.json]

The frame is the one capwin draws for the same --s / --half / --mpp on the same package (north up, the window centred
on the centreline point at s): pixel (i, j) covers world x = cx - half + (i + 0.5) mpp, y = cy + half - (j + 0.5) mpp
(the same mapping as owner_edges.py). Strokes are separated as 8-connected components after a 2 px closing (the drawn
lines are 2-4 px wide and anti-aliased); components under 40 px are dropped. A red component becomes a line by PCA, its
endpoints the extreme projections along the principal axis; a green component becomes the oriented bounding rectangle
of its pixels in their PCA frame. Lat/lon uses the pipeline's equirectangular frame (geo.enu) about the package origin.
--poly writes the digitised lines as lat/lon polylines for capwin --poly (the check render). The PNG is reference
imagery: local only, never committed; the JSON is the evidence and is tracked.
"""
import argparse
import json
import math
import os

import numpy as np
from PIL import Image
from scipy import ndimage


def masks(img, raw=None):
    """red / green stroke masks; with the clean capwin render of the same frame (raw), only pixels that differ from it
    count, so red or green objects in the imagery (a trailer stripe, a lawn) are not read as strokes"""
    a = np.asarray(img.convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 170) & (g < 110) & (b < 110) & (r - g > 90)
    green = (g > 150) & (r < 140) & (b < 140) & (g - r > 60)
    if raw is not None:
        d = np.abs(a - np.asarray(raw.convert('RGB')).astype(int)).sum(-1) > 30
        red, green = red & d, green & d
    return red, green


def components(mask, min_px=40):
    closed = ndimage.binary_closing(mask, structure=np.ones((3, 3), bool), iterations=1) | mask
    lab, n = ndimage.label(closed, structure=np.ones((3, 3), int))
    out = []
    for k in range(1, n + 1):
        sel = (lab == k) & mask
        if sel.sum() >= min_px:
            out.append(sel)
    return out


def frame_xy(mask, cx, cy, half, mpp):
    jj, ii = np.nonzero(mask)
    return np.c_[cx - half + (ii + 0.5) * mpp, cy + half - (jj + 0.5) * mpp]


def pca(P):
    c = P.mean(0)
    u, s, vt = np.linalg.svd(P - c, full_matrices=False)
    d = vt[0]
    if d[1] < 0 or (d[1] == 0 and d[0] < 0):  # a stable sign: point the axis north (or east)
        d = -d
    return c, d, np.array([-d[1], d[0]])


def bearing(d):
    return (math.degrees(math.atan2(d[0], d[1])) + 360.0) % 360.0  # from north, clockwise


class Track:
    def __init__(self, pkg):
        T = json.load(open(os.path.join(pkg, 'track.json')))
        self.C = np.array(T['center'])[:, :2]
        self.sp = T['spacing_m']
        t = np.roll(self.C, -1, 0) - np.roll(self.C, 1, 0)
        t /= np.linalg.norm(t, axis=1, keepdims=True)
        self.NL = np.c_[-t[:, 1], t[:, 0]]
        self.lat0, self.lon0 = T['origin']['lat'], T['origin']['lon']
        self.R = 6378137.0
        self.cosl = math.cos(math.radians(self.lat0))
        from scipy.spatial import cKDTree
        self.tree = cKDTree(self.C)

    def latlon(self, x, y):
        return [round(self.lat0 + math.degrees(y / self.R), 7), round(self.lon0 + math.degrees(x / (self.R * self.cosl)), 7)]

    def station(self, p):
        """nearest station: (s_m on the package, lateral offset m, + = left)"""
        _, k = self.tree.query(p)
        lat = float(((p - self.C[k]) * self.NL[k]).sum())
        return int(round(k * self.sp)), round(lat, 2)

    def passes(self, p, reach=80.0):
        """every pass of the lap within reach of p: the local minima of the distance to the centreline, each as
        {s_m, lateral_m (+ = left), dist_m}; a wall between two parts of the lap is seen from both"""
        d = np.linalg.norm(self.C - p, axis=1)
        out = []
        for k in range(len(d)):
            if d[k] < reach and d[k] < d[k - 1] and d[k] <= d[(k + 1) % len(d)]:
                if out and abs(out[-1]['s_m'] - k * self.sp) < 30:
                    continue
                out.append({'s_m': int(round(k * self.sp)), 'lateral_m': round(float(((p - self.C[k]) * self.NL[k]).sum()), 2),
                            'dist_m': round(float(d[k]), 2)})
        return out


def line_record(P, trk, px):
    c, d, n = pca(P)
    t = (P - c) @ d
    a, b = c + d * t.min(), c + d * t.max()
    rms = float(np.sqrt((((P - c) @ n) ** 2).mean()))
    sa, la = trk.station(a)
    sb, lb = trk.station(b)
    if sa > sb:
        a, b, sa, sb, la, lb = b, a, sb, sa, lb, la
    return {'a_enu': [round(float(a[0]), 3), round(float(a[1]), 3)], 'b_enu': [round(float(b[0]), 3), round(float(b[1]), 3)],
            'a_latlon': trk.latlon(*a), 'b_latlon': trk.latlon(*b), 'a_px': px(*a), 'b_px': px(*b),
            'length_m': round(float(t.max() - t.min()), 2), 'bearing_deg': round(bearing(d), 1), 'fit_rms_m': round(rms, 3),
            'px': int(len(P)), 'a_station': {'s_m': sa, 'lateral_m': la}, 'b_station': {'s_m': sb, 'lateral_m': lb},
            'a_passes': trk.passes(a), 'b_passes': trk.passes(b)}


def box_record(P, trk, px):
    c, d, n = pca(P)
    u, v = (P - c) @ d, (P - c) @ n
    corners = [c + d * uu + n * vv for uu, vv in ((u.min(), v.min()), (u.max(), v.min()), (u.max(), v.max()), (u.min(), v.max()))]
    centre = c + d * (u.min() + u.max()) / 2 + n * (v.min() + v.max()) / 2
    s_m, lat = trk.station(centre)
    return {'centre_enu': [round(float(centre[0]), 3), round(float(centre[1]), 3)], 'centre_latlon': trk.latlon(*centre),
            'centre_px': px(*centre),
            'size_m': [round(float(u.max() - u.min()), 2), round(float(v.max() - v.min()), 2)],
            'heading_deg': round(bearing(d), 1), 'corners_enu': [[round(float(q[0]), 3), round(float(q[1]), 3)] for q in corners],
            'corners_latlon': [trk.latlon(*q) for q in corners], 'px': int(len(P)), 'station': {'s_m': s_m, 'lateral_m': lat},
            'passes': trk.passes(centre)}


def run(png, s, half, mpp, pkg, raw=None):
    trk = Track(pkg)
    cx, cy = trk.C[int(round(s / trk.sp)) % len(trk.C)]
    img = Image.open(png)
    red, green = masks(img, Image.open(raw) if raw else None)
    px = lambda x, y: [round(float((x - (cx - half)) / mpp), 1), round(float(((cy + half) - y) / mpp), 1)]  # noqa: E731
    lines = [line_record(frame_xy(m, cx, cy, half, mpp), trk, px) for m in components(red)]
    boxes = [box_record(frame_xy(m, cx, cy, half, mpp), trk, px) for m in components(green)]
    lines.sort(key=lambda r: r['a_station']['s_m'])
    for bx in boxes:  # which line passes nearest the box centre, and how far
        q = np.array(bx['centre_enu'])
        best = None
        for i, ln in enumerate(lines):
            a, b = np.array(ln['a_enu']), np.array(ln['b_enu'])
            d = b - a
            t = float(np.clip(((q - a) @ d) / (d @ d), 0, 1))
            dist = float(np.linalg.norm(q - (a + t * d)))
            if best is None or dist < best[1]:
                best = (i, dist)
        bx['nearest_line'] = {'index': best[0], 'dist_m': round(best[1], 2)} if best else None
    return {'frame': {'s': float(s), 'half': float(half), 'mpp': float(mpp), 'centre_enu': [round(float(cx), 3), round(float(cy), 3)],
                      'image_px': [img.size[0], img.size[1]]},
            'red_lines': lines, 'green_boxes': boxes}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True)
    ap.add_argument('--png', required=True)
    ap.add_argument('--s', type=float, required=True)
    ap.add_argument('--half', type=float, default=45.0)
    ap.add_argument('--mpp', type=float, default=0.12)
    ap.add_argument('--pkg', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--poly', help='also write the lines and box outlines as lat/lon polylines for capwin --poly')
    ap.add_argument('--raw', help='the clean capwin --raw render of the same frame: only pixels that differ from it count as strokes')
    a = ap.parse_args()
    rec = run(a.png, a.s, a.half, a.mpp, a.pkg, a.raw)
    rec['track'] = a.track
    rec['png'] = os.path.basename(a.png)
    rec['stroke_filter'] = 'diff against the clean capwin render of the frame' if a.raw else 'colour only'
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    json.dump(rec, open(a.out, 'w'), indent=1)
    if a.poly:
        polys = [[ln['a_latlon'], ln['b_latlon']] for ln in rec['red_lines']]
        polys += [bx['corners_latlon'] + [bx['corners_latlon'][0]] for bx in rec['green_boxes']]
        json.dump(polys, open(a.poly, 'w'))
    for i, ln in enumerate(rec['red_lines']):
        print(f"line {i}: {ln['length_m']} m, bearing {ln['bearing_deg']}, rms {ln['fit_rms_m']} m, {ln['px']} px; "
              f"s {ln['a_station']['s_m']} ({ln['a_station']['lateral_m']:+} m) -> s {ln['b_station']['s_m']} ({ln['b_station']['lateral_m']:+} m)")
    for i, bx in enumerate(rec['green_boxes']):
        print(f"box {i}: {bx['size_m'][0]} x {bx['size_m'][1]} m, heading {bx['heading_deg']}, centre {bx['centre_enu']} "
              f"lat/lon {bx['centre_latlon']}, s {bx['station']['s_m']} ({bx['station']['lateral_m']:+} m), nearest line {bx['nearest_line']}")
    print(a.out)


if __name__ == '__main__':
    main()
