import { afterEach, describe, expect, it, vi } from 'vitest';
import { LoadProgress, loadIsSlow, mbReadout, streamBytes, throttled } from '../load-progress';

const stages = [{ id: 'a', weight: 0.25 }, { id: 'b', weight: 0.75 }];

describe('LoadProgress', () => {
  it('starts at 0 and ends at 1 only when every stage has ended', () => {
    const p = new LoadProgress(stages);
    expect(p.fraction()).toBe(0);
    p.end('a'); expect(p.fraction()).toBeCloseTo(0.25, 9);
    p.end('b'); expect(p.fraction()).toBe(1);
  });
  it('bytes move the bar inside the stage weight, byte-weighted across the stage\'s files', () => {
    const p = new LoadProgress(stages);
    p.bytes('b', 'big', 400, 800); p.bytes('b', 'small', 0, 200);
    expect(p.fraction()).toBeCloseTo(0.75 * (400 / 1000), 9);
    p.bytes('b', 'small', 200, 200);
    expect(p.fraction()).toBeCloseTo(0.75 * (600 / 1000), 9);
  });
  it('never reaches the stage weight on bytes alone (decode and parse still follow)', () => {
    const p = new LoadProgress(stages);
    p.bytes('b', 'f', 1000, 1000);
    expect(p.fraction()).toBeLessThan(0.75);
    p.end('b'); expect(p.fraction()).toBeCloseTo(0.75, 9);
  });
  it('is monotone non-decreasing even when reports arrive out of order or overshoot', () => {
    const p = new LoadProgress(stages);
    let last = 0;
    for (const [g, t] of [[100, 1000], [50, 1000], [900, 1000], [2000, 1000], [10, 1000]] as const) {
      p.bytes('b', 'f', g, t);
      const f = p.fraction();
      expect(f).toBeGreaterThanOrEqual(last); last = f;
    }
  });
  it('a missing Content-Length degrades to the stage tick', () => {
    const p = new LoadProgress(stages);
    p.bytes('b', 'f', 123456, undefined); p.bytes('b', 'g', 99, 0);
    expect(p.fraction()).toBe(0);
    p.end('b'); expect(p.fraction()).toBeCloseTo(0.75, 9);
  });
});

describe('throttled', () => {
  it('delivers at most every ms, and always the last value', () => {
    let t = 0; const seen: number[] = []; const timers: (() => void)[] = [];
    const th = throttled<number>((v) => seen.push(v), 100, () => t, (f) => { timers.push(f); });
    th.push(1); t = 30; th.push(2); t = 60; th.push(3);
    expect(seen).toEqual([1]);
    t = 100; timers.shift()!();
    expect(seen).toEqual([1, 3]);
    t = 250; th.push(4); expect(seen).toEqual([1, 3, 4]);
  });
});

describe('mbReadout and the slow-load decision', () => {
  it('one decimal, with the total when it is known', () => {
    expect(mbReadout(0.4 * 1048576, 1.7 * 1048576)).toBe('0.4 of 1.7 MB');
    expect(mbReadout(5 * 1048576, 1.7 * 1048576)).toBe('1.7 of 1.7 MB');   // never past the total
    expect(mbReadout(2.26 * 1048576, 0)).toBe('2.3 MB');
  });
  it('no movement for 20 s is slow', () => {
    expect(loadIsSlow(1000, 20999)).toBe(false);
    expect(loadIsSlow(1000, 21000)).toBe(true);
  });
});

describe('streamBytes', () => {
  afterEach(() => { vi.useRealTimers(); });
  const plainOf = (n: number) => () => Promise.resolve(new Response(new Uint8Array(n), { headers: { 'content-type': 'application/octet-stream' } }));
  const hang = (len: number) => new Response(new ReadableStream<Uint8Array>({ start(c) { c.enqueue(new Uint8Array(10)); }, pull() { return new Promise(() => {}); } }), { headers: { 'content-length': String(len) } });

  it('streams a file and counts its bytes against Content-Length', async () => {
    const seen: [number, number][] = [];
    const r = await streamBytes('f', { open: () => Promise.resolve(new Response(new Uint8Array(100), { headers: { 'content-length': '100' } })), onBytes: (g, t) => seen.push([g, t]) });
    expect(r?.buf.byteLength).toBe(100);
    expect(seen[0]).toEqual([0, 100]);
    expect(seen[seen.length - 1]).toEqual([100, 100]);
  });
  it('no chunk for 5 s: cancels, aborts and re-fetches plainly, logging one line', async () => {
    vi.useFakeTimers();
    const logs: string[] = [];
    let calls = 0;
    const open = (signal?: AbortSignal) => { calls++; return calls === 1 ? Promise.resolve(hang(1000)) : plainOf(1000)(); void signal; };
    const p = streamBytes('heightfield.bin', { open, log: (m) => logs.push(m) });
    await vi.advanceTimersByTimeAsync(4900);
    expect(calls).toBe(1);                       // still waiting
    await vi.advanceTimersByTimeAsync(200);
    const r = await p;
    expect(calls).toBe(2);
    expect(r?.buf.byteLength).toBe(1000);
    expect(logs).toEqual(['[loader] heightfield.bin: stream stalled after 10 bytes, re-fetched plainly']);
  });
  it('a read error falls back to the plain fetch, never to null', async () => {
    let calls = 0;
    const bad = new Response(new ReadableStream<Uint8Array>({ start(c) { c.enqueue(new Uint8Array(3)); }, pull(c) { c.error(new Error('boom')); } }), { headers: { 'content-length': '500' } });
    const r = await streamBytes('ortho.jpg', { open: () => { calls++; return calls === 1 ? Promise.resolve(bad) : plainOf(500)(); }, log: () => {} });
    expect(calls).toBe(2);
    expect(r).not.toBeNull();
    expect(r!.buf.byteLength).toBe(500);
  });
  it('a body that is not a stream goes straight to the plain fetch', async () => {
    let calls = 0;
    const noBody = { headers: new Headers({ 'content-length': '7' }), body: null, arrayBuffer: () => Promise.resolve(new ArrayBuffer(7)) } as unknown as Response;
    const r = await streamBytes('f', { open: () => { calls++; return calls === 1 ? Promise.resolve(noBody) : plainOf(7)(); }, log: () => {} });
    expect(r?.buf.byteLength).toBe(7);
  });
  it('only a real missing file gives null', async () => {
    expect(await streamBytes('gone', { open: () => Promise.resolve(null) })).toBeNull();
  });
});
