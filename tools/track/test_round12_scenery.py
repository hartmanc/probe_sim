"""Buttonwillow round 12 builder keys: declared_walls seam='far' (build_scenery.seam_far) only rotates a closed ring and refuses a
ring whose ends are not identical (a dropped or snapped point would change its closing segment); pit_lane.lane.to_walls.across;
closed_roads[].join_lane."""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_scenery as BS  # noqa: E402


def ring(n=11, r=3.5):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    P = np.c_[r * np.cos(a), r * np.sin(a)]
    return np.vstack([P, P[:1]])


def segs(P):
    return {tuple(sorted((tuple(P[i]), tuple(P[i + 1])))) for i in range(len(P) - 1)}


@pytest.mark.parametrize("j", [0, 1, 5, 10])
def test_rotation_keeps_every_vertex_and_segment(j):
    P = ring()
    R = BS.seam_far(P, j)
    assert np.array_equal(R[0], R[-1]) and np.array_equal(R[0], P[j])
    assert len(R) == len(P)
    assert sorted(map(tuple, R[:-1])) == sorted(map(tuple, P[:-1]))
    assert segs(R) == segs(P)


def test_nearly_closed_ring_is_refused():
    P = ring()
    P[-1] = P[-1] + [0.03, 0.0]   # ends 3 cm apart: not a closed ring
    with pytest.raises(SystemExit):
        BS.seam_far(P, 3)


def test_open_run_is_refused():
    with pytest.raises(SystemExit):
        BS.seam_far(ring()[:-3], 2)


def test_lane_edge_goes_through_a_declared_opening_to_the_wall_line():
    """to_walls.across (round 12): in an opening the lane's edge reaches the wall's line with no margin; beside a wall
    it stops `margin` short of it as before; beyond reach nothing moves."""
    xs = np.arange(0.0, 30.0, 1.0)
    part = {"center": [[x, 0.0, 0.0] for x in xs], "left": [[x, 2.0, 0.0] for x in xs], "right": [[x, -2.0, 0.0] for x in xs]}
    wall = {"kind": "concrete", "pts": [[-1.0, 5.0, 0.0], [10.0, 5.0, 0.0]]}
    lon_a, lat_a = BS.bl.lonlat(10.0, 5.0)
    lon_b, lat_b = BS.bl.lonlat(20.0, 5.0)
    BS.extend_parts_to_walls([part], [wall], reach=6.0, margin=0.3, across=[((float(lat_a), float(lon_a)), (float(lat_b), float(lon_b)))])
    L = np.array(part["left"])
    assert np.allclose(L[xs < 10, 1], 4.7)            # beside the wall: 0.3 m short of it
    assert np.allclose(L[(xs > 10) & (xs < 20), 1], 5.0, atol=0.01)   # in the opening: on the wall's line
    assert np.allclose(L[xs > 20, 1], 2.0)            # past the opening: unchanged
    assert np.allclose(np.array(part["right"])[:, 1], -2.0)


def test_join_lane_closes_the_lip_and_fades_across(monkeypatch):
    """closed_roads[].join_lane (round 12): where a road's edge meets the lane's edge its profile takes the lane's edge
    height, fading to 0 at `reach` m across; stations away from the join keep their profile; the lane is unchanged."""
    fr = [-1, -2 / 3, -1 / 3, 0, 1 / 3, 2 / 3, 1]
    xs = np.arange(0.0, 40.0, 1.0)
    lane = {"center": [[x, 0.0, 0.0] for x in xs], "left": [[x, 4.0, 0.0] for x in xs], "right": [[x, -4.0, 0.0] for x in xs],
            "profile_z": [[0.10] * 7 for _ in xs]}
    # the road north of the lane: its right edge on the lane's left edge for x 10..20 only, 3 m off elsewhere
    ry = [4.0 if 10 <= x <= 20 else 7.0 for x in xs]
    road = {"turn": "strip", "center": [[x, y + 6.0, 0.0] for x, y in zip(xs, ry)], "left": [[x, y + 12.0, 0.0] for x, y in zip(xs, ry)],
            "right": [[x, y, 0.0] for x, y in zip(xs, ry)], "profile_z": [[0.0] * 7 for _ in xs]}
    monkeypatch.setattr(BS, "SC_CFG", {"closed_roads": [{"name": "strip", "join_lane": {"reach": 6.0}}]})
    BS.join_lane([lane], [road], fr)
    P = np.array(road["profile_z"])
    assert np.allclose(P[10:21, -1], 0.10)          # the joining (right) edge on the lane's edge height
    assert np.allclose(P[10:21, 3], 0.0)            # 6 m across (the centre of a 12 m road): faded out
    assert np.allclose(P[10:21, 4], 0.10 * 1 / 3, atol=1e-3)   # 4 m across: a third left
    assert np.allclose(P[:5], 0.0) and np.allclose(P[26:], 0.0)   # away from the join (beyond the ramp): unchanged
    assert 0 < P[8, -1] < 0.10                      # the ramp along the road
    assert np.allclose(np.array(lane["profile_z"]), 0.10)
