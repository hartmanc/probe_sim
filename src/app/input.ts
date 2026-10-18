// Gamepad + keyboard input with remappable bindings and per-control
// calibration (see controls.ts). Runs its own requestAnimationFrame poll so
// it works before the sim starts and while the controls panel is open.
//
// Pedals from a gamepad: each raw source is watched for intermediate values.
// An analog source is used proportionally (calibrated + response curve); a
// source that has only ever reported 0/1 is ramped like a keyboard key. A
// source that reads pressed from the first sample is ignored until it has
// been released once (stale trigger reports).
//
// Menu navigation: while `navMode` is set (a menu or panel is open) no driving
// actions are emitted; arrows / WASD / d-pad / left stick (with key repeat),
// Enter / Space / A, Esc / B produce NavEvents (consumeNav). Start (b9) and
// Esc / O outside menus emit the 'menu' action.
//
// Look-around (cameras.ts): the pad stick not used for steering (lookStickAxes), its click looks back; held
// keys (`,` `.` look left / right, Backspace looks back); click-drag on the 3D view with the mouse.
// lookX (+ = left), lookY (+ = up) are −1..1 targets; the camera rate-limits and springs back.
//
// Touch (phones, touch.ts) is a third source: its steer / throttle / brake are merged like the pad's (largest
// steer, max pedals) and its buttons emit shiftUp / shiftDown / menu. Menus are navigated by tapping rows.
import {
  ANALOG_IDS, DIGITAL_IDS, FIXED_KEYS, KEY_IDS, LookLatch, RESERVED_PAD_BUTTONS, SourceTracker, applyPedal, applySteer, clearKeyBindings, clearPadProfile,
  defaultKeyBindings, defaultPadProfile, describeKeys, describePad, helpRows, loadKeyBindings, loadLookHold, loadPadProfile, lookBackButton,
  lookStickAxes, saveKeyBindings, saveLookHold, savePadProfile, shapeLook,
  triggerAxisToPedal, type AnalogId, type ControlId, type DigitalId, type KeyBindings, type KeyId, type PadProfile,
} from './controls';
import { MENU_BUTTONS, buttonGlyph, detectPadKind, type PadKind } from './glyphs';
import { RepeatGate, type NavEvent } from './menu';
import type { TouchControls } from './touch';

/** 'confirm': Enter / Space / pad A while driving (outside menus); used by the game-over card. */
export type Action = 'shiftUp' | 'shiftDown' | 'camera' | 'autoShift' | 'reset' | 'mute' | 'help' | 'menu' | 'controls' | 'confirm';
/** Things that can be named in hints: a bound control, or a menu verb. */
export type GlyphId = ControlId | 'select' | 'back' | 'menu';
type Dir = 'up' | 'down' | 'left' | 'right';

const NAV_KEYS: Record<string, NavEvent> = {
  ArrowUp: 'up', KeyW: 'up', ArrowDown: 'down', KeyS: 'down', ArrowLeft: 'left', KeyA: 'left', ArrowRight: 'right', KeyD: 'right',
  Enter: 'select', NumpadEnter: 'select', Space: 'select', Escape: 'back', Backspace: 'back',
};
const STICK_NAV = 0.5;

export interface PedalStatus {
  value: number;      // final 0..1 from the pad
  raw: number;        // raw source value fed to calibration
  source: string;     // human-readable source
  analog: boolean;    // proportional source detected
  armed: boolean;     // seen released at least once
}

type Capture =
  | { device: 'pad'; id: ControlId; base: { axes: number[]; buttons: number[] } | null; t0: number; cb: (r: string | null) => void }
  | { device: 'key'; id: KeyId; t0: number; cb: (r: string | null) => void };

interface Calib { id: AnalogId; t0: number; dur: number; lo: number; hi: number; cb: (ok: boolean) => void }

const CAPTURE_THRESHOLD = 0.5;
const CAPTURE_TIMEOUT_MS = 8000;

function approach(v: number, target: number, up: number, down: number, dt: number): number {
  const rate = Math.abs(target) > Math.abs(v) && Math.sign(target) !== -Math.sign(v) ? up : down;
  const d = target - v;
  const m = rate * dt;
  return Math.abs(d) <= m ? target : v + Math.sign(d) * m;
}

