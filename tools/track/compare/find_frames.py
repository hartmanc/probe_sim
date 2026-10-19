"""Onboard video vs sim: find the video time at which the car passes each target station s, lap by lap.

    uv run --python 3.12 --with numpy,scipy python tools/track/compare/find_frames.py

Logger GPS (log_0e98, ~1 Hz fixes) -> ENU (CONTRACTS §1) -> projected s on track.json. Camera time = logger UTC epoch
+ sync.json offset; video time = camera time - STARTS[file] (analysis/sync.py). Writes crossings.json beside this file.
"""
import csv, glob, json, math, os
from datetime import datetime
import numpy as np
from scipy.spatial import cKDTree

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
SRC = '/Users/cobyhartman/projects/starlink-go-pro'
STARTS = {"GL010045": 1791794721, "GL020045": 1791797727, "GL030045": 1791800763, "GL040045": 1791803768}
DUR = {"GL010045": 3011.0, "GL020045": 3011.0, "GL030045": 3011.0, "GL040045": 1012.3}
OFFSET = json.load(open(os.path.join(SRC, 'video/analysis/sync.json')))['0e98']['offset_s']
LAT0, LON0, R = 36.5843, -121.7535, 6378137.0

track = json.load(open(os.path.join(ROOT, 'public/tracks/laguna_seca/track.json')))
C = np.array(track['center'])[:, :2]
n = track['n']
kd = cKDTree(C)

rows = []
with open(glob.glob(os.path.join(SRC, 'LagunaData/log_0e98*.csv'))[0]) as fh:
    last = None
    for r in csv.DictReader(fh):
        if not r['gps_lat_deg'] or r['gps_fix'] in ('', '0'):
            continue
        key = (r['gps_lat_deg'], r['gps_lon_deg'])
        if key == last:
            continue  # the logger repeats the last fix at 10 Hz
        last = key
        t = datetime.fromisoformat(r['timestamp_utc']).timestamp() + OFFSET
        lat, lon = float(r['gps_lat_deg']), float(r['gps_lon_deg'])
        x = math.radians(lon - LON0) * R * math.cos(math.radians(LAT0))
        y = math.radians(lat - LAT0) * R
        rows.append((t, x, y, float(r['gps_speed_mps'] or 0)))
A = np.array(rows)
d, i = kd.query(A[:, 1:3])
s = i.astype(float)  # 1 m stations
ok = (d < 25) & (A[:, 3] > 8)  # on track and moving
t, s, v = A[ok, 0], s[ok], A[ok, 3]
print(f'{len(A)} fixes, {ok.sum()} on track and moving')

def where(tc):
    for f, st in STARTS.items():
        if st <= tc < st + DUR[f]:
            return f, tc - st
    return None, None

targets = {}
for c in track['corners']:
    nm = c['turn'] or c['name'].replace(' ', '_')
    for tag, ds in (('approach', -70), ('apex', 0), ('exit', 45)):
        targets[f'{nm}_{tag}'] = (c['s'] + ds) % n
for nm, ss in (('front_straight_approach', 3420), ('front_straight_bridge', 3540), ('front_straight_exit', 60)):
    targets[nm] = ss

out = {}
for name, st in targets.items():
    hits = []
    for k in range(len(t) - 1):
        a, b = s[k], s[k + 1]
        if t[k + 1] - t[k] > 3:
            continue
        db = (b - a + n / 2) % n - n / 2  # signed advance with wrap
        if not (0 < db < 120):
            continue
        da = (st - a) % n
        if da <= db:
            tc = t[k] + (t[k + 1] - t[k]) * da / db
            f, vt = where(tc)
            if f:
                hits.append({'file': f, 't': round(vt, 2), 'wall': datetime.utcfromtimestamp(tc).strftime('%H:%M:%S'),
                             'speed': round(float(v[k]), 1)})
    out[name] = {'s': int(st), 'hits': hits}
    print(name, st, len(hits), 'passes')
json.dump(out, open(os.path.join(HERE, 'crossings.json'), 'w'), indent=1)
