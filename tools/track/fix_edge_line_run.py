"""Add or extend a painted edge-line run in scenery.json from the imagery (18 Oct 2026 evening: the T2 approach right
side had no run from 240 to 544 although every clean capture, satellite_clean/c20_a1..a8, shows a continuous white line
there; the spline fit, fit_edges_spline.py, puts the edge on that line).
    python3 -I tools/track/fix_edge_line_run.py --side -1 --s0 250 --s1 544 [--write]
Runs on the same side that overlap or touch [s0, s1] (within 2 m) are merged into one run. Distances in metres."""
import argparse, json, os, sys
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'public', 'tracks', 'laguna_seca')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--side', type=int, required=True); ap.add_argument('--s0', type=float, required=True)
    ap.add_argument('--s1', type=float, required=True); ap.add_argument('--why', default='white line on the clean captures'); ap.add_argument('--write', action='store_true')
    a = ap.parse_args(); SC = json.load(open(os.path.join(OUT, 'scenery.json'))); runs = SC['edge_lines']['runs']
    s0, s1 = a.s0, a.s1; keep = []
    for r in runs:
        if r['side'] == a.side and r['s0'] <= s1 + 2 and r['s1'] >= s0 - 2: s0, s1 = min(s0, r['s0']), max(s1, r['s1']); print('merging', r)
        else: keep.append(r)
    keep.append({'side': a.side, 's0': round(s0, 1), 's1': round(s1, 1)}); keep.sort(key=lambda r: (r['side'], r['s0']))
    print('new run', keep[[i for i, r in enumerate(keep) if r['side'] == a.side and r['s0'] == round(s0, 1)][0]])
    if not a.write: print('dry run; --write to apply'); return
    SC['edge_lines']['runs'] = keep
    SC.setdefault('notes', {})[f'edge_line_{a.side}_{int(a.s0)}'] = f'18 Oct 2026: fix_edge_line_run.py --side {a.side} --s0 {a.s0} --s1 {a.s1}: {a.why}'
    json.dump(SC, open(os.path.join(OUT, 'scenery.json'), 'w'), separators=(',', ':')); print('wrote scenery.json')


if __name__ == '__main__':
    sys.exit(main())
