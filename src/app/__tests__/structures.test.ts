// The structure kit's pure geometry (src/app/structures.ts): triangle counts, bounds and determinism.
import { describe, expect, it } from 'vitest';
import {
  Soup, block, boards, fence, fuel, garage, grandstand, masts, paint, structureSoups, terraceDress,
  type BlockJson, type FuelJson, type GarageJson, type GrandstandJson, type StructureJson, type TerraceJson,
} from '../structures';

const stand: GrandstandJson = {
  type: 'grandstand', name: 'test', src: 'test', a: [0, 0], b: [100, 0], dir: [0, 1], z: 10,
  base: { h: 2.4, depth: 1.5, color: '#a89c88', panels: { colors: ['#ffffff', '#1d4e89'], w: 6, h: 1.2, gap: 1, z: 0.6 } },
  rows: { n: 30, depth: 0.9, rise: 0.33, z0: 2.6, seat: '#d8d2c4', riser: '#8d8a84', back: 0.4 },
  aisles: { pitch: 11, w: 1.2, color: '#b5b2aa' },
  towers: { w: 6, d0: 18, depth: 8, h: 14, steel: '#7d8186', cap: '#36553f' },
  suites: { d0: 28, d1: 45, floor: 14.5, glass: [15.6, 21.5], roof: [24, 26.2, 23, 0.45], color: '#3d5a45', glass_color: '#33424f',
    roof_color: '#36553f', columns: 10, back: { depth: 4, h: 20 }, lights: { t: [20, 80], h: 4 } },
  tower: { t0: 20, t1: 50, d0: 28, d1: 44, z0: 24, h: 29.8, color: '#3d5a45', glass: '#33424f', roof: '#2f4a37' },
  rear: { color: '#b9b1a1' },
};
const gar: GarageJson = {
  type: 'garage', name: 'g', src: 'test', c: [50, -20], heading: 0.3, l: 75, w: 14, z: 1, eave: 4.2, ridge: 6.1,
  wall: '#c9b58f', roof: '#3f5f48', trim: '#a8322b', trim_h: 0.5, doors: { side: 1, pitch: 5, w: 3.6, h: 3.2, color: '#d9d9d6' },
};
const blk: BlockJson = { type: 'block', name: 'b', src: 'test', c: [0, 0], heading: 1, l: 30, w: 20, z: 0, h: 7, storeys: 2, wall: '#cdbf9f', band: '#33424f', roof: '#9a9a96', parapet: 0.6 };
const fu: FuelJson = { type: 'fuel', name: 'f', src: 'test', c: [0, 0], heading: 0, l: 14, w: 9, z: 0, h: 4.8, fascia: 0.9, canopy: '#e9e7e1', fascia_color: '#f0efea', posts: 3, islands: 2,
  pylon: { at: [10, 6], h: 9, w: 2.4, color: '#1f3f73', panel: '#e9e7e1' } };
const terr: TerraceJson = { name: 'hill', run: 0.9, dir: [0, 1], z_ground_front: 0,
  rows: Array.from({ length: 20 }, (_, i) => ({ a: [0, i * 0.9] as [number, number], b: [60, i * 0.9] as [number, number], z: 0.4 * (i + 1) })) };

const all: StructureJson[] = [
  stand, gar, blk, fu,
  { type: 'fence', src: 't', pts: [[0, 0, 0], [10, 0, 0.5], [20, 2, 1]], h: 2 },
  { type: 'mast', src: 't', at: [[0, 0, 0, 0], [30, 0, 1, 1]], h: 20, heads: [3, 2] },
  { type: 'paint', src: 't', rects: [[0, 0, 0, 6, 0.12], [5, 0, 0.5, 6, 0.12]], color: '#f2f2ee' },
  { type: 'boards', src: 't', pts: [[0, 0, 0], [12, 0, 0]], z0: 1.1, h: 0.8, colors: ['#1d4e89', '#ffffff'], panel: 3 },
  { type: 'terrace_dress', src: 't', terrace: 'hill', bench: { color: '#c9c6bd', h: 0.35, depth: 0.35 }, aisles: { pitch: 20, w: 1.2, color: '#c2c0b9' },
    shades: [{ f0: 0.2, f1: 0.6, rows: 5, h: 3, color: '#e3e1da' }] },
];

