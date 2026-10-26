# Scoreboard: contract and client integration

A public arcade scoreboard: top 10 per board, no login, names of up to 12 characters, each name owned by the device(s)
that posted it (§1.1). Two modes:

| mode | score | order | how it is checked |
|---|---|---|---|
| `hotlap` | best valid lap time, s | lower is better | plausibility checks, then the server **replays the input trace** with the real physics |
| `race` | finish time of a 5-lap race (`LIMITS.raceLaps`) against the AI; a car classified short by distance, encoded above `LIMITS.raceDnfBase` | lower is better | plausibility checks only (`replay` field reserved). **Closed for the public since 0.4.0** (owner, 26 Oct 2026): until the server can replay a race, race posts and race board reads answer `410` and the client hides the race board and the results' submit row (`RACE_BOARDS_PUBLIC` in `src/app/scoreboard-client.ts`). The code paths stay and are tested with `HandlerDeps.raceBoards = true`. |

Code: `src/scoreboard/` (pure TS, shared by client and server), `api/scores.ts` (Vercel Function), `vercel.json`.

## 1. Boards

Board key (`boardKey()` in `src/scoreboard/validate.ts`):

```
hotlap:<track>:<car>:<physics>
race:<track>:<car>:<physics>:<ai_version>
```

`physics = physicsVersion(carJson, track.length_m, TRACKS[track].rev)` (`src/scoreboard/hash.ts`): a cyrb53 hash of
`PHYSICS_VERSION` (in `src/scoreboard/config.ts`), the track length and the canonical (key-sorted) car.json, plus, for a
track whose registry entry has one, its geometry revision `rev` (20 Oct 2026: a content fingerprint of the published
track.json, so rebuilding one track opens that track's boards only; a global `PHYSICS_VERSION` bump would reset every
track). Laguna has no `rev`: its key is byte-identical to 0.2.0's. The rolling start (`TRACKS[track].start`, a named
corner and distance, or a station in metres, and a speed) is part of every replay as well.
A car.json recalibration or a `PHYSICS_VERSION` bump therefore opens fresh boards automatically. **Bump
`PHYSICS_VERSION` whenever anything else a replay depends on changes**: src/physics code, track.json geometry,
heightfield.bin, scenery.json (walls, pit lane, paved zones, far terrain), ghosts.json (gear schedules, line
offsets), src/app/timing.ts (the lap timer the replay uses), or `src/scoreboard/sim.ts`. Otherwise old traces
stop replaying and players get "lap time differs" rejections.

Since 0.4.0 the hash ignores car.json's `"_"` comment keys (src/physics/spec.ts ignores them too), and
`PHYSICS_KEY_PINS` in `config.ts` maps the computed values of the shipped car.json to the keys the 0.3.0 boards were
published under, so the boards kept their entries through the comment edit. Any real change computes an unpinned
value and opens fresh boards as before. The server accepts only its own current physics value (`422 physics version
mismatch`) and, for a race, only the current AI board version (`currentRaceAiVersion()` = `<AI_VERSION>-<laps>L`).

Whitelists (`config.ts`, checked with `Object.hasOwn`): tracks = the keys of `TRACKS` (Laguna Seca, Sonoma,
Buttonwillow), cars `probe_gt`, modes `hotlap`/`race`, input `pad`/`keys`/`phone`.

Storage (Upstash Redis): one sorted set per board (`sb:z:<board>`, member = lower-cased name, score = time) plus a
hash of entry details (`sb:h:<board>`). Best per name is kept (`ZADD LT CH`), each board is trimmed to 100 entries,
GET returns the top 10. **Old boards expire**: at most once an hour per warm instance, after a POST, the server lists the
boards (`SCAN sb:z:*`) and gives every hot-lap board whose physics value is not the server's current one a 30-day TTL
(`LIMITS.staleBoardTtlS`) on both keys; race boards are left alone while hidden. The sweep runs **only after a POST**
(a quiet site expires nothing until the next post) and **skips race boards**, old ones included (their key carries the AI
version; they stay as they were until race boards reopen or the owner deletes them in the console). The TTL is set once
and not refreshed: a board that becomes stale is gone 30 days later even if it is read meanwhile.

