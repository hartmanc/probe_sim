# Phone play (iPhone Safari first, Android Chrome second) — notes for the lead (Oct 2026)

## How it works

- **Tier and touch** (`quality.ts`). `quality.touch` is on for a `(pointer: coarse)` device with `maxTouchPoints > 0`, or with `?phone=1`. `quality.tier` is `'phone'` in the same cases, unless the menu's **Graphics** row (Auto / Phone / Desktop, stored in localStorage, applied on reload) forces it. `?phone=0` forces desktop.
  - The phone tier renders at pixel ratio ≤ 1, capped at 1.2 MP. Shadow maps and the sun's shadow are off, and anisotropy is ≤ 2.
  - After `buildWorld`, `thinScenery` compacts the tree InstancedMeshes in place. Trees within 60 m of the centreline are all kept, half are kept out to 400 m, and a quarter beyond that. Laguna drops from 17 770 to 5 684 instances. `scene.ts` and `scenery.ts` are untouched.
  - There are no post-effects to drop.
- **Touch controls** (`touch.ts`). The controls are a DOM layer (z 4, above the HUD, below menus). It is shown only while driving.
  - Brake is the left third and gas is the right third. Pressure is the touch height: a 6 % dead band at the bottom, full at 92 %. Each finger keeps the zone it started in.
  - Steering defaults to tilt. The phone is held like a wheel and gravity is projected onto the screen plane, so how far it is tipped back does not matter. Which landscape side is up comes from gravity, not `screen.orientation`.
  - Tilt has a 15 Hz low-pass, 32° = full lock at sensitivity 1, and a 1° dead zone. It is recentred at every Hot lap / Race tap and from the menu.
  - The slider (drag in the middle third) is used whenever tilt is not delivering readings. The tilt states are unsupported (plain http) → prompt → requesting → granted → active, or silent / denied.
  - Pause is top right. The − / + shift paddles sit in the upper corners and appear only with auto-shift off.
  - The overlay dims after 2.5 s without a finger.
- **Input** (`input.ts`). Touch is a third source: largest steer, max pedals, and its buttons emit `shiftUp` / `shiftDown` / `menu`. Keyboard and pad still work alongside it.
  - `input.source` is `'keyboard' | 'gamepad' | 'touch'`, and `input.inputTag` is `'pad' | 'keys' | 'phone'` for the scoreboard.
  - Menus are tapped. The footer hints read "Tap select · Tap outside resume".
- **Menus.** Main and pause menus get a **Touch controls** submenu (Steering Tilt/Slider, Tilt sensitivity 0.6–1.8×, Recentre tilt) and a **Graphics** row. The pause menu also gets **Reset car** (touch only: there is no R key).
  - On a phone, "Controls & calibration" is hidden unless a gamepad is connected.
- **HUD** (`style.css`, `html.touch`). Sized for 844 × 390 with `env(safe-area-inset-*)`:
  - compact dash at the bottom centre
  - timing at the top left (lap, current, Δ; last and best hidden)
  - flags at the top centre
  - mode banner left of the pause button
  - status line and help hidden
  - corner table as a card after a lap, closed by a tap or after 12 s
- **Portrait.** A full-screen "Rotate your phone" overlay (CSS `orientation: portrait`). While driving, the pause menu opens and audio is suspended.
- **Page.** The viewport has `viewport-fit=cover`, no zoom, and `apple-mobile-web-app-capable` with `black-translucent` status bar metas. The manifest (`display: standalone`, `orientation: landscape`) has icons 512/192/180 (619 on green).
  - `touch-action: none` and `overscroll-behavior: none` prevent pull-to-refresh and double-tap zoom.
  - Text selection and the long-press callout are off. Menu cards still scroll vertically.
