# Mid-Ohio round 8: the look of the land and the control tower

Opus 5.5, 27 Oct 2026, branch `mid-ohio` (from a7a80a8, package rev 748b55ca59). The owner drove the round-7 preview
(probe-h8coektf2, e59c488) and wrote: "I think Mid-Ohio drives very well. It doesn't completely feel like Mid Ohio (some
grass is missing or is inexplicably dark or gray, seems like there should be a lot more trees, or denser trees,
especially by the back straight and going through Thunder Valley). Control tower doesn't look like the control tower
(by the pit straight)". The road is accepted in feel: track.json, heightfield.bin and ghosts.json stay byte-identical
to round 5; nothing in the AI or the line changes.

## 1. Diagnosis (before any change)

### 1a. The grass

`r8/ground_classes.py` on the round-7 package ortho (`r8/ground_classes_r7.json`): the ground pixels 3-40 m beyond each
edge, outside the course, the pit lane and the paved zones, per 100 m band and side, classed green grass (G over R and
B, saturation >= 0.12, luminance >= 70), grey (saturation < 0.12), brown / dry (R >= G) and dark (luminance < 70).

| band | what the ortho has there | cause |
|---|---|---|
| s 600-1300, both sides (T1 exit to the Keyhole and back) | 46-98 % green, median ~(80, 100, 72) | the south row of NAIP tiles: a greener, brighter acquisition |
| almost all the rest (s 200-600 L, 1300-3400 L, 0-300 R and 1300-3500 R) | 0-7 % green; 44-99 % dark; median ~(47-65, 54-70, 46-56): a dull dark olive-grey | the middle and north NAIP tiles: their grass is darker and less saturated than the south row (raw tile medians: green share 0.25-0.38 vs 0.69-0.80, grass ~(79-84, 90-93, 79-82) vs (80-100, 100-113, 84-93)); the round-7 grade (one black point, gamma 1.25) then pushes most of it under luminance 70 |
| s 1300-1700 L (back straight, woods side) | 88-99 % dark | the woods' canopy and its shadows baked into the NAIP ground, with few modelled trees standing on them (1b) |
| s 0-200 L and 3400-3595 L / R | 37-44 % grey, 28-42 % brown | the paddock concrete and the sand traps: real ground classes, not grass |
| the closed roads (round 7b) | pale weathered apron | not grass; the boundary audit's tone item (round 7 B2), unchanged here |

The in-season reference: the 2026 clean captures' grass (3.4 M pixels over all 91 captures: median (86, 103, 87),
`r8/capture_grass.json`, the same overhead geometry as the ortho); the 360 lap (Jul 2025) and the N837 (Apr 2026) frames
show uniformly green grass along the whole lap (sampled frames: G over R by 11-18, over B by 30-60; camera-graded, so
used for the hue only). No near/far seam is the cause: the far ortho is the same NAIP. Finding: the dark and grey grass is
the NAIP's own dull tiles plus baked canopy shadow, not a wrong ground class; nowhere does the ortho show gravel where
the frames show grass.

### 1b. The trees

`r8/tree_density.py` (`r8/tree_density_r7.json`): the 2019 lidar canopy (1 m cells whose highest class-1 return stands
over 2 m above the class-2 ground) against the modelled crown discs, in bands 5-150 m beyond each edge, per 100 m.

| stretch | lidar canopy cover | modelled crown cover | ratio |
|---|---|---|---|
| back straight, left (s 1300-1800, the woods) | 0.54-0.66 | 0.07-0.14 | ~0.18 |
| back straight, right (s 1500-1900) | 0.00-0.07 | 0.00 | - (open infield) |
| Thunder Valley, right (s 2800-3000) | 0.28-0.30 | 0.09-0.11 | ~0.35 |
| T7-T9, left (s 2200-2600) | 0.20-0.48 | 0.06-0.13 | ~0.27 |
| Carousel, left (s 3200-3300) | 0.25-0.49 | 0.12-0.19 | ~0.42 |

