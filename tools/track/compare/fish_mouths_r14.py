"""Buttonwillow round 14 (25 Oct 2026): the fish mouths on the front straight's left shoulder, measured from the owner's
round-10 green strokes (compare/buttonwillow/owner_edges_r10/strokes.json, the drawing page's vectors; each window's
capwin frame from tracks/buttonwillow/owner/r10/w_s*.json) with the package's pit wall (scenery barriers[0]) and pit-lane
right edge closing them. Writes tracks/buttonwillow/owner/r14_mouths.json: per mouth the stations, widths, depth and the
outline (ENU and lat/lon) that config runoff_zones[].outer_latlon carries (round14/LEDGER.md).

    uv run --python 3.12 --with numpy python -I tools/track/compare/fish_mouths_r14.py
"""
import json, math, os, sys
import numpy as np
W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
R = W + '/tools/track'
S0 = json.load(open(f'{R}/compare/buttonwillow/owner_edges_r10/strokes.json'))
out = {}
for w in ['w_s4500', 'w_s4625', 'w_s0000', 'w_s0125', 'w_s0250']:
    fr = json.load(open(f'{R}/tracks/buttonwillow/owner/r10/{w}.json'))['frame']
    cx, cy = fr['centre_enu']; half, mpp = fr['half'], fr['mpp']
    L = []
    for i, st in enumerate(S0[w]['strokes']):
        P = np.array(st['pts'], float)
        Q = np.c_[cx - half + (P[:, 0] + 0.5) * mpp, cy + half - (P[:, 1] + 0.5) * mpp]
        L.append({'i': i, 'c': st['c'], 'pts': [[round(x, 2), round(y, 2)] for x, y in Q]})
    out[w] = {'frame': fr, 'strokes': L}
S = out
T = json.load(open(f'{W}/public/tracks/buttonwillow/track.json'))
SC = json.load(open(f'{W}/public/tracks/buttonwillow/scenery.json'))
sys.path.insert(0, R); import trackcfg
cfg = trackcfg.load('buttonwillow'); lat0, lon0 = cfg['origin']
Rr = 6378137.0
def ll(x, y): return (round(lat0 + math.degrees(y / Rr), 7), round(lon0 + math.degrees(x / (Rr * math.cos(math.radians(lat0)))), 7))
# round trip check
x, y = cfg.enu(*ll(100.0, -200.0)); assert abs(x - 100) < 0.02 and abs(y + 200) < 0.02, (x, y)
C = np.array(T['center'])[:, :2]; L = np.array(T['left'])[:, :2]; n = len(C)
def proj(P):
    P = np.atleast_2d(P); d = ((P[:, None, :] - C[None]) ** 2).sum(2); k = d.argmin(1)
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); N = np.c_[-t[:, 1], t[:, 0]]
    lat = ((P - C[k]) * N[k]).sum(1); hw = ((L[k] - C[k]) * N[k]).sum(1)
    along = ((P - C[k]) * t[k]).sum(1)
    return ((k + along) % n) * T["spacing_m"], lat - hw    # track metres, distance beyond the left edge
st = lambda w, i: np.array(S[w]['strokes'][i]['pts'])
wall = np.array(SC['barriers'][0]['pts'])[:, :2]
lane_r = np.array(SC['pit_lane']['parts'][0]['right'])[:, :2]
def wall_between(xa, xb):
    m = (wall[:, 0] > min(xa, xb)) & (wall[:, 0] < max(xa, xb)); return wall[m][::(1 if xa < xb else -1)]
def wall_y(x): return float(np.interp(x, wall[:, 0], wall[:, 1]))
def lane_y(x): o = np.argsort(lane_r[:, 0]); return float(np.interp(x, lane_r[o, 0], lane_r[o, 1]))
def orient(P, first='edge'):
    """the stroke from the course edge end (smaller distance beyond the edge) first"""
    _, d = proj(P[[0, -1]]); return P if d[0] <= d[1] else P[::-1]
M = []
def add(name, west, top, east, top_kind, frames, notes):
    out = np.r_[west, top, east]
    s, d = proj(out)
    sw, dw = proj(west); se, de = proj(east)
    M.append(dict(name=name, s=[round(float(s[0]), 1), round(float(s[-1]), 1)], top=top_kind,
                  width_at_edge_m=round(float(np.hypot(*(east[-1] - west[0]))), 1),
                  width_at_top_m=round(float(np.hypot(*(east[0] - west[-1]))), 1),
                  depth_m=round(float(d.max()), 1), outline_enu=[[round(float(a), 2), round(float(b), 2)] for a, b in out],
                  outline_latlon=[ll(float(a), float(b)) for a, b in out], strokes=notes, frames=frames))
