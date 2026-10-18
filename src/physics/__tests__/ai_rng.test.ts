import { expect, test } from 'vitest';
import { Rng, hashSeed, aggressionFor } from '../ai/rng';

test('PRNG: same seed → same sequence, different seeds differ, uniform-ish', () => {
  const a = new Rng(42), b = new Rng(42), c = new Rng(43);
  const sa = Array.from({ length: 1000 }, () => a.next());
  const sb = Array.from({ length: 1000 }, () => b.next());
  const sc = Array.from({ length: 1000 }, () => c.next());
  expect(sa).toEqual(sb);
  expect(sa).not.toEqual(sc);
  const mean = sa.reduce((x, y) => x + y, 0) / sa.length;
  expect(Math.abs(mean - 0.5)).toBeLessThan(0.03);
  expect(Math.min(...sa)).toBeGreaterThanOrEqual(0);
  expect(Math.max(...sa)).toBeLessThan(1);
  // forks are deterministic and independent of later draws
  const f1 = new Rng(7).fork('car:711'), f2 = new Rng(7).fork('car:711');
  expect([f1.next(), f1.normal()]).toEqual([f2.next(), f2.normal()]);
  expect(hashSeed(1, 'x')).toBe(hashSeed(1, 'x'));
  expect(hashSeed(1, 'x')).not.toBe(hashSeed(2, 'x'));
});

test('aggression: stable per car number, class-weighted (A more aggressive than C)', () => {
  expect(aggressionFor('619', 'B')).toBe(aggressionFor('619', 'B'));
  let a = 0, c = 0;
  for (let i = 0; i < 2000; i++) { a += aggressionFor(String(i), 'A'); c += aggressionFor(String(i), 'C'); }
  expect(a / 2000).toBeGreaterThan(c / 2000 + 0.3);
});
