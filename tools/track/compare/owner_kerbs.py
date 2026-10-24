"""Kerb bands just outside the owner's red edge (Buttonwillow round 10, 23 Oct 2026). The owner draws the asphalt edge on
the track side of every kerb ("I am trying to stay to the inside of the kerb, but I am not drawing around the kerb"), and
the kerb is part of the racing surface, so the package edge is his red moved outward by the band's width where the
captures show a band beside it (spline.owner_edges kerb_inside, with the measured width).

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/owner_kerbs.py --track buttonwillow \
        --owner tools/track/tracks/buttonwillow/owner/r10/merged.json --pkg tools/track/out/bw_r9e \
        --out tools/track/tracks/buttonwillow/owner/r10/kerbs.json [--offs -0.8,2.4]

The edge frame is the package's centre with his red as both edges (gaps interpolated along s). compare/kerb_detect.py's
periodic block pattern is searched over --offs from his red (+ outward); per station the detected offsets are clustered
(0.21 m joins) and the cluster nearest his line is the band; a run (gaps <= 3 m, >= --min-len m) is a kerb zone when its
band starts within --touch m of his red (the band beside his edge, not a block line elsewhere). Per run: the stations of
the package, the band's inner / outer offset from his red (median, p10 / p90), its width (outer - inner, median), the
colour of the darker blocks, the captures, and the lat / lon of its ends on his red. Every run is a candidate the round's
outline page shows; the config cites this file.
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import trackcfg  # noqa: E402
import kerb_detect as KD  # noqa: E402
from capsample import Sampler  # noqa: E402


def red_frame(T, M):
    C = np.array(T['center'])[:, :2]; n = len(C); sp = T['spacing_m']
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NL = np.c_[-t[:, 1], t[:, 0]]
    hw = {}
    for side, sg in (('left', 1), ('right', -1)):
        v = np.full(n, np.nan)
        for x, y, s in M[side + '_enu_xys']:
            k = int(round(s / sp)) % n; v[k] = sg * float(((np.array([x, y]) - C[k]) * NL[k]).sum())
        ok = ~np.isnan(v); x = np.flatnonzero(ok)
        hw[side] = np.interp(np.arange(n), x, v[ok], period=n)
        hw[side + '_drawn'] = ok
    return C, NL, hw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True); ap.add_argument('--owner', required=True); ap.add_argument('--pkg', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--offs', default='-0.8,2.4'); ap.add_argument('--touch', type=float, default=0.5)
    ap.add_argument('--min-len', type=int, default=6)
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    T0 = json.load(open(os.path.join(a.pkg, 'track.json'))); M = json.load(open(a.owner))
    C, NL, hw = red_frame(T0, M); n = len(C); sp = T0['spacing_m']
    T = dict(center=[[float(x), float(y), 0.0] for x, y in C], n=n, spacing_m=sp,
             left=[[float(x), float(y)] for x, y in C + hw['left'][:, None] * NL],
             right=[[float(x), float(y)] for x, y in C - hw['right'][:, None] * NL])
    lo, hi = (float(v) for v in a.offs.split(','))
    KD.OFFS = np.round(np.arange(lo, hi + 0.01, 0.1), 2)
    smp = Sampler(cfg)
    res = []
    for side, sg in (('left', 1), ('right', -1)):
        hit, offs, col, used, st_of = KD.detect(cfg, T, smp, sg)
        band = np.full((n, 2), np.nan)
        for k in range(n):
            o = sorted(set(offs[k]))
            if not o:
                continue
            cl = [[o[0], o[0]]]
            for v in o[1:]:
                if v - cl[-1][1] <= 0.21: cl[-1][1] = v
                else: cl.append([v, v])
            c = min(cl, key=lambda c: abs(c[0]) if c[0] >= 0 else abs(c[0]) * 0.5 if c[1] >= 0 else abs(c[1]) + 1)
            band[k] = (c[0] - 0.05, c[1] + 0.05)
        near = ~np.isnan(band[:, 0]) & (band[:, 0] <= a.touch) & (band[:, 1] >= -0.2)
        for a_, b_ in KD.runs(near, n, gap=3, min_len=a.min_len):
            ks = np.arange(a_, b_ + 1) % n; m = near[ks]
            bi, bo = band[ks][m, 0], band[ks][m, 1]
            cc = np.nanmean(col[ks], 0)
            colour = ('red' if cc[0] - cc[2] > 25 else 'blue' if cc[2] - cc[0] > 8 else 'grey') if np.isfinite(cc).all() else '?'
            caps = sorted({smp.tiles[i]['name'] for i in used[np.isin(st_of, ks)] if i >= 0})
            ends = [[round(v, 7) for v in KD.lonlat(cfg, *(C[k] + NL[k] * sg * hw[side][k]))] for k in (ks[0], ks[-1])]
            r = dict(side=side, lo=int(a_), hi=int(b_ % n), s0=round(a_ * sp, 1), s1=round((b_ % n) * sp, 1), len_m=round((b_ - a_ + 1) * sp, 1),
                     coverage=round(float(m.mean()), 2), inner=round(float(np.median(bi)), 2), inner_p10_p90=[round(float(v), 2) for v in np.percentile(bi, [10, 90])],
                     outer=round(float(np.median(bo)), 2), outer_p10_p90=[round(float(v), 2) for v in np.percentile(bo, [10, 90])],
                     width=round(float(np.median(bo - np.maximum(bi, 0.0))), 2), red_drawn=round(float(hw[side + '_drawn'][ks].mean()), 2),
                     colour=colour, rgb=[int(v) for v in np.nan_to_num(cc)], a=ends[0], b=ends[1], captures=caps)
            res.append(r)
            print(f"{side:5s} st {r['lo']:5d}-{r['hi']:5d} ({r['len_m']:5.1f} m, {r['coverage']:.0%}) band {r['inner']:+.2f}..{r['outer']:+.2f} m from his red "
                  f"(inner p10/p90 {r['inner_p10_p90']}), width {r['width']:.2f} m, {colour} {', '.join(caps[:2])}")
    json.dump(dict(src=f'owner_kerbs.py --owner {a.owner} --pkg {a.pkg} --offs {a.offs} --touch {a.touch}', runs=res), open(a.out, 'w'), indent=1)
    print(f'{len(res)} kerb runs beside his red -> {a.out}')


if __name__ == '__main__':
    main()
