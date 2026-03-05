from __future__ import annotations

import argparse
import copy
import json
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from main import build_report_payload, variant_key
from shelf_framework import (
    BoundaryDefinition,
    CombinationRules,
    Footprint2D,
    Goal,
    Hypothesis,
    Module,
    Opening2D,
    Space3D,
    VerificationInput,
    evaluate_boundary_checks,
    evaluate_structural_checks,
    generate_shelf_type_specs,
    infer_grid_dimensions,
    modules_to_list,
    verify,
)

DOCS_DIR = Path("docs").resolve()

CHECK_MESSAGES: dict[str, str] = {
    "B1_layers_within_limit": "active layers exceed Boundary.max_layers",
    "B2_fixed_footprint": "base footprint must exactly match configured area",
    "C2_support_continuity": (
        "C2 violated: support/continuity contract failed "
        "(rod/interface readiness, footprint path, or bridge connectivity)"
    ),
    "C3_center_projection_stable": "C3 violated: center of mass projection is outside footprint",
    "C4_upper_layer_engaged": (
        "C4 violated: multi-layer mode requires every declared upper layer to be non-empty"
    ),
}

GOAL = Goal("Increase storage access efficiency per footprint area")
HYPOTHESIS = Hypothesis(
    hypothesis_id="H1",
    statement="With valid boundary and combination, access efficiency should improve",
)
DEFAULT_RULES = CombinationRules.default()
VALID_COMBOS = DEFAULT_RULES.valid_subsets()
CANDIDATE_COMBO = {Module.ROD, Module.CONNECTOR, Module.PANEL}

CACHE: dict[str, dict[str, Any]] = {}


def _decode_rule_mask(raw: str | None) -> dict[str, bool]:
    bits = (raw or "11111").strip()
    if len(bits) < 5 or any(ch not in {"0", "1"} for ch in bits):
        bits = "11111"
    return {
        "B2": bits[0] == "1",
        "C2": bits[1] == "1",
        "C3": bits[2] == "1",
        "C4": bits[3] == "1",
        "EFF": bits[4] == "1",
    }


def _encode_rule_mask(flags: dict[str, bool]) -> str:
    return "".join(
        "1" if flags.get(code, True) else "0"
        for code in ("B2", "C2", "C3", "C4", "EFF")
    )


def _passes_rule_mask(
    type_item: dict[str, Any],
    area: int,
    baseline_efficiency: float,
    flags: dict[str, bool],
) -> bool:
    verification = type_item.get("verification", {})
    if not verification.get("boundary_valid", True):
        return False
    if not verification.get("combination_valid", True):
        return False

    checks = type_item.get("structural_checks", {})
    if flags.get("B2", True) and not checks.get("B2_fixed_footprint", True):
        return False
    if flags.get("C2", True) and not checks.get("C2_support_continuity", True):
        return False
    if flags.get("C3", True) and not checks.get("C3_center_projection_stable", True):
        return False
    if flags.get("C4", True) and not checks.get("C4_upper_layer_engaged", True):
        return False

    if flags.get("EFF", True):
        active_cells_per_layer = type_item.get("active_cells_per_layer") or []
        base_cells = int(active_cells_per_layer[0]) if active_cells_per_layer else 0
        denominator = area if flags.get("B2", True) else max(1, base_cells)
        runtime_efficiency = float(type_item.get("total_active_cells", 0)) / float(
            denominator
        )
        if runtime_efficiency <= baseline_efficiency:
            return False

    return True


