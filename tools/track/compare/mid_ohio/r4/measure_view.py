"""Render one perpendicular view of a 360 equirect frame with a row grid in degrees of elevation (for the heights:
camera height from the road width, then the horizon ratio). Reference only (local output).
    python -I measure_view.py <equirect.jpg> <yaw> <pitch> <out.png>"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../inventory'))
import equirect as E  # noqa
src, yaw, pitch, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
eq = np.asarray(Image.open(src).convert('RGB'))
W, H, fov = 1200, 900, 70.0
v = Image.fromarray(E.view(eq, yaw, pitch, fov, W, H))
d = ImageDraw.Draw(v); f = (W / 2) / np.tan(np.radians(fov / 2))
for el in np.arange(-40, 41, 1.0):
    y = H / 2 - f * np.tan(np.radians(el - pitch))
    if 0 <= y < H:
        d.line([(0, y), (40 if el % 5 else 90, y)], fill=(255, 255, 0)); d.text((95 if el % 5 == 0 else 45, y - 6), f'{el:g}', fill=(255, 255, 0))
v.save(out)
