// Control bindings, calibration and response curves (pure logic, no DOM).
// Used by input.ts (runtime) and controls-panel.ts (UI); unit-tested.
import { axisGlyph, buttonGlyph, type PadKind } from './glyphs';

export type AnalogId = 'steer' | 'throttle' | 'brake';
export type DigitalId = 'shiftUp' | 'shiftDown' | 'handbrake' | 'camera' | 'reset' | 'autoShift';
export type ControlId = AnalogId | DigitalId;
/** Held keys that turn the camera (keyboard only; the pad looks with the stick not used for steering). */
export type LookKeyId = 'lookLeft' | 'lookRight' | 'lookBack';
export type KeyId = 'steerLeft' | 'steerRight' | 'throttle' | 'brake' | DigitalId | LookKeyId;

export const ANALOG_IDS: AnalogId[] = ['steer', 'throttle', 'brake'];
export const DIGITAL_IDS: DigitalId[] = ['shiftUp', 'shiftDown', 'handbrake', 'camera', 'reset', 'autoShift'];
export const CONTROL_IDS: ControlId[] = [...ANALOG_IDS, ...DIGITAL_IDS];
export const LOOK_KEY_IDS: LookKeyId[] = ['lookLeft', 'lookRight', 'lookBack'];
export const KEY_IDS: KeyId[] = ['steerLeft', 'steerRight', 'throttle', 'brake', ...DIGITAL_IDS, ...LOOK_KEY_IDS];

export const CONTROL_LABELS: Record<ControlId, string> = {
  steer: 'Steer', throttle: 'Throttle', brake: 'Brake', shiftUp: 'Shift up', shiftDown: 'Shift down',
  handbrake: 'Handbrake', camera: 'Cycle camera', reset: 'Reset to start line', autoShift: 'Auto-shift on/off',
};
export const KEY_LABELS: Record<KeyId, string> = {
  steerLeft: 'Steer left', steerRight: 'Steer right', throttle: 'Throttle', brake: 'Brake',
  shiftUp: 'Shift up', shiftDown: 'Shift down', handbrake: 'Handbrake', camera: 'Cycle camera',
  reset: 'Reset to start line', autoShift: 'Auto-shift on/off',
  lookLeft: 'Look left', lookRight: 'Look right', lookBack: 'Look back',
};

/** Keys that are fixed (not remappable): pause menu, mute, help, controls panel. */
export const FIXED_KEYS: Record<string, 'menu' | 'mute' | 'help' | 'controls'> = {
  Escape: 'menu', KeyO: 'menu', KeyM: 'mute', KeyH: 'help', KeyK: 'controls',
};

/** Standard-mapping Start: opens / closes the pause menu; never bindable. */
export const RESERVED_PAD_BUTTONS: readonly number[] = [9];

export type PadSource =
  | { kind: 'button'; index: number }
  | { kind: 'axis'; index: number; sign: 1 | -1 }  // raw = sign * axis
  | { kind: 'auto' }                                // pedals: standard trigger button, analog-detected, axis fallback
  | { kind: 'none' };

export interface Calibration {
  /** Raw value at rest (pedals) / full right (steer, negative). */
  min: number;
  /** Raw value at full travel (pedals) / full left (steer). */
  max: number;
  deadzone: number;   // 0..0.5 of normalised travel
  invert: boolean;
  expo: number;       // response exponent 0.5..2.5 (1 = linear)
}

export interface PadProfile {
  pad: Record<ControlId, PadSource>;
  cal: Record<AnalogId, Calibration>;
}
export type KeyBindings = Record<KeyId, string[]>;

export function defaultPadProfile(): PadProfile {
  return {
    pad: {
      steer: { kind: 'axis', index: 0, sign: -1 },  // stick left (−1) = steer left (+1)
      throttle: { kind: 'auto' },
      brake: { kind: 'auto' },
      shiftUp: { kind: 'button', index: 5 },    // RB paddle
      shiftDown: { kind: 'button', index: 4 },  // LB paddle
      handbrake: { kind: 'button', index: 1 },  // B
      camera: { kind: 'button', index: 3 },     // Y
      reset: { kind: 'button', index: 8 },      // Back / View
      autoShift: { kind: 'button', index: 2 },  // X
      // A (0) is free while driving (menu select); Start (9) is the pause menu.
    },
    cal: {
      steer: { min: -1, max: 1, deadzone: 0.08, invert: false, expo: 1.3 },
      throttle: { min: 0, max: 1, deadzone: 0.03, invert: false, expo: 1.0 },
      brake: { min: 0, max: 1, deadzone: 0.03, invert: false, expo: 1.4 },
    },
  };
}

