# Buttonwillow round 14: ledger (25 Oct 2026)

The owner's finding on his acceptance drive of round 13, scenery only. Branch `buttonwillow-r14` (from `integration`
95c8125); nothing pushed or deployed. Build records, caches and capture folders cloned from `probe_sim-wt/buttonwillow-r13`
(APFS `cp -c`, read only on the source). Package `public/tracks/buttonwillow`: rev **795c09c6cb -> b3f9b2d963 -> 2503ea567c** (the second after the review round below,
which supersedes the first's lane numbers).
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


## Review round (GPT 6 Astra, HOLD: one blocker, two fixes, three notes; 25 Oct 2026)

Rev b3f9b2d963 -> **2503ea567c**. The pit lane's drawn extent is unchanged (the dirt-median question stays the owner's).

### 1. BLOCKER: the lane's drawn asphalt paved in the physics (fixed)

Cause: the physics gives a point to the part whose centre is nearest (lane and zones are one list); the mouths'
centres, 0.5 m beyond the course edge, were nearer to the lane's samples behind the pit wall than the lane's own centre
(8.7-9.5 m beyond the wall), and a part's END takes every nearer point beyond it. Fix: the pit lane's own paving at
each mouth as a band part (`runoff_zones[].band`, build_scenery `make_band_part`): spanning the lane's full width, drawn
as the lane (asphalt) on the lane's own heights, its centre over the mouth the mirror of the mouth's centre about their
boundary (2 x wall distance - 0.5 m at A / B: the boundary on the wall line; 3.5 m beyond the lane's edge at E), bending
over 20 m (A, B) / 10 m (E) onto the lane's centre line and ending on 3 m of the lane's own points (equal centres: the
lane comes first in the physics' list, so the lane beyond the band is the lane's). Mouth C's deep part is now such a band
across the nose and behind the wall stretch (centre 6.5 m beyond the course edge, bending over 28 m at both ends), its
inner edge on the bisector with C's shallow part (3.5 m; where the deep centre bends near its west end the shallow
cap follows the bisector, `cap_knots`), beyond his line #5 (s 4532.6) from the wall only. The drawn look: C's paving
beyond 3.5-7 m from the course edge now reads as the lane (asphalt) rather than apron (stills below).

A seam found by the new lane scan that was not this round's: the end of OSM paddock lane 10409813 (x -132.6, y -201.5,
6 m north of the paddock-side K-rail) took the lane's samples 0.4-1.0 m from that K-rail at x -140 .. -127 (dirt since
round 8). The way is declared with its first node 4.0 m further north (y -197.5): 4 m of the paddock lane (paved on
satellite_paddock/pad_0) are dirt in the sim now; said here.

