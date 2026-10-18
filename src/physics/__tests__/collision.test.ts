import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, test } from 'vitest';
import { createCollisionWorld, createTrackSurface, LAUNCH_SPEED, Vehicle } from '../index';
import type { TrackJson } from '../index';
import { createDevScenery, createDevTrack, devGround } from '../devtrack';
import { DT, G, input, probeSpec } from './helpers';

const dev = createDevTrack();
const sc = createDevScenery(dev.options);
const surf = createTrackSurface(dev.track, dev.heightfield, { far: sc.far });
const world = createCollisionWorld(sc.scenery, dev.track);
const FRONT = probeSpec().hull.front;

function car(x: number, y: number, heading: number, speed: number): Vehicle {
  const v = new Vehicle(probeSpec(), { autoShift: true });
  v.setCollisionWorld(world);
  v.reset([x, y, surf.sample(x, y).z], heading, speed);
  return v;
}

describe('collisions', () => {
  test('10 m/s head-on into Armco: stops or bounces, never passes through', () => {
    const c = car(0, sc.armcoY + 6.5, -Math.PI / 2, 10);
    let minY = Infinity;
    for (let i = 0; i < 3000; i++) {
      c.step(input(), surf, DT);
      minY = Math.min(minY, c.state.pos[1]);
    }
    const s = c.state;
    console.log(`armco 10 m/s: impact ${s.impact?.speedNormal.toFixed(1)} m/s (${s.impact?.kind}), nose min gap ${(minY - FRONT - sc.armcoY).toFixed(3)} m, final vy ${s.vel[1].toFixed(2)}`);
    expect(s.impact?.kind).toBe('armco');
    expect(s.impact!.speedNormal).toBeGreaterThan(8);
    expect(minY - FRONT).toBeGreaterThan(sc.armcoY - 0.15); // nose never more than 15 cm into the rail
    expect(s.vel[1]).toBeGreaterThan(-0.2);
    expect(s.launched).toBe(false);
    expect(c.nanResets).toBe(0);
  });

  test('20° glancing hit slides along the wall and keeps most of its speed', () => {
    const a = (20 * Math.PI) / 180;
    const c = car(-120, sc.armcoY + 4, -a, 25);
    const inp = input({ throttle: 0.3 });
    let minY = Infinity, hit = false;
    for (let i = 0; i < 2000; i++) {
      c.step(inp, surf, DT);
      minY = Math.min(minY, c.state.pos[1]);
      if (c.state.impact) hit = true;
    }
    const s = c.state;
    const sp = Math.hypot(s.vel[0], s.vel[1]);
    console.log(`glancing 25 m/s @20°: impact ${s.impact?.speedNormal.toFixed(1)} m/s, speed after ${sp.toFixed(1)} m/s, x travelled ${(s.pos[0] + 120).toFixed(0)} m`);
    expect(hit).toBe(true);
    expect(sp).toBeGreaterThan(0.6 * 25);
    expect(s.pos[0]).toBeGreaterThan(-120 + 30);
    expect(minY).toBeGreaterThan(sc.armcoY + 0.5);
    expect(s.launched).toBe(false);
  });

  test('30 m/s into concrete blasts the car into space', () => {
    const c = car(0, sc.concreteY - 6.5, Math.PI / 2, 30);
    let tLaunch = -1;
    for (let i = 0; i < 4000; i++) {
      c.step(input({ throttle: 1 }), surf, DT);
      if (tLaunch < 0 && c.state.launched) tLaunch = i * DT;
    }
    const s = c.state;
    console.log(`concrete 30 m/s: launched at ${tLaunch.toFixed(3)} s, impact ${s.impact?.speedNormal.toFixed(1)} m/s, altitude after 4 s ${(s.pos[2] - devGround(s.pos[0], s.pos[1], dev.options)).toFixed(0)} m`);
    expect(s.launched).toBe(true);
    expect(s.impact!.speedNormal).toBeGreaterThan(LAUNCH_SPEED);
    expect(s.launchedAt).toBeGreaterThan(0);
    expect(s.pos[2]).toBeGreaterThan(200);
    expect(s.vel[1]).toBeLessThan(0); // thrown back off the wall
    // reset clears it
    c.reset([0, 0, 0], 0);
    expect(c.state.launched).toBe(false);
    expect(c.state.impact).toBeNull();
  });

  test('tyre wall at 40 m/s (90 mph) launches the car into space', () => {
    const x0 = (dev.track.length_m - 2 * Math.PI * dev.options.radius) / 2 / 2 + dev.options.radius + dev.options.halfWidth + 4;
    const c = car(x0 - 8, 0, 0, 40);
    for (let i = 0; i < 3000 && !c.state.launched; i++) c.step(input(), surf, DT);
    expect(c.state.launched).toBe(true);
  });

  test('tyre wall at 20 m/s absorbs the hit without a launch', () => {
    const x0 = (dev.track.length_m - 2 * Math.PI * dev.options.radius) / 2 / 2 + dev.options.radius + dev.options.halfWidth + 4;
    const c = car(x0 - 8, 0, 0, 20);
    let maxX = -Infinity;
    for (let i = 0; i < 3000; i++) { c.step(input(), surf, DT); maxX = Math.max(maxX, c.state.pos[0]); }
    expect(c.state.launched).toBe(false);
    expect(c.state.impact?.kind).toBe('tyres');
    expect(maxX + FRONT).toBeLessThan(x0 + 0.6);
  });

  test('tree trunk stops a car', () => {
    const c = car(sc.tree.x - 8, sc.tree.y + 0.3, 0, 12);
    let maxX = -Infinity;
    for (let i = 0; i < 2000; i++) { c.step(input(), surf, DT); maxX = Math.max(maxX, c.state.pos[0]); }
    expect(c.state.impact?.kind).toBe('tree');
    expect(maxX + FRONT).toBeLessThan(sc.tree.x);
  });

  test('car 2 km from the circuit rests on the far heightfield', () => {
    const x = 2000, y = 300;
    const c = car(x, y, 0.4, 0);
    const z0 = sc.farGround(x, y);
    expect(z0).toBeGreaterThan(10); // the near grid would have said ~0
    for (let i = 0; i < 3000; i++) c.step(input(), surf, DT);
    const s = c.state;
    const sum = s.wheels.reduce((a, w) => a + w.load, 0);
    expect(Math.abs(s.pos[2] - sc.farGround(s.pos[0], s.pos[1]))).toBeLessThan(0.1);
    expect(Math.abs(sum - probeSpec().mass * G) / (probeSpec().mass * G)).toBeLessThan(0.03);
    expect(Math.hypot(...s.vel)).toBeLessThan(0.05);
  });

  test('the far boundary stops a car driven at it', () => {
    const c = car(world.bounds.x1 - 60, 100, 0, 30);
    let maxX = -Infinity;
    for (let i = 0; i < 6000; i++) { c.step(input({ throttle: 1 }), surf, DT); maxX = Math.max(maxX, c.state.pos[0]); }
    expect(c.state.impact?.kind).toBe('boundary');
    expect(c.state.launched).toBe(false);
    expect(maxX + FRONT).toBeLessThan(world.bounds.x1 + 0.2);
    expect(c.nanResets).toBe(0);
  });

  test('Laguna scenery builds and queries fast', () => {
    const dir = fileURLToPath(new URL('../../../public/tracks/laguna_seca/', import.meta.url));
    const track = JSON.parse(readFileSync(dir + 'track.json', 'utf8')) as TrackJson;
    const scenery = JSON.parse(readFileSync(dir + 'scenery.json', 'utf8'));
    const t0 = performance.now();
    const cw = createCollisionWorld(scenery, track);
    const tb = performance.now() - t0;
    expect(cw.nSeg).toBeGreaterThan(1000);
    expect(cw.nCyl).toBeGreaterThan(1000);
    const t1 = performance.now();
    let total = 0;
    for (let i = 0; i < 100000; i++) {
      const x = -400 + (i % 400) * 2, y = -300 + Math.floor(i / 400) * 3;
      total += cw.query(x - 3.5, y - 3.5, x + 3.5, y + 3.5);
    }
    const tq = (performance.now() - t1) / 100000;
    console.log(`Laguna collision world: ${cw.nSeg} segments, ${cw.nCyl} cylinders, built in ${tb.toFixed(0)} ms, query ${(tq * 1000).toFixed(2)} µs (avg ${(total / 1e5).toFixed(1)} items)`);
    expect(tq).toBeLessThan(0.005);
  });
});
