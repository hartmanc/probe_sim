// World: terrain from the heightfield, track ribbon, lights, fog (the sky, environment and the look live in look.ts),
// corner signboards (only without scenery.json). ENU -> three: X = x, Y = z, Z = -y.
import * as THREE from 'three';
import type { TrackJson } from './physics-types';
import { curvatures, halfWidths, tangentAt } from './trackmath';
import { SHOULDER_WIDTH_M } from '../physics';
import { buildScenery, paintWearTexture, type PaintSurface, type SceneryAssets } from './scenery';

// Sunny Monterey afternoon. Colours are sRGB hex; three converts them to linear.
const SKY_HORIZON = new THREE.Color(0xb9d0e6);
const HAZE = new THREE.Color(0xc4d3e0);
const TERRAIN_STEP_M = 3;
// direction toward the sun in three coordinates: azimuth 235 deg (SW), elevation 38 deg
export const SUN_DIR = (() => {
  const az = THREE.MathUtils.degToRad(235), el = THREE.MathUtils.degToRad(38);
  const e = Math.sin(az) * Math.cos(el), n = Math.cos(az) * Math.cos(el), u = Math.sin(el);
  return new THREE.Vector3(e, u, -n).normalize();
})();

// ------------------------------------------------------------------ close-range ground detail
export interface GroundDetail { albedo: THREE.Texture; normal: THREE.Texture; tile: number }

/** Tileable value noise on a 256 grid with `cells` lattice cells per tile. */
function tileNoise(N: number, cells: number, seed: number): Float32Array {
  const h = (i: number, j: number) => {
    const x = Math.sin(((i % cells + cells) % cells) * 127.1 + ((j % cells + cells) % cells) * 311.7 + seed * 74.7) * 43758.5453;
    return x - Math.floor(x);
  };
  const out = new Float32Array(N * N);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const fx = (x / N) * cells, fy = (y / N) * cells;
    const i = Math.floor(fx), j = Math.floor(fy);
    let u = fx - i, v = fy - j;
    u = u * u * (3 - 2 * u); v = v * v * (3 - 2 * v);
    out[y * N + x] = (h(i, j) * (1 - u) + h(i + 1, j) * u) * (1 - v) + (h(i, j + 1) * (1 - u) + h(i + 1, j + 1) * u) * v;
  }
  return out;
}

/**
 * Procedural detail maps (generated once at startup, 256 px per tile). Albedo is a grey multiplier around 0.5
 * (the shader uses 2 x value); the normal map is derived from the same height field.
 *  - asphalt: aggregate chips and binder pores at mm-cm scale, 0.8 m tile
 *  - ground: dry-grass stalks, clods and pebbles, 1.6 m tile
 */
export function makeGroundDetail(kind: 'asphalt' | 'ground', maxAniso: number): GroundDetail {
  const N = 256;
  let seed = kind === 'asphalt' ? 7 : 13;
  const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
  const H = new Float32Array(N * N);
  const A = new Float32Array(N * N);
  const n1 = tileNoise(N, kind === 'asphalt' ? 64 : 12, 1), n2 = tileNoise(N, kind === 'asphalt' ? 128 : 48, 2), n3 = tileNoise(N, 24, 3);
  for (let k = 0; k < N * N; k++) {
    H[k] = kind === 'asphalt' ? 0.6 * n1[k] + 0.4 * n2[k] : 0.5 * n1[k] + 0.3 * n2[k] + 0.2 * n3[k];
    A[k] = kind === 'asphalt' ? 0.5 + (n1[k] - 0.5) * 0.25 + (n2[k] - 0.5) * 0.2 : 0.5 + (n1[k] - 0.5) * 0.35 + (n2[k] - 0.5) * 0.2;
  }
  const put = (x: number, y: number, dh: number, da: number) => {
    const xi = ((Math.round(x) % N) + N) % N, yi = ((Math.round(y) % N) + N) % N;
    H[yi * N + xi] += dh; A[yi * N + xi] += da;
  };
  if (kind === 'asphalt') {
    // aggregate: light and dark stone chips, 1-3 px (4-10 mm), raised
    for (let c = 0; c < 9000; c++) {
      const x = rnd() * N, y = rnd() * N, r = 0.6 + rnd() * 1.4, light = rnd() < 0.45;
      const da = light ? 0.18 + rnd() * 0.2 : -0.12 - rnd() * 0.1;
      for (let dy = -2; dy <= 2; dy++) for (let dx = -2; dx <= 2; dx++) if (dx * dx + dy * dy <= r * r) put(x + dx, y + dy, 0.35, da);
    }
    // pores between the chips
    for (let c = 0; c < 4000; c++) put(rnd() * N, rnd() * N, -0.5, -0.12);
  } else {
    // dry grass: short stalks in random directions, pale and dark
    for (let c = 0; c < 2600; c++) {
      const x = rnd() * N, y = rnd() * N, ang = rnd() * Math.PI, len = 4 + rnd() * 10, light = rnd() < 0.6;
      const da = light ? 0.06 + rnd() * 0.08 : -0.12;
      for (let t = 0; t < len; t++) put(x + Math.cos(ang) * t, y + Math.sin(ang) * t, 0.25, da);
    }
    // pebbles and clods
    for (let c = 0; c < 700; c++) {
      const x = rnd() * N, y = rnd() * N, r = 1 + rnd() * 2.5, da = rnd() < 0.5 ? 0.15 : -0.15;
      for (let dy = -3; dy <= 3; dy++) for (let dx = -3; dx <= 3; dx++) if (dx * dx + dy * dy <= r * r) put(x + dx, y + dy, 0.5 * (1 - (dx * dx + dy * dy) / (r * r + 1)), da);
    }
  }
  const alb = new Uint8Array(N * N * 4), nor = new Uint8Array(N * N * 4);
  const strength = kind === 'asphalt' ? 2.2 : 2.0;
  const hAt = (x: number, y: number) => H[((y + N) % N) * N + ((x + N) % N)];
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const k = y * N + x;
    const a = Math.max(0, Math.min(1, A[k])) * 255;
    alb[k * 4] = alb[k * 4 + 1] = alb[k * 4 + 2] = a; alb[k * 4 + 3] = 255;
    const dx = (hAt(x + 1, y) - hAt(x - 1, y)) * strength, dy = (hAt(x, y + 1) - hAt(x, y - 1)) * strength;
    const l = Math.hypot(dx, dy, 1);
    nor[k * 4] = (-dx / l * 0.5 + 0.5) * 255; nor[k * 4 + 1] = (dy / l * 0.5 + 0.5) * 255; nor[k * 4 + 2] = (1 / l * 0.5 + 0.5) * 255; nor[k * 4 + 3] = 255;
  }
  const mk = (d: Uint8Array) => {
    const t = new THREE.DataTexture(d, N, N, THREE.RGBAFormat);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.generateMipmaps = true;
    t.minFilter = THREE.LinearMipmapLinearFilter;
    t.magFilter = THREE.LinearFilter;
    t.anisotropy = Math.min(8, maxAniso);
    t.needsUpdate = true;
    return t;
  };
  return { albedo: mk(alb), normal: mk(nor), tile: kind === 'asphalt' ? 0.8 : 1.6 };
}

