import * as THREE from "./vendor/three/build/three.module.js";
import { OrbitControls } from "./vendor/three/examples/jsm/controls/OrbitControls.js";

const COMBINATIONS_URL = "../../artifacts/combinations.json";
const SUMMARY_URL = "../../artifacts/summary.json";

const state = {
  baseCombinations: [],
  baseSummary: null,
  combinations: [],
  summary: null,
  filtered: [],
  activeIndex: 0,
  autoSpin: false,
  activePage: "page-overview",
  searchKeyword: "",
  passFilter: "all",
  ruleConfig: {
    useR1: true,
    useR2: true,
    useR3: true,
    useR4: true,
    useR5: true,
    useR6: true,
    maxModules: 8,
  },
  enumerationRuns: 0,
};

const I18N = {
  family: {
    linear_bay: "线性层架",
    staggered_bay: "交错层架",
    stepped_tower: "阶梯塔架",
    cantilever_spine: "悬臂脊柱",
    portal_frame: "门式框架",
    honeycomb_cells: "蜂窝单元",
    bridge_twin: "双塔桥连",
    spine_wing: "脊柱翼展",
    zigzag_flow: "Z 字导流",
    hybrid_zone: "混合分区",
    combo_m1_m2_m3: "M1+M2+M3",
    combo_m2_m3: "M2+M3",
    combo_m1_m2: "M1+M2",
  },
  description: {
    "Balanced multi-bay frame with even load paths and full shelves.": "多跨均衡框架，承力路径均匀，层板完整。",
    "Alternating shelf depths to improve reachability and dynamic visual rhythm.": "层深交替变化，提升可达性与动态节奏。",
    "Tiered height zoning for mixed access frequencies.": "阶梯式高度分区，适配不同取用频率。",
    "Backbone-supported cantilevered layers for open front access.": "由主脊支撑的悬臂层，前向取用更开放。",
    "Strong structural arches with minimal storage surfaces.": "结构强但储物面较少的门式骨架。",
    "Cellular matrix optimized for modular compartmentalization.": "面向模块化分仓的蜂窝矩阵结构。",
    "Two towers linked by bridge decks for cross-zone access.": "双塔以桥板连接，支持跨区存取。",
    "Central spine with bilateral wing shelves for expanded lateral capacity.": "中央脊柱 + 双侧翼板，扩展横向容量。",
    "Diagonal flow layout prioritizing visual movement over stability.": "以对角流线为主的布局，强调形态流动。",
    "Combined compact and open sections for differentiated storage classes.": "紧凑区与开放区组合，适配不同存储类型。",
  },
  reason: {
    "module combination violates R1/R2 rules": "模块组合不满足 R1/R2 规则",
    "module combination violates parsed combination rules": "模块组合不满足组合规则",
    "module combination violates R1: module graph is disconnected": "组合原则 R1 不满足：模块图不连通",
    "module combination violates R2: connector module is required": "组合原则 R2 不满足：必须包含连接接口模块",
    "module combination violates R3: rod must connect through connector nodes": "组合原则 R3 不满足：杆必须通过连接接口连接",
    "module combination violates R3: panel must connect through connector nodes": "组合原则 R3 不满足：隔板必须通过连接接口连接",
    "module combination violates R4: connector must connect at least two modules": "组合原则 R4 不满足：连接接口至少连接两个模块",
    "module combination violates R5: panel must be horizontal": "组合原则 R5 不满足：隔板必须水平放置",
    "module combination violates R6: rod must be vertical": "组合原则 R6 不满足：杆必须垂直放置",
    "no panel surface, storage objective cannot be achieved": "没有层板承载面，无法满足储物目标",
    "goal score does not exceed baseline": "目标分数未超过基线",
    "target efficiency does not exceed baseline efficiency": "目标效率未超过基线效率",
    "open-style goal not satisfied": "目标验证失败：不满足开放式要求",
    "connector isolation: connector nodes must connect both rod and panel": "连接点存在孤立：连接接口必须同时连接杆与隔板",
    "footprint area exceeds boundary A": "占地投影边界面积超出边界 A",
    "stability index below 0.55": "稳定性指数低于 0.55",
    "accessibility index below 0.75": "可达性指数低于 0.75",
    "boundary A is not concretely specified in standard; boundary stage is pass-through": "标准未给出边界 A 的具体数值，边界验证阶段按通过处理",
  },
};

const VALIDATION_STAGE_LABEL = {
  combination: "组合原则验证",
  boundary: "边界验证",
  goal: "目标验证",
};

function tFamily(id, fallback = "") {
  return I18N.family[id] || fallback || id;
}

function tDescription(text) {
  return I18N.description[text] || text;
}

function tReason(text) {
  if (text.startsWith("module count exceeds limit")) return "模块总数超过配置上限";
  return I18N.reason[text] || text;
}

function detectFailureStages(item) {
  if (item.validation?.failed_stage) {
    return [item.validation.failed_stage];
  }
  const reasons = item.validation?.reasons || [];
  const stages = new Set();

  for (const reason of reasons) {
    if (
      reason.includes("module combination violates")
      || reason.includes("panel count exceeds")
      || reason.includes("rod count exceeds")
      || reason.includes("connector isolation")
    ) {
      stages.add("combination");
      continue;
    }
    if (reason.includes("boundary") || reason.includes("footprint")) {
      stages.add("boundary");
      continue;
    }
    if (
      reason.includes("target efficiency")
      || reason.includes("no panel surface")
      || reason.includes("open")
    ) {
      stages.add("goal");
    }
  }

  if (!stages.size && item.validation?.passed === false) {
    if (item.validation.combination_valid === false) stages.add("combination");
    else if (item.validation.goal_passed === false) stages.add("goal");
  }

  return [...stages];
}

function buildNodeMap(graph) {
  const map = new Map();
  for (const node of graph.nodes || []) {
    map.set(node.id, node.position);
  }
  return map;
}

function parsePositiveIntOrNull(value) {
  const raw = String(value ?? "").trim();
  if (!raw) return null;
  const num = Number(raw);
  if (!Number.isFinite(num) || num < 0) return null;
  return Math.floor(num);
}

function readRuleConfigFromUI() {
  return {
    useR1: document.getElementById("ruleR1")?.checked ?? true,
    useR2: document.getElementById("ruleR2")?.checked ?? true,
    useR3: document.getElementById("ruleR3")?.checked ?? true,
    useR4: document.getElementById("ruleR4")?.checked ?? true,
    useR5: document.getElementById("ruleR5")?.checked ?? true,
    useR6: document.getElementById("ruleR6")?.checked ?? true,
    maxModules: parsePositiveIntOrNull(document.getElementById("maxModuleInput")?.value),
  };
}

function round3(value) {
  return Number(Number(value).toFixed(3));
}

