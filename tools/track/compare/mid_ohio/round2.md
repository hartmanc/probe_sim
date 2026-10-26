# Mid-Ohio edge review — round 2

The owner requested the red race edge on the inside, asphalt-facing boundary of each kerb. This supersedes the original outer-kerb convention for Mid-Ohio. `spline.kerb_edge="inner"` selects the measured inner band limit for automatic red/white kerbs, declared kerbs, yellow kerbs and kerb-band evidence; ordinary painted-line detection and other tracks retain their earlier behavior. Geometry was refitted from the original cached evidence. No hand-edited package geometry or gate exceptions.

Candidate: `tools/track/out/mid_ohio_r2/`. Outline: `edges_r2/`. Drawing page: `review_r2/edges.html`, served separately on port 5198. Round-1 review files remain untouched on port 5197, including their existing browser storage namespace. No user browser profile was accessed. Hashes of the original review page, manifest and window metadata were checked unchanged.

Independent validation: 15 focused tests passed (`test_yellow_kerb.py`, `test_profile_gap.py`, `test_pit_merge.py`); edge/profile gates passed. Final length 3597.185 m is 1.011% below nominal 3633.934 m; this remains a failing geometry gate. T4's survey predates its reconstruction. No ghosts, scenery, app wiring, package publication or merge performed. Full baseline reproductions remain required before merge.

Visual checks: T1 red/white kerb at close_s0320 matches the owner's boundary example; T2 yellow kerb close_s1060 and T4 red/white close_s1960 also follow the asphalt-facing boundary. Edge width still varies at junctions; advisory exit-width findings at T1, Carousel and T13 remain for review. Reports: `geometry_report_r2.json`, `stage_geometry_r2.json`.

Future kerb rendering must place the kerb outside this revised road boundary; it must not reuse an assumption that the road edge includes the entire kerb. The current round changes geometry only.
