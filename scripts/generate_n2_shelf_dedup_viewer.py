from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from itertools import product
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_N = 2
DEFAULT_X = 30.0
DEFAULT_Y = 30.0
DEFAULT_H = 30.0

CORNERS = ("FL", "FR", "BR", "BL")
SIDES = ("front", "right", "back", "left")
SIDE_CORNERS = {
    "front": ("FL", "FR"),
    "back": ("BL", "BR"),
    "left": ("FL", "BL"),
    "right": ("FR", "BR"),
}

ROTATE_CORNER_90 = {"FL": "FR", "FR": "BR", "BR": "BL", "BL": "FL"}
ROTATE_SIDE_90 = {"front": "right", "right": "back", "back": "left", "left": "front"}


@dataclass(frozen=True)
class LayerPattern:
    rods: tuple[str, ...]
    side_panels: tuple[str, ...]


@dataclass(frozen=True)
class Combo:
    layers: tuple[LayerPattern, ...]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate rotation-dedup shelf combos for arbitrary layer count (N)."
    )
    parser.add_argument("--layers", type=int, default=DEFAULT_N, help="Layer count N")
    parser.add_argument("--x", type=float, default=DEFAULT_X, help="Per-layer span x")
    parser.add_argument("--y", type=float, default=DEFAULT_Y, help="Per-layer span y")
    parser.add_argument("--h", type=float, default=DEFAULT_H, help="Single-layer height h")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="",
        help="Output directory path (default: docs/diagrams/N{N}_x{X}_y{Y}_h{H}_panelmax{H})",
    )
    args = parser.parse_args()

    if args.layers <= 0:
        parser.error("--layers must be > 0")
    if args.x <= 0 or args.y <= 0 or args.h <= 0:
        parser.error("--x, --y, --h must all be > 0")
    return args


def fmt_num(value: float) -> str:
    return f"{value:g}"


def default_output_dir(n: int, x: float, y: float, h: float) -> Path:
    return ROOT / "docs" / "diagrams" / f"N{n}_x{fmt_num(x)}_y{fmt_num(y)}_h{fmt_num(h)}_panelmax{fmt_num(h)}"


def resolve_output_dir(n: int, x: float, y: float, h: float, output_dir: str) -> Path:
    if not output_dir:
        return default_output_dir(n, x, y, h)
    path = Path(output_dir)
    if not path.is_absolute():
        path = ROOT / path
    return path


def corner_xy(x: float, y: float) -> dict[str, tuple[float, float]]:
    return {
        "FL": (0.0, 0.0),
        "FR": (x, 0.0),
        "BL": (0.0, y),
        "BR": (x, y),
    }


def powerset(items: tuple[str, ...]) -> list[tuple[str, ...]]:
    out: list[tuple[str, ...]] = []
    for mask in range(1 << len(items)):
        out.append(tuple(items[i] for i in range(len(items)) if (mask >> i) & 1))
    return out


def corners_from_side_panels(side_panels: tuple[str, ...]) -> set[str]:
    covered: set[str] = set()
    for side in side_panels:
        c1, c2 = SIDE_CORNERS[side]
        covered.add(c1)
        covered.add(c2)
    return covered


def open_sides(side_panels: tuple[str, ...]) -> list[str]:
    return [side for side in SIDES if side not in side_panels]


def valid_layer_pattern(rods: tuple[str, ...], side_panels: tuple[str, ...]) -> bool:
    # Keep panel support complexity bounded: at most two side support panels per layer.
    if len(side_panels) > 2:
        return False

    # For adjacent panels, shared corner support is counted once (no double counting).
    panel_corner_count: dict[str, int] = {corner: 0 for corner in CORNERS}
    for side in side_panels:
        for corner in SIDE_CORNERS[side]:
            panel_corner_count[corner] += 1
    overlap_correction = sum(max(0, count - 1) for count in panel_corner_count.values())

    # R2: E(rod)=1, E(panel)=2, with overlap correction on shared panel corners.
    equivalent_total = len(rods) + 2 * len(side_panels) - overlap_correction
    if equivalent_total != 4:
        return False

    # R2 strong condition: full 4-corner support coverage is mandatory.
    if (set(rods) | corners_from_side_panels(side_panels)) != set(CORNERS):
        return False

    # R7: at least one side open.
    if len(open_sides(side_panels)) < 1:
        return False

    # Side support panel height <= h is enforced by generation model (one-layer panel).
    return True


