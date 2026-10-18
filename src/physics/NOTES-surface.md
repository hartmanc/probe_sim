# Off-pavement surface model (Oct 2026)

Owner's request: no tyre screech off pavement, and less grip there, "not drastically less" (dry Laguna dirt / dry
grass, not VIR wet glass).

## What counts as pavement

`createTrackSurface` already marks the track, the pit lane and the paved runoff zones (passed as `pitLane` parts by
the app and the scoreboard sim) as `paved`. All three keep full pavement grip: `mu = muOnTrack` (1.0), `dirt = 0`.
Everything else is off pavement.

## Surface sample (track.ts)

New optional fields on `SurfaceSample`:

| field | meaning |
|---|---|
| `dirt` | 0 on pavement, rising by smoothstep to 1 over the first `SURFACE_GRIP_BLEND_M` = 1.0 m past the nearest paved edge. It uses the same distance-past-the-edge the 5 m shoulder height blend uses (min over track and pit/runoff). |
| `mu` | `muOnTrack + dirt · (muOffTrack − muOnTrack)`: continuous, no step at the edge. |
| `muPaved` | `muOnTrack`, so a car can blend its own dirt mu. |

`muOffTrack` default changed from 0.6 to `OFF_PAVEMENT_MU` = 0.72.

Roughness: off pavement the ground gets a 3-wave undulation (wavelengths 3.7 / 5.3 / 8.9 m, odd directions, total
peak `DIRT_ROUGHNESS_M` = 12 mm), multiplied by `dirt` so it is zero at the paved edge and heights stay continuous.
It is a pure function of (x, y) (no time, no RNG), the normal includes its gradient, and it costs three sin/cos per
off-pavement sample. At 25 m/s it excites 3–7 Hz: a felt, not seen, rumble. `roughness: 0` disables it.

## Vehicle (vehicle.ts, car.json `surfaces`)

Per wheel, scaled by that wheel's `dirt` weight:

| car.json key | value | effect | why |
|---|---|---|---|
| `offPavementMu` | 0.72 | tyre friction = `muPaved · (1 − dirt · (1 − 0.72))`; overrides the surface's `muOffTrack` when set | street tyre on firm dry dirt / dry grass keeps ~0.65–0.8 of asphalt grip; 0.72 is "noticeably less, not ice" |
| `offPavementLateralStiffness` | 0.65 | lateral peak slip angle 7° → 10.8° (the Magic Formula is stretched; cornering stiffness ×0.65) | loose surfaces have a broad, late peak: the car drifts progressively instead of snapping |
| `offPavementRollingResistance` | 0.04 | ΔCrr added to the wheel's rolling-resistance torque | firm dirt / short dry grass Crr ≈ 0.04–0.06 vs 0.013 on asphalt |
| `offPavementRollingResistanceSpeed` | 0.0015 /(m/s) | ΔCrr grows with contact-patch speed | sinkage / ploughing drag grows with speed |

Measured (src/physics/__tests__/surface.test.ts):

- skidpad peak: 0.99 g on pavement, 0.76 g on dirt (ratio 0.76).
- coasting in neutral for 5 s from 25 m/s: 23.0 m/s on pavement, 19.7 m/s on dirt (~0.067 g extra drag).

`WheelState` gains `paved` (from the sample under the wheel, `paved ?? onTrack`) and `mu` (the friction actually
used), so the app can gate per wheel without re-sampling.

## On-pavement behaviour is bit-identical

Every new term is behind `dirt > 0` (`smp.dirt ?? 0`; the flat dev surfaces publish no `dirt`), and inside the tyre
the stiffness factor is exactly 1 on pavement (the only new arithmetic on that path is a multiply by exactly 1.0).
`surface.test.ts` replays a 9 s pure-pursuit drive on Laguna (track + pit lane + runoff) and compares 486 state
numbers with `===` against `__tests__/fixtures/onpave_drive.json`, recorded before the change. The calibration
tests (balance, vehicle) use flat pavement and are unchanged.

## Audio (src/app/audio.ts)

- `onPavement(w)` = `w.paved` (falls back to `onTrack`). `wheelSqueal` returns 0 for a wheel off pavement, so a
  wheel on dirt adds nothing to `squealMix` scrub or skid; the pit lane and runoff still squeal.
- `dirtMix(st)`: `level` = (loaded wheels off pavement / 4) × smoothstep(speed / 25 m/s); `spray` = the most-slipping
  dirt wheel's slipUse past 0.8 of the peak, × smoothstep(speed / 6). Graph: a low 140 Hz dirt bed (0.22 × level)
  plus the 420 Hz gravel band (0.1 × level), and a 2.6 kHz spray band (≤ 0.07) whose level flutters with a 22 Hz
  random envelope (stones, not hiss). All well under the engine (~0.5–1.0) and the road rumble's peak (0.32).

## Scoreboard

Off-pavement physics changed (and the off-track roughness), so `PHYSICS_VERSION` in src/scoreboard/config.ts was
bumped.
