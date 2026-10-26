"""The owner's traced edges (the owner-traced edge evidence, SKILL 1.5 / 1.9; Buttonwillow, 21 Oct 2026): read the red
(track edges) and green (extra lines, e.g. the end lines of a legitimate paved runoff) strokes the owner drew on a capwin
frame of the 2026 captures, and write them as world points per station of a package's centreline.

    uv run --python 3.12 --with numpy,pillow python -I tools/track/compare/owner_edges.py --track buttonwillow \
        --png tools/track/compare/buttonwillow/owner/owner_t2_edges_marked.png --s 583 --half 70 --mpp 0.1 \
        --pkg public/tracks/buttonwillow --out tools/track/tracks/buttonwillow/owner/t2_edges.json

Sonoma round 14B (23 Oct 2026): --frames <frames.json> --window <name> takes the window's capwin geometry from the
drawing page's frames file (centre ENU, px, mpp; the windows were cut from another package than the one projected on),
and --strokes <strokes.json> keeps only the stroke-coloured pixels within 3 px of the strokes the owner drew in that
window (the page's own vectors), so red or green objects in the imagery (a red roof, a red trailer) are not read as his
lines.

--by-stroke (Sonoma round 14B, part 1b): the strokes are read from their vectors (strokes.json), not from the PNG (the
round-14B marked windows carry the red fit under his red): each red stroke is sampled every 0.25 m, and a sample whose
stroke runs at more than --across-deg (35) to the course at its nearest station is a line ACROSS (a mouth's boundary),
kept apart in `across_enu` (one entry per run of such samples, with its stroke index) and left out of the edge points.

The frame is the one capwin draws for the same --s / --half / --mpp on the same package (north up, the window centred on
the centreline point at s): pixel (i, j) covers world x = cx - half + (i + 0.5) mpp, y = cy + half - (j + 0.5) mpp. Red
pixels (the edges) are projected onto the centreline; per station and side (lateral sign) the median lateral offset gives
one point [x, y, s_m] in world ENU (s_m: the station's track metres on that package), which stays valid when the centre moves (spline.owner_edges re-projects it on
every refit). Green pixels are written as world points (thinned to one per 1 m cell). The PNG is reference imagery:
local only, never committed; the JSON is the evidence and is tracked.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image


def masks(img):
    a = np.asarray(img.convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r > 170) & (g < 110) & (b < 110) & (r - g > 90)
    green = (g > 150) & (r < 140) & (b < 140) & (g - r > 60)
    return red, green


def frame_xy(mask, cx, cy, half, mpp):
    jj, ii = np.nonzero(mask)
    return np.c_[cx - half + (ii + 0.5) * mpp, cy + half - (jj + 0.5) * mpp]


def per_station(P, C, NL, sp=1.0):
    """median lateral offset of the points per centreline station and side; returns {side: [[x, y, s_m], ...]} with s_m the
    station's track metres on the package (rounded)"""
    from scipy.spatial import cKDTree
    _, k = cKDTree(C).query(P)
    lat = ((P - C[k]) * NL[k]).sum(1)
    out = {'left': [], 'right': []}
    for side, m in (('left', lat > 0), ('right', lat < 0)):
        for kk in np.unique(k[m]):
            sel = m & (k == kk)
            o = float(np.median(lat[sel]))
            q = C[kk] + NL[kk] * o
            out[side].append([float(q[0]), float(q[1]), int(round(kk * sp))])
    return out


def stroke_band(strokes, size, colour, width=7):
    """pixels within (width - 1) / 2 px of the strokes of one colour (the drawing page's vectors, image pixels)"""
    from PIL import ImageDraw
    im = Image.new('L', size, 0); d = ImageDraw.Draw(im)
    for st in strokes:
        if st.get('c') == colour:
            P = [tuple(p) for p in st['pts']]
            d.line(P if len(P) > 1 else P * 2, fill=255, width=width)
    return np.asarray(im) > 0


def run_strokes(strokes, s, half, mpp, track, centre, across_deg=35.0, step=0.25, origin=0.5):
    """--by-stroke: the edge points and the across lines from the stroke vectors (image pixels of the window).
    origin: the vector's offset added before scaling (0.5, the default: the pixel-index reading the PNG path uses;
    0.0 = --vector-origin continuous: the drawing page's canvas coordinates, where image pixel i spans [i, i + 1) and
    the window's left edge is 0, as capwin draws and edge_mark_transfer.cjs projects; Mid-Ohio round 3)"""
    C = np.array(track['center'])[:, :2]
    sp = track['spacing_m']
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True)
    NL = np.c_[-t[:, 1], t[:, 0]]
    cx, cy = centre
    from scipy.spatial import cKDTree
    kd = cKDTree(C)
    edge, G, across = [], [], []
    cosmin = np.cos(np.radians(across_deg))
    for si, st in enumerate(strokes):
        P = np.array(st['pts'], float)
        W = np.c_[cx - half + (P[:, 0] + origin) * mpp, cy + half - (P[:, 1] + origin) * mpp]
        if len(W) < 2:
            continue
        seg = np.linalg.norm(np.diff(W, axis=0), axis=1); u = np.r_[0, np.cumsum(seg)]
        if u[-1] <= 0:
            continue
        uu = np.arange(0, u[-1] + 1e-9, step)
        Q = np.c_[np.interp(uu, u, W[:, 0]), np.interp(uu, u, W[:, 1])]
        if st.get('c') == 'green':
            G.extend(Q.tolist()); continue
        d = np.gradient(Q, axis=0); d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-9)
        _, k = kd.query(Q)
        along = np.abs((d * t[k]).sum(1)) >= cosmin
        edge.extend(Q[along].tolist())
        # runs of across samples, one line each
        idx = np.flatnonzero(~along)
        if len(idx):
            br = np.flatnonzero(np.diff(idx) > 1); a0 = np.r_[0, br + 1]; a1 = np.r_[br, len(idx) - 1]
            for a, b in zip(a0, a1):
                seg_ = Q[idx[a]:idx[b] + 1]
                if len(seg_) * step >= 1.0:
                    across.append({'stroke': si, 'pts_enu': [[round(float(x), 3), round(float(y), 3)] for x, y in seg_[::4]] +
                                   [[round(float(seg_[-1][0]), 3), round(float(seg_[-1][1]), 3)]]})
    E = np.array(edge) if edge else np.zeros((0, 2))
    out = per_station(E, C, NL, sp) if len(E) else {'left': [], 'right': []}
    G = np.array(G) if G else np.zeros((0, 2))
    if len(G):
        cell = np.floor(G / 1.0).astype(int); _, idx = np.unique(cell, axis=0, return_index=True); G = G[np.sort(idx)]
    return {'frame': {'s': float(s), 'half': float(half), 'mpp': float(mpp), 'centre_enu': [round(float(cx), 3), round(float(cy), 3)],
                      'image_px': [int(round(2 * half / mpp))] * 2, 'by_stroke': True, 'across_deg': across_deg,
                      **({'vector_origin': 'continuous'} if origin == 0.0 else {})},
            'left_enu_xys': out['left'], 'right_enu_xys': out['right'],
            'green_enu_xy': [[round(float(x), 3), round(float(y), 3)] for x, y in G], 'across_enu': across}


