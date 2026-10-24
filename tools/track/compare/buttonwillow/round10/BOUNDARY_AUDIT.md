# Buttonwillow round 10: boundary audit (build-track 4.1b), 23 Oct 2026

Package `public/tracks/buttonwillow` rev 7acf260f50. Stills: `boundary_sheets.py poses` gave 969 poses (camera 1.2 m up, 6 m on the
unpaved side, looking across, every 25 m); `pose_walk.ts --tag b` on port 5179. **Tool defect found:** 214 poses share a name with another
(the 12 paddock-lane parts and the 2 parts of the front-straight pale strips and the front-straight crossover each restart their
`<zone>-<side>_<dist>` names), so the first walk overwrote them (755 files). Those 277 poses were reshot under unique names
(`-p00`..`-p11` per part, from `/tmp/bw_r10_prep/poses_dedup.json`); the tool itself is unchanged. Result: 969 stills, 41 sheets
(`boundary_sheets/sheet_000.jpg`..`sheet_040.jpg`). Round 8 had 743 stills and 31 sheets.

Every sheet was read at full size. Rows: kind, stations, side, what, and whether round 8 listed it. Station numbers for `edge_*`
poses are the package station the camera looks at (pose name minus about 15-40 m on the far part of the lap; the name is metres along
the edge polyline). Nothing was fixed (preparer only).

