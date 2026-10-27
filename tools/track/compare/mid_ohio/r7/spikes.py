"""Mid-Ohio round 7: isolated lidar spikes (2019 USGS lidar, local cache) in an ENU box: the highest non-ground return per
1 m cell above the bare-earth DEM (the max class-2 return in the cell, else the box median), local maxima over `min_h`
whose 3 m ring holds nothing over half their height (a pole, a mast, a post), with the track station and side.

    uv run --python 3.12 --with numpy,scipy python -I tools/track/compare/mid_ohio/r7/spikes.py x0 x1 y0 y1 [min_h]
"""
import json, os, sys
import numpy as np
from scipy.ndimage import maximum_filter
HERE = os.path.dirname(os.path.abspath(__file__)); TT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
x0, x1, y0, y1 = map(float, sys.argv[1:5]); mh = float(sys.argv[5]) if len(sys.argv) > 5 else 6.0
d = np.load(os.path.join(TT, 'cache/mid_ohio/lidar_points.npz'))
m = (d['x'] >= x0) & (d['x'] < x1) & (d['y'] >= y0) & (d['y'] < y1)
x, y, z, c = d['x'][m], d['y'][m], d['z'][m], d['c'][m]
nx, ny = int(x1 - x0), int(y1 - y0)
ix = np.clip((x - x0).astype(int), 0, nx - 1); iy = np.clip((y - y0).astype(int), 0, ny - 1)
G = np.full((ny, nx), np.nan); A = np.full((ny, nx), -1e9)
g = c == 2
np.fmax.at(G, (iy[g], ix[g]), z[g])
from scipy.ndimage import generic_filter
med = np.nanmedian(G)
Gf = np.where(np.isnan(G), med, G)
# fill ground holes with a local minimum filter of the known ground
from scipy.ndimage import grey_erosion
Gf2 = np.where(np.isnan(G), grey_erosion(np.where(np.isnan(G), 1e9, G), size=7), G); Gf2 = np.where(Gf2 > 1e8, med, Gf2)
ng = (c == 1) | (c == 17) | (c == 18)
np.maximum.at(A, (iy[ng], ix[ng]), z[ng])
H = A - Gf2; H[A < -1e8] = 0
loc = (H == maximum_filter(H, size=5)) & (H > mh)
T = json.load(open(os.path.join(TT, 'out/mid_ohio_r7/track.json')))
C = np.array(T['center'])[:, :2]; tg = np.roll(C, -1, 0) - np.roll(C, 1, 0); tg /= np.linalg.norm(tg, axis=1, keepdims=True); NL = np.c_[-tg[:, 1], tg[:, 0]]
import math
for j, i in zip(*np.nonzero(loc)):
    h = H[j, i]
    ring = H[max(0, j - 3):j + 4, max(0, i - 3):i + 4]
    share = float((ring > h / 2).mean())
    if share > 0.2:
        continue
    px, py = x0 + i + 0.5, y0 + j + 0.5
    k = ((C - [px, py]) ** 2).sum(1).argmin(); lat = (np.array([px, py]) - C[k]) @ NL[k]
    la = 40.689 + math.degrees(py / 6378137.0); lo = -82.636 + math.degrees(px / (6378137.0 * math.cos(math.radians(40.689))))
    print(f"spike ({px:.1f}, {py:.1f}) lat/lon ({la:.7f}, {lo:.7f}) h {h:.1f} m ring share {share:.2f} s {k} {'L' if lat > 0 else 'R'} {abs(lat):.1f} m")
