// Scoreboard UI: the new-best prompt (a pause-style menu card), the name editor (keyboard typing, a letter
// grid for the pad's d-pad / stick, tappable on phones) and the arcade top-10 screen opened from the main
// and pause menus. Network calls go through scoreboard-client.ts; nothing here blocks driving.
import type { Menu, MenuEntry, MenuPage, NavEvent } from './menu';
import {
  boardContext, hotlapBoard, raceBoard, fmtScore, fmtLapTime, postCandidate,
  type ApiResult, type Candidate, type ScoreboardClient, type SubmitOutcome,
} from './scoreboard-client';
import { LIMITS, nameKey, normalizeName, type Board, type Mode, type Score } from '../scoreboard';

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

// ---------------------------------------------------------------- name editor

type Cell = { label: string; kind: 'char' | 'space' | 'del' | 'cancel' | 'done'; ch?: string };

const GRID: Cell[][] = [
  ...['ABCDEFGHIJ', 'KLMNOPQRST', 'UVWXYZ-._!', '0123456789'].map((r) => [...r].map((ch): Cell => ({ label: ch, kind: 'char', ch }))),
  [{ label: 'Space', kind: 'space' }, { label: 'Del', kind: 'del' }, { label: 'Cancel', kind: 'cancel' }, { label: 'Done', kind: 'done' }],
];

/** Pure grid cursor (unit-tested): left/right wrap in a row, up/down keep the relative column. */
export function moveGridCursor(rows: number[], r: number, c: number, ev: 'up' | 'down' | 'left' | 'right'): [number, number] {
  const n = rows.length;
  if (ev === 'left' || ev === 'right') return [r, (c + (ev === 'left' ? -1 : 1) + rows[r]) % rows[r]];
  const r2 = (r + (ev === 'up' ? -1 : 1) + n) % n;
  const c2 = rows[r] <= 1 ? 0 : Math.round((c / (rows[r] - 1)) * (rows[r2] - 1));
  return [r2, Math.min(rows[r2] - 1, c2)];
}

const cps = (s: string) => [...s];

/** What a keydown does while the scoreboard owns the screen (pure; unit-tested). */
export type KeyRoute = 'pass' | 'skip' | 'open-editor' | 'type' | 'delete' | 'cancel' | 'commit';

/**
 * Keyboard routing, independent of which device drove the lap. While the new-best prompt is up, a printable key
 * opens the name editor with that character (it must never reach input.ts, where O / Esc mean "close menu" and
 * W A S D mean "move"), Esc skips; arrows / Enter / Space still navigate the card. In the editor every key goes
 * to the name (focused text field: native typing; otherwise typed here), Esc cancels, Enter saves.
 */
export function routeScoreboardKey(
  s: { promptOpen: boolean; editorOpen: boolean; fieldFocused: boolean },
  e: { key: string; ctrlKey?: boolean; metaKey?: boolean; altKey?: boolean; repeat?: boolean },
): KeyRoute {
  if (e.ctrlKey || e.metaKey || e.altKey) return 'pass';
  const printable = [...e.key].length === 1;
  if (s.editorOpen) {
    if (s.fieldFocused) return 'pass'; // the field handles it (its own Enter / Esc handler)
    if (e.key === 'Escape') return 'cancel';
    if (e.key === 'Enter') return 'commit';
    if (e.key === 'Backspace') return 'delete';
    return printable ? 'type' : 'pass';
  }
  if (s.promptOpen) {
    if (e.key === 'Escape') return e.repeat ? 'pass' : 'skip';
    if (printable && e.key !== ' ') return 'open-editor';
  }
  return 'pass';
}

export const EDITOR_SETTLE_MS = 400;

/** Pad B in the name grid: delete, or cancel on an empty name only when it is a fresh, deliberate press. */
export function editorBack(now: number, openedAt: number, lastDeleteAt: number, empty: boolean): 'ignore' | 'delete' | 'cancel' {
  if (now - openedAt < EDITOR_SETTLE_MS) return 'ignore'; // a press that was in flight when the editor opened
  if (!empty) return 'delete';
  return now - lastDeleteAt < EDITOR_SETTLE_MS ? 'ignore' : 'cancel'; // mashing B to clear must not also cancel
}

