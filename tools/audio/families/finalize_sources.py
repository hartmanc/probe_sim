"""After a build: record why each source is used and drop the ones that supplied no real bin.

    python3 -I finalize_sources.py FAMILY "why it fits the family"

Sets entry["why"] = <text> + the number of real bins it supplied. Entries with none are removed from sources.json
(and their cache files deleted); the family must then be rebuilt so the src numbering in engine.json matches.
"""
import json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__))
fam, why = sys.argv[1], sys.argv[2]
d = json.load(open(os.path.join(H, "..", "..", "..", "public", "audio", "families", fam, "engine.json")))
use = {}
for b in d["bins"]:
    for ld in ("on", "off"):
        x = b[ld]
        if x["tier"] in ("steady", "sweep"):
            use[re.match(r"(src\d+)", x["source"]).group(1)] = use.get(re.match(r"(src\d+)", x["source"]).group(1), 0) + 1
S = json.load(open(os.path.join(H, "sources.json")))
keep, dropped = [], []
live = [e for e in S[fam]["entries"] if not e.get("skip")]
for k, e in enumerate(live):
    n = use.get(f"src{k}", 0)
    if n == 0:
        dropped.append(e)
        continue
    e["why"] = f"{why}; supplies {n} real bins"
    e["notes"] = e.get("notes") or ""
    keep.append(e)
S[fam]["entries"] = keep
json.dump(S, open(os.path.join(H, "sources.json"), "w"), indent=1, ensure_ascii=False)
for e in dropped:
    f = os.path.join(H, e["file"])
    for p in (f, f[:-5] + ".json"):
        if os.path.exists(p):
            os.remove(p)
    print("dropped (no real bin):", e["title"])
print(fam, len(keep), "sources kept")
