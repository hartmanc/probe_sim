# Sonoma judge round 11 (22 Oct 2026, ~10:40 PDT)

Judge: **GPT 6 Astra through codex** (one batch of 17 images: the ten round-11 after-stills for the owner's notes 63-69 and his
seven round-10 screenshots; prompt `judge_r11/prompt_r11.md`, raw table `judge_r11/astra_r11.md`), checked by **the orchestrator
(Claude)** against the stills and the package. Package: branch track-pipeline 7d0d10f (a152668 Part A: notes 63-69, rev
ff9814637f, 4098.5 m; 7d0d10f Parts B and C: solid tyre walls, the rollover game-over). Verified first by the orchestrator:
build, python 29, compare_packages against eb5e3ad (no extra, no height diffs), stage-3 gates and coverage all ok (containment 0
escapes, wall ends 20/20 joined, coverage 0 missing / 30 dispositioned), Laguna package and drive.ts identical to the references,
Sonoma drive.ts differs as expected from the straight refit (heightfield.bin unchanged, track.json changed), vitest 426 passed
with one timing-budget test (ai_race "whole field step under 15 % of real time", 273 vs 258 ms) failing under the load of
thirteen parallel car builders; to be re-run idle before any merge.
Preview: https://probe-rgonplxjd-coby-hartmans-projects.vercel.app/?track=sonoma.

## The owner's notes, as built

| note | Astra | orchestrator's check |
|---|---|---|
| 63 T7 unused part + mouth kerb | FIXED: asphalt across the closed-road mouth, four delineators, the kerb starting beside the island | agreed |
| 64 / 69 Carousel-to-T7 edges | FIXED: straight legs, no lateral waves, consistent with the owner's satellite crop | agreed (two legs, drag strip 18.30 m, edge rms 0.009 / 0.020 m) |
| 65 T10 sunken wall + tan verge | PARTLY: green verge and an exposed wall base at T10, but `n65_T10_3160_after` still shows a depressed, stepped section of the left boarded barrier at about 3180-3230 | agreed on the still: the SONOMA RACEWAY boards step down between two taller runs with pale terrain wedges at the base; one row for round 12 |
| 66 infield building | NOT FIXED by Astra's reading (unchanged; it cannot verify the lidar from images) | by design: the pit garages measure 7.0 m on the lidar, as built; the owner decides |
| 67 wall on the dark line + bare tyre head | PARTLY: wall and fence present; the image does not resolve whether the tyre head's join is flush and protected | the package joins the wall to the tyre head (wall-ends gate 20/20 joined, tyre runs now checked); a closer still next round |
| 68 texture before T11 | FIXED: continuous asphalt, the pale shoulder gone | agreed |

Astra's other rows are all on the owner's round-10 screenshots (historical) and marked so. (Q1) the run-up reads as straight
legs. (Q2) what the owner would notice first: the stepped boarded barrier at T10, station ~3180-3230.

## Verdict

Round 11 closes notes 63, 64, 67, 68 and 69; note 65 keeps one row (the stepped boards at T10 ~3180-3230); note 66 stands on
the lidar for the owner's call. The physics (solid tyre walls) and the rollover screen are in the same package.