export class NameEditor {
  readonly root = el('div', 'sb-editor hidden');
  private field = el('input', 'sb-name-field');
  private msg = el('div', 'sb-name-msg');
  private grid = el('div', 'sb-grid');
  private hint = el('div', 'menu-footer');
  private cells: HTMLButtonElement[][] = [];
  private r = 0;
  private c = 0;
  private done: ((name: string | null) => void) | null = null;
  private openedAt = 0;
  private lastDeleteAt = 0;

  constructor(parent: HTMLElement, private touch: () => boolean, private hints: () => { select: string; back: string; menu: string; pad: boolean }) {
    const card = el('div', 'sb-card');
    card.append(el('h2', 'sb-title', 'ENTER YOUR NAME'), this.field, this.msg, this.grid, this.hint);
    this.root.append(card);
    this.root.addEventListener('click', (e) => { if (e.target === this.root) this.finish(null); });
    this.field.type = 'text';
    this.field.maxLength = LIMITS.nameMax * 2; // code points are capped below
    this.field.autocomplete = 'off';
    this.field.spellcheck = false;
    this.field.setAttribute('aria-label', `Name (up to ${LIMITS.nameMax} characters)`);
    this.field.addEventListener('input', () => this.cap());
    this.field.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault(); this.commit(); }
      else if (e.key === 'Escape') { e.preventDefault(); this.finish(null); }
      e.stopPropagation();
    });
    GRID.forEach((row, ri) => {
      const rowEl = el('div', 'sb-grid-row' + (row.length < 6 ? ' wide' : ''));
      this.cells.push(row.map((cell, ci) => {
        const b = el('button', 'sb-key', cell.label);
        b.type = 'button';
        b.dataset.kind = cell.kind;
        b.addEventListener('click', () => { this.r = ri; this.c = ci; this.press(cell); this.paint(); this.refocus(); });
        rowEl.append(b);
        return b;
      }));
      this.grid.append(rowEl);
    });
    parent.appendChild(this.root);
  }

  get isOpen(): boolean { return !this.root.classList.contains('hidden'); }
  get fieldFocused(): boolean { return document.activeElement === this.field; }

  /** A keydown routed here by ScoreboardUI (field not focused): type into the field and give it the focus. */
  key(r: KeyRoute, ch: string): void {
    if (r === 'cancel') { this.finish(null); return; }
    if (r === 'commit') { this.commit(); return; }
    if (r === 'delete') this.press({ label: '', kind: 'del' });
    else if (r === 'type') this.press(ch === ' ' ? { label: '', kind: 'space' } : { label: ch, kind: 'char', ch });
    this.field.focus({ preventScroll: true });
    this.paint();
  }

  open(initial: string | null, done: (name: string | null) => void): void {
    this.done = done;
    this.openedAt = performance.now();
    this.lastDeleteAt = 0;
    this.field.value = initial ?? '';
    this.msg.textContent = '';
    this.r = 0; this.c = 0;
    this.root.classList.remove('hidden');
    this.paint();
    this.refocus();
  }

  private refocus(): void {
    // keyboard typing goes into the field; on a phone the grid is the keyboard (no OS keyboard popping up)
    if (!this.touch()) this.field.focus({ preventScroll: true });
  }

  private cap(): void {
    const v = cps(this.field.value);
    if (v.length > LIMITS.nameMax) this.field.value = v.slice(0, LIMITS.nameMax).join('');
    this.msg.textContent = '';
  }

  private press(cell: Cell): void {
    const v = this.field.value;
    switch (cell.kind) {
      case 'char': case 'space':
        if (cps(v).length >= LIMITS.nameMax) { this.msg.textContent = `${LIMITS.nameMax} characters max`; return; }
        this.field.value = v + (cell.kind === 'space' ? ' ' : cell.ch!);
        this.msg.textContent = '';
        return;
      case 'del': this.field.value = cps(v).slice(0, -1).join(''); return;
      case 'cancel': this.finish(null); return;
      case 'done': this.commit(); return;
    }
  }

  private commit(): void {
    const n = normalizeName(this.field.value);
    if (!n) { this.msg.textContent = `1–${LIMITS.nameMax} letters, digits or symbols`; return; }
    this.finish(n);
  }

  private finish(name: string | null): void {
    if (!this.isOpen) return;
    this.root.classList.add('hidden');
    this.field.blur();
    const d = this.done; this.done = null;
    d?.(name);
  }

  /** Pad / arrow-key navigation (index.ts routes NavEvents here while open): A types, B deletes, Start is done. */
  nav(ev: NavEvent): void {
    if (!this.isOpen) return;
    const now = performance.now();
    if (now - this.openedAt < EDITOR_SETTLE_MS / 2 && (ev === 'select' || ev === 'menu')) return; // the press that opened it
    if (ev === 'select') this.press(GRID[this.r][this.c]);
    else if (ev === 'back') {
      const b = editorBack(now, this.openedAt, this.lastDeleteAt, !this.field.value);
      if (b === 'delete') { this.press({ label: '', kind: 'del' }); this.lastDeleteAt = now; }
      else if (b === 'cancel') this.finish(null);
    }
    else if (ev === 'menu') this.commit();
    else [this.r, this.c] = moveGridCursor(GRID.map((r) => r.length), this.r, this.c, ev);
    this.paint();
  }

  private paint(): void {
    this.cells.forEach((row, ri) => row.forEach((b, ci) => b.classList.toggle('active', ri === this.r && ci === this.c)));
    const h = this.hints();
    // the text field and the grid are always both there: keyboard typing works whichever device drove the lap
    this.hint.textContent = this.touch() ? 'Tap letters · Done to save'
      : `Type · Enter saves · Esc cancels${h.pad ? ` · grid: ${h.select} letter · ${h.back} delete · ${h.menu} done` : ''}`;
  }
}

