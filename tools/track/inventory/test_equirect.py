"""equirect.py on a synthetic equirectangular frame whose pixels encode their own longitude / latitude."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import equirect as E  # noqa: E402

W, H = 1440, 720


def synthetic():
    """float frame: channel 0 = longitude (deg, -180..180), channel 1 = latitude (deg, 90..-90) at pixel centres."""
    lon = (np.arange(W) + 0.5) / W * 360 - 180
    lat = 90 - (np.arange(H) + 0.5) / H * 180
    LON, LAT = np.meshgrid(lon, lat)
    return np.stack([LON, LAT, np.zeros_like(LON)], axis=-1).astype(np.float64)


def test_view_centre_looks_where_asked():
    eq = synthetic()
    for yaw, pitch in ((0, 0), (90, 0), (-90, 10), (45, -20), (170, 5)):
        v = E.view(eq, yaw, pitch, 90, 201, 101)
        c = v[50, 100]
        assert abs(c[0] - yaw) < 0.3 and abs(c[1] - pitch) < 0.3, (yaw, pitch, c)


def test_horizontal_fov_and_orientation():
    eq = synthetic()
    v = E.view(eq, 0, 0, 90, 401, 201)
    # the left and right borders are +-45 deg of longitude; right is +, top is up
    assert abs(v[100, 0, 0] + 45) < 0.5 and abs(v[100, -1, 0] - 45) < 0.5
    assert v[0, 200, 1] > 0 > v[-1, 200, 1]


def test_wraparound_behind_has_no_seam():
    # a field continuous across the +-180 deg seam (cos and sin of longitude) stays continuous in a view straight back
    eq = synthetic()
    lon = np.radians(eq[..., 0])
    f = np.stack([np.cos(lon), np.sin(lon), np.zeros_like(lon)], axis=-1)
    v = E.view(f, 180, 0, 60, 301, 101)
    step = np.abs(np.diff(v[50, :, :2], axis=0)).max()
    assert step < 0.01
    assert abs(v[50, 150, 0] + 1) < 1e-3           # straight back: cos(lon) = -1


def test_uint8_round_trip_and_straight_lines():
    # a vertical line of the world (one longitude) stays a vertical line in any level view
    eq = np.zeros((H, W, 3), np.uint8)
    col = int(W * (30 + 180) / 360)
    eq[:, col - 1:col + 2] = 255
    v = E.view(eq, 30, 0, 90, 301, 301)
    xs = [np.argmax(v[r, :, 0]) for r in range(20, 281, 20)]
    assert max(xs) - min(xs) <= 1
    assert v.dtype == np.uint8
