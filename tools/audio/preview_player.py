"""Analyse offline renders of the in-browser player (src/app/audio.ts run in an OfflineAudioContext, see README).

    uv run --python 3.12 --with numpy,scipy,soundfile,matplotlib python tools/audio/preview_player.py DIR

DIR holds sweep.f32 (10.5 s, full throttle, rpm 1000 -> 6500 linearly over 10 s, speed 0) and optionally
scenario.f32 (12 s: pull, lift-off, gear change dip, limiter, squeal ramp, lock-up), raw float32 mono 48 kHz.
Writes tools/audio/preview_player.png and prints the checks:
  - harmonic ladder: per-frame comb rpm vs the scripted rpm, and the largest frame-to-frame level step
  - clicks: 5 ms frames of > 6 kHz energy against their running median (loop seams / voice swaps would spike)
  - gaps: the quietest 50 ms frame against the median
"""

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import ndimage, signal

from common import CLIP_SOURCE, HERE, SR, STARTS, file_start, load_audio, load_logger

ORD = np.arange(1, 9) * 1.5
W = np.array([0.6, 1.5, 0.8, 1.2, 0.6, 0.8, 0.5, 0.5])


def comb_rpm(x, prior_fn, t_offset=0.0):
    nfft, hop = 8192, 1200
    f = np.fft.rfftfreq(nfft, 1 / SR)
    win = np.hanning(nfft)
    n = (len(x) - nfft) // hop + 1
    t = (np.arange(n) * hop + nfft / 2) / SR
    est = np.full(n, np.nan)
    for j in range(n):
        S = 20 * np.log10(np.abs(np.fft.rfft(x[j * hop:j * hop + nfft] * win)) + 1e-9)
        S -= np.median(S[8:400])
        p = prior_fn(t[j] + t_offset)
        cand = np.arange(p * 0.85, p * 1.15, 4.0)
        val = np.interp(cand[:, None] / 60 * ORD[None, :] / f[1], np.arange(len(f)), S)
        est[j] = cand[np.argmax(val @ W)]
    return t, est


