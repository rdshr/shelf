from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from knowledge_base_runtime.runtime_exports import (
    resolve_runtime_blueprint,
    resolve_runtime_documents,
)
from project_runtime import (
    DEFAULT_PROJECT_FILE,
    load_project_runtime,
    materialize_project_runtime,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


class ProjectRuntimeTest(unittest.TestCase):
    def test_load_default_project_uses_unified_config_and_package_compile(self) -> None:
        project = load_project_runtime(DEFAULT_PROJECT_FILE)

        self.assertEqual(project.metadata.project_id, "knowledge_base_basic")
        self.assertEqual(project.metadata.runtime_scene, "package_export_runtime")
        self.assertEqual(project.selection.root_modules["frontend"], "framework/frontend/L2-M0-前端框架标准模块.md")
        self.assertEqual(project.root_module_ids["frontend"], "frontend.L2.M0")
        self.assertEqual(project.root_module_ids["knowledge_base"], "knowledge_base.L2.M0")
        self.assertEqual(project.root_module_ids["backend"], "backend.L2.M0")
        self.assertGreaterEqual(len(project.package_compile_order), 3)
        self.assertIn("frontend.L2.M0", project.package_compile_order)
        runtime_blueprint = resolve_runtime_blueprint(project)
        runtime_documents = resolve_runtime_documents(project)
        self.assertEqual(runtime_blueprint["transport"]["project_config_endpoint"], "/api/knowledge/project-config")
        self.assertEqual(runtime_blueprint["landing_path"], "/knowledge-base")
        self.assertEqual(runtime_blueprint["page_routes"][0]["route_id"], "chat_home")
        self.assertEqual(runtime_blueprint["api_router_factory"], "knowledge_base_runtime.backend:build_knowledge_base_router")
        self.assertGreaterEqual(len(runtime_documents), 1)
        self.assertIn("runtime_blueprint", project.runtime_exports)
        self.assertIn("runtime_documents", project.runtime_exports)
        self.assertEqual(project.to_runtime_snapshot_dict()["project_config"]["project"]["project_id"], "knowledge_base_basic")
        self.assertFalse(hasattr(project, "library"))
        self.assertFalse(hasattr(project, "route"))
        self.assertFalse(hasattr(project, "chat"))

    def test_materialize_writes_canonical_and_derived_views(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project = materialize_project_runtime(
                DEFAULT_PROJECT_FILE,
                output_dir=Path(temp_dir) / "generated",
            )
            assert project.generated_artifacts is not None
            generated = project.generated_artifacts
            canonical_path = Path(temp_dir) / "generated" / "canonical_graph.json"
            self.assertTrue(canonical_path.exists())
            canonical = json.loads(canonical_path.read_text(encoding="utf-8"))
            self.assertEqual(set(canonical["layers"]), {"framework", "config", "code", "evidence"})
            package_result = canonical["layers"]["code"]["package_results"]["frontend.L2.M0"]
            self.assertEqual(
                package_result["package_source_file"],
                "src/framework_packages/modules/frontend_l2_m0/__init__.py",
            )
            derived_views = canonical["layers"]["evidence"]["derived_views"]
            self.assertEqual(
                derived_views["derived_governance_manifest_json"]["derived_from"],
                generated.canonical_graph_json,
            )
            strict_zone_report = json.loads(
                (Path(temp_dir) / "generated" / "strict_zone_report.json").read_text(encoding="utf-8")
            )
            for item in strict_zone_report["files"]:
                self.assertTrue((REPO_ROOT / item["file"]).exists(), item["file"])
            self.assertTrue((Path(temp_dir) / "generated" / "runtime_snapshot.py").exists())

    def test_strict_mapping_supports_json_output_for_report_scripts(self) -> None:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "validate_strict_mapping.py"), "--json", "--check-changes"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["passed"])
        self.assertIn("errors", payload)


if __name__ == "__main__":
    unittest.main()
