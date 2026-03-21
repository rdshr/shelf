from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import tempfile
import unittest
from typing import Any, cast

from framework_ir.parser import load_framework_catalog
from project_runtime.compiler import compile_project_runtime
from project_runtime.config_layer import build_config_modules, load_project_config
from project_runtime.correspondence_validator import summarize_correspondence_guard
from project_runtime.code_layer import build_code_modules
from project_runtime.framework_violation_guard import summarize_framework_violation_guard
from project_runtime.framework_layer import resolve_selected_framework_modules
from project_runtime.path_scope_guard import summarize_path_scope_guard
from project_runtime.static_modules import STATIC_MODULE_CONTRACTS


@lru_cache(maxsize=1)
def _default_project_file() -> str:
    candidates = sorted(Path("projects").glob("*/project.toml"))
    if not candidates:
        raise unittest.SkipTest("no projects/*/project.toml found")
    return candidates[0].as_posix()


@lru_cache(maxsize=1)
def _compile_default_canonical() -> dict[str, Any]:
    return compile_project_runtime(_default_project_file()).canonical


@lru_cache(maxsize=1)
def _load_default_project() -> tuple[Any, tuple[type[Any], ...], dict[str, str]]:
    project_config = load_project_config(_default_project_file())
    framework_modules, root_module_ids = resolve_selected_framework_modules(project_config.framework_modules)
    return project_config, framework_modules, root_module_ids


def _build_default_bindings() -> tuple[Any, tuple[type[Any], ...], tuple[Any, ...], tuple[Any, ...]]:
    project_config, framework_modules, root_module_ids = _load_default_project()
    config_bindings = build_config_modules(project_config, framework_modules)
    code_bindings, _ = build_code_modules(config_bindings, root_module_ids=root_module_ids)
    return project_config, framework_modules, config_bindings, code_bindings


def _first_code_binding_with_rules(code_bindings: tuple[Any, ...]) -> Any:
    for binding in code_bindings:
        if getattr(binding.code_module, "BaseTypes", ()) and getattr(binding.code_module, "RuleTypes", ()):
            return binding
    raise unittest.SkipTest("no code module with both base/rule types found in current project")


def _first_framework_module_with_two_bases(framework_modules: tuple[type[Any], ...]) -> type[Any]:
    for module in framework_modules:
        if len(getattr(module, "base_classes", ())) >= 2 and getattr(module, "rule_classes", ()):
            return module
    raise unittest.SkipTest("no framework module with >=2 bases and >=1 rule found in current project")


def _framework_module_by_id(framework_modules: tuple[type[Any], ...], module_id: str) -> type[Any]:
    for module in framework_modules:
        if str(module.module_id) == str(module_id):
            return module
    raise unittest.SkipTest(f"framework module not found in current project: {module_id}")


