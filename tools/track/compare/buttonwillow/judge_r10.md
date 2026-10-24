# Buttonwillow judge round r10 (23 Oct 2026, ~20:48-21:05 PDT)

Judge: **GPT 6 Astra through codex**: `codex exec -m gpt-6-astra --skip-git-repo-check --sandbox read-only`, reasoning effort
low (the codex default, as in round 8). Seven batches over the 50 round-10 sheets in lap order, 20:48-21:03:
- b1: fwd_00-06
- b2: fwd_07-13
- b3: fwd_14-15, side_00-04
- b4: side_05-11
- b5: side_12-13, back_00-04
- b6: back_05-07, pit_00-03
- b7: pit_04-05, runoff_00-05

The prompt is `judge_r10/prompt.md`. It is round 8's with the same table, checklist and rules, plus:
- the round-10 package facts;
- a "what round 10 changed" paragraph;
- the owner's decisions (the mouth cone lines, the open pit entry and the flush kerbs), to be judged on their execution only;
- the runoff-sheet caveat;
- Q1 and Q2.

b1 ran before the runoff caveat was added; it has no runoff sheets. The raw tables are `judge_r10/astra_b1..b7.md`, and the parsed rows are in `judge_r10/rows.json`. Every batch returned a full table with the checklist lines, a batch ten-worst list, and Q1 and Q2. The parser checked this.

A note on the files: b3's first run was valid, but my row counter missed its `sheet_`-prefixed names and started a retry. I
stopped the retry and kept the first run. As a result, `astra_stderr_b3.txt` is the stopped retry's log.

Every non-OK row was checked by **the orchestrator's delegate (Claude, Opus)**. The checks used:
- the package objects, projected onto stations by `/tmp/bw_judge_r10/objects.py` and listed in `judge_r10/package_objects.txt` (39 kerb strips, 47 cone lines, 17 barriers, 50 landmarks, 257 paint lines);
- the cone placement replayed as `buildPitExitCones` places the cones (every `spacing_m` along `pts`) and measured against the edge polylines;
- the 30 m station tolerance;
- round 10's `LEDGER.md`, `PREP_NOTES.md` (both passes) and `BOUNDARY_AUDIT.md`;
- round 8's settled rows;
- seven sheets read at full size by me: fwd_02, fwd_06, side_00, side_04, back_05, back_07, pit_02.

Package: branch buttonwillow e1dba23, `public/tracks/buttonwillow` rev 7acf260f50, lap 4699.19 m (n 4708, 0.99813 m spacing). Kerb strip stations below are metres along the lap (scenery `s0-s1`). Ledger zone stations are package station indices, about 0.2 % larger: zone L 2853-2859 is strip 2847.7-2853.6 m.

**Counts.**
- Rows: 347, of which 235 are OK_DIFFERENT and 112 non-OK. The batch ten-worst repeats (72 rows) are not counted.
- The 112 non-OK rows: 24 settled FALSE, 86 TRUE (as findings, grouped below), 2 UNSURE.
- The judge raised no cone-line execution fault on any sheet: every owner mouth line was OK_DIFFERENT. The package check below finds one.

## Settled FALSE (the package or the frames say so; the object is cited)

- **Kerbs "MISSING", 6 rows: the strips exist within 30 m.** In each of these the sim's kerb is there but not readable; that is the visibility finding below.
  - fwd_01 550 L: L 536.0-558.0 (new zone).
  - fwd_03 1000 R: R 1020.1-1049.0.
  - fwd_04 1450 L: L 1454.3-1478.2.
  - fwd_05 1750 R: R 1777.7-1817.6.
  - fwd_06 1850 R: R 1867.5-1932.4.
  - fwd_09 2750 R: R 2762.8-2789.8.
- **Kerb "EXTRA" fwd_10 3000 L:** the strip L 3002.4-3010.4 is from the block line on c20_s3150. Round 8 settled the same row (c20_s3100, r5).
- **Stations "solid pedestal / booth", 8 rows:** fwd_01 450, fwd_02 800, fwd_06 2050, fwd_14 4250, side_01 477, side_03 996 (type), side_04 1190 and side_09 3440. The frames show that construction (station_crops.jpg, r5 / r6); round 8 settled the same rows.
- **Station "MISSING" side_10 3765 R:** the T10 marshal landmark is at s 3712.0 R, 12.1 m out, 53 m behind the pose (r4 and r8 settled this).
- **Masts "MISSING" back_05 3300 / 3400 / 3500:** the lattice mast landmark is at s 3445.5 L, 161 m out, 49.5 m tall (OSM 10220517717). At 3500 the sim shows it as a dark green column (I saw this on the sheet). Its look is the round-8 mast row, listed under the findings.
- **fwd_00 0 L paddock buildings:** 13 lidar buildings stand north of the lane (round 8 settled this). They are low and far from s 0.
- **Cone rows, 3:**
  - fwd_09 2700 L "two cones MISSING": cone line 42, two cones at 2695.9-2699.9 L, 1.5 m out (onboard t092).
  - side_00 47 R "all orange, caption says yellow and orange": lines 19-22 are four cones at 40 / 45 / 50 / 55 R, 3.8 m out, coloured `#e8c21c` yellow, `#e6e4de` white, then orange, orange (t006). The 70-degree still at 47 sees the 50 / 55 orange pair.
  - side_06 1924 R "single cone MISSING": line 23 is at 1914.4 R, 1.5 m out. It is hidden by the A-pillar, as the judge itself allowed.
