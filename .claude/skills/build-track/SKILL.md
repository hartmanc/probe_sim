---
name: build-track
description: Build a new circuit package for the Probe sim (track.json, heightfield, ortho, ghosts, scenery, onboard compare pass with a GPT judge, calibration, AI retune, app wiring) with tools/track/build_track.py and a per-track config, from public satellite and lidar data, OpenStreetMap, the team's logger laps (optional) and onboard video, the way Laguna Seca was built on 17 and 18 Oct 2026, without the dead ends. Use for Sonoma, Buttonwillow, Road Atlanta, Mid-Ohio.
---

# Build a circuit for the Probe sim

Usage: `/build-track <track_id> "<Circuit name>"`, for example `/build-track sonoma "Sonoma Raceway"`.
Laguna Seca (`public/tracks/laguna_seca/`, `tools/track/tracks/laguna_seca/config.py`) is the reference implementation.
Read, in this order, before starting: `CONTRACTS.md` §1 (frames) and §2, §2b (formats), `tools/track/README.md`
(the pipeline, sources, method, acceptance numbers), `tools/track/trackcfg.py` (the config keys), Laguna's config,
`tools/track/out/laguna_dryrun/README.md` (what the pipeline reproduces and what it does not), then this file.

**The work is: write `tools/track/tracks/<id>/config.py`, run `build_track.py` stage by stage, read each report, and
put every fix into the config (a feature, a shape, a declared straight, a scenery entry), never into the package.**
Every stage below names its `build_track.py` stage, the config keys it reads, and Laguna's values as the worked
example; the scripts Laguna was built with step by step (17-18 Oct) are in git history (commit a21695f).

## How Laguna was built (the shape of the process)

1. **Contract first.** The lead wrote `CONTRACTS.md` before any builder ran: the local ENU frame, the byte-level
   formats of `track.json`, `heightfield.bin`, `ortho.jpg`, `ghosts.json`, `scenery.json`, the physics API and
   the app's scope. Builders may append a dated note under "Deviations" but never edit the contract otherwise.
2. **Builders in parallel against the contract, each in its own scope** (track data, physics, app, car model), then
   calibration and scenery, each a single Opus subagent with an explicit file scope, no git commits, a scratch
   directory, and a report cap. Each build script prints a validation report and exits 1 without writing
   outputs when a check fails.
3. **Validate the geometry by driving it, not by looking at it.** The autopilot (`tools/calibrate/drive.ts`) on
   the ghost racing line, compared corner by corner with the real ghost laps, is what exposed the v1 centreline
   (11 to 21 % slow at T5, T6, the Corkscrew and T11 because the radii were 20 to 70 % too tight). The IMU's
   lateral acceleration gives ground-truth curvature, κ = alat / v², to check any centreline against.
4. **Then compare with footage**, first the team's own onboard video, later the current-season series onboard
   and z20 satellite captures with a GPT judge, and fix what the sheets show.
5. **Only then** the look pass, the kerbs, cones, race mode and the rest.

## Working rules

- **One Opus subagent per stage, in sequence.** No swarms. Hand back numbers, not images. If a stage cannot be
  done from the data (lidar missing, fit impossible, line inconsistent with the paint), stop and report what it
  would take; never hand-edit heights or edges.
- **Source precedence on any conflict:** recent onboard video (team GoPro, current-season series onboard) beats
  Google satellite beats the NAIP ortho beats OSM beats the lidar survey year. Check the repave and runoff history
  of the circuit before trusting the survey (Laguna: 2017 lidar, 2023 full repave, 2025 paved runoff).
- **Reference material is reference only.** Race photos, video frames and satellite captures are never cropped
  into textures. Textures come from CC/PD sources with credits. No painted text unless legible in a reference.
- **Downloads are untrusted:** own directories under `tools/track/cache/`, never executed, readers run with
  `python -I` inside the `uv run` lines below. The system python has no numpy; always use
  `uv run --python 3.12 --with numpy,scipy,rasterio,pyproj,shapely,pillow,requests,pandas,matplotlib python -I <script>`
  (add `laspy[lazrs]` for the lidar point cloud).
- **Browser:** load the Chrome tools in one ToolSearch call, `tabs_context` first, own tabs only, never the owner's
  tab, close them when done. On the sim page set `navigator.getGamepads = () => []` after every load (a controller
  with a resting trigger is plugged in), place the car with `window.__sim.vehicle.reset([x, y, z], heading)` from
  `track.json`, and `window.__sim.setCamera('driver')` for driver's-eye captures.
- **Git:** `tools/track` scripts, configs and markdown records are tracked; its data (`cache`, `out`, `previews`, the
  imagery under `compare/`, every image, pickle, npy/npz, bin) is ignored, never committed. `tools/cars`, `tools/car`,
  `tools/audio` stay excluded. The package under `public/tracks/<id>/` is committed. Previews only
  (`vercel deploy --yes`), never `--prod` without the owner's approval. A new or changed track bumps `PHYSICS_VERSION`
  and opens fresh boards.
- **Never read `.env` files or print environment values.**

## The pipeline in one page

