// Field pace on any registered circuit: the Laguna field (identity.json, the 45 cars of MyLaps session 12975608) with
// each car's targets from that circuit's own Lemons race where the car raced it, else a placeholder. The per-track
// form of tools/race/pace_sonoma.ts (which stays as Sonoma's record; this tool reproduces its output).
//
//   npx tsx tools/race/pace_track.ts --track <id> --session <MyLaps session id> [--data tools/race/data/<id>] [--match]
//       [--label <name in the notes>] [--when 'in March 2026'] [--source <the file's source line>] [--quantile <q>]
//       writes public/cars/field/<id>/pace.json (TRACKS[id].pace), then: npx tsx tools/race/calibrate_field.ts --track <id>
//   --match   (re)write <data>/match_laguna.json from the classification: a Laguna car is matched to an entrant of the
//             circuit's race when the normalised team names are equal (lower case, letters and digits only); a team with
//             two entrants is matched by number, else it is not matched. No fuzzy matches (Buttonwillow: "TPF Racing" vs
//             "PH Racing" scored 0.82 and is a different team).
//
//
//   npx tsx tools/race/pace_track.ts --track <id> --session <MyLaps session id> --own [--data tools/race/data/<id>]
//       [--label <name>] [--source <the file's source line>] [--quantile <q>]
//       The circuit's OWN field (Buttonwillow, 22 Oct 2026): every entrant of the session becomes a car with its own
//       pace and stints under tools/race/pace.ts's rules (tools/race/pace_rules.ts: the official best is the 0.97 floor),
//       aggression = aggressionData(track, number, class) as pace.ts (L1 K3: the data tier, else aggressionFor); an entrant with no lap in the session (a non-starter) is
//       left out and named in `source` (Buttonwillow: #89, #6, #43, #101, #222); the player's car (#619) keeps a reference row
//       (`player: true`, its real grid slot, never an AI car) as in Laguna's file. Every car carries `id`: its number,
//       except a number that belongs to a DIFFERENT Laguna car (public/cars/field/pace.json numbers, not `same` in
//       match_laguna.json) gets "<number>_<id>" (Buttonwillow: "0_bw"), so its identity / model never resolve to the
//       Laguna car's. When the track's own identity.json exists its row for a number decides the id (a matched team
//       may race a different car: Buttonwillow #670 "670_bw") and the model (`model_id`, else `laguna_number` of a
//       renumbered car). Fitted scales of an earlier file are kept per id and stint while ai_version and the target match.
//
// Inputs in <data>: sessions_<session>_classification.json and laps/posNNN.json (MyLaps / Speedhive event results
// API, eventresults/sessions/<session>/classification and .../lapdata/<position>/laps), match_laguna.json.
// --quantile <q> (both forms, default 0.5 = the median, which is every public pace file): the target of a car and of
// each stint is the quantile q of its clean laps (tools/race/pace_rules.ts quantile; the outlier cuts still reference the
// median). The median of a race stint already carries the real race's traffic and the sim adds its own on top (owner,
// 27 Oct 2026: "They don't seem very fast, and I have no problem passing them."); a lower q anchors the solo lap nearer
// the car's free pace. The header records pace: { stat: "quantile", q }.
// Rules (tools/race/pace.ts): target = median (quantile q) of green non-pit laps after dropping those over 1.3 x the raw median;
// stints between pit stops, out laps dropped, laps over 1.2 x the stint median or 1.3 x the car median or under
// 0.97 x the best dropped, at least 5 laps. A car that did not race the circuit keeps a placeholder: its Laguna target x
// the AI Probe's solo-lap ratio <id> / Laguna at scale 1, marked in `targetSource`.
import { readFileSync, writeFileSync, readdirSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { loadTrackPack, loadProbeJson, loadPace, pacePath, trackArg, ROOT } from './load';
import { carPace, quantile, parseLap as officialLap } from './pace_rules';
import { aggressionData } from './aggression_tiers';
import { runSolo } from '../../src/physics/ai/solo';
import { TRACKS } from '../../src/scoreboard/config';
import { AI_VERSION, type PaceCar, type PaceJson, type PaceStint } from '../../src/physics/ai/field';

const ARGV = process.argv.slice(2);
const arg = (k: string) => { const i = ARGV.indexOf(`--${k}`); return i >= 0 ? ARGV[i + 1] : undefined; };
const TRACK = trackArg(ARGV);
const SESSION = arg('session');
if (!SESSION) throw new Error('--session <MyLaps session id> required');
const DATA = resolve(ROOT, arg('data') ?? `tools/race/data/${TRACK}`);
const MIN_STINT_LAPS = 5;
const Q = arg('quantile') !== undefined ? Number(arg('quantile')) : 0.5;
if (!(Q >= 0 && Q <= 1)) throw new Error('--quantile: a number from 0 to 1');
const parseLap = (s: string) => s.split(':').map(Number).reduce((t, p) => t * 60 + p, 0);
const median = (a: number[]) => { const b = [...a].sort((x, y) => x - y); const n = b.length; return n ? (n % 2 ? b[(n - 1) / 2] : 0.5 * (b[n / 2 - 1] + b[n / 2])) : NaN; };
const robustSigma = (a: number[]) => { const m = median(a); return 1.4826 * median(a.map((t) => Math.abs(t - m))); };
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9]/g, '');

