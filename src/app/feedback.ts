// Start menu → "Report a bug / request a feature" (owner's decision, 26 Oct 2026): the player types a description and
// picks bug / feature; the game adds the version, the build's commit, the track, the device class, the browser, the
// screen and the last captured error, and POSTs it to /api/feedback, which files a public GitHub issue (src/feedback).
// No email field. The scoreboard name registered on this device goes with it (the server checks the device secret).
import type { MenuEntry, MenuPage } from './menu';
import { lastError } from './errors';

export interface FeedbackPayload {
  kind: 'bug' | 'feature';
  description: string;
  context: { version: string; sha: string; track: string; device: string; ua: string; screen: string; error?: string };
  name?: string;
  secret?: string;
}

export const MAX_DESCRIPTION = 2000;

/** Pure: the request body. */
export function buildFeedback(a: {
  kind: 'bug' | 'feature'; description: string; version: string; sha: string; track: string; device: string;
  ua: string; screen: string; error: string | null; name: string | null; secret: string | undefined;
}): FeedbackPayload {
  return {
    kind: a.kind,
    description: a.description.trim().slice(0, MAX_DESCRIPTION),
    context: { version: a.version, sha: a.sha, track: a.track, device: a.device, ua: a.ua.slice(0, 300), screen: a.screen, ...(a.error ? { error: a.error } : {}) },
    ...(a.name && a.secret ? { name: a.name, secret: a.secret } : {}),
  };
}

export interface FeedbackPageOptions {
  version: string;
  sha: string;
  track: string;
  device: string;
  name(): string | null;
  secret(): string | undefined;
  toast(msg: string, ms?: number): void;
  refresh(): void;
  fetch?: (url: string, init: RequestInit) => Promise<Response>;
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

let box: HTMLElement | null = null;
let area: HTMLTextAreaElement | null = null;
let count: HTMLElement | null = null;

export function feedbackPage(o: FeedbackPageOptions): MenuPage {
  let kind: 'bug' | 'feature' = 'bug';
  let state: 'idle' | 'sending' | 'sent' = 'idle';
  if (!box) {
    box = el('div', 'feedback');
    area = el('textarea', 'fb-text');
    area.maxLength = MAX_DESCRIPTION;
    area.rows = 5;
    area.placeholder = 'What happened, where on the track, what you expected. Or the feature you would like.';
    area.setAttribute('aria-label', 'Description');
    count = el('div', 'fb-count');
    // typing belongs to the text box: keep keys from input.ts (W A S D, Esc, Enter = menu verbs); Esc leaves the box
    area.addEventListener('keydown', (e) => { e.stopPropagation(); if (e.key === 'Escape') area!.blur(); });
    area.addEventListener('keyup', (e) => e.stopPropagation());
    area.addEventListener('input', () => { count!.textContent = `${area!.value.length} / ${MAX_DESCRIPTION}`; });
    box.append(area, count, el('div', 'fb-note', 'The report and your scoreboard name are public on GitHub. Please do not include personal details.'));
  }
  const b = box, a = area!, cnt = count!;
  cnt.textContent = `${a.value.length} / ${MAX_DESCRIPTION}`;
  const send = () => {
    if (state === 'sending') return;
    const text = a.value.trim();
    if (!text) { o.toast('Type a description first'); a.focus(); return; }
    state = 'sending'; o.refresh();
    const body = buildFeedback({
      kind, description: text, version: o.version, sha: o.sha, track: o.track, device: o.device,
      ua: navigator.userAgent, screen: `${screen.width}x${screen.height}@${window.devicePixelRatio || 1} (${innerWidth}x${innerHeight})`,
      error: lastError(), name: o.name(), secret: o.secret(),
    });
    (o.fetch ?? ((u, i) => fetch(u, i)))('/api/feedback', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      .then(async (r) => {
        const j = (await r.json().catch(() => null)) as { ok?: boolean; number?: number; reasons?: string[]; error?: string } | null;
        if (r.ok && j?.ok) { state = 'sent'; a.value = ''; cnt.textContent = `0 / ${MAX_DESCRIPTION}`; o.toast(`Thanks! Filed as issue #${j.number ?? '?'} on GitHub`, 6000); }
        else { state = 'idle'; o.toast(`Could not send the report: ${j?.reasons?.[0] ?? j?.error ?? `HTTP ${r.status}`}`, 6000); }
      })
      .catch(() => { state = 'idle'; o.toast('Could not send the report: offline?', 6000); })
      .finally(() => o.refresh());
  };
  return {
    title: 'Report a bug / request a feature',
    subtitle: `Files a public GitHub issue · v${o.version}${o.sha ? ` · ${o.sha}` : ''} · ${o.name() ? `as ${o.name()}` : 'anonymous'}`,
    body: () => b,
    entries: (): MenuEntry[] => [
      { kind: 'choice', id: 'fbKind', label: 'Type', options: [{ value: 'bug', label: 'Bug' }, { value: 'feature', label: 'Feature' }], get: () => kind, set: (v) => { kind = v as 'bug' | 'feature'; } },
      { kind: 'action', id: 'fbSend', label: state === 'sent' ? 'Sent · send another' : 'Send', note: state === 'sending' ? 'sending…' : undefined, disabled: state === 'sending', run: () => { if (state === 'sent') state = 'idle'; send(); } },
      { kind: 'back', id: 'back', label: 'Back' },
    ],
  };
}
