import { describe, expect, it } from 'vitest';
import { MenuModel, RepeatGate, type MenuEntry, type MenuPage } from '../menu';

function makePage() {
  const log: string[] = [];
  const state = { on: false, cam: 'chase' };
  const sub: MenuPage = { title: 'Sub', entries: () => [{ kind: 'action', id: 'x', label: 'X', run: () => log.push('x') }, { kind: 'back', id: 'back', label: 'Back' }] };
  const entries: MenuEntry[] = [
    { kind: 'action', id: 'a', label: 'A', run: () => log.push('a') },
    { kind: 'action', id: 'off', label: 'Disabled', disabled: true, run: () => log.push('off') },
    { kind: 'toggle', id: 't', label: 'T', get: () => state.on, set: (v) => { state.on = v; } },
    {
      kind: 'choice', id: 'c', label: 'C', options: [{ value: 'chase', label: 'Chase' }, { value: 'hood', label: 'Hood' }, { value: 'driver', label: 'Driver' }],
      get: () => state.cam, set: (v) => { state.cam = v; },
    },
    { kind: 'submenu', id: 's', label: 'S', page: () => sub },
  ];
  return { page: { title: 'Root', entries: () => entries } as MenuPage, log, state };
}

describe('menu model', () => {
  it('wraps up/down and skips disabled rows', () => {
    const { page } = makePage();
    const m = new MenuModel(page);
    expect(m.current?.id).toBe('a');
    m.nav('down'); expect(m.current?.id).toBe('t'); // skipped the disabled row
    m.nav('up'); expect(m.current?.id).toBe('a');
    m.nav('up'); expect(m.current?.id).toBe('s');   // wrapped to the bottom
    m.nav('down'); expect(m.current?.id).toBe('a'); // and back to the top
  });
  it('starts on the first selectable row', () => {
    const page: MenuPage = { title: '', entries: () => [{ kind: 'action', id: 'd', label: 'd', disabled: true, run: () => {} }, { kind: 'back', id: 'b', label: 'b' }] };
    expect(new MenuModel(page).current?.id).toBe('b');
  });
  it('selects actions, flips toggles and cycles choices both ways', () => {
    const { page, log, state } = makePage();
    const m = new MenuModel(page);
    expect(m.nav('select')).toBe('changed'); expect(log).toEqual(['a']);
    m.nav('down');
    m.nav('select'); expect(state.on).toBe(true);
    m.nav('left'); expect(state.on).toBe(false);
    m.nav('down');
    m.nav('right'); expect(state.cam).toBe('hood');
    m.nav('select'); expect(state.cam).toBe('driver');
    m.nav('right'); expect(state.cam).toBe('chase'); // wraps
    m.nav('left'); expect(state.cam).toBe('driver');
    expect(m.focus(1)).toBe(false); // a disabled row cannot be focused (mouse)
  });
  it('opens submenus and backs out; back at the root closes only a closable menu', () => {
    const { page, log } = makePage();
    const pause = new MenuModel(page, true);
    pause.focus(4);
    expect(pause.nav('select')).toBe('pushed');
    expect(pause.page.title).toBe('Sub');
    pause.nav('select'); expect(log).toEqual(['x']);
    pause.nav('down');
    expect(pause.nav('select')).toBe('popped'); // the Back row
    expect(pause.page.title).toBe('Root');
    expect(pause.nav('back')).toBe('close');
    expect(pause.nav('menu')).toBe('close'); // Start closes the pause menu

    const main = new MenuModel(page, false);
    expect(main.nav('back')).toBe('none');
    expect(main.nav('menu')).toBe('changed'); // Start picks on the main menu
  });
});

describe('repeat gate', () => {
  it('fires on press, after 350 ms, then every 120 ms', () => {
    const g = new RepeatGate<'up' | 'down'>(350, 120);
    const fired: number[] = [];
    for (let t = 0; t <= 1000; t += 10) if (g.update('down', t)) fired.push(t);
    expect(fired).toEqual([0, 350, 470, 590, 710, 830, 950]);
  });
  it('restarts on release or a change of direction', () => {
    const g = new RepeatGate<'up' | 'down'>(350, 120);
    expect(g.update('down', 0)).toBe('down');
    expect(g.update('down', 100)).toBeNull();
    expect(g.update('up', 120)).toBe('up');
    expect(g.update(null, 130)).toBeNull();
    expect(g.update('up', 140)).toBe('up');
  });
  it('does not burst after a late poll', () => {
    const g = new RepeatGate<'up'>(350, 120);
    g.update('up', 0);
    expect(g.update('up', 2000)).toBe('up');
    expect(g.update('up', 2016)).toBeNull();
    expect(g.update('up', 2120)).toBe('up');
  });
  it('a keydown press is not repeated twice', () => {
    const g = new RepeatGate<'up'>(350, 120);
    g.press('up', 0);
    expect(g.update('up', 16)).toBeNull();
    expect(g.update('up', 350)).toBe('up');
  });
});

