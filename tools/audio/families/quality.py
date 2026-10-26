"""Quality measurement for the engine-sound families (round two, 26 Oct 2026): the owner's listening words as numbers.

    P="uv run --python 3.12 --with numpy,scipy,soundfile,webrtcvad-wheels,onnxruntime python -I"
    $P tools/audio/families/quality.py [FAMILY ...] [--json OUT.json] [--md]

Decodes each family's shipped Ogg sprites (as Chrome does), heals the loop seams as the player does
(audio.ts healLoopSeams), and measures every bin and load:

  speech    speechcheck.py on the loop (residual after the engine-cycle-synchronous average): vad / pitch / voice
  ratio     pitch ratio from the REAL recording the loop came from: 1 for a steady / sweep / idle bin (its loop rpm
            vs the bin), the stored factor for a pitch-shifted bin. "Tape" starts near 0.8 / 1.25.
  idle      the playback ratio at the family's idle rpm (bin 0 played at idle_rpm), and whether bin 0 is real
  loop_s    loop length, and the 8-engine-cycle length at the bin rpm (the low-rpm minimum)
  loopiness envelope periodicity at the loop period of the steady tone: 1 - the highest envelope autocorrelation at
            lags of 20-80 % of the loop (0 = every part of the loop alike, the repeat is inaudible; near 1 = the loop
            has one event that marks each repeat)
  seam_corr the build's seam correlation; seam_step the sample jump across the healed seam over the loop's 95th
            percentile step (listen_check's measure)
  harm      the share of 30-6000 Hz power within +-0.05 order of the engine's half orders (a fifth of the bins between
            them): near 1 = a clean "organ" tone, near 0.2 = noise
  level     A-weighted RMS of the on loop, dB re full scale

Gates (GATES below; test_quality.py asserts them):
  speech: no loop flagged; on ratio 0.88-1.14, off 0.85-1.18; bin 0 real and at idle (idle playback ratio inside the
  same windows); loop >= max(1.0 s, 8 engine cycles); seam correlation recorded per bin (compared before / after in
  the ledger).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import speechcheck as sc  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
# QUALITY_PUBLIC: another public/audio tree to measure (e.g. release-040's, extracted with git archive) instead of ours
AUD = os.environ.get("QUALITY_PUBLIC") or os.path.join(ROOT, "public", "audio")
FAM = os.path.join(AUD, "families")
SR = 48000
FFMPEG = "/opt/homebrew/bin/ffmpeg"
REAL = ("steady", "sweep", "idle")
GATES = {"on": (0.88, 1.14), "off": (0.85, 1.18), "min_loop_s": 1.0, "min_cycles": 8}
# the owner's ear (26 Oct 2026): these two are "OK" and are only changed for speech
OWNER_OK = ("mazda_kl_v6", "sohc_i4_loud")


def decode(path: str) -> np.ndarray:
    raw = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64).copy()


def heal(data: np.ndarray, refs: list, n: int = 256) -> None:
    for r in refs:
        a = round(r["offset"] * SR)
        ln = round(r["duration"] * SR)
        e = a + ln
        m = min(n, a, ln >> 2)
        for i in range(m):
            w = (i + 1) / m
            k = e - m + i
            data[k] += (data[a - m + i] - data[k]) * w


def family_files(fam: str):
    if fam == "mazda_kl_v6":
        ej = os.path.join(AUD, "engine.json")
        d = AUD
    else:
        ej = os.path.join(FAM, fam, "engine.json")
        d = os.path.join(FAM, fam)
    e = json.load(open(ej))
    sp = e.get("sprites") or {"on": "engine_on.ogg", "off": "engine_off.ogg"}
    return e, {k: os.path.join(d, sp[k]) for k in ("on", "off")}, ej


def load_family(fam: str):
    e, sp, ej = family_files(fam)
    spr = {k: decode(p) for k, p in sp.items()}
    for k in ("on", "off"):
        heal(spr[k], [b[k] for b in e["bins"]])
    idx = json.load(open(os.path.join(FAM, "index.json")))["families"][fam]
    meta = {"idle": e.get("idle_rpm") or idx.get("idle") or 850, "redline": e.get("redline_rpm") or idx.get("redline"),
            "cylinders": e.get("cylinders") or idx.get("cylinders") or 6}
    sizes = {k: os.path.getsize(p) for k, p in sp.items()}
    sizes["json"] = os.path.getsize(ej)
    return e, spr, meta, sizes


def loop_of(spr, ref):
    a = int(round(ref["offset"] * SR))
    L = int(round(ref["duration"] * SR))
    return spr[a:a + L]


def ratio_of(ref: dict, bin_rpm: float) -> float:
    """Pitch ratio from the real recording behind this loop (its playback at the bin rpm)."""
    if ref["tier"] in REAL:
        return bin_rpm / ref["rpm"]
    m = re.search(r"\(x([0-9.]+)\)", ref.get("source", ""))
    if m:
        return float(m.group(1)) * bin_rpm / ref["rpm"]
    return float("nan")  # borrowed from the other load / synth: not a recording at this load


def recorded_rpm(ref: dict, bin_rpm: float) -> float:
    r = ratio_of(ref, bin_rpm)
    return bin_rpm / r if np.isfinite(r) else float("nan")


def loopiness(lp: np.ndarray) -> float:
    b = signal.sosfiltfilt(signal.butter(2, [60, 4000], "bandpass", fs=SR, output="sos"), np.tile(lp, 3))[len(lp):2 * len(lp)]
    fl = int(0.005 * SR)
    n = len(b) // fl
    env = np.sqrt(np.mean(b[:n * fl].reshape(n, fl) ** 2, axis=1))
    env = env - env.mean()
    if np.allclose(env, 0) or n < 10:
        return 0.0
    F = np.fft.rfft(env)
    ac = np.fft.irfft(np.abs(F) ** 2, n)
    ac /= ac[0]
    lo, hi = int(0.2 * n), int(0.8 * n)
    return float(1 - ac[lo:hi + 1].max())


def seam_step(lp: np.ndarray) -> float:
    x = np.concatenate([lp[-64:], lp[:64]])
    jump = np.abs(np.diff(x))
    med = np.percentile(np.abs(np.diff(lp)), 95) + 1e-12
    return float(jump[63] / med)


def harmonicity(lp: np.ndarray, rpm: float) -> float:
    L = len(lp)
    X = np.abs(np.fft.rfft(np.tile(lp, 4) * np.hanning(4 * L))) ** 2
    fr = np.fft.rfftfreq(4 * L, 1 / SR)
    f_rev = rpm / 60.0
    band = (fr > 30) & (fr < 6000)
    on = np.zeros_like(fr, bool)
    for o in np.arange(0.5, 6000 / f_rev, 0.5):
        on |= np.abs(fr - o * f_rev) <= 0.1 * 0.5 * f_rev
    return float(X[band & on].sum() / (X[band].sum() + 1e-20))


def a_rms_db(lp: np.ndarray) -> float:
    from loopkit import rms_db  # noqa: E402
    return float(rms_db(lp))


def measure(fam: str, speech: bool = True) -> dict:
    e, spr, meta, sizes = load_family(fam)
    rows = []
    for b in e["bins"]:
        for ld in ("on", "off"):
            ref = b[ld]
            lp = loop_of(spr[ld], ref)
            r = ratio_of(ref, b["rpm"])
            row = {"bin": b["rpm"], "load": ld, "tier": ref["tier"], "loop_rpm": ref["rpm"],
                   "ratio": round(r, 4) if np.isfinite(r) else None,
                   "loop_s": round(len(lp) / SR, 4), "need_s": round(max(GATES["min_loop_s"], GATES["min_cycles"] * 120.0 / b["rpm"]), 4),
                   "cycles": round(len(lp) / SR * ref["rpm"] / 120.0, 2),
                   "seam_corr": ref.get("seam_corr"), "seam_step": round(seam_step(lp), 2),
                   "loopiness": round(loopiness(lp), 3), "harm": round(harmonicity(lp, ref["rpm"]), 3),
                   "level_dbA": round(a_rms_db(lp), 2), "source": ref.get("source", "")}
            if speech:
                f = sc.speech_features(lp, ref["rpm"], periodic=True)
                row.update({"sp_" + k: v for k, v in f.items()})
                row["speech"] = bool(sc.is_speech(f))
            rows.append(row)
    b0 = e["bins"][0]
    idle = meta["idle"]
    idle_row = {}
    for ld in ("on", "off"):
        rec = recorded_rpm(b0[ld], b0["rpm"])
        idle_row[ld] = {"tier": b0[ld]["tier"], "recorded_rpm": round(rec, 1) if np.isfinite(rec) else None,
                        "idle_ratio": round(idle / rec, 4) if np.isfinite(rec) else None}
    return {"family": fam, "idle": idle, "redline": meta["redline"], "bins": len(e["bins"]),
            "bin_lo": e["bins"][0]["rpm"], "bin_hi": e["bins"][-1]["rpm"], "rows": rows, "idle_play": idle_row,
            "sprite_bytes": sizes}


def gate_failures(m: dict) -> dict:
    """{gate: [description, ...]} for one family's measurement."""
    out = {"speech": [], "ratio": [], "idle": [], "loop": []}
    for r in m["rows"]:
        tag = f"{r['bin']} {r['load']}"
        if r.get("speech"):
            out["speech"].append(f"{tag} (silero share {r['sp_silero_share']}, max {r['sp_silero']})")
        lo, hi = GATES[r["load"]]
        if r["ratio"] is None or not (lo <= r["ratio"] <= hi):
            out["ratio"].append(f"{tag} x{r['ratio']}")
        # at least 1.0 s and at least 8 whole engine cycles (a loop is a whole number of cycles at its own rpm)
        if r["loop_s"] + 1e-3 < GATES["min_loop_s"] or r["cycles"] + 0.02 < GATES["min_cycles"]:
            out["loop"].append(f"{tag} {r['loop_s']:.2f}<{r['need_s']:.2f}s")
    for ld in ("on", "off"):
        ip = m["idle_play"][ld]
        lo, hi = GATES[ld]
        if ip["tier"] not in REAL:
            out["idle"].append(f"bin {m['bin_lo']} {ld} is {ip['tier']}")
        if ip["idle_ratio"] is None or not (lo <= ip["idle_ratio"] <= hi):
            out["idle"].append(f"idle {m['idle']} on the {ld} {m['bin_lo']} bin recorded at {ip['recorded_rpm']}: x{ip['idle_ratio']}")
    return out


