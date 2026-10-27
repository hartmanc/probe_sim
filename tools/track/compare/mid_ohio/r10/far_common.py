"""Mid-Ohio round 10: shared readers for the far-tree diagnosis (python -I; numpy, scipy, pillow).
Frames: ENU metres about the track origin (geo.py: R 6378137, equirectangular at the origin latitude); the far grid is
the far ortho's 5 m / px, row 0 north, x -2500..2500."""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__)); TT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
R_E = 6378137.0; LAT0, LON0 = 40.689, -82.636; COSL = math.cos(math.radians(LAT0))
FH, PX, W = 2500.0, 5.0, 1000
LIDAR_BOX = (-590.0, -790.0, 560.0, 850.0)
def enu(lat, lon): return math.radians(lon - LON0) * R_E * COSL, math.radians(lat - LAT0) * R_E
def to_px(x, y): return (np.asarray(x) + FH) / PX, (FH - np.asarray(y)) / PX
def _ring(geom): return [to_px(*enu(p['lat'], p['lon'])) for p in geom]
def osm_forest_mask(path=os.path.join(HERE, 'osm_wood.json')):
    d = json.load(open(path)); im = Image.new('L', (W, W), 0); dr = ImageDraw.Draw(im)
    for e in d['elements']:
        if e['type'] == 'way' and 'geometry' in e:
            dr.polygon(_ring(e['geometry']), fill=1)
    for e in d['elements']:   # multipolygon: outer ways filled, inner ways cut back out (members given as geometry)
        if e['type'] != 'relation': continue
        for m in e['members']:
            if m['type'] == 'way' and m.get('geometry'):
                dr.polygon(_ring(m['geometry']), fill=1 if m['role'] == 'outer' else 0)
    return np.array(im, bool)
def grid_xy():
    c = (np.arange(W) + 0.5) * PX - FH
    return np.meshgrid(c, c[::-1])        # X east, Y north, row 0 north
def track_distance(track_json):
    T = json.load(open(track_json)); C = np.array(T['center'])[:, :2]
    c, r = to_px(C[:, 0], C[:, 1]); m = np.ones((W, W), bool)
    m[np.clip(r.astype(int), 0, W - 1), np.clip(c.astype(int), 0, W - 1)] = False
    return ndi.distance_transform_edt(m) * PX, C
SECT = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
def sector_index(X, Y, cx, cy):
    b = (np.degrees(np.arctan2(X - cx, Y - cy)) + 360 + 22.5) % 360
    return (b // 45).astype(int)
def far_dark(img):
    """the builder's far_trees dark-canopy mask (build_scenery.far_trees), unchanged"""
    a = img.astype(np.float32); lum = a.mean(-1); bg = ndi.uniform_filter(lum, 25); green = a[..., 1] - a[..., 0]
    return (lum < bg - 18) & (lum < 95) & (green > -6), lum, bg, green
