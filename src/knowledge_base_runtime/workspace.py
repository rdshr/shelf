from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from framework_core import Base, BoundaryDefinition, BoundaryItem, Capability, VerificationInput, VerificationResult, verify
from project_runtime.knowledge_base import KnowledgeBaseCodeModule, load_knowledge_base_code_module


def _resolve_project(project: KnowledgeBaseCodeModule | None) -> KnowledgeBaseCodeModule:
    return project or load_knowledge_base_code_module()


def _module_capabilities(project: KnowledgeBaseCodeModule) -> tuple[Capability, ...]:
    return tuple(Capability(item.capability_id, item.statement) for item in project.domain_ir.capabilities)


def _module_boundary(project: KnowledgeBaseCodeModule) -> BoundaryDefinition:
    return BoundaryDefinition(
        items=tuple(BoundaryItem(item.boundary_id, item.statement) for item in project.domain_ir.boundaries)
    )


def _module_bases(project: KnowledgeBaseCodeModule) -> tuple[Base, ...]:
    return tuple(Base(item.base_id, item.name, item.inline_expr or item.statement) for item in project.domain_ir.bases)


KNOWLEDGE_BASE_WORKSPACE_CAPABILITIES = (
    Capability("C1", "将会话侧栏、聊天主区与来源抽屉收敛为统一知识问答客户端。"),
    Capability("C2", "统一当前知识库、当前文档、当前章节与当前会话的上下文传递。"),
    Capability("C3", "支持从回答内引用展开来源、进入文档详情并返回会话。"),
)

KNOWLEDGE_BASE_WORKSPACE_BOUNDARY = BoundaryDefinition(
    items=(
        BoundaryItem("SURFACE", "会话侧栏、聊天主区与引用抽屉必须同时存在。"),
        BoundaryItem("LIBRARY", "知识库切换、文档浏览与文件入口必须统一。"),
        BoundaryItem("PREVIEW", "来源抽屉、文档详情与章节锚点必须稳定。"),
        BoundaryItem("CHAT", "输入、回合顺序、流式回复与引用附着必须稳定。"),
        BoundaryItem("CONTEXT", "当前知识库、当前文档和当前章节上下文必须显式传递。"),
        BoundaryItem("RETURN", "引用必须能返回抽屉和文档详情页。"),
    )
)

KNOWLEDGE_BASE_WORKSPACE_BASES = (
    Base("B1", "聊天客户端场景基", "conversation sidebar + chat main + composer"),
    Base("B2", "引用来源场景基", "inline refs + citation drawer + document detail"),
    Base("B3", "知识问答回路场景基", "knowledge base select -> conversation -> citation -> document detail"),
)


@dataclass(frozen=True)
class WorkspaceScenario:
    scene_id: str
    title: str
    steps: tuple[str, ...]
    entry_path: str
    return_path: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compose_workspace_flow(project: KnowledgeBaseCodeModule | None = None) -> tuple[WorkspaceScenario, ...]:
    resolved = _resolve_project(project)
    lead_document = resolved.documents[0]
    lead_section = lead_document.sections[1]
    ui_spec = resolved.ui_spec
    return_policy = resolved.backend_spec["return_policy"]
    knowledge_base_detail = return_policy["knowledge_base_detail_path"].replace(
        "{knowledge_base_id}", resolved.library.knowledge_base_id
    )
    document_detail = (
        return_policy["document_detail_path"].replace("{document_id}", lead_document.document_id)
        + f"?section={lead_section.section_id}"
    )
    return (
        WorkspaceScenario(
            scene_id="chat_home",
            title=ui_spec["pages"]["chat_home"]["title"],
            steps=("open chat shell", "review current knowledge base", "start a new conversation"),
            entry_path=resolved.route.workbench,
            return_path=resolved.route.workbench,
        ),
        WorkspaceScenario(
            scene_id="citation_review",
            title=ui_spec["components"]["citation_drawer"]["title"],
            steps=("ask question", "inspect inline references", "open citation drawer"),
            entry_path=f"{resolved.route.workbench}?document={lead_document.document_id}&section={lead_section.section_id}",
            return_path=resolved.route.workbench,
        ),
        WorkspaceScenario(
            scene_id="document_trace",
            title=ui_spec["pages"]["document_detail"]["title"],
            steps=("open knowledge base detail", "open document detail", "return to chat"),
            entry_path=knowledge_base_detail,
            return_path=document_detail,
        ),
    )


def verify_workspace_flow(project: KnowledgeBaseCodeModule | None = None) -> VerificationResult:
    resolved = _resolve_project(project)
    boundary = _module_boundary(resolved)
    boundary_valid, boundary_errors = boundary.validate()
    result = verify(
        VerificationInput(
            subject="knowledge base workbench flow",
            pass_criteria=[
                "conversation sidebar, chat main, and citation drawer all exist",
                "the current knowledge base, document, and section stay explicit across chat and source review",
                "citations expose return paths back to drawer and document detail views",
            ],
            evidence={
                "project": resolved.public_summary,
                "capabilities": [item.to_dict() for item in _module_capabilities(resolved)],
                "boundary": boundary.to_dict(),
                "bases": [item.to_dict() for item in _module_bases(resolved)],
                "workbench_contract": resolved.workbench_contract,
                "ui_spec": resolved.ui_spec,
                "backend_spec": resolved.backend_spec,
                "workspace_flow": [item.to_dict() for item in compose_workspace_flow(resolved)],
                "rule_validation": (
                    resolved.validation_reports.knowledge_base.to_dict()
                    if resolved.validation_reports.knowledge_base is not None
                    else {}
                ),
            },
        )
    )
    return VerificationResult(
        passed=boundary_valid and result.passed,
        reasons=[*boundary_errors, *result.reasons],
        evidence=result.evidence,
    )
