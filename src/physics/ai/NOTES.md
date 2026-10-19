# Race mode core (src/physics/ai) — contract and integration spec

Pure TypeScript, no DOM. Everything is reachable from the public physics API as
`import { race } from '../physics'` (namespace export added to `src/physics/index.ts`).
AI_VERSION = 7 (`field.ts`). A race is reproducible from (seed, AI_VERSION, pace.json, identity.json)
plus the player's inputs.

## Files

| file | what |
|---|---|
| `rng.ts` | mulberry32 `Rng` (next, range, normal, pick, fork), `hashSeed`, `aggressionFor(number, class)` |
| `line.ts` | `RaceLine`: centreline frame per 1 m station, racing line (ghosts.json `line.offset_m`), curvature / grade / bank, ghost speed shape (driver_a_best), hint-based allocation-free projector |
| `field.ts` | pace.json / identity.json types, `resolveCarType` (drive, engine position, engine type, redline, gears), `aiCarJson` / `buildAiSpec` (Probe car.json + identity + pace scale), `measureCarPerf`, `buildSpeedProfile`, `describeAiCar` |
| `driver.ts` | `AiDriver`: per-tick DriverInput (pure pursuit + yaw feedback + understeer FF; profile speed + PI; traffic) |
| `traffic.ts` | `Traffic`: per-step snapshot of all cars sorted by s (insertion sort, ~O(n)) |
| `race.ts` | `RaceDirector` (field, grid, formation, green, laps, order, gaps, flag, player rules, results, poses) |
| `solo.ts` | `runSolo`: one AI car alone (calibration, tests) |
| `../cars.ts` | `CarCollider`: oriented-box car-vs-car contacts (impulses, friction, push-out, impact events) |
| `tools/race/pace.ts` | race data → `public/cars/field/pace.json` |
| `tools/race/calibrate_field.ts` | fits each car's pace scale (worker_threads, ~10–20 s for 45 cars) and records the resolved spec |
| `tools/race/sim_race.ts` | headless whole-field race with timing and a result table |
| `tools/race/selfplay.ts` (+ `selfplay_metrics.ts`) | headless self-play race with racecraft metrics: line when alone, passing, defending, rules, mishaps, cost |

## Construct (src/app/modes/race.ts)

```ts
import { race, createTrackSurface, createCollisionWorld } from '../../physics';
const line = new race.RaceLine(track, ghostsJson);               // once per track
const makeSurface = () => physics.createTrackSurface(track, heightfield, { far, pitLane }); // same options as the app's surface
const director = new race.RaceDirector({
  line, surface: appSurface, makeSurface,                         // makeSurface: one Surface per car (required for determinism, see below)
  probeJson: carSpecJson,                                         // public/cars/probe_gt/car.json
  pace: paceJson,                                                 // public/cars/field/pace.json
  identity: identityJson ?? null,                                 // public/cars/field/identity.json (optional)
  pitLane: scenery?.pit_lane ?? null,                             // penalty box; null → fallback box
  collisionWorld: cw,                                             // createCollisionWorld(scenery, track), AI cars get walls too
  playerVehicle: vehicle, playerSurface: appSurface,              // the app's Vehicle (Probe, autoShift as the user set it)
}, { laps: 10, seed, playerNumber: '619', greenWindow: [5, 30] });
```
Construction measures every AI car (≈3.4 k physics steps each) and builds its speed profile: ~0.25 s for
45 cars. `RaceConfig` defaults: `formationSpeed 20`, `gridGap 15`, `aiControlEvery 2`, `aiPhysicsEvery 2`
(AI physics at 500 Hz, staggered; solo laps match 1 kHz to 0.01 s), `aiWalls true`, `playerAi false`, `maxAi ∞`.

**Surfaces:** `Surface.sample()` caches the last station per instance, so its results depend on call
history. Give the director `makeSurface`: every car and the director's own rule checks then use their
own instance and per-car outcomes do not depend on evaluation order. `playerSurface` lets the player keep
the app's surface (the app also samples it for wheelOff/HUD, which would otherwise couple the two).

