from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import fields
from typing import Any

from project_runtime.correspondence_contracts import (
    BaseContract,
    ModuleContract,
    RuleContract,
    RuntimeBoundaryParamsContract,
    StaticBoundaryParamsContract,
    module_key_from_id,
)
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
    module_id_by_symbol: dict[str, str] = {}
    base_id_by_symbol: dict[str, str] = {}
    rule_id_by_symbol: dict[str, str] = {}

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
        expected_module_key = module_key_from_id(module_id)
        code_module = code_binding.code_module
        module_type = getattr(code_module, "ModuleType", None)
        static_type = getattr(code_module, "StaticBoundaryParamsType", None)
        runtime_type = getattr(code_module, "RuntimeBoundaryParamsType", None)
        base_types: tuple[type[Any], ...] = getattr(code_module, "BaseTypes", tuple())
        rule_types: tuple[type[Any], ...] = getattr(code_module, "RuleTypes", tuple())

        if not isinstance(module_type, type):
            reasons.append(f"CORRESPONDENCE_VIOLATION: module class missing for {module_id}")
            continue
        if not issubclass(module_type, ModuleContract):
            reasons.append(
                "CORRESPONDENCE_VIOLATION: module class does not implement ModuleContract "
                f"for {module_id}"
            )
        if not isinstance(static_type, type):
            reasons.append(
                "CORRESPONDENCE_VIOLATION: static params class missing "
                f"for {module_id}"
            )
            continue
        if not issubclass(static_type, StaticBoundaryParamsContract):
            reasons.append(
                "CORRESPONDENCE_VIOLATION: static params class does not implement "
                f"StaticBoundaryParamsContract for {module_id}"
            )
        if not isinstance(runtime_type, type):
            reasons.append(
                "CORRESPONDENCE_VIOLATION: runtime params class missing "
                f"for {module_id}"
            )
            continue
        if not issubclass(runtime_type, RuntimeBoundaryParamsContract):
            reasons.append(
                "CORRESPONDENCE_VIOLATION: runtime params class does not implement "
                f"RuntimeBoundaryParamsContract for {module_id}"
            )

        module_symbol = _symbol(module_type)
        module_symbols[module_id] = module_symbol
        mapped_module_id = module_id_by_symbol.get(module_symbol)
        if mapped_module_id and mapped_module_id != module_id:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: duplicate module class symbol "
                f"{module_symbol} for {module_id} and {mapped_module_id}"
            )
        module_id_by_symbol[module_symbol] = module_id

        if str(getattr(module_type, "framework_module_id", "")) != module_id:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: module class framework_module_id mismatch "
                f"for {module_id}"
            )
        if str(getattr(static_type, "framework_module_id", "")) != module_id:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: static params framework_module_id mismatch "
                f"for {module_id}"
            )
        if str(getattr(runtime_type, "framework_module_id", "")) != module_id:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: runtime params framework_module_id mismatch "
                f"for {module_id}"
            )
        if getattr(module_type, "StaticBoundaryParams", None) is not static_type:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: ModuleType.StaticBoundaryParams mismatch "
                f"for {module_id}"
            )
        if getattr(module_type, "RuntimeBoundaryParams", None) is not runtime_type:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: ModuleType.RuntimeBoundaryParams mismatch "
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
        framework_rule_by_short_id = {
            str(rule.rule_id): rule
            for rule in framework_module.rule_classes
        }
        for rule in framework_module.rule_classes:
            rule_short_id = str(getattr(rule, "rule_id", "")).strip()
            outputs = _tuple_of_text(getattr(rule, "output_capabilities", tuple()))
            invalids = _tuple_of_text(getattr(rule, "invalid_conclusions", tuple()))
            if not outputs and not invalids:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: rule must declare output_capabilities or invalid_conclusions "
                    f"{module_id}.{rule_short_id}"
                )

        base_signature_to_id: dict[
            tuple[frozenset[str], frozenset[str], frozenset[str]],
            str,
        ] = {}
        for base in framework_module.base_classes:
            base_full_id = f"{module_id}.{str(base.base_id)}"
            related_rule_ids = frozenset(_tuple_of_text(getattr(base, "related_rule_ids", tuple())))
            if not related_rule_ids:
                reasons.append(
                    f"CORRESPONDENCE_VIOLATION: base is not used by any rule {base_full_id}"
                )
            boundary_ids = frozenset(_tuple_of_text(getattr(base, "boundary_bindings", tuple())))
            downstream_effects: set[str] = set()
            for rule_short_id in related_rule_ids:
                framework_rule = framework_rule_by_short_id.get(rule_short_id)
                if framework_rule is None:
                    continue
                outputs = _tuple_of_text(getattr(framework_rule, "output_capabilities", tuple()))
                invalids = _tuple_of_text(getattr(framework_rule, "invalid_conclusions", tuple()))
                downstream_effects.update(f"capability:{item}" for item in outputs)
                downstream_effects.update(f"invalid:{item}" for item in invalids)
            signature = (
                boundary_ids,
                related_rule_ids,
                frozenset(downstream_effects),
            )
            duplicated_with = base_signature_to_id.get(signature)
            if duplicated_with and duplicated_with != base_full_id:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: redundant base split detected "
                    f"{duplicated_with} <-> {base_full_id} "
                    "(same boundary set, rule participation set, downstream impact set)"
                )
            else:
                base_signature_to_id[signature] = base_full_id

        actual_base_ids: set[str] = set()
        actual_rule_ids: set[str] = set()

        if not isinstance(base_types, tuple):
            reasons.append(f"CORRESPONDENCE_VIOLATION: BaseTypes must be tuple for {module_id}")
            base_types = tuple()
        if not isinstance(rule_types, tuple):
            reasons.append(f"CORRESPONDENCE_VIOLATION: RuleTypes must be tuple for {module_id}")
            rule_types = tuple()
        if tuple(getattr(module_type, "BaseTypes", tuple())) != base_types:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: ModuleType.BaseTypes not aligned with code module "
                f"for {module_id}"
            )
        if tuple(getattr(module_type, "RuleTypes", tuple())) != rule_types:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: ModuleType.RuleTypes not aligned with code module "
                f"for {module_id}"
            )

        for base_type in base_types:
            if not isinstance(base_type, type):
                reasons.append(f"CORRESPONDENCE_VIOLATION: invalid base class in {module_id}")
                continue
            if not issubclass(base_type, BaseContract):
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: base class does not implement BaseContract "
                    f"in {module_id}"
                )
            base_id = str(getattr(base_type, "framework_base_id", "")).strip()
            owner_id = str(getattr(base_type, "owner_module_id", "")).strip()
            base_boundary_ids = _tuple_of_text(getattr(base_type, "boundary_ids", tuple()))
            if not base_id:
                reasons.append(f"CORRESPONDENCE_VIOLATION: base class missing framework_base_id in {module_id}")
                continue
            if owner_id != module_id:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: base class owner mismatch "
                    f"{base_id} owner={owner_id} expected={module_id}"
                )
            if not base_boundary_ids:
                reasons.append(f"CORRESPONDENCE_VIOLATION: base boundary_ids missing {base_id}")
            for boundary_id in base_boundary_ids:
                if boundary_id not in expected_boundary_ids:
                    reasons.append(
                        "CORRESPONDENCE_VIOLATION: base boundary id not in owner module "
                        f"{base_id} -> {boundary_id}"
                    )
            actual_base_ids.add(base_id)
            base_symbol = _symbol(base_type)
            if base_id in base_symbols and base_symbols[base_id] != base_symbol:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: base mapped to multiple class symbols "
                    f"{base_id}"
                )
            base_symbols[base_id] = base_symbol
            mapped_base_id = base_id_by_symbol.get(base_symbol)
            if mapped_base_id and mapped_base_id != base_id:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: multiple base ids share one class symbol "
                    f"{base_symbol} -> {mapped_base_id}, {base_id}"
                )
            base_id_by_symbol[base_symbol] = base_id

        for rule_type in rule_types:
            if not isinstance(rule_type, type):
                reasons.append(f"CORRESPONDENCE_VIOLATION: invalid rule class in {module_id}")
                continue
            if not issubclass(rule_type, RuleContract):
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: rule class does not implement RuleContract "
                    f"in {module_id}"
                )
            rule_id = str(getattr(rule_type, "framework_rule_id", "")).strip()
            owner_id = str(getattr(rule_type, "owner_module_id", "")).strip()
            base_ids = _tuple_of_text(getattr(rule_type, "base_ids", tuple()))
            rule_boundary_ids = _tuple_of_text(getattr(rule_type, "boundary_ids", tuple()))
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
            if not rule_boundary_ids:
                reasons.append(f"CORRESPONDENCE_VIOLATION: rule boundary_ids missing {rule_id}")
            for base_id in base_ids:
                if base_id not in expected_base_ids:
                    reasons.append(
                        "CORRESPONDENCE_VIOLATION: rule base id not in owner module "
                        f"{rule_id} -> {base_id}"
                    )
            for boundary_id in rule_boundary_ids:
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
            mapped_rule_id = rule_id_by_symbol.get(rule_symbol)
            if mapped_rule_id and mapped_rule_id != rule_id:
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: multiple rule ids share one class symbol "
                    f"{rule_symbol} -> {mapped_rule_id}, {rule_id}"
                )
            rule_id_by_symbol[rule_symbol] = rule_id

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

        exact_export = config_binding.config_module.exact_export
        if isinstance(exact_export, Mapping) and "boundaries" in exact_export:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: legacy exact_export.boundaries is not allowed "
                f"for {module_id}"
            )
        communication_export = config_binding.config_module.communication_export
        if isinstance(communication_export, Mapping) and "boundaries" in communication_export:
            reasons.append(
                "CORRESPONDENCE_VIOLATION: legacy communication_export.boundaries is not allowed "
                f"for {module_id}"
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
            expected_prefix = f"exact_export.modules.{expected_module_key}.static_params."
            if not static_export_path.startswith(expected_prefix):
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: static export path not module scoped "
                    f"{module_id}:{boundary_id} path={static_export_path}"
                )

        code_bindings = code_module.code_bindings
        if isinstance(code_bindings, Mapping):
            boundary_param_bindings = code_bindings.get("boundary_param_bindings")
            if not isinstance(boundary_param_bindings, list):
                reasons.append(
                    "CORRESPONDENCE_VIOLATION: code boundary_param_bindings missing "
                    f"for {module_id}"
                )
                boundary_param_bindings = []
            boundary_binding_by_id = {
                str(item.get("boundary_id") or ""): item
                for item in boundary_param_bindings
                if isinstance(item, Mapping)
            }
            for boundary_id in expected_boundary_ids:
                binding_item = boundary_binding_by_id.get(boundary_id)
                if not binding_item:
                    reasons.append(
                        "CORRESPONDENCE_VIOLATION: code boundary params binding missing "
                        f"{module_id}:{boundary_id}"
                    )
                    continue
                static_symbol = str(binding_item.get("static_params_class_symbol") or "")
                runtime_symbol = str(binding_item.get("runtime_params_class_symbol") or "")
                if static_symbol != _symbol(static_type):
                    reasons.append(
                        "CORRESPONDENCE_VIOLATION: static params class symbol mismatch "
                        f"{module_id}:{boundary_id}"
                    )
                if runtime_symbol != _symbol(runtime_type):
                    reasons.append(
                        "CORRESPONDENCE_VIOLATION: runtime params class symbol mismatch "
                        f"{module_id}:{boundary_id}"
                    )
            implementation_slots = code_bindings.get("implementation_slots")
            if isinstance(implementation_slots, list):
                for slot in implementation_slots:
                    if not isinstance(slot, Mapping):
                        continue
                    slot_kind = str(slot.get("slot_kind") or "")
                    source_symbol = str(slot.get("source_symbol") or "")
                    anchor_path = str(slot.get("anchor_path") or "")
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
                    if "exact_export.boundaries." in source_symbol or "exact_export.boundaries." in anchor_path:
                        reasons.append(
                            "CORRESPONDENCE_VIOLATION: legacy boundary slot reference is not allowed "
                            f"{module_id}:{source_symbol or anchor_path}"
                        )
                    projection_paths = slot.get("projection_paths")
                    if isinstance(projection_paths, list) and any(
                        "exact_export.boundaries." in str(path)
                        for path in projection_paths
                    ):
                        reasons.append(
                            "CORRESPONDENCE_VIOLATION: projection paths contain legacy boundary slot "
                            f"for {module_id}:{slot.get('slot_id')}"
                        )
                    if slot_kind == "exact_boundary":
                        reasons.append(
                            "CORRESPONDENCE_VIOLATION: exact_boundary slot kind is deprecated "
                            f"for {module_id}:{slot.get('slot_id')}"
                        )
                    if slot_kind == "module_static_param":
                        expected_prefix = f"exact_export.modules.{expected_module_key}.static_params."
                        if not anchor_path.startswith(expected_prefix):
                            reasons.append(
                                "CORRESPONDENCE_VIOLATION: module_static_param slot anchor invalid "
                                f"{module_id}:{anchor_path}"
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
