import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createCampus, loadCampusTextures } from './buildings.js?v=20261019-alignment4';
import { createEnvironment } from './environment.js';

const $ = (id) => document.getElementById(id);
const params = new URLSearchParams(location.search);
const bootT = parseFloat(params.get('t'));

const state = {
  data: null,
  selected: null,
  hovered: null,
  labelsVisible: true,
  autoOrbit: false,
  t: Number.isFinite(bootT) ? Math.min(1, Math.max(0, bootT)) : 0.42,
  cameraTween: null,
  panoOpen: false,
};

const app = $('app');
const labelHost = $('labels');

const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;
renderer.outputColorSpace = THREE.SRGBColorSpace;
app.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 1, 6000);

const labelRenderer = new CSS2DRenderer({ element: labelHost });
labelRenderer.setSize(window.innerWidth, window.innerHeight);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.075;
controls.screenSpacePanning = false;
controls.maxPolarAngle = Math.PI * 0.495;
controls.minDistance = 35;
controls.maxDistance = 1400;
controls.target.set(0, 12, 0);
controls.autoRotateSpeed = 0.55;

const environment = createEnvironment({ THREE, scene, size: 2400 });
// keep the camera comfortably inside the sky dome so its gradient never clips
environment.sky.scale.setScalar(2.4);
let campus = null;
const labelObjects = [];

const clock = new THREE.Clock();
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2(-10, -10);

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
const BLURBS = [
  [/jockey club innovation tower/i, 'Zaha Hadid\u2019s Jockey Club Innovation Tower (2013) houses the School of Design \u2014 the campus\u2019s most sculptural landmark.'],
  [/pao yue-kong library|library/i, 'The Pao Yue-kong Library sits in the campus podium, with reading rooms, the LibCafe and the 24-hour study centre.'],
  [/jockey club auditorium/i, 'The Jockey Club Auditorium hosts concerts, ceremonies and public lectures at the heart of the campus.'],
  [/li ka shing tower/i, 'Li Ka Shing Tower (Block M) is one of the tallest academic towers on the podium, with interlocking academic blocks and an elevated cylindrical executive suite.'],
  [/hotel icon/i, 'PolyU\u2019s teaching hotel stands south-east of the main campus, close to the Hung Hom waterfront.'],
  [/block z/i, 'Block Z contains two academic wings, a lower teaching block and landscaped terraces across Chatham Road.'],
  [/block x/i, 'Block X gathers sports facilities and teaching rooms on the eastern side of the podium.'],
  [/industrial centre/i, 'The Industrial Centre provides engineering workshops, fabrication labs and prototyping space.'],
  [/communal building/i, 'The Communal Building holds canteens, student services and the University Gallery.'],
  [/shaw sports/i, 'Shaw Sports Complex includes the swimming pool, indoor courts and fitness rooms.'],
  [/lee shau kee/i, 'Lee Shau Kee Building (Block Y) is a faculty building on the eastern podium.'],
  [/tang ping yuan/i, 'Tang Ping Yuan Building houses lecture theatres and departmental offices.'],
  [/student hostel/i, 'The Jockey Club Student Hostel provides residential life on the eastern side of campus.'],
  [/hung hom bay/i, 'PolyU\u2019s Hung Hom Bay campus houses the Faculty of Humanities, a short walk east of the main campus.'],
  [/global student hub/i, 'The Wong Man and Tang Kit Wah Global Student Hub is a student commons beside the podium.'],
  [/house of innovation/i, 'House of Innovation supports entrepreneurship, design projects and the Inno Hub.'],
];

function describe(landmark) {
  // Hand-written blurbs win over the raw data description (which is either the
  // tour-wide blurb or a provenance note for the synthesized footprints).
  for (const [re, text] of BLURBS) if (re.test(landmark.name || '')) return text;
  const desc = landmark.description || '';
  if (desc && !/^polyu students are always fond/i.test(desc.trim())) return desc;
  const cat = (landmark.category || 'campus').toLowerCase();
  return `A ${cat} building in the PolyU Hung Hom campus, modelled from its OpenStreetMap footprint.`;
}

