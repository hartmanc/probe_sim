# Buttonwillow round 12: ledger (24 Oct 2026)

The owner (24 Oct 2026, evening): "Fix both tracks so they pass all gates." Round 12 makes the published Buttonwillow
package pass every gate of the merged pipeline (branch `integration` 152d422: the Sonoma round 12-14B gates and the
Buttonwillow round 9-11 gates). Scenery stage only; geometry byte-identical. Branch `buttonwillow-r12`; nothing pushed
or deployed; `PHYSICS_VERSION` and `src/app/changelog.ts` untouched (one version per publish; the preview is the
orchestrator's).

Build: the round-11 build records (`probe_sim-wt/buttonwillow/tools/track/out/bw_r11/`, read only) copied to
`tools/track/out/buttonwillow_r12/`; the worktree's track cache and compare imagery cloned (APFS `cp -c`, read only on
the source) from the same worktree. Stage 3 run twice (check, then `--publish --overwrite-package`), both exit 0 with 0
`[FAIL]` lines. Logs: `/tmp/bw12/stage3.log`, `/tmp/bw12/stage3_pub.log`. Package `public/tracks/buttonwillow`: rev
**69e80ace38 -> 4c9dab5340**, lap 4699.187 m (unchanged).

## What failed (merged gate CLI on rev 69e80ace38)

| gate | result | cause |
|---|---|---|
| wall ends | FAIL: 3 exposed, right, s 826 (5.4 m out), 1184 (7.8 m), 1020 (6.8 m) | the station 826 / 1185 surrounds and the T3 station mound tyres are CLOSED rings; each ring's polyline seam (first = last point) lay on its track side, and the gate (tyre runs within 8 m) reads a run's first point as its head |
| run gaps | FAIL: 2 holes in the pit lane's paddock-side K-rail, left, s 4657 (12.5 m, west / tower runs) and s 47 (14.5 m, tower / east runs), 22.9 m out | the K-rail's real openings to the paddock; nothing declared them |
| ground marks on surface | FAIL: 1680 of 19202 vertices off (-0.063 .. +0.027 m against 0 .. 0.01) | the round-11 crack seal (0.4 m polyline points) and the other paint lines kept heights from before the package's own surface; Buttonwillow never had `scenery.marks_on_surface` |
| everything else | ok | |

## What changed, with the evidence

### 1. Wall ends: the station rings' seams on their far side

Evidence (crops at the rings' ENU centres on the 2026 clean captures, `satellite_clean`): c20_s0550 / c20_s0950 (826),
c20_s1300 (1185), c20_s1150 (T3): each a continuous dark ring round the white roof, closed all round; the one pale break
(826) lies on the side away from the track. Onboard (`stage3_evidence/station_crops.jpg`): t034 and t046 one unbroken
low pale surround under the station, t138 (T11 approach) a continuous ring. So each surround is real and closed: it has
no end facing travel, and the head the gate read was a modelling artefact (where the loop of points began).

Fix: `build_scenery` declared walls take `seam='far'` (config-gated; it refuses a ring that is not closed): the ring
starts at its point farthest from the track. Points, segments, heights, colour and collision are unchanged; only where
the loop starts (checked: each changed barrier in scenery.json is a pure rotation of the same closed point list).
Applied as one rule to all nine closed station rings (the three failing ones and 2370, 3433, 3716, T5, T6, T11
approach; T11 and 2370 already started at their far point). Seams now 12.0 m (826), 14.6 m (1185) and 13.6 m (T3)
beyond the edge. No `known_exposures` entry was needed (no bare head shows on any evidence), nothing removed, nothing
added. SKILL 3.4 carries the rule.

### 2. Run gaps: two declared openings (`scenery.gates.openings`)

Evidence: the capture crops at both holes (c20_p0420 / c20_p0480 west of the tower, c20_p0480 / c20_p0540 east of it):
the red / white K-rail stops and the paving runs unbroken from the lane into the paddock, ~12 m wide on the capture
each. Pit-lane video ucmXJu5QKFQ 21:52 (t1312000): the K-rail ends at a pole west of the tower, people walk through the
gap, a yellow and an orange cone stand in it. Both declared with `why` and their frames; the walls are not moved.
Observation, not changed: the capture puts the tower run's east end ~3 m further east than the model (its hole reads
~11.6 m against 14.5 m), and the sim draws the paddock beyond both openings as dirt where the capture shows paving
(`pairs_paddock.jpg` rows 1-2). For the owner.

### 3. Ground marks: `scenery.marks_on_surface` on (lift 0.008 m)