// ---------------------------------------------------------------- the board screen + the prompt

interface BoardState { status: 'loading' | 'ok' | 'offline' | 'error'; board?: Board; error?: string }

const ORD = (n: number) => `${n}${n % 100 >= 11 && n % 100 <= 13 ? 'TH' : ['TH', 'ST', 'ND', 'RD'][n % 10] ?? 'TH'}`;
const MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC'];
function fmtDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? '' : `${String(d.getDate()).padStart(2, '0')} ${MONTHS[d.getMonth()]}`;
}
const INPUT_LABEL: Record<string, string> = { pad: 'PAD', keys: 'KEYS', phone: 'PHONE' };

export interface ScoreboardUIOptions {
  app: HTMLElement;
  menu: Menu;
  client: ScoreboardClient;
  toast(msg: string, ms?: number): void;
  touch(): boolean;
  hints(): { select: string; back: string; menu: string; pad: boolean };
  trackLength(): number;
  /** The scene needs a redraw (menu changes while paused). */
  onChange?(): void;
}

export class ScoreboardUI {
  readonly editor: NameEditor;
  private mode: Mode = 'hotlap';
  private states = new Map<string, BoardState>();
  private page: MenuPage;

  constructor(private o: ScoreboardUIOptions) {
    this.editor = new NameEditor(o.app, o.touch, o.hints);
    // capture phase: runs before input.ts's window listener, which would read letters as menu verbs / moves
    window.addEventListener('keydown', (e) => this.onKey(e), { capture: true });
    this.page = {
      title: 'HIGH SCORES',
      subtitle: '',
      body: () => this.renderBoard(),
      entries: (): MenuEntry[] => {
        const race = raceBoard();
        if (!race) this.mode = 'hotlap';
        return [
          ...(race ? [{
            kind: 'choice', id: 'sbBoard', label: 'Board',
            options: [{ value: 'hotlap', label: 'Hot lap' }, { value: 'race', label: 'Race' }],
            get: () => this.mode, set: (v: string) => { this.mode = v as Mode; this.load(); },
          } as MenuEntry] : []),
          { kind: 'action', id: 'sbRefresh', label: 'Refresh', run: () => this.load() },
          { kind: 'action', id: 'sbName', label: 'Name', note: o.client.name ?? 'not set', run: () => this.editName(() => this.load()) },
          { kind: 'back', id: 'back', label: 'Back' },
        ];
      },
    };
  }

  /** The Scoreboard submenu page (main + pause menus); fetches the board on open. */
  open(): MenuPage {
    this.load();
    return this.page;
  }

  get editorOpen(): boolean { return this.editor.isOpen; }
  /** The new-best prompt is on screen (index.ts then ignores Start / Esc-as-'menu': only Submit / Skip close it). */
  get promptOpen(): boolean { return !!this.promptPage && this.o.menu.isOpen && this.o.menu.state?.page === this.promptPage; }