/** World-space detail UVs in uv1 (for the normal map, channel 1). */
function addDetailUV(geo: THREE.BufferGeometry, tile: number): void {
  const p = geo.attributes.position as THREE.BufferAttribute;
  const uv1 = new Float32Array(p.count * 2);
  for (let i = 0; i < p.count; i++) { uv1[i * 2] = p.getX(i) / tile; uv1[i * 2 + 1] = -p.getZ(i) / tile; }
  geo.setAttribute('uv1', new THREE.BufferAttribute(uv1, 2));
}

/**
 * Photo-ground shading for ortho-textured surfaces: a tiled close-range detail layer (albedo multiplier + normal
 * map in world space, fading out between 30 and 80 m) over the 0.6 m/px imagery, and a mid-scale value-noise
 * mottle. With `asphaltAttr`, the per-vertex attribute `pgA` (1 on the racing surface, 0 on the shoulder) blends in
 * the asphalt grade (desaturate, darken, cool; painted lines kept) and the asphalt detail instead of the ground
 * detail, so the ribbon's shoulder looks exactly like the terrain it joins.
 */
export type GroundMaterial = THREE.MeshLambertMaterial | THREE.MeshStandardMaterial;
/** Desktop: physically shaded ground (sun sheen on the asphalt, environment fill); phone: Lambert. Set by buildWorld. */
let PBR_GROUND = false;
function groundMaterial(p: THREE.MeshLambertMaterialParameters, roughness = 0.95): GroundMaterial {
  return PBR_GROUND ? new THREE.MeshStandardMaterial({ ...p, metalness: 0, roughness }) : new THREE.MeshLambertMaterial(p);
}

