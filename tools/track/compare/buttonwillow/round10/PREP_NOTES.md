# Buttonwillow round 10, stage-4 prep notes (23 Oct 2026)

Package `public/tracks/buttonwillow` rev 7acf260f50 (HEAD e1dba23), lap 4699.19 m. These notes list what looks wrong
in the round-10 compare sheets before the judge reads them. They are the preparer's list, not a judge round: nothing was
changed in the package, the config, the gates or the tests.

## How the sheets were made

- **Camera walk (4.1): replayed.** `camera_walk.ts --replay` on the round-8 `walk.json` (copy at
  `/tmp/bw_r10_prep/walk_r8.json`): 289 poses shot again (fwd 95, left 37, right 47, back 48, pit 31, runoff 31). The
  round-8 stills were moved to `/tmp/bw_r10_prep/sim_r8/` first, so `compare_sheets/sim/` holds only round-10 stills.
- **Do the replay poses still sit on the track?** Yes. Every on-centre pose (fwd, rows, back: 227) lies inside the
  round-10 edges; the closest is `fwd_s1150` (T4), 1.02 m inside the left edge. But the round-8 centre is not the
  round-10 centre: 81 of the 227 poses are more than 1 m off the round-10 centre, 33 more than 2 m, 4 more than 3 m
  (`fwd_s1150` 4.31 m, `fwd_s2400` / `back_s2400` 3.84 m, `row_s2373_right` 3.58 m). The station of each pose on
  the round-10 centre differs from its caption s by -5.6 to +1.8 m. So the replay was kept (the brief's rule), and the
  judge should read `fwd_s1150` as a view from beside the left edge, not from the centre.
- **Compare sheets (4.2):** 50 sheets (fwd 16, side 14, back 8, pit 6, runoff 6), `compare_sheets/index.md`. Same
  sheet names and station ranges as round 8. The round-8 sheets are kept at `/tmp/bw_r10_prep/sheets_r8/` for a
  side-by-side.
- **Touched sheets:** all 50 (`round10/judge_sheets.txt`); the flush kerbs lie on every part of the lap. Two pit
  sheets (pit_03, pit_05) are marked weak.

## The two black things the round-10 stills show

**What they are in the package.** Both are `scenery.json` `paint_lines`, the crack-seal marks (`surface_marks`, 579
candidates on the clean captures, 257 kept; round 8 had 407 inside the wider round-8 edges). Each is a straight
two-point strip, 0.1 m wide, colour `#2a2a2a`, median 4.6 m long (p10 3.2 m, p90 9.2 m). `buildPaintLines`
(`src/app/scenery.ts`) draws them as flat quads with MeshLambert and a polygon offset. They lie 0-0.08 m above the
interpolated track surface: they are flat, not standing up.

- **Pit-entry straight (`pit_entry_s4290_r10`):** six marks at stations 4280-4323, five of them lengthwise. Three sit
  on the centreline (lateral 0.1, 0.0 and -0.3 m; 5.3, 14.5 and 6.3 m long) and one at -0.6 m (13.1 m), all measured
  on `c20_s4400` / `c20_s4450`. From the hood they line up as a dashed black centre line.
- **T2 apron at s ~641 (`t2_exception_s641_r10`):** the bar in the foreground is a crack-seal mark on the T2 asphalt
  inside the left edge. The nearest are at 605 (+5.8 m, 4.8 m long), 607 (-4.7 m, 5.6 m), 614 / 615 (-4.9 / -2.8 m) and
  613 / 623 (lying across the track). The still is shot 25 m before 641, turned 30 degrees left, so the bar is one of
  the 605-623 marks a few metres from the camera. At that range a 0.1 m strip is about 18 px wide.
- **Why they read as bars.** They are near-black against grey asphalt and dead straight. A lengthwise mark seen from
  behind projects as a short vertical bar: `fwd_s3900`, `fwd_s1600`, `fwd_s1650`, `fwd_s3800` and edge_L_3650 show a
  black stroke that seems to stand up in the lane.

**Do they look like the onboard?** In part.
- The onboard has real crack seal everywhere: dark, wavy, branching lines, many more than the sim, and some long ones
  (fwd s2400-2600, s400, s600, s1300, s3600). On the T7-T8 straight (`fwd_08`) the sim's long dark lines look much like
  the onboard's.
- Elsewhere the sim's marks are sparse, short, straight, uniform and darker than the real seal (which reads dark grey).
  On the pit-entry straight they form a dashed centre line. The onboard at s4250-4350 (`fwd_14`) shows tyre marks and
  wavy seal on the left half, not a centre line.
- At T2 the onboard (`fwd_02` s600-650) shows wavy dark cracks across the apron and no single straight black bar.

## Compare sheets: what looks wrong (preparer's list, not the judge's)

Station mapping can be off by up to 30 m, and the replayed poses sit up to 4.3 m off the round-10 centre.

**Kerbs**
- Kerbs are hard to see. In most forward pairs the onboard kerbs are wide and saturated red / white / blue. The sim's
  are thin and pale at the same distance, or not visible:
  - `fwd_00` s200 / s250: the onboard's long right kerb (R 189-268 in the package) does not show in the sim.
  - `fwd_09` s2750: the onboard's right kerb (R 2763-2790) does not show.
  - `fwd_14` s4450: the right kerb (R 4419-4496) does not show.
  - `fwd_04` s1450: the left kerb (L 1454-1478) does not show.
  - `fwd_11` s3500: the new left zone L 3475-3522 is faint.
  - `fwd_12` s3750-3850: the left kerb is thin and pale.
  - From the side and from the dirt (`side_04`, `side_09`, boundary sheets), the strips are in place and flush.
  - So in the forward view this is visibility (colour, width at a glancing angle), or the poses' offsets.
- **New zone R 1307-1312 is 6 m long.** `side_04` s1304 / s1309: the onboard shows the T4-exit right kerb running about
  30 m. The sim shows a short faint piece with the single cone.
- **New zone R 1172-1194:** it does not show in `fwd_s1150`, whose pose is 4.3 m off the centre beside the left edge.
  In `side_04` s1175 it is faint. The onboard at s1150 shows it ahead on the right.
- **New zone L 537-559:** it does not show in `fwd_s0500` / `s0550`, where the onboard at s550 shows the blue / white
  kerb ahead-left. `side_02` s531 is turned into the car's own A-pillar and does not show it.
- **New zone L 2853-2859:** nothing shows in either the onboard or the sim at s2850 (`fwd_09`).
- **T4 run L 1088-1117 (flush now):** `side_04` s1088 and `fwd_03` s1100 show it on the edge, as the onboard does. No
  gap or step is seen.

**Cone lines on his mouths** (all 19 are his decision 2; listed where the onboard at that station shows none)
- `fwd_00` s200: a cone line on the LEFT (mouth L 207-213). The onboard s200 shows nothing on the left.
- `fwd_05` s1500: big cones close on the left (Dog Leg mouth L 1503-1523). The onboard shows a few far-left cones.
- `fwd_05` s1650: a cone line on the right (R 1651-1685). The onboard s1650 shows a kerb on the left and no right
  cones; the sim's left kerb (L 1651-1678) does not show.
- `fwd_08` s2550, `fwd_10` s3000: cone lines on the right (drag-strip mouths R 2533-2561, R 2973-3015). The onboard
  shows none there.
- `fwd_13` s4150: a cone line on the right (Zorros R 4162-4174). The onboard shows a pale open area.
- `fwd_15` s4500: a cone line on the left by the station (L 4484-4534). The onboard shows none.
- `fwd_15` s4600 / s4650: cones on the right (Pacific R 4578-4606). The onboard shows the open paved area and no line
  (judge r3 read two single cones there, open item 2 of the ledger).
- **On the mouth:** in the boundary sheets the lines stand on the edge line over the mouths. At 1507 L, 1651 R, 1800 R,
  1989 L, 2525 R, 3225 R and 4575 R the closed road's asphalt ends in a hard-edged dirt shape under or beside the line
  (BOUNDARY_AUDIT.md).
- At 1800 R one cone stands off the line on the asphalt by the kerb end.

**Pit entry (L 4270-4314, open)**
- `pit_00`, edge_L_4350 and `fwd_14`: no cones at the pit entry, and the lane is open into the paving.
- The pit-in gore still shows two asphalt tones on a straight line (round-8 row).
- The crack-seal dashes on the pit-entry centreline are above.

**T2 (s 600-650) and the cut stub (s ~571)**
- `fwd_02` s600 / `back_01` s600: the T2 outside tyre wall (barrier 15, `#202020`, 1.0 m) reads as a flat black band
  on the horizon. The onboard at T2 shows no such dark band. This is not new in round 10 (unchanged barrier).
- The T2 runoff is open, and the exception line stands across the alternative section beyond it (`t2_exception_s641`).
- `side_02` s574 R: dirt inside the hairpin, no paved stub, as the onboard.
- A yellow-green curved line lies on the T2 concrete patch (`side_02` s590 R, boundary area_T2-concrete-patch_0000).
  That pose has no onboard frame, and the onboard at `fwd_02` s600 shows no such line: the judge should check it.

**Edges**
- No 20-80 m edge wave is visible in the forward or back sheets.

**Surface**
- A bright white sheen runs along the middle of the asphalt (`fwd_06` s1850-2050, edge_R_2150-2275). It is lighting on
  the ribbon, not in the onboard.

**Closed-road edges from his green**
- Seen from the track they look the same as round 8 at hood distance.
- From the dirt (boundary sheets), the roads' paving still ends square or leaves hard-edged dirt notches at the mouths
  (above).
- The paddock lanes (0-20 green points) show the same square ends and dirt triangles at their junctions.

**Weak sheets:** `pit_03` and `pit_05` show no round-10 change in view.

## Second pass: the sheets with no rows yet (24 Oct 2026)

Each sheet read at full size, in batches of four; rows are written after each batch. The count is 30, not the 29 in the first report: fwd_07, 11 side sheets, 7 back sheets, 5 pit sheets and 6 runoff sheets.

| sheet | s (m) | side | kind | what the sim shows against the onboard |
|---|---|---|---|---|
| fwd_07 | 2150 | right | cone | a single cone at the right edge; the onboard shows none at this time (declared single cone at 2158 R; position along may be off) |
| fwd_07 | 2300 | right | kerb | the onboard shows a long red / white / blue right kerb (R 2314-2339) ahead; the sim shows only a faint stripe far ahead |
| fwd_07 | 2100-2350 | both | surface | the sim's asphalt is clean grey with no crack seal; the onboard has dark crack lines (2350: a long one down the middle) |
| side_00 | 21 | left | wall | pit-wall K-rail with red panels, tower behind: as the onboard |
| side_00 | 21 | left | cone_line | a cone line in front of the pit wall (owner mouth L 29-41); the onboard frame looks ahead and cannot show it |
| side_00 | 47 | right | cone_line | two cones on the dirt beyond the edge; the caption says yellow and orange, the sim's are both orange |
| side_00 | 146 | right | cone_line | two cones on the dirt (Atlantic mouth); no onboard frame |
| side_00 | 186-216 | right | kerb | the right kerb is a thin, pale stripe; the onboard's (R 189-268) is wide and bright |
| side_01 | 246 | left | station | the T1 station does not show in the frame (trees and the far paddock only); the onboard frame looks ahead and cannot confirm it |
| side_01 | 256, 296 | right | kerb | the sim's right kerb is faint against the onboard's wide kerb; the single cone at 296 R does not show |
| side_01 | 300, 408 | left / right | kerb | kerbs flush at the edge, thinner and paler than the onboard |
| side_01 | 477 | right | station | the T1-exit station is a canopy on a tyre-ringed mound: as the caption |
| side_03 | 833 | right | station | the station does not show; the frame shows tyres at its right edge only |
| side_03 | 893 | left | cone_line | two cones on the dirt; no onboard frame |
| side_03 | 972, 996 | left | kerb | the left kerb (L 954-1011) is flush and faint; one cone at 972 L |
| side_03 | 996 | right | station | the T3 station with a tyre ring, as the caption (the canopy is black, not blue as the caption says) |
| side_03 | 1041 | right | kerb | the right kerb (R 1020-1049) is visible and flush; the single cone is not in view |
| side_05 | 1344 | left | kerb | the left kerb (L 1338-1395) is a thin, faint stripe along the edge; the onboard's is wide and bright |
| side_05 | 1476 | left | kerb | the left kerb (L 1454-1478) does not show; the onboard shows a kerb ahead on the right |
| side_05 | 1492 | right | kerb / station | the right kerb and the T5 station (canopy on a tyre-ringed mound) are present; the station is close to the kerb |
| side_05 | 1522 | right | station | the station is out of frame (the dirt and far trees only); the onboard shows it beyond the kerb on the right |
| side_05 | 1645 (x2) | left | kerb | the left kerb (L 1651-1678) is barely visible; the onboard shows a kerb ahead on the left. The two pairs are duplicates (the same pose shot twice) |
| side_06 | 1773 / 1793 | right | cone_line | cones in two rows over the drag-strip / crossover paving; no onboard frame. The second row stands ~10 m further out |
| side_06 | 1824 | right | cone_line | a cone line across the crossover mouth on the asphalt, with one big cone off the line close to the track (the 1800 R cone) |
| side_06 | 1839 | left | kerb | the left kerb (L 1842-1852) is bright and flush: as the onboard |
| side_06 | 1878 | right | kerb | the right kerb (R 1868-1932) is faint; the onboard's is wide |
| side_06 | 1924 | right | cone | the single cone at the kerb's end does not show in frame (no onboard frame) |
| side_07 | 2022 | left | ground | dirt only, as the onboard |
| side_07 | 2053 | right | station | the T6 station on the right, as the caption; the paving beside it is the apron |
| side_07 | 2158 | right | cone | the single cone is a small fleck at the far edge; the onboard shows it clearly at the edge |
| side_07 | 2313 / 2373 | right | kerb / station | the right kerb (R 2314-2339) is present but faint; the station on a mound, as the caption |
| side_07 | 2696 | left | kerb / cone | the left kerb (L 2686-2744) is visible and flush; two cones, as the caption |
| side_08 | 2760 / 2776 | right | kerb / station | the right kerb is bright and flush; the T8 station stands on a pale concrete pad (no tyre ring), as the caption |
| side_08 | 2857 | left | kerb | new zone L 2853-2859: not visible in this frame (dirt and the T8 apex). The onboard shows white paint marks on the asphalt here, not a kerb |
| side_08 | 3196 | left / right | cone | single cones at both edges, as the captions (no onboard frames) |
| side_08 | 3287 | left | cone_line | three widely spaced cones on the left; caption: orange cones along the left |
| side_10 | 3765 | right | station | the T10 station is out of frame (dirt and the far kerb only); the caption logs a corner station there |
| side_10 | 3787, 3914 | right | kerb | the right kerbs (R 3790-3806, R 3890-3930) are faint stripes; the onboard's are bright |
| side_10 | 3848, 3981 | left | kerb | the left kerbs (L 3841-3871, L 3967-4018) are visible and flush, thinner than the onboard's |
| side_10 | 4045 | right | cone_line | two cones on the right apron, as the caption |
| side_11 | 4065 / 4070 | right | cone / kerb | one cone, as the caption; the right kerb (R 4024-4121) does not show, while the onboard shows a white / blue kerb |
| side_11 | 4122 | right | kerb | the right kerb does not show (pale edge only); the onboard shows it at the edge |
| side_11 | 4273 | left | station / pit entry | the T11 approach station (canopy, tyre ring) under the trees; the pit-entry paving open beside it, no cones: as decided |
| side_11 | 4308 | right | kerb | the right kerb (R 4315-4364) does not show yet; the onboard shows it ahead |
| side_11 | 4371 | left | kerb | the left kerb (L 4376-4401) is visible far down the edge, faint |
| side_12 | 4410, 4458 | right | kerb | the right kerb (R 4419-4496) does not show; the onboard at 4458 shows a wide kerb on the right |
| side_12 | 4502 | left | cone_line / wall | a dense cone line (owner mouth L 4484-4534) in front of the station and the pit wall; the onboard frame (t0) shows the K-rail and no cones |
| side_12 | 4502 | right | runoff | flat dirt; the onboard shows a paved area on the right (caption: runoff) |
| side_12 | 4573 | right | cone | one cone on the dirt at the Pacific mouth; the onboard shows a single cone on pale ground |
| side_12 | 4593 | left | wall | the pit wall with red panels and trees behind; the onboard shows the K-rail and the tower further on |
| side_13 | 4593 | right | cone_line | three big cones close together on pale paving, off a clean line (Pacific mouth line R 4578-4606 plus the declared single cones); the onboard shows one cone |
| side_13 | 4599 / 4643 | left | wall | pit wall K-rail with red panels: as the onboard; black crack-seal dashes on the asphalt in the foreground at 4599 |
| side_13 | 4662 | left | cone_line | a cone line in front of the pit wall (owner mouth L 4662-4676); the onboard shows one cone near the wall |
| side_13 | 4693 / 4695 | left | building | control tower with blue flat roof: as the onboard |
| back_00 | 0 → 4599 | sim right (track left) | wall / cone_line | pit wall with red panels; a cone line ahead along the pit side (mouth L 4662-4676); the onboard shows the K-rail and the tower but no cone line |
| back_00 | 100 → 0 | - | wall / building | the tower and the pit wall at the end of the straight: as the onboard |
| back_00 | 200 → 100 | sim left (track right) | cone_line | a long cone line on the right of the straight (Atlantic / crossover mouths R 155-187, R 31-41); the onboard's view of that stretch shows none |
| back_00 | 300, 400 → 200, 300 | both | kerb | the T1 kerbs (L 284-323, R 189-268) are faint; the onboard's are wide and bright |
| back_00 | 500 → 400 | sim left (track right) | station | the T1-exit station with its tyre ring: as the onboard (seen from the other end) |
| back_02 | 1200, 1300, 1400 | both | kerb | the T4 kerbs show only as faint slivers; the onboard's are wide and bright. A black crack-seal stroke stands up on the asphalt at 1300 |
| back_02 | 1500, 1600 | - | surface | no kerb and no crack seal; the onboard shows a long crack line and the T5 kerb |
| back_02 | 1700 → 1600 | sim left (track right) | cone_line | a line of small cones far down the right (R 1651-1685); the onboard has none |
| back_03 | 1800 → 1700 | both | cone / kerb | cones at the left edge and a kerb on the left (L 1651-1678); the onboard shows the left edge open with tyre marks |
| back_03 | 1900 → 1800 | sim left (track right) | kerb | the kerb is faint; the onboard shows the kerb and cones on the right |
| back_03 | 2000 → 1900 | sim left (track right) | cone_line | a cone line across the crossover mouth (R 1820-1845) with big cones near the edge; the onboard shows the kerb and a few cones on the right |
| back_03 | 2100 → 2000 | sim right (track left) | station | the T6 station with its tyre ring: as the onboard |
| back_03 | 2200, 2300 | - | surface | clean asphalt, no kerb; the onboard shows long crack seal |
| back_04 | 2400-2700 | - | paint | black crack-seal strokes stand up in the lane in each frame; the onboard shows long dark seal lines lying along the lane |
| back_04 | 2400 → 2300 | sim left (track right) | kerb / station | the T7 kerb (R 2314-2339) does not show; the station is at the frame's left edge |
| back_04 | 2800 → 2700 | sim right (track left) | kerb / cone | the left kerb (L 2686-2744) is faint; the onboard shows the wide kerb and a cone |
| back_04 | 2900 → 2800 | sim right (track left) | kerb | new zone L 2853-2859 does not show; neither does the onboard show a kerb there |
| back_05 | 3000 → 2900 | sim left (track right) | cone_line | big cones close to the edge, then a line along it (drag-strip mouth R 2973-3015); the onboard view of that stretch shows none. A black crack-seal stroke stands up in the lane |
| back_05 | 3100, 3200 | - | surface | clean asphalt; the onboard shows long crack seal |
| back_05 | 3300 → 3200 | sim left (track right) | cone_line | cones at the right edge (Sweeper mouth R 3226-3250); the onboard shows a few small cones on the left |
| back_05 | 3400, 3500 | both | kerb | the T9 kerbs are faint slivers; the onboard at 3400 shows the wide right kerb |
| back_06 | 3600 → 3500 | sim right (track left) | kerb | the new left zone L 3475-3522 does not show from behind; the onboard (forward) shows a wide kerb |
| back_06 | 3700 → 3600 | sim right (track left) | cone_line | a faint cone line far away (Sweeper mouth R 3663-3683) |
| back_06 | 3800, 3900, 4000 | both | kerb | the T10 kerbs are faint stripes; the onboard's are wide and bright. A black stroke stands up in the lane at 3900 |
| back_06 | 4100 → 4000 | sim right (track left) | kerb | the right kerb (R 4024-4121) does not show; a black crack line runs along the right of the lane |
| back_07 | 4200 → 4100 | sim left (track right) | cone_line | a short cone line far ahead (Zorros mouth R 4162-4174); the onboard shows none |
| back_07 | 4300 → 4200 | - | paint | a long black crack-seal line runs down the middle of the lane toward the camera (the pit-entry centre marks); the onboard shows none |
| back_07 | 4400 → 4300 | sim right (track left) | kerb | the right kerb (R 4315-4364) shows as a red / white stripe: as the onboard |
| back_07 | 4500 → 4400 | sim right (track right of travel) | cone_line | cones on the right of the frame on the paving (owner mouth L 4484-4534); the onboard shows the open area |
| back_07 | 4600 → 4500 | sim left | cone_line | a cone line by the station (L 4484-4534) and big cones close by; the onboard (forward) shows the pit wall and one cone |
| back_07 | 4700 → 4600 | - | wall | the pit wall with red panels; cones far down the straight |
| pit_01 | 4493-4618 | both | wall | K-rail with red panels on both sides of the lane: as the pit-lane video |
| pit_01 | 4493 / 4515 | right | station | the T11 station's canopy and a cone line on the track side (beyond the wall); the video shows the low tower and the K-rail |
| pit_01 | 4493 | - | surface | the lane ahead is a pale near-white paving on the right; the video shows tan dirt and the lane's grey asphalt |
| pit_01 | 4542-4618 | left | cone_line | the six small cones at the paddock-side wall foot do not show at this distance; the video shows cones along the left wall |
| pit_02 | 4643 / 4668 | both | wall / building | the K-rail with red panels on both sides and the tower ahead: as the video. The video's tower is tan with a blue roof and a balcony, and the sim's matches it |
| pit_02 | 4643 | left | cone_line | one cone at the paddock-side wall foot; the video shows several small cones along the left wall |
| pit_02 | 4693 | right | station / tower | a scaffold-style stand on the right; the video shows a white scaffold platform on the right: as the video |
| pit_02 | 4693 | left | cone | the fluorescent yellow-green and orange cones at the tower foot do not show (the frame is at the tower) |
| pit_02 | 14-64 | right | surface | a green-toned strip of ground between the lane and the track (the round-8 front-straight green ground); no video frame |
| pit_03 | 89-215 | right | surface | the green-toned strip between the lane and the track continues; one black wall panel at 89 / 114 |
| pit_03 | 190 / 215 | right | station | the T1 station's canopy at the lane's right; the lane ends into pale paving |
| pit_04 | 238-405 | - | pit-out | the lane runs out as one surface with the track: no seam, no wall at its end. No video frame; a dark tyre-mark band crosses the lane at 380 |
| pit_05 | 410 | - | pit-out | the end of the lane at the track edge on the right; no change in view |
| runoff_00 | 1571 | Dog Leg | closed road | asphalt underfoot meets dirt on a hard diagonal; the track beyond with no kerb or cones in view |
| runoff_00 | 1752 | Dog Leg | closed road | the camera stands on dirt: no paving underfoot, and the track is a thin band at the horizon. Either the pose sits off the road or the road's paving ends short here (edges from his green) |
| runoff_00 | 1926 | Dog Leg | closed road | grey paving underfoot at the lower left, dirt ahead; the cone line of mouth L 1970-2002 does not show |
| runoff_00 | 1652 | front-straight crossover | cone_line / kerb | the cone line across the mouth (R 1651-1685) and the kerb from the paving: plausible; the onboard shows the kerb at this place |
| runoff_00 | 678 | outer T2 loop | closed road | pale paving underfoot meets dirt ahead; the T2 track is a dark band; no cones in view (the line at L 700-741 is behind or off-frame) |
| runoff_00 | 471 | paddock lanes | closed road | dirt underfoot, trees ahead; no paving and no track in view: the pose does not show the lane |
| runoff_01 | 566 | paddock lanes | closed road | pale paving underfoot to the left, dirt and trees; the T2 track not in view; no stub seen (the cut OSM stub is gone) |
| runoff_01 | 4156 | paddock lanes | closed road | dirt with a pale paved strip ahead, trees: the track is not in view |
| runoff_01 | 4273 | paddock lanes (pit entry) | closed road | pale paving with dirt patches underfoot, trees; no cones, as decided; the track is not in view |
| runoff_01 | 295 | pit lane | pit-out | dirt underfoot; the track a thin dark line at the horizon: the pose is off the lane |
| runoff_01 | 4419 | pit lane | pit lane | dirt underfoot, the track's edge on the left: the pose is off the lane paving |
| runoff_01 | 120 | Atlantic | closed road | grey paving underfoot; the pit wall with red panels and the tower beyond the track: as the onboard |
| runoff_02 | 1669 | Atlantic | closed road | dirt underfoot, the track a thin line: the pose is off the paving |
| runoff_02 | 1767 | crossover 34351015 | closed road | dirt underfoot; a faint cone line far away |
| runoff_02 | 1823 | crossover 34351015 | cone_line | standing behind the mouth's cone line on the paving, a cone close in front: plausible; the onboard shows cones and the kerb here |
| runoff_02 | 4666 | crossover 34351015 | closed road | pale paving underfoot meets dirt; the pit wall and tower across the track: as the onboard |
| runoff_02 | 2622, 2768 | drag strip | closed road | dirt underfoot at both poses, the track a thin band: neither pose shows drag-strip paving |
| runoff_03 | 2914 | drag strip | closed road | dirt underfoot, the track a thin band: the pose shows no drag-strip paving |
| runoff_03 | 4073 | drag strip | closed road | dirt, trees: the track is not in view |
| runoff_03 | 46 | front-straight crossover | closed road | paving underfoot to the left, dirt to the right; the tower and the pit wall beyond: plausible; the onboard shows the K-rail and the open straight |
| runoff_03 | 1700 | front-straight crossover | cone_line | dirt underfoot; a cone line and a pale paved strip in the distance |
| runoff_03 | 1835 | Pacific | closed road | grey paving underfoot meeting the track: one surface; no cones in view |
| runoff_03 | 4617 | Pacific | cone_line | the Pacific mouth cone line on the paving between the camera and the track, the pit wall beyond; the onboard (from the track) shows the open paved area and the wall |
| runoff_04 | 3268 | Sweeper | closed road | dirt underfoot, the Sweeper mouth cones far off: the pose shows no Sweeper paving |
| runoff_04 | 3603 | Sweeper | closed road | dirt underfoot, the track on the right: the pose is off the paving |
| runoff_04 | 2544 | Zorros | closed road | dirt with a pale paved strip ahead running to the track; plausible |
| runoff_04 | 4235 | Zorros | closed road | dirt, trees: the track is not in view |
| runoff_04 | 4618 | front straight pale strip west | zone | grey paving underfoot; cones across the far side (Pacific mouth): plausible |
| runoff_04 | 96 | front straight pale strip east | zone | grey paving underfoot running into the track: one surface, as the onboard |
| runoff_05 | 623 | T2 runoff | zone | pale concrete underfoot meeting the T2 asphalt on a hard line; a black crack-seal stroke stands up on the asphalt (the bar of `t2_exception_s641`); the exception cone line does not show in this frame |

**Second-pass summary (30 sheets, 128 rows).**
- **Runoff poses (checked after the pass; data in `/tmp/bw_r10_prep/runoff_check.py`).** 15 of the 31 runoff stills
  show dirt beyond the hood rather than the paved area they are named after: 1752, 471, 4156, 4273, 295, 4419, 1669,
  1767, 2622, 2768, 2914, 4073, 3268, 3603 and 4235.
  - Every one of the 15 pose points lies inside its own paved zone (or the pit lane) in both the round-8 package
    (`/private/tmp/bw10/pkg_r8/scenery.json`) and the round-10 package. The paving did not shrink in round 10, and the
    poses are not off.
  - The cause is the framing: along the view direction each pose leaves its zone after 0.5-5 m, which is about where the
    hood ends. The ground in view is the dirt beyond the zone's edge.
  - In 5 of the poses (471, 4156, 4273, 1669, 4073) the view never reaches the track.
  - A fresh walk would not change this: `runoffPoses` places the camera 4 m inside the polygon by the same rule. The
    judge should be told the runoff sheets show the place from just inside each road's edge, not the road's paving.
- **The same patterns as the first pass.** Kerbs are faint or invisible against the onboard's wide bright kerbs. Mouth cone lines stand where the onboard at that station shows none (back_00 s200, back_02 s1700, back_03 s2000, back_05 s3000 / s3300, back_07 s4200 / s4500 / s4600, side_12 s4502, side_13 s4593 / s4662). Crack-seal strokes stand up in the lane (back_02 s1300, back_04 2400-2700, back_05 s3000, back_06 s3900, back_07 s4300 on the pit-entry centre). The clean asphalt has no crack seal where the onboard has long seal lines (fwd_07, back_02, back_03, back_05).
- **Pit lane.** It matches the video on walls and the tower. The six small cones at the paddock-side wall foot do not show at hood range (pit_01 / pit_02). The round-8 green strip between the lane and the track remains (pit_02 / pit_03). The pit-out is one surface (pit_04).
- **New in this pass.** side_05 s1645 is the same pose shot twice (a duplicate in the walk). The Pacific mouth at side_13 s4593 has three big cones close together off the line. side_08 s2857: neither the onboard nor the sim shows a kerb at the new zone L 2853-2859, and the onboard has white paint marks there instead.
