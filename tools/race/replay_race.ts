// Re-run race recordings offline and measure how the human player passes the AI (docs/races.md).
//   npx tsx tools/race/replay_race.ts <recording.json[.gz]> [more files] [--force] [--out <dir>]
//   npx tsx tools/race/replay_race.ts --dir <dir of recordings> [--rerun] [--force] [--out <dir>]     (+ the aggregate, filtered on evidence:
//     --min-laps N (default the race's laps) --max-fouroff-per-lap 0.5 --max-contacts-per-lap 0.5 --max-lap-spread 1.25 --aborted (keep aborted ones))
//   npx tsx tools/race/replay_race.ts --fetch <id> --url https://<host>/api/races                     (fetch token from env RACES_FETCH_TOKEN)
//   npx tsx tools/race/replay_race.ts --fetch-day 2026-10-30 --url https://<host>/api/races            (saves the day's recordings to <out>/recordings)
// A recording is refused when its AI version or build sha is not this tree's (--force runs it and reports the mismatch), then the
// re-run must reproduce the live lap times, line crossings, classification and once-a-second positions exactly; a file that does not
// is flagged (the first divergence is printed) and left out of the aggregate. Output per race: <out>/<name>.md and <name>.json.
import { execSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs';
import { basename, resolve } from 'node:path';
import { gunzipSync } from 'node:zlib';
import { loadSimAssets } from '../../api/_lib/assets';
import { fromWire, type RaceRecording } from '../../src/scoreboard/racerec';
import { ROOT, loadIdentityJson, loadPace } from './load';
import { replayRecording, type ReplayResult } from './replay_core';
import { aggregateMd, raceMd, type RaceFile } from './replay_report';

const argv = process.argv.slice(2);
const opt = (k: string): string | null => { const i = argv.indexOf(k); return i >= 0 ? argv[i + 1] ?? null : null; };
const has = (k: string): boolean => argv.includes(k);
const force = has('--force');
const out = resolve(ROOT, opt('--out') ?? 'tools/race/out/replays');
const valued = new Set(['--dir', '--out', '--fetch', '--fetch-day', '--url', '--min-laps', '--max-fouroff-per-lap', '--max-contacts-per-lap', '--max-lap-spread']);
const num = (k: string): number | undefined => { const v = opt(k); return v === null ? undefined : Number(v); };

function sha(): string { try { return execSync('git rev-parse --short HEAD', { cwd: ROOT, stdio: ['ignore', 'pipe', 'ignore'] }).toString().trim(); } catch { return ''; } }

function readRecording(path: string): RaceRecording | null {
  try {
    const raw = readFileSync(path);
    const text = path.endsWith('.gz') ? gunzipSync(raw).toString('utf8') : raw.toString('utf8');
    const j = fromWire(JSON.parse(text)) as RaceRecording;
    return j && j.v === 1 && j.inputs && Array.isArray(j.inputs.rows) && j.live ? j : null;
  } catch { return null; }
}

async function replayOne(rec: RaceRecording, currentSha: string): Promise<ReplayResult> {
  const assets = await loadSimAssets(rec.trackId, 'probe_gt');
  return replayRecording(rec, { assets, pace: loadPace(rec.trackId), identity: loadIdentityJson(rec.trackId), currentSha, force, analyse: true });
}

async function tokenFetch(url: string): Promise<Response> {
  const token = process.env.RACES_FETCH_TOKEN;   // read here and only sent as a header: never printed
  if (!token) throw new Error('set RACES_FETCH_TOKEN in the environment (the fetch token the deployment was given)');
  return fetch(url, { headers: { 'X-Fetch-Token': token } });
}

async function fetchRecordings(): Promise<string[]> {
  const base = opt('--url');
  if (!base) throw new Error('--fetch needs --url https://<host>/api/races');
  mkdirSync(resolve(out, 'recordings'), { recursive: true });
  const ids: string[] = [];
  const day = opt('--fetch-day'), one = opt('--fetch');
  if (one) ids.push(one);
  if (day) {
    const r = await tokenFetch(`${base}?day=${encodeURIComponent(day)}`);
    if (!r.ok) throw new Error(`listing ${day}: HTTP ${r.status}`);
    for (const x of ((await r.json()) as { recordings: { id: string }[] }).recordings) ids.push(x.id);
  }
  const files: string[] = [];
  for (const id of ids) {
    const f = resolve(out, 'recordings', `${id}.json`);
    if (!existsSync(f)) {
      const r = await tokenFetch(`${base}?id=${encodeURIComponent(id)}`);
      if (!r.ok) { console.error(`${id}: HTTP ${r.status}`); continue; }
      writeFileSync(f, await r.text());
    }
    files.push(f);
  }
  return files;
}

function inputs(): string[] {
  const dir = opt('--dir');
  if (dir) return readdirSync(resolve(ROOT, dir)).filter((f) => /\.json(\.gz)?$/.test(f)).sort().map((f) => resolve(ROOT, dir, f));
  return argv.filter((a, i) => !a.startsWith('--') && !valued.has(argv[i - 1] ?? ''));
}

async function main(): Promise<void> {
  mkdirSync(out, { recursive: true });
  let files = inputs();
  if (opt('--fetch') || opt('--fetch-day')) files = [...(await fetchRecordings()), ...files];
  if (!files.length) { console.error('nothing to replay: give a recording, --dir <dir>, --fetch <id> --url <api>, or --fetch-day <day> --url <api>'); process.exit(1); }
  const cur = sha();
  const done: RaceFile[] = [];
  let flagged = 0;
  for (const f of files) {
    const name = basename(f).replace(/\.json(\.gz)?$/, '');
    const cache = resolve(out, `${name}.json`);
    let rf: RaceFile | null = null;
    if (has('--dir') && !has('--rerun') && existsSync(cache)) { try { const c = JSON.parse(readFileSync(cache, 'utf8')) as RaceFile; if (c.analysis && c.check) rf = c; } catch { /* re-run */ } }
    if (!rf) {
      const rec = readRecording(f);
      if (!rec) { console.error(`${name}: not a race recording (skipped)`); continue; }
      const r = await replayOne(rec, cur);
      console.log(`${name}: ${r.check.ok ? 'reproduced exactly' : 'FLAGGED'} (${r.steps} steps in ${r.wallS.toFixed(0)} s)`);
      for (const m of [...r.check.mismatches, ...r.check.problems]) console.log(`  ${m}`);
      if (!r.analysis) { flagged++; continue; }
      rf = { name, check: r.check, analysis: r.analysis };
      writeFileSync(cache, JSON.stringify(rf));
      writeFileSync(resolve(out, `${name}.md`), raceMd(name, r.check, r.analysis));
    } else console.log(`${name}: cached`);
    if (!rf.check.ok) flagged++;
    done.push(rf);
  }
  if (has('--dir') || done.length > 1) {
    const md = aggregateMd(done, { minLaps: num('--min-laps'), ...(num('--max-fouroff-per-lap') !== undefined ? { maxFourOffPerLap: num('--max-fouroff-per-lap')! } : {}), ...(num('--max-contacts-per-lap') !== undefined ? { maxContactsPerLap: num('--max-contacts-per-lap')! } : {}), ...(num('--max-lap-spread') !== undefined ? { maxLapSpread: num('--max-lap-spread')! } : {}), aborted: has('--aborted') });
    writeFileSync(resolve(out, 'aggregate.md'), md);
    console.log(`\naggregate: ${resolve(out, 'aggregate.md')}`);
  }
  console.log(`\n${done.length} analysed, ${flagged} flagged; reports in ${out}`);
  if (flagged) process.exitCode = 2;
}

main().catch((e) => { console.error(String((e as Error)?.message ?? e)); process.exit(1); });
