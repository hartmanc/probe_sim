# The object kit (build-track stage 3)

Every object a circuit package can carry, the config key that places it, its parameters, the evidence it needs, and one
reference still from the accepted Sonoma package (registry rev b8a51e2cfa, accepted by the owner on 20 Oct 2026: "drives
and feels like Sonoma"). The kit is the vocabulary of stage 3. A circuit uses an object only where its evidence shows
one (no object without a cited `src`; manifest rule). An object the kit lacks is a builder change (a new config key plus
an app generator), never a hand edit of scenery.json.

Every entry carries `src` naming its evidence: a clean z20 capture `c20_…`, an onboard time `m:ss` / frame `t###`, a
Street View panorama id, OSM, or the lidar. Heights carry `h_src` with a method from `tools/track/compare/HEIGHTS.md`.
Colours come from the most recent footage. Positions are lat/lon measured on the clean captures
(`compare/wall_measure.py`, `capwin.py`, `kerb_detect.py`, `terrace_measure.py`), or stations along an edge where the
key takes `s`. Source precedence when sources disagree: recent onboard > 2026 satellite > NAIP > OSM > lidar.

**Stills:** `tools/track/kit/stills/<object>_sonoma.jpg` (local only, git-ignored; 32 stills). Poses are in
`tools/track/kit/sonoma_poses.json` (tracked; x, y in Sonoma's ENU frame, heading in rad, pitch in deg, z sampled from the
drive surface). To retake one or all after a kit change:

```sh
python3 -I tools/track/kit/make_kit_poses.py            # rewrites sonoma_poses.json from the package (same instances)
npx vite --port 5180 --strictPort &                     # dev server of the worktree that holds the package
npx tsx tools/track/compare/pose_walk.ts --track sonoma --poses tools/track/kit/sonoma_poses.json \
    --out tools/track/kit/stills --tag sonoma --port 5180
```

## Barriers (scenery.json `barriers`; collision runs; app end caps on every rigid run)

| object | config key and parameters | evidence it needs | still: pose (x, y, heading, pitch) |
|---|---|---|---|
| Concrete wall with end caps | `scenery.declared_walls[]` {name, kind 'concrete', latlon (measured line), h, h_src, fence, color, cut, drop_within, src}; OSM walls via `osm_barrier_overrides` {kind, h, fence, color \| drop, src}. Caps close both ends (app). | a bright band picked by `wall_measure.py` (% picked, rms in `src`) and confirmed on the onboard; height off the hood line / Jersey 0.81 m / Street View scale; colour from the 2026 onboard | wall_concrete_endcap: (178.28, -74.99, -2.045, 0), the pit-wall nose at T1 |
| Wall with catch fence | same entry, `fence` = fence height above the wall top (m) | fence posts in the onboard (3-4 m posts, curved tops); the gate counts the fence as a fence object | wall_catch_fence: (407.91, -128.84, -2.778, 5), T10-T11 right |
| Jersey barrier | `declared_walls[]` kind 'concrete', h 0.81-0.9 m, colour (red / white separation Jersey: #c9473e) | the Jersey profile in the onboard; the line on the captures | wall_jersey_impact (below) |
| Armco | `declared_walls[]` / OSM kind 'armco' (Laguna) | Armco rails in recent footage; none at Sonoma (no still: retake from Laguna) | none at Sonoma |
| Stacked tyres (tyre wall) | `declared_walls[]` kind 'tyres', h, color (#161616 black / #dedede white), `stack` (tyres per stack, else round(h / 0.23)) | a dark (black tyres) or bright (white-wrapped) band on the captures; the stack height and colour in the onboard | tyres_black_stacked: (239.44, -31.57, -1.833, 0), 9a right; tyres_white_stacked: (478.8, -458.99, -1.379, 0), T11 hairpin |
| Tyre cushion at a wall head | a short `declared_walls[]` kind 'tyres' run ending on the wall's first point (wall-ends gate: "joined") | the dark section at the head of a wall in the onboard | tyre_cushion_head: (-52.83, 115.16, -2.741, 0), T6-T7 left |
| Tyre facing on a wall | `scenery.tyre_facings` {reach 2.6, off 0.55}: tyre points within reach of a wall move onto its track face | tyres in front of a wall in the onboard (tyre-facings gate fails a tyre run parallel 0.8-2.5 m off a wall) | movable_jersey_facing (below) |
| Movable barrier | `declared_walls[]` with the owner's or footage placement in `src`, flagged **movable** in the manifest | in road-race footage, absent from the capture (taken at another event) | movable_jersey_facing: (-429.22, 415.98, 2.464, 0), T7 paddock Jersey + black facing |
| Fence (standalone) | `declared_walls[]` kind 'fence', fence = height; terrace top fences from `terraces` | the fence line in the onboard; on a bank top the lidar DEM crest | fence_standalone: (-89.93, -5.95, 1.915, 5), Carousel left |
| Impact barrier | `scenery.impact_barriers[]` {wall (declared name), end 'start' \| 'end', w, d, h, color, src} (landmark `impact`) | the water / foam block at a wall nose in the footage | wall_jersey_impact: (487.61, -374.42, 0.324, 0), pit-in separation nose |

## Free-standing objects (scenery.json `landmarks`, drawn; blocks and huts also collide)

| object | config key and parameters | evidence it needs | still |
|---|---|---|---|
| Cones by colour and size | `cone_lines_declared[]` {latlon (the painted line they stand on) \| side + s + off, spacing, size, color, src}; `pit_exit_cones` {latlon, spacing, color, size}; `closed_roads[].mouth_cones` {near, src} | cones in the footage: colour, size (0.5 / 0.7 m), spacing; the line measured on the captures; `style: 'delineator'` = a tall pylon post (1.0 m, orange, white bands; Sonoma T7 fork, round 7e) | cones_orange: (-509.92, 150.68, 3.134, -5), Chute mouth; cones_yellow_small: (97.96, -65.02, -1.52, -5), pit-out blend |
| Tyre stack | `scenery.tyre_stacks[]` {latlon, h, w, style 'tyres' \| 'blocks', color, src} | a stack in the onboard with its place on a capture | tyre_stack: (-48.66, 122.35, 0.473, 0), Carousel-exit mast base |
| Concrete block (striped / plain) | `scenery.blocks[]` {latlon, w, d, h, style 'striped' \| 'plain', color, src} | the block in the onboard (higher precedence) or its outline on the capture | block_striped: (487.74, -448.39, 2.261, 0); block_plain: (478.52, -457.66, -1.398, 0), T11 |
| Marshal hut | `scenery.marshal_posts[]` {name, latlon, h (deck top), color (band), src}: deck on legs at h - 2.6 m, open-front hut, roof overhang, railing; a measured footprint (round 8, Sonoma 8a tower) adds `w` x `d` (hut across x along the facing; the roof seen on a capture is 1.2 m larger each way), `heading_deg` (the bearing the open front faces; absent: the nearest track point) and `roof` (colour; absent: white); `style: 'deck'` (round 9, Sonoma 8a): a solid lower storey (`color`) to a sill 1.0 m over the deck level, an open viewing deck (posts, rails, dark floor) under a broad flat roof slab overhanging 0.9 m at the front, roof top h - 0.19 m | a roofed hut in the onboard / owner frames, its roof and shadow on a capture (event trailers look alike: confirm on footage) | marshal_hut: (-203.17, 53.64, -2.568, 5), T6 hilltop |
| Light mast | `scenery.light_masts[]` {latlon, h, src} (landmark) or `structures` type 'mast' {at [(lat, lon, h)], heads, src, h_src} | an isolated lidar spike (DSM - DEM > 15 m) confirmed by a base and long shadow on a capture window | light_mast: (-163.7, 272.81, -2.378, 18) |
| Boards with typed names (on a wall) | `scenery.wall_boards[]` {wall, s (from, to), h, base (posts; none = on the wall), names [(text, bg, fg), ...] as tuples (a 'NAME\|#bg\|#fg' string here renders one letter per panel; the re-derivation of 20 Oct 2026 hit this), panel, src}; `bridge_banners` {osm way: ['NAME\|#bg\|#fg']} | the names and colours the recent footage shows per run, typed (no logo artwork); the run's start and end stations from the footage | boards_on_wall: (302.46, -28.19, 1.463, 3), T10 entry; bridge_banners (below) |
| Ground sign | `scenery.ground_signs[]` {latlon, length, height, heading, text, fg, bg, src}: typed text on a decal draped on the ground | a painted logo legible on a clean capture (illegible ones are not placed) | ground_sign: (-354.87, 448.13, -2.554, -5), O'Reilly at T7a |

## Structures (config top-level `structures`, `build_structures.py`, app `src/app/structures.ts`)

Every item has `src` and `h_src`. Footprints come from OSM (`osm=`) or lat/lon on the captures. Heights come from lidar
profiles across the outline (DSM - DEM every 2 m), checked against storeys. `suppress_osm` lists the OSM boxes a
structure replaces.

| object | parameters | evidence it needs | still |
|---|---|---|---|
| Grandstand | type 'grandstand': front line (t0, t1), rows (n, rise, riser, depth, seat), base, suites (deck, glass, roof, lights), tower, towers (stairs), aisles, colours | seat field on the captures, lidar profile, the recent footage for the look | grandstand: (222.21, -107.75, -2.242, 8) |
| Hillside terrace | `scenery.terraces[]` {name, osm, front / back (measured with `terrace_measure.py`), run (row pitch), src}; dressing `structures` type 'terrace_dress' {terrace, bench, aisles, shades, rail} | the row texture on the captures (period 0.85-1.45 m), the DEM crest; OSM only for rays the captures miss | terrace: (-450.26, 48.07, -2.59, 10), T3a-T4 |
| Garage row | type 'garage' {osm, eave, ridge, roof, wall, trim, trim_h (0: no band), windows, doors, side, mono, band {z0, z1, color} (round 9: a continuous band on all walls)} | OSM outline, lidar eave / ridge, roof and wall colours from the recent footage | garage_row: (389.07, -301.11, -2.833, 3), pit garages |
| Flat block | type 'block' {osm, h, storeys, parapet, band, roof, wall} | storeys in the footage (3.2 m each, HEIGHTS.md), lidar flat top | flat_block: (372.75, -238.89, -2.571, 3), T12 building |
| Fuel island | type 'fuel' {osm, h, canopy, fascia, fascia_color, hip, hip_color, islands, posts, pylon, pylon_at} | canopy on the capture, lidar edges, the pit-lane video | fuel_island: (425.77, -444.96, -2.712, 3) |
| Structure boards | type 'boards' {side, s0, s1, lat (from, to), h, panel, names, colors} | boards on the pit wall in the pit-lane video | boards_structure: (318.77, -185.14, -2.212, 0) |
| Scoring tower | type 'scoring_tower' {at, heading_deg, h, w, d, head, plinth, color} | isolated lidar spike plus the capture's base and shadow, the footage for the shape | scoring_tower: (-53.58, 20.91, -0.615, 14) |
| Round canopy | type 'canopy' {at (lat, lon), d, h (roof at the centre), hole (open centre), tilt_deg, tilt_bearing, color, post_color, posts, deck {h, d, color} (a raised round terrace)} (round 9) | the disc and its colour on a capture, the lidar for the roof and terrace heights, the footage for the shape | none |
| Pit-box lines | type 'paint' {runs [(a, b, pitch)], w, depth, color} | the white-line peaks along a straightened capture strip of the lane | none (seen in the pit sheets) |
| OSM building | (no key: OSM footprint, robust lidar height `building_height_robust`, `building_overrides` {osm \| contains, h \| drop \| plain, src}, `building_evidence`) | lidar p60 above ground; newer evidence overrides with a logged entry | osm_building: (501.06, -425.3, -0.006, 3) (the shed behind the T11 boards) |

## Bridges and surfaces

| object | config key and parameters | evidence it needs | still |
|---|---|---|---|
| Bridge with abutments | OSM `bridge=yes` way, deck from class-17 lidar; `scenery.bridge_stairs` (abutments from the DEM to the deck, stairs along the way); `bridge_banners` | OSM way, lidar deck, the footage for piers and fascia names | bridge_abutments: (-21.18, -101.34, -0.852, 5); bridge_banners: (-21.8, -90.03, -2.414, 4), T2 footbridge |
| Kerb strip | `scenery.kerbs_declared[]` {side, a, b (lat, lon on the edge), colors \| palette name, off, kind ('kerb' \| 'blocks'), name, src}; `scenery.kerb` {width, stripe_m, colors, palettes, profile {height, face, back}} | the block pattern from `kerb_detect.py` on the clean captures, confirmed on `capstrip.py` and the onboard; profile from the feel and Street View | kerb_strip: (148.79, -65.99, 1.438, -6), T1 exit |
| Raised kerb line | `scenery.kerb_lines[]` {latlon (on the kerb paint), src}, drawn at the track's kerb height | the island kerb paint on the captures | kerb_line_raised: (-360.52, 436.53, -2.787, -6), T7 islands |
| Declared paint line | `scenery.paint_lines_declared[]` {latlon, width, double, color, t, src}; `edge_line_cut` {side, s, why} | the painted line measured on the captures (merge lines, blend lines), its colour in the footage | paint_line_declared: (117.74, 73.16, -2.267, -6), pit-out double yellow |
| Closed-road surface | `scenery.closed_roads[]` {name, ways, half_width, max_half, surface 'asphalt' \| 'concrete', paint (edges by paint.measure), edges_from_paint, cones, mouth_cones, src}; `closed_roads_clip_walls`; allowed runoff in `gates.allowed` | OSM ways, the surface and painted edges on the captures, cones at mouths only where the footage shows them | closed_road_surface: (105.88, 65.12, -0.852, -3), 2020 bypass |
| Paved runoff | `closed_roads[]` with `cones=False` (open) or `paved_runoff` (Laguna), `aprons`, `shoulder_zones` | paved runoff in the onboard, its extent on the captures | paved_runoff_surface: (-374.15, 425.34, -0.691, -3), T7 inside runoff |
| Paved area | `scenery.paved_areas[]` {osm, name, surface, src} | a parking or paddock area whose ortho shows vehicles | none (paddock behind the garages) |
| Pit lane | `pit_lane` {lane {source, match_track_tone}, walls, boxes, buildings, furniture}; `pit_lane_clip_walls` | the pit-lane video end to end, the captures for walls and the box line | the pit sheets of `camera_walk.ts` |
| Season tint | `scenery.season_tint` {enabled, green, warm, bright, sat_max} (published ortho / far_ortho only) | the footage's season against the NAIP's | none |

Count: 36 kit objects (barriers 10, free-standing 7, structures 9, bridges and surfaces 10) and 32 stills. Some
objects have two stills (black and white tyres, orange and yellow cones, striped and plain blocks, the bridge's
abutments and banners). Armco, the Jersey (shared with the impact barrier still), pit-box lines, paved area, pit lane and
season tint have no still of their own.
