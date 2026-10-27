// Menus: a pure navigation model (MenuModel, RepeatGate; unit-tested) and a
// DOM view (Menu) with large click/touch targets. Used for the main menu at
// boot and the pause menu while driving.
//
// Navigation events come from input.ts (keyboard, d-pad, left stick, A/B,
// Start) or from clicks on the rows.

export type NavEvent = 'up' | 'down' | 'left' | 'right' | 'select' | 'back' | 'menu';

interface EntryBase {
  id: string;
  label: string;
  /** Greyed out and skipped by the cursor. */
  disabled?: boolean;
  /** Small text after the label, e.g. "coming soon". */
  note?: string;
}
export interface ActionEntry extends EntryBase { kind: 'action'; run(): void }
export interface ToggleEntry extends EntryBase { kind: 'toggle'; get(): boolean; set(on: boolean): void }
/** `disabled`: shown, but cycling skips it (a choice that does not apply here, e.g. a Laguna-only reference). */
export interface ChoiceOption { value: string; label: string; disabled?: boolean }
export interface ChoiceEntry extends EntryBase { kind: 'choice'; options: ChoiceOption[]; get(): string; set(v: string): void }
/** A drop-down: mouse and touch open a native <select> (nothing happens until a pick; a pick calls `set` once); keys
 *  and the pad open the options as a page of actions (select = pick). Left/right do nothing, so cycling never loads. */
export interface SelectEntry extends EntryBase { kind: 'select'; options: ChoiceOption[]; get(): string; set(v: string): void }
export interface SubmenuEntry extends EntryBase { kind: 'submenu'; page(): MenuPage }
export interface BackEntry extends EntryBase { kind: 'back' }
export type MenuEntry = ActionEntry | ToggleEntry | ChoiceEntry | SelectEntry | SubmenuEntry | BackEntry;

export interface MenuPage {
  title: string;
  /** Rich title content (the censored header); `title` stays the accessible name. */
  titleNodes?(): Node[];
  subtitle?: string;
  /** Called on every render, so labels and enabled states stay current. */
  entries(): MenuEntry[];
  /** Optional custom content between the subtitle and the rows (the scoreboard table); rebuilt on every render. */
  body?(): HTMLElement | null;
}

/** Result of a navigation step, for the owner. */
export type NavResult = 'none' | 'moved' | 'changed' | 'pushed' | 'popped' | 'close';

const selectable = (e: MenuEntry | undefined) => !!e && !e.disabled;

/** The options of a select as a page: picking one calls set (the Track select reloads) and closes the page. */
function selectPage(e: SelectEntry): MenuPage {
  return {
    title: e.label,
    entries: () => [
      ...e.options.map((o): MenuEntry => ({ kind: 'action', id: `${e.id}:${o.value}`, label: o.label, note: o.value === e.get() ? 'current' : undefined, disabled: o.disabled, run: () => { if (o.value !== e.get()) e.set(o.value); } })),
      { kind: 'back', id: 'back', label: 'Back' },
    ],
  };
}

/**
 * Stack of pages with a cursor per page. Up/down wrap and skip disabled rows;
 * left/right cycle choices and flip toggles; select runs / flips / cycles /
 * opens; back pops, and at the root returns 'close' when the menu is closable.
 */
export class MenuModel {
  private stack: { page: MenuPage; index: number }[] = [];

  constructor(root: MenuPage, readonly closable = false) { this.reset(root); }

  reset(root: MenuPage): void {
    this.stack = [{ page: root, index: 0 }];
    this.fixCursor(1);
  }

  get page(): MenuPage { return this.top.page; }
  get depth(): number { return this.stack.length; }
  get entries(): MenuEntry[] { return this.page.entries(); }
  get index(): number { return this.top.index; }
  get current(): MenuEntry | undefined { return this.entries[this.top.index]; }

  private get top() { return this.stack[this.stack.length - 1]; }

