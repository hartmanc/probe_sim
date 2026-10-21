# Sonoma judge round 10 (21 Oct 2026, ~09:50 PDT)

Judge: **GPT 6 Astra through codex** (one batch of 8 images: the round-10 stills, t088, the pit video t0300 / t0304; prompt
`judge_r10/prompt_r10.md`, raw table `judge_r10/astra_r10.md`), checked by **the orchestrator (Claude)** against the package,
the frames and the stills. Package: branch track-pipeline c88c0a8 (the five judge-r9 rows), geometry byte-identical
(track.json b54342ae7d1c2bddfdb664031abec570, heightfield.bin 5fd95a7d1ae2d72ab3be047c072e007d, ortho.jpg too, Laguna
untouched). Verified first by the orchestrator: vitest 394 + 1 expected fail, build, python 26, compare_packages against
c85df6c (no extra, no missing, no height diffs: every change is to an existing object), stage-3 gates and coverage all ok
(containment 0 escapes, wall ends 15 joined / 0 exposed, coverage 0 missing / 30 dispositioned / 1 advisory height row, pit
lane ok), drive.ts on Laguna and Sonoma byte-identical to the pre-round-5 reference.
Preview: https://probe-37ahctxt7-coby-hartmans-projects.vercel.app/?track=sonoma.

## The judge-r9 rows, as built

| row | Astra | orchestrator's check |
|---|---|---|
| R1 pit-exit building frontage | PARTLY: bays and openings are there, "still reads as flat panels divided by a broad black band"; the real frontage has more framing and recess depth | agreed, a kit-depth simplification (OK_DIFFERENT rows); low |
| R2 canopy's open terrace | PARTLY: the slab and posts are visible; the rail and the stair are hidden behind the building and the fence in the views supplied, "not evidence that they are missing" | they are in the package (canopy keys deck_posts, stair; compare_packages: the canopy changed, nothing new); settled |
| R3 pit-out lane surface | FIXED: one surface, the bands gone | agreed (pitwall_s140 / s170_back); the cause was the track ribbon's shoulder under the lane and the rule box lines, both cut by opt-in keys |
| R4 catch-fence arms | FIXED: angled arms with the mesh carried up them, as t0304 | agreed |
| R5 SONOMA TURN 8 panel | FIXED: legible on the facing's face, as t088 | agreed (panel_turn8_s2634_r10) |

## Remaining rows

| row | finding | check |
|---|---|---|
| "K-rail segment drawn ~1.1 m" (pitwall_s110, t0300: WRONG_HEIGHT, Astra's worst row) | the sim's wall beside the pit-out looks 1.1 m to Astra | FALSE by the package: barrier 2 (pitwall) is 0.85 m from the island (179, -86) to the blend at (114, -74) = s 85-158; only the front-straight run (barrier 1) is 1.1 m and ends at the island. A hood camera 1.05 m up puts a 0.85 m wall close to the hood line, which is the misread |
| catch-fence mesh pattern (canopy_from_lane, pitwall_s140, t0304: WRONG_TYPE) | the kit's chain-link diamond mesh vs the real fence's dense rectangular grid | low, kit: a rectangular-grid option for catch fences, some day |
| frontage framing depth (OK_DIFFERENT) | flat glazing rectangles vs framed recessed bays | low, kit |
| lettering panel (OK_DIFFERENT) | a uniform grey panel vs lettering on the dark face | accepted as a typed-text treatment |

## Verdict

Round 10 closes the judge rows: three FIXED, two simplifications accepted, one row FALSE by the package. No round 11 before the
owner's lap; the remaining two kit rows (fence mesh pattern, frontage depth) wait for his notes.
