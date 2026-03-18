from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
from functools import lru_cache
import inspect
from pathlib import Path
from typing import Any

from project_runtime.code_layer import CodeModuleBinding
from project_runtime.config_layer import ConfigModuleBinding
from project_runtime.correspondence_contracts import BaseContract, ModuleContract, RuleContract
from project_runtime.framework_layer import FrameworkModuleClass
from project_runtime.utils import REPO_ROOT, relative_path
from rule_validation_models import RuleValidationOutcome, RuleValidationSummary

_MAX_REASONS = 80
_PILOT_MODULE_ID = "backend.L2.M0"


def _symbol(class_type: type[Any]) -> str:
    return f"{class_type.__module__}:{class_type.__name__}"


def _source_ref_for_class(class_type: type[Any], *, fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        file_path = inspect.getsourcefile(class_type)
        _, line_no = inspect.getsourcelines(class_type)
    except (OSError, TypeError):
        if fallback:
            return dict(fallback)
        return {}
    if not file_path:
        if fallback:
            return dict(fallback)
        return {}
    return {
        "file_path": relative_path(Path(file_path).resolve()),
        "line": int(line_no),
    }


def _materialization_kind_for_class(class_type: type[Any]) -> str:
    source_ref = _source_ref_for_class(class_type)
    if not source_ref:
        return "runtime_dynamic_type"
    file_path = str(source_ref.get("file_path") or "")
    if not file_path:
        return "runtime_dynamic_type"
    return "static_python_class"


def _annotation_name(annotation: ast.expr | None) -> str:
    if annotation is None:
        return ""
    if isinstance(annotation, ast.Name):
        return annotation.id
    if isinstance(annotation, ast.Attribute):
        base = _annotation_name(annotation.value)
        return f"{base}.{annotation.attr}" if base else annotation.attr
    if isinstance(annotation, ast.Constant) and isinstance(annotation.value, str):
        return str(annotation.value)
    if isinstance(annotation, ast.Subscript):
        return _annotation_name(annotation.value)
    return ""


def _call_name(call: ast.Call) -> str:
    func = call.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        if isinstance(func.value, ast.Name):
            return f"{func.value.id}.{func.attr}"
        return func.attr
    return ""


def _extract_boundary_reads(function_node: ast.FunctionDef) -> set[str]:
    boundary_ids: set[str] = set()
    for node in ast.walk(function_node):
        if not isinstance(node, ast.Call):
            continue
        if not node.args:
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        if func.attr != "boundary_value":
            continue
        owner = func.value
        if not isinstance(owner, ast.Attribute):
            continue
        if owner.attr != "_module":
            continue
        if not isinstance(owner.value, ast.Name) or owner.value.id != "self":
            continue
        first_arg = node.args[0]
        if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
            boundary_ids.add(str(first_arg.value))
    return boundary_ids


def _class_name_to_node(tree: ast.Module) -> dict[str, ast.ClassDef]:
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }


def _function_name_to_node(class_node: ast.ClassDef) -> dict[str, ast.FunctionDef]:
    return {
        node.name: node
        for node in class_node.body
        if isinstance(node, ast.FunctionDef)
    }


@lru_cache(maxsize=32)
def _module_ast(file_path: str) -> tuple[ast.Module | None, dict[str, ast.ClassDef]]:
    candidate = (REPO_ROOT / file_path).resolve()
    if not candidate.exists():
        return None, {}
    try:
        text = candidate.read_text(encoding="utf-8")
    except OSError:
        return None, {}
    try:
        tree = ast.parse(text, filename=file_path)
    except SyntaxError:
        return None, {}
    return tree, _class_name_to_node(tree)


def _tuple_of_text(value: Any) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        return tuple()
    return tuple(str(item) for item in value)


