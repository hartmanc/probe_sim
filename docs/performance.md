# Performance round 1 (27 Oct 2026, branch `perf-round-1`)

Owner: "I had the sense that I was not getting 60 fps on my Mac while playing, particularly with the AI." Five options, in this
order: perf overlay + dev autopilot + adaptive quality, GPU trims, a Balanced tier, a physics LOD for far AI cars, the physics
and AI in a Web Worker.

## Switches

| URL | effect |
|---|---|
| `?perf=1` | overlay (top right, text rewritten 4 times a second): fps, frame p95 over 2 s, canvas pixels and ratio, AI cars drawn / shadow casters / adaptive level, ms per frame for physics (player, AI physics, AI control, contacts, traffic and rules), poses + rigs, render, HUD / DOM, audio; a `console.info` summary every 10 s. Off: no timers run. |
| `?playerai=1` | dev only: the race runs with `RaceConfig.playerAi`; the camera and HUD follow the AI-driven player car. The measurement rig and a demo mode. The hot lap is unaffected; the race results' submit row is hidden and `submit()` refuses while it is on. |
| `?adapt=0` | adaptive quality off (desktop tiers: on by default; never on the phone tier) |
| `?dynres=0` | the older dynamic resolution (look.ts) off, fixed pixel ratio (measuring) |
| `?shadowbox=<5..60>` | half-size (m) of the sun's shadow box (dev) |
| `?lod=1` / `?lod=0` | physics LOD for far AI cars (default **off**, see option 3) |
| `?worker=1` | physics and AI in a Web Worker (default **off**, see option 4) |

Graphics menu: Auto / Phone / **Balanced** / Desktop (the stored choice and `?phone=` work as before).

## Measurements, quiet machine (27 Oct 2026, after the calibration job ended)

Same rig, `npm run build` of HEAD served by `vite preview --port 4174`, Chrome window 1920 x 1080, Buttonwillow, `?dynres=0`, race samples at
`?playerai=1&seed=8` (shuffled grid, the player in slot **7**; the phone field is the real grid order, so there the player is slot 37),
battery 100 %, the 6 s sampler starting 3 s after the start (sim time about 8 s: the formation lap, so these are light-traffic numbers).
The 1-minute load was **2.0-2.9 (under 4) at every run** (checked right after each).

| run | fps | frame p95 ms | frames > 20 ms | JS p50 / p95 / max ms | worker busy | canvas | load |
|---|---|---|---|---|---|---|---|
| 1 hot lap, adaptive on (default) | 59.8 | 18.2 | 0 | 3.2 / 4.5 / 12.4 | - | 2400 x 907 (adapt level 4) | 2.1 |
| 1b hot lap, `adapt=0` | 59.8 | 18.3 | 0 | 3.0 / 4.6 / 4.9 | - | 2880 x 1089 | 2.9 |
| 2 race, desktop defaults (adaptive on) | 59.8 | 18.1 | 0 | 7.0 / 7.5 / 8.2 | - | 2880 x 1089 (level 3, 30 drawn) | 2.6 |
| 3 race, `adapt=0` | 59.8 | 17.8 | 0 | 7.0 / 7.6 / 7.9 | - | 2880 x 1089 | 2.3 |
| 4 race, Balanced | 59.8 | 17.7 | 0 | 7.0 / 7.8 / 9.0 | - | 2571 x 972 | 2.1 |
| 5 race, `lod=1` (79 of 99 cars far) | 59.8 | 18.4 | 0 | 6.1 / 6.7 / 8.1 | - | 2880 x 1089 | 2.4 |
| 6 race, `worker=1` | 59.8 | 17.9 | 0 | 3.2 / 3.9 / 4.5 | 30 % | 2880 x 1089 | 2.0 |
| 7 race, `worker=1&lod=1` | 59.8 | 18.2 | 0 | 3.7 / 4.5 / 6.5 | 24 % | 2880 x 1089 | 2.1 |
| 8 race, phone tier (41 cars) | 59.8 | 18.4 | 0 | 4.8 / 5.5 / 23.2 | - | 1781 x 673 | 2.0 |
| 9 = run 3 with `perf=1` | 58.0 | 17.9 | 3 | 7.2 / 8.0 / 14.2 | - | 2880 x 1089 | 2.3 |
| worst case, player at the back (seed 1, slot 64), default config | 59.8 | 18.0 | 0 | 7.4 / 8.3 / 12.4 | - | 2880 x 1089 (level 2) | 2.1 |

