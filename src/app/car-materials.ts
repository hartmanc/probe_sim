// Car materials for the look (look.ts): paint and liveries get a clear coat (MeshPhysicalMaterial), glass a wet,
// reflective finish; every other glTF material stays as built. Reflections come from scene.environment.
import * as THREE from 'three';

/** Material names that are the painted body: the Probe's `paint`, the kit's `car<N>_livery` / `_body`. */
export const PAINT_RE = /(^|_)(paint|livery|body)$/i;
export const GLASS_RE = /(^|_)glass$/i;
export const CLEARCOAT = 0.7;
export const CLEARCOAT_ROUGHNESS = 0.12;

function physicalFrom(st: THREE.MeshStandardMaterial): THREE.MeshPhysicalMaterial {
  const p = new THREE.MeshPhysicalMaterial();
  // copy the standard properties only (MeshPhysicalMaterial.copy expects a physical source); keep the PHYSICAL define
  THREE.MeshStandardMaterial.prototype.copy.call(p, st);
  p.defines = { STANDARD: '', PHYSICAL: '' };
  p.name = st.name;
  p.userData = { ...st.userData, lookUpgraded: true };
  return p;
}

/**
 * Replace paint and glass materials under `root` (shared materials are replaced once). `clearcoat` false (phone
 * tier) leaves the paint alone and only upgrades the glass. Returns the number of materials replaced.
 */
export function upgradeCarMaterials(root: THREE.Object3D, opts: { clearcoat?: boolean } = {}): number {
  const cc = opts.clearcoat ?? true;
  const done = new Map<THREE.Material, THREE.Material>();
  let n = 0;
  root.traverse((o) => {
    const m = o as THREE.Mesh;
    if (!m.isMesh || !m.material) return;
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    const out = mats.map((mat) => {
      const had = done.get(mat);
      if (had) return had;
      const st = mat as THREE.MeshStandardMaterial;
      if (!st.isMeshStandardMaterial || (st as THREE.MeshPhysicalMaterial).isMeshPhysicalMaterial || st.userData.lookUpgraded) return mat;
      let rep: THREE.MeshPhysicalMaterial | null = null;
      if (cc && PAINT_RE.test(st.name)) {
        rep = physicalFrom(st);
        rep.clearcoat = CLEARCOAT; rep.clearcoatRoughness = CLEARCOAT_ROUGHNESS;
        // scene.environmentIntensity (look.ts ENV_INTENSITY) scales this: the cars keep lively reflections while the ground stays calm
        rep.roughness = Math.min(st.roughness, 0.5); rep.metalness = 0; rep.envMapIntensity = 1.4;
      } else if (GLASS_RE.test(st.name)) {
        rep = physicalFrom(st);
        rep.roughness = 0.04; rep.metalness = 0; rep.envMapIntensity = 2.2;
      }
      if (!rep) return mat;
      done.set(mat, rep); n++;
      return rep;
    });
    m.material = Array.isArray(m.material) ? out : out[0];
  });
  return n;
}
