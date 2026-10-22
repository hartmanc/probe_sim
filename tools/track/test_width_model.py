"""The width gates (edge_gate.width_gates) and the width model's bias / width estimate (width_model.estimate), on
synthetic loops (Buttonwillow round 9, 22 Oct 2026)."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edge_gate  # noqa: E402
import width_model as WM  # noqa: E402

N = 1200   # a 1200 m circle, 1 m stations


def loop(hl, hr):
    a = np.arange(N) / N * 2 * np.pi; R = N / (2 * np.pi)
    C = np.c_[R * np.cos(a), R * np.sin(a)]
    NL = -np.c_[np.cos(a), np.sin(a)]          # counter-clockwise: left is inward
    return dict(n=N, spacing_m=float(np.linalg.norm(C[1] - C[0])), center=[[x, y, 0.0] for x, y in C],
                left=(C + hl[:, None] * NL).tolist(), right=(C - hr[:, None] * NL).tolist())


J = [('right', 300, 360, 'mouth', 'test')]


def test_constant_width_passes():
    met, fails = edge_gate.width_gates(loop(np.full(N, 6.0), np.full(N, 5.5)), J, log=lambda *_: None)
    assert fails == [] and met['width']['max_dev'] < 0.01


def test_width_step_fails_outside_junction_only():
    hr = np.full(N, 5.5); hr[320:340] += 2.0           # a mouth bulge inside the junction range: allowed
    assert edge_gate.width_gates(loop(np.full(N, 6.0), hr), J, log=lambda *_: None)[1] == []
    hr[700:760] += 0.5                                 # a 0.5 m widening in a section: fails
    assert 'width consistency' in edge_gate.width_gates(loop(np.full(N, 6.0), hr), J, log=lambda *_: None)[1]


def test_wave_fails():
    s = np.arange(N); hl = 6.0 + 0.6 * np.sin(2 * np.pi * s / 40.0) * ((s > 500) & (s < 700))
    f = edge_gate.width_gates(loop(hl, 11.5 - hl), J, log=lambda *_: None)[1]
    assert 'edge waviness left' in f and 'width consistency' not in f


def test_estimate_recovers_bias_and_width():
    rng = np.random.default_rng(1)
    E = {sd: dict(med=np.full(N, np.nan), conf=np.ones(N), kerb=np.full(N, np.nan), owner=np.full(N, np.nan)) for sd in ('left', 'right')}
    Wtrue = np.where(np.arange(N) < 600, 11.0, 12.5)
    for k in range(N):
        mid = 0.3 * np.sin(k / 50)
        L, R = Wtrue[k] / 2 + mid, Wtrue[k] / 2 - mid
        if k % 5 == 0: E['left']['kerb'][k] = L
        elif k % 5 == 1: E['right']['kerb'][k] = R
        E['left']['med'][k] = L + 1.0 + rng.normal(0, 0.1)      # the detector reads 1.0 m outward on the left
        E['right']['med'][k] = R + 0.6 + rng.normal(0, 0.1)     # and 0.6 m on the right
    for sd in ('left', 'right'):
        E[sd]['med'][~np.isnan(E[sd]['kerb'])] = np.nan
    jm, secs = WM.sections(N, [('both', 590, 610, 'mouth', 't'), ('both', 1190, 10, 'mouth', 't')])
    est = WM.estimate(E, N, secs, jm, log=lambda *_: None)
    assert abs(est['bias']['left'] - 1.0) < 0.05 and abs(est['bias']['right'] - 0.6) < 0.05
    assert sorted(round(float(w), 1) for w in est['W']) == [11.0, 12.5]