function forEachCombination(items, pickCount, onPick, start = 0, picked = []) {
  if (pickCount === 0) {
    onPick([...picked]);
    return;
  }
  if (start >= items.length) return;
  for (let i = start; i <= items.length - pickCount; i += 1) {
    picked.push(items[i]);
    forEachCombination(items, pickCount - 1, onPick, i + 1, picked);
    picked.pop();
  }
}

function connectorPositionByIndex(index, total) {
  const ringWidth = Math.max(2, Math.ceil(Math.sqrt(total)));
  const x = (index % ringWidth) * 0.9;
  const z = Math.floor(index / ringWidth) * 0.72;
  const y = ((index % 2) * 0.42) + 0.36;
  return [round3(x), round3(y), round3(z)];
}

function materializeTopologicalGraph(connectorCount, rodPairs, panelSupports) {
  const connectorIds = [...Array(connectorCount)].map((_, idx) => `N${String(idx).padStart(3, "0")}`);
  const idByIndex = new Map(connectorIds.map((id, idx) => [idx, id]));
  const nodes = connectorIds.map((id, idx) => ({
    id,
    position: connectorPositionByIndex(idx, connectorCount),
  }));

  const rods = rodPairs.map((pair) => ({
    from: idByIndex.get(pair[0]),
    to: idByIndex.get(pair[1]),
    role: "support",
    orientation: "vertical",
  }));

  const panels = panelSupports.map((supports, idx) => {
    const supportIds = [...new Set(supports.map((support) => idByIndex.get(support)))];
    const supportNodes = supportIds.map((id) => nodes.find((node) => node.id === id)).filter(Boolean);
    const xs = supportNodes.map((node) => node.position[0]);
    const ys = supportNodes.map((node) => node.position[1]);
    const zs = supportNodes.map((node) => node.position[2]);
    const minX = xs.length ? Math.min(...xs) : 0;
    const maxX = xs.length ? Math.max(...xs) : 1;
    const minZ = zs.length ? Math.min(...zs) : 0;
    const maxZ = zs.length ? Math.max(...zs) : 0.6;
    const centerX = round3((minX + maxX) * 0.5);
    const centerY = round3((ys.length ? (ys.reduce((a, b) => a + b, 0) / ys.length) : 0.36) - 0.03);
    const centerZ = round3((minZ + maxZ) * 0.5);
    const sizeX = round3(Math.max(0.45, (maxX - minX) + 0.42));
    const sizeZ = round3(Math.max(0.32, (maxZ - minZ) + 0.3));

    return {
      id: `P${String(idx).padStart(3, "0")}`,
      center: [centerX, centerY, centerZ],
      size: [sizeX, 0.05, sizeZ],
      supports: supportIds.sort(),
      role: "storage_surface",
      orientation: "horizontal",
    };
  });

  return { nodes, rods, panels };
}

function allConnectorPairs(connectorCount) {
  const pairs = [];
  for (let i = 0; i < connectorCount; i += 1) {
    for (let j = i + 1; j < connectorCount; j += 1) {
      pairs.push([i, j]);
    }
  }
  return pairs;
}

function allPanelSupportSets(connectorCount) {
  const indices = [...Array(connectorCount).keys()];
  const sets = [];
  for (let size = 2; size <= connectorCount; size += 1) {
    forEachCombination(indices, size, (picked) => {
      sets.push([...picked]);
    });
  }
  return sets;
}

function hashText(text) {
  let hash = 5381;
  for (let i = 0; i < text.length; i += 1) {
    hash = ((hash << 5) + hash) + text.charCodeAt(i);
    hash >>>= 0;
  }
  return hash.toString(16).padStart(8, "0");
}

function computeTopologySignature(graph) {
  const connectorIds = (graph.nodes || []).map((node) => node.id);
  const label = new Map();
  const adj = new Map();

  connectorIds.forEach((connectorId) => {
    const id = `C:${connectorId}`;
    label.set(id, "C");
    adj.set(id, []);
  });

  (graph.rods || []).forEach((rod, idx) => {
    const rid = `R:${idx}`;
    label.set(rid, "R");
    adj.set(rid, []);
    const a = `C:${rod.from}`;
    const b = `C:${rod.to}`;
    if (adj.has(a)) {
      adj.get(rid).push(a);
      adj.get(a).push(rid);
    }
    if (adj.has(b)) {
      adj.get(rid).push(b);
      adj.get(b).push(rid);
    }
  });

  (graph.panels || []).forEach((panel, idx) => {
    const pid = `P:${idx}`;
    const supports = [...new Set(panel.supports || [])].sort();
    label.set(pid, `P${supports.length}`);
    adj.set(pid, []);
    supports.forEach((support) => {
      const cid = `C:${support}`;
      if (!adj.has(cid)) return;
      adj.get(pid).push(cid);
      adj.get(cid).push(pid);
    });
  });

  let colors = new Map(label);
  for (let round = 0; round < 4; round += 1) {
    const nextColors = new Map();
    [...colors.keys()].sort().forEach((nodeId) => {
      const neighbours = (adj.get(nodeId) || []).map((n) => colors.get(n) || "").sort();
      const payload = `${colors.get(nodeId)}|${neighbours.join("/")}`;
      nextColors.set(nodeId, hashText(payload));
    });
    colors = nextColors;
  }

  const connectorProfile = connectorIds.map((connectorId) => {
    const rodIncident = (graph.rods || []).filter((rod) => rod.from === connectorId || rod.to === connectorId).length;
    const panelIncident = (graph.panels || []).filter((panel) => (panel.supports || []).includes(connectorId)).length;
    return `${rodIncident}-${panelIncident}`;
  }).sort();

  const colorCounts = new Map();
  [...colors.values()].forEach((color) => {
    colorCounts.set(color, (colorCounts.get(color) || 0) + 1);
  });
  const colorPart = [...colorCounts.keys()].sort().map((k) => `${k}:${colorCounts.get(k)}`).join(",");
  const profilePart = connectorProfile.join(",");
  return `C${graph.nodes.length}-R${graph.rods.length}-P${graph.panels.length}-CP[${profilePart}]-WL[${colorPart}]`;
}

function convexHull(points) {
  const unique = [...new Set(points.map((p) => `${p[0]}:${p[1]}`))]
    .map((token) => token.split(":").map((v) => Number(v)))
    .sort((a, b) => (a[0] - b[0]) || (a[1] - b[1]));
  if (unique.length <= 1) return unique;

  const cross = (o, a, b) => ((a[0] - o[0]) * (b[1] - o[1])) - ((a[1] - o[1]) * (b[0] - o[0]));
  const lower = [];
  unique.forEach((p) => {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], p) <= 0) {
      lower.pop();
    }
    lower.push(p);
  });

  const upper = [];
  [...unique].reverse().forEach((p) => {
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], p) <= 0) {
      upper.pop();
    }
    upper.push(p);
  });
  return lower.slice(0, -1).concat(upper.slice(0, -1));
}