export function photoGround(mat: GroundMaterial, opts: { grain?: number; ground: GroundDetail; asphalt?: GroundDetail; asphaltAttr?: boolean; paint?: THREE.Texture; rubber?: boolean; /** paved runoff: pale, sun-bleached asphalt, not the dark racing surface */ runoff?: boolean;
  /** concrete paving (a closed road the captures show as concrete): pale grey, painted lines kept */ concrete?: boolean }): void {
  const grain = opts.grain ?? 0.12;
  const G = opts.ground, A = opts.asphalt;
  const hasA = opts.asphaltAttr && A ? 1 : 0;
  // painted overlay (kerbs, verge paint, edge lines): needs the asphalt attributes plus `pgPaintUv`
  const hasP = hasA && opts.paint ? 1 : 0;
  // rubbered racing line: needs `pgD` (lateral offset from the line, m)
  const hasR = hasA && opts.rubber ? 1 : 0;
  // paved runoff zones: the real ones are pale grey (GPT judge, 18 Oct 2026: "dark asphalt lobes in the T9/T10 runoff")
  const hasO = hasA && opts.runoff ? 1 : 0;
  const hasC = hasA && opts.concrete ? 1 : 0;
  mat.normalMap = G.normal;   // uv1 = world / G.tile (see addDetailUV); gives the tangent frame
  G.normal.channel = 1;
  mat.normalScale.set(1, 1);
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.pgAlbG = { value: G.albedo };
    sh.uniforms.pgTileG = { value: G.tile };
    sh.uniforms.pgAlbA = { value: A?.albedo ?? G.albedo };
    sh.uniforms.pgNorA = { value: A?.normal ?? G.normal };
    sh.uniforms.pgTileA = { value: A?.tile ?? G.tile };
    sh.uniforms.pgPaint = { value: opts.paint ?? G.albedo };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', `#include <common>
varying vec3 vPgW;
varying float vPgA;
varying float vPgE;
varying vec2 vPgUvSrc;
varying vec2 vPgPaintUv;
varying float vPgD;
${hasA ? 'attribute float pgA; attribute float pgE; attribute vec2 pgUvSrc;' : ''}
${hasP ? 'attribute vec2 pgPaintUv;' : ''}
${hasR ? 'attribute float pgD;' : ''}`)
      .replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
vPgW = (modelMatrix * vec4(transformed, 1.0)).xyz;
vPgA = ${hasA ? 'pgA' : '0.0'};
vPgE = ${hasA ? 'pgE' : '0.0'};
vPgUvSrc = ${hasA ? 'pgUvSrc' : 'vec2(0.0)'};
vPgPaintUv = ${hasP ? 'pgPaintUv' : 'vec2(0.0)'};
vPgD = ${hasR ? 'pgD' : '1000.0'};`);
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
varying vec3 vPgW;
varying float vPgA;
varying float vPgE;
varying vec2 vPgUvSrc;
varying vec2 vPgPaintUv;
varying float vPgD;
float pgRub = 0.0;
uniform sampler2D pgAlbG, pgAlbA, pgNorA, pgPaint;
uniform float pgTileG, pgTileA;
float pgHash(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float pgNoise(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(pgHash(i), pgHash(i + vec2(1, 0)), f.x), mix(pgHash(i + vec2(0, 1)), pgHash(i + vec2(1, 1)), f.x), f.y); }
float pgFade() { return 1.0 - smoothstep(30.0, 80.0, length(vPgW - cameraPosition)); }
// de-tiled sampling: a second sample, rotated and rescaled, blended in by a ~25 m noise so no tile repeats in step
const mat2 pgR = mat2(0.80, -0.60, 0.60, 0.80);
const mat2 pgRi = mat2(0.80, 0.60, -0.60, 0.80);
float pgTileK(vec2 uv) { return smoothstep(0.35, 0.65, pgNoise(uv * 0.07)); }
vec4 pgTile(sampler2D t, vec2 uv) { return mix(texture2D(t, uv), texture2D(t, pgR * uv * 0.63 + vec2(0.37, 0.21)), pgTileK(uv)); }
vec3 pgTileN(sampler2D t, vec2 uv) {
  vec3 n1 = texture2D(t, uv).xyz * 2.0 - 1.0;
  vec3 n2 = texture2D(t, pgR * uv * 0.63 + vec2(0.37, 0.21)).xyz * 2.0 - 1.0;
  n2.xy = pgRi * n2.xy;
  return mix(n1, n2, pgTileK(uv));
}`)
      .replace('#include <map_fragment>', `#include <map_fragment>
{
  vec2 wp = vPgW.xz;
  vec2 wuv = vec2(vPgW.x, -vPgW.z);
  float w = clamp(vPgA, 0.0, 1.0);
  float pgPa = 0.0;
  float n = pgNoise(wp * 1.3) * 0.5 + pgNoise(wp * 0.35) * 0.3 + pgNoise(wp * 0.09) * 0.2;
  diffuseColor.rgb *= 1.0 + (n - 0.5) * ${grain.toFixed(3)};
#if ${hasA}
  {
    // near the edge, take the image from 1.2 m away (inward on asphalt, outward on the shoulder): the 0.6 m/px
    // aerial smears asphalt and dirt into each other right at the edge
    float e = smoothstep(0.0, 0.5, vPgE);
    diffuseColor.rgb = mix(diffuseColor.rgb, diffuse * texture2D(map, vPgUvSrc).rgb, e);
    // first metre of shoulder: packed dirt / fine gravel, a little darker and greyer than the open dirt
    if (w < 0.5) {
      float lg = dot(diffuseColor.rgb, vec3(0.2126, 0.7152, 0.0722));
      diffuseColor.rgb = mix(diffuseColor.rgb, mix(diffuseColor.rgb, vec3(lg), 0.25) * 0.8, e);
    }
    float l = dot(diffuseColor.rgb, vec3(0.2126, 0.7152, 0.0722));
    // painted lines (bright) keep their value, the rest of the surface becomes a dark cool asphalt
    float paint = smoothstep(0.58, 0.80, l);
    vec3 asph = vec3(min(l, 0.5)) * vec3(0.50, 0.53, 0.58) + vec3(0.004, 0.005, 0.007);
    diffuseColor.rgb = mix(diffuseColor.rgb, mix(asph, vec3(l) * 1.05, paint), w);
#if ${hasO}
    // paved runoff keeps the aerial photo's own colour (the sources disagree on its tone: the 2026 footage shows
    // asphalt, the satellite tan), so it reads as whatever the imagery shows, with only a little asphalt grade
    diffuseColor.rgb = mix(diffuseColor.rgb, diffuse * texture2D(map, vPgUvSrc).rgb * mix(1.0, 0.92, w), 0.85 * w);
#endif
#if ${hasC}
    // concrete paving: a pale grey that keeps the photo's local light / dark, painted lines kept
    vec3 conc = vec3(0.55, 0.55, 0.52) * (0.9 + 0.35 * (min(l, 0.6) - 0.3));
    diffuseColor.rgb = mix(diffuseColor.rgb, mix(conc, vec3(l) * 1.05, paint), w);
#endif
#if ${hasR}
    // rubber on the racing line: two darker strips at the tyre tracks over a wider, lighter darkening
    {
      float rub = 0.75 * (exp(-pow((vPgD - 0.75) / 0.42, 2.0)) + exp(-pow((vPgD + 0.75) / 0.42, 2.0))) + 0.3 * exp(-pow(vPgD / 1.3, 2.0));
      pgRub = clamp(rub, 0.0, 1.0) * w * (0.7 + 0.3 * pgNoise(wp * 0.15)) * (1.0 - paint);
      diffuseColor.rgb *= 1.0 - 0.3 * pgRub;
    }
#endif
#if ${hasP}
    // paint laid on that graded surface: it keeps the aerial's local light/dark (shade, dirt, rubber) relative to
    // the mean asphalt tone, so kerbs and lines sit in the same photograph as the road
    vec4 pt = texture2D(pgPaint, vPgPaintUv);
    float sh = clamp(dot(diffuseColor.rgb, vec3(0.2126, 0.7152, 0.0722)) / 0.06, 0.85, 1.15);
    diffuseColor.rgb = mix(diffuseColor.rgb, pt.rgb * sh, pt.a);
    pgPa = pt.a;
#endif
  }
#endif
  float dG = pgTile(pgAlbG, wuv / pgTileG).r * 2.0;
  float dA = pgTile(pgAlbA, wuv / pgTileA).r * 2.0;
  diffuseColor.rgb *= mix(1.0, mix(dG, dA, w), pgFade() * mix(0.5, 0.9, w) * (1.0 - 0.45 * pgPa));
}`)
      .replace('#include <roughnessmap_fragment>', `#include <roughnessmap_fragment>
  roughnessFactor = mix(roughnessFactor, 0.72, clamp(vPgA, 0.0, 1.0)) - 0.2 * pgRub;`)
      .replace('#include <normal_fragment_maps>', `
#ifdef USE_NORMALMAP_TANGENTSPACE
  {
    vec2 wuvN = vec2(vPgW.x, -vPgW.z);
    vec3 nG = pgTileN(normalMap, vNormalMapUv);
    vec3 nA = pgTileN(pgNorA, wuvN / pgTileA);
    vec3 mapN = mix(nG, nA, clamp(vPgA, 0.0, 1.0));
    mapN.xy *= normalScale * pgFade();
    normal = normalize(tbn * mapN);
  }
#endif`);
  };
  mat.customProgramCacheKey = () => `pg${hasA}${hasP}${hasR}${hasO}${hasC}${grain}`;
}

export interface World {
  scene: THREE.Scene;
  sun: THREE.DirectionalLight;
  hemi: THREE.HemisphereLight;
  /** Direction toward the sun (three coordinates); the Look (look.ts) sets it for the time of day. */
  sunDir: THREE.Vector3;
  /** Ribbon/terrain seam check (see seamReport), for debugging from the console. */
  seam: SeamReport;
  /** Keep the sun's shadow box on the car. */
  follow(target: THREE.Vector3, camera?: THREE.Camera): void;
}

function orthoUV(track: TrackJson, x: number, y: number): [number, number] {
  const o = track.ortho;
  return [(x - o.x0) / (o.x1 - o.x0), (y - o.y0) / (o.y1 - o.y0)];
}

/** Shoulder rows outside each edge (m beyond the edge); the last one lies on the terrain mesh. */
const SHOULDER_D = [0.5, 1.0, 1.75, 2.5, 3.5, SHOULDER_WIDTH_M]; // dense enough to follow the smoothstep blend over 2 m terrain detail
/** How far terrain vertices under the ribbon/shoulder are pushed below it (tapering to 0 at the shoulder's outer line). */
const TERRAIN_SINK_M = 0.3;

type Ground = (x: number, y: number) => number;

