# Probe Sim

A browser racing simulator for 24 Hours of Lemons car #619, a 1993 Ford Probe GT, on a computer (pad, wheel or
keyboard) or a phone or tablet (tilt or touch). Tracks: WeatherTech Raceway Laguna Seca and Sonoma Raceway, built from
OpenStreetMap, USGS lidar and aerial imagery and recent onboard video. Hot laps against the team's logged ghosts
(drivers A to D and Coby) with a server-checked scoreboard, and races against the real field of a 2026 Lemons race.
An unofficial fan project, not affiliated with 24 Hours of Lemons, the circuits or the teams shown; non-commercial
(some car models are CC BY-NC). Bugs and wishes: the game's Report button or GitHub issues.

- `src/physics` — vehicle model (6-DOF chassis, Pacejka tyres, FWD open diff).
- `src/app` — three.js renderer, input, HUD, audio, lap timing, ghosts.
- `tools/track`, `tools/ghosts` — Python pipelines that build `public/tracks/`.
- `tools/car` — Blender script that builds `public/cars/probe_gt/probe.glb`.
- `api/` — Vercel Functions: `scores.ts` (scoreboard, `docs/scoreboard.md`), `feedback.ts` (the report button).
- `CONTRACTS.md` — data formats and the physics API shared by all parts.
- `improvements.md` — assumptions to replace with measurements, data wishes.
- Notes index (where each part documents itself): the "Notes index" section of `CONTRACTS.md`.

Run: `npm install && npm run dev`, then open http://localhost:5173.
Build a static site: `npm run build` (output in `dist/`, relative paths, works on GitHub Pages).

## Licence

The code in this repository is released under the MIT License (`LICENSE`).

The game assets are not. `public/cars`, `public/audio` and `public/tracks` carry their own notices, listed on the
game's Credits page and in `public/cars/field/credits.json` and `public/audio/families/credits.json`: the field's car
models derive from CC BY and CC BY-NC work (the CC BY-NC-SA ones are shared under the same licence as changed here), the
engine sounds from CC BY recordings, the track outlines from OpenStreetMap data (ODbL), and the Probe #619 model, livery
and sounds belong to the team. The non-commercial statement on the Credits page applies to the game as a whole.

24 Hours of Lemons, its name, logos and the names of its races and awards are trademarks and property of their owner;
the same goes for the circuits (WeatherTech Raceway Laguna Seca, Sonoma Raceway, Buttonwillow Raceway Park, Mid-Ohio
Sports Car Course), the teams and their liveries, and the car makers' marks. They appear here only to describe the real
events and cars the game depicts. This is an unofficial fan project with no affiliation with or endorsement from any of
them, and nothing in this repository or its licence grants any right to those names or marks.
