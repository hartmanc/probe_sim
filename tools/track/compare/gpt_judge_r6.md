# GPT judge round 6: rebuilt track (branch edges-from-paint-wip, d5a333d) (18 Oct 2026)

Judge: OpenAI `codex exec`, model **gpt-6-astra** (confirmed in logs), read-only sandbox, images attached with `-i`,
prompts unchanged: `judge/prompt_corners.txt`, `judge/prompt_lap.txt`. Judge-only pass: no fixes, single run.

Sim renders: `youtube_sim_r6/` (14 hood-camera places, same stations/lateral offsets as round 5; 21 top-down tiles
at the `satellite/tiles.json` centres, which equal the main-branch centreline at the tile stations used in round 5),
canvas 1900x957, built with `render_post.sh r6 r6`. Onboard frames and Google captures reused unchanged.
Raw output: `judge/out_corners.md`, `judge/out_lap.md` (round 5 raw output moved to `judge/iter5/`).

| | Round 5 (main) | Round 6 (edges-from-paint-wip) |
|---|---|---|
| Places passing both views | 3 / 14 (T5, Rahal, T7) | 3 / 14 (T5, T6, Rahal) |
| Onboard MATCH / PARTIAL / MISMATCH | 0 / 14 / 0 | 1 / 8 / 5 |
| Top-down MATCH / PARTIAL / MISMATCH (14 places) | 2 / 12 / 0 | 2 / 12 / 0 |
| Lap tiles MATCH / PARTIAL / MISMATCH | 4 / 17 / 0 | 2 / 18 / 1 |
| Whole-lap top-down | YES (layout level) | YES (layout level), detail not passed |

## Round 6 per place (verbatim)

**Overall verdict: PARTIAL — not yet an acceptance pass.** The scenery captures the broad layout and several recognizable landmarks, but repeated differences in kerbs, green paint, runoff and barrier placement remain substantial. The strongest matches are T5, T6 and Rahal Straight.

I have allowed for the camera height and approximate station matching. Small road-to-aerial offsets do not cause failures; painted features visible only in the older ground photograph carry less weight.

