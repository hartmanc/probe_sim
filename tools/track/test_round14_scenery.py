"""Buttonwillow round 14 builder keys: runoff_zones[].outline (build_scenery.paved_zones make_outline_part: a zone whose
outline is a measured line, the owner's fish mouths on the front straight) and runoff_zones[].outline.join_lane
(build_scenery.join_lane_outline: a deep mouth part's profile takes the pit lane's edge height)."""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_scenery as BS  # noqa: E402

FR = [-1.0, -0.6, -0.3, 0.0, 0.3, 0.6, 1.0]


class FakeTrack:
    """A straight track along +x, station i at x = i * sp, half-width 5 m each side, edge height 0.10 m, ground 0.20 m."""
    n, sp, box = 400, 1.0, None

    def __init__(self):
        self.C = np.c_[np.arange(self.n) * self.sp, np.zeros(self.n), np.zeros(self.n)]
        self.T = np.tile([1.0, 0.0], (self.n, 1)); self.N = np.tile([0.0, 1.0], (self.n, 1))
        self.L = np.c_[self.C[:, 0], np.full(self.n, 5.0), np.full(self.n, 0.10)]
        self.R = np.c_[self.C[:, 0], np.full(self.n, -5.0), np.full(self.n, 0.10)]
        self.t = {"corners": [], "profile": {"fractions": FR}}

    def project(self, P):
        P = np.atleast_2d(np.asarray(P, float))[:, :2]
        i = np.clip(np.round(P[:, 0] / self.sp).astype(int), 0, self.n - 1)
        return i, P[:, 1], np.abs(P[:, 1]) - 5.0

    def hw(self, st, side):
        return np.full(len(np.atleast_1d(st)), 5.0)

    def ground(self, x, y):
        return np.full(len(np.atleast_1d(x)), 0.20)


class FakeOSM:
    def select(self, f, box=None):
        return []


def ll(pts):
    out = []
    for x, y in pts:
        lon, lat = BS.bl.lonlat(float(x), float(y))
        out.append((float(lat), float(lon)))
    return out


def mouth(x0=100.0, x1=120.0, top=11.0, flare=2.0):
    """a fish mouth on the left: from the edge (y 5) at x0 - flare up to y 7 at x0, up to the top, across, down"""
    return ll([(x0 - flare, 5.0), (x0, 7.0), (x0, 5.0 + top), (x1, 5.0 + top), (x1, 7.0), (x1 + flare, 5.0)])


def zones(monkeypatch, *zs):
    monkeypatch.setattr(BS, "SC_CFG", {"runoff_zones": list(zs)})
    monkeypatch.setattr(BS, "PAVED_RUNOFF", [])
    return BS.paved_zones(FakeTrack(), FakeOSM())["parts"]


def test_outline_part_follows_the_outline_with_a_constant_centre(monkeypatch):
    p, = zones(monkeypatch, dict(name="m", side="left", s=(95, 125), surface="apron", outline=dict(centre_off=0.5),
                                 outer_latlon=mouth(), src="test"))
    C, L, R = (np.array(p[k], float) for k in ("center", "left", "right"))
    assert np.allclose(C[:, 1], 5.5, atol=0.02)                      # the centre never swings with the width
    assert np.allclose(R[:, 1], 5.0, atol=0.02)                      # the inner edge on the course edge
    x = C[:, 0]
    mid = (x > 100.5) & (x < 119.5)
    assert np.allclose(L[mid, 1], 16.0, atol=0.05)                   # the outer edge on his line across the top
    fl = (x > 98.2) & (x < 99.8)                                     # the flare: 2 m deep over 2 m
    assert np.allclose(L[fl, 1], 5.0 + (x[fl] - 98.0), atol=0.1)
    assert x.min() >= 98.0 and x.max() <= 122.0                      # stations past the outline are left out
    assert p["surface"] == "apron" and p["turn"] == "m"
    assert np.allclose(np.array(p["gap_right"]), 0.0)                # the inner side touches the track


def test_profile_fractions_sit_where_the_physics_puts_them(monkeypatch):
    p, = zones(monkeypatch, dict(name="m", side="left", s=(95, 125), outline=dict(centre_off=0.5), outer_latlon=mouth(), src="t"))
    cz = np.array(p["center"], float)[:, 2]; pz = np.array(p["profile_z"], float)
    assert np.allclose(cz, pz[:, 3])                                 # f = 0 is the part's own centre
    # the left edge (f -1, the outer side here) takes the heightfield 11 m out, the right edge (f +1) the track edge
    j = len(cz) // 2
    assert abs(pz[j, 0] - 0.20) < 0.01 and abs(pz[j, -1] - 0.10) < 0.01