Stage 3 now drapes every ground mark on the package's own driven surface (`drape_marks.ts`, the Sonoma round-14B
mechanism): 3610 paint-line vertices (+0.008 m), 1092 cone points; 0 kerb-line points, 0 ground signs. Heights only:
0 plan (x, y) changes in any paint line or cone line (checked over the whole scenery.json). Largest paint-line height
change 0.071 m, largest cone 0.148 m (those cones stood that far off the surface before). The gate after: every vertex
0.008 m above the surface. The seal on the stills (`pairs_seal.jpg`: hood 850, 1000, 1100, 1600, 1650, 4300; back
2600): the same thin, glossy, wavy lines as round 11, nothing floating or sunk; the pixel differences (0.2-8 %) are the
hood's sky reflection and the asphalt grain, not the marks.

### 4. Cones off the surface: still ok (264 cones / 44 lines, deepest 0.00 m)

## Gates, rev 69e80ace38 (round 11) against 4c9dab5340 (round 12)

Stage-3 gate CLI (`run_gates.ts public/tracks/buttonwillow <the publish run's gates_config.json>`), plus the build's own:

| gate | round 11 | round 12 |
|---|---|---|
| edge (with walls), world continuity, profile | ok (0.066 / 0.066 rms; 0.0076 / 0.0073; 0.017) | ok, same numbers |
| owner reference / width / band (stage-3 owner gates) | ok (0.381 / 0.328; 0.384; 0.136 / 0.120) | ok, same numbers |
| barrier gaps | ok, min 4.17 m / 17 runs | ok, same |
| containment | ok, 0 escapes, 3166 allowed, 78 junction hits | ok, same |
| pit connectivity | ok, 388 / 382 m, lane 0 obstacles | ok, same |
| signs | ok, 16 | ok, 16 |
| **wall ends** | **FAIL**, 7 checked, 3 exposed | **ok**, 4 checked, 4 joined / lapped / tapered, 0 exposed, 0 known exposures |
| tyre facings, wall tops, wall-tyre joins, tyre faces | ok | ok |
| **run gaps** | **FAIL**, 2 holes | **ok**, 2 declared openings, 0 holes |
| terrain override | n/a (no region) | n/a |
| **ground marks on surface** | **FAIL**, 1680 off (-0.063 .. 0.027 m) | **ok**, 0 off (0.008 .. 0.008 m) |
| cones off the surface | ok, 264 / 44, deepest 0.00 m | ok, same |
| coverage | ok, MISSING 0, UNSUPPORTED 0, 5 dispositions | ok, same (87 rows, 167 objects) |
| pit lane | ok, 7 rows | ok, 7 rows |

Tests on the branch after the change: `npm run build` clean; `npx vitest run` 62 files, **510 passed**, 0 failed
(the registry test checks the new rev; kerb traversal on the unchanged kerbs); Python
`pytest tools/track` **79 passed, 3 skipped**.

## Geometry identity

`tools/track/out/buttonwillow_r12/` and `public/tracks/buttonwillow/` against rev 69e80ace38 (`git diff --quiet HEAD`
and `cmp`): track.json, heightfield.bin, ghosts.json, ortho.jpg, far_heightfield.bin, far_ortho.jpg byte-identical
(sha256 track.json 199358fe..., heightfield.bin 2c677efb..., ghosts.json e66b3218...). Stages 1 and 2 were not re-run
(the scenery stage reads the copied records). scenery.json is the only changed file; its value changes are exactly the
ring rotations, the paint-line heights and the cone heights above (the rest of its byte difference is number spelling,
1.0 -> 1, from the JSON round trip through drape_marks.ts).

`src/scoreboard/config.ts`: TRACKS.buttonwillow `rev` 69e80ace38 -> **4c9dab5340**, `length_m` unchanged.

## Stills (local only, `round12/stills/`; `pose_walk.ts --port 5212`, hood camera; `_before` = rev 69e80ace38 rendered on this branch, `_after` = 4c9dab5340)

- `pairs_stations.jpg`: rows 826 R and fwd 800 (yaw -35), 1184 R and fwd 1160, 996 R (round-11 pose) and fwd 995: the
  rings unchanged to the eye.
- `pairs_paddock.jpg`: the two openings from the lane (pit_gapW_row, pit_gapE_row, yaw 60; yaw 40 views) and the
  round-11 pit poses p0_012 / 013 / 014.
- `pairs_seal.jpg`: the round-11 seal poses (hood 850, 1600, 1650, 4300; back 2600) plus hood 1000 / 1100.
- Single stills `<pose>_before.jpg` / `<pose>_after.jpg`; poses in `/tmp/bw12/poses.json`.

## Open (for the owner)

1. The paddock beyond the two K-rail openings is drawn as dirt; the capture shows paving there.
2. The tower run's east end ~3 m short of the capture's.
3. Carried from round 11: the mouth lines without onboard cones, the T2 wall height, the 37 kerb-run extents, the hood
   camera.
