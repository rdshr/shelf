from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from scripts.publish_framework_draft import publish_framework_draft


class FrameworkDraftPublishTest(unittest.TestCase):
    def test_publish_moves_draft_into_framework_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            draft_root = repo_root / "framework_drafts" / "demo"
            draft_root.mkdir(parents=True)
            draft_file = draft_root / "L2-M0-测试模块.md"
            draft_file.write_text("# 测试模块:Demo\n\n@framework\n", encoding="utf-8")

            original_draft_root = publish_framework_draft.__globals__["DRAFT_ROOT"]
            original_published_root = publish_framework_draft.__globals__["PUBLISHED_ROOT"]
            try:
                publish_framework_draft.__globals__["DRAFT_ROOT"] = repo_root / "framework_drafts"
                publish_framework_draft.__globals__["PUBLISHED_ROOT"] = repo_root / "framework"
                _, target = publish_framework_draft(draft_file, force=False, keep_draft=False)
            finally:
                publish_framework_draft.__globals__["DRAFT_ROOT"] = original_draft_root
                publish_framework_draft.__globals__["PUBLISHED_ROOT"] = original_published_root

            self.assertFalse(draft_file.exists())
            self.assertTrue(target.exists())
            self.assertEqual(target.read_text(encoding="utf-8"), "# 测试模块:Demo\n\n@framework\n")


if __name__ == "__main__":
    unittest.main()
