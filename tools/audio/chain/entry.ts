// Browser side of the real-chain renderer (render_chain.ts bundles this with esbuild): the game's own EngineVoice
// (src/app/audio-field.ts) or CarAudio (src/app/audio.ts) in an OfflineAudioContext, updated at the scenario's frame
// rate exactly as the race mode does (one update per frame at ctx.currentTime, suspended between frames).
import { EngineVoice, loadFamily, type VoiceOptions } from '../../../src/app/audio-field';
import { CarAudio } from '../../../src/app/audio';
import type { VehicleState, WheelState } from '../../../src/app/physics-types';

export interface Job {
  family: string;
  /** family engine.json url (relative to the page), or null for the Probe's CarAudio (public/audio/) */
  engineUrl: string | null;
  fps: number;
  rpm: number[]; thr: number[];
  gear?: number[]; boxRpm?: number[];
  opts?: VoiceOptions & { shiftDrop?: boolean };
  idle?: number; redline?: number;
  seed?: number;
}

function seeded(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function b64(f: Float32Array): string {
  const u = new Uint8Array(f.buffer);
  let s = '';
  for (let i = 0; i < u.length; i += 0x8000) s += String.fromCharCode.apply(null, Array.from(u.subarray(i, i + 0x8000)));
  return btoa(s);
}

const wheel = (): WheelState => ({ load: 0, slipAngle: 0, slipRatio: 0, onTrack: true, paved: true } as unknown as WheelState);

async function render(job: Job): Promise<string> {
  Math.random = seeded(job.seed ?? 619);
  const SR = 48000;
  const n = job.rpm.length;
  const dur = n / job.fps;
  const ctx = new OfflineAudioContext(1, Math.round(dur * SR), SR);
  let step: (k: number, t: number) => void;
  if (job.engineUrl) {
    const assets = await loadFamily(ctx, job.engineUrl);
    const v = new EngineVoice(ctx, ctx.destination, assets, job.opts ?? {});
    v.output.gain.value = 1; // the 5 m reference distance: distance gain 1, no fade
    step = (k, t) => v.update(job.rpm[k], job.thr[k], 1, t, job.gear?.[k], job.boxRpm?.[k]);
  } else {
    const car = new CarAudio('audio/');
    car.configure({ idleRpm: job.idle ?? 850, revLimitRpm: job.redline ?? 6900 });
    await car.start(ctx);
    const st = { pos: [0, 0, 0], quat: [0, 0, 0, 1], vel: [0, 0, 0], angVel: [0, 0, 0], wheels: [wheel(), wheel(), wheel(), wheel()],
      rpm: 0, gear: 1, speed: 0, gLat: 0, gLong: 0, throttleOut: 0 } as unknown as VehicleState;
    step = (k) => { st.rpm = job.rpm[k]; st.throttleOut = job.thr[k]; st.gear = job.gear?.[k] ?? 1; car.update(st, job.thr[k]); };
  }
  for (let k = 0; k < n; k++) {
    const tk = k / job.fps;
    if (k === 0) { step(0, 0); continue; }
    ctx.suspend(tk).then(() => { step(k, ctx.currentTime); return ctx.resume(); });
  }
  const buf = await ctx.startRendering();
  return b64(buf.getChannelData(0));
}

(window as unknown as { renderEngine: typeof render }).renderEngine = render;