Cause, from the round-7 build log: the lidar finds 3729 crown maxima, and the NAIP imagery check (a crown counts only if
30 % of the NAIP pixels under it are darker than the image's 35th percentile and green) rejects 2491 of them (67 %). On
this NAIP the grass itself is dark and dull (1a), so the canopy is not distinctly darker, and the 2019 survey is
leaf-off (multi-return canopy, thin crowns in the NAIP). The onboard frames show tree walls there: N837 t050-t058 and
360 t060-t070 left (dense woods behind the catch fence the whole back straight), 360 t104-t110 both sides (Thunder
Valley under trees). Modelled per 100 m (bands by nearest station): 11-29 trees on the back straight left against a
canopy cover of 54-66 %.

### 1c. The control tower

What it is (frames N837 t004 / t128-t129, Apr 2026; 360 lap t022 ahead / t024 left / h0046, Jul 2025): a square tower
behind the pit lane at the line, a dark brown shaft, two upper storeys of dark glazing wrapped by decks with white
fascia boards, a red hip roof with a mast and a flag. Lidar 2019 (1 m height map round (57, 9) ENU, round8 notes): the
roof 19 x 18 m (x 48..67, y 0..18), its eaves 17 m and its top over 20 m above the ground (24 m with the mast). OSM
1315208899 ('building=tower') is a 17.6 m square 8.6 m west of the lidar footprint (not used). What round 7 had: a
10.5 m square block of 4 storeys, 12.8 m, tan walls with window bands, a flat red roof (no hip, no decks, 4-5 m too
low). Side by side: `compare_sheets_r8/tower_r7_vs_real.jpg` (local). The starter's stand beside it (a boarded cabin on
black legs over the pit wall) is modelled as a blue box on a post: crude, but the owner's note is the tower. The pit
garages (round 7b) are not the tower.

## 2. The fixes (from the evidence; config declarations and opt-in builder / app rules)

### 2a. Grass: `scenery.grass_tone` (new opt-in builder rule, `build_scenery.grass_tone`)

After the season step, on the published ortho and far ortho only: grass pixels (green over red and blue, not sand,
luminance 18-170, mask smoothed over 4 px against the JPEG's 8-px blocks; on the near ortho not under the 2019 lidar
canopy or a roof, CHM over 1 m, soft-edged) take a target tone at their own relative luminance, the gain taken from the
grass's local mean (40 m Gaussian) so the bright south tiles and the dull north tiles land on the same tone, contrast
eased (0.7). Target (93, 110, 71): the luminance of the 2026 captures' grass (median (86, 103, 87) over 3.4 M pixels of
all 91 captures, `r8/capture_grass.json`) with the hue of the in-season frames (N837 Apr 2026, 360 lap Jul 2025: B / G
0.32-0.70); the first pass on the captures' own hue read grey-blue at hood level (sheet fwd_00, build 8). Result
(`r8/ground_classes_r8.json`): over all 72 bands the green share 0.15 -> 0.58 and the dark share 0.56 -> 0.19; the
remaining dark is real canopy shadow (back straight left) and the woods; sand traps and paddock unchanged. Nine ground
lines the lifted grass made visible were reviewed on crops and dispositioned (armco shadows, paddock road edges, a
field edge, the pit-in island; the gate stays strict and passes).

### 2b. Trees: `tree_imagery_check=False`, `tree_min` radius 2 m / height 5 m (the Buttonwillow rule)

The lidar's own crowns, without the NAIP check that rejected 67 % of them; poles, masts and posts kept out by crown size
(8 small crowns dropped, the two utility poles by `tree_mast_clear`); 3719 crowns (was 1238); seven inside the control
tower's eaves dropped (the hip block clears its eaves, opt-in). Coverage against the lidar canopy (`r8/tree_density_r8.json`):

