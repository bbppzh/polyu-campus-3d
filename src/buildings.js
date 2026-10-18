// Procedural massing for the PolyU campus model.
// All geometry is generated from projected OSM footprints in data/campus.json.
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

const SHARED = {
  uNight: { value: 0 },
};

const PALETTE = {
  brick: '#a34233',
  brickLight: '#b55445',
  brickDark: '#8b372b',
  concrete: '#cec6b5',
  concreteLight: '#dcd6c8',
  glass: '#7e9aa4',
  glassLight: '#9db4bc',
  white: '#e6e2d8',
  metal: '#a7aaa7',
  roof: '#6d6962',
  roofLight: '#8d887f',
  green: '#8ea37c',
  ground: '#d8d1c3',
};

const ROAD_STYLE = {
  motorway: { w: 18, c: '#a9a49a' },
  trunk: { w: 16, c: '#a9a49a' },
  primary: { w: 13, c: '#ada79c' },
  secondary: { w: 10, c: '#b3ada1' },
  tertiary: { w: 8, c: '#b9b3a7' },
  residential: { w: 7, c: '#bcb6aa' },
  service: { w: 4.5, c: '#c3bdb1' },
  pedestrian: { w: 6, c: '#cfc8ba' },
  footway: { w: 2.6, c: '#cfc8b9' },
  path: { w: 2.4, c: '#cfc8b9' },
  steps: { w: 2.4, c: '#c8c1b3' },
  cycleway: { w: 2.4, c: '#c3bcae' },
  default: { w: 3, c: '#c6bfb2' },
};

let TEXTURE_CACHE = null;
let FALLBACK_TEX = null;

function fallbackTexture(THREE) {
  if (FALLBACK_TEX) return FALLBACK_TEX;
  const c = document.createElement('canvas');
  c.width = 1; c.height = 1;
  const ctx = c.getContext('2d');
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, 0, 1, 1);
  FALLBACK_TEX = new THREE.CanvasTexture(c);
  FALLBACK_TEX.needsUpdate = true;
  return FALLBACK_TEX;
}

