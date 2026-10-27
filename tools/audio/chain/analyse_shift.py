"""Measure an upshift in a chain render: the audible pitch track (harmonic comb on the output), how long the note takes
to fall to the next gear, the on / off layer balance through it, and the ladder share (tonality) of the output.

    python3 -I tools/audio/chain/analyse_shift.py JOBS.json RENDER_DIR [name ...] [--plot OUT.png]
"""
import json
import os
import sys

import numpy as np
from scipy import signal

SR = 48000


def comb_track(x, rpm_in, fps, cyl, lo, hi, hop_s=0.005):
    nper = 4096
    hop = int(hop_s * SR)
    f, t, Z = signal.stft(x, SR, nperseg=nper, noverlap=nper - hop, boundary=None, padded=False)
    t = t  # centre times
    S = np.log(np.abs(Z) + 1e-9)
    S -= signal.medfilt2d(S, (31, 1))  # whiten along frequency
    S = np.maximum(S, 0)
    grid = np.exp(np.linspace(np.log(lo), np.log(hi), 300))
    F = cyl / 2.0
    orders = np.arange(0.5, 12.01, 0.5)
    w = np.where(np.isclose(np.mod(orders, F), 0) | np.isclose(np.mod(orders, F), F), 1.0, 0.25)
    df = f[1] - f[0]
    track = np.zeros(len(t))
    for i in range(len(t)):
        col = S[:, i]
        sc = np.zeros(len(grid))
        for o, ww in zip(orders, w):
            idx = np.clip(np.round(o * grid / 60 / df).astype(int), 0, len(col) - 1)
            sc += ww * (col[idx] - 0.5)
        track[i] = grid[int(np.argmax(sc))]
    return t, track


def ladder_share(x, rpm):
    X = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    f_rev = rpm / 60
    band = (fr > 30) & (fr < 6000)
    on = np.zeros_like(fr, bool)
    for o in np.arange(0.5, 6000 / f_rev, 0.5):
        on |= np.abs(fr - o * f_rev) <= 0.05 * f_rev
    return float(X[band & on].sum() / (X[band].sum() + 1e-20))


def load_trace(thr, fps):
    L, out = 0.0, []
    for th in thr:
        tau = 0.035 if th > L else 0.07
        L += (th - L) * (1 - np.exp(-1 / fps / tau))
        out.append(L)
    return np.array(out)


def analyse(job, x, cyl):
    fps = job["fps"]
    rpm = np.array(job["rpm"])
    gear = np.array(job["gear"])
    box = np.array(job.get("boxRpm") or job["rpm"])
    red = job["redline"]
    L = load_trace(job["thr"], fps)
    t, tr = comb_track(x, rpm, fps, cyl, 0.3 * red, 1.15 * red)
    rin = np.interp(t, np.arange(len(rpm)) / fps, rpm)
    shifts = []
    for i in range(1, len(gear)):
        if gear[i] > gear[i - 1] >= 1:
            t0 = i / fps
            k = min(len(box) - 1, i + int(0.6 * fps))
            land = float(box[min(len(box) - 1, i + 3)])
            r0 = float(rpm[i - 1])
            m = (t >= t0 - 0.05) & (t <= t0 + 1.0)
            tt, aa, ii = t[m] - t0, tr[m], rin[m]
            # median-smooth the audible track (comb jitter)
            aa_s = signal.medfilt(aa, 9)

            def reach(v):
                j = np.nonzero(v <= land * 1.04)[0]
                return float(tt[j[0]]) if len(j) else float("nan")
            mid = (aa_s < r0 * 0.96) & (aa_s > land * 1.04)
            seg = x[int(t0 * SR):int((t0 + 0.4) * SR)]
            j0, j1 = i, min(len(L) - 1, i + int(0.6 * fps))
            shifts.append({"t": round(t0, 3), "from_rpm": round(r0), "landing_rpm": round(land),
                           "input_reaches_landing_s": reach(ii), "audible_reaches_landing_s": reach(aa_s),
                           "audible_glide_s": round(float(mid.sum() * (t[1] - t[0])), 3),
                           "off_weight_max": round(float(np.cos(L[j0:j1] * np.pi / 2).max()), 3),
                           "on_weight_during_glide": round(float(np.mean(np.sin(L[j0:j1] * np.pi / 2))), 3),
                           "ladder_share_0_400ms": round(ladder_share(seg, float(np.median(rpm[i:i + int(0.4 * fps)]))), 3)})
    ok = rin > 0.35 * red
    err = np.median(np.abs(tr[ok] - rin[ok]) / rin[ok])
    return {"name": job["name"], "pitch_err_median": round(float(err), 4), "shifts": shifts[:3], "_t": t, "_tr": tr, "_rin": rin}


if __name__ == "__main__":
    jobs = {j["name"]: j for j in json.load(open(sys.argv[1]))}
    rd = sys.argv[2]
    args = sys.argv[3:]
    plot = None
    if "--plot" in args:
        plot = args[args.index("--plot") + 1]
        args = [a for a in args if a not in ("--plot", plot)]
    names = args or list(jobs)
    idx = json.load(open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "public", "audio", "families", "index.json")))["families"]
    res = []
    for n in names:
        j = jobs[n]
        x = np.fromfile(os.path.join(rd, n + ".f32"), np.float32).astype(np.float64)
        r = analyse(j, x, idx[j["family"]]["cylinders"])
        res.append(r)
        print(json.dumps({k: v for k, v in r.items() if not k.startswith("_")}))
    if plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, axs = plt.subplots(len(res), 1, figsize=(12, 3 * len(res)))
        axs = np.atleast_1d(axs)
        for ax, r in zip(axs, res):
            ax.plot(r["_t"], signal.medfilt(r["_tr"], 9), lw=0.8, label="audible (comb)")
            ax.plot(r["_t"], r["_rin"], lw=0.8, label="input rpm")
            ax.set_title(r["name"], fontsize=9)
            ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(plot, dpi=70)
