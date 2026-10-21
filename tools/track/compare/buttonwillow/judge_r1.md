# Buttonwillow judge round r1 (20 Oct 2026)

Judge: **the orchestrator (Claude)**, with the JUDGE.md prompt and checklist; GPT 6 Astra was unavailable (the codex
server did not connect all day). Package: branch buttonwillow 8dd346e, rev 109a9acd5a. Sheets: `compare_sheets/`, 46
(16 forward, 12 side, 8 back, 6 pit, 4 runoff), read at 1700 px. Known and already in work (the stage-1 exits pass):
the T1 exit (355-432), T10 (3700-3757) and T11 exit (4402-4445) sit on the apron side of their block lines; rows for
them are listed once and marked `stage 1`.

## Rows

| sheet | s (m) | side | kind | onboard shows | sim shows | verdict |
|---|---|---|---|---|---|---|
| fwd_15, side_11, pit_02, back_00 | 4600-4695, 0-20 | left | building | the control tower: a 2-storey white building with a blue flat roof on posts, a blue canopy tent beside it, ~8 m | a 3-4 storey grey block with rows of windows, ~14 m, plus a separate white canopy | WRONG_TYPE / WRONG_HEIGHT / WRONG_COLOUR |
| side_10, side_11, back_00, back_07, fwd_00 | 4514-4695, 0-150 | left | wall | the pit-wall K-rail (white concrete, 0.81 m, red/white ends, a black section near 101) along the whole straight from the T11 exit | nothing visible at 70 deg or looking back; a faint low line on some forward stills | WRONG_HEIGHT or MISSING (confirm the run stands at 0.81 m, white, from 4514) |
| fwd_01, side_01 | 355-432 | right | kerb | block line on the car's right, converging ahead | kerb on the left, track on the apron | WRONG_POSITION (stage 1) |
| fwd_12, side_08 | 3700-3757 | left | kerb | long block line on the left | none on the left | WRONG_POSITION (stage 1) |
| fwd_14, side_10 | 4402-4475 | right | kerb | long rwb kerb on the right through the T11 exit | none | WRONG_POSITION (stage 1) |
| fwd_04 | 1200 | left | kerb | rwb kerb on the left (T4 exit) | a kerb on the right ahead, none on the left | WRONG_POSITION |
| side_04 | 1348 | left | kerb | long rwb block line on the left | none | MISSING (the 1318-1392 zone) |
| fwd_06, side_05 | 1878-1900 | right | kerb | long white block line on the right | none | MISSING |
| fwd_11, side_07 | 3329-3350 | left | kerb | rwb kerb on the left (Star Mazda entry) | none on the left; a kerb on the right ahead | MISSING |
| side_09 | 4122 | right | kerb | rwb kerb on the right | none | MISSING |
| fwd_14, side_09 | 4300-4308 | right | kerb | block line on the right (T11 approach) | a kerb on the left ahead, none right | WRONG_POSITION |
| side_01 | 297 | right | cone_line | one orange cone | none | MISSING |
| fwd_02 | 700 | left | cone_line | three or four orange cones on the pale apron | none | MISSING |
| fwd_02, side_02 | 750-770 | left | cone_line | a line of small cones | none | MISSING |
| fwd_02, side_02 | 834-850 | left | cone_line | one orange cone | none | MISSING |
| fwd_03, side_02 | 950-974 | left | cone_line | one orange cone by the kerb | none | MISSING |
| fwd_03, side_03 | 1040-1050 | right | cone_line | one orange cone | none | MISSING |
| side_06 | 2150-2160 | right | cone_line | one orange cone | none | MISSING |
| fwd_09 | 2700 | left | cone_line | two orange cones by the kerb | none (a cone shows at 2695 on side_06) | OK_DIFFERENT if the 2695 cone is this one; else MISSING |
| fwd_10 | 3200 | left | cone_line | three orange cones at a mouth on the left | none | MISSING |
| fwd_11, side_07 | 3438-3450 | right | cone_line | one orange cone by the station | none | MISSING |
| fwd_13 | 4050 | right | cone_line | cones on the right apron | none (one shows at 4065 on side_09) | OK_DIFFERENT if the same; else MISSING |
| fwd_15, side_10 | 4600 | right | cone_line | cones on the right | one cone at 4575-4593 | OK_DIFFERENT |
| side_00 | 246 | left | station | canopy on posts over a low concrete platform (T1) | nothing on the left | MISSING or WRONG_POSITION |
| fwd_01 | 450-500 | right | station | a structure left of centre ahead at 450; the inventory row is right at 500 | a blue/white hut right of the road | check the side against the onboard at 0:19-0:21 |
| fwd_07 | 2350 | right | station | a hut far right | nothing seen | MISSING or too small to see |
| side_08 | 3758 | right | station | corner station | nothing on the right | MISSING or WRONG_POSITION |
| side_03 | 996 | right | tyre_wall | the hut stands on a tyre-walled mound | hut on flat ground, no tyres | MISSING |
| side_04 | 1525 | right | tyre_wall | tyre-walled mound under the station | none | MISSING |
| side_06 | 2054 | right | tyre_wall | tyre-walled mound under the station | hut, no tyres | MISSING |
| side_09 | 4273 | left | tyre_wall | tyre-walled mound under the station | hut, no tyres | MISSING |
| pit_00..05 | pit lane | both | pit lane | (no frames) | the lane, its separation wall from 4503, the grey block at 4644-4669, the merge at 440-490 with a painted line | pit sheets carry no pit-lane frames: stage 4.2 incomplete, C9 and C10 not judged |
| fwd_12, back_06 | 3650-3750 | left | trees | a row of tall trees along the left | a few scattered trees | OK_DIFFERENT (data-derived trees) |

