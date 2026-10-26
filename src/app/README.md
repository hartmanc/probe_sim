# src/app — Probe Sim browser app

Rendering, input, HUD, audio, lap timing, ghosts and cameras. Consumes only the
physics API in CONTRACTS §4 and the packages under `public/`.

## Structure

| File | Role |
|---|---|
| `index.ts` | Composition root: boot, main menu with load progress, renderer, world, car, cameras, audio, input, pause menu, modes. One rAF loop: menus / panel first, then the fixed-step sim (physics 1000 Hz, accumulator capped at 50 ms per frame). Nothing is stepped and audio is suspended while a menu or the controls panel is open or the tab is hidden. Exposes `window.__sim` (vehicle, timer, cams, input, hud, track, setCamera, world, renderer, audio, surface, menu, mode, setMode(id)). |
| `menu.ts` | Menu model (pure: cursor, wrap, skip disabled, toggles, choices, submenus, back), `RepeatGate` key repeat (350 ms, then 120 ms) and the DOM view (large click / touch rows, footer hints in the current device's glyphs). Tested in `__tests__/menu.test.ts`. |
| `glyphs.ts` | Controller family from `Gamepad.id` (vendor 045e Xbox, 054c PlayStation, 057e Nintendo, or product words) and button / axis labels per family. Tested in `__tests__/glyphs.test.ts`. |
| `modes/mode.ts` | `GameMode` interface, `ModeContext` (services from index.ts), `ModeHost` (switching). See Modes below. |
| `modes/hotlap.ts` | Hot lap: rolling start before T11, ghosts, delta to the reference ghost, corner table, Ghosts submenu. |
| `modes/race.ts` | Race (stub): same car and rolling start, no ghosts, 5 laps, banner with placeholder position / field, `TODO(race-director)` hooks. |
| `loader.ts` | Fetches `tracks/laguna_seca/{track.json,heightfield.bin,ortho.jpg,ghosts.json,scenery.json,far_heightfield.bin,far_ortho.jpg}` and `cars/probe_gt/{car.json,probe.glb}` by relative URL, each with a fallback. |
| `scene.ts` | Terrain (heightfield on a 4 m grid, ortho via world UVs; vertices under the ribbon + shoulder sunk up to 0.3 m, then any terrain triangle that still reaches within 2 cm of the ribbon is lowered), track ribbon = 7-point lidar profile + 5 m shoulder rows each side (shoulder heights from the physics surface, outermost row snapped onto the terrain mesh; no lift, polygon offset), `photoGround` shader patch (procedural asphalt / dry-grass detail + normal maps fading 30–80 m, asphalt grade blended per vertex), start line, sky, haze, lights. `world.seam` reports the ribbon/terrain seam. Corner signboards only without scenery. |
| `scenery.ts` | CONTRACTS §2b: far terrain + horizon skirt, instanced oaks (3 crown variants near, 2 coarse far, chunked 250/900 m for culling), merged buildings with facade/bleacher textures, concrete walls, Armco, catch fences, instanced tyre stacks, kerbs with green paint, bridges with banners, brake/corner boards, the flag stand. |
| `car.ts` | Binds `body`, `wheel_*`, `steering_wheel`, `cam_driver`, `cam_hood`; poses from `VehicleState`; wheel steer pivots; steering wheel 2.9 turns lock-to-lock. Also the fallback box-on-wheels car. |
| `ghosts.ts` | Ghost laps (35 % opacity, tinted, name label), `t(s)` lookup, synthetic speed-profile ghosts when `ghosts.json` is missing. |
| `cameras.ts` | Chase (60°), hood and driver (70°, looks into corners). |
| `input.ts` | Gamepad + keyboard, polled in its own rAF loop; bindings, analog detection, calibration capture. |
| `controls.ts` | Pure binding/calibration logic: defaults, response curves, analog tracker, localStorage (try/catch). Tested in `__tests__/controls.test.ts`. |
| `controls-panel.ts` | Controls panel (K): live raw readout, Assign, calibration, test strip, defaults. |
| `hud.ts`, `style.css` | DOM HUD, mode banner, help overlay, corner table, toasts; menu styles. |
| `timing.ts` | Lap timing on projector `s` wrap, invalidation after >2 s fully off track; `clearSession()` for a mode restart. |
| `audio.ts` | Web Audio: recorded engine (sample sprites), recorded tyre squeal, road rumble, wind, impact thump. See Audio below. |
| `physics-types.ts` | Structural copy of the §4 interfaces (`PhysicsApi`). |
| `physics-stub.ts` | Kinematic bicycle car + heightfield/profile surface, same API. |
| `physics-loader.ts` | Picks the stub or the real physics. |
| `devtrack.ts` | Synthetic 1.5 km oval with a hill, flat heightfield and procedural ortho fallbacks. |
| `trackmath.ts` | Shared track geometry helpers. |

## Look

ACES at exposure 1 with sun 3.4 + hemisphere 0.95 gives about 0.9 × albedo on flat ground, so the ortho keeps its
own colours. Earlier settings (exposure 1.05, i.e. ×1.75 in three's ACES, a bluish fill at 1.4, fog from 500 m and
a light ribbon tint) washed it out. 60 fps on an M3 in Chrome at 1.5× pixel ratio: about 1.9 M triangles and
570 draw calls with scenery. `window.__sim.world` and `window.__sim.renderer` are exposed for debugging.

## Audio

`audio.ts` plays the sounds of this car, built by `tools/audio` from the team's onboard race footage (see `tools/audio/README.md`).

- **Engine.** `public/audio/engine_{on,off}.ogg` hold one loop per 250 rpm bin from 1000 to 6500 rpm, for on and off throttle; `engine.json` indexes them.
  - The two bins nearest the rpm play, each with both load layers, at playbackRate = rpm / loop rpm.
  - Bins and layers are equal-power cross-faded. The layer fade follows `st.throttleOut` with a 35 ms lag going up and 70 ms going down, so a lift-off reads as a note change and the 150 ms gear-change torque cut gives an audible dip.
  - Gain is 0.5–1.0 with load, plus a small rpm term. A low-pass opens with load, from about 1.3 kHz on the overrun to 10 kHz or more at full throttle.
  - Rev limiter: while rpm is within 60 of `revLimitRpm` and the pedal is past half (`update(st, di.throttle)`), the engine is gated at 16 Hz.
  - Below the lowest bin, the 1000 rpm loops play slowed down (idle 850 rpm = rate 0.85).
- **Engine voices.** Voices live in a pool of 8 slots, each a persistent GainNode. An AudioBufferSourceNode is created only when a slot switches bin, and an unused slot is released after 300 ms. There are no per-frame allocations. After decoding, the loop seams are healed against their padding copies (`healLoopSeams`).
- **Tyres.** Each wheel's squeal is `wheelSqueal`: `slipUse` when the physics provides it, otherwise hypot(α/α_peak, κ/κ_peak), with the peaks read from `car.json` (`audioParamsFromCarJson`).
  - The squeal is silent below 0.85 of the peak and rises smoothly (smoothstep) to full at 1.3.
  - Only wheels with load > 1500 N count, and only above 5 m/s.
  - `squealMix` splits the slip into lateral scrub (and wheelspin) and braking lock-up (κ < 0 past the peak, ABS pulsing included).
  - Scrub plays the recorded squeal at rate 0.94–1.10, rising with sliding speed. Lock-up plays it at about 0.62 through a 1.4 kHz low-pass, plus a 650 Hz noise howl.
  - The squeal attacks in 15 ms (time constant), so it is fully in within about 50 ms of a 60 Hz frame update.
- **Rumble, wind, impacts.** Road rumble is low-passed noise rising with speed, plus a gravel band when wheels are off the surface. Wind is subtler than before. The impact thump comes from `st.impact`. After a launch into space, the engine winds down and fades.
- **Output.** Everything goes through one master DynamicsCompressor set up as a soft limiter (−12 dB threshold, 12:1).
- **Startup.** The files are fetched at boot (`audio.preload()`). The 48 kHz AudioContext starts on the first gesture, and M mutes. `window.__sim.audio` exposes the player. `CarAudio.start(ctx)` also accepts an `OfflineAudioContext`, which `tools/audio/render_player.js` uses to render and analyse the real graph.
- **Fallback.** If the samples are missing or fail to decode, a plain oscillator plays instead.

## Menus

- **Main menu** at boot (replaces the old start overlay): Track (choice; registered tracks without `wip`), Hot lap,
  Race · 5 laps vs the 2026 field (its note is the field line: "40 of 133 cars on this device" on phones and tablets,
  "all 133 cars" on a computer; `field-select.ts`), How to play (`howto.ts`), Touch controls (touch devices), Controls &
  calibration (pads and keys), Graphics, Scoreboard (hot-lap boards; name, Transfer code, Use a transfer code), What's
  new, Credits (`credits.ts`: disclaimer and opt-out contact, map / terrain / software notices, field-car models with the
  non-commercial statement, engine-sound sources, privacy note) and Report a bug / request a feature (`feedback.ts`,
  POST /api/feedback, a public GitHub issue). Load progress and the version line (`v0.4.0 · <commit>`,
  `src/app/changelog.ts`, commit from vite `define`) show under the title; the mode rows are disabled until assets are
  loaded (or say "needs WebGL 2" when the browser has none: `webgl.ts`). Picking a mode is the user gesture that starts
  audio. **What's new** is the release history: one
  MAJOR.MINOR.PATCH number per publish to main / lemons-sim.app (MAJOR milestones, MINOR content and features, PATCH
  look / sound / AI / fixes), newest first, each entry naming the circuits whose lap times reset (the board key is
  `PHYSICS_VERSION`, not the version). Previews are not releases: everything since the last publish goes into the top
  entry, which keeps `date: ''` (shown as "preview") until it ships. Mirror the version in package.json;
  `changelog.test.ts` checks both.
- **Pause menu** (Start / Esc / O while driving): Resume, Restart (mode start procedure, fresh session), Camera (choice),
  Driver view, Auto-shift, ABS, the mode's rows (hot lap: Ghosts submenu with per-ghost toggles and the delta
  reference, Submit last lap; race: Standings, Seed, Results), Scoreboard, Touch controls and Reset car (touch devices),
  Controls & calibration, Graphics, Mute, AI engine sounds, Main menu. Clicking the dimmed backdrop resumes. Race
  results have no scoreboard row while race boards are closed (`RACE_BOARDS_PUBLIC`, docs/scoreboard.md).
