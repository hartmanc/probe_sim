# Menu / modes / controller glyphs — notes for the lead (Oct 2026)

Interface documentation lives in `src/app/README.md` (Menus, Modes, Controls). This file holds what the lead
needs to merge: contract additions, assumptions and open items.

## Suggested CONTRACTS.md addition (§5 App)

- `src/app/modes/mode.ts` is the integration point for game modes. `GameMode` = `{ id, label, start, restart,
  reset, step(dt), onLap(lap), frame(dt, now), hud(), pauseEntries(), dispose }`; the core calls `step` after the
  player's `vehicle.step` every 1 ms and never while a menu is open. The race director (src/physics/ai) is wired
  into `modes/race.ts` at the `TODO(race-director)` comments and needs no change in index.ts beyond, possibly,
  new `ModeContext` fields (e.g. the car model template for AI rigs, the scene to add them to).
- `window.__sim` gains `menu`, `mode` (getter: current GameMode) and `setMode(id)` (starts the mode and closes
  any menu). `hud` no longer has `setAutoShift`, `setCamera`, `setMuted`, `setAbs`, `toggleSettings`.

## Behaviour changes

- Start overlay replaced by the main menu; the settings panel and its ⚙ button are gone (content moved to the pause menu).
- Gamepad defaults: shift RB/LB, auto-shift X, Start = pause menu (reserved, never bindable, capture ignores it),
  A unbound while driving. Keyboard: Esc and O open the pause menu (O was the settings panel); Esc is now reserved.
- Pad profiles saved with `v: 2`. Old profiles are migrated once (see README) with a toast.
- Pause = physics not stepped + AudioContext suspended. The controls panel (K) now also suspends audio.
- In race mode, Reset (Back / R) recovers the car onto the centreline at its current distance, stopped, instead of the
  rolling start; Restart in the pause menu is the rolling start.
- Restart clears the session (laps, best). R / Back in hot lap keeps the session, as before.
- Game-over hint names the bound reset control ("Press R or Back to reset").

## Assumptions

- Non-standard mapping pads get the 'generic' glyphs ("Button n"); menu navigation on them still reads standard
  indices (9 / 0 / 1 / 12–15 / axes 0–1), which may not match. Keyboard and mouse always work.
- Glyph for Xbox 8/9 is "Back"/"Start" (the owner's 360 pad), not "View"/"Menu".
- Hints follow the last device used: the pad becomes the source on any button press or stick/pedal movement; a key press
  switches back to key names.
- Gamepad presses are not a browser user activation, so starting a mode from the pad may leave the AudioContext
  suspended until a key or click (unchanged from the old start overlay).

## Open items

- Scoreboard (main menu) and Standings (race pause menu) are disabled placeholders.
- Race: banner position (P20) and field size (45) are placeholders; the finish after lap 10 only toasts.
- No "Help" row in the menus: the help overlay is H only (pad users see bindings in the controls panel).
- Space-launch / game-over path was not re-triggered in the browser (code path unchanged apart from the hint text).
- `tsc` currently reports errors in `scene.ts` (another stream's in-progress work); none in the files touched here.
