import * as THREE from "./vendor/three/build/three.module.js";
import { OrbitControls } from "./vendor/three/examples/jsm/controls/OrbitControls.js";

const refs = {
  reloadBtn: document.getElementById("reloadBtn"),
  boundaryNInput: document.getElementById("boundaryNInput"),
  boundaryGInput: document.getElementById("boundaryGInput"),
  familySelect: document.getElementById("familySelect"),
  statusSelect: document.getElementById("statusSelect"),
  limitInput: document.getElementById("limitInput"),
  offsetInput: document.getElementById("offsetInput"),
  cacheInfo: document.getElementById("cacheInfo"),
  enumerationTotal: document.getElementById("enumerationTotal"),
  generatedTotal: document.getElementById("generatedTotal"),
  goalPassed: document.getElementById("goalPassed"),
  goalFailed: document.getElementById("goalFailed"),
  filteredTotal: document.getElementById("filteredTotal"),
  computeSeconds: document.getElementById("computeSeconds"),
  ruleFailed: document.getElementById("ruleFailed"),
  boundaryFailed: document.getElementById("boundaryFailed"),
  goalPassBar: document.getElementById("goalPassBar"),
  boundaryFailBar: document.getElementById("boundaryFailBar"),
  ruleFailBar: document.getElementById("ruleFailBar"),
  goalFailBar: document.getElementById("goalFailBar"),
  goalPassRate: document.getElementById("goalPassRate"),
  boundaryFailRate: document.getElementById("boundaryFailRate"),
  ruleFailRate: document.getElementById("ruleFailRate"),
  goalFailRate: document.getElementById("goalFailRate"),
  resultTbody: document.getElementById("resultTbody"),
  prevPageBtn: document.getElementById("prevPageBtn"),
  nextPageBtn: document.getElementById("nextPageBtn"),
  pageInfo: document.getElementById("pageInfo"),
  detailBox: document.getElementById("detailBox"),
  selectedTitle: document.getElementById("selectedTitle"),
  viewerCanvas: document.getElementById("viewerCanvas")
};

const state = {
  rows: [],
  selectedId: null
};

const viewer = createViewer(refs.viewerCanvas);

refs.reloadBtn.addEventListener("click", () => {
  loadCatalog();
});
refs.familySelect.addEventListener("change", () => {
  refs.offsetInput.value = "0";
  loadCatalog();
});
refs.statusSelect.addEventListener("change", () => {
  refs.offsetInput.value = "0";
  loadCatalog();
});
refs.limitInput.addEventListener("change", () => {
  refs.offsetInput.value = "0";
  loadCatalog();
});
refs.prevPageBtn.addEventListener("click", () => {
  const limit = Number(refs.limitInput.value || 40);
  const offset = Math.max(0, Number(refs.offsetInput.value || 0));
  refs.offsetInput.value = String(Math.max(0, offset - limit));
  loadCatalog();
});
refs.nextPageBtn.addEventListener("click", () => {
  const limit = Math.max(1, Number(refs.limitInput.value || 40));
  const offset = Math.max(0, Number(refs.offsetInput.value || 0));
  refs.offsetInput.value = String(offset + limit);
  loadCatalog();
});

window.addEventListener("resize", () => {
  viewer.resize();
});

loadCatalog();