function shortName(name = '') {
  return name
    .replace(/^The Hong Kong Polytechnic University\s*/i, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function setLoadingMsg(msg) {
  const el = $('loadingMsg');
  if (el) el.textContent = msg;
}

function hideLoading() {
  const el = $('loading');
  if (!el) return;
  if (params.has('noloading')) {
    el.remove();
    return;
  }
  el.classList.add('done');
  setTimeout(() => el.remove(), 800);
}

function formatTime(t) {
  const total = Math.round(t * 24 * 60);
  const h = Math.floor(total / 60) % 24;
  const m = total % 60;
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

function updateTimeUI() {
  const elev = Math.sin(Math.PI * state.t);
  $('timeSlider').value = String(state.t);
  $('timeLabel').textContent = formatTime(state.t);
  $('timeIcon').textContent = elev < 0.06 ? '☾' : (state.t < 0.3 || state.t > 0.7 ? '◔' : '☀︎');
}

function applyTime(t) {
  state.t = Math.min(1, Math.max(0, t));
  environment.setTimeOfDay(state.t);
  if (scene.fog) {
    scene.fog.near = 900;
    scene.fog.far = 3600;
  }
  // Use the sun's actual elevation (matches environment.js): negative at night.
  const elev = -Math.cos(Math.PI * 2 * state.t) * 1.22;
  const night = 1 - THREE.MathUtils.smoothstep(elev, -0.25, 0.35);
  if (campus) campus.setNight(night);
  updateTimeUI();
}

// ---------------------------------------------------------------------------
// Labels + interaction
// ---------------------------------------------------------------------------
function makeLabel(landmark) {
  const el = document.createElement('div');
  el.className = 'label';
  const en = document.createElement('span');
  en.textContent = shortName(landmark.name);
  el.appendChild(en);
  if (landmark.nameZh) {
    const zh = document.createElement('small');
    zh.textContent = landmark.nameZh;
    el.appendChild(zh);
  }
  el.addEventListener('click', (e) => {
    e.stopPropagation();
    selectLandmark(landmark);
  });
  const [cx, cz] = landmark.center || [0, 0];
  const obj = new CSS2DObject(el);
  obj.position.set(cx, (landmark.height || 18) + 9, cz);
  scene.add(obj);
  labelObjects.push({ obj, el, landmark });
  return obj;
}

function setLabelsVisible(visible) {
  state.labelsVisible = visible;
  for (const l of labelObjects) {
    if (!visible) l.obj.visible = false;
    else l.obj.visible = labelPriority(l.landmark) === 1;
  }
}

const MAJOR_LABEL = /hotel icon|pao yue-kong|innovation tower|auditorium|li ka shing|block z|block x|industrial centre|shaw sports|student hostel|hung hom bay|global student hub|communal building/i;

const SEARCH_ALIASES = [
  [/jockey club innovation tower/i, ['jcit', 'innovation tower', 'zaha', '創新樓', '创新楼']],
  [/jockey club auditorium/i, ['jca', 'auditorium', '賽馬會綜藝館']],
  [/li ka shing tower/i, ['lks', 'li ka shing', '李嘉誠']],
  [/pao yue-kong library/i, ['library', 'pyl', '包玉剛', '圖書館']],
  [/hotel icon/i, ['hotel', '唯港薈', 'icon']],
  [/block z/i, ['z block', 'z座', 'block z']],
  [/block x/i, ['x block', 'x座', 'block x']],
  [/industrial centre/i, ['ic', 'w座', 'industrial', '工業中心']],
  [/global student hub/i, ['gsh', 'student hub', '環球學生薈']],
  [/communal building/i, ['communal', '文康']],
  [/shaw sports complex/i, ['shaw', 'sports', '邵逸夫']],
];
function aliasMatch(landmark, q) {
  if (!q) return false;
  const text = (landmark.name || '') + ' ' + (landmark.nameZh || '') + ' ' + (landmark.category || '');
  if (text.toLowerCase().includes(q)) return true;
  return SEARCH_ALIASES.some(([re, terms]) => re.test(landmark.name || '') && terms.some((t) => t.includes(q)));
}

function labelPriority(landmark) {
  return MAJOR_LABEL.test(landmark.name || '') ? 1 : 2;
}

const _proj = new THREE.Vector3();
function updateLabelVisibility() {
  if (!state.labelsVisible) {
    for (const l of labelObjects) l.obj.visible = false;
    return;
  }
  const kept = [];
  const halfW = window.innerWidth * 0.5;
  const halfH = window.innerHeight * 0.5;
  const panelEl = $('panel');
  const panelRect = panelEl && panelEl.classList.contains('open') ? panelEl.getBoundingClientRect() : null;
  const intersects = (a, b, pad = 4) => a.left < b.right + pad && a.right > b.left - pad && a.top < b.bottom + pad && a.bottom > b.top - pad;
  const ordered = labelObjects.slice().sort((a, b) => {
    const pa = a.landmark === state.selected || a.landmark === state.hovered ? 0 : labelPriority(a.landmark);
    const pb = b.landmark === state.selected || b.landmark === state.hovered ? 0 : labelPriority(b.landmark);
    return pa - pb;
  });
  for (const l of ordered) {
    const [cx, cz] = l.landmark.center || [0, 0];
    const h = l.landmark.height || 18;
    const dist = camera.position.distanceTo(_proj.set(cx, h * 0.5, cz));
    let show =
      labelPriority(l.landmark) === 1 ||
      dist < 430 ||
      l.landmark === state.selected ||
      l.landmark === state.hovered;
    if (show) {
      _proj.set(cx, h + 9, cz).project(camera);
      if (_proj.z > 1 || Math.abs(_proj.x) > 0.94 || Math.abs(_proj.y) > 1.04) {
        show = false;
      } else {
        const sx = _proj.x * halfW + halfW;
        const sy = -_proj.y * halfH + halfH;
        const br = l.el.getBoundingClientRect();
        const w = br.width > 0 ? br.width : Math.max(130, shortName(l.landmark.name).length * 11 + 24);
        const hgt = br.height > 0 ? br.height : 34;
        const rect = { left: sx - w / 2, right: sx + w / 2, top: sy - hgt, bottom: sy };
        const isPriority = l.landmark === state.selected || l.landmark === state.hovered;
        if (panelRect && !isPriority && intersects(rect, panelRect, 6)) show = false;
        if (show) {
          for (const k of kept) {
            if (intersects(rect, k, 4)) { show = false; break; }
          }
        }
        if (show) kept.push(rect);
      }
    }
    l.obj.visible = show;
  }
}

function clearSelection() {
  if (state.selected) {
    state.selected = null;
    $('panel').classList.remove('open');
    for (const l of labelObjects) l.el.classList.remove('is-active');
  }
}

function obstructionScore(position, target, landmark) {
  const dir = target.clone().sub(position);
  const len = dir.length();
  if (len < 1) return 0;
  dir.normalize();
  raycaster.set(position, dir);
  raycaster.far = len - 1;
  const meshes = [];
  for (const entry of campus.landmarks) {
    if (entry.mesh && entry.data !== landmark) meshes.push(entry.mesh);
  }
  campus.group.traverse((o) => {
    if (o.isMesh && o.userData.context) meshes.push(o);
  });
  const hits = raycaster.intersectObjects(meshes, false);
  let nearest = len;
  for (const hit of hits) {
    if (hit.object.userData.landmark === landmark) continue;
    nearest = Math.min(nearest, hit.distance);
    break;
  }
  raycaster.far = Infinity;
  return nearest;
}

function focusCamera(landmark) {
  const [cx, cz] = landmark.center || [0, 0];
  const h = landmark.height || 18;
  const target = new THREE.Vector3(cx, Math.min(h * 0.45, 40), cz);
  const dist = THREE.MathUtils.clamp(h * 3.4 + 70, 90, 420);
  // Try 8 viewpoints and pick the one with the clearest line of sight.
  const candidates = [];
  for (let i = 0; i < 8; i++) {
    const angle = (i / 8) * Math.PI * 2 + 0.35;
    const dir = new THREE.Vector3(Math.sin(angle), 0.62, Math.cos(angle)).normalize();
    const position = target.clone().addScaledVector(dir, dist);
    position.y = Math.max(position.y, target.y + 35);
    candidates.push({ position, score: obstructionScore(position, target, landmark) });
  }
  candidates.sort((a, b) => b.score - a.score);
  const best = candidates[0] || { position: camera.position.clone() };
  tweenCamera(best.position, target);
}

function tweenCamera(position, target) {
  state.cameraTween = {
    fromPos: camera.position.clone(),
    toPos: position.clone(),
    fromTarget: controls.target.clone(),
    toTarget: target.clone(),
    t: 0,
  };
}

function selectLandmark(landmark) {
  state.selected = landmark;
  $('panelCat').textContent = landmark.category || 'Landmark';
  $('panelName').textContent = shortName(landmark.name);
  $('panelZh').textContent = landmark.nameZh || '';
  $('panelDesc').textContent = describe(landmark);
  $('panelHeight').textContent = `${Math.round(landmark.height || 0)} m`;
  $('panelHeight').title = landmark.heightBasis || 'Model height; not a surveyed dimension.';
  const rawForm = String(landmark.building || landmark.tags?.building || '').toLowerCase();
  const formNames = {
    yes: 'University building', university: 'University building', college: 'Academic building',
    concourse: 'Podium / concourse', hotel: 'Hotel / teaching complex', library: 'Library',
    sports: 'Sports building', commercial: 'Commercial / teaching', roof: 'Roof structure',
  };
  const formLabel = /hotel/i.test(landmark.category || '') || /hotel icon/i.test(landmark.name || '')
    ? 'Hotel / teaching complex'
    : formNames[rawForm] || (landmark.category || 'University building');
  $('panelForm').textContent = formLabel;
  const basisText = /official|SHTM|CTBUH|record/i.test(landmark.heightBasis || '')
    ? 'Model geometry · record-height reference'
    : 'Model estimate · not surveyed';
  const basisEl = $('panelHeightBasis');
  if (basisEl) basisEl.textContent = basisText;
  const panoBtn = $('panelPano');
  if (panoBtn) {
    panoBtn.hidden = !landmark.tourPanoId;
    panoBtn.onclick = () => openPano(landmark);
  }
  const thumb = $('panelThumb');
  if (landmark.thumb) {
    thumb.src = landmark.thumb;
    thumb.style.display = 'block';
  } else {
    thumb.removeAttribute('src');
    thumb.style.display = 'none';
  }
  $('panel').classList.add('open');
  for (const l of labelObjects) l.el.classList.toggle('is-active', l.landmark === landmark);
  focusCamera(landmark);
}

// ---------------------------------------------------------------------------
// Minimap
// ---------------------------------------------------------------------------
const map = {
  visible: true,
  canvas: null,
  ctx: null,
  base: null,
  dpr: 1,
  cssW: 180,
  cssH: 262,
  bounds: null,
  scale: 1,
  ox: 0,
  oy: 0,
  data: null,
};

const MAP_COLORS = {
  bg: '#efeae1',
  grass: 'rgba(186, 203, 167, 0.85)',
  wood: 'rgba(170, 189, 152, 0.85)',
  water: 'rgba(160, 195, 205, 0.9)',
  pavement: 'rgba(208, 201, 189, 0.75)',
  other: 'rgba(213, 206, 194, 0.7)',
  context: 'rgba(214, 206, 192, 0.85)',
  landmark: '#a34233',
  landmarkEdge: 'rgba(38, 34, 31, 0.4)',
  road: 'rgba(195, 188, 174, 0.9)',
};

function pointInPolygon(x, z, poly) {
  if (!poly || poly.length < 3) return false;
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, zi] = poly[i];
    const [xj, zj] = poly[j];
    if ((zi > z) !== (zj > z) && x < ((xj - xi) * (z - zi)) / (zj - zi) + xi) {
      inside = !inside;
    }
  }
  return inside;
}

function mapToWorld(px, py) {
  return {
    x: map.bounds.minX + (px - map.ox) / map.scale,
    z: map.bounds.minZ + (py - map.oy) / map.scale,
  };
}

function worldToMap(x, z) {
  return {
    x: map.ox + (x - map.bounds.minX) * map.scale,
    y: map.oy + (z - map.bounds.minZ) * map.scale,
  };
}

function initMinimap(data) {
  map.data = data;
  map.canvas = $('minimapCanvas');
  if (!map.canvas) return;
  map.ctx = map.canvas.getContext('2d');
  map.dpr = Math.min(window.devicePixelRatio || 1, 2);
  map.canvas.width = Math.round(map.cssW * map.dpr);
  map.canvas.height = Math.round(map.cssH * map.dpr);

  // bounds cover the main campus cluster (outliers stay off the map)
  let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
  for (const l of data.landmarks || []) {
    const [cx, cz] = l.center || [0, 0];
    if (Math.abs(cx) > 340 || Math.abs(cz) > 330) continue;
    for (const [x, z] of l.footprint || []) {
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (z < minZ) minZ = z;
      if (z > maxZ) maxZ = z;
    }
  }
  if (!Number.isFinite(minX)) { minX = -200; maxX = 200; minZ = -300; maxZ = 220; }
  const pad = 34;
  minX -= pad; maxX += pad; minZ -= pad; maxZ += pad;
  map.bounds = { minX, maxX, minZ, maxZ };
  const worldW = maxX - minX;
  const worldH = maxZ - minZ;
  const inner = 12;
  map.scale = Math.min((map.cssW - inner * 2) / worldW, (map.cssH - inner * 2) / worldH);
  map.ox = (map.cssW - worldW * map.scale) / 2;
  map.oy = (map.cssH - worldH * map.scale) / 2;

  map.base = document.createElement('canvas');
  map.base.width = map.canvas.width;
  map.base.height = map.canvas.height;
  drawMinimapBase();

  // click-to-fly, drag-to-pan
  let drag = null;
  const canvas = map.canvas;
  const worldFromEvent = (e) => {
    const rect = canvas.getBoundingClientRect();
    return mapToWorld(e.clientX - rect.left, e.clientY - rect.top);
  };
  const pan = (dx, dy) => {
    const wx = -dx / map.scale;
    const wz = -dy / map.scale;
    controls.target.x += wx;
    controls.target.z += wz;
    camera.position.x += wx;
    camera.position.z += wz;
    controls.update();
  };
  canvas.addEventListener('pointerdown', (e) => {
    e.preventDefault();
    drag = { x: e.clientX, y: e.clientY, moved: false };
    canvas.setPointerCapture(e.pointerId);
    canvas.classList.add('dragging');
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!drag) return;
    const dx = e.clientX - drag.x;
    const dy = e.clientY - drag.y;
    if (Math.abs(dx) + Math.abs(dy) > 2) drag.moved = true;
    if (drag.moved) pan(dx, dy);
    drag.x = e.clientX;
    drag.y = e.clientY;
  });
  const endDrag = (e) => {
    if (!drag) return;
    const wasClick = !drag.moved;
    drag = null;
    canvas.classList.remove('dragging');
    if (wasClick) {
      const { x, z } = worldFromEvent(e);
      const hit = (map.data.landmarks || []).find((l) => pointInPolygon(x, z, l.footprint));
      if (hit) {
        selectLandmark(hit);
      } else {
        const target = new THREE.Vector3(x, 10, z);
        const offset = camera.position.clone().sub(controls.target);
        tweenCamera(target.clone().add(offset), target);
      }
    }
  };
  canvas.addEventListener('pointerup', endDrag);
  canvas.addEventListener('pointercancel', () => {
    drag = null;
    canvas.classList.remove('dragging');
  });

  $('btnMap').addEventListener('click', () => {
    map.visible = !map.visible;
    $('minimap').classList.toggle('hidden', !map.visible);
    $('btnMap').classList.toggle('on', map.visible);
    $('btnMap').setAttribute('aria-pressed', String(map.visible));
    if (map.visible) drawMinimap();
  });

  drawMinimap();
}