function makeSurfaceTextures(THREE) {
  if (TEXTURE_CACHE) return TEXTURE_CACHE;
  const S = 512;

  function canvasTexture(canvas, colorSpace) {
    const tex = new THREE.CanvasTexture(canvas);
    tex.wrapS = THREE.RepeatWrapping;
    tex.wrapT = THREE.RepeatWrapping;
    tex.anisotropy = 4;
    if (colorSpace) tex.colorSpace = colorSpace;
    tex.needsUpdate = true;
    return tex;
  }

  function buildBrick() {
    const albedo = document.createElement('canvas');
    albedo.width = S; albedo.height = S;
    const actx = albedo.getContext('2d');
    const aimg = actx.createImageData(S, S);
    const rough = document.createElement('canvas');
    rough.width = S; rough.height = S;
    const rctx = rough.getContext('2d');
    const rimg = rctx.createImageData(S, S);
    const height = new Float32Array(S * S);
    const rows = 24;
    const cols = 9;
    const bh = S / rows;
    const bw = S / cols;
    const mortar = 2.2;
    let seed = 1234567;
    const rand = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    const brickPalette = [
      [152, 63, 49], [166, 74, 56], [142, 58, 45], [158, 70, 52],
      [148, 61, 47], [171, 82, 62], [136, 54, 43],
    ];
    for (let y = 0; y < S; y++) {
      const row = Math.floor(y / bh);
      const offset = (row % 2) * bw * 0.5;
      for (let x = 0; x < S; x++) {
        const wx = (x + offset) % S;
        const col = Math.floor(wx / bw);
        const fx = wx - col * bw;
        const fy = y - row * bh;
        const isMortar = fx < mortar || fx > bw - mortar || fy < mortar || fy > bh - mortar;
        const n = rand();
        let r, g, b, h, roughV;
        if (isMortar) {
          r = 196 + n * 14; g = 190 + n * 14; b = 178 + n * 12;
          h = 0.18; roughV = 236 + n * 16;
        } else {
          const p = brickPalette[Math.floor(rand() * brickPalette.length)];
          const shade = 0.88 + rand() * 0.24;
          r = p[0] * shade; g = p[1] * shade; b = p[2] * shade;
          h = 0.72 + rand() * 0.06; roughV = 196 + rand() * 26;
          // darker at the brick edges
          if (fx < mortar + 2 || fx > bw - mortar - 2 || fy < mortar + 1 || fy > bh - mortar - 1) {
            r *= 0.86; g *= 0.86; b *= 0.86;
          }
        }
        const i = (y * S + x) * 4;
        aimg.data[i] = r; aimg.data[i + 1] = g; aimg.data[i + 2] = b; aimg.data[i + 3] = 255;
        rimg.data[i] = roughV; rimg.data[i + 1] = roughV; rimg.data[i + 2] = roughV; rimg.data[i + 3] = 255;
        height[y * S + x] = h;
      }
    }
    actx.putImageData(aimg, 0, 0);
    rctx.putImageData(rimg, 0, 0);
    const normalCanvas = normalFromHeight(THREE, height, S, 2.2);
    return {
      albedo: canvasTexture(albedo, THREE.SRGBColorSpace),
      normal: canvasTexture(normalCanvas),
      roughness: canvasTexture(rough),
      scale: 0.5,
    };
  }

  function buildStone() {
    const albedo = document.createElement('canvas');
    albedo.width = S; albedo.height = S;
    const actx = albedo.getContext('2d');
    const aimg = actx.createImageData(S, S);
    const rough = document.createElement('canvas');
    rough.width = S; rough.height = S;
    const rctx = rough.getContext('2d');
    const rimg = rctx.createImageData(S, S);
    const height = new Float32Array(S * S);
    const cols = 4;
    const rows = 6;
    const cw = S / cols;
    const ch = S / rows;
    const joint = 2.4;
    let seed = 9876543;
    const rand = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    for (let y = 0; y < S; y++) {
      const row = Math.floor(y / ch);
      const offset = (row % 2) * cw * 0.5;
      for (let x = 0; x < S; x++) {
        const wx = (x + offset) % S;
        const col = Math.floor(wx / cw);
        const fx = wx - col * cw;
        const fy = y - row * ch;
        const isJoint = fx < joint || fx > cw - joint || fy < joint || fy > ch - joint;
        const n = rand();
        let r, g, b, h, roughV;
        if (isJoint) {
          r = 148 + n * 8; g = 141 + n * 8; b = 128 + n * 8;
          h = 0.25; roughV = 240;
        } else {
          const tone = 176 + rand() * 24;
          r = tone + 4; g = tone + 1; b = tone - 10;
          h = 0.7 + rand() * 0.05;
          roughV = 205 + rand() * 25;
          if (fx < joint + 3 || fy < joint + 3) { r *= 0.92; g *= 0.92; b *= 0.92; }
        }
        const i = (y * S + x) * 4;
        aimg.data[i] = r; aimg.data[i + 1] = g; aimg.data[i + 2] = b; aimg.data[i + 3] = 255;
        rimg.data[i] = roughV; rimg.data[i + 1] = roughV; rimg.data[i + 2] = roughV; rimg.data[i + 3] = 255;
        height[y * S + x] = h;
      }
    }
    actx.putImageData(aimg, 0, 0);
    rctx.putImageData(rimg, 0, 0);
    return {
      albedo: canvasTexture(albedo, THREE.SRGBColorSpace),
      normal: canvasTexture(normalFromHeight(THREE, height, S, 2.0)),
      roughness: canvasTexture(rough),
      scale: 0.28,
    };
  }

  function normalFromHeight(THREE, height, S, strength) {
    const c = document.createElement('canvas');
    c.width = S; c.height = S;
    const ctx = c.getContext('2d');
    const img = ctx.createImageData(S, S);
    for (let y = 0; y < S; y++) {
      for (let x = 0; x < S; x++) {
        const xl = (x - 1 + S) % S;
        const xr = (x + 1) % S;
        const yu = (y - 1 + S) % S;
        const yd = (y + 1) % S;
        const dx = (height[y * S + xr] - height[y * S + xl]) * strength;
        const dy = (height[yd * S + x] - height[yu * S + x]) * strength;
        let nx = -dx;
        let ny = -dy;
        let nz = 1;
        const len = Math.hypot(nx, ny, nz) || 1;
        nx /= len; ny /= len; nz /= len;
        const i = (y * S + x) * 4;
        img.data[i] = (nx * 0.5 + 0.5) * 255;
        img.data[i + 1] = (ny * 0.5 + 0.5) * 255;
        img.data[i + 2] = (nz * 0.5 + 0.5) * 255;
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    return c;
  }

  const textures = { brick: buildBrick(), stone: buildStone() };
  TEXTURE_CACHE = textures;
  return textures;
}

export async function loadCampusTextures(THREE) {
  const loader = new THREE.TextureLoader();
  const load = (src, srgb) =>
    new Promise((resolve, reject) => {
      loader.load(
        src,
        (tex) => {
          tex.wrapS = THREE.RepeatWrapping;
          tex.wrapT = THREE.RepeatWrapping;
          tex.anisotropy = 4;
          if (srgb) tex.colorSpace = THREE.SRGBColorSpace;
          tex.needsUpdate = true;
          resolve(tex);
        },
        undefined,
        reject
      );
    });
  try {
    const [bd, bn, br, sd, sn, sr] = await Promise.all([
      load('./assets/textures/brick/diffuse.jpg', true),
      load('./assets/textures/brick/normal.jpg', false),
      load('./assets/textures/brick/rough.jpg', false),
      load('./assets/textures/stone/diffuse.jpg', true),
      load('./assets/textures/stone/normal.jpg', false),
      load('./assets/textures/stone/rough.jpg', false),
    ]);
    return {
      brick: { albedo: bd, normal: bn, roughness: br, scale: 1.0, tint: '#a9483a', tintAmount: 0.42 },
      stone: { albedo: sd, normal: sn, roughness: sr, scale: 0.5, tint: '#cfc6b5', tintAmount: 0.55 },
    };
  } catch (err) {
    console.warn('Falling back to procedural facade textures:', err);
    return makeSurfaceTextures(THREE);
  }
}

function hexToVec3(hex) {
  const n = parseInt(String(hex).replace('#', ''), 16);
  return `vec3(${((n >> 16) & 255) / 255}, ${((n >> 8) & 255) / 255}, ${(n & 255) / 255})`;
}

function makeFacadeMaterial(THREE, color, opts = {}) {
  const mat = new THREE.MeshStandardMaterial({
    color,
    roughness: opts.roughness ?? 0.92,
    metalness: opts.metalness ?? 0.02,
    flatShading: false,
  });
  const uniforms = {
    uNight: SHARED.uNight,
    uSeed: { value: opts.seed ?? 1.0 },
    uWinSize: { value: new THREE.Vector2(opts.winW ?? 2.5, opts.floorH ?? 3.5) },
    uWinRatio: { value: new THREE.Vector2(opts.ratioX ?? 0.46, opts.ratioY ?? 0.52) },
    uGlass: { value: new THREE.Color(opts.glass ?? '#4a5c63') },
    uFrame: { value: new THREE.Color(opts.frame ?? '#d8cfbe') },
    uSky: { value: new THREE.Color(opts.sky ?? '#bcd3dc') },
    uStyle: { value: opts.style ?? 0 }, // 0 punched, 1 ribbon, 2 curtain, 3 trim
    uWinStrength: { value: opts.winStrength ?? 0.9 },
    uWinMix: { value: opts.winMix ?? 0.85 },
    uUseTex: { value: opts.texture ? 1 : 0 },
    uAlbedo: { value: opts.texture?.albedo ?? fallbackTexture(THREE) },
    uNormalMap: { value: opts.texture?.normal ?? fallbackTexture(THREE) },
    uRoughMap: { value: opts.texture?.roughness ?? fallbackTexture(THREE) },
    uTexScale: { value: new THREE.Vector2(opts.texture?.scale ?? 0.5, opts.texture?.scale ?? 0.5) },
    uTexMix: { value: opts.texture?.mix ?? 0.6 },
    uTexTint: { value: new THREE.Color(opts.texture?.tint ?? '#ffffff') },
    uTexTintAmount: { value: opts.texture?.tintAmount ?? 0 },
    uRoof: { value: new THREE.Color(opts.roof ?? '#8a857a') },
  };
  mat.userData.facadeUniforms = uniforms;

  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, uniforms);
    shader.vertexShader = shader.vertexShader
      .replace(
        '#include <common>',
        '#include <common>\nvarying vec3 vWPos;\nvarying vec3 vWNrm;'
      )
      .replace(
        '#include <begin_vertex>',
        `#include <begin_vertex>
        vWPos = (modelMatrix * vec4(transformed, 1.0)).xyz;
        vWNrm = normalize(mat3(modelMatrix) * objectNormal);`
      );

    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <common>',
        `#include <common>
        varying vec3 vWPos;
        varying vec3 vWNrm;
        uniform float uNight;
        uniform float uSeed;
        uniform vec2 uWinSize;
        uniform vec2 uWinRatio;
        uniform vec3 uGlass;
        uniform vec3 uFrame;
        uniform vec3 uSky;
        uniform float uStyle;
        uniform float uWinStrength;
        uniform float uWinMix;
        uniform float uUseTex;
        uniform sampler2D uAlbedo;
        uniform sampler2D uNormalMap;
        uniform sampler2D uRoughMap;
        uniform vec2 uTexScale;
        uniform float uTexMix;
        uniform vec3 uTexTint;
        uniform float uTexTintAmount;
        uniform vec3 uRoof;
        float polyuHash(vec2 p) {
          p = fract(p * vec2(123.34, 456.21));
          p += dot(p, p + 45.32);
          return fract(p.x * p.y);
        }`
      )
      .replace(
        '#include <color_fragment>',
        `#include <color_fragment>
        float facade = 1.0 - step(0.55, abs(vWNrm.y));
        float hcoord = abs(vWNrm.x) > abs(vWNrm.z) ? vWPos.z : vWPos.x;
        vec2 cell = vec2(hcoord / uWinSize.x, vWPos.y / uWinSize.y);
        vec2 f = fract(cell);
        vec2 id = floor(cell);
        vec2 e = (1.0 - uWinRatio) * 0.5;
        float winX = step(e.x, f.x) * step(f.x, 1.0 - e.x);
        float winY = step(e.y, f.y) * step(f.y, 1.0 - e.y);
        float win = winX * winY;

        if (uStyle > 0.5 && uStyle < 1.5) {
          // ribbon windows: continuous bands with slim vertical mullions
          float m = abs(fract(hcoord / 1.6) - 0.5) * 2.0;
          win *= step(0.10, m);
        } else if (uStyle > 1.5 && uStyle < 2.5) {
          // curtain wall: thin mullion grid
          float mx = smoothstep(0.0, 0.035, min(f.x, 1.0 - f.x));
          float my = smoothstep(0.0, 0.06, min(f.y, 1.0 - f.y));
          win *= mx * my;
        }
        win *= facade;

        // ground floor: taller shopfront glazing
        float groundBand = 1.0 - step(4.2, vWPos.y);
        float shop = groundBand * step(0.12, f.x) * step(f.x, 0.88) * step(0.2, f.y) * step(f.y, 0.92);
        win = max(win, shop);

        float edge = min(min(f.x, 1.0 - f.x), min(f.y, 1.0 - f.y));
        float frame = facade * (1.0 - smoothstep(0.0, 0.035, edge)) * step(uStyle, 2.5);
        float groundFrame = groundBand * (1.0 - smoothstep(0.0, 0.09, min(f.x, 1.0 - f.x)));
        frame = max(frame, groundFrame);

        // brick / stone colour variation
        float variation = polyuHash(id + vec2(uSeed, uSeed * 0.73));
        vec3 base = diffuseColor.rgb * (0.93 + 0.14 * variation);
        if (uStyle < 0.5) {
          // subtle brick courses
          float course = fract(vWPos.y / 0.34);
          base *= 1.0 - 0.05 * smoothstep(0.92, 1.0, course);
        }
        // floor slab band
        float band = smoothstep(0.93, 1.0, f.y) * facade;
        base = mix(base, uFrame * 0.96, band * 0.18);
        diffuseColor.rgb = base;

        vec2 polyuUV = vec2(hcoord, vWPos.y) * uTexScale;
        if (uUseTex > 0.5) {
          vec3 alb = texture2D(uAlbedo, polyuUV).rgb;
          alb = mix(alb, uTexTint, uTexTintAmount);
          float texMask = uTexMix * facade * (1.0 - win * 0.85);
          diffuseColor.rgb = mix(diffuseColor.rgb, alb, texMask);
        }

        // window glass with a fresnel-ish sky reflection
        vec3 viewDir = normalize(cameraPosition - vWPos);
        float fres = pow(1.0 - abs(dot(normalize(vWNrm), viewDir)), 2.5);
        vec3 glassCol = mix(uGlass, uSky, 0.3 + 0.5 * fres);
        diffuseColor.rgb = mix(diffuseColor.rgb, glassCol, win * uWinMix);

        // slim central mullion inside punched windows
        float mullion = win * (1.0 - smoothstep(0.0, 0.018, abs(f.x - 0.5)));
        diffuseColor.rgb = mix(diffuseColor.rgb, uFrame * 0.7, mullion * 0.25);

        // frames / facade joints
        diffuseColor.rgb = mix(diffuseColor.rgb, uFrame * 0.62, frame * 0.32);

        // stone plinth at ground level
        diffuseColor.rgb *= 1.0 - 0.14 * (1.0 - step(1.1, vWPos.y));

        // flat roofs: plain roof colour with gravel-like variation, no windows
        float roofMask = step(0.55, abs(vWNrm.y));
        float roofNoise = polyuHash(floor(vWPos.xz * 0.55) + uSeed * 2.3);
        vec3 roofCol = uRoof * (0.9 + 0.12 * roofNoise);
        diffuseColor.rgb = mix(diffuseColor.rgb, roofCol, roofMask);`
      )
      .replace(
        '#include <roughnessmap_fragment>',
        `#include <roughnessmap_fragment>
        roughnessFactor = mix(roughnessFactor, 0.12, win * uWinMix);
        roughnessFactor = mix(roughnessFactor, 0.45, frame * 0.4);
        if (uUseTex > 0.5) {
          float texRough = texture2D(uRoughMap, polyuUV).r;
          roughnessFactor = mix(roughnessFactor, texRough, uTexMix * facade * (1.0 - win));
        }`
      )
      .replace(
        '#include <normal_fragment_begin>',
        `#include <normal_fragment_begin>
        if (uUseTex > 0.5 && abs(vWNrm.y) < 0.6) {
          vec3 Nw = normalize(vWNrm);
          vec3 T = normalize(cross(vec3(0.0, 1.0, 0.0), Nw));
          vec3 B = normalize(cross(Nw, T));
          vec3 nm = texture2D(uNormalMap, vec2(hcoord, vWPos.y) * uTexScale).xyz * 2.0 - 1.0;
          vec3 nw = normalize(T * nm.x + B * nm.y + Nw * nm.z);
          vec3 nv = normalize(mat3(viewMatrix) * nw);
          normal = normalize(mix(normal, nv, uTexMix * facade * (1.0 - win * 0.8)));
        }`
      )
      .replace(
        '#include <metalnessmap_fragment>',
        `#include <metalnessmap_fragment>
        metalnessFactor = mix(metalnessFactor, 0.08, win * uWinMix);`
      )
      .replace(
        '#include <emissivemap_fragment>',
        `#include <emissivemap_fragment>
        float litRand = polyuHash(id + vec2(uSeed * 3.7, uSeed * 1.9));
        float lit = step(0.74, litRand) * win * uNight * uWinStrength;
        totalEmissiveRadiance += vec3(1.0, 0.7, 0.38) * lit * (0.32 + 0.42 * polyuHash(id + 9.1));`
      );
  };
  mat.customProgramCacheKey = () =>
    'polyu-facade-' + [opts.style ?? 0, opts.seed ?? 1, opts.winW ?? 2.5, opts.floorH ?? 3.5, opts.texture ? 1 : 0].join('-');
  return mat;
}

function shapeFromFootprint(THREE, footprint, holes = []) {
  const shape = new THREE.Shape();
  footprint.forEach(([x, z], i) => {
    if (i === 0) shape.moveTo(x, -z);
    else shape.lineTo(x, -z);
  });
  shape.closePath();
  for (const ring of holes) {
    const hole = new THREE.Path();
    ring.forEach(([x, z], i) => i === 0 ? hole.moveTo(x, -z) : hole.lineTo(x, -z));
    hole.closePath();
    shape.holes.push(hole);
  }
  return shape;
}

function extrudeBuilding(THREE, footprint, height, opts = {}) {
  const shape = shapeFromFootprint(THREE, footprint, opts.holes);
  const bevel = opts.bevel ?? 0.35;
  const geom = new THREE.ExtrudeGeometry(shape, {
    depth: height,
    bevelEnabled: bevel > 0,
    bevelThickness: bevel,
    bevelSize: bevel,
    bevelOffset: 0,
    bevelSegments: 1,
    curveSegments: 3,
    steps: 1,
  });
  geom.rotateX(-Math.PI / 2);
  geom.computeVertexNormals();
  return geom;
}