function polygonArea(points) {
  if (points.length < 3) return 0;
  let sum = 0;
  points.forEach((point, idx) => {
    const next = points[(idx + 1) % points.length];
    sum += (point[0] * next[1]) - (next[0] * point[1]);
  });
  return Math.abs(sum) * 0.5;
}

function rectangleUnionArea(rectangles) {
  if (!rectangles.length) return 0;
  const xs = [...new Set(rectangles.flatMap((r) => [r[0], r[1]]))].sort((a, b) => a - b);
  if (xs.length < 2) return 0;
  let area = 0;
  for (let i = 0; i < xs.length - 1; i += 1) {
    const left = xs[i];
    const right = xs[i + 1];
    const dx = right - left;
    if (dx <= 0) continue;

    const intervals = rectangles
      .filter((r) => r[0] < right && r[1] > left)
      .map((r) => [Math.min(r[2], r[3]), Math.max(r[2], r[3])])
      .sort((a, b) => a[0] - b[0]);
    if (!intervals.length) continue;

    const merged = [];
    intervals.forEach((interval) => {
      if (!merged.length || interval[0] > merged[merged.length - 1][1]) {
        merged.push(interval);
      } else {
        merged[merged.length - 1][1] = Math.max(merged[merged.length - 1][1], interval[1]);
      }
    });
    const covered = merged.reduce((acc, [start, end]) => acc + Math.max(0, end - start), 0);
    area += covered * dx;
  }
  return area;
}

function projectionBoundaryArea(graph) {
  const points = [];
  (graph.nodes || []).forEach((node) => {
    points.push([Number(node.position[0]), Number(node.position[2])]);
  });

  const rectangles = [];
  (graph.panels || []).forEach((panel) => {
    const [cx, , cz] = panel.center;
    const [sx, , sz] = panel.size;
    const hx = Number(sx) * 0.5;
    const hz = Number(sz) * 0.5;
    points.push([Number(cx) - hx, Number(cz) - hz]);
    points.push([Number(cx) - hx, Number(cz) + hz]);
    points.push([Number(cx) + hx, Number(cz) - hz]);
    points.push([Number(cx) + hx, Number(cz) + hz]);
    rectangles.push([Number(cx) - hx, Number(cx) + hx, Number(cz) - hz, Number(cz) + hz]);
  });

  const hullArea = points.length ? polygonArea(convexHull(points)) : 0;
  const panelUnion = rectangleUnionArea(rectangles);
  return Math.max(hullArea, panelUnion, 1e-6);
}

function computeMetricsFromGraph(graph, baseline) {
  const nodes = graph.nodes || [];
  const panels = graph.panels || [];
  const xs = nodes.map((n) => Number(n.position[0]));
  const ys = nodes.map((n) => Number(n.position[1]));
  const zs = nodes.map((n) => Number(n.position[2]));
  const spanX = xs.length ? Math.max(...xs) - Math.min(...xs) : 0;
  const spanY = ys.length ? Math.max(...ys) - Math.min(...ys) : 0;
  const spanZ = zs.length ? Math.max(...zs) - Math.min(...zs) : 0;
  const footprint = projectionBoundaryArea(graph);
  const panelSum = panels.reduce((acc, panel) => acc + (Number(panel.size[0]) * Number(panel.size[2])), 0);
  const targetEfficiency = panelSum / footprint;
  return {
    span_x: round3(spanX),
    span_y: round3(spanY),
    span_z: round3(spanZ),
    footprint_area: round3(footprint),
    footprint_projection_boundary_area: round3(footprint),
    storage_surface: round3(panelSum),
    panel_projection_area_sum: round3(panelSum),
    storage_efficiency: round3(targetEfficiency),
    target_efficiency: round3(targetEfficiency),
    goal_score: round3(targetEfficiency),
    baseline_score: round3(baseline),
    baseline_efficiency: round3(baseline),
    improvement_ratio: baseline > 0 ? round3(targetEfficiency / baseline) : 0,
  };
}

function isRodVertical(rod, nodeMap) {
  const a = nodeMap.get(rod.from);
  const b = nodeMap.get(rod.to);
  if (!a || !b) return false;
  const sameX = Math.abs(a[0] - b[0]) <= 1e-6;
  const sameZ = Math.abs(a[2] - b[2]) <= 1e-6;
  const diffY = Math.abs(a[1] - b[1]) > 1e-6;
  return sameX && sameZ && diffY;
}

function isPanelHorizontal(panel, nodeMap) {
  const supports = panel.supports || [];
  if (!supports.length) return false;
  const yValues = new Set();
  for (const support of supports) {
    const pos = nodeMap.get(support);
    if (!pos) return false;
    yValues.add(Number(pos[1]).toFixed(6));
  }
  return yValues.size === 1;
}

function isModuleGraphConnected(graph) {
  const connectorIds = (graph.nodes || []).map((node) => node.id);
  const rods = graph.rods || [];
  const panels = graph.panels || [];

  const moduleNodes = [];
  connectorIds.forEach((id) => moduleNodes.push(`C:${id}`));
  rods.forEach((_, idx) => moduleNodes.push(`R:${idx}`));
  panels.forEach((_, idx) => moduleNodes.push(`P:${idx}`));

  if (!moduleNodes.length) return false;

  const adj = new Map(moduleNodes.map((id) => [id, new Set()]));
  rods.forEach((rod, idx) => {
    const rid = `R:${idx}`;
    const ca = `C:${rod.from}`;
    const cb = `C:${rod.to}`;
    if (adj.has(ca)) {
      adj.get(rid).add(ca);
      adj.get(ca).add(rid);
    }
    if (adj.has(cb)) {
      adj.get(rid).add(cb);
      adj.get(cb).add(rid);
    }
  });
  panels.forEach((panel, idx) => {
    const pid = `P:${idx}`;
    for (const support of panel.supports || []) {
      const cid = `C:${support}`;
      if (!adj.has(cid)) continue;
      adj.get(pid).add(cid);
      adj.get(cid).add(pid);
    }
  });

  const stack = [moduleNodes[0]];
  const visited = new Set();
  while (stack.length) {
    const current = stack.pop();
    if (visited.has(current)) continue;
    visited.add(current);
    for (const next of adj.get(current) || []) {
      if (!visited.has(next)) stack.push(next);
    }
  }

  return visited.size === moduleNodes.length;
}

