# Improvements and data wishes

Things that would make the sim more accurate, and what we are assuming until
we have them. Add to this as you find gaps.

## Measure on the car

- **Differential**: assumed open (stock for a US 1993–97 Probe GT; the LSD
  version of the G25M-R gearbox was JDM-only). Check: jack both fronts, spin one
  wheel; if the other turns the opposite way it is open.
- **Corner weights with a driver**: assumed 1380 kg total, 62/38 front/rear.
- **Spring rates, damper types, ride heights**: assumed 30/25 N/mm front/rear,
  stock-ish ride height. Stock or aftermarket springs? Which struts?
- **Sway bars**: rear is a ~18 mm Contour/Mystique bar (Oct 2026 session);
  front diameter unknown, assumed stock.
- **Tyres**: model, size and pressures unknown. Assumed 225/50R16 200-treadwear.
  The measured rpm-per-mph gearing assumes that size; a different size shifts
  the derived ratios.
- **Brake pads and bias**: 70 % front below the proportioning-valve knee (calibrated).
- **ABS**: present but crude (Coby: a front can lock for about half a second
  before it acts; ABS was an option on the 1993 GT and this car has it).
  It is modelled as early-90s 3-channel ABS with a 0.45 s wake-up delay, on by
  default with a settings toggle. See the Balance section and
  src/physics/README.md "ABS". The pump cycle rate and the real wake-up delay
  are guesses.
- **Alignment**: camber and toe unknown; sim assumes 0 toe, -1° front camber.
- **Fuel load per stint**: unknown; the sim runs a fixed 25 kg.

## Logger data wishes (next race)

- 10 Hz GPS with the receiver's own timestamps (the Dual XGPS160 the team
  owns). 1 Hz GPS could not resolve the racing line, so Laguna ghosts run on a
  synthesized line with real timing and speed.
- Steering angle sensor. Without it transient behaviour can only be checked
  loosely against yaw rate.
- Brake pressure or at least a brake light signal.
- Throttle sensor scale: the OBD channel tops out at 95 %; treat 95 as full.
- Wheel speed (one front, one rear) would nail gearing and wheelspin.

## Track

- Lidar at 1 m does not resolve kerb profiles; kerbs are modelled parametrically.
- No pit lane in the MVP.

## Car model

- Exterior and interior hand-built in Blender from dimensions and race video.
  Photogrammetry (Apple Object Capture on this Mac) planned when the car is
  accessible: 60-photo walkaround on an overcast day plus interior photos.
- Livery modelled from seven race-weekend photos in tools/car/reference (Oct 2026). Still missing: a straight-on rear view, the roof from above, interior photos from the driver's seat, and a side profile shot square-on with a tape measure for proportions.

## Calibration

Done with `tools/calibrate/drive.ts` (autopilot on the ghost racing line, real physics at 1 kHz, real
track); details and how to run it in `tools/calibrate/README.md`; speed overlay in
`tools/calibrate/compare.png`. Truth: the driver A lap (1:59.32) and the optimal lap (1:57.99).

**What was tuned in `car.json` (before → after) and why**

| Field | Before | After | Reason |
|---|---|---|---|
| `aero.cd` × `frontalArea` | 0.34 × 1.95 (CdA 0.66) | 0.50 × 2.25 (CdA 1.125) | Logger full-throttle a(v) and the straight speed gains. Roof rack, sculpture and aliens add area, windows out add Cd. |
| `tyre.lateral.mu0` | 1.15 | 1.25 | Corner speeds; gives ~1.2 g steady state on the skidpad, the top of plausible for a 200TW tyre. |
| `tyre.longitudinal.mu0` | 1.10 | 1.20 | Braking margin, consistent with lateral. |
| `tyre.longitudinal.C` | 1.65 | 1.45 | A locked tyre kept only 52 % of peak, so any lock-up stayed locked (sticky lock at T11 and T2). It now keeps ~75 %, typical for dry asphalt. |
| `brakes.maxTorque` | 5000 | 6000 | At 5000 N·m the fronts were torque-limited at 0.96 g, only 4 % over the logger's peak of 0.92 g. Now grip-limited at 1.02 g (+11 %). |
| `brakes.frontBias`, `proportioningKnee`, `proportioningSlope` | 0.62 / 0.35 / 0.25 | 0.70 / 0.25 / 0.30 | The rear was over-braked (38 % at 0.5 g against a ~28 % rear load share). Trail braking locked the inside rear and spun the car. The split is now 70 % → 80 % front, close to ideal. |
| `suspension.travel`, `staticCompression` | 0.090 / 0.035 | 0.160 / 0.070 | 35 mm of droop let the inside rear reach full droop and lift under trail braking. 70 mm droop and 90 mm bump is typical strut travel. Lap 0.8 s faster and fewer excursions. |

