"""Edge sweep: where does the track.json edge depart from the painted road edge on the Google z20 captures?

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/sweep_paint.py [--out tools/track/out/sweep.npz]
        [--plot <png>] [--thr 0.4] [--min-len 5]

Why (18 Oct 2026): measure_paint.py walked out from the logged racing line with a 2 m window and drifted onto the pale
paved aprons (T5, T6, T9, T10, T11), the pit-lane joins and the shadows of walls, boards and bridges. This sweep
re-measures the paint ANCHORED AT THE CURRENT EDGE, so every station gets an independent check of the shipped edge:
for each station, side and z20 lap capture covering it (UI panels masked, each capture shifted by its registration
against the ortho, tools/track/out/paint_regs.json), the image is sampled along the station normal from 3.5 m inside
to 4 m outside the current edge (0.06 m steps, bilinear), and walked outward from solid asphalt to the first of
  - a white painted line whose far side is not this asphalt (the edge is the line's inner side; a white line with the
    same asphalt beyond is a marking or a map label and is stepped over),
  - a red/white kerb band (the edge is the kerb's outer limit: the v2/v3 edges include the kerbs),
  - 0.5 m of non-asphalt (dirt, verge paint, pale concrete, shadow darker than the asphalt by 35+).
The asphalt reference is the median of the 2.5 m just inside the walk start. Per station: the median over captures,
the number of captures and their spread. Shadows (a dark run where the walk ends) are flagged so the caller can mask
them. Writes dev_left/dev_right (detected minus current edge, metres, + = outward), n_left/n_right, spread_*,
kind_* (0 none, 1 white line, 2 kerb, 3 non-asphalt, 4 dark/shadow) and prints the runs where |dev| > --thr for at
least --min-len stations (median-5 filtered), the inventory the edge fixes start from.
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
SAT = os.path.join(HERE, 'compare', 'satellite'); OUTD = os.path.join(HERE, 'out')
MPP = 0.11992
# captures never traced: z20_s3400's registration against the ortho (-1.8, +0.9 m, peak 11.3) is ~1.3 m off its
# neighbours' (z20_s3315 -0.6/+0.3, z20_s3485 -0.9/0.0); the front-straight edges it fed carried that shift (18 Oct 2026)
EXCLUDE_TILES = {'z20_s3400'}


def ui_mask(H, W):
    """Google Maps UI on the captures (search panel, chips, controls): same rectangles as measure_paint.py."""
    m = np.ones((H, W), bool)
    m[:590, :470] = False; m[:62, :] = False; m[:, :78] = False; m[575:, 1265:] = False; m[675:, :] = False; m[610:, 85:180] = False
    return m


def bilinear(im, px, py):
    H, W = im.shape[:2]
    x0 = np.clip(np.floor(px).astype(int), 0, W - 2); y0 = np.clip(np.floor(py).astype(int), 0, H - 2)
    fx = (px - x0)[..., None]; fy = (py - y0)[..., None]
    a = im[y0, x0]; b = im[y0, x0 + 1]; c = im[y0 + 1, x0]; d = im[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def geometry(T):
    C = np.array(T['center'])[:, :2]; n = len(C)
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    NL = np.c_[-tg[:, 1], tg[:, 0]]
    L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]
    hl = ((L - C) * NL).sum(1); hr = -((R - C) * NL).sum(1)
    return C, NL, hl, hr


U = np.arange(-3.5, 4.0001, 0.06)          # lateral, metres outward from the current edge
I0 = int(np.searchsorted(U, 0.0))


def walk(v):
    """v: (len(U), 3) RGB along the outward normal. Returns (edge offset from the current edge, kind) or (nan, 0)."""
    br = v.mean(1); sat = v.max(1) - v.min(1)
    gb = np.abs(v[:, 1] - v[:, 2])
    red = (v[:, 0] > 100) & (v[:, 0] - v[:, 1] > 25) & (v[:, 0] - v[:, 2] > 20) & (gb < 20)
    grey = sat < 30
    # start: the innermost 2.5 m must be mostly grey; reference brightness from it
    seg = slice(0, int(2.5 / 0.06))
    if grey[seg].mean() < 0.6: return np.nan, 0
    ref = np.median(br[seg][grey[seg]])
    asph = grey & (np.abs(br - ref) < 22)
    white = (br > max(ref + 45, 165)) & (sat < 35) & (v[:, 0] - v[:, 2] < 22)    # warm pale dirt is not paint
    k = int(1.0 / 0.06)                       # start 2.5 m inside the edge (walk from U = -2.5)
    N = len(U); step = 0.06
    q = lambda m: max(1, int(round(m / step)))
    band = red | white
    while k < N - q(0.5):
        if band[k]:
            # a white or red band: walk over it (gaps under 0.12 m tolerated, kerb squares and joints)
            j = k; gap = 0
            while j < N and gap <= q(0.12):
                gap = 0 if band[j] else gap + 1; j += 1
            j -= gap; wdt = (j - k) * step
            has_red = red[k:j].mean() > 0.15
            b0, b1 = j + q(0.15), min(N, j + q(1.2))
            beyond_asph = b1 - b0 >= q(0.4) and asph[b0:b1].mean() > 0.7
            if wdt <= 0.35 and not has_red:
                if beyond_asph: k = j; continue           # a marking or a map label on the asphalt
                return U[(k + j) // 2], 1                   # painted edge line: its middle
            if wdt <= 1.4 or has_red:
                if beyond_asph: k = j; continue           # a painted box / text on the road
                return U[min(j, N - 1)], 2                  # kerb (red/white squares): its outer limit
            return U[k], 3                                  # long pale band: concrete runoff starts here
        if not asph[k]:
            if band[k:k + q(0.35)].any(): k += 1; continue    # blurred lead-in of a line or kerb
            w = slice(k, k + q(0.5))
            if (~asph[w]).mean() > 0.8:
                kind = 4 if (br[w] < ref - 35).mean() > 0.7 else 3
                return U[k], kind
        k += 1
    return np.nan, 0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=os.path.join(OUTD, 'sweep.npz'))
    ap.add_argument('--thr', type=float, default=0.4); ap.add_argument('--min-len', type=int, default=5)
    ap.add_argument('--track', default=os.path.join(ROOT, 'public/tracks/laguna_seca/track.json'))
    a = ap.parse_args()
    T = json.load(open(a.track)); C, NL, hl, hr = geometry(T); n = len(C)
    regs = {r[0]: r for r in json.load(open(os.path.join(OUTD, 'paint_regs.json')))}
    tiles = [t for t in json.load(open(os.path.join(SAT, 'z20_tiles.json'))) if t['name'] not in EXCLUDE_TILES]
    print('captures excluded:', sorted(EXCLUDE_TILES))
    meas = {s: [[] for _ in range(n)] for s in ('left', 'right')}; per_tile = []
    for t in tiles:
        im = np.asarray(Image.open(os.path.join(SAT, t['name'] + '_google.jpg')).convert('RGB')).astype(np.float32)
        H, W = im.shape[:2]; mask = ui_mask(H, W)
        r = regs.get(t['name']); dx, dy = (r[1], r[2]) if r and r[3] >= 8 else (0.0, 0.0)
        for side, sg, hw in (('left', 1, hl), ('right', -1, hr)):
            lat = sg * (hw[:, None] + U[None, :])                   # lateral from centre, + left
            X = C[:, 0:1] + lat * NL[:, 0:1] + dx; Y = C[:, 1:2] + lat * NL[:, 1:2] + dy
            px = W / 2 + (X - t['x']) / MPP; py = H / 2 - (Y - t['y']) / MPP
            ok = (px >= 1) & (px < W - 2) & (py >= 1) & (py < H - 2)
            idx = np.where(ok.all(1))[0]
            if not len(idx): continue
            pxi = np.round(px[idx]).astype(int); pyi = np.round(py[idx]).astype(int)
            good = mask[pyi, pxi].all(1)
            idx = idx[good]
            if not len(idx): continue
            V = bilinear(im, px[idx], py[idx])
            for row, i in zip(V, idx):
                e, kind = walk(row)
                if kind: meas[side][i].append((e, kind)); per_tile.append((i, 0 if side == 'left' else 1, tiles.index(t), e, kind))
    out = {}
    for side in ('left', 'right'):
        dev = np.full(n, np.nan); cnt = np.zeros(n, int); spr = np.full(n, np.nan); kd = np.zeros(n, int)
        for i in range(n):
            m = meas[side][i]
            if m:
                e = np.array([x[0] for x in m]); dev[i] = np.median(e); cnt[i] = len(e); spr[i] = e.max() - e.min()
                ks = [x[1] for x in m]; kd[i] = max(set(ks), key=ks.count)
        out[f'dev_{side}'] = dev; out[f'n_{side}'] = cnt; out[f'spread_{side}'] = spr; out[f'kind_{side}'] = kd
    out['hl'] = hl; out['hr'] = hr; out['per_tile'] = np.array(per_tile)
    np.savez(a.out, **out)
    print('stations measured left %d right %d of %d' % ((out['n_left'] > 0).sum(), (out['n_right'] > 0).sum(), n))
    for side in ('left', 'right'):
        d = out[f'dev_{side}']
        print(f'{side}: |dev| p50 {np.nanmedian(np.abs(d)):.2f} p90 {np.nanpercentile(np.abs(d), 90):.2f}')
        for r in runs(d, a.thr, a.min_len): print(f'  {side:5s} {r[0]:4d}-{r[1]:4d} ({r[1] - r[0] + 1:3d} st)  dev med {r[2]:+.2f} max {r[3]:+.2f}  kind {r[4]}')


def med_filter(d, w=5):
    n = len(d); h = w // 2; out = np.full(n, np.nan)
    for i in range(n):
        v = d[[(i + j) % n for j in range(-h, h + 1)]]; v = v[~np.isnan(v)]
        if len(v) >= 2: out[i] = np.median(v)
    return out


def runs(d, thr, min_len):
    f = med_filter(d); n = len(f); big = np.abs(np.nan_to_num(f)) > thr
    out = []; k = 0
    while k < n:
        if big[k]:
            j = k
            while j < n and (big[j] or (j + 1 < n and big[j + 1]) or (j + 2 < n and big[j + 2])): j += 1
            if j - k >= min_len:
                seg = f[k:j]; out.append((k, j - 1, float(np.nanmedian(seg)), float(seg[np.nanargmax(np.abs(seg))]), ''))
            k = j
        else: k += 1
    return out


if __name__ == '__main__':
    sys.exit(main())
