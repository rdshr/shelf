from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from project_runtime.compiler import compile_project_runtime
from project_runtime.config_layer import build_config_modules, load_project_config
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

    def test_framework_guard_scope_is_included_and_passes_on_current_project(self) -> None:
        canonical = compile_project_runtime().canonical
        validation_reports = canonical["evidence"]["validation_reports"]
        self.assertIn("framework_guard", validation_reports)
        self.assertTrue(validation_reports["framework_guard"]["passed"])
        self.assertEqual(validation_reports["framework_guard"]["rule_count"], 1)
        self.assertIn("path_scope_guard", validation_reports)
        self.assertTrue(validation_reports["path_scope_guard"]["passed"])
        self.assertEqual(validation_reports["path_scope_guard"]["rule_count"], 1)

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
