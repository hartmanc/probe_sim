"""The terrain override of stage 1 and its stage-3 drape (tools/track/terrain_override.py, Sonoma round 14A).

uv run --python 3.12 --with numpy,scipy,pytest python -I -m pytest -q tools/track/test_terrain_override.py

A synthetic straight course (x -150..150 along y = 0, half-width 5 m, a 3 % cross-slope falling to the right) over a
lumpy lidar ground: inside the region the surface continues the course at its edges (height and cross-slope), does not
follow short lumps or a trailer-sized spike, keeps to the lidar's long grade, takes bridge-deck returns where it has
them, and leaves the heightfield outside the region and its margin untouched; no region = the same array.
"""
import os
import sys
import tempfile

import pytest

np = pytest.importorskip("numpy")
pytest.importorskip("scipy")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import terrain_override as TO  # noqa: E402

FR = [-1, -0.6667, -0.3333, 0, 0.3333, 0.6667, 1]
DX = 2.0
X0, Y0 = -200.0, -100.0
NX, NY = 201, 101
SLOPE = 0.03


def course():
    xs = np.arange(-150.0, 151.0)
    C = np.c_[xs, np.zeros_like(xs)]
    hl = np.full(len(xs), 5.0)
    hr = np.full(len(xs), 5.0)
    prof = np.array([[-f * 5 * SLOPE + 0.01 * x for f in FR] for x in xs])
    return C, hl, hr, prof


def grid(fn):
    gx, gy = np.meshgrid(X0 + np.arange(NX) * DX, Y0 + np.arange(NY) * DX)
    return fn(gx, gy).astype("<f4")


def plane(x, y):
    return SLOPE * y + 0.01 * x


def lumpy(x, y):
    return plane(x, y) + 0.004 * y - 0.2 + 0.15 * np.sin(x / 2.7) * np.cos(y / 1.9)


def enu(lat, lon):            # the tests give the polygon directly in metres (lat = y, lon = x)
    return lon, lat


REGION = dict(name="test", latlon=[(-40, -60), (-40, 60), (40, 60), (40, -60)], margin=15.0, ramp=1.5, edge_hold=1.0,
              edge_band=4.0, smooth_m=40.0)


def at(hf, x, y):
    from scipy.ndimage import map_coordinates
    return float(map_coordinates(hf.astype(float), [[(y - Y0) / DX], [(x - X0) / DX]], order=1)[0])


def test_no_region_is_the_same_array():
    C, hl, hr, prof = course()
    hf = grid(lumpy)
    out, rep = TO.apply(hf, (X0, Y0), DX, [], enu, C, hl, hr, prof, FR, log=lambda *a: None)
    assert out is hf and rep == []


def test_course_continued_at_the_edges_and_lumps_not_followed():
    C, hl, hr, prof = course()
    hf = grid(lumpy)
    out, rep = TO.apply(hf, (X0, Y0), DX, [REGION], enu, C, hl, hr, prof, FR, log=lambda *a: None)
    for x in (-30.0, 0.0, 22.0):
        for side in (1, -1):
            e = 5.0 * side
            z_edge = SLOPE * e + 0.01 * x
            # height and cross-slope match the course at the edge (C1)
            assert abs(at(out, x, e + side * 0.05) - z_edge) < 0.01
            so = (at(out, x, e + side * 1.0) - at(out, x, e)) * side
            assert abs(so - SLOPE) < 0.006
    # beyond the band the surface keeps the lidar's long grade (0.4 % across) but not its 0.15 m lumps
    y = np.arange(14.0, 36.0, 1.0)
    z = np.array([at(out, 4.3, v) for v in y])
    d2 = np.abs(z[:-2] - 2 * z[1:-1] + z[2:])
    assert d2.max() < 0.01
    zr = np.array([at(hf, 4.3, v) for v in y])
    assert np.abs(zr[:-2] - 2 * zr[1:-1] + zr[2:]).max() > 0.03          # the lidar itself is lumpy there
    # outside the polygon and its margin: untouched
    assert np.array_equal(out[:, :60], hf[:, :60]) and np.array_equal(out[:, 140:], hf[:, 140:])
    assert rep[0]["nodes_inside"] > 0


