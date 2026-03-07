from __future__ import annotations

from itertools import combinations

from domain.enums import Module
from framework_core import CombinationRules, Rule


def default_combination_rules() -> CombinationRules[Module]:
    return CombinationRules(
        [
            Rule(
                rule_id="R1",
                description="module set must not be isolated",
                validator=lambda combo: len(combo) >= 2,
            ),
            Rule(
                rule_id="R2",
                description="connector must exist in every usable combination",
                validator=lambda combo: Module.CONNECTOR in combo,
            ),
        ]
    )


def module_type_combinations() -> list[set[Module]]:
    """R1+R2 level type combinations from module universe {R, C, P}."""
    return default_combination_rules().valid_subsets(universe=list(Module))


def geometric_type_combinations() -> list[set[Module]]:
    """Apply R5 geometric feasibility: panel requires rods for 4-corner support."""
    out: list[set[Module]] = []
    for combo in module_type_combinations():
        if Module.PANEL in combo and Module.ROD not in combo:
            continue
        out.append(combo)
    return out


def classify_combo_sets() -> dict[str, list[list[str]]]:
    return {
        "M_type": [sorted(item.value for item in combo) for combo in module_type_combinations()],
        "M_geo": [sorted(item.value for item in combo) for combo in geometric_type_combinations()],
    }


def build_extended_rules() -> CombinationRules:
    """Explicit rule set used in examples and teaching docs."""
    base = list(default_combination_rules().rules)
    base.append(
        Rule(
            rule_id="R5-type",
            description="panel-only support is invalid without rods",
            validator=lambda combo: not (Module.PANEL in combo and Module.ROD not in combo),
        )
    )
    return CombinationRules(base)


def all_module_subsets() -> list[set[Module]]:
    universe = list(Module)
    out: list[set[Module]] = [set()]
    for size in range(1, len(universe) + 1):
        for subset in combinations(universe, size):
            out.append(set(subset))
    return out
