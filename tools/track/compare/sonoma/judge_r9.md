# Sonoma judge round 9 (21 Oct 2026, ~09:15 PDT)

Judge: **GPT 6 Astra through codex** (one batch of 8 images: the round-9 stills at the round-8 poses, the owner's station
frame, t088 and the pit video t0304; prompt `judge_r9/prompt_r9.md`, raw table `judge_r9/astra_r9.md`), checked by **the
orchestrator (Claude)** against the package, the frames and the stills. Package: branch track-pipeline c85df6c (the five
judge-r8 rows), geometry byte-identical (track.json b54342ae7d1c2bddfdb664031abec570, heightfield.bin
5fd95a7d1ae2d72ab3be047c072e007d, Laguna untouched). Verified first by the orchestrator: vitest 394 + 1 expected fail, build,
python 26, compare_packages against 56a3ff0 (1 extra = the SONOMA TURN 8 board, 1 height diff = the catch fence 2.0 to 3.1 m,
nothing else), stage-3 gates and coverage all ok (containment 0 escapes, wall ends 15 joined / 0 exposed, coverage 0 missing /
30 dispositioned / 1 advisory height row, pit lane ok), drive.ts on Laguna and Sonoma byte-identical to the pre-round-5
reference. Preview: https://probe-4lp9oa2gd-coby-hartmans-projects.vercel.app/?track=sonoma.

## The judge-r8 rows, as built

| row | Astra | orchestrator's check |
|---|---|---|
| R1 tower's open deck | FIXED: "brown overhanging roof, dark open viewing deck and pale lower storey, matching the main features of owner_52" | agreed; from the drag strip the deck and the overhanging roof read as the owner's frame (tower_drag_s1760_right_r9) |
| R2 SONOMA TURN 8 lettering | PARTLY: the panel's place is behind the car's windscreen frame in the supplied still, "cannot verify the reported fix or its width" | the panel is in the package (compare_packages: sign 'SONOMA TURN 8' at s 2644, 7.7 m, 0.7 m) and shows as the lighter panel on the facing in tower_8a_s2650_right_r9; a closer still is owed for the record (round 10) |
| R3 pit-out catch fence | PARTLY: the taller fence is there (top 3.1 m within the footage estimate); the kit's posts are straight, the real posts have angled top arms | agreed; the angled arms are a kit detail (low) |
| R4 K-rail stretch height | PARTLY: the 0.85 m Jersey from the island to the blend is consistent with the footage; the front-straight stretch at 1.1 m is not shown in the batch | the orchestrator read t0288 (the pit lane at the GEICO boards): the wall top sits at about a parked SUV's sill, ~1.0-1.1 m, so 1.1 m stands against the lidar's 0.85 m median (a ground-offset reading on the lane side is the likely cause); h_src says both; low |
| R5 pit-exit building and canopy | PARTLY: the red roof edge and dark frontage are right, but the frontage is "a closed, largely featureless mass" where t0304 shows bays and openings, and the canopy "reads as a roof projection beside a closed building" without its open terrace | agreed: round 10 |

## Remaining rows (round 10, cosmetic; geometry stays)

| row | finding | check |
|---|---|---|
| **pit-exit building frontage** (pitwall_s110 / s140, t0304: WRONG_TYPE, C20) | the dark band is featureless; the frame shows structural bays, framing and openings along the frontage | TRUE: bays and openings per t0300 / t0304 with the kit's windows / doors keys |
| **canopy's open terrace** (pitwall_s140, t0304: WRONG_TYPE, C20) | the round red ring is there, but the elevated open terrace under it (posts, open sides, the deck) is not, so it reads as a roof stuck to the building | TRUE: the terrace deck on posts under the ring, open all round, per t0304 and the lidar's 2.9-3.2 m deck |
| **catch-fence post tops** (pitwall_s170_back, t0304: WRONG_TYPE) | straight posts vs angled upper arms | low, kit: an angled-arm option for catch-fence posts if cheap |
| **pit-out lane surface** (pitwall_s170_back, t0304: EXTRA, C17) | pale transverse rectangular bands across the pit-out lane beside the double yellow (s ~158-200) where the video shows uniform pavement; present in the round-8 still too | TRUE (pre-existing texture): find the cause (texture tiles, paved-zone sections or a paint-over) and make the lane one surface |
| **lettering still** (t088: OK_DIFFERENT) | the fix is in the package but no supplied still shows it clearly | a close still at the panel for the record; the 7.7 m vs "at least 8.4 m" width difference is modest |

## Verdict

Round 9 closes the owner's findings 59-61 for good (the tower now reads as his frame, Q1 "broadly yes", Q2 continuous to the
blend). Round 10 is the five rows above; the owner can drive the round-9 preview now.