function validateCombinationByConfig(item, config) {
  const graph = item.graph;
  const reasons = [];

  const moduleCount = (graph.nodes || []).length + (graph.rods || []).length + (graph.panels || []).length;
  if (config.maxModules !== null && moduleCount > config.maxModules) {
    reasons.push(`module count exceeds limit: ${moduleCount} > ${config.maxModules}`);
  }

  if (config.useR2 && (!graph.nodes || graph.nodes.length === 0)) {
    reasons.push("module combination violates R2: connector module is required");
  }

  if (config.useR3) {
    const nodeMap = buildNodeMap(graph);
    for (const rod of graph.rods || []) {
      if (!nodeMap.has(rod.from) || !nodeMap.has(rod.to)) {
        reasons.push("module combination violates R3: rod must connect through connector nodes");
        break;
      }
    }
    if (!reasons.some((text) => text.includes("R3"))) {
      for (const panel of graph.panels || []) {
        const supports = panel.supports || [];
        if (!supports.length || supports.some((id) => !nodeMap.has(id))) {
          reasons.push("module combination violates R3: panel must connect through connector nodes");
          break;
        }
      }
    }
  }

  if (config.useR4) {
    const counts = new Map();
    for (const node of graph.nodes || []) counts.set(node.id, 0);
    for (const rod of graph.rods || []) {
      if (counts.has(rod.from)) counts.set(rod.from, counts.get(rod.from) + 1);
      if (counts.has(rod.to)) counts.set(rod.to, counts.get(rod.to) + 1);
    }
    for (const panel of graph.panels || []) {
      for (const support of panel.supports || []) {
        if (counts.has(support)) counts.set(support, counts.get(support) + 1);
      }
    }
    const hasWeakConnector = [...counts.values()].some((count) => count < 2);
    if (hasWeakConnector) {
      reasons.push("module combination violates R4: connector must connect at least two modules");
    }
  }

  if (config.useR5) {
    for (const panel of graph.panels || []) {
      if ((panel.orientation || "horizontal") !== "horizontal") {
        reasons.push("module combination violates R5: panel must be horizontal");
        break;
      }
    }
  }

  if (config.useR6) {
    for (const rod of graph.rods || []) {
      if ((rod.orientation || "vertical") !== "vertical") {
        reasons.push("module combination violates R6: rod must be vertical");
        break;
      }
    }
  }

  if (config.useR1 && !isModuleGraphConnected(graph)) {
    reasons.push("module combination violates R1: module graph is disconnected");
  }

  return {
    pass: reasons.length === 0,
    reasons,
  };
}

function evaluateByThreeStages(item, config, summary) {
  const baseline = Number(summary?.standard_profile?.baseline_efficiency ?? summary?.baseline_score ?? 1);
  const boundaryLimit = summary?.standard_profile?.boundary_limit_a;
  const reasons = [];
  const warnings = [];

  const combination = validateCombinationByConfig(item, config);
  if (!combination.pass) {
    return {
      combination_valid: false,
      boundary_valid: null,
      goal_passed: null,
      open_style_valid: null,
      efficiency_valid: null,
      passed: false,
      failed_stage: "combination",
      reasons: combination.reasons,
      warnings,
    };
  }

  const footprint = Number(item.metrics.footprint_projection_boundary_area ?? item.metrics.footprint_area ?? 0);
  let boundaryValid = true;
  if (typeof boundaryLimit === "number" && Number.isFinite(boundaryLimit)) {
    if (footprint > boundaryLimit) {
      boundaryValid = false;
      reasons.push("footprint area exceeds boundary A");
    }
  } else {
    warnings.push("boundary A is not concretely specified in standard; boundary stage is pass-through");
  }
  if (!boundaryValid) {
    return {
      combination_valid: true,
      boundary_valid: false,
      goal_passed: null,
      open_style_valid: null,
      efficiency_valid: null,
      passed: false,
      failed_stage: "boundary",
      reasons,
      warnings,
    };
  }

  const targetEfficiency = Number(item.metrics.target_efficiency ?? item.metrics.goal_score ?? 0);
  const openStyleValid = true;
  const efficiencyValid = targetEfficiency > baseline;
  if (!openStyleValid) reasons.push("open-style goal not satisfied");
  if (!efficiencyValid) reasons.push("target efficiency does not exceed baseline efficiency");

  if (reasons.length) {
    return {
      combination_valid: true,
      boundary_valid: true,
      goal_passed: false,
      open_style_valid: openStyleValid,
      efficiency_valid: efficiencyValid,
      passed: false,
      failed_stage: "goal",
      reasons,
      warnings,
    };
  }

  return {
    combination_valid: true,
    boundary_valid: true,
    goal_passed: true,
    open_style_valid: true,
    efficiency_valid: true,
    passed: true,
    failed_stage: null,
    reasons: [],
    warnings,
  };
}

function buildRuntimeSummary(items, referenceSummary, ruleConfig, meta = {}) {
  const total = items.length;
  const passed = items.filter((item) => item.validation?.passed).length;
  const failed = total - passed;
  const scores = items.map((item) => Number(item.metrics.goal_score ?? item.metrics.target_efficiency ?? 0));
  const scoreMin = scores.length ? Math.min(...scores) : 0;
  const scoreMax = scores.length ? Math.max(...scores) : 0;
  const scoreAvg = scores.length ? scores.reduce((acc, value) => acc + value, 0) / scores.length : 0;

  const bins = 8;
  const width = scoreMax > scoreMin ? (scoreMax - scoreMin) / bins : 1;
  const scoreDistribution = [];
  for (let idx = 0; idx < bins; idx += 1) {
    const lower = scoreMax > scoreMin ? scoreMin + idx * width : scoreMin + idx;
    const upper = scoreMax > scoreMin ? lower + width : lower + 1;
    const countInBin = scores.filter((score) => (
      score >= lower && (score < upper || (idx === bins - 1 && score <= upper))
    )).length;
    scoreDistribution.push({
      bin: idx + 1,
      range: [Number(lower.toFixed(3)), Number(upper.toFixed(3))],
      count: countInBin,
    });
  }

  const familyMap = new Map();
  for (const item of items) {
    const key = item.family;
    if (!familyMap.has(key)) {
      familyMap.set(key, {
        family: item.family,
        label: item.family_label,
        count: 0,
        passed: 0,
        failed: 0,
        scoreSum: 0,
      });
    }
    const record = familyMap.get(key);
    record.count += 1;
    record.scoreSum += Number(item.metrics.goal_score ?? item.metrics.target_efficiency ?? 0);
    if (item.validation?.passed) record.passed += 1;
    else record.failed += 1;
  }

  const families = [...familyMap.values()].map((record) => ({
    family: record.family,
    label: record.label,
    count: record.count,
    passed: record.passed,
    failed: record.failed,
    pass_rate: Number((record.passed / Math.max(1, record.count)).toFixed(3)),
    avg_score: Number((record.scoreSum / Math.max(1, record.count)).toFixed(3)),
  }));

  return {
    ...referenceSummary,
    raw_candidates: meta.rawCandidates ?? referenceSummary.raw_candidates ?? total,
    generation_strategy: meta.generationStrategy ?? referenceSummary.generation_strategy ?? "rule_driven_enumeration",
    total_combinations: total,
    passed,
    failed,
    pass_rate: Number((passed / Math.max(1, total)).toFixed(3)),
    score_min: Number(scoreMin.toFixed(3)),
    score_max: Number(scoreMax.toFixed(3)),
    score_avg: Number(scoreAvg.toFixed(3)),
    score_distribution: scoreDistribution,
    families,
    active_rule_config: { ...ruleConfig },
  };
}