def _declared_model(
    framework_module: type[FrameworkModuleClass],
    config_binding: ConfigModuleBinding,
    code_binding: CodeModuleBinding,
) -> dict[str, Any]:
    module_type = code_binding.code_module.ModuleType
    static_type = code_binding.code_module.StaticBoundaryParamsType
    runtime_type = code_binding.code_module.RuntimeBoundaryParamsType
    base_types = code_binding.code_module.BaseTypes
    rule_types = code_binding.code_module.RuleTypes
    module_link = code_binding.code_module.code_bindings.get("module_class_binding", {})
    boundary_bindings = code_binding.code_module.code_bindings.get("boundary_param_bindings", [])
    boundary_binding_by_id = {
        str(item.get("boundary_id") or ""): item
        for item in boundary_bindings
        if isinstance(item, Mapping)
    }
    return {
        "module_id": framework_module.module_id,
        "module": {
            "symbol": _symbol(module_type),
            "source_ref": _source_ref_for_class(module_type, fallback=code_binding.code_module.source_ref),
            "materialization_kind": _materialization_kind_for_class(module_type),
            "boundary_field_map": dict(getattr(module_type, "boundary_field_map", {})),
            "merge_policy": str(getattr(module_type, "merge_policy", "")),
            "static_params_symbol": _symbol(static_type),
            "runtime_params_symbol": _symbol(runtime_type),
            "static_params_source_ref": _source_ref_for_class(static_type),
            "runtime_params_source_ref": _source_ref_for_class(runtime_type),
            "module_key": str(module_link.get("module_key") or module_type.module_key),
        },
        "bases": {
            str(base_type.framework_base_id): {
                "base_id": str(base_type.framework_base_id),
                "symbol": _symbol(base_type),
                "source_ref": _source_ref_for_class(base_type),
                "materialization_kind": _materialization_kind_for_class(base_type),
                "declared_boundary_ids": list(_tuple_of_text(getattr(base_type, "boundary_ids", tuple()))),
            }
            for base_type in base_types
            if isinstance(base_type, type) and issubclass(base_type, BaseContract)
        },
        "rules": {
            str(rule_type.framework_rule_id): {
                "rule_id": str(rule_type.framework_rule_id),
                "symbol": _symbol(rule_type),
                "source_ref": _source_ref_for_class(rule_type),
                "materialization_kind": _materialization_kind_for_class(rule_type),
                "declared_base_ids": list(_tuple_of_text(getattr(rule_type, "base_ids", tuple()))),
                "declared_boundary_ids": list(_tuple_of_text(getattr(rule_type, "boundary_ids", tuple()))),
            }
            for rule_type in rule_types
            if isinstance(rule_type, type) and issubclass(rule_type, RuleContract)
        },
        "framework": {
            "module_source_ref": dict(framework_module.source_ref),
            "boundary_ids": [item.boundary_id for item in framework_module.boundaries],
            "rule_ids": [f"{framework_module.module_id}.{item.rule_id}" for item in framework_module.rule_classes],
            "base_ids": [f"{framework_module.module_id}.{item.base_id}" for item in framework_module.base_classes],
        },
        "config": {
            "project_file": config_binding.config_module.source_ref.get("file_path", ""),
            "boundary_bindings": {
                boundary_id: {
                    "config_source_exact_path": str(record.get("config_source_exact_path") or ""),
                    "exact_export_static_path": str(record.get("exact_export_static_path") or ""),
                    "static_field_name": str(record.get("static_field_name") or ""),
                    "runtime_field_name": str(record.get("runtime_field_name") or ""),
                }
                for boundary_id, record in boundary_binding_by_id.items()
            },
        },
    }


def _extract_base_method_boundaries(class_node: ast.ClassDef) -> dict[str, set[str]]:
    method_boundaries: dict[str, set[str]] = {}
    for name, function_node in _function_name_to_node(class_node).items():
        if name == "__init__":
            continue
        method_boundaries[name] = _extract_boundary_reads(function_node)
    return method_boundaries


