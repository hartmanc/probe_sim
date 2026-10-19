"""Front-straight pit wall as a straight line (18-19 Oct 2026 night): the OSM pit-wall polyline bows up to 1.6 m toward the
track at stations 3390-3440 while the real wall is straight (clean captures c20_b3400/b3475); the left edge, kept
2 m from it, had a matching dent. Points of `pitwall` runs whose nearest station is in --lo..--hi and which lie more
than --tol m off the line RANSAC-fitted to the wall (fix_front_straight_lines.ransac, same stations as its left edge)
are projected onto that line. scenery.json only.
    uv run --python 3.12 --with numpy,pillow python -I tools/track/fix_pitwall_straight.py [--write]"""
import argparse, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fix_front_straight_lines import ransac, OUT  # noqa: E402


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--lo', type=int, default=3370); ap.add_argument('--hi', type=int, default=30)
    ap.add_argument('--tol', type=float, default=0.25); ap.add_argument('--write', action='store_true'); a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json'))); n = T['n']
    C = np.array(T['center'])[:, :2]; st = lambda p: int(np.argmin(np.hypot(*(C - np.array(p[:2])).T)))
    ks = set(k % n for k in range(a.lo, a.hi + n + 1)) if a.hi < a.lo else set(range(a.lo, a.hi + 1))
    pw = np.array([p[:2] for b in SC['barriers'] if b['kind'] == 'pitwall' for p in b['pts']])
    sel = np.array([st(p) in set(k % n for k in range(3390, 3590)) for p in pw])
    m, d, nin = ransac(pw[sel], 0.25, min_len=60); nr = np.array([-d[1], d[0]]); moved = []
    for b in SC['barriers']:
        if b['kind'] != 'pitwall': continue
        for i, p in enumerate(b['pts']):
            r = (np.array(p[:2]) - m) @ nr
            if st(p) in ks and abs(r) > a.tol:
                q = np.array(p[:2]) - r * nr; moved.append((st(p), round(float(r), 2))); b['pts'][i] = [round(float(q[0]), 3), round(float(q[1]), 3)] + list(p[2:])
    print(f'wall line from {nin} inliers; {len(moved)} points moved onto it:', moved)
    if not a.write: print('dry run; --write to apply'); return
    SC.setdefault('notes', {})['pitwall_straight'] = f'18-19 Oct 2026: fix_pitwall_straight.py --lo {a.lo} --hi {a.hi}: {len(moved)} pit-wall points projected onto the straight wall line'
    json.dump(SC, open(os.path.join(OUT, 'scenery.json'), 'w'), separators=(',', ':')); print('wrote scenery.json')


if __name__ == '__main__':
    sys.exit(main())
