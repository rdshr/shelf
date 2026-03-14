from __future__ import annotations

from dataclasses import dataclass
import json
from textwrap import dedent

from project_runtime.knowledge_base import KnowledgeBaseCodeModule


def _require_script_profile(project: KnowledgeBaseCodeModule) -> str:
    implementation = project.ui_spec.get("implementation")
    if not isinstance(implementation, dict):
        raise ValueError("ui_spec.implementation is required for frontend script selection")
    value = implementation.get("script_profile")
    if not isinstance(value, str):
        raise ValueError("ui_spec.implementation.script_profile must be a string")
    if value not in project.template_contract.supported_frontend_script_profiles:
        raise ValueError(f"unsupported frontend script_profile: {value}")
    return value


@dataclass(frozen=True)
class ChatScriptTemplateContext:
    project_spec_json: str

    def render(self) -> str:
        sections = (
            _chat_script_bootstrap(self.project_spec_json),
            _chat_script_utility_section(),
            _chat_script_conversation_section(),
            _chat_script_rendering_section(),
            _chat_script_loading_section(),
            _chat_script_drawer_section(),
            _chat_script_route_and_submit_section(),
            _chat_script_init_section(),
        )
        script_body = "\n".join(section.strip("\n") for section in sections)
        return "<script>\n" + script_body + "\n</script>"


def _chat_script_bootstrap(project_spec_json: str) -> str:
    return dedent(
        f"""
      const runtimeBundle = {project_spec_json};
      const productSpec = runtimeBundle.product_spec;
      const uiSpec = runtimeBundle.ui_spec;
      const backendSpec = runtimeBundle.backend_spec;
      const messageStreamSpec = uiSpec.components.message_stream;
      const composerSpec = uiSpec.components.chat_composer;
      const drawerSpec = uiSpec.components.citation_drawer;
      const switchDialogSpec = uiSpec.components.knowledge_switch_dialog;
      const conversationSpec = uiSpec.conversation;
      const storageKey = `shelf-kb-conversations:${{productSpec.product.project_id}}`;
      const state = {{
        knowledgeBases: [],
        documents: [],
        conversations: [],
        activeConversationId: "",
        currentKnowledgeBaseId: backendSpec.knowledge_base.knowledge_base_id,
        contextDocumentId: "",
        contextSectionId: "",
        drawerOpen: false,
        activeCitations: [],
        activeCitationIndex: 0,
        drawerSectionHtml: "",
        drawerSnippet: "",
        drawerDocumentPath: ""
      }};

      const elements = {{
        groups: document.getElementById("conversation-groups"),
        newChat: document.getElementById("new-chat"),
        knowledgeSwitchButtons: Array.from(document.querySelectorAll("[data-open-knowledge-switch]")),
        welcomeState: document.getElementById("welcome-state"),
        messageList: document.getElementById("message-list"),
        composer: document.getElementById("chat-form"),
        composerInput: document.getElementById("chat-input"),
        composerContext: document.getElementById("composer-context"),
        knowledgeBadge: document.getElementById("knowledge-badge"),
        knowledgeBadgeSecondary: document.getElementById("knowledge-badge-secondary"),
        headerTitle: document.getElementById("active-conversation-title"),
        headerSubtitle: document.getElementById("active-conversation-subtitle"),
        drawer: document.getElementById("citation-drawer"),
        drawerBackdrop: document.getElementById("drawer-backdrop"),
        drawerClose: document.getElementById("citation-drawer-close"),
        drawerTabs: document.getElementById("drawer-tabs"),
        drawerMeta: document.getElementById("drawer-meta"),
        drawerSnippet: document.getElementById("drawer-snippet"),
        drawerSection: document.getElementById("drawer-section"),
        drawerDocumentLink: document.getElementById("drawer-document-link"),
        knowledgeDialogBackdrop: document.getElementById("knowledge-dialog-backdrop"),
        knowledgeDialogClose: document.getElementById("knowledge-dialog-close"),
        knowledgeDialogList: document.getElementById("knowledge-dialog-list"),
        promptGrid: document.getElementById("prompt-grid")
      }};
        """
    )


