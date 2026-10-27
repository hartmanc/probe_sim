"""Licence gate for the AI engine families (pytest; no dependencies beyond the standard library).

    python3 -m pytest tools/audio/test_licences.py     (or: uv run --with pytest python -I -m pytest ...)

Every sources[] entry of public/audio/families/*/engine.json must be Creative Commons Attribution (CC BY), the owner's
own footage, or synthesised. A Standard YouTube License source (or anything else) fails the build.
"""
import glob
import json
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FAM = os.path.join(ROOT, "public", "audio", "families")


def allowed(licence: str, src: str) -> bool:
    if src == "synth":
        return licence.lower().startswith("synth")
    l = licence.lower()
    if "standard" in l:
        return False
    return l.startswith("creative commons attribution") and not any(w in l for w in ("noncommercial", "sharealike", "noderiv", "-nc", " nc"))


def test_every_family_source_is_cc_by_owner_or_synth():
    files = sorted(glob.glob(os.path.join(FAM, "*", "engine.json")))
    assert len(files) >= 12  # 13 AI families, one of them (classic_v8_lowrev) an alias of gm_sbc_v8 with no files of its own
    bad = []
    for f in files:
        d = json.load(open(f))
        assert d["sources"], f"{f}: no sources recorded"
        for s in d["sources"]:
            if not allowed(s.get("licence") or "", s["src"]):
                bad.append((os.path.basename(os.path.dirname(f)), s["src"], s.get("licence"), s.get("title")))
    assert not bad, f"sources that are not CC BY / owner's own / synth: {bad}"


def test_every_cc_source_has_a_credit_row():
    credits = json.load(open(os.path.join(FAM, "credits.json")))["families"]
    idx = json.load(open(os.path.join(FAM, "index.json")))
    assert set(credits) == set(idx["families"])
    for fid, f in idx["families"].items():
        if "note" in f and "own set" in f["note"]:
            assert credits[fid][0]["licence"] == "Owner's own footage"
            continue
        d = json.load(open(os.path.join(FAM, f["engine"])))
        urls = {s["url"] for s in d["sources"] if s["src"] != "synth"}
        assert urls == {r["url"] for r in credits[fid] if r["url"]}, fid
        for r in credits[fid]:
            assert set(r) == {"title", "channel", "url", "licence"}
            if r["url"]:
                assert r["channel"] and r["title"] and "Creative Commons Attribution" in r["licence"]


def test_no_preview_mp3_shipped():
    assert not glob.glob(os.path.join(FAM, "*", "preview.mp3"))


def test_engine_json_schema_unchanged():
    need = {"sampleRate", "format", "sprites", "padding_s", "levels", "bins", "real_bins", "family", "cylinders",
            "layout", "fire", "redline_rpm", "idle_rpm", "main_order", "borrowed_load", "sources", "fallback"}
    for f in glob.glob(os.path.join(FAM, "*", "engine.json")):
        d = json.load(open(f))
        assert need <= set(d), (f, need - set(d))
        assert d["sampleRate"] == 48000 and d["sprites"] == {"on": "engine_on.ogg", "off": "engine_off.ogg"}
        for b in d["bins"]:
            for k in ("on", "off"):
                assert {"offset", "duration", "rpm", "tier", "source", "seam_corr", "tick"} <= set(b[k])