describe('structure kit', () => {
  it('grandstand: rows, aisles, deck and towers in budget and inside its frame', () => {
    const s = new Soup();
    grandstand(stand, s);
    expect(s.tris).toBeGreaterThan(3000);
    expect(s.tris).toBeLessThan(20000);
    const { min, max } = s.bounds();
    // along t: the stair towers stand 6 m outside each end, the roof overhangs 0.4 m
    expect(min[0]).toBeGreaterThanOrEqual(-6.6);
    expect(max[0]).toBeLessThanOrEqual(106.6);
    // d: the base's panels sit 8 cm proud of the front line, the roof overhangs 1 m; back block to 49 m
    expect(min[1]).toBeGreaterThanOrEqual(-1.01);
    expect(max[1]).toBeLessThanOrEqual(49.5);
    // z: 0.5 m footing below the ground, the tower roof slab, the light clusters 4 m above the roof
    expect(min[2]).toBeGreaterThanOrEqual(10 - 0.51);
    expect(max[2]).toBeLessThanOrEqual(10 + 31);
    expect(max[2]).toBeGreaterThanOrEqual(10 + 29.8);
  });

  it('grandstand rows rise by the declared rise and the top row sits where declared', () => {
    const s = new Soup();
    grandstand({ ...stand, suites: undefined, tower: undefined, towers: undefined, aisles: undefined, base: { ...stand.base, panels: undefined } }, s);
    const zs = new Set<number>();
    for (let i = 2; i < s.pos.length; i += 3) zs.add(Math.round(s.pos[i] * 100) / 100);
    const top = 10 + 2.6 + 29 * 0.33;
    expect([...zs].some((z) => Math.abs(z - top) < 0.011)).toBe(true);
    expect(Math.max(...zs)).toBeLessThanOrEqual(top + 1.11);   // the top rail
  });

  it('garage: doors per pitch on the stated side, roof ridge at the stated height', () => {
    const s = new Soup();
    garage(gar, s);
    const noDoors = new Soup();
    garage({ ...gar, doors: undefined }, noDoors);
    expect((s.tris - noDoors.tris) / 2).toBe(Math.floor((75 - 1) / 5));
    const both = new Soup();
    garage({ ...gar, doors: { ...gar.doors!, side: 0 } }, both);
    expect(both.tris - noDoors.tris).toBe(2 * (s.tris - noDoors.tris));
    expect(s.bounds().max[2]).toBeCloseTo(1 + 6.1, 6);
    // footprint plus the 0.5 m overhang, rotated: the bounds stay within the circumscribed circle
    const r = Math.hypot(75 / 2 + 0.5, 14 / 2 + 0.5);
    const { min, max } = s.bounds();
    expect(Math.max(Math.abs(min[0] - 50), Math.abs(max[0] - 50), Math.abs(min[1] + 20), Math.abs(max[1] + 20))).toBeLessThanOrEqual(r + 1e-9);
  });

  it('block and fuel island: closed boxes with bands / posts / pylon', () => {
    const b = new Soup(); block(blk, b);
    expect(b.tris).toBe(10 + 4 * 10 + 2 * 4 * 2);   // body, 4 parapet boxes, 2 storeys x 4 bands
    expect(b.bounds().max[2]).toBeCloseTo(7.6, 6);
    const f = new Soup(); fuel(fu, f);
    expect(f.tris).toBeGreaterThan(60);
    expect(f.bounds().max[2]).toBeCloseTo(9, 6);
  });

  it('fence, masts, paint and boards', () => {
    const solid = new Soup(), fab = new Soup();
    fence(all[4] as never, solid, fab);
    expect(fab.tris).toBe(4);
    expect(fab.uv.length).toBe(fab.tris * 3 * 2);
    const m = new Soup(); masts(all[5] as never, m);
    expect(m.tris).toBe(2 * (8 + 10 + 2 * 6));
    expect(m.bounds().max[2]).toBeCloseTo(1 + 20 - 0.4 + 2 * 0.55, 6);
    const p = new Soup(); paint(all[6] as never, p, () => 3);
    expect(p.tris).toBe(4);
    expect(p.bounds().min[2]).toBeCloseTo(3.02, 6);
    const bo = new Soup(); boards(all[7] as never, bo);
    expect(bo.tris).toBe(4 * 10);
  });

  it('terrace dressing: benches broken by aisles, rails, shade roof', () => {
    const s = new Soup();
    terraceDress(all[8] as never, terr, s);
    expect(s.tris).toBeGreaterThan(20 * 4 * 2);
    const { min, max } = s.bounds();
    expect(min[0]).toBeGreaterThanOrEqual(-0.01);
    expect(max[0]).toBeLessThanOrEqual(60.01);
    expect(max[2]).toBeLessThanOrEqual(0.4 * 20 + 3 + 0.6 + 1e-6);
  });

  it('is deterministic and a full Sonoma-size set stays inside the triangle budget', () => {
    const a = structureSoups(all, [terr]), b = structureSoups(all, [terr]);
    expect(a.solid.pos).toEqual(b.solid.pos);
    expect(a.solid.col).toEqual(b.solid.col);
    expect(a.paint.pos).toEqual(b.paint.pos);
    const total = a.solid.tris + a.paint.tris + a.fabric.tris;
    expect(Object.values(a.perType).reduce((x, y) => x + y, 0)).toBe(total);
    expect(total).toBeLessThan(150000);
    // unknown types and a dressing of a missing terrace draw nothing
    const none = structureSoups([{ type: 'terrace_dress', src: 't', terrace: 'nope' } as StructureJson], []);
    expect(none.solid.tris).toBe(0);
  });
});
