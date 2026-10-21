# Sonoma round 8 (21 Oct 2026): continuous pit wall (note 59), the 8a station tower and its two walls (notes 53, 60, 61)

Scenery only (stage 3). Geometry byte-identical: stage 1 was re-run into a scratch candidate first and reproduced the
published track.json / heightfield.bin byte for byte; the published package keeps them.

| file | before (c232607) | after |
|---|---|---|
| public/tracks/sonoma/track.json (md5) | b54342ae7d1c2bddfdb664031abec570 | b54342ae7d1c2bddfdb664031abec570 |
| public/tracks/sonoma/heightfield.bin (md5) | 5fd95a7d1ae2d72ab3be047c072e007d | 5fd95a7d1ae2d72ab3be047c072e007d |
| ghosts.json, far_heightfield.bin, far_ortho.jpg | | unchanged (byte-identical) |
| scenery.json (sha256/16) | 7944c73cfc4d62b6 | changed (below) |
| ortho.jpg | | 482 px change by > 2 levels (pit-lane tone match on the re-clipped lane polygon; 293 of them at the pit-out, s ~125) |
| registry rev (src/scoreboard/config.ts) | 3fa66ae8a4 | 51c8d70642 (the package fingerprint; registry.test.ts) |

Before the change the pipeline (stage 1 + 2 + 3 into a scratch candidate, current config) reproduced every published
file byte for byte, so the diff below is the round's alone.

## A. The pit wall is continuous (owner note 59)

Owner: "I'm pretty sure the wall on the left side of the pit straight extends all the way up to the red arrow and through
the yellow line. Anything else would be extremely dangerous."

- `pit straight, pit-lane side, to its nose at T1` (ended at a nose point at s 92, pushed 0.99 m off the road) is now
  `pit straight, pit-lane side (continuous to the pit-out blend line)`: one run, s 3953 to s 158, 296 m (was 235 m).
  - s 3953-76: the 19 Oct measurement, unchanged.
  - s 79-85: the island's pit-lane-side line converging toward the track-side line. Measured with wall_measure.py along
    the left edge, offset 1.0-3.0 m, over s 40-96: 92 % picked, rms 0.05 m.
  - s 90-158: the wall at the edge. wall_measure.py along the left edge, offset -0.6..1.0 m: 84 % picked, rms 0.05 m,
    p90 0.09 m, offset beyond the edge p50 -0.05 m.
    - s 92-133, the K-rail segment tops (the "dotted block line"): 80 % picked, rms 0.15 m.
    - s 134-158, the solid section: 98 % picked, rms 0.03 m.
  - It ends at s ~158, 0.3 m from the first point of the double yellow blend line (pit_exit_cones.latlon[0]).
- Kind `pitwall` (was `concrete`). From s ~94 the measured wall stands at the fitted edge (-0.2..0.0 m). Under the round
  7f push-out rule a pit wall stands at the pit-wall minimum + 0.05 m (0.35 m); a concrete wall would be moved to
  0.55 m, 0.6 m off its measurement. 49 points were moved and logged: s 92-158 (measured -0.16..+0.10 m) and s 3962-3995
  (measured -0.27..+0.16 m).
  - Side effect: the front-straight start of the run (s 3953-3999) now stands 0.2 m closer to the track than in round 7f
    (0.30-0.35 m from the edge, was 0.55 m). The pit wall boards on it (blue, green) follow it. The other board and wall
    points move along the line only, because the barrier is resampled evenly over its new length.
- Removed: `T1 inside, block line from the pit-wall nose` (kerbs_declared, kind 'blocks', s 88.8-133.7). Per note 59
  those blocks were the K-rail's segment tops. No cone or paint stood in for the wall: the pit-exit cones and the double
  yellow start at s 158, unchanged.
- Removed: the gates.allowed entry 'pit lane', left, s 84-104 ("the pit-wall nose at T1 ... beyond it the pit-out lane runs
  beside the track"). With the continuous wall it is false, and containment passes without it (0 escapes; the entry was
  hit by 0 rays). Removing an allowance only tightens the gate.
- `edge_line_cut` now starts at s 88 (was 100) and its `why` was rewritten. The blocks strip used to break the white edge
  line from s 88.8. Without it the line would have run on along the K-rail to s 100, which the captures do not show. The
  left run now ends at s 88.8 (was 86.6). The run s 242-327 is now written in its wrapped form (4340.8-4426.1, the same
  stretch).
