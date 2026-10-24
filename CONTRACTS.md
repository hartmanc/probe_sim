# Probe Sim — data and code contracts

Browser racing sim for the 24 Hours of Lemons car #619, a 1993 Ford Probe GT, on
WeatherTech Raceway Laguna Seca. Several people build parts of this in parallel;
this file is the agreement between them. If you must deviate, document it here.

Stack: Vite 8 + TypeScript 7 + three 0.186 (installed in node_modules), vitest 5.
Python tooling runs with `uv run --python 3.12 --with <pkgs> python script.py`
(system python has no numpy/pandas). Blender 5.2 LTS is at
`/Applications/Blender.app/Contents/MacOS/Blender`.

## 1. Coordinate frames

**World ENU (all data files, physics):** metres. Origin lat0 = 36.5843,
lon0 = -121.7535 (same as the existing Laguna analysis).

```
R = 6378137
x = radians(lon - lon0) * R * cos(radians(lat0))   # east
y = radians(lat - lat0) * R                          # north
z = elevation_navd88 - z0                            # up, z0 recorded in track.json
```

**three.js scene:** X = x (east), Y = z (up), Z = -y (south). Loader converts.

**Vehicle body frame (physics, ISO 8855):** x forward, y left, z up. Origin =
midpoint of the wheelbase, midpoint of the track width, on the ground plane at
static ride height.

**glTF car model:** +Z = nose, +Y = up, +X = car's LEFT side. Same origin as the
body frame. body→model: model.x = body.y, model.y = body.z, model.z = body.x.
(Blender: model the car nose toward Blender -Y, Z up; the glTF exporter then
gives exactly this frame.)

Heading convention: yaw ψ measured from +x (east) toward +y (north), radians.

## 2. Track package `public/tracks/laguna_seca/`

### `track.json`
```jsonc
{
  "name": "WeatherTech Raceway Laguna Seca",
  "origin": { "lat": 36.5843, "lon": -121.7535 },
  "z0_navd88": 230.0,              // DEM elevation subtracted from all z
  "direction": "ccw",              // driving direction as seen from above
  "spacing_m": 1.0,
  "n": 3600,                       // number of stations; loop is closed (station n wraps to 0)
  "length_m": 3600.0,
  "center": [[x, y, z], ...],      // n stations along the track CENTRE, in driving order, station 0 = start/finish
  "left":   [[x, y, z], ...],      // left edge (driver's left) at the same station
  "right":  [[x, y, z], ...],      // right edge at the same station
  "profile": {                     // cross-section heights per station, from left edge to right edge
    "fractions": [-1, -0.6667, -0.3333, 0, 0.3333, 0.6667, 1],
    "z": [[z_-1, ..., z_+1], ...]  // n rows, 7 values, sampled from the lidar DEM
  },
  "start_finish": { "index": 0 },
  "corners": [ { "name": "Andretti Hairpin", "s": 480 }, ... ],   // s in metres from start/finish
  "heightfield": { "file": "heightfield.bin", "x0": -900, "y0": -700, "dx": 2.0, "nx": 900, "ny": 800 },
  "ortho": { "file": "ortho.jpg", "x0": -900, "y0": -700, "x1": 900, "y1": 900, "width_px": 3000, "height_px": 2667 },
  "sources": "OpenStreetMap (ODbL), USGS 3DEP 1 m DEM 2017 (public domain), USGS NAIP imagery (public domain)"
}
```
- `s` (distance along track) = station index × spacing_m. `n × spacing_m = length_m`.
- Left normal at a station with unit tangent t = (tx, ty) is n = (-ty, tx).
- `heightfield.bin`: float32 little-endian, row-major, `ny` rows of `nx` values;
  value (i, j) is ground z at x = x0 + j·dx, y = y0 + i·dx. Covers the track
  bounding box plus ≥ 150 m margin. No NaNs (fill holes).
- `ortho.jpg`: aerial image covering exactly the box (x0, y0)–(x1, y1) in ENU,
  **north up** (row 0 is y1). Pixel grid is linear in ENU x and y.
- `preview.png`: a quick plot of centre/edges over the ortho for eyeballing.

### `ghosts.json`
```jsonc
{
  "track": "laguna_seca",
  "s_grid_m": 2.0,                 // all arrays below are sampled at s = 0, 2, 4, ... < length_m
  "line": { "offset_m": [...] },   // synthesized racing line: lateral offset from centre, +left, per grid point
  "laps": [
    {
      "id": "driver_a_best", "driver": "driver A", "label": "driver A 1:59.32",
      "kind": "real",              // "real" | "optimal"
      "lap_time_s": 119.32,
      "t": [...],                  // seconds since crossing start/finish, monotonic, t[0] = 0
      "v_mps": [...], "rpm": [...], "throttle": [...]   // throttle 0..1 (logger sensor maxes at 95 % = full)
    }
  ]
}
```
Ghost placement in the app: at sim time τ find s with t(s) = τ, then world
position = centre(s) + line.offset(s)·leftNormal(s), z from the profile.

### 2b. Scenery `scenery.json`, `far_heightfield.bin`, `far_ortho.jpg`