function centroid(points) {
  let x = 0, z = 0;
  for (const p of points) { x += p[0]; z += p[1]; }
  return [x / points.length, z / points.length];
}

function footprintArea(points) {
  let a = 0;
  for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
    a += (points[j][0] + points[i][0]) * (points[j][1] - points[i][1]);
  }
  return Math.abs(a / 2);
}

function classifyLandmark(name = '') {
  const n = name.toLowerCase();
  if (n.includes('innovation tower')) return 'glass';
  if (n.includes('hotel')) return 'hotel';
  if (n.includes('library')) return 'library';
  if (n.includes('auditorium')) return 'auditorium';
  if (n.includes('sports') || n.includes('swimming')) return 'sports';
  if (n.includes('hostel') || n.includes('residence')) return 'residence';
  if (n.includes('hung hom bay')) return 'bay';
  if (n.includes('student hub') || n.includes('innovation')) return 'glass';
  if (n.includes('core')) return 'core';
  return 'facility';
}

function buildRibbons(THREE, roads, materials) {
  const out = new THREE.Group();
  const byStyle = new Map();
  for (const road of roads || []) {
    // Keep the model board tidy: trim OSM ways that run far beyond the campus
    // (a long trunk way reaching z=+2193 used to draw a strip over the harbour
    // that read as a spike). Roads over water are dropped entirely.
    const pts = (road.points || []).filter(
      (p) =>
        Array.isArray(p) &&
        p.length === 2 &&
        Number.isFinite(p[0]) &&
        Number.isFinite(p[1]) &&
        p[0] > -1400 &&
        p[0] < 1400 &&
        p[1] > -1250 &&
        p[1] < 430
    );
    if (pts.length < 2) continue;
    const style = ROAD_STYLE[road.class] || ROAD_STYLE.default;
    const key = road.class in ROAD_STYLE ? road.class : 'default';
    if (!byStyle.has(key)) byStyle.set(key, []);
    byStyle.get(key).push({ pts, width: style.w });
  }
  for (const [key, items] of byStyle) {
    const style = ROAD_STYLE[key] || ROAD_STYLE.default;
    const positions = [];
    for (const { pts, width } of items) {
      for (let i = 0; i < pts.length - 1; i++) {
        const [x1, z1] = pts[i];
        const [x2, z2] = pts[i + 1];
        const dx = x2 - x1, dz = z2 - z1;
        const len = Math.hypot(dx, dz);
        if (len < 0.01 || len > 400) continue;
        const nx = (-dz / len) * width * 0.5;
        const nz = (dx / len) * width * 0.5;
        const ax = x1 + nx, az = z1 + nz;
        const bx = x2 + nx, bz = z2 + nz;
        const cx = x2 - nx, cz = z2 - nz;
        const dx2 = x1 - nx, dz2 = z1 - nz;
        positions.push(ax, 0, az, bx, 0, bz, cx, 0, cz, ax, 0, az, cx, 0, cz, dx2, 0, dz2);
      }
    }
    if (!positions.length) continue;
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geom.computeVertexNormals();
    const mat = new THREE.MeshStandardMaterial({
      color: style.c, roughness: 1, metalness: 0,
      polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1,
    });
    const mesh = new THREE.Mesh(geom, mat);
    mesh.position.y = 0.045;
    mesh.receiveShadow = true;
    out.add(mesh);
    (materials || []).push(mat);
  }
  return out;
}

function buildAreas(THREE, areas) {
  const out = new THREE.Group();
  const areaMat = new THREE.MeshStandardMaterial({
    vertexColors: true, roughness: 1, metalness: 0,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
  });
  const colors = {
    grass: new THREE.Color('#9caf8b'),
    wood: new THREE.Color('#8fa07c'),
    water: new THREE.Color('#7fa3ad'),
    pavement: new THREE.Color('#cfc8ba'),
    sand: new THREE.Color('#d6c9ad'),
    other: new THREE.Color('#d5cec0'),
  };
  const positions = [];
  const cols = [];
  const c = new THREE.Color();
  for (const area of areas || []) {
    const poly = area.polygon || [];
    if (poly.length < 3) continue;
    c.copy(colors[area.kind] || colors.other);
    // robust triangulation for convex AND concave OSM areas
    const contour = poly.slice();
    if (contour.length > 1 && contour[0][0] === contour[contour.length - 1][0] &&
        contour[0][1] === contour[contour.length - 1][1]) contour.pop();
    const v2 = contour.map((p) => new THREE.Vector2(p[0], p[1]));
    let tris = THREE.ShapeUtils.triangulateShape(v2, []);
    if (!tris || tris.length === 0) {
      tris = [];
      for (let i = 1; i < contour.length - 1; i++) tris.push([0, i, i + 1]);
    }
    for (const tri of tris) {
      let p0 = contour[tri[0]], p1 = contour[tri[1]], p2 = contour[tri[2]];
      // orient every triangle so its normal points up (+Y)
      const cross = (p1[0] - p0[0]) * (p2[1] - p0[1]) - (p1[1] - p0[1]) * (p2[0] - p0[0]);
      if (cross > 0) { const tmp = p1; p1 = p2; p2 = tmp; }
      positions.push(p0[0], 0, p0[1], p1[0], 0, p1[1], p2[0], 0, p2[1]);
      for (let k = 0; k < 3; k++) cols.push(c.r, c.g, c.b);
    }
  }
  if (positions.length) {
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    geom.setAttribute('color', new THREE.Float32BufferAttribute(cols, 3));
    geom.computeVertexNormals();
    const mesh = new THREE.Mesh(geom, areaMat);
    mesh.position.y = 0.03;
    mesh.receiveShadow = true;
    out.add(mesh);
  }
  return out;
}

function seededRand(seed) {
  let s = seed >>> 0;
  return function () {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function pointInRing(x, z, poly) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const a = poly[i], b = poly[j];
    if ((a[1] > z) !== (b[1] > z) && x < (b[0] - a[0]) * (z - a[1]) / (b[1] - a[1]) + a[0]) inside = !inside;
  }
  return inside;
}

function pointInFootprint(x, z, shape) {
  return pointInRing(x, z, shape.footprint) && !(shape.holes || []).some(ring => pointInRing(x, z, ring));
}

function footprintsOverlap(a, b) {
  if (a.footprint.some(([x,z]) => pointInFootprint(x,z,b))) return true;
  if (b.footprint.some(([x,z]) => pointInFootprint(x,z,a))) return true;
  const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
  for (const ra of [a.footprint,...(a.holes||[])]) {
    for (const rb of [b.footprint,...(b.holes||[])]) {
      for(let i=0;i<ra.length;i++)for(let j=0;j<rb.length;j++){
        const p=ra[i],q=ra[(i+1)%ra.length],r=rb[j],t=rb[(j+1)%rb.length];
        if(cross(p,q,r)*cross(p,q,t)<-1e-10 && cross(r,t,p)*cross(r,t,q)<-1e-10)return true;
      }
    }
  }
  return false;
}

function buildTrees(THREE, landmarks, areas, obstacles = []) {
  const rand = seededRand(20261018);
  const count = 170;
  const trunkGeom = new THREE.CylinderGeometry(0.5, 0.7, 4, 5);
  const canopyGeom = new THREE.IcosahedronGeometry(1, 1);
  const trunkMat = new THREE.MeshStandardMaterial({ color: '#7d6a56', roughness: 1 });
  const canopyMat = new THREE.MeshStandardMaterial({ color: '#8aa478', roughness: 0.95, flatShading: true });
  const trunks = new THREE.InstancedMesh(trunkGeom, trunkMat, count);
  const canopies = new THREE.InstancedMesh(canopyGeom, canopyMat, count);
  trunks.castShadow = true;
  canopies.castShadow = true;
  canopies.receiveShadow = true;

  // exclusion: landmark centres (plus a little padding)
  const blocked = (landmarks || []).map((l) => {
    const c = l.center || centroid(l.footprint || [[0, 0]]);
    return { x: c[0], z: c[1], r: Math.sqrt(footprintArea(l.footprint || [[0, 0]])) * 0.62 + 8 };
  });
  const exclusions = obstacles.map(shape => ({ shape, bounds: footprintBounds(shape.footprint) }));
  const dummy = new THREE.Object3D();
  let placed = 0;
  let guard = 0;
  while (placed < count && guard < count * 60) {
    guard++;
    const a = rand() * Math.PI * 2;
    const r = 90 + rand() * 230;
    const x = Math.cos(a) * r;
    const z = Math.sin(a) * r * 0.85;
    let ok = true;
    for (const b of blocked) {
      if (Math.hypot(x - b.x, z - b.z) < b.r) { ok = false; break; }
    }
    if (!ok) continue;
    if (exclusions.some(({shape, bounds: b}) => x >= b.minX && x <= b.maxX && z >= b.minZ && z <= b.maxZ && pointInFootprint(x, z, shape))) continue;
    const h = 3.2 + rand() * 2.6;
    const spread = 2.8 + rand() * 2.4;
    dummy.position.set(x, h * 0.5, z);
    dummy.rotation.y = rand() * Math.PI;
    dummy.scale.set(1, h / 4, 1);
    dummy.updateMatrix();
    trunks.setMatrixAt(placed, dummy.matrix);
    dummy.position.set(x, h + spread * 0.62, z);
    dummy.rotation.y = rand() * Math.PI;
    const s = spread * 0.52;
    dummy.scale.set(s, s * (0.85 + rand() * 0.45), s);
    dummy.updateMatrix();
    canopies.setMatrixAt(placed, dummy.matrix);
    placed++;
  }
  trunks.count = placed;
  canopies.count = placed;
  trunks.instanceMatrix.needsUpdate = true;
  canopies.instanceMatrix.needsUpdate = true;
  const group = new THREE.Group();
  group.add(trunks, canopies);
  return group;
}

function buildParapets(THREE, landmarks, mat) {
  const group = new THREE.Group();
  for (const l of landmarks) {
    const fp = l.footprint;
    if (!fp || fp.length < 3) continue;
    if (/innovation tower/i.test(l.name || '')) continue;
    const area = footprintArea(fp);
    const h = l.height || 18;
    if (area < 120 || h < 8) continue;
    const [cx, cz] = l.center || centroid(fp);
    const grow = 1 + Math.min(0.05, 1.2 / Math.sqrt(area));
    const ring = fp.map(([x, z]) => [cx + (x - cx) * grow, cz + (z - cz) * grow]);
    const g = extrudeBuilding(THREE, ring, 0.9, { bevel: 0 });
    const m = new THREE.Mesh(g, mat);
    m.position.y = h - 0.25;
    m.castShadow = true;
    m.receiveShadow = true;
    group.add(m);
  }
  return group;
}

