from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import TYPE_CHECKING, Any

from fastapi import HTTPException
from knowledge_base_runtime.frontend_script import build_chat_script
from knowledge_base_runtime.runtime_profile import load_knowledge_base_runtime_profile
from knowledge_base_runtime.frontend_style import build_shared_style
from knowledge_base_runtime.runtime_exports import resolve_frontend_app_spec, resolve_knowledge_base_domain_spec
from project_runtime import (
    KnowledgeDocument,
    ProjectRuntimeAssembly,
    load_project_runtime,
)

if TYPE_CHECKING:
    from knowledge_base_runtime.backend import KnowledgeBaseDetailResponse, KnowledgeRepository


@dataclass(frozen=True)
class NavLinkSpec:
    key: str
    href: str
    label: str


@dataclass(frozen=True)
class AuxPageSpec:
    active_nav: str
    title: str
    subtitle: str
    actions: tuple[NavLinkSpec, ...]
    content_html: str


def _resolve_project(
    project: ProjectRuntimeAssembly | None,
) -> ProjectRuntimeAssembly:
    return project or load_project_runtime()


def _frontend_app_spec(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    return dict(resolve_frontend_app_spec(project))


def _frontend_ui(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    value = _frontend_app_spec(project)["ui"]
    if not isinstance(value, dict):
        raise ValueError("frontend_app_spec.ui must be a dict")
    return dict(value)


def _workbench(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    value = resolve_knowledge_base_domain_spec(project).get("workbench")
    if not isinstance(value, dict):
        raise ValueError("knowledge_base_domain_spec.workbench must be a dict")
    return dict(value)


def _library(project: ProjectRuntimeAssembly) -> dict[str, Any]:
    value = _workbench(project).get("library")
    if not isinstance(value, dict):
        raise ValueError("knowledge_base_domain_spec.workbench.library must be a dict")
    return dict(value)


def _copy(project: ProjectRuntimeAssembly) -> dict[str, str]:
    copy = _frontend_app_spec(project)["copy"]  # type: ignore[index]
    if not isinstance(copy, dict):
        raise ValueError("frontend_app_spec.copy must be a dict")
    return {str(key): str(value) for key, value in copy.items()}


def _require_frontend_renderer(project: ProjectRuntimeAssembly) -> str:
    implementation = _frontend_ui(project).get("implementation")
    if not isinstance(implementation, dict):
        raise ValueError("frontend_app_spec.ui.implementation is required for frontend renderer selection")
    value = implementation.get("frontend_renderer")
    if not isinstance(value, str):
        raise ValueError("frontend_app_spec.ui.implementation.frontend_renderer must be a string")
    if value not in load_knowledge_base_runtime_profile().supported_frontend_renderers:
        raise ValueError(f"unsupported frontend renderer: {value}")
    return value


def _shared_style(project: ProjectRuntimeAssembly) -> str:
    _require_frontend_renderer(project)
    return build_shared_style(project)


def _ghost_link(href: str, label: str) -> str:
    return f'<a class="ghost-link" href="{escape(href)}">{escape(label)}</a>'


def _chip(text: str) -> str:
    return f'<span class="chip">{escape(text)}</span>'


def _chip_list(items: tuple[str, ...] | list[str]) -> str:
    return "".join(_chip(item) for item in items)


def _aux_sidebar(project: ProjectRuntimeAssembly, active: str) -> str:
    frontend_ui = _frontend_ui(project)
    library = _library(project)
    aux_sidebar = frontend_ui["components"]["aux_sidebar"]
    knowledge_detail_href = frontend_ui["pages"]["knowledge_detail"]["path"].replace(
        "{knowledge_base_id}",
        str(library["knowledge_base_id"]),
    )
    items = (
        NavLinkSpec("chat", frontend_ui["pages"]["chat_home"]["path"], aux_sidebar["nav"]["chat"]),
        NavLinkSpec(
            "basketball-showcase",
            frontend_ui["pages"]["basketball_showcase"]["path"],
            aux_sidebar["nav"]["basketball_showcase"],
        ),
        NavLinkSpec("knowledge-list", frontend_ui["pages"]["knowledge_list"]["path"], aux_sidebar["nav"]["knowledge_list"]),
        NavLinkSpec("knowledge-detail", knowledge_detail_href, aux_sidebar["nav"]["knowledge_detail"]),
    )
    links = []
    for item in items:
        class_name = "active" if item.key == active else ""
        links.append(f'<a class="{class_name}" href="{escape(item.href)}">{escape(item.label)}</a>')
    copy = _copy(project)
    return f"""
    <aside class="aux-sidebar">
      <div>
        <span class="eyebrow">{escape(copy["hero_kicker"])}</span>
        <h1>{escape(project.metadata.display_name)}</h1>
        <p>{escape(str(library["knowledge_base_description"]))}</p>
      </div>
      <nav class="aux-nav">
        {''.join(links)}
      </nav>
      <div class="page-note">{escape(aux_sidebar["note"])}</div>
    </aside>
    """


def _render_page(title: str, style: str, body: str) -> str:
    return f"""
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(title)}</title>
    <style>{style}</style>
  </head>
  <body>
    {body}
  </body>
</html>
"""


def _render_aux_page(project: ProjectRuntimeAssembly, *, style: str, page: AuxPageSpec) -> str:
    header_actions = "".join(_ghost_link(item.href, item.label) for item in page.actions)
    body = f"""
    <div class="aux-shell">
      {_aux_sidebar(project, page.active_nav)}
      <main class="aux-main">
        <header class="aux-header">
          <div class="header-copy">
            <div class="header-title">{escape(page.title)}</div>
            <div class="header-subtitle">{escape(page.subtitle)}</div>
          </div>
          <div class="header-actions">
            {header_actions}
          </div>
        </header>
        <section class="aux-content">
          {page.content_html}
        </section>
      </main>
    </div>
    """
    return _render_page(page.title, style, body)


def compose_basketball_showcase_page(project: ProjectRuntimeAssembly) -> str:
    style = (
        _shared_style(project)
        + """
    .showcase-stage {
      position: relative;
      overflow: hidden;
      border-radius: 28px;
      padding: 32px;
      min-height: 420px;
      background:
        radial-gradient(circle at top left, rgba(255, 205, 96, 0.45), transparent 26%),
        radial-gradient(circle at right 20%, rgba(255, 120, 64, 0.35), transparent 24%),
        linear-gradient(140deg, rgba(15, 23, 42, 0.95), rgba(28, 28, 44, 0.96));
      box-shadow: 0 28px 64px rgba(15, 23, 42, 0.22);
      color: #f8fafc;
    }
    .showcase-stage::before {
      content: "";
      position: absolute;
      inset: 18px;
      border: 1px solid rgba(248, 250, 252, 0.16);
      border-radius: 22px;
      pointer-events: none;
    }
    .showcase-kicker {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px 14px;
      border-radius: 999px;
      background: rgba(248, 250, 252, 0.1);
      font-size: 13px;
      letter-spacing: 0.12em;
      text-transform: uppercase;
    }
    .showcase-grid {
      position: relative;
      z-index: 1;
      display: grid;
      gap: 24px;
      grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.8fr);
      margin-top: 24px;
    }
    .showcase-copy h2 {
      margin: 0;
      font-size: clamp(38px, 6vw, 72px);
      line-height: 0.94;
      letter-spacing: -0.05em;
    }
    .showcase-copy p {
      max-width: 40rem;
      margin: 18px 0 0;
      color: rgba(248, 250, 252, 0.82);
      line-height: 1.7;
    }
    .showcase-metrics {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
      margin-top: 24px;
    }
    .showcase-metric {
      padding: 16px;
      border-radius: 18px;
      background: rgba(248, 250, 252, 0.08);
      border: 1px solid rgba(248, 250, 252, 0.08);
    }
    .showcase-metric strong {
      display: block;
      font-size: 20px;
      line-height: 1.1;
    }
    .showcase-court {
      position: relative;
      min-height: 300px;
      border-radius: 24px;
      background:
        radial-gradient(circle at 50% 18%, rgba(255, 255, 255, 0.12), transparent 18%),
        linear-gradient(180deg, rgba(255, 168, 76, 0.2), rgba(255, 119, 48, 0.08)),
        rgba(12, 18, 32, 0.78);
      border: 1px solid rgba(248, 250, 252, 0.12);
    }
    .showcase-court::before,
    .showcase-court::after {
      content: "";
      position: absolute;
      inset: 18px;
      border: 2px solid rgba(248, 250, 252, 0.18);
      border-radius: 20px;
    }
    .showcase-court::after {
      inset: 50% 18px auto;
      height: 0;
      border-width: 0 0 2px;
      border-radius: 0;
    }
    .showcase-ball {
      position: absolute;
      right: 20%;
      top: 18%;
      width: 86px;
      height: 86px;
      border-radius: 50%;
      background:
        radial-gradient(circle at 28% 28%, rgba(255, 248, 220, 0.7), transparent 18%),
        linear-gradient(145deg, #ffb347, #ff6b35);
      box-shadow: 0 16px 40px rgba(255, 107, 53, 0.35);
      animation: float-ball 2.8s ease-in-out infinite;
    }
    .showcase-ball::before,
    .showcase-ball::after {
      content: "";
      position: absolute;
      inset: 0;
      border-radius: 50%;
      border: 2px solid rgba(47, 24, 10, 0.45);
    }
    .showcase-ball::after {
      inset: 12px 40px;
      border-left: 0;
      border-right: 0;
    }
    .showcase-player {
      position: absolute;
      left: 18%;
      bottom: 12%;
      width: 160px;
      height: 220px;
    }
    .showcase-player .head,
    .showcase-player .torso,
    .showcase-player .arm,
    .showcase-player .leg {
      position: absolute;
      background: #f8fafc;
      transform-origin: top center;
    }
    .showcase-player .head {
      left: 56px;
      top: 6px;
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: linear-gradient(180deg, #f8fafc, #d8e4f7);
    }
    .showcase-player .torso {
      left: 58px;
      top: 40px;
      width: 34px;
      height: 82px;
      border-radius: 18px;
      transform: skew(-10deg);
      background: linear-gradient(180deg, #f97316, #fb7185);
    }
    .showcase-player .arm {
      width: 18px;
      height: 92px;
      border-radius: 999px;
      background: linear-gradient(180deg, #f8fafc, #cbd5f5);
    }
    .showcase-player .arm.left {
      left: 48px;
      top: 50px;
      transform: rotate(48deg);
    }
    .showcase-player .arm.right {
      left: 92px;
      top: 48px;
      transform: rotate(-44deg);
    }
    .showcase-player .leg {
      width: 18px;
      height: 102px;
      border-radius: 999px;
      background: linear-gradient(180deg, #f8fafc, #cbd5f5);
      top: 112px;
    }
    .showcase-player .leg.left {
      left: 58px;
      transform: rotate(16deg);
    }
    .showcase-player .leg.right {
      left: 88px;
      transform: rotate(-20deg);
    }
    .showcase-cta {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 26px;
    }
    .showcase-cta a {
      text-decoration: none;
    }
    .showcase-note {
      margin-top: 18px;
      color: rgba(248, 250, 252, 0.72);
      font-size: 14px;
      line-height: 1.6;
    }
    @keyframes float-ball {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-16px); }
    }
    @media (max-width: 900px) {
      .showcase-grid {
        grid-template-columns: 1fr;
      }
      .showcase-metrics {
        grid-template-columns: 1fr;
      }
    }
    """
    )
    frontend_ui = _frontend_ui(project)
    page_spec = frontend_ui["pages"]["basketball_showcase"]
    showcase_content = f"""
    <article class="showcase-stage">
      <span class="showcase-kicker">{escape(page_spec['kicker'])}</span>
      <div class="showcase-grid">
        <div class="showcase-copy">
          <h2>{escape(page_spec['headline'])}</h2>
          <p>{escape(page_spec['intro'])}</p>
          <div class="showcase-metrics">
            <div class="showcase-metric">
              <strong>前端扩展页</strong>
              <span>不离开知识库工作台，也能挂一个独立专题页。</span>
            </div>
            <div class="showcase-metric">
              <strong>证据树可追踪</strong>
              <span>路由、surface contract、ui spec 会一起收敛，不是树外彩蛋。</span>
            </div>
            <div class="showcase-metric">
              <strong>视觉可变体</strong>
              <span>主界面保持知识问答秩序，专题页允许更强的视觉表达。</span>
            </div>
          </div>
          <div class="showcase-cta">
            {_ghost_link(frontend_ui['pages']['chat_home']['path'], page_spec['back_to_chat_label'])}
            {_ghost_link(frontend_ui['pages']['knowledge_list']['path'], page_spec['browse_knowledge_label'])}
          </div>
          <div class="showcase-note">页面主题是“蔡徐坤打球”，这里把它做成一个纯前端视觉专题，用来验证知识库产品也能承接轻量扩展场景。</div>
        </div>
        <div class="showcase-court" aria-hidden="true">
          <div class="showcase-ball"></div>
          <div class="showcase-player">
            <div class="head"></div>
            <div class="torso"></div>
            <div class="arm left"></div>
            <div class="arm right"></div>
            <div class="leg left"></div>
            <div class="leg right"></div>
          </div>
        </div>
      </div>
    </article>
    """
    return _render_aux_page(
        project,
        style=style,
        page=AuxPageSpec(
            active_nav="basketball-showcase",
            title=page_spec["title"],
            subtitle=page_spec["intro"],
            actions=(
                NavLinkSpec("chat", frontend_ui["pages"]["chat_home"]["path"], page_spec["back_to_chat_label"]),
                NavLinkSpec(
                    "knowledge-list",
                    frontend_ui["pages"]["knowledge_list"]["path"],
                    page_spec["browse_knowledge_label"],
                ),
            ),
            content_html=showcase_content,
        ),
    )


def compose_knowledge_base_list_page(project: ProjectRuntimeAssembly, repository: "KnowledgeRepository") -> str:
    style = _shared_style(project)
    frontend_ui = _frontend_ui(project)
    page_spec = frontend_ui["pages"]["knowledge_list"]
    knowledge_bases = repository.list_knowledge_bases()
    cards = []
    for item in knowledge_bases:
        detail_href = frontend_ui["pages"]["knowledge_detail"]["path"].replace("{knowledge_base_id}", item.knowledge_base_id)
        cards.append(
            f"""
            <article class="kb-card">
              <h3>{escape(item.name)}</h3>
              <p>{escape(item.description)}</p>
              <div class="card-meta">
                <span class="meta-chip">{item.document_count} documents</span>
                <span class="meta-chip">{escape(item.updated_at)}</span>
              </div>
              <div class="card-meta">
                <a class="ghost-link" href="{escape(frontend_ui['pages']['chat_home']['path'])}">{escape(page_spec['chat_action_label'])}</a>
                <a class="ghost-link" href="{escape(detail_href)}">{escape(page_spec['detail_action_label'])}</a>
              </div>
            </article>
            """
        )
    content_html = f"""
    <div class="page-card">
      <h2>{escape(page_spec['rationale_title'])}</h2>
      <p>{escape(page_spec['rationale_copy'])}</p>
    </div>
    <div class="page-grid">
      {''.join(cards)}
    </div>
    """
    return _render_aux_page(
        project,
        style=style,
        page=AuxPageSpec(
            active_nav="knowledge-list",
            title=page_spec["title"],
            subtitle=page_spec["subtitle"],
            actions=(NavLinkSpec("chat", frontend_ui["pages"]["chat_home"]["path"], page_spec["primary_action_label"]),),
            content_html=content_html,
        ),
    )


def compose_knowledge_base_detail_page(
    project: ProjectRuntimeAssembly,
    knowledge_base: "KnowledgeBaseDetailResponse",
) -> str:
    style = _shared_style(project)
    frontend_ui = _frontend_ui(project)
    page_spec = frontend_ui["pages"]["knowledge_detail"]
    cards = []
    for document in knowledge_base.documents:
        detail_href = frontend_ui["pages"]["document_detail"]["path"].replace("{document_id}", document.document_id)
        cards.append(
            f"""
            <article class="doc-card">
              <h3>{escape(document.title)}</h3>
              <p>{escape(document.summary)}</p>
              <div class="chip-row">
                {''.join(f'<span class="chip">{escape(tag)}</span>' for tag in document.tags)}
                <span class="chip">{escape(document.updated_at)}</span>
                <span class="chip">{document.section_count} sections</span>
              </div>
              <div class="card-meta">
                <a class="ghost-link" href="{escape(frontend_ui['pages']['chat_home']['path'])}?document={escape(document.document_id)}">{escape(page_spec['return_chat_with_document_label'])}</a>
                <a class="ghost-link" href="{escape(detail_href)}">{escape(page_spec['document_detail_action_label'])}</a>
              </div>
            </article>
            """
        )
    content_html = f"""
    <div class="page-card">
      <h2>{escape(page_spec['overview_title'])}</h2>
      <div class="chip-row">
        {_chip(str(knowledge_base.document_count) + ' documents')}
        {_chip(knowledge_base.updated_at)}
        {_chip_list(list(knowledge_base.source_types))}
      </div>
    </div>
    <div class="stack">
      {''.join(cards)}
    </div>
    """
    return _render_aux_page(
        project,
        style=style,
        page=AuxPageSpec(
            active_nav="knowledge-detail",
            title=knowledge_base.name,
            subtitle=knowledge_base.description,
            actions=(NavLinkSpec("chat", frontend_ui["pages"]["chat_home"]["path"], page_spec["chat_action_label"]),),
            content_html=content_html,
        ),
    )


def compose_document_detail_page(
    project: ProjectRuntimeAssembly,
    document: KnowledgeDocument,
    active_section_id: str | None = None,
) -> str:
    style = _shared_style(project)
    frontend_ui = _frontend_ui(project)
    page_spec = frontend_ui["pages"]["document_detail"]
    sections = []
    for section in document.sections:
        class_name = "document-section active" if section.section_id == active_section_id else "document-section"
        sections.append(
            f"""
            <section id="{escape(section.section_id)}" class="{class_name}">
              <h3>{escape(section.title)}</h3>
              {section.html}
            </section>
            """
        )
    content_html = f"""
    <article class="document-header">
      <h2>{escape(document.title)}</h2>
      <p>{escape(document.summary)}</p>
      <div class="chip-row">
        {_chip_list(list(document.tags))}
        {_chip(document.updated_at)}
      </div>
    </article>
    <div class="stack">
      {''.join(sections)}
    </div>
    """
    return _render_aux_page(
        project,
        style=style,
        page=AuxPageSpec(
            active_nav="knowledge-detail",
            title=page_spec["title"],
            subtitle=page_spec["subtitle"],
            actions=(
                NavLinkSpec(
                    "chat",
                    f"{frontend_ui['pages']['chat_home']['path']}?document={escape(document.document_id)}",
                    page_spec["return_chat_label"],
                ),
                NavLinkSpec(
                    "knowledge-detail",
                    frontend_ui["pages"]["knowledge_detail"]["path"].replace(
                        "{knowledge_base_id}",
                        str(_library(project)["knowledge_base_id"]),
                    ),
                    page_spec["return_knowledge_detail_label"],
                ),
            ),
            content_html=content_html,
        ),
    )


def _chat_script(project: ProjectRuntimeAssembly) -> str:
    _require_frontend_renderer(project)
    return build_chat_script(project)


def compose_knowledge_base_page(
    project: ProjectRuntimeAssembly | None = None,
) -> str:
    resolved = _resolve_project(project)
    frontend_ui = _frontend_ui(resolved)
    library = _library(resolved)
    sidebar_spec = frontend_ui["components"]["conversation_sidebar"]
    header_spec = frontend_ui["components"]["chat_header"]
    composer_spec = frontend_ui["components"]["chat_composer"]
    drawer_spec = frontend_ui["components"]["citation_drawer"]
    switch_dialog_spec = frontend_ui["components"]["knowledge_switch_dialog"]
    conversation_spec = frontend_ui["conversation"]
    style = _shared_style(resolved)
    copy = _copy(resolved)
    body = f"""
    <div class="chat-shell">
      <aside class="conversation-sidebar">
        <section class="sidebar-brand">
          <span class="eyebrow">{escape(copy["hero_kicker"])}</span>
          <h1>{escape(copy["hero_title"])}</h1>
          <p>{escape(copy["hero_copy"])}</p>
        </section>

        <button class="sidebar-primary-btn" id="new-chat" type="button">+ {escape(sidebar_spec["new_chat_label"])}</button>

        <section class="sidebar-section">
          <div class="sidebar-label">{escape(sidebar_spec["title"])}</div>
          <div class="conversation-groups" id="conversation-groups"></div>
        </section>

        <section class="sidebar-footer">
          <button class="sidebar-primary-btn" type="button" data-open-knowledge-switch="true" id="knowledge-badge"></button>
          <a class="secondary-link" href="{escape(frontend_ui['pages']['knowledge_list']['path'])}">{escape(sidebar_spec['browse_knowledge_label'])}</a>
          <a class="secondary-link" href="{escape(frontend_ui['pages']['basketball_showcase']['path'])}">{escape(sidebar_spec['basketball_showcase_label'])}</a>
        </section>
      </aside>

      <main class="chat-main">
        <header class="chat-header" id="chat-header">
          <div class="header-copy">
            <div class="header-title" id="active-conversation-title">{escape(resolved.metadata.display_name)}</div>
            <div class="header-subtitle" id="active-conversation-subtitle">{escape(header_spec['subtitle_template'].replace('{knowledge_base_name}', str(library['knowledge_base_name'])))}</div>
          </div>
          <div class="header-actions">
            <button class="pill-button" type="button" data-open-knowledge-switch="true" id="knowledge-badge-secondary"></button>
            <a class="ghost-link" href="{escape(frontend_ui['pages']['knowledge_list']['path'])}">{escape(header_spec['knowledge_entry_link_label'])}</a>
            <a class="ghost-link" href="{escape(frontend_ui['pages']['basketball_showcase']['path'])}">{escape(header_spec['showcase_link_label'])}</a>
          </div>
        </header>

        <section class="chat-content">
          <div class="chat-stream">
            <section class="welcome-state" id="welcome-state">
              <div class="welcome-card">
                <span class="eyebrow">{escape(conversation_spec['welcome_kicker'])}</span>
                <h2>{escape(conversation_spec['welcome_title'])}</h2>
                <p>{escape(conversation_spec['welcome_copy'])}</p>
                <div class="kb-pill" style="justify-content:center;">{escape(conversation_spec['current_knowledge_base_template'].replace('{knowledge_base_name}', str(library['knowledge_base_name'])))}</div>
                <div class="prompt-grid" id="prompt-grid"></div>
              </div>
            </section>
            <div class="message-list" id="message-list"></div>
          </div>
        </section>

        <div class="chat-composer-wrap">
          <form class="chat-composer" id="chat-form">
            <div class="composer-status">
              <span id="composer-context">{escape(composer_spec['context_template'].replace('{context_label}', str(library['knowledge_base_name'])))}</span>
              <span>{escape(composer_spec['citation_hint'])}</span>
            </div>
            <textarea
              class="composer-input"
              id="chat-input"
              rows="4"
              placeholder="{escape(composer_spec['placeholder'])}"
            ></textarea>
            <div class="composer-actions">
              <div class="left">
                <span class="source-chip">{escape(composer_spec['mode_label'])}</span>
                <a class="ghost-link" href="{escape(frontend_ui['pages']['knowledge_list']['path'])}">{escape(composer_spec['knowledge_link_label'])}</a>
                <a class="ghost-link" href="{escape(frontend_ui['pages']['basketball_showcase']['path'])}">{escape(composer_spec['showcase_link_label'])}</a>
              </div>
              <button class="primary-btn" type="submit">{escape(composer_spec['submit_label'])}</button>
            </div>
          </form>
        </div>
      </main>
    </div>

    <div class="drawer-backdrop hidden" id="drawer-backdrop"></div>
    <aside class="citation-drawer hidden" id="citation-drawer">
      <header class="drawer-head">
        <div id="drawer-meta"></div>
        <button class="drawer-close" id="citation-drawer-close" type="button" aria-label="{escape(drawer_spec['close_aria_label'])}">×</button>
      </header>
      <div class="drawer-tabs" id="drawer-tabs"></div>
      <section class="drawer-content">
        <article class="drawer-card" id="drawer-snippet"></article>
        <article class="drawer-card" id="drawer-section"></article>
      </section>
      <footer class="drawer-actions">
        <a class="ghost-link" id="drawer-document-link" href="{escape(frontend_ui['pages']['knowledge_list']['path'])}">{escape(drawer_spec['document_link_label'])}</a>
      </footer>
    </aside>

    <div class="dialog-backdrop hidden" id="knowledge-dialog-backdrop">
      <div class="dialog-shell">
        <section class="dialog-panel">
          <header class="dialog-head">
            <div>
              <h2>{escape(switch_dialog_spec['title'])}</h2>
              <p>{escape(switch_dialog_spec['description'])}</p>
            </div>
            <button class="drawer-close" id="knowledge-dialog-close" type="button" aria-label="{escape(switch_dialog_spec['close_aria_label'])}">×</button>
          </header>
          <div class="dialog-body">
            <div class="kb-list" id="knowledge-dialog-list"></div>
          </div>
        </section>
      </div>
    </div>

    {_chat_script(resolved)}
    """
    return _render_page(resolved.metadata.display_name, style, body)


def build_knowledge_base_page_handler(
    project: ProjectRuntimeAssembly,
    repository: "KnowledgeRepository" | None = None,
) -> Any:
    def handler() -> str:
        return compose_knowledge_base_page(project)

    return handler


def build_basketball_showcase_page_handler(
    project: ProjectRuntimeAssembly,
    repository: "KnowledgeRepository" | None = None,
) -> Any:
    def handler() -> str:
        return compose_basketball_showcase_page(project)

    return handler


def build_knowledge_base_list_page_handler(
    project: ProjectRuntimeAssembly,
    repository: "KnowledgeRepository" | None = None,
) -> Any:
    resolved_repository = _require_repository(project, repository)

    def handler() -> str:
        return compose_knowledge_base_list_page(project, resolved_repository)

    return handler


def build_knowledge_base_detail_page_handler(
    project: ProjectRuntimeAssembly,
    repository: "KnowledgeRepository" | None = None,
) -> Any:
    resolved_repository = _require_repository(project, repository)

    def handler(knowledge_base_id: str) -> str:
        knowledge_base = resolved_repository.get_knowledge_base(knowledge_base_id)
        if knowledge_base is None:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        return compose_knowledge_base_detail_page(project, knowledge_base)

    return handler


def build_document_detail_page_handler(
    project: ProjectRuntimeAssembly,
    repository: "KnowledgeRepository" | None = None,
) -> Any:
    resolved_repository = _require_repository(project, repository)

    def handler(document_id: str, section: str | None = None) -> str:
        document = resolved_repository.get_document(document_id)
        if document is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return compose_document_detail_page(project, document, active_section_id=section)

    return handler


def _require_repository(
    project: ProjectRuntimeAssembly,
    repository: "KnowledgeRepository" | None,
) -> "KnowledgeRepository":
    if repository is not None:
        return repository
    from knowledge_base_runtime.backend import KnowledgeRepository

    return KnowledgeRepository(project)
