"""Front straight, left edge along the pit wall (18 Oct 2026, edge sweep).
    uv run --python 3.12 --with numpy,pillow python -I tools/track/fix_front_straight_left.py [--fit 3350,40] [--ref 3470,40] [--write]

Why: the left half-width wandered 3 m against the straight pit wall: the edge sat on the wall (gap -0.9..-0.3 m to the
scenery.json `pitwall` polyline, i.e. the sim's wall stood on the track) over stations 3360-3430 and 2-2.5 m inside it
from 3470 on. The 3360-3440 stretch was measured on the z20_s3400 capture, whose registration (-1.8, +0.9 m) is ~1.3 m
off its neighbours' (-0.9, 0); the paint detector also stopped at the wall's shadow. On the z20_s3485 capture (good
registration) the edge lies at the wall's shadow line, and the pit wall and the outer concrete wall run parallel
(19.5 m apart, 3380-3500). So the left edge over --fit is set at the pit wall's lateral minus a constant gap, the
median gap over --ref (the stretch on the well-registered captures), the wall polyline's 2 m noise smoothed by a
Gaussian of 4 stations, blended over 15 stations at both ends. Over --clamp, where the pit-wall polyline converges on the
track at the pit-entry nose (it reads 0.6-0.9 m inside the edge there), the half-width runs straight from the first
station of --fit to the fitted stretch instead (the painted road is straight; the nose is left as an open question). Profile columns are re-evaluated at the moved
positions from each station's cross-section quadratic (as fix_edge_waves.py); the centre is untouched.
"""
import argparse, json, math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fix_edge_waves import quad_eval  # noqa: E402
ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')


