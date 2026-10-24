# Sonoma round 14, part B

Owner, round-13 drive (`compare/sonoma/owner_findings.md`, "Round 13 drive"): T1-T2 edges from his strokes, the T10 wall
end facing traffic; Astra's judge r14a regression (the drag-strip continuation's white edge line gone).

## Part 1: T1-T2 edges from the owner's red (stage 1; owner checkpoint, NOT published)

### Tools ported (buttonwillow f9c7aec / e1dba23)

- `compare/owner_edges.py`, `owner_merge.py`, `owner_mouths.py`, `owner_kerbs.py`, `test_owner_edges.py`, `outline_page.py`.
  Changes for Sonoma's frames only: `owner_edges.py --frames/--window` (the drawing page's `frames.json`: centre, px, mpp)
  and `--strokes` (keep stroke-coloured pixels within 3 px of his stroke vectors: 340 / 351 red pixels of the close-ups
  were a red roof and a red trailer); `owner_mouths.py --across` (a mouth named in his words whose arc meets one green
  line) and `--step` (a junction where his red ends on one line and resumes on another); `outline_page.py` runs without a
  width model (owner-reference gates, per-window widths before / after in every caption).
- Builder: `edges_spline` owner readings / anchors / chains (inert without `spline.owner_edges`), `edge_gate` OWNER_REF,
  `owner_reference`, `owner_station_gate`, `owner_waviness`, the width / band code and a new `owner_gates` (width against
  the width between his lines, 20-80 m band of fit minus red) for a circuit without a width model; `build_track`
  `owner_windows` / `owner_ref`, the owner files in the geometry hash, the per-window share gate, and `centre.local` as a
  LIST of windows (refitted in order, each holding everything outside it; the first is exactly round 11's refit).
  `trackcfg` remaps the owner windows and the local windows. Tests: `test_owner_edges_fit.py`, `test_owner_reference.py`
  (Laguna declares none; Sonoma's are local), `compare/test_owner_edges.py`: 49 Python tests pass.
- Regression proof: the new code with the round-14A config reproduces round 14A's stage 1 byte for byte
  (`out/sonoma_r14b_repro`: track.json and heightfield.bin `cmp`-identical to `public/tracks/sonoma`).

### What his strokes digitised to (`tracks/sonoma/owner/r14/`)

Frames checked against capwin re-renders of `public/tracks/sonoma`: zero pixel offset, JPEG noise only (p95 |d| 1-2).
Per window (`owner_edges.py`): w_s0250 left 169 / right 163 stations, close_s0175 61 / 62, close_s0205 57 / 61; green
298 / 71 / 61 points. Merged (`owner_merge.py`, round-14A stations): left 207 stations s 144-357 (gap 224-229, where his
red jumps), right 192 stations s 145-337; 17 stations where two windows differ by more than 0.3 m (his stroke
repeatability, 0.30-0.50 m, all at s 175-191 and 236-237 left, 198 right). Mouths (`mouths.json`):
- right 166-179, `red across`, 13.4 m, cones: his arc from where his green (the access road's edge) ends on it to where
  it rejoins his edge line. The paddock is on the package's RIGHT at T1 (the drive runs west there; the pit lane is on
  the left), so the brief's "left (paddock-side)" is the package's right.
- left 223-230, `junction step`, no cones, step 4.36 m: his red along the pit-exit blend line ends at s 223 and resumes
  on the merged pit-exit lane's outer edge at s 230, where his green (the pit-lane edge) meets it.

### The refit (config: `spline.owner_edges` local, `spline.owner_mouths`, `centre.local` second window config 114-383,
### `gate.exempt` right 145-198 for the access-road mouth, as Buttonwillow's mouth exemptions)

Width (m, median per 20-station range, same world points; round 14A -> 14B):

| s | width | change |
|---|---|---|
| 140-160 | 18.53 -> 18.32 | |
| 160-180 | 18.03 -> 17.28 | right edge on his arc across the paddock mouth (was 1.3 m into it) |
| 180-200 | 16.10 -> 15.84 | |
| 200-219 | 15.65 -> 15.43 | left no longer bulges toward the pit lane (0.3-0.7 m), right 0.3 m in |
| 219-239 | 17.73 -> 18.85 | the step onto the merged pit-exit lane at s ~223-230 (his red) |
| 239-259 | 18.70 -> 19.11 | |
| 259-359 | 16.68 / 13.84 / 12.81 / 13.12 / 13.12 -> 16.55 / 13.73 / 12.68 / 12.69 / 12.98 | |

Outside the T1 window (stations < 100 or > 400) both edges lie within 1.7 mm and the centre within 0.8 mm of round 14A
(projected on its polylines). Lap 4098.36 m (was 4098.50). track.json sha256 5bfe29bef15d7588 (not published).

### Gates (stage 1 into `out/sonoma_r14b`, written with --write-on-fail for this checkpoint)

| gate | result |
|---|---|
| owner edge left 144-358 (config window) | 92.3 % within 0.25 m (>= 90 %), max 0.285 m outside the mouth segments (<= 0.5; with them 1.267 at the step) |
| owner edge right 144-358 | 96.4 %, max 0.097 m (with the mouth stations 0.443) |
| owner reference left / right (0.40 m every station, mouths +-12 out) | max 0.285 m at 243 / 0.097 m at 268 |
| owner width (both-edge stations, 123) | max 0.282 m at 243 |
| owner band (20-80 m of fit minus red) left / right | 0.133 / 0.047 m (<= 0.3) |
| fit waviness left / right (against his red's own roll where drawn) | ok / ok (right peak 0.112 m on his stations, his own limit) |
| fit kink left / right | 0.27 / 0.46 deg per station (<= 0.5) |
| **fit left: observations within 0.25 m** | **FAIL 88.7 % (>= 90 %)**; right 93.7 % ok |
| coverage, gaps, painted-midpoint residual, lap length, edge jumps (0.288 m), cross slope, edge gate, world continuity, profile | ok |

Per drawing window (printed, not gated: Buttonwillow gates the config window): left w_s0250 94.6 %, close_s0175 100 %,
close_s0205 76.8 % (97.2 % outside the step's +-12); right 99.4 / 88.7 (100 % outside the arc's +-12) / 96.7 %.

Stations over 0.25 m from his red (outside the mouth segments): left 210 (-0.256 m), 243 (+0.285 m); right none. In the
mouth segments: left 218-235 at the pit-exit step (up to 1.27 m: the spline turns the 4.4 m step over ~15 stations, the
edge-jump gate allows 0.5 m per station); right 164-176 at the arc (up to 0.44 m).

The failing gate. The left side's share of capture rows within 0.25 m of the fit, whole lap, was 90.27 % in round 14A
(fit dumps `work/fit_assoc_left.json`, reproduced run). His red replaces the capture rows where he drew (382 rows at
97.1 % in 14A) by one reading per station (207 at 91.8 %). Outside his window the edges are unchanged (<= 1.7 mm), but the
statistic there reads 88.61 % (6429 rows) against 89.87 % (6434 rows) in 14A: 14A's figure was taken on the local
refit's own stations before its final re-stationing, this one after it, so the rows sampled differ (+-20 per 100
stations, most at s 1800-1900 and 2600-2700). The capture rows inside his window measured against the new edge agree
78 % (they read the pit-exit blend paint and the mouth). So the gate fails because the stretch that lifted the lap over
90 % now follows his red; no part of the lap outside T1 moved. Not loosened; for the orchestrator / owner: d14 measures
the edges against his red where drawn; whether this whole-lap capture statistic should then be taken over the stations
where his red is not drawn (88.6 %, it would still fail) or with his stations counted as his readings (as now) is a
gate-design call this round cannot make.

### Outline windows (owner checkpoint)

`compare/sonoma/edges_r14b/index.html` (the PNGs local): the whole lap every 125 m at 0.12 m/px (s 0-625 first) and
close-ups at s 175, 205, 235 at 0.06 m/px, captions with the width before / after; on w_s0250, close_s0175 and
close_s0205 a second picture with his strokes over the new fit and the mouth's cone points.

## Part 2 (prepared and tested on the round-14A geometry; NOT applied to the package)

Tested by stage 3 with the current config on the round-14A geometry as reproduced by the new code
(`out/sonoma_r14b_p2`, --write-on-fail, never published). The package (`public/tracks/sonoma`) is untouched.

**A. T10.** Measured (not guessed): round 11's run 37 is not a separate wall. The straightened strip (capstrip s
3240-3420, right) shows ONE dark line leaving the outer wall's line and converging smoothly to the tyre wall's head at the
edge; `wall_measure` on that guide: 104 m, 99 % picked, contrast 78, rms 0.41 m (bright top on the same line, 97 %, rms
0.72 m). Its offset from the edge: 12.4 m at s 3290 (on the outer wall's line), 10.4 m at 3335, 7.5 m at 3355, 4.5 m at
3385, 1.6 m at 3398. Round 11's line ran 1-5.5 m inside it between s 3335 and 3390 (its picks were on the parked trucks
along the wall's track side), so its head stood 4.8 m from the edge, 5.5 m inside the outer wall: the "separate wall" the
owner saw; the "dark texture" is the real wall's own line in the ground image. Onboard t112: the pale wall and catch
fence angling in across the grass. Config: that wall re-declared from s ~3324 (0.5 m from run 28: joined) to the tyre
head (joined). In the test build its head reads "joined to concrete run 28" at s 3330. No tyre wall was added: none is
on the evidence.
The old gate had checked run 37's head (4.8 m out, within 8 m) and passed it as "tapered" (4.8 m out at the head, 3.3 m
10 m on, on a wavy line), so the 8 m reach was not what let it through.
Widened wall-ends gate (`exposedEnds`: rigid runs 30 m, tyre runs 8 m as before; a run outside the head never protects
it; the old gate is a subset, checked: every exposure at 8 m is still one at 30 m): new vitest cases (head 11 m out bare
fails and passes under the old reach; the T10 layout bare fails, closed by a tyre link or a cap; pit wall / Armco at 20 m
checked, tyres at 20 m not); the "far" case moved from 15 to 35 m out (a bare head 15 m out now fails, by design).
On the round-14A package: 44 heads checked (was 20), 4 exposed (was 0), with T10 re-measured still the same 4:
right s 1062 9.4 m out (T5 to the T6 crest wall; the capture shows a rounded concrete head at a culvert), left s 735
12.7 m (T4 approach wall below the T3a-T4 stands), left s 3165 14.1 m (T10-T11 board wall; the bypass board wall ends
6.8 m away, farther out), right s 2080 24.2 m (the drag strip's NW far wall). Each needs its own evidence (frames,
captures) before stage 3 can pass: not resolved this round.
Laguna (report only, not changed): 53 heads checked (was 13), 2 exposed (was 1): left s 3259 2.2 m out (osm 640173934,
already exposed at 8 m), right s 920 9.6 m out (osm 640436959, new).

**B. Ground marks.** Cause measured on the round-14A package: 2175 of 2266 paint-line vertices lay off the driven surface,
-0.445 .. +0.260 m (the Chute's lines buried 0.17-0.45 m, the drag strip continuation's -0.168 .. +0.178 m), region or not:
closed-road lines took their zone's centre height + 0.02 m (cross-slope ignored), declared lines the raw heightfield.
Fix (config `scenery.marks_on_surface`, stage 3 after the terrain-override drape, `tools/track/drape_marks.ts` /
`gates/groundMarks.ts`): every paint-line vertex at the package's own driven surface + 0.008 m (the edge lines' lift),
cones, kerb lines and ground signs on it; the app draws ground signs 0.008 m up (was 0.02). Gate "ground marks on
surface" (run_gates.ts, REQUIRED, region or not): every paint-line, edge-line and ground-sign vertex 0 .. 0.01 m above
the driven surface. Test build: 2266 / 12354 / 680 vertices at 0.008 m, 0 off (largest change 0.453 m, the Chute).
Laguna: 11760 edge-line vertices, 0 off (no paint lines). Vitest `groundmarks.test.ts` (4 tests).
The stills (`strip_continuation_to_T7` before / after) wait for the go.

