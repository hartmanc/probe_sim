# Mid-Ohio edge review — round 2

The owner requested the red race edge on the inside, asphalt-facing boundary of each kerb. This supersedes the original outer-kerb convention for Mid-Ohio. `spline.kerb_edge="inner"` selects the measured inner band limit for automatic red/white kerbs, declared kerbs, yellow kerbs and kerb-band evidence; ordinary painted-line detection and other tracks retain their earlier behavior. Geometry was refitted from the original cached evidence. No hand-edited package geometry or gate exceptions.

Candidate: `tools/track/out/mid_ohio_r2/`. Outline: `edges_r2/`. Drawing page: `review_r2/edges.html`, served separately on port 5198. Round-1 review files remain untouched on port 5197, including their existing browser storage namespace. No user browser profile was accessed. Hashes of the original review page, manifest and window metadata were checked unchanged.

Independent validation: 15 focused tests passed (`test_yellow_kerb.py`, `test_profile_gap.py`, `test_pit_merge.py`); edge/profile gates passed. Final length 3597.185 m is 1.011% below nominal 3633.934 m; this remains a failing geometry gate. T4's survey predates its reconstruction. No ghosts, scenery, app wiring, package publication or merge performed. Full baseline reproductions remain required before merge.

Visual checks: T1 red/white kerb at close_s0320 matches the owner's boundary example; T2 yellow kerb close_s1060 and T4 red/white close_s1960 also follow the asphalt-facing boundary. Edge width still varies at junctions; advisory exit-width findings at T1, Carousel and T13 remain for review. Reports: `geometry_report_r2.json`, `stage_geometry_r2.json`.

Future kerb rendering must place the kerb outside this revised road boundary; it must not reuse an assumption that the road edge includes the entire kerb. The current round changes geometry only.

## Carry-over of original review marks

The owner requested existing round-one marks on this page as well. The updated
page attempts to read only the original review's browser-storage key through
`review_r1/edge_marks_to_5198_v2.html`, a read-only bridge on port 5197. Original
HTML, images and marks remain unchanged. Points and edit handles are mapped
through each window's north-up ENU center, crop extent and pixel scale to the
corresponding round-two window. Existing round-two marks are retained. A saved
import ledger prevents duplicate imports and respects later deletions.

Actual marks stay in the owner's browser; the transfer occurs on the next load
of round two in that browser. Both localhost and 127.0.0.1 source origins are
supported, and messages are restricted to the explicit local review origins.
The original and revised storage keys were checked unchanged.

Rebuild the drawing page with the existing flags plus:

```
--import-review tools/track/compare/mid_ohio/review_r1
--source-windows tools/track/compare/mid_ohio/edges_r1/windows.json
--target-windows tools/track/compare/mid_ohio/edges_r2/windows.json
```

Validation: four focused transfer tests pass. A temporary browser profile with
sample original and new marks verified automatic cross-port import, geographic
alignment, retention of new marks, duplicate prevention, respect for deletions,
and an unchanged original browser store. No owner browser profile was accessed.

### Transfer recovery after the owner's missing-marks report

The owner still saw saved strokes on 5197 and no strokes on 5198. The original
test used a single hostname and did not cover a blocked or partitioned embedded
bridge. The exact cause in the owner's browser was not observable from here.

The revised page provides a sticky **Bring original marks** button. It reads
first-party source storage in a user-opened window, trying both local addresses
without changing originals. It reports an actual import count. An explicit
transfer can restore missing marks despite a previous import ledger; automatic
reloads still respect deletions and existing round-two marks are merged.
**Load original marks file** accepts the original page's Download marks JSON
as a browser-independent fallback. A five-second timeout replaces silent
waiting with a recovery instruction. The older bridge file is retained unchanged.

Browser validation now also blocks the iframe request and stores originals at
localhost while the target uses 127.0.0.1. Direct transfer, alternate-address
retry, geographic registration, preservation of existing marks, duplicate
prevention, explicit restoration and an unchanged source store all passed.
The JSON file fallback was checked through the actual file input as well.
