import * as THREE from "https://unpkg.com/three@0.160.0/build/three.module.js";
import { OrbitControls } from "https://unpkg.com/three@0.160.0/examples/jsm/controls/OrbitControls.js";

const MODULE_LABEL = {
  rod: "杆",
  connector: "连接接口",
  panel: "隔板",
};

const DEFAULT_FORM_VALUES = {
  enable_layers_n: true,
  layers_n: 4,
  enable_payload_p_per_layer: true,
  payload_p_per_layer: 1,
  enable_space_width: true,
  space_width: 4,
  enable_space_depth: true,
  space_depth: 2,
  enable_space_height: true,
  space_height: 1,
  enable_opening_width: true,
  opening_width: 3,
  enable_opening_height: true,
  opening_height: 0.8,
  enable_footprint_width: true,
  footprint_width: 4.4,
  enable_footprint_depth: true,
  footprint_depth: 2.2,
  rod_count: 4,
  connector_count: 12,
  panel_count: 4,
  enable_rule_r1: true,
  enable_rule_r2: true,
};

const BOUNDARY_FIELDS = [
  { key: "layers_n", enable: "enable_layers_n", input: "layers_n" },
  {
    key: "payload_p_per_layer",
    enable: "enable_payload_p_per_layer",
    input: "payload_p_per_layer",
  },
  { key: "space_width", enable: "enable_space_width", input: "space_width" },
  { key: "space_depth", enable: "enable_space_depth", input: "space_depth" },
  { key: "space_height", enable: "enable_space_height", input: "space_height" },
  {
    key: "opening_width",
    enable: "enable_opening_width",
    input: "opening_width",
  },
  {
    key: "opening_height",
    enable: "enable_opening_height",
    input: "opening_height",
  },
  {
    key: "footprint_width",
    enable: "enable_footprint_width",
    input: "footprint_width",
  },
  {
    key: "footprint_depth",
    enable: "enable_footprint_depth",
    input: "footprint_depth",
  },
];

const form = document.getElementById("shelf-form");
const comboList = document.getElementById("combo-list");
const resultSummary = document.getElementById("result-summary");
const resetButton = document.getElementById("reset-demo");
const viewport = document.getElementById("viewport");
const comboTitle = document.getElementById("combo-title");
const statusPill = document.getElementById("status-pill");
const reasonsList = document.getElementById("reasons");
const metricsBox = document.getElementById("metrics");
const submitButton = document.getElementById("confirm-generate");

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
viewport.appendChild(renderer.domElement);

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0xdfe7de, 18, 76);

const camera = new THREE.PerspectiveCamera(46, 1, 0.1, 400);
camera.position.set(11, 9, 14);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.target.set(0, 1.8, 0);
controls.update();

scene.add(new THREE.HemisphereLight(0xf5fcea, 0x6c8a7a, 1.16));

const keyLight = new THREE.DirectionalLight(0xfff7d6, 1.08);
keyLight.position.set(18, 24, 13);
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0xcce4f7, 0.38);
fillLight.position.set(-11, 12, -8);
scene.add(fillLight);

const ground = new THREE.Mesh(
  new THREE.CircleGeometry(36, 72),
  new THREE.MeshStandardMaterial({
    color: 0xc6d5c6,
    roughness: 0.94,
    metalness: 0.04,
    transparent: true,
    opacity: 0.88,
  })
);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.015;
scene.add(ground);

const grid = new THREE.GridHelper(40, 60, 0x5a7f6e, 0x99b09e);
grid.position.y = 0.02;
grid.material.transparent = true;
grid.material.opacity = 0.3;
scene.add(grid);

const shelfGroup = new THREE.Group();
scene.add(shelfGroup);

let generatedContext = null;
let generatedResults = [];
let selectedComboId = "";

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

