# Sonoma kerb rollover (owner drive r2 #10, 20 Oct 2026)

Owner, hot lap at about 0:39: the car rolled onto its side off the track after a kerb. "Either the kerb is too
aggressive or the car is too prone to roll-over". Both play a part. The kerb's profile was the part that was wrong.

## Tools

- `npx tsx tools/physics/kerb_sweep.ts --track sonoma [--raised] [--angles 4,8,12] [--profile h,face,back] [--set car.path=v] [--trace i:off[:deg] --csv f] [--lap]`
  drives the player's Probe (car.json, 1 kHz) over every kerb or sausage strip at the speed profile's line speed. It
  runs on the racing line and 1 m either side (`--angles`: crossing paths over the band instead), and runs the same path
  on the plain road. It logs per-wheel kerb height, load and travel, roll relative to the road and roll rate, wheel lift
  (a wheel with zero load on the strip or within 0.3 s of leaving it, while the plain-road run keeps that wheel down),
  the air gap under a lifted wheel, hull contact and suspension speed.
  Probe module: `src/physics/__tests__/kerbprobe.ts`.
- `npx tsx tools/physics/roll_flat.ts`: fishhook and J-turn on flat tarmac and on adverse banks of 2 to 8 deg.

## Reproduction (package 0da269d, kerb 10 cm, face 0.25 m, back 0.30 m)

- Line sweep, 28 strips x 3 offsets: the car **rolled over at T3a (strip 8, s 760-814) on the line at 33 m/s**, peaking
  at 92.7 deg relative to the road (155 deg/s). The same path on the plain road peaked at 5.5 deg. 22 more traversals
  lifted a wheel. The highest roll angles were T2 exit (10.9 deg) and T9 exit (10.2 deg, 95 deg/s).
- Crossings at 4, 8 and 12 deg: rolled over at the **T2 apex (strip 5) at 4 deg, 35 m/s**, peaking at 94 deg (plain road
  6.1 deg). T7a at 12 deg reached 32.9 deg (plain road 7.1 deg).
- AI solo lap (the autopilot's driver): 2:21.75 with a max roll of 3.8 deg. It never rides the kerbs hard. The owner's
  0:39 (lap 1, from the rolling start) falls in the T3a-T4-T5 section, where these strips are.

## Mechanism (trace of T3a, `--trace 8:0`)

1. **The kick from the kerb.** The car comes back across the kerb from outside at about 18 deg (7 m/s lateral). The
   right wheels climb the 10 cm back slope in about 40 ms. Suspension speed reaches 3.2 m/s, and the linear damper
   (3000 N.s/m) makes about 9 kN at that speed, so the wheel load peaks at 13.6-14.3 kN (3.5 x static). The body takes a
   roll rate of 50-60 deg/s. The right wheels then leave the 10 cm face. A 10 cm drop is more than the 70 mm droop
   travel, so they stay in the air (load 0 from t 5.13 s) while the car turns on its two left wheels.
2. **The tip.** On two wheels the static rollover threshold falls from 1.51 g level (SSF = 1.51/(2 x 0.5)) to 0.98 g at
   12 deg and 0.89 g at 15 deg. The outer tyres still give about 1.0 g at twice their static load (mu0 1.1, load
   sensitivity -0.1, and no loss from camber). The car hangs at -12 to -15 deg for about 0.5 s, then goes over
   (roll rate 140 deg/s).
3. **Not the car alone.** On flat tarmac (`roll_flat.ts`), the fishhook and J-turn at 15-35 m/s reach a max roll of
   3.0-4.1 deg and never run on two wheels. Even on an 8 deg adverse bank the car reaches 11.3 deg with no lift. The kick
   from the kerb is needed.
4. **Not the step sampling.** Widening the face and back by the tyre's footprint, as enveloping would (face 0.5,
   back 0.55), still rolls the car at T3a (92.8 deg). A crossing at an angle stretches the ramp far beyond the
   0.18-0.25 m enveloping length, so point sampling is not what goes wrong here.

## Levers measured (Sonoma line sweep / angle sweep, rollovers caused by the kerb)

