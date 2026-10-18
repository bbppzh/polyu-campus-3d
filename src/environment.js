/**
 * PolyU campus diorama — environment module.
 *
 * Stylized architectural-model look: warm light, soft shadows, hazy Hong Kong air.
 * Campus landmarks sit roughly inside x,z ∈ [-260, 260] m (x = east, z = south).
 * Victoria Harbour is a water plane to the south (z from +420 to +1400, full width)
 * and a fogged low-poly skyline ring (r 800–1100 m) closes off the north/east/west.
 *
 * Public API (exact):
 *   export function createEnvironment({ THREE, scene, size = 2400 })
 *     -> { sky, sun, hemi, ground, water, setTimeOfDay(t), update(dt, elapsed), dispose() }
 *
 * setTimeOfDay(t): 0 = midnight, 0.25 = sunrise, 0.5 = noon, 0.75 = sunset, 1 = midnight.
 * It drives scene.background, scene.fog (color/near/far), the sun position/colour/intensity,
 * the hemisphere + ambient light colours/intensities, the sky-dome gradient/sun disc and
 * the star opacity. It is cheap enough to call on every slider frame.
 *
 * update(dt, elapsed): only animates the harbour ripple (analytic vertex displacement;
 * normals are rebuilt analytically). No per-frame allocations and no Vector3 churn.
 *
 * Assumptions / integration notes:
 *  - THREE is injected by the caller (no import at all, so no import-map needed here).
 *  - Renderer should use renderer.shadowMap.enabled = true and
 *    renderer.shadowMap.type = THREE.PCFSoftShadowMap; the sun is configured for it.
 *    Standard-color output (renderer.outputColorSpace = SRGBColorSpace) is expected.
 *  - Sky-dome radius is size * 0.6 = 1440 m, so the camera far plane must reach that.
 *  - Ground/harbour: the mandated 2400² land plane would otherwise sit ABOVE the water
 *    (y=-0.02 vs y=-0.5) and hide it for z < +1200. To keep the mandated water visible,
 *    the land plane keeps its size/position but its harbour cells (z > +420) are removed
 *    from the index, producing a clean straight quay edge at z ≈ +620 (exact for the
 *    default size). Set CUT_HARBOUR_FROM_GROUND = false to get a full 2400² plane back.
 *  - Fog near/far are camera-distance based; they are tuned for a diorama orbit of
 *    roughly 600–1000 m so the campus stays crisp and the ring reads as distant haze.
 */

const TAU = Math.PI * 2;
const DEG = Math.PI / 180;

// Land / water layout (metres, world units).
const HARBOUR_Z = 620; // shoreline (land ends, water starts); keeps Hotel ICON + all context on land
const WATER_SOUTH_EDGE = 1600; // far edge of the harbour
const CUT_HARBOUR_FROM_GROUND = true;

// Sun path.
const MAX_SUN_ELEVATION = 1.22; // radians (~70°)
const SUN_DISTANCE = 1300; // metres from the target
const MOON_INTENSITY = 0.38;
const STAR_COUNT = 650;

// Distant skyline ring.
const SKYLINE_COUNT = 120;
const SKYLINE_RING_MIN = 800;
const SKYLINE_RING_MAX = 1100;
// Angles measured with 0 = +x (east) and +pi/2 = +z (south). The harbour occupies the
// south sector; boxes are laid across the remaining 214° arc (east → north → west).
const SKYLINE_ARC_START = 163 * DEG;
const SKYLINE_ARC_LENGTH = 214 * DEG;

// Land plane segmentation (used for the harbour cut).
const GROUND_SEGMENTS_Z = 120;

