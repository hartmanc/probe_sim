# Whole-lap spline fit, 18-19 Oct 2026 night, commit ee26733
Owner after T2: "T2 looks good. Check the rest of the track and implement as needed".

    uv run --python 3.12 --with numpy,scipy,pillow,matplotlib python -I tools/track/fit_edges_spline.py \
        --lo 700 --hi 3800 --lam 30 --init-stiff 5 --write
    uv run --python 3.12 --with numpy,scipy,pillow python -I tools/track/add_paved_aprons.py --write   # + T9 teal apron

Data: 42 more clean captures every 75 m (satellite_clean/c20_b*), all within one pixel of the z20 captures
(register_clean.py, scale fixed). Fitter changes: kerb bands bridge block gaps once red is seen; dark kerb blocks pass
the inner-asphalt test; FEATURES 'keep' (Corkscrew 2425-2535 both sides, T11 right 3228-3425, front straight left
3330-3633, pit-out merge left 73-240): no observations, current edge followed within 0.15 m; boundary snapping along
the station normal with the edge width and height interpolated between stations, rows ramped, minimum 0.3 m width.
Reviewed every stretch moving > 0.6 m on the clean captures (rev1c/rev2/rev3.jpg). Real corrections: Rahal left
(edge was 1.6 m out on the apron), T9 left (teal apron was inside the edge), T6 approach right (1.4 m short of the
line), T3 / T4-T5 kerbs, T10 exit left, front straight right (white line; shoulder zone beyond).

| | before (7c35ea7) | after |
|---|---|---|
| edge_gate rms vs 41-st median, left / right | 0.104 / 0.082 m | 0.074 / 0.061 m |
| exit-overshoot flags | T1, T4, Rahal, T7, T8, Rainey | T1 (pit-out merge), T7, T8 |
| fit residuals within 0.25 m (fitted part) | | 92 % / 85 % |

Gate: build ok, line ok; 319/321. Red: ai_behaviour full field (defending vs clearly faster 2, needs 0), ai_race
45 cars (one car 0.638 of pace, floor 0.65). Self-play contacts per car-lap seed 1 / 2: 0.031 / 0.019 before tonight,
0.057 / 0.066 now, spread over the lap: the AI lane model is fitted to the old (too wide) road; retune pending.
