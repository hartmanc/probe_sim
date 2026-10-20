"""Kerb strips detected on the clean z20 captures (2026 imagery, 0.117 m/px; reference only): along both edges of a
package's track, the painted block pattern of a kerb (alternating light / coloured blocks, 0.8-1.4 m each) found as
periodic luminance along lines parallel to the edge, from 1.5 m inside it to 1.5 m outside it.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/kerb_detect.py --track sonoma \
        --pkg tools/track/out/sonoma_r3 [--out tools/track/out/sonoma_r3/work/kerbs_detected.json]

Per station and side: for each lateral offset, the luminance along s (0.1 m samples) in a 6 m window, detrended; the
share of its variance at periods 1.6-2.8 m (a block pair) and its amplitude. A station has a kerb where some offset
has band share >= 0.45 and std >= 16 (8-bit luminance). The kerb's lateral extent is the run of offsets that pass,
its colour the mean of the darker blocks (red: R - B > 25; blue: B - R > 8; else grey). Runs: detections merged across
gaps up to 3 m, at least 6 m long. Prints each run with its track s, lat/lon ends, offsets, colour and the captures it
was read on. Every run is a CANDIDATE: confirm it on the capture (capwin.py) and Street View / the onboard before it
goes into the config (scenery.kerbs_declared).
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from scipy.ndimage import uniform_filter1d

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import trackcfg  # noqa: E402
from capsample import Sampler  # noqa: E402

DS = 0.1
OFFS = np.round(np.arange(-1.5, 1.51, 0.1), 2)     # + outside the edge


def frame(T):
    C = np.array(T['center'])[:, :2]; L = np.array(T['left'])[:, :2]; R = np.array(T['right'])[:, :2]
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    NL = np.c_[-tg[:, 1], tg[:, 0]]
    return C, NL, ((L - C) * NL).sum(1), -((R - C) * NL).sum(1)


def lonlat(cfg, x, y):
    lat0, lon0 = cfg['origin']; R = 6378137.0
    return lat0 + math.degrees(y / R), lon0 + math.degrees(x / (R * math.cos(math.radians(lat0))))


def detect(cfg, T, smp, side):
    C, NL, hl, hr = frame(T); n = len(C); sp = T['spacing_m']
    hw = hl if side > 0 else hr
    m = int(round(n * sp / DS))
    u = np.arange(m) * DS / sp                       # fractional station
    k0 = np.floor(u).astype(int) % n; k1 = (k0 + 1) % n; f = (u - np.floor(u))[:, None]
    c = C[k0] * (1 - f) + C[k1] * f
    nl = NL[k0] * (1 - f) + NL[k1] * f; nl /= np.linalg.norm(nl, axis=1, keepdims=True)
    e = hw[k0] * (1 - f[:, 0]) + hw[k1] * f[:, 0]
    lat = side * (e[:, None] + OFFS[None, :])
    X = c[:, :1] + lat * nl[:, :1]; Y = c[:, 1:] + lat * nl[:, 1:]
    grp = np.repeat(np.arange(m)[:, None], len(OFFS), 1)
    rgb, used = smp.sample(X, Y, grp)
    lum = rgb.mean(-1)
    valid = ~np.isnan(lum)
    lum = np.where(valid, lum, np.nanmean(lum))
    # periodic share in a 6 m window, per offset: band-pass by difference of box filters (period ~1.6-2.8 m)
    W = int(6 / DS)
    hp = lum - uniform_filter1d(lum, int(2.8 / DS), axis=0, mode='wrap')           # remove > 2.8 m trends
    bp = hp - (uniform_filter1d(hp, int(0.5 / DS), axis=0, mode='wrap') - hp) * 0  # keep
    lp = uniform_filter1d(hp, int(0.5 / DS), axis=0, mode='wrap')                 # remove < 0.5 m texture
    var_all = uniform_filter1d((lum - uniform_filter1d(lum, W, axis=0, mode='wrap')) ** 2, W, axis=0, mode='wrap')
    var_band = uniform_filter1d(lp ** 2, W, axis=0, mode='wrap')
    del bp
    share = var_band / np.maximum(var_all, 1e-3)
    std = np.sqrt(var_band)
    # the period must be regular: autocorrelation of lp at lag P (1.6..2.8 m) high, at lag P/2 negative
    det = (share >= 0.45) & (std >= 16) & valid
    lags = np.arange(int(1.6 / DS), int(2.8 / DS) + 1)
    best_ac = np.full(det.shape, -1.0)
    den = uniform_filter1d(lp * lp, W, axis=0, mode='wrap') + 1e-3
    for L in lags:
        ac = uniform_filter1d(lp * np.roll(lp, -L, axis=0), W, axis=0, mode='wrap') / den
        best_ac = np.maximum(best_ac, ac)
    det &= best_ac >= 0.45
    # per station (1 m): any offset detected
    per = det.reshape(n, -1, len(OFFS)).any(1) if m == n * int(round(sp / DS)) else None
    st_of = np.floor(u).astype(int) % n
    hit = np.zeros(n, bool); offs = [[] for _ in range(n)]
    for i in np.nonzero(det.any(1))[0]:
        hit[st_of[i]] = True
        offs[st_of[i]].extend(OFFS[det[i]].tolist())
    # colour of the darker blocks on the detected offsets
    col = np.full((n, 3), np.nan)
    for k in np.nonzero(hit)[0]:
        sel = (st_of == k)
        R_ = rgb[sel][:, det[sel].any(0)] if det[sel].any() else None
        if R_ is None or not len(R_):
            continue
        R_ = R_.reshape(-1, 3); R_ = R_[~np.isnan(R_).any(1)]
        if len(R_) < 4:
            continue
        lm = R_.mean(1)
        col[k] = R_[lm <= np.median(lm)].mean(0)
    del per
    return hit, offs, col, used.reshape(-1, len(OFFS))[:, len(OFFS) // 2], st_of


def runs(hit, n, gap=3, min_len=6):
    idx = np.nonzero(hit)[0]
    if not len(idx):
        return []
    out, a, b = [], idx[0], idx[0]
    for k in idx[1:]:
        if k - b <= gap + 1:
            b = k
        else:
            out.append((a, b)); a = b = k
    out.append((a, b))
    if len(out) > 1 and out[0][0] == 0 and out[-1][1] == n - 1:
        out[0] = (out[-1][0], out[0][1] + n); out.pop()
    return [(a, b) for a, b in out if b - a + 1 >= min_len]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True)
    ap.add_argument('--pkg', required=True)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    smp = Sampler(cfg)
    C, NL, hl, hr = frame(T); n = len(C); sp = T['spacing_m']
    res = []
    for side in (1, -1):
        hit, offs, col, used, st_of = detect(cfg, T, smp, side)
        hw = hl if side > 0 else hr
        for a_, b_ in runs(hit, n):
            ks = np.arange(a_, b_ + 1) % n
            o = [v for k in ks for v in offs[k]]
            cc = np.nanmean(col[ks], 0)
            colour = ('red' if cc[0] - cc[2] > 25 else 'blue' if cc[2] - cc[0] > 8 else 'grey') if np.isfinite(cc).all() else '?'
            caps = sorted({smp.tiles[i]['name'] for i in used[np.isin(st_of, ks)] if i >= 0})
            ends = []
            for k in (ks[0], ks[-1]):
                p = C[k] + NL[k] * side * hw[k]
                ends.append([round(v, 7) for v in lonlat(cfg, *p)])
            r = dict(side='left' if side > 0 else 'right', s0=round(a_ * sp, 1), s1=round(b_ * sp, 1), len_m=round((b_ - a_ + 1) * sp, 1),
                     off_min=round(float(np.percentile(o, 10)), 2), off_max=round(float(np.percentile(o, 90)), 2),
                     coverage=round(float(hit[ks].mean()), 2), colour=colour, rgb=[int(v) for v in np.nan_to_num(cc)],
                     a=ends[0], b=ends[1], captures=caps)
            res.append(r)
            print(f"{r['side']:5s} s {r['s0']:7.1f}-{r['s1']:7.1f} ({r['len_m']:5.1f} m, {r['coverage']:.0%}) off {r['off_min']:+.1f}..{r['off_max']:+.1f} "
                  f"{colour:5s} {r['rgb']} {', '.join(caps[:3])}")
    out = a.out or os.path.join(a.pkg, 'work', 'kerbs_detected.json')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(res, open(out, 'w'), indent=1)
    print(f'{len(res)} candidate runs -> {out}')


if __name__ == '__main__':
    main()
