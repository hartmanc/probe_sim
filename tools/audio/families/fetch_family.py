"""Fetch (licence-checked, audio only) every non-skipped source of a family that is not in cache/ yet.

    python3 -I tools/audio/families/fetch_family.py FAMILY [--drop]      (--drop: delete the family's FLACs instead)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fetch_audio  # noqa: E402

fam = sys.argv[1]
src = json.load(open(os.path.join(HERE, "sources.json")))[fam]
for e in src["entries"]:
    if e.get("skip") or not e.get("url"):
        continue
    vid = re.search(r"v=([\w-]{11})", e["url"]).group(1)
    p = os.path.join(HERE, "cache", f"{fam}__{vid}.flac")
    if "--drop" in sys.argv:
        if os.path.exists(p):
            os.remove(p)
        continue
    if not os.path.exists(p):
        print("fetch", vid, e.get("title", "")[:60], flush=True)
        try:
            fetch_audio.main(fam, vid, max_s=int(max(900, float(e.get("t1") or 0) + 5)))
        except Exception as ex:  # a video that will not download now: the build skips it (and says so)
            print("  FAILED", vid, type(ex).__name__, flush=True)