```sh
W='numpy,scipy,rasterio,pyproj,shapely,pillow,requests,pandas,matplotlib,laspy[lazrs]'
B="uv run --python 3.12 --with $W python -I tools/track/build_track.py --track <id>"
$B --stage geometry      # stage 1: track.json, heightfield.bin, ortho.jpg in tools/track/out/<id>/ (+ work/)
$B --stage ghosts        # stage 2: ghosts.json (no logger: racing line only)
$B --stage scenery       # stage 3: scenery.json, far_*; post steps; edge and barrier gates
$B --publish             # all stages, then copy to public/tracks/<id>/ (refuses to replace a package without --overwrite-package)
uv run --python 3.12 --with numpy,scipy python -I tools/track/compare_package.py --cand tools/track/out/<id> --ref <dir> [--by-corner]
npx tsx tools/calibrate/drive.ts --track tools/track/out/<id> --alat 1.2 --learn 25 --bank --no-files [--ref-ghosts <ghosts.json>]
```

Each stage prints its validation report and exits 1 without writing when a check fails; `--write-on-fail` writes
anyway for diagnosis (never publish such a package). Config keys by stage (all in `trackcfg.py`, Laguna's values in
its config): stage 0 `origin`, `osm_bbox`, `loop_ways`, `pit_lane_way`, `dem_tiles`, `lidar_ept`, `dem13`,
`logger_dir`, `start_finish_latlon`, `corners`, `named_straights`; stage 1 `centre`, `centre_captures`,
`repave_fixes`, `captures`, `prior`, `shapes`, `spline`, `features`, `straights`, `gate`, `stations_ref`; stage 2
`ghosts`; stage 3 `scenery`; app `app`. `reproduce` exists only to rebuild Laguna's accepted package byte for byte
where its build had artefacts; a new circuit never has one.

## Stage 0: inputs

