from __future__ import annotations

from dataclasses import dataclass
from textwrap import dedent

from knowledge_base_runtime.runtime_exports import resolve_frontend_app_spec
from knowledge_base_runtime.runtime_profile import load_knowledge_base_runtime_profile
from project_runtime import ProjectRuntimeAssembly


@dataclass(frozen=True)
class StyleTemplateContext:
    bg: str
    panel: str
    panel_soft: str
    ink: str
    muted: str
    accent: str
    accent_soft: str
    line: str
    radius: str
    shadow: str
    font_body: str
    font_title: str
    font_hero: str
    sidebar_width: str
    drawer_width: str
    message_width: str
    shell_gap: str
    shell_padding: str
    panel_gap: str

    @classmethod
    def from_project(cls, project: ProjectRuntimeAssembly) -> "StyleTemplateContext":
        _require_style_profile(project)
        visual = resolve_frontend_app_spec(project)["ui"]["visual"]["tokens"]
        return cls(
            bg=visual["bg"],
            panel=visual["panel"],
            panel_soft=visual["panel_soft"],
            ink=visual["ink"],
            muted=visual["muted"],
            accent=visual["accent"],
            accent_soft=visual["accent_soft"],
            line=visual["line"],
            radius=visual["radius"],
            shadow=visual["shadow"],
            font_body=visual["font_body"],
            font_title=visual["font_title"],
            font_hero=visual["font_hero"],
            sidebar_width=visual["sidebar_width"],
            drawer_width=visual["drawer_width"],
            message_width=visual["message_width"],
            shell_gap=visual["shell_gap"],
            shell_padding=visual["shell_padding"],
            panel_gap=visual["panel_gap"],
        )

    def render(self) -> str:
        style = "\n\n".join(
            (
                _style_root_section(),
                _style_global_shell_section(),
                _style_sidebar_section(),
                _style_chat_section(),
                _style_drawer_section(),
                _style_aux_section(),
                _style_responsive_section(),
            )
        )
        for key, value in self.replacements().items():
            style = style.replace(key, value)
        return style

    def replacements(self) -> dict[str, str]:
        return {
            "__BG__": self.bg,
            "__PANEL__": self.panel,
            "__PANEL_SOFT__": self.panel_soft,
            "__INK__": self.ink,
            "__MUTED__": self.muted,
            "__ACCENT__": self.accent,
            "__ACCENT_SOFT__": self.accent_soft,
            "__LINE__": self.line,
            "__RADIUS__": self.radius,
            "__SHADOW__": self.shadow,
            "__FONT_BODY__": self.font_body,
            "__FONT_TITLE__": self.font_title,
            "__FONT_HERO__": self.font_hero,
            "__SIDEBAR_WIDTH__": self.sidebar_width,
            "__DRAWER_WIDTH__": self.drawer_width,
            "__MESSAGE_WIDTH__": self.message_width,
            "__SHELL_GAP__": self.shell_gap,
            "__SHELL_PADDING__": self.shell_padding,
            "__PANEL_GAP__": self.panel_gap,
        }


def _require_style_profile(project: ProjectRuntimeAssembly) -> str:
    implementation = resolve_frontend_app_spec(project)["ui"].get("implementation")
    if not isinstance(implementation, dict):
        raise ValueError("frontend_app_spec.ui.implementation is required for frontend style selection")
    value = implementation.get("style_profile")
    if not isinstance(value, str):
        raise ValueError("frontend_app_spec.ui.implementation.style_profile must be a string")
    if value not in load_knowledge_base_runtime_profile().supported_frontend_style_profiles:
        raise ValueError(f"unsupported frontend style_profile: {value}")
    return value


