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
frame looking ahead: compare what stands on that side). The caption gives the station s, the nearest corner, and the
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
single most wrong thing>". Finish with the ten worst rows of the whole lap, worst first.
```

## After the judge

1. The orchestrator checks each row against the inventory and the captures; true rows become inventory rows (if the
   inventory missed them) and scenery-round work items; false rows are listed with why.
2. The table, round by round, goes in `tools/track/compare/<id>/judge_r<n>.md` (tracked).
3. A build reaches the owner only after the coverage gate passes and the orchestrator has reviewed every compare sheet
   (forward and side) of the current package; the judge's table is attached to the hand-off.