function nearestEdge(footprint, tx = 0, tz = 0) {
  let best = null;
  for (let i = 0; i < footprint.length; i++) {
    const a = footprint[i];
    const b = footprint[(i + 1) % footprint.length];
    const mx = (a[0] + b[0]) / 2;
    const mz = (a[1] + b[1]) / 2;
    const d = Math.hypot(mx - tx, mz - tz);
    if (!best || d < best.d) {
      const dx = b[0] - a[0];
      const dz = b[1] - a[1];
      const len = Math.hypot(dx, dz) || 1;
      // outward normal: from the edge towards the reference point (campus core)
      let nx = tx - mx;
      let nz = tz - mz;
      const nl = Math.hypot(nx, nz) || 1;
      nx /= nl;
      nz /= nl;
      best = { mx, mz, dx: dx / len, dz: dz / len, len, nx, nz, d };
    }
  }
  return best;
}

function footprintBounds(footprint) {
  let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
  for (const [x, z] of footprint) {
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
    if (z < minZ) minZ = z;
    if (z > maxZ) maxZ = z;
  }
  return { minX, maxX, minZ, maxZ, w: maxX - minX, d: maxZ - minZ };
}

function buildLandmarkDetails(THREE, landmarks, materials) {
  const group = new THREE.Group();
  const trim = new THREE.MeshStandardMaterial({ color: '#e8e2d3', roughness: 0.75 });
  const glass = new THREE.MeshStandardMaterial({ color: '#728c96', roughness: 0.18, metalness: 0.35 });
  const green = new THREE.MeshStandardMaterial({ color: '#7d9a6f', roughness: 1 });
  const dark = new THREE.MeshStandardMaterial({ color: '#5b5a53', roughness: 0.9 });
  const detailMats = [trim, glass, green, dark];
  detailMats.forEach((m) => materials.push(m));

  function band(l, scale, y, depth, mat) {
    const [cx, cz] = l.center || centroid(l.footprint);
    const ring = l.footprint.map(([x, z]) => [cx + (x - cx) * scale, cz + (z - cz) * scale]);
    const g = extrudeBuilding(THREE, ring, depth, { bevel: 0 });
    const m = new THREE.Mesh(g, mat);
    m.position.y = y;
    m.castShadow = true;
    m.receiveShadow = true;
    group.add(m);
  }

  for (const l of landmarks) {
    const name = (l.name || '').toLowerCase();
    const h = l.height || 18;
    const fp = l.footprint;
    if (!fp || fp.length < 3) continue;
    const area = footprintArea(fp);
    const [cx, cz] = l.center || centroid(fp);

    if (/hotel icon/.test(name)) {
      for (const f of [0.18, 0.33, 0.48, 0.63, 0.78, 0.9]) band(l, 1.012, h * f, 0.35, trim);
    } else if (/library/.test(name)) {
      const edge = nearestEdge(fp, 0, 0);
      if (edge) {
        const w = Math.min(edge.len * 0.82, 30);
        const rot = Math.atan2(-edge.dz, edge.dx);
        const entrance = new THREE.Mesh(new THREE.BoxGeometry(w * 0.7, 7.2, 2.2), glass);
        entrance.position.set(edge.mx + edge.nx * 1.4, 3.6, edge.mz + edge.nz * 1.4);
        entrance.rotation.y = rot;
        group.add(entrance);
        // horizontal louvres over the glazed entrance
        for (let i = 0; i < 5; i++) {
          const slat = new THREE.Mesh(new THREE.BoxGeometry(w * 0.74, 0.16, 0.7), trim);
          slat.position.set(edge.mx + edge.nx * 2.6, 1.4 + i * 1.15, edge.mz + edge.nz * 2.6);
          slat.rotation.y = rot;
          group.add(slat);
        }
        const canopy = new THREE.Mesh(new THREE.BoxGeometry(w, 0.5, 5.2), trim);
        canopy.position.set(edge.mx + edge.nx * 2.6, 7.6, edge.mz + edge.nz * 2.6);
        canopy.rotation.y = rot;
        canopy.castShadow = true;
        group.add(canopy);
        // slim roof skylights across the reading rooms
        const bb = footprintBounds(fp);
        for (let i = -1; i <= 1; i++) {
          const sky = new THREE.Mesh(new THREE.BoxGeometry(bb.w * 0.18, 0.5, bb.d * 0.34), glass);
          sky.position.set(cx + i * bb.w * 0.24, h + 1.1, cz);
          group.add(sky);
        }
      }
    } else if (/auditorium/.test(name)) {
      // curved vault roof over the auditorium
      const bb = footprintBounds(fp);
      const w = Math.min(bb.w, bb.d) * 0.9;
      const depth = Math.max(bb.w, bb.d) * 0.92;
      const rise = Math.min(bb.w, bb.d) * 0.32;
      const shape = new THREE.Shape();
      shape.moveTo(-w / 2, 0);
      shape.quadraticCurveTo(0, rise * 2, w / 2, 0);
      shape.closePath();
      const vaultGeo = new THREE.ExtrudeGeometry(shape, {
        depth, bevelEnabled: false, curveSegments: 24, steps: 1,
      });
      vaultGeo.translate(0, 0, -depth / 2);
      vaultGeo.rotateY(Math.PI / 2);
      const vault = new THREE.Mesh(vaultGeo, trim);
      vault.position.set(cx, h - 0.2, cz);
      vault.castShadow = true;
      vault.receiveShadow = true;
      group.add(vault);
      band(l, 1.012, h, 0.55, trim);
    } else if (/block z/.test(name)) {
      const w = Math.min(24, Math.sqrt(area) * 0.5);
      const garden = new THREE.Mesh(new THREE.BoxGeometry(w, 0.3, w * 0.55), green);
      garden.position.set(cx, h + 0.35, cz);
      group.add(garden);
      const pavilion = new THREE.Mesh(new THREE.BoxGeometry(7, 3.2, 5), trim);
      pavilion.position.set(cx + w * 0.35, h + 1.6, cz - w * 0.2);
      pavilion.castShadow = true;
      group.add(pavilion);
    } else if (area > 120 && h > 6) {
      // a simple entrance canopy on the side facing the campus core
      const edge = nearestEdge(fp, 0, 0);
      if (edge && edge.len > 6) {
        const w = Math.min(edge.len * 0.5, 12);
        const canopy = new THREE.Mesh(new THREE.BoxGeometry(w, 0.35, 3.4), trim);
        canopy.position.set(edge.mx + edge.nx * 2.0, 3.8, edge.mz + edge.nz * 2.0);
        canopy.rotation.y = Math.atan2(-edge.dz, edge.dx);
        canopy.castShadow = true;
        group.add(canopy);
        for (const side of [-1, 1]) {
          const col = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.22, 3.8, 6), trim);
          col.position.set(
            edge.mx + edge.nx * 3.3 + edge.dx * side * (w / 2 - 0.7),
            1.9,
            edge.mz + edge.nz * 3.3 + edge.dz * side * (w / 2 - 0.7)
          );
          group.add(col);
        }
        // glazed entrance door and two shallow steps
        const door = new THREE.Mesh(new THREE.BoxGeometry(w * 0.36, 2.6, 0.3), glass);
        door.position.set(edge.mx + edge.nx * 0.45, 1.3, edge.mz + edge.nz * 0.45);
        door.rotation.y = Math.atan2(-edge.dz, edge.dx);
        group.add(door);
        for (let k = 0; k < 2; k++) {
          const step = new THREE.Mesh(new THREE.BoxGeometry(w * (0.74 + k * 0.12), 0.16, 2.0 + k * 0.9), trim);
          step.position.set(edge.mx + edge.nx * (1.6 + k * 0.45), 0.08 + k * 0.16, edge.mz + edge.nz * (1.6 + k * 0.45));
          step.rotation.y = Math.atan2(-edge.dz, edge.dx);
          step.receiveShadow = true;
          group.add(step);
        }
      }
    }
    // rooftop equipment is added separately
  }
  // simple rooftop flag poles on the tallest landmark
  const tallest = landmarks.slice().sort((a, b) => (b.height || 0) - (a.height || 0))[0];
  if (tallest) {
    const [cx, cz] = tallest.center || centroid(tallest.footprint);
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 12, 5), dark);
    pole.position.set(cx, (tallest.height || 20) + 6, cz);
    group.add(pole);
  }
  return group;
}

function buildRoofDetails(THREE, landmarks, materials) {
  const group = new THREE.Group();
  const rand = seededRand(77);
  const roofMat = new THREE.MeshStandardMaterial({ color: PALETTE.roofLight, roughness: 0.95 });
  const acMat = new THREE.MeshStandardMaterial({ color: '#b9b4a8', roughness: 0.72, metalness: 0.08 });
  const tankMat = new THREE.MeshStandardMaterial({ color: '#d0c9ba', roughness: 0.8 });
  const ventMat = new THREE.MeshStandardMaterial({ color: '#8d9191', roughness: 0.55, metalness: 0.3 });
  materials.push(roofMat, acMat, tankMat, ventMat);
  for (const l of landmarks) {
    const h = l.height;
    if (!l.footprint || l.footprint.length < 3) continue;
    if (/innovation tower/i.test(l.name || '')) continue;
    const [cx, cz] = l.center || centroid(l.footprint);
    const area = footprintArea(l.footprint);
    if (area < 250) continue;
    const span = Math.sqrt(area) * 0.3;
    const n = area > 2500 ? 3 : 2;
    for (let i = 0; i < n; i++) {
      const w = Math.min(18, Math.sqrt(area) * (0.22 + rand() * 0.18));
      const d = w * (0.7 + rand() * 0.6);
      const box = new THREE.Mesh(new THREE.BoxGeometry(w, 2.2 + rand() * 2.2, d), roofMat);
      box.position.set(cx + (rand() - 0.5) * span, h + 1, cz + (rand() - 0.5) * span);
      box.castShadow = true;
      box.receiveShadow = true;
      group.add(box);
    }
    // AC condensers
    for (let i = 0; i < 3; i++) {
      const w = 1.2 + rand() * 1.1;
      const ac = new THREE.Mesh(new THREE.BoxGeometry(w, 0.8 + rand() * 0.5, w * (0.8 + rand() * 0.5)), acMat);
      ac.position.set(cx + (rand() - 0.5) * span * 1.5, h + 0.5, cz + (rand() - 0.5) * span * 1.5);
      ac.castShadow = true;
      group.add(ac);
      const fan = new THREE.Mesh(new THREE.CylinderGeometry(w * 0.28, w * 0.28, 0.12, 12), ventMat);
      fan.position.set(ac.position.x, ac.position.y + 0.5, ac.position.z);
      fan.rotation.x = Math.PI / 2;
      group.add(fan);
    }
    // water tank / vent cluster on the larger roofs
    if (area > 900) {
      const tank = new THREE.Mesh(new THREE.CylinderGeometry(1.6, 1.8, 2.4, 16), tankMat);
      tank.position.set(cx + (rand() - 0.5) * span, h + 1.2, cz + (rand() - 0.5) * span);
      tank.castShadow = true;
      group.add(tank);
    }
    for (let i = 0; i < 3; i++) {
      const vent = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 1.2 + rand() * 1.2, 8), ventMat);
      vent.position.set(cx + (rand() - 0.5) * span * 1.6, h + 0.8, cz + (rand() - 0.5) * span * 1.6);
      group.add(vent);
    }
  }
  return group;
}