**Also prepared:** the cone line on his paddock-mouth arc (`cone_lines_declared`, 4 cones 4.4 m apart, default orange:
no frame shows cones there, his instruction).

Every other stage-3 gate on the test build passes except the owner-reference ones (expected there: the round-14A edges lie
up to 0.77 m from his red) and the wall ends above. Terrain gates unchanged (930 / 0 over; 0.0098 / 0.048).
Full vitest: 464 passed + 1 expected fail (457 + 7 new).

## Part 2, continued (orchestrator, while the T1 checkpoint is with the owner): the widened gate's four Sonoma heads

Each measured on a straightened capture strip (capstrip, scenery and raw), a zoomed capture window, `wall_measure` and the
package ortho (`round14b/ends/`, local PNGs); declared in config; test-built (stage 3 on the round-14A geometry,
`out/sonoma_r14b_p2`, --write-on-fail); stills from the grass looking along each wall toward its head
(`round14b/stills/end_*_after.jpg`, pose_walk on a dev server pointed at the test package).

| head (round 14A) | what the place has (evidence) | declared | test build |
|---|---|---|---|
| right s 1062, crest wall at the culvert, 9.4 m out | the wall's end curves away from the track into the bank at the culvert: bright top 11.5 m out at the head, 9.1 m 10 m on (c20_s2750 / c20_s2805, wall_measure bright on a guide along the hook, 20 m, 98 % picked, contrast 87, rms 0.09 m); the round-6 line was the track-side shadow smoothed over 3 m, which lost the curve | the head's first 20 m on the measured top, then the existing line from s ~1090 | tapered (11.5 m at the head, 9.1 m 10 m on): ok |
| left s 735, T4 approach wall below the T3a-T4 stands, 12.7 m out | a square concrete head with its catch-fence shadow in open grass; no tyres, no other run upstream (c20_s2420 at 0.02 m/px; strip s 680-790 left; the ortho, an older year, shows the wall ending ~5 m short of the 2026 head); the onboard (t022 / t024) does not resolve the head | nothing invented: **a bare head the real place has, listed for the owner** | still exposed (the one remaining wall-ends failure) |
| left s 3165, T10-T11 board wall, 14.1 m out | ONE wall: the bypass board wall continues past its declared tail and bends toward the track into the T10-T11 board wall (wall_measure dark 51 % / 90 % picked, rms 0.55 / 0.74 m, bright 60 %, c20_s0715 / c20_s0770); round 5's head stood 6 m inside it, on the paddock lot's parked trucks | the board wall's first 35 m re-measured from the bypass wall's tail (joined) to s ~3200 | joined to run 66: ok |
| right s 2080, drag strip NW far wall, 24.2 m out | round 5's third run lay on the continuation's NEAR painted edge line (0.3-0.9 m from the closed road's measured paint; a 0.2 m bright line, no shadow); the wall t066 shows stands at the FAR side: a light concrete wall from the island tip, where a black tyre bundle with a white top caps its head (c20_s0000 at 0.015 m/px), to the T8-8a wall (wall_measure bright, 56 m, 76 % picked, contrast 83, rms 0.22 m) | the wall moved to the far side, joined to the T8-8a wall; a 2 m tyre bundle at its head (a cushion) | joined to the tyre bundle: ok |

Inventory: the t066 row ("light blue concrete wall beyond the Chute") corrected (`attrs.correction`, round 14B): the wall
stands 40-45 m from the T7 road and nearer T8, so its nearest lap stations are T8's; `ahead_m` 125 -> 394.5 (s 2080.5 ->
2350). Only that row of inventory.json is updated (a full regeneration on the current package moved every row ~0.1 m and
unmatched four mast and one cone-line dispositions; not done; inventory.md not regenerated).