| Place | Onboard verdict | Top-down verdict | Pass | Notes |
|---|---|---|---|---|
| **Front straight** | **PARTIAL.** The overhead sign, pit enclosure and right-side spectator area are recognizable. The sim’s prominent cylindrical towers and sparse pit-side structures differ substantially from the onboard scene. | **PARTIAL.** The main pit building and grandstand footprints broadly agree. The paddock is conspicuously empty, and several surrounding structures are simplified or absent. | **NO** | Improve the permanent pit and spectator structures first; event vehicles and crowds are secondary. Check the towers’ shapes and placement. |
| **T1** | **PARTIAL.** The left pit-exit boundary and right hillside are present, but the broad green strip beside the real pit-exit wall becomes a thin, distant strip in the sim. The Porsche board and hillside spectator structures also differ in scale and placement. | **PARTIAL.** The barrier corridor and surrounding roads broadly correspond. The green strip is much less substantial, and nearby building footprints are simplified. | **NO** | Restore the width and continuity of the pit-exit paint, then improve the right-side board and spectator area. |
| **T2 Andretti** | **PARTIAL.** The outer green strip and perimeter barrier establish the correct setting. The real inside apex has a broad green treatment with a white boundary; the sim instead emphasizes an exposed red/white kerb beside a differently shaped green patch. | **PARTIAL.** The hairpin enclosure and island are recognizable. The sim has conspicuous, segmented green strips and kerb treatments that do not closely follow the satellite’s visible painted extents. | **NO** | Reconcile both apex treatments and the outer green runoff as continuous, deliberately shaped surfaces. |
| **T3** | **MISMATCH.** The real corner is framed by advertising barriers, nearby buildings and inside fencing with blue boards. The sim substitutes a largely bare embankment and distant generic buildings, with an exposed inside kerb and little of the close furniture. | **PARTIAL.** The pond, bridge and surrounding road arrangement correspond. The inside service area lacks much of the visible built detail, and the green/kerb coverage differs. | **NO** | Restore the close buildings, inside fence and boards, and outside advertising barrier; these dominate recognition here. |
| **T4** | **MISMATCH.** The prominent red Mission wall and boards immediately inside the real corner are largely absent from the corresponding sim view. Across the corner, the spectator area is replaced visually by a long, plain structure. | **PARTIAL.** The pond-side corner, outside barrier and grandstand arrangement broadly agree. The surrounding structures are simplified, and the rendered edge treatment does not closely reproduce the visible reference. | **NO** | Prioritize the inside Mission furniture and the outside grandstand’s appearance and placement. |
| **T5** | **MATCH.** The inside red/white kerb, dirt infield, outside dark barrier and tree-lined background reasonably agree. The sim’s trees are more isolated and regular than the reference’s fuller canopy. | **PARTIAL.** Runoff, perimeter barrier and service-road placement correspond well. Kerb/green-strip extents differ slightly, and vegetation density is approximate. | **YES** | Minor refinement: kerb endpoints and a less uniform outside tree line. |
| **T6** | **PARTIAL.** The inside kerb, uphill exit, left bank and red/black outside panels are recognizable. The sim’s advertising panels are smaller and more separated, while its fencing is more visually prominent. | **MATCH.** The bridge, runoff wedge, outside barrier and wooded surroundings broadly match. Small edge and vegetation differences do not undermine the setting. | **YES** | Refine the size and continuity of the advertising panels and the inside kerb’s extent. |
| **Rahal straight** | **PARTIAL.** The bridge and fenced uphill corridor reasonably match. The bridge lacks its visible sign treatment, and the real right-side barrier has a stronger dark lower band. | **MATCH.** The narrow track corridor, left access paths and dense right-side woodland agree reasonably well. Individual tree placements differ without changing the character. | **YES** | Add the bridge graphic and improve the right-side barrier finish. |
| **T7** | **PARTIAL.** The right kerb, green verge and catch fence are convincing. The sim adds a dominant nearby WeatherTech board absent from this reference view, and the left-side trees and furniture are arranged differently. | **PARTIAL.** The corridor and woodland boundary broadly agree. The transverse overhead structure appears substantially farther down the tile in the sim, and verge-paint extents differ. | **NO** | Verify the overhead structure’s station and the large sign placement. The top-down discrepancy cannot be explained by onboard station matching. |
| **T8 Corkscrew entry** | **MISMATCH.** The real inside apex has a distinct yellow raised kerb behind the red/white kerb and a shaped green apron; the sim lacks the visible yellow element and uses a different apron treatment. The enclosing trees, barriers and outside boards also differ substantially. | **PARTIAL.** The runoff enclosure and wooded setting are recognizable. The detailed kerb and green-apron shapes through the transition do not closely reproduce the reference. | **NO** | Restore the yellow sausage, apex paint shape and outside board/barrier arrangement. |
| **T8A** | **MISMATCH.** The real inside has a broad, white-outlined green apron and nearby purple/white boards. The sim’s green area has a different shape and boundary treatment, while trees and an exposed alternating barrier replace the reference’s spectator-bank setting. | **PARTIAL.** The overall Corkscrew enclosure agrees. The inside apron and connected kerb treatments remain visibly different; this is the same top-down tile as the entry view. | **NO** | Treat T8 and T8A as one continuous furniture-and-paint reconstruction, including the spectator bank’s tree distribution. |
| **T9 Rainey** | **MISMATCH.** The broad green inside strip and yellow apex element in the real view are not reproduced at comparable scale. The sim also substitutes a conspicuous Armco-lined outer slope for the reference’s darker, more continuous barrier edge. | **PARTIAL.** The runoff footprint, access roads and outer enclosure correspond. The sim’s fragmented green strips and kerb placement differ from the visible inside treatment. | **NO** | Restore continuous inside green paint, the yellow element and the correct outside barrier treatment. |
| **T10** | **PARTIAL.** The right red/white kerb and green apron are recognizable. The yellow apex sausage is missing, the apron’s white boundary is weak or absent, and the outside blue boards are not reproduced. | **PARTIAL.** The runoff and surrounding access-road arrangement broadly match. Green strips and kerb extents differ, with some paint apparently sitting outside the intended road-edge treatment. | **NO** | Add the yellow sausage, correct the green apron boundary and place the outside boards. |
| **T11** | **PARTIAL.** The inside concrete wall and outside blue barriers identify the corner. The real apex has a conspicuous yellow raised element and a clearly defined white/red kerb treatment that the sim does not reproduce convincingly. | **PARTIAL.** The pit-entry island, main pit building and outer runoff enclosure broadly agree. Apex detail and the long green strip alongside the pit-side approach differ. | **NO** | Rebuild the apex furniture and paint, then refine the wall termination and pit-side green strip. |

