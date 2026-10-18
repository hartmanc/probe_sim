// Touch controls for phones (iPhone Safari first, Android Chrome second).
//
// Layout (landscape): left third = brake, right third = throttle. Pedal pressure is how high the touch sits on
// the screen (bottom = 0, top = 1) with a short dead band at the bottom; a touch keeps the zone it started in.
// Steering: tilt (DeviceOrientation, the phone held like a wheel) by default, with a calibration offset
// ("recentre"), a sensitivity setting and a ~15 Hz low-pass; or a thumb slider (horizontal drag in the middle
// third), used automatically while tilt is unavailable (no permission, plain http, no sensor).
// Buttons: pause (top right), shift down / up paddles (upper corners, shown in manual mode).
// The overlay is DOM only and fades when no finger is down.
//
// The pure parts (zones, pedal and slider mapping, tilt maths, the tilt permission state machine) are exported
// and unit-tested in __tests__/touch.test.ts; the TouchControls class is the DOM layer.

export type TouchZone = 'brake' | 'throttle' | 'steer' | null;
export type SteerMode = 'tilt' | 'slider';
export type TouchAction = 'shiftUp' | 'shiftDown' | 'menu';

const clamp = (x: number, a: number, b: number) => (x < a ? a : x > b ? b : x);

/** Pedal dead band at the bottom of a zone, and the height above which the pedal is fully pressed. */
export const PEDAL_DEAD = 0.06, PEDAL_FULL = 0.92;
/** Slider: full lock at this fraction of the half-width of the middle third. */
export const SLIDER_FULL = 0.8;
/** Tilt: wheel angle (deg) for full lock at sensitivity 1, and the dead zone (deg). */
export const TILT_FULL_DEG = 32, TILT_DEAD_DEG = 1.0;
/** Tilt low-pass corner (Hz). */
export const TILT_LP_HZ = 15;
export const SENSITIVITIES = [0.6, 0.8, 1.0, 1.25, 1.5, 1.8];

/** Which zone a touch at (x, y) starts in, for a w × h layer. The middle third steers only in slider mode. */
export function hitZone(x: number, _y: number, w: number, _h: number, steer: SteerMode): TouchZone {
  if (w <= 0) return null;
  const u = x / w;
  if (u < 1 / 3) return 'brake';
  if (u >= 2 / 3) return 'throttle';
  return steer === 'slider' ? 'steer' : null;
}

/** Pedal 0..1 from the touch height: u = 0 at the bottom of the zone, 1 at the top. */
export function pedalFromHeight(u: number, dead = PEDAL_DEAD, full = PEDAL_FULL): number {
  if (!(u > dead)) return 0;
  return clamp((u - dead) / (full - dead), 0, 1);
}

/** Pedal from a client y inside a zone spanning [top, bottom] (CSS px, y grows downward). */
export function pedalFromY(y: number, top: number, bottom: number): number {
  const span = bottom - top;
  return span > 0 ? pedalFromHeight((bottom - y) / span) : 0;
}

/** Slider steering from x in the middle third [left, right]: +1 = full left (the sim's convention). */
export function sliderSteer(x: number, left: number, right: number, full = SLIDER_FULL): number {
  const half = ((right - left) / 2) * full;
  if (half <= 0) return 0;
  return clamp(((left + right) / 2 - x) / half, -1, 1);
}

/**
 * Wheel angle (rad) of a phone held like a steering wheel, from DeviceOrientation beta / gamma (deg) and the
 * screen orientation angle (deg: 0, 90, 180 / -180, 270 / -90). Gravity is projected onto the screen plane, so the
 * result does not depend on how far the phone is tipped back. + = rotated counter-clockwise (steer left).
 */
export function tiltAngle(betaDeg: number, gammaDeg: number, screenDeg: number): number {
  // screenDeg 90: the phone's top edge points left (device +x up); -90: top edge right
  const b = (betaDeg * Math.PI) / 180, g = (gammaDeg * Math.PI) / 180, a = (screenDeg * Math.PI) / 180;
  // "down" in device coordinates (x right, y up in portrait, z out of the screen)
  const dx = Math.cos(b) * Math.sin(g), dy = -Math.sin(b);
  // screen right / up in device coordinates for this screen orientation
  const rx = Math.cos(a), ry = -Math.sin(a);
  const ux = Math.sin(a), uy = Math.cos(a);
  const sx = dx * rx + dy * ry, sy = dx * ux + dy * uy;
  // level wheel: down = (0, -1) on screen; turning left swings it toward screen-left (-x)
  return Math.atan2(-sx, -sy);
}

