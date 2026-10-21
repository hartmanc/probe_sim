# Buttonwillow: the owner's findings

## Lap 1 (20 Oct 2026, ~22:40 PDT): preview https://probe-jb5yq8p5e-coby-hartmans-projects.vercel.app, branch b695c22, rev d7b31ce2af

Driven after the T2 and T4 mark-ups (owner/t2_edges.json, owner/t4_edges.json: those two stretches were known wrong on this
build). Notes as given, before bed:

1. **Kerbs: "a lot of weird, disjointed kerbs."** The package draws each block line as 10 m strips with their own lateral
   offset (`off` per strip, steps of up to 0.8 m between neighbours, e.g. 1282-1291 R at -1.70 m then 1292-1301 R at -0.90 m),
   so a run reads as broken pieces. A run must be one continuous line along its block line.
2. **"Some screwed up textures."** Place not given. Candidates: the worn `apron` surfaces, the pit-entry strip (judge r4 row:
   near-black between its lines), the painted-over NAIP patches, the crossovers in the asphalt tone, the T2 inside patch.
   To find on a low camera pass and fix.
3. **Star Mazda (T9): "the kerb is not aggressive enough; it's a big kerb."** The circuit's block lines are flat paint, but
   the T9 kerb is a raised one. Check the onboard (t112-t116, 1:48-1:56) and give that run a raised profile measured by the
   HEIGHTS.md method; the kerb profile must be per run, not per track.

## Lap 2 (21 Oct 2026, morning): preview https://probe-b6rag1eds-coby-hartmans-projects.vercel.app, branch 21fbd2f, rev b7a674a6da

1. **Star Mazda (T9), the OUTSIDE kerb: "should be more aggressive."** Screenshot from off track on the exit's outside
   (owner/owner_lap2_star_mazda_outside_kerb.png, local): the left exit run 3470-3518 L, drawn flat. Round 5 raised only the
   apex run (right 3400-3451, 6 cm from t114) and left the exit run flat because t116 showed 1-2 px. The owner has driven
   the real one: the exit kerb is a raised, aggressive kerb. Per-run profile for 3470-3518 L.
2. **The Esses (T10 complex) kerbs too** (owner/owner_lap2_esses_kerbs.png, local: the left kerb at the first Esses bend
   drawn flat): the runs 3691-3760 L, 3794-3810 R, 3845-3876 L, 3894-3935 R, 3972-4024 L are raised kerbs.
3. **The rule: "I think all of the kerb heights should be checked. Most Buttonwillow kerbs are not just flat extensions of
   the pavement."** Round 5's profile pass read 1-2 px on the distant frames and called every run but the T9 apex flat; that
   method under-reads. A whole-lap per-run height pass with better evidence (the 2021 lidar cross-profiles, the close onboard
   frames) and the owner's statement as the default where the evidence is ambiguous: raised unless a source shows flat.
4. **Texture fault on a raised kerb** (owner/owner_lap2_kerb_wedges.png, local): a curved red / white / blue kerb with tan
   triangular wedges between the painted blocks along its outer edge, the ground showing through. The only raised run on
   this build is the T9 apex (3400-3451 R, 6 cm), so this is the raised-kerb mesh on a curve: gaps between segments where
   the per-station offset or the curvature changes, or the back-slope quads not sharing vertices. Every run raised in round
   8 will show it unless the mesh is made watertight.
5. **A barrier / fence at a dark line in the infield** (owner/owner_lap2_infield_barrier_line.png, local: off track on
   dirt, a dark line running across the infield ahead with a tree beyond): "I'm pretty sure there's a barrier / fence here
   at this dark line; i.e., it shouldn't be possible for a car to slide off the track and into the infield." Place not
   given yet (corner to come). The round-2 barrier ledger called every infield dark line "tyre tracks" or "none" except the
   ones re-read later (the T11-approach tyre line at 4150-4260 L was one such miss, corrected in round 4): the ledger's
   "none" rows need a second read for dark linear features within ~40 m of the track on the infield side.
6. **Sunset (the straight from the Zorro's Corners mouth to the T11 sweep) has a bulge in the sim; the real road is straight
   on both sides** (owner/owner_lap2_sunset_straight_map.png: his two red lines along both edges on Google Maps, from just
   past the Zorro's Corners mouth to the West Pit In/Out junction; owner/owner_lap2_sunset_bulge_sim.png: the right edge
   bulging outward ahead, arrowed, from ~s 4200 looking toward T11). The fit's width report had 4135-4161 at 17.2 m (the
   Zorros mouth fillet) and 4241-4258 at 16.9 m; the right edge wanders out at both. Stage 1: declare Sunset a straight on
   both sides (config `straights`, as the front straight 4525..180), the mouth readings exempt.
7. **Texture issue at pit-in** (owner/owner_lap2_pit_in_texture.png, local): the gore between the track and the pit-in
   lane, ahead-left of the car approaching T11, is covered in tan / straw blotches on the asphalt, with the white lane line
   beside them. That is the round-7 paint-over of the NAIP hatch (on='any', 441 px) turned into ground-coloured patches, or
   the ground texture showing through the gore. The video (pit_ucm t1231000) shows a plain paved gore with the painted
   hatch: it must read as asphalt.
8. **Another bulge, on the LEFT side of Sunset** (owner/owner_lap2_sunset_left_bulge.png, local): the left edge swings
   outward ahead into a tan bay. Same stretch as note 6, the other side: the straight declaration covers both sides.
9. **White lines on the pit-in lane that are not there** (owner/owner_lap2_pit_in_box_lines.png, local): transverse white
   lines across the pit-in lane past the split. "These look like pit spots that should appear in pit lane itself, not pit
   in or pit out." The pit-box paint is drawn over the whole pit-lane part (pit-in, the lane, pit-out); the real boxes are
   along the pit wall only (the pit video: the lane between the two K-rails), and the pit-in and pit-out roads carry none.