Unchanged on purpose: the torque curve, `efficiency` and the autoShift rpm. The logger cannot separate power
from drag without a coast-down (`accel_fit.py`: torque scale 0.85–1.0 with CdA 0.77–1.38 fit equally well,
rms 0.06 g). The vitest open-diff wheelspin test needs stock torque, and the 0-60 test needs the 6750 rpm
autoShift. The drivers short-shift at ~5000 rpm (the ghosts never exceed 5450), so the autopilot does that
itself (`--upshift 5000`).

**Result** (`drive.ts --alat 1.4 --learn 25`, clean lap, max 0.96 m off the line, no wheel off track):
lap **2:00.89** (target 1:55–1:59). Front straight at s = 300: **141.2 km/h** (driver A 139.2, optimal 140.7;
the ghosts top out at 140–141, not the 145–149 of the single logger max). Flat-ground top speed 190 km/h.

| Corner (min speed, km/h) | driver A | Optimal | Sim | vs driver A | vs optimal | Line radius | Ghost lateral g implied |
|---|---|---|---|---|---|---|---|
| T2 Andretti | 66.6 | 64.3 | 66.4 | −0.4 % | +3.3 % | 26 m | 1.56 |
| T3 | 88.8 | 88.8 | 88.9 | +0.1 % | +0.1 % | 49 m | 1.34 |
| T4 | 107.2 | 107.2 | 108.3 | +1.0 % | +1.0 % | 73 m | 1.25 |
| T5 | 95.8 | 95.2 | 85.3 | −10.9 % | −10.4 % | 43 m | 1.68 |
| T6 | 116.3 | 118.1 | 93.4 | −19.7 % | −20.9 % | 49 m | 2.19 |
| Corkscrew T8/8A | 63.2 | 62.9 | 55.5 | −12.2 % | −11.8 % | 21 m | 1.54 |
| T9 Rainey | 106.5 | 108.9 | 101.9 | −4.2 % | −6.4 % | 68 m | 1.33 |
| T10 | 101.0 | 98.8 | 96.6 | −4.4 % | −2.3 % | 55 m | 1.55 |
| T11 | 57.9 | 53.5 | 47.4 | −18.2 % | −11.5 % | 16 m | 1.80 |

- **Acceleration.** This is the distance each trace needs to gain the same speed range on a straight. Front
  straight, 60→138 km/h: sim 543 m, driver A 590, optimal 540. T2→T3: 159 m vs 172/174. Rainey→T10: 89 vs 91/111.
  T3→T4, T4→T5 and T5→T6 come out 5–15 % weaker, because the sim is grip-limited coming out of the corners
  before them. Corkscrew→Rainey and T10→T11 come out 10–20 % stronger: these are downhill and short, so the
  numbers are sensitive to the grade and to where the logger's s sits.
- **Braking.** The logger's peak decel per zone is 0.90 g into T11, 0.73–0.76 into T2 and 0.68–0.71 into the
  Corkscrew. The sim reaches 1.02 g threshold-braking on flat ground (pedal 0.85, no lock), and 1.01 g in the lap.
  The drivers lift and brake earlier and more gently than the autopilot (see `compare.png`), so there is margin.

**What remains off, and what data would fix it**

