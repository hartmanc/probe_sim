"""Unseeded engine-rpm tracking from audio alone (no logger), for the AI cars' engine families.

Per 25 ms frame (170 ms Hann window, computed on a 12 kHz decimated copy):
  1. whitened log spectrum: dB minus a running median over ~±60 Hz, half-wave rectified (only peaks count).
  2. harmonic comb over the engine's order ladder, orders 0.5·k of crank rotation, weighted for the layout:
     the firing order F = cylinders / 2 (four-stroke: an I4 fires 2 per rev, an even-fire V6 or I6 3, a V8 4)
     and its multiples carry weight 1; the half-firing ladder F/2·j (bank pulses of a V or flat engine, the
     odd-fire beat) carries `w_half`; the other half orders `w_other`. The score is the weighted tooth level minus
     the level midway between the main teeth (the comb contrast), searched over 700–8500 rpm on a 0.4 % grid.
  3. dynamic programming (Viterbi) over the grid for continuity: free within ±150 rpm per frame, a quadratic
     penalty beyond, jumps capped at ±18 % per frame.
  3b. an optional weak log-normal rpm prior (track footage: 0.65 × redline) settles octave ambiguity.
  3c. octave-slip repair: a x1.75 step within 0.4 s is impossible for an engine, so the path is split there and
      each piece takes the octave that continues its most confident neighbour.
  4. confidence = the chosen candidate's comb contrast (dB) and its margin over the best candidate an octave
     away (catches octave errors).
  5. load label: on = accelerating under load or loud/bright for its rpm, off = decelerating and quiet/dark
     (overrun), 0 = unknown (shifts, steady cruise that is not clearly either, low confidence).

Run directly to validate on the Probe's own footage against the logger-seeded tracker (tools/audio/cache):
    uv run --python 3.12 --with numpy,scipy,soundfile,matplotlib python -I tools/audio/families/track_unseeded.py
"""

from __future__ import annotations

import os
import sys

import numpy as np
from scipy import ndimage, signal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from common import SR  # noqa: E402

DEC = 4                      # 48 kHz -> 12 kHz for the analysis
FS = SR // DEC
NWIN, NFFT, HOP = 2048, 4096, 300   # 170 ms window, zero-padded x2, 25 ms hop
FRAME = HOP / FS
RPM_MIN, RPM_MAX, GRID_STEP = 700.0, 8500.0, 0.004
FMIN, FMAX = 25.0, 1500.0    # comb teeth band (Hz): the same band for every candidate, so dense (low-rpm) combs
                             # are not favoured by covering only the strong low orders


def layout_weights(cylinders: int, fire: str, layout: str = "inline"):
    """Orders (0.5·k), their weights, the main ladder step (orders) and the midpoint orders for the contrast."""
    F = cylinders / 2.0
    main = F if (fire == "even" and layout == "inline") else F / 2.0
    if layout == "v" and cylinders == 8:
        # cross-plane V8: each bank fires unevenly, so orders 1 and 2 (the burble) are often stronger than the
        # firing order 4 in onboard recordings; a ladder of 2 then loses to rpm/2 or rpm/4 (seen on the Camaros)
        main = 1.0
    if cylinders <= 2:
        main = 0.5
    w_half = 0.25 if main == F else 0.7
    w_other = 0.08 if fire == "even" else 0.25
    orders = np.arange(1, 257) * 0.5
    w = np.full(len(orders), w_other)
    w[np.isclose(np.mod(orders, main), 0) | np.isclose(np.mod(orders, main), main)] = w_half
    w[np.isclose(np.mod(orders, F / 2.0), 0) | np.isclose(np.mod(orders, F / 2.0), F / 2.0)] = max(w_half, 0.85 if main < F / 2 else w_half)
    w[np.isclose(np.mod(orders, F), 0) | np.isclose(np.mod(orders, F), F)] = 1.0
    # the lowest orders are weak in most recordings (mic / codec high-pass): taper below order 1
    w[orders < 1.0] *= 0.5
    mids = np.arange(0, 1024) * main + main / 2.0
    mids = mids[mids <= orders[-1]]
    return orders, w, main, mids