function formatNumber(value) {
  if (!Number.isFinite(value)) {
    return "0";
  }
  if (Math.abs(value - Math.round(value)) < 1e-8) {
    return String(Math.round(value));
  }
  return value.toFixed(2).replace(/\.00$/, "");
}

function getElement(name) {
  return form.elements.namedItem(name);
}

function getChecked(name) {
  const element = getElement(name);
  return Boolean(element && element.type === "checkbox" && element.checked);
}

function getNumeric(name, fallback) {
  const element = getElement(name);
  if (!element) {
    return fallback;
  }
  return toNumber(element.value, fallback);
}

function applyDefaults() {
  for (const [name, value] of Object.entries(DEFAULT_FORM_VALUES)) {
    const element = getElement(name);
    if (!element) {
      continue;
    }
    if (element.type === "checkbox") {
      element.checked = Boolean(value);
    } else {
      element.value = String(value);
    }
  }
}

function refreshBoundaryEnableState() {
  for (const field of BOUNDARY_FIELDS) {
    const enabled = getChecked(field.enable);
    const input = getElement(field.input);
    if (!input) {
      continue;
    }
    input.disabled = !enabled;
    const row = input.closest(".input-row");
    if (row) {
      row.classList.toggle("inactive", !enabled);
    }
  }
}

function buildRequestPayload() {
  const boundaryInput = {};
  for (const field of BOUNDARY_FIELDS) {
    const raw = getNumeric(field.input, 1);
    const value =
      field.key === "layers_n" ? toInt(raw, 1) : toNumber(raw, 1);
    boundaryInput[field.key] = {
      enabled: getChecked(field.enable),
      value,
    };
  }

  return {
    boundary_input: boundaryInput,
    module_counts: {
      rod: Math.max(0, toInt(getNumeric("rod_count", 0), 0)),
      connector: Math.max(0, toInt(getNumeric("connector_count", 0), 0)),
      panel: Math.max(0, toInt(getNumeric("panel_count", 0), 0)),
    },
    rules: {
      r1: getChecked("enable_rule_r1"),
      r2: getChecked("enable_rule_r2"),
    },
  };
}

function setLoading(loading) {
  submitButton.disabled = loading;
  submitButton.textContent = loading ? "正在生成..." : "确认并生成组合结果";
}

async function requestGeneration(payload) {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    let body = {};
    try {
      body = await response.json();
    } catch {
      body = {};
    }

    if (!response.ok || !body.ok) {
      throw new Error(body.error || `请求失败（HTTP ${response.status}）`);
    }
    return body;
  } finally {
    window.clearTimeout(timeout);
  }
}

function renderComboList(results) {
  comboList.innerHTML = "";

  if (results.length === 0) {
    comboList.innerHTML =
      '<li class="combo-item"><p class="combo-title">没有可展示的组合</p></li>';
    return;
  }

  results.forEach((combo, idx) => {
    const li = document.createElement("li");
    li.className = "combo-item";
    li.dataset.comboId = combo.id;

    const badgeClass = combo.valid ? "badge-ok" : "badge-bad";
    const badgeText = combo.valid ? "有效" : "无效";
    const countLine = `M1:${combo.render_counts.rod}  M2:${combo.render_counts.connector}  M3:${combo.render_counts.panel}`;

    li.innerHTML = `
      <div class="combo-top">
        <p class="combo-title">#${idx + 1} ${combo.label}</p>
        <span class="combo-badge ${badgeClass}">${badgeText}</span>
      </div>
      <p class="combo-sub">${countLine}</p>
    `;

    comboList.appendChild(li);
  });
}

function updateSummary(context) {
  const activeRules = [];
  if (context.rules.r1) {
    activeRules.push("R1");
  }
  if (context.rules.r2) {
    activeRules.push("R2");
  }

  const ruleText = activeRules.length > 0 ? activeRules.join(" + ") : "无";
  resultSummary.textContent =
    `共 ${context.summary.total} 个组合，有效 ${context.summary.valid} 个；` +
    `生效边界参数 ${context.active_boundary_codes.length}/9；` +
    `生效规则 ${ruleText}`;
}

