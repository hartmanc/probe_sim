// Sound after a gamepad start (owner, 27 Oct 2026: "sometimes the sound doesn't load; if I refresh, typically I get it"):
// the browser's autoplay rule resumes an AudioContext only inside a real gesture (click, tap, key), and pad input is
// polled, so a session started from the pad used to keep a suspended context. prime(), called from any earlier gesture,
// makes the context then; start() takes it over; `suspended` tells the app to ask for a gesture when none has happened.
import { describe, expect, it, vi } from 'vitest';
import { CarAudio } from '../audio';

type Fake = BaseAudioContext & { state: string; resume: ReturnType<typeof vi.fn> };
function fakeCtx(): Fake {
  const c = { state: 'suspended' } as unknown as Fake;
  c.resume = vi.fn(async () => { c.state = 'running'; });
  return c;
}
/** A CarAudio whose graph, sample fetch and attach are stubbed: only the context handling runs. */
function quiet(): CarAudio {
  const a = new CarAudio();
  const r = a as unknown as Record<string, unknown>;
  r.buildGraph = () => undefined;
  r.preload = () => { r.fetched = Promise.resolve(null); };
  r.attachSamples = () => undefined;
  return a;
}

describe('audio unlock before a gamepad start', () => {
  it('prime() makes the context in the gesture and start() takes it over, resumed again', async () => {
    const a = quiet(); const made = fakeCtx(); const make = vi.fn(() => made);
    a.prime(make);
    expect(make).toHaveBeenCalledTimes(1);
    a.prime(make);                                   // a second gesture makes no second context
    expect(make).toHaveBeenCalledTimes(1);
    await a.start();                                 // the pad's start: no gesture, but the primed context is running
    expect((a as unknown as { ctx: unknown }).ctx).toBe(made);
    expect(made.resume).toHaveBeenCalledTimes(1);    // start() resumes the primed context (the fake factory did not)
    expect(a.suspended).toBe(false);
  });

  it('suspended is true while the browser keeps the context suspended, false once it runs or before any context', async () => {
    const a = quiet();
    expect(a.suspended).toBe(false);
    const stuck = fakeCtx(); stuck.resume = vi.fn(async () => undefined);   // a resume outside a gesture changes nothing
    await a.start(stuck);
    expect(a.suspended).toBe(true);
    stuck.state = 'running';
    expect(a.suspended).toBe(false);
  });

  it('prime() after start() only unlocks the running context', async () => {
    const a = quiet(); const c = fakeCtx(); c.state = 'running';
    await a.start(c);
    const make = vi.fn(fakeCtx);
    a.prime(make);
    expect(make).not.toHaveBeenCalled();
    expect((a as unknown as { ctx: unknown }).ctx).toBe(c);
  });
});
