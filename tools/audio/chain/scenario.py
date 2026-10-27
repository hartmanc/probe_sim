"""The listening scenario (round one's render.py, unchanged) plus the gear and the clutch-side rpm it implies, and the
job files for render_chain.ts.

    python3 -I tools/audio/chain/scenario.py JOBS.json [--shift-drop] [--physics TRACE.json] [family ...]

Scenario (25 s at 60 Hz): idle 1.5 s; first gear 1.2 x idle to redline over 4 s; upshift 0.25 s throttle off to
62 %; second to redline 5 s; upshift; third 62 % to 95 % over 6 s; lift to 60 % over 3 s; two downshifts with
0.3 s blips at 1.35 x; coast to idle 3 s. gear: 1, 2, 3, then 2 and 1 at the blips. boxRpm (the engine speed with the
clutch locked in the current gear): 62 % of the redline through each upshift (the car's speed is constant over
0.25 s), the scenario rpm everywhere else.
"""
import json
import os
import sys

import numpy as np

FPS = 60.0
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))


def scenario(idle, red):
    segs, marks = [], []
    t = 0.0

    def add(name, d, r0, r1, thr, gear, box=None):
        nonlocal t
        marks.append((name, round(t, 3), round(t + d, 3)))
        segs.append((d, r0, r1, thr, gear, box))
        t += d

    add("idle", 1.5, idle, idle, 0, 1)
    add("1st: full throttle", 4.0, 1.2 * idle, red, 1, 1)
    add("upshift 1", 0.25, red, 0.62 * red, 0, 2, 0.62 * red)
    add("2nd: full throttle", 5.0, 0.62 * red, red, 1, 2)
    add("upshift 2", 0.25, red, 0.62 * red, 0, 3, 0.62 * red)
    add("3rd: to 95%", 6.0, 0.62 * red, 0.95 * red, 1, 3)
    add("lift", 3.0, 0.95 * red, 0.60 * red, 0, 3)
    add("blip 1", 0.3, 0.60 * red * 1.35, 0.60 * red * 1.35, 1, 2)
    add("fall 1", 0.7, 0.60 * red * 1.35, 0.50 * red, 0, 2)
    add("blip 2", 0.3, 0.50 * red * 1.35, 0.50 * red * 1.35, 1, 1)
    add("fall 2", 0.7, 0.50 * red * 1.35, 0.40 * red, 0, 1)
    add("coast", 3.0, 0.40 * red, idle, 0, 1)
    n = int(round(t * FPS))
    rpm, thr, gear, box = np.zeros(n), np.zeros(n), np.zeros(n, int), np.zeros(n)
    for i in range(n):
        tt = i / FPS
        acc = 0.0
        for d, r0, r1, th, g, bx in segs:
            if tt < acc + d - 1e-9:
                u = (tt - acc) / d
                rpm[i] = r0 + (r1 - r0) * u
                thr[i], gear[i] = th, g
                box[i] = bx if bx is not None else rpm[i]
                break
            acc += d
        else:
            rpm[i], gear[i], box[i] = segs[-1][2], segs[-1][4], segs[-1][2]
    for nm, s, e in marks:  # the jump into each blip is ramped over 3 frames (as round one)
        if nm.startswith("blip"):
            i0 = int(round(s * FPS))
            prev = rpm[i0 - 1]
            for k in range(3):
                rpm[i0 + k] = prev + (rpm[i0 + 3] - prev) * (k + 1) / 4
                box[i0 + k] = rpm[i0 + k]
    return rpm, thr, gear, box, marks, t


def job(fam, entry, shift_drop=False, rpm=None, thr=None, gear=None, box=None, name=None):
    idle, red = entry["idle"], entry["redline"]
    if rpm is None:
        rpm, thr, gear, box, _, _ = scenario(idle, red)
    j = {"name": name or fam, "family": fam, "fps": FPS, "rpm": [round(float(x), 2) for x in rpm],
         "thr": [round(float(x), 4) for x in thr], "gear": [int(x) for x in gear], "boxRpm": [round(float(x), 2) for x in box],
         "idle": idle, "redline": red, "seed": 619}
    if fam == "mazda_kl_v6":
        j["engineUrl"] = None
    else:
        j["engineUrl"] = "audio/families/" + entry["engine"]
        j["opts"] = {"trim": 1, "muffler": 0.3, "redline": red, "idle": idle}
        if shift_drop:
            j["opts"]["shiftDrop"] = True
    return j


if __name__ == "__main__":
    out = sys.argv[1]
    args = sys.argv[2:]
    sd = "--shift-drop" in args
    phys = None
    if "--physics" in args:
        phys = args[args.index("--physics") + 1]
    fams = [a for a in args if not a.startswith("--") and a != phys]
    idx = json.load(open(os.path.join(ROOT, "public", "audio", "families", "index.json")))["families"]
    jobs = []
    for f in fams or list(idx):
        jobs.append(job(f, idx[f], sd))
    if phys:
        tr = json.load(open(phys))
        for key, fam in (("38", "modern_i4_stock"), ("41", "classic_v8_lowrev"), ("probe", "mazda_kl_v6")):
            r = tr[key]
            t = np.array(r["t"])
            n = int(t[-1] * FPS)
            ii = np.minimum((np.arange(n) / FPS * 1000).astype(int), len(t) - 1)
            rpm = np.array(r["rpm"])[ii]
            thr = np.array(r["thr"])[ii]
            gear = np.array(r["gear"])[ii]
            box = np.array(r.get("box", r["rpm"]))[ii]
            sl = slice(0, int(min(n, 9 * FPS)))
            e = dict(idx[fam])
            jobs.append(job(fam, e, sd, rpm[sl], thr[sl], gear[sl], box[sl], name=f"physics_{key}_{fam}"))
    json.dump(jobs, open(out, "w"))
    print(f"{len(jobs)} jobs -> {out}")