def _chat_script_utility_section() -> str:
    return dedent(
        """
      function escapeHtml(value) {
        return String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;")
          .replaceAll("'", "&#39;");
      }

      function conversationId() {
        if (window.crypto && "randomUUID" in window.crypto) {
          return window.crypto.randomUUID();
        }
        return `conv-${Date.now()}-${Math.random().toString(16).slice(2)}`;
      }

      function parseDateGroup(iso) {
        const updated = new Date(iso);
        const now = new Date();
        const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const diff = startOfToday.getTime() - new Date(updated.getFullYear(), updated.getMonth(), updated.getDate()).getTime();
        const days = Math.floor(diff / 86400000);
        if (days <= 0) return conversationSpec.relative_groups.today;
        if (days < 7) return conversationSpec.relative_groups.last_7_days;
        if (days < 30) return conversationSpec.relative_groups.last_30_days;
        return conversationSpec.relative_groups.older;
      }
        """
    )


def _chat_script_conversation_section() -> str:
    return dedent(
        """
      function persistConversations() {
        window.localStorage.setItem(storageKey, JSON.stringify(state.conversations));
      }

      function getActiveConversation() {
        return state.conversations.find((item) => item.id === state.activeConversationId) || null;
      }

      function saveActiveConversation(conversation) {
        state.conversations = state.conversations.map((item) => (item.id === conversation.id ? conversation : item));
        state.conversations.sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt));
        persistConversations();
      }

      function createConversation(seedMessage = "") {
        const conversation = {
          id: conversationId(),
          title: conversationSpec.default_title,
          knowledgeBaseId: state.currentKnowledgeBaseId,
          updatedAt: new Date().toISOString(),
          messages: []
        };
        state.conversations.unshift(conversation);
        state.activeConversationId = conversation.id;
        persistConversations();
        renderConversationGroups();
        renderActiveConversation();
        if (seedMessage) {
          elements.composerInput.value = seedMessage;
          void submitChat(seedMessage);
        }
      }

      function ensureConversationState() {
        try {
          const stored = window.localStorage.getItem(storageKey);
          state.conversations = stored ? JSON.parse(stored) : [];
        } catch (error) {
          state.conversations = [];
        }
        if (!Array.isArray(state.conversations) || state.conversations.length === 0) {
          createConversation();
          return;
        }
        state.activeConversationId = state.conversations[0].id;
      }
        """
    )


