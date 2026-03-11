from __future__ import annotations

import unittest

from project_runtime import (
    build_object_coverage_report,
    build_project_discovery_audit,
    build_strict_zone_report,
    discover_framework_driven_projects,
)
from project_runtime.governance import build_governance_closure
from project_runtime.knowledge_base import (
    DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
    load_knowledge_base_project,
)


class ProjectGovernanceTest(unittest.TestCase):
    def test_discover_framework_driven_projects_reports_registered_projects(self) -> None:
        discovered = discover_framework_driven_projects()
        project_ids = {item.project_id for item in discovered}

        self.assertIn("knowledge_base_basic", project_ids)
        knowledge_base = next(item for item in discovered if item.project_id == "knowledge_base_basic")
        self.assertEqual(knowledge_base.template_id, "knowledge_base_workbench")
        self.assertTrue(knowledge_base.discovery_reasons)
        self.assertIn("framework/knowledge_base/L2-M0-知识库工作台场景模块.md", knowledge_base.framework_refs)
        self.assertIn("governance_tree.json", knowledge_base.artifact_contract)

    def test_build_governance_closure_derives_object_first_strict_zone(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        closure = build_governance_closure(project)
        object_ids = {item.object_id for item in closure.structural_objects}
        strict_zone_files = {item.file for item in closure.strict_zone}
        classifications = {item.classification for item in closure.candidates}

        self.assertIn("kb.runtime.page_routes", object_ids)
        self.assertIn("kb.api.chat_contract", object_ids)
        self.assertIn("knowledge_base_basic.config_effect.backend.transport", object_ids)
        self.assertIn("src/knowledge_base_runtime/app.py", strict_zone_files)
        self.assertIn("src/knowledge_base_runtime/backend.py", strict_zone_files)
        self.assertIn("src/project_runtime/knowledge_base.py", strict_zone_files)
        self.assertIn("src/project_runtime/governance.py", strict_zone_files)
        self.assertIn("governed", classifications)
        self.assertTrue(all(item.status == "satisfied" for item in closure.role_bindings))
        self.assertTrue(all(item.classification in {"governed", "attached", "internal"} for item in closure.candidates))
        self.assertTrue(all(item.minimality_status in {"required", "uncertain", "redundant"} for item in closure.strict_zone))
        self.assertTrue(all(item.why_required for item in closure.strict_zone if item.minimality_status == "required"))

    def test_project_discovery_audit_is_explicit(self) -> None:
        audit = build_project_discovery_audit()
        entries = audit["entries"]
        self.assertEqual(audit["summary"]["recognized_count"], 1)
        self.assertEqual(entries[0]["project_id"], "knowledge_base_basic")
        self.assertEqual(entries[0]["classification"], "recognized")

    def test_strict_zone_and_object_coverage_reports_are_machine_readable(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        closure = build_governance_closure(project)
        strict_zone_report = build_strict_zone_report(closure)
        object_coverage_report = build_object_coverage_report(closure)
        self.assertEqual(strict_zone_report["summary"]["redundant_count"], 0)
        self.assertGreater(strict_zone_report["summary"]["required_count"], 0)
        self.assertEqual(object_coverage_report["summary"]["governed_object_count"], len(closure.structural_objects))
        self.assertGreater(object_coverage_report["summary"]["attached_candidate_count"], 0)
        self.assertTrue(
            any(
                entry["object_id"] == "kb.api.chat_contract" and entry["compare_status"] == "match"
                for entry in object_coverage_report["objects"]
            )
        )


if __name__ == "__main__":
    unittest.main()
