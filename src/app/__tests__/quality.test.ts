import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { aiShadowsUrlOff, keepTree, pickTier, pixelRatioFor, posHash, settingsFor, thinInstances, thinScenery, trackDistance } from '../quality';

describe('tier', () => {
  const env = (o: Partial<Parameters<typeof pickTier>[0]>) => ({ coarse: false, maxTouchPoints: 0, search: '', stored: null, ...o });
  it('phone on a coarse touch device, desktop otherwise', () => {
    expect(pickTier(env({ coarse: true, maxTouchPoints: 5 }))).toEqual({ tier: 'phone', reason: 'auto', touch: true });
    expect(pickTier(env({ coarse: false, maxTouchPoints: 10 }))).toEqual({ tier: 'desktop', reason: 'auto', touch: false }); // touch laptop
    expect(pickTier(env({ coarse: true, maxTouchPoints: 0 })).tier).toBe('desktop');
  });
  it('?phone=1 / 0 win; a stored choice forces the render tier but not the touch controls', () => {
    expect(pickTier(env({ search: '?phone=1' }))).toEqual({ tier: 'phone', reason: 'url', touch: true });
    expect(pickTier(env({ search: '?phone=0', coarse: true, maxTouchPoints: 5 })).tier).toBe('desktop');
    expect(pickTier(env({ stored: 'desktop', coarse: true, maxTouchPoints: 5 }))).toEqual({ tier: 'desktop', reason: 'forced', touch: true });
    expect(pickTier(env({ stored: 'phone' }))).toEqual({ tier: 'phone', reason: 'forced', touch: false });
  });
  it('AI draw caps', () => {
    expect(settingsFor('phone', 'auto', true).maxAiCarsDrawn).toBe(20);
    expect(settingsFor('desktop', 'auto', false).maxAiCarsDrawn).toBe(45);
    expect(settingsFor('phone', 'auto', true).shadows).toBe(false);
  });
  it('AI shadows: desktop 8 casters in a ±30 m / 2048 px box; phone and ?aishadows=0 keep the ±7 m / 1024 px player box', () => {
    const d = settingsFor('desktop', 'auto', false);
    expect([d.aiShadowCasters, d.shadowBoxM, d.shadowMapSize]).toEqual([8, 30, 2048]);
    const off = settingsFor('desktop', 'auto', false, { aiShadows: false });
    expect([off.aiShadowCasters, off.shadowBoxM, off.shadowMapSize]).toEqual([0, 7, 1024]);
    const p = settingsFor('phone', 'auto', true);
    expect([p.aiShadowCasters, p.shadowBoxM, p.shadowMapSize]).toEqual([0, 7, 1024]);
    expect(aiShadowsUrlOff('?aishadows=0')).toBe(true);
    expect(aiShadowsUrlOff('?aishadows=1')).toBe(false);
    expect(aiShadowsUrlOff('')).toBe(false);
  });
});

describe('balanced tier', () => {
  const env = (o: Partial<Parameters<typeof pickTier>[0]>) => ({ coarse: false, maxTouchPoints: 0, search: '', stored: null, ...o });
  it('settings: 30 AI cars drawn, 4 casters at 2048 px, 2.5 MP, anisotropy 8, shadows on', () => {
    const b = settingsFor('balanced', 'forced', false);
    expect([b.tier, b.device, b.maxAiCarsDrawn, b.aiShadowCasters, b.shadowMapSize, b.maxPixels, b.maxAnisotropy, b.shadows]).toEqual(['balanced', 'desktop', 30, 4, 2048, 2.5e6, 8, true]);
    expect(settingsFor('balanced', 'forced', false, { aiShadows: false }).aiShadowCasters).toBe(0);
    expect(settingsFor('balanced', 'forced', true, { device: 'tablet' }).device).toBe('tablet');
  });
  it('is a stored choice; ?phone= still wins; an unknown stored value is auto', () => {
    expect(pickTier(env({ stored: 'balanced' }))).toEqual({ tier: 'balanced', reason: 'forced', touch: false });
    expect(pickTier(env({ stored: 'balanced', search: '?phone=1' })).tier).toBe('phone');
    expect(pickTier(env({ stored: 'balanced', search: '?phone=0' })).tier).toBe('desktop');
    expect(pickTier(env({ stored: 'ultra' })).reason).toBe('auto');
  });
  it('pixel budget: a 1080p window at ratio 2 renders at most 2.5 MP', () => {
    const r = pixelRatioFor(settingsFor('balanced', 'forced', false), 2, 1920, 1080);
    expect(1920 * 1080 * r * r).toBeLessThanOrEqual(2.5e6 + 1);
    expect(r).toBeGreaterThan(1);
  });
});

describe('desktop trims (perf round 1)', () => {
  it('budget 3.5 MP, anisotropy 16', () => {
    const d = settingsFor('desktop', 'auto', false);
    expect(d.maxPixels).toBe(3.5e6); expect(d.maxAnisotropy).toBe(16);
  });
});

