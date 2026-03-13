from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from project_runtime import scaffold_registered_project
from project_runtime.project_config_source import (
    ProjectConfigLoadError,
    load_product_spec_document,
)


class ProjectConfigSourceTest(unittest.TestCase):
    def test_load_product_spec_document_reads_split_sections(self) -> None:
        product_spec_file = Path("projects/knowledge_base_basic/product_spec.toml")
        document = load_product_spec_document(product_spec_file)

        self.assertIn("chat", document.merged_data)
        self.assertIn("surface", document.merged_data)
        self.assertEqual(
            document.source_file_for_section("chat").as_posix().split("/")[-2:],
            ["product_spec", "chat.toml"],
        )
        self.assertGreaterEqual(document.line_for_section("chat"), 1)
        self.assertGreaterEqual(document.line_for_nested_section("chat", "copy"), 1)

    def test_duplicate_split_section_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir)
            (project_dir / "product_spec").mkdir(parents=True)
            (project_dir / "product_spec.toml").write_text(
                "\n".join(
                    [
                        "[project]",
                        'project_id = "demo"',
                        'template = "knowledge_base_workbench"',
                        'display_name = "Demo"',
                        'description = "Demo"',
                        'version = "0.1.0"',
                        "",
                        "[framework]",
                        'frontend = "framework/frontend/L2-M0-前端框架标准模块.md"',
                        'domain = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"',
                        'backend = "framework/backend/L2-M0-知识库接口框架标准模块.md"',
                        'preset = "document_chat_workbench"',
                        "",
                        "[chat]",
                        "enabled = true",
                    ]
                ),
                encoding="utf-8",
            )
            (project_dir / "product_spec" / "chat.toml").write_text(
                "\n".join(
                    [
                        "[chat]",
                        "enabled = true",
                    ]
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ProjectConfigLoadError):
                load_product_spec_document(project_dir / "product_spec.toml")

    def test_scaffold_registered_project_writes_modular_product_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "demo_project"
            written = scaffold_registered_project(
                project_dir,
                template_id="knowledge_base_workbench",
                display_name="Demo Project",
                modular_product_spec=True,
                force=False,
            )

            self.assertIn("product_spec.toml", written)
            self.assertIn("product_spec/chat.toml", written)
            self.assertTrue((project_dir / "product_spec.toml").exists())
            self.assertTrue((project_dir / "product_spec" / "chat.toml").exists())
            self.assertTrue((project_dir / "implementation_config.toml").exists())


if __name__ == "__main__":
    unittest.main()
