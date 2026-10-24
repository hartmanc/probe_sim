# Buttonwillow judge round r6 (21 Oct 2026, ~02:45 PDT)

Judge: **GPT 6 Astra through codex** for 7 of the 8 batches (02:12-02:32; batch 4, side_05-side_11, failed twice with "Your
workspace is out of credits", stderr kept in `judge_r6/`), **the orchestrator (Claude)** for side_05-side_11 and for the check
of every Astra row against the package, the frames and the round-6 stills. Package: branch buttonwillow 7423383, rev
84a9fc7678, 4704.318 m (geometry byte-identical to round 5). Verified first: vitest 409 + 1 xfail, build, python 42,
Laguna + Sonoma package diffs empty, track.json + heightfield identical to the orchestrator's fresh round-5 build, TS gates +
coverage ok (87 rows, 0 missing), drive.ts on Laguna and Sonoma byte-identical to the pre-round-5 reference.

## Settled FALSE (cite the object in the ledger)

- **Stations "single post over a box" (fwd_14 4200-4250, side_02 477, side_03 996, side_04 1190, back_03 2100; orchestrator:
  side_05 1522, side_07 2053 / 2373, side_08 2776, side_09 3440, side_11 4273):** the frames (station_crops.jpg) show exactly
  that construction; Astra reads the inventory text. side_12 4502 L "EXTRA station": the pit-in station at the pit-wall head
  (pit video 20:40). back_00 500 R "EXTRA": the T1-exit station (t020).
- **Kerbs "missing" within the mapping tolerance:** 550 L (536-558), 600 R (584-604), 1000 R (1020-1049), 1150 R (1168-1191),
  1450 L (1449-1479), 2300 R (2315-2340), 2750 R (2765-2792), back_02 1600 R (1495-1515), back_03 2000 R (1868-1933), back_06
  3800 L (3845-3876), back_07 4400-4500 R (4424-4501), the runoff far-edge rows. fwd_14 4300 R "starts late": the capture puts
  the block line's start at 4321 (round 6). fwd_10 3000 L "EXTRA": the short line is on c20_s3100.
- **Single cones and short lines "missing" (placed, 0.7 m):** 900 / 950 L (895-905 + 973), 2150 R, 2700 L, 3650 R, 4550-4600 R,
  770 L, 1041 R, side_00 186 R (the 170 R mouth row, 3 cones), back_01 800-1000 L, back_05 3300 R, back_06 3700 R, back_07
  4600 R, runoff 57 / 293 / 171 / 679 / 1823 / 1924 / 4075 / 4617 (the 46 R, 170 R, 1824 R mouth rows and the singles).
- **Pit-lane lead-in cones 4490-4514 L (pit_01):** t1240000 shows three cones far ahead at the left wall; t1249000 (abeam 4528)
  shows none beside the wall: those are the 4612-4662 row seen from 120 m. The row stands as placed.
- **fwd_00 100 L / side_00 104 L "dark section missing":** it renders at s 98-104 (`r6_dark_krail_section_r6.jpg`); the hood
  at 100 looks past it.
- **pit_00 4294-4318 L fence "missing":** re-measured on the tree line 20-27 m out (fence_r6.png); too thin on the sheet.
- **fwd_02 800 R "barrier beside the post":** the station's pale raised base (t034).
- **side_13 4593-4662 L "a second taller white wall behind":** the paddock-side K-rail of the pit lane, 21 m out, real.

## TRUE and CHECK rows (round 7, cosmetic; geometry stays)

| row | finding | check |
|---|---|---|
| **Apron tone** (side_02 574 R "dirt/grass interior"; orchestrator: side_05 1309 R / 1344 L / 1476 L, fwd_04 1300-1450, the T2 inside apron still) | the `apron` surface fades into the photo's tan, so most of each apron reads as straw / dirt; the onboard shows pale grey-beige concrete (t024, t058) | TRUE: the apron's own colour must dominate (fade only the outer 1 m), the tone pale grey like the T2 runoff's |
| **Apron fade edge** (back_05 3000 R "jagged tan intrusions"; `paved_apron_right_s_2963-3025_r6.jpg`) | the 2.5 m alpha fade against the dirt reads as jagged bites | TRUE: a straight, narrower feather |
| **Tower roof** (fwd_15 4600-4650 "thin projecting slab") | the real roof has depth: a fascia ~0.6 m and the deck under it | TRUE, kit: roof thickness / fascia |
| **Tower annex** (pit_02 4640 "large opaque white annex"; `r6_tower_from_lane_r6.jpg`) | from the lane the 11 m shade roof on posts reads as a solid white block (its end wall + roof) | CHECK: open sides from the lane (the video t1312000 shows open frontage with a tent beside the tower) |
| **runoff_04 623 "dark/light division"** | the track's dark asphalt against the pale runoff: real, but the onboard's track is mid-grey and the division softer | low: the track tone at T2 is the ortho's; leave unless the apron tone change covers it |
| **pit_00 4294-4318 R "ground-coloured hatch field"** | the NAIP yellow hatch beside the pit entry, open since r2 | TRUE: an `ortho_paint_over` outline (the same step as the T4 smears) |
| **fwd_08 2550 R chevrons** | NAIP, open since r3 | same paint-over step |
| **fwd_00 0 L "low paddock buildings behind the wall"** (r5 too) | the paddock structures (lidar) were dropped for no 2026 source; the onboard at s 0 and the pit video show low buildings and canopies behind the pit wall west of the tower | CHECK: 3.7 `building_evidence` with the capture + video as the source; place the ones the video shows, plain |
| **fwd_10 3200-3250 L cluster** | t108 shows ~3 cones at metre spacing; the package has 2 at 3200 and the 3250-3300 line | CHECK the count on t108 (side_08 caption says three) |
| **side_00 21 R yellow cone** | the pair is yellow + orange in the package (round 6); Astra sees orange | CHECK the render (the yellow one's colour) |
| **pit_02 4690 R stand** | "sparse frame" vs the dense rails and ladder | low, the fine scaffold is right by t1339000; a rail density tweak |

## Ten worst rows of the lap

1. Apron tone (every apron reads as dirt).
2. The apron fade edge at 2963-3025 R.
3. The tower roof's depth and the annex reading as a white block.
4. The NAIP hatch at the pit entry and the chevrons at 2550 R (paint-over).
5. The paddock buildings behind the pit wall west of the tower.
6. The 3200 L cone count.
7. The yellow cone's colour at 21 R.
8. The pit stand's rail density.
9. The K-rail's sloped profile (kit, open since r5).
10. Nothing else: kerbs, stations, cones, the pit lane, the fence, the runoff and the geometry all hold.

## Verdict

Ready for the owner's second lap now; round 7 is cosmetic and leaves the geometry byte-identical.