| lever | T3a line | T2 x4 | T7a x12 | Laguna |
|---|---|---|---|---|
| package as it was (10 cm / 0.25 / 0.30) | rolls (92.7) | rolls (94) | 32.9 deg | - |
| enveloping-sized ramps (10 cm / 0.5 / 0.55) | rolls | - | - | - |
| digressive damper (knee 0.3 m/s, 35 % above; car.json opt-in) | 12.5 deg | no roll | no roll | changes physics |
| kerb 8 cm / 0.25 / 0.6 | no roll | no roll | 40.8 deg | unchanged |
| **kerb 5 cm / 0.25 / 0.6 (adopted)** | 7.8 deg | no roll | no roll | unchanged |

## Fix: the config profile, 5 cm, face 0.25 m, back 0.6 m

The evidence points to a lower kerb than 10 cm:

- The July 2011 Street View notes read "low flat concrete" (streetview.md).
- The owner's T7 panorama (owner_8) shows the island dirt level with the kerb top, with no drop behind it, and a low
  lip on the track side.
- A 5 cm lip at 30-45 deg, enveloped by the 0.316 m tyre (sqrt(2 r h) = 0.18 m), is felt as a ramp of about 0.25 m.
- The earlier "10-15 cm" was most likely the sloped face's width.

The 0.6 m back stands in for the backfilled dirt behind the kerb, which the surface model cannot raise.

Stage 3 was rebuilt with `build_track.py --track sonoma --stage scenery`. Every scenery gate passed. Only
`kerbs.profile` changed in scenery.json, and the registry rev is now f050c52be8.

After the fix: line sweep max roll 7.5 deg, no rollover. In the angle sweep (outside the gate), three crossings still
pass 15 deg. Each runs off into terrain where the same path on the plain road already passes 13 deg:

- T8a at 12 deg: 20.3 deg (plain road 13.7).
- 9a at 8 deg: 27.5 deg (plain road 26.4).
- 9a at 12 deg, 40 m/s: 60.2 deg, rolled (plain road 20.7). Off-track terrain plus the kerb: a candidate for the
  damper or droop work below.

AI solo lap unchanged at 2:21.75.

## Kerb traversal gate (`src/physics/__tests__/kerbgate.test.ts`)

The gate covers every raised strip on every registered track (kerbs that have a profile, plus sausages), at line speed,
on the line and 1 m either side.

- **No roll past 15 deg and no rollover.** Passes on Laguna (30 sausage passes) and on Sonoma (84). It fails on the old
  Sonoma package (T3a, 92.7 deg).
- **No wheel lifted by a strip.**
  - Laguna passes. Its sausages sit 1.4 m beyond the edge, and no line +-1 m pass touches them.
  - **Sonoma fails, 16 of 84.** The 5 cm kerb still hops the light wheel for 14-397 ms, with air gaps up to 10.6 cm
    (T3a, T9 exit, T9a). A 3 cm kerb still lifts a wheel in 13 passes.
  - The cause is the car's suspension, not the kerb. Droop travel is 70 mm and rebound damping is linear: a lightly
    loaded inner rear (about 800 N of spring force against 3750 N.s/m) extends at only about 0.2 m/s. The plain Sonoma
    road also lifts wheels in this sweep, by up to 0.9 s per pass.
  - This half of the gate is `it.fails` for Sonoma. It is the owner's call whether to change droop or rebound (a car
    physics change: PHYSICS_VERSION and boards) or to accept short hops on raised kerbs.

## Laguna (unchanged)

- The digressive damper code is inert at its defaults: the on-pavement bit-identity fixture passes.
- Autopilot calibration lap: 2:03.84 before and after.
- AI solo lap: 2:00.20.
- Self-play seed 1: contacts 2 = 0.012 per car-lap, four-off 17, the same as today.
- No PHYSICS_VERSION bump is needed.

Sonoma self-play seed 1 gives the same numbers before and after (contacts 10 = 0.062 per car-lap, four-off 9,
recoveries 7). The field's surfaces have no kerbs (selfplay.ts `makeSurface`), so the profile does not reach the AI
cars. The contacts above the 0.02 target were there before this change.