def _chat_script_rendering_section() -> str:
    return dedent(
        """
      function renderPromptGrid() {
        elements.promptGrid.innerHTML = "";
        for (const prompt of uiSpec.conversation.welcome_prompts) {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "prompt-chip";
          button.textContent = prompt;
          button.addEventListener("click", () => {
            elements.composerInput.value = prompt;
            elements.composerInput.focus();
          });
          elements.promptGrid.appendChild(button);
        }
      }

      function renderConversationGroups() {
        elements.groups.innerHTML = "";
        const grouped = new Map();
        for (const conversation of state.conversations) {
          const key = parseDateGroup(conversation.updatedAt);
          if (!grouped.has(key)) grouped.set(key, []);
          grouped.get(key).push(conversation);
        }
        for (const [groupTitle, items] of grouped.entries()) {
          const section = document.createElement("section");
          section.className = "conversation-group";
          section.innerHTML = `<div class="conversation-group-title">${escapeHtml(groupTitle)}</div>`;
          for (const item of items) {
            const button = document.createElement("button");
            const isActive = item.id === state.activeConversationId;
            button.type = "button";
            button.className = "conversation-item" + (isActive ? " active" : "");
            button.dataset.navId = "conversation-item";
            button.setAttribute("aria-current", isActive ? "page" : "false");
            button.innerHTML = `
              <div class="conversation-title">${escapeHtml(item.title)}</div>
              <div class="conversation-meta">${escapeHtml(new Date(item.updatedAt).toLocaleString("zh-CN"))}</div>
            `;
            button.addEventListener("click", () => {
              state.activeConversationId = item.id;
              renderConversationGroups();
              renderActiveConversation();
            });
            section.appendChild(button);
          }
          elements.groups.appendChild(section);
        }
      }

      function renderWelcomeState(conversation) {
        const empty = !conversation || conversation.messages.length === 0;
        elements.welcomeState.style.display = empty ? "grid" : "none";
      }

      function currentKnowledgeBaseName() {
        const active = state.knowledgeBases.find((item) => item.knowledge_base_id === state.currentKnowledgeBaseId);
        return active ? active.name : backendSpec.knowledge_base.knowledge_base_name;
      }

      function renderHeader(conversation) {
        elements.headerTitle.textContent = conversation ? conversation.title : productSpec.product.display_name;
        elements.headerSubtitle.textContent = uiSpec.components.chat_header.subtitle_template.replace("{knowledge_base_name}", currentKnowledgeBaseName());
        elements.knowledgeBadge.textContent = uiSpec.components.conversation_sidebar.knowledge_entry_label.replace(
          backendSpec.knowledge_base.knowledge_base_name,
          currentKnowledgeBaseName()
        );
        elements.knowledgeBadgeSecondary.textContent = uiSpec.components.chat_header.knowledge_badge_template.replace(
          "{knowledge_base_name}",
          currentKnowledgeBaseName()
        );
        if (state.contextDocumentId && state.contextSectionId) {
          elements.composerContext.textContent = composerSpec.context_template.replace(
            "{context_label}",
            `${state.contextDocumentId} / ${state.contextSectionId}`
          );
        } else {
          elements.composerContext.textContent = composerSpec.context_template.replace(
            "{context_label}",
            currentKnowledgeBaseName()
          );
        }
      }

      function messageHtml(message) {
        if (message.role === "user") {
          return `<div class="message-bubble"><div class="message-content"><p>${escapeHtml(message.text)}</p></div></div>`;
        }
        const content = escapeHtml(message.text || "")
          .replace(/\\[(\\d+)\\]/g, '<button type="button" class="inline-ref" data-index="$1">[$1]</button>')
          .split(/\\n\\n+/)
          .map((part) => `<p>${part.replaceAll("\\n", "<br>")}</p>`)
          .join("");
        const citations = Array.isArray(message.citations) ? message.citations : [];
        const summary = citations.length
          ? `
            <div class="citation-summary">
              <span class="summary-label">${escapeHtml(messageStreamSpec.summary_template.replace("{count}", String(citations.length)))}</span>
              ${citations
                .map((citation, index) => `<button type="button" class="citation-chip" data-citation-index="${index}">[${index + 1}] ${escapeHtml(citation.document_title)}</button>`)
                .join("")}
            </div>
          `
          : "";
        const pending = message.pending ? `<div class="assistant-loading">${escapeHtml(backendSpec.interaction_copy.loading_text)}</div>` : "";
        return `
          <div class="assistant-body">
            ${pending}
            <div class="message-content">${content}</div>
            ${summary}
            <div class="message-actions">
              <button type="button" class="message-action" data-copy-answer="true">${escapeHtml(messageStreamSpec.copy_action_label)}</button>
            </div>
          </div>
        `;
      }

      function renderMessages() {
        const conversation = getActiveConversation();
        elements.messageList.innerHTML = "";
        if (!conversation) return;
        for (const message of conversation.messages) {
          const row = document.createElement("section");
          row.className = "message-row";
          row.innerHTML = `
            <article class="message-card ${message.role}">
              <div class="message-role">${message.role === "user" ? escapeHtml(messageStreamSpec.role_labels.user) : escapeHtml(messageStreamSpec.role_labels.assistant)}</div>
              ${messageHtml(message)}
            </article>
          `;
          for (const button of row.querySelectorAll(".inline-ref")) {
            button.addEventListener("click", () => {
              const index = Number(button.dataset.index || "1") - 1;
              openCitationDrawer(message.citations || [], index);
            });
          }
          for (const button of row.querySelectorAll("[data-citation-index]")) {
            button.addEventListener("click", () => {
              const index = Number(button.dataset.citationIndex || "0");
              openCitationDrawer(message.citations || [], index);
            });
          }
          const copyButton = row.querySelector("[data-copy-answer='true']");
          if (copyButton) {
            copyButton.addEventListener("click", async () => {
              try {
                await window.navigator.clipboard.writeText(message.text || "");
              } catch (error) {
                window.alert(messageStreamSpec.copy_failure_message);
              }
            });
          }
          elements.messageList.appendChild(row);
        }
      }

      function renderActiveConversation() {
        const conversation = getActiveConversation();
        renderConversationGroups();
        renderWelcomeState(conversation);
        renderHeader(conversation);
        renderMessages();
      }
        """
    )


