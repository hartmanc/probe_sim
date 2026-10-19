# Onboard video vs sim, corner by corner (17 Oct 2026)

Source: one clean sunny lap from GL030045 (video 790–913 s, driver B's stint), pit
exit from GL020045 2333–2375 s. Sheets in this folder: onboard frame left, sim
driver camera right at the same s and heading.

| Place | Onboard t (s) | Mismatch found | Status |
|---|---|---|---|
| Front straight | 658–665 | S/F bridge banners read MISSION · WeatherTech · MISSION · PORSCHE | fixed |
| T1 | 796 | PORSCHE billboard on the right bank | fixed |
| T3 | 816–820 | gabled "kinetic" hangar ahead-left; the T3–T4 bridge is the TIRE RACK arch | fixed |
| T4 | 825 | covered grandstand on the left hill | not added |
| T6 | 731, 859 | paved runoff on the outside; PORSCHE banner on the wall | fixed (paved zone s 1934–2029) |
| Rahal | 865 | twin white lattice towers with cables across the track | fixed |
| T7 | 870 | WeatherTech banner on the outside fence | fixed |
| After T8A | 875–877 | WeatherTech truss bridge with "Auto. Home. Pet. Find Your Fit." banner | fixed |
| T9 Rainey | 883 | paved runoff on the outside | fixed (paved zone s 2699–2804) |
| T10 | 890 | paved runoff on the outside with a green strip | fixed (paved zone s 2937–3032) |
| T11 | 899 | ad boards along the outside wall | fixed |
| T2, T5, kerbs, concrete walls, catch fences, pit exit, flag stand, bleachers | | match | – |

Not resolvable from proxy-quality footage: runoff at T1–T5 and T11 (left as
dirt), barrier distances, anything in the right third of the frame (the
inflatable alien blocks it). Only GL030045 syncs to the logger with the stored
offset; the other chapter files need a re-derived offset. Paved zones live in
scenery.json `paved_zones` and drive like the pit lane (grip 1.0, paved flag).