## Per physics step / per frame

- Per physics step (dt = 0.001): `director.step(dt, playerInput)`. The director steps **every** vehicle
  including the player's (do not call `vehicle.step` yourself), then car-vs-car contacts, lap counting,
  flags and the rule engine. Keep the app's fixed-step accumulator; just call `director.step` instead of
  `vehicle.step`.
- Per frame: `director.hud()` (plain object, reused) and `director.poses()` (stable array):
  `{ number, isPlayer, state: VehicleState, tint, identity, engine }`. `CarRig.pose(p.state)` works
  unchanged for every car (pos, quat, wheels[].pos/steer/spinAngle, steering wheel from the wheel steer).
  `state.impact` (kind `'car'` for car contacts, else wall kinds) drives the impact sound as today.
- `director.contacts[0..contactCount-1]` (this step): `{a, b, nx, ny, x, y, closing, aApproach, bApproach, impulse, depth}`
  if the app wants sparks or per-car thumps for AI cars.
- Restart: `director.restart(newSeed)` (same field and vehicles, new grid, new hidden green moment;
  resets the player's vehicle onto its grid slot). A new `RaceDirector` also works (0.25 s).

## Race flow

- Grid: a seeded shuffle of the whole field, player included (`car.grid` is reassigned 1..n; a new seed on every
  race and restart, `?seed=` reproduces one), single file on the racing line, ~15 m bumper to bumper, the whole
  column BEHIND the start/finish line: the leader starts `greenWindow[1] × formationSpeed + 30` m (630 m) before
  it so it is still short of the line at the latest green, the tail ~1.5 km back (around T9). Race distance and
  lap 1 therefore begin at the line after the green (until 17 Oct 2026 the grid was the real start order and
  straddled the line, so the distance counter ran during the formation lap). Cars start rolling at
  min(20 m/s, 0.9 × their profile). Every grid slot and marshal reset passes the ground normal to
  `Vehicle.reset(pos, heading, speed, up)`, which pitches and rolls the body onto the slope: spawned level, cars in
  the Corkscrew slots dropped their downhill wheels and rolled over (owner, 17 Oct 2026).
- Pit-exit cones: `RaceLine.restrictLeft(pit_exit_cones.pts)` (applied by the app's `raceLine()`, the test fixture and
  tools/race/load.ts) caps `halfL` at the cone line minus 0.5 m over its span, so the lane model never sends an AI
  car left of the cones the player is black-flagged for (owner, 17 Oct 2026); the 45-car test asserts zero crossings.
- `formation`: double yellow, pace 20 m/s (followers may do +3 m/s to close gaps), no passing.
- Green at a seeded time in `greenWindow` (private `#greenAt`, never in the HUD or any public field).
- Race distance `U` is metres from the start/finish line (negative before it). Lap 1 starts at the line;
  laps = floor(U / L). `chequered` when the leader's U ≥ laps × L; results are frozen at that instant
  (metres, fractional laps). Cars that cross the line afterwards cool down at 60 % pace. `finished`
  `FINISH_GRACE_S` = 3 s after the flag (the race is over when the leader takes the last lap, owner 17 Oct 2026),
  sooner if the player crosses the line or is ejected. `hud.raced` is the player's distance since the green
  (`car.greenU`): the live counter; results and the scoreboard keep line-based U.
- `setYellow(true|false)`: full-course yellow (no passing, cap 25 m/s) — not used by the race itself.
- Stuck / wrong-way AI cars (> 4 s / 2.5 s) get a marshal reset onto the racing line at their s when the
  road behind is clear (`recoveries` counts them; ~0–3 per 45-car 3-lap race).

## HUD (`RaceHud`)

`phase` ('formation'|'green'|'yellow'|'chequered'|'finished'), `flag` ('yellow'|'green'|'chequered'|'black';
black while a stop-and-go is pending, after ejection, and for 5 s after any black flag), `time`, `lap`,
`lapsTotal`, `position`, `carsTotal`, `classPosition`, `className`, `gapAhead`/`gapBehind`
(`{number, seconds, metres}`; seconds from a per-car time-at-distance ring, 4 m bins), `lastLap`,
`bestLap`, `penalties` (`count`, `pending` [s each], `servingRemaining`, `inBox`, `lapsToServe`,
`lastReason`, `lastAt`, `ejected`), `message` (banner text, e.g. "GREEN GREEN GREEN", "BLACK FLAG: …"),
`results` (`ResultRow[]` after the flag: position, number, team, class, metres, laps, lapsCompleted,
bestLap, status 'running'|'ejected', player).

## Player rules (player only; AI cars are not penalized)

- (a) contact at fault: a car-vs-car contact with closing speed > 5 mph (`CONTACT_FAULT_CLOSING` = 2.24 m/s;
  was 1 m/s until 17 Oct 2026: taps and door-to-door rubbing are not flagged) where the player's own velocity
  toward the other car along the contact normal exceeds the other's by > 0.5 m/s. One flag per other car
  per 2 s.
- (b) four wheels off: every wheel `!onTrack` and not `paved` (Surface.sample, the app's wheelOff),
  sustained 0.25 s; re-armed after 2 s back on a paved surface (the 2 s debounce).
- (c) passing under yellow: during formation / yellow, the player moving from behind to ahead of a
  running car (on track, > 5 m/s, not recovering) within 50 m.
- Escalation: 1st warning; 2nd, 3rd 60 s stop-and-go; 4th 180 s; 5th ejected. Pending penalties queue.
  Serve: stand still (< 0.5 m/s) in the penalty box = middle 40–70 % of `pit_lane.parts[0]` (beside the
  front straight; `director.penaltyBoxSpot()` for a marker). The clock pauses if the car moves. Fast-forward: once stopped in the box with more than
  `FF_TAIL_S` = 5 s left, the director holds the car (the player's input is replaced by brake + handbrake) and
  sets `director.timeScale` = `FF_SCALE` = 10 for the app's frame loop (`HotlapLoop.timeScale`); the last 5 s run
  at 1x with the driver back in control (`penalties.fastForward` in the HUD). Not
  served within 2 laps of race distance after it was issued (or after the previous one was served) →
  ejected (result = distance so far). Without pit-lane data the box is the 250 m before the line, off the
  racing surface. `director.penalize(reason)` issues a flag from app-side rules.
- The player's DriverInput is untouched by the director (no speed limiting); ejection only marks the
  result and HUD — the app decides whether to park the car.

## Data files

- `public/cars/field/pace.json` `{ ai_version, calibrated, source, track, cars: PaceCar[] }`. Per car:
  number, team, class, grid, finish, lapsCompleted, greenLaps, `targetLap` (median green non-pit lap,
  outliers > 1.3 × median dropped), bestLap, `sigma` (1.4826 × MAD), `aggression` (0/1/2, seeded from the
  number, class-weighted), `player` (619 only), `scale` (fitted), `achievedLap`, and `resolved`
  (make, model, drive, enginePos, frontWeight, engineLayout, cylinders, turbo, redline, shiftRpm, gears,
  gearRatios, massKg, powerKw (with the power factor), stockPowerKw, gripScale, powerScale, lateralG,
  topSpeedKph, exhaustNote, probeFallback), and `stints[]`: one per real pit-to-pit stint (index, laps,
  firstLap, targetLap = median of the stint's clean laps, bestLap, sigma, scale, achievedLap; outlier rules
  in tools/race/pace.ts). A race draws ONE stint per AI car with `drawPace(car, seed)` (uniform, seeded);
  the director builds the car at that stint's scale and `restart(seed)` redraws. Never shown to the player.
  Regenerate: `npx tsx tools/race/pace.ts` (keeps fitted scales), then
  `npx tsx tools/race/calibrate_field.ts`. Bump AI_VERSION whenever driver / car construction changes; the
  director sets `calibrationStale` when pace.json is older (it then estimates scale = 121.5 s / target).
- `public/cars/field/identity.json` (other agent): joined by `number`. Missing file or row → the car is a
  Probe clone (V6, FWD, 5 speeds) with its pace scale. Read keys: make, model, year, dims.{wheelbase_m,
  length_m, width_m, height_m, track_m, mass_kg, power_kw}, engine.{layout, cylinders, displacement_l,
  aspiration, redline_rpm, stock_power_kw, exhaust_note}, optional `drive` / `gears` overrides.
- Models: if a car's model is missing, render the Probe glb tinted with `pose.tint` (or identity
  `colors.primary`). Hull boxes follow identity dimensions, so a tinted Probe may overlap by a few cm.

## Engine sound for AI cars (audio stream)

Per AI car per frame from `pose.state`: `rpm`, `throttleOut`, `gear`, `speed` (and `impact`). Per car
once from `pose.engine` (or `pace.json` `resolved`): `layout` ("I4", "I6", "V6", "V8", "flat4", "I3",
"rotary", …), `cylinders`, `redline`, `shiftRpm`, `turbo`, `exhaustNote`, `drive`. Pick the sample family
by layout/cylinders, pitch by rpm / redline; the AI shifts at `shiftRpm` (its own redline-derived point,
not the Probe ghost schedule).

## Car construction (field.ts)

Pace fit: `paceSplit(scale)` → a grip factor (tyre mu, brakes, speed sensitivity; 0.55-1.25) and a power
factor (engine torque; 1 inside that grip range, cubic outside it), so power follows the powertrain and the
fit trims grip first: heavy V8s quick on the straights and slow in corners, light turbo cars quick
everywhere. The driver's speed profile is the car's own limit; the ghost shape is only a 1.3x sanity cap.

Probe car.json → identity overrides: mass (springs, dampers, bars, bump stops, tyre rate, Fz0, brakes,
inertias scale with it), dimensions (wheelbase, track, hull box, frontal area, CG height capped so the
static rollover threshold T/2h ≥ 1.35), drive layout and weight distribution from make/model/year
(rear engine 0.40 front, mid 0.43, front transaxle 0.50, FWD 0.62, RWD 0.53, AWD 0.58; RWD gets a bit
more front roll stiffness), engine: torque shape by type (V8 flat from low rpm, I4 peaky, I6/V6 between,
turbo boost from mid rpm) × stock power (floor: 70 % of the Probe's power-to-weight — Lemons swaps),
redline, shift at 90–96 % of redline, gear count by year (3 before 1955, 4 before 1975, 6 from 2004, else 5)
with geometric ratios whose top gear reaches the shift point just above the car's computed top speed.
Then the pace scale p: tyre mu × p² (× p below 1), brakes likewise, torque × p³, lateral speed
sensitivity ref × p. Steering shaping bypassed (AI sets the road-wheel angle).

## Vehicle / physics changes made for this (smallest possible; existing tests green)

- `Vehicle`: contact hooks `cgWorld`, `pointVelocity`, `invMassAt`, `applyImpulseAt`, `nudge`,
  `reportImpact(speed, kind)`; `reset()` now clears every per-run field (bit-identical to a new Vehicle;
  test `ai_vehicle_reset.test.ts`); a NaN recovery keeps the sim clock.
- `CarSpec.drivetrain.layout` 'fwd' | 'rwd' | 'awd' and `awdFrontShare` (default 0.4; open diffs, fixed
  split). FWD keeps the original code path exactly.
- `ImpactInfo.kind` gains `'car'` (please add to CONTRACTS §4 — I may not edit it).

## Measured

- Physics cost: whole field (45 AI + player) ≈ 60 µs per 1 ms step on the M3 unloaded (≈1.3 µs per
  car, 6 % of real time) with AI physics at 500 Hz; ≈ 125 µs (2.8 µs/car, 13 %) with everything at 1 kHz.
- Calibration: all 45 cars within 0.2 % of target (2–4 evaluations each, ~10–20 s on 6 workers).
- 3-lap 45-car race (seed 1): 0–3 recoveries, max car-car penetration ~3 cm, ~20 contacts > 3 m/s.

## Racecraft (the lane model) and mishaps

Measured with `npx tsx tools/race/selfplay.ts [--laps 4] [--seed 1] [--pace file] [--mishap-rate r]` (45 cars, the
player's car AI-driven); `ai_behaviour.test.ts` asserts the key numbers on short races.

- **Line when alone.** The driver steers for its own copy of the car's profile (`driverProfile`): corners at 95 % of
  the measured lateral grip, braking at 80 % of the measured braking on the friction ellipse (the field.ts profile is
  the car's full grip; at 100 % cars slid 2-4 m wide at T2, the Corkscrew and T11). The rear-slip brake release eases
  a trailing brake when the rear slides (profile braking only). A grip limiter lifts when the last pure-pursuit
  curvature needs more than the tyres' grip at the current speed. A held shift is clamped to the road at the look
  point, so the line sweeping across the road can no longer carry a car off.
- **Pace classes.** `CLEARLY_FASTER = 0.97`: a car whose target lap (`traffic.pace`) is more than 3 % quicker than
  the car ahead's is clearly faster. Within 3 % either way = close.
- **The lane model (replaces the per-tick pass / avoid heuristics, 17 Oct 2026).** Lane coordinate e = lateral offset
  from the racing line (+ left). The director measures every car's e and its low-passed rate `ve` (`Traffic.e`, `ve`);
  each AI driver publishes the e it is heading for (`Traffic.eT`, its clamped shift target; a human player's is e + 0.5 s
  of drift). A car occupies the lateral span [min(e, eT, e + 0.6 s · ve), max(...)] ± its half width; lanes are
  `Traffic.laneW` apart (widest car + 0.6 m = 2.63 m for this field: 3-5 lanes on Laguna's 9-17 m). Occupancy of a
  lane band over a horizon T (`laneBlock`): an occupant is in my window when its rear is within my front + 1.5 m +
  0.1 s, or its front within my rear + its braking cushion (1.5 m + 0.12 s + 0.6 s of closing speed); occupants are
  projected forward at their speed, me at my planned speed. With a lane given, the lateral overlap is tested where the
  two cars will be level, both lanes clamped to the road there: the racing line runs edge to edge, so lanes measured
  from it are pinched together at turn-in, apex and exit, and a lane the road squeezes into mine is occupied.
- **Following.** Only a car whose span overlaps the band I sweep through to reach it (clearance 0.4 m, plus 10 m ×
  |curvature| up to 0.8 m in tight corners, where yawed boxes sweep wider) or overlaps my lane where I will catch it
  (both clamped to the road) is followed (time headway by aggression, braking limit as before). A car in another lane
  is never followed, so a passer in a free lane is not slowed by the cars it passes.
- **Passing.** A clearly faster car (target lap < 0.97 × the car ahead's), or one behind a car that is off / nearly
  stopped, or quicker on pace and stuck > 1-3 s, plans every 0.2 s while following within max(30 m, 0.9 s): candidates
  are the grid lanes on each side clear of the blocker's span and the one beyond (inside of the next corner first),
  never across a car I am already beside, never into a lane a car passing me (within 25 m) occupies, the band swept on
  the way free; on the road over the next 30 m; my mean radius-limited speed in it over 100 m beats the blocker's
  (its own profile scaled when it is held up) by > 0.2 m/s; free (road-aware) until I am clear ahead of it by its
  cushion (horizon ≤ 10 s + 2 s; the blocker counts only where the lanes pinch while I am not yet alongside, centres
  > 0.7 car lengths apart). Score: clear time + inside bonus − time needed. Executing: shift at 1.3 × the normal rate,
  0.5 m from the edge, a lane speed limit from the clamped lane path's own curvature (8-48 m ahead, braking envelope),
  the grip limiter on the lane's curvature, not the lane-change transient. Where the lanes pinch and I am not alongside,
  following and the pinch guard keep me behind the car (0.3 s tail) and I keep the lane. Clear of it: a slower car
  ahead in the racing lane within 60 m becomes the next target (trains in one go), else merge back when the racing lane
  is free around me (cars behind / alongside; a car ahead in it is simply followed). Abort: fallen 30 m back, lane
  blocked ahead within 1 s (another lane around it if one is free), 30 s, flag, off.
- **Being passed.** Never defends a clearly faster car (unchanged rule); holds its lane: the lane of a car passing it
  (within 25 m) is reserved in its corridor; where the road pushes the passer's lane onto it within 1 s it makes room
  (never beyond its own road); lifts to 97 % only when the passer is alongside (within 0.7 car length) and converging.
- **Contact avoidance.** Lateral by lanes; the corridor beside cars alongside (0.45 m + corner clearance; the car further
  back gives way when squeezed); the pinch guard (a car alongside in the next lane whose lane and mine close up within
  ~2 s: the one further back drops to max(½, −4 m/s) of its speed); longitudinal by following. Rejoining from off
  track: waits at the edge until the lane it rejoins into is free for 2.5 s. Marshal reset: a stopped car right behind
  no longer blocks it (two stuck cars waited for each other).
- **Light defending (within 3 % only)** and formation / yellow single file: unchanged.
- **Mishaps (loss of control).** At each corner's braking point (`RaceLine.corners`, built once per line: track.json
  corners with radius < 150 m, the Corkscrew T8/T8A merged) an AI car rolls its own seeded `Rng`:
  p = `RaceConfig.mishapRate` (default 0.0002) × corner difficulty × aggression (calm 0.6, normal 1, aggressive 1.5).
  Difficulty = κ_peak · v_entry · v_apex · (1 + 6 · downhill grade), normalised to a mean of 1 over the lap:
  T2 1.47, T8 Corkscrew 1.34, T9 1.20, T11 1.13, T5 1.02, T10 0.94, T3 0.70, T4 0.61, T6 0.59. Kinds: 70 % run wide
  (brakes late, holds 1.15-1.3 × its profile speed into the corner and aims 0.4-2.8 m past the outside edge, then a
  slow phase at 0.45 × profile; ~3-10 s lost alone, more in traffic because it waits to rejoin), 30 % spin (handbrake
  and full lock at turn-in, then all brakes to a stop; the stuck / wrong-way marshal reset ends it, ~2-5 s lost
  alone). Only during green, never the player, never with `ctl.noise` false (calibration, solo laps); no yellow. A
  spinning car is flagged `off` in the Traffic (others pass it freely). `director.mishapLog` (t, idx, number, corner,
  kind), `director.mishaps`, `car.mishaps`; nothing in the HUD.
- **Measured, lane model (4 laps, 45 cars, shuffled grid formed behind the line, seeds 1 / 2; old per-tick driver on the
  same grid in brackets):** clearly-faster pairs completed 75 % / 76 % (81 / 81) — by pace ratio < 0.85: 93 / 93 %,
  0.85-0.92: 66 / 73 %, 0.92-0.97: 49 / 50 %; median stuck 10.5 / 8.7 s (6.2 / 6.4); AI-AI contacts > 1 m/s
  0.088 / 0.023 per car-lap (0.208 / 0.111); four wheels off 0.18 / 0.10 (0.10 / 0.08); defensive moves vs clearly
  faster 0; formation passes 0; line rms alone 0.24 / 0.29 m; CPU per car-step +17 % (bench, min of 3). 45-car 3-lap
  test, seed 1: worst best lap 1.37 × target, worst average speed 0.67 (old 1.46 / 0.70). Solo laps bit-identical
  (`calibrate_field.ts --dry --only 711,143`), so no recalibration. Not reached: completion > 85 % and median stuck
  < 7 s — 3-8 %-faster cars rarely gain enough between pinches, and lap 1 from a shuffled grid jams every lane;
  contacts ≤ 0.03 on seed 2 only. The previous per-tick numbers (old grid): completion 52-78 %, contacts 0.03-0.14.
- **Recalibrate** after these changes (the driver margins make every car ~5 % slower at a given scale).

## 18 Oct 2026: painted-road track (edges-from-paint-wip): grip cap, driver margins, lane retune

The track edges were rebuilt from the painted road (median width 12.1 m, was 12.9 m with 1-4 m extra at the apexes);
the field had been tuned on the wider geometry.

- **Rollover guard** (`aiCarJson`): CG lowered so T/2h >= max(1.35, 1.15 x fitted lateral mu). Above scale ~1.14 the
  tall RWD cars (#670 Volvo 245, #41) lifted both inside wheels through T2 and tipped over: that was the old "leaves
  the road at the T2 exit" cap. It no longer binds under the mu cap below.
- **Lateral grip cap** (owner): fitted lateral tyre mu <= `MU_LAT_MAX` 1.20 (`GRIP_MAX` = sqrt(1.20 / 1.10)), clamped
  in `aiCarJson`; above it the pace comes from power (`PACE_MAX` 1.8). Resolved lateralG: #670 / #41 1.105, #544 1.049,
  #74 1.046, #83 1.025, #189 0.968, #711 0.930, #249 0.925; median 0.72.
- **Driver deficit** (the grip had been papering over it): the speed profiles ignored the road's banking and the
  crest / dip load. `bankedG` credits 85 % of the banking toward the inside of the turn ((a + b) / (1 - a b); full
  credit ran the cars ~1 m wide at Rainey, T3, T5) and `loadFactor` scales grip by 1 + v^2 x vertical curvature
  (`RaceLine.vcurv`; the Corkscrew drop unloads the car). Margins 0.97 lateral / 0.85 braking (were 0.95 / 0.80); the
  grip limiter lifts only above 1.5 x the banked grip (at 1.0 it braked mid-corner for the pursuit's own correction
  curvature). A rear-drive car sliding while the engine brakes its rear wheels gets up to 20 % throttle (the light
  turbo Corona spun off T3 on a closed throttle). AI Probe solo lap at scale 1: 123.75 -> 120.18 s (real best 119.3 s);
  minimum speeds vs driver A (km/h): T2 67/67, Corkscrew 64/63, T10 101/101, T3 81/89, T5 86/96, T6 107/116, T11 53/58 (the
  last four are where the ghost implies 1.18-1.26 g of tyre on this line, beyond the Probe's 1.05 g).
- **Calibration** (8 workers): worst error 0.54 %; #670's 113.4-114.4 s stints reached at scale 1.18-1.21, #41's
  116.9-117.7 s at 1.14-1.16; a solo check of all 311 car / stint scales has no recovery and no sustained 3-wheels-off.
- **Lane model**: corridor beside a car alongside `ALONG_CLR` 0.45 -> 0.70 m (yawed cars side by side touched at
  0.1-0.4 m in T3, T9, T10); the merge back to the racing line checks the lane `MERGE_AHEAD` 60 m ahead (was front +
  7 m + 0.2 s: merges closing at 9-14 m/s rear-ended a slower car 20 m up the road); merging back (phase 3) keeps the
  full grip limiter (corner-exit merges carried cars off); no passing in the Corkscrew (`noPassZone`: 120 m before its
  braking point to 90 m past the apex; a pass still behind its car is given up, the merge is forced from the braking
  point). Alone driving is unchanged by these (solo laps identical).
- **Self-play band re-based to this geometry** (`selfplay.ts`, 4 laps, seeds 1-4; the earlier band, line rms
  0.25-0.29, clearly-faster passes 72-77 %, stuck ~10.5 s, contacts 0.012-0.038, recoveries 7-10, belonged to the
  over-wide geometry and the old driver): line rms alone 0.28-0.32 m; clearly-faster passes 65-75 % (68.8 % pooled);
  median stuck 11-15 s (12.5 mean); AI-AI contacts > 1 m/s 0.033-0.063 per car-lap (0.044 mean); four wheels off
  0.08-0.17 per car-lap; recoveries 1-3 per race; mishaps 0-1 per race (all run-wide), so recoveries are traffic
  stuck / wrong-way resets. About 70 % of the time a clearly faster car spends within 20 m of its target it is already
  in its pass lane, held behind where the lanes pinch or level on pace: with lateral grip capped, quick cars gain on
  the straights, not in the corners.
- Tests: corner-difficulty top three re-based to T11, T2, Corkscrew (pure geometry); the "clearly faster car behind"
  test picks the first seed whose grid puts T2 right behind T1 (the grid hash includes AI_VERSION). Still failing:
  `ai_race` 45 cars, seed 1: #670 (1:53.4 stint, starts P42) averages 0.640 of its pace against the 0.65 bound,
  traffic-bound (146 s of 447 s in its pass lane held behind the car it is passing, 91 s following clearly slower
  cars with no free lane). Not loosened.
- `tools/ghosts/build_ghosts.py`: optional `--kerb-margin`, `--jerk-w`, `--debug-out` (default output byte-identical).
  Kerb-aware bounds (0.75 / 0.5 / 0.3 m from the edge along the kerb strips) gain <= 0.07 s on the Probe lap; only T5
  opens (R 52 -> 56 m), so ghosts.json is unchanged.

## 19 Oct 2026: understeer unwind (AI_VERSION 8), self-play band re-based on 16 seeds

After the spline-fitted edges, 2 self-play seeds read 0.08 contacts per car-lap. On more seeds the edges were not the
cause: seeds 1-8 at ab4b15d (pre-edge) 0.051, at the fitted edges 0.058 (16 seeds 0.056); the 4-seed band above
(0.044 mean) was a lucky draw. Seed-to-seed spread is 0.01-0.11, so compare driver changes on 16 seeds (~3 min on 8 cores).

- **Cause** (per-contact traces, 2.5 s of both cars): about half the contacts involve a car 4-9 m off the line and slow,
  steering back across a car arriving or alongside. Those cars had ploughed: making room for a passer or changing lanes
  at turn-in, the front slid to 0.3-0.67 rad (tyre peak 0.12) at full lock, the car ran wide, then bit all at once as it
  slowed and was thrown back across the road (or spun: #143 seed 2, Rainey exit, rear slip to 1.5 rad).
- **Change**: an understeering car at speed (front slip > `STEER_PLOUGH` 2 x the tyre peak and above the rear's,
  > 10 m/s, on track) stops adding lock and unwinds it at 2/s; the cap recovers at 2/s once the front grips
  (`CarPerf.peakSlipAngle`). Applied regardless of phase (limited to understeer: a plain cap trapped low-speed and
  oversteering cars, 110-180 recoveries per 8 races).
- **Tried and dropped** (16 seeds, no gain or worse): pass lane changes limited by the spare lateral grip (0.045),
  a car far off the line treated as a merge back that waits for a free lane (0.072 on 8 seeds), threshold braking at
  a lock-up instead of the 3/s cap cut (0.043-0.045).
- **Calibration**: solo laps change for 26 of 311 car / stints (all faster; #700 by 3 s, it ploughed solo), so
  AI_VERSION 8 and pace.json recalibrated: AI Probe at scale 1 laps 120.20 s; worst error 0.19 % (#49 stint 7 needed a
  second `--only 49` run from the warm start).
- **Self-play band re-based** (`selfplay.ts`, 4 laps, seeds 1-16, AI_VERSION 8): line rms alone 0.24-0.33 m;
  clearly-faster passes 69.1 % pooled (64-70 %), median stuck 12.5 s mean; AI-AI contacts > 1 m/s 0.038 per car-lap
  pooled (0.012-0.085 per seed; was 0.056); four wheels off non-mishap 0.087 (was 0.116); recoveries 58 and mishaps 6
  over the 16 races. Seeds 1-4 alone: contacts 0.027.
- Tests: 321/321; `ai_race` 45 cars seed 1 now passes (the grid hash changes with AI_VERSION), not loosened.

## Assumptions and data wishes

- Target pace is the median green lap (traffic included), so AI cars run their real race pace, slower
  than their best laps; the player's real best (1:59.3) beats #619's own median (2:08.7).
- Pace differences are modelled as car capability (power, grip), not driver skill; every AI drives at the
  same fraction of its own grip.
- The shuffled grid mixes very slow cars in front (a 2:51 car can draw P1): the first laps are busy, like the
  real race, and different every time.
- Wishes: real per-car mass and power as raced (swaps), tyre class per car, real pit-lane penalty box
  position, a full-course-yellow log (the announcements file) to replay real yellows.
