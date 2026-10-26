"""Replace one family's sources.json entries with the fetched CC BY records in cache/<family>__*.json.

    python3 -I set_sources.py FAMILY [--context street|track] [id[:context[:t0[:t1]]] ...]

Entries are built from the fetch records (url, title, uploader, upload date, licence as shown). Ids not listed are
left out. `notes` and a `why` are filled by hand afterwards in sources.json.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
fam = sys.argv[1]
specs = [a for a in sys.argv[2:]]
src = json.load(open(os.path.join(HERE, "sources.json")))
old = src.get(fam, {})
entries = []
for s in specs:
    p = s.split(":")
    vid = p[0]
    ctx = p[1] if len(p) > 1 and p[1] else "street"
    r = json.load(open(os.path.join(HERE, "cache", f"{fam}__{vid}.json")))
    t0 = float(p[2]) if len(p) > 2 and p[2] else 0.0
    t1 = float(p[3]) if len(p) > 3 and p[3] else float(min(r["duration_s"], r["max_s"]))
    entries.append({"url": r["url"], "file": r["file"], "title": r["title"], "uploader": r["channel"],
                    "upload_date": r["upload_date"], "licence": r["licence"], "duration_s": r["duration_s"],
                    "t0": t0, "t1": t1, "context": ctx, "notes": ""})
old["entries"] = entries
src[fam] = old
json.dump(src, open(os.path.join(HERE, "sources.json"), "w"), indent=1, ensure_ascii=False)
print(fam, len(entries), "entries")
