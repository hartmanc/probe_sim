// Pose walk (the buildings round, 21 Oct 2026): sim stills from arbitrary poses (the pit lane, the paddock, the track
// turned toward a structure) for the before / after / reference sheets of tools/track/compare/<id>/buildings_sheets/,
// plus the renderer's draw calls and triangles at each pose and a timing of repeated renders (the frame-rate check).
// Same headless-Chrome-over-CDP method as camera_walk.ts (throwaway profile, never the owner's browser).
//
//   npx tsx tools/track/compare/pose_walk.ts --track sonoma --poses poses.json --out <dir> [--port 5180] [--tag after]
//
// poses.json: [{name, x, y, z, heading (rad, ENU), yaw (deg, + = left), pitch (deg, + = up)}]; the car is placed at
// (x, y, z) facing heading (z null: the drivable surface's height there, sampled in the page), the hood camera turned by yaw / pitch; --hide a,b hides scene objects by name. Writes <out>/<name>_<tag>.jpg and <out>/stats_<tag>.json.
import { spawn, type ChildProcess } from 'node:child_process';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const argv = process.argv.slice(2);
const opt = (k: string, d?: string) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d; };
const id = opt('track');
const posesPath = opt('poses');
if (!id || !posesPath) { console.error('--track <id> --poses <json> required'); process.exit(2); }
const port = Number(opt('port', '5180'));
const tag = opt('tag', 'sim')!;
const out = resolve(opt('out', '.')!);
const chromeBin = opt('chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')!;
const W = Number(opt('width', '1280')), H = Number(opt('height', '720'));
const poses: { name: string; x: number; y: number; z: number | null; heading: number; yaw?: number; pitch?: number }[] = JSON.parse(readFileSync(posesPath, 'utf8'));

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
  mkdirSync(out, { recursive: true });
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
      await cdp.eval(`window.__sim.vehicle.reset(${JSON.stringify([p.x, p.y, z])}, ${p.heading}, 0)`);
      await sleep(300);
      const r = await cdp.eval<{ url: string; calls: number; triangles: number; ms: number }>(`(() => { const S = window.__sim, cam = S.cams.camera, q = cam.quaternion.clone();
        cam.rotateY(${((p.yaw ?? 0) * Math.PI) / 180}); cam.rotateX(${((p.pitch ?? 0) * Math.PI) / 180}); cam.updateMatrixWorld(true);
        S.renderer.info.autoReset = false; S.renderer.info.reset(); S.renderer.render(S.world.scene, cam);
        const calls = S.renderer.info.render.calls, triangles = S.renderer.info.render.triangles;
        const gl = S.renderer.getContext(); const px = new Uint8Array(4); const t0 = performance.now();
        for (let i = 0; i < 20; i++) { S.renderer.render(S.world.scene, cam); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, px); }
        const ms = (performance.now() - t0) / 20; S.renderer.render(S.world.scene, cam);
        const u = S.renderer.domElement.toDataURL('image/jpeg', 0.88); S.renderer.info.autoReset = true; cam.quaternion.copy(q); cam.updateMatrixWorld(true);
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
