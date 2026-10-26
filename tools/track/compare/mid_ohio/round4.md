# Mid-Ohio round 4: the owner's checkpoint answers applied, stage 0 built

Opus 5.5, 26 Oct 2026, branch `mid-ohio` (from 2a90e8a). Scope: the owner's answers of 26 Oct 2026 evening (length
gate, D5, T4, checkpoint accepted) applied to the geometry, then stage 0 from three videos: the 360 lap reader, the
inventory, time-to-station maps, heights, the speed-integrated lap. Not in this round: racing line, scenery, far
terrain, registry, field, AI, previews. Package `tools/track/out/mid_ohio_r4/` (local; every geometry check passes
without `--write-on-fail`).

## 1. Applied decisions

| # | owner's answer | applied as | record |
|---|---|---|---|
| 1 | Length gate: the Buttonwillow rule | `loop_check.official_m = None`; the published 2.258 mi (3633.934 m) kept in the config comment as information; new opt-in gate `loop_check.osm_tol = 0.01` (built centre vs the raw stitched OSM loop of `loop_ways`; absent on every other track); the speed-integrated lap as the second independent measure (section 6) | config, `build_track.py`, `trackcfg.py` |
| 2 | D5 stands | no geometry change (round 3 applied it provisionally); marked approved | `round3.md` D5 row, config comment |
| 3 | T4 bank-halving rule, flagged | opt-in `profile_bank` rule (section 2) | `profile_bank.py`, `test_profile_bank.py`, config |
| 4 | Checkpoint accepted, no red marks; green marks maybe later | recorded; the round-2 green strokes stay the paved-boundary evidence for scenery | `round3.md` "Owner's answers" |

`round3.md`'s commit references were updated to the rewritten history (603a90c, bb27b86, f659250, 0993678, 8eab1bd; round
3 b4ddf70, bf1a458, 0db0524, 2a90e8a).

## 2. T4: the bank-halving rule (FLAGGED: every element is an assumption)

