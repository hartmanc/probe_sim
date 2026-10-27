"""Add fetched CC BY sources (cache/<family>__<id>.json from fetch_audio.py) to sources.json, or un-skip them.

    python3 -I tools/audio/families/add_sources.py FAMILY "WHY" VIDEO_ID [...]
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
fam, why, vids = sys.argv[1], sys.argv[2], sys.argv[3:]
p = os.path.join(HERE, "sources.json")
S = json.load(open(p))
ents = S[fam]["entries"]
for v in vids:
    rec = json.load(open(os.path.join(HERE, "cache", f"{fam}__{v}.json")))
    assert rec["licence"].startswith("Creative Commons Attribution"), rec
    hit = [e for e in ents if e.get("url", "").endswith(v)]
    if hit:
        for e in hit:
            e.pop("skip", None)
            e["why"] = why
        continue
    ents.append({"url": rec["url"], "file": rec["file"], "title": rec["title"], "uploader": rec["channel"],
                 "upload_date": rec["upload_date"], "licence": rec["licence"], "duration_s": rec["duration_s"],
                 "t0": 0.0, "t1": float(min(rec["duration_s"], rec.get("max_s", 900))), "context": "street", "notes": "round two",
                 "why": why})
json.dump(S, open(p, "w"), indent=1, ensure_ascii=False)
print(fam, len(ents), "entries")