function drawMinimapBase() {
  const ctx = map.base.getContext('2d');
  const dpr = map.dpr;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.fillStyle = MAP_COLORS.bg;
  ctx.fillRect(0, 0, map.cssW, map.cssH);

  const inside = (x, z) =>
    x > map.bounds.minX - 120 && x < map.bounds.maxX + 120 &&
    z > map.bounds.minZ - 120 && z < map.bounds.maxZ + 120;

  // land-use areas
  for (const area of map.data.areas || []) {
    const poly = area.polygon || [];
    if (poly.length < 3) continue;
    if (!poly.some(([x, z]) => inside(x, z))) continue;
    ctx.beginPath();
    const p0 = worldToMap(poly[0][0], poly[0][1]);
    ctx.moveTo(p0.x, p0.y);
    for (let i = 1; i < poly.length; i++) {
      const p = worldToMap(poly[i][0], poly[i][1]);
      ctx.lineTo(p.x, p.y);
    }
    ctx.closePath();
    ctx.fillStyle = MAP_COLORS[area.kind] || MAP_COLORS.other;
    ctx.fill();
  }

  // context massing
  ctx.fillStyle = MAP_COLORS.context;
  for (const b of map.data.context || []) {
    const poly = b.footprint || [];
    if (poly.length < 3) continue;
    const c = poly[0];
    if (!inside(c[0], c[1])) continue;
    ctx.beginPath();
    const p0 = worldToMap(poly[0][0], poly[0][1]);
    ctx.moveTo(p0.x, p0.y);
    for (let i = 1; i < poly.length; i++) {
      const p = worldToMap(poly[i][0], poly[i][1]);
      ctx.lineTo(p.x, p.y);
    }
    ctx.closePath();
    ctx.fill();
  }

  // roads
  ctx.lineJoin = 'round';
  ctx.lineCap = 'round';
  for (const road of map.data.roads || []) {
    const pts = road.points || [];
    if (pts.length < 2) continue;
    if (!pts.some(([x, z]) => inside(x, z))) continue;
    ctx.beginPath();
    const p0 = worldToMap(pts[0][0], pts[0][1]);
    ctx.moveTo(p0.x, p0.y);
    for (let i = 1; i < pts.length; i++) {
      const p = worldToMap(pts[i][0], pts[i][1]);
      ctx.lineTo(p.x, p.y);
    }
    const w = /primary|trunk|motorway/.test(road.class)
      ? 1.7
      : /secondary|tertiary|residential/.test(road.class)
        ? 1.1
        : 0.65;
    ctx.strokeStyle = MAP_COLORS.road;
    ctx.lineWidth = w;
    ctx.stroke();
  }

  // landmark footprints
  ctx.strokeStyle = MAP_COLORS.landmarkEdge;
  ctx.lineWidth = 0.5;
  for (const l of map.data.landmarks || []) {
    const poly = l.footprint || [];
    if (poly.length < 3) continue;
    const [cx, cz] = l.center || [0, 0];
    if (cx < map.bounds.minX - 40 || cx > map.bounds.maxX + 40 || cz < map.bounds.minZ - 40 || cz > map.bounds.maxZ + 40) continue;
    ctx.beginPath();
    const p0 = worldToMap(poly[0][0], poly[0][1]);
    ctx.moveTo(p0.x, p0.y);
    for (let i = 1; i < poly.length; i++) {
      const p = worldToMap(poly[i][0], poly[i][1]);
      ctx.lineTo(p.x, p.y);
    }
    ctx.closePath();
    ctx.fillStyle = MAP_COLORS.landmark;
    ctx.fill();
    ctx.stroke();
  }

  // north arrow
  ctx.fillStyle = 'rgba(38,34,31,.7)';
  ctx.font = '600 8px -apple-system,Helvetica,Arial,sans-serif';
  ctx.textAlign = 'left';
  ctx.fillText('N', 8, 15);
  ctx.beginPath();
  ctx.moveTo(17, 7);
  ctx.lineTo(20, 13);
  ctx.lineTo(14, 13);
  ctx.closePath();
  ctx.fill();

  // scale bar (nice round distance)
  const meters = 100;
  const barPx = meters * map.scale;
  if (barPx > 18) {
    ctx.strokeStyle = 'rgba(38,34,31,.45)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(8, map.cssH - 12);
    ctx.lineTo(8 + barPx, map.cssH - 12);
    ctx.stroke();
    ctx.fillStyle = 'rgba(38,34,31,.55)';
    ctx.font = '500 7px -apple-system,Helvetica,Arial,sans-serif';
    ctx.fillText('100 m', 8, map.cssH - 16);
  }
}

