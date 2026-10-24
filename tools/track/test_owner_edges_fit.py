"""The owner-traced edge in the fit (spline.owner_edges, edges_spline.owner_readings): his world points become one
half-width reading per station of the CURRENT centre; kerb_inside moves them outward by the kerb width; Laguna
declares none, so its fit path is unchanged (OWNER empty)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import edges_spline as ES  # noqa: E402
import trackcfg  # noqa: E402


def straight(n=200):
    C = np.c_[np.arange(n, dtype=float), np.zeros(n)]
    NL = np.c_[np.zeros(n), np.ones(n)]
    return C, NL


def test_readings_on_the_current_centre():
    C, NL = straight()
    pts = np.c_[np.arange(50, 80, 1.0) + 0.2, np.full(30, 5.0)]
    r = ES.owner_readings(C, NL, dict(side='left', pts=pts, kerb_inside=[], kerb_w=0.9), len(C))
    assert set(r) == set(range(50, 80)) and np.allclose(list(r.values()), 5.0)
    # the centre moved 1 m left: the same world points read 1 m less
    r2 = ES.owner_readings(C + np.array([0, 1.0]), NL, dict(side='left', pts=pts, kerb_inside=[], kerb_w=0.9), len(C))
    assert np.allclose(list(r2.values()), 4.0)


def test_right_side_sign_and_kerb_inside():
    C, NL = straight()
    pts = np.c_[np.arange(10, 40, 1.0), np.full(30, -4.0)]
    r = ES.owner_readings(C, NL, dict(side='right', pts=pts, kerb_inside=[(14, 34)], kerb_w=0.9), len(C))
    assert np.isclose(r[12], 4.0) and np.isclose(r[24], 4.9)
    # the shift ramps in over KERB_RAMP stations at each end of the kerb run: no step in the readings
    assert np.isclose(r[14], 4.0 + 0.9 / ES.KERB_RAMP) and np.isclose(r[34], 4.0 + 0.9 / ES.KERB_RAMP)
    assert max(abs(r[k + 1] - r[k]) for k in range(10, 39)) <= 0.9 / ES.KERB_RAMP + 1e-9


def test_measured_kerb_shift_ramps_outside_the_zone():
    # round 10: (lo, hi, shift) puts the full measured shift over the whole zone and ramps it outside, <= KERB_STEP / station
    C, NL = straight()
    pts = np.c_[np.arange(0, 60, 1.0), np.full(60, 4.0)]
    r = ES.owner_readings(C, NL, dict(side='left', pts=pts, kerb_inside=[(25, 35, 0.8)], kerb_w=0.9), len(C))
    assert all(np.isclose(r[k], 4.8) for k in range(25, 36))
    assert np.isclose(r[10], 4.0) and np.isclose(r[50], 4.0)
    assert max(abs(r[k + 1] - r[k]) for k in range(0, 59)) <= ES.KERB_STEP + 1e-9
    # two zones close together: their ramps meet at the larger shift, never the sum
    r2 = ES.owner_readings(C, NL, dict(side='left', pts=pts, kerb_inside=[(10, 20, 0.8), (24, 34, 0.8)], kerb_w=0.9), len(C))
    assert max(r2.values()) <= 4.8 + 1e-9


def test_owner_chains_split_the_lines_and_drop_lone_points():
    a = np.c_[np.arange(0, 30, 1.0), np.zeros(30)]; b = np.c_[np.arange(0, 30, 1.0), np.full(30, 9.0)]
    ch = ES.owner_chains(np.r_[a, b, [[50.0, 50.0]]])
    assert sorted(len(c) for c in ch) == [30, 30]


def test_laguna_declares_no_owner_edges():
    # Sonoma's (round 14B) are local to its T1-T2 window: test_owner_reference.test_sonoma_owner_edges_are_local
    assert not (trackcfg.load('laguna_seca')['spline'].get('owner_edges'))
    assert ES.OWNER == []


def test_local_refinement_follows_a_tight_turn_and_is_inert_when_absent():
    # round 14B part 1b (spline.refine): a 2 m step over 6 stations in the anchors; the 6-station periodic spline lags it,
    # the refined layer (2-station knots inside the zone) follows; with REFINE empty the fit is the periodic one exactly
    n = 300; K = n // 6; xs = np.arange(n, dtype=float)
    y = np.where(xs < 150, 5.0, 7.0); y[147:153] = np.linspace(5.0, 7.0, 6)
    args = (xs, y, K, n, 30.0, 0.25, xs, np.full(n, 6.0), np.full(n, 0.03), xs, y, np.full(n, 40.0))
    ES.REFINE[:] = []
    c0 = ES.periodic_fit(*args)
    base = ES.periodic_basis(xs, K, n) @ c0
    assert np.allclose(ES.basis(xs, K, n), ES.periodic_basis(xs, K, n))
    ES.REFINE[:] = [(120, 180, 2)]
    c1 = ES.periodic_fit(*args)
    fine = ES.basis(xs, K, n) @ c1
    ES.REFINE[:] = []
    e0 = np.abs(base - y)[140:160].max(); e1 = np.abs(fine - y)[140:160].max()
    assert e1 < 0.5 * e0
    # the coarse coefficients near the zone adjust a little in the joint fit; away from it the curve is the same
    assert np.abs(fine - base)[:90].max() < 2e-3 and np.abs(fine - base)[210:].max() < 2e-3
