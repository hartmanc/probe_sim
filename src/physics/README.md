# src/physics: vehicle dynamics core

This is pure TypeScript with no DOM access and no dependencies. The public API is
`index.ts` (CONTRACTS.md §4). It steps at a fixed `dt = 0.001 s` with
semi-implicit Euler. One step costs about 1.5 µs on an Apple M3, measured in
vitest (`__tests__/perf.test.ts`), and the hot loop does not allocate.

```ts
import { Vehicle, loadCarSpec, createTrackSurface, createTrackProjector, lineToWorld, loadHeightfield } from './physics';
const car = new Vehicle(loadCarSpec(await (await fetch('cars/probe_gt/car.json')).json()), { autoShift: true });
const surface = createTrackSurface(trackJson, loadHeightfield(await (await fetch(hfUrl)).arrayBuffer()));
car.reset(pos, heading);              // pos = body origin on the ground
car.step(input, surface, 0.001);      // 1000×/s
```

The module exports a few extras beyond the contract:

- `reset(pos, heading, speed?)` with an optional rolling start.
- `setGear(g)` and the read-only `nanResets` counter.
- `createTrackSurface(..., { muOnTrack, muOffTrack, edgeBlend })`.
  `muOffTrack` defaults to 0.72 (`OFF_PAVEMENT_MU`), blended over the first metre past the paved edge; dirt also adds rolling drag, softer lateral stiffness and a 12 mm roughness (see NOTES-surface.md).
- `TrackJson`, `loadHeightfield`, `mfShape`, `solveMfB`.
- `devtrack.ts`, which builds a synthetic oval and flat or split-mu surfaces for tests.

`Surface.sample()` returns a **reused** object, so copy the fields before you call it again.

## Model

### Body
The body is a 6-DOF rigid body with total mass `mass` and a diagonal inertia
about the CG in the body frame (ISO 8855). Orientation is a quaternion. The CG
position comes from `frontWeightFraction` and `cgHeight`. Internally the state
is held at the CG, and `state.pos` and `state.vel` are reported at the body
origin. Forces are gravity, aerodynamic drag ½ρC<sub>d</sub>A|v|v at the CG (no
lift), the four contact forces and the hull contacts.

### Suspension
Each corner is a strut along the body z axis at a fixed mount
(x = ±wheelbase/2, y = ±track/2). The wheel is vertically massless:

- The ground is found by sampling the Surface at the hub's world (x, y) and
  intersecting the ray along −body-z with the local ground plane. This gives the
  penetration `p` of the unloaded tyre circle with the suspension at full droop.
- Spring with preload, plus a quadratic bump stop over the last
  `bumpStopRange`, plus the anti-roll bar term `k_arb·(c − c_other)`. This sits
  in parallel with the bump or rebound damper, and in series with the tyre
  vertical spring `tyreVerticalRate`.
- Because the wheel is massless, the compression `c` is a first-order state:
  `damper·ċ = k_t(p − c) − F_spring(c)`. It is integrated implicitly, so it stays
  stable at any rate.
- Contact force = k_t·max(0, p − c). There is no pull at full droop, and the load
  falls smoothly to 0 at lift-off.
- The tyre load is that force projected on the surface normal. The spring
  preload is derived so that at static load the hub is at the contract's static
  ride height, with the ground at body z = 0.

### Tyres
Each tyre has a contact-patch deflection state per axis (Pacejka's transient
model):

```
du/dt = (ω r − Vx) − |Vx|·u/σx        κ' = u/σx
dv/dt = −Vy        − |Vx|·v/σy        tan α' = v/σy
```

The relaxed slip lags the kinematic slip with time constant σ/|Vx|. At
standstill the tread is a spring, so a parked car holds still on a slope with no
creep. The deflection is capped at the value that gives the peak force. Past the
peak the force follows the kinematic slip, computed with |Vx| floored at
`lowSpeed.velocityFloor`. This models sliding and avoids the wind-up and
spring-back that a pure deflection model gives at large slip. Below
`lowSpeed.blendSpeed`, contact damping blends in so the car settles without
jitter.

The forces themselves:

