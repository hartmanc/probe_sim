import carJson from '../../../public/cars/probe_gt/car.json';
import { loadCarSpec, type CarSpec, type DriverInput } from '../index';

export function probeJson(): any {
  return JSON.parse(JSON.stringify(carJson));
}

export function probeSpec(mod?: (j: any) => void): CarSpec {
  const j = probeJson();
  mod?.(j);
  return loadCarSpec(j);
}

export function input(p: Partial<DriverInput> = {}): DriverInput {
  return { steer: 0, throttle: 0, brake: 0, shiftUp: false, shiftDown: false, handbrake: false, ...p };
}

export const DT = 0.001;
export const G = 9.81;

/** Body z axis (up) in world, from quaternion (x, y, z, w). */
export function bodyUp(q: readonly number[]): [number, number, number] {
  const [x, y, z, w] = q;
  return [2 * (x * z + y * w), 2 * (y * z - x * w), 1 - 2 * (x * x + y * y)];
}

export function yawOf(q: readonly number[]): number {
  const [x, y, z, w] = q;
  return Math.atan2(2 * (x * y + z * w), 1 - 2 * (y * y + z * z));
}

/** Deterministic PRNG (mulberry32). */
export function rng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