describe('pixel ratio', () => {
  const phone = settingsFor('phone', 'auto', true), desk = settingsFor('desktop', 'auto', false);
  it('phone: ≤ 1 and ≤ 1.2 MP', () => {
    expect(pixelRatioFor(phone, 3, 844, 390)).toBe(1);
    const r = pixelRatioFor(phone, 2, 1366, 1024); // iPad
    expect(r).toBeLessThan(1);
    expect(1366 * 1024 * r * r).toBeLessThanOrEqual(1.2e6 + 1);
  });
  it('desktop: ≤ 1.5 as before', () => {
    expect(pixelRatioFor(desk, 2, 1920, 1080)).toBeCloseTo(Math.sqrt(3.5e6 / (1920 * 1080)), 6); // retina at 1.5 would be 4.7 MP: the budget wins
    expect(pixelRatioFor(desk, 1, 1920, 1080)).toBe(1);
    const k = pixelRatioFor(desk, 2, 3840, 2160); // a 4K display: the 3.5 MP budget
    expect(3840 * 2160 * k * k).toBeLessThanOrEqual(3.5e6 + 1);
    expect(pixelRatioFor(desk, 1, 1920, 1080)).toBe(1);
  });
});

describe('scenery thinning', () => {
  it('keeps every tree near the track, about half mid-range, a quarter far', () => {
    expect(keepTree(10, 0.99)).toBe(true);
    let mid = 0, far = 0;
    for (let i = 0; i < 4000; i++) { const h = posHash(i * 3.1, i * 7.7); if (keepTree(200, h)) mid++; if (keepTree(900, h)) far++; }
    expect(mid / 4000).toBeGreaterThan(0.4); expect(mid / 4000).toBeLessThan(0.6);
    expect(far / 4000).toBeGreaterThan(0.18); expect(far / 4000).toBeLessThan(0.32);
  });
  it('track distance via the grid matches brute force', () => {
    const center: [number, number, number][] = [];
    for (let i = 0; i < 400; i++) center.push([Math.cos(i / 400 * 2 * Math.PI) * 300, Math.sin(i / 400 * 2 * Math.PI) * 200, 0]);
    const d = trackDistance({ center });
    for (const [x, y] of [[0, 0], [310, 5], [-900, 40], [12, 260], [2000, 2000]]) {
      const bf = Math.min(...center.map((c) => Math.hypot(c[0] - x, c[1] - y)));
      if (bf < 600) expect(d(x, y)).toBeCloseTo(bf, 6);
      else expect(d(x, y)).toBeGreaterThanOrEqual(600);
    }
  });
  it('compacts instance matrices and colours in place', () => {
    const im = new THREE.InstancedMesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial(), 6);
    const m = new THREE.Matrix4();
    for (let i = 0; i < 6; i++) { im.setMatrixAt(i, m.makeTranslation(i, 0, -i)); im.setColorAt(i, new THREE.Color(i / 10, 0, 0)); }
    const [a, b] = thinInstances(im, (x) => x % 2 === 0);
    expect([a, b]).toEqual([6, 3]);
    expect(im.count).toBe(3);
    const p = new THREE.Vector3();
    const xs = [0, 1, 2].map((k) => { im.getMatrixAt(k, m); return p.setFromMatrixPosition(m).x; });
    expect(xs).toEqual([0, 2, 4]);
    const c = new THREE.Color(); im.getColorAt(2, c);
    expect(c.r).toBeCloseTo(0.4, 6);
  });
  it('thins only the trees group; crowns and trunks of one tree agree', () => {
    const scene = new THREE.Scene();
    const trees = new THREE.Group(); trees.name = 'trees'; scene.add(trees);
    const crowns = new THREE.InstancedMesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial(), 200);
    const trunks = new THREE.InstancedMesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial(), 200);
    const other = new THREE.InstancedMesh(new THREE.BoxGeometry(), new THREE.MeshBasicMaterial(), 200);
    const m = new THREE.Matrix4();
    for (let i = 0; i < 200; i++) {
      const x = 100 + i * 7.3, north = (i % 13) * 3;
      crowns.setMatrixAt(i, m.makeTranslation(x, 5, -north));
      trunks.setMatrixAt(199 - i, m.makeTranslation(x, 2, -north)); // different order, same positions
      other.setMatrixAt(i, m.makeTranslation(x, 0, -north));
    }
    trees.add(crowns, trunks); scene.add(other);
    const r = thinScenery(scene, { center: [[0, 0, 0], [50, 0, 0]] });
    expect(r.meshes).toBe(2);
    expect(crowns.count).toBe(trunks.count);
    expect(crowns.count).toBeLessThan(200);
    expect(other.count).toBe(200);
  });
});
