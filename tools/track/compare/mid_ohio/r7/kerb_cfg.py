"""Mid-Ohio round 7, step 1: the scenery.kerbs_declared entries from the capture band scan (kerb_scan.json) and the
eye-level inventory rows (the frames that show each kerb), printed as Python for tools/track/tracks/mid_ohio/config.py,
plus the kerb table for round7.md (r7/kerb_table.json).

Each scan run becomes one strip that follows the fitted edge (kerbs_declared a / b on the edge, `off` = the band centre
beyond the edge, `width` = the measured band): the race edge is the asphalt-facing face of the kerb (owner's decision 2),
so the band starts AT the edge (inner 0.0) and runs out to the paint's outer limit on the captures (the offset where the
run's paint share falls below 0.5). Yellow runs with a red outer band (the 2026 N837 frames: "yellow with red outer
band") become two strips, the yellow one from the edge and the red one beyond it, each with its measured width.
Profiles: the red / white blocks are a low raised concrete kerb (r7 kerb profile, round7.md), the yellow and red bands
flat paint (no profile).

    python3 -I tools/track/compare/mid_ohio/r7/kerb_cfg.py > /tmp/kerbs_cfg.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
scan = json.load(open(os.path.join(HERE, 'kerb_scan.json')))
inv = json.load(open(os.path.join(HERE, '..', 'inventory.json')))
O = scan['offsets']

# the corner names of the runs (package corners, config.py corners) and runs rejected after the capture check
NAMES = [('left', 299, 'T1 inside (apex) kerb'), ('left', 1030, 'T2 (Keyhole) exit kerb'), ('left', 2013, 'T4 exit kerb'),
         ('left', 2087, 'T5 (Madness) apex kerb'), ('left', 2351, 'T7 exit / T8 approach kerb'), ('left', 2446, 'T8 crest kerb'),
         ('left', 2578, 'T8 exit kerb'), ('left', 2727, 'T9 exit kerb'), ('left', 3082, 'T11 apex kerb'), ('left', 3439, 'T13 apex kerb'),
         ('right', 381, 'T1 exit kerb'), ('right', 871, 'T2 (Keyhole) apex kerb'),
         ('right', 1950, 'T4 apex kerb'), ('right', 2150, 'T6 kerb'), ('right', 2269, 'T7 apex kerb'),
         ('right', 2505, 'T8 apex kerb'), ('right', 2634, 'T9 apex kerb'), ('right', 3140, 'T11 exit kerb'),
         ('right', 3329, 'T12 (Carousel) apex kerb'), ('right', 3513, 'pit-straight kerb (T13 exit)')]
REJECT = {('left', 3595): 'the S/F timing stripes and the pit-wall foot at the line (c20_s3560): no kerb; no inventory kerb row'}

RW = ['#be383b', '#c7beb4']        # N837 t016 / t036 red (184-195, 49-63, 56-62) and white (191-206, 184-195, 172-186)
YEL = '#cba13c'                    # N837 t042 yellow (202, 161, 60)
PROFILE_RW = dict(height=0.05, face=0.25, back=0.3)


def name_of(r):
    for sd, s0, nm in NAMES:
        if r['side'] == sd and abs(r['s0'] - s0) < 3:
            return nm
    raise SystemExit(f"no name for {r['side']} {r['s0']}")


def frames(r):
    L = inv['length_m']
    out = []
    for q in inv['rows']:
        if q['kind'] != 'kerb' or q['side'] != r['side'] or q.get('scope', 'lap') != 'lap':
            continue
        s0, s1 = r['s0'], r['s1'] if r['s1'] >= r['s0'] else r['s1'] + L
        s = q['s'] if q['s'] >= s0 - 30 else q['s'] + L
        if s0 - 25 <= s <= s1 + 25:
            src = q['source'].replace('onboard:', '')
            out.append(f"{src} ({q['attrs'].get('type', '')}; s {q['s']:.0f}, {q['placement']})")
    return out


def outer(share, thr=0.5, start=0.0):
    k0 = min(range(len(O)), key=lambda k: abs(O[k] - start))
    last = None
    for k in range(k0, len(O)):
        if share[k] >= thr:
            last = k
        elif last is not None and O[k] > O[last] + 0.15:
            break
    return None if last is None else round(O[last] + 0.05, 2)


IW = [k for k, o in enumerate(O) if -0.25 <= o <= -0.05]


def white_line(pr):
    # the white edge line along the kerb's inner face: white share >= 0.3 within 0.05-0.25 m inside the edge
    return max(pr['white'][k] for k in IW) >= 0.3


entries, table = [], []
for r in scan['runs']:
    key = (r['side'], round(r['s0']))
    if any(r['side'] == sd and abs(r['s0'] - s0) < 3 for (sd, s0) in REJECT):
        table.append(dict(side=r['side'], s0=r['s0'], s1=r['s1'], rejected=[v for (sd, s0), v in REJECT.items() if sd == r['side'] and abs(r['s0'] - s0) < 3][0]))
        continue
    nm = name_of(r); fr = frames(r); pr = r['profile']
    caps = ', '.join(r['captures'])
    base = (f"kerb band scan (r7/kerb_scan.py) on {caps}: {r['kind']} paint s {r['s0']:.0f}-{r['s1']:.0f} "
            f"({r['length_m']:.0f} m) beyond the {r['side']} race edge, band median {r['width_m']:.2f} m "
            f"(p25-p75 {r['width_p25_p75'][0]:.2f}-{r['width_p25_p75'][1]:.2f})")
    csrc = '; '.join(fr) if fr else 'colour from the capture only (no inventory frame within 25 m)'
    if r['kind'] == 'redwhite':
        # the block band's outer limit from the red blocks (share >= 0.2: alternate blocks are red); the white share runs on
        # beyond it where a white line or the pit-exit paint lies next to the kerb (T1)
        w = outer(pr['red'], thr=0.2) or r['width_m']
        w = round(min(max(w, 0.6), 2.4), 2)
        e = dict(name=nm, side=r['side'], a=tuple(r['a']), b=tuple(r['b']), off=round(w / 2, 2), width=w, colors='rw',
                 pattern='blocks', profile='PROFILE_RW', edge_line=white_line(pr), colour_src=csrc, src=base + '; band from the edge (inner face = race edge) to the outer limit of the red blocks')
        entries.append(e)
        table.append(dict(name=nm, side=r['side'], s0=r['s0'], s1=r['s1'], colour='red / white blocks', edge_line=e['edge_line'], profile='raised 0.05 m', width=w,
                          off=e['off'], frames=fr, captures=r['captures'], forced=r.get('forced', False)))
    else:
        yo = outer(pr['yellow'])
        ro = outer(pr['red'], start=yo or 0.0) if r.get('red_outer') and r['red_outer'] >= 0.45 else None
        yw = round(min(max(yo or r['width_m'], 0.4), 2.2), 2)
        e = dict(name=nm, side=r['side'], a=tuple(r['a']), b=tuple(r['b']), off=round(yw / 2, 2), width=yw, colors='yel',
                 pattern='plain', edge_line=white_line(pr), colour_src=csrc, src=base + f'; yellow band 0.00-{yw:.2f} m beyond the edge')
        entries.append(e)
        row = dict(name=nm, side=r['side'], s0=r['s0'], s1=r['s1'], colour='yellow', edge_line=e['edge_line'], profile='flat paint', width=yw, off=e['off'],
                   frames=fr, captures=r['captures'])
        if ro and ro > yw + 0.2:
            rw_ = round(ro - yw, 2)
            entries.append(dict(name=nm + ', red outer band', side=r['side'], a=tuple(r['a']), b=tuple(r['b']), off=round(yw + rw_ / 2, 2),
                                width=rw_, colors='red', pattern='plain', edge_line=e['edge_line'], colour_src=csrc,
                                src=base + f'; red outer band {yw:.2f}-{ro:.2f} m beyond the edge (red share {r["red_outer"]:.2f} at the band\'s outer side)'))
            row['colour'] = f'yellow + red outer band ({yw:.2f} + {rw_:.2f} m)'
        table.append(row)

print('        kerbs_declared=[')
for e in entries:
    print(f"            dict(name={e['name']!r}, side={e['side']!r}, a={e['a']!r}, b={e['b']!r}, off={e['off']!r}, width={e['width']!r},")
    print(f"                 colors={e['colors']!r}, pattern={e['pattern']!r}" + (", profile=KERB_RAISED" if e.get('profile') else '') + (", edge_line=True" if e.get('edge_line') else '') + ",")
    print(f"                 colour_src={e['colour_src']!r},")
    print(f"                 src={e['src']!r}),")
print('        ],')
json.dump(table, open(os.path.join(HERE, 'kerb_table.json'), 'w'), indent=1)
import sys
print(f'# {len(entries)} strips from {len(scan["runs"])} scan runs', file=sys.stderr)
