#!/bin/sh
# Mid-Ohio round 3: the owner checkpoint page, changed region only (windows + captions + frames.json, then the drawing
# page). Window ids and frames are fixed by the published page (his strokes are saved per window id). Run from the
# worktree root. PNGs stay local (ignored); the JSON / HTML are tracked.
set -e
uv run -q --python 3.12 --with numpy,scipy,pillow python -I tools/track/compare/mid_ohio/r3/review_windows.py
uv run -q --python 3.12 python -I tools/track/compare/edge_draw_page.py \
  --src tools/track/compare/mid_ohio/owner_review_r3/src --out tools/track/compare/mid_ohio/owner_review_r3/page \
  --title "Mid-Ohio Edge Strokes, Round 3" --intro "$(cat tools/track/compare/mid_ohio/r3/page_intro.html)"
cp tools/track/compare/mid_ohio/owner_review_r3/src/frames.json tools/track/compare/mid_ohio/owner_review_r3/page/frames.json
