# Mid-Ohio round 11: the texture seam after T1, the dark verges, the blend-line black flag, the starter's stand legs

Sonnet 5.5, 26 Oct 2026, branch `mid-ohio` (from 2645e6d, package rev ea1a07f8bd). The owner's four notes from his round-10 drive. **Package rev 7dcbb9c278**
(registry `mid_ohio.rev`). `track.json`, `heightfield.bin`, `ghosts.json`, `far_ortho.jpg`, `far_heightfield.bin` unchanged (git diff empty); changed:
`scenery.json` (closed-road `tone`, `blend_line`, the stand) and `ortho.jpg` (verge tone).

## 1. The texture mismatch on the straight after T1

Diagnosis (screenshot projected onto the package: the T1-T3 connector, north (OSM 444205378) leaves the course on the right at s 472, 10 m wide; `r11/mkwalk.py`
poses at s 440-500): the "flat pale-grey plane" is that connector's paved zone, drawn in the default apron tone (0.50 / 0.49 / 0.46 albedo, rendered
about 190 grey against the course's 110). N837 t021 shows the connector asphalt a little darker and warmer than the course (patch means 144/131/116 and 135/121/106
against 156/147/138 and 161/152/144; the 360 lap reads it "a touch lighter" in the sun). The "tan area" beyond is the ortho's own ground: the T1 exit sand and its
red outer kerb band (360 t036 right shows the same tan strip along the edge), real, kept. The ragged outline is the zone's polygon edge (the owner's green strokes).
Fix: opt-in per-road `tone` (config `closed_roads[].tone` + `tone_src` -> scenery.json part `tone`; `src/app/scene.ts` passes it to the apron shader; absent = the
old default, other tracks byte-identical). Set (0.05, 0.045, 0.038) on all three closed roads: rendered apron luminance about the course's, warm. Calibrated by shooting
the sim (tone 0.5 / 0.2 / 0.1 / 0.06 / 0.025 / 0: the apron floors near 120-140 grey from the sky reflection at grazing angles, so the tone cannot go lower than about
equal to the course). The seam outline remains faintly visible. Sheet: sheet_owner_spot_r11.

## 2. The dark verge areas

Diagnosis: the grass tone of round 8 (`grass_tone`) needs green over red and blue (g-r > 1, g-b > 1), luminance 18-170 and no lidar canopy within 3 px of 1 m height.
The dark verge pixels fail it: shadowed grass is blue-grey (back straight left (12, 20, 31)), dulled grass olive-brown (70, 70, 55, g under r), and the strips beside
barriers are excluded because fences and armco (1-2.5 m) count as "canopy". So the ortho under the tone stayed dark (NAIP vintage and the far ortho are not the cause).
Fix (opt-in `grass_tone.verge`, `build_scenery.grass_verge_mask`): within 30 m of the edge (fade 5 m), outside the course, pit lane and paved zones, dark ground
(luminance under 110, R-G under 14: sand, dirt and kerb paint stay) under no TALL canopy (chm over 3 m, no dilation) takes the grass target at its relative
luminance, floored at 0.6 of the local mean (the shade in 360 t070 left reads mid green). The pit side is skipped (left s 3370-380: out of scope). Green share
(G over R and B by 4, per 300 m sector, 0-30 m beyond each edge, `r11/verge_stats.py`; before = round-10 ortho):

| s | left green before | after | right green before | after |
|---|---|---|---|---|
| 0-300 | 0.14 | 0.14 | 0.74 | 0.92 |
| 300-600 | 0.75 | 0.89 | 0.35 | 0.44 |
| 600-900 | 0.95 | 0.99 | 0.90 | 0.96 |
| 900-1200 | 0.79 | 0.79 | 0.77 | 0.77 |
| 1200-1500 | 0.59 | 0.87 | 0.75 | 0.85 |
| 1500-1800 | 0.33 | 0.78 | 0.51 | 0.92 |
| 1800-2100 | 0.62 | 0.79 | 0.66 | 0.94 |
| 2100-2400 | 0.65 | 0.82 | 0.73 | 0.97 |
| 2400-2700 | 0.57 | 0.73 | 0.85 | 0.98 |
| 2700-3000 | 0.58 | 0.81 | 0.71 | 0.97 |
| 3000-3300 | 0.80 | 0.93 | 0.71 | 0.86 |
| 3300-3600 | 0.34 | 0.36 | 0.59 | 0.75 |
| all | 0.592 | 0.742 | 0.690 | 0.860 |

Dark (luminance under 80, not green): left 0.179 -> 0.064, right 0.116 -> 0.004. What stays: the T1 exit sand (right 300-600 reads 0.44: the tan strip is real, 360 t036),
the pit side, and ground under the woods' tall crowns (left 1200-1800, dark under real trees). The ground-lines gate then showed three barrier shadows with a
changed extent; dispositioned as barrier shadows (left s 480-560; the wrapped right entry at s 3503-3597 split at the line, where it never overlapped a finding
that starts after 3503). Not loosened: the gate is still strict, 0 open. I could not identify the exact spot of screenshot 2 (the brief's "pit straight left" has
the pit wall, not an armco, on its left; the view matches the T1-exit and back-straight left verges); the sheet shows six left verges.

