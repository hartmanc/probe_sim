# Sonoma round 14D: the owner's notes (25 Oct 2026, from the decisions page review)

## T11 hairpin outside: a deep tyre wall and a thick white wall, no apron (decisions page Q2)

The owner, 25 Oct 2026, 00:10 PDT, with an onboard frame from https://www.youtube.com/watch?v=7hJizPBNrJ4 (a Porsche GT3 lap of
Sonoma; the frame is `owner/t11_tyre_wall_owner_frame.png`, local, reference only; his annotation "6' wide end" marks the END OF THE TYRE WALL that encapsulates the white wall; the owner's correction of 25 Oct: the white band is NOT 6 ft wide):

> In onboard (and from my experience), there is a deep tire wall at T11 that doesn't seem to appear in the satellite photos.
> Looking at this video, it appears that the tire wall runs from just before station 3648 (so it can encapsulate the white wall
> section), all the way around the outside of T11. There is no apron. I think the white is just a thick wall (maybe a SAFER
> barrier, for the NASCAR guys that come flying into T11 from T10 in their layout).

What this means for the package (rev f399cda140 models plain grey paving beyond the edge line there, "apron"):
- The grey-white band measured 3.1 m wide on the captures (`round14b/hairpin_band.json`) is the top of a thick white wall of
  unmeasured width with a deep, multi-row black tyre wall in front of and around it (the tyre wall's end about 1.8 m / 6 ft wide), not paving. The tyre wall's face is the
  course boundary; the owner's red (steps in ~1.1 m where the band begins at s ~3648, out ~1.5 m where it ends) already treats the
  band as outside the course, so the fitted edge and the junction corners stand (Q4).
- Round 14D: replace the apron with (1) a declared tyre wall, several rows deep, from just before s 3648 around the outside of T11 to
  where the band ends (its extent measured on the 2026 captures and on the onboard frames of 7hJizPBNrJ4 and RAZip6S84CM), its face at
  the owner's red; (2) behind it, the thick white wall (kind concrete, white; thickness and height measured on the frames and captures, not assumed), joined
  to the tyre wall; (3) no apron paving. Sources to cite: this note, the frames, the captures. New onboard source for the T11 area:
  7hJizPBNrJ4 (frames captured in the owner's Chrome tab the way the other onboard sources were; reference only).
- Gates to watch: wall ends (both ends of the tyre wall and the white wall), tyre facings (the tyres face the course, within 0.8 m
  of the wall), barrier gaps (face at or beyond the edge), coverage (an inventory row for the T11 tyre wall and the white wall).

## T9A right-hander: the inside red/white kerb reads short (decisions page Q1 note, 25 Oct 2026, 08:02 PDT)

The owner: "it looks like the inside red/white kerb on the right hander is missing. Onboard RAZip6S84CM at s ~3050 looks to have his
front right tire on the kerb. This extra racing surface would give more room for passing." The package's kerb 24 (right) runs
s 3019-3044 (round 14B); the round-14B judge's row "kerb 24 ends short" was marked FALSE by the judge agent; the owner's reading of
the onboard at s ~3050 says the kerb continues past 3044. Round 14D: measure kerb 24's extent and width on dense onboard frames
(RAZip6S84CM around 100 s, and 7hJizPBNrJ4) and the 2026 captures, extend the strip to the measured end (physics kerb, the owner's
"extra racing surface"), re-check the kerb traversal test at T9A, and re-judge that row. The owner's Q1 position: the line stays as
published; passing under the brakes and side by side through the chicane is normal ("if people can do it, AI drivers can do it"),
which is what the pass-lane fix (ai-passing, merged 24 Oct) is for.
