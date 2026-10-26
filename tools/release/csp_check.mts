// Release check (0.4.0): headless Chrome (throwaway profile, deleted on exit) against a local `vite preview`, which serves
// vercel.json's production headers. `csp` collects every `securitypolicyviolation` event (enforced or report-only) and
// every console / page error while it opens each Start-menu page, drives a 20 s hot lap and races to the results card
// (use ?laps=1), then writes the log to <out dir>. `og` renders the link-preview still (public/og.jpg was made with
// OG_WAIT=16000 OG_CAM=chase on ?track=sonoma&seed=7). One Chrome at a time (docs/scoreboard.md §5.1).
//   npx tsx tools/release/csp_check.mts <url> csp|og <out dir>
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [url, mode, out] = process.argv.slice(2);
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const W = mode === 'og' ? 1200 : 1280, H = mode === 'og' ? 630 : 720;

class CDP {
  ws!: WebSocket; id = 0; wait = new Map<number, (m: any) => void>(); events: any[] = [];
  async open(u: string) {
    this.ws = new WebSocket(u);
    await new Promise<void>((res, rej) => { this.ws.onopen = () => res(); this.ws.onerror = (e) => rej(e); });
    this.ws.onmessage = (ev) => { const m = JSON.parse(String(ev.data)); if (m.id && this.wait.has(m.id)) { this.wait.get(m.id)!(m); this.wait.delete(m.id); } else if (m.method) this.events.push(m); };
  }
  send(method: string, params: Record<string, unknown> = {}, t = 60000): Promise<any> {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((res, rej) => {
      const to = setTimeout(() => { this.wait.delete(id); rej(new Error(`${method} timeout`)); }, t);
      this.wait.set(id, (m) => { clearTimeout(to); m.error ? rej(new Error(`${method}: ${m.error.message}`)) : res(m.result); });
    });
  }
  async eval<T = unknown>(expr: string): Promise<T> {
    const r = await this.send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
    if (r.exceptionDetails) throw new Error(`page: ${r.exceptionDetails.exception?.description ?? r.exceptionDetails.text}`);
    return r.result.value as T;
  }
}

