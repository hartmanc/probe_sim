# AI engine families: notes

Every AI car gets an engine voice from one of 13 **families**. Each family is a set of sample loops cut from online
onboard videos. The player's Probe keeps its own set (`public/audio/engine*.ogg`), which `index.json` lists as
`mazda_kl_v6` without copying it. This is the **rough pass**. As the brief says, it only has to be good enough for
the AI cars to be believable.

## Files

| Path | What |
|---|---|
| `tools/audio/loopkit.py` | Loop-making DSP shared with the Probe build, moved verbatim out of `build_engine.py`: time-warp, spectral gate, loop search, crossfade, levels, pitch-shift. The Probe build was rerun into a scratch folder after the move. Its sprite PCM and `engine.json` are identical, and the decoded Ogg matches the shipped files sample for sample; only the random Ogg stream serial differs. The shipped public files were not regenerated. |
| `track_unseeded.py` | rpm from audio alone. Run it on its own to repeat the Probe validation. |
| `build_family.py --family <id>` | The whole build for one family (see Method). |
| `families.json` | The family definitions, the alias regexes, the fallback by layout and cylinders, and the exhaust-note-to-muffler table. |
| `sources.json` | Every source: URL, title, uploader, licence, seconds used (`t0`/`t1`) and notes. `skip: true` marks a source that is logged but not used. |
| `make_index.py` | Writes `public/audio/families/index.json`. `--check` prints the per-car mapping and writes nothing. |
| `previews/<id>.png` | Per family: the rpm track over the spectrogram with confidence and load, the chosen loops, seam correlation per bin, loop spectra against engine order, and the preview sweep. `probe_validation.png` is the tracker check. |
| `cache/` | Downloaded audio (FLAC) and track caches. Git-ignored by `tools/**/cache/`, and treated as untrusted data: only ffmpeg and soundfile read it. |
| `public/audio/families/<id>/` | `engine_on.ogg`, `engine_off.ogg` (Opus 48 kbps mono), `engine.json` and `preview.mp3`. The preview is a 12 s sweep for listening: idle → redline on throttle, 0.6 s on the limiter, then overrun to idle. It is not loaded by the game. |

## Method

1. **Audio:** each source's `[t0, t1]`, mono 48 kHz. The build downloads it with yt-dlp (audio only) if the cache file is missing.
2. **Unseeded rpm** (25 ms frames, 170 ms window on a 12 kHz copy):
   - **Whitened spectrum:** the spectrum in dB minus its running median over ±60 Hz, with negative values set to zero.
   - **Comb:** teeth at orders 0.5·k of crank rotation, weighted for the layout. The firing order F = cylinders / 2 and its multiples get weight 1. The half-firing ladder F/2·j gets 0.7 for V, flat and odd-fire engines, or 0.25 for even-fire inlines. All other half orders get 0.08.
   - **Score:** Σ w·(W − c) over the teeth in a fixed 25–1500 Hz band, where c = the frame's mean whitened level + 2.5 dB. An empty tooth costs c, which makes sub-multiples of the true rpm lose. Empty teeth on the weak orders cost 0.25·c, so a weak but real half order still beats the multiple of the rpm that skips it.
   - **Contrast term:** the score also gets 0.3 × the comb contrast (main-ladder teeth minus the midpoints between them). This term fixed the old-car recordings, where low-frequency rumble pulled the tracker down to a third of the rpm.
   - **Search and continuity:** the grid runs from 700 rpm to min(8500, 1.15 × redline) in 0.4 % steps. Viterbi dynamic programming joins the frames: changes up to 150 rpm per frame are free, a quadratic penalty applies beyond that, and the cap is 18 % per frame.
   - **Octave-slip repair:** an engine can't change speed by ×1.75 within 0.4 s, so a step like that is an octave error. The path is split there, and each piece takes the ×0.5/×1/×2 that continues its most confident neighbour. A flip happens only when it closes a clear step, and never pushes a piece out of range.
   - **Per-source octave check** (`build_family.py`): an entry's `context` says what kind of footage it is. Track footage (the default) must have a median confident rpm between 0.42 and 0.92 × redline; street footage between 0.25 and 0.8. Otherwise the whole source is relabelled ×2 or ×0.5, and the factor is logged in engine.json as `octave_relabel`. An entry can also pin the factor with `octave`.
   - **Why the octave handling is needed:** open-header V8s carry every half order, so the comb alone can't tell rpm from rpm/2. For cross-plane V8s the main ladder is also order 1, not 2, because the per-bank burble at orders 1 and 2 outweighs the firing order 4.
   - **Confidence:** the comb contrast in dB, plus an octave margin.
   - **Load:** on = rpm rising (> 120 rpm/s over ±0.25 s) and loud/bright for its rpm, or steady and clearly loud. Off = rpm falling and quiet/dark. The loudness and the spectral tilt (1–4 kHz vs 0.1–1 kHz) are judged as residuals from their trend against log rpm. Shift drops (< −3500 rpm/s) are left unlabelled. The label is median-filtered over ±0.15 s.
