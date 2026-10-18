// Controller kind detection and button / axis labels per controller family.
// Pure (no DOM); unit-tested in __tests__/glyphs.test.ts.
//
// Indices follow the W3C "standard" gamepad mapping: 0 bottom face button,
// 1 right, 2 left, 3 top, 4/5 bumpers, 6/7 triggers, 8 back/select, 9 start,
// 10/11 stick clicks, 12–15 d-pad up/down/left/right, 16 home.

export type PadKind = 'xbox' | 'playstation' | 'nintendo' | 'generic';

/** Guess the controller family from Gamepad.id (vendor id or product words). */
export function detectPadKind(id: string | null | undefined): PadKind {
  if (!id) return 'generic';
  const s = id.toLowerCase();
  // Chrome: "... (STANDARD GAMEPAD Vendor: 045e Product: 028e)"; Firefox: "045e-028e-..."
  const m = /vendor:\s*([0-9a-f]{4})/.exec(s) ?? /^([0-9a-f]{4})-[0-9a-f]{4}-/.exec(s);
  const vendor = m?.[1];
  if (vendor === '045e' || /xbox|xinput/.test(s)) return 'xbox';
  if (vendor === '054c' || /playstation|dualshock|dualsense|ps[345] controller/.test(s)) return 'playstation';
  if (vendor === '057e' || /pro controller|joy-con|nintendo|switch/.test(s)) return 'nintendo';
  return 'generic';
}

const DPAD = ['D-pad ↑', 'D-pad ↓', 'D-pad ←', 'D-pad →'];

const BUTTONS: Record<Exclude<PadKind, 'generic'>, string[]> = {
  xbox: ['A', 'B', 'X', 'Y', 'LB', 'RB', 'LT', 'RT', 'Back', 'Start', 'LS', 'RS', ...DPAD, 'Guide'],
  playstation: ['✕', '○', '□', '△', 'L1', 'R1', 'L2', 'R2', 'Share', 'Options', 'L3', 'R3', ...DPAD, 'PS'],
  // Nintendo: the bottom face button (standard index 0) is labelled B, the right one A.
  nintendo: ['B', 'A', 'Y', 'X', 'L', 'R', 'ZL', 'ZR', '−', '+', 'L-stick', 'R-stick', ...DPAD, 'Home'],
};

const AXES = ['Left stick X', 'Left stick Y', 'Right stick X', 'Right stick Y'];

/** Short label for a standard-mapping button, e.g. "RB", "R1", "ZR", "Button 5". */
export function buttonGlyph(kind: PadKind, index: number): string {
  if (kind === 'generic') return `Button ${index}`;
  return BUTTONS[kind][index] ?? `Button ${index}`;
}

/** Label for an axis. */
export function axisGlyph(kind: PadKind, index: number): string {
  return kind !== 'generic' && AXES[index] ? AXES[index] : `Axis ${index}`;
}

/** Display name of the family, for the controls panel header. */
export const PAD_KIND_NAMES: Record<PadKind, string> = {
  xbox: 'Xbox controller', playstation: 'PlayStation controller', nintendo: 'Nintendo controller', generic: 'Gamepad',
};

/** Standard-mapping buttons the menu uses (not remappable). */
export const MENU_BUTTONS = { select: 0, back: 1, menu: 9, up: 12, down: 13, left: 14, right: 15 } as const;
