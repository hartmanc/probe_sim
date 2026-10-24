# Buttonwillow judge round r5 (21 Oct 2026, ~01:50 PDT)

Judge: **GPT 6 Astra through codex** (credits back at ~01:00; same invocation as r2 and r3), eight batches over the 50
round-5 sheets, 01:12-01:34; prompt and raw tables in `judge_r5/`. Package: branch buttonwillow ec813d9, rev b3bd33079b,
4704.318 m (the owner's T2 and T4 edges in; the T2 runoff; 39 continuous kerb runs; the T9 apex run raised 6 cm; the texture
pass). The orchestrator (Claude) verified the round first (vitest 408 + 1 xfail, build, python 42, Laguna + Sonoma package
diffs empty, fresh stage-1 run byte-identical in track.json and heightfield.bin with 28 gate lines ok, Acceptance 6: Sonoma
byte for byte and Laguna's heightfield + d4e8634710813961, TS gates + coverage ok, hood set `hood_r5` 1.10 PASS on the new
T2 / T4 geometry, physics before / after round 5 identical on Laguna and Sonoma by drive.ts and self-play seed 1, Laguna's
rendering unchanged by eye at three poses), then checked Astra's 190 non-OK rows against the package, the frames and the
stills. Pit sheets 03-05 and runoff_04's pose list are unjudged as before.

## Settled FALSE (the package or the frames say so; the agent cites the object in the ledger)

- **Stations "on a single stem above a solid pedestal" (fwd_14 4250, side_02 477, side_03 996, side_04 1190, side_05 1522,
  side_07 2053, side_08 2776, side_09 3440, side_11 4273, back_01 900, back_03 2100).** The zoomed frames
  (`stage3_evidence/station_crops.jpg`: t034, t040, t046, t058, t074, t082, t092, t112, t122, t138) show exactly that: a flat
  canopy on one central pole over a cabinet on a raised pale base. Astra's "canopy on posts" comes from the inventory text,
  not the frames. The kit's canopy style stands.
- **Kerbs "missing" where a run exists within the 30 m mapping tolerance:** 600 R (run 584-604), 1150 R (1168-1191), 1450 L
  (1449-1479), 1650 L (1653-1680), 2750 R (2765-2792), back_02 1300 L (1203-1272), back_02 1600 R (1495-1515), back_03
  2000 R (1868-1933), back_07 4500 R (4424-4501), runoff rows 1668 L / 1833 L (far-edge visibility). side_04 1041 R EXTRA:
  settled real on c20_s1150 in round 4.
- **Single cones and short lines "missing" (placed, 0.7 m, too small for the sheet):** 300 R, 950 L, 1050 R, 1300 R, 1924 R,
  2150 R, 2700 L, 3650 R (3645-3655), 4050 R (4046-4054), 4618 R, 57 R / 293 R (the 46 R mouth cones), back_01 800-1000 L
  (752-772, 895-905, 973), back_05 3300 R, back_06 3700 R, runoff 170 R / 677 L / 1822 R / 1924 R.
- **back_07 4700 L "no tower looking back":** the tower stands beside the camera at 4640-4695, out of the rear view.
- **side_10 3765 R station:** the T10 hut is at 3698, behind the camera (as r4).
- **fwd_08 2550 R pale diagonal markings:** the NAIP chevrons at the drag-strip crossing, an open row since r3 (stage-2 paint-over).

## TRUE and CHECK rows (round 6)

