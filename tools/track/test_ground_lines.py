"""Round 13 (Sonoma owner notes 130-136): the unmodelled-ground-lines gate, the ortho inpainting under structures and
the bridge-deck shadow search, on a synthetic package (a straight track along x, a grass ortho at 0.6 m/px)."""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "gates"))

import ground_lines  # noqa: E402

O = {"file": "ortho.jpg", "x0": -150.0, "y0": -90.0, "x1": 150.0, "y1": 90.0, "width_px": 500, "height_px": 300}


def to_px(x, y):
    return (x - O["x0"]) / 0.6, (O["y1"] - y) / 0.6


def package(tmp, barriers, dark_y=-20.0):
    """A 300 m straight (half-width 5) with a dark 1.2 m line along y = dark_y from x -60 to 60 and its lit top beside it."""
    n = 300
    C = [[x - 150.0, 0.0, 0.0] for x in range(n)]
    T = {"n": n, "spacing_m": 1.0, "length_m": 300.0, "center": C, "left": [[x, 5.0, 0.0] for x, _, _ in C],
         "right": [[x, -5.0, 0.0] for x, _, _ in C], "ortho": O}
    rng = np.random.default_rng(1)
    im = np.zeros((O["height_px"], O["width_px"], 3), np.float32) + np.array([96, 120, 70], np.float32)
    im += rng.normal(0, 3, im.shape)
    x0, _ = to_px(-60, 0); x1, _ = to_px(60, 0); _, yd = to_px(0, dark_y); _, yp = to_px(0, dark_y - 1.5)
    im[int(yd) - 1:int(yd) + 1, int(x0):int(x1)] = 25
    im[int(yp) - 1:int(yp) + 1, int(x0):int(x1)] = 200
    os.makedirs(tmp, exist_ok=True)
    Image.fromarray(im.clip(0, 255).astype(np.uint8)).save(os.path.join(tmp, "ortho.jpg"), quality=95)
    json.dump(T, open(os.path.join(tmp, "track.json"), "w"))
    json.dump({"barriers": barriers}, open(os.path.join(tmp, "scenery.json"), "w"))
    return tmp


def wall(y):
    return {"kind": "concrete", "h": 1.0, "pts": [[x, y, 0.0] for x in range(-60, 61, 10)], "src": "w"}


def test_line_with_no_barrier_is_listed(tmp_path):
    rep = ground_lines.scan(package(str(tmp_path), []), {"contrast": 40, "min_len": 30})
    assert len(rep["findings"]) >= 1
    assert all(f["side"] == "right" and 13 <= f["out0"] <= 17 for f in rep["findings"])
    assert not rep["open"]          # no barrier near it: listed, not failing (not barrier-related)


def test_wall_set_back_from_the_line_fails(tmp_path):
    rep = ground_lines.scan(package(str(tmp_path), [wall(-24.0)]), {"contrast": 40, "min_len": 30})
    assert rep["open"] and all(f["barrier_related"] for f in rep["open"])   # the T2 / T4 case: the wall 4 m behind


def test_wall_on_the_line_passes_and_dispositions_apply(tmp_path):
    rep = ground_lines.scan(package(str(tmp_path), [wall(-20.5)]), {"contrast": 40, "min_len": 30})
    assert not rep["open"]
    rep = ground_lines.scan(package(str(tmp_path), [wall(-24.0)]),
                            {"contrast": 40, "min_len": 30, "dispositions": [{"side": "right", "s": (80, 220), "what": "x", "why": "y"}]})
    assert not rep["open"] and all(f["disposition"] for f in rep["findings"])


def test_inpaint_and_deck_shadow():
    import build_scenery as BS
    rng = np.random.default_rng(2)
    img = (np.zeros((300, 500, 3)) + np.array([90, 110, 60]) + rng.normal(0, 3, (300, 500, 3))).clip(0, 255).astype(np.uint8)
    # a bridge deck image (pale strip 3 m wide along x -20..20 at y 0) and its shadow 6 m north
    for (y_, val) in ((0.0, 230), (6.0, 20)):
        _, py = to_px(0, y_); px0, _ = to_px(-20, 0); px1, _ = to_px(20, 0)
        img[int(py) - 2:int(py) + 3, int(px0):int(px1)] = val
    b = {"id": "1", "a": [-20.0, 0.0], "b": [20.0, 0.0], "width": 3.0, "ends": []}
    sh = BS.deck_shadow(img, O, b, 2.5)
    assert sh is not None and abs(sh[0][1] - 6.0) <= 1.0
    polys = BS.structure_footprints({"bridges": [b]}, {"margin": 1.5, "bridge_margin": 3.0}, img, O)
    assert any("shadow" in k for k, _ in polys)
    out, n = BS.inpaint_ortho(img, polys, O)
    assert n > 0
    for y_ in (0.0, 6.0):
        _, py = to_px(0, y_); px, _ = to_px(0, 0)
        assert abs(out[int(py), int(px)].astype(float).mean() - img[10, 10].astype(float).mean()) < 25