def rotate_layer_pattern_90(pattern: LayerPattern) -> LayerPattern:
    rods = tuple(sorted(ROTATE_CORNER_90[item] for item in pattern.rods))
    side_panels = tuple(sorted(ROTATE_SIDE_90[item] for item in pattern.side_panels))
    return LayerPattern(rods=rods, side_panels=side_panels)


def rotate_combo_90(combo: Combo) -> Combo:
    return Combo(layers=tuple(rotate_layer_pattern_90(layer) for layer in combo.layers))


ComboKey = tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]


def combo_key(combo: Combo) -> ComboKey:
    return tuple((layer.rods, layer.side_panels) for layer in combo.layers)


def key_to_combo(key: ComboKey) -> Combo:
    return Combo(
        layers=tuple(
            LayerPattern(rods=item[0], side_panels=item[1])
            for item in key
        )
    )


def canonical_key_under_rotation(combo: Combo) -> ComboKey:
    cands: list[ComboKey] = []
    cur = combo
    for _ in range(4):
        cands.append(combo_key(cur))
        cur = rotate_combo_90(cur)
    return min(cands)


def combo_label(combo: Combo) -> str:
    labels: list[str] = []
    for idx, layer in enumerate(combo.layers, start=1):
        rods = "-".join(layer.rods) if layer.rods else "none"
        panels = "-".join(layer.side_panels) if layer.side_panels else "none"
        labels.append(f"L{idx}(R:{rods}|P:{panels})")
    return " ".join(labels)


def build_layer_patterns() -> list[LayerPattern]:
    patterns: list[LayerPattern] = []
    for rods in powerset(CORNERS):
        for side_panels in powerset(SIDES):
            rods_sorted = tuple(sorted(rods))
            side_panels_sorted = tuple(sorted(side_panels))
            if valid_layer_pattern(rods_sorted, side_panels_sorted):
                patterns.append(LayerPattern(rods=rods_sorted, side_panels=side_panels_sorted))
    return sorted(
        set(patterns),
        key=lambda item: (len(item.rods), len(item.side_panels), item.rods, item.side_panels),
    )


def merge_corner_rod_segments(combo: Combo, h: float) -> dict[str, list[tuple[float, float]]]:
    merged: dict[str, list[tuple[float, float]]] = {corner: [] for corner in CORNERS}
    for corner in CORNERS:
        segs: list[tuple[float, float]] = []
        for layer_idx, layer in enumerate(combo.layers):
            if corner in layer.rods:
                segs.append((layer_idx * h, (layer_idx + 1) * h))
        if not segs:
            continue
        segs.sort()
        cur0, cur1 = segs[0]
        for z0, z1 in segs[1:]:
            if abs(z0 - cur1) < 1e-9:
                cur1 = z1
            else:
                merged[corner].append((cur0, cur1))
                cur0, cur1 = z0, z1
        merged[corner].append((cur0, cur1))
    return merged


def side_panel_quads(
    combo: Combo,
    x: float,
    y: float,
    h: float,
) -> list[tuple[list[tuple[float, float, float]], int]]:
    quads: list[tuple[list[tuple[float, float, float]], int]] = []
    xy = corner_xy(x, y)
    for level_idx, layer in enumerate(combo.layers, start=1):
        z0 = (level_idx - 1) * h
        z1 = level_idx * h
        for side in layer.side_panels:
            c1, c2 = SIDE_CORNERS[side]
            x1, y1 = xy[c1]
            x2, y2 = xy[c2]
            quads.append(([(x1, y1, z0), (x2, y2, z0), (x2, y2, z1), (x1, y1, z1)], level_idx))
    return quads


def load_board_quads(n: int, x: float, y: float, h: float) -> list[list[tuple[float, float, float]]]:
    quads: list[list[tuple[float, float, float]]] = []
    for level_idx in range(1, n + 1):
        z = level_idx * h
        quads.append([(0.0, 0.0, z), (x, 0.0, z), (x, y, z), (0.0, y, z)])
    return quads