def test_a_trailer_in_the_ground_class_is_rejected():
    C, hl, hr, prof = course()
    base = grid(plane)
    hf = base.copy()
    j, i = int((10 - X0) / DX), int((25 - Y0) / DX)
    hf[i - 1:i + 2, j - 2:j + 3] += 1.2                                     # a 10 x 6 m block 1.2 m high
    out, _ = TO.apply(hf, (X0, Y0), DX, [REGION], enu, C, hl, hr, prof, FR, log=lambda *a: None)
    assert at(out, 10.0, 25.0) - at(base, 10.0, 25.0) < 0.1


def test_bridge_deck_returns_replace_the_creek_bed():
    C, hl, hr, prof = course()
    # a creek 4 m deep across x 10..20 beyond the course (y 12..40); the deck returns at road level over it
    hf = grid(lambda x, y: plane(x, y) - 4.0 * ((x > 8) & (x < 22) & (y > 10)))
    rng = np.random.default_rng(1)
    px = rng.uniform(9, 21, 4000)
    py = rng.uniform(12, 40, 4000)
    gx = rng.uniform(-40, 40, 4000)
    gy = rng.uniform(-60, -10, 4000)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "points.npz")
        np.savez(path, x=np.r_[px, gx].astype(np.float32), y=np.r_[py, gy].astype(np.float32),
                 z=np.r_[plane(px, py), plane(gx, gy)].astype(np.float32), c=np.r_[np.full(4000, 17), np.full(4000, 2)].astype(np.uint8))
        reg = dict(REGION, deck_returns=True, deck_fade=6.0)
        out, rep = TO.apply(hf, (X0, Y0), DX, [reg], enu, C, hl, hr, prof, FR, log=lambda *a: None, points=path, z0=0.0)
    assert rep[0]["deck_nodes"] > 50
    assert abs(at(out, 15.0, 25.0) - plane(15.0, 25.0)) < 0.1             # on the deck, not 4 m down in the creek
    assert at(hf, 15.0, 25.0) < plane(15.0, 25.0) - 3.9


def test_weight_and_drape():
    sc = {"regions": [{"name": "t", "ramp": 2.0, "poly": [[-40, -60], [40, -60], [40, 60], [-40, 60]]}]}
    w = TO.weight(np.array([[0, 0], [39.5, 0], [41, 0], [-37, 10]]), sc)
    assert w[0] == 1.0 and 0 < w[1] < 1 and w[2] == 0.0 and w[3] == 1.0
    hf = grid(plane)
    T = {"heightfield": {"x0": X0, "y0": Y0, "dx": DX, "nx": NX, "ny": NY}}
    xs = np.arange(-10.0, 11.0)
    inside = {"n": len(xs) + 2, "turn": "in", "center": [[-10.0, -11.0, 5.0]] * 3 + [[x, -11.0, 5.0] for x in xs[1:]],
              "left": [[-10.0, -8.0, 5.0]] * 3 + [[x, -8.0, 5.0] for x in xs[1:]],
              "right": [[-10.0, -14.0, 5.0]] * 3 + [[x, -14.0, 5.0] for x in xs[1:]],
              "profile_z": [[5.0] * 7] * (len(xs) + 2), "gap_left": [0.0] * (len(xs) + 2), "gap_right": [0.0] * (len(xs) + 2)}
    outside = {"n": 2, "turn": "out", "center": [[100.0, -11.0, 5.0], [101.0, -11.0, 5.0]], "left": [[100.0, -8.0, 5.0], [101.0, -8.0, 5.0]],
               "right": [[100.0, -14.0, 5.0], [101.0, -14.0, 5.0]], "profile_z": [[5.0] * 7] * 2, "gap_left": [0.0] * 2, "gap_right": [0.0] * 2}
    SC = {"paved_zones": {"fractions": FR, "parts": [inside, outside]}}
    TO.drape_parts(SC, T, hf, sc, log=lambda *a: None)
    a = SC["paved_zones"]["parts"][0]
    assert a["n"] == len(xs) and len(a["profile_z"]) == len(xs)            # the two zero-length stations are gone
    assert abs(a["profile_z"][10][0] - plane(0.0, -8.0)) < 1e-3 and abs(a["center"][10][2] - plane(0.0, -11.0)) < 1e-3
    assert SC["paved_zones"]["parts"][1]["profile_z"][0] == [5.0] * 7     # outside the region: as built
