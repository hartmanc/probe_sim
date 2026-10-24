"""Edge sheets for a person to look at (build-track stage 1; Buttonwillow round 3, 20 Oct 2026): crops of the clean
captures along given station ranges with the candidate package's fitted edges (red), centre (blue) and the edge
detector's readings on that capture (yellow dots: one per station and side, where the config's feature at that station
is asphalt_end / warm_end; cyan for kerb bands). Reference imagery only: never a texture, never committed.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/edge_sheets.py --track <id> \
        --pkg tools/track/out/<id> --out tools/track/compare/<id>/edge_sheets --stretch 2560:2660:clean_1 [--stretch ...]

Each stretch is drawn on the capture that covers its middle best, cropped to the stretch with 15 m of margin, scaled
to 1 px = 0.06 m (2x the capture), with station ticks every 10 m. One JPEG per stretch.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import trackcfg  # noqa: E402
import captures as CAP  # noqa: E402
import edges_spline as ES  # noqa: E402


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--track', required=True); ap.add_argument('--pkg', required=True)
    ap.add_argument('--out', required=True); ap.add_argument('--stretch', action='append', default=[])
    a = ap.parse_args()
    cfg = trackcfg.load(a.track); os.makedirs(a.out, exist_ok=True)
    sp = cfg['spline']; ES.AEND.update(jump=10.0, sat_max=30.0, lo=-1.2, hi=2.0); ES.AEND.update(sp.get('asphalt_end') or {})
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C = np.array(T['center'])[:, :2]; L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]; n = len(C)
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True); NL = np.c_[-tg[:, 1], tg[:, 0]]
    hl = ((L - C) * NL).sum(1); hr = -((R - C) * NL).sum(1)
    caps = CAP.capture_list(cfg, 'clean'); mpp = cfg['captures']['mpp']; feats = cfg['features']
    for spec in a.stretch:
        s0, s1, name = spec.split(':'); s0, s1 = int(s0), int(s1)
        ks = np.arange(s0, s1 + 1) % n; mid = C[ks[len(ks) // 2]]
        t = min(caps, key=lambda c: np.hypot(c['x'] - c['dx'] - mid[0], c['y'] - c['dy'] - mid[1]))
        im = Image.open(t['path']).convert('RGB'); arr = np.asarray(im).astype(np.float32); H, W = arr.shape[:2]
        topx = lambda P: (W / 2 + (P[..., 0] + t['dx'] - t['x']) / mpp, H / 2 - (P[..., 1] + t['dy'] - t['y']) / mpp)
        pts = np.r_[L[ks], R[ks]]; px, py = topx(pts)
        x0, x1 = int(max(0, px.min() - 15 / mpp)), int(min(W, px.max() + 15 / mpp)); y0, y1 = int(max(0, py.min() - 15 / mpp)), int(min(H, py.max() + 15 / mpp))
        if x1 - x0 < 50 or y1 - y0 < 50: print(f'{name}: not on {t["name"]}'); continue
        sc = 2
        crop = im.crop((x0, y0, x1, y1)).resize(((x1 - x0) * sc, (y1 - y0) * sc), Image.LANCZOS); d = ImageDraw.Draw(crop)
        cv = lambda X, Y: ((X - x0) * sc, (Y - y0) * sc)
        for E, col in ((L, (230, 40, 40)), (R, (230, 40, 40)), (C, (60, 110, 230))):
            X, Y = topx(E[ks]); d.line([cv(x, y) for x, y in zip(X, Y)], fill=col, width=2)
        mask = t['mask'](H, W)
        for side, sg, hw in (('left', 1, hl), ('right', -1, hr)):
            for k in ks:
                f = ES.feature_at(feats, side, int(k), n)
                lat = sg * (hw[k] + ES.U); P = C[k] + lat[:, None] * NL[k]; X, Y = topx(P)
                ok = (X > 1) & (X < W - 2) & (Y > 1) & (Y < H - 2)
                if ok.mean() < 0.8: continue
                ok &= mask[np.clip(Y.astype(int), 0, H - 1), np.clip(X.astype(int), 0, W - 1)]
                v = ES.bilinear(arr, np.clip(X, 1, W - 2), np.clip(Y, 1, H - 2))
                if f in ('asphalt_end', 'warm_end'):
                    e = ES.asphalt_end(v, ok) if f == 'asphalt_end' else ES.warm_end(v, ok)
                    if e is None: continue
                    q = C[k] + sg * (hw[k] + e) * NL[k]; col = (250, 220, 40)
                elif f == 'kerb_band':
                    bl = ES.bands(v, ok); c = ES.candidates(bl, sp.get('line_off', 0.26), True)
                    if not c: continue
                    e = min(c, key=lambda u: abs(u[0]))[0]; q = C[k] + sg * (hw[k] + e) * NL[k]; col = (40, 230, 230)
                else:
                    continue
                X, Y = topx(q); cx, cy = cv(X, Y); d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=col)
        for k in ks[::10]:
            X, Y = topx(C[k]); cx, cy = cv(X, Y); d.text((cx + 4, cy - 6), str(int(k)), fill=(255, 255, 255))
        d.rectangle([0, 0, 520, 16], fill=(0, 0, 0))
        d.text((4, 2), f'{name}: stations {s0}-{s1} on {t["name"]}; red fitted edges, blue centre, yellow asphalt-end readings, cyan kerb bands', fill=(255, 255, 0))
        crop.save(os.path.join(a.out, f'{name}_{s0}-{s1}.jpg'), quality=88)
        print(f'{name}: {s0}-{s1} on {t["name"]}')


if __name__ == '__main__':
    main()