| stretch | lidar canopy | modelled r7 (trees / 100 m) | modelled r8 (trees / 100 m) |
|---|---|---|---|
| back straight left s 1300-1400 | 0.66 | 0.15 (26) | 0.59 (118) |
| back straight left s 1500-1600 | 0.54 | 0.10 (11) | 0.45 (60) |
| back straight left s 1700-1800 | 0.54 | 0.07 (18) | 0.48 (94) |
| Thunder Valley right s 2800-2900 | 0.30 | 0.11 (10) | 0.28 (24) |
| Thunder Valley right s 2900-3000 | 0.28 | 0.09 (6) | 0.26 (20) |
| T7 left s 2300-2400 | 0.47 | 0.13 (34) | 0.38 (111) |
| Carousel left s 3200-3300 | 0.49 | 0.19 (101) | 0.41 (205) |

Near trees stand within the lidar box (the near ortho, ~600 m round the circuit); far trees beyond it unchanged (the
NAIP dark-canopy blobs, 7000).

### 2c. The control tower

One slender block ('Control tower', replacing round 7's 'Starter tower' and this round's first two-block attempt, which
the second judge rejected as a dark office cube): an 11 x 11 m tan shaft (#c4b29b, from N837 t129's overcast side
wall (105, 102, 109) and the 360 lap t024's sunlit (131, 128, 123), lightened for the renderer) to 17 m (the lidar
eaves), five storeys with dark glazing on the top two, two wrap decks 1.2 m out at 10.2 and 13.6 m (white and dark
rails: the open, railed observation levels of N837 t127-t129), a red hip roof 4 m out (19 m eaves, the lidar's 19 x
18 m roof) rising 4.5 m (21.5 m; lidar top over 20 m, 24 m with the mast). New opt-in app keys on the block kit:
`hip`, `wrap_decks` (absent on every other block). No signage (not legible). The manifest's 'placed' dispositions name
'Control tower'.

## 3. The second judge's round-7 findings (`review_mo_r7/judge.md`) and their disposition

| # | finding | fix / disposition | still (compare_sheets_r8_full/sim) |
|---|---|---|---|
| M1 | starter / control tower a dark flat cube | section 2c | fwd_s3550, row_s0012_left, pit_p0_0xx |
| M2 | T5 HONDA boards invisible | cause: every board run sat 0.3 m BEHIND its 1.2 m armco (`off=-0.3`; the round-7 armco is taller than the old single beam), so the armco hid them; all armco board runs now 0.45 m in front from the ground (`off=0.45, base=0`); proven with a pose facing a board (t5board) and the walk | row_s2051_right, row_s2105_right |
| M3 | T4 bleachers low and dark | `self_lit` (7b) + silver seats / risers (#dfe2e6 / #b4b8bd), 15 rows of 0.33 m (top 5.85 m: the frames' rows rise above the 3.5 m fence) | row_s1792_left, row_s1813_left |
| M4 | sheets made before the published build | the final walk and sheets are made FROM the published package after the last build; `compare_sheets_r8_full/index.md` records the rev, the scenery.json time and the walk / sheet times | index.md |
| m5 | T4 board run starts early | s 1915-1949 (360 t075.5) | row_s1935_left |
| m6 | pit-in banner run short | to s 3452 (360 t019) | row_s3422_left / row_s3426_left |
| m7 | barrels drawn as one box | three 0.9 m yellow cylinders (`tyre_stacks`, 360 t017-t018) | pit_p0_001 |
| m8 | PERMCO-bridge VELO too low | base 1.4 m, h 1.6 m on the fence (360 t108) | row_s2880_left |
| m9 | VELO at T11 missing | declared on OSM 956 s 3048-3058, high on the fence (360 t112) | row_s3053_right |
| m10 | station 5 post missing | a '5' number board on a post (N837 t074); manifest re-dispositioned | row_s2146_left |
| m11 | pylon face; white office at T5 | the building drawn plain (`building_overrides` plain, 360 t082: an open pavilion); the pylon's lit scoreboard face is not modelled (the kit has no digit board): open | row_s2105_right |
| m12 | video board on legs at s 1792-1813 right | not placed: N837 t059-t061 (Apr 2026) show no video board there; a temporary of the 2025 IndyCar weekend (360 t071) | - |
| m13 | infield structures s 1600-1616 R, s 1952 R | not placed: the s 1600-1616 dark board / scaffold and the s 1952 white covered structure appear in the 2025 360 lap only; N837 t056-t057 and t064-t066 (Apr 2026) show open infield; temporaries | - |
| m14 | road smear s 3300-3400; pit-out seam | `ortho_paint_over` pale and dark over s 3235-3295; pit lane `match_track_tone` k 0.5 -> 0.8 | back_s3300, pit_p0_023 |
| n15 | marshal tower yellow vs the 2025 dark cabin | kept yellow: N837 t054 (Apr 2026) shows the yellow tower; newer evidence wins | - |
| n16 | T11 exit kerb end | the capture scan ends the yellow at s 3203 (c20_s3160 / c20_s3200); kept | - |
| n17 | fence posts over the T9 white wall | not placed: N837 t096-t098 show the white wall with no catch fence over it; the posts in the 360 frame stand behind it (the OSM fence 1315208958 line, modelled) | - |
| n18 | T1 hospitality rejection | re-dispositioned 'not resolvable' (manifest): the red-roofed shelter (OSM 1315208908) has no measurable 2026 footprint or height | - |

Also from my own walk of the published package: the PERMCO bridge's banner faces were swapped (VELO faced oncoming
cars; now PERMCO / Pumps and Motors on the approach, VELO on the far face), the Keyhole board wall continued onto OSM 943
(s 963-1070, 360 t053-t055), and the pit wall's VELO banners are single-sided (`single`, opt-in: no mirrored text from
the lane).