def _style_root_section() -> str:
    return dedent(
        """
        :root {
          --bg: __BG__;
          --panel: __PANEL__;
          --panel-soft: __PANEL_SOFT__;
          --ink: __INK__;
          --muted: __MUTED__;
          --accent: __ACCENT__;
          --accent-soft: __ACCENT_SOFT__;
          --line: __LINE__;
          --radius: __RADIUS__;
          --shadow: __SHADOW__;
          --font-body: __FONT_BODY__;
          --font-title: __FONT_TITLE__;
          --font-hero: __FONT_HERO__;
          --sidebar-width: __SIDEBAR_WIDTH__;
          --drawer-width: __DRAWER_WIDTH__;
          --message-width: __MESSAGE_WIDTH__;
          --shell-gap: __SHELL_GAP__;
          --shell-padding: __SHELL_PADDING__;
          --panel-gap: __PANEL_GAP__;
          --sidebar-bg: #111827;
          --sidebar-ink: #f8fafc;
          --sidebar-muted: rgba(248, 250, 252, 0.68);
          --danger: #b42318;
          --success: #0f766e;
        }

        * { box-sizing: border-box; }

        html, body { margin: 0; }

        body {
          min-height: 100vh;
          font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
          font-size: var(--font-body);
          color: var(--ink);
          background:
            radial-gradient(circle at top left, rgba(37, 99, 235, 0.12), transparent 26%),
            radial-gradient(circle at bottom right, rgba(15, 118, 110, 0.08), transparent 20%),
            var(--bg);
        }

        button, input, textarea, select { font: inherit; }
        button { cursor: pointer; }
        a { color: inherit; text-decoration: none; }
        """
    ).strip()


def _style_global_shell_section() -> str:
    return dedent(
        """
        .chat-shell,
        .aux-shell {
          min-height: 100vh;
          display: grid;
          gap: var(--shell-gap);
          padding: var(--shell-padding);
        }

        .chat-shell {
          grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
        }

        .chat-main {
          min-height: calc(100vh - (var(--shell-padding) * 2));
          display: grid;
          grid-template-rows: auto minmax(0, 1fr) auto;
          background: rgba(255, 255, 255, 0.34);
          border-radius: calc(var(--radius) + 10px);
          overflow: hidden;
        }

        .chat-header,
        .aux-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 16px;
          padding: calc(var(--shell-padding) + 4px) calc(var(--shell-padding) * 2);
          border-bottom: 1px solid var(--line);
          background: rgba(255, 255, 255, 0.76);
          backdrop-filter: blur(14px);
          position: sticky;
          top: 0;
          z-index: 10;
        }

        .header-copy {
          display: grid;
          gap: 4px;
        }

        .header-title {
          margin: 0;
          font-size: 1.02rem;
          font-weight: 700;
        }

        .header-subtitle {
          color: var(--muted);
          font-size: 0.9rem;
        }

        .header-actions {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
          justify-content: flex-end;
        }

        .pill-button,
        .kb-pill,
        .source-chip {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 9px 12px;
          border-radius: 999px;
          border: 1px solid var(--line);
          background: rgba(255, 255, 255, 0.9);
          color: var(--ink);
        }

        .ghost-btn,
        .ghost-link,
        .secondary-link {
          border: 1px solid var(--line);
          border-radius: 16px;
          padding: 10px 14px;
          background: rgba(255, 255, 255, 0.82);
          color: var(--ink);
        }

        .ghost-link,
        .secondary-link {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }

        .primary-btn {
          border: 0;
          border-radius: 18px;
          padding: 12px 14px;
          background: var(--accent);
          color: white;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }
        """
    ).strip()


