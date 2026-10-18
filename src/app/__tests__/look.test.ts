// The look (look.ts) and tyre marks (marks.ts): the pure parts.
import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { DynamicResolution, SUN_DEFAULT, grade, lightingFor, postUrlOff, sunDirection, sunFromUrl } from '../look';
import { markIntensity, onPavement } from '../marks';
import { SUN_DIR } from '../scene';
import { GLASS_RE, PAINT_RE, upgradeCarMaterials } from '../car-materials';

describe('sun', () => {
  it('parses ?sun=az,el and falls back to the calibrated afternoon', () => {
    expect(sunFromUrl('')).toEqual(SUN_DEFAULT);
    expect(sunFromUrl('?sun=90,12')).toEqual({ azimuthDeg: 90, elevationDeg: 12 });
    expect(sunFromUrl('?sun=-10,120')).toEqual({ azimuthDeg: 350, elevationDeg: 89 });
    expect(sunFromUrl('?sun=abc')).toEqual(SUN_DEFAULT);
  });
  it('default direction matches the world sun the scene was calibrated with', () => {
    const d = sunDirection(SUN_DEFAULT);
    expect(d.distanceTo(SUN_DIR)).toBeLessThan(1e-9);
  });
  it('lighting keeps the calibrated sun at the default elevation and warms / dims toward the horizon', () => {
    const def = lightingFor(SUN_DEFAULT.elevationDeg);
    expect(def.sunIntensity).toBeCloseTo(3.4, 5);
    expect(def.sunColor.getHex()).toBe(0xffe7c8);
    const low = lightingFor(6);
    expect(low.sunIntensity).toBeLessThan(def.sunIntensity);
    expect(low.sunColor.r / low.sunColor.b).toBeGreaterThan(def.sunColor.r / def.sunColor.b);
  });
});

describe('post', () => {
  it('?post=0 turns the stack off', () => {
    expect(postUrlOff('')).toBe(false);
    expect(postUrlOff('?post=0')).toBe(true);
  });
  it('grade keeps black, white and the range', () => {
    expect(grade(0, 0, 0)).toEqual([0, 0, 0]);
    const w = grade(1, 1, 1);
    for (const c of w) expect(c).toBeGreaterThan(0.9);
    for (let i = 0; i < 50; i++) { const [r, g, b] = grade(Math.random(), Math.random(), Math.random()); for (const c of [r, g, b]) { expect(c).toBeGreaterThanOrEqual(0); expect(c).toBeLessThanOrEqual(1); } }
  });
  it('dynamic resolution steps down under long frames and back up under quick ones', () => {
    const d = new DynamicResolution(0.8, 1.5, 16.7);
    let changed: number | null = null;
    for (let i = 0; i < 200 && changed === null; i++) changed = d.sample(33);
    expect(changed).not.toBeNull();
    expect(d.ratio).toBeLessThan(1.5);
    for (let i = 0; i < 2000; i++) d.sample(33);
    expect(d.ratio).toBeCloseTo(0.8, 5);
    for (let i = 0; i < 2000; i++) d.sample(8);
    expect(d.ratio).toBeCloseTo(1.5, 5);
    expect(d.sample(500)).toBeNull(); // a hitch is ignored
  });
});

describe('marks', () => {
  it('a wheel marks past its grip peak on pavement, never unloaded', () => {
    expect(markIntensity({ slipUse: 0.9, slipRatio: 0, slipAngle: 0, load: 3000 })).toBe(0);
    expect(markIntensity({ slipUse: 1.3, slipRatio: 0, slipAngle: 0, load: 3000 })).toBe(0);
    expect(markIntensity({ slipUse: 1.6, slipRatio: 0, slipAngle: 0, load: 3000 })).toBeCloseTo(0.45, 5);
    expect(markIntensity({ slipUse: 2, slipRatio: 0, slipAngle: 0, load: 3000 })).toBe(1);
    expect(markIntensity({ slipUse: 2, slipRatio: 0, slipAngle: 0, load: 0 })).toBe(0);
    expect(markIntensity({ slipRatio: 0.3, slipAngle: 0, load: 3000 })).toBe(1); // stub physics: from the slips
    expect(onPavement({ onTrack: false, paved: true })).toBe(true);
    expect(onPavement({ onTrack: false })).toBe(false);
  });
});