const profile = mkdtempSync(join(tmpdir(), 'rel040-chrome-'));
const proc = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, `--window-size=${W},${H}`, '--no-first-run',
  '--no-default-browser-check', '--disable-extensions', '--mute-audio', '--autoplay-policy=no-user-gesture-required',
  '--ignore-gpu-blocklist', '--enable-webgl', '--use-angle=metal', '--lang=en-US', 'about:blank',
], { stdio: 'ignore' });
const log: string[] = [];
const say = (s: string) => { log.push(s); console.log(s); };
try {
  let ws = '';
  for (let k = 0; k < 100 && !ws; k++) {
    await sleep(150);
    try {
      const port = readFileSync(join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json() as any[];
      ws = list.find((t) => t.type === 'page')?.webSocketDebuggerUrl ?? '';
    } catch { /* not yet */ }
  }
  const c = new CDP();
  await c.open(ws);
  await c.send('Page.enable'); await c.send('Runtime.enable'); await c.send('Log.enable');
  await c.send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  await c.send('Page.addScriptToEvaluateOnNewDocument', { source: `window.__csp = []; document.addEventListener('securitypolicyviolation', (e) => window.__csp.push({ dir: e.violatedDirective, blocked: e.blockedURI, src: e.sourceFile, line: e.lineNumber, disp: e.disposition }));` });
  await c.send('Page.navigate', { url });
  const t0 = Date.now();
  for (;;) {
    await sleep(1000);
    const ok = await c.eval<boolean>(`!!(window.__sim)`).catch(() => false);
    if (ok) break;
    if (Date.now() - t0 > 180000) throw new Error('no __sim after 180 s');
  }
  say(`loaded in ${((Date.now() - t0) / 1000).toFixed(1)} s; headers check: ${await c.eval(`fetch(location.href).then(r => [(r.headers.get('content-security-policy') ? 'csp-enforced' : r.headers.get('content-security-policy-report-only') ? 'csp-ro' : 'NO CSP'), r.headers.get('x-frame-options'), r.headers.get('referrer-policy'), r.headers.get('permissions-policy')].join(' | '))`)}`);
  const click = (id: string) => c.eval(`(() => { const b = document.querySelector('.menu-row[data-id="${id}"]'); if (!b) return false; b.click(); return true; })()`);
  await sleep(1500);
  say(`race row: ${await c.eval(`document.querySelector('.menu-row[data-id="race"]')?.textContent`)}`);
  if (mode === 'csp') {
    // every Start-menu page
    for (const id of ['howto', 'credits', 'scoreboard', 'whatsnew', 'feedback']) {
      say(`open ${id}: ${await click(id)}`); await sleep(id === 'credits' ? 4000 : 1500);
      await c.eval(`document.querySelector('.menu-row[data-id="back"]')?.click()`); await sleep(500);
    }
    // hot lap 20 s, then the race with the whole field for a few minutes (models, field audio, marks)
    say(`hotlap: ${await click('hotlap')}`); await sleep(20000);
    await c.eval(`window.__sim.setMode('race')`);
    for (let k = 0; k < 60; k++) {
      await sleep(10000);
      const res = await c.eval<string>(`document.querySelector('.menu:not(.hidden) .menu-title')?.textContent ?? ''`);
      if (res === 'RESULTS') { say(`results card after ${(k + 1) * 10} s: ${await c.eval(`document.querySelector('.menu:not(.hidden) .menu-sub')?.textContent`)}; rows: ${await c.eval(`[...document.querySelectorAll('.menu:not(.hidden) .menu-row')].map(r => r.dataset.id).join(',')`)}`); break; }
      const st = await c.eval<string>(`(() => { const m = window.__sim.mode; const d = m && m.director; const fc = m && m.fieldCars; return d ? 'phase ' + d.hud().phase + ' lap ' + d.hud().lap + ' cars ' + d.cars.length + ' models ' + (fc ? d.cars.filter(x => !x.isPlayer && fc.kindOf(x.number) === 'model').length : 0) + ' audio ' + !!m.fieldAudio : 'no director'; })()`);
      say(`t+${(k + 1) * 10}s ${st}`);
    }
  } else if (mode === 'og') {
    await c.eval(`window.__sim.setMode('race')`);
    await sleep(Number(process.env.OG_WAIT ?? 45000));
    await c.eval(`(() => { document.querySelectorAll('.hud, .race-hud, .toast, .menu, .touch').forEach(e => e.style.visibility = 'hidden'); for (const el of document.querySelectorAll('#app > *:not(canvas)')) el.style.visibility = 'hidden'; })()`);
    if (process.env.OG_CAM) await c.eval(`window.__sim.setCamera(${JSON.stringify(process.env.OG_CAM)})`);
    await sleep(1500);
    const shot = await c.send('Page.captureScreenshot', { format: 'jpeg', quality: 86, clip: { x: 0, y: 0, width: W, height: H, scale: 1 } });
    writeFileSync(join(out, `og_${Date.now()}.jpg`), Buffer.from(shot.data, 'base64'));
  }
  const csp = await c.eval<unknown[]>(`window.__csp`);
  say(`CSP violations (securitypolicyviolation events, enforced or report-only): ${JSON.stringify(csp)}`);
  const errs = c.events.filter((e) => (e.method === 'Runtime.exceptionThrown') || (e.method === 'Log.entryAdded' && e.params.entry.level === 'error') || (e.method === 'Runtime.consoleAPICalled' && e.params.type === 'error'));
  say(`console / page errors: ${errs.length}`);
  for (const e of errs.slice(0, 20)) say('  ' + JSON.stringify(e.params).slice(0, 300));
  writeFileSync(join(out, `${mode}_${new URL(url).searchParams.get('track') ?? 'default'}${new URL(url).searchParams.get('phone') === '1' ? '_phone' : ''}_${new Date().toISOString().slice(0, 16).replace(':', '') + 'Z'}.txt`), [`url ${url}`, `date ${new Date().toISOString()}`, ...log].join('\n') + '\n');
} finally {
  proc.kill('SIGTERM');
  await sleep(500);
  rmSync(profile, { recursive: true, force: true });
}