- **T5, T6, Corkscrew, T11 (and part of T9/T10) cannot be matched with plausible tyres.** On this racing line the
  ghost minimum speeds imply 1.5–2.2 g of lateral acceleration (T6: 116 km/h on a 49 m radius). The car pulls about
  1.2 g. Even mu0 1.35 leaves T6 at −23 %. The ghost speeds are internally consistent: Σ ds/v matches the lap time
  to 2 %. So the fault is the geometry. The track centreline (OSM) and the min-curvature line have local radii
  that are too tight at these corners: the centreline radius at T6 grows from 24 m to 37 m as the chord is
  lengthened from 10 m to 40 m, which is a digitising kink. The line is also kept 1 m inside the edges, with no
  kerb use. Either of these would fix it:
  1. Build `line.offset_m` 100 % from the good-GPS laps' measured line (today it is 30 %), or better, from a
     dual-antenna or RTK GPS track.
  2. Log lateral g (IMU) so each corner's real radius is known: R = v²/a_y.
  Then re-run `drive.ts`; the tyre value should not need to move.
- **Lap time 2:00.9 vs 1:55–1:59.** The gap is entirely those corners (`compare.png` lower panel: −10 to −23 km/h
  through T5–T6 and Rahal). The straights and T2–T4 match.
- **Power vs drag are not separately identified.** A coast-down in neutral on the front straight (v(t), throttle 0)
  would pin CdA and Crr. The full-throttle runs then give the torque scale. The current split (stock torque,
  CdA 1.125) is one of a family that fits equally well.
- **Gamepad steering shaping limits the car.** `steering.shapingSpeed` 13.4 m/s caps the road-wheel angle at 4.8° at
  116 km/h and 3.4° at 140 km/h. T6 and T1 at the limit need more than that, so a gamepad player cannot drive the
  car to its grip limit there. The autopilot bypasses it. Consider raising `shapingSpeed` to about 18 m/s, or making
  the cap follow the grip limit (δ_max ≈ L·a_lat/v² + the slip-angle allowance).
- **Track surface.** At 45 m/s the lidar profile's vertical curvature gives ±0.5–1 g load spikes on some wheels: on
  the front straight before T2, and through Rainey (11 kN on one wheel). This makes the limit car nervous. Smoothing
  the profile along s over about 5 m (`tools/track`), or a kerb/bump model, would separate real bumps from DEM noise.
- `src/physics/README.md` still quotes the old brake split (62 % / 76 %) and the 35 mm static compression. The values
  now live in car.json with `_` comments. No physics bugs were found: every failure traced to the controller,
  the steering shaping or the tuning values.

## Calibration, second pass (after the centreline rebuild, 17 Oct 2026)

With the v2 centreline (corner radii now match the GPS-driven line) the tyre
grip came back down from 1.25/1.20 to 1.10/1.08 lateral/longitudinal mu0,
which is what the logger implies (0.8-1.1 g in most corners). Autopilot lap on
the driver A racing line: 1:59.24 against driver A 1:59.32 and the 1:58.00 optimal.
Front straight 141 km/h vs 139-141 real.

| Corner | driver A km/h | Sim km/h | Diff |
|---|---|---|---|
| T2 | 66.6 | 65.8 | -1 % |
| T3 | 88.8 | 87.9 | -1 % |
| T4 | 107.2 | 110.1 | +3 % |
| T5 | 95.8 | 83.9 | -12 % |
| T6 | 116.3 | 122.3 | +5 % |
| Corkscrew | 63.3 | 64.3 | +2 % |
| Rainey | 106.5 | 92.1 | -13 % |
| T10 | 101.0 | 100.4 | -1 % |
| T11 | 57.9 | 57.6 | -1 % |

Still off: T5 and Rainey, where the real car pulled 1.1-1.2 g with the banking.
Either the tyre is better than 1.1 g at those loads and speeds, or the local
banking/radius in the data is still slightly wrong. A 10 Hz GPS and a steering
sensor at the next race would settle it. The autopilot also drifts 0.9 m off
the line on the Rainey downhill, which caps its speed there.

## Balance (Oct 2026, after Coby's gamepad laps)

Coby's report on the real car: a stable, understeering FWD that only swings
out under trail braking. It can brake super late at T2 and still turn in, it
is not flat through T6, and it does not lose time up the hill. The sim was the
opposite on each count.

### What made the rear swing

The car was almost neutral, at about 0.4°/g of understeer gradient. Two things
caused that:

- **Load transfer:** the front-to-rear roll stiffness split put only 54 % of
  the lateral load transfer on the front, against 62 % of the weight. At 0.9 g
  the inside rear nearly lifts.
- **No understeer source:** with the same tyre front and rear and mild load
  sensitivity, nothing else added understeer.

A throttle lift at 0.9 g took the rear from 3.0° to 11.7° slip, well past its
7° peak.

These were checked and ruled out:

- **Lateral curve falloff:** E −1.0 keeps 97 % of peak at twice the peak slip.
  E −0.5 made no measurable difference.
- **Load sensitivity:** −0.2 helped only slightly.
- **Lift-off engine braking:** a small effect.

### Changes (car.json)

| Value | Before | After |
|---|---|---|
| Front anti-roll bar wheel rate | 18000 N/m | 32000 N/m |
| Front compliance steer (toe-out of the turn) | 0 | 0.40 °/kN |
| Rear compliance steer (in phase) | 0 | 0.12 °/kN |
| Steering rate fall-off `rateSpeed` | 30 m/s | 20 m/s (full flick 0.6 s at 100 km/h) |
| Lateral grip vs speed `tyre.speedSensitivity` | none | −1.8 %/(m/s) above 28 m/s (−10 % at 121 km/h) |
| ABS | none | 3-channel, 0.45 s wake-up, on by default |
| Kickdown | none | thr ≥ 0.8, rpm < 4100, < 0.15 g accel, < 0.5 g lat; hold to 5450 rpm |
| Upshift | always at 5000 | not while cornering above 0.6 g |

The front bar diameter is unknown (see "Measure on the car"). A stock GT front
bar is much stiffer than the 18 mm rear, so the stiffer front value is the
better guess.

### Manoeuvres

Flat surface at 100 km/h, from `src/physics/__tests__/balance.test.ts`:

| Manoeuvre | Before | After |
|---|---|---|
| Step steer to 0.9 g: yaw overshoot / rear slip | 56 % / 9.2° | 27 % / 3.8° |
| Full-stick step: max body slip | 7.6° | 5.0° |
| Throttle lift at 0.9 g: rear slip | 3.0 → 11.7° | 2.7 → 3.7° |
| Sine steer 1 Hz ±60 %: max body slip | 6.5° | 3.7° |
| 2nd-gear full-throttle exit: path curvature / inside slip | ×0.51 / 0.99 | ×0.51 / 1.45, body slip ≤ 1° |
| Trail-braked turn-in, 40 % at 0.8 g: rear vs front slip at 1 s | 5.7° vs 4.6° | 8.0° vs 6.6° (rotates, max body slip 12°, no spin) |

The step overshoot is still 27 %, above the ~20 % target. That is the
transient of a stick step beyond the front limit; below the limit it is about
18 %.

### ABS and T2

These numbers are from a line-following driver on the real track.

- **driver A's braking point (s ≈ 335) at 70 % pedal:** no front lock, within
  0.7 m of the line.
- **About 35 m later, full pedal and turning in:**
  - With ABS the fronts lock for 0.57 s, then the car follows the line within
    1.0 m.
  - Without ABS the fronts stay locked and the car runs 8 m wide.
- **100–0 km/h:** ABS 44.6 m, best non-locking pedal 43.2 m, locked 45.5 m.

The progressive pedal map (`pedalExponent`) was not needed once ABS was in,
and stays at 1.

### T6 grip

The vertical wheel loads do vary through T5–T6 on the v2 track (sum of the
four wheel loads / mg, autopilot lap):

| Location | Load factor |
|---|---|
| T5 compression (s 1510–1610) | 1.04–1.09 |
| T6 crest (s 1925–1930) | 0.87 |

The centreline then dips 0.4 m right at the T6 apex (z 17.05 → 16.66 m over
s 1920–1944, inside edge lowest). That gives a load factor of 1.18 at 121 km/h,
exactly where the car needs the grip. If that dip is a DEM artefact rather than
real, the track data over-grips T6. Worth checking in the next track build.

With the data as it is, the sim pulled 1.12 g at T6 against driver A's 1.0 g, and
went through flat at 122 km/h. The fix is the speed-dependent lateral grip
above. It brings the autopilot's T6 to 115.7 km/h (driver A 116.3). T5 and Rainey
are still about 12 % slow (a data limit, see the second calibration pass).