def summary(m: dict) -> dict:
    rows = m["rows"]
    rr = [r["ratio"] for r in rows if r["ratio"] is not None]
    on = [r for r in rows if r["load"] == "on"]
    off = [r for r in rows if r["load"] == "off"]
    f = gate_failures(m)
    return {"family": m["family"], "bins": f"{m['bin_lo']}-{m['bin_hi']} ({m['bins']})",
            "real_on": sum(r["tier"] in REAL for r in on), "real_off": sum(r["tier"] in REAL for r in off),
            "speech": len(f["speech"]), "ratio_fail": len(f["ratio"]),
            "ratio_min": min(rr) if rr else None, "ratio_max": max(rr) if rr else None,
            "borrowed": sum(r["ratio"] is None for r in rows),
            "idle_ok": not f["idle"], "idle_off_ratio": m["idle_play"]["off"]["idle_ratio"],
            "loop_med": float(np.median([r["loop_s"] for r in rows])), "loop_fail": len(f["loop"]),
            "loopiness_med": float(np.median([r["loopiness"] for r in rows])),
            "loopiness_max": float(np.max([r["loopiness"] for r in rows])),
            "seam_corr_med": float(np.median([r["seam_corr"] for r in rows if r["seam_corr"] is not None])),
            "seam_step_max": float(np.max([r["seam_step"] for r in rows])),
            "harm_med": float(np.median([r["harm"] for r in rows])),
            "level_on_dbA": float(np.median([r["level_dbA"] for r in on])),
            "bytes": int(sum(m["sprite_bytes"].values()))}


