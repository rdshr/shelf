from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MODULE_ORDER = ("rod", "connector", "panel")
MODULE_LABEL = {
    "rod": "杆",
    "connector": "连接接口",
    "panel": "隔板",
}


@dataclass(frozen=True)
class BoundarySpec:
    code: str
    display_name: str
    path: tuple[str, ...]
    minimum: float
    integer: bool
    fallback: float


BOUNDARY_SPECS: dict[str, BoundarySpec] = {
    "layers_n": BoundarySpec(
        code="N",
        display_name="层数（layers_n）",
        path=("layers_n",),
        minimum=1,
        integer=True,
        fallback=1,
    ),
    "payload_p_per_layer": BoundarySpec(
        code="P",
        display_name="每层承重（payload_p_per_layer）",
        path=("payload_p_per_layer",),
        minimum=0.1,
        integer=False,
        fallback=1,
    ),
    "space_width": BoundarySpec(
        code="S.width",
        display_name="每层空间宽度（space_s_per_layer.width）",
        path=("space_s_per_layer", "width"),
        minimum=0.1,
        integer=False,
        fallback=1,
    ),
    "space_depth": BoundarySpec(
        code="S.depth",
        display_name="每层空间深度（space_s_per_layer.depth）",
        path=("space_s_per_layer", "depth"),
        minimum=0.1,
        integer=False,
        fallback=1,
    ),
    "space_height": BoundarySpec(
        code="S.height",
        display_name="每层空间高度（space_s_per_layer.height）",
        path=("space_s_per_layer", "height"),
        minimum=0.1,
        integer=False,
        fallback=1,
    ),
    "opening_width": BoundarySpec(
        code="O.width",
        display_name="开口宽度（opening_o.width）",
        path=("opening_o", "width"),
        minimum=0.1,
        integer=False,
        fallback=1,
    ),
    "opening_height": BoundarySpec(
        code="O.height",
        display_name="开口高度（opening_o.height）",
        path=("opening_o", "height"),
        minimum=0.1,
        integer=False,
        fallback=1,
    ),
    "footprint_width": BoundarySpec(
        code="A.width",
        display_name="占地宽度（footprint_a.width）",
        path=("footprint_a", "width"),
        minimum=0.1,
        integer=False,
        fallback=1,
    ),
    "footprint_depth": BoundarySpec(
        code="A.depth",
        display_name="占地深度（footprint_a.depth）",
        path=("footprint_a", "depth"),
        minimum=0.1,
        integer=False,
        fallback=1,
    ),
}


