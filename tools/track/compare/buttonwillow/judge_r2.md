# Buttonwillow judge round r2 (20 Oct 2026, ~19:00 PDT)

Judge: **GPT 6 Astra through codex** (`codex exec -m gpt-6-astra --sandbox read-only -c model_reasoning_effort=high`, reachable
again after a day down), the JUDGE.md prompt, six batches of at most 8 sheets, two streams; prompt and raw outputs in
`judge_r2/` beside this file (`prompt.md`, `astra_b1..b6.md`: every table row, the per-sheet worst line and the C1-C21 line).
Package: branch buttonwillow 93106a6, rev dd0d1e6ab3 (stage 1 run 30, stage 3 after judge r1). Sheets: `compare_sheets/`,
47 (16 forward, 13 side, 8 back, 6 pit, 4 runoff). The orchestrator (Claude) read the 16-sheet hood set `hood_run30/`
first (SKILL 1.10: geometry PASS, the three exits on their block lines, every kerb side as the onboard), then checked
Astra's rows against the package (`scenery.json`), the inventory and the capture windows (`capwin.py`) where a fact could
settle a row. The pit sheets 03-05 (the pit-out lane, s 86-411) carry no video frame and no logged object: unjudged, as in r1.

## Orchestrator's own rows (before Astra's)

