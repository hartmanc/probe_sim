"""Measure a wall, tyre wall or fence line on the clean z20 captures (2026 imagery, 0.117 m/px; reference only) and print
it as a lat/lon polyline for the track config (scenery.declared_walls). The method of the 20 Oct 2026 pit-straight walls,
as a tool.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/wall_measure.py --track sonoma \
        --pkg tools/track/out/sonoma_r3 --guide x0,y0;x1,y1;... [--ll] [--search 1.5] [--feature bright|dark] [--step 10]
    ... --edge left --lo 1700 --hi 1900 --off 1.0,4.0          (a wall parallel to the edge: guide = the edge + offset)

Guide: a rough polyline drawn on capwin.py (ENU x,y; with --ll lat,lon pairs). Every 0.5 m along it, the luminance
profile across it (+-search m, 0.06 m samples, one capture per profile) is read; the wall is the centre of the brightest
0.25-1.2 m band (concrete top, `bright`) or the darkest (tyre stack, `dark`), accepted when its contrast with the
profile median is at least 25 (bright) / 20 (dark). Accepted offsets: 9-sample median, then a 3 m Gaussian; gaps
interpolated when under 6 m, else the line is split. Prints coverage, the residual of the raw picks about the smooth
line (rms, p90) and the polyline every `step` m (and its end points) as lat/lon. With --edge: per station the offset
from the edge, its median and spread, and the polyline.
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from scipy.ndimage import gaussian_filter1d, median_filter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import trackcfg  # noqa: E402
from capsample import Sampler  # noqa: E402


def lonlat(cfg, x, y):
    lat0, lon0 = cfg['origin']; R = 6378137.0
    return lat0 + math.degrees(y / R), lon0 + math.degrees(x / (R * math.cos(math.radians(lat0))))


def resample(P, step):
    d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.arange(0, d[-1] + 1e-9, step)
    return np.c_[np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], s


def pick(prof, offs, feature):
    """centre offset of the strongest 0.25-1.2 m band; contrast"""
    best = (None, 0.0)
    med = np.nanmedian(prof)
    for w in (0.25, 0.4, 0.6, 0.9, 1.2):
        k = max(1, int(round(w / (offs[1] - offs[0]))))
        c = np.convolve(prof, np.ones(k) / k, 'same')
        c = (c - med) if feature == 'bright' else (med - c)
        i = int(np.nanargmax(c))
        if c[i] > best[1] + 2:
            best = (offs[i], float(c[i]))
    return best


def measure(smp, P, search, feature):
    Q, s = resample(P, 0.5)
    t = np.gradient(Q, axis=0); t /= np.linalg.norm(t, axis=1, keepdims=True); nrm = np.c_[-t[:, 1], t[:, 0]]
    offs = np.arange(-search, search + 1e-9, 0.06)
    X = Q[:, :1] + offs[None, :] * nrm[:, :1]; Y = Q[:, 1:] + offs[None, :] * nrm[:, 1:]
    grp = np.repeat(np.arange(len(Q))[:, None], len(offs), 1)
    rgb, _ = smp.sample(X, Y, grp)
    lum = rgb.mean(-1)
    off = np.full(len(Q), np.nan); con = np.zeros(len(Q))
    thr = 25 if feature == 'bright' else 20
    for i in range(len(Q)):
        if np.isnan(lum[i]).any():
            continue
        o, c = pick(lum[i], offs, feature)
        if o is not None and c >= thr:
            off[i], con[i] = o, c
    return Q, s, nrm, off, con


def smooth(off, s, gap_m=6.0):
    ok = np.isfinite(off)
    if ok.sum() < 5:
        return None, ok
    o = off.copy()
    o[ok] = median_filter(off[ok], 9, mode='nearest')
    idx = np.arange(len(o))
    filled = np.interp(idx, idx[ok], o[ok])
    # gaps longer than gap_m stay gaps
    gap = np.zeros(len(o), bool)
    run = 0
    for i in range(len(o)):
        run = run + 1 if not ok[i] else 0
        gap[i] = False
    # mark long gaps
    i = 0
    while i < len(o):
        if not ok[i]:
            j = i
            while j < len(o) and not ok[j]:
                j += 1
            if (s[min(j, len(s) - 1)] - s[i]) > gap_m:
                gap[i:j] = True
            i = j
        else:
            i += 1
    sm = gaussian_filter1d(filled, 3.0 / 0.5, mode='nearest')
    sm[gap] = np.nan
    return sm, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True); ap.add_argument('--pkg', required=True)
    ap.add_argument('--guide', help='x,y;x,y;... (ENU) or lat,lon;... with --ll')
    ap.add_argument('--ll', action='store_true')
    ap.add_argument('--sguide', help='s,lat;s,lat;... in track coordinates (s m along the lap, lat m, + left of the centre), '
                                     'as read off capstrip.py; densified every 2 m of s')
    ap.add_argument('--edge', choices=['left', 'right']); ap.add_argument('--lo', type=float); ap.add_argument('--hi', type=float)
    ap.add_argument('--off', default='0.5,4.0', help='with --edge: offset range beyond the edge, m')
    ap.add_argument('--search', type=float, default=1.5)
    ap.add_argument('--feature', default='bright', choices=['bright', 'dark'])
    ap.add_argument('--step', type=float, default=10.0)
    ap.add_argument('--name', default='wall')
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    smp = Sampler(cfg)
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C = np.array(T['center'])[:, :2]; n, sp = T['n'], T['spacing_m']
    tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True); NL = np.c_[-tg[:, 1], tg[:, 0]]
    if a.sguide:
        q = np.array([tuple(map(float, v.split(','))) for v in a.sguide.split(';')])
        ss = np.arange(q[0, 0], q[-1, 0] + 1e-9, 2.0)
        if ss[-1] < q[-1, 0]: ss = np.r_[ss, q[-1, 0]]
        la = np.interp(ss, q[:, 0], q[:, 1])
        k = np.round(ss / sp).astype(int) % n
        P = C[k] + NL[k] * la[:, None]
        search = a.search
    elif a.edge:
        E = np.array(T[a.edge])[:, :2]; sg = 1 if a.edge == 'left' else -1
        o0, o1 = map(float, a.off.split(','))
        ks = np.arange(int(a.lo / sp), int(a.hi / sp) + 1) % n
        P = E[ks] + NL[ks] * sg * (o0 + o1) / 2
        search = (o1 - o0) / 2
    else:
        pts = [tuple(map(float, q.split(','))) for q in a.guide.split(';')]
        P = np.array([cfg.enu(*q) if a.ll else q for q in pts], float)
        search = a.search
    Q, s, nrm, off, con = measure(smp, P, search, a.feature)
    sm, ok = smooth(off, s)
    if sm is None:
        print(f'{a.name}: no {a.feature} band found ({int(np.isfinite(off).sum())} picks of {len(off)})'); return
    W = Q + nrm * np.nan_to_num(sm)[:, None]
    res = (off - sm)[ok & np.isfinite(sm)]
    print(f'{a.name}: {len(Q) * 0.5:.0f} m guided, {ok.mean():.0%} of profiles picked ({a.feature}, contrast p50 {np.median(con[ok]):.0f}); '
          f'raw picks about the smooth line rms {np.sqrt(np.mean(res ** 2)):.2f} m, p90 {np.percentile(np.abs(res), 90):.2f} m; '
          f'shift from the guide p50 {np.nanmedian(sm):+.2f} m')
    if a.edge:
        # offset from the edge per station
        E = np.array(T[a.edge])[:, :2]
        d = []
        for w in W[np.isfinite(sm)]:
            i = int(np.argmin(((C - w) ** 2).sum(1)))
            d.append(abs(((w - C[i]) * NL[i]).sum()) - abs(((E[i] - C[i]) * NL[i]).sum()))
        d = np.array(d)
        print(f'   offset beyond the {a.edge} edge: p10 {np.percentile(d, 10):.2f}, p50 {np.median(d):.2f}, p90 {np.percentile(d, 90):.2f} m')
    # polyline per continuous run, every step m
    runs, cur = [], []
    for i in range(len(W)):
        if np.isfinite(sm[i]):
            cur.append(i)
        elif cur:
            runs.append(cur); cur = []
    if cur:
        runs.append(cur)
    out = []
    for r in runs:
        if (len(r) - 1) * 0.5 < 4:
            continue
        r = np.array(r)
        keep = list(r[::max(1, int(a.step / 0.5))])
        if keep[-1] != r[-1]:
            keep.append(r[-1])
        ll = [tuple(round(v, 7) for v in lonlat(cfg, *W[i])) for i in keep]
        out.append(ll)
        print(f'   run {s[r[0]]:.0f}-{s[r[-1]]:.0f} m along the guide: ' + ', '.join(f'({la}, {lo})' for la, lo in ll))
    json.dump(out, open('/tmp/wall_measure_last.json', 'w'))


if __name__ == '__main__':
    main()
