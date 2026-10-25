# Buttonwillow round 14: ledger (25 Oct 2026)

The owner's finding on his acceptance drive of round 13, scenery only. Branch `buttonwillow-r14` (from `integration`
95c8125); nothing pushed or deployed. Build records, caches and capture folders cloned from `probe_sim-wt/buttonwillow-r13`
(APFS `cp -c`, read only on the source). Package `public/tracks/buttonwillow`: rev **795c09c6cb -> b3f9b2d963**.
Machine: on the charger throughout (91-100 %), load under 3.1, disk 10-11 GB free; one heavy process at a time.

## The finding

Lap 1, 0:18, hood view of the left side of the front straight: **"this left hand section is not paved, it's just dirt.
The only paved sections should be the fishmouths that I outlined in green"**. In the package: the round-8 runoff zones
`front straight pale strip west` (s 4536-4700) and `east` (s 2-190), surface apron, paved the whole shoulder from the
course edge to the pit-wall K-rail (owner lap 2 note 23 had been read as a paved shoulder). Removed.

## 1. The fish mouths, from his green

His round-10 strokes (`owner_edges_r10/strokes.json`, the drawing page's vectors) converted to ENU with each window's
capwin frame (`owner/r10/w_s*.json`), drawn over the clean captures and the package (local crops). Evidence file:
`tools/track/tracks/buttonwillow/owner/r14_mouths.json` (outlines ENU and lat/lon), made by
`tools/track/compare/fish_mouths_r14.py`.

**What the green pieces are** (windows w_s4500, w_s4625, w_s0000, w_s0125, w_s0250):
- **Mouths** (pairs of turn-downs from the course edge): A (w_s0000 #13 / #14, the same in w_s4625 #12+#18 / #19+#13),
  B (w_s0000 #7 / #8), C (w_s4500 #4 + #10 / #6 / #5), E (w_s0250 #12 + #17 / #16).
- **The lane-side line** (the long stroke, w_s4500 #7, w_s4625 #16 / #17, w_s0000 #15 / #16 / #17, w_s0125 #6, w_s0250
  #18): the pit lane's own paving edge, 3.5-6 m NORTH of the pit wall: between the wall and this line the captures show
  a dirt / hedge median. At A and B his strokes flare from the wall up into this line (w_s0000 #12 / #11, #10 / #9): the
  channel's paving continues through the median.
- **Pit-in berm / lane outline:** w_s4500 #8, #9, #11 (the curving pit-in lane's two edges and the berm side).
- **Not left-shoulder mouths:** the coordinator's clusters x 162-170 (s 146-155) and x 186-204 (s 171-189) are on the
  RIGHT side (w_s0125 #2-#5, w_s0250 #7: the Atlantic crossover's mouth, y -217 .. -266, south of the course). The right
  side crossovers at x -17..-8 and 45..57 (w_s4625 #7 / #8 / #20 / #21, w_s0000 #2-#5, #26-#29) are the same infield
  crossovers continuing across the track into A and B.

| mouth | stations (package s) | outline (ENU, from his strokes) | width at the edge | width at the top | depth | top | captures / frames |
|---|---|---|---|---|---|---|---|
| A | 4661.3-4677.3 | west (-22.6,-222.0) -> (-19.8,-216.7); wall; east (-9.0,-215.9) -> (-6.6,-220.9) | 16.0 m (flared) | 10.8 m | 5.8 m | the pit wall (continuous) | c20_s4650 / c20_s4700 / c20_s0000; onboard t004000-t005000; pit-lane t1258000-t1312000 |
| B | 28.1-41.0 | west (43.3,-217.4) -> (44.5,-212.1); wall; east (54.1,-211.6) -> (56.0,-216.3) | 12.8 m | 9.6 m | 5.8 m | the pit wall (continuous) | c20_s0050 / c20_s0100; onboard t005500-t006500; pit-lane t1294000-t1303000 |
| C | 4483.3-4535.8 | (-200.2,-234.7) -> (-194.0,-225.2) -> (-195.3,-223.3); the lane's edge (1 m in) to x -172.6; #6 (-172.2,-222.0) -> (-171.3,-225.8); the wall to x -151.5; #5 (-151.0,-225.9) -> (-147.7,-230.5) | 52.6 m | 24.1 m (at the lane) | 11.2 m | the pit lane (west of the wall head), then the wall | c20_s4550 / c20_s4600; onboard t146000-t148500, t000000-t001000; pit-lane t1240000 |
| E | 206.2-213.7 | west (220.8,-204.7) -> (223.6,-200.3) -> (223.4,-196.0); the pit-out lane's edge (1 m in); east (228.0,-193.3) -> (228.3,-204.2) | 7.5 m | 5.3 m | 14.3 m | the pit-out lane (past the wall's east end) | c20_s0250 / c20_s0300; onboard t009500-t011000 |

E: his lane-side line (#13 / #18) stops 2 m short of the package lane's right edge there; the capture shows the grey
paving running on into the lane, so E reaches the lane's edge.

**Surface tone** (clean-capture medians, 0.1 m mosaic): the mouths RGB 162-177 / 153-168 / 144-158, R-B +18..+20,
saturation 18-20 (A 177/168/158, B 175/166/155, C 162-166/153-157/144-148, E 164/155/146): pale grey paving, paler than
the course (155/151/145, R-B +11) and close to the lane (167/158/151, R-B +16). The shoulder between them: R-B +26..+33,
saturation 26-34 (A west 138/121/105, x -140..-100 155/139/125, x 120..180 150/136/122): dirt. Mouths `surface='apron'`.
Onboard t002000-t006000: a brown strip between the asphalt and the K-rail, paving only at the mouths (t004500).

## 2. Pit wall openings: evidence

- 2026 captures, 0.03 m/px crops over A and B: the white / red K-rail (with its shadow) runs unbroken across both paved
  channels; the channel is paved on both sides of it.
- Pit-lane video ucmXJu5QKFQ, t1249000-t1321000 (right half at full resolution): the K-rail on the track side is one
  continuous run of white / red panels; a dirt strip lies between the lane asphalt and the K-rail, the asphalt reaching
  the wall only at the channels (t1312000).
- Onboard 7QS2M-HGSI4 t001500-t006000 (left side): the K-rail continuous along the whole straight.

**Decision: no openings.** The wall stays continuous; A and B are paved up to it (the channel north of the wall lies in
the pit lane's own paving, which is drawn and paved to the wall). C and E have no wall between them and the lane (C is
west of the wall head, E east of its end), so they join the lane's paving. No `gates.openings`, no containment change,
the pit connectivity lane path unchanged (388 / 382 m).

## 3. Config and builder

- `runoff_zones`: the two pale strips removed; six outline zones `front straight mouth A / B / C / C deep / E / E deep`
  (`outer_latlon` = his outline, `src` his words, window, strokes and captures). The round-8 left `asphalt_end` straight
  fit and the white edge line stay.
- Builder key `runoff_zones[].outline` (build_scenery.paved_zones `make_outline_part`): the strip's centre at a constant
  offset beyond the edge (the mid-line of `make_part` swung with the flares: the first build failed paved coverage with
  213 unpaved samples and a 0.6 m sliver along the edge), the outer edge where each section leaves the outline, `caps`
  per stretch and an inner start `from_m`. Why C and E are two parts each: the physics gives a point to the nearest
  centre (lane and zones are one list); the deep part's centre lies 3.4-3.7 m short of the lane's edge (the lane centre
  is 4.0 m beyond it), so the mouth / lane boundary falls just inside the lane, and shallow / deep meet on their
  bisector (C 3.5 m, E 5.1 m beyond the edge), the shallow cap kept inside the deep part's end point beside its ends.
  `outline.join_lane {reach 4}`: the deep part takes the lane's edge height (C lip 0.061 m closed, E 0.005 m).
  Tests `tools/track/test_round14_scenery.py` (7). Zones without `outline` are built as before (T2 runoff identical).
- `gates.paved_coverage.parts` + `'^front straight mouth '`.
- `ortho_paint_over`: the round-8 cp5 box "green-toned ground beside the pit-wall K-rail (pale strip west ~75 m)"
  removed: it painted the whole 12 m box (x 87-99, y -214..-202, shoulder and hedge) one flat tone, a slab on what is
  now the visible dirt shoulder.
- Inventory: no row cites the pale strip (the rows there are the K-rail, tower and pit rows): nothing to correct. The
  manifest's three pale-strip lines carry a round-14 note.
- Containment `allowed`: no entry names the strip; the existing pit-lane entries cover the rays through C and E
  (allowed 3296, unchanged).
- Cone lines and marks: the two cone lines on his red across A and B (round 10) only re-draped (|dz| <= 0.001 m); cones
  off the surface and ground marks on surface ok.

## 4. Build and gates

Stage 3 builds: the published one `--publish --overwrite-package`, exit 0, 0 `[FAIL]` (`/tmp/bw14/logs/stage3_pub.log`);
diagnosis builds went to `tools/track/out/bw14_diag` only (never published). Gate CLI (`run_gates.ts
public/tracks/buttonwillow`, the publish run's gates_config rebuilt with the builder's logic): every gate ok, exit 0.

| gate | round 13 (795c09c6cb) | round 14 (b3f9b2d963) |
|---|---|---|
| edge (rms / step), world continuity, profile | ok 0.066 / 0.066; 0.0076 / 0.0073; 0.017 | ok, same |
| owner reference / width / band | ok 0.381 / 0.328; 0.384; 0.136 / 0.120 | ok, same |
| barrier gaps | ok, 4.17 m / 17 runs | ok, same |
| containment | ok, 0 escapes, 3296 allowed, 78 junction | ok, same |
| pit connectivity | ok 388 / 382 m | ok, same |
| signs, wall ends, tyre facings, wall tops, wall-tyre joins, tyre faces | ok | ok, same |
| run gaps | ok, 2 openings, 0 holes | ok, same |
| terrain override | n/a | n/a |
| ground marks on surface | ok, 0 off (3610 paint, 15220 edge-line vertices) | ok, same |
| cones off the surface | ok, 182 / 38, deepest 0.00 m | ok, same |
| paved coverage | ok, 7 parts, 129,608 samples, 0 unpaved | ok, 13 parts (+6 mouth parts), 137,550 samples, 0 unpaved |
| coverage | ok, MISSING 0, UNSUPPORTED 0 | ok, same (87 rows, 161 objects) |
| pit lane | ok, 7 rows | ok, same |

Joins on the physics' surface (transects every 0.5 m, 0.05 m steps): C 0.012 m largest step (p99 0.002), E 0.011 m
(the shallow / deep boundary), A 0.001 m, B 0.001 m.

**The lane beside the straight, point by point** (`x -205 .. 240` every 0.25 m, from the course edge to 14 m beyond the
wall, rev 795c09c6cb against b3f9b2d963, 146,305 off-course samples):
- south of the wall: 27,985 paved -> unpaved (the shoulder, now dirt), 1,847 unpaved -> paved (C's nose area and E).
- north of the wall: 8,159 unpaved -> paved: the band 1.8-4.3 m beyond the wall that the pale strips' centres had taken
  from the lane (the lane's drawn paving) is lane again along the straight; 833 paved -> unpaved, all at x -175 .. -150
  (behind C's wall stretch and its deep part's end): the band 0.3-2.3 m beyond the wall (to 6 m at the wall head) now
  goes to the mouth's centre and is dirt in the physics. The real ground there is the dirt median (his lane-side line
  lies 4.5-6 m beyond the wall, c20_s4550 / c20_s4600, pit-lane t1249000), the lane's drawing shows asphalt. Behind A
  and B the same band was already dirt in 795c09c6cb.
- 26 lane samples within 0.25 m of the lane's right edge beside the deep parts' ends (x -197 .. -190, 220 .. 230):
  paved -> unpaved (1.6 m2).
- lane paved in both: max |dz| 0.0017 m.

## Identity

`git diff --quiet 95c8125`: public/tracks/buttonwillow track.json, heightfield.bin, ghosts.json, far_heightfield.bin,
far_ortho.jpg byte-identical (sha256 track.json 199358fe..., heightfield.bin 2c677efb..., ghosts.json e66b3218...).
ortho.jpg: 1,105 of 6.67 M pixels differ, all in x 83.4 .. 103.2, y -214.8 .. -195.0 (the removed paint-over box and its
JPEG blocks; 420 by more than 8 levels). scenery.json: `paved_zones` (the two strips out, six mouth parts in; the other
29 parts identical) and `cone_lines` (two lines re-draped) only. public/tracks/sonoma byte-identical (rev 3cf8227da0).
`src/scoreboard/config.ts` TRACKS.buttonwillow rev -> b3f9b2d963 (no `wip` on integration). PHYSICS_VERSION and the
changelog untouched.

Tests: `npm run build` clean; `npx vitest run` 65 files, **537 passed**, 0 failed; `pytest tools/track` **123 passed,
3 skipped** (116 + 7 round 14).

## Stills (local only, `round14/stills/`; pose_walk --port 5214, hood camera; `_before` = rev 795c09c6cb's scenery and ortho)

- `pairs_owner.jpg`: his pose, s 20 down the straight, yaw 0 and 25.
- `pairs_mouths_a.jpg`: s 4550, 4680, 35 looking left; `pairs_mouths_b.jpg`: s 180, 4505 (C), 212 (E).
- `pairs_mouths_close.jpg`: A from s 4655, B from s 22, C from s 4478, E from s 200 (yaw 40-45, each mouth ahead-left).
- `overhead_before.jpg` / `overhead_after.jpg` (+ `_W`, `_M`, `_E`): the physics surface over the captures (blue course,
  yellow lane and zones, cyan off-course paddock), his green strokes by window.

## Open (questions for the owner)

1. **The dirt median behind the pit wall.** His lane-side line lies 3.5-6 m beyond the K-rail from the wall head to x
   ~64 (s ~4510 to ~45); the captures and the pit-lane video (t1249000-t1303000) show dirt there, but the package's pit
   lane is paved and drawn to the wall (round 4). Should the lane's paving stop at his line (the median dirt, the paved
   channels of A and B through it)? Not changed: the lane's geometry was outside this round.
2. The cone lines across A and B on his red (round 10, cones=True) stay; round 13's onboard check did not cover them.