/** Bilinear heightfield (same as the physics' off-track interpolant). */
function hfSampler(track: TrackJson, hf: Float32Array): Ground {
  const h = track.heightfield;
  return (x, y) => {
    let fx = (x - h.x0) / h.dx, fy = (y - h.y0) / h.dx;
    fx = Math.min(Math.max(fx, 0), h.nx - 1.000001); fy = Math.min(Math.max(fy, 0), h.ny - 1.000001);
    const j = Math.floor(fx), i = Math.floor(fy), tx = fx - j, ty = fy - i, k = i * h.nx + j;
    const za = hf[k] + tx * (hf[k + 1] - hf[k]), zb = hf[k + h.nx] + tx * (hf[k + h.nx + 1] - hf[k + h.nx]);
    return za + ty * (zb - za);
  };
}

export interface SeamReport { maxEdgeGap: number; maxPoke: number; pokeAtS: number; pokeOuter: boolean; over2cm: number; maxPokeInner: number; /** 0 = track, 1.. = pit-lane parts; pokeAtS is that ribbon's station */ pokeRibbon: number }

interface TerrainGrid {
  zgrid: Float32Array; cols: number; rows: number; cell: number;
  /** Height of the rendered terrain surface (same triangulation as the mesh index buffer). */
  surfaceZ: Ground;
  /** Lower the three vertices of the terrain triangle under (x, y) by dz. */
  lowerAt(x: number, y: number, dz: number): void;
}

function terrainGrid(track: TrackJson, hf: Float32Array, ground: Ground, strands: Strand[]): TerrainGrid {
  const h = track.heightfield;
  const step = Math.max(1, Math.round(TERRAIN_STEP_M / h.dx));
  const cols = Math.floor((h.nx - 1) / step) + 1;
  const rows = Math.floor((h.ny - 1) / step) + 1;
  const zgrid = new Float32Array(cols * rows);
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) zgrid[r * cols + c] = hf[(r * step) * h.nx + c * step];
  const cell = h.dx * step;
  // Sink terrain vertices under the ribbon + shoulder footprint just below that surface, so nothing pokes through on
  // crests or banking. The sink tapers to zero at the shoulder's outer line, where the shoulder is stitched onto
  // this mesh. Each vertex is assigned to the station it is most nearly abeam of.
  // per strand (track, pit-lane parts): distance beyond the paved edge of each vertex, from the station it is most
  // nearly abeam of; a vertex takes the smallest over all strands
  const best = new Float32Array(cols * rows).fill(Infinity);
  const along = new Float32Array(cols * rows);
  const dOut = new Float32Array(cols * rows);
  for (const st of strands) {
    along.fill(Infinity);
    for (let i = 0; i < st.n; i++) {
      const f = st.at(i);
      const tx = f.ny, ty = -f.nx; // tangent from the left normal (nx, ny) = (-ty, tx)
      for (let lat = -(f.hr + SHOULDER_WIDTH_M + cell); lat <= f.hl + SHOULDER_WIDTH_M + cell; lat += cell * 0.5) {
        const x = f.cx + f.nx * lat, y = f.cy + f.ny * lat;
        const c0 = Math.floor((x - h.x0) / cell), r0 = Math.floor((y - h.y0) / cell);
        for (let dr = 0; dr <= 1; dr++) for (let dc = 0; dc <= 1; dc++) {
          const cc = c0 + dc, rr = r0 + dr;
          if (cc < 0 || rr < 0 || cc >= cols || rr >= rows) continue;
          const k = rr * cols + cc;
          const vx = h.x0 + cc * cell - f.cx, vy = h.y0 + rr * cell - f.cy;
          const al = Math.abs(vx * tx + vy * ty);
          if (al < along[k]) {
            along[k] = al;
            const vl = vx * f.nx + vy * f.ny;
            dOut[k] = vl >= 0 ? vl - f.hl : -vl - f.hr;
          }
        }
      }
    }
    for (let k = 0; k < cols * rows; k++) if (along[k] <= cell && dOut[k] < best[k]) best[k] = dOut[k];
  }
  for (let k = 0; k < cols * rows; k++) dOut[k] = best[k];
  for (let k = 0; k < cols * rows; k++) {
    if (!(dOut[k] < SHOULDER_WIDTH_M)) continue;
    const x = h.x0 + (k % cols) * cell, y = h.y0 + Math.floor(k / cols) * cell;
    const sink = TERRAIN_SINK_M * Math.min(1, Math.max(0, (SHOULDER_WIDTH_M - dOut[k]) / 1.5));
    zgrid[k] = Math.min(zgrid[k], ground(x, y) - sink);
  }
  const locate = (x: number, y: number): [number, number, number, number, number] => {
    let fx = (x - h.x0) / cell, fy = (y - h.y0) / cell;
    fx = Math.min(Math.max(fx, 0), cols - 1.000001); fy = Math.min(Math.max(fy, 0), rows - 1.000001);
    const c = Math.floor(fx), r = Math.floor(fy);
    return [c, r, fx - c, fy - r, r * cols + c];
  };
  return {
    zgrid, cols, rows, cell,
    surfaceZ(x, y) {
      const [, , u, v, a] = locate(x, y);
      const za = zgrid[a], zb = zgrid[a + 1], zd = zgrid[a + cols], ze = zgrid[a + cols + 1];
      return u + v <= 1 ? za + u * (zb - za) + v * (zd - za) : ze + (1 - u) * (zd - ze) + (1 - v) * (zb - ze);
    },
    lowerAt(x, y, dz) {
      const [, , u, v, a] = locate(x, y);
      const tri = u + v <= 1 ? [a, a + 1, a + cols] : [a + 1, a + cols + 1, a + cols];
      for (const k of tri) zgrid[k] -= dz;
    },
  };
}

function terrainMesh(track: TrackJson, g: TerrainGrid, tex: THREE.Texture, detail: GroundDetail): THREE.Mesh {
  const h = track.heightfield;
  const { cols, rows, cell, zgrid } = g;
  const pos = new Float32Array(cols * rows * 3);
  const uv = new Float32Array(cols * rows * 2);
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const x = h.x0 + c * cell, y = h.y0 + r * cell, z = zgrid[r * cols + c];
    const k = r * cols + c;
    pos[k * 3] = x; pos[k * 3 + 1] = z; pos[k * 3 + 2] = -y;
    const [u, v] = orthoUV(track, x, y);
    uv[k * 2] = u; uv[k * 2 + 1] = v;
  }
  const idx = new Uint32Array((cols - 1) * (rows - 1) * 6);
  let p = 0;
  for (let r = 0; r < rows - 1; r++) for (let c = 0; c < cols - 1; c++) {
    const a = r * cols + c, b = a + 1, d = a + cols, e = d + 1;
    // winding so normals face +Y (three Z = -y flips handedness); split along the b-d diagonal (as surfaceZ)
    idx[p++] = a; idx[p++] = b; idx[p++] = d;
    idx[p++] = b; idx[p++] = e; idx[p++] = d;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geo.setIndex(new THREE.BufferAttribute(idx, 1));
  geo.computeVertexNormals();
  addDetailUV(geo, detail.tile);
  const mat = groundMaterial({ map: tex }, 0.95);
  photoGround(mat, { grain: 0.16, ground: detail });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.receiveShadow = true;
  mesh.name = 'terrain';
  return mesh;
}