- **Navigation:** d-pad or left stick (repeat after 350 ms, then every 120 ms), A select, B back, Start resume;
  keyboard arrows / WASD, Enter / Space select, Esc back. Mouse and touch: tap a row; tap ‹ › on a choice.
  In the controls panel B / Start / Esc close it (when not assigning). On a page whose body overflows (What's new,
  Credits) down on the last row / up on the first scrolls the body a step instead of wrapping the cursor; wheel and
  touch scroll it directly, and its scrollbar stays visible.
- Footer hints and the help overlay name controls in the glyphs of the connected pad (Xbox A/B/RB, PlayStation ✕/○/R1,
  Nintendo B/A/R, generic "Button n"); keyboard users see key names.

## Modes

`modes/mode.ts` defines the contract. index.ts owns the vehicle, lap timer, ghosts, HUD and camera; a mode only
decides what happens around the player's car.

```ts
interface GameMode {
  id: 'hotlap' | 'race'; label: string;
  start(): void;            // enter: run the start procedure
  restart(): void;          // pause menu → Restart
  reset(): void;            // Back / R: hot lap → rolling start; race → recover on track where you are
  step(dt: number): void;   // every 1 ms physics step, after the player's vehicle.step
  onLap(lap: Lap): void;    // player completed a lap (from the core lap timer, sampled at 200 Hz)
  frame(dt: number, now: number): void;  // once per rendered frame (ghosts, AI rigs)
  hud(): { banner: string | null; timing: boolean; delta: number | null; showDelta: boolean };
  pauseEntries(): MenuEntry[];           // inserted after ABS in the pause menu
  dispose(): void;
}
```