def run(png, s, half, mpp, track, centre=None, strokes=None):
    C = np.array(track['center'])[:, :2]
    sp = track['spacing_m']
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True)
    NL = np.c_[-t[:, 1], t[:, 0]]
    cx, cy = C[int(round(s / sp)) % len(C)] if centre is None else centre
    img = Image.open(png)
    red, green = masks(img)
    if strokes is not None:
        red &= stroke_band(strokes, img.size, 'red'); green &= stroke_band(strokes, img.size, 'green')
    edges = per_station(frame_xy(red, cx, cy, half, mpp), C, NL, sp)
    G = frame_xy(green, cx, cy, half, mpp)
    if len(G):
        cell = np.floor(G / 1.0).astype(int)
        _, idx = np.unique(cell, axis=0, return_index=True)
        G = G[np.sort(idx)]
    return {'frame': {'s': float(s), 'half': float(half), 'mpp': float(mpp), 'centre_enu': [round(float(cx), 3), round(float(cy), 3)],
                      'image_px': [img.size[0], img.size[1]]},
            'left_enu_xys': edges['left'], 'right_enu_xys': edges['right'],
            'green_enu_xy': [[round(float(x), 3), round(float(y), 3)] for x, y in G]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True)
    ap.add_argument('--png', help='the marked window (not with --by-stroke)')
    ap.add_argument('--by-stroke', action='store_true', help='read the strokes from --strokes vectors, not from the PNG')
    ap.add_argument('--across-deg', type=float, default=35.0)
    ap.add_argument('--vector-origin', choices=['pixel', 'continuous'], default='pixel',
                    help="--by-stroke: 'pixel' (default, +0.5 px as the PNG path) or 'continuous' (the drawing page's "
                         "canvas coordinates, no half-pixel offset: capwin / edge_mark_transfer.cjs; Mid-Ohio round 3)")
    ap.add_argument('--s', type=float)
    ap.add_argument('--frames', help="the drawing page's frames.json (Sonoma round 14B): the window's centre, px and mpp")
    ap.add_argument('--window', help='the window name in --frames / --strokes')
    ap.add_argument('--strokes', help="the drawing page's strokes.json: keep only stroke-coloured pixels on his strokes")
    ap.add_argument('--half', type=float, default=45.0)
    ap.add_argument('--mpp', type=float, default=0.12)
    ap.add_argument('--pkg', required=True)
    ap.add_argument('--src', default='')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    track = json.load(open(os.path.join(a.pkg, 'track.json')))
    centre = None
    if a.frames:
        fr = json.load(open(a.frames))[a.window]
        a.mpp = float(fr['mpp']); a.s = float(fr['s'])
        if 'centre' in fr:
            centre = tuple(fr['centre']); a.half = fr['px'] * a.mpp / 2
        else:
            # the outline windows' own record (build_edge_review.py windows.json / owner_review frames.json: center_enu,
            # half; Mid-Ohio round 3)
            centre = tuple(fr['center_enu']); a.half = float(fr['half'])
    strokes = json.load(open(a.strokes))[a.window]['strokes'] if a.strokes else None
    d = {'track': a.track, 'src': a.src or f'owner drawing {os.path.basename(a.png or a.window)} (capwin --s {a.s} --half {a.half} --mpp {a.mpp})'}
    if a.by_stroke:
        d.update(run_strokes(strokes, a.s, a.half, a.mpp, track, centre, a.across_deg,
                             origin=0.0 if a.vector_origin == 'continuous' else 0.5))
        print(f"{a.window}: {len(d['across_enu'])} across lines: " + ', '.join(f"stroke {x['stroke']} {len(x['pts_enu'])} pts" for x in d['across_enu']))
    else:
        d.update(run(a.png, a.s, a.half, a.mpp, track, centre, strokes))
    json.dump(d, open(a.out, 'w'), indent=1)
    print(f"{a.out}: left {len(d['left_enu_xys'])} / right {len(d['right_enu_xys'])} stations, green {len(d['green_enu_xy'])} points")


if __name__ == '__main__':
    main()