| sheet | pose(s) | kind | stations | side | what | round 8? |
|---|---|---|---|---|---|---|
| sheet_000 | area_T2-concrete-patch_0000 | paint | T2 apex (583 R) | R | a yellow-green curved line on the asphalt inside the kerb (paint line on the patch) | round 8 (T2 concrete patch, detail OPEN) |
| sheet_000 | area_apron-left-s-1305-1456_0025-0100, 0300 | tone step | apron L 1305-1456 | L | the apron reads as a flat pale grey band between track and dirt (a lighter strip with no edge feather) | new |
| sheet_000 | area_apron-left-s-3701-3783_0000, 0125, 0150 | overlap | apron L 3701-3783 (kerb L 3688-3756) | L | the kerb strip lies on the asphalt with the apron's pale band beyond; flush, no gap seen | new |
| sheet_000 | area_apron-right-s-1165-1239_0000 | tone step | 1165 R (NEW zone R 1172-1194) | R | a light smear on the asphalt at the kerb's start | new |
| sheet_000 | area_apron-right-s-1165-1239_0050 | paint | ~1210 R | R | a long black crack-seal line diagonal across the asphalt | new |
| sheet_001 | area_apron-right-s-1165-1239_0125 | overlap | ~1190 R (NEW zone R 1172-1194) | R | the new red / white kerb strip at close range: flush with the asphalt, its outer side meets a pale band then dirt | new |
| sheet_001 | area_apron-right-s-2963-3025_0000-0125 | tone step | apron R 2963-3025 (drag-strip mouth) | R | the apron's pale ground beyond the cone line is near-white against the asphalt (round 8: lighter triangle at the start) | round 8 (apron 2963-3025 R lighter ground, OPEN) |
| sheet_001 | area_apron-right-s-356-512_0000 | seam | 356 R (kerb R 361-376) | R | a red patch half under the dirt at the kerb end (kerb end buried / overlapped by the ground) | new |
| sheet_001 | area_apron-right-s-356-512_0025, 0050 | paint | 380-405 R (kerb R 411-425) | R | a blue kerb fragment and long dark marks along the edge line | new |
| sheet_001 | area_apron-right-s-356-512_0075 | seam | ~430 R | R | the edge's white line breaks with a triangular step where the apron meets the track | new |
| sheet_001 | area_apron-right-s-356-512_0175-0300 | tone step | apron R 356-512 | R | a pale grey band between track and dirt, as the other aprons | new |
| sheet_002 | area_apron-right-s-4133-4208_0075, 0150 | tone step | apron R 4133-4208 | R | a pale streak on the dirt beside the asphalt at the apron's end (smear, not a surface) | new |
| sheet_002 | area_apron-right-s-4406-4529_0000, 0075 | tone step | apron R 4406-4529 (kerb R 4419-4496) | R | a white smear on the apron beyond the kerb | new |
| sheet_002 | area_apron-right-s-4406-4529_0025 | paint | ~4430 R | R | a short black bar standing near the kerb (crack-seal mark seen end-on) | new |
| sheet_002 | area_apron-right-s-553-624_0050 | paint | ~600 R (T2 apex) | R | two long black crack-seal lines on the T2 asphalt | new |
| sheet_002 | area_apron-right-s-553-624_0075 | tone step | T2 apex apron | R | the apron reads as a flat light-grey slab against the darker track asphalt | round 8 (T2 concrete patch, detail OPEN) |
| sheet_002 / 003 | area_pit-in-gore_0000-0100 | seam / tone step | pit-in gore (pit entry L 4270-4314) | L | two asphalt tones meet on a straight line at the gore; a strip of dirt shows between the gore paving and the lane at 0000; a long black line on the asphalt at 0075 | round 8 (the slab was fixed in cp5; the tone step at the lane remains) |
| sheet_003 | edge_L_0000 | paint | 0 L (start line) | L | a white wedge (start line paint) sits on the track with a step to the pale lane paving | new |
| sheet_003 | edge_L_0075-0175 | seam | 75-175 L | L | a thin tan strip of dirt runs through the pale paving between the track and the pit lane (a gap between two paved meshes) | new |
| sheet_003 | edge_L_0025, 0075-0125, 0200-0250 | paint | 25-250 L | L | black crack-seal dashes across the front straight read as black bars | new |
| sheet_003 | edge_L_0375, 0400 | seam | ~387-411 L (paddock lanes mouth L 412-531 approach) | L | a jagged mosaic of dark asphalt and tan dirt shapes beside the edge, with a white line crossing it | new |
| sheet_003 | edge_L_0525 | overlap | ~515 L (NEW zone L 537-559 ahead) | L | the kerb strip with a pale band under its outer side on the dirt | new |
| sheet_004 | edge_L_0725 | seam | ~710 L (outer T2 loop mouth L 700-741) | L | a dirt triangle with a hard diagonal edge on the pale paving under the cone line | new |
| sheet_004 | edge_L_0750 | tone step | ~735 L (kerb L 745-767) | L | a white smear on the pale paving at the kerb's start | new |
| sheet_004 | edge_L_0775, 0900 | cone | ~760, ~885 L | L | a single cone stands on the dirt beside the edge (declared single cones; listed for C8) | new |
| sheet_004 | edge_L_1100, 1125 | overlap | ~1085-1110 L (T4 run L 1088-1117, moved flush) | L | the T4 kerb now lies flush on the asphalt edge; a faint pale band under its outer side, no gap | new |
| sheet_005 | edge_L_1325 | tone step | ~1311 L (apron L 1305-1456 start) | L | a white-grey blotch on the dirt with a soft edge | new |
| sheet_005 | edge_L_1450 | tone step | ~1435 L (apron) | L | the apron's flat pale-grey band between asphalt and dirt | new |
| sheet_005 | edge_L_1525 | seam | ~1507 L (Dog Leg mouth L 1503-1523) | L | a dirt rectangle with hard straight edges cut into the closed road's asphalt at the cone line | new |
| sheet_005 | edge_L_1550 | seam | ~1531 L | L | asphalt meets dirt on a hard diagonal; two dirt tones meet on a straight line | new |
| sheet_005 | edge_L_1675 | seam | ~1657 L (kerb L 1651-1678) | L | a strip of asphalt between the kerb and the dirt ends on a hard straight edge | new |
| sheet_006 | edge_L_1850 | tone step | ~1830 L (kerb L 1842-1852) | L | a white smear on the dirt beside the edge | new |
| sheet_006 | edge_L_1775, 1950, 1975, 2025, 2050 | paint | 1755-2030 L | L | long black crack-seal lines on the asphalt, some crossing the edge line | new |
| sheet_006 | edge_L_2000 | seam | ~1989 L (Dog Leg mouth L 1970-2002) | L | the closed road's asphalt meets the dirt on a hard diagonal under the cone line; a black line runs along the cones | new |
| sheet_006 | edge_L_2250, 2275 | pose | ~2232-2256 L | L | the track is not in the frame (dirt to the horizon): the pose looks over a rise or away from the edge; the boundary there is not audited | new |
| sheet_007 | edge_L_2725 | cone | ~2700 L | L | two cones on the dirt beside the kerb (declared: onboard t092, two orange cones) | new |
| sheet_007 | edge_L_2875 | overlap | ~2853 L (NEW zone L 2853-2859) | L | the new short blue / white strip at the edge, flush, no gap seen | new |
| sheet_008 | edge_L_3075-3225 | tone step | ~3052-3200 L | L | pale near-white ground beside the edge against tan dirt before and after | new |
| sheet_008 | edge_L_3225, 3275-3325 | cone | ~3200-3300 L | L | single cones on the dirt by the edge (declared: compare_sheets s3200, judge r5) | new |
| sheet_008 | edge_L_3525 | overlap | ~3487 L (NEW zone L 3475-3522) | L | the new left strip seen from the dirt: flush on the edge, no gap, no step | new |
| sheet_009 | edge_L_3650, 3675, 3700 | paint | ~3610-3660 L | L | crack-seal marks as black bars (3650: one stands near-vertical in the frame) | new |
| sheet_009 | edge_L_3775-3825 | tone step | apron L 3701-3783 | L | the apron's flat light-grey paving, a hard tone against the dirt | new |
| sheet_009 | edge_L_3875 | tone step | ~3840 L (kerb L 3841-3871) | L | a white wedge on the edge where the kerb starts | new |
| sheet_010 | edge_L_4225, 4500 | paint | ~4180, ~4460 L | L | crack-seal black bars on the asphalt | new |
| sheet_010 | edge_L_4350 | (ok) | ~4300 L (pit entry L 4270-4314, open) | L | the camera stands on the pit-entry paving: one asphalt surface into the lane, no cones, no seam seen | new |
| sheet_010 | edge_L_4375 | tone step | ~4325 L | L | an orange-toned dirt patch against the tan | new |
| sheet_010 | edge_L_4525 | (ok) | ~4475 L (mouth L 4484-4534) | L | the cone line stands on the edge line over pale ground | new |
| sheet_010 | edge_L_4550 | wall end | ~4500 L (pit wall start, barrier 0 at 4519) | L | the pose looks into the pit wall's start: a bare beige end face and a blue-grey slab fill the frame | new |
| sheet_010 | edge_L_4575 | seam | ~4525 L | L | a dirt rectangle with straight edges on the pale paving beside the track | new |
| sheet_010 | edge_L_4600-4725 | seam | ~4550-4690 L (pit-wall side of the straight) | L | tan dirt strips run through the pale paving between the track and the pit lane (same as 75-175 L) | new |
| sheet_011 | edge_R_0100 | tone | ~100 (pit wall, seen across the track) | L | one pit-wall panel renders black | new |
| sheet_011 | edge_R_0375 | tone step | ~375 R (kerb R 361-376) | R | a white smear on the dirt below the kerb | new |
| sheet_011 | edge_R_0400-0500 | tone step | apron R 356-512 | R | the apron's flat pale paving against the dirt, a soft white smear at its edge | new |
| sheet_012 | edge_R_0600 | overlap | ~600 R (T2 apex kerb R 584-604, T2 concrete patch) | R | kerb flush on the asphalt; the patch's pale paving meets the kerb on a soft line | round 8 (T2 concrete patch, detail OPEN) |
| sheet_012 | edge_R_0625, 0650 | overlap | ~620-640 (T2 outside tyre wall, seen across the track) | L | the tyre wall reads as a flat black band on the horizon | new |
| sheet_012 | edge_R_1175 | tone step | ~1172 R (NEW zone R 1172-1194) | R | a white smear on the dirt below the new strip's outer side | new |
| sheet_013 | edge_R_1250-1375, 1400 | paint | ~1250-1400 R | R | black crack-seal bars across the asphalt | new |
| sheet_013 | edge_R_1275 | tone step | ~1290 R | R | a small white blotch on the dirt beside the edge (C21) | new |
| sheet_013 | edge_R_1300, 1500 | overlap | ~1307 R (NEW zone R 1307-1312), ~1494 R | R | a kerb end seen as a short red wedge at the frame edge; no gap seen | new |
| sheet_013 | edge_R_1500, 1550, 1600 | tone step | ~1500-1600 R | R | a pale streak along the far (left) edge of the asphalt (seen across the track) | new |
| sheet_013 | edge_R_1650 | seam | ~1651 R (Atlantic / crossover mouth R 1651-1685) | R | a dirt shape with hard straight edges cut into the closed road's asphalt under the cone line | new |
| sheet_013 | edge_R_1775 | cone | ~1780 R | R | a single cone on the dirt by the kerb start (declared row) | new |
| sheet_014 | edge_R_1800 | seam | ~1800 R (kerb R 1778-1818 end, crossover mouth R 1820-1845) | R | the closed road's asphalt meets the dirt on a hard diagonal right at the kerb's end; a cone stands on that asphalt off the line | new |
| sheet_014 | edge_R_1825 | tone step | ~1825 R (mouth R 1820-1845) | R | pale near-white ground under the cone line; black lines run along and across the cone line | new |
| sheet_014 | edge_R_1925, 1950, 2000 | tone step | ~1925-2000 R (kerb R 1868-1932 end) | R | a white smear on the dirt beside the edge | new |
| sheet_014 | edge_R_1925, 1975, 2050, 2125 | paint | ~1925-2125 R | R | black crack-seal lines and a short standing bar on the asphalt | new |
| sheet_014 | edge_R_2125-2350 | tone step | ~2125-2350 R | R | pale blue-white ground beside the edge, a soft step to tan further on | new |
| sheet_014 | edge_R_2150-2275 | tone | ~2150-2275 R | R | the asphalt shows a bright white sheen band along its middle (lighting on the ribbon, not a texture) | new |
| sheet_015 | edge_R_2525 | tone step | 2525 (drag-strip mouth R 2533-2561) | R | the ground under the mouth cone line is a pale blue-white patch against the tan dirt either side | new |
| sheet_015 | edge_R_2950 | gap | 2950 (drag-strip mouth R 2973-3015) | R | a pale band of ground lies between the closed road's asphalt and the track edge under the cone line | new |
| sheet_015 / 016 | edge_R_2975, edge_R_3000-3150 | tone step | 2975-3150 | R | white / pale blue-grey ground beside the edge (bright patch) after the drag-strip mouth, against tan dirt from 3175 | new |
| sheet_016 | edge_R_3050, 3075, 3250, 3275, 3300 | paint | 3050-3300 | R | black crack-seal dashes on the track read as black bars across the asphalt from the dirt side | new |
| sheet_016 | edge_R_3175 | paint | 3175 | R | a long thin black line runs along the right edge (crack-seal mark on the edge line), with a single cone | new |
| sheet_016 | edge_R_3225 | seam | 3225 (Sweeper mouth R 3226-3250) | R | closed-road asphalt meets the dirt in a hard straight diagonal; cone line on the mouth stands on the asphalt | new |
| sheet_017 | edge_R_3600 | seam | 3600 (Sweeper south mouth R 3663-3683 approach) | R | closed-road asphalt meets the dirt in a stepped, notched edge with a dark band (a shading step) | new |
| sheet_017 | edge_R_3625 | seam | 3625 | R | a dirt triangle cut into the closed road's asphalt beside the cone line | new |
| sheet_017 | edge_R_4100, 4125, 4150 | tone step | 4100-4150 (Zorros mouth R 4162-4174) | R | a white strip of pale paving between the track edge and the dirt | new |
| sheet_018 | edge_R_4275 | tone step | 4275 (kerb R 4315-4364 approach) | R | a white smear on the dirt below the blue / white kerb | new |
| sheet_018 | edge_R_4575 | seam | 4575 (Pacific mouth R 4578-4606) | R | a grey asphalt triangle on the dirt with hard straight edges to the pale ground, beside the cone line | new |
| sheet_018 | edge_R_4575, edge_R_4650 | paint | 4575, 4650 | R | crack-seal marks stand out as black bars on the front straight (4650: a vertical black bar) | new |
| sheet_018 | pit_pit-left_0000 | seam | pit lane 0 m | L | the pit entry's asphalt wedge meets the dirt on a hard diagonal, two asphalt tones | new |
| sheet_019 | pit_pit-left_0175-0550 | tone | pit lane 175-550 m | L | the pit wall's red panels render near-black maroon from the paddock side (the lane side reads red) | new |
| sheet_019 | pit_pit-left_0375 | occlusion | pit lane 375 m | L | the frame is filled by a flat dark grey-olive face (camera behind or inside an untextured slab) | new |
| sheet_019 | pit_pit-left_0400 | tone step | pit lane 400 m | L | blue-green tint on the ground beside the wall | new |
| sheet_019 | pit_pit-left_0450-0500 | tone | pit lane 450-500 m | L | dark smudges on the ground at the wall foot | new |
| sheet_019 | pit_pit-left_0425, 0550 | wall end | pit lane 425, 550 m | L | a bare white K-rail end block standing on the dirt beside the asphalt | new |
| sheet_020 | pit_pit-right_0000, 0025 | tone step | pit lane 0-25 m (pit entry, T11 station) | R | two asphalt tones meet on a straight line (pit-in gore vs lane) | round 8 (the slab was fixed in cp5; the tone step at the lane remains) |
| sheet_020 | pit_pit-right_0200 | tone | pit lane 200 m | R | one wall segment drawn tan / beige next to the red and grey panels | new |
| sheet_020 | pit_pit-right_0300, 0325 | seam | pit lane 300-325 m | R | a thin tan line of dirt shows across the lane asphalt (a gap between two paving meshes) | new |
| sheet_020 | pit_pit-right_0375 | tone | pit lane 375 m (tower) | R | orange-pink ground with a white smear under the tower stairs | new |
| sheet_020 / 021 | pit_pit-right_0450-0575 | tone step | pit lane 450-575 m | R | green-toned ground beside the lane against tan elsewhere | new |
| sheet_021 | pit_pit-right_0750 | paint | pit lane 750 m | R | a black crack-seal bar on the lane / blend asphalt | new |
| sheet_021 | zone_Atlantic-left_0000, 0125 | ground | Atlantic mouth (R 155-187) | - | white blotches on the asphalt next to the cone line (C21) | new |
| sheet_021 | zone_Atlantic-left_0200 | seam | Atlantic far end | - | dark green X-shaped stripes on the pale dirt (overlapping strips or a z-fight) | new |
| sheet_021 / 022 | zone_Atlantic-right_0075, 0175, 0200 | seam | Atlantic | - | the road's asphalt ends square against the dirt; at 0200 dirt patches overlap the asphalt with jagged edges, a white blotch on it | round 8 (zone ends square-cut, OPEN), now seen at more roads |
| sheet_022 | zone_Dog-Leg-left_0400 | tone step | Dog Leg | - | a straight diagonal shading line across the dirt | new |
| sheet_022 | zone_Dog-Leg-right_0000 | seam | Dog Leg mouth (L 1970-2002) | - | a dirt triangle with hard straight edges on the asphalt by the cone line | new |
| sheet_023 | zone_Dog-Leg-right_0100, 0150, 0425 | seam | Dog Leg | - | the closed road's asphalt ends square; dirt patches overlap the asphalt with hard edges | round 8 (zone ends square-cut, OPEN), now seen at more roads |
| sheet_023 | zone_Pacific-left_0000, right_0000 | paint | Pacific mouth (R 4578-4606) | - | black crack-seal bars standing beside the cone line | new |
| sheet_023 | zone_Pacific-left_0025, right_0025 | ground | Pacific | - | a large white blotch on the asphalt (C21) | new |
| sheet_024 | zone_Pacific-right_0100, 0150 | seam | Pacific / front straight | - | the closed road's asphalt cut square into pale ground beside the track edge | round 8 (zone ends square-cut, OPEN), now seen at more roads |
| sheet_024 | zone_Sweeper-right_0175 | seam | Sweeper | - | a dirt triangle on the closed road's asphalt | new |
| sheet_024 / 025 | zone_T2-runoff-right_0000, 0025 | overlap | T2 runoff (606-641 L) | - | the T2 outside tyre wall reads as a flat black band on the horizon; pale concrete meets the asphalt on a hard edge | new |
| sheet_025 | zone_Zorros-left_0075, right_0100 | ground | Zorros | - | white blotches on the asphalt | new |
| sheet_025 | zone_Zorros-right_0075 | seam | Zorros | - | the road's asphalt cut square into pale dirt | round 8 (zone ends square-cut, OPEN), now seen at more roads |
| sheet_026 | zone_crossover-left_0000, 0150 | seam | crossover 34351015 mouth (R 1820-1845) | - | a dirt notch in the asphalt at the cone line; asphalt meets dirt on a diagonal | new |
| sheet_026 | zone_crossover-right_0000 | paint | crossover mouth | - | black crack-seal dashes in a line along the cone line | new |
| sheet_028 | zone_front-straight-pal-left-p00_0025 | ground | front straight (pit-wall side) | - | a yellow-tan patch on the asphalt (round 8: crossover left ~125 m) | round 8 (crossover left ~125 m, OPEN) |
| sheet_028 | zone_front-straight-pal-left-p01_0000 | tone step | front straight at the tower | - | a pale dirt rectangle on the asphalt with a white smear (hard tone step) | new |
| sheet_028 / 029 | zone_front-straight-pal-left-p01_0050-0175 | tone step | front straight west | - | green-toned ground against the pit wall (C11) | round 8 (pale strip west green ground; the paint-over did not remove it) |
| sheet_028 | zone_front-straight-cro-left-p01_0000 | paint | front-straight crossover | - | a long black diagonal crack-seal line across the asphalt by the kerb | new |
| sheet_029 | zone_front-straight-pal-left-p01_0100, pal-right-p01_0100 | tone | front straight | - | one pit-wall panel renders black instead of red | new |
| sheet_029 | zone_front-straight-pal-right-p00_0050, p01_0025, p01_0100 | paint | front straight | - | black crack-seal bars on the straight (0100: a thick one) | new |
| sheet_029 | zone_front-straight-pal-right-p01_0000 | paint | front straight | - | a wide white stripe across the asphalt by the tower | new |
| sheet_030 | zone_outer-T2-loop-left_0175-0225 | overlap | outer T2 loop (s 595-762) | - | the T2 outside tyre wall reads as a flat black band; a long black diagonal line on the asphalt (0200) | new |
| sheet_030 | zone_outer-T2-loop-right_0000 | tone step | outer T2 loop | - | a hard-edged pale patch where the loop meets the dirt | new |
| sheet_031-040 | zone_paddock-lanes-* (many) | seam | paddock lanes | - | lanes end square-cut against the dirt; dirt triangles with straight edges on the paving at junctions | round 8 (zone ends square-cut, OPEN), now seen at more roads |
| sheet_033 | zone_paddock-lanes-left-p06_0000 | ground | paddock | - | a red smear on the ground beside the lane | new |
| sheet_033 | zone_paddock-lanes-left-p07_0025 | pose | paddock | - | the camera is inside a building wall (pose inside a lidar building) | new |
| sheet_036 | zone_paddock-lanes-right-p01_0250 | ground | paddock | - | a red / pink and dark green smear on the ground | new |
| sheet_036-038 | zone_paddock-lanes-right-p01_0125, p04_0175-0300 | tone step | paddock | - | green-toned ground patches against tan | new |
| sheet_038 | zone_paddock-lanes-right-p06_0050, p08_0175 | ground | paddock | - | large dark blotches on the ground | new |
| sheet_040 | zone_paddock-lanes-right-p10_0000-0050 | pose | paddock / pit wall | - | the camera stands against a K-rail (a grey or pink slab fills the lower frame) | new |
| sheet_040 | zone_paddock-lanes-right-p11_0000 | ground | paddock | - | blue / yellow / red smears on the ground (a painted logo left in the ortho, C15) | new |

