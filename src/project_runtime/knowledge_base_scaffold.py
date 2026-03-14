from __future__ import annotations

from pathlib import Path


ROOT_TEMPLATE = """# Product Spec 只回答一件事：这个产品最终应该是什么。
# 这个入口文件保留项目身份和框架来源；其余产品边界 section 默认拆到同级 `product_spec/*.toml`，
# 这样边界 token 可以点对点跳到对应文件，同时保持 `projects/<project_id>/product_spec.toml`
# 仍然是人与 AI 协作时的总入口。

[project]
project_id = "{{PROJECT_ID}}"
template = "knowledge_base_workbench"
display_name = "{{DISPLAY_NAME}}"
description = "{{DESCRIPTION}}"
version = "0.1.0"

[framework]
frontend = "framework/frontend/L2-M0-前端框架标准模块.md"
domain = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"
backend = "framework/backend/L2-M0-知识库接口框架标准模块.md"
preset = "document_chat_workbench"
"""


SURFACE_TEMPLATE = """# [surface] 描述用户看到的工作台外层形态。
[surface]
shell = "conversation_sidebar_shell"
layout_variant = "chatgpt_knowledge_client"
sidebar_width = "md"
preview_mode = "drawer"
density = "comfortable"

[surface.copy]
hero_kicker = "Framework-Compiled Product"
hero_title = "{{DISPLAY_NAME}}"
hero_copy = "一个 chat-first 的知识问答客户端，回答可以回到来源抽屉和文档详情页。"
library_title = "Knowledge Bases"
preview_title = "Citation Sources"
toc_title = "Source Sections"
chat_title = "Knowledge Chat"
empty_state_title = "Start a knowledge conversation"
empty_state_copy = "像用 ChatGPT 一样直接提问，来源在需要时再展开。"
"""


VISUAL_TEMPLATE = """# [visual] 定义视觉语义，不直接定义实现 token。
[visual]
brand = "Shelf"
accent = "#2563eb"
surface_preset = "light"
radius_scale = "xl"
shadow_level = "md"
font_scale = "md"
"""


ROUTE_TEMPLATE = """# [route] 记录页面入口和 API 命名空间的稳定路径语义。
[route]
home = "/"
workbench = "/{{ROUTE_SLUG}}"
basketball_showcase = "/{{ROUTE_SLUG}}/showcase"
knowledge_list = "/knowledge-bases"
knowledge_detail = "/knowledge-bases/details"
document_detail_prefix = "/knowledge-bases/details/documents"
api_prefix = "/api/{{API_SLUG}}"
"""


SHOWCASE_TEMPLATE = """# [showcase_page] 定义不抢占主聊天链的辅助专题页。
[showcase_page]
title = "专题展示页"
kicker = "Chat-First Special Page"
headline = "{{DISPLAY_NAME}} · 辅助专题页"
intro = "这里可以承载不打断主聊天链的辅助专题内容，用来展示前端扩展页同样属于产品真相的一部分。"
back_to_chat_label = "返回知识聊天"
browse_knowledge_label = "去知识库列表"
"""


A11Y_TEMPLATE = """# [a11y] 定义产品层可访问顺序和键盘主路径。
[a11y]
reading_order = ["conversation_sidebar", "chat_header", "message_stream", "chat_composer", "citation_drawer"]
keyboard_nav = ["new-chat", "conversation-item", "chat-input", "citation-ref", "citation-drawer-close"]
announcements = ["current knowledge base", "active conversation", "citation source opened"]
"""


LIBRARY_TEMPLATE = """# [library] 定义知识库对象在产品中的稳定身份。
[library]
knowledge_base_id = "{{PROJECT_ID}}-knowledge"
knowledge_base_name = "{{DISPLAY_NAME}} 知识库"
knowledge_base_description = "当前产品默认承载的知识库对象，用于支撑检索、引用和可追溯对话。"
enabled = true
source_types = ["markdown"]
metadata_fields = ["title", "tags", "updated_at"]
default_focus = "current_knowledge_base"
list_variant = "conversation_companion"
allow_create = true
allow_delete = true

[library.copy]
search_placeholder = "Search knowledge files and snippets"
"""


PREVIEW_TEMPLATE = """# [preview] 定义来源预览如何从用户视角工作。
[preview]
enabled = true
renderers = ["markdown"]
anchor_mode = "heading"
show_toc = true
preview_variant = "citation_drawer"
"""


CHAT_TEMPLATE = """# [chat] 定义核心对话行为与引用露出方式。
[chat]
enabled = true
citations_enabled = true
mode = "retrieval_stub"
citation_style = "inline_refs"
bubble_variant = "assistant_soft"
composer_variant = "chatgpt_compact"
system_prompt = "Answer with concise structure-first guidance grounded in the selected knowledge base and cite concrete sections."
welcome_prompts = [
  "总结这个产品的结构主链",
  "解释引用抽屉和文档详情页如何形成来源回路",
  "说明哪些改动属于框架，哪些属于产品规格，哪些属于实现配置",
]

[chat.copy]
placeholder = "询问文档、规则或方案，系统会结合知识库回答…"
welcome = "像用 ChatGPT 一样直接提问。回答会携带引用，点开后可查看来源片段和文档详情。"
"""


CONTEXT_TEMPLATE = """# [context] 定义选择、检索、引用与追问时如何持续传递上下文。
[context]
selection_mode = "knowledge_base_default"
max_citations = 3
max_preview_sections = 10
sticky_document = false
"""


