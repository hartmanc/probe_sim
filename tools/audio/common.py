"""Shared helpers for the audio pipeline: source paths, audio extraction, logger loading and the time mapping.

Time frame: "camera epoch" = the GoPro's clock (Pacific wall time stored as if UTC, as in
starlink-go-pro/video/analysis/sync.py STARTS). Logger rows map onto it with  t_cam = t_logger + offset_s.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
from datetime import datetime

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
CACHE = os.path.join(HERE, "cache")
SRC = "/Users/cobyhartman/projects/starlink-go-pro"
PROXIES = os.path.join(SRC, "video", "proxies")
CLIPS = os.path.join(SRC, "video", "clips")
LOGGER = os.path.join(SRC, "LagunaData", "log_0e9892313a134bebabd0bf18dc429ac0.csv")  # the race (08:48-11:31)
SYNC_JSON = os.path.join(SRC, "video", "analysis", "sync.json")
FFMPEG = "/opt/homebrew/bin/ffmpeg"
SR = 48000
FIRES_PER_REV = 3  # even-fire V6, four-stroke: 6 cylinders / 2 revs

# Camera file start epochs, copied from video/analysis/sync.py STARTS (race files only)
STARTS = {"GL010045": 1791794721, "GL020045": 1791797727, "GL030045": 1791800763, "GL040045": 1791803768}
# Where the clips sit inside their source proxy, found by cross-correlating the audio (exact match, r = 1.000)
CLIP_SOURCE = {"03_hand_topspeed": ("GL030045", 510.0), "04_pass_fastback": ("GL030045", 1744.0),
               "07_pass_winged": ("GL030045", 992.0), "08_hudson": ("GL030045", 2879.0),
               "01_frustration": ("GL030045", 444.0)}
ALIGN_JSON = os.path.join(HERE, "alignment.json")


def audio_path(name: str) -> str:
    """Mono 48 kHz FLAC of a proxy (GL0x0045) or clip, extracted on first use into tools/audio/cache/."""
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, name + ".flac")
    if not os.path.exists(out):
        src = os.path.join(PROXIES, name + ".LRV") if name.startswith("GL") else os.path.join(CLIPS, name + ".mp4")
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", src, "-map", "0:a:0", "-vn", "-ac", "1", "-ar", str(SR),
                        "-c:a", "flac", out], check=True)
    return out


def load_audio(name: str, t0: float = 0.0, dur: float | None = None) -> np.ndarray:
    path = audio_path(name)
    start = int(round(t0 * SR))
    stop = None if dur is None else start + int(round(dur * SR))
    x, sr = sf.read(path, start=start, stop=stop, dtype="float32")
    assert sr == SR
    return x


def logger_offset() -> float:
    """Logger clock -> camera clock offset of the race logger file, from sync.json (yaw-rate match)."""
    return float(json.load(open(SYNC_JSON))["0e98"]["offset_s"])


def file_start(name: str) -> float:
    """Start of a race proxy on the logger-aligned clock. STARTS (camera media list, 1 s resolution) is off by a
    different constant per chapter file; align.py measures it from the engine harmonics (alignment.json)."""
    if os.path.exists(ALIGN_JSON):
        corr = json.load(open(ALIGN_JSON))["file_correction_s"].get(name)
        if corr is not None:
            return STARTS[name] - corr
    return float(STARTS[name])


def load_logger(offset: float | None = None) -> dict:
    """OBD rpm/throttle at their true read times (row time minus obd_age_s, one sample per new read) and the raw
    10 Hz IMU rows, all on the camera clock."""
    if offset is None:
        offset = logger_offset()
    obd_t, rpm, thr, imu_t, acc, gyro = [], [], [], [], [], []
    last_age = 1e9
    with open(LOGGER) as fh:
        for r in csv.DictReader(fh):
            t = datetime.fromisoformat(r["timestamp_utc"]).timestamp() + offset
            if r["accel_x_m_s2"] and r["gyro_x_rad_s"]:
                imu_t.append(t)
                acc.append([float(r[f"accel_{a}_m_s2"]) for a in "xyz"])
                gyro.append([float(r[f"gyro_{a}_rad_s"]) for a in "xyz"])
            if not r["rpm"] or not r["obd_age_s"]:
                continue
            age = float(r["obd_age_s"])
            if age < last_age:  # a fresh OBD read
                obd_t.append(t - age)
                rpm.append(float(r["rpm"]))
                thr.append(float(r["throttle_pct"]) if r["throttle_pct"] else np.nan)
            last_age = age
    return {"t": np.array(obd_t), "rpm": np.array(rpm), "thr": np.array(thr),
            "imu_t": np.array(imu_t), "acc": np.array(acc), "gyro": np.array(gyro), "offset": offset}


def file_for(t_cam: float) -> tuple[str, float] | None:
    """Which race proxy covers aligned time t, and the time inside it."""
    for name in STARTS:
        start = file_start(name)
        if 0 <= t_cam - start < 3011.0:
            return name, t_cam - start
    return None


def stft_mag(x: np.ndarray, nfft: int = 8192, hop: int = 480) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """|STFT| (freq x frames) with a Hann window; returns (freqs, frame centre times, mag)."""
    win = np.hanning(nfft).astype(np.float32)
    n = 1 + max(0, (len(x) - nfft) // hop)
    idx = np.arange(nfft)[None, :] + hop * np.arange(n)[:, None]
    frames = x[idx] * win
    mag = np.abs(np.fft.rfft(frames, axis=1)).T.astype(np.float32)
    return np.fft.rfftfreq(nfft, 1 / SR), (np.arange(n) * hop + nfft / 2) / SR, mag
