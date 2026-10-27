// The look: a physical sky and sun (time of day from `?sun=az,el`), an environment map baked from that sky for
// every PBR material (cars; the ground on the desktop tier), sun-tinted height fog patched into three's fog
// shader chunks (so every material, instanced scenery and particles included, gets the same aerial perspective),
// and the desktop post stack: bloom, speed blur, ACES, a grade LUT, vignette and SMAA, with dynamic resolution
// against the frame time. The phone tier keeps the sky, environment and fog and renders straight to the canvas
// at a fixed resolution; `?post=0` does the same on desktop.
import * as THREE from 'three';
import { Sky } from 'three/examples/jsm/objects/Sky.js';
import {
  BlendFunction, BloomEffect, Effect, EffectAttribute, EffectComposer, EffectPass, LookupTexture, LUT3DEffect,
  RenderPass, SMAAEffect, SMAAPreset, ToneMappingEffect, ToneMappingMode, VignetteEffect,
} from 'postprocessing';
import { pixelRatioFor, type QualitySettings } from './quality';
import type { World } from './scene';

export interface SunSpec { azimuthDeg: number; elevationDeg: number }
/** Sunny Monterey afternoon (the look the track and cars were calibrated under): azimuth 235 (SW), elevation 38. */
export const SUN_DEFAULT: Readonly<SunSpec> = { azimuthDeg: 235, elevationDeg: 38 };
/** three's sky example sits at exposure 0.5; the scene is calibrated for ACES at exposure 1, so the sky's radiance is scaled. */
export const SKY_GAIN = 0.35;
/** Fog: extinction per metre at the reference height (≈7 % at 2.5 km, 14 % at 5 km) and its height falloff (1/m). */
export const FOG_DENSITY = 3.0e-5;
export const FOG_FALLOFF = 0.004;
/** IBL strength on PBR materials and the hemisphere fill left for the Lambert scenery, per tier. */
export const ENV_INTENSITY = 0.4;
export const HEMI_DESKTOP = 0.45;
export const HEMI_PHONE = 0.95;
/** Speed blur at the frame's edge: from SPEED_BLUR_FROM to full strength SPEED_BLUR_SPAN m/s later. */
export const SPEED_BLUR_FROM = 24;
export const SPEED_BLUR_SPAN = 36;
/** Dynamic resolution: ratio floor as a fraction of the tier's cap; frame-time target (ms) and its bands. */
export const DYN_MIN_FRACTION = 0.65;
export const DYN_TARGET_MS = 16.7;

const clamp = (v: number, a: number, b: number) => Math.max(a, Math.min(b, v));
const smooth = (a: number, b: number, x: number) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };

/** Pure: `?sun=az,el` in degrees (azimuth clockwise from north, elevation 1..89); anything else is the default. */
export function sunFromUrl(search: string): SunSpec {
  const v = new URLSearchParams(search).get('sun');
  if (!v) return { ...SUN_DEFAULT };
  const [a, e] = v.split(',').map(Number);
  return {
    azimuthDeg: Number.isFinite(a) ? ((a % 360) + 360) % 360 : SUN_DEFAULT.azimuthDeg,
    elevationDeg: Number.isFinite(e) ? clamp(e, 1, 89) : SUN_DEFAULT.elevationDeg,
  };
}

/** Direction toward the sun in three coordinates (X east, Y up, Z south). */
export function sunDirection(s: SunSpec, out = new THREE.Vector3()): THREE.Vector3 {
  const az = THREE.MathUtils.degToRad(s.azimuthDeg), el = THREE.MathUtils.degToRad(s.elevationDeg);
  const e = Math.sin(az) * Math.cos(el), n = Math.cos(az) * Math.cos(el), u = Math.sin(el);
  return out.set(e, u, -n).normalize();
}

export interface Lighting { sunColor: THREE.Color; sunIntensity: number; fogColor: THREE.Color; fogSun: THREE.Color; hemiSky: THREE.Color; hemiGround: THREE.Color; low: number }