**The loop is the Lemons layout.** The configuration Lemons runs at each circuit is the layout picture on that track's
schedule page on the Lemons website (24hoursoflemons.com, the event's page). Pin the loop from it before anything else,
confirm it against a recent series onboard (the full lap, every junction), then name the OSM `highway=raceway` ways that
form it, in driving order from the start/finish, in the config (`loop_ways`; Laguna: the 8 circuit ways, "Pit Lane"
excluded). Several circuits have alternative loops and bypasses mapped as raceway ways; the stitcher takes only the
listed ways and fails loudly if they do not close. Also write down the start/finish line (`start_finish_latlon`, from
the painted line on the clean captures) and one lat/lon anchor per corner (`corners`).

| Input | Where | Needed for |
|---|---|---|
| Circuit centre `LAT0, LON0` and OSM bbox | OSM | local ENU frame (CONTRACTS §1), every script |
| OSM `highway=raceway` ways (the circuit is several named ways plus "Pit Lane"), `barrier=wall`/`fence`, buildings, `bridge=yes` ways | `curl -A "probe-sim/0.1" "https://api.openstreetmap.org/api/0.6/map?bbox=W,S,E,N"` cached as XML (Overpass was overloaded; the API map call worked) | loop, pit lane, scenery |
| USGS 3DEP 1 m DEM tiles covering the box | TNM staged products `prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/<project>/TIFF/`, read as windows over HTTP | profile, heightfield, banking |
| Entwine point tiles of the same survey | `usgs-lidar-public` bucket on AWS (not the rockyweb LAZ tiles: 40 KB/s) | lidar ground correction, trees, building and bridge heights |
| 1/3 arc-second DEM tile | TNM `Elevation/13/TIFF/current/` | far terrain |
| NAIP via the image service, 0.6 m/px near, 5 m/px far | `imagery.nationalmap.gov/arcgis/rest/services/USGSNAIPImagery/ImageServer/exportImage` | ortho, far ortho, scenery blobs |
| Google satellite captures at z20 (0.14 m/px), overlapping, whole lap, with centre lat/lon and scale in `tiles.json` | Chrome screenshots | painted edges (z19 at 0.34 m/px cannot trace a 12 cm line) |
| Team logger laps: `centreline.npy` (ENU, 1 m, index 0 at the transponder line, driving order), `traces_warped.pkl` (t, v, thr, rpm, alat), `sections.pkl`, `official.pkl` | `~/projects/starlink-go-pro/laps` style analysis, read only | centreline shape, start/finish, direction, ghosts, racing line, κ ground truth |
| Onboard video: the team's GoPro (with `sync.py` epochs and logger GPS for video time → s) and a recent series onboard on YouTube | team footage, YouTube | compare pass, repaves, runoff, landmarks |

**Street View survey (owner, 20 Oct 2026; every circuit).** In your own Chrome tab, open Google Maps Street View / user
photo spheres at every corner and major feature of the loop (both sides where available; the circuit's own spheres, and
road-side coverage of the access roads for stands and buildings). Record in `tools/track/compare/<id>/streetview.md`,
per place, the panorama id and heading, the capture date, walls (side, material), catch fencing, tyre walls,
corner-worker stands, kerb colour / width / height, runoff (paved / gravel / dirt), cones, bridges and gantries,
buildings and towers, grandstands (size, construction). Screenshots are reference only, never textures, never committed;
the record is the deliverable. Check its date against the recent onboard (source precedence). It feeds the declared
walls, kerbs and paved zones of stage 3 and the scenery task.

Without logger laps for the circuit (`logger_dir=None`, or `--no-logger`): the centreline shape comes from the painted
road midpoint alone (OSM loop -> NAIP midpoint -> painted midpoint -> spline-fitted edges -> refit to their midpoint,
soft move and stiff smoothing, `nologger_fit_a` 1e1 / `nologger_fit_b` 1e5, so the OSM nodes' kinks are not kept),
there are no ghosts (`ghosts.json` has the racing line and `laps: []`; the app, the scoreboard and the AI load it, the AI
corner finder runs on a curvature speed profile), the racing line is the pure minimum-curvature line, and the autopilot
lap replaces the implied-g checks. **Measured on Laguna (19 Oct 2026, same config, logger removed;
tools/track/out/laguna_dryrun/README.md):** centre 1.15 m rms from the logger-built centre (worst 5.3 m, at the
Corkscrew and T11; 0.2-0.7 m rms at T2-T5, T9, T10; 3 m at T1 where the pit-out merge counts as road), racing line
1.55 m rms (worst 5.0 m); every corner tighter on the line by 1-27 % (T6 67 vs 81 m, Corkscrew 23 vs 31 m, T11 19 vs
23 m); lap 3597.7 m vs 3588.0 m; autopilot 2:03.19 against 2:01.84 for the logger-built package with the same command
and 1:59.32 for the real best lap (T11 exit 41 vs 49 km/h). Expect a no-logger circuit to drive about 1 % slow before
the hand checks, most of it at its tightest corners; check those against the onboard first.

## Stage 1: centreline, edges, profile (`build_track.py --stage geometry`)

Output: `tools/track/out/<id>/{track.json, heightfield.bin, ortho.jpg}`, `work/preview.png`, `work/geometry_report.json`.
Modules: `geo.py` (frames, OSM, DEM, NAIP), `centre.py` (first centre, NAIP edges, profile, corners), `paint.py`,
`recentre.py`, `edges_spline.py`, `straights.py`, `edge_gate.py`. The steps below are the method; the config holds the
numbers.

1. **Loop.** Stitch the OSM raceway ways by shared end nodes into one loop, turn it to the driving direction, roll
   it so station 0 is the logger's start/finish, 1 m stations. The pit lane is a separate way. Check OSM against
   the GPS centreline (Laguna: median 3.2 m, p95 6.2 m) and station 0 against `centreline.npy[0]` (3.6 m).
2. **Frame registration before anything else.** Phase-correlate every z20 Google tile against the NAIP
   `ortho.jpg` (Laguna: Google minus NAIP = −0.3 m east, 0.0 m north, all 42 tiles under 1 m), then fit one rigid
   transform of the centreline to the painted road midpoint over all measured stations and compare the residual
   before and after (Laguna: tx −0.09 m, ty +0.18 m, 0.02°, rms 2.12 m before and 2.13 m after, so no global
   shift was applied). If the residual drops, apply the one transform and re-sample the profile; if it does not,
   the error is in the centreline shape. At Laguna it was: the GPS-driven line cut every apex by 2.5 to 5.6 m
   (chord and smoothing on the logged line), so the painted midpoint sat outside the centre at every corner.
3. **Centreline shape from the driven line, not from OSM.** Use `centreline.npy` (its curvature matched the IMU's
   κ to r = 0.98) and move it toward the painted-road midpoint with the penalised least-squares fit of
   `centre.py` (config `centre.naip_fit_a/b` for the NAIP pass, `centre.paint_fit_a/b` for the paint refit): `FIT_A` (stiff second difference on the lateral move keeps the driven curvature) and
   `FIT_B` (third difference on the positions removes kinks), two passes with edges re-detected along the new
   normals. Plot κ from the IMU against the centre and the line (`kappa_check.png`).
   The stiff fit (`FIT_A` 1e6) is only right when the driven line already sits mid-road. Where the logged line
   cuts the apexes, fit toward the painted midpoint with the soft weighted fit (`FIT_A` 1e3, as the 18 Oct rebuild
   did; the run that built the accepted centre used 1e4 with `FIT_B` 1e2, `recentre.py`): Laguna moved the centre p50
   1.12 m, p90 3.15 m, max 5.34 m and the painted-midpoint residual fell from 1.93 to 0.36 m rms. The painted
   midpoint is measured by `paint.py` (config `centre_captures`, `centre_registration`). Keep the station count and resample uniformly: `spacing_m` = L / n (Laguna 3588.05 m /
   3560 = 1.007879; the projector and the AI line honour `spacing_m`). Old station k lands at new station u(k)
   (up to 11.6 m apart at Laguna): remap every s-ranged scenery item through u(k) so it keeps its world position,
   re-run the ghost build in full so t/v are re-projected by world position, and re-solve the racing line
   (stage 2) rather than carrying the old `offset_m`, which would drag the apexes outward with the centre.
   Acceptance (printed by the geometry stage): lap length within 1 % of the official figure (Laguna 3588 vs 3602;
   the old centre gave 3560), on the first centre within ±60 m of every corner the minimum radius within 15 % of
   the driven line's (limit 25 %; the paint refit then tightens the apexes the logged line cut, so the final radii
   are printed, not checked), largest lateral edge change between adjacent stations under 0.5 m.
4. **Edges from the painted lines, per side** (the paint-step edges of `recentre.py`: since 18 Oct evening only the
   prior of the spline fit below; the rest of this step is how the prior is made and what was learnt). At each station the left and right half-width
   is the first painted line, kerb or non-asphalt surface met going out along the normal on every z20 capture
   covering the station; median across captures, median over 9 stations, Gaussian 2 m, floors at the pit-lane
   joins, width cap 16 m, slope limit 0.25 m per station. Kerbs and painted lines count as road. Store left and
   right separately (median difference 0.8 m, up to 4.4 m at Laguna); the profile fractions scale each side.
   Discard every measurement within 25 stations of a bridge crossing (`--bridge-win`): the detector reads the
   bridge shadow's edge as a painted line and puts a 1 to 4 m kink under each bridge where the road is straight;
   interpolate across from the clean stations instead (config `centre.bridge_win`; the prior is also interpolated
   across ±35 stations, `prior.bridge_win`, was `fix_bridge_edges.py`). Then the notch-and-wave pass (`fix_edge_waves.py`,
   superseded by the spline fit, kept here for what it taught):
   runs under 25 stations that sit over 0.35 m from a 41-station median are detector notches (seams, board and
   wall shadows) and go back to the median; on straights and gentle bends (centre radius over 250 m anywhere
   within 30 m, so an S-bend's inflection does not count as straight) the half-widths get a 5 m Gaussian and a
   0.10 m per station slope cap, because a painted line is smooth and a hood camera shows every 0.5 m wave; tight
   corners keep their real swings. Keep the old edge where a pit-lane join or the pit-exit blend lane touches the
   track. The painted edge is the
   kerb's track-side line, so apex and exit kerbs sit outside the edge afterwards (`inside: false`) and the
   physics must still treat them as pavement with a continuous height. Laguna result: painted width median
   12.9 → 11.6 m (p5 8.7, p95 16.0); apex half-widths such as T6 3.0/8.9 → 4.1/4.8 m, T11 3.0/9.6 → 5.4/6.6 m,
   front straight 7.9/8.5 → 4.7/5.4 m. The AI Probe's solo lap went from 120.4 s on the wide track to 123.8 s on the
   painted road with the old driver, and to 120.2 s once the AI's speed profile credited banking and crests
   (real best lap 119.3 s): expect a lap-time step from an edge rebuild and look for it in the driver before the tyres.
5. **Profile and heightfield.** `z0_navd88` at the start/finish centre. Profile from the 1 m DEM smoothed
   σ = 0.7 m, then `lidar_correct` onto the ground returns (gaps filled along s, 7-station median, 4 m Gaussian)
   and `clean_profile` (edge points ≤ 4 cm off the line through the five inner points, every point ≤ 2 cm off the
   section quadratic, 5-station median and 1.5 m Gaussian along s). Heightfield: unsmoothed DEM, bilinear, 2 m
   grid over the box plus ~220 m, agreeing with the profile on the centreline to 5 mm. Banking from the lidar is
   real (12 to 15 % at Laguna's T5, Corkscrew, Rainey): cross-slope limit 16 %, every station over 12 % listed
   and checked near-planar. Ignore bridge decks classed as ground. Edge points on a berm or kerb face are replaced
   by the road plane extended to the edge.
6. **Repaves.** Where the footage or the owner's own laps contradict the survey (Laguna T6: 0.4 m sag in the 2017
   lidar, a crest since the 2023 repave), rebuild the centre height over the window from its vertical curvature
   (`REPAVE_FIXES`): crest or flat in the crest zone, gentle sag elsewhere (R ≥ 1500 m), heights and slopes matching
   at the window ends, the same change across the section so banking is kept, carried into the heightfield fading
   2 to 12 m beyond the edges. Only hollows the footage confirms; grade changes are not dips.
7. **Corners.** Signed-curvature peaks within ±45 m of the logger's corner anchors, each with `name`, `turn`, `s`,
   `radius_m`, `dir`; named straights halfway between their corners.
8. **Roughness check** (`previews/profile_roughness.png`): 1 m second differences implying a vertical radius under
   150 m are allowed only where the lidar shows a real crest or drop (the Corkscrew at R ≈ 45 to 80 m); single-
   station steps over 1.5 cm near zero; apex minimum 1 m radius 155 m or more.

### Why Laguna's first painted-edge rebuild looked wrong, and the rule that follows

The detector measured the white line one station at a time on the z20 tiles and the pipeline treated each
measurement as truth, cleaned only by a 9-station median, a 2 m Gaussian and a 0.25 m per station slope cap. Bridge,
wall and board shadows, repave seams and pale aprons produced 1 to 4 m jogs, 0.5 m waves and bulges that a hood
camera shows at once and that neither the numeric gate, the 14 corner frames, the top-down tiles nor a half-width
table revealed. The owner found them by driving. Rules for every circuit from now on:

1. **Edges are curves, not samples.** Fit each side as a smooth curve to the detections with a curvature-change
   penalty and a robust loss (the same operators as the centreline fit), so a bad station cannot make a bump. Mask
   bridges, walls, boards and gantries before measuring; detect the white line itself (brightness and 12 cm width),
   not the first non-asphalt pixel; where a wall runs parallel, fit the line as a constant offset from it
   (now a declared straight, config `straights`, fit `pitwall`); keep the real features (corner swings, apron widenings, pit-lane joins).
2. **Geometry gate before anything downstream, and the build fails on it** (`tools/track/edge_gate.py`): edge
   residual against a 41-station median under 10 cm rms on straights (Laguna lands at 0.09-0.10 m after the sweep;
   the 5 cm first written here was never reached, not even by the baseline, and the hood sheet shows nothing at
   that level), no slope over 0.10 m per station outside tight corners, wall offsets steady where a wall runs
   parallel, barrier gaps never under 0.5 m, width changing slowly except at kerbs and junctions, no step over
   10 cm in any profile column (Laguna 0.09 m at the Corkscrew).
3. **Driver's-eye sheet of the whole lap:** driver-camera render every 50-75 m (48-72 frames), reviewed by the
   judge and by the owner before the AI work starts. Corner frames catch landmarks; only this catches waves. Cheap
   way, done on 18 Oct in one tab on localhost:5173 (own tab, hot lap started, `navigator.getGamepads = () => []`):
   a page script fetches track.json, and for each station calls `__sim.vehicle.reset([x,y,z], heading, 0)`, waits
   260 ms, calls `__sim.renderer.render(__sim.world.scene, __sim.cams.camera)` and `drawImage`s the GL canvas into a
   3x2 tile of a 1440x725 canvas (preserveDrawingBuffer is off, so the render and the copy must share one task);
   the 6-frame sheets are shown as a fixed full-screen `<img>` and screenshotted one by one. 48 frames cost eight
   screenshots instead of 48.
4. **Derived data rebuilds automatically after any edge change** (one script): racing line and ghosts
   (`build_ghosts.py`), the on-pavement fixture (`record_onpave.ts`), field pace (`calibrate_field.ts`), then the
   gate. Otherwise "alone racing line rms" and the surface fixture go red and the AI gate is noise.
5. **Paved shoulders come from the footage in the same pass**, as `paved_zones` parts level with the road, wherever
   the onboard shows pavement to a wall or apron.
6. **Check every capture's registration against its neighbours before tracing.** A capture whose shift in
   `paint_regs.json` differs by more than 0.5 m from both neighbours is excluded (`sweep_paint.EXCLUDE_TILES`) or
   re-captured; Laguna's `z20_s3400` was 1.3 m off and alone produced the front-straight hump, a left-edge wave and a
   pit wall "inside" the track. Record the exclusion in `track.json` notes.
7. **Write the edge convention down and apply it at every station.** The edge is the painted line where there is no
   kerb and the flat kerb's outer limit where there is one (sausage strips then sit behind the kerb). Painted runoff
   strips (green verge, teal aprons) lie OUTSIDE the edge: a first-non-asphalt detector puts the edge at their outer
   limit (Laguna T11 exit, 3 m too wide, with the verge then painted a second time on the shoulder). Re-trace by
   stretch with a window and a feature (`fix_edges_paint.py`: line / kerb / both / chord), or the strip's inner limit
   (`fix_t11_exit_right.py`), and never chord a hairpin or the Corkscrew: its painted swing is real. Apexes with a kerb
   at the bottom of a V and dirt beyond (T6, T10, T11, T8) go to the kerb limit; check the AI corridor afterwards, a
   3.8 m move at T8 put a self-play car off at T8A.
8. **Barriers get a gate too.** Every barrier point's gap from the nearest edge at least 0.5 m, pit walls at a
   constant measured gap along a straight (Laguna 2.0 m left, 4.0 m right to the concrete). OSM polylines cut across
   the paint at wall noses (`fix_pitwall_nose.py`). Print it with `edge_gate.py`.
9. **Scripts are idempotent or say they are not.** A fit range that wraps past the lap end (3380..3575 on a
   3560-station loop) re-blends stations 0-15 on every run; a shoulder regeneration after a later edge change is
   `fix_front_straight.py --zone-only`. Every script's arguments go in `track.json` / `scenery.json` notes. (The
   pipeline rebuilds from raw inputs every time, so idempotence is built in; the config is the record.)
10. **Sweep kit that found the rest** (all under `tools/track/`): `sweep_paint.py` (paint check per station, anchored
   at the current edge), `compare/straight_strip.py --side` (edge-relative strips, the current edge is the middle
   row, so deviations read off directly), `edge_gate.py`, `compare/edges_overlay.py` with `OLD_REF` and the
   registration shifts applied, a hood-level contact sheet of every changed place. An inventory with station ranges
   and the tile evidence goes to the owner before anything is applied.
11. **Trace straights with two references and fit exits with a shape, not a trace.** On the Rahal straight the sweep's
   retrace locked onto a repave seam 1.8 m inside the white line; the deployed track's own edge was right there, and the
   per-station paint sweep (`sweep_paint.py`) was right at the T7 approach kerb. `fix_rahal_left.py` takes the deployed
   polyline up to a station and the sweep's kerb detections after it, 21-station median, Gaussian 6, and drops sweep
   readings that fall outside the current edge where the edge is known to be beyond the kerb (stray readings under a
   board). On a corner exit where kerb, green strip and white line overlap (T11), per-station traces came out wavy
   twice; `fix_edge_shape.py` replaces the half-width with a monotone cubic through measured knots (apex kerb, kerb
   limit, straight width at the wall gap), blend 2 when the end knots equal the current values. A fix with long blends
   (60 stations) applies its full move only in the middle and leaves the old swell at both ends: place blends where the
   move is already zero.
12. **Edge-relative scenery moves with the edge.** Kerb strips, verge paint and sausages are drawn from the edge, so a
   wavy edge shows up as a wavy kerb; a kerb strip's extent is measured, not inherited (`fix_kerb_strip.py`). Walls
   from OSM run past their real ends (`fix_pitwall_exit.py`: the hot-pit wall ends at the pit-out lane; the painted
   strip alone separates the lane from the track to T1).
13. **Gate rule for exits**: within the first 120 stations after the centre radius is back over 150 m, the road width
   (left + right half-width, independent of where the centre sits) must not overshoot its value at the window end by
   more than 1 m (`edge_gate.py`, "exit overshoot"). Advisory, not a build failure: it also fires on real features (the
   pit-out merge at T1, the pit rejoin after T2, the T7 approach where the kerb narrows the road by 2 m), so each line
   is checked on the capture. Half-width alone fires at every apex the centreline cuts.

### Edges are FITTED, never traced (owner, 18 Oct 2026 evening; supersedes the trace-and-patch rules above)

Per-station tracing, short smoothing and stretch patches with blends made 20-80 m waves of 0.3-1 m that the hood camera
sees end-on and the top-down sheets cannot (record: tools/track/compare/edge_sweep_2026-10-18/t2_waviness_review/ and
t2_spline_fit/). Do this instead:
1. **Clean captures.** Google Maps satellite at z20 in your own Chrome tab: Layers > More > untick Labels, hide every UI
   element by page CSS (opacity 0 on everything at the screen corners and top bar), park the cursor in a corner, pan by
   dragging (navigation turns the labels back on), read each centre from the URL, `register_clean.py`. Overlap so every
   station is seen at least twice.
2. **One common shift** for all Google captures (median against the ortho). Captures agree with each other to a pixel;
   per-capture registrations against a 0.6 m ortho are noise and put 0.3-0.6 m jogs at capture boundaries.
3. **`edges_spline.py`** (was `fit_edges_spline.py`; config `spline`: runs, knot 6, lam 30, huber 0.25, line_off 0.26,
   prior 0.03; `features`; `shapes`) per side: every painted-line inner side (+0.26 m) and kerb outer limit as candidates,
   penalised cubic B-spline (6-station knots, `--lam 30`), Huber 0.25 m, nearest-candidate association with a shrinking
   gate, current edge as a weak prior (0.03) only for gaps, anchored joins. Kerb zones from red in the imagery; an
   explicit FEATURES table for ambiguous places (config `features`: 'keep', 'asphalt_end', 'kerb'; Laguna: Andretti
   apex inside = asphalt end). Measured shapes (`shapes`, monotone cubic through station:half-width knots, was
   `fix_edge_shape.py`) and declared straights (`straights`: a RANSAC line on the painted line, or a constant gap
   inside the straight pit wall, was `fix_front_straight_lines.py`) go into the prior before the fit and are applied
   again after it. The prior itself can take the first build's NAIP edge over a stretch (`prior.first_edge`, Laguna's
   Rahal left) or be interpolated across a junction (`prior.interp`).
