"""Straightened satellite strips: the Google z20 lap captures resampled in track coordinates (station along x, 0.25 m
per pixel; lateral down the page, left edge of the track at the top, 0.06 m per pixel), with the track.json edges
drawn as green ticks, an optional second track.json's edges as red ticks, and tools/track/out/sweep.npz detections
(blue = left, orange = right). In this frame a painted edge line that runs parallel to the track is a straight row
of white pixels, so a wave, notch, step or bulge of the green edge against the paint is plain to see.

    uv run --python 3.12 --with numpy,pillow python -I tools/track/compare/straight_strip.py <out.jpg> <s0> <s1>
        [--track track.json] [--ref ref_track.json] [--chunk 150] [--no-sweep]

Each station uses the capture where it sits farthest from the Google UI panels (same mask as measure_paint.py),
shifted by that capture's registration (tools/track/out/paint_regs.json).
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
TR = os.path.join(ROOT, 'tools', 'track'); sys.path.insert(0, TR)
from sweep_paint import ui_mask, bilinear, geometry, MPP, SAT, OUTD, EXCLUDE_TILES  # noqa: E402

DS, DL, PAD = 0.25, 0.06, 4.5


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('s0', type=int); ap.add_argument('s1', type=int)
    ap.add_argument('--track', default=os.path.join(ROOT, 'public/tracks/laguna_seca/track.json'))
    ap.add_argument('--ref', default=''); ap.add_argument('--chunk', type=int, default=150); ap.add_argument('--no-sweep', action='store_true')
    ap.add_argument('--title', default=''); ap.add_argument('--zoom', type=float, default=1.0)
    ap.add_argument('--side', default='', help='left|right: edge-relative view, the current edge is the middle row, outward up')
    ap.add_argument('--half', type=float, default=3.0)
    a = ap.parse_args()
    T = json.load(open(a.track)); C, NL, hl, hr = geometry(T); n = len(C)
    RF = None
    if a.ref:
        R_ = json.load(open(a.ref)); Lr = np.array(R_['left'])[:, :2]; Rr = np.array(R_['right'])[:, :2]
        RF = (((Lr - C) * NL).sum(1), -((Rr - C) * NL).sum(1))     # ref edges on this track's normals (same stations)
    sw = None if a.no_sweep or not os.path.exists(os.path.join(OUTD, 'sweep.npz')) else np.load(os.path.join(OUTD, 'sweep.npz'))
    regs = {r[0]: r for r in json.load(open(os.path.join(OUTD, 'paint_regs.json')))}
    tiles = [t for t in json.load(open(os.path.join(SAT, 'z20_tiles.json'))) if t['name'] not in EXCLUDE_TILES]; cache = {}

    def img(t):
        if t['name'] not in cache:
            im = np.asarray(Image.open(os.path.join(SAT, t['name'] + '_google.jpg')).convert('RGB')).astype(np.float32)
            cache[t['name']] = (im, ui_mask(*im.shape[:2]))
        return cache[t['name']]

    ks = [k % n for k in range(a.s0, a.s1)]
    sg = 1 if a.side == 'left' else -1
    if a.side: global DL; DL = 0.03
    lat_max = (a.half if a.side else max(max(hl[k], hr[k]) for k in ks) + PAD)
    lats = np.arange(lat_max, -lat_max - 1e-9, -DL)               # top = left of the track (side mode: outward)
    rows = []
    for k in ks:
        for f in np.arange(0, 1, DS):
            # interpolate the station frame along s
            k2 = (k + 1) % n; c = C[k] * (1 - f) + C[k2] * f; nl = NL[k] * (1 - f) + NL[k2] * f; nl /= np.linalg.norm(nl)
            if a.side:
                hw = (hl if a.side == 'left' else hr); e = hw[k] * (1 - f) + hw[k2] * f
                LL = sg * (e + lats)
            else: LL = lats
            X = c[0] + LL * nl[0]; Y = c[1] + LL * nl[1]; best = None
            for t in tiles:
                im, m = img(t); H, W = im.shape[:2]; r = regs.get(t['name']); dx, dy = (r[1], r[2]) if r and r[3] >= 8 else (0, 0)
                px = W / 2 + (X + dx - t['x']) / MPP; py = H / 2 - (Y + dy - t['y']) / MPP
                if not ((px >= 1) & (px < W - 2) & (py >= 1) & (py < H - 2)).all(): continue
                if not m[np.round(py).astype(int), np.round(px).astype(int)].all(): continue
                sc = abs(px.mean() - W * 0.6) / W + abs(py.mean() - H / 2) / H
                if best is None or sc < best[0]: best = (sc, im, px, py)
            rows.append(bilinear(best[1], best[2], best[3]) if best else np.zeros((len(lats), 3), np.float32))
    A = np.stack(rows, 1).clip(0, 255).astype(np.uint8)            # (lat, s)
    im = Image.fromarray(A); d = ImageDraw.Draw(im)
    py_of = lambda lat: (lat_max - lat) / DL
    if a.side:
        hw = hl if a.side == 'left' else hr
        for i, k in enumerate(ks):
            x = i / DS
            if i % 3 == 0: d.line([(x, py_of(0)), (x + 4, py_of(0))], fill=(40, 255, 40), width=2)
            if i % 4 == 0:
                for o in (0.4, -0.4): d.point([(x, py_of(o)), (x + 1, py_of(o))], fill=(255, 0, 255))
            if i % 10 == 0:
                for o in (1.0, -1.0, 2.0, -2.0): d.point([(x, py_of(o))], fill=(0, 255, 255))
            if RF is not None:
                y = py_of((RF[0][k] if a.side == 'left' else RF[1][k]) - hw[k]); d.point([(x + 1, y), (x + 2, y)], fill=(255, 40, 40))
            if sw is not None:
                dv = sw[f'dev_{a.side}'][k]
                if not np.isnan(dv): y = py_of(dv); d.point([(x + 2, y), (x + 3, y)], fill=(60, 140, 255))
            if k % 10 == 0:
                d.line([(x, 0), (x, 6)], fill=(255, 255, 0)); d.text((x + 2, 0), str(k), fill=(255, 255, 0))
        k_iter = []
    else: k_iter = list(enumerate(ks))
    for i, k in k_iter:
        x = i / DS
        for lat, col in ((hl[k], (60, 255, 60)), (-hr[k], (60, 255, 60))):
            y = py_of(lat); d.line([(x, y - 1), (x + 1, y - 1)], fill=col); d.line([(x, y + 1), (x + 1, y + 1)], fill=col)
        if RF is not None:
            for lat in (RF[0][k], -RF[1][k]):
                y = py_of(lat); d.point([(x + 2, y)], fill=(255, 40, 40))
        if sw is not None:
            for side, sg, hw, col in (('left', 1, hl, (60, 140, 255)), ('right', -1, hr, (255, 150, 0))):
                dv = sw[f'dev_{side}'][k]
                if not np.isnan(dv): y = py_of(sg * (hw[k] + dv)); d.point([(x + 2, y), (x + 3, y)], fill=col)
        if k % 10 == 0:
            d.line([(x, 0), (x, 6)], fill=(255, 255, 0)); d.text((x + 2, 0), str(k), fill=(255, 255, 0))
            d.line([(x, im.height - 6), (x, im.height)], fill=(255, 255, 0))
    # chunk into rows of a.chunk stations
    cw = int(a.chunk / DS); chunks = [im.crop((x, 0, min(im.width, x + cw), im.height)) for x in range(0, im.width, cw)]
    out = Image.new('RGB', (cw, len(chunks) * (im.height + 8) + 22), (20, 20, 20))
    dd = ImageDraw.Draw(out)
    dd.text((4, 4), a.title or f'stations {a.s0}-{a.s1}: green = track edge, red = reference, blue/orange = paint sweep; along {DS} m/px, across {DL} m/px', fill=(255, 255, 255))
    for i, c in enumerate(chunks): out.paste(c, (0, 22 + i * (im.height + 8)))
    if a.zoom != 1: out = out.resize((int(out.width * a.zoom), int(out.height * a.zoom)), Image.LANCZOS)
    out.save(a.out, quality=88); print(a.out, out.size)


if __name__ == '__main__':
    sys.exit(main())
