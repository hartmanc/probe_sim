"""After a build: record why each source is used and drop the ones that supplied no real bin.

    python3 -I finalize_sources.py FAMILY "why it fits the family"

Sets entry["why"] = <text> + the number of real bins it supplied. Entries with none are marked skip (their audio deleted);
src numbering keeps the original slots, so no re-track is needed. Rebuild afterwards so engine.json lists only the used sources.
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
for k, e in enumerate(S[fam]["entries"]):   # k is the src number engine.json uses (skipped entries keep their slot)
    if e.get("skip"):
        continue
    n = use.get(f"src{k}", 0)
    if n == 0:
        e["skip"] = True
        e["skip_reason"] = "supplied no real bin once the octave guard and the candidate scoring had run; not shipped"
        dropped.append(e)
        continue
    e["why"] = f"{why}; supplies {n} real bins"
    keep.append(e)
json.dump(S, open(os.path.join(H, "sources.json"), "w"), indent=1, ensure_ascii=False)
for e in dropped:
    f = os.path.join(H, e["file"])
    if os.path.exists(f):
        os.remove(f)   # the downloaded audio; the url stays in sources.json
    print("skipped (no real bin):", e["title"])
print(fam, len(keep), "sources kept")