## 3. The blend line black flag

Declared in the config (`scenery.blend_line`: the inner line of the pit-exit ladder, s 212-296, 80 m, 0.10 m beyond the left edge, from the pit wall's end (212) to
3 m before the raised T1 kerb (299.2); pit exit on its left; label "crossed the blend line at T1") -> scenery.json `blend_line` {pts, pit_side, label, s, src}.
Runtime (`src/physics/blendline.ts`, generic, absent = no rule, the player only): a car that enters the line's band from the course is on its lap: two wheels (centre
past the line, grace 0, never over a wheel width) on the pit side = violation; a car that enters from the pit side is leaving the pits: two wheels on the course side
= violation. Race: `RaceDirector` `blendLine` input, playerRules (b2): the four-wheels-off black-flag path and penalty, debounced like it (re-armed after 2 s legal);
toast "Black flag: crossed the blend line at T1". Hot lap: `HotlapSim` invalidates the lap (`LapTimer.invalidate`, `Lap.reason`), the scoreboard replay reason is
"replay: lap invalid (crossed the blend line at T1)", the hot-lap mode toasts the flag. Tests (`src/physics/__tests__/blendline.test.ts`, 18; `blendline_midohio.test.ts`, 5):
band, one wheel, two wheels, both directions, mirrored side, grace clamp, debounce, lap timer reason, race flag, no line = no rule (Laguna hot lap and race), and on the package:
declared geometry, the racing-line autopilot at pace 0.85 / 1.0 through the band (minimum wheel clearance 1.00 / 2.05 m, no flag), a placed car with two wheels across = lap invalid.
Laguna, Sonoma, Buttonwillow: package diff empty, soup hashes unchanged.

**AI items (reported, line and road not moved).** The AI knows no blend line. Self-play 2 laps, full 45-car stand-in field (`r11/blend_selfplay.ts`, every car's wheels against the line):
seeds 1, 2, 5: 0 episodes (worst wheel clearance 0.44, 0.12, -0.18 m); seed 3: 2 (car #20, a pass to the left at s 229, centre 0.6 m inside the edge at 19.8 m/s, and
s 284, up to 4.3 m across the line at 5.5 m/s); seed 4: 1 (#202, s 294); seed 6: 1 (#700, s 293). The T1 entry (s 284-294) is where the racing line runs 1.0 m
from the left edge and the AI's lateral error puts the left wheels 0.0-0.2 m across the line; the s 229 one is a left-side pass. The AI-driven player was never flagged by the rule. Fix belongs to the AI (a line clearance at the blend line), not the road.

## 4. The starter's stand

Frames: 360 lap t022-t024 left show the braced scaffold astride the wall line with the Honda board; N837 t129-t130 the stand over the wall; the ARCA photo a scaffold
with legs either side of the wall (arrangement only). The 2022 NAIP shows the white wall band interrupted under it (r11/overlay_stand.py). Built what the owner described.
Round 9's stand stood with its centre inside the wall's line: its track-side legs ON the course edge (lateral 5.94 against 6.02) and the pit-side legs against the wall
(the wall runs 8.1-8.6 m out there). Now (config only, no kit change): centre 0.9 m toward the pit side (lateral 7.94), depth 2.9 m, legs 2.5 m apart: track-side pair
at 6.67 m (0.56 m clear of the edge) on the apron, pit-side pair 9.2 m (0.65 m behind the wall), the wall passing between; braced on both long faces. Wall-tops, containment and pit-lane gates ok.

## Gates, proofs

`build_track.py --track mid_ohio --stage scenery --publish --overwrite-package` (out `tools/track/out/mid_ohio_r11`, from the r10 out; it reproduced r10 byte-identically before
the changes): exit 0, 21 lines [ok], ground lines strict 0 open, coverage 0 missing. On the package: `run_gates.ts` (/tmp/mo7/g9.json) rc 0, `run_coverage.ts` rc 0 (0 missing, 0 unsupported),
`edge_gate.py` rc 0. Sonoma stage 3 from its published files: all four outputs identical to public/tracks/sonoma; Laguna stage 3 on its reproduction (copy of laguna_r8chk): four outputs
identical (rc 1 as for the reproduction); structure soups f71411f3c2e78626 / e3b0c44298fc1c14 / 3da76e09e950dd5a unchanged. Full `npx vitest run`: 67 files, 566 tests passed; `npm run build` ok.
Not touched: road files, physics dynamics, the AI, the pits ("rough, but whatever"). `tools/race/selfplay.ts` now passes `blendLine`.

## Open

The connector mouth's ragged outline; the tone is calibrated by render, not a pixel-exact match; the screenshot-2 spot; AI clearance at the blend line (above); stand legs' exact placement is the owner's description plus plan evidence, the frames do not resolve the feet.
