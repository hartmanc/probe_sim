"""Engine Listening Room 2: round one's page (cards, notes boxes, db script) with round two's clips, the owner's
round-one note quoted on each card and what changed under it.

    python3 -I tools/audio/chain/make_page.py ROUND1_INDEX.html Q_BEFORE.json Q_AFTER_DIR CLIPS_DIR OUT.html
"""
import html
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

OWNER = {  # the owner's round-one notes, verbatim (26 Oct 2026)
    "mazda_kl_v6": "OK",
    "sohc_i4_loud": "OK",
    "modern_i4_stock": "Weird speech at 0:03 / High revs / upshift sounds like an organ note at 0:05",
    "classic_v8_lowrev": "Doesn't sound correct. 0:01 sounds like a VHS tape rewinding. Sounds loopy, dropping revs sound squeaky",
}
TRACED = {
    "modern_i4_stock": "The speech was a real voice: the 4250 rpm loop (heard at 0:03, the first-gear climb) was cut from the "
                       "Nissan B13 track-day video while someone talks; Silero hears it in every window of that loop. The "
                       "organ: the upshift glides the pitch of a clean, strongly tonal loop; in the game the physics' "
                       "clutch makes that glide 0.4-0.8 s long under throttle, longer than the clip's.",
    "classic_v8_lowrev": "The tape at 0:01 is the idle: 650 rpm played from a 750 rpm loop (x0.87) whose off-throttle "
                         "layer came from another recording. The squeak: the off-throttle loops above 3750 rpm were one "
                         "recording pitched up to x1.33. Loopy: 0.48-0.68 s loops on a lumpy V8 repeat 1.5-2 times a second.",
}


def fmt_ratio(r):
    return f"x{r:.2f}"


def changed_text(fam, b, a, added, clip):
    if fam in ("mazda_kl_v6", "sohc_i4_loud"):
        return ("Not rebuilt: you heard it as OK, and it passes the speech gate. Only the clip is new: rendered "
                "through the game's own audio chain and loudness-matched like the others"
                + (" (the player's CarAudio, unchanged)." if fam == "mazda_kl_v6" else
                   "; its upshifts now use the AI voices' new clutch drop."))
    parts = []
    if b["speech"]:
        parts.append(f"{b['speech']} loop{'s' if b['speech'] > 1 else ''} with a voice in {'them' if b['speech'] > 1 else 'it'} replaced; every "
                     "source is now screened for speech before cutting")
    parts.append(f"loops {b['loop_med']:.2f} s to {a['loop_med']:.2f} s (median), so the repeat is half as frequent")
    parts.append(f"largest pitch shift {fmt_ratio(max(b['ratio_max'], 1 / b['ratio_min']))} to "
                 f"{fmt_ratio(max(a['ratio_max'], 1 / a['ratio_min']))}")
    if a["idle_ok"] and not b["idle_ok"]:
        parts.append(f"idle is now a real idle recording (was the lowest loop pitched by x{b['idle_off_ratio']:.2f})")
    parts.append(f"real loops {b['real_on']}/{b['real_off']} to {a['real_on']}/{a['real_off']} (on/off)")
    if a.get("borrowed_off"):
        parts.append(f"{a['borrowed_off']} off-throttle bins are the on-throttle loop darkened at its own pitch, "
                     "instead of another loop pitched far")
    if added:
        parts.append(f"{added} new CC BY source{'s' if added > 1 else ''}")
    parts.append("upshifts drop with the clutch instead of gliding")
    return "; ".join(parts) + "."


