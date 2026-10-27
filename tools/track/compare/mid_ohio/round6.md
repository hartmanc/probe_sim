# Mid-Ohio round 6: the hood sheet (SKILL 1.10), T8 from evidence, the T4-entry margin

Opus 5.5, 26 Oct 2026, branch `mid-ohio` (from 7b9c532).

Scope:
- the driver's-eye hood sheet the skill requires before stage 2 is accepted;
- the T8 finding of round 5, settled from evidence;
- a proposal for the T4-entry wheel-off.

Nothing in the package, the line, the edges or the config changed. `public/tracks/mid_ohio/` and the `mid_ohio` registry
entry stay local and uncommitted; `cmp` shows the package's track.json and ghosts.json identical to
`tools/track/out/mid_ohio_r5`. Not in this round: scenery, far terrain, the registry commit, the field, AI tuning,
previews.

Machine health before each batch: battery 99-100 % on charge; 1-minute load 1.8-6.7, under 8 at every start; 11 GB
free. Heavy processes ran one at a time: the hood capture, the drive proxy, then the three reference drives.

## 1. The hood sheet (SKILL 1.10)

`tools/track/compare/mid_ohio/hood_r6/`. The 44 PNGs, the stills under `sim/` and the composites are local; `index.html`,
`README.md`, `frames.json` and `walk_plan*.json` are tracked. `index.html` is the page to publish: open it from the
directory, since its images are relative.

The sheets:
- `sheet_00_overview.png`: every station over the package ortho.
- 43 station sheets: each corner's entry, apex and exit (T1-T13, Keyhole, Madness, Thunder Valley, Carousel), and the
  midpoints of the four longest straights (T13-T1 pit straight, T1-T2, T2-T3, T3-T4 back straight).
- Order: T8 first (sheets 01-03), then T4 (04-06), then the lap in driving order from S/F (07-43).

Each sheet has three panels, at the same station:
- the sim's hood camera on the centre;
- the N837 hood frame (Apr 2026, every 1 s);
- the 2025 360 lap's ahead view (every 0.5 s).

The T8 and T4 sheets add a fourth still on the solver's line. Each sheet carries a caption saying what to judge:
edges, width, kerb starts and ends, crest or dip, and the T4 bank.

The page adds three evidence images:
- `t8_overlay.png`: the lines over the capture.
- `t8_crest.png`: the view from 60 m before the crest.
- `t8_walk.png`: the solver's line every 20 m from s 2380 to 2580.

It also adds `t4_entry_walk.png`: the line at s 1830-1890 beside the 360 lap.

How they were made:
- Stations: `r6/stations.py`. The apex is the package corner. Entry and exit are where the centre's curvature falls
  below half its peak, clamped to 20-80 m from the apex.
- Poses: `r6/plan.py`.
- Stills: `camera_walk.ts --replay`, which uses its own headless Chrome with a throwaway muted profile, and the dev
  server from this worktree on port 5183.
- Sheets: `r6/make_sheets.py` with `r6/captions.json`.
- Page: `r6/make_index.py`.

Time-map confidence:
- N837: largest leave-one-out residual 14.8 m.
- 360 lap: 20.4 m.
- Both are "direct", so every sheet has a 360 frame. The per-sheet sigma (4-20 m) is in README.md.
- Frame spacing adds up to about 15 m. N837 shows the T3 entry and apex in one frame (t052).
- N837 t062-t065 (T4) carry a YouTube player overlay, so the T4 apex is judged from the 360 still.

What the sheets show at a glance, for the orchestrator's review:
- The road shapes agree with both videos at every corner I looked at: the Keyhole arc, the T7 climb to the T8 brow, the
  drop into Thunder Valley, the Carousel.
- The visible differences are scenery, which stage 3 has not built: walls, stands, trees, boards and the bridges.
- The kerbs the app draws do not match the real red/white and yellow kerbs. That is also stage 3.
- One aside for the T4 placement: a transverse pavement joint shows on the capture at s ~1884 at the T4 entry. That is
  5 m from the rule's assumed core start (s 1889). It may be the 2024 repave boundary. It was not used.

## 2. T8: verdict (c). The edges are right, the crest is real, and the line and the AI profile are fine

The round-5 finding was:
- the solver's line opens T8 to R 88 m against R 52 m on the centre;
- N837 lap 149 brakes from 113 to 85 km/h just after a crest;
- the profile/N837 ratio is +18.5 % relative to the median.

The three explanations, against the evidence:

| question | evidence | finding |
|---|---|---|
| (a) edges too wide: a paved run-off or apron inside the edges | **Owner's review.** Round 2 accepted T8: the export marks 13 windows, none at T8 (w_s2375 / w_s2500 / w_s2625 unmarked: "the fits were good"); no green strokes there.<br>**Capture.** On `edges_r2/w_s2500` and `w_s2625`, both edges sit on the asphalt, with grass beyond them (sand trap only outside T9). The red/white apex kerb is outside the right edge (the inner-kerb convention).<br>**Width.** 12.0-12.3 m, rising to 13.4 m at s 2510-2530, where the capture shows the road widening at the kerb.<br>**Heightfield** 2-12 m beyond the edges (`r6/t8_profile.json`, cross sections): left falls 0.1-0.2 m at 2 m and 0.3-0.5 m at 4 m; right rises 0.1-0.2 m at 2 m. No level shelf on either side. | **No.** The T8 window for the drawing page is not needed and was not made. |
| (b) the crest makes T8 blind, so the real line brakes for visibility and the drop | **Profile** (`r6/t8_profile.json`). Crest at s 2454: the highest point, +7.0 % at s 2410 to -6.4 % at s 2490, strongest convexity R ~324 m at s 2456.<br>**Sight line** from the hood (eye 1.1 m) at s 2394, 60 m before the crest: road surface visible only to s 2431 (37 m), a 0.3 m kerb to s 2455. The T8 apex (s 2521) comes into view only within ~20 m of the crest.<br>**Real cars' positions** (`r6/t8_observed.json`, on `t8_overlay.png`): all three (N837, the 360 pace car, the IndyCar) are at the **left edge over the crest**, the yellow kerb at s 2451-2466 alongside. They apex on the right kerb at s 2510-2540 and exit onto the yellow left kerb at s 2565-2610.<br>**Solver's line** at s 2440-2490: +2.3 to -2.3 m, 2-4.5 m right of them. It crosses diagonally from the T7 apex. A smooth line through the real positions has its tightest radius R 77 m (at s 2566) against the solver's R 88 m. | The crest is real and blind, and the real cars' line differs in shape over it. But they do not brake for the crest itself: N837 lap 149 loses only 0.05 s to its best over t084-t087 (s 2392-2481). |
| (c) the line is fine and the AI's speed profile handles it | **Race AI's own profile** (`r6/ai_profile_t8.json`: field.ts buildSpeedProfile with the crest load factor; Probe, full pace). 102-104 km/h over the crest (load factor 0.71-0.77 at s 2450-2460), 113 km/h at the T8 apex, 120 km/h at s 2590, 80 km/h at T9. Without the crest term, 107 km/h at the apex: the sag after the crest adds load. The drive.ts target profile is within 0.5 km/h of the AI's through T8.<br>**N837 session best** (`r6/t8_delta.py`): the Catalyst DELTA readout every 1 s, frames t084-t097, against lap 149's speed-integrated positions (1.6 m off at the T9 anchor). Table below. | **Yes.** The session best of the same car runs T8 and T9 at the AI profile's speed (+3 % and +1 %, inside the +4 % that car carries at the end of every long straight). Lap 149's 85 km/h is that lap's loss: 0.72 s in 4 s, the fastest of the lap. |

N837 session best against the race AI's profile, section averages:

| section | s | lap 149 | session best (from the delta) | AI profile | best / AI |
|---|---|---|---|---|---|
| crest (T7 exit to the brow) | 2392-2481 | 3.00 s, 106.8 km/h | 2.95 s, 108.6 km/h | 101.7 km/h | 1.07 |
| T8 | 2481-2589 | 4.00 s, 96.8 km/h | 3.28 s, 118.0 km/h | 115.0 km/h | 1.03 |
| T9 | 2589-2673 | 4.00 s, 75.6 km/h | 3.23 s, 93.6 km/h | 92.8 km/h | 1.01 |

Caveats:
- These are section averages from a 0.01 s readout every 1 s: about ±3 % on a 3 s section.
- The session best is the same Lemons car on the same day, not a Probe.
- In t088 another car is in view far ahead, and in t087 two marshals stand at the station right of the crest. Whether
  either slowed lap 149 the frames cannot say.

**Verdict: (c).** The edges at T8 are right (owner-accepted, on the asphalt). The crest is real and blind, but neither
the real cars nor the profile slow for it. The solver's line and the race AI's speed profile (crest term included)
predict the pace that the N837 car's own best lap shows through T8 and T9. The round-5 +18 % came from comparing with
lap 149, which loses its most time of the lap exactly there.

No line or edge change follows.

What remains is a shape difference, for the owner if he wants it: the real cars hold the left edge over the brow,
while the line runs 2-4.5 m right of them there.
- The rule the skill allows for it is a `ghosts.margin_zones` entry with its evidence, as Sonoma's 9a chicane has. Here
  it would be on the right side, about s 2430-2490, at a margin of about 10.5 m from the right edge, which leaves the
  line within about 1.5 m of the left edge.