def _extract_rule_constructor_bases(
    class_node: ast.ClassDef,
    base_id_by_class_name: dict[str, str],
) -> tuple[dict[str, str], list[str]]:
    functions = _function_name_to_node(class_node)
    init_node = functions.get("__init__")
    if init_node is None:
        return {}, []
    arg_base_by_name: dict[str, str] = {}
    for arg in init_node.args.args[1:]:
        annotation_name = _annotation_name(arg.annotation).split(".")[-1]
        base_id = base_id_by_class_name.get(annotation_name)
        if base_id:
            arg_base_by_name[arg.arg] = base_id
    attr_base_map: dict[str, str] = {}
    for stmt in init_node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if len(stmt.targets) != 1:
            continue
        target = stmt.targets[0]
        value = stmt.value
        if not isinstance(target, ast.Attribute):
            continue
        if not isinstance(target.value, ast.Name) or target.value.id != "self":
            continue
        if not isinstance(value, ast.Name):
            continue
        base_id = arg_base_by_name.get(value.id)
        if base_id:
            attr_base_map[target.attr] = base_id
    return attr_base_map, [arg_base_by_name[name] for name in arg_base_by_name]


def _extract_rule_effective(
    class_node: ast.ClassDef,
    *,
    base_id_by_attr: dict[str, str],
    base_method_boundaries: dict[str, dict[str, set[str]]],
) -> tuple[set[str], set[str], list[dict[str, str]]]:
    effective_boundaries: set[str] = set()
    used_base_ids: set[str] = set()
    base_calls: list[dict[str, str]] = []
    for name, function_node in _function_name_to_node(class_node).items():
        if name == "__init__":
            continue
        effective_boundaries.update(_extract_boundary_reads(function_node))
        for node in ast.walk(function_node):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            owner = func.value
            if not isinstance(owner, ast.Attribute):
                continue
            if not isinstance(owner.value, ast.Name) or owner.value.id != "self":
                continue
            base_id = base_id_by_attr.get(owner.attr)
            if not base_id:
                continue
            used_base_ids.add(base_id)
            method_name = func.attr
            base_calls.append({"base_id": base_id, "method": method_name})
            effective_boundaries.update(base_method_boundaries.get(base_id, {}).get(method_name, set()))
    return effective_boundaries, used_base_ids, base_calls


def _extract_module_assembly(
    class_node: ast.ClassDef,
    *,
    base_id_by_class_name: dict[str, str],
    rule_id_by_class_name: dict[str, str],
) -> tuple[list[str], list[str], dict[str, list[str]]]:
    functions = _function_name_to_node(class_node)
    init_node = functions.get("__init__")
    if init_node is None:
        return [], [], {}
    base_ids: list[str] = []
    rule_ids: list[str] = []
    base_id_by_self_attr: dict[str, str] = {}
    rule_injected: dict[str, list[str]] = {}
    for stmt in init_node.body:
        if not isinstance(stmt, ast.Assign):
            continue
        if len(stmt.targets) != 1:
            continue
        target = stmt.targets[0]
        value = stmt.value
        if not isinstance(target, ast.Attribute):
            continue
        if not isinstance(target.value, ast.Name) or target.value.id != "self":
            continue
        if not isinstance(value, ast.Call):
            continue
        call_name = _call_name(value).split(".")[-1]
        base_id = base_id_by_class_name.get(call_name)
        if base_id:
            base_ids.append(base_id)
            base_id_by_self_attr[target.attr] = base_id
            continue
        rule_id = rule_id_by_class_name.get(call_name)
        if not rule_id:
            continue
        rule_ids.append(rule_id)
        injected_base_ids: list[str] = []
        for arg in value.args:
            if not isinstance(arg, ast.Attribute):
                continue
            if not isinstance(arg.value, ast.Name) or arg.value.id != "self":
                continue
            mapped = base_id_by_self_attr.get(arg.attr)
            if mapped:
                injected_base_ids.append(mapped)
        rule_injected[rule_id] = injected_base_ids
    return base_ids, rule_ids, rule_injected


