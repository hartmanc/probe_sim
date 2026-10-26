"""Build one AI engine family's sample set from online onboard recordings.

    P="uv run --python 3.12 --with numpy,scipy,soundfile,matplotlib python -I"
    $P tools/audio/families/build_family.py --family mazda_b_i4 [--force-track] [--bin-step 500]

Inputs: families.json (engine definition: cylinders, layout, fire, idle, top of the bin range) and sources.json
(per family: entries {url and/or file, t0, t1, title, licence, notes}). Media lives in cache/ (git-ignored,
untrusted data: only ffmpeg reads it).

Steps
  1. Audio: each entry's [t0, t1] as mono 48 kHz (downloaded with yt-dlp, audio only, if the file is missing).
  2. Unseeded rpm (track_unseeded.py): harmonic comb over the layout's order ladder + Viterbi; confidence; on/off
     label from rpm slope + loudness/tilt. Cached in cache/track_<family>_<k>.npz.
  3. Per 250 rpm bin and load: candidate runs (label, confidence, rpm near the bin), then the Probe pipeline's steps
     from ../loopkit.py: time-warp to constant rpm, spectral gating, 40 Hz high-pass, loop search over whole engine
     cycles, correlation-compensated crossfade; best candidate by contrast + seam correlation − tick.
  4. Levels as the Probe (off below on by the measured, clamped gap); missing bins pitch-shifted from the nearest
     real bin of the same load (or, if a load has no real bin at all, from the other load, darkened).
  5. Writes public/audio/families/<id>/engine_on.ogg, engine_off.ogg (Opus 48 kbps mono), engine.json (the Probe's
     format + family metadata), and
     tools/audio/families/previews/<id>.png.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from common import FFMPEG, ROOT, SR  # noqa: E402
from loopkit import (PAD, find_loop, highpass, make_loop, pitch_shift, rms_db, runs, spectral_gate,  # noqa: E402
                     transient_ratio, warp_flat)
import track_unseeded as tu  # noqa: E402

CACHE = os.path.join(HERE, "cache")
OUT_BASE = os.path.join(ROOT, "public", "audio", "families")
PREV = os.path.join(HERE, "previews")
TARGET_RMS_DB = -24.0
BUDGET_BYTES = 200_000
KBPS = 48


# ---------------------------------------------------------------- inputs

def load_defs(fam: str):
    defs = json.load(open(os.path.join(HERE, "families.json")))["families"][fam]
    src = json.load(open(os.path.join(HERE, "sources.json")))[fam]
    return defs, src


def entry_file(e: dict, fam: str, k: int) -> str:
    """Path of the entry's mono 48 kHz FLAC in cache/, downloading the audio track if it is missing."""
    if e.get("file"):
        p = e["file"] if os.path.isabs(e["file"]) else os.path.join(HERE, e["file"])
    else:
        slug = hashlib.sha1(e["url"].encode()).hexdigest()[:10]
        p = os.path.join(CACHE, f"{fam}__{slug}.flac")
    if os.path.exists(p):
        return p
    if not e.get("url"):
        raise FileNotFoundError(p)
    os.makedirs(CACHE, exist_ok=True)
    stem = os.path.splitext(p)[0] + ".dl"
    subprocess.run(["uvx", "yt-dlp", "--js-runtimes", "node", "-q", "--no-playlist", "-f", "bestaudio", "-o", stem + ".%(ext)s", e["url"]],
                   check=True, cwd=CACHE)
    got = [f for f in os.listdir(CACHE) if f.startswith(os.path.basename(stem) + ".")]
    subprocess.run([FFMPEG, "-v", "error", "-y", "-i", os.path.join(CACHE, got[0]), "-vn", "-ac", "1", "-ar",
                    str(SR), "-c:a", "flac", p], check=True)
    os.remove(os.path.join(CACHE, got[0]))
    return p


def read_span(path: str, t0: float, t1: float | None) -> np.ndarray:
    info = sf.info(path)
    assert info.samplerate == SR, path
    stop = None if t1 is None else int(round(t1 * SR))
    x, _ = sf.read(path, start=int(round(t0 * SR)), stop=stop, dtype="float32", always_2d=True)
    return x.mean(1)


OCTAVE_BOUNDS = {"track": (0.42, 0.92), "street": (0.25, 0.80)}


