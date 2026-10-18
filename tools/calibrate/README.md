# Car calibration against the logger ghosts

Drives the real physics (`src/physics`) at 1 kHz on the real Laguna Seca package with an
autopilot that follows the ghost racing line, and compares the lap with the driver A (1:59.32, real)
and optimal (1:57.99) ghosts in `public/tracks/laguna_seca/ghosts.json`.

## Run

```sh
npm i                                   # tsx is a dev dependency (the physics imports have no .ts extensions)

# calibrated "near-perfect" lap: start at a 1.4 g lateral budget and let 25 practice laps
# adapt it per corner until the car stays within 1 m of the line (about 4 s)
npx tsx tools/calibrate/drive.ts --alat 1.4 --learn 25

# the plot (reads tools/calibrate/out/)
uv run --python 3.12 --with matplotlib,numpy python tools/calibrate/plot_compare.py

# power/drag check: logger full-throttle acceleration vs speed, plus a least-squares torque-scale/CdA fit
uv run --python 3.12 --with numpy python tools/calibrate/accel_fit.py tools/calibrate/out/summary.json
```

`drive.ts` options:

| Option | Default | Meaning |
|---|---|---|
| `--car <path>` | `public/cars/probe_gt/car.json` | car spec to drive |
| `--set a.b.c=<number>` | | override any numeric car.json field (repeatable), e.g. `--set aero.cd=0.45` |
| `--torque-scale <k>` | 1 | multiply the torque curve |
| `--alat <g>` / `--abrake <g>` | 1.05 / 0.95 | lateral-grip and braking budgets for the target speed profile |
| `--learn <n>` | 0 | practice laps that adapt the lateral budget per corner (lower where the car ran > 1 m off the line, higher where it stayed within 0.5 m); the fastest clean lap is reported |
| `--upshift <rpm>` | 5000 | the drivers' shift point (the ghosts never exceed ~5450 rpm); 0 keeps car.json's autoShift |
| `--keep-shaping` | off | keep car.json's gamepad steering shaping (it caps the road-wheel angle at 4.8° at 116 km/h, too little for some corners at the limit) |
| `--track <dir>` | `public/tracks/laguna_seca` | track package (track.json, heightfield.bin, ghosts.json); corner windows follow its `corners[].s` |
| `--bank` | off | count the lidar road banking in the target speed (tyre budget + bank), see tools/track/README.md v2 |
| `--out <dir>` | `tools/calibrate/out` | output directory; `--no-files` writes nothing |
| `--json` / `--quiet` | | print the summary as one JSON line / no progress on stderr |

`--schedule <ghost id>` makes the autopilot's auto-shift follow that ghost's derived gear schedule;
`npx tsx tools/calibrate/gears.ts [ghostId]` prints the schedules and shift rpm.

`npx tsx tools/calibrate/fit_power.ts [--torque-scale k] [--cd x] [--area A] [--grid]` checks power against drag on the
two long full-throttle straights (front straight and the Rahal climb, real grade) against the driver A/optimal speed gains.

The autopilot adds an understeer feed-forward (deg of steer per g of lateral, measured on the flat at start-up;
`DRIVE_NOFF=1` disables it).

`tools/calibrate/sweep.sh "<drive args>" 1.1 1.2 1.3` prints one line per lateral budget, handy for parameter sweeps.
`DRIVE_DEBUG=380,470` prints per-step controller and wheel state between those s values.

Outputs in `out/`: `sim_lap.csv` (s on the ghosts' 2 m grid: t, v, rpm, gear, throttle, brake, steer, gLat, gLong,
lateral error to the line, ghost speed/time/rpm/throttle at the same s, line curvature and grade), `summary.json`,
`target_profile.csv` and `report.txt` (the console report: corner minimums, straights, speed-matched
acceleration, braking).

## How it works

- **Line:** `lineToWorld` with `ghosts.line.offset_m` at every 1 m station. Curvature from the line heading,
  Gaussian-smoothed over 4 m; grade from the line z.
- **Target speed:** v = sqrt(a_lat·g/|κ|), then a forward pass limited by the car's measured flat-ground
  full-throttle a(v) (run first, same shift strategy) minus grade, and a backward pass at the braking budget plus
  grade, both inside a friction ellipse.
- **Steering:** pure pursuit from the rear axle with look-ahead 3 m + 0.25 s·v, plus yaw-rate feedback
  (0.25 rad per rad/s) that catches slides. The road-wheel angle is commanded directly (see `--keep-shaping`).
- **Speed:** feed-forward of the profile's acceleration 0.12 s ahead plus PI on speed error, mapped to throttle
  or brake from the measured brake gain and coast-down decel. The "driver" eases the brake when a loaded wheel
  passes 1.5× the peak slip ratio and the throttle when a front wheel spins (no ABS/TC in the car).
- **Lap:** rolling start 350 m before the line, one timed flying lap; a lap counts as clean when the car never
  strays more than 1 m from the line (the line itself is ≥ 1 m inside the edges) and does not spin.
- **Straights check:** "speed-matched" distance each trace needs to gain the same speed range on a straight, so
  differing corner exits don't distort the power/drag comparison.

Calibration results and what is still off: `improvements.md`, section "Calibration".