  private onKey(e: KeyboardEvent): void {
    const r = routeScoreboardKey({ promptOpen: this.promptOpen, editorOpen: this.editor.isOpen, fieldFocused: this.editor.fieldFocused }, e);
    if (r === 'pass') return;
    e.preventDefault();
    e.stopImmediatePropagation();
    if (r === 'skip') this.promptDecide?.({ status: 'skipped' });
    else if (r === 'open-editor') {
      // a new name typed from scratch; the prompt stays open behind the editor
      this.editName(() => this.o.menu.refresh(), '');
      this.editor.key('type', e.key);
    } else this.editor.key(r, e.key);
  }

  /** Pause-menu row: offer the last best lap again if its prompt was skipped or the POST failed. */
  pauseEntries(): MenuEntry[] {
    const c = this.lastCandidate;
    if (!c) return [];
    return [{ kind: 'action', id: 'sbSubmitLast', label: 'Submit last lap', note: `${c.detail} · ${fmtScore(c.mode, c.score, undefined, 0)}`, run: () => { void this.offer(c); } }];
  }

  /** Open the name editor; `then` runs after a name was saved. */
  editName(then?: () => void, initial: string | null = this.o.client.name): void {
    this.editor.open(initial, (n) => {
      if (n) { this.o.client.setName(n); this.o.toast(`Name: ${n}`); then?.(); }
      this.o.menu.refresh();
      this.o.onChange?.();
    });
  }

  private key(): string | null { return this.mode === 'race' ? raceBoard() : hotlapBoard(); }

  private load(): void {
    const key = this.key();
    if (!key) { this.o.menu.refresh(); return; }
    const prev = this.states.get(key);
    this.states.set(key, { ...prev, status: 'loading' });
    this.o.menu.refresh();
    void this.o.client.board(key).then((r: ApiResult<Board>) => {
      this.states.set(key, r.ok ? { status: 'ok', board: r.value }
        : r.offline ? { status: 'offline', board: prev?.board } : { status: 'error', error: r.reasons.join('; ') || r.error });
      if (this.o.menu.state?.page === this.page) this.o.menu.refresh();
    });
  }

  private renderBoard(): HTMLElement {
    const box = el('div', 'sb-board');
    const key = this.key();
    const mode = this.mode;
    const ctx = boardContext();
    box.append(el('div', 'sb-caption', `${mode === 'race' ? 'RACE · METRES IN 10 LAPS' : 'HOT LAP'} · LAGUNA SECA · PROBE GT`));
    const st = key ? this.states.get(key) : undefined;
    if (!key || !ctx) { box.append(el('div', 'sb-msg', 'LOADING THE TRACK…')); return box; }
    const me = this.o.client.name;
    const myKey = me ? nameKey(me) : null;
    const row = (s: Score, cls = '') => {
      const r = el('div', `sb-row sb-r${Math.min(s.rank, 11)}${cls}`);
      if (myKey && nameKey(s.name) === myKey) r.classList.add('me');
      r.append(
        el('span', 'sb-rank', ORD(s.rank)),
        el('span', 'sb-nm', s.name.toUpperCase()),
        el('span', 'sb-score', fmtScore(mode, s.score, s.laps, this.o.trackLength())),
        el('span', 'sb-in', INPUT_LABEL[s.input] ?? s.input),
        el('span', 'sb-date', fmtDate(s.at)),
      );
      return r;
    };
    const head = el('div', 'sb-row sb-head');
    head.append(el('span', 'sb-rank', 'RANK'), el('span', 'sb-nm', 'NAME'), el('span', 'sb-score', mode === 'race' ? 'DISTANCE' : 'TIME'),
      el('span', 'sb-in', 'INPUT'), el('span', 'sb-date', 'DATE'));
    const board = st?.board;
    // status first (visible without scrolling), then the last good table if there is one
    if (!st || st.status === 'loading') box.append(el('div', 'sb-msg blink', 'LOADING…'));
    else if (st.status === 'offline') box.append(el('div', 'sb-msg bad', 'SCOREBOARD OFFLINE'), el('div', 'sb-small', `Could not reach the server. Driving is unaffected; try Refresh later.${board ? ' Showing the last board loaded.' : ''}`));
    else if (st.status === 'error') box.append(el('div', 'sb-msg bad', 'SCOREBOARD ERROR'), el('div', 'sb-small', st.error ?? ''));
    else if (!board?.entries.length) box.append(el('div', 'sb-msg', 'NO SCORES YET · SET THE FIRST ONE'));
    if (board && board.entries.length) {
      box.append(head, ...board.entries.map((s) => row(s)));
      const you = board.you;
      if (you && you.rank > LIMITS.top) box.append(el('div', 'sb-sep', '· · ·'), row(you, ' you'));
    }
    const pb = this.o.client.pb(key);
    const foot = [
      me ? `YOU: ${me.toUpperCase()}${board?.you ? ` · RANK ${board.you.rank}` : ''}` : 'NO NAME SET',
      pb !== null ? `DEVICE BEST ${fmtScore(mode, pb, undefined, 0)}` : '',
    ].filter(Boolean).join(' · ');
    box.append(el('div', 'sb-small', foot));
    if (mode === 'hotlap') box.append(el('div', 'sb-small', `Valid laps 1–${LIMITS.maxLap} after a reset can be posted; they are replayed on the server.`));
    return box;
  }

