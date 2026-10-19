"""Set a kerb strip's extent in scenery.json from a measurement (18 Oct 2026, T11 exit: the red/white exit kerb shows on
the z20 captures against the right edge from ~3282 to ~3360 stations; the strip stopped at 3318).
    python3 -I tools/track/fix_kerb_strip.py --side -1 --kind exit --near 3300 --s0 3299.5 --s1 3386.5 [--write]
Finds the strip on --side of --kind whose s0 is within 60 m of --near and sets its s0/s1 (metres). Records the change
in scenery.json notes.
"""
import argparse, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.join(ROOT, 'public', 'tracks', 'laguna_seca')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--side', type=int, required=True); ap.add_argument('--kind', required=True); ap.add_argument('--near', type=float, required=True)
    ap.add_argument('--s0', type=float, required=True); ap.add_argument('--s1', type=float, required=True); ap.add_argument('--why', default='measured on the z20 captures')
    ap.add_argument('--write', action='store_true')
    a = ap.parse_args()
    SC = json.load(open(os.path.join(OUT, 'scenery.json')))
    cands = [s for s in SC['kerbs']['strips'] if s['side'] == a.side and s.get('kind') == a.kind and abs(s['s0'] - a.near) < 60]
    if len(cands) != 1: print(f'{len(cands)} strips match (side {a.side}, kind {a.kind}, s0 near {a.near}); nothing done'); return 1
    st = cands[0]; print(f"strip side {st['side']} kind {st['kind']}: s0 {st['s0']} -> {a.s0}, s1 {st['s1']} -> {a.s1}")
    if not a.write: print('dry run; --write to apply'); return
    st['s0'], st['s1'] = a.s0, a.s1; st['src'] = f'fix_kerb_strip.py 18 Oct 2026: {a.why}'
    SC.setdefault('notes', {})
    if isinstance(SC['notes'], dict): SC['notes'][f'kerb_{a.kind}_{int(a.near)}'] = f'fix_kerb_strip.py --side {a.side} --kind {a.kind} --near {a.near} --s0 {a.s0} --s1 {a.s1}: {a.why}'
    json.dump(SC, open(os.path.join(OUT, 'scenery.json'), 'w'), separators=(',', ':')); print('wrote scenery.json')


if __name__ == '__main__':
    sys.exit(main())
