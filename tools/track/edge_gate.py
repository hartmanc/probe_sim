"""Geometry gate for a track package's edges (18 Oct 2026). Pure python. Library (gate()) for build_track.py, which
fails the geometry stage on it, and a CLI for any package:

    python3 -I tools/track/edge_gate.py [--track public/tracks/laguna_seca] [--config laguna_seca]

Prints per side: (1) rms of the half-width about its 41-station running median over stations whose centre radius is
over 250 m (straights; gate `straight_rms`, Laguna's accepted edges 0.07/0.06 m); (2) the max adjacent half-width step
outside tight corners (radius > 100 m at every station within +-30) and outside the junctions in config
`gate.exempt` (gate `step`); (3) the max change between adjacent stations of each profile
column relative to the centre column, i.e. the cross-section shape (gate `profile_step`); then, when the package has a
scenery.json, the wall gaps of config `gate.wall_gaps` (p10/p50/p90, advisory) and the max adjacent half-width step
within +-35 stations of each bridge, and the exit-overshoot lines (advisory: they also fire on real features, each is
checked on the captures).
"""
import argparse, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))


# Acceptance of the fitted method (build-track skill: 90 %+ of observations within 0.25 m; edges_spline.py: rolling
# waviness <= 0.04 m, peak <= 0.10 m, kink <= 0.5 deg/station; the share is of the associated observations, as the skill
# measured it, and at least 85 % of capture rows must hold a band within 1.2 m of the curve), coverage and gaps (20 Oct 2026: at least 60 % of
# stations with evidence, no stretch over 60 m without), and world-space continuity (the third difference of each edge
# polyline under 2 cm: a 2 cm step shows there, a smooth curve does not). A config can tighten these, never loosen.
FITTED = dict(within=0.90, assoc=0.85, covered=0.60, gap=60, wave_rms=0.04, wave_peak=0.10, kink=0.5, world_d3=0.02)
_TIGHTER = dict(within=max, assoc=max, covered=max, gap=min, wave_rms=min, wave_peak=min, kink=min, world_d3=min)


def fitted_thresholds(g):
    g = g or {}
    return {k: _TIGHTER[k](v, g.get('fit_' + k, v)) for k, v in FITTED.items()}


def world_continuity(T):
    """max |third difference| of the left and right edge polylines (world metres) and where."""
    out = {}
    for side in ('left', 'right'):
        E = T[side]; n = len(E); best = (0.0, 0)
        for k in range(n):
            a, b, c, d = E[(k - 1) % n], E[k], E[(k + 1) % n], E[(k + 2) % n]
            v = math.hypot(d[0] - 3 * c[0] + 3 * b[0] - a[0], d[1] - 3 * c[1] + 3 * b[1] - a[1])
            if v > best[0]: best = (v, k)
        out[side] = best
    return out