const src = loadPace('laguna_seca');
const matchPath = resolve(DATA, 'match_laguna.json');
if (ARGV.includes('--match') || !existsSync(matchPath)) {
  const cls = JSON.parse(readFileSync(resolve(DATA, `sessions_${SESSION}_classification.json`), 'utf8'));
  const rows: { name: string; startNumber: string }[] = cls.rows;
  const cars = src.cars.map((c) => {
    const same = rows.filter((r) => norm(r.name) === norm(c.team));
    const pick = same.length === 1 ? same[0] : same.find((r) => r.startNumber === c.number);
    if (!pick) return { laguna_number: c.number, laguna_team: c.team, [`${TRACK}_number`]: null, [`${TRACK}_team`]: null, status: 'absent',
      evidence: same.length ? `${same.length} entrants of that team, none numbered ${c.number}` : 'no entrant with that normalised team name' };
    return { laguna_number: c.number, laguna_team: c.team, [`${TRACK}_number`]: pick.startNumber, [`${TRACK}_team`]: pick.name,
      status: pick.startNumber === c.number ? 'same' : 'renumbered', evidence: `exact normalised team match${pick.startNumber === c.number ? '; number matches' : ''}` };
  });
  writeFileSync(matchPath, JSON.stringify({ note: `Laguna field car (public/cars/field/identity.json numbering, MyLaps session 12975608) -> ${TRACK} entrant (MyLaps session ${SESSION}); tools/race/pace_track.ts --match`, laguna_session: 12975608, [`${TRACK}_session`]: Number(SESSION), cars }, null, 1) + '\n');
}
const match = JSON.parse(readFileSync(matchPath, 'utf8'));
const numKey = `${TRACK}_number`, teamKey = `${TRACK}_team`;

const byNr = new Map<string, any>();
for (const f of readdirSync(resolve(DATA, 'laps'))) {
  const j = JSON.parse(readFileSync(resolve(DATA, 'laps', f), 'utf8'));
  byNr.set(String(j.lapDataInfo.participantInfo.startNr), j);
}
function ownPace(nr: string) {
  const j = byNr.get(nr);
  if (!j) throw new Error(`no ${TRACK} lap file for #${nr}`);
  const laps = j.laps.map((l: any) => {
    const st: string[] = Array.isArray(l.status) ? l.status : [l.status];
    const t = parseLap(l.lapTime);
    return { nr: l.lapNr, t, pit: !!l.inPit, ok: !l.inPit && st.length > 0 && st.every((x) => x === 'GREEN') && Number.isFinite(t) && t > 60 };
  });
  const green = laps.filter((l: any) => l.ok).map((l: any) => l.t);
  if (!green.length) return { targetLap: NaN, bestLap: NaN, sigma: NaN, greenLaps: 0, stints: [] as PaceStint[] };
  const m0 = median(green);
  const clean = green.filter((t: number) => t <= 1.3 * m0);
  const best = Math.min(...clean);
  const stints: PaceStint[] = [];
  let run: number[] = [], first = -1, afterPit = true;
  const flush = () => {
    if (run.length) {
      const sm = median(run);
      const keep = run.filter((t) => t <= 1.2 * sm && t <= 1.3 * m0 && t >= 0.97 * best);
      if (keep.length >= MIN_STINT_LAPS) stints.push({ index: stints.length, laps: keep.length, firstLap: first, targetLap: +quantile(keep, Q).toFixed(3), bestLap: +Math.min(...keep).toFixed(3), sigma: +robustSigma(keep).toFixed(3) });
    }
    run = []; first = -1;
  };
  for (const l of laps) {
    if (l.pit) { flush(); afterPit = true; continue; }
    if (afterPit) { afterPit = false; first = l.nr; continue; }
    if (first < 0) first = l.nr;
    if (l.ok) run.push(l.t);
  }
  flush();
  return { targetLap: +quantile(clean, Q).toFixed(3), bestLap: +best.toFixed(3), sigma: +robustSigma(clean).toFixed(3), greenLaps: clean.length, stints };
}

