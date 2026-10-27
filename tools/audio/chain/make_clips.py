"""The listening clips through the game's real chain, loudness-matched, as MP3.

    uv run --python 3.12 --with numpy,scipy python -I tools/audio/chain/make_clips.py OUT_CLIPS_DIR [family ...]

1. scenario.py jobs for every family (AI families as EngineVoice with the race mode's options: trim 1, muffler 0.3,
   shiftDrop on, the scenario's gear and clutch-side rpm; the Probe as the player's CarAudio, unchanged).
2. render_chain.ts (headless Chrome, OfflineAudioContext) -> raw float32 per family.
3. Loudness matching: every clip gets the same A-weighted RMS over its 25 s (LAeq); the common target is the highest
   one at which every clip's peak stays at or under -1 dBFS. No limiter, no compression.
4. ffmpeg: MP3 128 kbps, 48 kHz mono. clips.json records each clip's raw LAeq, gain and final peak.
"""
import json
import os
import subprocess
import sys

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import scenario  # noqa: E402

SR = 48000
FFMPEG = "/opt/homebrew/bin/ffmpeg"


def a_sos():
    f1, f2, f3, f4 = 20.598997, 107.65265, 737.86223, 12194.217
    p = [-2 * np.pi * f1] * 2 + [-2 * np.pi * f2, -2 * np.pi * f3] + [-2 * np.pi * f4] * 2
    zd, pd, kd = signal.bilinear_zpk([0, 0, 0, 0], p, (2 * np.pi * f4) ** 2, SR)
    sos = signal.zpk2sos(zd, pd, kd)
    _, h = signal.sosfreqz(sos, [1000], fs=SR)
    sos[0, :3] /= abs(h[0])
    return sos


def laeq(x):
    y = signal.sosfilt(a_sos(), x)
    return 20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-12)


def main():
    out = os.path.abspath(sys.argv[1])
    tg = [a for a in sys.argv[2:] if a.startswith("--target=")]  # a fixed common target (re-rendering a few clips of a set)
    fams = [a for a in sys.argv[2:] if not a.startswith("--")]
    idx = json.load(open(os.path.join(ROOT, "public", "audio", "families", "index.json")))["families"]
    fams = fams or list(idx)
    work = os.path.join(ROOT, "tools", "audio", "cache", "clips_raw")
    os.makedirs(work, exist_ok=True)
    os.makedirs(out, exist_ok=True)
    jobs = [scenario.job(f, idx[f], shift_drop=True) for f in fams]
    jf = os.path.join(work, "jobs.json")
    json.dump(jobs, open(jf, "w"))
    subprocess.run(["npx", "tsx", "tools/audio/chain/render_chain.ts", jf, work], check=True, cwd=ROOT)
    raw = {f: np.fromfile(os.path.join(work, f + ".f32"), np.float32).astype(np.float64) for f in fams}
    la = {f: laeq(x) for f, x in raw.items()}
    pk = {f: 20 * np.log10(np.max(np.abs(x)) + 1e-12) for f, x in raw.items()}
    target = float(tg[0].split("=")[1]) if tg else min(-16.0, min(-1.0 - (pk[f] - la[f]) for f in fams))
    prev = os.path.join(out, "clips.json")
    old = json.load(open(prev)) if tg and os.path.exists(prev) else None
    rec = old if old else {"target_laeq_dbfs": round(target, 2), "method": "A-weighted RMS over the whole 25 s clip, one common target, "
           "the highest at which every peak stays <= -1 dBFS; no limiter", "clips": {}}
    rec["clips"] = rec.get("clips", {})
    for f in fams:
        tf = min(target, -1.0 - (pk[f] - la[f]))  # with a fixed --target a clip whose peak would pass -1 dBFS stays below it
        g = 10 ** ((tf - la[f]) / 20)
        y = (raw[f] * g).astype(np.float32)
        p = subprocess.run([FFMPEG, "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-c:a", "libmp3lame",
                            "-b:a", "128k", "-ar", str(SR), os.path.join(out, f + ".mp3")], input=y.tobytes(), check=True)
        rec["clips"][f] = {"raw_laeq_dbfs": round(la[f], 2), "gain_db": round(tf - la[f], 2),
                           "peak_dbfs": round(pk[f] + tf - la[f], 2), "laeq_dbfs": round(tf, 2), "bytes": os.path.getsize(os.path.join(out, f + ".mp3"))}
        print(f, rec["clips"][f], flush=True)
    json.dump(rec, open(os.path.join(out, "clips.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
