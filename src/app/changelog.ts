// What's new (main menu → What's new): the release history, newest first, and the version shown in the main menu.
//
// Versioning (19 Oct 2026): the app carries one MAJOR.MINOR.PATCH release number for people. MAJOR is a milestone
// (1.0 when the planned circuits are in and the physics has settled), MINOR adds content or features (a circuit,
// cars, race or scoreboard features), PATCH is look, sound, AI behaviour and fixes. Whether lap times stay
// comparable is NOT encoded in the number: that is per board, keyed by PHYSICS_VERSION (src/scoreboard/config.ts)
// and the circuit, and every entry that opened fresh boards says so in `resets`. APP_VERSION is the newest entry's
// version; package.json mirrors it. The build's git commit (vite `define`, __GIT_SHA__) is shown next to it so a
// preview can be told from another.
import type { MenuEntry, MenuPage } from './menu';
import { PHYSICS_VERSION } from '../scoreboard/config';

export interface ChangeEntry {
  /** MAJOR.MINOR.PATCH */
  version: string;
  /** ISO date, YYYY-MM-DD */
  date: string;
  /** a short name for the release */
  title: string;
  /** boards whose lap times stopped being comparable (a physics or geometry change), by circuit name */
  resets?: string[];
  /** what changed, for players */
  items: string[];
}

/** Newest first. Add a new entry at the top and mirror its version in package.json. */
export const CHANGELOG: ChangeEntry[] = [
  {
    version: '0.3.1', date: '2026-10-19', title: "What's new",
    items: [
      'This page, and the version shown in the main menu.',
    ],
  },
  {
    version: '0.3.0', date: '2026-10-19', title: 'Painted road', resets: ['Laguna Seca'],
    items: [
      'Laguna Seca’s edges re-fitted to the painted lines in satellite imagery, one smooth curve per side: the front straight is straight, and Rahal, Rainey, T6 and T11 are their real widths.',
      'Racing line re-solved on the new edges.',
      'AI drivers: grip capped at a realistic level, banking and crests in their corner speeds, a lane model for the narrower road, and they ease the lock when the front washes out instead of ploughing on at full lock.',
      'Every car’s pace recalibrated to its real lap times.',
    ],
  },
  {
    version: '0.2.0', date: '2026-10-18', title: 'Look pass', resets: ['Laguna Seca'],
    items: [
      'Physical sky and baked lighting, sun-tinted fog, clear-coat paint, a rubbered racing line, bloom, speed blur, tyre marks, dust and smoke.',
      'Sausage kerbs on every apex. They are part of the physics, so lap times reset.',
      'Scenery from the onboard and satellite comparison rounds: grandstands, bridges and ad boards, walls and tyre walls, paved runoff, oaks and verges.',
      'Race results ranked by race time; personal bests on the scoreboard.',
    ],
  },
  {
    version: '0.1.0', date: '2026-10-17', title: 'First release',
    items: [
      'Hot lap and a 10-lap race against 45 real Lemons cars at Laguna Seca.',
      '1993 Ford Probe GT #619, with the team’s logged laps as ghosts.',
      'Online scoreboard; controller, keyboard and phone controls.',
    ],
  },
];

export const APP_VERSION = CHANGELOG[0].version;

// ---------------------------------------------------------------- pure helpers (unit-tested)

const SEMVER = /^(\d+)\.(\d+)\.(\d+)$/;
const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

export function isSemver(v: string): boolean { return SEMVER.test(v); }