function drawMinimap() {
  if (!map.visible || !map.ctx || !map.base) return;
  const ctx = map.ctx;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.drawImage(map.base, 0, 0);
  ctx.setTransform(map.dpr, 0, 0, map.dpr, 0, 0);

  // selected landmark ring
  if (state.selected) {
    const [cx, cz] = state.selected.center || [0, 0];
    const p = worldToMap(cx, cz);
    ctx.beginPath();
    ctx.arc(p.x, p.y, 5.5, 0, Math.PI * 2);
    ctx.strokeStyle = '#26221f';
    ctx.lineWidth = 1.2;
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(p.x, p.y, 5.5, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(255,255,255,.8)';
    ctx.lineWidth = 0.5;
    ctx.stroke();
  }

  // camera position + view wedge
  const cam = camera.position;
  const tgt = controls.target;
  let dx = tgt.x - cam.x;
  let dz = tgt.z - cam.z;
  const len = Math.hypot(dx, dz) || 1;
  dx /= len;
  dz /= len;
  let p = worldToMap(cam.x, cam.z);
  const m = 6;
  p.x = Math.min(map.cssW - m, Math.max(m, p.x));
  p.y = Math.min(map.cssH - m, Math.max(m, p.y));
  const angle = Math.atan2(dz, dx);
  const spread = 0.36;
  const reach = 26;
  ctx.beginPath();
  ctx.moveTo(p.x, p.y);
  ctx.lineTo(p.x + Math.cos(angle - spread) * reach, p.y + Math.sin(angle - spread) * reach);
  ctx.lineTo(p.x + Math.cos(angle + spread) * reach, p.y + Math.sin(angle + spread) * reach);
  ctx.closePath();
  ctx.fillStyle = 'rgba(173,32,53,.16)';
  ctx.fill();
  ctx.strokeStyle = 'rgba(173,32,53,.55)';
  ctx.lineWidth = 0.8;
  ctx.stroke();

  ctx.beginPath();
  ctx.arc(p.x, p.y, 2.6, 0, Math.PI * 2);
  ctx.fillStyle = '#ad2035';
  ctx.fill();
  ctx.strokeStyle = '#fff';
  ctx.lineWidth = 0.8;
  ctx.stroke();
}

// ---------------------------------------------------------------------------
// Finder: search + category filter
// ---------------------------------------------------------------------------
const CATEGORY_ORDER = ['Landmark', 'Library', 'Sports', 'Hotel', 'Campus building'];

function initFinder(data) {
  const places = data.landmarks || [];
  const categories = [...new Set(places.map((l) => l.category).filter(Boolean))].sort(
    (a, b) => {
      const ia = CATEGORY_ORDER.indexOf(a);
      const ib = CATEGORY_ORDER.indexOf(b);
      return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
    }
  );
  state.finder = { query: '', category: 'All', places, categories };

  $('finderCount').textContent = `${places.length} places`;
  const chipHost = $('catChips');
  const chips = ['All', ...categories];
  chipHost.innerHTML = '';
  for (const name of chips) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'chip' + (name === 'All' ? ' on' : '');
    b.textContent = name;
    b.dataset.cat = name;
    b.addEventListener('click', () => {
      state.finder.category = name;
      for (const c of chipHost.children) c.classList.toggle('on', c.dataset.cat === name);
      renderFinder();
    });
    chipHost.appendChild(b);
  }

  $('searchInput').addEventListener('input', (e) => {
    state.finder.query = e.target.value.trim();
    renderFinder();
  });
  $('searchInput').addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      e.target.value = '';
      state.finder.query = '';
      renderFinder();
      e.target.blur();
    }
  });

  // Deep link: ?q=library or ?cat=Sports opens the finder pre-filtered.
  const q0 = params.get('q');
  const cat0 = params.get('cat');
  if (q0) {
    state.finder.query = q0;
    $('searchInput').value = q0;
  }
  if (cat0 && categories.includes(cat0)) {
    state.finder.category = cat0;
    for (const c of chipHost.children) c.classList.toggle('on', c.dataset.cat === cat0);
  }
  if (q0 || cat0) renderFinder();
}

