# AI readiness: contacts by place, per-track knobs (24 Oct 2026, branch `integration`)

Target: AI-AI contacts (> 1 m/s closing, per pair per 1 s, green flag) <= 0.02 per car-lap, four wheels off down, race
time within 2 % of the untuned race on the same seeds, Laguna's races bit-identical. Standard self-play: 4 laps, the
whole field (player's car AI-driven), shuffled grid, the track's `TRACKS[id].ai` knobs.

Packages: Laguna Seca as merged; Sonoma round 14A (rev e4e8928b59, 134 cars, AI_VERSION 8 calibration 3ba7d82);
Buttonwillow round 10 (rev 7acf260f50, 100 cars, calibration cb9c5aa).

Tools (all deterministic: a rerun of the same seed reproduces every contact, four-off and the finishing order):
- `selfplay.ts --json` writes the race's events (`rules.contactAt` with ds / dl between the cars, `fourOffAt`,
  `recoveryAt`), the race pace (`pace`: median best lap / drawn target) and the finishing order (`order`).
- `selfplay_kinds.ts`: station histogram of contacts and four-offs (50 m bins), the contact kind from the cars' lane-frame
  offsets (rear-end |dl| < 1 m; side-by-side |ds| < 3 m; else quarter), the place (brake / entry / exit / straight,
  as `selfplay_where.ts`) and the track features in the bin (kerbs, cone lines, blends, wall ends), plus marshal resets.
- `selfplay_table.ts`: the trial table from `tools/race/out/<prefix>_<tag>_s<seed>.json`.
- `wall_phantoms.ts`: wall segments whose contact band reaches the road (see Sonoma T7 below).

Outputs go to `tools/race/out/` (git-ignored).

## 1. Where the contacts happen (seed 1, knobs as found)

| track | cars | car-laps | contacts / car-lap | four-off / car-lap | marshal resets | race time |
|---|---|---|---|---|---|---|
| laguna_seca | 45 | 169 | 0.012 (2) | 0.100 (17) | 2 | 620 s |
| sonoma (fs 1.4, lm 0.85, sg 1) | 134 | 445 | 0.076 (34) | 0.018 (8) | 210 | 688 s |
| buttonwillow (no knobs) | 100 | 353 | 0.068 (24) | 0.190 (67) | 23 | 743 s |

### Sonoma (seed 1)

Contact kinds: 12 quarter on braking, 6 side-by-side on braking, 5 rear-end on braking, 4 quarter in a corner, 3 quarter on
a straight, 2 rear-end in a corner, 1 rear-end on a straight, 1 side-by-side in a corner. Context: 15 line, 14 pass,
5 passing-other.

| station (m) | place | contacts | contact kinds | four-offs | four-off context | features |
|---|---|---|---|---|---|---|
| 2050-2100 | T7 brake | 21 | 11 quarter on braking, 6 side-by-side on braking, 4 rear-end on braking | 1 | traffic grip | tyre run #9 0.5 m off the left edge (wall_phantoms: phantom band on the racing line) |
| 3000-3050 | T9a entry / brake | 3 | 1 quarter in a corner, 1 rear-end on braking, 1 quarter on braking | 0 | - | kerb R |
| 1950-2000 | straight (T7 approach) | 2 | 1 rear-end, 1 quarter on a straight | 0 | - | drag-strip blend |
| 350-400 | T2 entry | 2 | 2 rear-end in a corner | 0 | - | kerb L, kerb R |
| 2450-2500 | T8a exit | 1 | 1 quarter in a corner | 1 | traffic rejoin | kerb R |
| 1050-1100 | T4 exit | 1 | 1 side-by-side in a corner | 1 | traffic rejoin | kerb L |
| 3600-3650 | T11 entry | 1 | 1 quarter in a corner | 0 | - | kerb R, wall ends |
| 200-250 | straight (pit exit) | 1 | 1 quarter on a straight | 0 | - | pit-exit cones, pit lane end |

