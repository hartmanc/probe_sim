"""A window of the clean z20 captures (reference only, never a texture) around a station or a world point, with the
package's track edges, station ticks and scenery drawn over it: the evidence viewer of the scenery round (20 Oct 2026).

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/capwin.py --track sonoma \
        --pkg tools/track/out/sonoma_r3 --s 2160 [--half 50] [--mpp 0.12] [--raw] --out /tmp/x.png

North is up. A world point p is drawn where the capture shows it (p + the capture's shift, captures.capture_list).
Overlay: track edges (white), ticks every 10 m along the left edge with the track s in metres every 50 m (yellow),
barriers (concrete white, pitwall orange, tyres red, armco blue, fence orange dashed), kerb strips (magenta),
pit lane / paved zones (cyan), cone lines (orange dots), landmarks (yellow squares), terraces (grey).
Round 14B (owner, 23 Oct 2026: "Can you change the course edge splines to the same red and green convention I was
using? The white line is not very high contrast"): --edge-color / --edge-width / --halo draw the track edges in a colour
with a dark halo; --zones-color draws the closed pavement (scenery pit_lane and paved_zones part edges) in that style,
also with --light; --zones-from takes those parts from another package's scenery.json (a stage-1-only package has
none). Defaults: the earlier white 1 px edges, no zones in --light.
Output and captures stay out of git (tools/track/compare imagery is ignored).
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import trackcfg  # noqa: E402
import captures as CAP  # noqa: E402


def mosaic(tiles, mpp, x0, y1, W, H, step):
    """RGB image of the world window [x0, x0 + W*step] x [y1 - H*step, y1], from the capture where each pixel sits most
    central (and unmasked); also the name of the capture used most."""
    gx = x0 + (np.arange(W) + 0.5) * step
    gy = y1 - (np.arange(H) + 0.5) * step
    X, Y = np.meshgrid(gx, gy)
    out = np.zeros((H, W, 3), np.float32)
    best = np.full((H, W), np.inf)
    used = {}
    for t in tiles:
        with Image.open(t['path']) as im_:
            Wt, Ht = im_.size
        px = Wt / 2 + (X + t['dx'] - t['x']) / mpp
        py = Ht / 2 - (Y + t['dy'] - t['y']) / mpp
        inside = (px >= 1) & (px < Wt - 2) & (py >= 1) & (py < Ht - 2)
        if not inside.any():
            continue
        sc = np.abs(px / Wt - 0.5) + np.abs(py / Ht - 0.5)
        take = inside & (sc < best)
        if not take.any():
            continue
        im = np.asarray(Image.open(t['path']).convert('RGB')).astype(np.float32)
        m = t['mask'](Ht, Wt)
        ok = take.copy()
        ok[take] = m[np.round(py[take]).astype(int), np.round(px[take]).astype(int)]
        if not ok.any():
            continue
        v = CAP.bilinear(im, px[ok], py[ok])
        out[ok] = v
        best[ok] = sc[ok]
        used[t['name']] = int(ok.sum())
    return out.clip(0, 255).astype(np.uint8), used


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True)
    ap.add_argument('--pkg', required=True, help='package dir with track.json (and scenery.json for the overlay)')
    ap.add_argument('--s', type=float, help='track s in metres (window centre on the centreline)')
    ap.add_argument('--xy', help='window centre x,y (ENU m)')
    ap.add_argument('--latlon', help='window centre lat,lon')
    ap.add_argument('--half', type=float, default=45.0, help='half-size of the window, m')
    ap.add_argument('--mpp', type=float, default=0.12, help='output m/px')
    ap.add_argument('--raw', action='store_true', help='no overlay (imagery only)')
    ap.add_argument('--light', action='store_true', help='edges and ticks only')
    ap.add_argument('--edge-color', default='255,255,255', help='track edges r,g,b (default white)')
    ap.add_argument('--edge-width', type=int, default=1, help='track edge line width, px')
    ap.add_argument('--halo', type=int, default=0, help='dark halo width added each side of the edge / zone lines, px (0: none)')
    ap.add_argument('--zones-color', help='r,g,b: draw the closed pavement (pit_lane / paved_zones part edges) in this colour, also with --light')
    ap.add_argument('--zones-from', help='package dir whose scenery.json gives the zones (default --pkg)')
    ap.add_argument('--poly', help='json file: list of lat/lon polylines to draw in red (wall_measure.py writes /tmp/wall_measure_last.json)')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    scp = os.path.join(a.pkg, 'scenery.json')
    SC = json.load(open(scp)) if os.path.exists(scp) and not a.raw else None
    C = np.array(T['center'])[:, :2]; L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]
    n, sp = T['n'], T['spacing_m']
    if a.s is not None:
        cx, cy = C[int(round(a.s / sp)) % n]
    elif a.xy:
        cx, cy = map(float, a.xy.split(','))
    else:
        la, lo = map(float, a.latlon.split(','))
        cx, cy = cfg.enu(la, lo)
    tiles = CAP.capture_list(cfg, 'clean')
    Wp = int(2 * a.half / a.mpp)
    img, used = mosaic(tiles, cfg['captures']['mpp'], cx - a.half, cy + a.half, Wp, Wp, a.mpp)
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    px = lambda x, y: ((x - (cx - a.half)) / a.mpp, ((cy + a.half) - y) / a.mpp)  # noqa: E731
    ecol = tuple(int(v) for v in a.edge_color.split(','))

    def stroke(P, col, width):
        """a polyline in `col`, `width` px, over a dark halo (--halo px each side); only the in-window part"""
        P = [q for q in P]
        inw = lambda q: -50 < q[0] < Wp + 50 and -50 < q[1] < Wp + 50  # noqa: E731
        segs = [(P[i], P[i + 1]) for i in range(len(P) - 1) if inw(P[i]) or inw(P[i + 1])]
        if a.halo:
            for p, q in segs:
                d.line([p, q], fill=(15, 15, 15), width=width + 2 * a.halo)
        for p, q in segs:
            d.line([p, q], fill=col, width=width)
    if not a.raw:
        if a.zones_color:
            zc = tuple(int(v) for v in a.zones_color.split(','))
            zp = os.path.join(a.zones_from or a.pkg, 'scenery.json')
            ZS = json.load(open(zp)) if os.path.exists(zp) else {}
            for grp in ('pit_lane', 'paved_zones'):
                for part in (ZS.get(grp) or {}).get('parts', []):
                    for side in ('left', 'right'):
                        stroke([px(p[0], p[1]) for p in part[side]], zc, a.edge_width)
        for E in (L, R):
            pts = [px(*p) for p in E]
            stroke(pts + pts[:1], ecol, a.edge_width)
        tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
        NL = np.c_[-tg[:, 1], tg[:, 0]]
        for i in range(0, n, max(1, int(round(10 / sp)))):
            p = px(*L[i]); q = px(*(L[i] + NL[i] * 1.5))
            if 0 <= p[0] < Wp and 0 <= p[1] < Wp:
                d.line([p, q], fill=(255, 230, 0), width=2)
                s = i * sp
                if abs(s / 50 - round(s / 50)) < 0.11:
                    d.text((q[0] + 2, q[1] - 6), f'{s:.0f}', fill=(255, 255, 0))
        if SC and not a.light:
            col = {'concrete': (255, 255, 255), 'pitwall': (255, 160, 0), 'tyres': (255, 40, 40), 'armco': (90, 140, 255),
                   'fence': (255, 120, 0)}
            for b in SC.get('barriers', []):
                pts = [px(p[0], p[1]) for p in b['pts']]
                d.line(pts, fill=col.get(b['kind'], (255, 0, 255)), width=3 if b['kind'] != 'fence' else 1)
            for grp in ('pit_lane', 'paved_zones'):
                for part in (SC.get(grp) or {}).get('parts', []):
                    for side in ('left', 'right'):
                        d.line([px(p[0], p[1]) for p in part[side]], fill=(0, 230, 230), width=1)
            for cl in (SC.get('cone_lines') or []) + ([SC['pit_exit_cones']] if SC.get('pit_exit_cones') else []):
                for p in cl['pts']:
                    q = px(p[0], p[1]); d.ellipse([q[0] - 2, q[1] - 2, q[0] + 2, q[1] + 2], fill=(255, 130, 0))
            ks = SC.get('kerbs', {})
            for k in ks.get('strips', []):
                i0, i1 = int(round(k['s0'] / sp)), int(round(k['s1'] / sp))
                st = np.arange(i0, i1 + 1) % n
                off = -ks.get('width', 0.9) / 2 if ks.get('inside', True) else 0.0
                E = L if k['side'] > 0 else R
                P = E[st] + NL[st] * (k['side'] * off)
                d.line([px(*p) for p in P], fill=(255, 0, 255), width=3)
            for m in SC.get('landmarks', []):
                q = px(m['x'], m['y'])
                d.rectangle([q[0] - 4, q[1] - 4, q[0] + 4, q[1] + 4], outline=(255, 255, 0))
                d.text((q[0] + 5, q[1] + 2), f"{m['kind'][:6]} {m.get('text', '')}", fill=(255, 255, 0))
            for tr in SC.get('terraces', []):
                for row in tr.get('rows', [])[::4]:
                    if row.get('pts'):
                        d.line([px(q[0], q[1]) for q in row['pts']], fill=(200, 200, 200), width=1)
                    else:
                        d.line([px(*row['a']), px(*row['b'])], fill=(200, 200, 200), width=1)
    if a.poly:
        for run in json.load(open(a.poly)):
            d.line([px(*cfg.enu(la, lo)) for la, lo in run], fill=(255, 0, 0), width=2)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    im.save(a.out)
    top = sorted(used.items(), key=lambda kv: -kv[1])[:4]
    print(f'{a.out}: centre ({cx:.1f}, {cy:.1f}), {Wp} px at {a.mpp} m/px; captures: ' + ', '.join(f'{k} {v}' for k, v in top))


if __name__ == '__main__':
    main()
