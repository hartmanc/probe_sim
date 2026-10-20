"""Hillside terrace extent in track coordinates (Sonoma scenery round 6, 21 Oct 2026): the clean z20 captures resampled
on a straightened strip beside the track (station along x, lateral offset from the centreline up the page) with a
row-texture score, plus the lidar bare-earth profile across the strip. A terrace field is a distinct texture on the
captures: rows of seats every ~0.9 m parallel to the track, i.e. an intensity oscillation ACROSS the strip with a
0.85-1.45 m period (Sonoma: 1.13-1.24 m). Its lower and upper edges per station are where that score rises above / falls below a threshold
(the longest run of scoring cells, 6 m at least); the DEM profile gives the bank's foot and crest (slope over / under 0.12) where the
captures do not reach. Reference only: the imagery is never a texture, and the output stays out of git.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/terrace_measure.py --track sonoma \
        --pkg tools/track/out/sonoma_r3 --side left --s0 400 --s1 530 --lat0 5 --lat1 120 --out /tmp/t2.png [--step 10]

Prints one row per `--step` metres: s, captured span, lower / upper edge of the row texture (m from the centreline),
the DEM foot / crest of the bank, the track edge offset and the package's terrace span for reference.

Ray mode (`--json out.json`): the footprint a config `scenery.terraces` entry declares (`front`, `back`). Rays every
`--ray-step` m along a guide below the stand (the track at `--guide-lat` m from the centreline over s0..s1, or a lat/lon
polyline `--guide "lat,lon;lat,lon;..."`, or `--guide "xy:x,y;x,y"` in ENU metres, read on capwin.py), each perpendicular to the guide and uphill, sampled at
0.1 m: the row-texture band ratio in a sliding 6 m window (three neighbouring rays averaged; gaps under 3 m closed) gives the field's lower and
upper edge on the ray; where the field runs to the end of the captures, the upper edge is the DEM crest less 3 m (the
top walkway and fence; Sonoma's captured tops sit 3-5 m below the crest). Rays with no field, or a lower edge over 6 m off the median of
its 9 neighbours, are dropped, and so are fields outside the longest run of rays with one (gaps of 2
rays bridged); lower and upper edges are smoothed with a running median of 5. Writes {front, back (lat/lon), rays (per-ray table), run (the
row pitch: the median dominant period on the rays)}.
`--fill-osm <way id>`: rays at the stand's ends whose captures stop below the bank's crest with no field seen (the stand
may run on above the captured strip) and that cross that OSM outline take their lower edge from the nearest measured ray
(the walkway / fence line) and their upper edge at the outline's far side, capped by the DEM crest less 3 m: the outline
is the only plan evidence there (the onboard confirms the seating, not its plan); these rays are marked `osm_fill`.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import trackcfg  # noqa: E402
import captures as CAP  # noqa: E402

DS, DL = 0.5, 0.15          # strip resolution: m per pixel along the track, across it


def sample(tiles, mpp, X, Y):
    """RGB at world points X, Y (any shape) from the capture where each point sits most central; NaN where none."""
    out = np.full(X.shape + (3,), np.nan, np.float32)
    best = np.full(X.shape, np.inf)
    for t in tiles:
        with Image.open(t['path']) as im_:
            Wt, Ht = im_.size
        px = Wt / 2 + (X + t['dx'] - t['x']) / mpp
        py = Ht / 2 - (Y + t['dy'] - t['y']) / mpp
        inside = (px >= 1) & (px < Wt - 2) & (py >= 1) & (py < Ht - 2)
        sc = np.abs(px / Wt - 0.5) + np.abs(py / Ht - 0.5)
        take = inside & (sc < best)
        if not take.any():
            continue
        im = np.asarray(Image.open(t['path']).convert('RGB')).astype(np.float32)
        m = t['mask'](Ht, Wt)
        ok = take.copy()
        ok[take] = m[np.round(py[take]).astype(int), np.round(px[take]).astype(int)]
        if ok.any():
            out[ok] = CAP.bilinear(im, px[ok], py[ok])
            best[ok] = sc[ok]
    return out


def row_score(G, valid):
    """Share of the across-strip spectral power (detrended, 6 m windows) in the 0.85-1.45 m period (Sonoma: 1.13-1.24 m) band, per pixel."""
    H, W = G.shape
    win = int(round(6.0 / DL))
    f = np.fft.rfftfreq(win, DL)
    band = (f >= 1 / 1.45) & (f <= 1 / 0.85)
    rest = f >= 1 / 4.0
    S = np.full((H, W), np.nan, np.float32)
    g = np.where(valid, G, np.nan)
    hann = np.hanning(win)
    for y0 in range(0, H - win, win // 4):
        blk = g[y0:y0 + win]
        okc = np.isfinite(blk).all(0)
        if not okc.any():
            continue
        b = blk[:, okc]
        b = b - b.mean(0)
        P = np.abs(np.fft.rfft(b * hann[:, None], axis=0)) ** 2
        r = P[band].sum(0) / (P[rest].sum(0) + 1e-6)
        col = np.full(W, np.nan, np.float32); col[okc] = r
        S[y0 + win // 2 - win // 8:y0 + win // 2 + win // 8 + 1] = col
    # smooth along the track (4 m) to read a field, not a single bright row
    k = int(round(4.0 / DS))
    Sf = np.where(np.isfinite(S), S, 0); Wf = np.isfinite(S).astype(float)
    Sf = ndi.uniform_filter1d(Sf, k, axis=1); Wf = ndi.uniform_filter1d(Wf, k, axis=1)
    return np.where(Wf > 0.3, Sf / np.maximum(Wf, 1e-6), np.nan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True)
    ap.add_argument('--pkg', required=True)
    ap.add_argument('--side', choices=['left', 'right'], required=True)
    ap.add_argument('--s0', type=float, required=True)
    ap.add_argument('--s1', type=float, required=True)
    ap.add_argument('--lat0', type=float, default=5.0)
    ap.add_argument('--lat1', type=float, default=120.0)
    ap.add_argument('--step', type=float, default=10.0)
    ap.add_argument('--thr', type=float, default=0.45, help='row-texture score threshold')
    ap.add_argument('--out', default='')
    ap.add_argument('--json', default='', help='ray mode: write the measured front / back lines here')
    ap.add_argument('--guide', default='', help='ray mode: guide polyline "lat,lon;lat,lon;..." below the stand')
    ap.add_argument('--guide-lat', type=float, default=None, help='ray mode: guide at this lateral offset (track mode)')
    ap.add_argument('--reach', type=float, default=90.0, help='ray mode: ray length uphill from the guide, m')
    ap.add_argument('--ray-step', type=float, default=3.0)
    ap.add_argument('--fill-osm', default='', help='ray mode: OSM way id filling the rays the captures do not reach (see the docstring)')
    a = ap.parse_args()
    if a.json:
        return rays(a)
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C = np.array(T['center'])[:, :2]; Lf = np.array(T['left'])[:, :2]; Rt = np.array(T['right'])[:, :2]
    n, sp = T['n'], T['spacing_m']
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    NL = np.c_[-tg[:, 1], tg[:, 0]]
    sgn = 1.0 if a.side == 'left' else -1.0
    s = np.arange(a.s0, a.s1 + 1e-6, DS)
    lat = np.arange(a.lat1, a.lat0 - 1e-6, -DL)          # far at the top
    fi = (s / sp) % n; i0 = np.floor(fi).astype(int); fr = fi - i0; i1 = (i0 + 1) % n
    Cs = C[i0] * (1 - fr[:, None]) + C[i1] * fr[:, None]
    Ns = NL[i0] * (1 - fr[:, None]) + NL[i1] * fr[:, None]; Ns /= np.linalg.norm(Ns, axis=1, keepdims=True)
    X = Cs[None, :, 0] + sgn * Ns[None, :, 0] * lat[:, None]
    Y = Cs[None, :, 1] + sgn * Ns[None, :, 1] * lat[:, None]
    tiles = CAP.capture_list(cfg, 'clean')
    rgb = sample(tiles, cfg['captures']['mpp'], X, Y)
    valid = np.isfinite(rgb).all(2)
    G = np.nan_to_num(rgb).mean(2)
    S = row_score(G, valid)
    # lidar bare earth across the strip
    lgp = os.path.join(os.path.dirname(HERE), 'cache', cfg['id'], 'lidar_grids.npz')
    lg = np.load(lgp) if os.path.exists(lgp) else None
    DEM = None
    if lg is not None:
        box = lg['box']; D = lg['DEM']
        c = np.clip((X - box[0]).astype(int), 0, D.shape[1] - 1); r = np.clip((Y - box[1]).astype(int), 0, D.shape[0] - 1)
        DEM = ndi.uniform_filter1d(np.nan_to_num(D[r, c]), 9, axis=0)
    # the package's terraces on this strip: lateral span per station (from their row quads)
    pk = np.zeros((len(lat), len(s)), bool)
    scp = os.path.join(a.pkg, 'scenery.json')
    if os.path.exists(scp):
        from shapely.geometry import Polygon
        from shapely import contains_xy
        from shapely.ops import unary_union
        polys = []
        for tr in json.load(open(scp)).get('terraces', []):
            u = np.array(tr['dir']); h = tr['run'] / 2
            for r in tr['rows']:
                if r.get('pts'):
                    P = np.array(r['pts'])[:, :2]; Nn = np.array(r['nrm'])
                    polys.append(Polygon(np.r_[P - Nn * h, (P + Nn * h)[::-1]]).buffer(0))
                else:
                    A_, B_ = np.array(r['a']), np.array(r['b'])
                    polys.append(Polygon([A_ - u * h, B_ - u * h, B_ + u * h, A_ + u * h]))
        if polys:
            pk = contains_xy(unary_union(polys).buffer(0.3), X, Y)
    edge = np.linalg.norm((Lf if a.side == 'left' else Rt)[i0] - C[i0], axis=1)
    # image: captures with the score in red where over the threshold; ticks every 10 m along, every 10 m across
    im = np.nan_to_num(rgb).astype(np.uint8)
    hot = np.nan_to_num(S) > a.thr
    im[hot] = (0.55 * im[hot] + 0.45 * np.array([255, 40, 40])).astype(np.uint8)
    pil = Image.fromarray(im); d = ImageDraw.Draw(pil)
    for k, sv in enumerate(s):
        if abs(sv / 10 - round(sv / 10)) < 1e-6:
            d.line([(k, pil.height - 12), (k, pil.height)], fill=(255, 255, 0))
            if abs(sv / 50 - round(sv / 50)) < 1e-6:
                d.text((k + 2, pil.height - 24), f's{sv:.0f}', fill=(255, 255, 0))
    for lv in np.arange(np.ceil(a.lat0 / 10) * 10, a.lat1, 10):
        y = int(round((a.lat1 - lv) / DL)); d.line([(0, y), (10, y)], fill=(0, 255, 255)); d.text((12, y - 6), f'{lv:.0f}', fill=(0, 255, 255))
    pil.save(a.out)
    print(f'{a.out}: {len(s)} x {len(lat)} px ({DS} m along, {DL} m across); {a.side} side, lateral from the centreline')
    print(' s     edge  captured        rows lo-hi (texture)   DEM foot-crest (slope 0.12)          package terrace')
    for sv in np.arange(a.s0, a.s1 + 1e-6, a.step):
        k = int(round((sv - a.s0) / DS)); kk = slice(max(0, k - 4), k + 5)
        col = np.nanmean(np.where(valid[:, kk], S[:, kk], np.nan), axis=1)
        cap = np.where(valid[:, k])[0]
        capt = f'{lat[cap.max()]:5.1f}-{lat[cap.min()]:5.1f}' if len(cap) else '   none    '
        on = np.nan_to_num(col) > a.thr
        lab, nl = ndi.label(on)
        txt = '      -      '
        if nl:
            sizes = ndi.sum(on, lab, range(1, nl + 1)); j = int(np.argmax(sizes)) + 1
            ys = np.where(lab == j)[0]
            if sizes[j - 1] * DL >= 3:
                txt = f'{lat[ys.max()]:5.1f}-{lat[ys.min()]:5.1f}'
                if ys.min() == 0 or (len(cap) and ys.min() <= cap.min() + 2):
                    txt += '+'          # runs to the end of the captures: the upper edge is beyond them
        dem = '     -     '
        if DEM is not None:
            z = DEM[::-1, k]; lv = lat[::-1]
            sl = np.gradient(z, DL)
            sl = ndi.uniform_filter1d(sl, int(3 / DL))
            up = np.where(sl > 0.12)[0]
            if len(up):
                lo_ = lv[up.min()]; run_ = up[up >= up.min()]
                # the first continuous climbing stretch (gaps under 4 m allowed)
                br = np.where(np.diff(run_) > int(4 / DL))[0]
                hi_ = lv[run_[br[0]] if len(br) else run_.max()]
                dem = f'{lo_:5.1f}-{hi_:5.1f} ({z[up.min()]:.1f}->{z[run_[br[0]] if len(br) else run_.max()]:.1f} m)'
        pp = np.where(pk[:, k])[0]
        pkg = f'{lat[pp.max()]:5.1f}-{lat[pp.min()]:5.1f}' if len(pp) else '-'
        print(f'{sv:6.0f} {edge[k]:5.1f}  {capt}  {txt:22s} {dem:34s} {pkg}')


def rays(a):
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C = np.array(T['center'])[:, :2]; n, sp = T['n'], T['spacing_m']
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    NL = np.c_[-tg[:, 1], tg[:, 0]]
    lg = np.load(os.path.join(os.path.dirname(HERE), 'cache', cfg['id'], 'lidar_grids.npz'))
    box = lg['box']; D = lg['DEM']

    def dem(X, Y):
        c = np.clip((X - box[0]).astype(int), 0, D.shape[1] - 1); r = np.clip((Y - box[1]).astype(int), 0, D.shape[0] - 1)
        return np.nan_to_num(D[r, c])
    # guide polyline (world) resampled at the ray step, with its normal
    if a.guide:
        if a.guide.startswith('xy:'):      # ENU metres, read off a capwin.py window
            G = np.array([[float(v) for v in q.split(',')] for q in a.guide[3:].split(';')])
        else:
            ll = np.array([[float(v) for v in q.split(',')] for q in a.guide.split(';')])
            G = np.array([cfg.enu(la, lo) for la, lo in ll], float)
    else:
        sgn = 1.0 if a.side == 'left' else -1.0
        ss = np.arange(a.s0, a.s1 + 1e-6, 1.0); ii = np.round(ss / sp).astype(int) % n
        G = C[ii] + sgn * NL[ii] * (a.guide_lat if a.guide_lat is not None else a.lat0)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(G, axis=0), axis=1))]
    m = np.arange(0, seg[-1] + 1e-6, a.ray_step)
    P = np.c_[np.interp(m, seg, G[:, 0]), np.interp(m, seg, G[:, 1])]
    tgv = np.gradient(P, axis=0); tgv /= np.linalg.norm(tgv, axis=1, keepdims=True)
    N = np.c_[-tgv[:, 1], tgv[:, 0]]
    # uphill: the side where the DEM 30 m out is higher on most rays
    up = np.sign(np.median(dem(P[:, 0] + N[:, 0] * 30, P[:, 1] + N[:, 1] * 30) - dem(P[:, 0] - N[:, 0] * 30, P[:, 1] - N[:, 1] * 30)))
    N = N * (up if up != 0 else 1.0)
    tt = np.arange(-5.0, a.reach + 1e-6, 0.1)
    X = P[:, None, 0] + N[:, None, 0] * tt[None]; Y = P[:, None, 1] + N[:, None, 1] * tt[None]
    rgb = sample(CAP.capture_list(cfg, 'clean'), cfg['captures']['mpp'], X, Y)
    valid = np.isfinite(rgb).all(2); g = np.nan_to_num(rgb).mean(2)
    win = 60; f = np.fft.rfftfreq(win, 0.1); band = (f >= 1 / 1.45) & (f <= 1 / 0.85); rest = f >= 1 / 4.0; hann = np.hanning(win)
    R = np.full(X.shape, np.nan); PER = np.full(X.shape, np.nan)
    for j in range(0, len(tt) - win, 5):
        blk = g[:, j:j + win]; ok = valid[:, j:j + win].all(1)
        b = blk - blk.mean(1, keepdims=True)
        Pw = np.abs(np.fft.rfft(b * hann[None], axis=1)) ** 2
        r = Pw[:, band].sum(1) / (Pw[:, rest].sum(1) + 1e-6)
        R[ok, j + win // 2 - 2:j + win // 2 + 3] = r[ok, None]
        pk = 1 / f[band][np.argmax(Pw[:, band], axis=1)]
        PER[ok, j + win // 2 - 2:j + win // 2 + 3] = pk[ok, None]
    Rs = ndi.uniform_filter1d(np.nan_to_num(R), 3, axis=0, mode='nearest')
    Z = dem(X, Y); Z = ndi.uniform_filter1d(Z, 15, axis=1)
    sl = ndi.uniform_filter1d(np.gradient(Z, 0.1, axis=1), 30, axis=1)
    rows, lo, hi, per = [], np.full(len(P), np.nan), np.full(len(P), np.nan), []
    for k in range(len(P)):
        on = Rs[k] > a.thr
        on = ndi.binary_closing(on, np.ones(31, bool)) | on       # aisles, walkways and dropouts under 3 m join the field
        lab, nl = ndi.label(on)
        cap = np.where(valid[k])[0]
        crest = np.nan
        clim = np.where(sl[k] > 0.12)[0]
        if len(clim):
            run_ = clim; br = np.where(np.diff(run_) > 40)[0]
            crest = tt[run_[br[0]] if len(br) else run_.max()]
        txt = 'no field'
        if nl:
            sizes = ndi.sum(on, lab, range(1, nl + 1)); j = int(np.argmax(sizes)) + 1
            ys = np.where(lab == j)[0]
            if sizes[j - 1] * 0.1 >= 6:     # a stand is at least 6 m deep
                lo[k] = tt[ys.min()]; hi[k] = tt[ys.max()]
                cut = len(cap) and ys.max() >= cap.max() - 40
                if cut and np.isfinite(crest) and crest - 3 > hi[k]:
                    hi[k] = crest - 3
                if len(ys) >= 80:       # row pitch: the zero-padded spectral peak over the field on this ray (8 m or more)
                    seg_ = g[k, ys.min():ys.max() + 1]; seg_ = (seg_ - seg_.mean()) * np.hanning(len(seg_))
                    fz = np.fft.rfftfreq(4096, 0.1); Pz = np.abs(np.fft.rfft(seg_, 4096)) ** 2
                    bz = (fz >= 1 / 1.45) & (fz <= 1 / 0.85)
                    per.append(float(1 / fz[bz][np.argmax(Pz[bz])]))
                txt = f'field {tt[ys.min()]:5.1f}-{tt[ys.max()]:5.1f}{" cut" if cut else ""}'
        rows.append(dict(m=round(float(m[k]), 1), captured=[round(float(tt[cap.min()]), 1), round(float(tt[cap.max()]), 1)] if len(cap) else None,
                         field=txt, crest=None if not np.isfinite(crest) else round(float(crest), 1),
                         lo=None if not np.isfinite(lo[k]) else round(float(lo[k]), 1), hi=None if not np.isfinite(hi[k]) else round(float(hi[k]), 1)))
    # the stand: the longest run of rays with a field (gaps of up to 2 rays bridged); isolated reads elsewhere are dropped
    fin = np.isfinite(lo)
    labr, nr = ndi.label(ndi.binary_closing(fin, np.ones(5, bool)) | fin)
    if nr > 1:
        big = 1 + int(np.argmax(ndi.sum(fin, labr, range(1, nr + 1))))
        for k in np.where(fin & (labr != big))[0]:
            rows[k]['dropped'] = 'outside the longest run of rays with a field'
            lo[k] = np.nan; hi[k] = np.nan
    # a ray whose lower edge is off its neighbours' by over 6 m read something else (a fence, a truck, the track): dropped
    ok_ = np.isfinite(lo)
    if ok_.sum() >= 5:
        idx_ = np.where(ok_)[0]
        med = ndi.median_filter(lo[idx_], 9, mode='mirror')
        bad = idx_[np.abs(lo[idx_] - med) > 6.0]
        for k in bad:
            rows[k]['dropped'] = 'lower edge off its neighbours by over 6 m'
        lo[bad] = np.nan; hi[bad] = np.nan
    if a.fill_osm:
        import xml.etree.ElementTree as ET
        from shapely.geometry import LineString, Polygon
        root = ET.parse(os.path.join(os.path.dirname(HERE), 'cache', cfg['id'], cfg['osm_file'])).getroot()
        nodes = {nd.get('id'): (float(nd.get('lat')), float(nd.get('lon'))) for nd in root.iter('node')}
        way = next(w for w in root.iter('way') if w.get('id') == str(a.fill_osm))
        poly = Polygon([cfg.enu(*nodes[nd.get('ref')]) for nd in way.iter('nd')]).buffer(0)
        meas = np.where(np.isfinite(lo))[0]
        for k in range(len(P)):
            if np.isfinite(lo[k]) or not len(meas):
                continue
            capk = np.where(valid[k])[0]
            crest_k = rows[k]['crest']
            if crest_k is None or (len(capk) and tt[capk.max()] >= crest_k - 3):
                continue                       # the captures saw this ray up to the crest: no field there
            seg = poly.intersection(LineString([P[k] + N[k] * tt[0], P[k] + N[k] * tt[-1]]))
            if seg.is_empty:
                continue
            ds = [float((np.array(q) - P[k]) @ N[k]) for g_ in getattr(seg, 'geoms', [seg]) for q in g_.coords]
            j = meas[np.argmin(np.abs(meas - k))]
            lo_k = max(lo[j], min(ds)); hi_k = min(max(ds), crest_k - 3)
            if hi_k - lo_k >= 6:
                lo[k], hi[k] = lo_k, hi_k
                rows[k].update(lo=round(float(lo_k), 1), hi=round(float(hi_k), 1), osm_fill=f'OSM {a.fill_osm}')
    keep = np.where(np.isfinite(lo))[0]
    if not len(keep):
        raise SystemExit('no terrace field on any ray')
    k0, k1 = keep.min(), keep.max()
    idx = np.arange(k0, k1 + 1)
    lo_i = np.interp(idx, keep, lo[keep]); hi_i = np.interp(idx, keep, hi[keep])
    lo_s = ndi.median_filter(lo_i, 5, mode='nearest'); hi_s = ndi.median_filter(hi_i, 5, mode='nearest')
    F = P[idx] + N[idx] * lo_s[:, None]; B = P[idx] + N[idx] * hi_s[:, None]
    lat0, lon0 = cfg['origin']; Re = 6378137.0
    to_ll = lambda Q: [[round(lat0 + math.degrees(y / Re), 7), round(lon0 + math.degrees(x / (Re * math.cos(math.radians(lat0)))), 7)] for x, y in Q]  # noqa: E731
    run = float(np.median(per)) if per else None
    json.dump(dict(front=to_ll(F), back=to_ll(B), run=None if run is None else round(run, 2), rays=rows), open(a.json, 'w'), indent=1)
    for r_ in rows:
        print(r_)
    print(f'{a.json}: {len(idx)} rays kept ({k0}..{k1} of {len(P)}), depth {np.min(hi_s - lo_s):.1f}-{np.max(hi_s - lo_s):.1f} m, '
          f'front {np.min(lo_s):.1f}-{np.max(lo_s):.1f} m from the guide, row pitch {run} m')


if __name__ == '__main__':
    main()
