import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import { STLExporter } from "three/addons/exporters/STLExporter.js";
import { mergeVertices } from "three/addons/utils/BufferGeometryUtils.js";

// ── DOM ──────────────────────────────────────────────────────────────────────
const viewport = document.getElementById("viewport");
const fileSelect = document.getElementById("file-select");
const reloadBtn = document.getElementById("reload-btn");
const autoReloadChk = document.getElementById("auto-reload");
const statusEl = document.getElementById("status");
const selectionInfo = document.getElementById("selection-info");
const extrudeDistance = document.getElementById("extrude-distance");
const extrudeDirection = document.getElementById("extrude-direction");
const extrudeBtn = document.getElementById("extrude-btn");
const clearExtrudeBtn = document.getElementById("clear-extrude-btn");
const saveBtn = document.getElementById("save-btn");
const downloadBtn = document.getElementById("download-btn");
const showEdgesChk = document.getElementById("show-edges");
const fitBtn = document.getElementById("fit-btn");
const clearSelectionBtn = document.getElementById("clear-selection-btn");

// ── Three.js scene ───────────────────────────────────────────────────────────
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x1a1d23);

const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 5000);
camera.position.set(300, 200, 300);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
viewport.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
// Left-drag orbits; short left-click (no drag) selects faces (see pointer handlers below).
controls.mouseButtons = {
  LEFT: THREE.MOUSE.ROTATE,
  MIDDLE: THREE.MOUSE.DOLLY,
  RIGHT: THREE.MOUSE.PAN,
};

scene.add(new THREE.AmbientLight(0xffffff, 0.55));
const key = new THREE.DirectionalLight(0xffffff, 0.85);
key.position.set(200, 300, 150);
scene.add(key);
const fill = new THREE.DirectionalLight(0xaaccff, 0.35);
fill.position.set(-150, -80, -200);
scene.add(fill);

const GRID_SIZE = 500;
const GRID_DIVS = 50;
const AXIS_LEN = 260;

const sceneHelpers = new THREE.Group();
scene.add(sceneHelpers);

const grid = new THREE.GridHelper(GRID_SIZE, GRID_DIVS, 0x4a5568, 0x2d3340);
grid.position.y = 0;
sceneHelpers.add(grid);

function makeAxisLabelSprite(text, color) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  const fontSize = 48;
  ctx.font = `bold ${fontSize}px system-ui, sans-serif`;
  const pad = 8;
  const w = Math.ceil(ctx.measureText(text).width) + pad * 2;
  const h = fontSize + pad * 2;
  canvas.width = w;
  canvas.height = h;
  ctx.font = `bold ${fontSize}px system-ui, sans-serif`;
  ctx.fillStyle = color;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, w / 2, h / 2);
  const texture = new THREE.CanvasTexture(canvas);
  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthTest: false,
    depthWrite: false,
  });
  const sprite = new THREE.Sprite(material);
  const height = 14;
  sprite.scale.set(height * (w / h), height, 1);
  return sprite;
}

const axesGroup = new THREE.Group();
const axisDefs = [
  { dir: new THREE.Vector3(1, 0, 0), label: "+X", color: "#f28b82" },
  { dir: new THREE.Vector3(0, 1, 0), label: "+Y", color: "#81c995" },
  { dir: new THREE.Vector3(0, 0, 1), label: "+Z", color: "#8ab4f8" },
];
for (const { dir, label, color } of axisDefs) {
  const end = dir.clone().multiplyScalar(AXIS_LEN);
  const lineGeom = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(), end]);
  axesGroup.add(
    new THREE.Line(
      lineGeom,
      new THREE.LineBasicMaterial({ color: new THREE.Color(color), linewidth: 2 })
    )
  );
  const tip = makeAxisLabelSprite(label, color);
  tip.position.copy(end);
  axesGroup.add(tip);
}
sceneHelpers.add(axesGroup);

// ── State ────────────────────────────────────────────────────────────────────
let currentFile = "car-2/enclosure_body.stl";
let lastMtime = 0;
let pollTimer = null;