### Rahal climb: gear and power

driver A climbs from T6 to the Corkscrew in 4th at 4600–5150 rpm. The sim sat in
5th at 3500–3800 rpm; kickdown and the cornering upshift inhibit fix that.

The joint torque-scale / CdA fit (`tools/calibrate/fit_power.ts`) runs full
throttle from the ghost exit speed over the real grade, averaged over three
start points. Speed gain in km/h, driver A / optimal / sim:

| Straight | Before (5th on the climb) | After |
|---|---|---|
| Front, T11 → T2 | 78.5 / 85.8 / 87.8 | 78.5 / 85.8 / 84.2 |
| Rahal, T6 → Corkscrew, 28 m rise | 16.1 / 13.9 / 14.0 | 16.1 / 13.9 / 13.5 |

- **Kickdown in the autopilot:** the Rahal gain went from 3 to 14 km/h from
  T6 exit.
- **No torque scale needed:** torque ×1.00 and CdA 0.50×2.25 match both
  straights within 2 km/h of the ghost mean.
- **driver A and the optimal ghost disagree:** they differ by 7 km/h on the front
  straight, so no single torque/CdA fits driver A on both.
- **Higher torque makes it worse:** ×1.05–1.1 helps Rahal but overshoots the
  front straight.

### Autopilot

`npx tsx tools/calibrate/drive.ts --alat 1.2 --learn 25 --bank`: 1:59.62,
against 1:59.24 before this pass and driver A's 1:59.32. Corner minimums:

| Corner | Sim | driver A |
|---|---|---|
| T2 | 64.8 | 66.6 |
| T3 | 87.6 | 88.8 |
| T4 | 107.6 | 107.2 |
| T5 | 83.5 | 95.8 |
| T6 | 115.7 | 116.3 |
| Corkscrew | 63.4 | 63.3 |
| Rainey | 94.1 | 106.5 |
| T10 | 100.8 | 101.0 |
| T11 | 55.2 | 57.9 |

Two changes to the autopilot came with this pass:

- **Understeer feed-forward:** the autopilot now adds steering in proportion
  to lateral g, about 2.3°/g measured on the flat at start-up. Without it the
  pure-pursuit driver runs wide in an understeering car and learns slower
  corners.
- **Rahal gain still low:** the autopilot's own Rahal gain stays at about
  9 km/h because its target-speed profile caps the climb at 124 km/h. That is
  a profile artefact; the car can do more, as the fit above shows.

### Auto-shift follows the reference ghost (Oct 2026)

Coby asked for the shift points to match where driver A shifts, not a fixed
5000 rpm. Auto-shift now follows the gear schedule derived from the selected
reference ghost's rpm and speed channels (`deriveGearSchedule`). It falls back
to the rpm rules when the car is more than 15 m off the line.

Derived shift rpm (median per transition):

| Ghost | Upshifts | Downshifts |
|---|---|---|
| driver A | 3→4 4821, 4→5 4682 | 5→3 3207, 4→3 3505 |
| Optimal | 3→4 5027, 4→5 4594 | — |
| Coby | 3→4 4821, 4→5 4821, 2→3 5401 (2nd only at T11) | — |

The other ghosts shift between 3400 and 5040 rpm.

**Chrome lap:** a scripted in-page driver on the driver A schedule shifted at
s 445, 911, 1267, 1531, 1661, 2421 and 2595. driver A shifts at 442, 908, 1264,
1528, 1658, 2418 and 2592, so each is 3 m later (the hysteresis). Upshifts came
at 4400–5200 rpm.

**Autopilot:** the track was rebuilt at 10:56, so these use the current track.
`drive.ts --alat 1.2 --learn 25 --bank`:

| Shifting | Lap |
|---|---|
| rpm rules | 2:00.32 |
| `--schedule driver_a` | 2:01.13 |

With the schedule the lap is 0.5 s faster everywhere except T6 and the Rahal
climb, which lose 1.3 s. On driver A's schedule the car is in 4th through T6, and
the autopilot holds full throttle at the apex, where driver A lifts (his throttle
reads 3–30 % there). The FWD car then pushes wide, and the learning lowers its
T6 speed to about 100 km/h. A human lifting there does not lose that time.

