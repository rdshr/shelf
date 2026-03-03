from __future__ import annotations

import json
from pathlib import Path

from shelf_framework import (
    BoundaryDefinition,
    CombinationRules,
    Footprint2D,
    Goal,
    Hypothesis,
    LogicRecord,
    LogicStep,
    Opening2D,
    ShelfCombination,
    Space3D,
    VerificationInput,
    generate_shelf_combinations,
    modules_to_list,
    strict_mapping_meta,
    validate_combination_principles,
    verify,
)


def build_logic_record(goal: Goal, result_ok: bool) -> LogicRecord:
    steps = [
        LogicStep("G", "goal", evidence=goal.to_dict()),
        LogicStep("M1", "rod", ["G"]),
        LogicStep("M2", "connector", ["G"]),
        LogicStep("M3", "panel", ["G"]),
        LogicStep("R1", "no isolated module", ["M1", "M2", "M3"]),
        LogicStep("R2", "connector is mandatory", ["M2"]),
        LogicStep("R3", "layers_n >= 2 for valid structure", ["M3"]),
        LogicStep("R4", "rods follow Z-axis and are perpendicular to panels", ["M1", "M3"]),
        LogicStep("R5", "panels are parallel and corners connect to rods via connectors", ["M1", "M2", "M3"]),
        LogicStep("R6", "valid set includes only results satisfying R1~R5", ["R1", "R2", "R3", "R4", "R5"]),
        LogicStep("R7", "candidate set may include invalid samples for comparison", ["R6"]),
        LogicStep("H1", "efficiency improves under valid constraints", ["R6"]),
        LogicStep("V1", "verify hypothesis", ["H1"], {"passed": result_ok}),
        LogicStep("C", "conclusion", ["V1"], {"adopt_now": result_ok}),
    ]
    return LogicRecord.build(steps)


def make_boundary(combo: ShelfCombination) -> BoundaryDefinition:
    return BoundaryDefinition(
        layers_n=combo.layers_n,
        payload_p_per_layer=30.0,
        space_s_per_layer=Space3D(
            width=float(combo.footprint_width_units()),
            depth=float(combo.footprint_depth_units()),
            height=float(combo.layers_n),
        ),
        opening_o=Opening2D(width=float(combo.footprint_width_units()), height=1.0),
        footprint_a=Footprint2D(
            width=float(combo.footprint_width_units()),
            depth=float(combo.footprint_depth_units()),
        ),
    )


def build_geometry_payload(combo: ShelfCombination) -> dict[str, object]:
    rod_heights = combo.rod_connection_heights()
    rods = [
        {"start": [x, y, 0], "end": [x, y, rod_heights[(x, y)]]}
        for x, y in sorted(combo.rod_points())
        if (x, y) in rod_heights
    ]

    panels: list[list[list[int]]] = []
    for x, y, z in combo.panel_cells():
        panels.append(
            [
                [x, y, z],
                [x + 1, y, z],
                [x + 1, y + 1, z],
                [x, y + 1, z],
            ]
        )

    return {
        "rods": rods,
        "panels": panels,
        "bounds": {
            "width": combo.footprint_width_units(),
            "depth": combo.footprint_depth_units(),
            "height": combo.layers_n,
        },
    }


