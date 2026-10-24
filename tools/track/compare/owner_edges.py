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
    ap.add_argument('--png', required=True)
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
        centre = tuple(fr['centre']); a.mpp = float(fr['mpp']); a.half = fr['px'] * a.mpp / 2; a.s = float(fr['s'])
    strokes = json.load(open(a.strokes))[a.window]['strokes'] if a.strokes else None
    d = {'track': a.track, 'src': a.src or f'owner drawing {os.path.basename(a.png)} (capwin --s {a.s} --half {a.half} --mpp {a.mpp})'}
    d.update(run(a.png, a.s, a.half, a.mpp, track, centre, strokes))
    json.dump(d, open(a.out, 'w'), indent=1)
    print(f"{a.out}: left {len(d['left_enu_xys'])} / right {len(d['right_enu_xys'])} stations, green {len(d['green_enu_xy'])} points")


if __name__ == '__main__':
    main()