/** @type {THREE.Mesh | null} */
let bodyMesh = null;
/** @type {THREE.LineSegments | null} */
let edgeLines = null;

/** Adjacency: triangle index -> Set of neighbor triangle indices */
let triangleAdjacency = new Map();

/** Faces numbered on first selection only (id -> center/normal/area). */
/** @type {Map<number, { id: number, center: THREE.Vector3, normal: THREE.Vector3, area: number }>} */
let registeredFaces = new Map();
/** Stable key (rounded center + normal) -> face id */
let faceKeyToId = new Map();
/** Triangle index -> face id (only for previously selected patches) */
let triangleToFaceId = new Map();
let nextFaceId = 1;

/** @type {Set<number>} */
let selectedTriangles = new Set();
/** @type {Set<number>} */
let selectedFaceIds = new Set();
/** @type {THREE.Mesh | null} */
let highlightMesh = null;

/** Extrusion meshes stacked on the body */
/** @type {THREE.Mesh[]} */
let extrusionMeshes = [];

/** Root group holding body + extrusions for export */
const modelGroup = new THREE.Group();
scene.add(modelGroup);

/** Labels live in model space so they follow orientation */
const faceLabelsGroup = new THREE.Group();
modelGroup.add(faceLabelsGroup);

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
const loader = new STLLoader();

// ── Resize ───────────────────────────────────────────────────────────────────
function onResize() {
  const w = viewport.clientWidth;
  const h = viewport.clientHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
}
window.addEventListener("resize", onResize);
onResize();

// ── API helpers ──────────────────────────────────────────────────────────────
async function fetchFiles() {
  const res = await fetch("/api/files");
  const data = await res.json();
  return data.files;
}

async function fetchMtime(file) {
  const res = await fetch(`/api/mtime?file=${encodeURIComponent(file)}`);
  if (!res.ok) return null;
  return res.json();
}

function setStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.style.color = isError ? "#f28b82" : "#9aa0a6";
}

// ── Geometry helpers ─────────────────────────────────────────────────────────
/** Weld STL vertices so coplanar faces share edges and can be flood-selected. */
function prepareGeometry(geometry) {
  let geom = geometry;
  if (!geom.index) {
    geom = geom.clone();
    geom.setIndex(
      Array.from({ length: geom.attributes.position.count }, (_, i) => i)
    );
  }
  geom = mergeVertices(geom, 1e-4);
  geom.computeVertexNormals();
  geom.computeBoundingBox();
  return geom;
}

function triangleCount(geometry) {
  if (geometry.index) return geometry.index.count / 3;
  return geometry.attributes.position.count / 3;
}

function triangleVertexIndices(geometry, triIndex) {
  if (geometry.index) {
    const index = geometry.index;
    return [
      index.getX(triIndex * 3),
      index.getX(triIndex * 3 + 1),
      index.getX(triIndex * 3 + 2),
    ];
  }
  const base = triIndex * 3;
  return [base, base + 1, base + 2];
}

function buildAdjacency(geometry) {
  const triCount = triangleCount(geometry);
  const edgeMap = new Map();

  function edgeKey(a, b) {
    return a < b ? `${a}_${b}` : `${b}_${a}`;
  }

  const adj = new Map();
  for (let t = 0; t < triCount; t++) {
    adj.set(t, new Set());
  }

  for (let t = 0; t < triCount; t++) {
    const [a, b, c] = triangleVertexIndices(geometry, t);
    for (const [v0, v1] of [
      [a, b],
      [b, c],
      [c, a],
    ]) {
      const key = edgeKey(v0, v1);
      if (!edgeMap.has(key)) edgeMap.set(key, []);
      edgeMap.get(key).push(t);
    }
  }

  for (const tris of edgeMap.values()) {
    for (let i = 0; i < tris.length; i++) {
      for (let j = i + 1; j < tris.length; j++) {
        adj.get(tris[i]).add(tris[j]);
        adj.get(tris[j]).add(tris[i]);
      }
    }
  }
  return adj;
}