| theme | rows | finding | check |
|---|---|---|---|
| **Timing tower massing** | fwd_15 4600-4650, side_13 4643-4693, side_14 4695, back_00 100, pit_01 4590, pit_02 4640-4690 | the sim draws an elongated glazed pavilion (continuous glazing on BOTH storeys under a broad roof). The pit video (t1312000, 21:52; t1339000) shows a COMPACT two-storey building: solid tan lower storey with a door and few windows, an upper storey with a deck and railing and windows, a deep roof overhang, an external stair; roughly 12-15 m along the lane, not 25 m | TRUE: the round-5 open-deck change glazed both storeys; the 25 x 20 m capture roof includes the attached low structure; measure the tower's own footprint on c20_p0420 / c20_s0050 and the video |
| **Pit lane paving** | pit_01 4540-4590, pit_02 4640-4690 (road_edge) | a white lane-edge line on the LEFT with a tan unpaved strip between it and the paddock-side wall; the video (t1267000, t1312000) has pavement to the wall base and no white line on the left | TRUE: `to_walls` did not take on the left / the left edge line must go |
| **Pit-lane cones** | pit_01 4490-4514 L, pit_02 4665-4690 L | round 4 removed every lane cone; t1267000 shows a short row of 4-6 small orange cones along the LEFT (paddock-side) wall ahead of the tower (abeam ~4600-4660), t1312000 two more at the tower's foot (one yellow) | TRUE: one short cone line from those frames, counted and spaced from them; none elsewhere |
| **Pit-entry fence** | pit_00 4294-4318 L (WRONG_POSITION), fwd_14 4300 L (EXTRA) | the sim's 1.5 m fence runs 1-2 m from the lane; the video frame shows it along the tree / paddock boundary 5-10 m from the lane, and from the track at 4300 the onboard shows an open verge | TRUE: re-measure the fence on c20_s4300 / c20_s4350 (the tree line) |
| **Pit-wall nose** | pit_01 4490 R | "an isolated station plinth followed by a wall run with an exposed square beginning" vs the video's broad concrete terminal continuous with the separation barrier under the shade station | CHECK on t1231000 / t1240000: the nose, the station and the barrier as one continuous end |
| **Surface look: aprons and the T2 runoff** | fwd_00 200-250 R, fwd_01 400 R / 550 L, fwd_03 1150 R, back_01 800 L (aprons "missing"); side_02 574 R (a raised rounded bank); runoff_04 623 R (a dark band across the apron) | the `apron` surface reads as tan dirt without grain, so every apron reads as unpaved; the T2 runoff in the track's dark asphalt tone cuts a dark band across the pale outer-loop pavement; at 574 R the inside apron reads as a raised earth bank | TRUE: aprons and the T2 runoff as pale weathered asphalt WITH grain (the onboard's pale grey pavement), one look for both; check the inside-T2 heights (the apron must sit at the track's level, not on a bank); check whether a T1-inside apron exists at 200-250 R on c20_s0300 |
| **Crossover mouths** | side_00 21 / 46 / 146 R, fwd_15 4600-4650 R (road_edge) | a tan strip still separates the track from the zone road at the mouths after `paved_zones_over` | TRUE (open from the texture pass): the zone must meet the track edge with no gap |
| **NAIP paint smears** | fwd_09 2800-2850 L (EXTRA: a broad white diagonal), plus the T4 ~1100 / ~1203 rows from the texture pass | bright NAIP marks kept as paint | TRUE: a stage-2 paint-over list with capture outlines |
| **Kerb extents to confirm** | fwd_14 4300 R (run starts 4321), fwd_14 4350 L (run starts 4381), fwd_01 550 L (run ends 549), back_00 500 R (410-424), fwd_14 4400 L (colour: "pale edging without coloured blocks") , fwd_10 3000 L (EXTRA: 3005-3013 L) | the onboard shows the T11 approach kerb from ~4300 and the inside blocks from ~4350 | CHECK each on the captures (c20_s4400 / c20_s4450, c20_s0600, c20_s3050) and the frames t140-t144 |
| **Masts** | fwd_11 3400 L (lattice comms tower as a thin pole), back_05 3500 R (no head cluster seen) | open since r3 | kit: a lattice style for the comms tower; check the floodlight head's size from behind |
| **Small rows** | side_00 21 R (one cone is yellow), side_00 104 L (the dark K-rail section not seen), fwd_10 3200 L (cluster density), side_13 4693 L (the starter's stand's heavy frame + solid canopy vs a fine scaffold), fwd_15 / side_00 (K-rail drawn as a vertical slab, real: sloped faces), fwd_15 4600 L ("stepped" red/white sections near the building) | | per-cone colour; check the dark section renders at s ~101; the cluster count from t108; the stand's frame; the K-rail profile and the section joins are kit items, low |

## Ten worst rows of the lap

1. The timing tower as an elongated two-storey glazed pavilion (the real one compact, solid below, deck and windows above).
2. The pit lane's left edge: a white line and a dirt strip where the video has pavement to the wall.
3. Aprons and the T2 runoff reading as dirt / a dark band: the surface look, not the geometry.
4. The pit-entry fence 1-2 m from the lane instead of 5-10 m on the tree line.
5. The crossover mouths' tan strips.
6. The short left-wall cone row in the pit lane (removed in round 4, present in the frames).
7. The NAIP paint smears at 2800-2850 L and T4.
8. Kerb extents at the T11 approach and apex (4300-4320 R, 4350-4380 L).
9. The pit-wall nose's continuity with the station and the barrier.
10. The masts' heads.

Settled since r4: the T2 and T4 geometry on the owner's lines, the T2 runoff drivable and contained, the kerbs continuous,
the T9 apex run raised, the pit-entry strip gone, the stations as the frames show them.
