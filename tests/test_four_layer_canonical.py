from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from project_runtime.compiler import compile_project_runtime
from project_runtime.config_layer import build_config_modules, load_project_config
from project_runtime.correspondence_validator import summarize_correspondence_guard
from project_runtime.code_layer import build_code_modules
from project_runtime.framework_violation_guard import summarize_framework_violation_guard
from project_runtime.framework_layer import resolve_selected_framework_modules
from project_runtime.path_scope_guard import summarize_path_scope_guard


class FourLayerCanonicalTest(unittest.TestCase):
    def test_framework_identities_and_source_refs_are_stable(self) -> None:
        first = compile_project_runtime().canonical
        second = compile_project_runtime().canonical
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
        first = compile_project_runtime().canonical
        second = compile_project_runtime().canonical
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
        canonical = compile_project_runtime().canonical
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
        target_module_id = "knowledge_base.L2.M0"
        framework_module = framework_modules[target_module_id]
        config_module = config_modules[target_module_id]
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

        self.assertIn("CHAT", framework_projection_by_boundary)
        self.assertEqual(
            framework_projection_by_boundary["CHAT"]["primary_exact_path"],
            compiled_projection_by_boundary["CHAT"]["primary_exact_path"],
        )
        self.assertEqual(
            framework_projection_by_boundary["SURFACE"]["primary_exact_path"],
            compiled_projection_by_boundary["SURFACE"]["primary_exact_path"],
        )
        self.assertEqual(
            config_module["compiled_config_export"]["projection_source"],
            "framework_export",
        )

    def test_base_bindings_resolve_to_owner_slots_and_symbols(self) -> None:
        canonical = compile_project_runtime().canonical
        base_bindings = [
            item
            for item in canonical["links"]["base_bindings"]
            if isinstance(item, dict) and str(item.get("module_id") or "") == "knowledge_base.L2.M0"
        ]
        self.assertTrue(base_bindings)
        for binding in base_bindings:
            self.assertTrue(binding["code_owner_id"])
            self.assertTrue(binding["code_owner_class_id"])
            self.assertTrue(binding["implementing_slot_ids"])
            self.assertTrue(binding["bound_symbols"])
            self.assertNotEqual(binding["binding_kind"], "code_module_class")

    def test_links_mark_mainline_and_trace_views(self) -> None:
        canonical = compile_project_runtime().canonical
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
        canonical = compile_project_runtime().canonical
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
        project_config = load_project_config("projects/knowledge_base_basic/project.toml")
        framework_modules, _ = resolve_selected_framework_modules(project_config.framework_modules)
        knowledge_modules = tuple(module for module in framework_modules if module.framework == "knowledge_base")
        config_bindings = build_config_modules(project_config, knowledge_modules)

        self.assertTrue(config_bindings)
        self.assertTrue(
            any(
                binding.config_module.compiled_config_export["projection_source"] == "framework_export"
                for binding in config_bindings
            )
        )

    def test_boundary_payloads_strip_projection_mirror_keys(self) -> None:
        canonical = compile_project_runtime().canonical
        config_modules = {
            str(module["module_id"]): module
            for module in canonical["config"]["modules"]
            if isinstance(module, dict)
        }
        frontend_module = config_modules["frontend.L2.M0"]
        exact_boundary = frontend_module["exact_export"]["boundaries"]["SURFACE"]
        communication_boundary = frontend_module["communication_export"]["boundaries"]["SURFACE"]
        self.assertNotIn("boundary_id", exact_boundary)
        self.assertNotIn("mapping_mode", exact_boundary)
        self.assertNotIn("boundary_id", communication_boundary)
        self.assertNotIn("mapping_mode", communication_boundary)

    def test_framework_guard_scope_is_included_and_passes_on_current_project(self) -> None:
        canonical = compile_project_runtime().canonical
        validation_reports = canonical["evidence"]["validation_reports"]
        self.assertIn("framework_guard", validation_reports)
        self.assertTrue(validation_reports["framework_guard"]["passed"])
        self.assertEqual(validation_reports["framework_guard"]["rule_count"], 1)
        self.assertIn("correspondence_guard", validation_reports)
        self.assertTrue(validation_reports["correspondence_guard"]["passed"])
        self.assertEqual(validation_reports["correspondence_guard"]["rule_count"], 1)
        self.assertIn("path_scope_guard", validation_reports)
        self.assertTrue(validation_reports["path_scope_guard"]["passed"])
        self.assertEqual(validation_reports["path_scope_guard"]["rule_count"], 1)

    def test_module_scoped_static_params_exports_and_correspondence_links(self) -> None:
        canonical = compile_project_runtime().canonical
        config_modules = {
            str(module["module_id"]): module
            for module in canonical["config"]["modules"]
            if isinstance(module, dict)
        }
        knowledge_module = config_modules["knowledge_base.L2.M0"]
        module_key = str(knowledge_module["module_key"])
        static_params = knowledge_module["exact_export"]["modules"][module_key]["static_params"]
        self.assertIn("chat", static_params)
        self.assertIn("boundaries", knowledge_module["exact_export"])
        self.assertIn("CHAT", knowledge_module["exact_export"]["boundaries"])

        links = canonical["links"]
        module_bindings = [
            item
            for item in links["module_class_bindings"]
            if isinstance(item, dict) and str(item.get("module_id")) == "knowledge_base.L2.M0"
        ]
        boundary_param_bindings = [
            item
            for item in links["boundary_param_bindings"]
            if isinstance(item, dict) and str(item.get("owner_module_id")) == "knowledge_base.L2.M0"
        ]
        self.assertTrue(module_bindings)
        self.assertTrue(boundary_param_bindings)
        self.assertTrue(
            all(
                ".modules.knowledge_base__L2__M0.static_params." in str(item["exact_export_static_path"])
                for item in boundary_param_bindings
            )
        )
        self.assertTrue(all(str(item["static_params_class_symbol"]) for item in boundary_param_bindings))
        self.assertTrue(all(str(item["runtime_params_class_symbol"]) for item in boundary_param_bindings))

    def test_correspondence_view_protocol_is_plugin_consumable(self) -> None:
        canonical = compile_project_runtime().canonical
        correspondence = canonical.get("correspondence")
        self.assertIsInstance(correspondence, dict)
        self.assertEqual(correspondence.get("correspondence_schema_version"), 1)

        objects = correspondence.get("objects")
        self.assertIsInstance(objects, list)
        self.assertTrue(objects)
        object_index = correspondence.get("object_index")
        self.assertIsInstance(object_index, dict)
        tree = correspondence.get("tree")
        self.assertIsInstance(tree, list)
        self.assertTrue(tree)

        for item in objects:
            self.assertIsInstance(item, dict)
            self.assertIn(item["object_kind"], {"module", "base", "rule", "boundary", "static_param", "runtime_param"})
            self.assertTrue(str(item.get("object_id") or ""))
            self.assertTrue(str(item.get("owner_module_id") or ""))
            self.assertTrue(str(item.get("display_name") or ""))
            self.assertIn(
                item["materialization_kind"],
                {"runtime_dynamic_type", "source_symbol", "generated_readonly"},
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
            target_kinds = {target["target_kind"] for target in targets if isinstance(target, dict)}
            self.assertIn(item["primary_nav_target_kind"], target_kinds)
            self.assertIn(item["primary_edit_target_kind"], target_kinds)

            primary_targets = [target for target in targets if isinstance(target, dict) and bool(target.get("is_primary"))]
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
                    for target in targets
                    if isinstance(target, dict)
                )
            )

            for target in targets:
                self.assertIsInstance(target, dict)
                self.assertIn(
                    target["target_kind"],
                    {
                        "framework_definition",
                        "config_source",
                        "code_correspondence",
                        "code_implementation",
                        "evidence_report",
                        "deprecated_alias",
                    },
                )
                self.assertIn(target["layer"], {"framework", "config", "code", "evidence"})
                self.assertTrue(str(target.get("file_path") or ""))
                self.assertGreaterEqual(int(target["start_line"]), 1)
                self.assertGreaterEqual(int(target["end_line"]), int(target["start_line"]))
                if target["target_kind"] == "deprecated_alias":
                    self.assertFalse(bool(target.get("is_primary")))
                    self.assertTrue(bool(target.get("is_deprecated_alias")))

            if item["materialization_kind"] == "runtime_dynamic_type":
                self.assertTrue(
                    {"framework_definition", "config_source", "code_correspondence"}.intersection(target_kinds),
                )

            anchor = item.get("correspondence_anchor")
            self.assertIsInstance(anchor, dict)
            self.assertEqual(anchor.get("target_kind"), "code_correspondence")
            implementation_anchor = item.get("implementation_anchor")
            self.assertIsInstance(implementation_anchor, dict)
            self.assertEqual(implementation_anchor.get("target_kind"), "code_implementation")

        sample_boundary = next(
            row
            for row in objects
            if isinstance(row, dict)
            and str(row.get("object_kind") or "") == "boundary"
            and str(row.get("owner_module_id") or "") == "knowledge_base.L2.M0"
        )
        boundary_targets = sample_boundary["navigation_targets"]
        self.assertTrue(
            any(
                str(target.get("target_kind") or "") == "deprecated_alias"
                and not bool(target.get("is_primary"))
                for target in boundary_targets
                if isinstance(target, dict)
            )
        )

        validation_summary = correspondence.get("validation_summary")
        self.assertIsInstance(validation_summary, dict)
        self.assertIn("issue_count_by_object", validation_summary)
        self.assertIn("issues", validation_summary)
        self.assertIn("error_count", validation_summary)
        issues = validation_summary["issues"]
        self.assertIsInstance(issues, list)
        for issue in issues:
            self.assertIsInstance(issue, dict)
            object_ids = issue.get("object_ids", [])
            self.assertIsInstance(object_ids, list)
            for object_id in object_ids:
                self.assertIn(object_id, object_index)

    def test_correspondence_guard_fails_when_rule_boundary_mapping_is_missing(self) -> None:
        project_config = load_project_config("projects/knowledge_base_basic/project.toml")
        framework_modules, root_module_ids = resolve_selected_framework_modules(project_config.framework_modules)
        config_bindings = build_config_modules(project_config, framework_modules)
        code_bindings, _ = build_code_modules(config_bindings, root_module_ids=root_module_ids)

        target = next(
            item
            for item in code_bindings
            if item.framework_module.module_id == "knowledge_base.L2.M0"
        )
        setattr(target.code_module.ModuleType, "boundary_field_map", {})

        summary = summarize_correspondence_guard(
            framework_modules=framework_modules,
            config_modules=config_bindings,
            code_modules=code_bindings,
        )
        self.assertFalse(summary.passed)
        reasons = summary.rules[0].reasons
        self.assertTrue(any("module boundary field missing" in reason for reason in reasons))

    def test_framework_guard_reports_out_of_projection_paths(self) -> None:
        project_config = load_project_config("projects/knowledge_base_basic/project.toml")
        framework_modules, _ = resolve_selected_framework_modules(project_config.framework_modules)

        exact_config = deepcopy(project_config.exact)
        communication_config = deepcopy(project_config.communication)
        frontend_exact = exact_config.setdefault("frontend", {})
        frontend_comm = communication_config.setdefault("frontend", {})
        self.assertIsInstance(frontend_exact, dict)
        self.assertIsInstance(frontend_comm, dict)
        frontend_exact["forbidden_extension"] = {"enabled": True}
        frontend_comm["non_projected_section"] = {"note": "unauthorized"}

        summary = summarize_framework_violation_guard(
            framework_modules=framework_modules,
            communication_config=communication_config,
            exact_config=exact_config,
        )

        self.assertFalse(summary.passed)
        reasons = summary.rules[0].reasons
        self.assertTrue(
            any("exact.frontend.forbidden_extension" in reason for reason in reasons)
        )
        self.assertTrue(
            any("communication.frontend.non_projected_section" in reason for reason in reasons)
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