/** Wrap an angle to (-π, π]. */
export function wrapAngle(a: number): number {
  let x = a;
  while (x > Math.PI) x -= 2 * Math.PI;
  while (x <= -Math.PI) x += 2 * Math.PI;
  return x;
}

/** Steering −1..1 from the wheel angle minus the calibration offset; sensitivity 1 = full lock at TILT_FULL_DEG. */
export function tiltSteer(angle: number, offset: number, sensitivity: number, fullDeg = TILT_FULL_DEG, deadDeg = TILT_DEAD_DEG): number {
  const d = (wrapAngle(angle - offset) * 180) / Math.PI;
  const mag = Math.abs(d);
  if (mag <= deadDeg) return 0;
  const full = fullDeg / Math.max(0.1, sensitivity);
  return Math.sign(d) * clamp((mag - deadDeg) / Math.max(1e-3, full - deadDeg), 0, 1);
}

/** One-pole low-pass step with corner `hz` over `dt` seconds. */
export function lowPass(prev: number, x: number, dt: number, hz = TILT_LP_HZ): number {
  if (!(dt > 0)) return prev;
  const k = 1 - Math.exp(-2 * Math.PI * hz * dt);
  return prev + (x - prev) * k;
}

// ---------------------------------------------------------------- tilt permission state machine

/**
 * unsupported: no sensor API or not a secure context (plain http on the LAN) → slider.
 * prompt: iOS, needs DeviceOrientationEvent.requestPermission() inside a user gesture.
 * requesting: the prompt is up. granted: allowed, waiting for the first reading.
 * active: readings are arriving (tilt steers). silent: allowed but no readings (no sensor, desktop).
 * denied: the user said no (iOS asks again only after Safari is restarted).
 */
export type TiltState = 'unsupported' | 'prompt' | 'requesting' | 'granted' | 'active' | 'silent' | 'denied';
export type TiltEvent = 'request' | 'grant' | 'deny' | 'reading' | 'timeout';

export function tiltInitial(env: { hasEvent: boolean; needsPermission: boolean; secure: boolean }): TiltState {
  if (!env.hasEvent || !env.secure) return 'unsupported';
  return env.needsPermission ? 'prompt' : 'granted';
}

export function tiltNext(s: TiltState, e: TiltEvent): TiltState {
  switch (s) {
    case 'unsupported': return s;
    case 'prompt': case 'denied': return e === 'request' ? 'requesting' : s;
    case 'requesting': return e === 'grant' ? 'granted' : e === 'deny' ? 'denied' : e === 'reading' ? 'active' : s;
    case 'granted': return e === 'reading' ? 'active' : e === 'timeout' ? 'silent' : s;
    case 'silent': return e === 'reading' ? 'active' : s;
    case 'active': return s;
  }
}

/** Steering actually used: tilt only while readings flow, otherwise the slider. */
export function effectiveSteer(mode: SteerMode, tilt: TiltState): SteerMode {
  return mode === 'tilt' && tilt === 'active' ? 'tilt' : 'slider';
}

export function tiltStatusText(s: TiltState): string {
  switch (s) {
    case 'unsupported': return 'needs HTTPS';
    case 'prompt': return 'tap to allow';
    case 'requesting': return 'asking…';
    case 'granted': return 'waiting for sensor';
    case 'silent': return 'no sensor';
    case 'denied': return 'denied';
    case 'active': return '';
  }
}

// ---------------------------------------------------------------- settings

export interface TouchSettings { steer: SteerMode; sensitivity: number }
export const TOUCH_KEY = 'probeSim.touch.v1';

export function loadTouchSettings(): TouchSettings {
  const d: TouchSettings = { steer: 'tilt', sensitivity: 1 };
  try {
    const j = JSON.parse(localStorage.getItem(TOUCH_KEY) ?? 'null') as Partial<TouchSettings> | null;
    if (j && (j.steer === 'tilt' || j.steer === 'slider')) d.steer = j.steer;
    if (j && typeof j.sensitivity === 'number' && isFinite(j.sensitivity)) d.sensitivity = clamp(j.sensitivity, 0.3, 3);
  } catch { /* no storage */ }
  return d;
}
function saveTouchSettings(s: TouchSettings): void {
  try { localStorage.setItem(TOUCH_KEY, JSON.stringify(s)); } catch { /* no storage */ }
}