/** Pure: sun, fog and fill colours for a sun elevation (deg). The default elevation reproduces the calibrated look. */
export function lightingFor(elevationDeg: number): Lighting {
  const low = 1 - smooth(4, 28, elevationDeg); // 0 with the sun high, 1 at the horizon
  const sunColor = new THREE.Color(0xffe7c8).lerp(new THREE.Color(0xff8a3c), low);
  const sunIntensity = 3.4 * (0.25 + 0.75 * clamp(Math.sin(THREE.MathUtils.degToRad(elevationDeg)) / Math.sin(THREE.MathUtils.degToRad(38)), 0, 1.15));
  const fogColor = new THREE.Color(0xc4d3e0).lerp(new THREE.Color(0xe3c7a8), low * 0.7);
  const fogSun = new THREE.Color(0xfff0d8).lerp(new THREE.Color(0xffb070), low);
  const hemiSky = new THREE.Color(0xb4cbe8).lerp(new THREE.Color(0xd9b89a), low * 0.6);
  const hemiGround = new THREE.Color(0x7a6448);
  return { sunColor, sunIntensity, fogColor, fogSun, hemiSky, hemiGround, low };
}

// ---------------------------------------------------------------- fog chunks

const CHUNK = THREE.ShaderChunk as unknown as Record<string, string>;
let fogPatched = false;

/**
 * Replace three's fog chunks with exponential height fog (density falls off above `heightM` with FOG_FALLOFF),
 * integrated along the view ray, tinted toward the sun's colour around the sun. Baked as constants: the sun is fixed
 * for a page load (`?sun=`), and a uniform added after three built its shader libraries would not reach the materials.
 * Must run before the first render; no-op in tests without a renderer.
 */
export function patchFogChunks(sunDir: THREE.Vector3, sunColor: THREE.Color, heightM: number, falloff = FOG_FALLOFF): void {
  const f = (x: number) => (Number.isFinite(x) ? x.toFixed(6) : '0.0');
  CHUNK.fog_pars_vertex = `#ifdef USE_FOG
	varying float vFogDepth;
	varying vec3 vFogWorld;
#endif`;
  CHUNK.fog_vertex = `#ifdef USE_FOG
	vFogDepth = - mvPosition.z;
	vFogWorld = cameraPosition + transpose( mat3( viewMatrix ) ) * mvPosition.xyz;
#endif`;
  CHUNK.fog_pars_fragment = `#ifdef USE_FOG
	uniform vec3 fogColor;
	varying float vFogDepth;
	varying vec3 vFogWorld;
	#ifdef FOG_EXP2
		uniform float fogDensity;
	#else
		uniform float fogNear;
		uniform float fogFar;
	#endif
	const vec3 lookFogSunDir = vec3( ${f(sunDir.x)}, ${f(sunDir.y)}, ${f(sunDir.z)} );
	const vec3 lookFogSunColor = vec3( ${f(sunColor.r)}, ${f(sunColor.g)}, ${f(sunColor.b)} );
	const float lookFogHeight = ${f(heightM)};
	const float lookFogFalloff = ${f(falloff)};
#endif`;
  CHUNK.fog_fragment = `#ifdef USE_FOG
	vec3 lookRay = vFogWorld - cameraPosition;
	float lookDist = length( lookRay );
	vec3 lookDir = lookRay / max( lookDist, 1e-3 );
	#ifdef FOG_EXP2
		float lookA = fogDensity * exp( - ( cameraPosition.y - lookFogHeight ) * lookFogFalloff );
		float lookDy = lookDir.y * lookFogFalloff;
		float lookInt = abs( lookDy ) > 1e-6 ? lookA * ( 1.0 - exp( - lookDist * lookDy ) ) / lookDy : lookA * lookDist;
		float fogFactor = 1.0 - exp( - min( lookInt, 20.0 ) );
	#else
		float fogFactor = smoothstep( fogNear, fogFar, vFogDepth );
	#endif
	float lookSun = pow( max( dot( lookDir, lookFogSunDir ), 0.0 ), 8.0 );
	gl_FragColor.rgb = mix( gl_FragColor.rgb, mix( fogColor, lookFogSunColor, lookSun ), clamp( fogFactor, 0.0, 1.0 ) );
#endif`;
  fogPatched = true;
}
export function fogChunksPatched(): boolean { return fogPatched; }

