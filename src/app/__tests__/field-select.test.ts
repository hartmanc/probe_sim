// Phones and tablets race the player's 40 pace neighbours (field-select.ts); the device class (quality.ts).
import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';
import { MOBILE_FIELD, aiCount, fieldCapFor, fieldLine, neighbourField } from '../field-select';
import { deviceClass, settingsFor } from '../quality';

const load = (p: string) => JSON.parse(readFileSync(new URL(`../../../public/${p}`, import.meta.url), 'utf8'));

describe('phone field: the 40 pace neighbours', () => {
  test('Sonoma: 40 of 133 AI cars, the ones nearest the Probe band, in the real order, the player kept', () => {
    const pace = load('cars/field/sonoma/pace.json');
    expect(aiCount(pace, '619')).toBe(133);
    const f = neighbourField(pace, MOBILE_FIELD, '619');
    expect(aiCount(f, '619')).toBe(40);
    expect(f.cars.some((c: { number: string }) => c.number === '619')).toBe(true);
    // the file's own order (real relative order) is kept
    const idx = f.cars.map((c: unknown) => pace.cars.indexOf(c));
    expect([...idx].sort((a, b) => a - b)).toEqual(idx);
    // every chosen car is at least as close to the band as every dropped one
    const me = pace.cars.find((c: { number: string }) => c.number === '619');
    const out = (c: { targetLap: number }) => Math.max(0, Math.abs(c.targetLap - me.targetLap) - me.sigma);
    const kept = f.cars.filter((c: { number: string }) => c.number !== '619');
    const dropped = pace.cars.filter((c: { number: string }) => c.number !== '619' && !f.cars.includes(c));
    expect(Math.max(...kept.map(out))).toBeLessThanOrEqual(Math.min(...dropped.map(out)));
    expect(dropped).toHaveLength(93);
  });
  test('Laguna: 40 of 44; a small field and a field without the player row', () => {
    const pace = load('cars/field/pace.json');
    expect(aiCount(neighbourField(pace, 40, '619'), '619')).toBe(40);
    const small = { cars: pace.cars.slice(0, 10) };
    expect(neighbourField(small, 40, '619')).toBe(small);
    const noMe = { cars: pace.cars.filter((c: { number: string }) => c.number !== '619') };
    expect(aiCount(neighbourField(noMe, 40, '619'), '619')).toBe(40);
  });
  test('deterministic: the same input picks the same cars', () => {
    const pace = load('cars/field/sonoma/pace.json');
    const a = neighbourField(pace, 40, '619').cars.map((c: { number: string }) => c.number);
    const b = neighbourField(pace, 40, '619').cars.map((c: { number: string }) => c.number);
    expect(a).toEqual(b);
  });
  test('caps and the Start-menu line', () => {
    expect(fieldCapFor('phone')).toBe(40);
    expect(fieldCapFor('tablet')).toBe(40);
    expect(fieldCapFor('desktop')).toBe(Infinity);
    expect(fieldLine(133, 'phone')).toBe('40 of 133 cars on this device');
    expect(fieldLine(133, 'tablet')).toBe('40 of 133 cars on this device');
    expect(fieldLine(133, 'desktop')).toBe('all 133 cars');
    expect(fieldLine(30, 'phone')).toBe('all 30 cars');
  });
});

describe('device class', () => {
  const env = { coarse: false, maxTouchPoints: 0, search: '', platform: 'MacIntel', screenMin: 900 };
  test('desktop, phone, tablet, iPad posing as a Mac, URL overrides', () => {
    expect(deviceClass(env)).toBe('desktop');
    expect(deviceClass({ ...env, coarse: true, maxTouchPoints: 5, platform: 'iPhone', screenMin: 390 })).toBe('phone');
    expect(deviceClass({ ...env, coarse: true, maxTouchPoints: 5, platform: 'Linux armv8l', screenMin: 800 })).toBe('tablet');
    expect(deviceClass({ ...env, maxTouchPoints: 5 })).toBe('tablet');   // iPadOS Safari with a trackpad
    expect(deviceClass({ ...env, search: '?phone=1' })).toBe('phone');
    expect(deviceClass({ ...env, coarse: true, maxTouchPoints: 5, platform: 'iPhone', search: '?phone=0' })).toBe('desktop');
  });
  test('settings carry the device class; the render tier does not decide it', () => {
    expect(settingsFor('desktop', 'forced', true, { device: 'tablet' }).device).toBe('tablet');
    expect(settingsFor('phone', 'auto', true).device).toBe('phone');
  });
});
