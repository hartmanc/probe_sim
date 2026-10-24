"""The owner's reference in the width and waviness gates (edge_gate.OWNER_REF, owner_reference, owner_station_gate,
owner_waviness, width_gates(owner=...); Buttonwillow round 10, the owner's decision of 23 Oct 2026 point 3), on
synthetic loops. Where no owner edge exists the gates are the original ones (the detected-edge fixture below); Laguna
declares no owner edges or mouths, so its gates take the original path; Sonoma's (round 14B) are local to T1-T2."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import edge_gate  # noqa: E402
import edges_spline as ES  # noqa: E402
import trackcfg  # noqa: E402

N = 1200
Q = lambda *_: None  # noqa: E731


def loop(hl, hr):
    a = np.arange(N) / N * 2 * np.pi; R = N / (2 * np.pi)
    C = np.c_[R * np.cos(a), R * np.sin(a)]
    NL = -np.c_[np.cos(a), np.sin(a)]
    T = dict(n=N, spacing_m=float(np.linalg.norm(C[1] - C[0])), center=[[x, y, 0.0] for x, y in C],
             left=(C + hl[:, None] * NL).tolist(), right=(C - hr[:, None] * NL).tolist())
    return T, C, NL


J = [('right', 300, 360, 'mouth', 'test')]


def ref_for(C, NL, ol, orr, across=()):
    rd = {'left': {k: float(ol[k]) for k in range(N) if not np.isnan(ol[k])},
          'right': {k: float(orr[k]) for k in range(N) if not np.isnan(orr[k])}}
    lines = []
    for side, lo, hi in across:
        sg = 1 if side == 'left' else -1; v = ol if side == 'left' else orr
        ks = np.arange(lo, hi + 1)
        lines.append((side, C[ks] + sg * v[ks][:, None] * NL[ks]))
    return edge_gate.owner_reference(C, rd, lines, N)


def test_detected_edges_unchanged():
    """the detected-edge fixture: a width bulge in a section and a 40 m wave; owner=None and a reference with no owner
    reading give the original result, metric for metric"""
    s = np.arange(N); hl = 6.0 + 0.6 * np.sin(2 * np.pi * s / 40.0) * ((s > 500) & (s < 700)); hr = np.full(N, 5.5)
    hr[800:860] += 0.5
    T, C, NL = loop(hl, hr)
    m0, f0 = edge_gate.width_gates(T, J, log=Q)
    assert f0 == ['width consistency', 'edge waviness left']
    ref = ref_for(C, NL, np.full(N, np.nan), np.full(N, np.nan))
    m1, f1 = edge_gate.width_gates(T, J, log=Q, owner=ref)
    assert f1 == f0
    assert abs(m1['width']['max_dev'] - m0['width']['max_dev']) < 1e-9 and m1['width']['at'] == m0['width']['at']
    assert abs(m1['wave_left']['max'] - m0['wave_left']['max']) < 1e-9
    assert edge_gate.owner_station_gate(*edge_gate.half_widths(T), ref, log=Q) == ({}, [])


def test_width_measured_against_his_width():
    """his lines change width (a section constant would fail); the fit that follows them passes; 0.5 m off fails"""
    s = np.arange(N); ol = 6.0 + 0.8 * (s > 600); orr = np.full(N, 5.5)
    T, C, NL = loop(ol.copy(), orr.copy())
    ref = ref_for(C, NL, ol, orr)
    assert edge_gate.width_gates(T, J, log=Q)[1] != []                       # the old gate fails his own widening
    assert edge_gate.width_gates(T, J, log=Q, owner=ref)[1] == []
    hr = orr.copy(); hr[900:960] += 0.5
    T2, _, _ = loop(ol.copy(), hr)
    f = edge_gate.width_gates(T2, J, log=Q, owner=ref)[1]
    assert 'width consistency' in f


def test_station_tolerance_and_mouth_segments():
    """every reference station within tol; the mouth segment and `corner` stations either side are left out"""
    ol = np.full(N, 6.0); orr = np.full(N, 5.5)
    hl = ol.copy(); hl[400:410] -= 0.6                                        # 0.6 m inside his red
    T, C, NL = loop(hl, orr.copy())
    ref = ref_for(C, NL, ol, orr)
    assert edge_gate.owner_station_gate(*edge_gate.half_widths(T), ref, log=Q)[1] == ['owner reference left']
    c = edge_gate.OWNER_REF['corner']
    ref2 = ref_for(C, NL, ol, orr, across=[('left', 400 + c, 440)])             # the deviation within `corner` of a segment
    assert edge_gate.owner_station_gate(*edge_gate.half_widths(T), ref2, log=Q)[1] == []
    ref3 = ref_for(C, NL, ol, orr, across=[('left', 401 + c, 440)])             # station 400 one beyond: counted
    assert edge_gate.owner_station_gate(*edge_gate.half_widths(T), ref3, log=Q)[1] == ['owner reference left']
    hl2 = ol.copy(); hl2[400:410] -= 0.35                                       # within OWNER_REF tol
    T4, _, _ = loop(hl2, orr.copy())
    m, f = edge_gate.owner_station_gate(*edge_gate.half_widths(T4), ref, log=Q)
    assert f == [] and len(m['left']['over_025']) == 10


def test_band_of_the_deviation():
    """his red carries a 40 m wave: the old band gate fails the fit that follows it, the owner band passes it; a wave
    his red does not have fails"""
    s = np.arange(N); ol = 6.0 + 0.5 * np.sin(2 * np.pi * s / 40.0) * ((s > 500) & (s < 700)); orr = np.full(N, 5.5)
    T, C, NL = loop(ol.copy(), orr.copy())
    ref = ref_for(C, NL, ol, orr)
    assert 'edge waviness left' in edge_gate.width_gates(T, J, log=Q)[1]
    assert edge_gate.width_gates(T, J, log=Q, owner=ref)[1] == []
    hr = orr + 0.5 * np.sin(2 * np.pi * s / 40.0) * ((s > 900) & (s < 1000))
    T2, _, _ = loop(ol.copy(), hr)
    assert 'edge waviness right' in edge_gate.width_gates(T2, J, log=Q, owner=ref)[1]


def test_rolling_waviness_against_his_red():
    s = np.arange(N); own = 6.0 + 0.08 * np.sin(2 * np.pi * s / 12.0)           # his stroke's wiggle
    loose = np.ones(N, bool); mask = np.ones(N, bool)

    def wav(v):
        qq = ES.local_quad_resid(np.r_[v[-25:], v, v[:25]], 25)[25:-25]
        roll = np.array([np.sqrt(np.mean(qq[np.arange(k - 50, k + 50) % N] ** 2)) for k in range(N)])
        return qq, roll
    qq, roll = wav(own * 0 + 6.0 + 0.04 * np.sin(2 * np.pi * s / 12.0))        # the fit follows half his wiggle
    w = edge_gate.owner_waviness(qq, roll, loose, own, mask, N)
    assert not w['bad_roll'].any() and not w['bad_peak'].any()
    qq2, roll2 = wav(6.0 + 0.2 * np.sin(2 * np.pi * s / 12.0))                  # a wave larger than his
    w2 = edge_gate.owner_waviness(qq2, roll2, loose, own, mask, N)
    assert w2['bad_roll'].any() and w2['bad_peak'].any()
    flat = np.full(N, 6.0)                                                      # his red calm: the original limits
    w3 = edge_gate.owner_waviness(qq2, roll2, loose, flat, mask, N)
    assert np.allclose(w3['roll_limit'], edge_gate.FITTED['wave_rms']) and w3['bad_roll'].any()


def test_tol_only_tightens():
    assert edge_gate.owner_ref_thresholds({'owner_ref_tol': 0.3})['tol'] == 0.3
    assert edge_gate.owner_ref_thresholds({'owner_ref_tol': 0.9})['tol'] == edge_gate.OWNER_REF['tol']


def test_laguna_declares_no_owner_reference():
    sp = trackcfg.load('laguna_seca')['spline']
    assert not sp.get('owner_edges') and not sp.get('owner_mouths')


def test_sonoma_owner_edges_are_local():
    """Sonoma round 14B: his T1-T2 red is used only in the local refit whose window holds it (centre.local list), so the
    rest of the lap is the round-14A geometry held in world position"""
    c = trackcfg.load('sonoma')
    ow = c['spline']['owner_edges']
    assert ow and all(w.get('local') for w in ow) and c['spline'].get('owner_mouths')
    wins = [lc['window'] for lc in c['centre']['local']]
    assert wins[0] == (1643, 2091)   # round 11's window first, unchanged
    for w in ow:
        assert any(lo <= w['lo'] and w['hi'] <= hi for lo, hi in wins[1:])
