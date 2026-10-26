"""Speech detector for engine loops and candidate segments (round two, 26 Oct 2026).

A narrated road-test video can leave a fragment of the driver's voice in a cut loop; the owner heard it as "weird
speech" in modern_i4_stock. Engine noise alone sets off a plain voice-activity detector, so the test runs on what is
NOT the engine: after the time-warp the engine repeats exactly once per engine cycle (2 crank revs), so the
cycle-synchronous average over the neighbouring cycles is the engine, and the residual (signal minus that average)
holds everything that does not repeat with the crank: speech, wind, road noise, cycle-to-cycle burble.

On the residual (resampled to 16 kHz, at the level it has when the whole signal sits at -20 dBFS RMS):
  vad      share of 30 ms frames that webrtcvad (mode 3, the strictest) calls speech
  pitch    share of 40 ms frames with a voice-like pitch: normalised autocorrelation > 0.55 at a lag of 2.5-12.5 ms
           (80-400 Hz) in the 70-1000 Hz band, in frames above the residual's median level
  voice    the residual's 300-3400 Hz level relative to the whole signal's, dB
  flux     median spectral flux of the residual's 300-3400 Hz band between 20 ms frames (formants move, wind does not)
A segment is speech when vad and pitch are both high (the thresholds in SPEECH_RULE were set on the shipped
round-one loops: see LEDGER.md round two).

webrtcvad comes from the `webrtcvad-wheels` package (the same Google WebRTC VAD as `webrtcvad`, prebuilt wheels).
"""
from __future__ import annotations

import os
import sys

import numpy as np
from scipy import signal

SR = 48000
SPEECH_RULE = {"silero_share": 0.08}
MODEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache", "silero", "silero_vad", "data",
                     "silero_vad.onnx")
_sess = None


def _silero():
    """The Silero VAD ONNX model (MIT licence), unpacked from the silero-vad wheel into tools/audio/cache/silero/ on
    first use: `pip download silero-vad --no-deps` into its own folder, only the .onnx file is read (onnxruntime runs
    the graph; nothing from the wheel is imported or executed)."""
    global _sess
    if _sess is None:
        if not os.path.exists(MODEL):
            import subprocess
            import zipfile
            dl = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(MODEL))), "dl_silero")
            os.makedirs(dl, exist_ok=True)
            subprocess.run([sys.executable, "-I", "-m", "pip", "download", "silero-vad==6.2.3", "--no-deps", "-d", dl, "-q"],
                           check=True)
            whl = [f for f in os.listdir(dl) if f.endswith(".whl")][0]
            with zipfile.ZipFile(os.path.join(dl, whl)) as z:
                z.extract("silero_vad/data/silero_vad.onnx", os.path.dirname(os.path.dirname(os.path.dirname(MODEL))))
        import onnxruntime as ort
        _sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    return _sess


def silero_probs(x16: np.ndarray) -> np.ndarray:
    """Speech probability per 32 ms window (512 samples at 16 kHz, with the model's 64-sample context)."""
    s = _silero()
    state = np.zeros((2, 1, 128), np.float32)
    ctx = np.zeros(64, np.float32)
    x = np.asarray(x16, np.float32)
    out = []
    sr = np.array(16000, np.int64)
    for i in range(0, len(x) - 511, 512):
        ch = np.concatenate([ctx, x[i:i + 512]])[None, :]
        p, state = s.run(None, {"input": ch, "state": state, "sr": sr})
        ctx = x[i + 448:i + 512]
        out.append(float(p[0, 0]))
    return np.array(out)


def cycle_residual(y: np.ndarray, rpm: float, k: int = 3, periodic: bool = False) -> np.ndarray:
    """y minus its engine-cycle-synchronous average over +-k cycles (fractional cycle length by linear interpolation).
    periodic=True treats y as one loop (circular shifts)."""
    m = SR * 120.0 / rpm
    n = len(y)
    idx = np.arange(n, dtype=np.float64)
    acc = np.zeros(n)
    cnt = np.zeros(n)
    for j in range(-k, k + 1):
        if j == 0:
            continue
        pos = idx + j * m
        if periodic:
            pos = np.mod(pos, n)
            i0 = np.floor(pos).astype(np.int64)
            fr = pos - i0
            acc += y[i0 % n] * (1 - fr) + y[(i0 + 1) % n] * fr
            cnt += 1
        else:
            ok = (pos >= 0) & (pos <= n - 2)
            i0 = np.floor(pos[ok]).astype(np.int64)
            fr = pos[ok] - i0
            acc[ok] += y[i0] * (1 - fr) + y[i0 + 1] * fr
            cnt[ok] += 1
    avg = np.where(cnt > 0, acc / np.maximum(cnt, 1), y)
    return y - avg


