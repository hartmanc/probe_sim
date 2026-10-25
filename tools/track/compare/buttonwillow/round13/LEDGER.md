# Buttonwillow round 13: ledger (25 Oct 2026)

The owner's decisions of 25 Oct 2026, scenery and look only. Branch `buttonwillow-r13` (from `integration` 893c961);
nothing pushed or deployed. Build: the round-12 records (`probe_sim-wt/buttonwillow-r12/tools/track/out/buttonwillow_r12/`)
cloned to `tools/track/out/buttonwillow_r13/` and the round-12 caches / capture folders cloned (APFS `cp -c`, read only on
the source). Stage 3 only, four check builds and one `--publish --overwrite-package`, every one exit 0 with 0 `[FAIL]`
(logs `/tmp/bw13/logs/stage3*.log`). Package `public/tracks/buttonwillow`: rev **52bf051dcc -> 8d02b04cb4 -> 795c09c6cb** (the second after the review fix below).

Machine: the first half ran on battery (light work only); builds, tests and renders ran after the owner's word relayed
by the coordinator ("Don't wait on power, just go"), one heavy process at a time, battery never under 82 %.

## 1. Cone lines where the onboard shows no cones: removed

Evidence: onboard 7QS2M-HGSI4 captured every 0.5 s over the whole lap (`/tmp/bw13/frames`, 318 frames, headless capture,
reference only). Each owner mouth entry set `cones=False` with a `cones_src` naming its frames; his red stays the course
boundary (stage 1 untouched).

| mouth (package s) | config entry (stations_ref) | frames | onboard |
|---|---|---|---|
| L 207-213 | left 206-213 | t009500-t012000 | K-rail ends on the left at 0:10.0, open dirt, no cones (the cones in view are the Atlantic row, right) |
| L 4484-4534 | left 4475-4528 | t000 (owner) and t145500-t148500 | wide pale paving to the white / red K-rail, no cone on it or across it |
| R 2533-2561 (drag strip) | right 2524-2551 | t086000-t090000 | the strip's paving joins with no cones (the one cone, t087500, is on the left) |
| R 2973-3015 (drag strip / Lost Hill) | right 2963-3006 | t099000-t103000 | no line across the mouth; single cones on the right paving at t100000 / t100500 and far ahead at t103000 |
| R 4162-4174 (Zorros fillet) | right 4152-4165 | t134500-t138500 | pale fillet at t136500-t137500, no cones |
| R 3663-3683 (Sweeper mouth, re-checked) | right 3653-3673 | t119500-t123500 | no line across the Sweeper's mouth (its paving and dashed white line at t121000-t121500); single cones at the right edge at t120500 and t122500-t123000 are the declared row's cones |

The declared row R 3645-3655 ("onboard t122") stays: the footage shows cones on the right there. Cone lines 44 -> 38,
cones 264 -> 182.

**Inventory:** no inventory row describes any of these six lines (they came from the owner's round-10 red, not from the
inventory); the rows at those stations are the K-rail (t000, s 4502) and pit-scope rows, unchanged. Nothing to correct.

**Containment** stays ok with 0 escapes; rays onto allowed runoff 3166 -> 3296: the opened mouths now let rays reach the
closed roads behind them, which existing `gates.allowed` entries already cover (drag strip, Zorros, Sweeper, with their
evidence). No allowed entry was added or widened.

## 2. Kerb extents of the 37 other runs: measured