function btnValue(pad: Gamepad, i: number): number {
  const b = pad.buttons[i];
  if (!b) return 0;
  return b.value === 0 && b.pressed ? 1 : b.value;
}

export class Input {
  steer = 0; throttle = 0; brake = 0; handbrake = false;
  source: 'keyboard' | 'gamepad' | 'touch' = 'keyboard';
  /** Touch controls (phones); null on desktop. */
  touch: TouchControls | null = null;
  /** True while the controls panel is open: no driving actions are emitted. */
  suspended = false;
  keys: KeyBindings = loadKeyBindings();
  profile: PadProfile = defaultPadProfile();
  padId: string | null = null;
  padStandard = true;
  /** Controller family of the connected pad, for glyphs ('generic' for non-standard mappings); null without a pad. */
  padKind: PadKind | null = null;
  /** Set by the app while a menu / panel is open: driving actions stop, navigation events flow. */
  navMode = false;
  readonly tracker = new SourceTracker();
  /** Pad-only results, for the controls panel test strip. */
  padSteer = 0; steerRaw = 0;
  /** Look-around target: x −1..1 (+ = left), y −1..1 (+ = up); lookBack = full look behind. Zero in menus. */
  lookX = 0; lookY = 0; lookBack = false;
  /** "Hold full look": a stick pushed past 95 % keeps the look when released (persisted). */
  lookHold = loadLookHold();
  pedal: Record<'throttle' | 'brake', PedalStatus> = {
    throttle: { value: 0, raw: 0, source: '–', analog: false, armed: false },
    brake: { value: 0, raw: 0, source: '–', analog: false, armed: false },
  };

  private held = new Set<string>();
  private kSteer = 0; private kThrottle = 0; private kBrake = 0;
  private rampThrottle = 0; private rampBrake = 0;
  private actions: Action[] = [];
  private digitalPrev = new Map<DigitalId, boolean>();
  private anyPrev: boolean[] | null = null;
  private nav: NavEvent[] = [];
  private gate = new RepeatGate<Dir>(350, 120);
  private notices: string[] = [];
  private axisRest = new Map<number, boolean>(); // trigger axis rests at −1?
  private capture: Capture | null = null;
  private calib: Calib | null = null;
  private listeners = new Set<() => void>();
  private lastT = performance.now();
  private latch = new LookLatch();
  private drag: { id: number; x0: number; y0: number; x: number; y: number } | null = null;

