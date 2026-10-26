"""Extract a tyre squeal loop from the race footage.

    uv run --python 3.12 --with numpy,scipy,soundfile,matplotlib python tools/audio/build_squeal.py

1. Lateral acceleration from the logger (yaw rate about the gravity axis x GPS speed). High-g stretches
   (|a_lat| > 10 m/s^2, speed > 12 m/s, >= 0.5 s) are candidates.
2. In each, a 25 ms-hop spectrogram with the engine's harmonics (orders 1.5k of the tracked rpm, +/-15 Hz)
   masked; per frame the strongest peak in 900-1700 Hz above the local spectral median ("tonal prominence").
   The candidate with the longest stretch of prominence > 7 dB at a steady pitch wins.
3. Spectral subtraction against the 0.8 s just before the squeal (same corner, same engine, no squeal),
   band 600-5000 Hz, then a loop with a 150 ms correlation-compensated crossfade.
Writes public/audio/squeal.ogg (Opus 64 kbps), public/audio/squeal.json and tools/audio/preview_squeal.png.
"""

from __future__ import annotations

import json
import os
import subprocess

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf
from scipy import ndimage, signal

from common import FFMPEG, HERE, ROOT, SR, STARTS, file_start, load_audio, load_logger
from track_rpm import gps_speed, track

OUT = os.path.join(ROOT, "public", "audio")
N, HOP = 4096, 1200
XF = int(0.15 * SR)


def lateral_accel(L):
    gt, gv = gps_speed(L["offset"])
    g = L["acc"].mean(0)
    up = g / np.linalg.norm(g)
    yaw = L["gyro"] @ up
    v = np.interp(L["imu_t"], gt, gv)
    return L["imu_t"], np.convolve(np.abs(yaw * v), np.ones(5) / 5, "same")


def prominence(x: np.ndarray, t0: float, r: dict):
    """Per-frame tonal prominence (dB) and frequency in 900-1700 Hz, engine harmonics masked."""
    win = np.hanning(N).astype(np.float32)
    f = np.fft.rfftfreq(N, 1 / SR)
    n = (len(x) - N) // HOP + 1
    ii = np.arange(N)[None, :] + HOP * np.arange(n)[:, None]
    S = 20 * np.log10(np.abs(np.fft.rfft(x[ii] * win, axis=1)) + 1e-7)
    tc = t0 + (np.arange(n) * HOP + N / 2) / SR
    R = np.interp(tc, r["t"], np.nan_to_num(r["rpm_a"], nan=3000.0))
    E = S - ndimage.median_filter(S, size=(1, 41))
    for k in range(n):
        fk = np.arange(1, 80) * 1.5 * R[k] / 60
        for h in fk[fk < 2000]:
            E[k, np.abs(f - h) < 15] = 0
    band = (f > 900) & (f < 1700)
    P = ndimage.uniform_filter1d(E[:, band], 3, axis=0)
    kk = np.argmax(P, axis=1)
    return tc, P[np.arange(n), kk], f[band][kk]


def longest_run(mask: np.ndarray, gap: int = 3):
    m = ndimage.binary_closing(mask, np.ones(gap)) if mask.any() else mask
    lab, nl = ndimage.label(m)
    if nl == 0:
        return 0, 0
    sizes = ndimage.sum(m, lab, range(1, nl + 1))
    i = int(np.argmax(sizes)) + 1
    idx = np.nonzero(lab == i)[0]
    return idx[0], idx[-1] + 1


