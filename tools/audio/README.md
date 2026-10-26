# tools/audio — engine and tyre sounds from the race footage

The sim's engine and tyre squeal are cut from the team's own onboard footage of car #619 at Laguna Seca
(2026-10-12), so the car sounds like this Probe's KL-DE V6 rather than a synthesiser. The road rumble and wind are
filtered noise, made in `src/app/audio.ts`.

Outputs (`public/audio/`, 352 KB in total):

| File | What |
|---|---|
| `engine_on.ogg`, `engine_off.ogg` | Opus 64 kbps, 48 kHz mono sprites. One loop per 250 rpm bin from 1000 to 6500 rpm, for on throttle (≥ 80 %) and off throttle (≤ 10 %). Each loop is stored as `[50 ms tail copy │ loop │ 50 ms head copy]`. |
| `engine.json` | `{sampleRate, bins: [{rpm, on: {offset, duration, rpm, tier, source, seam_corr, tick}, off: {…}}], levels, real_bins}`. `rpm` inside a layer is the loop's exact engine speed, so playbackRate = rpm / layer.rpm. `tier` is `steady`, `sweep` or `pitch-shifted`. |
| `squeal.ogg`, `squeal.json` | A 1.15 s tyre squeal loop from the footage, with its `{offset, duration, f0, source}`. |

## Sources (read-only)

- Audio comes from the race proxies `starlink-go-pro/video/proxies/GL010045…GL040045.LRV`. The audio is the same
  AAC 48 kHz as the clips, and the clips sit at whole seconds inside GL030045 (`common.CLIP_SOURCE`, found by
  cross-correlation, r = 1.000). Only the audio stream is extracted, to mono 48 kHz FLAC in `cache/` (git-ignored, about 0.9 GB).
- Logger: `LagunaData/log_0e98….csv`, the race file. OBD `rpm` and `throttle_pct` are taken at their true read times
  (`timestamp_utc − obd_age_s`, one sample per fresh read, about every 0.7 s). The IMU and GPS speed are used for lateral g.
- Clocks: `video/analysis/sync.json` (logger offset +3444.40 s, from a yaw-rate match) and the camera start
  epochs `sync.py STARTS`.

## Alignment: video time → real time → logger (`align.py`, `preview_alignment.png`)

For each candidate offset, the logger rpm predicts where the firing harmonics should sit in the audio: order 3 is rpm/60 × 3 Hz and order 6 is twice that. The script scores the whitened log spectrum at those frequencies. The offset with the highest score wins.

**Result:** the sync.json offset is right, but each GoPro chapter file's start time in `STARTS` is off by its own constant.

| File | Correction (s) | Peak over off-alignment (dB) |
|---|---|---|
| GL010045 | −20.21 | 6.3 |
| GL020045 | −25.29 | 5.2 |
| GL030045 | −0.38 | 4.6 |
| GL040045 | −6.44 | 5.1 |

Each correction is constant within its file: re-measured in ten 300 s windows, it stays within ±0.1 s. That points to an error in the camera's per-chapter start times, not to logger drift. The chapters are not 3011 s apart in `STARTS` either. The corrections are in `alignment.json`, and `common.file_start()` applies them.

**Check on 03_hand_topspeed.mp4:** the plot shows the audio's harmonics with the aligned logger rpm × 1.5/3/4.5/6 drawn over them. It also shows an rpm curve recovered from the audio with a harmonic comb, compared with the logger. The median error is 36 rpm aligned and 122 rpm with STARTS alone. The audio shows the even-fire V6 ladder: a strong order 3 with orders 1.5, 4.5, 6 and above, where the half orders are the bank-to-bank exhaust pulse.

## Engine (`track_rpm.py`, `build_engine.py`, `preview_engine.png`)

1. `track_rpm.py` produces a per-25 ms audio rpm for the whole race. It uses a comb over orders 1.5…12, searched within ±12 % of the aligned logger rpm and refined parabolically. Alongside it are:
   - harmonic contrast: comb level minus the level half-way between the harmonics, in dB
   - a 20–90 Hz rumble index
   - a 2–8 Hz modulation index of the > 1 kHz envelope, which flags speech or radio
   - the logger throttle and GPS speed

   The results are cached in `cache/track_*.npz`.
2. `build_engine.py` handles each bin and load in four steps:
   - **Candidates.** Runs where the audio rpm stays within ±120 rpm of the bin for ≥ 0.65 s (tier `steady`) and agrees with the logger within 300 rpm. The load test requires both OBD throttle reads around the moment to qualify. If there are none, runs within ±300 rpm for ≥ 0.5 s (tier `sweep`) are used. Candidates are scored on contrast, speech, rumble, rpm steadiness and length.
   - **Processing.** The top 10 candidates are each processed:
     - time-warped onto a constant-rpm phase grid (a cubic fit of the rpm track), so the harmonics stand still and a sweep is flattened
     - spectral gating against the floor between the harmonics, at most −10 dB. This is a per-window "quiet cabin" profile, because wind and road noise change with speed.
     - a 40 Hz high-pass
     - a loop search over start position and length near a whole number of engine cycles (2 revs), maximising the correlation across the seam
     - a 60 ms crossfade whose gains keep the power constant for the measured correlation (sin/cos-like when uncorrelated, linear when identical)
   - **Choice.** The best candidate wins on contrast + 4 × seam correlation, minus a penalty for any repeating > 6 kHz tick in the loop.
   - **Levels.** All on-throttle loops get the same A-weighted level. Each off-throttle loop is set below its on-throttle loop by the measured A-weighted gap, fitted over rpm and clamped to −16…−4 dB. The measured gap is only 3–4.5 dB, probably compressed by the GoPro's gain control, so most bins sit on the −4 dB floor. The player adds its own throttle gain and low-pass on top. One common factor sets the peak to 0.9.
