# Sonoma round 13, part B: the T7 complex ledger (owner note 135)

Owner, 23 Oct 2026, round-12 preview (`owner_drive_r3/owner_135_T7_complex.png`): "This T7 complex with un-used track looks
very bad. You should have a subagent whose only job it is, is to get this looking real. Not a mismatch of textures and
geometries." Rule of the same day: "if we are modeling textures in a long line on the ground, it's likely we are missing a
feature".

Scope: T7 (s ~2140-2200), the T7-T7a straight and the T7a hairpin (s ~2200-2330), and the roads, islands, barriers and
ground round them that the Lemons loop does not use (the Chute's T7 mouth, the short-T7 / PWC road, the T7 inside runoff,
the drag strip's continuation past the fork, the O'Reilly island, the paddock lot left of T7-T7a, the T7a outside paddock).
The raced track's edges, heightfield, ghosts and track.json are not touched.

Owner's pose (owner_135, matched in the sim): ENU (-404.3, 442.5), on the T7-T7a straight at s 2240 (0.7 m right of the
centre), the car turned ~80 deg right, heading 330 deg (looking ESE across the junction toward the drag strip), hood camera
pitched -2 deg (`stills/owner_135_*`).

## Evidence used

- 2026 clean z20 captures c20_s3850, c20_s3905, c20_s3960, c20_s4015, c20_s0000 (0.117 m/px; survey windows with a 10 m ENU
  grid in `survey/cap_*.png`, the model over them in `survey/capm_*.png`, over the package ortho in `survey/orm_*.png`).
  No capture covers the paddock lot west of x -505 and parts of the Chute west of the mouth (black in the windows).
- The package ortho (NAIP, 0.6 m/px; summer, an earlier year than the captures): `survey/ortho_raw_2200.png`,
  `survey/ortho_model_2200.png`.
- The March 2026 Lemons onboard RAZip6S84CM frames t064-t078 (1:04-1:18): t064 the pylons at the drag-strip mouth, t072
  the T7 post, the Chute mouth and the T7 island's grass, t074 the paddock left (dashed lane line, black tyre lines, the T7a
  terraces) and the cones / delineator posts across the short-T7 mouth on the right, t076 the small island's nose (red /
  white kerb, a mint-green painted band inside it, grass behind) with its delineator post.
- The owner's screenshot owner_135 and the round-12 package stills from the same poses (`stills/*_before.jpg`).

## What the sim showed (round 12 / 13A package, owner_135 and `survey/capm_-375_440.png`)

1. The NAIP's own junction paint (arrows, curved and cross lines from another layout year) and pale paving patches showed
   through the closed paved surfaces: the owner's "mismatch of textures". The 2026 captures show plain dark asphalt there.
2. Two closed-road strips laid along OSM ways through the junction ('T7 inside runoff', 'PWC lower hairpin' T7 section)
   took their paving edges and their painted edge lines from `paint.measure`, which has no road edge to find in an open
   junction: five white lines wandered across the junction and the strips' edges cut across the islands (the "mismatch of
   geometries"; yellow and green tangles in `survey/capm_-375_440.png`).
