"""Mid-Ohio round 10 diagnosis: per compass sector, in the band beyond the lidar box (>= 10 m outside it) and within
BAND m of the centreline: area, OSM forest share, the NAIP dark-canopy share, the far trees (count, crown cover), the
candidate count against the declared cap.
    uv run --python 3.12 --with numpy,scipy,pillow python -I far_diag.py <package dir> [--json out]"""
import json, sys, os
import numpy as np
import sys as _s, os as _o; _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
from far_common import *
pkg = sys.argv[1]
S = json.load(open(os.path.join(pkg, 'scenery.json')))
img = np.asarray(Image.open(os.path.join(TT, 'cache/mid_ohio/naip_far_2500_1000.png')).convert('RGB'))
dist, C = track_distance(os.path.join(pkg, 'track.json')); X, Y = grid_xy()
cx, cy = C[:, 0].mean(), C[:, 1].mean()
sec = sector_index(X, Y, cx, cy); osm = osm_forest_mask(); dark, lum, bg, green = far_dark(img)
b = LIDAR_BOX; outside = ~((X > b[0] + 10) & (X < b[2] - 10) & (Y > b[1] + 10) & (Y < b[3] - 10))
F = np.array(S['far_trees']['data']).reshape(-1, 5) * S['far_trees']['scale']
fc, fr = to_px(F[:, 0], F[:, 1]); fr_i = np.clip(fr.astype(int), 0, W - 1); fc_i = np.clip(fc.astype(int), 0, W - 1)
tsec = sector_index(F[:, 0], F[:, 1], cx, cy); tdist = dist[fr_i, fc_i]; tin = osm[fr_i, fc_i]
d_ = np.load(os.path.join(TT, 'cache/mid_ohio/far_canopy_cells.npz')); bx = d_['box']
CH = (np.clip(d_['VEG'] - d_['DEM'], 0, None) > 2.0) & (d_['MULTI'] > 0.18)
cxs = bx[0] + (np.arange(CH.shape[1]) + 0.5) * 2.0; cys = bx[1] + (np.arange(CH.shape[0]) + 0.5) * 2.0
jj = np.clip(((X - bx[0]) / 2.0).astype(int), 0, CH.shape[1] - 1); ii = np.clip(((Y - bx[1]) / 2.0).astype(int), 0, CH.shape[0] - 1)
lid = CH[ii, jj] & (X >= bx[0]) & (X < bx[2]) & (Y >= bx[1]) & (Y < bx[3]); inring = (X >= bx[0]) & (X < bx[2]) & (Y >= bx[1]) & (Y < bx[3])
rows = []
for band in ((230, 600), (600, 1200)):
    ring = outside & (dist >= band[0]) & (dist < band[1])
    for k, nm in enumerate(SECT):
        m = ring & (sec == k); mr = m & inring; area = m.sum() * PX * PX / 1e6
        tm = (tsec == k) & (tdist >= band[0]) & (tdist < band[1]); cover = (np.pi * F[tm, 4] ** 2).sum() / (m.sum() * PX * PX)
        rows.append(dict(band=f'{band[0]}-{band[1]}', sector=nm, area_km2=round(float(area), 3), osm_forest=round(float(osm[m].mean()), 3),
                         naip_dark=round(float(dark[m].mean()), 3), lidar_canopy=round(float(lid[mr].mean()), 3) if mr.sum() else None, ring_share=round(float(mr.sum() / max(m.sum(), 1)), 2), far_trees=int(tm.sum()), far_cover=round(float(cover), 3), far_cover_ring=round(float((np.pi * F[tm & (np.abs(F[:,0] - 0) < 1100) & (F[:,1] > bx[1]) & (F[:,1] < bx[3]), 4] ** 2).sum() / max(mr.sum() * PX * PX, 1)), 3),
                         trees_in_osm_forest=int((tm & tin).sum())))
for r in rows: print(r)
cand = int(((dark) & outside).sum())
print('far-tree cap: 7000 trees drawn;', len(F), 'in the package; dark pixels outside the lidar box', cand,
      '; trees in OSM forest overall', int(tin.sum()), 'of', len(F), '; OSM forest share of the far box', round(float(osm.mean()), 3),
      '; dark share inside OSM forest', round(float(dark[osm].mean()), 3), 'outside', round(float(dark[~osm].mean()), 3))
print('lum / local mean inside OSM forest: median lum', np.median(lum[osm & outside]).round(1), 'outside forest', np.median(lum[~osm & outside]).round(1))
if '--json' in sys.argv: json.dump(rows, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