  /** Keep the cursor on a selectable row (after entries change or a page opens). */
  fixCursor(dir: 1 | -1 = 1): void {
    const es = this.entries, t = this.top;
    if (!es.length) { t.index = 0; return; }
    t.index = Math.min(Math.max(0, t.index), es.length - 1);
    if (selectable(es[t.index])) return;
    for (let k = 1; k <= es.length; k++) {
      const i = (t.index + dir * k + es.length * k) % es.length;
      if (selectable(es[i])) { t.index = i; return; }
    }
  }

  move(dir: 1 | -1): NavResult {
    const es = this.entries, t = this.top;
    for (let k = 1; k <= es.length; k++) {
      const i = ((t.index + dir * k) % es.length + es.length) % es.length;
      if (selectable(es[i])) { const moved = i !== t.index; t.index = i; return moved ? 'moved' : 'none'; }
    }
    return 'none';
  }

  /** Put the cursor on row i (mouse hover / click). */
  focus(i: number): boolean {
    if (!selectable(this.entries[i])) return false;
    this.top.index = i;
    return true;
  }

  /** Cycle a choice or flip a toggle on the current row. */
  adjust(dir: 1 | -1): NavResult {
    const e = this.current;
    if (!e || e.disabled) return 'none';
    if (e.kind === 'toggle') { e.set(!e.get()); return 'changed'; }
    if (e.kind === 'choice' && e.options.length) {
      const i = e.options.findIndex((o) => o.value === e.get());
      const n = e.options.length;
      for (let k = 1; k <= n; k++) {
        const o = e.options[(((i < 0 ? 0 : i) + dir * k) % n + n) % n];
        if (o.disabled) continue;
        e.set(o.value);
        return 'changed';
      }
      return 'none';
    }
    return 'none';
  }

  select(): NavResult {
    const e = this.current;
    if (!e || e.disabled) return 'none';
    switch (e.kind) {
      case 'action': e.run(); return 'changed';
      case 'toggle': case 'choice': return this.adjust(1);
      case 'select': this.stack.push({ page: selectPage(e), index: Math.max(0, e.options.findIndex((o) => o.value === e.get())) }); this.fixCursor(1); return 'pushed';
      case 'submenu': this.stack.push({ page: e.page(), index: 0 }); this.fixCursor(1); return 'pushed';
      case 'back': return this.back();
    }
  }

  back(): NavResult {
    if (this.stack.length > 1) { this.stack.pop(); this.fixCursor(1); return 'popped'; }
    return this.closable ? 'close' : 'none';
  }

  nav(ev: NavEvent): NavResult {
    switch (ev) {
      case 'up': return this.move(-1);
      case 'down': return this.move(1);
      case 'left': return this.adjust(-1);
      case 'right': return this.adjust(1);
      case 'select': return this.select();
      case 'back': return this.back();
      case 'menu': return this.closable ? 'close' : this.select(); // Start: close the pause menu, or pick on the main menu
    }
  }
}

/**
 * Key repeat for held directions: one event on press, the next after
 * `initialMs`, then every `rateMs` while held.
 */
export class RepeatGate<T extends string = string> {
  private cur: T | null = null;
  private next = 0;
  constructor(readonly initialMs = 350, readonly rateMs = 120) {}

  /** Feed the held direction (or null) each poll; returns a direction to emit, or null. */
  update(dir: T | null, now: number): T | null {
    if (dir !== this.cur) {
      this.cur = dir;
      if (dir == null) return null;
      this.next = now + this.initialMs;
      return dir;
    }
    if (dir != null && now >= this.next) {
      this.next += this.rateMs;
      if (this.next <= now) this.next = now + this.rateMs; // late poll: no burst
      return dir;
    }
    return null;
  }

  /** A press already emitted elsewhere (keydown): start the repeat clock without a second event. */
  press(dir: T, now: number): void { this.cur = dir; this.next = now + this.initialMs; }
}

// ---------------------------------------------------------------- DOM view

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

export interface MenuHints { select: string; back: string; menu: string }

export interface MenuOptions {
  /** Pause menu (true): Back / Start at the root close it. Main menu (false): cannot be closed. */
  closable: boolean;
  /** 'main' is full screen and opaque; 'pause' dims the scene behind it. */
  variant: 'main' | 'pause';
  onClose?(): void;
  /** Called after any change (to re-render the scene, refresh the HUD, ...). */
  onChange?(): void;
}

