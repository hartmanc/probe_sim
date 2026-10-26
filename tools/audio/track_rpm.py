"""Per-frame engine rpm from the race audio (harmonic comb seeded by the aligned logger rpm) plus cleanliness
measures, cached as cache/track_<file>.npz. Used by build_engine.py and build_squeal.py.

Per 25 ms frame: rpm_a (audio rpm), contrast (dB: comb level at orders 1.5, 3, ... 12 minus the level half-way
between them, on a whitened log spectrum), rpm_l and thr (logger, aligned, linear between OBD reads), thr_lo/thr_hi
(the bracketing OBD throttle reads), speed (GPS m/s), lf (dB level 20-90 Hz minus 300-3000 Hz: wind/road rumble),
hf_mod (syllabic 2-8 Hz modulation of the 1-3 kHz envelope over +/-0.5 s: speech / radio).
"""

from __future__ import annotations

import csv
import os
from datetime import datetime

import numpy as np
from scipy import signal

from common import CACHE, LOGGER, SR, STARTS, file_start, load_audio, load_logger

NFFT, HOP = 8192, 1200
ORD = np.arange(1, 9) * 1.5
W = np.array([0.6, 1.5, 0.8, 1.2, 0.6, 0.8, 0.5, 0.5])


def gps_speed(offset: float):
    t, v = [], []
    with open(LOGGER) as fh:
        for r in csv.DictReader(fh):
            if r["gps_speed_mps"]:
                t.append(datetime.fromisoformat(r["timestamp_utc"]).timestamp() + offset)
                v.append(float(r["gps_speed_mps"]))
    return np.array(t), np.array(v)


def track(name: str, force: bool = False) -> dict:
    out = os.path.join(CACHE, f"track_{name}.npz")
    if os.path.exists(out) and not force:
        return dict(np.load(out))
    L = load_logger()
    gt, gv = gps_speed(L["offset"])
    x = load_audio(name)
    start = file_start(name)
    win = np.hanning(NFFT).astype(np.float32)
    freqs = np.fft.rfftfreq(NFFT, 1 / SR)
    kmax = int(2200 / (freqs[1]))
    nfr = (len(x) - NFFT) // HOP + 1
    tf = (np.arange(nfr) * HOP + NFFT / 2) / SR
    rl = np.interp(tf + start, L["t"], L["rpm"], left=np.nan, right=np.nan)
    th = np.interp(tf + start, L["t"], L["thr"], left=np.nan, right=np.nan)
    idx = np.searchsorted(L["t"], tf + start)
    idx = np.clip(idx, 1, len(L["t"]) - 1)
    th_a, th_b = L["thr"][idx - 1], L["thr"][idx]
    thr_lo, thr_hi = np.minimum(th_a, th_b), np.maximum(th_a, th_b)
    rpm_a = np.full(nfr, np.nan, np.float32)
    contrast = np.full(nfr, np.nan, np.float32)
    lf = np.full(nfr, np.nan, np.float32)
    hfenv = np.zeros(nfr, np.float32)
    df = freqs[1]
    bins = np.arange(kmax)
    b_lf = (freqs[:kmax] >= 20) & (freqs[:kmax] < 90)
    b_mid = (freqs[:kmax] >= 300) & (freqs[:kmax] < 2200)
    step = 4000
    for j0 in range(0, nfr, step):
        j1 = min(nfr, j0 + step)
        ii = np.arange(NFFT)[None, :] + HOP * np.arange(j0, j1)[:, None]
        spec = np.abs(np.fft.rfft(x[ii] * win, axis=1))[:, :kmax]
        p = spec ** 2
        lf[j0:j1] = 10 * np.log10(p[:, b_lf].mean(1) + 1e-12) - 10 * np.log10(p[:, b_mid].mean(1) + 1e-12)
        # 1-3 kHz envelope from a separate short FFT is overkill; use the 1-2.2 kHz part of this one
        hfenv[j0:j1] = 10 * np.log10(p[:, (freqs[:kmax] > 1000)].mean(1) + 1e-12)
        D = 20 * np.log10(spec + 1e-7)
        D -= np.median(D[:, 8:], axis=1, keepdims=True)
        for j in range(j0, j1):
            r0 = rl[j]
            if not np.isfinite(r0) or r0 < 600:
                continue
            cand = np.arange(r0 * 0.88, r0 * 1.12, 4.0)
            row = D[j - j0]
            fb = cand[:, None] / 60 * ORD[None, :] / df
            ok = fb < kmax - 2
            val = np.interp(fb, bins, row) * ok
            sc = val @ W
            k = int(np.argmax(sc))
            if 0 < k < len(cand) - 1:  # parabolic refinement
                a, b, c = sc[k - 1], sc[k], sc[k + 1]
                d = 0.5 * (a - c) / (a - 2 * b + c) if (a - 2 * b + c) != 0 else 0.0
                r = cand[k] + 4.0 * float(np.clip(d, -1, 1))
            else:
                r = cand[k]
            rpm_a[j] = r
            on = r / 60 * ORD / df
            mid = r / 60 * (ORD + 0.75) / df
            okk = mid < kmax - 2
            contrast[j] = np.interp(on[okk], bins, row).mean() - np.interp(mid[okk], bins, row).mean()
    # speech / radio: syllable-rate (2-8 Hz) modulation of the HF envelope
    fs_env = SR / HOP
    sos = signal.butter(2, [2.0, 8.0], "bandpass", fs=fs_env, output="sos")
    mod = signal.sosfiltfilt(sos, hfenv - np.median(hfenv))
    k = int(fs_env)
    hf_mod = np.sqrt(np.convolve(mod ** 2, np.ones(k) / k, "same")).astype(np.float32)
    res = {"t": tf.astype(np.float64), "rpm_a": rpm_a, "contrast": contrast, "rpm_l": rl.astype(np.float32),
           "thr": th.astype(np.float32), "thr_lo": thr_lo.astype(np.float32), "thr_hi": thr_hi.astype(np.float32),
           "speed": np.interp(tf + start, gt, gv, left=np.nan, right=np.nan).astype(np.float32), "lf": lf,
           "hf_mod": hf_mod}
    np.savez_compressed(out, **res)
    return res


if __name__ == "__main__":
    for n in STARTS:
        r = track(n, force=True)
        ok = np.isfinite(r["rpm_a"])
        print(n, ok.sum(), np.nanmedian(r["contrast"]), np.nanmedian(np.abs(r["rpm_a"] - r["rpm_l"])))