def gate(T, SC=None, g=None, log=print, world=False):
    """T: track.json dict; SC: scenery.json dict or None; g: config `gate` dict. Returns (metrics, fails)."""
    g = g or dict(straight_rms=0.10, step=0.10, profile_step=0.10)
    n, sp = T['n'], T['spacing_m']; C, L, R, Z = T['center'], T['left'], T['right'], T['profile']['z']; ci = T['profile']['fractions'].index(0)
    fails, met = [], {}

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
    # outside tight corners: the centre radius over 100 m at every station within +-30 (an S-bend's inflection, where the
    # local radius is large between two tight corners, does not count)
    loose = [all(rad[(k + d) % n] > 100 for d in range(-30, 31)) for k in range(n)]
    for si, side in enumerate(('left', 'right')):
        v = [h[si] for h in H]
        med = [sorted(v[(k + d) % n] for d in range(-20, 21))[20] for k in range(n)]
        st = [k for k in range(n) if rad[k] > 250]
        rms = math.sqrt(sum((v[k] - med[k]) ** 2 for k in st) / len(st))
        ex = set()
        for sd, lo, hi, _ in g.get('exempt', []):
            if sd == side: ex |= set(k % n for k in range(lo, hi + (n if hi < lo else 0) + 1))
        steps = [(abs(v[(k + 1) % n] - v[k]), k) for k in range(n) if loose[k] and k not in ex]
        col = 0 if side == 'left' else len(Z[0]) - 1
        zs = max((abs((Z[(k + 1) % n][col] - Z[(k + 1) % n][ci]) - (Z[k][col] - Z[k][ci])), k) for k in range(n))
        top = sorted(steps, reverse=True)[:3]
        met[side] = dict(straight_rms=rms, step=top[0][0], step_at=top[0][1], edge_col_step=zs[0])
        ok = rms <= g['straight_rms'] and top[0][0] <= g['step']
        log(f'[{"ok" if ok else "FAIL"}] edge gate {side:5s}: rms vs 41-st median (R>250 m, {len(st)} st) {rms:.3f} m '
            f'(<= {g["straight_rms"]}) | max adjacent step (R>100 m within +-30) {top[0][0]:.3f} m at {top[0][1]} (next {top[1][0]:.3f}@{top[1][1]}, '
            f'{top[2][0]:.3f}@{top[2][1]}; <= {g["step"]}) | max edge-column cross-section step {zs[0]:.3f} m at {zs[1]}')
        if not ok: fails.append(f'edge gate {side}')
    if world:
        thr = fitted_thresholds(g)['world_d3']
        for side, (v, k) in world_continuity(T).items():
            met[side]['world_d3'] = v
            ok = v <= thr
            log(f'[{"ok" if ok else "FAIL"}] world continuity {side:5s}: max |third difference| of the edge polyline {v:.4f} m at station {k} (<= {thr})')
            if not ok: fails.append(f'world continuity {side}')
    allcol = max((abs((Z[(k + 1) % n][c] - Z[(k + 1) % n][ci]) - (Z[k][c] - Z[k][ci])), k, c) for k in range(n) for c in range(len(Z[0])))
    met['profile_step'] = allcol[0]
    ok = allcol[0] <= g['profile_step']
    log(f'[{"ok" if ok else "FAIL"}] profile gate: max cross-section step any column {allcol[0]:.3f} m at station {allcol[1]} column {allcol[2]} (<= {g["profile_step"]})')
    if not ok: fails.append('profile gate')
    if SC:
        for side, kind, lo, hi in g.get('wall_gaps', []):
            sg = 1 if side == 'left' else -1
            pts = [p for b in SC['barriers'] if b['kind'] == kind for p in b['pts']]; gaps = []
            for k in (list(range(lo, n)) + list(range(0, hi + 1)) if hi < lo else range(lo, hi + 1)):
                e = (L if side == 'left' else R)[k]; nx, ny = nl(k); nx, ny = nx * sg, ny * sg; best = None
                for p in pts:
                    d = (p[0] - e[0]) * nx + (p[1] - e[1]) * ny; lat = abs((p[0] - e[0]) * (-ny) + (p[1] - e[1]) * nx)
                    if -2 < d < 15 and lat < 2 and (best is None or d < best): best = d
                if best is not None: gaps.append(best)
            if gaps:
                gaps.sort(); q = lambda f: gaps[int(f * (len(gaps) - 1))]
                log(f'wall gap {side} to {kind} ({lo}-{hi}, {len(gaps)} st): p10 {q(0.1):.2f} p50 {q(0.5):.2f} p90 {q(0.9):.2f} m')
        for br in SC.get('bridges', []):
            k0 = int(round(br['s'] / sp))
            for si, side in enumerate(('left', 'right')):
                m = max(abs(H[(k + 1) % n][si] - H[k % n][si]) for k in range(k0 - 35, k0 + 35))
                log(f'bridge s={br["s"]:7.1f} (station {k0}) {side}: max adjacent half-width step within +-35 {m:.3f} m')
    # corner exits widen once (owner, 18 Oct 2026, T11 exit: a 2.8 m swell 100 m after the apex): within the first 120
    # stations after the centre radius is back over 150 m, the ROAD WIDTH must not overshoot its value at the window end
    # by more than 1 m. Advisory: it fires on real features too (pit-out merge, pit rejoin, a kerb narrowing the road).
    kap = [abs(((head[(k + 1) % n] - head[k] + math.pi) % (2 * math.pi) - math.pi) / sp) for k in range(n)]
    kap = [sum(kap[(k + d) % n] for d in range(-3, 4)) / 7 for k in range(n)]
    for c in T.get('corners', []):
        k0 = int(round(c['s'] / sp))
        ks = [k for k in range(k0, k0 + 150) if kap[k % n] < 1 / 150.0]
        if len(ks) < 40: continue
        start = ks[0]; wid = [H[k % n][0] + H[k % n][1] for k in range(start, start + 120)]
        mx = max(wid); im = wid.index(mx); over = mx - wid[-1]
        if over > 1.0 and im < 110: log(f"exit overshoot (advisory) {c.get('name', '?'):14s}: road width +{over:.2f} m over its value 120 m on, at station {(start + im) % n} (exit from {start}, end width {wid[-1]:.1f} m)")
    return met, fails


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--track', default=os.path.join(ROOT, 'public/tracks/laguna_seca'))
    ap.add_argument('--config', default=None, help='track id whose config `gate` thresholds apply')
    a = ap.parse_args()
    d = a.track if os.path.isdir(a.track) else os.path.dirname(a.track)
    T = json.load(open(os.path.join(d, 'track.json')))
    scp = os.path.join(d, 'scenery.json'); SC = json.load(open(scp)) if os.path.exists(scp) else None
    g = None
    if a.config:
        sys.path.insert(0, HERE); import trackcfg; g = trackcfg.load(a.config)['gate']
    _, fails = gate(T, SC, g)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