/** The menu on screen. One instance; `show` swaps the page stack. */
export class Menu {
  readonly root = el('div', 'menu hidden');
  /** Extra content under the title of the root page (loading progress on the main menu). */
  readonly extra = el('div', 'menu-extra');
  private card = el('div', 'menu-card');
  private titleEl = el('h1', 'menu-title');
  private subEl = el('div', 'menu-sub');
  private bodyEl = el('div', 'menu-body');
  private list = el('div', 'menu-list');
  private footer = el('div', 'menu-footer');
  private model: MenuModel | null = null;
  private opts: MenuOptions = { closable: false, variant: 'main' };
  private hintText = '';

  constructor(parent: HTMLElement, private hints: () => MenuHints) {
    this.card.append(this.titleEl, this.subEl, this.extra, this.bodyEl, this.list, this.footer);
    this.root.append(this.card);
    // a click on the dimmed backdrop of the pause menu resumes
    this.root.addEventListener('click', (e) => { if (e.target === this.root && this.opts.closable) this.close(); });
    parent.appendChild(this.root);
  }

  get isOpen(): boolean { return !this.root.classList.contains('hidden'); }
  get variant(): MenuOptions['variant'] { return this.opts.variant; }
  get state(): MenuModel | null { return this.model; }

  show(page: MenuPage, opts: MenuOptions): void {
    this.opts = opts;
    this.model = new MenuModel(page, opts.closable);
    this.root.className = `menu menu-${opts.variant}`;
    this.render();
  }

  close(): void {
    if (!this.isOpen) return;
    this.root.classList.add('hidden');
    this.model = null;
    this.opts.onClose?.();
  }

  nav(ev: NavEvent): void {
    const m = this.model;
    if (!m || !this.isOpen) return;
    if ((ev === 'up' || ev === 'down') && this.scrollBody(ev === 'down' ? 1 : -1)) return;
    const r = m.nav(ev);
    this.after(r);
  }

  /**
   * A page whose body overflows (credits, what's new): down on the last row / up on the first scrolls the body a
   * step instead of wrapping the cursor, so pads and keys can read it without scroll rows; the wheel and touch
   * scroll the box directly. Returns false when there is nothing to scroll that way.
   */
  private scrollBody(dir: 1 | -1): boolean {
    const m = this.model, box = this.bodyEl.firstElementChild as HTMLElement | null;
    if (!m || !box || box.scrollHeight <= box.clientHeight + 1) return false;
    let first = -1, last = -1;
    m.entries.forEach((e, i) => { if (selectable(e)) { if (first < 0) first = i; last = i; } });
    if (dir > 0 ? m.index !== last : m.index !== first) return false;
    const room = dir > 0 ? box.scrollHeight - box.clientHeight - box.scrollTop : box.scrollTop;
    if (room <= 1) return false;
    box.scrollBy({ top: dir * Math.max(60, box.clientHeight * 0.6), behavior: 'auto' });
    return true;
  }

  private after(r: NavResult): void {
    if (r === 'close') { this.close(); return; }
    if (r === 'none') return;
    if (!this.isOpen || !this.model) return; // an action may have closed or replaced the menu
    this.model.fixCursor(1);
    this.render();
    this.opts.onChange?.();
  }

  /** Re-render (entries are read live, e.g. after loading finishes). */
  refresh(): void {
    if (!this.model || !this.isOpen) return;
    this.model.fixCursor(1);
    this.render();
  }

  /** Update the footer hints when the controller kind / last device changes (cheap; call every frame). */
  tickHints(): void {
    if (!this.isOpen) return;
    const t = this.hintLine();
    if (t !== this.hintText) { this.hintText = t; this.footer.textContent = t; }
  }

  private hintLine(): string {
    const h = this.hints();
    const parts = [`${h.select} select`];
    if (this.model && this.model.depth > 1) parts.push(`${h.back} back`);
    else if (this.opts.closable) parts.push(h.back === h.menu ? `${h.back} resume` : `${h.back} / ${h.menu} resume`);
    return parts.join(' · ');
  }

