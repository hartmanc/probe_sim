"""Neighbour check of the clean captures (build-track stage 1.2): every pair of captures whose footprints overlap by
more than --min-overlap of a frame is phase-correlated on the overlap (grey, 0.12 m/px, edges), and the residual
offset beyond what the two URL centres imply is printed. A capture that disagrees by more than --tol m with BOTH of its
best-overlapping neighbours goes in config captures.exclude (or is re-captured). The scale is the Web Mercator z20
value in tiles.json; a scale error would show as residuals growing with the pair's separation (printed per pair).

    uv run --python 3.12 --with numpy,pillow python -I tools/track/compare/capture_pairs.py --track <id> [--tol 0.5]
Reads reference imagery, writes numbers only (stdout and, with --out, a json).
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import trackcfg  # noqa: E402
import captures as CAP  # noqa: E402


def patch(path, mask, cx, cy, mpp, x0, y1, W, H, S):
    g = np.asarray(Image.open(path).convert('L').filter(ImageFilter.GaussianBlur(1.0)), float)
    m = mask(*g.shape)
    gx = x0 + np.arange(W) * S; gy = y1 - np.arange(H) * S
    px = g.shape[1] / 2 + (gx[None, :] - cx) / mpp; py = g.shape[0] / 2 - (gy[:, None] - cy) / mpp
    px = np.broadcast_to(px, (H, W)); py = np.broadcast_to(py, (H, W))
    ok = (px >= 1) & (px < g.shape[1] - 2) & (py >= 1) & (py < g.shape[0] - 2)
    xi = np.clip(px.astype(int), 0, g.shape[1] - 1); yi = np.clip(py.astype(int), 0, g.shape[0] - 1)
    return g[yi, xi], ok & m[yi, xi]


def edges(a):
    gx = np.zeros_like(a); gy = np.zeros_like(a); gx[:, 1:-1] = a[:, 2:] - a[:, :-2]; gy[1:-1] = a[2:] - a[:-2]
    e = np.hypot(gx, gy); return (e - e.mean()) / (e.std() + 1e-6)


def phase(a, b, w):
    F = np.fft.fft2(edges(a) * w) * np.conj(np.fft.fft2(edges(b) * w)); r = np.fft.ifft2(F / (np.abs(F) + 1e-6)).real
    iy, ix = np.unravel_index(r.argmax(), r.shape); H, W = r.shape
    # sub-pixel by a parabola through the peak's neighbours
    def sub(v0, v1, v2): d = v0 - 2 * v1 + v2; return 0.0 if abs(d) < 1e-9 else 0.5 * (v0 - v2) / d
    dx = ix + sub(r[iy, ix - 1], r[iy, ix], r[iy, (ix + 1) % W]); dy = iy + sub(r[iy - 1, ix], r[iy, ix], r[(iy + 1) % H, ix])
    if dy > H / 2: dy -= H
    if dx > W / 2: dx -= W
    return dx, dy, r.max() / r.std()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--track', required=True); ap.add_argument('--tol', type=float, default=0.5)
    ap.add_argument('--min-overlap', type=float, default=0.3); ap.add_argument('--out', default=None)
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    caps = CAP.capture_list(cfg, 'clean')
    T = {t['name']: t for t in json.load(open(os.path.join(cfg.path(cfg['captures']['clean_dir']), cfg['captures']['clean_index'])))}
    S = 0.12
    res = []
    for i, p in enumerate(caps):
        mpp = T[p['name']]['mpp']; fw, fh = 1440 * mpp, 725 * mpp
        for q in caps[i + 1:]:
            ox = fw - abs(p['x'] - q['x']); oy = fh - abs(p['y'] - q['y'])
            if ox <= 0 or oy <= 0 or ox * oy < a.min_overlap * fw * fh: continue
            x0 = max(p['x'], q['x']) - fw / 2 + 2; x1 = min(p['x'], q['x']) + fw / 2 - 2
            y0 = max(p['y'], q['y']) - fh / 2 + 2; y1 = min(p['y'], q['y']) + fh / 2 - 2
            W = int((x1 - x0) / S); H = int((y1 - y0) / S)
            if W < 64 or H < 64: continue
            A, ma = patch(p['path'], p['mask'], p['x'], p['y'], mpp, x0, y1, W, H, S)
            B, mb = patch(q['path'], q['mask'], q['x'], q['y'], mpp, x0, y1, W, H, S)
            w = np.outer(np.hanning(H), np.hanning(W)) * (ma & mb)
            dx, dy, pk = phase(A, B, w)
            res.append({'a': p['name'], 'b': q['name'], 'dx': round(dx * S, 2), 'dy': round(-dy * S, 2), 'peak': round(float(pk), 1),
                        'sep_m': round(math.hypot(p['x'] - q['x'], p['y'] - q['y']), 1)})
    good = [r for r in res if r['peak'] >= 8]
    print(f'{len(res)} overlapping pairs, {len(good)} with peak >= 8')
    off = np.array([math.hypot(r['dx'], r['dy']) for r in good])
    if len(off):
        print(f'pair residual |d| median {np.median(off):.2f} m, p90 {np.percentile(off, 90):.2f}, max {off.max():.2f}')
    bad = {}
    for r in good:
        d = math.hypot(r['dx'], r['dy'])
        for k in ('a', 'b'):
            bad.setdefault(r[k], []).append(d)
    flagged = [n for n, ds in bad.items() if len(ds) >= 2 and sorted(ds)[1] > a.tol] + [n for n, ds in bad.items() if len(ds) == 1 and ds[0] > a.tol]
    for r in good:
        if math.hypot(r['dx'], r['dy']) > a.tol:
            print(f"  {r['a']} vs {r['b']}: {r['dx']:+.2f} {r['dy']:+.2f} m (peak {r['peak']}, {r['sep_m']} m apart)")
    print('captures off by more than', a.tol, 'm from their two best neighbours:', flagged or 'none')
    names = {c['name'] for c in caps}
    lonely = sorted(n for n in names if n not in bad)
    print('captures with no well-registered neighbour:', lonely or 'none')
    if a.out:
        json.dump({'pairs': res, 'flagged': flagged, 'no_neighbour': lonely}, open(a.out, 'w'), indent=0)


if __name__ == '__main__':
    main()