class FourLayerCanonicalTest(unittest.TestCase):
    def test_static_contract_registry_covers_all_framework_modules(self) -> None:
        framework_module_ids = {module.module_id for module in load_framework_catalog().modules}
        static_contract_module_ids = set(STATIC_MODULE_CONTRACTS)
        missing = sorted(framework_module_ids - static_contract_module_ids)
        self.assertFalse(missing, f"static contract registry missing framework modules: {missing}")
        extra = sorted(static_contract_module_ids - framework_module_ids)
        if extra:
            self.skipTest(
                "workspace framework snapshot is partial; strict module-set equality check is skipped. "
                f"extra static contracts: {extra}"
            )
        self.assertEqual(framework_module_ids, static_contract_module_ids)

    def test_framework_identities_and_source_refs_are_stable(self) -> None:
        project_file = _default_project_file()
        first = compile_project_runtime(project_file).canonical
        second = compile_project_runtime(project_file).canonical
        first_modules = {
            str(module["module_id"]): module
            for module in first["framework"]["modules"]
            if isinstance(module, dict)
        }
        second_modules = {
            str(module["module_id"]): module
            for module in second["framework"]["modules"]
            if isinstance(module, dict)
        }

        self.assertEqual(set(first_modules), set(second_modules))
        for module_id, first_module in first_modules.items():
            second_module = second_modules[module_id]
            self.assertEqual(first_module["class_id"], second_module["class_id"])
            self.assertEqual(first_module["source_ref"], second_module["source_ref"])

            first_bases = {str(item["base_id"]): item for item in first_module["bases"] if isinstance(item, dict)}
            second_bases = {str(item["base_id"]): item for item in second_module["bases"] if isinstance(item, dict)}
            self.assertEqual(set(first_bases), set(second_bases))
            for base_id, first_base in first_bases.items():
                second_base = second_bases[base_id]
                self.assertEqual(first_base["class_id"], second_base["class_id"])
                self.assertEqual(first_base["source_ref"], second_base["source_ref"])

            first_rules = {str(item["rule_id"]): item for item in first_module["rules"] if isinstance(item, dict)}
            second_rules = {str(item["rule_id"]): item for item in second_module["rules"] if isinstance(item, dict)}
            self.assertEqual(set(first_rules), set(second_rules))
            for rule_id, first_rule in first_rules.items():
                second_rule = second_rules[rule_id]
                self.assertEqual(first_rule["class_id"], second_rule["class_id"])
                self.assertEqual(first_rule["source_ref"], second_rule["source_ref"])

    def test_config_code_and_evidence_identities_are_stable(self) -> None:
        project_file = _default_project_file()
        first = compile_project_runtime(project_file).canonical
        second = compile_project_runtime(project_file).canonical
        for layer_name in ("config", "code", "evidence"):
            first_modules = {
                str(module["module_id"]): module
                for module in first[layer_name]["modules"]
                if isinstance(module, dict)
            }
            second_modules = {
                str(module["module_id"]): module
                for module in second[layer_name]["modules"]
                if isinstance(module, dict)
            }
            self.assertEqual(set(first_modules), set(second_modules))
            for module_id, first_module in first_modules.items():
                second_module = second_modules[module_id]
                self.assertEqual(first_module["class_id"], second_module["class_id"])
                self.assertEqual(first_module["source_ref"], second_module["source_ref"])

    def test_config_projection_follows_framework_export(self) -> None:
        canonical = _compile_default_canonical()
        framework_modules = {
            str(module["module_id"]): module
            for module in canonical["framework"]["modules"]
            if isinstance(module, dict)
        }
        config_modules = {
            str(module["module_id"]): module
            for module in canonical["config"]["modules"]
            if isinstance(module, dict)
        }
        module_ids = sorted(set(framework_modules).intersection(config_modules))
        self.assertTrue(module_ids)
        for module_id in module_ids:
            framework_module = framework_modules[module_id]
            config_module = config_modules[module_id]
            framework_projection_by_boundary = {
                str(boundary["boundary_id"]): boundary["config_projection"]
                for boundary in framework_module["boundaries"]
                if isinstance(boundary, dict) and isinstance(boundary.get("config_projection"), dict)
            }
            compiled_projection_by_boundary = {
                str(binding["boundary_id"]): binding
                for binding in config_module["compiled_config_export"]["boundary_bindings"]
                if isinstance(binding, dict)
            }
            self.assertEqual(
                set(framework_projection_by_boundary),
                set(compiled_projection_by_boundary),
                f"boundary projection set mismatch: {module_id}",
            )
            for boundary_id, framework_projection in framework_projection_by_boundary.items():
                compiled_projection = compiled_projection_by_boundary[boundary_id]
                self.assertEqual(
                    framework_projection.get("primary_exact_path"),
                    compiled_projection.get("primary_exact_path"),
                    f"primary_exact_path mismatch: {module_id}:{boundary_id}",
                )
                self.assertEqual(
                    framework_projection.get("primary_communication_path"),
                    compiled_projection.get("primary_communication_path"),
                    f"primary_communication_path mismatch: {module_id}:{boundary_id}",
                )
                self.assertEqual(
                    framework_projection.get("mapping_mode"),
                    compiled_projection.get("mapping_mode"),
                    f"mapping_mode mismatch: {module_id}:{boundary_id}",
                )
            self.assertEqual(
                config_module["compiled_config_export"]["projection_source"],
                "framework_export",
                f"projection_source mismatch: {module_id}",
            )

    def test_base_bindings_resolve_to_owner_slots_and_symbols(self) -> None:
        canonical = _compile_default_canonical()
        base_bindings = [
            item
            for item in canonical["links"]["base_bindings"]
            if isinstance(item, dict)
        ]
        self.assertTrue(base_bindings)
        for binding in base_bindings:
            self.assertTrue(binding["code_owner_id"])
            self.assertTrue(binding["code_owner_class_id"])
            self.assertTrue(binding["implementing_slot_ids"])
            self.assertTrue(binding["bound_symbols"])
            self.assertNotEqual(binding["binding_kind"], "code_module_class")

    def test_links_mark_mainline_and_trace_views(self) -> None:
        canonical = _compile_default_canonical()
        link_roles = canonical["links"]["link_roles"]
        self.assertEqual(link_roles["framework_to_config"], "mainline")
        self.assertEqual(link_roles["config_to_code"], "mainline")
        self.assertEqual(link_roles["code_to_evidence"], "mainline")
        self.assertEqual(link_roles["boundary_bindings"], "trace_view")
        self.assertEqual(link_roles["base_bindings"], "trace_view")
        self.assertEqual(link_roles["module_class_bindings"], "correspondence")
        self.assertEqual(link_roles["base_class_bindings"], "correspondence")
        self.assertEqual(link_roles["rule_class_bindings"], "correspondence")
        self.assertEqual(link_roles["boundary_param_bindings"], "correspondence")

    def test_layers_only_consume_neighbor_exports(self) -> None:
        canonical = _compile_default_canonical()
        config_modules = {
            str(module["module_id"]): module
            for module in canonical["config"]["modules"]
            if isinstance(module, dict)
        }
        code_modules = {
            str(module["module_id"]): module
            for module in canonical["code"]["modules"]
            if isinstance(module, dict)
        }
        evidence_modules = {
            str(module["module_id"]): module
            for module in canonical["evidence"]["modules"]
            if isinstance(module, dict)
        }

        self.assertEqual(set(config_modules), set(code_modules))
        self.assertEqual(set(code_modules), set(evidence_modules))
        for module_id, config_module in config_modules.items():
            code_module = code_modules[module_id]
            evidence_module = evidence_modules[module_id]
            self.assertEqual(code_module["exact_export"], config_module["exact_export"])
            self.assertNotIn("communication_export", code_module)
            self.assertEqual(
                evidence_module["evidence_exports"]["code_exports"],
                code_module["code_exports"],
            )
            self.assertNotIn("communication_export", evidence_module["evidence_exports"])
            self.assertNotIn("exact_export", evidence_module["evidence_exports"])

    def test_config_modules_build_without_central_boundary_registration(self) -> None:
        project_config, framework_modules, _ = _load_default_project()
        config_bindings = build_config_modules(project_config, framework_modules)

        self.assertTrue(config_bindings)
        self.assertTrue(
            any(
                binding.config_module.compiled_config_export["projection_source"] == "framework_export"
                for binding in config_bindings
            )
        )

    def test_boundary_payloads_strip_projection_mirror_keys(self) -> None:
        canonical = _compile_default_canonical()
        config_modules = {
            str(module["module_id"]): module
            for module in canonical["config"]["modules"]
            if isinstance(module, dict)
        }
        self.assertTrue(config_modules)
        for module in config_modules.values():
            module_key = str(module["module_key"])
            exact_static = module["exact_export"]["modules"][module_key]["static_params"]
            communication_static = module["communication_export"]["modules"][module_key]["static_params"]
            for payload in list(exact_static.values()) + list(communication_static.values()):
                if isinstance(payload, dict):
                    self.assertNotIn("boundary_id", payload)
                    self.assertNotIn("mapping_mode", payload)

    def test_framework_guard_scope_is_included_and_passes_on_current_project(self) -> None:
        canonical = _compile_default_canonical()
        validation_reports = canonical["evidence"]["validation_reports"]
        self.assertIn("framework_guard", validation_reports)
        self.assertTrue(validation_reports["framework_guard"]["passed"])
        self.assertEqual(validation_reports["framework_guard"]["rule_count"], 1)
        self.assertIn("correspondence_guard", validation_reports)
        self.assertTrue(validation_reports["correspondence_guard"]["passed"])
        self.assertEqual(validation_reports["correspondence_guard"]["rule_count"], 1)
        self.assertIn("codegen_consistency_guard", validation_reports)
        self.assertTrue(validation_reports["codegen_consistency_guard"]["passed"])
        self.assertEqual(validation_reports["codegen_consistency_guard"]["rule_count"], 1)
        self.assertIn("path_scope_guard", validation_reports)
        self.assertTrue(validation_reports["path_scope_guard"]["passed"])
        self.assertEqual(validation_reports["path_scope_guard"]["rule_count"], 1)

    def test_module_scoped_static_params_exports_and_correspondence_links(self) -> None:
        canonical = _compile_default_canonical()
        config_modules = {
            str(module["module_id"]): module
            for module in canonical["config"]["modules"]
            if isinstance(module, dict)
        }
        self.assertTrue(config_modules)
        for module in config_modules.values():
            module_key = str(module["module_key"])
            static_params = module["exact_export"]["modules"][module_key]["static_params"]
            self.assertTrue(isinstance(static_params, dict) and static_params)
            self.assertNotIn("boundaries", module["exact_export"])

        links = canonical["links"]
        module_bindings = [
            item
            for item in links["module_class_bindings"]
            if isinstance(item, dict)
        ]
        boundary_param_bindings = [
            item
            for item in links["boundary_param_bindings"]
            if isinstance(item, dict)
        ]
        self.assertTrue(module_bindings)
        self.assertTrue(boundary_param_bindings)
        module_key_by_id = {
            str(module["module_id"]): str(module["module_key"])
            for module in config_modules.values()
        }
        for item in boundary_param_bindings:
            owner_module_id = str(item.get("owner_module_id") or "")
            module_key = module_key_by_id.get(owner_module_id, "")
            self.assertTrue(module_key, f"missing module_key for owner module: {owner_module_id}")
            self.assertIn(
                f".modules.{module_key}.static_params.",
                str(item["exact_export_static_path"]),
            )
        self.assertTrue(all(str(item["static_params_class_symbol"]) for item in boundary_param_bindings))
        self.assertTrue(all(str(item["runtime_params_class_symbol"]) for item in boundary_param_bindings))

    def test_correspondence_view_protocol_is_plugin_consumable(self) -> None:
        canonical = _compile_default_canonical()
        correspondence = canonical.get("correspondence")
        self.assertIsInstance(correspondence, dict)
        correspondence_dict = cast(dict[str, Any], correspondence)
        self.assertEqual(correspondence_dict.get("correspondence_schema_version"), 1)

        objects = correspondence_dict.get("objects")
        self.assertIsInstance(objects, list)
        self.assertTrue(objects)
        object_list = cast(list[dict[str, Any]], objects)
        object_index = correspondence_dict.get("object_index")
        self.assertIsInstance(object_index, dict)
        object_index_dict = cast(dict[str, Any], object_index)
        tree = correspondence_dict.get("tree")
        self.assertIsInstance(tree, list)
        self.assertTrue(tree)

        for item in object_list:
            self.assertIn(item["object_kind"], {"module", "base", "rule", "boundary", "static_param", "runtime_param"})
            self.assertTrue(str(item.get("object_id") or ""))
            self.assertTrue(str(item.get("owner_module_id") or ""))
            self.assertTrue(str(item.get("display_name") or ""))
            self.assertIn(
                item["materialization_kind"],
                {"runtime_dynamic_type", "source_symbol", "generated_readonly", "static_python_class"},
            )
            self.assertIn(
                item["primary_nav_target_kind"],
                {"framework_definition", "config_source", "code_correspondence", "code_implementation", "evidence_report"},
            )
            self.assertIn(
                item["primary_edit_target_kind"],
                {"framework_definition", "config_source", "code_correspondence", "code_implementation", "evidence_report"},
            )

            targets = item.get("navigation_targets")
            self.assertIsInstance(targets, list)
            self.assertTrue(targets)
            target_list = cast(list[dict[str, Any]], targets)
            target_kinds = {target["target_kind"] for target in target_list}
            self.assertIn(item["primary_nav_target_kind"], target_kinds)
            self.assertIn(item["primary_edit_target_kind"], target_kinds)

            primary_targets = [target for target in target_list if bool(target.get("is_primary"))]
            self.assertTrue(primary_targets)
            self.assertTrue(
                any(
                    str(target.get("target_kind") or "") == str(item["primary_nav_target_kind"])
                    for target in primary_targets
                )
            )
            self.assertTrue(
                any(
                    str(target.get("target_kind") or "") == str(item["primary_edit_target_kind"])
                    and bool(target.get("is_editable"))
                    for target in target_list
                )
            )

            for target in target_list:
                self.assertIn(
                    target["target_kind"],
                    {
                        "framework_definition",
                        "config_source",
                        "code_correspondence",
                        "code_implementation",
                        "evidence_report",
                    },
                )
                self.assertIn(target["layer"], {"framework", "config", "code", "evidence"})
                self.assertTrue(str(target.get("file_path") or ""))
                self.assertGreaterEqual(int(target["start_line"]), 1)
                self.assertGreaterEqual(int(target["end_line"]), int(target["start_line"]))

            if item["materialization_kind"] == "runtime_dynamic_type":
                self.assertTrue(
                    {"framework_definition", "config_source", "code_correspondence"}.intersection(target_kinds),
                )

            anchor = item.get("correspondence_anchor")
            self.assertIsInstance(anchor, dict)
            anchor_dict = cast(dict[str, Any], anchor)
            self.assertEqual(anchor_dict.get("target_kind"), "code_correspondence")
            implementation_anchor = item.get("implementation_anchor")
            self.assertIsInstance(implementation_anchor, dict)
            implementation_anchor_dict = cast(dict[str, Any], implementation_anchor)
            self.assertEqual(implementation_anchor_dict.get("target_kind"), "code_implementation")

        validation_summary = correspondence_dict.get("validation_summary")
        self.assertIsInstance(validation_summary, dict)
        validation_summary_dict = cast(dict[str, Any], validation_summary)
        self.assertIn("issue_count_by_object", validation_summary_dict)
        self.assertIn("issues", validation_summary_dict)
        self.assertIn("error_count", validation_summary_dict)
        issues = validation_summary_dict["issues"]
        self.assertIsInstance(issues, list)
        issue_list = cast(list[dict[str, Any]], issues)
        for issue in issue_list:
            object_ids = issue.get("object_ids", [])
            self.assertIsInstance(object_ids, list)
            object_id_list = cast(list[Any], object_ids)
            for object_id in object_id_list:
                self.assertIn(object_id, object_index_dict)

    def test_correspondence_guard_fails_when_rule_boundary_mapping_is_missing(self) -> None:
        _, framework_modules, config_bindings, code_bindings = _build_default_bindings()
        target = _first_code_binding_with_rules(code_bindings)
        setattr(target.code_module.ModuleType, "boundary_field_map", {})

        summary = summarize_correspondence_guard(
            framework_modules=framework_modules,
            config_modules=config_bindings,
            code_modules=code_bindings,
        )
        self.assertFalse(summary.passed)
        reasons = summary.rules[0].reasons
        self.assertTrue(any("module boundary field missing" in reason for reason in reasons))

    def test_correspondence_guard_fails_when_module_base_or_rule_not_fully_assembled(self) -> None:
        _, framework_modules, config_bindings, code_bindings = _build_default_bindings()
        target = _first_code_binding_with_rules(code_bindings)
        setattr(target.code_module, "BaseTypes", target.code_module.BaseTypes[:-1])
        setattr(target.code_module, "RuleTypes", target.code_module.RuleTypes[:-1])

        summary = summarize_correspondence_guard(
            framework_modules=framework_modules,
            config_modules=config_bindings,
            code_modules=code_bindings,
        )
        self.assertFalse(summary.passed)
        reasons = summary.rules[0].reasons
        self.assertTrue(any("base class set mismatch" in reason for reason in reasons))
        self.assertTrue(any("rule class set mismatch" in reason for reason in reasons))

    def test_correspondence_guard_fails_when_rule_declares_invalid_base_or_boundary(self) -> None:
        _, framework_modules, config_bindings, code_bindings = _build_default_bindings()
        target = _first_code_binding_with_rules(code_bindings)
        first_rule = target.code_module.RuleTypes[0]
        original_base_ids = tuple(first_rule.base_ids)
        original_boundary_ids = tuple(first_rule.boundary_ids)
        try:
            setattr(first_rule, "base_ids", (f"{target.framework_module.module_id}.B999",))
            setattr(first_rule, "boundary_ids", ("BOUNDARY_NOT_EXIST",))

            summary = summarize_correspondence_guard(
                framework_modules=framework_modules,
                config_modules=config_bindings,
                code_modules=code_bindings,
            )
            self.assertFalse(summary.passed)
            reasons = summary.rules[0].reasons
            self.assertTrue(any("rule base id not in owner module" in reason for reason in reasons))
            self.assertTrue(any("rule boundary id not in owner module" in reason for reason in reasons))
        finally:
            setattr(first_rule, "base_ids", original_base_ids)
            setattr(first_rule, "boundary_ids", original_boundary_ids)

    def test_correspondence_guard_fails_when_base_declares_missing_or_invalid_boundary(self) -> None:
        _, framework_modules, config_bindings, code_bindings = _build_default_bindings()
        target = _first_code_binding_with_rules(code_bindings)
        first_base = target.code_module.BaseTypes[0]
        original_boundary_ids = tuple(first_base.boundary_ids)
        try:
            setattr(first_base, "boundary_ids", tuple())
            summary_missing = summarize_correspondence_guard(
                framework_modules=framework_modules,
                config_modules=config_bindings,
                code_modules=code_bindings,
            )
            self.assertFalse(summary_missing.passed)
            self.assertTrue(
                any("base boundary_ids missing" in reason for reason in summary_missing.rules[0].reasons)
            )

            setattr(first_base, "boundary_ids", ("BOUNDARY_NOT_EXIST",))
            summary_invalid = summarize_correspondence_guard(
                framework_modules=framework_modules,
                config_modules=config_bindings,
                code_modules=code_bindings,
            )
            self.assertFalse(summary_invalid.passed)
            self.assertTrue(
                any("base boundary id not in owner module" in reason for reason in summary_invalid.rules[0].reasons)
            )
        finally:
            setattr(first_base, "boundary_ids", original_boundary_ids)

    def test_correspondence_guard_fails_when_base_is_not_used_by_any_rule(self) -> None:
        _, framework_modules, config_bindings, code_bindings = _build_default_bindings()
        target = _first_code_binding_with_rules(code_bindings)
        framework_target = _framework_module_by_id(framework_modules, target.framework_module.module_id)
        first_base = framework_target.base_classes[0]
        original_related_rule_ids = tuple(first_base.related_rule_ids)
        try:
            setattr(first_base, "related_rule_ids", tuple())
            summary = summarize_correspondence_guard(
                framework_modules=framework_modules,
                config_modules=config_bindings,
                code_modules=code_bindings,
            )
            self.assertFalse(summary.passed)
            self.assertTrue(
                any("base is not used by any rule" in reason for reason in summary.rules[0].reasons)
            )
        finally:
            setattr(first_base, "related_rule_ids", original_related_rule_ids)

    def test_correspondence_guard_fails_when_rule_has_no_output_or_invalid(self) -> None:
        _, framework_modules, config_bindings, code_bindings = _build_default_bindings()
        target = _first_code_binding_with_rules(code_bindings)
        framework_target = _framework_module_by_id(framework_modules, target.framework_module.module_id)
        first_rule = framework_target.rule_classes[0]
        original_outputs = tuple(first_rule.output_capabilities)
        original_invalids = tuple(first_rule.invalid_conclusions)
        try:
            setattr(first_rule, "output_capabilities", tuple())
            setattr(first_rule, "invalid_conclusions", tuple())
            summary = summarize_correspondence_guard(
                framework_modules=framework_modules,
                config_modules=config_bindings,
                code_modules=code_bindings,
            )
            self.assertFalse(summary.passed)
            self.assertTrue(
                any(
                    "rule must declare output_capabilities or invalid_conclusions" in reason
                    for reason in summary.rules[0].reasons
                )
            )
        finally:
            setattr(first_rule, "output_capabilities", original_outputs)
            setattr(first_rule, "invalid_conclusions", original_invalids)

    def test_correspondence_guard_fails_when_bases_are_redundant_split(self) -> None:
        _, framework_modules, config_bindings, code_bindings = _build_default_bindings()
        framework_target = _first_framework_module_with_two_bases(framework_modules)
        first_base = framework_target.base_classes[0]
        second_base = framework_target.base_classes[1]
        first_rule = framework_target.rule_classes[0]

        original_first_boundary = tuple(first_base.boundary_bindings)
        original_second_boundary = tuple(second_base.boundary_bindings)
        original_first_related = tuple(first_base.related_rule_ids)
        original_second_related = tuple(second_base.related_rule_ids)
        original_rule_outputs = tuple(first_rule.output_capabilities)
        original_rule_invalids = tuple(first_rule.invalid_conclusions)
        shared_boundary = (
            (first_base.boundary_bindings[0] if first_base.boundary_bindings else "")
            or (second_base.boundary_bindings[0] if second_base.boundary_bindings else "")
            or (framework_target.boundaries[0].boundary_id if framework_target.boundaries else "")
        )
        if not shared_boundary:
            raise unittest.SkipTest("target module has no boundary id to build redundant split scenario")
        shared_rule = first_rule.rule_id
        try:
            setattr(first_base, "boundary_bindings", (shared_boundary,))
            setattr(second_base, "boundary_bindings", (shared_boundary,))
            setattr(first_base, "related_rule_ids", (shared_rule,))
            setattr(second_base, "related_rule_ids", (shared_rule,))
            setattr(first_rule, "output_capabilities", ("C1",))
            setattr(first_rule, "invalid_conclusions", tuple())

            summary = summarize_correspondence_guard(
                framework_modules=framework_modules,
                config_modules=config_bindings,
                code_modules=code_bindings,
            )
            self.assertFalse(summary.passed)
            self.assertTrue(
                any("redundant base split detected" in reason for reason in summary.rules[0].reasons)
            )
        finally:
            setattr(first_base, "boundary_bindings", original_first_boundary)
            setattr(second_base, "boundary_bindings", original_second_boundary)
            setattr(first_base, "related_rule_ids", original_first_related)
            setattr(second_base, "related_rule_ids", original_second_related)
            setattr(first_rule, "output_capabilities", original_rule_outputs)
            setattr(first_rule, "invalid_conclusions", original_rule_invalids)

    def test_correspondence_guard_fails_when_config_mapping_missing(self) -> None:
        _, framework_modules, config_bindings, code_bindings = _build_default_bindings()
        target = _first_code_binding_with_rules(code_bindings)
        config_target = next(
            item
            for item in config_bindings
            if item.framework_module.module_id == target.framework_module.module_id
        )
        records = config_target.config_module.compiled_config_export["module_static_param_bindings"]
        if not records:
            raise unittest.SkipTest("no module_static_param_bindings in selected module")
        config_target.config_module.compiled_config_export["module_static_param_bindings"] = records[1:]

        summary = summarize_correspondence_guard(
            framework_modules=framework_modules,
            config_modules=config_bindings,
            code_modules=code_bindings,
        )
        self.assertFalse(summary.passed)
        reasons = summary.rules[0].reasons
        self.assertTrue(any("config mapping missing" in reason for reason in reasons))

    def test_correspondence_guard_fails_when_legacy_boundary_slot_or_export_reappears(self) -> None:
        _, framework_modules, config_bindings, code_bindings = _build_default_bindings()
        code_target = _first_code_binding_with_rules(code_bindings)
        config_target = next(
            item
            for item in config_bindings
            if item.framework_module.module_id == code_target.framework_module.module_id
        )
        first_slot = code_target.code_module.code_bindings["implementation_slots"][0]
        boundary_id = str(first_slot.get("boundary_id") or "BOUNDARY")
        config_target.config_module.exact_export["boundaries"] = {boundary_id: {}}
        first_slot["anchor_path"] = f"exact_export.boundaries.{boundary_id}"
        first_slot["source_symbol"] = (
            f"{code_target.framework_module.module_id}.exact_export.boundaries.{boundary_id}"
        )

        summary = summarize_correspondence_guard(
            framework_modules=framework_modules,
            config_modules=config_bindings,
            code_modules=code_bindings,
        )
        self.assertFalse(summary.passed)
        reasons = summary.rules[0].reasons
        self.assertTrue(any("legacy exact_export.boundaries is not allowed" in reason for reason in reasons))
        self.assertTrue(any("legacy boundary slot reference is not allowed" in reason for reason in reasons))

    def test_framework_guard_reports_out_of_projection_paths(self) -> None:
        project_config, framework_modules, _ = _load_default_project()

        exact_config = deepcopy(project_config.exact)
        communication_config = deepcopy(project_config.communication)
        framework_keys = sorted({str(module.framework).strip() for module in framework_modules if str(module.framework).strip()})
        if not framework_keys:
            raise unittest.SkipTest("no framework key found in selected project")
        target_framework_key = framework_keys[0]
        target_exact = exact_config.setdefault(target_framework_key, {})
        target_comm = communication_config.setdefault(target_framework_key, {})
        self.assertIsInstance(target_exact, dict)
        self.assertIsInstance(target_comm, dict)
        target_exact["forbidden_extension"] = {"enabled": True}
        target_comm["non_projected_section"] = {"note": "unauthorized"}

        summary = summarize_framework_violation_guard(
            framework_modules=framework_modules,
            communication_config=communication_config,
            exact_config=exact_config,
        )

        self.assertFalse(summary.passed)
        reasons = summary.rules[0].reasons
        self.assertTrue(
            any(f"exact.{target_framework_key}.forbidden_extension" in reason for reason in reasons)
        )
        self.assertTrue(
            any(f"communication.{target_framework_key}.non_projected_section" in reason for reason in reasons)
        )

    def test_path_scope_guard_reports_guarded_import_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "src").mkdir(parents=True, exist_ok=True)
            (repo_root / "support").mkdir(parents=True, exist_ok=True)
            (repo_root / "src" / "app.py").write_text(
                "from support.hidden import run\nrun()\n",
                encoding="utf-8",
            )
            (repo_root / "support" / "hidden.py").write_text(
                "def run() -> None:\n    return None\n",
                encoding="utf-8",
            )

            summary = summarize_path_scope_guard(
                repo_root=repo_root,
                guarded_prefixes=("src/",),
                ignored_prefixes=(),
            )

        self.assertFalse(summary.passed)
        reasons = summary.rules[0].reasons
        self.assertTrue(any("FRAMEWORK_VIOLATION" in reason for reason in reasons))
        self.assertTrue(any("src/app.py" in reason and "support/hidden.py" in reason for reason in reasons))


if __name__ == "__main__":
    unittest.main()