function setStatus(valid) {
  statusPill.classList.remove("status-ok", "status-bad");
  if (valid) {
    statusPill.classList.add("status-ok");
    statusPill.textContent = "当前组合有效";
  } else {
    statusPill.classList.add("status-bad");
    statusPill.textContent = "当前组合无效";
  }
}

function setReasons(errors) {
  const lines =
    errors.length > 0 ? errors : ["通过当前启用的边界校验与组合原则。"];
  reasonsList.innerHTML = lines.map((line) => `<li>${line}</li>`).join("");
}

function setMetrics(context, combo) {
  const cards = [
    { label: "模块类型", value: String(combo.modules.length) },
    {
      label: "模块数量",
      value: `杆:${combo.render_counts.rod} 接口:${combo.render_counts.connector} 隔板:${combo.render_counts.panel}`,
    },
    { label: "层数 N", value: String(context.boundary.layers_n) },
    {
      label: "占地 A",
      value: `${formatNumber(context.boundary.footprint_a.width)} x ${formatNumber(context.boundary.footprint_a.depth)}`,
    },
    {
      label: "每层承重 P",
      value: formatNumber(context.boundary.payload_p_per_layer),
    },
    {
      label: "生效边界",
      value: context.active_boundary_codes.join(", ") || "无",
    },
  ];

  metricsBox.innerHTML = cards
    .map(
      (item) =>
        `<div class="metric"><span class="label">${item.label}</span><span class="value">${item.value}</span></div>`
    )
    .join("");
}

function disposeNode(node) {
  for (const child of node.children) {
    disposeNode(child);
  }
  if (node.geometry) {
    node.geometry.dispose();
  }
  if (node.material) {
    if (Array.isArray(node.material)) {
      node.material.forEach((item) => item.dispose());
    } else {
      node.material.dispose();
    }
  }
}

function clearGroup(group) {
  while (group.children.length > 0) {
    const child = group.children[0];
    group.remove(child);
    disposeNode(child);
  }
}

function normalizeBoundary(boundary) {
  const layers = clamp(Math.round(boundary.layers_n), 1, 12);
  const width = clamp(boundary.footprint_a.width, 1, 20);
  const depth = clamp(boundary.footprint_a.depth, 1, 16);
  const layerHeight = clamp(boundary.space_s_per_layer.height, 0.5, 6);
  const panelWidth = clamp(boundary.space_s_per_layer.width, 0.7, width * 0.98);
  const panelDepth = clamp(boundary.space_s_per_layer.depth, 0.7, depth * 0.98);
  const openingWidth = clamp(boundary.opening_o.width, 0.4, width * 0.98);
  const openingHeight = clamp(boundary.opening_o.height, 0.4, layers * layerHeight);

  return {
    layers,
    width,
    depth,
    layerHeight,
    panelWidth,
    panelDepth,
    openingWidth,
    openingHeight,
  };
}

function buildRodPositions(count, width, depth) {
  if (count <= 0) {
    return [];
  }

  const cols = Math.max(2, Math.ceil(Math.sqrt(count)));
  const rows = Math.max(2, Math.ceil(count / cols));
  const inset = Math.max(0.16, Math.min(width, depth) * 0.1);
  const availableWidth = Math.max(0.3, width - inset * 2);
  const availableDepth = Math.max(0.3, depth - inset * 2);

  const points = [];
  for (let idx = 0; idx < count; idx += 1) {
    const row = Math.floor(idx / cols);
    const col = idx % cols;
    const x =
      cols === 1 ? 0 : -availableWidth / 2 + (availableWidth * col) / (cols - 1);
    const z =
      rows === 1 ? 0 : -availableDepth / 2 + (availableDepth * row) / (rows - 1);
    points.push({ x, z });
  }

  return points;
}

