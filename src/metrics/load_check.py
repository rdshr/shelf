from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class LoadCheckInput:
    payload_per_layer: float
    panel_capacity: float | None = None
    rod_capacity: float | None = None
    connector_capacity: float | None = None
    safety_factor: float = 1.0


@dataclass(frozen=True)
class LoadCheckResult:
    performed: bool
    passed: bool
    layer_capacity: float | None
    reason: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def simplified_load_check(payload: LoadCheckInput) -> LoadCheckResult:
    """Conservative check: P_layer_cap = min(panel, rod, connector) / safety_factor."""
    if payload.panel_capacity is None or payload.rod_capacity is None or payload.connector_capacity is None:
        return LoadCheckResult(
            performed=False,
            passed=False,
            layer_capacity=None,
            reason="missing material/section/connector parameters; engineering safety not concluded",
        )

    if payload.safety_factor <= 0:
        return LoadCheckResult(
            performed=False,
            passed=False,
            layer_capacity=None,
            reason="invalid safety_factor; must be > 0",
        )

    layer_capacity = min(payload.panel_capacity, payload.rod_capacity, payload.connector_capacity)
    layer_capacity /= payload.safety_factor
    passed = layer_capacity >= payload.payload_per_layer
    reason = "passed" if passed else "payload exceeds simplified capacity"
    return LoadCheckResult(performed=True, passed=passed, layer_capacity=layer_capacity, reason=reason)
