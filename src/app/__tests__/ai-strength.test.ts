// AI strength setting (AI round 1, 27 Oct 2026): the stored choice (pure functions over a Storage), the board version string.
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { AI_STRENGTH_KEY, AI_STRENGTH_PCTS, aiStrengthLabel, parseAiStrength, raceBoardVersion, storeAiStrength, storedAiStrength } from '../modes/race';

const mem = () => { const m = new Map<string, string>(); return { m, getItem: (k: string) => m.get(k) ?? null, setItem: (k: string, v: string) => void m.set(k, v), removeItem: (k: string) => void m.delete(k) }; };

describe('AI strength setting', () => {
  it('choices 100, 105 and 110 % (the solo-verified range), anything else reads as 100', () => {
    expect(AI_STRENGTH_PCTS).toEqual([100, 105, 110]);
    for (const v of AI_STRENGTH_PCTS) expect(parseAiStrength(String(v))).toBe(v);
    for (const v of [null, undefined, '', 'x', '101', '120', '90', '95', '0', '-5']) expect(parseAiStrength(v as string | null)).toBe(100);
  });
  it('persists like the Graphics choice: the default is no key; a throwing storage reads 100', () => {
    const s = mem();
    expect(storedAiStrength(s)).toBe(100);
    storeAiStrength(105, s); expect(s.m.get(AI_STRENGTH_KEY)).toBe('105'); expect(storedAiStrength(s)).toBe(105);
    storeAiStrength(95, s); expect(storedAiStrength(s)).toBe(100);
    storeAiStrength(105, s);
    storeAiStrength(100, s); expect(s.m.has(AI_STRENGTH_KEY)).toBe(false); expect(storedAiStrength(s)).toBe(100);
    storeAiStrength(123, s); expect(s.m.has(AI_STRENGTH_KEY)).toBe(false);
    const bad = { getItem: () => { throw new Error('denied'); }, setItem: () => { throw new Error('denied'); }, removeItem: () => { throw new Error('denied'); } };
    expect(storedAiStrength(bad)).toBe(100);
    expect(() => storeAiStrength(105, bad)).not.toThrow();
    expect(storedAiStrength(null)).toBe(100);
  });
  it('the board version carries the strength when it is not 100 % (the default keeps the key)', () => {
    expect(raceBoardVersion(8)).toBe('8-5L');
    expect(raceBoardVersion(8, 5, 100)).toBe('8-5L');
    expect(raceBoardVersion(8, 5, 110)).toBe('8-5L-S110');
    expect(aiStrengthLabel(105)).toBe('AI 105 %');
  });
  it('the Start menu has no AI strength row (removed on the owner\'s call, 29 Oct 2026); the plumbing stays for the tools', () => {
    const src = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), '../index.ts'), 'utf8');
    expect(src).not.toMatch(/aiStrength|AI strength|storedAiStrength|storeAiStrength|AI_STRENGTH/);
    // the stored key of an earlier build is ignored: a race built with no explicit strength is built at 100 %
    expect(readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), '../modes/race.ts'), 'utf8')).toMatch(/deps\.aiStrength \? deps\.aiStrength\(\) : 100\)/);
  });
});