## Track surface history (checked 17 Oct 2026)

- Full repave finished June 2023 (first since 2006/07). The lidar is from 2017, so
  the 0.4 m sag the survey showed at the T6 apex was removed and replaced with a
  smooth crest (Coby: T6 is a crest you cannot take flat).
- 2025 (KSBW report, Friends of Laguna Seca): runoff areas paved and drainage
  rebuilt, Trylon LED panels, garages and suites renovated. Our aerial imagery may
  predate the runoff paving; corners whose runoff is now asphalt should get full
  grip and an asphalt look in the sim. Ask the drivers which corners.

## Field cars and the AI race (17 Oct 2026)

Formats are in CONTRACTS §3b and §4e. This section records what is assumed and what data would help.

### Identifying the field

- **Speedhive / MYLAPS has no make or model**, only number, team, class, grid, laps and lap times. Make, model and
  year come from Lemons award pages (as declared by the team, and often a joke: #20 "1951 Ford Mach 1" is a K-car
  wagon), from a few web articles, and from 400 px race photos (`tools/cars/field/NOTES.md`).
- **Identity confidence** (`confidence` in identity.json): 32 high, 11 medium, 2 low. Least certain: #55 (Dodge
  B-series pickup, or a Ford F-1 or Studebaker), #34 (Geo Metro with a Mercedes grille, guessed from team history),
  #169 (E70 Corolla wagon), #200, #100, #2 and #97 (from photos only).
