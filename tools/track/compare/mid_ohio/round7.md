# Mid-Ohio round 7: stage 3, the scenery, to a drivable package

Opus 5.5, 27 Oct 2026, branch `mid-ohio` (from b5343d7). Scope (the brief): kerbs outside the race edges with the
yellow ones included, the paved extras from the owner's green strokes, walls, bridges, stands, buildings, boards, the
pit lane, far terrain; publish with every gate passing; commit the registry entry as wip; judge the compare sheets.
The owner's two answers of 26 Oct (evening) are applied as given: the hood sheet's road is accepted (kerbs are this
round's job, "would be easier to just drive the track"); **no T4 margin zone** ("Don't make the tracks less
representative of reality to patch over an underlying AI issue"): the line is unchanged, the braking drift is an AI
issue.

Machine health: battery 95-100 % (on charge at the start, discharging from the Sonoma check on, never under 90 %),
1-minute load 1.5-10.6 (one burst to 10.6 while the Buttonwillow / Laguna checks overlapped another agent; one heavy
process of mine at a time), 21 GB free.

Package `public/tracks/mid_ohio/`, **rev 748b55ca59** (round 7b, section 13 on; was a692501d35 at the first hand-back) (registry rule: sha256 over the sha256 of track.json,
heightfield.bin, ghosts.json, scenery.json, far_heightfield.bin).

## 1. Kerbs outside the race edges (step 1)

**Wiring.** The race edges are the asphalt-facing face of every kerb (owner decision 2), so every strip lies in a
band from the edge outward:
- builder (`build_scenery.py`): config `scenery.kerb.inside` (absent: True) is written to `scenery.json kerbs.inside`;
  a/b strips of `kerbs_declared` may now carry `width`, `profile` and `edge_line` (absent: as before).
- physics: `src/physics/track.ts kerbBandCentre` already reads `inside` and a strip's `off` (band centre beyond the
  edge); `buildKerbStrips` raises the band at that offset (no change).
- app: `src/app/scenery.ts buildKerbs` draws a strip with `off` from off - w/2 to off + w/2 (no change).
- gates: `gates/terrainGates.ts` (kerbs on surface) reads `off` / `inside` the same way (no change); the kerb traversal
  gate (`src/physics/__tests__/kerbgate.test.ts`) ran on mid_ohio: no roll past 15 deg, no rollover (max roll 3-4 deg).
Every Mid-Ohio strip carries its measured `off` = width / 2 (the band 0.00 .. width beyond the edge).

**Measurement.** `r7/kerb_scan.py`: along both edges every 0.5 m, the clean z20 capture pixels from -0.4 to +2.4 m
beyond the edge classified red / white / yellow; a station is a kerb where the band 0-0.6 m holds >= 25 % yellow or
red and white blocks (>= 8 % each); runs merged over 3 m gaps, >= 5 m; per run the per-offset colour profile, the
yellow band's outer limit (share >= 0.5) and a red outer band beyond it, the red / white block band's outer limit (red
share >= 0.2). Four stretches the local rule split were read as one run after the capture check (`--force`): right
2505-2541 (T8 apex), right 381-458 (T1 exit), left 2727-2785 (T9 exit), left 2578-2615 (T8 exit). One run was
rejected: left 3595-2 (the S/F stripes and the pit-wall foot, c20_s3560). `r7/kerb_cfg.py` writes the config entries
and `r7/kerb_table.json`; the frames are the inventory rows within 25 m.

**Type and colour.** Red / white: low raised concrete kerbs with a rounded outer face (N837 t016, IndyCar t030); the
height is NOT measured (no frame resolves it): declared 0.05 m over a 0.25 m face (Sonoma's driven profile). **Owner question** (also in the registry comment): the 5 cm is a declaration, not a measurement; the owner judges it in the drive. Yellow and
the red outer bands: flush paint (N837 t042, 360 t036 / t054: no face). Colours from the sunlit 2025 frames (360 t054
left / t130 right, IndyCar t022): red #c8443c, white #e2ddd4, yellow #e2b21c (the overcast N837 values read washed out,
judge F1). Block length 1.0 m (c20_s0880). 13 strips keep the white edge line along their inner face where the captures
show it (white share >= 0.3 within 0.05-0.25 m inside the edge; `edge_line`).

