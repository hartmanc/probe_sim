// DOM HUD: speed, gear, rpm + shift light, lap times, delta, off-track flag,
// corner min-speed table, mode banner, help overlay, toasts. Settings live in
// the pause menu (menu.ts, built in index.ts).
import { CONTROL_MAP } from './input';
import type { Lap } from './timing';

export const SHIFT_LIGHT_RPM = 6500;
const RPM_MAX = 7200;
const MPH = 2.236936;
/** Phone: the corner card closes itself after this long. */
const CORNERS_CARD_MS = 12000;   // phone card
const CORNERS_PANEL_MS = 10000;  // desktop panel (owner: "should go away after a few seconds")

export function fmtTime(t: number | null | undefined): string {
  if (t == null || !isFinite(t)) return '–:––.–––';
  const m = Math.floor(t / 60);
  const s = t - m * 60;
  return `${m}:${s.toFixed(3).padStart(6, '0')}`;
}

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

export interface CornerRow { name: string; player: number; ref: number }

export interface HudFrame {
  speed: number; gear: number; rpm: number; autoShift: boolean;
  lapNumber: number; started: boolean; current: number; last: Lap | null; best: Lap | null;
  delta: number | null; offTrack: boolean; invalid: boolean;
  /** ABS modulating (flashes a small tag). */
  absActive?: boolean;
  /** Show the lap timing panel (timer + delta). */
  timing?: boolean;
  /** Show the delta-to-reference bar (hot lap). */
  showDelta?: boolean;
}

export interface GameOverOptions {
  /** "Reset" (hot lap: rolling start) or "Recover" (race: back on track in place). */
  resetLabel: string;
  /** e.g. "Press A or Back", "Tap Reset", "Press R or Enter". */
  hint: string;
  onReset(): void;
  onMenu(): void;
  /** Race mode: own title / text and extra buttons between the main button and Main menu (hot lap: none). */
  title?: string;
  line?: string;
  extra?: { label: string; run(): void }[];
}

export class Hud {
  readonly root: HTMLDivElement;
  private speed = el('div', 'speed-val', '0');
  private gear = el('div', 'gear-val', '1');
  private gearMode = el('div', 'gear-mode', 'AUTO');
  private rpmFill = el('div', 'rpm-fill');
  private rpmText = el('div', 'rpm-text', '0');
  private shiftLight = el('div', 'shift-light');
  private lapNo = el('span', 'val', '–');
  private cur = el('span', 'val big', fmtTime(null));
  private last = el('span', 'val', fmtTime(null));
  private best = el('span', 'val', fmtTime(null));
  private deltaVal = el('span', 'delta-val', '±0.00');
  private deltaFill = el('div', 'delta-fill');
  private refName = el('span', 'ref-name', '');
  private flags = el('div', 'flags');
  private offFlag = el('div', 'flag off', 'OFF TRACK');
  private invFlag = el('div', 'flag inv', 'LAP INVALID');
  private absFlag = el('div', 'flag abs', 'ABS');
  private corners = el('div', 'panel corners hidden');
  private banner = el('div', 'mode-banner hidden');
  private timingPanel = el('div', 'panel timing');
  private deltaBox = el('div', 'delta');
  private help = el('div', 'help hidden');
  private toastEl = el('div', 'toast');
  private status = el('div', 'status');
  private gameOverEl = el('div', 'gameover hidden');
  private gearFlashTimer = 0;
  private autoSource: string | null = null;
  private helpHint = 'K remaps and calibrates · Press H to close';
  private helpRows: [string, string, string][] = CONTROL_MAP;
  private toastTimer = 0;
  private cornersTimer = 0;
  /** Phone layout: the corner table is a card that closes on a tap or after CORNERS_CARD_MS. */
  compact = false;
  private lastText = new Map<HTMLElement, string>();

  constructor(parent: HTMLElement) {
    this.root = el('div', 'hud hidden');
    parent.appendChild(this.root);

    // ---- timing panel (top left)
    const timing = this.timingPanel;
    const row = (label: string, v: HTMLElement, cls = '') => { const r = el('div', 'row' + cls); r.append(el('span', 'lbl', label), v); return r; };
    timing.append(row('LAP', this.lapNo), row('CURRENT', this.cur), row('LAST', this.last, ' row-last'), row('BEST', this.best, ' row-best'));
    const d = this.deltaBox;
    const dh = el('div', 'row'); dh.append(el('span', 'lbl', 'Δ'), this.refName, this.deltaVal);
    const bar = el('div', 'delta-bar'); bar.append(el('div', 'delta-mid'), this.deltaFill);
    d.append(dh, bar);
    timing.append(d);
    this.root.append(timing);

    // ---- mode banner + flags (top centre)
    this.root.append(this.banner);
    this.flags.append(this.offFlag, this.invFlag, this.absFlag);
    this.root.append(this.flags);

    // ---- dash (bottom centre)
    const dash = el('div', 'panel dash');
    const sp = el('div', 'speed'); sp.append(this.speed, el('div', 'speed-unit', 'MPH'));
    const gr = el('div', 'gear'); gr.append(this.gear, this.gearMode);
    const top = el('div', 'dash-top'); top.append(sp, gr);
    const rpm = el('div', 'rpm');
    const rpmBar = el('div', 'rpm-bar');
    const mark = el('div', 'rpm-mark'); mark.style.left = `${(SHIFT_LIGHT_RPM / RPM_MAX) * 100}%`;
    rpmBar.append(this.rpmFill, mark);
    const rpmRow = el('div', 'rpm-row'); rpmRow.append(this.shiftLight, rpmBar, this.rpmText);
    rpm.append(rpmRow);
    dash.append(top, rpm);
    this.root.append(dash);

    // ---- corner table (left)
    this.root.append(this.corners);

    // ---- help (above menus), toasts (above everything)
    this.buildHelp();
    this.root.append(this.status);
    parent.append(this.gameOverEl, this.help, this.toastEl);
  }