function triangleNormal(geometry, triIndex, target = new THREE.Vector3()) {
  const pos = geometry.attributes.position;
  const [ia, ib, ic] = triangleVertexIndices(geometry, triIndex);
  const va = new THREE.Vector3().fromBufferAttribute(pos, ia);
  const vb = new THREE.Vector3().fromBufferAttribute(pos, ib);
  const vc = new THREE.Vector3().fromBufferAttribute(pos, ic);
  target.subVectors(vb, va).cross(new THREE.Vector3().subVectors(vc, va)).normalize();
  return target;
}

const NORMAL_THRESHOLD = 0.992; // ~7°

function floodSelectFace(geometry, startTri, adjacency) {
  const baseNormal = triangleNormal(geometry, startTri);
  const visited = new Set();
  const queue = [startTri];

  while (queue.length) {
    const t = queue.pop();
    if (visited.has(t)) continue;
    const n = triangleNormal(geometry, t);
    if (n.dot(baseNormal) < NORMAL_THRESHOLD) continue;
    visited.add(t);
    for (const nb of adjacency.get(t) || []) {
      if (!visited.has(nb)) queue.push(nb);
    }
  }
  return visited;
}

function faceKeyFromStats(stats) {
  const roundPos = (v) => Math.round(v * 10) / 10;
  const roundNormal = (v) => Math.round(v * 1000) / 1000;
  const c = stats.center;
  const n = stats.normal;
  return `${roundPos(c.x)},${roundPos(c.y)},${roundPos(c.z)}|${roundNormal(n.x)},${roundNormal(n.y)},${roundNormal(n.z)}`;
}

/** Assign a stable id the first time this patch is selected; reuse on re-select. */
function registerFacePatch(geometry, triangles) {
  const stats = computeFaceStats(geometry, triangles);
  const key = faceKeyFromStats(stats);
  let id = faceKeyToId.get(key);
  if (!id) {
    id = nextFaceId++;
    faceKeyToId.set(key, id);
    registeredFaces.set(id, {
      id,
      center: stats.center.clone(),
      normal: stats.normal.clone(),
      area: stats.area,
    });
  }
  for (const t of triangles) triangleToFaceId.set(t, id);
  return id;
}

function faceIdsFromTriangles(triangles) {
  const ids = new Set();
  for (const t of triangles) {
    const id = triangleToFaceId.get(t);
    if (id) ids.add(id);
  }
  return [...ids].sort((a, b) => a - b);
}

const labelTextureCache = new Map();

function getFaceLabelTexture(faceId) {
  if (labelTextureCache.has(faceId)) return labelTextureCache.get(faceId);

  const text = String(faceId);
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  const fontSize = 40;
  ctx.font = `bold ${fontSize}px system-ui, sans-serif`;
  const pad = 10;
  const w = Math.ceil(ctx.measureText(text).width) + pad * 2;
  const h = fontSize + pad * 2;
  canvas.width = w;
  canvas.height = h;

  ctx.font = `bold ${fontSize}px system-ui, sans-serif`;
  ctx.fillStyle = "rgba(20, 24, 32, 0.82)";
  ctx.beginPath();
  ctx.roundRect(0, 0, w, h, 6);
  ctx.fill();
  ctx.strokeStyle = "rgba(126, 184, 255, 0.9)";
  ctx.lineWidth = 2;
  ctx.stroke();
  ctx.fillStyle = "#e8f0ff";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, w / 2, h / 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.userData.labelAspect = w / h;
  labelTextureCache.set(faceId, texture);
  return texture;
}

function clearLabelTextures() {
  for (const texture of labelTextureCache.values()) texture.dispose();
  labelTextureCache.clear();
}

function createFaceLabelSprite(faceId, selected = false) {
  const texture = getFaceLabelTexture(faceId);
  const material = new THREE.SpriteMaterial({
    map: texture,
    transparent: true,
    depthTest: false,
    depthWrite: false,
    opacity: selected ? 1 : 0.92,
  });
  const sprite = new THREE.Sprite(material);
  const height = selected ? 7.5 : 6;
  const aspect = texture.userData.labelAspect || 1;
  sprite.scale.set(height * aspect, height, 1);
  sprite.userData.faceId = faceId;
  return sprite;
}

