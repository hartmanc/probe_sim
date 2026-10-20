# Sonoma: Street View survey (SKILL 0.5), rederive run 20 Oct 2026

Route: the agent's own Claude-in-Chrome tab (a headless Chrome rendered Street View black: no WebGL panorama), one tab,
closed after the captures. Screenshots are reference only (git-ignored, `inventory/streetview/`), never textures.

Every panorama found on the circuit is dated **July 2011**. The 2026 onboard (RAZip6S84CM) outranks it: a Street View row
is kept only where the onboard shows the same structure (SKILL source precedence).

| place | panorama | heading | date | what it shows | kept? |
|---|---|---|---|---|---|
| S/F, pit straight | 5MY4xR9O7etAXEHnZCVnGQ | 300 | Jul 2011 | left pit wall (concrete, 1.08 m by horizon ratio, HEIGHTS ex. 1), right drag-strip Jersey (0.93 m), catch fence none on the drag side | heights kept: same walls on the onboard 0:00-0:04 |
| T11 hairpin, outside | jrXpHaDfJT2APw6zcyBKRA | 40 | Jul 2011 | tall board wall behind a Jersey (5.2 m, HEIGHTS ex. 3), yellow/blue tyre stack facing | wall height kept (onboard 1:56 door-ref 5.0-5.6 m); 2011 boards (Save Mart, Yokohama) not used: 2026 boards differ |
| T11 hairpin, apex | jrXpHaDfJT2APw6zcyBKRA | 196 | Jul 2011 | yellow/blue tyre stacks on the apex apron, painted runoff | rejected: the 2026 onboard 2:02-2:04 shows red/white striped blocks there |
| T2 entry | H9xspk4q_OoFIjVDhaMzDA | 210 | Jul 2011 | flat blue/white kerb (under 2 cm, HEIGHTS ex. 7), terraces on the hill, tyre wall at their foot | kerb position kept, colour not (red/white on the 2026 onboard 0:14) |
| T12 | QduY6QTXmw4JDevQVE_b-g | 0 | Jul 2011 | 2-storey suites and the T12 control building (6.4 m, HEIGHTS ex. 8), STP boards | building heights cross-checked with the lidar p60; 2011 boards not used |

Not surveyed (no panorama found by pano id; the circuit roads have only the 2011 drive): T3-T9a. Those places rest on
the onboard and the captures alone.
