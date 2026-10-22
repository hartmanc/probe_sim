You are judging seven places of a racing-sim circuit against the owner's own screenshots of the sim and the 2026 satellite
captures, image by image. Circuit: Sonoma Raceway (sonoma), the 24 Hours of Lemons layout (clockwise, 4098.5 m). This is
round 11 of the scenery, which answered the owner's notes 63-69 from his round-10 lap; everything else is unchanged and already
judged. Judge ONLY what the attached images show.

The owner's notes (his words, from his round-10 lap) and what round 11 did:
- Note 63, the T7 complex: the unused part of the T7 road showed the wrong texture (pale concrete) and a kerb ran across the
  mouth where cones stand. Round 11: that closed part of the road is now the track's asphalt; the T7a kerb starts at the
  O'Reilly island's nose (station 2259, was 2208) so no kerb crosses the mouth; the four delineator posts stay.
- Note 64 and note 69, the Carousel-to-T7 run-up (stations 1680-2060): "I don't think this section going to T7 is wavy like
  this"; the edges waved in the sim and are straight on the satellite. Round 11 fitted the drag strip and the T7 road as two
  straight legs meeting at station 1901 (the captures show them 11 degrees apart), each with one width (drag strip 18.30 m,
  edge rms 0.009 / 0.020 m, was 0.06 m; T7 road left edge rms 0.014 m, was 0.47 m with a chord 1-3 m inside the asphalt
  end). The real asphalt end bows up to 0.9 m inside the straight T7 road line at 1938-1995; it was kept straight per the owner.
- Note 65, T10: a sunken tyre wall and tan grass on the verge. Round 11: the app's terrain mesh had buried the T10-T11
  boarded wall by up to 1.06 m and the T11 walls by up to 0.99 m; the mesh under every barrier line is now lowered to the
  barrier's base (physics unchanged). The verge is green grass on the onboard (t104 / t106 / t110), so grass zones were added
  to the season tint (verge about (0.45, 0.55, 0.31)). There is no sign on that verge in the footage.
- Note 66, the infield building looked too low. Round 11: no change; the building in the owner's view is the pit garages,
  lidar p90 7.0 m against the ridge at 7.0 m; the shed, long shed and fuel canopy agree with the lidar; the tall blobs beside
  the long shed are trees.
- Note 67, a wall missing along a dark line, with a bare tyre-wall head: "As a general rule, the wall transition shown in the
  sim generally don't exist because they are extremely dangerous." Round 11: the dark line measures as a wall (97 % picked,
  rms 0.65 m; t112 / t114 show a pale wall and catch fence): placed as 1.1 m concrete with a 3.5 m fence, ending on the
  T11-approach tyre head that was bare at station 3398, 0.6 m from the edge. The wall-ends gate now checks tyre runs too.
- Note 68, before T11: a wrong texture on the left. Round 11: the track's left shoulder rose through the pit-in lane (stations
  3522-3635); the shoulder is cut there (same cause as the round-10 pit-out).

The images, in the order attached (the file name is given; use it as the "image" column). The *_after.jpg files are the sim's
hood camera at the place in the name after round 11; the owner_*.png files are the owner's own screenshots of the ROUND-10 sim
(before the fix) with his notes, so the "after" images should show the fix at the same place:
1. owner_69_carousel_to_T7_satellite.png


Ignore the sim car's hood and figures, lighting, sky, clouds, the camera height, other cars, and the owner's cursor or HUD. The
station mapping can be off by up to 30 m.

For EACH note give a verdict line "N<nn>: FIXED / PARTLY / NOT FIXED: <why, citing the image>" (N63, N64/69 together, N65,
N66, N67, N68), then for EVERY image list every remaining difference as rows of this table (one row per object, nothing else,
no prose):

| image | s (m) | side (left/right/ahead) | kind | owner or footage shows | sim shows | verdict |

kind is one of: wall, fence, kerb, tyre_wall, tyre_stack, stand, station, bridge, building, mast, cone_line, boards, paint,
runoff, road_edge, surface. verdict is one of: MISSING, EXTRA, WRONG_HEIGHT, WRONG_TYPE, WRONG_COLOUR, WRONG_POSITION (more than
about 3 m off laterally or 15 m along), FLOATING (does not meet the ground or its supports), SUNKEN (buried in the ground),
WAVY (an edge or line that should be straight is not), OK_DIFFERENT (different but acceptable, say why). Heights: estimate with
known sizes (Jersey barrier 0.81 m, catch-fence posts 3-4 m, cone 0.7 m, a car 1.4 m) and give both numbers.

Then one line per image: "image <name>: <n> rows, worst: <the single most wrong thing>", and one line with the checklist
answers for that image: "image <name>: C1 ok, C2 n/a, ..., C21 FINDING" (checklist below). Finish with the five worst rows of
this batch, worst first, and then two direct answers, one line each: (Q1) do the Carousel-to-T7 edges now read as two straight
legs with no waves, in the run-up images? (Q2) which object in this batch would the owner notice first on his next lap?

Checklist (answer each line for EVERY image as `C<n>: ok`, `C<n>: n/a` (nothing of that kind in the image) or `C<n>: FINDING`
with a table row above):

| # | check (answer per image) |
|---|---|
| C1 | Wall ends: does any barrier run end with an open face or a bare end toward oncoming travel, with no cap, cushion or impact block? |
| C2 | Joins: where two runs meet, is it one continuous line (no step toward the track, no shingled overlap, no gap, no two runs side by side)? |
| C3 | Facings: does every tyre run beside a wall stand against its track face (or meet it end to end), black or white as the footage, stacked to its height? |
| C4 | Run extents: does each wall, tyre wall and fence start and end where the footage shows it (not 20-30 m early or late)? |
| C5 | Heights: do walls, fences and boards stand as tall as the footage, enclosing where the real place encloses? |
| C6 | Bands: is there a light or dark band in the ground texture where the footage shows a barrier, or a barrier where it shows paint? |
| C7 | Containment: is any paved area (drag strip, closed road, paddock) open to the track where the footage shows a wall, tyres or cones? |
| C8 | Cones: colour, size and spacing as the footage, standing on the painted line, none inside a lane or a blend? |
| C9 | Pit lane: open end to end, walls on the sides the footage shows, no rule boards in it? |
| C10 | Blends: does a lane taper into the track as one surface (no seam, no lighter strip, no raised shoulder through it)? |
| C11 | Kerbs: a kerb exactly where the clean captures show the block pattern, none across a mouth or where cones stand, colours as the footage? |
| C12 | Stands: does each stand start, end and rise where the footage shows it, nothing floating or buried? |
| C13 | Huts: is each corner station visible, roofed, raised, open-fronted, on the side of the wall the footage shows? |
| C14 | Boards: does each board run start and end at the footage's stations, names typed in the footage's colours? |
| C15 | Logos: a painted ground logo drawn as typed text in its colours, no smear in the ortho? |
| C16 | Movable barriers: a barrier the footage shows but the capture does not, placed and flagged movable? |
| C17 | Surface tone: two road textures, seams or coloured smears between the track, pit lane, runoff and closed roads? |
| C18 | Closed roads: do unused roads look like race track (its surface, painted edges), coned off where the footage shows cones? |
| C19 | Supports: does every bridge, deck and raised structure meet the ground? |
| C20 | Buildings and towers: shape, roof, colours and height as the most recent footage, the tall landmarks present? |
| C21 | Ground: a sunken barrier, a wall buried in the terrain, a tan patch where the footage has green grass, or a blotch baked into the ground where the footage has an object? |
