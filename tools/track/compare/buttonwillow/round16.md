# Buttonwillow round 16: ledger (26 Oct 2026, evening)

Branch `buttonwillow-r16` (from `buttonwillow-r15` ef1445b), worktree `probe_sim-wt/buttonwillow-r14`. Nothing pushed, deployed or merged.
Package `public/tracks/buttonwillow`: rev **d65c062829 -> f2cc14f2ee**, scenery.json only (track.json, heightfield, ghosts identical; lap 4705.982 m).
The owner's drive of round 15: "Buttonwillow is fantastic. My only complaints: there is a small kerb on the inside of the left hand kink after Phil Hill that is missing in the sim; the outside kerb at Star Mazda. In my memory, it is taller. With those two changes, it is ready for prod."

## The two readings (and the ambiguities as put to the coordinator)

**Phil Hill.** OSM has no such name. The official Race #1 CCW map (frame of the ccw_7Qw video) puts Phil Hill on the bulge east of the Drag Strip's north end: the sim's T8 (OSM "Lost Hill", apex right at s ~2770), with the Drag Strip after it. Clockwise, the left-hand kinks after it are at s 2835-2880 (21 deg) and 2983-3035 (16 deg).
Ambiguity: "the left-hand kink after Phil Hill" could be either. The second already has a kerb strip (left 3005-3013), so the missing one is the first; that is the reading taken.

**Star Mazda outside kerb.** T9 is a right-hander, so the outside is the left. Ambiguity: two left runs, the entry (left 3341-3384, 6 cm default) and the exit (left 3470-3518, flat in round 15). The owner's round-2 note on it ("the exit kerb is a raised, aggressive kerb") and "taller" than flat both point at the exit run, so only the exit run changed; the entry run keeps its 6 cm default.

## Kerb 1: added

Left, package s 2846-2865 (round-14 metres 2841.7-2860.6 in the config; the builder remaps), band 0 .. 0.9 m beyond the race edge (`kerb.inside=False`), flat painted white blocks (white `#e2dfd6` over `#8f8c86`), width 0.9 m (the track standard; t096's blocks span the T8 apex's 0.86 m).
Evidence: onboard t096 (1:36, 66 mph): 8-10 white blocks of ~1 m at the left edge, flush with the asphalt, no face band (as t094); capwin window at s 2860 (0.1 m/px, 10 m ticks): white blocks from just before the 2850 tick to between the 2860 and 2870 ticks. Round 11 dropped "run left s 2849-2855" reading t096 as paint with no kerb; the owner's report corrects that. Inventory: the t096 paint row is now a kerb row (`inventory.json`, `observations.jsonl`). The race edge did not move.

## Kerb 2: taller

Left 3474-3521 (config `run left s 3470-3518`): flat -> 6 cm / 0.15 m face / 0.30 m back. Frames cannot measure it: t116, the closest frame, shows a flush edge with a face of 1-2 px (<= 0.02 m), so the measured-profile method gives flat, against the owner's memory. His memory is taken as the evidence of the real kerb and the run takes the next taller profile the family has, the measured T9 apex 6 cm (t114); not 10 cm, because round 8's 10 cm lifted a wheel in the traversal gate on this run (215-562 ms). Dated note (26 Oct 2026) in the config.

## Gates and proofs

- Rebuild `build_track.py --track buttonwillow --stage all --publish --overwrite-package`: exit 0, no [FAIL]; kerbs 40 (was 39).
- `run_gates.ts` (with the build's gates_config.json) rc 0, `run_coverage.ts` rc 0 (89 rows, MISSING 0, UNSUPPORTED 0), `manifest_tables.ts` rc 0. Containment 0 escapes; cones 95 / 36; paved coverage 0 unpaved; ground marks ok (edge-line vertices 15100 against 15148 in round 15; the paint count 3352 is the same).
- `red_adherence.py`: identical to round 15 (left all 0.019 / 0.069, right all 0.019 / 0.064 median / p90; worst 0.348 m at left s 1306). Lap length 4705.982 m (unchanged).
- Identity: `git diff ef1445b -- public/tracks/{sonoma,laguna_seca,mid_ohio}` empty; `soup_hash.ts sonoma laguna_seca` f71411f3c2e78626 / e3b0c44298fc1c14 (buttonwillow 3da76e09e950dd5a).
- `npx vitest run` 66 files, 549 passed; `npm run build` ok; pytest `tools/track` 136 passed, 3 skipped. TRACKS.buttonwillow rev f2cc14f2ee (`wip: true` untouched).

## Crest case (kerb gate, kerbgate.test.ts)

Buttonwillow 34 crest passes (round 15: 33), **worst roll 11.4 deg** (left 523-551 at 88 km/h, unchanged; next 11.3). The taller exit run: crest 2 m onto left 3474-3521 at 85 km/h, max roll 5.6 deg, lifted 0 ms. The new flat kerb adds line passes, not crest cases (flat): 120 line passes (117), worst 6.9 deg on the exit run; the exit run lifts the car 275-326 ms on the line passes, air gap up to 5.9 cm (advisory lift report, as for the other 6 cm runs).

## Self-play (`selfplay.ts --track buttonwillow --laps 2 --seed 1 --max-ai 100`, 100 cars)

Contacts (>1 m/s AI-AI) 3 = 0.018 per car-lap, of which 2 above 3 m/s; four-off 4 (2 from mishaps); mishaps 2 (T5); line when alone rms 0.28 m. Round 15 (seed 1): contacts 4 (2 mishaps), four-off 4 (2). No bound this round; the owner decides card 24 separately.

## Stills

`compare_sheets_r16/` (index.md): the driver's eye at each kerb with the onboard frame beside it (local; images are not committed).