export function defaultKeyBindings(): KeyBindings {
  return {
    steerLeft: ['ArrowLeft', 'KeyA'], steerRight: ['ArrowRight', 'KeyD'],
    throttle: ['ArrowUp', 'KeyW'], brake: ['ArrowDown', 'KeyS'],
    shiftUp: ['KeyE', 'ShiftLeft', 'ShiftRight'], shiftDown: ['KeyQ'], handbrake: ['Space'],
    camera: ['KeyC'], reset: ['KeyR'], autoShift: ['KeyT'],
    lookLeft: ['Comma'], lookRight: ['Period'], lookBack: ['Backspace'],
  };
}

// ---------------------------------------------------------------- response

const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));

/** Deadzone + exponent on a 0..1 magnitude. */
export function shape(u: number, deadzone: number, expo: number): number {
  const a = clamp(u, 0, 1);
  const dz = clamp(deadzone, 0, 0.9);
  if (a <= dz) return 0;
  const n = (a - dz) / (1 - dz);
  return Math.pow(n, clamp(expo, 0.5, 2.5));
}

/** Steering: raw (sign already applied, + = left) to −1..1. */
export function applySteer(raw: number, c: Calibration): number {
  const maxL = c.max > 0.05 ? c.max : 1;
  const maxR = c.min < -0.05 ? -c.min : 1;
  const u = raw >= 0 ? raw / maxL : raw / maxR;
  const s = Math.sign(u) * shape(Math.abs(u), c.deadzone, c.expo);
  return clamp(c.invert ? -s : s, -1, 1);
}

/** Pedal: raw to 0..1 using min (rest) and max (full). */
export function applyPedal(raw: number, c: Calibration): number {
  const span = c.max - c.min;
  let u = Math.abs(span) < 1e-3 ? clamp(raw, 0, 1) : (raw - c.min) / span;
  u = clamp(u, 0, 1);
  if (c.invert) u = 1 - u;
  return shape(u, c.deadzone, c.expo);
}

// ---------------------------------------------------------------- analog evidence

/**
 * Remembers, per raw source ('b6', 'a2'), whether it has ever reported an
 * intermediate value (it is analog) and whether it has been seen at rest
 * (armed). A trigger that reads fully pressed from the first sample is not
 * trusted until it is released once (stale reports on some OS/browser combos).
 */
export class SourceTracker {
  private fractional = new Set<string>();
  private armed = new Set<string>();
  private lastVal = new Map<string, number>();

  /** v: value in 0..1 (pedal-normalised). */
  observe(key: string, v: number): void {
    if (v > 0.02 && v < 0.98) this.fractional.add(key);
    if (v < 0.1) this.armed.add(key);
    this.lastVal.set(key, v);
  }
  isAnalog(key: string): boolean { return this.fractional.has(key); }
  isArmed(key: string): boolean { return this.armed.has(key); }
  reset(): void { this.fractional.clear(); this.armed.clear(); this.lastVal.clear(); }
}

/** Trigger pressure from an axis: −1..1 resting at −1, or 0..1 resting at 0. */
export function triggerAxisToPedal(a: number, restsAtMinusOne: boolean): number {
  return restsAtMinusOne ? clamp((a + 1) / 2, 0, 1) : clamp(a, 0, 1);
}

// ---------------------------------------------------------------- labels

/** Button label for the controller family; verbose adds the raw index ("RB (b5)") for the controls panel. */
export function buttonName(i: number, kind: PadKind = 'xbox', verbose = false): string {
  const g = buttonGlyph(kind, i);
  return verbose && kind !== 'generic' ? `${g} (b${i})` : g;
}
export function axisName(i: number, kind: PadKind = 'xbox', verbose = false): string {
  const g = axisGlyph(kind, i);
  return verbose && kind !== 'generic' ? `${g} (a${i})` : g;
}

