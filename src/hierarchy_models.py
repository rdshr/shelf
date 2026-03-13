from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HierarchyNode:
    node_id: str
    label: str
    level: int
    description: str
    order: int | None = None
    metadata: dict[str, Any] | None = None

    def to_payload_dict(self) -> dict[str, Any]:
        payload = {
            "id": self.node_id,
            "label": self.label,
            "level": self.level,
            "description": self.description,
        }
        if self.order is not None:
            payload["order"] = self.order
        if self.metadata:
            payload.update(self.metadata)
        return payload


@dataclass(frozen=True)
class HierarchyEdge:
    source: str
    target: str
    relation: str
    metadata: dict[str, Any]

    def to_payload_dict(self) -> dict[str, Any]:
        payload = {
            "from": self.source,
            "to": self.target,
            "relation": self.relation,
        }
        payload.update(self.metadata)
        return payload


@dataclass(frozen=True)
class HierarchyFrameworkGroup:
    name: str
    order: int
    local_levels: list[int]
    level_node_counts: dict[int, int]

    def to_payload_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "order": self.order,
            "local_levels": self.local_levels,
            "level_node_counts": {str(level): count for level, count in self.level_node_counts.items()},
        }


@dataclass(frozen=True)
class HierarchyGraph:
    title: str
    description: str
    level_labels: dict[int, str]
    nodes: list[HierarchyNode]
    edges: list[HierarchyEdge]
    layout_mode: str = "global_levels"
    framework_groups: list[HierarchyFrameworkGroup] | None = None
    storage_key_stem: str | None = None

    def to_payload_dict(self) -> dict[str, Any]:
        root: dict[str, Any] = {
            "title": self.title,
            "description": self.description,
            "level_labels": {str(level): label for level, label in self.level_labels.items()},
            "nodes": [node.to_payload_dict() for node in self.nodes],
            "edges": [edge.to_payload_dict() for edge in self.edges],
        }
        if self.layout_mode != "global_levels":
            root["layout_mode"] = self.layout_mode
        if self.framework_groups:
            root["framework_groups"] = [group.to_payload_dict() for group in self.framework_groups]
        if self.storage_key_stem is not None:
            root["storage_key_stem"] = self.storage_key_stem
        return {"root": root}