def _build_variant(area: int, layers: int, rule_mask: str) -> dict[str, Any]:
    key = variant_key(area, layers)
    cache_key = f"{key}|rr={rule_mask}"
    if cache_key in CACHE:
        return CACHE[cache_key]

    grid_width, grid_depth = infer_grid_dimensions(area)
    boundary = BoundaryDefinition(
        layers_n=layers,
        payload_p_per_layer=30.0,
        space_s_per_layer=Space3D(width=2.0, depth=2.0, height=30.0),
        opening_o=Opening2D(width=1.8, height=1.6),
        footprint_a=Footprint2D(width=float(grid_width), depth=float(grid_depth)),
    )

    specs, meta = generate_shelf_type_specs(
        boundary=boundary,
        footprint_area_cells=area,
        max_layers=layers,
        baseline_efficiency=1.0,
        rules=DEFAULT_RULES,
        combo=CANDIDATE_COMBO,
    )
    specs_payload = [item.to_dict() for item in specs]
    flags = _decode_rule_mask(rule_mask)
    filtered_types: list[dict[str, Any]] = []
    for item in specs_payload:
        if not _passes_rule_mask(
            item,
            area=area,
            baseline_efficiency=meta["baseline_efficiency"],
            flags=flags,
        ):
            continue
        filtered_types.append(copy.deepcopy(item))

    if filtered_types:
        sample_checks = filtered_types[0].get("structural_checks", {})
    else:
        sample_masks = ((1 << meta["cell_count"]) - 1,)
        sample_checks = {
            **evaluate_boundary_checks(
                sample_masks,
                boundary=boundary,
                footprint_area_cells=area,
            ),
            **evaluate_structural_checks(
                sample_masks,
                grid_width=meta["grid_width"],
                grid_depth=meta["grid_depth"],
                combo=CANDIDATE_COMBO,
            ),
        }

    verification_result = verify(
        VerificationInput(
            boundary=boundary,
            combo=CANDIDATE_COMBO,
            valid_combinations=VALID_COMBOS,
            baseline_efficiency=1.0,
            target_efficiency=1.01,
            extra_checks=sample_checks,
            extra_check_messages=CHECK_MESSAGES,
        )
    )

    variant_payload = build_report_payload(
        goal=GOAL,
        boundary=boundary,
        hypothesis=HYPOTHESIS,
        candidate_combo=CANDIDATE_COMBO,
        valid_combos=VALID_COMBOS,
        types=filtered_types,
        meta=meta,
        verification_result=verification_result.to_dict(),
    )
    profile = {
        "key": key,
        "label": f"A={area}, N<={layers}",
        "area": area,
        "max_layers": layers,
        "grid_width": meta["grid_width"],
        "grid_depth": meta["grid_depth"],
        "total_types": variant_payload["summary"]["total"],
        "passed": variant_payload["summary"]["passed"],
        "failed": variant_payload["summary"]["failed"],
        "module_combo": modules_to_list(CANDIDATE_COMBO),
    }

    payload = {
        "key": key,
        "rule_mask": _encode_rule_mask(flags),
        "profile": profile,
        "variant": variant_payload,
    }
    CACHE[cache_key] = payload
    return payload


def _parse_positive_int(query: dict[str, list[str]], name: str) -> int:
    raw = (query.get(name) or [""])[0].strip()
    value = int(raw)
    if value <= 0:
        raise ValueError(f"{name} must be > 0")
    return value


class ShelfHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(DOCS_DIR), **kwargs)

    def log_message(self, format: str, *args: Any) -> None:
        super().log_message(format, *args)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _write_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/variant":
            try:
                query = parse_qs(parsed.query)
                area = _parse_positive_int(query, "area")
                layers = _parse_positive_int(query, "layers")
                rule_mask = (query.get("rr") or ["11111"])[0]
                payload = _build_variant(area, layers, rule_mask=rule_mask)
                self._write_json(HTTPStatus.OK, payload)
            except ValueError as err:
                self._write_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "bad_request", "message": str(err)},
                )
            except Exception as err:  # noqa: BLE001
                self._write_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": "server_error", "message": str(err)},
                )
            return

        if parsed.path in {"", "/"}:
            self.path = "/groups.html"
        else:
            self.path = parsed.path
        super().do_GET()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve docs and runtime variant API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4173)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), ShelfHandler)
    print(f"Serving on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