3. Missing bins are pitch-shifted (resampled) from the nearest real bin of the same load and re-looped. `engine.json` marks them with `tier: pitch-shifted` and names the source.

**Coverage:** 20 of 23 bins per load come from real audio at their own rpm. The team short-shifted at about 5000 rpm, so high-rpm material is rare.

- **On throttle:** 1000 and 1250 are pitch-shifted from 1500 (×0.66 and ×0.83), and 6000 from 6250. The 1500, 5750 and 6500 bins are `sweep` tier.
- **Off throttle:** 6000–6500 are pitch-shifted from 5750 (×1.04–1.13). The 5250–5750 bins are `sweep` tier.

`preview_engine.png` puts five bins side by side: the unprocessed footage window and the shipped loop tiled three times, with the seams marked. The order ladder survives and the floor between harmonics drops by about 10 dB.

## Tyre squeal (`build_squeal.py`, `preview_squeal.png`): extracted from the footage

Lateral acceleration is yaw rate about gravity × GPS speed. In the 94 high-g stretches (> 10 m/s², > 12 m/s) that also carry a sustained tone, the script looks for a peak in 900–1700 Hz that is not an engine harmonic. The masked band is ±15 Hz around every order 1.5k.

The same tone, 1110–1180 Hz, shows up again and again at corner exits under power. The FWD car's front tyres scrub as the driver goes to full throttle at about 1.1–1.4 g. The tone stays at that pitch whatever the rpm, so it is not the engine. The longest clean one is GL030045 at 1521.98 s, 1.3 s long, at 1137 Hz with 11.7 dB prominence.

The loop is made by spectral subtraction against the 0.8 s just before the squeal (the same corner, engine and wind, but no squeal), then a 600–5000 Hz band-pass and a 150 ms crossfade loop. In the player, the scrub layer is this loop at rate 0.94–1.10, rising with sliding speed. The lock-up "skid" layer is the same loop at rate 0.60–0.68 through a 1.4 kHz low-pass, plus a 650 Hz band of noise.

## Player verification (`render_player.js`, `recv_render.py`, `preview_player.py`)

There is no Web Audio in Node, so the real `CarAudio` runs in Chrome inside an `OfflineAudioContext`, updated at 60 Hz like the app:

1. `python3 tools/audio/recv_render.py DIR` starts a receiver on 127.0.0.1:8765.
2. Paste `render_player.js` into the dev page's console.
3. Run `preview_player.py DIR`.

Results on the current build, for a full-throttle sweep from 1000 to 6500 rpm in 10 s:

- **Pitch:** the harmonic ladder slides with no steps. The rpm read back from the harmonics is within 22 rpm of the script (median; 65 rpm at the 95th percentile), and the worst stretch is the weak 6000–6500 bins.
- **Clicks:** none. The largest > 6 kHz burst is 2.6 × its running median.
- **Level:** the largest 50 ms step is 2.8 dB, and no frame falls more than 3.1 dB below the median, so there are no gaps.

`preview_scenario.png` shows the other cases: a lift-off reading as a darker, quieter note; the 150 ms gear-change dip; the 16 Hz limiter stutter; the squeal fading in smoothly once slip passes 0.85 of the peak; and the lower lock-up skid.

**Codec seams:** Opus coding error left steps of up to 12 × the normal sample step at some loop seams, and a higher bitrate did not help. The player heals each loop after decoding (`healLoopSeams`): it blends the last 256 samples into the decoded tail-pad copy that runs into loopStart. After that the worst seam is 3.5 × the mean sample step, which is ordinary for these waveforms.

## Rebuild

```sh
cd tools/audio
P="uv run --python 3.12 --with numpy,scipy,soundfile,matplotlib python"
$P align.py         # alignment.json + preview_alignment.png  (~20 s; extracts audio to cache/ on first run)
$P track_rpm.py     # cache/track_*.npz                        (~70 s)
$P build_engine.py  # engine_on/off.ogg, engine.json, preview_engine.png (~15 s)
$P build_squeal.py  # squeal.ogg, squeal.json, preview_squeal.png        (~50 s)
```

Browser support: Ogg Opus decodes in Chrome, Edge and Firefox. If decoding fails, as it may in older Safari, the engine falls back to a plain oscillator and the squeal stays silent.
