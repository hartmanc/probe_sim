"""Independent stage-2 check of a no-logger ghosts.json (Mid-Ohio round 5): laps empty, the grid matches the package,
and the racing line inside the race edges (track.json left / right: the inside-of-kerb boundaries, owner decision 2)
by at least the solver's margin (1.0 m, build-track skill 2.2) at every 1 m station, the offsets interpolated the way
the app and the AI read them (linear on the s_grid_m grid, periodic).

    python3 -I tools/track/compare/mid_ohio/r5/line_check.py <package dir> [margin_m]
"""
import json
import math
import sys

pkg = sys.argv[1]
margin = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
T = json.load(open(pkg + '/track.json'))
G = json.load(open(pkg + '/ghosts.json'))
C = [p[:2] for p in T['center']]; Lf = [p[:2] for p in T['left']]; Rt = [p[:2] for p in T['right']]
n = len(C); sp = float(T['spacing_m'])
off = G['line']['offset_m']; ds = float(G['s_grid_m']); m = len(off)
fails = []
if G['laps'] != []:
    fails.append(f"laps not empty ({len(G['laps'])})")
if G['track'] != T.get('name', G['track']) and G['track'] != 'mid_ohio':
    fails.append('track id')
if abs(m * ds - n * sp) > ds:
    fails.append(f'grid {m} x {ds} m != lap {n * sp:.1f} m')
worst = (1e9, None, None)
L = n * sp
kmax = 0.0
P = []
for k in range(n):
    s = k * sp
    u = s / ds; i = int(math.floor(u)) % m; f = u - math.floor(u)
    e = (1 - f) * off[i] + f * off[(i + 1) % m]
    a, b = C[(k - 1) % n], C[(k + 1) % n]
    tx, ty = b[0] - a[0], b[1] - a[1]; h = math.hypot(tx, ty); tx /= h; ty /= h
    nx, ny = -ty, tx
    hl = (Lf[k][0] - C[k][0]) * nx + (Lf[k][1] - C[k][1]) * ny
    hr = -((Rt[k][0] - C[k][0]) * nx + (Rt[k][1] - C[k][1]) * ny)
    cl, cr = hl - e, hr + e
    P.append((C[k][0] + e * nx, C[k][1] + e * ny))
    if min(cl, cr) < worst[0]:
        worst = (min(cl, cr), k, 'left' if cl < cr else 'right')
    if min(cl, cr) < margin - 1e-3:
        fails.append(f'station {k}: clearance {min(cl, cr):.3f} m ({"left" if cl < cr else "right"})')
for k in range(n):
    a, b, c = P[k - 1], P[k], P[(k + 1) % n]
    d1 = ((c[0] - a[0]) / 2, (c[1] - a[1]) / 2); d2 = (c[0] - 2 * b[0] + a[0], c[1] - 2 * b[1] + a[1])
    kk = abs(d1[0] * d2[1] - d1[1] * d2[0]) / (math.hypot(*d1) ** 3)
    kmax = max(kmax, kk)
lap_line = sum(math.hypot(P[(k + 1) % n][0] - P[k][0], P[(k + 1) % n][1] - P[k][1]) for k in range(n))
print(json.dumps(dict(stations=n, grid_points=m, s_grid_m=ds, laps=len(G['laps']), method=G['line']['method'],
                      min_clearance_m=round(worst[0], 3), at_station=worst[1], side=worst[2], margin_m=margin,
                      offset_range_m=[round(min(off), 2), round(max(off), 2)], line_length_m=round(lap_line, 1),
                      centre_length_m=round(L, 1), min_line_radius_m=round(1 / kmax, 1), fails=fails[:20],
                      n_fails=len(fails)), indent=1))
sys.exit(1 if fails else 0)
