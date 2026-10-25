# Sonoma round 14C: the published package passes every gate of the merged pipeline

Branch `sonoma-r14c` (from `integration` 152d422), 24 Oct 2026. The owner's instruction: "Fix both tracks so they pass
all gates." Scenery stage only; geometry unchanged. Nothing pushed or deployed.

Package: **rev f399cda140** (was 6b766e08d6), lap 4105.328 m. `src/scoreboard/config.ts` TRACKS.sonoma `rev` updated.

## What failed (merged gate CLI on rev 6b766e08d6)

| gate | finding | cause |
|---|---|---|
| cones off the surface | 8 cones more than 0.15 m inside an edge | 7 on the pit-in double white line: round 14B's gates_config.json predates the merged `cones_exempt`. 1 on the owner's T1 paddock-side mouth arc, s 173.9 right, 0.26 m inside: the line follows his red arc, and the round-14B edge sits off his red inside the mouth (the owner-reference gates leave mouths +-12 stations out). |
| wall ends (issue #12; passed, wrongly) | the far wall's head at s ~2347 counted as "joined to the tyre bundle" | the bundle ("drag strip NW end: tyre bundle at the far wall's head (round 14B)") was three coincident points at (-365.49, 393.21): zero length, nothing drawn. The judge (r14b A14) saw a bare head. |

## What changed

1. **Gate hardening** (commit 5578d98; `tools/track/gates/sceneryGates.ts`, `run_gates.ts`). A tyre, concrete, pit-wall
   or Armco run shorter than 0.5 m (or with fewer than two points) is **degenerate**. It never counts as a join, a
   cushion or a lapping run in the wall-ends gate, nor as a lapping run in the run-gaps gate. The wall-ends gate lists
   it and FAILS. Tightening only. Tests: `src/scoreboard/__tests__/scenerygates.test.ts`, "degenerate runs" (2 cases,
   both fail on the old gate). On rev 6b766e08d6 the hardened gate fails: "1 degenerate runs ... tyres run 50 ...
   (0 m long, at -365.49, 393.21)".
2. **Builder fix at the cause** (commit bc5862d; `tools/track/build_scenery.py` `tyre_facings`). It was not the
   barrier-gap mover (the bundle stands 21-23 m from the edge), the clip or the joins. `tyre_facings` moves every tyre
   point within reach (2.6 m) of a rigid wall onto the NEAREST point of the wall line, 0.55 m toward the track. That
   nearest point is clamped to the segment, so every point of a cushion lying in line beyond the wall's head landed on
   the head itself. Now a point whose nearest wall point is a free end (beyond the run's first point on its first
   segment, or its last on its last) goes onto the wall's line extended past that end, the same 0.55 m in front, and
   keeps its place along it. Points beside a wall snap as before.
   - First try, kept the points where declared: the T8a-T9 bank tyres' tail (two points that had collapsed onto the
     T9 wall head the same way) then stood off the wall's line and wall-tyre joins failed (s 2584, wall head 0.39 m
     proud). The extended-line rule passes it (-0.68 m).
   - Tests: `tools/track/test_tyre_facings.py` (2 cases, both fail on the old code).
   - The bundle now: 3 points, 2.04 m, along the far wall's line 0.55 m in front, its tail 0.44 m from the head. The
     wall-ends gate: "s 2346 joined to tyres run 50". Wall-tyre joins: s 2346 -1.17 m (not proud).