Marshal resets 210: 97 at T7 brake (s 2050-2100), 21 on its approach (2000-2050), 32 at T2 entry (350-400: a lap-1/2
queue up the hill, cars crawling < 2 m/s for 4 s are reset; 2 contacts there).
Seeds 1 + 2 pooled (880 car-laps): 70 contacts, 39 of them at T7 brake; T9a 5, T2 5, T11 entry 6.

### Buttonwillow (seed 1, no knobs)

Contact kinds: 6 quarter on a straight, 6 side-by-side on a straight, 3 side-by-side in a corner, 3 quarter in a corner,
3 rear-end on a straight, 3 rear-end in a corner. Context: 18 pass, 4 line, 1 off, 1 passing-other. Four-offs: 31
traffic rejoin, 25 traffic grip, 8 alone rejoin.

| station (m) | place | contacts | contact kinds | four-offs | four-off context | features |
|---|---|---|---|---|---|---|
| 4050-4100 | straight | 4 | 2 quarter, 1 rear-end, 1 side-by-side on a straight | 3 | 2 traffic rejoin, 1 grip | kerb R, cone lines off the edge |
| 2550-2600 | straight | 3 | 3 side-by-side on a straight | 4 | 3 traffic grip, 1 rejoin | cone line on the road 0.2 m (visual only, not in physics); drag-strip blend |
| 550-600 | T2 entry / exit | 2 | 1 quarter, 1 rear-end in a corner | 4 | 2 rejoin, 2 grip | kerbs, T2 runoff blends |
| 1200-1250 | T4 exit | 1 | 1 rear-end in a corner | 5 | 3 alone rejoin, 2 traffic rejoin | kerb L |
| 3900-3950 | T10 exit | 3 | side-by-side, quarter, rear-end | 0 | - | kerb R |
| 1000-1050 | T3 exit | 2 | 2 quarter in a corner | 1 | traffic grip | kerbs |
| 3950-4000 | straight | 2 | rear-end, side-by-side on a straight | 1 | traffic grip | kerb L |
| 3800-3850 | T10 exit | 0 | - | 5 | 4 traffic grip, 1 alone grip | kerbs |

Marshal resets 23: 7 at T4 exit (1200-1250), 4 at the T8 exit.

### Laguna Seca (seed 1, the clean reference)

2 contacts (1 side-by-side in a corner at T11 exit s 3250-3300, 1 quarter on braking at T5 s 1450-1500), both passes.
Four-offs 17: T11 exit 3 (traffic rejoin), T2 exit 3 (rejoin), T4 4, scattered singles. Marshal resets 2 (T4 exit).

### What the worst places have in common, and how they differ from Laguna