def clicks(x):
    hp = signal.sosfilt(signal.butter(4, 6000, "highpass", fs=SR, output="sos"), x)
    fr = int(0.005 * SR)
    e = np.sqrt(np.mean(hp[: len(hp) // fr * fr].reshape(-1, fr) ** 2, axis=1)) + 1e-9
    med = ndimage.median_filter(e, 81)
    return np.arange(len(e)) * fr / SR, e / med


def level(x, fr_s=0.05):
    fr = int(fr_s * SR)
    return 20 * np.log10(np.sqrt(np.mean(x[: len(x) // fr * fr].reshape(-1, fr) ** 2, axis=1)) + 1e-9)


def main(d):
    x = np.fromfile(os.path.join(d, "sweep.f32"), dtype=np.float32).astype(np.float64)
    script = lambda t: 1000 + 5500 * np.clip(t / 10, 0, 1)
    t, est = comb_rpm(x, script)
    ok = (t > 0.3) & (t < 10)
    err = np.abs(est[ok] - script(t[ok]))
    tc, cr = clicks(x)
    sel = (tc > 0.2) & (tc < 10.2)
    lv = level(x)
    tl = np.arange(len(lv)) * 0.05
    lvs = lv[(tl > 0.3) & (tl < 10)]
    print(f"sweep: comb rpm vs script median |err| {np.median(err):.0f} rpm, 95th pct {np.percentile(err, 95):.0f} rpm")
    print(f"sweep: max HF click ratio {cr[sel].max():.2f} (>6 kHz 5 ms energy / running median; > 3 = click)")
    print(f"sweep: level range {lvs.min():.1f}..{lvs.max():.1f} dBFS, largest 50 ms step {np.abs(np.diff(lvs)).max():.2f} dB, "
          f"quietest frame {lvs.min() - np.median(lvs):.1f} dB vs median")

    # footage: the full-throttle pull in 03_hand_topspeed (clip 13.5-21 s, ~2900 -> 5450 rpm)
    src, at = CLIP_SOURCE["03_hand_topspeed"]
    raw = load_audio(src, at + 13.0, 8.5)
    L = load_logger()
    st = file_start(src)
    fig, ax = plt.subplots(4, 1, figsize=(13, 17), gridspec_kw={"height_ratios": [3, 3, 1.3, 1.3]})
    for a, sig, title, rpmf in (
        (ax[0], x, "player render (OfflineAudioContext): full throttle, rpm 1000 -> 6500 over 10 s; dashed: orders 3 and 6 of the scripted rpm",
         script),
        (ax[1], raw, f"footage: full-throttle pull, 03_hand_topspeed.mp4 13.0-21.5 s ({src} {at + 13:.0f} s); dashed: orders 3 and 6 of the logger rpm",
         lambda tt: np.interp(tt + at + 13.0 + st, L["t"], L["rpm"]))):
        f, tt, S = signal.spectrogram(sig, SR, nperseg=8192, noverlap=8192 - 1200)
        D = 10 * np.log10(S + 1e-14)
        D -= np.median(D, axis=1, keepdims=True)
        a.pcolormesh(tt, f, D, shading="auto", cmap="magma", vmin=0, vmax=25)
        for k in (3, 6):
            a.plot(tt, rpmf(tt) / 60 * k, "c--", lw=0.7)
        a.set_ylim(0, 1200)
        a.set_ylabel("Hz")
        a.set_title(title, fontsize=9)
    for b in range(1000, 6501, 250):
        ax[0].axvline((b - 1000) / 550, color="w", lw=0.3, alpha=0.4)
    ax[2].plot(t[ok], est[ok] - script(t[ok]), "k", lw=0.8)
    ax[2].set_ylabel("comb rpm - script")
    ax[2].set_ylim(-150, 150)
    ax[2].set_title("render: rpm read back from the harmonics (bin boundaries every 250 rpm = every 0.455 s, faint lines above)", fontsize=9)
    ax[3].plot(tl, lv - np.median(lvs), "b", lw=0.8, label="50 ms level, dB re median")
    ax[3].plot(tc, 10 * np.log10(cr), "r", lw=0.5, label="> 6 kHz click detector, dB re running median")
    ax[3].set_ylim(-20, 15)
    ax[3].set_xlim(0, 10.5)
    ax[3].legend(fontsize=8)
    ax[3].set_xlabel("render time, s")
    for a in ax[2:]:
        a.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "preview_player.png"), dpi=75)

    sc = os.path.join(d, "scenario.f32")
    if os.path.exists(sc):
        y = np.fromfile(sc, dtype=np.float32).astype(np.float64)
        tc2, cr2 = clicks(y)
        fig, ax = plt.subplots(2, 1, figsize=(13, 8))
        f, tt, S = signal.spectrogram(y, SR, nperseg=4096, noverlap=4096 - 600)
        D = 10 * np.log10(S + 1e-14)
        ax[0].pcolormesh(tt, f, D, shading="auto", cmap="magma", vmin=D.max() - 70, vmax=D.max())
        ax[0].set_ylim(0, 3000)
        for t0, lab in ((0, "pull"), (3, "lift"), (5, "on"), (6, "shift"), (7, "limiter"), (8.5, "squeal ramp"),
                        (10.3, "lock-up")):
            ax[0].axvline(t0, color="w", lw=0.6)
            ax[0].text(t0 + 0.05, 2800, lab, color="w", fontsize=8)
        ax[0].set_title("player render, scenario (speed 20 m/s): engine, lift-off, gear-change dip, limiter, squeal, skid", fontsize=9)
        lv2 = level(y, 0.01)
        ax[1].plot(np.arange(len(lv2)) * 0.01, lv2, "b", lw=0.7, label="10 ms level dBFS")
        ax[1].plot(tc2, 10 * np.log10(cr2) - 40, "r", lw=0.5, label="click detector - 40 dB")
        ax[1].legend(fontsize=8)
        ax[1].set_xlim(0, 12)
        fig.tight_layout()
        fig.savefig(os.path.join(HERE, "preview_scenario.png"), dpi=75)
        print(f"scenario: peak {np.abs(y).max():.2f}, max HF click ratio {cr2[(tc2 > 0.2) & (tc2 < 11.8)].max():.2f}")


if __name__ == "__main__":
    main(sys.argv[1])
