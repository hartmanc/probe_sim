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
    BS.validate_declared_wall(dict(name="t", kind="tyres", rows=2))
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


def test_clip_heads_enforces_the_margin_as_a_segment_clearance():
    # a wall crossing obliquely between two rows' rays is caught by the segment check, not only by the rays
    C = [[float(k), 0.0, 0.0] for k in range(20)]
    part = dict(center=C, left=[[x, 3.0, 0.0] for x, _, _ in C], right=[[x, -3.0, 0.0] for x, _, _ in C])
    wall = dict(kind="concrete", src="w", pts=[[5.0, -2.2, 0.0], [15.0, -2.2, 0.0]])
    p = json_copy(part); BS.clip_parts_at_walls([p], [wall], margin=0.3, label="t", heads=True)
    d, _ = BS.clearance_report([p], [wall])
    assert d >= 0.3 - 1e-6
    # a wall bowing between rows (its vertex between two rays) is cleared by the margin too
    wall2 = dict(kind="concrete", src="w2", pts=[[8.0, -3.4, 0.0], [8.5, -2.4, 0.0], [9.0, -3.4, 0.0]])
    p2 = json_copy(part); BS.clip_parts_at_walls([p2], [wall2], margin=0.3, label="t", heads=True)
    d2, _ = BS.clearance_report([p2], [wall2])
    assert d2 >= 0.3 - 1e-6


def test_a_four_row_run_is_two_collided_two_row_runs():
    rec = dict(kind="tyres", h=0.8, fence=0.0, src="declared: deep", pts=[[0.0, 0.0, 0.0], [10.0, 0.0, 0.0], [20.0, 0.0, 0.0]],
               sections=[dict(from_m=10.0, to_m=999.0, color="#fff")])
    mem = BS.stacked_tyre_runs(rec, 4)
    assert len(mem) == 2 and all(m["rows"] == 2 for m in mem)
    assert [m["stack_of"]["k"] for m in mem] == [0, 1] and all(m["stack_of"]["n"] == 2 for m in mem)
    assert np.allclose(np.array(mem[1]["pts"])[:, 1], 1.2)       # 1.2 m to the polyline's left: rows 2 and 3
    assert mem[1]["sections"][0]["from_m"] == 10.0


def test_odd_rows_and_sections_on_a_thick_wall_fail_the_build():
    for r in (1, 3, 5, 7):
        with pytest.raises(SystemExit, match="even"):
            BS.validate_declared_wall(dict(name="t", kind="tyres", rows=r))
    with pytest.raises(SystemExit, match="sections"):
        BS.validate_declared_wall(dict(name="t", kind="concrete", w=0.96, sections=[dict(from_m=0, to_m=5, color="#fff")]))
    with pytest.raises(SystemExit, match="sections"):
        BS.validate_declared_wall(dict(name="t", kind="concrete", w=0.96, pattern=dict(colors=["#fff", "#000"], period_m=2)))


def test_astras_nearly_parallel_wall_clears_or_fails():
    # third review 3: centres (0,0),(0,1), left edges (10,0),(10,1), wall (-10,-0.51) to (20,0.09): the ray-wise loop
    # stopped at 0.147 m; the perpendicular correction must end at or above 0.30 m (or the build fails)
    part = dict(center=[[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]], left=[[10.0, 0.0, 0.0], [10.0, 1.0, 0.0]], right=[[-1.0, 0.0, 0.0], [-1.0, 1.0, 0.0]])
    wall = dict(kind="concrete", pts=[[-10.0, -0.51, 0.0], [20.0, 0.09, 0.0]])
    BS.clip_parts_at_walls([part], [wall], margin=0.3, label="t", heads=True)
    d, _ = BS.clearance_report([part], [wall])                     # 0.31 m: the edge rows moved 0.2 m off the wall
    assert d >= 0.3 - 1e-6, d


def test_an_unlabelled_barrier_counts_too():
    C = [[float(k), 0.0, 0.0] for k in range(20)]
    part = dict(center=C, left=[[x, 3.0, 0.0] for x, _, _ in C], right=[[x, -3.0, 0.0] for x, _, _ in C])
    wall = dict(kind="tyres", pts=[[5.0, -2.85, 0.0], [15.0, -2.85, 0.0]])   # no src: a cone line passed as a run
    BS.clip_parts_at_walls([part], [wall], margin=0.3, label="t", heads=True)
    assert BS.clearance_report([part], [wall])[0] >= 0.3 - 1e-6


def test_a_stack_is_placed_as_one_wall():
    from test_tyre_facings import _straight
    trk = _straight()
    wall = dict(kind="concrete", pts=[[100.0, -12.0, 0.0], [200.0, -12.0, 0.0]])
    # a 4-row stack drawn westward on the right side (rows toward the wall): row 0 at -6.0, rear member at -7.2, last row -7.8
    rec = dict(kind="tyres", src="deep", pts=[[150.0, -6.0, 0.0], [145.0, -6.0, 0.0], [140.0, -6.0, 0.0]])
    mem = BS.stacked_tyre_runs(rec, 4)
    BS.tyre_facings(trk, [wall] + mem, reach=2.6, off=0.55)
    # 4.2 m off the wall: out of reach, nothing moves
    assert np.allclose(np.array(mem[0]["pts"])[:, 1], -6.0) and np.allclose(np.array(mem[1]["pts"])[:, 1], -7.2)
    rec2 = dict(kind="tyres", src="deep2", pts=[[150.0, -8.0, 0.0], [145.0, -8.0, 0.0], [140.0, -8.0, 0.0]])
    mem2 = BS.stacked_tyre_runs(rec2, 4)                        # last row at -9.8: 2.2 m off the wall, within reach
    BS.tyre_facings(trk, [wall] + mem2, reach=2.6, off=0.55)
    rear, front = np.array(mem2[1]["pts"])[:, 1], np.array(mem2[0]["pts"])[:, 1]
    assert np.allclose(rear + -0.6, -11.45)                     # the rear member's last row 0.55 m in front of the wall
    assert np.allclose(front - rear, 1.2)                       # the front member followed at the row spacing


def test_an_edge_just_beyond_a_wall_is_brought_back_inside_it():
    # the lane's right edge 0.1 m beyond a wall it reaches over (no crossing between rows, no ray hit at its ends): the
    # correction must move it back toward the centre line, never further out
    C = [[float(k), 0.0, 0.0] for k in range(6)]
    part = dict(center=C, left=[[x, 3.0, 0.0] for x, _, _ in C], right=[[x, -3.0, 0.0] for x, _, _ in C])
    wall = dict(kind="concrete", pts=[[1.5, -2.9, 0.0], [3.5, -2.9, 0.0]])   # between rows 1 / 4, 0.1 m inside the edge
    BS.clip_parts_at_walls([part], [wall], margin=0.3, label="t", heads=True)
    R = np.array(part["right"])[:, 1]
    assert BS.clearance_report([part], [wall])[0] >= 0.3 - 1e-6
    assert (R >= -3.0 - 1e-9).all()                                    # never pushed outward