function renderFinder() {
  const f = state.finder;
  if (!f) return;
  const results = $('results');
  const q = f.query.toLowerCase();
  const matches = f.places.filter((l) => {
    const inCat = f.category === 'All' || l.category === f.category;
    if (!inCat) return false;
    if (!q) return true;
    return aliasMatch(l, q);
  });

  const show = f.query.length > 0 || f.category !== 'All';
  results.hidden = !show;
  if (!show) return;

  results.innerHTML = '';
  if (!matches.length) {
    const empty = document.createElement('div');
    empty.className = 'results-empty';
    empty.textContent = 'No matching place — try “library”, “JCIT”, “hotel”, or “Z座”.';
    results.appendChild(empty);
    return;
  }
  for (const landmark of matches.slice(0, 16)) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'result';
    const label = document.createElement('span');
    label.textContent = shortName(landmark.name);
    if (landmark.nameZh) {
      const zh = document.createElement('em');
      zh.textContent = landmark.nameZh;
      label.appendChild(zh);
    }
    const cat = document.createElement('small');
    cat.textContent = landmark.category || '';
    b.append(label, cat);
    b.addEventListener('click', () => {
      selectLandmark(landmark);
      $('results').hidden = true;
      $('searchInput').blur();
    });
    results.appendChild(b);
  }
}

// ---------------------------------------------------------------------------
// 360° panorama viewer (official tour stills)
// ---------------------------------------------------------------------------
const panoViewer = {
  open: false,
  renderer: null,
  scene: null,
  camera: null,
  texture: null,
  yaw: 0,
  pitch: 0,
  fov: 72,
  raf: 0,
  drag: null,
};

function disposePano() {
  if (panoViewer.raf) cancelAnimationFrame(panoViewer.raf);
  panoViewer.raf = 0;
  if (panoViewer.texture) {
    panoViewer.texture.dispose();
    panoViewer.texture = null;
  }
  if (panoViewer.renderer) {
    panoViewer.renderer.dispose();
    if (panoViewer.renderer.domElement.parentNode) {
      panoViewer.renderer.domElement.parentNode.removeChild(panoViewer.renderer.domElement);
    }
    panoViewer.renderer = null;
  }
  panoViewer.scene = null;
  panoViewer.camera = null;
  panoViewer.drag = null;
}

function closePano() {
  if (!panoViewer.open) return;
  panoViewer.open = false;
  state.panoOpen = false;
  $('panoModal').classList.remove('open');
  $('panoModal').setAttribute('aria-hidden', 'true');
  $('panoModal').inert = true;
  document.body.classList.remove('pano-open');
  disposePano();
}

function applyPanoOrientation() {
  if (!panoViewer.camera) return;
  panoViewer.camera.rotation.set(panoViewer.pitch, panoViewer.yaw, 0, 'YXZ');
}

