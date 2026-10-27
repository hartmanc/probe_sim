// Start menu → How to play: the controls (the player's current bindings), the modes, the scoreboard, the phone field.
import type { MenuEntry, MenuPage } from './menu';
import { LIMITS } from '../scoreboard/config';
import { MOBILE_FIELD } from './field-select';

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

/** The sections as text (pure; unit-tested). */
export function howtoSections(o: { raceLaps: number; touch: boolean; fieldLine: string | null }): { title: string; lines: string[] }[] {
  return [
    { title: 'The car', lines: [
      'You drive car #619, a 1993 Ford Probe GT that races in the 24 Hours of Lemons, front-wheel drive with a five-speed. The physics model tyres, weight transfer and an open differential: brake in a straight line, turn in gently and feed the throttle on the way out.',
    ] },
    { title: 'Controls', lines: [
      o.touch ? 'Phone or tablet: hold it sideways. Left third of the screen brakes, right third accelerates, higher on the screen = harder. Steer by tilting (or the slider, in Touch controls). A pad paired with the device also works.'
        : 'An Xbox / PlayStation pad (analog steering and pedals) or the keyboard. The table below is your current setup; Controls & calibration (K) remaps keys and buttons and calibrates a pad or a wheel.',
      'Auto-shift is on by default (pause menu); with it off, shift up and down yourself. ABS is the crude 1993 kind.',
    ] },
    { title: 'Modes', lines: [
      `Hot lap: a rolling start, then lap after lap against the team's logged ghosts. Off track with all four wheels for more than 2 s makes the lap invalid. R resets to the start. Ghost & delta (Start or pause menu) picks the lap the ghost car and the delta timer follow: your session best, the scoreboard's all-time best, or the team's real lap (Laguna only).`,
      `Race: ${o.raceLaps} laps against the real field of a 2026 Lemons race on that track, each car with the pace its drivers ran there. Black flags, as at a real Lemons race, for four wheels off, for contact you cause, for passing under yellow and for crossing the pit-exit cones; a stop-and-go in the pit lane serves them. Hit a wall hard and you are out.`,
      o.fieldLine ? `On phones and tablets the race is the ${MOBILE_FIELD} cars whose real pace is closest to the Probe's (${o.fieldLine}); a computer races the whole field.` : `On phones and tablets the race is the ${MOBILE_FIELD} cars whose real pace is closest to the Probe's; a computer races the whole field.`,
    ] },
    { title: 'Scoreboard', lines: [
      `Hot-lap boards, one per track. A valid lap that beats your best (laps 1–${LIMITS.maxLap} after a reset) offers to post; the server re-runs your inputs through the same physics and stores the time it gets, so only real laps count.`,
      'Your first post claims your name for this device. To post as the same name on another device, open Scoreboard → Transfer code here and type the code in Scoreboard → Use a transfer code there.',
      'Race boards come back once races can be checked the same way.',
    ] },
  ];
}

export function howtoPage(o: { rows(): [string, string, string][]; touch: boolean; fieldLine(): string | null; raceLaps: number }): MenuPage {
  const box = el('div', 'credits howto');
  box.tabIndex = -1;
  const render = () => {
    const parts: HTMLElement[] = [];
    for (const s of howtoSections({ raceLaps: o.raceLaps, touch: o.touch, fieldLine: o.fieldLine() })) {
      const sec = el('section', 'cr-section');
      sec.append(el('h3', 'cr-h', s.title));
      for (const l of s.lines) sec.append(el('div', 'cr-intro', l));
      if (s.title === 'Controls' && !o.touch) {
        const t = el('table', 'ht-table');
        const head = el('tr');
        head.append(el('th', undefined, ''), el('th', undefined, 'Pad'), el('th', undefined, 'Keyboard'));
        t.append(head);
        for (const [a, pad, keys] of o.rows()) { const tr = el('tr'); tr.append(el('td', undefined, a), el('td', undefined, pad), el('td', undefined, keys)); t.append(tr); }
        sec.append(t);
      }
      parts.push(sec);
    }
    box.replaceChildren(...parts);
  };
  render();
  return {
    title: 'How to play',
    body: () => box,
    entries: (): MenuEntry[] => [{ kind: 'back', id: 'back', label: 'Back' }],
  };
}
