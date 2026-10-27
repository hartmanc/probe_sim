"""Mid-Ohio round 6 hood sheet page: the evidence composites for T8 (the crest from 60 m before it, the hood walk on the
solver's line through the crest and T8) and the T4 entry (the hood walk through the braking zone beside the real
frames), and hood_r6/index.html (one row per sheet: corner, station, what to compare, the caption).

    uv run --python 3.12 --with pillow python -I tools/track/compare/mid_ohio/r6/make_index.py <hood_r6 dir>
"""
import html
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..', '..'))
IDIR = os.path.join(ROOT, 'tools/track/compare/mid_ohio/inventory')
hd = sys.argv[1]
F = json.load(open(os.path.join(hd, 'frames.json')))
CAP = json.load(open(os.path.join(HERE, 'captions.json')))
P8 = json.load(open(os.path.join(HERE, 't8_profile.json')))
OV = json.load(open(os.path.join(HERE, 't8_overlay.json')))
AI = json.load(open(os.path.join(HERE, 'ai_profile_t8.json')))
T4 = json.load(open(os.path.join(HERE, 't4_entry.json')))
fnt = lambda s: ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', s)  # noqa: E731


def grid(cells, cols, w, out, title):
    ims = []
    for path, label in cells:
        im = Image.open(path).convert('RGB'); h = int(im.size[1] * w / im.size[0]); im = im.resize((w, h), Image.LANCZOS)
        c = Image.new('RGB', (w, h + 26), (20, 20, 20)); c.paste(im, (0, 26)); ImageDraw.Draw(c).text((6, 3), label, fill=(240, 240, 240), font=fnt(17))
        ims.append(c)
    H = max(i.size[1] for i in ims); rows = (len(ims) + cols - 1) // cols
    S = Image.new('RGB', (cols * (w + 6) + 6, 44 + rows * (H + 6)), (10, 10, 10))
    ImageDraw.Draw(S).text((8, 10), title, fill=(255, 220, 120), font=fnt(24))
    for k, im in enumerate(ims):
        S.paste(im, (6 + (k % cols) * (w + 6), 44 + (k // cols) * (H + 6)))
    S.save(os.path.join(hd, out))


sim = lambda f: os.path.join(hd, 'sim', f)  # noqa: E731
inv = lambda f: os.path.join(IDIR, f)  # noqa: E731
sl = next(r for r in P8['sight_lines'] if r['before_crest_m'] == 60)
grid([(sim('t8_crest_minus60_s2394_centre.jpg'), 'SIM hood, centre, s 2394 (60 m before the crest)'),
      (sim('t8_crest_minus60_s2394_line.jpg'), "SIM hood, solver's line, s 2394"),
      (inv('frames_n837/t084.jpg'), 'N837 t084, s 2392 (speed-integrated)'),
      (inv('frames_360_half/h0186_ahead.jpg'), '360 lap t 93.0, s ~2395')], 2, 640, 't8_crest.png',
     f"T8 crest (s {P8['crest']['s']}) from 60 m before: the road surface is visible only to s {sl['see_road_to_s']} "
     f"({sl['see_road_m']} m ahead); a 0.3 m kerb to s {sl['see_kerb_0p3_to_s']}")
walk = [(sim(f't8_walk_s{s:04d}_line.jpg'), f"SIM line s {s}") for s in range(2380, 2581, 20)]
grid(walk, 4, 420, 't8_walk.png', "T8: the hood walk on the solver's line, s 2380-2580 every 20 m (crest s 2454, apex s 2521)")
t4c = []
for s, k in ((1830, 145), (1850, 146), (1870, 147), (1890, 148)):
    t4c += [(sim(f't4_entry_s{s:04d}_line.jpg'), f"SIM line s {s}"), (inv(f'frames_360_half/h{k:04d}_ahead.jpg'), f"360 lap h{k:04d} (s ~{s})")]
grid(t4c, 4, 420, 't4_entry_walk.png', "T4 entry braking zone on the solver's line (left margin 1.0 m at s 1855-1871) beside the 360 lap")

tags = {'T8': 'crest, edges, width, apex kerb', 'T4': 'the T4 bank, kerbs, width, braking room'}
rows = []
for sh in F['sheets']:
    key = sh['id'].split('_', 2)[2]
    what = tags.get(sh['corner'], 'edges, width' + (', kerbs' if sh['phase'] != 'mid' else ', straightness'))
    if sh['corner'] in ('T7', 'T9', 'T10'):
        what += ', crest / dip'
    rows.append(f"<tr><td>{len(rows) + 1}</td><td><b>{html.escape(sh['corner'])}</b> {html.escape(sh['name'] if sh['name'] != sh['corner'] else '')} {sh['phase']}</td>"
                f"<td>{sh['s']:.0f}</td><td>{what}</td><td>{html.escape(CAP.get(key, ''))}</td>"
                f"<td>N837 {sh['n837']['frame'].split('/')[-1]} (s {sh['n837']['s_frame']:.0f}, &plusmn;{sh['n837']['sigma_m']:.0f} m)<br>"
                f"360 {sh['v360']['frame'].split('/')[-1]} (s {sh['v360']['s_frame']:.0f}, &plusmn;{sh['v360']['sigma_m']:.0f} m)</td></tr>"
                f"<tr><td colspan=6><a href='{sh['id']}.png'><img loading='lazy' src='{sh['id']}.png' alt='{sh['id']}'></a></td></tr>")
ai8 = {r['s']: r for r in AI['rows']}
mo = T4['mid_ohio']
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mid-Ohio Hood Sheet</title>
<style>
:root{{--bg:#111;--fg:#e8e8e8;--mut:#9a9a9a;--acc:#ffd27a;--line:#333}}
@media (prefers-color-scheme: light){{:root:not([data-theme="dark"]){{--bg:#fafafa;--fg:#1a1a1a;--mut:#555;--acc:#8a5a00;--line:#ddd}}}}
:root[data-theme="light"]{{--bg:#fafafa;--fg:#1a1a1a;--mut:#555;--acc:#8a5a00;--line:#ddd}}
:root[data-theme="dark"]{{--bg:#111;--fg:#e8e8e8;--mut:#9a9a9a;--acc:#ffd27a;--line:#333}}
body{{background:var(--bg);color:var(--fg);font:15px/1.45 -apple-system,system-ui,sans-serif;margin:0;padding:16px;max-width:1500px}}
h1,h2{{color:var(--acc);font-weight:600}} h1{{font-size:22px}} h2{{font-size:18px;margin-top:28px}}
img{{max-width:100%;height:auto;display:block;border:1px solid var(--line)}}
table{{border-collapse:collapse;width:100%}} td,th{{border-bottom:1px solid var(--line);padding:6px;vertical-align:top;text-align:left}}
.mut{{color:var(--mut)}} .wrap{{overflow-x:auto}}
</style></head><body>
<h1>Mid-Ohio round 6: the driver's-eye hood sheet (build-track 1.10)</h1>
<p>Each sheet puts the sim's hood camera on the local package (round 5: geometry and racing line only; <b>no scenery, far terrain or trees yet</b>)
beside the N837 Lemons hood camera (Apr 2026) and the 2025 IndyCar 360 lap's ahead view (pace car roof) at the same station.
<b>Judge the road only:</b> the edges, the width, where each kerb starts and ends, crests and dips, and the T4 bank. Each caption says what to look at.
The sim car sits on the centre facing the lap. For T8 and T4 a second still shows it on the solver's racing line.
The &plusmn; after each frame's station is its time map's error. N837 has a frame every 1 s, the 360 lap every 0.5 s, so a frame can sit 10-20 m from the sim still.</p>
<h2>Overview</h2><a href="sheet_00_overview.png"><img src="sheet_00_overview.png" alt="overview"></a>
<h2>T8 evidence (the round-5 finding)</h2>
<p>The solver opens T8 to R {OV['t8_min_radius_m']['solver']['R']} m (the centre's tightest radius is R {OV['t8_min_radius_m']['centre']['R']} m). A smooth line through the real cars' positions gives
R {OV['t8_min_radius_m']['real_fit']['R']} m. The real cars stay at the <b>left edge over the blind crest</b> (s {P8['crest']['s']}; yellow kerb at s 2451-2466), apex on the right kerb at about s 2510-2540,
and exit to the left kerb (s 2565-2610). The solver's line crosses diagonally from the T7 apex, so it is 2-4.5 m right of the real cars at s 2440-2490.
The race AI's own profile takes the T8 apex at {ai8[2520]['v_ai_kmh']} km/h. The N837 session best covers s 2481-2589 at about 119 km/h on average
(from the Catalyst delta), so lap 149's 85 km/h minimum belongs to that lap, not to the circuit. Full numbers: <code>round6.md</code> section 2.</p>
<a href="t8_overlay.png"><img src="t8_overlay.png" alt="T8 overlay"></a>
<a href="t8_crest.png"><img src="t8_crest.png" alt="T8 crest"></a>
<a href="t8_walk.png"><img src="t8_walk.png" alt="T8 walk"></a>
<h2>T4 entry (the autopilot's wheel-off)</h2>
<p>Under braking at 0.85-0.88 g into T4, the line reaches its 1.0 m left margin at s 1855-1871. The autopilot drifts {mo['max_outward_err_at_margin_braking_m']} m outward,
so the left front wheel's centre comes within {mo['min_wheel_clear_m']:.2f} m of the edge and the tyre is over it for {mo['rows_off_track']} grid rows (290 steps, 0.29 s). Sonoma, Buttonwillow and Laguna, driven by the same command,
keep their wheel centres at least {T4['sonoma']['min_wheel_clear_m']} / {T4['buttonwillow']['min_wheel_clear_m']} / {T4['laguna_seca']['min_wheel_clear_m']} m inside.
The 360 car brakes about 1-1.5 m from the left line. The proposal is in <code>round6.md</code> section 3 (not applied).</p>
<a href="t4_entry_walk.png"><img src="t4_entry_walk.png" alt="T4 entry walk"></a>
<h2>The sheets (T8, T4, then the lap in driving order)</h2>
<div class="wrap"><table><tr><th>#</th><th>corner</th><th>s (m)</th><th>compare</th><th>what to judge</th><th>source frames</th></tr>
{''.join(rows)}
</table></div>
<p class="mut">Reference imagery only (YouTube frames, satellite captures); not committed, never a texture. Package rev 05d6072129 (local stand-in), branch mid-ohio.</p>
</body></html>"""
open(os.path.join(hd, 'index.html'), 'w').write(page)
print('index.html', len(rows), 'sheets')