  /** Show / hide the driving HUD (hidden behind the main menu). */
  setVisible(on: boolean): void { this.root.classList.toggle('hidden', !on); }

  private buildHelp(rows: [string, string, string][] = this.helpRows): void {
    this.helpRows = rows;
    const h = this.help;
    h.replaceChildren();
    h.append(el('h2', '', 'Controls'));
    const t = el('table');
    const hr = el('tr'); hr.append(el('th', '', ''), el('th', '', 'Gamepad'), el('th', '', 'Keyboard'));
    t.append(hr);
    for (const [a, p, k] of rows) { const r = el('tr'); r.append(el('td', '', a), el('td', '', p || '–'), el('td', '', k)); t.append(r); }
    h.append(t, el('p', 'hint', this.helpHint));
  }

  /** Rebuild the help overlay from the current bindings (labels already in the pad's glyphs). */
  setControlRows(rows: [string, string, string][], hint?: string): void {
    if (hint) this.helpHint = hint;
    this.buildHelp(rows);
  }

  /** Mode banner at the top centre (race: "Race · lap 1/10 · P20 · 45 cars"); null hides it. */
  setBanner(text: string | null): void {
    this.banner.classList.toggle('hidden', !text);
    this.text(this.banner, text ?? '');
  }

  /** Hide the corner table (mode change / restart). */
  hideCorners(): void { this.corners.classList.add('hidden'); clearTimeout(this.cornersTimer); }

  setRefName(label: string): void { this.refName.textContent = label; }
  /** Label the auto-shift mode with the ghost whose gear schedule it follows (null: rpm rules). */
  setAutoSource(driver: string | null): void { this.autoSource = driver; }
  get autoSourceDriver(): string | null { return this.autoSource; }
  /** Briefly highlight the gear number (automatic shift), so a learner sees where the ghost shifts. */
  flashGear(): void {
    this.gear.classList.remove('flash');
    void this.gear.offsetWidth; // restart the animation
    this.gear.classList.add('flash');
    clearTimeout(this.gearFlashTimer);
    this.gearFlashTimer = window.setTimeout(() => this.gear.classList.remove('flash'), 700);
  }
  setStatus(text: string): void { this.status.textContent = text; }

  /**
   * Full-screen game over after the space launch: a card with a large Reset (or Recover, in a race) button and
   * Main menu. speedMps: closing speed of the hit; hint names the controls for the input in use.
   */
  showGameOver(speedMps: number, opts: GameOverOptions): void {
    const mph = Math.round(speedMps * MPH);
    const reset = el('button', 'btn go-reset', opts.resetLabel);
    reset.addEventListener('click', (e) => { e.stopPropagation(); opts.onReset(); });
    const main = el('button', 'btn go-menu', 'Main menu');
    main.addEventListener('click', (e) => { e.stopPropagation(); opts.onMenu(); });
    const btns = el('div', 'go-buttons'); btns.append(reset);
    for (const x of opts.extra ?? []) {
      const b = el('button', 'btn go-extra', x.label);
      b.addEventListener('click', (e) => { e.stopPropagation(); x.run(); });
      btns.append(b);
    }
    btns.append(main);
    const card = el('div', 'go-card');
    card.append(
      el('h1', undefined, opts.title ?? 'GAME OVER'),
      el('div', 'line', opts.line ?? `You hit the wall at ${mph} mph and blasted into space.`),
      btns,
      el('div', 'hint', opts.hint),
    );
    this.gameOverEl.replaceChildren(card);
    this.gameOverEl.classList.remove('hidden');
  }
  get gameOverOpen(): boolean { return !this.gameOverEl.classList.contains('hidden'); }

  hideGameOver(): void { this.gameOverEl.classList.add('hidden'); }
  toggleHelp(): void { this.help.classList.toggle('hidden'); }
  get helpOpen(): boolean { return !this.help.classList.contains('hidden'); }
  hideHelp(): void { this.help.classList.add('hidden'); }

