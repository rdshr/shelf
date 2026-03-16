from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
import re
from typing import Any

from project_runtime.utils import REPO_ROOT

CORRESPONDENCE_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class NavigationTarget:
    target_kind: str
    layer: str
    file_path: str
    start_line: int
    end_line: int
    symbol: str
    label: str
    is_primary: bool
    is_editable: bool
    is_deprecated_alias: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CorrespondenceNode:
    object_kind: str
    object_id: str
    owner_module_id: str
    display_name: str
    materialization_kind: str
    primary_nav_target_kind: str
    primary_edit_target_kind: str
    correspondence_anchor: dict[str, Any]
    implementation_anchor: dict[str, Any]
    navigation_targets: tuple[NavigationTarget, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["navigation_targets"] = [item.to_dict() for item in self.navigation_targets]
        return payload


@lru_cache(maxsize=128)
def _file_lines(file_path: str) -> tuple[str, ...]:
    resolved = (REPO_ROOT / file_path).resolve()
    if not resolved.exists():
        return tuple()
    return tuple(resolved.read_text(encoding="utf-8").splitlines())


def _find_line(file_path: str, needle: str, *, fallback: int = 1) -> int:
    if not needle:
        return fallback
    for line_no, line_text in enumerate(_file_lines(file_path), start=1):
        if needle in line_text:
            return line_no
    return fallback


def _line_range(start_line: Any, end_line: Any | None = None) -> tuple[int, int]:
    try:
        start = int(start_line)
    except (TypeError, ValueError):
        start = 1
    if start < 1:
        start = 1
    if end_line is None:
        return start, start
    try:
        end = int(end_line)
    except (TypeError, ValueError):
        end = start
    if end < start:
        end = start
    return start, end


def _target(
    *,
    target_kind: str,
    layer: str,
    file_path: str,
    start_line: int,
    end_line: int,
    symbol: str,
    label: str,
    is_primary: bool = False,
    is_editable: bool = False,
    is_deprecated_alias: bool = False,
) -> NavigationTarget:
    start, end = _line_range(start_line, end_line)
    return NavigationTarget(
        target_kind=target_kind,
        layer=layer,
        file_path=str(file_path),
        start_line=start,
        end_line=end,
        symbol=str(symbol),
        label=str(label),
        is_primary=bool(is_primary),
        is_editable=bool(is_editable),
        is_deprecated_alias=bool(is_deprecated_alias),
    )


def _source_ref_target(
    *,
    target_kind: str,
    layer: str,
    source_ref: dict[str, Any],
    symbol: str,
    label: str,
    is_primary: bool,
    is_editable: bool,
    is_deprecated_alias: bool = False,
) -> NavigationTarget:
    file_path = str(source_ref.get("file_path") or "")
    start_line, end_line = _line_range(source_ref.get("line"), source_ref.get("end_line"))
    return _target(
        target_kind=target_kind,
        layer=layer,
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        symbol=symbol,
        label=label,
        is_primary=is_primary,
        is_editable=is_editable,
        is_deprecated_alias=is_deprecated_alias,
    )


def _display_name_from_symbol(symbol: str, fallback: str) -> str:
    text = str(symbol or "").strip()
    if ":" in text:
        _, _, tail = text.partition(":")
        if tail:
            return tail
    return fallback


def _path_section_line(project_file: str, dotted_path: str) -> int:
    section_name = f"[{dotted_path}]"
    return _find_line(project_file, section_name, fallback=1)


def _code_correspondence_target(
    *,
    kind: str,
    label: str,
    symbol: str,
    is_primary: bool,
) -> NavigationTarget:
    file_path = "src/project_runtime/code_layer.py"
    if kind == "module":
        line = _find_line(file_path, "def _build_module_contract_type(", fallback=1)
    elif kind == "base":
        line = _find_line(file_path, "def _build_base_contract_types(", fallback=1)
    elif kind == "rule":
        line = _find_line(file_path, "def _build_rule_contract_types(", fallback=1)
    elif kind == "static_param":
        line = _find_line(file_path, "def _build_static_params_type(", fallback=1)
    elif kind == "runtime_param":
        line = _find_line(file_path, "def _build_runtime_params_type(", fallback=1)
    else:
        line = _find_line(file_path, "def _build_implementation_slots(", fallback=1)
    return _target(
        target_kind="code_correspondence",
        layer="code",
        file_path=file_path,
        start_line=line,
        end_line=line,
        symbol=symbol,
        label=label,
        is_primary=is_primary,
        is_editable=True,
    )


def _module_tree_node(
    *,
    module_id: str,
    module_object_id: str,
    base_ids: list[str],
    rule_ids: list[str],
    boundary_ids: list[str],
    static_param_ids: list[str],
    runtime_param_ids: list[str],
) -> dict[str, Any]:
    return {
        "module_object_id": module_object_id,
        "module_id": module_id,
        "bases": base_ids,
        "rules": rule_ids,
        "boundaries": boundary_ids,
        "static_params": static_param_ids,
        "runtime_params": runtime_param_ids,
    }


def _module_ids(canonical: dict[str, Any]) -> list[str]:
    modules = canonical.get("framework", {}).get("modules", [])
    if not isinstance(modules, list):
        return []
    return [
        str(item.get("module_id") or "")
        for item in modules
        if isinstance(item, dict) and str(item.get("module_id") or "").strip()
    ]


def _find_module(canonical: dict[str, Any], layer: str, module_id: str) -> dict[str, Any]:
    modules = canonical.get(layer, {}).get("modules", [])
    if not isinstance(modules, list):
        return {}
    for item in modules:
        if isinstance(item, dict) and str(item.get("module_id") or "") == module_id:
            return item
    return {}


def _module_runtime_implementation_target(
    *,
    code_module: dict[str, Any],
    fallback_symbol: str,
    is_primary: bool,
) -> NavigationTarget:
    bindings = code_module.get("code_bindings", {})
    slots = bindings.get("implementation_slots") if isinstance(bindings, dict) else []
    if isinstance(slots, list):
        runtime_slot = next(
            (
                item
                for item in slots
                if isinstance(item, dict) and str(item.get("slot_kind") or "") == "runtime_export"
            ),
            None,
        )
        if isinstance(runtime_slot, dict):
            source_ref = runtime_slot.get("source_ref")
            if isinstance(source_ref, dict):
                return _source_ref_target(
                    target_kind="code_implementation",
                    layer="code",
                    source_ref=source_ref,
                    symbol=str(runtime_slot.get("source_symbol") or fallback_symbol),
                    label="Code implementation anchor",
                    is_primary=is_primary,
                    is_editable=True,
                )
    line = _find_line("src/project_runtime/code_layer.py", "def build_code_modules(", fallback=1)
    return _target(
        target_kind="code_implementation",
        layer="code",
        file_path="src/project_runtime/code_layer.py",
        start_line=line,
        end_line=line,
        symbol=fallback_symbol,
        label="Code implementation anchor",
        is_primary=is_primary,
        is_editable=True,
    )


def _boundary_slot_target(
    *,
    code_module: dict[str, Any],
    boundary_id: str,
    slot_kind: str,
    target_kind: str,
    fallback_symbol: str,
    fallback_label: str,
    fallback_target: NavigationTarget,
    is_primary: bool,
) -> NavigationTarget:
    bindings = code_module.get("code_bindings", {})
    slots = bindings.get("implementation_slots") if isinstance(bindings, dict) else []
    if isinstance(slots, list):
        matched_slot = next(
            (
                item
                for item in slots
                if isinstance(item, dict)
                and str(item.get("slot_kind") or "") == slot_kind
                and str(item.get("boundary_id") or "") == boundary_id
            ),
            None,
        )
        if isinstance(matched_slot, dict):
            source_ref = matched_slot.get("source_ref")
            if isinstance(source_ref, dict):
                return _source_ref_target(
                    target_kind=target_kind,
                    layer="code",
                    source_ref=source_ref,
                    symbol=str(matched_slot.get("source_symbol") or fallback_symbol),
                    label=fallback_label,
                    is_primary=is_primary,
                    is_editable=True,
                )
    return fallback_target


def _deprecated_alias_target(alias_path: str, *, is_primary: bool = False) -> NavigationTarget:
    line = _find_line("src/project_runtime/config_layer.py", "deprecated_boundary_anchor_path", fallback=1)
    return _target(
        target_kind="deprecated_alias",
        layer="code",
        file_path="src/project_runtime/config_layer.py",
        start_line=line,
        end_line=line,
        symbol=alias_path,
        label="Deprecated boundary alias",
        is_primary=is_primary,
        is_editable=True,
        is_deprecated_alias=True,
    )


_MODULE_BOUNDARY_PAIR_PATTERN = re.compile(r"(?P<module>[A-Za-z0-9_]+\.[A-Za-z0-9_]+\.[A-Za-z0-9_]+):(?P<boundary>[A-Z0-9_]+)")


def _collect_known_object_ids(
    object_payload: list[dict[str, Any]],
) -> tuple[set[str], set[str], set[str], set[str], dict[tuple[str, str], str]]:
    module_ids: set[str] = set()
    base_ids: set[str] = set()
    rule_ids: set[str] = set()
    object_ids: set[str] = set()
    boundary_object_ids: dict[tuple[str, str], str] = {}
    for item in object_payload:
        object_id = str(item.get("object_id") or "")
        object_kind = str(item.get("object_kind") or "")
        owner_module_id = str(item.get("owner_module_id") or "")
        object_ids.add(object_id)
        if object_kind == "module":
            module_ids.add(object_id)
            continue
        if object_kind == "base":
            base_ids.add(object_id)
            continue
        if object_kind == "rule":
            rule_ids.add(object_id)
            continue
        if object_kind == "boundary":
            _, _, boundary_id = object_id.partition("::boundary::")
            if owner_module_id and boundary_id:
                boundary_object_ids[(owner_module_id, boundary_id)] = object_id
    return module_ids, base_ids, rule_ids, object_ids, boundary_object_ids


def _reason_object_ids(
    reason: str,
    *,
    module_ids: set[str],
    base_ids: set[str],
    rule_ids: set[str],
    boundary_object_ids: dict[tuple[str, str], str],
) -> list[str]:
    mapped: list[str] = []
    for rule_id in sorted(rule_ids):
        if rule_id in reason:
            mapped.append(rule_id)
    for base_id in sorted(base_ids):
        if base_id in reason:
            mapped.append(base_id)
    for match in _MODULE_BOUNDARY_PAIR_PATTERN.finditer(reason):
        module_id = str(match.group("module") or "")
        boundary_id = str(match.group("boundary") or "")
        object_id = boundary_object_ids.get((module_id, boundary_id))
        if object_id:
            mapped.append(object_id)
    for module_id in sorted(module_ids):
        if module_id in reason:
            mapped.append(module_id)
    deduped = list(dict.fromkeys(mapped))
    return deduped


def _guard_summary(canonical: dict[str, Any], object_payload: list[dict[str, Any]]) -> dict[str, Any]:
    reports = canonical.get("evidence", {}).get("validation_reports", {})
    if not isinstance(reports, dict):
        return {"passed": False, "issues": [], "rule_count": 0}
    scope = reports.get("correspondence_guard", {})
    if not isinstance(scope, dict):
        return {"passed": False, "issues": [], "rule_count": 0}
    rules = scope.get("rules")
    module_ids, base_ids, rule_ids, _, boundary_object_ids = _collect_known_object_ids(object_payload)
    issues: list[dict[str, Any]] = []
    if isinstance(rules, list):
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            reasons = rule.get("reasons")
            if isinstance(reasons, list):
                for reason in reasons:
                    reason_text = str(reason)
                    object_ids = _reason_object_ids(
                        reason_text,
                        module_ids=module_ids,
                        base_ids=base_ids,
                        rule_ids=rule_ids,
                        boundary_object_ids=boundary_object_ids,
                    )
                    issues.append(
                        {
                            "issue_kind": "guard_reason",
                            "level": "error",
                            "reason": reason_text,
                            "object_ids": object_ids,
                            "primary_object_id": object_ids[0] if object_ids else "",
                        }
                    )
            evidence = rule.get("evidence")
            if isinstance(evidence, dict):
                object_issues = evidence.get("object_issues")
                if isinstance(object_issues, list):
                    for item in object_issues:
                        if isinstance(item, dict):
                            issues.append(dict(item))
    issue_count_by_object: dict[str, int] = {}
    for issue in issues:
        raw_object_ids = issue.get("object_ids")
        if not isinstance(raw_object_ids, list):
            continue
        for object_id in raw_object_ids:
            key = str(object_id)
            issue_count_by_object[key] = issue_count_by_object.get(key, 0) + 1
    return {
        "passed": bool(scope.get("passed")),
        "rule_count": int(scope.get("rule_count") or 0),
        "error_count": len(issues),
        "issues": issues,
        "issue_count_by_object": issue_count_by_object,
    }


def build_correspondence_view(canonical: dict[str, Any]) -> dict[str, Any]:
    module_link_items = canonical.get("links", {}).get("module_class_bindings", [])
    base_link_items = canonical.get("links", {}).get("base_class_bindings", [])
    rule_link_items = canonical.get("links", {}).get("rule_class_bindings", [])
    boundary_link_items = canonical.get("links", {}).get("boundary_param_bindings", [])
    if not isinstance(module_link_items, list):
        module_link_items = []
    if not isinstance(base_link_items, list):
        base_link_items = []
    if not isinstance(rule_link_items, list):
        rule_link_items = []
    if not isinstance(boundary_link_items, list):
        boundary_link_items = []

    module_links = {
        str(item.get("module_id") or ""): item
        for item in module_link_items
        if isinstance(item, dict) and str(item.get("module_id") or "").strip()
    }
    base_links = {
        str(item.get("base_id") or ""): item
        for item in base_link_items
        if isinstance(item, dict) and str(item.get("base_id") or "").strip()
    }
    rule_links = {
        str(item.get("rule_id") or ""): item
        for item in rule_link_items
        if isinstance(item, dict) and str(item.get("rule_id") or "").strip()
    }
    boundary_links = [
        item
        for item in boundary_link_items
        if isinstance(item, dict)
    ]

    objects: list[CorrespondenceNode] = []
    tree: list[dict[str, Any]] = []

    for module_id in _module_ids(canonical):
        framework_module = _find_module(canonical, "framework", module_id)
        config_module = _find_module(canonical, "config", module_id)
        code_module = _find_module(canonical, "code", module_id)
        module_link = module_links.get(module_id, {})
        module_symbol = str(module_link.get("module_class_symbol") or "")
        module_display = _display_name_from_symbol(module_symbol, module_id)
        module_source_ref = framework_module.get("source_ref", {}) if isinstance(framework_module, dict) else {}
        if not isinstance(module_source_ref, dict):
            module_source_ref = {}
        project_file = str(canonical.get("config", {}).get("project_file") or "")
        module_config_bindings = []
        compiled = config_module.get("compiled_config_export", {}) if isinstance(config_module, dict) else {}
        if isinstance(compiled, dict):
            item = compiled.get("module_static_param_bindings")
            if isinstance(item, list):
                module_config_bindings = [row for row in item if isinstance(row, dict)]

        module_framework_target = _source_ref_target(
            target_kind="framework_definition",
            layer="framework",
            source_ref=module_source_ref,
            symbol=module_id,
            label="Framework module definition",
            is_primary=False,
            is_editable=True,
        )
        module_correspondence_target = _code_correspondence_target(
            kind="module",
            label="Code correspondence anchor",
            symbol=module_symbol or "project_runtime.code_layer:ModuleContract",
            is_primary=True,
        )
        module_implementation_target = _module_runtime_implementation_target(
            code_module=code_module,
            fallback_symbol=module_symbol or "project_runtime.code_layer:build_code_modules",
            is_primary=False,
        )
        module_targets = (
            module_correspondence_target,
            module_framework_target,
            module_implementation_target,
        )
        module_object_id = module_id
        objects.append(
            CorrespondenceNode(
                object_kind="module",
                object_id=module_object_id,
                owner_module_id=module_id,
                display_name=module_display,
                materialization_kind="runtime_dynamic_type",
                primary_nav_target_kind="code_correspondence",
                primary_edit_target_kind="framework_definition",
                correspondence_anchor=module_correspondence_target.to_dict(),
                implementation_anchor=module_implementation_target.to_dict(),
                navigation_targets=module_targets,
            )
        )

        base_object_ids: list[str] = []
        rule_object_ids: list[str] = []
        boundary_object_ids: list[str] = []
        static_param_object_ids: list[str] = []
        runtime_param_object_ids: list[str] = []

        framework_bases = framework_module.get("bases", []) if isinstance(framework_module, dict) else []
        if not isinstance(framework_bases, list):
            framework_bases = []
        for base in framework_bases:
            if not isinstance(base, dict):
                continue
            short_base_id = str(base.get("base_id") or "")
            if not short_base_id:
                continue
            base_id = f"{module_id}.{short_base_id}"
            base_link = base_links.get(base_id, {})
            base_symbol = str(base_link.get("base_class_symbol") or "")
            base_framework_target = _source_ref_target(
                target_kind="framework_definition",
                layer="framework",
                source_ref=base.get("source_ref", {}) if isinstance(base.get("source_ref"), dict) else {},
                symbol=base_id,
                label="Framework base definition",
                is_primary=True,
                is_editable=True,
            )
            base_code_correspondence_target = _code_correspondence_target(
                kind="base",
                label="Base correspondence anchor",
                symbol=base_symbol or "project_runtime.code_layer:BaseContract",
                is_primary=False,
            )
            base_code_implementation_target = _module_runtime_implementation_target(
                code_module=code_module,
                fallback_symbol=base_symbol or "project_runtime.code_layer:build_code_modules",
                is_primary=False,
            )
            base_targets = (
                base_framework_target,
                base_code_correspondence_target,
                base_code_implementation_target,
            )
            base_object_ids.append(base_id)
            objects.append(
                CorrespondenceNode(
                    object_kind="base",
                    object_id=base_id,
                    owner_module_id=module_id,
                    display_name=_display_name_from_symbol(base_symbol, short_base_id),
                    materialization_kind="runtime_dynamic_type",
                    primary_nav_target_kind="framework_definition",
                    primary_edit_target_kind="framework_definition",
                    correspondence_anchor=base_code_correspondence_target.to_dict(),
                    implementation_anchor=base_code_implementation_target.to_dict(),
                    navigation_targets=base_targets,
                )
            )

        framework_rules = framework_module.get("rules", []) if isinstance(framework_module, dict) else []
        if not isinstance(framework_rules, list):
            framework_rules = []
        for rule in framework_rules:
            if not isinstance(rule, dict):
                continue
            short_rule_id = str(rule.get("rule_id") or "")
            if not short_rule_id:
                continue
            rule_id = f"{module_id}.{short_rule_id}"
            rule_link = rule_links.get(rule_id, {})
            rule_symbol = str(rule_link.get("rule_class_symbol") or "")
            rule_framework_target = _source_ref_target(
                target_kind="framework_definition",
                layer="framework",
                source_ref=rule.get("source_ref", {}) if isinstance(rule.get("source_ref"), dict) else {},
                symbol=rule_id,
                label="Framework rule definition",
                is_primary=True,
                is_editable=True,
            )
            rule_code_correspondence_target = _code_correspondence_target(
                kind="rule",
                label="Rule correspondence anchor",
                symbol=rule_symbol or "project_runtime.code_layer:RuleContract",
                is_primary=False,
            )
            rule_code_implementation_target = _module_runtime_implementation_target(
                code_module=code_module,
                fallback_symbol=rule_symbol or "project_runtime.code_layer:build_code_modules",
                is_primary=False,
            )
            rule_targets = (
                rule_framework_target,
                rule_code_correspondence_target,
                rule_code_implementation_target,
            )
            rule_object_ids.append(rule_id)
            objects.append(
                CorrespondenceNode(
                    object_kind="rule",
                    object_id=rule_id,
                    owner_module_id=module_id,
                    display_name=_display_name_from_symbol(rule_symbol, short_rule_id),
                    materialization_kind="runtime_dynamic_type",
                    primary_nav_target_kind="framework_definition",
                    primary_edit_target_kind="framework_definition",
                    correspondence_anchor=rule_code_correspondence_target.to_dict(),
                    implementation_anchor=rule_code_implementation_target.to_dict(),
                    navigation_targets=rule_targets,
                )
            )

        framework_boundaries = framework_module.get("boundaries", []) if isinstance(framework_module, dict) else []
        if not isinstance(framework_boundaries, list):
            framework_boundaries = []
        for boundary in framework_boundaries:
            if not isinstance(boundary, dict):
                continue
            boundary_id = str(boundary.get("boundary_id") or "")
            if not boundary_id:
                continue
            boundary_link = next(
                (
                    item
                    for item in boundary_links
                    if str(item.get("owner_module_id") or "") == module_id
                    and str(item.get("boundary_id") or "") == boundary_id
                ),
                {},
            )
            boundary_object_id = f"{module_id}::boundary::{boundary_id}"
            boundary_object_ids.append(boundary_object_id)

            framework_target = _source_ref_target(
                target_kind="framework_definition",
                layer="framework",
                source_ref=boundary.get("source_ref", {}) if isinstance(boundary.get("source_ref"), dict) else {},
                symbol=boundary_object_id,
                label="Framework boundary definition",
                is_primary=False,
                is_editable=True,
            )
            config_exact_path = str(boundary_link.get("config_source_exact_path") or "")
            config_line = _path_section_line(project_file, config_exact_path) if project_file and config_exact_path else 1
            config_target = _target(
                target_kind="config_source",
                layer="config",
                file_path=project_file or "projects/knowledge_base_basic/project.toml",
                start_line=config_line,
                end_line=config_line,
                symbol=config_exact_path,
                label="Config boundary source",
                is_primary=True,
                is_editable=True,
            )
            correspondence_target = _code_correspondence_target(
                kind="boundary",
                label="Boundary correspondence anchor",
                symbol=str(boundary_link.get("static_params_class_symbol") or "project_runtime.code_layer:CodeBoundaryStaticClass"),
                is_primary=False,
            )
            correspondence_target = _boundary_slot_target(
                code_module=code_module,
                boundary_id=boundary_id,
                slot_kind="module_static_param",
                target_kind="code_correspondence",
                fallback_symbol=str(boundary_link.get("static_params_class_symbol") or "project_runtime.code_layer:CodeBoundaryStaticClass"),
                fallback_label="Boundary correspondence anchor",
                fallback_target=correspondence_target,
                is_primary=False,
            )
            implementation_target = _module_runtime_implementation_target(
                code_module=code_module,
                fallback_symbol=str(boundary_link.get("runtime_params_class_symbol") or "project_runtime.code_layer:build_code_modules"),
                is_primary=False,
            )
            implementation_target = _boundary_slot_target(
                code_module=code_module,
                boundary_id=boundary_id,
                slot_kind="runtime_export",
                target_kind="code_implementation",
                fallback_symbol=str(boundary_link.get("runtime_params_class_symbol") or "project_runtime.code_layer:build_code_modules"),
                fallback_label="Code implementation anchor",
                fallback_target=implementation_target,
                is_primary=False,
            )
            deprecated_target = _deprecated_alias_target(
                str(boundary_link.get("deprecated_boundary_anchor_path") or f"exact_export.boundaries.{boundary_id}"),
                is_primary=False,
            )
            boundary_targets = (
                config_target,
                framework_target,
                correspondence_target,
                implementation_target,
                deprecated_target,
            )
            objects.append(
                CorrespondenceNode(
                    object_kind="boundary",
                    object_id=boundary_object_id,
                    owner_module_id=module_id,
                    display_name=boundary_id,
                    materialization_kind="source_symbol",
                    primary_nav_target_kind="config_source",
                    primary_edit_target_kind="config_source",
                    correspondence_anchor=correspondence_target.to_dict(),
                    implementation_anchor=implementation_target.to_dict(),
                    navigation_targets=boundary_targets,
                )
            )

            static_field = str(boundary_link.get("static_field_name") or "")
            runtime_field = str(boundary_link.get("runtime_field_name") or static_field)
            static_object_id = f"{module_id}::static_param::{static_field}"
            runtime_object_id = f"{module_id}::runtime_param::{runtime_field}"
            static_param_object_ids.append(static_object_id)
            runtime_param_object_ids.append(runtime_object_id)

            static_correspondence_target = _code_correspondence_target(
                kind="static_param",
                label="Static params correspondence anchor",
                symbol=str(boundary_link.get("static_params_class_symbol") or "project_runtime.code_layer:StaticBoundaryParamsContract"),
                is_primary=False,
            )
            static_correspondence_target = _boundary_slot_target(
                code_module=code_module,
                boundary_id=boundary_id,
                slot_kind="module_static_param",
                target_kind="code_correspondence",
                fallback_symbol=str(boundary_link.get("static_params_class_symbol") or "project_runtime.code_layer:StaticBoundaryParamsContract"),
                fallback_label="Static params correspondence anchor",
                fallback_target=static_correspondence_target,
                is_primary=False,
            )
            static_targets = (
                config_target,
                static_correspondence_target,
                implementation_target,
                deprecated_target,
            )
            objects.append(
                CorrespondenceNode(
                    object_kind="static_param",
                    object_id=static_object_id,
                    owner_module_id=module_id,
                    display_name=static_field,
                    materialization_kind="runtime_dynamic_type",
                    primary_nav_target_kind="config_source",
                    primary_edit_target_kind="config_source",
                    correspondence_anchor=static_correspondence_target.to_dict(),
                    implementation_anchor=implementation_target.to_dict(),
                    navigation_targets=static_targets,
                )
            )

            runtime_correspondence_target = _code_correspondence_target(
                kind="runtime_param",
                label="Runtime params correspondence anchor",
                symbol=str(boundary_link.get("runtime_params_class_symbol") or "project_runtime.code_layer:RuntimeBoundaryParamsContract"),
                is_primary=True,
            )
            runtime_correspondence_target = _boundary_slot_target(
                code_module=code_module,
                boundary_id=boundary_id,
                slot_kind="runtime_export",
                target_kind="code_correspondence",
                fallback_symbol=str(boundary_link.get("runtime_params_class_symbol") or "project_runtime.code_layer:RuntimeBoundaryParamsContract"),
                fallback_label="Runtime params correspondence anchor",
                fallback_target=runtime_correspondence_target,
                is_primary=True,
            )
            runtime_targets = (
                runtime_correspondence_target,
                framework_target,
                implementation_target,
            )
            objects.append(
                CorrespondenceNode(
                    object_kind="runtime_param",
                    object_id=runtime_object_id,
                    owner_module_id=module_id,
                    display_name=runtime_field,
                    materialization_kind="runtime_dynamic_type",
                    primary_nav_target_kind="code_correspondence",
                    primary_edit_target_kind="code_correspondence",
                    correspondence_anchor=runtime_correspondence_target.to_dict(),
                    implementation_anchor=implementation_target.to_dict(),
                    navigation_targets=runtime_targets,
                )
            )

        tree.append(
            _module_tree_node(
                module_id=module_id,
                module_object_id=module_object_id,
                base_ids=base_object_ids,
                rule_ids=rule_object_ids,
                boundary_ids=boundary_object_ids,
                static_param_ids=static_param_object_ids,
                runtime_param_ids=runtime_param_object_ids,
            )
        )

    object_payload = [item.to_dict() for item in objects]
    object_index = {item["object_id"]: item for item in object_payload}
    return {
        "correspondence_schema_version": CORRESPONDENCE_SCHEMA_VERSION,
        "objects": object_payload,
        "object_index": object_index,
        "tree": tree,
        "validation_summary": _guard_summary(canonical, object_payload),
    }
