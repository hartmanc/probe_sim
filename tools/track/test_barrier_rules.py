"""Tests of barrier_rules.py (round 12, Sonoma judge r11 N65 / N67)."""
import numpy as np

import barrier_rules as BR


def _run(z, step=2.0):
    return [[i * step, 0.0, float(v)] for i, v in enumerate(z)]


def test_ditch_under_a_wall_is_bridged_level():
    # the T10-T11 boarded wall's ground at s 3189-3222 (scenery.json r11, 2 m points): a 3 m deep ditch between lips
    z = [-0.49, -0.51, -0.54, -0.60, -1.15, -3.07, -3.44, -3.44, -2.40, -2.04, -1.51, -1.70, -2.03, -2.76, -3.51, -3.40,
         -2.46, -1.00, -0.70, -0.84, -0.86]
    lift = BR.run_lift(_run(z))
    top = np.array(z) + lift
    assert lift.max() > 2.8                                   # the ditch bottom lifted by its depth
    assert np.abs(np.diff(top)).max() / 2.0 < 0.1             # the top line has no step (was 1.92 m in 2 m)
    assert lift[0] == 0 and lift[-1] == 0                     # the lips stay on the ground
    assert np.all(lift >= 0)


def test_gentle_sag_is_followed():
    # a 1 m sag over 30 m (slope at most ~0.13): ground the wall follows, no lift (Laguna's sags: slopes 0.03-0.33)
    s = np.arange(0, 32, 2.0)
    z = -1.0 * np.sin(np.pi * s / 30.0)
    assert BR.hollow_lift(s, z).max() == 0


def test_a_one_sided_drop_is_not_bridged():
    # an embankment: 0 m then 2 m lower for good; no lip on the far side, no lift (the gate shows the step instead)
    assert BR.run_lift(_run([0.0, 0.0, 0.0, -2.0, -2.0, -2.0, -2.0, -2.0])).max() == 0


def test_a_hollow_wider_than_the_span_is_not_bridged():
    # a steep-sided hollow 40 m wide: no chord of 30 m spans it; the wall goes down (the wall-tops gate fails on it)
    z = [0.0, 0.0, -2.0] + [-2.0] * 18 + [0.0, 0.0]
    assert BR.run_lift(_run(z)).max() == 0


def test_barrier_tops_writes_top_z_only_where_lifted():
    SC = {"barriers": [
        {"kind": "concrete", "h": 1.2, "fence": 0, "pts": _run([0.0, 0.0, -2.0, -2.0, 0.0, 0.0])},
        {"kind": "concrete", "h": 1.0, "fence": 0, "pts": _run([0.0, -0.1, -0.2, -0.3])},
        {"kind": "tyres", "h": 1.0, "fence": 0, "pts": _run([0.0, 0.0, -2.0, 0.0, 0.0])},
    ]}
    rep = BR.barrier_tops(SC, None, log=lambda *a: None)
    assert [r[0] for r in rep] == [0]
    assert SC["barriers"][0]["top_z"] == [1.2] * 6            # level at lip height + h
    assert "top_z" not in SC["barriers"][1] and "top_z" not in SC["barriers"][2]
    assert BR.barrier_tops(SC, False, log=lambda *a: None) == []


def test_tyre_face_out():
    # row 1 toward the track: the face is 0.91 m in front of the line; behind it: 0.31 m (the stack radius)
    f = BR.tyre_face_out(np.zeros((2, 2)), [True, False], [0.55, 0.55])
    assert np.allclose(f, [0.55 - 0.91, 0.55 - 0.31])
