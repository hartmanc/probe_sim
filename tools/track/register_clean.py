"""Register clean Google captures (UI hidden by page CSS, labels off; the config's captures.clean_dir) for the track
pipeline. Each capture is a 1440x725 z20 screenshot whose centre is the lat/lon in the URL (tile index entries
{name, lat, lon}). The captures agree with each other to a pixel, so ONE common Google-to-ortho shift is used for all
of them (captures.py); this script measures it.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/register_clean.py --track <id> [--ortho <ortho.jpg>] [--write]

Two cases:
  * the config has masked z20 captures (Laguna, 18 Oct 2026): each clean capture is phase-correlated at 0.12 m/px
    against the z20 capture it overlaps best and gets rel_dx/rel_dy relative to the raw z20 imagery; the common shift
    is the config's captures.common_shift (the median of the z20 registrations, out/paint_regs.json);
  * clean captures only (every new circuit): each capture is phase-correlated against the graded ortho of the first
    build (paint.register, edge maps at 0.3 m/px); the common shift is the median over captures, written to
    shift.json in the capture folder ({"common_shift": [dx, dy], "per_capture": {name: [dx, dy, peak]}}), and each
    capture gets rel_dx = rel_dy = 0 (per-capture registrations against a 0.6 m ortho are noise: 0.3-0.6 m jogs).
Run the geometry stage once first (it writes out/<id>/work/ortho.jpg and work/v2/track.json), register, then rebuild.
Without --write it only prints. The tile index gains x, y (ENU) for every capture either way.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import trackcfg  # noqa: E402
import captures as CAP  # noqa: E402


def world_patch(im, cx, cy, mpp, x0, y0, S, W, H):
    """resample image (centre world cx,cy, mpp) onto a W x H grid of step S starting at world (x0, y0) top-left."""
    gx = x0 + np.arange(W) * S; gy = y0 - np.arange(H) * S
    px = im.shape[1] / 2 + (gx[None, :] - cx) / mpp; py = im.shape[0] / 2 - (gy[:, None] - cy) / mpp
    px = np.broadcast_to(px, (H, W)); py = np.broadcast_to(py, (H, W))
    ok = (px >= 0) & (px < im.shape[1] - 1) & (py >= 0) & (py < im.shape[0] - 1)
    xi = np.clip(px.astype(int), 0, im.shape[1] - 1); yi = np.clip(py.astype(int), 0, im.shape[0] - 1)
    return im[yi, xi], ok, xi, yi


def edges(a):
    gx = np.zeros_like(a); gy = np.zeros_like(a); gx[:, 1:-1] = a[:, 2:] - a[:, :-2]; gy[1:-1] = a[2:] - a[:-2]
    e = np.hypot(gx, gy); return (e - e.mean()) / (e.std() + 1e-6)


def against_z20(cfg, meta, mpp, regs):
    """Laguna's case: shift of each clean capture relative to the raw z20 capture it overlaps best."""
    cc = cfg['captures']; zdir = cfg.path(cc['z20_dir'])
    z20 = json.load(open(os.path.join(zdir, cc['z20_index'])))
    mask = CAP.MASKS[cc.get('z20_mask') or 'google_ui_2026_10_18']
    for m in meta:
        x, y = m['x'], m['y']
        g = np.asarray(Image.open(os.path.join(cfg.path(cc['clean_dir']), m['name'] + '_google.jpg')).convert('L'), float)
        best = None
        for t in z20:
            if math.hypot(t['x'] - x, t['y'] - y) > 100: continue
            r = regs.get(t['name']); rdx, rdy = (r[1], r[2]) if r and r[3] >= 8 else (0.0, 0.0)  # noqa: F841
            o = np.asarray(Image.open(os.path.join(zdir, t['name'] + '_google.jpg')).convert('L'), float); om = mask(*o.shape)
            S = 0.12; W, H = 512, 256; x0, y0 = (x + t['x']) / 2 - W * S / 2, (y + t['y']) / 2 + H * S / 2
            A, okA, xi, yi = world_patch(o, t['x'], t['y'], mpp, x0, y0, S, W, H); okA &= om[yi, xi]
            Bp, okB, _, _ = world_patch(g, x, y, mpp, x0, y0, S, W, H)   # z20 captures share one scale
            w = (okA & okB) * np.outer(np.hanning(H), np.hanning(W))
            if w.mean() < 0.15: continue
            Fq = np.fft.fft2(edges(A) * w) * np.conj(np.fft.fft2(edges(Bp) * w)); rr = np.fft.ifft2(Fq / (np.abs(Fq) + 1e-6)).real
            iy, ix = np.unravel_index(rr.argmax(), rr.shape); sc = rr.max() / rr.std()
            iy = iy - H if iy > H // 2 else iy; ix = ix - W if ix > W // 2 else ix
            # feature in A at grid (j, i) appears in B at (j - iy, i - ix): B world = A world + (-ix*S, +iy*S)
            if best is None or sc > best[0]: best = (sc, -ix * S, iy * S, t['name'])
        if best is None:
            print(m['name'], 'no overlapping z20 capture; shift 0'); m.update(mpp=mpp, rel_dx=0.0, rel_dy=0.0, score=0.0, ref=''); continue
        sc, sx, sy, ref = best
        m.update(mpp=mpp, rel_dx=round(float(sx), 2), rel_dy=round(float(sy), 2), score=round(float(sc), 1), ref=ref)
        print(f"{m['name']}: shift vs {ref} {sx:+.2f} {sy:+.2f} m, score {sc:.1f}")


