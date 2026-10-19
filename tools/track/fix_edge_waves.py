"""Remove detector notches and waves from track.json edges (owner, 18 Oct 2026: "is this wavy edge on the real track? I
don't think so" at the T9 approach and on the left after T11).
    python3 -I tools/track/fix_edge_waves.py [--notch 0.35] [--notch-len 25] [--sigma 5] [--slope 0.10] [--write]
Per side: (1) notches, runs shorter than --notch-len stations where the half-width departs from a 41-station running
median by more than --notch m, are replaced by that median (a seam or a shadow read as the painted line); (2) a Gaussian
of --sigma stations and a slope limit of --slope m per station make the edge as smooth as a painted line is; long
widenings (aprons) survive both. Stations where a pit-lane or paved-zone part touches the track edge keep their value,
blended over 15 stations, so the junctions stay closed. Profile columns are re-evaluated at the moved lateral
positions from each station's cross-section quadratic; the centre is untouched.
"""
import argparse, json, math, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')


def quad_eval(xs, ys, x):
    sx = [sum(v ** p for v in xs) for p in range(5)]; sy = [sum(y * v ** p for v, y in zip(xs, ys)) for p in range(3)]
    A = [[sx[0], sx[1], sx[2]], [sx[1], sx[2], sx[3]], [sx[2], sx[3], sx[4]]]; b = sy[:]
    for i in range(3):
        piv = max(range(i, 3), key=lambda r: abs(A[r][i])); A[i], A[piv] = A[piv], A[i]; b[i], b[piv] = b[piv], b[i]
        for r in range(i + 1, 3):
            f = A[r][i] / A[i][i]
            for c_ in range(i, 3): A[r][c_] -= f * A[i][c_]
            b[r] -= f * b[i]
    co = [0, 0, 0]
    for i in (2, 1, 0): co[i] = (b[i] - sum(A[i][j] * co[j] for j in range(i + 1, 3))) / A[i][i]
    return co[0] + co[1] * x + co[2] * x * x


def running_median(v, w):
    n = len(v); h = w // 2
    return [sorted(v[(k + d) % n] for d in range(-h, h + 1))[h] for k in range(n)]


def gaussian(v, sigma):
    n = len(v); r = int(3 * sigma); ker = [math.exp(-0.5 * (d / sigma) ** 2) for d in range(-r, r + 1)]; s = sum(ker)
    return [sum(v[(k + d) % n] * ker[d + r] for d in range(-r, r + 1)) / s for k in range(n)]


