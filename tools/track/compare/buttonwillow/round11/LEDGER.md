# Buttonwillow round 11: ledger (23 Oct 2026)

Round 11 carries out the real findings of the judge round over round 10 (`judge_r10.md`), the owner's answers of 23 Oct
2026 relayed by the orchestrator during the round, and four tool fixes. It stops before the preview and the judge.

Build: `tools/track/out/bw_r11` (stages 1, 2 and 3; published with `--publish --overwrite-package`). Package
`public/tracks/buttonwillow`: rev **7acf260f50 -> 69e80ace38**, lap 4699.187 m (unchanged). Logs in the round's scratch
(`/tmp/bw11/stage1.log`, `stage2.log`, `stage3.log`, `stage3_pub.log`).

## The owner's words (23 Oct 2026, relayed by the orchestrator) and what each became

| topic | his words | what it became |
|---|---|---|
| kerbs | "Use the onboard. I didn't intend to make any statement on kerbs when fitting the lines." The new zone L 2853-2859: "Sure" (drop it). | Kerb width, extent and colour from the onboard (item 2). R 1304.6-1309.5 extended to what the onboard shows; L 2849-2855 dropped. |
| crossover mouth 1800 R | "Only one row: do whatever matches onboard video." | One row: the declared onboard row (t066-t068); his mouth line's cones off (item 1b). |
| Pacific 4575 / 4593 | "I made no statement on cone placement or quantity when I fitted the lines. Do whatever matches onboard video." | The two declared single cones; his mouth line's cones off (item 1b). |
| all mouth lines | his line defines the course boundary at a mouth; the cones' placement and count follow the onboard where it shows them | Applied where an onboard row overlaps a mouth line: 1800 R, Pacific, and the connector mouth R 30-40 (onboard t006). The others are listed under "Open". |
| crack seal | "Redraw" | Item 6: same measured marks, drawn thin on their measured wavy lines, glossy near-black; the pit-entry centreline marks dropped. A procedural seal network is GitHub issue #10 (future). |

## Stage 1: no refit

Stage 1 reproduces round 10 byte for byte: `out/bw_r11/track.json` and `heightfield.bin` are `cmp`-identical to the
round-10 package (0 `[FAIL]` lines; every owner-reference gate as round 10: owner reference left max 0.381 at 1859, right
0.328 at 4393; width consistency 0.384 at 549; edge waviness 0.136 / 0.120). Stage 2: `ghosts.json` identical. The
stage-1 kerb zone of L 2837-2843 (stations_ref) stays in `OWNER_KERBS_R10`: the accepted edges do not move; only the
stage-3 strip over it is dropped.

## Items

### 1. Cones on the racing surface; the "cones off the surface" gate

- **Gate** (`gates/sceneryGates.ts` `conesOffSurface`, `coneSpots`; `run_gates.ts`; REQUIRED in every stage 3 through
  `build_track.scenery_gates`): every cone of every line, its spots placed exactly as the app places them
  (`buildPitExitCones`: one per `spacing_m`, the remainder carried over vertices), fails when it stands inside the
  course polygon (the track's station quads) more than 0.15 m from the nearer edge polyline. Not gated (counted
  `onLane`): a pit lane's separation line where the lane and the track share the pavement (SKILL 3.5): the
  `pit_exit_cones` line, any cone within 0.5 m of the pit-lane paving, and lines a track's gate config names in
  `scenery.gates.cones_exempt` with the reason. Sonoma declares one (its pit-in double white line, owner notes 15-16);
  Laguna's only line is its pit-exit blend line. Tests: `scenerygates.test.ts` (spot placement; on / beyond the edge
  passes, a 0.5 m bulge fails at those cones, 0.1 m inside passes; the three pit exemptions).
- **Builder** (`build_scenery.owner_mouth_cones`, config `owner_mouth_cones.clip_out = 0.1`): where his red lies less than
  0.1 m outside the fitted edge, its points move out along the station normal to 0.1 m beyond the edge (0.1 m so the
  containment rays, which start 0.05 m beyond the edge, still meet the line); elsewhere the line keeps its shape.
  Log per line: Atlantic R 154-186 deepest 1.25 m inside before; 1960-1993 L 0.24; 2524-2551 R 0.27; the rest <= 0.14.

