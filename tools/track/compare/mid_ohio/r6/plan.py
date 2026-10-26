"""Mid-Ohio round 6: the hood-camera pose plan for camera_walk.ts --replay (one pose per sheet of hood_r6/frames.json,
on the centre facing the driving direction, as camera_walk's 'fwd' pose; plus, for the T8 investigation, the same
stations on the solver's racing line (ghosts.json offset) and a crest sight-line series s 2380-2500 every 20 m).

    python3 -I tools/track/compare/mid_ohio/r6/plan.py <package dir> <frames.json> <out walk_plan.json>
"""
import json
import math
import os
import sys

pkg, fj, out = sys.argv[1:4]
T = json.load(open(os.path.join(pkg, 'track.json')))
G = json.load(open(os.path.join(pkg, 'ghosts.json')))
F = json.load(open(fj))
C = T['center']; n = len(C); sp = T['spacing_m']
off = G['line']['offset_m']; ds = G['s_grid_m']; m = len(off)


def pose(s, lat=0.0):
    i = int(round(s / sp)) % n
    a, b, c = C[(i - 2) % n], C[(i + 2) % n], C[i]
    h = math.atan2(b[1] - a[1], b[0] - a[0])
    nx, ny = -math.sin(h), math.cos(h)          # left normal
    return [c[0] + lat * nx, c[1] + lat * ny, None if lat else c[2]], h


def line_off(s):
    u = s / ds; i = int(math.floor(u)) % m; f = u - math.floor(u)
    return (1 - f) * off[i] + f * off[(i + 1) % m]


shots = []
for sh in F['sheets']:
    p, h = pose(sh['s'])
    shots.append(dict(file=f"sim/{sh['id']}.jpg", s=sh['s'], side='fwd', pos=p, heading=h, yaw=0, kind='centre'))
for sh in F['sheets']:
    if sh['corner'] in ('T8', 'T4'):
        e = line_off(sh['s'])
        p, h = pose(sh['s'], e)
        shots.append(dict(file=f"sim/{sh['id']}_line.jpg", s=sh['s'], side='fwd', pos=p, heading=h, yaw=0, kind=f'line {e:+.2f} m'))
for s in range(2380, 2581, 20):
    e = line_off(s)
    p, h = pose(s, e)
    shots.append(dict(file=f"sim/t8_walk_s{s:04d}_line.jpg", s=s, side='fwd', pos=p, heading=h, yaw=0, kind=f'T8 walk, line {e:+.2f} m'))
for s in range(1830, 1891, 10):
    e = line_off(s)
    p, h = pose(s, e)
    shots.append(dict(file=f"sim/t4_entry_s{s:04d}_line.jpg", s=s, side='fwd', pos=p, heading=h, yaw=0, kind=f'T4 entry, line {e:+.2f} m'))
json.dump(dict(track='mid_ohio', shots=shots), open(out, 'w'), indent=1)
print(len(shots), 'poses')