// ---------------------------------------------------------------- sky

/** A physical sky (three's Sky: Preetham scattering + clouds) lit by `dir`, scaled to the scene's exposure. */
export function makeSky(dir: THREE.Vector3, elevationDeg: number): Sky {
  const sky = new Sky();
  sky.scale.setScalar(450000);
  const low = 1 - smooth(4, 28, elevationDeg);
  const u = sky.material.uniforms;
  u.turbidity.value = 2.5 + 4 * low;
  u.rayleigh.value = 1.0 + 1.5 * low;
  u.mieCoefficient.value = 0.004 + 0.004 * low;
  u.mieDirectionalG.value = 0.85;
  u.sunPosition.value.copy(dir);
  u.cloudCoverage.value = 0.22;
  u.cloudDensity.value = 0.35;
  u.cloudElevation.value = 0.45;
  u.skyGain = { value: SKY_GAIN };
  const fs = sky.material.fragmentShader;
  const a = 'uniform float showSunDisc;', b = 'gl_FragColor = vec4( texColor, 1.0 );';
  if (fs.includes(a) && fs.includes(b)) {
    // the sun disc is capped so the bloom around it cannot pop as it enters or leaves the frame
    sky.material.fragmentShader = fs.replace(a, `${a}\nuniform float skyGain;`).replace(b, 'gl_FragColor = vec4( min( texColor * skyGain, vec3( 6.0 ) ), 1.0 );');
  } else console.warn('look: sky shader changed, radiance gain not applied');
  sky.frustumCulled = false;
  sky.renderOrder = -1;
  sky.name = 'sky';
  return sky;
}

/** PMREM environment from the sky plus a ground disc (dry ground at the radiance sunlit ground has in this scene). */
function bakeEnvironment(renderer: THREE.WebGLRenderer, dir: THREE.Vector3, elevationDeg: number, ground: THREE.Color): THREE.Texture {
  const pm = new THREE.PMREMGenerator(renderer);
  const s = new THREE.Scene();
  const sky = makeSky(dir, elevationDeg);
  const disc = new THREE.Mesh(new THREE.CircleGeometry(100000, 48).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: ground.clone().multiplyScalar(0.9) }));
  disc.position.y = -30;
  s.add(sky, disc);
  const rt = pm.fromScene(s, 0, 1, 1e6);
  pm.dispose();
  sky.material.dispose(); sky.geometry.dispose(); disc.geometry.dispose(); (disc.material as THREE.Material).dispose();
  return rt.texture;
}

// ---------------------------------------------------------------- post stack

/** Radial blur toward the frame's edge, strength 0..1 (set per frame from the car's speed). */
export class SpeedBlurEffect extends Effect {
  constructor() {
    super('SpeedBlurEffect', `uniform float strength;
void mainImage(const in vec4 inputColor, const in vec2 uv, out vec4 outputColor) {
	vec2 d = uv - 0.5;
	float m = smoothstep(0.2, 0.75, length(d)) * strength;
	if (m < 0.002) { outputColor = inputColor; return; }
	vec3 acc = inputColor.rgb;
	for (int i = 1; i <= 6; i++) { float t = float(i) / 6.0; acc += texture2D(inputBuffer, uv - d * m * 0.07 * t).rgb; }
	outputColor = vec4(acc / 7.0, inputColor.a);
}`, { blendFunction: BlendFunction.NORMAL, attributes: EffectAttribute.CONVOLUTION, uniforms: new Map([['strength', new THREE.Uniform(0)]]) });
  }
  set strength(v: number) { this.uniforms.get('strength')!.value = v; }
  get strength(): number { return this.uniforms.get('strength')!.value as number; }
}

/** Pure: the grade applied after tone mapping (values 0..1): a touch more saturation, warm highlights, cool shadows. */
export function grade(r: number, g: number, b: number): [number, number, number] {
  const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  const sat = 1.08;
  let R = lum + (r - lum) * sat, G = lum + (g - lum) * sat, B = lum + (b - lum) * sat;
  const t = smooth(0.05, 0.7, lum);
  R *= 0.965 + (1.035 - 0.965) * t; G *= 0.99 + (1.0 - 0.99) * t; B *= 1.045 + (0.945 - 1.045) * t;
  return [clamp(R, 0, 1), clamp(G, 0, 1), clamp(B, 0, 1)];
}

