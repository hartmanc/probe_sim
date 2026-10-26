#!/bin/sh
# Mid-Ohio round 3: the owner's round-2 windows (owner_edges.py --by-stroke --vector-origin continuous on
# tools/track/out/mid_ohio_r2, frames from compare/mid_ohio/owner_review_r2/frames.json) merged into merged.json with the
# overlap dispositions of compare/mid_ohio/round3.md ("Overlap dispositions"); each --drop leaves one window's red out over
# the stations where two windows disagree by more than 0.3 m and the paint / kerb evidence picks the other. Run from the
# worktree root.
exec uv run -q --python 3.12 --with numpy,scipy python -I tools/track/compare/owner_merge.py \
  --dir tools/track/tracks/mid_ohio/owner/r2 --pkg tools/track/out/mid_ohio_r2 \
  --out tools/track/tracks/mid_ohio/owner/r2/merged.json \
  --drop w_s0250:right:186:243 --drop w_s0125:left:189:200 --drop w_s0250:left:274:295 \
  --drop w_s0375:left:311:323 --drop w_s0375:right:339:340 --drop w_s0500:right:427:475 \
  --drop w_s0000:left:3519:3538 --drop w_s0000:right:3519:3524 --drop w_s3500:right:3431:3443
