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
10. **"Try to place the fence around the infield."** New source from the owner: a CCW onboard, youtube.com/watch?v=_7QwJdGQtaE
    (reference only, frames only), frame at 2:18 saved as owner/owner_lap2_infield_fence_ccw_video.png: the car on the
    pit-out / front-straight area running CCW; "shown at far left from driver's POV is the pit wall, the wall to the right
    of that is the wall between pit lane and the paddock"; his arrow points at a chain-link fence on posts running along the
    infield edge beyond the walls, in front of the big trees. The infield is fenced; the sim has no fence there. This is the
    barrier of note 5 or its kind: a chain-link fence line around the infield, to be traced on the captures (post shadows,
    the thin line) and confirmed on this video.
11. **The fence at T1** (CCW video _7QwJdGQtaE at 22:47, &t=1367; owner/owner_lap2_t1_fence_ccw_video.png): running CCW
    toward T1 (the CW lap's T1 exit / Sunrise seen from the other side), a chain-link fence on posts at the far right by the
    trees (his arrow): the infield fence of note 10 at the T1 end.
12. **Tyre barriers at T2 that the sim does not have** (CCW video at 22:33, &t=1353; owner/owner_lap2_t2_tyre_barriers_ccw_video.png;
    the sim at the same place owner/owner_lap2_t2_outside_sim.png): a long black tyre wall around the OUTSIDE of the T2
    hairpin, behind the outer-loop pavement, with the paddock buildings behind it and cones on the pavement; the sim shows a
    wavy tan ridge there (the lidar / heightfield bump of the tyre wall) and no barrier. The CW barrier ledger has the T2
    outside as "none".
13. **Texture weirdness at T2** (owner/owner_lap2_t2_kerb_apron_mashup.png, local): at the T2 apex on the right, the kerb
    strip (584-604 R), a pale grey band, green patches and the pale apron (553-624 R) overlap in layers along the edge: the
    apron draws over part of the kerb, green ground shows between the layers, and the track edge, the apron edge and the kerb
    do not meet cleanly. "Check texture mash-ups and transitions along the track edges, pit in, pit out. This seems to be a
    common problem." A systematic boundary pass: every place two surfaces meet, with a close still, and a draw order that
    holds everywhere (kerb over apron over shoulder; no green strip beside a kerb).
14. **The awning is BEHIND the control tower, not on its side** (owner/owner_lap2_tower_awning_video.png: the CCW video
    frame with his arrow on the shade roof to the left of the tower; owner/owner_lap2_tower_awning_map.png: Google Maps,
    reference only, "Starter's Tower": the tower's square roof at the pit lane and a second square ribbed roof directly
    behind it, on the paddock side toward Slow Ln). Round 6-7 put the shade-roof annex beside the tower along the lane
    (the west 11 m of the 25 x 19 m capture roof); the capture roof is the tower (south, at the lane) plus the awning (north,
    behind it).
15. **"Make sure the infield layout and buildings are at least vaguely modeled"** (owner/owner_lap2_infield_layout_map.png,
    Google Maps, reference only): the paddock grid (Cal Club Rd, Slow Ln, Ralf St, the paddock lanes), the Fast Lane Racing
    School buildings and the big white garages at the north end, the small buildings in the paddock rows, the tree rows
    between the paddock lanes, the kart track in the north-east corner, the Cal Club buildings. The sim dropped the paddock
    structures for want of a 2026 source; the owner wants them present at a plain level.
16. **The willows around the infield are big**, "especially those coming out by Star Mazda all the way through Sunset": the
    tree rows along the infield's north and west edges (T9 to T11) are tall. The sim's trees there read small.
17. **Off Ramp (T2): a concrete patch close to the inside kerb** (owner/owner_lap2_t2_concrete_patch_map.png, Google Maps,
    his arrow at the hairpin's exit on the inside beside the block line; owner/owner_lap2_t2_concrete_patch_video.png: a
    THIRD onboard source, youtube.com/watch?v=XIxXIvsDz3s at 7:55 (&t=475), CW, Catalyst overlay, "Full Throttle Driving
    Academy": a pale smooth concrete slab between the inside kerb and the dark asphalt at the exit). The round-5 'apron
    right s 553-624' covers that ground as weathered asphalt; the real surface is a concrete patch with its own outline.
18. **The racing surface is cracked, with dark sealant over the cracks**, visible on the satellite (owner/owner_lap2_crack_seal_map.png:
    the Off Ramp / A Section pavement with the crack-seal network) and in the onboard (owner/owner_lap2_crack_seal_video.png,
    the same video, his arrows on the seal lines across the road). "Can the agent model this?" Yes: measured, not textured.
    The crack-seal lines are dark linear features on the 2026 clean captures within the road polygon; detect them (a dark
    ridge filter on the road area, vectorised to polylines with a width), publish them as a `surface_marks` layer, and draw
    them in the kit as dark semi-transparent lines on the road, the way paint is drawn. The captures stay reference only:
    the lines are measurements, like the kerbs and the edges.
19. **The kerb at the top of the hill in Cotton Corners is more aggressive than in the sim** (owner/owner_lap2_cotton_hilltop_kerb_sim.png:
    the right-hand red / white kerb at the crest, flat; owner/owner_lap2_cotton_hilltop_kerb_video.png: the third video
    XIxXIvsDz3s, lap time 0:32, segment 5, around 8:07: a raised concrete kerb on the right with a pale face and worn blue /
    white paint, white K-rail blocks and the "Cal Club" board beyond it). The run 1020-1049 R. "In general, all the kerbs
    should be checked" (note 3 again). The same frame shows white K-rail blocks on the right at the crest that the sim does
    not have, and the sim shows a dark diagonal stripe across the road on the approach (the round-7 paint-over at ~1100?).
20. **A bulge on the drag strip that is not there** (owner/owner_lap2_drag_strip_bulge_sim.png: on the drag-strip leg
    toward T9, the left edge swings outward ahead into a pale bay; owner/owner_lap2_drag_strip_map.png, Google Maps,
    reference only: the drag strip is a straight strip of constant width). Like Sunset (note 6): the stretch from the
    drag-strip rejoin (the 2963-3025 R apron) to the T9 entry is a straight on both sides; the fit follows pale side
    pavement there.
21. **The drag strip narrows toward Star Mazda in the sim** (owner/owner_lap2_drag_strip_narrowing_sim.png: the strip
    pinching ahead with the left-side cone line beside it); it is one uniform width all the way down. Same stretch as note
    20: the straight on both sides must hold one width from the rejoin to the T9 entry (the fit had 11.7 m at 3200 and
    11.9 m at 3380 against 15-16.5 m at 3040-3100).
22. **The kerb on the outside of the Star Mazda entrance is WIDE; too narrow in the sim** (owner/owner_lap2_star_mazda_entry_kerb_sim.png:
    the left kerb on the approach drawn as the 0.9 m strip; owner/owner_lap2_star_mazda_entry_kerb_video.png: the third
    video, segment 12, 99 mph on the drag strip into T9: a wide raised kerb, long blocks, a sloped face, roughly 2-3 m wide).
    "Again, check the kerb height, width, and angle." The kerb WIDTH is per run too, and it is directly measurable on the
    captures (the painted band's width at 0.12 m/px); the kit draws every run at the track's one width (0.9 m).
23. **"I don't think the front straight is this wide"** (owner/owner_lap2_front_straight_sim.png: the sim's straight from
    the T11 exit, ~17 m wide, the K-rail far left; owner/owner_lap2_front_straight_map.png: Google Maps, reference only,
    his two red lines along the racing surface from the T11 exit to the T1 entry: the lower one on the south asphalt
    edge, the UPPER one on the boundary between the dark track and the PALE strip that lies between the track and the
    pit-wall K-rail). The round-4 straight declaration fitted both sides to asphalt-end readings "between the pit-wall
    median and the infield dirt" (16.9 m); the pale strip north of the dark band is not racing surface.
24. **Weird cones blocking nothing before T1** (owner/owner_lap2_t1_cones_sim.png: three cones in a row across the pale
    pavement on the right of the T1 approach). The satellite (owner/owner_lap2_t1_access_road_map.png, Google Maps,
    reference only) shows a paved service road leaving the inside of Sunrise there and running diagonally through the
    infield to the outside of Cotton Corners: "This might be for an emergency vehicle route between Sunrise and Cotton
    Corners (that shouldn't be blocked off for realism's sake)." The sim's cone line 140-160 R (from onboard t006-t008)
    stands at that road's mouth; the road itself is not modelled.

## Lap 3 (22 Oct 2026, the round-8 checkpoint-6 preview ccf00b4, probe-rddrews1f)

25. **The strip left of the start / finish straight** (owner/owner_lap3_108.png, arrow): "The non-paved area on the left side of the
    start/finish straight should look like the dirt that's around the circuit everywhere else. In the sim it looks like
    concrete." Round 8 drew the pale strip between the dark band and the K-rail as two drivable zones in the apron look (the
    orchestrator's brief read the capture's pale tone as pavement): it is DIRT; the zones go, the ground is the dirt of the rest.
26. **The starter's stand at the pit wall** (owner/owner_lap3_109.png, arrows): "The start / finish tower hangs over the pit wall,
    but its legs/structure are behind the pit wall. Also its stairs are floating." The scaffold stand's deck overhangs the wall
    with its legs behind it, and its stair stands in the air: the stand's footprint and the stair's foot from the capture
    (c20_p0420) and the pit video, the stair meeting the ground.
27. **The track edges** (owner/owner_lap3_110..116.png: the edge line waving in and out at seven places, a bulge into the dirt,
    a kerb running away from the asphalt with a gap, the road narrowing and widening on straights): "The track edges seem off in
    enough places that something seems wrong with the pipeline. This feels like a regression on the track edges. When I look
    at the satellite photo of the track, it seems to have a relatively uniform width (except where the 'usable' track
    interfaces with track segments that aren't used, or service roads). Something seems fundamentally wrong with how we are
    approaching Buttonwillow. Is the satellite photo so low contrast that the agent can't tell where the track edges are (gray
    pavement vs. brown dirt)?" Orchestrator's measurement on ccf00b4: width p5 / p50 / p95 = 10.7 / 13.1 / 16.5 m; the
    20-80 m band of the width has p95 1.14 m and max 1.8 m (s 1419), on straights p95 0.72 m; the agent's own round-8 note said
    the dirt and the asphalt are within 18 grey levels on the captures. The edge gate measures smoothness against a 41-station
    median and adjacent steps, not truth against a width prior, so a 20-80 m wander passes it.
