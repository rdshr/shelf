from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "diagrams" / "N2_x30_y30_h30_panelmax30"

N = 2
X = 30.0
Y = 30.0
H = 30.0

CORNERS = ("FL", "FR", "BR", "BL")
SIDES = ("front", "right", "back", "left")
CORNER_XY = {
    "FL": (0.0, 0.0),
    "FR": (X, 0.0),
    "BL": (0.0, Y),
    "BR": (X, Y),
}
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
    layer1: LayerPattern
    layer2: LayerPattern


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
    # R7: at least one side open
    if len(open_sides(side_panels)) < 1:
        return False
    # Side support panel height <= h is enforced by generation model (one-layer panel).
    return True


def rotate_layer_pattern_90(pattern: LayerPattern) -> LayerPattern:
    rods = tuple(sorted(ROTATE_CORNER_90[item] for item in pattern.rods))
    side_panels = tuple(sorted(ROTATE_SIDE_90[item] for item in pattern.side_panels))
    return LayerPattern(rods=rods, side_panels=side_panels)


def rotate_combo_90(combo: Combo) -> Combo:
    return Combo(
        layer1=rotate_layer_pattern_90(combo.layer1),
        layer2=rotate_layer_pattern_90(combo.layer2),
    )


def combo_key(combo: Combo) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    return (
        combo.layer1.rods,
        combo.layer1.side_panels,
        combo.layer2.rods,
        combo.layer2.side_panels,
    )


def key_to_combo(key: tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]) -> Combo:
    return Combo(
        layer1=LayerPattern(rods=key[0], side_panels=key[1]),
        layer2=LayerPattern(rods=key[2], side_panels=key[3]),
    )