Rule (`tools/track/profile_bank.py`, config `profile_bank`): at each station the measured chord bank toward the inside
(right) g is scaled about the inside edge, z'(l) = z(l) - (1 - 0.5) w(s) max(g, 0) d(l), d the distance from the inside
edge; the crown (the section's shape about its chord) is kept; w = 1 over 520 ft (158.496 m) centred on the measured
2019 bank peak, a smoothstep over the 400 ft (121.92 m) before it, no exit taper. The peak is measured (largest
5-station chord bank within 40 m of the config's T4 anchor), not declared. The heightfield carries the same change under
the road, holds the outside edge's change 2 m beyond it and fades it over 6 m; inside edge and everything outside the
interval untouched. It runs only when `profile_bank` is in the config.

Result (build log, `geometry_report_r4.json`): peak station 1968, bank 4.38 -> 2.20 deg; interval stations 1767..2047
(core 1889..2047); profile changed at stations 1864..2005 only (the bank toward the inside is zero before 1864 and after
2005: the adverse T5-approach slope, -1.6 deg at 2040, is left as measured); outside edge down 0.460 m at most, centre
down 0.229 m at most, inside edge unchanged (0.000 m); largest station-to-station change of the delta 0.018 m (the
measured bank's own rate at s ~1985-1995; the rule refuses > 0.02 m, which would mean a missing blend).

Assumptions (round 3's table, all kept as assumptions):

| assumption | status after round 4 |
|---|---|
| the rebuilt 158.5 m lies symmetric about the 2019 bank peak | supported in position by the 2025 360 lap (below), not measured |
| the inside edge keeps its 2019 elevation | assumed ("footprint and apex curbing kept"); apex kerb present in 2025 |
| the chord bank toward the inside halved everywhere in the interval | assumed (4 -> 2 deg is the peak ratio) |
| the outside edge drops by the rotation (excavation = lowering) | assumed; 0.46 m against "up to 18 inches" (0.457 m) |
| smoothstep over the 400 ft regraded approach; no exit taper | assumed (approach bank toward the inside is 0 until s ~1864) |
| crown and the inside edge's longitudinal profile unchanged | assumed |
| run-off: the outside change held 2 m, faded over 6 m to the 2019 ground | assumed (the operator's raise has no numbers; not measurable from the videos) |

Placement evidence (`r4/t4_placement.json`; frames local under `tools/track/cache/mid_ohio/video/t4fine/` and
`inventory/frames_360_half/`): in the 2025 360 lap's ahead views (pitched down, 0.3-0.5 s) a transverse joint to darker,
fresher asphalt appears just past the "100" board (crossed at t 74.0, s ~1898) and a joint back to lighter grey beside the
T4-exit yellow kerb (crossed at t 79.4, s ~2033): new surface over about 135 m centred on s ~1965. The rule's core is
1889..2047 centred on 1968: 9 m before the observed entry joint and 14 m past the exit joint, inside the 360 time map's
±20 m. The IndyCar segments through T4 (A 44.5-49, B 112-117.5, C 178.5-183 s) show the same dark surface from the braking
zone and lighter grey beyond the exit kerb; their joints are not resolvable better than ~20 m. The red/white apex kerb is
in place in 2025 (t 76.5). Run-off: grass then sand/gravel on the outside; its height against the road is not measurable
from the roof camera. No video measures the bank angle (a hood or roof camera cannot separate bank from roll).

## 3. Gate table (round 4 geometry, `--stage geometry --out tools/track/out/mid_ohio_r4`, exit 0)

| gate | value | limit | result |
|---|---|---|---|
| owner edge left 3425-576 | 99.6 % within 0.25 m, max 0.356 m | >= 90 %, <= 0.5 m | ok |
| owner edge right 3425-576 | 100.0 %, max 0.154 m | same | ok |
| fit left: observations / coverage / gap / waviness / kink | 97.9 % / 88 % / 31 st / 0.019 (peak 0.040) m / 0.11 deg | 90 % / 60 % / 60 / 0.04 (0.1) / 0.5 | ok |
| fit right | 98.7 % / 92 % / 30 st / 0.025 (0.075) m / 0.22 deg | same | ok |
| painted-midpoint residual | rms 0.03 m | | ok |
| loop stations | 3595 | 3500-3750 | ok |
| lap length vs OSM loop (new) | 3597.49 vs 3620.22 m, -0.63 % | 1 % | ok |
| lap length vs the published figure | not a gate (official_m None); -1.003 % against 3633.934 m, information | | n/a |
| elevation range | 41.6 m | 0-100 | ok |
| direction / start-finish | cw / 0.16 m from the timing line | / 5 m | ok |
| edge jumps | 0.083 / 0.084 m | 0.10 | ok |
| cross slope inner / edge thirds | 11.6 % / 11.4 % | | ok |
| no NaN | | | ok |
| edge gate left / right (build and `edge_gate.py`) | rms 0.023 / 0.023 m, step 0.023 / 0.020 m | 0.10 | ok |
| world continuity left / right | 0.0050 / 0.0073 m | 0.02 | ok |
| profile gate | 0.021 m | 0.10 | ok |

Advisory (unchanged from rounds 2-3): T1 exit overshoot +2.19 m at station 392. Tests: every `test_*.py` under
`tools/track` 134 passed (125 + 4 `test_profile_bank.py` + 4 `test_equirect.py` + 1 new inventory test);
`inventory/test_inventory.py` unittest OK; `test_edge_mark_transfer.cjs` 4 passed.

**Held course (round 4 vs round 3, `r4/held_check.py`)**: n, spacing, length, z0, corners, frame boxes, origin identical;
every centre / left / right plan position identical (max 0.0000 m). Profile: 142 stations differ, 1864..2005, all inside
the rule's interval 1767..2047; outside it 0.0000 m. Stored centre z max change 0.229 m, left 0.460 m, right 0.
Heightfield: 756 of 472896 cells differ (-0.460..0.000 m), ENU extent x -240..-132 m, y 292..392 m, nearest centre
stations 1863..2006; 0 changed cells outside the interval. Package sha256: track.json d19cfb78..., heightfield.bin
eb74f481... (round 3: 738ba625..., f8d5993b...).

**Shared code (byte identity)**: `build_track.py` runs the two new blocks only when the config has `profile_bank` /
`loop_check.osm_tol`. Sonoma stage-1 reproduction (`--out tools/track/out/sonoma_repro_r4`, exit 0, 1019 s):
track.json and heightfield.bin byte-identical to `public/tracks/sonoma` (`cmp`). Laguna reproduction: NOT obtained:
the run stops in the provisional racing line (`tools/ghosts/build_ghosts.py` on the logger laps raises "argmin of an
empty sequence" in pandas) before any round-4 code is reached; pre-existing in this environment, not investigated
further this round (open item). `inventory.py`'s new `extra_maps` key: Sonoma and Buttonwillow inventory outputs from
the new and HEAD versions compared byte-identical (`cmp`).

## 4. Stage 0: sources (licences)

| source | what | date | used for | licence |
|---|---|---|---|---|
| e25u_vjn1uM (NTT INDYCAR SERIES) | 360 deg roof camera on the Honda pace car, one lap (S/F 0:24.0 -> 2:11.1, 107.1 s) plus lead-in and T1 | 4 Jul 2025 | both sides every 2 s, 0.5 s landmarks, T4 joints, heights | Standard YouTube; downloaded (format 313, 3840x2048 equirect, + audio 251-7) into `tools/track/cache/mid_ohio/video/` (ignored, never executed); video file deleted after extraction, audio and frames kept (117 MB) |
| OJaBJz18xEo (N837 Motorsport) | Lemons hood camera with Garmin Catalyst overlay, lap 149 (2:04.84) | 15 Apr 2026 | primary time map (lap-time readout + GPS dots), 2 s rows, speed-integrated lap | Standard YouTube; headless frames (`headless_capture.ts`), 1 s, 0-135 s |
| 9Drr1VkE1_U (Andretti) | IndyCar Practice 1 compilation: segment A 0-68.5 s (yellow car, P1), B 69-134.5 s (blue, P2; cut before the PERMCO bridge), C 135.5-201 s (teal, P8); each from Thunder Valley | 3 Jul 2026 | three segment time maps, 2 s rows, T4 surface | Standard YouTube; headless frames, 2 s and 0.5 s |
| x5Fk-R-e_Zc (INDYCAR On FOX) | 2026 Honda Indy 200 in-car broadcast, 2.6 h | 5 Jul 2026 | pit-lane candidate: NOT surveyed (a 60 s scan stalled on black frames; pre-race segments of another event) | Standard YouTube |
| Google Street View | coverage only on public and paddock / parking roads; none on the circuit or the pit lane | | `streetview.md` | reference only |

No 2024+ video driving the Mid-Ohio pit lane was found (web search, 26 Oct 2026). The pit rows (13, `pit.jsonl`) are the
pit wall and pit exit seen from the track in the 360 lap.

## 5. Time-to-station maps (`inventory/source.json`; leave-one-out residual m, profile interpolation)

N837 (primary; S/F from the Catalyst lap-time readout: t - lap time = 5.03 s, and 129.87 s where the completed lap reads
2:04.84; corner anchors from the Catalyst GPS dots, r4/dots_n837.json, bracket checked in the 1 s frames): footbridge
-14.4, T1 +9.9, T2 -11.2, T3 +2.2, T5 -14.8, T7 -0.7, T9 +7.7, PERMCO bridge +13.7, T10 -8.9, T12 -12.3, T13 -4.0
(max 14.8 m). T4 is not an anchor (t061 stale twice, t062-t065 player overlay).

360 lap (lead-in from the Carousel at 15.0 s, s from 3351.3 across S/F into lap 2): S/F +17.9, footbridge -16.9, T2 +20.4,
T4 -7.0, T5 -8.2, PERMCO bridge +19.6, T12 (lap 2) +1.8 (max 20.4 m).

IndyCar (lead-in from the Carousel kerb in the 2 s frames, +-1 s): A: S/F +13.1, footbridge -4.9, T2 +12.1, T4 -22.4;
B: S/F +60.1, footbridge -11.7, T2 +34.3; C: S/F +44.3, footbridge -26.1, T2 +38.2, T4 -55.1. B's and C's S/F residuals
come from the 2 s lead-in anchor; C between T2 and T4 is the weakest stretch (no back-straight landmark): rows there are
confidence 0.7 and are covered by the 360 lap and N837 anyway.

Corrections (`source.json corrections`): the T1 kerb anchors of the 360 lap and the IndyCar segments dropped (the T1
inside kerb runs s 285-360; "alongside" is not the curvature peak: implied 45, 80, 95 m/s); N837 T4 not used.

## 6. Speed-integrated lap (second independent length measure)

`inventory/catalyst_speed.py`: template OCR of the Catalyst speed digits (templates from 15 frames read by eye; all
123 readings then checked by eye on a contact sheet: correct; touching "71" split), trapezoid in video time between the
two S/F crossings of the lap-time readout (5.03 -> 129.87 s), t061 missing (interpolated 91 -> 62 mph in the T4 braking
zone). Output `r4/speed_lap_n837.json`.

| measure | length (m) | vs built centre |
|---|---|---|
| speed-integrated lap, N837 lap 149 (driven line) | **3558.9** (every other sample 3561.9 / 3555.5; display quantisation bound +-27.9) | -1.07 % |
| built centre (round 4) | 3597.5 | |
| raw OSM loop | 3620.2 | +0.63 % |
| published 2.258 mi (information) | 3633.9 | +1.01 % |

Consistency check: over 10-120 s the integrated distance is 0.9 % shorter than the GPS dots' advance on the centre
(3138 vs 3167 m), the same order as the whole lap (the dots are fitted to the centre, so this is a check, not a third
measure). A driven line runs about 1 % inside a centreline (Buttonwillow: 4650 m driven vs 4701 m OSM); the measure
agrees with the built centre and OSM, and would need a 2.1 % driven-line deficit to match the published figure.

## 7. Inventory summary (`inventory.json`, `inventory.md`)

380 rows (lap 367, pit 13): wall 111, kerb 80, runoff 65, fence 38, boards 25, stand 13, bridge 11, building 9, sign 9,
paint 7, station 5, tower 4, mast 2, cone_line 1. By video: 360 lap 196 (+ the 13 pit rows, placed by s from its time map), N837 105, IndyCar A 26, B 19, C 21.
The 360 lap gives both sides at 2 s from S/F to S/F; the hood cams add what they see (kerbs, bridges, boards, the
2026 cones). Coverage: 63 of 72 50-m bins on the left and 64 of 72 on the right hold a row (gaps: left bins 2, 33, 43,
50, 56, 58, 63, 65, 70; right 6, 16, 21, 29, 31, 33, 56, 65). No tyre wall or tyre stack was seen in any video (the
red stacked W-beam armco is the common barrier). Heights: 75 rows carry one (`r4/heights.json`): camera 1.7 m (pace car
roof + mount, roof-edge check), horizon-ratio pit wall 0.7 m (0.64-0.75), armco 1.0 m (two readings 0.8 and 1.3 m:
+-0.3 m), catch fence 3.5 m (fence-post-ref, 3.0-4.5), starter tower 13 m, pit garages 4 m, covered grandstand 7 m
(storeys); 0 rows marked unmeasured; bridges, pylon, bleachers and boards carry no height (scenery stage with lidar).

Paved extras (owner's round-2 green strokes): the unused chicane and the T1-T3 connector are grey asphalt, a touch
lighter than the racing surface (360 t40, t42, t64); the pit-exit apron at T1 is the track's asphalt with white hatched
blend lines (360 t32, N837 t14). A measured tone (capture RGB inside the green outlines) is left to the scenery stage.

## 8. Deferred (recorded so nothing is lost)

- Field: Lemons 2026 "Mid-West Crisis" results, https://24hoursoflemons.com/results-2/?id=439 (+ the owner's #619).
- Racing line (stage 2; no logger: line only, validated against N837's Catalyst speed trace, now read: `r4/speed_lap_n837.json`).
- Scenery: the inventory above, the green strokes, the pit wall (0.7 m, 3496 -> 216), the pit-exit hatch, the two
  footbridges, the T4 run-off. The pit lane itself has no 2024+ video survey (candidate x5Fk-R-e_Zc).
- Laguna stage-1 reproduction (blocked by the ghost builder error above); Astra review of this round.
- Owner's green marks on the round-3 page, if he makes them.

## 9. Stage ledger (round 4)

| step | record |
|---|---|
| 0.1 loop | unchanged (6 config ways, owner's clarified loop) |
| 0.2 sources | table above; sources.json `inventory_r4`, `pit_lane_video`, `streetview` |
| 0.3 clean captures | unchanged (round 1) |
| 0.4 recent video | N837 2026, IndyCar 2026, 360 2025; pit-lane video: none found |
| 0.5 Street View | coverage checked: paddock roads only; not surveyed (`streetview.md`) |
| 0.6 2 s steps | 360 S/F -> S/F both sides; N837 0-130 s; IndyCar segments inside their anchors |
| 0.7 time maps | four maps (N837 primary + three extra maps for 360 / IndyCar A-C as `extra_maps`), residuals above |
| 0.8 pit / Street View rows | `pit.jsonl` 13 rows (from the track) |
| 0.9 heights | `r4/heights.json`, methods cited per row |
| 0.10 validate | `inventory.py --track mid_ohio --pkg tools/track/out/mid_ohio_r4`: 0 errors |
| 1.x geometry | round 4 gates above; T4 `profile_bank`; length by the Buttonwillow rule + OSM gate |
