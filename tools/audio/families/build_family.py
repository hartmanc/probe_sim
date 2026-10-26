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
from scipy import ndimage, signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from common import FFMPEG, ROOT, SR  # noqa: E402
from loopkit import (PAD, XFADE, find_loop, highpass, make_loop, pitch_shift, rms_db, runs, spectral_gate,  # noqa: E402
                     transient_ratio, warp_flat)
import speechcheck as sc  # noqa: E402
import track_unseeded as tu  # noqa: E402

CACHE = os.path.join(HERE, "cache")
OUT_BASE = os.path.join(ROOT, "public", "audio", "families")
PREV = os.path.join(HERE, "previews")
TARGET_RMS_DB = -24.0
KBPS = 48
# round two (26 Oct 2026): the quality gates (quality.py GATES) are build rules. Loops at least LOOP_MIN_S and
# LOOP_CYCLES engine cycles long (the old 200 KB budget gave 0.4-0.6 s loops that repeat audibly), every bin either
# real or pitch-shifted within the on / off ratio window of a real recording, a real idle bin, no speech.
LOOP_MIN_S, LOOP_CYCLES, LOOP_MAX_S = 1.0, 8, 1.5
RATIO = {"on": (0.88, 1.14), "off": (0.85, 1.18)}
REAL_TIERS = ("steady", "sweep", "idle")


def loop_need(B: float) -> float:
    """Shortest loop allowed at bin rpm B, s: 1.0 s and at least 8 engine cycles (2 revs each)."""
    return max(LOOP_MIN_S, LOOP_CYCLES * 120.0 / B)


def loop_target(B: float) -> float:
    """Longest loop searched at bin rpm B: the need plus a little over one engine cycle (find_loop takes whole cycles),
    capped at LOOP_MAX_S above 1000 rpm."""
    return max(min(LOOP_MAX_S, loop_need(B) + 0.15), loop_need(B) + 1.05 * 120.0 / B)