function clearFaceLabels() {
  while (faceLabelsGroup.children.length) {
    const child = faceLabelsGroup.children[0];
    faceLabelsGroup.remove(child);
    child.material.dispose();
  }
}

function updateFaceLabels() {
  clearFaceLabels();
  for (const id of selectedFaceIds) {
    const face = registeredFaces.get(id);
    if (!face) continue;
    const sprite = createFaceLabelSprite(id, true);
    const offset = face.normal.clone().multiplyScalar(Math.max(0.8, Math.sqrt(face.area) * 0.02));
    sprite.position.copy(face.center).add(offset);
    faceLabelsGroup.add(sprite);
  }
}

function computeFaceStats(geometry, triangles) {
  const pos = geometry.attributes.position;
  const tempA = new THREE.Vector3();
  const tempB = new THREE.Vector3();
  const tempC = new THREE.Vector3();
  const edge1 = new THREE.Vector3();
  const edge2 = new THREE.Vector3();

  let area = 0;
  const center = new THREE.Vector3();
  const normal = triangleNormal(geometry, [...triangles][0]);
  const min = new THREE.Vector3(Infinity, Infinity, Infinity);
  const max = new THREE.Vector3(-Infinity, -Infinity, -Infinity);

  for (const t of triangles) {
    const [ia, ib, ic] = triangleVertexIndices(geometry, t);
    tempA.fromBufferAttribute(pos, ia);
    tempB.fromBufferAttribute(pos, ib);
    tempC.fromBufferAttribute(pos, ic);
    edge1.subVectors(tempB, tempA);
    edge2.subVectors(tempC, tempA);
    const triArea = edge1.cross(edge2).length() * 0.5;
    area += triArea;
    center.add(tempA).add(tempB).add(tempC);
    for (const v of [tempA, tempB, tempC]) {
      min.min(v);
      max.max(v);
    }
  }
  center.multiplyScalar(1 / (triangles.size * 3));

  const size = new THREE.Vector3().subVectors(max, min);
  const origin = new THREE.Vector3();
  const tangent = new THREE.Vector3();
  const bitangent = new THREE.Vector3();
  buildFaceBasis(normal, tangent, bitangent);

  let uMin = Infinity,
    uMax = -Infinity,
    vMin = Infinity,
    vMax = -Infinity;
  for (const t of triangles) {
    for (let k = 0; k < 3; k++) {
      const vi = triangleVertexIndices(geometry, t)[k];
      tempA.fromBufferAttribute(pos, vi);
      const du = tempA.dot(tangent);
      const dv = tempA.dot(bitangent);
      uMin = Math.min(uMin, du);
      uMax = Math.max(uMax, du);
      vMin = Math.min(vMin, dv);
      vMax = Math.max(vMax, dv);
    }
  }

  return {
    area,
    center,
    normal,
    bboxSize: size,
    planeWidth: uMax - uMin,
    planeHeight: vMax - vMin,
    triangleCount: triangles.size,
    min,
    max,
  };
}

function buildFaceBasis(normal, tangent, bitangent) {
  const up =
    Math.abs(normal.y) < 0.9 ? new THREE.Vector3(0, 1, 0) : new THREE.Vector3(1, 0, 0);
  tangent.crossVectors(up, normal).normalize();
  bitangent.crossVectors(normal, tangent).normalize();
}

function fmt(n, digits = 2) {
  return Number.isFinite(n) ? n.toFixed(digits) : "—";
}

