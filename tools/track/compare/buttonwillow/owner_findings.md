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
