// Controls panel (K): live gamepad readout, remap by pressing, calibration
// (range capture, deadzone, invert, response curve), test strip, defaults.
import type { Input } from './input';
import {
  ANALOG_IDS, CONTROL_IDS, CONTROL_LABELS, KEY_IDS, KEY_LABELS, LOOK_KEY_IDS, axisName, buttonName, describeKeys, keyName, lookBackGlyph,
  lookStickName, shape, type AnalogId, type ControlId, type KeyId, type LookKeyId,
} from './controls';
import { PAD_KIND_NAMES, detectPadKind, type PadKind } from './glyphs';

const kindOf = (p: Gamepad): PadKind => (p.mapping === 'standard' ? detectPadKind(p.id) : 'generic');

function el<K extends keyof HTMLElementTagNameMap>(tag: K, cls?: string, text?: string): HTMLElementTagNameMap[K] {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

const PROMPTS: Partial<Record<ControlId, string>> = {
  steer: 'Move the steering stick fully LEFT…',
  throttle: 'Press the throttle control…',
  brake: 'Press the brake control…',
};

export class ControlsPanel {
  readonly root = el('div', 'controls-panel hidden');
  private timer = 0;
  private padInfo = el('div', 'cp-pad');
  private raw = el('div', 'cp-raw');
  private padCells = new Map<ControlId, HTMLSpanElement>();
  private keyCells = new Map<KeyId, HTMLSpanElement>();
  private lookPadCells = new Map<LookKeyId, HTMLSpanElement>();
  private msg = el('div', 'cp-msg');
  private test: { steer: HTMLDivElement; throttle: HTMLDivElement; brake: HTMLDivElement; vals: Record<AnalogId, HTMLSpanElement>; src: Record<'throttle' | 'brake', HTMLSpanElement> };
  private cal = new Map<AnalogId, { canvas: HTMLCanvasElement; range: HTMLSpanElement; dz: HTMLInputElement; dzv: HTMLSpanElement; inv: HTMLInputElement; ex: HTMLInputElement; exv: HTMLSpanElement; btn: HTMLButtonElement }>();
  private rawSig = '';
  private closeBtn: HTMLButtonElement;

  constructor(parent: HTMLElement, private input: Input, private onClose?: () => void) {
    parent.appendChild(this.root);
    const r = this.root;
    const head = el('div', 'cp-head');
    head.append(el('h2', '', 'Controls & calibration'), this.padInfo);
    const close = el('button', 'btn cp-close', 'Close (K)');
    close.addEventListener('click', () => this.close());
    this.closeBtn = close;
    head.append(close);
    r.append(head);

    // ---- test strip
    const strip = el('div', 'cp-section cp-test');
    strip.append(el('h3', '', 'Test'));
    const bar = (label: string, centred: boolean) => {
      const row = el('div', 'cp-bar-row');
      const b = el('div', 'cp-bar' + (centred ? ' centred' : ''));
      const fill = el('div', 'cp-fill');
      if (centred) b.append(el('div', 'cp-mid'));
      b.append(fill);
      const v = el('span', 'cp-val', '0.00');
      row.append(el('span', 'cp-lbl', label), b, v);
      strip.append(row);
      return { fill, v };
    };
    const s = bar('Steer', true), t = bar('Throttle', false), b = bar('Brake', false);
    const srcRow = el('div', 'cp-src');
    const ts = el('span'), bs = el('span');
    srcRow.append(el('span', '', 'Throttle source: '), ts, el('span', '', ' · Brake source: '), bs);
    strip.append(srcRow);
    this.test = { steer: s.fill, throttle: t.fill, brake: b.fill, vals: { steer: s.v, throttle: t.v, brake: b.v }, src: { throttle: ts, brake: bs } };
    r.append(strip);

    // ---- bindings
    const bind = el('div', 'cp-section');
    bind.append(el('h3', '', 'Bindings'), el('div', 'hint', 'Click Assign, then move or press the control. Esc cancels a keyboard assignment.'));
    const table = el('table', 'cp-table');
    const hr = el('tr'); hr.append(el('th', '', 'Action'), el('th', '', 'Gamepad'), el('th', '', ''), el('th', '', 'Keyboard'), el('th', '', ''));
    table.append(hr);
    const keyRowsFor = (id: ControlId): KeyId[] => (id === 'steer' ? ['steerLeft', 'steerRight'] : [id as KeyId]);
    for (const id of CONTROL_IDS) {
      const ks = keyRowsFor(id);
      ks.forEach((kid, k) => {
        const tr = el('tr');
        if (k === 0) {
          const name = el('td', '', CONTROL_LABELS[id]); name.rowSpan = ks.length;
          const padCell = el('span', 'cp-binding');
          this.padCells.set(id, padCell);
          const pc = el('td'); pc.rowSpan = ks.length; pc.append(padCell);
          const ab = el('button', 'btn small', 'Assign');
          ab.addEventListener('click', () => this.assignPad(id, ab));
          const ac = el('td'); ac.rowSpan = ks.length; ac.append(ab);
          tr.append(name, pc, ac);
        }
        const keyCell = el('span', 'cp-binding');
        this.keyCells.set(kid, keyCell);
        const kc = el('td');
        if (ks.length > 1) kc.append(el('span', 'cp-sub', kid === 'steerLeft' ? 'left ' : 'right '));
        kc.append(keyCell);
        const kb = el('button', 'btn small', 'Assign');
        kb.addEventListener('click', () => this.assignKey(kid, kb));
        const kbc = el('td'); kbc.append(kb);
        tr.append(kc, kbc);
        table.append(tr);
      });
    }
    // look-around: keys remappable; the pad uses the stick not used for steering and its click (not assignable)
    for (const kid of LOOK_KEY_IDS) {
      const tr = el('tr');
      const padCell = el('span', 'cp-binding');
      this.lookPadCells.set(kid, padCell);
      const pc = el('td'); pc.append(padCell);
      const keyCell = el('span', 'cp-binding');
      this.keyCells.set(kid, keyCell);
      const kc = el('td'); kc.append(keyCell);
      const kb = el('button', 'btn small', 'Assign');
      kb.addEventListener('click', () => this.assignKey(kid, kb));
      const kbc = el('td'); kbc.append(kb);
      tr.append(el('td', '', KEY_LABELS[kid]), pc, el('td'), kc, kbc);
      table.append(tr);
    }
    bind.append(table, this.msg);
    r.append(bind);

    // ---- calibration
    const calSec = el('div', 'cp-section');
    calSec.append(el('h3', '', 'Calibration & response'));
    const grid = el('div', 'cp-cal-grid');
    for (const id of ANALOG_IDS) {
      const card = el('div', 'cp-cal');
      card.append(el('h4', '', CONTROL_LABELS[id]));
      const canvas = el('canvas', 'cp-curve'); canvas.width = 180; canvas.height = 120;
      card.append(canvas);
      const range = el('span', 'cp-range');
      const btn = el('button', 'btn small', 'Capture range (4 s)');
      btn.addEventListener('click', () => this.calibrate(id, btn));
      const rr = el('div', 'cp-row'); rr.append(btn, range);
      card.append(rr, el('div', 'hint', id === 'steer' ? 'Move the stick fully left and right.' : 'Press fully and release, a few times.'));
      const slider = (label: string, min: number, max: number, step: number) => {
        const row = el('label', 'cp-row');
        const inp = el('input'); inp.type = 'range'; inp.min = String(min); inp.max = String(max); inp.step = String(step);
        const v = el('span', 'cp-val');
        row.append(el('span', 'cp-lbl', label), inp, v);
        card.append(row);
        return { inp, v };
      };
      const dz = slider('Deadzone', 0, 0.3, 0.01);
      const ex = slider('Curve', 0.5, 2.5, 0.05);
      const invRow = el('label', 'cp-row');
      const inv = el('input'); inv.type = 'checkbox';
      invRow.append(inv, el('span', '', 'Invert'));
      card.append(invRow);
      dz.inp.addEventListener('input', () => this.input.setCal(id, { deadzone: Number(dz.inp.value) }));
      ex.inp.addEventListener('input', () => this.input.setCal(id, { expo: Number(ex.inp.value) }));
      inv.addEventListener('change', () => this.input.setCal(id, { invert: inv.checked }));
      this.cal.set(id, { canvas, range, dz: dz.inp, dzv: dz.v, inv, ex: ex.inp, exv: ex.v, btn });
      grid.append(card);
    }
    calSec.append(grid);
    r.append(calSec);

    // ---- raw readout
    const rawSec = el('div', 'cp-section');
    rawSec.append(el('h3', '', 'Raw gamepad readout'), el('div', 'hint', 'What the browser reports, 30 times a second. If a trigger shows only 0 or 1, it is digital.'), this.raw);
    r.append(rawSec);

    const reset = el('button', 'btn', 'Reset to defaults');
    reset.addEventListener('click', () => { this.input.resetDefaults(); this.say('Bindings and calibration reset to defaults.'); });
    r.append(reset);

    input.onChange(() => this.refreshBindings());
    this.refreshBindings();
  }

  get isOpen(): boolean { return !this.root.classList.contains('hidden'); }

  toggle(): void { if (this.isOpen) this.close(); else this.open(); }

  open(): void {
    this.root.classList.remove('hidden');
    this.input.suspended = true;
    this.refreshBindings();
    clearInterval(this.timer);
    this.timer = window.setInterval(() => this.tick(), 33);
    this.tick();
  }

  close(): void {
    this.root.classList.add('hidden');
    this.input.cancelCapture();
    this.input.suspended = false;
    clearInterval(this.timer);
    this.onClose?.();
  }

  private say(t: string): void { this.msg.textContent = t; }

  private assignPad(id: ControlId, btn: HTMLButtonElement): void {
    btn.textContent = 'Waiting…';
    this.say(PROMPTS[id] ?? `Press the button for ${CONTROL_LABELS[id]}…`);
    this.input.beginPadCapture(id, (r) => {
      btn.textContent = 'Assign';
      this.say(r ? `${CONTROL_LABELS[id]} → ${r}` : 'Assignment cancelled (nothing moved).');
      this.refreshBindings();
    });
  }

  private assignKey(id: KeyId, btn: HTMLButtonElement): void {
    btn.textContent = 'Press a key…';
    btn.blur();
    this.say(`Press a key for ${KEY_LABELS[id]} (Esc, M, H, O, K are reserved; Esc cancels)…`);
    this.input.beginKeyCapture(id, (code) => {
      btn.textContent = 'Assign';
      this.say(code ? `${KEY_LABELS[id]} → ${keyName(code)}` : 'Assignment cancelled.');
      this.refreshBindings();
    });
  }

  private calibrate(id: AnalogId, btn: HTMLButtonElement): void {
    btn.disabled = true;
    this.say(`Capturing ${CONTROL_LABELS[id]} range…`);
    this.input.beginCalibration(id, (ok) => {
      btn.disabled = false;
      btn.textContent = 'Capture range (4 s)';
      this.say(ok ? `${CONTROL_LABELS[id]} range saved.` : `${CONTROL_LABELS[id]}: not enough movement, range unchanged.`);
      this.refreshBindings();
    });
  }

  private refreshBindings(): void {
    for (const id of CONTROL_IDS) this.padCells.get(id)!.textContent = this.input.describe(id, true);
    for (const id of KEY_IDS) this.keyCells.get(id)!.textContent = describeKeys(this.input.keys[id]);
    const k = this.input.glyphKind, p = this.input.profile;
    for (const id of LOOK_KEY_IDS) this.lookPadCells.get(id)!.textContent = id === 'lookBack' ? `${lookBackGlyph(p, k)} (held)` : `${lookStickName(p, k)} ${id === 'lookLeft' ? '←' : '→'}`;
    for (const id of ANALOG_IDS) {
      const c = this.input.profile.cal[id], ui = this.cal.get(id)!;
      ui.dz.value = String(c.deadzone); ui.dzv.textContent = c.deadzone.toFixed(2);
      ui.ex.value = String(c.expo); ui.exv.textContent = c.expo.toFixed(2);
      ui.inv.checked = c.invert;
      ui.range.textContent = `min ${c.min.toFixed(2)} · max ${c.max.toFixed(2)}`;
    }
    const n = navigator.getGamepads ? [...navigator.getGamepads()].filter((p) => p && p.connected).length : 0;
    const kind = this.input.padKind;
    this.padInfo.textContent = this.input.padId
      ? `${kind ? PAD_KIND_NAMES[kind] + ' · ' : ''}${this.input.padId}${n > 1 ? ` (+${n - 1} more)` : ''} · settings saved for this controller · Start is reserved for the pause menu`
      : 'No gamepad detected: press any button on the controller.';
    this.closeBtn.textContent = this.input.padId ? `Close (K · ${this.input.glyph('back')})` : 'Close (K)';
  }

  private drawCurve(id: AnalogId): void {
    const ui = this.cal.get(id)!;
    const c = this.input.profile.cal[id];
    const g = ui.canvas.getContext('2d');
    if (!g) return;
    const W = ui.canvas.width, H = ui.canvas.height, P = 8;
    g.clearRect(0, 0, W, H);
    g.strokeStyle = 'rgba(255,255,255,0.15)'; g.lineWidth = 1;
    g.strokeRect(P, P, W - 2 * P, H - 2 * P);
    g.beginPath(); g.moveTo(P, H - P); g.lineTo(W - P, P); g.setLineDash([3, 3]); g.stroke(); g.setLineDash([]);
    g.strokeStyle = '#f2c230'; g.lineWidth = 2; g.beginPath();
    for (let k = 0; k <= 60; k++) {
      const u = k / 60, y = shape(u, c.deadzone, c.expo);
      const px = P + u * (W - 2 * P), py = H - P - y * (H - 2 * P);
      if (k) g.lineTo(px, py); else g.moveTo(px, py);
    }
    g.stroke();
    // live marker: current input magnitude
    let u: number, out: number;
    if (id === 'steer') {
      const raw = this.input.steerRaw;
      const m = raw >= 0 ? (c.max > 0.05 ? c.max : 1) : (c.min < -0.05 ? -c.min : 1);
      u = Math.min(1, Math.abs(raw) / m); out = Math.abs(this.input.padSteer);
    } else {
      const st = this.input.pedal[id];
      const span = c.max - c.min;
      u = Math.abs(span) > 1e-3 ? Math.max(0, Math.min(1, (st.raw - c.min) / span)) : st.raw;
      if (c.invert) u = 1 - u;
      out = st.value;
    }
    g.fillStyle = '#7fd1ff';
    g.beginPath(); g.arc(P + u * (W - 2 * P), H - P - out * (H - 2 * P), 4, 0, Math.PI * 2); g.fill();
    const cb = this.input.calibrating();
    ui.btn.textContent = cb && cb.id === id ? `Capturing… ${(cb.lo).toFixed(2)}…${(cb.hi).toFixed(2)}` : ui.btn.disabled ? 'Capturing…' : 'Capture range (4 s)';
  }

  private tick(): void {
    const inp = this.input;
    // test strip (combined keyboard + gamepad result)
    const st = Math.max(-1, Math.min(1, inp.steer));
    const w = Math.abs(st) * 50;
    this.test.steer.style.left = st >= 0 ? `${50 - w}%` : '50%'; // steer + = left: bar grows left
    this.test.steer.style.width = `${w}%`;
    this.test.throttle.style.width = `${inp.throttle * 100}%`;
    this.test.brake.style.width = `${inp.brake * 100}%`;
    this.test.vals.steer.textContent = (Math.abs(st) < 0.005 ? '' : st > 0 ? 'L ' : 'R ') + Math.abs(st).toFixed(2);
    this.test.vals.throttle.textContent = inp.throttle.toFixed(2);
    this.test.vals.brake.textContent = inp.brake.toFixed(2);
    for (const id of ['throttle', 'brake'] as const) {
      const p = inp.pedal[id];
      this.test.src[id].textContent = `${p.source} · ${!p.armed ? 'waiting for release' : p.analog ? 'analog' : 'digital → ramped'} · raw ${p.raw.toFixed(3)}`;
    }
    for (const id of ANALOG_IDS) this.drawCurve(id);
    this.renderRaw();
  }

  private renderRaw(): void {
    const pads = navigator.getGamepads ? [...navigator.getGamepads()].filter((p): p is Gamepad => !!p && p.connected) : [];
    const sig = pads.map((p) => `${p.index}:${p.axes.length}:${p.buttons.length}`).join('|');
    if (sig !== this.rawSig) {
      this.rawSig = sig;
      this.raw.replaceChildren();
      if (!pads.length) { this.raw.append(el('div', 'hint', 'No gamepad reported by the browser. Press a button on the controller.')); }
      for (const p of pads) {
        const box = el('div', 'cp-rawpad');
        box.dataset.index = String(p.index);
        box.append(el('div', 'cp-rawid', `#${p.index} ${p.id} · mapping: ${p.mapping || 'none'}`));
        const axes = el('div', 'cp-axes');
        p.axes.forEach((_, i) => {
          const row = el('div', 'cp-axis');
          const bar = el('div', 'cp-bar centred'); bar.append(el('div', 'cp-mid'), el('div', 'cp-fill'));
          row.append(el('span', 'cp-lbl', axisName(i, kindOf(p), true)), bar, el('span', 'cp-val', '0'));
          axes.append(row);
        });
        const btns = el('div', 'cp-buttons');
        p.buttons.forEach((_, i) => {
          const b = el('div', 'cp-btn');
          b.append(el('div', 'cp-btn-name', buttonName(i, kindOf(p), true)), el('div', 'cp-btn-val', '0'), el('div', 'cp-btn-bar'));
          btns.append(b);
        });
        box.append(axes, btns);
        this.raw.append(box);
      }
    }
    pads.forEach((p, k) => {
      const box = this.raw.children[k] as HTMLElement | undefined;
      if (!box) return;
      const axes = box.querySelectorAll<HTMLElement>('.cp-axis');
      p.axes.forEach((a, i) => {
        const row = axes[i]; if (!row) return;
        const fill = row.querySelector<HTMLElement>('.cp-fill')!;
        const w = Math.min(1, Math.abs(a)) * 50;
        fill.style.left = a >= 0 ? '50%' : `${50 - w}%`;
        fill.style.width = `${w}%`;
        row.querySelector<HTMLElement>('.cp-val')!.textContent = a.toFixed(3);
      });
      const bs = box.querySelectorAll<HTMLElement>('.cp-btn');
      p.buttons.forEach((b, i) => {
        const cell = bs[i]; if (!cell) return;
        cell.classList.toggle('on', b.pressed);
        (cell.querySelector('.cp-btn-val') as HTMLElement).textContent = b.value.toFixed(3) + (b.pressed ? ' ●' : '');
        (cell.querySelector('.cp-btn-bar') as HTMLElement).style.width = `${b.value * 100}%`;
      });
    });
  }
}
