// Player rule engine: black flags (contact at fault, four wheels off, passing under yellow), the
// Lemons escalation, the stop-and-go in the pit lane and ejection.
import { expect, test } from 'vitest';
import { input } from './helpers';
import { director } from './ai_fixture';
import { FF_SCALE, FF_TAIL_S, type RaceDirector, type RaceCar } from '../ai/race';

const brake = input({ brake: 1 });

function place(d: RaceDirector, car: RaceCar, s: number, lat: number, v: number): void {
  const pos = new Float64Array(2);
  d.line.pointAt(s, lat, pos);
  car.vehicle.reset([pos[0], pos[1], car.surface.sample(pos[0], pos[1]).z], d.line.headingAt(s), v);
  car.hint = -1;
  car.driver?.resetState();
}
function run(d: RaceDirector, seconds: number, inp = brake): void { const n = Math.round(seconds * 1000); for (let i = 0; i < n; i++) d.step(0.001, inp); }

test('four wheels off → warning, then 60 s stop-and-go; escalation to 180 s and ejection', () => {
  const d = director({ seed: 1, maxAi: 2, greenWindow: [0.01, 0.02] }, { walls: false });
  run(d, 0.1);
  expect(d.phase).toBe('green');
  const P = d.player;
  const s = 1300, edgeR = d.line.at(d.line.halfR, s);
  place(d, P, s, -(edgeR + 15), 0);
  expect(d.surface.sample(P.vehicle.state.pos[0], P.vehicle.state.pos[1]).paved).toBeFalsy();
  run(d, 0.5);
  let h = d.hud();
  expect(h.penalties.count).toBe(1);                     // 1st = warning only
  expect(h.penalties.pending).toEqual([]);
  expect(h.flag).toBe('black');
  expect(h.penalties.lastReason).toMatch(/four wheels off/);
  run(d, 1);                                             // still off: debounced, no new flag
  expect(d.hud().penalties.count).toBe(1);
  place(d, P, s, d.line.at(d.line.off, s), 0);           // back on track 2.5 s, off again
  run(d, 2.5);
  place(d, P, s, -(edgeR + 15), 0);
  run(d, 0.5);
  h = d.hud();
  expect(h.penalties.count).toBe(2);
  expect(h.penalties.pending).toEqual([60]);
  expect(h.penalties.lapsToServe).toBeCloseTo(2, 1);
  d.penalize('test');
  expect(d.hud().penalties.pending).toEqual([60, 60]);
  d.penalize('test');
  expect(d.hud().penalties.pending).toEqual([60, 60, 180]);
  d.penalize('test');
  h = d.hud();
  expect(h.penalties.ejected).toBe(true);
  expect(h.flag).toBe('black');
});

test('stop-and-go served in the pit-lane box; not served within 2 laps → ejected', () => {
  const d = director({ seed: 2, maxAi: 2, greenWindow: [0.01, 0.02] }, { walls: false });
  run(d, 0.1);
  d.penalize('a'); d.penalize('b');
  expect(d.hud().penalties.pending).toEqual([60]);
  const spot = d.penaltyBoxSpot();
  expect(spot).not.toBeNull();
  const P = d.player;
  P.vehicle.reset([spot!.x, spot!.y, P.surface.sample(spot!.x, spot!.y).z], spot!.heading, 0);
  P.hint = -1;
  run(d, 1);
  let h = d.hud();
  expect(h.penalties.inBox).toBe(true);
  expect(h.penalties.servingRemaining).toBeGreaterThan(58);
  expect(h.penalties.servingRemaining).toBeLessThan(60);
  run(d, 59.5);
  h = d.hud();
  expect(h.penalties.pending).toEqual([]);
  expect(h.penalties.ejected).toBe(false);
  // a new one, not served: 2 laps later the car is out
  d.penalize('c');
  expect(d.hud().penalties.pending).toEqual([60]);
  P.U += 2 * d.line.L + 5;
  run(d, 0.01);
  expect(d.hud().penalties.ejected).toBe(true);
}, 60000);

