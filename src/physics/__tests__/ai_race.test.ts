// RaceDirector: formation → seeded green, lap counting / positions, determinism, a 45-car race, cost.
import { expect, test } from 'vitest';
import { director, pack } from './ai_fixture';

test('formation → green at a seeded random moment inside the window, never revealed before', () => {
  const times: number[] = [];
  for (const seed of [1, 2, 3, 4]) {
    const d = director({ seed, maxAi: 3 }, { walls: false });
    expect(Object.keys(d).some((k) => /green/i.test(k))).toBe(false);
    let tGreen = NaN;
    while (d.time < 31) {
      d.step(0.001);
      const h = d.hud();
      if (h.phase === 'formation') { expect(h.flag === 'yellow' || h.flag === 'black').toBe(true); expect(JSON.stringify(h)).not.toMatch(/green/i); }
      if (h.phase === 'green') { tGreen = d.time; break; }
    }
    expect(tGreen).toBeGreaterThanOrEqual(5);
    expect(tGreen).toBeLessThanOrEqual(30);
    times.push(tGreen);
    // same seed → same moment
    const d2 = director({ seed, maxAi: 3 }, { walls: false });
    while (d2.phase === 'formation') d2.step(0.001);
    expect(d2.time).toBe(tGreen);
  }
  expect(new Set(times.map((t) => t.toFixed(3))).size).toBeGreaterThan(1);
}, 60000);

test('lap counting, positions and results (5 cars, 2 laps)', () => {
  const d = director({ seed: 3, laps: 2, maxAi: 4, playerAi: true, greenWindow: [5, 6] });
  const L = d.line.L;
  while (d.phase !== 'finished' && d.time < 600) {
    d.step(0.001);
    if (Math.round(d.time * 1000) % 5000 === 0) {
      const h = d.hud();
      expect(h.position).toBeGreaterThanOrEqual(1);
      expect(h.position).toBeLessThanOrEqual(5);
      expect(h.carsTotal).toBe(5);
      if (h.gapAhead) expect(h.gapAhead.metres).toBeGreaterThanOrEqual(0);
      if (h.gapBehind) { expect(h.gapBehind.metres).toBeGreaterThanOrEqual(0); expect(h.gapBehind.seconds).toBeGreaterThanOrEqual(0); }
    }
  }
  expect(d.phase).toBe('finished');
  const res = d.getResults()!;
  expect(res.map((r) => r.position)).toEqual([1, 2, 3, 4, 5]);
  for (let k = 1; k < res.length; k++) expect(res[k].metres).toBeLessThanOrEqual(res[k - 1].metres);
  expect(res[0].laps).toBeGreaterThanOrEqual(2);
  expect(res[0].lapsCompleted).toBe(2);
  for (const r of res) expect(r.lapsCompleted).toBe(Math.floor(r.metres / L));
  // lap times were recorded and are sane against each car's target
  for (const c of d.cars) {
    expect(Number.isFinite(c.bestLap)).toBe(true);
    expect(c.bestLap / c.paceTarget).toBeGreaterThan(0.97);
    // 1.45 since the pit-exit cone cap (RaceLine.restrictLeft): no passing left on the front straight, so a car stuck
    // behind a slower one for 2 laps measured 1.39 (was 1.3 with the lane open; a seeded run-wide costs ~15 %)
    expect(c.bestLap / c.paceTarget).toBeLessThan(1.45);
  }
  const playerRow = res.find((r) => r.player)!;
  expect(playerRow.number).toBe('619');
}, 120000);

test('determinism: same seed → identical race state after 20 s with the full field', () => {
  const run = (seed: number) => {
    const d = director({ seed, playerAi: true });
    while (d.time < 20) d.step(0.001);
    return JSON.stringify(d.poses().map((p) => [p.number, p.state.pos, p.state.quat, p.state.rpm])) + JSON.stringify(d.hud());
  };
  const a = run(11), b = run(11), c = run(12);
  expect(a).toBe(b);
  expect(a).not.toBe(c);
}, 120000);

