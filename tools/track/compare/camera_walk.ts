// Drive proxy (build-track stage 4): walk the sim's hood camera round the whole lap and toward every inventory row,
// for the compare sheets (tools/track/compare/make_compare_sheets.py) that the orchestrator and the judge review
// before the owner drives. Replaces stills at builder-chosen spots.
//
//   npx tsx tools/track/compare/camera_walk.ts --track sonoma [--step 50] [--port 5179] [--camera hood] [--yaw 70]
//        [--out tools/track/compare/<id>/compare_sheets] [--no-rows] [--only s0,s1]
//
// Needs the dev server on the port (npx vite --port 5179 --strictPort). Launches its own headless Chrome with a
// throwaway profile (never the owner's browser) and drives the page over the DevTools protocol, the same hooks as the
// hood stills of 20 Oct (window.__sim): hot-lap mode, navigator.getGamepads = () => [], the car placed on the centre
// at station s facing the driving direction with __sim.vehicle.reset([x, y, z], heading, 0), 300 ms to settle, then
// one render of the hood camera read back in the same task (preserveDrawingBuffer is off). Side views turn the
// camera about its vertical axis by +-yaw. Output: <out>/sim/fwd_s####.jpg every step metres, <out>/sim/row_s####_<side>.jpg
// at every inventory row station and side (deduplicated per 10 m), and <out>/walk.json. Local only (ignored by git).
import { spawn, type ChildProcess } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const argv = process.argv.slice(2);
const opt = (k: string, d?: string) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d; };
const has = (k: string) => argv.includes(`--${k}`);
const ROOT = resolve(import.meta.dirname, '..', '..', '..');
const id = opt('track');
if (!id) { console.error('--track <id> required'); process.exit(2); }
const step = Number(opt('step', '50'));
const port = Number(opt('port', '5179'));
const camera = opt('camera', 'hood')!;
const yawDeg = Number(opt('yaw', '70'));
const out = resolve(opt('out', join(ROOT, 'tools/track/compare', id, 'compare_sheets'))!);
const only = opt('only')?.split(',').map(Number);
const chromeBin = opt('chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')!;
const W = Number(opt('width', '1280')), H = Number(opt('height', '720'));

const track = JSON.parse(readFileSync(join(ROOT, 'public/tracks', id, 'track.json'), 'utf8'));
const invPath = join(ROOT, 'tools/track/compare', id, 'inventory.json');
const inv = existsSync(invPath) ? JSON.parse(readFileSync(invPath, 'utf8')) : null;
const L: number = track.n * track.spacing_m;

function pose(s: number): { pos: [number, number, number]; heading: number } {
  const n = track.n, i = ((Math.round(s / track.spacing_m) % n) + n) % n;
  const a = track.center[(i - 2 + n) % n], b = track.center[(i + 2) % n], c = track.center[i];
  return { pos: [c[0], c[1], c[2]], heading: Math.atan2(b[1] - a[1], b[0] - a[0]) };
}