def _style_sidebar_section() -> str:
    return dedent(
        """
        .conversation-sidebar {
          background:
            linear-gradient(180deg, rgba(255, 255, 255, 0.04), transparent 24%),
            var(--sidebar-bg);
          color: var(--sidebar-ink);
          padding: calc(var(--shell-padding) + 8px) var(--shell-padding);
          display: grid;
          grid-template-rows: auto auto minmax(0, 1fr) auto;
          gap: var(--panel-gap);
          border-right: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: calc(var(--radius) + 6px);
        }

        .sidebar-brand {
          display: grid;
          gap: var(--panel-gap);
        }

        .eyebrow {
          display: inline-flex;
          align-items: center;
          width: fit-content;
          padding: 6px 10px;
          border-radius: 999px;
          background: rgba(255, 255, 255, 0.08);
          color: var(--sidebar-muted);
          letter-spacing: 0.08em;
          text-transform: uppercase;
          font-size: 0.72rem;
        }

        .sidebar-brand h1,
        .aux-sidebar h1 {
          margin: 0;
          font-size: var(--font-hero);
          line-height: 1.08;
          overflow-wrap: anywhere;
        }

        .sidebar-brand p,
        .aux-sidebar p {
          margin: 0;
          color: var(--sidebar-muted);
          line-height: 1.58;
        }

        .sidebar-primary-btn {
          width: 100%;
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 18px;
          padding: 12px 14px;
          background: rgba(255, 255, 255, 0.08);
          color: var(--sidebar-ink);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
        }

        .sidebar-section {
          min-height: 0;
          display: grid;
          grid-template-rows: auto minmax(0, 1fr);
          gap: var(--panel-gap);
        }

        .sidebar-label {
          font-size: 0.76rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--sidebar-muted);
        }

        .conversation-groups {
          min-height: 0;
          overflow: auto;
          padding-right: 4px;
          display: grid;
          gap: calc(var(--panel-gap) + 4px);
        }

        .conversation-group {
          display: grid;
          gap: 10px;
        }

        .conversation-group-title {
          color: var(--sidebar-muted);
          font-size: 0.78rem;
        }

        .conversation-item {
          width: 100%;
          border: 0;
          text-align: left;
          padding: 11px 12px;
          border-radius: 16px;
          background: transparent;
          color: var(--sidebar-ink);
          display: grid;
          gap: 4px;
        }

        .conversation-item:hover,
        .conversation-item.active {
          background: rgba(255, 255, 255, 0.08);
        }

        .conversation-title {
          font-weight: 600;
          line-height: 1.4;
        }

        .conversation-meta {
          font-size: 0.82rem;
          color: var(--sidebar-muted);
        }

        .sidebar-footer {
          display: grid;
          gap: 10px;
        }

        .sidebar-footer .secondary-link {
          border-color: rgba(255, 255, 255, 0.08);
          background: rgba(255, 255, 255, 0.04);
          color: var(--sidebar-ink);
        }
        """
    ).strip()


def _style_chat_section() -> str:
    return dedent(
        """
        .chat-content {
          min-height: 0;
          overflow: auto;
          padding: calc(var(--shell-padding) * 2) calc(var(--shell-padding) * 2) calc(var(--shell-padding) + 10px);
        }

        .chat-stream {
          width: min(100%, calc(var(--message-width) + 80px));
          margin: 0 auto;
          display: grid;
          gap: calc(var(--panel-gap) * 1.5);
        }

        .welcome-state {
          min-height: calc(100vh - 280px);
          display: grid;
          place-items: center;
          padding: 20px 0 8px;
        }

        .welcome-card {
          width: min(100%, 760px);
          display: grid;
          gap: calc(var(--panel-gap) + 4px);
          text-align: center;
        }

        .welcome-card h2 {
          margin: 0;
          font-size: clamp(2rem, 4vw, 2.8rem);
          line-height: 1.05;
        }

        .welcome-card p {
          margin: 0;
          color: var(--muted);
          line-height: 1.7;
        }

        .prompt-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
          gap: 12px;
        }

        .prompt-chip {
          border: 1px solid var(--line);
          border-radius: 18px;
          background: rgba(255, 255, 255, 0.86);
          padding: 14px 16px;
          text-align: left;
          line-height: 1.55;
          color: var(--ink);
        }

        .message-list {
          display: grid;
          gap: calc(var(--panel-gap) * 1.5);
          padding-bottom: 16px;
        }

        .message-row {
          display: grid;
          gap: 10px;
        }

        .message-card {
          width: min(100%, var(--message-width));
          margin: 0 auto;
          display: grid;
          gap: var(--panel-gap);
          padding: 0 8px;
        }

        .message-card.user {
          justify-items: end;
        }

        .message-card.user .message-bubble {
          max-width: 86%;
          background: #eceff4;
          border-radius: 24px;
          padding: 14px 18px;
          border: 1px solid rgba(17, 24, 39, 0.06);
        }

        .message-role {
          font-size: 0.74rem;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--muted);
        }

        .message-content {
          line-height: 1.8;
          color: var(--ink);
        }

        .message-content p {
          margin: 0 0 14px;
        }

        .message-content p:last-child {
          margin-bottom: 0;
        }

        .assistant-body {
          display: grid;
          gap: var(--panel-gap);
        }

        .inline-ref {
          border: 0;
          background: transparent;
          color: var(--accent);
          padding: 0 2px;
          font-weight: 700;
        }

        .inline-ref:hover {
          text-decoration: underline;
        }

        .message-actions,
        .citation-summary {
          display: flex;
          align-items: center;
          gap: 10px;
          flex-wrap: wrap;
        }

        .message-action {
          border: 0;
          background: transparent;
          color: var(--muted);
          padding: 0;
        }

        .summary-label {
          color: var(--muted);
          font-size: 0.9rem;
        }

        .citation-chip {
          border: 1px solid var(--line);
          background: rgba(255, 255, 255, 0.9);
          border-radius: 999px;
          padding: 8px 12px;
          color: var(--ink);
        }

        .assistant-loading {
          color: var(--muted);
          font-style: italic;
        }

        .chat-composer-wrap {
          padding: 0 calc(var(--shell-padding) * 2) calc(var(--shell-padding) + 6px);
          background: linear-gradient(180deg, rgba(244, 247, 251, 0.0), rgba(244, 247, 251, 0.92) 18%, rgba(244, 247, 251, 0.96));
        }

        .chat-composer {
          width: min(100%, 920px);
          margin: 0 auto;
          display: grid;
          gap: var(--panel-gap);
          padding: 16px;
          border-radius: 28px;
          border: 1px solid var(--line);
          background: rgba(255, 255, 255, 0.92);
          box-shadow: var(--shadow);
          backdrop-filter: blur(16px);
        }

        .composer-status {
          display: flex;
          justify-content: space-between;
          gap: 12px;
          flex-wrap: wrap;
          color: var(--muted);
          font-size: 0.92rem;
        }

        .composer-input {
          width: 100%;
          border: 0;
          background: transparent;
          resize: none;
          min-height: 88px;
          color: var(--ink);
          outline: none;
          line-height: 1.7;
        }

        .composer-actions {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
          flex-wrap: wrap;
        }

        .composer-actions .left {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          align-items: center;
        }
        """
    ).strip()


