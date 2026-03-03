from __future__ import annotations

from array import array
from dataclasses import asdict, dataclass
from functools import lru_cache
import gzip
import itertools
import math
from pathlib import Path
import pickle
import time


@dataclass(frozen=True)
class SearchSpace:
    slots_x: int
    slots_y: int
    slots_z: int
    panel_length: float
    panel_width: float
    rod_length: float
    dedupe_symmetry: bool = True


@dataclass(frozen=True)
class BoundaryConstraint:
    max_layers_n: int
    baseline_gain: float


@dataclass(frozen=True)
class PatternStat:
    cells: tuple[tuple[int, int], ...]
    cell_count: int
    edge_count: int
    support_mask: int


@dataclass(frozen=True)
class RuleResult:
    r1_no_stack: bool
    r2_no_penetration: bool
    r3_min_counts: bool
    r4_connector_only: bool
    r5_orthogonal: bool
    r6_parallel_or_collinear: bool
    r7_endpoint_only: bool
    r8_single_connected: bool
    r9_top_capped: bool
    r10_panel_four_corner_supported: bool

    @property
    def passed(self) -> bool:
        return all(asdict(self).values())


@dataclass(frozen=True)
class DesignMetrics:
    footprint_a: float
    panel_area_total: float
    panel_area_above: float
    usable_area_total: float
    avg_space_s_per_layer: float
    coverage_mean: float
    coverage_std: float
    open_edge_ratio: float
    accessibility_score: float
    complexity_penalty: float
    efficiency_current: float
    efficiency_baseline: float
    gain_ratio: float
    rod_segments: int
    connector_points: int
    panel_count: int


def default_search_space() -> SearchSpace:
    return SearchSpace(
        slots_x=3,
        slots_y=3,
        slots_z=3,
        panel_length=1.0,
        panel_width=1.0,
        rod_length=1.0,
        dedupe_symmetry=True,
    )


def default_boundary() -> BoundaryConstraint:
    return BoundaryConstraint(
        max_layers_n=3,
        baseline_gain=1.0,
    )