# A: x -22.6 .. -6.6, the crossover OSM 34351015 across the track into the lane
# up to the pit wall (continuous across it); his flares w_s0000 #12 / #11 continue the channel north of the wall, through
# the dirt median, to his lane-side line: that part lies in the pit lane's own paving (paved to the wall) and is not drawn
wA = orient(st('w_s0000', 13)); eA = orient(st('w_s0000', 14))[::-1]
add('A', wA, wall_between(wA[-1, 0] + 0.3, eA[0, 0] - 0.3), eA, 'pit wall (continuous)',
    ['c20_s4650', 'c20_s4700', 'c20_s0000', 'onboard t004000-t005000', 'pit-lane t1312000'],
    'w_s0000 #13 (west) / #14 (east) from the course edge to the wall, the same mouth in w_s4625 #12+#18 / #19+#13; north of the wall his flares #12 / #11 (w_s4625 #14 / #15) meet his lane-side line')
# B: x 43.3 .. 56.0, the crossover OSM 34351026 across the track into the lane
wB = orient(st('w_s0000', 7)); eB = orient(st('w_s0000', 8))[::-1]
add('B', wB, wall_between(wB[-1, 0] + 0.3, eB[0, 0] - 0.3), eB, 'pit wall (continuous)',
    ['c20_s0050', 'c20_s0100', 'onboard t005500-t006500', 'pit-lane t1303000'],
    'w_s0000 #7 (west) / #8 (east) from the course edge to the wall; north of the wall his flares #10 / #9 meet his lane-side line')
# C: the pit-wall head apron, x -200 .. -148: his line from the course edge to the lane (w_s4500 #4 + #10), the lane's
# edge across (package lane right edge, 1.0 m into the lane), his turn-down to the wall head (#6), the wall, #5
wC = np.r_[orient(st('w_s4500', 4)), st('w_s4500', 10)[1:]]
xs = np.arange(-194.5, -172.6, 1.0); topC = np.c_[xs, [lane_y(x) + 1.0 for x in xs]]
d6 = st('w_s4500', 6); d6 = d6[np.argsort(-d6[:, 1])][::-1]  # from the lane line down to the wall head
wl = wall_between(d6[-1, 0] + 0.5, -151.5)
eC = np.r_[d6, wl, orient(st('w_s4500', 5))[::-1]]
add('C', wC, topC, eC, 'pit lane (1.0 m into its right edge) then the pit-wall head and the wall',
    ['c20_s4550', 'c20_s4600', 'c20_s4650', 'onboard t146000-t148500', 'onboard t000000-t001000', 'pit-lane t1240000'],
    'w_s4500 #4 + #10 (west, edge to the lane), #6 (lane line to the wall head), #5 (wall to the edge, east)')
# E: past the pit wall's east end, x 220.8 .. 228.3: his west line #12 + #17 (to y -196), across to the package lane's
# right edge (+1.0 m), his east line #16
wE = np.r_[orient(st('w_s0250', 12)), st('w_s0250', 17)]
wE = wE[np.argsort(-wE[:, 1])][::-1] if False else wE
e16 = st('w_s0250', 16)  # (228.0,-193.3) -> (228.3,-204.2)
xs = np.arange(wE[-1, 0], e16[0, 0] + 0.01, 1.0); topE = np.c_[xs, [lane_y(x) + 1.0 for x in xs]]
add('E', wE, topE, e16, 'pit-out lane (1.0 m into its right edge)',
    ['c20_s0250', 'c20_s0300', 'onboard t009500-t011000'],
    'w_s0250 #12 + #17 (west), #16 (east); his lane-side flare #13 and line #18 run along the dirt between the wall end and the lane')
for m in M:
    print(m['name'], 's', m['s'], 'edge w', m['width_at_edge_m'], 'top w', m['width_at_top_m'], 'depth', m['depth_m'], len(m['outline_enu']), 'pts')
json.dump(dict(src='round 14 (tools/track/compare/buttonwillow/round14/LEDGER.md): the owner round-10 green strokes (compare/buttonwillow/owner_edges_r10/strokes.json, '
               'capwin frames of owner/r10/w_s*.json) converted to ENU; stations and distances on public/tracks/buttonwillow (track.json, pit wall and pit lane as in rev 795c09c6cb)',
               mouths=M), open(f'{R}/tracks/buttonwillow/owner/r14_mouths.json', 'w'), indent=1)
