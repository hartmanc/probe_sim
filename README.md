# Probe Sim

A browser racing simulator for 24 Hours of Lemons car #619, a 1993 Ford Probe GT,
built for driver practice on a laptop with an Xbox gamepad or keyboard.
First track: WeatherTech Raceway Laguna Seca, built from OpenStreetMap, USGS
lidar and USGS aerial imagery. Ghost laps come from the team's own race logger.

- `src/physics` — vehicle model (6-DOF chassis, Pacejka tyres, FWD open diff).
- `src/app` — three.js renderer, input, HUD, audio, lap timing, ghosts.
- `tools/track`, `tools/ghosts` — Python pipelines that build `public/tracks/`.
- `tools/car` — Blender script that builds `public/cars/probe_gt/probe.glb`.
- `CONTRACTS.md` — data formats and the physics API shared by all parts.
- `improvements.md` — assumptions to replace with measurements, data wishes.
- Notes index (where each part documents itself): the "Notes index" section of `CONTRACTS.md`.

Run: `npm install && npm run dev`, then open http://localhost:5173.
Build a static site: `npm run build` (output in `dist/`, relative paths, works on GitHub Pages).
