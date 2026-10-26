// Board keys (0.4.0): the hash ignores car.json comments; the 0.3.0 key pins were dropped with the cheaper-pow round.
import { readFileSync } from 'node:fs';
import { describe, expect, test } from 'vitest';
import { physicsVersion, stripComments } from '../hash';
import { TRACKS } from '../config';

const car = JSON.parse(readFileSync(new URL('../../../public/cars/probe_gt/car.json', import.meta.url), 'utf8'));

describe('board keys', () => {
  test('comments do not change the key; a physics value does', () => {
    const L = TRACKS.laguna_seca.length_m;
    expect(physicsVersion({ ...car, _x: 'a note' }, L)).toBe(physicsVersion(car, L));
    expect(physicsVersion({ ...car, mass: (car.mass ?? 1000) + 1 }, L)).not.toBe(physicsVersion(car, L));
  });
  test('stripComments drops "_" keys at any depth', () => {
    expect(stripComments({ a: 1, _b: 2, c: [{ _d: 1, e: 2 }] })).toEqual({ a: 1, c: [{ e: 2 }] });
  });
});
