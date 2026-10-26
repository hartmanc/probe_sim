"""Procedural engine-note generator for the AI families that have no CC BY recording.

    P="uv run --python 3.12 --with numpy,scipy,soundfile,matplotlib python -I"
    $P tools/audio/families/synth_engine.py --family vintage_i6 [--compare bmw_m20_i6]

Writes the same on / off sprites (Opus 48 kbps mono, 250 rpm bins, [tail pad | loop | head pad]), engine.json and
index data as build_family.py does (it calls build_family.write_family), with `sources: [{"src": "synth", ...}]`
and tier "synth" on every bin. Nothing is sampled from anywhere: it is arithmetic.

Model (one loop = a whole number of 4-stroke cycles, built on the loop's own FFT grid, so it is periodic by
construction and needs no crossfade):
  * firing events: cylinder k fires at its crank angle (even-fire spacing 720/n degrees; the bank pattern of a
    cross-plane V8 and the unequal pipe lengths of a flat four are per-family), each with its own pressure
    amplitude jitter (lognormal, bigger at idle and for rough old engines) and timing jitter (a fraction of a
    degree);
  * exhaust: each event is a Gaussian blow-down pulse whose width is a fixed crank angle (so it narrows as the
    engine speeds up), passed through a small bank of pipe resonances (quarter-wave odd modes at a fixed length,
    in Hz, not in orders) and a tail-pipe low-pass. Pulses of the two banks of a V engine / boxer reach a
    shared collector with a small delay;
  * intake: a noise burst per intake stroke through a Helmholtz-like band-pass whose centre rises a little with
    rpm; on throttle it is a growl, off throttle (closed plate, high vacuum) it is louder and darker;
  * mechanical: valve-train ticks at the cam rate (OHV/SOHC: a few kHz, jittered) and a broadband block-noise
    floor that follows rpm and load;
  * load: on throttle the exhaust pulses carry full pressure; off throttle they drop to ~25 % and the note
    darkens (overrun burble comes from the jitter plus an occasional extra weak event).
The family profiles below are tuned with `--compare`, which prints the 1/3-octave band levels against a clean real
family at the same rpm and records the mean absolute difference in dB.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from common import ROOT, SR  # noqa: E402
from loopkit import PAD, rms_db, transient_ratio  # noqa: E402
import build_family as bf  # noqa: E402

# Per-family profile. pulse_deg: exhaust blow-down width (crank degrees); pipe_f1: quarter-wave fundamental (Hz);
# tail_fc: tail-pipe low-pass; amp_jit / ang_jit: per-event amplitude (lognormal sigma) and timing (degrees) jitter;
# w_*: mix weights (exhaust, intake, mechanical, floor); banks: pattern of firing-order bank ids (None = one bank);
# bank_delay_ms: extra pipe delay of bank 1 (unequal-length headers); tick_hz: valve-train tick band.
PROFILES = {
    "vintage_i6": {"pulse_deg": 46, "pipe_f1": 62, "tail_fc": 1500, "amp_jit": 0.10, "ang_jit": 0.35,
                   "w_exh": 1.0, "w_int": 0.35, "w_mech": 0.22, "w_floor": 0.06, "banks": None, "bank_delay_ms": 0.0,
                   "tick_hz": 2600, "int_fc": 190, "ref": "bmw_m20_i6"},
    "ohv_v6": {"pulse_deg": 38, "pipe_f1": 74, "tail_fc": 2100, "amp_jit": 0.14, "ang_jit": 0.5,
               "w_exh": 1.0, "w_int": 0.42, "w_mech": 0.30, "w_floor": 0.08, "banks": [0, 1, 0, 1, 0, 1],
               "bank_delay_ms": 0.35, "tick_hz": 3200, "int_fc": 230, "ref": "probe"},
    "classic_v8_lowrev": {"pulse_deg": 52, "pipe_f1": 55, "tail_fc": 1300, "amp_jit": 0.16, "ang_jit": 0.7,
                          "w_exh": 1.0, "w_int": 0.40, "w_mech": 0.20, "w_floor": 0.05,
                          "banks": [0, 1, 1, 0, 1, 0, 0, 1], "bank_delay_ms": 0.6, "tick_hz": 2200, "int_fc": 150,
                          "ref": "probe"},
    "gm_sbc_v8": {"pulse_deg": 40, "pipe_f1": 68, "tail_fc": 2600, "amp_jit": 0.12, "ang_jit": 0.5,
                  "w_exh": 1.0, "w_int": 0.45, "w_mech": 0.28, "w_floor": 0.07,
                  "banks": [0, 1, 1, 0, 1, 0, 0, 1], "bank_delay_ms": 0.5, "tick_hz": 3000, "int_fc": 210,
                  "ref": "probe"},
    "vw_aircooled_flat4": {"pulse_deg": 44, "pipe_f1": 80, "tail_fc": 1900, "amp_jit": 0.13, "ang_jit": 0.6,
                           "w_exh": 1.0, "w_int": 0.30, "w_mech": 0.55, "w_floor": 0.10,
                           "banks": [0, 1, 1, 0], "bank_delay_ms": 0.9, "tick_hz": 2400, "int_fc": 260,
                           "ref": "subaru_fa20_flat4"},
}


def firing_angles(n_cyl: int, banks: list | None, ang_jit: float, rng) -> np.ndarray:
    """Crank angles (deg, within 720) of the firing events in firing order, plus bank ids."""
    base = np.arange(n_cyl) * 720.0 / n_cyl
    return base


def _fft_filter(x: np.ndarray, H: np.ndarray) -> np.ndarray:
    return np.fft.irfft(np.fft.rfft(x) * H, n=len(x))


def exhaust_tf(f: np.ndarray, f1: float, tail_fc: float) -> np.ndarray:
    """Quarter-wave pipe modes (odd multiples of f1) as resonant peaks, a direct path, and a tail-pipe low-pass."""
    H = np.full_like(f, 0.55, dtype=np.complex128)
    for k, (m, g, q) in enumerate(((1, 1.0, 3.0), (3, 0.7, 4.5), (5, 0.45, 6.0), (7, 0.28, 7.0))):
        fk = f1 * m
        H += g * (1j * f / (fk * q)) / (1 - (f / fk) ** 2 + 1j * f / (fk * q)) * 1.6
    lp = 1.0 / (1 + (f / tail_fc) ** 4)
    return H * lp


def synth_loop(B: int, load: str, prof: dict, n_cyl: int, max_len: float, seed: int, idle: float):
    """One exactly periodic loop at B rpm: returns (samples, effective rpm)."""
    rng = np.random.default_rng(seed)
    n_cyc = max(1, int(round(max_len * B / 120.0)))
    L = int(round(n_cyc * 120.0 * SR / B))
    rpm_eff = n_cyc * 120.0 * SR / L
    t = np.arange(L) / SR
    f = np.fft.rfftfreq(L, 1 / SR)
    rev_s = 60.0 / rpm_eff                  # seconds per crank revolution
    deg_s = rev_s / 360.0                   # seconds per crank degree
    on = load == "on"
    rough = 1.0 + 1.6 * np.exp(-(B - 600) / 700.0) if B > 600 else 2.6  # idle is lumpier
    banks = prof["banks"]
    # ---- events
    n_ev = n_cyc * n_cyl
    ex = np.zeros(L)
    inl = np.zeros(L)
    mech = np.zeros(L)
    amp_cyl = rng.lognormal(0.0, prof["amp_jit"] * 0.5, n_cyl)      # per-cylinder fixed bias (cylinder-to-cylinder)
    width = prof["pulse_deg"] * deg_s                               # Gaussian sigma ~ width/2.4
    sig = max(width / 2.4, 2.0 / SR)
    amp_on = 1.0 if on else 0.24
    for e in range(n_ev):
        cyl = e % n_cyl
        ang = (e * 720.0 / n_cyl) + rng.normal(0, prof["ang_jit"] * rough)
        t_e = (ang * deg_s) % (L / SR)
        a = amp_on * amp_cyl[cyl] * rng.lognormal(0.0, prof["amp_jit"] * rough)
        if not on and rng.random() < 0.07 * (B < 3500):             # overrun burble: a partial / extra event
            a *= rng.uniform(1.5, 3.0)
        bank = banks[cyl % len(banks)] if banks else 0
        t_ex = t_e + (prof["bank_delay_ms"] * 1e-3 if bank else 0.0)
        for te, arr, amp, s in ((t_ex, ex, a, sig),):
            idx = np.arange(int(max(0, te - 5 * s) * SR) - 2, int((te + 5 * s) * SR) + 3)
            tt = (idx / SR - te)
            arr[idx % L] += amp * np.exp(-0.5 * (tt / s) ** 2) * (1 - 0.25 * (tt / s))  # slightly skewed blow-down
        # intake stroke burst (offset by 180 deg of crank from the exhaust event of the same cylinder)
        t_i = ((ang + 360.0) * deg_s) % (L / SR)
        ib = (0.6 if on else 1.15) * rng.lognormal(0.0, 0.18)
        k0 = int(t_i * SR)
        ln = int(min(0.18 * 720 / n_cyl * deg_s * SR * 2, L // 3))
        win = np.hanning(max(8, ln))
        burst = rng.standard_normal(len(win)) * win * ib
        inl[(k0 + np.arange(len(win))) % L] += burst
        # valve train tick, twice per cylinder cycle (inlet + exhaust valves)
        for off_deg in (-30.0, 140.0):
            k1 = int(((ang + off_deg) * deg_s * SR) % L)
            tick = np.sin(2 * np.pi * prof["tick_hz"] * np.arange(40) / SR) * np.exp(-np.arange(40) / 9.0)
            mech[(k1 + np.arange(40)) % L] += tick * rng.lognormal(0.0, 0.3) * 0.5
    # ---- shaping on the loop's own FFT grid (periodic)
    ex_f = _fft_filter(ex, exhaust_tf(f, prof["pipe_f1"], prof["tail_fc"] * (1.0 if on else 0.7)).astype(np.complex128))
    int_fc = prof["int_fc"] * (0.8 + 0.5 * B / 6000.0) * (1.0 if on else 0.8)
    b, a_ = signal.butter(2, [max(40, int_fc * 0.5), int_fc * 3.0], "bandpass", fs=SR)
    inl_f = signal.lfilter(b, a_, np.tile(inl, 3))[L:2 * L]
    mech_f = _fft_filter(mech, (1.0 / (1 + (f / 5200.0) ** 2)).astype(np.complex128))
    # block-noise floor: shaped noise 300-3500 Hz, modulated at firing rate, louder with rpm and load
    nz = rng.standard_normal(L)
    sos = signal.butter(2, [300, 3500], "bandpass", fs=SR, output="sos")
    nzf = signal.sosfilt(sos, np.tile(nz, 3))[L:2 * L]
    fire_hz = rpm_eff / 60.0 * n_cyl / 2.0
    nzf *= 0.55 + 0.45 * np.cos(2 * np.pi * fire_hz * t + rng.uniform(0, 6.28))
    floor_gain = prof["w_floor"] * (0.5 + B / 4000.0) * (1.0 if on else 0.5)
    sc = lambda x: x / (np.std(x) + 1e-12)
    y = (prof["w_exh"] * sc(ex_f) * (1.0 if on else 0.55)
         + prof["w_int"] * sc(inl_f) * (0.7 if on else 1.0)
         + prof["w_mech"] * sc(mech_f) * (0.5 + B / 6000.0)
         + floor_gain * sc(nzf) * 3.0)
    # rpm-dependent loudness (engines get louder with speed), then a gentle 40 Hz high-pass like the sprites
    y = signal.sosfilt(signal.butter(2, 40, "highpass", fs=SR, output="sos"), np.tile(y, 3))[L:2 * L]
    y = y - np.mean(y)
    return y.astype(np.float64), rpm_eff


def band_levels(x: np.ndarray, fs: int = SR) -> tuple[np.ndarray, np.ndarray]:
    """1/3-octave band levels (dB re the band mean) of a looped signal, 50 Hz-8 kHz."""
    X = np.abs(np.fft.rfft(np.tile(x, 4) * np.hanning(4 * len(x)))) ** 2
    fr = np.fft.rfftfreq(4 * len(x), 1 / fs)
    centres = 1000 * 2.0 ** (np.arange(-13, 10) / 3.0)
    lv = []
    for c in centres:
        m = (fr >= c / 2 ** (1 / 6)) & (fr < c * 2 ** (1 / 6))
        lv.append(10 * np.log10(X[m].sum() + 1e-18))
    lv = np.array(lv)
    return centres, lv - lv.max()


def ref_loop(ref: str, rpm: int, load: str):
    """The bin nearest `rpm` of a real reference family (decoded from its Ogg sprite) as a numpy loop."""
    if ref == "probe":
        base = os.path.join(ROOT, "public", "audio")
    else:
        base = os.path.join(ROOT, "public", "audio", "families", ref)
    ej = json.load(open(os.path.join(base, "engine.json")))
    b = min(ej["bins"], key=lambda z: abs(z["rpm"] - rpm))
    spr = bf.decode(os.path.join(base, f"engine_{load}.ogg"))
    r = b[load]
    a = int(round(r["offset"] * SR))
    return spr[a:a + int(round(r["duration"] * SR))], b["rpm"]


def compare(fam: str, prof: dict, defs: dict, ref: str, max_len: float, seed: int) -> dict:
    """Mean absolute 1/3-octave difference (dB, shape only, both normalised to their own peak band) at 3 rpm points,
    on and off throttle, between the synthesised loop and the reference family's loop at the same rpm."""
    out = {}
    for frac in (0.3, 0.55, 0.85):
        B = int(round((defs["idle_rpm"] + frac * (defs["redline_rpm"] - defs["idle_rpm"])) / 250.0) * 250)
        for load in ("on", "off"):
            y, _ = synth_loop(B, load, prof, defs["cylinders"], max_len, seed + B, defs["idle_rpm"])
            try:
                r, rb = ref_loop(ref, B, load)
            except Exception as ex:  # noqa: BLE001
                out[f"{load}@{B}"] = None
                continue
            c, ls = band_levels(y)
            _, lr = band_levels(r)
            keep = (c >= 63) & (c <= 5000)
            out[f"{load}@{B}"] = round(float(np.mean(np.abs(ls[keep] - lr[keep]))), 2)
    return out