**Method.** Frames every 0.5 s over the lap plus every 0.1 s round each run end (`/tmp/bw13/frames_fine`, 728 frames;
times from the frames' presented media time). Station of a frame: the Catalyst overlay speed read on every frame (digit
templates; checked on 66 frames read by eye, 0 wrong), integrated and scaled to the lap (5.47 s -> 0, 152.95 s -> L;
K 1.0097); it agrees with the inventory's GPS anchors within +-17 m. Station of an image row: u = s(t) + Z, Z level pinhole
(H 1.08 m as round 11; f 1010 px from the 1 m kerb blocks, colour transitions on t146.0 / t146.5). A line scan (rows Z
4.8-12 m, red / white / blue paint 0.8-14 m to that side) gives each run's painted interval; every end that moved was then
read by eye on its own frames (`/tmp/bw13/sheets/e*.jpg`). The speed map's local offset against the captures was taken
as the median of the confirmed ends within 300 m (0-3 m) and added to each onboard reading. Rule: an end moves when the
corrected reading differs from the capture end by more than 5 m; otherwise it is confirmed. Precision about +-3 m.

| run | old extent (package s) | measured | new extent | frames |
|---|---|---|---|---|
| L 1449-1479 | 1454.3-1478.2 | start 1429.8 (+2.8) | **1432.5**-1478.2 | t056189 / t056290 |
| L 1653-1680 | 1650.9-1677.9 | start 1643.4 (+1.4) | **1645.0**-1677.9 | t062095 / t062195 |
| L 1843-1851 | 1842.5-1851.5 | start 1831.5 (+0.5) | **1832.0**-1851.5 | t067668 / t067868 |
| L 2539-2544 | 2536.2-2541.2 | start 2522.7 (+0.8) | **2523.5**-2541.2 | t086887 / t086987 |
| L 2689-2746 | 2686.0-2743.9 | start 2672.5 (+1.0) | **2673.5**-2743.9 | t090791 / t090891 (end kept: the run leaves the frame side, t092693 / t092793) |
| L 3845-3876 | 3840.8-3870.7 | start 3827.3 (+2.4) | **3829.5**-3870.7 | t127294 / t127394 |
| R 188-268 | 188.6-268.5 | start 182.1 (-1.9) | **180.0**-268.5 | t009877 / t009977 |
| R 360-376 | 361.3-376.3 | paint unbroken to the next run | 361.3-**411.0** | t016683 / t016783 / t017784 / t017885 |
| R 584-604 | 583.9-603.9 | end 611.4 (+0.0) | 583.9-**611.5** | t025692 / t025893 |
| R 1020-1049 | 1020.1-1049.0 | start 1013.1 (+2.0) | **1015.0**-1049.0 | t040173 / t040374 (a 5.1 m move against the 5 m deadband and +-3 m precision: marginal) |
| R 1868-1933 | 1867.5-1932.4 | end 1956.0 (+0.5) | 1867.5-**1956.5** | t071171 / t071371 / t071772 / t071872 |
| R 2315-2340 | 2313.7-2338.6 | start 2306.7 (-1.1) | **2305.5**-2338.6 | t081281 / t081381 |
| R 3794-3810 | 3789.9-3805.9 | start 3769.9 (+1.4); end 3799.9 (+1.4, within 5 m: kept) | **3771.5**-3805.9 | t125692 / t125792 / t126493 / t126593 |
| R 3894-3935 | 3889.7-3929.6 | start 3878.7 (+2.4) | **3881.0**-3929.6 | t128595 / t128695 |

