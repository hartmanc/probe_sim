// Tyre audio off pavement: no squeal from wheels on dirt, a gravel / grass layer instead.
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { audioParamsFromCarJson, dirtMix, onPavement, squealMix, wheelSqueal, DIRT_FULL_SPEED, type DirtMix, type SquealMix } from '../audio';
import type { VehicleState, WheelState } from '../physics-types';

const carJson = JSON.parse(readFileSync(new URL('../../../public/cars/probe_gt/car.json', import.meta.url).pathname, 'utf8'));
const P = audioParamsFromCarJson(carJson);

const wheel = (o: Partial<WheelState> = {}): WheelState => ({
  pos: [0, 0, 0], spinAngle: 0, steer: 0, compression: 0, omega: 0, slipRatio: 0, slipAngle: 0, load: 3500,
  onTrack: true, paved: true, mu: 1, ...o,
});
const dirtW = (o: Partial<WheelState> = {}) => wheel({ onTrack: false, paved: false, mu: 0.72, ...o });
const state = (w: WheelState[], speed = 20): VehicleState => ({
  pos: [0, 0, 0], quat: [0, 0, 0, 1], vel: [speed, 0, 0], angVel: [0, 0, 0],
  wheels: [w[0], w[1], w[2], w[3]], rpm: 4000, gear: 3, speed, gLat: 0, gLong: 0, throttleOut: 1,
});
const sq = (): SquealMix => ({ scrub: 0, skid: 0, slide: 0 });
const dm = (): DirtMix => ({ level: 0, spray: 0 });

describe('squeal gating by surface', () => {
  it('a wheel on dirt never squeals, however hard it slides', () => {
    expect(wheelSqueal(dirtW({ slipUse: 2 }), 30, P)).toBe(0);
    expect(wheelSqueal(wheel({ slipUse: 2 }), 30, P)).toBeCloseTo(1, 6);
  });
  it('pit lane / paved runoff (onTrack false, paved true) still squeals', () => {
    expect(wheelSqueal(wheel({ onTrack: false, paved: true, slipUse: 1.5 }), 20, P)).toBeGreaterThan(0.9);
  });
  it('without WheelState.paved (older physics) falls back to onTrack', () => {
    const w = wheel({ slipUse: 1.5 });
    delete (w as { paved?: boolean }).paved;
    expect(onPavement(w)).toBe(true);
    expect(onPavement({ ...w, onTrack: false })).toBe(false);
  });
  it('two wheels paved, two on dirt: only the paved pair contributes to scrub and skid', () => {
    // left side on the pavement, right side dropped onto the dirt, all four sliding and the rears locked
    const st = state([
      wheel({ slipUse: 1.4, slipAngle: 0.15 }), dirtW({ slipUse: 1.4, slipAngle: 0.15 }),
      wheel({ slipUse: 1.4, slipRatio: -0.5 }), dirtW({ slipUse: 1.4, slipRatio: -0.5 }),
    ], 25);
    const mixed = squealMix(st, P, sq());
    // same car with only the paved pair present (dirt pair unloaded) must give the same mix
    const pavedOnly = squealMix(state([st.wheels[0], dirtW({ load: 0 }), st.wheels[2], dirtW({ load: 0 })], 25), P, sq());
    expect(mixed).toEqual(pavedOnly);
    expect(mixed.scrub).toBeGreaterThan(0.5);
    expect(mixed.skid).toBeGreaterThan(0.5);
    // all four on dirt: silent
    const allDirt = squealMix(state(st.wheels.map((w) => ({ ...w, paved: false, onTrack: false })), 25), P, sq());
    expect(allDirt.scrub).toBe(0);
    expect(allDirt.skid).toBe(0);
  });
});

describe('gravel / grass layer', () => {
  it('follows the number of wheels off pavement × speed', () => {
    const lvl = (n: number, v: number) => dirtMix(state([0, 1, 2, 3].map((i) => (i < n ? dirtW() : wheel())), v), P, dm()).level;
    expect(lvl(0, 30)).toBe(0);
    expect(lvl(2, 30)).toBeCloseTo(0.5, 6);
    expect(lvl(4, 30)).toBeCloseTo(1, 6);
    expect(lvl(2, DIRT_FULL_SPEED / 2)).toBeLessThan(lvl(2, DIRT_FULL_SPEED));
    expect(lvl(4, 0)).toBe(0);
  });
  it('the pit lane is not gravel', () => {
    const st = state([0, 1, 2, 3].map(() => wheel({ onTrack: false, paved: true })), 20);
    expect(dirtMix(st, P, dm()).level).toBe(0);
  });
  it('spray appears only when an off-pavement wheel slides', () => {
    const rolling = state([wheel(), wheel(), dirtW({ slipUse: 0.3 }), dirtW({ slipUse: 0.3 })], 20);
    expect(dirtMix(rolling, P, dm()).spray).toBe(0);
    const sliding = state([wheel({ slipUse: 2 }), wheel({ slipUse: 2 }), dirtW({ slipUse: 1.6 }), dirtW({ slipUse: 0.3 })], 20);
    const m = dirtMix(sliding, P, dm());
    expect(m.spray).toBeCloseTo(1, 6);
    expect(m.level).toBeGreaterThan(0.4); // two of four wheels, 20 m/s (below full speed)
    expect(m.level).toBeLessThan(0.5);
    // the paved wheels sliding hard does not make spray
    const pavedSlide = state([wheel({ slipUse: 2 }), wheel({ slipUse: 2 }), dirtW({ slipUse: 0.2 }), dirtW({ slipUse: 0.2 })], 20);
    expect(dirtMix(pavedSlide, P, dm()).spray).toBe(0);
  });
  it('airborne (unloaded) wheels make no dirt noise', () => {
    expect(dirtMix(state([dirtW({ load: 0 }), dirtW({ load: 0 }), dirtW({ load: 0 }), dirtW({ load: 0 })], 30), P, dm()).level).toBe(0);
  });
});
