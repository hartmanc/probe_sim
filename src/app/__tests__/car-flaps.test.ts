// Wind-shaken inflatables: `flap_*` nodes lean back with speed and flutter out of phase with one another.
import { describe, expect, it } from 'vitest';
import * as THREE from 'three';
import { buildFallbackCar, CarRig, FLAP_LEAN } from '../car';

function rigWithFlaps(): CarRig {
  const model = buildFallbackCar();
  for (const name of ['flap_01', 'flap_02']) { const o = new THREE.Object3D(); o.name = name; o.position.set(0.5, 1, 1.9); model.add(o); }
  return new CarRig(model);
}
/** Backward tilt (rad) of a node's up axis in the car frame (+z forward): > 0 = top leaning toward the tail. */
function leanBack(o: THREE.Object3D): number {
  const up = new THREE.Vector3(0, 1, 0).applyQuaternion(o.quaternion);
  return Math.atan2(-up.z, up.y);
}

describe('flap shake', () => {
  it('finds the flap nodes and leaves them nearly upright at rest', () => {
    const rig = rigWithFlaps();
    expect(rig.flaps.map((f) => f.node.name)).toEqual(['flap_01', 'flap_02']);
    rig.shakeFlaps(0, 1.234);
    for (const f of rig.flaps) expect(Math.abs(leanBack(f.node))).toBeLessThan(0.06);
  });
  it('leans back more the faster the car goes, up to FLAP_LEAN, and the two nodes do not move in unison', () => {
    const rig = rigWithFlaps();
    const mean = (v: number) => { let s = 0; const n = 200; for (let k = 0; k < n; k++) { rig.shakeFlaps(v, k * 0.013); s += leanBack(rig.flaps[0].node); } return s / n; };
    const slow = mean(10), fast = mean(40);
    expect(fast).toBeGreaterThan(slow + 0.2);
    expect(fast).toBeLessThan(FLAP_LEAN + 0.25);
    rig.shakeFlaps(40, 0.7);
    expect(Math.abs(leanBack(rig.flaps[0].node) - leanBack(rig.flaps[1].node))).toBeGreaterThan(0.01);
  });
  it('brake lamps: a `brake` material glows and lamp discs show only while braking', () => {
    const model = buildFallbackCar();
    const lamp = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.1, 0.02), new THREE.MeshStandardMaterial({ name: 'car99_brake', color: 0x991111 }));
    model.add(lamp);
    const rig = new CarRig(model);
    rig.addBrakeLamps([[0.5, 0.8, -2.0, 0.05], [-0.5, 0.8, -2.0, 0.05]]);
    const discs = rig.root.getObjectByName('brake_lamps')!;
    expect(discs.children.length).toBe(2);
    expect(discs.visible).toBe(false);
    expect((lamp.material as THREE.MeshStandardMaterial).emissiveIntensity).toBe(0);
    rig.setBrakeLights(true);
    expect(discs.visible).toBe(true);
    expect((lamp.material as THREE.MeshStandardMaterial).emissiveIntensity).toBeGreaterThan(1);
    rig.setBrakeLights(false);
    expect(discs.visible).toBe(false);
    expect((lamp.material as THREE.MeshStandardMaterial).emissiveIntensity).toBe(0);
  });
  it('a model without flap nodes is untouched', () => {
    const rig = new CarRig(buildFallbackCar());
    expect(rig.flaps).toEqual([]);
    rig.shakeFlaps(40, 1);
  });
});