function buildJCITTower(THREE, l, group, landmarks, materials, mats) {
  const fp = l.footprint;
  const [cx, cz] = l.center || centroid(fp);
  const bb = footprintBounds(fp);
  const h = l.height || 48;
  const baseY = 6.5;
  const rx = Math.max(19, bb.w * 0.26);
  const rz = Math.max(17, bb.d * 0.25);
  const M = 64;
  const N = 22;

  const point = (theta, t, extra = 0) => {
    const taper = 1 - 0.12 * Math.pow(t, 1.25);
    const organic = 1 + 0.22 * Math.cos(2 * theta + 0.9) + 0.09 * Math.cos(3 * theta - 0.6);
    const leanX = 10 * t * t;
    const leanZ = -6 * t * t;
    const warp = 3.4 * Math.pow(t, 3) * Math.cos(theta + 0.7);
    return [
      cx + leanX + (rx * organic * taper + extra) * Math.cos(theta),
      baseY + (h - baseY) * t + warp,
      cz + leanZ + (rz * organic * taper + extra) * Math.sin(theta),
    ];
  };

  const whiteMat = new THREE.MeshStandardMaterial({ color: '#e9e5db', roughness: 0.68, metalness: 0.03 });
  const glassBandMat = new THREE.MeshStandardMaterial({
    color: '#41575e', roughness: 0.22, metalness: 0.18, side: THREE.DoubleSide,
  });
  materials.push(whiteMat, glassBandMat);

  // compact podium
  const podiumRing = fp.map(([x, z]) => [cx + (x - cx) * 0.8, cz + (z - cz) * 0.8]);
  const podiumGeo = extrudeBuilding(THREE, podiumRing, baseY, { bevel: 0.8 });
  const podium = new THREE.Mesh(podiumGeo, whiteMat);
  podium.castShadow = true;
  podium.receiveShadow = true;
  group.add(podium);
  landmarks.push({ mesh: podium, data: l });

  // fluid white shell
  const verts = [];
  const idx = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N;
    for (let j = 0; j < M; j++) {
      const theta = (j / M) * Math.PI * 2;
      const [x, y, z] = point(theta, t);
      verts.push(x, y, z);
    }
  }
  for (let i = 0; i < N; i++) {
    for (let j = 0; j < M; j++) {
      const a = i * M + j;
      const b = i * M + ((j + 1) % M);
      const c = (i + 1) * M + ((j + 1) % M);
      const d = (i + 1) * M + j;
      idx.push(a, d, b, b, d, c);
    }
  }
  const topCenter = [cx + 10, h + 3.6, cz - 6];
  const topIndex = verts.length / 3;
  verts.push(...topCenter);
  for (let j = 0; j < M; j++) {
    idx.push(N * M + j, topIndex, N * M + ((j + 1) % M));
  }
  const shellGeo = new THREE.BufferGeometry();
  shellGeo.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
  shellGeo.setIndex(idx);
  shellGeo.computeVertexNormals();
  const shell = new THREE.Mesh(shellGeo, whiteMat);
  shell.castShadow = true;
  shell.receiveShadow = true;
  group.add(shell);
  landmarks.push({ mesh: shell, data: l });

  // flush dark glazing ribbons at every storey
  const floorH = 3.4;
  for (let y = baseY + floorH * 0.55; y < h - 1.6; y += floorH) {
    const t0 = (y - baseY) / (h - baseY);
    const t1 = (y + 1.15 - baseY) / (h - baseY);
    const bverts = [];
    const bidx = [];
    for (let k = 0; k < 2; k++) {
      const t = k === 0 ? t0 : t1;
      for (let j = 0; j < M; j++) {
        const theta = (j / M) * Math.PI * 2;
        const p = point(theta, t, 0.16);
        bverts.push(p[0], p[1], p[2]);
      }
    }
    for (let j = 0; j < M; j++) {
      const a = j;
      const b = (j + 1) % M;
      const c = M + ((j + 1) % M);
      const d = M + j;
      bidx.push(a, d, b, b, d, c);
    }
    const bg = new THREE.BufferGeometry();
    bg.setAttribute('position', new THREE.Float32BufferAttribute(bverts, 3));
    bg.setIndex(bidx);
    bg.computeVertexNormals();
    const band = new THREE.Mesh(bg, glassBandMat);
    group.add(band);
  }
}

function buildContextDetails(THREE, context, materials, landmarkEnvelopes = []) {
  const group = new THREE.Group();
  const whiteMat = new THREE.MeshStandardMaterial({ color: '#d6d0c2', roughness: 0.85 });
  const roofMat = new THREE.MeshStandardMaterial({ color: '#918b80', roughness: 0.95 });
  const darkMat = new THREE.MeshStandardMaterial({ color: '#646d70', roughness: 0.7, metalness: 0.12 });
  const glassMat = new THREE.MeshStandardMaterial({ color: '#294c57', roughness: 0.22, metalness: 0.2 });
  const greenMat = new THREE.MeshStandardMaterial({ color: '#6d8d5b', roughness: 1 });
  materials.push(whiteMat, roofMat, darkMat, glassMat, greenMat);
  const buckets = { white: [], roof: [], dark: [], glass: [], green: [] };
  const rand = seededRand(3141);
  const add = (bucket, w, h, d, x, y, z) => {
    const g = new THREE.BoxGeometry(w, h, d);
    g.translate(x, y, z);
    buckets[bucket].push(g);
  };
  const addCyl = (bucket, r, h, x, y, z) => {
    const g = new THREE.CylinderGeometry(r, r, h, 8);
    g.translate(x, y, z);
    buckets[bucket].push(g);
  };
  const addRot = (bucket, w, h, d, x, y, z, rot) => {
    const g = new THREE.BoxGeometry(w, h, d);
    g.rotateY(rot);
    g.translate(x, y, z);
    buckets[bucket].push(g);
  };
  const fitsRoof = (shape, x, z, w, d) => {
    const nx = Math.max(2, Math.ceil(w / 0.6));
    const nz = Math.max(2, Math.ceil(d / 0.6));
    for (let i = 0; i <= nx; i++) {
      for (let j = 0; j <= nz; j++) {
        if (!pointInFootprint(x + w * (i / nx - 0.5), z + d * (j / nz - 0.5), shape)) return false;
      }
    }
    return true;
  };
  const blockingShapes = [...context, ...landmarkEnvelopes].map(shape => ({shape, bounds: footprintBounds(shape.footprint)}));
  const excludedContextIds = new Set([236028367, 236028374, 236028379]);
  for (let i = 0; i < context.length; i++) {
    const b = context[i];
    if (!b.footprint || b.footprint.length < 3) continue;
    if (excludedContextIds.has(b.id)) continue;
    const area = footprintArea(b.footprint);
    if (area < 10) continue;
    const h = Math.max(4, b.height || 16);
    const [cx, cz] = b.center || centroid(b.footprint);
    const bb = footprintBounds(b.footprint);
    const span = Math.min(bb.w, bb.d);
    // roof parapet follows the actual footprint edges (concave/L-shaped safe)
    if (h > 3) {
      for (const ring of [b.footprint, ...(b.holes || [])]) {
        for (let k = 0; k < ring.length; k++) {
          const a = ring[k];
          const c = ring[(k + 1) % ring.length];
          const dx = c[0] - a[0];
          const dz = c[1] - a[1];
          const len = Math.hypot(dx, dz);
          if (len < 0.6) continue;
          const ang = Math.atan2(-dz, dx);
          const g = new THREE.BoxGeometry(len + 0.3, 0.7, 0.38);
          g.rotateY(ang);
          g.translate((a[0] + c[0]) / 2, h + 0.35, (a[1] + c[1]) / 2);
          buckets.white.push(g);
      }
      }
    }
    // Roof props sit on the roof, with their entire base inside the polygon.
    if (area > 280) {
      const px = cx + (rand() - 0.5) * bb.w * 0.25;
      const pz = cz + (rand() - 0.5) * bb.d * 0.25;
      const pw = Math.min(10, span * 0.25), pd = Math.min(8, span * 0.2);
      const ph = 1.4 + rand() * 1.2;
      if (fitsRoof(b, px, pz, pw + 0.2, pd + 0.2)) add('roof', pw, ph, pd, px, h + ph / 2, pz);
      const vx = cx + bb.w * 0.2, vz = cz - bb.d * 0.18, vh = 1.5 + rand();
      if (fitsRoof(b, vx, vz, 0.7, 0.7)) add('dark', 0.5, vh, 0.5, vx, h + vh / 2, vz);
    }
    if (area > 900) {
      const wx = cx - bb.w * 0.22, wz = cz + bb.d * 0.2, r = Math.min(2.2, span * 0.06);
      if (fitsRoof(b, wx, wz, r * 2 + 0.2, r * 2 + 0.2)) addCyl('white', r, 2.6, wx, h + 1.3, wz);
    }
    // shopfront + awning follow one real footprint edge (not a bbox side)
    if (area > 40 && h > 4 && !b.clipped) {
      let bestEdge = null;
      for (let e = 0; e < b.footprint.length; e++) {
        const a = b.footprint[e];
        const c = b.footprint[(e + 1) % b.footprint.length];
        const dx = c[0] - a[0];
        const dz = c[1] - a[1];
        const len = Math.hypot(dx, dz);
        if (len < 6) continue;
        const mx = (a[0] + c[0]) / 2;
        const mz = (a[1] + c[1]) / 2;
        let nx = dz / len;
        let nz = -dx / len;
        if (pointInFootprint(mx + nx * .05, mz + nz * .05, b)) { nx = -nx; nz = -nz; }
        // Exact edge crossings and containment protect the full awning,
        // including narrow neighbours missed by a centre/corner/grid sample.
        const width = Math.min(len * .62, 18) + .8;
        const radius = width/2 + 1.4;
        const obstacles = blockingShapes.filter(({shape, bounds: q}) => shape !== b && q.minX < mx+radius && q.maxX > mx-radius && q.minZ < mz+radius && q.maxZ > mz-radius);
        const awning = {footprint: [[-.5,.2],[.5,.2],[.5,1.3],[-.5,1.3]].map(([along,normal]) => [mx+dx/len*along*width+nx*normal,mz+dz/len*along*width+nz*normal])};
        const clear = !obstacles.some(({shape}) => footprintsOverlap(awning,shape));
        if (clear && (!bestEdge || len > bestEdge.len)) bestEdge = { mx, mz, dx, dz, len, nx, nz };
      }
      if (bestEdge) {
        const w = Math.min(bestEdge.len * 0.62, 18.0);
        const rot = Math.atan2(-bestEdge.dz, bestEdge.dx);
        const gx = bestEdge.mx + bestEdge.nx * 0.22;
        const gz = bestEdge.mz + bestEdge.nz * 0.22;
        addRot('glass', w, 2.7, 0.25, gx, 1.55, gz, rot);
        addRot('white', w + 0.8, 0.22, 1.1, bestEdge.mx + bestEdge.nx * 0.75, 3.2, bestEdge.mz + bestEdge.nz * 0.75, rot);
      }
    }
    // occasional roof garden
    if (area > 700 && h < 30 && i % 5 === 0) {
      const gx = cx + bb.w * 0.1;
      const gz = cz;
      const gw = Math.min(10, bb.w * 0.3), gd = Math.min(6, bb.d * 0.2);
      if (fitsRoof(b, gx, gz, gw + 0.2, gd + 0.2)) {
        add('green', gw, 0.55, gd, gx, h + 0.275, gz);
      }
    }
  }
  const mats = { white: whiteMat, roof: roofMat, dark: darkMat, glass: glassMat, green: greenMat };
  for (const key of Object.keys(buckets)) {
    if (!buckets[key].length) continue;
    const merged = mergeGeometries(buckets[key], false);
    if (!merged) continue;
    const mesh = new THREE.Mesh(merged, mats[key]);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.context = true;
    group.add(mesh);
  }
  return group;
}

