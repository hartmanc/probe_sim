"""Octave / order sanity check on a built family's loops (reads the shipped Ogg sprites).

    python3 -I tools/audio/families/qa_orders.py FAMILY

For each real (non pitch-shifted) bin and load, the loop's power at engine orders 0.5, 1, 1.5, ... 12 (order 1 =
crank rev) is summed in +-4 % windows. A correct label puts the strongest order at the firing order F = n/2 or one
of its multiples; a loop labelled an octave too high shows its strongest order at F/2, and one labelled too low at
2F. Prints a flag per bin: ok / low-octave? / high-octave? and the strongest order.
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


def check(fam):
    base = os.path.join(ROOT, "public", "audio", "families", fam)
    ej = json.load(open(os.path.join(base, "engine.json")))
    F = ej["cylinders"] / 2.0
    res = {}
    for load in ("on", "off"):
        spr = bf.decode(os.path.join(base, f"engine_{load}.ogg"))
        for b in ej["bins"]:
            r = b[load]
            if r["tier"] not in ("steady", "sweep"):
                continue
            a = int(round(r["offset"] * SR))
            lp = spr[a:a + int(round(r["duration"] * SR))]
            X = np.abs(np.fft.rfft(np.tile(lp, 4) * np.hanning(4 * len(lp)))) ** 2
            fr = np.fft.rfftfreq(4 * len(lp), 1 / SR)
            f_rev = r["rpm"] / 60.0
            orders = np.arange(0.5, 12.01, 0.5)
            pw = []
            for o in orders:
                m = np.abs(fr - o * f_rev) <= 0.04 * o * f_rev
                pw.append(X[m].sum())
            pw = np.array(pw)
            k = int(np.argmax(pw))
            top = orders[k]
            ratio = top / F
            ok = abs(ratio - round(ratio)) < 0.01 and round(ratio) >= 1
            flag = "ok" if ok else ("low-octave?" if ratio < 1 else "other")
            res[(load, b["rpm"])] = (top, flag)
    return res, F


if __name__ == "__main__":
    fam = sys.argv[1]
    res, F = check(fam)
    bad = {k: v for k, v in res.items() if v[1] != "ok"}
    print(f"{fam}: firing order {F:g}; {len(res) - len(bad)}/{len(res)} real bins have their strongest order on a multiple of it")
    for k, v in sorted(bad.items()):
        print("  ", k, "strongest order", v[0], v[1])