function gradeLut(size = 32): LookupTexture {
  const lut = LookupTexture.createNeutral(size);
  const d = lut.image.data as Float32Array;
  for (let i = 0; i < d.length; i += 4) { const [r, g, b] = grade(d[i], d[i + 1], d[i + 2]); d[i] = r; d[i + 1] = g; d[i + 2] = b; }
  lut.needsUpdate = true;
  return lut;
}

interface PostStack { composer: EffectComposer; speed: SpeedBlurEffect; dispose(): void }

function buildPost(renderer: THREE.WebGLRenderer, scene: THREE.Scene, camera: THREE.Camera): PostStack {
  const composer = new EffectComposer(renderer, { frameBufferType: THREE.HalfFloatType, multisampling: 0 });
  composer.addPass(new RenderPass(scene, camera));
  const speed = new SpeedBlurEffect();
  // only what is really bright blooms (the sun, lamps, paint highlights): the sky and haze must stay crisp
  const bloom = new BloomEffect({ mipmapBlur: true, luminanceThreshold: 1.3, luminanceSmoothing: 0.1, intensity: 0.3, radius: 0.55 });
  const tone = new ToneMappingEffect({ mode: ToneMappingMode.ACES_FILMIC });
  const lut = new LUT3DEffect(gradeLut());
  const vignette = new VignetteEffect({ offset: 0.32, darkness: 0.42 });
  const smaa = new SMAAEffect({ preset: SMAAPreset.HIGH });
  // convolution effects (speed blur, SMAA) each need their own pass; bloom reads the HDR frame before tone mapping
  composer.addPass(new EffectPass(camera, speed));
  composer.addPass(new EffectPass(camera, bloom, tone, lut, vignette));
  composer.addPass(new EffectPass(camera, smaa));
  return { composer, speed, dispose: () => composer.dispose() };
}

/** Pure: `?post=0` turns the post stack off. */
export function postUrlOff(search: string): boolean {
  const v = new URLSearchParams(search).get('post');
  return v === '0' || v === 'false';
}

// ---------------------------------------------------------------- dynamic resolution

/** Dynamic resolution: frames between decisions, and the cooldown after a change (a resize is a visible step). */
export const DYN_WINDOW = 40;
export const DYN_COOLDOWN = 150;

/** Pure controller: lowers the pixel ratio while frames run long, raises it back only when they are clearly quick. */
export class DynamicResolution {
  ratio: number;
  private ema = DYN_TARGET_MS;
  private frames = 0;
  private cooldown = 0;
  constructor(public min: number, public max: number, public targetMs = DYN_TARGET_MS) { this.ratio = max; }
  /** Feed one frame (ms); returns the new ratio when it changes (at most once per DYN_WINDOW frames, then a cooldown). */
  sample(frameMs: number): number | null {
    if (!(frameMs > 0) || frameMs > 100) return null; // hitch, tab switch or a paused frame
    this.ema += (frameMs - this.ema) * 0.08;
    if (this.cooldown > 0) { this.cooldown--; return null; }
    if (++this.frames < DYN_WINDOW) return null;
    this.frames = 0;
    let r = this.ratio;
    // wide hysteresis: down past 1.15 x target, up only below 0.8 x, so a frame time near the target never oscillates
    if (this.ema > this.targetMs * 1.15) r = Math.max(this.min, r * 0.88);
    else if (this.ema < this.targetMs * 0.8) r = Math.min(this.max, r * 1.06);
    if (Math.abs(r - this.ratio) < 1e-3) return null;
    this.ratio = r;
    this.cooldown = DYN_COOLDOWN;
    return r;
  }
}

// ---------------------------------------------------------------- the look

export interface LookOptions { sun?: SunSpec; post?: boolean; /** reference height of the fog (m, three Y) */ fogHeightM?: number }

