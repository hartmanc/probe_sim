// Reference captures in a headless Chrome with a throwaway profile (build-track stage 0.3 / 0.4 / 0.6 / 4.2): no tab of
// the owner's Chrome is touched, the video is muted and paused before every frame, and the profile is deleted on exit.
// Frames and captures are REFERENCE ONLY: never textures, never committed (they land under ignored folders).
//
//   # onboard frames: one JPEG per time (seconds into the video), drawn from the paused <video> into a full-window canvas
//   npx tsx tools/track/compare/headless_capture.ts yt --id <video id> --times 0:150:2 --out <dir> [--pattern t{t}.jpg]
//       --times a:b:step | t1,t2,...    --pattern  {t} = whole seconds zero-padded to 3, {ms} = milliseconds (for 0.5 s)
//   # clean Google satellite captures at z20 (labels off, UI hidden by page CSS, panned by dragging, centre from the URL)
//   npx tsx tools/track/compare/headless_capture.ts maps --points <points.json> --out <dir> [--zoom 20]
//       points.json: [{name, lat, lon}, ...]; writes <name>_google.jpg (1440 x 725) and tiles.json {name, lat, lon, mpp}
//
// Chrome: /Applications/Google Chrome.app (proprietary codecs for YouTube). One process at a time.
import { spawn, type ChildProcess } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';

