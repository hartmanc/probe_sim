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
  The statistic is a parameter (AI round 1, 27 Oct 2026): `targetLap` (car and stint) is the quantile `q` of the clean
  laps (`--quantile <q>` on pace.ts, pace_track.ts, pace_sonoma.ts; default 0.5 = the median, every public file so far;
  recorded in the header as `pace: { stat: "quantile", q }`; outlier cuts still reference the median). Why: a race
  stint's median already carries the real race's traffic and the sim adds its own, so the field ran slow (owner: "They
  don't seem very fast, and I have no problem passing them."). `calibrate_field.ts --pace <file>` calibrates a
  candidate file (tools/race/out/pace_q/<q>/<track>/pace.json) without touching the public one.
  **The rule (AI round 1, 27 Oct 2026): q stays 0.5 on all four tracks** (the public files' targets and fits unchanged). The
  gate (Laguna, 5 laps, whole field, shuffled grid, the AI Probe at scale 1 = 120.2 s, seeds 1-8; pick the largest q whose
  mean finish is P5-7, the real result) passed no candidate: mean finish q 0.5 P18.5, 0.35 P22.75, 0.25 P22.1, 0.15 P20.6
  (per seed in "27 Oct 2026: round 1"). The finish follows the shuffled grid (the player starts P29 on average over those
  seeds), not the pace; the owner's call (orchestrator) was to keep 0.5 and report a grid-free pace position instead.
- `cars[].curve` (AI round 1): the car's solo lap against its pace scale, [scale, lap] pairs by rising scale with the lap
  falling, from every calibration of the car (its fit and its stints' at q 0.5 / 0.35 / 0.25 / 0.15), made monotone
  (pool-adjacent-violators in ln-ln), thinned to 1 % apart: `npx tsx tools/race/pace_curve.ts --track <id>` (reads
  tools/race/out/pace_q/<q>/<track>/pace.json; writes only `curve`). The AI strength setting (field.ts `strengthPace`)
  reads it. Regenerate after any recalibration.
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
  blocked ahead within 1 s (another lane around it if one is free), 30 s, flag, off; the road shutting the lane beside it
  before I am ahead, and a pass is not started in such a lane (24 Oct 2026, below).
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

## 20 Oct 2026: self-play with kerbs (re-based bands), Sonoma lane changes within the grip

- **Self-play surface fixed** (`tools/race/load.ts` `makeSurface`): selfplay / selfplay_trace / sim_race gave every car a
  pit-lane-only surface, so self-play never saw Laguna's sausages or Sonoma's 5 cm kerb profile. The pack now builds its
  surfaces with the app's options (`surfaceFactory`: pit lane + paved zones, far terrain, sausages, kerbs);
  `selfplay --no-kerbs` keeps the old surface for comparison. Solo laps (calibration) unchanged.
- **Laguna band re-based (measurement change, 16 seeds, 4 laps, AI_VERSION 8)**: without kerbs contacts 0.038 per car-lap,
  four-off 0.090 (non-mishap 0.087), clearly-faster passes 69.1 %, line rms 0.29 (the 19 Oct band, reproduced); with
  kerbs **0.036, 0.090 (0.088), 69.2 %, 0.29**, recoveries 55, mishaps 6 (per seed contacts 0.012-0.075).
- **Sonoma baseline with kerbs** (seeds 1-8): contacts 0.042, four-off 0.097, passes 73.6 %, rms 0.37 (without kerbs
  0.047 / 0.119 / 71.9 %); seeds 1-16: 0.047 / 0.094 / 73.0 %.
- **Clusters (traces, seeds 1-8)**: 19 of 54 contacts involve a spinning car, 50 of 123 four-offs are spins, mostly
  in the esses s 2400-2800 (T8a-T9) and RWD cars (#76 Fiero, #200 86, #0, #55, #43). Mechanism: a room-making / corridor
  push (2 x SHIFT_RATE) or a pass lane change at 20-25 m/s asks 3-5 x the line's curvature; the car slides, the grip
  limiter brakes on the pursuit's counter-steer curvature with the rear sliding, the car spins (also with shift 0 after
  a slide). The rest: inside passes into T4 (s 990-1000) and T11 (s 3610-3660), where the road takes the inside lane away
  at the apex and the passer, clamped onto the line, runs 1-2 m wide into the car making room (closing 1-3 m/s); 9a rear-ends.
- **Changes (per track, `TRACKS[id].ai`, Laguna's arithmetic unchanged, seeds bit-identical)**: `shiftGrip` (RaceConfig,
  0 = off): the lane-shift rate is capped at shiftGrip x a_spare x Ld / v (>= 0.8 m/s), a_spare = lateral grip minus the
  line's v^2 k; Sonoma 1. `laneMargin` (1 = Laguna): a pass lane's own path speed at that share of the corner margin;
  Sonoma 0.85. **Sonoma, 16 seeds**: contacts 0.047 -> 0.033 (shiftGrip) -> 0.025 (+ laneMargin), four-off 0.094 ->
  0.031 -> 0.019, passes 73.0 -> 73.7 -> 73.5 %, rms 0.36; **seeds 1-8: 0.024 / 0.017 / 72.7 % / 0.36** (target contacts
  <= 0.02 not reached). Remaining contacts: T4 entry 10, T11 entry 9, T7 7-10, straights 9.
- **Shared trials (not kept)**: shiftGrip on Laguna (16 seeds): contacts 0.035, four-off 0.020, passes 71.4 %, recoveries
  13 (from 55), but total green passes -11 % and `ai_behaviour` "full field, 2 laps" fails (passesTotal 140, needs > 150;
  not loosened); exempting pass lane changes from the cap passes that test but gives back the gain (Sonoma 0.039 / 0.046,
  Laguna 0.043 / 0.076). laneMargin 0.85 on Laguna: contacts 0.036 (no gain). On Sonoma, no gain beyond noise: throttle
  cut on rear slide for RWD, brake easing under the grip limiter (0.045 / 0.090), shift rate x min(1, 15/v) (0.030 /
  0.057 alone, 0.044 with shiftGrip), the follow check scanning the lane pinch on the way (0.039), extra room for a
  passer (0.6 / 1.2 m: 0.035 / 0.038). 8-seed spread is +-0.006 contacts: compare on 16.
- No AI_VERSION bump: Laguna solo laps are bit-identical; on Sonoma shiftGrip changes one checked solo lap by 0.008 s
  (#200 stint scale 0.8), far inside the 0.2 % calibration tolerance (as the 18 Oct lane retune, no recalibration).
- The app passes `followScale` only (`src/app/modes/race.ts`): `laneMargin` and `shiftGrip` must be passed from
  `TRACK.ai` there too for the app's Sonoma race to use them.

## Assumptions and data wishes

- Target pace is the median green lap (traffic included), so AI cars run their real race pace, slower
  than their best laps; the player's real best (1:59.3) beats #619's own median (2:08.7).
- Pace differences are modelled as car capability (power, grip), not driver skill; every AI drives at the
  same fraction of its own grip.
- The shuffled grid mixes very slow cars in front (a 2:51 car can draw P1): the first laps are busy, like the
  real race, and different every time.
- Wishes: real per-car mass and power as raced (swaps), tyre class per car, real pit-lane penalty box
  position, a full-course-yellow log (the announcements file) to replay real yellows.

## 24 Oct 2026: merged tree, own fields (Sonoma 134 cars, Buttonwillow 100): contacts by place, Buttonwillow knobs

Details, tables and the rerun command lines: `tools/race/AI_READINESS.md`.

- **Buttonwillow** `TRACKS.buttonwillow.ai = { followScale: 1.4, laneMargin: 0.7, shiftGrip: 1 }` (seeds 1-3, 4 laps):
  contacts 0.058 -> 0.020 per car-lap, four-off 0.185 -> 0.033, race time -0.4 %, median best lap / target +5.6 %.
- **Sonoma** knobs unchanged: 39 of 70 contacts (two seeds) are at T7 brake (s 2068-2081), where tyre run #9's oblique end
  segments put `vehicle.ts collide()`'s through-the-wall band (hull point beyond the segment's line within its span, far
  side from the CG) on the racing line: cars on the line are stopped or launched by a wall they never touch
  (`tools/race/wall_phantoms.ts`; none on Laguna or Buttonwillow). Not fixable by knobs; physics or scenery, the owner's
  call. Outside T7, laneMargin 0.7 halves the contacts: the first trial for the round-14B rerun.
- No shared code changed, no AI_VERSION bump; Laguna seed 1 bit-identical (contacts, four-offs, finishing order).

## 24 Oct 2026: a pass needs its lane through the corner (branch `ai-passing`)

Owner: no no-pass zone at Sonoma's T9A chicane ("cars pass each other at the chicane all the time"); fix the shared pass
logic. Diagnosis, traces and tables: `tools/race/AI_READINESS.md` section 6.

Mechanism (Sonoma T9A, T11 and T2 entries; Laguna's T4 and T11 exits the mirror case): the racing line runs to the inside
edge at an apex (and to the outside edge at the track-out), so a lane measured from it on that side is clamped onto the line
over 10-15 m. A car held in such a lane (a pass in hand, or a pass given up and waiting to merge back) while overlapping the
car on the line is steered into it by the road; the car on the line cannot make 2-3 m of room at the limit in time.

Changes (`driver.ts`, shared by every track, no station lists, no track names, no new knob):
- **Pinch guard in lane coordinates.** Its "straight ahead: following handles it" skip and its side test compared the two
  cars' absolute lateral offsets from the centre line. A few metres apart in a corner these differ by the line's sweep across
  the road (2-3 m in T9A), so a car one lane over read as straight ahead while following, in lane coordinates, saw it in
  another lane: neither held the car back. Both now use the lane coordinate e, as following does.
- **Pinch guard sampled every 5 m** (was 10 m) over its look-ahead (`PINCH_T` = 2 s, unchanged): a 10-15 m shut could be
  stepped over.
- **`shutBeside` (a pass needs its lane through the corner).** The first station within max(12 m, PINCH_T s) where my pass
  lane and the passed car's lane, both clamped to the road, come closer than the pinch guard's clearance; r = where I am
  relative to that car when I get there at the closing speed. A pass in hand is given up (`passEnd` 'shut', then the
  usual phase 2: the pinch guard, no longer exempting that car, drops me behind it, and the merge waits for a free lane)
  when r is neither PINCH_OK car lengths ahead of it nor still behind it. Planning (`planLane`) does not start a pass in a
  lane that the road shuts before I would be ahead of it by PINCH_OK car lengths. Horizon: my speed x the occupancy
  horizon Tn = min(PLAN_T, D / adv) (the whole pass when it takes up to PLAN_T = 10 s, its first 10 s otherwise), never
  less than the pass-in-hand look-ahead, at most PLAN_SHUT_MAX = 150 m; closing at the planned advantage or the speed
  difference now if larger. (Checking long passes to their end instead: Sonoma contacts 0.022 -> 0.031, Laguna 0.033 ->
  0.038 over 8 seeds, Sonoma green passes -6 %: not kept.) A lane that will be shut before I am ahead is no lane
  (also when I would still be behind there: pulling out into the outside lane at an apex that the track-out takes away
  put cars off Laguna's T4 exit).
- Lanes in `shutBeside`: mine clamped as a pass lane is held (`laneAt`, PASS_EDGE from the edge, as the lateral target
  in a pass), the passed car's with the 0.15 m road margin a car off a pass is held at: each where that car will be (the
  pinch guard clamps both with the 0.15 m margin). The closing speed is floored at 0: a passer falling back is projected
  where it is now, so a pass losing ground is given up rather than kept on the hope of being behind by the shut.
- The Corkscrew no-pass is unchanged.

Not kept: a 3 s pinch / pass look-ahead (Sonoma contacts 0.016 per car-lap, Laguna 0.018 / four-off 0.072 over 8 seeds)
fails `ai_behaviour` "full field, 2 laps" (clearly faster completed 51 %, needs > 58 %; > 15 % quicker 63 %, needs > 72 %)
and "within 3 %" (no defending move); 3 s only for a car in phase 2 still fails the full-field case (57 %); the planning
check that let a pass start when I would still be behind at the shut raised Laguna's four-offs 0.093 -> 0.110 (8 seeds).

Solo laps (`tools/race/out/solo_check.ts`, local: 4 cars per track at their fitted scales, 2 laps) are bit-identical to
152d422 on Laguna, Sonoma and Buttonwillow: the changes act only with another car in reach. **No AI_VERSION bump** (8), the
calibrations stand.

## 26 Oct 2026: AI robustness (branch `ai-robust`, after the determinism round)

With the physics and the AI on one arithmetic (`dmath`, the server's), two seeded tests failed on every host. Both now
pass, fixed as driver logic; no test, threshold or physics changed, no AI_VERSION bump (solo calibration laps move by at
most 0.19 %, inside the calibration tolerance). Tools: `tools/race/cone_trace.ts` (replays the 45-car test race or any
self-play and prints each pit-exit cone crossing / spin with the driver's state; `--detail` per-wheel slips), and
self-play now reports (r) cone crossings (in control or not) and spins (heading > 1.3 rad off) without a mishap.

**Diagnoses (traces, `ai_race` seed 1 and self-play seeds 1-3).**
- #49 (Triumph Mayflower, RWD) on Laguna's front straight: pushed 1.8 m right by a car alongside while the racing line
  sweeps 4.8 m left toward the pit-exit cones (s 150-240), at 32-34 m/s the driven rear right wheel ran at combined
  slip 1.3-1.8 on full throttle; the rear let go (rear slip 0.09 -> 0.45 rad in 1 s). Pure pursuit aims the nose, so
  with the nose 0.2-0.5 rad left of the direction of travel it kept steering left (into the rotation), the grip
  limiter braked at 0.25-0.3 for the pursuit's curvature (the rotation, not the path), and by the time the target
  swung to the right of the nose the car was beyond what 10 degrees of speed-shaped lock can catch. No mishap is
  counted because mishaps are only the seeded ones: this was an unplanned spin. The same mechanism (rear past its peak
  under trail braking or the grip limiter's braking, steering not opposing the rotation) made the other spins without a
  mishap at T4, T6 and T10 (16 in seeds 1-3 at Laguna).
- #37: a pass lane 5.3 m left planned at s 147 where the cap allowed it; the line then sweeps toward the cap, the
  shift clamp at the look point shut the lane abruptly while the car moved left at 6 m/s absolute, and it overshot by
  2.2 m. At the cap the driver counted itself off track (`outside` used the capped edge), which dropped the clamp and
  started a slow rejoin from where it was. A pass lane runs into the cap because the clamp looked only 10 m ahead.
- Passes (`ai_behaviour` full field, 2 laps): not a pass-logic weakness. Seeds 1-6, this test's measure:

| code | passes per seed (1-6) | mean |
|---|---|---|
| release-040 on this Mac's FMA-contracted maths | 168, 165, 158, 102, 203, 235 | 171.8 |
| determinism (the server's maths) | 140, 146, 186, 112, 215, 213 | 168.7 |
| this round | 168, 142, 160, 148, 166, 229 | 168.8 |

  Seed 1's 140 was one draw of a chaotic race (seeds 2 and 4 are under 150 under every arithmetic). The check that also
  failed under the new code, "no defending against a clearly faster car", was real: a defender skipped a clearly faster
  car rejoining 5 m behind it and covered the inside against the within-3 % car behind that (fixed below; 0 on all six
  seeds now, release-040 had 2 and 1 on seeds 2 and 6).

**Fixes (`driver.ts`, `line.ts`).**
- A slide = rear slip past 1.5 x the tyre's peak and over the front's by half a peak, and the car rotating faster than
  its direction of travel turns (yaw rate - a_lat / v, same sign, > 0.15 rad/s). Then the front wheels are never
  steered into the rotation past their own direction of travel (road angle + ISO slip angle); the brake comes off (at
  most 0.1, except when following a car ahead); a driven rear gets at most 0.15 throttle, a front-drive car at least
  0.15. The rear-slide brake easing (REAR_SLIP) also applies under the grip limiter.
- Off the road = off the pavement (`RaceLine.halfLRoad`): the cone cap is a lane boundary. A cap ahead
  (`RaceLine.capL`) bounds the shift, in lane coordinates, by an approach at 3 m/s^2 laterally over 100 m.
- Defending: a clearly faster car rejoining right behind is not skipped.
- A pass given up merges once the road has put the car back on the line (in phase 2 it followed the car ahead at
  headway, which the lane check reads as occupied, and steered back out past the apex; `ai_passing` "drops back").
- Tried and dropped: a symmetric front-slip band (fronts within 1.2 x peak of their travel direction) slowed solo laps
  by up to 2.4 %; traction on the combined slip of a driven wheel moved solo laps 0.5-1.4 %; counter-steering at
  0.5 x peak against the rotation cost one Buttonwillow car 5 % solo (it bound in normal limit driving).

**Issue #19.** `NO_PASS_CORNERS = { laguna_seca: ['T8'] }` keyed by `RaceLine.trackId` and `LineCorner.turn`. Laguna
seed 1 and Sonoma seed 1 self-play are identical (every metric); Sonoma never had a T8 on the line (merged into T7a).
Buttonwillow's T8 opens: "corkscrew" pass ends 36 / 43 / 45 -> 0 (seeds 1-3), pass attempts 1041 / 1058 / 1009 ->
1107 / 1122 / 1055, green passes 305 / 340 / 336 -> 313 / 365 / 318, passes in T8's old zone (s 2580-2864) 9 / 29 / 15
-> 17 / 15 / 6 (the race diverges from the first T8 passage, so the per-zone counts are one draw each), contacts
0.021 -> 0.009 per car-lap pooled.

**Bands (self-play, `selfplay.ts`; baseline = determinism fa342f6, same arithmetic; Buttonwillow also against #19 alone).**
Pooled per car-lap (per-seed tables in the round's hand-back):

| track (laps, seeds) | run | contacts (max seed) | four-off | passes / car-lap | in-control cone crossings | spins without a mishap |
|---|---|---|---|---|---|---|
| Laguna (4, 1-6) | baseline | 0.041 (0.054) | 0.093 | 1.76 | 7 | 34 |
| Laguna (4, 1-6) | this round | 0.018 (0.026) | 0.071 | 1.72 | 0 | 9 |
| Sonoma (2, 1-12) | baseline | 0.028 (0.052) | 0.016 | 2.98 | 0 | 28 |
| Sonoma (2, 1-12) | this round | 0.030 (0.062) | 0.008 | 3.04 | 0 | 9 |
| Buttonwillow (2, 1-3) | baseline / #19 only | 0.021 / 0.009 (0.024 / 0.020) | 0.030 / 0.022 | 2.10 / 2.16 | 0 | 6 / 6 |
| Buttonwillow (2, 1-3) | this round | 0.017 (0.026) | 0.013 | 2.17 | 0 | 0 |

Median best lap / drawn target per seed stays in the baseline's spread (Laguna 1.10-1.16 vs 1.10-1.14, Sonoma
1.18-1.29 vs 1.19-1.36, Buttonwillow 1.25-1.33 vs 1.23-1.34); line rms alone unchanged (0.25-0.40 m). Open: one Sonoma
seed (7: 0.062) and one Buttonwillow seed (3: 0.026, one contact) sit above the baseline's worst seed although the pooled
rates are flat or lower, and 9 + 9 unplanned spins remain (all from deeper slides at T4 / T10 Laguna, T2 / T10 Sonoma).

## 27 Oct 2026: round 1 (branch `ai-round-1`): pace anchor, AI strength, the player's pace, racecraft against the player

Owner: "they often don't follow the line. They don't seem very fast, and I have no problem passing them." Stage 1 (Sonnet)
made the pace statistic a quantile and calibrated q 0.35 / 0.25 / 0.15 candidates (tools/race/out/pace_q/).

- **Part A, the anchor: q stays 0.5.** Gate: Laguna, 5 laps, whole field, shuffled grid, the AI-driven Probe at scale 1
  (`selfplay.ts --player-scale 1`, 120.2 s solo = the owner's real best 119.3), seeds 1-8, the largest q with a mean finish
  in P5-7 (the real result). Finishes per seed 1-8: q 0.5: 9, 29, 11, 23, 30, 28, 15, 3 (mean 18.5); q 0.35: 13, 27, 12,
  31, 40, 34, 14, 11 (22.75); q 0.25: 17, 31, 7, 28, 38, 34, 18, 4 (22.1); q 0.15: 14, 30, 12, 23, 32, 32, 17, 5 (20.6). No
  candidate passes; the player's grid slots on those seeds are P24, 38, 22, 33, 43, 45, 20, 7 (mean 29): five laps from a
  shuffled grid measure the grid, not the pace. At q 0.5 the quicker player does not finish better either: scale 1.05 mean
  P18.4 (10, 26, 13, 23, 38, 24, 11, 2), scale 1.10 P18.25 (12, 28, 14, 18, 27, 30, 16, 1). Kept 0.5 (orchestrator); a
  grid-free report measure, the player's pace position (1 + AI cars with a quicker mean / best lap over the race's completed
  laps), is in the self-play JSON (`playerPace`).
- **Part A.4:** a stint whose fit did not converge (|achieved / target - 1| > 0.5 %, a car at the caps) races with its
  achievable lap as `Traffic.pace` (field.ts `paceHint`); the slower-car test reads the car's own hint.
- **Part B, AI strength** (Start menu, under Race; the row was removed on the owner's call, 29 Oct 2026: the race build is at 100 % unless a caller passes `strengthPct`; `--strength` stays a tool switch, `RaceConfig.strengthPct`, `strengthPace` and the identity test at 105 % stay; stored like Graphics, `probeSim.aiStrength.v1`; read at each race build;
  shown in the formation toast, results, standings and pause menu; `raceBoardVersion` adds `-S<pct>` off 100 %):
  `RaceConfig.strength`, every AI car built at field.ts `strengthPace(curve, ...)`: the scale at which its curve laps target /
  strength, anchored on the stint's own point; 100 % bit for bit; hint, sigma and so the classes and mishaps follow; never the
  player. 110 % is a calibrated point of every stint (`tools/race/pace_target_scale.ts --strength 1.1` writes a copy with
  every target / 1.10, `calibrate_field.ts --pace` that copy, `pace_curve.ts` folds it in; 28 Oct 2026: worst fit error
  2.1 / 10.9 / 5.8 / 7.6 % Laguna / Sonoma / Buttonwillow / Mid-Ohio, those are cars at the caps). Solo check, 6 cars per
  track spread over the field (`tools/race/strength_check.ts`), worst error not at the caps: 105 % 0.24 / 0.29 / 0.72 / 0.92
  %, 110 % 0.20 / 0.17 / 1.88 (#562, scale 1.79, power-capped) / 0.11 %; at PACE_MAX: Sonoma #747 (128.1 s for 119.6 s),
  Mid-Ohio #372 (102.7 s for 98.0 s). Held at PACE_MAX at 110 % (car-level / stints): Laguna 0 / 0, Sonoma 11 / 147,
  Buttonwillow 0 / 14, Mid-Ohio 4 / 37; at 105 %: 0 / 0, 1 / 16, 0 / 1, 0 / 0. Choices 100 / 105 / 110 %; below 100 % the
  curves have no calibrated point (95 % missed by up to 4.5 %, 90 % by 8.2 % before the 110 % calibration): not offered.
  Regenerating a pace file (pace.ts, pace_track.ts) drops `curve`: re-run pace_curve.ts after the calibration.
- **Part C, the player's pace** (`playerPaceEstimate`, race.ts): starts at the pace row's best lap (Laguna 119.3 s), without
  a row at `TRACKS[id].probeRefLap` (the AI Probe at scale 1: 120.2 / 143.4 / 156.01 / 118.55 s); after each completed green
  lap the median of his last three laps not interrupted by an off (four wheels off the paved surface 0.25 s), a penalty (a
  black flag or a stop-and-go in it) or a contact at fault, within 0.9-1.3 x the start. `Traffic.pace[player]` reads it; the
  AI-driven player keeps its drawn pace.
- **Part D, racecraft against a close car: tried and dropped (driver.ts is the A-C tree).** Tried, shared by every track:
  (D.1) defend from the braking point of a passable corner when a car within 3 % is within 0.6 / 0.8 / 1.0 s (by aggression)
  and not falling back, covering up to one lane toward the inside, held to the apex, one move per corner; (D.2) the 97 %
  lift only for a clearly faster passer; (D.3) a car within 3 % and quicker on the day (its speed above the car ahead's for
  2 s) plans a pass. With all three, 4 laps, seeds 1-8 (main fd8a8d7 -> D): contacts Laguna 0.027 -> 0.034, Sonoma 0.028 ->
  0.027, Buttonwillow 0.015 -> 0.017, Mid-Ohio 0.028 -> 0.016; clearly-faster completed Buttonwillow 63.7 -> 63.1 %; and the
  player pass cost (`--player-scale 1.05`, 5 laps) moved the wrong way on every track (AI cars passed per race Laguna 12.9 ->
  14.5, Sonoma 11.1 -> 14.2, Buttonwillow 9.4 -> 11.8, Mid-Ohio 7.2 -> 9.5): in self-play the player is AI-driven, so D.3
  helped him pass as much as D.1 hindered him. D.3 dropped; D.1 alone then fails `ai_behaviour` "full field, 2 laps"
  (clearly faster completed 56 %, needs > 58 %), D.2 alone fails its "no defending against a clearly faster car" (1, needs
  0), both 53 %: not loosened, so Part D is out. Self-play keeps the split pass cost (cars within 3 % of the player's pace
  / others) and the defensive moves made against the player as report measures.
- **Bands, 4 laps, seeds 1-8 (main fd8a8d7 / this branch without Part D / with Part D):** contacts per car-lap Laguna 0.027 /
  0.027 / 0.034, Sonoma 0.028 / 0.028 / 0.027, Buttonwillow 0.015 / 0.015 / 0.017, Mid-Ohio 0.028 / 0.028 / 0.016; four-off
  0.094 / 0.094 / 0.076, 0.011 / 0.011 / 0.010, 0.009 / 0.005 / 0.008, 0.072 / 0.072 / 0.073; clearly-faster completed 69.3 /
  69.3 / 70.3, 59.2 / 59.2 / 59.2, 63.7 / 65.2 / 63.1, 62.7 / 62.7 / 62.3 %. Parts A-C leave the bands where main has them
  (Buttonwillow moves through the A.4 hint of its capped cars). Laguna's 0.018 band (seeds 1-6, 26 Oct) reads 0.027 on seeds 1-8
  on main itself.
- **Mid-Ohio knobs** (`TRACKS.mid_ohio.ai`, seeds 1-4, 4 laps, from none): contacts 0.029 -> 0.012 per car-lap, four-off 0.073
  -> 0.012, clearly-faster completed 61.3 -> 73.1 %: `followScale 1.8, laneMargin 0.85, shiftGrip 1` (trials in AI_READINESS 7).
- **The player's pace position (report):** Laguna q 0.5, 5 laps, seeds 1-8, by mean lap / by best lap: Probe scale 1.0 P14.6 /
  P13.5, 1.05 P14.5 / P16.1, 1.10 P15.5 / P14.1 (his mean lap 153.5-154.8 s against 120.2 s solo): in five laps from a
  shuffled grid the player's own laps are traffic-bound too, so neither finish nor pace position separates the scales.
- No AI_VERSION bump: the solo path is unchanged (calibrate `--dry` on 4 cars per track: Laguna and Mid-Ohio identical, the rest
  refit within 0.25 s).

## Traffic round (28 Oct 2026, branch `traffic-1`): matching the MyLaps passing data

Owner: "realistically represent the Lemons field ... match data instead of going off my vibes." The yardstick is the 2026 MyLaps
crossings of the four races (57 017 usable pairs, `tools/race/data/traffic/REPORT.md`, `curves.json`): a pair = attacker X
crossing the line with Y on the road ahead within 10 s; outcome at X's next crossing; d = pace delta of the two stint refs
(quantile 0.2), g = gap at the line.

**Stage 0, the yardstick in the sim.** `RaceDirector.crossings` logs every line crossing (player included; `green` = the lap
was raced under green, a cool-down lap after the flag is not; `pit` = the player in the penalty box on that lap; pushed in the
crossing branch, no per-step cost). `tools/race/traffic_sim.ts` runs self-play races (as selfplay.ts, the player AI-driven)
in worker processes, one stint per car = the whole race, ref = quantile 0.2 of its usable laps by `traffic_curves.ts`'s own
rules (lap 1 excluded), pools, and compares cell for cell with `curves.json` (`--compare`), plus contacts, four-off, green
passes per track. The data's laps are 120-190 s, the four tracks' sim laps 120-200 s: the seconds compare without scaling.
`tools/race/solo_hash.ts` hashes the solo laps of 3 cars per track (gate G5); `selfplay_trace.ts --loss` splits every AI
car's time over its own profile into free / following / passing / merging / off by pace quartile, corner phase, pass phase
and speed limiter (and, with it, why pass-lane candidates are rejected).

**Baseline** (round-1 code 27e81ce, 10 laps, seeds 1-8, all four tracks; `tools/race/out/traffic/baseline.{json,md}`),
pooled, g < 2 s:

| d | data | sim (n) |
|---|---|---|
| Y faster (floor) | 8.2 % | 17.2 % (8446) |
| 0-1 % | 39.4 | 35.5 (2391) |
| 1-3 % | 60.3 | 58.2 (3014) |
| 3-8 % | 86.9 | 74.7 (3026) |
| 8-15 % | 97.8 | 87.3 (890) |
| > 15 % | 99.7 | 94.2 (379) |

Gap curve (d >= 3 %), data / sim: 0-0.5 s 96 / 87, 0.5-1 91 / 80, 1-2 88 / 66, 2-3 88 / 60, 3-5 84 / 53, 5-8 77 / 57, 8-10 62 /
38 %. Attacker's time lost per lap (g < 2 s), data / sim: stuck 2.5 / 2.8, 4.3 / 6.0, 8.4 / 11.5, 17.7 / 19.7 s (d 0-1, 1-3,
3-8, 8-15 %); on the lap of the pass 1.9 / 4.0, 2.1 / 3.3, 2.9 / 5.7, 3.4 / 11.5 s. Per track (byD Yfaster..>15, sim / data):
Laguna 18 35 42 62 85 97 / 7 37 52 82 98 100; Sonoma 25 46 61 74 84 93 / 9 43 60 87 97 100; Buttonwillow 15 38 59 74 88 92 / 9
37 60 83 98 100; Mid-Ohio 8 24 57 81 95 90 / 7 37 62 90 99 100. Rules, seeds 1-8 per car-lap: contacts Laguna 0.0248, Sonoma
0.0297, Buttonwillow 0.0166, Mid-Ohio 0.0128; four-off 0.0858 / 0.0104 / 0.0086 / 0.0104; green passes 4193 / 22490 / 10918 /
6386; `defending.vsClearlyFaster` 3 / 14 / 4 / 5 over 8 seeds of 10 laps (the 2-lap test's 0 holds; long races do it).
Pressure (Y's own time lost, data / sim): slow Y with a faster X near 3.6 / 3.1 s, far 2.4 / 0.4; any other Y with a close
(not faster) X near 3.1 / 7.2 s. Aggression groups (against the sim's own curves): fastest quartile as attacker 0.97 (data 1.02).

**Diagnosis.** The close bins (d < 3 %) are on the data pooled (Laguna 1-3 % 11 pp low). The sim diverges where a car is
clearly faster: 3-8 % and 8-15 % 10-12 pp low on every track, the gap curve 20-30 pp low from 1 s out, the passing lap costs
2-3 x the data's, and the floor is twice the data's. The floor is the same failure seen from the other side: when a slower X
gets by a faster Y in the sim, Y lost a median 15.3 s on that lap (4.5 s when it was not passed; Sonoma seeds 1-6): the faster
car was stuck, and the slower car went by it in a train pass. Where the time goes (`selfplay_trace.ts --loss`, Laguna seed 1
5 laps / Sonoma seed 1 4 laps, s per car-lap over the car's own profile): the fastest quartile laps at 127 / 142 % of its solo
target, 21 / 37 s of it in a pass in hand (half its race time is spent in phase 1 or 2) and 9 / 17 s following; inside the pass
the loss is following the car being passed (6 / 11 s: held behind it at PASS_HEADWAY where the lanes pinch) and driving the pass
lane (5 s: the lane's own speed and laneFactor); before the pass, following a clearly slower car while no lane qualifies (7 /
11 s). The slower quartiles lose 10-24 s per lap following close and faster cars (the lap-1 jam of a shuffled grid is in it).
Candidate lanes rejected while planning (Laguna): off the road 28 k, a passer's lane 11 k, the band to sweep occupied 8 k, lane
occupied over the pass 6 k, shut by the road beside the car 5 k, accepted 1.1 k. That is AI round 1's "27 % of its pace to
traffic": it is the clearly faster car's slow commit and slow pass, on the straights (half the loss) and into the heavy
braking zones (Sonoma T2, T9a; Laguna T4, T10, T11).

**Order of the steps by what the diagnosis says buys the most:** A (decisive passing: the 3-8 / 8-15 % cells, the gap curve, the
passing-lap time, and the floor through it), then B (per-car aggression: the tiers set how early A commits), D (no lift on a
straight: the passed car holds its speed), C (yield: look and predictability, little pass rate per the data), E (close
racing, behind its switch: the d < 3 % cells are already on the data, so it must not move them).

**The steps (screens: Laguna + Mid-Ohio, seeds 1-8, 10 laps, against the baseline's same runs; 16 seeds where a contact rate came
within the 8-seed spread).** Seed noise first: the baseline itself, Laguna + Mid-Ohio pooled, reads 3-8 % 75.6 / 74.4 % and 8-15
% 89.7 / 84.8 % on seeds 1-8 / 9-16 (16 seeds: 75.1 / 87.0 %), contacts per car-lap Laguna 0.0248 / 0.0276 (0.0262), Mid-Ohio
0.0128 / 0.0095 (0.0112). A cell moves 3-5 pp between seed sets, so a step had to move it more than that. A variant with every
step switched off reproduces the baseline bit for bit (Laguna seed 1: contacts, four-offs, passes, every crossing), so the
screens compare like with like.

| step (variant) | 3-8 % / 8-15 % (g < 2) | floor | contacts Laguna / Mid-Ohio | green passes L / MO | verdict |
|---|---|---|---|---|---|
| baseline | 75.6 / 89.7 | 10.5 | 0.0248 / 0.0128 | 4193 / 6386 | |
| A1: plan from 1.0 / 1.3 / 1.6 s back by aggression (was 0.9 s), follow a clearly slower car at 0.6 / 0.45 / 0.32 s while waiting | 72.4 / 82.8 | 11.9 | 0.0261 / 0.0146 | 4411 / 7054 | dropped (G1 no better, G3) |
| A2: a pass lane without laneFactor's flat 1.2 %/m in corners | 73.0 / 84.9 | 10.1 | 0.0360 / 0.0113 | 4235 / 6717 | dropped (G3) |
| A3: abort a pass only 8 m further back than where it began (a pass planned 0.9 s = 35 m back was "dropped" by the 30 m rule at its first step: 324 of 820 attempts, Laguna seed 1) | 70.3 / 84.2 | 11.6 | 0.0331 / 0.0130 | 4157 / 7307 | dropped (G3); completed attempts 163 -> 190, stuck median 15.7 -> 13.1 s on Laguna seed 1, but the curves did not move |
| A4: A3 + a clearly faster car level on the inside of the corner keeps its pass through the shut (the car beside gives way) | 72.2 / 84.3 | 11.7 | 0.0291 / 0.0146 | 4226 / 7428 | dropped (G1 no better, G3) |
| B: aggression from the data tiers (Laguna 11, Sonoma 55, Buttonwillow 36, Mid-Ohio 33 cars moved; generators read curves.json, `--keep-layout` moved only `aggression`) | 73.5 / 83.4 | 11.8 | 0.0300 (16 seeds 0.0307 vs 0.0262) / 0.0099 | 4160 / 6585 | dropped (G3 Laguna on 16 seeds); the fastest quartile now passes 1.020 x its gap and pace (data 1.022, baseline 0.97) |
| D: no 97 % lift for a passer alongside on a straight (corner only); the audit found no other lift, lane change or slow-down for a car behind on a straight (making room where the road pushes the passer's lane, the corridor, the pinch guard and the give-way are contact avoidance and stay) | 75.4 / 83.8 | 10.0 | 0.0282 (16 seeds 0.0272 vs 0.0262) / 0.0077 (16: 0.0090 vs 0.0112) | 16 seeds 8272 / 13493 (vs 8206 / 13385) | dropped by the letter (Laguna +0.001 on 16 seeds; Mid-Ohio better, four-off lower on both) |
| C: yield as specified (slowest 10 % by target lap, 1-2 s seeded lag, one lane to the inside of the coming corner, slowest 3 % all lap, no lift) | 66.6 / 82.0 | 16.0 | 0.0414 / 0.0204 | 4637 / 10723 | dropped (G1, G3); slow car under pressure lost 3.9 s (data 3.6, baseline 2.3) |
| C2: C with one side per yield episode and the slowest 3 % reacting with no lag instead of all lap | 70.9 / 83.5 | 15.8 | 0.0345 / 0.0233 | 4525 / 10434 | dropped (G1, G3) |
| E: close racing on (one covering move to the inside lane per corner) | 72.4 / 84.7 | 11.0 | 0.0342 / 0.0121 | 4382 / 6752 | default OFF (G3 Laguna, beyond the spread on 8 seeds) |

Reading: the clearly-faster cells are not limited by when a pass is committed or how fast the pass lane is, but by the lane model
holding a pass where the lanes pinch (the shut rule, the pinch guard, the passed car's room) and by the trains a fast car meets
every lap; loosening any of those raises contacts on Laguna first. The yield as specified moves slow cars across the racing line
in front of cars that are already planning their pass (the inside is also where planLane prefers to pass): contacts double on
Mid-Ohio. What the data asks for next (not done here): a pass held through the corner needs the passed car to know it earlier
(its room-making look-ahead, 1 s today) than the pinch guard's 2 s; the 3 s look-ahead of 24 Oct failed the 2-lap test, a
look-ahead for the passed car only was not tried.

**Kept on the branch.** The yardstick (crossings, traffic_sim, solo_hash, the --loss trace and the plan-rejection tally), the
black-flag hook and the close-racing switch (off). Racing behaviour at the defaults is the baseline's, bit for bit (solo hashes,
and the four tracks' seed-1 races: every crossing identical), so the bands above stand.

**Black-flag hook.** `driver.ts passRisk(j, e, side)` returns 0 today; planLane rejects a lane whose risk exceeds PASS_RISK_MAX = 1
and takes RISK_W (4) x risk off its score. The AI black-flag round plugs in the expected flag cost of that commit (the
contact-at-fault and four-off odds of the lane at this closing speed, from self-play) against the time the pass gains.

## C1: the offset planner (28 Oct 2026, branch `planner-c1`)

Owner: "I prefer to just try C now." The traffic round's diagnosis: the lane model needs a free LANE through the corner, and
where the lanes pinch the car further back gives way, so clearly faster cars get by 10-12 points less often than the real field.
C1 replaces the lane model's pass machinery with a continuous lateral offset chosen every tick against the other cars'
projections (the rFactor 2 / AMS2 / iRacing shape), **behind a switch: `RaceConfig.planner` 'lanes' (default, the phone
fallback, untouched) | 'offset'**; `?planner=offset` (race mode -> race-build -> the worker host), `selfplay.ts --planner
offset`, `traffic_sim.ts --set planner=offset`, `solo_hash.ts --planner offset`, `selfplay_trace.ts --planner offset`.

**Design (`planner.ts`, pure: PlanWork preallocated, PlanEnv; no transcendental, `Math.sqrt` only).** A plan every PLAN_EVERY
0.2 s (staggered by car index) while a car is within 150 m ahead or 25 m behind (the 8 nearest by distance, ties by index);
alone, e* = 0 and nothing is evaluated (the alone path is today's, bit for bit). Neighbours are projected as the lane model
projects an occupant (span e / eT / 0.6 s drift clamped to the road where it will be, ± half width, + 0.8 m when off; speed from
its own profile x how held up it is now, planLane's estimate; the human player at its speed now). Candidates: the current target,
the racing line, a defending cover (light DEFEND within 3 %, the lane model's trigger), and 13 offsets 0.5 m apart around me,
inside the corridor (the road minus PASS_EDGE, the line always in it). Each is the transition at PASS_SHIFT x SHIFT_RATE then
held, clamped to the corridor, sampled every 0.25 s over 10 s. Costs (s): time lost against my race-line profile (laneFactor at
the offset; the clamped path's own curvature as a grip speed; capped behind a car in my band at its speed and my headway);
clearance below ALONG_CLR 0.7 m, steep by aggression (CLR_W 6 / 4 / 2.5); corridor edge; off the line 0.006 s/m/s while racing a
car within 30 m, 0.04 when nobody is, 0.5 inside a no-pass window; damping 0.02 s/m; a reversal before the apex of the move
while a car is within 20 m +2 s (one move); a lane change asking more than the lateral grip (v²κ + v·rate/Ld) 4 s per unit excess,
moves away from the line only; a pass that does not progress or would take > PLAN_T_MAX 40 s 1.5 s; passRisk x 4 (0 today).
Hard rules: 2 BIG for a move toward a clearly faster car within 25 m behind (any move when it is straight behind), never across
a car within the sweep length, a move into the margin of a car my body overlaps now (overlap holds), from behind to ahead of a
running car in a no-pass window (formation / yellow: e* = 0, single file); BIG + samples left (earlier is worse) within the
first T_HARD 2.5 s for clearance below LANE_CLR 0.3 m, braking onto a car newly in my band beyond 0.85 x the brakes (room to
its bumper), and the road clamping my offset on the OUTSIDE of a corner faster than the shift rate (turn-in / track-out);
beyond 2.5 s those are steep costs. Selection: the minimum, ties to the current target, a new target held MIN_HOLD 1 s and
better by HYST 0.5 / 0.35 / 0.25 s by aggression. When every candidate breaks a rule against a car right ahead / beside me, I
give way to it (its speed - 1.5 m/s) until the next plan. In the driver (offset only): the pass start / passStep / planLane,
the passer reserve and the pinch guard are off; a car my body overlaps and clear of me laterally is not followed; the give-way
only when squeezed; the 97 % lift for a car alongside behind me and converging in a corner only; the controller (SHIFT_RATE,
PASS_SHIFT, the grip limiter, the lane speed look-ahead, PASS_EDGE) treats a held e* as a pass lane.

**What the first build needed (each found on traces, Laguna 6 seeds x 3 laps):** the far-horizon rules soft (they forced yields
to cars 100 m away); the move back to the line exempt from the grip term; the outside-at-turn-in path (carried offsets clamped
onto the line faster than a car can move: four-off 0.31 -> 0.10 per car-lap); graded infeasibility and a yield only to a car
right ahead (a yield cascade took cars to 3-5 m/s on straights); the braking rule firing on the car I already follow, which
replaced the target 200 times a car-lap (now 31; the lane model started about 4 passes a car-lap on the same run). AI_VERSION 8; no pace file touched.

**A/B, Laguna + Mid-Ohio, seeds 1-8, 10 laps** (`tools/race/out/c1/{lanes,b1,v2,v3}.{md,json}`; the lanes run reproduces
`baseline.json` exactly: every cell, contacts, passes):

| run | Yf / 0-1 / 1-3 / 3-8 / 8-15 / >15 % (g < 2 s) | gap curve d >= 3 %, 0-0.5 .. 8-10 s | passing lap 3-8 / 8-15 s | contacts L / MO | four-off L / MO | green passes L / MO |
|---|---|---|---|---|---|---|
| data | 8.2 / 39.4 / 60.3 / 86.9 / 97.8 / 99.7 | 96 91 88 88 84 77 62 | 2.9 / 3.4 | | | |
| lanes (= baseline) | 10.5 / 25.7 / 54.6 / 75.6 / 89.7 / 95.7 | 90 84 63 66 46 55 35 | 4.0 / 7.8 | 0.0248 / 0.0128 | 0.0858 / 0.0104 | 4193 / 6386 |
| b1, first build | 8.5 / 22.3 / 53.2 / 71.1 / 79.9 / 88.7 | 91 79 65 54 62 72 50 | 3.6 / 10.7 | 0.0127 / 0.0116 | 0.0540 / 0.0064 | 3110 / 4987 |
| **v2**, the outside-only road rule (kept) | 8.0 / 23.1 / 52.1 / 75.9 / 86.3 / 91.0 | 95 81 72 65 66 46 83 | 3.6 / 7.7 | 0.0226 / 0.0195 | 0.0607 / 0.0105 | 3034 / 5164 |
| v3 = v2 + merge back in the projection once 30 m clear | 8.8 / 24.9 / 51.8 / 68.8 / 78.7 / 91.2 | 94 77 62 64 64 67 61 | 3.9 / 10.4 | 0.0206 / 0.0203 | 0.0589 / 0.0094 | 3221 / 5158 |

(Pooled time lost on the passing lap here is Laguna + Mid-Ohio; the brief's 5.7 / 11.5 s is the four-track pool.)

**Gates (v2, the tree as committed).** G1 FAIL: 3-8 % 75.9 (needs >= 81), 8-15 % 86.3 (>= 94); floor 8.0 (<= 10.5, pass);
passing-lap loss 3.6 / 7.7 s (needs <= 2.7 / 5.2 against these runs: fail); d < 3 % cells 23.1 / 52.1 against 25.7 / 54.6 (within
5, pass). G3: contacts Laguna 0.0226 (<= 0.0248, pass), Mid-Ohio 0.0195 (<= 0.0128; beyond the ±0.006 spread, so no 16-seed
decision: FAIL); four-off 0.0607 / 0.0105 (<= 0.0858 / 0.0104: Laguna pass, Mid-Ohio level); green passes 3034 / 5164 (below
4193 / 6386: FAIL). G4: suite green; `ai_behaviour` runs twice (describe.each lanes / offset, same thresholds): with the
planner on, "within 3 %" makes no covering move (0, needs >= 1) and "full field, 2 laps" makes 111 situations and 97 passes
(> 150 each; 63 % completed, > 15 % 85 %, contacts 0.013, no defending against a clearly faster car, no formation pass: those
hold): both run as `test.fails` for 'offset' only, nothing loosened. Worker identity with `planner: 'offset'` added (the switch
reaches every driver in the worker). Planner unit tests (`planner.test.ts`): pass a slow car, overlap holds, never across, no
move toward a clearly faster car behind, no-pass window (and an off car passed freely), one move / hysteresis / reversal, alone
= e* 0 with no plan evaluated. G5: solo hashes identical with the planner off and on (laguna 6b8f157f11f72166, sonoma
288bd306e8620212, buttonwillow 4f81fe2cda1b3ef5, mid_ohio 6e6024a7c42062d5). G7: build green, e2e 13/13.

**CPU** (`selfplay.ts --laps 2 --seed 1`, sequential, quiet machine): Sonoma 2.23 -> 2.36 µs per car-step (+5.8 %), Laguna 1.89 ->
1.91 (+1 %). Nothing cut. The 0.1 s tick near a car was not tried (the budget went to the screens).

**Reading.** The offset planner is safer per pass (b1 halved Laguna's contacts, four-offs down a third) and its passer keeps
the lap of the pass close to the lanes' or better (3-8 % 3.6 s against 4.0), but it passes less: green passes -25 %, the 8-15
% cell 3-10 points under the lanes. On the selfplay measure it completes more clearly-faster situations (Laguna 79.7 % against
71.5 %), so what it loses is the encounters a lap at 1-5 s gaps (the gap curve) and the trains: a candidate is "move and hold",
priced 10 s ahead against neighbours that are themselves projected as holding, and every conflict inside 2.5 s is a hard
stop, so a car commits only when the whole pass looks clean; the road rule (v2) moved the 3-8 % cell from 71 to 76 and the
8-15 % from 80 to 86 but put Mid-Ohio's contacts up (0.012 -> 0.020). The merge in the projection (v3) made things worse:
with the return to the line priced as free, the line candidate behind the slow car stops losing against the pass. Not
reached here, and the next things to try (C2).

**C2 list.** Tuning on all four tracks and 16 seeds with the owner's drive notes; per-car aggression from the data tiers
(HEADWAY, CLR_W, HYST already take it); the yield trait (dropped in the traffic round); the traffic read, a pick one corner
ahead (which side of the slow car the next corner opens); candidates that end (a pass with its own merge, priced as the lane
model's phase 2-3, not the v3 shortcut) and a two-move horizon; the hard window T_HARD per closing speed; the 0.1 s tick near a
car; a covering move within 3 % that the "within 3 %" test sees; the passRisk / black-flag cost; the phone tier (it stays on
the lane model).

## C2 (28 Oct 2026, branch `planner-c1`): tuning the offset planner to the MyLaps passing data

Owner: "Try C2." The lane model stays the default and untouched; everything below is `planner: 'offset'` only.

**Stage 1, the wait (no behaviour change).** New measure, positions only and the same for both planners
(`selfplay_metrics` `passing.wait`, reported by `traffic_sim.ts`): a clearly faster car (pace hint >= 3 %) arriving within 25 m
behind a running car in green; the time from that arrival to its centre being ahead, or the wait ending otherwise (dropped
> 60 m back, the car ahead off, the flag). And `traffic_sim.ts --why` (offset only): after every plan of a car whose nearest car
ahead is clearly slower and within 25 m, the plan is tallied as alongside, pass (the chosen target is laterally clear of the slow
car's projected band) or hold, and for a hold what kept the best candidate clear of that band from winning: a hard rule (WHY; on
the car ahead or another car; that car still on its line or moving), no such candidate in the corridor, the min hold, the
hysteresis, or the soft cost component (`planner.ts` COMP, filled only while `planTally.on`) by which it lost.

Laguna seeds 1-3, 5 laps (`tools/race/out/c2/diag_{lanes,offset}.md`):

| planner | waits | done | median s | p90 s | dropped / off / flag |
|---|---|---|---|---|---|
| lanes | 1318 | 961 | 13.8 | 59.8 | 259 / 48 / 50 |
| offset (C1 v2) | 996 | 766 | 10.6 | 84.8 | 145 / 39 / 46 |

What held the clearly faster car (offset, 153 k plans within 25 m behind a clearly slower car): pass 22.9 %, alongside 6.2 %,
hold 70.9 %, of which: **hard 'faster' 13.1 %** (a clearly faster car within 25 m behind me forbids every move when it is straight
behind: in a train the middle car freezes behind the slow car); **hard 'across' on the car ahead 14.3 %** (7.9 still, 6.4 moving:
the never-across rule fires on the car I am following in its band whenever its centre is a few cm toward the side I pull out to,
so a pull-out to that side is a "cross"); soft grip 10.4 % (the move asks more than the lateral grip: into corners); hard brake
6.5 % (5.2 on the car ahead); soft clearance 6.6 %; no room in the corridor 3.9 %; soft line 3.9 %; the no-pass window 3.7 %
(Corkscrew, by design); soft reversal 2.5 %; LONG 2.2 %; the hard road rule 0.7 % + soft 0.3 %; hard clearance 1.2 %; the
hysteresis 0.9 %; the min hold 0.3 %. The projection band of the car ahead (eT span, drift) shows up as 'moving' in about a third
of the hard holds on it.

Reading: the fast car does not wait on the price of the pass but on two rules misfiring in the following position (27 % of
its plans), then the grip cost into corners and the braking rule; the hard window, the hysteresis / hold and the outside road
rule hold it less than 2 % each. Order of the steps: H0 (the two misfiring rules: never across means from one side of a car to
the other, not out of its band; a clearly faster car behind me does not freeze a pass on a clearly slower car ahead) with H1
(predictability) first, then the grip / commit (H4), then H3 + H5, then H2, then H6 on what the screens show.

**Stage 2, the hypotheses** (`planner.ts` `knobs`, set per run with `traffic_sim.ts --knob k=v`; the kept ones are the defaults).
H0 = the two misfiring rules of stage 1. Added on the way: **tail** (part of H2: the time lost behind a car in my band at the end
of the horizon carried on TAIL_T 10 s; without it a pass of a 5 % slower car gains under 0.5 s in 10 s and any cost beats it),
**H4's pressure headway** (a clearly slower car ahead is followed at PASS_HEADWAY 0.3 s, as the lane model's pass phase 1: at
0.55 s the fast car sat 20 m back and a 5 % pass took 20 s, longer than the horizon), and in **H6** the passed car is told
(Traffic.passing set by the offset passer, so the lane model's room-making look-ahead works for it) and the road rule fires on the
inside too while a car is beside me there, at ROAD_K 0.6 of the shift rate. Screens: Laguna + Mid-Ohio, seeds 1-8, 10 laps
(`tools/race/out/c2/s1..s5.{md,json}`); dev runs (Laguna or Mid-Ohio seeds 1-3, 5 laps, not screens) picked between variants.

| screen | 3-8 / 8-15 % (g < 2) | floor / 0-1 / 1-3 % | gap 2-3 / 3-5 / 5-8 s | passing lap 3-8 / 8-15 s | contacts L / MO | four-off L / MO | green passes L / MO | verdict |
|---|---|---|---|---|---|---|---|---|
| lanes (= baseline) | 75.6 / 89.7 | 10.5 / 25.7 / 54.6 | 66 / 46 / 55 | 4.0 / 7.8 | 0.0248 / 0.0128 | 0.0858 / 0.0104 | 4193 / 6386 | |
| C1 v2 | 75.9 / 86.3 | 8.0 / 23.1 / 52.1 | 65 / 66 / 46 | 3.6 / 7.7 | 0.0226 / 0.0195 | 0.0607 / 0.0105 | 3034 / 5164 | |
| s1 H0 + H1 | 72.7 / 81.9 | 7.9 / 23.0 / 53.8 | 64 / 57 / 59 | 3.6 / 9.5 | 0.0193 / 0.0195 | 0.0637 / 0.0100 | 2932 / 5368 | kept (the rules were wrong; cells within noise) |
| s2 + H2 (ending candidates) + tail | 70.5 / 87.7 | 10.2 / 24.1 / 47.8 | 63 / 63 / 56 | 3.6 / 8.1 | 0.0447 / 0.0176 | 0.1243 / 0.0229 | 2781 / 4689 | kept only with H4 (alone: Laguna contacts and four-offs up) |
| s3 + H4 (commit margin, no min hold, pressure headway) | 78.5 / 95.2 | 6.2 / 23.6 / 49.6 | 74 / 75 / 59 | 4.7 / 7.2 | 0.0338 / 0.0422 | 0.1350 / 0.0379 | 2878 / 8439 | kept with H6 |
| **s4 + H6** (the passed car told; inside road rule beside a car; ROAD_K 0.6) | **82.3 / 96.2** | 6.6 / 26.3 / 52.3 | 74 / 72 / 69 | 4.5 / 5.9 | 0.0258 / 0.0189 | 0.1089 / 0.0273 | 2945 / 8887 | **kept: the C2 tree** |
| s5 = s4 + H3 (hard window by closing speed 1-4 s) + H5 (outside road rule a cost beyond 1 s) | 79.8 / 93.2 | 8.1 / 25.2 / 51.7 | 79 / 70 / 73 | 5.3 / 6.4 | 0.0265 / 0.0215 | 0.1661 / 0.0325 | 2865 / 8647 | reverted (switched off: four-offs up 50 % on Laguna, cells lower) |

Dev runs, not screened: the grip term at the onset / stop of a lateral move only (Laguna four-off 0.08 -> 0.22) and only where the
line uses > half the grip (contacts 0.015 -> 0.066): both off, the grip cost stays C1's; ROAD_K 0.4 and H4's headway 0.42 s: no
change beyond the 3-seed noise. The sixth screen was not used. s4 is past the halfway rule (>= 81 / >= 94), so the full
evaluation ran on it. H6's cause (Mid-Ohio, C1 v2 and s3): side contacts at turn-in (T2 s 800-1000, T1, T4 s 1940), the passer
on the inside overlapping the rear of the car on the line while the road clamps the inside offset onto the line faster than a car
moves sideways (8 m in 50 m at T2), the passed car learning of it from its corridor only (it lifts, 'passed'); C1 had exempted the
inside from the road rule. The planner does not read the Mid-Ohio `ai:` knobs as knobs of its own: followScale scales the
headway it is handed, laneMargin and shiftGrip act through roadLo / roadHi and the controller it shares with the lane model.

**Full evaluation** (C2 tree at f672da1, all four tracks, seeds 1-16, 10 laps, `tools/race/out/c2/full_{offset,lanes}.{md,json}`;
the lane model run on the same commit and seeds on all four tracks: Laguna 0.0262 and Mid-Ohio 0.0112 reproduce the traffic
round's 16-seed numbers exactly). Pooled, g < 2 s, 43 284 pairs (offset) / 42 998 (lanes):

| d | data | lanes | offset C2 |
|---|---|---|---|
| Y faster (floor) | 8.2 | 16.8 | 10.3 |
| 0-1 % | 39.4 | 36.3 | 32.3 |
| 1-3 % | 60.3 | 58.9 | 54.1 |
| 3-8 % | 86.9 | 75.0 | 82.3 |
| 8-15 % | 97.8 | 85.1 | 95.9 |
| > 15 % | 99.7 | 94.3 | 99.2 |

Gap curve (d >= 3 %, 0-0.5 .. 8-10 s): data 96 91 88 88 84 77 62; lanes 87 80 67 62 61 60 40; offset 95 87 75 74 77 66 59. Time lost
(d 0-1 / 1-3 / 3-8 / 8-15 %), passing lap: data 1.9 / 2.1 / 2.9 / 3.4, lanes 3.8 / 3.2 / 5.9 / 12.5, offset 6.6 / 5.2 / 5.5 / 7.1 s;
stuck: data 2.5 / 4.3 / 8.4 / 17.7, lanes 2.8 / 6.1 / 11.8 / 20.6, offset 5.1 / 7.3 / 11.5 / 16.2 s. The wait (positions only):
median 13.7 -> 9.6 s, p90 73 -> 54 s, time lost per wait 3.5 -> 2.1 s; 68 % -> 86 % of waits end ahead.

| track | byD Yf..>15 lanes | offset | gap curve offset | contacts lanes / offset | four-off lanes / offset | green passes lanes / offset |
|---|---|---|---|---|---|---|
| laguna_seca | 15 36 43 62 84 96 | 8 24 41 75 92 99 | 93 84 78 76 70 65 55 | 0.0262 / 0.0211 | 0.0784 / 0.1165 | 8206 / 5753 |
| sonoma | 24 46 60 76 84 95 | 12 40 59 85 98 100 | 94 88 78 78 82 75 90 | 0.0312 / 0.0463 | 0.0106 / 0.0230 | 46121 / 53932 |
| buttonwillow | 14 38 60 72 84 93 | 12 31 50 80 95 99 | 97 84 70 66 76 55 50 | 0.0184 / 0.0208 | 0.0089 / 0.0359 | 20930 / 21849 |
| mid_ohio | 9 26 59 80 91 92 | 6 26 53 83 96 99 | 96 88 73 77 81 73 64 | 0.0112 / 0.0191 | 0.0094 / 0.0257 | 13385 / 17850 |

(data per track, Yf..>15: Laguna 7 37 52 82 98 100, Sonoma 9 43 60 87 97 100, Buttonwillow 9 37 60 83 98 100, Mid-Ohio 7 37 62 90 99
100.)

**Gates (C2 tree).** G1 FAIL by two cells and two gap bins: 1-3 % 54.1 (-6.2, tolerance 6), gap 2-3 s 74 (-13.1), 5-8 s 66
(-11.2); pass: 0-1 % (-7.1 within 8), 3-8 % (-4.6), 8-15 % (-1.9), > 15 % (-0.5), floor 10.3 (<= 12), gap 3-5 s (-6.6). G2 FAIL:
passing-lap medians 6.6 / 5.2 / 5.5 / 7.1 s against 1.9 / 2.1 / 2.9 / 3.4 (tolerance max(35 %, 1.5 s): all four out), stuck 5.1 /
7.3 / 11.5 vs 2.5 / 4.3 / 8.4 out, 16.2 vs 17.7 in. G3 FAIL: contacts Laguna 0.0211 <= 0.0262 pass; Sonoma 0.0463 vs 0.0312,
Buttonwillow 0.0208 vs 0.0184, Mid-Ohio 0.0191 vs 0.0112 fail; four-off fails on all four (1.5-4 x); green passes >= lanes on
Sonoma, Buttonwillow, Mid-Ohio, not Laguna (5753 vs 8206). G4: `npx vitest run` 826 passed + 1 expected fail (below). G5: solo
hashes identical with the planner on and off (6b8f157f11f72166 / 288bd306e8620212 / 4f81fe2cda1b3ef5 / 6e6024a7c42062d5), AI_VERSION
8, no pace file touched. G6: Sonoma 2.26 -> 2.42 µs per car-step (+7 %; `selfplay.ts --laps 2 --seed 1`). G7: build green, e2e
13/13. The default stays 'lanes'.

**Stage 3, the behaviour tests.** `passing.situations` and `completed` are counted from positions (a clearly faster car within
40 m of the car directly ahead, real once within 20 m; done when 2 m ahead): the same for both planners, unchanged. `defending.
within3` counts the lane model's defend decision (`defendSide`), which the offset planner computes too but only took as a 0.3 s/m
preference: in the "within 3 %" case it counted 16 decisions with no move (0.00-0.42 m for 0.8). New, both planners:
`defending.covers`, a lateral move of >= DEFEND[aggression] toward the inside of a passable corner (braking point within 120 m)
with a car within 3 % and 1 s (30 m) behind, one per corner approach; the test reads it, threshold unchanged (>= 1). Lane model,
full field seed 1 2 laps: within3 13, covers 22 (the position count also sees inside moves made for other reasons). The offset
planner now makes the move: COVER_W 2 s/m on the cover (was PREF_W 0.3), and the case is a real test for 'offset'. The full field
(2 laps): offset 165 situations (> 150 pass), 68 % completed, > 15 % 87 %, contacts 0.038, four-off 0.19, defending against a
clearly faster car 1 (needs 0), green passes 119 (needs > 150): still `test.fails` for 'offset'. COVER_W came after the full
evaluation; dev runs (seeds 1-3, 5 laps) put it within their noise (Laguna contacts 0.023 -> 0.017, Mid-Ohio 0.012 -> 0.014).

**Reading.** The wait was the rules, then the horizon's arithmetic: a pass of a car 5 % slower gains under 0.5 s in a 10 s horizon
from 20 m back, so the planner chose to follow almost every time. Pricing the staying behind past the horizon, following closer,
committing at the aggressive margin and passes that end lifted the clearly-faster cells onto the data (3-8 % 75 -> 82, 8-15 % 85
-> 96, floor 17 -> 10) and the gap curve by 10-16 points, but the passing lap now costs 5-7 s (the pressure pass is long and
side by side) and contacts and four-offs rise wherever the passes rise (Sonoma, Mid-Ohio contacts +50-70 %; four-offs 1.5-4 x:
Laguna T11 / T10 / T4 track-out, Mid-Ohio spins after side contacts). Not a default.

**C3 list.** The four-offs and contacts of the pressure pass (track-out: the car lags its shift target; side by side at turn-in:
the passed car needs the pass earlier than its corridor); the passing-lap time (a pass that commits from 0.3 s back on a straight
and finishes, not a side-by-side through the next corner); the 1-3 % cell and the 2-3 / 5-8 s gap bins; the full field's green
passes; the yield trait; the traffic-read pick (which side the next corner opens); per-car aggression from the data tiers; the
passRisk / black-flag cost; the phone tier (stays on the lane model).

## C3 (29 Oct 2026, branch `planner-c1`): the vortex rule, lead cars that hold their line, the cost side

Owner (28 Oct, evening, after driving C2): the offset AI is too deferential to traffic and makes more mistakes (the P1 car off
Laguna T10 with #711 behind it); the "Vortex of Danger" rule: the lead car drives its line, the passer must be alongside by
turn-in or back out. Everything below is `planner: 'offset'` only; the lane model is untouched (solo hashes, its runs). Knobs
(planner.ts `knobs`, `traffic_sim.ts --knob k=v`): r1, r2, r3, tv, gr, ctl, lift, room, tailT, fc, vt.

**As built.** **R1** (lead cars hold their line): a car behind me whose body does not overlap mine is invisible to my plan
(`behindClear`: no clearance, never-across, road-beside, following / braking on the projection when it passes me, LONG, the
'racing' line rate, the one-move rule) and to my corridor in the driver (the alongside loop skips it; no room-making look-ahead
and no told lift for it). What remains: overlap holds (nOwn; the corridor; `room`: room made, as the lane model does, for a
passer my body overlaps, where the road pushes its lane), the alongside lift in a corner only and only for a car alongside
(`lift`: its nose past PINCH_OK of the overlap and laterally clear; a car in my wake whose front overlaps my rear got a brake
test: Mid-Ohio's 'follow/passed' contacts), the no-defence rule (cfSide), the cover within 3 %. Told (Traffic.passing) = my
target frozen (plan() keeps the current target unless it breaks a rule), except by a car within 3 % (the cover first: frozen,
"within 3 %" made no covering move). **R2** (the passer's vortex): per neighbour ahead, the corner it drives next (driver
`vortexCorners`: turn-in / track-out where |κ| of the corner's sign falls below VORTEX_K 0.3 of its peak, from the apex out;
Laguna T2 46 / 102 m, T10 30 / 92 m, Mid-Ohio T4 50 / 44 m); a candidate on which my body comes to overlap it on its inside
after its turn-in (before the apex), or on its outside after its apex (before its track-out), when I did not overlap it at its
turn-in / apex, is refused: 2 BIG + samples left within knobs.tv 4 s, a clearance-weight cost beyond; no corner, no vortex. The
first build (my body anywhere in the triangle behind it) held 34 % of the fast cars' plans and cut the 3-8 % cell to 53 (dev
run, Laguna + Mid-Ohio seeds 1-3, 5 laps): rebuilt as the dive (arriving alongside), 5.6 % of the holds. **R3**: the plan moves
at `shiftRate` (the grip the line leaves, a_lat - v²|κ|, times Ld / v; at most the pass rate, at least SHIFT_MIN 0.8 m/s) and
the road rule fires where the clamp moves my offset faster than that rate (whoever I race); `ctl`: the controller moves a held
offset at the same rate while another car is within the horizon (alone it is today's: the solo hashes); `gr`: the GRIP cost at
that rate. Not kept (switches off): `fc` (the friction circle under braking in both) and `vt` (the vortex in the projection's
tier, below a braking conflict): dev runs within noise, contacts up. **R4**: `tailT` (C2's TAIL_T 10 s; 90 s prices a lap
behind a 5 % slower car at 4.5 s) tried, not kept.

**Dev runs** (Laguna + Mid-Ohio, seeds 1-3, 10 laps; `tools/race/out/c3/d10_*`): s1 tree 3-8 / 8-15 % 68 / 77, contacts L / MO
0.008 / 0.013, four-off 0.026 / 0.012; + gr alone 74 / 84, 0.025 / 0.021, 0.079 / 0.020 (moves into corners the controller then
overdrives); + tailT 40 78 / 88, 0.033 / 0.027, 0.136 / 0.023; tailT 90 78 / 86, 0.026 / 0.028, 0.194 / 0.038; + gr + ctl 76 / 89,
0.022 / 0.032, 0.015 / 0.018; + lift 72 / 82, 0.021 / 0.026; + room (= s3) 66 / 76, 0.005 / 0.011, 0.018 / 0.010; gr + ctl + lift +
room (= s2) 77 / 90, 0.010 / 0.015, 0.033 / 0.021; + fc + vt 78 / 86, 0.018 / 0.025; fc alone 78 / 95, 0.017 / 0.023, 0.022 / 0.011;
vt alone 77 / 90, 0.013 / 0.017. What held the fast car (s2 tree, `--why`): pass 37 %, soft clearance 8.7, alongside 6.6, the
vortex 6.2, no room 6.1, reversal 5.5, grip 3.7, the road rule 2.8 + 1.9 + 1.2 + 2.3 (soft); no single cause.

**Screens** (Laguna + Mid-Ohio, seeds 1-8, 10 laps, `tools/race/out/c3/s1..s5.{md,json}`; five of six used):

| run | 0-1 / 1-3 / 3-8 / 8-15 / >15 % (g < 2), floor | gap 2-3 / 3-5 / 5-8 s | passing lap 0-1 / 1-3 / 3-8 / 8-15 s | contacts L / MO | four-off non-mishap L / MO | green passes L / MO | wait median / p90 s |
|---|---|---|---|---|---|---|---|
| data | 39.4 / 60.3 / 86.9 / 97.8 / 99.7, 8.2 | 88 / 84 / 77 | 1.9 / 2.1 / 2.9 / 3.4 | | | | |
| lanes (C1 baseline) | 25.7 / 54.6 / 75.6 / 89.7 / 95.7, 10.5 | 66 / 46 / 55 | - / - / 4.0 / 7.8 | 0.0248 / 0.0128 | 0.0858 / 0.0104 (all) | 4193 / 6386 | |
| C2 s4 (the C2 tree) | 26.3 / 52.3 / 82.3 / 96.2 / 99.0, 6.6 | 74 / 72 / 69 | 5.3 / 5.7 / 4.5 / 5.9 | 0.0258 / 0.0189 | 0.1089 / 0.0273 (all) | 2945 / 8887 | 11.5 / 52 |
| s1 R1 + R2 + R3 | 24.0 / 51.0 / 71.2 / 78.6 / 95.4, 9.1 | 57 / 61 / 60 | 6.0 / 3.3 / 3.9 / 8.9 | 0.0095 / 0.0163 | 0.0212 / 0.0104 | 2450 / 5405 | 19.7 / 112 |
| s2 + gr + ctl + lift + room | 24.3 / 56.2 / 75.5 / 86.7 / 96.2, 11.0 | 56 / 64 / 51 | 6.5 / 3.6 / 4.0 / 9.5 | 0.0125 / 0.0164 | 0.0280 / 0.0185 | 2619 / 6489 | 18.6 / 93 |
| s3 s1 + lift + room | 24.7 / 50.9 / 68.4 / 75.9 / 94.0, 10.4 | 72 / 67 / 52 | 4.8 / 2.9 / 4.6 / 8.8 | 0.0053 / 0.0132 | 0.0174 / 0.0099 | 2277 / 5556 | 19.5 / 111 |
| s4 s2 + tailT 90 (R4) | 27.6 / 54.3 / 80.7 / 90.6 / 98.5, 8.5 | 72 / 58 / 57 | 6.3 / 3.6 / 4.2 / 6.7 | 0.0196 / 0.0195 | 0.0833 / 0.0357 | 2723 / 7426 | 17.2 / 79 |
| **s5 = s2 + the cover exception + alone untouched (the tree as committed)** | 28.6 / 54.2 / 73.6 / 85.7 / 98.6, 9.2 | 59 / 47 / 57 | 4.6 / 3.8 / 4.5 / 7.1 | 0.0125 / 0.0161 | 0.0274 / 0.0225 | 2482 / 6167 | 19.3 / 92 |

Where the cost went: R1 took Laguna's four-offs from 0.11 to 0.02 per car-lap (the lead cars' track-out four-offs at T11 / T10 /
T4 are gone: they were the room-making for a passer from up to 12 m back) and contacts from 0.026 to 0.005-0.013. Mid-Ohio's
contacts stay 0.013-0.016 (lanes 0.0128): the T4 braking zone (1830-1970 m, 50 -> 21 m/s), a passer half a car over closing at 2-9
m/s on the car ahead under braking ('follow/follow', 'follow/profile'), and the side contacts at the T4 / T2 apexes. The passing
lap did not come down: 8-15 % 6.7-9.5 s in every screen (data 3.4), so the pass is not "close, alongside under braking, exit"
yet: with the lead car no longer making room, the passer waits (median 19 s, p90 79-112 s against C2's 11.5 / 52).

**Stopped** (the brief's rule): after the screens the passing lap still costs > 4.9 s (8-15 %: 7.1 s on the tree as committed, 6.7
at best) and Mid-Ohio's contacts are above the lanes; no change in hand is clearly the fix (R4's commit buys the cells, 80.7 /
90.6, with Laguna's four-offs back at the lanes' 0.083 and Mid-Ohio's at 3.4 x). No full evaluation; the default stays
'lanes'.

**Gates on the tree as committed (s5 and the suite).** G1 / G2 / G3: not evaluated on four tracks (stopped); on the screen G1
fails (3-8 % -13.3, 8-15 % -12.2, gap 2-3 / 3-5 / 5-8 s -28 / -37 / -20), G2 fails (passing lap 4.6 / 3.8 / 4.5 / 7.1 s), G3 fails on
Mid-Ohio (contacts 0.0161 vs 0.0128, four-off 0.0225 vs 0.0104) and on Laguna's green passes (2482 vs 4193); Laguna's contacts
and four-offs pass. G4: `npx vitest run` 829 passed + 1 expected fail: the full field for 'offset' (seed 1, 2 laps: 113
situations and 81 green passes, > 150 each; 70 % completed, > 15 % 52 / 53, contacts 0.075, no defending against a clearly faster
car) stays `test.fails`; planner unit tests for R1 (two cars behind change no cost; overlap holds; told holds), R2 (the dive
refused, backing out / in its wake / alongside by turn-in / a straight allowed, the exit vortex), R3 (the rate the grip leaves;
the road clamp at the limit). G5: solo hashes identical with the planner on and off (6b8f157f11f72166 / 288bd306e8620212 /
4f81fe2cda1b3ef5 / 6e6024a7c42062d5; the controller's rate first changed Laguna's and Buttonwillow's alone: now only while a car
is within the horizon), AI_VERSION 8, no pace file touched. G6: Sonoma 2.24 -> 2.43 µs per car-step (+8.5 %). G7: build green,
e2e 13/13.

**R5, Eyesore** (Laguna seeds 1-8, 10 laps; `tools/race/out/c3/eyesore.{ts,md}`; the solo target is the pace file's target lap,
#711 113.8 s; waits are the done waits of that car as the attacker; places gained per lap from the crossing order):

| planner | cars | race median lap / race best lap over the target | wait per slower car, median / p90 | net places per lap |
|---|---|---|---|---|
| lanes | #711 | +27.9 / +11.8 s | 10.9 / 46.1 s (411 waits) | 1.88 |
| lanes | fastest quartile (12) | +27.9 / +10.1 s | 13.4 / 60.3 s | 1.26 |
| offset (s5) | #711 | +30.6 / +10.9 s | 12.4 / 67.8 s (283) | 1.79 |
| offset (s5) | fastest quartile | +26.7 / +10.0 s | 14.2 / 88.0 s | 0.94 |

Where Eyesore stands: in a race it laps 28-31 s over its own target with either planner (its best race lap still 11 s over),
because it spends 11-12 s (p90 46-68 s) behind every slower car it catches; a human at the Probe's pace is not held like that,
so the owner's reading holds on both planners: #711 will not lap faster than him until the wait is fixed. C3's offset tree waits
longer than the lanes (p90 68 vs 46 s).

**C4 list.** The pass itself (the passer has to make the pass the lead car no longer makes for it: a commit on the straight with
the pull-out early enough to be alongside by the braking point, priced over the lap without the four-off cost s4 showed; the
traffic-read pick, which side the next corner opens); Mid-Ohio's T4 braking zone (a passer half a car over closing under braking:
the braking rule on the car it leaves, the friction circle `fc` against a 16-seed run); the yield trait; the data aggression
tiers; passRisk / black flags; the phone tier (stays on the lane model).

## Pace anchor q 0.2 (29 Oct 2026, branch `reanchor`)

Owner, 28 Oct: "solo pace should be closer to best lap pace. Median pace reflects traffic; it seems that we are double-penalizing."
The four public pace files are regenerated at q 0.2 of each car's / stint's clean laps (the traffic yardstick's "free pace"), header
`pace: { stat: "quantile", q: 0.2 }`; generators only (reproduced at q 0.5 first: identical `cars`; the Mid-Ohio #56 notes text and
model_id are the known difference). `curve` carried over by car id from the q 0.5 files; every scale / `achievedLap` / `resolved`
recalibrated (`calibrate_field.ts --workers 6`, tolerance 0.2 %). AI_VERSION 8. `pace_quantile.test.ts` reads each file's own q.

| track | cars / stints | car / stint median target change | worst residual | cars / stints off by > 0.5 % before -> after | wall-clock |
|---|---|---|---|---|---|
| Laguna | 44 / 261 (+ #619 row) | -4.5 % / -1.9 % | 1.18 % | 0 / 0 -> 0 / 1 | 344 s |
| Sonoma | 133 / 1056 | -4.7 % / -2.7 % | 2.61 % | 1 / 4 -> 1 / 17 | 1622 s |
| Buttonwillow | 99 / 774 | -3.7 % / -2.4 % | 0.28 % | 2 / 60 -> 0 / 0 | 1363 s |
| Mid-Ohio | 85 / 702 | -3.0 % / -1.9 % | 0.33 % | 0 / 0 -> 0 / 0 | 818 s |

No car or stint sits at PACE_MAX (1.8) in either set; "off" is the cap measure of round 1 (|achieved / target - 1| > 0.5 %: the
car cannot reach the target). Buttonwillow's 60 stints off in the median file (worst 9.05 %) are not off in the fresh calibration (cause not investigated). `aggression` unchanged on every car. Capped cars still race by `achievedLap`
(field.ts `paceHint`, unchanged). The stint median moves less than the brief's -3 %: a stint's q 0.2 is nearer its median than
the car-wide one (a stint is 5-30 laps from one driver).

**Bands** (lane model, seeds 1-8, 10 laps, `traffic_sim.ts --workers 6 --compare`; before = the C2/C3 lanes numbers / baseline.md):

| | before (q 0.5) | after (q 0.2) |
|---|---|---|
| contacts / car-lap Laguna / Sonoma / Buttonwillow / Mid-Ohio | 0.0248 / 0.0297 / 0.0166 / 0.0128 | **0.0400** / 0.0206 / 0.0113 / 0.0126 |
| four-off / car-lap | 0.0858 / 0.0104 / 0.0086 / 0.0104 | 0.0601 / 0.0056 / 0.0086 / 0.0068 |
| green passes | 4193 / 22490 / 10918 / 6386 | 4224 / 22542 / 10800 / 6618 |
| clearly-faster completed | 71.5 / 61.0 / 68.0 / 76.7 % | 70.7 / 61.4 / 68.2 / 75.6 % |
| pooled cell d 3-8 % / 8-15 % (g < 2 s) | 74.7 / 87.3 % (data 86.9 / 97.8) | 73.6 / 84.2 % |
| pooled passing lap, d 3-8 % / 8-15 % | 5.7 / 11.5 s (data 2.9 / 3.4) | 5.2 / 13.4 s |
| pooled wait of a clearly faster car (median / time lost per done wait) | not recorded | 13.5 s / 3.5 s (p90 19.7 s) |

Laguna contacts rise by 0.015 per car-lap, beyond the +-0.006 spread (Sonoma and Buttonwillow fall, Mid-Ohio equal; Laguna four-offs
fall by 0.026). Where: 133 contacts on 8 seeds, spread round the lap (no corner above 19), 48 of 133 in the following context
(`line/follow/follow`), mean closing speed 4.5 m/s: the field is 4.5 % quicker at the car level and the AI-driven Probe is not, so
more cars arrive from behind at the same trains. Nothing tuned; reported.

Self-play Laguna, 5 laps, seeds 1-8, the AI Probe at scale 1 (`--player-scale 1`): pace position by mean lap / by best lap
P22.3 / P14.9 (seeds 1-8 mean: 19, 34, 31, 22, 26, 25, 18, 3 / 17, 33, 7, 4, 29, 10, 4, 15); q 0.5 (27 Oct, round 1): P14.6 / P13.5.
Eyesore (#711, target 113.8 -> 111.8 s), Laguna seeds 1-8, 10 laps, lanes: race median lap / best over the new target +32.2 / +8.1 s
(C3 NOTES at q 0.5: +27.9 / +11.8 s), wait per slower car 12.9 / 49.9 s (351 waits; was 10.9 / 46.1, 411), net places per lap 1.69
(1.88); fastest quartile +32.4 / +11.3 s, wait 13.7 / 61.7 s, 1.30 (+27.9 / +10.1, 13.4 / 60.3, 1.26). Its median race lap is
144.0 s against 141.7 s before: the faster target is paid back in traffic, not kept.

**Solo hashes** (`solo_hash.ts`, planner lanes and offset identical): Laguna 8530e05a097e4a7d, Sonoma 4ac773bad171b7a2, Buttonwillow
19e2628dc499c20e, Mid-Ohio 71c58e0ef9e5bd32 (were 6b8f157f11f72166 / 288bd306e8620212 / 4f81fe2cda1b3ef5 / 6e6024a7c42062d5; they change
by design, the scales are new).

**Tests left red by the new files** (not loosened): `ai_behaviour` "planner lanes: full field, 2 laps" (clearly faster big-ratio
completed 0.714, needs > 0.72) and "planner offset: alone on track" (racing line rms 0.533 m, needs < 0.5; the first five cars
of the new Laguna file). Both pass on the q 0.5 files (42d32fd).