Test build: wall ends 44 heads, 43 joined / lapped / cushioned / tapered, 1 exposed (left s 735, above); coverage passes
(MISSING 0); every other stage-3 gate passes except the owner-reference gates (expected on the round-14A edges).

## Laguna's two (report only; Laguna's package and config unchanged)

| head | what the captures show | declaration needed |
|---|---|---|
| left s 3259, osm 640173934 (concrete, 2.2 m out) | an 8 m OSM concrete outline on top of a cluster of black tyre stacks, the bulged head of the tyre wall, 4 m upstream of the long tyre-faced run (strip s 3200-3320 left) | `osm_barrier_overrides`: this way as tyres (kind tyres), extended 4 m to the next run so it joins it; or a declared tyre run over the cluster |
| right s 920, osm 640436959 (concrete, 9.6 m out) | the way is a CLOSED outline (first vertex = last): the gate takes its first vertex (s 920, the run's DOWNSTREAM end by the bridge pier's angled tyre wall) as its head; its real upstream end is at s ~866, where it meets the tyre run (strip s 860-980 right) | `osm_barrier_overrides`: the way as an open line in driving order (s 866 -> 920), or the gate to take a closed ring's lowest-s vertex as its head (a builder / gate change, not made) |

## The failing stage-1 gate, by stretch (not changed; for the owner)