- pit_lane.walls: the declared wall's name was updated, and its range now runs to s 158 (was s1 105).
- The pit-lane polygon is re-clipped at the new wall (pit_lane_clip_walls): 52 right-edge rows (721-772) moved by up to
  0.66 m. The lane-path gate passes: 855 stations, 0 obstacles, 0 pinched.
- Comments now say what is true: the round 7f "not placed" note, the stage-1 pit_exit comment (comment only; the
  geometry config id is unchanged), the pit_exit_near_wall_only note and the blend-line note.
- Height: the run keeps 1.1 m (the SAFER wall). The T1 section is K-rail, 0.8-0.9 m: the shadow gives about 0.8 m, and the
  inventory pit row s 100 reads 0.9 m (jersey-ref). It is drawn at 1.1 m because a run has one height. That is within
  the HEIGHT tolerance, and h_src says so.
- Wall-ends gate: passes on its own with the continuous wall. 14 upstream ends were checked, 0 exposed (round 7f checked
  15; round 5's T9-right part 1 head is no longer an end). The run's only end near the merge is downstream, at s 158.

## B. The 8a station is a brown-roofed tower over a wall (owner notes 60, 61)

Owner (note 61): "The tower's roof sits over the wall, but the wall facing T6 runs all the way across the red line I drew
(protects the station from people losing control at T6)" and "note I didn't outline the wall all the way back towards T7,
just close to the tower for you".

1. Removed: marshal post `8a outside` (s 2483, 10.9 m left, among the campers). Per note 60 it is a camper.
2. Placed: marshal post `8a (T9) station tower` (the kit's elevated hut, style 'tower').
   - Position and size: centre (38.1645832, -122.4585614) = ENU (-84.15, 209.64), from owner/t8a_station.json. The
     owner's 4.0 x 3.5 m outline (long axis bearing 280.6) is read as the roof seen from above. The hut is therefore
     w 2.8 x d 2.3 m under the kit's 0.6 m overhang.
   - Facing: the open front faces bearing 10.6 (`heading_deg`), toward the 8a-T9 pass.
   - Seen from both passes: s 2659, 32.2 m right, on the 8a-T9 pass; s 1772, 40.7 m right, on the drag strip.
   - Colours: roof `#3a2917`, the median of the roof pixels on c20_s0275, rgb (58, 41, 23), a dark brown (note 60:
     "brown-roofed"). Walls white with no coloured band, from owner_52.
   - Height: 2017 lidar DSM - DEM over the footprint shows a 4 x 4 m block 3.5-4.1 m above the ground (p90 3.65 m,
     max 4.06 m; the roof falls to the SE). With h 4.0 the kit's roof top is at 3.81 m and the deck at 1.4 m, over the
     0.85 m Jersey.
   - Builder and app: optional marshal-post keys `heading_deg`, `d` and `roof` (build_scenery.py, src/app/scenery.ts,
     kit README). Without them a post is built as before, and every other post's record is byte-identical.
3. Walls, measured with wall_measure.py along the owner's lines and their extensions on c20_s0165 / s0220 / s0275 /
   s0330 / s0385 / s3465 / o0440. The final polylines come from a robust pass over wall_measure's own picks: a 15 m
   running median that rejects parked trailers (more than 0.4 m off), then the 3 m Gaussian. The figures below are
   wall_measure.py re-run along each final line.
   - **Track-side wall**, `T8a to T9, right: the 8a station wall along the paddock (round 8)`. Concrete, h 1.0, pale
     blue.
     - Length and range: 166 m, from s 2515 (20.3 m right) to s 2667 (30.7 m right) on the 8a-T9 pass. Seen from the
       drag strip at s 1922-1766, 34-48 m right.
     - Fit: 93 % picked, rms 0.06 m. The robust pass: 99 % picked, 98 % kept, rms 0.04 m. Along the owner's line 1:
       100 % picked, rms 0.03 m.
     - It is one wall, and it replaces round 5's `T9, right: concrete wall along the 2020 bypass` parts 1 and 2 (the
       same wall, in two pieces with a 9 m gap at a parked trailer). It also replaces round 5's `T8a, right` tyre line,
       which left the dark band after s ~2550 and ran 3-5 m behind the wall in the grass.
     - It is NOT the continuation of `T8 to 8a, right` (that run ends at s 2510). The 8a crossover road lies between
       the two, 13.5 m end to end, and gates.allowed lists that gap. So the two runs are not joined.
     - Lidar 2017 along the wall: median 1.08 m (facing included).
   - **Black tyre facings** on its track face, black, h 1.0, snapped by tyre_facings (0.55 m):
     - NW part, s 2515-2590: wall_measure dark, 99 % picked, rms 0.39 m. A 2026 trailer hides about 18 m of it; onboard
       t084 shows one continuous black wall.
     - In front of the station, s 2636-2665, along the owner's line 1: wall_measure dark, 100 % picked, rms 0.42 m. This
       follows note 53 (owner_52) and onboard t088, which shows a dark wall with a SONOMA TURN 8 sign. The sign is not
       placed: no local frame of it is legible.
     - Between the two (s 2590-2636) the wall is light grey with no facing (t086).
   - **T6-facing wall**, `T9 to the back straight, right: T6-facing Jersey under the 8a station (round 8)`. Concrete,
     h 0.85.
     - Length and range: 179 m, from the tower (s 2653, 28.7 m right; 0.8 m past the owner's drawn NW end) to the paved
       area by the 2020 bypass (s 2864, 48.6 m right of the back straight). That is 125 m past the owner's drawn SE end,
       which was clipped at the window edge. Seen from the drag strip at s ~1780, 38 m right.
     - Fit: 100 % picked, rms 0.05 m. The robust pass: 98 % kept, rms 0.04 m.
     - Lidar 2017: median 0.84 m (p25 0.78, p75 0.91) over the owner's part, and 0.8-1.0 m on the extension (one 30 m
       stretch reads 2.8-3.0 m, from vehicles parked in 2017). That is a Jersey.
     - Lidar 0.0-0.2 m in the 14 m NW of the tower: the wall does not reach the track-side wall.
     - It is continuous under the tower, with no gap. The tower centre is 1.95 m from the measured line (the owner's line:
       1.67 m), and 1.1 m of the wall runs under the owner's roof outline.
4. Both passes: one object per wall and the tower, none created per pass. The coverage tables give the T6-facing wall
   stations 1692-2864 (its points are nearest the drag strip at the NW part, nearest the back straight at the SE end).
   Rows covered:
   - s 2517 right tyre_wall: the NW facing.
   - s 2591 right wall: the track-side wall.
   - s 2644 right wall ("dark wall with a SONOMA TURN 8 sign"): the track-side and T6-facing walls.
   - The drag-strip rows s 1742 / 1809 right are unchanged.
   - No station row exists near either pass, so the tower is supported by its capture source. The '8a outside' hut had
     no row either: MISSING 0, UNSUPPORTED 0.

## Gates and tests (verbatim)

`build_track.py --track sonoma --stage scenery --publish --overwrite-package` (scratch candidate /tmp/r8/cand, stage 1
re-run there first, byte-identical):

```
[ok] edge gate left : rms vs 41-st median (R>250 m, 1983 st) 0.051 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.078 m at 4001 (next 0.077@3999, 0.077@4000; <= 0.1) | max edge-column cross-section step 0.018 m at 1098
[ok] edge gate right: rms vs 41-st median (R>250 m, 1983 st) 0.030 m (<= 0.1) | max adjacent step (R>100 m within +-30) 0.086 m at 2825 (next 0.086@2826, 0.086@2786; <= 0.1) | max edge-column cross-section step 0.036 m at 3062
[ok] world continuity left : max |third difference| of the edge polyline 0.0099 m at station 3056 (<= 0.02)
[ok] world continuity right: max |third difference| of the edge polyline 0.0072 m at station 3076 (<= 0.02)
[ok] profile gate: max cross-section step any column 0.036 m at station 3062 column 6 (<= 0.1)
[ok] barrier gaps: min gap to the edge 0.30 m over 71 runs
[ok] containment: 12324 rays (normal, +-35 deg, every 2 m, 120 m), 0 escapes in 0 runs, 1218 onto allowed runoff, 201 pit-lane junction hits
[ok] pit connectivity: pit box -> pit exit -> track: 249 m, 0 barrier crossings, 1 m unpaved, 0 cone-line crossings; track -> pit entry -> pit box: 640 m, 0 barrier crossings, 1 m unpaved, 1 cone-line crossings
       lane (two paths 1.5 m from each edge, 1.0 m clearance, cone lines count): 855 stations, 0 obstacles, 0 pinched stations
[ok] sign placement: 129 signs, boards and posts checked, 0 misplaced
[ok] wall ends: 14 upstream run ends within 8 m of an edge checked, 14 joined / cushioned / lapped / tapered, 0 exposed to oncoming travel
[ok] tyre facings: 0 tyre runs standing 0.8-2.5 m off a wall side by side (a tyre run beside a wall must face it, within 0.8 m, or meet it end to end)
[ok] coverage: 280 inventory rows checked (13 'ahead' rows without a distance skipped), 207 scenery objects; MISSING 0 (none), UNSUPPORTED 0 (none); DISPOSITIONED 30 (ASSIGNED 0); ...
[ok] pit lane: 13 pit-lane wall rows; 0 not declared in the config's pit_lane.walls, 0 with no barrier in the package
```

Barrier gaps: the minimum is 0.3013 m, at station 3997, on the pit wall (kind pitwall; the gate's minimum is 0.3 m). It
is a front-straight point measured +0.30 m from the edge, so the rule leaves it where it was measured. Round 7f had
0.51 m, with the run as concrete.

- `npx tsx tools/track/gates/run_gates.ts public/tracks/sonoma <gates_config.json>`: exit 0, with the same containment,
  pit connectivity, lane, sign, wall-ends and tyre-facing lines as above.
- `npx tsx tools/track/gates/run_coverage.ts public/tracks/sonoma tools/track/compare/sonoma/inventory.json
  <coverage_config.json>`: exit 0. Output:
  `COVERAGE_JSON {"pass":true,"missing":0,"unsupported":0,"assigned":0,"dispositioned":30,"invalid":0,"missingByKind":{},"unsupportedByKind":{},"heights":0,"pit":{"pass":true,"undeclared":0,"absent":0}}`
- `npx vitest run`: Test Files 51 passed (51); Tests 394 passed | 1 expected fail (395). The first run failed only
  `registry.test.ts › sonoma: rev is the fingerprint of the published package`, which every publish changes. It passed
  after the rev update.
- `uv run ... python -I -m pytest tools/track -q -p no:cacheprovider`: 26 passed.
- `npx vite build`: built. `tsc --noEmit -p tsconfig.build.json`: exit 0.
- `python3 -I tools/track/compare/compare_packages.py --ref <copy of the c232607 package> --cand public/tracks/sonoma`:
  matched 373, missing 2, extra 3, height diffs 0.
  - Missing: the kerb `T1 inside, block line from the pit-wall nose` (s 112) and the station `8a outside` (s 2483).
  - Extra: the station `8a (T9) station tower` (s 2659), the tyre wall `T9, right: black tyre facing in front of the 8a
    station`, and the wall `T6-facing Jersey under the 8a station`.
  - Within the 15 m matching the following count as matched: the pit wall's extension, the track-side wall (it replaces
    two parts at the same place) and the re-measured NW facing.
  - Record level: in barriers, 4 removed (the old pit wall, the T8a right tyres, T9 right parts 1 and 2) and 5 added
    (the continuous pit wall, the track-side wall, two facings, the T6-facing wall). Kerbs: 30 to 29. Landmarks: one hut
    swapped for the tower. Also changed: the edge-line runs (above), the pit-lane parts (the re-clip) and the two
    pit-wall board structures' points (they follow the wall).

## Evidence (local only, imagery never committed)

- Capture windows (capwin.py, --pkg public/tracks/sonoma; the owner's lines and outline in red):
  - `capwin_s120_h60_pitwall.png`
  - `capwin_s2600_h90_tower_walls.png`
  - `capwin_s1770_h60_tower_walls.png`
- Eye-level stills (pose_walk.ts, the hood_r7e tool; dev server on a private port, headless Chrome with a throwaway
  profile):
  - `pitwall_s075_along_r8.jpg`, `pitwall_s110_along_r8.jpg`, `pitwall_s140_along_r8.jpg`, `pitwall_s170_back_r8.jpg`
  - `tower_drag_s1760_right_r8.jpg`, `tower_drag_s1740_aheadright_r8.jpg` (drag strip, looking right)
  - `tower_8a_s2650_right_r8.jpg`, `tower_8a_s2620_aheadright_r8.jpg` (8a-T9, looking right)
  - `wall_8a_s2540_right_r8.jpg` (the NW part of the track-side wall)
- Reference frames read, not copied: inventory frames t084 / t086 / t088 (RAZip6S84CM), owner_52, owner_61.