- **Audio** (`audio.ts`).
  - `audio.start()` runs synchronously in the Hot lap / Race click. It creates the context and calls `resume()` inside the gesture, and sets `navigator.audioSession.type = 'playback'` (iOS 16.4+, so the silent switch does not mute the game).
  - A tap after an iOS interruption calls `audio.unlock()`.
  - **AAC fallback.** `tools/audio/encode_fallback.py` writes `engine_on/off.m4a` and `squeal.m4a` (AAC-LC 96 kbps 48 kHz mono, Apple `aac_at`) and adds `engine.json.fallback = {on, off, squeal, offset_s, offsets_s, priming_s, lengths_s}`.
  - The offsets are measured by cross-correlating ffmpeg decodes against the Opus decode. All are 0 to within 0.03 samples, with an edit list hiding 2112 samples of priming.
  - The player fetches the m4a up front if `canPlayType('audio/ogg; codecs="opus"')` is empty, and otherwise falls back when the Ogg decode fails.
  - It adds the offset to every loop offset. It also adds `priming_s` if the decode came back longer than `lengths_s` (a decoder that ignores the edit list).
  - Chrome decodes the m4a to exactly `lengths_s` with lag 0.
  - **Re-run `encode_fallback.py` after `build_engine.py` / `build_squeal.py`**: they rewrite engine.json without the field.
  - The m4a set adds 542 KB, so the folder is now 890 KB. A device only downloads one set.

## Testing on the iPhone

1. **Touch-slider steering (plain http).** On the same Wi-Fi, open `http://192.168.1.125:5173/`. Tilt shows "needs HTTPS" and the slider is used.
2. **Tilt (HTTPS).** Run `npm run dev:https`. It uses `vite.https.config.ts` and `@vitejs/plugin-basic-ssl` on port 5174. The 5173 server is untouched.
   - Open `https://192.168.1.125:5174/` and tap Show Details → visit this website. That is enough for a secure context and the motion prompt.
   - Tap Hot lap and allow Motion & Orientation Access. Hold the phone level when you tap, because that is "straight".
   - For a fully trusted certificate (needed for Add to Home Screen over HTTPS): AirDrop `node_modules/.vite/basic-ssl/_cert.pem` to the phone, install the profile (Settings → General → VPN & Device Management), then enable it under Settings → General → About → Certificate Trust Settings.
3. **Add to Home Screen.** In Safari, tap Share → Add to Home Screen, then start from the icon. It runs full screen in landscape without browser chrome.
4. **Desktop check of the phone path.** Open `http://localhost:5173/?phone=1`. Touch events, or the mouse via pointer events on the zones, drive the car.

## Known iOS limits

- No Fullscreen API on iPhone: full screen only comes from Add to Home Screen.
- No `navigator.vibrate`: paddle haptics work on Android only.
- The tilt permission is asked once per session, and only after a tap and over HTTPS. After a "Don't Allow", iOS will not ask again until Safari is restarted, so the slider is used and the menu shows "tilt denied".
- The manifest's `orientation` is not enforced by iOS, hence the rotate overlay.
- `apple-mobile-web-app-capable` is deprecated but still honoured; the manifest covers newer iOS.
- Web Audio needs the first tap. Ogg Opus decoding exists only on recent iOS, and older devices use the m4a.

## Race integration: AI-car draw cap

`import { quality } from './quality'` (also on `window.__sim.quality`). `quality.maxAiCarsDrawn` is 20 on the phone tier and 45 on desktop.

The race director must simulate every car but add or pose at most that many AI rigs: the nearest to the player by track distance, with the rest hidden. Use `quality.tier === 'phone'` for any other per-tier choice, such as cheaper AI car models or no AI shadows.

## Verified (Chrome, `?phone=1`, 844 × 390 viewport emulated by overriding innerWidth/innerHeight — the window could not be resized)

- **Tier and scenery:** tier phone, shadowMap off, pixel ratio 1, canvas 844 × 390, trees 17 770 → 5 684.
- **Touch input:** synthetic touch PointerEvents gave throttle 0.79 high / 0.20 low and brake 0.97, with steer on the slider at +0.82 / −0.87 and 0 after release. The source became `touch`, tag `phone`.
- **Buttons and menus:** the pause button opens the pause menu; menu taps toggle auto-shift and steering; the paddles shift 4→5→4.
- **Overlays:** portrait pauses and suspends audio; the corner card closes on a tap; Reset car clears a space launch.
- **Layout and errors:** no HUD element is outside the viewport and there are no console errors.
- **Desktop path:** no touch layer, shadows on, pixel ratio 1.5, 17 770 trees, keyboard throttle 1, help table unchanged.

Screenshots are in the session scratchpad `phone/`.

## Files outside the listed scope

- `vite.https.config.ts` (new; it keeps `vite.config.ts` and the running 5173 server untouched).
- `src/app/__tests__/{touch,quality,audio-fallback}.test.ts`.