def octave_check(res: dict, defs: dict, e: dict) -> float:
    """Relabel a whole source by x2 / x0.5 when its median confident rpm is implausible for the footage
    (entry 'context': track = race/track day, most time in the upper half of the rev range; street = cruising).
    Open-header V8s carry every half order, and the comb alone cannot tell rpm from rpm/2 there."""
    lo, hi = OCTAVE_BOUNDS[e.get("context", "track")]
    if "octave" in e:
        f = float(e["octave"])
    else:
        good = res["conf"] > 2.0
        rr = res["rpm"][good] if good.sum() > 50 else res["rpm"]
        med, p90 = float(np.median(rr)), float(np.percentile(rr, 90))
        f = 1.0
        # x2 only when the doubled source still stays below the redline (a source that mixes octaves would push
        # its correct stretches far past it)
        while (med * f < lo * defs["redline_rpm"] and med * f * 2 <= hi * defs["redline_rpm"]
               and p90 * f * 2 <= 1.15 * defs["redline_rpm"]):
            f *= 2
        while med * f > hi * defs["redline_rpm"] and med * f / 2 >= lo * defs["redline_rpm"]:
            f /= 2
    if f != 1.0:
        res["rpm"] = (res["rpm"] * f).astype(np.float32)
        res["slope"] = (res["slope"] * f).astype(np.float32)
    return f


def tracks(fam: str, defs: dict, src: dict, force: bool):
    """Per entry: {'x': audio, 'res': tracker output, 'meta': entry}."""
    T = {}
    for k, e in enumerate(src["entries"]):
        if e.get("skip"):
            continue
        p = entry_file(e, fam, k)
        x = read_span(p, float(e.get("t0", 0.0)), e.get("t1"))
        key = hashlib.sha1(json.dumps([p, e.get("t0"), e.get("t1"), defs, 6]).encode()).hexdigest()[:10]
        cp = os.path.join(CACHE, f"track_{fam}_{k}_{key}.npz")
        if os.path.exists(cp) and not force:
            res = dict(np.load(cp))
        else:
            res = tu.track(x, defs["cylinders"], defs["fire"], defs["layout"],
                           rpm_max=min(tu.RPM_MAX, defs["redline_rpm"] * 1.15))
            np.savez_compressed(cp, **res)
        res["octave"] = octave_check(res, defs, e)
        res["label_name"] = f"src{k}"
        T[k] = {"x": x, "res": res, "meta": e, "t0": float(e.get("t0", 0.0))}
        r = res
        good = r["conf"] > 2.0
        print(f"  src{k}: {len(x) / SR:.0f} s, conf median {np.median(r['conf']):.1f} dB, "
              f"{100 * good.mean():.0f}% frames > 2 dB, rpm p5-p95 {np.percentile(r['rpm'][good], 5) if good.any() else 0:.0f}"
              f"-{np.percentile(r['rpm'][good], 95) if good.any() else 0:.0f}, on {100 * np.mean(r['load'] == 1):.0f}% "
              f"off {100 * np.mean(r['load'] == -1):.0f}%, octave x{r['octave']:g}  ({e.get('title', '')[:50]})")
    return T


# ---------------------------------------------------------------- candidates and processing

def candidates(T: dict, B: int, load: str, tol: float, min_s: float, conf_min: float):
    out = []
    want = 1 if load == "on" else -1
    for k, d in T.items():
        r = d["res"]
        ra = r["rpm"]
        lab = r["load"] == want
        if load == "off":  # overrun: clearly falling, not a clutch-in shift drop
            lab &= (r["slope"] < -150) & (r["slope"] > -3000)
        m = (np.abs(ra - B) <= tol) & lab & (r["conf"] >= conf_min) & (r["octave_margin"] > -0.5)
        # bridge 1-2 frame dropouts
        m = signal.medfilt(m.astype(np.float64), 5) > 0.5
        for s, e in runs(m):
            dur = (e - s) * tu.FRAME
            if dur < min_s:
                continue
            span = int(round(1.0 / tu.FRAME))
            best = None
            for a in range(s, max(s + 1, e - span + 1), 4):
                b = min(e, a + span)
                c = float(np.mean(r["conf"][a:b]))
                sd = float(np.std(ra[a:b] - np.polyval(np.polyfit(np.arange(b - a), ra[a:b], 1), np.arange(b - a)))) if b - a > 3 else 0.0
                score = c - sd / 40.0 + 1.5 * min((b - a) * tu.FRAME, 0.9) + 0.3 * float(np.mean(r["octave_margin"][a:b]))
                if best is None or score > best[0]:
                    best = (score, a, b)
            out.append((best[0], k, best[1], best[2]))
    out.sort(key=lambda z: -z[0])
    return out