interface RibbonSections {
  K: number;               // columns per station
  n: number;               // stations
  closed: boolean;         // the track loops; pit-lane parts do not
  pos: Float32Array;       // ENU x, y, z per vertex (n x K)
  A: Float32Array;         // 1 = racing surface, 0 = shoulder (hard switch at the duplicated edge columns)
  E: Float32Array;         // near-edge weight: 1 at the edge, 0 at 0.5 m inside / 1.5 m outside
  src: Float32Array;       // ENU x, y to sample the aerial image from near the edge (1.2 m away from the blurred edge)
  D?: Float32Array;        // lateral offset from the racing line (m, +left); the track ribbon only
}

/** A ribbon's stations: the closed track, or an open pit-lane part. Gaps are the free width beyond each edge before
 *  another paved surface (Infinity for the track); shoulders are squeezed into smaller gaps. */
interface StationFrame { cx: number; cy: number; nx: number; ny: number; hl: number; hr: number; gapL: number; gapR: number }
interface Strand { n: number; closed: boolean; fractions: number[]; at(i: number): StationFrame }

function trackStrand(track: TrackJson): Strand {
  return {
    n: track.n, closed: true, fractions: track.profile.fractions,
    at(i) {
      const c = track.center[i];
      const [tx, ty] = tangentAt(track, i);
      const [hl, hr] = halfWidths(track, i);
      return { cx: c[0], cy: c[1], nx: -ty, ny: tx, hl, hr, gapL: Infinity, gapR: Infinity };
    },
  };
}

type PitPart = NonNullable<NonNullable<SceneryAssets['json']['pit_lane']>['parts']>[number];

function pitStrand(part: PitPart, fractions: number[]): Strand {
  return {
    n: part.n, closed: false, fractions,
    at(i) {
      const c = part.center[i];
      const a = part.center[Math.max(0, i - 1)], b = part.center[Math.min(part.n - 1, i + 1)];
      const tx = b[0] - a[0], ty = b[1] - a[1], l = Math.hypot(tx, ty) || 1;
      const L = part.left[i], R = part.right[i];
      return {
        cx: c[0], cy: c[1], nx: -ty / l, ny: tx / l,
        hl: Math.hypot(L[0] - c[0], L[1] - c[1]), hr: Math.hypot(R[0] - c[0], R[1] - c[1]),
        gapL: part.gap_left[i], gapR: part.gap_right[i],
      };
    },
  };
}

/** Columns: left shoulder (outermost first), left edge twice (shoulder side, then track side), a column 0.5 m inside
 *  the edge, the profile's interior columns, the same mirrored on the right. Racing-surface columns are placed as
 *  the physics maps the profile (lateral = -f x that side's half-width from the centre station); heights come from
 *  `ground` (the physics surface); the outermost shoulder rows lie on the terrain mesh. */
function ribbonSections(st: Strand, ground: Ground, terrainZ: Ground, lineOff?: (i: number) => number): RibbonSections {
  const n = st.n, S = SHOULDER_D.length;
  const fr = st.fractions;
  const interior = fr.filter((f) => f > fr[0] && f < fr[fr.length - 1]);
  // lateral plan per station: [lat, A, E, srcShift] with lat +left; built per station because half-widths vary
  type Col = [number, number, number, number];
  const squeeze = (gap: number) => (gap >= SHOULDER_WIDTH_M ? 1 : Math.max(0, gap - 0.05) / SHOULDER_WIDTH_M);
  const plan = (hl: number, hr: number, gL: number, gR: number): Col[] => {
    const cols: Col[] = [];
    const qL = squeeze(gL), qR = squeeze(gR);
    for (let k = S - 1; k >= 0; k--) { const d = SHOULDER_D[k]; cols.push([hl + d * qL, 0, d <= 0.5 ? 1 : 0, d <= 0.5 ? 1.2 : 0]); }
    cols.push([hl, 0, 1, 1.2], [hl, 1, 1, -1.2], [hl - 0.5, 1, 0, 0]);
    for (const f of interior) {
      const lat = -f * (f < 0 ? hl : hr);
      if (lat < hl - 0.6 && lat > -(hr - 0.6)) cols.push([lat, 1, 0, 0]);
    }
    cols.push([-(hr - 0.5), 1, 0, 0], [-hr, 1, 1, 1.2], [-hr, 0, 1, -1.2]);
    for (let k = 0; k < S; k++) { const d = SHOULDER_D[k]; cols.push([-(hr + d * qR), 0, d <= 0.5 ? 1 : 0, d <= 0.5 ? -1.2 : 0]); }
    return cols;
  };
  const K = plan(5, 5, Infinity, Infinity).length;
  const pos = new Float32Array(n * K * 3), A = new Float32Array(n * K), E = new Float32Array(n * K), src = new Float32Array(n * K * 2);
  const D = lineOff ? new Float32Array(n * K) : undefined;
  for (let i = 0; i < n; i++) {
    const f = st.at(i);
    let cols = plan(f.hl, f.hr, f.gapL, f.gapR);
    // keep the column count fixed: pad/trim interior columns if a very narrow station drops one
    while (cols.length < K) cols.splice(S + 3, 0, cols[S + 3]);
    if (cols.length > K) cols = cols.slice(0, S + 3).concat(cols.slice(cols.length - (K - S - 3)));
    cols.forEach(([lat, a, e, shift], k) => {
      const q = i * K + k;
      const x = f.cx + f.nx * lat, y = f.cy + f.ny * lat;
      const outer = k === 0 || k === K - 1;
      pos[q * 3] = x; pos[q * 3 + 1] = y; pos[q * 3 + 2] = outer ? terrainZ(x, y) : ground(x, y);
      A[q] = a; E[q] = e;
      if (D) D[q] = lat - lineOff!(i);
      // source point for the aerial image: `shift` is along +lat (left), already signed outward/inward per column
      src[q * 2] = f.cx + f.nx * (lat + shift);
      src[q * 2 + 1] = f.cy + f.ny * (lat + shift);
    });
  }
  return { K, n, closed: st.closed, pos, A, E, src, D };
}

