// The race Worker (?worker=1): message shell around RaceSimHost (race-host.ts). The main thread is race-worker-client.ts.
import { RaceSimHost, type HostBuild, type HostInit, type HostInput } from './race-host';

type In =
  | ({ type: 'init' } & HostInit)
  | ({ type: 'build' } & HostBuild)
  | ({ type: 'input' } & HostInput)
  | { type: 'run'; on: boolean }
  | { type: 'flush' }
  | { type: 'recover'; s: number }
  | { type: 'violation'; kind: string; detail?: string };

const host = new RaceSimHost();
const ctx = self as unknown as { postMessage(m: unknown, t?: Transferable[]): void; onmessage: ((e: MessageEvent<In>) => void) | null };
const POST_EVERY_MS = 14;
let lastPost = 0;

const post = (now: number): void => {
  const s = host.snapshot(now);
  if (s) ctx.postMessage(s, [s.f32.buffer, s.f64.buffer]);
  lastPost = now;
};

// the worker's own clock: a short timer, stepping to real time (RaceSimHost.tick); a snapshot about every 14 ms
setInterval(() => {
  const now = performance.now();
  if (!host.running) return;
  host.tick(now);
  if (now - lastPost >= POST_EVERY_MS) post(now);
}, 3);

ctx.onmessage = (e) => {
  const m = e.data;
  const now = performance.now();
  switch (m.type) {
    case 'init': host.init(m); ctx.postMessage({ type: 'ready' }); break;
    case 'build': host.build(m, now); post(now); break;
    case 'input': host.input(m); break;
    case 'run': host.setRunning(m.on, now); break;
    case 'recover': host.recover(m.s); break;
    case 'violation': host.violation(m.kind, m.detail); break;
    case 'flush': ctx.postMessage(host.flush() ?? { type: 'rec', gen: host.gen, none: true }); break;
  }
};