describe('select entry (the Track drop-down)', () => {
  const make = () => {
    const picks: string[] = [];
    let cur = 'laguna';
    const page: MenuPage = {
      title: 'Root',
      entries: () => [{
        kind: 'select', id: 'track', label: 'Track',
        options: [{ value: 'laguna', label: 'Laguna' }, { value: 'sonoma', label: 'Sonoma' }, { value: 'bw', label: 'Buttonwillow' }, { value: 'mo', label: 'Mid-Ohio' }],
        get: () => cur, set: (v) => { picks.push(v); cur = v; },
      }],
    };
    return { page, picks };
  };
  it('left/right never pick (no load on the way through)', () => {
    const { page, picks } = make();
    const m = new MenuModel(page);
    expect(m.nav('right')).toBe('none'); expect(m.nav('left')).toBe('none');
    expect(picks).toEqual([]);
  });
  it('opening lists every option with the cursor on the current one, without picking', () => {
    const { page, picks } = make();
    const m = new MenuModel(page);
    expect(m.nav('select')).toBe('pushed');
    expect(m.entries.filter((e) => e.kind === 'action').map((e) => e.label)).toEqual(['Laguna', 'Sonoma', 'Buttonwillow', 'Mid-Ohio']);
    expect(m.current?.id).toBe('track:laguna');
    m.nav('down'); m.nav('down');
    expect(picks).toEqual([]);
  });
  it('a pick calls set once; picking the current one does nothing; back closes the list', () => {
    const { page, picks } = make();
    const m = new MenuModel(page);
    m.nav('select'); m.nav('select'); // current option
    expect(picks).toEqual([]);
    m.nav('down'); m.nav('select');
    expect(picks).toEqual(['sonoma']);
    expect(m.nav('back')).toBe('popped');
    expect(m.page.title).toBe('Root');
  });
});

describe('menu model: two columns', () => {
  const act = (id: string, col: 0 | 1, extra: Partial<MenuEntry> = {}): MenuEntry => ({ kind: 'action', id, label: id, col, run: () => {}, ...extra } as MenuEntry);
  const choice = (id: string, col: 0 | 1): MenuEntry => ({ kind: 'choice', id, label: id, col, options: [{ value: 'a', label: 'A' }, { value: 'b', label: 'B' }], get: () => st[id] ?? 'a', set: (v) => { st[id] = v; } });
  let st: Record<string, string> = {};
  // left: track (choice), hotlap, race, ghost (choice), cars; right: howto, controls, graphics (choice), scoreboard, whatsnew, credits, feedback
  const list = (): MenuEntry[] => [
    choice('track', 0), act('hotlap', 0), act('race', 0), choice('ghost', 0), act('cars', 0),
    act('howto', 1), act('controls', 1), choice('graphics', 1), act('scoreboard', 1), act('whatsnew', 1), act('credits', 1), act('feedback', 1),
  ];
  const model = (cols = true) => { st = {}; const m = new MenuModel({ title: '', entries: list }); m.columns = cols; return m; };
  const to = (m: MenuModel, id: string) => { for (let k = 0; k < 20 && m.current?.id !== id; k++) m.nav('down'); expect(m.current?.id).toBe(id); };

  it('up and down wrap inside the column', () => {
    const m = model();
    to(m, 'cars');
    m.nav('down'); expect(m.current?.id).toBe('track');   // wrapped inside the left column
    m.nav('up'); expect(m.current?.id).toBe('cars');
  });
  it('left and right on a non-value row jump to the other column at the nearest row', () => {
    const m = model();
    to(m, 'hotlap');                                            // left row 1
    expect(m.nav('right')).toBe('moved'); expect(m.current?.id).toBe('controls');   // right row 1
    expect(m.nav('left')).toBe('moved'); expect(m.current?.id).toBe('hotlap');
    to(m, 'cars');                                              // left row 4
    m.nav('right'); expect(m.current?.id).toBe('whatsnew');     // right row 4
    to(m, 'feedback');                                          // right row 6, the left column has 5 rows: clamped to its last
    m.nav('left'); expect(m.current?.id).toBe('cars');
  });
  it('value rows (a choice) keep left and right for their values', () => {
    const m = model();
    expect(m.current?.id).toBe('track');
    m.nav('right'); expect(m.current?.id).toBe('track'); expect(st.track).toBe('b');
    to(m, 'ghost'); m.nav('left'); expect(m.current?.id).toBe('ghost'); expect(st.ghost).toBe('b');
  });
  it('a disabled row is skipped when jumping, and the focus survives a submenu round trip', () => {
    st = {};
    const es = list().map((e) => (e.id === 'controls' ? { ...e, disabled: true } : e)) as MenuEntry[];
    const sub: MenuPage = { title: 'S', entries: () => [{ kind: 'back', id: 'back', label: 'Back' }] };
    es[8] = { kind: 'submenu', id: 'scoreboard', label: 's', col: 1, page: () => sub };
    const m = new MenuModel({ title: '', entries: () => es }); m.columns = true;
    to(m, 'hotlap'); m.nav('right');
    expect(m.current?.id).toBe('howto');                        // the nearest selectable row (controls is disabled)
    to(m, 'scoreboard'); m.nav('select'); m.nav('select');      // open and back
    expect(m.current?.id).toBe('scoreboard');
  });
  it('one column (a narrow screen): the old behaviour, one cycle over the whole list; left/right do nothing on actions', () => {
    const m = model(false);
    to(m, 'cars'); m.nav('down'); expect(m.current?.id).toBe('howto');
    expect(m.nav('right')).toBe('none'); expect(m.current?.id).toBe('howto');
  });
});