/** Visit sample points on every ribbon quad (both triangles, interior points and edge midpoints). */
function forRibbonSamples(rs: RibbonSections, fn: (x: number, y: number, z: number, i: number, outer: boolean) => void): void {
  const n = rs.n, K = rs.K, sec = rs.pos;
  const W = [[1 / 3, 1 / 3], [0.5, 0], [0, 0.5], [0.5, 0.5], [0.15, 0.15], [0.7, 0.15], [0.15, 0.7]];
  for (let i = 0; i < (rs.closed ? n : n - 1); i++) {
    const j = (i + 1) % n;
    for (let k = 0; k < K - 1; k++) {
      const a = (i * K + k) * 3, b = (i * K + k + 1) * 3, c = (j * K + k) * 3, d = (j * K + k + 1) * 3;
      for (const [p0, p1, p2] of [[a, b, c], [b, d, c]]) {
        for (const [u, v] of W) {
          const w0 = 1 - u - v;
          fn(sec[p0] * w0 + sec[p1] * u + sec[p2] * v, sec[p0 + 1] * w0 + sec[p1 + 1] * u + sec[p2 + 1] * v,
            sec[p0 + 2] * w0 + sec[p1 + 2] * u + sec[p2 + 2] * v, i, k === 0 || k === K - 2);
        }
      }
    }
  }
}

/**
 * Track ribbon (see ribbonSections). The racing surface ends at a hard line: the edge columns are duplicated, so the
 * asphalt grade/detail switch to the terrain look exactly at the edge. Within 0.5 m of the edge the aerial image is
 * sampled 1.2 m away from it (inward on the asphalt, outward on the shoulder), because at 0.6 m/px it smears asphalt
 * and dirt into each other; the first metre of shoulder is darkened like packed dirt/gravel.
 */
function buildRibbon(track: TrackJson, tex: THREE.Texture, rs: RibbonSections, asphalt: GroundDetail, groundDetail: GroundDetail, name = 'track', offsetUnits = -2, runoff = false, concrete = false): THREE.Mesh {
  const n = rs.n, K = rs.K;
  const pos = new Float32Array(n * K * 3);
  const uv = new Float32Array(n * K * 2);
  const uvSrc = new Float32Array(n * K * 2);
  for (let q = 0; q < n * K; q++) {
    const x = rs.pos[q * 3], y = rs.pos[q * 3 + 1];
    pos[q * 3] = x; pos[q * 3 + 1] = rs.pos[q * 3 + 2]; pos[q * 3 + 2] = -y;
    const [u, v] = orthoUV(track, x, y);
    uv[q * 2] = u; uv[q * 2 + 1] = v;
    const [us, vs] = orthoUV(track, rs.src[q * 2], rs.src[q * 2 + 1]);
    uvSrc[q * 2] = us; uvSrc[q * 2 + 1] = vs;
  }
  const segs = rs.closed ? n : n - 1;
  const idx = new Uint32Array(segs * (K - 1) * 6);
  let p = 0;
  for (let i = 0; i < segs; i++) {
    const j = (i + 1) % n;
    for (let k = 0; k < K - 1; k++) {
      const a = i * K + k, b = i * K + k + 1, c = j * K + k, d = j * K + k + 1;
      // left->right across, i->j along driving direction; face up
      idx[p++] = a; idx[p++] = b; idx[p++] = c;
      idx[p++] = b; idx[p++] = d; idx[p++] = c;
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
  geo.setAttribute('pgA', new THREE.BufferAttribute(rs.A, 1));
  geo.setAttribute('pgE', new THREE.BufferAttribute(rs.E, 1));
  geo.setAttribute('pgUvSrc', new THREE.BufferAttribute(uvSrc, 2));
  if (rs.D) geo.setAttribute('pgD', new THREE.BufferAttribute(rs.D, 1));
  geo.setIndex(new THREE.BufferAttribute(idx, 1));
  geo.computeVertexNormals();
  addDetailUV(geo, groundDetail.tile);
  const mat = groundMaterial({ map: tex, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: offsetUnits }, 0.9);
  photoGround(mat, { grain: 0.12, ground: groundDetail, asphalt, asphaltAttr: true, rubber: !!rs.D, runoff, concrete });
  const mesh = new THREE.Mesh(geo, mat);
  mesh.receiveShadow = true;
  mesh.name = name;
  return mesh;
}

/** Seam diagnostics (metres): outer shoulder rows vs the terrain mesh, and the worst poke-through of terrain above
 *  the ribbon/shoulder over the whole lap. */
function seamReport(rss: RibbonSections[], terrainZ: Ground): SeamReport {
  let maxEdgeGap = 0, maxPoke = -Infinity, pokeAtS = 0, pokeOuter = false, over2cm = 0, maxPokeInner = -Infinity, pokeRibbon = 0;
  rss.forEach((rs, r) => {
    const K = rs.K, sec = rs.pos;
    for (let i = 0; i < rs.n; i++) {
      for (const k of [0, K - 1]) {
        const q = (i * K + k) * 3;
        maxEdgeGap = Math.max(maxEdgeGap, Math.abs(sec[q + 2] - terrainZ(sec[q], sec[q + 1])));
      }
    }
    forRibbonSamples(rs, (x, y, z, i, outer) => {
      const poke = terrainZ(x, y) - z;
      if (poke > 0.02) over2cm++;
      if (!outer) maxPokeInner = Math.max(maxPokeInner, poke);
      if (poke > maxPoke) { maxPoke = poke; pokeAtS = i; pokeOuter = outer; pokeRibbon = r; }
    });
  });
  return { maxEdgeGap, maxPoke, pokeAtS, pokeOuter, over2cm, maxPokeInner, pokeRibbon };
}

/** Painted track furniture (kerbs, verge paint, edge lines) shaded exactly like the ribbon: the graded aerial image
 *  and the asphalt detail under a paint layer (see photoGround `paint`). Geometry supplies pgA/pgE/pgUvSrc/pgPaintUv. */
function paintSurface(track: TrackJson, ortho: THREE.Texture, asphalt: GroundDetail, groundDetail: GroundDetail): PaintSurface {
  return {
    uv: (x, y) => orthoUV(track, x, y),
    mesh(geo, paint, name, offsetUnits) {
      addDetailUV(geo, groundDetail.tile);
      const mat = groundMaterial({ map: ortho, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: offsetUnits }, 0.9);
      photoGround(mat, { grain: 0.12, ground: groundDetail, asphalt, asphaltAttr: true, paint });
      const mesh = new THREE.Mesh(geo, mat);
      mesh.receiveShadow = true;
      mesh.name = name;
      return mesh;
    },
  };
}

/** Pit-lane paint: white edge lines wherever an edge is clear of the track (> 1 m gap), and pit boxes (transverse
 *  lines every 10 m across the garage-side half) along the part beside the front straight. 1 cm above the surface. */
function buildPitPaint(pit: NonNullable<SceneryAssets['json']['pit_lane']>, ground: Ground): THREE.Mesh | null {
  const pos: number[] = [], uv: number[] = [];
  const quad = (pts: [number, number][], u0: number, u1: number) => {
    const P = pts.map(([x, y]) => new THREE.Vector3(x, ground(x, y) + 0.01, -y));
    for (const [k, u, v] of [[0, u0, 0], [1, u0, 1], [2, u1, 0], [2, u1, 0], [1, u0, 1], [3, u1, 1]] as [number, number, number][]) {
      pos.push(P[k].x, P[k].y, P[k].z); uv.push(u, v);
    }
  };
  pit.parts.forEach((part, pi) => {
    const st = pitStrand(part, pit.fractions);
    const W = 0.12, IN = 0.15;
    for (let i = 0; i < part.n - 1; i++) {
      const a = st.at(i), b = st.at(i + 1);
      for (const side of [1, -1]) {
        const gap = side > 0 ? Math.min(a.gapL, b.gapL) : Math.min(a.gapR, b.gapR);
        if (!(gap > 1.0)) continue;
        const ha = side > 0 ? a.hl : a.hr, hb = side > 0 ? b.hl : b.hr;
        const pt = (f: StationFrame, h: number, o: number): [number, number] => [f.cx + f.nx * side * (h - o), f.cy + f.ny * side * (h - o)];
        quad([pt(a, ha, IN + W), pt(a, ha, IN), pt(b, hb, IN + W), pt(b, hb, IN)], i / 2, (i + 1) / 2);
      }
    }
    // pit boxes on the longer part (beside the front straight): garage side = the side further from the track
    if (pi !== 0) return;
    for (let i = 40; i < part.n - 40; i += 10) {
      const f = st.at(i), g = st.at(i + 1);
      const side = f.gapL > f.gapR ? 1 : -1;
      const h = side > 0 ? f.hl : f.hr;
      const tx = g.cx - f.cx, ty = g.cy - f.cy, l = Math.hypot(tx, ty) || 1;
      const ux = (tx / l) * 0.06, uy = (ty / l) * 0.06;
      const p0: [number, number] = [f.cx, f.cy], p1: [number, number] = [f.cx + f.nx * side * (h - 0.3), f.cy + f.ny * side * (h - 0.3)];
      quad([[p0[0] - ux, p0[1] - uy], [p0[0] + ux, p0[1] + uy], [p1[0] - ux, p1[1] - uy], [p1[0] + ux, p1[1] + uy]], 0, 1);
    }
  });
  if (!pos.length) return null;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
  g.computeVertexNormals();
  const mesh = new THREE.Mesh(g, new THREE.MeshLambertMaterial({ color: 0xf3f2ec, map: paintWearTexture(), side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -10 }));
  mesh.receiveShadow = true;
  mesh.name = 'pit_paint';
  return mesh;
}

function buildStartLine(track: TrackJson, ground: Ground): THREE.Mesh {
  // a 1 m band across the road at the S/F station, columns placed like the ribbon's, heights from the driven surface
  const i = track.start_finish?.index ?? 0;
  const fr = track.profile.fractions;
  const c = track.center[i];
  const [tx, ty] = tangentAt(track, i);
  const nx = -ty, ny = tx;
  const [hl, hr] = halfWidths(track, i);
  const pos: number[] = [];
  for (const along of [0, 1]) for (const f of fr) {
    const lat = -f * (f < 0 ? hl : hr);
    const x = c[0] + nx * lat + tx * along, y = c[1] + ny * lat + ty * along;
    pos.push(x, ground(x, y) + 0.01, -y);
  }
  const m = fr.length, idx: number[] = [];
  for (let k = 0; k < m - 1; k++) idx.push(k, k + 1, m + k, k + 1, m + k + 1, m + k);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  return new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ color: 0xf2f2f2, side: THREE.DoubleSide, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4 }));
}