def project_point(point: tuple[float, float, float]) -> tuple[float, float]:
    ax = math.radians(25)
    ay = math.radians(-36)
    x0, y0, z0 = point
    x1 = x0 * math.cos(ay) + z0 * math.sin(ay)
    y1 = y0
    z1 = -x0 * math.sin(ay) + z0 * math.cos(ay)
    x2 = x1
    y2 = y1 * math.cos(ax) - z1 * math.sin(ax)
    return (x2, -y2)


def draw_preview_png(combo: Combo, out_path: Path, title: str, x: float, y: float, h: float) -> None:
    side_quads = side_panel_quads(combo, x, y, h)
    board_quads = load_board_quads(len(combo.layers), x, y, h)
    rods = merge_corner_rod_segments(combo, h)
    xy = corner_xy(x, y)

    pts: list[tuple[float, float]] = []
    for quad in board_quads:
        pts.extend(project_point(p) for p in quad)
    for quad, _ in side_quads:
        pts.extend(project_point(p) for p in quad)
    for corner in CORNERS:
        x0, y0 = xy[corner]
        for z0, z1 in rods[corner]:
            pts.extend([project_point((x0, y0, z0)), project_point((x0, y0, z1))])

    minx = min(p[0] for p in pts)
    maxx = max(p[0] for p in pts)
    miny = min(p[1] for p in pts)
    maxy = max(p[1] for p in pts)

    width, height, pad = 760, 560, 60
    sx = (width - 2 * pad) / max(maxx - minx, 1e-6)
    sy = (height - 2 * pad) / max(maxy - miny, 1e-6)
    scale = min(sx, sy)

    def to_canvas(point3: tuple[float, float, float]) -> tuple[int, int]:
        xp, yp = project_point(point3)
        return (int((xp - minx) * scale + pad), int((yp - miny) * scale + pad))

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img, "RGBA")

    panel_palette = [
        (245, 158, 11, 130),
        (249, 115, 22, 130),
        (251, 146, 60, 130),
        (234, 88, 12, 130),
    ]
    for quad, level_idx in side_quads:
        fill = panel_palette[(level_idx - 1) % len(panel_palette)]
        draw.polygon([to_canvas(p) for p in quad], fill=fill, outline=(154, 52, 18, 255), width=2)

    for quad in board_quads:
        draw.polygon([to_canvas(p) for p in quad], fill=(59, 130, 246, 95), outline=(30, 64, 175, 255), width=2)

    for corner in CORNERS:
        x0, y0 = xy[corner]
        for z0, z1 in rods[corner]:
            draw.line([to_canvas((x0, y0, z0)), to_canvas((x0, y0, z1))], fill=(17, 24, 39, 255), width=5)

    open_desc = " | ".join(
        f"L{idx} open={open_sides(layer.side_panels)}"
        for idx, layer in enumerate(combo.layers, start=1)
    )
    draw.text((16, 12), title, fill=(0, 0, 0, 255))
    draw.text((16, 34), open_desc, fill=(0, 0, 0, 255))
    img.save(out_path)


def write_obj(combo: Combo, out_path: Path, x: float, y: float, h: float) -> None:
    vertices: list[tuple[float, float, float]] = []
    lines: list[tuple[int, int]] = []
    faces: list[tuple[int, int, int, int]] = []

    rods = merge_corner_rod_segments(combo, h)
    xy = corner_xy(x, y)

    for corner in CORNERS:
        x0, y0 = xy[corner]
        for z0, z1 in rods[corner]:
            i1 = len(vertices) + 1
            vertices.append((x0, y0, z0))
            i2 = len(vertices) + 1
            vertices.append((x0, y0, z1))
            lines.append((i1, i2))

    for quad, _ in side_panel_quads(combo, x, y, h):
        a = len(vertices) + 1
        vertices.append(quad[0])
        b = len(vertices) + 1
        vertices.append(quad[1])
        c = len(vertices) + 1
        vertices.append(quad[2])
        d = len(vertices) + 1
        vertices.append(quad[3])
        faces.append((a, b, c, d))

    for quad in load_board_quads(len(combo.layers), x, y, h):
        a = len(vertices) + 1
        vertices.append(quad[0])
        b = len(vertices) + 1
        vertices.append(quad[1])
        c = len(vertices) + 1
        vertices.append(quad[2])
        d = len(vertices) + 1
        vertices.append(quad[3])
        faces.append((a, b, c, d))

    with out_path.open("w", encoding="utf-8") as f:
        f.write("# generated shelf combo\n")
        for x0, y0, z0 in vertices:
            f.write(f"v {x0:.4f} {y0:.4f} {z0:.4f}\n")
        for a, b in lines:
            f.write(f"l {a} {b}\n")
        for a, b, c, d in faces:
            f.write(f"f {a} {b} {c} {d}\n")


