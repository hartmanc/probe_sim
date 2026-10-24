# Buttonwillow judge round r4 (20 Oct 2026, ~20:50 PDT)

Judge: **the orchestrator (Claude)** with the JUDGE.md prompt and checklist. GPT 6 Astra was tried first (eight batches,
same invocation as r2 and r3) and every batch failed at 20:34 with "Your workspace is out of credits" (`judge_r4/astra_stderr_*.txt`);
no Astra table exists for this round. Package: branch buttonwillow b695c22, rev d7b31ce2af, 4697.634 m (geometry unchanged
from rev e08631e61f, byte-identical). Sheets: `compare_sheets/`, 50 (16 forward, 15 side, 8 back, 6 pit, 5 runoff), all read at
1800 px, plus the 16-sheet hood set `hood_r4/`. Verified before judging: vitest 403 + 1 xfail, build, python 37, Laguna + Sonoma
diffs empty, TS gates + coverage ok (87 rows, 0 missing, 5 dispositions), the package's contents as reported (161 strips, 27 cone
lines, 11 barriers incl. the 1.5 m entry fence and the 0.85 m tree-line tyres, per-station canopies, patterned K-rails).

## Rows

| sheet | s (m) | side | kind | onboard shows | sim shows | verdict |
|---|---|---|---|---|---|---|
| pit_00 | 4294-4361 | ahead | runoff (surface) | the pit-entry pavement in the same grey as the lane and the track | the painted-over entry strip renders near-black between the white lines, a hard tone step against the grey lane from ~4441 on | WRONG_COLOUR (C17): the entry strip's material should be the lane's tone |
| pit_02, side_13, side_14, fwd_15 | 4639-4695 | left | building | the timing tower's upper storey is an OPEN deck with a railing under a deep roof overhang (pit video 21:43), divided glazing behind | a set-back glazed upper storey with mullions under the blue deck; tan ground storey, stair and roof deck as the footage | OK_DIFFERENT (much closer than r3; the open deck is a kit refinement, low priority) |
| fwd_05, runoff_00 | 1700 | left | runoff | a broad paved apron with tyre marks on the T5 exit | dirt beside a narrow pale strip | MISSING paved apron (the agent's open row: needs a capture outline, the edges give no gap there) |
| side_06 | 1839 | left | kerb | the block line at the Dog Leg mouth beside the car | the strip drawn 6.65 m inside the left edge (the one strip the builder still reports) | WRONG_POSITION (edge): held for the geometry round with the owner's mark-ups (a zone there failed waviness and moved the held T2 width in run 33) |
| side_11 | 4045 | right | cone_line | several cones on the right apron | one cone | OK_DIFFERENT (count; the 4046-4054 line exists) |
| side_08 | 2696 | left | cone_line | two cones, one tipped over | one upright cone | OK_DIFFERENT |
| side_10 | 3765 | right | station | the T10 station (inventory 3758 R) | not in the side view at 3765 | FALSE: the hut stands at s 3698, 15 m out, 67 m behind the camera; it shows on fwd_12 at 3650-3700 |
| runoff_02 | 4068 | right | cone_line | cones along the drag-strip boundary | none at the mouth | open (the agent: the frame shows the single cone already placed; no branch outlined) |

Everything else on the 50 sheets reads as the onboard: the kerb runs now reach the block lines' measured ends (T2 apex,
T4 exit, 1430-1480 L, the T5 inside kerb, 4023-4120 R); every station is an open canopy on a pale round base with the cabinet
colour of its frame and its tyre ring; the pit lane has its red/white K-rails, the rounded pale nose, the entry fence, the pit-in
station and three yellow cones at the tower's foot and no others; the aprons at the T1 exit, the T2 inside, T4, T4-T5, T10, the
Zorros mouth and the T11 exit fray into the dirt; the tree-line tyre barrier stands under the trees on the T11 approach; the
3500 mast carries its floodlight head; the crossover and mouth cones stand where the frames show them. Pit sheets 03-05 (the
pit-out lane, no video) are unjudged as before.

Checklist, all sheets: C1-C5 ok or n/a (one wall end, cushioned; joins continuous); C6 ok; C7 ok (0 escapes); C8 ok except the
two count rows above; C9 ok; C10 ok (the pit-out blend is one surface); C11 ok except 1839 L; C12 n/a; C13 ok; C14-C16 n/a;
C17 FINDING on pit_00 only; C18 ok; C19 ok; C20 ok (tower: OK_DIFFERENT); C21 ok.

## Verdict

Ready for the owner's lap. One fix row (the pit-entry strip's tone), two open evidence rows (the T5 exit apron, the 4068 R mouth),
one kit refinement (the tower's open upper deck), and the 1839 L strip that waits for the geometry round with the owner's T2 and
T4 mark-ups. No round 5 before the owner has driven it.