def canonical_key_under_rotation(combo: Combo) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    cands: list[tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = []
    cur = combo
    for _ in range(4):
        cands.append(combo_key(cur))
        cur = rotate_combo_90(cur)
    return min(cands)


def combo_label(combo: Combo) -> str:
    r1 = "-".join(combo.layer1.rods) if combo.layer1.rods else "none"
    p1 = "-".join(combo.layer1.side_panels) if combo.layer1.side_panels else "none"
    r2 = "-".join(combo.layer2.rods) if combo.layer2.rods else "none"
    p2 = "-".join(combo.layer2.side_panels) if combo.layer2.side_panels else "none"
    return f"L1(R:{r1}|P:{p1}) L2(R:{r2}|P:{p2})"


def build_layer_patterns() -> list[LayerPattern]:
    patterns: list[LayerPattern] = []
    for rods in powerset(CORNERS):
        for side_panels in powerset(SIDES):
            rods_sorted = tuple(sorted(rods))
            side_panels_sorted = tuple(sorted(side_panels))
            if valid_layer_pattern(rods_sorted, side_panels_sorted):
                patterns.append(LayerPattern(rods=rods_sorted, side_panels=side_panels_sorted))
    return sorted(set(patterns), key=lambda item: (len(item.rods), len(item.side_panels), item.rods, item.side_panels))


def merge_corner_rod_segments(combo: Combo) -> dict[str, list[tuple[float, float]]]:
    merged: dict[str, list[tuple[float, float]]] = {corner: [] for corner in CORNERS}
    for corner in CORNERS:
        segs: list[tuple[float, float]] = []
        if corner in combo.layer1.rods:
            segs.append((0.0, H))
        if corner in combo.layer2.rods:
            segs.append((H, 2 * H))
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


def side_panel_quads(combo: Combo) -> list[tuple[list[tuple[float, float, float]], str]]:
    quads: list[tuple[list[tuple[float, float, float]], str]] = []
    for side in combo.layer1.side_panels:
        c1, c2 = SIDE_CORNERS[side]
        x1, y1 = CORNER_XY[c1]
        x2, y2 = CORNER_XY[c2]
        quads.append(([(x1, y1, 0.0), (x2, y2, 0.0), (x2, y2, H), (x1, y1, H)], "L1"))
    for side in combo.layer2.side_panels:
        c1, c2 = SIDE_CORNERS[side]
        x1, y1 = CORNER_XY[c1]
        x2, y2 = CORNER_XY[c2]
        quads.append(([(x1, y1, H), (x2, y2, H), (x2, y2, 2 * H), (x1, y1, 2 * H)], "L2"))
    return quads


def load_board_quads() -> list[list[tuple[float, float, float]]]:
    return [
        [(0.0, 0.0, H), (X, 0.0, H), (X, Y, H), (0.0, Y, H)],
        [(0.0, 0.0, 2 * H), (X, 0.0, 2 * H), (X, Y, 2 * H), (0.0, Y, 2 * H)],
    ]


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


def draw_preview_png(combo: Combo, out_path: Path, title: str) -> None:
    side_quads = side_panel_quads(combo)
    board_quads = load_board_quads()
    rods = merge_corner_rod_segments(combo)

    pts: list[tuple[float, float]] = []
    for quad in board_quads:
        pts.extend(project_point(p) for p in quad)
    for quad, _ in side_quads:
        pts.extend(project_point(p) for p in quad)
    for corner in CORNERS:
        x0, y0 = CORNER_XY[corner]
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

    for quad, level in side_quads:
        fill = (245, 158, 11, 130) if level == "L1" else (249, 115, 22, 130)
        draw.polygon([to_canvas(p) for p in quad], fill=fill, outline=(154, 52, 18, 255), width=2)
    for quad in board_quads:
        draw.polygon([to_canvas(p) for p in quad], fill=(59, 130, 246, 95), outline=(30, 64, 175, 255), width=2)
    for corner in CORNERS:
        x0, y0 = CORNER_XY[corner]
        for z0, z1 in rods[corner]:
            draw.line([to_canvas((x0, y0, z0)), to_canvas((x0, y0, z1))], fill=(17, 24, 39, 255), width=5)

    draw.text((16, 12), title, fill=(0, 0, 0, 255))
    draw.text(
        (16, 34),
        f"L1 open={open_sides(combo.layer1.side_panels)} L2 open={open_sides(combo.layer2.side_panels)}",
        fill=(0, 0, 0, 255),
    )
    img.save(out_path)


def write_obj(combo: Combo, out_path: Path) -> None:
    vertices: list[tuple[float, float, float]] = []
    lines: list[tuple[int, int]] = []
    faces: list[tuple[int, int, int, int]] = []

    rods = merge_corner_rod_segments(combo)
    for corner in CORNERS:
        x0, y0 = CORNER_XY[corner]
        for z0, z1 in rods[corner]:
            i1 = len(vertices) + 1
            vertices.append((x0, y0, z0))
            i2 = len(vertices) + 1
            vertices.append((x0, y0, z1))
            lines.append((i1, i2))

    for quad, _ in side_panel_quads(combo):
        a = len(vertices) + 1
        vertices.append(quad[0])
        b = len(vertices) + 1
        vertices.append(quad[1])
        c = len(vertices) + 1
        vertices.append(quad[2])
        d = len(vertices) + 1
        vertices.append(quad[3])
        faces.append((a, b, c, d))

    for quad in load_board_quads():
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


def build_interactive_html(items: list[dict]) -> str:
    combos_json = json.dumps(items, ensure_ascii=False)
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
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
      grid-template-columns: 360px 1fr;
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
<div id="app">
  <div id="panel">
    <h3 style="margin: 0 0 10px 0;">Shelf 3D Combos (Rotation-Dedup)</h3>
    <div class="row">N=2, x=30, y=30, h=30</div>
    <div class="row">Unique combos: <b>__COUNT__</b></div>
    <div class="row">
      <button id="prevBtn">Prev</button>
      <button id="nextBtn">Next</button>
    </div>
    <div class="row">
      <select id="comboSelect"></select>
    </div>
    <div class="row mono" id="info"></div>
    <div class="row" style="font-size:12px;color:#555;">
      Left-drag: rotate | Wheel: zoom | Right-drag: pan
    </div>
  </div>
  <div id="viewer"><canvas id="cv"></canvas></div>
</div>

<script>
const combos = __COMBOS__;
const X = 30, Y = 30, H = 30;
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

function resizeCanvas() {
  const dpr = window.devicePixelRatio || 1;
  const w = viewer.clientWidth;
  const h = viewer.clientHeight;
  cv.width = Math.max(1, Math.floor(w * dpr));
  cv.height = Math.max(1, Math.floor(h * dpr));
  cv.style.width = w + 'px';
  cv.style.height = h + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  draw();
}

function rotatePoint(p) {
  // shift origin to shelf center on xy
  const x0 = p[0] - X / 2;
  const y0 = p[1] - Y / 2;
  const z0 = p[2] - H;

  // yaw around z
  const cy = Math.cos(yaw), sy = Math.sin(yaw);
  const x1 = x0 * cy - y0 * sy;
  const y1 = x0 * sy + y0 * cy;
  const z1 = z0;

  // pitch around x
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
    if (combo.layer1.rods.includes(c)) segs.push([0, H]);
    if (combo.layer2.rods.includes(c)) segs.push([H, 2 * H]);
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

  // load boards
  faces.push(drawFace(
    [[0,0,H], [X,0,H], [X,Y,H], [0,Y,H]],
    'rgba(59,130,246,0.30)', 'rgba(30,64,175,0.90)'
  ));
  faces.push(drawFace(
    [[0,0,2*H], [X,0,2*H], [X,Y,2*H], [0,Y,2*H]],
    'rgba(59,130,246,0.30)', 'rgba(30,64,175,0.90)'
  ));

  // side support panels
  for (const s of combo.layer1.support_panels) {
    faces.push(drawFace(panelQuad(s, 0, H), 'rgba(245,158,11,0.45)', 'rgba(154,52,18,0.95)'));
  }
  for (const s of combo.layer2.support_panels) {
    faces.push(drawFace(panelQuad(s, H, 2*H), 'rgba(249,115,22,0.45)', 'rgba(154,52,18,0.95)'));
  }

  // painter's order: far to near
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

  // rods
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
  document.getElementById('info').textContent =
    combo.combo_id + '\\n' +
    combo.label + '\\n' +
    'equivalent_count=' + combo.equivalent_count + '\\n' +
    'L1 rods=' + JSON.stringify(combo.layer1.rods) + '\\n' +
    'L1 panels=' + JSON.stringify(combo.layer1.support_panels) + '\\n' +
    'L2 rods=' + JSON.stringify(combo.layer2.rods) + '\\n' +
    'L2 panels=' + JSON.stringify(combo.layer2.support_panels);
}

function renderCurrent() {
  const sel = document.getElementById('comboSelect');
  sel.value = String(current);
  refreshInfo();
  draw();
}

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
</script>
</body>
</html>
""".replace("__COMBOS__", combos_json).replace("__COUNT__", str(len(items)))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for old in OUT_DIR.glob("CASE-*.obj"):
        old.unlink()
    for old in OUT_DIR.glob("CASE-*.png"):
        old.unlink()

    layer_patterns = build_layer_patterns()
    all_combos = [Combo(layer1=l1, layer2=l2) for l1 in layer_patterns for l2 in layer_patterns]

    groups: dict[
        tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]],
        list[Combo],
    ] = {}
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
        write_obj(combo, OUT_DIR / obj_name)
        draw_preview_png(combo, OUT_DIR / png_name, f"{combo_id} {combo_label(combo)}")

        unique_items.append(
            {
                "combo_id": combo_id,
                "label": combo_label(combo),
                "equivalent_count": len(group_members),
                "equivalent_members": [combo_label(item) for item in sorted(group_members, key=combo_key)],
                "layer1": {
                    "rods": list(combo.layer1.rods),
                    "support_panels": list(combo.layer1.side_panels),
                    "open_sides": open_sides(combo.layer1.side_panels),
                },
                "layer2": {
                    "rods": list(combo.layer2.rods),
                    "support_panels": list(combo.layer2.side_panels),
                    "open_sides": open_sides(combo.layer2.side_panels),
                },
                "obj": obj_name,
                "preview_png": png_name,
            }
        )

    thumb_w, thumb_h = 260, 190
    cols = 5
    rows = math.ceil(len(unique_items) / cols)
    sheet = Image.new("RGB", (thumb_w * cols, thumb_h * rows), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, item in enumerate(unique_items):
        r, c = divmod(idx, cols)
        x0, y0 = c * thumb_w, r * thumb_h
        img = Image.open(OUT_DIR / item["preview_png"]).convert("RGB").resize((thumb_w, thumb_h - 20))
        sheet.paste(img, (x0, y0 + 20))
        draw.text((x0 + 8, y0 + 3), f"{item['combo_id']} ({item['equivalent_count']})", fill=(0, 0, 0))
    sheet.save(OUT_DIR / "ALL_COMBOS_3D.png")

    summary = {
        "assumptions": {
            "N": N,
            "x": X,
            "y": Y,
            "h": H,
            "side_panel_height_max": H,
            "rod_length_unlimited": True,
            "payload_ignored": True,
            "opening_ignored": True,
        },
        "rule_interpretation": {
            "single_layer_patterns": len(layer_patterns),
            "raw_total_for_N2": f"{len(layer_patterns)} x {len(layer_patterns)} = {len(all_combos)}",
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
    (OUT_DIR / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT_DIR / "interactive_3d.html").write_text(build_interactive_html(unique_items), encoding="utf-8")

    print(
        json.dumps(
            {
                "single_layer_patterns": len(layer_patterns),
                "raw_combo_count": len(all_combos),
                "unique_combo_count": len(unique_items),
                "output_dir": str(OUT_DIR.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