def build_interactive_html(items: list[dict], n: int, x: float, y: float, h: float) -> str:
    combos_json = json.dumps(items, ensure_ascii=False)
    return """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Shelf Combos 3D (Local)</title>
  <style>
    html, body {
      margin: 0;
      height: 100%;
      font-family: Arial, sans-serif;
      background: #f6f7fb;
    }
    #app {
      display: grid;
      grid-template-columns: 380px 1fr;
      height: 100%;
    }
    #panel {
      padding: 14px;
      background: #ffffff;
      border-right: 1px solid #d6d8e1;
      overflow: auto;
    }
    #viewer {
      position: relative;
      overflow: hidden;
    }
    #cv {
      width: 100%;
      height: 100%;
      display: block;
      background: #f6f7fb;
    }
    .row { margin-bottom: 10px; }
    .mono {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      white-space: pre-wrap;
    }
    button { padding: 6px 10px; margin-right: 6px; }
    select { width: 100%; padding: 6px; }
  </style>
</head>
<body>
<div id=\"app\">
  <div id=\"panel\">
    <h3 style=\"margin: 0 0 10px 0;\">Shelf 3D Combos (Rotation-Dedup)</h3>
    <div class=\"row\">N=__N__, x=__X__, y=__Y__, h=__H__</div>
    <div class=\"row\">Unique combos: <b>__COUNT__</b></div>
    <div class=\"row\">
      <button id=\"prevBtn\">Prev</button>
      <button id=\"nextBtn\">Next</button>
      <button id=\"fitBtn\">Fit</button>
    </div>
    <div class=\"row\">
      <select id=\"comboSelect\"></select>
    </div>
    <div class=\"row mono\" id=\"status\" style=\"color:#b91c1c;\">Initializing viewer...</div>
    <div class=\"row mono\" id=\"info\"></div>
    <div class=\"row\" style=\"font-size:12px;color:#555;\">
      Left-drag: rotate | Wheel: zoom | Right-drag: pan
    </div>
  </div>
  <div id=\"viewer\"><canvas id=\"cv\"></canvas></div>
</div>

<script id=\"combo-data\" type=\"application/json\">__COMBOS_JSON__</script>
<script>
let combos = [];
const statusEl = document.getElementById('status');
function showStatus(msg, isError) {
  if (!statusEl) return;
  statusEl.style.color = isError ? '#b91c1c' : '#065f46';
  statusEl.textContent = msg || '';
}
try {
  const raw = document.getElementById('combo-data').textContent || '[]';
  combos = JSON.parse(raw);
} catch (err) {
  showStatus('Failed to parse combo JSON: ' + String(err), true);
}
window.addEventListener('error', function (e) {
  showStatus('JS error: ' + String(e.message) + ' @' + String(e.lineno) + ':' + String(e.colno), true);
});

const N = __N__, X = __X__, Y = __Y__, H = __H__;
const TOTAL_H = N * H;
const sideCorners = {
  front: ['FL', 'FR'],
  back: ['BL', 'BR'],
  left: ['FL', 'BL'],
  right: ['FR', 'BR']
};
const cornerXY = {
  FL: [0, 0],
  FR: [X, 0],
  BL: [0, Y],
  BR: [X, Y]
};

const cv = document.getElementById('cv');
const ctx = cv.getContext('2d');
const viewer = document.getElementById('viewer');

let yaw = -0.9;
let pitch = 0.55;
let zoom = 8.2;
let panX = 0;
let panY = 0;
let current = 0;

function fitView() {
  const w = Math.max(1, viewer.clientWidth);
  const h = Math.max(1, viewer.clientHeight);
  const modelSize = Math.max(X, Y, TOTAL_H, 1);
  zoom = Math.max(2.0, Math.min(40.0, Math.min(w, h) * 0.55 / modelSize));
  panX = 0;
  panY = 0;
}

function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  const w = viewer.clientWidth;
  const h = viewer.clientHeight;
  cv.width = Math.max(1, Math.floor(w * dpr));
  cv.height = Math.max(1, Math.floor(h * dpr));
  cv.style.width = w + 'px';
  cv.style.height = h + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  fitView();
  draw();
}

function rotatePoint(p) {
  const x0 = p[0] - X / 2;
  const y0 = p[1] - Y / 2;
  const z0 = p[2] - TOTAL_H / 2;

  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const x1 = x0 * cy - y0 * sy;
  const y1 = x0 * sy + y0 * cy;
  const z1 = z0;

  const cp = Math.cos(pitch), sp = Math.sin(pitch);
  const x2 = x1;
  const y2 = y1 * cp - z1 * sp;
  const z2 = y1 * sp + z1 * cp;
  return [x2, y2, z2];
}

function project(p) {
  const [x, y, z] = rotatePoint(p);
  const w = viewer.clientWidth;
  const h = viewer.clientHeight;
  const cx = w * 0.5 + panX;
  const cy = h * 0.5 + panY;
  return [cx + x * zoom, cy - y * zoom, z];
}

function buildRods(combo) {
  const rods = { FL: [], FR: [], BL: [], BR: [] };
  for (const c of ['FL', 'FR', 'BL', 'BR']) {
    const segs = [];
    for (let i = 0; i < combo.layers.length; i++) {
      if (combo.layers[i].rods.includes(c)) segs.push([i * H, (i + 1) * H]);
    }
    segs.sort((a, b) => a[0] - b[0]);
    if (!segs.length) continue;
    let a0 = segs[0][0], a1 = segs[0][1];
    for (let i = 1; i < segs.length; i++) {
      const b0 = segs[i][0], b1 = segs[i][1];
      if (Math.abs(a1 - b0) < 1e-9) a1 = b1;
      else { rods[c].push([a0, a1]); a0 = b0; a1 = b1; }
    }
    rods[c].push([a0, a1]);
  }
  return rods;
}

function panelQuad(side, z0, z1) {
  const c = sideCorners[side];
  const p0 = cornerXY[c[0]];
  const p1 = cornerXY[c[1]];
  return [
    [p0[0], p0[1], z0],
    [p1[0], p1[1], z0],
    [p1[0], p1[1], z1],
    [p0[0], p0[1], z1],
  ];
}

function drawFace(points3, fill, stroke) {
  const pts = points3.map(project);
  const zAvg = pts.reduce((s, p) => s + p[2], 0) / pts.length;
  return { pts, zAvg, fill, stroke };
}

function draw() {
  const w = viewer.clientWidth;
  const h = viewer.clientHeight;
  ctx.clearRect(0, 0, w, h);

  const combo = combos[current];
  if (!combo) return;

  const faces = [];

  for (let level = 1; level <= N; level++) {
    const z = level * H;
    faces.push(drawFace(
      [[0,0,z], [X,0,z], [X,Y,z], [0,Y,z]],
      'rgba(59,130,246,0.30)', 'rgba(30,64,175,0.90)'
    ));
  }

  for (let i = 0; i < combo.layers.length; i++) {
    const layer = combo.layers[i];
    const z0 = i * H;
    const z1 = (i + 1) * H;
    const alpha = 0.45;
    const red = 245 - (i % 4) * 8;
    const green = 158 - (i % 4) * 14;
    const blue = 11 + (i % 4) * 12;
    for (const s of layer.support_panels) {
      faces.push(drawFace(panelQuad(s, z0, z1), `rgba(${red},${green},${blue},${alpha})`, 'rgba(154,52,18,0.95)'));
    }
  }

  faces.sort((a, b) => a.zAvg - b.zAvg);
  for (const f of faces) {
    ctx.beginPath();
    ctx.moveTo(f.pts[0][0], f.pts[0][1]);
    for (let i = 1; i < f.pts.length; i++) ctx.lineTo(f.pts[i][0], f.pts[i][1]);
    ctx.closePath();
    ctx.fillStyle = f.fill;
    ctx.fill();
    ctx.strokeStyle = f.stroke;
    ctx.lineWidth = 1.5;
    ctx.stroke();
  }

  const rods = buildRods(combo);
  ctx.strokeStyle = 'rgba(17,24,39,1)';
  ctx.lineWidth = 3;
  for (const c of ['FL', 'FR', 'BL', 'BR']) {
    const xy = cornerXY[c];
    for (const seg of rods[c]) {
      const p0 = project([xy[0], xy[1], seg[0]]);
      const p1 = project([xy[0], xy[1], seg[1]]);
      ctx.beginPath();
      ctx.moveTo(p0[0], p0[1]);
      ctx.lineTo(p1[0], p1[1]);
      ctx.stroke();
    }
  }
}

function refreshInfo() {
  const combo = combos[current];
  if (!combo) {
    document.getElementById('info').textContent = '';
    return;
  }
  const lines = [
    combo.combo_id,
    combo.label,
    'equivalent_count=' + combo.equivalent_count
  ];
  for (let i = 0; i < combo.layers.length; i++) {
    const layer = combo.layers[i];
    lines.push(`L${i + 1} rods=` + JSON.stringify(layer.rods));
    lines.push(`L${i + 1} panels=` + JSON.stringify(layer.support_panels));
  }
  document.getElementById('info').textContent = lines.join('\\n');
}

function renderCurrent() {
  if (!combos.length) {
    showStatus('No combos available to render.', true);
    draw();
    return;
  }
  const sel = document.getElementById('comboSelect');
  sel.value = String(current);
  refreshInfo();
  draw();
}

try {
  const sel = document.getElementById('comboSelect');
  combos.forEach((c, idx) => {
    const op = document.createElement('option');
    op.value = String(idx);
    op.textContent = c.combo_id + '  (' + c.equivalent_count + ')  ' + c.label;
    sel.appendChild(op);
  });
  sel.addEventListener('change', () => {
    current = Number(sel.value);
    renderCurrent();
  });

  document.getElementById('prevBtn').addEventListener('click', () => {
    current = (current - 1 + combos.length) % combos.length;
    renderCurrent();
  });
  document.getElementById('nextBtn').addEventListener('click', () => {
    current = (current + 1) % combos.length;
    renderCurrent();
  });
  document.getElementById('fitBtn').addEventListener('click', () => {
    fitView();
    draw();
  });

  let dragging = false;
  let mode = 'rotate';
  let lastX = 0;
  let lastY = 0;
  cv.addEventListener('contextmenu', (e) => e.preventDefault());
  cv.addEventListener('mousedown', (e) => {
    dragging = true;
    mode = (e.button === 2) ? 'pan' : 'rotate';
    lastX = e.clientX;
    lastY = e.clientY;
  });
  window.addEventListener('mouseup', () => dragging = false);
  window.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    const dx = e.clientX - lastX;
    const dy = e.clientY - lastY;
    lastX = e.clientX;
    lastY = e.clientY;
    if (mode === 'rotate') {
      yaw += dx * 0.008;
      pitch += dy * 0.008;
      pitch = Math.max(-1.4, Math.min(1.4, pitch));
    } else {
      panX += dx;
      panY += dy;
    }
    draw();
  });
  cv.addEventListener('wheel', (e) => {
    e.preventDefault();
    const k = Math.exp(-e.deltaY * 0.0015);
    zoom = Math.max(2.0, Math.min(40.0, zoom * k));
    draw();
  }, { passive: false });

  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();
  renderCurrent();
  showStatus('Viewer ready. combos=' + combos.length, false);
} catch (err) {
  showStatus('Viewer init failed: ' + String(err), true);
}
</script>
</body>
</html>
""".replace("__COMBOS_JSON__", combos_json).replace("__COUNT__", str(len(items))).replace("__N__", str(n)).replace(
        "__X__", fmt_num(x)
    ).replace("__Y__", fmt_num(y)).replace("__H__", fmt_num(h))