Optional; the app runs without them. Built by `tools/track/build_scenery.py`
(details in `tools/track/README.md`). All coordinates ENU (§1), z relative to `z0_navd88`.
```jsonc
{
  "version": 1,
  "units": "ENU metres (CONTRACTS section 1); z relative to z0_navd88 of track.json",
  "sources": "OpenStreetMap (ODbL); USGS 3DEP lidar ...; USGS NAIP ...; hand-placed items noted in each entry's src",
  "far": { "heightfield": { "file": "far_heightfield.bin", "x0": -2500, "y0": -2500, "dx": 10, "nx": 501, "ny": 501 },
           "ortho": { "file": "far_ortho.jpg", "x0": -2500, "y0": -2500, "x1": 2500, "y1": 2500 },  // or null
           "ground_color": "#b59a6a" },          // used when there is no far ortho
  "trees":     { "stride": 5, "fields": ["x","y","z","height","crown_radius"], "scale": 0.1, "data": [int, ...] },
  "far_trees": { ...same... },                   // outside the ortho box; value = data[i] * scale
  "buildings": [ { "kind": "building|garage|grandstand|tower", "name": "", "z": base, "h": height,
                   "footprint": [[x, y], ...], "src": "osm|lidar" } ],
  "bridges":   [ { "id", "kind": "foot|road", "name", "s": station crossed, "deck_z": deck top,
                   "a": [x, y], "b": [x, y], "width": m, "banners": [[texts facing oncoming cars], [texts on the far face]],
                   "style": "deck|arch" } ],
  "barriers":  [ { "kind": "concrete|armco|tyres|pitwall|fence", "h": wall height, "fence": catch-fence height above it (0 = none),
                   "pts": [[x, y, ground z], ...], "src": "..." } ],
  "kerbs":     { "width": 0.9, "inside": true (kerb lies edge - width .. edge; v2 edges include kerbs), "stripe_m": 2.0,
                 "strips": [ { "side": 1 (left) | -1 (right), "s0": station, "s1": station (may exceed n; wraps),
                               "kind": "apex|exit", "paint": green strip width beyond the kerb (optional) } ] },
  "edge_lines": { "width": 0.12, "inset": 0.15 (m inside the edge), "runs": [ { "side": 1 | -1, "s0", "s1" } ] },  // painted white lines
  "pit_lane": { "spacing_m": 1, "fractions": [same as track.json], "open": true,
                "parts": [ { "n", "center": [[x,y,z]...], "left": [...], "right": [...], "profile_z": [[7 values]...],
                             "gap_left": [m to the track edge per station], "gap_right": [...], "track_s": [s at first, last] } ] },
               // paved pit lane: open polylines, same layout/profile mapping as the track (f<0 scales the left half-width);
               // physics: createTrackSurface(track, hf, { pitLane }) -> mu 1.0 and paved = true there (onTrack false)
  "paved_zones": { same layout as "pit_lane" }, // paved runoff (parts carry "turn"); the app appends these parts to the
               // pit lane's for createTrackSurface({ pitLane }) -> mu 1.0, paved = true; rendered as asphalt
  "pit_exit_cones": { "spacing_m": 16, "s0": 122, "s1": 375, "pts": [[x, y, z], ...], "src": "..." },
               // the black-flag cone line on the driver's left from the pit-wall end (s0) to where the pit-exit road
               // splits off (s1); pts every 2 m along the painted blend line, cones drawn every spacing_m (no collision)
  "landmarks": [ { "kind": "brake|corner|flagstand|oak|banner|sign|gantry", "text", "x", "y", "z", "heading": rad (direction the face points, §1 convention), "h", "w",
                   "x2", "y2", "z2" (gantry: second tower) } ]
}
```
- `far_heightfield.bin`: float32 LE, same layout as `heightfield.bin`; inside the
  near box it repeats the near heightfield so the seam matches.
- `far_ortho.jpg`: north up over its box, like `ortho.jpg`.
- Barriers stay ≥ 2 m outside the track edge, except `pitwall` (0.6 m).
- `pit_exit_cones`: `build_scenery.py --only pit_exit_cones` rewrites just that section (no downloads). Crossing
  the polyline is a violation: `PitExitCones` in `src/app/trackmath.ts` fires once per crossing, re-arms 4 m clear
  of the line, ignores jumps over 25 m and must be `clear()`ed on reset. Hot lap shows a black-flag toast; race mode
  calls `director.reportViolation('pit_exit_cones')` (§4e).

## 3. Car package `public/cars/probe_gt/`

### `probe.glb`
glTF binary, metres, frame as in §1. Required node names:
- `body` — everything that moves with the chassis except the wheels.
- `wheel_fl`, `wheel_fr`, `wheel_rl`, `wheel_rr` — one mesh each, origin at the
  hub centre, axle axis = local +X. Spin is a rotation about local X.
  Wheel centres must sit at: x = ±0.757 (left +), z = 0.316, nose-ward z(glTF) =
  +1.307 front / -1.307 rear. Tyre radius 0.316 m (225/50R16).
- `steering_wheel` — origin at the rim centre; local +Z points at the driver
  along the column axis; rotate about local Z to steer.
- `cam_driver` — empty at the driver's eye point (helmet, left seat).
- `cam_hood` — empty just above the hood near the windscreen base.
Budget ≤ 90 k triangles total (was 80 k; see Deviations). Materials: PBR, textures baked into the glb.

### `car.json`
Physics spec, schema owned by `src/physics` (see `src/physics/spec.ts`).
Values for the Probe live in this file so the car can be tuned without code.

## 3b. Field cars `public/cars/field/`

The 45 cars of the Lemons "Twenty Ridiculous Years" race at Laguna Seca (12 Oct 2026), raced by the AI (§4e).
Every file here is optional: a missing row or file degrades a car, never the race (see "Fallbacks" below).
Files are joined by `number`, which is a **string** ("0" is a real car number). #619 is the player.

| File | Built by | Read by |
|---|---|---|
| `identity.json` | `tools/cars/field/build_identity.py` (curated rows in `cars_data.py`; method in `tools/cars/field/NOTES.md`) | AI car construction (`src/physics/ai/field.ts`), the box-car fallback, `tools/audio/families/make_index.py` |
| `pace.json` | `tools/race/pace.ts`, then `tools/race/calibrate_field.ts` | `RaceDirector` |
| `models.json`, `models/<num>.glb` | `tools/cars/build_car.py` (scratch kit or import path) | app `field-cars.ts` / `loader.ts` |
| `credits.json` | `tools/cars/kit/import_model.py` | credits screen (§5f) |
| `models/credits.json` | `tools/cars/build_car.py` | credits screen (§5f) |

### `identity.json`
An array of 45 rows in finish order. One row:
```jsonc
{
  "number": "189", "team": "Tired Iron Racing", "class": "A",
  "grid": 7, "finish": 2, "class_finish": 2, "laps": 203, "best_lap_s": 109.158,   // MYLAPS / Speedhive
  "make": "Mazda", "model": "MX-5 Miata", "generation": "NA (1989-97)", "year": 1991,
  "body": "roadster",
  "confidence": "high",                         // high | medium | low: how sure the make/model identification is
  "evidence": "Prior Lemons awards: ...; photos: ...",
  "dims": { "wheelbase_m", "length_m", "width_m", "height_m", "track_m" (front), "mass_kg" (stock curb), "power_kw",
            "source": "<Wikipedia URL>", "verified_this_run": false, "note": "..." },
  "engine": {
    "family": "Mazda B6 1.6 I4",                // free text; the audio aliases match on it
    "cylinders": 4,
    "layout": "I4",                             // I3 | I4 | I6 | V6 | V8 | flat4 (rotary etc. allowed, falls back by cylinders)
    "displacement_l": 1.6, "aspiration": "NA",  // NA | turbo | supercharged
    "redline_rpm": 7200, "stock_power_kw": 86,
    "exhaust_note": "loud open",                // free text; mapped to a muffler value (§5e)
    "confidence": "high",                       // high | medium | low: low = swap likely, donor unknown, stock engine kept
    "evidence": "1991 = 1.6 B6"
  },
  "colors": { "primary": "#d98a4a", "secondary": "#e8b070", "accents": ["#222222"] },
  "numbers": { "color": "black on white roundel/board", "boards": ["door", "rear wing endplate"] },
  "livery": "...", "theme": "...",
  "photos": ["IMG_8207.jpg", "IMG_8207_XL.jpg", ...],   // in tools/cars/field/photos/<number>/ (not shipped)
  "photo_sightings": 18
  // optional, read by field.ts when present: "drive": "fwd|rwd|awd", "gears": n (overrides of the derived values)
}
```
- `dims` are infobox-level (about ±2 % on length and width, ±10 % on mass) unless `verified_this_run`.
- Race photos are SmugMug gallery images: **reference only, never reused in a model or shipped** (licence rules below).

