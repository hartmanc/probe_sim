# Sonoma round 14, part A: one surface for the T7 complex (owner, round-13 drive)

Owner, 23 Oct 2026, round-13 preview, hot-lap camera stopped on the T7 approach (~s 2090) looking into the complex: the
inactive paving on the left (the Chute / short-T7 road) on another level from the course with a ridge where the dark
block meets it; the island with the red / white kerbs reading as a trough, its blocks tilted on the rim; the blue / white
kerb run on the right and the paving beyond it stepping down; a dark lump of paving in the middle distance with a crease
across it. "We might have to deviate from the lidar scan ... The key thing is that the active and inactive track surfaces
actually go together in a sensical way that doesn't break immersion." Rule for the round: every paved surface touching the
course joins it with no step, ridge or trough, the ground between them on the same smooth surface; where the lidar
disagrees, the lidar loses.

## Cause (measured on the round-13B package, the driven surface as the app builds it: `compare/terrain_sample.ts`)

`profiles_before.png` (s 2080-2320 every 40 m, -60..+90 m lateral, height and height minus its 8 m trend) and
`heightmap_before.png` (hillshade, residual from a 10 m smooth, |second difference| at 1 m). Four sources, not one:

1. **Zones on their own levels.** A closed road's height is a 7-point linear fit across of the DEM, smoothed along it
   (`build_scenery.lane_parts`); the ground beside it is the raw DEM; the course's 5 m shoulder blends from the edge,
   flattening its cross-slope to zero at every paved edge. Where the 2022-24 lidar carries old paving edges, berms and
   grading, the three disagree: at s 2240 the T7 inside runoff steps 0.17 m at its edge, the drag strip's continuation
   lies 0.2-0.3 m below its own banks (a trough with lips), the junction ground carries 0.1-0.3 m bumps.
2. **A phantom paved plateau** (the "dark lump with a crease"): the T7 inside runoff's first four stations repeat one
   centre point (both edges clamped onto one track station). The physics reads a zero-length segment's lateral as 0, so
   every point whose nearest station it is counts as paved at that station's height: a plateau up to 0.58 m above the
   ground over the small island's nose (-404..-396, 420..438), drawn by the terrain mesh.
3. **The Chute dives into the creek.** The Chute crosses the creek on a bridge 10-80 m from its T7 mouth; the DEM is bare
   earth, so the zone was built on the creek bed: 26.6 m at the mouth, 21.6 m at the bottom, 28.8 m at the far abutment.
   The lidar's bridge-deck returns (class 17) are 26.8-28.5 m, up to 6.9 m higher. From the T7 approach the left-hand
   paving visibly falls away behind a crest.
4. **The kerbed islands on troughs.** The O'Reilly and small-island kerb lines stood on DEM hollows; kerb blocks tilted up
   to 11.7 deg from the surface round them.

