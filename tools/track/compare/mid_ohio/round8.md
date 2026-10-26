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
