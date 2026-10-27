"""The opt-in bank-scaling rule (profile_bank.py, Mid-Ohio T4 round 4): the inside edge held, the chord bank toward the
inside scaled over the declared interval, the crown kept, nothing changed outside the interval (profile and
heightfield), a step at the interval's end refused."""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import profile_bank as PB  # noqa: E402

FR = [-1, -0.6667, -0.3333, 0, 0.3333, 0.6667, 1]
N = 600


def fixture(adverse_end=False):
    C = np.c_[np.arange(N, dtype=float), np.zeros(N)]            # along +x; left normal is +y
    hl = np.full(N, 6.0); hr = np.full(N, 6.0)
    lat = PB.lateral(hl, hr, FR)                                  # + left
    s = np.arange(N, dtype=float)
    bank = np.radians(4.4) * np.exp(-((s - 300) / 40) ** 2)       # banked toward the right (inside): left higher
    if adverse_end:
        x = np.clip((s - 330) / 30, 0, 1)
        bank = bank - np.radians(1.5) * x * x * (3 - 2 * x)          # an adverse slope from s ~345 on, through the core's end
    g = np.tan(bank)
    crown = -0.0004 * lat ** 2
    prof = 0.01 * s[:, None] + g[:, None] * (lat + 6.0) + crown   # right edge (lat -6) is the inside reference
    return C, hl, hr, prof


def rule(**k):
    r = dict(name='T4 test', anchor_latlon=(290.0, 0.0), search_m=40, inside='right', length_m=158.5,
             approach_m=121.9, factor=0.5, src='synthetic', why='test')
    r.update(k)
    return r


def test_inside_edge_held_bank_halved_crown_kept_outside_unchanged():
    C, hl, hr, prof = fixture()
    q = PB.rules(C, prof, hl, hr, [rule()], lambda a, b: (a, b), FR)
    assert q[0]['peak'] == 300
    new, delta, rep = PB.apply_profile(prof, hl, hr, q, FR, log=lambda *a: None)
    assert np.allclose(new[:, 6], prof[:, 6])                     # inside (right) edge held exactly
    g0 = (prof[300, 0] - prof[300, 6]) / 12; g1 = (new[300, 0] - new[300, 6]) / 12
    assert abs(g1 - 0.5 * g0) < 1e-12                             # chord bank halved at the peak
    # crown about the chord kept: the section's quadratic term unchanged
    lat = PB.lateral(hl, hr, FR)[300]
    assert abs(np.polyfit(lat, new[300], 2)[0] - np.polyfit(lat, prof[300], 2)[0]) < 1e-12
    lo, hi = 300 - 79.25 - 121.9, 300 + 79.25
    s = np.arange(N)
    out = (s < lo - 1) | (s > hi + 1)
    assert np.array_equal(new[out], prof[out])                    # outside the interval: byte-identical rows
    assert rep[0]['max_station_step_m'] <= PB.STEP_MAX


def test_factor_one_and_absent_are_no_ops():
    C, hl, hr, prof = fixture()
    q = PB.rules(C, prof, hl, hr, [rule(factor=1.0)], lambda a, b: (a, b), FR)
    new, delta, _ = PB.apply_profile(prof, hl, hr, q, FR, log=lambda *a: None)
    assert np.array_equal(new, prof)
    assert PB.rules(C, prof, hl, hr, [], lambda a, b: (a, b), FR) == []


def test_step_at_the_interval_end_is_refused_unless_an_exit_blend_is_declared():
    C, hl, hr, prof = fixture(adverse_end=True)
    # an adverse slope is left as measured, so the positive-part rule stays continuous there
    q = PB.rules(C, prof, hl, hr, [rule()], lambda a, b: (a, b), FR)
    PB.apply_profile(prof, hl, hr, q, FR, log=lambda *a: None)
    # a bank toward the inside at the end of the core: a step, refused
    C2, hl2, hr2, prof2 = fixture()
    prof2 = prof2 + np.tan(np.radians(2.0)) * (PB.lateral(hl2, hr2, FR) + 6.0)
    q2 = PB.rules(C2, prof2, hl2, hr2, [rule()], lambda a, b: (a, b), FR)
    with pytest.raises(ValueError):
        PB.apply_profile(prof2, hl2, hr2, q2, FR, log=lambda *a: None)
    q3 = PB.rules(C2, prof2, hl2, hr2, [rule(exit_m=60.0, approach_m=200.0)], lambda a, b: (a, b), FR)
    PB.apply_profile(prof2, hl2, hr2, q3, FR, log=lambda *a: None)


