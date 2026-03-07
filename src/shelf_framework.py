from __future__ import annotations

from framework_core import (
    Base,
    BoundaryDefinition as FrameworkBoundaryDefinition,
    BoundaryItem,
    Capability,
    CombinationRules,
    Goal,
    Hypothesis,
    LogicRecord,
    LogicStep,
    Rule,
    VerificationInput as FrameworkVerificationInput,
    VerificationResult as FrameworkVerificationResult,
)
from shelf_domain import (
    BoundaryDefinition,
    ExactFitSpec,
    Footprint2D,
    MODULE_ROLE,
    Module,
    Opening2D,
    Space3D,
    StructuralPrinciples,
    VerificationInput,
    VerificationResult,
    modules_to_list,
    verify,
)

STRICT_MAPPING_LEVEL = "L3"
STRICT_MAPPING_REGISTRY = "mapping/mapping_registry.json"
STRICT_MAPPING_VALIDATION_COMMAND = (
    "uv run python scripts/validate_strict_mapping.py --check-changes"
)


def strict_mapping_meta() -> dict[str, str]:
    return {
        "level": STRICT_MAPPING_LEVEL,
        "registry": STRICT_MAPPING_REGISTRY,
        "validation_command": STRICT_MAPPING_VALIDATION_COMMAND,
    }


__all__ = [
    "Base",
    "BoundaryDefinition",
    "BoundaryItem",
    "Capability",
    "CombinationRules",
    "ExactFitSpec",
    "Footprint2D",
    "FrameworkBoundaryDefinition",
    "FrameworkVerificationInput",
    "FrameworkVerificationResult",
    "Goal",
    "Hypothesis",
    "LogicRecord",
    "LogicStep",
    "MODULE_ROLE",
    "Module",
    "Opening2D",
    "Rule",
    "Space3D",
    "StructuralPrinciples",
    "STRICT_MAPPING_LEVEL",
    "STRICT_MAPPING_REGISTRY",
    "STRICT_MAPPING_VALIDATION_COMMAND",
    "VerificationInput",
    "VerificationResult",
    "modules_to_list",
    "strict_mapping_meta",
    "verify",
]