def process(T: dict, cand, B: int, main_order: float, max_len: float):
    _, k, a, b = cand
    d = T[k]
    r = d["res"]
    t = r["t"]
    t0 = max(0.0, t[a] - 0.3)
    t1 = min(len(d["x"]) / SR, t[b - 1] + 0.3)
    x = d["x"][int(t0 * SR):int(t1 * SR)].astype(np.float64)
    fr = (t >= t0) & (t <= t1)
    y, wobble = warp_flat(x, t[fr] - t0, r["rpm"][fr], np.clip(r["conf"][fr], 0.1, None), B)
    y = highpass(spectral_gate(y, B, -10.0, order_step=min(1.0, main_order)))
    trim = int(0.2 * SR)
    if len(y) - 2 * trim > 2 * PAD + int(0.3 * SR):
        y = y[trim:len(y) - trim]
    a_, L, rho, n_cyc = find_loop(y, B, max_len_s=max_len, min_len_s=0.8 * max_len)
    loop = make_loop(y, a_, L, rho)
    return {"loop": loop, "rho": rho, "tick": transient_ratio(loop), "rpm": n_cyc * 120.0 * SR / L,
            "n_cycles": n_cyc, "wobble": wobble, "name": f"src{k}", "src": k,
            "t": float(d["t0"] + t[a]), "dur_src": float((b - a) * tu.FRAME),
            "contrast": float(np.mean(r["conf"][a:b])), "long": y, "raw": highpass(x)}


def order_ok(loop: np.ndarray, rpm: float, n_cyl: int) -> bool:
    """Octave guard: the loop's strongest engine order (0.5 steps up to 12, +-4 % windows) must sit on a whole multiple of
    the firing order F = cylinders / 2. A loop whose label is an octave too high peaks at F/2 or lower. Not used for V8s
    (a cross-plane V8's strongest order is the per-bank burble at 1 or 2, not the firing order)."""
    X = np.abs(np.fft.rfft(np.tile(loop, 4) * np.hanning(4 * len(loop)))) ** 2
    fr = np.fft.rfftfreq(4 * len(loop), 1 / SR)
    f_rev = rpm / 60.0
    orders = np.arange(0.5, 12.01, 0.5)
    pw = [X[np.abs(fr - o * f_rev) <= 0.04 * o * f_rev].sum() for o in orders]
    ratio = orders[int(np.argmax(pw))] / (n_cyl / 2.0)
    return ratio >= 0.99 and abs(ratio - round(ratio)) < 0.01


def darken(p: dict, fc: float = 1800.0) -> dict:
    q = dict(p)
    sos = signal.butter(2, fc, "lowpass", fs=SR, output="sos")
    q["long"] = signal.sosfiltfilt(sos, p["long"])
    q["loop"] = signal.sosfiltfilt(sos, np.tile(p["loop"], 3))[len(p["loop"]):2 * len(p["loop"])]
    return q


# ---------------------------------------------------------------- main build

