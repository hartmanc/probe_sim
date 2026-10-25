"""Buttonwillow round 13 builder key: kerbs_declared[].extent (build_scenery.kerb_run), a run's start and end measured from
dense onboard frames in place of its block line's ends; only with kerb.flush_runs and an extent_src."""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import build_scenery as BS  # noqa: E402


class FakeTrack:
    """A straight track along +x, 1 station = sp m, half-width 5 m each side."""
    n, sp = 1000, 0.998128

    def project(self, P):
        P = np.asarray(P, float)
        return P[:, 0] / self.sp, P[:, 1], np.zeros(len(P))

    def hw(self, st, side):
        return np.full(len(np.atleast_1d(st)), 5.0)


def line(x0, x1, y=5.2):
    pts = []
    for x in np.arange(x0, x1 + 1e-9, 2.0):
        lon, lat = BS.bl.lonlat(float(x), y)
        pts.append((float(lat), float(lon)))
    return pts


@pytest.fixture
def flush(monkeypatch):
    monkeypatch.setattr(BS, "SC_CFG", {"kerb": {"flush_runs": True, "width": 0.9}})


def run(**kw):
    k = dict(side="left", line_latlon=line(100, 120), colors=["#c4463b", "#e2dfd6"], name="t", src="test")
    k.update(kw)
    return BS.kerb_run(FakeTrack(), k, {}, max_step=0.1)


def test_without_extent_the_block_line_sets_the_ends(flush):
    r = run()
    assert abs(r["s0"] * FakeTrack.sp - 100) <= 1.0 and abs(r["s1"] * FakeTrack.sp - 120) <= 1.0


def test_extent_sets_the_ends_and_keeps_the_flush_offset(flush):
    r = run(extent=(95.0, 131.0), extent_src="onboard frames")
    assert r["s0"] == round(95.0 / FakeTrack.sp) and r["s1"] == round(131.0 / FakeTrack.sp)
    assert len(r["offs"]) == r["s1"] - r["s0"] + 1
    assert all(abs(v + 0.45) < 1e-9 for v in r["offs"])


def test_extent_needs_its_evidence(flush):
    with pytest.raises(SystemExit):
        run(extent=(95.0, 131.0))


def test_extent_needs_flush_runs(monkeypatch):
    monkeypatch.setattr(BS, "SC_CFG", {"kerb": {"width": 0.9}})
    with pytest.raises(SystemExit):
        run(extent=(95.0, 131.0), extent_src="onboard frames")


def test_extent_must_be_a_run(flush):
    with pytest.raises(SystemExit):
        run(extent=(131.0, 95.0), extent_src="onboard frames")
