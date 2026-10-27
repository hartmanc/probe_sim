"""Lidar cross-check of three inventory heights (Mid-Ohio round 5; Astra round-4 review): the pit wall (inventory 0.7 m,
horizon ratio), the T1 (Firestone) footbridge deck (inventory: no height) and the main-straight covered grandstand
(inventory 7 m, storeys). The 2019 USGS lidar (local cache tools/track/cache/mid_ohio/lidar_points.npz: ENU, NAVD88,
ASPRS classes) against the package's road (track.json centre / left / right z + z0_navd88).

    uv run --python 3.12 --with numpy,scipy python -I tools/track/compare/mid_ohio/r5/lidar_heights.py \
        tools/track/cache/mid_ohio/lidar_points.npz tools/track/out/mid_ohio_r5 tools/track/compare/mid_ohio/r5/lidar_heights.json

Pit wall: the cross-section (1.5 m either side of the station, 0.25 m lateral bins) beyond the left (pit-side) edge;
the wall top is the highest bin within 6 m of the edge; its height is that minus the road's left-edge height, and minus
the ground on the pit-lane side (median of the bins 3-6 m beyond the wall). Footbridge: every return over the road
within 0.5 m of the station, minus the road centre. Grandstand: the highest return 3-120 m beyond the right edge, minus
the right edge and minus the 10th percentile of the class-2 ground between the edge and that return.
"""
import json
import sys

import numpy as np
from scipy.spatial import cKDTree

pts, pkg, out = sys.argv[1:4]
Z = np.load(pts)
x, y, z, c = Z['x'].astype(float), Z['y'].astype(float), Z['z'].astype(float), Z['c']
T = json.load(open(pkg + '/track.json'))
z0 = float(T['z0_navd88'])
C3 = np.array(T['center']); L3 = np.array(T['left']); R3 = np.array(T['right'])
C = C3[:, :2]; n = len(C); sp = float(T['spacing_m'])
t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1)[:, None]
nl = np.c_[-t[:, 1], t[:, 0]]
hl = ((L3[:, :2] - C) * nl).sum(1); hr = -((R3[:, :2] - C) * nl).sum(1)
tree = cKDTree(np.c_[x, y])


def sec(s, along, lo, hi):
    k = int(round(s / sp)) % n
    idx = np.array(tree.query_ball_point(C[k], max(abs(lo(k)), abs(hi(k))) + along + 2))
    d = np.c_[x[idx], y[idx]] - C[k]; a = d @ t[k]; l = d @ nl[k]
    m = (np.abs(a) <= along) & (l >= lo(k)) & (l <= hi(k))
    return k, l[m], z[idx][m] - z0, c[idx][m]


res = {'z0_navd88': z0, 'lidar': 'USGS OH_Statewide_Phase1_3_2019 (EPT), local cache', 'package': pkg}
wall = []
for s in (3510, 3540, 3570, 20, 50, 80, 110, 140, 170, 200):
    k, l, zz, cc = sec(s, 1.5, lambda k: hl[k] - 1, lambda k: hl[k] + 9)
    b = np.arange(hl[k], hl[k] + 9, 0.25)
    top = np.array([zz[(l >= q) & (l < q + 0.25)].max() if ((l >= q) & (l < q + 0.25)).any() else np.nan for q in b])
    win = b <= hl[k] + 6
    j = int(np.nanargmax(np.where(win, top, -np.inf)))
    pit = top[(b >= b[j] + 3) & (b <= b[j] + 6)]
    wall.append(dict(s=s, offset_from_edge_m=round(float(b[j] - hl[k] + 0.125), 2),
                     top_above_track_edge_m=round(float(top[j] - L3[k, 2]), 2),
                     top_above_pit_side_m=round(float(top[j] - np.nanmedian(pit)), 2) if np.isfinite(pit).any() else None,
                     ridge_width_m=round(float(((top > L3[k, 2] + 0.4) & (b >= b[j] - 2) & (b <= b[j] + 2)).sum() * 0.25), 2)))
res['pit_wall'] = dict(inventory=dict(h_m=0.7, method='horizon-ratio', range_m=[0.64, 0.75], frame='360 k52 (t26) left'),
                       sections=wall,
                       median_above_track_edge_m=round(float(np.median([w['top_above_track_edge_m'] for w in wall])), 2),
                       median_above_pit_side_m=round(float(np.median([w['top_above_pit_side_m'] for w in wall if w['top_above_pit_side_m'] is not None])), 2))
deck = []
for s in range(224, 243, 2):
    k, l, zz, cc = sec(s, 0.5, lambda k: -hr[k], lambda k: hl[k])
    d = zz - C3[k, 2]
    hi = d > 2.0
    deck.append(dict(s=s, returns=int(len(d)), over_road=int(hi.sum()),
                     deck_p50_above_road_m=round(float(np.median(d[hi])), 2) if hi.any() else None,
                     deck_p90_above_road_m=round(float(np.percentile(d[hi], 90)), 2) if hi.any() else None,
                     classes=sorted(set(int(v) for v in cc[hi]))))
on = [q for q in deck if q['over_road'] > 0.5 * q['returns']]
res['footbridge'] = dict(inventory='no height (bridges deferred to the scenery stage with lidar)', sections=deck,
                         deck_stations=[on[0]['s'], on[-1]['s']] if on else None,
                         deck_top_above_road_m=round(float(np.median([q['deck_p50_above_road_m'] for q in on])), 2) if on else None)
gs = []
for s in list(range(3530, 3597, 15)) + list(range(0, 196, 15)):
    k, l, zz, cc = sec(s, 3.0, lambda k: -hr[k] - 120, lambda k: -hr[k] - 3)
    j = int(np.argmax(zz)); far = -hr[k] - l[j]
    g = zz[(cc == 2) & (l > l[j]) & (l < -hr[k] - 3)]
    gs.append(dict(s=s, highest_beyond_right_edge_m=round(float(far), 1), above_right_edge_m=round(float(zz[j] - R3[k, 2]), 2),
                   above_ground_between_m=round(float(zz[j] - np.percentile(g, 10)), 2) if len(g) else None))
stand = [q for q in gs if q['above_right_edge_m'] > 4.0]
res['grandstand'] = dict(inventory=dict(h_m=7, method='storeys', rows='covered grandstand, red roof, right of the main straight'),
                         sections=gs, sections_over_4m=[q['s'] for q in stand],
                         above_right_edge_m=[min(q['above_right_edge_m'] for q in stand), max(q['above_right_edge_m'] for q in stand)] if stand else None,
                         above_ground_between_m=[min(q['above_ground_between_m'] for q in stand), max(q['above_ground_between_m'] for q in stand)] if stand else None)
json.dump(res, open(out, 'w'), indent=1)
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'sections'} if isinstance(v, dict) else v for k, v in res.items()}, indent=1))
