// Composition root: boot, assets, renderer, world, car, cameras, audio, input,
// menus and game modes. Fixed-step physics (1000 Hz) while driving; nothing is
// stepped and audio is suspended while a menu or the controls panel is open.
import * as THREE from 'three';
import './style.css';
import { physics, usingStub } from './physics-loader';
import type { GhostLap, Surface, TrackJson, VehicleLike } from './physics-types';
import { loadAssets, type Assets } from './loader';
import { buildWorld, type World } from './scene';
import { Look, postUrlOff, sunFromUrl } from './look';
import { upgradeCarMaterials } from './car-materials';
import { TrackMarks } from './marks';
import { setFieldLook } from './field-cars';
import { CarRig } from './car';
import { GhostManager } from './ghosts';
import { CAMERA_MODES, CameraRig, DRIVER_VIEW_DEFAULTS, EYE_RANGE, FOV_CHOICES, OFFSET_STEP, SEAT_RANGE, type CameraMode } from './cameras';
import { Input, type Action } from './input';
import { ControlsPanel } from './controls-panel';
import { Hud } from './hud';
import { CarAudio, audioParamsFromCarJson } from './audio';
import { Menu, type MenuEntry, type MenuPage } from './menu';
import { ModeHost, type GameMode, type ModeContext, type ModeId } from './modes/mode';
import { createHotLap, HotlapLoop } from './modes/hotlap';
import { createRace, fieldAudioHook, fieldAudioUrlOff, fieldVoicesFor, raceMenuLabel } from './modes/race';
import { pitExitConeWatcher } from './scenery';
import { creditsPage } from './credits';
import { APP_VERSION, changelogPage, versionLine } from './changelog';
/** AI engine sounds in a race (src/app/audio-field.ts): on by default; pause-menu toggle (persisted); ?fieldaudio=0 forces off. */
const FIELD_AUDIO_URL_OFF = fieldAudioUrlOff(location.search);
const FIELD_AUDIO_KEY = 'probeSim.fieldAudio.v1';
let fieldAudioOn = (() => { try { return localStorage.getItem(FIELD_AUDIO_KEY) !== '0'; } catch { return true; } })();
const setFieldAudioOn = (on: boolean) => {
  fieldAudioOn = on;
  try { if (on) localStorage.removeItem(FIELD_AUDIO_KEY); else localStorage.setItem(FIELD_AUDIO_KEY, '0'); } catch { /* no storage */ }
};
import { applyQuality, pixelRatioFor, quality, storeTierChoice, storedTierChoice, type ThinReport, type TierChoice } from './quality';
import { SENSITIVITIES, TouchControls, tiltStatusText } from './touch';
import { HotlapSim, LIMITS, type SimAssets, type SceneryLike, type InputType } from '../scoreboard';
import { LAUNCH_S } from '../scoreboard/config';
import { ScoreboardClient, buildHotlapSubmission, checkHotlap, hotlapBoard, offerCandidate, setBoardContext, fmtLapTime } from './scoreboard-client';
import { ScoreboardUI } from './scoreboard-ui';

// The player's car runs in HotlapSim (src/scoreboard/sim.ts): 1000 Hz physics, 200 Hz timing, input sampled on a
// 100 Hz grid, rolling start 130 m before T11 at 22 m/s. Its constants live in src/scoreboard/config.ts.
const MAX_FRAME = 0.05;      // cap per rendered frame
const GAME_OVER_DELAY_MS = 2500;        // space-launch easter egg: GAME OVER this long after the launch
const TITLE = 'Probe GT · Laguna Seca';

const app = document.getElementById('app')!;
// phone layout + touch controls (quality.ts): html.touch styles the HUD for a small landscape screen
document.documentElement.classList.toggle('touch', quality.touch);
document.documentElement.classList.toggle('tier-phone', quality.tier === 'phone');
const input = new Input();
const touch = quality.touch ? new TouchControls(app) : null;
input.attachTouch(touch);
const audio = new CarAudio();
audio.preload(); // fetch the engine / squeal samples while the track loads
const hud = new Hud(app);
hud.compact = quality.touch;
const menu = new Menu(app, () => ({ select: input.glyph('select'), back: input.glyph('back'), menu: input.glyph('menu') }));
const controlsPanel = new ControlsPanel(app, input);
const scoreClient = new ScoreboardClient();
const scoreUI = new ScoreboardUI({
  app, menu, client: scoreClient,
  toast: (m, ms) => hud.toast(m, ms),
  touch: () => input.source === 'touch',
  hints: () => ({ select: input.glyph('select'), back: input.glyph('back'), menu: input.glyph('menu'), pad: input.source === 'gamepad' && !!input.padId }),
  trackLength: () => sim?.trackLength ?? 0,
  onChange: () => sim?.markDirty(),
});
const scoreboardEntry = (): MenuEntry => ({
  kind: 'submenu', id: 'scoreboard', label: 'Scoreboard', note: sim ? undefined : 'loading…', disabled: !sim, page: () => scoreUI.open(),
});