def build(fam: str, force_track: bool = False, bin_step: int | None = None):
    defs, src = load_defs(fam)
    print(f"{fam}: {defs}")
    T = tracks(fam, defs, src, force_track)
    if not T:
        raise SystemExit("no usable source entries")
    main_order = float(next(iter(T.values()))["res"]["main_order"])
    lo = 750 if defs["idle_rpm"] < 700 else 1000
    hi = int(np.ceil(defs["redline_rpm"] / 250.0) * 250)
    step = bin_step or 250
    # loop length from the size budget: ~(budget − json) at KBPS split over both sprites
    sec_total = (BUDGET_BYTES - 12_000) * 8 / (KBPS * 1000) * 0.93
    nb = len(range(lo, hi + 1, step))
    max_len = sec_total / 2 / nb - 2 * PAD / SR - 0.4 / nb
    if max_len < 0.42 and bin_step is None:
        step = 500
        nb = len(range(lo, hi + 1, step))
        max_len = sec_total / 2 / nb - 2 * PAD / SR - 0.4 / nb
    max_len = float(min(1.0, max_len))
    BINS = list(range(lo, hi + 1, step))
    allconf = np.concatenate([d["res"]["conf"] for d in T.values()])
    conf_min = max(1.2, float(np.percentile(allconf, 35)))
    print(f"  bins {lo}..{hi} step {step} ({nb}), loop <= {max_len:.2f} s, conf_min {conf_min:.2f} dB")

    chosen = {"on": {}, "off": {}}
    for load in ("on", "off"):
        for B in BINS:
            tier = "steady"
            cs = candidates(T, B, load, 120, 0.45, conf_min)
            if not cs:
                tier = "sweep"
                cs = candidates(T, B, load, 0.09 * B + 80, 0.3, conf_min)
            if not cs:
                continue
            best = None
            for c in cs[:8]:
                try:
                    p = process(T, c, B, main_order, max_len)
                except Exception as ex:  # too short to loop etc.
                    print(f"    skip candidate {c}: {ex}")
                    continue
                if defs["cylinders"] != 8 and not order_ok(p["loop"], p["rpm"], defs["cylinders"]):
                    continue  # strongest order off the firing ladder: an octave-slipped label
                if p["tick"] > 8.0:  # a click / knock repeating once per loop: rather pitch-shift a neighbour
                    continue
                score = p["contrast"] + 4.0 * p["rho"] - 2.0 * max(0.0, p["tick"] - 2.5) - 60 * p["wobble"] * (tier == "steady")
                if best is None or score > best[0]:
                    best = (score, p)
            if best is None or best[1]["rho"] < 0.2:
                continue
            p = best[1]
            p["tier"], p["bin"] = tier, B
            chosen[load][B] = p
            print(f"  {load:3s} {B:5d} {tier:6s} {p['name']} t={p['t']:.2f} conf={p['contrast']:.1f} rho={p['rho']:.3f} "
                  f"tick={p['tick']:.1f} loop={len(p['loop']) / SR:.3f}s rpm_eff={p['rpm']:.1f}")

    if not chosen["on"] and not chosen["off"]:
        raise SystemExit("no bin found any candidate")
    # a load with no real bin at all borrows the other load (darkened for the overrun)
    borrowed = {}
    for load, other in (("on", "off"), ("off", "on")):
        if not chosen[load] and chosen[other]:
            borrowed[load] = other
            for B, p in chosen[other].items():
                q = darken(p) if load == "off" else dict(p)
                q["tier"] = f"from-{other}"
                chosen[load][B] = q
    on_db = {B: rms_db(p["loop"]) for B, p in chosen["on"].items()}
    off_db = {B: rms_db(p["loop"]) for B, p in chosen["off"].items()}
    both = sorted(set(on_db) & set(off_db))
    diffs = np.array([off_db[B] - on_db[B] for B in both]) if both else np.array([])
    # one constant gap: the recordings differ in gain and distance, so a slope over rpm fitted across them is noise
    gap = float(np.clip(np.median(diffs), -9.0, -4.0)) if (len(both) >= 3 and not borrowed) else -6.0
    fit = np.array([0.0, gap])
    print("  off-on level fit", fit)

    final = {"on": {}, "off": {}}
    for load in ("on", "off"):
        real = sorted(chosen[load])
        for B in BINS:
            if B in chosen[load]:
                final[load][B] = chosen[load][B]
                continue
            sb = min(real, key=lambda R: (abs(R - B), -R))
            s = dict(chosen[load][sb])
            s["bin"] = sb
            need = (max_len + 2 * PAD / SR + 0.25) * SR * (B / s["rpm"])
            if len(s["long"]) < need:  # a short segment shifted up: tile its (seamless) loop instead
                s["long"] = np.tile(s["loop"], int(np.ceil(need / len(s["loop"]))) + 1)
            p = pitch_shift(s, B, max_len_s=max_len)
            p["tier"], p["bin"] = "pitch-shifted", B
            final[load][B] = p
    return write_family(fam, defs, T, final, BINS, gap, main_order, borrowed)