/** --own: the circuit's own field from its session (see the header). */
function ownField(): void {
  const PLAYER = '619';
  const cls = JSON.parse(readFileSync(resolve(DATA, `sessions_${SESSION}_classification.json`), 'utf8'));
  const lagunaNumbers = new Set(src.cars.map((c) => c.number));
  const sameCar = new Set(match.cars.filter((m: any) => m.status === 'same' && m[numKey] === m.laguna_number).map((m: any) => String(m.laguna_number)));
  // the event's id suffix (Buttonwillow "_bw", Sonoma "_sp" as tools/race/data/sonoma/ids.json); another track: its id
  const SUFFIX = ({ buttonwillow: 'bw', sonoma: 'sp', mid_ohio: 'mo' } as Record<string, string>)[TRACK] ?? TRACK;
  const idFor = (n: string) => (lagunaNumbers.has(n) && !sameCar.has(n) ? `${n}_${SUFFIX}` : n);
  // the track's own identity.json (TRACKS[id].identity), when written, is the authority on ids: its row for a number
  // gives the id (Buttonwillow #670 is a different car from Laguna's #670 though the team matches: "670_bw") and the
  // model (`model_id`, else `laguna_number` when the car was renumbered: #6 Tinyvette = Laguna #8 -> model_id "8")
  const IDENT_REL = process.env.FIELD_TRACK === TRACK && process.env.FIELD_IDENTITY ? process.env.FIELD_IDENTITY : TRACKS[TRACK].identity;   // FIELD_IDENTITY: see load.ts pacePath
  const ownIdent = IDENT_REL ? resolve(ROOT, 'public', IDENT_REL) : null;
  const identRows: any[] = ownIdent && existsSync(ownIdent) ? (([j]) => (Array.isArray(j) ? j : j.cars ?? []))([JSON.parse(readFileSync(ownIdent, 'utf8'))]) : [];
  const identBy = new Map(identRows.filter((r) => r?.number != null).map((r) => [String(r.number), r]));
  const fromIdent: string[] = [];
  const prev: PaceJson | null = existsSync(pacePath(TRACK)) ? JSON.parse(readFileSync(pacePath(TRACK), 'utf8')) : null;
  const keepScales = prev?.ai_version === AI_VERSION;
  const prevBy = new Map((prev?.cars ?? []).map((c) => [c.id ?? c.number, c]));
  const out: PaceCar[] = [];
  const noLaps: string[] = [], dropped: string[] = [];
  for (const r of cls.rows) {
    const number = String(r.startNumber);
    const j = byNr.get(number);
    if (!j) throw new Error(`no ${TRACK} lap file for #${number}`);
    // an entrant with no timed lap in the session (did not start) has no pace of its own: left out, named in `source`
    if (!j.laps.length || !(r.numberOfLaps > 0)) { noLaps.push(number); continue; }
    const row = identBy.get(number);
    // an entrant the track's own identity.json leaves out (the owner dropped it: Sonoma d08, 23 Oct 2026, #122 / #68 /
    // #55 / #299 never found, no placeholder cars in the field) is not raced; the player's reference row is kept
    if (identRows.length && !row && number !== PLAYER) { dropped.push(number); continue; }
    const id = row?.id != null ? String(row.id) : idFor(number);
    if (id !== idFor(number)) fromIdent.push(`#${number} ${id} (match rule: ${idFor(number)})`);
    const lagN = row?.laguna_number != null ? String(row.laguna_number) : null;
    const model_id = row?.model_id != null ? String(row.model_id) : lagN && lagN !== number && lagN !== id ? lagN : undefined;
    const p = prevBy.get(id);
    const same = p?.number === number;
    const pc = carPace(j.laps, officialLap(r.bestTime), (k, target) => {
      const old = keepScales && same ? p?.stints?.[k] : undefined;
      return old && old.targetLap === target && old.scale !== undefined ? { scale: old.scale, achievedLap: old.achievedLap } : null;
    }, Q);
    out.push({
      id, ...(model_id ? { model_id } : {}), number, team: r.name, class: r.resultClass, grid: j.lapDataInfo.participantInfo.startPos, finish: r.position,
      classFinish: r.positionInClass, lapsCompleted: r.numberOfLaps,
      greenLaps: pc.greenLaps, targetLap: pc.targetLap, bestLap: pc.bestLap, sigma: pc.sigma,
      aggression: aggressionData(TRACK, number, r.resultClass),   // (L1 K3) the data tier, else the seeded draw
      ...(number === PLAYER ? { player: true } : {}),
      ...(keepScales && same && p?.scale !== undefined && p.targetLap === pc.targetLap ? { scale: p.scale, achievedLap: p.achievedLap } : {}),
      stints: pc.stints,
    });
  }
  // the player's car did not race this event (Sonoma, March 2026): its reference row from the previous file is kept
  // (marked in `targetSource`) so self-play's AI-driven player car keeps a calibrated pace; never an AI car
  let playerKept = false;
  if (!out.some((c) => c.number === PLAYER)) {
    const pp = prev?.cars.find((c) => c.player && c.number === PLAYER);
    if (pp) {
      const { resolved: _r, ...rest } = pp as PaceCar & { resolved?: unknown };
      out.push({ ...rest, grid: out.length + 1, targetSource: (pp as any).targetSource?.startsWith('KEPT') ? (pp as any).targetSource
        : `KEPT from the previous ${TRACK} pace file: #${PLAYER} did not race MyLaps session ${SESSION}; ${(pp as any).targetSource ?? 'its own row'}` } as PaceCar);
      playerKept = true;
    }
  }
  out.sort((a, b) => a.grid - b.grid);
  const renamed = out.filter((c) => c.id != null && c.id !== c.number).map((c) => c.id!);
  const label = arg('label') ?? TRACK;
  const ai = out.filter((c) => !c.player);
  const file: PaceJson = {
    ai_version: AI_VERSION,
    source: arg('source') ?? `MyLaps session ${SESSION} (${label}): ${out.length - (playerKept ? 1 : 0)} of its ${cls.rows.length} entrants from their own laps (${ai.length} AI cars + the player's `
      + `#${PLAYER} as a reference row${playerKept ? ' kept from the previous file (it did not race this event)' : ''}; ${noLaps.length ? `left out with no lap in the session: ${noLaps.map((n) => '#' + n).join(', ')}` : 'none left out'}`
      + `${dropped.length ? `; left out with no row in ${IDENT_REL} (dropped by the owner): ${dropped.map((n) => '#' + n).join(', ')}` : ''}), `
      + `tools/race/pace.ts rules (tools/race/pace_rules.ts); ids from ${identRows.length ? IDENT_REL : 'the match rule'}: numbers except ${renamed.length} of a different `
      + `car at Laguna: ${renamed.join(', ')}; tools/race/pace_track.ts --own`,
    notes: `Ids: a number that is a different car at Laguna gets "<n>_${SUFFIX}" (${dirname(matchPath).replace(ROOT + '/', '')}/match_laguna.json not 'same'`
      + `${fromIdent.length ? `, overridden by ${IDENT_REL}: ${fromIdent.join(', ')}` : ''}). `
      + (noLaps.length ? `Left out: ${noLaps.map((n) => `#${n}${identBy.get(n)?.id && identBy.get(n).id !== n ? ` (${identBy.get(n).id})` : ''}`).join(', ')}, entrants with no lap in the session `
        + `(classified ${noLaps.map((n) => cls.rows.find((r: any) => String(r.startNumber) === n).position).join(', ')} with 0 laps${(() => {
        const odd = noLaps.filter((n) => cls.rows.find((r: any) => String(r.startNumber) === n).numberOfLaps > 0);
        return odd.length ? `; ${odd.map((n) => `#${n} is classified with ${cls.rows.find((r: any) => String(r.startNumber) === n).numberOfLaps} laps but its lap file has none`).join(', ')}` : '';
      })()}): with no clean laps there is no pace or stint to draw, `
        + `the rule of tools/race/pace.ts (a car's pace is its own clean laps) has nothing to build them from. Their identity rows stay in identity.json.` : 'No entrant left out.')
      + (dropped.length ? ` Also left out: ${dropped.map((n) => '#' + n).join(', ')}, entrants with no row in ${IDENT_REL} (dropped by the owner: no placeholder cars in the field).` : '')
      + (playerKept ? ` #${PLAYER} did not race this event: its reference row (player: true, never an AI car) is kept from the previous file.` : ''),
    track: TRACK,
    pace: { stat: 'quantile', q: Q },
    cars: out,
  };
  mkdirSync(dirname(pacePath(TRACK)), { recursive: true });
  writeFileSync(pacePath(TRACK), JSON.stringify(file, null, 1) + '\n');
  const noStint = ai.filter((c) => !(c.stints ?? []).length);
  console.log(`${out.length} cars (${ai.length} AI), ${ai.reduce((a, c) => a + (c.stints?.length ?? 0), 0)} AI stints; ${noStint.length} AI cars without a stint `
    + `(car-level pace): ${noStint.map((c) => `#${c.number} (${c.greenLaps} green laps)`).join(', ') || 'none'}`);
  if (fromIdent.length) console.log(`ids from ${IDENT_REL}: ${fromIdent.join(', ')}`);
  console.log(`renamed ids: ${renamed.join(', ')}; left out (no laps): ${noLaps.join(', ') || 'none'}; left out (no identity row): ${dropped.join(', ') || 'none'}${playerKept ? `; #${PLAYER} reference row kept from the previous file` : ''}`);
  console.log(`wrote ${pacePath(TRACK)}`);
}

if (ARGV.includes('--own')) { ownField(); process.exit(0); }

const probe = loadProbeJson();
const solo = (id: string) => { const p = loadTrackPack(id); const r = runSolo(p.line, p.surface, probe, null, 1, 2); return r.laps[1]; };
const a = solo('laguna_seca'), b = solo(TRACK), k = b / a;
const r3 = (x: number) => +(x * k).toFixed(3);
const label = arg('label') ?? TRACK;
// the race in the placeholder note (Sonoma's record: 'in March 2026'); default the session
const when = arg('when') ?? `in session ${SESSION}`;
let real = 0;
const cars = src.cars.map((c) => {
  const m = match.cars.find((r: any) => r.laguna_number === c.number);
  const p = m?.[numKey] && byNr.has(String(m[numKey])) ? ownPace(m[numKey]) : null;
  if (p && p.greenLaps > 0) {
    real++;
    return { ...c, ...p, scale: undefined, achievedLap: undefined, resolved: undefined,
      targetSource: `${label} #${m[numKey]} ${m[teamKey]} (MyLaps ${SESSION}; ${m.status}: ${m.evidence.split(';')[0]})` };
  }
  return { ...c, targetLap: r3(c.targetLap), bestLap: r3(c.bestLap), sigma: +(c.sigma * k).toFixed(3), scale: undefined, achievedLap: undefined, resolved: undefined,
    stints: (c.stints ?? []).map((s) => ({ ...s, targetLap: r3(s.targetLap), bestLap: r3(s.bestLap), sigma: +(s.sigma * k).toFixed(3), scale: undefined, achievedLap: undefined })),
    targetSource: `PLACEHOLDER: Laguna target x ${k.toFixed(4)} (did not race ${label} ${when}${m ? '; ' + m.status : ''}${m?.[numKey] ? `; matched #${m[numKey]} has no green laps` : ''})` };
});
const out: PaceJson = {
  ai_version: AI_VERSION,
  source: arg('source') ?? `${real} cars from their own laps at ${label} (MyLaps session ${SESSION}; ${dirname(matchPath).replace(ROOT + '/', '')}/match_laguna.json), `
    + `${cars.length - real} as Laguna (session 12975608) x ${k.toFixed(4)} (AI Probe solo-lap ratio, placeholder); tools/race/pace_track.ts`,
  track: TRACK,
  pace: { stat: 'quantile', q: Q },
  cars: cars as PaceJson['cars'],
};
mkdirSync(dirname(pacePath(TRACK)), { recursive: true });
writeFileSync(pacePath(TRACK), JSON.stringify(out, null, 1) + '\n');
console.log(`AI Probe solo laps: Laguna ${a.toFixed(2)} s, ${TRACK} ${b.toFixed(2)} s, ratio ${k.toFixed(4)}; ${real} cars from ${TRACK} laps; wrote ${pacePath(TRACK)}`);
for (const c of cars) if (!c.targetSource.startsWith('PLACEHOLDER')) console.log(`  #${c.number.padEnd(4)} target ${c.targetLap.toFixed(2)} (placeholder would be ${(src.cars.find((x) => x.number === c.number)!.targetLap * k).toFixed(2)})  ${c.targetSource}`);