def md_table(sums: list) -> str:
    h = ("| Family | bins | real on/off | speech loops | ratio fails (min-max) | idle real & in gate (off ratio) | "
         "loop median s (fails) | loopiness med/max | seam corr med | seam step max | ladder share med | on level dBA | bytes |")
    lines = [h, "|" + "---|" * 13]
    for s in sums:
        lines.append(f"| `{s['family']}` | {s['bins']} | {s['real_on']}/{s['real_off']} | {s['speech']} | "
                     f"{s['ratio_fail']} ({s['ratio_min']:.2f}-{s['ratio_max']:.2f}) | "
                     f"{'yes' if s['idle_ok'] else 'no'} (x{s['idle_off_ratio']}) | {s['loop_med']:.2f} ({s['loop_fail']}) | "
                     f"{s['loopiness_med']:.2f}/{s['loopiness_max']:.2f} | {s['seam_corr_med']:.2f} | {s['seam_step_max']:.1f} | "
                     f"{s['harm_med']:.2f} | {s['level_on_dbA']:.1f} | {s['bytes']:,} |")
    return "\n".join(lines)


def all_families() -> list:
    return list(json.load(open(os.path.join(FAM, "index.json")))["families"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("families", nargs="*")
    ap.add_argument("--json")
    ap.add_argument("--md", action="store_true")
    ap.add_argument("--no-speech", action="store_true")
    a = ap.parse_args()
    fams = a.families or all_families()
    res = {}
    for fam in fams:
        m = measure(fam, speech=not a.no_speech)
        res[fam] = {"measure": m, "summary": summary(m), "fails": gate_failures(m)}
        s = res[fam]["summary"]
        print(f"{fam}: real {s['real_on']}/{s['real_off']}, speech {s['speech']}, ratio fails {s['ratio_fail']} "
              f"({s['ratio_min']:.2f}-{s['ratio_max']:.2f}), idle ok {s['idle_ok']}, loop med {s['loop_med']:.2f} s "
              f"fails {s['loop_fail']}, loopiness {s['loopiness_med']:.2f}/{s['loopiness_max']:.2f}, {s['bytes']} B", flush=True)
    if a.json:
        json.dump(res, open(a.json, "w"), indent=1)
    if a.md:
        print(md_table([res[f]["summary"] for f in fams]))