function runConfiguredCombination() {
  state.ruleConfig = readRuleConfigFromUI();
  state.enumerationRuns += 1;
  if (state.ruleConfig.maxModules === null || state.ruleConfig.maxModules <= 0) {
    state.combinations = [];
    state.summary = buildRuntimeSummary([], state.baseSummary || state.summary, state.ruleConfig, {
      rawCandidates: 0,
      generationStrategy: "rule_driven_enumeration",
    });
    state.summary.enumeration_elapsed_ms = 0;
    state.summary.enumeration_run_id = state.enumerationRuns;
    document.getElementById("listHint").textContent = "请先填写最大模块总数，再点击按配置组合。";
    renderGlobalStats(state.summary);
    renderOverviewHighlights(state.summary);
    updateDonut(state.summary);
    drawHistogram(state.summary);
    drawFamilyBars(state.summary);
    applyFilters(true);
    return;
  }

  const baseline = Number(state.baseSummary?.standard_profile?.baseline_efficiency ?? state.baseSummary?.baseline_score ?? 1);
  const representatives = new Map();
  let rawCandidates = 0;
  const t0 = performance.now();
  const maxModules = state.ruleConfig.maxModules;

  for (let connectorCount = 1; connectorCount <= maxModules; connectorCount += 1) {
    const remainingAfterConnector = maxModules - connectorCount;
    const pairCandidates = allConnectorPairs(connectorCount);
    const panelSupportCandidates = allPanelSupportSets(connectorCount);

    for (let rodCount = 0; rodCount <= remainingAfterConnector; rodCount += 1) {
      if (rodCount > pairCandidates.length) break;
      const remainingAfterRod = remainingAfterConnector - rodCount;

      for (let panelCount = 0; panelCount <= remainingAfterRod; panelCount += 1) {
        if (panelCount > panelSupportCandidates.length) break;

        // R4 lower bound prune: each connector must have at least 2 incidences.
        // Rod contributes 2 incidences; panel contributes at least 2 incidences.
        if (state.ruleConfig.useR4 && (rodCount + panelCount < connectorCount)) continue;

        forEachCombination(pairCandidates, rodCount, (rodPairs) => {
          const rodIncidence = Array(connectorCount).fill(0);
          rodPairs.forEach((pair) => {
            rodIncidence[pair[0]] += 1;
            rodIncidence[pair[1]] += 1;
          });

          forEachCombination(panelSupportCandidates, panelCount, (panelSupports) => {
            const totalModules = connectorCount + rodCount + panelCount;
            if (totalModules > maxModules) return;

            const panelIncidence = Array(connectorCount).fill(0);
            panelSupports.forEach((supports) => {
              supports.forEach((connectorIdx) => {
                panelIncidence[connectorIdx] += 1;
              });
            });

            if (state.ruleConfig.useR4) {
              for (let idx = 0; idx < connectorCount; idx += 1) {
                if ((rodIncidence[idx] + panelIncidence[idx]) < 2) return;
              }
            }

            const graph = materializeTopologicalGraph(connectorCount, rodPairs, panelSupports);
            const comboCheck = validateCombinationByConfig({ graph }, state.ruleConfig);
            if (!comboCheck.pass) return;

            rawCandidates += 1;
            const signature = computeTopologySignature(graph);
            if (!representatives.has(signature)) {
              representatives.set(signature, graph);
            }
          });
        });
      }
    }
  }

  const evaluated = [...representatives.keys()].sort().map((signature, idx) => {
    const graph = representatives.get(signature);
    const panelCountLocal = (graph.panels || []).length;
    const rodCountLocal = (graph.rods || []).length;
    const connectorCountLocal = (graph.nodes || []).length;
    const family = `p${panelCountLocal}_r${rodCountLocal}_c${connectorCountLocal}`;
    const familyLabel = `隔板${panelCountLocal}-杆${rodCountLocal}-连接接口${connectorCountLocal}`;
    const modules = [];
    if (connectorCountLocal > 0) modules.push("connector");
    if (panelCountLocal > 0) modules.push("panel");
    if (rodCountLocal > 0) modules.push("rod");
    const metrics = computeMetricsFromGraph(graph, baseline);
    const item = {
      id: `SHELF-${String(idx + 1).padStart(4, "0")}`,
      family,
      family_label: familyLabel,
      description: `拓扑代表结构：${familyLabel}`,
      variant: idx + 1,
      topology_signature: signature,
      modules: modules.sort(),
      graph,
      metrics,
    };
    return {
      ...item,
      validation: evaluateByThreeStages(item, state.ruleConfig, state.baseSummary || state.summary),
    };
  });

  state.combinations = evaluated;
  state.summary = buildRuntimeSummary(evaluated, state.baseSummary || state.summary, state.ruleConfig, {
    rawCandidates,
    generationStrategy: "rule_driven_enumeration",
  });
  const elapsedMs = Math.round(performance.now() - t0);
  state.summary.enumeration_elapsed_ms = elapsedMs;
  state.summary.enumeration_run_id = state.enumerationRuns;
  state.searchKeyword = "";
  const searchInput = document.getElementById("searchInput");
  if (searchInput) searchInput.value = "";
  renderGlobalStats(state.summary);
  renderOverviewHighlights(state.summary);
  updateDonut(state.summary);
  drawHistogram(state.summary);
  drawFamilyBars(state.summary);
  const histogramSubtitle = document.getElementById("histogramSubtitle");
  if (histogramSubtitle) {
    histogramSubtitle.textContent = `${state.summary.total_combinations} 种分型的目标分数区间分布`;
  }
  applyFilters(true);
}

