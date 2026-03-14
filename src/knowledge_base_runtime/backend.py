from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re

from fastapi import APIRouter, HTTPException, Query, status
from framework_core import Base, BoundaryDefinition, BoundaryItem, Capability, VerificationInput, VerificationResult, verify
from project_runtime.knowledge_base import (
    KnowledgeBaseCodeModule,
    KnowledgeDocument,
    KnowledgeDocumentSection,
    SeedDocumentSource,
    compile_knowledge_document_source,
    load_knowledge_base_code_module,
)
from pydantic import BaseModel, Field


def _resolve_project(project: KnowledgeBaseCodeModule | None) -> KnowledgeBaseCodeModule:
    return project or load_knowledge_base_code_module()


def _require_backend_renderer(project: KnowledgeBaseCodeModule) -> str:
    implementation = project.backend_spec.get("implementation")
    if not isinstance(implementation, dict):
        raise ValueError("backend_spec.implementation is required for backend renderer selection")
    value = implementation.get("backend_renderer")
    if not isinstance(value, str):
        raise ValueError("backend_spec.implementation.backend_renderer must be a string")
    if value not in project.template_contract.supported_backend_renderers:
        raise ValueError(f"unsupported backend renderer: {value}")
    return value


def _module_capabilities(project: KnowledgeBaseCodeModule) -> tuple[Capability, ...]:
    return tuple(Capability(item.capability_id, item.statement) for item in project.backend_ir.capabilities)


def _module_boundary(project: KnowledgeBaseCodeModule) -> BoundaryDefinition:
    return BoundaryDefinition(
        items=tuple(BoundaryItem(item.boundary_id, item.statement) for item in project.backend_ir.boundaries)
    )


def _module_bases(project: KnowledgeBaseCodeModule) -> tuple[Base, ...]:
    return tuple(Base(item.base_id, item.name, item.inline_expr or item.statement) for item in project.backend_ir.bases)


KNOWLEDGE_BASE_API_CAPABILITIES = (
    Capability("C1", "稳定提供知识库列表、详情、文档列表、创建、删除、文档详情与章节锚点接口。"),
    Capability("C2", "稳定提供正文预览、章节读取、引用抽屉与文档详情所需的来源结构。"),
    Capability("C3", "稳定提供问答、行内引用、引用返回路径与文档详情跳转接口。"),
)

KNOWLEDGE_BASE_API_BOUNDARY = BoundaryDefinition(
    items=(
        BoundaryItem("LIBRARY", "知识库列表、详情、文档列表与写入入口必须统一。"),
        BoundaryItem("PREVIEW", "正文、章节和锚点接口必须返回完整来源结构。"),
        BoundaryItem("CHAT", "对话输入、回答、行内引用与来源跳转结构必须统一。"),
        BoundaryItem("RESULT", "接口返回结构必须保持稳定。"),
        BoundaryItem("AUTH", "写入类能力需由实例策略显式声明。"),
        BoundaryItem("TRACE", "请求参数、错误原因与引用来源必须可追踪。"),
    )
)

KNOWLEDGE_BASE_API_BASES = (
    Base("B1", "知识库浏览接口基", "knowledge base list + detail + document list endpoints"),
    Base("B2", "来源详情接口基", "document detail + section + citation drawer source endpoints"),
    Base("B3", "问答引用接口基", "chat turn + inline refs + return/document detail paths"),
)


class KnowledgeBaseSummaryResponse(BaseModel):
    knowledge_base_id: str
    name: str
    description: str
    document_count: int
    source_types: list[str]
    updated_at: str


class KnowledgeDocumentSummaryResponse(BaseModel):
    document_id: str
    title: str
    summary: str
    tags: list[str]
    updated_at: str
    section_count: int


class KnowledgeBaseDetailResponse(KnowledgeBaseSummaryResponse):
    documents: list[KnowledgeDocumentSummaryResponse]


class KnowledgeSectionResponse(BaseModel):
    section_id: str
    title: str
    level: int
    html: str
    plain_text: str


class KnowledgeDocumentDetailResponse(KnowledgeDocumentSummaryResponse):
    body_html: str
    sections: list[KnowledgeSectionResponse]