Capture rows within 0.25 m of the fitted edge, 14B stage-1 output (`work/fit_assoc_*.json`; his readings excluded: left
207 at 91.8 %, right 192 at 96.4 %):

| s (m) | left rows | left within | right rows | right within |
|---|---|---|---|---|
| 0-200 | 364 | 89.6 % | 321 | 93.5 % |
| 200-400 | 99 | 100.0 % | 133 | 100.0 % |
| 400-600 | 205 | 84.4 % | 178 | 91.6 % |
| 600-800 | 420 | 98.6 % | 390 | 95.1 % |
| 800-1000 | 247 | 91.9 % | 302 | 89.4 % |
| 1000-1200 | 321 | 90.3 % | 417 | 94.0 % |
| 1200-1400 | 206 | 85.9 % | 261 | 92.3 % |
| 1400-1600 | 421 | 98.3 % | 477 | 100.0 % |
| 1600-1800 | 333 | 88.6 % | 279 | 94.6 % |
| 1800-2000 | 412 | 77.9 % | 615 | 96.3 % |
| 2000-2200 | 191 | 72.3 % | 425 | 83.1 % |
| 2200-2400 | 191 | 80.1 % | 302 | 91.1 % |
| 2400-2600 | 353 | 93.8 % | 407 | 96.3 % |
| 2600-2800 | 273 | 91.2 % | 307 | 89.3 % |
| 2800-3000 | 313 | 98.1 % | 216 | 94.0 % |
| 3000-3200 | 236 | 85.2 % | 372 | 98.1 % |
| 3200-3400 | 262 | 98.5 % | 302 | 91.4 % |
| 3400-3600 | 436 | 87.8 % | 499 | 95.2 % |
| 3600-3800 | 388 | 94.6 % | 416 | 90.9 % |
| 3800-4000 | 557 | 89.4 % | 380 | 95.8 % |
| 4000-4098 | 210 | 40.5 % | 211 | 92.9 % |

The three worst (all left, all outside his window; the edges there are round 14A's to 1.7 mm):
1. **s 4000-4098 (front straight before the line), 40.5 %, 125 misses:** a pair of parallel white lines along the pit-wall
   side; the readings sit 0.34-0.36 m INSIDE the declared straight (fit 'paint') at s 4000-4060, 0.08-0.24 m at 4060-4098.
   A double painted line, the straight held on the outer one.
2. **s 2000-2200 (T7 road), 72.3 %:** the left edge is asphalt to the wall with no paint (feature asphalt_end); readings
   0.3-0.5 m inside the declared parallel straight at s 1980-2010 and scattered either way at 2060 and 2120: an unpainted
   asphalt end the detector reads ragged, the fit held by the straight.
3. **s 1800-2000 (drag strip leg into the fork), 77.9 %:** at s 1860 readings 0.18-0.38 m outside (the strip's SW paint
   turning into the fork corner) and at 1900-2000 0.3-0.5 m inside (the fork junction, gate.exempt 1860-1980, then the
   asphalt end): a junction and a paint line crossing it.

## Part 1b: the owner's ten checkpoint windows (stage 1; owner checkpoint, NOT published)

The owner on the round-14B checkpoint page: no flags at T1 (accepted as fitted: the step and the arc stay); ten windows
flagged and drawn: w_s0500, w_s2125, w_s2250, w_s2750, w_s3000, w_s3125, w_s3375, w_s3500, w_s3625, w_s3750
(`compare/sonoma/owner_edges_r14b/`: strokes.json, docs, frames.json on the round-14B centre).

**Digitising.** The marked PNGs carry the red fit under his red, so the strokes are read from their vectors:
`owner_edges.py --by-stroke` samples each red stroke every 0.25 m and keeps apart the samples whose stroke runs at more than
35 deg to the course at its nearest station (lines across). Per window (left / right stations, green points, lines across):
w_s0500 0 / 118 (he drew the right edge only), w_s2125 122 / 188 (green 528), w_s2250 207 / 222 (349), w_s2750 175 / 186
(144), w_s3000 200 / 167 (385; across 17.5 + 9.2 m), w_s3125 173 / 171 (310; across 17.3 + 12.0 m), w_s3375 158 / 161,
w_s3500 120 / 158 (342), w_s3625 224 / 267, w_s3750 287 / 287; the other across samples are 1-2 m stroke ends. Merged
(`owner/r14b/merged.json`): left 1300, right 1457 stations; 140 / 154 stations where two windows differ by more than 0.3 m.

What the coordinator flagged, checked:
- w_s3000 / w_s3125 (T9A): his red runs along the course past the escape road's mouth; the V his strokes make into the road
  (lat -11 .. -24 m at s 3072-3083) is the across line, left out of the edge. Owner: "T9A is a sharp right hander; on the
  other side of its entry is an escape road ... No cones, just white lines": no mouth, no cones, no exemption (config: the
  2020 fast bypass is that escape road, `off_course` prepared for part 2, below).