3. **Candidates:** per bin and load, runs where rpm is within ±120 for ≥ 0.45 s (tier `steady`) or within ±(9 % + 80) for ≥ 0.3 s (tier `sweep`), with the right load label and confidence ≥ the 35th percentile. Overrun runs must also fall at 150–3000 rpm/s.
4. **Processing:** loopkit, exactly as for the Probe. Time-warp to constant rpm, spectral gate, 40 Hz high-pass, loop search over whole engine cycles, power-preserving crossfade.
   - The gate's harmonic spacing is min(1, main order).
   - The loop length comes from the size budget: about 0.5 s with 250 rpm bins. Below 0.42 s the build switches to 500 rpm bins.
   - Candidates whose loop repeats a click (tick > 8) are rejected.
5. **Levels:** every on loop gets the same A-weighted level. Off loops sit at on + the median measured gap, clamped to −9…−4 dB. A slope over rpm was tried first, but fitted across different recordings it was noise.
6. **Gaps:** missing bins are pitch-shifted from the nearest real bin of the same load. A short source is tiled first. If a load has no real bin at all, it borrows the other load, darkened.

## Tracker accuracy on the Probe's own footage

GL030045, three 120 s slices, compared with the logger-seeded tracker cache (`tools/audio/cache/track_GL030045.npz`):

| Slice (s) | Median error | p90 | Within 150 rpm | vs logger | On-label precision (thr ≥ 50 %) | Off-label precision (thr ≤ 20 %) |
|---|---|---|---|---|---|---|
| 300–420 | **29 rpm** | 600 | 76 % | 31 | 87 % | 64 % |
| 900–1020 | **35 rpm** | 686 | 70 % | 42 | 85 % | 57 % |
| 2000–2120 | **28 rpm** | 385 | 79 % | 29 | 85 % | 60 % |

- The median is well under the 80 rpm target.
- The p90 comes from overrun stretches, where the Probe's harmonics nearly vanish. The seeded tracker is unsure there too.
- The off label is only about 60 % precise against the OBD throttle, which is read every 0.7 s and lags. The build therefore also requires a falling rpm for off candidates.
- Earlier tracker versions failed in instructive ways: a mean-normalised comb locked onto 1/3 of the rpm, and then onto 2× rpm on the overrun. The cost-per-tooth score fixed both.

## Families

Real bins come from the family's own audio at their own rpm; the rest are pitch-shifted from the nearest real
bin. Sizes are the runtime files (two sprites plus engine.json); each `preview.mp3` adds about 95 KB.

| Family | Bins (rpm / step) | Real bins | Off − on (dB) | Size | Sources (licences) |
|---|---|---|---|---|---|
| `bmw_m20_i6` | 1000–6500 / 250 | 23/23 on, 13/23 off | −4.0 | 171 KB | 3 (all CC BY) |
| `classic_v8_lowrev` | 750–5000 / 250 | 11/18 on, 14/18 off | −4.0 | 169 KB | 3 (Standard YT) |
| `gm_sbc_v8` | 1000–6000 / 250 | 19/21 on, 16/21 off | −7.6 | 162 KB | 3 (Standard YT) |
| `mazda_b_i4` | 1000–7250 / 250 | 21/26 on, 16/26 off | −5.2 | 189 KB | 2 (CC BY) |
| `mini_supercharged_i4` | 1000–6750 / 250 | 22/24 on, 20/24 off | −7.4 | 176 KB | 2 (CC BY, Standard YT) |
| `modern_i4_stock` | 1000–6750 / 250 | 21/24 on, 15/24 off | −5.1 | 172 KB | 1 (Standard YT) |
| `ohv_v6` | 1000–6000 / 250 | 20/21 on, 13/21 off | −4.0 | 174 KB | 5 (Standard YT) |
| `sohc_i4_loud` | 1000–6500 / 250 | 23/23 on, 21/23 off | −5.8 | 182 KB | 3 (CC BY, Standard YT) |
| `subaru_fa20_flat4` | 1000–7500 / 250 | 27/27 on, 21/27 off | −7.9 | 174 KB | 2 (CC BY) |
| `toyota_1jz_turbo` | 1000–7000 / 250 | 25/25 on, 23/25 off | −4.0 | 172 KB | 2 (CC BY, Standard YT) |
| `twincam_i4_loud` | 1000–7500 / 500 | 12/14 on, 13/14 off | −9.0 | 134 KB | 2 (CC BY, Standard YT) |
| `vintage_i6` | 750–5000 / 250 | 16/18 on, 9/18 off | −4.4 | 171 KB | 2 (Standard YT) |
| `vw_aircooled_flat4` | 1000–4750 / 250 | 16/16 on, 13/16 off | −9.0 | 140 KB | 2 (Standard YT) |
| `mazda_kl_v6` (Probe, referenced) | 1000–6500 / 250 | own footage | — | 352 KB | team footage |