4. **Gate** on the printed local waviness (residual about a +-25-station quadratic, rolling 100 m) and kink per
   station, observation residuals (90 %+ within 0.25 m) and coverage, plus hood-cam frames; pit-lane and apron
   boundaries are moved onto the new edge by the script.

## Stage 2: ghosts and racing line (`build_track.py --stage ghosts`, i.e. `tools/ghosts/build_ghosts.py --config <id> --track-dir <dir>`)

Output: `ghosts.json`, `work/preview_ghosts.png`, `work/kappa_check.png`. Config `logger_*`, `ghosts` (margin,
kerb_margin, nudge, jerk_w, implied_g_turns, implied_g_exempt, kappa_drivers).

- Lap times scaled to the official timing; each driver's best clean lap; the optimal lap from `optimal.solve` over
  clean good-GPS laps, stitched section by section. Logger distance mapped onto track s by projecting
  `centreline.npy` onto the centre, smoothed and monotonic.
- Racing line: bounded least squares (active set) on curvature plus 3× curvature change, bounds a smoothed lower
  envelope of each side's edge less 1 m, then a second bounded solve pulling 30 % toward the measured good-GPS
  line (not a clipped blend: that kinked where the measured line lay outside the bounds).
- Implied-g table per corner, plain and tyre share after banking μ = (a − tan b)/(1 + a·tan b): tyre share ≤ 1.3
  at apexes, ≤ 1.35 anywhere, plain ≥ 0.9. Re-run only when station 0 or the length changes.