test('45 cars, 3 laps: no NaN, nobody stuck, every car within 20 % of its pace', () => {
  const d = director({ seed: 1, laps: 3, playerAi: true });
  const U0 = d.cars.map((c) => c.U);
  let maxDepth = 0;
  // the pit-exit cone line (driver's left, s0..s1): no AI car may be left of it
  const cones = pack().scenery.pit_exit_cones as { s0: number; s1: number; pts: number[][] };
  const coneLat: [number, number][] = cones.pts.map((p) => { const q = d.line.project(p[0], p[1]); return [q.s, q.lateral] as [number, number]; }).sort((a, b) => a[0] - b[0]);
  const latAt = (s: number) => { let lo = 0, hi = coneLat.length - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (coneLat[m][0] <= s) lo = m; else hi = m; } const [sa, la] = coneLat[lo], [sb, lb] = coneLat[hi]; return la + (sb > sa ? (s - sa) / (sb - sa) : 0) * (lb - la); };
  const coneHits = new Map<string, number>();
  let k = 0;
  while (d.phase !== 'finished' && d.time < 700) {
    d.step(0.001);
    if (++k % 20 === 0) for (const c of d.cars) { const s = d.traffic.s[c.idx]; if (s >= cones.s0 && s <= cones.s1 && d.traffic.lat[c.idx] > latAt(s) + 0.2) coneHits.set(c.number, (coneHits.get(c.number) ?? 0) + 1); }
    for (let k = 0; k < d.contactCount; k++) maxDepth = Math.max(maxDepth, d.contacts[k].depth);
    if (d.phase === 'chequered' && d.time > 400) break;
  }
  expect(d.getResults()).not.toBeNull();
  const L = d.line.L;
  const worst = [...d.cars].filter((c) => Number.isFinite(c.bestLap)).sort((a, b) => b.bestLap / b.paceTarget - a.bestLap / a.paceTarget).slice(0, 4);
  console.log('slowest vs pace: ' + worst.map((c) => `#${c.number} ${(c.bestLap / c.paceTarget).toFixed(3)} (mishaps ${c.mishaps}, recov ${c.recoveries}, stint ${c.stint}, target ${c.paceTarget.toFixed(1)})`).join('; '));
  for (const c of d.cars) {
    const st = c.vehicle.state;
    expect(c.vehicle.nanResets).toBe(0);
    for (const x of [...st.pos, ...st.quat, ...st.vel]) expect(Number.isFinite(x)).toBe(true);
    expect(st.launched).toBe(false);
    expect(c.recoveries).toBeLessThanOrEqual(3);   // seed 1, shuffled grid: one car needs 3 marshal resets
    expect(c.U).toBeGreaterThan(1.5 * L);                       // everybody kept racing
    // in traffic: best lap (when the car completed a timed lap) against the target, and the average speed over the
    // whole race (formation included) against the target's
    // a seeded loss of control in traffic costs ~15-30 % of a lap (cautious rejoin), so a car that had one gets a looser bound
    // 1.4 / 0.65 (seed 1, shuffled grid formed behind the line, lane model, NOTES.md "Racecraft (the lane model) and mishaps"):
    // measured worst best lap 1.37 (#169) and worst average speed 0.67 (#41, a 1:57 car that starts near the back and has
    // to pass ~40 slower cars in 3 laps through lanes that must be free); the old per-tick driver on the same grid:
    // 1.46 / 0.70 with 4-8x the contacts. Not tightened toward 1.2: passes in dense lap-1 traffic still take too long.
    // 1.55 / 1.65 since the pit-exit cone cap closed the front-straight left lane (measured 1.50 for #41, no mishap)
    if (Number.isFinite(c.bestLap)) expect(c.bestLap / c.paceTarget).toBeLessThan(c.mishaps > 0 ? 1.65 : 1.55);
    expect((c.U - U0[c.idx]) / d.time / (L / c.paceTarget)).toBeGreaterThan(c.mishaps > 0 ? 0.6 : 0.65);
  }
  console.log(`45-car race: ${d.recoveries} recoveries, ${d.mishapLog.length} mishaps, max contact depth ${maxDepth.toFixed(3)} m, contacts ${d.collider.totalContacts}`);
  expect(maxDepth).toBeLessThan(0.5);
  console.log(`pit-exit cones crossed (car: 20 ms samples left of the line): ${[...coneHits].map(([n, v]) => `#${n} ${v} (mishaps ${d.cars.find((c) => c.number === n)!.mishaps}, recoveries ${d.cars.find((c) => c.number === n)!.recoveries})`).join(', ') || 'none'}`);
  // a car that lost control (a seeded run-wide at T11 lands in the pit-exit lane) may cross; a car in control never does
  for (const n of coneHits.keys()) { const c = d.cars.find((x) => x.number === n)!; expect(c.mishaps + c.recoveries).toBeGreaterThan(0); }
}, 300000);

test('cost: whole field step at 1 kHz (AI physics 500 Hz) under 15 % of real time', () => {
  const d = director({ seed: 5, playerAi: true, greenWindow: [5, 6] });
  while (d.time < 8) d.step(0.001); // warm up, racing
  // baseline in the same conditions (vitest runs files in parallel): one Vehicle step on the real surface
  const base = d.player.vehicle;
  const t00 = performance.now();
  for (let i = 0; i < 4000; i++) base.step(d.player.driver!.input, d.player.surface, 0.001);
  const usCar = ((performance.now() - t00) * 1000) / 4000;
  const n = 4000;
  const t0 = performance.now();
  for (let i = 0; i < n; i++) d.step(0.001);
  const us = ((performance.now() - t0) * 1000) / n;
  console.log(`field step: ${us.toFixed(1)} µs per 1 ms step (${(us / d.cars.length).toFixed(2)} µs per car, ${(us / 10).toFixed(1)} % of real time); one Vehicle step ${usCar.toFixed(2)} µs`);
  // ~46 cars at 500 Hz + the player at 1 kHz + AI, contacts, bookkeeping: well under 46 Vehicle steps
  expect(us).toBeLessThan(70 * usCar);
  // absolute: ~60 µs (6 %) measured on an unloaded M3 with tools/race/sim_race.ts; generous here because
  // vitest runs the files in parallel (and other work may share the machine)
  expect(us).toBeLessThan(800);
}, 60000);
