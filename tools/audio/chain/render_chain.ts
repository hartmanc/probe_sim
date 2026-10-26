// Render engine sounds through the game's REAL audio chain: headless Chrome (throwaway profile, muted), an
// OfflineAudioContext, and src/app/audio-field.ts EngineVoice / src/app/audio.ts CarAudio bundled by esbuild.
//
//   npx tsx tools/audio/chain/render_chain.ts JOBS.json OUTDIR [--public DIR]
//     JOBS.json: [{name, family, engineUrl | null, fps, rpm[], thr[], gear?, boxRpm?, opts?, idle?, redline?, seed?}]
//     writes OUTDIR/<name>.f32 (48 kHz mono float32, raw chain output, un-normalised)
// One Chrome process; the profile is deleted on exit (as tools/track/compare/headless_capture.ts).
import { spawn } from 'node:child_process';
import { createServer } from 'node:http';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve, extname } from 'node:path';
import { build } from 'esbuild';

const argv = process.argv.slice(2);
const jobsFile = resolve(argv[0]);
const outDir = resolve(argv[1]);
const pi = argv.indexOf('--public');
const pub = resolve(pi >= 0 ? argv[pi + 1] : 'public');
const chromeBin = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

class CDP {
  private ws!: WebSocket; private id = 0; private wait = new Map<number, (m: any) => void>();
  logs: string[] = [];
  async open(url: string) {
    this.ws = new WebSocket(url);
    await new Promise<void>((res, rej) => { this.ws.onopen = () => res(); this.ws.onerror = (e) => rej(e); });
    this.ws.onmessage = (ev) => {
      const m = JSON.parse(String(ev.data));
      if (m.id && this.wait.has(m.id)) { this.wait.get(m.id)!(m); this.wait.delete(m.id); }
      else if (m.method === 'Runtime.consoleAPICalled') this.logs.push(m.params.args.map((a: any) => a.value ?? a.description).join(' '));
    };
  }
  send(method: string, params: Record<string, unknown> = {}, timeoutMs = 600000): Promise<any> {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((res, rej) => {
      const to = setTimeout(() => { this.wait.delete(id); rej(new Error(`${method}: no answer in ${timeoutMs} ms`)); }, timeoutMs);
      this.wait.set(id, (m) => { clearTimeout(to); if (m.error) rej(new Error(`${method}: ${m.error.message}`)); else res(m.result); });
    });
  }
  async eval<T = unknown>(expr: string): Promise<T> {
    const r = await this.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(`page: ${r.exceptionDetails.exception?.description ?? r.exceptionDetails.text}`);
    return r.result.value as T;
  }
  close() { try { this.ws.close(); } catch { /* closed */ } }
}

const MIME: Record<string, string> = { '.js': 'text/javascript', '.json': 'application/json', '.ogg': 'audio/ogg', '.m4a': 'audio/mp4', '.html': 'text/html' };

async function main() {
  mkdirSync(outDir, { recursive: true });
  const tmp = mkdtempSync(join(tmpdir(), 'render-chain-'));
  const r = await build({ entryPoints: [resolve('tools/audio/chain/entry.ts')], bundle: true, format: 'iife', write: false, target: 'es2022' });
  const bundle = r.outputFiles[0].text;
  const html = '<!doctype html><html><body><script src="/bundle.js"></script></body></html>';
  const server = createServer((req, res) => {
    const u = decodeURIComponent((req.url ?? '/').split('?')[0]);
    if (u === '/' || u === '/index.html') { res.writeHead(200, { 'content-type': 'text/html' }); res.end(html); return; }
    if (u === '/bundle.js') { res.writeHead(200, { 'content-type': 'text/javascript' }); res.end(bundle); return; }
    const f = join(pub, u);
    if (!f.startsWith(pub) || !existsSync(f) || !statSync(f).isFile()) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'content-type': MIME[extname(f)] ?? 'application/octet-stream' });
    res.end(readFileSync(f));
  });
  await new Promise<void>((res) => server.listen(0, '127.0.0.1', () => res()));
  const port = (server.address() as { port: number }).port;
  const profile = mkdtempSync(join(tmpdir(), 'render-chain-profile-'));
  const proc = spawn(chromeBin, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run',
    '--no-default-browser-check', '--disable-extensions', '--mute-audio', '--autoplay-policy=no-user-gesture-required', 'about:blank'], { stdio: 'ignore' });
  let ws = '';
  try {
    for (let k = 0; k < 100 && !ws; k++) {
      await sleep(150);
      try {
        const p = readFileSync(join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
        const list = await (await fetch(`http://127.0.0.1:${p}/json/list`)).json() as { type: string; webSocketDebuggerUrl: string }[];
        ws = list.find((t) => t.type === 'page')?.webSocketDebuggerUrl ?? '';
      } catch { /* not up */ }
    }
    if (!ws) throw new Error('Chrome did not open its DevTools port');
    const cdp = new CDP();
    await cdp.open(ws);
    await cdp.send('Runtime.enable');
    await cdp.send('Page.enable');
    await cdp.send('Page.navigate', { url: `http://127.0.0.1:${port}/` });
    for (let k = 0; k < 100; k++) { await sleep(100); if (await cdp.eval<boolean>('typeof window.renderEngine === "function"').catch(() => false)) break; }
    const jobs = JSON.parse(readFileSync(jobsFile, 'utf8')) as { name: string }[];
    for (const j of jobs) {
      const t0 = Date.now();
      const b = await cdp.eval<string>(`window.renderEngine(${JSON.stringify(j)})`);
      writeFileSync(join(outDir, `${j.name}.f32`), Buffer.from(b, 'base64'));
      console.log(`${j.name}: ${((Date.now() - t0) / 1000).toFixed(1)} s`);
    }
    if (cdp.logs.length) console.log('page log:\n  ' + cdp.logs.slice(0, 20).join('\n  '));
    cdp.close();
  } finally {
    proc.kill();
    server.close();
    await sleep(300);
    rmSync(profile, { recursive: true, force: true });
    rmSync(tmp, { recursive: true, force: true });
  }
}
main().catch((e) => { console.error(e); process.exit(1); });
