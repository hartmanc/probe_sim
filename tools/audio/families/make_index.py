"""Write public/audio/families/index.json from families.json, the built families and the field's identity.json.

    uv run --python 3.12 python -I tools/audio/families/make_index.py

index.json = {
  version, base: "audio/families/",
  families: {id: {cylinders, layout, redline, idle, engine, sprites, real_bins}}   (built families only, + the Probe's set),
  aliases:  [[regex, id, {rpm_scale?, trim?}], ...]   tried in order, case-insensitive, on "<engine.family> <make> <model>",
  fallback: [{cylinders, layout, family}], default: id,
  muffler:  [[regex over engine.exhaust_note, 0..1], ...], muffler_default,
  cars:     {"<number>": {family, trim, muffler, rpm_scale, redline, engine}}   precomputed for the current field
}
"""
from __future__ import annotations

import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "public", "audio", "families")
LAYOUT = {"I": "inline", "V": "v", "flat": "flat", "H": "flat", "B": "flat"}


def layout_of(s: str | None) -> str | None:
    if not s:
        return None
    m = re.match(r"(flat|[IVHB])", s, re.I)
    return LAYOUT.get(m.group(1) if m.group(1).lower() != "flat" else "flat", None) if m else None


def main(check: bool = False):
    F = json.load(open(os.path.join(HERE, "families.json")))
    fams = {}
    for fid, d in F["families"].items():
        ej = os.path.join(OUT, fid, "engine.json")
        if not os.path.exists(ej) and not check:
            continue
        idx = json.load(open(ej)) if os.path.exists(ej) else {}
        fams[fid] = {"cylinders": d["cylinders"], "layout": d["layout"], "redline": d["redline_rpm"],
                     "idle": d["idle_rpm"], "engine": f"{fid}/engine.json",
                     "sprites": {"on": f"{fid}/engine_on.ogg", "off": f"{fid}/engine_off.ogg"},
                     "real_bins": idx.get("real_bins"), "character": d.get("character")}
    p = F["probe"]
    fams[p["id"]] = {"cylinders": p["cylinders"], "layout": p["layout"], "redline": p["redline_rpm"],
                     "idle": p["idle_rpm"], "engine": p["engine"], "sprites": p["sprites"], "note": p["note"]}
    built = set(fams)
    default = F["default"] if F["default"] in built else sorted(built - {p["id"]})[0] if len(built) > 1 else p["id"]

    def resolve(engine_family: str, make: str, model: str, cyl: int | None, lay: str | None):
        s = f"{engine_family} {make} {model}"
        for a in F["aliases"]:
            if re.search(a[0], s, re.I) and a[1] in built:
                return a[1], (a[2] if len(a) > 2 else {})
        for f in F["fallback"]:
            if f["cylinders"] == cyl and (lay is None or f["layout"] == lay) and f["family"] in built:
                return f["family"], {}
        for f in F["fallback"]:
            if f["cylinders"] == cyl and f["family"] in built:
                return f["family"], {}
        return default, {}

    def muffler(note: str | None) -> float:
        for rx, v in F["muffler"]:
            if note and re.search(rx, note, re.I):
                return v
        return F["muffler_default"]

    cars = {}
    ident = json.load(open(os.path.join(ROOT, "public", "cars", "field", "identity.json")))
    for c in ident:
        e = c.get("engine") or {}
        fam, ov = resolve(e.get("family") or "", c.get("make") or "", c.get("model") or "", e.get("cylinders"),
                          layout_of(e.get("layout")))
        h = int(hashlib.sha1(str(c["number"]).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
        cars[str(c["number"])] = {"family": fam, "trim": round(ov.get("trim", 0.97 + 0.06 * h), 4),
                                  "muffler": muffler(e.get("exhaust_note")), "rpm_scale": ov.get("rpm_scale", 1.0),
                                  "redline": e.get("redline_rpm"), "engine": e.get("family")}
    index = {"version": 1, "base": "audio/families/", "families": fams, "aliases": F["aliases"],
             "fallback": F["fallback"], "default": default, "muffler": F["muffler"],
             "muffler_default": F["muffler_default"], "cars": cars}
    os.makedirs(OUT, exist_ok=True)
    if not check:
        json.dump(index, open(os.path.join(OUT, "index.json"), "w"), indent=1)
    by = {}
    for n, c in cars.items():
        by.setdefault(c["family"], []).append(n)
    for f, ns in sorted(by.items()):
        print(f"{f:22s} {len(ns):2d}  {' '.join(ns)}")


def refresh_real_bins():
    """Update only each family's real_bins in index.json from its engine.json (ids, aliases, fallback, default and the
    per-car rows stay byte for byte as they were, so familyFor assigns every car as before)."""
    p = os.path.join(OUT, "index.json")
    idx = json.load(open(p))
    for fid, f in idx["families"].items():
        ej = os.path.join(OUT, f["engine"])
        if "real_bins" in f and os.path.exists(ej):
            f["real_bins"] = json.load(open(ej))["real_bins"]
    json.dump(idx, open(p, "w"), indent=1)


if __name__ == "__main__":
    import sys
    if "--real-bins-only" in sys.argv:
        refresh_real_bins()
        raise SystemExit(0)
    main("--check" in sys.argv)  # --check: map the field as if every family were built, write nothing