def test_heightfield_changes_only_inside_the_interval_and_fades_beyond_the_outside_edge():
    C, hl, hr, prof = fixture()
    q = PB.rules(C, prof, hl, hr, [rule()], lambda a, b: (a, b), FR)
    new, delta, _ = PB.apply_profile(prof, hl, hr, q, FR, log=lambda *a: None)
    dx = 1.0
    box = (0.0, -30.0, N - 1.0, 30.0)
    x, y = np.meshgrid(np.arange(N, dtype=float), np.arange(-30.0, 31.0))
    hf = (0.01 * x).astype('<f4')
    out, rep = PB.heightfield(hf, box, dx, C, hl, hr, delta, q, FR)
    d = out.astype(float) - hf.astype(float)
    ch = np.abs(d) > 0
    xs = x[ch]
    assert xs.min() >= q[0]['first'] - 1 and xs.max() <= q[0]['last'] + 1
    assert rep['total_cells'] == int(ch.sum())
    row = lambda yy: int(round(yy + 30))
    assert np.all(d[row(-8), :] == 0)                              # beyond the inside (right) edge: unchanged
    assert abs(d[row(6), 300] - delta[300, 0]) < 1e-5              # outside (left) edge: the profile's change
    assert abs(d[row(7.5), 300] - delta[300, 0]) < 1e-5            # held over the 2 m shoulder
    assert np.all(d[row(15), :] == 0)                              # faded out by 2 + 6 m beyond
    assert abs(d[row(0), 300] - delta[300, 3]) < 1e-5              # the centre: the profile's change


def _two_bank_fixture():
    """Two separate inside-banked corners (s 300 and s 1200) on one straight centre."""
    n = 1500
    C = np.c_[np.arange(n, dtype=float), np.zeros(n)]
    hl = np.full(n, 6.0); hr = np.full(n, 6.0)
    lat = PB.lateral(hl, hr, FR)
    s = np.arange(n, dtype=float)
    bank = np.radians(4.4) * (np.exp(-((s - 300) / 40) ** 2) + np.exp(-((s - 1200) / 40) ** 2))
    prof = 0.01 * s[:, None] + np.tan(bank)[:, None] * (lat + 6.0) - 0.0004 * lat ** 2
    return C, hl, hr, prof


def test_overlapping_rules_are_refused():
    C, hl, hr, prof = _two_bank_fixture()
    with pytest.raises(ValueError, match='overlap'):
        PB.rules(C, prof, hl, hr, [rule(name='a'), rule(name='b', anchor_latlon=(330.0, 0.0))],
                 lambda a, b: (a, b), FR)


def test_two_separate_rules_each_apply_once_in_profile_and_heightfield():
    C, hl, hr, prof = _two_bank_fixture()
    enu = lambda a, b: (a, b)
    ra, rb = rule(name='a'), rule(name='b', anchor_latlon=(1190.0, 0.0))
    both = PB.rules(C, prof, hl, hr, [ra, rb], enu, FR)
    new, delta, rep = PB.apply_profile(prof, hl, hr, both, FR, log=lambda *a: None)
    qa = PB.rules(C, prof, hl, hr, [ra], enu, FR); _, da, _ = PB.apply_profile(prof, hl, hr, qa, FR, log=lambda *a: None)
    qb = PB.rules(C, prof, hl, hr, [rb], enu, FR); _, db, _ = PB.apply_profile(prof, hl, hr, qb, FR, log=lambda *a: None)
    assert np.array_equal(delta, da + db)                          # each rule once, nothing stacked
    for pk in (300, 1200):                                         # each peak's chord bank halved, not quartered
        g0 = (prof[pk, 0] - prof[pk, 6]) / 12; g1 = (new[pk, 0] - new[pk, 6]) / 12
        assert abs(g1 - 0.5 * g0) < 1e-12
    dx = 1.0
    n = len(C)
    box = (0.0, -30.0, n - 1.0, 30.0)
    x, _ = np.meshgrid(np.arange(n, dtype=float), np.arange(-30.0, 31.0))
    hf = (0.01 * x).astype('<f4')
    out2, _ = PB.heightfield(hf, box, dx, C, hl, hr, delta, both, FR)
    outa, _ = PB.heightfield(hf, box, dx, C, hl, hr, da, qa, FR)
    outb, _ = PB.heightfield(hf, box, dx, C, hl, hr, db, qb, FR)
    d2 = out2.astype(float) - hf; dsum = (outa.astype(float) - hf) + (outb.astype(float) - hf)
    assert np.allclose(d2, dsum, atol=1e-5)                        # the heightfield carries each rule once
    assert abs(d2[36, 300] - delta[300, 0]) < 1e-5 and abs(d2[36, 1200] - delta[1200, 0]) < 1e-5
