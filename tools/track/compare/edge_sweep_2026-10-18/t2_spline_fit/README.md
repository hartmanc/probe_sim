# T2 spline fit (option B), 18 Oct 2026 late evening, commit 7c35ea7
Owner chose B (global robust spline fit) after the GPT 6 review in ../t2_waviness_review/. Proof on T2, stations 240-700.

    uv run --python 3.12 --with numpy,scipy,pillow,matplotlib python -I tools/track/fit_edges_spline.py \
        --lo 240 --hi 700 --lam 30 --init-stiff 5 --write
    python3 -I tools/track/fix_edge_line_run.py --side -1 --s0 250 --s1 544 --write

Data: 8 new clean captures (tools/track/compare/satellite_clean/, Google Maps with all UI hidden by page CSS and labels
off, registered by tools/track/register_clean.py: same scale as z20, within one pixel of the old captures) + the z20
captures; ONE common shift (-0.3, 0.0) m for all: the captures agree to a pixel, the per-capture registrations (up to
0.6 m apart) were noise. Feature table in the script (Andretti apex inside: asphalt end, not the thin line).

| | before (ab4b15d) | after |
|---|---|---|
| left local waviness, rolling 100 m rms max / peak (m) | 0.173 / 0.506 | 0.065 / 0.138 |
| right | 0.192 / 0.502 | 0.068 / 0.136 |
| largest edge kink (deg/station) left / right | 5.47 / 3.07 | 1.72 / 1.11 (both at the join at 240) |
| observations / stations covered left, right | | 1547 / 84 %, 1773 / 92 % |
| residual within 0.25 m left / right | | 87 % / 94 % |

The residual left in the waviness number is real geometry (pit-out gore 290-320, T2 exit narrowing 545-580), not waves.
Gate: build ok; 320/321, ai_behaviour full field lap 1 contacts 0.104 vs 0.1 (baseline note 0.083). Self-play contacts
seed 1 0.031 -> 0.057, seed 2 0.019 -> 0.038, but T2-zone contacts unchanged (2/2, 0/0); extras at T3/T6/T9/T10.
Files: t2_before_after.jpg (red before, blue after on clean captures), fit_final.png, hood_T2_after.jpg.