**Sources:**
- `sources.json` holds the full list: URL, title, uploader, licence and seconds used. Each family's `engine.json` repeats the sources it used, with any octave relabel.
- Roughly half the material is CC BY and needs attribution if the game is published. The rest is under the Standard YouTube License, which is fine for a private rough pass. Replace those clips, or get permission, before any public release; the per-family licence column above shows which ones.
- Logged but not used (`skip`):
  - The Hudson Lemons chase video: two engines and fixed tones.
  - One flathead clip: no frame reaches 2 dB comb contrast.

**Substitutions:**
- `ohv_v6` relies on a '92 Ranger Lemons in-car whose engine (a 2.9 Cologne or a 3.0 Vulcan) is inferred, plus short street clips of a Taurus, Ranger, Aerostar and Probe LX.
- `twincam_i4_loud` uses AE86 4A-G/20v footage only; no Alfa or Opel source was found.
- `vintage_i6` uses a slant-six Polara and a 235 Corvette (both street driving); the Hudson was rejected.
- `classic_v8_lowrev` uses 1936 flathead street drives and a Charger 318 clip, with no track pulls.

## AAC fallback

Older Safari cannot `decodeAudioData` Ogg Opus. Every family directory also holds `engine_on.m4a` / `engine_off.m4a`
(AAC-LC, 96 kbps, 48 kHz mono, Apple AudioToolbox when ffmpeg has it), about 0.25-0.34 MB per family and 4.1 MB for all 13.
`mazda_kl_v6` has none of its own: it uses the Probe's files, which already have a fallback.

- **Build:** `uv run --python 3.12 --with numpy,scipy,soundfile python -I tools/audio/encode_fallback.py --families [id ...]`
  (no ids = every family directory). The Ogg files are only read. Re-run it after `build_family.py`, which rewrites `engine.json` without the block.
- **What it writes:** a `fallback` block in each family's `engine.json` (`on`, `off`, `format`, `offset_s`, `offsets_s`, `priming_s`,
  `lengths_s`; no `squeal`), measured as for the Probe: ffmpeg decodes both files and the lag is found by cross-correlation.
  Every other field is left as it was. Measured offsets are 0 to within 1 µs (the MP4 edit list is honoured), and `priming_s` is 0.044 s (2112 samples).
- **Player:** `loadFamily` decodes the Ogg first and uses the m4a if the fetch or decode fails, or if `canPlayOggOpus()` says no.
  Loop offsets are shifted by `fallbackShift` (offset, plus priming when the decode came back longer than `lengths_s`), as `audio.ts` does.
  If neither codec works the load rejects and `FieldAudio`'s retry back-off applies.
- **Index:** `index.json` and `make_index.py` do not know about the fallback; the player reads each family's `engine.json`.

## What sounds rough, and why

- **Pitch-shifted bins:** these are mostly the off-throttle top end and idle. A shift of up to about ×1.3 changes the timbre (formants move with it). It is audible on `vintage_i6` and `classic_v8_lowrev`, where real off bins are 9–14 of 18.
- **Short loops** (0.42–0.9 s, set by the 200 KB budget) repeat audibly on a steady cruise. That's fine at a distance, but noticeable if an AI car sits beside the player at constant rpm.
- **Octave consistency:** this is the real weak point of unseeded tracking from compressed YouTube audio.
  - Short stretches can still sit an octave off: about 50 s of the first Camaro source, and the first 30 s of the Mid-Ohio Miata. Loops cut there play an octave out of place. In the preview this shows as a step in the harmonic ladder around 2000 rpm on `gm_sbc_v8`.
  - Each family's `previews/<id>.png` shows these stretches.
  - The fix is a per-entry `t0`/`t1` trim or an `octave` pin in `sources.json`; then rebuild that family.