Gate numbers on the round-13B package with the round-14A region (the same gates as below): pavement joins 138 of 930
boundary points over (max step 0.103 m, max cross-slope change 47 deg on the Chute's sides); surface smoothness max second
difference 0.170 m, deepest trough 0.47 m, highest ridge 0.59 m, 2738 + 3240 points over; kerbs 103 of 247 blocks over
(max tilt 11.7 deg).

## Mechanism (config-driven, `tools/track/terrain_override.py`, build-track skill 1.13)

- **Stage 1** (`terrain_override`, a list of regions): inside the polygon the heightfield (2 m grid) is ONE thin-plate
  surface: the course held, and its edge height continued with the edge third's cross-slope for `edge_hold` 1 m beyond
  each edge (C1), pulled to that continuation out to `edge_band` 4 m; beyond, a Tukey-biweight (IRLS) fit to the lidar
  ground with a 40 m cutoff wavelength (`smooth_m`; 8 % of nodes rejected, robust sigma 0.042 m); the Chute's bridge deck
  from the class-17 returns (20th percentile per cell; 336 cells with returns, 259 interior ones held), the creek bed within 8 m of the
  deck no data, its sides faded to the lidar over 6 m; outside the polygon held to the lidar (stiffening over 15 m), so no
  ditch or bank beyond the region moves. The surface is built from track.json as written (the physics' own arrays).
- **Stage 3**: scenery.json `terrain_override` ({regions: [{name, ramp 1.5, poly}]}); every paved part inside is draped
  on the surface (profile points = heightfield), and its zero-length stations are dropped (the plateau of cause 2).
- **Physics** (`src/physics/track.ts`, `packageSurfaceOptions`): inside a region the off-pavement surface and the paved
  parts are the heightfield itself (no 5 m shoulder blend, no dirt roughness), weighted in over `ramp` m inside the
  polygon; the course is unchanged. Without `terrain_override` every sample is bit for bit as before (test).
- **App**: `kerb_lines` blocks now stand each corner on its own ground (they were drawn level across at the higher side,
  which on a 5 % fall left a gap under the low side's 0.05 m skirt).
- The region (config `terrain_override`, 43 vertices): the junction and islands right of T7-T7a from the T7 apex island
  (s ~2110) round to the T7a exit (s ~2352), the drag strip's continuation to its fork, the T7 inside runoff, the
  O'Reilly island, the paddock lot left of T7-T7a to the wall below the T7a stands, the T7a outside paddock, the Chute
  from its mouth across its bridge (zone + 4.5 m); the course's edge + 1 m along T6-T7 and T7a-T8, so the creek bank left
  of T6-T7, the T7a stands' bank and the T8 bank stay lidar. Left out on purpose: the drag strip continuation SE of the T7
  apex island (s < 2110 abeam), which is separated from the junction by a 1.8 m bank under the T8 leg; inside the region
  the TPS lifted it up to 1.3 m and tilted it (tried, rejected). Its pre-existing zone lips are untouched.

## Gates (new, REQUIRED in stage 3; `tools/track/gates/terrainGates.ts` via `run_gates.ts`)

| gate | limit | round 14A (stage 3 of `out/sonoma_r14a`) |
|---|---|---|
| pavement joins: course edges and paved-part edges and ends in the region, every metre | step 0.02 m, cross-slope change 2 deg | 930 points (114 in the ramps, not gated): max step 0.0059 m, max change 0.52 deg, 0 over |
| surface smoothness: cross-profiles at every station in the region, 1 m spacing | second difference 0.01 m; 0.05 m below / above the line 5 m either side | 342 profiles, 20473 points: max 0.0098 m; trough 0.048 m, ridge 0.042 m, 0 over |
| kerbs on surface: kerb_lines blocks and the course's kerb strips in the region | tilt 2 deg from the surface round it; no gap under a block | 247 blocks: max tilt 0.51 deg, gap 0, 0 over |

The 0.01 m second-difference limit: a 1 % grade change per metre (vertical radius 100 m); paved lots are laid to ACI 330's
6 mm under a 3 m straightedge (5 mm per m^2 for a uniform bend), and their designed grade breaks (crowns, valley gutters)
change 1-2 % over a metre or more. The smoothness and trough numbers pass with little margin (0.0098 / 0.048); the
tightest points are the T7a inside edge at s 2290 and the drag strip continuation's island flank (s 2165 right, +70 m).

Every other stage-3 gate unchanged and passing (0 [FAIL] lines in the stage-3 log). Stage-1 gates pass (edge gate,
profile gate, as before).

## What changed in the package (public/tracks/sonoma, rev e4e8928b59, was a64834f45f)

- **track.json: byte-identical** (rebuilt by stage 1 from the raw inputs; the override does not touch it). **ghosts.json
  byte-identical** (stage 2 rebuilt). ortho.jpg and far_ortho.jpg byte-identical.
- heightfield.bin: 5915 of 501466 nodes changed, all inside the region and its margin; on the course, between profile
  stations sampled every 0.5 m at s 2080-2320, the driven height is unchanged (max |dz| 0). Off the course: p50 0.024 m,
  up to 0.32 m cut / 0.28 m raised in the junction, up to 6.96 m raised on the Chute's bridge (the deck).
  far_heightfield.bin follows (it copies the near grid).
- scenery.json: `terrain_override` added; paved_zones heights (the Chute's two parts, the drag strip continuation, the T7
  inside runoff, which also loses its 4 zero-length stations: 66 -> 62); heights only (plan positions identical) of 10
  barriers, 4 cone lines, 1 ground sign, both kerb lines, 7 landmarks, 3 paint lines, 2 light masts, the T7a terrace
  rows (1 cm) and trees.
- `src/scoreboard/config.ts` Sonoma rev e4e8928b59 (fresh boards for the new surface).

Not changed: Laguna (`git diff public/tracks/laguna_seca` empty; its config has no `terrain_override`, its scenery hash
is unchanged), Buttonwillow (not on this branch; its config has no `terrain_override`).

## Evidence

- `profiles_before.png`, `profiles_after.png` (after with the before in grey): s 2080, 2120, 2160, 2200, 2240, 2280, 2320.
- `heightmap_before.png`, `heightmap_after.png` (x -520..-300, y 290..490; the region dashed) and `heightmap_change.png`.
- `stills/*_before.jpg` (round-13B package; the before stills were taken with the committed kerb-line renderer) and
  `*_after.jpg`, the round-13B poses (walk_2080..2360 every 40 m, six turned poses, strip_continuation_to_T7, owner_135)
  and the owner's own pose `owner_r13_T7` (car on the centre line at s 2090, chase camera = the hot lap's start camera,
  `pose_walk.ts --camera` / per-pose `camera`). Clearest differences: owner_135 (the lump on the island nose gone, the
  kerb run flat), turn_2150_chute_left (the Chute level with the mouth, no crest and dive).

Open: the drag strip continuation SE of the region keeps its zone lips (bank-separated, not a join with the course); the
Chute's bridge is drawn as a road on a 6 m embankment (no deck structure); the stills are not judged (orchestrator).