- **Sonoma T7 brake (s 2050-2100) is not a racecraft place.** The racing line runs at +4.6 m with the left edge at
  5.65 m; tyre run #9 (scenery barrier, drawn 0.7 m off the edge, inner face 0.5 m off it) turns away from the road at
  both ends (s 2069 and 2081). `vehicle.ts collide()` tests hull points against each segment's infinite line within the
  segment's span and treats a point on the far side from the CG as through the wall (up to 2.9 m deep). At the oblique
  end segments that band reaches back over the road edge onto the racing line: #56 (seed 1, formation, on the line,
  e -0.03) is stopped dead from 8.7 m/s at s 2081 by segment 718 with a 1.39 m deep contact it never touched
  (local diagnosis scripts `tools/race/out/hit.ts`, `hitseg.ts`); #100 (green, 31 m/s on the line) is launched by the same contact (30.9 m/s tyre impact,
  above the launch speed) and leaves the planet. The queue behind each stopped car makes the contacts (rear-ends and
  quarters on braking, closing 5-17 m/s) and the resets. `wall_phantoms.ts`: Sonoma has exactly these two segments
  (712 at s 2068-2069, 718 at s 2081) whose band covers the racing line +- 1 m; Laguna and Buttonwillow have none.
  Diagnosis (barrier #9 points s 2069-2081 removed in memory, `out/diag_selfplay.ts`): contacts 0.076 -> 0.017 (seed 1),
  0.083 -> 0.035 (seed 2), pooled 0.080 -> 0.026; resets 210 -> 71 and 172 -> 100.
- **The racecraft places** (Sonoma T9a, T11 and T4 entries; Buttonwillow T3 entry, T11 entry, T10 exit) share Laguna's
  old Sonoma pattern: a pass lane on the inside at turn-in where the road takes the lane away at the apex (the line runs
  edge to edge), the passer runs 1-2 m wide into the car making room: quarter / side-by-side contacts in a corner,
  closing 1-4 m/s. Laguna's clean places are wider relative to the line or covered by its no-pass Corkscrew.
- **Buttonwillow's four-offs** are rejoin and grip events in traffic on corner exits (T4, T9, T10) and the long
  straights where a car pushed off by a lane change rejoins: what `shiftGrip` caps on Sonoma. Kerbs are in every bin
  but are not the cause (no sausage or launch at any of them; the cone lines are visual only).
- **Sonoma T9a** (owner's right-hander at s ~3043; the coordinator's kerb-probe note of 24 Oct: line speed 23.8 m/s vs
  14.7 m/s for the -1 m path on 14A): 5 of 70 pooled contacts (0.006 per car-lap), all rear-end / quarter on braking or
  entry at s 2990-3032, before the apex; **no four-off there at the kept knobs** (1-2 per two seeds only in the fs 1.0,
  fs 1.8 and sg 1.5 trials, s 3062-3106). The contacts are braking-zone traffic, which followScale / laneMargin reach
  (lm 0.7: 0 and 3 there). No evidence on 14A that a per-track corner-speed reserve is needed; check the round-14B rerun
  (tighter T9a / 9a radii) for four-offs at s 3040-3110 before deciding.

## 2. Knob trials (seeds 1 and 2, one change at a time; seed 3 for the kept Buttonwillow setting)

### Buttonwillow (from no knobs)

| trial | knobs (followScale / laneMargin / shiftGrip) | seeds | contacts / car-lap | four-off / car-lap | recoveries | race time (s) | median best lap / target | clearly-faster passes |
|---|---|---|---|---|---|---|---|---|
| base | 1 / 1 / 0 | 1, 2, 3 | **0.058** (0.068 / 0.062 / 0.043) | **0.185** (0.190 / 0.174 / 0.194) | 23 / 25 / 17 | 743 / 813 / 758 | 1.127 / 1.159 / 1.196 | 59.9 % |
| sg1 | 1 / 1 / 1 | 1, 2 | **0.061** (0.063 / 0.058) | **0.057** (0.066 / 0.047) | 19 / 14 | 758 / 778 | 1.168 / 1.231 | 61.0 % |
| lm85 | 1 / 0.85 / 0 | 1, 2 | **0.047** (0.042 / 0.052) | **0.167** (0.188 / 0.146) | 19 / 14 | 747 / 774 | 1.133 / 1.258 | 56.6 % |
| fs14 | 1.4 / 1 / 0 | 1, 2 | **0.056** (0.053 / 0.058) | **0.127** (0.137 / 0.116) | 16 / 15 | 753 / 788 | 1.177 / 1.307 | 60.8 % |
| sg1lm85 | 1 / 0.85 / 1 | 1, 2 | **0.077** (0.049 / 0.105) | **0.038** (0.038 / 0.039) | 13 / 21 | 753 / 768 | 1.161 / 1.238 | 60.3 % |
| sg1lm85fs14 | 1.4 / 0.85 / 1 | 1, 2 | **0.043** (0.049 / 0.037) | **0.028** (0.022 / 0.034) | 11 / 6 | 771 / 747 | 1.147 / 1.261 | 67.5 % |
| sg1lm85fs18 | 1.8 / 0.85 / 1 | 1, 2 | **0.029** (0.033 / 0.025) | **0.033** (0.030 / 0.036) | 13 / 9 | 773 / 777 | 1.201 / 1.291 | 67.1 % |
| **sg1lm70fs14 (kept)** | 1.4 / 0.7 / 1 | 1, 2, 3 | **0.020** (0.025 / 0.011 / 0.025) | **0.033** (0.033 / 0.044 / 0.023) | 11 / 4 / 2 | 765 / 760 / 779 | 1.155 / 1.263 / 1.260 | 65.2 % |

Kept: `followScale 1.4, laneMargin 0.7, shiftGrip 1`. Contacts 0.058 -> 0.020 over three seeds (per seed 0.011-0.025:
at the target pooled, not on every seed), four-offs 0.185 -> 0.033, recoveries 65 -> 17, clearly-faster passes 59.9 ->
65.2 %. Race time 771 -> 768 s mean (-0.4 %, inside 2 %). The median best lap over the drawn target rises 1.161 ->
1.226 (+5.6 %): the cars wait behind more instead of forcing a lane, as on Sonoma (fs 1.4 alone costs as much). The
registry run (`selfplay.ts --track buttonwillow`, seed 1) reproduces the trial bit for bit. Remaining at the kept
setting (3 seeds): T3 entry 6 (inside passes into the T3/T4 pinch), T11 entry 4, T10 exit 2; four-offs are rejoins at
T9 exit and the Dog Leg straight.

### Sonoma (from the 20 Oct knobs)

| trial | knobs (followScale / laneMargin / shiftGrip) | seeds | contacts / car-lap | contacts outside 2040-2110 | four-off / car-lap | recoveries | race time (s) | median best lap / target | clearly-faster passes |
|---|---|---|---|---|---|---|---|---|---|
| head (kept) | 1.4 / 0.85 / 1 | 1, 2 | **0.080** (0.076 / 0.083) | 0.034 | **0.022** (0.018 / 0.025) | 210 / 172 | 688 / 690 | 1.310 / 1.272 | 60.1 % |
| fs18 | 1.8 / 0.85 / 1 | 1, 2 | **0.071** (0.061 / 0.081) | 0.029 | **0.017** (0.022 / 0.012) | 124 / 173 | 697 / 712 | 1.274 / 1.315 | 59.3 % |
| lm70 | 1.4 / 0.7 / 1 | 1, 2 | **0.085** (0.064 / 0.106) | 0.019 | **0.017** (0.020 / 0.014) | 122 / 207 | 694 / 706 | 1.343 / 1.342 | 56.8 % |
| sg15 | 1.4 / 0.85 / 1.5 | 1, 2 | **0.109** (0.092 / 0.128) | 0.047 | **0.031** (0.042 / 0.019) | 168 / 225 | 708 / 704 | 1.324 / 1.288 | 59.3 % |
| fs10 | 1 / 0.85 / 1 | 1, 2 | **0.121** (0.132 / 0.110) | 0.043 | **0.026** (0.020 / 0.032) | 193 / 218 | 686 / 697 | 1.276 / 1.268 | 59.1 % |
| diag: tyre run #9 s 2069-2081 removed (not a fix) | 1.4 / 0.85 / 1 | 1, 2 | **0.026** (0.017 / 0.035) | 0.026 | **0.010** (0.009 / 0.012) | 71 / 100 | 682 / 674 | - | 60.2 % |

No Sonoma change kept: every trial's total is decided by the T7 phantom contact (39 of 70 pooled contacts at the
current knobs), so no knob beats the current setting beyond seed noise. Outside T7, laneMargin 0.7 halves the contacts
(0.034 -> 0.019, the same mechanism as Buttonwillow T3) at +1.7 % race time: **the first trial for the round-14B rerun**,
once T7 is resolved. followScale 1.0 (Laguna's) is clearly worse (0.121), so 1.4 stays.

### Laguna bit-identity

Laguna has no `ai` keys and no shared code changed. Seed 1 before (HEAD 5ae6002) and after the Buttonwillow knob: contacts
2 / 2, four-offs 17 / 17, `contactAt`, `fourOffAt`, race time (620.11 s) and the 45-car finishing order identical
(`out/lg_head_s1.json` vs `out/lg_final_s1.json`), and identical to the 23 Oct run of the same seed.

## 3. What knobs cannot fix

| place | station | cause | evidence | who decides |
|---|---|---|---|---|
| Sonoma T7 brake | s 2068-2069 and 2081, left | phantom wall contact: `vehicle.ts collide()` treats a hull point beyond an oblique tyre-run end segment's line (within its span, far side from the CG) as through the wall; tyre run #9's two end segments put that band on the racing line | #56 stopped from 8.7 m/s on the line by segment 718 (1.39 m deep, t 0.001); #100 launched at 30.9 m/s; `wall_phantoms.ts --track sonoma` lists only these two segments (none on Laguna or Buttonwillow); removing the run's points in memory: 0.080 -> 0.026 contacts, resets 382 -> 171 | owner: either a physics fix (contact only within the segment's half thickness, or only for points that crossed the line this step; touches every track, Laguna to be re-checked) or a scenery fix (the run's ends turned less obliquely, or the run moved off the edge) in the package |
| Sonoma T2 entry | s 350-400 | 134 cars queue up the hill on laps 1-2; cars below the stuck speed for 4 s get marshal resets (65 over two seeds) | snapshots at t 128-150: 16-19 cars in 90 m at 0-5 m/s, `lim follow`; 5 contacts pooled | field size / grid (not a knob); harmless to the contact count |

## 4. Both tracks still move: rerun on the final packages

- **Sonoma round 14B** is being built on track-pipeline: T1, T9A and the T11 hairpin edges refit from the owner's red
  strokes, the lap about 6.5 m longer, T9A from R 31.4 to 25.6 m and the 9a left-hander from 20.6 to 16.3 m, a paved
  escape road on the left at T9A. The Sonoma calibration (3ba7d82) and every Sonoma number above get a rerun on it;
  check whether tyre run #9 at T7 changed (`wall_phantoms.ts`).
- **Buttonwillow round 11** keeps the round-10 geometry with scenery fixes only: the calibration stands; rerun the
  self-play check (and `wall_phantoms.ts`, since scenery changes the walls).

One-line reruns (from the worktree root; the machine-health gate before each, one at a time):

```
npx tsx tools/race/calibrate_field.ts --track sonoma                       # recalibrate (3ba7d82 used --workers 7, ~24 min)
npx tsx tools/race/wall_phantoms.ts --track sonoma                         # phantom wall bands on the racing line
npx tsx tools/race/selfplay.ts --track sonoma --laps 4 --seed 1 --quiet --json tools/race/out/so_head_s1.json
npx tsx tools/race/selfplay.ts --track sonoma --laps 4 --seed 2 --quiet --json tools/race/out/so_head_s2.json
npx tsx tools/race/selfplay.ts --track sonoma --laps 4 --seed 1 --quiet --json tools/race/out/so_lm70_s1.json --lane-margin 0.7
npx tsx tools/race/selfplay.ts --track sonoma --laps 4 --seed 2 --quiet --json tools/race/out/so_lm70_s2.json --lane-margin 0.7
npx tsx tools/race/selfplay_kinds.ts --track sonoma --md --top 8 tools/race/out/so_head_s1.json tools/race/out/so_head_s2.json
npx tsx tools/race/selfplay_table.ts --exclude 2040-2110 so head lm70
npx tsx tools/race/selfplay.ts --track buttonwillow --laps 4 --seed 1 --quiet --json tools/race/out/bw_final_s1.json
npx tsx tools/race/selfplay_kinds.ts --track buttonwillow --md --top 8 tools/race/out/bw_final_s1.json
npx tsx tools/race/selfplay.ts --track laguna_seca --laps 4 --seed 1 --quiet --json tools/race/out/lg_final_s1.json   # 2 contacts, 17 four-offs, 620.11 s
```

Each Sonoma self-play takes ~3.3 min, Buttonwillow ~2.5 min, Laguna ~45 s (single thread).

## 5. Rerun on the final packages (24 Oct 2026, refreshed `integration`)

Packages: Sonoma round 14B (rev 6b766e08d6, lap 4105.328 m), Buttonwillow round 11 (rev 69e80ace38, round-10 geometry),
Laguna unchanged. Knobs unchanged. The Sonoma self-plays below ran BEFORE the round-14B recalibration (on 3ba7d82's
14A scales); see "Calibration" at the end.

### wall_phantoms

| track | segments whose phantom band covers road | reaching the racing line +- 1 m |
|---|---|---|
| sonoma (14B) | 2: s 3729 L tyres seg 1948, s 3907-3908 R concrete seg 348, both reaching 0.0 m into the road | **0** (round 14A: segments 712 / 718 of tyre run #9 at T7, gone with the run in 14B) |
| buttonwillow (r11) | 0 | 0 |
| laguna_seca | 0 | 0 |

### Sonoma 14B, seeds 1 and 2 (4 laps, 134 cars)

| trial | knobs (fs / lm / sg) | contacts / car-lap | contacts outside 2040-2110 (T7) | four-off / car-lap | recoveries | race time (s) | median best lap / target | clearly-faster passes |
|---|---|---|---|---|---|---|---|---|
| head (kept) | 1.4 / 0.85 / 1 | **0.046** (0.039 / 0.052) | 0.046 | **0.011** (0.011 / 0.011) | 52 / 69 | 694 / 693 | 1.334 / 1.224 | 59.0 % |
| lm70 | 1.4 / 0.7 / 1 | **0.039** (0.037 / 0.041) | 0.039 | **0.029** (0.028 / 0.030) | 51 / 106 | 686 / 690 | 1.284 / 1.265 | 58.0 % |
| (14A head, section 2) | 1.4 / 0.85 / 1 | 0.080 | 0.034 | 0.022 | 210 / 172 | 688 / 690 | 1.310 / 1.272 | 60.1 % |

T7 is clean: 0 contacts in s 2040-2110 in all four races (39 of 70 on 14A); recoveries (marshal resets) fell 382 -> 121 (head).
The total halved (0.080 -> 0.046), but outside T7 it rose 0.034 -> 0.046, and the new top place is T9A.

Head, seeds 1 + 2 pooled (900 car-laps; 41 contacts; kinds 17 quarter in a corner, 11 side-by-side in a corner, 5
rear-end in a corner, 4 rear-end on braking, 2 quarter on a straight, 2 quarter on braking; context 27 line, 9 pass):

| station (m) | place | contacts | kinds | four-offs |
|---|---|---|---|---|
| 3000-3050 | T9A entry | 11 | 5 side-by-side, 4 quarter, 2 rear-end in a corner | 0 |
| 350-400 | T2 entry | 9 | 6 quarter, 2 side-by-side, 1 rear-end in a corner | 0 |
| 3600-3650 | T11 entry | 6 | 4 quarter, 2 side-by-side in a corner | 0 |
| 2500-2550 | T8a exit | 3 | 2 rear-end, 1 quarter in a corner | 0 |
| 3050-3100 | T9a (left-hander) entry | 2 | 2 side-by-side in a corner | 1 (traffic follow) |
| 2550-2600 / 300-350 / 250-300 / 200-250 | T8a exit, T2 brake, straight | 2 each | quarter / rear-end | 0 |
| 2750-2800 | straight (bypass blend) | 0 | - | 3 (traffic grip) |

lm70 pooled (894 car-laps; 35 contacts, 18 pass / 14 line): T9A entry 12 (6 quarter, 5 side-by-side, 1 rear-end in a
corner), T11 entry 3 + 2, T2 entry 3, the back straight s 2750-2950 5 with 6 four-offs (traffic grip / rejoin), T9 exit
1 + 2 four-offs. Four-offs 26: 12 traffic rejoin, 11 traffic grip.

**T9A chicane, s 2990-3120 (tighter 14B radii: R 25.6 m right, 16.3 m left):** contacts head 6 + 7 = 13 of 41 (32 %;
on 14A 5 of 70), all at s 3018-3070, the right-hander's apex and the turn to the left-hander, in a corner (side-by-side
and quarter: the 14A racecraft pattern of a pass lane taken away at the apex); lm70 5 + 7 = 12. Four-offs there: head
1 (s 3068, traffic follow), lm70 3 (s 3062-3065, grip / rejoin); none alone. So the tighter chicane is now the first
contact place, with traffic four-offs at its exit; it is not an alone-car departure in these races (the kerb probe's
-1 m run departs, the AI line does not).

**Not kept:** laneMargin 0.7 cuts contacts 0.046 -> 0.039 (within the two-seed spread) but nearly triples the four-offs
(0.011 -> 0.029, back-straight and T9 exit rejoins) for -1.0 % race time; on 14A outside T7 it halved them. Sonoma stays
at 1.4 / 0.85 / 1. Target 0.02 is not met; T9A (13), T2 entry (9 + the lap-1/2 hill queue, 56 resets) and T11 entry
(6) are the places. The owner's T9A options (ledger round 14B: the chicane margin as built, a lap-wide 2.0 margin, or a
speed reserve in the short-corner model) stand; the reserve would be new AI mechanics, not done here.

