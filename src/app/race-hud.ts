// Race HUD: the flag banner (top centre), the race panel (top left: position, lap, gaps, penalties, metres),
// the standings table (pause menu → Standings) and the results table (at the flag). `raceHudView` maps the
// director's RaceHud to display strings and is pure (unit-tested); the DOM classes only render it.
import { FF_SCALE, type RaceHud, type ResultRow } from '../physics/ai/race';
import { fmtTime } from './hud';
import { fmtLapTime, fmtMetres } from './scoreboard-client';

export type FlagKind = 'yellow' | 'green' | 'chequered' | 'black' | 'none';

export interface RaceHudView {
  flag: FlagKind;
  flagTitle: string;
  flagDetail: string;
  position: string;
  lap: string;
  ahead: string | null;
  behind: string | null;
  penalties: string;
  metres: string;
  lastLap: string;
  bestLap: string;
}

export interface ViewInfo {
  /** team name for a car number */
  teamOf(num: string): string;
  /** metres covered by the player (race distance, ≥ 0) */
  metres: number;
  /** why the player is out of the race (space launch), or null */
  out: string | null;
}

const fmtM = (m: number) => `${Math.round(Math.max(0, m)).toLocaleString('en-US')} m`;
const short = (s: string, n = 22) => (s.length > n ? s.slice(0, n - 1) + '…' : s);

/** Director HUD state → what the race HUD shows. */
export function raceHudView(h: RaceHud, o: ViewInfo): RaceHudView {
  const p = h.penalties;
  let flag: FlagKind = 'none', title = '', detail = '';
  if (o.out) {
    flag = 'black'; title = 'OUT OF THE RACE'; detail = `${o.out} · your race ended at ${fmtM(o.metres)}`;
  } else if (p.ejected) {
    flag = 'black'; title = 'BLACK FLAG · EJECTED'; detail = (h.message ?? p.lastReason ?? '').replace(/^EJECTED:\s*/, '') || 'You are out of the race';
  } else if (p.pending.length > 0) {
    flag = 'black'; title = `BLACK FLAG${p.lastReason ? ` · ${p.lastReason}` : ''}`;
    const more = p.pending.length > 1 ? ` (+${p.pending.length - 1} more queued)` : '';
    if (p.inBox) detail = p.fastForward ? `Serving stop-and-go: ${Math.ceil(p.servingRemaining)} s — car held, time ×${FF_SCALE}${more}`
      : `Serving stop-and-go: ${Math.ceil(p.servingRemaining)} s — stay stopped, get ready to go${more}`;
    else {
      const laps = p.lapsToServe == null ? '' : ` · ${p.lapsToServe.toFixed(1)} laps left to serve it`;
      detail = `Serve a ${Math.ceil(p.servingRemaining || p.pending[0])} s stop-and-go in the pit lane (penalty box)${laps}${more}`;
    }
  } else if (h.flag === 'black') {
    flag = 'black'; title = `BLACK FLAG${p.lastReason ? ` · ${p.lastReason}` : ''}`;
    detail = p.count === 1 ? 'Warning — the next one is a stop-and-go' : (h.message ?? 'Stop-and-go served — rejoin the race');
  } else if (h.phase === 'formation') {
    flag = 'yellow'; title = 'DOUBLE YELLOW · formation'; detail = 'Single file, no passing — the green comes any moment';
  } else if (h.phase === 'yellow') {
    flag = 'yellow'; title = 'DOUBLE YELLOW'; detail = 'No passing';
  } else if (h.phase === 'chequered' || h.phase === 'finished') {
    flag = 'chequered'; title = 'CHEQUERED FLAG'; detail = `P${h.position} of ${h.carsTotal} · ${fmtM(o.metres)}`;
  } else if (h.message && /GREEN/.test(h.message)) {
    flag = 'green'; title = 'GREEN FLAG'; detail = 'Race!';
  } else if (h.message) {
    // leftover director messages (a black flag older than 5 s, "stop-and-go served — rejoin")
    flag = /BLACK|EJECT/i.test(h.message) ? 'black' : 'green'; title = h.message; detail = '';
  }
  const gap = (g: RaceHud['gapAhead'], sign: string) =>
    g ? `${sign} #${g.number} ${short(o.teamOf(g.number))} ${g.seconds < 60 ? `${g.seconds.toFixed(1)} s` : fmtM(g.metres)}` : null;
  const pending = p.pending.length ? ` · ${p.pending.map((s) => `${s} s`).join(' + ')} to serve` : '';
  return {
    flag, flagTitle: title, flagDetail: detail,
    position: `P${h.position}/${h.carsTotal}`,
    lap: `LAP ${h.lap}/${h.lapsTotal}`,
    ahead: gap(h.gapAhead, '▲'),
    behind: gap(h.gapBehind, '▼'),
    penalties: p.count ? `Black flags ${p.count}${pending}` : 'Black flags 0',
    metres: fmtM(o.metres),
    lastLap: fmtTime(h.lastLap),
    bestLap: fmtTime(h.bestLap),
  };
}

// ---------------------------------------------------------------- DOM

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

export class RaceHudDom {
  private flagBox = el('div', 'race-flag hidden');
  private flagTitle = el('div', 'rf-title');
  private flagDetail = el('div', 'rf-detail');
  private panel = el('div', 'panel race-panel');
  private pos = el('span', 'rp-pos');
  private lap = el('span', 'rp-lap');
  private ahead = el('div', 'rp-gap ahead');
  private behind = el('div', 'rp-gap behind');
  private metres = el('div', 'rp-m');
  private pens = el('div', 'rp-pen');
  private laps = el('div', 'rp-laps');
  private last = new Map<HTMLElement, string>();

