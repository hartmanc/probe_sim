#!/usr/bin/env python3
"""Car viewer data: public/cars/field/<track>/awards.json (Laguna: public/cars/field/awards.json).

Per car {number, id, awards: [verbatim award names]}, cars in the award page's order (first award row). An award row {id: Lemons results page id, event, award, team,
number, car} belongs to a field car when the number and the normalised team name both match within ONE results page;
each event's page is the one whose rows match its field best (Laguna: the page whose rows carry the event label
'Lemons: Twenty Ridiculous Years'). Prints the page chosen, the match counts and the award rows that matched no car.
Never invents a match.

Run:  python3 -I tools/race/field_awards.py <awards.json> <repo root>
"""
import json, os, re, sys

FIELDS = {  # track -> (identity rel. to public/cars/field, output rel., event label that pins the page, or None)
    'laguna_seca': ('identity.json', 'awards.json', 'Lemons: Twenty Ridiculous Years'),
    'sonoma': ('sonoma/identity.json', 'sonoma/awards.json', None),
    'buttonwillow': ('buttonwillow/identity.json', 'buttonwillow/awards.json', None),
    'mid_ohio': ('mid_ohio/identity.json', 'mid_ohio/awards.json', None),
}
PINNED = {'sonoma': 433}  # owner: Sonoma March 2026 is page 433


def norm(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower().replace('&', 'and'))


def match_rows(rows, cars):
    """Award rows -> {car id: [awards]} and the rows that matched none. cars: [{id, number, team}]."""
    by = {}
    for c in cars:
        by.setdefault((str(c['number']), norm(c['team'])), []).append(c)
    got, miss = {}, []
    for r in rows:
        t = norm(r['team'])
        hit = by.get((str(r['number']), t))
        if not hit and len(t) >= 8:  # the archive cuts long team names: same number and one name is the start of the other
            hit = [c for (n, k), cs in by.items() if n == str(r['number']) and (k.startswith(t) or t.startswith(k)) for c in cs]
        if hit and len(hit) == 1:
            got.setdefault(hit[0]['id'], []).append(r['award'])
        else:
            miss.append(r)
    return got, miss


def pick_page(rows, cars, label=None, pinned=None):
    if pinned is not None:
        return pinned
    pages = sorted({r['id'] for r in rows})
    if label:
        lp = [p for p in pages if any(r['event'] == label for r in rows if r['id'] == p)]
        if lp:
            return lp[0]
    best, bp = -1, None
    for p in pages:
        got, _ = match_rows([r for r in rows if r['id'] == p], cars)
        n = sum(len(v) for v in got.values())
        if n > best:
            best, bp = n, p
    return bp


def main(awards_path, repo):
    rows = json.load(open(awards_path))
    for track, (ident, out, label) in FIELDS.items():
        identity = json.load(open(os.path.join(repo, 'public/cars/field', ident)))
        cars = [{'id': str(c.get('id') or c['number']), 'number': str(c['number']), 'team': c['team']} for c in identity]
        page = pick_page(rows, cars, label, PINNED.get(track))
        prow = [r for r in rows if r['id'] == page]
        got, miss = match_rows(prow, cars)
        byid = {c['id']: c for c in cars}  # cars in the page's award order (first award row), the viewer's order
        res = [{'number': byid[i]['number'], 'id': i, 'awards': a} for i, a in got.items()]
        with open(os.path.join(repo, 'public/cars/field', out), 'w') as fh:
            json.dump(res, fh, indent=1); fh.write('\n')
        print(f'{track}: page {page}, {len(prow)} award rows, {sum(len(v) for v in got.values())} matched to {len(res)} cars, {len(miss)} unmatched')
        for r in miss:
            print(f"  unmatched: {r['award']} | {r['team']} | #{r['number']} | {r['car']}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