Confirmed within 5 m (unchanged), with the line scan's reading: L 283-322 (286.0-325.5), L 745-767 (740.6-766.6),
L 954-1011 (949.5 by eye, the scan's 947 was a cone; 1010.2), L 1089-1116 (1090.0-1118.5), L 1203-1272 (1200.7-1270.7),
L 1338-1396 (1334.0-1394.0), L 3005-3013 (3002.4-3013.4), L 3340-3383 (3331.7-3381.2), L 3470-3518 (3467.5-3517.5),
L 3691-3760 (3691.1-3755.6), L 3972-4024 (3962.6-4012.6), L 4381-4406 (4373.3-4403.3), R 410-424 (end 425.2), R 1168-1191
(1165.3-1185.8), R 1495-1515 (1490.7-1509.7), R 1779-1818 (start 1775 by eye: faded white blocks; 1818.7), R 2765-2792
(2758.8-2789.3), R 3400-3451 (start: the scan's 3383 is white runoff lines, t111278; 3445.1), R 4030-4127 (the middle is
faded white blocks, t133467; end 4114 + 3.2 = 4117, within 5 m), R 4321-4370 (start 4308 + 2.5 = 4310.5, within 5 m;
4359.9), R 4424-4501 (4415.2-4495.2).

**Not resolved, left as they were:** L 536-549 (T2 hairpin entry: the onboard reads 525.5-552.5, both ends 6-10 m early,
but in the hairpin the rows' forward distance is not distance along the track); L 1541-1574 (in the near rows the kerb
lies beyond the frame's left side; far rows suggest it runs on to ~1595, not precise enough to set).

Builder key `kerbs_declared[].extent` (metres of this package, flush runs only, with `extent_src`; tests
`tools/track/test_round13_scenery.py`). The L 1449-1479 start was dropped in round 8 because the edge stepped out there;
the round-10 edges have no step (half-width 5.4-5.9 m smooth over 1420-1462). Kerb strips 1621 m in all; kerb run step
ok, kerb traversal (vitest) ok.

**Finding for the owner (not changed, outside the 37):** by the same method the T5 apex run (round 11, R 1304.6-1322.5)
reads 1282-1308 on the onboard (t051385 / t051485, t052286 / t052386), about 20 m earlier than placed.
Also seen: a short white / red kerb on the right at the Sweeper mouth's exit (t122500-t123500, near the detected band
3672-3678 of stations_ref that round 10 left unplaced); and the single cones at t100000 / t100500 (drag strip) are not
placed.

## 3. Tyre walls drawn as used tyres (every track)

`src/app/scenery.ts` (`TYRE_LOOK`, `tyreStackGeometry`, `tyreCasing`): each tyre a flat tread band between rounded
shoulders and a deep groove (3 profile points per tyre, 7 lathe segments), per-tyre shade (levels 0.86-1.10) and a wear
patch round each tyre (+-16 %), each stack turned by its own angle and its shade varied +-10 %; a rough standard material
(roughness 0.88) so the casings take the sky light; flat-black recorded colours lifted 70 % toward the used-rubber grey
#3b3c3d (Sonoma's #161616), lighter ones kept. The free-standing tyre stacks (landmarks) get the same casing colour,
gain and material, not the tread profile (they stay plain cylinders). Rendering only: no collision change. Height unchanged (T2
wall 1.0 m). The renderer gain (2.0) was set from the stills: the T2 wall's lit faces from 9 m (p75 of the dark pixels)
before (33, 37, 33) -> after (57, 62, 58), against the onboard t288 sunlit median #3c443e (60, 68, 62); median before
(4, 8, 10). Tests: `src/app/__tests__/tyre-look.test.ts`.

Draw cost (pose_walk, whole scene): Buttonwillow 1,786,680 -> 1,842,046 triangles (+3.1 %, including this round's new
paving and kerbs), Sonoma 2,558,619 -> 2,749,903 (+7.5 %); draw calls per pose unchanged (one instanced mesh per stack
height, e.g. son_T7_approach 211 / 211, fwd_s0590 219 / 219); render time within the noise (5.9-15 ms either way).

## 4. Paddock paving extended from further captures

Three new z20 captures (`satellite_paddock13/pad13_w / pad13_c / pad13_e / pad13_ww`, headless maps, 25 Oct 2026) fill
the y -165 .. -140 m gap between the c20_p* and pad_* sets. Measured on the mosaic (0.12 m/px, 1.2 m patches every 0.5 m,
paving = saturation < 0.14), north of the paddock-side K-rail every 5 m and along rows y -150 .. -180: the block round the
timing tower is paved from the K-rail to the paddock road (x -32 .. 57 m; dirt and trees west of x -33 and east of x 57
north of the strips); east of the round-12 strip the paving runs on to x ~156 m at 21 m (21.5 at x 110-135, 20-20.5 at
140-150, 21 at 155).

**Review fix (GPT 6 Astra, "ship with fixes"): the drawn paving and the physics must agree.** The physics gives a point
to the paved part whose centre line is nearest (the pit lane and the zones are one list), so the first build's
overlapping bands, ending inside one another's drawing, left seams under continuous drawn paving (the full scan of the
drawn bands: 2,878 unpaved samples at 0.25 m; round 12's own strips had 245). The paddock paving is now seven declared
bands laid out for that rule, each point with its own half-width (builder key `closed_roads[].ways[].halves`; points used
as declared, one per metre on common normals of the K-rail, end segments parallel to it so the bands end on one normal):
- **I** x -124 .. 154: centre and half-width = the lane centre's perpendicular distance D (6.5-8.9 m), so the lane / paddock
  boundary lies on the K-rail line everywhere; `join_lane` in the openings.
- **T** same x: up to the strip top (21 m west of x -32, ramped to 22 m by x -24, 22 m to x 98, 21 m east of x 102); over
  the block from the I / T bisector, its top 22 m = the T / B2 bisector.
- **B2-B5, U** x -22 .. 57 (the tower block): centres equally spaced from 44 - c_T to U's, U's centre 6.75 m south of the
  paddock road's centre (the road keeps its southern edge) and its top 3.1 m south of it (short of the north-south lane
  that starts on the road at x 11); each layer reaches its bisectors with 0.3 m overlap, tapered to 0 over the last 3 m
  where the layers end (so no drawn point beyond an end is nearer that end than its own band).
