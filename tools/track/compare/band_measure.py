"""A light band beside the owner's red (Sonoma round 14B part 1b, coordinator decision 3, 24 Oct 2026: the T11 hairpin
outside, where his red steps in where a light band begins and out where it ends). Per station of the package, the clean
captures sampled along the normal outward from his red (-1 .. +4 m, 0.04 m steps, one capture per profile); the band =
the brightest contiguous run starting within --touch m of his red whose luminance stands --contrast over the asphalt
inside his red; its inner / outer offsets from his red, width, colour (median RGB). At each end of the band: his red just
beyond the band (where it steps back out) against the band's outer edge, to tell whether the band's outer edge continues
the adjacent asphalt edge (within 0.3 m). Writes --json (evidence; the captures are reference only).

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/band_measure.py --track sonoma \
        --pkg tools/track/out/sonoma_r14b --side left --lo 3630 --hi 3750 --json tools/track/compare/sonoma/round14b/hairpin_band.json
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import trackcfg  # noqa: E402
import edges_spline  # noqa: E402
from capsample import Sampler  # noqa: E402


def main():
    import build_track as BT
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True); ap.add_argument('--pkg', required=True); ap.add_argument('--side', required=True)
    ap.add_argument('--lo', type=int, required=True); ap.add_argument('--hi', type=int, required=True)
    ap.add_argument('--touch', type=float, default=0.4); ap.add_argument('--contrast', type=float, default=25.0)
    ap.add_argument('--json')
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C = np.array(T['center'])[:, :2]; n = len(C)
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NL = np.c_[-t[:, 1], t[:, 0]]
    cw = trackcfg.remap_stations(cfg, n, float(np.linalg.norm(np.roll(C, -1, 0) - C, axis=1).sum()), C=C)
    sg = 1 if a.side == 'left' else -1
    red = {}
    for w in BT.owner_windows(cfg, cw, n=n):
        if w['side'] == a.side:
            w = dict(w, kerb_inside=[])   # his red as drawn (no kerb shift)
            for k, v in edges_spline.owner_readings(C, NL, w, n).items():
                if a.lo - 30 <= k <= a.hi + 30:
                    red[k] = v
    S = Sampler(cfg)
    U = np.arange(-1.0, 4.0 + 1e-9, 0.04)
    rows = []
    for k in range(a.lo, a.hi + 1):
        if k not in red:
            continue
        P = C[k][None, :] + sg * (red[k] + U)[:, None] * NL[k][None, :]
        rgb, used = S.sample(P[:, 0], P[:, 1], group=np.zeros(len(U), int))
        if np.isnan(rgb).any():
            continue
        lum = rgb.mean(1)
        asph = float(np.median(lum[U < -0.3]))
        hi_ = lum > asph + a.contrast
        # the run of bright samples starting nearest his red (within --touch)
        start = next((i for i in range(len(U)) if hi_[i] and abs(U[i]) <= a.touch), None)
        if start is None:
            rows.append(dict(k=k, red=round(red[k], 3), band=None)); continue
        i0 = start
        while i0 > 0 and hi_[i0 - 1]: i0 -= 1
        i1 = start
        while i1 < len(U) - 1 and (hi_[i1 + 1] or (i1 + 2 < len(U) and hi_[i1 + 2])): i1 += 1
        col = np.median(rgb[i0:i1 + 1], axis=0)
        rows.append(dict(k=k, red=round(red[k], 3), inner=round(float(U[i0]), 2), outer=round(float(U[i1] + 0.04), 2),
                         width=round(float(U[i1] + 0.04 - U[i0]), 2), rgb=[int(v) for v in col], asphalt_lum=round(asph, 1),
                         band_lum=round(float(lum[i0:i1 + 1].mean()), 1), capture=S.tiles[int(used[0])]['name'] if used[0] >= 0 else None))
    band = [r for r in rows if r.get('band', 1) is not None and 'width' in r]
    ks = [r['k'] for r in band]
    out = dict(pkg=a.pkg, side=a.side, lo=a.lo, hi=a.hi, rows=rows)
    if band:
        W = np.array([r['width'] for r in band]); O = np.array([r['red'] + r['outer'] for r in band])
        out['band'] = dict(stations=[min(ks), max(ks)], n=len(band), width_median=round(float(np.median(W)), 2),
                           width_p10=round(float(np.percentile(W, 10)), 2), width_p90=round(float(np.percentile(W, 90)), 2),
                           rgb_median=[int(v) for v in np.median(np.array([r['rgb'] for r in band]), axis=0)])
        # ends: his red beyond the band (the step back out) against the band's outer edge (half-width from the centre)
        ends = []
        for k_end, step in ((min(ks), -1), (max(ks), +1)):
            outer = [r['red'] + r['outer'] for r in band if abs(r['k'] - k_end) <= 3]
            beyond = [red[k] for k in range(k_end + step, k_end + step * 6, step) if k in red]
            if outer and beyond:
                ends.append(dict(end=k_end, band_outer_halfwidth=round(float(np.median(outer)), 3),
                                 red_beyond_halfwidth=round(float(np.median(beyond[:3])), 3),
                                 diff=round(float(np.median(outer) - np.median(beyond[:3])), 3)))
        out['ends'] = ends
        print(f"band {a.side} stations {min(ks)}-{max(ks)} ({len(band)} profiles): width median {out['band']['width_median']} m "
              f"(p10 {out['band']['width_p10']}, p90 {out['band']['width_p90']}), rgb {out['band']['rgb_median']}")
        for e in ends:
            print(f"  end {e['end']}: band outer {e['band_outer_halfwidth']} m vs his red beyond {e['red_beyond_halfwidth']} m: {e['diff']:+.3f} m")
    if a.json:
        json.dump(out, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
