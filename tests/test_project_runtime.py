from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from knowledge_base_runtime.projection import resolve_knowledge_base_projection
from project_runtime import (
    DEFAULT_PROJECT_FILE,
    load_project_runtime_bundle,
    materialize_project_runtime_bundle,
)


class ProjectRuntimeTest(unittest.TestCase):
    def test_load_default_project_uses_unified_config_and_package_compile(self) -> None:
        project = load_project_runtime_bundle(DEFAULT_PROJECT_FILE)

        self.assertEqual(project.metadata.project_id, "knowledge_base_basic")
        self.assertEqual(project.metadata.runtime_scene, "knowledge_base_workbench")
        self.assertEqual(project.selection.root_modules["frontend"], "framework/frontend/L2-M0-前端框架标准模块.md")
        self.assertEqual(project.root_module_ids["frontend"], "frontend.L2.M0")
        self.assertEqual(project.root_module_ids["knowledge_base"], "knowledge_base.L2.M0")
        self.assertEqual(project.root_module_ids["backend"], "backend.L2.M0")
        self.assertGreaterEqual(len(project.package_compile_order), 3)
        self.assertIn("frontend.L2.M0", project.package_compile_order)
        projection = resolve_knowledge_base_projection(project)
        self.assertEqual(projection.backend_spec["transport"]["project_config_endpoint"], "/api/knowledge/project-config")
        self.assertEqual(projection.ui_spec["implementation"]["frontend_renderer"], "knowledge_chat_client_v1")
        self.assertIn("frontend_contract", project.runtime_exports)
        self.assertEqual(project.to_runtime_bundle_dict()["project_config"]["project"]["project_id"], "knowledge_base_basic")

    def test_materialize_writes_canonical_and_derived_views(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = materialize_project_runtime_bundle(
                DEFAULT_PROJECT_FILE,
                output_dir=Path(temp_dir) / "generated",
            )
            assert project.generated_artifacts is not None
            generated = project.generated_artifacts
            canonical_path = Path(temp_dir) / "generated" / "canonical_graph.json"
            self.assertTrue(canonical_path.exists())
            canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
            self.assertEqual(set(canonical["layers"]), {"framework", "config", "code", "evidence"})
            derived_views = canonical["layers"]["evidence"]["derived_views"]
            self.assertEqual(
                derived_views["governance_manifest_json"]["derived_from"],
                generated.canonical_graph_json,
            )
            self.assertTrue((Path(temp_dir) / "generated" / "runtime_bundle.py").exists())


if __name__ == "__main__":
    unittest.main()
