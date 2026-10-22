# Sonoma round 11 (22 Oct 2026): owner notes 63-69, the tyre-wall physics note, the rollover game note

Built on branch track-pipeline from eb5e3ad by the Opus build agent (Part A: the track; Parts B and C: physics and game in
a second commit). Not judged here. Evidence images (reference only, never committed) are under
`tools/track/compare/sonoma/round11/` (capture windows and strips) and `round11/stills/` (sim stills at the owner's poses,
`<note>_before.jpg` from the eb5e3ad package, `<note>_after.jpg` from this one).

Owner, on the rest of the track: "Other than that, Sonoma drives very well." Only what the notes name was changed.

## Package

- Published `public/tracks/sonoma` (stage 1 -> 2 -> 3, `--publish`): track.json sha256 1dfde4e757ab3180, registry rev
  ff9814637f (was 4804fb0170), length_m 4098.5 (was 4098.796). heightfield.bin, far_heightfield.bin, far_ortho.jpg are
  byte-identical to eb5e3ad's; ortho.jpg changed by the T10 grass zones only.
- Laguna stage-1 reproduction after the builder changes: track.json sha256 d4e8634710813961, heightfield.bin identical,
  the known `edge gate left` 0.105 m at station 46 (Acceptance 6): no leak.

## Note 69 and 64: the Carousel exit to T7 straight (geometry, the only geometry change)

Owner: "I don't think this section going to T7 is wavy like this" (69); "I don't think this line should be wiggly. It
should be straight" (64).

What the captures show (strips `strip_part0-2.png`, `axisL_drag*.png`, `axisL_T7road.png`, `win_1900_raw.png`): two
straight legs 11 deg apart, not one line. The drag strip (both lanes, heading 141.6 deg) from the Carousel exit to the
fork, then the T7 road (152.9 deg) whose left asphalt end leaves the drag strip's SW paint line at a vertex (config 1901,
current ~1909). The NE paint line runs parallel to the SW line at 18.3-18.45 m to config 1827 (current 1835) and then
curves in ~1.4 m toward the fork (every overlapping capture agrees).

