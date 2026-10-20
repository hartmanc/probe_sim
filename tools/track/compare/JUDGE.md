# Judging the compare sheets (build-track stage 4, before the owner's lap)

The sheets from `camera_walk.ts` + `make_compare_sheets.py` (`tools/track/compare/<id>/compare_sheets/`, local only)
are judged sheet by sheet before any build reaches the owner. Judge: GPT 6 Astra through codex when credits exist,
else the orchestrator with this same prompt (say which in the report). The judge lists differences; it never decides
a fix, and the inventory and the captures settle disagreements, not a re-ask.

## Invocation (Astra)

From the worktree, read-only, one run per batch of at most 8 sheets, the prompt on stdin and the sheets attached:

```sh
cd <worktree>
codex exec -m gpt-6-astra --sandbox read-only -c model_reasoning_effort=high \
  -i tools/track/compare/<id>/compare_sheets/sheet_fwd_00.jpg -i ... \
  < tools/track/out/judge_<id>_<round>/prompt.md \
  > tools/track/out/judge_<id>_<round>/astra_<batch>.md 2> tools/track/out/judge_<id>_<round>/astra_stderr.txt
```

(The form of the 19 Oct review, `tools/track/out/review_sonoma_cp1/astra_stderr.txt`: "Reading prompt from stdin",
model gpt-6-astra, sandbox read-only, reasoning effort high.) If codex reports no credits or quota, the orchestrator
judges with the prompt below and writes the same table.

## Prompt template (fill the braces)

```text
You are judging a racing-sim circuit against real onboard footage, sheet by sheet. Circuit: {name} ({id}), the
{layout} layout. Each attached sheet has six pairs: LEFT is a frame of a real onboard lap ({video url}, {date}) at the
video time mapped to that lap station; RIGHT is the sim's hood camera at the same station facing the driving direction
(forward sheets), or turned {yaw} degrees toward one side (side sheets, where the left image is the nearest onboard
frame looking ahead: compare what stands on that side), or looking BACK along the lap (back sheets: the left image is
the onboard 100 m earlier looking at the same stretch from its other end), or inside the pit lane (pit sheets: the left
image is the nearest frame of a pit-lane video), or from a paved runoff looking back at the track (runoff sheets: the
left image is the onboard at that station, the place seen from the track). The caption gives the station s, the nearest corner, and the
eye-level inventory rows near it (what a person logged from the video: walls with heights, fences, kerbs, tyre walls,
stands, stations, masts, boards).

Ignore: the sim car's own hood and figures, other cars, lighting, sky, clouds, video colour grading, the camera's
height and field of view (the onboard is a wide-angle windscreen camera about 1.3 m up), tree species, grass colour.
The station mapping can be off by up to 30 m: if the same feature appears in the neighbouring pair, it is the same.

For EVERY pair list every difference in what stands beside the track, as rows of this table (one row per object,
nothing else, no prose):

| sheet | s (m) | side (left/right/ahead) | kind | onboard shows | sim shows | verdict |

kind is one of: wall, fence, kerb, tyre_wall, tyre_stack, stand, station, bridge, building, mast, cone_line, boards,
paint, runoff, road_edge. verdict is one of: MISSING (in the onboard, not in the sim), EXTRA (in the sim, not in the
onboard), WRONG_HEIGHT, WRONG_TYPE (e.g. concrete vs tyres, flat vs raised kerb), WRONG_COLOUR, WRONG_POSITION
(more than about 3 m off laterally or 15 m along), FLOATING (does not meet the ground or its supports), OK_DIFFERENT
(different but acceptable, say why). Heights: estimate with known sizes (Jersey barrier 0.81 m, catch-fence posts
3-4 m, cone 0.7 m, a car 1.4 m) and give both numbers. Then one line per sheet: "sheet <name>: <n> rows, worst: <the
single most wrong thing>", and one line with the checklist answers for that sheet: "sheet <name>: C1 ok, C2 n/a, ...,
C21 FINDING" (the checklist is below this prompt in JUDGE.md: paste it here). Finish with the ten worst rows of the whole
lap, worst first.
```

## Checklist (codify round, 20 Oct 2026; from the owner's 54 drive notes, `compare/sonoma/owner_drive_r2/README.md`)

