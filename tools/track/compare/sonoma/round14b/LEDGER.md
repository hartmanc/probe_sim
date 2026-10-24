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
