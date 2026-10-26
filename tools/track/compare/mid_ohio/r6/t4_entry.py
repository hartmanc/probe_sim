"""Mid-Ohio round 6, the T4-entry wheel-off (round 5: 290 steps, 0.29 s, at s 1861-1871): the autopilot's lateral
error trace (drive.ts sim_lap.csv, one row per 2 m of the line grid) against the line's clearance to each race edge,
and the same measures on the published Sonoma, Buttonwillow and Laguna packages driven with the same command, to see
how their braking zones at the 1.0 m margin fare. Wheel clearance = line clearance - outward lateral error - half the
Probe's wheel track (car.json trackFront 1.514 m / 2).

    python3 -I tools/track/compare/mid_ohio/r6/t4_entry.py <out.json> <name>=<package dir>:<drive out dir> ...
"""
import csv
import json
import math
import sys

HT = 1.514 / 2
out = sys.argv[1]
res = {}
for arg in sys.argv[2:]:
    name, rest = arg.split('=', 1); pkg, drv = rest.split(':')
    T = json.load(open(pkg + '/track.json')); G = json.load(open(pkg + '/ghosts.json'))
    C = T['center']; Lf = T['left']; Rt = T['right']; n = len(C); sp = T['spacing_m']
    off = G['line']['offset_m']; ds = G['s_grid_m']; m = len(off)

    def clear(s):
        k = int(round(s / sp)) % n
        a, b = C[(k - 1) % n], C[(k + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]; h = math.hypot(tx, ty); tx /= h; ty /= h
        nx, ny = -ty, tx
        hl = (Lf[k][0] - C[k][0]) * nx + (Lf[k][1] - C[k][1]) * ny
        hr = -((Rt[k][0] - C[k][0]) * nx + (Rt[k][1] - C[k][1]) * ny)
        u = s / ds; i = int(math.floor(u)) % m; f = u - math.floor(u)
        e = (1 - f) * off[i] + f * off[(i + 1) % m]
        return hl - e, hr + e, e
    rows = []
    for r in csv.DictReader(open(drv + '/sim_lap.csv')):
        s = float(r['s']); cl, cr, e = clear(s); le = float(r['lat_err_m'])
        rows.append(dict(s=round(s, 1), v_kmh=float(r['v_kmh']), brake=float(r['brake']), gLong=float(r['gLong']), gLat=float(r['gLat']),
                         line_off=round(e, 3), line_clear_left=round(cl, 3), line_clear_right=round(cr, 3), lat_err=le,
                         wheel_clear_left=round(cl - le - HT, 3), wheel_clear_right=round(cr + le - HT, 3), on_track=int(r['on_track'])))
    near = [r for r in rows if min(r['line_clear_left'], r['line_clear_right']) <= 1.05]
    nb = [r for r in near if r['brake'] > 0.05]
    def outward(r):
        return r['lat_err'] if r['line_clear_left'] < r['line_clear_right'] else -r['lat_err']
    worst = min(rows, key=lambda r: min(r['wheel_clear_left'], r['wheel_clear_right']))
    res[name] = dict(
        rows_off_track=sum(1 for r in rows if not r['on_track']),
        min_wheel_clear_m=round(min(worst['wheel_clear_left'], worst['wheel_clear_right']), 3), at_s=worst['s'],
        line_at_margin_rows=len(near), line_at_margin_braking_rows=len(nb),
        max_outward_err_at_margin_m=round(max((outward(r) for r in near), default=0), 3),
        max_outward_err_at_margin_braking_m=round(max((outward(r) for r in nb), default=0), 3),
        braking_at_margin_zones=sorted({int(r['s'] // 50 * 50) for r in nb}))
    if name == 'mid_ohio':
        res[name]['trace_1780_1960'] = [r for r in rows if 1780 <= r['s'] <= 1960]
json.dump(res, open(out, 'w'), indent=1)
for k, v in res.items():
    print(k, {a: b for a, b in v.items() if a != 'trace_1780_1960'})
for r in res['mid_ohio']['trace_1780_1960']:
    print(f"s {r['s']:7.1f} v {r['v_kmh']:6.1f} brk {r['brake']:.2f} gLong {r['gLong']:+.2f} gLat {r['gLat']:+.2f} off {r['line_off']:+.2f} "
          f"clrL {r['line_clear_left']:.2f} err {r['lat_err']:+.3f} wheelL {r['wheel_clear_left']:+.3f} on {r['on_track']}")
