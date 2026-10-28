// Sonoma field pace: the Laguna field (identity.json, the 45 cars of MyLaps session 12975608) on Sonoma.
//
//   npx tsx tools/race/pace_sonoma.ts [--quantile <q>]   # writes public/cars/field/sonoma/pace.json, then: calibrate_field.ts --track sonoma
//
// Cars that raced Sonoma's March 2026 Lemons race (tools/race/data/sonoma/match_laguna.json: matched by team and
// transponder; 143 -> 685 is NOT a match) get their targets from that race's own laps (tools/race/data/sonoma/laps,
// MyLaps session 11838772), with tools/race/pace.ts's rules: target = median of green non-pit laps after dropping those
// over 1.3 x the raw median; stints between pit stops, out laps dropped, laps over 1.2 x the stint median or 1.3 x the
// car median or under 0.97 x the best dropped, at least 5 laps. Every other car keeps the ratio placeholder: its Laguna
// target x the AI Probe's solo-lap ratio Sonoma / Laguna at scale 1 (tools/race/pace_ratio.ts), marked in `targetSource`.
import { readFileSync, writeFileSync, readdirSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { loadTrackPack, loadProbeJson, loadPace, pacePath, ROOT } from './load';
import { quantile } from './pace_rules';
import { runSolo } from '../../src/physics/ai/solo';
import { AI_VERSION, type PaceJson, type PaceStint } from '../../src/physics/ai/field';

const DATA = resolve(ROOT, 'tools/race/data/sonoma');
const MIN_STINT_LAPS = 5;
// --quantile <q> (default 0.5 = the median, as the public files): the target of a car and of each stint is the quantile q
// of its clean laps (tools/race/pace_rules.ts); a lower q anchors the solo lap nearer the car's free pace, since a race
// stint's median already carries the real race's traffic and the sim adds its own (owner, 27 Oct 2026: "They don't seem
// very fast, and I have no problem passing them."). The header records pace: { stat: "quantile", q }.
const qi = process.argv.indexOf('--quantile');
const Q = qi >= 0 ? Number(process.argv[qi + 1]) : 0.5;
if (!(Q >= 0 && Q <= 1)) throw new Error('--quantile: a number from 0 to 1');
const parseLap = (s: string) => s.split(':').map(Number).reduce((t, p) => t * 60 + p, 0);
const median = (a: number[]) => { const b = [...a].sort((x, y) => x - y); const n = b.length; return n ? (n % 2 ? b[(n - 1) / 2] : 0.5 * (b[n / 2 - 1] + b[n / 2])) : NaN; };
const robustSigma = (a: number[]) => { const m = median(a); return 1.4826 * median(a.map((t) => Math.abs(t - m))); };

const match = JSON.parse(readFileSync(resolve(DATA, 'match_laguna.json'), 'utf8'));
const byNr = new Map<string, any>();
for (const f of readdirSync(resolve(DATA, 'laps'))) {
  const j = JSON.parse(readFileSync(resolve(DATA, 'laps', f), 'utf8'));
  byNr.set(String(j.lapDataInfo.participantInfo.startNr), j);
}
function sonomaPace(nr: string) {
  const j = byNr.get(nr);
  if (!j) throw new Error(`no Sonoma lap file for #${nr}`);
  const laps = j.laps.map((l: any) => {
    const st: string[] = Array.isArray(l.status) ? l.status : [l.status];
    const t = parseLap(l.lapTime);
    return { nr: l.lapNr, t, pit: !!l.inPit, ok: !l.inPit && st.length > 0 && st.every((x) => x === 'GREEN') && Number.isFinite(t) && t > 60 };
  });
  const green = laps.filter((l: any) => l.ok).map((l: any) => l.t);
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

const probe = loadProbeJson();
const solo = (id: string) => { const p = loadTrackPack(id); const r = runSolo(p.line, p.surface, probe, null, 1, 2); return r.laps[1]; };
const a = solo('laguna_seca'), b = solo('sonoma'), k = b / a;
const src = loadPace('laguna_seca');
const r3 = (x: number) => +(x * k).toFixed(3);
let real = 0;
const cars = src.cars.map((c) => {
  const m = match.cars.find((r: any) => r.laguna_number === c.number);
  if (m?.sonoma_number) {
    real++;
    const p = sonomaPace(m.sonoma_number);
    return { ...c, ...p, scale: undefined, achievedLap: undefined, resolved: undefined,
      targetSource: `Sonoma #${m.sonoma_number} ${m.sonoma_team} (MyLaps 11838772; ${m.status}: ${m.evidence.split(';')[0]})` };
  }
  return { ...c, targetLap: r3(c.targetLap), bestLap: r3(c.bestLap), sigma: +(c.sigma * k).toFixed(3), scale: undefined, achievedLap: undefined, resolved: undefined,
    stints: (c.stints ?? []).map((s) => ({ ...s, targetLap: r3(s.targetLap), bestLap: r3(s.bestLap), sigma: +(s.sigma * k).toFixed(3), scale: undefined, achievedLap: undefined })),
    targetSource: `PLACEHOLDER: Laguna target x ${k.toFixed(4)} (did not race Sonoma in March 2026${m ? '; ' + m.status : ''})` };
});
const out: PaceJson = {
  ai_version: AI_VERSION,
  source: `${real} cars from their own laps at Sonoma (MyLaps session 11838772, 21-22 Mar 2026; tools/race/data/sonoma/match_laguna.json), `
    + `${cars.length - real} as Laguna (session 12975608) x ${k.toFixed(4)} (AI Probe solo-lap ratio, placeholder); tools/race/pace_sonoma.ts`,
  track: 'sonoma',
  pace: { stat: 'quantile', q: Q },
  cars: cars as PaceJson['cars'],
};
mkdirSync(dirname(pacePath('sonoma')), { recursive: true });
writeFileSync(pacePath('sonoma'), JSON.stringify(out, null, 1) + '\n');
console.log(`AI Probe solo laps: Laguna ${a.toFixed(2)} s, Sonoma ${b.toFixed(2)} s, ratio ${k.toFixed(4)}; ${real} cars from Sonoma laps; wrote ${pacePath('sonoma')}`);
for (const c of cars) if (!c.targetSource.startsWith('PLACEHOLDER')) console.log(`  #${c.number.padEnd(4)} target ${c.targetLap.toFixed(2)} (placeholder would be ${(src.cars.find((x) => x.number === c.number)!.targetLap * k).toFixed(2)})  ${c.targetSource}`);