  toast(msg: string, ms = 1600): void {
    this.toastEl.textContent = msg;
    this.toastEl.classList.add('show');
    clearTimeout(this.toastTimer);
    this.toastTimer = window.setTimeout(() => this.toastEl.classList.remove('show'), ms);
  }

  private text(e: HTMLElement, s: string): void {
    if (this.lastText.get(e) !== s) { e.textContent = s; this.lastText.set(e, s); }
  }

  update(f: HudFrame): void {
    this.text(this.speed, Math.round(Math.abs(f.speed) * MPH).toString());
    this.text(this.gear, f.gear === -1 ? 'R' : f.gear === 0 ? 'N' : String(f.gear));
    this.text(this.gearMode, f.autoShift ? (this.autoSource ? `AUTO · ${this.autoSource.toUpperCase()}` : 'AUTO') : 'MANUAL');
    const r = Math.max(0, Math.min(1, f.rpm / RPM_MAX));
    this.rpmFill.style.transform = `scaleX(${r.toFixed(3)})`;
    this.text(this.rpmText, (Math.round(f.rpm / 50) * 50).toString());
    const shift = f.rpm >= SHIFT_LIGHT_RPM;
    this.shiftLight.classList.toggle('on', shift);
    this.rpmFill.classList.toggle('hot', shift);
    this.text(this.lapNo, f.started ? String(f.lapNumber) : 'out lap');
    this.text(this.cur, f.started ? fmtTime(f.current) : fmtTime(null));
    this.text(this.last, f.last ? fmtTime(f.last.time) : fmtTime(null));
    this.last.classList.toggle('invalid', !!f.last && !f.last.valid);
    this.text(this.best, f.best ? fmtTime(f.best.time) : fmtTime(null));
    this.cur.classList.toggle('invalid', f.invalid);
    if (f.delta == null) {
      this.text(this.deltaVal, '±0.00');
      this.deltaFill.style.width = '0';
      this.deltaVal.className = 'delta-val';
    } else {
      const d = f.delta;
      this.text(this.deltaVal, (d >= 0 ? '+' : '−') + Math.abs(d).toFixed(2));
      this.deltaVal.className = 'delta-val ' + (d > 0 ? 'slower' : 'faster');
      const w = Math.min(1, Math.abs(d) / 2) * 50;
      this.deltaFill.style.width = `${w}%`;
      this.deltaFill.style.left = d > 0 ? '50%' : `${50 - w}%`;
      this.deltaFill.className = 'delta-fill ' + (d > 0 ? 'slower' : 'faster');
    }
    this.offFlag.classList.toggle('show', f.offTrack);
    this.invFlag.classList.toggle('show', f.invalid);
    this.absFlag.classList.toggle('show', !!f.absActive);
    this.timingPanel.classList.toggle('hidden', f.timing === false);
    this.deltaBox.classList.toggle('hidden', f.showDelta === false);
  }

  showCorners(lap: Lap, refLabel: string, rows: CornerRow[]): void {
    const c = this.corners;
    c.replaceChildren();
    c.classList.remove('hidden');
    const h = el('div', 'corner-head');
    h.append(el('span', '', `Lap ${lap.n} · ${fmtTime(lap.time)}${lap.valid ? '' : ' (invalid)'}`));
    c.append(h);
    const t = el('table');
    const hr = el('tr'); hr.append(el('th', '', 'Corner'), el('th', '', 'You'), el('th', '', refLabel), el('th', '', 'Δ'));
    t.append(hr);
    for (const r of rows) {
      const tr = el('tr');
      const pm = isFinite(r.player) ? r.player * MPH : NaN, rm = r.ref * MPH;
      const dd = pm - rm;
      const dcell = el('td', isFinite(dd) ? (dd >= 0 ? 'faster' : 'slower') : '', isFinite(dd) ? (dd >= 0 ? '+' : '−') + Math.abs(dd).toFixed(1) : '–');
      tr.append(el('td', '', r.name), el('td', '', isFinite(pm) ? pm.toFixed(1) : '–'), el('td', '', rm.toFixed(1)), dcell);
      t.append(tr);
    }
    c.append(t, el('div', 'hint', 'Minimum speed (mph) within ±60 m of each corner'));
    if (this.compact) {
      const x = el('button', 'corner-close', '×');
      x.type = 'button';
      x.setAttribute('aria-label', 'Close');
      c.prepend(x);
    }
    // the table is a post-lap card everywhere: a click/tap dismisses it, otherwise it fades after a few seconds
    c.onpointerdown = (e) => { e.stopPropagation(); this.hideCorners(); };
    clearTimeout(this.cornersTimer);
    this.cornersTimer = window.setTimeout(() => this.hideCorners(), this.compact ? CORNERS_CARD_MS : CORNERS_PANEL_MS);
  }
}