def main():
    L = load_logger()
    at, al = lateral_accel(L)
    cands = []
    for name in STARTS:
        r = track(name)
        st = file_start(name)
        a = np.interp(r["t"] + st, at, al, left=0, right=0)
        hi = np.nonzero((a > 10) & (r["speed"] > 12) & np.isfinite(r["rpm_a"]))[0]
        if len(hi) == 0:
            continue
        for seg in np.split(hi, np.nonzero(np.diff(hi) > 4)[0] + 1):
            if len(seg) < 20:
                continue
            t0, t1 = r["t"][seg[0]] - 0.5, r["t"][seg[-1]] + 1.5  # squeal often lasts into the exit
            x = load_audio(name, t0, t1 - t0)
            tc, pv, fq = prominence(x, t0, r)
            s, e = longest_run((pv > 7) & (np.abs(fq - np.median(fq[pv > 7]) if (pv > 7).any() else 0) < 120))
            if e - s < 8:
                continue
            dur = (e - s) * HOP / SR
            score = dur * float(np.mean(pv[s:e]))
            cands.append((score, name, float(tc[s]), float(tc[e - 1]), float(np.median(fq[s:e])),
                          float(np.mean(pv[s:e])), float(a[seg].mean())))
    cands.sort(key=lambda c: -c[0])
    print(f"{len(cands)} high-g stretches with a sustained tone; best:")
    for c in cands[:8]:
        print("  %s %.2f-%.2f s  f=%.0f Hz  prominence %.1f dB  a_lat %.1f m/s2  score %.1f" % (c[1], c[2], c[3], c[4],
              c[5], c[6], c[0]))
    _, name, ts, te, f0, prom, alat = cands[0]
    dur = min(1.6, max(0.9, te - ts + 0.1))
    s0 = ts - 0.05
    x = load_audio(name, s0 - 1.0, dur + 1.3)
    base = x[int(0.1 * SR):int(0.9 * SR)]  # 0.9..0.1 s before the squeal
    # spectral subtraction against the pre-squeal baseline
    nf, hop = 2048, 256
    _, _, Zb = signal.stft(base, SR, nperseg=nf, noverlap=nf - hop)
    Nb = np.mean(np.abs(Zb) ** 2, axis=1)
    f, _, Z = signal.stft(x, SR, nperseg=nf, noverlap=nf - hop)
    P = signal.convolve2d(np.abs(Z) ** 2, np.ones((1, 3)) / 3, mode="same", boundary="symm")
    g = np.maximum(10 ** (-30 / 20), 1 - 2.0 * Nb[:, None] / (P + 1e-20))
    g *= ((f > 600) & (f < 5000))[:, None]
    g = signal.convolve2d(g, np.ones((3, 3)) / 9, mode="same", boundary="symm")
    _, y = signal.istft(Z * g, SR, nperseg=nf, noverlap=nf - hop)
    y = y[:len(x)]
    y = signal.sosfiltfilt(signal.butter(4, [600, 5000], "bandpass", fs=SR, output="sos"), y)
    seg = y[int(1.0 * SR):int((1.0 + dur) * SR)]
    # loop: last XF samples crossfade into the head
    Lp = len(seg) - XF
    a_, b_ = seg[:XF], seg[Lp:]
    rho = float(np.clip(a_ @ b_ / (np.linalg.norm(a_) * np.linalg.norm(b_) + 1e-12), 0, 1))
    s = (np.arange(XF) + 0.5) / XF
    k = 1 / np.sqrt(s * s + (1 - s) ** 2 + 2 * rho * s * (1 - s))
    loop = seg[:Lp].copy()
    loop[:XF] = s * k * seg[:XF] + (1 - s) * k * seg[Lp:]
    loop *= 0.5 / np.max(np.abs(loop))
    os.makedirs(OUT, exist_ok=True)
    wav = os.path.join(HERE, "cache", "squeal.wav")
    pad = int(0.05 * SR)
    sprite = np.concatenate([np.zeros(int(0.1 * SR)), loop[-pad:], loop, loop[:pad], np.zeros(int(0.1 * SR))])
    sf.write(wav, sprite.astype(np.float32), SR, subtype="FLOAT")
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", wav, "-c:a", "libopus", "-b:a", "64k", "-ar", "48000", "-ac", "1",
                    os.path.join(OUT, "squeal.ogg")], check=True)
    meta = {"offset": round((int(0.1 * SR) + pad) / SR, 6), "duration": round(Lp / SR, 6), "f0": round(f0, 1),
            "source": f"{name} @ {s0:.2f} s (+{dur:.2f} s), a_lat {alat:.1f} m/s2, tone prominence {prom:.1f} dB",
            "route": "extracted from the footage (spectral subtraction against the pre-squeal 0.8 s)",
            "seam_corr": round(rho, 3)}
    json.dump(meta, open(os.path.join(OUT, "squeal.json"), "w"), indent=1)
    print(meta, "bytes", os.path.getsize(os.path.join(OUT, "squeal.ogg")))

    # preview
    r = track(name)
    st = file_start(name)
    ctx = load_audio(name, s0 - 2.0, dur + 4.0)
    fig, ax = plt.subplots(3, 1, figsize=(13, 11))
    for a, sig, t0, title in ((ax[0], ctx, s0 - 2.0, f"footage {name} {s0 - 2:.1f}-{s0 + dur + 2:.1f} s (unprocessed, absolute dB)"),
                              (ax[1], np.tile(loop, 3), 0.0, f"shipped loop x3 ({Lp / SR:.2f} s, seams dashed)")):
        ff, tt, S = signal.spectrogram(sig, SR, nperseg=2048, noverlap=2048 - 256)
        D = 10 * np.log10(S + 1e-14)
        top = D[(ff > 300) & (ff < 5000)].max()
        a.pcolormesh(tt + t0, ff, D, shading="auto", cmap="magma", vmin=top - 55, vmax=top)
        a.set_ylim(300, 5000)
        a.set_ylabel("Hz")
        a.set_title(title, fontsize=9)
    for sx in (1, 2):
        ax[1].axvline(sx * Lp / SR, color="w", ls="--", lw=0.8)
    ax[0].axvspan(s0, s0 + dur, color="c", alpha=0.12)
    tg = np.linspace(s0 - 2, s0 + dur + 2, 400)
    ax[2].plot(tg, np.interp(tg + st, at, al) / 9.81, "c", label="|a_lat| (g, logger yaw rate x GPS speed)")
    ax[2].plot(tg, np.interp(tg, r["t"], r["thr"]) / 95, "g", label="throttle (1 = full)")
    ax[2].plot(tg, np.interp(tg, r["t"], r["speed"]) / 40, "k", label="speed / 40 m/s")
    ax[2].axvspan(s0, s0 + dur, color="c", alpha=0.12, label="extracted")
    ax[2].legend(fontsize=8)
    ax[2].set_xlabel(f"{name} time, s")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "preview_squeal.png"), dpi=75)


if __name__ == "__main__":
    main()
