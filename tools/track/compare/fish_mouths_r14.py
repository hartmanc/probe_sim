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
# A: x -22.6 .. -6.6, the crossover OSM 34351015 across the track into the lane: round 14, the owner's decision of
# 26 Oct 2026 ("Stop the lane paving at my line: dirt median, A and B as channels"): the channel runs from the course
# edge across the pit wall (continuous) and the dirt median to his lane-side line: his #13 + #12 (west) / #11 + #14
# (east), the top along his line between the flares' tops
LINE = np.array(json.load(open(f'{R}/tracks/buttonwillow/owner/r14_lane_line.json'))['enu'])
def line_between(xa, xb):
    xs = np.arange(np.ceil(min(xa, xb) + 0.3), max(xa, xb) - 0.3, 1.0)
    P = np.c_[xs, np.interp(xs, LINE[:, 0], LINE[:, 1])]
    return P if xa < xb else P[::-1]
wA = np.r_[orient(st('w_s0000', 13)), st('w_s0000', 12)]
eA = np.r_[st('w_s0000', 11)[::-1], orient(st('w_s0000', 14))[::-1]]
add('A_channel', wA, line_between(wA[-1, 0], eA[0, 0]), eA, "his lane-side line (the channel through the dirt median; the pit wall continuous across it)",
    ['c20_s4650', 'c20_s4700', 'c20_s0000', 'onboard t004000-t005000', 'pit-lane t1312000'],
    'his whole green at A (the coverage check): w_s0000 #13 + #12 (west) / #11 + #14 (east), the top along his lane-side line')
# the mouth part itself: course edge to the pit wall (north of the wall the channel is the pit lane's paving: the lane's
# edge follows his flares #12 / #11 down to the wall there, owner/r14_lane_line.json)
wA = orient(st('w_s0000', 13)); eA = orient(st('w_s0000', 14))[::-1]
add('A', wA, wall_between(wA[-1, 0] + 0.3, eA[0, 0] - 0.3), eA, 'pit wall (continuous)',
    ['c20_s4650', 'c20_s4700', 'c20_s0000', 'onboard t004000-t005000', 'pit-lane t1312000'],
    'w_s0000 #13 (west) / #14 (east) from the course edge to the wall, the same mouth in w_s4625 #12+#18 / #19+#13')
# B: x 43.3 .. 56.0, the crossover OSM 34351026 across the track into the lane; a channel to his line as A
wB = np.r_[orient(st('w_s0000', 7)), st('w_s0000', 10)]
eB = np.r_[st('w_s0000', 9)[::-1], orient(st('w_s0000', 8))[::-1]]
add('B_channel', wB, line_between(wB[-1, 0], eB[0, 0]), eB, "his lane-side line (the channel through the dirt median; the pit wall continuous across it)",
    ['c20_s0050', 'c20_s0100', 'onboard t005500-t006500', 'pit-lane t1303000'],
    'his whole green at B (the coverage check): w_s0000 #7 + #10 (west) / #9 + #8 (east), the top along his lane-side line')
wB = orient(st('w_s0000', 7)); eB = orient(st('w_s0000', 8))[::-1]
add('B', wB, wall_between(wB[-1, 0] + 0.3, eB[0, 0] - 0.3), eB, 'pit wall (continuous)',
    ['c20_s0050', 'c20_s0100', 'onboard t005500-t006500', 'pit-lane t1303000'],
    'w_s0000 #7 (west) / #8 (east) from the course edge to the wall; north of the wall the channel is the lane (its edge on his flares #10 / #9)')
# C: the pit-wall head apron, x -200 .. -148: his line from the course edge to the lane (w_s4500 #4 + #10), the lane's
# edge across (package lane right edge, 0.15 m into the lane), his turn-down to the wall head (#6), the wall, #5
wC = np.r_[orient(st('w_s4500', 4)), st('w_s4500', 10)[1:]]
# his line up to where it meets the top (0.15 m inside the lane's right edge); his hook beyond it (#10's last 1 m, inside
# the lane) is the lane's own paving (review: the hook crossed the lowered top)
k_ = next(i for i, (x, y) in enumerate(wC) if y >= lane_y(x) + 0.15)
a_, b_ = wC[k_ - 1], wC[k_]; ga, gb = a_[1] - lane_y(a_[0]) - 0.15, b_[1] - lane_y(b_[0]) - 0.15
wC = np.r_[wC[:k_], [a_ + (b_ - a_) * (ga / (ga - gb))]]
# the top along the lane's edge to x -174.5 (east of it the lane's edge drops round the nose to the wall head; the
# line goes on to his turn-down #6, whose top is his lane line)
xs = np.arange(np.ceil(wC[-1, 0] + 0.5), -174.4, 1.0); topC = np.c_[xs, [lane_y(x) + 0.15 for x in xs]]
d6 = st('w_s4500', 6); d6 = d6[np.argsort(-d6[:, 1])]  # north first: from the lane line down to the wall head (review fix: was south first, a backtrack)
wl = wall_between(d6[-1, 0] + 0.5, -151.5)
eC = np.r_[d6, wl, orient(st('w_s4500', 5))[::-1]]
add('C', wC, topC, eC, 'pit lane (0.15 m into its right edge) then the pit-wall head and the wall',
    ['c20_s4550', 'c20_s4600', 'c20_s4650', 'onboard t146000-t148500', 'onboard t000000-t001000', 'pit-lane t1240000'],
    'w_s4500 #4 + #10 (west, edge to the lane), #6 (lane line to the wall head), #5 (wall to the edge, east)')
# E: past the pit wall's east end, x 220.8 .. 228.3: his west line #12 + #17 (to y -196), across to the package lane's
# right edge (+0.15 m), his east line #16
wE = np.r_[orient(st('w_s0250', 12)), st('w_s0250', 17)]
wE = wE[np.argsort(-wE[:, 1])][::-1] if False else wE
e16 = st('w_s0250', 16)  # (228.0,-193.3) -> (228.3,-204.2)
xs = np.arange(wE[-1, 0], e16[0, 0] + 0.01, 1.0); topE = np.c_[xs, [lane_y(x) + 0.15 for x in xs]]
add('E', wE, topE, e16, 'pit-out lane (0.15 m into its right edge)',
    ['c20_s0250', 'c20_s0300', 'onboard t009500-t011000'],
    'w_s0250 #12 + #17 (west), #16 (east); his lane-side flare #13 and line #18 run along the dirt between the wall end and the lane')
# the outline traversed once, in order: its station along the track never falls back more than his own stroke's hook
for m in M:
    sv, _ = proj(np.array(m['outline_enu']))
    back = float((np.maximum.accumulate(sv) - sv).max())
    m['max_backtrack_m'] = round(back, 2)
    print(m['name'], 'max backtrack along the track %.2f m' % back)
for m in M:
    print(m['name'], 's', m['s'], 'edge w', m['width_at_edge_m'], 'top w', m['width_at_top_m'], 'depth', m['depth_m'], len(m['outline_enu']), 'pts')
json.dump(dict(src='round 14 (tools/track/compare/buttonwillow/round14/LEDGER.md): the owner round-10 green strokes (compare/buttonwillow/owner_edges_r10/strokes.json, '
               'capwin frames of owner/r10/w_s*.json) converted to ENU; stations and distances on public/tracks/buttonwillow (track.json, pit wall and pit lane as in rev 795c09c6cb)',
               mouths=M), open(f'{R}/tracks/buttonwillow/owner/r14_mouths.json', 'w'), indent=1)
