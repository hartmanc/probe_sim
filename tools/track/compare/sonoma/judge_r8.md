# Sonoma judge round 8 (21 Oct 2026, ~09:00 PDT)

Judge: **GPT 6 Astra through codex** (credits back; two batches of 8 images, `judge_r8/prompt_b1.md` / `prompt_b2.md`, raw
tables `judge_r8/astra_b1.md` / `astra_b2.md`), checked row by row by **the orchestrator (Claude)** against the package, the
frames and the round-8 stills. Package: branch track-pipeline 56a3ff0 (owner notes 59-61: the continuous pit wall, the 8a
tower and its two walls), geometry byte-identical (track.json b54342ae7d1c2bddfdb664031abec570, heightfield.bin
5fd95a7d1ae2d72ab3be047c072e007d, Laguna untouched). Verified first by the orchestrator: vitest 394 + 1 expected fail,
build, python 26, compare_packages (2 missing = the removed blocks kerb and the camper hut, 3 extra = the tower, the
station facing and the T6-facing Jersey, 0 height diffs), stage-3 gates and coverage all ok (containment 0 escapes, wall
ends 14 joined / 0 exposed, coverage 0 missing / 30 dispositioned, pit lane ok), drive.ts on Laguna and Sonoma byte-identical
to the pre-round-5 reference. Preview: https://probe-hm91sq1c0-coby-hartmans-projects.vercel.app/?track=sonoma.

## The owner's findings, as built

| note | result |
|---|---|
| 59 pit wall continuous through s 134-158 | FIXED. Astra Q2: "Yes across the supplied pit-out views: no intermediate nose or gap is visible around stations 88-103, and the wall reaches the blend near 158." One run s 3953 to 158 (296 m), measured on the captures (84-98 % picked, rms 0.03-0.05 m), the T1 inside "block line" removed (K-rail segment tops), the wall-ends gate passing by itself |
| 60-61 the 8a tower over the T6-facing wall | FIXED for position, walls and height. Astra Q1: "Broadly yes for position, foreground facing and believable height"; the tower at the owner's footprint (overlay rows within tolerance), roof top 3.8 m from the lidar, the 166 m paddock wall with its two black facings where t084 / t088 show them, the 0.85 m Jersey continuous under the tower to s 2864 |

## TRUE rows (round 9, cosmetic; geometry stays)

| row | finding | check by the orchestrator |
|---|---|---|
| **tower's track face** (tower_8a_s2650_right, owner_52: WRONG_TYPE, C13 / C20) | the sim's tower is a pale box with a narrow opening; the owner's May 2025 frame shows a broad brown overhanging roof over a dark OPEN viewing deck with the lighter structure below | TRUE: the kit's 'tower' style must open the upper storey (posts and a rail under the roof) on the track side at least; roof overhang as the owner's frame. Astra Q3: the thing the owner notices first |
| **"SONOMA TURN 8" lettering** (t088, tower_8a_s2650_right: MISSING, C14) | white letters on the grey wall's track face beside the station at ~s 2640; the agent left it out as "not legible", but t088 reads it plainly | TRUE: typed white text on the wall face (allowed: typed text, no logo art) |
| **pit-out catch fence** (pitwall_s110 / s140 / s170_back, t0304: WRONG_HEIGHT, C5) | the paddock-side wall along the pit-out lane carries a 3-4 m mesh catch fence with angled tops (t0304, inventory row s 160 "catch fence on the wall, curved-top posts, 4.0 m, fence-post-ref"); the barrier entry 'pit-out lane, paddock side' has fence=1.0 while pit_lane.walls declares fence=4.0 for s 150-170 | TRUE (pre-existing since round 5, exposed at the judged place): fence 4.0 m on that wall where the video shows it (from the building to the lane's end, ~s 130-190, measured on t0300 / t0304), and the pit-lane declaration and the object must agree |
| **K-rail stretch height** (pitwall_s075 / s110, t0296 / t0300: WRONG_HEIGHT) | the run is drawn at 1.1 m end to end; the pit video shows 0.8-0.9 m segmented Jersey from the island to the blend (the agent's own note: 0.8-0.9 m for s 92-133) | TRUE, minor: split the run where the lidar height steps (SAFER-type ~1.1 m on the front straight, Jersey ~0.85 m from the island) as two runs joined end to end on one line; the wall-ends gate treats a joined run as covered |
| **pit-exit building** (pitwall_s075 / s110 / s140, t0300 / t0304: WRONG_TYPE / MISSING, C20) | the sim draws a big pale rectangular building with blue window bands and red bands; the video shows a low building with a sloping red-edged roof and dark frontage, and a conspicuous round red canopy on an elevated terrace beside it (t0304) | TRUE, medium (kit): massing and roof per t0300 / t0304, the round red canopy as a structure on the terrace; the owner passes it on every out-lap |

## Settled or not judgeable

- pit-side lane paint "missing" (t0296, pitwall_s075): the pit video is driven inside the lane, the sim stills are on the
  track with the wall between: not judgeable from these views; the lane's paint is the pit sheets' business (unchanged this round).
- the wall's end at s 158 "exposed rectangular face" (pitwall_s140 / s170_back, C1): a downstream end (traffic on both sides
  runs with it), passed by the wall-ends gate; the real end has a yellow-topped end post (note 56): a low cosmetic item.
- the T6-facing wall's continuity under the tower: Astra calls it "partly obscured" in the stills; the overlay and the
  measurement (100 % picked, rms 0.05 m, one object) settle it.
- Batch 1's Q2 and batch 2's Q1 are "cannot judge" by design (each batch holds one place).

## Verdict

The two owner findings are fixed and the package is drivable now; round 9 is cosmetic (five rows above), geometry untouched.