def render_3d_view_html(output_path: Path, payload: dict[str, object]) -> None:
    data_json = json.dumps(payload, ensure_ascii=False)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>组合 3D 模型</title>
  <style>
    :root {{
      --bg: #f0ede6;
      --card: #ffffff;
      --line: #d6d3d1;
      --ink: #111827;
      --accent: #0f766e;
      --soft: #d1fae5;
      --fail: #b91c1c;
      --ok: #166534;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: "Microsoft YaHei UI", "Noto Sans SC", sans-serif;
      background:
        radial-gradient(1200px 400px at 10% -10%, #dbeafe, transparent 60%),
        radial-gradient(1000px 350px at 90% -10%, #fee2e2, transparent 50%),
        var(--bg);
    }}
    .wrap {{
      max-width: 1280px;
      margin: 20px auto;
      padding: 0 14px;
      display: grid;
      gap: 12px;
      grid-template-columns: 330px 1fr;
    }}
    .card {{
      border: 1px solid var(--line);
      border-radius: 14px;
      background: var(--card);
      box-shadow: 0 8px 24px rgba(17, 24, 39, 0.08);
    }}
    .side {{
      padding: 12px;
      display: grid;
      gap: 10px;
      align-content: start;
      max-height: calc(100vh - 56px);
      position: sticky;
      top: 12px;
      overflow: hidden;
    }}
    .controls {{
      display: grid;
      gap: 8px;
    }}
    .row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }}
    select, input, button {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px;
      font-size: 14px;
      background: #fff;
    }}
    button {{
      cursor: pointer;
      background: linear-gradient(90deg, #ecfeff, #ecfccb);
    }}
    .list {{
      border: 1px solid var(--line);
      border-radius: 10px;
      overflow: auto;
      max-height: 54vh;
      background: #fafaf9;
    }}
    .item {{
      border-bottom: 1px solid #e7e5e4;
      padding: 8px;
      cursor: pointer;
      font-size: 13px;
      line-height: 1.35;
    }}
    .item:hover {{ background: #f1f5f9; }}
    .item.active {{
      background: var(--soft);
      border-left: 3px solid var(--accent);
      padding-left: 5px;
    }}
    .main {{
      padding: 10px;
      display: grid;
      gap: 10px;
    }}
    .topbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
    }}
    .pill {{
      font-size: 12px;
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 10px;
      background: #fff;
    }}
    .ok {{ color: var(--ok); font-weight: 700; }}
    .fail {{ color: var(--fail); font-weight: 700; }}
    canvas {{
      width: 100%;
      height: 640px;
      border-radius: 12px;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
    }}
    .meta {{
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px;
      background: #fff;
      font-size: 14px;
      line-height: 1.5;
    }}
    @media (max-width: 960px) {{
      .wrap {{ grid-template-columns: 1fr; }}
      .side {{ position: static; max-height: none; }}
      canvas {{ height: 460px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <aside class="card side">
      <h3 style="margin:0;">组合筛选</h3>
      <div class="controls">
        <div class="row">
          <select id="layerFilter">
            <option value="all">层数: 全部</option>
            <option value="1">层数: 1</option>
            <option value="2">层数: 2</option>
          </select>
          <select id="areaFilter">
            <option value="all">占地: 全部</option>
            <option value="1">占地: 1</option>
            <option value="2">占地: 2</option>
            <option value="3">占地: 3</option>
            <option value="4">占地: 4</option>
          </select>
        </div>
        <input id="searchBox" type="text" placeholder="搜索组合 ID..." />
        <div class="row">
          <button id="prevBtn" type="button">上一个</button>
          <button id="nextBtn" type="button">下一个</button>
        </div>
      </div>
      <div class="list" id="comboList"></div>
    </aside>
    <main class="card main">
      <div class="topbar">
        <span class="pill">可旋转、可缩放（滚轮）</span>
        <span class="pill">支持面积3与“田”字（2x2）组合</span>
        <span class="pill">当前列表仅展示满足 R1~R5 的有效输出</span>
        <label class="pill" style="display:flex;align-items:center;gap:8px;">
          旋转
          <input id="angleRange" type="range" min="0" max="360" value="30" style="width:180px;padding:0;border:none;" />
        </label>
      </div>
      <canvas id="view" width="1100" height="640"></canvas>
      <div class="meta" id="meta"></div>
    </main>
  </div>
  <script>
    const payload = {data_json};
    const allCombos = payload.combinations;
    const layerFilter = document.getElementById("layerFilter");
    const areaFilter = document.getElementById("areaFilter");
    const searchBox = document.getElementById("searchBox");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const comboList = document.getElementById("comboList");
    const angleRange = document.getElementById("angleRange");
    const canvas = document.getElementById("view");
    const ctx = canvas.getContext("2d");
    const meta = document.getElementById("meta");

    let filtered = [...allCombos];
    let currentIndex = 0;
    let zoom = 1.0;

    function sortByUsefulOrder(items) {{
      return items.sort((a, b) =>
        a.layers_n - b.layers_n ||
        a.footprint_area_units - b.footprint_area_units ||
        a.total_panel_count - b.total_panel_count ||
        a.combination_id.localeCompare(b.combination_id)
      );
    }}

    function applyFilters() {{
      const layerValue = layerFilter.value;
      const areaValue = areaFilter.value;
      const q = searchBox.value.trim().toLowerCase();
      filtered = allCombos.filter((item) => {{
        if (layerValue !== "all" && String(item.layers_n) !== layerValue) return false;
        if (areaValue !== "all" && String(item.footprint_area_units) !== areaValue) return false;
        if (q && !item.combination_id.toLowerCase().includes(q)) return false;
        return true;
      }});
      sortByUsefulOrder(filtered);
      if (currentIndex >= filtered.length) currentIndex = 0;
      renderList();
      updateView();
    }}

    function renderList() {{
      comboList.innerHTML = "";
      if (!filtered.length) {{
        comboList.innerHTML = '<div class="item">无匹配组合</div>';
        return;
      }}
      filtered.forEach((item, idx) => {{
        const div = document.createElement("div");
        div.className = `item ${{idx === currentIndex ? "active" : ""}}`;
        div.innerHTML = `
          <div><b>${{item.combination_id}}</b></div>
          <div>层=${{item.layers_n}} 占地=${{item.footprint_area_units}} 每层面积=${{item.layer_areas.join("/")}}</div>
        `;
        div.addEventListener("click", () => {{
          currentIndex = idx;
          renderList();
          updateView();
        }});
        comboList.appendChild(div);
      }});
    }}

    function projectPoint(p, angle) {{
      const [x, y, z] = p;
      const xr = x * Math.cos(angle) - y * Math.sin(angle);
      const yr = x * Math.sin(angle) + y * Math.cos(angle);
      return [xr, -z * 1.6 - yr * 0.65];
    }}

    function fitTransform(combo, angle) {{
      const points = [];
      for (const rod of combo.geometry.rods) {{
        points.push(rod.start, rod.end);
      }}
      for (const panel of combo.geometry.panels) {{
        points.push(...panel);
      }}
      const projected = points.map((p) => projectPoint(p, angle));
      const xs = projected.map((p) => p[0]);
      const ys = projected.map((p) => p[1]);
      const minX = Math.min(...xs), maxX = Math.max(...xs);
      const minY = Math.min(...ys), maxY = Math.max(...ys);
      const spanX = Math.max(1e-6, maxX - minX);
      const spanY = Math.max(1e-6, maxY - minY);
      const scale = Math.min((canvas.width * 0.78) / spanX, (canvas.height * 0.72) / spanY) * zoom;
      const tx = canvas.width * 0.5 - ((minX + maxX) / 2) * scale;
      const ty = canvas.height * 0.56 - ((minY + maxY) / 2) * scale;
      return {{ scale, tx, ty }};
    }}

    function drawCombo(combo) {{
      const angle = (Number(angleRange.value) * Math.PI) / 180;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const tf = fitTransform(combo, angle);
      const map = (p) => {{
        const t = projectPoint(p, angle);
        return [t[0] * tf.scale + tf.tx, t[1] * tf.scale + tf.ty];
      }};

      const panelPolys = combo.geometry.panels.map((panel) => {{
        const avgDepth = panel.reduce((acc, p) => acc + p[1] + p[2], 0) / panel.length;
        return {{ panel, avgDepth }};
      }});
      panelPolys.sort((a, b) => a.avgDepth - b.avgDepth);

      for (const item of panelPolys) {{
        const projected = item.panel.map((p) => map(p));
        ctx.beginPath();
        ctx.moveTo(projected[0][0], projected[0][1]);
        for (let i = 1; i < projected.length; i += 1) {{
          ctx.lineTo(projected[i][0], projected[i][1]);
        }}
        ctx.closePath();
        ctx.fillStyle = "rgba(15, 118, 110, 0.22)";
        ctx.strokeStyle = "rgba(15, 118, 110, 0.95)";
        ctx.lineWidth = 1.8;
        ctx.fill();
        ctx.stroke();
      }}

      for (const rod of combo.geometry.rods) {{
        const s = map(rod.start);
        const e = map(rod.end);
        ctx.beginPath();
        ctx.moveTo(s[0], s[1]);
        ctx.lineTo(e[0], e[1]);
        ctx.strokeStyle = "rgba(17, 24, 39, 0.95)";
        ctx.lineWidth = 2.0;
        ctx.stroke();
      }}
    }}

    function updateView() {{
      if (!filtered.length) {{
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        meta.innerHTML = "当前筛选下无组合。";
        return;
      }}
      const combo = filtered[currentIndex];
      drawCombo(combo);
      const stateClass = combo.verification.passed ? "ok" : "fail";
      const stateText = combo.verification.passed ? "通过" : "失败";
      meta.innerHTML = `
        <div><b>${{combo.combination_id}}</b></div>
        <div>层数=${{combo.layers_n}} | 占地面积=${{combo.footprint_area_units}} | 每层面积=${{combo.layer_areas.join("/")}} | 目标效率=${{combo.target_efficiency.toFixed(2)}}</div>
        <div>验证：<span class="${{stateClass}}">${{stateText}}</span></div>
        <div>原因：${{combo.verification.reasons.length ? combo.verification.reasons.join("；") : "无"}}</div>
      `;
    }}

    layerFilter.addEventListener("change", applyFilters);
    areaFilter.addEventListener("change", applyFilters);
    searchBox.addEventListener("input", applyFilters);
    angleRange.addEventListener("input", updateView);
    prevBtn.addEventListener("click", () => {{
      if (!filtered.length) return;
      currentIndex = (currentIndex - 1 + filtered.length) % filtered.length;
      renderList();
      updateView();
    }});
    nextBtn.addEventListener("click", () => {{
      if (!filtered.length) return;
      currentIndex = (currentIndex + 1) % filtered.length;
      renderList();
      updateView();
    }});
    canvas.addEventListener("wheel", (event) => {{
      event.preventDefault();
      const factor = event.deltaY < 0 ? 1.06 : 0.94;
      zoom = Math.max(0.35, Math.min(3.5, zoom * factor));
      updateView();
    }}, {{ passive: false }});

    applyFilters();
  </script>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def render_validation_html(output_path: Path, payload: dict[str, object]) -> None:
    data_json = json.dumps(payload, ensure_ascii=False)
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>组合验证结果</title>
  <style>
    :root {{
      --line: #ddd6ce;
      --ink: #111827;
      --ok: #166534;
      --fail: #b91c1c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      color: var(--ink);
      font-family: "Microsoft YaHei UI", "Noto Sans SC", sans-serif;
      background:
        radial-gradient(1000px 400px at 20% -20%, #fef3c7, transparent 60%),
        radial-gradient(1000px 400px at 80% -20%, #dbeafe, transparent 55%),
        #fafaf9;
    }}
    .wrap {{
      max-width: 1260px;
      margin: 20px auto;
      padding: 0 14px 24px;
      display: grid;
      gap: 12px;
    }}
    .card {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 12px;
      box-shadow: 0 8px 22px rgba(17, 24, 39, 0.08);
    }}
    .stats {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      margin-top: 8px;
      font-size: 14px;
    }}
    .pill {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 10px;
      background: #fff;
    }}
    .ok {{ color: var(--ok); font-weight: 700; }}
    .fail {{ color: var(--fail); font-weight: 700; }}
    .toolbar {{
      display: grid;
      grid-template-columns: 180px 180px 1fr;
      gap: 8px;
      margin-top: 10px;
    }}
    select, input {{
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 8px;
      font-size: 14px;
    }}
    canvas {{
      width: 100%;
      height: 280px;
      border: 1px solid var(--line);
      border-radius: 10px;
      margin-top: 10px;
      background: #fff;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      text-align: left;
      padding: 8px 6px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }}
    thead th {{
      position: sticky;
      top: 0;
      background: #f8fafc;
      z-index: 1;
    }}
    .table-wrap {{
      max-height: 68vh;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 10px;
    }}
    @media (max-width: 900px) {{
      .toolbar {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="card">
      <h2 style="margin:0;">组合验证结果总览</h2>
      <div class="stats" id="summary"></div>
      <div class="toolbar">
        <select id="layerFilter">
          <option value="all">层数: 全部</option>
          <option value="1">层数: 1</option>
          <option value="2">层数: 2</option>
        </select>
        <select id="stateFilter">
          <option value="all">结果: 全部</option>
          <option value="pass">仅通过</option>
          <option value="fail">仅失败</option>
        </select>
        <input id="searchBox" type="text" placeholder="搜索 ID 或原因..." />
      </div>
      <canvas id="chart" width="1180" height="280"></canvas>
    </section>
    <section class="card">
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>组合</th>
              <th>层数</th>
              <th>占地</th>
              <th>每层面积</th>
              <th>目标效率</th>
              <th>结果</th>
              <th>原因</th>
            </tr>
          </thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
    </section>
  </div>
  <script>
    const payload = {data_json};
    const allItems = payload.combinations.slice();
    const baseline = payload.baseline_efficiency;
    const candidateSummary = payload.candidate_summary || {{ total: allItems.length, valid_by_principles: allItems.length, invalid_by_principles: 0 }};

    const summary = document.getElementById("summary");
    const rows = document.getElementById("rows");
    const layerFilter = document.getElementById("layerFilter");
    const stateFilter = document.getElementById("stateFilter");
    const searchBox = document.getElementById("searchBox");
    const canvas = document.getElementById("chart");
    const ctx = canvas.getContext("2d");

    let filtered = [];

    function updateSummary(items) {{
      const passCount = items.filter((x) => x.verification.passed).length;
      const failCount = items.length - passCount;
      summary.innerHTML = `
        <span class="pill">候选总数: <b>${{candidateSummary.total}}</b></span>
        <span class="pill">原则有效输出: <b>${{items.length}}</b></span>
        <span class="pill">原则筛除: <b>${{candidateSummary.invalid_by_principles}}</b></span>
        <span class="pill">通过: <span class="ok">${{passCount}}</span></span>
        <span class="pill">失败: <span class="fail">${{failCount}}</span></span>
        <span class="pill">基线效率: <b>${{baseline}}</b></span>
      `;
    }}

    function applyFilters() {{
      const layerValue = layerFilter.value;
      const stateValue = stateFilter.value;
      const q = searchBox.value.trim().toLowerCase();
      filtered = allItems.filter((item) => {{
        if (layerValue !== "all" && String(item.layers_n) !== layerValue) return false;
        if (stateValue === "pass" && !item.verification.passed) return false;
        if (stateValue === "fail" && item.verification.passed) return false;
        if (q) {{
          const blob = `${{item.combination_id}} ${{item.verification.reasons.join(" ")}}`.toLowerCase();
          if (!blob.includes(q)) return false;
        }}
        return true;
      }}).sort((a, b) =>
        a.layers_n - b.layers_n ||
        a.footprint_area_units - b.footprint_area_units ||
        a.total_panel_count - b.total_panel_count ||
        a.combination_id.localeCompare(b.combination_id)
      );
      renderRows(filtered);
      renderChart(filtered);
      updateSummary(filtered);
    }}

    function renderRows(items) {{
      rows.innerHTML = "";
      for (const item of items) {{
        const tr = document.createElement("tr");
        const stateClass = item.verification.passed ? "ok" : "fail";
        const stateText = item.verification.passed ? "通过" : "失败";
        tr.innerHTML = `
          <td><b>${{item.combination_id}}</b></td>
          <td>${{item.layers_n}}</td>
          <td>${{item.footprint_area_units}}</td>
          <td>${{item.layer_areas.join("/")}}</td>
          <td>${{item.target_efficiency.toFixed(2)}}</td>
          <td class="${{stateClass}}">${{stateText}}</td>
          <td>${{item.verification.reasons.length ? item.verification.reasons.join("；") : "无"}}</td>
        `;
        rows.appendChild(tr);
      }}
    }}

    function renderChart(items) {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      if (!items.length) return;

      const pad = 36;
      const chartW = canvas.width - pad * 2;
      const chartH = canvas.height - pad * 2;
      const maxY = Math.max(...items.map((x) => x.target_efficiency), baseline, 1);
      const barW = chartW / items.length;

      ctx.strokeStyle = "#6b7280";
      ctx.beginPath();
      ctx.moveTo(pad, canvas.height - pad);
      ctx.lineTo(canvas.width - pad, canvas.height - pad);
      ctx.stroke();

      const baselineY = canvas.height - pad - (baseline / maxY) * chartH;
      ctx.strokeStyle = "#b91c1c";
      ctx.setLineDash([5, 4]);
      ctx.beginPath();
      ctx.moveTo(pad, baselineY);
      ctx.lineTo(canvas.width - pad, baselineY);
      ctx.stroke();
      ctx.setLineDash([]);

      items.forEach((item, idx) => {{
        const h = (item.target_efficiency / maxY) * chartH;
        const x = pad + idx * barW + 1;
        const y = canvas.height - pad - h;
        ctx.fillStyle = item.verification.passed ? "rgba(22, 101, 52, 0.75)" : "rgba(185, 28, 28, 0.75)";
        ctx.fillRect(x, y, Math.max(2, barW - 2), h);
      }});
    }}

    layerFilter.addEventListener("change", applyFilters);
    stateFilter.addEventListener("change", applyFilters);
    searchBox.addEventListener("input", applyFilters);
    applyFilters();
  </script>
</body>
</html>
"""
    output_path.write_text(html, encoding="utf-8")


def main() -> None:
    goal = Goal("提升单位占地面积下的存取效率")
    hypothesis = Hypothesis(
        hypothesis_id="H1",
        statement="在有效组合原则约束下，单位占地面积效率应提升",
    )

    max_layers_n = 2
    max_footprint_area = 4
    panel_unit_area = 1.0
    baseline_efficiency = 1.0

    rules = CombinationRules.default()
    valid_module_combinations = rules.valid_subsets()
    all_combinations = generate_shelf_combinations(
        max_layers_n=max_layers_n,
        max_footprint_area=max_footprint_area,
        panel_unit_area=panel_unit_area,
    )

    candidate_results: list[dict[str, object]] = []
    for combo in all_combinations:
        boundary = make_boundary(combo)
        geometry_ok, geometry_errors = validate_combination_principles(combo, rules)

        verification_input = VerificationInput(
            boundary=boundary,
            combo=set(combo.module_combo),
            valid_combinations=valid_module_combinations,
            baseline_efficiency=baseline_efficiency,
            target_efficiency=combo.target_efficiency(),
            geometry_principles_valid=geometry_ok,
            geometry_errors=geometry_errors,
        )
        verification_result = verify(verification_input)

        candidate_results.append(
            {
                **combo.to_dict(),
                "module_combo": modules_to_list(set(combo.module_combo)),
                "geometry": build_geometry_payload(combo),
                "principles_valid": geometry_ok,
                "verification": verification_result.to_dict(),
            }
        )

    valid_results = [item for item in candidate_results if item["principles_valid"]]
    pass_count = sum(1 for item in valid_results if item["verification"]["passed"])

    docs_dir = Path("docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

    report_payload = {
        "goal": goal.to_dict(),
        "hypothesis": hypothesis.to_dict(),
        "strict_mapping": strict_mapping_meta(),
        "constraints": {
            "panel_unit_area": panel_unit_area,
            "max_layers_n": max_layers_n,
            "max_footprint_area": max_footprint_area,
        },
        "baseline_efficiency": baseline_efficiency,
        # R7: candidate set may contain invalid samples for comparison.
        "candidate_summary": {
            "total": len(candidate_results),
            "valid_by_principles": len(valid_results),
            "invalid_by_principles": len(candidate_results) - len(valid_results),
        },
        # R6/R7: final output only includes combinations satisfying R1~R5.
        "combinations": valid_results,
        "summary": {
            "total": len(valid_results),
            "passed": pass_count,
            "failed": len(valid_results) - pass_count,
        },
    }

    (docs_dir / "combination_validation_results.json").write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    render_3d_view_html(docs_dir / "combination_3d_view.html", report_payload)
    render_validation_html(docs_dir / "combination_validation_dashboard.html", report_payload)

    logic_record = build_logic_record(goal, pass_count > 0)
    logic_record.export_json("docs/logic_record.json")

    snapshot = {
        "goal": goal.to_dict(),
        "hypothesis": hypothesis.to_dict(),
        "strict_mapping": strict_mapping_meta(),
        "constraints": report_payload["constraints"],
        "summary": report_payload["summary"],
        "artifacts": {
            "json": "docs/combination_validation_results.json",
            "view_3d": "docs/combination_3d_view.html",
            "view_validation": "docs/combination_validation_dashboard.html",
            "logic_record_path": "docs/logic_record.json",
        },
    }
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

