from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from project_runtime.knowledge_base import materialize_knowledge_base_project
from scripts import validate_strict_mapping


class ProjectGenerationDisciplineTest(unittest.TestCase):
    def test_project_directory_forbids_direct_code_files(self) -> None:
        source_instance = Path("projects/knowledge_base_basic/instance.toml")
        instance_text = source_instance.read_text(encoding="utf-8")

        with tempfile.TemporaryDirectory(dir=validate_strict_mapping.PROJECTS_DIR) as temp_dir:
            project_dir = Path(temp_dir)
            instance_file = project_dir / "instance.toml"
            instance_file.write_text(instance_text, encoding="utf-8")
            (project_dir / "app.py").write_text("print('forbidden')\n", encoding="utf-8")

            issues = validate_strict_mapping.validate_project_generation_discipline([instance_file])

        self.assertTrue(any(issue["code"] == "PROJECT_DIRECT_CODE_FORBIDDEN" for issue in issues))

    def test_generated_artifacts_must_stay_in_sync(self) -> None:
        source_instance = Path("projects/knowledge_base_basic/instance.toml")
        instance_text = source_instance.read_text(encoding="utf-8")

        with tempfile.TemporaryDirectory(dir=validate_strict_mapping.PROJECTS_DIR) as temp_dir:
            project_dir = Path(temp_dir)
            instance_file = project_dir / "instance.toml"
            instance_file.write_text(instance_text, encoding="utf-8")
            materialize_knowledge_base_project(instance_file)
            generated_file = project_dir / "generated" / "project_bundle.py"
            generated_file.write_text("# manually edited\n", encoding="utf-8")

            issues = validate_strict_mapping.validate_project_generation_discipline([instance_file])

        self.assertTrue(any(issue["code"] == "PROJECT_GENERATED_OUT_OF_SYNC" for issue in issues))

    def test_instance_layout_rejects_legacy_top_level_sections(self) -> None:
        source_instance = Path("projects/knowledge_base_basic/instance.toml")
        instance_text = source_instance.read_text(encoding="utf-8")

        with tempfile.TemporaryDirectory(dir=validate_strict_mapping.PROJECTS_DIR) as temp_dir:
            project_dir = Path(temp_dir)
            instance_file = project_dir / "instance.toml"
            instance_file.write_text(instance_text + '\n[theme]\nbrand = "Legacy"\n', encoding="utf-8")

            issues = validate_strict_mapping.validate_project_generation_discipline([instance_file])

        self.assertTrue(any(issue["code"] == "PROJECT_INSTANCE_SECTION_UNKNOWN" for issue in issues))


if __name__ == "__main__":
    unittest.main()