`ModeContext` gives a mode: physics, track, vehicle, timer, ghosts, ghostData, hud, input, `simTime()`, `s()`,
`playerPos()`, `rollingStart()`, `recoverAt(s)`, `setScheduleLap(lap)` (auto-shift gear schedule) and `toast()`.
`ModeHost.set(id)` disposes the old mode before starting a fresh instance of the new one.

The race director (src/physics/ai) plugs into `modes/race.ts` at the `TODO(race-director)` comments: create it in
`createRace`, grid it in `start()`, step it in `step(dt)`, pose AI rigs in `frame()`, read position / field size for
the banner, and tear down in `dispose()`.

## Controls

| Action | Xbox gamepad | Keyboard |
|---|---|---|
| Steer | Left stick (deadzone 0.08, curve 1.3) | ← → / A D |
| Throttle | Right trigger | ↑ / W |
| Brake | Left trigger | ↓ / S |
| Shift up / down | RB / LB | E or Shift / Q |
| Handbrake | B | Space |
| Cycle camera | Y | C |
| Auto-shift toggle | X | T |
| Reset (hot lap: start line; race: recover) | Back/View | R |
| Pause menu | Start (reserved) | Esc / O |
| Mute / help / controls panel | – | M / H / K |

A is free while driving (menu select). These are the defaults; all except Start, Esc, O, M, H and K are remappable
in the controls panel (K, or Controls & calibration in either menu). The help overlay follows the current bindings.