FAMILY_META: tuple[tuple[str, str], ...] = (
    ("point_ground", "点式-地面主导"),
    ("point_mixed", "点式-混合提升"),
    ("point_elevated", "点式-上层主导"),
    ("band_ground", "带式-地面主导"),
    ("band_mixed", "带式-混合提升"),
    ("band_elevated", "带式-上层主导"),
    ("plane_ground", "面式-地面主导"),
    ("plane_mixed", "面式-混合提升"),
    ("plane_elevated", "面式-上层主导"),
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_CACHE_DIR = REPO_ROOT / "data"
CATALOG_CACHE_PATH = CATALOG_CACHE_DIR / "catalog_3x3x3_v2.pkl.gz"
CATALOG_CACHE_VERSION = 4
ENGINE_VERSION = "2026-03-03-r10-corner-v1"
ROD_SEGMENT_RULE = "trim_to_highest_attached_panel_level"


def list_family_meta() -> list[dict[str, str]]:
    return [{"key": key, "label": label} for key, label in FAMILY_META]


def _family_key_label(
    *,
    footprint_cells: int,
    panel_ground_count: int,
    panel_above_count: int,
) -> tuple[str, str]:
    if footprint_cells <= 2:
        plane_key = "point"
        plane_label = "点式"
    elif footprint_cells <= 5:
        plane_key = "band"
        plane_label = "带式"
    else:
        plane_key = "plane"
        plane_label = "面式"

    if panel_above_count == 0:
        elev_key = "ground"
        elev_label = "地面主导"
    elif panel_above_count <= panel_ground_count:
        elev_key = "mixed"
        elev_label = "混合提升"
    else:
        elev_key = "elevated"
        elev_label = "上层主导"

    return f"{plane_key}_{elev_key}", f"{plane_label}-{elev_label}"


def _status_match(goal_passed: bool, rule_passed: bool, boundary_passed: bool, status: str) -> bool:
    if status == "goal_pass":
        return goal_passed
    if status == "goal_fail":
        return not goal_passed
    if status == "rule_fail":
        return not rule_passed
    if status == "boundary_fail":
        return rule_passed and (not boundary_passed)
    return True


def _symmetry_transforms(width: int, height: int) -> list[str]:
    if width == height:
        return [
            "identity",
            "rot90",
            "rot180",
            "rot270",
            "flip_x",
            "flip_y",
            "diag",
            "anti_diag",
        ]
    return ["identity", "rot180", "flip_x", "flip_y"]


def _transform_xy(x: int, y: int, width: int, height: int, transform: str) -> tuple[int, int]:
    if transform == "identity":
        return x, y
    if transform == "rot90":
        return height - 1 - y, x
    if transform == "rot180":
        return width - 1 - x, height - 1 - y
    if transform == "rot270":
        return y, width - 1 - x
    if transform == "flip_x":
        return width - 1 - x, y
    if transform == "flip_y":
        return x, height - 1 - y
    if transform == "diag":
        return y, x
    if transform == "anti_diag":
        return width - 1 - y, height - 1 - x
    return x, y


def _apply_transform(mask: int, width: int, height: int, transform: str) -> int:
    transformed = 0
    for iy in range(height):
        for ix in range(width):
            bit = iy * width + ix
            if not ((mask >> bit) & 1):
                continue
            nx, ny = _transform_xy(ix, iy, width, height, transform)
            nbit = ny * width + nx
            transformed |= 1 << nbit
    return transformed


def _canonical_mask(mask: int, width: int, height: int) -> int:
    candidates = [
        _apply_transform(mask=mask, width=width, height=height, transform=item)
        for item in _symmetry_transforms(width, height)
    ]
    return min(candidates)


@lru_cache(maxsize=128)
def _layer_patterns(width: int, height: int, dedupe_symmetry: bool) -> tuple[int, ...]:
    total_cells = width * height
    if total_cells <= 0:
        return (0,)

    if total_cells > 22:
        raise ValueError(
            "位点过大，当前穷举复杂度过高。"
            "请降低X/Y位点数量（建议 width*height <= 22）。"
        )

    if not dedupe_symmetry:
        return tuple(range(1 << total_cells))

    canonical_set: set[int] = set()
    for mask in range(1 << total_cells):
        canonical_set.add(_canonical_mask(mask=mask, width=width, height=height))
    return tuple(sorted(canonical_set))


@lru_cache(maxsize=128)
def _pattern_stats(width: int, height: int, dedupe_symmetry: bool) -> dict[int, PatternStat]:
    patterns = _layer_patterns(width=width, height=height, dedupe_symmetry=dedupe_symmetry)
    edge_cells = {
        (ix, iy)
        for ix in range(width)
        for iy in range(height)
        if ix in (0, width - 1) or iy in (0, height - 1)
    }

    stats: dict[int, PatternStat] = {}
    for mask in patterns:
        cells: list[tuple[int, int]] = []
        edge_count = 0
        support_mask = 0

        for bit in range(width * height):
            if not ((mask >> bit) & 1):
                continue
            ix = bit % width
            iy = bit // width
            cells.append((ix, iy))
            if (ix, iy) in edge_cells:
                edge_count += 1

            corners = ((ix, iy), (ix + 1, iy), (ix, iy + 1), (ix + 1, iy + 1))
            for cx, cy in corners:
                support_bit = cy * (width + 1) + cx
                support_mask |= 1 << support_bit

        stats[mask] = PatternStat(
            cells=tuple(cells),
            cell_count=len(cells),
            edge_count=edge_count,
            support_mask=support_mask,
        )

    return stats


def _support_points_from_mask(support_mask: int, width: int, height: int) -> list[list[int]]:
    points: list[list[int]] = []
    grid_w = width + 1
    grid_h = height + 1
    for bit in range(grid_w * grid_h):
        if not ((support_mask >> bit) & 1):
            continue
        ix = bit % grid_w
        iy = bit // grid_w
        points.append([ix, iy])
    return points


def _panel_support_bits(ix: int, iy: int, width: int) -> tuple[int, int, int, int]:
    grid_w = width + 1
    return (
        iy * grid_w + ix,
        iy * grid_w + (ix + 1),
        (iy + 1) * grid_w + ix,
        (iy + 1) * grid_w + (ix + 1),
    )


def _rod_profile_from_masks(
    masks: tuple[int, ...],
    *,
    pattern_stats: dict[int, PatternStat],
    width: int,
    height: int,
) -> tuple[int, dict[int, int], int, int]:
    layer_support_masks = tuple(pattern_stats[mask].support_mask for mask in masks)
    max_support_bits = (width + 1) * (height + 1)

    top_level_by_support: dict[int, int] = {}
    for level, support_mask_at_level in enumerate(layer_support_masks):
        for bit in range(max_support_bits):
            if not ((support_mask_at_level >> bit) & 1):
                continue
            current = top_level_by_support.get(bit, -1)
            if level > current:
                top_level_by_support[bit] = level

    support_mask = 0
    rod_segments = 0
    connector_points = 0
    for bit, top_level in top_level_by_support.items():
        support_mask |= 1 << bit
        # 杆只保留到该列最高有效板层，禁止向上冗余延伸。
        rod_segments += max(0, top_level)
        connector_points += top_level + 1

    return support_mask, top_level_by_support, rod_segments, connector_points


def _rod_columns_from_top_levels(top_level_by_support: dict[int, int], width: int) -> list[list[int]]:
    columns: list[list[int]] = []
    grid_w = width + 1
    for bit, top_level in sorted(top_level_by_support.items()):
        ix = bit % grid_w
        iy = bit // grid_w
        columns.append([ix, iy, int(top_level)])
    return columns


def _r10_panel_four_corner_supported(level_support_masks: tuple[int, ...]) -> bool:
    if not level_support_masks:
        return True
    ground_support_mask = level_support_masks[0]
    support_above_mask = 0
    for item in level_support_masks[1:]:
        support_above_mask |= item
    # 方案B：所有层板四角都必须连杆；等价为0层角点必须被上层杆系覆盖。
    return (ground_support_mask & ~support_above_mask) == 0


def _is_single_connected_system(
    masks: tuple[int, ...],
    pattern_stats: dict[int, PatternStat],
    *,
    width: int,
    height: int,
) -> bool:
    support_union = 0
    for mask in masks:
        support_union |= pattern_stats[mask].support_mask

    if support_union == 0:
        return False

    max_bits = (width + 1) * (height + 1)
    parent: dict[int, int] = {}

    for bit in range(max_bits):
        if (support_union >> bit) & 1:
            parent[bit] = bit

    def find(item: int) -> int:
        node = item
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    def union(a: int, b: int) -> None:
        root_a = find(a)
        root_b = find(b)
        if root_a != root_b:
            parent[root_b] = root_a

    for mask in masks:
        for ix, iy in pattern_stats[mask].cells:
            corner_bits = _panel_support_bits(ix=ix, iy=iy, width=width)
            anchor = corner_bits[0]
            for bit in corner_bits[1:]:
                union(anchor, bit)

    roots = {find(bit) for bit in parent}
    return len(roots) == 1


def _shift_mask(mask: int, width: int, height: int, dx: int, dy: int) -> int:
    shifted = 0
    for bit in range(width * height):
        if not ((mask >> bit) & 1):
            continue
        x = bit % width
        y = bit // width
        nx = x + dx
        ny = y + dy
        if nx < 0 or nx >= width or ny < 0 or ny >= height:
            raise ValueError("mask shift out of bounds")
        shifted |= 1 << (ny * width + nx)
    return shifted


def _normalize_sequence_translation(
    masks: tuple[int, ...],
    *,
    width: int,
    height: int,
) -> tuple[int, ...]:
    min_x = width
    min_y = height
    has_cell = False

    for mask in masks:
        for bit in range(width * height):
            if not ((mask >> bit) & 1):
                continue
            x = bit % width
            y = bit // width
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            has_cell = True

    if not has_cell:
        return masks
    if min_x == 0 and min_y == 0:
        return masks

    dx = -min_x
    dy = -min_y
    return tuple(_shift_mask(mask, width, height, dx, dy) for mask in masks)


def _canonical_sequence_signature(
    masks: tuple[int, ...],
    *,
    width: int,
    height: int,
    enable_symmetry: bool,
) -> tuple[int, ...]:
    transforms = _symmetry_transforms(width, height) if enable_symmetry else ["identity"]
    candidates: list[tuple[int, ...]] = []

    for transform in transforms:
        transformed = tuple(
            _apply_transform(mask=mask, width=width, height=height, transform=transform) for mask in masks
        )
        normalized = _normalize_sequence_translation(transformed, width=width, height=height)
        candidates.append(normalized)

    return min(candidates)


def _panel_cells_from_masks(
    masks: tuple[int, ...],
    pattern_stats: dict[int, PatternStat],
) -> list[list[int]]:
    cells: list[list[int]] = []
    for level, mask in enumerate(masks, start=0):
        for ix, iy in pattern_stats[mask].cells:
            cells.append([level, ix, iy])
    return cells


def _cells_from_mask(mask: int, width: int, height: int) -> list[tuple[int, int]]:
    cells: list[tuple[int, int]] = []
    for bit in range(width * height):
        if not ((mask >> bit) & 1):
            continue
        cells.append((bit % width, bit // width))
    return cells


def _sequence_from_flat(flat_data: array, index: int) -> tuple[int, int, int]:
    base = index * 3
    return flat_data[base], flat_data[base + 1], flat_data[base + 2]


def _is_fixed_3x3x3_space(space: SearchSpace) -> bool:
    return (
        space.slots_x == 3
        and space.slots_y == 3
        and space.slots_z == 3
        and abs(space.panel_length - 1.0) < 1e-9
        and abs(space.panel_width - 1.0) < 1e-9
        and abs(space.rod_length - 1.0) < 1e-9
        and space.dedupe_symmetry
    )


def _support_mask_lookup(width: int, height: int) -> dict[int, int]:
    lookup: dict[int, int] = {0: 0}
    for cell_mask in range(1, 1 << (width * height)):
        support = 0
        for ix, iy in _cells_from_mask(cell_mask, width=width, height=height):
            corners = ((ix, iy), (ix + 1, iy), (ix, iy + 1), (ix + 1, iy + 1))
            for cx, cy in corners:
                support |= 1 << (cy * (width + 1) + cx)
        lookup[cell_mask] = support
    return lookup


def _single_connected_lookup(width: int, height: int) -> dict[int, bool]:
    pattern_stats = _pattern_stats(width=width, height=height, dedupe_symmetry=False)
    lookup: dict[int, bool] = {0: False}
    for cell_mask in range(1, 1 << (width * height)):
        lookup[cell_mask] = _is_single_connected_system(
            (cell_mask,),
            pattern_stats,
            width=width,
            height=height,
        )
    return lookup


def _family_code_map() -> tuple[dict[str, int], dict[int, tuple[str, str]]]:
    key_to_code = {key: index for index, (key, _label) in enumerate(FAMILY_META)}
    code_to_meta = {index: item for index, item in enumerate(FAMILY_META)}
    return key_to_code, code_to_meta


@lru_cache(maxsize=1)
def _load_or_build_fixed_cache() -> dict[str, object]:
    if CATALOG_CACHE_PATH.exists():
        with gzip.open(CATALOG_CACHE_PATH, "rb") as fp:
            payload = pickle.load(fp)
        if payload.get("version") == CATALOG_CACHE_VERSION:
            return payload

    payload = _build_fixed_cache_payload()
    CATALOG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with gzip.open(CATALOG_CACHE_PATH, "wb") as fp:
        pickle.dump(payload, fp, protocol=pickle.HIGHEST_PROTOCOL)
    return payload


def _build_fixed_cache_payload() -> dict[str, object]:
    width = 3
    height = 3
    levels = 3

    patterns = _layer_patterns(width=width, height=height, dedupe_symmetry=True)
    connected_lookup = _single_connected_lookup(width=width, height=height)
    seen_signatures: set[tuple[int, ...]] = set()
    flat_sequences = array("H")
    family_codes = array("B")

    key_to_code, _code_to_meta = _family_code_map()
    duplicate_removed = 0
    r8_filtered_removed = 0
    raw_sequence_total = 0

    for sequence in itertools.product(patterns, repeat=levels):
        raw_sequence_total += 1
        signature = _canonical_sequence_signature(
            sequence,
            width=width,
            height=height,
            enable_symmetry=True,
        )
        if signature in seen_signatures:
            duplicate_removed += 1
            continue
        seen_signatures.add(signature)

        m0, m1, m2 = signature
        union_mask = m0 | m1 | m2
        if not connected_lookup[union_mask]:
            r8_filtered_removed += 1
            continue

        footprint_cells = union_mask.bit_count()
        panel_ground_count = m0.bit_count()
        panel_above_count = m1.bit_count() + m2.bit_count()
        family_key, _family_label = _family_key_label(
            footprint_cells=footprint_cells,
            panel_ground_count=panel_ground_count,
            panel_above_count=panel_above_count,
        )

        flat_sequences.extend((m0, m1, m2))
        family_codes.append(key_to_code[family_key])

    return {
        "version": CATALOG_CACHE_VERSION,
        "engine_version": ENGINE_VERSION,
        "rod_segment_rule": ROD_SEGMENT_RULE,
        "space": {
            "slots_x": 3,
            "slots_y": 3,
            "slots_z": 3,
            "panel_length": 1.0,
            "panel_width": 1.0,
            "rod_length": 1.0,
            "dedupe_symmetry": True,
        },
        "raw_sequence_total": raw_sequence_total,
        "duplicate_removed": duplicate_removed,
        "r8_filtered_removed": r8_filtered_removed,
        "sequence_count": len(flat_sequences) // 3,
        "flat_sequences": flat_sequences,
        "family_codes": family_codes,
    }

def _evaluate_masks(
    masks: tuple[int, ...],
    *,
    space: SearchSpace,
    boundary: BoundaryConstraint,
    pattern_stats: dict[int, PatternStat],
    edge_cells_per_layer: int,
) -> tuple[str, str, RuleResult, bool, bool, tuple[str, ...], DesignMetrics, int, tuple[float, ...]]:
    layer_counts: list[int] = []
    occupied_cells: set[tuple[int, int]] = set()
    edge_occupied = 0

    for mask in masks:
        stat = pattern_stats[mask]
        layer_counts.append(stat.cell_count)
        occupied_cells.update(stat.cells)
        edge_occupied += stat.edge_count

    panel_area_per_piece = space.panel_length * space.panel_width
    panel_count = sum(layer_counts)
    layer_area_sums = tuple(round(count * panel_area_per_piece, 6) for count in layer_counts)
    panel_ground_count = layer_counts[0] if layer_counts else 0
    panel_above_count = panel_count - panel_ground_count

    level_support_masks = tuple(pattern_stats[mask].support_mask for mask in masks)
    support_mask, top_level_by_support, rod_segments, connector_points = _rod_profile_from_masks(
        masks,
        pattern_stats=pattern_stats,
        width=space.slots_x,
        height=space.slots_y,
    )

    footprint_a = len(occupied_cells) * panel_area_per_piece
    panel_area_total = panel_count * panel_area_per_piece
    panel_area_above = panel_above_count * panel_area_per_piece
    usable_area_total = footprint_a + panel_area_above
    avg_space_s_per_layer = usable_area_total

    total_cells = max(1, space.slots_x * space.slots_y)
    coverage_values = [count / total_cells for count in layer_counts]
    coverage_mean = sum(coverage_values) / len(coverage_values)
    coverage_std = math.sqrt(
        sum((item - coverage_mean) ** 2 for item in coverage_values) / len(coverage_values)
    )

    edge_total = edge_cells_per_layer * space.slots_z
    open_edge_ratio = 0.0 if edge_total == 0 else max(0.0, (edge_total - edge_occupied) / edge_total)

    accessibility_score = (
        0.34
        + 0.56 * open_edge_ratio
        + 0.34 * max(0.0, 1.0 - coverage_std)
        + 0.23 * max(0.0, 1.0 - abs(coverage_mean - 0.70))
    )
    accessibility_score = min(1.2, max(0.08, accessibility_score))

    complexity_penalty = (
        0.022 * math.log1p(max(0, rod_segments))
        + 0.018 * math.log1p(max(0, connector_points))
        + 0.010 * math.log1p(max(0, panel_count))
    )

    # 增益以“单位占地可取用面积”计算，取用面积=地面+上层板面（0层板与地面互斥计入）。
    efficiency_current = 0.0 if footprint_a <= 0 else (usable_area_total / footprint_a)
    efficiency_baseline = max(1e-9, boundary.baseline_gain)
    gain_ratio = efficiency_current / efficiency_baseline
    single_connected = _is_single_connected_system(
        masks,
        pattern_stats,
        width=space.slots_x,
        height=space.slots_y,
    )
    # R9: 杆段必须在最高有效板层截断，不得向上冗余延伸。
    top_capped = all(level >= 0 for level in top_level_by_support.values())
    r10_panel_four_corner_supported = _r10_panel_four_corner_supported(level_support_masks)

    rule_result = RuleResult(
        r1_no_stack=True,
        r2_no_penetration=True,
        r3_min_counts=(panel_count > 0 and rod_segments > 0),
        r4_connector_only=True,
        r5_orthogonal=True,
        r6_parallel_or_collinear=True,
        r7_endpoint_only=True,
        r8_single_connected=single_connected,
        r9_top_capped=top_capped,
        r10_panel_four_corner_supported=r10_panel_four_corner_supported,
    )

    boundary_reasons: list[str] = []
    if space.slots_z > boundary.max_layers_n:
        boundary_reasons.append(
            f"边界失败：层数N={space.slots_z}超过上限{boundary.max_layers_n}。"
        )

    boundary_passed = len(boundary_reasons) == 0
    goal_passed = rule_result.passed and boundary_passed and gain_ratio > 1.0

    fail_reasons: list[str] = []
    if not rule_result.r3_min_counts:
        fail_reasons.append("R3失败：至少需要1个板位与对应杆位。")
    if not rule_result.r8_single_connected:
        fail_reasons.append("R8失败：系统未构成单一连通整体。")
    if not rule_result.r9_top_capped:
        fail_reasons.append("R9失败：存在未端接板面的冗余杆段。")
    if not rule_result.r10_panel_four_corner_supported:
        fail_reasons.append("R10失败：存在板角点未与杆相连（方案B含0层）。")
    fail_reasons.extend(boundary_reasons)
    if rule_result.passed and boundary_passed and not goal_passed:
        fail_reasons.append(
            "目标失败：增益比未超过1。"
            f" 当前={gain_ratio:.3f}。"
        )

    family_key, family_label = _family_key_label(
        footprint_cells=len(occupied_cells),
        panel_ground_count=panel_ground_count,
        panel_above_count=panel_above_count,
    )

    metrics = DesignMetrics(
        footprint_a=round(footprint_a, 6),
        panel_area_total=round(panel_area_total, 6),
        panel_area_above=round(panel_area_above, 6),
        usable_area_total=round(usable_area_total, 6),
        avg_space_s_per_layer=round(avg_space_s_per_layer, 6),
        coverage_mean=round(coverage_mean, 6),
        coverage_std=round(coverage_std, 6),
        open_edge_ratio=round(open_edge_ratio, 6),
        accessibility_score=round(accessibility_score, 6),
        complexity_penalty=round(complexity_penalty, 6),
        efficiency_current=round(efficiency_current, 6),
        efficiency_baseline=round(efficiency_baseline, 6),
        gain_ratio=round(gain_ratio, 6),
        rod_segments=rod_segments,
        connector_points=connector_points,
        panel_count=panel_count,
    )

    return (
        family_key,
        family_label,
        rule_result,
        boundary_passed,
        goal_passed,
        tuple(fail_reasons),
        metrics,
        support_mask,
        layer_area_sums,
    )


def _build_catalog_by_enumeration(
    space: SearchSpace,
    boundary: BoundaryConstraint,
    *,
    family_filter: str = "all",
    status_filter: str = "all",
    sort_key: str = "enum_order",
    offset: int = 0,
    limit: int = 80,
) -> dict[str, object]:
    del sort_key

    patterns = _layer_patterns(
        width=space.slots_x,
        height=space.slots_y,
        dedupe_symmetry=space.dedupe_symmetry,
    )
    pattern_stats = _pattern_stats(
        width=space.slots_x,
        height=space.slots_y,
        dedupe_symmetry=space.dedupe_symmetry,
    )

    edge_cells_per_layer = sum(
        1
        for ix in range(space.slots_x)
        for iy in range(space.slots_y)
        if ix in (0, space.slots_x - 1) or iy in (0, space.slots_y - 1)
    )

    rows: list[dict[str, object]] = []
    total_after_filter = 0

    generated_total = 0
    enumerated_total = 0
    duplicate_removed = 0
    goal_passed_count = 0
    goal_failed_count = 0
    rule_failed_count = 0
    boundary_failed_count = 0
    seen_signatures: set[tuple[int, ...]] = set()

    start_index = max(0, offset)
    end_index = start_index + max(1, limit)

    for sequence in itertools.product(patterns, repeat=space.slots_z):
        if space.dedupe_symmetry:
            signature = _canonical_sequence_signature(
                sequence,
                width=space.slots_x,
                height=space.slots_y,
                enable_symmetry=True,
            )
            if signature in seen_signatures:
                duplicate_removed += 1
                continue
            seen_signatures.add(signature)

        enumerated_total += 1
        case_index = enumerated_total
        design_id = f"D{case_index:07d}"

        (
            family_key,
            family_label,
            rule_result,
            boundary_passed,
            goal_passed,
            fail_reasons,
            metrics,
            _support_mask,
            layer_area_sums,
        ) = _evaluate_masks(
            sequence,
            space=space,
            boundary=boundary,
            pattern_stats=pattern_stats,
            edge_cells_per_layer=edge_cells_per_layer,
        )

        if not rule_result.passed:
            rule_failed_count += 1
        else:
            generated_total += 1
            if goal_passed:
                goal_passed_count += 1
            else:
                goal_failed_count += 1

            if not boundary_passed:
                boundary_failed_count += 1

        family_match = family_filter in ("", "all") or family_filter == family_key
        status_match = _status_match(
            goal_passed=goal_passed,
            rule_passed=rule_result.passed,
            boundary_passed=boundary_passed,
            status=status_filter,
        )
        if not (family_match and status_match):
            continue

        row_index = total_after_filter
        total_after_filter += 1
        if row_index < start_index or row_index >= end_index:
            continue

        _row_support_mask, row_top_level_by_support, _row_rod_segments, _row_connector_points = _rod_profile_from_masks(
            sequence,
            pattern_stats=pattern_stats,
            width=space.slots_x,
            height=space.slots_y,
        )
        row_rod_columns = _rod_columns_from_top_levels(
            row_top_level_by_support,
            width=space.slots_x,
        )

        rows.append(
            {
                "design_id": design_id,
                "family": {"key": family_key, "label": family_label},
                "params": {
                    "slots_x": space.slots_x,
                    "slots_y": space.slots_y,
                    "slots_z": space.slots_z,
                    "panel_length": space.panel_length,
                    "panel_width": space.panel_width,
                    "rod_length": space.rod_length,
                },
                "layout": {
                    "panel_cells": _panel_cells_from_masks(sequence, pattern_stats),
                    "rod_support_points": [[ix, iy] for ix, iy, _top_level in row_rod_columns],
                    "rod_columns": row_rod_columns,
                    "layer_masks": [int(item) for item in sequence],
                    "layer_area_sums": list(layer_area_sums),
                    "slots_x": space.slots_x,
                    "slots_y": space.slots_y,
                    "slots_z": space.slots_z,
                },
                "validation": {
                    "rules": asdict(rule_result),
                    "rules_passed": rule_result.passed,
                    "boundary_passed": boundary_passed,
                    "goal_passed": goal_passed,
                    "fail_reasons": list(fail_reasons),
                },
                "metrics": asdict(metrics),
            }
        )

    enumeration_total = enumerated_total

    return {
        "meta": {
            "offset": start_index,
            "limit": max(1, limit),
            "total_after_filter": total_after_filter,
            "families": list_family_meta(),
            "sort_key": "enum_order",
            "goal_rule": "gain_ratio > 1",
            "boundary": asdict(boundary),
            "search_space": asdict(space),
            "layer_pattern_count": len(patterns),
            "enumeration_total": enumeration_total,
            "duplicate_removed": duplicate_removed,
            "engine_version": ENGINE_VERSION,
            "rod_segment_rule": ROD_SEGMENT_RULE,
        },
        "summary": {
            "generated_total": generated_total,
            "goal_passed": goal_passed_count,
            "goal_failed": goal_failed_count,
            "rule_failed": rule_failed_count,
            "boundary_failed": boundary_failed_count,
        },
        "rows": rows,
    }


def _build_catalog_by_cache(
    space: SearchSpace,
    boundary: BoundaryConstraint,
    *,
    family_filter: str,
    status_filter: str,
    offset: int,
    limit: int,
) -> dict[str, object]:
    start_time = time.time()
    cache = _load_or_build_fixed_cache()

    flat_sequences: array = cache["flat_sequences"]
    family_codes: array = cache["family_codes"]
    sequence_count = int(cache["sequence_count"])
    duplicate_removed = int(cache["duplicate_removed"])
    r8_filtered_removed = int(cache.get("r8_filtered_removed", 0))

    key_to_code, code_to_meta = _family_code_map()
    support_lookup = _support_mask_lookup(width=space.slots_x, height=space.slots_y)
    connected_lookup = _single_connected_lookup(width=space.slots_x, height=space.slots_y)
    max_support_bits = (space.slots_x + 1) * (space.slots_y + 1)
    edge_cells_per_layer = sum(
        1
        for ix in range(space.slots_x)
        for iy in range(space.slots_y)
        if ix in (0, space.slots_x - 1) or iy in (0, space.slots_y - 1)
    )

    cell_count_lookup = [mask.bit_count() for mask in range(1 << (space.slots_x * space.slots_y))]
    edge_count_lookup: list[int] = []
    for mask in range(1 << (space.slots_x * space.slots_y)):
        count = 0
        for ix, iy in _cells_from_mask(mask, width=space.slots_x, height=space.slots_y):
            if ix in (0, space.slots_x - 1) or iy in (0, space.slots_y - 1):
                count += 1
        edge_count_lookup.append(count)

    piece_area = space.panel_length * space.panel_width
    boundary_passed_global = space.slots_z <= boundary.max_layers_n

    start_index = max(0, offset)
    end_index = start_index + max(1, limit)

    rows: list[dict[str, object]] = []
    total_after_filter = 0

    generated_total = 0
    goal_passed_count = 0
    goal_failed_count = 0
    rule_failed_count = 0
    boundary_failed_count = 0

    for idx in range(sequence_count):
        case_index = idx + 1
        design_id = f"D{case_index:07d}"
        m0, m1, m2 = _sequence_from_flat(flat_sequences, idx)
        layer_masks = (m0, m1, m2)
        layer_counts = (
            cell_count_lookup[m0],
            cell_count_lookup[m1],
            cell_count_lookup[m2],
        )

        panel_ground_count = layer_counts[0]
        panel_above_count = layer_counts[1] + layer_counts[2]
        panel_count = panel_ground_count + panel_above_count

        union_mask = m0 | m1 | m2
        footprint_cells = cell_count_lookup[union_mask]

        support_m0 = support_lookup[m0]
        support_m1 = support_lookup[m1]
        support_m2 = support_lookup[m2]

        top_level_2_mask = support_m2
        top_level_1_mask = support_m1 & ~support_m2
        top_level_0_mask = support_m0 & ~(support_m1 | support_m2)
        top_level_2_count = top_level_2_mask.bit_count()
        top_level_1_count = top_level_1_mask.bit_count()
        top_level_0_count = top_level_0_mask.bit_count()

        # 杆段按最高有效板层截断：level0=0段、level1=1段、level2=2段。
        rod_segments = top_level_1_count + 2 * top_level_2_count
        connector_points = top_level_0_count + 2 * top_level_1_count + 3 * top_level_2_count

        r3_min_counts = panel_count > 0 and rod_segments > 0
        r8_single_connected = connected_lookup[union_mask]
        r9_top_capped = True
        r10_panel_four_corner_supported = (support_m0 & ~(support_m1 | support_m2)) == 0
        rules_passed = (
            r3_min_counts
            and r8_single_connected
            and r9_top_capped
            and r10_panel_four_corner_supported
        )

        if not rules_passed:
            rule_failed_count += 1
        else:
            generated_total += 1

        footprint_a = footprint_cells * piece_area
        panel_area_total = panel_count * piece_area
        panel_area_above = panel_above_count * piece_area
        usable_area_total = footprint_a + panel_area_above
        efficiency_current = 0.0 if footprint_a <= 0 else usable_area_total / footprint_a
        efficiency_baseline = max(1e-9, boundary.baseline_gain)
        gain_ratio = efficiency_current / efficiency_baseline

        edge_occupied = edge_count_lookup[m0] + edge_count_lookup[m1] + edge_count_lookup[m2]
        edge_total = edge_cells_per_layer * space.slots_z
        open_edge_ratio = 0.0 if edge_total == 0 else max(0.0, (edge_total - edge_occupied) / edge_total)

        total_cells = max(1, space.slots_x * space.slots_y)
        coverage_values = [count / total_cells for count in layer_counts]
        coverage_mean = sum(coverage_values) / len(coverage_values)
        coverage_std = math.sqrt(
            sum((item - coverage_mean) ** 2 for item in coverage_values) / len(coverage_values)
        )

        accessibility_score = (
            0.34
            + 0.56 * open_edge_ratio
            + 0.34 * max(0.0, 1.0 - coverage_std)
            + 0.23 * max(0.0, 1.0 - abs(coverage_mean - 0.70))
        )
        accessibility_score = min(1.2, max(0.08, accessibility_score))

        complexity_penalty = (
            0.022 * math.log1p(max(0, rod_segments))
            + 0.018 * math.log1p(max(0, connector_points))
            + 0.010 * math.log1p(max(0, panel_count))
        )

        boundary_passed = boundary_passed_global
        goal_passed = rules_passed and boundary_passed and gain_ratio > 1.0

        if rules_passed:
            if goal_passed:
                goal_passed_count += 1
            else:
                goal_failed_count += 1
            if not boundary_passed:
                boundary_failed_count += 1

        family_key, family_label = code_to_meta[family_codes[idx]]

        family_match = family_filter in ("", "all") or family_filter == family_key
        status_match = _status_match(
            goal_passed=goal_passed,
            rule_passed=rules_passed,
            boundary_passed=boundary_passed,
            status=status_filter,
        )
        if not (family_match and status_match):
            continue

        row_index = total_after_filter
        total_after_filter += 1
        if row_index < start_index or row_index >= end_index:
            continue

        fail_reasons: list[str] = []
        if not r3_min_counts:
            fail_reasons.append("R3失败：至少需要1个板位与对应杆位。")
        if not r8_single_connected:
            fail_reasons.append("R8失败：系统未构成单一连通整体。")
        if not r9_top_capped:
            fail_reasons.append("R9失败：存在未端接板面的冗余杆段。")
        if not r10_panel_four_corner_supported:
            fail_reasons.append("R10失败：存在板角点未与杆相连（方案B含0层）。")
        if not boundary_passed:
            fail_reasons.append(f"边界失败：层数N={space.slots_z}超过上限{boundary.max_layers_n}。")
        if rules_passed and boundary_passed and not goal_passed:
            fail_reasons.append(f"目标失败：增益比未超过1。 当前={gain_ratio:.3f}。")

        metrics = DesignMetrics(
            footprint_a=round(footprint_a, 6),
            panel_area_total=round(panel_area_total, 6),
            panel_area_above=round(panel_area_above, 6),
            usable_area_total=round(usable_area_total, 6),
            avg_space_s_per_layer=round(usable_area_total, 6),
            coverage_mean=round(coverage_mean, 6),
            coverage_std=round(coverage_std, 6),
            open_edge_ratio=round(open_edge_ratio, 6),
            accessibility_score=round(accessibility_score, 6),
            complexity_penalty=round(complexity_penalty, 6),
            efficiency_current=round(efficiency_current, 6),
            efficiency_baseline=round(efficiency_baseline, 6),
            gain_ratio=round(gain_ratio, 6),
            rod_segments=rod_segments,
            connector_points=connector_points,
            panel_count=panel_count,
        )

        rule_result = RuleResult(
            r1_no_stack=True,
            r2_no_penetration=True,
            r3_min_counts=r3_min_counts,
            r4_connector_only=True,
            r5_orthogonal=True,
            r6_parallel_or_collinear=True,
            r7_endpoint_only=True,
            r8_single_connected=r8_single_connected,
            r9_top_capped=r9_top_capped,
            r10_panel_four_corner_supported=r10_panel_four_corner_supported,
        )

        layer_area_sums = [round(count * piece_area, 6) for count in layer_counts]
        panel_cells = []
        for level, mask in enumerate(layer_masks):
            for ix, iy in _cells_from_mask(mask, width=space.slots_x, height=space.slots_y):
                panel_cells.append([level, ix, iy])

        rod_columns: list[list[int]] = []
        for bit in range(max_support_bits):
            top_level = -1
            if (support_m2 >> bit) & 1:
                top_level = 2
            elif (support_m1 >> bit) & 1:
                top_level = 1
            elif (support_m0 >> bit) & 1:
                top_level = 0
            if top_level < 0:
                continue
            ix = bit % (space.slots_x + 1)
            iy = bit // (space.slots_x + 1)
            rod_columns.append([ix, iy, top_level])

        rows.append(
            {
                "design_id": design_id,
                "family": {"key": family_key, "label": family_label},
                "params": {
                    "slots_x": space.slots_x,
                    "slots_y": space.slots_y,
                    "slots_z": space.slots_z,
                    "panel_length": space.panel_length,
                    "panel_width": space.panel_width,
                    "rod_length": space.rod_length,
                },
                "layout": {
                    "panel_cells": panel_cells,
                    "rod_support_points": [[ix, iy] for ix, iy, _top_level in rod_columns],
                    "rod_columns": rod_columns,
                    "layer_masks": [int(item) for item in layer_masks],
                    "layer_area_sums": layer_area_sums,
                    "slots_x": space.slots_x,
                    "slots_y": space.slots_y,
                    "slots_z": space.slots_z,
                },
                "validation": {
                    "rules": asdict(rule_result),
                    "rules_passed": rules_passed,
                    "boundary_passed": boundary_passed,
                    "goal_passed": goal_passed,
                    "fail_reasons": fail_reasons,
                },
                "metrics": asdict(metrics),
            }
        )

    compute_seconds = round(time.time() - start_time, 3)

    return {
        "meta": {
            "offset": start_index,
            "limit": max(1, limit),
            "total_after_filter": total_after_filter,
            "families": list_family_meta(),
            "sort_key": "enum_order",
            "goal_rule": "gain_ratio > 1",
            "boundary": asdict(boundary),
            "search_space": asdict(space),
            "layer_pattern_count": len(_layer_patterns(width=3, height=3, dedupe_symmetry=True)),
            "enumeration_total": sequence_count,
            "duplicate_removed": duplicate_removed,
            "r8_filtered_removed": r8_filtered_removed,
            "cache_file": str(CATALOG_CACHE_PATH),
            "compute_seconds": compute_seconds,
            "engine_version": str(cache.get("engine_version", ENGINE_VERSION)),
            "rod_segment_rule": str(cache.get("rod_segment_rule", ROD_SEGMENT_RULE)),
        },
        "summary": {
            "generated_total": generated_total,
            "goal_passed": goal_passed_count,
            "goal_failed": goal_failed_count,
            "rule_failed": rule_failed_count,
            "boundary_failed": boundary_failed_count,
        },
        "rows": rows,
    }


def build_catalog(
    space: SearchSpace,
    boundary: BoundaryConstraint,
    *,
    family_filter: str = "all",
    status_filter: str = "all",
    sort_key: str = "enum_order",
    offset: int = 0,
    limit: int = 80,
) -> dict[str, object]:
    if _is_fixed_3x3x3_space(space):
        return _build_catalog_by_cache(
            space=space,
            boundary=boundary,
            family_filter=family_filter,
            status_filter=status_filter,
            offset=offset,
            limit=limit,
        )
    return _build_catalog_by_enumeration(
        space=space,
        boundary=boundary,
        family_filter=family_filter,
        status_filter=status_filter,
        sort_key=sort_key,
        offset=offset,
        limit=limit,
    )
