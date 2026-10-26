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

Two blocks (structures 'Control tower shaft' and 'Control tower'), replacing round 7's 'Starter tower': the shaft 10 x
10 m to 10.5 m (3 storeys, dark brown, one glazed band at the top storey), the upper block 13 x 13 m from 10.5 to 16.8 m
(2 storeys of dark glazing) wrapped by two decks 1.5 m out with white 1.1 m fascia rails, a red hip roof 3 m out (19 m
eaves, the lidar roof 19 x 18 m) rising 5 m (top 21.8 m against the lidar's over 20 m). New opt-in app keys on the
block kit: `hip` and `wrap_decks` (absent on every other block). Typed signage only: none (the fascia lettering is not
legible in the frames). The manifest's 'placed' dispositions now name 'Control tower'.

## 3. Compare sheets and judge (round 8, the changed places)

`compare_sheets_r8/` (local): 82 stills (forward every 50 m, side views at the inventory rows, back every 100 m) over
the back straight (s 1450-1950), Thunder Valley (2800-3100) and the pit straight (3450-60), plus
`tower_r7_vs_real.jpg`; 17 sheets. Judged by this agent against JUDGE.md (the second judge's round-7 findings are to
come; the round stays open for them):

| # | sheet | s | finding | status |
|---|---|---|---|---|
| R1 | fwd_00, fwd_02 | 0-1900 | grass read grey-blue after the first pass (captures' hue) | fixed: target hue from the frames |
| R2 | fwd_05, side_00 | 3500-3596, 0-50 L | tower: a box with a flat roof (r7) | fixed: shaft, glazed upper block, decks, red hip roof; matches N837 t127-t129 and 360 t024 in massing and colour |
| R3 | fwd_05 | 3550 L | a lidar crown growing out of the tower roof | fixed: trees cleared under the eaves |
| R4 | fwd_00-02 | 1450-1900 L | the woods wall along the back straight | ok: dense trees behind the fence as N837 t052-t060 / 360 t064-t074 (the real trees are leaf-off in April) |
| R5 | fwd_03-04 | 2800-3100 | Thunder Valley trees | ok: trees both sides, sparser on the right as the lidar has it |
| R6 | side_00 | 0 L | the starter's stand is a blue box on a post (real: a boarded cabin on black legs) | open (not the owner's note) |
| R7 | fwd_02 | 1750-1900 | grass a little duller than the 360 lap's July green | accepted: between the April (N837) and July references |

## 4. Gates, proofs, registry, tests

`build_track.py --stage scenery --publish` (exit 0, 21 lines `[ok]`); on the package `run_gates.ts` exit 0,
`run_coverage.ts` exit 0. Every gate as round 7b's table (round7.md section 18), with ground lines 162 lines, 114
dispositioned, 0 open; coverage 251 rows, 0 MISSING, 0 UNSUPPORTED.

**Package rev 9538d19a7d** (registry `mid_ohio.rev`).

Identity: track.json, heightfield.bin, ghosts.json `cmp`-identical to round 5; Sonoma stage 3 from its published files:
scenery.json and far_heightfield.bin identical; Laguna stage 3 on its reproduction: all four outputs identical to the
b5343d7 builder's; structure soups of Sonoma, Laguna and Buttonwillow identical (`r7/soup_hash.ts`: f71411f3c2e78626,
e3b0c44298fc1c14, 3da76e09e950dd5a); Buttonwillow stage all into `tools/track/out/bw_idcheck`: see section 5.

## 6. Open

- The second judge's round-7 findings (to come; this round stays open for them).
- The starter's stand's look (R6); the far trees beyond the lidar box are the NAIP blobs (unchanged).
- Round 7's open items stand (field, AI, pit-lane survey, T4 run-off raise, kerb height as an owner question).
