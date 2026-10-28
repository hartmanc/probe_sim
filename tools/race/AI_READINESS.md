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

### 5b. Sonoma round 14B on the round-14B calibration (24 Oct 2026, 17:30 PDT; the rerun owed from §5)

`selfplay.ts --track sonoma --laps 4 --seed {1,2} --quiet` at the registry knobs (followScale 1.4, laneMargin 0.85, shiftGrip 1),
package rev 6b766e08d6, pace.json from cf2a09d (scales +2.0 % at the median):

| seeds | contacts / car-lap | four-off / car-lap | recoveries | race time (s) | median best lap / target |
|---|---|---|---|---|---|
| 1, 2 pooled | **0.054** (0.038 / 0.071) | 0.024 (0.020 / 0.027) | 43 / 93 | 665 / 698 | 1.250 / 1.252 |
| §5, 14A scales | 0.046 (0.039 / 0.052) | 0.011 | 121 | 694 / 693 | |

Where the 48 pooled contacts are (50 m bins): **s 3000-3050: 21** (the T9A right-hander's entry and apex; 22 of 48 in s 2950-3150),
s 3600-3650: 6 (the T11 hairpin entry), s 350-400: 3 (T2 entry), s 2150-2200: 3 (T7). T7 brake s 2040-2110: 0 (the phantom wall is
gone with the round-14B package). The 0.02 target is not met; the chicane is now about half of Sonoma's AI contacts, and no existing
knob reaches it (laneMargin 0.7 tripled the four-offs in §5). Levers for the owner: a per-track no-pass stretch through the chicane
(the Corkscrew rule in `driver.ts` is hard-coded; a per-track list would be the same mechanic), a per-track corner-speed reserve, or the
lap-wide line margin; see the coordinator's matrix of 24 Oct.

## 6. Passing where the lane closes at the apex (24 Oct 2026, branch `ai-passing`)

Owner's call: no no-pass zone at the chicane, fix the shared pass logic. Traces: `selfplay` seeds 1 and 2 on Sonoma round
14B at the registry knobs, every car every 0.1 s (a local copy of `selfplay_trace.ts` that also keeps the pass lane,
pass phase and target, git-ignored), the 3-5 s before each contact in s 2950-3150, 3580-3680 and 330-420, plus a probe
that replays one car's pinch-guard scan with the driver's own helpers.

### Diagnosis

The geometry (lane coordinates = offset from the racing line, [right edge / left edge]): T9A is a right-hander whose line
runs from the left edge (s 2990: -10.2 / +1.0) to the right-hand apex at s 3048-3050 (-1.5 / +13.3) and back left for
9a (s 3080: -16.8 / +3.6). An inside (right) lane 2.6 or 5.2 m right of the line exists down to s ~3035 (edge -6.8 at
3033) and is gone over s ~3040-3058: the road clamps it onto the line, a 10-15 m stretch. T11 is the same shape
(s 3641: -3.7, s 3651-3661: -2.0 / -1.9), T2 too (s 397-427: -2.3 to -1.2).

Pooled seeds 1-2 at 152d422 (48 contacts, 22 in s 2950-3150): 33 traced in the windows. In the chicane and T11 the
pattern is one: **a car held in a lane right of the line (a pass in hand, phase 1, or a pass just given up and waiting
to merge back, phase 2) is level with or 1-5 m behind the car on the line (centre distance 0.4-5 m: overlapping) when the
road shuts its lane at the apex.** The road edge sweeps 4-6 m across the lane coordinates in 20 m, the held shift is
clamped to the road at the look point, so the car in the shut lane is steered left into the car on the line at 1-4 m/s
(quarter and side-by-side contacts at s 3018-3050, closing 1-4 m/s). The car on the line makes room only for a car
passing it (and only at its rate-limited lane-change speed, 0.8-2 m/s on Sonoma's shiftGrip), moving 1-2 m out by the
contact. Of the 22 chicane contacts, 13 are of this kind; the others are lap 1-2 rear-ends on braking into a queue
stopped at the apex (closing 5-8 m/s, s 2981-3018, line to line: the car ahead at 1-4 m/s), a different mechanism.

Why the existing guards did not hold the car back: the **pinch guard** (a car ahead in the next lane whose lane and mine
close up within 2 s: the car further back drops behind it) is the rule for exactly this case, but
1. its "straight ahead, following handles it" skip compared the two cars' *absolute* lateral offsets from the centre
   line, a few metres apart in s. In T9A the racing line moves 2-3 m across the road between them, so a car one lane
   over read as straight ahead (|dlat| 0.4-0.7 m) while following, which works in lane coordinates, saw it 2.3 m over in
   another lane and did not follow it: neither held the car back;
2. it sampled its 2 s look-ahead every 10 m, so a lane shut for 10-15 m could be stepped over;
3. a passer alongside its pass target (centres within 0.7 car lengths) was exempt ("it makes room"), which at an apex it
   cannot do in time.

**Example 1** (seed 1, #0 behind #701, contact s 3045, t 206.3, closing 1.3 m/s). #0 (target lap 153.4 s) had given up a
pass on #701 (149.6 s; ended `blocked`) and was in phase 2 holding lane -2.6. t 203.4 s 2997: 13.7 m behind, 23.2 vs 15.3
m/s. The probe at t 204.0-204.9 (s 3010-3025, 9.7-5.3 m behind): its own lane -2.6 is clamped to -1.45 ... -0.52 at
s 3044-3050 (#701's lane 0: 0.5-1.5 m apart, needing 2.1), but |dlat| = 0.41-0.70 m, under the 1.6 m "straight ahead"
threshold: the pinch guard skipped #701 and the limiter stayed `follow` / `lane` (a car further ahead) at 15.5-16.2 m/s.
From s 3030 the road pushed #0's lane in (e -2.57 -> -0.64 at s 3046), #701 moved out 0 -> +1.8 (eT +2-3.6, making room
as a car being squeezed) and #0's `alongside` give-way came 2 m behind its centre, too late.

**Example 2** (seed 1, #41 passing #135, s 3043, t 396.2, closing 3.1 m/s). #41 (150.0 s) in lane -5.2 on #135 (131.1 s,
itself passing in lane -2.6). t 393.3 s 2998: 11 m behind at 19.8 vs 9.9 m/s; from t 393.9 its limiter is `pinch` and
`alongside`, 6.4 -> 4.3 m behind; at s 3028 (4.3 m behind its centre, overlapping) the lane -5.2 is shut ahead and the
road takes #41 from -5.5 to -0.8 in 1.2 s into #135, which had pulled out to +2 (its own lane -2.6 clamped to the line
too). Both slowed to 7-9 m/s against a profile of 16-17: the two lanes right of the line both end at the apex.

T11 entry (s 3600-3650, 6 contacts pooled) is the same mechanism (e.g. seed 1 #938 passing #191 in lane -2.6, 3.5-4 m
behind its centre at the shut, s 3641). T2 entry (s 350-420, 3) is mixed: one is the same (seed 2 #327 on #199, lane -5.2,
s 367), the others are lap 1-2 queue rear-ends on the hill (#199 stopped, v 0-1 m/s).

### The fix (`driver.ts`, NOTES "24 Oct 2026: a pass needs its lane through the corner")

1. Pinch guard in lane coordinates (straight-ahead skip and side test on e, as following) and sampled every 5 m.
2. `shutBeside`: a pass in hand is given up (`passEnd` 'shut') when the road shuts its lane beside the car being passed
   within 2 s and the passer would get there neither PINCH_OK car lengths ahead of it nor still behind it; `planLane`
   does not start a pass in a lane the road shuts before the passer would be ahead (over the whole pass, at most 150 m).
The Corkscrew no-pass is unchanged. Solo laps bit-identical on all three tracks (4 cars each): AI_VERSION stays 8.

### Verification: 152d422 (base) against the fix (final), same seeds, 4 laps, registry knobs

`selfplay.ts --json`, base run from a `git archive` copy of 152d422 (it reproduces §5b: Sonoma seed 1 17 contacts, 43
resets; Laguna seed 1 620.11 s, 2 contacts, 17 four-offs). `passAt` (new in `selfplay_metrics.ts`) is the station of
each green pass.

| track | trial | seeds | contacts / car-lap | four-off / car-lap | recoveries | race time (s) | median best lap / target | clearly-faster passes |
|---|---|---|---|---|---|---|---|---|
| sonoma | base | 1, 2, 3 | **0.046** (0.038 / 0.071 / 0.032) | **0.022** (0.020 / 0.027 / 0.020) | 43 / 93 / 7 | 665 / 698 / 658 | 1.250 / 1.252 / 1.232 | 59.2 % |
| sonoma | final | 1, 2, 3 | **0.022** (0.026 / 0.018 / 0.022) | **0.015** (0.011 / 0.018 / 0.016) | 34 / 68 / 1 | 676 / 711 / 653 | 1.288 / 1.231 / 1.217 | 59.2 % |
| buttonwillow | base | 1, 2 | **0.018** (0.019 / 0.017) | **0.011** (0.019 / 0.003) | 4 / 2 | 756 / 757 | 1.157 / 1.281 | 66.5 % |
| buttonwillow | final | 1, 2 | **0.022** (0.019 / 0.025) | **0.017** (0.027 / 0.006) | 2 / 1 | 759 / 757 | 1.134 / 1.287 | 67.6 % |
| laguna_seca | base | 1, 2 | **0.030** (0.012 / 0.049) | **0.084** (0.100 / 0.068) | 2 / 3 | 620 / 593 | 1.144 / 1.116 | 69.8 % |
| laguna_seca | final | 1, 2 | **0.055** (0.061 / 0.049) | **0.092** (0.115 / 0.068) | 3 / 2 | 597 / 588 | 1.116 / 1.094 | 70.1 % |
| laguna_seca | base | 1-8 | **0.031** (0.012 / 0.049 / 0.036 / 0.025 / 0.031 / 0.043 / 0.019 / 0.032) | **0.093** | 20 | 602 mean | 1.122 mean | 68.8 % |
| laguna_seca | final | 1-8 | **0.033** (0.061 / 0.049 / 0.018 / 0.044 / 0.044 / 0.024 / 0.024 / 0.000) | **0.085** | 26 | 601 mean | 1.119 mean | 68.3 % |

Race time: Sonoma +0.9 % (mean 674 -> 680 s), Buttonwillow +0.2 %, Laguna -0.2 % (8 seeds). Pass completion by pace
ratio (< 0.85 / 0.85-0.92 / 0.92-0.97): Sonoma 76 / 62 / 52 % -> 74 / 61 / 54 %; Buttonwillow 83 / 70 / 57 -> 80 / 67 /
62 %; Laguna (8 seeds) 87 / 64 / 48 -> 86 / 63 / 49 %. All green passes: Sonoma 3710 -> 3717, Laguna (8 seeds) -5 %.
**Passing through the chicane is kept**: green passes in s 2950-3120, seeds 1-3, 571 (159 / 225 / 187) -> 634
(219 / 230 / 185).

Sonoma contacts by place (seeds 1-3 pooled): T9A entry s 3000-3050 **27 -> 6** (10 side-by-side + 10 quarter in a
corner, 7 rear-end -> 3 side-by-side, 2 quarter, 1 rear-end); T11 s 3580-3720 10 -> 10 (the lane shuts there too, but
after a longer braking zone from 35-40 m/s: the 2 s look-ahead starts the drop-back too late, see "not reached");
T2 s 240-420 6 -> 5; contact context pass 25 -> 7, line 31 -> 23. Recoveries 143 -> 103
(the lap-1/2 queue at T2 entry: 71 -> 49). Four-offs 30 -> 20.

Buttonwillow (seeds 1-2): 13 -> 16 contacts, T11 entry s 4350-4400 4, T1 entry 3, T3 entry 2 (base: T3 exit 2, the T8
brake 2); four-offs 8 -> 12 (7 traffic grip). The two seeds are within the round-10 kept setting's spread (0.011-0.025
per seed in §2).

Laguna: seeds 1-2 are not the same races (the fix changes every pass decision, so the races diverge). Seed 1: contacts
2 -> 10 (T3 brake 2, the Corkscrew brake s 2718-2749 3, T11 exit 2, T9 brake 2, T4 1), four-offs 17 -> 19, race time
620.1 -> 596.8 s, winner #40 -> #0 (8 of 45 cars in the same place, mean move 3.9 places); seed 2: contacts 8 -> 8,
four-offs 11 -> 11, 593.2 -> 587.5 s, winner #37 both (8 of 45 in place, mean move 3.1). Over 8 seeds (the band in
NOTES has per-seed contacts 0.012-0.075) nothing moves beyond the spread: contacts 0.031 -> 0.033, four-offs
0.093 -> 0.085, clearly-faster passes 68.8 -> 68.3 %, race time 602 -> 601 s.

### Not reached, and the alternative that reaches it

| | kept: 2 s look-ahead (fe) | 3 s look-ahead (ff) | base 152d422 |
|---|---|---|---|
| Sonoma contacts, seeds 1-3 (target <= 0.02) | 0.022: **not met** by 3 contacts | **0.016** | 0.046 |
| Buttonwillow contacts, seeds 1-2 (<= 0.02) | 0.022: **not met** by 1.5 contacts | **0.014** | 0.018 |
| Laguna contacts / four-offs, 8 seeds | 0.033 / 0.085 (= base) | **0.018 / 0.072** | 0.031 / 0.093 |
| Laguna seed 1 contacts (0.012 today) | 0.061 | **0.000** | 0.012 |
| Laguna clearly-faster passes, 8 seeds | 68.3 % (= base) | 66.2 %, all green passes -9 % | 68.8 % |
| Sonoma race time | +0.9 % | +1.9 % | |
| `ai_behaviour` at today's thresholds | **all pass** | **2 fail**: "full field, 2 laps" (completed 51 %, needs > 58 %; > 15 % quicker 63 %, needs > 72 %), "within 3 %" (no defending move) | pass |
| verdict | kept: the only setting that passes every behaviour test | not allowed (would need a test loosened) | |

Also tried and dropped (each fails "full field, 2 laps" at its threshold): 3 s for the pinch guard only (Sonoma 0.020,
completion 59 % in the test but "within 3 %" fails); 3 s only for a car in a pass lane or waiting to merge (57 %);
3 s only where a braking zone is ahead (profile 3 s ahead > 5 or 8 m/s below the current speed: 57-60 %, one defensive
move against a clearly faster car); the planning check letting a pass start when the passer would still be behind at
the shut (Laguna four-offs 0.093 -> 0.110 over 8 seeds: cars pulled into the outside lane at T4's apex that the track-out
takes away). What remains at T9A and T11 is mostly a car waiting to merge back (phase 2) 1-5 m behind a car on the line,
both braking at their limit, so the one behind cannot drop back in 2 s.

### Review round (GPT 6 Astra, 24 Oct 2026)

- **Planning horizon.** The code and NOTES now say what the check does: my speed x the occupancy horizon Tn =
  min(PLAN_T, D / adv) (the whole pass up to 10 s, its first 10 s for a longer one), at least the pass-in-hand look-ahead,
  at most PLAN_SHUT_MAX = 150 m (an absolute cap on the planning scan now). Checking long passes to their end (D / adv)
  was tried, seeds as above: Sonoma 0.022 -> **0.031** (0.045 / 0.032 / 0.016), Buttonwillow 0.022 -> 0.019, Laguna
  8 seeds 0.033 -> **0.038**, four-offs 0.085 -> 0.091, Sonoma green passes 3717 -> 3481 (-6 %): not kept. The kept code
  reproduces the tables above bit for bit (Laguna seeds 1 and 4, Sonoma seed 1: contacts, race time, finishing order).
- **Lane clamps.** Kept different and documented: the passer's lane as a pass lane is held (PASS_EDGE from the edge),
  the passed car's as a car off a pass is held (0.15 m): each where that car will be.
- **dv floored at 0.** Intended and documented: a passer falling back is projected where it is now.
- **Tests.** `ai_passing.test.ts` now also covers planning (`planLane` rejects the inside lane 45 m before the slowest
  corner's apex behind a car 15 % below its profile, finds a lane on the widest stretch) and a 8 s multi-tick run
  (after 'shut' the car is behind the other car's rear at its apex and starts merging back). Deleting the planning check
  fails the planning and multi-tick tests; deleting the 'shut' end fails the first and multi-tick tests.
- vitest 513 passed (511 + 2 new), build clean.

## Mid-Ohio field pace and calibration (26-27 Oct 2026, branch `field-mid-ohio`, stage 4)

The real Lemons "Mid-West Crisis" field (MyLaps race session 11926749, 10-12 Apr 2026), not the registry's Laguna
stand-in. `TRACKS.mid_ohio` still points at `cars/field/pace.json` (+ the global identity), so the tools take
`FIELD_TRACK=mid_ohio FIELD_PACE=cars/field/mid_ohio/pace.json FIELD_IDENTITY=cars/field/mid_ohio/identity.json`
(tools/race/load.ts `pacePath` / `identityPath`, inert when unset: Buttonwillow and Sonoma regenerate byte-identically
with the old and the new tool, Laguna's files are not touched).
```
FIELD_TRACK=mid_ohio FIELD_PACE=cars/field/mid_ohio/pace.json FIELD_IDENTITY=cars/field/mid_ohio/identity.json \
  npx tsx tools/race/pace_track.ts --track mid_ohio --session 11926749 --own --label "Mid-Ohio (Mid-West Crisis, 10-12 Apr 2026)" --source "<the file's source line>"
FIELD_TRACK=... (same three)  npx tsx tools/race/calibrate_field.ts --track mid_ohio --workers 6     # 677 s
```
- **Field**: 85 cars (90 classified; ids from identity.json: 36 `_mo`, #56 TPF Racing = id 156), 702 stints (every car has
  at least one), no player row (#619 did not race). Left out as at Buttonwillow (no lap: #164, #713, #991) and Sonoma
  (no identity row, no placeholder cars: #643, #116); all five named in `source`.
- **Rules** (pace.ts / pace_rules.ts): green non-pit laps, outliers over 1.3 x the raw median dropped, stints between
  stops, out laps dropped, laps over 1.2 x the stint median or under 0.97 x the official best dropped, 5 laps minimum.
- **Spread**: car target laps 107.755 s (#372 Lemonaid) to 137.418 s (#318 Fat Bastard Racing), median 121.87 s; stint
  targets 105.11 to 162.78 s; the widest car has a slowest/fastest stint ratio of 1.30.
- **Calibration** (AI_VERSION 8, the track's own identity.json, 787 fits = 85 cars + 702 stints, tolerance 0.2 %): AI
  Probe at scale 1 on the Mid-Ohio package (rev ea1a07f8bd) 118.55 s. Fit errors: median 0.12 %, p95 0.19 %, worst
  0.40 %, none outside 0.5 %, none not converged. Scales: median 0.871, range 0.375 to 1.372 (21 fits under 0.6, the slow
  stints; 202 at or above 1.0).

## 7. AI round 1 (27-28 Oct 2026, branch `ai-round-1`)

Pace anchor, AI strength, the player's pace; Part D (racecraft against a close car) tried and dropped: src/physics/ai/NOTES.md
"27 Oct 2026: round 1". Runs: `tools/race/out/r1/` (local; `sum.py <prefix>`). Bands, 4 laps, seeds 1-8, pooled per car-lap:

| track | contacts main / A-C / +D | four-off main / A-C / +D | clearly-faster completed main / A-C / +D |
|---|---|---|---|
| Laguna | 0.027 / 0.027 / 0.034 | 0.094 / 0.094 / 0.076 | 69.3 / 69.3 / 70.3 % |
| Sonoma | 0.028 / 0.028 / 0.027 | 0.011 / 0.011 / 0.010 | 59.2 / 59.2 / 59.2 % |
| Buttonwillow | 0.015 / 0.015 / 0.017 | 0.009 / 0.005 / 0.008 | 63.7 / 65.2 / 63.1 % |
| Mid-Ohio (no knobs) | 0.028 / 0.028 / 0.016 | 0.072 / 0.072 / 0.073 | 62.7 / 62.7 / 62.3 % |

Player pass cost (`--player-scale 1.05`, 5 laps, seeds 1-8), AI cars passed per race / mean s within 20 m behind before the
pass, A-C -> +D (all three D rules): Laguna 12.9 / 30.5 -> 14.5 / 30.2, Sonoma 11.1 / 29.8 -> 14.2 / 23.5, Buttonwillow 9.4 /
33.5 -> 11.8 / 29.7, Mid-Ohio 7.2 / 30.8 -> 9.5 / 25.0.

Mid-Ohio knob trials (A-C tree, 85 cars, 4 laps, seeds 1-4; followScale / laneMargin / shiftGrip):

| trial | contacts (per seed) | four-off | clearly-faster completed | green passes | race time | best lap / target |
|---|---|---|---|---|---|---|
| none 1 / 1 / 0 | 0.029 (0.028 / 0.019 / 0.027 / 0.042) | 0.073 | 61.3 % | 2034 | 541 s | 1.187 |
| 1.4 / 0.85 / 1 | 0.011 (0.010 / 0.010 / 0.010 / 0.016) | 0.008 | 66.6 % | 1345 | 543 s | 1.173 |
| 1.4 / 0.7 / 1 | 0.007 (0.003 / 0.016 / 0.003 / 0.007) | 0.003 | 65.2 % | 1092 | 539 s | 1.180 |
| 1 / 1 / 1 | 0.037 (0.039 / 0.026 / 0.031 / 0.052) | 0.016 | 66.0 % | 1414 | 529 s | 1.163 |
| 1.4 / 1 / 0 | 0.008 (0.007 / 0.007 / 0.013 / 0.007) | 0.044 | 66.7 % | 1751 | 551 s | 1.190 |
| **1.8 / 0.85 / 1 (kept)** | 0.012 (0.013 / 0.017 / 0.007 / 0.010) | 0.012 | 73.1 % | 1287 | 544 s | 1.184 |

Kept the block that reaches <= 0.02 with the most clearly-faster completion; every block with shiftGrip 1 cuts all green
passes by a third or more (1.4 / 1 / 0 keeps 86 % of them, at four-off 0.044).