class KnowledgeTagItem(BaseModel):
    name: str
    count: int


class KnowledgeTagListResponse(BaseModel):
    items: list[KnowledgeTagItem]


class KnowledgeDocumentCreateRequest(BaseModel):
    document_id: str | None = None
    title: str = Field(min_length=3)
    summary: str = Field(min_length=12)
    body_markdown: str = Field(min_length=20)
    tags: list[str] = Field(default_factory=list)
    updated_at: str | None = None


class KnowledgeCitationResponse(BaseModel):
    citation_id: str
    document_id: str
    document_title: str
    section_id: str
    section_title: str
    snippet: str
    return_path: str
    document_path: str


class KnowledgeChatTurnRequest(BaseModel):
    message: str = Field(min_length=3)
    document_id: str | None = None
    section_id: str | None = None


class KnowledgeChatTurnResponse(BaseModel):
    answer: str
    citations: list[KnowledgeCitationResponse]
    context_document_id: str | None
    context_section_id: str | None


class KnowledgeDocumentDeleteResponse(BaseModel):
    document_id: str
    deleted: bool


@dataclass(frozen=True)
class RankedSection:
    document: KnowledgeDocument
    section: KnowledgeDocumentSection
    score: int


@dataclass(frozen=True)
class AnswerDraft:
    answer: str
    citations: list[KnowledgeCitationResponse]
    context_document_id: str | None
    context_section_id: str | None