- The OSM paddock lane 765811053 along the east K-rail run (x 52 .. 165, 5-13 m north of it) is dropped: it lay wholly
  inside the strip and its own centre line punched seams round its ends.

**Postcondition:** stage-3 gate `paved coverage` (`tools/track/gates/pavedCoverage.ts`, config
`gates.paved_coverage {parts ^paddock band, step 0.25, wall_clear 0.4, edge_tol 0.1}`, strict): every sample of the bands'
drawn strips on a 0.25 m grid, 0.4 m round the barriers and 0.1 m along the drawn edges left out (the strip edges are
chords at 0.01 m, the physics interpolates the half-width per segment; bands meet on their bisectors), must be paved.
Published package: **129,608 samples, 0 unpaved** (5,059 edge samples left out). vitest
`src/scoreboard/__tests__/pavedcoverage.test.ts`: the published bands pass; a narrow part inserted inside band T makes the
gate find a seam (220 holes at 0.5 m, all within 8 m of it). The build with the first fixes failed on this gate (63, then
41, 7, 3 unpaved) before the layout above passed.

**Undrawn (dirt in the sim) though paved on the captures, said so:** x -163 .. -140 (an 8 m strip: a band that narrow would
take the lane's last metres), x -130 .. -124 between the north-south paddock lane and the bands (that lane's centre is
nearer there), the road-side apron west of x -33, the block above T at x -32 .. -22 and x 57 .. 65 (where the layers end).
The OSM paddock lanes (round 8) keep junction seams elsewhere in the paddock (scan at 0.5 m: 283 unpaved in round 12,
187 now, including 10 new ones where the road meets U's ends at x -28 and 56); not in this gate's scope.

**Proof, the lane beside the K-rail (point by point, the same 27,018 sample points: x -165 .. 190 every 0.5 m, 0.4-8.0 m
south of the K-rail line every 0.2 m, round 12 rev 52bf051dcc against 795c09c6cb):** 26,622 samples are lane in both with
the same height (max |dz| 0.000000 m) and the same grip / course flags; 205 differ, all toward the lane: 141 that round
12's bands took from the lane 0.4-1.2 m from the wall (paved apron, off-course; x -130 .. -100 and x 30 .. 50) are lane
again, 63 unpaved in round 12 (0.4-1.4 m from the tower run, x 20 .. 50) are lane now, and 1 unpaved sample in both
changes its shoulder height (x -127.5, 0.094 m). No sample went from paved to unpaved. (The first round-13 package,
8d02b04cb4, was not unchanged, as its aggregate counts suggested: against round 12 it had 6 lane samples paved -> unpaved
and 56 still off-course.)

## Gates (stage-3 build and the gate CLI on public/tracks/buttonwillow, every one ok)

| gate | round 12 (52bf051dcc) | round 13 (795c09c6cb) |
|---|---|---|
| edge (rms / step), world continuity, profile | ok 0.066 / 0.066; 0.0076 / 0.0073; 0.017 | ok, same |
| owner reference / width / band | ok 0.381 / 0.328; 0.384; 0.136 / 0.120 | ok, same |
| barrier gaps | ok, 4.17 m / 17 runs | ok, same |
| containment | ok, 0 escapes, 3166 allowed, 78 junction | ok, 0 escapes, 3296 allowed, 78 junction |
| pit connectivity | ok 388 / 382 m | ok, same |
| signs, wall ends, tyre facings, wall tops, wall-tyre joins, tyre faces | ok | ok, same |
| run gaps | ok, 2 openings | ok, 2 openings, 0 holes |
| terrain override | n/a | n/a |
| ground marks on surface | ok, 0 off | ok, 0 off (3610 paint, 15220 edge-line vertices) |
| cones off the surface | ok, 264 / 44 | ok, 182 / 38, deepest 0.00 m |
| coverage | ok, MISSING 0, UNSUPPORTED 0, 5 dispositions | ok, same (87 rows, 161 objects) |
| pit lane | ok, 7 rows | ok, 7 rows |
| paved coverage (new) | (2,878 unpaved on the first round-13 bands) | ok, 7 parts, 129,608 samples, 0 unpaved |

Tests (re-verified on 795c09c6cb): `npm run build` clean; `npx vitest run` 65 files, **524 passed** (515 + 7 tyre-look
+ 2 paved-coverage), 0 failed; `pytest tools/track` **96 passed, 3 skipped** (91 + 5 round-13). Gate CLI on
`public/tracks/buttonwillow` with the publish run's gates_config.json: every gate ok, exit 0.

## Identity

`git diff --quiet 893c961`: public/tracks/buttonwillow track.json, heightfield.bin, ghosts.json, ortho.jpg,
far_heightfield.bin, far_ortho.jpg byte-identical (sha256 track.json 199358fe..., heightfield.bin 2c677efb..., ghosts.json
e66b3218...); scenery.json is the only changed file (rev 795c09c6cb). public/tracks/sonoma byte-identical, rev f399cda140.
`src/scoreboard/config.ts` TRACKS.buttonwillow rev -> 795c09c6cb. PHYSICS_VERSION and changelog untouched.

## Stills (local only, `round13/stills/`; pose_walk --port 5213; `_before` = rev 52bf051dcc with the old scenery.ts)

- `pairs_cones.jpg`: the six mouths (cone_L4484, R2533, R2973, R4162, L207, R3663).
- `pairs_kerbs.jpg`: the runs that moved most (L1432, R1956, R3771, L2523, R0376, L3829).
- `pairs_tyres_t2.jpg`: T2 wall from the hood at s 590 / 600 (the owner's distance), mid and 9 m close.
- `pairs_tyres_sonoma.jpg`: Sonoma T7 approach and close, the s 2347 bundle far and close.
- `pairs_paddock.jpg`: tower from the lane, both openings, the east strip, the tower block.

## Open

1. T5 apex run reads ~20 m earlier on the onboard than placed (above); the Sweeper-exit right kerb and the drag-strip
   single cones (above).
2. L 536-549 and L 1541-1574 extents not resolved by the frames.
3. Paddock: the undrawn spots listed above, the OSM paddock lanes' own junction seams, the x 57-75 width (above).
4. Carried: the hood camera (unchanged by the owner's decision).