def main():
    tpl, qb, qa_dir, clips_dir, out = sys.argv[1:6]
    s = open(tpl).read()
    QB = json.load(open(qb))
    clips = json.load(open(os.path.join(clips_dir, "clips.json")))
    srcj = json.load(open(os.path.join(ROOT, "tools", "audio", "families", "sources.json")))
    s = s.replace("<title>Engine Listening Room</title>", "<title>Engine Listening Room 2</title>")
    s = s.replace("<h1>Engine Listening Room</h1>", "<h1>Engine Listening Room 2</h1>")
    s = re.sub(r'<p class="lede">.*?</p>', '<p class="lede">Round two. The same 25 second climb for every motor (idle, three '
               'gears with two upshifts, a lift, two blipped downshifts, back to idle), now rendered through the game\'s own '
               'audio chain (its engine voice code running in Chrome) and loudness-matched: every clip has the same '
               f'A-weighted level ({clips["target_laeq_dbfs"]:.1f} dBFS), so a quiet motor is not a quiet clip. Your round-one '
               'note is quoted on each card, with what changed under it.</p>', s, count=1, flags=re.S)
    s = s.replace("</style>", ".owner{margin:.6em 0;padding:6px 10px;border-left:3px solid var(--acc);color:var(--ink);font-size:.92rem}"
                  ".owner b{color:var(--mut);font-weight:600}.changed{background:var(--hi);border-radius:8px;padding:8px 10px;"
                  "margin:.6em 0;font-size:.92rem}</style>", 1)
    for m in list(re.finditer(r'<section class="card" id="c-([a-z0-9_]+)"', s)):
        pass
    fams = re.findall(r'<section class="card" id="c-([a-z0-9_]+)"', s)
    for fam in fams:
        i = s.find(f'<section class="card" id="c-{fam}"')
        j = s.find("</section>", i)
        card = s[i:j]
        b = QB[fam]["summary"]
        qa_path = os.path.join(qa_dir, f"q_after_{fam}.json")
        a = json.load(open(qa_path))[fam]["summary"] if os.path.exists(qa_path) else b
        rows = json.load(open(qa_path))[fam]["measure"]["rows"] if os.path.exists(qa_path) else []
        a = dict(a)
        a["borrowed_off"] = sum(1 for r in rows if r["load"] == "off" and r["tier"] == "from-on")
        added = sum(1 for e in srcj.get(fam, {}).get("entries", []) if "round two" in (e.get("notes") or "") or "Round two" in (e.get("why") or ""))
        note = OWNER.get(fam)
        q = (f'<blockquote class="owner"><b>Round one, your note:</b> &ldquo;{html.escape(note)}&rdquo;</blockquote>' if note
             else '<blockquote class="owner"><b>Round one:</b> no note yet.</blockquote>')
        tr = f'<p class="changed"><b>Traced to.</b> {html.escape(TRACED[fam])}</p>' if fam in TRACED else ""
        ch = f'<p class="changed"><b>What changed.</b> {html.escape(changed_text(fam, b, a, added, clips["clips"].get(fam)))}</p>'
        weak = ""
        if os.path.exists(qa_path) and fam not in ("mazda_kl_v6", "sohc_i4_loud"):
            F = json.load(open(qa_path))[fam]["fails"]
            bits = []
            if F["idle"]:
                bits.append("no real idle recording near its idle yet (the lowest loop is pitched to it)")
            if F["ratio"]:
                bits.append("still pitch-shifted past the limit at " + ", ".join(x.split(" x")[0] for x in F["ratio"][:6]) + " rpm")
            if a["seam_corr_med"] < b["seam_corr_med"]:
                bits.append(f"loop seams a little less clean than round one's shorter loops (median correlation {a['seam_corr_med']:.2f} vs {b['seam_corr_med']:.2f}): listen for a soft repeat once a second")
            if bits:
                weak = f'<p class="changed"><b>Still weak.</b> {html.escape("; ".join(bits))}.</p>'
        card2 = re.sub(r'<p class="listen">.*?</p>', lambda _m: q + tr + ch + weak, card, count=1, flags=re.S)
        # sources list from the shipped engine.json
        ej = os.path.join(ROOT, "public", "audio", "engine.json") if fam == "mazda_kl_v6" else \
            os.path.join(ROOT, "public", "audio", "families", fam, "engine.json")
        E = json.load(open(ej))
        if fam != "mazda_kl_v6" and E.get("sources"):
            li = "".join(f'<li><a href="{html.escape(x["url"])}" target="_blank" rel="noopener">{html.escape(x.get("title") or "")}</a> '
                         f'<span class=\'mut\'>{html.escape(x.get("channel") or "")} · {html.escape(x.get("licence") or "")}</span></li>'
                         for x in E["sources"])
            rep = f'<p class="mut">Sources ({len(E["sources"])}), rendered through the game\'s EngineVoice chain</p><ul>{li}</ul>'
            card2 = re.sub(r'<p class="mut">Sources \(\d+\), rendered through [^<]*</p><ul>.*?</ul>', lambda _m: rep,
                           card2, count=1, flags=re.S)
        else:
            card2 = card2.replace("rendered through the player's CarAudio chain", "rendered through the game's CarAudio chain")
        s = s[:i] + card2 + s[j:]
    open(out, "w").write(s)
    print("wrote", out, len(fams), "cards")


if __name__ == "__main__":
    main()