def analysis_spectrum(x: np.ndarray):
    """Decimate to 12 kHz, |STFT| in dB, whitened. Returns (freqs, frame times, whitened dB [frames x bins],
    band levels dict)."""
    y = signal.resample_poly(x.astype(np.float64), 1, DEC)
    win = np.hanning(NWIN)
    n = 1 + max(0, (len(y) - NWIN) // HOP)
    freqs = np.fft.rfftfreq(NFFT, 1 / FS)
    kmax = int(np.searchsorted(freqs, 4200))
    D = np.empty((n, kmax), np.float32)
    for j0 in range(0, n, 2000):
        j1 = min(n, j0 + 2000)
        idx = np.arange(NWIN)[None, :] + HOP * np.arange(j0, j1)[:, None]
        D[j0:j1] = np.abs(np.fft.rfft(y[idx] * win, NFFT, axis=1))[:, :kmax]
    P = D.astype(np.float64) ** 2
    bands = {}
    for name, lo, hi in (("lo", 100, 1000), ("hi", 1000, 4000), ("all", 50, 4000)):
        b = (freqs[:kmax] >= lo) & (freqs[:kmax] < hi)
        bands[name] = 10 * np.log10(P[:, b].sum(1) + 1e-12)
    L = 20 * np.log10(D + 1e-9)
    df = freqs[1]
    med = ndimage.median_filter(L, size=(1, int(round(120 / df)) | 1), mode="nearest")
    W = np.maximum(L - med, 0.0).astype(np.float32)
    t = (np.arange(n) * HOP + NWIN / 2) / FS
    return freqs[:kmax], t, W, bands


def rpm_grid(rpm_max: float = RPM_MAX):
    return RPM_MIN * (1 + GRID_STEP) ** np.arange(int(np.log(rpm_max / RPM_MIN) / np.log1p(GRID_STEP)) + 1)


def comb_scores(W: np.ndarray, freqs: np.ndarray, grid: np.ndarray, cylinders: int, fire: str, layout: str,
                cost_db: float = 2.5, half_cost: float = 0.25, beta: float = 0.3, fmin: float = FMIN):
    """Per frame x grid rpm: the comb score used for tracking and the comb contrast (dB) used as confidence.

    score = sum over teeth in the fixed band of w·(W − c), c = the frame's mean whitened level + cost_db. An empty
    tooth costs c, so a sub-multiple of the true rpm (a denser comb, half its teeth empty) loses; a weak but real
    peak (W > c) still adds, so a multiple of the true rpm (a sparser comb that skips the weak half orders) loses
    too. contrast = mean tooth level − mean level midway between the main-ladder teeth."""
    orders, w, main, mids = layout_weights(cylinders, fire, layout)
    df = freqs[1]
    nb = W.shape[1]
    band = (freqs > FMIN) & (freqs < FMAX)
    c = (W[:, band].mean(1) + cost_db)[:, None].astype(np.float32)

    def sample(order_list, weights, centred: bool, cost_scale=None):
        f = grid[None, :] / 60.0 * order_list[:, None]          # [orders x grid]
        ok = (f < min(FMAX, freqs[-1] - 2 * df)) & (f > fmin)
        fb = np.where(ok, f / df, 0.0)
        i0 = np.floor(fb).astype(np.int64)
        fr = (fb - i0).astype(np.float32)
        wt = (weights[:, None] * ok).astype(np.float32)
        acc = np.zeros((W.shape[0], len(grid)), np.float32)
        for k in range(len(order_list)):
            if not ok[k].any():
                continue
            a = np.clip(i0[k], 0, nb - 2)
            # max of the two neighbouring bins tolerates small rpm grid / smear errors
            v = np.maximum(W[:, a], W[:, a + 1]) * 0.6 + (W[:, a] * (1 - fr[k]) + W[:, a + 1] * fr[k]) * 0.4
            acc += ((v - c * (1.0 if cost_scale is None else cost_scale[k])) if centred else v) * wt[k]
        return acc, wt.sum(0) + 1e-6
    # an empty tooth on the weaker (half / other) orders costs less than an empty firing-order tooth
    s_teeth, _ = sample(orders, w, True, np.where(w >= 1.0, 1.0, half_cost))
    main_orders = np.arange(1, 1024) * main
    main_orders = main_orders[main_orders <= orders[-1]]
    t_main, n_main = sample(main_orders, np.ones(len(main_orders)), False)
    t_mid, n_mid = sample(mids, np.ones(len(mids)), False)
    contrast = t_main / n_main - t_mid / n_mid
    return s_teeth / 10.0 + beta * contrast, contrast, main


def viterbi(S: np.ndarray, grid: np.ndarray, free_rpm: float = 150.0, k_pen: float = 3.0, max_jump: float = 0.18):
    """Best path maximising sum(score) - transition penalty. Penalty for |Δ| > free_rpm: k_pen·((|Δ|-free)/free)^2."""
    n, m = S.shape
    dmax = int(np.ceil(np.log1p(max_jump) / np.log1p(GRID_STEP)))
    # PEN[i, k]: penalty for arriving at state i from state i + k - dmax
    src_idx = np.arange(m)[:, None] + np.arange(-dmax, dmax + 1)[None, :]
    valid = (src_idx >= 0) & (src_idx < m)
    jump = np.abs(grid[:, None] - grid[np.clip(src_idx, 0, m - 1)])
    PEN = np.where(valid, k_pen * np.maximum(0.0, (jump - free_rpm) / free_rpm) ** 2, np.inf)
    back = np.zeros((n, m), np.int16)
    acc = S[0].astype(np.float64).copy()
    pad = np.full(dmax, -np.inf)
    for j in range(1, n):
        win = np.lib.stride_tricks.sliding_window_view(np.r_[pad, acc, pad], 2 * dmax + 1)  # [m, 2dmax+1]
        v = win - PEN
        k = np.argmax(v, axis=1)
        acc = v[np.arange(m), k] + S[j]
        acc -= acc.max()
        back[j] = k - dmax
    path = np.zeros(n, np.int64)
    path[-1] = int(np.argmax(acc))
    for j in range(n - 1, 0, -1):
        path[j - 1] = path[j] + back[j, path[j]]
    return path


def fix_octave_segments(rpm: np.ndarray, conf: np.ndarray, jump: float = 1.75, span: int = 16,
                        rpm_min: float = RPM_MIN, rpm_max: float = RPM_MAX) -> np.ndarray:
    """An engine cannot change speed by x1.75 within 0.4 s (an upshift drop is ~x1.3-1.4, a rev-match blip less),
    so such a step in the Viterbi path is an octave slip. Split the path at the middle of each such transition; the
    segment with the most confidence keeps its octave and the others take the factor (x0.5, x1, x2) that best
    continues their already-fixed neighbours."""
    r = rpm.astype(np.float64).copy()
    if len(r) <= span:
        return rpm
    ratio = np.abs(np.log(r[span:] / r[:-span]))
    mark = np.zeros(len(r), bool)
    mark[:-span] = ratio > np.log(jump)
    d = np.diff(np.r_[0, mark.astype(np.int8), 0])
    cuts = [(s + e + span) // 2 for s, e in zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0])]
    cuts = [c for c in cuts if 0 < c < len(r)]
    if not cuts:
        return rpm
    edges = np.r_[0, cuts, len(r)]
    segs = list(zip(edges[:-1], edges[1:]))
    weight = [float(np.clip(conf[a:b], 0, None).sum()) for a, b in segs]
    fixed = {int(np.argmax(weight)): 1.0}
    while len(fixed) < len(segs):
        best = None
        for i, (a, b) in enumerate(segs):
            if i in fixed:
                continue
            # compare the levels just outside the transition zone (the cut sits mid-transition)
            w = 20
            for nb, side in ((i - 1, "start"), (i + 1, "end")):
                if nb in fixed and 0 <= nb < len(segs):
                    na, nbb = segs[nb]
                    if side == "start":
                        own = r[min(b - 1, a + span // 2): min(b, a + span // 2 + w)]
                        other = r[max(na, nbb - span // 2 - w): max(na + 1, nbb - span // 2)]
                    else:
                        own = r[max(a, b - span // 2 - w): max(a + 1, b - span // 2)]
                        other = r[min(nbb - 1, na + span // 2): min(nbb, na + span // 2 + w)]
                    target = float(np.median(other)) * fixed[nb]
                    lvl = float(np.median(own))
                    f = min((0.5, 1.0, 2.0), key=lambda f: abs(np.log(lvl * f / target)))
                    # flip only a clear octave step that the flip closes, and never out of the search range
                    if (abs(np.log(lvl / target)) < np.log(1.6) or abs(np.log(lvl * f / target)) > np.log(1.25)
                            or not (rpm_min * 0.9 <= np.percentile(r[a:b], 5) * f)
                            or np.percentile(r[a:b], 95) * f > rpm_max * 1.02):
                        f = 1.0
                    cand = (-weight[i], i, f)
                    if best is None or cand < best:
                        best = cand
        if best is None:
            break
        fixed[best[1]] = best[2]
    for i, (a, b) in enumerate(segs):
        r[a:b] *= fixed.get(i, 1.0)
    return r.astype(rpm.dtype)


def track(x: np.ndarray, cylinders: int, fire: str = "even", layout: str = "inline", rpm_max: float = RPM_MAX,
          prior_rpm: float | None = None, prior_w: float = 1.5, **comb_kw) -> dict:
    """Track rpm in mono 48 kHz audio x. Returns per-frame arrays: t, rpm, conf (comb contrast, dB),
    octave_margin (dB), load (+1 on, -1 off, 0 unknown), slope (rpm/s), level/tilt residuals."""
    freqs, t, W, bands = analysis_spectrum(x)
    grid = rpm_grid(rpm_max)
    S, C, main = comb_scores(W, freqs, grid, cylinders, fire, layout, **comb_kw)
    if prior_rpm:
        # weak log-normal prior: when every half order is present the comb cannot tell rpm from rpm/2 by itself
        # (open-header V8s); a factor 2 away from the prior costs 0.72 at prior_w 1.5
        S = S - (prior_w * np.log(grid / prior_rpm) ** 2)[None, :].astype(np.float32)
    path = viterbi(S, grid)
    rows = np.arange(len(path))
    rpm = grid[path]
    # parabolic refinement on the grid
    i = np.clip(path, 1, len(grid) - 2)
    a, b, c = S[rows, i - 1], S[rows, i], S[rows, i + 1]
    den = a - 2 * b + c
    d = np.where(np.abs(den) > 1e-6, 0.5 * (a - c) / np.where(den == 0, 1, den), 0.0)
    rpm = grid[i] * (1 + GRID_STEP) ** np.clip(d, -1, 1)
    conf = C[rows, path].astype(np.float32)
    rpm = fix_octave_segments(rpm, conf, rpm_max=rpm_max)
    # octave check: best score within ±3 % of rpm/2 and rpm·2
    oct_best = np.full(len(path), -np.inf)
    for fac in (0.5, 2.0):
        j = np.searchsorted(grid, rpm * fac)
        for dd in range(-7, 8):
            jj = np.clip(j + dd, 0, len(grid) - 1)
            v = np.where((j + dd >= 0) & (j + dd < len(grid)), S[rows, jj], -np.inf)
            oct_best = np.maximum(oct_best, v)
    margin = (S[rows, path] - oct_best).astype(np.float32)
    out = {"t": t, "rpm": rpm.astype(np.float32), "conf": conf, "octave_margin": margin, "main_order": main}
    out.update(load_label(t, out["rpm"], conf, bands))
    return out


def load_label(t, rpm, conf, bands) -> dict:
    """On/off throttle from rpm slope plus loudness and spectral tilt relative to their rpm trend."""
    fs = 1 / (t[1] - t[0])
    r = signal.savgol_filter(rpm.astype(np.float64), 9, 2)          # ±0.1 s
    slope = signal.savgol_filter(rpm.astype(np.float64), 21, 2, deriv=1) * fs   # ±0.25 s
    lev = signal.medfilt(bands["all"], 11)
    tilt = signal.medfilt(bands["hi"] - bands["lo"], 11)
    good = conf > np.percentile(conf, 30)
    def resid(v):
        if good.sum() < 20:
            return v - np.median(v)
        p = np.polyfit(np.log(r[good]), v[good], 1)
        e = v - np.polyval(p, np.log(r))
        return e / (np.std(e[good]) + 1e-6)
    zl, zt = resid(lev), resid(tilt)
    loud = 0.65 * zl + 0.35 * zt
    load = np.zeros(len(rpm), np.int8)
    shift = slope < -3500                                            # clutch-in shift drop / blip
    on = ((slope > 120) & (loud > -0.4)) | ((np.abs(slope) <= 120) & (loud > 0.8))
    off = ((slope < -120) & (loud < 0.4)) | ((np.abs(slope) <= 120) & (loud < -1.0))
    load[on] = 1
    load[off & ~on] = -1
    load[shift | (slope > 6000)] = 0
    load = signal.medfilt(load.astype(np.float64), 13).astype(np.int8)   # ±0.15 s
    # a label must hold for ≥ 0.2 s
    k = max(1, int(round(0.2 * fs)))
    for val in (1, -1):
        m = load == val
        d = np.diff(np.r_[0, m.astype(np.int8), 0])
        for s, e in zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]):
            if e - s < k:
                load[s:e] = 0
    return {"load": load, "slope": slope.astype(np.float32), "loud": loud.astype(np.float32)}


# ---------------------------------------------------------------- validation on the Probe's own footage

def validate_probe(t0: float = 900.0, dur: float = 120.0, rpm_max: float = RPM_MAX, plot: bool = True, **kw):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from common import CACHE, load_audio
    name = "GL030045"
    x = load_audio(name, t0, dur)
    res = track(x, 6, "even", "v", rpm_max=rpm_max, **kw)
    ref = dict(np.load(os.path.join(CACHE, f"track_{name}.npz")))
    sel = (ref["t"] >= t0) & (ref["t"] <= t0 + dur)
    rt = ref["t"][sel] - t0
    ra = np.interp(res["t"], rt, ref["rpm_a"][sel])
    rl = np.interp(res["t"], rt, ref["rpm_l"][sel])
    thr = np.interp(res["t"], rt, ref["thr"][sel])
    ok = np.isfinite(ra)
    err = np.abs(res["rpm"] - ra)[ok]
    errl = np.abs(res["rpm"] - rl)[np.isfinite(rl)]
    hc = ok & (res["conf"] > np.percentile(res["conf"], 25))
    lab = res["load"]
    on_ok = np.mean(thr[lab == 1] >= 50) if (lab == 1).any() else np.nan
    off_ok = np.mean(thr[lab == -1] <= 20) if (lab == -1).any() else np.nan
    stats = {"slice": f"{name} {t0:.0f}-{t0 + dur:.0f} s", "median_err_vs_seeded": float(np.median(err)),
             "p90_err_vs_seeded": float(np.percentile(err, 90)),
             "frac_within_150": float(np.mean(err < 150)),
             "median_err_vs_logger": float(np.median(errl)),
             "median_err_top75conf": float(np.median(np.abs(res["rpm"] - ra)[hc])),
             "on_label_frac": float(np.mean(lab == 1)), "off_label_frac": float(np.mean(lab == -1)),
             "on_label_precision(thr>=50)": float(on_ok), "off_label_precision(thr<=20)": float(off_ok)}
    if not plot:
        return stats
    fig, ax = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
    ax[0].plot(res["t"], ra, color="0.6", lw=2, label="logger-seeded comb (cache)")
    ax[0].plot(res["t"], res["rpm"], color="C3", lw=0.8, label="unseeded comb + DP")
    ax[0].set_ylabel("rpm"); ax[0].legend(fontsize=8)
    ax[0].set_title(f"Unseeded tracker on the Probe footage: median |err| {stats['median_err_vs_seeded']:.0f} rpm, "
                    f"p90 {stats['p90_err_vs_seeded']:.0f}")
    ax[1].plot(res["t"], res["conf"], lw=0.7, label="comb contrast (dB)")
    ax[1].plot(res["t"], res["octave_margin"], lw=0.7, label="octave margin (score)")
    ax[1].legend(fontsize=8)
    ax[2].plot(res["t"], thr, color="0.5", label="logger throttle %")
    ax[2].plot(res["t"], 50 + 40 * lab, color="C2", lw=0.8, label="audio load label (90 on / 10 off)")
    ax[2].legend(fontsize=8); ax[2].set_xlabel("s")
    fig.tight_layout()
    os.makedirs(os.path.join(HERE, "previews"), exist_ok=True)
    fig.savefig(os.path.join(HERE, "previews", "probe_validation.png"), dpi=70)
    return stats


if __name__ == "__main__":
    import json
    import time
    t_start = time.time()
    st = validate_probe(*(float(a) for a in sys.argv[1:3]))
    st["seconds"] = round(time.time() - t_start, 1)
    print(json.dumps(st, indent=1))
