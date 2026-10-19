"""Satellite overlay check: a candidate package's edges, centre and racing line drawn on the track's own Google z20
captures (reference only, never textures), one sheet per capture (or per station window), for the builder to read.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/overlay_captures.py --track <id> \
        --pkg tools/track/out/<id> [--ref <other package dir>] [--out tools/track/compare/<id>/overlay] [--which clean]
        [--stations a:b] [--scale 0.5] [--grid 2]

Each capture is drawn at its own position with the config's capture shift applied (a feature at world p appears at
p + (dx, dy)), so the lines sit where the pipeline believes the paint is. Colours: candidate edges red, centre blue,
racing line yellow, --ref edges green (dashed by dots), station ticks every 50 m in white with the number every 100 m.
--grid N packs N x N downscaled captures per sheet (fewer screenshots to read). Writes JPEGs only (git-ignored).
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import trackcfg  # noqa: E402
import captures as CAP  # noqa: E402


def load_pkg(d):
    T = json.load(open(os.path.join(d, 'track.json')))
    g = os.path.join(d, 'ghosts.json')
    G = json.load(open(g)) if os.path.exists(g) else None
    C = np.array(T['center'])[:, :2]; Lp = np.array(T['left'])[:, :2]; Rp = np.array(T['right'])[:, :2]
    line = None
    if G is not None:
        n = len(C); sp = T.get('spacing_m', 1.0)
        off = np.array(G['line']['offset_m']); s = np.arange(len(off)) * G['s_grid_m'] / sp
        e = np.interp(np.arange(n), s, off, period=n)
        t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True)
        nl = np.c_[-t[:, 1], t[:, 0]]
        line = C + e[:, None] * nl
    return dict(T=T, C=C, L=Lp, R=Rp, line=line, sp=T.get('spacing_m', 1.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True)
    ap.add_argument('--pkg', required=True)
    ap.add_argument('--ref', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--which', default='clean')
    ap.add_argument('--stations', default=None, help='a:b, only captures covering these stations')
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--grid', type=int, default=1)
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    out = a.out or os.path.join(HERE, a.track, 'overlay')
    os.makedirs(out, exist_ok=True)
    P = load_pkg(a.pkg); Q = load_pkg(a.ref) if a.ref else None
    mpp = cfg['captures']['mpp']
    tiles = CAP.capture_list(cfg, a.which)
    n = len(P['C'])
    sel = None
    if a.stations:
        lo, hi = (int(v) for v in a.stations.split(':'))
        sel = np.arange(lo, hi + (n if hi < lo else 0) + 1) % n
    font = ImageFont.load_default()
    imgs = []
    for t in tiles:
        im = Image.open(t['path']).convert('RGB'); W, H = im.size
        dr = ImageDraw.Draw(im)

        def px(XY):
            X = XY[:, 0] + t['dx']; Y = XY[:, 1] + t['dy']
            return np.c_[W / 2 + (X - t['x']) / mpp, H / 2 - (Y - t['y']) / mpp]
        pc = px(P['C'])
        inside = (pc[:, 0] >= 0) & (pc[:, 0] < W) & (pc[:, 1] >= 0) & (pc[:, 1] < H)
        if not inside.any() or (sel is not None and not inside[sel].any()):
            continue

        def poly(XY, col, w=2, dots=False):
            p = px(XY)
            for i in range(len(p) - 1):
                if not (inside[i] or inside[(i + 1) % n]):
                    continue
                if dots and i % 3:
                    continue
                dr.line([tuple(p[i]), tuple(p[i + 1])], fill=col, width=w)
        if Q is not None:
            poly(Q['L'], (60, 230, 60), 2, True); poly(Q['R'], (60, 230, 60), 2, True)
        poly(P['L'], (255, 40, 40)); poly(P['R'], (255, 40, 40)); poly(P['C'], (60, 120, 255), 1)
        if P['line'] is not None:
            poly(P['line'], (255, 220, 0), 1)
        step = max(1, int(round(50 / P['sp'])))
        pl, pr = px(P['L']), px(P['R'])
        for i in range(0, n, step):
            if inside[i]:
                dr.line([tuple(pl[i]), tuple(pr[i])], fill=(255, 255, 255), width=1)
                if i % (2 * step) == 0:
                    dr.text(tuple(pr[i] + 4), f'{i}', fill=(255, 255, 255), font=font)
        ks = np.nonzero(inside)[0]
        dr.rectangle([0, 0, 420, 14], fill=(0, 0, 0))
        dr.text((4, 2), f"{t['name']}  stations {ks.min()}..{ks.max()}  red=cand edges, blue=centre, yellow=line"
                + (", green dots=ref" if Q else ''), fill=(255, 255, 255), font=font)
        if a.scale != 1.0:
            im = im.resize((int(W * a.scale), int(H * a.scale)), Image.LANCZOS)
        imgs.append((t['name'], int(np.median(ks)), im))
    imgs.sort(key=lambda r: r[1])
    g = a.grid
    for j in range(0, len(imgs), g * g):
        chunk = imgs[j:j + g * g]
        w, h = chunk[0][2].size
        sh = Image.new('RGB', (w * g, h * ((len(chunk) + g - 1) // g)), (0, 0, 0))
        for k, (_, _, im) in enumerate(chunk):
            sh.paste(im, ((k % g) * w, (k // g) * h))
        name = chunk[0][0] if g == 1 else f'sheet_{j // (g * g):02d}_{chunk[0][1]:04d}-{chunk[-1][1]:04d}'
        sh.save(os.path.join(out, name + '.jpg'), quality=85)
    print(f'{len(imgs)} captures drawn -> {out}')


if __name__ == '__main__':
    main()
