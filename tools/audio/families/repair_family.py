"""Round three (26 Oct 2026): replace contaminated bins of a shipped family from its clean real bins, without the source
audio (YouTube refuses new downloads here, and the round-two FLACs were dropped after each build).

    P="uv run --python 3.12 --with numpy,scipy,soundfile,matplotlib,webrtcvad-wheels,onnxruntime python -I"
    $P tools/audio/families/repair_family.py FAMILY BIN:LOAD [BIN:LOAD ...] [--donors BIN:LOAD,...]

Decodes the family's sprites, keeps every unlisted bin as it is (loop, tier, rpm, seam correlation, recorded source),
replaces each listed bin with a pitch-shifted copy of the nearest donor: a clean REAL loop (steady / sweep / idle,
not listed) of the same load, else the other load's (darkened when an on loop serves an off bin, the round-two rule),
nearest in pitch ratio, and writes the sprites and engine.json again through build_family.write_family (the
Opus sprites are re-encoded once more). --lp=FC low-passes the donor of a repaired on bin (a donor whose high band is gated in and out). Bins whose copy lands outside the quality.py ratio window are printed and stay
gate failures.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
import build_family as bf  # noqa: E402
import quality as q  # noqa: E402

SR = bf.SR


def main():
    fam = sys.argv[1]
    flagged = {(int(a.split(":")[0]), a.split(":")[1]) for a in sys.argv[2:] if ":" in a and not a.startswith("--")}
    lp_fc = next((float(a.split("=")[1]) for a in sys.argv if a.startswith("--lp=")), None)  # Hz: low-pass the donor on an on bin
    e, spr, meta, _ = q.load_family(fam)
    defs, _src = bf.load_defs(fam)
    BINS = [b["rpm"] for b in e["bins"]]
    final = {"on": {}, "off": {}}
    for b in e["bins"]:
        for ld in ("on", "off"):
            r = b[ld]
            lp = q.loop_of(spr[ld], r).copy()
            final[ld][b["rpm"]] = {"loop": lp, "tier": r["tier"], "rpm": r["rpm"], "rho": r.get("seam_corr") or 0.0,
                                   "tick": r.get("tick") or 0.0, "name": "", "t": 0.0, "source_text": r["source"]}
    maxd = next((float(a.split("=")[1]) for a in sys.argv if a.startswith("--maxdonor=")), 1e9)  # no donor above this bin

    def donor(ld, B):
        cands = []
        for dl in (ld, "off" if ld == "on" else "on"):
            for R, p in final[dl].items():
                if R > maxd or (R, dl) in flagged or p["tier"] not in bf.REAL_TIERS:
                    continue
                if dl == "off" and ld == "on":
                    continue  # an overrun loop does not stand in for a pull
                ratio = B / p["rpm"]
                cands.append((abs(np.log(ratio)) + (0.0 if dl == ld else 0.15), dl, R, ratio))
        lo, hi = q.GATES[ld]
        cands.sort(key=lambda c: (0 if lo <= c[3] <= hi else 1, c[0]))  # a copy inside the ratio window first
        return cands[0]
    orig = {k: dict(v) for k, v in ((ld, final[ld]) for ld in final)}
    out = {"on": dict(final["on"]), "off": dict(final["off"])}
    for (B, ld) in sorted(flagged):
        _, dl, R, ratio = donor(ld, B)
        p0 = final[dl][R]
        s_ = {"loop": p0["loop"].copy(), "rpm": p0["rpm"], "name": "", "t": 0.0, "bin": R}
        if dl == "on" and ld == "off":
            s_ = bf.darken({**s_, "long": np.tile(s_["loop"], 8)})
            s_["bin"] = R
        else:
            s_["long"] = np.tile(s_["loop"], 8)
            if lp_fc and ld == "on":
                s_ = bf.darken(s_, lp_fc)
                s_["bin"] = R
        need, tgt = bf.loop_need(B), bf.loop_target(B)
        qd = bf.pitch_shift(s_, B, max_len_s=tgt, min_len_s=need)
        how = "pitch-shifted" if dl == ld else f"from-{dl}"
        txt = (f"pitch-shifted from the {R} rpm bin (x{qd['ratio']:.3f}), round three repair of the contaminated {ld} loop; donor: {p0['source_text']}"
               if dl == ld else
               f"the {dl}-throttle {R} rpm loop{' darkened' if dl == 'on' else ''} (x{qd['ratio']:.3f}), round three repair; donor: {p0['source_text']}")
        qd.update({"tier": how, "source_text": txt, "bin": B, "from_load": dl})
        out[ld][B] = qd
        lo, hi = q.GATES[ld]
        print(f"{B} {ld} <- {dl} {R} x{qd['ratio']:.3f} {'IN' if lo <= qd['ratio'] <= hi else 'OUT of window'} ({how})")
    gap = e["levels"]["off_minus_on_db"]
    bf.write_family(fam, defs, {}, out, BINS, gap, e.get("main_order"), e.get("borrowed_load") or {}, sources=e["sources"], plot=False)


if __name__ == "__main__":
    main()
