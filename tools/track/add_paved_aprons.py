"""Paved aprons beyond the painted edge as scenery.json `paved_zones` parts (18 Oct 2026, edge sweep).

    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/add_paved_aprons.py [--write]

Why: where fix_edges_paint.py pulled an edge in from a paved apron onto the painted line (T2 entry, right; Rahal
straight, left), the apron itself is still pavement in reality (Mustang onboard 8fGzs8Lnn0Q frames T2_Andretti and
Rahal_straight: pale pavement runs on past the white line) and must not turn into dirt in the sim. For each apron in
APRONS the paved width beyond the edge is measured per station on the Google z20 lap captures (the most central one,
registration shift applied): walking out from the edge, pavement = grey or olive-grey (red ~ green; the local dirt
is red > green by 15-25) or the green-blue apron paint; the apron ends at the first 0.8 m that is not pavement (or at --max m). The width is median-filtered over
9 stations, Gaussian-smoothed (sigma 3), capped 1.5 m short of the nearest scenery barrier (the rule of the other
runoff zones), at least 0.4 m, and tapered over 12 m at both ends. The part follows the format of the existing parts
(CONTRACTS 2b: center/left/right/profile_z/gap_left/gap_right/track_s): its inner side is the track edge (gap 0),
level with the road (the road's own cross-slope continued, clamped to 3 %).
"""
import argparse, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fix_edges_paint import tiles_and_images, sample_profiles  # noqa: E402
from sweep_paint import geometry  # noqa: E402
ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')