def _to_number(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed


def _to_non_negative_int(value: Any) -> int:
    parsed = _to_number(value, 0)
    return max(0, int(round(parsed)))


def _set_nested(target: dict[str, Any], path: tuple[str, ...], value: Any) -> None:
    cursor = target
    for key in path[:-1]:
        if key not in cursor or not isinstance(cursor[key], dict):
            cursor[key] = {}
        cursor = cursor[key]
    cursor[path[-1]] = value


def _base_boundary() -> dict[str, Any]:
    return {
        "layers_n": 1,
        "payload_p_per_layer": 1.0,
        "space_s_per_layer": {"width": 1.0, "depth": 1.0, "height": 1.0},
        "opening_o": {"width": 1.0, "height": 1.0},
        "footprint_a": {"width": 1.0, "depth": 1.0},
    }


def _resolve_boundary(
    boundary_input: dict[str, Any]
) -> tuple[dict[str, Any], list[str], list[str]]:
    boundary = _base_boundary()
    errors: list[str] = []
    active_codes: list[str] = []

    for key, spec in BOUNDARY_SPECS.items():
        payload = boundary_input.get(key, {})
        enabled = bool(payload.get("enabled", True))
        raw_value = _to_number(payload.get("value", spec.fallback), spec.fallback)
        value = int(round(raw_value)) if spec.integer else raw_value

        if enabled:
            active_codes.append(spec.code)
            if spec.integer:
                if not isinstance(value, int) or value < spec.minimum:
                    errors.append(f"{spec.display_name} 必须是大于 0 的整数")
            elif value < spec.minimum:
                errors.append(f"{spec.display_name} 必须大于 0")
        else:
            value = spec.fallback

        if spec.integer:
            value = max(int(spec.minimum), int(round(value)))
        else:
            value = max(spec.minimum, float(value))

        _set_nested(boundary, spec.path, value)

    return boundary, errors, active_codes


def _subsets(items: list[str]) -> list[list[str]]:
    if not items:
        return [[]]

    output: list[list[str]] = []
    for mask in range(1, 1 << len(items)):
        bucket: list[str] = []
        for idx, name in enumerate(items):
            if mask & (1 << idx):
                bucket.append(name)
        output.append(bucket)
    return output


def _render_counts(module_counts: dict[str, int], modules: list[str]) -> dict[str, int]:
    return {
        "rod": module_counts["rod"] if "rod" in modules else 0,
        "connector": module_counts["connector"] if "connector" in modules else 0,
        "panel": module_counts["panel"] if "panel" in modules else 0,
    }


def _build_combinations(
    module_counts: dict[str, int],
    boundary_errors: list[str],
    rule_r1: bool,
    rule_r2: bool,
) -> list[dict[str, Any]]:
    available_modules = [name for name in MODULE_ORDER if module_counts[name] > 0]
    buckets = _subsets(available_modules)
    combos: list[dict[str, Any]] = []

    for idx, modules in enumerate(buckets):
        errors = list(boundary_errors)
        if rule_r1 and len(modules) < 2:
            errors.append("R1 失败：组合至少包含 2 种模块类型")
        if rule_r2 and "connector" not in modules:
            errors.append("R2 失败：组合必须包含连接接口（connector）")

        combo_id = "|".join(modules) if modules else f"empty-{idx}"
        label = " + ".join(MODULE_LABEL[item] for item in modules) if modules else "空组合"
        combos.append(
            {
                "id": combo_id,
                "modules": modules,
                "label": label,
                "valid": len(errors) == 0,
                "errors": errors,
                "render_counts": _render_counts(module_counts, modules),
            }
        )

    combos.sort(
        key=lambda item: (
            0 if item["valid"] else 1,
            -len(item["modules"]),
            item["label"],
        )
    )
    return combos


def generate_simulation(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("请求体必须是 JSON 对象")

    boundary_input = payload.get("boundary_input", {})
    if not isinstance(boundary_input, dict):
        raise ValueError("boundary_input 必须是对象")

    module_counts_raw = payload.get("module_counts", {})
    if not isinstance(module_counts_raw, dict):
        raise ValueError("module_counts 必须是对象")

    rules_raw = payload.get("rules", {})
    if not isinstance(rules_raw, dict):
        raise ValueError("rules 必须是对象")

    boundary, boundary_errors, active_codes = _resolve_boundary(boundary_input)
    module_counts = {
        "rod": _to_non_negative_int(module_counts_raw.get("rod", 0)),
        "connector": _to_non_negative_int(module_counts_raw.get("connector", 0)),
        "panel": _to_non_negative_int(module_counts_raw.get("panel", 0)),
    }
    rules = {
        "r1": bool(rules_raw.get("r1", True)),
        "r2": bool(rules_raw.get("r2", True)),
    }

    combinations = _build_combinations(
        module_counts=module_counts,
        boundary_errors=boundary_errors,
        rule_r1=rules["r1"],
        rule_r2=rules["r2"],
    )
    valid_count = sum(1 for item in combinations if item["valid"])

    return {
        "ok": True,
        "boundary": boundary,
        "active_boundary_codes": active_codes,
        "boundary_errors": boundary_errors,
        "module_counts": module_counts,
        "rules": rules,
        "combinations": combinations,
        "summary": {
            "total": len(combinations),
            "valid": valid_count,
        },
    }