| sheet | s (m) | side | kind | onboard shows | sim shows | verdict | check |
|---|---|---|---|---|---|---|---|
| fwd_02, side_02 | 570-605 | right | kerb + road_edge | T2 hairpin: the block line on the inside of the apex (onboard 0:25.3 ahead-right, curving; c20 captures: a curved line of white blocks from s ~570 to the apex) | no kerb strip (none in 590-660); the fitted right edge runs ~6 m beyond the blocks onto the pale paved patch inside the hairpin (inventory 574 R "pale paved / concrete patch inside the hairpin") | MISSING kerb, WRONG_POSITION edge (stage 1: SKILL 1.5, the edge is the blocks' outer limit) | TRUE: windows tmp `cw_618_zoom.png`, `cw_630.png`; no inventory kerb row (add one). Also settle which line the onboard shows close on the LEFT at 0:26.5 (t032): the captures put the outer-loop block line 15-20 m out there |
| fwd_15, side_11, side_12, pit_01, pit_02, runoff_01 | 4550-4695 | left | building | timing tower: tan / beige walls, a glazed band on the upper storey only, a broad blue roof overhang (deck on posts), exterior stair and balcony on the track side, a blue canopy tent beside it | a white block with continuous dark horizontal bands under a blue roof | WRONG_TYPE / WRONG_COLOUR (r1 item 1 not closed) | TRUE on the zooms at s 4550 / 4600 / 4650 |
| fwd_00, fwd_15, side_00, side_10-12, back_00, pit_01-02, runoff | 4514-150 | left | wall | white K-rail with red sections and a dark section near s 101 | one pale colour, present (0.81 m from 4513) | WRONG_COLOUR | TRUE; the kit draws one colour per run: a kit item (colour segments), see round 3 |
| (package) | 542-555 L, 1384-1387 L, 1442-1471 L, 1528-1564 L, 1835-1842 L, 3105-3112 L, 3821-3866 L; 1170-1179 R, 1282-1291 R, 1836-1842 R, 1916-1925 R, 4056-4065 R | both | kerb | block lines where the footage shows them at the track edge | 22 strips drawn 1.5-9 m OUTSIDE the fitted edge (`off` -1.5 to -8.95 m) | WRONG_POSITION (strip or edge) | TRUE as a list: each is a block line the edge must reach (kerb_search zone, SKILL 1.5) or a false detection on another pavement to drop with the capture cited; 1835-1842 L (-5.6 m), 1836-1842 R (-9.0 m) and 3105-3112 L (Astra: EXTRA, no inventory kerb) look false |

## Astra's rows, by theme, with the orchestrator's check

Rows are in `judge_r2/astra_b*.md`; the themes below carry every material row. "false" = settled against the package or the
inventory; "check" = the agent settles it with the frame or capture named; "true" = settled.

1. **Corner stations drawn as enclosed cabins (WRONG_TYPE, C13).** Rows at 450 R, 477 R, 800 R, 950-1000 R, 996 R, 1188 R, 1521 R,
   2050-2052 R, 2100 L*, 2400 L*, 2700 R, 2778 R, 2800 L*, 3150 R, 3400-3450 R, 3500 L*, 3650 R, 3800 L*, 4200-4250 L, 4273 L,
   4300 R*, 4679 R (pit: a raised platform with railings and an access stair) (* = back sheets, driving-side given). The onboard
   frames (t020, t034, t040, t046, t058, t074, t082, t092, t112, t122, t138) show open canopies on posts over tyre-faced mounds,
   some with a low platform; the kit's hut (`style 'tower'`, colour #2f5d9e) draws solid blue panels under the roof. TRUE for
   the whole set: one kit change (an open canopy style), not fourteen placements. r1 had passed the huts; Astra is right by
   the frames.
2. **Kerb colours (WRONG_COLOUR, C11).** Astra reads red-and-white on most forward sheets where the onboard shows red / white /
   blue (200, 250, 300, 400, 550, 950, 1100, 1150, 1250, 1350, 1650, 1800, 2300, 1643, 1658). The package carries all three
   colours on 133 of 166 strips (18 blue/white, 15 red/white) with `stripe_m` 1.0; the blue (#3c62a8) reads dark at distance
   and the real blocks are ~1.5-2 m. CHECK with a close still against t014 / t044 (block length, blue tone); 1643-1658 L
   (runoff_00/01) is a red/white strip: check the frame.
3. **Kerbs missing or short (C11).** 600 R: TRUE (above). 750 L: the package has 741-747 L only (7 m, red/white) where the onboard
   (0:32) shows a long block line beside the cones: CHECK extent. 1000 L: inventory 975 / 996 L exist; CHECK extent. 1224 L: the
   strip starts at 1236: CHECK start. 1300 R: strips 1282-1301 R sit 0.9-1.7 m outside the edge: in the list above. 1450 L:
   strips 1442-1471 L sit 1.5-2.75 m outside the edge: in the list above. 1500 R: strips 1482-1502 R at -0.7 m exist: FALSE
   (visibility), unless the close still says otherwise. 1750 R: 1768-1797 R exist: FALSE. 1850-1900 R: 1858-1867 and
   1868-1908 R exist (bands reader), faint on the sheet: CHECK the render (colour, offset) with a close still. 1839 L: the
   strip is 5.6 m out: in the list above. 3100 L EXTRA: 3105-3112 L at -1.7 m, no inventory kerb: CHECK on c20_s3150, likely
   drop. 3750-3800 L MISSING and 3800 R: the package's left strips end at 3751 and the right strips run 3764-3799, i.e. the
   T10 line changes side there, while the onboard at 2:04.9 and 2:06.3 (hood s 3750, s 3800) has the block line on the LEFT
   beside the car: TRUE as an open question for the captures (c20_s3800 / c20_s3850): if the diagonal line is the left
   limit, the centre must follow it (prior_shift / zone), not only the strips. 4350 L: the left strips start at 4365 (15 m,
   within tolerance): FALSE unless the capture shows blocks from 4350. 2400 L (back_04): 2301-2330 R exist: FALSE (the
   back view at 100 m).
4. **Cones (MISSING, C8 / C7 / C18).** Single placed cones (297, 533, 834, 973, 1040, 1307, 2158, 2696, 3439, 4071, 4575, 4593)
   are 0.7 m objects 1.5 m off the edge and do not read on the sheets: Astra's rows at 300 R, 550 L, 950 L, 1050 R, 1300 R,
   2150 R, 3450 R, 4550-4600 R are FALSE by the package (cite the object per row). TRUE or CHECK by the frames: 150 R
   (several cones on the paved shoulder, t006-t008), 900 L (t036), 1800 R (a long line separating the adjacent pavement,
   t066-t068), 3250 / 3300 L (t108-t110), 3650 R (t122), back_03 1900 L / 2200, back_05 3300 both sides / 3400 R / 3500 L,
   back_06 4100 L, back_07 4600 L, and the runoff closures the footage shows where the sim leaves a paved branch open:
   1562 L (T5 branch), 1780 R, 1824 R, 4064 R (drag strip), 46 R and 4607 R (front-straight crossover), 293 R, 3256 L. The
   pit-lane cones (~0.46 m) along the pit wall at 4478-4679 and s 11, both sides (pit_01, pit_02; pit video): TRUE if the
   video shows them.
5. **Pit-in mouth and paint (pit_00 4282-4329 R, fwd_14 4300 L).** The pit entry renders as a narrow lane with a white edge and
   a yellow hatch field, separated from a broad paved apron by an unpaved wedge; the footage shows a continuous paved apron
   and no yellow field, and the onboard at 4300 shows no broad paved mouth on the left: CHECK against c20_s4300-c20_s4400
   and the pit video (the mouth's shape, the paint, the station ahead-right at 4306-4329 seen from the lane).
6. **Surface tone (C17).** The paved aprons and crossovers (4572-4600 R, 4500-4600 L, 667 L, 1658-1824 R, 1689 R) render much
   paler than the track where the footage shows a modest difference; the pale chevron marks at the 1824 R mouth (runoff_02)
   are not in the footage: CHECK the closed-road tone and mouth marks against the frames; r1 had read the pale aprons as
   matching the footage, so the frames decide.
7. **Smaller rows.** 450 R station barrier pale (white-faced tyres?) vs black tyres (t020); 800 R station base wall ~0.6-0.8 m
   vs exposed legs (t034); masts at 3200 / 3500 R drawn as plain poles (the footage: a lattice / floodlight head) and a 10-15 m
   mast at 3256 R on runoff_03 (MISSING); the 574 R inside apron as a paved zone (side_02); 1476 L and 2023 L paint rows
   unresolved (n/a).

## Ten worst rows of the lap (orchestrator's order)

1. T2 hairpin inside block line: no kerb strip, the right edge ~6 m past it onto the inside paved patch (stage 1 + kerb + paved zone).
2. The corner stations as enclosed blue cabins where every frame shows an open canopy on posts (kit).
3. The timing tower still a banded white block (kit / evidence: tan walls, upper glazing, blue deck, stair).
4. 22 kerb strips 1.5-9 m outside the fitted edge: block lines the edge must reach, or false detections (stage 1 / strips).
5. T10 3740-3810: the line's side (package right, onboard left) and the centre there.
6. The K-rail and pit-lane walls one colour where the footage has red / white sections (kit).
7. Cone lines the footage shows that the package lacks (150 R, 900 L, 1800 R, 3250-3300 L, the runoff closures, the pit-lane cones).
8. The pit-in mouth's shape and yellow hatch paint (C9 / C10 / C18).
9. Closed-road tone and mouth marks (C17).
10. Kerb colour / block length at distance (C11).

Not in this round: the T4 kink width (1034-1115): the owner will mark up the edges on the 2026 capture; the agent leaves that
stretch as it is until then.