RETURN_TEMPLATE = """# [return] 定义引用回路与返回语义。
[return]
enabled = true
targets = ["citation_drawer", "document_detail"]
anchor_restore = true
citation_card_variant = "chips"
"""


DOCUMENTS_TEMPLATE = '''# [[documents]] 记录种子产品内容。
[[documents]]
document_id = "product-overview"
title = "{{DISPLAY_NAME}} Overview"
summary = "Explain the product shape, primary shell, and source-traceability loop."
tags = ["product", "overview"]
updated_at = "2026-03-13"
body_markdown = """
## Product Shape
{{DISPLAY_NAME}} keeps the main experience chat-first: one conversation rail, one message stream, and one lightweight citation loop.

## Traceability
Answers should let the user reopen citations, inspect source context, and continue the same conversation.
"""

[[documents]]
document_id = "framework-relationship"
title = "Framework Relationship"
summary = "Describe how framework, product spec, implementation config, and generated code converge."
tags = ["framework", "generator"]
updated_at = "2026-03-13"
body_markdown = """
## One-Way Convergence
Framework defines the shared structure language. Product spec fixes concrete product truth. Implementation config chooses one realization path.

## Generated Runtime
Generated code and evidence should stay derivable from the same framework and project truth inputs.
"""
'''


IMPLEMENTATION_CONFIG_TEMPLATE = """# Implementation Config 只回答一件事：在不改写产品真相的前提下，
# 当前仓库准备如何把 product_spec.toml 中已经确定的产品落到一条具体实现路径上。

[frontend]
renderer = "knowledge_chat_client_v1"
style_profile = "knowledge_chat_web_v1"
script_profile = "knowledge_chat_browser_v1"

[backend]
renderer = "knowledge_chat_backend_v1"
transport = "http_json"
retrieval_strategy = "retrieval_stub"

[evidence]
product_spec_endpoint = "/api/{{API_SLUG}}/product-spec"

[artifacts]
canonical_graph_json = "canonical_graph.json"
framework_ir_json = "framework_ir.json"
product_spec_json = "product_spec.json"
implementation_bundle_py = "implementation_bundle.py"
generation_manifest_json = "generation_manifest.json"
governance_manifest_json = "governance_manifest.json"
governance_tree_json = "governance_tree.json"
strict_zone_report_json = "strict_zone_report.json"
object_coverage_report_json = "object_coverage_report.json"
"""


SECTION_TEMPLATES = (
    ("surface", SURFACE_TEMPLATE),
    ("visual", VISUAL_TEMPLATE),
    ("route", ROUTE_TEMPLATE),
    ("showcase_page", SHOWCASE_TEMPLATE),
    ("a11y", A11Y_TEMPLATE),
    ("library", LIBRARY_TEMPLATE),
    ("preview", PREVIEW_TEMPLATE),
    ("chat", CHAT_TEMPLATE),
    ("context", CONTEXT_TEMPLATE),
    ("return", RETURN_TEMPLATE),
    ("documents", DOCUMENTS_TEMPLATE),
)


def _render(template: str, replacements: dict[str, str]) -> str:
    rendered = template
    for key, value in replacements.items():
        rendered = rendered.replace(f"{{{{{key}}}}}", value)
    return rendered.strip() + "\n"


def _default_display_name(project_id: str) -> str:
    words = [item for item in project_id.replace("-", "_").split("_") if item]
    if not words:
        return "Knowledge Base Project"
    return " ".join(word.capitalize() for word in words)


def scaffold_knowledge_base_project(
    project_dir: Path,
    display_name: str | None,
    modular_product_spec: bool,
    force: bool,
) -> tuple[str, ...]:
    project_path = project_dir.resolve()
    project_id = project_path.name
    resolved_display_name = (display_name or _default_display_name(project_id)).strip()
    route_slug = project_id.replace("_", "-").strip("-") or "knowledge-base"
    api_slug = route_slug
    replacements = {
        "PROJECT_ID": project_id,
        "DISPLAY_NAME": resolved_display_name,
        "DESCRIPTION": f"{resolved_display_name} compiled from Shelf framework standards.",
        "ROUTE_SLUG": route_slug,
        "API_SLUG": api_slug,
    }

    files_to_write: list[tuple[Path, str]] = []
    if modular_product_spec:
        files_to_write.append((project_path / "product_spec.toml", _render(ROOT_TEMPLATE, replacements)))
        for section_name, template in SECTION_TEMPLATES:
            files_to_write.append(
                (
                    project_path / "product_spec" / f"{section_name}.toml",
                    _render(template, replacements),
                )
            )
    else:
        combined_parts = [_render(ROOT_TEMPLATE, replacements)]
        combined_parts.extend(_render(template, replacements) for _, template in SECTION_TEMPLATES)
        files_to_write.append((project_path / "product_spec.toml", "\n".join(part.strip() for part in combined_parts) + "\n"))

    files_to_write.append(
        (
            project_path / "implementation_config.toml",
            _render(IMPLEMENTATION_CONFIG_TEMPLATE, replacements),
        )
    )

    existing = [path for path, _ in files_to_write if path.exists()]
    if existing and not force:
        existing_rel = ", ".join(sorted(str(path.relative_to(project_path)) for path in existing))
        raise ValueError(f"project scaffold target already exists: {existing_rel}")

    written: list[str] = []
    for file_path, content in files_to_write:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        written.append(str(file_path.relative_to(project_path)))
    return tuple(written)
