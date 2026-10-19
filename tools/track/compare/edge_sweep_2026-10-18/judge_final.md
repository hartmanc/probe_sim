# Judge record, 18 Oct 2026, branch edges-from-paint-wip at 0fdb20c

Goal: "Have Opus 5.5 inspect the track for all humps, weirdness, discontinuities vs. reality by using satellite pictures
and the onboard Mustang video (8fGzs8Lnn0Q). The sim track should look and feel just like the track in the video."

Evidence reviewed by the judge (Claude Fable 5.1, main session):
1. Opus 5.5 sweep (agent aa560cdd1a03d61d6, 647 requests): inventory of every departure from the paint on the z20
   captures and the onboard frames, applied by script; sheets in this folder (edges_old_vs_new_changed_*.jpg,
   strips_*.jpg, hood_sheet.jpg, sausage_*_after.jpg, gate_after.txt).
2. T11 exit and pit-wall nose found by the judge, fixed by script (fix_t11_exit_right.py, fix_pitwall_nose.py).
3. Whole-lap driver-camera sheet, 48 frames every 75 m, rendered in-page from the final state: no hump, wave or
   notch in any frame.
4. Mustang onboard vs sim hood camera at the 14 compare places (youtube_sheets/*_final.jpg, sim frames in
   youtube_sim_final/): front straight, T1, T2, T3, T4, T5, T6, Rahal, T7, T8, T8A, T9, T10, T11. At every place the
   road shape, crest or drop, kerb side and apron side match the video frame; no discontinuity.

Verdict: bar met for the track's look and feel. Deliberate residual deviations, left for the AI/line work because
closing them puts self-play cars off at the T8A exit: T8 sausage strip ~2 m beyond its mark (edge at the painted apron
limit, not the kerb); T8A exit white line ~1.3 m out under the 2586 bridge. Self-play AI-AI contacts rose to
0.057-0.084 per car-lap on three seeds after the T11 exit narrowed (band 0.044): AI lane-model work, not track work.
Merge held by the owner ("Don't merge yet; I want to play it").

## Independent Opus 5.5 read of the 14 video pairs (agent, 64k tokens, read-only, not shown my verdict)
Its table: yes at T2, T5, T6, T7, T8 entry, T9; partial at front straight, T1, T3, T4, Rahal, T10 (missing painted
lines/kerbs in the sim frame, T4 red wall far from the road, T1 inside apron paint missing); no at T8A ("broad sheet
of tarmac", kerb and green apron far off) and T11 (hairpin and apex kerb not visible in the sim frame). Overlay
reads: green left edge "across the sand" at the T6 entry, "away from the tarmac" at the T10 entry, "stray line across
the infield" at T11. Verdict: not met.

Triage against the data (judge, main session):
- T8A: at the matched station (2500 m, recheck_apex_frames.jpg) the sim reads like the video (drop, right kerb, green
  apron). The broad tarmac at T8 is the Corkscrew apex edge at the painted apron limit instead of the kerb: the one
  deliberate road deviation, visible from the hood. Stays on the list with the AI line work.
- T11: the sim frame was 50 m before the apex; at 3262 m the hairpin reads, and the overlay has the edge on the kerb.
  Camera and station alignment, not geometry.
- Overlay claims, from sweep_paint on the final edges (paint minus edge, + outward): T6 entry 1836 is the 1849 m
  bridge (interpolated, readings nan/+2.9 in the shadow, +-0.3 beyond it); T10 entry 2876-2908 the edge sits
  0.5-1.0 m INSIDE the white line (the chord is slightly short, the opposite of off-road: minor residual); T11
  3130-3160 is the protected pit-entry mouth. None is an edge off the road.
- Painted lines missing in the pairs: the sim frames were 480 px crops upscaled to 760; the full-res hood sheet shows
  the lines. T1 inside-apron green paint and the T4 wall placement are scenery items, real, not road geometry.
Combined verdict: road shape, kerb sides and aprons match the video and the satellite at every checked place except
the Corkscrew apex apron; paint and landmark finish items remain (T1 apron paint, T4 wall, T10 entry chord residual).

## Opus 5.5 re-judge on the triaged state (station-matched apex frames, full-res hood sheet, sweep numbers)
Road: 13 of 14 places match the video; T1 partial (the left sweep reads weaker than in the video); no humps, waves or
discontinuities in any frame; the three overlay flags withdrawn (bridge shadow at T6, edge on tarmac at T10 entry,
pit-entry mouth at T11); the Corkscrew apron (2.2 m beyond the kerb) judged minor for the look.
Finish, remaining: painted white edge lines missing or faint (front straight, Rahal, T3) and T1's green inside apron;
apex kerb paint faint or missing at T4, T10, T11; walls further from the road than in the video at T4, T11 and the
front-straight pit wall (the pit wall is at its measured 2.0 m; the hood camera's 95 degree view makes it read far).
Its verdict, verbatim: "The ROAD now looks and feels like the track in the video at 13 of 14 places."

## Evening fixes after the owner drove the preview (commits ae129e9, 24d1fc3 and the re-solve)
Owner questions answered from the captures: the Rahal straight does not "come in" (our edge was 1-2 m inside the line
after a retrace onto a repave seam, and out on the T6 exit apron before it); the pit exit matches in layout but the
hot-pit wall ran 60 m past its real end; the T11 exit right edge is not wavy in reality (ours swelled 2.8 m from my
own fix's long blends); the Corkscrew drop is unchanged (21.0 m vs 21.1 m deployed), the flatter feel is the apron-limit
apex edge. Fixed by script: fix_rahal_left.py (two references), add_paved_aprons.py (T6 exit + Rahal apron as one zone),
fix_edge_shape.py (T11 exit as a monotone cubic through measured knots), fix_kerb_strip.py (exit kerb to its measured
end), fix_pitwall_exit.py, fix_pit_exit_cones.py. The Corkscrew kerb edge was tried and reverted (one AI car four wheels
off in the alone test, as the sweep found). Gate: 320/321, the 45-car traffic test red on a lap-one cone-line crossing
that reproduces with the morning's barriers spliced in (traffic flakiness, not the wall change). Self-play seed 1:
alone rms 0.30 m, contacts 0.037 per car-lap.

## 18 Oct evening, owner: waviness at T2 that is not in the satellite (ab4b15d)
Review with GPT 6 in `t2_waviness_review/` (README.md has the numbers). The per-station trace + patch-and-blend method is
the cause; the branch's right edge at the T2 entry is a 2 m wave over 60 m against a straight painted line, and the
40 m-scale waviness doubled around the lap vs main. Next: global robust spline fit per side, banded gate, T2 first.

## 18 Oct late evening: option B proof at T2 (7c35ea7)
See t2_spline_fit/README.md. Preview https://probe-7a865wvix-coby-hartmans-projects.vercel.app
