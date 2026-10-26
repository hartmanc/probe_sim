// Upshift note shaping (audio-field.ts ShiftDrop, round two of the engine sounds, 26 Oct 2026). The rpm-follow logic is
// tested without Web Audio against the physics itself: an AI car (built exactly as the race builds it) and the Probe at
// full throttle with autoShift, sampled at 60 Hz like the race mode's audio update.
import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { EngineVoice, ShiftDrop, SHIFT_DROP_MAX_S, type FamilyAssets } from '../audio-field';
import { boxRpmOf, fillAudioCar, type AudioGearbox } from '../modes/race';
import type { FieldAudioCar } from '../modes/mode';
import { Vehicle, loadCarSpec, type CarSpec } from '../../physics/index';
import { createFlatSurface } from '../../physics/devtrack';
import { buildAiSpec, parseIdentity } from '../../physics/ai/field';

const probeJson = JSON.parse(readFileSync('public/cars/probe_gt/car.json', 'utf8'));
const ids = parseIdentity(JSON.parse(readFileSync('public/cars/field/identity.json', 'utf8')));

interface Frame { t: number; rpm: number; thr: number; gear: number; box: number | undefined }

/** Full throttle from rest, autoShift, physics at 1 kHz, frames at 60 Hz (as race.ts feeds the field audio). */
function drive(spec: CarSpec, T = 14): Frame[] {
  const car = new Vehicle(spec, { autoShift: true });
  const flat = createFlatSurface();
  car.reset([0, 0, 0], 0);
  const gb: AudioGearbox = { ratios: spec.drivetrain.gearRatios, radius: spec.wheel.radius };
  const inp = { steer: 0, throttle: 1, brake: 0, shiftUp: false, shiftDown: false, handbrake: false };
  const out: Frame[] = [];
  let next = 0;
  for (let i = 1; i <= T * 1000; i++) {
    car.step(inp, flat, 0.001);
    if (i / 1000 >= next) {
      const s = car.state;
      out.push({ t: i / 1000, rpm: s.rpm, thr: s.throttleOut, gear: s.gear, box: boxRpmOf(s, gb) });
      next += 1 / 60;
    }
  }
  return out;
}

const cars: [string, CarSpec][] = [
  ['#38 (modern_i4_stock)', buildAiSpec(probeJson, ids.get('38') ?? null, 1)],
  ['#41 (classic_v8_lowrev)', buildAiSpec(probeJson, ids.get('41') ?? null, 1)],
  ['Probe', loadCarSpec(probeJson)],
];

describe('ShiftDrop against the physics', () => {
  for (const [name, spec] of cars) {
    it(`${name}: the note drops with the clutch on every upshift, and is the physics rpm everywhere else`, () => {
      const fr = drive(spec);
      const sd = new ShiftDrop();
      const played = fr.map((f, k) => sd.step(f.rpm, f.gear, f.box, k ? f.t - fr[k - 1].t : 1 / 60));
      const ups = fr.map((f, k) => (k > 0 && f.gear > fr[k - 1].gear && fr[k - 1].gear >= 1 ? k : -1)).filter((k) => k > 0);
      expect(ups.length).toBeGreaterThanOrEqual(2);
      let checked = 0;
      for (const k of ups) {
        const r0 = fr[k - 1].rpm;
        // the physics: its minimum after the shift and how long it takes to cover 90 % of the drop
        let kMin = k;
        for (let j = k; j < Math.min(fr.length, k + 60); j++) if (fr[j].rpm < fr[kMin].rpm) kMin = j;
        const drop = r0 - fr[kMin].rpm;
        if (drop < 0.08 * r0) continue; // wheelspin shift: the engine hardly falls, nothing to shape
        checked++;
        const reach = (xs: number[]) => { for (let j = k; j < Math.min(fr.length, k + 60); j++) if (xs[j] <= r0 - 0.9 * drop) return fr[j].t - fr[k].t; return Infinity; };
        const tPhys = reach(fr.map((f) => f.rpm));
        const tPlay = reach(played);
        expect(tPhys).toBeGreaterThan(0.3);   // the slipping clutch's glide this fixes
        expect(tPlay).toBeLessThanOrEqual(0.2); // drops with the clutch
        // never above the physics, never below the road-speed clutch side
        for (let j = k; j < Math.min(fr.length, k + 60); j++) {
          expect(played[j]).toBeLessThanOrEqual(fr[j].rpm + 1e-9);
          expect(played[j]).toBeGreaterThanOrEqual(Math.min(fr[j].rpm, fr[j].box ?? 0) * 0.98);
        }
      }
      expect(checked).toBeGreaterThanOrEqual(1);
      // back on the physics rpm within the cap, and never a jump back up (rejoining is smooth: no rise per frame
      // bigger than the physics' own rise + 1 %, or 3 %)
      for (let k = 1; k < fr.length; k++) {
        const sinceUp = Math.min(...ups.map((u) => (k >= u ? fr[k].t - fr[u].t : Infinity)));
        if (sinceUp > SHIFT_DROP_MAX_S + 0.5) expect(played[k]).toBe(fr[k].rpm);
        const riseP = (played[k] - played[k - 1]) / played[k - 1];
        const riseR = (fr[k].rpm - fr[k - 1].rpm) / fr[k - 1].rpm;
        expect(riseP).toBeLessThanOrEqual(Math.max(0.03, riseR + 0.01));
      }
      // before the first upshift the voice plays the physics rpm exactly
      for (let k = 0; k < ups[0]; k++) expect(played[k]).toBe(fr[k].rpm);
    });
  }
});