## 4. Compare sheets of the published package, and the judge pass

`compare_sheets_r8_full/` (local): 356 stills (fwd 72, rows 215, back 36, pit 25, runoff 9) and 67 sheets, made after
the final build from `public/tracks/mid_ohio` (rev cf609d6a3e; index.md: scenery.json written 15:26:17, walk finished
15:28:23, sheets 15:28:29). Earlier passes kept for the record: `compare_sheets_r8_pass1..3` (each superseded by a fix
and a rebuild). Judged by this agent against JUDGE.md on all 67 sheets: the findings of passes 1-3 were fixed (bridge
faces, the Keyhole board run, the boards hidden behind the armco, the road smear, the T11 banner extent); on the final
sheets no MAJOR remains. Open: the pylon's scoreboard face (m11), the starter's stand still a boarded box on a post
(NOTE), the closed roads' apron tone (round 7 B2), the grass a little duller than July (between April and July
references). Boards are counted placed only where a still shows them (the C14 rule the second judge set).

## 5. Gates, proofs, registry, tests

`build_track.py --stage scenery --publish` (exit 0, 21 lines `[ok]`); on the package `run_gates.ts` exit 0,
`run_coverage.ts` exit 0. Every gate as round 7b's table (round7.md section 18), with ground lines 162 lines, 114
dispositioned, 0 open; coverage 251 rows, 0 MISSING, 0 UNSUPPORTED.

**Package rev cf609d6a3e** (registry `mid_ohio.rev`).

Identity: track.json, heightfield.bin, ghosts.json `cmp`-identical to round 5; Sonoma stage 3 from its published files:
scenery.json and far_heightfield.bin identical; Laguna stage 3 on its reproduction: all four outputs identical to the
b5343d7 builder's; structure soups of Sonoma, Laguna and Buttonwillow identical (`r7/soup_hash.ts`: f71411f3c2e78626,
e3b0c44298fc1c14, 3da76e09e950dd5a); Buttonwillow: `build_track.py --track buttonwillow --stage all --out tools/track/out/bw_idcheck` (rc 0, after the final build): all seven files `cmp`-identical to `public/tracks/buttonwillow`. CLIs on the package: `run_gates.ts`, `run_coverage.ts`, `edge_gate.py` exit 0; the build 21 lines `[ok]` (ground lines strict, 0 open). Tests: `npm run build` ok; full `npx vitest run` 64 files, 537 tests passed (no timeout this run).

## 6. Open

- The starter's stand's look (R6), the T5 pylon's scoreboard face (m11); the far trees beyond the lidar box are the NAIP blobs (unchanged).
- Round 7's open items stand (field, AI, pit-lane survey, T4 run-off raise, kerb height as an owner question).