function updateSelectionUI(stats, faceIds = []) {
  if (!stats) {
    selectionInfo.className = "info-panel empty";
    selectionInfo.textContent = "No face selected";
    extrudeBtn.disabled = true;
    selectedFaceIds.clear();
    updateFaceLabels();
    return;
  }
  selectedFaceIds = new Set(faceIds);
  const idLabel = faceIds.length === 1 ? "Face" : "Faces";
  const idText =
    faceIds.length === 1
      ? `#${faceIds[0]}`
      : faceIds.map((id) => `#${id}`).join(", ");
  selectionInfo.className = "info-panel";
  selectionInfo.innerHTML = `
    <dl>
      <dt>${idLabel}</dt><dd class="face-id">${idText}</dd>
      <dt>Area</dt><dd>${fmt(stats.area)} mm²</dd>
      <dt>Plane size (in-face)</dt><dd>${fmt(stats.planeWidth)} × ${fmt(stats.planeHeight)} mm</dd>
      <dt>World bbox</dt><dd>${fmt(stats.bboxSize.x)} × ${fmt(stats.bboxSize.y)} × ${fmt(stats.bboxSize.z)} mm</dd>
      <dt>Center</dt><dd>(${fmt(stats.center.x)}, ${fmt(stats.center.y)}, ${fmt(stats.center.z)})</dd>
      <dt>Normal</dt><dd>(${fmt(stats.normal.x, 3)}, ${fmt(stats.normal.y, 3)}, ${fmt(stats.normal.z, 3)})</dd>
      <dt>Triangles</dt><dd>${stats.triangleCount}</dd>
    </dl>`;
  extrudeBtn.disabled = false;
  updateFaceLabels();
}

