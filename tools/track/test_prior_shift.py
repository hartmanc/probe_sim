"""centre.prior_shift (geo.prior_shift): a measured sideways shift of the first centre over a stretch."""
import math
import numpy as np
import geo


def loop(R=200.0):
    t = np.linspace(0, 2 * np.pi, int(2 * np.pi * R), endpoint=False)
    return np.c_[R * np.cos(t), R * np.sin(t)]


enu = lambda la, lo: (lo, la)  # noqa: E731  (synthetic: lat/lon are y/x)


def test_no_entries_is_identity():
    C = loop()
    P, L = geo.prior_shift(C, [], enu)
    assert P is C and L is None


def test_shift_inside_zero_outside_start_kept():
    C = loop()
    n = len(C)
    nl = geo.left_normals(C)
    a, b = 300, 400
    knots = [(C[a][1], C[a][0], 3.0), (C[b][1], C[b][0], 3.0)]
    P, L = geo.prior_shift(C, [dict(knots=knots, blend=40, src='test')], enu)
    assert np.allclose(P[0], C[0], atol=1e-6)
    # the middle of the stretch moved ~3 m to the left (towards the circle's centre for a ccw loop)
    m = C[350] + 3.0 * nl[350]
    assert abs(geo.project(P, m[None])[1][0]) < 0.05
    # far from the stretch nothing moved
    far = C[(a + b) // 2 + n // 2]
    assert abs(geo.project(P, far[None])[1][0]) < 0.05


def test_knots_out_of_order_fail():
    C = loop()
    knots = [(C[400][1], C[400][0], 1.0), (C[300][1], C[300][0], 1.0)]
    try:
        geo.prior_shift(C, [dict(knots=knots, src='test')], enu)
    except SystemExit:
        return
    raise AssertionError('expected SystemExit')


def test_periodic_shift_joins_across_station_zero():
    # round 10: a whole-lap entry (periodic) interpolates round the loop, the last knot joined to the first
    C = loop()
    n = len(C)
    knots = [(C[k][1], C[k][0], 2.0 if k < n // 2 else 4.0) for k in range(10, n, 100)]
    P, L = geo.prior_shift(C, [dict(knots=knots, periodic=True, src='test')], enu)
    nl = geo.left_normals(C)
    # between the last knot and the first (across station 0) the shift lies between 4 and 2 m, no zero gap
    for k in (n - 5, 0, 5):
        lat = geo.project(P, (C[k] + 3.0 * nl[k])[None])[1][0]
        assert abs(lat) < 1.05
