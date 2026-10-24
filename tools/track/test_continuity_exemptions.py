"""Sonoma round 14B part 1b: declared junction corners (gate.continuity_exemptions), the foot-of-normal owner readings, the
declared steps in his red and the refine layer's sub-ranges."""
import numpy as np

import edge_gate as EG
import edges_spline as ES


def _track(left_fn, n=200):
    s = np.arange(n, dtype=float)
    C = np.c_[s, np.zeros(n)]
    L = np.c_[s, left_fn(s)]
    R = np.c_[s, -5.0 * np.ones(n)]
    return dict(n=n, center=C.tolist(), left=L.tolist(), right=R.tolist())


def test_no_exemptions_is_inert():
    T = _track(lambda s: 5.0 + 0 * s)
    assert EG.exemptions({}, np.array(T['center'])) == []
    assert EG.exempt_stations({}, 'left', T['n'], np.array(T['center'])) == set()
    assert EG.continuity_exemption_report(T, {}) == []


def test_exemption_resolved_from_world_points_and_shapes():
    # a 1 m jog over one station interval at s 100: declared as a step it is exempt (smooth either side)
    T = _track(lambda s: np.where(s < 100.5, 5.0, 6.0))
    g = dict(continuity_exemptions=[dict(side='left', kind='step', enu=[(96.0, 5.0), (105.0, 6.0)], reason='t')])
    (e,) = EG.exemptions(g, np.array(T['center']))
    assert (e['lo'], e['hi']) == (96, 105)
    (line, ok), = EG.continuity_exemption_report(T, g)
    assert ok and 'step' in line and 'exempt' in line
    # the same jog declared as a corner (straight or smooth) is NOT exempt: an exemption cannot hide a kink
    g2 = dict(continuity_exemptions=[dict(side='left', kind='corner', enu=[(96.0, 5.0), (105.0, 6.0)], reason='t')])
    (line2, ok2), = EG.continuity_exemption_report(T, g2)
    assert not ok2 and 'FAIL' in line2
    # world continuity leaves the declared stations out and still measures the rest
    # (the synthetic track is open: its largest third difference is at the wrap, which the exemption does not cover)
    T['left'] = T['left'][:]; Lw = np.array(T['left']); n = T['n']
    ex = EG.exempt_stations(g, 'left', n, np.array(T['center']), (2, 1))
    assert set(range(94, 107)) <= ex
    d3 = np.linalg.norm(np.roll(Lw, -2, 0) - 3 * np.roll(Lw, -1, 0) + 3 * Lw - np.roll(Lw, 1, 0), axis=1)
    inner = [k for k in range(5, n - 5) if k not in ex]
    assert max(d3[inner]) < 1e-9 and max(d3[k] for k in ex) > 0.5


def test_smooth_arc_passes_per_metre():
    # a gentle bulge (radius well over 6 m) declared as an arc: smooth per metre
    T = _track(lambda s: 5.0 + 2.0 * np.exp(-((s - 100) / 8.0) ** 2))
    g = dict(continuity_exemptions=[dict(side='left', kind='arc', enu=[(85.0, 5.0), (115.0, 5.0)], reason='t')])
    (line, ok), = EG.continuity_exemption_report(T, g)
    assert ok and 'smooth per metre' in line


def test_foot_projection_on_a_curve():
    # points 10 m outside a circle of radius 20: the foot station is exact, the nearest centre point is not
    n = 400; R = 20.0; th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    C = np.c_[R * np.cos(th), R * np.sin(th)]
    t = np.roll(C, -1, 0) - np.roll(C, 1, 0); t /= np.linalg.norm(t, axis=1, keepdims=True); NL = np.c_[-t[:, 1], t[:, 0]]
    phi = th[100] + 0.37 * (th[1] - th[0])
    P = np.array([[30.0 * np.cos(phi), 30.0 * np.sin(phi)]])
    s, lat = ES.foot_project(C, NL, P)
    assert abs(s[0] - 100.37) < 0.02 and abs(abs(lat[0]) - 10.0) < 0.01


def test_step_profile_absent_and_present():
    n = 120; C = np.c_[np.arange(n, dtype=float), np.zeros(n)]; NL = np.c_[np.zeros(n), np.ones(n)]
    pts = np.c_[np.arange(n, dtype=float), np.where(np.arange(n) < 60, 5.0, 4.0)]
    w = dict(side='left', lo=0, hi=n - 1, pts=pts, chains=None, kerb_inside=[], project='foot')
    assert ES.step_profile('left', [], [w], C, NL, n) is None
    J = ES.step_profile('left', [('left', 55, 65)], [w], C, NL, n)
    assert abs((J[60] - J[59]) - (-1.0)) < 0.05 and abs(J[5]) < 1e-9 and abs(J[115]) < 1e-9


def test_refine_subrange_penalty_only_inside():
    ES.REFINE[:] = [(0, 60, 2.0, 10.0, 'left', [(20, 40, 0.1)])]
    D = ES._fine_penalty()
    ES.REFINE[:] = [(0, 60, 2.0, 10.0)]
    D0 = ES._fine_penalty()
    ES.REFINE[:] = []
    rows = np.abs(D).sum(1) / np.abs(D0).sum(1)
    assert rows.min() < 0.2 and abs(rows[0] - 1.0) < 1e-6 and abs(rows[-1] - 1.0) < 1e-6
