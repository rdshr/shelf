from __future__ import annotations

from typing import Any

from framework_packages.contract import PackageConfigContract, PackageConfigFieldRule
from project_runtime.models import jsonable
from project_runtime.utils import flatten_config_paths


def flatten_project_payload(root_payload: dict[str, Any]) -> dict[str, Any]:
    return flatten_config_paths(root_payload)


def resolve_config_slice(
    available_payload: dict[str, Any],
    *,
    contract: PackageConfigContract,
    package_id: str,
) -> dict[str, Any]:
    flattened = _flatten_if_needed(available_payload)
    declared_paths = {item.path for item in contract.fields}
    resolved: dict[str, Any] = {}

    for item in contract.fields:
        path = item.path
        if item.presence == "required":
            if path not in flattened:
                raise ValueError(f"missing required config path for {package_id}: {path}")
            resolved[path] = jsonable(flattened[path])
            continue
        if item.presence == "optional":
            if path in flattened:
                resolved[path] = jsonable(flattened[path])
            continue
        if item.presence == "default":
            resolved[path] = jsonable(flattened[path]) if path in flattened else jsonable(item.default_value)
            continue
        if item.presence == "forbidden" and path in flattened:
            raise ValueError(f"forbidden config path for {package_id}: {path}")
        if item.presence not in {"required", "optional", "default", "forbidden"}:
            raise ValueError(f"unsupported contract presence for {package_id}: {item.presence}")

    if contract.allow_extra_paths:
        return resolved

    extra_paths = sorted(
        path
        for path in flattened
        if _is_under_covered_root(path, contract.covered_roots)
        and path not in declared_paths
    )
    if extra_paths:
        raise ValueError(f"undeclared config paths for {package_id}: {', '.join(extra_paths)}")
    return resolved


def project_owned_config_payload(
    available_payload: dict[str, Any],
    *,
    contract: PackageConfigContract,
) -> dict[str, Any]:
    flattened = _flatten_if_needed(available_payload)
    owned: dict[str, Any] = {}
    if contract.allow_extra_paths:
        owned.update(flattened)
    else:
        owned.update(
            {
                path: jsonable(value)
                for path, value in flattened.items()
                if _is_under_covered_root(path, contract.covered_roots)
            }
        )
    for item in contract.fields:
        if item.presence == "default" and item.path not in owned:
            owned[item.path] = jsonable(item.default_value)
    return owned


def merge_config_contracts(*contracts: PackageConfigContract) -> PackageConfigContract:
    fields_by_path: dict[str, PackageConfigFieldRule] = {}
    covered_roots: set[str] = set()
    allow_extra_paths = False
    for contract in contracts:
        allow_extra_paths = allow_extra_paths or contract.allow_extra_paths
        covered_roots.update(contract.covered_roots)
        for field in contract.fields:
            existing = fields_by_path.get(field.path)
            if existing is None:
                fields_by_path[field.path] = field
                continue
            if existing != field:
                raise ValueError(f"conflicting config contract for path: {field.path}")
    return PackageConfigContract(
        fields=tuple(sorted(fields_by_path.values(), key=lambda item: item.path)),
        covered_roots=tuple(sorted(covered_roots)),
        allow_extra_paths=allow_extra_paths,
    )


def _flatten_if_needed(payload: dict[str, Any]) -> dict[str, Any]:
    if payload and all("." in key or key in {"project", "selection", "truth", "refinement", "narrative"} for key in payload):
        # Nested payloads still need flattening; flat payloads already carry dotted keys.
        if any("." in key for key in payload):
            return {str(key): jsonable(value) for key, value in payload.items()}
    return flatten_config_paths(payload)


def _is_under_covered_root(path: str, covered_roots: tuple[str, ...]) -> bool:
    for root in covered_roots:
        if path == root or path.startswith(f"{root}."):
            return True
    return False