test('stop-and-go fast-forward: the car is held and time runs x10 until the last 5 s', () => {
  const d = director({ seed: 2, maxAi: 2, greenWindow: [0.01, 0.02] }, { walls: false });
  run(d, 0.1);
  d.penalize('a'); d.penalize('b');
  const spot = d.penaltyBoxSpot()!;
  const P = d.player;
  P.vehicle.reset([spot.x, spot.y, P.surface.sample(spot.x, spot.y).z], spot.heading, 0);
  P.hint = -1;
  expect(d.timeScale).toBe(1);
  run(d, 1);
  let h = d.hud();
  expect(h.penalties.inBox).toBe(true);
  expect(h.penalties.fastForward).toBe(true);
  expect(d.timeScale).toBe(FF_SCALE);
  // full throttle while held: the car stays put and the clock keeps running
  const x0 = P.vehicle.state.pos[0], y0 = P.vehicle.state.pos[1];
  run(d, 2, input({ throttle: 1 }));
  expect(Math.hypot(P.vehicle.state.pos[0] - x0, P.vehicle.state.pos[1] - y0)).toBeLessThan(0.05);
  h = d.hud();
  expect(h.penalties.fastForward).toBe(true);
  expect(h.penalties.servingRemaining).toBeLessThan(58);
  // the last FF_TAIL_S seconds run at 1x with the driver back in control
  run(d, 60 - FF_TAIL_S - 2.5);
  h = d.hud();
  expect(h.penalties.servingRemaining).toBeLessThan(FF_TAIL_S);
  expect(h.penalties.fastForward).toBe(false);
  expect(d.timeScale).toBe(1);
  run(d, 5);
  expect(d.hud().penalties.pending).toEqual([]);
  expect(d.timeScale).toBe(1);
}, 60000);

test('contact: the player closing on a car is at fault; being hit is not', () => {
  const d = director({ seed: 3, maxAi: 1, greenWindow: [0.01, 0.02] }, { walls: false });
  run(d, 0.1);
  const P = d.player, ai = d.cars.find((c) => !c.isPlayer)!;
  const s = 1200, lat = d.line.at(d.line.off, s);
  place(d, ai, s + 9, d.line.at(d.line.off, s + 9), 8);
  place(d, P, s, lat, 25);
  run(d, 1.5, input({ throttle: 1 }));
  let h = d.hud();
  expect(h.penalties.count).toBe(1);
  expect(h.penalties.lastReason).toMatch(/contact with #/);
  // the AI runs into a stationary player: no flag
  const d2 = director({ seed: 3, maxAi: 1, greenWindow: [0.01, 0.02] }, { walls: false });
  run(d2, 0.1);
  const P2 = d2.player, ai2 = d2.cars.find((c) => !c.isPlayer)!;
  place(d2, P2, s + 6, d2.line.at(d2.line.off, s + 6), 0);
  place(d2, ai2, s, d2.line.at(d2.line.off, s), 25);
  let contacts = 0;
  for (let i = 0; i < 1500; i++) { d2.step(0.001, brake); contacts += d2.contactCount; }
  expect(contacts).toBeGreaterThan(0);
  h = d2.hud();
  expect(h.penalties.count).toBe(0);
});

test('passing under yellow during the formation → black flag', () => {
  const d = director({ seed: 4, maxAi: 3, greenWindow: [25, 30] }, { walls: false });
  run(d, 3, input({ brake: 1 })); // stop on the grid (steer 0 would leave the track at the T1 kink)
  expect(d.phase).toBe('formation');
  expect(d.hud().penalties.count).toBe(0);
  const P = d.player;
  // the car just ahead of the player
  const ahead = d.cars.filter((c) => c !== P && c.U > P.U).sort((a, b) => a.U - b.U)[0];
  const sA = d.traffic.s[ahead.idx];
  place(d, P, sA + 12, d.line.at(d.line.off, sA + 12), 15);
  run(d, 0.05, input({ throttle: 0.3 }));
  const h = d.hud();
  expect(h.penalties.count).toBeGreaterThanOrEqual(1);
  expect(h.penalties.lastReason).toMatch(/passing under yellow/);
});
