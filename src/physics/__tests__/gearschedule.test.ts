import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';
import { deriveGearSchedule, scheduleGearAt, scheduleTargetAt, shiftRpmSummary, Vehicle } from '../index';
import { createFlatSurface } from '../devtrack';
import { DT, input, probeSpec } from './helpers';

const dir = fileURLToPath(new URL('../../../public/tracks/laguna_seca/', import.meta.url));
const ghosts = JSON.parse(readFileSync(dir + 'ghosts.json', 'utf8'));
const driver_a = ghosts.laps.find((l: { id: string }) => l.id === 'driver_a_best');

describe('gear schedule from a ghost', () => {
  const spec = probeSpec();
  const sch = deriveGearSchedule(spec, driver_a, ghosts.s_grid_m);

  test('driver A: 4th all the way up the Rahal climb, shifts near his rpm', () => {
    for (let s = 1700; s <= 2400; s += 10) expect(scheduleGearAt(sch, s)).toBe(4);
    const sum = shiftRpmSummary(sch);
    console.log('driver A shift rpm: ' + sum.map((x) => `${x.from}->${x.to} @${x.rpm.toFixed(0)} (x${x.count})`).join(', '));
    for (const x of sum.filter((x) => x.to > x.from)) {
      expect(x.rpm).toBeGreaterThan(4400);
      expect(x.rpm).toBeLessThan(5300);
    }
    // only real gears, no flicker: every run lasts at least ~30 m
    expect(sch.shifts.length).toBeLessThan(16);
    for (let i = 1; i < sch.shifts.length; i++) expect(sch.shifts[i].s - sch.shifts[i - 1].s).toBeGreaterThanOrEqual(30);
  });

  test('target hysteresis: the change counts a few metres past the shift point', () => {
    const sh = sch.shifts[0];
    expect(scheduleTargetAt(sch, sh.s + 0.5)).toBe(sh.from);
    expect(scheduleTargetAt(sch, sh.s + 5)).toBe(sh.to);
  });

  test('every ghost gives a usable schedule', () => {
    for (const lap of ghosts.laps) {
      const s = deriveGearSchedule(spec, lap, ghosts.s_grid_m);
      expect(s.gear.every((g) => g >= 1 && g <= 5)).toBe(true);
    }
  });
});

describe('Vehicle follows a scheduled gear', () => {
  test('upshifts when the schedule says so (and the revs are there), downshifts, guards the limiter', () => {
    const car = new Vehicle(probeSpec(), { autoShift: true });
    const flat = createFlatSurface();
    car.reset([0, 0, 0], 0, 20);
    car.setGear(2);
    car.setScheduledGear(2);
    const full = input({ throttle: 1 });
    // held in 2nd past the 5000 rpm rpm-rule point, until the limiter guard
    let maxRpm = 0;
    for (let i = 0; i < 4000 && car.state.gear === 2; i++) { car.step(full, flat, DT); maxRpm = Math.max(maxRpm, car.state.rpm); }
    expect(maxRpm).toBeGreaterThan(6000);
    expect(car.state.gear).toBe(3); // limiter guard
    // schedule asks for 4th: goes up
    car.setScheduledGear(4);
    for (let i = 0; i < 3000; i++) car.step(full, flat, DT);
    expect(car.state.gear).toBe(4);
    // schedule asks for 2nd while braking: comes down through 3rd
    car.setScheduledGear(2);
    for (let i = 0; i < 3000; i++) car.step(input({ brake: 0.4 }), flat, DT);
    expect(car.state.gear).toBe(2);
    // 0 = back to the rpm rules
    car.setScheduledGear(0);
    for (let i = 0; i < 6000; i++) car.step(full, flat, DT);
    expect(car.state.gear).toBeGreaterThanOrEqual(3);
  });
});
