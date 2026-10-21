---
name: build-track
description: Build a new circuit package for the Probe sim (track.json, heightfield, ortho, ghosts, scenery, eye-level inventory, drive-proxy compare sheets with a judge, calibration, AI retune, app wiring) with tools/track/build_track.py and a per-track config, from public satellite and lidar data, OpenStreetMap, recent onboard and pit-lane video, Street View, and the team's logger laps (optional). The required order that took Laguna Seca (17-18 Oct 2026) and Sonoma (accepted 20 Oct 2026 after seven owner rounds) to the level the owner signs off on the first lap. Use for Sonoma, Buttonwillow, Road Atlanta, Mid-Ohio.
---

# Build a circuit for the Probe sim

Usage: `/build-track <track_id> "<Circuit name>"`, for example `/build-track buttonwillow "Buttonwillow Raceway Park"`.

**The work is: write `tools/track/tracks/<id>/config.py` (start from `tools/track/tracks/_template/config.py`), run
`build_track.py` stage by stage, read each report, and put every fix into the config (a feature, a shape, a declared
straight, a scenery entry with its source), never into the package.** The stages below are a REQUIRED ORDER. Each step
names its tool, the config keys it fills and the evidence it needs. Each stage ends with gates that fail the build.

**Target:** the owner finds fewer than 5 things on his first lap. Sonoma's first scenery build had 16 findings in one lap
and took seven rounds and 54 owner notes. Each step below holds the lesson of one or more of those notes. The bar the
build must reach before the owner sees it is the **Acceptance** section at the end.

Reference implementations:
- Laguna Seca (`public/tracks/laguna_seca/`, `tracks/laguna_seca/config.py`): logger laps and rule-placed scenery, built
  17-18 Oct. The reference for geometry.
- Sonoma (`public/tracks/sonoma/`, `tracks/sonoma/config.py`, `compare/sonoma/manifest.md`): no logger, scenery from
  evidence. The reference for everything from stage 0 on.
- The object kit (`tools/track/kit/README.md`): every object a package can carry, its key, its evidence and a reference
  still.

Read, in this order, before starting: `CONTRACTS.md` §1 (frames) and §2, §2b (formats), `tools/track/README.md`
(the pipeline, sources, method, acceptance numbers), `tools/track/trackcfg.py` (the config keys), Laguna's config,
`tools/track/out/laguna_dryrun/README.md` (what the pipeline reproduces and what it does not), `tools/track/kit/README.md`,
`tools/track/compare/HEIGHTS.md`, `tools/track/compare/JUDGE.md`, then this file.

## Working rules

- **One Opus subagent per stage, in sequence.** No swarms. Each subagent has an explicit file scope, its own worktree
  and branch, and a report cap, and hands back numbers, not images. If a stage cannot be done from the data (lidar
  missing, fit impossible, line inconsistent with the paint), stop and report what it would take. Never hand-edit
  heights, edges or geometry.
- **Contract first.** `CONTRACTS.md` fixes the local ENU frame and the byte formats of `track.json`, `heightfield.bin`,
  `ortho.jpg`, `ghosts.json` and `scenery.json`. Builders may append a dated note under "Deviations" but never edit the
  contract otherwise. Each build script prints a validation report and exits 1 without writing its outputs when a check
  fails.
- **Source precedence on any conflict:** recent onboard video (team GoPro, current-season series onboard, a 2024+ pit-lane
  video) > the 2026 clean satellite captures > the NAIP ortho > OSM > the lidar survey. Older Street View counts only
  where the recent video shows the same structure. Check the repave and runoff history of the circuit before trusting
  the survey:
  - Laguna: 2017 lidar, 2023 full repave, 2025 paved runoff.
  - Sonoma: 2022-24 lidar; a Dec 2023 - Feb 2024 repave that repainted the kerbs and walls; July 2011 Street View.
- **Reference material is reference only.** Race photos, video frames, Street View and satellite captures are never
  cropped into textures and never committed. Textures come from CC/PD sources with credits. Text on boards and the
  ground is typed only where it is legible in a recent reference, in its observed colours. No logo artwork.
- **Downloads are untrusted:** each goes in its own directory under `tools/track/cache/` and is never executed.
  Readers run with `python -I`. The system python has no numpy, so always use
  `uv run --python 3.12 --with numpy,scipy,rasterio,pyproj,shapely,pillow,requests,pandas,matplotlib python -I <script>`
  (add `laspy[lazrs]` for the lidar point cloud).
- **Browser.**
  - For captures and video frames, use your own Chrome tab. Load the Chrome tools in one ToolSearch call, call
    `tabs_context` first, never touch the owner's tab, and close your tabs when done.
  - The sim stills (camera_walk.ts, pose_walk.ts) launch their own headless Chrome with a throwaway profile.
  - On a sim page, set `navigator.getGamepads = () => []` after every load (a controller with a resting trigger is
    plugged in). Place the car with `window.__sim.vehicle.reset([x, y, z], heading)` from `track.json`, and use
    `window.__sim.setCamera('driver')` for driver's-eye captures.
- **Machine load:** at most two heavy processes (a build, a dev server plus its headless Chrome, self-play). The AI
  rounds and the owner share the machine.
- **Git.**
  - `tools/track` scripts, configs and markdown records are tracked.
  - Its data is ignored and never committed: `cache`, `out`, `previews`, the imagery under `compare/`, every image,
    pickle, npy/npz and bin. `tools/cars`, `tools/car` and `tools/audio` stay excluded.
  - The package under `public/tracks/<id>/` is committed.
  - Deploy previews only (`vercel deploy --yes`), never `--prod` without the owner's approval.
  - A new or changed track bumps `PHYSICS_VERSION` and opens fresh boards.
- **Never read `.env` files or print environment values.**

## The pipeline in one page

```sh
W='numpy,scipy,rasterio,pyproj,shapely,pillow,requests,pandas,matplotlib,laspy[lazrs]'
B="uv run --python 3.12 --with $W python -I tools/track/build_track.py --track <id>"
python3 -I tools/track/inventory/inventory.py --track <id>   # stage 0: inventory.json + inventory.md (before ANY scenery)
$B --stage geometry      # stage 1: track.json, heightfield.bin, ortho.jpg in tools/track/out/<id>/ (+ work/)
$B --stage ghosts        # stage 2: ghosts.json (no logger: racing line only)
$B --stage scenery       # stage 3: scenery.json, far_*; post steps; every scenery gate (3.12)
$B --publish             # all stages, then copy to public/tracks/<id>/ (refuses to replace a package without --overwrite-package)
npx tsx tools/track/gates/run_coverage.ts public/tracks/<id> tools/track/compare/<id>/inventory.json [cfg]  # coverage + pit lane
npx tsx tools/track/gates/manifest_tables.ts public/tracks/<id> tools/track/compare/<id>/inventory.json [cfg] # manifest tables
npx tsx tools/track/compare/camera_walk.ts --track <id>        # stage 4: drive proxy (dev server on 5179)
uv run --python 3.12 --with pillow python -I tools/track/compare/make_compare_sheets.py --track <id>   # compare sheets + index.md
uv run --python 3.12 --with numpy,scipy python -I tools/track/compare_package.py --cand tools/track/out/<id> --ref <dir> [--by-corner]
python3 -I tools/track/compare/compare_packages.py --ref <package> --cand <package>   # scenery object by object
npx tsx tools/calibrate/drive.ts --track tools/track/out/<id> --alat 1.2 --learn 25 --bank --no-files [--ref-ghosts <ghosts.json>]
```

Each stage prints its validation report and exits 1 without writing when a check fails. `--write-on-fail` writes anyway
for diagnosis; never publish such a package. Config keys by stage are all in `trackcfg.py`, and the template names the
step that fills each one:
- stage 0: `origin`, `osm_bbox`, `loop_ways`, `pit_lane_way`, `dem_tiles`, `lidar_ept`, `dem13`, `logger_dir`,
  `start_finish_latlon`, `corners`, `named_straights`, `captures`, `sources`;
- stage 1: `centre`, `centre_captures`, `repave_fixes`, `prior`, `shapes`, `spline`, `features`, `straights`, `gate`,
  `stations_ref`;
- stage 2: `ghosts`;
- stage 3: `scenery`, `pit_lane`, `structures`;
- app: `app`.

`reproduce` exists only to rebuild Laguna's accepted package byte for byte where its build had artefacts. A new circuit
never has one. Every new builder rule is config-gated: Laguna's and Sonoma's packages must come out of the pipeline
byte-identical after any builder change (rebuild stage 3 into `tools/track/out/<id>_*` and compare, and
`git diff main -- public/tracks/laguna_seca` empty).

## Stage 0: sources and the eye-level inventory (10 steps; REQUIRED before stage 3)

Why: satellite, lidar and OSM see only what is visible from above. Everything vertical lives at eye level: walls and
their heights, fences, tyre walls, stations, boards, cones. On Sonoma's round-3 build the owner found sixteen things in
one lap that nobody had caught:
- walls at the default 1 m, and a missing T10 outside wall;
- a pit lane with no walls, and a pit exit that never blends;
- a floating bridge;
- kerbs where there are none, and missing stations;
- a tent extruded to 12 m.

The onboard and Street View had been spot checks at places the builder chose. The inventory makes them a continuous
source, and the coverage gate (3.12) holds the package to it.