**The kerb table** (23 strips in 20 runs; the inventory's 80 kerb rows are all covered, MISSING 0):

| # | kerb | side | s (m) | colour | profile | band beyond the edge (m) | white edge line along it | captures | frames (video@t) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | T1 inside (apex) kerb | left | 299-348 | red / white blocks | raised 0.05 m | 0.00-1.65 | no | c20_s0240, c20_s0280 | e25u_vjn1uM@32.0; OJaBJz18xEo@16.0; 9Drr1VkE1_U@90.0 |
| 2 | T2 (Keyhole) exit kerb | left | 1030-1102 | yellow + red outer band | flat paint | yellow 0.00-1.05, red to 2.15 | no | c20_s0960, c20_s1000, c20_s1040 | 9Drr1VkE1_U@102.0; e25u_vjn1uM@54.0; 9Drr1VkE1_U@34.0; OJaBJz18xEo@42.0; 9Drr1VkE1_U@168.0; e25u_vjn1uM@56.0 |
| 3 | T4 exit kerb | left | 2013-2042 | yellow | flat paint | 0.00-1.45 | no | c20_s1920, c20_s1960 | 9Drr1VkE1_U@48.0; e25u_vjn1uM@78.0 |
| 4 | T5 (Madness) apex kerb | left | 2087-2138 | red / white blocks | raised 0.05 m | 0.00-1.65 | yes | c20_s2040, c20_s2080 | 9Drr1VkE1_U@184.0; 9Drr1VkE1_U@50.0; e25u_vjn1uM@82.0; OJaBJz18xEo@72.0 |
| 5 | T7 exit / T8 approach kerb | left | 2352-2402 | yellow | flat paint | 0.00-1.55 | no | c20_s2280, c20_s2320, c20_s2360 | e25u_vjn1uM@92.0; OJaBJz18xEo@84.0; 9Drr1VkE1_U@192.0; 9Drr1VkE1_U@58.0 |
| 6 | T8 crest kerb | left | 2446-2464 | yellow | flat paint | 0.00-1.15 | yes | c20_s2400 | none within 25 m (capture only) |
| 7 | T8 exit kerb | left | 2578-2615 | yellow | flat paint | 0.00-1.35 | yes | c20_s2520, c20_s2560 | 9Drr1VkE1_U@196.0; OJaBJz18xEo@92.0; e25u_vjn1uM@100.0 |
| 8 | T9 exit kerb | left | 2727-2784 | yellow + red outer band | flat paint | yellow 0.00-0.85, red to 1.45 | no | c20_s2680, c20_s2720 | e25u_vjn1uM@104.0; OJaBJz18xEo@98.0 |
| 9 | T11 apex kerb | left | 3082-3114 | red / white blocks | raised 0.05 m | 0.00-1.65 | yes | c20_s3040, c20_s3080 | OJaBJz18xEo@110.0; e25u_vjn1uM@114.0 |
| 10 | T13 apex kerb | left | 3440-3474 | red / white blocks | raised 0.05 m | 0.00-1.65 | yes | c20_s3400 | e25u_vjn1uM@126.0; OJaBJz18xEo@126.0 |
| 11 | T1 exit kerb | right | 382-458 | yellow + red outer band | flat paint | yellow 0.00-1.15, red to 2.15 | no | c20_s0320, c20_s0360 | 9Drr1VkE1_U@22.0; 9Drr1VkE1_U@156.0; e25u_vjn1uM@36.0; OJaBJz18xEo@20.0; 9Drr1VkE1_U@92.0 |
| 12 | T2 (Keyhole) apex kerb | right | 872-1016 | red / white blocks | raised 0.05 m | 0.00-1.65 | yes | c20_s0800, c20_s0840, c20_s0880, c20_s0920, c20_s0960 | 9Drr1VkE1_U@98.0; 9Drr1VkE1_U@30.0; OJaBJz18xEo@34.0; e25u_vjn1uM@48.0; 9Drr1VkE1_U@164.0; OJaBJz18xEo@36.0; e25u_vjn1uM@50.0; 9Drr1VkE1_U@100.0; 9Drr1VkE1_U@32.0; 9Drr1VkE1_U@166.0; e25u_vjn1uM@52.0; OJaBJz18xEo@40.0 |
| 13 | T4 apex kerb | right | 1950-1984 | red / white blocks | raised 0.05 m | 0.00-1.65 | yes | c20_s1880, c20_s1920 | e25u_vjn1uM@76.0; 9Drr1VkE1_U@116.0; OJaBJz18xEo@66.0 |
| 14 | T6 kerb | right | 2150-2194 | yellow | flat paint | 0.00-1.15 | yes | c20_s2080, c20_s2120 | e25u_vjn1uM@84.0; OJaBJz18xEo@76.0 |
| 15 | T7 apex kerb | right | 2270-2304 | red / white blocks | raised 0.05 m | 0.00-1.65 | yes | c20_s2200, c20_s2240 | 9Drr1VkE1_U@54.0; OJaBJz18xEo@80.0 |
| 16 | T8 apex kerb | right | 2506-2541 | red / white blocks | raised 0.05 m | 0.00-1.25 | yes | c20_s2440, c20_s2480 | OJaBJz18xEo@88.0; 9Drr1VkE1_U@60.0 |
| 17 | T9 apex kerb | right | 2634-2681 | red / white blocks | raised 0.05 m | 0.00-1.45 | yes | c20_s2600, c20_s2640 | OJaBJz18xEo@94.0; e25u_vjn1uM@102.0 |
| 18 | T11 exit kerb | right | 3140-3203 | yellow | flat paint | 0.00-1.25 | yes | c20_s3080, c20_s3120, c20_s3160 | OJaBJz18xEo@112.0; e25u_vjn1uM@116.0; OJaBJz18xEo@114.0 |
| 19 | T12 (Carousel) apex kerb | right | 3329-3390 | red / white blocks | raised 0.05 m | 0.00-1.65 | yes | c20_s3280, c20_s3320 | OJaBJz18xEo@120.0; e25u_vjn1uM@122.0; e25u_vjn1uM@16.0; OJaBJz18xEo@122.0; e25u_vjn1uM@124.0; 9Drr1VkE1_U@82.0; 9Drr1VkE1_U@12.0 |
| 20 | pit-straight kerb (T13 exit) | right | 3514-3575 | yellow | flat paint | 0.00-1.65 | no | c20_s3480, c20_s3520 | 9Drr1VkE1_U@148.0; e25u_vjn1uM@22.0; OJaBJz18xEo@128.0; 9Drr1VkE1_U@84.0; e25u_vjn1uM@130.0; OJaBJz18xEo@4.0 |

Inventory rows the time maps displace were corrected (attrs.correction, `ahead_m`): T4 exit (IndyCar C 182, A 48, 360
78), T5 (C 184), T4 apex (B 114, C 180, A 46), T7 (C 188, A 54), the Carousel (B 82, C 146, A 12). The IndyCar B / C
rows ('corroborate', sigma 34-60 m) set no endpoint: every strip's extent is the captures'.

## 2. The paved extras from the green strokes (step 2)

The owner's round-2 green strokes (`tracks/mid_ohio/owner/r2/merged.json green_enu_xy`, 1223 points) are the paving
edges (`edges_from_green`) of three closed roads on the OSM raceway ways the loop does not use:

| closed road | OSM way | paving edge on his green | surface | mouths |
|---|---|---|---|---|
| inner chicane | 444205376 | left 180 / 203, right 202 / 203 points | asphalt (grey, a touch lighter: the ortho's own tone) | rejoin mouth coned: 4 orange cones (N837 t026-t027, Apr 2026); entry mouth open (360 t040) |
| T1-T3 connector, south | 444205377 | 81 / 105, 105 / 105 | asphalt | open (c20_s0560, c20_s1280) |
| T1-T3 connector, north | 444205378 | 67 / 102, 94 / 102 | asphalt | open (360 t064 right) |

`zones_meet_edge` and `paved_zones_over` take the mouths onto the road (no dirt wedge). The pit-exit apron is the pit
lane's own paving to its merge (section 4) with the painted ladder line (`paint_lines_declared`: two 0.15 m lines 0.8 m
apart from the pit wall's end to the T1 inside kerb, s 212-298; the rungs are not drawn: no kit pattern). Every mouth's
containment rays are listed in `gates.allowed` with the frames that show them open.

Paved coverage of his green (`r7/green_cover.py` -> `r7/green_cover.json`): 95.1 % of his green points lie within 2.0 m
of a modelled paved boundary (73.8 % within 0.5 m, p50 0.11 m). Farther: 25 points along the pit-exit / footbridge
(x -138..-166: the lane's left edge from the NAIP sits 2-6 m inside his line under the bridge), 7 + 13 + 5 + 4 at the
chicane / connector mouths where his line turns onto the course edge (2.8-4.6 m), 6 at the south connector's west end.
There is no paved-coverage gate in this branch (searched: tools/track, src, the skill); this measure stands in for it
and the remaining 4.9 % is open.

## 3. Walls, fences, bridges, stands, buildings, boards (step 3)

**Barriers.** OSM maps the circuit's barrier lines (ways 13152089xx, 2025); `r7/barrier_table.py` set each run beside
the inventory rows on its side and range, and each was checked on its capture window. Every OSM wall now carries an
`osm_barrier_overrides` entry with its source: red stacked W-beam armco (the footage's 'armco (stacked W-beam), red' on
the inventory's wall rows; three beams, 360 t042 left), 1.2 m (horizon ratio 1.4 m with the 1.7 m camera on 360 t042,
fence-post ratio 1.45 m; the round-4 readings 0.8 / 1.3 m; +-0.25 m), colour #8c4a42 (sunlit N837 t016 / t022), a 2.3 m
catch fence on the runs the footage shows it on (3.5 m total, fence-post-ref). New opt-in keys: armco `rails` (stacked
beams, app), `osm_fence` (overrides on OSM fences), and the OSM-wall name 'osm:<id>' for boards.

| kind | runs | evidence |
|---|---|---|
| armco (red, 3 rails, 1.2 m) | 31 (12 with a 2.3 m catch fence) | OSM line + the frames named per run in the config |
| white concrete | 3: T9-PERMCO wall 0.8 m (360 t104), T13 pit-entry side wall 1.04 m (IndyCar A t012), the black pit-in barrier 1.0 m with three yellow impact barrels (360 t018, N837 t125; measured `wall_measure.py --feature dark`, rms 0.56 m) | |
| pit wall | 1 (measured, below) | |
| fence (OSM, 2.4 m, height unmeasured) | 7 kept, 3 dropped (no 2026 evidence, off the captures) | c20 windows |
| tyres | 1: a 6 m tyre cushion at the head of the T3 armco (c20_s1400 / c20_s1440 shows a tyre bundle there) | kept: the capture is the evidence and wins over the brief's 'no tyre walls', which was a reading of the videos (the orchestrator's ruling, 27 Oct 2026) |
| dropped OSM walls | 4 (the line behind the pit boxes: 360 t024-t030 left shows the boxes open to the paddock) + the OSM pit-wall line (superseded) + the OSM T1-inside armco (replaced by a declared run: under the footbridge the contaminated 2019 ground stepped its top 1.85 m) | |

Wall ends: two known exposures (gate-listed for the owner): the armco head at the T5-T6 access-road mouth (9 m out,
c20_s2120) and the T1 inside armco stopped 9 m before the footbridge abutment. One declared opening: the PERMCO
footbridge's abutment between the armco and the white wall (c20_s2800).

**Heights.** Pit wall **1.04 m**: the 360 lap t026 left re-read (base row 386, top 346, horizon 320-325 from the heads
of the people in the lane) gives 1.03-1.08 m with the 1.7 m camera; the 2019 lidar 1.04 m (r5); round 4's 0.7 m put the
horizon too low. Resolved: 1.04 m, +-0.1 m (inventory rows corrected). Footbridge decks from the 2019 lidar: T1 4.5 m
(the builder's class-17 / class-1 read over the road; 4.42 m in r5), PERMCO 5.6 m; both with `bridge_stairs`.

**Stands and structures** (`structures`): main grandstand (covered, two tiers, red roof at 6.3 m: lidar 6.3-6.9 m;
OSM 1315208916 footprint on c20_s3480), T1-approach covered stand (89 m, roof 6.2 -> 4.6 m: lidar 6.7 -> 4.5 m), T4
bleachers north and south (OSM leisure=bleachers, 14 rows, lidar box 4.8 m), starter tower (4 storeys, 12.8 m, red
roof; its roof and the lidar's 15 m top at (57, 11) ENU, 8.6 m east of the OSM outline), S/F starter's stand (N837 t130
PERMCO boards), T5 scoring pylon (lidar column 4 x 4 m, 30.7 m), pit garages east / west (garage kit, white with red
bands, lidar 5.3-5.4 m). New opt-in: grandstand `cover` (a roof over the rows, app + collision box). Buildings: 6 OSM
footprints kept with their capture source (`building_evidence`), 11 dropped with no 2026 source (NAIP 2022 only: the
clean captures mask the paddock), lidar `building_height_robust`.

**Boards** (typed names in the observed colours, no logo artwork): Keyhole outside PERMCO / HRC / SUMMIT / HONDA /
START / O'REILLY / HRC (N837 t038-t040), T4 outside HONDA, T5 hillside HONDA (360 t080), T7 Firestone / HONDA, the pit
straight's HONDA wall (360 t130), T3 HONDA / NTT DATA, VELO on the pit wall toward the footbridge, HONDA on the pit-in
barrier, VELO at the PERMCO bridge; 108 panels. Bridge banners: Firestone / HONDA (T1 footbridge), PERMCO + Pumps and
Motors / VELO (PERMCO bridge). Distance boards (stacked digits, new app rule for multi-digit text): 12, from N837
t029-t031 / t059-t060 / t106 and the 360 lap. Cones: 3 lines (T4 braking zone 2, the Keyhole verge 2, the chicane
mouth 4; Lemons event cones, Apr 2026). Marshal post: the yellow back-straight tower (N837 t054). Masts: two timber
utility poles on the T1 inside (lidar spikes 8.3 / 9.9 m). "Turn N" paint: none seen. Run-off classes: the ortho's own
(grass / sand). **The T4 run-off raise stays unresolved and unmodelled** (round 4's bank rule lowers the outside
shoulder; the operator's raise has no numbers).

**Corroborate rows (IndyCar B / C).** No object takes an endpoint from a B or C row alone: their kerb rows were moved
to the kerbs the captures show (section 1); their wall rows sit on armco the 360 lap and N837 show on the same side.

**Dispositions** (manifest.md, round 7): 15 lines (placed 9, rejected 6: IndyCar-weekend scaffolds, tents and canopy
the Apr 2026 Lemons onboard does not show). Inventory corrections: the chicane re-join kerb is a closed road's kerb
(drawn as `kerb_lines`), the starter's stand is a tower (built), the T5 hillside is ground; rows added for the judge's
findings (cones, the T4 fence).

## 4. Pit lane (step 4)

OSM 'Pit Lane' (444205379) from the pit-in at the T13 exit (s ~3369) along the pit straight, under the footbridge and
round the T1 inside to the pit-out (s ~380), 590 m paved, tone matched to the track (`match_track_tone`), clipped to
its walls with the head clearance postcondition (0.301 m). The pit wall (`declared_walls 'pit wall'`, `pit_lane.walls`
side right as driven): measured on the captures (`wall_measure.py`: the grass-island run 100 % picked, rms 0.11 m; the
straight 99 %, rms 0.22 m, 1.0-1.2 m beyond the left edge), from its nose beside the T13 kerb's end (s ~3477) to its
end 15 m before the footbridge where the ladder line takes over (c20_s0120). The pit-in barrier and barrels as
section 3. No pit-exit cones (360 t030-t034, N837 t014-t016). Gates: pit connectivity ok (box -> exit 382 m, entry ->
box 239 m, 0 crossings, lane paths clear), pit lane ok (6 rows). **Open**: no 2024+ video drives the lane: the boxes,
their lines (rule lines kept), the paddock-side edge (NAIP width, 37-55 % found) and the garages' fronts are not
surveyed.

## 5. Far terrain and imagery (step 5)

As the other tracks: far heightfield 5 x 5 km at 10 m from the 1/3" DEM with the near lidar DEM blended (z -53..40 m),
far ortho from NAIP, 7000 far trees, 1238 near trees (lidar, imagery check). Season: no tint (as Buttonwillow): the
NAIP is summer and the 2025 360 lap (July) is green; the Apr 2026 N837 grass is green too. Seventeen tree shadows on
the NAIP road were painted to the road median (`ortho_paint_over` dark, judge F12).

## 6. Gates (build_track.py --stage scenery, final build; the same on the published package by the CLIs)

| gate | value | result |
|---|---|---|
| edge left / right | rms 0.023 / 0.023 m, step 0.023 / 0.020 m | ok |
| world continuity left / right | 0.0050 / 0.0073 m | ok |
| profile | 0.021 m | ok |
| barrier gaps | min 0.97 m over 43 runs | ok |
| containment | 10788 rays, 0 escapes, 972 onto allowed (chicane, connectors, pit-in / pit-out) | ok |
| pit connectivity + lane paths | 0 crossings, 1 m unpaved, 0 obstacles | ok |
| signs | 121 checked, 0 misplaced | ok |
| wall ends | 28 checked, 26 joined / lapped / cushioned / tapered, 2 known exposures | ok |
| tyre facings / wall-tyre joins / tyre faces | 0 / 1 join ok / 0 | ok |
| wall tops | 35 runs, 0 steps | ok |
| run gaps | 1 declared opening, 0 holes | ok |
| ground marks on surface | 162 paint-line, 13518 edge-line vertices, 0 off | ok |
| cones off the surface | 8 cones on 3 lines, 0 inside | ok |
| coverage | 251 rows, MISSING 0, UNSUPPORTED 0, 15 dispositioned | ok |
| pit lane | 6 rows declared and standing | ok |
| kerb traversal (vitest) | mid_ohio: no roll > 15 deg, no rollover | ok |
| terrain override | no region | n/a |
| ground lines | 107 lines not on a modelled feature (35 barrier-related) | advisory (no `scenery.ground_lines`): **open** |

Gate CLIs on `public/tracks/mid_ohio`: `run_gates.ts` exit 0 (every line ok), `run_coverage.ts` exit 0,
`edge_gate.py --track public/tracks/mid_ohio --config mid_ohio` exit 0.

## 7. Identity proofs

- Stage 1 / 2 outputs of the published package `cmp`-identical to round 5 (`tools/track/out/mid_ohio_r5`): track.json
  d19cfb7823695525, heightfield.bin eb74f48192e28e3c, ghosts.json 9124c3d34baffcfd (the publish ran every stage).
- Sonoma: stage 3 rebuilt from its published track.json / heightfield.bin / ortho.jpg with this round's builder:
  scenery.json and far_heightfield.bin `cmp`-identical to `public/tracks/sonoma`.
- Laguna: stage 3 on the stage-1 reproduction (laguna_repro_r5) with this round's builder and with b5343d7's builder:
  scenery.json, far_heightfield.bin, far_ortho.jpg, ortho.jpg `cmp`-identical (both exit 1 on Laguna's documented
  pre-existing gate failures; no difference).
- Buttonwillow: **not obtained**: its stage 3 stops in this worktree before the scenery is written
  (`compare/buttonwillow/satellite_clean/shift.json` missing: the captures are not in this worktree). By construction
  every new key is absent from its config (`kerb.inside`, `rails`, `osm_fence`, a/b `width` / `profile` / `edge_line`,
  `brake_boards_declared`, `cover`; the 'osm:<id>' registration writes nothing); the app changes are opt-in by field
  (`rails`, `cover`) and by board text length (Buttonwillow has no brake boards). The orchestrator can run the check in a
  worktree with its captures.
- `git diff b5343d7 -- public/tracks/sonoma public/tracks/laguna_seca public/tracks/buttonwillow`: empty.

## 8. Registry and the stand-in field (step 7)

`src/scoreboard/config.ts` `mid_ohio`: rev a692501d35, length_m 3597.492, `wip: true` (not in the Start menu; its
`?track=mid_ohio` link loads it), Lemons name 'Mid-Ohio Sports Car Course', short 'Mid-Ohio', start 230 m before the
last directed corner T13 (s 3454 -> 3224, the skill's rule; the registry test's 150 m-past-a-hairpin check passes).
**The field is a stand-in**: pace `cars/field/pace.json` and the global identity are LAGUNA's, labelled in the config
comment and in the Start menu's race line ('Race · 10 laps vs a stand-in field (Laguna's)', new `fieldLabel`, opt-in).
The real field (Lemons 2026 Mid-West Crisis; results page in sources.json) is deferred.

## 9. Drive proxy, judge, sanity (step 8)

Camera walk (356 stills) and 67 compare sheets under `compare_sheets_r7/` (local). Judged against JUDGE.md by this
agent (Astra unavailable): `judge_r7.md`, 24 rows, 18 fixed in builds 10-11, the fixed places re-shot. Autopilot on the
published package (`r7/drive_report.txt`): 1:59.25, complete, the line unchanged (max lateral error 0.94 m, 290
wheel-off steps at the T4 entry: the AI issue the owner filed). Stand-in self-play, 2 laps, 45 cars:

| seed | line rms alone (p95) | AI-AI contacts / car-lap | four-off / car-lap | mishaps | passes |
|---|---|---|---|---|---|
| 1 | 0.33 m (0.62) | 0.038 | 0.051 | 2 | 153 |
| 2 | 0.27 m (0.56) | 0.000 | 0.103 | 0 | 167 |

(untuned AI knobs; T8 still carries Laguna's "Corkscrew" no-pass zone, round 6's AI finding.)

Tests: `npm run build` ok; `npx vitest run` 64 files, 537 tests passed; `pytest tools/track` 144 passed;
`inventory/test_inventory.py` OK; `test_edge_mark_transfer.cjs` 4 passed.

## 10. Stage ledger (steps of this round)

| step | record |
|---|---|
| 0.10 inventory corrections | inventory/*.jsonl attrs.correction (round 7), rows added for judge findings |
| 3.1 manifest | manifest.md round 7 (dispositions), `r7/manifest_tables.md` (generated), this file |
| 3.2 ground, trees, far terrain | section 5 |
| 3.3 kerbs | section 1 |
| 3.4 walls | section 3; barrier scan: `r7/barrier_table.py` (every OSM run against its rows); per-capture scan ledgers: `r7/scan_ledger.md` (round 7b, section 14) |
| 3.5 pit lane | section 4 |
| 3.6 closed roads | section 2 |
| 3.7 stands, buildings | section 3 |
| 3.8 furniture | section 3 (one marshal post, two poles, cones) |
| 3.9 boards, ground signs | section 3; logo scan in `r7/scan_ledger.md`: none legible |
| 3.10 bridges | two OSM bridges, lidar decks, stairs, banners |
| 3.11 paint | edge lines (kept along 13 kerbs), the ladder line |
| 3.12 gates | section 6 |
| 3.13 dispositions | 15 |
| 4.1 camera walk | 356 stills |
| 4.1b boundary audit | section 15 (round 7b) |
| 4.2 compare sheets | 67 sheets |
| 4.3 judge | judge_r7.md (builder as judge; Astra unavailable) |
| 4.4 structure stills | in the sheets; no separate pose_walk set (open) |

## 11. Acceptance checklist state

1 (stage 1): accepted. 2 (every 3.12 gate on the package): yes. 3 (no MISSING / UNSUPPORTED): yes. 4 (orchestrator has
judged every sheet): **no** (this agent judged; the orchestrator's pass is required). 5 (manifest current): dispositions
and tables yes; scan ledgers no. 6 (no leak, build + vitest): Sonoma and Laguna proven, Buttonwillow by construction
only; build and vitest pass; the stage-1 reproductions not re-run (build_track.py stage 1 unchanged this round). 7 (step
ledger): section 10. 8 (scan ledgers): **not complete**.

## 12. Open

- The field and pace (Lemons Mid-West Crisis 2026): the stand-in is Laguna's, labelled.
- AI: the T4-entry braking drift (owner: an AI issue), T8's inherited Corkscrew no-pass zone, untuned knobs.
- Pit lane survey (no driving video): boxes, box lines, paddock-side edge, garage fronts.
- The T4 run-off raise (unmodelled), the kerb heights (declared 5 cm, unmeasured), the OSM fence heights (2.4 m kept).
- The IndyCar B / C rows: used only where the captures or another video corroborate them.
- The per-capture scan ledgers (barrier, station, logo), the boundary audit, the ground-lines dispositions (107).
- 4.9 % of the green strokes farther than 2 m from a modelled paved edge (section 2); the T4 bleachers render dark.
- Buttonwillow's stage-3 byte identity (needs its captures).
- The orchestrator's judge pass over compare_sheets_r7 and the Astra review (unavailable).


## 13. Round 7b (27 Oct 2026, after the orchestrator's message): the steps left open, done

Machine health: battery 92 -> 87 % discharging, never near 35 %; load 4.6-8.0 (one heavy process of mine at a time).
The package changed (steps 2-4): **rev 748b55ca59**; every gate re-run (section 18); identities re-proved (section 19).

## 14. Scan ledgers over all 91 captures (SKILL 3.4 barrier, 3.8 station / furniture, 3.9 logo; Acceptance 8)

`r7/scan_ledger.md` (generated by `r7/scan_ledger.py` from the package and `r7/scan_notes.json`): 182 rows, every clean
capture of `satellite_clean/tiles.json` and both sides, with the stations it covers, the modelled barrier runs, the
stations / masts / towers / boards inside its footprint on that side, the logo column and the review note. Every
capture was read on 3 x 4 contact grids (local). Findings the scan adds (not placed, all open for the owner):

| capture | side | s (m) | what the capture shows | why not placed |
|---|---|---|---|---|
| c20_s0240 / c20_s0280 | left | ~330-370, 40-60 m out | two small bleacher stands on the T1 inside beyond the armco | the 360 lap t032-t034 left shows them only far and small; footprint not measured this round |
| c20_s0240 | right | ~300 | a dark facing at the T1 gravel trap's far corner | the armco there is modelled; whether tyres face it is not resolvable from the frames |
| c20_s0440 / c20_s1240-c20_s1320 | right | infield, 26 m out | the infield pair (OSM 969 / 970) reads as two lines of dark stacked objects, possibly tyres | modelled as armco from OSM; no onboard frame resolves it |
| c20_s0800-c20_s0960 | right | ~870, 30 m out | a small concrete structure on a mound in the Keyhole infield | the 360 lap's right views show open infield; not resolvable |
| c20_s1440 | left | ~1450 | a small hut at an armco gap | not resolvable from the frames (the yellow tower at ~1555 is placed from N837 t054) |
| c20_s1520 / c20_s1560 | right | ~1590-1630 | a dark object inside the barrier outline right of T3 (also ground-lines 88-90) | no video frame shows it |
| c20_s2280-c20_s2360 | right | ~2290-2330, 15-20 m out | short white low walls behind the armco | the 360 t090-t092 right show armco and grass; not resolvable |
| c20_s3040 | right | ~3080, 8 m out | a small white hut at the armco | not resolvable from the frames |
| c20_s3320 / c20_s3360 | right | ~3320-3340, 40 m out | two bleacher stands outside the Carousel | the 360 t016-t018 right show grass and armco; footprint not measured |

Stations: one marshal post placed (the yellow tower, N837 t054); the scan found three more candidate huts (above), none
confirmed by a frame. Logos: no painted ground logo is legible on any of the 91 captures (none placed). "Turn N" paint:
none on the captures.

## 15. Boundary audit (SKILL 4.1b)

`boundary_sheets.py poses --step 30` (309 poses: both course edges, the pit lane's edges, the three closed roads'
edges), `pose_walk.ts --tag b` on the dev server, `boundary_sheets.py sheets` -> `boundary_sheets_r7/` (13 sheets,
local). Every sheet read:

| # | kind | where | what | status |
|---|---|---|---|---|
| B1 | tone | edge_L_0000 (pit lane at the line) | a red smear on the pit-lane ground: the starter's stand's red post baked into the ortho | fixed: `ortho_paint_over` (on any, all) over the post (re-shot clean) |
| B2 | tone | edge_R_0480 / 0630 / 0690, zone_* (all three closed roads) | the closed roads drawn in the ortho's own tone read as pale gravel with dark NAIP blotches | fixed: `surface='apron'` (pale weathered asphalt with the grain; re-shot uniform); still paler than the footage's "a touch lighter" grey: open, a look item |
| B3 | boards | edge_L_0150-0210, edge_L_2910 | wall boards seen from behind (from the pit lane / beyond the fence) show their text mirrored | open: the kit's boards are double-faced planes on every track; not changed |
| B4 | pose | edge_L_1710-1770, edge_L_2160, pit-left_0090, pit-right_0090-0390 | the camera 6 m to the unpaved side lands on a bank, inside a building or behind the pit wall | pose artefacts, no surface finding |
| B5 | tone | edge_L_1320-1410 | dark ground beside the back straight: tree shadows of the NAIP on the verge | accepted: real trees stand there (modelled) |
| B6 | paint | edge_L_0240-0360, edge_L_3420 | pale chevrons on the pit exit / pit-in paving | accepted: the NAIP's hatched blend paint, real (360 t030-t032, N837 t014) |

No seam, gap, overlap or z-fight was found at the course edges, the kerb bands, the pit lane's edges or the closed-road
mouths.

## 16. Ground-lines dispositions (gate round 13)

All 107 findings of the scan on the package were reviewed on ortho crops with the edges and barriers drawn (local
grids) and each written into `scenery.ground_lines.dispositions` as "accepted as built: <why>" with its finding
number (the key makes the gate strict on this track; it passes: 107 dispositioned, 0 open). By cause:

| what | findings |
|---|---|
| paddock / service road edge or curb | 34 |
| shadow of the modelled armco / catch fence | 15 |
| gravel trap / grass boundary | 14 |
| building edge or its shadow | 8 |
| the T1 footbridge's access road and its shadow | 8 |
| mown line or footpath in the grass | 5 |
| the pit-in island and its barrier | 5 |
| the armco itself in the NAIP | 4 |
| the bleachers' rows or their pad | 4 |
| dark enclosure inside the T3-right armco outline | 3 |
| the kerb's outer edge / sand beside it | 2 |
| the T5 scoring pylon's shadow | 2 |
| the PERMCO footbridge's abutment and stairs | 1 |
| paddock tents / parked trailers | 1 |
| asphalt shoulder seam at the right edge | 1 |

The three "dark enclosure inside the T3-right armco outline" findings (88-90) are dispositioned as built but flagged
open for the owner (section 14). No finding called for a fix in the package.

## 17. The T4 bleachers rendered dark (judge F19)

Cause: the stands' rows face west, away from the stills' sun, and the structure soup is drawn with plain Lambert
(`structures_solid`), so the seat faces received only the ambient term. Not a missing face or a flipped normal (the
soup is double-sided; the boxes are closed). Fix (opt-in): grandstand `self_lit` in the app (`src/app/structures.ts`
structureSoups: a stand with `self_lit` goes to the terraces' part-self-lit soup, TERRACE_SELF_LIT 0.45), set on the two
T4 bleachers. Re-shot (row s 1813 left): light grey aluminium rows. Proof that other tracks are unchanged:
`r7/soup_hash.ts` (sha256 of every structure soup's positions and colours) before / after the change: Sonoma
f71411f3c2e78626, Laguna e3b0c44298fc1c14 (no structures), Buttonwillow 3da76e09e950dd5a, identical; Mid-Ohio
changes as intended.

## 18. Gates re-run on rev 748b55ca59

`build_track.py --stage scenery --publish` (exit 0, every line `[ok]`, 21 lines), then on `public/tracks/mid_ohio`:
`run_gates.ts` exit 0, `run_coverage.ts` exit 0, `edge_gate.py` exit 0; kerb traversal (vitest) ok.

| gate | value | result |
|---|---|---|
| edge left / right | rms 0.023 / 0.023 m | ok |
| world continuity | 0.0050 / 0.0073 m | ok |
| profile | 0.021 m | ok |
| barrier gaps | min 0.97 m over 43 runs | ok |
| containment | 0 escapes | ok |
| pit connectivity + lane paths | 0 crossings, 0 obstacles | ok |
| signs | 121, 0 misplaced | ok |
| wall ends | 2 declared known exposures | ok |
| tyre facings / wall tops / wall-tyre joins / tyre faces / run gaps | as before | ok |
| ground marks on surface / cones off the surface | 0 off / 0 inside | ok |
| coverage | 251 rows, 0 MISSING, 0 UNSUPPORTED, 15 dispositioned | ok |
| pit lane | 6 rows | ok |
| ground lines (now strict: `scenery.ground_lines`) | 107 findings, 107 dispositioned, 0 open | ok |
| kerb traversal | no roll > 15 deg | ok |

## 19. Identities re-proved (rev 748b55ca59)

- Published track.json d19cfb7823695525, heightfield.bin eb74f48192e28e3c, ghosts.json 9124c3d34baffcfd: `cmp`-identical
  to round 5 (`tools/track/out/mid_ohio_r5`).
- Sonoma: stage 3 rebuilt from its published stage-1 files: scenery.json and far_heightfield.bin `cmp`-identical to
  `public/tracks/sonoma`.
- Laguna: stage 3 on the stage-1 reproduction: scenery.json, far_heightfield.bin, far_ortho.jpg, ortho.jpg identical to
  the b5343d7 builder's output.
- App: the structure soups of Sonoma, Laguna and Buttonwillow identical before / after the `self_lit` change (section 17).
- Buttonwillow's stage-3 byte identity: the orchestrator's (its captures are in another worktree).
- `git diff b5343d7 -- public/tracks/sonoma public/tracks/laguna_seca public/tracks/buttonwillow`: empty.

Registry: `mid_ohio.rev` 748b55ca59; the comment carries the kerb-height owner question.

Open after round 7b (replacing section 12's scan / audit / ground-lines / bleacher items): the scan's unplaced
candidates (section 14), B2's apron tone and B3's mirrored board backs (section 15), the 4.4 structure stills; the rest of
section 12 stands (field, AI, pit-lane survey, T4 run-off raise, kerb height as an owner question, OSM fence heights,
IndyCar B / C rows, Buttonwillow identity, the second judge's pass).