## Stage 3: scenery (`build_track.py --stage scenery`: `build_scenery.py`, then `scenery_post.py`)

Output: `scenery.json`, `far_heightfield.bin`, `far_ortho.jpg`, regraded `ortho.jpg`, `work/scenery_preview.png`. The
per-circuit constants are config `scenery`: `tyre_corners`, `paved_runoff`, `brake_board_corners`, `no_exit_kerb`,
`pit_wall` (fence, end, `at: first_edge`), `oak`, `gantry`, `banner_boards`, `bridge_banners`, `bridge_style`,
`hangars`, and the post steps that were scripts on 18 Oct: `shoulder_zones` (fix_front_straight.py), `aprons`
(add_paved_aprons.py), `pitwall_end` / `pitwall_setback` / `pitwall_straight` (fix_pitwall_*.py), `kerb_extents`
(fix_kerb_strip.py), `edge_line_runs` (fix_edge_line_run.py), `pit_exit_cones` (fix_pit_exit_cones.py). What the
footage rounds placed by hand at Laguna (kerb re-measurements, sausages, signs, extra oaks: compare/satellite/apply_round*.py)
has no config key yet: put such items in the config as new `scenery` entries with a builder change, not into scenery.json.
Every placement derives from `track.json` (kerb ranges, barrier runs, boards, the pit wall, the lidar box), so one
command regenerates it after any track change; the lidar and NAIP caches are keyed by the box.

