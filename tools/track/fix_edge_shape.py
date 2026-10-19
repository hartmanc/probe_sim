"""Replace one side's half-width over a stretch by a smooth MONOTONE curve through measured knots (18 Oct 2026, T11 exit
right: the painted edge widens once from the apex kerb to the straight; per-station traces of the kerb/teal/line
there came out wavy because the three features overlap).
    python3 -I tools/track/fix_edge_shape.py --side right --knots 3283:4.2,3310:5.4,3340:7.0,3360:7.3,3400:7.9 [--blend 10] [--write]
Knots are station:half-width (metres from the centre). Between knots a monotone cubic (Fritsch-Carlson) is used, so the
width never overshoots a knot. The curve replaces the half-width from the first to the last knot, blended into the
untouched edge over --blend stations at both ends; profile columns are re-evaluated from each station's cross-section
quadratic (centre untouched); arguments go into track.json notes.
"""
import argparse, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fix_edge_waves import quad_eval  # noqa: E402
ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')


def pchip(xs, ys):
    """Fritsch-Carlson monotone cubic interpolant; returns f(x)."""
    m = len(xs); h = [xs[i + 1] - xs[i] for i in range(m - 1)]; d = [(ys[i + 1] - ys[i]) / h[i] for i in range(m - 1)]
    t = [0.0] * m
    t[0] = d[0]; t[-1] = d[-1]
    for i in range(1, m - 1):
        if d[i - 1] * d[i] <= 0: t[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            t[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    for i in range(m - 1):
        if d[i] == 0: t[i] = t[i + 1] = 0.0
        else:
            a, b = t[i] / d[i], t[i + 1] / d[i]
            if a * a + b * b > 9: s = 3 / math.sqrt(a * a + b * b); t[i] = s * a * d[i]; t[i + 1] = s * b * d[i]

    def f(x):
        i = max(0, min(m - 2, next((j for j in range(m - 1) if x <= xs[j + 1]), m - 2)))
        u = (x - xs[i]) / h[i]; h00 = 2 * u ** 3 - 3 * u ** 2 + 1; h10 = u ** 3 - 2 * u ** 2 + u; h01 = -2 * u ** 3 + 3 * u ** 2; h11 = u ** 3 - u ** 2
        return h00 * ys[i] + h10 * h[i] * t[i] + h01 * ys[i + 1] + h11 * h[i] * t[i + 1]
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--side', choices=('left', 'right'), required=True); ap.add_argument('--knots', required=True)
    ap.add_argument('--blend', type=int, default=10); ap.add_argument('--why', default=''); ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    knots = sorted((int(p.split(':')[0]), float(p.split(':')[1])) for p in a.knots.split(','))
    T = json.load(open(os.path.join(OUT, 'track.json')))
    n = T['n']; fr = T['profile']['fractions']; Z = T['profile']['z']; C, L, R = T['center'], T['left'], T['right']

    def lnormal(k):
        p, q = C[(k - 1) % n], C[(k + 1) % n]; tx, ty = q[0] - p[0], q[1] - p[1]; l = math.hypot(tx, ty) or 1
        return -ty / l, tx / l

    def hw(k):
        nx, ny = lnormal(k); c = C[k]
        return ((L[k][0] - c[0]) * nx + (L[k][1] - c[1]) * ny, -((R[k][0] - c[0]) * nx + (R[k][1] - c[1]) * ny))

    si = 0 if a.side == 'left' else 1
    f = pchip([k for k, _ in knots], [v for _, v in knots]); lo, hi = knots[0][0], knots[-1][0]
    new = {}
    for k in range(lo, hi + 1):
        cur = hw(k % n)[si]; tgt = f(k); d = min(k - lo, hi - k); w = 1.0 if d >= a.blend else (d / a.blend) ** 2 * (3 - 2 * d / a.blend)
        new[k] = cur + w * (tgt - cur)
    steps = [abs(new[k + 1] - new[k]) for k in range(lo, hi)]
    print(f'{a.side} half-width over {lo}..{hi}: ' + ' '.join(f'{k}:{hw(k % n)[si]:.1f}->{new[k]:.1f}' for k in range(lo, hi + 1, max(1, (hi - lo) // 12))))
    print(f'max adjacent step {max(steps):.3f} m; max move {max(abs(new[k] - hw(k % n)[si]) for k in new):.2f} m; monotone: {all(new[k + 1] >= new[k] - 1e-6 for k in range(lo, hi)) or all(new[k + 1] <= new[k] + 1e-6 for k in range(lo, hi))}')
    if not a.write: print('dry run; --write to apply'); return
    for k in range(lo, hi + 1):
        kk = k % n; hl_old, hr_old = hw(kk); hl, hr = (new[k], hr_old) if si == 0 else (hl_old, new[k])
        nx, ny = lnormal(kk); c = C[kk]
        xs_old = [(-g) * hl_old if g < 0 else -g * hr_old for g in fr]; xs_new = [(-g) * hl if g < 0 else -g * hr for g in fr]
        znew = [quad_eval(xs_old, Z[kk], x) for x in xs_new]; znew[fr.index(0)] = Z[kk][fr.index(0)]
        Z[kk] = [round(z, 3) for z in znew]
        L[kk] = [round(c[0] + nx * hl, 3), round(c[1] + ny * hl, 3), Z[kk][0]]
        R[kk] = [round(c[0] - nx * hr, 3), round(c[1] - ny * hr, 3), Z[kk][-1]]
    note = f'18 Oct 2026: fix_edge_shape.py --side {a.side} --knots {a.knots} --blend {a.blend}: monotone cubic through measured knots. {a.why}'
    if isinstance(T.get('notes'), dict): T['notes'][f'shape_{a.side}_{lo}'] = note
    else: T['notes'] = (T.get('notes') or '') + ' | ' + note
    json.dump(T, open(os.path.join(OUT, 'track.json'), 'w'), separators=(',', ':')); print('wrote track.json')


if __name__ == '__main__':
    sys.exit(main())