### `pace.json`
```jsonc
{
  "ai_version": 5,                              // AI_VERSION the file was generated for
  "source": "MYLAPS session 12975608 (...); tools/race/pace.ts",
  "track": "laguna_seca",
  "calibrated": { "ai_version": 5, "date": "2026-10-17", "tolerance": 0.002 },   // set by calibrate_field.ts
  "cars": [ {
    "number": "0", "team": "The Supranos", "class": "A",
    "grid": 2, "finish": 38, "classFinish": 8, "lapsCompleted": 104, "greenLaps": 91,
    "targetLap": 130.447,                       // s, median green non-pit lap (outliers > 1.3 x median dropped)
    "bestLap": 112.619, "sigma": 12.165,        // sigma = 1.4826 x MAD, s
    "aggression": 2,                            // 0 | 1 | 2, seeded from the number, class-weighted
    "scale": 0.9136,                            // fitted pace scalar (§4e: paceSplit → grip, power)
    "achievedLap": 130.685,                     // solo lap at that scale
    "stints": [ {                               // the car's real pit-to-pit stints = its drivers; a race draws ONE (drawPace)
      "index": 0, "laps": 23, "firstLap": 2,
      "targetLap": 126.9,                       // s, median of that stint's clean laps (pace.ts outlier rules)
      "bestLap": 118.1, "sigma": 4.2,
      "scale": 0.955, "achievedLap": 126.95     // fitted per stint
    } ],
    "player": true,                             // #619 only
    "resolved": {                               // the car the physics actually built (for audio, HUD, debugging)
      "make", "model", "drive": "fwd|rwd|awd", "enginePos": "front|mid|rear", "frontWeight": 0.53,
      "engineLayout": "I6", "cylinders": 6, "turbo": true, "redline": 7000, "shiftRpm": 6500,
      "gears": 4, "gearRatios": [overall ratios, 1st..top], "massKg": 1000,
      "powerKw": 157.1,                         // after the power factor (stock, or the swap floor, unless grip alone could not reach the lap)
      "gripScale": 0.91, "powerScale": 1.0,     // paceSplit(scale)
      "lateralG": 0.96, "topSpeedKph": 171.2,   // driver lateral budget and drag-limited top speed
      "stockPowerKw": 206, "exhaustNote": "loud open",
      "probeFallback": false                    // true = no identity row, built as a Probe clone
    }
  } ]
}
```
- Regenerate: `npx tsx tools/race/pace.ts` (keeps fitted scales), then `npx tsx tools/race/calibrate_field.ts`
  (worker threads, about 5 min for 45 cars + 266 stints with 4 workers, every fit within 0.2 % of its target).