def against_ortho(cfg, meta, mpp, ortho_path, O):
    """Clean captures only: each against the graded ortho; the median is the common shift, rel = 0."""
    import paint
    ORT = Image.open(ortho_path).convert('L'); per = {}
    for m in meta:
        g = Image.open(os.path.join(cfg.path(cfg['captures']['clean_dir']), m['name'] + '_google.jpg')).convert('RGB')
        dx, dy, pk = paint.register(g, m, ORT, O, mpp)
        per[m['name']] = [round(dx, 2), round(dy, 2), round(float(pk), 1)]
        m.update(mpp=mpp, rel_dx=0.0, rel_dy=0.0, score=round(float(pk), 1), ref='ortho')
        print(f"{m['name']}: vs ortho {dx:+.2f} {dy:+.2f} m, peak {pk:.1f}")
    good = [v for v in per.values() if v[2] >= 8] or list(per.values())
    shift = [round(float(np.median([v[0] for v in good])), 2), round(float(np.median([v[1] for v in good])), 2)]
    spread = max(math.hypot(v[0] - shift[0], v[1] - shift[1]) for v in good)
    print(f"common shift (median of {len(good)} registrations with peak >= 8): {shift} m; largest departure {spread:.2f} m")
    return {'common_shift': shift, 'per_capture': per}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--track', required=True)
    ap.add_argument('--ortho', default=None, help="graded ortho.jpg of the first build (default out/<id>/work/ortho.jpg)")
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    cfg = trackcfg.load(a.track); cc = cfg['captures']; mpp = cc['mpp']
    idx = os.path.join(cfg.path(cc['clean_dir']), cc['clean_index'])
    meta = json.load(open(idx))
    for m in meta:
        x, y = cfg.enu(m['lat'], m['lon']); m['x'], m['y'] = round(float(x), 3), round(float(y), 3)
    shift = None
    if cc.get('z20_dir'):
        rp = os.path.join(HERE, 'out', 'paint_regs.json')
        regs = {r[0]: r for r in json.load(open(rp))} if os.path.exists(rp) else {}
        against_z20(cfg, meta, mpp, regs)
    else:
        op = a.ortho or os.path.join(HERE, 'out', cfg['id'], 'work', 'ortho.jpg')
        T = json.load(open(os.path.join(os.path.dirname(op), 'v2', 'track.json')))
        shift = against_ortho(cfg, meta, mpp, op, T['ortho'])
    if not a.write:
        print('dry run; --write to update the tile index' + (' and shift.json' if shift else '')); return
    json.dump(meta, open(idx, 'w'), indent=1)
    if shift:
        json.dump(shift, open(os.path.join(os.path.dirname(idx), 'shift.json'), 'w'), indent=1)
    print('wrote', idx)


if __name__ == '__main__':
    main()