**0.1 The loop is the Lemons layout.** The configuration Lemons runs is the layout picture on that track's schedule page
on the Lemons website (24hoursoflemons.com, the event's page). Pin the loop from it before anything else. Confirm it
against a recent series onboard, the full lap and every junction. Then name the OSM `highway=raceway` ways that form it,
in driving order from the start/finish, in `loop_ways`.
- Laguna: the 8 circuit ways, "Pit Lane" excluded.
- Sonoma: 3 ways; the 2020 bypass, the Chute, the short T7 and the drag strip are not driven.

Several circuits map alternative loops and bypasses as raceway ways. The stitcher takes only the listed ways
(`'way:from_node:to_node'` takes part of a way) and fails loudly if they do not close. Also write down the start/finish
line (`start_finish_latlon`, from the painted line on the clean captures) and one lat/lon anchor per corner (`corners`).

**0.2 Data sources.**

| Input | Where | Needed for |
|---|---|---|
| Circuit centre `LAT0, LON0` and OSM bbox | OSM | local ENU frame (CONTRACTS §1), every script |
| OSM `highway=raceway` ways (the circuit is several named ways plus "Pit Lane"), `barrier=wall`/`fence`, buildings, `bridge=yes` ways | `curl -A "probe-sim/0.1" "https://api.openstreetmap.org/api/0.6/map?bbox=W,S,E,N"` cached as XML (Overpass was overloaded; the API map call worked) | loop, pit lane, scenery |
| USGS 3DEP 1 m DEM tiles covering the box | TNM staged products `prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/<project>/TIFF/`, read as windows over HTTP | profile, heightfield, banking |
| Entwine point tiles of the same survey | `usgs-lidar-public` bucket on AWS (not the rockyweb LAZ tiles: 40 KB/s) | lidar ground correction, trees, building, mast and bridge heights |
| 1/3 arc-second DEM tile | TNM `Elevation/13/TIFF/current/` | far terrain |
| NAIP via the image service, 0.6 m/px near, 5 m/px far | `imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/exportImage` | ortho, far ortho, scenery blobs |
| Clean Google satellite captures at z20 (0.12 m/px), overlapping, whole lap, with centre lat/lon and scale in `tiles.json` (0.3) | your own Chrome tab | painted edges, kerbs, walls, every scenery measurement (z19 at 0.34 m/px cannot trace a 12 cm line) |
| Team logger laps (optional): `centreline.npy` (ENU, 1 m, index 0 at the transponder line, driving order), `traces_warped.pkl` (t, v, thr, rpm, alat), `sections.pkl`, `official.pkl` | `~/projects/starlink-go-pro/laps` style analysis, read only | centreline shape, start/finish, direction, ghosts, racing line, κ ground truth |
| A RECENT onboard (2024+) of the Lemons layout and a recent video that drives the pit lane (0.4) | YouTube search, team footage | the inventory, the compare sheets, repaves, runoff, landmarks |
| Street View / photo spheres (0.5) | Google Maps | heights, what stands behind a wall, buildings |

**0.3 Clean captures.** Use Google Maps satellite at z20 in your own Chrome tab.
- Layers > More > untick Labels. Hide every UI element by page CSS (opacity 0 on everything at the screen corners and
  top bar) and park the cursor in a corner.
- Pan by dragging, because navigation turns the labels back on. Read each centre from the URL and run
  `register_clean.py`.
- Overlap the captures so every station is seen at least twice. Cover the pit lane, the paddock edges and every runoff,
  not only the road.
- Use **one common shift** for all captures (the median against the ortho; config `captures.common_shift`). The
  captures agree with each other to a pixel, while per-capture registrations against a 0.6 m ortho are noise and put
  0.3-0.6 m jogs at capture boundaries.
- Captures taken during an event are full of trailers and canopies. Note their date, and confirm any object that looks
  like a hut or a stack on the footage.

**0.4 Recent video.** Find one full lap of a RECENT onboard of the Lemons layout (the series' own or a team's, 2024
onward), plus any 2024+ video that drives the pit lane (pit in, the boxes, pit out). Search YouTube in your own Chrome
tab or through its search page in a headless Chrome, and open nothing from a result list in the extension: an agent's
tab once played an unrelated race broadcast with sound while the owner sat at the keyboard. Frames come from a
headless Chrome with a throwaway profile (`tools/track/compare/headless_capture.ts` on the buttonwillow branch; the
re-derivation used the same route): the watch page with `&t=<s>` in the URL (setting `currentTime` alone stalls),
muted and paused, the ad state detected and skipped, 720p forced, the frame drawn from the video element to a canvas
and saved. Never the embed (blocked for some videos, error 153), never a download. Frames go under
`tools/track/compare/<id>/inventory/frames/`
(ignored). Record each video (id, title, date, camera, lap time) in `inventory/source.json` and the config's `sources`.

**0.5 Street View survey (every circuit).** In your own Chrome tab (a headless Chrome renders Street View black; the
extension in the agent's own tab, exact panorama URLs only, the tab closed when done), open Google Maps Street View and
user photo spheres at every corner and major feature of the loop, on both sides where available. Use the circuit's own spheres, and the
road-side coverage of the access roads for stands and buildings. Record in `tools/track/compare/<id>/streetview.md`,
per place:
- the panorama id and heading, and the capture date;
- walls (side, material), catch fencing, tyre walls, corner-worker stands;
- kerb colour / width / height, runoff (paved / gravel / dirt), cones;
- bridges and gantries, buildings and towers, grandstands (size, construction).

Screenshots are reference only, never textures, never committed; the record is the deliverable. Check each panorama's
date against the recent onboard (source precedence).

**0.6 Step the lap every 2 s** (about 70 frames a lap; do them all).
- Grab the frames with the headless route of 0.4, one process per batch of times, never by playing the video in the
  extension.
- For each frame, write one row per object on each side into `inventory/observations.jsonl`:
  `{t, side, kind, attrs {type, colour, raised, h_m, h_method, ahead_m}, confidence, note}`. The kinds are wall, fence,
  kerb, tyre_wall, tyre_stack, stand, station, bridge, building, mast, cone_line, boards, paint, runoff (`inventory.py`
  KINDS).
- Log what is there, not what the package has.
- An object seen ahead gets `side: ahead` and, when you can tell, `ahead_m`. A wide-angle lens makes things look far
  (Sonoma's footbridge "85 m ahead" was 20 m), so time the object's passage instead.
- Log these too, because they are what the owner found missing:
  - every corner station (a roofed hut on legs, often behind the wall);
  - every cone (colour, size, spacing);
  - every board run, with the names it carries and where it starts and ends;
  - painted logos on the ground;
  - cushions and dark sections at wall heads, and tyre facings.

**0.7 Time-to-station map** (`inventory/source.json`).
- Anchors:
  - the start/finish crossings (s = 0 and L);
  - every corner apex you can time to 0.5 s (a 0.5 s 2x2 grid of the video around it), anchored to the package's
    corner stations (`track.json` corners);
  - landmarks with a known s: a bridge passing overhead, a wall nose, a Jersey start.
- Between anchors, t -> s follows a curvature speed profile's own time, because the car slows into corners
  (`interp: linear` gives a plain piecewise-linear map).
- `inventory.py` prints each anchor's leave-one-out residual and the mean speed in and out. A speed no car could do
  means a wrong anchor:
  - Sonoma's T1 at 0:05 implied 54 m/s to the footbridge and was dropped;
  - its S/F at 0:02.2 implied 45 m/s until 0.05 s captures put it at 0:01.2.
- Record each correction in `source.json` `corrections`.
- Sonoma ended with 18 anchors and residuals of 1-33 m with the profile (5-66 m linear). Where the map is ±40 m (braking
  for a hairpin), add an anchor at the next landmark before trusting the rows there.

**0.8 Pit lane and Street View rows.** Put rows with an explicit `s` and `source` (`onboard:<video>@<t>`,
`streetview:<panorama id>@<heading>`) in `pit.jsonl` (`scope: pit`) and `streetview.jsonl`. They cover what the lap video
cannot show: heights, what stands behind a wall, the pit lane end to end. Street View is old: keep it only where the
recent video shows the same structure.

**0.9 Heights by a method, never by default.** `tools/track/compare/HEIGHTS.md` gives the methods: horizon ratio with the
2.5 m Street View camera, a known-size reference (Jersey 0.81 m, SAFER ~1.1 m, fence posts ~3 m over the wall, a door,
a person, a car), the camera height from a Jersey barrier, and shadows. The helper is
`tools/track/inventory/heights.py`. Every `h_m` cites its `h_method`; `inventory.py` refuses one without and counts the
`unmeasured` ones.

**0.10 Validate.** `python3 -I tools/track/inventory/inventory.py --track <id>` validates and writes
`compare/<id>/inventory.json` and `inventory.md` (tracked; the frames are not). A misread row is never deleted. Correct
it with `attrs.correction` {round, was, why}: an object seen ahead gets `ahead_m`, a misread kind gets its kind, and an
added row is marked `added`.

## Stage 1: centreline, edges, profile (`build_track.py --stage geometry`; 12 steps)

Output: `tools/track/out/<id>/{track.json, heightfield.bin, ortho.jpg}`, `work/preview.png`, `work/geometry_report.json`.
Modules: `geo.py` (frames, OSM, DEM, NAIP), `centre.py` (first centre, NAIP edges, profile, corners), `paint.py`,
`recentre.py`, `edges_spline.py`, `straights.py`, `edge_gate.py`. The steps are the method; the config holds the numbers.
Iterating landmarks on wrong geometry wasted five rounds at Laguna, so stage 1 is accepted, by the gate and the hood
sheet, before stage 3 starts.

**Stage 1 reads three stage-3 keys, and its record does not hash them.** The centre refit's pit merge takes the pit-lane
parts, the barriers and the pit-exit cone line from `build_scenery` (config `pit_lane`, `scenery.declared_walls`,
`scenery.pit_exit_cones` and what those readers use), while `config_id('geometry')` leaves `scenery` and `pit_lane`
out. A later scenery edit can therefore move the centre without invalidating a passed stage-1 record. Measured on
20 Oct 2026: Sonoma's accepted geometry (built 19 Oct 18:05) rebuilt with its full config, the same geometry hash,
the same captures and lidar, gives 4101.9 m against the accepted 4098.8 m, with the left observation gate at 89.5 %
and the right waviness gate failing at 2752-2814; the re-derivation's reduced config gives 4099.1 m. Until the hash
covers what stage 1 reads, or the pit merge takes stage-1 keys only, treat those three keys as frozen once stage 1 has
passed: a change to them re-runs stage 1, and the re-run must pass before stage 3 runs on it.

**1.1 Loop.** Stitch the OSM raceway ways by shared end nodes into one loop, turn it to the driving direction, and roll
it so station 0 is the start/finish. Use 1 m stations. The pit lane is a separate way. With a logger, check OSM against
the GPS centreline (Laguna: median 3.2 m, p95 6.2 m) and station 0 against `centreline.npy[0]` (3.6 m).

- **Where the OSM way runs on an apron**, the first centre is corrected by a measured shift or by the OSM way that
  runs on the circuit, never by tracing. Otherwise the NAIP edges and the fit's search windows all start on the wrong
  pavement, and no edge knob gets there.
  - The OSM way on the circuit is a `loop_ways` part (`way:node:node`) when the ways share nodes.
  - Otherwise use `centre.prior_shift` [dict(knots=[(lat, lon, dx_m)], blend, src)]: points of the first centre with
    the lateral shift (+ left) of the real pavement's midline. The shift is interpolated along the stations and applied
    before the NAIP edges and the fit; the edges stay fitted.
  - The evidence form is a capture window with a 2 m ruler drawn across the first centre every 10 m, measured from the
    midline between the asphalt end and the block line, cited in `src`.
  - A shift changes the loop's length and so its station count. Freeze `stations_ref` (and `stations_ref.json`) to the
    accepted station frame first, so the config's stations, masks and kerb-search zones map by world position.
  - Buttonwillow, 20 Oct 2026: T1 exit, T10 and T11 exit, where the OSM ways run on the paved aprons beyond the block
    lines. Shifts of +11.0, -10.9 and +14.4 m put all three edges on their blocks.

**1.2 Frame registration before anything else.**
- Phase-correlate the captures against the NAIP `ortho.jpg` (Laguna: Google minus NAIP = −0.3 m east, 0.0 m north,
  all 42 tiles under 1 m).
- Then fit one rigid transform of the centreline to the painted road midpoint over all measured stations, and compare
  the residual before and after. Laguna: tx −0.09 m, ty +0.18 m, 0.02°, rms 2.12 m before and 2.13 m after, so no
  global shift was applied.
- If the residual drops, apply the one transform and re-sample the profile. If it does not, the error is in the
  centreline shape. At Laguna it was: the GPS-driven line cut every apex by 2.5 to 5.6 m (chord and smoothing on the
  logged line), so the painted midpoint sat outside the centre at every corner.
- **Check every capture's registration against its neighbours before tracing.** A capture that differs by more than
  0.5 m from both neighbours is excluded (`captures.exclude`) or re-captured. Laguna's `z20_s3400` was 1.3 m off and
  alone produced the front-straight hump, a left-edge wave and a pit wall "inside" the track. Record the exclusion in
  `track.json` notes.

**1.3 Centreline shape.**
- **With logger laps: from the driven line, not from OSM.**
  - Use `centreline.npy` (its curvature matched the IMU's κ to r = 0.98) and move it toward the painted-road midpoint
    with the penalised least-squares fit of `centre.py`. Config `centre.naip_fit_a/b` sets the NAIP pass and
    `centre.paint_fit_a/b` the paint refit.
  - `FIT_A` (a stiff second difference on the lateral move) keeps the driven curvature; `FIT_B` (a third difference on
    the positions) removes kinks.
  - Run two passes with the edges re-detected along the new normals, and plot κ from the IMU against the centre and the
    line (`kappa_check.png`).
  - The stiff fit (`FIT_A` 1e6) is only right when the driven line already sits mid-road. Where the logged line cuts
    the apexes, fit toward the painted midpoint with the soft weighted fit (`FIT_A` 1e3, as the 18 Oct rebuild did; the
    run that built the accepted centre used 1e4 with `FIT_B` 1e2, `recentre.py`). Laguna moved the centre p50 1.12 m,
    p90 3.15 m, max 5.34 m, and the painted-midpoint residual fell from 1.93 to 0.36 m rms.
  - The painted midpoint is measured by `paint.py` (config `centre_captures`, `centre_registration`).
- **Without logger laps** (`logger_dir=None` or `--no-logger`), the centreline comes from the painted road midpoint
  alone: OSM loop -> NAIP midpoint -> painted midpoint -> spline-fitted edges -> refit to their midpoint.
  - Use a soft move and stiff smoothing (`nologger_fit_a` 1e1 / `nologger_fit_b` 1e5) so the OSM nodes' kinks are not
    kept.
  - There are no ghosts: `ghosts.json` has the racing line and `laps: []`. The app, the scoreboard and the AI load it,
    and the AI corner finder runs on a curvature speed profile.
  - The racing line is the pure minimum-curvature line, and the autopilot lap replaces the implied-g checks.
  - **Measured on Laguna (19 Oct 2026, same config, logger removed; tools/track/out/laguna_dryrun/README.md):**
    - centre 1.15 m rms from the logger-built centre (worst 5.3 m at the Corkscrew and T11; 0.2-0.7 m rms at T2-T5,
      T9, T10; 3 m at T1, where the pit-out merge counts as road);
    - racing line 1.55 m rms (worst 5.0 m);
    - every corner tighter on the line by 1-27 % (T6 67 vs 81 m, Corkscrew 23 vs 31 m, T11 19 vs 23 m);
    - lap 3597.7 m vs 3588.0 m;
    - autopilot 2:03.19, against 2:01.84 for the logger-built package with the same command and 1:59.32 for the real
      best lap (T11 exit 41 vs 49 km/h).
  - Expect a no-logger circuit to drive about 1 % slow before the hand checks, most of it at its tightest corners. Check
    those against the onboard first.
- **Stations.**
  - Keep the station count and resample uniformly: `spacing_m` = L / n (Laguna 3588.05 m / 3560 = 1.007879; the
    projector and the AI line honour `spacing_m`).
  - Old station k lands at new station u(k), up to 11.6 m apart at Laguna. Remap every s-ranged scenery item through
    u(k) so it keeps its world position (config station numbers refer to `stations_ref` and are mapped by world
    position).
  - Re-run the ghost build in full so t/v are re-projected by world position, and re-solve the racing line (stage 2)
    rather than carrying the old `offset_m`, which would drag the apexes outward with the centre.
- **Acceptance, printed by the geometry stage:**
  - the lap length within 1 % of the official figure (Laguna 3588 vs 3602; the old centre gave 3560);
  - on the first centre, within ±60 m of every corner, the minimum radius within 15 % of the driven line's (limit
    25 %). The paint refit then tightens the apexes the logged line cut, so the final radii are printed, not checked;
  - the largest lateral edge change between adjacent stations under 0.5 m.

**1.4 Edges are FITTED, never traced** (owner, 18 Oct 2026). Per-station tracing, short smoothing and stretch patches with
blends made 20-80 m waves of 0.3-1 m. The hood camera sees them end-on; the top-down sheets cannot (record:
compare/edge_sweep_2026-10-18/t2_waviness_review/ and t2_spline_fit/). Use `edges_spline.py` (config `spline`: runs,
knot 6, lam 30, huber 0.25, line_off 0.26, prior 0.03), per side:
- Candidates: every painted-line inner side (+0.26 m) and kerb outer limit.
- Fit: a penalised cubic B-spline (6-station knots, `--lam 30`) with a Huber loss of 0.25 m, so a bad station cannot
  make a bump. Associate each candidate with the nearest one under a shrinking gate. The current edge is a weak prior
  (0.03), only for gaps, and joins are anchored.
- Masks: mask bridges, walls, boards and gantries before measuring. Detect the white line itself (brightness and 12 cm
  width), not the first non-asphalt pixel.
- Kerb zones come from red in the imagery.
- An explicit FEATURES table covers ambiguous places (config `features`: 'keep', 'asphalt_end', 'kerb'). Laguna: the
  Andretti apex inside is asphalt end. Sonoma: the T7 road left is asphalt to the wall with no paint.
- Measured shapes (`shapes`, a monotone cubic through station:half-width knots) and declared straights (`straights`: a
  RANSAC line on the painted line, or a constant gap inside a straight pit wall, `fit: 'parallel'` to the other side)
  go into the prior before the fit and are applied again after it.
- The prior can take the first build's NAIP edge over a stretch (`prior.first_edge`, Laguna's Rahal left) or be
  interpolated across a junction (`prior.interp`).
- Keep the real features: corner swings, apron widenings, pit-lane joins.

**1.5 The edge convention, at every station.**
- **Where the edge is.** The painted line where there is no kerb, and the flat kerb's outer limit where there is one
  (sausage strips then sit behind the kerb). Kerbs and painted lines count as road.
- **Per side.** Store left and right separately (median difference 0.8 m, up to 4.4 m at Laguna); the profile fractions
  scale each side.
- **Painted runoff strips** (green verge, teal aprons) lie OUTSIDE the edge. A first-non-asphalt detector puts the edge
  at their outer limit: at Laguna's T11 exit it was 3 m too wide, with the verge then painted a second time on the
  shoulder.
- **Corners.** Never chord a hairpin or the Corkscrew: its painted swing is real. Apexes with a kerb at the bottom of a V
  and dirt beyond (Laguna T6, T10, T11, T8) go to the kerb limit. Check the AI corridor afterwards: a 3.8 m move at T8
  put a self-play car off at T8A.
- **Bridges and painted stripes.** Bridge shadows read as painted lines and put a 1 to 4 m kink under each bridge where
  the road is straight. Discard measurements within 25 stations of a bridge crossing (`centre.bridge_win`) and
  interpolate the prior across ±35 stations (`prior.bridge_win`). Painted lines across the road, like Sonoma's chequered
  S/F stripe, go in `prior.extra_bridges`.
- **Junctions.** Keep the old edge where a pit-lane join or the pit-exit blend lane touches the track.
- **Block-line kerbs on wider pavement.** On a circuit where paved aprons or runoffs meet the track with no paint and a
  line of kerb blocks separates them (Buttonwillow), an asphalt-end edge runs out to the far side of the apron.
  - Reach the blocks. The kerb search must reach the blocks wherever they sit, not only ±1.5 m from the current edge.
    Give each such zone a `kerb_band` feature and its own search window in `spline.kerb_search`
    [(side, lo, hi, (w_lo, w_hi), src)]. The window also works for `asphalt_end` and `warm_end` zones.
  - Cite the evidence. Each zone cites its capture window and onboard frame, and its side follows the onboard: blocks on
    the car's right are the right edge.
  - Look first. `kerb_detect.py --offs=-10,-1` lists the candidates.
  - Buttonwillow, 20 Oct 2026. Nine block lines sat 1.3-16 m inside the fitted edges; 13 onboard kerb rows were MISSING
    in stage 3. The T1-exit line runs diagonally across the whole fitted track, and the flying lap runs west of it.
  - What the fit cannot do. It moves an edge only as far as its gate lets an observation pull the curve (1.2 m on the
    first pass). It cannot jump 13-16 m. Where a block line ends and the apron edge runs on 4-5 m out, the edge-gate step
    (0.1 m per station) fails. Both are reported, not forced.
- **The operator's width range is a stage-1 advisory check.** Put the published track width in `spline.report_width`
  (Buttonwillow: 36-55 ft = 10.97-16.76 m). Then read the report's shares of stations outside it. Stations over the top
  usually mean an apron fitted as track, so look at each run on a capture window. Buttonwillow before the block-line
  zones: p90 16.94 m, max 19.33 m at s 2437, 12.0 % of stations over 16.76 m.
- **Laguna's result:** painted width median 12.9 → 11.6 m (p5 8.7, p95 16.0); apex half-widths such as T6 3.0/8.9 →
  4.1/4.8 m and T11 3.0/9.6 → 5.4/6.6 m; front straight 7.9/8.5 → 4.7/5.4 m. The AI Probe's solo lap went from 120.4 s
  on the wide track to 123.8 s on the painted road with the old driver, and to 120.2 s once the AI's speed profile
  credited banking and crests (real best lap 119.3 s). Expect a lap-time step from an edge rebuild, and look for it in
  the driver before the tyres.

**1.6 Profile, heightfield, repaves.**
- **Profile.** Set `z0_navd88` at the start/finish centre. Build the profile from the 1 m DEM smoothed σ = 0.7 m, then
  `lidar_correct` it onto the ground returns (gaps filled along s, 7-station median, 4 m Gaussian). Then
  `clean_profile`: edge points ≤ 4 cm off the line through the five inner points, every point ≤ 2 cm off the section
  quadratic, a 5-station median and a 1.5 m Gaussian along s.
- **Heightfield.** Unsmoothed DEM, bilinear, a 2 m grid over the box plus ~220 m, agreeing with the profile on the
  centreline to 5 mm.
- **Banking.** Banking from the lidar is real (12 to 15 % at Laguna's T5, Corkscrew and Rainey). The cross-slope limit
  is 16 %; every station over 12 % is listed and checked near-planar. Ignore bridge decks classed as ground. Edge points
  on a berm or kerb face are replaced by the road plane extended to the edge.
- **Repaves.** Use `repave_fixes` only where the footage or the owner's own laps contradict the survey. Laguna T6 had a
  0.4 m sag in the 2017 lidar and has been a crest since the 2023 repave.
  - Rebuild the centre height over the window from its vertical curvature: a crest or flat in the crest zone, and a
    gentle sag elsewhere (R ≥ 1500 m).
  - Heights and slopes match at the window ends, and the change is the same across the section, so banking is kept.
  - Carry it into the heightfield, fading 2 to 12 m beyond the edges.
  - Fix only the hollows the footage confirms; grade changes are not dips.

**1.7 Corners.** Signed-curvature peaks within ±45 m of the corner anchors (an optional 7th element sets another window),
each with `name`, `turn`, `s`, `radius_m`, `dir`. Anchor a long constant arc at its slow point (Sonoma T10: window 3 m).
Named straights sit halfway between their corners.

**1.8 Roughness check** (`previews/profile_roughness.png`).
- 1 m second differences implying a vertical radius under 150 m are allowed only where the lidar shows a real crest or
  drop (the Corkscrew at R ≈ 45 to 80 m).
- Single-station steps over 1.5 cm must be near zero.
- The apex minimum 1 m radius must be 155 m or more.

**1.9 Edge gate, which fails the build** (`edge_gate.py`, config `gate`).
- The edge residual against a 41-station median stays under 10 cm rms on straights. Laguna lands at 0.09-0.10 m after
  the sweep; the 5 cm first written here was never reached, not even by the baseline, and the hood sheet shows nothing at
  that level.
- No slope over 0.10 m per station outside tight corners.
- The printed local waviness (residual about a ±25-station quadratic, rolling 100 m) and the kink per station pass.
- Observation residuals: 90 %+ within 0.25 m.
- Coverage passes (60 % of stations).
- **Unpainted sides (the owner's decision, 20 Oct 2026; `edge_gate.UNPAINTED`, `side_within_gate`, code-defined, no
  per-track numbers).** On a side with no painted edge line, the curve must run through the middle of the ragged evidence,
  with the fit-quality gates binding; painted circuits are untouched.
  - A side is unpainted when `asphalt_end` readings are the majority of its associated readings
    (`asphalt_end_majority`).
  - At Buttonwillow the 2026 captures and the 2021 lidar show a 2-4 m asphalt-to-dirt transition. The readings agree
    across captures (98 % within 0.25 m of their station's median) but scatter along the track (46-50 % within 0.25 m
    of the fitted edge).
  - An unpainted side's within gate is a **bias gate over all its readings**, `asphalt_end` and kerb pooled: over
    rolling 41-station windows holding at least 10 readings, the median signed residual (reading minus fitted edge) lies
    within ±0.25 m in at least 90 % of the windows. The worst window is listed with its stations, and the spread is
    printed, not gated.
  - Its coverage threshold is 50 % of stations (Buttonwillow 54 / 56 %).
  - Why kerbs are pooled: the grey block bands of an unpainted circuit blur on the captures like the asphalt end
    (Buttonwillow: 85-86 % within 0.25 m, a 0.25-0.6 m tail, zone medians within ±0.05 m).
  - The numbers per evidence kind are a printed report, never gated. The bias gate still catches a zone that sits off
    centre: fix such a zone from its capture window.
  - A painted side keeps the gates above, computed exactly as before. Longest gap, waviness, kink, the edge gate, world
    continuity and profile are unchanged. A config may only tighten.
  - An object beside an unpainted edge that the detector reads as the edge (a marshal mound) is masked with
    `spline.mask` [(side, lo, hi, capture)], never exempted.
  - The owner's fallback for a circuit worse than Buttonwillow: "the owner draws the edges on the captures", a future
    evidence feature (an owner-traced edge), not implemented.
- World continuity: the edge polyline's third difference stays ≤ 2 cm.
- Wall offsets stay steady where a wall runs parallel.
- Width changes slowly except at kerbs and junctions.
- No step over 10 cm in any profile column (Laguna 0.09 m at the Corkscrew).
- Junction exemptions (`gate.exempt`) name the capture that shows the junction.
- **Exit overshoot** is advisory, not a build failure: within the first 120 stations after the centre radius is back over
  150 m, the road width (left + right half-width, independent of where the centre sits) must not overshoot its value at
  the window end by more than 1 m. It also fires on real features (Laguna's pit-out merge at T1, the pit rejoin after
  T2, the T7 approach where the kerb narrows the road by 2 m), so check each line on the capture. Half-width alone
  fires at every apex the centreline cuts.

**Sweep kit for the edge rounds** (all under `tools/track/`):
- `sweep_paint.py`: the paint check per station, anchored at the current edge;
- `compare/straight_strip.py --side`: edge-relative strips with the current edge as the middle row, so deviations read
  off directly. Trace straights with two references;
- `edge_gate.py`;
- `compare/edges_overlay.py`, with `OLD_REF` and the registration shifts applied;
- a hood-level contact sheet of every changed place.

An inventory with station ranges and the tile evidence goes to the owner before anything is applied.

**Barrier gaps** are part of the same gate: every barrier point is at least 0.5 m from the nearest edge, and pit walls
stand at a constant measured gap along a straight. The gate is printed with `edge_gate.py` and re-run in stage 3.

**1.10 Driver's-eye sheet of the whole lap** before stage 2 is accepted: the hood camera every 50-75 m
(`camera_walk.ts --no-rows --back-step 0 --pit-step 0 --no-runoff`), reviewed by the orchestrator. Corner frames catch
landmarks; only this catches waves. Pit-lane and apron boundaries are moved onto the new edge by the script.

**Validate the geometry by driving it, not by looking at it.** The autopilot (`tools/calibrate/drive.ts`) on the ghost
racing line, compared corner by corner with the real ghost laps, exposed Laguna's v1 centreline: 11 to 21 % slow at T5,
T6, the Corkscrew and T11, because the radii were 20 to 70 % too tight. The IMU's lateral acceleration gives the
ground-truth curvature, κ = alat / v², to check any centreline against.

**1.11 Derived data rebuilds automatically after any edge change** (one script): racing line and ghosts
(`build_ghosts.py`), the on-pavement fixture (`record_onpave.ts`), field pace (`calibrate_field.ts`), then the gate.
Otherwise "alone racing line rms" and the surface fixture go red and the AI gate is noise. Edge-relative scenery (kerb
strips, verge paint, sausages) is drawn from the edge, so a wavy edge shows up as a wavy kerb. The pipeline rebuilds
everything from raw inputs every time, which makes it idempotent; every argument lives in the config.

**1.12 Paved shoulders in the same pass**, as `paved_zones` parts level with the road, wherever the onboard shows
pavement to a wall or apron.

## Stage 2: ghosts and racing line (`build_track.py --stage ghosts`; 3 steps)

This runs `tools/ghosts/build_ghosts.py --config <id> --track-dir <dir>`. Output: `ghosts.json`,
`work/preview_ghosts.png`, `work/kappa_check.png`. Config: `logger_*` and `ghosts` (margin, kerb_margin, nudge, jerk_w,
implied_g_turns, implied_g_exempt, kappa_drivers).

**2.1 Laps** (logger only). Lap times are scaled to the official timing. Take each driver's best clean lap, and the
optimal lap from `optimal.solve` over clean good-GPS laps, stitched section by section. Logger distance is mapped onto
track s by projecting `centreline.npy` onto the centre, smoothed and monotonic.

**2.2 Racing line.** Bounded least squares (active set) on curvature plus 3× curvature change, with bounds at a smoothed
lower envelope of each side's edge less 1 m. Then a second bounded solve pulls 30 % toward the measured good-GPS line.
This is not a clipped blend, which kinked where the measured line lay outside the bounds. Without a logger, it is the
pure minimum-curvature line.

**2.3 Implied-g table per corner,** plain and tyre share after banking, μ = (a − tan b)/(1 + a·tan b): tyre share ≤ 1.3
at apexes, ≤ 1.35 anywhere, plain ≥ 0.9. Re-run only when station 0 or the length changes. Without a logger, the
autopilot lap (stage 5) checks the line instead.

## Stage 3: scenery from evidence (`build_track.py --stage scenery`; 13 steps)

The stage runs `build_scenery.py`, then `scenery_post.py`, then `build_structures.py`, then the gates.
- Output: `scenery.json`, `far_heightfield.bin`, `far_ortho.jpg`, the regraded `ortho.jpg`, `work/scenery_preview.png`,
  `work/gates_report.json`, `work/coverage_report.json`.
- Every placement derives from `track.json` and the config (kerb ranges, barrier runs, boards, the lidar box), so one
  command regenerates it after any track change. The lidar and NAIP caches are keyed by the box.
- The objects and their keys are in `tools/track/kit/README.md`. An object the kit lacks gets a new config key with a
  builder change, never a hand edit of scenery.json. What the Laguna footage rounds placed by hand
  (compare/satellite/apply_round*.py) is the example of what not to do.

**3.1 No object without a cited source; the manifest.** Sonoma's round-2 scenery was rejected ("not ready for me to
review") because every miss came from Laguna's generic rules:
- a radius-rule kerb on T7's open side, and Laguna's green after-kerb strip and flat profile;
- a brake board in the pit-in lane, and the pit wall closing the pit exit;
- the drag strip reachable from the T1 runoff;
- OSM grandstand slabs where the stands are terraces;
- missing walls and corner stations.

Every kerb strip, wall, tyre wall, fence, grandstand, corner station, sign, cone line and structure traces to evidence:
- a clean z20 capture `c20_…`;
- a Street View panorama id (its date checked against the recent onboard);
- an onboard time (`m:ss` / frame `t###`);
- OSM;
- or the lidar.

The config entry carries that source in `src`, and heights carry `h_src`. Laguna's rules are off for every other circuit
(`brake_board_corners=[]`, `corner_boards=False`, `flagstand=False`, `pit_wall=dict(rule=False)`); the template starts
there.

Keep `tools/track/compare/<id>/manifest.md` round by round. It holds:
- one row per object (kind, side, stations, source, how measured);
- a "removed for lack of evidence" table;
- the survey walk (every Street View spot: placed or not, and why);
- each scan, with the captures examined;
- the dispositions (3.13).

Its object and row tables are generated by `manifest_tables.ts`.

**Laguna's post-step keys** were scripts on 18 Oct: `shoulder_zones` (paved shoulders), `aprons`, `pitwall_end` /
`pitwall_setback` / `pitwall_straight`, `kerb_extents`, `edge_line_runs`, `pit_exit_cones`, plus `tyre_corners`,
`paved_runoff`, `brake_board_corners`, `no_exit_kerb`, `pit_wall`, `oak`, `gantry`, `banner_boards`, `hangars` and
`bridge_style`. They stay available, each used only with the evidence the rule asks for.

**3.2 Data-derived ground** (rules, no per-object evidence):
- **Ortho grade** (`grade_ortho`): one black point for all channels (0.5th percentile), one white point, gamma 1.25, a
  25 % smoothstep S-curve, +6 % saturation. Per-channel black points turn dry grass orange. The washed-out look was the
  renderer (ACES exposure ×1.75, cold sky fill 1.4, fog from 500 m), fixed in the app, not the data.
- **Lidar grids** at 1 m: the bare-earth DEM, the max of all returns, the max of class 1, the max of class 17 (bridge
  deck), and the multi-return share of class 1. The survey has no vegetation or building classes.
- **Trees:**
  - class-1 height over 2 m with a multi-return share over 0.18 (roofs are single-return);
  - crowns are local maxima over 3 m at least ~4 m apart, with radius √(area/π) clamped to 1.2-11 m;
  - building footprints and anything within 1.5 m of the edge are masked;
  - the app removes any tree within 10 m beyond its crown of any driveable centreline (track, pit lane, paved runoff):
    no trees where a car can go;
  - far trees are dark greenish blobs in the 5 m/px NAIP, capped at 7000.
- **Far terrain:** 5 × 5 km at 10 m from the 1/3 arc-second DEM with the near heightfield copied in.
- **Season tint** (`scenery.season_tint`, optional): the summer NAIP's dry grass shifted to the footage's season, on the
  published ortho / far_ortho only, as the stage's last step. The NAIP cache, the paint detector and the tree tests read
  the untinted images. Put a before / after sheet in the manifest's evidence folder. Known limit: ploughed and pale
  fields go green too.
- **Seam and continuity:** the ribbon carries shoulder rows snapped onto the terrain mesh, with no height lift, and the
  physics blends from the edge height to the heightfield over the shoulder. After every scenery build, run the in-page
  continuity scan (`scan_surfaces.js`):
  - every ribbon, shoulder, pit, zone, kerb and line triangle is checked against `window.__sim.surface`, flagged over
    2 cm;
  - the surface is walked from 0.5 m inside to 18 m outside each edge, for steps and slope changes over 8 % per metre.

  Fix the data that creases.

**3.3 Kerbs from the imagery** (`scenery.kerbs_declared`, `scenery.kerb`, `kerb_lines`).
- **Detect.** `compare/kerb_detect.py` finds the painted block pattern along BOTH edges. Confirm each run on
  `compare/capstrip.py` / `capwin.py` and the onboard.
- **Declare** each run's ends (lat, lon on the edge), colour (per strip or a `kerb.palettes` name) and band offset
  (`off`).
- **Only where the captures show one.** Check both sides of every corner:
  - Sonoma T7 left had none;
  - 3a had a kerb on the right only;
  - T1's outside had two striped runs joined by a block line (kind `blocks`, drawn only).
- No green verge or after-kerb strip unless the imagery shows it.
- **A strip's extent is measured, not inherited** from the radius rule or an earlier build. Edge-relative strips move
  with the edge.
- **Measure** the width and block period on the captures, and the colours on the recent onboard (Sonoma's 2011 blue /
  white was repainted red / white in the 2024 repave).
- **Colour and pattern per strip, never a track-wide default** (Sonoma owner note 58: round 3 set every strip red /
  white; the T5 inside kerb is a plain yellow strip). For EACH strip, map its stations to onboard times, look at the
  frames that show it, and declare what they show: `colors` (a pair or a `kerb.palettes` name) and `pattern` ('blocks':
  red / white, blue / white, ... alternating; 'plain': one colour, e.g. plain yellow). Record the frame in the strip's
  `colour_src` and in the manifest's per-strip kerb table. A strip no local frame shows keeps its colour with
  `colour_src='colour unverified: no local frame (...)'` and goes to the owner. `kerb.require_colour_src=True` fails the
  stage on a strip without one; `kerb.colors` stays only as the fallback.
- **Kerb height** per track (`kerb.profile` {height, face, back}) is read by the physics (`createTrackSurface` option
  `kerbs`) and the app from scenery.json; absent means flat paint. The kerb traversal gate (3.12) holds it. Sonoma's
  10 cm profile rolled the car (`compare/sonoma/kerb_rollover.md`); 5 cm over a 0.25 m face felt right.
- **Raised kerb lines** on island kerb paint (`kerb_lines`) are measured on the paint.
- **Sausage kerbs** (`sausages`: height 0.06, width 0.5, gap 0.25, kerb_width 0.9) go only where stills show them. The
  raised-cosine profile with a tyre-widened half-width and slope cap 0.6 drives correctly; 13 cm with steep flanks rolled
  the car.
- **Laguna's rule kerbs stay for Laguna only:**
  - an apex kerb inside every directed corner (half-length 0.9 × radius, 28 to 45 m);
  - an exit kerb outside from s + 15 m, 45 to 70 m, with 1.5 m green beyond;
  - 0.9 m wide inside the edge, red/white every 2 m with a dark seam.

**3.4 Walls and barriers measured, not assumed** (`scenery.declared_walls`, `osm_barrier_overrides`, `tyre_facings`,
`impact_barriers`).
- **Bands are barriers.** A continuous narrow bright or dark band parallel to the track 2-45 m out on the captures (and
  the light band it leaves in the NAIP ground) is a barrier line unless the onboard shows otherwise. Sonoma's owner
  note 11 was a light band at the foot of the hill where the wall stands.
  - Scan EVERY outside-of-corner stretch and both sides of every straight. The scan is a ledger in the manifest: one
    row per clean capture and side, including the captures with nothing on them, so the orchestrator can see what was
    looked at. The far lines count: Sonoma's T3 and T4 tyre lines stand 20-37 m out and the T9 bank carries a wall,
    tyres and a fence on one line 19 m out. The re-derivation of 20 Oct 2026 found 27 of the accepted 84 runs because
    it measured where the inventory rows pointed and nowhere else, and the coverage gate (±15 m of a row) passed.
  - Measure each band with `compare/wall_measure.py` and a guide (ENU, lat/lon, track s/lateral `--sguide`, or along an
    edge `--edge --off`). It picks the bright concrete top or the dark tyre stack every 0.5 m. Put the polyline, rms and
    pick rate in the `src`.
  - Confirm each on the onboard, and list every band examined in the manifest (placed or not, and why).
- **A bright line is not a wall until the onboard shows one.** Painted edges and drag-strip lane edges pick as bright
  bands. Check every declared wall's head against the frames: Sonoma's drag-strip far wall and T6-T7 head were paint.
- **Heights from evidence.** Each wall carries `h` / `fence` read off the onboard against the hood line or Street View
  scale (Jersey 0.81 m, SAFER ~1.1 m, fence posts ~3 m over the wall), with the method in `h_src`. Unread heights stay
  1.0 m and the manifest says so. Walls that enclose (Sonoma T10-T12) are what makes a place feel like itself.
- **Joins.** A wall measured on two captures is one run. Re-measure across the capture boundary instead of declaring two
  runs that step at the joint (Sonoma T5).
- **Wall ends.** A wall's upstream end within 8 m of an edge must be joined, lapped, cushioned, tapered, or leave the
  track at > 60°:
  - joined: another run, a tyre cushion or an impact block within 1.5 m;
  - lapped: a run on the same side ending within 25 m upstream, closer to the track;
  - cushioned: declare the cushion the onboard shows (Sonoma's T6-T7 wall starts with a black section; T5 is one
    continuous Jersey);
  - tapered: 1.5 m further out at its head than 10 m on.

  The app caps every rigid end.
- **Push-out.** A declared point inside the barrier-gap minimum is moved out to the minimum + 0.05 m and logged (0.55 m;
  0.35 m for kind 'pitwall', per point). A short wall whose upstream end stays within 8 m of the edge still needs its end
  protection from the evidence (Sonoma's T1 pit-side wall, round 7f, waits on the owner for that).
- **Facings.** A tyre run beside a wall stands against its track face (`tyre_facings` {reach, off}: tyre points within
  reach move onto the wall's track side) or meets it end to end, never parallel 0.8-2.5 m off (Sonoma 8a). Impact blocks
  at noses go in `impact_barriers` {wall, end, w, d, h, color}.
- **Stacked tyres.** Tyre runs render as stacked tyres with `stack` (tyres per stack, from the evidence or round(h /
  0.23)) and a colour per run (black / white as the footage). Sonoma's T11 hairpin is white, two high.
- **Movable barriers.** A barrier present in road-race footage but absent from the capture (taken at another kind of
  event) is placed from the footage, with the owner's placement recorded in `src`, and flagged **movable** in the
  manifest (Sonoma's T7 paddock Jersey with its black tyre facing, round 7d).
- **Other keys.** `drop_within` drops the parts of a wall the course itself runs over; `cut` trims a wall at a lane
  mouth. OSM walls are re-kinded or dropped on evidence (`osm_barrier_overrides`). Barriers are collision runs, so place
  nothing on the road.
- **Laguna's rule barriers stay for Laguna only:**
  - OSM walls resampled at 2 m and pushed out to ≥ 2 m from the edge;
  - a median distance under 14 m means 1 m concrete plus a 3 m catch fence, else Armco;
  - tyre walls by metres before/after the corner s on the outside of the heavy-braking and runoff corners, 1 m in front
    of the nearest wall (12 m out if none), rendered as stacks every 0.58 m with a white pair every 12;
  - pit walls at a constant measured gap along a straight (Laguna 2.0 m left, 4.0 m right to the concrete).
  - OSM polylines cut across the paint at wall noses, and walls from OSM run past their real ends. Measure the nose
    and the end (Laguna: the hot-pit wall ends at the pit-out lane; the painted strip alone separates the lane from the
    track to T1).

**3.5 Pit lane first-class** (config `pit_lane`, `trackcfg.py`; `trackcfg.check_pit_lane`).
- **Declare the lane end to end from the pit-lane video and the captures:**
  - the lane (`osm` or `declared` latlon, width_m);
  - the walls (side, stations or lat/lon ends, height, material, fence, src);
  - boxes, buildings and furniture.

  Each declared wall has geometry: `latlon` measured on the captures (built as a barrier), or `declared` naming the
  scenery wall it is. `pit_lane_clip_walls` keeps the lane polygon inside its walls. The lane is clipped at declared
  cone lines as at walls.
- **Pit-in.**
  - The separation wall between the track and the pit-in lane, with its impact barrier at the nose and the cones along
    the double line, as the footage shows (Sonoma owner notes 15-16).
  - Walls on both sides of the lane where the footage shows them (note 18).
  - No rule board stands in a pit lane (note 1).
- **Pit-out and blend.**
  - The pit-side wall ends at its nose; it never closes the exit (note 2).
  - Beyond the nose, the lane and the track are one surface in plan, height and tone. `pit_lane.lane.match_track_tone`
    maps the ortho inside the lane polygon onto the track asphalt's tone, because the lighter NAIP paving and paint
    smears read as a second road (notes 17, 24-26).
  - The blend line is the painted line measured on the captures (`paint_lines_declared`, its colour from the footage,
    e.g. a double yellow; `edge_line_cut` where the edge paint is not the white line).
  - Where parked vehicles hide the line on the captures, take it from the footage and from the wall it continues:
    Sonoma's blend line is the straight continuation of the pit wall's line past its nose (owner note 55).
  - The lane's outer edge beyond the line's end is the track edge, with no polygon angling across.
- **Cones from evidence.** Colour, size and spacing come from the footage. Cones stand ON the measured painted line
  (`pit_exit_cones.latlon`, `cone_lines_declared[].latlon`), never at an offset from the fitted edge, which can follow a
  wall at a lane mouth. Sonoma's pit-out cones are small yellow 0.5 m cones every 17 m on the double yellow line, not
  the large orange line along the front straight that round 6 drew (notes 42-43).
- **Driven by the gates:** pit connectivity with the lane paths, and the pit-lane walls gate (3.12).

**3.6 Closed roads and runoff** (`scenery.closed_roads`, `paved_areas`, `gates.allowed`).
- **Closed roads are race surface.** Paved roads of the circuit that the loop does not use are driveable (owner note 12).
  - Declare each with `surface` (asphalt / concrete from the captures) and `paint=True` (painted edges by `paint.measure`
    along its centre).
  - `edges_from_paint` puts the paving edge on the measured paint wherever paint is measured within 8 m, so the seams lie
    on measured lines (note 45).
  - `closed_roads_clip_walls` stops the paving at its walls.
  - Every paved stretch the course does not use is declared, including a road's continuation past a fork the course
    leaves (Sonoma's drag strip past the T7 fork, OSM 834724051, was unpaved ground until round 7e, owner note 57).
  - Closed-road edge lines stop at the circuit's paved width; they are never drawn across the track at a mouth.
- **Cones** go across a mouth only where the footage or the captures show them (`mouth_cones` {near, src}). An inside
  runoff the cars may use gets no cones (`cones=False`).
- **Parked areas.** Paved ground the ortho fills with parked vehicles is drawn as plain paving (`paved_areas`).
- **Containment.** Every paved polygon the track reaches without a barrier is either walled off or listed in
  `gates.allowed` (target, side, stretch as lat/lon on the track, and why, with evidence that it is open). Sonoma's T1
  runoff reached the drag strip until its wall was declared (note 4).
- **Paved runoff** (Laguna, `paved_runoff`, from the footage, later than the lidar):
  - the zone runs from the edge to 1.5 m short of the wall, with tapered ends;
  - its heights are the surface the car drives on, blending from the edge to the heightfield over 5 m. Never use a flat
    DEM fit, which creased the kerbs and paint at the zone ends;
  - it is rendered in the aerial's own colour.

**3.7 Stands, buildings and structures** (`scenery.terraces`, building keys, config `structures`).
- **Hillside stands from a measured footprint,** not the OSM outline.
  - `compare/terrace_measure.py` (ray mode, `--json`) reads the seating field as a texture on the clean captures (rows
    every 1.1-1.25 m across the strip). It takes the lower and upper edge per ray, and the DEM crest less 3 m where the
    captures end; `--fill-osm <way>` is only for rays the captures do not reach.
  - The result goes in `scenery.terraces` as `front` / `back` (lat/lon, matched by index; `osm` then only suppresses
    the slab).
  - The rows follow the stand (polyline rows on the ground at each tread's back edge). The app lifts them onto the drawn
    3 m terrain mesh and draws bleacher-grey concrete with a dark line per row (part self-lit).
  - OSM outlines cut straight rows across curved banks, so 20-36 % of each tread was buried and the rest floated,
    invisible from the track.
  - Check each stand's start and end against the onboard: Sonoma's back-straight stand ended at the access road, not
    at 9a.
  - Verify from the track with `compare/pose_walk.ts` (`--hide name` isolates a mesh). `grandstand_on_terrain` sets
    stands on the terrain, and `terrace_dress` adds benches, aisles and shade roofs.
- **Building heights from a robust lidar statistic** (`scenery.building_height_robust`): the 60th percentile of the
  lidar surface above the footprint's ground.
  - Use the p50 where p90 - p50 > 6 m (logged: a mast, tower or hillside inside the outline).
  - Drop the footprint when p90 < 2.5 m (logged).
  - The p85 rule made Sonoma's main grandstand a 25.6 m block. Check the tallest few against Street View storeys and the
    captures, and write them in the manifest.
- **Newer evidence over lidar.**
  - `scenery.building_overrides` [{osm | contains, h | drop | plain, src}] applies only where a newer source contradicts
    the lidar. Each use is logged, and an unmatched entry fails the stage.
  - `building_evidence` [{contains, src | drop}] gives each OSM building its 2026 source, or drops it. Sonoma dropped 10
    with no 2026 source, and a temporary tent on the newest onboard. Two behaviours to know (the re-derivation of 20 Oct
    2026): the coverage gate can report a building as UNSUPPORTED although a capture shows it when it has no
    `building_evidence` entry, so every kept building gets its entry with the capture id or onboard time; and an entry
    for a footprint that `suppress_osm` also names keeps the building, so a footprint is in one list, never both. A
    paddock building standing on the 2026 captures has its source (the capture); the re-derivation dropped 13 for want
    of one and kept 9 of the accepted 17.
- **Structures** (config `structures`, `build_structures.py`, app `src/app/structures.ts`: parametric generators in three
  merged meshes). Grandstands, pit and paddock garages, blocks, fuel islands, masts, pit-box lines, pit-wall boards and
  tall singular structures (a scoring tower: an isolated lidar spike plus the capture's base and shadow) are declared
  here. Every item carries `src` and `h_src`.
  - Footprints come from OSM (`osm=`) or lat/lon on the clean captures.
  - Heights come from lidar profiles across the outline (DSM - DEM every 2 m), checked against storeys.
  - Masts come from isolated lidar spikes, each confirmed on a capture window.
  - Colours and shapes come from the most recent video, not 2011 Street View (owner notes 20-25).
  - `suppress_osm` lists the OSM boxes a structure replaces (each must match, logged).

  Shoot before / after / reference sheets with `compare/pose_walk.ts` (it also reports draw calls and triangles) and
  keep the kit under ~150k triangles.

**3.8 Furniture** (`marshal_posts`, `tyre_stacks`, `blocks`, `light_masts`, `cone_lines_declared`).
- **Marshal huts.**
  - Scan for 2-5 m bright blobs within 25 m of the edges, and inspect each on a capture window.
  - Captures taken during an event are full of trailers, so place a hut only when the onboard, an owner frame or Street
    View confirms it.
  - Look at the frames of every inventory station row and at the bank tops: Sonoma's T8 and 9a huts stood behind the
    wall and on the skyline (owner notes 47, 49, 50, 53).
  - Every corner has a station. Scan each corner's inside and outside on the captures (the blob, its long shadow when
    raised) and its frames (the roof on the skyline), and write a ledger row per corner: found, with the capture and
    frame, or not found, with the captures examined. The eye-level inventory alone logged 3 of Sonoma's 6 stations,
    and the re-derivation of 20 Oct 2026 placed 1.
  - A hut is an open-front hut with a coloured band (`color`) on a deck on legs, `h` being the deck top from the
    footage, so it reads from the track (note 40).
- **Tyre stacks and blocks.** Free-standing stacks and striped or plain blocks go where the onboard shows them. The
  onboard outranks a capture taken at another event (Sonoma's T11 apex blocks).
- **Masts.** Isolated lidar spikes (DSM - DEM > 15 m) confirmed by a base and a long shadow on a capture window. Masts
  seen in the onboard but resolvable on no capture are dispositioned (3.13), not guessed. Small poles are no lidar
  spikes: 3-5 m light poles along a fence line (Sonoma's nine at the foot of the T2 terraces, onboard 0:14-0:16) are
  placed from the onboard along the measured fence line at the spacing the frames show, and listed in the furniture
  ledger (13 of the accepted 41 masts were missing from the re-derivation, nine of them these).
- **Cones.** Colour, size and spacing from the footage, on measured lines (3.5). Single marker cones count too (Sonoma
  9a). Tall pylons (delineator posts, ~1 m, white bands) are `style='delineator'`, not cones (Sonoma's
  T7 fork, owner note 57: round 5 read them as a tyre line); a line that closes a road stands across its mouth.

**3.9 Boards and signs** (`wall_boards`, structure `boards`, `bridge_banners`, `ground_signs`).
- **No rule boards.** Brake boards (3-2-1 at 150/100/50 m before the braking corners), turn boards (75 m before each
  turn) and the flag stand (on the pit wall 8 m before the S/F bridge) are Laguna's rules. Place them only where the
  footage shows them.
- **Boards carry names.**
  - `wall_boards[].names` and structure `boards.names` hold the sponsor names the recent footage shows on that run as
    (text, background, text colour) tuples, typed in the observed colours; `bridge_banners` takes 'NAME|#bg|#fg'
    strings. A string in `names` renders one letter per panel (the re-derivation of 20 Oct 2026 lost a round to it).
    This is text only, no logo artwork.
  - Each run starts and ends at the footage's stations (Sonoma F4: the wall before s 2105 is plain).
  - Every wall the onboard shows boards on gets its run: a long wall that repeats one name set (Sonoma's drag-strip
    infield wall, onboard 2:08-2:18, carries LAS VEGAS / O'REILLY / EchoPark / zMAX / TOYOTA / SONOMA RACEWAY four
    times over 120 m) and the far face of a wall the pit-lane video sees from the other side (the GENERAL TIRE face of
    the pit-in board wall). The re-derivation placed 84 of the accepted 125 boards; the 20 it missed on that one wall
    were all in one frame range it had logged.
  - The manifest records, per run, the names, the onboard time and the colours.
  - Panels with no `base` stand on their wall and count toward its height in the coverage gate; panels on posts carry
    `base`.
- **Ground signs.** Scan the WHOLE lap for painted ground logos: capture windows every ~120 m, both sides, 0.25 m/px or
  better. Each legible one goes in `ground_signs`: typed text on a decal draped on the ground, sized and headed from the
  capture, in its colours. List illegible ones and logo artwork, and do not place them (Sonoma's O'Reilly at T7a, owner
  note 46).

**3.10 Bridges.** Take OSM `bridge=yes` ways crossing the circuit.
- The deck height comes from class-17 points, or the surface 3.5 to 12 m above the track (default 6 m).
- The span is the part within 25 m of the edge.
- `bridge_stairs` gives each span end an abutment from the DEM to the deck and a stair flight along the way: no deck
  hangs in the air (owner note 29).
- Banners go on only with text legible in the footage (3.9).

**3.11 Edge lines and paint.** White edge lines 0.12 m wide sit 0.15 m inside the edges, broken through kerbs and where
the pit lane touches. They are drawn by rule, since NAIP cannot see them; the captures show white edge lines everywhere
except through kerbs. `edge_line_cut` removes them where the edge paint is something else. `paint_lines_declared` holds
measured lines with their colour.

**3.12 Every gate is REQUIRED.** `build_track.py --stage scenery` runs them and fails the stage. Each has tests.

| gate | what fails | where |
|---|---|---|
| edge (with walls and bridges) | the stage-1 edge checks (1.9) on the built scenery | `edge_gate.py` |
| world continuity | the edge polyline's third difference over 2 cm. Also run the in-page scan after each build (3.2): a scenery triangle off the drive surface by > 2 cm; steps or slope changes > 8 %/m from 0.5 m inside to 18 m outside the edges | `build_track.py`; `scan_surfaces.js` |
| profile | a step over 10 cm in any profile column | `build_track.py` |
| barrier gaps | any barrier point under 0.5 m from the edge (pit wall 0.3 m) | `build_track.py` |
| containment | from every 2 m station, both sides, rays on the normal and ±35° up to 120 m: another paved polygon (pit lane, closed road) reached before a barrier or a cone line, unless `gates.allowed` lists it | `gates/sceneryGates.ts` |
| pit connectivity with lane paths | the path pit box -> pit exit -> track and track -> pit entry -> pit box (`gates.pit_box_latlon`) crosses a barrier or leaves the paving. The lane is also driven on two paths 1.5 m from its edges: a barrier or cone line within 1.0 m of a path or inside the lane polygon, or a lane under 3 m between two closed edges, fails | `sceneryGates.ts` |
| signs | boards, banners, flag stands and posts on the track or inside a pit-lane, closed-road or `gates.paddock` polygon; brake and turn boards more than 15 m from an edge | `sceneryGates.ts` |
| wall ends | a rigid run's upstream end within 8 m of an edge not joined / lapped / cushioned / tapered / leaving at > 60° (3.4) | `sceneryGates.ts` |
| tyre facings | a tyre run parallel 0.8-2.5 m off a rigid wall for 2 m or more (joints within 1.5 m of a wall end and runs angling in are not counted) | `sceneryGates.ts` |
| coverage | every inventory row of a physical kind needs an object of that kind on that side within ±15 m of its station, else MISSING. MISSING walls, fences, kerbs, tyre walls and bridges always fail; a MISSING row of any other kind fails unless the manifest carries a valid disposition (3.13). Every object of those kinds needs an inventory row or a capture source within ±15 m, else UNSUPPORTED. HEIGHT mismatches (> max(0.3 m, 25 %), wall-mounted boards counting) are listed. No inventory = fail | `gates/coverageGate.ts`, `run_coverage.ts` |
| pit lane | every pit-lane wall row of the inventory declared in `pit_lane.walls` on that side and standing as a barrier on that side of the lane within ±15 m | `coverageGate.ts` |
| kerb traversal | on every registered track, every raised strip at line speed, on the line and 1 m either side: no roll past 15° and no rollover; no wheel lifted by a strip (`it.fails` for Sonoma pending the owner's suspension call) | `src/physics/__tests__/kerbgate.test.ts` (vitest) |

Laguna's logger build (report only, 20 Oct 2026): containment fails on its pit lane (s 375-573 left, the pit-out lane
after T2, and two rays at T11), and it has no inventory. Its package is the reference for geometry, not for these gates.

**3.13 The coverage work list and dispositions.** The MISSING list of the coverage gate is the work list of the scenery
round. Each row is fixed one of three ways:
- by an object measured on the evidence;
- by a logged correction of the inventory row (`attrs.correction`, 0.10);
- for kinds other than wall, fence, kerb, tyre wall and bridge, by a **disposition line** in the manifest.

The line format is:

```
| kind | side | s (m) | what | source | <disposition> |
```

The disposition is one of:
- `placed: <object name> (...)`: the object stands in the package beyond the ±15 m match (a stand seen across the
  infield, a mast seen ahead). The name must match an object of that kind, by its label in scenery.json: a declared
  wall's `name`, a structure's `name` (a terrace built as a structure carries the structure's name, not the terrace
  key's).
- `assigned: <round>`: kind building only.
- `rejected: <evidence>`: a person, a temporary item, or old Street View the recent footage contradicts. Name the capture,
  the onboard time or frame, the panorama or the lidar.
- `not resolvable: <captures named, why>`: the place was examined and the object cannot be placed from the evidence.

`tools/track/manifest.py` parses the lines and `coverageGate.dispositionProblem` validates them. An invalid line, or a
MISSING row with none, fails the gate. Sonoma's accepted package carries 31 (15 placed, 15 not resolvable, 1 rejected).
Write the generated tables with `manifest_tables.ts` after each round.

## Stage 4: drive proxy, judge round, owner's lap (5 steps)

**4.1 Camera walk with the owner's poses** (`npx tsx tools/track/compare/camera_walk.ts --track <id>`; dev server on
5179; its own headless Chrome with a throwaway profile; the `__sim` hooks). It shoots:
- the hood camera every 50 m round the lap;
- turned ±70° toward the side of every inventory row;
- **looking back every 100 m** (wall ends, joins and facings show from the other direction);
- **inside the pit lane end to end** every 25 m, facing the way the cars drive it;
- **from every paved runoff and closed road the track reaches, looking back at the track** (the containment rays' runs,
  one pose per 150 m, 4 m inside the polygon, and each paved runoff zone).

These are the places the owner went on his laps. Every pose is recorded in `walk.json`, and `--replay <walk.json>`
reshoots the same poses on another package. Sonoma: 344 stills (fwd 82, rows 173, back 41, pit 36, runoff 12).

**4.2 Compare sheets.** Capture the onboard frame at the mapped time of every 50 m step (`inventory.py --times 50`;
2x2 grids in your own Chrome tab, cropped into `compare_sheets/onboard/` with `onboard.json`). Then run
`make_compare_sheets.py`: 6 pairs a sheet, reference left and sim right, captioned with the station, the corner and the
inventory rows there.
- Forward and side sheets pair each still with the onboard.
- Back sheets pair it with the onboard 100 m earlier looking at the same stretch.
- Pit sheets pair it with the nearest pit-lane video frame.
- Runoff sheets pair it with the onboard at that station.

The output is `compare_sheets/index.md` (Sonoma: 58 sheets), local only. These sheets replace stills at builder-chosen
spots as the review. Hood stills at spots the builder chose show what was placed, never what is missing; the inventory
and the sheets do.

**4.3 The orchestrator's judge round with the checklist.**
- The orchestrator reviews EVERY sheet.
- The judge lists every difference per sheet as inventory-style rows with the prompt of `tools/track/compare/JUDGE.md`.
  The judge is GPT 6 Astra via codex when credits exist, else the orchestrator, who says so. The judge is never the
  agent that built the package: a builder judging its own sheets passes what it placed (the re-derivation of 20 Oct
  2026 judged itself and missed the T9 bank barrier, the T2 light poles and five marshal huts).
- The judge answers the JUDGE.md checklist for every sheet: C1-C21, from the owner's 54 notes (wall ends, joins,
  facings, cones, pit blend, kerbs per the satellite, stand extents, hut visibility, board extents, logos, movable
  barriers, tone seams, ...).
- The table goes in `compare/<id>/judge_r<n>.md`. True rows become inventory rows and scenery work; false rows are listed
  with why.
- The judge's contradictions on tone are settled by the recent footage, never by re-asking.

**4.4 Structures and surveyed spots.** Shoot hood or pose stills of every surveyed spot and every structure with
`compare/pose_walk.ts`, in the round's folder with a README (station, matching panorama id / onboard time). The kit's
reference stills (`tools/track/kit/README.md`) are the look each object should have.

**4.5 The owner's lap.** Only after the Acceptance section below.
- Publish a preview (`vercel deploy --yes` with `--build-env GIT_SHA=...`), never `--prod`.
- The owner's findings go in `compare/<id>/owner_drive_r<n>/README.md`, one numbered note each.
- Each finding becomes a work item, and its lesson becomes an edit to the step of this skill it belongs to and, where it
  can be checked, a gate or a checklist line.

**Earlier compare tools (still valid where the footage exists):**
- **Team footage first.**
  - `find_frames.py` maps logger GPS to video time (camera epochs from `sync.py`, logger offsets from `sync.json`) and
    to track s.
  - `grab.py` extracts windscreen crops at each corner's approach, apex and exit from clean, sunny laps.
  - `make_sheets.py` builds `<corner>.jpg` with the onboard frame left and the sim's driver-camera render right, at the
    same s and heading.
  - Findings go to `findings.md`.
- **Series onboard and satellite.**
  - `make_youtube_sheets.py` captures a recent series onboard from Chrome at the same places.
  - `make_satellite_sheets.py` lays the sim's top-down against the z20 captures for the whole lap, not only the
    corners.
  - `render_post.sh` captures the sim with the post stack on.
  - `make_judge_images.py` feeds the whole-lap top-down to the judge.
- **Budget.** Three to four rounds. Items the builder cannot express go on a list for a builder change.

## Stage 5: calibration, AI, gate

- `npx tsx tools/calibrate/drive.ts --track <dir> --alat 1.2 --learn 25 --bank --no-files` runs the autopilot on the
  ghost line against the ghost laps. Straights, braking and corner minimums should be within a few percent of the
  fastest real lap (Laguna ended at 1:59.24 vs 1:59.32). A corner 10 % or more slow with the car matching elsewhere is
  a geometry problem, not a car problem.
- `npx tsx tools/race/calibrate_field.ts --dry --only 619` gives the AI Probe solo lap. The per-stint field pace
  (`pace.json`) is per track and must be rebuilt from that circuit's results.
- Gate before any merge:
  - `npm run build` and the full `npx vitest run`;
  - `npx tsx tools/race/selfplay.ts` inside the band (Laguna: line rms 0.25 to 0.29 m, clearly-faster passes 72 to
    77 %, stuck median ~10.5 s, AI-AI contacts 0.012 to 0.038 per car-lap, recoveries 7 to 10);
  - a manual race start on a preview at 60 fps with no console errors.

  Fix a test only where its expectation was tied to the old geometry. Never loosen a behavioural check.

**What an edge rebuild does to the AI (Laguna, 18 Oct 2026).** The race AI and the field pace are fitted to the
geometry, so after any edge change expect the gate to fail and plan one AI session:
- **Field pace fit:** one scale per stint, grip first, then power. Cap the fitted lateral tyre grip at 1.20 g
  (`MU_LAT_MAX` in `src/physics/ai/field.ts`); above it, pace comes from power. Uncapped, the fit reached 1.48 g for
  the quickest cars on 200TW tyres and they rolled over at T2. The field median is about 0.72 g.
- **AI driver deficit:** scale 1 must mean the real lap. The deficit on the painted road was the speed profile ignoring
  banking and crests. The fix: 85 % banking credit (100 % ran cars wide at Rainey), a crest load term, margins 0.97
  lateral / 0.85 braking, and the grip limiter only above 1.5× the banked grip.
- **Lane model:** a narrower road has fewer lanes. Passes fall (Laguna 72–77 % → 69 %) and contacts rise until the
  corridor beside a car alongside (0.70 m), the merge-back look-ahead (60 m) and a no-passing zone through the
  Corkscrew are set. Re-base the self-play band to the new geometry with a dated note; never loosen a behavioural check.
- **Player-car grip is decided on evidence, not on an autopilot.**
  - Compute the tyre share the real laps imply on the line per corner (banking included, and once with the line
    allowed onto the kerbs).
  - Prove the calibration autopilot has saturated, and only then sweep mu0.
  - At Laguna the autopilot needed an unphysical 1.83 g peak to match the real lap, while the geometry asked
    1.18–1.26 g only where paved aprons let real drivers run wide, so the car was left alone.
- **Narrowing an exit moves the self-play band.** Laguna's T11 exit came in 2.7 m on the right (edge to the white line
  instead of the green runoff strip's outer limit). AI-AI contacts went from 0.02-0.04 to 0.06-0.08 per car-lap on
  three seeds, with the alone-line rms improving (0.40 -> 0.26 m). Re-run self-play on at least three seeds after any
  edge change, and treat a band miss as AI lane-model work, never as a reason to widen the track.

## Stage 6: app wiring (done once, 19 Oct 2026)

The app, the scoreboard and the tools read one registry, `TRACKS` in `src/scoreboard/config.ts` (dir, name, short,
`length_m`, pace file) with `DEFAULT_TRACK`.
- A page picks its track from `?track=<id>` (`src/app/track-choice.ts`). The Start menu shows a Track choice once two
  tracks are registered; a pick reloads with the new `?track=`.
- The rolling start is 230 m before the track's last directed corner (`lastCorner` in `src/scoreboard/sim.ts`).
- Boards are keyed `track/car`.
- The race tools take `--track <id>` (`tools/race/load.ts`: selfplay, sim_race, calibrate_field, pace).

A new track needs:
- its `TRACKS` entry (`length_m` = track.json's);
- `public/cars/field/<id>/pace.json` (pace.ts with that circuit's results, then calibrate_field.ts --track <id>);
- a `PHYSICS_VERSION` bump;
- its tests' fixtures, if any.

## Acceptance (the build reaches the owner only when ALL of these hold)

1. Stage 1 is accepted: the geometry gates pass, the lap length is within 1 %, and the whole-lap hood sheet has been
   reviewed (1.10).
2. **Every gate of 3.12 passes** on the package to be published: edge, world continuity, profile, barrier gaps,
   containment, pit connectivity with the lane paths, signs, wall ends, tyre facings, coverage, pit lane, kerb
   traversal.
3. **The coverage gate has no MISSING rows of ANY kind without a written disposition** (3.13), no invalid disposition,
   and no UNSUPPORTED object. The HEIGHT mismatches are fixed or explained in the manifest.
4. **The orchestrator has judged every compare sheet** of the current package (forward, side, back, pit, runoff), with
   the JUDGE.md checklist answered per sheet and every FINDING fixed or dispositioned in the manifest. The judge table is
   in `compare/<id>/judge_r<n>.md`.
5. The manifest is current: object and row tables generated, every scan listed with its captures, movable barriers
   flagged.
6. Laguna's and every other published package are byte-identical through the pipeline (no builder change leaks), and
   `npm run build` plus the full `npx vitest run` pass.
7. **The step ledger is complete.** The manifest carries a table of every numbered step of this skill (0.1 to 4.5)
   with its record (the file, table or commit that shows it was done) or `n/a: <why>`. The orchestrator reads the
   ledger before the comparison or the owner's lap; a step with no record was not done. The Sonoma re-derivation of
   20 Oct 2026 skipped the 3.9 ground-logo scan, said so, and had all 8 accepted ground signs missing.
8. **The scan ledgers are complete.** The barrier scan (3.4), the station and furniture scan (3.8) and the logo scan
   (3.9) each list EVERY clean capture of the lap (`satellite_clean/tiles.json`), both sides, with what was examined
   and what was placed or not. A capture absent from a ledger was not scanned. Scale: Sonoma's accepted package holds
   84 barrier runs (38 walls, 24 tyre walls, 22 fences), 6 marshal stations, 41 masts and 8 ground signs from 80
   captures; a circuit of that size with half those counts has not been scanned, whatever the coverage gate says (the
   eye-level inventory alone matched 27 barrier runs and 1 station in the re-derivation, and the gate passed).

The target is fewer than 5 owner findings on the first lap. When the owner finds more, each finding's lesson goes into
this skill (step, gate or checklist line) before the next circuit. `tools/track/compare/REDERIVE.md` is the test of that
claim: a fresh agent re-derives Sonoma from a clean config with only this skill, and `compare_packages.py` measures the
result against the accepted package. First run, 20 Oct 2026 (`compare/sonoma/rederive_2026-10-20.md`): 261 of 375
objects matched, 114 missing, every stage-3 gate passing, the misses in the 3.4, 3.8 and 3.9 scans the agent did not
run to the end; items 7 and 8 above and the ledger lines in those steps come from it.

## Dead ends not to repeat

- Station-by-station traces and stretch patches with blends (`fix_edges_paint.py`, `fix_rahal_left.py`,
  `fix_t11_exit_right.py`, `fix_edge_waves.py`, 18 Oct) made 20-80 m waves the hood camera sees. Fit, do not trace.
  - A fix with long blends (60 stations) applies its full move only in the middle and leaves the old swell at both
    ends.
  - On the Rahal straight, a retrace locked onto a repave seam 1.8 m inside the white line.
- A spline fit whose 'keep' zone holds a step in its prior: the spline rings ahead of it (Laguna T11 apex left fell to
  a 1.7 m half-width in the dry run). Interpolate the prior across such a junction (`prior.interp`) or declare it.
- A spline through the OSM nodes as the centreline (v1): kinks at way junctions, corner radii 20 to 70 % too tight,
  ghost speeds implying 1.5 to 2.2 g. Recentring along its own normals kept the kinks.
- NAIP asphalt-extent edges with symmetric half-widths clamped 4.5 to 8.5 m: 1 to 4 m too wide, 3 to 4 s a lap.
- z19 screenshots for edge tracing; only z20 resolves the painted line.
- The first lidar correction (3 to 5-return medians, zero fill, 1 m smoothing) and the 0.15 m edge snap: 1 to 2 cm
  noise everywhere, felt as dips at apexes.
- Flat DEM fits for runoff zones.
- Per-channel black points in the ortho grade.
- The clipped racing-line blend.
- Rockyweb LAZ downloads.
- Tall, steep sausage kerbs.
- Lidar as an edge source where the asphalt meets dirt with no painted line (Buttonwillow, 20 Oct 2026,
  `tools/track/lidar_edge.py`): even with the points of +-10 m along the track stacked per station, the 2021 survey
  gives 14-65 ground points per 0.1 m cross bin, the intensity is an even ramp over 4 m with no step, and the slope
  break sits 0.7-0.9 m outside the capture edge with no stable sign. An outside-in capture detector is worse than the
  inside-out one (tyre tracks and vegetation beyond the edge). The transition itself is 2-4 m wide on both sources, so
  no detector reaches 90 % of readings within 0.25 m; what to measure there is the owner's decision (round 2 of the
  Buttonwillow manifest).
- Landmark rounds before the geometry is right.
- Parallel agent swarms.
- Raising a render exposure to fix a washed-out ortho.
- Scenery by another circuit's rules (Sonoma round 2: Laguna's radius kerbs, green strips, brake boards, rule pit wall).
- Hood stills at spots the builder chose as the review (Sonoma rounds 3-4): they show what was placed, never what is
  missing.
- Cone lines and blend lines at an offset from the fitted edge (Sonoma round 6: the pit-in cones converged into the wall,
  and the pit-out cones stood off the paint). Measure the line.
- Two wall runs measured on different captures and left unjoined (Sonoma T5: a 2.6 m step toward the track).
- OSM outlines for hillside stands: rows buried and floating.