function buildPanelHeights(panelCount, totalHeight) {
  if (panelCount <= 0) {
    return [];
  }
  const count = Math.min(24, panelCount);
  const heights = [];
  for (let idx = 0; idx < count; idx += 1) {
    heights.push(((idx + 1) / (count + 1)) * totalHeight);
  }
  return heights;
}

function buildConnectorPoints(rodPositions, layers, layerHeight, count) {
  const points = [];
  if (count <= 0 || rodPositions.length === 0) {
    return points;
  }

  for (const rod of rodPositions) {
    for (let level = 0; level <= layers; level += 1) {
      points.push({
        x: rod.x,
        y: level * layerHeight,
        z: rod.z,
      });
      if (points.length >= count) {
        return points;
      }
    }
  }

  return points;
}

function refitCamera(width, totalHeight, depth) {
  const span = Math.max(width, depth, totalHeight);
  const distance = span * 2.25 + 4;
  camera.position.set(distance * 0.84, totalHeight + span * 0.94 + 2, distance);
  controls.target.set(0, totalHeight * 0.48, 0);
  controls.update();
}

function drawShelf(boundary, renderCounts, valid) {
  clearGroup(shelfGroup);
  const spec = normalizeBoundary(boundary);
  const totalHeight = spec.layers * spec.layerHeight;

  const frame = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(spec.width, totalHeight, spec.depth)),
    new THREE.LineBasicMaterial({ color: 0x2d5a4d })
  );
  frame.position.y = totalHeight / 2;
  shelfGroup.add(frame);

  const base = new THREE.Mesh(
    new THREE.BoxGeometry(spec.width + 0.36, 0.24, spec.depth + 0.36),
    new THREE.MeshStandardMaterial({
      color: 0x3f6457,
      roughness: 0.62,
      metalness: 0.2,
    })
  );
  base.position.y = -0.12;
  shelfGroup.add(base);

  const rodPositions = buildRodPositions(renderCounts.rod, spec.width, spec.depth);
  const rodRadius = clamp(Math.min(spec.width, spec.depth) * 0.035, 0.06, 0.28);
  const rodGeometry = new THREE.CylinderGeometry(
    rodRadius,
    rodRadius,
    totalHeight + 0.01,
    18
  );
  const rodMaterial = new THREE.MeshStandardMaterial({
    color: 0x88a79b,
    roughness: 0.32,
    metalness: 0.86,
  });
  for (const point of rodPositions) {
    const rod = new THREE.Mesh(rodGeometry, rodMaterial);
    rod.position.set(point.x, totalHeight / 2, point.z);
    shelfGroup.add(rod);
  }

  const panelHeights = buildPanelHeights(renderCounts.panel, totalHeight);
  const panelThickness = clamp(spec.layerHeight * 0.16, 0.08, 0.3);
  const panelGeometry = new THREE.BoxGeometry(
    spec.panelWidth,
    panelThickness,
    spec.panelDepth
  );
  const panelMaterial = new THREE.MeshStandardMaterial({
    color: 0xcaab70,
    roughness: 0.8,
    metalness: 0.06,
  });
  for (const y of panelHeights) {
    const panel = new THREE.Mesh(panelGeometry, panelMaterial);
    panel.position.y = y;
    shelfGroup.add(panel);
  }

  const connectorPoints = buildConnectorPoints(
    rodPositions,
    spec.layers,
    spec.layerHeight,
    renderCounts.connector
  );
  const connectorGeometry = new THREE.SphereGeometry(
    clamp(rodRadius * 0.78, 0.05, 0.2),
    14,
    14
  );
  const connectorMaterial = new THREE.MeshStandardMaterial({
    color: 0xdf7b36,
    roughness: 0.44,
    metalness: 0.2,
    emissive: valid ? 0x173a23 : 0x4f1711,
    emissiveIntensity: valid ? 0.08 : 0.15,
  });
  for (const point of connectorPoints) {
    const node = new THREE.Mesh(connectorGeometry, connectorMaterial);
    node.position.set(point.x, point.y, point.z);
    shelfGroup.add(node);
  }

  const openingBottom = Math.max(0.04, spec.layerHeight * 0.08);
  const openingTop = clamp(
    openingBottom + spec.openingHeight,
    openingBottom,
    totalHeight - 0.02
  );
  const halfOpening = spec.openingWidth / 2;
  const openingZ = spec.depth / 2 + 0.07;

  const openingPoints = [
    new THREE.Vector3(-halfOpening, openingBottom, openingZ),
    new THREE.Vector3(halfOpening, openingBottom, openingZ),
    new THREE.Vector3(halfOpening, openingTop, openingZ),
    new THREE.Vector3(-halfOpening, openingTop, openingZ),
    new THREE.Vector3(-halfOpening, openingBottom, openingZ),
  ];
  const openingLine = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints(openingPoints),
    new THREE.LineBasicMaterial({ color: 0x2c6a87 })
  );
  shelfGroup.add(openingLine);

  refitCamera(spec.width, totalHeight, spec.depth);
}

