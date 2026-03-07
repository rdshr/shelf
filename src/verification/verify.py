from __future__ import annotations

from dataclasses import dataclass

from domain.enums import StructureFamily
from domain.models import BoundaryDefinition, DiscreteGrid, StructureTopology, VerificationInput
from metrics.efficiency import UtilizationResult, calculate_utilization
from rules.combination_rules import geometric_type_combinations
from rules.structural_rules import StructuralCheck, evaluate_structural_rules
from shelf_domain import verify


@dataclass(frozen=True)
class StructureVerificationReport:
    family: str
    passed: bool
    boundary_valid: bool
    combination_valid: bool
    structural_valid: bool
    utilization_improved: bool
    target_utilization: float
    baseline_utilization: float
    reasons: list[str]
    structural_checks: list[StructuralCheck]
    utilization: UtilizationResult

    @property
    def efficiency_improved(self) -> bool:
        return self.utilization_improved

    @property
    def target_efficiency(self) -> float:
        return self.target_utilization

    @property
    def baseline_efficiency(self) -> float:
        return self.baseline_utilization

    @property
    def efficiency(self) -> UtilizationResult:
        return self.utilization

    def to_dict(self) -> dict[str, object]:
        return {
            "family": self.family,
            "passed": self.passed,
            "boundary_valid": self.boundary_valid,
            "combination_valid": self.combination_valid,
            "structural_valid": self.structural_valid,
            "metric_name": "space_utilization",
            "utilization_improved": self.utilization_improved,
            "target_utilization": self.target_utilization,
            "baseline_utilization": self.baseline_utilization,
            "efficiency_improved": self.utilization_improved,
            "target_efficiency": self.target_utilization,
            "baseline_efficiency": self.baseline_utilization,
            "reasons": self.reasons,
            "structural_checks": [item.to_dict() for item in self.structural_checks],
            "utilization": self.utilization.to_dict(),
            "efficiency": self.utilization.to_dict(),
        }


def verify_structure(
    topology: StructureTopology,
    boundary: BoundaryDefinition,
    grid: DiscreteGrid,
    baseline_efficiency: float,
    frame_forbid_dangling_rods: bool = False,
) -> StructureVerificationReport:
    valid_combinations = geometric_type_combinations()
    combo = topology.module_combo()

    utilization = calculate_utilization(topology, boundary, grid, baseline_efficiency)
    base = verify(
        VerificationInput(
            boundary=boundary,
            combo=combo,
            valid_combinations=valid_combinations,
            baseline_efficiency=baseline_efficiency,
            target_efficiency=utilization.target_utilization,
        )
    )

    structural_checks = evaluate_structural_rules(
        topology,
        grid,
        forbid_dangling_rods=frame_forbid_dangling_rods,
    )
    structural_valid = all(item.passed for item in structural_checks)

    reasons = [*base.reasons]
    for item in structural_checks:
        reasons.extend(item.reasons)

    if topology.family == StructureFamily.FRAME:
        reasons.append("family-specific verification path: FRAME (R4/R5/R6 not applicable, frame rules enabled)")
    else:
        reasons.append("family-specific verification path: SHELF (R3/R4/R5/R6)")

    passed = base.passed and structural_valid

    return StructureVerificationReport(
        family=topology.family.value,
        passed=passed,
        boundary_valid=base.boundary_valid,
        combination_valid=base.combination_valid,
        structural_valid=structural_valid,
        utilization_improved=base.efficiency_improved,
        target_utilization=utilization.target_utilization,
        baseline_utilization=baseline_efficiency,
        reasons=reasons,
        structural_checks=structural_checks,
        utilization=utilization,
    )
