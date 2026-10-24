# Sonoma judge, round 14B (rev 6b766e08d6, lap 4105.328 m)

Judge: GPT 6 Astra (`codex exec -m gpt-6-astra --sandbox read-only -c model_reasoning_effort=high`, codex-cli 0.163.0),
three runs, one per place, from the track-pipeline worktree on 24 Oct 2026. Prompts, image lists and raw outputs are in
`judge_r14b/` (`prompt_r14b_{A,B,C}.md`, `images_{A,B,C}.txt`, `astra_r14b_{A,B,C}.md`, the stderr logs). The images
(stills in `round14b/stills/`, onboard crops in `compare_sheets/onboard/`, the owner's marked windows in
`owner_edges_r14b/`) stay local.

| batch | place | images | sim stills (after / before / after-only) | onboard crops | owner windows |
|---|---|---|---|---|---|
| A | T1 and the T7 complex, wall heads s 1062 and s 2347 | 24 | 8 / 8 / 2 | s0150 s0250 s1050 s2100 s2150 s2350 | - |
| B | T9 to T9A, wall head s 3169 | 23 | 8 / 8 / 1 | s3000 s3050 s3100 s3150 | w_s3000 w_s3125 |
| C | T11 hairpin and T10, wall head s 736 | 24 | 7 / 7 / 1 | s3350 s3600 s3650 s3700 s3750 s3800 s0750 | w_s3625 w_s3750 |

The checklist was JUDGE.md's C1-C21, answered per sim image (in the raw outputs). The onboard station map is on the old
4098.5 m lap, so from T9A on it reads up to ~7 m early.

Every row below was checked by the orchestrator against the stills (with zoomed crops), the onboard frame, and the package
(`public/tracks/sonoma/scenery.json`, `track.json`), the manifest, the inventory and the ledger. Rows the judge repeated
for before and after, or for several neighbouring stills, are merged into one row that cites every image. Verdicts:
**TRUE** (the difference is real; "history" = a round-14A defect that round 14B fixed), **FALSE** (with the reason),
**OK_DIFFERENT**, **UNSURE** (what would settle it).

## Counts

| verdict | A | B | C | all |
|---|---|---|---|---|
| TRUE, current | 6 | 3 | 2 | 11 |
| TRUE, history (fixed in 14B) | 3 | 3 | 2 | 8 |
| FALSE | 0 | 4 | 1 | 5 |
| OK_DIFFERENT | 3 | 2 | 7 | 12 |
| UNSURE | 3 | 5 | 5 | 13 |
| rows | 15 | 17 | 17 | 49 |