  private render(): void {
    const m = this.model!;
    const page = m.page;
    if (page.titleNodes) { this.titleEl.replaceChildren(...page.titleNodes()); this.titleEl.setAttribute('aria-label', page.title); }
    else { this.titleEl.textContent = page.title; this.titleEl.removeAttribute('aria-label'); }
    this.subEl.textContent = page.subtitle ?? '';
    this.subEl.classList.toggle('hidden', !page.subtitle);
    this.extra.classList.toggle('hidden', m.depth > 1 || !this.extra.childElementCount);
    const body = page.body?.() ?? null;
    this.bodyEl.replaceChildren(...(body ? [body] : []));
    this.bodyEl.classList.toggle('hidden', !body);
    const rows: HTMLElement[] = [];
    m.entries.forEach((e, i) => {
      const isSelect = e.kind === 'select';
      const row = (isSelect ? el('div', 'menu-row menu-select-row') : el('button', 'menu-row')) as HTMLElement;
      if (row instanceof HTMLButtonElement) row.type = 'button';
      row.dataset.id = e.id;
      if (i === m.index) row.classList.add('active');
      if (e.disabled) { row.classList.add('disabled'); row.setAttribute('aria-disabled', 'true'); }
      const label = el('span', 'menu-label', e.label);
      row.append(label);
      if (e.note) label.append(el('span', 'menu-note', e.note));
      if (e.kind === 'toggle') {
        const on = e.get();
        row.append(el('span', 'menu-val pill' + (on ? ' on' : ''), on ? 'On' : 'Off'));
      } else if (e.kind === 'choice') {
        const cur = e.options.find((o) => o.value === e.get());
        const val = el('span', 'menu-val choice');
        const prev = el('span', 'menu-arrow', '‹'), next = el('span', 'menu-arrow', '›');
        prev.addEventListener('click', (ev) => { ev.stopPropagation(); if (m.focus(i)) this.after(m.adjust(-1)); });
        next.addEventListener('click', (ev) => { ev.stopPropagation(); if (m.focus(i)) this.after(m.adjust(1)); });
        val.append(prev, el('span', 'menu-choice', cur?.label ?? '–'), next);
        row.append(val);
      } else if (e.kind === 'select') {
        const sel = el('select', 'menu-select');
        sel.setAttribute('aria-label', e.label);
        sel.disabled = !!e.disabled;
        const cur = e.get();
        for (const o of e.options) {
          const opt = el('option', undefined, o.label);
          opt.value = o.value;
          opt.disabled = !!o.disabled;
          opt.selected = o.value === cur;
          sel.append(opt);
        }
        sel.addEventListener('click', (ev) => ev.stopPropagation());
        sel.addEventListener('focus', () => { if (m.index !== i && m.focus(i)) this.markActive(i); });
        sel.addEventListener('change', () => { if (sel.value !== e.get()) e.set(sel.value); }); // a pick, once
        row.append(sel);
      } else if (e.kind === 'submenu') {
        row.append(el('span', 'menu-val', '›'));
      }
      row.addEventListener('click', () => {
        if (!m.focus(i)) return;
        const sel = row.querySelector('select');
        if (sel) { // the label side of a select row opens the native list; no picker support: the options page
          try { (sel as HTMLSelectElement & { showPicker(): void }).showPicker(); this.markActive(i); return; } catch { /* fall through */ }
        }
        this.after(m.select());
      });
      row.addEventListener('pointermove', () => {
        if (m.index !== i && m.focus(i)) this.markActive(i);
      });
      rows.push(row);
    });
    this.list.replaceChildren(...rows);
    rows[m.index]?.scrollIntoView?.({ block: 'nearest' }); // tall pages (the scoreboard) on small screens
    this.hintText = this.hintLine();
    this.footer.textContent = this.hintText;
  }

  private markActive(i: number): void {
    this.list.querySelectorAll('.menu-row').forEach((r, k) => r.classList.toggle('active', k === i));
  }
}
