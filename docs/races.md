# Race recordings (30 Oct 2026)

Owner, 30 Oct 2026: "I still smoked the AI, even those in clearly faster cars. It might be worth instrumenting my (and all users')
sessions to understand how human drivers are getting past AI."

A race is deterministic from (seed, AI version, build, config, the player's inputs) -- the worker identity test
(`src/app/__tests__/race-worker.test.ts`) proves the Worker and the main thread step the same bits -- so a race is recorded as those,
uploaded once, and re-run offline, where every car's state is available at 1 kHz.

## The format (`src/scoreboard/racerec.ts`, `RaceRecording`, `v: 1`)

| field | what |
|---|---|
| `trackId`, `fieldId`, `seed`, `laps`, `aiVersion`, `buildSha`, `physics` | which race, on which AI (`AI_VERSION`, a string), which build (vite `__GIT_SHA__`) and physics version |
| `build` | what `buildDirector` was given: `realGrid`, `playerAi`, `lod`, `strengthPct`, `closeRacing`, `planner`, `fieldCap` (the phone / tablet field selection, `neighbourField`), and the sim's `ref` / `autoShift` / `abs` at the start |
| `config` | the director's whole effective `RaceConfig` (`aiControlEvery`, `aiPhysicsEvery`, `mishapRate`, `followScale`, ... and `powerShare`); the re-run checks its own equal |
| `inputs` | the player's quantised 100 Hz samples in the hot-lap trace's encoding (`InputTrace`: rows `[step, steer, throttle, brake, flags]` written on change, gear-schedule `ref` changes, `steps`). On the wire, in the stored body and in a downloaded file the rows are one flat delta array `inputs.d` (`toWire` / `fromWire`: 5 ints per row, change of step / 10, steer, throttle, brake, absolute flags; 2-5 x smaller after gzip). They are the sim's own recorded rows (`HotlapSim` `record`), i.e. exactly what the director consumed, on the main-thread path and in the Worker alike |
| `events` | what the inputs cannot say, logged at the sim step it happened before: the player's recovery `[step, 0, s]` and an app-side rule report `[step, 1, kind]` (the pit-exit cones) |
| `live` | the safeguard: the player's lap times, every line crossing `{car, lapNr, t}`, the classification (`number, laps, time, metres`) |
| `snapshot` | a second check: every car's station (0.1 m, as Int16 deltas) and lane offset (0.1 m, Int8) once per sim second, base64 |
| `owner`, `started`, `durationS`, `aborted`, `truncated` | the owner token was present (the server decides), ISO start time, sim seconds, ended before the flag, cut to fit the cap |

Nothing identifying: no name, device id, secret or user agent. The privacy note (Credits) says so; `?record=0` switches it off,
`?record=download` also adds "Download the recording" to the results card (an `<a download>`, for the owner's machine).

When it is built: at the flag (once the stop-and-go is settled), when the player is out (`aborted`), when the race is restarted or
left (`aborted`; under 20 s it is not worth sending). `?playerai=1` races are not uploaded.

Size: JSON, gzipped in the browser (`CompressionStream`; without it the raw JSON is sent). The cap is 512 KB after compression
(`REC_MAX_BYTES`): a recording over it loses its snapshot first, then the tail of the inputs (rows, events and the live data cut at a
step, `truncated.atStep`); one that still does not fit is dropped. See "Size" below for measured numbers.

## The endpoint (`api/races.ts`, `src/scoreboard/racehandler.ts`)

- `POST /api/races`, body = the recording as `application/json` or gzip as `application/gzip` -> `204`. Same origin as the scoreboard;
  rate limit = the scoreboard's (10 per IP per 10 min, `429` + `Retry-After`); `415` content type, `413` over 512 KB compressed (the
  stream is cut off, not just the header trusted) or a gzip that unpacks past 12 MB, `400` not JSON / not gzip, `422` shape
  (`checkRecording`: `aiVersion` and `buildSha` strings, `inputs` within bounds and on the 100 Hz grid, snapshot sizes exact, known track).
- Stored gzipped (base64) at `sb:rr:<id>` for 90 days, `<id>` = `YYYY-MM-DD-<12 hex>`; the day's index is the sorted set board
  `rr:<YYYY-MM-DD>` (member = id, score = time, a small meta per member: track, seed, laps, AI, sha, bytes, owner), up to 5000 a day.
  The scoreboard's stale-board sweep skips `rr:` boards.
- `GET` is for the owner only (header `X-Owner-Token`, else `403`): `?day=YYYY-MM-DD` lists the day (`recordings: [{id, at, owner, track, seed, laps, ai, sha, bytes, ...}]`),
  `?id=<id>` returns the recording JSON. No public GET. 240 GETs per IP per 10 min.
- The owner token is the environment variable `RACES_OWNER_TOKEN` (16+ characters of `A-Za-z0-9_-`; set in Vercel, never printed; unset =
  nobody is the owner, `GET` answers `403`, every recording is public). The client sends it only when this device has it: open the site
  once with `#owner=<token>` (a hash fragment, which the browser never sends to the server, so it stays out of request logs; it is stored in `localStorage` as `probe-sim.owner.token` and cleared from the address bar, and is not in the recording). The server compares hashes and
  sets `owner` itself; a client's claim without the token is dropped.

## The offline tool (`tools/race/replay_race.ts`)

```
npx tsx tools/race/replay_race.ts <recording.json[.gz]> [--force] [--out <dir>]
npx tsx tools/race/replay_race.ts --dir <dir> [--rerun] [--force]            # every recording + the aggregate
npx tsx tools/race/replay_race.ts --fetch-day 2026-10-30 --url https://<host>/api/races   # needs RACES_OWNER_TOKEN in the environment
npx tsx tools/race/replay_race.ts --fetch <id> --url https://<host>/api/races
```

It builds the director from the recording's `build` exactly as `race.ts` does (`buildDirector`), steps the same `HotlapSim` with the
recorded rows and events, and CHECKS before it trusts anything:

1. `aiVersion`, `buildSha` (short-sha prefix) and `physics` must be this tree's, else it refuses (`--force` runs it and reports the mismatch);
   the effective `config` must equal the recording's.
2. the live lap times, every crossing time, the classification and every once-a-second position must come out identical; the first
   divergence is printed (`snapshot differs at second 212, car #14: ...`) and the file is flagged (left out of the aggregate; exit code 2).

Per race (`<out>/<name>.md` and `<name>.json`, default `tools/race/out/replays/`): the player's passes made and received, by the
selfplay position rule (from behind to ahead within 50 m of a running car, in green, checked every 0.1 s), each with station, corner
phase (straight / brake / entry / exit, `selfplay_where`), side (inside / outside / straight), pace ratio, the gap 5 s before and the closing
speed, time spent within 20 m behind, and the other car's state and the player's from -5 s to +5 s at 10 Hz (s, e, speed, speed over its
own profile, throttle, brake, lane-model state alone / following / pass phase / making room / lifting, its target lane, the speed limiter).
Lane-model state: `lifting` = limiter `passed`; `making room` = limiter `yield` or `alongside`, or a target lane more than 0.5 m off the line
while not passing; `pass phase` = `passPhase` 1-3; `following` = limiter `follow` or a lead car; else `alone`. Also: the player's laps against
the field's median, the AI's wait behind the player (a car 3 % or more faster arriving within 25 m behind it until it is ahead), contacts with
the player, four wheels off for 0.25 s.

`--dir` adds `aggregate.md`: passes by corner phase and side (made / received), the passed car's state distribution, the gap histogram, and
the traffic yardstick's cells (`traffic_curves.ts`: pass within a lap by pace delta d and gap g) for the human attacker (#619) against the AI
attackers in the same races, the owner's recordings apart from the public's.

Tests: `src/app/__tests__/racerec.test.ts` (a playerai race and a driven race with a recovery and a cone report, recorded as the app does,
re-run exactly, a tampered input stream, a wrong AI version / build refused, the Worker path on a fake clock),
`src/scoreboard/__tests__/racerec.test.ts`, `src/app/__tests__/racerec-client.test.ts`, `api/__tests__/races.test.ts`.