export function describePad(id: ControlId, s: PadSource, kind: PadKind = 'xbox', verbose = false): string {
  switch (s.kind) {
    case 'none': return '–';
    case 'auto': {
      const b = id === 'throttle' ? 7 : id === 'brake' ? 6 : -1;
      return b < 0 ? 'auto' : verbose ? `${buttonGlyph(kind, b)} (auto)` : buttonGlyph(kind, b);
    }
    case 'button': return buttonName(s.index, kind, verbose);
    case 'axis': {
      const dir = id === 'steer' ? '' : s.sign > 0 ? ' +' : ' −';
      return axisName(s.index, kind, verbose) + dir;
    }
  }
}

const KEY_NAMES: Record<string, string> = {
  ArrowLeft: '←', ArrowRight: '→', ArrowUp: '↑', ArrowDown: '↓', Space: 'Space',
  ShiftLeft: 'Shift', ShiftRight: 'R-Shift', ControlLeft: 'Ctrl', ControlRight: 'R-Ctrl',
  AltLeft: 'Alt', AltRight: 'R-Alt', Enter: 'Enter', Escape: 'Esc', Backspace: 'Backspace', Tab: 'Tab',
  Comma: ',', Period: '.', Slash: '/', BracketLeft: '[', BracketRight: ']', Semicolon: ';', Quote: "'", Backquote: '`',
};
export function keyName(code: string): string {
  if (KEY_NAMES[code]) return KEY_NAMES[code];
  if (code.startsWith('Key')) return code.slice(3);
  if (code.startsWith('Digit')) return code.slice(5);
  return code;
}
export function describeKeys(codes: string[]): string {
  const names: string[] = [];
  for (const c of codes) { const n = keyName(c); if (!names.includes(n.replace('R-', ''))) names.push(n); }
  return names.length ? names.join(' / ') : '–';
}

/** Rows for the help overlay: [action, gamepad, keyboard]. */
export function helpRows(p: PadProfile, k: KeyBindings, kind: PadKind = 'xbox'): [string, string, string][] {
  const d = (id: ControlId) => describePad(id, p.pad[id], kind);
  return [
    ['Steer', d('steer'), `${describeKeys(k.steerLeft)} | ${describeKeys(k.steerRight)}`],
    ['Throttle', d('throttle'), describeKeys(k.throttle)],
    ['Brake', d('brake'), describeKeys(k.brake)],
    ...DIGITAL_IDS.map((id): [string, string, string] => [CONTROL_LABELS[id], d(id), describeKeys(k[id])]),
    ['Look around', lookStickName(p, kind), `${describeKeys(k.lookLeft)} | ${describeKeys(k.lookRight)} · mouse drag`],
    ['Look back', lookBackGlyph(p, kind), describeKeys(k.lookBack)],
    ['Pause menu', buttonGlyph(kind, 9), 'Esc'],
    ['Mute', '–', 'M'],
    ['Controls / calibration', '–', 'K'],
    ['This help', '–', 'H'],
  ];
}

// ---------------------------------------------------------------- look stick

/** Pad axes the look stick reads: the stick not used for steering (standard mapping: right stick 2/3, or the
 *  left stick 0/1 when steering is on the right stick). null when a binding already uses one of its axes
 *  (e.g. throttle on the right stick's Y), so looking never fights a pedal. */
export function lookStickAxes(p: PadProfile): [number, number] | null {
  const s = p.pad.steer;
  const pair: [number, number] = s.kind === 'axis' && (s.index === 2 || s.index === 3) ? [0, 1] : [2, 3];
  for (const id of CONTROL_IDS) {
    const b = p.pad[id];
    if (b.kind === 'axis' && pair.includes(b.index)) return null;
  }
  return pair;
}

/** Look-back button on the pad: the look stick's click (R3 / L3), unless a control is bound to it. */
export function lookBackButton(p: PadProfile): number | null {
  const axes = lookStickAxes(p);
  if (!axes) return null;
  const b = axes[0] === 2 ? 11 : 10;
  for (const id of CONTROL_IDS) { const s = p.pad[id]; if (s.kind === 'button' && s.index === b) return null; }
  return b;
}

