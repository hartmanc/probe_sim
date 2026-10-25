---
name: build-field-cars
description: Build the AI field for one Lemons event in the Probe sim (identities from the event's SmugMug gallery and the Lemons award archive, pace from the MyLaps session, one glb per car from the car kit with Sketchfab imports first), the way the Laguna Oct 2026 field was built and the Buttonwillow Sep 2026 field is being built. Use for every new event field.
---

# build-field-cars

The field of one event: every entrant of its MyLaps race session except #619 becomes an AI car with its real pace,
an identity row and, car by car, a glb model. The recipe for a single car is `tools/cars/README.md` (the kit lives in
`tools/cars/`, local only, excluded from git by `.git/info/exclude`; the outputs under `public/cars/field/` are
committed). This skill is the event-level method around it.

## Defaults (owner, 22 Oct 2026)

- **Sketchfab first.** A recognisable stock car with a usable free model on Sketchfab is imported (`tools/cars/kit/IMPORT.md`,
  licences CC0 / CC-BY, NC or SA only where `kit/model_sources.json` records the owner accepting them, no flagged
  uploaders or suspected re-uploads); the kit loft is the fallback and the report says when it was used.
- **The event's gallery is the photo source:** `https://24hoursoflemons.smugmug.com/Race/<event-album>`. Index it, download
  it politely (the Laguna scripts in `tools/cars/field/`), read numbers off contact sheets, place each car's best
  photos in `tools/cars/field/photos/<event>/<num>/` and list the number in `READY.json` as you go, so car builders
  can start. Photos are reference only, never committed, never textures.
- **The Sketchfab token is the owner's.** `kit/sketchfab_fetch.py` reads `SKETCHFAB_TOKEN`; the documented route sources
  `.env.local` silently. An agent denied that step lists the uids and output directories it needs and the owner runs the
  fetches (`! (set -a; . ./.env.local >/dev/null 2>&1; set +a; uv run --python 3.12 python -I tools/cars/kit/sketchfab_fetch.py --uid <uid> --out tools/cars/kit/downloads/<num>/)`
  from the prompt) or starts the session with the token exported. No agent works around the denial or asks another
  agent to do it.

## Stages

1. **Data (Sonnet).** MyLaps / Speedhive event results API: the race session's classification and every position's
   lap file into `tools/race/data/<track>/` (untrusted downloads, `python -I` readers). `match_laguna.json` (or the
   previous event's) by exact normalised team name, number as tie-break, no fuzzy matches: the same car at two events
   keeps one id and one model.
2. **Identities (Sonnet).** The gallery (above); `tools/cars/field/lemons_results/awards.json` (Lemons award pages,
   `fetch_results.py`; the event's own page names the award winners' cars, earlier pages the long-running teams');
   web for the rest. `cars_data_<event>.py` rows in the shape of `cars_data.py` (dimensions with a Wikipedia source per
   model; identity, colours, livery, theme details, engine guess, confidence, evidence per car) and
   `build_identity.py` writing `public/cars/field/<track>/identity.json` in finish order. Notes in
   `tools/cars/field/NOTES-<event>.md`.
3. **Ids.** A car's id is its number. A car whose number belongs to a different car in an earlier event's field gets
   `<num>_<event tag>` (Buttonwillow: `0_bw`, `1_bw`, `8_bw`, `9_bw`, `16_bw`, `40_bw`, `43_bw`, `89_bw`, `711_bw`,
   `801_bw`). pace, identity and models rows carry `id`; the app resolves identity and model by id with number as the
   fallback; `models.json` is one global pool.
4. **Pace (Opus).** `tools/race/pace_track.ts` in its own-session mode: every entrant with its own stints under the
   `tools/race/pace.ts` rules, `public/cars/field/<track>/pace.json`, then `calibrate_field.ts --track <id>` (heavy:
   one background process, log to a file). Laguna races must stay bit-identical.
5. **Cars (Opus, a few per agent, in parallel only with the owner's say-so).** Per car the README recipe: identify from
   the photos and the identity row, stock dimensions and a true side view, Sketchfab survey and import (or loft), spec
   `tools/cars/specs/<id>.py` with `photo_event`, build, `check_car.py`, previews and sheet, the IMPORT.md acceptance
   checklist. Builders never commit; the orchestrator commits specs' outputs (`public/cars/field/models/<id>.glb`,
   `models.json`, `credits.json`) on the field branch and sends the owner the preview sheets.
6. **Review.** The owner looks at every car's sheet against its photos (he checks theme details first); Astra or Claude
   judges the sheets when he asks. Fixes go back to the same builder.

## Rules

Never read `.env*` or print environment values (presence-only checks). Downloads untrusted: own directories, never
executed. At most 2 heavy processes per agent; stop under 10 GB free. No `git add -A`; explicit paths; the usual
commit identity and trailers. The field branch merges to main only on the owner's say-so, with the track it belongs to.