class ShelfViewer {
  constructor(container) {
    this.container = container;
    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.Fog(0xf4f2eb, 8, 23);

    this.camera = new THREE.PerspectiveCamera(48, 1, 0.01, 120);
    this.camera.position.set(4.8, 4, 5.4);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.08;
    container.appendChild(this.renderer.domElement);

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.06;
    this.controls.maxDistance = 20;
    this.controls.minDistance = 1.3;
    this.controls.target.set(1, 1, 0.3);

    this.root = new THREE.Group();
    this.scene.add(this.root);

    this.rodUnit = new THREE.CylinderGeometry(1, 1, 1, 10);
    this.connectorGeometry = new THREE.IcosahedronGeometry(0.048, 1);

    this.materials = {
      rod: new THREE.MeshStandardMaterial({ color: 0x2f5f74, roughness: 0.26, metalness: 0.1 }),
      brace: new THREE.MeshStandardMaterial({ color: 0x206c60, roughness: 0.25, metalness: 0.08 }),
      panel: new THREE.MeshStandardMaterial({ color: 0xe9be6c, roughness: 0.42, metalness: 0.03 }),
      connector: new THREE.MeshStandardMaterial({ color: 0x14384a, roughness: 0.2, metalness: 0.35 }),
      panelWire: new THREE.LineBasicMaterial({ color: 0x7f673f, transparent: true, opacity: 0.5 }),
    };

    this.scene.add(new THREE.AmbientLight(0xffffff, 0.42));

    const hemi = new THREE.HemisphereLight(0xe5f6f5, 0xd9c190, 0.95);
    hemi.position.set(0, 12, 0);
    this.scene.add(hemi);

    const key = new THREE.DirectionalLight(0xffffff, 1.15);
    key.position.set(4.2, 8.6, 5.7);
    this.scene.add(key);

    const fill = new THREE.DirectionalLight(0xb8def1, 0.45);
    fill.position.set(-4, 4, -2);
    this.scene.add(fill);

    const floor = new THREE.Mesh(
      new THREE.CircleGeometry(10, 80),
      new THREE.MeshStandardMaterial({
        color: 0xeff4f1,
        transparent: true,
        opacity: 0.9,
        roughness: 0.95,
        metalness: 0,
      })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.02;
    this.scene.add(floor);

    this.autoSpin = false;
    this.clock = new THREE.Clock();
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);
    this.resize();
    this.animate();
  }

  setAutoSpin(on) {
    this.autoSpin = Boolean(on);
  }

  clearRoot() {
    while (this.root.children.length) {
      const child = this.root.children[0];
      this.root.remove(child);
      if (child.geometry) child.geometry.dispose();
      if (child.material && child.material.dispose) child.material.dispose();
    }
  }

  addRod(start, end, role = "support") {
    const a = new THREE.Vector3(start[0], start[1], start[2]);
    const b = new THREE.Vector3(end[0], end[1], end[2]);
    const delta = new THREE.Vector3().subVectors(b, a);
    const length = delta.length();
    if (length <= 1e-4) return;

    const radiusByRole = {
      vertical: 0.028,
      bridge: 0.027,
      brace: 0.021,
      cantilever: 0.024,
      diag: 0.02,
      support: 0.024,
    };
    const radius = radiusByRole[role] || 0.023;

    const material = role === "brace" || role === "diag" ? this.materials.brace : this.materials.rod;
    const rod = new THREE.Mesh(this.rodUnit.clone(), material.clone());
    rod.scale.set(radius, length, radius);
    rod.position.copy(a).add(b).multiplyScalar(0.5);
    rod.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), delta.normalize());
    rod.castShadow = false;
    rod.receiveShadow = true;
    this.root.add(rod);
  }

  addPanel(center, size) {
    const geometry = new THREE.BoxGeometry(size[0], size[1], size[2]);
    const panel = new THREE.Mesh(geometry, this.materials.panel.clone());
    panel.position.set(center[0], center[1], center[2]);
    panel.castShadow = false;
    panel.receiveShadow = true;

    const edge = new THREE.LineSegments(new THREE.EdgesGeometry(geometry), this.materials.panelWire.clone());
    edge.position.copy(panel.position);
    this.root.add(panel);
    this.root.add(edge);
  }

  addConnector(pos) {
    const connector = new THREE.Mesh(this.connectorGeometry.clone(), this.materials.connector.clone());
    connector.position.set(pos[0], pos[1], pos[2]);
    this.root.add(connector);
  }

  frameRoot() {
    const box = new THREE.Box3().setFromObject(this.root);
    if (box.isEmpty()) return;

    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);

    const maxDim = Math.max(size.x, size.y, size.z, 1.2);
    const distance = maxDim * 1.6;
    const direction = new THREE.Vector3(1.4, 0.95, 1.25).normalize();
    this.camera.position.copy(center).add(direction.multiplyScalar(distance));
    this.controls.target.copy(center);
    this.controls.update();
  }

  renderCombination(item) {
    this.clearRoot();
    const nodeMap = {};
    for (const node of item.graph.nodes) {
      nodeMap[node.id] = node.position;
      this.addConnector(node.position);
    }

    for (const rod of item.graph.rods) {
      const start = nodeMap[rod.from];
      const end = nodeMap[rod.to];
      if (!start || !end) continue;
      this.addRod(start, end, rod.role);
    }

    for (const panel of item.graph.panels) {
      this.addPanel(panel.center, panel.size);
    }

    this.frameRoot();
  }

  resize() {
    const width = this.container.clientWidth || 1;
    const height = this.container.clientHeight || 1;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    const delta = this.clock.getDelta();
    if (this.autoSpin) {
      this.root.rotation.y += delta * 0.34;
    }
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}

function fmt(value, digits = 3) {
  return Number(value).toFixed(digits);
}

function createElement(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}

function renderGlobalStats(summary) {
  const stats = document.getElementById("globalStats");
  stats.innerHTML = "";
  const items = [
    ["总组合数", summary.total_combinations],
    ["穷举批次", summary.enumeration_run_id ?? 0],
    ["规则候选", summary.raw_candidates ?? "-"],
    ["通过率", `${fmt((summary.pass_rate || 0) * 100, 1)}%`],
    ["均值效率", fmt(summary.score_avg ?? 0, 3)],
    ["穷举耗时", `${summary.enumeration_elapsed_ms ?? 0} ms`],
  ];

  for (const [label, value] of items) {
    const chip = createElement("article", "stat-chip");
    chip.appendChild(createElement("span", "", label));
    chip.appendChild(createElement("strong", "", String(value)));
    stats.appendChild(chip);
  }
}

function renderOverviewHighlights(summary) {
  const target = document.getElementById("overviewHighlights");
  target.innerHTML = "";
  const families = [...(summary.families || [])];
  if (!families.length) return;

  const topByRate = [...families].sort((a, b) => b.pass_rate - a.pass_rate)[0];
  const topByScore = [...families].sort((a, b) => b.avg_score - a.avg_score)[0];
  const lowByRate = [...families].sort((a, b) => a.pass_rate - b.pass_rate)[0];

  const insights = [
    `通过率最高：${tFamily(topByRate.family, topByRate.label)}（${fmt(topByRate.pass_rate * 100, 0)}%）`,
    `平均效率最高：${tFamily(topByScore.family, topByScore.label)}（${fmt(topByScore.avg_score, 3)}）`,
    `当前短板：${tFamily(lowByRate.family, lowByRate.label)}（通过率 ${fmt(lowByRate.pass_rate * 100, 0)}%）`,
    `总体结论：${summary.total_combinations} 种中通过 ${summary.passed} 种，失败 ${summary.failed} 种`,
  ];

  for (const line of insights) {
    const item = createElement("article", "highlight-item");
    item.innerHTML = `<strong>•</strong> ${line}`;
    target.appendChild(item);
  }
}

