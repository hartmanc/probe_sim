"""Register clean Google captures (UI hidden by page CSS, labels off; tools/track/compare/satellite_clean/) against the
masked z20 captures they overlap (18 Oct 2026, fit_edges_spline.py data). Each clean capture is a 1440x725 screenshot
whose centre is the lat/lon in the URL; this finds its scale (metres per pixel) and its shift relative to every
overlapping z20 capture by phase correlation at 0.12 m/px over the z20 capture's unmasked pixels, and records
rel_dx/rel_dy = the clean capture's shift relative to the raw z20 imagery (fit_edges_spline.py adds the one common
Google-to-ortho shift to both).
    uv run --python 3.12 --with numpy,pillow python -I tools/track/register_clean.py
Reads/writes satellite_clean/tiles.json: [{name, lat, lon, x, y, mpp, rel_dx, rel_dy, score, ref}]."""
import json, math, os, sys
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from sweep_paint import ui_mask, MPP, SAT, OUTD  # noqa: E402
CLEAN = os.path.join(HERE, 'compare', 'satellite_clean')


def ll2xy():
    t = json.load(open(os.path.join(SAT, 'z20_tiles.json')))
    LL = np.array([[d['lat'], d['lon'], 1] for d in t]); X = np.array([[d['x'], d['y']] for d in t])
    co, *_ = np.linalg.lstsq(LL, X, rcond=None); return lambda lat, lon: np.array([lat, lon, 1]) @ co


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


def main():
    f = ll2xy(); meta = json.load(open(os.path.join(CLEAN, 'tiles.json')))
    z20 = json.load(open(os.path.join(SAT, 'z20_tiles.json'))); regs = {r[0]: r for r in json.load(open(os.path.join(OUTD, 'paint_regs.json')))}
    for m in meta:
        x, y = f(m['lat'], m['lon']); m['x'], m['y'] = round(float(x), 3), round(float(y), 3)
        g = np.asarray(Image.open(os.path.join(CLEAN, m['name'] + '_google.jpg')).convert('L'), float)
        best = None
        for t in z20:
            if math.hypot(t['x'] - x, t['y'] - y) > 100: continue
            r = regs.get(t['name']); rdx, rdy = (r[1], r[2]) if r and r[3] >= 8 else (0.0, 0.0)
            o = np.asarray(Image.open(os.path.join(SAT, t['name'] + '_google.jpg')).convert('L'), float); om = ui_mask(*o.shape)
            S = 0.12; W, H = 512, 256; x0, y0 = (x + t['x']) / 2 - W * S / 2, (y + t['y']) / 2 + H * S / 2
            A, okA, xi, yi = world_patch(o, t['x'], t['y'], MPP, x0, y0, S, W, H); okA &= om[yi, xi]
            for mpp in (MPP,):   # z20 captures share one scale (39 of 42 matched exactly; a free scale wandered by 0.5-1 % on weak overlaps)
                Bp, okB, _, _ = world_patch(g, x, y, mpp, x0, y0, S, W, H)
                w = (okA & okB) * np.outer(np.hanning(H), np.hanning(W))
                if w.mean() < 0.15: continue
                Fq = np.fft.fft2(edges(A) * w) * np.conj(np.fft.fft2(edges(Bp) * w)); rr = np.fft.ifft2(Fq / (np.abs(Fq) + 1e-6)).real
                iy, ix = np.unravel_index(rr.argmax(), rr.shape); sc = rr.max() / rr.std()
                iy = iy - H if iy > H // 2 else iy; ix = ix - W if ix > W // 2 else ix
                # feature in A at grid (j, i) appears in B at (j - iy, i - ix): B world = A world + (-ix*S, +iy*S)
                if best is None or sc > best[0]: best = (sc, mpp, -ix * S, iy * S, t['name'], rdx, rdy)
                if False: print(f"   vs {t['name']} (reg {rdx:+.1f} {rdy:+.1f}): shift {-ix * S:+.2f} {iy * S:+.2f} score {sc:.1f}")
        if best is None: print(m['name'], 'no overlapping z20 capture; shift 0'); m.update(mpp=MPP, rel_dx=0.0, rel_dy=0.0, score=0.0, ref=''); continue
        sc, mpp, sx, sy, ref, rdx, rdy = best
        # Google z20 feature at world p + (rdx, rdy); in the clean capture at p + (rdx + sx, rdy + sy)
        m.update(mpp=round(float(mpp), 5), rel_dx=round(float(sx), 2), rel_dy=round(float(sy), 2), score=round(float(sc), 1), ref=ref)
        print(f"{m['name']}: mpp {mpp:.5f} ({mpp / MPP:.3f} x z20), shift vs {ref} {sx:+.2f} {sy:+.2f} m, score {sc:.1f}")
    json.dump(meta, open(os.path.join(CLEAN, 'tiles.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
