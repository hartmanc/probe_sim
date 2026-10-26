"""AAC fallback for browsers that cannot decode Ogg Opus with decodeAudioData (older iOS Safari).

Converts public/audio/engine_on.ogg, engine_off.ogg and squeal.ogg to .m4a (AAC-LC, 48 kHz mono, ~96 kbps,
Apple's AudioToolbox encoder when ffmpeg has it) and measures where each AAC decode sits relative to the Opus
decode, so the player can keep the loop points (engine.json offsets, squeal.json) sample-aligned.

Measurement: both files are decoded with ffmpeg (Opus pre-skip and the MP4 edit list applied) and cross-correlated;
the lag (m4a minus ogg, seconds) is `offset_s`. The m4a is also decoded with the edit list ignored, which gives the
encoder priming (`priming_s`): a browser that does not honour the edit list returns that many extra samples at
the start, which the player detects from the decoded length (`lengths_s` = the edit-listed length per file).

Writes into engine.json (other fields untouched):
  "fallback": {"on": "engine_on.m4a", "off": "engine_off.m4a", "squeal": "squeal.m4a", "format": ...,
               "offset_s": <median>, "offsets_s": {on, off, squeal}, "priming_s": ..., "lengths_s": {on, off, squeal}}

Run after build_engine.py / build_squeal.py (they rewrite engine.json without this field):
  uv run --python 3.12 --with numpy,scipy,soundfile python -I tools/audio/encode_fallback.py

AI engine families (public/audio/families/<id>/, on and off sprites only, no squeal; the player's squeal is shared):
  ... python -I tools/audio/encode_fallback.py --families            # every family directory
  ... python -I tools/audio/encode_fallback.py --families bmw_m20_i6 # named ones
Each family's engine.json gets the same `fallback` block (without "squeal"); other fields and the .ogg files are
left untouched. Families whose engine.json points at another directory's sprites (sprites paths with "/" or "..")
are skipped. Re-run after build_family.py, which rewrites engine.json without this field.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

import numpy as np
from scipy.signal import correlate

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "..", "public", "audio"))
SR = 48000
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
FILES = {"on": "engine_on", "off": "engine_off", "squeal": "squeal"}
BITRATE = "96k"
MAX_LAG = 6000  # samples searched either way (AAC priming is 1024..2112 samples)


def encoders() -> str:
    return subprocess.run([FFMPEG, "-hide_banner", "-encoders"], capture_output=True, text=True).stdout


def decode(path: str, ignore_editlist: bool = False) -> np.ndarray:
    pre = ["-ignore_editlist", "1"] if ignore_editlist else []
    raw = subprocess.run([FFMPEG, "-v", "error", *pre, "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def lag_of(ref: np.ndarray, sig: np.ndarray) -> float:
    """Lag (samples, sub-sample) at which `sig` best matches `ref`: sig[n + lag] ~ ref[n]."""
    n = min(len(ref), len(sig), SR * 4)
    a, b = ref[:n], sig[: n + MAX_LAG]
    c = correlate(b, a, mode="full", method="fft")
    zero = len(a) - 1
    lo, hi = zero - MAX_LAG, zero + MAX_LAG
    seg = c[lo:hi + 1]
    k = int(np.argmax(seg))
    frac = 0.0
    if 0 < k < len(seg) - 1:
        y0, y1, y2 = seg[k - 1], seg[k], seg[k + 1]
        d = y0 - 2 * y1 + y2
        frac = 0.5 * (y0 - y2) / d if d != 0 else 0.0
    return (k + lo - zero) + frac


def encode_set(d: str, keys: dict[str, str], codec: str) -> dict:
    """Encode `keys` ({key: stem}) from <d>/<stem>.ogg to <d>/<stem>.m4a; return the fallback block parts."""
    offsets, lengths, primings, sizes = {}, {}, {}, {}
    for key, stem in keys.items():
        src = os.path.join(d, stem + ".ogg")
        dst = os.path.join(d, stem + ".m4a")
        ref = decode(src)
        args = [FFMPEG, "-v", "error", "-y", "-i", src, "-c:a", codec, "-b:a", BITRATE, "-ar", str(SR), "-ac", "1"]
        if codec == "aac_at":
            args += ["-aac_at_mode", "cbr"]
        subprocess.run(args + ["-movflags", "+faststart", dst], check=True)
        dec = decode(dst)
        raw = decode(dst, ignore_editlist=True)
        lag = lag_of(ref, dec)
        lag_raw = lag_of(ref, raw)
        offsets[key] = round(lag / SR, 7)
        primings[key] = round((lag_raw - lag) / SR, 7)
        lengths[key] = round(len(dec) / SR, 6)
        sizes[key] = os.path.getsize(dst)
        # quality check: residual after alignment
        k = int(round(lag))
        n = min(len(ref), len(dec) - max(0, k)) - abs(k)
        a = ref[max(0, -k):max(0, -k) + n]
        b = dec[max(0, k):max(0, k) + n]
        snr = 10 * np.log10(np.sum(a * a) / max(1e-12, np.sum((a - b) ** 2)))
        print(f"{stem}: ogg {len(ref)} smp, m4a {len(dec)} smp (raw {len(raw)}), lag {lag:+.2f} smp, "
              f"priming {lag_raw - lag:.1f} smp, SNR vs opus {snr:.1f} dB, {sizes[key]} B")
    vals = sorted(offsets.values())
    return {"offset_s": vals[len(vals) // 2], "offsets_s": offsets, "priming_s": max(primings.values()),
            "lengths_s": lengths, "_sizes": sizes}


def write_block(idx_path: str, block: dict) -> None:
    with open(idx_path) as f:
        index = json.load(f)
    index["fallback"] = block
    with open(idx_path, "w") as f:
        json.dump(index, f, indent=1)


def family_dirs(names: list[str]) -> list[str]:
    root = os.path.join(OUT, "families")
    ids = names or sorted(x for x in os.listdir(root) if os.path.isdir(os.path.join(root, x)))
    return ids


def run_families(names: list[str], codec: str) -> int:
    root = os.path.join(OUT, "families")
    total = 0
    for fam in family_dirs(names):
        d = os.path.join(root, fam)
        idx_path = os.path.join(d, "engine.json")
        with open(idx_path) as f:
            sp = json.load(f).get("sprites") or {"on": "engine_on.ogg", "off": "engine_off.ogg"}
        if any("/" in v for v in sp.values()) or not all(v.endswith(".ogg") for v in sp.values()):
            print(f"{fam}: sprites live elsewhere ({sp}), skipped")
            continue
        print(f"== {fam}")
        keys = {"on": sp["on"][:-4], "off": sp["off"][:-4]}
        r = encode_set(d, keys, codec)
        sizes = r.pop("_sizes")
        block = {"on": keys["on"] + ".m4a", "off": keys["off"] + ".m4a",
                 "format": f"m4a AAC-LC {BITRATE}bps 48 kHz mono ({codec})", **r}
        write_block(idx_path, block)
        total += sum(sizes.values())
        print(f"{fam}: offsets_s {block['offsets_s']} priming_s {block['priming_s']} m4a {sum(sizes.values())} B")
    print("family m4a total", total, "B")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", nargs="*", default=None, metavar="ID",
                    help="encode the AI family directories (all when no id is given) instead of the Probe's files")
    args = ap.parse_args()
    enc = encoders()
    codec = "aac_at" if " aac_at " in enc else "aac"
    print("encoder:", codec)
    if args.families is not None:
        return run_families(args.families, codec)
    r = encode_set(OUT, FILES, codec)
    sizes = r.pop("_sizes")
    block = {"on": "engine_on.m4a", "off": "engine_off.m4a", "squeal": "squeal.m4a",
             "format": f"m4a AAC-LC {BITRATE}bps 48 kHz mono ({codec})", **r}
    write_block(os.path.join(OUT, "engine.json"), block)
    total = sum(os.path.getsize(os.path.join(OUT, x)) for x in os.listdir(OUT))
    print("fallback:", json.dumps(block))
    print("m4a total", sum(sizes.values()), "B; audio folder", total, "B")
    return 0


if __name__ == "__main__":
    sys.exit(main())