// ------------------------------------------------------------------ minimal DevTools protocol client
class CDP {
  private ws!: WebSocket; private id = 0; private wait = new Map<number, (m: any) => void>();
  async open(url: string) {
    this.ws = new WebSocket(url);
    await new Promise<void>((res, rej) => { this.ws.onopen = () => res(); this.ws.onerror = (e) => rej(e); });
    this.ws.onmessage = (ev) => { const m = JSON.parse(String(ev.data)); if (m.id && this.wait.has(m.id)) { this.wait.get(m.id)!(m); this.wait.delete(m.id); } };
  }
  send(method: string, params: Record<string, unknown> = {}): Promise<any> {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((res, rej) => this.wait.set(id, (m) => (m.error ? rej(new Error(`${method}: ${m.error.message}`)) : res(m.result))));
  }
  async eval<T = unknown>(expr: string): Promise<T> {
    const r = await this.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(`page: ${r.exceptionDetails.exception?.description ?? r.exceptionDetails.text}`);
    return r.result.value as T;
  }
  close() { try { this.ws.close(); } catch { /* closed */ } }
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

async function launch(): Promise<{ proc: ChildProcess; ws: string; profile: string }> {
  const profile = mkdtempSync(join(tmpdir(), 'camera-walk-'));
  const dbg = 9300 + Math.floor(Math.random() * 400);
  const proc = spawn(chromeBin, [
    '--headless=new', `--remote-debugging-port=${dbg}`, `--user-data-dir=${profile}`, `--window-size=${W},${H}`,
    '--no-first-run', '--no-default-browser-check', '--disable-extensions', '--mute-audio', '--ignore-gpu-blocklist',
    '--enable-webgl', '--use-angle=metal', 'about:blank',
  ], { stdio: 'ignore' });
  for (let k = 0; k < 100; k++) {
    await sleep(150);
    try {
      const list = await (await fetch(`http://127.0.0.1:${dbg}/json/list`)).json() as { type: string; webSocketDebuggerUrl: string }[];
      const page = list.find((t) => t.type === 'page');
      if (page) return { proc, ws: page.webSocketDebuggerUrl, profile };
    } catch { /* not up yet */ }
  }
  proc.kill();
  throw new Error('Chrome did not open its DevTools port');
}

async function main() {
  mkdirSync(join(out, 'sim'), { recursive: true });
  const { proc, ws, profile } = await launch();
  const cdp = new CDP();
  const shots: { file: string; s: number; side: 'fwd' | 'left' | 'right'; kind?: string }[] = [];
  try {
    await cdp.open(ws);
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
    await cdp.send('Page.addScriptToEvaluateOnNewDocument', { source: 'navigator.getGamepads = () => [];' });
    await cdp.send('Page.navigate', { url: `http://localhost:${port}/?track=${id}` });
    let ready = false;
    for (let k = 0; k < 240 && !ready; k++) { await sleep(500); ready = await cdp.eval<boolean>('!!(window.__sim && window.__sim.vehicle && window.__sim.track)').catch(() => false); }
    if (!ready) throw new Error(`the sim did not start on localhost:${port} (dev server running?)`);
    const gl = await cdp.eval<string>(`(() => { const g = window.__sim.renderer.getContext(); const d = g.getExtension('WEBGL_debug_renderer_info'); return d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : 'webgl'; })()`);
    console.log(`sim up on localhost:${port} (${gl}); track ${id}, ${L.toFixed(0)} m; camera ${camera}`);
    await cdp.eval(`(() => { navigator.getGamepads = () => []; window.__sim.setMode('hotlap'); window.__sim.setCamera(${JSON.stringify(camera)}); })()`);
    await sleep(1500);
    const shoot = async (s: number, yaw: number) => {
      const p = pose(s);
      await cdp.eval(`window.__sim.vehicle.reset(${JSON.stringify(p.pos)}, ${p.heading}, 0)`);
      await sleep(300);
      const url = await cdp.eval<string>(`(() => { const S = window.__sim, cam = S.cams.camera, q = cam.quaternion.clone();
        cam.rotateY(${yaw}); cam.updateMatrixWorld(true); S.renderer.render(S.world.scene, cam);
        const u = S.renderer.domElement.toDataURL('image/jpeg', 0.86); cam.quaternion.copy(q); cam.updateMatrixWorld(true); return u; })()`);
      return Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
    };
    const fwd: number[] = [];
    for (let s = 0; s < L; s += step) if (!only || (s >= only[0] && s <= only[1])) fwd.push(s);
    for (const s of fwd) {
      const f = `sim/fwd_s${String(Math.round(s)).padStart(4, '0')}.jpg`;
      writeFileSync(join(out, f), await shoot(s, 0));
      shots.push({ file: f, s, side: 'fwd' });
    }
    console.log(`${fwd.length} forward stills every ${step} m`);
    if (inv && !has('no-rows')) {
      const yaw = (yawDeg * Math.PI) / 180, seen = new Set<string>();
      let n = 0;
      for (const r of inv.rows as { s: number; side: string; kind: string; scope?: string }[]) {
        if ((r.scope ?? 'lap') !== 'lap' || (r.side !== 'left' && r.side !== 'right')) continue;
        if (only && (r.s < only[0] || r.s > only[1])) continue;
        const key = `${r.side}${Math.round(r.s / 10)}`;
        if (seen.has(key)) continue;
        seen.add(key);
        const f = `sim/row_s${String(Math.round(r.s)).padStart(4, '0')}_${r.side}.jpg`;
        writeFileSync(join(out, f), await shoot(r.s, r.side === 'left' ? yaw : -yaw));
        shots.push({ file: f, s: r.s, side: r.side as 'left' | 'right', kind: r.kind });
        n++;
      }
      console.log(`${n} side stills toward inventory rows (+-${yawDeg} deg)`);
    }
    writeFileSync(join(out, 'walk.json'), JSON.stringify({ track: id, step, camera, yaw_deg: yawDeg, size: [W, H], gl, port, shots }, null, 1));
    console.log(`wrote ${out}/walk.json and ${shots.length} stills`);
  } finally {
    cdp.close();
    proc.kill('SIGTERM');
    await sleep(500);
    try { rmSync(profile, { recursive: true, force: true }); } catch { /* left behind in tmp */ }
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
