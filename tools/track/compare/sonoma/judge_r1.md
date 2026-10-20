# Sonoma judge round r1 (rederive run, 20 Oct 2026)

Judge: **the orchestrating agent itself** (JUDGE.md prompt and checklist). GPT 6 Astra was not used: the codex MCP server
failed to connect in this session. Sheets: `compare_sheets/` (local), 50 sheets (fwd 14, side 19, back 7, pit 6,
runoff 4) from `camera_walk.ts` on port 5182 and `make_compare_sheets.py`. Two passes: pass A on the first stage-3
package (findings fixed in config), pass B on the package committed with this file (every sheet re-read; the back, late
side, pit and runoff sheets as 2x2 montages).

## Pass A findings fixed in the config (now OK on pass B)

| sheet | s (m) | side | kind | onboard shows | sim showed | verdict | fix |
|---|---|---|---|---|---|---|---|
| fwd_10/11, side_12 | 3100-3450 | left | boards | SONOMA RACEWAY / SUNBELT / TOYOTA / HUMBOLDT / SAVE MART / ZMAX / ECHOPARK | black panels with one letter each | WRONG_COLOUR | names as (text, bg, fg) tuples |
| fwd_05, side_05 | 1550 | left | tower | tall dark infield tower with green light | absent | MISSING | scoring_tower at the 27.9 m lidar spike (c20_s3300) |
| fwd_11 | 3450-3550 | left | wall | LAS VEGAS / O'Reilly board wall to 5 m | boards hidden inside the shed box | WRONG_POSITION | wall line 0.6 m toward the track, shed plain |
| side_07, back_03 | 2085-2140 | left | boards | TOYOTA / Safety-Kleen boards on posts | none | MISSING | wall_boards with base 1.4 m |
| side_06 | 1510-1615 | right | tyre_wall | tyre line along the drag-strip shoulder | line 5 m off the band | WRONG_POSITION | re-measured (rms 0.83 m) |
| fwd_13, side_15 | 3950-4010 | both | boards | green ECHOPARK panels on both walls | plain walls | MISSING | wall_boards on pit wall and drag-strip wall |
| fwd_00, side_00 | 113-180 | left | building | pale pit-out building, red roof | grey box | WRONG_COLOUR | garage structure, red roof |
| fwd_11 | 3300-3420 | right | building | tyres and catch fence only | 12.5 m box (event tent on c20_s1045) | EXTRA | building_evidence drop |
| fwd_13 | 3995-7 | left | stand | bleachers with suites deck | OSM slab / missing | WRONG_TYPE | grandstand structure from terrace_measure footprint |
| side_02 | 409 | left | fence | catch fence at the terrace foot | none | MISSING | fence 2.5 m on the T2 tyre wall |
| side_03 | 861-917 | left | fence | fence posts on the Jersey | none | MISSING | fence 2.5 m on the T3a Jersey |

## Pass B table (open rows; none of the must-cover kinds)

| sheet | s (m) | side | kind | onboard shows | sim shows | verdict |
|---|---|---|---|---|---|---|
| fwd_13, side_17, back_00 | 4085 | both | paint | chequered S/F stripe and the SONOMA RACEWAY ground logo | plain asphalt (ortho) | MISSING |
| fwd_12, side_16 | 3630-3700 | right | paint | TOYOTA / Save Mart / Coca-Cola ground logos in the T11 infield | ortho smear only | MISSING |
| fwd_02, side_03 | 805-830 | right | station | white tower, open deck on tall legs | kit hut (box with band) | OK_DIFFERENT (kit shape) |
| fwd_13, mont2 | 3995-7 | left | stand | light grey bleachers | darker grey in shade | WRONG_COLOUR (minor; lighting) |
| pit_00..02 | 3520-3740 | both | tyre_wall | GENERAL TIRE wall with black stacks along the lane | white board wall, no stacks on the lane side | WRONG_COLOUR (pit side of the boards not surveyed) |
| fwd_09 | 2750 | right | cone_line | two orange cones at the bypass mouth | cone line across the mouth | OK_DIFFERENT (mouth line) |
| fwd_04 | 1300-1450 | right | wall | white wall on the bank foot with gaps | continuous wall with two short gaps | OK_DIFFERENT |
| fwd_06 | 1800-2050 | left | wall | light blue Jersey | light blue Jersey | OK |
| side_10 | 2663 | left | stand | back-straight terrace ahead | terrace, shade roof | OK |
| fwd_08 | 2450-2550 | right | mast | light masts beside T8a | lidar masts | OK |

## Checklist (C1-C21) per sheet

All 50 sheets: C1 ok, C2 ok, C3 ok, C4 ok, C5 ok, C6 ok, C7 ok, C8 ok, C9 ok (pit sheets) / n/a, C10 ok (pit_05) / n/a,
C11 ok, C12 ok, C13 ok (fwd_01, fwd_02, fwd_07, side_01-03, side_08) / n/a, C14 ok, C16 ok (side_08: movable tyre stacks
at T7) / n/a, C17 ok, C18 ok (runoff_00-03) / n/a, C19 ok (fwd_00 footbridge with abutments) / n/a, C20 ok, C21 ok;
**C15 FINDING** on fwd_12, fwd_13, side_16, side_17, back_00 (ground logos, rows above). Exceptions per sheet: fwd_02 C13
OK_DIFFERENT (hut shape), pit_00-02 C14 FINDING (pit-side board names not surveyed).

## Ten worst rows of the lap (pass B)

1. s 4085 both, paint: S/F chequered stripe and SONOMA RACEWAY ground logo missing (C15).
2. s 3630-3700 right, paint: T11 infield ground logos (TOYOTA, Save Mart, Coca-Cola) missing (C15).
3. s 3520-3740 pit side, boards: GENERAL TIRE board face and its tyre stacks inside the pit-in lane not modelled.
4. s 3995-7 left, stand: grandstand reads darker than the onboard.
5. s 805-830 right, station: T3a tower drawn as the kit hut, not the tall open tower.
6. s 2150 left, station: T7 tower likewise (kit shape).
7. s 1300-1450 right, wall: T5 wall drawn continuous; the onboard shows breaks for access gaps.
8. s 2750 right, cone_line: bypass mouth cones as a full line; onboard shows two cones.
9. s 3100-3450 left, boards: panel widths uniform (8 m); real panels vary (SUNBELT is ~20 m).
10. s 0-250, kerbs: T1 exit right strip c colour unverified (no local frame).