The most important remaining fixes, in priority order:

1. **Rebuild the distinctive apex treatments:** yellow sausage kerbs visibly missing at T8 entry, T9, T10 and T11; correct their placement behind the main kerbs.
2. **Correct green paint and white boundaries:** especially T1, T2, T8–T8A and T9. Match width, continuity and endpoints, and distinguish painted pavement from dirt.
3. **Restore close, corner-defining barriers and signs:** T3’s fence and boards, T4’s Mission wall, and the Corkscrew’s outside boards and barrier arrangement.
4. **Verify furniture positions:** particularly the overhead structure near T7 and the large nearby WeatherTech sign.
5. **Improve permanent scenery:** front-straight buildings and towers, T3/T4 spectator structures, and the denser, less uniformly spaced tree groups around the Corkscrew.

## Round 6 whole lap (verbatim)

**Overall: yes—the sim’s top-down layout reasonably matches the circuit, but several kerb, verge, barrier and structure details remain only partial matches.** The major landmarks and trackside spaces are recognizable throughout the lap.

I’ve ignored the Google UI and differences in aerial-photo age, colour and parked vehicles. At this resolution, individual yellow sausage kerbs and some fence details are too small to judge reliably; the table focuses on visible placement and extent.

| Tile / station range (m) | Verdict | Concrete differences |
|---|---|---|
| 1 · s0000–0170 | PARTIAL | Start-area bridge and major paddock building footprints broadly correspond. The sim’s green strip beside the paddock buildings is much less extensive; trackside wall and fence detail is simplified. |
| 2 · s0170–0340 | PARTIAL | Barriers around the approach and adjacent bend broadly follow the reference. The satellite’s long turquoise verge along the left-hand track section is largely absent; the sim instead emphasizes green paint around the adjacent bend. |
| 3 · s0340–0510 | PARTIAL | T2’s island and surrounding barrier enclosure are recognizable. The reference’s broad turquoise outer-exit apron becomes a narrower, darker green band; the sim’s inner green kerb backing is more conspicuous. |
| 4 · s0510–0680 | PARTIAL | The overlapping T2 view confirms the mismatch in painted apron width and extent. Island boundaries and outer barriers broadly agree, but the sim’s outside barrier reads as a strongly segmented black line. |
| 5 · s0680–0850 | PARTIAL | T3-area bridge and runoff boundaries correspond. The sim adds a prominent green-backed strip around the upper outside of the bend, where the reference shows a paler, less extensive edge treatment. |
| 6 · s0850–1020 | PARTIAL | Bridge location and nearby island footprint broadly match. Its dark frame and shadow are substantially more dominant in the sim; kerb backing and the paddock-side boundary need closer matching. |
| 7 · s1020–1190 | PARTIAL | T4 and the long grandstand occupy the expected locations. The sim’s stand is visibly split into distinct blocks with different roof tones; green paint on the outside of the turn extends more prominently down the straight. |
| 8 · s1190–1360 | PARTIAL | Trackside boundaries and grandstand continuation broadly agree. The reference’s white, green-roofed building beside the service road is missing or substantially underrepresented in the sim. |
| 9 · s1360–1530 | PARTIAL | The overhead crossing is in approximately the right place. The nearby green-roofed trackside building is again missing; the crossing’s deck/support treatment differs visibly from the reference. |
| 10 · s1530–1700 | PARTIAL | T5’s runoff enclosure and roadside tree line broadly correspond. The sim’s outer black barrier is unusually broken-looking, and its green-backed kerb differs in visible extent from the reference’s pale edge strip. |
| 11 · s1700–1870 | MATCH | The large road bridge, its curved approaches and nearby barriers align reasonably well. No major additional-object placement error is apparent at this scale. |
| 12 · s1870–2040 | PARTIAL | T6’s bridge and runoff enclosure broadly agree. The reference has a long turquoise strip through and beyond the bend; the sim substitutes a narrower green treatment with different endpoints. |
| 13 · s2040–2210 | MATCH | Rahal straight’s flanking boundaries and access paths broadly correspond. Vegetation appearance differs substantially, but this view does not establish a major misplaced added structure. |
| 14 · s2210–2380 | MISMATCH | The conspicuous transverse overhead structure/shadow lies much farther down the sim tile than its counterpart in the reference. The narrow roadside boundary and verge treatments also differ. |
| 15 · s2380–2550 | PARTIAL | The Corkscrew’s runoff enclosure and perimeter wall broadly correspond. The sim’s broad green backing through the direction change differs from the reference’s thinner turquoise edge treatment and its endpoints. |
| 16 · s2550–2720 | PARTIAL | The crossing below the Corkscrew and the T9-area enclosure are recognizable. The sim crossing reads as a broad, solid beige slab; the reference appears slimmer. T9’s turquoise painted edge is not reproduced with the same width and coverage. |
| 17 · s2720–2890 | PARTIAL | T9 exit, approach to T10 and the upper runoff boundary broadly agree. Green-backed kerbs are more prominent and have different extents, especially along the upper bend and the left side of the tile. |
| 18 · s2890–3060 | PARTIAL | T10’s surrounding walls and access-road junction correspond reasonably well. The sim emphasizes an inner green-backed kerb where the reference shows a much less prominent pale edge; the outer paved apron’s surface treatment differs. |
| 19 · s3060–3230 | PARTIAL | T11 approach, pit-building footprint and pit-entry separation are recognizable. The sim’s green band on the outgoing straight is longer/more continuous, and pit-entry wall ends and separation details need refinement. |
| 20 · s3230–3400 | PARTIAL | T11’s broad runoff, outside enclosure and adjacent building broadly match. The reference’s wide turquoise exit strip becomes a narrower green band; apex kerb and pit-divider details differ. |
| 21 · s3400–3570 | PARTIAL | Front-straight grandstands, pit building and parallel pit lane occupy the expected locations. Grandstand segmentation and roof proportions differ, while the pit-wall line and smaller pit-side structures are simplified. |

The whole lap passes a **broad layout acceptance check**: bridges, grandstands, pit facilities and major runoff enclosures generally appear in the right areas. It does **not yet pass a close trackside-detail check**. The most persistent visible issue is the width, length and placement of painted verges and kerb backing. The overhead feature in tile 14 is the clearest apparent local placement error. Centre-line geometry is excluded from this judgment.

Top five remaining fixes, in priority order:

1. **Resolve the tile 14 overhead-feature discrepancy.** Check the actual structure and its station before adjusting its placement; distinguish the structure from its shadow.
2. **Match kerb and verge footprints around the lap.** Prioritize T2, T6, the Corkscrew/T9 and T11. Match widths and endpoints before colour; verify yellow sausage kerbs with closer views.
3. **Restore the missing trackside building around s1190–1530.** The white building with the green roof is a clear landmark in two overlapping reference tiles.
4. **Refine barriers and pit separation.** Focus on the segmented-looking outer barriers at T2/T5, wall endpoints, pit entry and the front-straight pit wall.
5. **Correct bridge and grandstand forms.** Refine deck widths, supports, stand segmentation and roof proportions, especially the crossing below the Corkscrew and stands beside T4/front straight.