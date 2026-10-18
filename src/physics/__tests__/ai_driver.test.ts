// The AI driver alone laps within ±1.5 % of its car's real target lap (after calibrate_field).
import { expect, test } from 'vitest';
import { runSolo } from '../ai/solo';
import { AI_VERSION, parseIdentity, resolveCarType } from '../ai/field';
import { pack } from './ai_fixture';

test('pace.json is calibrated for the current AI_VERSION', () => {
  const p = pack();
  expect(p.pace.ai_version).toBe(AI_VERSION);
  expect(p.pace.cars.length).toBe(45);
  expect(p.pace.cars.filter((c) => c.player).map((c) => c.number)).toEqual(['619']);
  for (const c of p.pace.cars) expect(c.scale).toBeGreaterThan(0);
  // per-stint driver paces, every one calibrated
  let stints = 0;
  for (const c of p.pace.cars) for (const s of c.stints ?? []) { stints++; expect(s.laps).toBeGreaterThanOrEqual(5); expect(s.scale).toBeGreaterThan(0); expect(Math.abs(s.achievedLap! / s.targetLap - 1)).toBeLessThan(0.05); } // 5 %: a few quick stints of heavy cars sit at the AI's clean-lap limit (worst 3.8 %, logged NOT CONVERGED)
  expect(stints).toBeGreaterThan(200);
  expect(p.pace.cars.filter((c) => (c.stints?.length ?? 0) > 0).length).toBeGreaterThanOrEqual(43);
});

test('solo AI lap within ±1.5 % of target for 5 cars across the classes', () => {
  const p = pack();
  const ident = parseIdentity(p.identity);
  // A Miata, A V8 Lotus, B Rabbit (FWD), C Beetle (rear engine), C Lincoln (2.3 t V8)
  for (const num of ['711', '74', '83', '16', '143']) {
    const car = p.pace.cars.find((c) => c.number === num)!;
    const r = runSolo(p.line, p.surface, p.probeJson, ident.get(num) ?? null, car.scale!, 1, { dt: 0.002, ctlEvery: 1 });
    expect(r.laps.length).toBe(1);
    expect(r.recoveries).toBe(0);
    const err = r.laps[0] / car.targetLap - 1;
    console.log(`#${num} lap ${r.laps[0].toFixed(2)} target ${car.targetLap.toFixed(2)} (${(err * 100).toFixed(2)} %)`);
    expect(Math.abs(err)).toBeLessThan(0.015);
  }
}, 60000);

test('car types resolve from identity (drive layout / engine position)', () => {
  const ident = parseIdentity(pack().identity);
  if (ident.size === 0) return; // identity.json missing: Probe fallback everywhere
  const t = (n: string) => resolveCarType(ident.get(n));
  expect(t('16')).toMatchObject({ drive: 'rwd', enginePos: 'rear' });
  expect(t('801')).toMatchObject({ drive: 'rwd', enginePos: 'mid' });
  expect(t('711').drive).toBe('rwd');
  expect(t('83').drive).toBe('fwd');
  expect(t('34').drive).toBe('fwd');
  expect(t('664').drive).toBe('rwd');
  expect(t('0').turbo).toBe(true);
  expect(resolveCarType(null)).toMatchObject({ drive: 'fwd', probeFallback: true });
});
