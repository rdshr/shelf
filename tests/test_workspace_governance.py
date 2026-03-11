from __future__ import annotations

from pathlib import Path
import unittest

from workspace_governance import (
    DEFAULT_WORKSPACE_GOVERNANCE_JSON,
    build_workspace_governance_payload,
    parse_workspace_governance_payload,
    resolve_workspace_change_context,
)


class WorkspaceGovernanceTest(unittest.TestCase):
    def test_build_workspace_governance_payload_contains_standards_and_project_tree(self) -> None:
        payload = build_workspace_governance_payload()
        node_ids = {item["id"] for item in payload["root"]["nodes"]}
        governance = payload["governance"]

        self.assertIn("workspace:shelf", node_ids)
        self.assertIn("workspace:shelf:standards", node_ids)
        self.assertIn("workspace:shelf:projects", node_ids)
        self.assertIn("project:knowledge_base_basic", node_ids)
        self.assertIn("project:knowledge_base_basic:structure:object:kb.answer.behavior", node_ids)
        self.assertIn("knowledge_base_basic", governance["project_trees"])
        self.assertIn("project_discovery_audit", governance)

    def test_resolve_workspace_change_context_maps_framework_change_to_project(self) -> None:
        payload = build_workspace_governance_payload()

        context = resolve_workspace_change_context(
            payload,
            {"framework/knowledge_base/L2-M0-知识库工作台场景模块.md"},
        )

        self.assertIn("projects/knowledge_base_basic/product_spec.toml", context["affected_project_spec_files"])
        self.assertIn("projects/knowledge_base_basic/product_spec.toml", context["materialize_project_spec_files"])
        self.assertTrue(context["run_standard_checks"])
        self.assertTrue(context["run_project_checks"])

    def test_parse_workspace_governance_payload_accepts_generated_file(self) -> None:
        self.assertTrue(DEFAULT_WORKSPACE_GOVERNANCE_JSON.exists())
        payload = parse_workspace_governance_payload(DEFAULT_WORKSPACE_GOVERNANCE_JSON)
        self.assertIn("root", payload)
        self.assertIn("governance", payload)

    def test_workspace_governance_artifacts_are_nodes_in_the_tree(self) -> None:
        payload = build_workspace_governance_payload()

        context = resolve_workspace_change_context(
            payload,
            {"docs/hierarchy/project_discovery_audit.json"},
        )

        self.assertIn(
            "workspace:shelf:evidence:artifact:project_discovery_audit_json",
            context["touched_nodes"],
        )
        self.assertTrue(context["affected_nodes"])


if __name__ == "__main__":
    unittest.main()