def _effective_model(code_binding: CodeModuleBinding, declared: dict[str, Any]) -> dict[str, Any]:
    module_type = code_binding.code_module.ModuleType
    module_source = _source_ref_for_class(module_type)
    file_path = str(module_source.get("file_path") or "")
    if not file_path:
        return {
            "status": "unsupported",
            "reason": "module source file unavailable",
        }
    _, class_map = _module_ast(file_path)
    if not class_map:
        return {
            "status": "unsupported",
            "reason": f"cannot parse module source: {file_path}",
        }

    base_types = code_binding.code_module.BaseTypes
    rule_types = code_binding.code_module.RuleTypes
    base_id_by_class_name = {
        base_type.__name__: str(base_type.framework_base_id)
        for base_type in base_types
        if isinstance(base_type, type) and issubclass(base_type, BaseContract)
    }
    rule_id_by_class_name = {
        rule_type.__name__: str(rule_type.framework_rule_id)
        for rule_type in rule_types
        if isinstance(rule_type, type) and issubclass(rule_type, RuleContract)
    }
    module_class_node = class_map.get(module_type.__name__)
    if module_class_node is None:
        return {
            "status": "unsupported",
            "reason": f"module class node missing: {module_type.__name__}",
        }

    base_models: dict[str, Any] = {}
    base_method_boundaries: dict[str, dict[str, set[str]]] = {}
    for base_type in base_types:
        base_id = str(getattr(base_type, "framework_base_id", "")).strip()
        if not base_id:
            continue
        class_node = class_map.get(base_type.__name__)
        if class_node is None:
            base_models[base_id] = {"status": "missing_class_node"}
            continue
        method_boundaries = _extract_base_method_boundaries(class_node)
        base_method_boundaries[base_id] = method_boundaries
        boundary_ids = sorted({item for values in method_boundaries.values() for item in values})
        base_models[base_id] = {
            "symbol": _symbol(base_type),
            "source_ref": _source_ref_for_class(base_type),
            "effective_boundary_ids": boundary_ids,
            "method_boundary_reads": {
                method: sorted(boundaries)
                for method, boundaries in sorted(method_boundaries.items())
            },
        }

    rule_models: dict[str, Any] = {}
    for rule_type in rule_types:
        rule_id = str(getattr(rule_type, "framework_rule_id", "")).strip()
        if not rule_id:
            continue
        class_node = class_map.get(rule_type.__name__)
        if class_node is None:
            rule_models[rule_id] = {"status": "missing_class_node"}
            continue
        attr_base_map, constructor_base_ids = _extract_rule_constructor_bases(
            class_node,
            base_id_by_class_name,
        )
        effective_boundaries, used_base_ids, base_calls = _extract_rule_effective(
            class_node,
            base_id_by_attr=attr_base_map,
            base_method_boundaries=base_method_boundaries,
        )
        rule_models[rule_id] = {
            "symbol": _symbol(rule_type),
            "source_ref": _source_ref_for_class(rule_type),
            "effective_base_ids": list(dict.fromkeys(constructor_base_ids)),
            "effective_boundary_ids": sorted(effective_boundaries),
            "used_base_ids": sorted(used_base_ids),
            "base_method_calls": base_calls,
        }

    assembled_base_ids, assembled_rule_ids, module_rule_injected = _extract_module_assembly(
        module_class_node,
        base_id_by_class_name=base_id_by_class_name,
        rule_id_by_class_name=rule_id_by_class_name,
    )
    return {
        "status": "supported",
        "module": {
            "symbol": declared["module"]["symbol"],
            "source_ref": module_source,
            "module_init_source_ref": {
                "file_path": file_path,
                "line": int(module_class_node.lineno),
            },
            "effective_assembled_base_ids": list(dict.fromkeys(assembled_base_ids)),
            "effective_assembled_rule_ids": list(dict.fromkeys(assembled_rule_ids)),
            "module_rule_injected_base_ids": {
                rule_id: list(dict.fromkeys(base_ids))
                for rule_id, base_ids in sorted(module_rule_injected.items())
            },
        },
        "bases": base_models,
        "rules": rule_models,
    }


def _issue(
    *,
    issue_kind: str,
    level: str,
    module_id: str,
    object_id: str,
    reason: str,
) -> dict[str, Any]:
    return {
        "issue_kind": issue_kind,
        "level": level,
        "module_id": module_id,
        "object_ids": [object_id] if object_id else [module_id],
        "primary_object_id": object_id or module_id,
        "reason": reason,
    }


