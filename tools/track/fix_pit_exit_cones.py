"""Start the pit-exit cone line where the hot-pit wall ends (18 Oct 2026). fix_pitwall_exit.py removed the OSM pit wall
over stations 72-120 (reality: painted strip only there), after which an AI car in control drove left of the cone line
that began at 122 m. The cone line is the AI lane model's cap on the front-straight left lane and the race test's
"nobody in control crosses it" check, so it must begin where the wall ends.
    python3 -I tools/track/fix_pit_exit_cones.py [--s0 73] [--write]
New cone points are placed every `spacing_m` along the pit-lane part's track-side boundary (the boundary nearest the
first existing cone) from --s0 m to the first existing cone, with that boundary's heights; s0 is updated.
"""
import argparse, json, math, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--s0', type=float, default=73.0); ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n, sp = T['n'], T['spacing_m']; C, L = T['center'], T['left']
    pc = SC['pit_exit_cones']; first = pc['pts'][0]
    part = min(SC['pit_lane']['parts'], key=lambda p: min(math.hypot(q[0] - first[0], q[1] - first[1]) for q in p['left'] + p['right']))
    side = min(('left', 'right'), key=lambda s: min(math.hypot(q[0] - first[0], q[1] - first[1]) for q in part[s]))
    poly = part[side]; psp = part.get('spacing_m', SC['pit_lane'].get('spacing_m', 1.0))

    def station_of(p): return min(range(n), key=lambda k: math.hypot(C[k][0] - p[0], C[k][1] - p[1]))
    # index of the polyline point nearest the first cone, then walk back along the polyline to s0
    j_first = min(range(len(poly)), key=lambda j: math.hypot(poly[j][0] - first[0], poly[j][1] - first[1]))
    cum = [0.0]
    for j in range(1, len(poly)): cum.append(cum[-1] + math.hypot(poly[j][0] - poly[j - 1][0], poly[j][1] - poly[j - 1][1]))
    s_first = pc['s0']; new = []
    s = s_first - pc['spacing_m']
    while s >= a.s0 - 1e-6:
        target = cum[j_first] - (s_first - s)
        if target < 0: break
        j = max(1, min(len(poly) - 1, next((i for i in range(1, len(poly)) if cum[i] >= target), len(poly) - 1)))
        u = (target - cum[j - 1]) / max(1e-9, cum[j] - cum[j - 1]); p, q = poly[j - 1], poly[j]
        new.append([round(p[0] + u * (q[0] - p[0]), 2), round(p[1] + u * (q[1] - p[1]), 2), round(p[2] + u * (q[2] - p[2]), 2)])
        s -= pc['spacing_m']
    new.reverse()
    for p in new:
        k = station_of(p); print(f'  new cone at s~{k * sp:6.1f} m, {math.hypot(L[k][0] - p[0], L[k][1] - p[1]):.2f} m from the track left edge')
    print(f'{len(new)} cones added along pit-lane part boundary "{side}" from {a.s0} m to {s_first} m (spacing {pc["spacing_m"]} m)')
    if not a.write: print('dry run; --write to apply'); return
    pc['pts'] = new + pc['pts']; pc['s0'] = round(a.s0, 1); pc['src'] = str(pc.get('src', '')) + f' | fix_pit_exit_cones.py --s0 {a.s0} 18 Oct 2026: line starts where the hot-pit wall ends'
    SC.setdefault('notes', {})
    if isinstance(SC['notes'], dict): SC['notes']['pit_exit_cones'] = f'fix_pit_exit_cones.py --s0 {a.s0}: cone line from the wall end (fix_pitwall_exit.py)'
    json.dump(SC, open(os.path.join(OUT, 'scenery.json'), 'w'), separators=(',', ':')); print('wrote scenery.json')


if __name__ == '__main__':
    sys.exit(main())
