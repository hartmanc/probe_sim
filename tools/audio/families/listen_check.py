"""Objective stand-in for a listen test: decode each family's AAC fallback sprites and measure the on-throttle loop at
idle, mid and redline.

    python3 -I tools/audio/families/listen_check.py [FAMILY ...]     (default: every family)

There is no ear in the loop here. For each of the three bins the table gives: the loop's rpm, level (dB re full scale,
RMS), peak, spectral centroid (Hz), the share of power under 300 Hz, the strongest engine order (order 1 = crank rev)
and the firing order's share of the power in orders 0.5-12, the wrap step (largest sample jump at the loop seam over
the median jump: ~1 is seamless, > 6 clicks) and the off-throttle level relative to on.
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import build_family as bf  # noqa: E402
from common import ROOT, SR  # noqa: E402

BASE = os.path.join(ROOT, "public", "audio", "families")


def analyse(fam):
    d = os.path.join(BASE, fam)
    ej = json.load(open(os.path.join(d, "engine.json")))
    fb = ej.get("fallback")
    spr = {ld: bf.decode(os.path.join(d, fb[ld])) for ld in ("on", "off")}
    shift = fb.get("offset_s", 0.0)
    bins = ej["bins"]
    lo, hi = bins[0]["rpm"], bins[-1]["rpm"]
    pick = [min(bins, key=lambda b: abs(b["rpm"] - t)) for t in (ej["idle_rpm"], lo + 0.5 * (hi - lo), ej["redline_rpm"])]
    F = ej["cylinders"] / 2.0
    rows = []
    for b in pick:
        out = {"rpm": b["rpm"], "tier": b["on"]["tier"]}
        lv = {}
        for ld in ("on", "off"):
            r = b[ld]
            a = int(round((r["offset"] + shift) * SR))
            L = int(round(r["duration"] * SR))
            lp = spr[ld][a:a + L]
            lv[ld] = 20 * np.log10(np.sqrt(np.mean(lp ** 2)) + 1e-12)
            if ld == "off":
                continue
            # the player loops [a, a+L): the seam is lp[-1] -> lp[0]
            x = np.concatenate([lp[-64:], lp[:64]])
            jump = np.abs(np.diff(x))
            med = np.median(np.abs(np.diff(lp))) + 1e-12
            X = np.abs(np.fft.rfft(np.tile(lp, 4) * np.hanning(4 * L))) ** 2
            fr = np.fft.rfftfreq(4 * L, 1 / SR)
            f_rev = r["rpm"] / 60.0
            ords = np.arange(0.5, 12.01, 0.5)
            pw = np.array([X[np.abs(fr - o * f_rev) <= 0.04 * o * f_rev].sum() for o in ords])
            out.update({"rms_db": lv[ld], "peak_db": 20 * np.log10(np.max(np.abs(lp)) + 1e-12),
                        "centroid": float((fr * X).sum() / X.sum()), "lt300": float(X[fr < 300].sum() / X.sum()),
                        "top_order": float(ords[int(np.argmax(pw))]),
                        "fire_share": float(sum(pw[i] for i, o in enumerate(ords) if abs(o / F - round(o / F)) < 1e-6 and o >= F) / pw.sum()),
                        "seam": float(jump[63] / med)})
        out["off_minus_on"] = lv["off"] - lv["on"]
        rows.append(out)
    return rows


if __name__ == "__main__":
    fams = sys.argv[1:] or sorted(json.load(open(os.path.join(BASE, "index.json")))["families"])
    print("| Family | rpm (tier) | RMS dB | peak dB | centroid Hz | <300 Hz | top order | firing-ladder share | seam step | off-on dB |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for f in fams:
        if not os.path.exists(os.path.join(BASE, f, "engine_on.m4a")):
            continue
        for r in analyse(f):
            print(f"| {f} | {r['rpm']} ({r['tier']}) | {r['rms_db']:.1f} | {r['peak_db']:.1f} | {r['centroid']:.0f} | "
                  f"{100 * r['lt300']:.0f}% | {r['top_order']:g} | {100 * r['fire_share']:.0f}% | {r['seam']:.1f} | {r['off_minus_on']:.1f} |")