describe('car materials', () => {
  it('names: the Probe paint, kit liveries and glass', () => {
    expect(PAINT_RE.test('paint')).toBe(true);
    expect(PAINT_RE.test('car/x/derived_spec.py_livery')).toBe(true);
    expect(PAINT_RE.test('brake')).toBe(false);
    expect(GLASS_RE.test('car711_glass')).toBe(true);
  });
  it('replaces paint with a clear-coated physical material and glass with a reflective one, once', () => {
    const paint = new THREE.MeshStandardMaterial({ name: 'paint', color: 0xc8102e, roughness: 0.8 });
    const glass = new THREE.MeshStandardMaterial({ name: 'glass', transparent: true, opacity: 0.6, roughness: 0.2 });
    const tyre = new THREE.MeshStandardMaterial({ name: 'tyre' });
    const g = new THREE.BoxGeometry();
    const root = new THREE.Group();
    root.add(new THREE.Mesh(g, paint), new THREE.Mesh(g, [paint, glass]), new THREE.Mesh(g, tyre));
    expect(upgradeCarMaterials(root)).toBe(2);
    const m0 = (root.children[0] as THREE.Mesh).material as THREE.MeshPhysicalMaterial;
    expect(m0.isMeshPhysicalMaterial).toBe(true);
    expect(m0.clearcoat).toBeGreaterThan(0);
    expect(m0.roughness).toBeLessThanOrEqual(0.5);
    expect(m0.color.getHex()).toBe(0xc8102e);
    expect(m0.defines).toMatchObject({ PHYSICAL: '' });
    const m1 = (root.children[1] as THREE.Mesh).material as THREE.Material[];
    expect(m1[0]).toBe(m0); // shared paint replaced once
    expect((m1[1] as THREE.MeshPhysicalMaterial).isMeshPhysicalMaterial).toBe(true);
    expect((m1[1] as THREE.MeshPhysicalMaterial).transparent).toBe(true);
    expect((root.children[2] as THREE.Mesh).material).toBe(tyre);
    expect(upgradeCarMaterials(root)).toBe(0);
    // phone tier: glass only
    const root2 = new THREE.Group(); root2.add(new THREE.Mesh(g, new THREE.MeshStandardMaterial({ name: 'paint' })));
    expect(upgradeCarMaterials(root2, { clearcoat: false })).toBe(0);
  });
});

describe('thresholds (owner, 18 Oct: "people aren\'t smoking their tires every 10 seconds")', () => {
  it('marks start well past the grip peak; smoke needs a locked or spinning wheel', async () => {
    const { smokes, MARK_USE_ON } = await import('../marks');
    expect(MARK_USE_ON).toBeGreaterThanOrEqual(1.25);
    expect(markIntensity({ slipUse: 1.2, slipRatio: -0.1, slipAngle: 0.05, load: 3000 })).toBe(0); // ABS chatter / trail braking
    expect(smokes({ slipRatio: -0.3, load: 3000 }, 30)).toBe(false);
    expect(smokes({ slipRatio: -0.95, load: 3000 }, 30)).toBe(true);   // locked at speed
    expect(smokes({ slipRatio: -0.95, load: 3000 }, 3)).toBe(false);   // locked while nearly stopped: no smoke
    expect(smokes({ slipRatio: 1.5, load: 3000 }, 0)).toBe(true);      // burnout
  });
  it('no tree within reach of a driveable surface', async () => {
    const { keepTreeClear, TREE_CLEARANCE_M } = await import('../scenery');
    expect(keepTreeClear(5, 3)).toBe(false);
    expect(keepTreeClear(TREE_CLEARANCE_M + 3, 3)).toBe(true);
    expect(keepTreeClear(TREE_CLEARANCE_M + 2, 3)).toBe(false);
  });
});
