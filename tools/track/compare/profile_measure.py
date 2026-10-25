"""Cross-profiles of the clean z20 captures (reference only) outward from a package edge (Sonoma round 14D, 25 Oct 2026):
per station, luminance from -1 m (on the course) to --reach m beyond the fitted edge, every 0.04 m, split into runs of
light (> asphalt + --contrast) and dark samples. Prints the runs and writes --json (evidence). Used for the T11
hairpin outside (the white band in front of the pit road: the tyre wall and the white wall) and the T4 wall head.

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/profile_measure.py --track sonoma \
        --pkg public/tracks/sonoma --side left --lo 3630 --hi 3760 --step 5 --reach 9 --json out.json
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE)); sys.path.insert(0, HERE)
import trackcfg  # noqa: E402
from capsample import Sampler  # noqa: E402


def runs(mask, U):
    out = []; i = 0
    while i < len(U):
        j = i
        while j + 1 < len(U) and mask[j + 1] == mask[i]: j += 1
        out.append((bool(mask[i]), round(float(U[i]), 2), round(float(U[j] + 0.04), 2))); i = j + 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', required=True); ap.add_argument('--pkg', required=True); ap.add_argument('--side', required=True)
    ap.add_argument('--lo', type=int, required=True); ap.add_argument('--hi', type=int, required=True)
    ap.add_argument('--step', type=int, default=5); ap.add_argument('--reach', type=float, default=9.0)
    ap.add_argument('--contrast', type=float, default=40.0); ap.add_argument('--min-run', type=float, default=0.25)
    ap.add_argument('--json')
    a = ap.parse_args()
    cfg = trackcfg.load(a.track)
    T = json.load(open(os.path.join(a.pkg, 'track.json')))
    C = np.array(T['center'])[:, :2]; E = np.array(T[a.side])[:, :2]; sp = T['spacing_m']
    S = Sampler(cfg)
    U = np.arange(-1.0, a.reach + 1e-9, 0.04)
    rows = []
    for k in range(a.lo, a.hi + 1, a.step):
        nrm = E[k] - C[k]; nrm /= np.linalg.norm(nrm)
        P = E[k][None, :] + U[:, None] * nrm[None, :]
        rgb, used = S.sample(P[:, 0], P[:, 1], group=np.zeros(len(U), int))
        if np.isnan(rgb).any():
            rows.append(dict(k=k, s=round(k * sp, 1), runs=None)); continue
        lum = rgb.mean(1); asph = float(np.median(lum[U < -0.2]))
        light = lum > asph + a.contrast
        rr = [r for r in runs(light, U) if r[2] - r[1] >= a.min_run or not r[0]]
        lr = [dict(a=r[1], b=r[2], w=round(r[2] - r[1], 2)) for r in rr if r[0]]
        rows.append(dict(k=k, s=round(k * sp, 1), asphalt_lum=round(asph, 1), light_runs=lr,
                         lum_profile=[int(v) for v in lum[::5]], capture=S.tiles[int(used[0])]['name'] if used[0] >= 0 else None))
        print(f"k {k} s {k*sp:.0f} asph {asph:.0f}: " + '  '.join(f"[{r['a']:+.2f},{r['b']:+.2f}]" for r in lr))
    if a.json:
        json.dump(dict(pkg=a.pkg, side=a.side, lo=a.lo, hi=a.hi, step_m=0.04, profile_every=0.2, rows=rows), open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