export function lookStickName(p: PadProfile, kind: PadKind = 'xbox'): string {
  const a = lookStickAxes(p);
  if (!a) return '–';
  if (kind === 'generic') return `Axes ${a[0]}/${a[1]}`;
  return a[0] === 2 ? 'Right stick' : 'Left stick';
}
export function lookBackGlyph(p: PadProfile, kind: PadKind = 'xbox'): string {
  const b = lookBackButton(p);
  return b == null ? '–' : buttonGlyph(kind, b);
}

export const LOOK_DEADZONE = 0.15;
export const LOOK_EXPO = 1.6;
/** Stick deflection beyond which "hold full look" latches the look. */
export const LOOK_LATCH = 0.95;

/** Radial deadzone + expo on a stick: raw axes (x right +, y down +) to look (x + = left, y + = up), magnitude ≤ 1. */
export function shapeLook(ax: number, ay: number, deadzone = LOOK_DEADZONE, expo = LOOK_EXPO): [number, number] {
  const m = Math.hypot(ax, ay);
  if (m <= deadzone || m === 0) return [0, 0];
  const s = shape(Math.min(1, m), deadzone, expo) / m;
  return [-ax * s, -ay * s];
}

/**
 * "Hold full look" (look over the shoulder): once the stick goes past LOOK_LATCH the look stays at that full
 * deflection when the stick is let go, until the stick is centred and then moved again.
 */
export class LookLatch {
  private held: [number, number] | null = null;
  private centred = false;
  /** raw: stick deflection magnitude 0..1 before shaping; look: shaped look vector. */
  update(raw: number, look: [number, number], enabled: boolean): [number, number] {
    if (!enabled) { this.held = null; return look; }
    if (raw >= LOOK_LATCH) {
      const m = Math.hypot(look[0], look[1]) || 1;
      this.held = [look[0] / m, look[1] / m];
      this.centred = false;
      return look;
    }
    if (!this.held) return look;
    if (raw <= LOOK_DEADZONE) { this.centred = true; return this.held; }
    if (this.centred) { this.held = null; return look; } // moved again after centring: release
    return this.held;                                     // still on its way back from the latch
  }
  get latched(): boolean { return !!this.held; }
  clear(): void { this.held = null; }
}

// ---------------------------------------------------------------- persistence

const NS = 'probeSim.controls.v1';
/** Saved pad-profile format. 2: paddle shifting, Start reserved for the pause menu (Oct 2026). */
export const PAD_PROFILE_VERSION = 2;
/** Digital defaults before version 2, for migrating saved profiles. */
const V1_DIGITAL: Record<DigitalId, number> = { shiftUp: 0, shiftDown: 2, handbrake: 1, camera: 3, reset: 8, autoShift: 9 };

function storageGet(key: string): string | null {
  try { return window.localStorage.getItem(key); } catch { return null; }
}
function storageSet(key: string, v: string | null): void {
  try { if (v == null) window.localStorage.removeItem(key); else window.localStorage.setItem(key, v); } catch { /* storage unavailable */ }
}

function validSource(s: unknown, analogOnly: boolean): PadSource | null {
  if (!s || typeof s !== 'object') return null;
  const o = s as Record<string, unknown>;
  if (o.kind === 'none' || o.kind === 'auto') return analogOnly && o.kind === 'auto' ? null : { kind: o.kind } as PadSource;
  const idx = typeof o.index === 'number' && o.index >= 0 && o.index < 64 ? Math.floor(o.index) : -1;
  if (idx < 0) return null;
  if (o.kind === 'button') return analogOnly || RESERVED_PAD_BUTTONS.includes(idx) ? null : { kind: 'button', index: idx };
  if (o.kind === 'axis') return { kind: 'axis', index: idx, sign: o.sign === 1 ? 1 : -1 };
  return null;
}