def _module_diff(module_id: str, declared: dict[str, Any], effective: dict[str, Any]) -> dict[str, Any]:
    conformance_errors: list[dict[str, Any]] = []
    undeclared_usage: list[dict[str, Any]] = []
    audit_drift: list[dict[str, Any]] = []

    if effective.get("status") != "supported":
        if module_id == _PILOT_MODULE_ID:
            conformance_errors.append(
                _issue(
                    issue_kind="conformance_error",
                    level="error",
                    module_id=module_id,
                    object_id=module_id,
                    reason=f"effective extraction unsupported for pilot module: {effective.get('reason', '')}",
                )
            )
        return {
            "conformance_error": conformance_errors,
            "undeclared_usage": undeclared_usage,
            "audit_drift": audit_drift,
            "summary": {
                "conformance_error_count": len(conformance_errors),
                "undeclared_usage_count": len(undeclared_usage),
                "audit_drift_count": len(audit_drift),
            },
        }

    declared_base_ids = set(declared["bases"].keys())
    declared_rule_ids = set(declared["rules"].keys())
    assembled_base_ids = set(effective["module"]["effective_assembled_base_ids"])
    assembled_rule_ids = set(effective["module"]["effective_assembled_rule_ids"])

    for missing_base_id in sorted(declared_base_ids - assembled_base_ids):
        conformance_errors.append(
            _issue(
                issue_kind="conformance_error",
                level="error",
                module_id=module_id,
                object_id=missing_base_id,
                reason=f"declared base not assembled in module __init__: {missing_base_id}",
            )
        )
    for extra_base_id in sorted(assembled_base_ids - declared_base_ids):
        undeclared_usage.append(
            _issue(
                issue_kind="undeclared_usage",
                level="error",
                module_id=module_id,
                object_id=module_id,
                reason=f"module __init__ assembled undeclared base: {extra_base_id}",
            )
        )
    for missing_rule_id in sorted(declared_rule_ids - assembled_rule_ids):
        conformance_errors.append(
            _issue(
                issue_kind="conformance_error",
                level="error",
                module_id=module_id,
                object_id=missing_rule_id,
                reason=f"declared rule not assembled in module __init__: {missing_rule_id}",
            )
        )
    for extra_rule_id in sorted(assembled_rule_ids - declared_rule_ids):
        undeclared_usage.append(
            _issue(
                issue_kind="undeclared_usage",
                level="error",
                module_id=module_id,
                object_id=module_id,
                reason=f"module __init__ assembled undeclared rule: {extra_rule_id}",
            )
        )

    boundary_map = declared["module"]["boundary_field_map"]
    expected_boundaries = set(declared["framework"]["boundary_ids"])
    mapped_boundaries = set(boundary_map.keys()) if isinstance(boundary_map, Mapping) else set()
    if mapped_boundaries != expected_boundaries:
        conformance_errors.append(
            _issue(
                issue_kind="conformance_error",
                level="error",
                module_id=module_id,
                object_id=module_id,
                reason=(
                    "boundary_field_map mismatch "
                    f"expected={sorted(expected_boundaries)} actual={sorted(mapped_boundaries)}"
                ),
            )
        )

    for base_id, declared_base in sorted(declared["bases"].items()):
        effective_base = effective["bases"].get(base_id)
        if not isinstance(effective_base, Mapping):
            conformance_errors.append(
                _issue(
                    issue_kind="conformance_error",
                    level="error",
                    module_id=module_id,
                    object_id=base_id,
                    reason=f"effective base extraction missing: {base_id}",
                )
            )
            continue
        declared_boundaries = set(declared_base.get("declared_boundary_ids", []))
        effective_boundaries = set(effective_base.get("effective_boundary_ids", []))
        for boundary_id in sorted(effective_boundaries - declared_boundaries):
            undeclared_usage.append(
                _issue(
                    issue_kind="undeclared_usage",
                    level="error",
                    module_id=module_id,
                    object_id=base_id,
                    reason=f"base reads undeclared boundary: {base_id} -> {boundary_id}",
                )
            )
        for boundary_id in sorted(declared_boundaries - effective_boundaries):
            audit_drift.append(
                _issue(
                    issue_kind="audit_drift",
                    level="warning",
                    module_id=module_id,
                    object_id=base_id,
                    reason=f"declared boundary not effectively read by base: {base_id} -> {boundary_id}",
                )
            )

    for rule_id, declared_rule in sorted(declared["rules"].items()):
        effective_rule = effective["rules"].get(rule_id)
        if not isinstance(effective_rule, Mapping):
            conformance_errors.append(
                _issue(
                    issue_kind="conformance_error",
                    level="error",
                    module_id=module_id,
                    object_id=rule_id,
                    reason=f"effective rule extraction missing: {rule_id}",
                )
            )
            continue
        declared_base_ids_for_rule = set(declared_rule.get("declared_base_ids", []))
        effective_base_ids_for_rule = set(effective_rule.get("effective_base_ids", []))
        declared_boundary_ids_for_rule = set(declared_rule.get("declared_boundary_ids", []))
        effective_boundary_ids_for_rule = set(effective_rule.get("effective_boundary_ids", []))
        for base_id in sorted(effective_base_ids_for_rule - declared_base_ids_for_rule):
            undeclared_usage.append(
                _issue(
                    issue_kind="undeclared_usage",
                    level="error",
                    module_id=module_id,
                    object_id=rule_id,
                    reason=f"rule constructor injects undeclared base: {rule_id} -> {base_id}",
                )
            )
        for base_id in sorted(declared_base_ids_for_rule - effective_base_ids_for_rule):
            audit_drift.append(
                _issue(
                    issue_kind="audit_drift",
                    level="warning",
                    module_id=module_id,
                    object_id=rule_id,
                    reason=f"declared rule base not injected by constructor: {rule_id} -> {base_id}",
                )
            )
        for boundary_id in sorted(effective_boundary_ids_for_rule - declared_boundary_ids_for_rule):
            undeclared_usage.append(
                _issue(
                    issue_kind="undeclared_usage",
                    level="error",
                    module_id=module_id,
                    object_id=rule_id,
                    reason=f"rule reads undeclared boundary: {rule_id} -> {boundary_id}",
                )
            )
        for boundary_id in sorted(declared_boundary_ids_for_rule - effective_boundary_ids_for_rule):
            audit_drift.append(
                _issue(
                    issue_kind="audit_drift",
                    level="warning",
                    module_id=module_id,
                    object_id=rule_id,
                    reason=f"declared rule boundary not effectively read: {rule_id} -> {boundary_id}",
                )
            )
        assembled_rule_injected = set(
            effective["module"]["module_rule_injected_base_ids"].get(rule_id, [])
        )
        if assembled_rule_injected and assembled_rule_injected != effective_base_ids_for_rule:
            conformance_errors.append(
                _issue(
                    issue_kind="conformance_error",
                    level="error",
                    module_id=module_id,
                    object_id=rule_id,
                    reason=(
                        "rule constructor bases and module assembly injected bases mismatch "
                        f"{rule_id}: constructor={sorted(effective_base_ids_for_rule)} "
                        f"module_init={sorted(assembled_rule_injected)}"
                    ),
                )
            )

    return {
        "conformance_error": conformance_errors,
        "undeclared_usage": undeclared_usage,
        "audit_drift": audit_drift,
        "summary": {
            "conformance_error_count": len(conformance_errors),
            "undeclared_usage_count": len(undeclared_usage),
            "audit_drift_count": len(audit_drift),
        },
    }


