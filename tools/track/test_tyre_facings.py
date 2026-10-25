"""build_scenery.tyre_facings (Sonoma round 14C, issue #12): a tyre point beyond a wall's free end (a cushion at the
wall's head, in line with it) goes onto the wall's line extended, keeping its place along it (it used to land on the end
point, so a cushion collapsed to zero length); points beside the wall still snap onto its track face.

uv run --python 3.12 --with numpy,scipy,... python -I -m pytest -q tools/track/test_tyre_facings.py
"""
import os
import sys

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_scenery as BS  # noqa: E402


def _straight():
    # a 400 m straight along +x, 1 m stations, half-width 5 m; flat ground
    n = 400
    C = [[float(k), 0.0, 0.0] for k in range(n)]
    t = dict(n=n, spacing_m=1.0, corners=[], center=C, left=[[x, 5.0, 0.0] for x, _, _ in C],
             right=[[x, -5.0, 0.0] for x, _, _ in C],
             heightfield=dict(x0=-50.0, y0=-50.0, dx=1.0, nx=500, ny=100), ortho=dict(x0=-50, y0=-50, x1=450, y1=50))
    return BS.Track(t, hf=np.zeros((100, 500), np.float32))


def test_a_cushion_beyond_the_wall_head_keeps_its_length():
    trk = _straight()
    # the wall 20 m right of the edge (y -25), from x 100 on; the 2 m bundle in line with it, its tail at the wall's head
    wall = dict(kind="concrete", pts=[[100.0, -25.0, 0.0], [200.0, -25.0, 0.0]])
    bundle = dict(kind="tyres", pts=[[98.0, -25.0, 0.0], [99.0, -25.0, 0.0], [100.0, -25.0, 0.0]])
    BS.tyre_facings(trk, [wall, bundle], reach=2.6, off=0.55)
    P = np.array(bundle["pts"])[:, :2]
    # beyond the head: on the wall's line extended, 0.55 m in front, each at its own place along it
    assert np.allclose(P, [[98.0, -24.45], [99.0, -24.45], [100.0, -24.45]])
    L = np.linalg.norm(np.diff(P, axis=0), axis=1).sum()
    assert abs(L - 2.0) < 1e-6                                         # was 0: every point onto the wall's end point


def test_a_facing_beside_the_wall_still_snaps_onto_its_face():
    trk = _straight()
    wall = dict(kind="concrete", pts=[[100.0, -25.0, 0.0], [200.0, -25.0, 0.0]])
    facing = dict(kind="tyres", pts=[[120.0, -23.5, 0.0], [130.0, -23.5, 0.0], [140.0, -23.5, 0.0]])
    BS.tyre_facings(trk, [wall, facing], reach=2.6, off=0.55)
    assert np.allclose(np.array(facing["pts"])[:, 1], -24.45)          # 0.55 m in front of the wall line
    # past the wall's far (tail) end as well
    tail = dict(kind="tyres", pts=[[201.0, -25.0, 0.0], [202.5, -25.0, 0.0]])
    BS.tyre_facings(trk, [wall, tail], reach=2.6, off=0.55)
    assert np.allclose(np.array(tail["pts"])[:, :2], [[201.0, -24.45], [202.5, -24.45]])
