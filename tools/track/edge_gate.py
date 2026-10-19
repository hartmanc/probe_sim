"""Geometry gate for track.json edges after the edge fixes (18 Oct 2026). Pure python.
    python3 -I tools/track/edge_gate.py [--track public/tracks/laguna_seca/track.json]

Prints per side: (1) rms of the half-width about its 41-station running median over stations whose centre radius is
over 250 m (straights; target < 0.05 m); (2) the max adjacent half-width step outside tight corners (radius > 100 m;
target <= 0.10 m); (3) the max change between adjacent stations of each profile column relative to the centre column,
i.e. the cross-section shape (target <= 0.05 m); then the front-straight wall gaps (left to the pit wall, right to the
concrete wall, stations 3420-40, p10/p50/p90) and the max adjacent half-width step within +-35 stations of each bridge.
"""
import argparse, json, math, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--track', default=os.path.join(ROOT, 'public/tracks/laguna_seca/track.json'))
    a = ap.parse_args()
    T = json.load(open(a.track)); SC = json.load(open(os.path.join(ROOT, 'public/tracks/laguna_seca/scenery.json')))
    n, sp = T['n'], T['spacing_m']; C, L, R, Z = T['center'], T['left'], T['right'], T['profile']['z']; ci = T['profile']['fractions'].index(0)

    def nl(k):
        a_, b_ = C[(k - 1) % n], C[(k + 1) % n]; tx, ty = b_[0] - a_[0], b_[1] - a_[1]; l = math.hypot(tx, ty) or 1
        return -ty / l, tx / l
    H = []
    for k in range(n):
        nx, ny = nl(k); c = C[k]
        H.append(((L[k][0] - c[0]) * nx + (L[k][1] - c[1]) * ny, -((R[k][0] - c[0]) * nx + (R[k][1] - c[1]) * ny)))
    head = [math.atan2(C[(k + 1) % n][1] - C[k][1], C[(k + 1) % n][0] - C[k][0]) for k in range(n)]
    kap = [abs(((head[(k + 1) % n] - head[k] + math.pi) % (2 * math.pi) - math.pi) / sp) for k in range(n)]
    kap = [sum(kap[(k + d) % n] for d in range(-5, 6)) / 11 for k in range(n)]
    rad = [1 / max(x, 1e-6) for x in kap]
    for si, side in enumerate(('left', 'right')):
        v = [h[si] for h in H]
        med = [sorted(v[(k + d) % n] for d in range(-20, 21))[20] for k in range(n)]
        st = [k for k in range(n) if rad[k] > 250]
        rms = math.sqrt(sum((v[k] - med[k]) ** 2 for k in st) / len(st))
        steps = [(abs(v[(k + 1) % n] - v[k]), k) for k in range(n) if rad[k] > 100]
        col = 0 if side == 'left' else len(Z[0]) - 1
        zs = max((abs((Z[(k + 1) % n][col] - Z[(k + 1) % n][ci]) - (Z[k][col] - Z[k][ci])), k) for k in range(n))
        top = sorted(steps, reverse=True)[:3]
        print(f'{side:5s}: rms vs 41-st median (R>250 m, {len(st)} st) {rms:.3f} m | max adjacent step (R>100 m) '
              f'{top[0][0]:.3f} m at {top[0][1]} (next {top[1][0]:.3f}@{top[1][1]}, {top[2][0]:.3f}@{top[2][1]}) | '
              f'max edge-column cross-section step {zs[0]:.3f} m at {zs[1]}')
    allcol = max((abs((Z[(k + 1) % n][c] - Z[(k + 1) % n][ci]) - (Z[k][c] - Z[k][ci])), k, c) for k in range(n) for c in range(len(Z[0])))
    print(f'max cross-section step any column: {allcol[0]:.3f} m at station {allcol[1]} column {allcol[2]}')
    for side, kind, sg in (('left', 'pitwall', 1), ('right', 'concrete', -1)):
        pts = [p for b in SC['barriers'] if b['kind'] == kind for p in b['pts']]; gaps = []
        for k in list(range(3420, n)) + list(range(0, 41)):
            e = (L if side == 'left' else R)[k]; nx, ny = nl(k); nx, ny = nx * sg, ny * sg; best = None
            for p in pts:
                d = (p[0] - e[0]) * nx + (p[1] - e[1]) * ny; lat = abs((p[0] - e[0]) * (-ny) + (p[1] - e[1]) * nx)
                if -2 < d < 15 and lat < 2 and (best is None or d < best): best = d
            if best is not None: gaps.append(best)
        gaps.sort(); q = lambda f: gaps[int(f * (len(gaps) - 1))]
        print(f'front straight {side} gap to {kind} (3420-40, {len(gaps)} st): p10 {q(0.1):.2f} p50 {q(0.5):.2f} p90 {q(0.9):.2f} m')
    for br in SC['bridges']:
        k0 = int(round(br['s'] / sp))
        for si, side in enumerate(('left', 'right')):
            m = max(abs(H[(k + 1) % n][si] - H[k % n][si]) for k in range(k0 - 35, k0 + 35))
            print(f'bridge s={br["s"]:7.1f} (station {k0}) {side}: max adjacent half-width step within +-35 {m:.3f} m')
    # corner exits widen once: within 150 stations after an apex the half-width must not overshoot its value at the
    # window end by more than 0.5 m (owner, 18 Oct 2026, T11 exit: a 2.8 m swell 100 m after the apex)
    # Half-width is measured from a centreline that cuts the apexes, so the check starts where the centre radius is back
    # over 150 m (the exit proper) and uses the ROAD WIDTH (left + right), which does not depend on where the centre sits.
    head = [math.atan2(C[(k + 1) % n][1] - C[k][1], C[(k + 1) % n][0] - C[k][0]) for k in range(n)]
    kap = [abs(((head[(k + 1) % n] - head[k] + math.pi) % (2 * math.pi) - math.pi) / sp) for k in range(n)]
    kap = [sum(kap[(k + d) % n] for d in range(-3, 4)) / 7 for k in range(n)]
    for c in T.get('corners', []):
        k0 = int(round(c['s'] / sp))
        ks = [k for k in range(k0, k0 + 150) if kap[k % n] < 1 / 150.0]
        if len(ks) < 40: continue
        start = ks[0]; wid = [H[k % n][0] + H[k % n][1] for k in range(start, start + 120)]
        mx = max(wid); im = wid.index(mx); over = mx - wid[-1]
        if over > 1.0 and im < 110: print(f"exit overshoot {c.get('name', '?'):14s}: road width +{over:.2f} m over its value 120 m on, at station {(start + im) % n} (exit from {start}, end width {wid[-1]:.1f} m)")


if __name__ == '__main__':
    main()
