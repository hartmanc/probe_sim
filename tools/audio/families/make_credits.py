"""Write public/audio/families/credits.json for the Credits page from every family's engine.json.

    python3 -I tools/audio/families/make_credits.py

Schema (agreed with the release-040 Credits page):
  {"families": {"<family id>": [{"title", "channel", "url", "licence"}, ...]}}
One row per distinct video (a video cut in two time ranges is one credit). Synthesised families get one row naming the
generator; the Probe's own set (mazda_kl_v6) is the owner's own footage.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "..", "public", "audio", "families")
CC = "Creative Commons Attribution license (reuse allowed)"  # as YouTube shows it for CC BY 3.0 videos


def main():
    idx = json.load(open(os.path.join(OUT, "index.json")))
    fams = {}
    for fid, f in idx["families"].items():
        if "note" in f and "own set" in f["note"]:
            fams[fid] = [{"title": "Probe sim team onboard footage, car #619 (KL-DE V6), Laguna Seca, 12 Oct 2026",
                          "channel": "Probe sim team (the owner's own footage)", "url": "",
                          "licence": "Owner's own footage"}]
            continue
        ej = json.load(open(os.path.join(OUT, f["engine"])))
        rows, seen = [], set()
        for s in ej["sources"]:
            if s["src"] == "synth":
                rows.append({"title": "Synthesised engine note (procedural generator, no recorded source)",
                             "channel": "Probe sim (tools/audio/families/synth_engine.py)", "url": "",
                             "licence": "Synthesised"})
                continue
            if s["url"] in seen:
                continue
            seen.add(s["url"])
            lic = s["licence"]
            rows.append({"title": s["title"], "channel": s.get("channel") or "", "url": s["url"],
                         "licence": CC if lic.startswith("Creative Commons Attribution") else lic})
        fams[fid] = rows
    json.dump({"families": fams}, open(os.path.join(OUT, "credits.json"), "w"), indent=1, ensure_ascii=False)
    print({k: len(v) for k, v in fams.items()})


if __name__ == "__main__":
    main()
