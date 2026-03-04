import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";
import { OrbitControls } from "https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js";

const MODULE_ORDER = ["rod", "connector", "panel"];
const SCALE = 0.1;

const defaultValues = {
  layers_n: 4,
  payload_p_per_layer: 30,
  space_width: 80,
  space_depth: 35,
  space_height: 30,
  opening_width: 65,
  opening_height: 28,
  footprint_width: 90,
  footprint_depth: 40,
  rod_count: 4,
  connector_count: 12,
  panel_count: 4,
  baseline_efficiency: 1.0,
  target_efficiency: 1.22,
};

const form = document.getElementById("shelf-form");
const viewport = document.getElementById("viewport");
const statusPill = document.getElementById("status-pill");
const reasonsList = document.getElementById("reasons");
const metricsBox = document.getElementById("metrics");
const resetButton = document.getElementById("reset-demo");

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
viewport.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xdfe5d8, 16, 82);

const camera = new THREE.PerspectiveCamera(48, 1, 0.1, 320);
camera.position.set(24, 17, 29);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.target.set(0, 4, 0);
controls.update();

scene.add(new THREE.HemisphereLight(0xf2fbe8, 0x7f9f8e, 1.15));

const keyLight = new THREE.DirectionalLight(0xfff8d8, 1.1);
keyLight.position.set(16, 24, 10);
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0xc6f0ff, 0.35);
fillLight.position.set(-12, 9, -10);
scene.add(fillLight);

const ground = new THREE.Mesh(
  new THREE.CircleGeometry(40, 72),
  new THREE.MeshStandardMaterial({
    color: 0xc2d1bf,
    roughness: 0.93,
    metalness: 0.02,
    transparent: true,
    opacity: 0.9,
  })
);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.02;
scene.add(ground);

const grid = new THREE.GridHelper(80, 72, 0x5f846d, 0x9cb39e);
grid.position.y = 0.02;
grid.material.opacity = 0.28;
grid.material.transparent = true;
scene.add(grid);

const shelfGroup = new THREE.Group();
scene.add(shelfGroup);

