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


def test_a_joined_corner_keeps_the_clamp():
    # Astra's review of round 14C: at a wall end joined to another wall (a corner), a cushion beyond the end must not be
    # extended along the line through the adjoining wall; it goes onto the end point as before
    trk = _straight()
    wall = dict(kind="concrete", pts=[[100.0, -25.0, 0.0], [200.0, -25.0, 0.0]])
    corner = dict(kind="concrete", pts=[[100.0, -25.0, 0.0], [100.0, -45.0, 0.0]])   # the wall turns away at its head
    bundle = dict(kind="tyres", pts=[[98.0, -25.0, 0.0], [99.0, -25.0, 0.0]])
    BS.tyre_facings(trk, [wall, corner, bundle], reach=2.6, off=0.55)
    P = np.array(bundle["pts"])[:, :2]
    assert np.allclose(P, [[100.0, -24.45], [100.0, -24.45]])           # the clamp: nothing past the joined end


def test_an_extension_crossing_another_barrier_keeps_the_clamp():
    # a free end (no rigid run within 1.5 m) whose extension's stacks would cross another barrier line (a fence 1.7 m
    # beyond the head)
    trk = _straight()
    wall = dict(kind="concrete", pts=[[100.0, -25.0, 0.0], [200.0, -25.0, 0.0]])
    other = dict(kind="fence", pts=[[98.3, -23.0, 0.0], [98.3, -30.0, 0.0]])
    cushion = dict(kind="tyres", pts=[[97.6, -25.0, 0.0], [99.5, -25.0, 0.0]])
    BS.tyre_facings(trk, [wall, other, cushion], reach=2.6, off=0.55)
    P = np.array(cushion["pts"])[:, :2]
    assert np.allclose(P[0], [100.0, -24.45])                           # through the fence: clamped onto the end
    assert np.allclose(P[1], [99.5, -24.45])                            # clear of it: on the extended line
