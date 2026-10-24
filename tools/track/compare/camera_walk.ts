// Drive proxy (build-track stage 4): walk the sim's hood camera round the whole lap, toward every inventory row, and
// from the poses the owner takes when he drives (codify round, 20 Oct 2026), for the compare sheets
// (tools/track/compare/make_compare_sheets.py) that the orchestrator and the judge review before the owner drives.
// Replaces stills at builder-chosen spots.
//
//   npx tsx tools/track/compare/camera_walk.ts --track sonoma [--step 50] [--back-step 100] [--pit-step 25] [--port 5179]
//        [--camera hood] [--yaw 70] [--out tools/track/compare/<id>/compare_sheets] [--no-rows] [--no-runoff]
//        [--only s0,s1] [--replay <walk.json>]
//
// Needs the dev server on the port (npx vite --port 5179 --strictPort). Launches its own headless Chrome with a
// throwaway profile (never the owner's browser) and drives the page over the DevTools protocol, the same hooks as the
// hood stills of 20 Oct (window.__sim): hot-lap mode, navigator.getGamepads = () => [], the car placed at a pose with
// __sim.vehicle.reset([x, y, z], heading, 0), 300 ms to settle, then one render of the hood camera read back in the same
// task (preserveDrawingBuffer is off). Poses (every shot's pose is recorded in walk.json):
//   fwd     on the centre every --step m facing the driving direction            sim/fwd_s####.jpg
//   left/right  turned +-yaw toward the side of every inventory row (one per 10 m and side)  sim/row_s####_<side>.jpg
//   back    on the centre every --back-step m facing BACK along the lap (the owner's look over his shoulder: wall ends,
//           joins and facings show from the other direction)                     sim/back_s####.jpg
//   pit     inside the pit lane, end to end every --pit-step m along each lane part, facing the way the cars drive it
//                                                                                sim/pit_p#_###.jpg
//   runoff  from every paved polygon the track reaches before a barrier (the containment gate's rays, allowed runoff
//           and closed roads, one pose per 150 m of each run, from the polygon's far side looking back across its paving: 5 m beyond it, or 25 m into a polygon deeper than 30 m) and from every paved runoff zone,
//           looking back at the track                                          sim/runoff_##.jpg
// --replay <walk.json> shoots the poses of an earlier walk again (another package, same poses: compare_packages.py).
// Output: <out>/sim/*.jpg and <out>/walk.json. Local only (ignored by git).
import { spawn, type ChildProcess } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { pitPoses, runoffPoses, type Kind, type Shot } from './poses';

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
const backStep = Number(opt('back-step', '100'));
const pitStep = Number(opt('pit-step', '25'));
const replay = opt('replay');

const track = JSON.parse(readFileSync(join(ROOT, 'public/tracks', id, 'track.json'), 'utf8'));
const invPath = join(ROOT, 'tools/track/compare', id, 'inventory.json');
const inv = existsSync(invPath) ? JSON.parse(readFileSync(invPath, 'utf8')) : null;
const L: number = track.n * track.spacing_m;
const scenery = existsSync(join(ROOT, 'public/tracks', id, 'scenery.json')) ? JSON.parse(readFileSync(join(ROOT, 'public/tracks', id, 'scenery.json'), 'utf8')) : {};

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
    const shots: Shot[] = [];
    const shootPose = async (sh: Shot) => {
      const z = sh.pos[2] === null
        ? await cdp.eval<number>(`window.__sim.surface.sample(${sh.pos[0]}, ${sh.pos[1]}).z`)
        : sh.pos[2];
      await cdp.eval(`window.__sim.vehicle.reset(${JSON.stringify([sh.pos[0], sh.pos[1], z])}, ${sh.heading}, 0)`);
      await sleep(300);
      const url = await cdp.eval<string>(`(() => { const S = window.__sim, cam = S.cams.camera, q = cam.quaternion.clone();
        cam.rotateY(${sh.yaw}); cam.updateMatrixWorld(true); S.renderer.render(S.world.scene, cam);
        const u = S.renderer.domElement.toDataURL('image/jpeg', 0.86); cam.quaternion.copy(q); cam.updateMatrixWorld(true); return u; })()`);
      writeFileSync(join(out, sh.file), Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'));
      shots.push(sh);
    };
    const onCentre = (s: number, side: Kind, file: string, yaw = 0, back = false, kind?: string): Shot => {
      const p = pose(s);
      return { file, s, side, pos: p.pos, heading: back ? p.heading + Math.PI : p.heading, yaw, kind };
    };
    const inRange = (s: number) => !only || (s >= only[0] && s <= only[1]);
    let plan: Shot[] = [];
    if (replay) {
      plan = (JSON.parse(readFileSync(replay, 'utf8')).shots as Shot[]).filter((sh) => sh.pos && inRange(sh.s));
      console.log(`replaying ${plan.length} poses of ${replay}`);
    } else {
      for (let s = 0; s < L; s += step) if (inRange(s)) plan.push(onCentre(s, 'fwd', `sim/fwd_s${String(Math.round(s)).padStart(4, '0')}.jpg`));
      if (inv && !has('no-rows')) {
        const yaw = (yawDeg * Math.PI) / 180, seen = new Set<string>();
        for (const r of inv.rows as { s: number; side: string; kind: string; scope?: string }[]) {
          if ((r.scope ?? 'lap') !== 'lap' || (r.side !== 'left' && r.side !== 'right')) continue;
          if (!inRange(r.s)) continue;
          const key = `${r.side}${Math.round(r.s / 10)}`;
          if (seen.has(key)) continue;
          seen.add(key);
          plan.push(onCentre(r.s, r.side as Kind, `sim/row_s${String(Math.round(r.s)).padStart(4, '0')}_${r.side}.jpg`, r.side === 'left' ? yaw : -yaw, false, r.kind));
        }
      }
      if (backStep > 0) for (let s = 0; s < L; s += backStep) if (inRange(s)) plan.push(onCentre(s, 'back', `sim/back_s${String(Math.round(s)).padStart(4, '0')}.jpg`, 0, true));
      plan.push(...pitPoses(track, scenery, pitStep).filter((sh) => inRange(sh.s)));
      if (!has('no-runoff')) plan.push(...runoffPoses(track, scenery).filter((sh) => inRange(sh.s)));
    }
    for (const sh of plan) await shootPose(sh);
    const count: Record<string, number> = {};
    for (const sh of shots) count[sh.side] = (count[sh.side] ?? 0) + 1;
    console.log(`stills by pose: ${Object.entries(count).map(([k, v]) => `${k} ${v}`).join(', ')} (forward every ${step} m, rows +-${yawDeg} deg, back every ${backStep} m, pit lane every ${pitStep} m, runoff)`);
    writeFileSync(join(out, 'walk.json'), JSON.stringify({ track: id, step, back_step: backStep, pit_step: pitStep, camera, yaw_deg: yawDeg, size: [W, H], gl, port, replay: replay ?? null, shots }, null, 1));
    console.log(`wrote ${out}/walk.json and ${shots.length} stills`);
  } finally {
    cdp.close();
    proc.kill('SIGTERM');
    await sleep(500);
    try { rmSync(profile, { recursive: true, force: true }); } catch { /* left behind in tmp */ }
  }
}

main().catch((e) => { console.error(e); process.exit(1); });