// ---------------------------------------------------------------- DOM layer

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

interface Ptr { zone: TouchZone; x: number; y: number }

const IDLE_MS = 2500;

type DOEWithPermission = { requestPermission?: () => Promise<'granted' | 'denied'> };

export class TouchControls {
  readonly layer = el('div', 'touch-layer hidden');
  steer = 0; throttle = 0; brake = 0;
  settings: TouchSettings = loadTouchSettings();
  tilt: TiltState;
  /** Raw (filtered) wheel angle from the sensor, rad; NaN before the first reading. */
  tiltRaw = NaN;
  tiltOffset = 0;
  private pendingRecentre = true;
  private ptrs = new Map<number, Ptr>();
  private actions: TouchAction[] = [];
  private lastTouch = 0;
  private lastOrientT = 0;
  private side: 90 | -90 | 0 = 0;
  private sliderTarget = 0;
  private visible = false;
  private manual = false;
  private listeners = new Set<() => void>();
  private brakeFill = el('div', 'tc-fill');
  private throttleFill = el('div', 'tc-fill');
  private steerKnob = el('div', 'tc-knob');
  private steerFill = el('div', 'tc-sfill');
  private steerLabel = el('div', 'tc-steer-label');
  private steerBox = el('div', 'tc-steer');
  private shiftDown = el('button', 'tc-btn tc-shift tc-down', '−');
  private shiftUp = el('button', 'tc-btn tc-shift tc-up', '+');
  private pauseBtn = el('button', 'tc-btn tc-pause');
  readonly rotate = el('div', 'rotate-overlay');
  private portraitMq: MediaQueryList | null = null;

  constructor(parent: HTMLElement) {
    const W = window as unknown as { DeviceOrientationEvent?: DOEWithPermission };
    const DOE = W.DeviceOrientationEvent;
    this.tilt = tiltInitial({
      hasEvent: !!DOE, needsPermission: !!DOE && typeof DOE.requestPermission === 'function', secure: window.isSecureContext !== false,
    });

    // ---- overlay
    const mk = (side: 'brake' | 'throttle', fill: HTMLElement, label: string) => {
      const z = el('div', `tc-zone tc-${side}`);
      const bar = el('div', 'tc-bar');
      bar.append(fill);
      z.append(bar, el('div', 'tc-label', label));
      return z;
    };
    const track = el('div', 'tc-track');
    track.append(el('div', 'tc-mid'), this.steerFill, this.steerKnob);
    this.steerBox.append(track, this.steerLabel);
    for (const b of [this.shiftDown, this.shiftUp, this.pauseBtn]) b.type = 'button';
    this.pauseBtn.setAttribute('aria-label', 'Pause');
    this.shiftDown.setAttribute('aria-label', 'Shift down');
    this.shiftUp.setAttribute('aria-label', 'Shift up');
    const ui = el('div', 'tc-ui');
    ui.append(mk('brake', this.brakeFill, 'BRAKE'), mk('throttle', this.throttleFill, 'GAS'), this.steerBox, el('div', 'tc-sep l'), el('div', 'tc-sep r'));
    this.layer.append(ui, this.shiftDown, this.shiftUp, this.pauseBtn);
    this.rotate.append(el('div', 'rotate-icon', '⟳'), el('div', 'rotate-text', 'Rotate your phone to landscape'));
    parent.append(this.layer, this.rotate);

    // ---- buttons (pointerdown: no 300 ms click delay, works while another finger holds a pedal)
    const btn = (b: HTMLElement, a: TouchAction) => b.addEventListener('pointerdown', (e) => {
      e.preventDefault(); e.stopPropagation();
      this.actions.push(a);
      this.poke();
      if (a !== 'menu') try { navigator.vibrate?.(8); } catch { /* not allowed */ }
    });
    btn(this.shiftDown, 'shiftDown');
    btn(this.shiftUp, 'shiftUp');
    btn(this.pauseBtn, 'menu');

    // ---- pedal / slider pointers
    const L = this.layer;
    L.addEventListener('pointerdown', (e) => this.onDown(e));
    L.addEventListener('pointermove', (e) => this.onMove(e));
    for (const t of ['pointerup', 'pointercancel', 'lostpointercapture'] as const) L.addEventListener(t, (e) => this.onUp(e as PointerEvent));
    // no long-press menu / selection / scroll on the layer
    L.addEventListener('contextmenu', (e) => e.preventDefault());
    L.addEventListener('touchstart', (e) => e.preventDefault(), { passive: false });

    // ---- sensor
    window.addEventListener('deviceorientation', (e) => this.onOrientation(e));
    if (this.tilt === 'granted') this.armSilentTimeout();

    this.portraitMq = window.matchMedia?.('(orientation: portrait)') ?? null;
    this.applyClasses();
  }

