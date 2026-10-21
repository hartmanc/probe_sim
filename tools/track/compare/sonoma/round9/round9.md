# Sonoma round 9 (21 Oct 2026): the five cosmetic rows of judge_r8.md

Scenery only (stage 3). The geometry is byte-identical: the scratch candidate's stage-1 record (/tmp/r8/cand, current
config) still holds, and the published files did not change.

| file | before (56a3ff0 / ba344c3) | after |
|---|---|---|
| track.json (md5) | b54342ae7d1c2bddfdb664031abec570 | b54342ae7d1c2bddfdb664031abec570 |
| heightfield.bin (md5) | 5fd95a7d1ae2d72ab3be047c072e007d | 5fd95a7d1ae2d72ab3be047c072e007d |
| ortho.jpg, far_ortho.jpg, far_heightfield.bin, ghosts.json | | byte-identical |
| scenery.json | | changed (below) |
| registry rev | 51c8d70642 | 2be1bb6dd9 |

## 1. The tower's track face (owner_52)

Marshal post `8a (T9) station tower`, now `style='deck'`. This is a new opt-in style of the kit's hut; every other post
is byte-identical in scenery.json, and the app code path for the other styles is unchanged.

It draws three parts, as owner_52 shows them:
- a solid lighter lower storey (`color`) up to a sill 1.0 m above the deck level;
- an open viewing deck: corner and mid-side posts, front and side rails, a dark deck floor, open all round;
- a broad flat roof slab (0.3 m, brown `roof`), overhanging 0.9 m at the front (the heading, toward the 8a-T9 pass) and
  0.6 m elsewhere.

The roof top stays at h - 0.19 = 3.81 m (lidar 3.5-4.1 m).

## 2. SONOMA TURN 8

- **What and where:** a wall board with typed white text on grey `#8f9392` (no logo art), on
  `T9, right: black tyre facing in front of the 8a station (round 8)` at s 2641-2647. It is one panel, 7.7 m long, 0.7 m
  tall, 0.15 m above the ground. Package position: (-104, 223), s 2644.
- **Source:** t088 shows the grey panel with the white lettering on the dark wall, between the camera and the station.
- **Length:** the panel is 142 px long against the 1.0 m wall face's 17 px there, so it is at least 8.4 m (a lower
  bound, because the view is foreshortened). The stretch s 2641-2647 gives one 7.7 m panel.
- **Not placed:** the small logo mark left of the text (no logo art).

## 3. Pit-out catch fence

`pit-out lane, paddock side` is split at its vertex s ~151 into two runs joined end to end on the same measured line:
- s 106-151: the low chain-link, fence 1.0 m. In t0300 the lane's left along the apron is the low black steel fence
  (inventory pit row s 100).
- s 151 to the Jersey end (s ~268): `pit-out lane, paddock side: wall with the catch fence (round 9)`, fence 2.1 m over
  the 1.0 m wall, top 3.1 m.

How the height was measured (each post against the wall face directly beneath it, so the ratio holds):

| frame | wall face | post to its bend | post to the top of its arm |
|---|---|---|---|
| t0304, post at x ~180 | 82 px | 148 px (1.8 x) | 180 px (2.2 x) |
| t006, post at x ~80 | 26 px | 47 px (1.8 x) | 52 px (2.0 x) |

The kit's fence is vertical, so the angled post tops are not drawn.

The declaration now matches the object: pit_lane.walls s 150-170 names this run, with h 1.0 and fence 2.1 (was h 1.1,
fence 4.0).

One HEIGHT row is advisory and explained in the manifest: inventory row s 184 (t006) reads 2.0 m to the top, while the
package has 3.1 m. That frame's own ratio gives about 3.0 m.

## 4. K-rail stretch height

The pit wall is now two runs joined end to end on the same measured line at the island vertex (s ~85, 38.1619249,
-122.4555526), both kind pitwall:

| run | stations | h | h_src |
|---|---|---|---|
| `pit straight, pit-lane side: front-straight wall to the island` | s 3953-85 | 1.1 m | onboard 2:14-2:17 and Street View 1.08 m; lidar median 0.85 m (p25 0.83, p75 0.87; 115 samples) |
| `pit straight, pit-lane side: K-rail from the island to the blend line` | s 85-158 | 0.85 m | lidar median 0.85 m (p25 0.83, p75 0.89; 33 samples); t0300 Jersey; pit row s 100 0.9 m |

