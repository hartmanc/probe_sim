"""Rahal straight, left edge (owner, 18 Oct 2026: "Does the course come in like this on the actual track?" No).
    python3 -I tools/track/fix_rahal_left.py [--lo 2060] [--hi 2300] [--ref main] [--write]
The sweep's retrace put the left edge 1-2 m inside the painted line from ~2140 to ~2235 (it locked onto the wrong
feature), and the first paint rebuild had put it on the OUTER limit of the T6 exit apron at ~2080-2115 (8.5 m from
the centre). The deployed track's left edge (git ref --ref) sits on the white line along this whole stretch (checked on
the z20 captures with the per-station paint sweep drawn on them). This script puts the branch's left half-width at the
point where the station's normal crosses that reference polyline, smooths it (sigma 3 stations), blends over --blend
stations at both ends (lengthened until no blend step exceeds --max-step), re-evaluates the profile columns from
each station's cross-section quadratic (centre untouched) and records its arguments in track.json notes.
Run tools/track/add_paved_aprons.py --write afterwards: the T6 exit apron and the Rahal apron become paved zones
outside the corrected edge.
"""
import argparse, json, math, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fix_edge_waves import quad_eval, gaussian  # noqa: E402
ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lo', type=int, default=2060); ap.add_argument('--hi', type=int, default=2362)
    ap.add_argument('--ref', default='main'); ap.add_argument('--blend', type=int, default=10)
    ap.add_argument('--max-step', type=float, default=0.10); ap.add_argument('--write', action='store_true')
    ap.add_argument('--sweep', default=os.path.join(ROOT, 'tools', 'track', 'out', 'sweep_final.npz'), help='sweep_paint output; its left detections are the reference from --sweep-from on')
    ap.add_argument('--sigma', type=float, default=6.0, help='final Gaussian smoothing of the target, stations')
    ap.add_argument('--sweep-max-out', type=float, default=0.5, help='in the kerb region ignore detections more than this far OUTSIDE the current edge (the edge is known to sit beyond the kerb there; readings under the T7 board are stray)')
    ap.add_argument('--sweep-from', type=int, default=2236, help='from this station the T7 approach kerb (sweep kerb-limit detections) is the reference, not the --ref polyline')
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json')))
    T0 = json.loads(subprocess.check_output(['git', '-C', ROOT, 'show', f'{a.ref}:public/tracks/laguna_seca/track.json']))
    n, sp = T['n'], T['spacing_m']; fr = T['profile']['fractions']; Z = T['profile']['z']; C, L, R = T['center'], T['left'], T['right']
    L0 = T0['left']; n0 = T0['n']

    def lnormal(k):
        p, q = C[(k - 1) % n], C[(k + 1) % n]; tx, ty = q[0] - p[0], q[1] - p[1]; l = math.hypot(tx, ty) or 1
        return -ty / l, tx / l

    def hw(k):
        nx, ny = lnormal(k); c = C[k]
        return ((L[k][0] - c[0]) * nx + (L[k][1] - c[1]) * ny, -((R[k][0] - c[0]) * nx + (R[k][1] - c[1]) * ny))

    def ref_cross(k):
        """distance along the left normal from C[k] to the reference left polyline (nearest crossing, 2..10 m)"""
        c = C[k]; nx, ny = lnormal(k)
        j0 = min(range(n0), key=lambda j: math.hypot(L0[j][0] - c[0], L0[j][1] - c[1]))
        best = None
        for j in range(j0 - 40, j0 + 40):
            p, q = L0[j % n0], L0[(j + 1) % n0]
            # solve c + t*nrm = p + u*(q-p)
            dx, dy = q[0] - p[0], q[1] - p[1]; det = nx * (-dy) - ny * (-dx)
            if abs(det) < 1e-9: continue
            rx, ry = p[0] - c[0], p[1] - c[1]
            t = (rx * (-dy) - ry * (-dx)) / det; u = (nx * ry - ny * rx) / det
            if 0.0 <= u <= 1.0 and 2.0 <= t <= 10.0 and (best is None or t < best): best = t
        return best

    H = [hw(k) for k in range(n)]
    tgt = {}
    for k in range(a.lo, min(a.hi, a.sweep_from - 1) + 1):
        t = ref_cross(k % n)
        if t is not None: tgt[k] = t
    if a.hi >= a.sweep_from:
        import numpy as np
        dl = np.load(a.sweep)['dev_left']
        for k in range(a.sweep_from, a.hi + 1):
            if np.isfinite(dl[k % n]) and -3.0 < dl[k % n] < a.sweep_max_out: tgt[k] = H[k % n][0] + float(dl[k % n])
    miss = [k for k in range(a.lo, a.hi + 1) if k not in tgt]
    if miss: print('no reference at', len(miss), 'stations (interpolated):', miss[:12], '...' if len(miss) > 12 else '')
    ks = sorted(tgt); vals = [tgt[k] for k in ks]
    # fill gaps by linear interpolation, then a 21-station running median against stray detections, then a 4-station Gaussian
    full = []
    for k in range(a.lo, a.hi + 1):
        if k in tgt: full.append(tgt[k]); continue
        lo_k = max((q for q in ks if q < k), default=None); hi_k = min((q for q in ks if q > k), default=None)
        if lo_k is None: full.append(tgt[hi_k])
        elif hi_k is None: full.append(tgt[lo_k])
        else: full.append(tgt[lo_k] + (tgt[hi_k] - tgt[lo_k]) * (k - lo_k) / (hi_k - lo_k))
    med = [sorted(full[max(0, i - 10):i + 11])[len(full[max(0, i - 10):i + 11]) // 2] for i in range(len(full))]
    v = [0.0] * n
    for i, k in enumerate(range(a.lo, a.hi + 1)): v[k % n] = med[i] - H[k % n][0]
    sm = gaussian(v, a.sigma)
    blend = a.blend
    while True:
        out = [0.0] * n
        for k in range(a.lo, a.hi + 1):
            d = min(k - a.lo, a.hi - k); w = 1.0 if d >= blend else (d / blend) ** 2 * (3 - 2 * d / blend)
            out[k % n] = w * sm[k % n]
        step = max(abs(out[(k + 1) % n] - out[k % n]) for k in range(a.lo - 2, a.hi + 2))
        if step <= a.max_step or blend > 40: break
        blend += 2
    worst = max(range(a.lo, a.hi + 1), key=lambda k: abs(out[k % n]))
    print(f'left edge move over {a.lo}..{a.hi}: max {out[worst % n]:+.2f} m at {worst}; blend {blend}; max adjacent step {step:.3f} m')
    print('station: half-width now -> after  ' + '  '.join(f'{k}:{H[k % n][0]:.1f}->{H[k % n][0] + out[k % n]:.1f}' for k in range(a.lo, a.hi + 1, 15)))
    if not a.write: print('dry run; --write to apply'); return
    for k in range(a.lo, a.hi + 1):
        kk = k % n; mv = out[kk]
        if abs(mv) < 1e-6: continue
        hl_old, hr = H[kk]; hl = hl_old + mv; nx, ny = lnormal(kk); c = C[kk]
        xs_old = [(-f) * hl_old if f < 0 else -f * hr for f in fr]; xs_new = [(-f) * hl if f < 0 else -f * hr for f in fr]
        znew = [quad_eval(xs_old, Z[kk], x) for x in xs_new]; znew[fr.index(0)] = Z[kk][fr.index(0)]
        Z[kk] = [round(z, 3) for z in znew]
        L[kk] = [round(c[0] + nx * hl, 3), round(c[1] + ny * hl, 3), Z[kk][0]]
    note = (f'18 Oct 2026: fix_rahal_left.py --lo {a.lo} --hi {a.hi} --ref {a.ref} --sweep-from {a.sweep_from} --sigma {a.sigma} --blend {a.blend} --max-step {a.max_step}: left edge put on the '
            f'painted line as the {a.ref} left polyline marks it up to {a.sweep_from - 1}, then on the T7 approach kerb limit from the paint sweep (max move {out[worst % n]:+.2f} m at {worst}); the T6 exit apron and the Rahal apron are paved zones outside it')
    if isinstance(T.get('notes'), dict): T['notes']['rahal_left'] = note
    else: T['notes'] = (T.get('notes') or '') + ' | ' + note
    json.dump(T, open(os.path.join(OUT, 'track.json'), 'w'), separators=(',', ':')); print('wrote track.json')


if __name__ == '__main__':
    sys.exit(main())