def _chat_script_loading_section() -> str:
    return dedent(
        """
      async function loadKnowledgeBases() {
        const response = await fetch(runtimeBundle.routes.api.knowledge_bases);
        state.knowledgeBases = response.ok ? await response.json() : [];
        renderKnowledgeDialog();
        renderActiveConversation();
      }

      async function loadDocuments() {
        const response = await fetch(runtimeBundle.routes.api.documents);
        state.documents = response.ok ? await response.json() : [];
      }

      function renderKnowledgeDialog() {
        elements.knowledgeDialogList.innerHTML = "";
        for (const item of state.knowledgeBases) {
          const article = document.createElement("article");
          article.className = "kb-card" + (item.knowledge_base_id === state.currentKnowledgeBaseId ? " active" : "");
          article.innerHTML = `
            <h3>${escapeHtml(item.name)}</h3>
            <p>${escapeHtml(item.description)}</p>
            <div class="card-meta">
              <span class="meta-chip">${item.document_count} documents</span>
              <span class="meta-chip">${escapeHtml(item.updated_at)}</span>
            </div>
            <div class="card-meta">
              <button type="button" class="primary-btn" data-select-kb="${escapeHtml(item.knowledge_base_id)}">${escapeHtml(switchDialogSpec.select_action_label)}</button>
              <a class="ghost-link" href="${uiSpec.pages.knowledge_detail.path.replace("{knowledge_base_id}", item.knowledge_base_id)}">${escapeHtml(switchDialogSpec.detail_action_label)}</a>
            </div>
          `;
          const selectButton = article.querySelector("[data-select-kb]");
          if (selectButton) {
            selectButton.addEventListener("click", () => {
              state.currentKnowledgeBaseId = item.knowledge_base_id;
              const conversation = getActiveConversation();
              if (conversation) {
                conversation.knowledgeBaseId = item.knowledge_base_id;
                conversation.updatedAt = new Date().toISOString();
                saveActiveConversation(conversation);
              }
              closeKnowledgeDialog();
              renderKnowledgeDialog();
              renderActiveConversation();
            });
          }
          elements.knowledgeDialogList.appendChild(article);
        }
      }

      function openKnowledgeDialog() {
        elements.knowledgeDialogBackdrop.classList.remove("hidden");
      }

      function closeKnowledgeDialog() {
        elements.knowledgeDialogBackdrop.classList.add("hidden");
      }
        """
    )


def _chat_script_drawer_section() -> str:
    return dedent(
        """
      async function fetchSectionHtml(citation) {
        const url = runtimeBundle.routes.api.section_detail
          .replace("{document_id}", citation.document_id)
          .replace("{section_id}", citation.section_id);
        const response = await fetch(url);
        if (!response.ok) {
          state.drawerSectionHtml = `<p>${escapeHtml(drawerSpec.load_failure_text)}</p>`;
          return;
        }
        const payload = await response.json();
        state.drawerSectionHtml = payload.html;
        state.drawerSnippet = citation.snippet;
      }

      async function openCitationDrawer(citations, index) {
        if (!Array.isArray(citations) || citations.length === 0) return;
        state.activeCitations = citations;
        state.activeCitationIndex = Math.max(0, Math.min(index, citations.length - 1));
        const citation = state.activeCitations[state.activeCitationIndex];
        state.drawerDocumentPath = citation.document_path;
        state.contextDocumentId = citation.document_id;
        state.contextSectionId = citation.section_id;
        await fetchSectionHtml(citation);
        renderDrawer();
        elements.drawer.classList.remove("hidden");
        elements.drawerBackdrop.classList.remove("hidden");
        state.drawerOpen = true;
        syncRoute();
        renderActiveConversation();
      }

      function closeCitationDrawer() {
        state.drawerOpen = false;
        elements.drawer.classList.add("hidden");
        elements.drawerBackdrop.classList.add("hidden");
        syncRoute();
      }

      function renderDrawer() {
        const citation = state.activeCitations[state.activeCitationIndex];
        if (!citation) return;
        elements.drawerTabs.innerHTML = "";
        for (let index = 0; index < state.activeCitations.length; index += 1) {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "drawer-tab" + (index === state.activeCitationIndex ? " active" : "");
          button.textContent = `[${index + 1}]`;
          button.addEventListener("click", () => openCitationDrawer(state.activeCitations, index));
          elements.drawerTabs.appendChild(button);
        }
        elements.drawerMeta.innerHTML = `
          <h2>${escapeHtml(citation.document_title)}</h2>
          <p class="drawer-subtitle">${escapeHtml(drawerSpec.section_label)}：${escapeHtml(citation.section_title)}</p>
        `;
        elements.drawerSnippet.innerHTML = `
          <h3>${escapeHtml(drawerSpec.snippet_title)}</h3>
          <p>${escapeHtml(state.drawerSnippet || citation.snippet)}</p>
        `;
        elements.drawerSection.innerHTML = `
          <h3>${escapeHtml(drawerSpec.source_context_title)}</h3>
          ${state.drawerSectionHtml || `<p>${escapeHtml(drawerSpec.empty_context_text)}</p>`}
        `;
        elements.drawerDocumentLink.href = citation.document_path;
        elements.drawerDocumentLink.textContent = drawerSpec.document_link_label;
      }
        """
    )