- **`classic_v8_lowrev`:**
  - The flathead street clips have weak harmonics: only about 20 % of frames reach 2 dB contrast.
  - Nothing goes above about 3500 rpm, so the top bins are pitched up.
  - It will sound like a cruising old V8 rather than a race car, which suits the low-revving cars it serves.
- **Sustained high rpm:** `ohv_v6` and `vw_aircooled_flat4` have little of it, and `vintage_i6` is street-only.
- **Load labels:** the on/off label is about 85 % / 60 % precise on the Probe test. Some 'off' loops are really light-throttle cruise, so lift-offs are less distinct than the player's.
- **Off − on level:** where the measured gap was small (−4 dB, the clamp), lifting off mostly changes the brightness, through the player's muffler × load.
- **Mixed-in sounds:**
  - `toyota_1jz_turbo`: the S13 and E36 drift footage carries limiter bouncing and tyre smoke noise into some loops, and the turbo whistle is only present where the loop happens to catch it.
  - `mini_supercharged_i4`: the supercharger whine is in the loops (it scales with rpm, so the player keeps it right).
- **Preview limitation:** `preview.mp3` is rendered by a Python emulation of the player (two bins × two loads, rate = rpm / loop rpm, the 16 Hz limiter). It is not a browser render. The real `FieldAudio` path is covered only by the unit tests with a fake Web Audio.

## Integration spec (race integration owns this; `src/app/audio-field.ts` is the player)

**Setup (once per race):**
```ts
const index = await fetch('audio/families/index.json').then(r => r.json());
const field = new FieldAudio(ctx, fieldBus /* GainNode → the same master as CarAudio, or its own */, {
  maxVoices: isPhone ? FIELD_VOICES_PHONE /* 4 */ : FIELD_VOICES_DESKTOP /* 8 */, index });
field.preload([...new Set(gridCars.map(c => index.cars[c.number]?.family ?? index.default))]);
```
- `FieldAudio` never touches `CarAudio`.
- It needs a running AudioContext. Create it after the player's audio starts and reuse that context.

**Choosing each car's family:** the per-car table `index.cars["<number>"]` gives `{family, trim, muffler, rpm_scale, redline, engine}`. It is precomputed from `public/cars/field/identity.json` by `make_index.py`.
- **Aliases:** regexes over `engine.family make model`, first match wins.
- **Fallback:** by cylinders + layout (identity's `I4`/`V8`/`flat4` mapped to inline/v/flat), then by cylinders alone, then `default`.
- **Trim:** a stable 0.97–1.03 from the car number, so two Miatas don't sound identical.
- **Muffler:** from `engine.exhaust_note`: straight pipe 0, loud 0.1, side-exit 0.15, stock muffler 0.6.
- **rpm_scale:** set for #34's Suzuki G10 three-cylinder. It plays the I4 family at 0.75 × rpm so the firing frequency matches, with trim 1.04.
- **New cars:** call `familyFor(index, {engineFamily, make, model, cylinders, layout})`. `pace.json` is not needed for the sound. Its car numbers key `index.cars`, and the AI's redline already comes from the physics.

**Per frame:**
```ts
field.update({ pos, vel, quat }, aiCars.map(c => ({
  id: c.number, pos: c.pos, vel: c.vel,
  rpm: c.rpm * (meta.rpm_scale ?? 1), throttle: c.throttle, redline: c.redline,
  family: meta.family, trim: meta.trim, muffler: meta.muffler })));
```
- **listener:** the camera or the player car: world position (m), velocity (m/s) and orientation quat. The axes are the physics' own: z up, body x forward.
- **pos, vel:** world frame.
- **throttle:** the AI's applied throttle, 0..1.
- **redline:** drives the limiter stutter, which kicks in at redline − 60 with throttle > 0.5.

**What the player does for you:**
- N nearest within 150 m, with hysteresis.
- Distance gain max(0.04, 5 m / d), fading to 0 over the last 20 % of the range.
- Equal-power PannerNode, with its own distance roll-off off.
- Doppler as a rate factor, clamped ±15 %.
- Fade in about 0.15 s and out about 0.25 s; a voice is reused after 0.5 s.

**Limits:**
- The families have no AAC fallback. In browsers that can't decode Ogg Opus (older Safari), the AI cars are silent.
- Mix level against the player's engine is not set. Start `fieldBus.gain` around 0.5 and tune by ear.