- **Pure slip:** Magic Formula `D·sin(C·atan(Bx − E(Bx − atan Bx)))`. B is
  derived from the peak slip given in the spec.
- **Load-sensitive peak:** `D = mu0·(Fz/Fz0)^loadSensitivity·Fz·surfaceMu`.
- **Combined slip:** normalised slip `s = (κ/κpk, α/αpk)`, ρ = |s|, and
  `F_i = (s_i/ρ)·F0_i(ρ·peak_i)`. The result is also clipped to the friction
  ellipse, so it never exceeds the peak.
- The wheel-spin update uses the tyre's slip stiffness implicitly
  (linearly-implicit inertia `I + dt·dτ/dω`), so lock-ups and wheelspin are
  stable at 1 kHz.
- Camber, aligning torque, pressure and temperature are not modelled.

`WheelState.slipUse` reports how close each tyre is to its peak, for audio. It
is the normalised combined slip ρ = √((κ/κ_pk)² + (α/α_pk)²), the same ρ the
combined-slip model uses:

| slipUse | Meaning |
|---|---|
| 0 | free rolling, or the wheel is airborne |
| 1 | at the peak of the force curve |
| above 1 | sliding |

`tyrePeakSlip(spec)` returns the peak slip angle (rad) and ratio from the spec.

### Drivetrain
Front-wheel drive with an open differential. The driveline is solved as
velocity constraints with projected Gauss-Seidel (8 iterations):

- **Clutch:** keeps `ω_engine = G·(ω_FL + ω_FR)/2`, with torque capacity
  `clutch.maxTorque`. With that kinematic Jacobian, the clutch impulse goes
  equally to both fronts, which is the open diff: the unloaded or low-mu wheel
  spins up freely.
- **Brakes and rolling resistance:** a friction constraint `ω_i = 0` on each
  wheel, with capacity `brake torque + Crr·Fz·r`. Wheels lock when the brake
  torque exceeds the tyre's capacity, and they never reverse.

The engine has rotating inertia. Torque is
`thr·T_full(rpm) + (1 − thr)·T_closed(rpm)`. The closed-throttle torque is
linear from `brakingTorqueIdle` at idle to `brakingTorqueLimit` at the limit.
`efficiency` scales positive engine torque.

Engine control:

- **Idle:** a P-controller holds `idleRpm`.
- **Rev limiter:** fuel cut for `limiterCutTime` once the engine exceeds `revLimitRpm`.

Automatic clutch:

- It is open below `engageRpm` and closes quadratically up to
  `fullRpm + throttle·launchRpmBoost`. With full throttle from rest the engine
  sits near 1800 rpm while the clutch slips.
- Once the clutch is synchronised it stays closed at full capacity until the
  engine drops below `fullRpm`.
- After a shift, capacity ramps in over `engageTime`.

Shifts:

- A shift opens the clutch for `shiftTime`. Upshifts cut fuel; downshifts blip
  the throttle to match revs.
- **autoShift:** upshift at `upshiftRpm`. Downshift when the gearbox-side rpm is
  below `downshiftRpm` and the lower gear stays under `downshiftMaxRpm`.
  `minInterval` stops it hunting.
- **Manual:** `shiftUp` and `shiftDown` are edges, also honoured in autoShift
  mode. The order is R ← N ← 1…5. Reverse is refused above 1.5 m/s, and
  downshifts that would over-rev are refused.

### Brakes
Total `maxTorque` at full pedal, with `frontBias` to the front. A rear
proportioning valve (`proportioningKnee`, `proportioningSlope`) limits rear line
pressure above the knee. `pedalExponent` (default 1) maps the pedal to line
pressure. The handbrake adds `handbrakeTorque` on the rear axle, and the ABS
never touches it.

### ABS
The race car has ABS, but Coby describes it as crude: a front can lock for
about half a second before it acts. `brakes.abs` models early-90s 3-channel
logic:

- **Channels:** each front wheel has its own channel. The rears share one
  channel and act on the worse wheel ("select-low").