- w_s3375: his strokes are on the T10-T11 run (s 3302-3452), both edges; NONE on the front straight (no reading of his at
  s 3841-4107 on either side), so the question of which pit-wall-side line he took does not arise in this window. His
  left red lies on the fitted left edge (100 % within 0.25 m before the refit already); his right red ran 0.4-0.5 m inside
  the round-14A right edge.
- w_s3625 (T11 hairpin): his inner (right) red sits on the asphalt side of the apex kerb: the fit (the kerb's outer limit)
  was 0.88 m outside it over the kerb run. Rule applied (his convention): where a package kerb run lies beside his red and
  the fit sat more than half a kerb width outside it (T2 apex, T7 island, T7a exit outside, T9 exit, both T9A apexes, the
  T11 hairpin apex: +0.62 .. +1.50 m), `kerb_inside` moves his reading out by the kerb width (0.65 m); at the O'Reilly
  island (+0.14 m) and the T10 exit outside (+0.29 m) his red already sits at the kerb's outer limit, no shift.

**Refit.** Owner windows (config) 411-533 (right only), 2033-2385, 2673-2856, 2894-3200, 3285-3825; local windows 383-560,
2005-2413, 2645-3228, 3257-3853 refitted in order after round 11's and T1's. Lap 4105.78 m (was 4098.50; official 4088,
0.4 %).

| stretch (m) | width round 14A -> 14B (median) | max change |
|---|---|---|
| 414-532 T2 exit (right drawn) | 12.25 -> 12.16 | 1.72 |
| 2038-2160 T7 approach | 11.37 -> 11.90 | 0.74 |
| 2160-2375 T7 / T7a | 16.65 -> 15.67 | 4.11 |
| 2668-2852 T9 | 12.92 -> 11.82 | 4.64 |
| 2897-3030 back straight end | 11.98 -> 11.43 | 1.67 |
| 3030-3110 T9A | 13.93 -> 13.44 | 4.48 |
| 3110-3202 T9A exit to T10 | 12.72 -> 12.77 | 0.58 |
| 3291-3480 T10 to T11 approach | 13.01 -> 12.05 | 2.51 |
| 3480-3600 T11 approach / pit-in | 13.11 -> 11.56 | 4.84 |
| 3600-3831 T11 hairpin | 12.58 -> 12.33 | 4.15 |

**Gates** (stage 1 into `out/sonoma_r14b`, --write-on-fail; failing):

| owner window (config) | left within 0.25 m / max | right within 0.25 m / max |
|---|---|---|
| 143-357 T1 | 89.8 % / 0.369 (FAIL; was 92.3 %: the later windows' refits re-station the lap) | 96.8 % / 0.121 |
| 411-533 T2 exit | none drawn (printed, no gate: the run's "no owner reading" check failed it; fixed in code since) | 100 % / 0.207 |
| 2033-2385 T7 / T7a | 96.3 % / 0.624 (FAIL: max) | 99.1 % / 0.269 |
| 2673-2856 T9 | 100 % / 0.127 | 100 % / 0.211 |
| 2894-3200 9a / T9A | 85.8 % / 1.812 (FAIL) | 85.1 % / 2.297 (FAIL) |
| 3285-3825 T10 to T11 | 93.3 % / 0.938 (FAIL: max) | 100 % / 0.212 |

Stations over 0.25 m from his red (owner reference, mouth segments left out): left 210 (0.25), 242-244 (0.37), 2262-2267
(0.62), 2299-2304 (0.48), 3035-3070 (1.81), 3074-3080 (0.50), 3087, 3105, 3178, 3519 (0.25-0.27), 3647-3654 (0.74),
3658-3665 (0.36), 3716-3722 (0.35), 3727-3735 (0.94); right 2150, 2203, 2255 (0.27), 3035-3055 (0.70), 3059-3066 (0.69),
3071-3074 (0.52), 3078 (0.49), 3091-3093 (2.30), 3096-3105 (0.79). Owner reference left / right FAIL (1.812 / 2.297 m),
owner width FAIL (2.285 m at 3091), owner band left / right FAIL (1.049 / 0.791 m, both at T9A), world continuity left /
right FAIL (0.093 / 0.079 m at T9A), fit left waviness FAIL (rms 0.044 elsewhere), fit left observations 84.6 % FAIL;
fit right 90.8 %, kinks, edge jumps (0.404 / 0.374 m), lap length, cross slope, edge gate, profile: ok.

**Not done / open.** T9A: the fitted edges miss his red by up to 1.8 m (left) and 2.3 m (right) at s 3035-3105; the spline
(6-station knots) on a centre refitted with stiff smoothing cannot turn the corner as tightly as he drew it, and the world-
continuity gate fails there. Making it follow would take a finer knot spacing or a softer centre fit locally (a builder
change not made this round). T7a exit left (0.62 m) and the T11 hairpin outside (0.94 m at 3727-3735) also exceed the 0.40 m
cap. The page shows all of it to the owner.

Outline page: `compare/sonoma/edges_r14b/index.html` (+ intro.html, extra.html), all 36 windows re-rendered red / green on
the new fit, `_owner` overlays for the 13 drawn windows (T1's three and the ten).

**Prepared for part 2 (scenery only, not applied):** the 2020 fast bypass is the T9A escape road (`off_course=True`,
`kind='escape road'`, `mouth_cones` empty): stage 3 marks its parts `off_course`, the physics keeps them paved
(`SurfaceSample.offCourse`), and the app's and the scoreboard's lap validity count a car on it as off
(src/app/index.ts wheelOff, src/scoreboard/sim.ts allOff); vitest `offcourse.test.ts`. The course's white edge line runs
along the fitted edge across its mouth (edge lines break only at kerbs).

## Part 1b, second run (24 Oct 2026): local knot refinement; STOPPED, not published

What was finished from the WIP (fdb6ab9), and what was dropped:
- **Kept: `spline.refine`** (`edges_spline.REFINE`, a second layer of cubic B-splines at 3-station knots, only inside
  [lo, hi] and only in the local refits whose window holds it; absent = the periodic spline exactly; test
  `test_local_refinement_follows_a_tight_turn_and_is_inert_when_absent`). Zones (config stations): T7a exit 2240-2330,
  T9A 3005-3135, T11 hairpin 3620-3745.
- **Dropped: `centre.soft`** (softer centre smoothing at T9A). Its run (23:09 on 23 Oct, config 33f070ce, this branch's WIP)
  bunched the left-edge stations at s 3087 to 0.07 m apart and spread the right ones to 2.0 m (the centre's radius
  came down to the inside half-width), and world continuity read 0.12 / 0.17 m. Code, config and trackcfg remap removed;
  recentre.py is back to 6784bcc.
- **Measurement corrections (not loosenings; both numbers printed):** (1) the owner-edge share is geometric: each fitted
  edge point's distance to his red (his readings with the kerb shifts, as one world polyline densified to 0.1 m, broken
  at gaps > 3 stations), over every station of the config window, mouth segments included as before (the WIP had
  taken it outside the mouths: reverted). The max and `owner_station_gate`'s 0.40 m cap stay station-based, with the
  geometric max printed beside them. (2) The fit gates (observations, waviness, kink) are measured by one more
  `fit_periodic` pass after the local refits, with hold weight 0 (it returns the held edges exactly, so the geometry
  is not touched) and every owner window in place. Before this, the last local refit's metrics held only its own
  window's owner lines, and were taken before the final re-stationing. So the capture rows inside the other owner
  windows were scored against his red there (T7 road left 50 %). Only runs with `spline.owner_edges` and
  `centre.local` reach this pass.

Conventions kept from 6784bcc: red = the asphalt edge. Where a package kerb run lies beside his red, the course edge =
his red + the kerb width (`kerb_inside`, 0.65 m), because his red is on the asphalt side of a kerb. Green = closed
pavement. A stroke running more than 35 deg to the course is a line across, not an edge (`owner_edges.py --by-stroke`).
T1 is accepted as fitted (the rounded pit-exit step; the paddock-mouth arc with its cone line). At w_s3000 / w_s3125
his red is the course through T9A, and the paving straight on past the T9A entry is an ESCAPE ROAD ("no cones, just
white lines; if you go off you get black flagged"), not a mouth: no exemption, no cone line.

Stage 1 into `out/sonoma_r14b` (--write-on-fail, diagnosis only; 49 min; track.json sha256 3376e97393cc4046, lap
4106.10 m, n 4108). Per config window (share geometric / station-based; max station-based / geometric, outside mouth
segments):

| window | left | right |
|---|---|---|
| T1 143-357 | **89.9 / 89.9 %**, max 0.366 / 0.363 (FAIL: share) | 96.8 %, 0.119 |
| T2 exit 412-535 | none drawn | 100 %, 0.209 |
| T7-T7a 2039-2379 | 98.8 / 98.5 %, 0.393 / 0.365 | 99.4 %, 0.272 / 0.269 |
| T9 2668-2847 | 100 %, 0.129 | 100 %, 0.223 |
| 9a / T9A 2883-3212 | 96.0 %, **0.910 / 0.809** at s 3047 (FAIL) | 97.2 %, **0.780 / 0.628** at s 3091 (FAIL) |
| T10-T11 3297-3842 | 96.6 %, **0.784 / 0.501** at the hairpin outside (FAIL) | 100 %, 0.211 |

Other gates: owner reference left 0.910 m (s 3047, 39 stations over 0.25) / right 0.780 m (s 3091, 11 over) FAIL; owner
width 0.891 m (s 3091) FAIL; owner band left 0.308 m (s 3049, 2 stations) FAIL, right 0.257 ok; **world continuity left
0.201 m (s 3047) / right 0.210 m (s 3079) FAIL** (<= 0.02); edge jumps 0.684 / 0.741 m FAIL; fit left observations 87.6 %
FAIL (right 95.3 % ok); waviness, kink, coverage, gaps, edge gate, profile, cross slope, lap length, painted midpoint: ok.
Compared with 6784bcc: T9A 1.81 / 2.30 -> 0.91 / 0.78 m, the T7a exit 0.62 -> 0.39 m, the hairpin outside 0.94 -> 0.78 m,
but world continuity 0.093 / 0.079 -> 0.201 / 0.210 m.

Stations over 0.25 m from his red: left 242-244 (T1), 2296-2298, 3038-3059 (T9A outside corner, up to 0.91), 3085-3087,
3648-3654 and 3728-3733 (the hairpin's steps); right 2147, 3090-3098.

**Why it stops here: a conflict between his red and the world-continuity gate.** `compare/owner_feasibility.py`
(committed; `round14b/owner_feasibility.json`) fits the smoothest polyline at a uniform spacing that holds the gate's
|third difference| <= 0.02 m to his red (kerb shifts included), with no data across his gaps. This is a lower bound
for any station-indexed edge:
- T9A left (outside of the right-hander, across the escape road's mouth): 0.19 m at 1 m spacing, but **2.00 m** at
  the package's edge spacing there (p95 1.49 m: on the outside of a 22 m corner the edge's stations spread out).
- T9A right (where his line comes back out of the escape road, s ~3091): 0.36 m at 1 m spacing, **2.84 m** at the
  package's (p95 1.65 m).
- T11 hairpin outside: **0.79 m at any spacing**. His red steps in 1.1 m at s ~3650 and out 1.5 m at s ~3730, where the
  light band on the outside begins and ends. No package kerb lies there, so no `kerb_inside`. Both of his windows
  (w_s3625, w_s3750) draw the same steps.
- Everything else he drew can be followed within the gates (0.06-0.31 m). T1 left 0.93 m is his pit-exit step, a
  declared mouth.
Not done: no gate or test loosened; nothing published; part 2 not applied. For the owner / orchestrator: is the hairpin
band a kerb (edge = his red + its width)? At T9A, which gives: the 0.40 m cap or the world-continuity limit (an
evidence-cited local exemption would be a gate-design call, not taken here)?

Regression: Laguna stage 1 (`out/laguna_r14b_repro`) reproduces the pipeline reference: heightfield.bin `cmp`-identical
to `public/tracks/laguna_seca`, track.json sha256 d4e8634710813961, the one known `edge gate left` 0.105 m at 46. Sonoma
outside the local windows: edges within 10.6 mm (left) / 8.2 mm (right) laterally of round 14A, centre within 2.4 mm
p99 (the larger moves are in the windows' blend zones). Python tests: 59 passed (with requests, rasterio, pyproj,
pandas, matplotlib added: without them `test_ground_lines` cannot import build_scenery).

Outline page re-rendered on this fit: 36 windows red / green plus 13 `_owner` overlays (`edges_r14b/`, PNGs local);
extra.html carries the three places still off his red.

## Part 1b, finished (24 Oct 2026, coordinator decisions while the owner is away): stage 1 PASSES

**Decisions (the coordinator's, each for the owner to check):**
1. *T1 share.* The accepted gate design (Buttonwillow round 10's `owner_station_gate`): the 0.25 m count and the cap are
   taken outside his mouth segments (+-12), the all-stations number printed beside it. Distance to his red (geometric).
2. *T9A.* The course edge there has real pavement angles: where his red leaves the straight-on paving across the escape
   road's mouth (left, a convex arc of radius ~8 m) and where it comes back out of the escape road (right). These are
   declared junction corners, `gate.continuity_exemptions` (side, kind, two world points on his red, reason, evidence:
   capture window and stroke). World continuity and edge jumps leave those stations out and report them as
   "exempt (junction corner)" with the measured values, never as a pass. Inside a stretch the edge must be straight
   (chord <= 0.10 m) or smooth per metre (cubic through the stations, sampled at 1 m of arc length: |third difference|
   <= 0.02 m, radius >= 6 m). The gate prints which case holds. Rationale: the per-station limit depends on the spacing.
   On the outside of the R 22 m corner the edge stations sit 1.3-1.6 m apart, so his arc reads 0.06 m per station while
   it is as smooth per metre as anything the gate passes elsewhere.
3. *T11 hairpin outside.* Measured on the clean captures (`compare/band_measure.py`, `round14b/hairpin_band.json`): the
   light apron is 3.1 m wide (median; p10 1.0, p90 4.2), rgb ~186/185/183 (grey-white). Its outer edge does not continue
   the asphalt edge on either side: +1.04 m at its start, +4.06 m at its end (limit 0.3 m). So it is not a flush kerb-type
   strip, and the two steps are declared the same way, kind 'step': one jog over at most 2 station intervals, smooth per
   metre either side. **Open question for the owner: is the hairpin apron a kerb?**
4. Python tests with the full dependency list.

**Builder changes (all config-gated; absent = unchanged):**
- `gate.continuity_exemptions` (edge_gate `exemptions` / `exempt_stations` / `continuity_exemption_report`; build_track
  edge jumps). Kinds: arc / corner (straight or smooth), step (jog <= 2 intervals). Stretches come from world points,
  so re-stationing cannot move them.
- Declared steps in his red: `edges_spline.step_profile`. The spline fits his red with the jog taken out (a sharp step
  minus a smoothstep of the same size over +-30 stations, its size from lines through his readings either side, his own
  fraction inside the jog), and the jog is put back on the edge.
- `owner_edges` entry keys: `project='foot'` reads his line at the foot of its normals (`edges_spline.foot_project`; the
  nearest centre point put a point 10 m out up to a station off its foot, so his reading moved 0.3-0.9 m with the
  stationing and his smooth arc read as kinks); `reach='drawn'` ties capture rows to his line only within 3 stations of
  a reading of his. Without it, at the T2 exit left (he drew only the right) and over the pit-in gap the capture rows
  were associated with an edge 2-4 m away (T2 exit left 52 %).
- `spline.owner_measure='foot'`: the owner gates read every window at the foot of the normals (T1's round-14 entry
  keeps its fit readings). T1's edges, within 3 mm of part 1, had read 0.285 / 0.369 m by station.
- `spline.kerb_ramp='smooth'`: kerb_inside ramps in as a smoothstep over 10 stations. The linear 6-station ramp's
  corners read as third-difference kinks.
- `kerb_inside` runs may be two world points: the 9a kerb runs from the package's kerb strips. At T9A, config stations
  3022-3070 all map to current stations 3078-3086, because the centre moved 3.3 m and the frozen reference centre cuts
  the S, so the 9a kerb shifts had landed 40 stations off.
- `spline.refine` (lo, hi, knot[, mult[, side[, sub-ranges]]]): per-side zones; a penalty multiplier; sub-ranges given
  by two world points on the centre, with the penalty change eased over +-3 rows. Config: T7a (2240-2330, 3 m, x3); T9A
  left 2 m x10 (x0.3 over the arc); T9A right 2 m x30 (x50 over the right-hander's inside apex, where his readings
  jitter; x0.3 over the corner out of the escape road). The hairpin zone is gone (its steps are declared).
- `centre.local` window keys `refit_final=True` (the window's last fit on the uniform stations themselves) and
  `centre_smooth=1.0`. The window's centre is Gaussian-smoothed, sigma 1 station, moving it <= 0.03 m: the refit loop's
  station-scale curvature jitter, carried 10-12 m out by the normals, read 0.03-0.04 m at T7a and T9A. Both on the four
  part-1b windows.
- `centre.restation='index'`: the uniform re-stationing takes the edges along the station index. Outside the window the
  held edges are the window's own half-widths, not re-projections, which had moved the T9A arc 0.15-0.24 m during the
  next window's refit.

**Gates (stage 1 into `out/sonoma_r14b`, passed, no --write-on-fail; track.json sha256 2c043135a7b27767, lap 4105.33 m,
n 4108; 8 min 44 s):**

| owner window (config) | left: share / max, station (geometric) | right |
|---|---|---|
| T1 143-357 | 97.8 % outside mouths (91.3 % all stations) / 0.350 (0.348) | 100 % (96.4 %) / 0.082 |
| T2 exit 412-535 | none drawn | 100 % / 0.142 |
| T7-T7a 2039-2379 | 99.4 % / 0.319 (0.317) | 100 % / 0.212 |
| T9 2668-2847 | 100 % / 0.121 | 100 % / 0.154 |
| 9a / T9A 2883-3211 | 99.4 % / 0.271 (0.259) | 98.6 % / 0.379 (0.325) |
| T10-T11 3297-3842 | 99.8 % / 0.314 (0.259) | 100 % / 0.179 |

Owner reference 0.350 m left (station 242) / 0.379 m right (3091), <= 0.40 at every station. Owner width 0.392 m (242).
Owner band 0.160 / 0.122 m. Fit observations: left 90.9 %, right 95.4 %. Waviness, kink, coverage and gaps ok. Edge jumps
outside the corners 0.313 / 0.416 m. World continuity outside the corners: left 0.0164 m (2260), right 0.0184 m (3043).
Declared corners, exempt (measured):

| stretch | per station: d3 / half-width change | shape |
|---|---|---|
| left 3037-3062 (T9A arc) | 0.063 / 0.775 m | smooth per metre: d3 0.0123 m, min radius 9.9 m |
| right 3074-3096 (T9A out of the escape road) | 0.067 / 0.786 m | smooth per metre: d3 0.0099 m, radius 11.4 m |
| left 3645-3654 (hairpin apron start) | 1.235 / 0.683 m | step: jog 3649-3651 (2 intervals), either side d3 <= 0.0028 m, R >= 48.8 m |
| left 3726-3735 (hairpin apron end) | 1.564 / 0.857 m | step: jog 3729-3731 (2 intervals), either side d3 <= 0.0036 m, R >= 49.8 m |

Lap length 4105.33 m (official 4088, 0.4 %). Painted-midpoint residual, cross slope, edge gate, profile: ok.

Stations over 0.25 m from his red, station-based: left 10 (242-244 T1, the T9A arc flanks, hairpin jog ends), right 4
(3089-3091).

Width (median, round 14A -> 14B, same world points; max change): T2 exit 414-532 12.25 -> 11.49 (2.11: his right red
2 m inside the 14A edge at s 455-470); T7 approach 11.36 -> 11.90 (0.75); T7 / T7a 16.65 -> 15.64 (3.92); T9 12.92 ->
11.82 (4.64); back straight end 11.98 -> 11.46 (1.03); T9A 13.93 -> 13.64 (7.67: the corners); T9A exit 12.72 -> 12.80
(0.58); T10 to T11 approach 13.00 -> 12.05 (2.50); T11 approach / pit-in 13.26 -> 11.54 (5.30); hairpin 12.60 -> 12.29
(4.44).

**Proofs.**
- T1: part 1 (895c5dd) rebuilt in a temporary worktree reproduces its track.json (5bfe29bef15d7588, byte for byte).
  The T1 edges of this build lie within 2.8 mm (left), 2.7 mm (right) and 1.9 mm (centre) of it over s 140-360.
- Laguna stage 1 (`out/laguna_r14b_repro`): heightfield.bin `cmp`-identical, track.json d4e8634710813961, the one known
  `edge gate left` 0.105 m at 46.
- Sonoma outside the local windows against round 14A: centre <= 3.4 mm; edges <= 4.9 mm at s 2440-2630 and <= 1.4 mm at
  3870-4100, but up to 19.2 / 12.9 mm at s 600-1640 (T3-T6: the index re-stationing replaces the projection, whose own
  error was in round 14A's held edges there).

Python tests: 65 passed (59 + 6 new in `test_continuity_exemptions.py`).
Outline page re-rendered on this fit (36 windows + 13 `_owner` overlays; intro.html / extra.html for part 1b, with the
decisions and the apron question).
