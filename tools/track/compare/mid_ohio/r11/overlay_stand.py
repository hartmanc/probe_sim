"""Plan view of the starter's stand (round 11): the package ortho, the course edges, the pit wall, the stand's four legs and cabin footprint.
    uv run --python 3.12 --with numpy --with pillow python -I overlay_stand.py <package dir> <out.png>"""
import json, math, sys, numpy as np
from PIL import Image, ImageDraw
pk = sys.argv[1]; t = json.load(open(pk + '/track.json')); s = json.load(open(pk + '/scenery.json')); o = t['ortho']
im = Image.open(pk + '/ortho.jpg').convert('RGB'); W, H = im.size; mx = (o['x1'] - o['x0']) / W
st = [x for x in s['structures'] if x['type'] == 'starter_stand'][0]; cx, cy = st['c']; R = 14.0; sc = 24
x0, x1, y0, y1 = cx - R, cx + R, cy - R, cy + R
c = im.crop((int((x0 - o['x0']) / mx), int((o['y1'] - y1) / mx), int((x1 - o['x0']) / mx), int((o['y1'] - y0) / mx))).resize((int(2 * R * sc),) * 2, Image.LANCZOS)
d = ImageDraw.Draw(c); tf = lambda p: ((p[0] - x0) * sc, (y1 - p[1]) * sc)
for k, col in (('left', (255, 255, 0)), ('right', (255, 255, 0))): d.line([tf(p) for p in t[k]], fill=col, width=2)
for b in s['barriers']:
    d.line([tf(p) for p in b['pts']], fill={'pitwall': (0, 255, 255)}.get(b['kind'], (255, 128, 0)), width=3)
for z in s['pit_lane']['parts']:
    for k in ('left', 'right'): d.line([tf(p) for p in z[k]], fill=(0, 255, 0), width=2)
h = math.radians(st['heading_deg']); u = np.array([math.cos(h), math.sin(h)]); v = np.array([-math.sin(h), math.cos(h)]); c0 = np.array(st['c'])
hw, hd = st['w'] / 2, st['d'] / 2
for a in (-hw + .2, hw - .2):
    for b in (-hd + .2, hd - .2):
        P = c0 + u * a + v * b; q = [tf(P + u * i * 0.09 + v * j * 0.09) for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]; d.polygon(q, outline=(255, 0, 255))
d.polygon([tf(c0 + u * a + v * b) for a, b in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))], outline=(255, 0, 0))
c.save(sys.argv[2])