  constructor() {
    window.addEventListener('keydown', (e) => this.onKeyDown(e));
    window.addEventListener('keyup', (e) => this.held.delete(e.code));
    window.addEventListener('blur', () => this.held.clear());
    window.addEventListener('gamepaddisconnected', () => { this.padId = null; });
    // mouse look: drag on the 3D view (canvas.view); released = spring back
    window.addEventListener('pointerdown', (e) => {
      if (e.pointerType !== 'mouse' || e.button !== 0 || this.navMode || this.suspended) return;
      if (!(e.target instanceof HTMLCanvasElement) || !e.target.classList.contains('view')) return;
      this.drag = { id: e.pointerId, x0: e.clientX, y0: e.clientY, x: e.clientX, y: e.clientY };
    });
    window.addEventListener('pointermove', (e) => { if (this.drag && e.pointerId === this.drag.id) { this.drag.x = e.clientX; this.drag.y = e.clientY; } });
    const endDrag = (e: PointerEvent) => { if (this.drag && e.pointerId === this.drag.id) this.drag = null; };
    window.addEventListener('pointerup', endDrag);
    window.addEventListener('pointercancel', endDrag);
    const loop = (t: number) => {
      const dt = Math.min(0.05, Math.max(0, (t - this.lastT) / 1000));
      this.lastT = t;
      this.poll(dt);
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  }

  // ------------------------------------------------------------ public API

  /** Input type tag for the scoreboard: 'pad', 'keys' or 'phone'. */
  get inputTag(): 'pad' | 'keys' | 'phone' { return this.source === 'gamepad' ? 'pad' : this.source === 'touch' ? 'phone' : 'keys'; }

  /** Attach the phone's touch controls as a third source. Any touch on the page makes 'touch' the source. */
  attachTouch(t: TouchControls | null): void {
    this.touch = t;
    if (!t) return;
    window.addEventListener('pointerdown', (e) => { if (e.pointerType === 'touch') this.setSource('touch'); }, { capture: true });
  }

  private setSource(s: Input['source']): void {
    if (s === this.source) return;
    this.source = s;
    this.changed();
  }

  /** Kept for callers that drive input explicitly; polling is self-driven. */
  update(_dt: number): void { /* polled in our own rAF loop */ }

  consumeActions(): Action[] { const a = this.actions; this.actions = []; return a; }

  /** Menu navigation events since the last call (only produced in navMode). */
  consumeNav(): NavEvent[] { const n = this.nav; this.nav = []; return n; }

  /** One-time messages for the player (e.g. a migrated controller profile). */
  consumeNotices(): string[] { const n = this.notices; this.notices = []; return n; }

  onChange(fn: () => void): () => void { this.listeners.add(fn); return () => this.listeners.delete(fn); }
  private changed(): void { for (const f of this.listeners) f(); }

  /** Glyph family for pad labels: the connected pad's, or Xbox when none is connected. */
  get glyphKind(): PadKind { return this.padKind ?? 'xbox'; }

  helpRows(): [string, string, string][] { return helpRows(this.profile, this.keys, this.glyphKind); }
  /** Pad binding label; verbose adds raw indices (controls panel). */
  describe(id: ControlId, verbose = false): string { return describePad(id, this.profile.pad[id], this.glyphKind, verbose); }

  /** Name of a control for the device in use: key names for keyboard users, controller glyphs for pad users. */
  glyph(id: GlyphId): string {
    const pad = this.source === 'gamepad' && this.padId != null;
    if (this.source === 'touch' && (id === 'select' || id === 'back' || id === 'menu')) return id === 'select' ? 'Tap' : 'Tap outside';
    if (id === 'select') return pad ? buttonGlyph(this.glyphKind, MENU_BUTTONS.select) : 'Enter';
    if (id === 'back') return pad ? buttonGlyph(this.glyphKind, MENU_BUTTONS.back) : 'Esc';
    if (id === 'menu') return pad ? buttonGlyph(this.glyphKind, MENU_BUTTONS.menu) : 'Esc';
    if (pad) return this.describe(id);
    if (id === 'steer') return `${describeKeys(this.keys.steerLeft)} ${describeKeys(this.keys.steerRight)}`;
    return describeKeys(this.keys[id]);
  }

  capturing(): { device: 'pad' | 'key'; id: string } | null { return this.capture ? { device: this.capture.device, id: this.capture.id } : null; }
  calibrating(): { id: AnalogId; frac: number; lo: number; hi: number } | null {
    const c = this.calib;
    return c ? { id: c.id, frac: Math.min(1, (performance.now() - c.t0) / c.dur), lo: c.lo, hi: c.hi } : null;
  }

  beginPadCapture(id: ControlId, cb: (r: string | null) => void): void {
    this.cancelCapture();
    this.capture = { device: 'pad', id, base: null, t0: performance.now(), cb };
  }
  beginKeyCapture(id: KeyId, cb: (r: string | null) => void): void {
    this.cancelCapture();
    this.capture = { device: 'key', id, t0: performance.now(), cb };
  }
  cancelCapture(): void {
    const c = this.capture; this.capture = null;
    if (c) c.cb(null);
  }

  beginCalibration(id: AnalogId, cb: (ok: boolean) => void, seconds = 4): void {
    this.calib = { id, t0: performance.now(), dur: seconds * 1000, lo: Infinity, hi: -Infinity, cb };
  }

  setCal(id: AnalogId, patch: Partial<PadProfile['cal'][AnalogId]>): void {
    Object.assign(this.profile.cal[id], patch);
    this.save();
  }

  setLookHold(on: boolean): void {
    this.lookHold = on;
    saveLookHold(on);
    if (!on) this.latch.clear();
  }

  resetDefaults(): void {
    this.profile = defaultPadProfile();
    this.keys = defaultKeyBindings();
    if (this.padId) clearPadProfile(this.padId);
    clearKeyBindings();
    this.tracker.reset();
    this.changed();
  }

  // ------------------------------------------------------------ keyboard

  private onKeyDown(e: KeyboardEvent): void {
    const tag = (e.target as HTMLElement | null)?.tagName;
    const cap = this.capture;
    if (cap && cap.device === 'key') {
      e.preventDefault();
      if (e.code === 'Escape') { this.cancelCapture(); return; }
      if (e.code in FIXED_KEYS) return; // reserved; keep waiting
      for (const k of KEY_IDS) this.keys[k] = this.keys[k].filter((c) => c !== e.code);
      this.keys[cap.id] = [e.code];
      saveKeyBindings(this.keys);
      this.capture = null;
      cap.cb(e.code);
      this.changed();
      return;
    }
    if (tag === 'INPUT' || tag === 'SELECT') return;
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space', 'Enter'].includes(e.code)) e.preventDefault();
    this.held.add(e.code);
    this.source = 'keyboard';
    if (e.repeat) return;
    if (this.navMode) {
      const ev = NAV_KEYS[e.code];
      if (ev) {
        this.nav.push(ev);
        if (ev === 'up' || ev === 'down' || ev === 'left' || ev === 'right') this.gate.press(ev, performance.now());
        return;
      }
    }
    const fixed = FIXED_KEYS[e.code];
    if (fixed) { this.actions.push(fixed); return; }
    if (this.suspended || this.navMode) return;
    if (e.code === 'Enter' || e.code === 'NumpadEnter' || e.code === 'Space') this.actions.push('confirm');
    for (const id of DIGITAL_IDS) {
      if (id !== 'handbrake' && this.keys[id].includes(e.code)) this.actions.push(id);
    }
  }

  private keyHeld(id: KeyId): boolean {
    for (const c of this.keys[id]) if (this.held.has(c)) return true;
    return false;
  }

  // ------------------------------------------------------------ gamepad

  private getPad(): Gamepad | null {
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    let pad: Gamepad | null = null;
    for (const p of pads) if (p && p.connected) { pad = p; break; }
    if (!pad) return null;
    if (pad.id !== this.padId) {
      this.padId = pad.id;
      this.padStandard = pad.mapping === 'standard';
      this.padKind = this.padStandard ? detectPadKind(pad.id) : 'generic';
      const { profile, migrated } = loadPadProfile(pad.id);
      this.profile = profile;
      if (migrated) {
        const k = this.padKind;
        this.notices.push(`New controller layout: shift ${buttonGlyph(k, 5)} / ${buttonGlyph(k, 4)}, ${buttonGlyph(k, 9)} pauses, auto-shift ${buttonGlyph(k, 2)}`);
      }
      this.tracker.reset();
      this.axisRest.clear();
      this.digitalPrev.clear();
      this.anyPrev = null;
      this.changed();
    }
    return pad;
  }

  private save(): void {
    if (this.padId) savePadProfile(this.padId, this.profile);
    this.changed();
  }

  /** Raw pedal reading for throttle/brake from its bound source. */
  private readPedal(pad: Gamepad, id: 'throttle' | 'brake', dt: number): PedalStatus {
    const src = this.profile.pad[id];
    const cal = this.profile.cal[id];
    let raw = 0, key = '', label = '';
    let norm = 0; // 0..1 linear, for analog detection
    if (src.kind === 'auto') {
      const bi = id === 'throttle' ? 7 : 6;
      const bkey = `b${bi}`;
      const bv = btnValue(pad, bi);
      this.tracker.observe(bkey, bv);
      raw = bv; key = bkey; label = describePad(id, src, this.glyphKind, true);
      if (!this.tracker.isAnalog(bkey)) {
        // trigger-as-axis fallback (non-standard mappings report triggers as axes)
        const cands = pad.axes.length > 4 ? (id === 'throttle' ? [5, 4] : [2, 3]) : [];
        for (const ai of cands) {
          const a = pad.axes[ai] ?? 0;
          if (!this.axisRest.has(ai)) this.axisRest.set(ai, a < -0.9);
          const v = triggerAxisToPedal(a, this.axisRest.get(ai)!);
          const akey = `a${ai}t`;
          this.tracker.observe(akey, v);
          if (this.tracker.isAnalog(akey)) { raw = v; key = akey; label = `Axis ${ai} (trigger)`; break; }
        }
      }
      norm = raw;
    } else if (src.kind === 'button') {
      raw = btnValue(pad, src.index); key = `b${src.index}`; label = describePad(id, src, this.glyphKind, true);
      norm = raw;
      this.tracker.observe(key, raw);
    } else if (src.kind === 'axis') {
      raw = src.sign * (pad.axes[src.index] ?? 0); key = `a${src.index}${src.sign > 0 ? '+' : '-'}`; label = describePad(id, src, this.glyphKind, true);
      const span = cal.max - cal.min;
      norm = Math.abs(span) > 1e-3 ? Math.max(0, Math.min(1, (raw - cal.min) / span)) : Math.max(0, raw);
      this.tracker.observe(key, norm);
    } else {
      return { value: 0, raw: 0, source: '–', analog: false, armed: true };
    }
    const analog = this.tracker.isAnalog(key);
    const armed = this.tracker.isArmed(key);
    let value: number;
    if (!armed) value = 0;
    else if (analog) value = applyPedal(raw, cal);
    else {
      // digital 0/1 source: ramp, never a step
      const target = (cal.invert ? 1 - norm : norm) > 0.5 ? 1 : 0;
      if (id === 'throttle') value = this.rampThrottle = approach(this.rampThrottle, target, 3.0, 6.0, dt);
      else value = this.rampBrake = approach(this.rampBrake, target, 2.5, 8.0, dt);
    }
    if (analog) { if (id === 'throttle') this.rampThrottle = value; else this.rampBrake = value; }
    return { value, raw, source: label, analog, armed };
  }

  private digitalPressed(pad: Gamepad, id: DigitalId): boolean {
    const s = this.profile.pad[id];
    if (s.kind === 'button') return btnValue(pad, s.index) > 0.5;
    if (s.kind === 'axis') return s.sign * (pad.axes[s.index] ?? 0) > 0.5;
    return false;
  }

  private processPadCapture(pad: Gamepad): void {
    const c = this.capture;
    if (!c || c.device !== 'pad') return;
    const axes = Array.from(pad.axes);
    const buttons = pad.buttons.map((_, i) => btnValue(pad, i));
    if (!c.base) { c.base = { axes, buttons }; return; }
    let best: { kind: 'axis' | 'button'; index: number; d: number } | null = null;
    for (let i = 0; i < axes.length; i++) {
      const d = axes[i] - (c.base.axes[i] ?? 0);
      if (Math.abs(d) > CAPTURE_THRESHOLD && (!best || Math.abs(d) > Math.abs(best.d))) best = { kind: 'axis', index: i, d };
    }
    if (c.id !== 'steer') {
      for (let i = 0; i < buttons.length; i++) {
        if (RESERVED_PAD_BUTTONS.includes(i)) continue; // Start stays the pause menu
        const d = buttons[i] - (c.base.buttons[i] ?? 0);
        if (Math.abs(d) > CAPTURE_THRESHOLD && !best) best = { kind: 'button', index: i, d };
      }
    }
    if (!best) return;
    const id = c.id;
    const p = this.profile;
    if (best.kind === 'axis') {
      const sign: 1 | -1 = best.d > 0 ? 1 : -1;
      p.pad[id] = { kind: 'axis', index: best.index, sign };
      if (id === 'steer') { p.cal.steer.min = -1; p.cal.steer.max = 1; }
      else if (id === 'throttle' || id === 'brake') { p.cal[id].min = sign * (c.base.axes[best.index] ?? 0); p.cal[id].max = 1; }
    } else {
      p.pad[id] = { kind: 'button', index: best.index };
      if (id === 'throttle' || id === 'brake') { p.cal[id].min = 0; p.cal[id].max = 1; }
    }
    this.digitalPrev.delete(id as DigitalId);
    this.capture = null;
    this.save();
    c.cb(this.describe(id, true));
  }

  /** Start → 'menu' action; in navMode A / B / d-pad / left stick → navigation (with key repeat). */
  private padMenu(pad: Gamepad, pressed: boolean[], edge: (i: number) => boolean): void {
    if (edge(MENU_BUTTONS.menu)) this.actions.push('menu');
    if (!this.navMode) {
      const a = MENU_BUTTONS.select;
      if (edge(a) && !this.suspended && !DIGITAL_IDS.some((id) => { const s = this.profile.pad[id]; return s.kind === 'button' && s.index === a; })) this.actions.push('confirm');
      this.gate.update(null, performance.now());
      return;
    }
    if (edge(MENU_BUTTONS.select)) this.nav.push('select');
    if (edge(MENU_BUTTONS.back)) this.nav.push('back');
    const ax = pad.axes[0] ?? 0, ay = pad.axes[1] ?? 0;
    let dir: Dir | null = null;
    if (pressed[MENU_BUTTONS.up]) dir = 'up';
    else if (pressed[MENU_BUTTONS.down]) dir = 'down';
    else if (pressed[MENU_BUTTONS.left]) dir = 'left';
    else if (pressed[MENU_BUTTONS.right]) dir = 'right';
    else if (Math.abs(ay) > STICK_NAV && Math.abs(ay) >= Math.abs(ax)) dir = ay < 0 ? 'up' : 'down';
    else if (Math.abs(ax) > STICK_NAV) dir = ax < 0 ? 'left' : 'right';
    if (dir) this.source = 'gamepad';
    this.navRepeat(dir);
  }

  private navRepeat(padDir: Dir | null): void {
    // held keys repeat too (their first press was emitted on keydown)
    let dir = padDir;
    if (!dir) for (const [code, ev] of Object.entries(NAV_KEYS)) {
      if (this.held.has(code) && (ev === 'up' || ev === 'down' || ev === 'left' || ev === 'right')) { dir = ev; break; }
    }
    const e = this.gate.update(dir, performance.now());
    if (e) this.nav.push(e);
  }

  private poll(dt: number): void {
    // capture timeout
    if (this.capture && performance.now() - this.capture.t0 > CAPTURE_TIMEOUT_MS) this.cancelCapture();

    // ---- keyboard (ramped)
    const tSteer = (this.keyHeld('steerLeft') ? 1 : 0) - (this.keyHeld('steerRight') ? 1 : 0);
    this.kSteer = approach(this.kSteer, tSteer, 2.2, 4.0, dt);
    this.kThrottle = approach(this.kThrottle, this.keyHeld('throttle') ? 1 : 0, 3.0, 6.0, dt);
    this.kBrake = approach(this.kBrake, this.keyHeld('brake') ? 1 : 0, 4.0, 8.0, dt);
    let steer = this.kSteer, throttle = this.kThrottle, brake = this.kBrake;
    let hb = this.keyHeld('handbrake');
    // look keys: a glance to ±90° (stick reaches ±120°), the back key looks behind
    let lookX = ((this.keyHeld('lookLeft') ? 1 : 0) - (this.keyHeld('lookRight') ? 1 : 0)) * 0.75, lookY = 0;
    let lookBack = this.keyHeld('lookBack');
    if (this.drag) {
      const s = Math.max(240, Math.min(window.innerWidth, window.innerHeight) * 0.5); // half the short side = full look
      // the view follows the mouse: drag right looks right, drag up looks up
      lookX = Math.max(-1, Math.min(1, (this.drag.x0 - this.drag.x) / s));
      lookY = Math.max(-1, Math.min(1, (this.drag.y0 - this.drag.y) / s));
    }

    // ---- gamepad
    const pad = this.getPad();
    if (pad) {
      const pressed = pad.buttons.map((b) => b.pressed || b.value > 0.5);
      const before = this.anyPrev;
      const edge = (i: number) => !!before && !!pressed[i] && !before[i];
      this.anyPrev = pressed;
      if (before && pressed.some((p, i) => p && !before[i])) this.source = 'gamepad';

      if (this.capture?.device === 'pad') this.processPadCapture(pad);
      else if (!this.capture) this.padMenu(pad, pressed, edge);

      const ss = this.profile.pad.steer;
      this.steerRaw = ss.kind === 'axis' ? ss.sign * (pad.axes[ss.index] ?? 0) : 0;
      this.padSteer = ss.kind === 'axis' ? applySteer(this.steerRaw, this.profile.cal.steer) : 0;
      this.pedal.throttle = this.readPedal(pad, 'throttle', dt);
      this.pedal.brake = this.readPedal(pad, 'brake', dt);

      const capturing = !!this.capture;
      for (const id of DIGITAL_IDS) {
        const on = this.digitalPressed(pad, id);
        const prev = this.digitalPrev.get(id);
        this.digitalPrev.set(id, on);
        if (id === 'handbrake') { if (!capturing) hb = hb || on; continue; }
        if (on && prev === false && !capturing && !this.suspended && !this.navMode) this.actions.push(id);
      }

      if (!capturing) {
        if (Math.abs(this.padSteer) > Math.abs(steer)) steer = this.padSteer;
        throttle = Math.max(throttle, this.pedal.throttle.value);
        brake = Math.max(brake, this.pedal.brake.value);
      }
      if (this.pedal.throttle.value > 0.05 || this.pedal.brake.value > 0.05 || Math.abs(this.padSteer) > 0.05) this.source = 'gamepad';

      // look stick (standard mapping only: other mappings put triggers on axes 2/3)
      const la = this.padStandard ? lookStickAxes(this.profile) : null;
      if (la && !capturing) {
        const ax = pad.axes[la[0]] ?? 0, ay = pad.axes[la[1]] ?? 0;
        const [sx, sy] = this.latch.update(Math.hypot(ax, ay), shapeLook(ax, ay), this.lookHold);
        if (Math.abs(sx) > Math.abs(lookX)) lookX = sx;
        if (Math.abs(sy) > Math.abs(lookY)) lookY = sy;
        const lb = lookBackButton(this.profile);
        if (lb != null && btnValue(pad, lb) > 0.5) lookBack = true;
      }
    } else {
      this.padKind = null;
      if (this.source === 'gamepad') this.source = 'keyboard';
      if (this.navMode) this.navRepeat(null);
      this.padSteer = 0; this.steerRaw = 0;
      this.pedal.throttle = { value: 0, raw: 0, source: 'no gamepad', analog: false, armed: false };
      this.pedal.brake = { value: 0, raw: 0, source: 'no gamepad', analog: false, armed: false };
    }

    // ---- calibration sweep
    const cb = this.calib;
    if (cb) {
      const raw = cb.id === 'steer' ? this.steerRaw : this.pedal[cb.id].raw;
      cb.lo = Math.min(cb.lo, raw); cb.hi = Math.max(cb.hi, raw);
      if (performance.now() - cb.t0 >= cb.dur) {
        this.calib = null;
        let ok = false;
        const cal = this.profile.cal[cb.id];
        if (cb.id === 'steer') {
          if (cb.lo < -0.3) { cal.min = cb.lo; ok = true; }
          if (cb.hi > 0.3) { cal.max = cb.hi; ok = true; }
        } else if (cb.hi - cb.lo > 0.3) {
          cal.min = cb.lo; cal.max = cb.hi; ok = true;
        }
        if (ok) this.save();
        cb.cb(ok);
      }
    }

    // ---- touch (phones)
    const tc = this.touch;
    if (tc) {
      tc.update(dt);
      for (const a of tc.consumeActions()) if (!this.suspended && !this.navMode) this.actions.push(a);
      if (tc.isVisible && !this.suspended && !this.navMode) {
        if (Math.abs(tc.steer) > Math.abs(steer)) steer = tc.steer;
        throttle = Math.max(throttle, tc.throttle);
        brake = Math.max(brake, tc.brake);
        if (tc.engaged) this.source = 'touch';
      }
    }

    this.steer = Math.max(-1, Math.min(1, steer));
    this.throttle = Math.max(0, Math.min(1, throttle));
    this.brake = Math.max(0, Math.min(1, brake));
    this.handbrake = hb;
    const off = this.suspended || this.navMode || !!this.capture;
    if (off) this.latch.clear();
    this.lookX = off ? 0 : Math.max(-1, Math.min(1, lookX));
    this.lookY = off ? 0 : Math.max(-1, Math.min(1, lookY));
    this.lookBack = !off && lookBack;
  }
}

/** Default rows for the help overlay (the HUD refreshes from Input.helpRows()). */
export const CONTROL_MAP: [string, string, string][] = helpRows(defaultPadProfile(), defaultKeyBindings());
export { ANALOG_IDS };