function highlightSelected() {
  const rows = comboList.querySelectorAll(".combo-item");
  rows.forEach((row) => {
    row.classList.toggle("active", row.dataset.comboId === selectedComboId);
  });
}

function selectCombo(comboId) {
  if (!generatedContext) {
    return;
  }

  const combo = generatedResults.find((item) => item.id === comboId);
  if (!combo) {
    return;
  }

  selectedComboId = comboId;
  highlightSelected();

  comboTitle.textContent = `当前组合：${combo.label}`;
  setStatus(combo.valid);
  setReasons(combo.errors);
  setMetrics(generatedContext, combo);
  drawShelf(generatedContext.boundary, combo.render_counts, combo.valid);
}

function showError(message) {
  resultSummary.textContent = `生成失败：${message}`;
  comboList.innerHTML =
    '<li class="combo-item"><p class="combo-title">接口调用失败，请检查后端服务是否启动</p></li>';
  comboTitle.textContent = "未选择组合";
  statusPill.classList.remove("status-ok");
  statusPill.classList.add("status-bad");
  statusPill.textContent = "无法生成";
  reasonsList.innerHTML = `<li>${message}</li>`;
  metricsBox.innerHTML = "";
  clearGroup(shelfGroup);
}

async function generateAndRender() {
  setLoading(true);
  try {
    const payload = buildRequestPayload();
    const context = await requestGeneration(payload);

    generatedContext = context;
    generatedResults = context.combinations;

    updateSummary(context);
    renderComboList(generatedResults);

    const firstChoice =
      generatedResults.find((item) => item.valid) || generatedResults[0];
    if (firstChoice) {
      selectCombo(firstChoice.id);
    } else {
      showError("未返回任何组合结果");
    }
  } catch (error) {
    const message =
      error instanceof Error
        ? error.message
        : "未知错误，请检查网络和后端服务";
    showError(message);
  } finally {
    setLoading(false);
  }
}

function resizeRenderer() {
  const width = Math.max(1, viewport.clientWidth);
  const height = Math.max(1, viewport.clientHeight);
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await generateAndRender();
});

comboList.addEventListener("click", (event) => {
  const node = event.target.closest(".combo-item");
  if (!node || !node.dataset.comboId) {
    return;
  }
  selectCombo(node.dataset.comboId);
});

form.querySelectorAll(".param-enable").forEach((checkbox) => {
  checkbox.addEventListener("change", refreshBoundaryEnableState);
});

resetButton.addEventListener("click", async () => {
  applyDefaults();
  refreshBoundaryEnableState();
  await generateAndRender();
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

applyDefaults();
refreshBoundaryEnableState();
resizeRenderer();
generateAndRender();
animate();
