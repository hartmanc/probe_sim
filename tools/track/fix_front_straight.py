"""Front straight, owner 18 Oct 2026 (Mustang onboard 8fGzs8Lnn0Q): "None of these humps exist here ... There is pavement
that runs up to the wall, with the right side of track painted at an offset from the wall."
    python3 -I tools/track/fix_front_straight.py [--write] [--zone-only]
(A) is not idempotent at its blend ends (the fit range 3380..3575 wraps past the lap end to station 15), so after any
later edge change use --zone-only to rebuild the shoulder from the current edge without re-fitting the edge.
(A) track.json: the right half-width over stations 3380..3575 is replaced by its least-squares quadratic in s (the
    painted line keeps a steady offset from the straight concrete wall; the detector put a 1 m bulge at ~3460),
    blended over 15 stations at both ends; profile columns re-evaluated at the moved positions, centre untouched.
(B) scenery.json: a paved zone on the right of the front straight from the T11 exit (station 3330) to past the S/F
    bridge (station 45), from the painted edge to 1.5 m short of the nearest concrete wall (the rule of the other
    runoff zones), level with the road (the road's own cross-slope continued), tapered over 12 m at both ends.
    Same part format as the existing paved_zones parts (CONTRACTS 2b).
"""
import argparse, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fix_edge_waves import quad_eval
ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--write', action='store_true')
    ap.add_argument('--zone-only', action='store_true', help='rebuild the shoulder zone (B) from the current edge; leave track.json alone')
    ap.add_argument('--fit', type=str, default='3380,3575'); ap.add_argument('--zone', type=str, default='3330,45')
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n, sp = T['n'], T['spacing_m']; fr = T['profile']['fractions']; Z = T['profile']['z']; C, L, R = T['center'], T['left'], T['right']

    def rnormal(k):
        a_, b_ = C[(k - 1) % n], C[(k + 1) % n]; tx, ty = b_[0] - a_[0], b_[1] - a_[1]; l = math.hypot(tx, ty) or 1
        return ty / l, -tx / l                                       # right normal

    def hw(k):
        nx, ny = rnormal(k); c = C[k]
        hl = -((L[k][0] - c[0]) * nx + (L[k][1] - c[1]) * ny); hr = (R[k][0] - c[0]) * nx + (R[k][1] - c[1]) * ny
        return hl, hr

    # ---------------- (A) right edge fit
    lo, hi = [int(x) for x in a.fit.split(',')]
    ks = list(range(lo, hi + 1)); xs = [float(k - lo) for k in ks]; ys = [hw(k % n)[1] for k in ks]
    walls_pre = [p for b in SC['barriers'] if b['kind'] == 'concrete' for p in b['pts']]
    def gap_pre(k):
        e = R[k % n]; nx, ny = rnormal(k % n); best = None
        for p in walls_pre:
            d = (p[0] - e[0]) * nx + (p[1] - e[1]) * ny; lat = abs((p[0] - e[0]) * (-ny) + (p[1] - e[1]) * nx)
            if 0 < d < 30 and lat < 3 and (best is None or d < best): best = d
        return best
    gp = [gap_pre(k) for k in ks]; gmed = sorted(g for g in gp if g is not None)[len([g for g in gp if g is not None]) // 2]
    # target: the painted edge keeps the median offset from the wall; where no wall point is found keep the data
    raw = {k: (hw(k % n)[1] + (g - gmed) if g is not None else hw(k % n)[1]) for k, g in zip(ks, gp)}
    fit = {}
    for k in ks:                                                  # 3-station Gaussian along the wall polyline noise
        acc = 0.0; wsum = 0.0
        for d in range(-9, 10):
            q = k + d
            if lo <= q <= hi: w_ = math.exp(-0.5 * (d / 3.0) ** 2); acc += raw[q] * w_; wsum += w_
        fit[k] = acc / wsum
    print(f'(A) wall gap median {gmed:.2f} m; found at {sum(1 for g in gp if g is not None)}/{len(ks)} stations')
    bl = 15
    for k in ks:
        d = min(k - lo, hi - k); t = 1.0 if d >= bl else d / bl
        fit[k] = (1 - t) * hw(k % n)[1] + t * fit[k]
    moved = max(abs(fit[k] - hw(k % n)[1]) for k in ks)
    print(f'(A) right half-width fitted over {lo}..{hi}: max move {moved:.2f} m; at 3420/3460/3500/3540: '
          + ' '.join(f'{hw(k)[1]:.2f}->{fit[k]:.2f}' for k in (3420, 3460, 3500, 3540)))
    if a.write and not a.zone_only:
        for k in ks:
            kk = k % n; hl, hr_old = hw(kk); hr = fit[k]; nx, ny = rnormal(kk); c = C[kk]
            xs_old = [(-f) * hl if f < 0 else -f * hr_old for f in fr]; xs_new = [(-f) * hl if f < 0 else -f * hr for f in fr]
            znew = [quad_eval(xs_old, Z[kk], x) for x in xs_new]; znew[fr.index(0)] = Z[kk][fr.index(0)]
            Z[kk] = [round(z, 3) for z in znew]
            R[kk] = [round(c[0] + nx * hr, 3), round(c[1] + ny * hr, 3), Z[kk][-1]]

    # ---------------- (B) paved shoulder zone on the right
    z0, z1 = [int(x) for x in a.zone.split(',')]
    stations = list(range(z0, n)) + list(range(0, z1 + 1)) if z1 < z0 else list(range(z0, z1 + 1))
    walls = [p for b in SC['barriers'] if b['kind'] == 'concrete' for p in b['pts']]

    def wall_gap(k):
        e = R[k]; nx, ny = rnormal(k); best = None
        for p in walls:
            d = (p[0] - e[0]) * nx + (p[1] - e[1]) * ny; lat = abs((p[0] - e[0]) * (-ny) + (p[1] - e[1]) * nx)
            if 0 < d < 30 and lat < 3 and (best is None or d < best): best = d
        return best

    gaps = [wall_gap(k) for k in stations]
    last = next((g for g in gaps if g is not None), 4.0)
    for i, g in enumerate(gaps):
        if g is None: gaps[i] = last
        else: last = g
    # smooth the width a little (the OSM wall is a 2 m polyline) and taper the ends
    w = [max(1.0, min(12.0, g - 1.5)) for g in gaps]
    w = [sum(w[max(0, i - 4):i + 5]) / len(w[max(0, i - 4):i + 5]) for i in range(len(w))]
    m = len(stations)
    for i in range(m):
        d = min(i, m - 1 - i)
        if d < 12: t = d / 12; w[i] = 0.4 + (w[i] - 0.4) * (t * t * (3 - 2 * t))
    pts_c, pts_l, pts_r, prof, gl, gr = [], [], [], [], [], []
    for i, k in enumerate(stations):
        e = R[k]; nx, ny = rnormal(k)
        # road cross-slope at the right edge, continued onto the shoulder (clamped)
        hl, hr = hw(k); x5, x6 = -fr[5] * hr, -fr[6] * hr
        slope = (Z[k][6] - Z[k][5]) / (x6 - x5) if abs(x6 - x5) > 1e-6 else 0.0
        slope = max(-0.03, min(0.03, -slope))                      # per metre outward (right)
        zc = [round(e[2] + slope * w[i] * (f + 1) / 2, 3) for f in fr]
        pts_l.append([round(e[0], 3), round(e[1], 3), zc[0]])
        pts_r.append([round(e[0] + nx * w[i], 3), round(e[1] + ny * w[i], 3), zc[-1]])
        pts_c.append([round(e[0] + nx * w[i] / 2, 3), round(e[1] + ny * w[i] / 2, 3), zc[3]])
        prof.append(zc); gl.append(0.0); gr.append(99)
    part = {'n': m, 'turn': 'Front straight', 'center': pts_c, 'left': pts_l, 'right': pts_r, 'profile_z': prof,
            'gap_left': gl, 'gap_right': gr, 'track_s': [round(z0 * sp, 1), round(z1 * sp, 1)],
            'note': 'paved shoulder to the right-hand wall, T11 exit to past the S/F bridge (owner, Mustang onboard, 18 Oct 2026)'}
    print(f'(B) shoulder zone: {m} points, width p50 {sorted(w)[m // 2]:.1f} m, min {min(w):.1f}, max {max(w):.1f}; wall gap p50 {sorted(gaps)[m // 2]:.1f} m')
    if a.write:
        SC['paved_zones']['parts'] = [p for p in SC['paved_zones']['parts'] if p.get('turn') != 'Front straight'] + [part]
        if isinstance(T.get('notes'), dict):
            T['notes']['front_straight_right'] = (f'18 Oct 2026: fix_front_straight.py --fit {a.fit} --zone {a.zone} --write: right edge at '
                                                  f'the median {gmed:.2f} m gap to the concrete wall; paved shoulder zone to the wall')
        if not a.zone_only: json.dump(T, open(os.path.join(OUT, 'track.json'), 'w'), separators=(',', ':'))
        json.dump(SC, open(os.path.join(OUT, 'scenery.json'), 'w'), separators=(',', ':'))
        print('wrote scenery.json' + ('' if a.zone_only else ' and track.json'))
    else:
        print('dry run; --write to apply')


if __name__ == '__main__':
    sys.exit(main())