def write_family(fam: str, defs: dict, T: dict, final: dict, BINS: list, gap: float, main_order: float,
                 borrowed: dict, sources: list | None = None, plot: bool = True):
    """Levels, the two Opus sprites, engine.json and the listening sweep, from the finished per-bin loops
    (final[load][bin] = {loop, tier, rpm, rho, tick, name, t, ...}). Shared with the synthesiser (synth_engine.py)."""
    real_bins = {load: sum(1 for B in BINS if final[load][B]["tier"] in ("steady", "sweep")) for load in final}
    print("  real bins", real_bins, "of", len(BINS), "borrowed", borrowed)

    out = os.path.join(OUT_BASE, fam)
    os.makedirs(out, exist_ok=True)
    os.makedirs(CACHE, exist_ok=True)
    index = {"sampleRate": SR, "format": f"ogg/opus {KBPS} kbps mono", "sprites": {"on": "engine_on.ogg",
             "off": "engine_off.ogg"}, "padding_s": PAD / SR,
             "levels": {"off_minus_on_db": round(gap, 2)}, "bins": []}
    entries = {B: {"rpm": B} for B in BINS}
    scaled = {"on": {}, "off": {}}
    for load in ("on", "off"):
        for B in BINS:
            lp = final[load][B]["loop"]
            target = TARGET_RMS_DB if load == "on" else TARGET_RMS_DB + gap
            scaled[load][B] = lp * 10 ** ((target - rms_db(lp)) / 20)
    peak = max(np.max(np.abs(v)) for dd in scaled.values() for v in dd.values())
    g = min(1.0, 0.9 / peak)
    index["levels"]["on_rms_dbA"] = round(TARGET_RMS_DB + 20 * np.log10(g), 2)
    for load in ("on", "off"):
        parts = [np.zeros(int(0.1 * SR))]
        pos = len(parts[0])
        for B in BINS:
            p = final[load][B]
            lp = scaled[load][B] * g
            parts.append(np.concatenate([lp[-PAD:], lp, lp[:PAD]]))
            if p["tier"] == "pitch-shifted":
                srcs = f"pitch-shifted from the {p['from_rpm']} rpm bin (x{p['ratio']:.3f}), {p['name']} @ {p['t']:.2f} s"
            else:
                srcs = f"{p['name']} @ {p['t']:.2f} s"
            entries[B][load] = {"offset": round((pos + PAD) / SR, 6), "duration": round(len(lp) / SR, 6),
                                "rpm": round(p["rpm"], 2), "tier": p["tier"], "source": srcs,
                                "seam_corr": round(p["rho"], 3), "tick": round(p["tick"], 2)}
            pos += len(lp) + 2 * PAD
            p["final"] = lp
        parts.append(np.zeros(int(0.1 * SR)))
        wav = os.path.join(CACHE, f"{fam}_engine_{load}.wav")
        sf.write(wav, np.concatenate(parts).astype(np.float32), SR, subtype="FLOAT")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", wav, "-c:a", "libopus", "-b:a", f"{KBPS}k", "-ar", "48000",
                        "-ac", "1", "-application", "audio", "-frame_duration", "20",
                        os.path.join(out, f"engine_{load}.ogg")], check=True)
    index["bins"] = [entries[B] for B in BINS]
    index["real_bins"] = real_bins
    index.update({"family": fam, "cylinders": defs["cylinders"], "layout": defs["layout"], "fire": defs["fire"],
                  "redline_rpm": defs["redline_rpm"], "idle_rpm": defs["idle_rpm"], "main_order": main_order,
                  "borrowed_load": borrowed or None,
                  "sources": sources if sources is not None else
                  [{"src": f"src{k}", "url": d["meta"].get("url"), "title": d["meta"].get("title"),
                    "channel": d["meta"].get("uploader"), "upload_date": d["meta"].get("upload_date"),
                    "licence": d["meta"].get("licence"), "t0": d["meta"].get("t0"),
                    "octave_relabel": float(d["res"]["octave"]),
                    "t1": d["meta"].get("t1")} for k, d in T.items()]})
    json.dump(index, open(os.path.join(out, "engine.json"), "w"), indent=1)
    sizes = {f: os.path.getsize(os.path.join(out, f)) for f in ("engine_on.ogg", "engine_off.ogg", "engine.json")}
    print("  sizes", sizes, "total", sum(sizes.values()))
    sweep = render_preview(out, index, defs)  # for listening checks: written to cache/, never shipped
    if plot:
        plot_preview(fam, T, final, BINS, index, sweep)
    return index


# ---------------------------------------------------------------- preview: a player emulation (like audio.ts)