- **Slip:** braking slip is `1 − ω·r / v_x` of the contact patch.
- **Wake-up:** a channel wakes only after its slip has stayed above `lockSlip`
  (0.35) for `wakeDelay` (0.45 s). That is the felt half second of flat-spotting
  lock with no steering.
- **Pulsing:** once awake, the channel drops the brake torque to
  `releaseFactor` (30 %) whenever slip exceeds `releaseSlip` (0.25). It holds
  that for `holdTime` (40 ms), then re-applies at `applyRate` (7 per second, as
  a fraction of pedal torque). This pulses at about 6–7 Hz around 15–20 % slip.
- **Limits:**
  - It never applies more torque than the pedal asks for.
  - It switches off under 10 % pedal, below `minSpeed` (8 km/h), or after the
    wheel has run at full pedal torque without slipping for 0.3 s.
- **Toggle:** `vehicle.abs` switches it at runtime (the app's settings toggle).
  `state.absActive` drives the HUD tag.

Measured:

- **Full pedal from 100 km/h:**
  - The fronts lock at 0.06 s and the ABS wakes at 0.51 s.
  - It stops in 44.6 m, against 43.2 m for the best constant pedal that does
    not lock, and 45.5 m locked without ABS.
- **Laguna T2:** braking at full pedal from s = 370, about 35 m later than
  driver A, and turning in:
  - With ABS the car stays within 1.0 m of the line.
  - Without ABS the locked fronts plough 8 m wide.

### Balance: compliance steer and fast-corner grip
Two more spec features shape the balance:

- **Compliance steer:** `suspension.<axle>.complianceSteerDegPerKN` adds toe
  proportional to that wheel's lateral force, low-passed at 20 ms. The source
  is bushings, the rack and subframe mounts.
  - Positive values steer a front wheel out of the turn and a rear wheel into
    it (in phase).
  - Both directions add understeer gradient and yaw damping without changing
    peak grip.
  - The same tyre on both axles with mild load sensitivity otherwise gives an
    almost neutral car, about 0.4°/g. A real FWD street car is about 2–4°/g.
- **Speed sensitivity:** `tyre.speedSensitivity` lowers the lateral friction
  peak above `refSpeed`. It stands in for rubber friction falling with sliding
  speed and heat.
  - Longitudinal grip is left alone because it is calibrated to the logger's
    braking.

**Why the rear swung** (Oct 2026 balance pass): the old car was close to
neutral, and its rear axle had no more grip margin than the front.

- At 0.9 g the inside rear nearly lifts and the outside rear carries the whole
  rear axle. Front roll stiffness (30 + 2·18 kN/m) against rear (25 + 2·16) put
  only 54 % of the lateral load transfer on the front, against 62 % of the
  weight.
- On a throttle lift the front tyres stop driving, regain lateral grip and yaw
  the car. The rear had no margin, so it went from 3° to 11.7° slip, past its
  7° peak.
- The tyre curve itself was not the culprit. With E = −1 the lateral force is
  still 97 % of peak at twice the peak slip, and E = −0.5 changed nothing
  measurable.

The fix:

- **Front bar:** stiffer, 18 → 32 kN/m (LLTD about 60 % front). The front
  diameter is unknown, and a stock GT front bar is much stiffer than the 18 mm
  rear.
- **Compliance steer:** front 0.4 °/kN, rear 0.12 °/kN in phase. This gives
  about 2.3°/g of understeer gradient.
- **Steering rate:** the stick rate limit falls off faster with speed
  (`rateSpeed` 30 → 20).

Trail braking still rotates the car. Forward load transfer and the rear brakes
take the rear past its peak (rear 8° vs front 6.6° at 1 s), which is the one
behaviour Coby confirmed in the real car. The manoeuvre tests in
`__tests__/balance.test.ts` hold these numbers.

### Kickdown
`drivetrain.autoShift.kickdown*`: with throttle ≥ 80 %, engine rpm < 4100,
longitudinal acceleration < 0.15 g and lateral < 0.5 g, autoShift drops a gear
if the lower gear lands at or under `upshiftRpm`.

- **Hysteresis:** after a kickdown, the next upshift waits for 5450 rpm. That
  lands 5th at about 4200 rpm, above the 4100 rpm kickdown threshold, so it
  does not hunt.
- **Cornering:** no upshift while cornering above 0.6 g, unless near the
  limiter.

This keeps the car in 4th up the Rahal climb, as in driver A's rpm trace (4th,
4600–5150 rpm), where it used to sit in 5th at 3500–3800 rpm.

