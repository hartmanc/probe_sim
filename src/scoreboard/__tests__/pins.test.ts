// 0.4.0: car.json comments edited (team members' names) and the hash ignores "_" keys; the published board keys stay.
import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';
import { physicsVersion, stripComments } from '../hash';
import { PHYSICS_KEY_PINS, TRACKS } from '../config';

const car = JSON.parse(readFileSync(new URL('../../../public/cars/probe_gt/car.json', import.meta.url), 'utf8'));

describe('board-key pins', () => {
  test('the shipped car.json answers the keys the 0.3.0 boards were published under', () => {
    expect(physicsVersion(car, TRACKS.laguna_seca.length_m, TRACKS.laguna_seca.rev)).toBe('12oxe5efqsv');
    expect(physicsVersion(car, TRACKS.sonoma.length_m, TRACKS.sonoma.rev)).toBe('0aitg05wi4d');
    expect(physicsVersion(car, TRACKS.buttonwillow.length_m, TRACKS.buttonwillow.rev)).toBe('0ewchkyn2w5');
  });
  test('comments do not change the key; a physics value does (and is not pinned)', () => {
    const L = TRACKS.laguna_seca.length_m;
    expect(physicsVersion({ ...car, _x: 'a note' }, L)).toBe(physicsVersion(car, L));
    const changed = physicsVersion({ ...car, mass: (car.mass ?? 1000) + 1 }, L);
    expect(changed).not.toBe(physicsVersion(car, L));
    expect(Object.values(PHYSICS_KEY_PINS)).not.toContain(changed);
  });
  test('stripComments drops "_" keys at any depth', () => {
    expect(stripComments({ a: 1, _b: 2, c: [{ _d: 1, e: 2 }] })).toEqual({ a: 1, c: [{ e: 2 }] });
  });
});