| gate "cones off the surface" | round 10 package | round 11 package |
|---|---|---|
| Buttonwillow | **FAIL**: 305 cones / 47 lines, 20 cones more than 0.15 m inside (deepest 1.24 m: line 9 Atlantic 168.7-186.7 R; line 5 1996-1999 L 0.17-0.22; line 11 1819.6 / 1820.6 R 0.74; line 12 2538 R 0.20) | **ok**: 264 cones / 44 lines, 0 inside (deepest 0.00 m) |
| Sonoma (published package, its gate config) | ok: 54 cones / 9 lines, deepest 0.02 m, 20 on a pit separation line | (unchanged package) |
| Laguna (published package) | ok: 19 cones / 1 line (pit exit), 15 on the pit separation line | (unchanged package) |

All 19 owner lines and the 28 declared lines were checked by the same gate (table row 1). The declared lines were all
off the surface already.

### 1b. Mouth cones per the onboard (the owner's answers)

`owner_mouths_r10` entries set `cones=False` with `cones_src` (his line remains the course boundary; stage 1 reads
`owner/r10/mouths.json`, untouched):
- **R 1811-1835 (crossover)**: onboard 7QS2M-HGSI4 1:07.0 / 1:07.5 (frames captured at 0.5 s, reference only,
  `/tmp/bw11/dl_onboard/t067000.jpg`, `t067500.jpg`): one cone at the kerb's end, then ONE row of cones ~6 m apart on the
  crossover paving a few metres off the edge = the declared row "onboard t066-t068" (6 m, 3.0 m out), kept. No cones on
  the edge line.
- **R 4571-4599 (Pacific)**: onboard 2:29.0-2:30.5 (`t149000`-`t150500`): single orange cones at the edge of the pale
  paved area, one in view at a time, no row: the declared singles (s 4575, onboard t002; s 4593, onboard t150) kept.
- **R 30-40 (connector, OSM 34351026)**: onboard t006: four cones (yellow, orange, orange) on the connector's paving
  3.8 m out = the declared row (s 40-55), none on the edge line.
Containment still passes (0 escapes; 3166 rays onto allowed runoff against 3493: the clipped lines stand 0.1 m out).

### 2. Kerbs from the onboard (width, extent, colour)

**Measurement.** `compare/kerb_onboard_width.py` (new): the kerb's width across it on the ground from an onboard frame,
level pinhole at the camera height H (HEIGHTS.md), per row of the nearest 40 % of the rows, the longest run of paint, the
run's direction from its centre X(Z), p80 over the rows; VALID only when the kerb runs within 25 deg of the view, the rows
agree (p50 / p80 >= 0.75), 8+ near rows spanning 40+ px down to row 440, the run not cut by the frame side. **H = 1.08 m**:
the pit-wall Jersey reference of the inventory (1.05 m, t004) and the 240SX ahead at s 4500 (1.12 m: 1.69 m wide, 145 px at
its tyre row 378, horizon 282). The config's older 1.49 m (from the CRX roof on t116) disagrees with both and was not used.
All 37 inventory kerb frames were read; 14 are valid. Uncertainty about +-0.15 m (H, partial detection).

| run | width before (m, source) | onboard frame (p80) | width after |
|---|---|---|---|
| L 283-322 | 0.5 (capture band) | t014 0.97 | 0.95 |
| L 1203-1272 | 0.75 | t050 0.73 | 0.75 |
| L 1338-1396 | 0.9 (standard) | t054 0.69 | 0.70 |
| L 1843-1851 | 1.1 | t068 0.66 | 0.65 |
| L 2689-2746 | 1.1 | t092 0.53 | 0.55 |
| L 3845-3876 | 0.75 | t128 0.97 | 0.95 |
| L 3972-4024 | 0.9 | t132 0.99 | 1.00 |
| R 188-268 | 1.3 | t010 0.87 | 0.85 |
| R 360-376 | 1.1 | t018 0.70 | 0.70 |
| R 410-424 | 0.9 | t018 0.70 | 0.70 |
| R 1495-1515 | 0.9 | t058 0.42 | 0.40 |
| R 2315-2340 | 1.1 | t082 0.49 | 0.50 |
| R 2765-2792 | 0.9 | t094 0.86 | 0.85 |
| R 3794-3810 | 1.1 | t126 0.69 | 0.70 |
| R 4424-4501 | 0.9 | t146 0.93 | 0.95 |

