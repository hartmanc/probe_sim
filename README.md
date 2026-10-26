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
