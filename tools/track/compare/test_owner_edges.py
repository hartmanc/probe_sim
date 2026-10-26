"""owner_edges.py on a synthetic frame: a straight centreline along +x, the owner's red strokes 5 m left and 4 m right of
it, a green stroke beyond; the per-station points come back at those offsets."""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import owner_edges as OE  # noqa: E402


def test_synthetic_frame(tmp_path):
    n = 400
    C = np.c_[np.arange(n) - 200.0, np.zeros(n)]
    track = {'center': C.tolist(), 'spacing_m': 1.0}
    half, mpp = 30.0, 0.1
    W = int(2 * half / mpp)
    a = np.full((W, W, 4), 255, np.uint8); a[..., :3] = 200
    def row(y):   # pixel row of world y (the frame is centred on station 200 = (0, 0))
        return int((half - y) / mpp)
    for y, col in ((5.0, (230, 30, 30)), (-4.0, (230, 30, 30)), (12.0, (30, 220, 30))):
        r = row(y); a[r - 1:r + 2, 20:W - 20, :3] = col
    png = tmp_path / 'frame.png'; Image.fromarray(a).save(png)
    d = OE.run(str(png), 200.0, half, mpp, track)
    L = np.array(d['left_enu_xys']); R = np.array(d['right_enu_xys'])
    assert len(L) > 50 and len(R) > 50
    assert np.allclose(L[:, 1], 5.0, atol=0.06) and np.allclose(R[:, 1], -4.0, atol=0.06)
    assert len(d['green_enu_xy']) > 20 and np.allclose(np.array(d['green_enu_xy'])[:, 1], 12.0, atol=0.2)


def test_by_stroke_vector_origin():
    """--by-stroke: a stroke along image row y px reads world y = cy + half - y * mpp with --vector-origin continuous (the
    drawing page's canvas coordinates, as capwin draws / edge_mark_transfer.cjs projects), and half a pixel lower with the
    default 'pixel' reading (Mid-Ohio round 3)"""
    n = 400
    C = np.c_[np.arange(n) - 200.0, np.zeros(n)]
    track = {'center': C.tolist(), 'spacing_m': 1.0}
    half, mpp = 30.0, 0.1
    y_px = (half - 5.0) / mpp   # world y = 5.0 in continuous canvas coordinates
    st = [{'c': 'red', 'kind': 'line', 'pts': [[20.0, y_px], [580.0, y_px]]}]
    d0 = OE.run_strokes(st, 200.0, half, mpp, track, (0.0, 0.0), origin=0.0)
    d5 = OE.run_strokes(st, 200.0, half, mpp, track, (0.0, 0.0))
    L0 = np.array(d0['left_enu_xys']); L5 = np.array(d5['left_enu_xys'])
    assert np.allclose(L0[:, 1], 5.0, atol=1e-6) and np.allclose(L5[:, 1], 5.0 - 0.5 * mpp, atol=1e-6)
    assert d0['frame'].get('vector_origin') == 'continuous' and 'vector_origin' not in d5['frame']