### Controls panel and calibration

- **Raw readout** of every axis and button of each connected gamepad at 30 Hz.
- **Assign**: click, then move/press the control; the first input that moves
  more than 0.5 from where it was is bound (axis with direction, or button).
  Steer takes axes only (move the stick LEFT). Keyboard Assign takes the next key.
- **Calibration** per steer/throttle/brake: capture range (4 s sweep), deadzone,
  invert, response curve exponent 0.5–2.5 with a graph and a live marker.
  Defaults: steer 1.3, throttle 1.0, brake 1.4.
- **Test** strip shows the final steer/throttle/brake and each pedal's source.
- Saved in localStorage per gamepad id (`probeSim.controls.v1.pad:<id>`) and
  `probeSim.controls.v1.keys`; works without storage. Driving pauses while the
  panel is open. Pad profiles carry `v: 2`; an older profile is migrated on load
  (buttons on the old defaults move to the new ones, custom buttons stay unless
  two controls would share a button, then all buttons reset; calibration is kept),
  saved back, and a one-time toast names the new layout.

Pedal sources: by default throttle = RT (b7), brake = LT (b6). A source that
has reported an intermediate value is used proportionally; one that has only
reported 0/1 is ramped like a key. With non-standard mappings, trigger axes
(−1..1 resting at −1) are tried as a fallback. A trigger that reads pressed from
the first sample is ignored until it has been released once.

## Fallbacks

A missing asset (HTTP error, or Vite's HTML fallback page) is replaced and
listed in the bottom-left status line and on the main menu:

- `track.json` missing → `devtrack.ts` oval + its heightfield (also forced with `?devtrack=1`).
- `heightfield.bin` missing → flat ground under the lowest track point.
- `ortho.jpg` missing → procedural canvas drawn from the track edges.
- `ghosts.json` missing → three synthetic speed-profile laps (optimal + two "real").
- `scenery.json` missing → no scenery; the old floating corner signboards are shown instead. Far terrain files missing → no far terrain.
- `car.json` missing → `{}` passed to `loadCarSpec` (fine for the stub; the real loader may reject it).
- `probe.glb` missing → box/cylinder/torus car with the same node names.

## Switching from the stub to the real physics

`?stub=1` always uses the stub. When `src/physics/index.ts` exists, change this
one line in `src/app/physics-loader.ts`:

```ts
import * as real from './physics-stub';
```
to
```ts
import * as real from '../physics';
```

Then `npm run build` — the real module must be assignable to `PhysicsApi` in
`physics-types.ts` (it is a structural copy of CONTRACTS §4).