function updateHighlight(geometry, triangles) {
  if (highlightMesh) {
    modelGroup.remove(highlightMesh);
    highlightMesh.geometry.dispose();
    highlightMesh.material.dispose();
    highlightMesh = null;
  }
  if (!triangles.size) return;

  const pos = geometry.attributes.position;
  const verts = [];
  const idx = [];
  let vi = 0;
  for (const t of triangles) {
    for (let k = 0; k < 3; k++) {
      const src = triangleVertexIndices(geometry, t)[k];
      verts.push(pos.getX(src), pos.getY(src), pos.getZ(src));
      idx.push(vi++);
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(verts, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  highlightMesh = new THREE.Mesh(
    g,
    new THREE.MeshBasicMaterial({
      color: 0x3d7eff,
      transparent: true,
      opacity: 0.45,
      side: THREE.DoubleSide,
      depthTest: true,
    })
  );
  modelGroup.add(highlightMesh);
}

function getBoundaryEdges(geometry, triangles) {
  const edgeCount = new Map();

  function edgeKey(a, b) {
    return a < b ? `${a}_${b}` : `${b}_${a}`;
  }

  for (const t of triangles) {
    const verts = triangleVertexIndices(geometry, t);
    for (const [a, b] of [
      [verts[0], verts[1]],
      [verts[1], verts[2]],
      [verts[2], verts[0]],
    ]) {
      const key = edgeKey(a, b);
      edgeCount.set(key, (edgeCount.get(key) || 0) + 1);
    }
  }

  const boundary = [];
  for (const [key, count] of edgeCount) {
    if (count === 1) {
      const [a, b] = key.split("_").map(Number);
      boundary.push([a, b]);
    }
  }
  return boundary;
}

function extrudeFace(geometry, triangles, distance, sign) {
  const pos = geometry.attributes.position;
  const stats = computeFaceStats(geometry, triangles);
  const normal = stats.normal.clone().multiplyScalar(sign * distance);

  const vertices = [];
  const indices = [];
  const vertMap = new Map();

  function getVertCopy(vi, offset) {
    const key = offset ? `o${vi}` : `${vi}`;
    if (vertMap.has(key)) return vertMap.get(key);
    const idx = vertices.length / 3;
    const v = new THREE.Vector3(pos.getX(vi), pos.getY(vi), pos.getZ(vi));
    if (offset) v.add(normal);
    vertices.push(v.x, v.y, v.z);
    vertMap.set(key, idx);
    return idx;
  }

  for (const t of triangles) {
    const [a, b, c] = triangleVertexIndices(geometry, t);
    const ia = getVertCopy(a, false);
    const ib = getVertCopy(b, false);
    const ic = getVertCopy(c, false);
    const oa = getVertCopy(a, true);
    const ob = getVertCopy(b, true);
    const oc = getVertCopy(c, true);
    indices.push(ia, ib, ic);
    indices.push(oa, oc, ob);
  }

  const boundary = getBoundaryEdges(geometry, triangles);
  for (const [a, b] of boundary) {
    const ia = getVertCopy(a, false);
    const ib = getVertCopy(b, false);
    const oa = getVertCopy(a, true);
    const ob = getVertCopy(b, true);
    indices.push(ia, ib, ob, ia, ob, oa);
  }

  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  g.setIndex(indices);
  g.computeVertexNormals();
  return g;
}

// ── Model loading ────────────────────────────────────────────────────────────
function clearModel() {
  selectedTriangles.clear();
  selectedFaceIds.clear();
  registeredFaces.clear();
  faceKeyToId.clear();
  triangleToFaceId.clear();
  nextFaceId = 1;
  clearFaceLabels();
  clearLabelTextures();
  updateSelectionUI(null);
  if (highlightMesh) {
    modelGroup.remove(highlightMesh);
    highlightMesh.geometry.dispose();
    highlightMesh.material.dispose();
    highlightMesh = null;
  }
  for (const m of extrusionMeshes) {
    modelGroup.remove(m);
    m.geometry.dispose();
    m.material.dispose();
  }
  extrusionMeshes = [];
  clearExtrudeBtn.disabled = true;

  if (bodyMesh) {
    modelGroup.remove(bodyMesh);
    bodyMesh.geometry.dispose();
    bodyMesh.material.dispose();
    bodyMesh = null;
  }
  if (edgeLines) {
    modelGroup.remove(edgeLines);
    edgeLines.geometry.dispose();
    edgeLines.material.dispose();
    edgeLines = null;
  }
  triangleAdjacency = new Map();
  modelGroup.quaternion.identity();
  modelGroup.position.set(0, 0, 0);
}

/** Lowest downward-facing triangle — exterior bottom in Z-up CAD exports. */
function findBottomTriangle(geometry) {
  const pos = geometry.attributes.position;
  const triCount = triangleCount(geometry);
  let bestTri = 0;
  let bestZ = Infinity;
  let fallbackTri = 0;
  let fallbackZ = Infinity;

  for (let t = 0; t < triCount; t++) {
    const normal = triangleNormal(geometry, t);
    const [ia, ib, ic] = triangleVertexIndices(geometry, t);
    const cz = (pos.getZ(ia) + pos.getZ(ib) + pos.getZ(ic)) / 3;
    if (cz < fallbackZ) {
      fallbackZ = cz;
      fallbackTri = t;
    }
    if (normal.z > -0.85) continue;
    if (cz < bestZ) {
      bestZ = cz;
      bestTri = t;
    }
  }
  return bestZ < Infinity ? bestTri : fallbackTri;
}

function registerBottomAsFaceOne(geometry, patch, stats) {
  const key = faceKeyFromStats(stats);
  faceKeyToId.set(key, 1);
  registeredFaces.set(1, {
    id: 1,
    center: stats.center.clone(),
    normal: stats.normal.clone(),
    area: stats.area,
  });
  for (const t of patch) triangleToFaceId.set(t, 1);
  nextFaceId = 2;
}

/** Rotate and drop the model so the exterior bottom sits on the Y=0 grid. */
function orientModelOnBottom(geometry, adjacency) {
  const bottomTri = findBottomTriangle(geometry);
  const patch = floodSelectFace(geometry, bottomTri, adjacency);
  const stats = computeFaceStats(geometry, patch);
  const normal = stats.normal.clone().normalize();

  const ground = new THREE.Vector3(0, -1, 0);
  if (Math.abs(normal.dot(ground)) < 0.999) {
    modelGroup.quaternion.setFromUnitVectors(normal, ground);
  } else {
    modelGroup.quaternion.identity();
  }
  modelGroup.position.set(0, 0, 0);
  modelGroup.updateMatrixWorld(true);

  const box = new THREE.Box3().setFromObject(modelGroup);
  modelGroup.position.y = -box.min.y;

  registerBottomAsFaceOne(geometry, patch, stats);
}

function fitToObject() {
  const box = new THREE.Box3().setFromObject(modelGroup);
  if (box.isEmpty()) return;
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const maxDim = Math.max(size.x, size.y, size.z);
  const dist = maxDim * 1.8;
  camera.position.set(center.x + dist * 0.65, center.y + dist * 0.45, center.z + dist * 0.75);
  controls.target.copy(center);
  controls.update();
}

function updateEdges() {
  if (edgeLines) {
    modelGroup.remove(edgeLines);
    edgeLines.geometry.dispose();
    edgeLines.material.dispose();
    edgeLines = null;
  }
  if (!showEdgesChk.checked || !bodyMesh) return;
  const edges = new THREE.EdgesGeometry(bodyMesh.geometry, 15);
  edgeLines = new THREE.LineSegments(
    edges,
    new THREE.LineBasicMaterial({ color: 0x6a7380 })
  );
  modelGroup.add(edgeLines);
}

async function loadModel(file, quiet = false) {
  if (!quiet) setStatus(`Loading ${file}…`);
  try {
    const url = `/api/model/${encodeURIComponent(file)}?t=${Date.now()}`;
    if (!quiet) setStatus(`Loading ${file}…`);
    const raw = await loader.loadAsync(url);
    if (!quiet) setStatus(`Preparing mesh for face selection…`);
    const geom = prepareGeometry(raw);

    clearModel();

    const mat = new THREE.MeshStandardMaterial({
      color: 0xb8c0cc,
      metalness: 0.15,
      roughness: 0.65,
      side: THREE.DoubleSide,
    });
    bodyMesh = new THREE.Mesh(geom, mat);
    modelGroup.add(bodyMesh);
    triangleAdjacency = buildAdjacency(geom);
    orientModelOnBottom(geom, triangleAdjacency);
    updateEdges();
    fitToObject();

    const mt = await fetchMtime(file);
    if (mt) lastMtime = mt.mtime;
    setStatus(`${file} — ${(mt?.size / 1024 / 1024).toFixed(2) || "?"} MB`);
  } catch (err) {
    setStatus(`Load failed: ${err.message}`, true);
  }
}

// ── Export merged mesh as STL binary ─────────────────────────────────────────
function buildExportObject() {
  const group = new THREE.Group();
  if (bodyMesh) group.add(bodyMesh.clone());
  for (const m of extrusionMeshes) group.add(m.clone());
  return group;
}

function exportSTLBinary() {
  const exporter = new STLExporter();
  const group = buildExportObject();
  const result = exporter.parse(group, { binary: true });
  group.traverse((c) => {
    if (c.geometry) c.geometry.dispose();
    if (c.material) c.material.dispose();
  });
  return result;
}

// ── Polling for file changes ─────────────────────────────────────────────────
async function pollMtime() {
  if (!autoReloadChk.checked || !currentFile) return;
  const mt = await fetchMtime(currentFile);
  if (mt && mt.mtime > lastMtime + 0.001) {
    setStatus(`File changed — reloading ${currentFile}`);
    await loadModel(currentFile, true);
  }
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(pollMtime, 1500);
}

// ── Interaction (left-click select, left-drag orbit) ───────────────────────
const CLICK_DRAG_PX = 6;
let pointerDownPos = null;

function pickFace(clientX, clientY, shiftKey) {
  if (!bodyMesh) return;
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const hits = raycaster.intersectObject(bodyMesh, false);
  if (!hits.length || hits[0].faceIndex === undefined || hits[0].faceIndex === null) {
    if (!shiftKey) {
      selectedTriangles.clear();
      updateHighlight(bodyMesh.geometry, selectedTriangles);
      updateSelectionUI(null);
    }
    return;
  }
  const faceIndex = hits[0].faceIndex;
  const patch = floodSelectFace(bodyMesh.geometry, faceIndex, triangleAdjacency);
  registerFacePatch(bodyMesh.geometry, patch);
  if (shiftKey) {
    for (const t of patch) selectedTriangles.add(t);
  } else {
    selectedTriangles = patch;
  }
  updateHighlight(bodyMesh.geometry, selectedTriangles);
  const stats = computeFaceStats(bodyMesh.geometry, selectedTriangles);
  const faceIds = faceIdsFromTriangles(selectedTriangles);
  updateSelectionUI(stats, faceIds);
}

renderer.domElement.addEventListener("pointerdown", (event) => {
  if (event.button !== 0) return;
  pointerDownPos = { x: event.clientX, y: event.clientY };
});

renderer.domElement.addEventListener("pointerup", (event) => {
  if (event.button !== 0 || !pointerDownPos) return;
  const dx = event.clientX - pointerDownPos.x;
  const dy = event.clientY - pointerDownPos.y;
  pointerDownPos = null;
  if (dx * dx + dy * dy > CLICK_DRAG_PX * CLICK_DRAG_PX) return;
  pickFace(event.clientX, event.clientY, event.shiftKey);
});

// ── UI events ────────────────────────────────────────────────────────────────
fileSelect.addEventListener("change", () => {
  currentFile = fileSelect.value;
  loadModel(currentFile);
});

reloadBtn.addEventListener("click", () => loadModel(currentFile));
autoReloadChk.addEventListener("change", startPolling);
fitBtn.addEventListener("click", fitToObject);
showEdgesChk.addEventListener("change", updateEdges);

clearSelectionBtn.addEventListener("click", () => {
  selectedTriangles.clear();
  if (bodyMesh) updateHighlight(bodyMesh.geometry, selectedTriangles);
  updateSelectionUI(null);
});

extrudeBtn.addEventListener("click", () => {
  if (!bodyMesh || !selectedTriangles.size) return;
  const dist = parseFloat(extrudeDistance.value);
  const sign = parseInt(extrudeDirection.value, 10);
  if (!dist || dist <= 0) return;
  const geom = extrudeFace(bodyMesh.geometry, selectedTriangles, dist, sign);
  const mesh = new THREE.Mesh(
    geom,
    new THREE.MeshStandardMaterial({
      color: 0x7eb8ff,
      metalness: 0.1,
      roughness: 0.7,
      side: THREE.DoubleSide,
    })
  );
  extrusionMeshes.push(mesh);
  modelGroup.add(mesh);
  clearExtrudeBtn.disabled = false;
  setStatus(`Extruded ${fmt(dist)} mm (${extrusionMeshes.length} add-on${extrusionMeshes.length > 1 ? "s" : ""})`);
});

clearExtrudeBtn.addEventListener("click", () => {
  const last = extrusionMeshes.pop();
  if (last) {
    modelGroup.remove(last);
    last.geometry.dispose();
    last.material.dispose();
  }
  clearExtrudeBtn.disabled = extrusionMeshes.length === 0;
  setStatus(extrusionMeshes.length ? `${extrusionMeshes.length} extrusion(s) remaining` : "Extrusions cleared");
});

saveBtn.addEventListener("click", async () => {
  if (!bodyMesh) return;
  const stl = exportSTLBinary();
  setStatus("Saving…");
  try {
    const res = await fetch(`/api/save?file=${encodeURIComponent(currentFile)}`, {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream" },
      body: stl,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || res.statusText);
    lastMtime = data.mtime;
    setStatus(`Saved ${data.file} (${(data.size / 1024 / 1024).toFixed(2)} MB)`);
  } catch (err) {
    setStatus(`Save failed: ${err.message}`, true);
  }
});

downloadBtn.addEventListener("click", () => {
  if (!bodyMesh) return;
  const stl = exportSTLBinary();
  const blob = new Blob([stl], { type: "application/octet-stream" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = currentFile.split("/").pop() || "model.stl";
  a.click();
  URL.revokeObjectURL(a.href);
});

// ── Init ─────────────────────────────────────────────────────────────────────
async function init() {
  const files = await fetchFiles();
  fileSelect.innerHTML = "";
  for (const f of files) {
    const opt = document.createElement("option");
    opt.value = f.path;
    opt.textContent = `${f.path} (${(f.size / 1024 / 1024).toFixed(1)} MB)`;
    fileSelect.appendChild(opt);
  }
  const preferred = files.find((f) => f.path === "car-2/enclosure_body.stl");
  currentFile = preferred ? preferred.path : files[0]?.path || currentFile;
  fileSelect.value = currentFile;
  await loadModel(currentFile);
  startPolling();
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();
init();
