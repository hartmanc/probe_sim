// The AI engine families must keep assigning every car exactly as before the CC BY rebuild:
// familyFor() over the three field identity files, compared with a committed baseline taken on main (6f890b9),
// plus the parts of index.json that drive the assignment (family ids, aliases, fallback, default).
// UPDATE_FAMILY_BASELINE=1 rewrites the baseline (only do that on purpose).
import { describe, expect, it } from 'vitest';
import { existsSync, readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { familyFor, type FamilyIndex, type Layout } from '../audio-field';

const ROOT = resolve(__dirname, '../../..');
const FIXTURE = resolve(__dirname, 'fixtures/family-assignments.json');
const IDENTITY = ['public/cars/field/identity.json', 'public/cars/field/buttonwillow/identity.json', 'public/cars/field/sonoma/identity.json'];
const readJson = (p: string) => JSON.parse(readFileSync(resolve(ROOT, p), 'utf8'));

const layoutOf = (s?: string): Layout | undefined => {
  if (!s) return undefined;
  const m = /^(flat|[IVHB])/i.exec(s);
  if (!m) return undefined;
  const k = m[1].toLowerCase();
  return k === 'i' ? 'inline' : k === 'v' ? 'v' : 'flat';
};

function assignments(index: FamilyIndex) {
  const out: Record<string, Record<string, string>> = {};
  for (const f of IDENTITY) {
    const rows: Record<string, string> = {};
    for (const c of readJson(f) as { number: string; id?: string; make?: string; model?: string; engine?: { family?: string; cylinders?: number; layout?: string } }[]) {
      const e = c.engine ?? {};
      rows[c.id ?? c.number] = familyFor(index, { engineFamily: e.family, make: c.make, model: c.model, cylinders: e.cylinders, layout: layoutOf(e.layout) });
    }
    out[f] = rows;
  }
  return out;
}

const drivers = (index: FamilyIndex & { cars?: unknown }) => ({
  families: Object.keys(index.families).sort(), aliases: index.aliases, fallback: index.fallback, default: index.default, cars: index.cars,
});

describe('engine family assignment is unchanged', () => {
  const index = readJson('public/audio/families/index.json') as FamilyIndex;
  const now = { assignments: assignments(index), index: drivers(index) };
  if (process.env.UPDATE_FAMILY_BASELINE) writeFileSync(FIXTURE, JSON.stringify(now, null, 1));

  it('has a baseline', () => { expect(existsSync(FIXTURE)).toBe(true); });
  it('familyFor gives every car of the three fields the same family as on main', () => {
    const base = readJson('src/app/__tests__/fixtures/family-assignments.json');
    expect(now.assignments).toEqual(base.assignments);
  });
  it('index.json keeps the same family ids, aliases, fallback, default and per-car rows', () => {
    const base = readJson('src/app/__tests__/fixtures/family-assignments.json');
    expect(now.index).toEqual(base.index);
  });
});

describe('every family index entry loads its sprites', () => {
  const index = readJson('public/audio/families/index.json') as FamilyIndex;
  for (const [id, f] of Object.entries(index.families)) {
    it(`${id}: engine.json, both sprites and every bin offset inside the sprite`, () => {
      const base = resolve(ROOT, 'public/audio/families');
      const ej = resolve(base, f.engine);
      expect(existsSync(ej)).toBe(true);
      const eng = JSON.parse(readFileSync(ej, 'utf8'));
      const dir = resolve(ej, '..');
      const sprites = f.sprites ?? eng.sprites;
      for (const k of ['on', 'off'] as const) expect(existsSync(resolve(base, sprites[k]))).toBe(true);
      expect(eng.bins.length).toBeGreaterThan(5);
      for (const b of eng.bins) for (const k of ['on', 'off'] as const) {
        expect(b[k].duration).toBeGreaterThan(0.15);
        expect(b[k].offset).toBeGreaterThan(0);
      }
      if (eng.fallback) for (const k of ['on', 'off']) expect(existsSync(resolve(dir, eng.fallback[k]))).toBe(true);
    });
  }
});