// ---- shared menu rows: touch controls (phones) and the render tier
const touchPage = (t: TouchControls): MenuPage => ({
  title: 'Touch controls',
  subtitle: 'Brake: left third · Gas: right third · higher = harder',
  entries: (): MenuEntry[] => [
    {
      kind: 'choice', id: 'steerMode', label: 'Steering',
      note: t.settings.steer === 'tilt' && t.steerMode !== 'tilt' ? `tilt ${tiltStatusText(t.tilt)} · using slider` : undefined,
      options: [{ value: 'tilt', label: 'Tilt' }, { value: 'slider', label: 'Slider' }],
      get: () => t.settings.steer, set: (v) => t.setSteerMode(v as 'tilt' | 'slider'), // a tap: may show the iOS prompt
    },
    {
      kind: 'choice', id: 'sens', label: 'Tilt sensitivity', disabled: t.settings.steer !== 'tilt',
      options: SENSITIVITIES.map((v) => ({ value: String(v), label: `${v.toFixed(2).replace(/0$/, '')}×` })),
      get: () => String(SENSITIVITIES.reduce((a, b) => (Math.abs(b - t.settings.sensitivity) < Math.abs(a - t.settings.sensitivity) ? b : a))),
      set: (v) => t.setSensitivity(Number(v)),
    },
    { kind: 'action', id: 'recentre', label: 'Recentre tilt (hold the phone level)', disabled: t.steerMode !== 'tilt', run: () => { t.recentre(); hud.toast('Tilt recentred'); } },
    { kind: 'back', id: 'back', label: 'Back' },
  ],
});
let tierChoice: TierChoice = storedTierChoice();
const graphicsEntry = (): MenuEntry => ({
  kind: 'choice', id: 'graphics', label: 'Graphics',
  note: tierChoice === (quality.reason === 'forced' ? quality.tier : 'auto') ? `${quality.tier}${quality.reason === 'url' ? ' (URL)' : ''}` : 'reload to apply',
  options: [{ value: 'auto', label: 'Auto' }, { value: 'phone', label: 'Phone' }, { value: 'desktop', label: 'Desktop' }],
  get: () => tierChoice, set: (v) => { tierChoice = v as TierChoice; storeTierChoice(tierChoice); },
});
const reloadEntry = (): MenuEntry[] => tierChoice !== (quality.reason === 'forced' ? quality.tier : 'auto')
  ? [{ kind: 'action', id: 'reload', label: 'Reload to apply graphics', run: () => location.reload() }] : [];
/** Controls & calibration is for pads and keys; hidden on a phone unless a pad is connected. */
const showControlsPanelRow = () => !quality.touch || !!input.padId;

const refreshHelp = () => hud.setControlRows(input.helpRows(), `${input.glyph('menu')} pause menu · K remaps and calibrates · Press H to close`);
refreshHelp();
input.onChange(refreshHelp);

// ---------------------------------------------------------------- main menu (shown from the first frame)

const loadBox = document.createElement('div');
loadBox.className = 'menu-load';
loadBox.innerHTML = `<div class="progress"><div></div></div><div class="load-label">Loading…</div>`;
menu.extra.append(loadBox);
// the release and the build's commit (What's new has the history)
const GIT_SHA = typeof __GIT_SHA__ === 'string' ? __GIT_SHA__ : '';
const versionEl = document.createElement('div');
versionEl.className = 'menu-version';
versionEl.textContent = versionLine(APP_VERSION, GIT_SHA);
menu.extra.append(versionEl);
const progressBar = loadBox.querySelector('.progress > div') as HTMLDivElement;
const loadLabel = loadBox.querySelector('.load-label') as HTMLDivElement;

let sim: Sim | null = null;

const mainPage: MenuPage = {
  title: TITLE,
  subtitle: '1993 Ford Probe GT · 24 Hours of Lemons #619',
  entries: (): MenuEntry[] => [
    { kind: 'action', id: 'hotlap', label: 'Hot lap', note: sim ? undefined : 'loading…', disabled: !sim, run: () => startMode('hotlap') },
    { kind: 'action', id: 'race', label: raceMenuLabel(location.search), note: sim ? undefined : 'loading…', disabled: !sim, run: () => startMode('race') },
    ...(touch ? [{ kind: 'submenu', id: 'touch', label: 'Touch controls', page: () => touchPage(touch) } as MenuEntry] : []),
    ...(showControlsPanelRow() ? [{ kind: 'action', id: 'controls', label: 'Controls & calibration', run: () => controlsPanel.open() } as MenuEntry] : []),
    graphicsEntry(),
    ...reloadEntry(),
    scoreboardEntry(),
    { kind: 'submenu', id: 'whatsnew', label: "What's new", note: `v${APP_VERSION}`, page: () => changelogPage(GIT_SHA) },
    { kind: 'submenu', id: 'credits', label: 'Credits', page: creditsPage },
  ],
};

