"""Shared loop-making DSP for the sample-based engines (the Probe's build_engine.py and families/build_family.py).

Moved verbatim out of build_engine.py (the Probe build still produces identical sprites); the only generalisation
is spectral_gate's `order_step` (harmonic spacing in engine orders: 1.5 for the Probe's even-fire V6, 0.5 for any
engine whose half orders matter), which defaults to the Probe's value.

All functions work at common.SR (48 kHz). Engine cycle = 2 crank revs (four-stroke).
"""

from __future__ import annotations

import numpy as np
from scipy import signal

from common import SR

XFADE = int(0.06 * SR)
PAD = int(0.05 * SR)


def runs(mask: np.ndarray):
    d = np.diff(np.r_[0, mask.astype(np.int8), 0])
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))


def sinc_interp(x: np.ndarray, pos: np.ndarray, taps: int = 32) -> np.ndarray:
    """Band-limited read of x at fractional sample positions (Blackman-windowed sinc)."""
    base = np.floor(pos).astype(np.int64)
    frac = pos - base
    k = np.arange(-taps // 2 + 1, taps // 2 + 1)
    idx = np.clip(base[:, None] + k[None, :], 0, len(x) - 1)
    d = frac[:, None] - k[None, :]
    w = np.sinc(d) * (0.42 + 0.5 * np.cos(np.pi * d / (taps / 2)) + 0.08 * np.cos(2 * np.pi * d / (taps / 2)))
    w[np.abs(d) >= taps / 2] = 0
    out = np.empty(len(pos), np.float64)
    for i0 in range(0, len(pos), 65536):
        sl = slice(i0, i0 + 65536)
        out[sl] = (x[idx[sl]] * w[sl]).sum(1)
    return out


def warp_flat(x: np.ndarray, t_frames: np.ndarray, rpm_frames: np.ndarray, weights: np.ndarray, B: float):
    """Resample x (time 0 = x[0]) so the engine runs at exactly B rpm. Returns the warped signal."""
    ok = np.isfinite(rpm_frames)
    deg = 3 if ok.sum() > 12 else 1
    p = np.polyfit(t_frames[ok], rpm_frames[ok], deg, w=np.clip(weights[ok], 0.5, None))
    tt = np.arange(len(x)) / SR
    r = np.polyval(p, tt)
    cyc = np.cumsum(r / 120.0) / SR  # engine cycles (2 revs) elapsed
    m_per_cycle = SR * 120.0 / B
    n_out = int((cyc[-1] - cyc[0]) * m_per_cycle) - 2
    c_out = cyc[0] + np.arange(n_out) / m_per_cycle
    pos = np.interp(c_out, cyc, np.arange(len(x)))
    return sinc_interp(x.astype(np.float64), pos), float(np.std(r) / B)


def spectral_gate(y: np.ndarray, B: float, gmin_db: float = -10.0, order_step: float = 1.5) -> np.ndarray:
    """Gentle gating against the floor between the harmonics (the engine is at constant B after warping)."""
    nfft, hop = 8192, 1024
    f, t, Z = signal.stft(y, SR, nperseg=nfft, noverlap=nfft - hop, window="hann", boundary="even")
    P = np.abs(Z) ** 2
    Pm = P.mean(1)
    spacing = order_step * B / 60.0 / (f[1] - f[0])  # bins between harmonics
    w = max(5, int(2.2 * spacing) | 1)
    floor = np.exp(signal.order_filter(np.log(Pm + 1e-20), np.ones(w), int(w * 0.25)))
    floor = np.convolve(floor, np.ones(9) / 9, "same")
    Ps = signal.convolve2d(P, np.ones((1, 3)) / 3, mode="same", boundary="symm")
    g = np.maximum(10 ** (gmin_db / 20), 1 - floor[:, None] / (Ps + 1e-20))
    g = signal.convolve2d(g, np.ones((3, 3)) / 9, mode="same", boundary="symm")
    _, out = signal.istft(Z * g, SR, nperseg=nfft, noverlap=nfft - hop, window="hann", boundary=True)
    return out[: len(y)]


def highpass(y: np.ndarray, fc: float = 40.0) -> np.ndarray:
    return signal.sosfiltfilt(signal.butter(2, fc, "highpass", fs=SR, output="sos"), y)


def find_loop(y: np.ndarray, B: float, max_len_s: float = 1.0, min_len_s: float = 0.6):
    """Pick start a and length L (near a whole number of engine cycles) maximising the correlation of the
    XFADE samples after a with those after a + L. Returns (a, L, rho, n_cycles)."""
    m = SR * 120.0 / B
    avail = len(y) - 2 * PAD - XFADE
    n_cyc = int(min(max_len_s * SR, avail) // m)
    if n_cyc * m < min_len_s * SR * 0.75 or n_cyc < 1:
        n_cyc = max(1, int(avail // m))
    L0 = n_cyc * m
    band = signal.sosfiltfilt(signal.butter(2, [60, 3000], "bandpass", fs=SR, output="sos"), y)
    best = (-2.0, 0, int(round(L0)))
    lags = np.arange(int(L0 * 0.994), int(L0 * 1.006) + 1)
    starts = np.arange(PAD, max(PAD + 1, len(y) - PAD - XFADE - lags[-1]), int(0.004 * SR))
    sq = np.r_[0.0, np.cumsum(band ** 2)]
    for a in starts:
        seg = band[a:a + XFADE]
        na = np.linalg.norm(seg) + 1e-12
        lo, hi = a + lags[0], min(len(band) - XFADE, a + lags[-1])
        if hi < lo:
            break
        c = np.correlate(band[lo:hi + XFADE], seg, mode="valid")
        e = np.sqrt(sq[lo + XFADE:hi + 1 + XFADE] - sq[lo:hi + 1]) + 1e-12
        rr = c / (na * e)
        k = int(np.argmax(rr))
        if rr[k] > best[0]:
            best = (float(rr[k]), int(a), int(lags[0] + k))
    rho, a, L = best
    return a, L, rho, n_cyc


def make_loop(y: np.ndarray, a: int, L: int, rho: float) -> np.ndarray:
    """Loop of L samples starting at a; the head is crossfaded with what follows the tail."""
    out = y[a:a + L].copy()
    s = (np.arange(XFADE) + 0.5) / XFADE
    r = float(np.clip(rho, 0.0, 1.0))
    k = 1.0 / np.sqrt(s * s + (1 - s) ** 2 + 2 * r * s * (1 - s))
    out[:XFADE] = s * k * y[a:a + XFADE] + (1 - s) * k * y[a + L:a + L + XFADE]
    return out


def _a_weight_sos():
    """IEC 61672 A-weighting as a digital filter (bilinear transform of the analog prototype)."""
    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217
    z = [0, 0, 0, 0]
    p = [-2 * np.pi * f1] * 2 + [-2 * np.pi * f2, -2 * np.pi * f3] + [-2 * np.pi * f4] * 2
    k = (2 * np.pi * f4) ** 2
    zd, pd, kd = signal.bilinear_zpk(z, p, k, SR)
    sos = signal.zpk2sos(zd, pd, kd)
    w, h = signal.sosfreqz(sos, [1000], fs=SR)
    sos[0, :3] /= abs(h[0])
    return sos


A_SOS = _a_weight_sos()


def transient_ratio(loop: np.ndarray) -> float:
    """Largest 5 ms burst of > 6 kHz energy over its running median, on the loop played twice (seam included).
    A tick in the source would repeat once per loop."""
    y = np.tile(loop, 3)
    hp = signal.sosfilt(signal.butter(4, 6000, "highpass", fs=SR, output="sos"), y)
    fr = int(0.005 * SR)
    e = np.sqrt(np.mean(hp[: len(hp) // fr * fr].reshape(-1, fr) ** 2, axis=1)) + 1e-12
    r = e / signal.medfilt(e, 81)
    n = len(loop) // fr
    return float(r[n: 2 * n + 2].max())


def rms_db(y: np.ndarray) -> float:
    """A-weighted RMS level, dB re full scale (the unweighted level is dominated by sub-100 Hz rumble)."""
    ya = signal.sosfilt(A_SOS, np.tile(y, 2))[len(y):]
    return 20 * np.log10(np.sqrt(np.mean(ya ** 2)) + 1e-12)


def pitch_shift(src: dict, B: int, max_len_s: float = 1.0) -> dict:
    """Resample the source's processed segment so its engine runs at B rpm, then loop it again."""
    ratio = B / src["rpm"]
    y = src["long"]
    pos = np.arange(0, len(y) - 32, ratio)
    z = sinc_interp(y, pos)
    if ratio > 1:  # raising pitch: band-limit first to avoid aliasing above Nyquist
        z = signal.sosfiltfilt(signal.butter(8, 0.95 * SR / 2 / ratio, fs=SR, output="sos"), z) if ratio > 1.05 else z
    a_, L, rho, n_cyc = find_loop(z, B, max_len_s=max_len_s, min_len_s=min(0.4, max_len_s))
    lp = make_loop(z, a_, L, rho)
    return {"loop": lp, "rho": rho, "tick": transient_ratio(lp), "rpm": n_cyc * 120.0 * SR / L, "n_cycles": n_cyc,
            "long": z, "name": src["name"], "t": src["t"], "from_rpm": src["bin"], "ratio": ratio}