| key | what | written by |
|---|---|---|
| `sb:z:<board>`, `sb:h:<board>` | a board and its entry details | POST |
| `sb:own:<name>` | name ownership: the string `v1\|<iso date>\|<hash>,<hash>,…` (sha256 of each device secret, ≤ 5) | first POST of the name (`SET NX`); `adopt` (Lua) |
| `sb:xfer:<name>` | the name's current transfer code (its hash), 1 h TTL, deleted when used | `transfer-code` (Lua) |
| `sb:fbdup:<sha256>` | a filed report (issue number) for 10 min, so a repeat is not filed twice | /api/feedback |
| `sb:rl:post:<ip>`, `sb:rl:code:<ip>`, `sb:rl:adopt:<ip>`, `sb:rl:adoptname:<ip>:<name>`, `sb:rl:adoptname:<name>`, `sb:rl:feedback:<ip>` | rate-limit counters, 10 min TTL | POST, ops, /api/feedback |

### 1.1 Name ownership (owner, 26 Oct 2026)

- Every device makes a **secret** once: 128 random bits as 32 hex characters, `localStorage['probe-sim.scoreboard.secret']`,
  sent as `secret` with every POST. The server stores only `SHA-256("probe-sim/owner/v1/" + secret)`.
- **The first device to post a name claims it** (`SET sb:own:<name> … NX` after the lap passes the replay). A POST
  without a well-formed secret answers `422 device secret missing: reload the game`; a POST of a name owned by other
  devices answers `403 name taken` **before** any replay.
- **Transfer code**: on the owning device, Scoreboard → Transfer code POSTs `{ op: 'transfer-code', name, secret }`
  and shows a six-character code (alphabet without 0/O/1/I/L, 31^6 ≈ 8.9e8 codes), valid one hour, single use, bound to
  that name. On the other device, Scoreboard → Use a transfer code POSTs `{ op: 'adopt', name, code, secret }`, which adds
  that device's secret hash to the name (at most 5 devices; the oldest drops). An adopted device is a full owner: it can
  issue codes and add devices too, and five adoptions in a row evict the first device.
