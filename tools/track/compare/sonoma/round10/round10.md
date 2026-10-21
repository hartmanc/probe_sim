# Sonoma round 10 (21 Oct 2026): the remaining rows of judge_r9.md

Scenery only. Geometry and ortho are byte-identical to c85df6c's package.

| file | before (c85df6c) | after |
|---|---|---|
| track.json (md5) | b54342ae7d1c2bddfdb664031abec570 | b54342ae7d1c2bddfdb664031abec570 |
| heightfield.bin (md5) | 5fd95a7d1ae2d72ab3be047c072e007d | 5fd95a7d1ae2d72ab3be047c072e007d |
| ortho.jpg, far_ortho.jpg, far_heightfield.bin, ghosts.json | | byte-identical |
| registry rev | 2be1bb6dd9 | 4804fb0170 |

## 1. Pit-exit building frontage

The lane-side (track) face is broken into bays with the kit's `windows` / `doors` keys:
- glazed upper bays: pitch 3.6 m, 3.0 x 2.4 m at 4.5 m, pale glass `#8c9eab`, over the dark 2.0-4.0 m band;
- ground-level openings every other bay: pitch 7.2 m, 2.6 x 1.9 m, `#3d4248`;
- the grey wall between the panes reads as the framing.

Evidence: t0304 shows glass in white-framed bays about 3.5 m apart, measured against the 3 m mesh panels. t0300 shows a door
in the lower part of the end.

The kit draws openings on the long sides only, so the end face keeps the plain dark band.

## 2. The canopy's open terrace

`Pit-exit round canopy` gets two new kit keys:
- `deck_posts` 8: the 3.0 m terrace is now a 0.3 m slab on a ring of 8 posts (at 0.85 of its radius) plus a centre post,
  open beneath, with a 1.0 m edge rail.
- `stair`: a 2.5 m flight leaving south (bearing 180) from the terrace's west half (1.8 m west of the centre line), 8 m
  run, solid steps.

Without these keys the round-9 podium is drawn as before.

Evidence:
- t0304: open space and posts under the ring.
- c20_s1870 / c20_s1925: a 2.5 m hatched flight from under the canopy southward, about 9 m.
- lidar 2017: 1.0-1.7 m along x ~76, y -98..-106.

## 3. Pit-out lane surface (s ~158-200)

I found the cause by hiding scene meshes in pose_walk.ts at the round-8 pose s 170 back (stills kept local in /tmp):
- hiding `pit_paint` removed only the white transverse bars;
- hiding `pit_lane_0` showed the terrain;
- hiding `track` made the lane uniform.

So there were two causes:
1. **The track ribbon's left shoulder rows.** They are drawn with a ground (dirt) look and extended under the lane; they
   rose through the lane's polygon offset as pale irregular patches. Fix: `scenery.track_shoulder_cut` [{side left, s
   150-240}] (new). The app gives the track no shoulder there, and the lane is drawn from the edge.
2. **The app's rule pit-box lines.** They are drawn every 10 lane stations along the whole of Sonoma's one-part lane,
   including the pit-out. Fix: `pit_lane.lane.no_box_lines` [{s 150-222}] (new). The builder writes lane stations
   766-836 as `no_boxes`, and the app skips them.

The ortho in the lane was not the cause. A first attempt that flattened the lane's ortho there changed nothing in the still
and was reverted.

## 4. Catch-fence post tops

`fence_arm` {len 0.5, deg 45} is a new opt-in on a declared wall. The app draws an arm on each catch-fence post, leaning to
the side where the track lies, and carries the mesh up the arms. Every other fence is byte-identical.

The vertical mesh is now 1.8 m over the 1.0 m wall (to the bend), and the arm tips stand at ~3.15 m. Round 9 drew a
vertical 2.1 m, top 3.1 m.

| frame | wall face | to the bend | arm rise |
|---|---|---|---|
| t0304 | 82 px | 148 px | +32 px (0.39 m) |
| t006 | 26 px | 47 px | ~+5 px |

pit_lane.walls s 150-170 now says fence 1.8, to match.

## 5. The SONOMA TURN 8 still

The panel was in the package but stood inside the rendered tyre stacks. It sat 0.93 m from the wall line, while the two
stack rows start 0.55 m from it, 0.6 m apart, so their fronts are at ~1.43 m. That is why no still showed it.

A new `wall_boards[].off` (0.7) puts it on the stacks' front, ~1.5 m from the wall line, where t088 shows the lettering: on
the face of the dark barrier. Size (7.7 x 0.7 m), base, text and colours are unchanged.

Stills: `panel_turn8_s2634_r10.jpg` (18 m, turned 49 deg right) and `panel_turn8_s2628_r10.jpg`.

## Front-straight pit wall

h stays 1.1. Its h_src now carries the orchestrator's t0288 reading: the wall top is at about a parked SUV's sill, 1.0-1.1
m, so the lidar's 0.85 m median there is read as a ground-offset artefact on the lane side.

## Gates and tests

`build_track.py --stage scenery --publish --overwrite-package`: all 13 gate lines [ok].
- barrier gaps: min 0.31 m over 73 runs
- containment: 0 escapes
- pit connectivity: 0 crossings; lane: 855 stations, 0 obstacles, 0 pinched
- signs: 130 checked, 0 misplaced
- wall ends: 15 checked, 15 joined, 0 exposed
- tyre facings: 0
- coverage: 280 rows, 210 objects, MISSING 0, UNSUPPORTED 0, DISPOSITIONED 30, 1 advisory HEIGHT row (explained in the
  manifest)
- pit lane: 13 rows, 0 undeclared, 0 absent

Other checks:
- `run_gates.ts`: exit 0.
- `run_coverage.ts`: exit 0,
  `{"pass":true,"missing":0,"unsupported":0,"assigned":0,"dispositioned":30,"invalid":0,...,"heights":1,"pit":{"pass":true,...}}`.
- vitest: 51 files; 394 passed and 1 expected fail (395), with the rev updated.
- pytest: 26 passed.
- vite build: built. tsc: 0.

`compare_packages.py --ref <c85df6c's package> --cand public/tracks/sonoma`: matched 380, missing 0, extra 0, height diffs
0. Every change is to an existing object.

Record-level diff of scenery.json:
- barriers: 1 changed, the catch-fence run (`fence` 2.1 to 1.8, `arm` added);
- landmarks: 1 changed, the SONOMA TURN 8 panel's x / y;
- structures: 2 changed, the building (`windows`, `doors`, src) and the canopy (`deck_posts`, `stair`, src);
- pit_lane parts: `no_boxes` added on part 0;
- `track_shoulder_cut`: new.
- Nothing else changed.

## Stills (local, gitignored; pose_walk.ts, tag r10)

In `tools/track/compare/sonoma/round10/`:
- `pitwall_s110_along_r10.jpg`, `pitwall_s140_along_r10.jpg`, `pitwall_s170_back_r10.jpg`
- `panel_turn8_s2634_r10.jpg`, `panel_turn8_s2628_r10.jpg`
- `canopy_from_lane_s155_r10.jpg`
- `tower_8a_s2650_right_r10.jpg`, `tower_drag_s1760_right_r10.jpg`

Reference frames read, not copied: t0288, t0300, t0304 (24of8fjjAug), t006, t088 (RAZip6S84CM).
