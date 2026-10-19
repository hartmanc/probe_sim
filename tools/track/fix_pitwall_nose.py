"""Pit-wall nose at the T11 exit (18 Oct 2026 sweep): the OSM pit-wall polyline leaves the T11 tyre wall and cuts
diagonally across the painted left-edge line (0.9 m inside the track at station 3365) before settling on the real wall
at a steady 2.0 m from the paint (tile z20_s3315 vs z20_s3400, tools/track/compare/edge_sweep_2026-10-18).
    python3 -I tools/track/fix_pitwall_nose.py [--lo 3285] [--hi 3425] [--min 2.0] [--write]
Every point of a `pitwall` barrier run whose nearest station lies in lo..hi and whose gap outside the left edge (along
the edge's normal) is under --min is moved outward along that normal to --min. Points already further out are kept, so
the run still starts at the tyre wall. scenery.json only; track.json is untouched.
"""
import argparse, json, math, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lo', type=int, default=3285); ap.add_argument('--hi', type=int, default=3425)
    ap.add_argument('--min', type=float, default=2.0); ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n = T['n']; C, L = T['center'], T['left']

    def lnormal(k):
        p, q = C[(k - 1) % n], C[(k + 1) % n]; tx, ty = q[0] - p[0], q[1] - p[1]; l = math.hypot(tx, ty) or 1
        return -ty / l, tx / l

    def station_of(p):
        return min(range(a.lo - 60, a.hi + 60), key=lambda k: math.hypot(C[k % n][0] - p[0], C[k % n][1] - p[1])) % n

    moved = []
    for ri, run in enumerate(SC['barriers']):
        if run.get('kind') != 'pitwall': continue
        for j, p in enumerate(run['pts']):
            k = station_of(p)
            if not (a.lo <= k <= a.hi): continue
            nx, ny = lnormal(k); g = (p[0] - L[k][0]) * nx + (p[1] - L[k][1]) * ny
            if g < a.min and g > -3.0:
                p[0] = round(L[k][0] + nx * a.min, 3); p[1] = round(L[k][1] + ny * a.min, 3)
                moved.append((ri, j, k, round(g, 2)))
    if moved:
        print(f'{len(moved)} pit-wall points moved to {a.min:.2f} m outside the left edge, stations {min(m[2] for m in moved)}..{max(m[2] for m in moved)}; '
              f'worst gap before {min(m[3] for m in moved):+.2f} m (run {moved[0][0]})')
    else:
        print('no pit-wall point inside the minimum gap; nothing to do')
    if not a.write: print('dry run; --write to apply'); return
    note = f'18 Oct 2026: fix_pitwall_nose.py --lo {a.lo} --hi {a.hi} --min {a.min}: {len(moved)} pit-wall points at the T11 exit nose moved out to {a.min} m from the left edge (OSM polyline cut across the paint)'
    SC.setdefault('notes', {})
    if isinstance(SC['notes'], dict): SC['notes']['pitwall_nose'] = note
    else: SC['notes'] = {'pitwall_nose': note, 'previous': SC['notes']}
    json.dump(SC, open(os.path.join(OUT, 'scenery.json'), 'w'), separators=(',', ':')); print('wrote scenery.json')


if __name__ == '__main__':
    sys.exit(main())