The judge's table lists what differs; the checklist makes sure the differences the owner found by driving are looked for
on every sheet. Answer each line for EVERY sheet (forward, side, back, pit, runoff), as `C<n>: ok`, `C<n>: n/a` (nothing
of that kind in the sheet) or `C<n>: FINDING` with a table row above. The notes each line comes from are in brackets.

| # | check (answer per sheet) |
|---|---|
| C1 | Wall ends: does any barrier run end with an open face or a bare end toward oncoming travel, with no cap, cushion or impact block? [36, 39, 41] |
| C2 | Joins: where two runs meet, is it one continuous line (no step toward the track, no shingled overlap, no gap, no two runs side by side)? [39, 48] |
| C3 | Facings: does every tyre run beside a wall stand against its track face (or meet it end to end), black or white as the footage, stacked to its height? [21, 38, 48, 52, 53] |
| C4 | Run extents: does each wall, tyre wall and fence start and end where the footage shows it (not 20-30 m early or late), with the start the footage shows (cushion, dark section)? [36, 41] |
| C5 | Heights: do walls, fences and boards stand as tall as the footage (Jersey 0.81 m, fence posts 3-4 m), enclosing where the real place encloses? [13, 14] |
| C6 | Bands: is there a light or dark band in the ground texture where the footage shows a barrier, or a barrier where it shows paint? [11, 36] |
| C7 | Containment: is any paved area (drag strip, closed road, paddock) open to the track where the footage shows a wall, tyres or cones? [4] |
| C8 | Cones: colour, size and spacing as the footage, standing on the painted line, none inside a lane or a blend, none where the footage has none? [42, 43, 49] |
| C9 | Pit lane: open end to end (nothing across it), walls on the sides the footage shows, separation wall with its impact barrier at the nose, no rule boards in it? [1, 2, 15, 16, 18, 37] |
| C10 | Pit-out blend: does the lane taper into the track as one surface (no seam, no lighter strip, no wall at its end), with the merge line and cones the footage shows? [24, 25, 26, 42, 43] |
| C11 | Kerbs: a kerb exactly where the clean captures show the block pattern (both sides checked), none elsewhere, colours as the footage, no green after-kerb strip unless shown? [3, 6, 7, 8, 9, 31] |
| C12 | Stands: does each stand start, end and rise where the footage shows it, built into the hill, rows on the ground, nothing floating or buried? [5, 22, S1] |
| C13 | Huts: is each corner station visible from where the footage shows it, roofed, raised, open-fronted, on the side of the wall the footage shows? [30, 40, 47, 49, 50, 53] |
| C14 | Boards: does each board run start and end at the footage's stations, with its names typed in the footage's colours (no blank panels, no logo art)? [34, F4] |
| C15 | Logos: is a painted ground logo the captures show drawn as typed text in its colours, and no smear left in the ortho where it was? [46] |
| C16 | Movable barriers: does the footage show a barrier (Jersey, tyres) that the capture does not (another kind of event), and is it placed and flagged movable? [44, 51, 52, 54] |
| C17 | Surface tone: two road textures, seams or coloured smears between the track, pit lane, runoff and closed roads? [17, 19, 26, 45] |
| C18 | Closed roads: do unused roads look like race track (painted edges, its surface), coned off where the footage shows cones? [12, 45] |
| C19 | Supports: does every bridge, deck and raised structure meet the ground (abutments, piers, stairs, legs)? [29] |
| C20 | Buildings and towers: shape, roof, colours and height as the most recent footage (not old Street View), the tall landmarks present? [20, 22, 23, 25, 33, 35] |
| C21 | Ground: a white blotch or patch baked into the ground texture where the footage has an object (station, vehicle, sign)? [30] |

Per sheet, after the table rows: `sheet <name>: C1 ok, C2 n/a, ... C21 ok` (all 21 answers on one line). A build reaches the
owner only when every FINDING is fixed, or written into the manifest with its disposition and why.

## After the judge

1. The orchestrator checks each row against the inventory and the captures; true rows become inventory rows (if the
   inventory missed them) and scenery-round work items; false rows are listed with why.
2. The table, round by round, goes in `tools/track/compare/<id>/judge_r<n>.md` (tracked).
3. A build reaches the owner only after the coverage gate passes and the orchestrator has reviewed every compare sheet
   (forward and side) of the current package; the judge's table is attached to the hand-off.