function buildEquirect(images) {
  // 2048x1024 is the natural resolution for six 512px faces.
  const W = 2048;
  const H = 1024;
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  const ctx = canvas.getContext('2d');
  const out = ctx.createImageData(W, H);
  const data = out.data;

  // read each face once into a flat RGBA buffer
  const src = {};
  const size = 512;
  for (const key of ['r', 'l', 'u', 'd', 'b', 'f']) {
    const img = images[key];
    const c = document.createElement('canvas');
    c.width = size;
    c.height = size;
    const cc = c.getContext('2d');
    cc.drawImage(img, 0, 0, size, size);
    src[key] = cc.getImageData(0, 0, size, size).data;
  }

  const PI = Math.PI;
  const TWO_PI = PI * 2;
  let o = 0;
  for (let y = 0; y < H; y++) {
    const lat = (0.5 - (y + 0.5) / H) * PI;
    const cosLat = Math.cos(lat);
    const sinLat = Math.sin(lat);
    for (let x = 0; x < W; x++) {
      const lon = ((x + 0.5) / W - 0.5) * TWO_PI;
      const dx = cosLat * Math.cos(lon);
      const dy = sinLat;
      const dz = cosLat * Math.sin(lon);
      const ax = Math.abs(dx);
      const ay = Math.abs(dy);
      const az = Math.abs(dz);
      let face, u, v;
      if (az >= ax && az >= ay) {
        if (dz < 0) { face = 'f'; u = dx / -dz; v = dy / -dz; }
        else { face = 'b'; u = -dx / dz; v = dy / dz; }
      } else if (ax >= ay) {
        if (dx > 0) { face = 'r'; u = dz / dx; v = dy / dx; }
        else { face = 'l'; u = dz / dx; v = -dy / dx; }
      } else if (dy > 0) {
        face = 'u'; u = dx / dy; v = dz / dy;
      } else {
        face = 'd'; u = dx / -dy; v = dz / dy;
      }
      const sx = Math.min(size - 1, Math.max(0, Math.round((u + 1) * 0.5 * (size - 1))));
      const sy = Math.min(size - 1, Math.max(0, Math.round((1 - v) * 0.5 * (size - 1))));
      const si = (sy * size + sx) * 4;
      const pixels = src[face];
      data[o] = pixels[si];
      data[o + 1] = pixels[si + 1];
      data[o + 2] = pixels[si + 2];
      data[o + 3] = 255;
      o += 4;
    }
  }
  ctx.putImageData(out, 0, 0);
  return canvas;
}