def main() -> None:
    args = parse_args()
    out_dir = resolve_output_dir(args.layers, args.x, args.y, args.h, args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for old in out_dir.glob("CASE-*.obj"):
        old.unlink()
    for old in out_dir.glob("CASE-*.png"):
        old.unlink()

    layer_patterns = build_layer_patterns()
    all_combos = [
        Combo(layers=layers)
        for layers in product(layer_patterns, repeat=args.layers)
    ]

    groups: dict[ComboKey, list[Combo]] = {}
    for combo in all_combos:
        key = canonical_key_under_rotation(combo)
        groups.setdefault(key, []).append(combo)

    canonical_keys = sorted(groups.keys())
    unique_items: list[dict] = []

    for idx, key in enumerate(canonical_keys, start=1):
        combo = key_to_combo(key)
        group_members = groups[key]
        combo_id = f"CASE-{idx:02d}"
        obj_name = f"{combo_id}.obj"
        png_name = f"{combo_id}.png"
        write_obj(combo, out_dir / obj_name, args.x, args.y, args.h)
        draw_preview_png(combo, out_dir / png_name, f"{combo_id} {combo_label(combo)}", args.x, args.y, args.h)

        unique_items.append(
            {
                "combo_id": combo_id,
                "label": combo_label(combo),
                "equivalent_count": len(group_members),
                "equivalent_members": [combo_label(item) for item in sorted(group_members, key=combo_key)],
                "layers": [
                    {
                        "rods": list(layer.rods),
                        "support_panels": list(layer.side_panels),
                        "open_sides": open_sides(layer.side_panels),
                    }
                    for layer in combo.layers
                ],
                "obj": obj_name,
                "preview_png": png_name,
            }
        )

    thumb_w, thumb_h = 260, 190
    cols = 5
    rows = max(1, math.ceil(len(unique_items) / cols))
    sheet = Image.new("RGB", (thumb_w * cols, thumb_h * rows), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, item in enumerate(unique_items):
        r, c = divmod(idx, cols)
        x0, y0 = c * thumb_w, r * thumb_h
        img = Image.open(out_dir / item["preview_png"]).convert("RGB").resize((thumb_w, thumb_h - 20))
        sheet.paste(img, (x0, y0 + 20))
        draw.text((x0 + 8, y0 + 3), f"{item['combo_id']} ({item['equivalent_count']})", fill=(0, 0, 0))
    sheet.save(out_dir / "ALL_COMBOS_3D.png")

    summary = {
        "assumptions": {
            "N": args.layers,
            "x": args.x,
            "y": args.y,
            "h": args.h,
            "side_panel_height_max": args.h,
            "rod_length_unlimited": True,
            "payload_ignored": True,
            "opening_ignored": True,
        },
        "rule_interpretation": {
            "single_layer_patterns": len(layer_patterns),
            "raw_total_for_N": f"{len(layer_patterns)}^{args.layers} = {len(all_combos)}",
            "dedup": "rotation equivalence around vertical axis (0/90/180/270 deg)",
            "R2": "per layer E_total=4 with E(rod)=1 and E(panel)=2, shared panel corner counted once; full-corner coverage",
            "R4_note": "90-degree panel-panel connection is allowed but does not relax corner support completeness",
            "R7": "per layer at least one side open",
        },
        "raw_combo_count": len(all_combos),
        "unique_combo_count_after_rotation_dedup": len(unique_items),
        "valid_combos": unique_items,
        "overview_png": "ALL_COMBOS_3D.png",
        "interactive_html": "interactive_3d.html",
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out_dir / "interactive_3d.html").write_text(
        build_interactive_html(unique_items, args.layers, args.x, args.y, args.h),
        encoding="utf-8",
    )

    try:
        out_dir_display = str(out_dir.relative_to(ROOT))
    except ValueError:
        out_dir_display = str(out_dir)

    print(
        json.dumps(
            {
                "single_layer_patterns": len(layer_patterns),
                "raw_combo_count": len(all_combos),
                "unique_combo_count": len(unique_items),
                "output_dir": out_dir_display,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
