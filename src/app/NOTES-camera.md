# Cameras, driver view, look-around, game-over card — notes (17 Oct 2026)

## Driver view (cameras.ts)
- Seat offsets are applied in the app on top of the glb `cam_driver` (model frame): defaults eye +4 cm, seat −4 cm
  (back), 90° horizontal FOV. At 16:9 the rim top sits 18.5 % of the frame height below the horizon (15.6–17.5 % at
  1000×1000); the gauges stay visible through the top of the wheel. Persisted in localStorage
  `probeSim.camera.v1.driverView`; pause menu → Driver view (eye height, seat fore/aft, FOV, look-stick release, reset).
- FOV rule: every camera has a horizontal FOV (chase 90°, hood 95°, driver setting); vertical = from aspect, capped at
  1.05× its 16:9 value (`VFOV_CAP`) so square / portrait windows do not fill with headliner and dash (square → 61.7°
  vertical, was 70°). Phone landscape (2.16:1) gets a narrower vertical than 16:9.

## For the Probe model agent (glb geometry, measured by ray casts from cam_driver)
- The windshield opening seen from the driver's eye is only ~12° tall: the header trim / cage bar bottom is at
  y ≈ 1.17 m, z ≈ 0.28 (0.68 m ahead, 12 cm above the eye) and the gauge binnacle top at y ≈ 1.02, z ≈ 0.22.
  Headliner at y ≈ 1.297 fills the top quarter of any frame. In the onboard photos the header band sits clearly higher.
- The banner band itself is not too tall (≈3–5 cm visible above the cage bar, behind it); it is the low/close
  header + cage bar, not the banner, that eats the frame. In the photos the banner is a ~15 cm strip *below* the bar.
- The steering wheel rim is only 0.35 m from the eye (rim top y 1.009, z −0.051); a real seated driver is ~0.5 m away.
  With the glb as is, moving the seat back costs view out of the windshield, so the defaults are a compromise.

## Look-around (input.ts → cameras.ts)
- Pad: the stick not used for steering (standard mapping: right stick, axes 2/3; left stick if steering is bound to
  the right one; disabled if any binding uses those axes, e.g. throttle on the right stick Y; disabled on
  non-standard mappings). Radial deadzone 0.15, expo 1.6. Its click (RS / L3) looks back while held unless bound.
- Driver / hood: yaw ±120°, pitch ±25°. Chase: orbit ±180°, elevation ±25°. Out: fast follow; release: spring
  back at ≤ 4.5 rad/s (≈0.5 s from full). Look back snaps to 180° and back.
- "Look stick released: Holds full look" (persisted `probeSim.controls.v1.lookHold`): past 95 % the look latches;
  centring and moving the stick again releases it.
- Keys (remappable in the controls panel): `,` / `.` look ±90° while held, Backspace looks back. Mouse: drag on the
  3D view (half the short side = full look), springs back on release.

## Game-over card (hud.ts, index.ts, input.ts)
- Card with a large Reset (hot lap) / Recover (race) button and Main menu. While it is shown: pad A, Back and
  Start, keys R, Enter and Space reset (new Action 'confirm' = Enter / Space / pad A outside menus; Start resets only
  when the pad is the input source, Esc still pauses). Hint follows the input: "Press A or Back", "Tap Reset",
  "Press R or Enter".
- Race: the race mode's banner still says "OUT OF THE RACE · Restart from the pause menu" after a launch while the
  card offers Recover (which works: the car is put back on track). The race agent should decide which one wins.

## Verified
- Headless Chromium (playwright-core from ~/dev/frame-it) against :5173 for timings and screenshots; Claude-in-Chrome
  tab for the menu rows, help rows, persistence across reload, console (no errors). The shared Chrome window is
  844×303 and cannot be resized, so the 1600×900 / 1000×1000 shots are headless.