def build_codegen_consistency_report(
    *,
    framework_modules: Sequence[type[FrameworkModuleClass]],
    config_modules: Sequence[ConfigModuleBinding],
    code_modules: Sequence[CodeModuleBinding],
) -> dict[str, Any]:
    framework_by_module = {module.module_id: module for module in framework_modules}
    config_by_module = {binding.framework_module.module_id: binding for binding in config_modules}
    code_by_module = {binding.framework_module.module_id: binding for binding in code_modules}

    module_reports: list[dict[str, Any]] = []
    all_conformance: list[dict[str, Any]] = []
    all_undeclared: list[dict[str, Any]] = []
    all_drift: list[dict[str, Any]] = []

    for module_id in sorted(framework_by_module):
        framework_module = framework_by_module[module_id]
        config_binding = config_by_module.get(module_id)
        code_binding = code_by_module.get(module_id)
        if config_binding is None or code_binding is None:
            module_reports.append(
                {
                    "module_id": module_id,
                    "status": "unsupported",
                    "declared": {},
                    "effective": {
                        "status": "unsupported",
                        "reason": "missing config/code binding",
                    },
                    "diff": {
                        "conformance_error": [],
                        "undeclared_usage": [],
                        "audit_drift": [],
                        "summary": {
                            "conformance_error_count": 0,
                            "undeclared_usage_count": 0,
                            "audit_drift_count": 0,
                        },
                    },
                }
            )
            continue

        declared = _declared_model(framework_module, config_binding, code_binding)
        if module_id != _PILOT_MODULE_ID:
            effective = {
                "status": "unsupported",
                "reason": "effective extraction not enabled for this module yet",
            }
        else:
            effective = _effective_model(code_binding, declared)
        diff = _module_diff(module_id, declared, effective)
        module_reports.append(
            {
                "module_id": module_id,
                "status": str(effective.get("status") or "unknown"),
                "declared": declared,
                "effective": effective,
                "diff": diff,
            }
        )
        all_conformance.extend(diff["conformance_error"])
        all_undeclared.extend(diff["undeclared_usage"])
        all_drift.extend(diff["audit_drift"])

    return {
        "scope": "codegen_consistency_guard",
        "pilot_module_id": _PILOT_MODULE_ID,
        "modules": module_reports,
        "summary": {
            "conformance_error_count": len(all_conformance),
            "undeclared_usage_count": len(all_undeclared),
            "audit_drift_count": len(all_drift),
            "error_count": len(all_conformance) + len(all_undeclared),
            "supported_module_count": sum(1 for item in module_reports if item.get("status") == "supported"),
            "unsupported_module_count": sum(1 for item in module_reports if item.get("status") != "supported"),
        },
    }