- **Engine guesses are the weakest field** (`engine.confidence`: 17 high, 19 medium, 9 low). "Low" means a swap is
  likely but the donor is unknown, so the stock engine is kept (#49, #51, #41, #906, #55, #544). Confirmed swaps:
  #0 1JZ-GTE, #74 GM V8, #8 2.5 L Opel CIH. The physics floors power at 70 % of the Probe's power-to-weight.
- **Dimensions** are infobox-level (about ±2 % on length and width, ±10 % on mass), stock curb weight. Lemons cars
  are gutted and caged, roughly ±5 % net.
- **Data wishes:** a short questionnaire to the teams (engine as raced, weight with driver, tyre size and
  treadwear); a side photo of each car in the paddock; the announcements file, for a log of full-course yellows.

### AI pace

- **Pace-in-traffic gap.** Each car's target is its median green lap, which already includes the time it lost in
  traffic. `calibrate_field.ts` fits each car to that target **alone on track**, and in a race the AI then loses
  traffic time again. In-race AI laps are therefore probably slower than the real ones (traffic counted twice).
  This has not been measured against the real lap chart. Fixes: calibrate to a traffic-free statistic (for example
  the 25th percentile of green laps), or fit the scales from a whole-field `tools/race/sim_race.ts` run.
- Pace differences are modelled as car capability (power, grip). Every AI drives at the same fraction of its own
  grip, and the only per-driver variation is `aggression` and `sigma`.
- The player's real best (1:59.3) beats #619's own median (2:08.7), so a good player gains places that the real
  #619 did not.
- The real grid puts very slow cars at the front (#20 at P1 runs 2:51), so the first laps are busy, as in the race.
- The penalty box is in the middle 40–70 % of `pit_lane.parts[0]`, a guess. **Data wish:** the real stop-and-go
  position.

### Field car models

- **No true side photo exists for many cars.** Commons often has only 3/4 views (#0 Corona, #2 Saturn, #156 Milan,
  among others). Those specs use near-side photos with `wheel_px` yaw correction, or a long-lens race photo of the
  car itself, so their proportion check is weaker than the 5 % gate suggests.
- Race photos are 400 px (XL copies carry a watermark), so stickers and small text are often unreadable. Only the
  Probe has owner photos.
- **Kit limits** (from the specs' `theme_details`):
  - no transparent prop material (#89's bubble dome is drawn as hoops);
  - the scratch kit cannot cut or remove a bumper (#37's torn-off bumper is simply not built);
  - bumpers take no decals (#963's TOW plate is a board prop);
  - the importer's `cut` removes faces but builds no new panels (wagon from a sedan, ute cuts: #169, #670, #963);
  - no fender `flare` parameter, chrome is a light grey swatch, and the importer does not detect `forward_axis`.
- **Licences.** Some imported bases are CC BY-NC or BY-NC-SA (#8 and #16 so far), accepted by the owner for a
  non-commercial site. If the site ever becomes commercial, those cars must be rebuilt.
- **Two credits files (wart).** `public/cars/field/credits.json` (model bases, `{about, cars: {num: {...}}}`,
  written by `import_model.py`) and `public/cars/field/models/credits.json` (images, `{num: [...]}`, written by
  `build_car.py`) have different shapes and writers. The image list can repeat an entry. Consumers must merge both
  (CONTRACTS §3b). Better: one file with `{cars: {num: {model, images: []}}}` that both tools update. No credits
  screen was found in `src/app` when this was merged; CONTRACTS §5f is its contract.
- **Player Probe:** no cleanly licensed 2nd-gen Probe model exists (the candidates are a Humster3D re-upload and an
  Assetto Corsa rip), so the hand-built `probe.glb` stays. Its driver view is cramped: the header and cage bar sit
  low and the wheel rim is 0.35 m from the eye (a seated driver is about 0.5 m away; `src/app/NOTES-camera.md`).
  **Data wish:** photos from the driver's seat with a tape measure in frame.

### Field audio

- **No onboard footage of the other cars.** Their engines come from 13 families cut from online videos of similar
  engines (`tools/audio/families/sources.json`), not from the cars themselves. A car's voice is only as right as
  its engine guess.
- The families have no AAC fallback, so AI cars are silent where Ogg Opus does not decode (older Safari). The
  level against the player's engine is not tuned, so the field stays behind `?fieldaudio=1`.
- **Data wish:** a phone recording of each car in the paddock or on a straight at the next event.

### Determinism and tests

- **Safari / Firefox float drift.** Hot-lap replays are validated by the server in Node (V8). `Math.sin`, `cos`,
  `atan2`, `exp` and `pow` need not be correctly rounded, so JavaScriptCore or SpiderMonkey can differ in the last
  bit, and a long lap could drift past the 0.05 s tolerance. Untested. If Safari or Firefox players see "lap time
  differs" rejections, add deterministic math helpers to `src/physics` (or widen the tolerance). Race results across
  engines are not replayed, so the race is only reproducible within one engine.
- **Flaky timing tests under load.** `perf.test.ts`, `collision.test.ts` and `ai_race.test.ts` measure wall-clock
  time and fail when several vitest runs share the machine (as with parallel agents). Rerun alone before treating a
  failure as a regression.
- The hot-lap trace grows for as long as the player drives without a reset (a few MB per 10 min). Race mode turns
  recording off.

### Track details found today

- Pit-exit cones start at s 122, where the OSM pit wall ends. The real wall probably ends near the start/finish
  bridge (s ~50). Correct the barrier, then re-run `build_scenery.py --only pit_exit_cones`.
- Kerbs: the T8 entry verge paint (green with a white border, outside) is missing; the yellow-orange strip at
  T8/8A is unresolved; stripe length (2 m) and kerb width (0.9 m) are unverified. NAIP at 0.6 m/px cannot place
  kerbs, and it predates the 2023 repave. **Data wish:** a walk of the kerbs with a tape, or a drone pass.
- "No pit lane in the MVP" under Track above is out of date: the pit lane and the paved runoff exist (CONTRACTS §2b).

### Docs that lag the code (17 Oct 2026)

- `src/physics/README.md` "Surface and track" still says mu 0.6 off track (now 0.72, blended; §4d).
- `docs/scoreboard.md` §6 still says `Vehicle.reset()` keeps per-run fields (now fixed; §4a).
- `src/app/README.md` still calls race mode a stub and the scoreboard a disabled placeholder.
- `src/app/NOTES-camera.md`: after a launch in a race, the banner and the game-over card used to disagree. The race
  notes describe the newer "YOU'RE OUT OF THE RACE" card; check that the banner text matches.
- The main menu still says "10 laps" under `?laps=`.
