from __future__ import annotations

import unittest

from standards_tree import (
    StandardsTreeNode,
    build_standards_tree,
    build_standards_tree_node,
    discover_l2_standard_files,
    level_files_from_tree,
)


class StandardsTreeTest(unittest.TestCase):
    def test_build_standards_tree_node_serializes_to_canonical_payload(self) -> None:
        root = build_standards_tree_node()

        self.assertIsInstance(root, StandardsTreeNode)
        self.assertEqual(root.level, "L0")
        self.assertEqual(root.file_name, "specs/规范总纲与树形结构.md")
        self.assertEqual(root.to_dict(), build_standards_tree())

    def test_level_files_from_tree_accepts_node_and_payload(self) -> None:
        root = build_standards_tree_node()
        payload = build_standards_tree()

        self.assertEqual(level_files_from_tree(root), level_files_from_tree(payload))

    def test_discovered_l2_files_have_stable_node_ids(self) -> None:
        discovered = discover_l2_standard_files()

        self.assertTrue(discovered)
        self.assertTrue(all(item.node_id.startswith("NODE-L2-") for item in discovered))
        self.assertTrue(all(item.file_name.startswith("framework/") for item in discovered))


if __name__ == "__main__":
    unittest.main()