- **Ortho grade** (`grade_ortho`): one black point for all channels (0.5th percentile), one white point, gamma
  1.25, 25 % smoothstep S-curve, +6 % saturation. Per-channel black points turn dry grass orange. The washed-out
  look was the renderer (ACES exposure ×1.75, cold sky fill 1.4, fog from 500 m), fixed in the app, not the data.
- **Lidar grids** at 1 m: bare-earth DEM, max of all returns, max of class 1, max of class 17 (bridge deck), and
  the multi-return share of class 1. The survey has no vegetation or building classes.
- **Trees:** class-1 height over 2 m with multi-return share over 0.18 (roofs are single-return); crowns are local
  maxima over 3 m at least ~4 m apart; radius √(area/π) clamped 1.2 to 11 m; building footprints and anything
  within 1.5 m of the edge masked. The app then removes any tree within 10 m beyond its crown of any driveable
  centreline (track, pit lane, paved runoff): no trees where a car can go. Far trees: dark greenish blobs in the
  5 m/px NAIP, capped at 7000.
- **Buildings:** OSM footprints with height = p85 of the lidar surface in the footprint (fallback levels × 3.2 m or
  4 m), kinds kept for `grandstand`, `garage`, towers; unmapped compact single-return blobs 45 to 6000 m² as
  rotated rectangles. Grandstands with 4-corner footprints render as stepped 0.85 m tiers.
