// What's new (main menu → What's new): the release history, newest first, and the version shown in the main menu.
//
// Versioning (owner, 19 Oct 2026): one MAJOR.MINOR.PATCH number per PUBLISH, i.e. per merge to main that goes to
// lemons-sim.app; previews do not get numbers, so everything since the last publish rolls into the one entry at the
// top, which stays `date: ''` (unreleased) until it ships. MAJOR is a milestone (1.0 when the planned circuits are
// in and the physics has settled), MINOR adds content or features (a circuit, cars, race or scoreboard features),
// PATCH is look, sound, AI behaviour and fixes only. Whether lap times stay comparable is NOT encoded in the number:
// that is per board, keyed by PHYSICS_VERSION (src/scoreboard/config.ts) and the circuit, and every entry that
// opened fresh boards says so in `resets`. APP_VERSION is the top entry's version; package.json mirrors it. The
// build's git commit (vite `define`, __GIT_SHA__) is shown next to it so one preview can be told from another.
import type { MenuEntry, MenuPage } from './menu';
import { PHYSICS_VERSION } from '../scoreboard/config';

export interface ChangeEntry {
  /** MAJOR.MINOR.PATCH */
  version: string;
  /** ISO date YYYY-MM-DD of the publish; '' on the top entry while it is unreleased (in previews only) */
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
    version: '0.4.0', date: '', title: 'Ready for the paddock',
    items: [
      'Your scoreboard name is yours: the first device to post it claims it. To post as the same name on another device, get a transfer code in Scoreboard on this one and type it there. Times already on the boards stay.',
      'Race boards are off until the server can check a race the way it checks a hot lap. Hot-lap boards stay, every lap re-run on the server.',
      'Report a bug or ask for a feature from the Start menu: it files a public GitHub issue with the game version, the track and your device.',
      'Phones and tablets race the 40 cars whose real pace is closest to the Probe’s, so the race around you is the real one and the phone keeps up. Computers race the whole field.',
      'How to play, and a Credits page with the data, software, models and engine-sound sources, the privacy note and how a team can ask to be left out.',
      'A plain message when the browser cannot run WebGL 2, and a reload button when the graphics drop out.',
      'The team’s ghost laps are labelled driver A to D.',
    ],
  },
  {
    version: '0.3.0', date: '2026-10-25', title: 'Sonoma Raceway',
    items: [
      'Sonoma Raceway in its 24 Hours of Lemons layout: the road fitted to the painted lines in 2026 satellite imagery, the ground from USGS lidar, and the trackside built from the March 2026 onboard: walls at their real heights, catch fences, the deep tyre wall round the T11 hairpin, kerbs in their real colours, the pit lane with both walls, the hillside grandstands, the main grandstand and garages, marshal posts, the scoring tower, sponsor boards and painted logos. Unused roads are real pavement, coned off.',
      'A track pipeline that builds a circuit from public data and recent video, with gates for containment, pit-lane connectivity, wall ends and coverage of everything the onboard shows, so the next circuits start at this level.',
      'Race at Sonoma against the field of the March 2026 Sears Pointless race (133 cars and you), each car modelled from its photos, with the pace it ran there.',
      'AI drivers: at Sonoma their lane changes are capped by spare grip and a passing car keeps a margin; on every track a driver no longer commits to a pass where the road takes the lane away at the apex, and tucks back in instead. Laguna’s lap pace is unchanged.',
      'Sonoma’s kerbs are 5 cm raised concrete; a kerb traversal check keeps every kerb on every track from lifting a wheel at racing speed.',
      'Per-track scoreboards: a rebuilt circuit opens its own boards without resetting the others.',
      'Tyre walls are solid now, like the concrete ones, and rolling the car ends the run: “You are banned from Lemons for one year for rolling your hooptie”.',
      'Drive far off the track, into the hills, and you are launched into space like a hard wall hit: “You got lost in the hills, so the tow truck sent you home the fast way.”',
    ],
  },
  {
    version: '0.2.0', date: '2026-10-19', title: 'Painted road', resets: ['Laguna Seca'],
    items: [
      'Laguna Seca’s edges re-fitted to the painted lines in satellite imagery, one smooth curve per side: the front straight is straight, and Rahal, Rainey, T6 and T11 are their real widths. Racing line re-solved on them.',
      'Sausage kerbs on every apex. They and the edges are part of the physics, so lap times reset.',
      'Physical sky and baked lighting, sun-tinted fog, clear-coat paint, a rubbered racing line, bloom, speed blur, tyre marks, dust and smoke.',
      'Scenery from the onboard and satellite comparison rounds: grandstands, bridges and ad boards, walls and tyre walls, paved runoff, oaks and verges.',
      'AI drivers: grip capped at a realistic level, banking and crests in their corner speeds, a lane model for the narrower road, and they ease the lock when the front washes out instead of ploughing on at full lock. Every car’s pace recalibrated to its real lap times.',
      'Race results ranked by race time; personal bests on the scoreboard.',
      'This What’s new page, and the version shown in the main menu.',
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

/** '2026-10-19' → '19 Oct 2026' (no Date object: no time-zone drift); '' → 'unreleased'. */
export function formatDate(iso: string): string {
  if (iso === '') return 'unreleased';
  const m = ISO_DATE.exec(iso);
  if (!m) return iso;
  const month = MONTHS[Number(m[2]) - 1];
  return month ? `${Number(m[3])} ${month} ${m[1]}` : iso;
}

/** Problems with a change log (empty when it is well-formed): newest first, versions strictly falling, dates not rising,
 *  at most the top entry unreleased. */
export function validateChangelog(entries: ChangeEntry[]): string[] {
  const out: string[] = [];
  if (!entries.length) out.push('no entries');
  entries.forEach((e, i) => {
    if (!isSemver(e.version)) out.push(`${e.version}: not MAJOR.MINOR.PATCH`);
    if (e.date === '' ? i !== 0 : !ISO_DATE.test(e.date)) out.push(`${e.version}: date ${JSON.stringify(e.date)} is not YYYY-MM-DD${i === 0 ? '' : ' (only the top entry may be unreleased)'}`);
    if (!e.title.trim()) out.push(`${e.version}: no title`);
    if (!e.items.length || e.items.some((s) => !s.trim())) out.push(`${e.version}: empty item`);
    if (e.resets && (!e.resets.length || e.resets.some((s) => !s.trim()))) out.push(`${e.version}: empty resets`);
    const prev = entries[i - 1];
    if (prev && isSemver(prev.version) && isSemver(e.version) && compareSemver(prev.version, e.version) <= 0) out.push(`${prev.version} is not newer than ${e.version}`);
    if (prev && prev.date !== '' && prev.date < e.date) out.push(`${prev.version} is dated before ${e.version}`);
  });
  return out;
}

/** The version line for the main menu: 'v0.2.0 · 1ffcd93', 'v0.2.0 preview · 1ffcd93' while that release is unreleased
 *  (the commit only when the build knows it). */
export function versionLine(version: string, sha?: string, released = true): string {
  const s = (sha ?? '').trim();
  const v = released ? `v${version}` : `v${version} preview`;
  return s ? `${v} · ${s.slice(0, 7)}` : v;
}

/** True when the top entry has shipped (has a date). */
export const APP_RELEASED = CHANGELOG[0].date !== '';

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
  foot.textContent = `Build ${versionLine(APP_VERSION, sha, APP_RELEASED)} · scoreboard key ${PHYSICS_VERSION}`;
  parts.push(foot);
  box.replaceChildren(...parts);
}

let box: HTMLElement | null = null;


/** Main menu → What's new. Static data, rendered once; the page keeps its scroll position across menu re-renders.
 *  The box scrolls by wheel / touch, and by up / down on the Back row (Menu.scrollBody). */
export function changelogPage(sha?: string): MenuPage {
  if (!box) { box = el('div', 'credits changelog'); box.tabIndex = -1; renderChangelog(CHANGELOG, box, sha); }
  const b = box;
  b.scrollTop = 0;
  return {
    title: "What's new",
    subtitle: APP_RELEASED ? `Version ${APP_VERSION}` : `Version ${APP_VERSION}, in preview`,
    body: () => { const top = b.scrollTop; queueMicrotask(() => { b.scrollTop = top; }); return b; },
    entries: (): MenuEntry[] => [{ kind: 'back', id: 'back', label: 'Back' }],
  };
}
