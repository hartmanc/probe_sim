"""T11 exit, right side (18 Oct 2026 sweep): the painted-edge detector read the OUTER limit of the green runoff strip
as the road edge, so from station ~3300 to ~3380 the right edge ran 1-3 m beyond the white line, the green strip lay
inside the drivable track and scenery.json painted a second green strip (kerbs.strips kind 'verge') outward from that
edge, over what the Mustang onboard and the captures show as plain pavement to the wall.
    python3 -I tools/track/fix_t11_exit_right.py [--lo 3290] [--hi 3395] [--write]
Per station in lo..hi the Google z20 captures (registration shift from tools/track/out/paint_regs.json; z20_s3400 is
misregistered and is used with the mean shift of its two neighbours, as the sweep's colour check did) are sampled along
the right edge's normal from 6 m inside to 1 m outside the current edge; the green band (g > r+20, b > r+10) nearest
the edge is found; the white line lies just inside it, so the edge target is the band's inner limit minus --line m.
Stations without a band keep their edge. Targets are inward-only, Gaussian-smoothed (--sigma stations, default 5), blended into
the untouched edge at both ends (at least --blend stations, lengthened until no blend step exceeds --max-step m), the
half-width moved, profile columns re-evaluated from each station's cross-section quadratic (centre untouched).
The verge strip is then trimmed to the band's measured extent and width (paint from the new edge outward).
Run tools/track/fix_front_straight.py --write afterwards: its shoulder zone starts at the right edge.
"""
import argparse, json, math, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fix_edge_waves import quad_eval, gaussian  # noqa: E402
ROOT = os.path.abspath(os.path.join(HERE, '..', '..')); OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')
SAT = os.path.join(ROOT, 'tools', 'track', 'compare', 'satellite')
MPP = 156543.03 * math.cos(math.radians(36.5843)) / 2 ** 20
NEIGHBOUR_REG = {'z20_s3400': ('z20_s3315', 'z20_s3485')}      # misregistered capture: use the mean shift of these two
STEP = 0.1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lo', type=int, default=3290); ap.add_argument('--hi', type=int, default=3395)
    ap.add_argument('--line', type=float, default=0.3, help='white line centre this far inside the green band')
    ap.add_argument('--blend', type=int, default=12); ap.add_argument('--max-step', type=float, default=0.07)
    ap.add_argument('--sigma', type=float, default=5.0, help='Gaussian smoothing of the traced target, stations')
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n, sp = T['n'], T['spacing_m']; fr = T['profile']['fractions']; Z = T['profile']['z']; C, L, R = T['center'], T['left'], T['right']
    tiles = {t['name']: t for t in json.load(open(os.path.join(SAT, 'z20_tiles.json')))}
    regs = {r[0]: (r[1], r[2]) for r in json.load(open(os.path.join(ROOT, 'tools', 'track', 'out', 'paint_regs.json')))}
    for nm, (p, q) in NEIGHBOUR_REG.items(): regs[nm] = ((regs[p][0] + regs[q][0]) / 2, (regs[p][1] + regs[q][1]) / 2)
    names = ('z20_s3230', 'z20_s3315', 'z20_s3400', 'z20_s3485'); imgs = {nm: Image.open(os.path.join(SAT, nm + '_google.jpg')).convert('RGB') for nm in names}

    def lnormal(k):
        p, q = C[(k - 1) % n], C[(k + 1) % n]; tx, ty = q[0] - p[0], q[1] - p[1]; l = math.hypot(tx, ty) or 1
        return -ty / l, tx / l

    def hw(k):
        nx, ny = lnormal(k); c = C[k]
        return ((L[k][0] - c[0]) * nx + (L[k][1] - c[1]) * ny, -((R[k][0] - c[0]) * nx + (R[k][1] - c[1]) * ny))

    def sample(x, y):
        best = None
        for nm, im in imgs.items():
            t = tiles[nm]; dx, dy = regs[nm]; W, H = im.size
            px = W / 2 + (x + dx - t['x']) / MPP; py = H / 2 - (y + dy - t['y']) / MPP
            if 2 <= px < W - 2 and 2 <= py < H - 2:
                d = math.hypot(px - W / 2, py - H / 2)
                if best is None or d < best[0]:
                    acc = [0, 0, 0]
                    for u in (-1, 0, 1):
                        for v in (-1, 0, 1):
                            c = im.getpixel((int(px) + u, int(py) + v)); acc = [s + w for s, w in zip(acc, c)]
                    best = (d, [s / 9 for s in acc])
        return None if best is None else best[1]

    offs = [i * STEP for i in range(int(-6.0 / STEP), int(1.0 / STEP) + 1)]
    band = {}                                                   # station -> (inner, outer) m outward from the current edge
    for k in range(a.lo, a.hi + 1):
        nx, ny = lnormal(k); flags = []
        for o in offs:
            c = sample(R[k][0] - nx * o, R[k][1] - ny * o)
            flags.append(bool(c) and c[1] > c[0] + 20 and c[2] > c[0] + 10)
        runs = []; i = 0
        while i < len(offs):
            if flags[i]:
                j = i
                while j < len(offs) and flags[j]: j += 1
                runs.append((offs[i], offs[j - 1])); i = j
            else: i += 1
        runs = [r for r in runs if r[1] - r[0] >= 2 * STEP]
        if runs: band[k] = max(runs, key=lambda r: r[1])
    if not band: print('no green band found; nothing to do'); return
    ks = sorted(band); print(f'green band found at {len(band)} of {a.hi - a.lo + 1} stations, {ks[0]}..{ks[-1]}; '
                             f'width median {sorted(b[1] - b[0] + STEP for b in band.values())[len(band) // 2]:.2f} m; '
                             f'inner limit median {sorted(b[0] for b in band.values())[len(band) // 2]:+.2f} m from the edge')
    # target move per station (negative = inward), only where a band exists; others 0
    target = {k: min(0.0, band[k][0] - a.line) if k in band else 0.0 for k in range(a.lo, a.hi + 1)}
    v = [0.0] * n
    for k, t in target.items(): v[k % n] = t
    sm = gaussian(v, a.sigma)
    # blend into the untouched edge at both ends, lengthening until no step exceeds max-step
    blend = a.blend
    while True:
        out = sm[:]
        for k in range(a.lo, a.hi + 1):
            d = min(k - a.lo, a.hi - k); t = 1.0 if d >= blend else (d / blend) ** 2 * (3 - 2 * d / blend)
            out[k % n] = t * sm[k % n]
        for k in range(n):
            if not (a.lo <= k <= a.hi): out[k] = 0.0
        step = max(abs(out[(k + 1) % n] - out[k]) for k in range(a.lo - 2, a.hi + 2))
        if step <= a.max_step or blend > 60: break
        blend += 2
    worst = min(range(a.lo, a.hi + 1), key=lambda k: out[k % n])
    print(f'edge move: max inward {out[worst % n]:+.2f} m at station {worst}; blend {blend} stations; max adjacent step {step:.3f} m')
    print('station: move  ' + '  '.join(f'{k}:{out[k % n]:+.2f}' for k in range(a.lo, a.hi + 1, 7)))
    strip = next((s for s in SC['kerbs']['strips'] if s.get('kind') == 'verge' and s['side'] == -1 and 3300 < s.get('s0', 0) < 3400), None)
    new_strip = None
    if strip:
        widths = sorted(b[1] - b[0] + STEP for b in band.values()); w = round(widths[len(widths) // 2], 1)
        new_strip = dict(strip); new_strip.update({'s0': round(ks[0] * sp, 1), 's1': round(ks[-1] * sp, 1), 'inset': 0.0, 'paint': w,
                                                   'src': 'google_sat z20 band trace, fix_t11_exit_right.py 18 Oct 2026'})
        print(f"verge strip: s0 {strip['s0']} -> {new_strip['s0']}, s1 {strip['s1']} -> {new_strip['s1']}, paint {strip.get('paint')} -> {w}")
    if not a.write: print('dry run; --write to apply'); return
    for k in range(a.lo, a.hi + 1):
        kk = k % n; mv = out[kk]
        if abs(mv) < 1e-6: continue
        hl, hr_old = hw(kk); hr = hr_old + mv; nx, ny = lnormal(kk); c = C[kk]
        xs_old = [(-f) * hl if f < 0 else -f * hr_old for f in fr]; xs_new = [(-f) * hl if f < 0 else -f * hr for f in fr]
        znew = [quad_eval(xs_old, Z[kk], x) for x in xs_new]; znew[fr.index(0)] = Z[kk][fr.index(0)]
        Z[kk] = [round(z, 3) for z in znew]
        R[kk] = [round(c[0] - nx * hr, 3), round(c[1] - ny * hr, 3), Z[kk][-1]]
    note = (f'18 Oct 2026: fix_t11_exit_right.py --lo {a.lo} --hi {a.hi} --line {a.line} --sigma {a.sigma} --blend {a.blend} --max-step {a.max_step}: right edge moved in to the '
            f'white line inside the green runoff strip (band at {ks[0]}..{ks[-1]}, max move {out[worst % n]:+.2f} m); z20_s3400 sampled with the mean shift of its neighbours')
    if isinstance(T.get('notes'), dict): T['notes']['t11_exit_right'] = note
    else: T['notes'] = (T.get('notes') or '') + ' | ' + note
    json.dump(T, open(os.path.join(OUT, 'track.json'), 'w'), separators=(',', ':')); print('wrote track.json')
    if new_strip:
        SC['kerbs']['strips'] = [new_strip if s is strip else s for s in SC['kerbs']['strips']]
        SC.setdefault('notes', {})
        if isinstance(SC['notes'], dict): SC['notes']['t11_exit_verge'] = 'verge strip trimmed to the traced green band (fix_t11_exit_right.py)'
        json.dump(SC, open(os.path.join(OUT, 'scenery.json'), 'w'), separators=(',', ':')); print('wrote scenery.json')


if __name__ == '__main__':
    sys.exit(main())
