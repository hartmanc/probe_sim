# Buttonwillow round 15: ledger (26 Oct 2026)

Branch `buttonwillow-r15` (from `buttonwillow-r14` fea4ac1), worktree `probe_sim-wt/buttonwillow-r14`. Nothing pushed,
deployed or merged. Package `public/tracks/buttonwillow`: rev **29f4afedba -> d65c062829**. Machine: on the charger
(100 %), load 2.5-23 (other agents), one heavy process of mine at a time, disk 19 GB free.

**STOPPED AT THE BOUND (self-play contacts rose).** Steps 1-3 are complete and published; step 4's stills and judge pass
were not done: the brief's bound says stop and report the alternatives when the AI's contacts or four-offs in the 2-lap
self-play rise above round 14's. Section 7 holds the numbers and the alternatives.

## Decisions applied (the owner, 26 Oct 2026)

1. Item 19 `outside_band`: the race edges on his red everywhere (no `kerb_inside`, no kerb-zone widening, no ramps); every
   kerb a band OUTSIDE the edge at its measured width (`scenery.kerb.inside=False`, Mid-Ohio's key); the track limit the
   kerb's outside (section 4).
2. Item 18 `measured_default`: track default profile = the T9 apex measurement (0.06 m, face 0.15 m, back 0.30 m); flat
   where a frame resolves flat (kerb table).
3. Cones: 3-6 per closed mouth at the onboard's spacing; the 23 single evidence cones and the onboard lines unchanged.
4. Paddock bands I / T / B2-B5 / U: paved for the physics, not drawn (`closed_roads[].draw=False` with `draw_src`).

## 1. Stage 1: the edges on his red

Stage 1 exit 0, every gate ok: owner edge 99.3-100 % within 0.25 m (max 0.347 m), owner reference 0.347 / 0.303 m, width
0.317 m, band 0.120 / 0.109 m; edge gate rms 0.050 m, max step 0.028 / 0.030 m; world continuity 0.0076 / 0.0073 m;
profile 0.017 m. Lap **4699.19 -> 4705.98 m** (OSM 4701 m: +0.1 %, inside the 1 % rule). Corners T1 R45.4, T2 22.7, T5
43.1, T9 32.3, T11 30.7 m.

**Adherence to his merged red** (`tools/track/compare/red_adherence.py`: each red point of merged.json to the package
edge of its side; + = the package edge outside his red; median / p90 / max |d| in m; "along kerb strips" = the strip's
stations +-3; mouths = within 12 m of a red-across line):

| side | set | round 14 (29f4afedba) | round 15 (d65c062829) |
|---|---|---|---|
| left | away from kerbs and mouths | 0.022 / 0.244 / 1.339 | 0.017 / 0.064 / 0.348 |
| left | along kerb strips | 0.914 / 1.252 / 1.411 | 0.024 / 0.085 / 0.234 |
| left | mouths | 0.025 / 0.187 / 0.767 | 0.022 / 0.115 / 0.580 |
| left | all | 0.031 / 0.936 / 1.411 | 0.019 / 0.069 / 0.580 |
| right | away from kerbs and mouths | 0.021 / 0.198 / 1.587 | 0.018 / 0.057 / 0.324 |
| right | along kerb strips | 0.865 / 1.327 / 1.590 | 0.020 / 0.067 / 0.228 |
| right | mouths | 0.028 / 0.393 / 1.304 | 0.023 / 0.137 / 0.747 |
| right | all | 0.030 / 0.919 / 1.590 | 0.019 / 0.064 / 0.747 |

Worst 10 places outside the mouths (round 15):

| side | s | ENU | d (m) | |
|---|---|---|---|---|
| left | 1306 | (427.5, -466.9) | -0.348 | |
| right | 4393 | (-299.6, -235.1) | -0.324 | |
| right | 1643 | (121.7, -370.0) | +0.273 | |
| left | 1860 | (-85.0, -376.6) | -0.269 | |
| left | 580 | (269.6, 69.1) | -0.262 | |
| left | 1195 | (488.3, -370.9) | -0.239 | |
| left | 1647 | (112.1, -376.0) | -0.234 | kerb |
| left | 616 | (286.2, 105.2) | -0.229 | |
| right | 1303 | (425.0, -456.4) | +0.228 | kerb |
| left | 4383 | (-293.6, -220.0) | -0.221 | kerb |

## 2. Stage 2: the racing line and the lap

Pure minimum-curvature line within the edges less 1 m (clearance 1.00 m). Against round 14's line (world positions):
median 0.39 / p90 0.95 / max 1.48 m over the lap; **at the kerb strips median 0.49 / p90 1.13 / max 1.48 m** (L3967-4018
1.48, R4024-4121 1.47, L284-323 1.42, R1015-1049 1.39, R583-612 1.29, R3881-3930 1.13 m). Autopilot (`drive.ts --alat 1.2
--learn 25 --bank`): **2:31.88 (round 14) -> 2:34.33** (the stage-2 candidate and the published package alike); corner
minimums T5 114.8 -> 109.8, T7 131.4 -> 127.6, T10 125.2 -> 117.5 km/h. (`drive.ts` did not parse: two identifiers the
history rewrite split, fixed in 2afd376.)

## 3. Stage 3

**Kerbs** (39 strips, every one a band from the edge outward; `off` = +width / 2):

| run | side | s (package m) | width (m) | band beyond the edge (m) | profile | profile source |
|---|---|---|---|---|---|---|
| left s 283-322 | L | 283.9-323.9 | 0.95 | 0 .. 0.95 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 536-549 | L | 522.8-550.8 | 0.90 | 0 .. 0.90 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 745-767 | L | 745.7-767.7 | 1.05 | 0 .. 1.05 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 954-1011 | L | 955.6-1012.6 | 0.90 | 0 .. 0.90 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 1089-1116 | L | 1090.5-1120.5 | 0.90 | 0 .. 0.90 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 1203-1272 | L | 1205.5-1275.5 | 0.75 | 0 .. 0.75 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 1338-1396 | L | 1340.4-1398.4 | 0.70 | 0 .. 0.70 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 1449-1479 | L | 1435.4-1481.4 | 0.65 | 0 .. 0.65 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 1541-1574 | L | 1543.3-1577.3 | 1.15 | 0 .. 1.15 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 1653-1680 | L | 1648.3-1681.3 | 0.90 | 0 .. 0.90 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 1843-1851 | L | 1836.2-1855.2 | 0.65 | 0 .. 0.65 | flat paint | flat (round 14: Dog Leg separation blocks) |
| left s 2539-2544 | L | 2527.9-2545.9 | 0.90 | 0 .. 0.90 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 2689-2746 | L | 2677.9-2747.8 | 0.55 | 0 .. 0.55 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 3005-3013 | L | 3006.7-3014.7 | 1.10 | 0 .. 1.10 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 3340-3383 | L | 3341.6-3384.5 | 1.25 | 0 .. 1.25 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 3470-3518 | L | 3473.5-3520.5 | 0.90 | 0 .. 0.90 | flat paint | flat: t116 face <= 0.02 m |
| left s 3691-3760 | L | 3693.4-3761.4 | 0.90 | 0 .. 0.90 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 3845-3876 | L | 3835.4-3876.3 | 0.95 | 0 .. 0.95 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 3972-4024 | L | 3973.3-4024.3 | 1.00 | 0 .. 1.00 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| left s 4381-4406 | L | 4381.1-4408.1 | 1.05 | 0 .. 1.05 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 188-268 | R | 179.9-268.9 | 0.85 | 0 .. 0.85 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 360-376 | R | 361.8-411.8 | 0.70 | 0 .. 0.70 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 410-424 | R | 411.8-424.8 | 0.70 | 0 .. 0.70 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 584-604 | R | 583.7-612.7 | 0.60 | 0 .. 0.60 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 1020-1049 | R | 1016.6-1051.5 | 1.05 | 0 .. 1.05 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 1168-1191 | R | 1172.5-1194.5 | 0.90 | 0 .. 0.90 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 1304-1323 | R | 1285.4-1311.4 | 0.90 | 0 .. 0.90 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 1495-1515 | R | 1497.4-1517.3 | 0.40 | 0 .. 0.40 | flat paint | flat: t058 at 79 mph, flush (item 18) |
| right s 1779-1818 | R | 1781.2-1821.2 | 0.90 | 0 .. 0.90 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 1868-1933 | R | 1871.2-1960.2 | 0.70 | 0 .. 0.70 | flat paint | flat (round 14: Dog Leg separation blocks) |
| right s 2315-2340 | R | 2309-2343 | 0.50 | 0 .. 0.50 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 2765-2792 | R | 2766.8-2793.8 | 0.85 | 0 .. 0.85 | flat paint | flat: t094 no face vs t114 (found by the crest case) |
| right s 3400-3451 | R | 3401.5-3452.5 | 0.90 | 0 .. 0.90 | raised 0.06 m / face 0.15 | measured 6 cm: t114 horizon ratio |
| right s 3680-3690 (Sweeper | R | 3684.4-3694.4 | 0.40 | 0 .. 0.40 | flat paint | flat (round 14: t123, no face) |
| right s 3794-3810 | R | 3776.4-3811.4 | 0.70 | 0 .. 0.70 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 3894-3935 | R | 3886.3-3935.3 | 0.55 | 0 .. 0.55 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 4030-4127 | R | 4030.3-4127.2 | 0.70 | 0 .. 0.70 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 4321-4370 | R | 4321.1-4370.1 | 1.15 | 0 .. 1.15 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |
| right s 4424-4501 | R | 4426.1-4503.1 | 0.95 | 0 .. 0.95 | raised 0.06 m / face 0.15 | default: measured T9 6 cm (no resolving frame) |

Extents: round 13 / 14's `extent` values and his kerb drawing page stay the source. They were metres along rev 29f4afedba
and the lap grew 6.8 m, so they are mapped by world position (`scenery.metres_ref`, `trackcfg.remap_metres`, the round-14
centre frozen in `tracks/buttonwillow/metres_ref_r14.json`; the same for `runoff_zones` s and the C lane band's metres).
Identity proven: mapping rev 29f4afedba's own centre returns every value unchanged ((4659, 4680), (26, 43), (4458, 4580),
...). Without it mouths A and C fell 6.7 m short of his outlines (596 unpaved samples in the paved-coverage gate).

**Cones** (`owner_mouth_cones.count=(3, 6)`: cones end to end across his red at round(width / spacing) + 1 clamped to 3-6;
spacing 6 m from the Dog Leg crossover line, onboard t066-t068; the Sweeper mouth its own 8 m, t108-t110; mouths no frame
covers take 6 m; the spacing set on the stored line so the last cone stands on the end). **168 cones on 36 lines -> 95 on
36** (the eight mouths 113 -> 40). Per line, before (rev 29f4afedba) / after (d65c062829), cones @ spacing:

| s (package) | before | after | evidence |
|---|---|---|---|
| 637 | 10 @ 2 m | 4 @ 6.29 m | owner round-10 mouth left 634-636 (kink): cones on his red, drawn on the outline window over c2 |
| 721 | 22 @ 2 m | 6 @ 8.46 m | owner round-10 mouth left 693-734 (red across): cones on his red, drawn on the outline window o |
| 1513 | 12 @ 2 m | 5 @ 5.63 m | owner round-10 mouth left 1494-1514 (red across): cones on his red, drawn on the outline window |
| 1987 | 17 @ 2 m | 6 @ 6.66 m | owner round-10 mouth left 1960-1993 (red across): cones on his red, drawn on the outline window |
| 171 | 16 @ 2 m | 6 @ 6.36 m | owner round-10 mouth right 154-186 (red across): cones on his red, drawn on the outline window  |
| 1668 | 19 @ 2 m | 6 @ 7.25 m | owner round-10 mouth right 1643-1677 (red across): cones on his red, drawn on the outline windo |
| 3238 | 12 @ 2 m | 4 @ 7.99 m | owner round-10 mouth right 3216-3240 (red across): cones on his red, drawn on the outline windo |
| 4671 | 5 @ 2 m | 3 @ 4.99 m | owner round-10 mouth right 4659-4669 (red across): cones on his red, drawn on the outline windo |
| 41 | 1 @ 4 m | 1 @ 4 m | onboard t006 at full resolution (round 8, owner lap 2 note 24): four cones (yellow, white, oran |
| 46 | 1 @ 4 m | 1 @ 4 m | onboard t006 at full resolution (round 8, owner lap 2 note 24): four cones (yellow, white, oran |
| 51 | 1 @ 4 m | 1 @ 4 m | onboard t006 at full resolution (round 8, owner lap 2 note 24): four cones (yellow, white, oran |
| 56 | 1 @ 4 m | 1 @ 4 m | onboard t006 at full resolution (round 8, owner lap 2 note 24): four cones (yellow, white, oran |
| 1915 | 1 @ 4 m | 1 @ 4 m | compare_sheets onboard s1900 (t 70.76): an orange cone beside the end of the right kerb (judge  |
| 3200 | 1 @ 4 m | 1 @ 4 m | compare_sheets onboard s3200 (t 107.15): an orange cone at the right edge (judge r3 fwd_10 3200 |
| 900 | 2 @ 5 m | 2 @ 5 m | onboard t036 (judge r2, fwd_02 / fwd_03): orange cones on the left |
| 1805 | 9 @ 6 m | 9 @ 6 m | onboard t066-t068 (judge r2, fwd_06): a long line of cones separating the adjacent pavement (th |
| 3275 | 7 @ 8 m | 7 @ 8 m | onboard t108-t110 (judge r2, fwd_10 / fwd_11): orange cones along the left |
| 3650 | 2 @ 5 m | 2 @ 5 m | onboard t122 (judge r2, fwd_12): orange cones on the right |
| 4633 | 6 @ 10 m | 6 @ 10 m | pit-lane video t1267000 (21:07): six small orange cones along the left (paddock-side) wall ahea |
| 4690 | 1 @ 4 m | 1 @ 4 m | pit-lane video t1312000 / t1339000: the fluorescent yellow-green cone at the tower foot (judge  |
| 4694 | 1 @ 4 m | 1 @ 4 m | pit-lane video t1312000 / t1339000: the orange cone beside it at the tower foot |
| 762 | 5 @ 4 m | 5 @ 4 m | onboard t030 / compare_sheets s0700, s0750 (fwd_02, side_02): a line of small orange cones on t |
| 3200 | 1 @ 4 m | 1 @ 4 m | compare_sheets s3200 (fwd_10): orange cones at a mouth on the left; judge r5 fwd_10 3200 L: onb |
| 4050 | 2 @ 4 m | 2 @ 4 m | compare_sheets s4050 (fwd_13): cones on the right apron, 20 m before the t134 cone at s 4071 |
| 298 | 1 @ 4 m | 1 @ 4 m | onboard t012.jpg (orange; inventory s 297 right: single orange cone); position along the track  |
| 534 | 1 @ 4 m | 1 @ 4 m | onboard t022.jpg (orange; inventory s 533 left: single orange cone); position along the track f |
| 835 | 1 @ 4 m | 1 @ 4 m | onboard t034.jpg (orange; inventory s 834 left: single orange cone); position along the track f |
| 974 | 1 @ 4 m | 1 @ 4 m | onboard t038.jpg (orange; inventory s 973 left: single orange cone); position along the track f |
| 1041 | 1 @ 4 m | 1 @ 4 m | onboard t042.jpg (orange; inventory s 1040 right: single orange cone); position along the track |
| 1308 | 1 @ 4 m | 1 @ 4 m | onboard t052.jpg (orange; inventory s 1307 right: single orange cone); position along the track |
| 2159 | 1 @ 4 m | 1 @ 4 m | onboard t078.jpg (orange; inventory s 2158 right: single orange cone); position along the track |
| 2698 | 2 @ 4 m | 2 @ 4 m | onboard t092.jpg (orange; inventory s 2696 left: two orange cones); position along the track fr |
| 3440 | 1 @ 4 m | 1 @ 4 m | onboard t114.jpg (orange; inventory s 3439 right: single orange cone); position along the track |
| 4072 | 1 @ 4 m | 1 @ 4 m | onboard t134.jpg (orange; inventory s 4071 right: single orange cone); position along the track |
| 4576 | 1 @ 4 m | 1 @ 4 m | onboard t002.jpg (orange; inventory s 4575 right: single orange cone); position along the track |
| 4594 | 1 @ 4 m | 1 @ 4 m | onboard t150.jpg (orange; inventory s 4593 right: single orange cone); position along the track |

Coinciding lines: at the Dog Leg crossover the owner mouth right 1811-1835 has had cones off since round 11, so the
onboard t066-t068 line is the one line there (unchanged, 9 cones @ 6 m as the frames show). The onboard t030 apron line
(left 753-773) and the outer T2 loop mouth line (left 701-742) stand 11.7 m apart on different evidence: both kept (the
coordinator's ruling).

**Paddock**: the seven bands paved and off-course as before, `draw: false`; the paved-coverage gate checks them as
undrawn parts (`gates.paved_coverage.undrawn`; `pavedcoverage.test.ts` OPTS likewise): 12 parts, 139,065 samples, 0
unpaved. The pit-in still that proves the ortho's paddock shows was NOT shot (the bound, section 7).

**Inventory**: one logged correction (row t144 right kerb: `ahead_m` 15, s 4410.1 -> 4425.1; the run starts 18 m past
the old row on the longer lap). `inventory.py` was not re-run: it rewrote 75 rows and dropped 3 pit rows the committed
inventory carries; the row was corrected in place in observations.jsonl and inventory.json.

## 4. The track-limit rule (physics, opt-in)

Before: a band outside the edge was off the course (`onTrack` false, `paved` false), so with the edges on his red a car
on a kerb would have been off for lap validity, the black flag and the self-play four-off. Now `SurfaceSample.onKerbBand`
(`src/physics/track.ts`): with `kerbs.inside === false`, a point beyond the edge within a strip's band (raised or flat;
'verge' / 'blocks' excepted) on its stations. The track-limit tests count it as course: the app's `wheelOff`, the
scoreboard's `allOff` (lap validity and lost-in-the-hills), the race's four-wheels-off black flag, the self-play four-off
metric. Grip, height, `paved`, `onTrack` unchanged; the AI driver's own off-track recovery (`wheelsOff` by `onTrack`)
unchanged. Tests `src/physics/__tests__/kerbband.test.ts` (5): on the band, beyond its outer edge, past its ends, the
other side, a blocks line, a raised band, and inside kerbs (absent / true) identical in every field. CONTRACTS §4d.
Laguna and Sonoma: inside kerbs, never set. **Mid-Ohio inherits the rule at runtime** (its package carries
`kerbs.inside: false`); its files are untouched on this branch. Open: a FLAT outside band keeps the dirt grip blend over
its first metre (raised bands get paved grip on the hump); not changed (beyond the classification).

## 5. Kerb gate with the crest case

`kerbprobe.ts crestCases`: the player's car at the player's speed (the fastest ghost lap, else the onboard's overlay
speed, `compare/buttonwillow/inventory/overlay_speed.json`: 318 Catalyst readings of 7QS2M-HGSI4 OCR'd in round 13,
numbers only, force-added past the compare ignore rule) with its strip-side wheels 2 m past each raised strip's
track-side edge; no rollover, no roll past 15 deg. Existing cases unchanged.
- Buttonwillow: 117 line passes ok (48 with a lift, worst roll among them 7.0 deg); **33 crest passes, worst 11.4 deg**
  (L523-551 at 88 km/h; R1173-1195 11.3, R1285-1311 10.0). The first run ROLLED the Probe at T8 apex R2767-2794 at 105
  km/h (91.8 deg; 10.0 deg at 0.9 x the speed) with the 6 cm default: t094 read against t114 shows no face there, so
  the run is flat (item 18's "a frame resolves flat"). Laguna: 10 crest passes on its Optimal ghost lap, worst 8.9 deg.
  Sonoma: no ghost lap and no overlay speed: 0 crest cases (printed).

## 6. Gates, proofs, tests

Stage 3 `--publish --overwrite-package` exit 0, 0 [FAIL]. Gate CLIs on the package: `run_gates.ts` exit 0, `run_coverage.ts`
exit 0, `manifest_tables.ts` exit 0.

| gate | round 14 (29f4afedba) | round 15 (d65c062829) |
|---|---|---|
| edge rms / step, world continuity, profile | ok 0.066 / 0.066; 0.0076 / 0.0073; 0.017 | ok 0.050 / 0.030; 0.0076 / 0.0073; 0.017 |
| owner reference / width / band | ok 0.381 / 0.328; 0.384; 0.136 / 0.120 | ok 0.347 / 0.303; 0.317; 0.120 / 0.109 |
| barrier gaps | ok 4.17 m / 17 runs | ok 4.16 m / 17 runs |
| containment | ok 0 escapes, 3295 allowed | ok 0 escapes, 3279 allowed, 73 junction |
| pit connectivity | ok 388 / 382 m | ok 387 / 381 m |
| signs, wall ends, tyre facings, wall tops, joins, tyre faces, run gaps | ok | ok |
| ground marks | ok 0 off | ok 0 off (3352 paint, 15148 edge-line vertices) |
| cones off the surface | ok 168 / 36 | ok 95 / 36, deepest 0.00 m |
| paved coverage | ok 12 parts 139,086; lane 77,779; outlines 10,227; 0 unpaved | ok 12 parts 139,065; lane 77,811; outlines 10,227; 0 unpaved |
| coverage, pit lane | ok MISSING 0, UNSUPPORTED 0; 7 rows | ok MISSING 0, UNSUPPORTED 0, 88 rows / 160 objects; 7 rows |
| kerb traversal (+ crest) | ok | ok (section 5) |

Identity: `git diff fea4ac1 -- public/tracks/sonoma public/tracks/laguna_seca public/tracks/mid_ohio` empty (no Mid-Ohio
package on this branch). **The stage-3 rebuild of Sonoma could not be done here**: this worktree has no Sonoma cache or
captures (OSM, DEM, lidar, the gitignored clean captures); the only copy is in the main checkout, which the brief puts
out of bounds. In its place: none of the new keys (`kerb.inside`, `owner_mouth_cones.count` / `cone_spacing`,
`closed_roads[].draw`, `paved_coverage.undrawn`, `scenery.metres_ref`) is in Sonoma's or Laguna's config, every new code
path is behind them, and `pytest tools/track` 136 passed, 3 skipped. TRACKS.buttonwillow rev d65c062829, `length_m`
4705.982. Tests: full `npx vitest run` **66 files, 549 passed** (no timeouts); `npm run build` clean (dist deleted).

## 7. Self-play (2 laps, the 100-car field, seeds 1-3) and the bound

| package | seed | AI-AI contacts (>3 m/s) | four-off (mishaps) | contact stations | four-off stations |
|---|---|---|---|---|---|
| round 14 | 1 | 0 (0) | 4 (2) | - | 3890, 1120, 1532, 3487 |
| round 14 | 2 | 3 (1) | 3 (0) | 4389, 1882, 3390 | 3912, 3944, 1728 |
| round 14 | 3 | 4 (2) | 4 (0) | 410, 3073, 1760, 519 | 426, 387, 555, 4636 |
| round 15 | 1 | **4 (2)** | 4 (2) | 3704, 567, 2534, 2536 | 3481, 392, 1539, 1537 |
| round 15 | 2 | 4 (1) | 1 (0) | 291, 1216, 1031, 1032 | 3526 |
| round 15 | 3 | 4 (2) | 2 (0) | 1551, 527, 3486, 527 | 570, 586 |

Seed 1 (the brief's 2-lap run): contacts 0 -> 4, four-off 4 -> 4. Three seeds: contacts 7 -> 12 (0.014 -> 0.025 per
car-lap), four-offs 11 -> 7. Line when alone rms 0.32 -> 0.28 m. Several round-15 contacts sit at narrowed kerb stretches
(527 / 567 T2 entry, 1031, 2534-2536, 3486). Contacts rose: **the bound is met; stopped**. Alternatives:
- (a) Accept and re-base the Buttonwillow self-play band with a dated note: the narrower course at the kerbs is the
  owner's geometry (SKILL stage 5: a narrowed exit moves the band, never a reason to widen the track); round 14 seed 3
  already had 4.
- (b) AI lane-model work (fix the AI, not the track): let the AI's line bounds and the alongside corridor use the
  outside kerb bands up to their outer edge (the track limit), so the usable width at the kerbs is what it was; stage 2's
  margins and the lane model read `kerbs.inside` false.
- (c) Tune the track's AI knobs (`TRACKS.buttonwillow.ai` laneMargin 0.7 / followScale 1.4) on 3+ seeds for the new
  geometry.

## 8. Not done (the bound)

Step 4: the compare stills from the published package (kerb runs at Sunset, T1, T2, T5, T9, T10; the mouths with their
cones; the pit-in split and the paddock), the judge pass with findings. The pose list is ready (`/tmp/bw15/scripts/poses.py`,
local).

## 9. Open items

1. The bound above (the owner's choice among a-c).
2. Flat outside bands keep the dirt grip blend over their first metre (physics, not changed).
3. T8 apex declared flat from t094 (a judgement of no face against t114); a 6 cm kerb there rolls the Probe at the
   player's 105 km/h when he is 2 m onto it.
4. The Dog Leg crossover's onboard line has 9 cones (the frames' extent), above "three to six"; left as evidence.
5. Sonoma stage-3 rebuild not run (no inputs in this worktree).