Declared (config `straights`, all `local=True`): the drag-strip left (SW paint, RANSAC, `once`, config 1716-1878), the
drag-strip right (NE paint, `once`, `width_shared`, config 1716-1827) and the T7 road's left line from the vertex
(`parallel` to the T7 road's right line, config 1901-1984, joining the existing 1985-2095 entry). The feature
`('left', 1860, 2060, 'asphalt_end')` started 40 stations before the vertex where the SW paint line is the edge; inside
the local refit it starts at the vertex (`replaced_by_local` / `local`).

| | before (eb5e3ad) | after |
|---|---|---|
| drag-strip width, current 1725-1835 | 18.04-18.78 m (waving) | 18.26-18.43 m (one width, 18.30 m read from 280 of 299 readings) |
| left edge rms about its own line, 1725-1835 | 0.062 m (max 0.171) | 0.009 m (max 0.018) |
| right edge rms about its own line, 1725-1835 | 0.060 m (max 0.103) | 0.020 m (max 0.085, the join) |
| T7 road left edge rms about its line, 1910-2095 | 0.468 m (max 1.03; the free fit chorded 1-3 m inside the asphalt end) | 0.014 m (max 0.069) |
| lap length | 4098.796 m | 4098.500 m |

Measured caveat: on the saturation step between the asphalt and the tan dirt, the T7 road's asphalt end sits 0.2-0.9 m
inside its straight line at current 1938-1995 (a shallow fillet at the junction) and 0.3-0.6 m outside it at 2082-2098;
the line is kept straight per the owner (and one width with the road's right paint line).

**Edge-difference report** (every candidate polyline point's distance to the eb5e3ad polyline, by world position):

| polyline | max outside current stations 1650-2100 | p99 outside | max inside |
|---|---|---|---|
| centre | 0.0041 m (st 2166) | 0.0023 m | 1.047 m (st 1923) |
| left | 0.0065 m (st 2175) | 0.0033 m | 2.991 m (st 1925, the vertex corner) |
| right | 0.0038 m (st 2152) | 0.0022 m | 0.459 m (st 1922) |

How it stays local (builder change, config-gated, `centre.local` {window (1643, 2091) config stations, blend 15}): the
fitted method converges first without the local items (36 refits, the accepted path), then refits inside the window
only with every straight, holding the centre and edges outside in world position; the fit's gates are measured on the
held edges on those stations; then the stations are re-spaced uniformly (no refit). A plain re-run moved the lap by up to
2.6 m (9a, the T7 hairpin, the pit-out merge: the refit loop's limit cycles and the re-stationing).

Stage-1 gates: 25 ok, 0 FAIL (`fit left` observations within 0.25 m 90.3 % against the accepted build's 90.5 %; `fit right`
93.8 % against 93.4 %; edge gates left 0.047 / right 0.029 m rms; lap length ok). Two earlier attempts are on record:
the right line read first went 0.7 deg off (RANSAC from the red / white blocks, where the NE line itself is not detected,
to the paint; `axisR_cand.png`), and ending the left straight at the vertex fought the paint's turn into the fork (edge
readings 0.3-0.5 m outside at current 1887-1905): the left straight ends at config 1878.

## Note 63: the unused T7 (texture and the mouth kerb)

- The PWC lower hairpin road's T7 section (the normal T7, closed) was drawn in pale concrete (`surface='concrete'`); the
  captures (c20_s3960 / c20_s0000, `win_t7mouth.png`) and onboard 1:14 (t074) show the track's dark asphalt with a centre
  line: a `part_overrides` entry gives that part `asphalt`. `part_overrides` was read nowhere until now (the round-7e entry
  near the fork matched no part of this road and was a no-op; it is removed with a note, that place being the 'drag strip
  past the T7 fork' road, asphalt since round 7e); an unmatched entry now fails the stage.
- The kerb: the T7a island (O'Reilly) strip started at s 2208 and ran ~50 m across the open mouth of the normal T7; the
  captures show the blocks only round the island from its nose, and t074 shows the orange delineator posts across the
  mouth, no kerb (t072 / 1:12 shows the island tips' red / white blocks and, further, the Chute's cones): the strip starts
  at s 2258.8 (the edge point 0.19 m from the first block). The four delineator posts declared from t074 (s 2196-2212)
  stay; the island tip's own blocks stay drawn by its raised kerb line.

## Note 65: T10's sunken wall and the verge

- The wall: the owner's frame shows the T10-T11 boarded wall's far stretch with its top near the ground. Every barrier's
  base is the DEM at its own line (all within 0.01 m); the drawn ground is a 4 m mesh sampling the 2 m heightfield, so a
  wall along a narrow hollow stood under it: the T10-T11 boarded wall (barrier 27) by up to 1.06 m near s 3220 (on a 1.2 m
  wall), the T11 walls 43 / 44 by up to 0.99 / 0.79 m (25-34 % of their points). App fix (src/app/scene.ts): the mesh
  triangles under every barrier line are lowered to its base, every metre, before the ribbon stitch; physics unchanged
  (its ground is the heightfield). Stills `n65_T10_3160_*`.
- The verge: onboard 1:44-1:50 (t104, t106, t110) shows green grass on both sides of T10 to the walls and no painted sign;
  the ortho's verge was pale olive / tan (0.50-0.61, 0.51-0.62, 0.36-0.50; saturation 0.12-0.34), missed by the season
  tint. Ground colour zones (`season_tint.zones`, right s 3140-3330 m, left s 3140-3260 m, 0.5-12 m beyond the edges):
  now (0.45, 0.55, 0.31) / (0.40, 0.49, 0.25).

## Note 66: the infield building

From the T10-T11 right verge (the owner's frame: the TOYOTA / HUMBOLDT / SAVE MART / zMAX boards of wall 27 on the left,
wall 28 and its fence on the right) the long low building across the infield is the pit garages. Lidar (2022-24, DSM -
DEM): Pit garages north / south roof p50 6.1 / 6.0, p90 7.0 m against eave 4.3 / ridge 7.0 m; paddock garages p90 7.8 /
7.7 against ridges 7.8 / 7.7; the T10-T11 shed p60 5.6 against 5.6; the long shed east of the T10-T11 straight p60 4.6
against 4.5. Roof-like returns (multi-return share < 0.2, > 4 m) within 110 m of the garages that no footprint covers:
one, the fuel canopy (p60 6.4 m; declared 4.8 m + 1.2 m hip = 6.0 m). The taller blobs beside the long shed are trees
(multi-return 0.43-0.77). No building is too low by the lidar and none is missing: no change. (Outside the owner's view: a
34 x 20 m section at 7.0 m inside the OSM building at (502, -498), drawn at its footprint's p60 4.7 m; not changed.)
Stills `n66_infield_before.jpg` (a first pose), `n66_garages_after.jpg`.

## Note 67: the wall missing along the dark line

Owner: "Seems like there is a wall missing along this dark texture line. Without it, there is a tire wall that abruptly
starts, with an end that someone could smash into at speed. As a general rule, the wall transition shown in the sim
generally don't exist because they are extremely dangerous".

- The bare head: the T11-approach tyre wall (barrier 37) started at s 3398, 0.6 m beyond the right edge, 10.8 m from any
  other barrier.
- The dark line: `wall_measure.py --feature dark` on the guide (396,-110)..(425,-196.6) ENU, c20_s0990 / c20_s1045: 97 %
  picked, rms 0.65 m; kept from (403.5, -139), where it converges onto the tyres' head (north of it the picks run into the
  T10-exit dirt and tyre marks). Onboard 1:52 (t112): the pale wall with its catch fence angling in across the grass toward
  the edge; 1:54 (t114): the tyres stand in front of it at the edge. Placed: 'T11 approach, right: wall and catch fence
  onto the tyre wall (round 11)', concrete 1.1 m, fence 3.5 m (as the T10-T11 wall), 14 points, ending on the tyres' head.
- The gate: `exposedEnds` skipped every tyre run. Tightened: tyre runs are checked like every run; only a cushion (a tyre
  run of at most 12 m whose tail joins a rigid run) is exempt. Test added (bare tyre head fails; joined passes; a long run
  is no cushion). New catches on the published packages (list only): Sonoma 1 (this tyre wall, s 3398, fixed: now 20 / 20
  joined), Laguna 0 (its one exposed end, concrete osm:640173934 at s 3259, was already reported), Buttonwillow
  (buttonwillow branch ff2eb57) 2: the s 826 station surround tyres (3.7 m out) and the T3 station mound tyres (7.6 m out).

## Note 68: the texture before T11

The owner's frame: pale patches beside the car where the pit-in lane meets the track. Same cause as the pit-out lane in
round 10: the pit-in lane runs against the left edge (gap 0) from s 3522 to ~3635, and the track ribbon's left shoulder
rows (draping the ortho's lane paint) rose through the lane (`n68_left_before.jpg`). `track_shoulder_cut` left s
3515-3640 m. No box lines or paint-over at the pit-in; the pale area right of the track is the paved lot (real).

## Stage 3, gates and checks (the published package)

- Stage 3 / run_gates.ts / run_coverage.ts: edge, world continuity, profile, barrier gaps (min 0.31 m), containment (0
  escapes), pit connectivity, signs (0 misplaced), wall ends (20 / 20), tyre facings (0), coverage (0 MISSING, 0
  UNSUPPORTED, 30 dispositioned: one new `placed` line for the s 3335 right mast row, its kit mast 15.9 m behind it after
  the 0.30 m shorter lap moved its station from 3320.5 to 3319.3 m), pit lane: all ok.
- compare_packages against eb5e3ad's package: 380 / 380 matched, 0 missing, 0 extra, 0 height differences. Object counts
  +3: the note-67 wall and its fence, and one closed-road painted edge (the 2020 fast bypass, s 2807-2819) split in two by
  a 2 m gap: the edge paint is re-measured on the re-spaced stations (both pieces on the old line, median offset 0.0 m).
- Kerb sweep (`kerb_sweep.ts --track sonoma`): 87 traversals, max roll 8.0 deg, 0 past 15 deg, 0 rollovers; 20 with an
  advisory wheel lift.
- Tests: vitest 425 passed + 1 expected fail; 2 timeouts under machine load (another job running Blender / node at
  load ~150): `replay.test.ts` acceptance threshold (passes alone) and `ai_behaviour.test.ts` full field 2 laps (91 s
  alone against its 60 s limit, 95 s with the eb5e3ad collision code too: not this round). pytest 29 passed (the Sonoma
  manifest disposition count 30 -> 31). `npm run build` ok.
- Not re-run: the AI field pace (calibrate_field) and the on-pavement fixture (Laguna's); the geometry change is local.