function toNumber(value, fallback = 0) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function toInt(value, fallback = 0) {
  return Math.round(toNumber(value, fallback));
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function readState() {
  const data = new FormData(form);
  return {
    boundary: {
      layers_n: toInt(data.get("layers_n"), defaultValues.layers_n),
      payload_p_per_layer: toNumber(
        data.get("payload_p_per_layer"),
        defaultValues.payload_p_per_layer
      ),
      space_s_per_layer: {
        width: toNumber(data.get("space_width"), defaultValues.space_width),
        depth: toNumber(data.get("space_depth"), defaultValues.space_depth),
        height: toNumber(data.get("space_height"), defaultValues.space_height),
      },
      opening_o: {
        width: toNumber(data.get("opening_width"), defaultValues.opening_width),
        height: toNumber(data.get("opening_height"), defaultValues.opening_height),
      },
      footprint_a: {
        width: toNumber(data.get("footprint_width"), defaultValues.footprint_width),
        depth: toNumber(data.get("footprint_depth"), defaultValues.footprint_depth),
      },
    },
    modules: {
      rod: Math.max(0, toInt(data.get("rod_count"), defaultValues.rod_count)),
      connector: Math.max(
        0,
        toInt(data.get("connector_count"), defaultValues.connector_count)
      ),
      panel: Math.max(0, toInt(data.get("panel_count"), defaultValues.panel_count)),
    },
    baseline_efficiency: toNumber(
      data.get("baseline_efficiency"),
      defaultValues.baseline_efficiency
    ),
    target_efficiency: toNumber(
      data.get("target_efficiency"),
      defaultValues.target_efficiency
    ),
  };
}

function validateBoundary(boundary) {
  const errors = [];

  if (!Number.isInteger(boundary.layers_n) || boundary.layers_n <= 0) {
    errors.push("layers_n must be > 0");
  }
  if (boundary.payload_p_per_layer <= 0) {
    errors.push("payload_p_per_layer must be > 0");
  }
  if (
    boundary.space_s_per_layer.width <= 0 ||
    boundary.space_s_per_layer.depth <= 0 ||
    boundary.space_s_per_layer.height <= 0
  ) {
    errors.push("space_s_per_layer must be positive on all dimensions");
  }
  if (boundary.opening_o.width <= 0 || boundary.opening_o.height <= 0) {
    errors.push("opening_o must be positive on all dimensions");
  }
  if (boundary.footprint_a.width <= 0 || boundary.footprint_a.depth <= 0) {
    errors.push("footprint_a must be positive on all dimensions");
  }

  return errors;
}

function getCandidateCombo(modules) {
  return MODULE_ORDER.filter((name) => modules[name] > 0);
}

function allModuleSubsets() {
  const items = [...MODULE_ORDER];
  const subsets = [];

  for (let mask = 0; mask < 1 << items.length; mask += 1) {
    const subset = [];
    for (let idx = 0; idx < items.length; idx += 1) {
      if ((mask & (1 << idx)) !== 0) {
        subset.push(items[idx]);
      }
    }
    subsets.push(subset);
  }
  return subsets;
}

function validCombinations() {
  return allModuleSubsets().filter(
    (subset) => subset.length >= 2 && subset.includes("connector")
  );
}

function sameSet(left, right) {
  if (left.length !== right.length) {
    return false;
  }
  return left.every((item) => right.includes(item));
}

function verifyState(state) {
  const boundaryErrors = validateBoundary(state.boundary);
  const candidateCombo = getCandidateCombo(state.modules);
  const validCombos = validCombinations();

  const combinationValid = validCombos.some((combo) =>
    sameSet(combo, candidateCombo)
  );
  const efficiencyImproved =
    state.target_efficiency > state.baseline_efficiency;

  const reasons = [...boundaryErrors];
  if (!combinationValid) {
    reasons.push("combo is not in valid combinations");
  }
  if (!efficiencyImproved) {
    reasons.push("target_efficiency must be > baseline_efficiency");
  }

  return {
    boundary_valid: boundaryErrors.length === 0,
    combination_valid: combinationValid,
    efficiency_improved: efficiencyImproved,
    passed:
      boundaryErrors.length === 0 && combinationValid && efficiencyImproved,
    reasons,
    candidate_combo: candidateCombo,
    valid_combinations: validCombos,
  };
}

function renderBoundary(boundary) {
  return {
    layers: Math.max(1, Math.round(Math.abs(boundary.layers_n || 1))),
    width: Math.max(2, Math.abs(boundary.footprint_a.width) * SCALE),
    depth: Math.max(2, Math.abs(boundary.footprint_a.depth) * SCALE),
    layerHeight: Math.max(1, Math.abs(boundary.space_s_per_layer.height) * SCALE),
    panelWidth: Math.max(1, Math.abs(boundary.space_s_per_layer.width) * SCALE),
    panelDepth: Math.max(1, Math.abs(boundary.space_s_per_layer.depth) * SCALE),
    openingWidth: Math.max(0.6, Math.abs(boundary.opening_o.width) * SCALE),
    openingHeight: Math.max(0.6, Math.abs(boundary.opening_o.height) * SCALE),
  };
}

function buildRodPositions(count, width, depth) {
  if (count <= 0) {
    return [];
  }

  const cols = Math.max(2, Math.ceil(Math.sqrt(count)));
  const rows = Math.max(2, Math.ceil(count / cols));
  const inset = Math.max(0.22, Math.min(width, depth) * 0.08);
  const usableWidth = Math.max(0.2, width - inset * 2);
  const usableDepth = Math.max(0.2, depth - inset * 2);

  const points = [];
  for (let idx = 0; idx < count; idx += 1) {
    const row = Math.floor(idx / cols);
    const col = idx % cols;
    const x =
      cols === 1
        ? 0
        : -usableWidth / 2 + (usableWidth * col) / (cols - 1);
    const z =
      rows === 1
        ? 0
        : -usableDepth / 2 + (usableDepth * row) / (rows - 1);
    points.push({ x, z });
  }
  return points;
}

function buildPanelLevels(panelCount, layers) {
  if (panelCount <= 0) {
    return [];
  }
  if (panelCount >= layers) {
    return Array.from({ length: layers }, (_, idx) => idx + 1);
  }

  const levels = new Set();
  for (let idx = 0; idx < panelCount; idx += 1) {
    const ratio = (idx + 1) / (panelCount + 1);
    const level = clamp(Math.round(ratio * layers), 1, layers);
    levels.add(level);
  }

  if (levels.size < panelCount) {
    for (let level = 1; level <= layers && levels.size < panelCount; level += 1) {
      levels.add(level);
    }
  }

  return [...levels].sort((a, b) => a - b);
}

function buildConnectorPoints(rodPositions, layers, layerHeight, connectorCount) {
  const points = [];
  if (connectorCount <= 0 || rodPositions.length === 0) {
    return points;
  }

  for (const rod of rodPositions) {
    for (let level = 0; level <= layers; level += 1) {
      points.push({
        x: rod.x,
        y: level * layerHeight,
        z: rod.z,
      });
      if (points.length >= connectorCount) {
        return points;
      }
    }
  }
  return points;
}

function disposeObject(node) {
  for (const child of node.children) {
    disposeObject(child);
  }
  if (node.geometry) {
    node.geometry.dispose();
  }
  if (node.material) {
    if (Array.isArray(node.material)) {
      node.material.forEach((material) => material.dispose());
    } else {
      node.material.dispose();
    }
  }
}

function clearGroup(group) {
  while (group.children.length > 0) {
    const child = group.children[0];
    group.remove(child);
    disposeObject(child);
  }
}

function setStatus(result) {
  statusPill.classList.remove("status-ok", "status-bad");
  if (result.passed) {
    statusPill.classList.add("status-ok");
    statusPill.textContent = "Verification passed";
  } else {
    statusPill.classList.add("status-bad");
    statusPill.textContent = "Verification failed";
  }

  const reasons = result.reasons.length > 0 ? result.reasons : ["all checks passed"];
  reasonsList.innerHTML = reasons
    .map((reason) => `<li>${reason}</li>`)
    .join("");
}

function setMetrics(metrics) {
  const entries = [
    { label: "active modules", value: metrics.activeModules || "none" },
    { label: "valid combos", value: String(metrics.validCombos) },
    { label: "rendered rods", value: String(metrics.rods) },
    { label: "rendered connectors", value: String(metrics.connectors) },
    { label: "rendered panels", value: String(metrics.panels) },
    { label: "estimated height", value: `${metrics.totalHeight.toFixed(1)} u` },
  ];

  metricsBox.innerHTML = entries
    .map(
      (item) =>
        `<div class="metric"><span class="label">${item.label}</span><span class="value">${item.value}</span></div>`
    )
    .join("");
}

function refitCamera(width, totalHeight, depth) {
  const span = Math.max(width, depth, totalHeight);
  const distance = span * 2.2 + 8;
  camera.position.set(distance * 0.78, totalHeight + span * 1.08 + 2, distance);
  controls.target.set(0, totalHeight * 0.45, 0);
  controls.update();
}

function drawShelf(state, result) {
  clearGroup(shelfGroup);

  const bounds = renderBoundary(state.boundary);
  const totalHeight = bounds.layers * bounds.layerHeight;
  const rodCount = Math.max(0, state.modules.rod);
  const connectorCount = Math.max(0, state.modules.connector);
  const panelCount = Math.max(0, state.modules.panel);

  const rodPositions = buildRodPositions(rodCount, bounds.width, bounds.depth);
  const panelLevels = buildPanelLevels(panelCount, bounds.layers);
  const connectorPoints = buildConnectorPoints(
    rodPositions,
    bounds.layers,
    bounds.layerHeight,
    connectorCount
  );

  const frame = new THREE.LineSegments(
    new THREE.EdgesGeometry(
      new THREE.BoxGeometry(bounds.width, totalHeight, bounds.depth)
    ),
    new THREE.LineBasicMaterial({ color: 0x25544a })
  );
  frame.position.y = totalHeight / 2;
  shelfGroup.add(frame);

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(bounds.width + 0.45, 0.32, bounds.depth + 0.45),
    new THREE.MeshStandardMaterial({
      color: 0x3f5f53,
      roughness: 0.65,
      metalness: 0.18,
    })
  );
  base.position.y = -0.16;
  shelfGroup.add(base);

  const rodRadius = clamp(Math.min(bounds.width, bounds.depth) * 0.028, 0.12, 0.42);
  const rodGeometry = new THREE.CylinderGeometry(rodRadius, rodRadius, totalHeight + 0.02, 18);
  const rodMaterial = new THREE.MeshStandardMaterial({
    color: 0x88a89a,
    roughness: 0.3,
    metalness: 0.86,
  });
  for (const point of rodPositions) {
    const rod = new THREE.Mesh(rodGeometry, rodMaterial);
    rod.position.set(point.x, totalHeight / 2, point.z);
    shelfGroup.add(rod);
  }

  const safePanelWidth = clamp(bounds.panelWidth, 0.8, bounds.width * 0.97);
  const safePanelDepth = clamp(bounds.panelDepth, 0.8, bounds.depth * 0.97);
  const panelThickness = clamp(bounds.layerHeight * 0.11, 0.1, 0.42);
  const panelGeometry = new THREE.BoxGeometry(
    safePanelWidth,
    panelThickness,
    safePanelDepth
  );
  const panelMaterial = new THREE.MeshStandardMaterial({
    color: 0xc9ab6f,
    roughness: 0.78,
    metalness: 0.06,
  });
  for (const level of panelLevels) {
    const panel = new THREE.Mesh(panelGeometry, panelMaterial);
    panel.position.y = level * bounds.layerHeight - panelThickness / 2;
    shelfGroup.add(panel);
  }

  const connectorRadius = clamp(rodRadius * 0.82, 0.09, 0.28);
  const connectorGeometry = new THREE.SphereGeometry(connectorRadius, 14, 14);
  const connectorMaterial = new THREE.MeshStandardMaterial({
    color: 0xea7f35,
    roughness: 0.45,
    metalness: 0.2,
    emissive: result.passed ? 0x153a1e : 0x3f0d08,
    emissiveIntensity: result.passed ? 0.08 : 0.16,
  });
  for (const point of connectorPoints) {
    const connector = new THREE.Mesh(connectorGeometry, connectorMaterial);
    connector.position.set(point.x, point.y, point.z);
    shelfGroup.add(connector);
  }

  const openingWidth = clamp(bounds.openingWidth, 0.3, bounds.width * 0.98);
  const openingHeight = clamp(bounds.openingHeight, 0.3, totalHeight);
  const openingBaseY = Math.max(0.05, bounds.layerHeight * 0.08);
  const openingTopY = clamp(openingBaseY + openingHeight, openingBaseY, totalHeight);
  const openingZ = bounds.depth / 2 + 0.08;
  const halfOpeningWidth = openingWidth / 2;

  const openingPoints = [
    new THREE.Vector3(-halfOpeningWidth, openingBaseY, openingZ),
    new THREE.Vector3(halfOpeningWidth, openingBaseY, openingZ),
    new THREE.Vector3(halfOpeningWidth, openingTopY, openingZ),
    new THREE.Vector3(-halfOpeningWidth, openingTopY, openingZ),
    new THREE.Vector3(-halfOpeningWidth, openingBaseY, openingZ),
  ];
  const openingGeometry = new THREE.BufferGeometry().setFromPoints(openingPoints);
  const openingLine = new THREE.Line(
    openingGeometry,
    new THREE.LineBasicMaterial({ color: 0x2a6983 })
  );
  shelfGroup.add(openingLine);

  refitCamera(bounds.width, totalHeight, bounds.depth);

  setStatus(result);
  setMetrics({
    activeModules: result.candidate_combo.join(", "),
    validCombos: result.valid_combinations.length,
    rods: rodPositions.length,
    connectors: connectorPoints.length,
    panels: panelLevels.length,
    totalHeight,
  });
}

function syncForm(values) {
  for (const [key, value] of Object.entries(values)) {
    const input = form.querySelector(`[name="${key}"]`);
    if (input) {
      input.value = String(value);
    }
  }
}

function run() {
  const state = readState();
  const result = verifyState(state);
  drawShelf(state, result);
}

function resizeRenderer() {
  const width = Math.max(1, viewport.clientWidth);
  const height = Math.max(1, viewport.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

let scheduleHandle = 0;
function scheduleRun() {
  window.clearTimeout(scheduleHandle);
  scheduleHandle = window.setTimeout(() => {
    run();
  }, 90);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  run();
});

form.addEventListener("input", scheduleRun);

resetButton.addEventListener("click", () => {
  syncForm(defaultValues);
  run();
});

const resizeObserver = new ResizeObserver(() => {
  resizeRenderer();
});
resizeObserver.observe(viewport);

window.addEventListener("resize", resizeRenderer);

function animate() {
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

resizeRenderer();
syncForm(defaultValues);
run();
animate();