def test_caps_and_from_m_shape_a_shallow_and_a_deep_part(monkeypatch):
    sh, dp = zones(monkeypatch,
                   dict(name="sh", side="left", s=(95, 125), outline=dict(centre_off=0.5, caps=[(3.0, 95, 125)]), outer_latlon=mouth(), src="t"),
                   dict(name="dp", side="left", s=(100, 120), outline=dict(centre_off=6.0, from_m=2.4), outer_latlon=mouth(), src="t"))
    Ls, Ld, Rd, Cd = (np.array(q, float) for q in (sh["left"], dp["left"], dp["right"], dp["center"]))
    assert Ls[:, 1].max() <= 8.0 + 0.02                               # capped 3 m beyond the edge
    assert np.allclose(Rd[:, 1], 7.4, atol=0.02) and np.allclose(Cd[:, 1], 11.0, atol=0.02)
    assert np.allclose(Ld[(Ld[:, 0] > 100.5) & (Ld[:, 0] < 119.5), 1], 16.0, atol=0.05)
    assert np.allclose(np.array(dp["gap_right"]), 2.4)


def test_outline_needs_from_m_inside_the_centre(monkeypatch):
    with pytest.raises(SystemExit):
        zones(monkeypatch, dict(name="m", side="left", s=(95, 125), outline=dict(centre_off=0.5, from_m=0.5), outer_latlon=mouth(), src="t"))


def test_a_zone_without_outline_is_built_as_before(monkeypatch):
    z = dict(name="old", side="left", s=(95, 125), outer_latlon=ll([(90, 12.0), (130, 12.0)]), src="t")
    p, = zones(monkeypatch, z)
    C, L = np.array(p["center"], float), np.array(p["left"], float)
    assert np.allclose(L[:, 1], 12.0, atol=0.05) and np.allclose(C[:, 1], 8.5, atol=0.05)   # the mid-line centre


def sloping_lane(y0=15.0, y1=23.0, x0=60, x1=160, z0=0.05, slope=0.02):
    """a straight lane along +x from y0 (right edge) to y1 (left edge), its surface rising `slope` per metre across
    (0.16 m over its 8 m) and along x by 0.001 per metre"""
    xs = np.arange(x0, x1 + 1, 1.0)
    z = lambda x, y: z0 + slope * (y - y0) + 0.001 * (x - x0)   # noqa: E731
    fr = np.array(FR)
    lane = {"n": len(xs), "center": [[x, (y0 + y1) / 2, z(x, (y0 + y1) / 2)] for x in xs],
            "left": [[x, y1, z(x, y1)] for x in xs], "right": [[x, y0, z(x, y0)] for x in xs],
            "profile_z": [[z(x, (y0 + y1) / 2 - f * (y1 - y0) / 2) for f in fr] for x in xs]}
    return lane, z


def test_lane_surface_z_reads_the_lane_as_the_physics_does():
    lane, z = sloping_lane()
    P = np.array([[100.3, 16.0], [120.7, 21.5], [100.0, 14.0], [100.0, 24.0]])
    zz, ins = BS.lane_surface_z([lane], P, FR)
    assert ins.tolist() == [True, True, False, False]
    assert abs(zz[0] - z(100.3, 16.0)) < 1e-6 and abs(zz[1] - z(120.7, 21.5)) < 1e-6


def test_join_lane_outline_meets_a_sloping_lane_with_no_step(monkeypatch):
    """planar + join: the part's height at the ownership boundary (the lane's right edge) is the lane's own there, within 5 mm,
    on a lane sloping 2 % across and 0.1 % along"""
    lane, z = sloping_lane()
    z = dict(name="dp", side="left", s=(100, 120), outline=dict(planar=True, centre_off=6.0, from_m=2.4, join_lane=dict(reach=1.0)),
             outer_latlon=mouth(top=10.15), src="t")
    dp, = zones(monkeypatch, z)
    BS.join_lane_outline([lane], [dp], FR, trk=FakeTrack())
    # sample both surfaces the physics' way along sections across the boundary (the lane's right edge, y 15)
    C, L, R = (np.array(dp[k], float)[:, :2] for k in ("center", "left", "right"))
    prof = np.array(dp["profile_z"], float); fr = np.array(FR)
    worst = 0.0
    for i in range(3, len(C) - 3):
        hl = np.hypot(*(L[i] - C[i])); y_in = 15.0 + 0.0   # the boundary on the lane's edge
        f = -(y_in - C[i][1]) / hl                      # left of the centre: f < 0
        z_part = np.interp(f, fr, prof[i])
        z_lane, _ = BS.lane_surface_z([lane], np.array([[C[i][0], y_in + 1e-6]]), FR)
        worst = max(worst, abs(z_part - z_lane[0]))
    assert worst < 0.005, worst


def test_join_lane_outline_fails_when_few_sections_reach_the_lane(monkeypatch):
    z = dict(name="dp", side="left", s=(100, 120), outline=dict(centre_off=6.0, from_m=2.4, join_lane=dict(reach=1.0)),
             outer_latlon=mouth(), src="t")
    dp, = zones(monkeypatch, z)
    far, _ = sloping_lane(y0=80.0, y1=88.0)
    with pytest.raises(SystemExit):
        BS.join_lane_outline([far], [dp], FR)