function openPano(landmark) {
  if (!landmark || !landmark.tourPanoId) return;
  const stage = $('panoStage');
  const loading = $('panoLoading');
  const error = $('panoError');
  closePano();
  disposePano();

  panoViewer.open = true;
  state.panoOpen = true;
  $('panoName').textContent = shortName(landmark.name);
  $('panoModal').classList.add('open');
  $('panoModal').setAttribute('aria-hidden', 'false');
  $('panoModal').inert = false;
  document.body.classList.add('pano-open');
  loading.hidden = false;
  error.hidden = true;

  const w = stage.clientWidth || 900;
  const h = stage.clientHeight || 520;
  const renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setSize(w, h);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  stage.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(panoViewer.fov, w / h, 0.1, 100);
  camera.rotation.order = 'YXZ';
  panoViewer.renderer = renderer;
  panoViewer.scene = scene;
  panoViewer.camera = camera;
  panoViewer.yaw = 0;
  panoViewer.pitch = 0;
  panoViewer.fov = 72;
  applyPanoOrientation();

  const base = `./assets/pano/${landmark.tourPanoId}/`;
  // Load the six photo-cube faces and stitch them into one equirectangular
  // texture. The tour ships normal photo-oriented faces, so a small amount of
  // re-projection is needed; this gives clean seams and simple camera dragging.
  const faceDefs = [
    { key: 'r', file: 'r.jpg' },
    { key: 'l', file: 'l.jpg' },
    { key: 'u', file: 'u.jpg' },
    { key: 'd', file: 'd.jpg' },
    { key: 'b', file: 'b.jpg' },
    { key: 'f', file: 'f.jpg' },
  ];
  const images = {};
  let remaining = 6;
  let failed = false;
  const fail = () => {
    if (failed) return;
    failed = true;
    loading.hidden = true;
    error.hidden = false;
  };
  const finish = () => {
    const canvas = buildEquirect(images);
    const texture = new THREE.CanvasTexture(canvas);
    texture.mapping = THREE.EquirectangularReflectionMapping;
    texture.colorSpace = THREE.SRGBColorSpace;
    texture.needsUpdate = true;
    scene.background = texture;
    panoViewer.texture = texture;
    loading.hidden = true;
  };
  faceDefs.forEach((def) => {
    const img = new Image();
    img.onload = () => {
      images[def.key] = img;
      remaining -= 1;
      if (remaining === 0) finish();
    };
    img.onerror = fail;
    img.src = base + def.file;
  });
  // drag to look around
  const canvas = renderer.domElement;
  canvas.addEventListener('pointerdown', (e) => {
    panoViewer.drag = { x: e.clientX, y: e.clientY };
    canvas.setPointerCapture(e.pointerId);
  });
  canvas.addEventListener('pointermove', (e) => {
    if (!panoViewer.drag) return;
    const dx = e.clientX - panoViewer.drag.x;
    const dy = e.clientY - panoViewer.drag.y;
    panoViewer.drag = { x: e.clientX, y: e.clientY };
    panoViewer.yaw -= dx * 0.0026;
    panoViewer.pitch = THREE.MathUtils.clamp(panoViewer.pitch - dy * 0.0026, -1.35, 1.35);
    applyPanoOrientation();
  });
  const endDrag = () => { panoViewer.drag = null; };
  canvas.addEventListener('pointerup', endDrag);
  canvas.addEventListener('pointercancel', endDrag);
  canvas.addEventListener('wheel', (e) => {
    e.preventDefault();
    panoViewer.fov = THREE.MathUtils.clamp(panoViewer.fov + e.deltaY * 0.03, 36, 96);
    camera.fov = panoViewer.fov;
    camera.updateProjectionMatrix();
  }, { passive: false });

  (function panoLoop() {
    if (!panoViewer.open) return;
    panoViewer.raf = requestAnimationFrame(panoLoop);
    renderer.render(scene, camera);
  })();
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------
async function loadData() {
  const res = await fetch('./data/campus.json', { cache: 'no-cache' });
  if (!res.ok) throw new Error(`campus.json: HTTP ${res.status}`);
  const data = await res.json();
  const entranceRes = await fetch('./data/hotel-entrances.json', { cache: 'no-cache' });
  if (!entranceRes.ok) throw new Error(`hotel-entrances.json: HTTP ${entranceRes.status}`);
  data.hotelEntranceRegistration = await entranceRes.json();
  const layoutRes = await fetch('./data/scene-layout.json', { cache: 'no-cache' });
  if (!layoutRes.ok) throw new Error(`scene-layout.json: HTTP ${layoutRes.status}`);
  data.sceneLayout = await layoutRes.json();
  return data;
}

function buildScene(data, textures, jcitModel, libraryModel, jcaModel, hotelModel, lksModel, blockzModel, blockxModel, communalModel, shawModel, gshModel, leeshaukeeModel, industrialModel, shirleyModel, choiModel, chowModel, mongModel, ngModel, yipModel, chanModel, taioModel, luiModel, ghModel, cmaModel, anitaModel, hoiModel, chungModel, sealModel, stanleyModel, fongModel, tangModel, autoModels) {
  state.data = data;
  campus = createCampus(THREE, data, { textures, jcitModel, libraryModel, jcaModel, hotelModel, lksModel, blockzModel, blockxModel, communalModel, shawModel, gshModel, leeshaukeeModel, industrialModel, shirleyModel, choiModel, chowModel, mongModel, ngModel, yipModel, chanModel, taioModel, luiModel, ghModel, cmaModel, anitaModel, hoiModel, chungModel, sealModel, stanleyModel, fongModel, tangModel, autoModels });
  scene.add(campus.group);

  for (const l of data.landmarks || []) makeLabel(l);
  setLabelsVisible(state.labelsVisible);

  initFinder(data);
  initMinimap(data);

  const selectName = params.get('select');
  if (selectName) {
    const hit = (data.landmarks || []).find((l) =>
      (l.name || '').toLowerCase().includes(selectName.toLowerCase())
    );
    if (hit) {
      setTimeout(() => {
        selectLandmark(hit);
        if (params.has('pano')) openPano(hit);
      }, 60);
    }
  }

  // frame the main campus cluster (outlying Hotel ICON / Hung Hom Bay stay outside)
  const box = new THREE.Box3();
  for (const l of data.landmarks || []) {
    if (!l.footprint) continue;
    const [cx, cz] = l.center || [0, 0];
    if (Math.abs(cx) > 340 || Math.abs(cz) > 330) continue;
    for (const [x, z] of l.footprint) {
      box.expandByPoint(new THREE.Vector3(x, 0, z));
      box.expandByPoint(new THREE.Vector3(x, l.height || 18, z));
    }
  }
  if (box.isEmpty()) box.setFromCenterAndSize(new THREE.Vector3(), new THREE.Vector3(400, 60, 400));
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const span = Math.max(size.x, size.z);
  const dist = span * 1.22;
  camera.position.set(center.x - dist * 0.08, dist * 0.5, center.z - dist * 0.98);
  controls.target.set(center.x, Math.min(center.y + 6, 40), center.z);
  controls.update();

  state.defaultView = {
    position: camera.position.clone(),
    target: controls.target.clone(),
  };

  // Deep link for a specific viewpoint: ?cam=x,y,z&target=x,y,z
  const camParam = (params.get('cam') || '').split(',').map(Number);
  const tgtParam = (params.get('target') || '').split(',').map(Number);
  if (camParam.length === 3 && camParam.every(Number.isFinite)) camera.position.set(...camParam);
  if (tgtParam.length === 3 && tgtParam.every(Number.isFinite)) controls.target.set(...tgtParam);
  if (camParam.length === 3 || tgtParam.length === 3) controls.update();
}

// ---------------------------------------------------------------------------
// Pointer
// ---------------------------------------------------------------------------
function updatePointer(e) {
  pointer.set(
    (e.clientX / window.innerWidth) * 2 - 1,
    -(e.clientY / window.innerHeight) * 2 + 1
  );
}

function pick() {
  if (!campus) return null;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObjects(campus.landmarks.map((l) => l.mesh), false);
  return hits.length ? hits[0].object.userData.landmark : null;
}

renderer.domElement.addEventListener('pointermove', (e) => {
  updatePointer(e);
  const hit = pick();
  if (hit !== state.hovered) {
    state.hovered = hit;
    renderer.domElement.style.cursor = hit ? 'pointer' : 'grab';
  }
});

renderer.domElement.addEventListener('pointerleave', () => {
  state.hovered = null;
});

renderer.domElement.addEventListener('click', (e) => {
  updatePointer(e);
  const hit = pick();
  if (hit) selectLandmark(hit);
  else clearSelection();
});

// ---------------------------------------------------------------------------
// UI wiring
// ---------------------------------------------------------------------------
$('timeSlider').addEventListener('input', (e) => applyTime(parseFloat(e.target.value)));

$('btnLabels').addEventListener('click', () => {
  state.labelsVisible = !state.labelsVisible;
  $('btnLabels').classList.toggle('on', state.labelsVisible);
  setLabelsVisible(state.labelsVisible);
});

$('btnOrbit').addEventListener('click', () => {
  state.autoOrbit = !state.autoOrbit;
  controls.autoRotate = state.autoOrbit;
  $('btnOrbit').classList.toggle('on', state.autoOrbit);
});

$('btnReset').addEventListener('click', () => {
  if (!state.defaultView) return;
  clearSelection();
  tweenCamera(state.defaultView.position.clone(), state.defaultView.target.clone());
});

$('panelClose').addEventListener('click', (e) => {
  e.stopPropagation();
  clearSelection();
});

$('panoClose').addEventListener('click', (e) => {
  e.stopPropagation();
  closePano();
});
$('panoModal').addEventListener('click', (e) => {
  if (e.target === $('panoModal')) closePano();
});
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && panoViewer.open) closePano();
});

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
  labelRenderer.setSize(window.innerWidth, window.innerHeight);
  if (panoViewer.open && panoViewer.renderer) {
    const stage = $('panoStage');
    panoViewer.renderer.setSize(stage.clientWidth || 900, stage.clientHeight || 520);
    panoViewer.camera.aspect = (stage.clientWidth || 900) / (stage.clientHeight || 520);
    panoViewer.camera.updateProjectionMatrix();
  }
});

// ---------------------------------------------------------------------------
// Render loop
// ---------------------------------------------------------------------------
function animate() {
  const dt = Math.min(clock.getDelta(), 0.05);
  const elapsed = clock.elapsedTime;

  if (state.cameraTween) {
    const tw = state.cameraTween;
    tw.t = Math.min(1, tw.t + dt * 1.7);
    const e = 1 - Math.pow(1 - tw.t, 3);
    camera.position.lerpVectors(tw.fromPos, tw.toPos, e);
    controls.target.lerpVectors(tw.fromTarget, tw.toTarget, e);
    if (tw.t >= 1) state.cameraTween = null;
  }

  if (state.panoOpen) {
    requestAnimationFrame(animate);
    return;
  }
  if (environment.sky.visible) environment.sky.position.copy(camera.position);
  environment.update(dt, elapsed);
  updateLabelVisibility();
  controls.update();
  drawMinimap();
  renderer.render(scene, camera);
  labelRenderer.render(scene, camera);
  requestAnimationFrame(animate);
}

