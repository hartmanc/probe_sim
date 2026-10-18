# Scoreboard client — notes for the lead (17 Oct 2026)

Spec: `docs/scoreboard.md`. Client code: `src/app/scoreboard-client.ts` (HTTP, localStorage, submissions, board
context, `submitRace`), `src/app/scoreboard-ui.ts` (new-best prompt, name editor, arcade top 10),
`src/app/modes/hotlap.ts` (`HotlapLoop`), `src/app/index.ts` (wiring). Tests: `src/app/__tests__/scoreboard-client.test.ts`.

## What changed in the loop

- The player's car now runs in `HotlapSim` (src/scoreboard/sim.ts) in **both** modes. index.ts no longer owns a
  Vehicle, a physics surface, a LapTimer, `stepCount`, `simTime` or the gear-schedule code; `physicsStep()` is gone.
- `HotlapLoop` (modes/hotlap.ts) is the frame → fixed-step bridge: same accumulator, same 1 ms step, same 50 ms
  frame cap. Input is read only inside `sim.step()`'s sampler (every 10th step, 100 Hz) and held; shift presses
  are latched until the next sample (up to 10 ms later than before — not noticeable). After every step it calls
  `mode.step()`; lap events go to `onLap(lap, tag)` where `tag` is the most-used input type at the samples of that lap.
- Rolling start / R / Restart = `loop.reset()` → `sim.reset()`: new Vehicle + Surface, timer cleared, step counter
  zeroed, new recording. The rolling start itself (130 m before T11, 22 m/s) now comes from `canonicalReset()`.
- Auto-shift, ABS and the reference ghost (gear schedule) go through `hsim.autoShift` / `hsim.abs` /
  `hsim.setRef()`, so they are applied at the next sample and land in the trace. The pause-menu toggles read the
  requested values. The ABS row is no longer disabled for the stub (the sim is always the real physics).
- The HUD / off-track tag / scenery still use index.ts's own `createTrackSurface()`; the sim's surface is private.
- `ModeContext.vehicle` is now a getter (a reset makes a new Vehicle); `ctx.simTime()` / `ctx.s()` read the sim.
  Race recovery (`recoverAt`) still calls `vehicle.reset()` on the current vehicle — fine, races are not replayed.
- `?stub=1` no longer affects the player's car (ghosts only).
- Easter egg, ghosts, delta, corner table unchanged (verified in Chrome).
- `window.__sim` gains `hotlap` (the HotlapSim), `loop`, `scoreboard: { client, ui }`; `vehicle` is a getter.
- `menu.ts`: `MenuPage.body?()` — optional custom content above the rows (the scoreboard table). `hud.toast(msg, ms?)`.

## Scoreboard flow

- Lap event in hot lap: `checkHotlap()` → if valid, faster than this device's PB (`probe-sim.scoreboard.pb.<board>`)
  and faster than anything already offered this session: the trace is copied **in the lap handler**, then the
  prompt opens (a pause-style menu card, sim paused): "NEW BEST 2:18.904 · Lap 1 · Submit as NAME?" →
  Submit / Change name / Skip (no name yet: Enter name). The POST runs in the background; the result
  (rank, replayed time, or the 422 reasons / "offline" / "reload the page") is a toast. PB stored only on ok.
- Not submittable (a new best that cannot be posted) is told in a toast with the reason: lap > 6 after a reset,
  trace over the caps, stand-in assets loaded, lap time outside 90–600 s. After lap 6 a one-off hint says to reset.
- Name editor: keyboard types into the field (Enter saves, Esc cancels); pad: letter grid with d-pad / stick,
  A types, B deletes (B on empty cancels), Start = done; touch: the same grid is tappable (no OS keyboard).
- Scoreboard screen: main menu and pause menu → Scoreboard. Fetches on open (no polling); rows Board (only when a
  race board exists), Refresh, Name, Back. Top 10 in arcade style (rank, name, time / laps+metres, input, date),
  own row highlighted, own rank under a "· · ·" separator when outside the top 10, OFFLINE / ERROR states.
- On load `GET /api/scores` checks the server's board key against ours; a mismatch toasts "reload the page".

## Fix: prompt vanished when typing after a pad lap (owner report)

Root cause: the prompt was a closable menu card, and keys typed on it went to input.ts, where O and Esc mean
"close menu" (and W A S D mean "move", K opens the controls panel). So typing "Coby" closed it at the "o" and
counted that as Skip. Fix: a capture-phase keydown in `ScoreboardUI` (`routeScoreboardKey`) sends any printable
key on the prompt into the name editor (starting a fresh name). In the editor, keys always go to the name, even if
the pad grid had focus. Esc skips the prompt / cancels the editor. The prompt is no longer closable: only
Submit / Skip close it, and pad Start / B do nothing on it. In the grid, pad B cancels only on a fresh press of
an empty name (`editorBack`: ignores the first 400 ms after opening and B pressed right after clearing the name).
A lap not yet posted (skipped, dismissed or failed) stays in the pause menu as "Submit last lap".

## Testing locally

- `npx vitest run src/app/__tests__/scoreboard-client.test.ts` — a lap driven through `HotlapLoop` (variable frame
  dt, a reset, ABS / reference changes, latched shifts) replays to the identical lap time with `replayTrace`, and
  the resulting submission goes through `handleScores` (memory store) to rank 1; plus client/offline/PB/grid tests.
- Browser against a local API:
  `SCOREBOARD_ALLOWED_ORIGINS=http://localhost:5173 vercel dev --listen 3000` (memory store without Redis env),
  then open `http://localhost:5173/?api=http://localhost:3000`. Without `?api=` the Vite server has no API and
  the board shows SCOREBOARD OFFLINE (driving unaffected).
- A scripted lap through the live path in the console: replace `__sim.loop.read` with a sampler returning
  `{ steer, throttle, brake, handbrake, tag }` (e.g. the autopilot from `src/scoreboard/__tests__/fixtures.ts`).

## What the race mode must call

```ts
import { setBoardContext, submitRace } from '../scoreboard-client';
setBoardContext({ raceAiVersion: AI_VERSION });   // once: enables the Race board in the Scoreboard screen
// at the end of the race (or on retire):
void submitRace({ metres, laps, aiVersion: AI_VERSION, seed, position, finished });
```

`submitRace` compares with the device PB for `race:<track>:<car>:<physics>:<ai>`, shows the same new-best prompt,
POSTs and resolves `{ status: 'submitted' | 'skipped' | 'not-best' | 'unavailable' | 'failed' }`; it never throws.
`seed` goes into the reserved `replay` field. Race mode keeps using the shared HotlapSim car (its trace is recorded
but never sent); if the race director needs its own stepping, it can build its own loop.

## Open items

- The sim records a trace in race mode too and for as long as the player drives without a reset (memory grows
  ~a few MB per 10 min of pad driving; nothing is sent). A `record` toggle in HotlapSim would need a scoreboard
  change (and a `PHYSICS_VERSION` thought), so it was left alone.
- Skipped laps are remembered for the session only (a slower lap does not re-prompt; a reload forgets).
- Cross-engine determinism (Safari / Firefox) is untested, as docs §6 says.
- `src/physics/__tests__/ai_race.test.ts` (AI agent's work) was failing at the time of writing; not touched.
