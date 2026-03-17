from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields
from typing import Any

from project_runtime.config_layer import ConfigModuleBinding
from project_runtime.framework_layer import FrameworkModuleClass
from project_runtime.code_layer import CodeModuleBinding
from rule_validation_models import RuleValidationOutcome, RuleValidationSummary

_MAX_REASONS = 40


def _tuple_of_text(value: Any) -> tuple[str, ...]:
    if not isinstance(value, tuple):
        return tuple()
    return tuple(str(item) for item in value)


def _field_names(class_type: type[Any]) -> set[str]:
    return {field.name for field in fields(class_type)}


def _symbol(class_type: type[Any]) -> str:
    return f"{class_type.__module__}:{class_type.__name__}"


def summarize_correspondence_guard(
    *,
    framework_modules: Sequence[type[FrameworkModuleClass]],
    config_modules: Sequence[ConfigModuleBinding],
    code_modules: Sequence[CodeModuleBinding],
) -> RuleValidationSummary:
    reasons: list[str] = []
    module_symbols: dict[str, str] = {}
    base_symbols: dict[str, str] = {}
    rule_symbols: dict[str, str] = {}
    seen_symbols: dict[str, str] = {}

    framework_by_module = {module.module_id: module for module in framework_modules}
    config_by_module = {binding.framework_module.module_id: binding for binding in config_modules}
    code_by_module = {binding.framework_module.module_id: binding for binding in code_modules}

    for module_id, framework_module in framework_by_module.items():
        config_binding = config_by_module.get(module_id)
        code_binding = code_by_module.get(module_id)
        if config_binding is None:
            reasons.append(f"CORRESPONDENCE_VIOLATION: missing config module binding for {module_id}")
            continue
        if code_binding is None:
            reasons.append(f"CORRESPONDENCE_VIOLATION: missing code module binding for {module_id}")
            continue
        code_module = code_binding.code_module
        module_type = getattr(code_module, "ModuleType", None)
        static_type = getattr(code_module, "StaticBoundaryParamsType", None)
        runtime_type = getattr(code_module, "RuntimeBoundaryParamsType", None)
        base_types: tuple[type[Any], ...] = getattr(code_module, "BaseTypes", tuple())
        rule_types: tuple[type[Any], ...] = getattr(code_module, "RuleTypes", tuple())

        if not isinstance(module_type, type):
            reasons.append(f"CORRESPONDENCE_VIOLATION: module class missing for {module_id}")
            continue
        if not isinstance(static_type, type):
            reasons.append(
                "CORRESPONDENCE_VIOLATION: static params class missing "
                f"for {module_id}"
            )
            continue
        if not isinstance(runtime_type, type):
            reasons.append(
                "CORRESPONDENCE_VIOLATION: runtime params class missing "
                f"for {module_id}"
            )
            continue

        module_symbol = _symbol(module_type)
        module_symbols[module_id] = module_symbol
        if module_symbol in seen_symbols and seen_symbols[module_symbol] != module_id:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: duplicate module class symbol "
                f"{module_symbol} for {module_id} and {seen_symbols[module_symbol]}"
            )
        seen_symbols[module_symbol] = module_id

        if str(getattr(module_type, "framework_module_id", "")) != module_id:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: module class framework_module_id mismatch "
                f"for {module_id}"
            )

        static_field_names = _field_names(static_type)
        runtime_field_names = _field_names(runtime_type)
        boundary_field_map = getattr(module_type, "boundary_field_map", {})
        if not isinstance(boundary_field_map, Mapping):
            reasons.append(
                "CORRESPONDENCE_VIOLATION: module boundary_field_map missing "
                f"for {module_id}"
            )
            boundary_field_map = {}

        expected_boundary_ids = tuple(boundary.boundary_id for boundary in framework_module.boundaries)
        expected_base_ids = {
            f"{module_id}.{base.base_id}"
            for base in framework_module.base_classes
        }
        expected_rule_ids = {
            f"{module_id}.{rule.rule_id}"
            for rule in framework_module.rule_classes
        }

        actual_base_ids: set[str] = set()
        actual_rule_ids: set[str] = set()

        if not isinstance(base_types, tuple):
            reasons.append(f"CORRESPONDENCE_VIOLATION: BaseTypes must be tuple for {module_id}")
            base_types = tuple()
        if not isinstance(rule_types, tuple):
            reasons.append(f"CORRESPONDENCE_VIOLATION: RuleTypes must be tuple for {module_id}")
            rule_types = tuple()

        for base_type in base_types:
            if not isinstance(base_type, type):
                reasons.append(f"CORRESPONDENCE_VIOLATION: invalid base class in {module_id}")
                continue
            base_id = str(getattr(base_type, "framework_base_id", "")).strip()
            owner_id = str(getattr(base_type, "owner_module_id", "")).strip()
            if not base_id:
                reasons.append(f"CORRESPONDENCE_VIOLATION: base class missing framework_base_id in {module_id}")
                continue
            if owner_id != module_id:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: base class owner mismatch "
                    f"{base_id} owner={owner_id} expected={module_id}"
                )
            actual_base_ids.add(base_id)
            base_symbol = _symbol(base_type)
            if base_id in base_symbols and base_symbols[base_id] != base_symbol:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: base mapped to multiple class symbols "
                    f"{base_id}"
                )
            base_symbols[base_id] = base_symbol

        for rule_type in rule_types:
            if not isinstance(rule_type, type):
                reasons.append(f"CORRESPONDENCE_VIOLATION: invalid rule class in {module_id}")
                continue
            rule_id = str(getattr(rule_type, "framework_rule_id", "")).strip()
            owner_id = str(getattr(rule_type, "owner_module_id", "")).strip()
            base_ids = _tuple_of_text(getattr(rule_type, "base_ids", tuple()))
            boundary_ids = _tuple_of_text(getattr(rule_type, "boundary_ids", tuple()))
            if not rule_id:
                reasons.append(f"CORRESPONDENCE_VIOLATION: rule class missing framework_rule_id in {module_id}")
                continue
            if owner_id != module_id:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: rule class owner mismatch "
                    f"{rule_id} owner={owner_id} expected={module_id}"
                )
            if not base_ids:
                reasons.append(f"CORRESPONDENCE_VIOLATION: rule base_ids missing {rule_id}")
            if not boundary_ids:
                reasons.append(f"CORRESPONDENCE_VIOLATION: rule boundary_ids missing {rule_id}")
            for base_id in base_ids:
                if base_id not in expected_base_ids:
                    reasons.append(
                        "CORRESPONDENCE_VIOLATION: rule base id not in owner module "
                        f"{rule_id} -> {base_id}"
                    )
            for boundary_id in boundary_ids:
                if boundary_id not in expected_boundary_ids:
                    reasons.append(
                        "CORRESPONDENCE_VIOLATION: rule boundary id not in owner module "
                        f"{rule_id} -> {boundary_id}"
                    )
            actual_rule_ids.add(rule_id)
            rule_symbol = _symbol(rule_type)
            if rule_id in rule_symbols and rule_symbols[rule_id] != rule_symbol:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: rule mapped to multiple class symbols "
                    f"{rule_id}"
                )
            rule_symbols[rule_id] = rule_symbol

        if actual_base_ids != expected_base_ids:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: base class set mismatch "
                f"for {module_id} expected={sorted(expected_base_ids)} actual={sorted(actual_base_ids)}"
            )
        if actual_rule_ids != expected_rule_ids:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: rule class set mismatch "
                f"for {module_id} expected={sorted(expected_rule_ids)} actual={sorted(actual_rule_ids)}"
            )

        config_bindings = config_binding.config_module.compiled_config_export.get("module_static_param_bindings")
        if not isinstance(config_bindings, list):
            reasons.append(f"CORRESPONDENCE_VIOLATION: missing module_static_param_bindings for {module_id}")
            config_bindings = []
        config_binding_by_boundary = {
            str(item.get("boundary_id") or ""): item
            for item in config_bindings
            if isinstance(item, Mapping)
        }
        for boundary_id in expected_boundary_ids:
            field_name = str(boundary_field_map.get(boundary_id) or "").strip()
            if not field_name:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: module boundary field missing "
                    f"{module_id}:{boundary_id}"
                )
                continue
            if field_name not in static_field_names:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: static params field missing "
                    f"{module_id}:{boundary_id}:{field_name}"
                )
            if field_name not in runtime_field_names:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: runtime params field missing "
                    f"{module_id}:{boundary_id}:{field_name}"
                )
            binding_record = config_binding_by_boundary.get(boundary_id)
            if not binding_record:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: config mapping missing "
                    f"{module_id}:{boundary_id}"
                )
                continue
            source_exact = str(binding_record.get("config_source_exact_path") or "")
            static_export_path = str(binding_record.get("exact_export_static_path") or "")
            if not source_exact or not static_export_path:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: config->code mapping incomplete "
                    f"{module_id}:{boundary_id}"
                )
            expected_suffix = f".static_params.{field_name}"
            if not static_export_path.endswith(expected_suffix):
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: static export field mismatch "
                    f"{module_id}:{boundary_id} path={static_export_path} field={field_name}"
                )

        code_bindings = code_module.code_bindings
        if isinstance(code_bindings, Mapping):
            implementation_slots = code_bindings.get("implementation_slots")
            if isinstance(implementation_slots, list):
                for slot in implementation_slots:
                    if not isinstance(slot, Mapping):
                        continue
                    source_symbol = str(slot.get("source_symbol") or "")
                    if "communication_export" in source_symbol:
                        reasons.append(
                            "CORRESPONDENCE_VIOLATION: code must not consume communication_export "
                            f"{module_id}:{source_symbol}"
                        )
                    if "framework/" in source_symbol:
                        reasons.append(
                            "CORRESPONDENCE_VIOLATION: code must not consume framework markdown "
                            f"{module_id}:{source_symbol}"
                        )

    outcome = RuleValidationOutcome(
        rule_id="CORRESPONDENCE_GUARD",
        name="mbrd correspondence guard",
        passed=not reasons,
        reasons=tuple(reasons[:_MAX_REASONS]),
        evidence={
            "module_count": len(framework_by_module),
            "config_module_count": len(config_by_module),
            "code_module_count": len(code_by_module),
            "module_class_binding_count": len(module_symbols),
            "base_class_binding_count": len(base_symbols),
            "rule_class_binding_count": len(rule_symbols),
            "reason_count": len(reasons),
        },
    )
    return RuleValidationSummary(module_id="framework.correspondence", rules=(outcome,))
