from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from project_runtime.framework_layer import FrameworkModuleClass
from rule_validation_models import RuleValidationOutcome, RuleValidationSummary

_SYSTEM_ALLOWED_EXACT_PREFIXES: tuple[str, ...] = ("exact.evidence",)
_SYSTEM_ALLOWED_COMMUNICATION_PREFIXES: tuple[str, ...] = tuple()
_MAX_REASONS = 20


def _clean_path(value: Any) -> str:
    text = str(value or "").strip()
    return text.strip(".")


def _iter_projection_paths(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [
        path
        for item in value
        for path in (_clean_path(item),)
        if path
    ]


def _collect_allowed_exact_paths(
    framework_modules: Sequence[type[FrameworkModuleClass]],
) -> set[str]:
    allowed = set(_SYSTEM_ALLOWED_EXACT_PREFIXES)
    for module in framework_modules:
        for projection in module.boundary_projection_map.values():
            allowed_path = _clean_path(projection.get("primary_exact_path"))
            if allowed_path:
                allowed.add(allowed_path)
            allowed.update(_iter_projection_paths(projection.get("related_exact_paths")))
        for overlay_path in module.exact_overlay_paths:
            cleaned = _clean_path(overlay_path)
            if cleaned:
                allowed.add(cleaned)
    return allowed


def _collect_allowed_communication_paths(
    framework_modules: Sequence[type[FrameworkModuleClass]],
) -> set[str]:
    allowed = set(_SYSTEM_ALLOWED_COMMUNICATION_PREFIXES)
    for module in framework_modules:
        for projection in module.boundary_projection_map.values():
            allowed_path = _clean_path(projection.get("primary_communication_path"))
            if allowed_path:
                allowed.add(allowed_path)
            allowed.update(_iter_projection_paths(projection.get("related_communication_paths")))
    return allowed


def _collect_non_one_to_one_projection_violations(
    framework_modules: Sequence[type[FrameworkModuleClass]],
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for module in framework_modules:
        module_id = str(getattr(module, "module_id", "") or "")
        boundary_map = getattr(module, "boundary_projection_map", {}) or {}
        if not isinstance(boundary_map, Mapping):
            continue
        for boundary_id, projection in boundary_map.items():
            if not isinstance(projection, Mapping):
                continue
            boundary_text = str(boundary_id or "").strip()
            primary_exact = _clean_path(projection.get("primary_exact_path"))
            related_exact = _iter_projection_paths(projection.get("related_exact_paths"))
            primary_communication = _clean_path(projection.get("primary_communication_path"))
            related_communication = _iter_projection_paths(projection.get("related_communication_paths"))
            exact_is_one_to_one = bool(primary_exact) and related_exact == [primary_exact]
            communication_is_one_to_one = (
                bool(primary_communication)
                and related_communication == [primary_communication]
            )
            if exact_is_one_to_one and communication_is_one_to_one:
                continue
            violations.append(
                {
                    "module_id": module_id,
                    "boundary_id": boundary_text,
                    "primary_exact_path": primary_exact,
                    "related_exact_paths": related_exact,
                    "primary_communication_path": primary_communication,
                    "related_communication_paths": related_communication,
                }
            )
    return violations


def _collect_config_paths(payload: Mapping[str, Any], root_prefix: str) -> set[str]:
    paths: set[str] = {root_prefix}

    def visit(value: Any, current: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                child_path = _clean_path(f"{current}.{key}")
                if not child_path:
                    continue
                paths.add(child_path)
                visit(child, child_path)
            return
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                if isinstance(item, Mapping):
                    visit(item, current)

    visit(payload, root_prefix)
    return paths


def _path_is_allowed(path: str, allowed_prefixes: set[str]) -> bool:
    for prefix in allowed_prefixes:
        if path == prefix:
            return True
        if path.startswith(f"{prefix}."):
            return True
        if prefix.startswith(f"{path}."):
            return True
    return False


def _collapse_to_top_paths(paths: Sequence[str]) -> list[str]:
    collapsed: list[str] = []
    for path in sorted({path for path in paths if path}):
        if any(path == kept or path.startswith(f"{kept}.") for kept in collapsed):
            continue
        collapsed.append(path)
    return collapsed


def summarize_framework_violation_guard(
    framework_modules: Sequence[type[FrameworkModuleClass]],
    communication_config: Mapping[str, Any],
    exact_config: Mapping[str, Any],
) -> RuleValidationSummary:
    allowed_exact_paths = _collect_allowed_exact_paths(framework_modules)
    allowed_communication_paths = _collect_allowed_communication_paths(framework_modules)

    observed_exact_paths = _collect_config_paths(exact_config, "exact")
    observed_communication_paths = _collect_config_paths(communication_config, "communication")

    invalid_exact_paths = _collapse_to_top_paths(
        [
            path
            for path in observed_exact_paths
            if path != "exact" and not _path_is_allowed(path, allowed_exact_paths)
        ]
    )
    invalid_communication_paths = _collapse_to_top_paths(
        [
            path
            for path in observed_communication_paths
            if path != "communication" and not _path_is_allowed(path, allowed_communication_paths)
        ]
    )
    non_one_to_one_violations = _collect_non_one_to_one_projection_violations(framework_modules)

    reasons: list[str] = []
    for path in invalid_exact_paths:
        reasons.append(
            f"FRAMEWORK_VIOLATION: {path} is outside framework projected exact paths; "
            "update framework first, then materialize."
        )
    for path in invalid_communication_paths:
        reasons.append(
            f"FRAMEWORK_VIOLATION: {path} is outside framework projected communication paths; "
            "update framework first, then materialize."
        )
    for violation in non_one_to_one_violations:
        reasons.append(
            "FRAMEWORK_VIOLATION: boundary projection must be one-to-one: "
            f"{violation['module_id']}/{violation['boundary_id']} "
            f"primary_exact={violation['primary_exact_path']} "
            f"related_exact={violation['related_exact_paths']} "
            f"primary_communication={violation['primary_communication_path']} "
            f"related_communication={violation['related_communication_paths']}; "
            "update framework first, then materialize."
        )

    outcome = RuleValidationOutcome(
        rule_id="FRAMEWORK_VIOLATION_GUARD",
        name="framework projected path guard",
        passed=not reasons,
        reasons=tuple(reasons[:_MAX_REASONS]),
        evidence={
            "allowed_exact_paths": sorted(allowed_exact_paths),
            "allowed_communication_paths": sorted(allowed_communication_paths),
            "invalid_exact_paths": invalid_exact_paths,
            "invalid_communication_paths": invalid_communication_paths,
            "non_one_to_one_projection_count": len(non_one_to_one_violations),
            "non_one_to_one_projections": non_one_to_one_violations[:_MAX_REASONS],
        },
    )
    return RuleValidationSummary(module_id="framework.guard", rules=(outcome,))