export class Look {
  readonly sun: SunSpec;
  readonly sunDir = new THREE.Vector3();
  readonly lighting: Lighting;
  readonly sky: Sky;
  readonly post: PostStack | null;
  readonly dyn: DynamicResolution | null;
  private w = 1; private h = 1;
  /** adaptive quality (perf.ts): an upper bound on the pixel ratio, on top of the tier's budget */
  private ratioLimit = Infinity;
  private time = 0;

  constructor(private readonly renderer: THREE.WebGLRenderer, private readonly world: World, private readonly camera: THREE.PerspectiveCamera,
    private readonly q: QualitySettings, opts: LookOptions = {}) {
    this.sun = opts.sun ?? { ...SUN_DEFAULT };
    sunDirection(this.sun, this.sunDir);
    const L = (this.lighting = lightingFor(this.sun.elevationDeg));
    const scene = world.scene;
    // sun + fill
    world.sunDir.copy(this.sunDir);
    world.sun.color.copy(L.sunColor);
    world.sun.intensity = L.sunIntensity;
    world.hemi.color.copy(L.hemiSky);
    world.hemi.groundColor.copy(L.hemiGround);
    world.hemi.intensity = q.tier === 'phone' ? HEMI_PHONE : HEMI_DESKTOP;
    // sky, environment, fog
    this.sky = makeSky(this.sunDir, this.sun.elevationDeg);
    scene.add(this.sky);
    scene.environment = bakeEnvironment(renderer, this.sunDir, this.sun.elevationDeg, L.hemiGround);
    scene.environmentIntensity = ENV_INTENSITY;
    scene.background = L.fogColor.clone();
    scene.fog = new THREE.FogExp2(L.fogColor.clone(), FOG_DENSITY);
    patchFogChunks(this.sunDir, L.fogSun, opts.fogHeightM ?? 0);
    // post + dynamic resolution (desktop)
    const post = (opts.post ?? true) && q.tier !== 'phone';
    this.post = post ? buildPost(renderer, scene, camera) : null;
    const cap = pixelRatioFor(q, window.devicePixelRatio, window.innerWidth, window.innerHeight);
    this.dyn = post ? new DynamicResolution(cap * DYN_MIN_FRACTION, cap) : null;
    this.resize(window.innerWidth, window.innerHeight);
  }

  /** CSS-pixel viewport changed. */
  resize(w: number, h: number): void {
    this.w = w; this.h = h;
    const cap = Math.max(0.5, Math.min(pixelRatioFor(this.q, window.devicePixelRatio, w, h), this.ratioLimit));
    if (this.dyn) { this.dyn.max = cap; this.dyn.min = cap * DYN_MIN_FRACTION; this.dyn.ratio = Math.min(this.dyn.ratio, cap); }
    this.renderer.setPixelRatio(this.dyn ? this.dyn.ratio : cap);
    this.renderer.setSize(w, h);
    this.post?.composer.setSize(w, h, false);
  }

  /** Adaptive quality: cap the pixel ratio (Infinity: the tier's own cap) and re-fit the canvas now. */
  setRatioLimit(r: number): void {
    if (r === this.ratioLimit) return;
    this.ratioLimit = r;
    this.resize(this.w, this.h);
  }

  /** Current render pixel ratio (debug / tests). */
  get pixelRatio(): number { return this.renderer.getPixelRatio(); }

  /** Draw one frame. `dt` s since the last frame (0 for a repaint), `speed` the player's speed (m/s) for the blur. */
  render(dt: number, speed = 0): void {
    this.time += dt;
    this.sky.material.uniforms.time.value = this.time;
    if (!this.post) { this.renderer.render(this.world.scene, this.camera); return; }
    this.post.speed.strength = clamp((Math.abs(speed) - SPEED_BLUR_FROM) / SPEED_BLUR_SPAN, 0, 1) * 0.9;
    // resize BEFORE drawing: a resized canvas is cleared to black, so it has to be redrawn in the same frame
    // (owner, 18 Oct 2026: "the lighting flickers / suddenly goes dark" — one black frame per resolution step)
    const r = this.dyn!.sample(dt * 1000);
    if (r !== null) { this.renderer.setPixelRatio(r); this.post.composer.setSize(this.w, this.h, false); }
    this.post.composer.render(dt);
  }
}