def rng(a, b, n):
    return list(range(a, n)) + list(range(0, b + 1)) if b < a else list(range(a, b + 1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--write', action='store_true')
    ap.add_argument('--fit', default='3355,40'); ap.add_argument('--clamp', default='3355,3420'); ap.add_argument('--clear', type=float, default=0.6); ap.add_argument('--ref', default='3470,40'); ap.add_argument('--blend', type=int, default=15)
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n = T['n']; fr = T['profile']['fractions']; Z = T['profile']['z']; C, L, R = T['center'], T['left'], T['right']

    def nl(k):
        a_, b_ = C[(k - 1) % n], C[(k + 1) % n]; tx, ty = b_[0] - a_[0], b_[1] - a_[1]; l = math.hypot(tx, ty) or 1
        return -ty / l, tx / l

    def hw(k):
        nx, ny = nl(k); c = C[k]
        return (L[k][0] - c[0]) * nx + (L[k][1] - c[1]) * ny, -((R[k][0] - c[0]) * nx + (R[k][1] - c[1]) * ny)

    wall = [p for b in SC['barriers'] if b['kind'] == 'pitwall' for p in b['pts']]

    def wall_lat(k):
        nx, ny = nl(k); c = C[k]; best = None
        for p in wall:
            d = (p[0] - c[0]) * nx + (p[1] - c[1]) * ny; along = abs((p[0] - c[0]) * (-ny) + (p[1] - c[1]) * nx)
            if 0 < d < 25 and along < 2 and (best is None or d < best): best = d
        return best

    f0, f1 = [int(x) for x in a.fit.split(',')]; r0, r1 = [int(x) for x in a.ref.split(',')]
    ks = rng(f0, f1, n); wl = [wall_lat(k) for k in ks]
    if any(w is None for w in wl): print('pit wall not found at', [k for k, w in zip(ks, wl) if w is None][:10]); return 1
    ref = set(rng(r0, r1, n)); gaps = sorted(w - hw(k)[0] for k, w in zip(ks, wl) if k in ref); g0 = gaps[len(gaps) // 2]
    sm = []
    for i in range(len(ks)):                                     # Gaussian, sigma 4 stations, inside the stretch
        acc = ws = 0.0
        for d in range(-12, 13):
            j = i + d
            if 0 <= j < len(ks): w_ = math.exp(-0.5 * (d / 4.0) ** 2); acc += wl[j] * w_; ws += w_
        sm.append(acc / ws)
    # where the pit wall converges on the track (pit-entry nose) a constant gap would pinch the road: there the edge
    # only keeps --clear m off the wall
    c0, c1 = [int(x) for x in a.clamp.split(',')]; clamp = set(rng(c0, c1, n))
    tgt = [None if k in clamp else sm[i] - g0 for i, k in enumerate(ks)]
    tgt[0] = hw(ks[0])[0]
    idx = [i for i, v in enumerate(tgt) if v is not None]
    for i in range(len(tgt)):                                    # straight half-width across the nose stretch
        if tgt[i] is None:
            lo_ = max(j for j in idx if j < i); hi_ = min(j for j in idx if j > i)
            tgt[i] = tgt[lo_] + (tgt[hi_] - tgt[lo_]) * (i - lo_) / (hi_ - lo_)
    m = len(ks); tg2 = []
    for i in range(m):
        acc = ws = 0.0
        for d in range(-12, 13):
            j = i + d
            if 0 <= j < m: w_ = math.exp(-0.5 * (d / 4.0) ** 2); acc += tgt[j] * w_; ws += w_
        tg2.append(acc / ws)
    # pit-lane / paved-zone junctions on the left edge keep their edge, 15-station blend (as fix_edge_waves.py)
    import numpy as np
    from fix_edges_paint import junction_stations
    J = sorted(junction_stations(T, SC)['left'])
    def jgaps():
        E = np.array(L)[:, :2]; out = []
        for part in SC['pit_lane']['parts']:
            for key, gaps in (('left', part['gap_left']), ('right', part['gap_right'])):
                for i_, g in enumerate(gaps):
                    if g is not None and g <= 0.3:
                        q = np.array(part[key][i_][:2]); d = np.hypot(*(E - q).T); k_ = int(np.argmin(d))
                        if k_ in set(ks) and d[k_] < 1.5: out.append((k_, round(float(d[k_]), 3)))
        return sorted(set(out))
    before = jgaps()
    new = {}
    for i, k in enumerate(ks):
        d = min(i, m - 1 - i); t = 1.0 if d >= a.blend else (d / a.blend) ** 2 * (3 - 2 * d / a.blend)
        if J:
            dj = min(min(abs(k - p_), n - abs(k - p_)) for p_ in J)
            if dj < 15: t *= dj / 15
        new[k] = (1 - t) * hw(k)[0] + t * tg2[i]
    moves = [new[k] - hw(k)[0] for k in ks]
    print(f'pit-wall gap median over {a.ref}: {g0:.2f} m; left half-width moved p50 {sorted(moves)[m // 2]:+.2f} '
          f'min {min(moves):+.2f} max {max(moves):+.2f}')
    print('  ' + ' '.join(f'{k}:{hw(k)[0]:.2f}->{new[k]:.2f}' for k in ks[::20]))
    if not a.write: print('dry run; --write to apply'); return 0
    for k in ks:
        hl_o, hr_ = hw(k); hl_n = new[k]; nx, ny = nl(k); c = C[k]
        xs_o = [(-f) * hl_o if f < 0 else -f * hr_ for f in fr]; xs_n = [(-f) * hl_n if f < 0 else -f * hr_ for f in fr]
        zn = [quad_eval(xs_o, Z[k], x) for x in xs_n]; zn[fr.index(0)] = Z[k][fr.index(0)]; Z[k] = [round(z, 3) for z in zn]
        L[k] = [round(c[0] + nx * hl_n, 3), round(c[1] + ny * hl_n, 3), Z[k][0]]
        R[k][2] = Z[k][-1]
    after = jgaps()
    print('pit-lane junction gaps on the left edge inside the fit (station, m) before:', before[:12], '... n', len(before))
    print('                                                               after: ', after[:12], '... n', len(after),
          ' max |change|', max([abs(x[1] - y[1]) for x, y in zip(before, after)] or [0]))
    if isinstance(T.get('notes'), dict):
        T['notes']['front_straight_left'] = (f'18 Oct 2026: fix_front_straight_left.py --fit {a.fit} --clamp {a.clamp} --ref {a.ref} --blend {a.blend} --write: '
            f'left edge at a constant {g0:.2f} m from the pit-wall polyline (median over the ref stretch, outside z20_s3400), straight across the nose stretch; '
            f'pit-lane junction stations protected ({len(J)})')
    json.dump(T, open(os.path.join(OUT, 'track.json'), 'w'), separators=(',', ':')); print('wrote track.json')
    return 0


if __name__ == '__main__':
    sys.exit(main())