function textSprite(text: string, sub: string): THREE.Sprite {
  const cv = document.createElement('canvas');
  cv.width = 1024; cv.height = 256;
  const g = cv.getContext('2d')!;
  g.fillStyle = 'rgba(14,18,24,0.88)';
  g.beginPath(); g.roundRect(8, 8, 1008, 240, 28); g.fill();
  g.strokeStyle = '#f2c230'; g.lineWidth = 10; g.stroke();
  g.fillStyle = '#ffffff';
  g.textAlign = 'center'; g.textBaseline = 'middle';
  let size = 104;
  g.font = `700 ${size}px system-ui, -apple-system, Segoe UI, sans-serif`;
  while (g.measureText(text).width > 950 && size > 40) { size -= 4; g.font = `700 ${size}px system-ui, -apple-system, Segoe UI, sans-serif`; }
  g.fillText(text, 512, 112);
  g.fillStyle = '#f2c230';
  g.font = '600 48px system-ui, -apple-system, Segoe UI, sans-serif';
  g.fillText(sub, 512, 204);
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: tex }));
  sp.scale.set(12, 3, 1);
  return sp;
}

function buildCornerSigns(track: TrackJson): THREE.Group {
  const group = new THREE.Group();
  group.name = 'corner_signs';
  const kap = curvatures(track, 15);
  const postMat = new THREE.MeshLambertMaterial({ color: 0x444444 });
  const postGeo = new THREE.CylinderGeometry(0.08, 0.08, 4, 6);
  track.corners.forEach((c, k) => {
    const i = Math.round(c.s / track.spacing_m) % track.n;
    const ctr = track.center[i];
    const tn = (() => { const a = track.center[(i - 1 + track.n) % track.n], b = track.center[(i + 1) % track.n]; const dx = b[0] - a[0], dy = b[1] - a[1], l = Math.hypot(dx, dy) || 1; return [dx / l, dy / l]; })();
    const nx = -tn[1], ny = tn[0];
    const [hl, hr] = halfWidths(track, i);
    // outside of the corner: right for a left-hander
    const side = (c.dir === 'left' ? 1 : c.dir === 'right' ? -1 : kap[i]) >= 0 ? -1 : 1;
    const off = side > 0 ? hl + 9 : -(hr + 9);
    const x = ctr[0] + nx * off, y = ctr[1] + ny * off;
    const z = ctr[2];
    const sp = textSprite(c.name, c.turn ? (c.turn === c.name ? '' : c.turn) : (c.turn === null ? '' : `Turn ${k + 1}`));
    sp.position.set(x, z + 5.5, -y);
    const post = new THREE.Mesh(postGeo, postMat);
    post.position.set(x, z + 2, -y);
    group.add(sp, post);
  });
  return group;
}