// Time-of-day keyframes. Colours are sRGB hex; intensities are three.js physical values.
const PALETTE = [
  { t: 0.0, zenith: 0x040812, horizon: 0x0d1828, sun: 0xa9bde0, sunI: 0.0, hemiSky: 0x22314e, hemiGround: 0x0d1016, hemiI: 0.18, ambient: 0x34435f, ambI: 0.3, fogNear: 450, fogFar: 1900 },
  { t: 0.18, zenith: 0x0e1a2f, horizon: 0x2b3350, sun: 0xffa76d, sunI: 0.05, hemiSky: 0x2f3d5c, hemiGround: 0x171820, hemiI: 0.22, ambient: 0x3a4766, ambI: 0.3, fogNear: 450, fogFar: 2000 },
  { t: 0.25, zenith: 0x3f5c8f, horizon: 0xd9885c, sun: 0xff8a45, sunI: 0.9, hemiSky: 0x94a7c8, hemiGround: 0x6a5a4a, hemiI: 0.34, ambient: 0x8b7a72, ambI: 0.2, fogNear: 600, fogFar: 2300 },
  { t: 0.34, zenith: 0x5a88bd, horizon: 0xc6d5da, sun: 0xffd3a4, sunI: 1.7, hemiSky: 0xb8cfe8, hemiGround: 0xaea28f, hemiI: 0.46, ambient: 0xc4beb2, ambI: 0.2, fogNear: 680, fogFar: 2450 },
  { t: 0.5, zenith: 0x4a86c8, horizon: 0xd2e0e6, sun: 0xfff3dc, sunI: 2.1, hemiSky: 0xc9def4, hemiGround: 0xc4b9a3, hemiI: 0.58, ambient: 0xd8d2c4, ambI: 0.22, fogNear: 700, fogFar: 2500 },
  { t: 0.66, zenith: 0x5a8cc0, horizon: 0xd8d9cf, sun: 0xffe6bb, sunI: 1.8, hemiSky: 0xc2d5e9, hemiGround: 0xc2b49d, hemiI: 0.5, ambient: 0xd0c6b4, ambI: 0.2, fogNear: 680, fogFar: 2450 },
  { t: 0.75, zenith: 0x4f5c8e, horizon: 0xe87c46, sun: 0xff7436, sunI: 0.95, hemiSky: 0xb98f7e, hemiGround: 0x846349, hemiI: 0.34, ambient: 0x9a7a68, ambI: 0.18, fogNear: 600, fogFar: 2300 },
  { t: 0.82, zenith: 0x1b2848, horizon: 0x6e3f47, sun: 0xff5a2b, sunI: 0.12, hemiSky: 0x3b4260, hemiGround: 0x221a1a, hemiI: 0.22, ambient: 0x3a4160, ambI: 0.24, fogNear: 480, fogFar: 2000 },
  { t: 1.0, zenith: 0x040812, horizon: 0x0d1828, sun: 0xa9bde0, sunI: 0.0, hemiSky: 0x22314e, hemiGround: 0x0d1016, hemiI: 0.18, ambient: 0x34435f, ambI: 0.3, fogNear: 450, fogFar: 1900 },
];

// Cheap shore swell: [amplitude, kx, kz, phase speed].
const WAVES = [
  [0.22, 0.06, 0.024, 0.8],
  [0.13, -0.035, 0.075, 1.15],
  [0.06, 0.11, -0.032, 1.6],
];

const SKY_VERTEX_SHADER = /* glsl */ `
  varying vec3 vSkyWorldPosition;

  void main() {
    vec4 worldPosition = modelMatrix * vec4( position, 1.0 );
    vSkyWorldPosition = worldPosition.xyz;
    gl_Position = projectionMatrix * viewMatrix * worldPosition;
  }
`;

const SKY_FRAGMENT_SHADER = /* glsl */ `
  uniform vec3 uZenith;
  uniform vec3 uHorizon;
  uniform vec3 uSunColor;
  uniform vec3 uSunDir;
  uniform float uSunStrength;
  varying vec3 vSkyWorldPosition;

  #include <common>
  #include <dithering_pars_fragment>

  void main() {
    // View direction from the camera: correct even when the orbit camera is far from
    // the dome center. cameraPosition is a built-in three.js ShaderMaterial uniform.
    vec3 dir = normalize( vSkyWorldPosition - cameraPosition );

    // Smooth vertical gradient: pale hazy horizon -> saturated zenith.
    float height = clamp( dir.y, 0.0, 1.0 );
    vec3 color = mix( uHorizon, uZenith, pow( height, 0.42 ) );

    // Soft sun disc + two halos. uSunStrength fades it out below the horizon.
    float sunDot = clamp( dot( dir, normalize( uSunDir ) ), 0.0, 1.0 );
    float wideHalo = pow( sunDot, 8.0 ) * 0.12;
    float tightHalo = pow( sunDot, 64.0 ) * 0.35;
    float disc = smoothstep( 0.99955, 0.99990, sunDot );
    color += uSunColor * ( wideHalo + tightHalo + disc * 1.6 ) * uSunStrength;

    // Below the horizon: gently sink into a darker version of the horizon haze so the
    // dome never shows a hard seam at dir.y == 0.
    float below = smoothstep( 0.0, -0.16, dir.y );
    color = mix( color, uHorizon * 0.82, below * 0.85 );

    gl_FragColor = vec4( color, 1.0 );

    #include <tonemapping_fragment>
    #include <colorspace_fragment>
    #include <dithering_fragment>
  }
`;

