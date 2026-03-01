from __future__ import annotations

import unittest

from domain.enums import Module
from rules.combination_rules import geometric_type_combinations, module_type_combinations


class CombinationRulesTest(unittest.TestCase):
    def test_type_combinations_include_rc_and_rcp(self) -> None:
        combos = [frozenset(item) for item in module_type_combinations()]
        self.assertIn(frozenset({Module.ROD, Module.CONNECTOR}), combos)
        self.assertIn(frozenset({Module.ROD, Module.CONNECTOR, Module.PANEL}), combos)

    def test_cp_invalid_under_r5_geometric_filter(self) -> None:
        combos = [frozenset(item) for item in geometric_type_combinations()]
        self.assertNotIn(frozenset({Module.CONNECTOR, Module.PANEL}), combos)


if __name__ == "__main__":
    unittest.main()