def _chat_script_route_and_submit_section() -> str:
    return dedent(
        """
      function syncRoute() {
        const params = new URLSearchParams(window.location.search);
        if (state.contextDocumentId) params.set("document", state.contextDocumentId);
        else params.delete("document");
        if (state.contextSectionId) params.set("section", state.contextSectionId);
        else params.delete("section");
        if (state.drawerOpen) params.set("citation", String(state.activeCitationIndex + 1));
        else params.delete("citation");
        const query = params.toString();
        const nextUrl = query ? `${window.location.pathname}?${query}` : window.location.pathname;
        window.history.replaceState(null, "", nextUrl);
      }

      async function hydrateFromQuery() {
        const params = new URLSearchParams(window.location.search);
        const documentId = params.get("document");
        const sectionId = params.get("section");
        if (!documentId || !sectionId) return;
        const documentItem = state.documents.find((item) => item.document_id === documentId);
        if (!documentItem) return;
        const citation = {
          citation_id: params.get("citation") || "1",
          document_id: documentId,
          document_title: documentItem.title,
          section_id: sectionId,
          section_title: sectionId,
          snippet: documentItem.summary,
          return_path: `${window.location.pathname}?document=${documentId}&section=${sectionId}`,
          document_path: uiSpec.pages.document_detail.path.replace("{document_id}", documentId) + `?section=${sectionId}`
        };
        await openCitationDrawer([citation], 0);
      }

      async function submitChat(forcedMessage) {
        const conversation = getActiveConversation();
        if (!conversation) return;
        const raw = typeof forcedMessage === "string" ? forcedMessage : elements.composerInput.value;
        const message = raw.trim();
        if (!message) return;

        conversation.messages.push({ role: "user", text: message });
        const pendingMessage = { role: "assistant", text: "", citations: [], pending: true };
        conversation.messages.push(pendingMessage);
        conversation.updatedAt = new Date().toISOString();
        if (conversation.title === conversationSpec.default_title) {
          conversation.title = message.slice(0, 24);
        }
        saveActiveConversation(conversation);
        renderActiveConversation();
        if (!forcedMessage) {
          elements.composerInput.value = "";
        }

        try {
          const response = await fetch(runtimeBundle.routes.api.chat_turns, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              message,
              document_id: state.contextDocumentId || null,
              section_id: state.contextSectionId || null
            })
          });
          if (!response.ok) {
            throw new Error("chat request failed");
          }
          const payload = await response.json();
          pendingMessage.pending = false;
          pendingMessage.text = payload.answer;
          pendingMessage.citations = payload.citations;
          state.contextDocumentId = payload.context_document_id || state.contextDocumentId;
          state.contextSectionId = payload.context_section_id || state.contextSectionId;
          conversation.updatedAt = new Date().toISOString();
          saveActiveConversation(conversation);
          renderActiveConversation();
          syncRoute();
        } catch (error) {
          pendingMessage.pending = false;
          pendingMessage.text = backendSpec.interaction_copy.error_text;
          pendingMessage.citations = [];
          saveActiveConversation(conversation);
          renderActiveConversation();
        }
      }
        """
    )


def _chat_script_init_section() -> str:
    return dedent(
        """
      elements.newChat.addEventListener("click", () => createConversation());
      for (const button of elements.knowledgeSwitchButtons) {
        button.addEventListener("click", openKnowledgeDialog);
      }
      elements.knowledgeDialogClose.addEventListener("click", closeKnowledgeDialog);
      elements.knowledgeDialogBackdrop.addEventListener("click", (event) => {
        if (event.target === elements.knowledgeDialogBackdrop) closeKnowledgeDialog();
      });
      elements.drawerClose.addEventListener("click", closeCitationDrawer);
      elements.drawerBackdrop.addEventListener("click", closeCitationDrawer);
      elements.composer.addEventListener("submit", async (event) => {
        event.preventDefault();
        await submitChat();
      });
      elements.composerInput.addEventListener("keydown", async (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
          event.preventDefault();
          await submitChat();
        }
      });

      async function init() {
        renderPromptGrid();
        ensureConversationState();
        renderConversationGroups();
        renderActiveConversation();
        await Promise.all([loadKnowledgeBases(), loadDocuments()]);
        await hydrateFromQuery();
      }

      void init();
        """
    )


def build_chat_script(project: KnowledgeBaseCodeModule) -> str:
    _require_script_profile(project)
    context = ChatScriptTemplateContext(
        project_spec_json=json.dumps(project.to_spec_dict(), ensure_ascii=False),
    )
    return context.render()