- **Bridges:** OSM `bridge=yes` ways crossing the circuit; deck height from class-17 points or the surface 3.5 to
  12 m above the track, default 6 m; span = the part within 25 m of the edge. Banners only with text legible in
  the footage.
- **Barriers:** OSM walls resampled at 2 m, pushed out to ≥ 2 m from the edge; median distance under 14 m means
  1 m concrete plus 3 m catch fence, else Armco. Tyre walls hand-placed by metres before/after the corner s on
  the outside of the heavy-braking and runoff corners, 1 m in front of the nearest wall (12 m out if none),
  rendered as stacks every 0.58 m with a white pair every 12. Pit wall 1.1 m concrete 0.6 m off the left edge
  along the OSM pit lane, set back where the footage shows it. Collisions come from these runs, footprints and
  trunks (`createCollisionWorld`), so place nothing on the road.
- **Edge lines:** 0.12 m white, 0.15 m inside the edges, broken through kerbs and where the pit lane touches;
  drawn by rule, since NAIP cannot see them.
- **Pit lane:** OSM way at 1 m, 4 m half-width fallback, edges inside the track clamped onto the track edge at the
  track's height, stretches inside the track's paved width dropped, straight-line DEM cross-sections. Pit-exit
  cones (`pit_exit_cones`) along the blend boundary at ~10 m, crossing them is a black flag.
- **Paved runoff** (config `scenery.paved_runoff`, from the footage, later than the lidar): zone from the edge to 1.5 m short of
  the wall, tapered ends, heights = the surface the car drives on (edge blending to the heightfield over 5 m).
  Never a flat DEM fit (it creased the kerbs and paint at the zone ends). Rendered in the aerial's own colour.
- **Kerbs:** apex kerb inside every directed corner (half-length 0.9 × radius, 28 to 45 m; kinks ±25 m), exit kerb
  outside from s + 15 m, 45 to 70 m, 1.5 m green beyond; 0.9 m wide inside the edge, red/white every 2 m with a
  dark seam; then re-measured per corner against the footage. Sausage kerbs (`sausages`: height 0.06, width 0.5,
  gap 0.25, kerb_width 0.9) only where stills show them; the raised-cosine profile with tyre-widened half-width
  and slope cap 0.6 drives correctly, 13 cm with steep flanks rolled the car.
- **Boards and flag stand** by rule: 3-2-1 at 150/100/50 m before the braking corners, corner numbers 75 m before
  each turn, flag stand on the pit wall 8 m before the S/F bridge. Branded boards only where the footage shows them.
- **Far terrain:** 5 × 5 km at 10 m from the 1/3 arc-second DEM with the near heightfield copied in.
- **Seam and continuity:** the ribbon carries shoulder rows snapped onto the terrain mesh, no height lift, and the
  physics blends from the edge height to the heightfield over the shoulder. After every scenery build, run the
  in-page continuity scan (every ribbon, shoulder, pit, zone, kerb and line triangle against
  `window.__sim.surface`, flag over 2 cm; walk the surface from 0.5 m inside to 18 m outside each edge for steps
  and slope changes over 8 % per metre) and fix the data that creases.

- **From the Street View survey and the captures (20 Oct 2026):** walls OSM does not map as `declared_walls` (lat/lon
  polylines measured on the clean captures, material and fence from the survey); kerb paint, width and block length per
  track (`scenery.kerb`: colours, width, stripe_m; measure width and block period on the captures); paved roads of the
  circuit the loop does not use as `closed_roads` (driveable paved zones with a cone line across each mouth; an inside
  runoff the cars may use gets no cones); hillside grandstands on the terrain (`grandstand_on_terrain`).

## Stage 4: compare pass with a judge (`tools/track/compare/`)

Only after stage 1 is accepted: iterating landmarks on wrong geometry wasted five rounds at Laguna, and the judge
flagged edge mismatches every time.

1. **Team footage first.** `find_frames.py` maps logger GPS to video time (camera epochs from `sync.py`, logger
   offsets from `sync.json`) and to track s; `grab.py` extracts windscreen crops at each corner's approach, apex and
   exit from clean, sunny laps; `make_sheets.py` builds `<corner>.jpg` with the onboard frame left and the sim's
   driver-camera render right at the same s and heading; findings go to `findings.md`.
2. **Series onboard and satellite.** `make_youtube_sheets.py` captures a recent series onboard from Chrome at the
   same places; `make_satellite_sheets.py` lays the sim's top-down against the z20 captures for the whole lap, not
   only the corners; `render_post.sh` captures the sim with the post stack on.
3. **One judge run per round.** `make_judge_images.py` then `codex exec` (model `gpt-6-astra`) for the per-place
   verdicts plus the whole-lap top-down; the table, round by round, goes in the report. The judge's contradictions
   on tone are settled by the recent footage, never by re-asking. Three to four rounds is the budget; items the
   builder cannot express (curved wall ends, frontages, towers) go on a list for a builder change.

## Stage 5: calibration, AI, gate

