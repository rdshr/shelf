from typing import TYPE_CHECKING

from .enums import MODULE_ROLE, Module, StructureFamily
from .models import (
    BoundaryDefinition,
    CandidateEvaluation,
    DiscreteGrid,
    EnumerationConfig,
    EnumerationStats,
    ExactFitSpec,
    Footprint2D,
    GridEdge3D,
    GridPoint3D,
    Opening2D,
    PanelPlacement,
    Rect2D,
    Space3D,
    StructureTopology,
    VerificationInput,
    VerificationResult,
)
if TYPE_CHECKING:
    from framework_core import (
        Base,
        BoundaryDefinition as FrameworkBoundaryDefinition,
        BoundaryItem,
        Capability,
        Goal,
        Hypothesis,
        LogicRecord,
        LogicStep,
    )
else:
    try:
        import framework_core as _framework_core
    except ModuleNotFoundError:  # pragma: no cover - compatibility for src.package imports
        from .. import framework_core as _framework_core

    Base = _framework_core.Base
    FrameworkBoundaryDefinition = _framework_core.BoundaryDefinition
    BoundaryItem = _framework_core.BoundaryItem
    Capability = _framework_core.Capability
    Goal = _framework_core.Goal
    Hypothesis = _framework_core.Hypothesis
    LogicRecord = _framework_core.LogicRecord
    LogicStep = _framework_core.LogicStep

__all__ = [
    "Base",
    "BoundaryDefinition",
    "BoundaryItem",
    "Capability",
    "CandidateEvaluation",
    "DiscreteGrid",
    "EnumerationConfig",
    "EnumerationStats",
    "ExactFitSpec",
    "Footprint2D",
    "FrameworkBoundaryDefinition",
    "GridEdge3D",
    "GridPoint3D",
    "Goal",
    "Hypothesis",
    "LogicRecord",
    "LogicStep",
    "MODULE_ROLE",
    "Module",
    "Opening2D",
    "PanelPlacement",
    "Rect2D",
    "Space3D",
    "StructureFamily",
    "StructureTopology",
    "VerificationInput",
    "VerificationResult",
]