function showMainMenu(): void {
  hud.hideHelp();
  menu.show(mainPage, { closable: false, variant: 'main', onChange: () => sim?.markDirty() });
}

/** Menu pick (a user gesture): start audio, switch mode, drive. */
function startMode(id: ModeId): void {
  if (!sim) return;
  void audio.start(); // synchronously inside the tap / click: unlocks the AudioContext on iOS
  if (touch) { touch.requestTilt(); touch.recentre(); } // tilt permission prompt needs this gesture too
  sim.setMode(id);
  menu.close();
}

showMainMenu();

// ---------------------------------------------------------------- UI loop (menus, panel, shared shortcuts)

let uiPaused = true; // last applied pause state (audio suspended, clock held)

function sharedAction(a: Action): boolean {
  switch (a) {
    case 'mute': audio.setMuted(!audio.muted); hud.toast(audio.muted ? 'Muted' : 'Sound on'); menu.refresh(); return true;
    case 'help': hud.toggleHelp(); return true;
    case 'controls': controlsPanel.toggle(); return true;
    default: return false;
  }
}

/** The cursor hides this long after the last pointer move while the game runs. */
const CURSOR_HIDE_MS = 1500;
let lastPointerMoveAt = 0;
window.addEventListener('pointermove', () => { lastPointerMoveAt = performance.now(); }, { passive: true });

function uiTick(now: number): void {
  requestAnimationFrame(uiTick);
  const editing = scoreUI.editorOpen;
  const blocked = menu.isOpen || controlsPanel.isOpen || editing;
  input.navMode = blocked;
  for (const n of input.consumeNotices()) hud.toast(n);
  const actions = input.consumeActions();
  const navs = input.consumeNav();

  if (editing) {
    // the name editor sits above any menu: pad d-pad / A / B / Start (typing goes to its text field)
    for (const a of actions) if (a === 'menu') scoreUI.editor.nav('menu');
    for (const n of navs) scoreUI.editor.nav(n);
  } else if (controlsPanel.isOpen) {
    for (const a of actions) if (a === 'menu') controlsPanel.close(); else sharedAction(a);
    for (const n of navs) if (n === 'back') controlsPanel.close();
  } else if (menu.isOpen) {
    // the new-best prompt only closes on Submit / Skip (Start would 'select' on a non-closable card)
    for (const a of actions) if (a === 'menu') { if (!scoreUI.promptOpen) menu.nav('menu'); } else sharedAction(a);
    for (const n of navs) {
      if (hud.helpOpen && (n === 'back' || n === 'select')) { hud.hideHelp(); continue; }
      menu.nav(n);
    }
    menu.tickHints();
  }

  // phone held in portrait: open the pause menu and show the rotate overlay (CSS)
  const portrait = !!touch?.portrait;
  if (portrait && sim?.running && !menu.isOpen && !controlsPanel.isOpen && !editing) sim.openPause();
  touch?.setVisible(!!sim?.running && !menu.isOpen && !controlsPanel.isOpen && !editing && !portrait);

  const paused = menu.isOpen || controlsPanel.isOpen || editing || document.hidden || portrait;
  // no mouse cursor over the game while driving (it comes back on any pointer move, and in menus)
  document.body.style.cursor = !paused && sim?.running && performance.now() - lastPointerMoveAt > CURSOR_HIDE_MS ? 'none' : '';
  if (paused !== uiPaused) {
    uiPaused = paused;
    if (paused) audio.suspend(); else audio.resume();
  }
  hud.setVisible(!!sim?.running && !(menu.isOpen && menu.variant === 'main'));
  sim?.frame(now, blocked ? [] : actions, paused);
}
requestAnimationFrame(uiTick);

// iOS suspends ("interrupts") the AudioContext after a call, Siri or backgrounding; resume on the next tap
for (const ev of ['touchend', 'pointerup'] as const) document.addEventListener(ev, () => { if (!uiPaused) audio.unlock(); }, { capture: true, passive: true });

// ---------------------------------------------------------------- boot