describe('ShiftDrop edge cases', () => {
  it('passes the rpm through without gear / boxRpm, on downshifts and in neutral', () => {
    const sd = new ShiftDrop();
    expect(sd.step(5000, undefined, undefined, 1 / 60)).toBe(5000);
    expect(sd.step(5000, 3, 5000, 1 / 60)).toBe(5000);
    expect(sd.step(5200, 2, 3900, 1 / 60)).toBe(5200); // downshift (blip): untouched
    expect(sd.step(5200, 0, undefined, 1 / 60)).toBe(5200);
    expect(sd.shaping).toBe(false);
  });
  it('an upshift into a gear the engine already matches (no drop) is not shaped', () => {
    const sd = new ShiftDrop();
    sd.step(4000, 2, 4000, 1 / 60);
    expect(sd.step(4000, 3, 3990, 1 / 60)).toBe(4000);
    expect(sd.shaping).toBe(false);
  });
  it('lands at the new gear x the slip the engine ran at before the shift, and rejoins the engine when they meet', () => {
    const sd = new ShiftDrop();
    for (let k = 0; k < 120; k++) sd.step(6000, 2, 5455, 1 / 60); // 10 % wheelspin in 2nd
    let r = sd.step(6000, 3, 4000, 1 / 60);
    for (let k = 0; k < 12; k++) r = sd.step(6200, 3, 4000, 1 / 60); // the physics flares with the clutch slipping
    expect(r).toBeGreaterThan(4300);
    expect(r).toBeLessThan(4500);
    r = sd.step(4450, 3, 4010, 1 / 60);
    expect(r).toBe(4450);
    expect(sd.shaping).toBe(false);
  });
  it('blends back to the physics rpm after the cap if the two never meet', () => {
    const sd = new ShiftDrop();
    sd.step(6000, 2, 6000, 1 / 60);
    let r = 0;
    for (let k = 0; k < Math.ceil(SHIFT_DROP_MAX_S * 60) + 40; k++) r = sd.step(6000, 3, 4000, 1 / 60);
    expect(r).toBe(6000);
    expect(sd.shaping).toBe(false);
  });
});