/** Negative when a < b, positive when a > b, 0 when equal (both must be MAJOR.MINOR.PATCH). */
export function compareSemver(a: string, b: string): number {
  const pa = a.split('.').map(Number), pb = b.split('.').map(Number);
  for (let i = 0; i < 3; i++) if (pa[i] !== pb[i]) return pa[i] - pb[i];
  return 0;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** '2026-10-19' → '19 Oct 2026' (no Date object: no time-zone drift). */
export function formatDate(iso: string): string {
  const m = ISO_DATE.exec(iso);
  if (!m) return iso;
  const month = MONTHS[Number(m[2]) - 1];
  return month ? `${Number(m[3])} ${month} ${m[1]}` : iso;
}

/** Problems with a change log (empty when it is well-formed): newest first, versions strictly falling, dates not rising. */
export function validateChangelog(entries: ChangeEntry[]): string[] {
  const out: string[] = [];
  if (!entries.length) out.push('no entries');
  entries.forEach((e, i) => {
    if (!isSemver(e.version)) out.push(`${e.version}: not MAJOR.MINOR.PATCH`);
    if (!ISO_DATE.test(e.date)) out.push(`${e.version}: date ${e.date} is not YYYY-MM-DD`);
    if (!e.title.trim()) out.push(`${e.version}: no title`);
    if (!e.items.length || e.items.some((s) => !s.trim())) out.push(`${e.version}: empty item`);
    if (e.resets && (!e.resets.length || e.resets.some((s) => !s.trim()))) out.push(`${e.version}: empty resets`);
    const prev = entries[i - 1];
    if (prev && isSemver(prev.version) && isSemver(e.version) && compareSemver(prev.version, e.version) <= 0) out.push(`${prev.version} is not newer than ${e.version}`);
    if (prev && prev.date < e.date) out.push(`${prev.version} is dated before ${e.version}`);
  });
  return out;
}

/** The version line for the main menu: 'v0.3.1 · 1ffcd93' (the commit only when the build knows it). */
export function versionLine(version: string, sha?: string): string {
  const s = (sha ?? '').trim();
  return s ? `v${version} · ${s.slice(0, 7)}` : `v${version}`;
}

// ---------------------------------------------------------------- the card

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

/** The change log as DOM (pure rendering of the entries). */
export function renderChangelog(entries: ChangeEntry[], box: HTMLElement, sha?: string): void {
  const parts: HTMLElement[] = [];
  for (const e of entries) {
    const s = el('section', 'cr-section');
    const h = el('h3', 'cr-h');
    h.append(el('span', 'cl-ver', `v${e.version}`), el('span', 'cl-date', formatDate(e.date)), el('span', 'cl-title', e.title));
    s.append(h);
    if (e.resets?.length) s.append(el('div', 'cl-reset', `Lap times reset: ${e.resets.join(', ')}`));
    const ul = el('ul', 'cl-items');
    for (const it of e.items) ul.append(el('li', undefined, it));
    s.append(ul);
    parts.push(s);
  }
  const foot = el('div', 'cr-intro cl-keys');
  foot.textContent = `Build ${versionLine(APP_VERSION, sha)} · scoreboard key ${PHYSICS_VERSION}`;
  parts.push(foot);
  box.replaceChildren(...parts);
}

let box: HTMLElement | null = null;

const scrollBox = (dir: 1 | -1) => { if (box) box.scrollBy({ top: dir * Math.max(80, box.clientHeight * 0.8), behavior: 'auto' }); };

/** Main menu → What's new. Static data, rendered once; the page keeps its scroll position across menu re-renders. */
export function changelogPage(sha?: string): MenuPage {
  if (!box) { box = el('div', 'credits changelog'); box.tabIndex = -1; renderChangelog(CHANGELOG, box, sha); }
  const b = box;
  b.scrollTop = 0;
  return {
    title: "What's new",
    subtitle: `Version ${APP_VERSION}`,
    body: () => { const top = b.scrollTop; queueMicrotask(() => { b.scrollTop = top; }); return b; },
    entries: (): MenuEntry[] => [
      { kind: 'action', id: 'clDown', label: 'Scroll down ▾', run: () => scrollBox(1) },
      { kind: 'action', id: 'clUp', label: 'Scroll up ▴', run: () => scrollBox(-1) },
      { kind: 'back', id: 'back', label: 'Back' },
    ],
  };
}