3. **Config** (`tools/track/tracks/sonoma/config.py`; evidence in the comments).
   - `scenery.gates.cones_exempt` for the pit-in double white line was already in the merged config (integration
     refresh merge 2). The round-14C build carries it into gates_config.json: 19 cones on a separation line, not gated.
   - The T1 mouth arc: round 14B's `cone_lines_declared` row moved to `scenery.owner_mouths_r14` +
     `scenery.owner_mouth_cones` (from 'owner_mouths_r14', spacing 4.4, **clip_out 0.1**), the Buttonwillow round-11
     mechanism. 22 of the arc's 28 points were clipped to 0.1 m outside the edge (deepest 0.27 m inside). It is the same
     line from his red (owner/r14/mouths.json, the same 8 points), the same default orange cone and the same 4 cones,
     4.4 m apart over 13.7 m.
   - `owner_mouth_cones` takes an optional `label` for the src (absent: "owner round-10 mouth", Buttonwillow's text).
     Sonoma's is "owner round-13 drive mouth".

## Stage 3 (`build_track.py --track sonoma --stage scenery --out tools/track/out/sonoma_r14c`, then `--publish --overwrite-package`)

The 14B build records were copied from `track-pipeline/tools/track/out/sonoma_r14b`. Stages 1 and 2 were not re-run:
their records stayed current. The local inputs were APFS-cloned (no shared files): `tools/track/cache` from the main
checkout, and `compare/sonoma/satellite_clean`, `compare/buttonwillow/satellite_clean`, `compare/satellite`,
`compare/satellite_clean`. No --write-on-fail package was ever published.

- Run 1 stopped on the missing clean captures.
- Run 2 failed wall-tyre joins (the first builder fix, above).
- Run 3 passed. The publish run rebuilt it and published; out and public are cmp-identical, all 7 files.

| gate | result |
|---|---|
| edge gate L / R | ok, rms 0.040 / 0.046 m |
| world continuity L / R | ok, 0.0164 / 0.0184 m (4 declared junction corners exempt) |
| profile | ok, 0.028 m |
| owner reference L / R, width, band L / R | ok, 0.350 / 0.379 m, 0.392 m, 0.160 / 0.122 m |
| barrier gaps | ok, min 0.34 m over 73 runs |
| containment | ok, 0 escapes (1282 allowed) |
| pit connectivity, sign placement | ok |
| wall ends | ok: 41 checked, 40 joined / cushioned / lapped / tapered, 1 known exposure (T4 left s 736), **0 degenerate** |
| tyre facings, tyre faces | ok, 0 / 0 |
| wall tops | ok |
| wall-tyre joins | ok, 6 joins, none proud (s 1721 -0.13, 2584 -0.68, 414 -0.60, 2346 -1.17, 2243 -0.61, 3472 -0.34) |
| run gaps | ok, 6 openings, 0 holes |
| pavement joins / smoothness / kerbs on surface | ok, 0.0056 m 1.63 deg / 0.0099 m / 0.71 deg |
| ground marks on surface | ok, 0.008 m |
| **cones off the surface** | **ok: 58 cones on 10 lines, 0 more than 0.15 m inside (deepest 0.08 m), 19 on the pit-in separation line** |
| coverage | ok, MISSING 0, UNSUPPORTED 0 |
| pit lane, ground lines | ok |

Stage-3 gate CLI on `public/tracks/sonoma` with the new `work/scenery_tmp/gates_config.json` (cones_exempt, allowed,
paddock, openings, known_exposures): every gate ok, exit 0.

## Proofs

- **Geometry identical.** track.json, heightfield.bin, ghosts.json, far_heightfield.bin and far_ortho.jpg are
  byte-identical to rev 6b766e08d6: `git status` shows only scenery.json and ortho.jpg modified in public/tracks/sonoma,
  and track.json is still sha256 2c043135a7b27767.
- **ortho.jpg** changed: 137 px by more than 8 grey levels, every one within 8 m of a changed tyre run. The ortho is
  inpainted under barrier runs ("65 barrier runs banded"), so the bundle and the five re-placed tyre end points move
  their bands. The rest is JPEG re-encode ripple (4976 px > 0).
- **scenery.json changes against rev 6b766e08d6.** No other section changed.
  - Barriers: the bundle (0 -> 2.04 m) and five other tyre runs whose points beyond a wall's end moved from the end
    point onto the extended line: T8a-T9 bank (2 points, the collapsed tail), T11 hairpin left (1), T2 approach far
    left (1), 9a right (1), T7a terrace tyre line (1).
  - Cone lines: the T1 arc line (clipped, new src).
- **Laguna and Buttonwillow unchanged by the tool change.** Only Sonoma sets `scenery.tyre_facings` or
  `owner_mouth_cones.label`. Each track's scenery stage was run with the new `build_scenery.py` and with the old one
  (5578d98's), on identical inputs:
  - Buttonwillow (bw_r11 records cloned to `out/bw_r14c_check`): scenery.json, ortho.jpg, far_ortho.jpg and
    far_heightfield.bin byte-identical old vs new; the gate lines are identical too. Against the published package the
    values are equal (JSON-equal). The one byte difference is the starter's stand's key order (`roof` before `color`),
    which the merged code writes and INTEGRATION.md already notes. The stage fails wall ends, run gaps and ground marks
    on both tools, the known round-11 findings (INTEGRATION.md); that is the other worktree's round.
  - Laguna (`out/laguna_ab`: laguna_dryrun's stage-1 records, `--write-on-fail`, nothing published): scenery.json,
    ortho.jpg, far_ortho.jpg and far_heightfield.bin byte-identical old vs new; the logs are identical too. Laguna's
    published track.json has no current stage-1 record, so it cannot be rebuilt from its own package.

## Tests

- `npm run build`: clean.
- `npx vitest run`: 62 files, **512 passed** (510 + the 2 degenerate-run tests), 0 failed.
- Python (`uv run ... pytest tools/track -q`): **84 passed**, 0 skipped. That is the 79 passed and 3 skipped of
  before, + 2 tyre_facings tests; the 3 data tests that skipped before now run, because the worktree now has the
  caches and captures.

## Stills (local, reference only, not committed)

`tools/track/compare/sonoma/round14c/stills/`, `<pose>_before.jpg` (rev 6b766e08d6) and `<pose>_after.jpg` (rev
f399cda140), pose_walk.ts:
- `t1_220_right`: the round-14B pose.
- `t1_mouth_arc`, `t1_mouth_arc_high`: the T1 mouth arc and its 4 cones (the clip moves them by at most 0.37 m,
  barely visible at this scale).
- `end_2347_far_wall_tip`: the round-14B pose.
- `end_2347_bundle_close`: the bundle drawn at the far wall's head; before, a bare square head.
- `pit_in_line_3500`, `pit_in_line_3520`: the pit-in separation line; unchanged, exemption only.

Poses: `/tmp/r14c/poses.json` (local).

## Open (not in scope)

- The bundle is drawn black. The capture shows a white top (c20_s0000), and the config gives TYRE_BLACK only, as in
  round 14B.
- The judge's other round-14B rows (T7 approach edge line and pale shoulder, the T9A mouth line, the pre-existing
  items) are untouched.