async function loadCatalog() {
  refs.reloadBtn.disabled = true;
  refs.reloadBtn.textContent = "计算中...";

  const params = new URLSearchParams({
    boundary_n: refs.boundaryNInput.value.trim(),
    boundary_g: refs.boundaryGInput.value.trim(),
    family: refs.familySelect.value,
    status: refs.statusSelect.value,
    limit: refs.limitInput.value.trim(),
    offset: refs.offsetInput.value.trim()
  });

  try {
    const response = await fetch(`/api/catalog?${params.toString()}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "请求失败");
    }

    syncFamilyOptions(payload.meta?.families || []);
    renderSummary(payload.summary, payload.meta);
    renderPager(payload.meta);

    state.rows = payload.rows || [];
    renderTable(state.rows);

    if (state.rows.length > 0) {
      const candidate = state.rows.find((item) => item.design_id === state.selectedId);
      const fallback = state.rows.find((item) => Number(item.metrics.panel_count || 0) > 0) || state.rows[0];
      selectDesign(candidate ? candidate.design_id : fallback.design_id);
    } else {
      state.selectedId = null;
      refs.selectedTitle.textContent = "当前筛选无结果";
      refs.detailBox.textContent = "请调整筛选条件或降低位点规模后重试。";
      viewer.clear();
    }
  } catch (error) {
    refs.selectedTitle.textContent = "加载失败";
    refs.detailBox.textContent = `加载失败：${error.message}`;
    refs.pageInfo.textContent = "第 - / - 页";
    refs.prevPageBtn.disabled = true;
    refs.nextPageBtn.disabled = true;
    viewer.clear();
  } finally {
    refs.reloadBtn.disabled = false;
    refs.reloadBtn.textContent = "刷新组合结果";
  }
}

function syncFamilyOptions(families) {
  const previous = refs.familySelect.value || "all";
  refs.familySelect.innerHTML = "";

  const allOption = document.createElement("option");
  allOption.value = "all";
  allOption.textContent = "全部分型";
  refs.familySelect.appendChild(allOption);

  families.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.key;
    option.textContent = item.label;
    refs.familySelect.appendChild(option);
  });

  if ([...refs.familySelect.options].some((item) => item.value === previous)) {
    refs.familySelect.value = previous;
  } else {
    refs.familySelect.value = "all";
  }
}

function renderSummary(summary, meta) {
  if (!summary) {
    refs.enumerationTotal.textContent = "-";
    refs.generatedTotal.textContent = "-";
    refs.goalPassed.textContent = "-";
    refs.goalFailed.textContent = "-";
    refs.filteredTotal.textContent = "-";
    refs.computeSeconds.textContent = "-";
    refs.ruleFailed.textContent = "-";
    refs.boundaryFailed.textContent = "-";
    refs.cacheInfo.textContent = "缓存文件：-";
    refs.goalPassBar.style.width = "0";
    refs.boundaryFailBar.style.width = "0";
    refs.ruleFailBar.style.width = "0";
    refs.goalFailBar.style.width = "0";
    refs.goalPassRate.textContent = "-";
    refs.boundaryFailRate.textContent = "-";
    refs.ruleFailRate.textContent = "-";
    refs.goalFailRate.textContent = "-";
    return;
  }

  const total = Number(meta?.enumeration_total || 0);
  const generated = Number(summary.generated_total || 0);
  const goalPassed = Number(summary.goal_passed || 0);
  const goalFailed = Number(summary.goal_failed || 0);
  const boundaryFailed = Number(summary.boundary_failed || 0);
  const ruleFailed = Number(summary.rule_failed || 0);
  const filtered = Number(meta?.total_after_filter || 0);
  const computeSeconds = Number(meta?.compute_seconds || 0);
  const cacheFile = meta?.cache_file || "-";
  const engineVersion = meta?.engine_version || "-";
  const rodRule = meta?.rod_segment_rule || "-";
  const r8FilteredRemoved = Number(meta?.r8_filtered_removed || 0);

  refs.enumerationTotal.textContent = formatInt(total);
  refs.generatedTotal.textContent = formatInt(generated);
  refs.goalPassed.textContent = formatInt(goalPassed);
  refs.goalFailed.textContent = formatInt(goalFailed);
  refs.filteredTotal.textContent = formatInt(filtered);
  refs.computeSeconds.textContent = computeSeconds.toFixed(3);
  refs.ruleFailed.textContent = formatInt(ruleFailed);
  refs.boundaryFailed.textContent = formatInt(boundaryFailed);
  refs.cacheInfo.textContent =
    `缓存文件：${cacheFile}｜引擎版本：${engineVersion}` +
    `｜杆段规则：${rodRule}｜R8预过滤剔除：${formatInt(r8FilteredRemoved)}`;

  const passRate = total > 0 ? (goalPassed / total) * 100 : 0;
  const goalFailRate = total > 0 ? (goalFailed / total) * 100 : 0;
  const boundaryFailRate = total > 0 ? (boundaryFailed / total) * 100 : 0;
  const ruleFailRate = total > 0 ? (ruleFailed / total) * 100 : 0;

  refs.goalPassBar.style.width = `${passRate.toFixed(2)}%`;
  refs.goalFailBar.style.width = `${goalFailRate.toFixed(2)}%`;
  refs.ruleFailBar.style.width = `${ruleFailRate.toFixed(2)}%`;
  refs.boundaryFailBar.style.width = `${boundaryFailRate.toFixed(2)}%`;

  refs.goalPassRate.textContent = `${passRate.toFixed(1)}%`;
  refs.goalFailRate.textContent = `${goalFailRate.toFixed(1)}%`;
  refs.ruleFailRate.textContent = `${ruleFailRate.toFixed(1)}%`;
  refs.boundaryFailRate.textContent = `${boundaryFailRate.toFixed(1)}%`;
}

function renderPager(meta) {
  const total = Number(meta?.total_after_filter || 0);
  const offset = Math.max(0, Number(meta?.offset || 0));
  const limit = Math.max(1, Number(meta?.limit || 40));
  const page = total === 0 ? 0 : Math.floor(offset / limit) + 1;
  const pages = total === 0 ? 0 : Math.ceil(total / limit);

  refs.pageInfo.textContent = `第 ${page} / ${pages} 页`;
  refs.prevPageBtn.disabled = offset <= 0;
  refs.nextPageBtn.disabled = offset + limit >= total;
}

function renderTable(rows) {
  refs.resultTbody.innerHTML = "";

  rows.forEach((row) => {
    const tr = document.createElement("tr");
    tr.dataset.id = row.design_id;
    tr.classList.add(row.validation.goal_passed ? "row-goal-pass" : "row-goal-fail");

    if (row.design_id === state.selectedId) {
      tr.classList.add("selected");
    }

    const failReasonText = formatFailReasons(row.validation.fail_reasons || []);

    tr.innerHTML = `
      <td>${row.design_id}</td>
      <td>${row.family.label}</td>
      <td>${formatFloat(row.metrics.footprint_a)}</td>
      <td>${formatFloat(row.metrics.usable_area_total)}</td>
      <td>${formatFloat(row.metrics.gain_ratio)}</td>
      <td>${statusPill(row.validation.rules_passed)}</td>
      <td>${statusPill(row.validation.boundary_passed)}</td>
      <td>${statusPill(row.validation.goal_passed)}</td>
      <td class="reason-cell" title="${escapeAttr(failReasonText)}">${failReasonText}</td>
    `;

    tr.addEventListener("click", () => selectDesign(row.design_id));
    refs.resultTbody.appendChild(tr);
  });
}

function statusPill(passed) {
  const cls = passed ? "status-pass" : "status-fail";
  const text = passed ? "通过" : "失败";
  return `<span class="status-pill ${cls}">${text}</span>`;
}

function selectDesign(designId) {
  const selected = state.rows.find((item) => item.design_id === designId);
  if (!selected) {
    return;
  }

  state.selectedId = designId;
  for (const tr of refs.resultTbody.querySelectorAll("tr")) {
    tr.classList.toggle("selected", tr.dataset.id === designId);
  }

  refs.selectedTitle.textContent = `${selected.design_id} · ${selected.family.label}`;
  refs.detailBox.textContent = JSON.stringify(
    {
      family: selected.family,
      params: selected.params,
      validation: selected.validation,
      metrics: selected.metrics,
      layer_masks: selected.layout.layer_masks,
      layer_area_sums: selected.layout.layer_area_sums,
      rod_columns: selected.layout.rod_columns || []
    },
    null,
    2
  );

  viewer.renderDesign(selected);
}

function createViewer(container) {
  const scene = new THREE.Scene();

  const camera = new THREE.PerspectiveCamera(48, 1, 0.01, 500);
  camera.position.set(3.0, 2.4, 3.2);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.6));
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.target.set(0, 0.8, 0);

  const hemiLight = new THREE.HemisphereLight(0xb5efff, 0x1a2f3c, 0.95);
  const keyLight = new THREE.DirectionalLight(0xfff0d0, 0.82);
  keyLight.position.set(5, 8, 2);
  const fillLight = new THREE.DirectionalLight(0x7ee5ff, 0.42);
  fillLight.position.set(-4, 3, -5);
  scene.add(hemiLight, keyLight, fillLight);

  const gridHelper = new THREE.GridHelper(12, 24, 0x3e8fa6, 0x2a4b5b);
  gridHelper.position.y = 0;
  scene.add(gridHelper);

  let activeGroup = null;
  const tmpBox = new THREE.Box3();
  const tmpVec = new THREE.Vector3();

  function renderDesign(row) {
    if (activeGroup) {
      scene.remove(activeGroup);
      disposeGroup(activeGroup);
    }

    const group = new THREE.Group();
    const {
      slots_x: slotsX,
      slots_y: slotsY,
      slots_z: slotsZ,
      panel_length: panelLength,
      panel_width: panelWidth,
      rod_length: rodLength
    } = row.params;

    const panelCells = row.layout.panel_cells || [];
    const rodColumns = row.layout.rod_columns || [];
    const supportPoints =
      rodColumns.length > 0
        ? rodColumns.map(([ix, iy]) => [ix, iy])
        : (row.layout.rod_support_points || []);

    const rodRadius = Math.min(panelLength, panelWidth) * 0.06;
    const panelThickness = Math.max(0.02, rodLength * 0.1);

    const rodGeo = new THREE.CylinderGeometry(rodRadius, rodRadius, rodLength * 0.95, 12);
    const rodMat = new THREE.MeshStandardMaterial({
      color: 0x63d5d3,
      roughness: 0.38,
      metalness: 0.52
    });

    if (rodColumns.length > 0) {
      for (const [ixRaw, iyRaw, topLevelRaw] of rodColumns) {
        const ix = Number(ixRaw);
        const iy = Number(iyRaw);
        const topLevel = Math.max(0, Number(topLevelRaw || 0));
        for (let level = 0; level < topLevel; level += 1) {
          const rodMesh = new THREE.Mesh(rodGeo, rodMat);
          rodMesh.position.set(ix * panelLength, (level + 0.5) * rodLength, iy * panelWidth);
          group.add(rodMesh);
        }
      }
    } else {
      for (const [ix, iy] of supportPoints) {
        for (let level = 0; level < slotsZ; level += 1) {
          const rodMesh = new THREE.Mesh(rodGeo, rodMat);
          rodMesh.position.set(ix * panelLength, (level + 0.5) * rodLength, iy * panelWidth);
          group.add(rodMesh);
        }
      }
    }

    const panelGeo = new THREE.BoxGeometry(panelLength * 0.94, panelThickness, panelWidth * 0.94);
    const panelMat = new THREE.MeshStandardMaterial({
      color: 0xffc884,
      roughness: 0.48,
      metalness: 0.18
    });
    for (const [level, ix, iy] of panelCells) {
      const panelMesh = new THREE.Mesh(panelGeo, panelMat);
      panelMesh.position.set((ix + 0.5) * panelLength, level * rodLength, (iy + 0.5) * panelWidth);
      group.add(panelMesh);
    }

    const connectorRadius = rodRadius * 0.68;
    const connectorGeo = new THREE.SphereGeometry(connectorRadius, 10, 10);
    const connectorMat = new THREE.MeshStandardMaterial({
      color: 0xa8edff,
      roughness: 0.3,
      metalness: 0.2
    });

    if (rodColumns.length > 0) {
      for (const [ixRaw, iyRaw, topLevelRaw] of rodColumns) {
        const ix = Number(ixRaw);
        const iy = Number(iyRaw);
        const topLevel = Math.max(0, Number(topLevelRaw || 0));
        for (let level = 0; level <= topLevel; level += 1) {
          const connector = new THREE.Mesh(connectorGeo, connectorMat);
          connector.position.set(ix * panelLength, level * rodLength, iy * panelWidth);
          group.add(connector);
        }
      }
    } else {
      for (const [ix, iy] of supportPoints) {
        for (let level = 0; level <= slotsZ; level += 1) {
          const connector = new THREE.Mesh(connectorGeo, connectorMat);
          connector.position.set(ix * panelLength, level * rodLength, iy * panelWidth);
          group.add(connector);
        }
      }
    }

    const centerOffsetX = (slotsX * panelLength) / 2;
    const centerOffsetZ = (slotsY * panelWidth) / 2;
    group.position.set(-centerOffsetX, 0, -centerOffsetZ);

    scene.add(group);
    activeGroup = group;
    fitCameraToObject(group);
  }

  function fitCameraToObject(object3D) {
    tmpBox.setFromObject(object3D);
    if (tmpBox.isEmpty()) {
      return;
    }

    const size = tmpBox.getSize(tmpVec);
    const center = tmpBox.getCenter(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z);
    const fov = (camera.fov * Math.PI) / 180;
    const distance = (maxDim / Math.tan(fov / 2)) * 0.72;

    camera.position.set(center.x + distance * 0.88, center.y + distance * 0.68, center.z + distance * 0.88);
    camera.near = Math.max(0.01, distance / 150);
    camera.far = Math.max(200, distance * 8);
    camera.updateProjectionMatrix();
    controls.target.copy(center);
    controls.update();
  }

  function clear() {
    if (activeGroup) {
      scene.remove(activeGroup);
      disposeGroup(activeGroup);
      activeGroup = null;
    }
    renderer.render(scene, camera);
  }

  function resize() {
    const width = Math.max(10, container.clientWidth);
    const height = Math.max(10, container.clientHeight);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  }

  function animate() {
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }
  animate();

  resize();

  return {
    renderDesign,
    clear,
    resize
  };
}

function disposeGroup(group) {
  group.traverse((child) => {
    if (!child.isMesh) {
      return;
    }
    if (child.geometry) {
      child.geometry.dispose();
    }
    if (Array.isArray(child.material)) {
      child.material.forEach((item) => item.dispose());
    } else if (child.material) {
      child.material.dispose();
    }
  });
}

function formatInt(value) {
  return Number(value || 0).toLocaleString("zh-CN");
}

function formatFloat(value) {
  return Number(value || 0).toFixed(3);
}

function formatFailReasons(reasons) {
  if (!Array.isArray(reasons) || reasons.length === 0) {
    return "通过";
  }
  if (reasons.length === 1) {
    return reasons[0];
  }
  return `${reasons[0]}（+${reasons.length - 1}项）`;
}

function escapeAttr(text) {
  return String(text || "")
    .replaceAll("&", "&amp;")
    .replaceAll("\"", "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}