def summarize_codegen_consistency_guard(
    *,
    framework_modules: Sequence[type[FrameworkModuleClass]],
    config_modules: Sequence[ConfigModuleBinding],
    code_modules: Sequence[CodeModuleBinding],
) -> tuple[RuleValidationSummary, dict[str, Any]]:
    report = build_codegen_consistency_report(
        framework_modules=framework_modules,
        config_modules=config_modules,
        code_modules=code_modules,
    )
    reasons: list[str] = []
    object_issues: list[dict[str, Any]] = []
    for module_report in report["modules"]:
        diff = module_report.get("diff", {})
        conformance_items = diff.get("conformance_error", [])
        undeclared_items = diff.get("undeclared_usage", [])
        drift_items = diff.get("audit_drift", [])
        for item in conformance_items:
            if isinstance(item, Mapping):
                object_issues.append(dict(item))
                reason = str(item.get("reason") or "")
                if reason:
                    reasons.append(f"CONFORMANCE_ERROR: {reason}")
        for item in undeclared_items:
            if isinstance(item, Mapping):
                object_issues.append(dict(item))
                reason = str(item.get("reason") or "")
                if reason:
                    reasons.append(f"UNDECLARED_USAGE: {reason}")
        for item in drift_items:
            if isinstance(item, Mapping):
                object_issues.append(dict(item))
    passed = not reasons
    outcome = RuleValidationOutcome(
        rule_id="codegen_consistency.declared_vs_effective",
        name="declared vs effective codegen consistency",
        passed=passed,
        reasons=tuple(reasons[:_MAX_REASONS]),
        evidence={
            "object_issues": object_issues,
            "summary": report["summary"],
            "modules": report["modules"],
        },
    )
    return (
        RuleValidationSummary(
            module_id="framework.codegen_consistency_guard",
            rules=(outcome,),
        ),
        report,
    )

