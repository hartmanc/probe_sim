"""Sonoma round 14D review (25 Oct 2026): declared-wall keys the app and the gates read as the same numbers
(build_scenery.validate_declared_wall), a thick wall built as its two collision faces (thick_wall_faces), and a tyre run
that declares its `rows` facing a wall with its last row (tyre_facings).

uv run --python 3.12 --with numpy,scipy,... python -I -m pytest -q tools/track/test_r14d_walls.py
"""
import os
import sys

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_scenery as BS  # noqa: E402
from test_tyre_facings import _straight  # noqa: E402


@pytest.mark.parametrize("rows", [0, 9, 20, 2.5, "4", True])
def test_rows_outside_1_to_8_or_not_an_integer_fails_the_build(rows):
    with pytest.raises(SystemExit, match="rows"):
        BS.validate_declared_wall(dict(name="t", kind="tyres", rows=rows))


def test_rows_on_a_wall_and_w_on_armco_or_tyres_fail_the_build():
    with pytest.raises(SystemExit, match="rows"):
        BS.validate_declared_wall(dict(name="t", kind="concrete", rows=4))
    for kind in ("armco", "tyres", "pitwall", "fence"):
        with pytest.raises(SystemExit, match="only for a concrete run"):
            BS.validate_declared_wall(dict(name="t", kind=kind, w=0.96))
    with pytest.raises(SystemExit, match="width > 0"):
        BS.validate_declared_wall(dict(name="t", kind="concrete", w=0))


def test_valid_keys_pass():
    BS.validate_declared_wall(dict(name="t", kind="tyres", rows=1))
    BS.validate_declared_wall(dict(name="t", kind="tyres", rows=8))
    BS.validate_declared_wall(dict(name="t", kind="concrete", w=0.96))
    BS.validate_declared_wall(dict(name="t", w=0.96))     # kind absent: concrete


def test_thick_wall_faces_stand_w_over_2_either_side_of_the_centre():
    P = np.array([[0.0, -10.0], [10.0, -10.0], [20.0, -10.0]])   # a wall right of a track along +x: the track to its left
    front, back, side = BS.thick_wall_faces(P, +1, 0.96)
    assert np.allclose(front[:, 1], -9.52) and np.allclose(back[:, 1], -10.48)
    assert side == -1                                               # the back face to the front polyline's right


def test_a_run_with_rows_faces_the_wall_with_its_last_row():
    trk = _straight()
    wall = dict(kind="concrete", pts=[[100.0, -10.0, 0.0], [200.0, -10.0, 0.0]])
    # drawn westward along the right side: its left (its rows) toward the wall; row 0 at y -6.0, row 1 at -6.6
    legacy = dict(kind="tyres", pts=[[150.0, -6.0, 0.0], [140.0, -6.0, 0.0]])
    BS.tyre_facings(trk, [wall, legacy], reach=2.6, off=0.55)
    assert np.allclose(np.array(legacy["pts"])[:, 1], -6.0)        # 4 m off the wall line: out of reach, kept
    deep = dict(kind="tyres", rows=4, pts=[[150.0, -7.2, 0.0], [140.0, -7.2, 0.0]])   # last row at -9.0, 1 m off
    BS.tyre_facings(trk, [wall, deep], reach=2.6, off=0.55)
    P = np.array(deep["pts"])[:, 1]
    assert np.allclose(P, -9.45 + 1.8)                              # the last row 0.55 m in front of the wall, row 0 1.8 m before it


def test_clip_heads_brings_in_the_rows_round_a_wall_end_inside_the_strip():
    # a lane along +x, centre y 0, right edge y -3; a wall from x 10.5 on, 2 m right of the centre (its head between rows 10 / 11)
    C = [[float(k), 0.0, 0.0] for k in range(20)]
    part = dict(center=C, left=[[x, 3.0, 0.0] for x, _, _ in C], right=[[x, -3.0, 0.0] for x, _, _ in C])
    wall = dict(kind="concrete", pts=[[10.5, -2.0, 0.0], [30.0, -2.0, 0.0]])
    p1 = json_copy(part); BS.clip_parts_at_walls([p1], [wall], margin=0.3, label="t")
    assert abs(p1["right"][10][1] - -3.0) < 1e-9 and abs(p1["right"][11][1] - -1.7) < 1e-9   # row 10 misses the head
    p2 = json_copy(part); BS.clip_parts_at_walls([p2], [wall], margin=0.3, label="t", heads=True)
    assert abs(p2["right"][10][1] - -1.7) < 1e-9 and abs(p2["right"][11][1] - -1.7) < 1e-9


def json_copy(x):
    import json
    return json.loads(json.dumps(x))
