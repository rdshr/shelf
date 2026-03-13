from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from project_runtime.knowledge_base import materialize_knowledge_base_project
from scripts import validate_strict_mapping


def _copy_sample_project_config(project_dir: Path) -> Path:
    source_product_spec = Path("projects/knowledge_base_basic/product_spec.toml")
    source_product_spec_dir = Path("projects/knowledge_base_basic/product_spec")
    source_implementation_config = Path("projects/knowledge_base_basic/implementation_config.toml")
    product_spec_file = project_dir / "product_spec.toml"
    implementation_config_file = project_dir / "implementation_config.toml"
    shutil.copy2(source_product_spec, product_spec_file)
    shutil.copy2(source_implementation_config, implementation_config_file)
    shutil.copytree(source_product_spec_dir, project_dir / "product_spec")
    return product_spec_file


class ProjectGenerationDisciplineTest(unittest.TestCase):
    def test_project_directory_forbids_direct_code_files(self) -> None:
        with tempfile.TemporaryDirectory(dir=validate_strict_mapping.PROJECTS_DIR) as temp_dir:
            project_dir = Path(temp_dir)
            product_spec_file = _copy_sample_project_config(project_dir)
            (project_dir / "app.py").write_text("print('forbidden')\n", encoding="utf-8")

            issues = validate_strict_mapping.validate_project_generation_discipline([product_spec_file])

        self.assertTrue(any(issue["code"] == "PROJECT_DIRECT_CODE_FORBIDDEN" for issue in issues))

    def test_generated_artifacts_must_stay_in_sync(self) -> None:
        with tempfile.TemporaryDirectory(dir=validate_strict_mapping.PROJECTS_DIR) as temp_dir:
            project_dir = Path(temp_dir)
            product_spec_file = _copy_sample_project_config(project_dir)
            materialize_knowledge_base_project(product_spec_file)
            generated_file = project_dir / "generated" / "implementation_bundle.py"
            generated_file.write_text("# manually edited\n", encoding="utf-8")

            issues = validate_strict_mapping.validate_project_generation_discipline([product_spec_file])

        self.assertTrue(any(issue["code"] == "PROJECT_GENERATED_OUT_OF_SYNC" for issue in issues))

    def test_product_spec_layout_rejects_legacy_top_level_sections(self) -> None:
        with tempfile.TemporaryDirectory(dir=validate_strict_mapping.PROJECTS_DIR) as temp_dir:
            project_dir = Path(temp_dir)
            product_spec_file = _copy_sample_project_config(project_dir)
            product_spec_text = product_spec_file.read_text(encoding="utf-8")
            product_spec_file.write_text(product_spec_text + '\n[theme]\nbrand = "Legacy"\n', encoding="utf-8")

            issues = validate_strict_mapping.validate_project_generation_discipline([product_spec_file])

        self.assertTrue(any(issue["code"] == "PROJECT_PRODUCT_SPEC_SECTION_UNKNOWN" for issue in issues))


if __name__ == "__main__":
    unittest.main()