function signTexture(THREE, name, zh) {
  const c = document.createElement('canvas');
  c.width = 640;
  c.height = 160;
  const ctx = c.getContext('2d');
  ctx.fillStyle = 'rgba(250,248,243,0.96)';
  ctx.fillRect(0, 0, 640, 160);
  ctx.fillStyle = '#ad2035';
  ctx.fillRect(0, 0, 640, 8);
  ctx.fillStyle = '#ad2035';
  ctx.font = '600 15px Helvetica, Arial, sans-serif';
  ctx.fillText('THE HONG KONG POLYTECHNIC UNIVERSITY', 26, 36);
  ctx.fillStyle = '#26221f';
  ctx.font = '700 38px Helvetica, Arial, sans-serif';
  let title = name;
  while (ctx.measureText(title).width > 580 && title.length > 8) title = title.slice(0, -2);
  ctx.fillText(title, 26, 86);
  if (zh) {
    ctx.fillStyle = '#5e574e';
    ctx.font = '500 25px "PingFang HK", "Noto Sans HK", sans-serif';
    ctx.fillText(zh, 26, 128);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function buildEntranceSigns(THREE, landmarks, materials, group, hotelRegistration) {
  for (const l of landmarks) {
    if (!l.name) continue;
    if (!l.footprint || l.footprint.length < 3) continue;
    let edge;
    const hotelEntry = /^hotel icon$/i.test(l.name) ? hotelRegistration?.entries?.find(e => e.id === 'hotel') : null;
    if (hotelEntry) {
      const [mx, mz] = hotelEntry.wall_world_xz;
      const [nx, nz] = hotelEntry.outward_world_xz;
      edge = { mx, mz, nx, nz };
    } else if (/innovation tower/i.test(l.name)) {
      edge = nearestEdge(l.footprint, 0, 0);
    } else if (/pao yue-kong library/i.test(l.name)) {
      let best = null;
      for (let i = 0; i < l.footprint.length - 1; i++) {
        const a = l.footprint[i];
        const b = l.footprint[i + 1];
        const len = Math.hypot(b[0] - a[0], b[1] - a[1]);
        if (len < 12) continue;
        const mz = (a[1] + b[1]) / 2;
        if (!best || mz < best.mz) best = { mx: (a[0] + b[0]) / 2, mz };
      }
      if (best) edge = { mx: best.mx, mz: best.mz, nx: 0, nz: -1 };
      else edge = nearestEdge(l.footprint, 0, 0);
    } else {
      edge = nearestEdge(l.footprint, 0, 0);
    }
    if (!edge) continue;
    const tex = signTexture(THREE, (l.name || '').toUpperCase(), l.nameZh);
    const mat = new THREE.MeshBasicMaterial({
      map: tex, transparent: true, alphaTest: 0.05, toneMapped: false, side: THREE.DoubleSide,
    });
    materials.push(mat);
    const feature = /library|innovation tower/i.test(l.name);
    const wide = hotelEntry ? 2.2 : feature ? 13.5 : 10.5;
    const sign = new THREE.Mesh(new THREE.PlaneGeometry(wide, wide / 4), mat);
    const y = hotelEntry ? 3.42 : /library/i.test(l.name) ? 8.8 : /innovation tower/i.test(l.name) ? 4.3 : 6.4;
    const off = hotelEntry ? hotelEntry.canopy_depth_m + 0.10 : /pao yue-kong library/i.test(l.name) ? 3.2 : 0.9;
    sign.position.set(edge.mx + edge.nx * off, Math.min(y, (l.height || 18) - 2), edge.mz + edge.nz * off);
    sign.rotation.y = Math.atan2(edge.nx, edge.nz);
    group.add(sign);
  }
}

export function createCampus(THREE, data, opts = {}) {
  const renderContext = data.sceneLayout?.context || data.context || [];
  const group = new THREE.Group();
  const materials = [];
  const landmarks = [];
  const disposables = [];
  const textures = opts.textures || makeSurfaceTextures(THREE);

  const brick = makeFacadeMaterial(THREE, PALETTE.brick, {
    style: 1, seed: 1.1, winW: 2.4, floorH: 3.4, ratioX: 0.94, ratioY: 0.42,
    glass: '#7f9ca4', frame: '#d9d0bd', winStrength: 0.9, winMix: 0.72, texture: { ...textures.brick, mix: 0.62 },
  });
  const brickLight = makeFacadeMaterial(THREE, PALETTE.brickLight, {
    style: 1, seed: 2.7, winW: 2.5, floorH: 3.4, ratioX: 0.94, ratioY: 0.42,
    glass: '#83a0a7', frame: '#ded5c2', winStrength: 0.9, winMix: 0.7, texture: { ...textures.brick, mix: 0.58 },
  });
  const brickDark = makeFacadeMaterial(THREE, PALETTE.brickDark, {
    style: 1, seed: 4.3, winW: 2.6, floorH: 3.6, ratioX: 0.94, ratioY: 0.42,
    glass: '#7d999f', frame: '#cfc5b2', winStrength: 0.8, winMix: 0.7, texture: { ...textures.brick, mix: 0.58 },
  });
  const concrete = makeFacadeMaterial(THREE, PALETTE.concrete, {
    style: 1, seed: 1.9, winW: 3.2, floorH: 3.6, ratioX: 0.94, ratioY: 0.52,
    glass: '#4e636a', frame: '#d9d1c1', winStrength: 0.75, texture: { ...textures.stone, mix: 0.5 },
  });
  const concreteLight = makeFacadeMaterial(THREE, PALETTE.concreteLight, {
    style: 0, seed: 6.2, winW: 3.0, floorH: 3.6, ratioX: 0.38, ratioY: 0.48,
    glass: '#9db1b3', frame: '#e6dfd0', winStrength: 0.7, winMix: 0.42, texture: { ...textures.stone, mix: 0.42 },
  });
  const glass = makeFacadeMaterial(THREE, PALETTE.glass, {
    style: 2, seed: 3.4, winW: 1.8, floorH: 3.6, ratioX: 0.97, ratioY: 0.86,
    glass: '#4d6a75', frame: '#c9d4d7', winStrength: 1.0, roughness: 0.55, metalness: 0.15,
  });
  const glassLight = makeFacadeMaterial(THREE, PALETTE.glassLight, {
    style: 2, seed: 5.1, winW: 1.9, floorH: 3.6, ratioX: 0.96, ratioY: 0.84,
    glass: '#5d7c86', frame: '#d6dfe1', winStrength: 1.0, roughness: 0.5, metalness: 0.18,
  });
  const white = makeFacadeMaterial(THREE, PALETTE.white, {
    style: 0, seed: 7.5, winW: 2.0, floorH: 3.6, ratioX: 0.28, ratioY: 0.46,
    glass: '#a0b3b5', frame: '#ece6d9', winStrength: 0.65, winMix: 0.45,
  });
  const contextMat = makeFacadeMaterial(THREE, '#cfc9bb', {
    style: 0, seed: 8.4, winW: 3.0, floorH: 3.5, ratioX: 0.32, ratioY: 0.38,
    glass: '#a6b3b1', frame: '#d4ccbc', winStrength: 0.35, winMix: 0.28,
  });
  const campusBrick = makeFacadeMaterial(THREE, '#a65a48', {
    style: 1, seed: 9.2, winW: 2.5, floorH: 3.4, ratioX: 0.94, ratioY: 0.42,
    glass: '#819da4', frame: '#d8cebb', winStrength: 0.8, winMix: 0.68, texture: { ...textures.brick, mix: 0.55 },
  });
  const campusStone = makeFacadeMaterial(THREE, '#d3c7b4', {
    style: 1, seed: 10.6, winW: 3.1, floorH: 3.5, ratioX: 0.94, ratioY: 0.5,
    glass: '#506369', frame: '#ded5c5', winStrength: 0.7, texture: { ...textures.stone, mix: 0.5 },
  });
  const cityMat = makeFacadeMaterial(THREE, '#cfc9bb', {
    style: 0, seed: 12.8, winW: 2.8, floorH: 3.5, ratioX: 0.3, ratioY: 0.36,
    glass: '#aab6b3', frame: '#cfc7b7', winStrength: 0.28, winMix: 0.22,
  });
  const cityMat2 = makeFacadeMaterial(THREE, '#c2bcae', {
    style: 1, seed: 21.4, winW: 3.2, floorH: 3.3, ratioX: 0.9, ratioY: 0.4,
    glass: '#8da6a8', frame: '#c8c0b0', winStrength: 0.36, winMix: 0.3,
  });
  const cityMat3 = makeFacadeMaterial(THREE, '#d1c9b9', {
    style: 0, seed: 28.7, winW: 2.4, floorH: 3.6, ratioX: 0.26, ratioY: 0.44,
    glass: '#94a6a8', frame: '#d8d0c1', winStrength: 0.33, winMix: 0.26,
  });
  const trimMat = makeFacadeMaterial(THREE, '#c3baa9', {
    style: 3, seed: 2.0, winW: 3.0, floorH: 3.5, ratioX: 0.2, ratioY: 0.2,
    glass: '#56666b', frame: '#b8afa0', winStrength: 0,
  });
  materials.push(brick, brickLight, brickDark, concrete, concreteLight, glass, glassLight, white, contextMat, campusBrick, campusStone, cityMat, cityMat2, cityMat3, trimMat);
  const hotelWhite = new THREE.MeshStandardMaterial({ color: '#ece7dd', roughness: 0.6, metalness: 0.02 });
  const blockzGreen = new THREE.MeshStandardMaterial({ color: '#6f8f5d', roughness: 0.95 });
  const blockxBlue = new THREE.MeshStandardMaterial({ color: '#376778', roughness: 0.8 });
  materials.push(hotelWhite, blockzGreen, blockxBlue);

  const FACADES = {
    core: [brick, brickLight, brickDark],
    facility: [concrete, concreteLight],
    residence: [concreteLight, white],
    library: [brick, brickDark],
    auditorium: [brickDark, brick],
    hotel: [glassLight, glass],
    glass: [glassLight, white],
    sports: [concreteLight, glass],
    bay: [concrete, glassLight],
  };

  // ---- landmarks -----------------------------------------------------------
  (opts.noLandmarks ? [] : (data.landmarks || [])).forEach((l, idx) => {
    if (!l.footprint || l.footprint.length < 3) return;
    if (/tang ping yuan building/i.test(l.name) && opts.tangModel) {
      const model = opts.tangModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('TPY_brick')) return campusBrick;
        if (n.startsWith('TPY_white')) return hotelWhite;
        if (n.startsWith('TPY_glass')) return glassLight;
        if (n.startsWith('TPY_green')) return blockzGreen;
        if (n.startsWith('TPY_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/fong shu chuen hall/i.test(l.name) && opts.fongModel) {
      const model = opts.fongModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('FSC_brick')) return campusBrick;
        if (n.startsWith('FSC_white')) return hotelWhite;
        if (n.startsWith('FSC_glass')) return glassLight;
        if (n.startsWith('FSC_green')) return blockzGreen;
        if (n.startsWith('FSC_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/stanley ho building/i.test(l.name) && opts.stanleyModel) {
      const model = opts.stanleyModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('SHB_brick')) return campusBrick;
        if (n.startsWith('SHB_white')) return hotelWhite;
        if (n.startsWith('SHB_glass')) return glassLight;
        if (n.startsWith('SHB_green')) return blockzGreen;
        if (n.startsWith('SHB_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/seal of love foundation building/i.test(l.name) && opts.sealModel) {
      const model = opts.sealModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('SOL_brick')) return campusBrick;
        if (n.startsWith('SOL_white')) return hotelWhite;
        if (n.startsWith('SOL_glass')) return glassLight;
        if (n.startsWith('SOL_green')) return blockzGreen;
        if (n.startsWith('SOL_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/chung sze yuen building/i.test(l.name) && opts.chungModel) {
      const model = opts.chungModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('CSY_brick')) return campusBrick;
        if (n.startsWith('CSY_white')) return hotelWhite;
        if (n.startsWith('CSY_glass')) return glassLight;
        if (n.startsWith('CSY_green')) return blockzGreen;
        if (n.startsWith('CSY_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/house of innovation/i.test(l.name) && opts.hoiModel) {
      const model = opts.hoiModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('HOI_brick')) return campusBrick;
        if (n.startsWith('HOI_white')) return hotelWhite;
        if (n.startsWith('HOI_glass')) return glassLight;
        if (n.startsWith('HOI_green')) return blockzGreen;
        if (n.startsWith('HOI_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/anita chan lai ling building/i.test(l.name) && opts.anitaModel) {
      const model = opts.anitaModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('ACL_brick')) return campusBrick;
        if (n.startsWith('ACL_white')) return hotelWhite;
        if (n.startsWith('ACL_glass')) return glassLight;
        if (n.startsWith('ACL_green')) return blockzGreen;
        if (n.startsWith('ACL_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/cma building/i.test(l.name) && opts.cmaModel) {
      const model = opts.cmaModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('CMA_brick')) return campusBrick;
        if (n.startsWith('CMA_white')) return hotelWhite;
        if (n.startsWith('CMA_glass')) return glassLight;
        if (n.startsWith('CMA_green')) return blockzGreen;
        if (n.startsWith('CMA_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/gh block/i.test(l.name) && opts.ghModel) {
      const model = opts.ghModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('GHB_brick')) return campusBrick;
        if (n.startsWith('GHB_white')) return hotelWhite;
        if (n.startsWith('GHB_glass')) return glassLight;
        if (n.startsWith('GHB_green')) return blockzGreen;
        if (n.startsWith('GHB_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/lui che woo building/i.test(l.name) && opts.luiModel) {
      const model = opts.luiModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('LCW_brick')) return campusBrick;
        if (n.startsWith('LCW_white')) return white;
        if (n.startsWith('LCW_glass')) return glassLight;
        if (n.startsWith('LCW_green')) return blockzGreen;
        if (n.startsWith('LCW_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/chan tai ho building/i.test(l.name) && opts.taioModel) {
      const model = opts.taioModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('CTH_stone')) return campusStone;
        if (n.startsWith('CTH_white')) return hotelWhite;
        if (n.startsWith('CTH_glass')) return glassLight;
        if (n.startsWith('CTH_green')) return blockzGreen;
        if (n.startsWith('CTH_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/chan sui wai building/i.test(l.name) && opts.chanModel) {
      const model = opts.chanModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('CSW_brick')) return campusBrick;
        if (n.startsWith('CSW_white')) return hotelWhite;
        if (n.startsWith('CSW_glass')) return glassLight;
        if (n.startsWith('CSW_green')) return blockzGreen;
        if (n.startsWith('CSW_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/yip kit chuen building/i.test(l.name) && opts.yipModel) {
      const model = opts.yipModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('YKC_brick')) return campusBrick;
        if (n.startsWith('YKC_white')) return hotelWhite;
        if (n.startsWith('YKC_glass')) return glassLight;
        if (n.startsWith('YKC_green')) return blockzGreen;
        if (n.startsWith('YKC_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/ng wing hong building/i.test(l.name) && opts.ngModel) {
      const model = opts.ngModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('NWH_brick')) return campusBrick;
        if (n.startsWith('NWH_upper')) return white;
        if (n.startsWith('NWH_white')) return hotelWhite;
        if (n.startsWith('NWH_glass')) return glassLight;
        if (n.startsWith('NWH_green')) return blockzGreen;
        if (n.startsWith('NWH_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/mong man wai building/i.test(l.name) && opts.mongModel) {
      const model = opts.mongModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('MMW_brick')) return campusBrick;
        if (n.startsWith('MMW_white')) return hotelWhite;
        if (n.startsWith('MMW_glass')) return glassLight;
        if (n.startsWith('MMW_green')) return blockzGreen;
        if (n.startsWith('MMW_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/chow yei ching building/i.test(l.name) && opts.chowModel) {
      const model = opts.chowModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('CHW_brick')) return campusBrick;
        if (n.startsWith('CHW_white')) return hotelWhite;
        if (n.startsWith('CHW_glass')) return glassLight;
        if (n.startsWith('CHW_green')) return blockzGreen;
        if (n.startsWith('CHW_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/choi kai yau building/i.test(l.name) && opts.choiModel) {
      const model = opts.choiModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('CHK_brick')) return campusBrick;
        if (n.startsWith('CHK_white')) return hotelWhite;
        if (n.startsWith('CHK_glass')) return glassLight;
        if (n.startsWith('CHK_green')) return blockzGreen;
        if (n.startsWith('CHK_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/shirley chan building/i.test(l.name) && opts.shirleyModel) {
      const model = opts.shirleyModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('SHC_brick')) return campusBrick;
        if (n.startsWith('SHC_white')) return hotelWhite;
        if (n.startsWith('SHC_glass')) return glassLight;
        if (n.startsWith('SHC_green')) return blockzGreen;
        if (n.startsWith('SHC_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    const autoModel = opts.autoModels && opts.autoModels[l.name];
    if (autoModel) {
      const model = autoModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('GEN_brick')) return campusBrick;
        if (n.startsWith('GEN_white')) return hotelWhite;
        if (n.startsWith('GEN_upper')) return white;
        if (n.startsWith('GEN_glass')) return glassLight;
        if (n.startsWith('GEN_green')) return blockzGreen;
        if (n.startsWith('GEN_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/industrial centre/i.test(l.name) && opts.industrialModel) {
      const model = opts.industrialModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('IND_brick')) return campusBrick;
        if (n.startsWith('IND_white')) return hotelWhite;
        if (n.startsWith('IND_glass')) return glassLight;
        if (n.startsWith('IND_green')) return blockzGreen;
        if (n.startsWith('IND_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/lee shau kee building/i.test(l.name) && opts.leeshaukeeModel) {
      const model = opts.leeshaukeeModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('LSKB_brick')) return campusBrick;
        if (n.startsWith('LSKB_white')) return hotelWhite;
        if (n.startsWith('LSKB_glass')) return glassLight;
        if (n.startsWith('LSKB_green')) return blockzGreen;
        if (n.startsWith('LSKB_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/global student hub/i.test(l.name) && opts.gshModel) {
      const model = opts.gshModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('GSH_brick')) return campusBrick;
        if (n.startsWith('GSH_white')) return hotelWhite;
        if (n.startsWith('GSH_glass')) return glassLight;
        if (n.startsWith('GSH_green')) return blockzGreen;
        if (n.startsWith('GSH_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/shaw sports complex/i.test(l.name) && opts.shawModel) {
      const model = opts.shawModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('SHAW_brick')) return campusBrick;
        if (n.startsWith('SHAW_white')) return hotelWhite;
        if (n.startsWith('SHAW_glass')) return glassLight;
        if (n.startsWith('SHAW_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/communal building/i.test(l.name) && opts.communalModel) {
      const model = opts.communalModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('COM_brick')) return campusBrick;
        if (n.startsWith('COM_white')) return hotelWhite;
        if (n.startsWith('COM_glass')) return glassLight;
        if (n.startsWith('COM_green')) return blockzGreen;
        if (n.startsWith('COM_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/^block x$/i.test(l.name) && opts.blockxModel) {
      const model = opts.blockxModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('BLKX_brick')) return campusBrick;
        if (n.startsWith('BLKX_white')) return hotelWhite;
        if (n.startsWith('BLKX_glass')) return glassLight;
        if (n.startsWith('BLKX_blue')) return blockxBlue;
        if (n.startsWith('BLKX_green')) return blockzGreen;
        if (n.startsWith('BLKX_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/^block z$/i.test(l.name) && opts.blockzModel) {
      const model = opts.blockzModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('BLKZ_brick')) return campusBrick;
        if (n.startsWith('BLKZ_white')) return hotelWhite;
        if (n.startsWith('BLKZ_glass')) return glassLight;
        if (n.startsWith('BLKZ_green')) return blockzGreen;
        if (n.startsWith('BLKZ_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/li ka shing tower/i.test(l.name) && opts.lksModel) {
      const model = opts.lksModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('LKS_terracotta') || n.startsWith('LKS_brick')) return campusBrick;
        if (n.startsWith('LKS_glazing') || n.startsWith('LKS_glass')) return glassLight;
        if (n.startsWith('LKS_stone')) return campusStone;
        if (n.startsWith('LKS_metal') || n.startsWith('LKS_white')) return hotelWhite;
        if (n.startsWith('LKS_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/hotel icon/i.test(l.name) && opts.hotelModel) {
      const model = opts.hotelModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('HICON_white')) return hotelWhite;
        if (n.startsWith('HICON_glass')) return glassLight;
        if (n.startsWith('HICON_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/jockey club auditorium/i.test(l.name) && opts.jcaModel) {
      const model = opts.jcaModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('JCA_white')) return trimMat;
        if (n.startsWith('JCA_glass')) return glassLight;
        if (n.startsWith('JCA_brick')) return brick;
        if (n.startsWith('JCA_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/pao yue-kong library/i.test(l.name) && opts.libraryModel) {
      const model = opts.libraryModel.clone(true);
      const [mcx, mcz] = l.center || [0, 0];
      model.position.set(mcx, 0, mcz);
      const mapMat = (m) => {
        const n = (m && m.name) || '';
        if (n.startsWith('LIB_brick')) return brick;
        if (n.startsWith('LIB_glass')) return glassLight;
        if (n.startsWith('LIB_white')) return trimMat;
        if (n.startsWith('LIB_dark')) return glass;
        return m;
      };
      model.traverse((o) => {
        if (!o.isMesh) return;
        o.material = Array.isArray(o.material) ? o.material.map(mapMat) : mapMat(o.material);
        o.castShadow = true;
        o.receiveShadow = true;
        landmarks.push({ mesh: o, data: l });
      });
      group.add(model);
      return;
    }
    if (/innovation tower/i.test(l.name)) {
      if (opts.jcitModel) {
        const model = opts.jcitModel.clone(true);
        const [mcx, mcz] = l.center || [0, 0];
        model.position.set(mcx, 0, mcz);
        model.traverse((o) => {
          if (!o.isMesh) return;
          o.castShadow = true;
          o.receiveShadow = true;
          landmarks.push({ mesh: o, data: l });
        });
        group.add(model);
      } else {
        buildJCITTower(THREE, l, group, landmarks, materials, { glass: glassLight, sky: glassLight });
      }
      return;
    }
    const kind = classifyLandmark(l.name);
    const mats = FACADES[kind] || FACADES.facility;
    const mat = mats[idx % mats.length];
    const geom = extrudeBuilding(THREE, l.footprint, Math.max(3, l.height || 18));
    disposables.push(geom);
    const mesh = new THREE.Mesh(geom, mat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.landmark = l;
    mesh.userData.baseMaterial = mat;
    group.add(mesh);

    // crisp model-board edge lines
    const edges = new THREE.EdgesGeometry(geom, 28);
    const line = new THREE.LineSegments(
      edges,
      new THREE.LineBasicMaterial({ color: 0x3a332c, transparent: true, opacity: 0.16 })
    );
    line.position.copy(mesh.position);
    group.add(line);
    disposables.push(edges);

    // landmark-specific silhouette accents
    if (kind === 'glass' && /innovation tower/i.test(l.name)) {
      const accent = new THREE.Mesh(
        new THREE.BoxGeometry(4, l.height * 0.55, 4),
        white
      );
      const [cx, cz] = l.center || centroid(l.footprint);
      accent.position.set(cx + 14, l.height * 0.55 * 0.5, cz - 8);
      accent.castShadow = true;
      group.add(accent);
    }
    if (kind === 'auditorium') {
      const [cx, cz] = l.center || centroid(l.footprint);
      const canopy = new THREE.Mesh(new THREE.BoxGeometry(34, 2.4, 24), white);
      canopy.position.set(cx, (l.height || 12) + 2.4, cz);
      canopy.castShadow = true;
      group.add(canopy);
    }
    if (kind === 'library') {
      const [cx, cz] = l.center || centroid(l.footprint);
      const lantern = new THREE.Mesh(new THREE.BoxGeometry(20, 6, 20), glassLight);
      lantern.position.set(cx, (l.height || 30) + 4, cz);
      lantern.castShadow = true;
      group.add(lantern);
    }
    if (kind === 'sports') {
      const [cx, cz] = l.center || centroid(l.footprint);
      const strip = new THREE.Mesh(new THREE.BoxGeometry(30, 1.2, 14), new THREE.MeshStandardMaterial({ color: '#6f97ab', roughness: 0.6 }));
      strip.position.set(cx, (l.height || 12) + 2, cz);
      group.add(strip);
    }

    landmarks.push({ mesh, data: l });
  });

  // ---- context massing (merged, split into campus fabric vs surrounding city) ----
  if (!opts.noContext) {
  // OSM records that duplicate the custom Hotel ICON tower/podium; keep
  // University House (236028367) remains a separate building.
  const excludedContextIds = new Set([236028367, 236028374, 236028379]);
  const campusGeoms = [];
  const cityGeoms = [];
  renderContext.forEach((b, i) => {
    if (!b.footprint || b.footprint.length < 3) return;
    if (excludedContextIds.has(b.id)) return;
    const h = Math.max(4, b.height || 16);
    const g = extrudeBuilding(THREE, b.footprint, h, { bevel: 0, holes: b.holes });
    const [cx, cz] = b.center || centroid(b.footprint);
    const isCampus =
      cx > -185 && cx < 205 && cz > -350 && cz < 265;
    (isCampus ? campusGeoms : cityGeoms).push({ g, i });
  });
  const mergeInto = (items, mat) => {
    if (!items.length) return;
    const merged = mergeGeometries(items.map((x) => x.g), false);
    disposables.push(merged, ...items.map((x) => x.g));
    const mesh = new THREE.Mesh(merged, mat);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    mesh.userData.context = true;
    group.add(mesh);
  };
  // alternate brick / stone for a varied campus fabric
  const campusBrickGeoms = campusGeoms.filter((x) => x.i % 2 === 0);
  const campusStoneGeoms = campusGeoms.filter((x) => x.i % 2 === 1);
  mergeInto(campusBrickGeoms, campusBrick);
  mergeInto(campusStoneGeoms, campusStone);
  mergeInto(cityGeoms.filter((x) => x.i % 3 === 0), cityMat);
  mergeInto(cityGeoms.filter((x) => x.i % 3 === 1), cityMat2);
  mergeInto(cityGeoms.filter((x) => x.i % 3 === 2), cityMat3);
  group.add(buildContextDetails(THREE, renderContext, materials, data.sceneLayout?.landmarkEnvelopes || []));
  }

  // ---- ground plane details ------------------------------------------------
  if (!opts.noRoads) {
    const roadsGroup = buildRibbons(THREE, data.roads, materials);
    group.add(roadsGroup);
  }
  if (!opts.noAreas) {
    const areasGroup = buildAreas(THREE, data.areas);
    group.add(areasGroup);
  }
  if (!opts.noTrees) {
    const trees = buildTrees(THREE, data.landmarks || [], data.areas, data.sceneLayout?.treeObstacles || []);
    group.add(trees);
  }
  if (!opts.noRoofs) {
    const custom = [];
    if (opts.jcitModel) custom.push(/innovation tower/i);
    if (opts.libraryModel) custom.push(/pao yue-kong library/i);
    if (opts.jcaModel) custom.push(/jockey club auditorium/i);
    if (opts.hotelModel) custom.push(/hotel icon/i);
    if (opts.lksModel) custom.push(/li ka shing tower/i);
    if (opts.blockzModel) custom.push(/^block z$/i);
    if (opts.blockxModel) custom.push(/^block x$/i);
    if (opts.communalModel) custom.push(/communal building/i);
    if (opts.shawModel) custom.push(/shaw sports complex/i);
    if (opts.gshModel) custom.push(/global student hub/i);
    if (opts.leeshaukeeModel) custom.push(/lee shau kee building/i);
    if (opts.industrialModel) custom.push(/industrial centre/i);
    if (opts.shirleyModel) custom.push(/shirley chan building/i);
    if (opts.choiModel) custom.push(/choi kai yau building/i);
    if (opts.chowModel) custom.push(/chow yei ching building/i);
    if (opts.mongModel) custom.push(/mong man wai building/i);
    if (opts.ngModel) custom.push(/ng wing hong building/i);
    if (opts.yipModel) custom.push(/yip kit chuen building/i);
    if (opts.chanModel) custom.push(/chan sui wai building/i);
    if (opts.taioModel) custom.push(/chan tai ho building/i);
    if (opts.luiModel) custom.push(/lui che woo building/i);
    if (opts.ghModel) custom.push(/gh block/i);
    if (opts.cmaModel) custom.push(/cma building/i);
    if (opts.anitaModel) custom.push(/anita chan lai ling building/i);
    if (opts.hoiModel) custom.push(/house of innovation/i);
    if (opts.chungModel) custom.push(/chung sze yuen building/i);
    if (opts.sealModel) custom.push(/seal of love foundation building/i);
    if (opts.stanleyModel) custom.push(/stanley ho building/i);
    if (opts.fongModel) custom.push(/fong shu chuen hall/i);
    if (opts.tangModel) custom.push(/tang ping yuan building/i);
    const auto = opts.autoModels || {};
    const detailLandmarks = (data.landmarks || []).filter(
      (l) => !custom.some((re) => re.test(l.name || '')) && !auto[l.name]
    );
    const roofs = buildRoofDetails(THREE, detailLandmarks, materials);
    group.add(roofs);
    const parapets = buildParapets(THREE, detailLandmarks, trimMat);
    group.add(parapets);
    const details = buildLandmarkDetails(THREE, detailLandmarks, materials);
    group.add(details);
    buildEntranceSigns(THREE, data.landmarks || [], materials, group, data.hotelEntranceRegistration);
  }

  function setNight(v) {
    SHARED.uNight.value = v;
  }

  function dispose() {
    group.traverse((o) => {
      if (o.geometry) o.geometry.dispose();
      if (o.material) {
        if (Array.isArray(o.material)) o.material.forEach((m) => m.dispose());
        else o.material.dispose();
      }
    });
    materials.forEach((m) => m.dispose());
  }

  for (const entry of landmarks) {
    if (entry.mesh) entry.mesh.userData.landmark = entry.data;
  }
  return { group, landmarks, setNight, dispose };
}