Reading it: on the quiet machine every configuration holds 60 fps through the formation lap; the difference is main-thread JS: 7.0 ms
per race frame (desktop), 6.1 with the LOD, 3.2 with the worker (3.7 with both: the worker + LOD pair is not cheaper on the main thread;
the LOD's saving moves into the worker, whose busy share fell 30 -> 24 %), 4.8 for the phone field. The overlay's own cost is about
0.2 ms of JS per frame (7.0 -> 7.2) plus a little DOM; three frames over 20 ms in its 6 s run. Not measured on the quiet machine: the
pack at its worst (green flag, a bunched field), which is where the loaded runs showed the 14-19 ms.

**Finding: the adaptive policy's 18 ms threshold sits on the vsync noise.** At a steady 60 fps the frame-interval p95 reads 17.7-18.4 ms
(runs above), so the policy steps down (levels 2-4 reached in 9 s with no real load: hot lap 2400 x 907, 30 cars drawn) and only steps back up
after 10 s under 14 ms, which a 60 Hz display never reads. Hold: `ADAPT_DOWN_MS` in `src/app/perf.ts`; a threshold of about 20 ms
(or the p95 of frame work rather than the interval) would stop it. Left as the brief specified; the owner's call.

Tests on the quiet machine: `npx vitest run` 93 files, **777 / 777 passed** (including `ai_behaviour`'s full-field test: the earlier failure
was load only); `npm run test:e2e` 13 / 13; `npm run build` passes.

## Measurements, loaded machine (read this first, then the quiet table above)

Chrome on this M3 MacBook Air, plugged in (battery 100 %), Buttonwillow, 99-car field, window 1920 x 1080 (canvas CSS 1920 x 726,
2880 x 1089 = 3.14 MP at ratio 1.5), race samples at `?playerai=1&seed=1&adapt=0&dynres=0`, sampled 6 s starting about 28 s
after the start (sim time about 33 s, the green flag, the pack bunched). **The brief asks for a 1-minute load under 4. It never
was: another agent's field calibration ran at about 600 % CPU the whole session, load 9-18 at every sample (written next to
each number). The absolute numbers below are therefore pessimistic and noisy (the pack's AI physics measured 0.5 ms per step,
against the NOTES' 0.06 ms unloaded); only the same-session pairs can be compared, and every pair should be re-run on a quiet
machine.**

| run | load | fps | frame interval p95 ms | main-thread JS p50 / p95 ms |
|---|---|---|---|---|
| hot lap, before (opt 1 build, 4096 map, 12 casters) | 10.6 | 49.7 | 34.2 | 4.1 / 7.9 |
| hot lap, after option 5 | 11.1 | 53.8 | 33.3 | 3.8 / 6.2 |
| race, before option 5 (4096 / 12 casters / ±30 m) | 9.6 | 41.2 | 50.2 | 17.8 / 49.2 |
| race, option 5 (2048 / 8 casters / ±30 m) | 17.8 | 45.5 | 34.6 | 17.5 / 34.6 |
| race, option 5 with `?shadowbox=15` | 15.3 | 47.7 | 34.1 | 17.4 / 29.7 |
| race, desktop tier (option 2 build) | 11.4 | 48.5 | 34.2 | 17.7 / 30.3 |
| race, **Balanced** (2571 x 972 = 2.5 MP, 30 AI drawn) | 10.6 | 55.8 | 33.4 | 16.2 / 27.1 |
| race, phone tier (41 cars, 20 drawn, 1781 x 673) | 8.9 | 59.8 | 17.9 | 6.3 / 7.0 |
| race, LOD off (`?lod=0`) | 10.0 | 43.5 | 34.4 | 18.7 / 36.3 |
| race, LOD on (`?lod=1`, 61 of 99 cars far) | 9.8 | 56.7 | 18.3 | 14.1 / 20.8 |
| race, `?worker=1` | 15.1 | 59.0 | 18.2 | 6.8 / 10.0 |
| race, adaptive quality on (default), after 45 s | 11.8 | 59.8 | 18.0 | 14.3 / 15.4 |

The overlay's per-frame split of the LOD pair and the worker (load 10-15): LOD off: JS 25.1 ms per frame, of which physics 19.3
(26.6 steps per frame: a slow frame is followed by catch-up steps; AI physics 13.1, AI control 4.9, render 4.3); LOD on: 14.7,
physics 8.8 (16.7 steps; AI physics 5.9, AI control 2.1), per step 0.67 ms -> 0.48 ms (-29 %). Worker: main-thread JS 6.5 ms per
frame, physics on the main thread 0.24 ms (the input message and applying the snapshot); the worker was 91 % busy at load 15 and
fell behind real time (sim time 27 s against 32 s), which a quiet machine will not.

Self-play (`tools/race/selfplay.ts` against `tools/perf/selfplay_lod.ts --lod`, Buttonwillow, 2 laps, 100 cars, seeds 1 / 2 / 3,
loaded machine): cost per step 533 / 603 / 528 us -> 369 / 366 / 348 us.

What the numbers say, and what they do not: the main thread carries about 6-7 ms per race frame when quiet and 14-19 ms in the
bunched pack; the biggest single item is the AI physics, and the loop's catch-up (up to 50 ms of physics in a frame) turns one
slow frame into the next. Option 5 and the Balanced tier help GPU-bound frames (fps 41 -> 45-48 -> 56 at the same load, but the
JS time did not move: this machine was CPU-bound by the other agent). The LOD and the worker take the CPU off the render
thread. The adaptive policy found the floor of its ladder under this load and held 60 fps.

## Option 1: overlay, autopilot, adaptive quality

`src/app/perf.ts` (flags, `perf` accumulators, `FrameWindow`, `adaptLadder`, `AdaptivePolicy`, `AdaptiveQuality`, `PerfOverlay`),
`RaceDirector.timing` (`DirectorTiming`, `performance.now()` per group, not per car; `null` = no timers), probes in `index.ts` and
`modes/race.ts` (`if (perf.on)`), `FieldCars.setLimits`, `Look.setRatioLimit`. Adaptive quality: the frame-time p95 over the last 2 s
above 18 ms steps down (AI shadow casters halved, then 0; drawn AI cars to 30; the pixel-ratio cap -0.25 down to 1.0), 3 s between
steps; 10 s under 14 ms steps back up one level; never below the phone tier's numbers (0 casters, 20 cars, ratio 1). The ladder
is built from the tier's own numbers (a tier with 4 casters goes 4, 2, 0). It works alongside the older dynamic resolution in
`look.ts`, which lowers the ratio inside the cap. Tests: `src/app/__tests__/perf.test.ts`.

## Option 5: GPU trims

Desktop defaults: shadow map 4096 -> 2048, AI casters 12 -> 8, `maxPixels` 3.5 MP (a 4K display at ratio 1.5 would be 4.7 MP; at
1920 x 726 CSS the budget is not reached, so the canvas is unchanged there). **Shadow box: I chose +-15 m** (the same 68 px/m
as the old +-30 m at 4096 px: the player's shadow keeps its density) over keeping +-30 m (34 px/m, softer). I measured both
(row above: `?shadowbox=15` 47.7 fps against 45.5, inside the noise). A caster only casts inside the box (`FieldCarsOptions.shadowRangeM`;
beyond it the car keeps its contact blob, as the `contactShadow` comment always said). AI cars between 15 and 30 m lose their
real shadow. `?shadowbox=30` restores the wide box. Existing quality tests updated to the new numbers (not loosened).

## Option 2: Balanced tier

`Tier` grows `'balanced'`: desktop field and device class, shadows on at 2048 px, 4 casters, 30 AI cars drawn, 2.5 MP, anisotropy
8, no scenery thinning, post stack as desktop. Graphics menu row; the stored choice, `?phone=` and `pickTier` keep working. Tests in
`quality.test.ts`.

## Option 3: physics LOD for far AI cars (shipped OFF; `?lod=1`)

`RaceConfig.lod` (default false), `lodFarM` 300, `lodHystM` 50, `lodNearM` 40, `lodEvery` 2: an AI car more than 300 m of track
(both ways, wrapped) from the player steps at 250 Hz (control every physics step, as today), a car inside 300 m or within 40 m of a
car that is inside stays at 500 Hz, hysteresis 50 m, rates re-evaluated every 50 steps; each step integrates the real time since the
car's last step, so a car changing rate keeps the clock. With every car near it is the ordinary step bit for bit
(`ai_lod.test.ts`). The app: `?lod=1|0`, else `LOD_DEFAULT` (false).

**Why off: the stability gate failed.** `tools/perf/lod_stability.ts` (the stiffest cars: highest pace `scale`, lightest mass,
highest scale per kg; every car x stint of pace.json is a candidate) runs a solo lap at 250 Hz and at the race's 500 Hz: none left
the road (0 recoveries, no extra steps with 3 wheels off), but the lap times differ by up to 0.32-0.35 % for the highest-scale
cars (#250 at scale 1.34 and 1.25) against the 0.1 % allowed; Buttonwillow 4 of 10 cars fail, Laguna 3 of 8, Sonoma 5 of 7.
Behaviour gate (self-play, Buttonwillow 2 laps, seeds 1 / 2 / 3, LOD off -> on): AI-AI contacts 4 / 3 / 5 -> 4 / 2 / 3, four-off 4 / 0 /
0 -> 4 / 1 / 0, green passes 298 / 351 / 301 -> 278 / 333 / 309, stuck median 11.8 / 19.0 / 14.5 s -> 17.3 / 15.0 / 16.5 s; the finishing
order changes (a chaotic race: any numerical change reorders it), the metrics stay inside the seed spread. The solo calibration
laps cannot change (`runSolo` and calibration have no director; `solo.ts`, `vehicle.ts` untouched); no `AI_VERSION` bump. To ship it
on by default, either exempt the cars above scale about 1.15 from the LOD or accept 0.35 % on cars 300 m away; the owner's call.

## Option 4: physics and AI in a Web Worker (shipped OFF; `?worker=1`)

`race-worker.ts` (message shell), `race-host.ts` (`RaceSimHost`: the player's `HotlapSim` + `RaceDirector` on the worker's clock,
1 ms accumulator, 50 ms cap, the director's time scale, a snapshot about every 14 ms), `race-snapshot.ts` (83 floats per car in one
transferable `Float32Array`, per-car race numbers in a `Float64Array`, so distances and lap times stay exact; the HUD object and the
other cars' contacts ride along as a small clone), `race-worker-client.ts` (main side), `race-build.ts` (the DOM-free director
construction both sides share). The main thread still builds the director (specs, identities, the line) but never steps it:
`installMirror` takes over `hud()`, `getResults()`, `poses()` brake flags, `reportViolation()` and `step()`; `applySnapshot` writes
each snapshot into the same `VehicleState` objects the rig, camera, HUD, audio and marks already read. Input: each frame the main
thread sends the device input and the shift latches; pause / menu stop the worker (`GameMode.setPaused`), recovery and the pit-exit
cone violation are forwarded. No `SharedArrayBuffer`. The hot lap, the scoreboard replay and `HotlapLoop` are untouched (e2e: 13 tests
pass). A failing worker falls back to the main-thread race.

**Identity proof** (Chrome, Buttonwillow, `?playerai=1&seed=1&laps=1&adapt=0`, with and without `&worker=1`): the same 100-car
finishing order, the same hash of the whole results table (`7753e17`), the same hash of every car's best / last lap and finish
time (`c2631de1`), the same `director.contactTotal` (1808), the leader's time 112.02 s. Unit test: the host on a fake clock equals the
main-thread race bit for bit (`race-worker.test.ts`). Not default until the owner drives it.

Seen on the way, and not a bug: with `?playerai=1` the player starts P74 of 100 on the grid, 1.8 km behind the line (race distance
starts negative), so "530 m after 124 s" is the back of the pack at 18 m/s average (formation lap, then traffic); self-play puts
#619 at P54-85 after 2 laps the same way, and the app-built director matches its grid neighbours
(`src/app/__tests__/playerai.test.ts`). For a clean-air run use `?playerai=1` with a front grid slot, or read the pack's cost, as here.

## Not shipped / not done

- LOD default on (gate failed, above); worker default on (owner's drive first).
- Measurements under load < 4: not possible this session (the calibration job ran throughout); every pair should be re-run quiet.
- The overlay's own cost with `?perf=1` on was not measured (off: no timers, no DOM).
- The 4K / 4.7 MP case itself was not measured (this window is 1920 wide).
- `ai_behaviour`'s "full field, 2 laps" test hits its 60 s timeout when the machine is loaded (it did on the untouched baseline too);
  it passes alone.
