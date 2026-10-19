"""Pit wall at the pit exit (owner, 18 Oct 2026: "Does pit exit actually look like this?"). On the z20 captures the hot-pit
wall between the track and the pit lane ends where the pit-out lane begins (about station 70); from there to T1 the
separation is the painted strip only, and a low wall resumes at T1 (the second pitwall run, stations 182-243). The OSM
pitwall polyline kept running along the painted strip to about station 140.
    python3 -I tools/track/fix_pitwall_exit.py [--end 70] [--write]
Removes every point of a `pitwall` barrier run whose nearest station lies in --end..180 and which sits within 3 m of
the track's left edge, so the first run ends at --end. scenery.json only.
"""
import argparse, json, math, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--end', type=int, default=70); ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    T = json.load(open(os.path.join(OUT, 'track.json'))); SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    n = T['n']; C, L = T['center'], T['left']

    def station_of(p):
        return min(range(-80, 260), key=lambda k: math.hypot(C[k % n][0] - p[0], C[k % n][1] - p[1])) % n

    removed = []
    for ri, run in enumerate(SC['barriers']):
        if run.get('kind') != 'pitwall': continue
        keep = []
        for p in run['pts']:
            k = station_of(p); near = math.hypot(L[k][0] - p[0], L[k][1] - p[1]) < 3.0
            if a.end < k <= 180 and near: removed.append((ri, k)); continue
            keep.append(p)
        run['pts'] = keep
    if removed: print(f'{len(removed)} pit-wall points removed, stations {min(r[1] for r in removed)}..{max(r[1] for r in removed)} (run {removed[0][0]})')
    else: print('nothing to remove')
    if not a.write: print('dry run; --write to apply'); return
    SC.setdefault('notes', {})
    if isinstance(SC['notes'], dict): SC['notes']['pitwall_exit'] = f'18 Oct 2026: fix_pitwall_exit.py --end {a.end}: hot-pit wall ends at the pit-out lane start; painted strip only from there to the T1 wall'
    json.dump(SC, open(os.path.join(OUT, 'scenery.json'), 'w'), separators=(',', ':')); print('wrote scenery.json')


if __name__ == '__main__':
    sys.exit(main())
