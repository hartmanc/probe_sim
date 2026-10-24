// Pose walk (the buildings round, 21 Oct 2026): sim stills from arbitrary poses (the pit lane, the paddock, the track
// turned toward a structure) for the before / after / reference sheets of tools/track/compare/<id>/buildings_sheets/,
// plus the renderer's draw calls and triangles at each pose and a timing of repeated renders (the frame-rate check).
// Same headless-Chrome-over-CDP method as camera_walk.ts (throwaway profile, never the owner's browser).
//
//   npx tsx tools/track/compare/pose_walk.ts --track <id> --poses <poses.json> --out <dir> --port <dev server port> \
//       [--tag sim] [--hide a,b] [--width 1280] [--height 720] [--chrome <Chrome binary>]
//
// Flags (round 11, 23 Oct 2026: the walk wrote into the current directory and looked for the dev server on 5180 when
// a brief named another port and folder; both are now given explicitly):
//   --track   the package id: the page opens http://localhost:<port>/?track=<id> (public/tracks/<id>/)
//   --poses   poses.json: [{name, x, y, z, heading (rad, ENU), yaw (deg, + = left), pitch (deg, + = up), eye (m above
//             the surface, optional: the camera then stands 4 m ahead of the car, clear of its body), camera ('hood' |
//             'chase', optional)}]; the car is placed
//             at (x, y, z) facing heading (z null: the drivable surface's height there, sampled in the page), the hood
//             camera turned by yaw / pitch
//   --out     REQUIRED: the folder the stills go to (<out>/<name>_<tag>.jpg) with stats_<tag>.json; created if missing
//   --port    REQUIRED: the port of the dev server already running from the worktree whose package is to be shot
//             (npx vite --port <port> --strictPort); the walk checks it answers before launching Chrome
//   --tag     the stills' suffix (default 'sim'), e.g. before / after
//   --camera  'hood' (default) or 'chase' for the whole walk (round 14A); a pose's own camera wins
//   --hide    hide the named scene objects (diagnosis: which mesh draws what)
//   --width / --height  the render size (default 1280 x 720); --chrome the Chrome binary (default the macOS app)
import { spawn, type ChildProcess } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const argv = process.argv.slice(2);
const opt = (k: string, d?: string) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d; };
const id = opt('track');
const posesPath = opt('poses');
if (!id || !posesPath) { console.error('--track <id> --poses <json> required'); process.exit(2); }
const portArg = opt('port'), outArg = opt('out');
if (!portArg || !outArg) { console.error('--port <dev server port> and --out <dir> are required (see the header)'); process.exit(2); }
const port = Number(portArg);
if (!Number.isInteger(port) || port <= 0) { console.error(`--port ${portArg}: not a port number`); process.exit(2); }
const tag = opt('tag', 'sim')!;
const out = resolve(outArg);
const chromeBin = opt('chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')!;
const W = Number(opt('width', '1280')), H = Number(opt('height', '720'));
// camera (round 14A): 'hood' (default) or 'chase' (the hot lap's start camera) for the whole walk (--camera) or per pose
const poses: { name: string; x: number; y: number; z: number | null; heading: number; yaw?: number; pitch?: number; eye?: number; camera?: string }[] = JSON.parse(readFileSync(posesPath, 'utf8'));
const cameraDefault = opt('camera', 'hood')!;

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
  const profile = mkdtempSync(join(tmpdir(), 'pose-walk-'));
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
  // the dev server must answer on the given port before Chrome is launched (no silent walk against another server)
  try { const r = await fetch(`http://localhost:${port}/`); if (!r.ok) throw new Error(`HTTP ${r.status}`); }
  catch (e) { throw new Error(`no dev server on localhost:${port} (${(e as Error).message}); start it with npx vite --port ${port} --strictPort`); }
  mkdirSync(out, { recursive: true });
  console.log(`pose walk: ${poses.length} poses of ${id} from localhost:${port} into ${out} (tag ${tag})`);
  const { proc, ws, profile } = await launch();
  const cdp = new CDP();
  const stats: Record<string, unknown>[] = [];
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
    await cdp.eval(`(() => { window.__sim.setMode('hotlap'); window.__sim.setCamera('hood'); })()`);
    await sleep(1500);
    const scene = await cdp.eval<Record<string, number>>(`(() => { let tris = 0, meshes = 0; window.__sim.world.scene.traverse((o) => {
      if (o.isMesh && o.geometry) { meshes++; const g = o.geometry; const n = g.index ? g.index.count / 3 : g.attributes.position.count / 3; tris += n * (o.isInstancedMesh ? o.count : 1); } });
      const st = window.__sim.world.scene.getObjectByName('structures'); let stTris = 0, stMeshes = 0;
      if (st) st.traverse((o) => { if (o.isMesh) { stMeshes++; stTris += o.geometry.attributes.position.count / 3; } });
      return { sceneMeshes: meshes, sceneTriangles: Math.round(tris), structureMeshes: stMeshes, structureTriangles: stTris }; })()`);
    console.log('scene', JSON.stringify(scene));
    // --hide name,name: hide the named scene objects (diagnosis: which mesh draws what)
    const hide = opt('hide', '');
    if (hide) console.log('hidden', await cdp.eval<number>(`(() => { let n = 0; for (const nm of ${JSON.stringify(hide.split(','))}) window.__sim.world.scene.traverse((o) => { if (o.name === nm) { o.visible = false; n++; } }); return n; })()`));
    for (const p of poses) {
      const z = p.z === null || p.z === undefined ? await cdp.eval<number>(`window.__sim.surface.sample(${p.x}, ${p.y}).z`) : p.z;
      const cam = p.camera ?? cameraDefault;
      await cdp.eval(`window.__sim.setCamera(${JSON.stringify(cam)})`);
      await cdp.eval(`window.__sim.vehicle.reset(${JSON.stringify([p.x, p.y, z])}, ${p.heading}, 0)`);
      await sleep(cam === 'hood' ? 300 : 2500);   // the chase camera eases in behind the car
      // eye (texture pass, 21 Oct 2026): the camera this many m above the surface at the pose (world y is up), else the hood
      const eye = p.eye === undefined ? 'null' : String(p.eye);
      const r = await cdp.eval<{ url: string; calls: number; triangles: number; ms: number }>(`(() => { const S = window.__sim, cam = S.cams.camera, q = cam.quaternion.clone(), p0 = cam.position.clone();
        if (${eye} !== null) { cam.position.y = ${z} + ${eye}; cam.position.x += 4 * Math.cos(${p.heading}); cam.position.z -= 4 * Math.sin(${p.heading}); }   // 4 m ahead of the car: clear of the body
        cam.rotateY(${((p.yaw ?? 0) * Math.PI) / 180}); cam.rotateX(${((p.pitch ?? 0) * Math.PI) / 180}); cam.updateMatrixWorld(true);
        S.renderer.info.autoReset = false; S.renderer.info.reset(); S.renderer.render(S.world.scene, cam);
        const calls = S.renderer.info.render.calls, triangles = S.renderer.info.render.triangles;
        const gl = S.renderer.getContext(); const px = new Uint8Array(4); const t0 = performance.now();
        for (let i = 0; i < 20; i++) { S.renderer.render(S.world.scene, cam); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); }
        const ms = (performance.now() - t0) / 20; S.renderer.render(S.world.scene, cam);
        const u = S.renderer.domElement.toDataURL('image/jpeg', 0.88); S.renderer.info.autoReset = true; cam.quaternion.copy(q); cam.position.copy(p0); cam.updateMatrixWorld(true);
        return { url: u, calls, triangles, ms }; })()`);
      writeFileSync(join(out, `${p.name}_${tag}.jpg`), Buffer.from(r.url.slice(r.url.indexOf(',') + 1), 'base64'));
      stats.push({ pose: p.name, calls: r.calls, triangles: r.triangles, ms_per_render: Math.round(r.ms * 100) / 100 });
      console.log(`${p.name}: ${r.calls} draw calls, ${r.triangles} triangles, ${r.ms.toFixed(2)} ms per render`);
    }
    writeFileSync(join(out, `stats_${tag}.json`), JSON.stringify({ track: id, tag, size: [W, H], scene, poses: stats }, null, 1));
  } finally {
    cdp.close();
    proc.kill('SIGTERM');
    await sleep(500);
    try { rmSync(profile, { recursive: true, force: true }); } catch { /* left behind in tmp */ }
  }
}

void main().catch((e) => { console.error(e); process.exit(1); });
