# The re-derivation test (codify round, 20 Oct 2026)

**The claim under test:** following `.claude/skills/build-track/SKILL.md` from a clean config produces, before the owner
drives, the level of the Sonoma package the owner accepted on 20 Oct 2026 (registry rev b8a51e2cfa, "drives and feels
like Sonoma"). That level took seven owner-review rounds the first time. The test shows whether the skill holds those
rounds' lessons. A fresh agent re-derives Sonoma from raw sources. `compare_packages.py` then measures the result
against the accepted package.

## Roles

- **Orchestrator.** Sets up the worktree, writes the brief, audits the agent's transcript for forbidden reads, runs the
  comparison, and reports. It never passes the agent anything from the accepted scenery.
- **Fresh agent.** One Opus subagent with no memory of the Sonoma rounds. It gets this file's "Allowed" list and the
  skill. It works stage by stage in its own worktree, with every gate and its own judge round, up to the skill's
  "Acceptance" section.
- **Owner.** Drives the result only after the comparison, as the skill's last step.

## Setup (orchestrator)

1. Create a fresh worktree on its own branch from the codify commit:
   `git worktree add ../probe_sim-wt/rederive-sonoma -b rederive-sonoma <codify commit>`. Symlink `node_modules`,
   `tools/track/cache` (raw downloads: OSM, DEM, lidar, NAIP) and `tools/track/compare/sonoma/satellite_clean` (the raw
   clean captures and `tiles.json`). Nothing else is symlinked.
2. In that worktree, in one setup commit:
   - Replace `tools/track/tracks/sonoma/config.py` with `tools/track/tracks/_template/config.py`. Fill in Sonoma's
     **layout and source keys** from the accepted config: id, name, direction, origin, osm_bbox, osm_file, loop_ways,
     pit_lane_way, dem_tiles, lidar_ept, lidar_survey, dem13, logger_dir, start_finish_latlon, corners,
     named_straights, loop_check, captures. In `sources`, list the onboard RAZip6S84CM (March 2026) and the pit-lane video
     24of8fjjAug (2025). Also copy the **stage 1-2 keys**: stations_ref, centre, spline, features, prior, shapes,
     straights, gate, ghosts. The geometry is accepted and is not under test; the agent rebuilds it and must reproduce
     track.json, heightfield.bin and ghosts.json byte for byte. Copy `tracks/sonoma/stations_ref.json` too.
   - Delete the derived Sonoma records: `tools/track/compare/sonoma/` except `satellite_clean`. That removes manifest.md,
     inventory.json, inventory/, streetview.md, coverage.md, owner_drive_r2/, owner_findings.md, judge_*.md,
     kerb_rollover.md, the hood, buildings, compare and season folders, and overlay/.
   - Delete `public/tracks/sonoma/scenery.json`, `far_heightfield.bin`, `far_ortho.jpg` and `ortho.jpg`. Keep track.json,
     heightfield.bin and ghosts.json, so the app and the drive proxy have the geometry; stage 3 writes the rest.
   - Delete `tools/track/kit/sonoma_poses.json`. The kit README stays: it lists the objects, their keys and their
     evidence, not Sonoma's placements.
3. Write the agent's brief: the skill path, this file's Allowed and Forbidden lists, the raw sources, and the stop
   condition (the skill's Acceptance section). Add no Sonoma findings, no owner notes and no hints.

## Allowed

- The skill (`.claude/skills/build-track/SKILL.md`) and the documents it points to: CONTRACTS.md, tools/track/README.md,
  trackcfg.py, HEIGHTS.md, JUDGE.md, `tools/track/kit/README.md`, and this file's Setup section.
- Every tool under `tools/track/` and the app.
- Laguna's config and package (the reference implementation).
- The raw sources: the cache, the clean captures, the onboard and pit-lane videos (YouTube, watched in the agent's own
  headless or own-tab browser, frames only, never downloaded), live Street View / photo spheres, OSM and the lidar.
- Its own worktree's outputs.

## Forbidden (any read voids the run)

- The accepted config's scenery sections: `scenery`, `pit_lane`, `structures` in `tools/track/tracks/sonoma/config.py`,
  on any branch, in any commit (`git show`, `git log -p`, `git diff` against main or track-pipeline), or in the main
  checkout.
- The accepted package's `public/tracks/sonoma/scenery.json` and its ortho images, on any ref or in any other checkout.
- Sonoma's manifest, inventory, streetview.md, coverage.md, judge tables and owner notes (`compare/sonoma/*.md`,
  `owner_drive_r2/`), and the accepted compare sheets and stills (`compare/sonoma/compare_sheets`,
  `tools/track/kit/stills`, hood folders).
- Memory files and earlier transcripts about the Sonoma rounds.

The orchestrator checks the agent's tool calls for these paths and refs before running the comparison. A void run is
repeated with a new agent.

## The comparison (orchestrator, after the agent reports Acceptance)

```sh
# objects per kind: matched within 15 m / missing / extra, height differences
python3 -I tools/track/compare/compare_packages.py --ref public/tracks/sonoma \
    --cand ../probe_sim-wt/rederive-sonoma/public/tracks/sonoma --out tools/track/out/rederive/report.md \
    --json tools/track/out/rederive/report.json
# stills at the same poses: the accepted walk (compare/sonoma/compare_sheets/walk.json) replayed on the candidate
(cd ../probe_sim-wt/rederive-sonoma && npx vite --port 5181 --strictPort) &
npx tsx tools/track/compare/camera_walk.ts --track sonoma --port 5181 \
    --replay tools/track/compare/sonoma/compare_sheets/walk.json --out tools/track/out/rederive/stills
uv run --python 3.12 --with pillow python -I tools/track/compare/compare_packages.py --ref public/tracks/sonoma \
    --cand ../probe_sim-wt/rederive-sonoma/public/tracks/sonoma \
    --stills-ref tools/track/compare/sonoma/compare_sheets --stills-cand tools/track/out/rederive/stills \
    --sheets tools/track/out/rederive/sheets
```

The `camera_walk.ts` above runs from THIS worktree. It loads the candidate's package from the server on 5181, which
serves the rederive worktree's `public/`. `--replay` takes every pose recorded in the accepted walk and samples the
ground height on the candidate's surface.

## Pass bar

These are the orchestrator's proposal. The owner may change them.

| measure | bar |
|---|---|
| geometry | track.json, heightfield.bin, ghosts.json byte-identical to the accepted package |
| gates | every stage-3 gate passes in the candidate; coverage has 0 undispositioned MISSING rows |
| walls, tyre walls, fences, kerbs (compare_packages) | matched >= 90 % of the reference objects of each kind |
| stations, stands, buildings, bridge, boards, cone lines, blocks, tyre stacks, masts, ground signs | matched >= 75 % per kind |
| extra objects | each listed with its evidence in the candidate's manifest (an extra with evidence may be a find the accepted rounds missed) |
| heights of matched walls, tyre walls, fences | <= 10 % of them differ by more than max(0.3 m, 25 %) |
| side-by-side sheets | the orchestrator answers the JUDGE.md checklist on the candidate's sheets with no FINDING the accepted sheets do not also show |
| the owner's lap | fewer than 5 owner findings (the skill's target) |

## Report

Write the report to `tools/track/compare/sonoma/rederive_<date>.md` in the main worktree. It holds the per-kind table
from compare_packages, the missing and extra lists, each grouped by the skill step that should have produced the object,
the gate results, the agent's owner-facing findings count, and the void-run audit. Every miss becomes an edit to the
step of the skill it belongs to, so the next circuit gets the fix. A miss never becomes an edit to Sonoma's config.
