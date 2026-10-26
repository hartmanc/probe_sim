"""catalyst_speed.py's integration (Astra round-4 review of Mid-Ohio): a known-distance synthetic trace, a missing
sample, timestamp validation, and the saved N837 lap re-integrated from its own rows."""
import json
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import catalyst_speed as CS  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def test_known_distance_piecewise_linear_speed():
    # 20 m/s for 10 s, a linear ramp 20 -> 40 m/s over 10 s, 40 m/s for 10 s: 200 + 300 + 400 = 900 m
    t = np.arange(0.0, 30.0 + 1e-9, 1.0)
    v = np.interp(t, [0, 10, 20, 30], [20, 20, 40, 40])
    D, n = CS.integrate(t, v, 0.0, 30.0)
    assert abs(D - 900.0) < 1e-9 and n == 29
    # crossings between samples: the speed there is interpolated; 2.5 -> 27.5 s = 150 + 300 + 300 = 750 m
    D, _ = CS.integrate(t, v, 2.5, 27.5)
    assert abs(D - 750.0) < 1e-9


def test_missing_samples_are_bridged_by_their_neighbours():
    rows = [dict(t=float(k), reading=r) for k, r in enumerate([50, 50, None, 50, 50, 60, 70, None, 70])]
    t, v = CS.series(rows, 'mph')
    assert len(t) == 7 and 2.0 not in t and 7.0 not in t
    D, _ = CS.integrate(t, v, 0.0, 8.0)
    # constant 50 mph to 4 s, ramp 50 -> 70 mph over 4..6 s, 70 mph to 8 s; the gaps lie on linear stretches: exact
    exp = (4 * 50 + 2 * 60 + 2 * 70) * 0.44704
    assert abs(D - exp) < 1e-9
    # a missing sample on a kink is bridged linearly (the documented approximation): 4 s at a, not at the peak
    t2 = np.array([0.0, 1.0, 3.0, 4.0]); v2 = np.array([10.0, 10.0, 10.0, 10.0])
    assert abs(CS.integrate(t2, v2, 0.0, 4.0)[0] - 40.0) < 1e-12


def test_timestamps_validated():
    with pytest.raises(ValueError, match='strictly increasing'):
        CS.integrate([0.0, 1.0, 0.9, 2.0], [10, 10, 10, 10], 0.0, 2.0)
    with pytest.raises(ValueError, match='strictly increasing'):
        CS.integrate([0.0, 1.0, 1.0, 2.0], [10, 10, 10, 10], 0.0, 2.0)
    with pytest.raises(ValueError, match='non-finite'):
        CS.integrate([0.0, np.nan, 2.0], [10, 10, 10], 0.0, 2.0)
    with pytest.raises(ValueError, match='outside the samples'):
        CS.integrate([1.0, 2.0, 3.0], [10, 10, 10], 0.5, 3.0)
    with pytest.raises(ValueError, match='out of order'):
        CS.integrate([0.0, 1.0, 2.0], [10, 10, 10], 2.0, 1.0)
    with pytest.raises(ValueError, match='strictly increasing'):
        CS.series([dict(t=0.0, reading=50), dict(t=2.0, reading=50), dict(t=1.5, reading=50)])


def test_saved_n837_lap_reintegrates_to_its_recorded_distance():
    d = json.load(open(os.path.join(ROOT, 'tools/track/compare/mid_ohio/r4/speed_lap_n837.json')))
    t, v = CS.series(d['rows'], 'mph')
    D, n = CS.integrate(t, v, d['t0'], d['t1'])
    assert round(D, 1) == d['distance_m'] and n == d['samples']
    assert [round(CS.integrate(t[::2], v[::2], d['t0'], d['t1'])[0], 1),
            round(CS.integrate(t[1::2], v[1::2], d['t0'], d['t1'])[0], 1)] == d['distance_2step_m']
