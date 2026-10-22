"""Declared straights (straights.targets): the `once` and `width_shared` options (Buttonwillow round 8, ported to the
track-pipeline branch for Sonoma round 11, owner notes 64 / 69).

python3 -I -m pytest -q tools/track/test_straights.py   (needs numpy and pillow; skipped without them)
"""
import os
import sys

import pytest

np = pytest.importorskip('numpy')
pytest.importorskip('PIL')
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import straights  # noqa: E402


def _road(n=400, half_l=9.0, half_r=9.3):
    """A straight road along +x (station k at x = k), its left normal +y; noisy half-widths (the free fit's waves)."""
    C = np.c_[np.arange(n, dtype=float), np.zeros(n)]
    NL = np.tile([0.0, 1.0], (n, 1))
    k = np.arange(n)
    return C, NL, half_l + 0.2 * np.sin(k / 9.0), half_r + 0.3 * np.cos(k / 13.0)


def _reader(lines):
    """A stand-in for straights.paint_points: per side, painted-line points at y = lines[side] (+ a few outliers)."""
    def read(C, NL, hw, sg, ks, tiles, mpp):
        side = 'left' if sg > 0 else 'right'
        pts = [(C[k, 0], lines[side]) for k in ks]
        pts += [(C[k, 0], lines[side] + 2.0 * sg) for k in ks[::25]]   # a second band 2 m out (blocks, a lane line)
        return np.array(pts)
    return read


def test_width_shared_is_parallel_at_the_median_distance(monkeypatch):
    straights._ONCE.clear()
    C, NL, hl, hr = _road()
    monkeypatch.setattr(straights, 'paint_points', _reader({'left': 9.10, 'right': -9.25}))
    decl = [dict(side='left', fit='paint', lo=50, hi=300, join=(50, 55), end=300, tol=0.15, once=True, why='L'),
            dict(side='right', fit='paint', lo=50, hi=250, join=(50, 55), end=250, tol=0.15, once=True, width_shared=True, why='R')]
    out, rep = straights.targets(C, NL, hl, hr, decl, [], 0.117, log=lambda *a: None)
    ksl, vl = out['left']; ksr, vr = out['right']
    assert np.allclose(vl, 9.10, atol=1e-6)            # the left line, RANSAC on the readings (outliers rejected)
    assert np.allclose(vr, 9.25, atol=1e-6)            # the right: parallel, at the readings' median distance: one width
    assert np.ptp(np.array(vl)[: len(vr)] + np.array(vr)) < 1e-6


def test_width_shared_needs_the_other_side_first(monkeypatch):
    straights._ONCE.clear()
    C, NL, hl, hr = _road()
    monkeypatch.setattr(straights, 'paint_points', _reader({'left': 9.1, 'right': -9.2}))
    decl = [dict(side='right', fit='paint', lo=50, hi=250, join=(50, 55), end=250, width_shared=True, why='R')]
    with pytest.raises(SystemExit):
        straights.targets(C, NL, hl, hr, decl, [], 0.117, log=lambda *a: None)


def test_once_reuses_the_first_reading(monkeypatch):
    straights._ONCE.clear()
    C, NL, hl, hr = _road()
    decl = [dict(side='left', fit='paint', lo=50, hi=300, join=(50, 55), end=300, tol=0.15, once=True, why='L'),
            dict(side='right', fit='paint', lo=50, hi=300, join=(50, 55), end=300, tol=0.15, once=True, width_shared=True, why='R')]
    monkeypatch.setattr(straights, 'paint_points', _reader({'left': 9.10, 'right': -9.25}))
    first, _ = straights.targets(C, NL, hl, hr, decl, [], 0.117, log=lambda *a: None)
    # a refit around a moved edge would read the line elsewhere; `once` keeps the first line
    monkeypatch.setattr(straights, 'paint_points', _reader({'left': 9.60, 'right': -9.90}))
    again, _ = straights.targets(C, NL, hl + 0.5, hr + 0.6, decl, [], 0.117, log=lambda *a: None)
    assert np.allclose(first['left'][1], again['left'][1]) and np.allclose(first['right'][1], again['right'][1])
    # without `once` the line follows the new reading
    straights._ONCE.clear()
    plain = [dict(d, once=False) for d in decl]
    moved, _ = straights.targets(C, NL, hl, hr, plain, [], 0.117, log=lambda *a: None)
    assert np.allclose(moved['left'][1], 9.60, atol=1e-6)