- **side_00 104 L "dark section missing":** barrier 0's section `from_m 286-292` (`#3b3a38`) maps to s 95.8-101.8 L, 5.6 m out, which is behind the 104 pose's view. The boundary audit (edge_R_0100) sees that one panel render black from across the track. It exists and renders, so this is FALSE. It remains the fourth judge in a row not to see it from s 100 forward; that is a placement-versus-sightline note, not a missing object.

## Real findings (TRUE, with sheet and station)

| theme | rows | finding | check |
|---|---|---|---|
| **Kerb visibility from the hood** | 24 WRONG_TYPE / WRONG_COLOUR rows plus the 6 settled-MISSING rows above: fwd_00 200 / 250 R, fwd_01 300 L / 400 R / 550 L, fwd_02 600 R / 750 L, fwd_03 950 L / 1000 R, fwd_04 1200 / 1250 / 1350 / 1450 L, fwd_05 1500 R / 1650 L / 1750 R, fwd_06 1800 / 1850 / 1900 R, fwd_07 2300 R, fwd_09 2700 L / 2750 R, fwd_11 3350 L / 3400 R / 3500 L, fwd_12 3700 / 3750 / 3850 L, fwd_13 3900 R, fwd_14 4300-4400 | The onboard's kerbs are wide, saturated, readable blocks well ahead. The sim's strips are thin and pale and vanish at the same distance. This is Q2 below. | TRUE, high. I saw it on fwd_06 (s1850: plain onboard kerb, nothing in the sim) and fwd_02 (s600). The strips are all placed and flush (ledger, boundary audit). This is a visibility problem: the 0.5-1.3 m strip widths, the colours and the flat 0.1 m profile at a grazing angle. It is not placement. The forward sheets prove it; the side, back and runoff views do not (the judge said so in each). |
| **Crack seal: shape** | fwd_05 1600 / 1650, fwd_02 850, fwd_10 3150, fwd_13 3900, fwd_14 4300, back_01 800, back_02 1300 / 1700, back_04 2400 / 2600, back_05 3000, back_06 3900, back_07 4300, runoff_02 1823, runoff_04 4618, runoff_05 623 (WRONG_TYPE) | The 257 `paint_lines` are straight, 0.1 m wide, `#2a2a2a`, median 4.6 m long. They read as black bars or dashes, not wavy dark-grey seal. | TRUE, high. The judge never claims they stand up ("lying on the asphalt"). In perspective a lengthwise mark becomes a vertical bar (prep notes). back_07 4300 (I saw it) and fwd_14 4300 show the pit-entry centreline marks (three on the centre, 5-15 m long, at 4280-4323) as one long black centre line. |
| **Crack seal: density** | fwd_00 150, fwd_01 500, fwd_02 650 / 700, fwd_03 900, fwd_04 1400, fwd_05 1700, fwd_06 1950 / 2000, fwd_08 2500-2550, fwd_09 2900, fwd_14 4200 / 4350, fwd_15 4500-4650, back_02 1500, back_03 1800, back_04 2500 / 2700 / 2900, pit_01 4568 / 4593 (MISSING / WRONG_TYPE) | The onboard has a dense, branching seal network everywhere, including the pit lane. The sim's is sparse, because 257 marks were kept against round 8's 407 on the narrower round-10 edges. | TRUE, medium. Same object. One fix covers both: shape (wavy, branching, dark grey) and coverage. |
| **Atlantic mouth cones on the track** (my package check; the judge missed it) | side_00 186 R (a cone on the asphalt by the edge, seen on the sheet), back_00 200, cone line 9 (owner mouth R 154-186) | Of the line's 17 cones, 9 stand **0.30-1.24 m inside the right edge** at s 171-187, on the racing surface. Line 11 (crossover R 1811-1835) has 2 cones 0.74 m inside at 1820-1821. The other 17 owner lines are within -0.23 / +0.45 m of the edge, and the T2 kink line starts 0.48 m outside by design. | TRUE, high: an execution fault of decision 2. The owner gates leave out the mouth segments ±12 stations, so the fitted edge there can sit off his red, and the cones follow his red. At 186 the cones are 1.2 m inside, against a ghost line held 1.0 m inside the edges. Either the cones are clipped to the edge in the mouth segments, or the edge follows his red there. |
| **T2 outside tyre wall as a black band** | fwd_02 600 L (EXTRA; also prep notes, boundary audit edge_R_0625 / 0650 and zone_T2-runoff) | Barrier 15 (tyres, 1.0 m, `#202020`, L 585.9-634.8, 29-40 m out, from c20_s0700 / s0750) reads as a continuous flat black band on the horizon. The onboard at the same station shows nothing dark there. | TRUE as look; I saw it on fwd_02. Whether it should be lower, greyer and broken, or set further back, is UNSURE until checked on t024-t028 and the capture. Unchanged since round 8. |
| **Control tower massing** | pit_02 4643 / 4668 / 4693 L (WRONG_TYPE) | The pit video shows a compact tan tower with an open upper balcony and an exterior stair. The sim (structures 0, 1, 4) reads as a long low tan block with an enclosed window band under a broad blue roof. | TRUE, medium; I saw it on pit_02. The colours and the blue roof now match (round 8's checkpoint 6), but the elongated plan and enclosed upper floor of round 8's row 1 remain. |
| **Lattice mast reads solid** | fwd_10 3250, fwd_11 3350, back_05 3500 | The 49.5 m lattice mast renders as a solid narrow green column. | TRUE, low (kit). Round 8's open mast row. |
| **T11-approach station tyres pale** | back_07 4300 (WRONG_COLOUR) | Barrier 13 (L 4276-4283) is `#d2cab8`, but its own source says "the dark tyre ring round the station roof" (c20_s4400). The onboard shows a dark base. Barriers 10-12 (T3, T5, T6) have the same source text and the same pale colour. | TRUE, small; I saw it on back_07. Check barriers 10-13 for the colour mismatch. |
| **Owner-decision items, executed but differing from the onboard** (for Coby, not the builder) | side_04 1304 / 1309 R; side_06 1773-1824 R; side_13 4593 R / side_12 4573 R; side_08 2857 L | (a) The new strip R 1304.6-1309.5 is **4.9 m** long. The onboard at 1304 / 1309 shows a T4-exit kerb of roughly 30 m; I saw it on side_04. (b) At 1780-1830 R the declared onboard line 26 (t066-t068, 6 m spacing, 3.0 m out) stands beside his mouth line 11 on the edge. This is the "cone at 1800 R off its line" and the two rows on side_06. (c) Pacific: his line 17 (4578.4-4606.4, on the edge) plus the declared single cones 45 (4575.4) and 46 (4593.4), 1.5 m out, give the "three big cones off a clean line" (ledger open item 2). (d) New strip L 2847.7-2853.6 (zone 2853-2859): neither the onboard nor the sim shows a kerb there; the onboard has white paint marks (prep notes second pass; judge OK_DIFFERENT). | The judge rated all four OK_DIFFERENT. They are TRUE as observations. Each needs his word: the zone length, whether to drop line 26 and cones 45 / 46 now his lines exist, and the 2853 zone. |
| **T2 patch curved line** | side_02 590 R (OK_DIFFERENT, no onboard frame) | A broad yellow-green curved stripe across the T2 concrete patch. | OPEN: the judge could not judge it without a frame, and the onboard fwd_02 s600 shows no such line (prep notes). This is round 8's T2 patch detail. |

UNSURE (2):
- **side_03 996 R canopy colour** ("blue" vs the sim's beige-grey): the colour comes from the caption. The prep agent's full-size read says the onboard canopy is black. All marshal roofs are `#cfd4d8`. Not checked on the frame.
- **pit_02 4693 R starter's stand** ("dark skeletal platform" vs "small pale platform"): on the sheet both read as an open scaffold platform. The sim's members look darker and its roof broader. Not measured.

## Q1 and Q2 (the judge's answers, merged across the seven batches)

**Q1 (crack seal).** Not as the onboard's seal, in any batch. They read as **straight black bars or strokes** at:
- fwd_05 s1650; fwd_14 s4300;
- back_01 s800; back_02 s1300 / 1700; back_04 s2400 / 2600;
- back_05 s3000; back_06 s3900; back_07 s4300;
- runoff_05 s623; runoff_02 s1823; runoff_04 s4618.

They read as **isolated lane dashes, close to a dashed centre line**, at fwd_05 s1600, fwd_02 s850, fwd_10 s3150 and fwd_13 s3900. back_04 s2600-2700 is loosely dash-like.

Elsewhere the problem is **missing coverage**, the onboard's branching network absent: fwd_01 s500, fwd_05 s1700, fwd_08 2500-2550, fwd_09 2900, fwd_14 4250 / 4350-4450, fwd_15 4500-4650, back_02 1500, back_03 1800, back_04 2500 / 2900, and pit_01 4568-4593.

Every batch says the marks lie on the asphalt, and none sees one standing up. The pit-entry centreline (back_07 s4300, fwd_14 s4300) is the clearest centre-line reading. I confirmed it on back_07.

**Q2 (kerb visibility).** No.
- **The sim's kerbs vanish** (blocks unreadable or absent) at fwd_01 s550, fwd_03 s1000, fwd_04 s1450, fwd_05 s1750, fwd_06 s1850 and fwd_09 s2750.
- **They turn thin or pale** at:
  - fwd_00 s200-250; fwd_01 s300 / 400; fwd_02 s600 / 750; fwd_03 s950; fwd_04 s1200-1350; fwd_06 s1900;
  - fwd_07 s2300; fwd_09 s2700; fwd_11 s3350 / 3400 / 3500; fwd_12 s3700 / 3750 / 3850; fwd_13 s3900; fwd_14 s4300-4400;
  - back_05 s3400 and back_06 s3800-4000.
- **Good matches:** fwd_03 s1100 (the T4 run, now flush) and back_07 s4400.
- **The side, back and runoff batches** (b4, b5, b7) say their views cannot establish forward visibility. There the strips are identifiable (side_05 1344 / 1492, side_06 1839 / 1878, side_07 2313 / 2696, side_09 3479, side_10 3848 / 3981, side_12 4410-4458).

## Ten worst rows of the lap (from the judge's batch rankings), with my verdict

1. **fwd_06 1850 R kerb MISSING.**
   - FALSE as placement: strip R 1867.5-1932.4 exists.
   - TRUE as visibility: I saw it on fwd_06. The onboard's long kerb is plain and the sim shows nothing.
   - It stands for the kerb-visibility theme, the worst thing on the lap.
2. **fwd_02 600 L tyre wall EXTRA (black band).**
   - TRUE as look: I saw it, and the onboard shows nothing dark there.
   - UNSURE as existence: barrier 15 is declared from the capture's dark band.
3. **fwd_05 1650 crack seal as a black bar.** TRUE (the paint-line shape: 0.1 m straight `#2a2a2a` strips).
4. **back_04 2600 isolated straight strokes instead of the network.** TRUE (shape and density).
5. **fwd_14 4300 straight strokes at the pit entry.**
   - TRUE: the three centreline marks at 4280-4323 read as a centre line.
   - Also seen on back_07 4300.
6. **pit_02 4668 control tower elongated, enclosed upper level.** TRUE: I saw it on pit_02. It is round 8's row 1, still open in its massing.
7. **side_10 3765 R corner station MISSING.** FALSE: the T10 station is at s 3712.0 R, behind the pose.
8. **back_05 3500 floodlight mast MISSING.**
   - FALSE as missing: the mast is at s 3445.5 L, 161 m out, 49.5 m tall.
   - TRUE that it reads as a solid green column (seen on back_05).
9. **side_09 3440 R station as a solid booth.** FALSE: the frames show that construction (r5 / r6, round 8 settled).
10. **back_07 4300 station tyres white vs dark.**
    - TRUE: I saw white stacks against the onboard's dark base.
    - Barrier 13 is `#d2cab8` although its source says a dark tyre ring.

Not in the judge's ten, but worse than 7-10 because it is on the racing surface: **the Atlantic mouth cones up to 1.24 m inside the right edge at s 171-187** (from the package; the judge rated side_00 186 OK).

## Verdict

Round 10's owner decisions show up as he made them: the edges, the flush strips, 19 mouth lines and the open pit entry. Judging those as his decisions, the judge found no execution fault in them. The package check found one: the Atlantic and crossover mouth cones that stand inside the edge.

The two big look problems from the hood are:
- the kerbs' visibility (placed and flush, but too thin and pale to read ahead);
- the crack seal (too sparse, and straight black strokes where the onboard has wavy grey seal, including a false centre line at the pit entry).

For the owner: the 4.9 m strip at R 1304.6-1309.5 against the onboard's ~30 m kerb, the declared line 26 beside his crossover mouth line, the Pacific single cones beside his line, and the 2853 zone where neither view shows a kerb.

Unchanged rows carried from round 8: the tower massing, the T2 tyre band, the mast, and the station tyre colours.
