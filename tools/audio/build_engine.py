"""Build the sample-based engine from the race footage.

    uv run --python 3.12 --with numpy,scipy,soundfile,matplotlib python tools/audio/build_engine.py

Needs alignment.json (align.py) and the per-frame rpm tracks (track_rpm.py, cached; built on demand).
Writes public/audio/engine_on.ogg, engine_off.ogg (Opus, 48 kHz mono, 64 kbps), public/audio/engine.json and
tools/audio/preview_engine.png.

For every rpm bin (1000..6500 step 250) and load (on: throttle >= 80 at both bracketing OBD reads, off: <= 10):
  1. candidates = runs where the audio rpm stays within +/-120 of the bin for >= 0.65 s (tier "steady"); if there is
     none, runs within +/-300 for >= 0.5 s (tier "sweep", flattened by step 2); the audio rpm must agree with the
     logger within 300 rpm.
  2. each candidate is time-warped onto a constant-rpm phase grid (rpm track: cubic fit to the 25 ms comb
     estimates), so the harmonics sit still; then spectral gating against the inter-harmonic floor (max -10 dB),
     40 Hz high-pass, loop search (start and length near a whole number of engine cycles, picked by the
     correlation across the seam), correlation-compensated equal-power crossfade.
  3. score = harmonic contrast + seam correlation - speech/radio and rumble penalties; best wins.
Bins with no candidate are pitch-shifted (resampled) from the nearest real bin of the same load.
Levels: every on loop at the same RMS; off loops at the on level plus the measured off-on difference (linear fit
over rpm, clamped to -16..-4 dB).
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
from scipy import signal

from common import FFMPEG, HERE, ROOT, SR, STARTS, load_audio
from loopkit import (A_SOS, PAD, XFADE, find_loop, highpass, make_loop, pitch_shift, rms_db, runs, sinc_interp,
                     spectral_gate, transient_ratio, warp_flat)
from track_rpm import track

OUT = os.path.join(ROOT, "public", "audio")
BINS = list(range(1000, 6501, 250))
FRAME = 0.025  # track_rpm hop
TARGET_RMS_DB = -24.0  # A-weighted


# ---------------------------------------------------------------- candidate search


def candidates(T: dict, B: int, load: str, tol: float, min_s: float, speech_thr: float, lf_med: float):
    out = []
    for name, r in T.items():
        lm = (r["thr_lo"] >= 80) if load == "on" else (r["thr_hi"] <= 10)
        ra = r["rpm_a"]
        m = (np.abs(ra - B) <= tol) & (np.abs(ra - r["rpm_l"]) <= 300) & lm & np.isfinite(r["contrast"])
        for s, e in runs(m):
            dur = (e - s) * FRAME
            if dur < min_s:
                continue
            # long runs: score sliding 1.2 s windows, keep the best
            span = int(round(1.2 / FRAME))
            best = None
            for a in range(s, max(s + 1, e - span + 1), 4):
                b = min(e, a + span)
                c = float(np.nanmean(r["contrast"][a:b]))
                sp = float(np.nanmax(r["hf_mod"][a:b]))
                lf = float(np.nanmean(r["lf"][a:b]))
                sd = float(np.nanstd(ra[a:b]))
                score = (c - 2.0 * max(0.0, sp - speech_thr) - 0.15 * max(0.0, lf - lf_med) - sd / 60.0
                         + 1.5 * min((b - a) * FRAME, 1.1))
                if best is None or score > best[0]:
                    best = (score, a, b)
            out.append((best[0], name, best[1], best[2]))
    out.sort(key=lambda z: -z[0])
    return out


# ---------------------------------------------------------------- DSP: shared with families/build_family.py (loopkit.py)


# ---------------------------------------------------------------- per-candidate processing


def process(T: dict, cand, B: int):
    _, name, a, b = cand
    r = T[name]
    t0 = r["t"][a] - 0.35
    t1 = r["t"][b - 1] + 0.35
    x = load_audio(name, t0, t1 - t0)
    fr = (r["t"] >= t0) & (r["t"] <= t1)
    y, wobble = warp_flat(x, r["t"][fr] - t0, r["rpm_a"][fr], r["contrast"][fr], B)
    raw_flat = y.copy()
    y = highpass(spectral_gate(y, B))
    # trim the 0.25 s processing margins (keep PAD for the sprite pads)
    trim = int(0.25 * SR)
    y = y[trim:len(y) - trim]
    raw_flat = raw_flat[trim:len(raw_flat) - trim]
    a_, L, rho, n_cyc = find_loop(y, B)
    loop = make_loop(y, a_, L, rho)
    rpm_eff = n_cyc * 120.0 * SR / L
    return {"loop": loop, "rho": rho, "tick": transient_ratio(loop), "rpm": rpm_eff, "n_cycles": n_cyc, "wobble": wobble, "name": name,
            "t": float(r["t"][a]), "dur_src": float((b - a) * FRAME), "contrast": float(np.nanmean(r["contrast"][a:b])),
            "long": y, "raw": highpass(x), "raw_flat": raw_flat}


# ---------------------------------------------------------------- main


def main():
    T = {n: track(n) for n in STARTS}
    allmod = np.concatenate([r["hf_mod"] for r in T.values()])
    speech_thr = float(np.nanpercentile(allmod, 95))
    lf_med = float(np.nanmedian(np.concatenate([r["lf"] for r in T.values()])))
    chosen = {"on": {}, "off": {}}
    for load in ("on", "off"):
        for B in BINS:
            tier = "steady"
            cs = candidates(T, B, load, 120, 0.65, speech_thr, lf_med)
            if not cs:
                tier = "sweep"
                cs = [c for c in candidates(T, B, load, 300, 0.5, speech_thr, lf_med) if c[0] > 7.0]
            if not cs:
                continue
            best = None
            for c in cs[:10]:
                p = process(T, c, B)
                score = (p["contrast"] + 4.0 * p["rho"] - 200 * p["wobble"] * (tier == "steady")
                         - 2.0 * max(0.0, p["tick"] - 2.5))
                if best is None or score > best[0]:
                    best = (score, p)
            p = best[1]
            p["tier"], p["bin"] = tier, B
            chosen[load][B] = p
            print(f"{load:3s} {B:5d} {tier:6s} {p['name']} t={p['t']:.2f} contrast={p['contrast']:.1f} "
                  f"rho={p['rho']:.3f} tick={p['tick']:.1f} loop={len(p['loop']) / SR:.3f}s rpm_eff={p['rpm']:.1f}")

    # levels: measured off - on difference on bins where both are real
    on_db = {B: rms_db(p["loop"]) for B, p in chosen["on"].items()}
    off_db = {B: rms_db(p["loop"]) for B, p in chosen["off"].items()}
    both = sorted(set(on_db) & set(off_db))
    diffs = np.array([off_db[B] - on_db[B] for B in both])
    fit = np.polyfit(both, diffs, 1) if len(both) >= 3 else np.array([0.0, -8.0])
    print("off-on level differences (dB):", dict(zip(both, np.round(diffs, 1))), "fit", fit)

    # fill missing bins
    final = {"on": {}, "off": {}}
    for load in ("on", "off"):
        real = sorted(chosen[load])
        for B in BINS:
            if B in chosen[load]:
                final[load][B] = chosen[load][B]
            else:
                src = chosen[load][min(real, key=lambda R: (abs(R - B), -R))]
                p = pitch_shift(src, B)
                p["tier"], p["bin"] = "pitch-shifted", B
                final[load][B] = p
                print(f"{load:3s} {B:5d} pitch-shifted from {src['bin']} (x{p['ratio']:.3f}) rho={p['rho']:.3f}")

    # normalise and write sprites
    os.makedirs(OUT, exist_ok=True)
    index = {"sampleRate": SR, "format": "ogg/opus 64 kbps mono", "sprites": {"on": "engine_on.ogg",
             "off": "engine_off.ogg"}, "padding_s": PAD / SR,
             "levels": {"off_minus_on_db": "clamp(%.5f*rpm %+.2f, -16, -4)" % tuple(fit)},
             "bins": []}
    entries = {B: {"rpm": B} for B in BINS}
    scaled = {"on": {}, "off": {}}
    for load in ("on", "off"):
        for B in BINS:
            lp = final[load][B]["loop"]
            target = TARGET_RMS_DB if load == "on" else TARGET_RMS_DB + float(np.clip(np.polyval(fit, B), -16, -4))
            scaled[load][B] = lp * 10 ** ((target - rms_db(lp)) / 20)
    peak = max(np.max(np.abs(v)) for d in scaled.values() for v in d.values())
    g = min(1.0, 0.9 / peak)  # one common factor, so the on/off and bin-to-bin levels are kept
    index["levels"]["on_rms_dbA"] = round(TARGET_RMS_DB + 20 * np.log10(g), 2)
    for load in ("on", "off"):
        parts = [np.zeros(int(0.1 * SR))]
        pos = len(parts[0])
        for B in BINS:
            p = final[load][B]
            lp = scaled[load][B] * g
            tiled = np.concatenate([lp[-PAD:], lp, lp[:PAD]])
            parts.append(tiled)
            src = (f"{p['name']} @ {p['t']:.2f} s" if p["tier"] != "pitch-shifted"
                   else f"pitch-shifted from the {p['from_rpm']} rpm bin (x{p['ratio']:.3f}), {p['name']} @ {p['t']:.2f} s")
            entries[B][load] = {"offset": round((pos + PAD) / SR, 6), "duration": round(len(lp) / SR, 6),
                                "rpm": round(p["rpm"], 2), "tier": p["tier"], "source": src,
                                "seam_corr": round(p["rho"], 3), "tick": round(p["tick"], 2)}
            pos += len(tiled)
            p["final"] = lp
        parts.append(np.zeros(int(0.1 * SR)))
        sprite = np.concatenate(parts)
        wav = os.path.join(HERE, "cache", f"engine_{load}.wav")
        sf.write(wav, sprite.astype(np.float32), SR, subtype="FLOAT")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", wav, "-c:a", "libopus", "-b:a", "64k", "-ar", "48000",
                        "-ac", "1", "-application", "audio", "-frame_duration", "20",
                        os.path.join(OUT, f"engine_{load}.ogg")], check=True)
    index["bins"] = [entries[B] for B in BINS]
    index["real_bins"] = {load: sum(1 for B in BINS if final[load][B]["tier"] != "pitch-shifted") for load in final}
    json.dump(index, open(os.path.join(OUT, "engine.json"), "w"), indent=1)
    sizes = {f: os.path.getsize(os.path.join(OUT, f)) for f in ("engine_on.ogg", "engine_off.ogg", "engine.json")}
    print("sizes", sizes, "total", sum(sizes.values()))
    preview(final)


def preview(final):
    """Spectrograms: raw footage window vs the shipped loop (tiled 3x), for a few bins."""
    show = [("on", 2000), ("on", 3500), ("on", 5000), ("off", 3000), ("on", 6250)]
    fig, ax = plt.subplots(len(show), 2, figsize=(14, 3.2 * len(show)))
    for i, (load, B) in enumerate(show):
        p = final[load][B]
        lp = p["final"]
        tiled = np.tile(lp, 3)[: int(2.4 * SR)]
        raw = p.get("raw")
        if raw is None:  # pitch-shifted: show its source footage
            raw = final[load][p["from_rpm"]]["raw"]
        for j, (sig, title) in enumerate(((raw, f"footage {p['name']} @ {p['t']:.1f} s (unprocessed)"),
                                          (tiled, f"{load} {B} rpm loop x3 ({p['tier']}), seams at "
                                                  f"{len(lp) / SR:.2f} s"))):
            f, t, S = signal.spectrogram(sig, SR, nperseg=4096, noverlap=4096 - 512)
            a = ax[i, j]
            a.pcolormesh(t, f, 10 * np.log10(S + 1e-14), shading="auto", cmap="magma",
                         vmin=10 * np.log10(S.max()) - 70, vmax=10 * np.log10(S.max()))
            a.set_ylim(0, 1200)
            for k in range(1, 20):
                fk = B / 60 * 1.5 * k
                if fk < 1200:
                    a.plot([t[-1] * 1.005, t[-1] * 1.04], [fk, fk], color="c" if k % 2 == 0 else "0.45", lw=1.2,
                           clip_on=False)
            a.set_title(title, fontsize=9)
            if j == 1:
                for s in (1, 2):
                    a.axvline(s * len(lp) / SR, color="w", lw=0.6, ls="--")
    for a in ax[-1]:
        a.set_xlabel("s  (ticks right of each panel: firing orders 1.5, 4.5, 7.5 grey; 3, 6, 9 cyan, of the bin rpm)")
    for a in ax[:, 0]:
        a.set_ylabel("Hz", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "preview_engine.png"), dpi=70)


if __name__ == "__main__":
    main()