const argv = process.argv.slice(2);
const mode = argv[0];
const opt = (k: string, d?: string) => { const i = argv.indexOf(`--${k}`); return i >= 0 ? argv[i + 1] : d; };
const chromeBin = opt('chrome', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')!;
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

class CDP {
  private ws!: WebSocket; private id = 0; private wait = new Map<number, (m: any) => void>();
  async open(url: string) {
    this.ws = new WebSocket(url);
    await new Promise<void>((res, rej) => { this.ws.onopen = () => res(); this.ws.onerror = (e) => rej(e); });
    this.ws.onmessage = (ev) => { const m = JSON.parse(String(ev.data)); if (m.id && this.wait.has(m.id)) { this.wait.get(m.id)!(m); this.wait.delete(m.id); } };
  }
  send(method: string, params: Record<string, unknown> = {}, timeoutMs = 60000): Promise<any> {
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

async function launch(W: number, H: number): Promise<{ proc: ChildProcess; ws: string; profile: string }> {
  const profile = mkdtempSync(join(tmpdir(), 'headless-capture-'));
  // port 0: Chrome picks a free port and writes it to <profile>/DevToolsActivePort, so two captures never share a browser
  const proc = spawn(chromeBin, [
    '--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, `--window-size=${W},${H}`,
    '--no-first-run', '--no-default-browser-check', '--disable-extensions', '--mute-audio', '--autoplay-policy=no-user-gesture-required',
    '--ignore-gpu-blocklist', '--enable-webgl', '--use-angle=metal', '--lang=en-US', 'about:blank',
  ], { stdio: 'ignore' });
  for (let k = 0; k < 100; k++) {
    await sleep(150);
    try {
      const port = readFileSync(join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0].trim();
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json() as { type: string; webSocketDebuggerUrl: string }[];
      const page = list.find((t) => t.type === 'page');
      if (page) return { proc, ws: page.webSocketDebuggerUrl, profile };
    } catch { /* not up yet */ }
  }
  proc.kill();
  throw new Error('Chrome did not open its DevTools port');
}

async function shot(cdp: CDP, file: string, quality = 90, clip?: { x: number; y: number; width: number; height: number }) {
  const r = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality, ...(clip ? { clip: { ...clip, scale: 1 } } : {}) });
  writeFileSync(file, Buffer.from(r.data, 'base64'));
}

function parseTimes(s: string): number[] {
  if (s.includes(':')) { const [a, b, st] = s.split(':').map(Number); const o: number[] = []; for (let t = a; t <= b + 1e-9; t += st) o.push(+t.toFixed(3)); return o; }
  return s.split(',').map(Number);
}

async function yt() {
  const id = opt('id'); const out = resolve(opt('out')!); const times = parseTimes(opt('times', '0:10:2')!);
  const pattern = opt('pattern', 't{t}.jpg')!;
  const W = Number(opt('width', '1280')), H = Number(opt('height', '720'));
  if (!id || !/^[A-Za-z0-9_-]{11}$/.test(id)) throw new Error('--id <11-character video id> required');
  mkdirSync(out, { recursive: true });
  const { proc, ws, profile } = await launch(W, H);
  const cdp = new CDP();
  try {
    await cdp.open(ws);
    await cdp.send('Page.enable'); await cdp.send('Runtime.enable');
    await cdp.send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
    await cdp.send('Page.navigate', { url: `https://www.youtube.com/watch?v=${id}` });
    let ok = false;
    for (let k = 0; k < 80 && !ok; k++) { await sleep(500); ok = await cdp.eval<boolean>(`!!document.querySelector('video') && document.querySelector('video').readyState >= 1`).catch(() => false); }
    if (!ok) { await shot(cdp, join(out, '_page.jpg')); throw new Error('no playable <video> (consent page or player blocked; see _page.jpg)'); }
    // past any pre-roll ad: the main video has a finite duration and the player is not .ad-showing
    for (let k = 0; k < 120; k++) {
      const st = await cdp.eval<any>(`(() => { const v = document.querySelector('video'); const p = document.getElementById('movie_player');
        if (v) v.muted = true; const skip = document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern'); if (skip) skip.click();
        return { ad: !!(p && p.classList.contains('ad-showing')), d: v ? v.duration : 0 }; })()`);
      if (!st.ad && Number.isFinite(st.d) && st.d > 0) break;
      if (k % 10 === 0) await cdp.eval(`(() => { const p = document.getElementById('movie_player'); const v = document.querySelector('video'); try { p.mute(); p.playVideo(); } catch (e) {} v && v.play().catch(() => {}); })()`);
      await sleep(500);
    }
    // ask for the best rendition and play muted for a few seconds so the player switches to it
    await cdp.eval(`(async () => { const p = document.getElementById('movie_player'); const v = document.querySelector('video'); v.muted = true;
      try { const q = p.getAvailableQualityLevels(); const best = q.includes('hd720') ? 'hd720' : q[0]; p.setPlaybackQualityRange(best, best); p.setPlaybackQuality && p.setPlaybackQuality(best); } catch (e) {}
      if (Number.isFinite(v.duration)) v.currentTime = Math.min(${times[0] ?? 0} + 1, v.duration - 1); await Promise.race([v.play().catch(() => {}), new Promise((r) => setTimeout(r, 3000))]);
      for (let k = 0; k < 40; k++) { await new Promise((r) => setTimeout(r, 500)); const w = document.querySelector('video');
        if (w && Number.isFinite(w.duration) && w.duration > 0 && w.readyState >= 2 && w.videoWidth >= 1280 && k >= 4) break; }
      document.querySelector('video').pause(); })()`);
    const info = await cdp.eval<any>(`(async () => {
      const v = document.querySelector('video'); v.muted = true; v.pause();
      const p = document.getElementById('movie_player');
      try { p.mute(); p.setPlaybackQualityRange('hd1080', 'hd1080'); p.setPlaybackQuality && p.setPlaybackQuality('hd1080'); } catch (e) {}
      const r = (p && p.getVideoData) ? p.getVideoData() : {};
      return { title: r.title || document.title, author: r.author || '', duration: (p && p.getDuration ? p.getDuration() : 0) || v.duration,
               date: (document.querySelector('meta[itemprop=uploadDate]') || {}).content || (document.querySelector('meta[itemprop=datePublished]') || {}).content || '' };
    })()`);
    console.log(`video ${id}: ${info.title} | ${info.author} | ${info.date} | ${Math.round(info.duration)} s`);
    // full-window canvas the paused frame is drawn into (the player UI never shows in the capture)
    await cdp.eval(`(() => { const c = document.createElement('canvas'); c.id = '__cap'; c.width = ${W}; c.height = ${H};
      Object.assign(c.style, { position: 'fixed', left: 0, top: 0, width: '${W}px', height: '${H}px', zIndex: 2147483647, background: '#000' });
      document.body.appendChild(c); })()`);
    const meta: any[] = [];
    for (const t of times) {
      if (t > info.duration) break;
      // seek the paused <video> and wait for the NEW frame to be presented (requestVideoFrameCallback), then draw it
      const grab = () => cdp.eval<any>(`(async () => {
        const p = document.getElementById('movie_player'); const sl = (ms) => new Promise((r) => setTimeout(r, ms));
        for (let k = 0; k < 120 && p.classList.contains('ad-showing'); k++) { const b = document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button, .ytp-ad-skip-button-modern'); if (b) b.click(); await sl(500); }
        let v = document.querySelector('video'); v.muted = true; v.pause();
        // low rendition after a reload: ask for 720p and play muted until the player has switched up
        for (let k = 0; k < 2 && v.videoWidth < 1280; k++) {
          try { const q = p.getAvailableQualityLevels(); const best = q.includes('hd720') ? 'hd720' : q[0]; p.setPlaybackQualityRange(best, best); } catch (e) {}
          v.currentTime = Math.max(0, ${t} - 3); await Promise.race([v.play().catch(() => {}), sl(3000)]);
          for (let j = 0; j < 16 && v.videoWidth < 1280; j++) await sl(250);
          v.pause(); v = document.querySelector('video');
        }
        const shown = new Promise((r) => { v.requestVideoFrameCallback((now, md) => r(md.mediaTime)); setTimeout(() => r(-1), 10000); });
        v.currentTime = ${t};
        const mt = await shown;
        await sl(150); v.pause();
        const c = document.getElementById('__cap'), g = c.getContext('2d');
        const s = Math.min(c.width / v.videoWidth, c.height / v.videoHeight), w = v.videoWidth * s, h = v.videoHeight * s;
        g.fillStyle = '#000'; g.fillRect(0, 0, c.width, c.height); g.drawImage(v, (c.width - w) / 2, (c.height - h) / 2, w, h);
        return { t: v.currentTime, media_t: mt, vw: v.videoWidth, vh: v.videoHeight, rs: v.readyState, paused: v.paused };
      })()`);
      let res: any;
      try { res = await grab(); } catch (e) { console.log(`t ${t}: ${(e as Error).message}; retrying`); res = await grab(); }
      const name = pattern.replace('{t}', String(Math.floor(t)).padStart(3, '0')).replace('{ms}', String(Math.round(t * 1000)).padStart(6, '0'));
      await shot(cdp, join(out, name));
      if (statSync(join(out, name)).size < 15000) {   // a black frame: the player errored ("Something went wrong"); reload it
        console.log(`t ${t}: black frame, reloading the player`);
        await cdp.send('Page.navigate', { url: `https://www.youtube.com/watch?v=${id}&t=${Math.floor(t)}s` });
        for (let k = 0; k < 80; k++) { await sleep(500); if (await cdp.eval<boolean>(`(() => { const v = document.querySelector('video'); const p = document.getElementById('movie_player');
          return !!(v && p && p.getDuration && p.getDuration() > 0 && !p.classList.contains('ad-showing')); })()`).catch(() => false)) break; }
        await cdp.eval(`(() => { const p = document.getElementById('movie_player'); p.mute(); p.pauseVideo(); const c = document.createElement('canvas'); c.id = '__cap'; c.width = ${W}; c.height = ${H};
          Object.assign(c.style, { position: 'fixed', left: 0, top: 0, width: '${W}px', height: '${H}px', zIndex: 2147483647, background: '#000' }); document.body.appendChild(c); })()`);
        res = await grab(); await shot(cdp, join(out, name));
        if (statSync(join(out, name)).size < 15000) {
          const why = await cdp.eval<any>(`(() => { const p = document.getElementById('movie_player'); const v = document.querySelector('video');
            return { state: p.getPlayerState(), cls: p.className.split(' ').filter((c) => /ad|ended|error|unstarted|paused|buffering/.test(c)).join(' '),
              err: (document.querySelector('.ytp-error-content-wrap-reason') || {}).textContent || '', src: (v.src || '').slice(0, 20), nvid: document.querySelectorAll('video').length,
              overlay: [...document.querySelectorAll('tp-yt-paper-dialog, yt-confirm-dialog-renderer, .ytp-autonav-endscreen-countdown-overlay')].map((e) => (e.textContent || '').trim().slice(0, 80)) }; })()`);
          console.log(`t ${t}: still black (rs ${res.rs}, ${res.vw}x${res.vh}) ${JSON.stringify(why)}`); res.black = true;
          await cdp.eval(`document.getElementById('__cap').style.display = 'none'`); await shot(cdp, join(out, `_page_${name}`)); await cdp.eval(`document.getElementById('__cap').style.display = ''`);
        }
      }
      meta.push({ file: name, t, ...res });
    }
    writeFileSync(join(out, `_frames_${id}.json`), JSON.stringify({ id, url: `https://www.youtube.com/watch?v=${id}`, ...info, frames: meta }, null, 1));
    const q = meta.length ? `${meta[0].vw}x${meta[0].vh}` : '-';
    console.log(`wrote ${meta.length} frames to ${out} (source ${q}); video paused and muted`);
  } finally {
    await cdp.eval(`(() => { const v = document.querySelector('video'); if (v) { v.pause(); v.muted = true; } })()`).catch(() => {});
    cdp.close(); proc.kill('SIGTERM'); await sleep(500);
    try { rmSync(profile, { recursive: true, force: true }); } catch { /* tmp */ }
  }
}

// Google Maps clean satellite captures: hide the UI by page CSS, labels off by the Layers menu, pan by dragging.
async function maps() {
  const pts = JSON.parse(readFileSync(resolve(opt('points')!), 'utf8')) as { name: string; lat: number; lon: number }[];
  const out = resolve(opt('out')!); const zoom = Number(opt('zoom', '20'));
  const W = 1440, H = 725;
  mkdirSync(out, { recursive: true });
  const idxPath = join(out, 'tiles.json');
  const index: any[] = existsSync(idxPath) ? JSON.parse(readFileSync(idxPath, 'utf8')) : [];
  const { proc, ws, profile } = await launch(W, H);
  const cdp = new CDP();
  const urlCentre = async () => {
    const u = await cdp.eval<string>('location.href');
    const m = u.match(/@(-?\d+\.\d+),(-?\d+\.\d+),([\d.]+)(z|m)/);
    if (!m) throw new Error(`no centre in ${u}`);
    return { lat: +m[1], lon: +m[2], z: m[4] === 'z' ? +m[3] : NaN, url: u };
  };
  try {
    await cdp.open(ws);
    await cdp.send('Page.enable'); await cdp.send('Runtime.enable');
    await cdp.send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
    const p0 = pts[0];
    await cdp.send('Page.navigate', { url: `https://www.google.com/maps/@${p0.lat},${p0.lon},${zoom}z/data=!3m1!1e3?hl=en` });
    await sleep(6000);
    // labels off: Layers > More > Labels (the toggle is a checkbox in the layer menu)
    const lab = await cdp.eval<string>(`(async () => {
      const q = (s) => Array.from(document.querySelectorAll(s));
      const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
      const layers = q('button, div[role=button]').find((b) => /Layers/i.test(b.getAttribute('aria-label') || b.textContent || ''));
      if (layers) { layers.dispatchEvent(new MouseEvent('mouseover', { bubbles: true })); await sleep(800); }
      let more = q('button, div[role=button], li').find((b) => /^More$/i.test((b.textContent || '').trim()) || /More/i.test(b.getAttribute('aria-label') || ''));
      if (more) { more.click(); await sleep(1500); }
      const cb = q('input[type=checkbox], button[role=checkbox], [role=menuitemcheckbox], [role=checkbox]').find((b) => /Labels/i.test((b.getAttribute('aria-label') || '') + (b.closest('label, li, div') || {}).textContent));
      if (!cb) return 'no labels toggle (layers ' + !!layers + ', more ' + !!more + ')';
      const on = cb.checked ?? (cb.getAttribute('aria-checked') === 'true');
      if (on) { cb.click(); await sleep(1200); }
      const close = q('button').find((b) => /Close/i.test(b.getAttribute('aria-label') || ''));
      if (close) close.click();
      await sleep(800);
      return 'labels ' + (on ? 'turned off' : 'already off');
    })()`);
    console.log(lab);
    // hide every UI element: only the map canvas stays visible (visibility can be re-enabled below a hidden ancestor)
    await cdp.eval(`(() => { const st = document.createElement('style'); st.id = '__clean';
      st.textContent = 'body * { visibility: hidden !important; } canvas { visibility: visible !important; }';
      document.head.appendChild(st); })()`);
    // park the cursor in the bottom-right corner
    await cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: W - 2, y: H - 2 });
    await sleep(2500);
    const mpp0 = 156543.03392 / 2 ** zoom;
    for (const p of pts) {
      if (!argv.includes('--redo') && existsSync(join(out, `${p.name}_google.jpg`)) && index.some((t) => t.name === p.name)) continue;
      // pan by dragging from the current centre to p
      for (let it = 0; it < 6; it++) {
        const c = await urlCentre();
        const mpp = mpp0 * Math.cos((c.lat * Math.PI) / 180);
        const dx = ((p.lon - c.lon) * Math.PI / 180) * 6378137 * Math.cos((c.lat * Math.PI) / 180) / mpp;
        const dy = ((p.lat - c.lat) * Math.PI / 180) * 6378137 / mpp;
        if (Math.hypot(dx, dy) < 3) break;
        const steps = Math.max(10, Math.ceil(Math.min(500, Math.hypot(dx, dy)) / 8));
        // drag in chunks of at most ~500 px so the grab stays inside the window
        let rx = -dx, ry = dy;
        while (Math.hypot(rx, ry) > 0.5) {
          const k = Math.min(1, 500 / Math.hypot(rx, ry)); const mx = rx * k, my = ry * k;
          const x0 = W / 2 - mx / 2, y0 = H / 2 - my / 2;
          await cdp.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: x0, y: y0, button: 'left', clickCount: 1 });
          for (let s = 1; s <= steps; s++) { await cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: x0 + (mx * s) / steps, y: y0 + (my * s) / steps, button: 'left', buttons: 1 }); await sleep(16); }
          await sleep(400);   // hold still before releasing: no fling
          await cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: x0 + mx, y: y0 + my, button: 'left', clickCount: 1 });
          await sleep(250);
          rx -= mx; ry -= my;
        }
        await cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: W - 2, y: H - 2 });
        await sleep(1200);
      }
      await sleep(3500);   // tiles settle
      const c = await urlCentre();
      if (Math.abs(c.z - zoom) > 0.01) throw new Error(`zoom changed to ${c.z} (${c.url})`);
      await shot(cdp, join(out, `${p.name}_google.jpg`), 92);
      const mpp = +(mpp0 * Math.cos((c.lat * Math.PI) / 180)).toFixed(5);
      const e = { name: p.name, lat: c.lat, lon: c.lon, mpp };
      const k = index.findIndex((t) => t.name === p.name); if (k >= 0) index[k] = { ...index[k], ...e }; else index.push(e);
      writeFileSync(idxPath, JSON.stringify(index, null, 0).replace(/},{/g, '},\n{'));
      console.log(`${p.name}: centre ${c.lat}, ${c.lon} (asked ${p.lat}, ${p.lon})`);
    }
  } finally {
    cdp.close(); proc.kill('SIGTERM'); await sleep(500);
    try { rmSync(profile, { recursive: true, force: true }); } catch { /* tmp */ }
  }
}