## Per sheet

- fwd_00: 2 rows (tower, K-rail), worst: the K-rail not visible. C1 ok, C2 ok, C3 n/a, C4 FINDING, C5 FINDING, C6 ok, C7 ok, C8 ok, C9 n/a, C10 n/a, C11 ok, C12 n/a, C13 ok, C14 n/a, C15 n/a, C16 n/a, C17 ok, C18 ok, C19 n/a, C20 FINDING, C21 ok.
- fwd_01: 3 rows (T1 exit kerb, station side, cone 297), worst: the T1 exit on the apron. C1-C7 ok/n/a, C8 FINDING, C9 n/a, C10 ok, C11 FINDING, C12 n/a, C13 FINDING, C14-C16 n/a, C17 ok, C18 ok, C19 n/a, C20 n/a, C21 ok.
- fwd_02: 3 rows (cones 700, 750-770, 834-850), worst: the apron cones. C8 FINDING, C11 ok, C13 ok, C18 ok, rest ok/n/a.
- fwd_03: 2 rows (cones 950, 1050), C8 FINDING, C11 ok, C13 ok, rest ok/n/a.
- fwd_04: 2 rows (kerb 1200 L, cone 1300 R seen on side_04 as OK), C11 FINDING, rest ok/n/a.
- fwd_05: 0 rows. all ok/n/a.
- fwd_06: 1 row (kerb 1900 R), C11 FINDING, rest ok/n/a.
- fwd_07: 2 rows (cone 2150, station 2350), C8 FINDING, C13 FINDING, rest ok/n/a.
- fwd_08: 0 rows.
- fwd_09: 1 row (cones 2700, likely the 2695 cone), rest ok.
- fwd_10: 1 row (cones 3200), C8 FINDING.
- fwd_11: 2 rows (kerb 3350 L, cone 3450), C8 FINDING, C11 FINDING.
- fwd_12: 2 rows (T10 kerb, trees), C11 FINDING (stage 1).
- fwd_13: 1 row (cones 4050), C8 FINDING.
- fwd_14: 2 rows (kerb 4300 R, T11 exit kerb), C11 FINDING.
- fwd_15: 3 rows (tower, K-rail, cones 4600), C4 FINDING, C5 FINDING, C20 FINDING.
- side_00: 3 rows (tower at 20 L, K-rail 101 L, station 246 L), C4 FINDING, C5 FINDING, C13 FINDING, C20 FINDING.
- side_01: 2 rows (cone 297, T1 exit kerb 410), C8 FINDING, C11 FINDING; the 477 R station with its tyre mound is OK (C3 ok, C13 ok).
- side_02: 3 rows (cones 770, 834, 974), C8 FINDING.
- side_03: 2 rows (tyre mound 996, cone 1040), C3 FINDING, C8 FINDING.
- side_04: 2 rows (kerb 1348, tyre mound 1525), C3 FINDING, C11 FINDING.
- side_05: 1 row (kerb 1878 R), C11 FINDING.
- side_06: 2 rows (tyre mound 2054, cone 2160), C3 FINDING, C8 FINDING.
- side_07: 2 rows (kerb 3329, cone 3438), C8 FINDING, C11 FINDING.
- side_08: 2 rows (T10 kerb, station 3758), C11 FINDING (stage 1), C13 FINDING.
- side_09: 3 rows (kerb 4122, tyre mound 4273, kerb 4308), C3 FINDING, C11 FINDING.
- side_10: 3 rows (T11 exit kerbs 4417/4475, K-rail 4514 and 4593), C4 FINDING, C5 FINDING, C11 FINDING (stage 1).
- side_11: 2 rows (K-rail 4609-4662, tower 4695), C4 FINDING, C5 FINDING, C20 FINDING.
- back_00..07: the geometry, kerbs and huts seen looking back agree with the forward findings; no new row. back_00 and back_07: C4/C5 FINDING (K-rail), C20 FINDING (tower); the others ok/n/a.
- pit_00..05: no onboard frames; C9 and C10 not judged. The separation wall shows from 4503; no rule boards in the lane (C9 partial ok).
- runoff_00..03: the paved runoffs read as pale pavement against the dark track, as the footage; C17 ok, C18 ok, C7 ok (0 escapes by the gate); the tower block shows from the crossover at 4644 (C20 FINDING, same row).

## Ten worst rows of the lap

1. The control tower at the line drawn as a 3-4 storey grey block with window rows; the real one is 2 storeys, white, blue flat roof on posts, with a blue canopy beside it (C20).
2. The T1 exit, T10 and T11 exit on the apron side of their block lines (stage 1, in work).
3. The pit-wall K-rail not visible along 4514-150 left on side and back sheets (C4, C5).
4. Ten cone places missing (297 R, 700 L, 750-770 L, 834-850 L, 950-974 L, 1040-1050 R, 2150 R, 3200 L, 3438 R, 4050 R) against 13 placed (C8).
5. Kerb block lines missing or on the wrong side at 1200 L, 1348 L, 1878-1900 R, 3329-3350 L, 4122 R, 4300-4308 R (C11).
6. The pit sheets carry no pit-lane frames, so the lane, its walls and the pit-out blend are unjudged against the footage (4.2, C9, C10).
7. Stations not visible at 246 L (T1), 2350 R (T7) and 3758 R (T10) (C13).
8. The tyre-walled mounds under the huts at 996 R, 1525 R, 2054 R and 4273 L not drawn; only the 477 R mound has its tyres (C3).
9. The T1-exit station side: the onboard at 0:19-0:21 shows the structure left of centre ahead; the package has it right at 500 (C13).
10. Widths under the operator minimum at T2 entry and T4 (stage 1 check in work).