**The 2017 lidar does not step.** DSM - DEM, sampled every 2 m along the line (the maximum of the 3 x 3 m around each
point), has a median of 0.85 m on both stretches. So I made the split where the wall type changes instead: on the captures
(the island's convergence) and in the pit video (t0296 shows a continuous wall, t0300 Jersey segments). The front-straight
run keeps the onboard and Street View 1.1 m.

pit_lane.walls is split to match: s 4000-85 (h 1.1) and s 85-158 (jersey, h 0.85).

Wall-ends gate: 15 upstream ends checked (was 14), 15 joined / cushioned / lapped / tapered, 0 exposed. The K-rail run's
upstream end is the front-straight run's downstream end, so it counts as joined.

The front-straight run is now shorter and is resampled evenly over its length, so its points and the pit-wall boards on it
move along the line. The boards move at most 0.10 m across it.

## 5. Pit-exit building and the round canopy

`Pit-exit building` (garage):
- Changed to match t0300: grey walls `#6f7277`, a continuous dark frontage band 2.0-4.0 m on all four walls (new garage key
  `band`), no window rows and no red mid-wall band (`trim_h` 0; the kit now skips the band at 0).
- Kept: the red roof edge, the mono-pitch roof and the lidar heights, 4.2 m to 8.2 m. In t0300 the high end stands about
  2.2 x the low end; the lidar ratio is 1.95 x.
- Not modelled: the open terrace under the roof's high end.

`Pit-exit round canopy` (new structure type `canopy`; build_structures.py, src/app/structures.ts, kit README):
- **Position and size:** centre (38.1618691, -122.4567031), from c20_s1870 (the red disc, 10 m across, with a dark open
  centre).
- **Roof:** a ring roof of red `#a9594d` panels (capture median rgb 169, 89, 77), open centre 2.5 m. Its centre is at
  7.6 m, tilted 14 deg up to the east; the lidar reads 6.3 m at the west rim and 8.8 m at the east rim.
- **Support:** six posts plus the inner ring posts, standing on a 10.5 m round terrace 3.0 m high (lidar 2.9-3.2 m through
  the open centre).
- **Footage:** t0304, a red ring roof on a steel ring with an open middle, beside the building.
- **Comparison tool:** compare_packages now classifies it as a building.

## Gates and tests

From `build_track.py --stage scenery --publish --overwrite-package`, all 13 gate lines are [ok]:
- barrier gaps: "min gap to the edge 0.31 m over 73 runs"
- containment: 0 escapes (1218 allowed, 201 junctions)
- pit connectivity: 0 barrier crossings; lane: 855 stations, 0 obstacles, 0 pinched
- sign placement: "130 ... 0 misplaced"
- wall ends: "15 ... checked, 15 joined / cushioned / lapped / tapered, 0 exposed"
- tyre facings: 0
- coverage: "280 inventory rows checked ..., 210 scenery objects; MISSING 0 (none), UNSUPPORTED 0 (none); DISPOSITIONED 30"
  with 1 HEIGHT row (advisory, explained above)
- pit lane: "13 pit-lane wall rows; 0 not declared ..., 0 with no barrier"

Other checks:
- `run_gates.ts`: exit 0.
- `run_coverage.ts`: exit 0,
  `{"pass":true,"missing":0,"unsupported":0,"assigned":0,"dispositioned":30,"invalid":0,...,"heights":1,"pit":{"pass":true,...}}`.
- vitest: 51 files passed; 394 passed and 1 expected fail (395). This is after the rev update; the fingerprint test
  requires a new rev on every publish.
- pytest: 26 passed.
- `npx vite build`: built. tsc: exit 0.

`compare_packages.py --ref <56a3ff0's package> --cand public/tracks/sonoma`: matched 375, missing 0, extra 1, height
diffs 1.
- The extra is the board SONOMA TURN 8.
- The height diff is the catch fence, 2.0 to 3.1 m.
- The round canopy is matched to the pit-exit building within 15 m, so it does not show as extra.

Record-level diff of scenery.json:
- barriers: removed 1 (the continuous pit wall); added 3 (its two runs and the catch-fence run); changed 1 (the shortened
  low pit-out run).
- landmarks: added 1 (the board); changed 1 (the tower's style).
- structures: added 1 (the canopy); changed 3 (the building, and the two pit-wall board runs following the resampled
  wall).
- pit_lane parts: re-clipped at the split walls, by up to 0.01 m.
- Nothing else changed.

## Stills (local, gitignored; pose_walk.ts at the round-8 poses, tag r9)

In `tools/track/compare/sonoma/round9/`:
- `tower_8a_s2650_right_r9.jpg`, `tower_drag_s1760_right_r9.jpg`
- `pitwall_s110_along_r9.jpg`, `pitwall_s140_along_r9.jpg`, `pitwall_s170_back_r9.jpg`
- also at the round-8 poses: `pitwall_s075_along_r9.jpg`, `tower_drag_s1740_aheadright_r9.jpg`,
  `tower_8a_s2620_aheadright_r9.jpg`, `wall_8a_s2540_right_r9.jpg`

Reference frames read, not copied: t0296, t0300, t0304 (24of8fjjAug), t006, t088 (RAZip6S84CM), owner_52.
