# Race mode in the app — notes for the lead (17 Oct 2026)

Core: `src/physics/ai` (RaceDirector, see its NOTES.md). App side: `modes/race.ts` (wiring), `field-cars.ts`
(AI rigs), `race-hud.ts` (flag banner, race panel, standings / results tables), `loader.ts` (`loadFieldData`,
`loadFieldModel`), `style.css` (`.race-*`, `.rt-*`), `index.ts` (`ctx.race` services, launch card).
Tests: `src/app/__tests__/race.test.ts` (+ the race case in `modes.test.ts`).

## How it is wired

- **Player car = the HotlapSim car.** `HotlapSim` (src/scoreboard/sim.ts) gained two fields: `record` (now mutable;
  the race sets it false, so no trace grows during a race) and `stepVehicle` (null = plain `vehicle.step`). In a race
  `sim.stepVehicle = (di) => director.step(STEP, di)`: each 1 ms HotlapSim step hands its quantised 100 Hz-held input
  to the director, which steps every car (the player's with that input), contacts, laps, flags, rules. HotlapSim
  keeps its clock, 200 Hz projection and gear schedule. `mode.step()` runs after each step (AI-AI thumps near you).
- **Build / restart.** `build()` = `ctx.rollingStart()` (fresh Vehicle + Surface, step 0) → `new RaceDirector({...,
  playerVehicle: sim.vehicle, playerSurface: sim.surface, makeSurface (same options as the sim's surface),
  collisionWorld: sim.collision, pitLane: scenery.pit_lane})`. Restart (pause menu, results "Race again", launch
  card) draws a new seed and rebuilds (≈0.25–0.4 s hitch). RaceLine is cached per track.
- **Per frame:** `director.hud()` → `raceHudView()` → DOM; toasts (green, lap done with lap time, position ±
  after 1 s stable, black flags, chequered); `poses()` → `FieldCars.update()`; penalty-box marker (yellow pad +
  "PENALTY BOX" sprite) while a stop-and-go is pending; field audio; results card when `phase === 'finished'`.
- **Pit-exit cones:** `pitExitConeWatcher()` (scenery.ts) per race; `update(x, y)` each frame →
  `director.reportViolation('pit_exit_cones')`; `clear()` on build and on recover. New director API (tiny,
  documented in race.ts): `reportViolation(kind, detail?)` — same escalation as the built-in rules, one flag per
  kind per 2 s; banner reason "crossed the pit-exit cones".
- **Space launch** ends the player's race: result = metres at the launch, status `out`. The GAME OVER card in race
  mode reads "YOU'RE OUT OF THE RACE" with Results / Race again (new seed) / Main menu (`GameOverOptions.title /
  line / extra` in hud.ts; hot lap unchanged). R / Enter / pad A → Results.
- **Reset (R) in a race** recovers on the centreline at the current s (as before).
- **Pause / menus** pause everything (nothing is stepped). Pause menu: Standings (running order table), Seed row,
  Results (after the flag).
- **Scoreboard:** `setBoardContext({ raceAiVersion: '2' })` at each build; results → `submitRace({ metres, laps,
  aiVersion, seed, position, finished })` through the usual prompt; the results card reopens afterwards.

## Per-event fields and field keys (22 Oct 2026)

- **Files per track.** `TRACKS[id].pace` (required) and `TRACKS[id].identity` (optional, a circuit's own field:
  `cars/field/<track>/identity.json`). `loadFieldData` loads the track's own identity file and falls back to the global
  `cars/field/identity.json` (Laguna's) when the track has none or the file is missing / 404 (`loadIdentityWithFallback`;
  the fallback is noted in `FieldData.missing` and `identityPath` says which file was used). `models.json` stays one
  global pool for every track. The tools do the same (`tools/race/load.ts` `identityPath` / `loadIdentity(track)`).
- **Field key = `id`, else the number** (`fieldKey`, src/physics/ai/field.ts). pace.json cars, identity.json rows and
  models.json rows may carry `id`; the director finds a car's identity row by it (`RaceCar.id`, `CarPose.id`), the app
  its model (`modelQueue` in modes/race.ts) and its index.json sound row. Laguna's files carry no ids, so everything
  resolves by number exactly as before (seeded self-play unchanged). FieldCars, tints, stint draws, driver seeds and
  results stay keyed by the number (unique within one race).
- **Model key** (`modelKey`): the pace row's `model_id`, else the identity row's `model_id`, else the field key. A car
  renumbered since an earlier event reuses its model that way (Buttonwillow #6 Tinyvette = Laguna #8 would get
  `model_id: "8"`; #6 ran no lap, so it is not in this field, but the rule stays). `RaceCar.model` / `modelQueue`.
- **Buttonwillow** (`tools/race/pace_track.ts --own`): the race's own 100 cars (99 AI + the player's reference row;
  the five entrants with no lap, #89, #6, #43, #101, #222, left out and named in pace.json `notes`). Ids come from
  `cars/field/buttonwillow/identity.json` (104 rows, all with `id`) when it exists, else the match rule: a number that
  is a different car at Laguna gets `<n>_bw` (0, 1, 8, 9, 16, 40, 670, 711, 801 in the field; 43, 89 in identity only;
  #670 Bernal Dads raced a Ram van here, not the Laguna Volvo), so it never shows the Laguna car's identity or model;
  #38, 189, 544, 963 (and the player's 619) are the same cars and keep their numbers. A car without a model row keeps
  the placeholder.
- **Electric cars** (#16_bw, a Chevrolet Bolt: identity engine `layout: "EV"`, `cylinders: 0`): `resolveCarType` gives
  layout `EV`, cylinders 0, a flat-then-constant-power torque shape, no turbo; nothing divides by the cylinder count
  (engine inertia is 0.1 + 0.025 x cylinders). The field audio gives it no voice (`silentEngine`: silence rather than a
  borrowed petrol family) unless index.json's `cars["16_bw"]` names a family.

## Dev overrides (URL)

| param | effect |
|---|---|
| `?seed=<int>` | first race uses this seed (restarts draw new ones); the pause menu shows the current seed |
| `?laps=<1..10>` | shorter race; Submit is disabled ("10-lap races only") unless `?devsubmit=1` |
| `?devsubmit=1` | allow posting a shortened race (local API testing) |
| `?fieldaudio=1` | AI engine sounds (see below) |
| `?phone=1` | phone tier: 20 AI cars drawn, no AI shadows |

Debug: `__sim.mode.director` (RaceDirector), `__sim.mode.fieldCars`, `__sim.mode.seed`.

## Placeholders / what is not final

- AI cars without a glb (all but the models in models.json) are a ~300-triangle box car: wedge lower body + tapered
  glasshouse in identity `colors.primary` (else the director's tint), number boards on both doors, roof and tail
  (canvas texture), 14-sided wheels, sized from the car's physics hull / wheelbase / tracks. 6 draw calls each.
- glb models load one at a time in the background after the race is built, and swap in live
  (`FieldCars.useModel`, tyre radius from models.json `tyre_radius_m`; CarRig now takes `{ tyreRadius,
  physicsRadius, castShadow }` and drops the hub so a different wheel still touches the road).
- Draw cap: nearest `quality.maxAiCarsDrawn` by track distance (wrapped); frustum culling on.
- Lighting: on desktop the nearest `quality.aiShadowCasters` = 12 AI cars cast shadow-map shadows inside the sun's
  ±30 m / 4096 px box (applyQuality widens it from the ±7 m / 1024 px player box; same texel density), and hide their
  contact-shadow blob; the rest, and every AI car on the phone tier or with `?aishadows=0`, keep the blob.
  Field materials get a small canvas sky/ground environment map (`fieldEnvMap`, PMREM'd on first use, intensity
  `FIELD_ENV_INTENSITY` = 1.0) and metalness is zeroed on painted surfaces (`prepareCarMaterials`).
- Brake lights: `CarPose.brake` (the AI driver's pedal) → `FieldCars.update(..., brakes)` → `CarRig.setBrakeLights`:
  lamp discs at models.json `brake_lamps` for field cars, the `brake` material for the Probe (index.ts uses the sim's input).
  `brake_lamps_fallback` (imported bodies with no lamp spec, 15 cars) keeps the discs visible dim red as tail lights.
- Results status for the player is `running` (the director reports running | ejected; `out` is app-side).
- The main-menu label still says "10 laps" under `?laps=`.

## When more data lands

- **More car models:** nothing to do — `models.json` is read at the first race of a page load; new rows load
  lazily. (A reload picks up models built after the page was opened.)
- **audio-field.ts / families:** wired behind `?fieldaudio=1` (`fieldAudioHook` in modes/race.ts): fetches
  `audio/families/index.json`, maps each car with `familyFor(engine.family, make, model, cylinders, layout)`, trim
  0.96–1.04 per number, muffler from `exhaust_note`, feeds `FieldAudio.update` per frame with the player's car as
  listener. It reads CarAudio's private `ctx` / `master` in index.ts (one place, marked); replace that with a public
  accessor on CarAudio and flip the flag default once the families exist (index.json was missing today: the hook
  logs a warning and stays silent).
- **Player–AI impact sounds** come through the existing `st.impact` → `audio.impact()` path (kind `'car'`);
  AI–AI contacts within 40 m add a distance-scaled `audio.impact()`.

## Measured (M3, Chrome, this session; other agents were running tests)

- Desktop, 45 cars, chase cam: 57 fps, median frame 16.9 ms (p95 26.7), 388–413 draw calls, 1.8–1.9 M triangles.
  Physics in the frame (≈17 director steps): median 5.5 ms, p95 11.2 ms.
- `?phone=1`: 60 fps, median 16.7 ms (p95 18.8), 242 draw calls, 1.5 M triangles, 20 AI cars drawn.

## Race polish (17 Oct 2026, later)

- **AI engine sounds on by default.** `CarAudio.context` (existing getter) + new `CarAudio.fieldBus()`: a GainNode
  (`FIELD_BUS_GAIN` 0.55) into the master, so Mute and the master limiter apply. The private-field hack in index.ts is
  gone. `fieldAudioHook(ctx, bus, fieldVoicesFor(quality.tier))` (modes/race.ts) re-reads index.json per race
  (no-cache), retries a missing/unusable index every 10 s, and resolves each car with `carSound()`: index.json
  `cars[num]` (family, trim, muffler, rpm_scale) when its family exists, else `familyFor()` + hashed trim + the
  index's `muffler` table. `fillAudioCar()` feeds rpm × rpm_scale and redline × rpm_scale (limiter still trips at
  the car's own redline). Pause-menu toggle "AI engine sounds" (localStorage `probeSim.fieldAudio.v1`, off = "0");
  `?fieldaudio=0` forces off (the row is disabled); `?fieldaudio=1` is no longer needed. Debug: `__sim.mode.fieldAudio`.
- **audio-field.ts (small change):** a family whose files fail (missing, bad JSON, no usable bins, undecodable Ogg)
  is warned about once and retried every `FAMILY_RETRY_S` = 10 s instead of every frame. Seen live: `twincam_i4_loud`
  failed to decode mid-rebuild and the race carried on.
- **Measured in Chrome** (seed 42, player stopped after the start): context running, field bus RMS up to 0.02,
  8 voices, Doppler 1.107 approaching / 0.942 receding. Mix level is a first guess; tune `FIELD_BUS_GAIN` by ear.
- **Statuses:** `rowStatus()` (race-hud.ts): at the flag every classified car reads "finished"; the player
  "out" (launch) or "ejected"; before the flag "running". After the flag, Standings shows the flag classification.
  `raceResultFor().finished` accepts "finished".
- **Main menu:** `raceMenuLabel(location.search)` ("Race · 3 laps vs the 2026 field" under `?laps=3`).
- **Placeholder boards:** door boards fill the height below the belt line (≤ 0.56 m tall, 2:1), roof board fills
  the roof, tail 0.84 × 0.42 m; 512×256 texture, 900-weight digits with a stroke, board dark on light bodies and
  light on dark (`boardColor`), team primary-colour band along the bottom, emissive 0.35 so the shaded side reads.
  Still about 300 triangles (test: ≤ 400). Readable at about 26×13 px.
- **Credits** (src/app/credits.ts, main menu → Credits): re-reads cars/field/credits.json,
  cars/field/models/credits.json, audio/families/index.json (+ each family's engine.json `sources`, `skip: true`
  excluded) and identity.json (team names) each time it opens, merges by car number and source, and adds the
  SmugMug "Twenty Ridiculous Years at Laguna" reference-only line. Body scrolls with wheel/touch; "Scroll down / up"
  rows for pads and keys.
- Tests: src/app/__tests__/race-polish.test.ts (credits, label, statuses, boards) and the "race field-audio hook" block
  in audio-field.test.ts (OfflineAudioContext-style fake: rpm_scale, bus output, missing-family retry, bad index).