def slope_limit(v, lim):
    n = len(v); out = v[:]
    for _ in range(3):                                           # forward and backward passes, repeated
        for k in range(1, n): out[k] = max(out[k - 1] - lim, min(out[k - 1] + lim, out[k]))
        for k in range(n - 2, -1, -1): out[k] = max(out[k + 1] - lim, min(out[k + 1] + lim, out[k]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--notch', type=float, default=0.35); ap.add_argument('--notch-len', type=int, default=25)
    ap.add_argument('--sigma', type=float, default=5.0); ap.add_argument('--slope', type=float, default=0.10)
    ap.add_argument('--write', action='store_true'); ap.add_argument('--dump', type=str, default='')
    ap.add_argument('--keep-left', type=str, default='82,380', help='station range of the pit-out blend lane: left edge kept as is')
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n, sp = T['n'], T['spacing_m']; fr = T['profile']['fractions']; Z = T['profile']['z']; C, L, R = T['center'], T['left'], T['right']

    def normal(k):
        a_, b_ = C[(k - 1) % n], C[(k + 1) % n]; tx, ty = b_[0] - a_[0], b_[1] - a_[1]; l = math.hypot(tx, ty) or 1
        return -ty / l, tx / l

    def hw(k):
        nx, ny = normal(k); c = C[k]
        return ((L[k][0] - c[0]) * nx + (L[k][1] - c[1]) * ny, -((R[k][0] - c[0]) * nx + (R[k][1] - c[1]) * ny))

    H = [hw(k) for k in range(n)]
    # curvature weight: smoothing applies fully where the centre radius is over 250 m (straights, gentle bends) and
    # not at all under 100 m (the Corkscrew, hairpins), where the painted edges genuinely swing against the centre
    head = [math.atan2(C[(k + 1) % n][1] - C[k][1], C[(k + 1) % n][0] - C[k][0]) for k in range(n)]
    dh = [((head[(k + 1) % n] - head[k] + math.pi) % (2 * math.pi) - math.pi) / sp for k in range(n)]
    kap3 = gaussian(dh, 3)
    kap = [max(abs(kap3[(k + d) % n]) for d in range(-30, 31)) for k in range(n)]   # running max: an S-bend's inflection is not a straight
    wsm = [min(1.0, max(0.0, (250.0 - 1.0 / max(abs(c_), 1e-6)) / (250.0 - 100.0))) for c_ in kap]
    wsm = [1.0 - w for w in wsm]                                      # 1 on straights, 0 in tight corners
    # protected stations: a pit-lane or paved-zone part touches the track edge there
    prot = {'left': set(), 'right': set()}
    for grp in ('pit_lane', 'paved_zones'):
        for part in (SC.get(grp) or {}).get('parts', []):
            for s_, gl, gr in zip(part.get('track_s', []), part.get('gap_left', []), part.get('gap_right', [])):
                k = int(round(s_ / sp)) % n
                if gl is not None and gl <= 0.3: prot['left'].add(k)
                if gr is not None and gr <= 0.3: prot['right'].add(k)
    report = {}
    newH = [list(h) for h in H]
    for si, side in enumerate(('left', 'right')):
        v = [h[si] for h in H]; med = running_median(v, 41)
        dev = [v[k] - med[k] for k in range(n)]; big = [abs(d) > a.notch for d in dev]
        fixed = v[:]; notches = []
        k = 0
        while k < n:
            if big[k] and wsm[k] > 0.5:
                j = k
                while j < n and big[j]: j += 1
                if j - k < a.notch_len:
                    for q in range(k, j): fixed[q] = med[q]
                    notches.append((k, j - 1, round(max(abs(dev[q]) for q in range(k, j)), 2)))
                k = j
            else: k += 1
        fixed = gaussian(fixed, 2.0)                                   # taper the notch replacements (the pipeline's own 2 m)
        sm = slope_limit(gaussian(fixed, a.sigma), a.slope)
        sm = [wsm[k] * sm[k] + (1 - wsm[k]) * fixed[k] for k in range(n)]
        # protected stations keep the original value, blended over 15 stations
        P = sorted(prot[side])
        for k in range(n):
            if k in prot[side]: sm[k] = v[k]
        for k in range(n):
            if k in prot[side]: continue
            d = min((abs(k - p) if abs(k - p) <= n // 2 else n - abs(k - p)) for p in P) if P else 99
            if d < 15:
                t = d / 15; sm[k] = (1 - t) * v[k] + t * sm[k]
        if side == 'left' and a.keep_left:
            lo_, hi_ = [int(x) for x in a.keep_left.split(',')]
            for k in range(lo_, hi_ + 1): sm[k % n] = v[k % n]
            for k in range(hi_ + 1, hi_ + 16): t = (k - hi_) / 15; sm[k % n] = (1 - t) * v[k % n] + t * sm[k % n]
            for k in range(lo_ - 15, lo_): t = (lo_ - k) / 15; sm[k % n] = (1 - t) * v[k % n] + t * sm[k % n]
        for k in range(n): newH[k][si] = sm[k]
        moved = [abs(sm[k] - v[k]) for k in range(n)]
        worst = sorted(range(n), key=lambda q: -moved[q])[:6]
        report[side] = {'notches': notches, 'moved_p50': round(sorted(moved)[n // 2], 3), 'moved_max': round(max(moved), 2),
                        'worst': [(q, round(sm[q] - v[q], 2)) for q in worst], 'protected': len(P)}
    for side, r in report.items():
        print(f"{side}: {len(r['notches'])} notches replaced {r['notches'][:8]}{' ...' if len(r['notches']) > 8 else ''}")
        print(f"       moved p50 {r['moved_p50']} m, max {r['moved_max']} m at {r['worst']}; protected stations {r['protected']}")
    print('stations fully smoothed (R > 250 m):', sum(1 for w in wsm if w >= 0.999), ' untouched (R < 100 m):', sum(1 for w in wsm if w <= 0.001))
    if a.dump:
        lo, hi = [int(x) for x in a.dump.split(',')]
        print('station  L old->new   R old->new')
        for k in range(lo, hi, 4): print(f'{k:5d}  {H[k][0]:5.2f}->{newH[k][0]:5.2f}  {H[k][1]:5.2f}->{newH[k][1]:5.2f}')
    if not a.write: print('dry run; --write to apply'); return
    for k in range(n):
        hl_old, hr_old = H[k]; hl, hr = newH[k]
        nx, ny = normal(k); c = C[k]
        xs_old = [(-f) * hl_old if f < 0 else -f * hr_old for f in fr]; xs_new = [(-f) * hl if f < 0 else -f * hr for f in fr]
        znew = [quad_eval(xs_old, Z[k], x) for x in xs_new]; znew[fr.index(0)] = Z[k][fr.index(0)]
        Z[k] = [round(z, 3) for z in znew]
        L[k] = [round(c[0] + nx * hl, 3), round(c[1] + ny * hl, 3), Z[k][0]]
        R[k] = [round(c[0] - nx * hr, 3), round(c[1] - ny * hr, 3), Z[k][-1]]
    note = f'18 Oct 2026: edge notches/waves removed (fix_edge_waves.py notch {a.notch} len {a.notch_len} sigma {a.sigma} slope {a.slope})'
    if isinstance(T.get('notes'), dict): T['notes']['edge_waves'] = note
    else: T['notes'] = (T.get('notes') or '') + ' | ' + note
    json.dump(T, open(os.path.join(OUT, 'track.json'), 'w'), separators=(',', ':')); print('wrote track.json')


if __name__ == '__main__':
    sys.exit(main())
