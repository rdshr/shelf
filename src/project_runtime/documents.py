from __future__ import annotations

from html import escape
import re
from typing import Any

from project_runtime.models import KnowledgeDocument, KnowledgeDocumentSection, SeedDocumentSource
from project_runtime.utils import slugify


def render_markdown(markdown: str) -> str:
    lines = markdown.strip().splitlines()
    html_parts: list[str] = []
    in_list = False
    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            continue
        if stripped.startswith("### "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f"<h4>{escape(stripped[4:])}</h4>")
            continue
        if stripped.startswith("## "):
            if in_list:
                html_parts.append("</ul>")
                in_list = False
            html_parts.append(f"<h3>{escape(stripped[3:])}</h3>")
            continue
        if stripped.startswith("- "):
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{escape(stripped[2:])}</li>")
            continue
        if in_list:
            html_parts.append("</ul>")
            in_list = False
        html_parts.append(f"<p>{escape(stripped)}</p>")
    if in_list:
        html_parts.append("</ul>")
    return "\n".join(html_parts)


def plain_text(markdown: str) -> str:
    text = re.sub(r"^#{2,3}\s+", "", markdown, flags=re.MULTILINE)
    text = re.sub(r"^-\s+", "", text, flags=re.MULTILINE)
    return " ".join(part.strip() for part in text.splitlines() if part.strip())


def split_markdown_sections(summary: str, body_markdown: str) -> tuple[KnowledgeDocumentSection, ...]:
    sections: list[KnowledgeDocumentSection] = [
        KnowledgeDocumentSection(
            section_id="summary",
            title="Summary",
            level=2,
            markdown=summary.strip(),
            html=render_markdown(summary.strip()),
            plain_text=plain_text(summary.strip()),
            search_text=f"summary {summary.strip()}",
        )
    ]
    seen_ids = {"summary"}
    current_title = "Overview"
    current_level = 2
    current_lines: list[str] = []
    saw_heading = False

    def flush() -> None:
        nonlocal current_title, current_level, current_lines
        content = "\n".join(current_lines).strip()
        if not content:
            current_lines = []
            return
        section_id = slugify(current_title)
        counter = 2
        while section_id in seen_ids:
            section_id = f"{section_id}-{counter}"
            counter += 1
        seen_ids.add(section_id)
        section_plain_text = plain_text(content)
        sections.append(
            KnowledgeDocumentSection(
                section_id=section_id,
                title=current_title,
                level=current_level,
                markdown=content,
                html=render_markdown(content),
                plain_text=section_plain_text,
                search_text=f"{current_title} {section_plain_text}",
            )
        )
        current_lines = []

    for raw_line in body_markdown.strip().splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("## "):
            saw_heading = True
            flush()
            current_title = stripped[3:].strip()
            current_level = 2
            continue
        if stripped.startswith("### "):
            saw_heading = True
            flush()
            current_title = stripped[4:].strip()
            current_level = 3
            continue
        current_lines.append(raw_line)

    if not saw_heading and body_markdown.strip():
        current_title = "Overview"
        current_level = 2
    flush()
    return tuple(sections)


def compile_knowledge_document_source(source: SeedDocumentSource) -> KnowledgeDocument:
    sections = split_markdown_sections(source.summary, source.body_markdown)
    body_html = "\n".join(
        (
            f"<section id=\"{escape(item.section_id)}\" "
            f"data-level=\"{item.level}\"><h3>{escape(item.title)}</h3>{item.html}</section>"
        )
        for item in sections
    )
    return KnowledgeDocument(
        document_id=source.document_id,
        title=source.title,
        summary=source.summary,
        body_markdown=source.body_markdown,
        body_html=body_html,
        tags=source.tags,
        updated_at=source.updated_at,
        sections=sections,
    )


def export_documents(sources: tuple[SeedDocumentSource, ...]) -> list[dict[str, Any]]:
    return [compile_knowledge_document_source(item).to_dict() for item in sources]