- `npx tsx tools/calibrate/drive.ts --track <dir> --alat 1.2 --learn 25 --bank --no-files`: the autopilot on the
  ghost line against the ghost laps. Straights, braking and corner minimums within a few percent of the fastest
  real lap (Laguna ended at 1:59.24 vs 1:59.32). A corner 10 % or more slow with the car matching elsewhere is a
  geometry problem, not a car problem.
- `npx tsx tools/race/calibrate_field.ts --dry --only 619` for the AI Probe solo lap; the per-stint field pace
  (`pace.json`) is per track and must be rebuilt from that circuit's results.
- Gate before any merge: `npm run build`, full `npx vitest run`, `npx tsx tools/race/selfplay.ts` inside the band
  (Laguna: line rms 0.25 to 0.29 m, clearly-faster passes 72 to 77 %, stuck median ~10.5 s, AI-AI contacts 0.012
  to 0.038 per car-lap, recoveries 7 to 10), then a manual race start on a preview at 60 fps with no console
  errors. Fix a test only where its expectation was tied to the old geometry; never loosen a behavioural check.

### What an edge rebuild does to the AI (Laguna, 18 Oct 2026)

The race AI and the field pace are fitted to the geometry, so after any edge change expect the gate to fail and
plan one AI session:

- **Field pace fit:** one scale per stint, grip first then power. Cap the fitted lateral tyre grip at 1.20 g
  (`MU_LAT_MAX` in `src/physics/ai/field.ts`); above it pace comes from power. Uncapped, the fit reached 1.48 g
  for the quickest cars on 200TW tyres and they rolled over at T2. The field median is about 0.72 g.
- **AI driver deficit:** scale 1 must mean the real lap. The deficit on the painted road was the speed profile
  ignoring banking and crests: 85 % banking credit (100 % ran cars wide at Rainey), a crest load term, margins
  0.97 lateral / 0.85 braking, and the grip limiter only above 1.5× the banked grip.
- **Lane model:** a narrower road has fewer lanes; passes fall (Laguna 72–77 % → 69 %) and contacts rise
  until the corridor beside a car alongside (0.70 m), the merge-back look-ahead (60 m) and a no-passing zone
  through the Corkscrew are set. Re-base the self-play band to the new geometry with a dated note; never
  loosen a behavioural check.
- **Player-car grip is decided on evidence, not on an autopilot:** compute the tyre share the real laps imply
  on the line per corner (banking included, once with the line allowed onto the kerbs), prove the calibration
  autopilot has saturated, and only then sweep mu0. At Laguna the autopilot needed an unphysical 1.83 g peak to
  match the real lap while the geometry asked 1.18–1.26 g only where paved aprons let real drivers run wide,
  so the car was left alone.

- **Narrowing an exit moves the self-play band.** Laguna's T11 exit came in 2.7 m on the right (edge to the white line
  instead of the green runoff strip's outer limit) and AI-AI contacts went from 0.02-0.04 to 0.06-0.08 per car-lap on
  three seeds with the alone-line rms improving (0.40 -> 0.26 m). Re-run self-play on at least three seeds after any
  edge change and treat a band miss as AI lane-model work, never as a reason to widen the track.

## Stage 6: app wiring (done once, 19 Oct 2026)

The app, the scoreboard and the tools read one registry, `TRACKS` in `src/scoreboard/config.ts` (dir, name, short,
`length_m`, pace file) with `DEFAULT_TRACK`. A page picks its track from `?track=<id>` (`src/app/track-choice.ts`);
the Start menu shows a Track choice once two tracks are registered (a pick reloads with the new `?track=`). The rolling
start is 230 m before the track's last directed corner (`lastCorner` in `src/scoreboard/sim.ts`). Boards are keyed
`track/car`. The race tools take `--track <id>` (`tools/race/load.ts`: selfplay, sim_race, calibrate_field, pace).
A new track needs: its `TRACKS` entry (`length_m` = track.json's), `public/cars/field/<id>/pace.json` (pace.ts with that
circuit's results, then calibrate_field.ts --track <id>), a `PHYSICS_VERSION` bump, and its tests' fixtures if any.

## Dead ends not to repeat

- Station-by-station traces and stretch patches with blends (`fix_edges_paint.py`, `fix_rahal_left.py`,
  `fix_t11_exit_right.py`, `fix_edge_waves.py`, 18 Oct): 20-80 m waves the hood camera sees. Fit, do not trace.
- A spline fit whose 'keep' zone holds a step in its prior: the spline rings ahead of it (Laguna T11 apex left fell to
  a 1.7 m half-width in the dry run). Interpolate the prior across such a junction (`prior.interp`) or declare it.

- A spline through the OSM nodes as the centreline (v1): kinks at way junctions, corner radii 20 to 70 % too
  tight, ghost speeds implying 1.5 to 2.2 g; recentring along its own normals kept the kinks.
- NAIP asphalt-extent edges, symmetric half-widths clamped 4.5 to 8.5 m: 1 to 4 m too wide, 3 to 4 s a lap.
- z19 screenshots for edge tracing; only z20 resolves the painted line.
- The first lidar correction (3 to 5-return medians, zero fill, 1 m smoothing) and the 0.15 m edge snap: 1 to
  2 cm noise everywhere, felt as dips at apexes.
- Flat DEM fits for runoff zones; per-channel black points in the ortho grade; the clipped racing-line blend;
  rockyweb LAZ downloads; tall steep sausage kerbs; landmark rounds before the geometry is right; parallel
  agent swarms; raising a render exposure to fix a washed-out ortho.