**124 rows: 111 new, 13 already listed in round 8.**

Round-8 rows not seen again: the pit-lane right ~175 m dark blotch and the Dog Leg 1900 L dark brown patch (both painted over in round 8
checkpoint 5) do not show in these stills.

Patterns across the rows (for the orchestrator, not a fix list):
- **Crack-seal paint lines** (`paint_lines`, 257 dark #2a2a2a strips 0.1 m wide, median 4.6 m long) read from the dirt side as black
  bars on the asphalt at almost every edge sheet; seen across the track at a low angle the ones lying across it stand out most.
- **Closed-road mouths**: where a closed road meets the track under its cone line, a dirt triangle or rectangle with hard straight
  edges cuts into the road's asphalt (1507 L, 1651 R, 1800 R, 1989 L, 2525 R, 3225 R, 3625 R, 4575 R): the road's paving ends square
  short of the round-10 edge or overlaps it.
- **Pale / white ground** beside the edge in long stretches (2125-2350 R, 2975-3150 R, 3052-3200 L, 4100-4150 R) and white smears at
  kerb ends (375 R, 1172 R, 1311 L, 1830 L, 1925-2000 R, 4275 R).
- **Seam between the front-straight track and the pit-lane paving** (75-175 L and 4550-4690 L): a thin tan strip of dirt.
- **Kerbs flush**: every strip seen from the dirt side (T4 1085-1110 L, the five new zones) lies flush on the edge with no gap and no
  step. A pale band shows under the outer side of several.
- **Pose problems** (not surface faults): edge_L_2250 / 2275 do not see the track; edge_L_4550, zone_paddock-lanes-left-p07_0025 and
  zone_paddock-lanes-right-p10_0000..0050 stand inside or against a wall or building.