function validCal(c: unknown, d: Calibration): Calibration {
  if (!c || typeof c !== 'object') return { ...d };
  const o = c as Record<string, unknown>;
  const n = (v: unknown, def: number, lo: number, hi: number) => (typeof v === 'number' && isFinite(v) ? clamp(v, lo, hi) : def);
  return {
    min: n(o.min, d.min, -1, 1), max: n(o.max, d.max, -1, 1),
    deadzone: n(o.deadzone, d.deadzone, 0, 0.5), invert: typeof o.invert === 'boolean' ? o.invert : d.invert,
    expo: n(o.expo, d.expo, 0.5, 2.5),
  };
}

export interface ParsedPadProfile {
  profile: PadProfile;
  /** True when an older saved profile was converted (save it back and tell the player once). */
  migrated: boolean;
}

/**
 * Parse a saved profile. Version 1 profiles (no `v`) are migrated: buttons
 * still on the old defaults move to the new ones, custom buttons are kept, and
 * if that leaves two digital controls on one button (or one on Start) all
 * digital buttons go back to the new defaults. Calibration is always kept.
 */
export function readPadProfile(json: string | null): ParsedPadProfile {
  const d = defaultPadProfile();
  if (!json) return { profile: d, migrated: false };
  let o: Record<string, any>;
  try { o = JSON.parse(json); } catch { return { profile: d, migrated: false }; }
  if (!o || typeof o !== 'object') return { profile: d, migrated: false };
  const old = !(typeof o.v === 'number' && o.v >= PAD_PROFILE_VERSION);
  for (const id of CONTROL_IDS) {
    const raw = o.pad?.[id];
    if (old && DIGITAL_IDS.includes(id as DigitalId) && raw?.kind === 'button' && raw.index === V1_DIGITAL[id as DigitalId]) continue; // old default → new default
    const s = validSource(raw, id === 'steer');
    if (s && !(s.kind === 'auto' && id !== 'throttle' && id !== 'brake')) d.pad[id] = s;
  }
  if (old) {
    const used = new Set<number>();
    let clash = false;
    for (const id of DIGITAL_IDS) {
      const s = d.pad[id];
      if (s.kind !== 'button') continue;
      if (used.has(s.index)) clash = true;
      used.add(s.index);
    }
    if (clash) { const nd = defaultPadProfile(); for (const id of DIGITAL_IDS) d.pad[id] = nd.pad[id]; }
  }
  for (const id of ANALOG_IDS) d.cal[id] = validCal(o.cal?.[id], d.cal[id]);
  return { profile: d, migrated: old };
}

export function parsePadProfile(json: string | null): PadProfile { return readPadProfile(json).profile; }

export function parseKeyBindings(json: string | null): KeyBindings {
  const d = defaultKeyBindings();
  if (!json) return d;
  try {
    const o = JSON.parse(json);
    for (const id of KEY_IDS) {
      const v = o?.[id];
      if (Array.isArray(v) && v.every((x) => typeof x === 'string') && v.length <= 4) d[id] = v.filter((x) => !(x in FIXED_KEYS));
    }
  } catch { /* defaults */ }
  return d;
}

/** Load the saved profile for a pad; a migrated profile is saved back so the notice shows once. */
export function loadPadProfile(padId: string): ParsedPadProfile {
  const r = readPadProfile(storageGet(`${NS}.pad:${padId}`));
  if (r.migrated) savePadProfile(padId, r.profile);
  return r;
}
export function serializePadProfile(p: PadProfile): string { return JSON.stringify({ v: PAD_PROFILE_VERSION, ...p }); }
export function savePadProfile(padId: string, p: PadProfile): void { storageSet(`${NS}.pad:${padId}`, serializePadProfile(p)); }
export function clearPadProfile(padId: string): void { storageSet(`${NS}.pad:${padId}`, null); }
/** "Hold full look" for the look stick (input.ts); default off = spring back. */
export function loadLookHold(): boolean { return storageGet(`${NS}.lookHold`) === '1'; }
export function saveLookHold(on: boolean): void { storageSet(`${NS}.lookHold`, on ? '1' : null); }
export function loadKeyBindings(): KeyBindings { return parseKeyBindings(storageGet(`${NS}.keys`)); }
export function saveKeyBindings(k: KeyBindings): void { storageSet(`${NS}.keys`, JSON.stringify(k)); }
export function clearKeyBindings(): void { storageSet(`${NS}.keys`, null); }
