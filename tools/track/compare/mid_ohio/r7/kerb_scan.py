"""Mid-Ohio round 7, step 1: the kerb bands OUTSIDE the race edges, read from the clean z20 captures (reference only).

The owner's decision 2 (HANDOFF_OPUS_5_5.txt): the race edges are the asphalt-facing face of every kerb, so a kerb lies
in a band starting at the edge and running outward. Per 0.5 m along each edge and per 0.1 m outward from -0.4 to +2.4 m,
the capture pixel (capsample.Sampler: the capture where the point sits most central, with its registration) is
classified as red (kerb paint), white (kerb paint / line), yellow (kerb paint), or other (asphalt, grass, sand). A
station has a kerb where, over +-1.5 m along the edge, the paint share in the band 0.0..0.6 m beyond the edge is >= 0.5;
its kind is 'yellow' (yellow share dominant), 'redwhite' (red and white both present) or 'red' / 'white'. The band's
outer limit is the outermost offset whose paint share stays >= 0.4; the width is outer - inner (inner: the first paint
offset from -0.4 m). Runs: kerb stations merged across gaps up to 3 m, at least 5 m long. Each run: track s, lat/lon of
its ends on the edge, width (median, p25-p75), colour shares, a red outer band (yellow runs) and the band-centre line
(smoothed offset per 2 m) as lat/lon for scenery.kerbs_declared line_latlon. Every run is a CANDIDATE for the frames.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/mid_ohio/r7/kerb_scan.py \
        --pkg tools/track/out/mid_ohio_r7 --out tools/track/compare/mid_ohio/r7/kerb_scan.json
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from scipy.ndimage import uniform_filter1d, median_filter

HERE = os.path.dirname(os.path.abspath(__file__))
TT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, TT); sys.path.insert(0, os.path.join(TT, 'compare'))
import trackcfg  # noqa: E402
from capsample import Sampler  # noqa: E402

DS = 0.5
OFFS = np.round(np.arange(-0.4, 2.41, 0.1), 2)


def classify(rgb):
    """0 other, 1 red, 2 white, 3 yellow (8-bit RGB, (..., 3))."""
    R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.maximum(np.maximum(R, G), B); mn = np.minimum(np.minimum(R, G), B)
    c = np.zeros(R.shape, np.int8)
    red = (R > 110) & (R - G > 45) & (R - B > 40)
    yel = (R > 140) & (G > 110) & (R - B > 55) & (G - B > 40) & (np.abs(R - G) < 60)
    wht = (mn > 170) & (mx - mn < 40)
    c[red] = 1; c[wht] = 2; c[yel] = 3
    c[np.isnan(R)] = -1
    return c


def lonlat(cfg, x, y):
    lat0, lon0 = cfg['origin']; R = 6378137.0
    return lat0 + math.degrees(y / R), lon0 + math.degrees(x / (R * math.cos(math.radians(lat0))))


def scan(cfg, T, smp, side):
    C = np.array(T['center'])[:, :2]; E = np.array(T['left' if side > 0 else 'right'])[:, :2]
    n = len(C); sp = T['spacing_m']
    m = int(round(n * sp / DS)); u = np.arange(m) * DS / sp
    i0 = np.floor(u).astype(int) % n; i1 = (i0 + 1) % n; f = (u - np.floor(u))[:, None]
    Ce = C[i0] * (1 - f) + C[i1] * f; Ee = E[i0] * (1 - f) + E[i1] * f
    tg = np.roll(Ee, -1, 0) - np.roll(Ee, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    nrm = np.c_[-tg[:, 1], tg[:, 0]]
    sgn = np.sign(((Ee - Ce) * nrm).sum(1)); nrm *= sgn[:, None]           # outward
    X = Ee[:, 0][:, None] + nrm[:, 0][:, None] * OFFS[None, :]
    Y = Ee[:, 1][:, None] + nrm[:, 1][:, None] * OFFS[None, :]
    rgb, used = smp.sample(X, Y, group=np.repeat(np.arange(m), len(OFFS)).reshape(X.shape))
    cls = classify(rgb.reshape(m, len(OFFS), 3))
    return u * sp, Ee, nrm, cls, used.reshape(m, len(OFFS))


def runs_of(cfg, s, Ee, nrm, cls, used, tiles, side, WANT, force=None):
    win = int(round(1.5 / DS))
    band = (OFFS >= 0.0) & (OFFS <= 0.6)
    # per-station kind from the local (+-1.5 m) shares in the band: yellow, red/white blocks, or neither (a plain white
    # line, a concrete wall foot or an apron is no kerb)
    sh_ = {v: uniform_filter1d((cls[:, band] == v).mean(1).astype(float), 2 * win + 1, mode='wrap') for v in (1, 2, 3)}
    kind_st = np.where(sh_[3] >= 0.25, 3, np.where((sh_[1] >= 0.08) & (sh_[2] >= 0.08) & (sh_[1] + sh_[2] >= 0.35), 1, 0))
    on = kind_st == WANT
    if force is not None:
        # a stretch read as one run whatever the local shares say (confirmed on the capture window; the reason in the ledger)
        on = np.zeros(len(s), bool); on[int(force[0] / DS):int(force[1] / DS) + 1] = True
    # merge gaps <= 3 m, keep >= 5 m
    m = len(s); idx = np.where(on)[0]
    out = []
    if not len(idx):
        return out
    groups = []; a = idx[0]; b = idx[0]
    for k in idx[1:]:
        if (k - b) * DS <= 3.0:
            b = k
        else:
            groups.append((a, b)); a = b = k
    groups.append((a, b))
    if len(groups) > 1 and groups[0][0] == 0 and groups[-1][1] == m - 1:
        groups[0] = (groups[-1][0] - m, groups[0][1]); groups.pop()
    for a, b in groups:
        if (b - a) * DS < 5.0:
            continue
        kk = np.arange(a, b + 1) % m
        c = cls[kk]
        shares = {nm: float((c[:, band] == v).mean()) for nm, v in (('red', 1), ('white', 2), ('yellow', 3))}
        if shares['yellow'] > max(shares['red'], shares['white']):
            kind = 'yellow'
        elif shares['red'] > 0.08 and shares['white'] > 0.08:
            kind = 'redwhite'
        else:
            kind = 'red' if shares['red'] >= shares['white'] else 'white'
        # per-station inner / outer limits of the paint (smoothed over 1.5 m)
        P = uniform_filter1d((c >= 1).astype(float), 2 * win + 1, axis=0, mode='nearest')
        inner = np.full(len(kk), np.nan); outer = np.full(len(kk), np.nan)
        for j in range(len(kk)):
            ok = np.where(P[j] >= 0.4)[0]
            if len(ok):
                # the contiguous run of offsets that contains the band 0.0..0.6
                k0 = ok[0]; run = [k0]
                for q in ok[1:]:
                    if q == run[-1] + 1:
                        run.append(q)
                    else:
                        if OFFS[run[-1]] >= 0.0:
                            break
                        run = [q]
                inner[j] = OFFS[run[0]] - 0.05; outer[j] = OFFS[run[-1]] + 0.05
        w = outer - inner
        red_outer = None
        if kind == 'yellow':
            # a red band at the outer side of a yellow kerb (360 / N837 frames: "yellow with red outer band")
            ro = []
            for j in range(len(kk)):
                if np.isnan(outer[j]):
                    continue
                o = OFFS > outer[j] - 0.45
                o &= OFFS <= outer[j]
                if o.any():
                    ro.append(float((c[j, o] == 1).mean()))
            red_outer = float(np.mean(ro)) if ro else 0.0
        cen = (inner + outer) / 2
        good = ~np.isnan(cen)
        cen_s = np.interp(np.arange(len(kk)), np.where(good)[0], cen[good]) if good.any() else np.zeros(len(kk))
        cen_s = uniform_filter1d(median_filter(cen_s, 9, mode='nearest'), 9, mode='nearest')
        pts = Ee[kk] + nrm[kk] * cen_s[:, None]
        step = int(round(2.0 / DS))
        line = [lonlat(cfg, *p) for p in pts[::step]] + ([lonlat(cfg, *pts[-1])] if (len(pts) - 1) % step else [])
        ea = lonlat(cfg, *Ee[kk[0]]); eb = lonlat(cfg, *Ee[kk[-1]])
        tl = sorted({tiles[t]['name'] for t in used[kk][:, band].ravel() if t >= 0})
        out.append(dict(side='left' if side > 0 else 'right', s0=round(float(a * DS), 1) % round(m * DS, 1), s1=round(float(b * DS), 1),
                        length_m=round((b - a) * DS, 1), kind=kind, shares={k: round(v, 2) for k, v in shares.items()},
                        width_m=round(float(np.nanmedian(w)), 2), width_p25_p75=[round(float(np.nanpercentile(w, 25)), 2), round(float(np.nanpercentile(w, 75)), 2)],
                        inner_m=round(float(np.nanmedian(inner)), 2), centre_m=round(float(np.nanmedian(cen)), 2),
                        red_outer=None if red_outer is None else round(red_outer, 2),
                        a=[round(ea[0], 7), round(ea[1], 7)], b=[round(eb[0], 7), round(eb[1], 7)],
                        line_latlon=[[round(p[0], 7), round(p[1], 7)] for p in line], captures=tl,
                        # per-offset colour shares over the run (offsets OFFS, + beyond the edge): the yellow / red split
                        profile={nm: [round(float(v), 2) for v in (c == q).mean(0)] for nm, q in (('red', 1), ('white', 2), ('yellow', 3))}))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', default='mid_ohio')
    ap.add_argument('--pkg', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--force', action='append', default=[], help="side:s0:s1 read as one run (left|right)")
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    smp = Sampler(cfg, 'clean')
    res = []
    for side in (1, -1):
        s, Ee, nrm, cls, used = scan(cfg, T, smp, side)
        for want in (1, 3):
            res += runs_of(cfg, s, Ee, nrm, cls, used, smp.tiles, side, want)
        for f in a.force:
            sd, f0, f1 = f.split(':')
            if (sd == 'left') == (side > 0):
                rr = runs_of(cfg, s, Ee, nrm, cls, used, smp.tiles, side, 1, force=(float(f0), float(f1)))
                for r_ in rr:
                    r_['forced'] = True
                res = [r_ for r_ in res if not (r_['side'] == sd and r_['s0'] < float(f1) and r_['s1'] > float(f0))] + rr
    res.sort(key=lambda r: (r['side'], r['s0']))
    for r in res:
        print(f"{r['side']:5s} s {r['s0']:7.1f}-{r['s1']:7.1f} ({r['length_m']:5.1f} m) {r['kind']:8s} w {r['width_m']:.2f} "
              f"[{r['width_p25_p75'][0]:.2f}-{r['width_p25_p75'][1]:.2f}] inner {r['inner_m']:+.2f} centre {r['centre_m']:+.2f} "
              f"red/white/yellow {r['shares']['red']:.2f}/{r['shares']['white']:.2f}/{r['shares']['yellow']:.2f}"
              + (f" red outer {r['red_outer']:.2f}" if r['red_outer'] is not None else '') + f" {','.join(r['captures'])}")
    json.dump(dict(pkg=a.pkg, offsets=OFFS.tolist(), runs=res), open(a.out, 'w'), indent=1)
    print(f"{len(res)} runs -> {a.out}")


if __name__ == '__main__':
    main()