Of the 11 current TRUE rows, 14B caused or touched four: A14 (the tyre bundle), A10 / A11 (the T7 approach left edge
line, which 14B's tyre removal exposed), and B7 (the T9A mouth line). The other seven were there before 14B and are
unchanged by it.

## Rows

### Batch A: T1, the T7 complex, wall heads s 1062 and s 2347

| # | image | s (m) | check | judge | verdict | evidence |
|---|---|---|---|---|---|---|
| A1 | hood_150_after | 166-179 R | C8 | "Added orange cone line ... extra against the onboard" (EXTRA) | OK_DIFFERENT | s0150 shows no cones there (confirmed). The owner asked for the cones: LEDGER part 2, "4 cones 4.4 m apart, default orange: no frame shows cones there, his instruction". The judge says it is "owner-requested". |
| A2 | hood_150/200/250 after+before | 150-270 L | C17 / C10 | "Strongly contrasting pale pit-exit strip beside darker track" (WRONG_COLOUR) | UNSURE | In the sim, the pit-exit lane left of the yellow blend line is a lighter grey. In s0150 that lane is also lighter than the course, with its yellow line and cones, but the frame's grading hides how much lighter. 14B did not change it (`track_shoulder_cut` 150-240). A colour sample of capture c20_s1870 would settle it. |
| A3 | hood_150/200/250 after+before | ~270 ahead | C20 / C19 | "Flat canopy, vertical posts and advertising fascia; exposed lattice structure absent" (WRONG_SHAPE) | TRUE (pre-14B) | A crop shows a dark roof on posts over the board fascia. s0250 shows the boards hung on an open truss, with lattice end sections at both piers and no roof. |
| A4 | hood_150/200/250 after+before | ~270 ahead | C14 | "second Toyota/GR panel ... black lettering on a grey field" (WRONG_COLOUR) | OK_DIFFERENT | Both panels are white-ground, and the first (red, white text) matches. The difference is the GR logo art, which C14 leaves out (typed names, no logo art). |
| A5 | hood_150 after+before | ~111-150 L | C14 / C1 | "red-and-white advertising panels on the track-facing pit wall ... Plain wall face" (MISSING) | TRUE (pre-14B) | A crop of s0150 shows two red panels with white logos at the base of the pit wall near its nose. Inventory row s 111 has "red/white painted section at the far end". The sim draws a plain grey wall face. |
| A6 | strip_continuation_to_T7_before | ~2080-2100 | C4 | "substantial white wall along the near painted margin" (WRONG_POSITION) | TRUE, history | The before still shows round 5's third run on the near paint. 14B moved it to the far side (LEDGER part 2; config). In the after still the near margin is open with its white line. |
| A7 | strip_continuation_to_T7_before | ~2100 | C3 | "isolated black tyre facing against the distant concrete run" (EXTRA) | TRUE, history | This is the T7-approach tyre run that 14B removed. It is absent in the after still. |
| A8 | t7_approach_wall_left_before | ~2100 L | C3 | "stacked black tyres obscure the lower wall" (EXTRA) | TRUE, history | s2050 / s2100 show the light-blue wall bare to the asphalt. The after still has no tyres there. This confirms the ledger's onboard reading (t066-t072). |
| A9 | t7_approach_wall_left after+before | 2070-2150 L | C14 / C4 | "Nearby advertising absent; remaining boards concentrated farther ahead ... tens of metres late" (WRONG_POSITION) | UNSURE | Inventory s 2112 (t070) puts the Toyota boards on posts above the wall, and s2100 has them abeam. The sim pose is turned left, so the start of the board run cannot be read from it. A forward still at s 2090-2110 would settle it. |
| A10 | t7_approach_wall_left after+before | ~2000-2160 L | C6 / paint | "White longitudinal line along the wall-side pavement" (EXTRA) | **TRUE** | A crop of the after still shows a white line about 1 m off the wall's foot. In s2100 the left side is dark asphalt to the wall with no line (the line is on the right). The ledger (failing stage-1 gate, item 2) says "the left edge is asphalt to the wall with no paint (feature asphalt_end)". In scenery.json, edge_lines left run s 1649.9-2295.5 runs straight through. |
| A11 | t7_approach_wall_left after+before | ~2000-2160 L | C17 | "Separate pale shoulder strip between the main asphalt and concrete" (WRONG_COLOUR) | **TRUE** | Same crop: a paler, coarser band lies between that line and the wall. In s2100 the course asphalt runs to the wall's foot. |
| A12 | paddock_lot_left_2178 after+before | ~2178-2240 L | C3 | "Uniformly black protective run" where the closure has "alternating dark and light sections" (WRONG_COLOUR) | UNSURE | At 600 px, s2150 / s2200 do not resolve a barrier 100 m or more away. Inventory s 2237 (t074) logs a "black tyre wall line, recovery vehicles behind". |
| A13 | end_1062_crest_right_after | 1062 R | C1 | "Wall curves away in plan but finishes with a broad, exposed rectangular face" (WRONG_SHAPE) | OK_DIFFERENT | A crop shows the wall hooking away from the course into the bank and ending in a square face about 1 m high. The ledger's evidence (c20_s2750 / s2805) is a rounded concrete head at a culvert, turned into the bank. The real place also has an unprotected concrete head turned away from traffic. Square against rounded is a small shape difference, not a C1 failure on the evidence. |
| A14 | end_2347_far_wall_tip_after | ~2347 (the island tip) | C1 / C3 | "exposed rectangular concrete face. No black tyre bundle with a white top is identifiable there" (WRONG_SHAPE) | **TRUE; contradicts the ledger** | A zoomed crop shows the near wall ending in a bare square face beside the mast, with nothing at its head. **Cause:** in the published scenery.json, the barrier "drag strip NW end: tyre bundle at the far wall's head (round 14B)" has three coincident points, all (-365.49, 393.21): zero length. Config declares it as two latlon points about 2 m apart (config.py lines 1008-1011). The ledger's "joined to the tyre bundle: ok" (part 2 table) and stage 3's "wall ends 40 ok" count a run that draws nothing. |
| A15 | end_2347_far_wall_tip_after; t7_approach_wall_left | 2090-2160 L | C14 | "entirely of white panels with black Toyota lettering" (WRONG_COLOUR) | TRUE (pre-14B, minor) | In s2100 the first panel is red with white TOYOTA and the next is white with a red logo. In the sim, every panel is white with black TOYOTA (crop). |

### Batch B: T9 to T9A, wall head s 3169

| # | image | s (m) | check | judge | verdict | evidence |
|---|---|---|---|---|---|---|
| B1 | t9a_3000 / 3020 / escape_road_left, after+before | 3000-3050 L | C4 / C12 | "Pronounced bank between the road and wall, raising the wall above the approach" (WRONG_SHAPE) | UNSURE | The left wall with its 2.5 m catch fence is 14-26 m from the centre at s 3001-3048 (7-20 m beyond the edge). The sim's verge rises to it. s3000 reads as a flatter verge with the wall nearer, but through a wide-angle lens. 14B left it unchanged. A lidar cross-profile at s 3000-3040 against t096 / t098 would settle it. |
| B2 | t9a_3000 ... t9a_3100, after+before | 3050-3120 R | C5 / C4 | "catch fencing absent immediately above the near black barrier" (MISSING) | UNSURE (leaning true) | Package, right side: a tyre wall at s 3103-3137 with no fence, then concrete with a 2.9 m fence at s 3133-3180. From 3050 to 3103 there is only the grey tyre stack. In s3100 the fence posts run back to the frame's right edge above a dark barrier, so the real fence may start about 25 m before 3133. Check the fence's start on c20_s0715. Unchanged by 14B. |
| B3 | t9a_* after+before | 3000-3120 R | C12 | "Broad sloping panels with sparse divisions" (WRONG_SHAPE) | OK_DIFFERENT | The terraces' rows are drawn at art level. Position and extent are not in question. Unchanged by 14B. |
| B4 | t9a_3020 after+before | 3031 L | C8 | "Isolated orange cone on the verge" (EXTRA) | FALSE | scenery.json has one cone at s 3031, 10.8 m left, from "onboard RAZip6S84CM 1:36-1:38 (t096 / t098; owner_49 crop): one orange cone ~0.5 m on the grass verge". s3000 / s3050 are 2 s either side of it. |
| B5 | t9a_3020 after+before | 3047 R | C16 | "Isolated blue-grey cylindrical stack beside the kerb" (EXTRA) | FALSE | Landmark at s 3047, -12.8 m: "onboard 1:40: a stack of 2 grey tyres just past the 9a right apex kerb". |
| B6 | t9a_3020 / 3040 / escape_road_left | 3040-3060 L | C4 | "White wall terminates without that dark continuation" (MISSING) | UNSURE | s3050 shows the light wall, with darker low objects at the far end of the escape road; 600 px does not resolve them. The package has the left wall to s 3048, then the T10-entry board wall from s 3057, 33 m out. |
| B7 | t9a_3040_after; t9a_escape_road_left_after | 3037-3062 L | C18 / paint | "Mouth reads as largely undifferentiated asphalt ... fragmented"; "the before boundary was more legible" (WRONG_SHAPE) | **TRUE** | edge_lines left run s 2647.3-3059.0 ends at 3059 (the next starts at 3176.9, after kerb 25 at 3062-3174). In the after stills the course line fades out along the arc across the mouth (crop). s3050 shows clear white lines: the course line and the escape road's own lines, which meet in a V. So against the onboard, the line across the mouth reads worse than in 14A. The escape road's own lines are drawn (LEDGER: 65 / 78 stations). |
| B8 | t9a_3040_after; t9a_escape_road_left_after | 3050-3080 ahead | C17 | "Irregular transverse pale seam where the new dark pavement meets the farther surface" (WRONG_TYPE) | UNSURE | The crop shows a darker blotch in the escape road's asphalt and a lighter far surface, which reads more like ortho tone than a material seam. A still standing on the escape road would settle it. |
| B9 | t9a_3040_after | 3040-3055 R | C11 | "the red-and-white run visible in t9a_3020_after ends before this portion" (WRONG_SHAPE) | FALSE | Kerb 24 is right s 3019-3044 (detector 3021-3036; colour from t100). The camera at s 3040 is at the kerb's end, so the kerb lies beside and behind it. s3050 shows the same layout: the kerb beside the car, then the white line along the grass. |
| B10 | t9a_3080_after | 3074-3100 R | paint | "Clearly visible line from the before view is lost across the widened foreground" (MISSING) | UNSURE | edge_lines right run s 3047.0-3215.9 is declared. A crop of the after still shows no line in the right foreground, where the before showed one. The declared corner (right 3074-3096) moved the right edge, so the line may be out of frame. A still turned right at s ~3085 would settle it. |
| B11 | t9a_3080_before | 3074-3100 R | C17 | "broad pale paved-looking strip outside the white line" (WRONG_TYPE) | TRUE, history | Visible in the before crop, gone in the after. |
| B12 | t9a_3100 / 3120 after+before; end_3169_board_wall_left_after | 3100-3180 L | C14 | "Many short panels repeating small SONOMA RACEWAY text" where s3150 has large lettering and long SUNBELT panels (WRONG_SHAPE) | TRUE (pre-14B, minor) | s3150 shows a large SONOMA panel, then a long green SUNBELT RENTALS run. The sim shows several navy SONOMA RACEWAY panels before the green ones. |
| B13 | t9a_3100 after+before | 3129 L | C16 | "Freestanding black cylindrical stack on the grass" (EXTRA) | FALSE | Landmark at s 3129, 16.3 m left: "onboard 1:44: a black tyre stack in front of the T10-entry board wall at its start". |
| B14 | t9a_3120; t10_grass_along_outer_wall; hairpin_3640; end_735_T4_left | lap-wide | C5 | "posts have conspicuous angled upper extensions ... Straight vertical posts" (WRONG_SHAPE) | TRUE (pre-14B, lap-wide, minor) | The inventory logs "curved-top posts" (s 3638, 3670, 3680 and others). Every catch fence in the package is drawn with straight posts. Recorded once for all four batches' rows. |
| B15 | t9a_3100 / 3120 before | 3165-3169 L | C2 | "separated near and far wall runs with a visible opening" (WRONG_SHAPE) | TRUE, history | 14B re-measured it as one wall, joined to run 66 (LEDGER part 2). |
| B16 | end_3169_board_wall_left_after | 3165-3169 L | C2 | "Continuous faceted return ... acceptable" (OK_DIFFERENT) | OK_DIFFERENT | Agreed. In the still the board wall runs on continuously. |
| B17 | t9a_3040 / escape_road_left before | 3037-3080 L | C18 | "pale, ground-like surface outside the curved white line" (WRONG_TYPE) | TRUE, history | In 14A this area was unpaved. 14B paves the escape road. |

### Batch C: the T11 hairpin and T10, wall head s 736

| # | image | s (m) | check | judge | verdict | evidence |
|---|---|---|---|---|---|---|
| C1 | hairpin_3600 after+before | ~3590-3615 L | C3 / C16 | "alternating red/white vertical protective panels" and "exposed black tyre tops behind" (WRONG_COLOUR, MISSING) | **TRUE (pre-14B)** | A crop of s3600 shows a row of tyres wrapped in red / white panels against the light-blue Jersey along the pit-in separation. The sim has a red band at the foot of the tall board wall and no tyre facing. The inventory has no row for it: rows 3588 and 3638 list the Jersey only, and 3570 (24of8fjjAug) lists red / white water barriers at the nose. |
| C2 | hairpin_3600 after+before | 3590-3630 L | C14 | "Coca-Cola, Xfinity, Lucky ... replace the visible reference sequence" (FoodMaxx, Busch) (WRONG_TYPE) | UNSURE | The sim follows inventory rows 3588 (Lucky / Save Mart / Pit Boss) and 3638 (Coca-Cola / xfinity). s3600 (t 118.7) shows foodmaxx and Busch Light on the same wall. Re-read t118 / t120 to see which panels stand where. |
| C3 | hairpin_3600 / 3720 / 3760 / 3800, after+before | 3600-3810 R | C17 | "Strong material/texture boundary between the main road and adjoining paving" (WRONG_COLOUR) | TRUE (pre-14B) | In hairpin_3760 / 3800 a pale textured infield apron meets the course at a hard straight seam. In s3750 / s3800 the two are the same asphalt tone, separated by the white line. |
| C4 | hairpin_3600 / 3640 / 3680 | 3640-3680 ahead L | C20 | "Enclosed white rectangular blocks with continuous dark window bands" (WRONG_TYPE) | OK_DIFFERENT | Building art level (the glazed hospitality building, inventory 3670). Its position is not in question. |
| C5 | hairpin_3640 after+before | 3640-3665 L | C3 / C4 | "White drum-like tyre units occupy this visible outside leg" where s3650 shows a concrete face (WRONG_TYPE) | UNSURE | The package's white tyre run is s 3643-3730 (c20_s1265, white tyre band). The inventory has 3638 (t120) "light blue low wall round the T11 outside", then 3670 (t122) "white tyre stacks along the far wall" and 3699 "white tyre wall, T11 exit". The run may start 20-30 m early. Check where the band begins on c20_s1265 against t120 / t122. |
| C6 | hairpin_3680 after+before | 3684-3687 L | C1 | "Plain rectangular blocks project inward ahead of the tyre line, presenting exposed square ends" (EXTRA) | FALSE | Three blocks from capture c20_s1320 sit at the outside apron's edge (manifest row 133: "onboard 2:02 (t122) white blocks along the apron edge"). |
| C7 | hairpin_3680 / 3720 after+before | 3670-3730 L | C3 | "Smooth, pinched, two-lobed columns rather than tyre stacks" (WRONG_SHAPE) | OK_DIFFERENT | This is the tyre-wall mesh style, the same lap-wide. Height (0.8 m) and colour match. |
| C8 | hairpin_3680 / 3720 / 3760 / 3800 | 3690-3810 | C20 | masts, building windows, the green-roofed tower: "WRONG_SHAPE" | OK_DIFFERENT | Art-level detail of objects that are present at the right place and height. |
| C9 | hairpin_3720 / 3760 / 3800 after+before | 3730-3810 L | C14 | "repeated small rectangular panels along the building-side barrier ... Blank barrier face" (MISSING) | UNSURE | s3750 / s3800 show small panels on the pit-road-side wall. Inventory 3699 does not log them. Re-read t126 / t128. |
| C10 | hairpin_3800 after+before | 3780-3810 R | C14 | "LAS VEGAS ... remains beside the exit"; sim "zMAX/EchoPark" (WRONG_TYPE) | UNSURE | hairpin_3760 after shows O'REILLY / LAS VEGAS boards on the right ahead. The judge's mismatch may come from the station offset of s3800. |
| C11 | hairpin_3760 / 3800 | 3750-3810 | - | "Largely uniform granular road without the prominent rubber trails" (MISSING) | OK_DIFFERENT | Surface wear, not an object. |
| C12 | t10_grass_along_outer_wall_after | 3324-3398 R | C2 | "Main wall/fence turns inward; the separate inner run is gone. After is closer" (OK_DIFFERENT) | OK_DIFFERENT | Agreed. This is the 14B re-declaration (LEDGER part 2 A). |
| C13 | t10_grass_along_outer_wall_before | 3324-3398 R | C2 / C1 | "separate inner concrete/fence run with an exposed head" (EXTRA) | TRUE, history | Round 11's run 37, fixed in 14B. |
| C14 | t10_grass_along_outer_wall after+before | 3290-3400 L | C20 / C14 | "Smooth white advertising-wall face without the ribbed screen" / "Repeated red zMAX, black EchoPark" (WRONG_TYPE) | UNSURE | s3350 shows a tall grey corrugated screen with an EchoPark board, where the sim has a white board wall (zMAX / EchoPark). Re-read t112 / t114 for the screen's extent. Unchanged by 14B. |
| C15 | hairpin_3720_before | 3710-3730 L | C2 | "the concrete slab visibly intersects and progressively hides the tyre columns at the join" (SUNKEN) | TRUE, history | In the after still the columns stand clear of the wall. |
| C16 | end_735_T4_left_after | 736 L | C1 | "Exposed square concrete head ... Recorded exposure, not a verified mismatch or endorsement" (OK_DIFFERENT) | OK_DIFFERENT | Agreed, with one correction: the judge says "clearly shows". The still is rolled about 30 degrees and the head is about 40 px across, a light wall end with its fence and no tyres. This is the declared known exposure (`gates.known_exposures`). |
| C17 | hairpin_3680 / 3720 after+before | 3650-3730 L | C11 | apron: "Paved outside margin without an added red/white kerb. Flat treatment is plausible" (OK_DIFFERENT) | OK_DIFFERENT | Agreed. See open question (i). |

## TRUE rows as work items for the next round

Each item is inventory-style: place, what the evidence shows, what the package has.

1. **Drag-strip far wall head, tyre bundle (s ~2347, the island tip; batch A14). Gate gap.** In scenery.json the declared
   2 m bundle ("drag strip NW end: tyre bundle at the far wall's head (round 14B)") is three coincident points at ENU
   (-365.49, 393.21), so nothing is drawn and the wall head is bare in the sim. Config gives two latlon points about 2 m
   apart. Find the build step that collapses a 2-point tyre run. The wall-ends gate passed the head as "joined to the tyre
   bundle", so it should also reject a protecting run under about 1 m long.
2. **T7 approach left (s ~2000-2160; A10, A11).** The edge line and a pale shoulder are drawn along an unpainted asphalt
   end. The onboard (s2050 / s2100) and the ledger's asphalt_end show dark asphalt to the wall's foot and no line. Break
   the left edge line over the asphalt_end stretch and match the shoulder to the course asphalt. 14B's tyre removal
   exposed this.
3. **T9A escape-road mouth (left s 3037-3062; B7).** The course line along the arc fades out across the mouth. s3050
   shows a clear course line and the escape road's lines meeting in a V. Check the drawn line between s 3037 and 3059 and
   its continuity at the arc. The run ends at 3059 by design (kerb 25 starts at 3062).
4. **Pit-in separation (left s ~3590-3615; C1).** s3600 shows a red / white wrapped tyre facing in front of the
   light-blue Jersey. Add the inventory row first, then the object.
5. **T11 infield apron seam (right s 3600-3810; C3).** The infield apron's texture meets the course at a hard pale seam,
   where the onboard shows one asphalt tone (C17).
6. **Pit wall nose panels (left s ~111-150; A5).** Two red panels with white logos at the base of the pit wall
   (inventory s 111 "red/white painted section"). The sim wall is plain.
7. **T2 footbridge (s ~270; A3).** The boards hang on an open truss with lattice end sections and no roof. The sim draws
   a roof on posts.
8. **T7 approach Toyota boards (s ~2090-2160; A15).** Alternate the panels red (white text) and white (red logo) as
   in s2100.
9. **T10 entry board wall (s 3100-3180 left; B12).** One large SONOMA panel, then the long green SUNBELT RENTALS run (s3150).
10. **Catch-fence posts, lap-wide (B14).** The inventory logs curved-top posts. The package draws straight ones.

Items 6-10 were there before 14B, and the judges of earlier rounds did not raise them as rows. They are low priority
next to items 1-5.

## The UNSURE rows: what settles each

A2 (colour of the T1 pit-exit lane, sample c20_s1870); A9 (a forward still at s 2090-2110 for where the board run starts);
A12 (the tyre line in the paddock lot, beyond the onboard's resolution); B1 (lidar profile at s 3000-3040 left against
t096 / t098); B2 (where the catch fence starts on the right at s ~3105, c20_s0715); B6 (s3050 left beyond the wall end);
B8 (a still on the escape road); B10 (a still turned right at s ~3085 for the right edge line); C2 / C9 / C14 (re-read
t118-t128 and t112-t114 for board and screen identities); C5 (where the white tyre band starts on c20_s1265 against
t120 / t122); C10 (station offset of s3800).

## The owner's open questions: what the judge saw (described, not decided)

**(i) The hairpin's outside apron (left s ~3650-3730, grey-white, measured 3.1 m wide): kerb or apron?**
The judge, batch C Q1: "The outside band reads more plausibly as pale apron/runoff than as a demonstrated raised red/white
kerb, but these images do not settle its cross-section. ... the unmistakable red/white kerb is on the **inside/right**.
hairpin_3640_after, hairpin_3680_after and hairpin_3720_after do not show an added outside block kerb. ... The owner's
plan-view jogs are not evidence of vertical surface steps." Checked against the evidence:
- In w_s3625 / w_s3750 the band is a uniform pale strip with no block pattern. The inside apex kerb in the same windows
  shows red / white blocks.
- In s3750 the band is a wide, flat, white strip along the left at the exit.
- In s3700 the white tyre wall stands beyond it.
- Three white blocks stand on its edge (manifest row 133, c20_s1320, onboard t122).
- In the sim (hairpin_3680 / 3720 / 3760 after) the white edge line runs along his red, and beyond it is the same grey
  paving, not a distinct grey-white band.

Stills and crops: hairpin_3680 / 3720 / 3760 (after, before), onboard s3650 / s3700 / s3750, w_s3625 / w_s3750.

**(ii) The bare wall head at left s 736.**
The judge, batch C Q2: "onboard/s0750.jpg does **not** resolve the s736 wall's terminal face, so it establishes neither
bare concrete nor tyres, a cap or a cushion at that end ... the supplied evidence does not justify adding protection or
accepting the bare end as confirmed."
- s0700 / s0750 show the wall and fence far ahead-left, too small to resolve.
- end_735_T4_left_after is rolled about 30 degrees, and the head is about 40 px across: a light square wall end with its
  fence and no tyres.

The only evidence of the real end is still the capture (c20_s2420, capstrip s 680-790; LEDGER part 2). Stills:
end_735_T4_left_after, onboard s0700 / s0750.

**(iii) The T9A junction corners (left arc s 3037-3062, right corner s 3074-3096) against the onboard.**
The judge, batch B Q2: "The owner's thick red strokes in w_s3000_marked.png and w_s3125_marked.png do contain the sharp
changes of direction described ... The supplied images therefore support neither an exact-fit approval nor a confident
claim that either declared junction corner invents a pavement shape."
- It raised two legibility points. The course line across the escape road's mouth fades (B7, TRUE). The right edge line is
  not visible at t9a_3080 after (B10, UNSURE: the line is declared there, so it may lie out of frame).
- s3050 shows a broad paved opening straight on to the left of the right-hander, marked with white lines, with no cones
  and no kerb across it. The red / white kerb is at the right-hand apex.
- No still shows a pavement shape the onboard contradicts. The hood views cannot measure the arcs.

Stills: t9a_3040 / 3060 / 3080 / 3100 (after, before), t9a_escape_road_left, onboard s3050 / s3100, w_s3000 / w_s3125.

**(iv) The T9A chicane line: where the real cars run through the chicane.**
The judge, batch B Q3: "In onboard/s3000.jpg the car approaches toward the left side, leaving substantial width to its
right. In s3050 it has turned right and runs close alongside the right-hand red-and-white apex, with most of the available
pavement to its left. In s3100 it is alongside the left-hand apex/exit paint after changing direction, leaving substantial
width to the right. By s3150 it is opening its path toward the next rightward bend. ... It does not visibly take the
straight-on escape branch. Four separated frames cannot establish exact tyre-to-kerb clearances."
- This agrees with the ledger's reading of t100 (`round14b/t9a_onboard.json`): the camera about 1.5 m from the apex
  paint, with the left edge about 12 m away.
- So the real car is close to the right apex and then close to the left apex. It uses nearly the full width between
  them and does not use the escape road.
- One frame per 50 m does not show whether its wheels go over kerb 24 or 25.

The owner's three options (the measured 1.5 m chicane margin as published, a lap-wide 2 m margin, an AI speed reserve)
are not visible in stills. Neither the judge nor this check can choose between them. Stills: onboard s3000 / s3050 /
s3100 / s3150, t9a_3000-3120.

## Where the judge contradicted the ledger's evidence

- **Contradicted, and the ledger is wrong (A14).** LEDGER part 2 reads "right s 2080, drag strip NW far wall ... a 2 m
  tyre bundle at its head (a cushion) | joined to the tyre bundle: ok". The judge saw a bare terminal, and the package has
  a zero-length bundle (work item 1).
- **Contradicted the ledger's claim and is right in part (B7).** The ledger says "The course's white edge line runs along
  the fitted edge across its mouth". It does run to s 3059, but in the stills it fades along the arc, and the onboard's
  marking is clearer.
- **Contradicted the evidence and is wrong (B4, B5, B9, B13, C6).** Each object it called EXTRA or misplaced is in the
  package from a cited onboard frame or capture.
- **Confirmed the ledger:** the removed T7-approach tyre run (A8; s2050 / s2100 show none); the far wall moved off the
  near paint (A6); the board wall at s 3165 joined (B15 / B16); T10's single wall (C12 / C13); the T1 cones as the owner's
  instruction, with none in the footage (A1).