// Street View coverage check: Maps at a zoom, the pegman pressed (the blue coverage overlay shows where panoramas and
// photo spheres exist), one screenshot. Reference only.
async function svcover() {
  const lat = Number(opt('lat')), lon = Number(opt('lon')), zoom = Number(opt('zoom', '16')); const out = resolve(opt('out')!);
  const W = 1440, H = 900;
  const { proc, ws, profile } = await launch(W, H);
  const cdp = new CDP();
  try {
    await cdp.open(ws); await cdp.send('Page.enable'); await cdp.send('Runtime.enable');
    await cdp.send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
    await cdp.send('Page.navigate', { url: `https://www.google.com/maps/@${lat},${lon},${zoom}z/data=!3m1!1e3?hl=en` });
    await sleep(7000);
    const r = await cdp.eval<any>(`(() => { const b = [...document.querySelectorAll('button, div[role=button]')].find((e) => /Street View|pegman/i.test((e.getAttribute('aria-label') || '') + (e.className || '')));
      if (!b) return null; const q = b.getBoundingClientRect(); return { x: q.x + q.width / 2, y: q.y + q.height / 2, label: b.getAttribute('aria-label') }; })()`);
    console.log('pegman', JSON.stringify(r));
    if (r) {
      await cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: r.x, y: r.y });
      await cdp.send('Input.dispatchMouseEvent', { type: 'mousePressed', x: r.x, y: r.y, button: 'left', clickCount: 1 });
      for (let k = 1; k <= 10; k++) { await cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: r.x - k * 20, y: r.y - k * 20, button: 'left', buttons: 1 }); await sleep(60); }
      await sleep(3500);
    }
    await shot(cdp, out, 90);
    // --drop x,y: release the pegman there (window pixels), then record the panorama URL and shoot the given headings
    const drop = opt('drop');
    if (r && drop) {
      const [dx, dy] = drop.split(',').map(Number);
      for (let k = 1; k <= 15; k++) { await cdp.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: r.x + (dx - r.x) * k / 15, y: r.y + (dy - r.y) * k / 15, button: 'left', buttons: 1 }); await sleep(60); }
      await sleep(1500);
      await cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: dx, y: dy, button: 'left', clickCount: 1 });
      await sleep(7000);
      const u = await cdp.eval<string>('location.href'); console.log('panorama url', u);
      const base = u.replace(/,(\d+(\.\d+)?)h,/, ',HDGh,');
      for (const h of (opt('headings', '0,90,180,270')!).split(',')) {
        await cdp.send('Page.navigate', { url: base.replace('HDG', h).replace(/,(\d+(\.\d+)?)t\//, ',90t/') }); await sleep(6000);
        await cdp.eval(`(() => { const st = document.createElement('style'); st.textContent = 'body * { visibility: hidden !important; } canvas { visibility: visible !important; }'; document.head.appendChild(st); })()`);
        await sleep(500); await shot(cdp, out.replace(/\.jpg$/, `_h${h}.jpg`), 88);
        console.log('heading', h, await cdp.eval<string>('location.href'));
      }
      const meta = await cdp.eval<string>(`(document.body.innerText.match(/(Image capture|Street View)[^\n]{0,40}|[A-Z][a-z]{2} 20\d\d/g) || []).slice(0, 6).join(' | ')`).catch(() => '');
      console.log('captions', meta);
    } else if (r) await cdp.send('Input.dispatchMouseEvent', { type: 'mouseReleased', x: W - 5, y: 5, button: 'left', clickCount: 1 }).catch(() => {});
  } finally {
    cdp.close(); proc.kill('SIGTERM'); await sleep(500);
    try { rmSync(profile, { recursive: true, force: true }); } catch { /* tmp */ }
  }
}

(mode === 'yt' ? yt() : mode === 'maps' ? maps() : mode === 'svcover' ? svcover() : Promise.reject(new Error('mode: yt | maps | svcover'))).catch((e) => { console.error(e.message ?? e); process.exit(1); });
