from __future__ import annotations

import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import validate_strict_mapping


class CodeLanguageStandardsContractTest(unittest.TestCase):
    def test_code_language_standards_contract_passes_with_agents_refs(self) -> None:
        with tempfile.TemporaryDirectory(dir=validate_strict_mapping.REPO_ROOT) as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "specs/code").mkdir(parents=True)
            (repo_root / "specs/code/Python实现质量标准.md").write_text("# Python\n", encoding="utf-8")
            (repo_root / "specs/code/TypeScript实现质量标准.md").write_text("# TypeScript\n", encoding="utf-8")
            (repo_root / "specs/code/代码语言标准索引.toml").write_text(
                textwrap.dedent(
                    """
                    version = 1

                    [[mapping]]
                    patterns = ["*.py"]
                    standards = ["specs/code/Python实现质量标准.md"]

                    [[mapping]]
                    patterns = ["*.ts"]
                    standards = ["specs/code/TypeScript实现质量标准.md"]
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (repo_root / "AGENTS.md").write_text(
                textwrap.dedent(
                    """
                    - `specs/code/Python实现质量标准.md`
                    - `specs/code/TypeScript实现质量标准.md`
                    - `specs/code/代码语言标准索引.toml`
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )

            issues = validate_strict_mapping.validate_code_language_standards_contract(repo_root)
            self.assertEqual(issues, [])

    def test_agents_must_reference_all_standard_files_from_index(self) -> None:
        with tempfile.TemporaryDirectory(dir=validate_strict_mapping.REPO_ROOT) as tmp_dir:
            repo_root = Path(tmp_dir)
            (repo_root / "specs/code").mkdir(parents=True)
            (repo_root / "specs/code/Python实现质量标准.md").write_text("# Python\n", encoding="utf-8")
            (repo_root / "specs/code/代码语言标准索引.toml").write_text(
                textwrap.dedent(
                    """
                    version = 1

                    [[mapping]]
                    patterns = ["*.py"]
                    standards = ["specs/code/Python实现质量标准.md"]
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            (repo_root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")

            issues = validate_strict_mapping.validate_code_language_standards_contract(repo_root)
            self.assertTrue(any(issue["code"] == "AGENTS_CODE_STANDARD_REF_MISSING" for issue in issues))