  // ---- the new-best prompt

  private pending: Promise<SubmitOutcome> | null = null;
  private promptPage: MenuPage | null = null;
  private promptDecide: ((o: SubmitOutcome) => void) | null = null;
  /** Best candidate not yet posted (skipped, dismissed or failed): "Submit last lap" in the pause menu. */
  private lastCandidate: Candidate | null = null;

  /**
   * "New best 1:59.321 · Submit as NAME?" as a pause-style menu card (the sim is paused while it is open).
   * Resolves when the player picked; the POST runs in the background after Submit.
   */
  offer(c: Candidate): Promise<SubmitOutcome> {
    const { menu, client } = this.o;
    // a prompt replaced by another menu (portrait pause, …) never decided: release it
    if (this.pending && !this.promptOpen) this.promptDecide?.({ status: 'skipped' });
    if (this.pending) return Promise.resolve({ status: 'skipped' });
    this.lastCandidate = c;
    const scoreText = fmtScore(c.mode, c.score, undefined, 0);
    let resolve!: (o: SubmitOutcome) => void;
    const p = new Promise<SubmitOutcome>((r) => { resolve = r; });
    this.pending = p;
    let decided = false;
    const decide = (o: SubmitOutcome | 'post') => {
      if (decided) return;
      decided = true;
      this.pending = null;
      this.promptPage = null;
      this.promptDecide = null;
      menu.close();
      if (o !== 'post') { resolve(o); return; }
      const name = client.name!;
      this.o.toast(`Submitting ${scoreText} as ${name}…`, 4000);
      void postCandidate(client, c, name).then((out) => {
        if (out.status === 'submitted') {
          if (this.lastCandidate === c) this.lastCandidate = null;
          const r = out.result;
          const stored = r.replayed !== undefined ? ` (${fmtLapTime(r.replayed)})` : '';
          this.o.toast(r.rank !== null ? `Scoreboard: ${name} is #${r.rank}${stored}${r.improved ? '' : ' · your older score stays'}` : `Scoreboard: posted${stored}, outside the top ${LIMITS.keep}`, 5000);
        } else if (out.status === 'failed') this.o.toast(out.message, 6000);
        resolve(out);
      });
    };
    const page: MenuPage = {
      title: `NEW BEST ${scoreText}`,
      get subtitle() {
        const name = client.name;
        return `${c.detail} · ${name ? `Submit as ${name}?` : 'Set a name to submit'}${client.offline ? ' · scoreboard looks offline' : ''}`;
      },
      entries: (): MenuEntry[] => {
        const name = client.name;
        return [
          name
            ? { kind: 'action', id: 'sbSubmit', label: `Submit as ${name}`, run: () => decide('post') }
            : { kind: 'action', id: 'sbSetName', label: 'Enter name', run: () => this.editName(() => decide('post')) },
          { kind: 'action', id: 'sbChange', label: 'Change name', disabled: !name, run: () => this.editName(() => menu.refresh()) },
          { kind: 'action', id: 'sbSkip', label: 'Skip', run: () => decide({ status: 'skipped' }) },
        ];
      },
    };
    this.promptPage = page;
    this.promptDecide = (o) => decide(o);
    // not closable: Back / Start / a backdrop tap do nothing; only Submit or Skip (or Esc on the keyboard) close it
    menu.show(page, {
      closable: false, variant: 'pause',
      onClose: () => decide({ status: 'skipped' }),
      onChange: () => this.o.onChange?.(),
    });
    return p;
  }
}
