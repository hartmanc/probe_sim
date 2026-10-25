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


def test_join_lane_outline_takes_the_lanes_edge_height(monkeypatch):
    z = dict(name="dp", side="left", s=(100, 120), outline=dict(centre_off=6.0, from_m=2.4, join_lane=dict(reach=4.0)),
             outer_latlon=mouth(), src="t")
    dp, = zones(monkeypatch, z)
    # a lane whose right edge runs along y 15 at 0.05 m (the zone's outer edge, y 16, lies 1 m inside it)
    xs = np.arange(90, 131, 1.0)
    lane = {"left": [[x, 23.0, 0.05] for x in xs], "right": [[x, 15.0, 0.05] for x in xs],
            "profile_z": [[0.05] * len(FR) for _ in xs]}
    before = np.array(dp["profile_z"], float)
    BS.join_lane_outline([lane], [dp], FR)
    after = np.array(dp["profile_z"], float)
    x = np.array(dp["center"], float)[:, 0]; mid = (x > 101) & (x < 119)
    assert np.allclose(after[mid, 0], 0.05, atol=1e-3)               # the outer edge at the lane's height
    assert np.allclose(after[mid, -1], before[mid, -1], atol=1e-6)   # 8.6 m from the outer edge: unchanged (reach 4 m)
    assert np.allclose(np.array(dp["left"], float)[mid, 2], 0.05, atol=1e-3)


def test_join_lane_outline_needs_the_lane(monkeypatch):
    z = dict(name="dp", side="left", s=(100, 120), outline=dict(centre_off=6.0, from_m=2.4, join_lane=dict(reach=4.0)),
             outer_latlon=mouth(), src="t")
    dp, = zones(monkeypatch, z)
    far = {"left": [[0, 90.0, 0.0], [1, 90.0, 0.0]], "right": [[0, 80.0, 0.0], [1, 80.0, 0.0]], "profile_z": [[0.0] * 7, [0.0] * 7]}
    with pytest.raises(SystemExit):
        BS.join_lane_outline([far], [dp], FR)