function smoothstep(edge0, edge1, x) {
  if (edge0 === edge1) return x < edge0 ? 0 : 1;
  const t = Math.min(Math.max((x - edge0) / (edge1 - edge0), 0), 1);
  return t * t * (3 - 2 * t);
}

/** Deterministic PRNG so the diorama is identical on every reload. */
function mulberry32(seed) {
  let a = seed >>> 0;
  return function random() {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function createEnvironment({ THREE, scene, size = 2400 } = {}) {
  if (!THREE) throw new Error('createEnvironment: THREE is required');
  if (!scene) throw new Error('createEnvironment: scene is required');

  const halfSize = size / 2;

  // ---------------------------------------------------------------------------
  // Palette (colors are converted once; per-frame interpolation writes into temps)
  // ---------------------------------------------------------------------------
  const keys = PALETTE.map((key) => ({
    t: key.t,
    zenith: new THREE.Color(key.zenith),
    horizon: new THREE.Color(key.horizon),
    sun: new THREE.Color(key.sun),
    hemiSky: new THREE.Color(key.hemiSky),
    hemiGround: new THREE.Color(key.hemiGround),
    ambient: new THREE.Color(key.ambient),
    sunI: key.sunI,
    hemiI: key.hemiI,
    ambI: key.ambI,
    fogNear: key.fogNear,
    fogFar: key.fogFar,
  }));

  const cZenith = new THREE.Color();
  const cHorizon = new THREE.Color();
  const cSun = new THREE.Color();
  const cHemiSky = new THREE.Color();
  const cHemiGround = new THREE.Color();
  const cAmbient = new THREE.Color();
  const sunDir = new THREE.Vector3(); // unit vector from the scene toward the sun

  // ---------------------------------------------------------------------------
  // Sky dome
  // ---------------------------------------------------------------------------
  const skyGeometry = new THREE.SphereGeometry(size * 0.6, 32, 16);
  const skyMaterial = new THREE.ShaderMaterial({
    uniforms: {
      uZenith: { value: new THREE.Color(0x4a86c8) },
      uHorizon: { value: new THREE.Color(0xd2e0e6) },
      uSunColor: { value: new THREE.Color(0xfff3dc) },
      uSunDir: { value: new THREE.Vector3(0, 1, 0) },
      uSunStrength: { value: 1 },
    },
    vertexShader: SKY_VERTEX_SHADER,
    fragmentShader: SKY_FRAGMENT_SHADER,
    side: THREE.BackSide,
    depthWrite: false,
    fog: false,
    toneMapped: false,
    dithering: true,
  });
  const sky = new THREE.Mesh(skyGeometry, skyMaterial);
  sky.name = 'environment.sky';
  sky.frustumCulled = false;
  sky.renderOrder = -10; // always paint behind the diorama

  // ---------------------------------------------------------------------------
  // Stars (cheap Points, upper hemisphere, only visible at night)
  // ---------------------------------------------------------------------------
  const starRandom = mulberry32(0x51a7c0de);
  const starPositions = new Float32Array(STAR_COUNT * 3);
  const starRadius = size * 0.52;
  for (let i = 0; i < STAR_COUNT; i += 1) {
    const y = 0.05 + starRandom() * 0.95;
    const phi = starRandom() * TAU;
    const r = Math.sqrt(1 - y * y);
    const index = i * 3;
    starPositions[index] = Math.cos(phi) * r * starRadius;
    starPositions[index + 1] = y * starRadius;
    starPositions[index + 2] = Math.sin(phi) * r * starRadius;
  }
  const starGeometry = new THREE.BufferGeometry();
  starGeometry.setAttribute('position', new THREE.BufferAttribute(starPositions, 3));
  const starMaterial = new THREE.PointsMaterial({
    color: 0xd7e2ff,
    size: 1.7,
    sizeAttenuation: false,
    transparent: true,
    opacity: 0,
    depthWrite: false,
    fog: false,
    toneMapped: false,
  });
  const stars = new THREE.Points(starGeometry, starMaterial);
  stars.name = 'environment.stars';
  stars.frustumCulled = false;
  stars.renderOrder = -5;
  stars.visible = false;

  // ---------------------------------------------------------------------------
  // Lights
  // ---------------------------------------------------------------------------
  const sun = new THREE.DirectionalLight(0xfff3dc, 2.1);
  sun.name = 'environment.sun';
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  sun.shadow.camera.left = -600;
  sun.shadow.camera.right = 600;
  sun.shadow.camera.top = 600;
  sun.shadow.camera.bottom = -600;
  sun.shadow.camera.near = 1;
  sun.shadow.camera.far = 2500;
  sun.shadow.bias = -0.0005;
  sun.shadow.normalBias = 0.02;
  sun.shadow.camera.updateProjectionMatrix();
  const sunTarget = new THREE.Object3D();
  sunTarget.position.set(0, 0, 0);
  sun.target = sunTarget;

  // A soft, shadowless moon keeps the model-board readable at night / for window emissives.
  const moon = new THREE.DirectionalLight(0xa9c2ff, 0);
  moon.name = 'environment.moon';
  moon.castShadow = false;

  const hemi = new THREE.HemisphereLight(0xc9def4, 0xc4b9a3, 0.58);
  hemi.name = 'environment.hemi';
  const ambient = new THREE.AmbientLight(0xd8d2c4, 0.22);
  ambient.name = 'environment.ambient';

  // ---------------------------------------------------------------------------
  // Ground (land board). Harbour cells are stripped from the index so the water
  // below at y = -0.5 is actually visible instead of being covered by the board.
  // ---------------------------------------------------------------------------
  const groundGeometry = new THREE.PlaneGeometry(size, size, 1, GROUND_SEGMENTS_Z);
  groundGeometry.rotateX(-Math.PI / 2);

  const groundStep = size / GROUND_SEGMENTS_Z;
  // PlaneGeometry rows run north (z = -halfSize) -> south (z = +halfSize), and with
  // the -90° X rotation world z = row * groundStep - halfSize.
  const cutRow = Math.round((halfSize + HARBOUR_Z) / groundStep);
  let shoreZ = halfSize < HARBOUR_Z ? halfSize : HARBOUR_Z;
  if (CUT_HARBOUR_FROM_GROUND && cutRow > 0 && cutRow < GROUND_SEGMENTS_Z) {
    shoreZ = cutRow * groundStep - halfSize;
    const source = groundGeometry.index.array;
    // 2 triangles per grid cell, one cell per row (widthSegments = 1): the first
    // `cutRow` rows are the land north of the shoreline.
    const kept = source.slice(0, cutRow * 6);
    groundGeometry.setIndex(new THREE.BufferAttribute(kept, 1));
  }

  const groundMaterial = new THREE.MeshStandardMaterial({
    color: 0xd7d1c4,
    roughness: 1.0,
    metalness: 0.0,
  });
  const ground = new THREE.Mesh(groundGeometry, groundMaterial);
  ground.name = 'environment.ground';
  ground.position.set(0, -0.02, 0);
  ground.receiveShadow = true;

  // ---------------------------------------------------------------------------
  // Water (Victoria Harbour). A segmented plane so update() can add gentle swell.
  // ---------------------------------------------------------------------------
  const waterNorth = shoreZ;
  const waterDepth = WATER_SOUTH_EDGE - waterNorth;
  const waterGeometry = new THREE.PlaneGeometry(size, waterDepth, 96, 36);
  waterGeometry.rotateX(-Math.PI / 2);
  const waterMaterial = new THREE.MeshStandardMaterial({
    color: 0x5f828c,
    roughness: 0.15,
    metalness: 0.35,
  });
  const water = new THREE.Mesh(waterGeometry, waterMaterial);
  water.name = 'environment.water';
  water.position.set(0, -0.5, waterNorth + waterDepth / 2);
  water.receiveShadow = true;

  const waterPositionAttribute = waterGeometry.getAttribute('position');
  const waterNormalAttribute = waterGeometry.getAttribute('normal');
  const waterPositions = waterPositionAttribute.array;
  const waterNormals = waterNormalAttribute.array;
  const waterVertexCount = waterPositions.length / 3;

  function updateWaterRipples(time) {
    for (let i = 0; i < waterVertexCount; i += 1) {
      const index = i * 3;
      const x = waterPositions[index];
      const z = waterPositions[index + 2];
      let height = 0;
      let slopeX = 0;
      let slopeZ = 0;

      for (let w = 0; w < WAVES.length; w += 1) {
        const wave = WAVES[w];
        const phase = wave[1] * x + wave[2] * z + wave[3] * time;
        const sinPhase = Math.sin(phase);
        const cosPhase = Math.cos(phase);
        height += wave[0] * sinPhase;
        slopeX += wave[0] * wave[1] * cosPhase;
        slopeZ += wave[0] * wave[2] * cosPhase;
      }

      waterPositions[index + 1] = height;
      const invLength = 1 / Math.sqrt(slopeX * slopeX + slopeZ * slopeZ + 1);
      waterNormals[index] = -slopeX * invLength;
      waterNormals[index + 1] = invLength;
      waterNormals[index + 2] = -slopeZ * invLength;
    }

    waterPositionAttribute.needsUpdate = true;
    waterNormalAttribute.needsUpdate = true;
  }

  updateWaterRipples(0);

  // ---------------------------------------------------------------------------
  // Distant skyline ring (instanced boxes, muted blue-grey, fully fogged)
  // ---------------------------------------------------------------------------
  const skylineGeometry = new THREE.BoxGeometry(1, 1, 1);
  skylineGeometry.translate(0, 0.5, 0); // pivot at the base
  const skylineMaterial = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    roughness: 0.92,
    metalness: 0.0,
  });
  const skyline = new THREE.InstancedMesh(skylineGeometry, skylineMaterial, SKYLINE_COUNT);
  skyline.name = 'environment.skyline';
  skyline.castShadow = false;
  skyline.receiveShadow = false;
  skyline.frustumCulled = false;

  const skylineRandom = mulberry32(0x9e3779b9);
  const instanceDummy = new THREE.Object3D();
  const instanceColor = new THREE.Color();
  for (let i = 0; i < SKYLINE_COUNT; i += 1) {
    const angle =
      SKYLINE_ARC_START +
      ((i + 0.5) / SKYLINE_COUNT) * SKYLINE_ARC_LENGTH +
      (skylineRandom() - 0.5) * 0.014;
    const radius =
      SKYLINE_RING_MIN + skylineRandom() * (SKYLINE_RING_MAX - SKYLINE_RING_MIN);
    const width = 15 + skylineRandom() * 25;
    const depth = 12 + skylineRandom() * 18;
    const height = 20 + skylineRandom() * 70;

    instanceDummy.position.set(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
    instanceDummy.rotation.set(0, angle + Math.PI / 2, 0);
    instanceDummy.scale.set(width, height, depth);
    instanceDummy.updateMatrix();
    skyline.setMatrixAt(i, instanceDummy.matrix);

    instanceColor.setHSL(
      0.575 + skylineRandom() * 0.03,
      0.07 + skylineRandom() * 0.05,
      0.44 + skylineRandom() * 0.12,
    );
    skyline.setColorAt(i, instanceColor);
  }
  skyline.instanceMatrix.needsUpdate = true;
  if (skyline.instanceColor) skyline.instanceColor.needsUpdate = true;

  // ---------------------------------------------------------------------------
  // Atmosphere + scene graph
  // ---------------------------------------------------------------------------
  const fog = new THREE.Fog(0xd2e0e6, 700, 2500);
  scene.fog = fog;

  scene.add(sky);
  scene.add(stars);
  scene.add(sun);
  scene.add(sunTarget);
  scene.add(moon);
  scene.add(hemi);
  scene.add(ambient);
  scene.add(ground);
  scene.add(water);
  scene.add(skyline);

  // ---------------------------------------------------------------------------
  // Time of day
  // ---------------------------------------------------------------------------
  let internalElapsed = 0;
  let currentTime = 0.5;

  function setTimeOfDay(value) {
    const t = Math.min(Math.max(Number.isFinite(value) ? value : 0.5, 0), 1);
    currentTime = t;

    // Find the keyframe pair and ease between them.
    let i = 0;
    while (i < keys.length - 2 && t > keys[i + 1].t) i += 1;
    const from = keys[i];
    const to = keys[i + 1];
    const span = to.t - from.t;
    const rawU = span > 0 ? (t - from.t) / span : 0;
    const u = rawU * rawU * (3 - 2 * rawU);

    cZenith.copy(from.zenith).lerp(to.zenith, u);
    cHorizon.copy(from.horizon).lerp(to.horizon, u);
    cSun.copy(from.sun).lerp(to.sun, u);
    cHemiSky.copy(from.hemiSky).lerp(to.hemiSky, u);
    cHemiGround.copy(from.hemiGround).lerp(to.hemiGround, u);
    cAmbient.copy(from.ambient).lerp(to.ambient, u);

    const sunIntensity = from.sunI + (to.sunI - from.sunI) * u;
    const hemiIntensity = from.hemiI + (to.hemiI - from.hemiI) * u;
    const ambientIntensity = from.ambI + (to.ambI - from.ambI) * u;
    const fogNear = from.fogNear + (to.fogNear - from.fogNear) * u;
    const fogFar = from.fogFar + (to.fogFar - from.fogFar) * u;

    // Sun direction: elevation = -cos(2πt) so midnight is below the horizon, sunrise
    // (t=0.25) and sunset (t=0.75) are exactly on it and noon (t=0.5) is at the top.
    // Azimuth travels east -> south -> west over the day.
    const elevation = -Math.cos(TAU * t) * MAX_SUN_ELEVATION;
    const azimuth = Math.PI * (2 * t - 0.5);
    const cosElevation = Math.cos(elevation);
    sunDir.set(
      cosElevation * Math.cos(azimuth),
      Math.sin(elevation),
      cosElevation * Math.sin(azimuth),
    );

    // --- Sky dome ---
    skyMaterial.uniforms.uZenith.value.copy(cZenith);
    skyMaterial.uniforms.uHorizon.value.copy(cHorizon);
    skyMaterial.uniforms.uSunColor.value.copy(cSun);
    skyMaterial.uniforms.uSunDir.value.copy(sunDir);
    skyMaterial.uniforms.uSunStrength.value = smoothstep(-0.035, 0.05, sunDir.y);

    // --- Sun ---
    sun.position.copy(sunDir).multiplyScalar(SUN_DISTANCE);
    sun.color.copy(cSun);
    // Fade the directional light away as it sinks through the horizon.
    sun.intensity = sunIntensity * smoothstep(-0.04, 0.14, sunDir.y);
    sun.visible = sun.intensity > 0.001;

    // --- Moon (opposite the sun, only at night) ---
    moon.position.copy(sunDir).multiplyScalar(-SUN_DISTANCE);
    moon.intensity = MOON_INTENSITY * (1 - smoothstep(-0.08, 0.08, sunDir.y));
    moon.visible = moon.intensity > 0.001;

    // --- Hemisphere + ambient ---
    hemi.color.copy(cHemiSky);
    hemi.groundColor.copy(cHemiGround);
    hemi.intensity = hemiIntensity;
    ambient.color.copy(cAmbient);
    ambient.intensity = ambientIntensity;

    // --- Stars ---
    const starFactor = 1 - smoothstep(-0.18, 0.0, sunDir.y);
    starMaterial.opacity = 0.85 * starFactor;
    stars.visible = starFactor > 0.01;

    // --- Fog + background (same colour, so distant geometry melts into the horizon) ---
    fog.color.copy(cHorizon);
    fog.near = fogNear;
    fog.far = fogFar;
    scene.background = cHorizon;
  }

  // ---------------------------------------------------------------------------
  // Per-frame update
  // ---------------------------------------------------------------------------
  function update(dt, elapsed) {
    const delta = Number.isFinite(dt) ? Math.min(Math.max(dt, 0), 0.25) : 0;
    internalElapsed += delta;
    const time = Number.isFinite(elapsed) ? elapsed : internalElapsed;
    updateWaterRipples(time);
  }

  // ---------------------------------------------------------------------------
  // Dispose
  // ---------------------------------------------------------------------------
  function dispose() {
    const objects = [sky, stars, sun, sunTarget, moon, hemi, ambient, ground, water, skyline];
    for (let i = 0; i < objects.length; i += 1) {
      const object = objects[i];
      if (object && object.parent) object.parent.remove(object);
    }

    skyGeometry.dispose();
    skyMaterial.dispose();
    starGeometry.dispose();
    starMaterial.dispose();
    groundGeometry.dispose();
    groundMaterial.dispose();
    waterGeometry.dispose();
    waterMaterial.dispose();
    skylineGeometry.dispose();
    skylineMaterial.dispose();

    if (scene.fog === fog) scene.fog = null;
    if (scene.background === cHorizon) scene.background = null;
  }

  setTimeOfDay(currentTime);

  return {
    sky,
    sun,
    hemi,
    ground,
    water,
    setTimeOfDay,
    update,
    dispose,
  };
}