- **Driver draw:** `drawPace(car, seed)` (field.ts) picks one stint uniformly from (seed, number, AI_VERSION); the
  director builds the car with that stint's scale and the driver with its targetLap / sigma; `restart(seed)` redraws
  and rebuilds the AI cars whose draw changed. A car without eligible stints keeps its car-level pace. The draw is
  internal: never in the HUD or results (owner's call).
- **Pace fit = grip first:** `paceSplit(scale)` maps the fitted scalar to a grip factor (tyre mu, brakes, speed
  sensitivity; 0.55-1.25) and a power factor (engine torque; 1 inside that grip range, cubic outside it). Power
  therefore follows the car's own powertrain (identity stock power or the 70 % swap floor): heavy V8s are quick on
  the straights and slow in corners, light turbo cars quick everywhere. The driver's speed profile is the car's own
  limit (grip + acceleration + braking passes); the ghost shape is only a 1.3x sanity cap.
- If `calibrated.ai_version` is older than the code's `AI_VERSION`, the director sets `calibrationStale` and
  estimates `scale = 121.5 s / targetLap`. Recalibrate after every `AI_VERSION` bump.

### `models.json` and `models/<num>.glb`
```jsonc
{
  "about": "...",
  "cars": [ {
    "number": "1", "file": "models/1.glb", "tris": 9895, "bytes": 568504, "materials": 2,
    "length_m", "width_m", "height_m",          // from the spec
    "bbox_m": [x, y, z],                        // includes mirrors, wings and props
    "wheelbase_m": 2.036, "track_front_m": 1.21, "track_rear_m": 1.17,
    "tyre_radius_m": 0.262,                     // FRONT wheel mesh radius
    "tyre_radius_rear_m": 0.262,                // rear (may differ: per-axle tyres)
    "hubs": { "wheel_fl": [x, y, z], "wheel_fr": [...], "wheel_rl": [...], "wheel_rr": [...] },  // glTF translations, model frame
    "brake_lamps": [[x, y, z, r], ...],        // rear lamp lens centres, model frame (+z forward): lit discs under braking
    "team": "Team Bean Redux", "car": "1962 Austin Mini (Mk1)",
    "import": { "method", "scale", "source_tris", "model_track", "model_tyre_radius", "hub_z_front", "hub_z_rear",
                "model_length", "model_width", "model_height", "tris", "file" }   // only for imported bodies
  } ]
}
```
A car without a row has no glb: the app draws the box car. The app reads `models.json` once at the first race
of a page load and loads the glbs lazily in the background, swapping them in live; a reload picks up new builds.

**glb node contract (field cars).** Frame and origin as §1 (glTF +Z nose, +Y up, +X car's left, metres, origin
mid-wheelbase / mid-track on the ground). Checked by `tools/cars/kit/check_car.py`:
- `body`, `wheel_fl`, `wheel_fr`, `wheel_rl`, `wheel_rr` at the **scene root**, unit scale.
- Wheel nodes: origin at the hub, identity rotation, axle = local +X (spin about local X). Hubs within 5 mm of
  (±track/2, tyre radius of that axle, ±wheelbase/2) and symmetric. The wheel mesh radius equals that axle's
  tyre radius (1 % + 2 mm).
- `cam_driver` and `cam_hood` empties are present (the kit adds them). No `steering_wheel` is required.
- ≤ 12 000 triangles, file < 1.5 MB, JPEG textures, 2 materials (livery atlas + glass). The bbox length must be
  within 8 % of spec length + bumpers; width and height only warn (props, mirrors).
- The app (`CarRig`) takes `{ tyreRadius, physicsRadius, castShadow }`, places wheels from the physics state and
  drops the hub offset, so a wheel of a different radius still touches the road.

**Fallbacks.** No identity row → Probe clone (V6, FWD, 5 speeds) at the car's pace scale. No glb → a ~300-triangle
box car in `colors.primary` (else the director's tint) with number boards, sized from the physics hull.
No `pace.json` → no race.

### Credits (two files)
- `credits.json` (here): **3D model bases** of imported bodies, written by `import_model.py`:
  `{ "about", "cars": { "<num>": { "title", "author", "licence", "licence_url", "url", "changes" } } }`.
- `models/credits.json`: **external images** painted on a car (decals, cards, windshield banners), written by
  `build_car.py`: `{ "<num>": [ { "image", "source", "author", "licence" }, ... ] }`. A car that uses no external
  image has no key (the build removes it). The list can repeat an image used twice.
- **Merge rule** (credits screen, §5f): per car number, the model credit (if any) followed by the image credits,
  de-duplicated on `source`; a car appears if either file has it. Kit procedural images (`kit:*`) need no credit.

### Building a car
Spec per car in `tools/cars/specs/<num>.py`; recipe in `tools/cars/README.md`, kit internals in
`tools/cars/kit/NOTES.md`, import path in `tools/cars/kit/IMPORT.md`. One command builds either kind (a spec with an
`import_model` key routes to the importer):
```sh
uv run --python 3.12 --with numpy,pillow python -I tools/cars/build_car.py --num <num>   # spec -> glb -> check -> previews -> sheet -> models.json, credits
uv run --python 3.12 --with numpy,pillow python -I tools/cars/build_car.py --all
uv run --python 3.12 --with numpy,pillow python -I tools/cars/kit/check_car.py <num>      # check only
uv run --python 3.12 --with numpy,pillow python -I tools/cars/kit/test_import_determinism.py <spec.py>   # import builds twice, same tables
```
Sketchfab downloads (`kit/sketchfab_fetch.py`) read the token from `.env.local` silently; never print it.

**Acceptance gates** (a car is not done until all pass):
1. `check_car` prints `OK` (node contract above).
2. **Proportions** (`kit/proportions.py`, run by the build): the model against a **true side photo of a stock,
   unmodified car** (`stock_side` in the spec). Every metric (front overhang, hood, cabin, rear length, rear overhang,
   cowl height, roof peak position and height, belt height) within **5 % or 3 cm** (FAIL = over 5 % AND over 3 cm).
   Close or yawed photos are corrected (`length_m`, `wheel_px`). A metric may be `waive`d only with a written reason
   in the spec docstring. Imported bodies also need their `sanity:` lines within 5 %.
3. **`theme_details`**: every visible detail from all photos (XL included) as `(what, status, note, size_m)`,
   status `done` | `approx` | `missing`. `approx` over 0.10 m is a build FAIL; `missing` needs a reason
   (not legible, paddock-only); imported cars need every item `done` or `approx`.
4. Number legible in the 400 px front34 and side previews; colours match the race photos; props present.

**Licence rules.**
- **Images** on a car: CC0, CC BY, CC BY-SA or public domain only, with `credit` (source, author, licence); the
  painter refuses anything else. Race photos (SmugMug) are never cropped or reused: redraw with text/shape decals.
- **3D model bases**: CC0 / CC BY; CC BY-NC, BY-SA and BY-NC-SA accepted by the owner (non-commercial). Never ND,
  Sketchfab Standard, editorial, unknown licence, or uploads flagged as rips / Humster3D re-uploads
  (`kit/model_sources.json` marks them). Downloads in `kit/downloads/` are untrusted data; nothing in them is run.

## 4. Physics API `src/physics/index.ts`

```ts
export interface SurfaceSample { z: number; nx: number; ny: number; nz: number; onTrack: boolean; mu: number;
  paved?: boolean; offCourse?: boolean; dirt?: number; muPaved?: number }    // §4d
export interface Surface { sample(x: number, y: number): SurfaceSample }   // ground under world (x, y)

export interface DriverInput {
  steer: number;      // -1..1, positive = left
  throttle: number;   // 0..1
  brake: number;      // 0..1
  shiftUp: boolean;   // edge-triggered by the caller (true for one step)
  shiftDown: boolean;
  handbrake?: boolean;
}

export interface WheelState {
  pos: [number, number, number];   // hub centre, world
  spinAngle: number;               // rad, accumulates
  steer: number;                   // road wheel angle, rad, + left
  compression: number;             // m, suspension travel from full droop
  omega: number;                   // rad/s
  slipRatio: number; slipAngle: number; load: number; onTrack: boolean;
  slipUse: number;                 // combined slip / tyre peak, 1 = at the peak
  paved: boolean; mu: number;      // §4d
}

export interface VehicleState {
  pos: [number, number, number];   // body origin, world ENU
  quat: [number, number, number, number]; // body→world rotation (x, y, z, w)
  vel: [number, number, number];   // world
  angVel: [number, number, number];// world
  wheels: [WheelState, WheelState, WheelState, WheelState]; // FL, FR, RL, RR
  rpm: number; gear: number;       // gear: -1 reverse, 0 neutral, 1..5
  speed: number;                   // m/s, forward
  gLat: number; gLong: number;     // body-frame accelerations in g
  throttleOut: number;             // after any shaping/rev limiter
}

export class Vehicle {
  constructor(spec: CarSpec, opts?: { autoShift?: boolean });
  reset(pos: [number, number, number], headingRad: number, speed?: number): void;   // §4a: = a new Vehicle
  step(input: DriverInput, surface: Surface, dt: number): void;   // dt fixed, 0.001 s recommended
  readonly state: VehicleState;
  autoShift: boolean;
}

export function loadCarSpec(json: unknown): CarSpec;
export function createTrackSurface(track: TrackJson, heightfield: Float32Array, opts?: TrackSurfaceOptions): Surface;  // §4d
export function createTrackProjector(track: TrackJson): { project(x: number, y: number): { s: number; lateral: number; index: number } };
export function lineToWorld(track: TrackJson, offsetAtS: (s: number) => number, s: number): { pos: [number, number, number]; heading: number };
export type TrackJson = /* mirrors track.json above */;
export * as race from './ai/index';   // §4e
```
Steering shaping (speed-dependent max road-wheel angle and rate limit) lives
in `Vehicle`, configured from `car.json`, so a gamepad stick is drivable.

### 4a. Determinism
- No `Math.random` or `Date` in `src/physics`; floating-point order is fixed. Same inputs, same JS engine → bit-identical states.
- `Vehicle.reset(pos, heading, speed?)` clears every per-run field (gear schedule, kickdown hold, clutch timers,
  launch, impact, ABS state): a reset car is **bit-identical to a new `Vehicle`** (test `ai_vehicle_reset.test.ts`).
  A NaN recovery keeps the sim clock.
- `Surface.sample()` caches the last station and returns a **reused** object, so its results depend on call
  history. Every consumer that must be reproducible owns its own `Surface` (the hot-lap sim, each race car, the
  director's rule checks); the app keeps a separate one for HUD and scenery.
- The scoreboard replay (§5d) and the race (§4e) depend on all of this.

### 4b. Driven axles
car.json `drivetrain.layout`: `'fwd'` (default; the Probe's original code path, unchanged), `'rwd'` or `'awd'`, all
with open differentials. `'awd'` is an open centre diff with a fixed torque split `drivetrain.awdFrontShare`
(default 0.4). Used by the AI field; the Probe stays FWD.

### 4c. Car-vs-car contacts
- `CarCollider` (`src/physics/cars.ts`, exported as `race.CarCollider`): oriented-box contacts between vehicles
  with impulses, friction and push-out (max penetration about 3 cm in a 45-car race).
- `Vehicle` contact hooks used by it: `cgWorld`, `pointVelocity`, `invMassAt`, `applyImpulseAt`, `nudge`,
  `reportImpact(speed, kind)`.
- `ImpactInfo.kind` (`state.impact`) gains **`'car'`** next to the wall kinds (concrete, armco, tyres, pitwall,
  fence, building, tree, boundary); the impact sound path is the same.
- Per-step contact list: `director.contacts[0 .. contactCount-1]` =
  `{ a, b, nx, ny, x, y, closing, aApproach, bApproach, impulse, depth }`.

### 4d. Surface: pavement, dirt and per-wheel friction
- `SurfaceSample` gains optional `dirt` (0 on pavement, smoothstep to 1 over the first `SURFACE_GRIP_BLEND_M` = 1.0 m
  past the nearest paved edge; track, pit lane and paved runoff are pavement) and `muPaved` (= `muOnTrack`).
  `mu = muOnTrack + dirt·(muOffTrack − muOnTrack)`, continuous at the edge. Surfaces without `dirt` count as pavement.
- `SurfaceSample.offCourse` (round 14B): true on a paved part the track package marks `off_course` (Sonoma's T9A escape
  road): pavement for grip, but off the course for lap validity, like dirt (`wheelOff` in the app, `allOff` in the
  scoreboard). Absent / false everywhere else.
- `createTrackSurface` options: `{ far, pitLane, muOnTrack (1.0), muOffTrack (OFF_PAVEMENT_MU = 0.72, was 0.6),
  gripBlend (1.0 m), roughness (DIRT_ROUGHNESS_M = 0.012 m, 0 disables), edgeBlend (SHOULDER_WIDTH_M = 5 m) }`.
  Exported constants: `OFF_PAVEMENT_MU`, `SURFACE_GRIP_BLEND_M`, `DIRT_ROUGHNESS_M`, `SHOULDER_WIDTH_M`.
- Off-pavement roughness: three waves (3.7 / 5.3 / 8.9 m), 12 mm peak in total, × `dirt`; a pure function of (x, y).
- `WheelState` gains `paved` (sample under the wheel, `paved ?? onTrack`) and `mu` (friction the tyre actually used).
  The app gates per wheel on these (off track = neither `onTrack` nor `paved`; no squeal off pavement).
- car.json `surfaces` (all optional, scaled per wheel by `dirt`): `offPavementMu` 0.72 (overrides the surface's
  `muOffTrack`; tyre mu = `muPaved·(1 − dirt·(1 − offPavementMu))`), `offPavementLateralStiffness` 0.65 (peak slip
  angle 7° → 10.8°), `offPavementRollingResistance` 0.04 and `offPavementRollingResistanceSpeed` 0.0015 per m/s (ΔCrr).
  Measured: skidpad 0.99 g pavement vs 0.76 g dirt. On pavement every new term is exactly neutral (state compared
  with `===` against a recorded drive, `surface.test.ts`). Details: `src/physics/NOTES-surface.md`.

### 4e. Race library (`import { race } from './physics'`)
Pure TS, no DOM; full spec in `src/physics/ai/NOTES.md`.

```ts
const line = new race.RaceLine(track, ghostsJson);                   // once per track
line.restrictLeft(scenery.pit_exit_cones.pts);                      // AI road edge = the pit-exit cone line (the app, tests and tools all do this)
const director = new race.RaceDirector({
  line, surface, makeSurface: () => createTrackSurface(track, hf, { far, pitLane }),   // one Surface per car
  probeJson, pace, identity: identity ?? null,                       // car.json, pace.json, identity.json (§3b)
  pitLane: scenery?.pit_lane ?? null, collisionWorld: cw,
  playerVehicle, playerSurface,                                      // optional: the app's own
}, { laps: 10, seed, playerNumber: '619', greenWindow: [5, 30] });   // Partial<RaceConfig>
director.step(0.001, playerInput);   // per physics step: steps EVERY car incl. the player's (do not call vehicle.step)
director.hud();                      // per frame: RaceHud (phase, flag, lap, position, gaps, penalties, message, results)
director.poses();                    // per frame: CarPose[] { number, isPlayer, state: VehicleState, tint, identity, engine }
director.restart(newSeed);           // same field, new grid and green moment
director.reportViolation('pit_exit_cones', detail?);  // app-side rule → black flag, same escalation; 1 per kind per 2 s
director.penalize(reason); director.penaltyBoxSpot(); director.setYellow(on); director.getResults();
director.timeScale;                  // per frame: 10 while a stop-and-go is fast-forwarded (car held in the box), else 1
```
- `RaceConfig` defaults: `laps 10, seed 1, ai_version AI_VERSION, playerNumber '619', greenWindow [5, 30],
  formationSpeed 20, gridGap 15, aiControlEvery 2, aiPhysicsEvery 2 (AI physics at 500 Hz, staggered), aiWalls true,
  playerAi false, maxAi ∞`. Construction measures every car: about 0.25 s for 45.
- `AiDriver(vehicle, line, perf, spec, profile, params, idx, traffic)`: `update(dt) → DriverInput` (pure pursuit +
  yaw feedback + understeer feed-forward, speed profile + PI, traffic). Race control sets `driver.ctl`
  (`speedCap, noPass, minGap, paceFactor, noise`). `AiDriverParams = { number, scale, targetLap, sigma, aggression, seed }`.
- AI car = Probe car.json overridden by identity (mass, dimensions, drive layout and weight split, engine shape,
  redline, gear count), then pace scale p: tyre mu × p² (× p below 1), brakes likewise, torque × p³. AI cars are
  never penalized; player rules (contact at fault above `CONTACT_FAULT_CLOSING` = 5 mph closing, four wheels off, passing under yellow; warning → stop-and-go
  60/60/180 s → ejected) are in the NOTES.
- **Determinism:** a race is reproducible from (`seed`, `AI_VERSION`, pace.json, identity.json) plus the player's
  inputs, given `makeSurface`. The green moment is seeded and never exposed. **Bump `AI_VERSION`** (`ai/field.ts`,
  now 5) whenever driver logic or AI car construction changes, then recalibrate pace.json; the race scoreboard
  board key includes it (§5d).
- Cost: whole field (45 AI + player) about 60 µs per 1 ms step on an M3 (6 % of real time).
- **Racecraft (the lane model) and mishaps** (NOTES "Racecraft (the lane model) and mishaps"). Every car has a lane coordinate e (lateral offset
  from the racing line), measured by the director (`Traffic.e`, rate `ve`) and aimed for by its driver (`Traffic.eT`);
  it occupies [min(e, eT, e + 0.6 s drift) ± half width], lanes `Traffic.laneW` apart (widest car + 0.6 m, 2.63 m now).
  A car follows only a car whose span overlaps its path (now, or where it will catch it with both lanes clamped to the
  road). A car whose target lap is > 3 % quicker than the car ahead's (clearly faster) plans a pass every 0.2 s: the
  lane beside the blocker (or the one beyond) that is on the road, quicker for it, and free until it is clear ahead,
  occupants projected forward at their speed and the road squeezing lanes together counted as occupancy; it holds that
  lane past one car or a train, merges back when the racing lane is free around it, gives up when it falls 30 m back,
  the lane is blocked, or after 30 s. The car being passed never defends, holds its lane, never drifts into its
  passer's lane, makes room where the road pinches the passer onto it, and lifts 3 % only when the passer is alongside
  and converging; the car further back yields where two lanes pinch. Within 3 % the slower car covers the inside
  lightly (0.5-1.1 m, once per corner) when the car behind is within ~1 s. Solo laps are unchanged. AI losses of control: per AI car per
  corner passage during green, p = `RaceConfig.mishapRate` (default 0.0002) × corner difficulty (`RaceLine.corners`,
  mean 1; T2, the Corkscrew and T9 hardest) × aggression (0.6 / 1 / 1.5); 70 % run wide, 30 % spin (marshal reset).
  Seeded from each car's own Rng, so a race stays reproducible from (seed, AI_VERSION); never the player, never without
  pace noise, no yellow. `director.mishapLog`, `director.mishaps`, `car.mishaps` for tools and tests (not in the HUD).
  Measure with `tools/race/selfplay.ts`.

## 5. App `src/app/`

Owns rendering, input, HUD, audio, lap timing, ghosts, cameras. Imports only
the public physics API above. Loads the packages from `public/` by relative
URL (`tracks/laguna_seca/track.json` etc.) so the site works under any base path.
File-level documentation: `src/app/README.md`.

### 5a. Modes
Main menu → **Hot lap** or **Race** (5 laps vs the 2026 field; was 10 until 17 Oct 2026). `src/app/modes/mode.ts` is the integration point:
```ts
interface GameMode {
  id: 'hotlap' | 'race'; label: string;
  start(): void; restart(): void;        // restart = pause menu → Restart (fresh session; race: new seed)
  reset(): void;                         // R / Back: hot lap → rolling start; race → recover on the centreline at the current s
  step(dt: number): void;                // after every 1 ms physics step; never while a menu is open
  onLap(lap: Lap): void;
  frame(dt: number, now: number): void;  // once per rendered frame
  hud(): { banner: string | null; timing: boolean; delta: number | null; showDelta: boolean };
  pauseEntries(): MenuEntry[];
  dispose(): void;
}
```
- The player's car always runs in `HotlapSim` (`src/scoreboard/sim.ts`) through `HotlapLoop` (modes/hotlap.ts):
  1 ms steps, input sampled at 100 Hz and held, shift presses latched to the next sample, 50 ms frame cap.
  `ModeContext.vehicle` is a getter (a reset builds a new Vehicle).
- Race: `sim.record = false` and `sim.stepVehicle = (di) => director.step(STEP, di)`, so the director steps the
  whole field with the player's quantised input. Space launch ends the player's race (status `out`, app-side).
- Pause = nothing stepped + AudioContext suspended (menus, controls panel, hidden tab, portrait phone).
- `window.__sim` exposes `menu`, `mode`, `setMode(id)`, `hotlap`, `loop`, `scoreboard`, `quality`, `vehicle` (getter).
- Dev URL flags: `?seed=`, `?laps=1..10` (submission off unless `?devsubmit=1`), `?fieldaudio=1`, `?phone=0|1`,
  `?stub=1` (ghosts only), `?devtrack=1`, `?api=<origin>` (scoreboard server).

### 5b. Input, menus and glyphs
| Action | Xbox gamepad | Keyboard |
|---|---|---|
| Steer | Left stick (deadzone 0.08, curve 1.3) | ← → / A D |
| Throttle / brake | RT / LT | ↑ / W, ↓ / S |
| Shift up / down | RB / LB | E or Shift / Q |
| Handbrake | B | Space |
| Cycle camera | Y | C |
| Auto-shift | X | T |
| Reset (hot lap) / recover (race) | Back | R |
| Pause menu | Start (**reserved**) | Esc / O (**reserved**) |
| Look around | right stick (the stick not steering), RS = look back | `,` / `.` ±90°, Backspace = back; mouse drag |
| Mute / help / controls panel | – | M / H / K |

- A is unbound while driving (menu select; also `confirm` on the game-over card with Enter / Space).
  Everything except Start, Esc, O, M, H and K is remappable in the controls panel. Pad profiles are saved with
  `v: 2` (`probeSim.controls.v1.pad:<id>`); older profiles migrate once with a toast.
- Menu navigation: d-pad / left stick (repeat 350 ms then 120 ms), A select, B back, Start resume; arrows / WASD,
  Enter / Space, Esc; tap a row on touch.
- **Glyphs** follow the last device used (`glyphs.ts`, family from `Gamepad.id`: vendor 045e Xbox, 054c PlayStation,
  057e Nintendo): Xbox A / B / RB with "Back" / "Start" for buttons 8 / 9 (the owner's 360 pad, not View / Menu),
  PlayStation ✕ / ○ / R1, Nintendo B / A / R, non-standard mappings "Button n"; keyboard users see key names, touch
  users "Tap ...". Hints name the *bound* control ("Press R or Back to reset").

### 5c. Quality tiers and touch (phone)
- `quality.ts`: `quality.tier` = `'phone' | 'desktop'`, `quality.touch`, `quality.maxAiCarsDrawn`. Phone when the
  device is `(pointer: coarse)` with touch points, or `?phone=1`; `?phone=0` forces desktop; the menu's Graphics row
  (Auto / Phone / Desktop, `probeSim.quality.tier.v1`, applied on reload) overrides auto.
- Phone tier: pixel ratio ≤ 1 and ≤ 1.2 MP, no shadow maps, anisotropy ≤ 2, trees thinned (all within 60 m, half
  to 400 m, a quarter beyond: 17 770 → 5 684 at Laguna). AI shadows: on desktop the 12 nearest AI cars cast
  shadow-map shadows inside the sun's ±30 m box at 4096 px (`quality.aiShadowCasters / shadowBoxM / shadowMapSize`,
  same ~70 px/m as the old ±7 m / 1024 px player box; `?aishadows=0` restores that); every other AI car, and all of
  them on the phone tier, gets a contact-shadow blob.
- **AI draw cap:** the race simulates every car but poses at most `quality.maxAiCarsDrawn` rigs (phone 20, desktop
  45), the nearest by wrapped track distance; the rest are hidden.
- **Touch controls** (`touch.ts`, shown only while driving): left third brake, right third throttle (pressure =
  touch height, 6 % dead band, full at 92 %); steering by **tilt** (gravity projected on the screen plane, 15 Hz
  low-pass, 32° = full lock at sensitivity 1 (0.6–1.8×), 1° dead zone, recentred at every Hot lap / Race tap) or
  a middle-third slider whenever tilt gives no readings (http, denied). Pause top right; shift paddles only with
  auto-shift off. `input.source` gains `'touch'` and `input.inputTag` = `'pad' | 'keys' | 'phone'`.
- Tilt needs HTTPS on iOS: `npm run dev:https` (port 5174, `vite.https.config.ts`). Portrait shows a rotate overlay
  and pauses. Audio: `audio.start()` runs inside the tap; AAC fallbacks (`engine_on/off.m4a`, `squeal.m4a`,
  `engine.json.fallback`) for browsers without Ogg Opus. **Re-run `tools/audio/encode_fallback.py` after
  `build_engine.py` / `build_squeal.py`**, which rewrite engine.json without the `fallback` field.

### 5d. Scoreboard
Contract, HTTP API, trace format and deployment: **`docs/scoreboard.md`** (code in `src/scoreboard/`, `api/scores.ts`).
- Boards: `hotlap:<track>:<car>:<physics>` (lap time, server replays the input trace, |replayed − claimed| ≤ 0.05 s)
  and `race:<track>:<car>:<physics>:<ai_version>` (metres in a 10-lap race, plausibility only; the seed goes in the
  reserved `replay` field). `physics` = hash of `PHYSICS_VERSION` + track length + canonical car.json, so a car.json
  change opens fresh boards automatically.
- **Bump `PHYSICS_VERSION`** (`src/scoreboard/config.ts`) whenever anything else a replay depends on changes:
  `src/physics` code, track.json, heightfield.bin, scenery.json walls / pit lane / paved zones / far terrain,
  ghosts.json (gear schedules, line), `src/app/timing.ts`, or `src/scoreboard/sim.ts`. Otherwise old traces fail
  with "lap time differs". (Bumped on 17 Oct 2026 for the off-pavement model.)
- The app drives the player only through `HotlapSim` (rules in docs §3.1); submissions only laps 1–6 after a reset.
  Race mode calls `setBoardContext({ raceAiVersion })` and `submitRace({ metres, laps, aiVersion, seed, position, finished })`.
- Client storage: `probe-sim.scoreboard.{name,device,pb.<board>}`. Without a server the board shows OFFLINE and
  driving is unaffected.

### 5e. Field audio
`public/audio/families/index.json` (built by `tools/audio/families/make_index.py` from identity.json; notes in
`tools/audio/families/NOTES.md`; player `src/app/audio-field.ts`):
```jsonc
{
  "version": 1, "base": "audio/families/",
  "families": { "<id>": { "cylinders": 4, "layout": "inline|v|flat", "redline": 6750, "idle": 750,
                          "engine": "<id>/engine.json", "sprites": { "on": "<id>/engine_on.ogg", "off": "<id>/engine_off.ogg" },
                          "real_bins": { "on": 19, "off": 14 }, "character": "..." } },  // mazda_kl_v6 points at the Probe's own files
  "aliases": [ ["<regex over 'engine.family make model'>", "<family id>"], ... ],   // first match wins
  "fallback": [ { "cylinders": 8, "layout": "v", "family": "..." }, ... ],          // then by cylinders alone, then default
  "default": "sohc_i4_loud",
  "muffler": [ ["<regex over engine.exhaust_note>", 0.0], ... ], "muffler_default": 0.3,
  "cars": { "<number>": { "family", "trim": 0.97..1.03 (stable per number), "muffler": 0..1 (0 straight pipe … 0.6 stock),
                          "rpm_scale": 1.0 (0.75 plays an I4 for #34's I3), "redline", "engine" } }
}
```
- Per family folder: `engine_on.ogg`, `engine_off.ogg` (Opus 48 kbps mono sprites), `engine.json` (same layout as the
  Probe's), `preview.mp3` (listening only, never loaded). No AAC fallback yet.
- A car missing from `cars` gets `familyFor(index, { engineFamily, make, model, cylinders, layout })`.
- Per frame the player gets each AI car's `rpm × rpm_scale`, `throttleOut`, `redline`, pos, vel from `pose.state`;
  it plays the N nearest within 150 m (8 desktop, 4 phone). Wired behind `?fieldaudio=1` until the mix is set.

### 5f. Credits screen
Lists, per field car, the merged credits of §3b (model base: title, author, licence with link, url, changes; then
each external image: author, licence, source), plus the track sources (`track.json` / `scenery.json` `sources`)
and the audio sources (`tools/audio/families/sources.json` licences). Anything shipped that carries attribution
(CC BY, BY-SA, BY-NC, BY-NC-SA) must appear there.

## Notes index

Where each part documents itself (read these before changing that part):

| Area | File |
|---|---|
| App structure, audio, menus, controls | `src/app/README.md` |
| Menus, modes, pad glyphs | `src/app/NOTES-menu.md` |
| Phone tier, touch, tilt, iOS audio | `src/app/NOTES-phone.md` |
| Cameras, driver view, look-around, game-over card | `src/app/NOTES-camera.md` |
| Race mode in the app (rigs, HUD, dev flags) | `src/app/NOTES-race.md` |
| Scoreboard client | `src/app/NOTES-scoreboard.md`, contract `docs/scoreboard.md` |
| Vehicle model | `src/physics/README.md` |
| Off-pavement surface model | `src/physics/NOTES-surface.md` |
| AI field and race director | `src/physics/ai/NOTES.md` |
| Track pipeline / scenery | `tools/track/README.md`; kerbs and pit-exit cones `tools/track/compare/kerbs/NOTES.md` |
| Player car model | `tools/car/` (detail pass `tools/car/NOTES-detail.md`) |
| Field identification | `tools/cars/field/NOTES.md` |
| Field car models | `tools/cars/README.md`, `tools/cars/kit/NOTES.md`, `tools/cars/kit/IMPORT.md` |
| Engine families (AI audio) | `tools/audio/families/NOTES.md` |
| Assumptions, data wishes, calibration history | `improvements.md` |

## Deviations

- 2026-10-17 (track scenery): added §2b (`scenery.json`, `far_heightfield.bin`,
  `far_ortho.jpg`; optional). `ortho.jpg` is now colour-graded for display
  (dehaze, gentle S-curve, +6 % saturation; `grade_ortho` in `build_laguna.py`).
  Its box and pixel grid are unchanged, and edge detection still uses the raw image.
- 2026-10-17 (physics collisions): additions to §4, existing signatures unchanged.
  `createTrackSurface(track, heightfield, opts?)` takes `opts.far = { heightfield, x0, y0, dx, nx, ny }`
  (scenery.json `far.heightfield` + decoded `far_heightfield.bin`) and uses it outside the near grid.
  `createCollisionWorld(scenery | null, track)` builds walls (barrier runs, building footprints), tree
  trunks (r 0.35 m) and an invisible boundary 200 m inside the outermost heightfield; attach it with
  `vehicle.setCollisionWorld(cw)`. `VehicleState` gains optional `impact: { speedNormal, kind, t } | null`,
  `launched: boolean` and `launchedAt: number` (hits faster than 25 m/s normal on concrete, armco,
  pit wall, building or tree launch the car into space; `reset()` clears it).
- 2026-10-17 (pit lane): `scenery.json` gains `pit_lane` (§2b). `SurfaceSample` gains an optional
  `paved` flag (track or pit lane), and `createTrackSurface` takes an optional `pitLane`. The app counts a
  wheel as off track only when it is neither onTrack nor paved.
- 2026-10-17 (physics balance pass): more additions to §4, existing signatures unchanged.
  `Vehicle.abs` (ABS toggle) and `VehicleState.absActive`; `WheelState.slipUse` (combined slip / tyre
  peak, 1 = at the peak); `tyrePeakSlip(spec)`; `deriveGearSchedule(spec, lap, grid)`,
  `scheduleTargetAt(schedule, s)` and `Vehicle.setScheduledGear(g)` (autoShift follows a ghost's gears;
  0 = rpm rules). car.json gains `brakes.abs`, `brakes.pedalExponent`, `suspension.*.complianceSteerDegPerKN`,
  `tyre.speedSensitivity`, `drivetrain.autoShift.kickdown*` and `scheduleMinUpshiftRpm` (all optional).
- 2026-10-17 (onboard comparison): `scenery.json` gains `paved_zones` (paved runoff, pit_lane layout), bridge
  `style`, and landmark kinds `banner`, `sign` and `gantry`; the building kind `hangar` gets a gabled roof.
- 2026-10-17 (race, field cars, app; merged from the agents' notes): added §3b (field cars), §4a–§4e and §5a–§5f.
  Changes to earlier lines:
  - §4 `SurfaceSample` gains `dirt` and `muPaved`; `WheelState` gains `slipUse`, `paved` and `mu` (listed in the
    interface above). `muOffTrack` default 0.6 → 0.72, now blended over 1 m past the paved edge instead of a step,
    and off-pavement ground gets a 12 mm roughness (scoreboard `PHYSICS_VERSION` bumped).
  - §4 `Vehicle.reset()` is now bit-identical to a new Vehicle (it previously kept `schedGear`, `kickHold`,
    `engageTimer`; docs/scoreboard.md §6 still describes the old behaviour). `ImpactInfo.kind` gains `'car'`.
  - §3 / car.json: `drivetrain.layout` (`fwd` default, `rwd`, `awd`) and `awdFrontShare`; `surfaces.*`.
  - `src/physics/index.ts` exports the `race` namespace and the surface constants.
  - §2b `scenery.json` gains `pit_exit_cones`; `units` and `sources` are documented.
  - §3 Probe glb triangle budget is now 90 k (detail pass, `check_glb.py`), was 80 k.
  - §5: the app no longer owns a Vehicle; the player always runs in `HotlapSim`. Start overlay and settings panel
    replaced by the main and pause menus; Start and Esc are reserved; gamepad profiles are `v: 2`.

**20 Oct 2026, track packages (§1, §2): the ENU origin is per package.** §1's lat0 = 36.5843, lon0 = -121.7535 is
Laguna Seca's origin, not a universal one. Every track package declares its own frame in `track.json` `origin`
(Sonoma: lat 38.1627, lon -122.4576), and every other file of that package (heightfield, ortho, scenery, ghosts) is in
that frame. Consumers read the origin from the package; nothing may assume Laguna's. The axes, units and z
convention (relative to `z0_navd88`) are unchanged.

**22 Oct 2026, scenery barriers (§2b), Sonoma round 12.** A `barriers[]` run may carry `top_z`: one absolute z per point
(same frame and datum as `pts`) for the top of the wall where it stands level across a hollow in its ground
(tools/track/barrier_rules.py). `pts[i][2]` stays the ground at the line and the wall is drawn from the ground to
`top_z[i]`; a catch fence stands on `top_z`. Absent: the top is ground + `h`, as before. The physics does not read it
(the collision wall is unchanged). The app draws a tyre run's second row 0.6 m to the polyline's LEFT (unchanged); the
scenery builder now orders a tyre run so that row stands behind the line where it would otherwise reach the road.