def bin_grid(idle: int, redline: int) -> list:
    """The idle bin, then multiples of 125 rpm up to 1000 (no two bins more than x1.25 apart at the bottom), then
    250 rpm steps to the first bin at or above the redline."""
    idle = int(idle)
    bins = [idle]
    b = (idle // 125 + 1) * 125
    while b < 1000:
        if b > idle + 60:
            bins.append(b)
        b += 125
    hi = int(np.ceil(redline / 250.0) * 250)
    bins += [x for x in range(1000, hi + 1, 250) if x > idle + 60]
    return bins


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


def speech_map(x: np.ndarray, cp: str) -> np.ndarray:
    """Silero speech probability per 32 ms of the whole source (16 kHz), cached; candidates that overlap speech are
    never cut (round two: the 'weird speech' in modern_i4_stock was a narrated stretch)."""
    if os.path.exists(cp):
        return np.load(cp)["p"]
    from speechcheck import silero_probs
    x16 = signal.resample_poly(x.astype(np.float64), 1, 3)
    g = 10 ** (-20 / 20) / (np.sqrt(np.mean(x16 ** 2)) + 1e-12)
    p = silero_probs(x16 * g).astype(np.float32)
    np.savez_compressed(cp, p=p)
    return p


def track_speed(defs: dict) -> int:
    """V8s are tracked on the audio played at double speed (round two): their half-order ladder at 650-2000 rpm is
    5-17 Hz apart, inside the tracker's 170 ms window resolution, so the comb contrast stayed near 0 dB on every old-V8
    source; at x2 the same window spans 340 ms of the engine and the median contrast rises from ~0.1 to 1-2.4 dB
    (idle, dyno and autocross clips), with the idle read where the cycle autocorrelation puts it."""
    return 2 if defs["cylinders"] == 8 else 1


def run_track(x: np.ndarray, defs: dict, rpm_max: float, rpm_min: float) -> dict:
    k = track_speed(defs)
    xs = signal.resample_poly(x.astype(np.float64), 1, k) if k > 1 else x
    r = tu.track(xs, defs["cylinders"], defs["fire"], defs["layout"], rpm_max=rpm_max * k, rpm_min=rpm_min * k)
    if k > 1:
        r["rpm"] = (r["rpm"] / k).astype(np.float32)
        r["t"] = r["t"] * k
        r["slope"] = (r["slope"] / (k * k)).astype(np.float32)
    return r


def frame_s(r: dict) -> float:
    return float(r["t"][1] - r["t"][0]) if len(r["t"]) > 1 else tu.FRAME


def idle_track(x: np.ndarray, defs: dict, res: dict, cp: str):
    """Idle stretches. The full-range tracker reads a quiet idle an octave up (the I4's order 2 at 750 rpm is 25 Hz, the
    bottom of the comb band), so idle gets its own track over 0.6-1.6 x the family idle. A frame is idle when that
    track is confident and steady, off the search edges, and the source is quiet there (bottom 40 % of its frame
    levels): a car standing still, engine running. Returns a tracker-like dict or None."""
    idle = defs["idle_rpm"]
    if os.path.exists(cp):
        ri = dict(np.load(cp))
    else:
        ri = run_track(x, defs, 1.6 * idle, 0.6 * idle)
        ri = {k: ri[k] for k in ("t", "rpm", "conf", "slope", "octave_margin")}
        np.savez_compressed(cp, **ri)
    t = ri["t"]
    n = min(len(t), len(res["t"]))
    fl = int(0.05 * SR)
    lev = np.array([np.sqrt(np.mean(x[max(0, int(tt * SR) - fl // 2):int(tt * SR) + fl // 2] ** 2) + 1e-12) for tt in t[:n]])
    quiet = 20 * np.log10(lev) <= np.percentile(20 * np.log10(lev), 50)
    # (the full track is no check here: it reads a quiet idle at 2-6x)
    inside = (ri["rpm"][:n] > 0.62 * idle) & (ri["rpm"][:n] < 1.55 * idle)  # not pinned to the search edge
    ok = (ri["conf"][:n] >= 1.5) & (np.abs(ri["slope"][:n]) < 120) & inside & quiet & ~res["speech"][:n]
    ok = signal.medfilt(ok.astype(np.float64), 7) > 0.5
    if ok.sum() < int(1.2 / frame_s(ri)):
        return None
    return {"t": t[:n], "rpm": ri["rpm"][:n], "conf": ri["conf"][:n], "slope": ri["slope"][:n],
            "octave_margin": np.full(n, 1.0, np.float32), "load": np.zeros(n, np.int8), "speech": ~ok,
            "main_order": res["main_order"], "octave": 1.0, "label_name": res["label_name"] + "-idle"}


def tracks(fam: str, defs: dict, src: dict, force: bool):
    """Per entry: {'x': audio, 'res': tracker output, 'meta': entry}."""
    T = {}
    rpm_min = min(tu.RPM_MIN, 0.8 * defs["idle_rpm"])
    for k, e in enumerate(src["entries"]):
        if e.get("skip"):
            continue
        p = entry_file(e, fam, k)
        x = read_span(p, float(e.get("t0", 0.0)), e.get("t1"))
        key = hashlib.sha1(json.dumps([os.path.basename(p), e.get("t0"), e.get("t1"), defs, 7, rpm_min, track_speed(defs)]).encode()).hexdigest()[:10]
        cp = os.path.join(CACHE, f"track_{fam}_{k}_{key}.npz")
        if os.path.exists(cp) and not force:
            res = dict(np.load(cp))
        else:
            res = run_track(x, defs, min(tu.RPM_MAX, defs["redline_rpm"] * 1.15), rpm_min)
            np.savez_compressed(cp, **res)
        sp = speech_map(x, os.path.join(CACHE, f"speech_{fam}_{k}_{key}.npz"))
        # per tracker frame: speech within +-0.3 s
        tf = res["t"]
        ps = np.interp(tf, (np.arange(len(sp)) + 0.5) * 0.032, sp) if len(sp) else np.zeros(len(tf))
        sm = ps > 0.5
        sm = ndimage.binary_dilation(sm, iterations=int(round(0.3 / frame_s(res)))) if sm.any() else sm
        res["speech"] = sm
        res["octave"] = octave_check(res, defs, e)
        res["label_name"] = f"src{k}"
        T[k] = {"x": x, "res": res, "meta": e, "t0": float(e.get("t0", 0.0))}
        ri = idle_track(x, defs, res, os.path.join(CACHE, f"idle2_{fam}_{k}_{key}.npz"))
        if ri is not None:
            T[f"{k}i"] = {"x": x, "res": ri, "meta": e, "t0": float(e.get("t0", 0.0)), "idle_only": True, "of": k}
        r = res
        good = r["conf"] > 2.0
        print(f"  src{k}: {len(x) / SR:.0f} s, conf median {np.median(r['conf']):.1f} dB, "
              f"{100 * good.mean():.0f}% frames > 2 dB, rpm p5-p95 {np.percentile(r['rpm'][good], 5) if good.any() else 0:.0f}"
              f"-{np.percentile(r['rpm'][good], 95) if good.any() else 0:.0f}, on {100 * np.mean(r['load'] == 1):.0f}% "
              f"off {100 * np.mean(r['load'] == -1):.0f}%, octave x{r['octave']:g}, speech {100 * np.mean(r['speech']):.0f}%  ({e.get('title', '')[:50]})")
    return T


# ---------------------------------------------------------------- candidates and processing

def candidates(T: dict, B: int, load: str, tol: float, min_s: float, conf_min: float, span_s: float = 1.0):
    """load 'on' / 'off' / 'idle' (idle: steady near B, any label, |slope| < 150 rpm/s)."""
    out = []
    want = {"on": 1, "off": -1}.get(load, 0)
    for k, d in T.items():
        if bool(d.get("idle_only")) != (load == "idle"):
            continue
        r = d["res"]
        ra = r["rpm"]
        if load == "idle":
            lab = np.abs(r["slope"]) < 100
        else:
            lab = r["load"] == want
        if load == "off":  # overrun: clearly falling, not a clutch-in shift drop
            lab &= (r["slope"] < -150) & (r["slope"] > -3000)
        m = (np.abs(ra - B) <= tol) & lab & (r["conf"] >= conf_min) & (r["octave_margin"] > -0.5)
        # bridge 1-2 frame dropouts
        m = signal.medfilt(m.astype(np.float64), 5) > 0.5
        m &= ~r["speech"]
        for s, e in runs(m):
            FR = frame_s(r)
            dur = (e - s) * FR
            if dur < min_s:
                continue
            span = int(round(span_s / FR))
            best = None
            for a in range(s, max(s + 1, e - span + 1), 4):
                b = min(e, a + span)
                c = float(np.mean(r["conf"][a:b]))
                sd = float(np.std(ra[a:b] - np.polyval(np.polyfit(np.arange(b - a), ra[a:b], 1), np.arange(b - a)))) if b - a > 3 else 0.0
                score = c - sd / 40.0 + 1.5 * min((b - a) * FR, 0.9) + 0.3 * float(np.mean(r["octave_margin"][a:b]))
                if best is None or score > best[0]:
                    best = (score, a, b)
            out.append((best[0], k, best[1], best[2]))
    out.sort(key=lambda z: -z[0])
    return out


def process(T: dict, cand, B: int, main_order: float, max_len: float, min_len: float | None = None):
    _, k, a, b = cand
    d = T[k]
    r = d["res"]
    t = r["t"]
    t0 = max(0.0, t[a] - 0.25)
    t1 = min(len(d["x"]) / SR, t[b - 1] + 0.25)
    x = d["x"][int(t0 * SR):int(t1 * SR)].astype(np.float64)
    fr = (t >= t0) & (t <= t1)
    y, wobble = warp_flat(x, t[fr] - t0, r["rpm"][fr], np.clip(r["conf"][fr], 0.1, None), B)
    y = highpass(spectral_gate(y, B, -10.0, order_step=min(1.0, main_order)))
    trim = int(0.2 * SR)
    if len(y) - 2 * trim > 2 * PAD + XFADE + int((min_len or 0.3) * SR):
        y = y[trim:len(y) - trim]
    a_, L, rho, n_cyc = find_loop(y, B, max_len_s=max_len, min_len_s=min_len or 0.8 * max_len)
    if min_len and L < min_len * SR * 0.995:
        raise ValueError(f"loop {L / SR:.2f} s < {min_len:.2f} s")
    loop = make_loop(y, a_, L, rho)
    return {"loop": loop, "rho": rho, "tick": transient_ratio(loop), "rpm": n_cyc * 120.0 * SR / L,
            "n_cycles": n_cyc, "wobble": wobble, "name": f"src{d.get('of', k)}", "src": d.get("of", k),
            "t": float(d["t0"] + t[a]), "dur_src": float((b - a) * frame_s(r)),
            "contrast": float(np.mean(r["conf"][a:b])), "long": y, "raw": highpass(x)}


def order_ok(loop: np.ndarray, rpm: float, n_cyl: int) -> bool:
    """Octave guard: the loop's strongest engine order (0.5 steps up to 12, +-4 % windows) must sit on a whole multiple of
    the firing order F = cylinders / 2. A loop whose label is an octave too high peaks at F/2 or lower. For V8s only a
    half order is rejected (a cross-plane V8's strongest order may be the per-bank burble at 1 or 2, not the firing order)."""
    X = np.abs(np.fft.rfft(np.tile(loop, 4) * np.hanning(4 * len(loop)))) ** 2
    fr = np.fft.rfftfreq(4 * len(loop), 1 / SR)
    f_rev = rpm / 60.0
    orders = np.arange(0.5, 12.01, 0.5)
    pw = [X[np.abs(fr - o * f_rev) <= 0.04 * o * f_rev].sum() for o in orders]
    top = orders[int(np.argmax(pw))]
    if n_cyl == 8:  # cross-plane V8: the burble orders 1, 2 or the firing order 4 may lead; only a half order is wrong
        return top >= 1.0
    ratio = top / (n_cyl / 2.0)
    return ratio >= 0.99 and abs(ratio - round(ratio)) < 0.01


def darken(p: dict, fc: float = 1800.0) -> dict:
    q = dict(p)
    sos = signal.butter(2, fc, "lowpass", fs=SR, output="sos")
    q["long"] = signal.sosfiltfilt(sos, p["long"])
    q["loop"] = signal.sosfiltfilt(sos, np.tile(p["loop"], 3))[len(p["loop"]):2 * len(p["loop"])]
    return q


# ---------------------------------------------------------------- main build

def chain_loop(ys: list, B: float, need: float):
    """A loop of 2 or 3 real segments at the same rpm: [A | B (| C)], each a whole number of engine cycles; each
    segment's head is crossfaded with what follows the previous segment's tail in its own recording (the same
    power-preserving crossfade as make_loop), the start points chosen to maximise the weakest join correlation. The
    repeat is need s or longer although no single recording holds a steady need s. Returns (loop, rho_min) or None."""
    n = len(ys)
    m = SR * 120.0 / B
    ncyc = [int(np.ceil(need * SR / n / m))] * n
    Ls = [int(round(c * m)) for c in ncyc]
    band = lambda y: signal.sosfiltfilt(signal.butter(2, [60, 3000], "bandpass", fs=SR, output="sos"), y)
    bs = [band(y) for y in ys]
    step = int((0.004 if n == 2 else 0.008) * SR)
    starts = [np.arange(PAD, len(y) - L - XFADE - PAD, step) for y, L in zip(ys, Ls)]
    if any(len(st) < 1 for st in starts):
        return None

    def win(b, st):
        W = np.stack([b[s0:s0 + XFADE] for s0 in st])
        return W / (np.linalg.norm(W, axis=1, keepdims=True) + 1e-12)
    heads = [win(b, st) for b, st in zip(bs, starts)]
    tails = [win(b, st + L) for b, st, L in zip(bs, starts, Ls)]
    # J[i]: head of segment (i+1) % n against the tail of segment i, shape [starts_i, starts_{i+1}]
    J = [tails[i] @ heads[(i + 1) % n].T for i in range(n)]
    if n == 2:
        sc_ = np.minimum(J[0], J[1].T)
        i0, i1 = np.unravel_index(int(np.argmax(sc_)), sc_.shape)
        idx = [int(i0), int(i1)]
        rho = float(sc_[i0, i1])
    else:
        best = (-2.0, None)
        for i1 in range(len(starts[1])):
            sc_ = np.minimum(np.minimum(J[0][:, i1][:, None], J[1][i1, :][None, :]), J[2].T)
            k = int(np.argmax(sc_))
            if sc_.flat[k] > best[0]:
                i0, i2 = np.unravel_index(k, sc_.shape)
                best = (float(sc_.flat[k]), [int(i0), i1, int(i2)])
        rho, idx = best
    st = [int(starts[i][idx[i]]) for i in range(n)]
    segs = [ys[i][st[i]:st[i] + Ls[i]].copy() for i in range(n)]
    gs = [np.sqrt(np.mean(sg ** 2)) + 1e-12 for sg in segs]
    g = float(np.exp(np.mean(np.log(gs))))
    sx = (np.arange(XFADE) + 0.5) / XFADE
    out = []
    for i in range(n):
        prev = (i - 1) % n
        cont = ys[prev][st[prev] + Ls[prev]:st[prev] + Ls[prev] + XFADE] * g / gs[prev]
        head = segs[i][:XFADE] * g / gs[i]
        r = float(np.clip(J[prev][idx[prev], idx[i]], 0.0, 1.0))
        kk = 1.0 / np.sqrt(sx * sx + (1 - sx) ** 2 + 2 * r * sx * (1 - sx))
        seg = segs[i] * g / gs[i]
        seg[:XFADE] = sx * kk * head + (1 - sx) * kk * cont
        out.append(seg)
    return np.concatenate(out), rho


def best_pair(T, cs, B, main_order, defs, need, tier, n_seg: int = 2):
    """n_seg (2 or 3) shorter real candidates joined into one loop (chain_loop), for a bin where no single stretch is
    long enough. Segments must match in timbre (1/3-octave envelope within 6 dB on average)."""
    seg = need / n_seg + 1.05 * 120.0 / B
    procs = []
    for c in cs[:7]:
        try:
            p = process(T, c, B, main_order, seg, min(seg, 0.3))
        except Exception:
            continue
        if not order_ok(p["loop"], p["rpm"], defs["cylinders"]) or p["tick"] > 8.0:
            continue
        procs.append(p)

    def env(y):
        X = np.abs(np.fft.rfft(y * np.hanning(len(y)))) ** 2
        fr = np.fft.rfftfreq(len(y), 1 / SR)
        edges = 63 * 2 ** (np.arange(0, 22) / 3)
        e = np.array([10 * np.log10(X[(fr >= lo) & (fr < hi)].sum() + 1e-20) for lo, hi in zip(edges[:-1], edges[1:])])
        return e - e.mean()
    envs = [env(p["loop"]) for p in procs]
    import itertools
    best = None
    for combo in itertools.combinations(range(len(procs)), n_seg):
        ps = [procs[i] for i in combo]
        if any(a["src"] == b["src"] and abs(a["t"] - b["t"]) < 0.3 for a, b in itertools.combinations(ps, 2)):
            continue
        mis = max(float(np.mean(np.abs(envs[i] - envs[j]))) for i, j in itertools.combinations(combo, 2))
        if mis > 6.0:
            continue
        r = chain_loop([p["long"] for p in ps], B, need)
        if r is None:
            continue
        loop, rho = r
        if rho < 0.3:
            continue
        tick = transient_ratio(loop)
        if tick > 8.0:
            continue
        score = float(np.mean([p["contrast"] for p in ps])) + 4.0 * rho - 0.5 * mis - 2.0 * max(0.0, tick - 2.5)
        if best is None or score > best[0]:
            best = (score, ps, loop, rho, tick, mis)
    if best is None:
        return None
    _, ps, loop, rho, tick, mis = best
    sf_ = sc.speech_features(loop, B, periodic=True)
    if sc.is_speech(sf_):
        return None
    q = dict(ps[0])
    q.update({"loop": loop, "rho": rho, "tick": tick, "name2": " + ".join(p["name"] for p in ps[1:]),
              "t2": ps[1]["t"], "parts": [(p["name"], round(p["t"], 2)) for p in ps],
              "long": np.concatenate([p["long"] for p in ps]), "pair_mismatch_db": mis})
    m = SR * 120.0 / B
    q["rpm"] = (round(len(loop) / m) * 120.0 * SR) / len(loop)
    return q


def best_loop(T, cs, B, main_order, defs, need, tgt, tier):
    best = None
    for c in cs[:8]:
        try:
            p = process(T, c, B, main_order, tgt, need)
        except Exception as ex:  # too short to loop etc.
            print(f"    skip candidate {c[1:]}: {ex}")
            continue
        if not order_ok(p["loop"], p["rpm"], defs["cylinders"]):
            continue  # strongest order off the firing ladder: an octave-slipped label
        if p["tick"] > 8.0:  # a click / knock repeating once per loop: rather pitch-shift a neighbour
            continue
        sf_ = sc.speech_features(p["loop"], p["rpm"], periodic=True)
        if sc.is_speech(sf_):
            print(f"    reject candidate {c[1:]}: speech in the loop (silero share {sf_['silero_share']})")
            continue
        score = p["contrast"] + 4.0 * p["rho"] - 2.0 * max(0.0, p["tick"] - 2.5) - 60 * p["wobble"] * (tier in ("steady", "idle"))
        if best is None or score > best[0]:
            best = (score, p)
    if best is None or best[1]["rho"] < 0.2:
        return None
    return best[1]


def build(fam: str, force_track: bool = False, bin_step: int | None = None):
    defs, src = load_defs(fam)
    print(f"{fam}: {defs}")
    T = tracks(fam, defs, src, force_track)
    if not T:
        raise SystemExit("no usable source entries")
    main_order = float(next(iter(T.values()))["res"]["main_order"])
    allconf = np.concatenate([d["res"]["conf"] for d in T.values() if not d.get("idle_only")])
    conf_min = max(1.2, float(np.percentile(allconf, 35)))
    chosen = {"on": {}, "off": {}}
    # the idle bin: a steady idle recording (neither label), the same loop for both loads. It sits at the recording's
    # own rpm, which must play the family idle within the pitch window of both loads (x0.88-1.14)
    idle = defs["idle_rpm"]
    lo_r, hi_r = idle / RATIO["on"][1], idle / RATIO["on"][0]
    c_r, tol_r = 0.5 * (lo_r + hi_r), 0.5 * (hi_r - lo_r)
    p = None
    for n_seg in (1, 2, 3):
        need0 = loop_need(c_r)
        cs = candidates(T, c_r, "idle", tol_r, need0 / n_seg + (0.35 if n_seg == 1 else 0.2), 0.8 * conf_min,
                        span_s=need0 / n_seg + 0.5)
        # prefer stretches whose own rpm is nearest the family idle
        cs = sorted(cs, key=lambda c: (abs(float(np.median(T[c[1]]["res"]["rpm"][c[2]:c[3]])) - idle) > 0.06 * idle, -c[0]))
        if not cs:
            continue
        B0 = int(round(float(np.median(T[cs[0][1]]["res"]["rpm"][cs[0][2]:cs[0][3]])) / 5.0) * 5)
        need, tgt = loop_need(B0), loop_target(B0)
        if n_seg == 1:
            p = best_loop(T, cs, B0, main_order, defs, need, tgt, "idle")
        elif len(cs) >= n_seg:
            p = best_pair(T, cs, B0, main_order, defs, need, "idle", n_seg)
        if p is not None:
            break
    if p is not None:
        p["tier"], p["bin"] = "idle", B0
        chosen["on"][B0] = chosen["off"][B0] = p
        print(f"  idle {B0:5d} idle   {p['name']} t={p['t']:.2f} conf={p['contrast']:.1f} rho={p['rho']:.3f} "
              f"loop={len(p['loop']) / SR:.3f}s rpm_eff={p['rpm']:.1f}")
    else:
        B0 = idle
        print(f"  idle {idle}: no steady idle stretch within the window found")
    BINS = bin_grid(B0, defs["redline_rpm"])
    print(f"  bins {BINS[0]}..{BINS[-1]} ({len(BINS)}): {BINS[:6]}..., loops >= max(1.0 s, 8 cycles), conf_min {conf_min:.2f} dB")
    for load in ("on", "off"):
        for B in BINS:
            if B in chosen[load]:
                continue
            need, tgt = loop_need(B), loop_target(B)
            p = None
            for tier, tol, min_s in (("steady", min(120.0, 0.06 * B), need + 0.35), ("sweep", min(0.09 * B + 80, 0.11 * B), need + 0.25)):
                cs = candidates(T, B, load, tol, min_s, conf_min, span_s=need + 0.5)
                if cs:
                    p = best_loop(T, cs, B, main_order, defs, need, tgt, tier)
                for n_seg in (2, 3):  # two or three shorter real stretches joined
                    if p is not None:
                        break
                    cs = candidates(T, B, load, tol, need / n_seg + 0.2, conf_min, span_s=need / n_seg + 0.45)
                    if len(cs) >= n_seg:
                        p = best_pair(T, cs, B, main_order, defs, need, tier, n_seg)
                if p is not None:
                    p["tier"] = tier
                    break
            if p is None and B <= 1.5 * defs["idle_rpm"]:
                # near idle neither label is reliable: a steady unloaded stretch at this rpm (a high idle, rolling
                # in neutral) serves both loads, as the idle bin does
                for n_seg in (1, 2, 3):
                    cs = candidates(T, B, "idle", min(60.0, 0.07 * B), need / n_seg + (0.35 if n_seg == 1 else 0.2),
                                    0.8 * conf_min, span_s=need / n_seg + 0.5)
                    if n_seg == 1 and cs:
                        p = best_loop(T, cs, B, main_order, defs, need, tgt, "idle")
                    elif len(cs) >= n_seg:
                        p = best_pair(T, cs, B, main_order, defs, need, "idle", n_seg)
                    if p is not None:
                        p["tier"] = "idle"
                        other = "off" if load == "on" else "on"
                        chosen[other].setdefault(B, p)
                        break
            if p is None:
                continue
            p["bin"] = B
            chosen[load][B] = p
            print(f"  {load:3s} {B:5d} {p['tier']:6s} {p['name']} t={p['t']:.2f} conf={p['contrast']:.1f} rho={p['rho']:.3f} "
                  f"tick={p['tick']:.1f} loop={len(p['loop']) / SR:.3f}s rpm_eff={p['rpm']:.1f}")

    if not chosen["on"] and not chosen["off"]:
        raise SystemExit("no bin found any candidate")
    borrowed = {}
    on_db = {B: rms_db(p["loop"]) for B, p in chosen["on"].items() if p["tier"] != "idle"}
    off_db = {B: rms_db(p["loop"]) for B, p in chosen["off"].items() if p["tier"] != "idle"}
    both = sorted(set(on_db) & set(off_db))
    diffs = np.array([off_db[B] - on_db[B] for B in both]) if both else np.array([])
    # one constant gap: the recordings differ in gain and distance, so a slope over rpm fitted across them is noise
    gap = float(np.clip(np.median(diffs), -9.0, -4.0)) if len(both) >= 3 else -6.0
    print("  off-on level gap", round(gap, 2))

    final = {"on": {}, "off": {}}
    gate_fail = []
    for load in ("on", "off"):
        other = "off" if load == "on" else "on"
        lo, hi = RATIO[load]
        for B in BINS:
            if B in chosen[load]:
                final[load][B] = chosen[load][B]
                continue
            need, tgt = loop_need(B), loop_target(B)
            # 1. a real loop of the same load within the ratio window, 2. a real loop of the other load at this rpm
            # (darkened for the overrun), 3. the nearest same-load loop anyway (a gate failure, reported)
            same = [R for R, q in chosen[load].items() if lo <= B / q["rpm"] <= hi]
            oth = [R for R, q in chosen[other].items() if lo <= B / q["rpm"] <= hi and q["tier"] != "idle"]
            if same:
                sb, pool, how = min(same, key=lambda R: (abs(np.log(B / chosen[load][R]["rpm"])), -R)), chosen[load], "pitch-shifted"
            elif oth:
                sb, pool, how = min(oth, key=lambda R: (abs(np.log(B / chosen[other][R]["rpm"])), -R)), chosen[other], f"from-{other}"
            else:
                real = sorted(chosen[load]) or sorted(chosen[other])
                pool = chosen[load] if chosen[load] else chosen[other]
                sb, how = min(real, key=lambda R: (abs(R - B), -R)), "pitch-shifted"
                gate_fail.append(f"{load} {B} from {sb} x{B / pool[sb]['rpm']:.3f}")
            s = dict(pool[sb])
            if how == "from-on" and load == "off":
                s = darken(s)
            s["bin"] = sb
            need_n = (tgt + 2 * PAD / SR + 0.25) * SR * (B / s["rpm"])
            if len(s["long"]) < need_n:  # a short segment shifted up: tile its (seamless) loop instead
                s["long"] = np.tile(s["loop"], int(np.ceil(need_n / len(s["loop"]))) + 1)
            p = pitch_shift(s, B, max_len_s=tgt, min_len_s=need)
            p["tier"], p["bin"], p["how"] = ("pitch-shifted" if how == "pitch-shifted" else how), B, how
            p["from_load"] = load if how == "pitch-shifted" else other
            final[load][B] = p
    if gate_fail:
        print("  RATIO GATE FAILS (need more real bins):", "; ".join(gate_fail))
    return write_family(fam, defs, T, final, BINS, gap, main_order, borrowed)


def write_family(fam: str, defs: dict, T: dict, final: dict, BINS: list, gap: float, main_order: float,
                 borrowed: dict, sources: list | None = None, plot: bool = True):
    """Levels, the two Opus sprites, engine.json and the listening sweep, from the finished per-bin loops
    (final[load][bin] = {loop, tier, rpm, rho, tick, name, t, ...}). Shared with the synthesiser (synth_engine.py)."""
    real_bins = {load: sum(1 for B in BINS if final[load][B]["tier"] in REAL_TIERS) for load in final}
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
            elif p["tier"].startswith("from-"):
                srcs = (f"the {p['from_load']}-throttle {p['from_rpm']} rpm loop{' darkened' if p['from_load'] == 'on' else ''} "
                        f"(x{p['ratio']:.3f}), {p['name']} @ {p['t']:.2f} s")
            else:
                srcs = (" + ".join(f"{n_} @ {t_:.2f} s" for n_, t_ in p["parts"]) if p.get("parts") else f"{p['name']} @ {p['t']:.2f} s")
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
                    "t1": d["meta"].get("t1")} for k, d in T.items() if not d.get("idle_only")]})
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
    T = {k: v for k, v in T.items() if not v.get("idle_only")}
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