### Buttonwillow r11, seed 1 (kept knobs 1.4 / 0.7 / 1)

| package | contacts / car-lap | four-off / car-lap | recoveries | race time | median best lap / target | first five |
|---|---|---|---|---|---|---|
| round 11 (merged tree) | 0.019 (7) | 0.019 (7) | 4 | 756.0 s | 1.157 | 562 48 26 333 9 |
| round 10 package, merged code (diagnostic) | 0.025 (9) | 0.033 (12) | 11 | - | 1.155 | 48 333 26 562 9 |
| round 10, section 2 (kept row, seed 1) | 0.025 | 0.033 | 11 | 765 s | 1.155 | - |

Not the round-10 numbers: the round-10 package on the merged code reproduces section 2 exactly, so the merge changed
nothing; the difference is round 11's kerbs (one strip dropped, 15 widths from the onboard, the T5 apex run extended),
which the physics drives on. Within the target at seed 1; the calibration (on round 8/10 geometry) is unchanged.

### Laguna seed 1

Bit-identical: the same seed on the pre-merge code (b779969, run from a `git archive` copy) and on the refreshed tree
give 2 contacts, 17 four-offs, 2 recoveries, race time 620.11 s, identical `contactAt`, `fourOffAt`, `recoveryAt` and
45-car finishing order (40 83 0 1 156 ...).