def _make_document_id(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "knowledge-document"


def _document_detail_path(project: KnowledgeBaseCodeModule, document_id: str, section_id: str | None = None) -> str:
    base = project.backend_spec["return_policy"]["document_detail_path"].replace("{document_id}", document_id)
    if section_id:
        return f"{base}?section={section_id}"
    return base


class KnowledgeRepository:
    def __init__(self, project: KnowledgeBaseCodeModule | None = None) -> None:
        self.project = _resolve_project(project)
        _require_backend_renderer(self.project)
        self.backend_spec = self.project.backend_spec
        self._documents = {item.document_id: item for item in self.project.documents}
        self._document_order = [item.document_id for item in self.project.documents]

    def list_knowledge_bases(self) -> list[KnowledgeBaseSummaryResponse]:
        latest = max((item.updated_at for item in self._documents.values()), default=date.today().isoformat())
        return [
            KnowledgeBaseSummaryResponse(
                knowledge_base_id=self.project.library.knowledge_base_id,
                name=self.project.library.knowledge_base_name,
                description=self.project.library.knowledge_base_description,
                document_count=len(self._document_order),
                source_types=list(self.project.library.source_types),
                updated_at=latest,
            )
        ]

    def get_knowledge_base(self, knowledge_base_id: str) -> KnowledgeBaseDetailResponse | None:
        if knowledge_base_id != self.project.library.knowledge_base_id:
            return None
        summary = self.list_knowledge_bases()[0]
        return KnowledgeBaseDetailResponse(
            **summary.model_dump(),
            documents=[_to_document_summary(item) for item in self.list_documents()],
        )

    def list_documents(self, query: str = "", tag: str | None = None) -> list[KnowledgeDocument]:
        query_tokens = set(query.lower().split())
        tag_normalized = tag.strip().lower() if tag else None
        items: list[KnowledgeDocument] = []
        for document_id in self._document_order:
            document = self._documents[document_id]
            if tag_normalized and tag_normalized not in {item.lower() for item in document.tags}:
                continue
            if query_tokens:
                haystack = f"{document.title} {document.summary} {document.body_markdown}".lower()
                if not all(token in haystack for token in query_tokens):
                    continue
            items.append(document)
        return items

    def get_document(self, document_id: str) -> KnowledgeDocument | None:
        return self._documents.get(document_id)

    def get_section(self, document_id: str, section_id: str) -> KnowledgeDocumentSection | None:
        document = self.get_document(document_id)
        if document is None:
            return None
        for section in document.sections:
            if section.section_id == section_id:
                return section
        return None

    def list_tags(self) -> list[KnowledgeTagItem]:
        counts: dict[str, int] = {}
        for document_id in self._document_order:
            document = self._documents[document_id]
            for tag in document.tags:
                counts[tag] = counts.get(tag, 0) + 1
        return [KnowledgeTagItem(name=name, count=count) for name, count in sorted(counts.items())]

    def create_document(self, payload: KnowledgeDocumentCreateRequest) -> KnowledgeDocument:
        if not self.project.library.allow_create:
            raise ValueError("document creation is disabled by the current product settings")
        document_id = payload.document_id or _make_document_id(payload.title)
        if document_id in self._documents:
            raise ValueError(f"document_id already exists: {document_id}")
        normalized_tags = [item.strip() for item in payload.tags if item.strip()]
        source = SeedDocumentSource(
            document_id=document_id,
            title=payload.title.strip(),
            summary=payload.summary.strip(),
            body_markdown=payload.body_markdown.strip(),
            tags=tuple(normalized_tags),
            updated_at=payload.updated_at or date.today().isoformat(),
        )
        document = compile_knowledge_document_source(source)
        self._documents[document.document_id] = document
        self._document_order.insert(0, document.document_id)
        return document

    def delete_document(self, document_id: str) -> None:
        if not self.project.library.allow_delete:
            raise ValueError("document deletion is disabled by the current product settings")
        if document_id not in self._documents:
            raise KeyError(document_id)
        del self._documents[document_id]
        self._document_order = [item for item in self._document_order if item != document_id]

    # @governed_symbol id=kb.answer.behavior owner=product_spec kind=answer_behavior risk=high
    def answer_question(
        self,
        message: str,
        document_id: str | None = None,
        section_id: str | None = None,
    ) -> KnowledgeChatTurnResponse:
        retrieval = self.backend_spec["retrieval"]
        ranked = self._rank_sections(message, document_id=document_id, section_id=section_id)
        citations = self._build_citations(
            ranked[: retrieval["max_citations"]],
        )
        answer_draft = self._build_answer_draft(
            citations,
            fallback_document_id=document_id,
            fallback_section_id=section_id,
        )
        return KnowledgeChatTurnResponse(
            answer=answer_draft.answer,
            citations=answer_draft.citations,
            context_document_id=answer_draft.context_document_id,
            context_section_id=answer_draft.context_section_id,
        )

    def _rank_sections(
        self,
        message: str,
        document_id: str | None = None,
        section_id: str | None = None,
    ) -> list[RankedSection]:
        retrieval = self.backend_spec["retrieval"]
        strategy = retrieval["strategy"]
        if strategy == self.project.template_contract.required_chat_mode:
            return self._rank_sections_stub(message, document_id=document_id, section_id=section_id)
        raise ValueError(f"unsupported backend retrieval strategy: {strategy}")

    def _rank_sections_stub(
        self,
        message: str,
        document_id: str | None = None,
        section_id: str | None = None,
    ) -> list[RankedSection]:
        retrieval = self.backend_spec["retrieval"]
        query_tokens = {
            token for token in message.lower().split() if len(token) >= retrieval["query_token_min_length"]
        }
        if not query_tokens:
            return []

        documents = self._rankable_documents(document_id)
        if not documents:
            return []

        ranked: list[RankedSection] = []
        for document in documents:
            for section in document.sections[: retrieval["max_preview_sections"]]:
                score = self._section_match_score(
                    document,
                    section,
                    query_tokens=query_tokens,
                    document_id=document_id,
                    section_id=section_id,
                )
                if score == 0:
                    continue
                ranked.append(RankedSection(document=document, section=section, score=score))
        ranked.sort(key=lambda item: (-item.score, item.document.title, item.section.title))
        return ranked

    def _build_citations(self, ranked_sections: list[RankedSection]) -> list[KnowledgeCitationResponse]:
        return [
            KnowledgeCitationResponse(
                citation_id=str(index),
                document_id=item.document.document_id,
                document_title=item.document.title,
                section_id=item.section.section_id,
                section_title=item.section.title,
                snippet=item.section.plain_text[:220],
                return_path=(
                    f"{self.backend_spec['return_policy']['chat_path']}?document={item.document.document_id}"
                    f"&section={item.section.section_id}&citation={index}"
                ),
                document_path=_document_detail_path(
                    self.project,
                    item.document.document_id,
                    item.section.section_id,
                ),
            )
            for index, item in enumerate(ranked_sections, start=1)
        ]

    def _build_answer_draft(
        self,
        citations: list[KnowledgeCitationResponse],
        *,
        fallback_document_id: str | None,
        fallback_section_id: str | None,
    ) -> AnswerDraft:
        answer_policy = self.backend_spec["answer_policy"]
        if not citations:
            return AnswerDraft(
                answer=answer_policy["no_match_text"],
                citations=citations,
                context_document_id=fallback_document_id,
                context_section_id=fallback_section_id,
            )

        lead = citations[0]
        answer_parts = [
            answer_policy["lead_template"].format(
                document_title=lead.document_title,
                section_title=lead.section_title,
                citation_index=1,
            ),
            answer_policy["lead_snippet_template"].format(snippet=lead.snippet),
        ]
        for index, citation in enumerate(citations[1:], start=2):
            answer_parts.append(
                answer_policy["followup_template"].format(
                    document_title=citation.document_title,
                    section_title=citation.section_title,
                    citation_index=index,
                    snippet=citation.snippet,
                )
            )
        answer_parts.append(answer_policy["closing_text"])
        return AnswerDraft(
            answer="\n\n".join(answer_parts),
            citations=citations,
            context_document_id=lead.document_id,
            context_section_id=lead.section_id,
        )

    def _rankable_documents(self, document_id: str | None) -> tuple[KnowledgeDocument, ...]:
        if document_id is None:
            return tuple(self._documents[item] for item in self._document_order)
        focused = self.get_document(document_id)
        if focused is None:
            return ()
        return (focused,)

    def _section_match_score(
        self,
        document: KnowledgeDocument,
        section: KnowledgeDocumentSection,
        *,
        query_tokens: set[str],
        document_id: str | None,
        section_id: str | None,
    ) -> int:
        retrieval = self.backend_spec["retrieval"]
        score = 0
        if section_id and document.document_id == document_id and section.section_id == section_id:
            score += retrieval["focus_section_bonus"]
        haystack = f"{document.title} {document.summary} {section.search_text}".lower()
        for token in query_tokens:
            if token in haystack:
                score += retrieval["token_match_bonus"]
        return score


def _to_document_summary(document: KnowledgeDocument) -> KnowledgeDocumentSummaryResponse:
    return KnowledgeDocumentSummaryResponse(
        document_id=document.document_id,
        title=document.title,
        summary=document.summary,
        tags=list(document.tags),
        updated_at=document.updated_at,
        section_count=len(document.sections),
    )


def _to_document_detail(document: KnowledgeDocument) -> KnowledgeDocumentDetailResponse:
    return KnowledgeDocumentDetailResponse(
        **_to_document_summary(document).model_dump(),
        body_html=document.body_html,
        sections=[
            KnowledgeSectionResponse(
                section_id=section.section_id,
                title=section.title,
                level=section.level,
                html=section.html,
                plain_text=section.plain_text,
            )
            for section in document.sections
        ],
    )


def verify_knowledge_base_backend(project: KnowledgeBaseCodeModule | None = None) -> VerificationResult:
    resolved = _resolve_project(project)
    boundary = _module_boundary(resolved)
    boundary_valid, boundary_errors = boundary.validate()
    result = verify(
        VerificationInput(
            subject="knowledge base backend",
            pass_criteria=[
                "knowledge base list/detail, document list/detail, section, tag, create, delete, and chat endpoints all exist",
                "chat answers cite concrete sections and expose drawer plus document detail paths",
                "product spec endpoint exposes compiled product truth",
            ],
            evidence={
                "project": resolved.public_summary,
                "capabilities": [item.to_dict() for item in _module_capabilities(resolved)],
                "boundary": boundary.to_dict(),
                "bases": [item.to_dict() for item in _module_bases(resolved)],
                "routes": resolved.to_spec_dict()["routes"]["api"],
                "backend_spec": resolved.backend_spec,
                "upload_enabled": resolved.features.upload,
            },
        )
    )
    return VerificationResult(
        passed=boundary_valid and result.passed,
        reasons=[*boundary_errors, *result.reasons],
        evidence=result.evidence,
    )


def build_knowledge_base_router(
    project: KnowledgeBaseCodeModule | None = None,
    repository: KnowledgeRepository | None = None,
) -> APIRouter:
    resolved = _resolve_project(project)
    _require_backend_renderer(resolved)
    repo = repository or KnowledgeRepository(resolved)
    router = APIRouter(prefix=resolved.route.api_prefix, tags=[resolved.metadata.project_id])

    # @governed_symbol id=kb.api.library_contracts owner=framework kind=api_contract risk=high
    @router.get("/knowledge-bases", response_model=list[KnowledgeBaseSummaryResponse])
    def list_knowledge_bases() -> list[KnowledgeBaseSummaryResponse]:
        return repo.list_knowledge_bases()

    # @governed_symbol id=kb.api.library_contracts owner=framework kind=api_contract risk=high
    @router.get("/knowledge-bases/{knowledge_base_id}", response_model=KnowledgeBaseDetailResponse)
    def get_knowledge_base(knowledge_base_id: str) -> KnowledgeBaseDetailResponse:
        knowledge_base = repo.get_knowledge_base(knowledge_base_id)
        if knowledge_base is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found")
        return knowledge_base

    # @governed_symbol id=kb.api.library_contracts owner=framework kind=api_contract risk=high
    @router.get("/documents", response_model=list[KnowledgeDocumentSummaryResponse])
    def list_documents(
        query: str = "",
        tag: str | None = Query(default=None),
    ) -> list[KnowledgeDocumentSummaryResponse]:
        return [_to_document_summary(item) for item in repo.list_documents(query=query, tag=tag)]

    # @governed_symbol id=kb.api.library_contracts owner=framework kind=api_contract risk=high
    @router.post("/documents", response_model=KnowledgeDocumentDetailResponse, status_code=status.HTTP_201_CREATED)
    def create_document(payload: KnowledgeDocumentCreateRequest) -> KnowledgeDocumentDetailResponse:
        try:
            document = repo.create_document(payload)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return _to_document_detail(document)

    # @governed_symbol id=kb.api.library_contracts owner=framework kind=api_contract risk=high
    @router.get("/documents/{document_id}", response_model=KnowledgeDocumentDetailResponse)
    def get_document(document_id: str) -> KnowledgeDocumentDetailResponse:
        document = repo.get_document(document_id)
        if document is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        return _to_document_detail(document)

    # @governed_symbol id=kb.api.library_contracts owner=framework kind=api_contract risk=high
    @router.get("/documents/{document_id}/sections/{section_id}", response_model=KnowledgeSectionResponse)
    def get_section(document_id: str, section_id: str) -> KnowledgeSectionResponse:
        section = repo.get_section(document_id, section_id)
        if section is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
        return KnowledgeSectionResponse(
            section_id=section.section_id,
            title=section.title,
            level=section.level,
            html=section.html,
            plain_text=section.plain_text,
        )

    # @governed_symbol id=kb.api.library_contracts owner=framework kind=api_contract risk=high
    @router.delete("/documents/{document_id}", response_model=KnowledgeDocumentDeleteResponse)
    def delete_document(document_id: str) -> KnowledgeDocumentDeleteResponse:
        try:
            repo.delete_document(document_id)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found") from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        return KnowledgeDocumentDeleteResponse(document_id=document_id, deleted=True)

    # @governed_symbol id=kb.api.library_contracts owner=framework kind=api_contract risk=high
    @router.get("/tags", response_model=KnowledgeTagListResponse)
    def list_tags() -> KnowledgeTagListResponse:
        return KnowledgeTagListResponse(items=repo.list_tags())

    # @governed_symbol id=kb.api.chat_contract owner=framework kind=api_contract risk=high
    @router.post("/chat/turns", response_model=KnowledgeChatTurnResponse)
    def create_chat_turn(payload: KnowledgeChatTurnRequest) -> KnowledgeChatTurnResponse:
        return repo.answer_question(
            payload.message,
            document_id=payload.document_id,
            section_id=payload.section_id,
        )

    return router