The other 23 runs keep their width: their frame is not a valid reading (kerb across the view or cut by the frame:
t012, t022, t032, t038, t040, t044, t048, t052, t060, t062, t066, t070, t110, t112, t114, t116, t124, t130, t134, t136,
t140, t142, t144) or they have none. Each changed run carries `width_src` naming its frame.

**Extent.** R 1304.6-1309.5 -> **1304.6-1323.5** (`zone=(1294, 1313)`, `extent_src`): onboard 0:51.5-0:52.6 at 0.5 s
(`t051500`-`t052500`): the whole run in view at 0:51.5, 16-18 blocks of ~1.05 m; its far end passes the hood at
0:52.5-0:52.6; measured **19 +- 3 m**, not the ~30 m read by eye in the judge round. L 2849-2855 **dropped** (the owner,
"Sure"; no kerb on t096 / s2850). The other runs' extents stay those of their capture block lines, each confirmed on
its colour frame (the 2 s frames cannot place a run's ends to better than ~30 m; listed under Open).

**Colour.** The paint as the onboard shows it at close range (kerb_onboard_width over the valid frames): red
#a0596b-#b76372, blue #2f73ab-#4983b1, white #b7beca-#c4c3ca (sun, haze). The sim's kerb as rendered at s 1100 (the
judge's good match): red #c1746c against the onboard's #b46d5f, white #cbc7c6 against #d1c3b0. The palettes already
render as the onboard's paint; they are unchanged. Each run's pattern (rwb / rw / wb) was already read from its frame.

**Why the kerbs still vanish from the hood (finding for the orchestrator).** The onboard kerbs are 0.4-1.0 m wide
(median 0.7 m), no wider than the sim's. They read large on the onboard because its camera sits at the front of the hood:
the road shows from ~2 m ahead, the horizon at row ~270 of 720. The sim's `hood` camera (HFOV 95 deg) sits behind the
car's long hood and the two figures: the road shows only from ~5-6 m ahead, the horizon at row ~395, and a kerb 10-40 m
ahead covers a few pixel rows (`round11/stills/diag_pitch.jpg`: pitching the camera down only shows more hood). That is
a camera placement in the app, not package data; it is not changed here.

Kerb gates: kerb run step 0.000 m on all 38 runs; kerb traversal (vitest) ok on the three tracks, Buttonwillow 114 passes
(117 before: one strip fewer), 56 with a wheel lift (61), advisory; the worst L 1203-1273 off -1: roll 10.8 deg (< 15).

### 3. T2 outside tyre wall (barrier 15)

It exists: the capture's dark band (`stage3_evidence/t2tyres_r8.png` on c20_s0700 / c20_s0750) and the CCW onboard t286 /
t288 (a row of tyres in front of the dirt berm). Its colour on t288 in the sun: median **#3c443e** (darker 60 %
#2e362f), not #202020: colour set to #3e443f. The height stays 1.0 m (no reference object in the frame to measure it);
the renderer draws it as stacked tyres already. Not removed. From the hood at s 600 it still reads as a dark band at
30-40 m (`pairs_scenery.jpg` row 1); the onboard at s 600 shows it as a thin grey line on the horizon. Open.

### 4. Scenery look items carried from round 8

- **Lattice mast at s 3445 L.** The "solid green column" was a TREE: the lidar crown rule made a 49.8 m crown of 3.6 m
  radius 2.8 m from the mast (the lattice's returns are multi-return like a crown). New config-gated rule
  `scenery.tree_mast_clear` (radius 6 m from a declared light mast): that crown dropped (log), trees 231 -> 230. The
  lattice renders as the thin grey lattice of round 6 (`pairs_scenery.jpg` back_s3500, fwd_s3250).
- **Control tower massing.** Pit video t1312000 (21:52) / t1339000: the upper level is an open deck under the blue roof,
  posts and a railing at its lane edge, the glazed room set back against the tower's back. The upper storey went from
  11 x 8 m (filling the deck) to 9 x 5.5 m against the tower's paddock face (~4 m open deck on the lane side, ~2.5 m at
  each end). The west shade roof and the awning are unchanged (both in the video); the elongated read from the lane is
  partly them. `pairs_scenery.jpg` pit_p0_013 / 014.
- **Station tyre rings** (pale #d2cab8 where the capture shows a dark ring), colours from the onboard surround faces:
  T3 #605d61 (t040: #5d5858 / #626168), T6 #80736f (t074), T11 approach #786255 (t138), T5 #6f6662 (no frame shows its
  face: the median of the three, with the capture's dark ring c20_s1600). The six "pale surround" rings (826, 1185,
  2370, 3433, 3716, T1 exit), whose own frames show a pale surround, are unchanged. `pairs_stations.jpg`.

### 5. Tool fixes (their own commits)

| commit | fix | check |
|---|---|---|
| b64aaa1 | `boundary_sheets.py`: unique pose names; the parts of one road get -p00, -p01, ... (as the round-10 reshoot); asserted | the round-10 package: 969 poses, 969 unique names (round 10: 214 overwritten); `test_boundary_sheets.py` |
| 7e5fa02 | `pose_walk.ts`: `--port` and `--out` required, flags documented in the header, the server checked before Chrome | used for every still of this round (port 5193, out `/tmp/bw11/stills`) |
| d7fd2a6 | `runoffPoses`: the car at the polygon's far side looking back across its paving (5 m beyond a polygon shallower than 30 m, 25 m into a deeper one) | `poses.test.ts` (new framing + deep-polygon case); a fresh runoff walk is the orchestrator's next judge round |

### 6. Crack seal redraw (the owner: "Redraw")

`build_scenery.surface_marks` (config-gated keys `polyline`, `step`, `width`, `color`, `gloss`, `drop`), app
`buildPaintLines` (optional per-line `gloss`: a lit standard material, roughness 1 - 0.8 gloss; lines without it draw
as before):
- the same 579 candidates / measured marks; each now on its own measured line (its pixels binned every 0.4 m along the
  principal axis, the median offset across per bin, median-of-3 smoothed): median 12 points per mark;
- 0.05 m wide (0.1), #151515 with gloss 0.5 (flat #2a2a2a); flat on the surface 0.008 m up as before;
- **dropped (7)**, the lengthwise marks on the pit-entry straight s 4275-4328 (within 30 deg of the track): s 4285
  (lateral -0.0 m, 14.5 m long), 4296 (-0.3, 6.3 m), 4309 (-0.6, 13.1 m), 4326 (-0.3, 4.7 m) on the centre; 4303 (-3.5,
  4.2 m), 4315 (-5.4, 4.2 m), 4324 (-5.3, 3.4 m): from the hood they line up as a dashed centre line the onboard
  (fwd_14 s4250-4350) does not show;
- paint lines 257 -> 250. `pairs_seal.jpg` (hood 850, 1600, 1650, 4300; back 2600): the straight black bars are now thin
  wavy lines, the pit-entry centre line is gone.
A procedural seal network (coverage) is GitHub issue #10 (future).

## Gates, before (round 10, e1dba23) and after (round 11)

| gate | round 10 | round 11 |
|---|---|---|
| stage 1 (all, incl. owner reference, width, waviness) | ok | ok, track.json / heightfield.bin byte-identical |
| stage 2 | ok | ok, ghosts.json identical |
| edge (with walls), world continuity, profile | ok (0.066 / 0.066 rms; 0.0076 / 0.0073; 0.017) | ok, same numbers |
| barrier gaps | ok, min 4.17 m / 17 runs | ok, min 4.17 m / 17 runs |
| containment | ok, 0 escapes, 3493 allowed, 78 junction hits | ok, 0 escapes, 3166 allowed, 78 junction hits |
| pit connectivity | ok, 388 / 382 m, lane 0 obstacles | ok, 388 / 382 m, lane 0 obstacles |
| signs / wall ends / tyre facings | ok 16 / 1 of 1 / 0 | ok 16 / 1 of 1 / 0 |
| **cones off the surface (new)** | **FAIL** (20 cones, deepest 1.24 m) | **ok** (0) |
| coverage | ok, MISSING 0, UNSUPPORTED 0, 5 dispositions | ok, MISSING 0, UNSUPPORTED 0, 5 dispositions (167 objects) |
| pit lane | ok, 7 rows | ok, 7 rows |
| kerb run step | 0.000 m | 0.000 m (38 runs) |
| kerb traversal (vitest) | ok, 117 Buttonwillow passes, 61 lifts | ok, 114 passes, 56 lifts |
| `npx vitest run` | - | 53 files, 413 tests passed (4 new) |
| Python tests | - | 53 passed, 3 skipped (1 new) |

Sonoma: a full rebuild (stages 1-3) into `out/sonoma_r11chk` with this round's builder exits 0 with every stage-3 gate ok (cones off the surface: 54 cones, deepest 0.02 m, 20 on its pit separation lines), and track.json, heightfield.bin, ghosts.json, scenery.json, far_heightfield.bin, far_ortho.jpg and ortho.jpg are byte-identical to `public/tracks/sonoma`: no builder change leaks. Laguna was not rebuilt (its config is untouched; every new builder key is config-gated). `npx tsc --noEmit -p tsconfig.build.json` passes.

## The package against round 10

| object | change |
|---|---|
| track.json, heightfield.bin, ghosts.json, ortho.jpg, far_* | unchanged (byte-identical) |
| kerbs | 39 -> 38 (L 2849-2855 dropped); 15 widths from the onboard; R 1304.6-1309.5 -> 1304.6-1323.5 |
| cone lines | 47 -> 44 (owner mouth lines R 30-40, R 1811-1835, R 4571-4599 off); 16 owner lines clipped to >= 0.1 m beyond the edge |
| paint lines | 257 -> 250, crack seal redrawn (item 6) |
| barriers | colours: T2 outside tyre wall #3e443f; T3 / T5 / T6 / T11-approach station rings from the onboard |
| structures | timing tower upper storey 11 x 8 -> 9 x 5.5 m, set back |
| trees | 231 -> 230 (the crown on the lattice mast) |

`src/scoreboard/config.ts`: Buttonwillow `rev` 7acf260f50 -> **69e80ace38** (the registry test's fingerprint), `length_m`
unchanged. `PHYSICS_VERSION` and `src/app/changelog.ts` untouched (one version per publish; the preview is the
orchestrator's).

## Stills (local, `round11/stills/`; `pose_walk.ts`, the round-10 walk's poses, hood camera, `_before` = round 10)

- `pairs_kerbs_a.jpg` (hood 550, 1000, 1100, 1450), `pairs_kerbs_b.jpg` (hood 1750, 1850, 2750; row 1304 R: the T5
  run extended; row 2857 L: the dropped strip), `diag_pitch.jpg` (the hood camera finding).
- `pairs_cones.jpg` (row 186 R and back 200: the Atlantic cones off the asphalt; rows 1793 / 1824 R: one row; rows 4573
  / 4593 R: the Pacific singles; row 47 R: the connector's four cones).
- `pairs_scenery.jpg` (hood 600: T2 tyre wall; hood 3250, back 3500: the mast; pit 4643 / 4668: the tower).
- `pairs_stations.jpg` (rows 996 R, 1492 R, 2053 R, 4273 L; back 4300).
- `pairs_seal.jpg` (hood 850, 1600, 1650, 4300; back 2600).

## Not changed: for the owner / open

1. The mouth lines where the onboard shows no cones at all: L 4484-4534 (onboard t000: K-rail, no cones), drag-strip R
   2533-2561 / 2973-3015, Zorros R 4162-4174, L 207-213 (prep notes). His rule covers placement where the onboard shows
   cones; whether lines stay where it shows none is his call.
2. Sweeper mouth R 3663-3683 beside the declared row R 3645-3655 (onboard t122 "cones on the right"): t122 does not show
   them clearly; not changed.
3. Kerb extents of the 37 other runs: from their capture block lines, confirmed on their frames; dense onboard frames
   (0.5 s) would measure them the way the T5 run was measured.
4. The hood camera placement (item 2): the reason the kerbs vanish from the hood.
5. The T2 tyre wall's height (no reference in frame) and its dark read at distance.
6. Crack-seal coverage: GitHub issue #10.
7. Carried: the T2 patch curved line (side_02 590 R), the paddock lanes' square ends, the in-page surface scan
   (not rerun this round).

## Verification note (24 Oct 2026, 11:35 PDT)

The full test suite on this branch at 9c61d17, run on a quiet machine (1-minute load 2.2, nothing else heavy but one
single-threaded Sonoma stage build): 53 files, 413 tests passed in 50 s (`npx vitest run`). The seven timing failures seen
on 23 Oct (perf.test 2.4 s against its 2 s budget, replay, poses, scenerygates, ai_behaviour's 60 s self-play) were the
machine's load at 30-70, not the branch; the preview's caveat is cleared.
