// Cross-engine replay (docs/determinism.md section 5): six hot laps recorded in WebKit (Playwright 1.61.1's WebKit 26.5,
// the engine of Safari and every iPhone browser) on the built game by tools/determinism/browser_trace.mts, replayed here
// with the server's code. Every lap time and the final state must be WebKit's to the bit.
// Re-recorded 26 Oct 2026 for the cheaper-pow physics (docs/determinism.md section 9): the same trace and bits came out of
// WebKit, Chrome and Firefox. The maths is the game's own on every host, so the bits hold on any machine.
import { readFileSync } from 'node:fs';
import { gunzipSync } from 'node:zlib';
import { describe, expect, test } from 'vitest';
import { HotlapSim } from '../sim';
import { SAMPLE_EVERY } from '../config';
import type { InputTrace } from '../types';
import { lagunaAssets } from './fixtures';

interface Recorded { engine: string; ua: string; laps: { n: number; time: number; valid: boolean; bits: string }[]; state: string[]; trace: InputTrace }
const rec = JSON.parse(gunzipSync(readFileSync(new URL('./fixtures/webkit_laguna_6.json.gz', import.meta.url))).toString('utf8')) as Recorded;
const f = new Float64Array(1), b = new Uint8Array(f.buffer);
const hex = (x: number) => { f[0] = x; return Buffer.from(b).toString('hex'); };

describe('a WebKit trace replays on the server to the bit', () => {
  test(`${rec.engine}: six laps and the final state`, () => {
    const t = rec.trace;
    expect(t.track).toBe('laguna_seca');
    // replayTrace's loop (src/scoreboard/replay.ts) without its 720 s cap: six autopilot laps take 860 s
    const sim = new HotlapSim(lagunaAssets(), { record: false, ref: t.ref[0]?.[1] ?? null });
    const laps: { n: number; time: number; valid: boolean }[] = [];
    let ri = 0, fi = 0;
    while (sim.stepIndex < t.steps + 1000) {
      const k = sim.stepIndex;
      if (k % SAMPLE_EVERY === 0) {
        while (fi < t.ref.length && t.ref[fi][0] <= k) { sim.replayRef(t.ref[fi][1]); fi++; }
        if (fi === 0) sim.replayRef(null);
        while (ri + 1 < t.rows.length && t.rows[ri + 1][0] <= k) ri++;
        sim.applyRow(t.rows[ri], t.rows[ri][0] === k);
      }
      const ev = sim.advance();
      if (ev && ev !== 'start') { laps.push(ev); if (ev.n === 6) break; }
    }
    expect(laps.map((l) => `${l.n} ${hex(l.time)} ${l.valid}`)).toEqual(rec.laps.map((l) => `${l.n} ${l.bits} ${l.valid}`));
    const s = sim.vehicle.state;
    const st = [...s.pos, ...s.quat, ...s.vel, ...s.angVel, s.rpm, s.gear, s.speed, sim.simTime, sim.s, sim.stepIndex];
    for (const w of s.wheels) st.push(...w.pos, w.spinAngle, w.steer, w.compression, w.omega, w.slipRatio, w.slipAngle, w.load);
    expect(st.map(hex)).toEqual(rec.state);
  }, 60000);
});