def _style_drawer_section() -> str:
    return dedent(
        """
        .citation-drawer {
          position: fixed;
          top: 0;
          right: 0;
          bottom: 0;
          width: min(100vw, var(--drawer-width));
          background: rgba(255, 255, 255, 0.97);
          box-shadow: -12px 0 40px rgba(15, 23, 42, 0.16);
          border-left: 1px solid var(--line);
          z-index: 40;
          display: grid;
          grid-template-rows: auto auto minmax(0, 1fr) auto;
          transform: translateX(0);
          transition: transform 160ms ease;
        }

        .citation-drawer.hidden {
          transform: translateX(100%);
        }

        .drawer-backdrop,
        .dialog-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(15, 23, 42, 0.36);
          z-index: 30;
        }

        .drawer-backdrop.hidden,
        .dialog-backdrop.hidden {
          display: none;
        }

        .drawer-head,
        .dialog-head {
          padding: calc(var(--shell-padding) + 6px) calc(var(--shell-padding) + 8px) calc(var(--shell-padding) + 2px);
          border-bottom: 1px solid var(--line);
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 16px;
        }

        .drawer-head h2,
        .dialog-head h2,
        .page-card h2,
        .document-header h2 {
          margin: 0;
          font-size: 1rem;
        }

        .drawer-subtitle,
        .dialog-head p,
        .page-note {
          color: var(--muted);
          line-height: 1.6;
          margin: 6px 0 0;
        }

        .drawer-close {
          border: 0;
          background: transparent;
          font-size: 1.3rem;
          color: var(--muted);
        }

        .drawer-tabs {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          padding: 14px calc(var(--shell-padding) + 8px) 0;
        }

        .drawer-tab {
          border: 1px solid var(--line);
          border-radius: 999px;
          padding: 8px 12px;
          background: rgba(255, 255, 255, 0.92);
          color: var(--muted);
        }

        .drawer-tab.active {
          color: var(--accent);
          border-color: rgba(37, 99, 235, 0.28);
          background: rgba(37, 99, 235, 0.08);
        }

        .drawer-content {
          overflow: auto;
          padding: calc(var(--shell-padding) + 4px) calc(var(--shell-padding) + 8px) calc(var(--shell-padding) + 8px);
          display: grid;
          gap: var(--panel-gap);
        }

        .drawer-card,
        .page-card,
        .document-section {
          border: 1px solid var(--line);
          border-radius: 22px;
          background: rgba(255, 255, 255, 0.9);
          padding: 18px;
        }

        .drawer-card h3,
        .document-section h3 {
          margin: 0 0 10px;
          font-size: 1rem;
        }

        .drawer-card p,
        .document-section p,
        .document-section li,
        .page-card p,
        .page-card li {
          line-height: 1.7;
          color: var(--ink);
        }

        .drawer-actions {
          padding: 0 calc(var(--shell-padding) + 8px) calc(var(--shell-padding) + 8px);
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
        }

        .dialog-shell {
          min-height: 100%;
          display: grid;
          place-items: center;
          padding: 24px;
        }

        .dialog-panel {
          width: min(100%, 720px);
          background: rgba(255, 255, 255, 0.98);
          border-radius: 28px;
          border: 1px solid var(--line);
          box-shadow: 0 24px 64px rgba(15, 23, 42, 0.22);
          overflow: hidden;
        }

        .dialog-body {
          padding: calc(var(--shell-padding) + 6px) calc(var(--shell-padding) + 8px) calc(var(--shell-padding) + 8px);
          display: grid;
          gap: var(--panel-gap);
        }
        """
    ).strip()