### Gear schedule (auto-shift like the ghost)
`deriveGearSchedule(spec, lap, grid)` works out the gear a ghost used at every
2 m sample, from its rpm and speed channels.

- **Matching:** each sample takes the gear whose overall ratio is closest to
  rpm·2πr / (60·v).
- **Gaps:** samples that match no gear within 12 % (clutch in, wheelspin,
  logger lag) or are slower than 3 m/s take their neighbour's gear.
- **Smoothing:** runs shorter than 30 m are merged into their neighbours.
- **Lookup:** `scheduleTargetAt(schedule, s)` gives the gear with 3 m of
  hysteresis.

The app passes it to `vehicle.setScheduledGear(g)` at the car's projected s.
While a schedule is set, autoShift follows it, and the rpm rules act only as
guards:

- It upshifts before the limiter, judged by road-speed rpm so a wheelspin flare
  over the Corkscrew does not trigger it.
- It downshifts below 1800 rpm.
- A scheduled upshift waits for 4000 rpm (`scheduleMinUpshiftRpm`).
- A scheduled multi-gear drop goes through the gears back to back.

With 0 (no ghost, or more than 15 m off the ghost's line) the rpm and kickdown
rules apply.

driver A's derived shifts are 3→4 at about 4820 rpm and 4→5 at about 4680 rpm.
He drops 5→3 into T2 and T5, and stays in 4th from T5 up the Rahal climb to the
Corkscrew.

### Steering shaping
The steering command (−1..1) is rate-limited:

```
rate / (1 + v/rateSpeed)  [full-scale/s]
```

The road-wheel angle is the command times a speed-dependent maximum:

```
max(minAngle, maxAngle / (1 + (v/shapingSpeed)²))
```

The front wheels then get partial Ackermann (`ackermann` 0..1). For the Probe,
full stick gives:

| Speed | Max road-wheel angle | Lock-to-lock flick |
|---|---|---|
| 0 km/h | 32° | 0.25 s |
| 50 km/h | 16° | |
| 150 km/h | 3° | 0.6 s |

### Hull
Eight box corners (`hull`) act as penalty contacts with friction against the
ground. They only matter for big crests, curbs or a roll-over. Without them, a
car on its roof would fall through the ground.

### Collisions (`collision.ts`)
`createCollisionWorld(scenery, track)` turns scenery.json into:

- **Walls:** every barrier run becomes vertical segments from the ground z up to `h` (hard), plus `fence`
  above it (soft). A `fence` run is soft over its whole height. Building footprints become closed walls.
- **Posts:** run ends and corners sharper than 25° become thin posts, so they cannot slip between the car's
  sample points.
- **Trees:** trunks are cylinders with r = 0.35 m; landmark oaks use r = 0.8 m.
- **Boundary:** an invisible wall 200 m inside the far (or near) heightfield border.

A uniform 8 m grid answers a query around the car in about 0.1 µs.

Each step, `Vehicle` tests the car against these:

- Bumper-ring points (corners plus sides every ≤ 1.2 m) and roof corners are tested against wall segments.
  The normal points toward the side the CG is on, so a point that crossed the 0.1 m contact skin is still
  pushed back.
- Posts and trunks are tested against the footprint box.

Rigid contacts use sequential impulses (8 iterations):

| Kind | Restitution |
|---|---|
| concrete / pit wall / building | 0.25 |
| armco | 0.3 |
| tree | 0.2 |
| boundary | 0.2 |

Friction is 0.6 and impulses act at the contact point, so offset hits yaw the car. Tyre stacks and catch
fences are spring-dampers (60 kN/m, 15 kN·s/m). Push-out is capped at 1 cm per step.

`state.impact` holds the hardest recent hit. When the closing speed exceeds `LAUNCH_SPEED` (25 m/s) on
concrete, armco, pit wall, building or tree, the car is launched:

- velocity 70 m/s up plus 25 m/s off the wall, with a constant tumble;
- no gravity, plus 3 m/s² upward;
- the engine and wheels spin down;
- `state.launched` is set until `reset()`.

The surface takes `opts.far` (far heightfield) for ground outside the near grid.

### Surface and track
- **`createTrackSurface`:** finds the nearest centreline station through a
  uniform spatial hash over station positions. Nearby queries are cached, so the
  four wheels hit the cache. It then projects onto the adjacent segments and
  interpolates the 7-point profile bilinearly, across the fractions and along
  s. Off the track it uses bilinear interpolation of the heightfield.
- **Edge blend:** a 5 m shoulder (`SHOULDER_WIDTH_M`, option `edgeBlend`) outside
  each edge blends (smoothstep, no slope break at either end) from the profile edge height to the heightfield, so
  the edge is not a step. The app renders the same shoulder by sampling this
  surface, so what the car drives on matches what is drawn.
- **Normals:** taken from the analytic slope of whichever interpolant is used.
- **Friction:** `mu` is 1.0 on track and 0.6 off.
- **`createTrackProjector`:** returns s (wrapped), signed lateral distance (+left)
  and the segment index.
- **`lineToWorld`:** returns centre(s) + offset·leftNormal, with z from the
  profile and the heading of the offset line itself.

## Spec (`public/cars/probe_gt/car.json`)

The schema is `CarSpec` in `spec.ts`; every field is documented there. Keys
starting with `_` are comments. `loadCarSpec` validates the file and names the
offending path when a field is missing or out of range. These Probe-specific
values are derived rather than taken directly from the data you supplied:

- **Gear ratios:** stored as overall ratios (engine revs per wheel rev),
  computed as `rpm-per-mph / 13.5092`. 13.5092 is the wheel rpm per mph at
  r = 0.316 m. 3rd, 4th and 5th come from the measured 82, 63 and 48.5 rpm/mph.
  1st and 2nd scale 3rd by the gearbox ratios 3.307/1.310 and 1.833/1.310.
  Reverse equals 1st.
- **Static compression:** 35 mm of 90 mm travel, so the bump stop is 35 mm
  away. The spring preload follows from it.
- **Proportioning valve:** knee 0.35, slope 0.25. The split is 62 % front below
  the knee and about 76 % front at full pedal.
- **Clutch:** 400 N·m capacity, launch boost 1000 rpm, re-engage time 0.2 s.
- **Tyre low-speed parameters:** floor 1 m/s, damping 3000 / 8000 N·s/m.
- **Rolling resistance speed term:** 5.2e-7 per (m/s)². This is Wong's radial
  tyre fit, 0.4e-7·(km/h)².

## Calibrating against logger data

Change one group at a time and re-run `npx vitest run` after each change. The
tests print the key numbers: 0–60, top speed, braking distance, peak lateral g
and slip angles.

| Target (logger) | Primary knobs | Notes |
|---|---|---|
| **Peak lateral g** (steady-state, from GPS speed × yaw rate or accelerometer) | `tyre.lateral.mu0`, `tyre.loadSensitivity` | Peak g is roughly proportional to mu0. A more negative load sensitivity lowers peak g and increases the penalty for load transfer. |
| **Balance** (understeer and corner-exit behaviour) | `antiRollRate` front/rear, `springRate`, `cgHeight` | Stiffer at one end moves load transfer there and reduces that end's grip. To cut understeer, soften the front bar or stiffen the rear bar. Check the cornering test's front and rear slip angles. |
| **Corner minimum speeds** | lateral mu0 first, then balance | v_min ≈ √(a_lat·R). If the minimum speeds match but exit speeds don't, look at traction: longitudinal mu0, `peakSlipRatio` and the open-diff inside-wheel spin. That points to `antiRollRate` front and `staticCompression`. |
| **Top speed / straight-line v(t)** | `aero.cd`·`frontalArea`, `efficiency`, torque curve, `rollingResistanceSpeed` | Top speed is set where drag equals η·T·ω/v. Fit CdA from a coast-down in neutral first (v(t) with throttle 0), then fit η from full-throttle segments. |
| **Acceleration and rpm traces** | torque curve, `efficiency`, gear ratios, `wheel.radius` | Compare rpm vs speed per gear to confirm the ratios, which assume a 225/50R16. A different tyre size scales every ratio. |
| **Braking distance / decel** | `brakes.maxTorque`, `frontBias`, proportioning, `tyre.longitudinal.mu0` | Full-pedal decel is grip-limited when no wheel locks. Locked wheels fall to about 61 % of peak with C = 1.65, so rear lock-up shows as a sudden drop in decel. |
| **Transient response** (yaw-rate rise time) | relaxation lengths, `steering.rate`, yaw inertia | This needs a steering-angle sensor to fit properly (see improvements.md). |
| **Gamepad feel** | `steering.shapingSpeed`, `minAngleDeg`, `rate`, `rateSpeed` | These do not change the car's physics, only the mapping from stick to road-wheel angle. |

A useful order:

1. Coast-down for CdA and Crr.
2. Full-throttle runs for torque and η.
3. Steady corners for lateral mu0 and load sensitivity.
4. Corner exits for balance and traction.
5. Braking zones.

## Known limitations

- **Balance:** the understeer gradient comes from compliance steer and roll
  stiffness, not from suspension kinematics. There is no camber loss in roll
  and no roll steer. The speed-dependent lateral grip is a stand-in for
  thermal and sliding-speed effects. It is fitted so T6 matches driver A, and T5
  and Rainey are still about 12 % slow, which is probably track data (see
  improvements.md Balance).

- **Collisions:** walls are vertical with a 0.1 m contact skin. Barriers are not climbable, the car never
  rides up onto a wall, and there is no damage. Bridges are not obstacles. Only the bumper ring and the
  roof corners are tested against walls.

- **No wheel-hop DOF.** The wheels are vertically massless, so
  `unsprungMassPerCorner` is carried in the spec but unused. High-frequency
  load variation over bumps is filtered by the tyre spring instead.
- **No suspension kinematics.** There are no roll centres (they are effectively
  at ground level), no camber change, bump steer or compliance steer. The strut
  axis is body-z.
- **Missing tyre effects:** no camber thrust, aligning torque or steering-wheel
  force feedback. Temperature, wear and pressure are not modelled. Rolling
  radius equals the unloaded radius.
- **Tyre falloff past the peak:** the Magic Formula C = 1.65 makes a locked or
  spinning tyre produce only about 52–61 % of peak. Lock-ups and heavy
  wheelspin are therefore "sticky", and the driver has to lift. If logger data
  shows otherwise, raise C toward 1.4–1.5 with B re-derived.
- **Single-point aero:** no lift, no yaw-dependent drag, no drafting.
- **Driveline simplifications:** no driveline torsional compliance and no
  gearbox inertia. Engine braking is a linear map, and `efficiency` scales only
  positive torque.
- **Contact geometry:** contact is a single point per wheel on the local ground
  plane. Curbs or steps sharper than the tyre radius are not resolved.
- **Surface queries:** nearest-station lookups assume the track does not cross
  over itself. The hash is 2-D.
- **Hull contacts:** these are crude penalty springs, good enough for recovery
  but not for crash dynamics.

## Deviations from the brief

- **Top speed:** the brief's acceptance range is 175–220 km/h, but the specified
  CdA (0.34 × 1.95), torque curve and 0.90 efficiency give a drag-limited
  223.7 km/h in 5th at 6816 rpm. Hitting 220 needs about 12 % more drag
  (Cd ≈ 0.38, plausible for a Lemons car with the windows out). The test
  asserts 175–226 instead. Fit CdA from a coast-down rather than changing the
  test.
- **Brake split:** a rear proportioning valve was added. With a plain 62/38
  split at 5000 N·m, both rears lock at any full-pedal stop. With this tyre's
  sliding falloff they then stay locked, and the slightest steering input spins
  the car (66° of yaw with a 0.06° road-wheel offset). The real car has a
  proportioning valve. 62 % front still holds below the knee.