async function boot(): Promise<void> {
  let assets: Assets;
  try {
    assets = await loadAssets((f, label) => {
      progressBar.style.width = `${Math.round(f * 100)}%`;
      loadLabel.textContent = `Loading ${label}… ${Math.round(f * 100)}%`;
    });
  } catch (e) {
    loadLabel.className = 'load-label err';
    loadLabel.textContent = `Failed to load: ${String((e as Error)?.stack ?? e)}`;
    throw e;
  }
  progressBar.style.width = '100%';
  sim = createSim(assets);
  loadLabel.textContent = assets.fallbacks.length ? `Using stand-ins: ${assets.fallbacks.join(', ')}` : 'Ready';
  loadBox.classList.add('done');
  if (menu.isOpen && menu.variant === 'main' && menu.state?.depth === 1) menu.state.focus(0); // Hot lap is now pickable
  menu.refresh();
  sim.renderOnce();
}

// ---------------------------------------------------------------- sim

type Sim = ReturnType<typeof createSim>;

function createSim(assets: Assets) {
  const { track, heightfield } = assets;
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  // render tier (quality.ts): phone = pixel ratio ≤ 1 and ≤ 1.2 MP, no shadow maps; desktop = ≤ 1.5 as before
  renderer.setPixelRatio(pixelRatioFor(quality, window.devicePixelRatio, window.innerWidth, window.innerHeight));
  renderer.setSize(window.innerWidth, window.innerHeight);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;
  renderer.domElement.className = 'view';
  app.insertBefore(renderer.domElement, app.firstChild);

  // the physics surface (ribbon profile + blended shoulder + heightfield) also shapes the rendered shoulder, kerbs
  // and barrier feet, so what is drawn is what the car drives on
  // far terrain (scenery.json far.heightfield) keeps the ground under the car everywhere
  const farGrid = assets.scenery?.json.far?.heightfield;
  const farHf = assets.scenery?.farHeightfield ?? null;
  const far = farGrid && farHf ? { heightfield: farHf, x0: farGrid.x0, y0: farGrid.y0, dx: farGrid.dx, nx: farGrid.nx, ny: farGrid.ny } : null;
  // the pit lane (scenery.json pit_lane) is paved: full grip and its own smooth profile
  const pit = assets.scenery?.json.pit_lane ?? null;
  const zones = assets.scenery?.json.paved_zones ?? null;
  // paved runoff zones share the pit lane's code path in the physics: one list of open paved parts
  const pitLane = pit || zones
    ? { spacing_m: 1, fractions: (pit ?? zones)!.fractions, parts: [...(pit?.parts ?? []), ...(zones?.parts ?? [])] }
    : null;
  // rendering / HUD surface. The physics surface is private to HotlapSim: Surface.sample() caches the last
  // station, so sampling the sim's surface from the HUD would change the physics (docs/scoreboard.md §3.1)
  const surface: Surface = physics.createTrackSurface(track, heightfield, { far, pitLane, sausages: assets.scenery?.json.sausages ?? null });
  /** A wheel is off track only if it is on neither the track nor the paved pit lane. */
  const wheelOff = (w: { onTrack: boolean; pos: [number, number, number] }) => !w.onTrack && !surface.sample(w.pos[0], w.pos[1]).paved;
  const world: World = buildWorld(track, heightfield, assets.ortho, Math.min(quality.maxAnisotropy, renderer.capabilities.getMaxAnisotropy()), assets.scenery,
    (x, y) => surface.sample(x, y).z, { pbr: quality.tier !== 'phone', line: assets.ghosts?.line ? { s_grid_m: assets.ghosts.s_grid_m, offset_m: assets.ghosts.line.offset_m } : null });
  const thinned: ThinReport | null = applyQuality(quality, renderer, world, track);
  // the look (look.ts): clear-coated paint on the player's car and the field, reflections from the sky's environment
  upgradeCarMaterials(assets.carModel, { clearcoat: quality.tier !== 'phone' });
  setFieldLook({ clearcoat: quality.tier !== 'phone', sceneEnv: true });
  const ghostTemplate = assets.carModel.clone(true);
  const car = new CarRig(assets.carModel);
  world.scene.add(car.root);

  audio.configure(audioParamsFromCarJson(assets.carSpecJson)); // rev limit, idle, tyre peaks (squeal onset fallback)
  // the player's car: the deterministic HotlapSim (fresh Vehicle + private Surface on every reset, collision world,
  // 200 Hz timing + gear schedule, input trace for the scoreboard). Always the real physics (?stub=1 no longer
  // affects the player's car).
  const simAssets: SimAssets = {
    trackId: 'laguna_seca', carId: 'probe_gt', track: track as unknown as SimAssets['track'], heightfield,
    carJson: assets.carSpecJson, scenery: (assets.scenery?.json ?? null) as SceneryLike | null,
    farHeightfield: assets.scenery?.farHeightfield ?? null, ghosts: assets.ghosts as unknown as SimAssets['ghosts'],
  };
  const hsim = new HotlapSim(simAssets, { record: true, autoShift: true });
  /** The current Vehicle (a new one after every reset). */
  const veh = (): VehicleLike => hsim.vehicle as unknown as VehicleLike;
  const timer = hsim.timer;
  const loop = new HotlapLoop(hsim, () => ({ steer: input.steer, throttle: input.throttle, brake: input.brake, handbrake: input.handbrake, tag: input.inputTag as InputType }));
  // physics-relevant stand-ins (synthetic track, flat heightfield, synthetic ghosts, no scenery / car.json) make
  // submissions fail the server's physics check or replay, so they are not offered
  const assetsOk = !assets.fallbacks.some((f) => !/^(ortho|car model)/.test(f));
  setBoardContext({ client: scoreClient, track: 'laguna_seca', car: 'probe_gt', physics: hsim.physics, input: () => input.inputTag, assetsOk, offer: (c) => scoreUI.offer(c) });
  void scoreClient.info().then((r) => {
    if (!r.ok) return; // offline: the Scoreboard screen says so when opened
    const server = r.value.boards['laguna_seca/probe_gt'];
    if (server && server !== hotlapBoard()) hud.toast('Scoreboard: this page is out of date — reload to post laps', 5000);
  });

  const ghosts = new GhostManager(physics, track, assets.ghosts, ghostTemplate);
  ghosts.group.visible = false; // a mode shows them
  world.scene.add(ghosts.group);

  const cams = new CameraRig(window.innerWidth / window.innerHeight);
  const look = new Look(renderer, world, cams.camera, quality, { sun: sunFromUrl(location.search), post: !postUrlOff(location.search), fogHeightM: track.center[0][2] });
  // tyre marks, dust and smoke for the player (here) and the AI field (race.ts), on the rendering surface
  const marks = new TrackMarks(world.scene, (x, y) => surface.sample(x, y));

  // space-launch easter egg: camera follows the car up, GAME OVER after 2.5 s, reset clears it
  let launchSeenAt = -1, gameOverShown = false, lastImpactT = -1;
  function clearLaunch(): void {
    launchSeenAt = -1; gameOverShown = false; lastImpactT = -1;
    cams.setLaunched(false);
    hud.hideGameOver();
  }

  /** Race recovery only (not replayed): put the current vehicle on the centreline at s. Hot lap never calls it. */
  const placeCar = (s: number, speed: number) => {
    const p = physics.lineToWorld(track, () => 0, ((s % track.length_m) + track.length_m) % track.length_m);
    veh().reset([p.pos[0], p.pos[1], p.pos[2]], p.heading, speed);
    clearLaunch();
    dirty = true;
  };
  /** Rolling start = HotlapSim reset: new Vehicle + Surface, timer and sim clock cleared, a new trace begins. */
  const rollingStart = (o: { launch?: boolean } = {}) => {
    loop.reset();
    loop.sim.launchUntil = o.launch ? LAUNCH_S : 0;
    clearLaunch();
    dirty = true;
  };

  // auto-shift follows a ghost's gear schedule (derived in HotlapSim from its rpm and speed channels, recorded in
  // the trace); the vehicle falls back to its rpm rules off the ghost's line (> 15 m) or without a schedule
  function setScheduleLap(lap: GhostLap | null): void {
    hsim.setRef(lap ? lap.id : null);
    hud.setAutoSource(lap && lap.rpm && lap.rpm.length ? lap.driver : null);
  }
  let lastGear = veh().state.gear, manualShiftAt = -1;
  const statusBits = [usingStub ? 'stub physics' : 'physics', track.name];
  if (assets.fallbacks.length) statusBits.push('stand-ins: ' + assets.fallbacks.join(', '));
  hud.setStatus(statusBits.join(' · '));

  let last = performance.now();
  let running = false;   // a mode has been started
  let wasPaused = true;
  let dirty = true;      // render once while paused (menu changes, camera choice)
  /** Best hot-lap time offered to the scoreboard this session (submitted or skipped), so slower laps do not re-prompt. */
  let offeredBest: number | null = null;

  const ctx: ModeContext = {
    marks,
    physics, track, timer, ghosts, ghostData: assets.ghosts, hud, input,
    get vehicle() { return veh(); },
    simTime: () => hsim.simTime,
    s: () => hsim.s,
    playerPos: () => car.root.position,
    rollingStart,
    recoverAt: (s) => placeCar(s, 0),
    setScheduleLap,
    toast: (m) => hud.toast(m),
    // race mode (modes/race.ts, NOTES-race.md): the director steps the HotlapSim car; AI rigs go into the scene
    race: {
      sim: hsim, scene: world.scene, menu, quality, search: location.search,
      mainMenu: () => showMainMenu(),
      impact: (v) => audio.impact(v),
      // AI engine sounds: FieldAudio on CarAudio's context, into its field bus (under the master: Mute applies)
      fieldAudio: () => fieldAudioHook(audio.context, audio.fieldBus(), fieldVoicesFor(quality.tier)),
      fieldAudioEnabled: () => fieldAudioOn && !FIELD_AUDIO_URL_OFF,
      // the pit-exit cone line (scenery.json pit_exit_cones): crossing it is a black flag
      coneLine: () => pitExitConeWatcher(),
    },
  };
  const modes = new ModeHost<ModeContext>({ hotlap: createHotLap, race: createRace }, ctx);
  const mode = (): GameMode | null => modes.current;

  const pausedEl = document.createElement('div');
  pausedEl.className = 'paused hidden';
  pausedEl.textContent = 'PAUSED';
  app.appendChild(pausedEl);

  window.addEventListener('resize', () => {
    look.resize(window.innerWidth, window.innerHeight);
    cams.resize(window.innerWidth / window.innerHeight);
    dirty = true;
  });

  const setCamera = (m: CameraMode) => { cams.setMode(m); dirty = true; };

  // ---- Driver view (cameras.ts): seat offsets over the glb's cam_driver, horizontal FOV, look-stick release
  const cmLabel = (cm: number) => `${cm > 0 ? '+' : ''}${Math.round(cm)} cm`;
  const cmChoices = (r: readonly [number, number]) => {
    const out = [];
    for (let cm = Math.round(r[0] * 100); cm <= Math.round(r[1] * 100); cm += Math.round(OFFSET_STEP * 100)) out.push({ value: String(cm), label: cmLabel(cm) });
    return out;
  };
  const driverViewPage = (): MenuPage => ({
    title: 'Driver view',
    subtitle: `Defaults: eye ${cmLabel(DRIVER_VIEW_DEFAULTS.eyeY * 100)}, seat ${cmLabel(DRIVER_VIEW_DEFAULTS.seatZ * 100)}, ${DRIVER_VIEW_DEFAULTS.fov}° wide · offsets from the model's eye point`,
    entries: (): MenuEntry[] => [
      { kind: 'choice', id: 'eye', label: 'Eye height', options: cmChoices(EYE_RANGE), get: () => String(Math.round(cams.driverView.eyeY * 100)), set: (v) => { cams.setDriverView({ eyeY: Number(v) / 100 }); dirty = true; } },
      { kind: 'choice', id: 'seat', label: 'Seat fore/aft', note: '+ = forward', options: cmChoices(SEAT_RANGE), get: () => String(Math.round(cams.driverView.seatZ * 100)), set: (v) => { cams.setDriverView({ seatZ: Number(v) / 100 }); dirty = true; } },
      { kind: 'choice', id: 'fov', label: 'Field of view', note: 'horizontal', options: FOV_CHOICES.map((f) => ({ value: String(f), label: `${f}°` })), get: () => String(cams.driverView.fov), set: (v) => { cams.setDriverView({ fov: Number(v) }); dirty = true; } },
      { kind: 'choice', id: 'lookHold', label: 'Look stick released', options: [{ value: 'spring', label: 'Springs back' }, { value: 'hold', label: 'Holds full look' }], get: () => (input.lookHold ? 'hold' : 'spring'), set: (v) => input.setLookHold(v === 'hold') },
      { kind: 'action', id: 'reset', label: 'Reset driver view', run: () => { cams.resetDriverView(); dirty = true; menu.refresh(); } },
      { kind: 'back', id: 'back', label: 'Back' },
    ],
  });

  // ---- pause menu
  const pausePage: MenuPage = {
    title: 'Paused',
    entries: (): MenuEntry[] => [
      { kind: 'action', id: 'resume', label: 'Resume', run: () => menu.close() },
      { kind: 'action', id: 'restart', label: 'Restart', run: () => { modes.restart(); menu.close(); } },
      {
        kind: 'choice', id: 'camera', label: 'Camera',
        options: CAMERA_MODES.map((m) => ({ value: m, label: m[0].toUpperCase() + m.slice(1) })),
        get: () => cams.mode, set: (v) => setCamera(v as CameraMode),
      },
      { kind: 'submenu', id: 'driverView', label: 'Driver view', page: driverViewPage },
      // settings go through the sim: applied (and recorded in the trace) at the next 100 Hz sample
      { kind: 'toggle', id: 'autoShift', label: hud.autoSourceDriver ? `Auto-shift (${hud.autoSourceDriver}'s gears)` : 'Auto-shift', get: () => hsim.autoShift, set: (on) => { hsim.autoShift = on; } },
      { kind: 'toggle', id: 'abs', label: 'ABS (crude, 1993)', get: () => hsim.abs, set: (on) => { hsim.abs = on; } },
      ...(mode()?.pauseEntries() ?? []),
      ...(mode()?.id === 'hotlap' ? scoreUI.pauseEntries() : []),
      scoreboardEntry(),
      ...(touch ? [
        { kind: 'action', id: 'resetCar', label: 'Reset car', run: () => { mode()?.reset(); menu.close(); } } as MenuEntry,
        { kind: 'submenu', id: 'touch', label: 'Touch controls', page: () => touchPage(touch) } as MenuEntry,
      ] : []),
      ...(showControlsPanelRow() ? [{ kind: 'action', id: 'controls', label: 'Controls & calibration', run: () => controlsPanel.open() } as MenuEntry] : []),
      graphicsEntry(),
      ...reloadEntry(),
      { kind: 'toggle', id: 'mute', label: 'Mute', get: () => audio.muted, set: (m) => audio.setMuted(m) },
      {
        kind: 'toggle', id: 'fieldAudio', label: 'AI engine sounds', note: FIELD_AUDIO_URL_OFF ? 'off (?fieldaudio=0)' : undefined,
        disabled: FIELD_AUDIO_URL_OFF, get: () => fieldAudioOn && !FIELD_AUDIO_URL_OFF, set: setFieldAudioOn,
      },
      { kind: 'action', id: 'main', label: 'Main menu', run: () => showMainMenu() },
    ],
  };
  const openPause = () => {
    hud.hideHelp();
    menu.show({ ...pausePage, subtitle: mode()?.label }, { closable: true, variant: 'pause', onChange: () => { dirty = true; } });
  };

  const handle = (a: Action) => {
    switch (a) {
      case 'shiftUp': loop.shiftUp(); manualShiftAt = performance.now(); break;
      case 'shiftDown': loop.shiftDown(); manualShiftAt = performance.now(); break;
      case 'camera': { const m = cams.cycle(); hud.toast(`Camera: ${m}`); break; }
      case 'autoShift': hsim.autoShift = !hsim.autoShift; hud.toast(`Auto-shift ${hsim.autoShift ? 'on' : 'off'}`); break;
      case 'reset': mode()?.reset(); break;
      // game-over card: Enter / Space / A reset, and so does the pad's Start (Esc still pauses)
      case 'confirm': if (gameOverShown) mode()?.reset(); break;
      case 'menu': if (gameOverShown && input.source === 'gamepad') mode()?.reset(); else openPause(); break;
      default: sharedAction(a);
    }
  };

  // ---- the fixed-step loop: HotlapLoop steps HotlapSim at 1 kHz (same accumulator as before)
  loop.onStep = () => mode()?.step(0.001);
  loop.timeScale = () => mode()?.timeScale?.() ?? 1; // 10 while the race fast-forwards a stop-and-go
  loop.halt = () => menu.isOpen; // the new-best prompt opened: stop stepping this frame
  loop.onLap = (lap, tag) => {
    // the trace is exactly at this lap's end; copy it now if the lap is a scoreboard candidate
    const hot = mode()?.id === 'hotlap';
    const board = hotlapBoard();
    let offer: (() => void) | null = null;
    let note: string | null = null;
    if (hot && board) {
      const pb = scoreClient.pb(board);
      const quick = checkHotlap(lap, { pb, offered: offeredBest, steps: hsim.stepIndex, rows: 0, assetsOk });
      if (quick.best && quick.submittable) {
        const trace = hsim.trace();
        const chk = checkHotlap(lap, { pb, offered: offeredBest, steps: trace.steps, rows: trace.rows.length, assetsOk });
        if (chk.submittable) {
          offeredBest = lap.time;
          offer = () => void offerCandidate({
            mode: 'hotlap', board, score: lap.time, detail: `Lap ${lap.n}`,
            build: (name) => buildHotlapSubmission({ lap, trace, name, input: tag, device: scoreClient.device }),
          });
        } else note = chk.reason!;
      } else if (quick.best && lap.valid) note = quick.reason!;
    }
    mode()?.onLap(lap);
    if (note) hud.toast(`Lap ${lap.n} ${fmtLapTime(lap.time)} is a new best but can't be posted: ${note}`, 5000);
    else if (hot && lap.n === LIMITS.maxLap && !offer) hud.toast(`Lap ${lap.n} done · laps after ${LIMITS.maxLap} can't be posted to the scoreboard — reset to post again`, 4000);
    offer?.();
  };

  const render = () => {
    const vehicle = veh();
    car.pose(vehicle.state);
    cams.update(car, 1 / 60, 0, vehicle.state.speed);
    world.follow(car.root.position, cams.camera);
    look.render(0, vehicle.state.speed);
  };

  /** One rendered frame; called from the UI loop. paused: a menu / panel is open or the tab is hidden. */
  const frame = (now: number, actions: Action[], paused: boolean) => {
    if (!running) return;
    pausedEl.classList.toggle('hidden', !document.hidden);
    if (paused) {
      wasPaused = true;
      if (dirty && !document.hidden) { dirty = false; render(); }
      return;
    }
    if (wasPaused) { wasPaused = false; last = now; loop.acc = 0; }
    const dt = Math.min((now - last) / 1000, MAX_FRAME);
    last = now;
    for (const a of actions) handle(a);
    if (menu.isOpen) return; // 'menu' just opened the pause menu
    touch?.setManual(!hsim.autoShift);
    loop.advance(dt); // input is sampled inside, on the sim's 100 Hz grid
    const vehicle = veh();

    const st = vehicle.state;
    if (st.gear !== lastGear) {
      if (vehicle.autoShift && now - manualShiftAt > 400 && st.gear > 0 && lastGear > 0) hud.flashGear();
      lastGear = st.gear;
    }
    if (st.impact && st.impact.t !== lastImpactT) {
      lastImpactT = st.impact.t;
      audio.impact(st.impact.speedNormal);
    }
    if (!st.launched && launchSeenAt >= 0) clearLaunch(); // reset from elsewhere (console)
    if (st.launched && launchSeenAt < 0) {
      launchSeenAt = now;
      cams.setLaunched(true);
    }
    if (st.launched && !gameOverShown && now - launchSeenAt > GAME_OVER_DELAY_MS) {
      gameOverShown = true;
      // race: a space launch ends the player's race (result = distance so far); the main button shows the results
      const race = mode()?.id === 'race';
      const label = race ? 'Results' : 'Reset';
      const verb = race ? 'see the results' : 'reset';
      const hint = input.source === 'touch' ? `Tap ${label}`
        : input.source === 'gamepad' && input.padId ? `Press ${input.glyph('select')} or ${input.glyph('reset')} to ${verb}`
          : `Press ${input.glyph('reset')} or Enter to ${verb}`;
      // the car's actual speed at the impact (the normal component only decides whether it launches)
      const hitSpeed = st.impact?.speed ?? st.impact?.speedNormal ?? 0;
      const mph = Math.round(hitSpeed * 2.236936);
      hud.showGameOver(hitSpeed, {
        resetLabel: label, hint,
        onReset: () => { mode()?.reset(); dirty = true; },
        onMenu: () => { hud.hideGameOver(); showMainMenu(); },
        ...(race ? {
          title: "YOU'RE OUT OF THE RACE",
          line: `You hit the wall at ${mph} mph and blasted into space. Your race ends at the distance you had covered.`,
          extra: [{ label: 'Race again (new seed)', run: () => { hud.hideGameOver(); modes.restart(); dirty = true; } }],
        } : {}),
      });
    }
    car.pose(st);
    marks.car(0, st, dt);
    car.setBrakeLights(hsim.input.brake > 0.05);
    mode()?.frame(dt, now);
    cams.setLook(input.lookX, input.lookY, input.lookBack);
    cams.update(car, dt, input.steer, st.speed);
    world.follow(car.root.position, cams.camera);
    audio.update(st, hsim.input.throttle); // load follows st.throttleOut; the pedal arms the rev-limiter stutter

    const mh = mode()?.hud() ?? { banner: null, timing: true, delta: null, showDelta: false };
    hud.setBanner(mh.banner);
    hud.update({
      speed: st.speed, gear: st.gear, rpm: st.rpm, autoShift: vehicle.autoShift,
      lapNumber: timer.lapNumber, started: timer.started, current: timer.current(hsim.simTime),
      last: timer.last, best: timer.best, delta: mh.delta,
      offTrack: st.wheels.some(wheelOff), invalid: timer.started && !timer.currentValid,
      absActive: st.absActive, timing: mh.timing, showDelta: mh.showDelta,
    });
    marks.update(dt, cams.camera, renderer.domElement.height);
    look.render(dt, st.speed);
  };

  const setMode = (id: ModeId) => {
    modes.set(id);
    running = true;
    wasPaused = true;
    dirty = true;
  };

  // debug handle for console / automated checks
  (window as unknown as Record<string, unknown>).__sim = {
    get vehicle() { return veh(); }, timer, cams, input, hud, world, renderer, audio, surface, track: track as TrackJson, menu,
    quality, touch, thinned, hotlap: hsim, loop, scoreboard: { client: scoreClient, ui: scoreUI },
    get mode() { return modes.current; },
    setMode: (id: ModeId) => { setMode(id); menu.close(); },
    setCamera,
  };

  return {
    frame,
    setMode,
    get running() { return running; },
    trackLength: track.length_m,
    markDirty() { dirty = true; },
    openPause,
    renderOnce() {
      rollingStart();
      ghosts.update(null, car.root.position);
      cams.update(car, 1, 0, 0);
      render();
    },
  };
}

void boot();