export interface WorldOptions {
  /** Physically shaded ground (desktop tier): sun sheen on the asphalt, environment fill. */
  pbr?: boolean;
  /** The racing line (ghosts.json `line`) for the rubbered band on the track. */
  line?: { s_grid_m: number; offset_m: number[] } | null;
}

/** Racing-line lateral offset (+left, m) at station i from ghosts.json's line (a coarser grid, wrapped). */
function lineOffsetFn(line: { s_grid_m: number; offset_m: number[] }, track: TrackJson): (i: number) => number {
  const g = line.s_grid_m, offs = line.offset_m, N = offs.length;
  return (i) => {
    const u = (i * track.spacing_m) / g, k = Math.floor(u), t = u - k;
    return offs[((k % N) + N) % N] * (1 - t) + offs[(((k + 1) % N) + N) % N] * t;
  };
}

export function buildWorld(track: TrackJson, hf: Float32Array, ortho: THREE.Texture, maxAniso: number, scenery?: SceneryAssets | null, groundIn?: Ground, opts: WorldOptions = {}): World {
  PBR_GROUND = !!opts.pbr;
  const lineOff = opts.line && opts.line.offset_m?.length ? lineOffsetFn(opts.line, track) : undefined;
  const scene = new THREE.Scene();
  scene.background = SKY_HORIZON.clone();
  // light aerial haze: ~9 % at 2.5 km, ~30 % at 5 km
  scene.fog = new THREE.FogExp2(HAZE.clone(), 1.2e-4);

  ortho.anisotropy = Math.min(16, maxAniso);
  ortho.wrapS = ortho.wrapT = THREE.ClampToEdgeWrapping;
  ortho.colorSpace = THREE.SRGBColorSpace;
  ortho.needsUpdate = true;

  const ground = groundIn ?? hfSampler(track, hf);
  const groundDetail = makeGroundDetail('ground', maxAniso);
  // ribbons: the track, then the pit-lane parts (scenery.json pit_lane)
  const pit = scenery?.json.pit_lane;
  const zones = scenery?.json.paved_zones;
  const strands: Strand[] = [
    trackStrand(track),
    ...(pit?.parts ?? []).filter((p) => p.n >= 2).map((p) => pitStrand(p, pit!.fractions)),
    ...(zones?.parts ?? []).filter((p) => p.n >= 2).map((p) => pitStrand(p, zones!.fractions)),
  ];
  const grid = terrainGrid(track, hf, ground, strands);
  // Stitch: the outer shoulder rows sit on the terrain; wherever the terrain still comes within 2 cm of a ribbon or
  // shoulder (a 4 m terrain triangle can reach under it from outside), lower that triangle and re-stitch.
  let secs = strands.map((st, k) => ribbonSections(st, ground, grid.surfaceZ, k === 0 ? lineOff : undefined));
  for (let it = 0; it < 8; it++) {
    let fixes = 0;
    for (const sec of secs) {
      forRibbonSamples(sec, (x, y, z, _i, outer) => {
        // the outermost shoulder quads touch the terrain along the stitch line, so only real poke-through counts there
        const poke = outer ? grid.surfaceZ(x, y) - z - 0.03 : grid.surfaceZ(x, y) - (z - 0.02);
        if (poke > 0) { grid.lowerAt(x, y, poke + 0.03); fixes++; }
      });
    }
    secs = strands.map((st, k) => ribbonSections(st, ground, grid.surfaceZ, k === 0 ? lineOff : undefined));
    if (!fixes) break;
  }
  scene.add(terrainMesh(track, grid, ortho, groundDetail));
  const asphaltDetail = makeGroundDetail('asphalt', maxAniso);
  const ribbon = buildRibbon(track, ortho, secs[0], asphaltDetail, groundDetail);
  scene.add(ribbon);
  // pit lane: drawn over the track's shoulder where they overlap (stronger polygon offset)
  const nPit = (pit?.parts ?? []).filter((p) => p.n >= 2).length;
  // paved zones: a closed road with a declared surface takes the road material ('asphalt') or pale concrete; the rest
  // keep the aerial photo's colour (paved runoff, Laguna)
  const zoneSurf = (zones?.parts ?? []).filter((p) => p.n >= 2).map((p) => p.surface);
  secs.slice(1).forEach((sec, k) => {
    const surf = k >= nPit ? zoneSurf[k - nPit] : 'asphalt';
    scene.add(buildRibbon(track, ortho, sec, asphaltDetail, groundDetail, k < nPit ? `pit_lane_${k}` : `paved_runoff_${k - nPit}`, -6, k >= nPit && !surf, surf === 'concrete'));
  });
  if (pit) { const m = buildPitPaint(pit, ground); if (m) scene.add(m); }
  const seam = seamReport(secs, grid.surfaceZ);
  scene.add(buildStartLine(track, ground));
  if (scenery) scene.add(buildScenery(track, hf, scenery, maxAniso, ground, paintSurface(track, ortho, asphaltDetail, groundDetail)));
  else scene.add(buildCornerSigns(track));
  // Lambert BRDF is albedo/pi: sun 3.4 at 38 deg elevation + sky fill ~ 0.9 x albedo on flat ground, so the
  // ortho shows close to its own colours under ACES at exposure 1.
  const hemi = new THREE.HemisphereLight(0xb4cbe8, 0x7a6448, 0.95);
  scene.add(hemi);
  const sun = new THREE.DirectionalLight(0xffe7c8, 3.4);
  sun.castShadow = true;
  // player-only box; applyQuality (src/app/quality.ts) widens it to ±30 m at 4096 px on desktop so nearby AI cars cast too
  sun.shadow.mapSize.set(1024, 1024);
  const sc = sun.shadow.camera;
  sc.left = -7; sc.right = 7; sc.top = 7; sc.bottom = -7; sc.near = 1; sc.far = 80;
  sun.shadow.bias = -0.0005;
  sun.shadow.normalBias = 0.02;
  sun.shadow.radius = 4;
  scene.add(sun, sun.target);
  const sunDir = SUN_DIR.clone();

  return {
    scene, sun, hemi, sunDir, seam,
    follow(target) {
      sun.target.position.copy(target);
      sun.position.copy(target).addScaledVector(sunDir, 40);
      sun.target.updateMatrixWorld();
    },
  };
}