def decode(path: str) -> np.ndarray:
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def sweep_profile(defs: dict, dur: float = 12.0):
    """rpm, throttle per sample: idle 0.8 s, pull to redline by 7.6 s (slower near the top), 0.6 s on the
    limiter, overrun back to idle."""
    t = np.arange(int(dur * SR)) / SR
    idle, red = defs["idle_rpm"], defs["redline_rpm"]
    rpm = np.empty_like(t)
    thr = np.zeros_like(t)
    a = t < 0.8
    rpm[a] = idle
    b = (t >= 0.8) & (t < 7.6)
    u = (t[b] - 0.8) / 6.8
    rpm[b] = idle + (red - 40 - idle) * (1 - (1 - u) ** 1.6)
    thr[b] = 1
    c = (t >= 7.6) & (t < 8.2)
    rpm[c] = red - 40 + 50 * (np.floor(t[c] * 30) % 2)
    thr[c] = 1
    d = t >= 8.2
    u = np.clip((t[d] - 8.2) / 3.2, 0, 1)
    rpm[d] = idle + (red - idle) * (1 - u) ** 1.5
    return t, rpm, thr


def render_preview(out: str, index: dict, defs: dict) -> np.ndarray:
    spr = {"on": decode(os.path.join(out, "engine_on.ogg")), "off": decode(os.path.join(out, "engine_off.ogg"))}
    bins = index["bins"]
    br = np.array([b["rpm"] for b in bins], float)
    t, rpm, thr = sweep_profile(defs)
    n = len(t)
    blk = 128
    y = np.zeros(n)
    phase = {}
    rng = np.random.default_rng(1)
    load = 0.0
    gains = {}
    for s0 in range(0, n, blk):
        s1 = min(n, s0 + blk)
        r = float(rpm[s0])
        tau = 0.035 if thr[s0] > load else 0.07
        load += (thr[s0] - load) * (1 - np.exp(-(s1 - s0) / SR / tau))
        w_on, w_off = np.sin(load * np.pi / 2), np.cos(load * np.pi / 2)
        if r <= br[0]:
            pairs = [(0, 1.0)]
        elif r >= br[-1]:
            pairs = [(len(br) - 1, 1.0)]
        else:
            i = int(np.searchsorted(br, r) - 1)
            u = (r - br[i]) / (br[i + 1] - br[i])
            pairs = [(i, np.cos(u * np.pi / 2)), (i + 1, np.sin(u * np.pi / 2))]
        want = {}
        for i, wb in pairs:
            want[(i, "on")] = wb * w_on
            want[(i, "off")] = wb * w_off
        for key in set(gains) | set(want):
            g0 = gains.get(key, 0.0)
            g1 = want.get(key, 0.0)
            g1 = g0 + (g1 - g0) * (1 - np.exp(-(s1 - s0) / SR / 0.012))
            gains[key] = g1
            if max(g0, g1) < 1e-4:
                continue
            i, ld = key
            ref = bins[i][ld]
            a = int(round(ref["offset"] * SR))
            L = int(round(ref["duration"] * SR))
            loop = spr[ld][a:a + L]
            rate = r / ref["rpm"]
            ph = phase.get(key, rng.uniform(0, L))
            pos = ph + rate * np.arange(s1 - s0)
            phase[key] = (ph + rate * (s1 - s0)) % L
            i0 = np.floor(pos).astype(int)
            fr = pos - i0
            v = loop[i0 % L] * (1 - fr) + loop[(i0 + 1) % L] * fr
            y[s0:s1] += v * np.linspace(g0, g1, s1 - s0)
    level = 0.95 * (0.5 + 0.5 * thr ** 0.8) * (0.8 + 0.2 * np.minimum(1.2, rpm / 6000))
    level = signal.lfilter([1 - np.exp(-1 / (0.02 * SR))], [1, -np.exp(-1 / (0.02 * SR))], level)
    lim = (rpm >= defs["redline_rpm"] - 60) & (thr > 0.5)
    gate = np.where(lim & (np.floor(t * 16 * 2) % 2 == 1), 0.15, 1.0)
    gate = signal.lfilter([1 - np.exp(-1 / (0.004 * SR))], [1, -np.exp(-1 / (0.004 * SR))], gate)
    y *= level * gate
    y *= 0.8 / (np.max(np.abs(y)) + 1e-9)
    wav = os.path.join(CACHE, "preview_tmp.wav")
    sf.write(wav, y.astype(np.float32), SR)
    # preview.mp3 is no longer shipped (26 Oct 2026): the sweep stays in cache/ (git-ignored) for the listen test
    pv = os.path.join(CACHE, "preview_" + os.path.basename(out) + ".wav")
    sf.write(pv, y.astype(np.float32), SR)
    return y