- This is a per-stretch line constraint from the three videos above.
- It would tighten T8 toward R ~77 m and cost the AI about 6 % of apex speed (R 77 against R 88).
- I do not recommend it now. The speed evidence says the present line is right for pace, and the difference shows only
  as the AI's lateral position over a blind brow.

## 3. T4 entry: the wheel-off at the 1.0 m margin, and a proposal (not applied)

Trace: `r6/t4_entry.py` -> `r6/t4_entry.json`. It reads drive.ts `sim_lap.csv` from
`npx tsx tools/calibrate/drive.ts --track tools/track/out/mid_ohio_r5 --alat 1.2 --learn 25 --bank --out tools/track/out/mid_ohio_r6_drive`.
That run reproduces round 5 exactly: 1:59.25, max lateral error 0.94 m, 290 off-track steps. Wheel clearance is
computed as the line clearance minus the outward error minus half the Probe's track (0.757 m).

| s | v (km/h) | decel (g) | lat. (g) | line's left clearance (m) | lateral error, + outward (m) | left wheel centre to edge (m) | on track |
|---|---|---|---|---|---|---|---|
| 1825 | 167 | 0.18 | -0.10 | 1.64 | +0.04 | 0.84 | yes |
| 1845 | 156 | 0.83 | -0.19 | 1.13 | +0.13 | 0.24 | yes |
| 1855 | 149 | 0.86 | -0.26 | 1.02 | +0.19 | 0.07 | yes |
| 1861-1871 | 145-138 | 0.85-0.88 | -0.30 | 1.01-1.10 | +0.23-0.29 | 0.02-0.06 | **no** (6 grid rows, 290 steps, 0.29 s) |
| 1881 | 130 | 0.80 | -0.47 | 1.39 | +0.39 | 0.25 | yes |
| 1925 | 98 | 0.55 | -0.77 | 7.00 | +0.78 | 5.47 | yes |

Why it happens:
- The line reaches its 1.0 m left margin at s 1855-1871. That is under full braking (0.85-0.88 g), with the turn-in
  already started (-0.3 g lateral).
- The road there falls ~0.8 % toward the left: the profile's left edge is 9-10 cm below the right at s 1800-1840.
- The autopilot lags outward. Its error grows steadily (0.04 m at s 1825, 0.29 m at s 1871, 0.78 m at s 1925).
- Beyond the left edge is grass, then a wall. The capture shows no paved shoulder, so this is a true wheel off.

How the other packages fare: Sonoma, Buttonwillow and Laguna were driven with the same command (`tools/track/out/r6_drive_*`).

| package | autopilot lap | wheel-off steps | min wheel centre to edge | braking rows with the line at the margin | max outward error there |
|---|---|---|---|---|---|
| Mid-Ohio (round 5) | 1:59.25 | 290 | 0.02 m (s 1863) | 11 (T2, T4 entry) | 0.26 m |
| Sonoma (published) | 2:24.14 | 0 | 0.15 m | 19 (5 zones) | 0.12 m |
| Buttonwillow (published) | 2:31.88 | 0 | 0.14 m | 7 (3 zones) | 0.11 m |
| Laguna (published) | 2:01.73 | 0 | 0.07 m | 8 (2 zones) | 0.13 m |

All four use the same global 1.0 m margin; Laguna adds `kerb_margin` 1.0 and `nudge`. Only Sonoma has a local zone:
`margin_zones` right 1.5 m at the 9a chicane, from its onboard (round 14B). The other three tracks do brake at the
margin. Mid-Ohio's T4 entry is the one place where the drift reaches the wheel. It is the hardest combination on the
four tracks: 167 km/h, the end of the longest straight, a road falling to the outside, and the turn-in under full
braking.

Real cars at the T4 braking zone:
- 360 lap h0144-h0147 (s ~1820-1880, the 200 and 100 boards on the left): the car brakes with the left line about
  1-1.5 m from its centre.
- IndyCar t044.5-t045: about 1 m.
- N837 t060 and t062: about 1.5 m, with cones on the grass.

Options:

| | A: local margin zone, left 1.3 m, s ~1825-1890 | B: lap-wide margin 1.2 m | C: leave the line; the AI stage fixes the autopilot's braking drift | D: accept as is |
|---|---|---|---|---|
| mechanism | `ghosts.margin_zones` (build_ghosts.line_bounds, the Sonoma 9a key; needs `src`), eased in and out over 10 m | `ghosts.margin` 1.0 -> 1.2 | drive.ts / AI controller (out of track scope) | none |
| evidence | 360 lap, IndyCar and N837 braking frames: about 1-1.5 m from the left line | none for the whole lap | | |
| expected wheel clearance at T4 entry | about 0.25 m with the same 0.29 m drift (0.54 m with none): Sonoma / Buttonwillow's 0.14-0.15 m or better | about 0.15 m with the same drift | 0.02 m -> depends on the AI work | 0.02 m, 0.29 s off |
| effect on the rest of the line | none outside s ~1815-1900; the T4 entry line moves at most ~0.3 m right | every corner 0.2 m narrower; slower everywhere | none | none |
| lap time (solver) | negligible (straight-line braking zone) | a few tenths | none | none |
| precedent | Sonoma round 14B (accepted) | none | | |
| rebuild | stage 2 only (ghosts.json; geometry identical) + line_check 1.3 m in the zone + drive proxy | stage 2 + everything downstream | none | none |
| verdict | **proposed** | over-broad | the AI stage may still want it | leaves the only wheel-off on four tracks |

The proposed config entry is NOT applied. The lat/lon are on the package centre at s 1825 and 1890:

```python
ghosts=dict(margin_zones=[dict(side='left', a=(40.691305, -82.6388667), b=(40.6918495, -82.638587), margin=1.3,
    src='T4 entry braking: 2025 360 lap h0144-h0147 (200/100 boards), IndyCar 9Drr1VkE1_U t044.5-t045, N837 t060/t062: '
        'cars brake ~1-1.5 m from the left line; autopilot drift 0.29 m at the 1.0 m margin (round6.md 3)')]),
```

After applying it:
- rebuild stage 2 into a new out dir;
- run `r5/line_check.py` (it should report 1.3 m in the zone);
- run the drive proxy, expecting 0 off-track steps;
- re-run the T4 sheets on the line.

## 4. The AI's "T8 Corkscrew" (record only)

`src/physics/ai/line.ts:188` names any corner `T8` (or `T8A`) "T8 Corkscrew". `src/physics/ai/driver.ts:203` finds the
Corkscrew by that name and applies Laguna's no-passing zone: from 120 m before its braking point to 90 m past the apex.
**Mid-Ohio's T8 inherits Laguna's Corkscrew no-passing zone until the AI round fixes the hard-coded name.** The code is
left as is; the orchestrator files the issue.

This round's AI profile output names it so (`r6/ai_profile_t8.json`: "T8 Corkscrew", passable false, braking point
s 2505.7, apex s 2523.7). So the zone covers s ~2386-2614: T7 exit, the crest, T8, and up to T9's braking.

## 5. Stage ledger (round 6)

| step | record |
|---|---|
| 0.x inventory | unchanged; the time maps are used for the sheet frames |
| 1.x geometry | unchanged |
| 1.10 driver's-eye sheet | **made** (section 1). For the orchestrator's review and the owner's page before stage 2 is accepted |
| 1.11 derived data | unchanged |
| 2.2 racing line | unchanged. T8 settled as (c), no change (section 2). T4 entry: margin zone proposed, not applied (section 3) |
| drive proxy | re-run, identical to round 5. The other three packages give the reference numbers |
| stage 2 acceptance | waits on the orchestrator's review of the sheet and the owner's call on section 3 (and, if he wants it, the crest shape in section 2) |

## 6. Left open for scenery and later stages

- Section 3: the T4-entry margin zone, for the owner's decision. Section 2: the optional crest shape.
- The kerbs: the real red/white and yellow kerbs at every corner, with their starts and ends from the sheets. The app
  draws its own strips at the race edges for now. Stage 3 places them from evidence.
- Everything round 5 left open still stands:
  - the green strokes as paved boundaries;
  - the 'corroborate' IndyCar B / C rows;
  - the pit wall height (0.7 m against 1.04 m);
  - the armco heights;
  - the footbridge deck (4.4 m);
  - the grandstand extents;
  - the pit lane;
  - the T4 run-off raise;
  - the Mid-Ohio field and pace;
  - the registry entry and package publication;
  - the AI knobs.
- The transverse joint at s ~1884 (section 1) may be the 2024 T4 repave start. It could corroborate the `profile_bank`
  placement. It has not been measured.
- The AI: the Corkscrew name (section 4). Also the autopilot's outward drift under braking into a turn-in (section 3,
  option C).

## 7. Commits (branch `mid-ohio`)

- abba1ef: the hood sheet (step 1).
- 2c6a288: T8 evidence and verdict (step 2).
- f5b2f6c: the T4-entry analysis and the sheet page (step 3).
- This ledger (steps 4-5).