  // ------------------------------------------------------------ public

  /** The steering in use now (tilt only while the sensor delivers). */
  get steerMode(): SteerMode { return effectiveSteer(this.settings.steer, this.tilt); }
  /** A finger is on a pedal / the slider. */
  get engaged(): boolean { return this.ptrs.size > 0; }
  /** Portrait on a touch device: the app pauses and shows the rotate overlay (CSS). */
  get portrait(): boolean { return !!this.portraitMq?.matches; }
  get isVisible(): boolean { return this.visible; }

  onChange(fn: () => void): void { this.listeners.add(fn); }
  private changed(): void { this.applyClasses(); for (const f of this.listeners) f(); }

  consumeActions(): TouchAction[] { const a = this.actions; this.actions = []; return a; }

  /** Shown while driving (no menu open). Hiding releases every pointer. */
  setVisible(on: boolean): void {
    if (on === this.visible) return;
    this.visible = on;
    this.layer.classList.toggle('hidden', !on);
    if (!on) { this.ptrs.clear(); this.recompute(); }
    else this.poke();
  }

  /** Manual gearbox: show the shift paddles. */
  setManual(on: boolean): void {
    if (on === this.manual) return;
    this.manual = on;
    this.layer.classList.toggle('manual', on);
  }

  setSteerMode(m: SteerMode): void {
    this.settings.steer = m;
    saveTouchSettings(this.settings);
    if (m === 'tilt') this.requestTilt();
    this.changed();
  }

  setSensitivity(s: number): void {
    this.settings.sensitivity = s;
    saveTouchSettings(this.settings);
    this.changed();
  }

  /** Straight ahead = how the phone is held now (or at the next reading if none yet). */
  recentre(): void {
    if (isFinite(this.tiltRaw)) { this.tiltOffset = this.tiltRaw; this.pendingRecentre = false; }
    else this.pendingRecentre = true;
  }

  /**
   * Ask for motion-sensor access. MUST be called synchronously inside a user gesture (tap / click handler):
   * iOS only shows the prompt then, and only in a secure context.
   */
  requestTilt(): void {
    const DOE = (window as unknown as { DeviceOrientationEvent?: DOEWithPermission }).DeviceOrientationEvent;
    if (this.tilt !== 'prompt' && this.tilt !== 'denied') return;
    if (!DOE?.requestPermission) return;
    this.tilt = tiltNext(this.tilt, 'request');
    this.changed();
    let p: Promise<'granted' | 'denied'>;
    try { p = DOE.requestPermission(); } catch { this.tilt = tiltNext(this.tilt, 'deny'); this.changed(); return; }
    p.then((r) => {
      this.tilt = tiltNext(this.tilt, r === 'granted' ? 'grant' : 'deny');
      if (this.tilt === 'granted') { this.pendingRecentre = true; this.armSilentTimeout(); }
      this.changed();
    }, () => { this.tilt = tiltNext(this.tilt, 'deny'); this.changed(); });
  }

  /** Per input poll: smooth the slider return, update the overlay. */
  update(dt: number): void {
    if (this.steerMode === 'tilt') {
      this.steer = isFinite(this.tiltRaw) ? tiltSteer(this.tiltRaw, this.tiltOffset, this.settings.sensitivity) : 0;
    } else {
      // finger down: direct; released: back to centre at 5 /s (no snap)
      const held = [...this.ptrs.values()].some((p) => p.zone === 'steer');
      if (held) this.steer = this.sliderTarget;
      else { const m = 5 * dt; this.steer = Math.abs(this.steer) <= m ? 0 : this.steer - Math.sign(this.steer) * m; }
    }
    if (this.visible) this.draw();
  }

  // ------------------------------------------------------------ internals

  private applyClasses(): void {
    this.layer.classList.toggle('tilt', this.steerMode === 'tilt');
    this.layer.classList.toggle('slider', this.steerMode === 'slider');
    const t = this.steerMode === 'tilt' ? 'TILT' : this.settings.steer === 'tilt' ? `SLIDE · tilt ${tiltStatusText(this.tilt)}` : 'SLIDE';
    this.steerLabel.textContent = t;
  }