def plot_preview(fam: str, T: dict, final: dict, BINS: list, index: dict, sweep: np.ndarray):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    os.makedirs(PREV, exist_ok=True)
    nsrc = len(T)
    fig = plt.figure(figsize=(15, 3.0 * nsrc + 7))
    gs = fig.add_gridspec(nsrc + 2, 2)
    for row, (k, d) in enumerate(T.items()):
        ax = fig.add_subplot(gs[row, :])
        r = d["res"]
        tt = r["t"] + d["t0"]
        f, ts, S = signal.spectrogram(d["x"], SR, nperseg=8192, noverlap=8192 - 1200)
        fmax = 900
        kk = f <= fmax
        ax.pcolormesh(ts + d["t0"], f[kk] * 60 / r["main_order"] / 1, 10 * np.log10(S[kk] + 1e-14), shading="auto",
                      cmap="magma", vmin=10 * np.log10(S[kk].max()) - 60, vmax=10 * np.log10(S[kk].max()))
        good = r["conf"] > 2.0
        col = np.where(r["load"] == 1, "lime", np.where(r["load"] == -1, "deepskyblue", "w"))
        ax.scatter(tt[good], r["rpm"][good], c=col[good], s=0.6)
        ax.scatter(tt[~good], r["rpm"][~good], c="0.5", s=0.3)
        for load, c in (("on", "red"), ("off", "cyan")):
            for B in BINS:
                p = final[load][B]
                if p["tier"] in ("steady", "sweep") and p.get("src") == k:
                    ax.plot([p["t"], p["t"] + p["dur_src"]], [B, B], color=c, lw=3)
        ax.set_ylim(0, index["redline_rpm"] * 1.15)
        ax.set_ylabel(f"rpm (spectrogram y = Hz × 60 / {r['main_order']:g})")
        ax.set_title(f"src{k}: {d['meta'].get('title', '')[:90]} — tracked rpm (green on / blue off / white unknown, "
                     f"grey = conf < 2 dB); chosen loops red (on) / cyan (off)", fontsize=9)
    ax = fig.add_subplot(gs[nsrc, 0])
    for load, m in (("on", "o"), ("off", "s")):
        tiers = [final[load][B]["tier"] for B in BINS]
        cols = ["C2" if x == "steady" else "C1" if x == "sweep" else "C3" if x == "pitch-shifted" else "C7" for x in tiers]
        ax.scatter(BINS, [final[load][B]["rho"] for B in BINS], c=cols, marker=m, label=load)
    ax.set_xlabel("bin rpm"); ax.set_ylabel("seam corr")
    ax.set_title("loops: green steady, orange sweep, red pitch-shifted, grey borrowed; o on, s off", fontsize=9)
    ax = fig.add_subplot(gs[nsrc, 1])
    for B in BINS[:: max(1, len(BINS) // 5)]:
        lp = final["on"][B]["final"]
        sp = np.abs(np.fft.rfft(np.tile(lp, 2) * np.hanning(2 * len(lp))))
        fr = np.fft.rfftfreq(2 * len(lp), 1 / SR)
        orders = fr / (B / 60)
        ax.plot(orders, 20 * np.log10(sp / sp.max() + 1e-6), lw=0.7, label=f"{B}")
    ax.set_xlim(0, 16); ax.set_ylim(-70, 2); ax.set_xlabel("engine order"); ax.legend(fontsize=7)
    ax.set_title("on-throttle loop spectra vs engine order", fontsize=9)
    ax = fig.add_subplot(gs[nsrc + 1, :])
    f, ts, S = signal.spectrogram(sweep, SR, nperseg=4096, noverlap=4096 - 512)
    kk = f < 1500
    ax.pcolormesh(ts, f[kk], 10 * np.log10(S[kk] + 1e-14), shading="auto", cmap="magma",
                  vmin=10 * np.log10(S[kk].max()) - 60)
    ax.set_title("preview.mp3: 12 s sweep (idle → redline on throttle, limiter, overrun)", fontsize=9)
    ax.set_ylabel("Hz")
    fig.tight_layout()
    fig.savefig(os.path.join(PREV, f"{fam}.png"), dpi=60)
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True)
    ap.add_argument("--force-track", action="store_true")
    ap.add_argument("--bin-step", type=int, default=None)
    a = ap.parse_args()
    build(a.family, a.force_track, a.bin_step)
