"""Verify / refine the logger -> camera clock offset with the engine itself.

For each candidate offset the logger rpm predicts where the firing harmonics (order 3 = rpm/60*3 Hz, and order 6)
should sit in the race audio; the offset whose prediction lands on the most harmonic energy wins. Each proxy chapter gets its own
correction (the camera's per-file start times are off by different amounts). The result goes to
alignment.json (read by common.logger_offset) and preview_alignment.png shows the audio's dominant harmonic against
the logger on 03_hand_topspeed.mp4.

    uv run --python 3.12 --with numpy,scipy,soundfile,matplotlib python tools/audio/align.py
"""

import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import ALIGN_JSON, CLIP_SOURCE, HERE, SR, STARTS, load_audio, load_logger, stft_mag

NFFT, HOP = 8192, 2400  # 5.9 Hz bins, 0.05 s frames
FMAX = 1500.0


def whitened(name: str):
    """Log spectrum up to FMAX, each frame minus its median (removes broadband loudness), in 120 s chunks."""
    x = load_audio(name)
    ts, out = [], []
    chunk = 120 * SR
    for s in range(0, len(x) - NFFT, chunk):
        f, t, m = stft_mag(x[s:s + chunk + NFFT], NFFT, HOP)
        keep = f <= FMAX
        d = 20 * np.log10(m[keep] + 1e-7)
        d -= np.median(d[(f[keep] > 50)], axis=0, keepdims=True)
        ts.append(t + s / SR)
        out.append(d.astype(np.float32))
    return f[keep], np.concatenate(ts), np.concatenate(out, axis=1)


def order_score(f, t_cam, D, lt, lrpm, offsets, orders=(3.0, 6.0)):
    """Mean whitened level at the predicted harmonic bins, per candidate offset (relative to the logger's)."""
    df = f[1] - f[0]
    scores = []
    for off in offsets:
        r = np.interp(t_cam - off, lt, lrpm, left=np.nan, right=np.nan)
        ok = np.isfinite(r) & (r > 1500)
        acc, n = 0.0, 0
        for k in orders:
            b = np.rint(r[ok] / 60 * k / df).astype(int)
            good = b < len(f) - 1
            cols = np.nonzero(ok)[0][good]
            acc += D[b[good], cols].sum()
            n += good.sum()
        scores.append(acc / max(n, 1))
    return np.array(scores)


def audio_rpm(f, D, prior):
    """Per-frame rpm from a harmonic comb (orders 1.5..9 step 1.5, order 3/6 weighted) searched within ±20 % of a
    prior; used only for the plot."""
    df = f[1] - f[0]
    est = np.full(D.shape[1], np.nan)
    orders = np.array([1.5, 3, 4.5, 6, 7.5, 9])
    w = np.array([0.5, 1.5, 0.7, 1.0, 0.5, 0.5])
    for j in range(D.shape[1]):
        if not np.isfinite(prior[j]) or prior[j] < 1200:
            continue
        cand = np.arange(prior[j] * 0.8, prior[j] * 1.2, 5.0)
        b = cand[:, None] / 60 * orders[None, :] / df
        val = np.interp(b, np.arange(len(f)), D[:, j])
        est[j] = cand[np.argmax(val @ w)]
    return est


def main():
    L = load_logger()  # sync.json offset (yaw-rate match); per-file corrections are searched on top
    base = L["offset"]
    coarse = np.arange(-150, 150.01, 0.25)
    corrections, scores, spec = {}, {}, {}
    for name in STARTS:
        f, t, D = whitened(name)
        spec[name] = (f, t, D)
        s = order_score(f, t + STARTS[name], D, L["t"], L["rpm"], coarse)
        if np.nanmax(s) - np.nanmedian(s) < 2.0:
            print(f"{name}: no clear harmonic match (no logger overlap?)")
            continue
        c0 = coarse[np.nanargmax(s)]
        fine = np.arange(c0 - 1, c0 + 1.001, 0.02)
        sf_ = order_score(f, t + STARTS[name], D, L["t"], L["rpm"], fine)
        corrections[name] = round(float(fine[np.argmax(sf_)]), 2)
        scores[name] = (coarse, s)
        print(f"{name}: correction {corrections[name]:+.2f} s, peak {np.nanmax(s) - np.nanmedian(s):.1f} dB over "
              f"the off-alignment level")
    json.dump({"logger_offset_s": base, "file_correction_s": corrections,
               "meaning": "audio time tau in proxy F lines up with logger time (timestamp_utc + logger_offset_s) = "
                          "STARTS[F] + tau - file_correction_s[F]; the correction is constant within each file "
                          "(checked in 300 s windows), so it is an error in the camera's per-chapter start time",
               "method": "max mean whitened level at logger-predicted order 3 and 6 harmonics"},
              open(ALIGN_JSON, "w"), indent=1)

    # --- plot: 03_hand_topspeed, spectrogram with the aligned logger harmonics, and audio rpm vs logger rpm
    src, at = CLIP_SOURCE["03_hand_topspeed"]
    corr = corrections[src]
    f, t, D = spec[src]
    sel = (t >= at) & (t <= at + 36)
    tc = t[sel] - at
    Ds = D[:, sel]
    t_cam = t[sel] + STARTS[src]
    r_aligned = np.interp(t_cam - corr, L["t"], L["rpm"])
    r_raw = np.interp(t_cam, L["t"], L["rpm"])
    est = audio_rpm(f, Ds, r_aligned)
    err = np.nanmedian(np.abs(est - r_aligned))
    err_raw = np.nanmedian(np.abs(audio_rpm(f, Ds, r_raw) - r_raw))
    fig, ax = plt.subplots(3, 1, figsize=(13, 13), gridspec_kw={"height_ratios": [3, 2, 1.4]})
    ax[0].pcolormesh(tc, f, Ds, vmin=0, vmax=22, shading="auto", cmap="magma")
    for k in (1.5, 3, 4.5, 6):
        ax[0].plot(tc, r_aligned / 60 * k, "c--" if k in (3, 6) else "c:", lw=0.9)
    ax[0].set_ylim(0, 700)
    ax[0].set_ylabel("Hz")
    ax[0].set_title("03_hand_topspeed.mp4 audio (whitened log spectrum) with aligned logger rpm × orders 1.5, 3, 4.5, 6")
    ax[1].plot(tc, est, "k", lw=1, label=f"audio: harmonic-comb rpm (median error {err:.0f} rpm)")
    ax[1].plot(tc, r_aligned, "c", lw=2, label=f"logger rpm, aligned ({corr:+.2f} s for {src})")
    ax[1].plot(tc, r_raw, "r--", lw=1, label=f"logger rpm, sync.json + STARTS only (median error {err_raw:.0f} rpm)")
    ax[1].set_ylabel("rpm")
    ax[1].set_xlabel("clip time, s")
    ax[1].legend(loc="lower right", fontsize=8)
    for a in ax[:2]:
        a.set_xlim(0, 36)
    for name, (c, s) in scores.items():
        ax[2].plot(c, s - np.nanmedian(s), lw=0.8, label=f"{name}: {corrections[name]:+.2f} s")
    ax[2].set_xlabel("correction (logger time minus camera STARTS time), s")
    ax[2].set_ylabel("harmonic score, dB")
    ax[2].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "preview_alignment.png"), dpi=80)
    print(f"03_hand_topspeed: audio vs logger median |error| {err:.0f} rpm aligned, {err_raw:.0f} rpm unaligned")


if __name__ == "__main__":
    main()