async function loadAutoModels() {
  try {
    const res = await fetch('./data/custom-models.json?v=20261019-alignment4');
    const list = await res.json();
    const loader = new GLTFLoader();
    const entries = await Promise.all(list.map((e) => new Promise((resolve) => {
      loader.load(
        './' + e.file + '?v=20261019-alignment4',
        (gltf) => resolve([e.name, gltf.scene]),
        undefined,
        () => resolve([e.name, null])
      );
    })));
    return Object.fromEntries(entries.filter(([, scene]) => scene));
  } catch (err) {
    console.warn('Auto model registry not available.', err);
    return {};
  }
}

function loadTangModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/tang.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Tang Ping Yuan GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadFongModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/fong.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Fong Shu Chuen GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadStanleyModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/stanley.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Stanley Ho GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadSealModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/seal.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Seal of Love GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadChungModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/chung.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Chung Sze Yuen GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadHoiModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/hoi.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('House of Innovation GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadAnitaModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/anita.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Anita Chan Lai Ling GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadCmaModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/cma.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('CMA GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadGhModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/gh.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('GH Block GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadLuiModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/lui.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Lui Che Woo GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadTaioModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/taio.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Chan Tai Ho GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadChanModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/chan.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Chan Sui Wai GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadYipModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/yip.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Yip Kit Chuen GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadNgModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/ng.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Ng Wing Hong GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadMongModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/mong.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Mong Man Wai GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadChowModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/chow.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Chow Yei Ching GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadChoiModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/choi.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Choi Kai Yau GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadShirleyModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/shirley.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Shirley Chan GLB not available, using template fallback.', err);
        resolve(null);
      }
    );
  });
}

function loadIndustrialModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/industrial.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Industrial Centre GLB not available, using procedural massing.', err);
        resolve(null);
      }
    );
  });
}

function loadLeeShauKeeModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/leeshaukee.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Lee Shau Kee GLB not available, using procedural massing.', err);
        resolve(null);
      }
    );
  });
}

function loadGSHModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/gsh.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Global Student Hub GLB not available, using procedural massing.', err);
        resolve(null);
      }
    );
  });
}

function loadShawModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/shaw.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Shaw GLB not available, using procedural massing.', err);
        resolve(null);
      }
    );
  });
}

function loadCommunalModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/communal.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Communal GLB not available, using procedural massing.', err);
        resolve(null);
      }
    );
  });
}

function loadBlockXModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/blockx.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Block X GLB not available, using procedural massing.', err);
        resolve(null);
      }
    );
  });
}

function loadBlockZModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/blockz.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Block Z GLB not available, using procedural massing.', err);
        resolve(null);
      }
    );
  });
}

function loadLKSModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/lks.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('LKS GLB not available, using procedural massing.', err);
        resolve(null);
      }
    );
  });
}

function loadHotelModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/hotel_icon.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Hotel ICON GLB not available, using procedural massing.', err);
        resolve(null);
      }
    );
  });
}

function loadJCAModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/jca.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('JCA GLB not available, using procedural massing.', err);
        resolve(null);
      }
    );
  });
}

function loadLibraryModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/library.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('Library GLB not available, using procedural massing.', err);
        resolve(null);
      }
    );
  });
}

function loadJCITModel() {
  return new Promise((resolve) => {
    new GLTFLoader().load(
      './assets/models/jcit.glb?v=20261019-alignment4',
      (gltf) => resolve(gltf.scene),
      undefined,
      (err) => {
        console.warn('JCIT GLB not available, using procedural fallback.', err);
        resolve(null);
      }
    );
  });
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
(async function boot() {
  try {
    setLoadingMsg('Loading landmark data');
    const data = await loadData();
    // OSM "Core A..U" ways are small lift cores inside the podium; not landmark masses.
    data.landmarks = (data.landmarks || []).filter((l) => !/^core [a-u]$/i.test(shortName(l.name)));
    setLoadingMsg(`Building ${data.landmarks?.length ?? 0} landmarks`);
    const textures = await loadCampusTextures(THREE);
    const [jcitModel, libraryModel, jcaModel, hotelModel, lksModel, blockzModel, blockxModel, communalModel, shawModel, gshModel, leeshaukeeModel, industrialModel, shirleyModel, choiModel, chowModel, mongModel, ngModel, yipModel, chanModel, taioModel, luiModel, ghModel, cmaModel, anitaModel, hoiModel, chungModel, sealModel, stanleyModel, fongModel, tangModel, autoModels] = await Promise.all([loadJCITModel(), loadLibraryModel(), loadJCAModel(), loadHotelModel(), loadLKSModel(), loadBlockZModel(), loadBlockXModel(), loadCommunalModel(), loadShawModel(), loadGSHModel(), loadLeeShauKeeModel(), loadIndustrialModel(), loadShirleyModel(), loadChoiModel(), loadChowModel(), loadMongModel(), loadNgModel(), loadYipModel(), loadChanModel(), loadTaioModel(), loadLuiModel(), loadGhModel(), loadCmaModel(), loadAnitaModel(), loadHoiModel(), loadChungModel(), loadSealModel(), loadStanleyModel(), loadFongModel(), loadTangModel(), loadAutoModels()]);
    buildScene(data, textures, jcitModel, libraryModel, jcaModel, hotelModel, lksModel, blockzModel, blockxModel, communalModel, shawModel, gshModel, leeshaukeeModel, industrialModel, shirleyModel, choiModel, chowModel, mongModel, ngModel, yipModel, chanModel, taioModel, luiModel, ghModel, cmaModel, anitaModel, hoiModel, chungModel, sealModel, stanleyModel, fongModel, tangModel, autoModels);
    applyTime(state.t);
    updateTimeUI();
    if (params.has('embed')) {
      document.body.classList.add('embed');
      renderer.setPixelRatio(1);
      controls.enableRotate = false;
      controls.enableZoom = false;
      controls.enablePan = false;
      controls.enableDamping = false;
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.32;
      // lower, more cinematic backdrop angle: skyline against the sky
      camera.position.y = controls.target.y + Math.max(110, camera.position.y * 0.42);
      controls.update();
      if (campus) campus.setNight(1 - THREE.MathUtils.smoothstep(Math.sin(Math.PI * state.t), 0.02, 0.26));
    }
    hideLoading();
    animate();
  } catch (err) {
    console.error(err);
    setLoadingMsg('Could not load data/campus.json — run a local server (see README)');
  }
})();