  constructor(private parent: HTMLElement) {
    this.flagBox.append(this.flagTitle, this.flagDetail);
    const top = el('div', 'rp-top'); top.append(this.pos, this.lap);
    this.panel.append(top, this.ahead, this.behind, this.metres, this.laps, this.pens);
    parent.append(this.flagBox, this.panel);
  }

  private text(e: HTMLElement, s: string): void { if (this.last.get(e) !== s) { e.textContent = s; this.last.set(e, s); } }

  update(v: RaceHudView): void {
    this.flagBox.className = `race-flag flag-${v.flag}${v.flag === 'none' ? ' hidden' : ''}`;
    this.text(this.flagTitle, v.flagTitle);
    this.text(this.flagDetail, v.flagDetail);
    this.flagDetail.classList.toggle('hidden', !v.flagDetail);
    this.text(this.pos, v.position);
    this.text(this.lap, v.lap);
    this.text(this.ahead, v.ahead ?? '▲ leading');
    this.text(this.behind, v.behind ?? '▼ —');
    this.text(this.metres, v.metres);
    this.text(this.laps, `LAST ${v.lastLap} · BEST ${v.bestLap}`);
    this.text(this.pens, v.penalties);
    this.pens.classList.toggle('bad', !v.penalties.endsWith(' 0'));
  }

  /** Loading / no-data state before the director exists. */
  waiting(msg: string): void {
    this.flagBox.className = 'race-flag flag-yellow';
    this.text(this.flagTitle, msg);
    this.flagDetail.classList.add('hidden');
  }

  dispose(): void { this.flagBox.remove(); this.panel.remove(); }
}

/** One row of the standings / results table. */
export interface TableRow {
  position: number; number: string; team: string; class: string;
  metres: number; laps: number; status: string; player: boolean; bestLap?: number | null;
  /** race time to complete all laps, s (finishers only) */
  time?: number | null;
  /** unserved stop-and-go seconds added to `time` (the player, owner 30 Oct 2026) */
  penaltyS?: number;
}

/** Unserved stop-and-go seconds as the screens write them: "60", "20.4". */
export const fmtPenaltyS = (s: number): string => String(+s.toFixed(1));
/** The status cell: "finished", and "finished +60 s" for a player carrying unserved stop-and-go time. */
export const statusText = (r: Pick<TableRow, 'status' | 'penaltyS'>): string =>
  r.penaltyS && r.penaltyS > 0 ? `${r.status} +${fmtPenaltyS(r.penaltyS)} s` : r.status;
/** The results header's note after the time, '' when nothing was added. */
export const penaltyNote = (s: number | undefined): string => (s && s > 0 ? ` · ${fmtPenaltyS(s)} s unserved stop-and-go added` : '');

export type RowStatus = 'running' | 'finished' | 'out' | 'ejected';
/**
 * Status shown in the standings and results tables. At the flag everyone still in the race is classified
 * (Lemons: distance at the flag), so they read "finished"; the player out of the race (space launch) reads "out",
 * a black-flag ejection "ejected"; before the flag, "running".
 */
export function rowStatus(o: { player: boolean; out: boolean; ejected: boolean; flagged: boolean }): RowStatus {
  if (o.player && o.out) return 'out';
  if (o.player && o.ejected) return 'ejected';
  return o.flagged ? 'finished' : 'running';
}

/** Results rows from the director's ResultRow[] (the classification at the flag): "finished", or "out" / "ejected". */
export function resultRows(rows: ResultRow[], out: { metres: number } | null): TableRow[] {
  return rows.map((r) => ({
    position: r.position, number: r.number, team: r.team, class: r.class,
    metres: r.player && out ? out.metres : r.metres,
    laps: r.player && out ? -1 : r.lapsCompleted,
    status: rowStatus({ player: r.player, out: !!out, ejected: r.status === 'ejected', flagged: true }),
    player: r.player, bestLap: r.bestLap, time: r.time, ...(r.penaltyS ? { penaltyS: r.penaltyS } : {}),
  }));
}

/** The standings / results table (`.rt-*`), the player's row highlighted. */
export function raceTable(rows: TableRow[], trackLength: number, caption: string): HTMLElement {
  const box = el('div', 'race-table');
  box.append(el('div', 'rt-caption', caption));
  const head = el('div', 'rt-row rt-head');
  head.append(el('span', 'rt-pos', 'POS'), el('span', 'rt-num', '#'), el('span', 'rt-team', 'TEAM'), el('span', 'rt-dist', 'LAPS + M'), el('span', 'rt-st', 'STATUS'));
  box.append(head);
  let me: HTMLElement | null = null;
  for (const r of rows) {
    const row = el('div', `rt-row${r.player ? ' me' : ''}`);
    const laps = r.laps >= 0 ? r.laps : Math.floor(r.metres / trackLength);
    row.append(
      el('span', 'rt-pos', String(r.position)), el('span', 'rt-num', r.number),
      el('span', 'rt-team', `${r.team}${r.player ? ' (you)' : ''}`),
      el('span', 'rt-dist', r.time != null && laps > 0 ? `${laps}L ${fmtLapTime(r.time)}` : fmtMetres(Math.max(0, r.metres), Math.max(0, laps), trackLength)),
      el('span', `rt-st st-${r.status}`, statusText(r)),
    );
    box.append(row);
    if (r.player) me = row;
  }
  // keep the player's row in view once the menu lays out
  if (me) requestAnimationFrame(() => me!.scrollIntoView({ block: 'nearest' }));
  return box;
}