def test_a_self_intersecting_outline_fails(monkeypatch):
    bad = ll([(98.0, 5.0), (100.0, 7.0), (100.0, 16.0), (120.0, 9.0), (110.0, 16.0), (120.0, 7.0), (122.0, 5.0)])
    with pytest.raises(SystemExit, match="crosses itself"):
        zones(monkeypatch, dict(name="m", side="left", s=(95, 125), outline=dict(centre_off=0.5), outer_latlon=bad, src="t"))


def test_a_reversed_outline_fails(monkeypatch):
    with pytest.raises(SystemExit, match="wrong way round"):
        zones(monkeypatch, dict(name="m", side="left", s=(95, 125), outline=dict(centre_off=0.5), outer_latlon=mouth()[::-1], src="t"))


def test_a_backtracking_outline_fails(monkeypatch):
    # the round-14 bug: a turn-down traversed from its foot up (south first), so the line goes back along the track
    back = ll([(98.0, 5.0), (100.0, 7.0), (100.0, 16.0), (112.0, 16.0), (112.0, 9.0), (109.0, 12.0), (115.0, 8.0), (120.0, 7.0), (122.0, 5.0)])
    with pytest.raises(SystemExit):
        zones(monkeypatch, dict(name="m", side="left", s=(95, 125), outline=dict(centre_off=0.5), outer_latlon=back, src="t"))


def test_an_outline_with_a_gap_fails(monkeypatch):
    # two mouths in one outline: the stations between them leave it, so one entry would make two runs
    two = ll([(98.0, 5.0), (100.0, 9.0), (104.0, 9.0), (104.0, 5.0), (114.0, 5.0), (114.0, 9.0), (118.0, 9.0), (120.0, 5.0)])
    with pytest.raises(SystemExit):
        zones(monkeypatch, dict(name="m", side="left", s=(95, 125), outline=dict(centre_off=0.5), outer_latlon=two, src="t"))


def test_check_strip_refuses_crossed_and_reversed_sections():
    C = np.c_[np.arange(10.0), np.zeros(10)]
    L = C + [0, 3.0]; R = C - [0, 2.0]
    BS.check_strip("ok", C, L, R)
    L2 = L.copy(); L2[5] = [3.5, 3.0]                    # the outer edge runs backwards between sections 4 .. 6
    with pytest.raises(SystemExit):
        BS.check_strip("rev", C, L2, R)
    R3 = R.copy(); R3[4], R3[5] = R[5].copy(), R[4].copy()   # two sections cross
    with pytest.raises(SystemExit):
        BS.check_strip("cross", C, L, R3)
    with pytest.raises(SystemExit):
        BS.check_strip("side", C, R, L)                  # edges on the wrong sides


def test_cap_knots_follow_a_line(monkeypatch):
    p, = zones(monkeypatch, dict(name="m", side="left", s=(95, 125), outline=dict(centre_off=0.5, cap_knots=[(100, 3.0), (120, 7.0)]),
                                 outer_latlon=mouth(), src="t"))
    L = np.array(p["left"], float); x = L[:, 0]; m = (x > 101) & (x < 119)
    assert np.allclose(L[m, 1], 5.0 + 3.0 + (x[m] - 100) * 0.2, atol=0.1)


def test_band_spans_the_lane_and_ends_on_its_own_points(monkeypatch):
    lane, _ = sloping_lane(y0=10.4, y1=26.0, x0=40, x1=180)
    monkeypatch.setattr(BS, "LANE_PARTS", [lane])
    z = dict(name="b", side="left", s=(80, 140), surface="asphalt", src="t",
             band=dict(core=(100, 120), centre=[(100, 11.0), (120, 11.0)], inner=[(100, 5.3), (120, 5.3)], taper=20.0, ends=3.0,
                       inner_lane=True, lane_surface=dict(reach=1.0)))
    b, = zones(monkeypatch, z)
    C, L, R = (np.array(b[k], float)[:, :2] for k in ("center", "left", "right"))
    assert b["lane_copy"][0] >= 3 and b["lane_copy"][1] >= 3
    lc = np.array(lane["center"], float)[:, :2]
    for P in (C[0], C[-1]):                                       # its end points ARE lane centre points
        assert np.min(np.hypot(*(lc - P).T)) < 1e-9
    core = (C[:, 0] > 101) & (C[:, 0] < 119)
    assert np.allclose(C[core, 1], 16.0, atol=0.05)               # 11 m beyond the edge (y 5)
    assert np.all(L[:, 1] <= 26.0 + 1e-6) and np.all(R[:, 1] >= 10.4 - 0.2)   # never below the lane's right edge (inner_lane)
    BS.check_strip("b", C, L, R)


