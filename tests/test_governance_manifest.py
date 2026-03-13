from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from project_runtime.governance import (
    GovernedBinding,
    build_governance_manifest,
    build_governance_tree,
    collect_governed_bindings,
    compare_project_to_manifest,
    compare_project_to_tree,
    governed_files_for_project,
    parse_governance_manifest,
    parse_governance_tree,
)
from project_runtime.knowledge_base import (
    DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
    load_knowledge_base_project,
    materialize_knowledge_base_project,
)
from scripts import validate_strict_mapping


def _copy_sample_project_config(project_dir: Path) -> tuple[Path, Path]:
    source_product_spec = Path("projects/knowledge_base_basic/product_spec.toml")
    source_product_spec_dir = Path("projects/knowledge_base_basic/product_spec")
    source_implementation_config = Path("projects/knowledge_base_basic/implementation_config.toml")
    product_spec_file = project_dir / "product_spec.toml"
    implementation_config_file = project_dir / "implementation_config.toml"
    shutil.copy2(source_product_spec, product_spec_file)
    shutil.copy2(source_implementation_config, implementation_config_file)
    shutil.copytree(source_product_spec_dir, project_dir / "product_spec")
    return product_spec_file, project_dir / "product_spec" / "route.toml"


class GovernanceManifestTest(unittest.TestCase):
    def test_materialize_writes_governance_manifest_with_expected_structural_objects(self) -> None:
        project = materialize_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        assert project.generated_artifacts is not None
        manifest_path = Path(project.generated_artifacts.governance_manifest_json)

        payload = parse_governance_manifest(manifest_path)
        object_ids = {item["object_id"] for item in payload["structural_objects"]}
        candidate_ids = {item["candidate_id"] for item in payload["candidates"]}
        strict_zone_files = {item["file"] for item in payload["strict_zone"]}

        self.assertEqual(payload["project_id"], "knowledge_base_basic")
        self.assertIn("kb.runtime.page_routes", object_ids)
        self.assertIn("kb.frontend.surface_contract", object_ids)
        self.assertIn("kb.workbench.surface_contract", object_ids)
        self.assertIn("kb.ui.surface_spec", object_ids)
        self.assertIn("kb.backend.surface_spec", object_ids)
        self.assertIn("kb.api.library_contracts", object_ids)
        self.assertIn("kb.api.chat_contract", object_ids)
        self.assertIn("kb.answer.behavior", object_ids)
        self.assertIn("knowledge_base_basic.config_effect.backend.transport", object_ids)
        self.assertTrue(any(candidate_id.endswith("function:build_knowledge_base_router") for candidate_id in candidate_ids))
        self.assertIn("src/knowledge_base_runtime/backend.py", strict_zone_files)

    def test_materialize_writes_governance_tree_with_expected_roots_and_structural_objects(self) -> None:
        project = materialize_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        assert project.generated_artifacts is not None
        tree_path = Path(project.generated_artifacts.governance_tree_json)

        payload = parse_governance_tree(tree_path)
        node_ids = {item["node_id"] for item in payload["nodes"]}
        object_ids = {
            item["object_id"]
            for item in payload["nodes"]
            if item.get("kind") == "structural_object"
        }
        candidate_node_ids = {
            item["candidate_id"]
            for item in payload["nodes"]
            if item.get("kind") == "structural_candidate"
        }

        self.assertEqual(payload["project_id"], "knowledge_base_basic")
        self.assertEqual(payload["root_node_id"], "project:knowledge_base_basic")
        self.assertIn("project:knowledge_base_basic:framework", node_ids)
        self.assertIn("project:knowledge_base_basic:product_spec", node_ids)
        self.assertIn("project:knowledge_base_basic:implementation_config", node_ids)
        self.assertIn("project:knowledge_base_basic:structure", node_ids)
        self.assertIn("project:knowledge_base_basic:code", node_ids)
        self.assertIn("project:knowledge_base_basic:evidence", node_ids)
        self.assertIn("kb.runtime.page_routes", object_ids)
        self.assertIn("kb.frontend.surface_contract", object_ids)
        self.assertIn("kb.answer.behavior", object_ids)
        self.assertTrue(any(candidate_id.endswith("function:build_frontend_contract") for candidate_id in candidate_node_ids))

    def test_temp_output_materialization_stays_byte_stable(self) -> None:
        materialize_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        canonical_generated_dir = Path("projects/knowledge_base_basic/generated")

        with tempfile.TemporaryDirectory(dir=".") as temp_dir:
            temp_generated_dir = Path(temp_dir) / "generated"
            materialize_knowledge_base_project(
                DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
                output_dir=temp_generated_dir,
            )

            for file_name in (
                "framework_ir.json",
                "product_spec.json",
                "implementation_bundle.py",
                "generation_manifest.json",
                "governance_manifest.json",
                "governance_tree.json",
            ):
                self.assertEqual(
                    (canonical_generated_dir / file_name).read_bytes(),
                    (temp_generated_dir / file_name).read_bytes(),
                    msg=file_name,
                )

    def test_validate_project_governance_detects_stale_evidence(self) -> None:
        with tempfile.TemporaryDirectory(dir=validate_strict_mapping.PROJECTS_DIR) as temp_dir:
            project_dir = Path(temp_dir)
            product_spec_file, route_file = _copy_sample_project_config(project_dir)
            materialize_knowledge_base_project(product_spec_file)
            route_text = route_file.read_text(encoding="utf-8")
            route_file.write_text(
                route_text.replace('workbench = "/knowledge-base"', 'workbench = "/knowledge-chat"'),
                encoding="utf-8",
            )

            issues = validate_strict_mapping.validate_project_governance([product_spec_file])

        self.assertTrue(any(issue["code"] == "STALE_EVIDENCE" for issue in issues))

    def test_compare_project_to_manifest_detects_manifest_expectation_drift(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        payload = build_governance_manifest(project)
        structural_object = next(
            item for item in payload["structural_objects"] if item["object_id"] == "kb.frontend.surface_contract"
        )
        structural_object["expected_evidence"]["layout_variant"] = "broken_variant"
        structural_object["expected_fingerprint"] = "sha256:broken"

        issues = compare_project_to_manifest(project, payload)

        self.assertTrue(
            any(
                issue["code"] == "GOVERNANCE_MANIFEST_INVALID" and issue["symbol_id"] == "kb.frontend.surface_contract"
                for issue in issues
            )
        )

    def test_compare_project_to_manifest_accepts_current_project(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        payload = build_governance_manifest(project)

        issues = compare_project_to_manifest(project, payload)

        self.assertFalse(any(issue["code"] == "EXPECTATION_MISMATCH" for issue in issues))

    def test_compare_project_to_manifest_detects_code_drift(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        payload = build_governance_manifest(project)
        drifted_project = replace(
            project,
            frontend_contract={
                **project.frontend_contract,
                "interaction_actions": [
                    *project.frontend_contract["interaction_actions"],
                    {"action_id": "rogue_action", "boundary": "INTERACT"},
                ],
            },
        )

        issues = compare_project_to_manifest(drifted_project, payload)

        self.assertTrue(
            any(
                issue["code"] == "EXPECTATION_MISMATCH" and issue["symbol_id"] == "kb.frontend.surface_contract"
                for issue in issues
            )
        )

    def test_compare_project_to_manifest_detects_missing_binding(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        payload = build_governance_manifest(project)

        with mock.patch("project_runtime.governance.collect_governed_bindings", return_value={}):
            issues = compare_project_to_manifest(project, payload)

        self.assertTrue(any(issue["code"] == "MISSING_BINDING" for issue in issues))

    def test_compare_project_to_manifest_detects_unknown_binding_symbol(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        payload = build_governance_manifest(project)
        binding_index = collect_governed_bindings(governed_files_for_project(project))
        binding_index["kb.rogue.symbol"] = [
            GovernedBinding(
                symbol_id="kb.rogue.symbol",
                owner="framework",
                kind="api_contract",
                risk="high",
                file="src/knowledge_base_runtime/backend.py",
                locator="function:rogue_route",
                line=1,
            )
        ]

        with mock.patch("project_runtime.governance.collect_governed_bindings", return_value=binding_index):
            issues = compare_project_to_manifest(project, payload)

        self.assertTrue(any(issue["code"] == "UNKNOWN_BINDING" for issue in issues))

    def test_build_governance_manifest_rejects_unknown_binding_symbol(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        binding_index = collect_governed_bindings(governed_files_for_project(project))
        binding_index["kb.rogue.symbol"] = [
            GovernedBinding(
                symbol_id="kb.rogue.symbol",
                owner="framework",
                kind="api_contract",
                risk="high",
                file="src/knowledge_base_runtime/backend.py",
                locator="function:rogue_route",
                line=1,
            )
        ]

        with mock.patch("project_runtime.governance.collect_governed_bindings", return_value=binding_index):
            with self.assertRaises(ValueError):
                build_governance_manifest(project)

    def test_compare_project_to_manifest_detects_invalid_binding_metadata(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        payload = build_governance_manifest(project)
        binding_index = collect_governed_bindings(governed_files_for_project(project))
        binding_index["kb.frontend.surface_contract"] = [
            GovernedBinding(
                symbol_id="kb.frontend.surface_contract",
                owner="product_spec",
                kind="surface_contract",
                risk="high",
                file="src/frontend_kernel/contracts.py",
                locator="function:build_frontend_contract",
                line=9,
            )
        ]

        with mock.patch("project_runtime.governance.collect_governed_bindings", return_value=binding_index):
            issues = compare_project_to_manifest(project, payload)

        self.assertTrue(any(issue["code"] == "INVALID_BINDING_METADATA" for issue in issues))

    def test_compare_project_to_manifest_detects_missing_manifest_symbol(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        payload = build_governance_manifest(project)
        payload["structural_objects"] = [
            item for item in payload["structural_objects"] if item["object_id"] != "kb.answer.behavior"
        ]

        issues = compare_project_to_manifest(project, payload)

        self.assertTrue(any(issue["code"] == "GOVERNANCE_MANIFEST_INVALID" for issue in issues))

    def test_compare_project_to_tree_accepts_current_project(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        payload = build_governance_tree(project)

        issues = compare_project_to_tree(project, payload)

        self.assertFalse(any(issue["code"] == "EXPECTATION_MISMATCH" for issue in issues))

    def test_compare_project_to_tree_detects_code_drift(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        payload = build_governance_tree(project)
        drifted_project = replace(
            project,
            frontend_contract={
                **project.frontend_contract,
                "interaction_actions": [
                    *project.frontend_contract["interaction_actions"],
                    {"action_id": "rogue_action", "boundary": "INTERACT"},
                ],
            },
        )

        issues = compare_project_to_tree(drifted_project, payload)

        self.assertTrue(
            any(
                issue["code"] == "EXPECTATION_MISMATCH" and issue["symbol_id"] == "kb.frontend.surface_contract"
                for issue in issues
            )
        )

    def test_compare_project_to_tree_detects_missing_tree_symbol(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        payload = build_governance_tree(project)
        payload["nodes"] = [
            item
            for item in payload["nodes"]
            if item.get("object_id") != "kb.answer.behavior"
        ]

        issues = compare_project_to_tree(project, payload)

        self.assertTrue(any(issue["code"] == "GOVERNANCE_TREE_INVALID" for issue in issues))


if __name__ == "__main__":
    unittest.main()