def _style_aux_section() -> str:
    return dedent(
        """
        .kb-list,
        .page-grid {
          display: grid;
          gap: var(--panel-gap);
        }

        .kb-card,
        .doc-card {
          border: 1px solid var(--line);
          border-radius: 22px;
          padding: 18px;
          background: rgba(255, 255, 255, 0.92);
          display: grid;
          gap: 10px;
        }

        .kb-card.active {
          border-color: rgba(37, 99, 235, 0.28);
          box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.14);
        }

        .kb-card h3,
        .doc-card h3,
        .page-card h3 {
          margin: 0;
          font-size: 1rem;
        }

        .card-meta,
        .chip-row {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .chip,
        .meta-chip {
          display: inline-flex;
          align-items: center;
          padding: 6px 10px;
          border-radius: 999px;
          background: var(--panel-soft);
          color: var(--muted);
          font-size: 0.82rem;
        }

        .aux-shell {
          grid-template-columns: 280px minmax(0, 1fr);
        }

        .aux-sidebar {
          padding: calc(var(--shell-padding) + 10px) var(--shell-padding);
          display: grid;
          grid-template-rows: auto auto minmax(0, 1fr);
          gap: var(--panel-gap);
          background:
            linear-gradient(180deg, rgba(255, 255, 255, 0.04), transparent 24%),
            var(--sidebar-bg);
          color: var(--sidebar-ink);
          border-radius: calc(var(--radius) + 6px);
        }

        .aux-nav {
          display: grid;
          gap: 10px;
          align-content: start;
        }

        .aux-nav a {
          display: block;
          padding: 12px 14px;
          border-radius: 16px;
          background: rgba(255, 255, 255, 0.04);
          color: var(--sidebar-ink);
        }

        .aux-nav a.active,
        .aux-nav a:hover {
          background: rgba(255, 255, 255, 0.10);
        }

        .aux-main {
          min-height: calc(100vh - (var(--shell-padding) * 2));
          display: grid;
          grid-template-rows: auto minmax(0, 1fr);
          background: rgba(255, 255, 255, 0.34);
          border-radius: calc(var(--radius) + 10px);
          overflow: hidden;
        }

        .aux-content {
          padding: calc(var(--shell-padding) * 2);
          display: grid;
          gap: calc(var(--panel-gap) + 2px);
          align-content: start;
        }

        .document-header {
          display: grid;
          gap: 10px;
          padding: 22px;
          border-radius: 28px;
          background: rgba(255, 255, 255, 0.88);
          border: 1px solid var(--line);
        }

        .document-section.active {
          border-color: rgba(37, 99, 235, 0.3);
          box-shadow: inset 0 0 0 1px rgba(37, 99, 235, 0.12);
        }

        .stack {
          display: grid;
          gap: var(--panel-gap);
        }
        """
    ).strip()


def _style_responsive_section() -> str:
    return dedent(
        """
        @media (max-width: 980px) {
          .chat-shell,
          .aux-shell {
            grid-template-columns: 1fr;
            gap: 0;
            padding: 0;
          }

          .conversation-sidebar,
          .aux-sidebar {
            min-height: auto;
            border-radius: 0;
          }

          .chat-main,
          .aux-main {
            border-radius: 0;
          }

          .citation-drawer {
            width: 100vw;
          }

          .chat-header,
          .aux-header,
          .chat-content,
          .chat-composer-wrap,
          .aux-content {
            padding-left: 18px;
            padding-right: 18px;
          }

          .welcome-state {
            min-height: auto;
          }
        }
        """
    ).strip()


def build_shared_style(project: ProjectRuntimeAssembly) -> str:
    return StyleTemplateContext.from_project(project).render()
