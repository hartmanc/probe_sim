"""Stage-2 validation without logger laps (Mid-Ohio round 5): the N837 Catalyst speed trace (round 4,
r4/speed_lap_n837.json; a Lemons car, not a Probe) against the racing line's speed profile (drive.ts target_profile.csv,
the solver's prediction) and the autopilot lap (drive.ts sim_lap.csv), per corner and per straight. Shapes and ratios,
not absolutes: each value is also given relative to the median ratio over all corners / straights.

    python3 -I tools/track/compare/mid_ohio/r5/footage_compare.py <package dir> <drive out dir> <out.json>

N837 samples (about 1 Hz) are put on the track by the inventory's N837 time map (inventory/source.json anchors, profile
interpolation; leave-one-out residuals up to 14.8 m): a corner minimum from them is the lowest 1 Hz sample in the window
(it can miss the true minimum by the speed change over half a second) and its position carries the map's error.
"""
import csv
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'track', 'inventory'))
import inventory as INV  # noqa: E402

pkg, drive, out = sys.argv[1:4]
track = json.load(open(os.path.join(pkg, 'track.json')))
src = json.load(open(os.path.join(ROOT, 'tools/track/compare/mid_ohio/inventory/source.json')))
anchors, L = INV.anchors_from(src, track)
tm = INV.TimeMap(anchors, L, INV.speed_profile(track), track['spacing_m'])
lap = json.load(open(os.path.join(ROOT, 'tools/track/compare/mid_ohio/r4/speed_lap_n837.json')))
MPH = 0.44704 * 3.6
n837 = [(tm.s(r['t']) % L, r['reading'] * MPH, r['t']) for r in lap['rows']
        if r['reading'] is not None and lap['t0'] <= r['t'] <= lap['t1']]
prof = [(float(r['s']), float(r['vprof_kmh'])) for r in csv.DictReader(open(os.path.join(drive, 'target_profile.csv')))]
curv = [(float(r['s']), float(r['curv'])) for r in csv.DictReader(open(os.path.join(drive, 'target_profile.csv')))]
sim = [(float(r['s']), float(r['v_kmh']), float(r['t'])) for r in csv.DictReader(open(os.path.join(drive, 'sim_lap.csv')))]
summ = json.load(open(os.path.join(drive, 'summary.json')))
corners = sorted(track['corners'], key=lambda c: c['s'])


def inwin(s, a, b):
    s %= L; a %= L; b %= L
    return a <= s <= b if a <= b else (s >= a or s <= b)


def vmin(series, a, b):
    v = [(x[1], x[0]) for x in series if inwin(x[0], a, b)]
    return min(v) if v else (None, None)


def vmax(series, a, b):
    v = [(x[1], x[0]) for x in series if inwin(x[0], a, b)]
    return max(v) if v else (None, None)


W = 60.0
rows_c = []
for c in corners:
    a, b = c['s'] - W, c['s'] + W
    n_, ns = vmin(n837, a, b); p_, ps = vmin(prof, a, b); s_, ss = vmin(sim, a, b)
    k = [x for x in curv if inwin(x[0], a, b)]
    rline = 1 / max(abs(x[1]) for x in k)
    rows_c.append(dict(corner=c.get('name') or c.get('turn'), s=round(c['s'], 1), R_centre_m=c.get('radius_m'),
                       R_line_min_m=round(rline, 1), n837_kmh=round(n_, 1) if n_ else None,
                       n837_at=round(ns, 0) if ns is not None else None, profile_kmh=round(p_, 1), profile_at=round(ps, 0),
                       sim_kmh=round(s_, 1), sim_at=round(ss, 0)))
rows_s = []
for c, d in zip(corners, corners[1:] + corners[:1]):
    a, b = c['s'] + W, d['s'] - W + (L if d['s'] < c['s'] else 0)
    if b - a < 40:      # corners closer than 2 W + 40 m: no straight between them
        continue
    n_, ns = vmax(n837, a, b); p_, ps = vmax(prof, a, b); s_, ss = vmax(sim, a, b)
    rows_s.append(dict(straight=f"{c.get('name') or c.get('turn')} -> {d.get('name') or d.get('turn')}",
                       n837_kmh=round(n_, 1) if n_ else None, profile_kmh=round(p_, 1), sim_kmh=round(s_, 1)))
for rows in (rows_c, rows_s):
    for key in ('profile', 'sim'):
        rat = [r[f'{key}_kmh'] / r['n837_kmh'] for r in rows if r['n837_kmh']]
        med = statistics.median(rat)
        for r in rows:
            if r['n837_kmh']:
                r[f'{key}_over_n837'] = round(r[f'{key}_kmh'] / r['n837_kmh'], 3)
                r[f'{key}_rel_median_pct'] = round((r[f'{key}_kmh'] / r['n837_kmh'] / med - 1) * 100, 1)
        rows[0].setdefault('_median', {})[key] = round(med, 3)
res = dict(n837=dict(lap_s=lap['lap_s'], distance_m=lap['distance_m'], mean_kmh=round(lap['distance_m'] / lap['lap_s'] * 3.6, 1),
                     samples=len(n837), min_kmh=round(min(v for _, v, _ in n837), 1), max_kmh=round(max(v for _, v, _ in n837), 1)),
           profile=dict(lap_s=round(summ['profileLapTime'], 2), min_kmh=round(min(v for _, v in prof), 1), max_kmh=round(max(v for _, v in prof), 1)),
           sim=dict(lap_s=round(summ['lapTime'], 2), min_kmh=round(min(v for _, v, _ in sim), 1), max_kmh=round(max(v for _, v, _ in sim), 1),
                    off_track_steps=summ['offTrackSteps'], max_lat_err_m=round(summ['maxLatErr'], 2)),
           lap_time_ratio=dict(profile_over_n837=round(summ['profileLapTime'] / lap['lap_s'], 3),
                               sim_over_n837=round(summ['lapTime'] / lap['lap_s'], 3)),
           corners=rows_c, straights=rows_s, window_m=W, length_m=L)
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ('corners', 'straights')}, indent=1))
print('corner              s  Rline  N837  @s     prof  @s     sim   @s    prof/N  rel%   sim/N  rel%')
for r in rows_c:
    print(f"{r['corner']:<18}{r['s']:6.0f} {r['R_line_min_m']:5.0f} {r['n837_kmh'] or 0:6.1f} {r['n837_at'] or 0:5.0f} {r['profile_kmh']:6.1f} {r['profile_at']:5.0f} "
          f"{r['sim_kmh']:6.1f} {r['sim_at']:5.0f}  {r.get('profile_over_n837', 0):.3f} {r.get('profile_rel_median_pct', 0):+5.1f}  "
          f"{r.get('sim_over_n837', 0):.3f} {r.get('sim_rel_median_pct', 0):+5.1f}")
print('straight                          N837   prof    sim   prof/N rel%  sim/N rel%')
for r in rows_s:
    print(f"{r['straight']:<32}{r['n837_kmh'] or 0:6.1f} {r['profile_kmh']:6.1f} {r['sim_kmh']:6.1f}  {r.get('profile_over_n837', 0):.3f} "
          f"{r.get('profile_rel_median_pct', 0):+5.1f}  {r.get('sim_over_n837', 0):.3f} {r.get('sim_rel_median_pct', 0):+5.1f}")
