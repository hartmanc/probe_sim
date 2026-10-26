"""Which source each real bin came from: python3 -I usage.py FAMILY"""
import json, os, re, sys
H = os.path.dirname(os.path.abspath(__file__))
fam = sys.argv[1]
d = json.load(open(os.path.join(H, "..", "..", "..", "public", "audio", "families", fam, "engine.json")))
use = {}
for b in d["bins"]:
    for ld in ("on", "off"):
        x = b[ld]
        if x["tier"] in ("steady", "sweep"):
            m = re.match(r"(src\d+)", x["source"]); use.setdefault(m.group(1), []).append(f"{ld}{b['rpm']}")
for s in d["sources"]:
    print(s["src"], (s.get("title") or "")[:48], "->", len(use.get(s["src"], [])), "real bins")
