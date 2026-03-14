from __future__ import annotations

import unittest

from framework_ir import load_framework_registry, parse_framework_module
from project_runtime.knowledge_base import materialize_knowledge_base_project


class FrameworkIrTest(unittest.TestCase):
    def test_parse_framework_module_extracts_structured_sections(self) -> None:
        module = parse_framework_module("framework/knowledge_base/L2-M0-知识库工作台场景模块.md")
        self.assertEqual(module.module_id, "knowledge_base.L2.M0")
        self.assertGreaterEqual(len(module.capabilities), 3)
        self.assertGreaterEqual(len(module.non_responsibilities), 1)
        self.assertEqual(module.boundaries[0].boundary_id, "SURFACE")
        self.assertEqual(module.bases[0].base_id, "B1")
        self.assertEqual(module.rules[0].rule_id, "R1")
        self.assertEqual(module.verifications[0].verification_id, "V1")

    def test_registry_contains_frontend_and_domain_modules(self) -> None:
        registry = load_framework_registry()
        frontend = registry.get_module("frontend", 2, 0)
        knowledge_base = registry.get_module("knowledge_base", 2, 0)
        self.assertEqual(frontend.title_en, "FrontendFrameworkStandard")
        self.assertEqual(knowledge_base.title_en, "KnowledgeBaseWorkbenchScenarios")

    def test_materialized_project_contains_generated_ir_and_closure(self) -> None:
        project = materialize_knowledge_base_project()
        self.assertGreaterEqual(len(project.resolved_modules), 6)
        self.assertIsNotNone(project.generated_artifacts)
        assert project.generated_artifacts is not None
        self.assertTrue(project.generated_artifacts.framework_ir_json.endswith("framework_ir.json"))
        self.assertTrue(project.generated_artifacts.product_spec_json.endswith("product_spec.json"))
        self.assertTrue(project.generated_artifacts.implementation_bundle_py.endswith("implementation_bundle.py"))
        self.assertTrue(project.generated_artifacts.generation_manifest_json.endswith("generation_manifest.json"))
        self.assertTrue(project.generated_artifacts.governance_manifest_json.endswith("governance_manifest.json"))
        self.assertTrue(project.generated_artifacts.governance_tree_json.endswith("governance_tree.json"))


if __name__ == "__main__":
    unittest.main()
