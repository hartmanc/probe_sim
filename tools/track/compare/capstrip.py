"""Straightened strips of the clean z20 captures (reference only, never textures) along a package's track: track s runs
left to right, the left side of the track is at the top, the centreline is the middle row. The evidence sheet of the
scenery round (20 Oct 2026): kerbs, walls, tyre walls, fences, marshal posts and runoff read off station by station.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/capstrip.py --track sonoma \
        --pkg tools/track/out/sonoma_r3 --s0 0 --s1 150 [--lat 30] [--mpp 0.15] [--scenery] [--detected] --out x.png

Overlay: the track edges (green dots), ticks every 10 m with the track s every 50 m (yellow), lateral ticks every 5 m
(cyan, left margin); --scenery draws the package's barriers / kerbs / landmarks (as in capwin.py), --detected the
kerb_detect.py candidates (magenta bars at the edge). The lateral scale is the distance along each station's normal,
so far from the track on the inside of a tight corner the picture folds; read those places on capwin.py instead.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import trackcfg  # noqa: E402
from capsample import Sampler  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True); ap.add_argument('--pkg', required=True)
    ap.add_argument('--s0', type=float, required=True); ap.add_argument('--s1', type=float, required=True)
    ap.add_argument('--lat', type=float, default=30.0); ap.add_argument('--mpp', type=float, default=0.15)
    ap.add_argument('--scenery', action='store_true'); ap.add_argument('--detected', action='store_true')
    ap.add_argument('--poly', help='json: list of lat/lon polylines drawn in red (wall_measure.py output)')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C = np.array(T['center'])[:, :2]; L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]
    n, sp = T['n'], T['spacing_m']
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    NL = np.c_[-tg[:, 1], tg[:, 0]]
    hl = ((L - C) * NL).sum(1); hr = -((R - C) * NL).sum(1)
    s = np.arange(a.s0, a.s1, a.mpp)
    u = s / sp; k0 = np.floor(u).astype(int) % n; k1 = (k0 + 1) % n; f = (u - np.floor(u))[:, None]
    c = C[k0] * (1 - f) + C[k1] * f
    nl = NL[k0] * (1 - f) + NL[k1] * f; nl /= np.linalg.norm(nl, axis=1, keepdims=True)
    lats = np.arange(a.lat, -a.lat, -a.mpp)
    X = c[None, :, 0] + lats[:, None] * nl[None, :, 0]; Y = c[None, :, 1] + lats[:, None] * nl[None, :, 1]
    rgb, _ = Sampler(cfg).sample(X, Y)
    img = np.nan_to_num(rgb, nan=30).clip(0, 255).astype(np.uint8)
    im = Image.fromarray(img); d = ImageDraw.Draw(im)
    H, W = img.shape[:2]
    py = lambda lat: (a.lat - lat) / a.mpp  # noqa: E731
    px = lambda sv: (sv - a.s0) / a.mpp  # noqa: E731
    for j in range(0, W, 4):
        k = k0[j]
        for v in (hl[k], -hr[k]):
            d.point([(j, py(v))], fill=(0, 255, 0))
    for sv in np.arange(np.ceil(a.s0 / 10) * 10, a.s1, 10):
        x = px(sv); d.line([(x, 0), (x, 8)], fill=(255, 230, 0)); d.line([(x, H - 8), (x, H)], fill=(255, 230, 0))
        if abs(sv % 50) < 1e-6:
            d.text((x + 2, 9), f'{sv:.0f}', fill=(255, 255, 0)); d.text((x + 2, H - 20), f'{sv:.0f}', fill=(255, 255, 0))
    for lv in np.arange(-a.lat, a.lat + 0.1, 5):
        d.line([(0, py(lv)), (6, py(lv))], fill=(0, 255, 255)); d.text((8, py(lv) - 6), f'{lv:+.0f}', fill=(0, 255, 255))

    def proj(P):
        P = np.atleast_2d(np.asarray(P, float))[:, :2]
        dd = ((P[:, None, :] - C[None, :, :]) ** 2).sum(-1); i = dd.argmin(1)
        lat = ((P - C[i]) * NL[i]).sum(1); along = ((P - C[i]) * tg[i]).sum(1)
        sv = i * sp + along
        # unwrap into the window
        sv = np.where(sv < a.s0 - n * sp / 2, sv + n * sp, sv)
        return sv, lat
    if a.scenery:
        SC = json.load(open(os.path.join(a.pkg, 'scenery.json')))
        col = {'concrete': (255, 255, 255), 'pitwall': (255, 160, 0), 'tyres': (255, 40, 40), 'armco': (90, 140, 255), 'fence': (255, 120, 0)}
        sel = lambda sv: (sv >= a.s0 - 5) & (sv <= a.s1 + 5)  # noqa: E731
        for b in SC.get('barriers', []):
            sv, lat = proj(b['pts'])
            for i in range(len(sv) - 1):
                if sel(sv[i]) and sel(sv[i + 1]) and abs(sv[i + 1] - sv[i]) < 20 and abs(lat[i]) < a.lat:
                    d.line([(px(sv[i]), py(lat[i])), (px(sv[i + 1]), py(lat[i + 1]))], fill=col.get(b['kind'], (255, 0, 255)), width=2)
        ks = SC.get('kerbs', {})
        for kb in ks.get('strips', []):
            if kb['s1'] < a.s0 or kb['s0'] > a.s1:
                continue
            e = lambda sv: hl[int(sv / sp) % n] if kb['side'] > 0 else -hr[int(sv / sp) % n]  # noqa: E731
            for sv in np.arange(max(kb['s0'], a.s0), min(kb['s1'], a.s1), 1.0):
                lv = e(sv) - kb['side'] * ks.get('width', 0.9) / 2
                d.point([(px(sv), py(lv)), (px(sv), py(lv) + 1)], fill=(255, 0, 255))
        for m in SC.get('landmarks', []):
            sv, lat = proj([[m['x'], m['y']]])
            if sel(sv[0]) and abs(lat[0]) < a.lat:
                x, y = px(sv[0]), py(lat[0]); d.rectangle([x - 4, y - 4, x + 4, y + 4], outline=(255, 255, 0))
                d.text((x + 5, y - 5), f"{m['kind'][:7]} {m.get('text', '')}", fill=(255, 255, 0))
    if a.detected:
        for r in json.load(open(os.path.join(a.pkg, 'work', 'kerbs_detected.json'))):
            if r['s1'] < a.s0 or r['s0'] > a.s1:
                continue
            sg = 1 if r['side'] == 'left' else -1
            for sv in np.arange(max(r['s0'], a.s0), min(r['s1'], a.s1), 0.5):
                k = int(sv / sp) % n; e = hl[k] if sg > 0 else hr[k]
                d.line([(px(sv), py(sg * (e + 1.8))), (px(sv), py(sg * (e + 2.4)))], fill=(255, 0, 255))
    if a.poly:
        for run in json.load(open(a.poly)):
            sv, lat = proj([cfg.enu(la, lo) for la, lo in run])
            pts = [(px(x), py(y)) for x, y in zip(sv, lat) if a.s0 - 5 <= x <= a.s1 + 5]
            if len(pts) > 1:
                d.line(pts, fill=(255, 0, 0), width=2)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    im.save(a.out)
    print(a.out, im.size)


if __name__ == '__main__':
    main()