- **Atomic** (Astra review, 26 Oct 2026): issuing (check the owner, store the code) and adopting (check and consume the
  code, then add the device only if the owner record still exists) are each ONE Redis operation, a Lua script under
  `EVAL` (`LUA_ISSUE`, `LUA_ADOPT` in `src/scoreboard/store.ts`). Two devices racing with one code: exactly one wins; a
  code issued meanwhile is not consumed by the wrong adoption; a manual release is never undone by an adoption in flight.
  The memory store runs the same logic as one uninterrupted step (`owner-race.test.ts`). The scripts were not executed
  against a real Redis in the 0.4.0 round (no Redis here): **smoke test on the first preview**: post a lap as a test
  name from browser A, take its transfer code, type it in browser B (Scoreboard → Use a transfer code: "This device now
  posts as …"), type the same code in browser C ("that code is wrong or expired"), and check in the Upstash console that
  `GET sb:own:<name>` holds two hashes and `sb:xfer:<name>` is gone. A script error shows as a 500 and
  `[scores] error: … redis: …` in the function log.
- **Limits and the trade-off**: the code alone cannot spoof a post: it must be paired with the name, it only adds a
  device, it expires in an hour and dies on first use. Adopt attempts: 5 per IP, 5 per IP + name and 100 per name from
  all IPs per 10 minutes (on top of the 10-per-IP POST limit and the WAF rule). The per-name ceiling bounds brute force
  (at most 600 guesses in a code's hour: ≈ 7e-7 chance); the price is that 20 or more addresses can block a name's
  transfers for 10 minutes at a time. The owner's existing devices keep posting meanwhile.
- **Existing entries** (posted before 0.4.0) keep their times; the first device to post that name afterwards claims it.
- **Releasing a name** (owner, Upstash console → Data Browser or CLI): `DEL sb:own:<lower-cased name>` and
  `DEL sb:xfer:<lower-cased name>`. The next device to post the name claims it; its board entries are untouched (remove
  an entry with `ZREM sb:z:<board> "<name>"` and `HDEL sb:h:<board> "<name>"`).

## 2. HTTP API (`/api/scores`)

All responses are JSON with `Cache-Control: no-store`. Errors: `{ ok: false, error, reasons?: string[] }`.

| request | response |
|---|---|
| `GET /api/scores` | `{ ok, store: "memory"\|"upstash", boards: { "laguna_seca/probe_gt": "<current hot-lap board key>" } }` |
| `GET /api/scores?board=<key>[&name=<name>]` | `{ ok, board, mode, entries: Score[], you?: Score\|null }` (`you` only when `name` is given) |
| `POST /api/scores` with a `Submission` (JSON, with `secret`) | `{ ok, board, rank, best, improved, replayed? }` |
| `POST /api/scores` `{ op: 'transfer-code', name, secret }` | `{ ok, name, code, expires_s }` (404 name not registered, 403 another device's) |
| `POST /api/scores` `{ op: 'adopt', name, code, secret }` | `{ ok, name }` (403 wrong or expired code) |

`Score = { rank, name, score, input, at, ai_version?, laps? }`. Status codes: 400 bad JSON / board key,
403 foreign `Origin` or `name taken`, 410 race board / race post (closed), 413 body > 2.5 MB, 415 not JSON, 422 rejected
(with `reasons`), 429 rate limited (10 POSTs per IP per 10 min, `Retry-After`), 503 server assets missing, 500 otherwise.

Same origin only: requests without an `Origin` header (same-origin GETs, curl) pass; a present `Origin`
must match the request host or be listed in `SCOREBOARD_ALLOWED_ORIGINS` (comma separated; e.g. the Vite
dev server when testing against `vercel dev`).

### Submission (`src/scoreboard/types.ts`)

```ts
// hot lap
{ mode: 'hotlap', track: 'laguna_seca', car: 'probe_gt', physics: sim.physics,
  name, input: 'pad'|'keys'|'phone', device?: string,
  time: lap.time, lap: lap.n, valid: lap.valid, trace: sim.trace() }

// race (reserved shape; plausibility-checked only)
{ mode: 'race', track, car, physics, ai_version, name, input, device?,
  metres, laps, position?, finished?, replay?: unknown /* reserved, ignored */ }
```

Plausibility (`validateSubmission`): whitelisted ids; `physics` equals the server's (else "reload the
game"); name 1-12 printable characters after trimming and collapsing spaces (no control, format or
zero-width characters); hot lap: 90 s < time < 600 s, `valid === true`, `lap` 1..6, trace present and
well formed and matching track/car/physics; race: 0 < metres <= 5 x track length + 250 m, `laps` 0..5
and consistent with metres (+-250 m), `finished` implies 5 laps and a race time. The hot lap is then replayed: lap `lap`
must complete, be valid, and |replayed - claimed| <= 0.05 s. The **replayed** time is what is stored.

### Input trace (`InputTrace`)

```ts
{ v: 1, physics, track, car, hz: 100, dt: 0.001,
  reset: { pos: [x, y, z], heading, speed },     // the canonical rolling start (checked)
  ref: [[0, 'driver_a_best'], [step, id|null], ...], // gear-schedule reference ghost changes (Laguna's ids)
  rows: [[step, steer, throttle, brake, flags], ...],
  steps }                                         // physics steps from the reset to the submit
```

Rows are integers, written only when something changed: `step` is a multiple of 10 counted from the
reset; steer -1000..1000 (+ = left), throttle/brake 0..1000; flags: 1 shiftUp, 2 shiftDown (pulses, act
on that row's step only), 4 handbrake, 8 autoShift on, 16 ABS on (held states). A 140 s lap from a pad is
about 13 000 rows / 270 KB of JSON; the caps are 720 000 steps, 72 001 rows, 2.5 MB.

## 3. Client integration (for the menu/mode framework)

### 3.1 Drive the car through `HotlapSim`

Determinism only holds if the browser runs exactly the loop the server replays, so hot-lap mode should use
`HotlapSim` (`src/scoreboard/sim.ts`) instead of its own `physicsStep()`:

```ts
import { HotlapSim, type SimAssets } from '../scoreboard';
const simAssets: SimAssets = { trackId: 'laguna_seca', carId: 'probe_gt', track, heightfield,
  carJson: assets.carSpecJson, scenery: assets.scenery?.json ?? null,
  farHeightfield: assets.scenery?.farHeightfield ?? null, ghosts: assets.ghosts };
const sim = new HotlapSim(simAssets, { record: true, autoShift, abs });

// fixed-step loop (replaces physicsStep):
while (acc >= STEP) {
  const ev = sim.step(() => {               // called on every 10th step only (100 Hz grid)
    const raw = { steer: input.steer, throttle: input.throttle, brake: input.brake,
                  handbrake: input.handbrake, shiftUp: latchedUp, shiftDown: latchedDown };
    latchedUp = latchedDown = false;        // shift presses are latched until the next sample
    return raw;
  });
  if (ev && ev !== 'start') onLap(ev);
  acc -= STEP;
}
```

Rules this implies:

- Read the car from `sim.vehicle` every frame (reset builds a **new** Vehicle) and lap state from
  `sim.timer` / `sim.simTime`. Do not call `vehicle.step`, `reset` or `setScheduledGear` yourself.
- `sim.surface` is private to the sim: `Surface.sample()` caches the last station, so any extra call
  (HUD off-track tag, scenery placement) changes later results. Build a second `createTrackSurface()`
  for rendering/HUD.
- Settings go through the sim and take effect at the next 100 Hz sample, where they are recorded:
  `sim.autoShift = on`, `sim.abs = on`, `sim.setRef(ghostId | null)` (the HUD's reference ghost drives
  the auto-shift gear schedule).
- Reset (R key, menu restart) = `sim.reset()`: fresh vehicle and surface, timer cleared, step counter
  zeroed, and **a new recording starts**. Recording always starts at the hot-lap reset (the canonical
  rolling start 130 m before T11 at 22 m/s); there is no other valid start.
- Pausing (menu open, tab hidden, controls panel) is fine: no steps, nothing recorded.
- What is applied is the quantised input (`sim.input`), held for 10 ms; feed audio/HUD from it or from the
  device, either is fine.

### 3.2 Submitting

On a lap event with `lap.valid` and `lap.time` better than the player's stored PB for the board:

1. Ensure a name: `localStorage['probe-sim.scoreboard.name']`; if missing, prompt (max 12 chars) and store it.
2. `device`: `localStorage['probe-sim.scoreboard.device']`, a random id (`crypto.randomUUID()`) made once.
3. `input` tag: count `input.source` (`'gamepad'` -> `'pad'`, `'keyboard'` -> `'keys'`; touch controls,
   when they exist, -> `'phone'`) at each 100 Hz sample during the lap and send the most used one.
4. POST the submission (3.1's `sim.trace()` taken in the lap handler, before any further step) with
   `fetch('/api/scores', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body })`.
   Show the returned `rank`, or the `reasons` of a 422. Store the PB under
   `localStorage['probe-sim.scoreboard.pb.<board>']` only on `ok`.
5. The trace runs from the reset, so only laps 1..6 can be submitted; after lap 6 tell the player to
   reset (R) to keep posting. Keep `physics` from `sim.physics`; a 422 "physics version mismatch" means
   the page is stale: ask the player to reload.

Wrap all `localStorage` access in try/catch (private windows). Never block driving on the network.

### 3.3 Menu "Scoreboard" entry

- Board key: `boardKey('hotlap', 'laguna_seca', 'probe_gt', physicsVersion(carJson, track.length_m))`
  (or take `boards['laguna_seca/probe_gt']` from `GET /api/scores`).
- `GET /api/scores?board=<key>&name=<stored name>`; render `entries` as rank, name, time
  (`m:ss.sss`), input icon; if `you` is set and `you.rank > 10`, add a separator row with it.
- Race tab (hidden while `RACE_BOARDS_PUBLIC` is false): key `boardKey('race', track, car, physics,
  raceBoardVersion(AI_VERSION))`; finish time, or laps + distance for a car classified short.
- Fetch on open, no polling; show "offline" on failure. Responses are `no-store`.

## 4. Server notes

- `api/scores.ts` exports `GET`/`POST`/`OPTIONS` (Web `Request` -> `Response`) and delegates to
  `handleScores()` in `src/scoreboard/handler.ts` (tested directly in vitest).
- **Assets for the replay** are shipped with the function by `vercel.json`
  `functions["api/scores.ts"].includeFiles = "public/{tracks,cars}/**/*.{json,bin}"` (about 4 MB) and read
  from `<cwd>/public/...` by `api/_lib/assets.ts` (override with `SCOREBOARD_ASSET_ROOT`), decoded once per
  warm instance. They are the same files the static site serves, so client and server see the same bytes.
- **Module resolution**: Vercel transpiles each `.ts` file but keeps import specifiers, and the package is
  `"type": "module"`, so the extensionless imports in `src/` fail under Node ESM (verified locally:
  `ERR_MODULE_NOT_FOUND`). `api/_lib/resolve-hook.ts` installs a `module.registerHooks` resolve hook
  (Node >= 22.15) that retries with `.js`/`.ts`/`/index.js`, and `api/scores.ts` imports the handler
  graph dynamically after installing it. Verified by transpiling every file individually with esbuild
  and running GET/POST under plain Node 26. Keep the Vercel project on Node 22.15+ (24 is fine).
- A replay of rolling start + one 139 s lap (159 000 steps) takes about 0.25-0.3 s of CPU; the worst case
  (720 000 steps) about 1.3 s. `maxDuration` is 30 s.

### Environment variables (names only)

| name | purpose |
|---|---|
| `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN` | Upstash REST endpoint + token (checked first) |
| `KV_REST_API_URL`, `KV_REST_API_TOKEN` | the same, under the names the Vercel Marketplace integration injects |
| `SCOREBOARD_ALLOWED_ORIGINS` | optional extra allowed origins (comma separated) |
| `SCOREBOARD_ASSET_ROOT` | optional override of the public/ directory the replay reads |
| `GITHUB_ISSUES_TOKEN` | api/feedback.ts only: a fine-grained GitHub token limited to Issues (read and write) on hartmanc/probe_sim; unset = the report button answers 503 |

With neither Redis pair set the function uses an in-memory store (local dev, tests; on Vercel that would
mean per-instance, throwaway boards, and `GET /api/scores` reports `"store": "memory"`).

## 5. Deployment (lead + owner)

1. `vercel link` (choose/create the project; framework Vite, output `dist`, both also set in `vercel.json`).
2. In the Vercel dashboard: Storage / Marketplace -> **Upstash for Redis** -> create a database and connect
   it to the project (all environments). This injects the `KV_REST_API_*` (and/or `UPSTASH_REDIS_REST_*`)
   variables. Check presence without printing values: `vercel env ls`.
3. Project Settings -> Node.js version 22.x or 24.x.
4. `vercel deploy --prod`.
5. Smoke test (replace `$HOST`):

```sh
curl -s https://$HOST/api/scores                      # store must be "upstash"; note the board key
curl -s "https://$HOST/api/scores?board=hotlap:laguna_seca:probe_gt:<physics>"
curl -s -X POST https://$HOST/api/scores -H 'Content-Type: application/json' \
  -d '{"mode":"hotlap","name":"x"}'                   # expect 422 with reasons
# full round trip with a real autopilot lap (prints the claimed lap time, writes sub.json):
npx tsx -e "import {writeFileSync} from 'node:fs'; import {recordLap} from './src/scoreboard/__tests__/fixtures';
  const {lap,trace}=recordLap(); writeFileSync('sub.json', JSON.stringify({mode:'hotlap',track:'laguna_seca',
  car:'probe_gt',physics:trace.physics,name:'smoke test',secret:'0123456789abcdef0123456789abcdef',input:'pad',time:lap.time,lap:lap.n,valid:lap.valid,trace}));
  console.log(lap.time)"
curl -s -X POST https://$HOST/api/scores -H 'Content-Type: application/json' --data-binary @sub.json
```

The last call should answer `{"ok":true,...,"replayed":138.904}` (the autopilot lap). That entry then sits
on the public board; the board has no delete endpoint, so remove it with the Upstash console
(`ZREM sb:z:<board> "smoke test"` and `HDEL sb:h:<board> "smoke test"`) or use a name you are happy to keep.

## 5.1 Security headers (`vercel.json`)

Every path gets an enforcing `Content-Security-Policy` (`default-src 'self'`; scripts only from the site; inline styles
allowed for the DOM HUD; `blob:` for GLTF textures, images, audio and workers; `connect-src` adds the analytics host),
`X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy: strict-origin-when-cross-origin` and a `Permissions-Policy`
denying camera, microphone and geolocation. A second rule, for every host except `lemons-sim.app` (`missing` host),
replaces the CSP with one that also allows the Vercel preview toolbar (`vercel.live`, `vercel.com`,
`assets.vercel.com`, `wss://ws-us3.pusher.com`; https://vercel.com/docs/vercel-toolbar/managing-toolbar), so the toolbar
works on preview deployments while production keeps the strict policy. Not verifiable locally: check once on the first
preview that the toolbar loads, and on production that `curl -sI https://lemons-sim.app/` shows the strict policy.
`vite preview` serves the production rule (vite.config.ts), so a local preview shows what production enforces.

Evidence for the zero-violation claim: `tools/release/csp_check.mts` (headless Chrome against `vite preview`, collects
`securitypolicyviolation` events and console errors while it opens every Start-menu page, drives a hot lap and races to
the results card) and its logs in `docs/evidence/`. Rerun:

```sh
npm run build && npx vite preview --port 4173 --strictPort &
npx tsx tools/release/csp_check.mts "http://localhost:4173/?track=sonoma&laps=1" csp docs/evidence
npx tsx tools/release/csp_check.mts "http://localhost:4173/?track=laguna_seca&laps=1" csp docs/evidence
```

## 5.2 The report button (`/api/feedback`)

`POST /api/feedback { kind: 'bug'|'feature', description, context?: { version, sha, track, device, ua, screen, error },
name?, secret? }` → `{ ok, number, url }` files an issue on hartmanc/probe_sim with the labels `from-game` and the kind
(`src/feedback/handler.ts`, `docs/feedback.md`). Same origin only; 3 reports per IP per 10 min (the scores store's counter); body ≤ 4 KB;
description 1-2000 characters; control and format characters stripped; everything the player typed sits in code
fences (no mentions, links or markup), the title's `@` becomes `(at)`. The issue carries the scoreboard name only when
the device secret owns it, else "anonymous". No email field. 503 without `GITHUB_ISSUES_TOKEN`, 502 when GitHub refuses.

## 6. Determinism findings (for the physics owner)

The replay is bit-identical to the live run (test: `src/scoreboard/__tests__/replay.test.ts`) **given the
rules in 3.1**. Things in the current code that break it if the app does not go through `HotlapSim`:

- `Vehicle.reset()` does not clear `schedGear`, `kickHold`, `engageTimer` (and `simTime`, harmless): a
  reset car is not a fresh car. `HotlapSim` builds a new Vehicle on every reset.
- `createTrackSurface().sample()` is stateful (`cache` = last station, then a downhill walk), so results
  depend on the history of calls; `src/app/index.ts` shares one surface between physics, the off-track
  check and the per-frame HUD. `HotlapSim` owns a private surface and rebuilds it on reset.
- `src/app/index.ts` keeps `stepCount` across resets, so the 200 Hz timing/gear-schedule phase relative
  to the reset varies, and it samples input per rendered frame (variable rate, unquantised).
- No `Math.random`/`Date` in src/physics. Floating-point order is fixed. Remaining cross-engine risk:
  `Math.sin/cos/atan2/exp/pow` are not required to be correctly rounded, so Safari (JavaScriptCore) or
  Firefox can differ from V8 (Node/Chrome) in the last bit and a long lap could drift past 0.05 s.
  Not testable here; if Safari players see rejections, the fix is deterministic math helpers in
  src/physics (or a wider tolerance).
