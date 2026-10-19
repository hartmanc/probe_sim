# T2 entry waviness review (18 Oct 2026, evening)

Owner: "I am seeing waviness that is not in the satellite photos ... apparent right at T2. Review the approach with GPT 6."
Judge: `codex exec -m gpt-6-astra -s read-only -c model_reasoning_effort=medium` with the four images attached
(`gpt6_brief.md` in, `gpt6_review.md` out). Overlays: `overlay_t2.py` (yellow main, cyan 4c654a4 paint rebuild, red branch
head ab4b15d, dots = sweep_final.npz detections). Stats: `wave_stats.py <dir with track_<ref>.json>`.

## Numbers (branch head ab4b15d unless stated)
- Right half-width at the T2 entry: 6.5 (380) -> 6.9 (390) -> 5.0 (430) -> 6.8 (450) m; the sweep's own white-line detections
  say the line is 1.4 m INSIDE the current edge at 390 and 0.5 m OUTSIDE it at 430-435: a 2 m wave over 60 m against a
  smooth painted line. Cause: the 'T2_entry_right' stretch (380-450, fix_edges_paint.py) blended in over 26 stations from a
  neighbour (346-379, whole-lap rebuild) that sits 0.6-1.2 m out on the paved apron; its own trace is 0.5 m inside the line
  at 430-440 (kerb start; Google Maps label and route arrows lie on the track there and are not masked).
- Left edge: 5.3/4.2/3.8/3.6 degree kinks at 381-384 (capture hole 380-385 where the NAIP edge was kept); detection kind
  flips every few stations at 305-375 (line / non-asphalt / shadow, +-2 m).
- Local quadratic residual, +-20 station window (curvature-preserving waviness at 40 m scale), stations 300-470:
  centre 0.011 m rms (main 0.007); left 0.059 rms / 0.22 max (main 0.032 / 0.08); right 0.122 rms / 0.44 max (main 0.031 / 0.09).
  Whole lap: left 0.083 (main 0.043), right 0.079 (main 0.043). The centreline is not the problem; the branch doubled the
  40 m-scale edge waviness around the lap and quadrupled it on the right at T2.
- Sweep statistics, whole lap, left: 622 stations with no capture (64 holes, median 6 st), 2393 single-capture, 545 with 2+;
  660 kind flips between neighbours; 476 detection jumps > 0.5 m; |dev| > 0.5 m at 1151 of 2938. Right similar.
- Neighbouring captures' registrations differ by 0.3 m along the normal here (1.3 m at z20_s3400, excluded).
- Gaussian sigma 5 stations keeps 58 % of a 30 m wave and 87 % of a 60 m wave (GPT 6); edge_gate.py had no threshold and
  measured only the residual about a 41-station median plus the per-station step (0.10 m/station accepted = 5.7 degrees).

## Verdict
Per-station detection + short smoothing + local patches with blends into unverified neighbours = 20-80 m waves of
0.3-1 m that the top-down checks cannot see (2-3 px) and the hood camera sees end-on. Fix: a global robust spline fit
per side (periodic cubic B-spline, 15-25 m knots, curvature-variation penalty, Huber 0.2-0.3 m, only trusted
line/kerb observations, map graphics masked, registration frozen first), banded waviness gate (rolling 100 m window,
0.10 m rms / 0.25 m peak in the 15-120 m bands on gentle sections; 0.5 deg/m kink), T2 300-480 first.