function renderList() {
  const list = document.getElementById("comboList");
  list.innerHTML = "";

  if (!state.filtered.length) {
    list.appendChild(createElement("p", "", "没有匹配的组合。"));
    document.getElementById("listHint").textContent = `显示 0 / 共 ${state.combinations.length}（规则候选：${state.summary?.raw_candidates ?? 0}）`;
    return;
  }

  state.filtered.forEach((item, index) => {
    const card = createElement("article", "combo-card");
    if (index === state.activeIndex) card.classList.add("active");

    const top = createElement("div", "combo-top");
    top.appendChild(createElement("span", "combo-id", item.id));
    top.appendChild(
      createElement(
        "span",
        `badge ${item.validation.passed ? "pass" : "fail"}`,
        item.validation.passed ? "通过" : "失败"
      )
    );

    card.appendChild(top);
    card.appendChild(
      createElement("div", "combo-family", `${tFamily(item.family, item.family_label)} · 变体${item.variant}`)
    );

    const metrics = createElement("div", "combo-metrics");
    metrics.appendChild(
      createElement("span", "", `物品存取效率：${fmt(item.metrics.target_efficiency ?? item.metrics.goal_score, 3)}`)
    );
    metrics.appendChild(createElement("span", "", `提升：${fmt(item.metrics.improvement_ratio, 2)}x`));
    metrics.appendChild(createElement("span", "", `隔板数：${item.graph.panels.length}`));
    metrics.appendChild(createElement("span", "", `杆数：${item.graph.rods.length}`));
    metrics.appendChild(createElement("span", "", `连接接口数：${item.graph.nodes.length}`));
    metrics.appendChild(
      createElement(
        "span",
        "",
        `模块总数：${item.graph.panels.length + item.graph.rods.length + item.graph.nodes.length}`
      )
    );
    card.appendChild(metrics);

    card.addEventListener("click", () => {
      state.activeIndex = index;
      renderList();
      renderActive();
    });

    list.appendChild(card);
  });

  document.getElementById("listHint").textContent = `显示 ${state.filtered.length} / 共 ${state.combinations.length}（规则候选：${state.summary?.raw_candidates ?? 0}）`;
}

function renderActiveMetrics(item) {
  const wrap = document.getElementById("activeMetrics");
  wrap.innerHTML = "";
  const metrics = [
    ["物品存取效率", fmt(item.metrics.target_efficiency ?? item.metrics.goal_score, 3)],
    ["提升倍数", `${fmt(item.metrics.improvement_ratio, 2)}x`],
    ["隔板数", String(item.graph.panels.length)],
    ["杆数", String(item.graph.rods.length)],
    ["连接接口数", String(item.graph.nodes.length)],
    ["模块总数", String(item.graph.panels.length + item.graph.rods.length + item.graph.nodes.length)],
    ["隔板投影面积和", fmt(item.metrics.panel_projection_area_sum ?? item.metrics.storage_surface, 3)],
    ["占地投影边界面积", fmt(item.metrics.footprint_projection_boundary_area ?? item.metrics.footprint_area, 3)],
  ];

  for (const [label, value] of metrics) {
    const card = createElement("article", "metric-card");
    card.appendChild(createElement("span", "", label));
    card.appendChild(createElement("strong", "", value));
    wrap.appendChild(card);
  }
}

function renderValidation(item) {
  const target = document.getElementById("validationDetails");
  target.innerHTML = "";

  if (item.validation.passed) {
    target.appendChild(
      createElement("div", "validation-item pass", "三阶段全部通过：组合原则验证、边界验证、目标验证。")
    );
  }

  if (!item.validation.reasons.length && item.validation.passed) {
    target.appendChild(
      createElement("div", "validation-item pass", "未发现失败项。")
    );
  } else {
    const stages = detectFailureStages(item);
    if (stages.length) {
      const labels = stages.map((stage) => VALIDATION_STAGE_LABEL[stage] || stage).join("、");
      target.appendChild(createElement("div", "validation-item fail", `失败阶段：${labels}`));
    }
    for (const reason of item.validation.reasons) {
      target.appendChild(createElement("div", "validation-item fail", tReason(reason)));
    }
  }

  if (item.validation.warnings && item.validation.warnings.length) {
    for (const warning of item.validation.warnings) {
      target.appendChild(createElement("div", "validation-item warn", tReason(warning)));
    }
  }
}

function renderActive() {
  const item = state.filtered[state.activeIndex];
  if (!item) {
    document.getElementById("activeTitle").textContent = "无可展示组合";
    document.getElementById("activeSubtitle").textContent = "请调整筛选条件";
    document.getElementById("activeMetrics").innerHTML = "";
    document.getElementById("validationDetails").innerHTML = "";
    return;
  }

  document.getElementById("activeTitle").textContent = `${item.id} · ${tFamily(item.family, item.family_label)}`;
  document.getElementById("activeSubtitle").textContent = tDescription(item.description);
  document.getElementById("baselineTextOverview").textContent = `基线效率：${fmt(state.summary.baseline_score, 3)}`;
  renderActiveMetrics(item);
  renderValidation(item);
  viewer.renderCombination(item);
}

function updateDonut(summary) {
  const passRate = summary.pass_rate || 0;
  const passPct = Math.max(0, Math.min(100, passRate * 100));
  const donut = document.getElementById("passDonut");
  donut.style.background = `conic-gradient(var(--pass) 0 ${passPct}%, var(--fail) ${passPct}% 100%)`;

  document.getElementById("passRateText").textContent = `${fmt(passPct, 1)}%`;
  document.getElementById("passCountText").textContent = `通过：${summary.passed}`;
  document.getElementById("failCountText").textContent = `失败：${summary.failed}`;
}

