# Buttonwillow judge round r8 (21 Oct 2026, ~13:10 PDT)

Judge: **GPT 6 Astra through codex**, seven batches over the 50 round-8 sheets (12:49-13:03; prompt `judge_r8/prompt.md`, raw
tables `judge_r8/astra_b1..b7.md`), every non-OK row checked by **the orchestrator (Claude)** against the package (the
cone-line, kerb and barrier records of 4d85b8a against round 7's 886c22e), the frames, the ledgers and the round-5/6/7 judge
files. Package: branch buttonwillow 4d85b8a (round 8, checkpoints 1-5: the straights, raised kerbs with lifts advisory, the T2
tyre wall, the awning, the paddock, the willows, the T1 cones, the T2 patch, crack seal, the seam fixes), rev c0fbb9bd11,
4703.81 m. Verified first by the orchestrator at every checkpoint: vitest 409, build, python 42, Laguna + Sonoma package diffs
empty, drive.ts identity on both, stage-1 geometry byte-identical to the orchestrator's own build at checkpoint 1 and unchanged
since, TS gates + coverage ok. Preview: https://probe-bblimt5cn-coby-hartmans-projects.vercel.app/?track=buttonwillow.

## Settled FALSE (the package or the frames say so; cite the object in the ledger)

- **Kerbs "missing" within the 30 m mapping tolerance** (550 L, 1000 R, 1150 R, 1450 L, 1750 R, 1850 R, 4350 L, back_00 300 / 400 /
  500, back_02 1600 R, back_04 2400 R): the runs exist as in rounds 5-7 (6 kerb groups, every run re-sampled on the new edges);
  fwd_10 3000 L EXTRA: c20_s3100 (r5). The Dog Leg "long block run on the right" (fwd_06 1850): the separation block line, now flat.
- **Mouth and branch cone lines "missing"** (runoff 46 / 295 / 678 / 1571 / 1823 / 1926 / 4073 / 4617 / 4618, fwd_05 1500 L, back_02
  1600 L, fwd_07 2150 R, fwd_12 3650 R, fwd_13 4050 R, back_05 3300 R, back_06 3700 R, side_06 1924, side_07 2158): the package
  holds the same 30 cone lines as round 7 (16 re-sampled by the 0.5 m geometry shift, the 140-160 R line removed on t008's posts,
  the T1 pair replaced by the four t006 cones at 40-55 R); the 0.7 m cones are placed. Third judge in a row to miss them at
  30-60 m: see the CHECK on cone visibility below.
- **Stations "single stem over a box / solid pedestal"** (fwd_01 450, fwd_02 800, side_01 477, side_03 996, side_04 1175 / 1190,
  side_09 3440, fwd_06 2050, fwd_14 4200 / 4250, runoff_02 2768): the frames show that construction (station_crops.jpg, r5 / r6).
  side_12 4502 L / fwd_15 4500 L EXTRA: the pit-in station at the pit-wall head (pit video 20:40, r6). side_10 3765 R: the T10
  hut at 3698, behind the camera (r4).
- **Pit-lane lead-in cones 4493 / 4515 L** (pit_01): t1249000 shows none beside the wall (r6).
- **fwd_00 0 L paddock buildings "not discernible"**: 13 lidar buildings and the shade roof stand north of the lane (checkpoint
  2); low and far from s 0.

## TRUE and CHECK rows (checkpoint 6; geometry stays)

| theme | rows | finding | check |
|---|---|---|---|
| **Control tower massing** | fwd_15 4600 / 4650 (WRONG_HEIGHT 3-4 vs 6-7 m), side_13 4693 / 4695, pit_01 4542-4618, pit_02 4643-4693 (WRONG_TYPE) | the tower reads squat and elongated under a disproportionately broad roof with an enclosed window band; the pit video shows a COMPACT two-storey tan tower, open upper balcony on posts under a projecting roof, an exterior stair, ~8 m (caption) | TRUE, high: checkpoint 2 put the tower under the whole 25 x 19 m lidar roof. The tower's own footprint is the compact block (12-15 m along the lane, r5 judge; measure on c20_p0420 / c20_s0050 and t1312000 / t1339000); the big roof is the awning BEHIND it (owner note 14), an open shade roof on posts. Upper floor: open balcony with posts and rail, exterior stair, projecting roof; height from the lidar |
| **Station surrounds** | fwd_02 800 R, fwd_03 1150 R, fwd_07 2300 R, fwd_09 2750 R, fwd_11 3350 R, fwd_12 3700 R (MISSING wall 0.6-0.8 m), runoff_02 2768 | the onboard shows a low pale protective surround (tyre ring or low blocks) around most stations; the sim has it at some (Cotton, 1000 R) and not at these | TRUE, medium: per station from the frames (t034, t058, t074, t082, t112, t122 etc.): ring or none, height from the frame, as the kit's station tyre ring |
| **Apron and runoff tone** | fwd_01 400 R, fwd_02 600 L / 750 L, fwd_04 1200 R / 1350 L, side_02 574 R, side_12 4502 R, back_01 800 L, back_04 2600 L, runoff_05 623 (WRONG_TYPE / WRONG_COLOUR "broad uniform pale apron", "sharp regular band") | every apron reads as a uniform pale slab meeting the dark track along a hard line; the onboard's aprons are worn, patched pavement with a soft transition | TRUE, medium: the apron look needs variation (grain, patches, a darker worn tone nearer the track) and the track / apron boundary a wider feather on the APRON side; one look for all aprons, then the T2 runoff |
| **Remaining wedges and seams** | fwd_08 2550 R (sharp diagonal seam), fwd_09 2800 L (pale triangle), fwd_14 4300 L (ground wedge into the junction), side_02 590 R (jagged tan strip beside the T2 apex kerb) | tan or pale intrusions where two paved surfaces meet | TRUE (C17): the two seams the agent left open (the apron 2963-3025 R outline corner; the square-cut zone ends) plus these four; outlines re-traced on the captures, zone ends feathered |
| **Pit wall pattern and nose** | fwd_00 100 L / back_07 4600 L (WRONG_COLOUR: the first section unpainted beige, red sections shorter), pit_00 4469 R + pit_01 4493 R (the wall and its station start later than the pit video shows; the nose a "short white tapered nose" vs a substantial beige section), pit_01 4515 L (C1: a bare square end toward pit-in traffic) | | CHECK on t1231000 / t1240000 and c20_s4300: the nose's position, its unpainted first section, the red / white section lengths (`pattern` / `sections`), and the pit-in-facing end's cushion or cone row |
| **Pit-lane cone colour** | pit_02 4668 / 4693 L (fluorescent yellow-green vs orange) | | TRUE, small: per-cone colour from t1312000 |
| **T1 cones** | side_00 47 R (WRONG_COLOUR yellow + orange; WRONG_POSITION: on the paved crossover, not on the tan ground 3.8 m out) | the checkpoint-2 line stands on dirt beyond the pavement | CHECK on t006 and c20_s0050: the four cones on the pavement, colours as the frame |
| **T2 apex kerb** | fwd_02 600 R ("narrow uncoloured strips"), runoff_05 623 ("no coloured block pattern") | the T2 apex run 584-604 R may render narrow / uncoloured after the width pass | CHECK the render and the run's colours and width (the capture band) |
| **Dark K-rail section** | side_00 104 L, back_00 200 L (MISSING black section) | r6 said it renders at s 98-104; two judges since see none | CHECK its extent on t020 and the capture; make it visible from s 100 |
| **Wall extent at the T1 end** | fwd_00 150 / 200 L (WRONG_POSITION: the sim's wall runs farther than the onboard) | | CHECK the K-rail's end on c20_s0200 |
| **Masts** | fwd_10 3100 / 3250, fwd_11 3350 / 3400 (lattice mast reads as a thick dark shaft) | the lattice style renders solid at distance | low, kit: thinner members / lighter colour so the lattice reads |
| **Pit-entry fence** | pit_00 4296 / 4320 L (MISSING 1-1.3 m wire fence under the trees) | placed 20-27 m out on the tree line (r6); the pit video shows it close under the trees | CHECK against t138-t140 / the pit video frame; part of the infield fence, pending the owner's line |
| **4100 R kerb end** | fwd_13 4100 R (extends beyond the onboard endpoint) | | CHECK the run's end on the capture |
| **Cone visibility** | the runoff rows above | 0.7 m cones at 30-60 m vanish on three judges' sheets | CHECK once in the renderer: cone size, colour and the sheet's resolution; if real cones at that range are visible on the onboard and not in the sim, the draw is wrong |

## Ten worst rows of the lap

1. The control tower: squat and elongated under the awning's roof, enclosed upper floor (the owner sees it every lap).
2. Station surrounds missing at six stations.
3. Aprons as uniform pale slabs with a hard boundary to the track.
4. The six remaining wedges and seams.
5. The pit wall's pattern start and nose position.
6. The T1 cones off the pavement.
7. The T2 apex kerb's look.
8. The pit-lane cone colours.
9. The dark K-rail section not seen.
10. The lattice masts reading solid.

## Verdict

The package is drivable for the owner's third lap now (preview above); checkpoint 6 takes the rows above, geometry untouched.
The infield fence and the kart track stay open for the owner's line and more capture tiles.