### Calibration on round 14B (rev 6b766e08d6)

`npx tsx tools/race/calibrate_field.ts --track sonoma --workers 4` (as 3ba7d82, 4 workers instead of 7 for the
machine's load rule; 1144 s), AI_VERSION 8, the track's own identity.json, 1195 fits (134 cars + 1061 stints). What
moved:
- AI Probe at scale 1: 141.73 s (14A) -> **143.42 s** (+1.2 %: the lap 6.5 m longer and the tighter T9A).
- Scales: median new / old **1.020** (p5 1.007, p95 1.036; extremes 0.60 and 1.17 on the slow stints that sit on the
  scale-0.6 floor): every car needs about 2 % more of its grip to hold its real lap on the slower lap.
- Fit errors (1189 AI fits): median 0.11 %, p95 0.19 % (unchanged); outside 0.5 %: **5 fits in 2 cars** (17 in 8 on
  14A): #685_sp (car +0.59 %, stints 0 +1.92 %, 2 +0.71 %, 9 +0.59 %) and #747 stint 6 (+0.98 %), left as the tool
  wrote them; worst 1.92 % (14A 12.15 %, #515 stint 2, now within tolerance).
- The Sonoma self-plays above ran on the 14A scales. **A seed 1-2 rerun at the kept knobs on these scales is still to do**
  (not run: the machine was on battery when the calibration finished).