describe('race-mode wiring', () => {
  it('boxRpmOf: road speed / radius x the gear ratio; fillAudioCar scales it with rpm_scale and only with a gearbox', () => {
    const st = { pos: [0, 0, 0] as [number, number, number], vel: [0, 0, 0] as [number, number, number], rpm: 3000, throttleOut: 1, gear: 2, speed: -15.3 };
    const gb: AudioGearbox = { ratios: [12, 8, 6], radius: 0.3 };
    expect(boxRpmOf(st, gb)).toBeCloseTo((51 * 8 * 60) / (2 * Math.PI), 6);
    expect(boxRpmOf({ ...st, gear: 0 }, gb)).toBeUndefined();
    const snd = { family: 'x', trim: 1, muffler: 0.3, rpmScale: 0.75 };
    const c: FieldAudioCar = { id: 1, pos: [0, 0, 0], vel: [0, 0, 0], rpm: 0, throttle: 0, redline: 0, family: '' };
    fillAudioCar(c, st, 6000, snd, gb);
    expect(c.gear).toBe(2);
    expect(c.boxRpm).toBeCloseTo(0.75 * (51 * 8 * 60) / (2 * Math.PI), 6);
    const c2: FieldAudioCar = { id: 1, pos: [0, 0, 0], vel: [0, 0, 0], rpm: 0, throttle: 0, redline: 0, family: '' };
    fillAudioCar(c2, st, 6000, snd);
    expect(c2.gear).toBeUndefined();
    expect(c2.boxRpm).toBeUndefined();
  });
});

// ---- EngineVoice: the option changes only the rpm it plays (a recording fake of the few nodes it builds)
/* eslint-disable @typescript-eslint/no-explicit-any */
class RParam { calls: [number, number][] = []; value = 0; setTargetAtTime(v: number, t: number) { this.calls.push([t, v]); this.value = v; return this; } setValueAtTime(v: number) { this.value = v; return this; } cancelScheduledValues() { return this; } }
class RNode { connect(d: any) { return d; } disconnect() { /* */ } }
class RGain extends RNode { gain = new RParam(); }
class RBiquad extends RNode { type = ''; frequency = new RParam(); Q = new RParam(); }
class RSrc extends RNode { buffer: any = null; loop = false; loopStart = 0; loopEnd = 0; playbackRate = new RParam(); onended: any = null; start() { /* */ } stop() { /* */ } }
function rctx() {
  const srcs: RSrc[] = [];
  return { srcs, ctx: { currentTime: 0, createGain: () => new RGain(), createBiquadFilter: () => new RBiquad(), createBufferSource: () => { const s = new RSrc(); srcs.push(s); return s; } } as any };
}
const assets = (): FamilyAssets => {
  const bins = [2000, 3000, 4000, 5000, 6000].map((rpm, i) => ({ rpm, on: { offset: i, duration: 1, rpm }, off: { offset: i, duration: 1, rpm } }));
  return { index: { sampleRate: 48000, bins } as any, on: {} as any, off: {} as any, binRpm: Float64Array.from(bins.map((b) => b.rpm)), idle: 900, redline: 6500 };
};

describe('EngineVoice with and without shiftDrop', () => {
  const run = (shiftDrop: boolean) => {
    const { srcs, ctx } = rctx();
    const v = new EngineVoice(ctx, new RNode() as any, assets(), shiftDrop ? { shiftDrop: true } : {});
    const seq: [number, number, number, number][] = [[6000, 1, 2, 6000], [6000, 1, 2, 6000], [5950, 0, 3, 4200], [5900, 0, 3, 4200],
      [5850, 0, 3, 4210], [5800, 0, 3, 4220], [5800, 0, 3, 4230], [5800, 0, 3, 4230], [5800, 0, 3, 4230], [5800, 0, 3, 4230], [5750, 1, 3, 4240]];
    seq.forEach(([rpm, thr, g, box], k) => { ctx.currentTime = k / 60; v.update(rpm, thr, 1, k / 60, g, box); });
    // the rpm each frame's rate targets imply: rate x loop rpm of the source it was set on
    return srcs.map((s) => s.playbackRate.calls.map(([t, r]) => [t, r]));
  };
  it('without the option the rates follow rpm / loop rpm (gear and boxRpm ignored); with it the note falls toward the clutch side', () => {
    const off = run(false), on = run(true);
    const lastRate = (calls: number[][][]) => Math.max(...calls.map((c) => c.length ? c[c.length - 1][1] : 0));
    // without: last frame rpm 5750 on the 5000 / 6000 bins -> rates 1.15 / 0.958
    expect(lastRate(off)).toBeCloseTo(5750 / 5000, 6);
    // with: after 10 frames (0.17 s) the note sits near 4240 -> rates on the 4000 / 5000 bins, all below 5750 / 5000
    expect(lastRate(on)).toBeLessThan(5750 / 5000 - 0.05);
  });
});
