"""Mid-Ohio round 8, owner note "there should be a lot more trees, or denser trees, especially by the back straight and
going through Thunder Valley": the 2019 lidar canopy (cells of 1 m whose highest class-1 return stands > 2 m over the
class-2 ground) against the package's modelled trees (scenery.json trees, crown discs) in bands 5-150 m beyond each edge,
per 100 m of track: canopy cover share, modelled crown cover share, modelled trees per 100 m.

    uv run --python 3.12 --with numpy,scipy python -I tools/track/compare/mid_ohio/r8/tree_density.py <package dir> [--json out]
"""
import json, os, sys
import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
HERE = os.path.dirname(os.path.abspath(__file__)); TT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
pkg = sys.argv[1]
T = json.load(open(os.path.join(pkg, 'track.json'))); S = json.load(open(os.path.join(pkg, 'scenery.json')))
d = np.load(os.path.join(TT, 'cache/mid_ohio/lidar_points.npz'))
x, y, z, c = d['x'], d['y'], d['z'], d['c']
x0, y0 = float(x.min()), float(y.min()); nx, ny = int(x.max() - x0) + 1, int(y.max() - y0) + 1
ix = (x - x0).astype(int); iy = (y - y0).astype(int)
G = np.full((ny, nx), np.nan, np.float32); np.fmin.at(G, (iy[c == 2], ix[c == 2]), z[c == 2])
gi = np.isnan(G); idx = ndi.distance_transform_edt(gi, return_distances=False, return_indices=True); G = G[tuple(idx)]
V = np.full((ny, nx), -1e9, np.float32); m = c == 1; np.maximum.at(V, (iy[m], ix[m]), z[m])
CHM = np.where(V > -1e8, V - G, 0); can = CHM > 2.0
D = np.array(S['trees']['data']).reshape(-1, 5) * S['trees']['scale']
crowns = np.zeros((ny, nx), bool)
for tx, ty, tz, th, tr in D:
    cx, cy = int(tx - x0), int(ty - y0); r = int(np.ceil(tr))
    yy, xx = np.ogrid[max(0, cy - r):min(ny, cy + r + 1), max(0, cx - r):min(nx, cx + r + 1)]
    crowns[max(0, cy - r):min(ny, cy + r + 1), max(0, cx - r):min(nx, cx + r + 1)] |= (yy - cy) ** 2 + (xx - cx) ** 2 <= tr ** 2
C = np.array(T['center'])[:, :2]; n = len(C)
out = []
for side in ('left', 'right'):
    E = np.array(T[side])[:, :2]
    for b0 in range(0, n, 100):
        cells = set()
        for i in range(b0, min(n, b0 + 100)):
            nv = (E[i] - C[i]); nv /= np.linalg.norm(nv)
            for off in range(5, 151, 1):
                p = E[i] + nv * off; cells.add((int(p[1] - y0), int(p[0] - x0)))
        cl = np.array([q for q in cells if 0 <= q[0] < ny and 0 <= q[1] < nx])
        cc = can[cl[:, 0], cl[:, 1]].mean(); mc = crowns[cl[:, 0], cl[:, 1]].mean()
        # trees in the band (by nearest station)
        kd = cKDTree(C); _, k = kd.query(D[:, :2]); lat = ((D[:, :2] - C[k]) * np.c_[-(np.roll(C, -1, 0) - np.roll(C, 1, 0))[k, 1], (np.roll(C, -1, 0) - np.roll(C, 1, 0))[k, 0]]).sum(1)
        inb = (k >= b0) & (k < b0 + 100) & ((lat > 0) == (side == 'left'))
        out.append(dict(side=side, s0=b0, canopy=round(float(cc), 3), modelled=round(float(mc), 3), trees=int(inb.sum())))
for r in out:
    print(f"{r['side']:5s} {r['s0']:4d} canopy {r['canopy']:.2f} modelled {r['modelled']:.2f} trees {r['trees']}")
if '--json' in sys.argv: json.dump(out, open(sys.argv[sys.argv.index('--json') + 1], 'w'), indent=1)