3. Paving drawn as zones (dark asphalt shading) next to paving left as ground (the NAIP's pale paving): a tone seam along
   every zone edge, at the Chute mouth, the junction and the paddock.
4. The O'Reilly island was a red panel with white letters over the NAIP's red patch: the 2026 captures show a dark painted
   island with white outlined O'REILLY lettering inside red / white kerb blocks.
5. The small island's raised kerb line stood ~1 m off its painted blocks.

## Ledger

| # | feature | evidence | in the sim (before) | action | disposition |
|---|---|---|---|---|---|
| F1 | Raced road: T7 (s 2140-2200), T7-T7a straight, T7a hairpin (s 2200-2330); edges, kerb strips (T7 island apex, O'Reilly hairpin side, T7a exit outside) | c20_s3850..s4070; t072-t078 | edges fitted (round 11), kerb strips placed (rounds 7b-11) | none (outside this round's remit: edges are the owner's) | unchanged; byte-identical track.json, heightfield, ghosts |
| F2 | Junction pavement inside T7 / T7a (between the T7 apex, the T7 island tip, the small island tip and the O'Reilly island; the short-T7 / PWC road) | c20_s3905 / c20_s3960: plain dark asphalt, no arrows; white line along the islands; t074 cones across the short-T7 road, delineator posts on the open mouth | zones 'T7 inside runoff' (66 st) and 'PWC lower hairpin' T7 part (59 st) with paint-measured edges crossing the islands; 5 painted edge lines (paint.measure) across the junction; the NAIP's paint and patches showing through (owner_135) | config: both roads `paint=False`, `edges_from_paint` off (no painted edge exists in an open junction); the ground under all 2026 paving retextured (F16) | done: both junction roads paint off; five stray lines gone; the T7 inside runoff zone brought in to the 2026 paving (38 edge points, smoothed) so it no longer lies on the islands; the PWC lower hairpin zone REMOVED (its OSM line loops round the small island's nose: it lay on the island and over the runoff zone, and the two zones' shoulders painted raw ortho over each other, the pale band of owner_135); its containment allowance replaced by one to the drag-strip continuation across the same open junction (s 2208-2278 right, evidence in the entry). The junction paving left as ground now drives as ground grip (off the course, lap invalid there anyway) |
| F3 | Drag strip past the T7 fork (closed) | c20_s3630..s3905: asphalt, white edge lines both sides, a light centre line; t064 pylons at its mouth | zone with paint-measured edges (on the lines), edge lines drawn; centre line missing; NAIP texture under it | centre line measured on the captures (`paint_lines_declared`); ground retextured (F16) | done: centre line measured (175 m, 85 % picked, rms 0.02 m) and drawn; ground retextured |
| F4 | The Chute's T7 mouth (closed) | c20_s3850 / c20_s3905: dark asphalt ~15 m wide between a pale strip (NW) and a low wall with a parked trailer (SE); t072 small orange cones and a low black tyre line across it | zone strip (6 m half-width, NAIP width) narrower than the paving; its two painted edge lines wandered into the parked trailer; NAIP shows pale paving and the long shadows of parked trailers | the part's painted lines off (`part_overrides` paint False, new key); ground retextured (F16); cones and tyre line kept | done: the mouth part's two wandering lines gone (part_overrides paint False); its zone brought in to the 2026 paving (36-44 points); ground retextured; cones / tyres kept |
| F5 | Paddock lot left of T7-T7a (10-80 m left of s 2160-2250) | c20_s3850..s3960: grey asphalt, parking-bay lines, a dashed lane line along the course, the long white line under the T7a stands (the round-5 wall), the movable Jersey line (owner, round 7c) | terrain with the NAIP's pale paving, a NAIP-year temporary structure and its shadow (ground-lines disposition s 2177-2209, 43-48 m left) | ground retextured to the paving tone (F16), the NAIP object removed with it; barriers kept | done: paddock paving retextured; the NAIP object and its ground-lines disposition (s 2170-2215) gone. Left: a few NAIP patches where the 2026 captures show trailers or lighter paving stay as NAIP (open item) |
| F6 | T7a outside paddock (left of s 2255-2320, 10-35 m) | c20_s3960 / c20_s4015: dark asphalt to the grass of the bank, trailers and a tent parked (event) | terrain with the NAIP's pale paving; its edge with the grass was a ground-lines disposition (s 2287-2310, 27-34 m left) | ground retextured (F16) | done: retextured to the dark paving; its ground-lines line and disposition (s 2280-2315) gone. Left: two pale NAIP squares under the 2026 tent / trailers (open item) |
| F7 | O'Reilly island (inside the T7a hairpin) | c20_s3960 / c20_s0000 at 0.05 m/px (`survey`, oreilly window): dark painted island, white outlined O'REILLY lettering ~15 x 6 m reading NW, red / white kerb blocks all round | ground sign with a RED panel (from the NAIP's red patch, round 7b) over the NAIP's red / pink island | island interior retextured to the dark paving (F16, kerb band included); the sign's panel removed: white lettering only | done: island interior dark paving (fill 'paving' over its measured outline), the O'Reilly sign without its red panel (white lettering) |
| F8 | Small island (between the drag-strip continuation and the short-T7 road) | c20_s3960: dirt, red / white blocks along its NE edge and round its nose, a dark green patch at the nose; t076 red / white kerb with a mint-green band inside, grass behind | kerb line ~1 m off the blocks; the junction strips' edges ran onto it | kerb line re-measured on the blocks (`wall_measure --feature bright`); the strips fixed by F2 | done: kerb line re-measured round the nose and the NE edge (60 m, 81 % picked, rms 0.18 m); the nose's green band filled (#5aa586, onboard t076); no zone lies on it now |
| F9 | T7 island (between the T7 road and the continuation) | c20_s3850 / c20_s3905: kerb blocks round its NW tip; t072 green grass | track kerb strip on the apex side; island ground from the NAIP + season tint (green) | none: the tip's blocks on the apex side are the track's strip; the NE side shows a white line (the continuation's edge line, drawn) | no change |
| F10 | Cones and posts closing the unused roads | t064 pylons (drag-strip mouth), t072 Chute-mouth cones, t074 cones across the short-T7 road, t074 / t076 delineator posts on the open mouth and the island nose | all placed (rounds 5-7f) | none | no change |
| F11 | Barriers: T6-T7 wall to the T7 post, T7 approach tyre wall, the Chute's T7 mouth tyre line, the movable Jersey and its tyre facing, the wall below the T7a stands, the T7a tyre line and low wall at the terraces' foot, the T7a-T8 tyre line, the drag strip NW far wall, the T8-8a wall to the PWC road | captures (wall_measure, rounds 5-7) and t070-t078 | placed; wall-ends, joins, run-gaps gates pass | checked on the ortho for lines beside them (ground-lines gate, F17) | checked: no barrier-related ground line in the complex (gate: 0 open); barriers unchanged |
| F12 | T7 marshal post (raised white hut on legs, left at the wall end) | t072; c20_s3905 | placed (round 7) | none | no change |
| F13 | Boards: TOYOTA on posts above the T7 approach wall, PIRELLI / red boards on the low wall at its end | t070 / t072 | placed (round 5-7) | none | no change |
| F14 | T7a hill terraces and their top fence | t074; captures | placed (rounds 6-8) | none | no change |
| F15 | Ground tones: islands and banks | t072 / t076 green grass on the islands; t074 golden grass on the T7a bank | NAIP + season tint (green) | none | no change |
| F16 | NEW: the ground under the complex's paving | the 2026 captures' paving (dark, unsaturated asphalt with its white paint and red / white kerb blocks) | NAIP paving of another year: pale, painted arrows, parked-trailer shadows, red island | new config step `scenery.ortho_pave` (stage 3, after the post steps): inside a declared region polygon, the paving mask is read on the 2026 captures (NAIP pavement rule where no capture covers), closed over parked vehicles and paint; the raced track's own paving is excluded. Under the paved zones (closed roads, drawn with the road shader) the ortho takes the track asphalt's own ortho tone; under paving left as ground it takes the tone the road shader renders, so the two read as one surface; a fine grain from the track's ortho; no paint kept (the 2026 lines are drawn as geometry) | done: config scenery.ortho_pave (new, config-gated builder step after the post steps): 17378 m2 retextured in the complex, 407 m2 on the O'Reilly island, 26 m2 green nose; track tone (127, 141, 148) under zones, ground tone x (0.87, 0.78, 0.81) calibrated on the renders (track 110 / 110 / 120 vs ground paving 76 / 85 / 98 at the first try), ground tone also under the track ribbon's 5 m shoulders (track_shoulder) which show the ortho raw |
| F17 | Long lines in the ground texture (the owner's rule) | ground-lines gate on the package ortho | 2 in-complex dispositions (s 2177-2209 NAIP object; s 2287-2310 paving edge) | re-run after F16; dispositions dropped where the line is gone | done: 37 lines, 22 on a feature, 15 dispositioned (the two complex dispositions dropped: their lines are gone), 0 open |

## Results (stage 3 into tools/track/out/sonoma_r13b, published to public/tracks/sonoma)

Changed in the package: scenery.json (paved_zones: the Chute T7 part and the T7 inside runoff clipped, the PWC lower hairpin
zone removed; paint_lines: 7 junction / Chute-mouth lines removed, the continuation centre line added; kerb_lines: the small
island re-measured; ground_signs: O'Reilly without its panel) and ortho.jpg (the complex retextured). track.json,
heightfield.bin, ghosts.json, far_heightfield.bin, far_ortho.jpg byte-identical to round 13A. Registry rev 0837e8c746.

Builder: `build_scenery.ortho_pave` (stage 3, called by build_track after the post steps when the config has
`scenery.ortho_pave`) and `closed_roads[].part_overrides[].paint=False`; both config-gated (no other track config has the keys).

Stills: `stills/*_before.jpg` (round 13A package) and `*_after.jpg`, same poses: owner_135 (2000 x 965, the owner's
framing), walk_2080..2360 every 40 m, six turned poses (car turned 60-90 deg: the Chute mouth, the junction, the paddock,
the islands, the O'Reilly island, the T7a paddock) and one on the continuation looking at T7; top-down ortho crops
`topdown_T7_complex_{before,after}.png` (raw) and `_model_` (with the model drawn). Survey windows in `survey/`.

Open: (1) NAIP patches remain where the 2026 captures show parked trailers / a tent / lighter paving (paddock, T7a
paddock): the mask does not call them paving; (2) the junction paving off the zones drives with ground grip; (3) the
retextured ground paving carries the terrain's ground grain close up, finer than the road shader's asphalt; (4) the
dashed lane line in the paddock (t074) is not drawn (no dashed paint key).