  private armSilentTimeout(): void {
    window.setTimeout(() => {
      if (this.tilt !== 'granted') return;
      this.tilt = tiltNext(this.tilt, 'timeout');
      this.changed();
    }, 2000);
  }

  private onOrientation(e: DeviceOrientationEvent): void {
    if (e.beta == null || e.gamma == null) return;
    // Which way the phone is turned (top to the left = 90, to the right = -90), from gravity itself, so a
    // browser's screen-angle convention cannot invert the steering. Latched with hysteresis.
    const dx = Math.cos((e.beta * Math.PI) / 180) * Math.sin((e.gamma * Math.PI) / 180);
    if (this.side === 0 || Math.abs(dx) > 0.6) this.side = dx < 0 ? 90 : -90;
    const angle = this.side;
    const raw = tiltAngle(e.beta, e.gamma, angle);
    const now = performance.now();
    const dt = this.lastOrientT ? Math.min(0.2, (now - this.lastOrientT) / 1000) : 0;
    this.lastOrientT = now;
    if (!isFinite(this.tiltRaw) || dt === 0 || dt >= 0.2) this.tiltRaw = raw;
    else this.tiltRaw = this.tiltRaw + lowPass(0, wrapAngle(raw - this.tiltRaw), dt);
    this.tiltRaw = wrapAngle(this.tiltRaw);
    if (this.pendingRecentre) { this.tiltOffset = this.tiltRaw; this.pendingRecentre = false; }
    if (this.tilt !== 'active') {
      const before = this.tilt;
      this.tilt = tiltNext(this.tilt, 'reading');
      if (this.tilt !== before) this.changed();
    }
  }

  private rect(): DOMRect { return this.layer.getBoundingClientRect(); }

  private onDown(e: PointerEvent): void {
    if ((e.target as HTMLElement).closest?.('button')) return;
    if (e.pointerType === 'mouse' && e.button !== 0) return;
    e.preventDefault();
    const r = this.rect();
    const zone = hitZone(e.clientX - r.left, e.clientY - r.top, r.width, r.height, this.steerMode);
    this.ptrs.set(e.pointerId, { zone, x: e.clientX, y: e.clientY });
    try { this.layer.setPointerCapture(e.pointerId); } catch { /* synthetic */ }
    this.poke();
    this.recompute();
  }

  private onMove(e: PointerEvent): void {
    const p = this.ptrs.get(e.pointerId);
    if (!p) return;
    p.x = e.clientX; p.y = e.clientY;
    this.recompute();
  }

  private onUp(e: PointerEvent): void {
    if (!this.ptrs.delete(e.pointerId)) return;
    this.lastTouch = performance.now();
    this.recompute();
  }

  private recompute(): void {
    const r = this.rect();
    let brake = 0, throttle = 0;
    for (const p of this.ptrs.values()) {
      if (p.zone === 'brake') brake = Math.max(brake, pedalFromY(p.y, r.top, r.bottom));
      else if (p.zone === 'throttle') throttle = Math.max(throttle, pedalFromY(p.y, r.top, r.bottom));
      else if (p.zone === 'steer') this.sliderTarget = sliderSteer(p.x, r.left + r.width / 3, r.left + (2 * r.width) / 3);
    }
    this.brake = brake; this.throttle = throttle;
    this.layer.classList.toggle('idle', this.ptrs.size === 0 && performance.now() - this.lastTouch > IDLE_MS);
  }

  private poke(): void {
    this.lastTouch = performance.now();
    this.layer.classList.remove('idle');
  }

  private lastDrawn = '';
  private draw(): void {
    if (this.ptrs.size === 0 && performance.now() - this.lastTouch > IDLE_MS) this.layer.classList.add('idle');
    const s = this.steer;
    const key = `${this.brake.toFixed(3)}|${this.throttle.toFixed(3)}|${s.toFixed(3)}`;
    if (key === this.lastDrawn) return;
    this.lastDrawn = key;
    this.brakeFill.style.transform = `scaleY(${this.brake.toFixed(3)})`;
    this.throttleFill.style.transform = `scaleY(${this.throttle.toFixed(3)})`;
    // knob: + steer = left
    const pos = 50 - s * 50;
    this.steerKnob.style.left = `${pos.toFixed(2)}%`;
    this.steerFill.style.left = `${Math.min(50, pos).toFixed(2)}%`;
    this.steerFill.style.width = `${Math.abs(s * 50).toFixed(2)}%`;
  }
}