def _vad_share(x16: np.ndarray) -> float:
    import webrtcvad
    v = webrtcvad.Vad(3)
    fl = 480  # 30 ms at 16 kHz
    pcm = np.clip(x16 * 32767, -32768, 32767).astype(np.int16)
    n = len(pcm) // fl
    if n == 0:
        return 0.0
    hits = sum(v.is_speech(pcm[i * fl:(i + 1) * fl].tobytes(), 16000) for i in range(n))
    return hits / n


def _pitch_share(x16: np.ndarray) -> float:
    b = signal.sosfiltfilt(signal.butter(4, [70, 1000], "bandpass", fs=16000, output="sos"), x16)
    fl, hop = 640, 320
    n = (len(b) - fl) // hop + 1
    if n <= 0:
        return 0.0
    fr = np.stack([b[i * hop:i * hop + fl] for i in range(n)]) * np.hanning(fl)
    e = (fr ** 2).sum(1)
    loud = e >= np.median(e)
    lo, hi = 40, 200  # lags 2.5-12.5 ms
    hits = 0
    tot = 0
    for f, l in zip(fr, loud):
        if not l:
            continue
        tot += 1
        ac = np.correlate(f, f, "full")[fl - 1:]
        if ac[0] <= 0:
            continue
        # normalise by the overlap so long lags are not penalised
        r = ac[lo:hi] / ac[0] * fl / (fl - np.arange(lo, hi))
        if r.max() > 0.55:
            hits += 1
    return hits / max(1, tot)


def _band_db(x: np.ndarray, lo: float, hi: float) -> float:
    b = signal.sosfiltfilt(signal.butter(4, [lo, hi], "bandpass", fs=SR, output="sos"), x)
    return 10 * np.log10(np.mean(b ** 2) + 1e-20)


def _flux(x16: np.ndarray) -> float:
    f, t, Z = signal.stft(x16, 16000, nperseg=320, noverlap=0)
    band = (f >= 300) & (f <= 3400)
    S = np.log(np.abs(Z[band]) ** 2 + 1e-12)
    if S.shape[1] < 3:
        return 0.0
    return float(np.median(np.sqrt(np.mean(np.diff(S, axis=1) ** 2, axis=0))))


def speech_features(y: np.ndarray, rpm: float, periodic: bool = False) -> dict:
    """Features of y (48 kHz) at engine speed rpm. periodic=True: y is a loop (tiled to 3 s for the frame tests)."""
    y = np.asarray(y, np.float64)
    if periodic:
        res = cycle_residual(y, rpm, periodic=True)
        reps = int(np.ceil(3.0 * SR / len(y)))
        y_t, r_t = np.tile(y, reps), np.tile(res, reps)
    else:
        res = cycle_residual(y, rpm)
        y_t, r_t = y, res
    g = 10 ** (-20 / 20) / (np.sqrt(np.mean(y_t ** 2)) + 1e-12)
    r16 = signal.resample_poly(r_t * g, 1, 3)
    y16 = signal.resample_poly(y_t * g, 1, 3)
    pr = silero_probs(y16)
    pr_res = silero_probs(r16)
    return {"silero": round(float(pr.max()) if len(pr) else 0.0, 3),
            "silero_share": round(float(np.mean(pr > 0.5)) if len(pr) else 0.0, 3),
            "silero_res": round(float(pr_res.max()) if len(pr_res) else 0.0, 3),
            "vad": round(_vad_share(r16), 3), "pitch": round(_pitch_share(r16), 3),
            "voice": round(_band_db(r_t, 300, 3400) - _band_db(y_t, 300, 3400), 2), "flux": round(_flux(r16), 3)}


def is_speech(feat: dict) -> bool:
    """Speech when Silero hears it in at least 8 % of the 32 ms windows. Set on round one's loops (26 Oct 2026): clean
    engine loops reach at most 5 %, a synthetic voice mixed in at -6 dB re the loop reaches 78-92 % (median)."""
    return bool(feat["silero_share"] >= SPEECH_RULE["silero_share"])
