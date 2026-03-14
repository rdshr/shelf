from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "A11yConfig": ("project_runtime.models", "A11yConfig"),
    "ArtifactConfig": ("project_runtime.models", "ArtifactConfig"),
    "BackendRefinementConfig": ("project_runtime.models", "BackendRefinementConfig"),
    "ChatConfig": ("project_runtime.models", "ChatConfig"),
    "ContextConfig": ("project_runtime.models", "ContextConfig"),
    "DEFAULT_PROJECT_FILE": ("project_runtime.pipeline", "DEFAULT_PROJECT_FILE"),
    "FeatureConfig": ("project_runtime.models", "FeatureConfig"),
    "FrameworkDrivenProjectRecord": ("project_runtime.project_governance", "FrameworkDrivenProjectRecord"),
    "FrontendRefinementConfig": ("project_runtime.models", "FrontendRefinementConfig"),
    "GeneratedArtifactPaths": ("project_runtime.models", "GeneratedArtifactPaths"),
    "KnowledgeDocument": ("project_runtime.models", "KnowledgeDocument"),
    "KnowledgeDocumentSection": ("project_runtime.models", "KnowledgeDocumentSection"),
    "LibraryConfig": ("project_runtime.models", "LibraryConfig"),
    "ModuleSelection": ("project_runtime.models", "ModuleSelection"),
    "PreviewConfig": ("project_runtime.models", "PreviewConfig"),
    "ProjectCompilationState": ("project_runtime.models", "ProjectCompilationState"),
    "ProjectDiscoveryAuditEntry": ("project_runtime.project_governance", "ProjectDiscoveryAuditEntry"),
    "ProjectMetadata": ("project_runtime.models", "ProjectMetadata"),
    "ProjectRuntimeAssembly": ("project_runtime.models", "ProjectRuntimeAssembly"),
    "RefinementConfig": ("project_runtime.models", "RefinementConfig"),
    "ReturnConfig": ("project_runtime.models", "ReturnConfig"),
    "RuntimeProjection": ("project_runtime.models", "RuntimeProjection"),
    "RouteConfig": ("project_runtime.models", "RouteConfig"),
    "SeedDocumentSource": ("project_runtime.models", "SeedDocumentSource"),
    "SelectedRootModule": ("project_runtime.models", "SelectedRootModule"),
    "ShowcasePageConfig": ("project_runtime.models", "ShowcasePageConfig"),
    "SurfaceConfig": ("project_runtime.models", "SurfaceConfig"),
    "UnifiedProjectConfig": ("project_runtime.models", "UnifiedProjectConfig"),
    "VisualConfig": ("project_runtime.models", "VisualConfig"),
    "build_project_discovery_audit": ("project_runtime.project_governance", "build_project_discovery_audit"),
    "build_project_runtime_app_from_project_file": ("project_runtime.pipeline", "build_project_runtime_app_from_project_file"),
    "compile_knowledge_document_source": ("project_runtime.documents", "compile_knowledge_document_source"),
    "compile_project_runtime_bundle": ("project_runtime.pipeline", "compile_project_runtime_bundle"),
    "discover_project_entry_files": ("project_runtime.project_governance", "discover_project_entry_files"),
    "discover_framework_driven_projects": ("project_runtime.project_governance", "discover_framework_driven_projects"),
    "load_project_runtime_bundle": ("project_runtime.pipeline", "load_project_runtime_bundle"),
    "materialize_project_runtime_bundle": ("project_runtime.pipeline", "materialize_project_runtime_bundle"),
    "render_project_discovery_audit_markdown": ("project_runtime.project_governance", "render_project_discovery_audit_markdown"),
}

__all__ = sorted(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(name)
    module_name, attr_name = _EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
