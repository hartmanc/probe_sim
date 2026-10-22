# Sonoma judge round 12 (22 Oct 2026, ~14:35 PDT)

Judge: **GPT 6 Astra through codex** (one batch of 13 images: the six round-12 after-stills for the owner's notes 65 and 67, the
six round-11 before-stills at the same poses, and his round-10 screenshot of the sunken T10 wall; prompt `judge_r12/prompt_r12.md`,
filled copy `judge_r12/prompt_r12_filled.md`, raw table `judge_r12/astra_r12.md`), checked by **the orchestrator (Claude)**
against the stills and the package. Package: branch track-pipeline 85d5043 (rev 1d38e06899, on top of the round-11 judge ac29850).
Verified first by the orchestrator on 85d5043: vitest 430 passed + 1 expected fail (no timing failure, machine idle), vite build
ok, python 35 passed, stage-3 gates all ok (containment 0 escapes, wall ends 20/20, wall tops 41 runs / 115 boards, wall-tyre
joins 3, tyre faces 0), coverage 0 missing / 30 dispositioned / pit lane ok, Laguna and Buttonwillow packages byte-identical to
ac29850, the Sonoma package differs from ac29850 in `scenery.json` only.
Preview: https://probe-9ykksa4o8-coby-hartmans-projects.vercel.app/?track=sonoma.

## The owner's notes, as built

| note | Astra | orchestrator's check |
|---|---|---|
| 65 T10 boards stepped at ~3180-3230 | FIXED: one continuous, evenly graded boarded run with a grounded base; the dips and the pale wedges are gone (`n65_T10_3160`, `_3185_left`, `_3200_left` after) | agreed. Cause: barrier 27 (the T10-T11 boarded wall) followed the lidar ground across a 3.5 m drainage ditch at s 3196-3218 (base -0.60 to -3.51 m, slope 0.96), so the boards sat at -1.83 to -0.01 m between neighbours at 0.66 and 0.34. `barrier_rules.py` now keeps a concrete or pit wall level across a hollow (span <= 30 m, slope >= 0.5, lips >= 0.3 m); 15 points lifted, max 2.84 m; the top falls evenly 0.66 -> 0.50 m; boards 34-38 at 0.59-0.51 m; the terrain mesh is lowered only to the wall's top minus its height, no longer into the ditch |
| 67 the T11-approach tyre head at ~3398 | FIXED: the tyre head meets the concrete wall without the trackward projection; the fence continues over the joint (`n67_tyre_head_close` after) | agreed. Run 38's second row stood toward the track: 0.73 m proud of the wall face and 0.37 m onto the road. `tyre_rows_outside` reverses such a run; its face is now +0.23 m beyond the edge and 0.13 m from the wall face, and the two catch fences meet at one post |

Astra's other rows are all on the round-11 before-stills and the owner's round-10 screenshot (historical) and marked so.
(Q1) yes, one continuous, gently graded boarded wall with a grounded base. (Q2) what the owner would notice first: the repaired
SONOMA RACEWAY boarded wall approaching T10.

## Gates added in round 12

Wall tops (no concrete / pit-wall / Armco top line steeper than 0.5 m per m; every wall board within 0.10 m of its wall's top),
wall-tyre joins (a downstream head at most 0.15 m proud toward the track), tyre faces (a tyre run's drawn face at least 0.2 m
beyond the edge). On the round-11 package they fail exactly the two findings (step 0.96 at s 3197 plus two boards off the top;
the join +0.73 m at s 3398; the face -0.37 m at s 3404); on round 12, Laguna and Buttonwillow they pass.

## Verdict

Round 12 closes notes 65 and 67, the last open rows from the owner's round-10 lap except note 66 (the infield building, which
stands on the lidar at 7.0 m for his call). Merge to main is held for the owner's drive, his decision of 22 Oct.
