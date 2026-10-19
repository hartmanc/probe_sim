"""Remove the bridge-shadow kinks from track.json edges (owner, 18 Oct 2026: "There is no little kink here. This is
straight underneath the bridge in real life").
    python3 -I tools/track/fix_bridge_edges.py [--win 25] [--write]
The painted-edge detector read each bridge shadow's edge as a painted line, so the left/right half-widths jog by 1-4 m
under the road bridges. Within +-win stations of each crossing the half-widths are replaced by a linear interpolation
of the clean half-widths at the window ends (the road is straight under every bridge), the profile columns are
re-evaluated at the moved lateral positions from each station's own cross-section quadratic, and the centre is kept.
The start/finish bridge is skipped (the pit-lane gaps there hang off the left edge and the paint was right) and so is
the Rahal lattice gantry (no shadow jog).
"""
import argparse, json, math, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')
SKIP = {'sign'}             # bridge styles never masked
SKIP_S = (37.1,)           # start/finish footbridge: pit-lane coupling, paint was right there


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--win', type=int, default=25); ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n, sp = T['n'], T['spacing_m']; fr = T['profile']['fractions']; Z = T['profile']['z']
    C, L, R = T['center'], T['left'], T['right']

    def normal(k):
        a_, b_ = C[(k - 1) % n], C[(k + 1) % n]
        tx, ty = b_[0] - a_[0], b_[1] - a_[1]; l = math.hypot(tx, ty) or 1
        return -ty / l, tx / l                                     # left normal

    def hw(k):
        nx, ny = normal(k); c = C[k]
        hl = (L[k][0] - c[0]) * nx + (L[k][1] - c[1]) * ny
        hr = -((R[k][0] - c[0]) * nx + (R[k][1] - c[1]) * ny)
        return hl, hr

    def quad_eval(xs, ys, x):
        """least-squares quadratic through (xs, ys), evaluated at x (7 points, well conditioned)"""
        m = len(xs); sx = [sum(v ** p for v in xs) for p in range(5)]
        sy = [sum(y * v ** p for v, y in zip(xs, ys)) for p in range(3)]
        A = [[sx[0], sx[1], sx[2]], [sx[1], sx[2], sx[3]], [sx[2], sx[3], sx[4]]]; b = sy[:]
        for i in range(3):                                           # gaussian elimination
            piv = max(range(i, 3), key=lambda r: abs(A[r][i])); A[i], A[piv] = A[piv], A[i]; b[i], b[piv] = b[piv], b[i]
            for r in range(i + 1, 3):
                f = A[r][i] / A[i][i]
                for c_ in range(i, 3): A[r][c_] -= f * A[i][c_]
                b[r] -= f * b[i]
        co = [0, 0, 0]
        for i in (2, 1, 0): co[i] = (b[i] - sum(A[i][j] * co[j] for j in range(i + 1, 3))) / A[i][i]
        return co[0] + co[1] * x + co[2] * x * x

    report = []
    for br in SC['bridges']:
        if br.get('style') in SKIP or br['s'] in SKIP_S: continue
        k0 = int(round(br['s'] / sp)); lo, hi = k0 - a.win, k0 + a.win
        hl_lo, hr_lo = hw(lo % n); hl_hi, hr_hi = hw(hi % n)
        worst = (0.0, 0.0)
        for k in range(lo, hi + 1):
            kk = k % n; t = (k - lo) / (hi - lo)
            hl_new = hl_lo + t * (hl_hi - hl_lo); hr_new = hr_lo + t * (hr_hi - hr_lo)
            hl_old, hr_old = hw(kk)
            worst = (max(worst[0], abs(hl_new - hl_old), key=abs), max(worst[1], abs(hr_new - hr_old), key=abs))
            nx, ny = normal(kk); c = C[kk]
            # profile columns: old lateral positions -> z quadratic -> new lateral positions
            # fractions: f<0 scales the left half-width (lateral +), f>0 the right (lateral -)
            xs_old = [(-f) * hl_old if f < 0 else -f * hr_old for f in fr]
            xs_new = [(-f) * hl_new if f < 0 else -f * hr_new for f in fr]
            znew = [quad_eval(xs_old, Z[kk], x) for x in xs_new]
            znew[fr.index(0)] = Z[kk][fr.index(0)]                       # centre height untouched
            Z[kk] = [round(v, 3) for v in znew]
            L[kk] = [round(c[0] + nx * hl_new, 3), round(c[1] + ny * hl_new, 3), Z[kk][0]]
            R[kk] = [round(c[0] - nx * hr_new, 3), round(c[1] - ny * hr_new, 3), Z[kk][-1]]
        report.append((br.get('style'), br['s'], k0, round(worst[0], 2), round(worst[1], 2)))
    for r in report: print(f"bridge {r[0]:5s} s={r[1]:7.1f} station {r[2]:4d}  max edge move left {r[3]:+.2f} m  right {r[4]:+.2f} m")
    if a.write:
        note = f'18 Oct 2026: bridge-shadow edge kinks removed under {len(report)} bridges (fix_bridge_edges.py, win {a.win})'
        if isinstance(T.get('notes'), dict): T['notes']['bridge_fix'] = note
        elif isinstance(T.get('notes'), list): T['notes'].append(note)
        else: T['notes'] = (T.get('notes') or '') + ' | ' + note
        json.dump(T, open(os.path.join(OUT, 'track.json'), 'w'), separators=(',', ':'))
        print('wrote', os.path.join(OUT, 'track.json'))
    else:
        print('dry run; --write to apply')


if __name__ == '__main__':
    sys.exit(main())