# turn label, side, first station, last station, why
# Tried and not added (18 Oct 2026): T3 outside-left 760-860 and T4 right 1030-1110 measured 0.4-0.5 m of pavement
# next to the edge (dirt or kerb paint first), so the onboard's pale aprons there do not start at the painted edge.
APRONS = [
    ('T2 entry apron', 'right', 372, 452, 'braking apron right of the white line before the Andretti hairpin (z20_s0425, onboard T2_Andretti)'),
    ('T9 teal apron', 'left', 2668, 2752, 'teal-painted paved apron outside the white line on the T9 (Rainey) entry; the edge was on its outer limit until fit_edges_spline.py put it on the line (18 Oct late evening, clean captures c20_b2650/b2725)'),
    ('Rahal apron', 'left', 2026, 2330, 'pale paved apron left of the painted line from the T6 exit (abutting the T6 zone at 2040.8 m) along the Rahal straight (z20_s2125/s2210, onboard Rahal_straight); 18 Oct evening: starts at the T6 exit since fix_rahal_left.py put the edge back on the line there'),
]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--write', action='store_true'); ap.add_argument('--max', type=float, default=10.0)
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n, sp = T['n'], T['spacing_m']; fr = T['profile']['fractions']; Z = T['profile']['z']
    C, NL, hl, hr = geometry(T); tiles, regs, img = tiles_and_images()
    walls = [p for b in SC['barriers'] for p in b['pts']]
    from scipy.ndimage import median_filter, gaussian_filter1d
    parts = []
    for turn, side, s0, s1, why in APRONS:
        sg = 1 if side == 'left' else -1; hw = hl if side == 'left' else hr; E = np.array(T[side])
        ks = list(range(s0, s1 + 1)); offs = np.arange(0.15, a.max + 1e-9, 0.1)
        P, _ = sample_profiles(C, NL, hw, sg, ks, offs, tiles, regs, img)
        w = np.full(len(ks), np.nan)
        for i, v in enumerate(P):
            if np.isnan(v[0, 0]): continue
            br = v.mean(1); sat = v.max(1) - v.min(1); warm = v[:, 0] - v[:, 2]
            teal = (v[:, 2] - v[:, 0] > 15) & (v[:, 1] - v[:, 0] > 15)          # painted apron (Laguna's green-blue)
            # concrete and dusty asphalt read R ~ G (B may be lower); the local dirt is R > G by 15-25
            pave = ((np.abs(v[:, 0] - v[:, 1]) < 12) & (br > 60) & (sat < 45)) | teal
            bad = np.convolve(~pave, np.ones(8), 'valid') >= 7        # 0.8 m of non-pavement
            j = int(np.argmax(bad)) if bad.any() else len(offs) - 1
            w[i] = offs[j]
        idx = np.arange(len(w)); ok = ~np.isnan(w); w = np.interp(idx, idx[ok], w[ok])
        w = gaussian_filter1d(median_filter(w, 9, mode='nearest'), 3, mode='nearest'); raw = np.median(w)
        for i, k in enumerate(ks):                                  # barrier cap
            e = E[k, :2]; nx, ny = sg * NL[k]
            for p in walls:
                d = (p[0] - e[0]) * nx + (p[1] - e[1]) * ny; lat = abs((p[0] - e[0]) * (-ny) + (p[1] - e[1]) * nx)
                if 0 < d < w[i] + 1.5 and lat < 3: w[i] = max(0.4, d - 1.5)
        w = np.maximum(w, 0.4); m = len(ks); print(f'  {turn}: measured width p50 {raw:.1f} m before the barrier cap')
        for i in range(m):
            d = min(i, m - 1 - i)
            if d < 12: t = d / 12; w[i] = 0.4 + (w[i] - 0.4) * (t * t * (3 - 2 * t))
        pc, pl, pr, prof, gl, gr = [], [], [], [], [], []
        for i, k in enumerate(ks):
            e = E[k]; nx, ny = sg * NL[k]
            x5, x6 = (fr[1] * -hw[k], fr[0] * -hw[k]) if side == 'left' else (-fr[5] * hw[k], -fr[6] * hw[k])
            za, zb = (Z[k][1], Z[k][0]) if side == 'left' else (Z[k][5], Z[k][6])
            slope = (zb - za) / (abs(x6 - x5) or 1)                  # per metre outward
            slope = max(-0.03, min(0.03, slope))
            outer = [e[0] + nx * w[i], e[1] + ny * w[i]]
            zc = [round(e[2] + slope * w[i] * (f + 1) / 2, 3) for f in fr]          # f=-1 at the zone's left
            if side == 'right':      # zone left = track edge, zone right = outer
                L_, R_ = [e[0], e[1], zc[0]], [outer[0], outer[1], zc[-1]]; gl.append(0.0); gr.append(99)
                prof.append(zc)
            else:                    # zone left = outer, zone right = track edge
                zc = zc[::-1]; L_, R_ = [outer[0], outer[1], zc[0]], [e[0], e[1], zc[-1]]; gl.append(99); gr.append(0.0)
                prof.append(zc)
            pl.append([round(v, 3) for v in L_]); pr.append([round(v, 3) for v in R_])
            pc.append([round((L_[0] + R_[0]) / 2, 3), round((L_[1] + R_[1]) / 2, 3), zc[3]])
        parts.append({'n': m, 'turn': turn, 'center': pc, 'left': pl, 'right': pr, 'profile_z': prof, 'gap_left': gl,
                      'gap_right': gr, 'track_s': [round(s0 * sp, 1), round(s1 * sp, 1)], 'note': why + ' (add_paved_aprons.py, 18 Oct 2026)'})
        print(f'{turn:16s} {side:5s} {s0}-{s1}: width p50 {np.median(w):.1f} m, min {w.min():.1f}, max {w.max():.1f}')
    if not a.write: print('dry run; --write to apply'); return
    names = {p['turn'] for p in parts}
    SC['paved_zones']['parts'] = [p for p in SC['paved_zones']['parts'] if p.get('turn') not in names] + parts
    json.dump(SC, open(os.path.join(OUT, 'scenery.json'), 'w'), separators=(',', ':')); print('wrote scenery.json')
    if isinstance(T.get('notes'), dict):
        T['notes']['paved_aprons'] = (f'18 Oct 2026: add_paved_aprons.py --max {a.max} --write: scenery.json paved_zones parts '
                                      + ', '.join(f"{p['turn']} {p['track_s']}" for p in parts))
        json.dump(T, open(os.path.join(OUT, 'track.json'), 'w'), separators=(',', ':')); print('noted in track.json')


if __name__ == '__main__':
    sys.exit(main())