def build(fam: str, compare_ref: str | None = None, seed: int = 7):
    defs, _ = bf.load_defs(fam)
    prof = dict(PROFILES[fam])
    ref = compare_ref or prof["ref"]
    lo = 750 if defs["idle_rpm"] < 700 else 1000
    hi = int(np.ceil(defs["redline_rpm"] / 250.0) * 250)
    BINS = list(range(lo, hi + 1, 250))
    sec_total = (bf.BUDGET_BYTES - 12_000) * 8 / (bf.KBPS * 1000) * 0.93
    max_len = float(min(1.0, sec_total / 2 / len(BINS) - 2 * PAD / SR - 0.4 / len(BINS)))
    cmp_ = compare(fam, prof, defs, ref, max_len, seed)
    print(f"  spectrum match vs {ref} (mean |dB| over 1/3-octave bands 63 Hz-5 kHz):", cmp_)
    final = {"on": {}, "off": {}}
    for load in ("on", "off"):
        for B in BINS:
            y, rpm_eff = synth_loop(B, load, prof, defs["cylinders"], max_len, seed + B + (100000 if load == "off" else 0),
                                    defs["idle_rpm"])
            final[load][B] = {"loop": y, "tier": "synth", "bin": B, "rpm": rpm_eff, "rho": 1.0,
                              "tick": transient_ratio(y), "name": "synth", "t": 0.0, "dur_src": 0.0,
                              "long": y}
    gap = -6.0
    main_order = defs["cylinders"] / 2.0
    sources = [{"src": "synth", "url": None, "title": "procedural engine-note generator (tools/audio/families/synth_engine.py)",
                "channel": None, "licence": "synth (original work, no recorded source)", "t0": None, "t1": None,
                "octave_relabel": 1.0, "reference_for_tuning": ref, "spectrum_match_db": cmp_}]
    idx = bf.write_family(fam, defs, {}, final, BINS, gap, main_order, {}, sources=sources, plot=False)
    return idx, cmp_


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True)
    ap.add_argument("--compare", default=None)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    build(a.family, a.compare, a.seed)