function drawHistogram(summary) {
  const svg = document.getElementById("histogram");
  svg.innerHTML = "";
  const data = summary.score_distribution || [];
  const maxCount = Math.max(1, ...data.map((d) => d.count));
  const chartW = 500;
  const chartH = 160;
  const barW = chartW / Math.max(1, data.length);

  data.forEach((bin, idx) => {
    const h = (bin.count / maxCount) * 120;
    const x = idx * barW + 10;
    const y = chartH - h - 24;

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", String(x));
    rect.setAttribute("y", String(y));
    rect.setAttribute("width", String(barW - 16));
    rect.setAttribute("height", String(h));
    rect.setAttribute("rx", "6");
    rect.setAttribute("fill", idx % 2 ? "#0f8b8d" : "#2f5f74");
    rect.setAttribute("opacity", "0.85");
    svg.appendChild(rect);

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", String(x + (barW - 16) / 2));
    label.setAttribute("y", String(chartH - 8));
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("font-size", "10");
    label.setAttribute("fill", "#435360");
    label.textContent = `${bin.range[0]}-${bin.range[1]}`;
    svg.appendChild(label);

    const countText = document.createElementNS("http://www.w3.org/2000/svg", "text");
    countText.setAttribute("x", String(x + (barW - 16) / 2));
    countText.setAttribute("y", String(y - 4));
    countText.setAttribute("text-anchor", "middle");
    countText.setAttribute("font-size", "11");
    countText.setAttribute("fill", "#1a2731");
    countText.textContent = String(bin.count);
    svg.appendChild(countText);
  });
}

function drawFamilyBars(summary) {
  const svg = document.getElementById("familyBars");
  svg.innerHTML = "";
  const families = [...(summary.families || [])].sort((a, b) => b.pass_rate - a.pass_rate);
  const lineH = 22;
  const chartW = 420;
  const left = 88;

  families.forEach((family, idx) => {
    const y = 18 + idx * lineH;
    const width = family.pass_rate * chartW;

    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", "2");
    label.setAttribute("y", String(y + 11));
    label.setAttribute("font-size", "11");
    label.setAttribute("fill", "#22303a");
    label.textContent = tFamily(family.family, family.label);
    svg.appendChild(label);

    const bg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    bg.setAttribute("x", String(left));
    bg.setAttribute("y", String(y));
    bg.setAttribute("width", String(chartW));
    bg.setAttribute("height", "14");
    bg.setAttribute("rx", "6");
    bg.setAttribute("fill", "#d7e3e2");
    svg.appendChild(bg);

    const fg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    fg.setAttribute("x", String(left));
    fg.setAttribute("y", String(y));
    fg.setAttribute("width", String(width));
    fg.setAttribute("height", "14");
    fg.setAttribute("rx", "6");
    fg.setAttribute("fill", family.pass_rate > 0.85 ? "#227c4f" : family.pass_rate > 0.5 ? "#0f8b8d" : "#cb3a31");
    svg.appendChild(fg);

    const value = document.createElementNS("http://www.w3.org/2000/svg", "text");
    value.setAttribute("x", String(left + chartW + 8));
    value.setAttribute("y", String(y + 11));
    value.setAttribute("font-size", "11");
    value.setAttribute("fill", "#22303a");
    value.textContent = `${fmt(family.pass_rate * 100, 0)}%`;
    svg.appendChild(value);
  });
}

function applyFilters(resetIndex = true) {
  const query = state.searchKeyword.trim().toLowerCase();
  state.filtered = state.combinations.filter((item) => {
    if (state.passFilter === "pass" && !item.validation.passed) return false;
    if (state.passFilter === "fail" && item.validation.passed) return false;

    if (!query) return true;
    const target = [
      item.id,
      item.family,
      item.family_label,
      item.description,
      item.modules.join(" "),
    ]
      .join(" ")
      .toLowerCase();
    return target.includes(query);
  });

  if (resetIndex || state.activeIndex >= state.filtered.length) {
    state.activeIndex = 0;
  }
  renderList();
  renderActive();
}

function setPassFilter(nextFilter) {
  state.passFilter = nextFilter;
  document.querySelectorAll(".filter-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.filter === nextFilter);
  });
  applyFilters(true);
}

function switchPage(pageId) {
  state.activePage = pageId;
  document.querySelectorAll(".page").forEach((page) => {
    page.classList.toggle("is-active", page.id === pageId);
  });

  document.querySelectorAll(".nav-btn").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === pageId);
  });

  if (pageId === "page-designs" && viewer) {
    requestAnimationFrame(() => viewer.resize());
  }
}

function bindEvents() {
  const search = document.getElementById("searchInput");
  search.addEventListener("input", (event) => {
    state.searchKeyword = event.target.value || "";
    applyFilters(true);
  });

  document.querySelectorAll(".filter-btn").forEach((button) => {
    button.addEventListener("click", () => setPassFilter(button.dataset.filter || "all"));
  });

  document.querySelectorAll(".nav-btn").forEach((button) => {
    button.addEventListener("click", () => switchPage(button.dataset.page));
  });

  const applyRuleBtn = document.getElementById("applyRuleBtn");
  if (applyRuleBtn) {
    applyRuleBtn.addEventListener("click", () => {
      runConfiguredCombination();
    });
  }

  document.getElementById("prevBtn").addEventListener("click", () => {
    if (!state.filtered.length) return;
    state.activeIndex = (state.activeIndex - 1 + state.filtered.length) % state.filtered.length;
    renderList();
    renderActive();
  });

  document.getElementById("nextBtn").addEventListener("click", () => {
    if (!state.filtered.length) return;
    state.activeIndex = (state.activeIndex + 1) % state.filtered.length;
    renderList();
    renderActive();
  });

  const spinButton = document.getElementById("autoSpinBtn");
  spinButton.addEventListener("click", () => {
    state.autoSpin = !state.autoSpin;
    viewer.setAutoSpin(state.autoSpin);
    spinButton.textContent = `自动旋转：${state.autoSpin ? "开" : "关"}`;
  });
}

async function loadData() {
  const bust = `t=${Date.now()}`;
  const [combinationsRes, summaryRes] = await Promise.all([
    fetch(`${COMBINATIONS_URL}?${bust}`, { cache: "no-store" }),
    fetch(`${SUMMARY_URL}?${bust}`, { cache: "no-store" }),
  ]);
  if (!combinationsRes.ok) throw new Error(`Cannot load ${COMBINATIONS_URL}`);
  if (!summaryRes.ok) throw new Error(`Cannot load ${SUMMARY_URL}`);

  const combinationsPayload = await combinationsRes.json();
  const summary = await summaryRes.json();
  return {
    combinations: combinationsPayload.combinations || [],
    summary,
  };
}

let viewer;

async function main() {
  const container = document.getElementById("viewerCanvas");
  viewer = new ShelfViewer(container);

  try {
    const data = await loadData();
    state.baseCombinations = data.combinations;
    state.baseSummary = data.summary;
    state.combinations = [];
    state.summary = data.summary;
    state.filtered = [];
    state.searchKeyword = "";
    state.passFilter = "all";

    bindEvents();
    setPassFilter("all");
    runConfiguredCombination();
    switchPage("page-overview");
  } catch (error) {
    console.error(error);
    document.getElementById("listHint").textContent = "加载失败";
    document.getElementById("comboList").innerHTML =
      "<p>数据加载失败。请先运行生成脚本，并使用 HTTP 服务打开页面。</p>";
  }
}

main();