**Gate:** `gates.paved_coverage.lane_box [-205, -245, 245, -175]`: the gate now scans the pit lane's drawn strip beside the
straight too (same 0.25 m grid, 0.4 m round barriers, 0.1 m round drawn edges, strict). Published: **17 parts, 232,192
samples, 0 unpaved** (the lane's strip in the box 102,590 samples with the mouths, 0 unpaved). vitest: without mouth A's
band the gate finds the lane seam behind mouth A (all holes there).

**The lane, point by point against 95c8125** (its drawn strip in the box, 0.25 m, the gate's exclusions; 94,809 samples):
paved -> paved 85,188, **paved -> unpaved 0**, unpaved -> paved 9,621 (the band the round-8 pale strips had taken), unpaved ->
unpaved 0; where paved in both, max |dz| 0.013 m (x 235, E's band end; the boundary steps are the table below, not zero).

### 2. FIX: outline validity verified, not repaired (fixed)

`outline_polygon`: the closed outline must be a simple ring, run the right way round (increasing s) and not backtrack
along the track by more than 1.5 m; otherwise the stage fails naming the zone (no `buffer(0)`). More than one run of
stations fails (no "longest run kept"). `check_strip`: every generated strip (outline and band) with an edge on the
wrong side, an edge running backwards or two sections crossing fails. The traversal bug: `d6` was sorted south-first,
so C's outline went up #6 from the wall head and back down to the wall (a zigzag); now north first, and the end of his
#10 hook that lies inside the lane is cut at the top. Proof (`owner/r14_mouths.json`, `max_backtrack_m`): A 0.36 m, B
0.03 m, C 0.05 m, E 0.59 m (his own strokes' curls), every outline a simple ring traversed once. Tests: a
self-intersecting, a reversed, a backtracking and a gapped outline each fail; crossed / reversed / wrong-side strips fail.

### 3. FIX: the lane join (fixed)

`join_lane_outline`: inside the lane a part's profile points take the LANE'S OWN DRIVEN HEIGHT (`lane_surface_z`: the
physics' rule restricted to the lane's parts), outside it the correction of the section's outermost inside point fades
linearly over `reach`, and along the part over `reach` from the last section that meets the lane; fewer than 75 % of
sections meeting the lane fails. `planar` (C, C deep, E, E deep): outside the lane the heights lie on one straight line
per station from the course edge to the lane's own height at its right edge, so shallow and deep parts sample one
line (their boundary keeps the interpolation between each part's own profile points: millimetres, measured below). Test on a lane sloping 2 % across and 0.1 % along: the part's height at the boundary within 5 mm of the lane's.

**Steps measured** (transects every 0.5 m across, 0.05 m along each, every ownership boundary crossed: shallow / deep,
deep / lane, band / lane, mouth / band at the wall, including the parts' ends; 0.4 m round the barriers left out):

| region | round 14 rev 2503ea567c | 95c8125 there |
|---|---|---|
| C, x -205 .. -140 | 0.0029 m at (-188, -222.35) | 0.0015 m |
| A, x -40 .. 10 | 0.0022 m | 0.0030 m |
| B, x 15 .. 80 | **0.0074 m** at (70.5, -200.85), B's band / lane boundary in its east bend, 1.3 m from the lane centre | 0.0038 m |
| E, x 195 .. 240 | 0.0039 m at (224, -191.45) | 0.0019 m |

(b3f9b2d963 had 0.0117 m at C's lane join and 0.0154 m at C's shallow / deep boundary.) The 7 mm in B's bend is the
band's 7 fractions across the lane against the lane's own: left as measured.

### 4. NOTE: ends by evidence

Each mouth part's two ends (its drawn samples within 3 m of its first / last section): A 140 / 104, B 114 / 142, C 92 /
122, C deep 362 / 763, E 107 / 244, E deep 378 / 378, A band 761 / 787, B band 762 / 497, E band 361 / 362 samples, **0
unpaved** at every end. Beyond his outlines and the lane's drawn strip (course edge + 0.3 m to the lane): 105 paved of
46,199 samples, 13 of them more than 0.3 m outside, at most 0.6 m (C at the top of #4 / #10, x -195; C at the top of #5,
x -151; B's band at x 71.5). Paving he drew that is not drawn: about 2 m2 at C's #4 / #10 top (s 4489.8-4491.5) and 0.6
m2 at the top of #5 (s 4532.6-4533.5), where a shallow and a deep part cannot both reach.

### 5. NOTE: wording

The overlap claims are reworded to what was measured: the transects of item 3, the gate of item 1.

### 6. Stills (local, `round14/stills/review/`; `_before` = rev b3f9b2d963)

`pairs_review_a.jpg`: mouths A (s 4655) and B (s 22), the cone lines gone; C (s 4478); E (s 200). `pairs_review_b.jpg`:
the lane at C's nose and behind it, the lane at E. `overhead_after_W / M / E.jpg`: the physics surface over the
captures: the lane paved to the wall everywhere beside the straight, the mouths his outlines.

### Cones at A and B (the owner's round-13 rule)

Onboard 7QS2M-HGSI4 at 0.5 s, left side at full resolution: A t004000-t005000 (the mouth's paving to the continuous
K-rail at t004500), B t005500-t006500: no cone on or across either mouth. Both round-10 lines removed (`owner_mouths_r10`
left 29-41 and 4655-4669, cones=False with `cones_src`). Cones 182 -> 168 on 38 -> 36 lines. No inventory row describes
these lines (they came from his round-10 red); nothing to correct there.

### Gates and identity (rev 2503ea567c)

Stage 3 `--publish --overwrite-package` exit 0, 0 `[FAIL]`; build == package (every file); gate CLI on the package: every
gate ok, exit 0 (containment 0 escapes, 3296 allowed; pit connectivity 388 / 382 m, lane paths 0 obstacles; cones off
the surface 168 / 36; ground marks 0 off; paved coverage as item 1). track.json, heightfield.bin, ghosts.json,
far_heightfield.bin, far_ortho.jpg identical to 95c8125; ortho.jpg differs only in the paint-over box (1,105 px, x
83.4 .. 103.2, y -214.8 .. -195.0); Sonoma identical (3cf8227da0). TRACKS.buttonwillow rev 2503ea567c. Tests: `npm run
build` clean; vitest 65 files **539 passed** (537 + 2); pytest **131 passed, 3 skipped** (116 + 15 round 14).

## Second review round (GPT 6 Astra, HOLD, eight items) and the owner's decisions of 26 Oct 2026

Rev 2503ea567c -> **29f4afedba**. Astra's fixes first, then the owner's four items, one build. Every number below was
measured on the published package (physics surface, `createTrackSurface` / the gate's `plainSurface`).

### A1. The lane box derived, not hand numbers

`gates.paved_coverage.lane = {margin: 10}`: the box is the bounds of every named part's drawn strip (the round-13 set,
below) grown by 10 m: **[-210.42, -244.70, 238.44, -129.68]**; the pit lane's drawn strip inside it **77,779 samples,
0 unpaved** (925 within 0.1 m of a drawn edge left out). `lane_box` is gone from the gate and the tests.

### A2. OSM 10409813's footprint restored; the lane seam at x -140 .. -127

The aisle's own part ends at y -197.73 (its declared first node); across its end a block part (`scenery.block_parts`,
build_scenery `block_part`): its centre line runs through the aisle's end point (1 cm beyond it, moved +0.76 m from the
declared y -198.5) with a centre point there, so every sample beyond the aisle's end has a block centre point nearest
(the physics' nearest-centre rule; the aisle's `over` region is a 5 mm sliver), halves 4.04 m (north, over the aisle's
end) / 3.01 m (south, to y -200.75: round 13's end), x -136.8 .. -128.2, the aisle's own heights. Its centre is 8.5 m or
more from the lane's samples by the paddock-side K-rail (the lane's centre is 8.2 m), so it takes none.
Coverage: the aisle beside the lane is checked (`also: ^paddock lanes`, within 10 m of the lane's strip): **443
samples, 0 unpaved**. Against 95c8125, point by point: **(a)** every sample of 95c8125's paddock strips paved there,
**523,044: still paved 523,044, 0 now unpaved**; **(b)** the new lane strip, paved in 95c8125: **81,227, still paved
81,227, 0 now unpaved** (max |dz| 11.5 mm at (-195.5, -224.25), C's nose, the band below). vitest: the footprint box
x -136.4 .. -128.8, y -200.55 .. -197.2 is paved at every 0.2 m sample; without the block it is not.

### A3. Mouth C pale over the mouth; the lane's asphalt only over the lane

C's apron part draws pale over all of his outline (`draw_full`); the C lane band (`make_lane_band`, on the lane's own
stations) is not drawn (`draw: false`); the lane draws its own paving, which now stops at his line (O1). The band's
right edge reaches toward the course only inside his C outline (`lane_band.within`: from the lane's edge along each
section as far as his outline runs; a section whose lane edge lies outside it keeps the lane's edge): to the course at
24 of 121 stations. Stills (local, `round14/stills/r3/`): `mouthC_s4478`, `laneC_nose`, `laneC_behind_wall`
(`pairs_r3_a.jpg`): the nose reads pale over the mouth, asphalt over the lane, dirt beyond his line.

### A4. B's join step; the bent band in the physics

B has no band now: its centre is the lane's centre mirrored about the pit wall's line (`outline.centre = 'mirror_wall'`),
so the nearest-centre boundary with the lane lies on the wall and the lane paves the channel above it itself. C: the
apron part takes the band's own surface wherever its profile points lie in the band (`outline.surface_from`, 196 of
1,477 points, change -4.4 .. +4.2 mm), so the two meet on one surface. **Transects** (physics, every 0.5 m across, 1 cm
along, from the lane's centre 15 m toward the course, every paved sample; max |dz| between neighbours / max second
difference):

| region | rev 29f4afedba | rev 2503ea567c | 95c8125 |
|---|---|---|---|
| A, x -30 .. 0 | 1.86 mm at (-8.5, -221.04): the course edge itself / 1.89 | 1.05 | 1.08 |
| B, x 35 .. 65 | **0.19 mm** / 0.14 | 0.68 | 0.54 |
| C, x -205 .. -150 | 1.90 mm at (-184.5, -233.48) / 1.93 (3.90 before `surface_from`) | 3.41 | 0.28 |
| E, x 215 .. 232 | 0.48 mm / 0.53 | 3.81 | 0.08 |

(Astra's 7.4 mm at B was measured her way; on these transects rev 2503ea567c shows 0.68 mm there.) A's maximum is the
course's edge (paved -> on track at y -221.04), not a part boundary. Tests: pytest
`test_lane_band_meets_the_lane_with_its_surface_on_a_bent_band` (the C construction, kinked and bent back, on a lane
twisting 1-3 % across: every 1 mm sample across paved, worst step beyond the slope < 0.1 mm); vitest transects on the
package (< 3 mm per cm at A, B, C, E).

### A5. Round-13's check kept exactly

The round-13 check samples the named parts' drawn strips with their own edge exclusions, as before; the lane, the aisle
and his outlines are three separate sample sets, each with its own exclusions. The only change to the round-13 set:
a part with `draw: false` (none existed in round 13) has no drawn strip and is not in it (its paving is checked as the
lane's and his outlines'). Published: **12 parts, 139,086 samples, 0 unpaved** (5,428 on an edge left out).

### A6. Outline validation: closed (no change).

### A7. His outlines, paved

`gates.paved_coverage.outlines = 'runoff_zones'`: each mouth's outline as he drew it (`owner_outline_latlon`, else
`outer_latlon`), closed 3 m inside the course; every sample in them off the course must be paved: **4 outlines, 10,227
samples, 0 unpaved** (449 on an outline edge left out). What made it so: sections every 0.25 m; each section's outer
edge the farthest reach of its own ray and the rays a third of a step either side; a push where a corner of his outline
lies between two sections beyond the physics' interpolated half-width (A 22, B 17, C 2, E 15 section edges); tips kept to
0.05 m; 0.3 m pads past each part's end sections; on the lane, 14 pushes where his line's corners (the channels' feet)
lie between two lane stations. **Paved outside his outlines and his lane line** (the bounded deviation; 0.25 m grid
between the course edge and the lane, 0.4 m round barriers left out): **257 samples (16.1 m2), at most 1.10 m from
his outline or the lane's edge**: by x, C's west flare (x -200 .. -175) 73, C's east end (-175 .. -150) 55 + 8, A 28, B
18, E 75: the corners' chamfers, the end pads, and C's band reaching his outline's top across the flare's slanted side.

### A8. Wording

"meet with no step" (review item 3) and "a gradual change, no step" (item 1) are corrected above: the boundaries are the
millimetres in A4's table. The A / B lane-band descriptions of the first review (20 m tapers) describe rev 2503ea567c;
those bands are gone in this round (A4).

### O1. The pit lane stops at his line: dirt median, A and B as channels

`pit_lane.lane.edge_line` (`owner/r14_lane_line.json`, his lane-side green from w_s4500 / w_s4625 / w_s0000 / w_s0125,
one point a metre, with his detours down A's #12 / #11 and B's #10 / #9 flares to the wall face + 0.3 m): each lane
station whose right edge lay beyond his line moves onto it (never outward; the farthest of the station's own ray and
the rays half a station either side, then the corner pushes), **241 stations moved more than 1 cm, x -194.2 ..
68.95** (the build logs 244 points moved, 14 pushes); the centre (the AI's
pit path) does not move; the profile on the cut side is re-read on the lane's own surface. East of x 64: his line runs
on to x 216, but the lane's edge lies beyond it only to x 68.95 (5 stations x 64 .. 69, 5.3 m on average, where his
stroke closes onto the wall); from x 69 east the lane's edge is on or inside his line and the lane is kept as it was.
The median: 95c8125's lane strip outside the new one, paved there **7,652 samples (478 m2): now dirt 7,466**, still
paved 186 (the channels and mouths). The AI's path: the lane's least right half-width beside the straight is **3.31 m
at station 208 (-142.4, -216.1)** (95c8125: 3.99 m); the lane centre sampled every 0.1 station: 1 unpaved sample, as in
95c8125; pit connectivity ok (388 m out, 382 m in, 0 barrier crossings, 2 m unpaved, as before). A and B: the lane
paves each channel above the wall; the mouths pave from the course edge to his wall-top line (`mirror_wall`). C and E
join the lane as before. Ortho: differs from 95c8125 in 1,919 px (691 m2, x -296 .. 186, y -229 .. -172: the median's
tone with the lane's paving gone from it) and from rev 2503ea567c in 1,615 px in the same box. Stills:
`laneA_channel`, `laneB_channel`, `lane_median_x-100`, `lane_median_x150` (`pairs_r3_a / b.jpg`).

### O2. T5 apex: the right run moved to the dense frames' reading

`kerbs_declared` 'run right s 1304-1323': `extent = (1282.0, 1308.0)` with `extent_src` (round 13's frames t051385 /
t051485, t052286 / t052386; the line scan's raw paint 1280-1309 m; width 0.9 m, the standard block). Was 1304.6-1322.5.
Kerb traversal (Probe at line speed): **R s1282-1308: 3.17 / 3.14 / 7.97 deg** (line -1 / 0 / +1 m; +1 m lifts a wheel
385 ms, 8.1 cm). Stills `kerbT5_near`, `kerbT5_mid` (`pairs_r3_kerbs.jpg`).

### O3. The Sweeper exit kerb added

'run right s 3680-3690 (Sweeper exit)': flat red / white / blue strip, `extent = (3679.5, 3689.5)` m, width 0.4 m:
onboard 0.5 s frames 2:00-2:05.5 and 0.1 s 2:02.7-2:05.9 (t123100 far, t123300 passing the hood); the line scan's red and
blue rows on the right at 3677-3688 m of the overlay-speed map, + 1.4 m (its local offset at R 3794-3810, round 13).
Inventory row added (`observations.jsonl`, `inventory.json`: kerb rows 39). Kerb traversal **R s3679-3689: 1.42 / 1.32 /
1.40 deg**, no lift. The kerbs-on-surface gate (`kerbsOnSurface`) runs on terrain-override kerb lines only (none at
Buttonwillow, n/a); the strip's build log: max step 0.000 m, ground marks 0 off. Still `kerbSweeper_near`.

### O4. His kerb ticks (w_s0547, w_s1557)

Stations re-derived from his strokes on the capwin frames (ENU x = cx + (px - 666.5) 0.06, y = cy - (py - 666.5) 0.06,
projected onto this package's edges): **L 536-549 -> 522.7-550.6 m**, **L 1541-1574 -> 1539.7-1574.0 m** (`extent`,
`extent_src` citing the strokes' pixels). Third ticks: w_s0547's on the RIGHT edge at 583.1 m, 0.8 m from R 584-604's
start (583.9): within a metre, so the start is 583.1 (end 611.5 kept); w_s1557's at 1514.1 m on the right, on R
1495-1515's end (1514.2): no change. Kerb traversal: **L s523-551 (T2 entry): 2.86 / 2.95 / 8.27 deg** (+1 m lifts 360
ms, 7.5 cm); **L s1540-1574 (after T5): 3.15 / 3.07 / 3.08 deg**; R s583-612: 3.59 / 3.44 / 3.44 deg. Every Buttonwillow
pass: 117, worst 10.80 deg (gate 15). Stills `kerbL523_start`, `kerbL550_end`, `kerbL1540_start`, `kerbL1574_end`.

### Gates and identity (rev 29f4afedba)

Stage 3 `--publish --overwrite-package` exit 0, 0 `[FAIL]`; build == package (every file); gate CLI on the package
every gate ok, exit 0 (containment 0 escapes, 3,295 allowed; pit connectivity 388 / 382 m; cones off the surface 168 /
36; ground marks 0 off; paved coverage as A1 / A5 / A7). track.json, heightfield.bin, ghosts.json, far_heightfield.bin,
far_ortho.jpg identical to 95c8125; ortho.jpg as O1; Sonoma identical. TRACKS.buttonwillow rev 29f4afedba. Tests: `npm run
build` clean; vitest 65 files **541 passed**; pytest **136 passed, 3 skipped** (131 + 5).
