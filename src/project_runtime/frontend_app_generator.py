from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from project_runtime.knowledge_base import KnowledgeBaseProject


def build_frontend_app_files(project: "KnowledgeBaseProject") -> dict[str, str]:
    return {
        ".env.example": "VITE_API_BASE_URL=http://127.0.0.1:8000\n",
        "README.md": _readme(project),
        "index.html": _index_html(project),
        "package.json": _package_json(project),
        "postcss.config.js": _postcss_config(),
        "tailwind.config.ts": _tailwind_config(),
        "tsconfig.json": _tsconfig_json(),
        "tsconfig.app.json": _tsconfig_app_json(),
        "tsconfig.node.json": _tsconfig_node_json(),
        "vite.config.ts": _vite_config(),
        "src/index.css": _index_css(),
        "src/main.tsx": _main_tsx(),
        "src/App.tsx": _app_tsx(project),
    }


def _readme(project: "KnowledgeBaseProject") -> str:
    return f"""# {project.metadata.project_id} frontend-app

Generated React + Vite + Tailwind frontend app.

1. Start the repository backend so `{project.route.api_prefix}/*` is reachable.
2. Copy `.env.example` to `.env`.
3. Install dependencies.
4. Run `npm run dev` or `pnpm dev`.

Do not hand-edit this directory. Re-materialize instead.
"""


def _index_html(project: "KnowledgeBaseProject") -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{project.metadata.display_name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""


def _package_json(project: "KnowledgeBaseProject") -> str:
    payload = {
        "name": f"{project.metadata.project_id}-frontend",
        "private": True,
        "version": project.metadata.version,
        "type": "module",
        "scripts": {"dev": "vite", "build": "tsc -b && vite build", "preview": "vite preview"},
        "dependencies": {
            "react": "^19.0.0",
            "react-dom": "^19.0.0",
            "react-router-dom": "^7.2.0",
        },
        "devDependencies": {
            "@types/react": "^19.0.10",
            "@types/react-dom": "^19.0.4",
            "@vitejs/plugin-react": "^4.3.4",
            "autoprefixer": "^10.4.20",
            "postcss": "^8.5.3",
            "tailwindcss": "^3.4.17",
            "typescript": "^5.7.3",
            "vite": "^6.2.0",
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _postcss_config() -> str:
    return "export default { plugins: { tailwindcss: {}, autoprefixer: {} } };\n"


def _tailwind_config() -> str:
    return """import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: []
} satisfies Config;
"""


def _tsconfig_json() -> str:
    return """{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
"""


def _tsconfig_app_json() -> str:
    return """{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true
  },
  "include": ["src"]
}
"""


def _tsconfig_node_json() -> str:
    return """{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "Bundler"
  },
  "include": ["vite.config.ts", "tailwind.config.ts"]
}
"""


def _vite_config() -> str:
    return """import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()]
});
"""


def _index_css() -> str:
    return """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  min-height: 100vh;
  font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
  background: #f8fafc;
  color: #0f172a;
}

a {
  color: inherit;
}

button,
textarea {
  font: inherit;
}

#root {
  min-height: 100vh;
}
"""


def _main_tsx() -> str:
    return """import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
"""


def _app_tsx(project: "KnowledgeBaseProject") -> str:
    placeholders = {
        "__PROJECT_TITLE__": json.dumps(project.metadata.display_name, ensure_ascii=False),
        "__HERO_KICKER__": json.dumps(project.copy["hero_kicker"], ensure_ascii=False),
        "__HERO_TITLE__": json.dumps(project.copy["hero_title"], ensure_ascii=False),
        "__HERO_COPY__": json.dumps(project.copy["hero_copy"], ensure_ascii=False),
        "__EMPTY_TITLE__": json.dumps(project.copy["empty_state_title"], ensure_ascii=False),
        "__EMPTY_COPY__": json.dumps(project.copy["empty_state_copy"], ensure_ascii=False),
        "__CHAT_TITLE__": json.dumps(project.copy["chat_title"], ensure_ascii=False),
        "__LIBRARY_TITLE__": json.dumps(project.copy["library_title"], ensure_ascii=False),
        "__PREVIEW_TITLE__": json.dumps(project.copy["preview_title"], ensure_ascii=False),
        "__LIBRARY_NAME__": json.dumps(project.library.knowledge_base_name, ensure_ascii=False),
        "__LIBRARY_DESC__": json.dumps(project.library.knowledge_base_description, ensure_ascii=False),
        "__KB_ID__": json.dumps(project.library.knowledge_base_id, ensure_ascii=False),
        "__PLACEHOLDER__": json.dumps(project.chat.placeholder, ensure_ascii=False),
        "__WELCOME_PROMPTS__": json.dumps(list(project.chat.welcome_prompts), ensure_ascii=False, indent=2),
        "__LOGIN_TITLE__": json.dumps(project.auth.copy.login_title, ensure_ascii=False),
        "__LOGIN_SUBTITLE__": json.dumps(project.auth.copy.login_subtitle, ensure_ascii=False),
        "__LOGIN_PRIMARY__": json.dumps(project.auth.copy.primary_action, ensure_ascii=False),
        "__LOGIN_SECONDARY__": json.dumps(project.auth.copy.secondary_action, ensure_ascii=False),
        "__LOGIN_GUARD__": json.dumps(project.auth.copy.guard_message, ensure_ascii=False),
        "__LOGIN_FAILURE__": json.dumps(project.auth.copy.failure_message, ensure_ascii=False),
        "__LOGIN_EXPIRED__": json.dumps(project.auth.copy.expired_message, ensure_ascii=False),
        "__LOGIN_CANCEL__": json.dumps(project.auth.copy.cancel_message, ensure_ascii=False),
        "__LOGIN_REAUTH__": json.dumps(project.auth.copy.reauth_message, ensure_ascii=False),
        "__LOGIN_SHOW_BRAND__": json.dumps(project.auth.surface.show_brand),
        "__LOGIN_SHOW_GUARD__": json.dumps(project.auth.surface.show_guard_message),
        "__LOGIN_SHOW_RETURN_HINT__": json.dumps(project.auth.surface.show_return_hint),
        "__LOGIN_SHOW_SECONDARY__": json.dumps(project.auth.surface.show_secondary_action),
        "__AUTH_ENTRY_VARIANT__": json.dumps(project.auth.surface.entry_variant, ensure_ascii=False),
        "__LOGIN_RESTORE_TARGET__": json.dumps(project.auth.flow.restore_target),
        "__LOGIN_CONTAINER_VARIANT__": json.dumps(project.auth.surface.container_variant, ensure_ascii=False),
        "__LOGIN_DENSITY__": json.dumps(project.auth.surface.density, ensure_ascii=False),
        "__LOGIN_ACTION_EMPHASIS__": json.dumps(project.auth.surface.action_emphasis, ensure_ascii=False),
        "__LOGIN_HEADER_ALIGNMENT__": json.dumps(project.auth.surface.header_alignment, ensure_ascii=False),
        "__LOGIN_STYLE_PROFILE__": json.dumps(project.implementation.frontend.auth_style_profile, ensure_ascii=False),
        "__LOGIN_ACTION_PROFILE__": json.dumps(
            project.implementation.frontend.auth_action_emphasis_profile,
            ensure_ascii=False,
        ),
        "__LOGIN_MOTION_PROFILE__": json.dumps(project.implementation.frontend.auth_motion_profile, ensure_ascii=False),
        "__LOGIN_TITLE_HIERARCHY_PROFILE__": json.dumps(
            project.implementation.frontend.auth_title_hierarchy_profile,
            ensure_ascii=False,
        ),
        "__LOGIN_SUBTITLE_TONE_PROFILE__": json.dumps(
            project.implementation.frontend.auth_subtitle_tone_profile,
            ensure_ascii=False,
        ),
        "__WORKSPACE_SHELL_PAGES__": json.dumps(list(project.page_shells.workspace_shell), ensure_ascii=False),
        "__STANDALONE_SHELL_PAGES__": json.dumps(list(project.page_shells.standalone_shell), ensure_ascii=False),
        "__WORKSPACE_LAYOUT_RUNTIME__": json.dumps(
            project.implementation.frontend.workspace_layout_runtime,
            ensure_ascii=False,
        ),
        "__STANDALONE_LAYOUT_RUNTIME__": json.dumps(
            project.implementation.frontend.standalone_layout_runtime,
            ensure_ascii=False,
        ),
        "__HOME_PATH__": json.dumps(project.route.home, ensure_ascii=False),
        "__LOGIN_PATH__": json.dumps(project.route.login, ensure_ascii=False),
        "__WORKBENCH_PATH__": json.dumps(project.route.workbench, ensure_ascii=False),
        "__KNOWLEDGE_LIST_PATH__": json.dumps(project.route.knowledge_list, ensure_ascii=False),
        "__KNOWLEDGE_DETAIL_PATH__": json.dumps(
            f"{project.route.knowledge_detail}/:knowledgeBaseId",
            ensure_ascii=False,
        ),
        "__DOCUMENT_DETAIL_PATH__": json.dumps(
            f"{project.route.document_detail_prefix}/:documentId",
            ensure_ascii=False,
        ),
        "__KB_LIST_API__": json.dumps(f"{project.route.api_prefix}/knowledge-bases", ensure_ascii=False),
        "__KB_DETAIL_API_PREFIX__": json.dumps(
            f"{project.route.api_prefix}/knowledge-bases",
            ensure_ascii=False,
        ),
        "__DOC_DETAIL_API_PREFIX__": json.dumps(f"{project.route.api_prefix}/documents", ensure_ascii=False),
        "__CHAT_API__": json.dumps(f"{project.route.api_prefix}/chat/turns", ensure_ascii=False),
        "__AUTH_LOGIN_API__": json.dumps(
            f"{project.route.api_prefix}{project.implementation.backend.auth_api.login_endpoint}",
            ensure_ascii=False,
        ),
        "__AUTH_LOGOUT_API__": json.dumps(
            f"{project.route.api_prefix}{project.implementation.backend.auth_api.logout_endpoint}",
            ensure_ascii=False,
        ),
        "__AUTH_SESSION_API__": json.dumps(
            f"{project.route.api_prefix}{project.implementation.backend.auth_api.session_endpoint}",
            ensure_ascii=False,
        ),
        "__AUTH_LOGIN_METHOD__": json.dumps(project.implementation.backend.auth_api.login_method, ensure_ascii=False),
        "__AUTH_LOGOUT_METHOD__": json.dumps(project.implementation.backend.auth_api.logout_method, ensure_ascii=False),
        "__AUTH_SESSION_METHOD__": json.dumps(project.implementation.backend.auth_api.session_method, ensure_ascii=False),
        "__AUTH_SESSION_HEADER__": json.dumps(project.implementation.backend.auth_api.session_header, ensure_ascii=False),
        "__AUTH_LOGIN_ACTION__": json.dumps(project.auth.contract.login_action, ensure_ascii=False),
        "__AUTH_SESSION_PROBE__": json.dumps(project.auth.contract.session_probe, ensure_ascii=False),
        "__AUTH_FAILURE_MODES__": json.dumps(list(project.auth.contract.failure_modes), ensure_ascii=False),
        "__AUTH_GUARD_BEHAVIOR__": json.dumps(project.auth.flow.guard_behavior, ensure_ascii=False),
        "__AUTH_SUCCESS_BEHAVIOR__": json.dumps(project.auth.flow.success_behavior, ensure_ascii=False),
        "__AUTH_FAILURE_FEEDBACK__": json.dumps(project.auth.flow.failure_feedback, ensure_ascii=False),
    }

    template = """import React, { useEffect, useMemo, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation, useNavigate, useParams } from "react-router-dom";

type KnowledgeBaseSummary = {
  knowledge_base_id: string;
  name: string;
  description: string;
  document_count: number;
  updated_at: string;
};

type KnowledgeDocumentSummary = {
  document_id: string;
  title: string;
  summary: string;
  tags: string[];
  updated_at: string;
};

type KnowledgeBaseDetail = KnowledgeBaseSummary & {
  documents: KnowledgeDocumentSummary[];
};

type KnowledgeSection = {
  section_id: string;
  title: string;
  html: string;
};

type KnowledgeDocumentDetail = KnowledgeDocumentSummary & {
  sections: KnowledgeSection[];
};

type Citation = {
  citation_id: string;
  document_title: string;
};

type ChatTurnResponse = {
  answer: string;
  citations: Citation[];
};

type Message = {
  id: string;
  role: "user" | "assistant";
  text: string;
  citations?: Citation[];
};

type Conversation = {
  id: string;
  title: string;
  messages: Message[];
};

type AuthSessionResponse = {
  signed_in: boolean;
  session_token: string | null;
  user_id: string | null;
  display_name: string | null;
  failure_mode?: string | null;
};

type LoginCredentials = {
  username?: string;
  password?: string;
};

const appText = {
  title: __PROJECT_TITLE__,
  heroKicker: __HERO_KICKER__,
  heroTitle: __HERO_TITLE__,
  heroCopy: __HERO_COPY__,
  emptyTitle: __EMPTY_TITLE__,
  emptyCopy: __EMPTY_COPY__,
  chatTitle: __CHAT_TITLE__,
  libraryTitle: __LIBRARY_TITLE__,
  previewTitle: __PREVIEW_TITLE__,
  libraryName: __LIBRARY_NAME__,
  libraryDesc: __LIBRARY_DESC__,
  placeholder: __PLACEHOLDER__,
  knowledgeBaseId: __KB_ID__,
  welcomePrompts: __WELCOME_PROMPTS__,
  loginTitle: __LOGIN_TITLE__,
  loginSubtitle: __LOGIN_SUBTITLE__,
  loginPrimary: __LOGIN_PRIMARY__,
  loginSecondary: __LOGIN_SECONDARY__,
  loginGuard: __LOGIN_GUARD__
};

const routesConfig = {
  home: __HOME_PATH__,
  login: __LOGIN_PATH__,
  workbench: __WORKBENCH_PATH__,
  knowledgeList: __KNOWLEDGE_LIST_PATH__,
  knowledgeDetail: __KNOWLEDGE_DETAIL_PATH__,
  documentDetail: __DOCUMENT_DETAIL_PATH__
};

const endpointConfig = {
  knowledgeBases: __KB_LIST_API__,
  knowledgeBaseDetailPrefix: __KB_DETAIL_API_PREFIX__,
  documentDetailPrefix: __DOC_DETAIL_API_PREFIX__,
  chatTurns: __CHAT_API__,
  auth: {
    login: __AUTH_LOGIN_API__,
    logout: __AUTH_LOGOUT_API__,
    session: __AUTH_SESSION_API__,
    loginMethod: __AUTH_LOGIN_METHOD__,
    logoutMethod: __AUTH_LOGOUT_METHOD__,
    sessionMethod: __AUTH_SESSION_METHOD__,
    sessionHeader: __AUTH_SESSION_HEADER__
  }
};

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\\/$/, "");
const storageKey = "knowledge-base-basic-frontend-conversations";
const authStorageKey = "knowledge-base-basic-auth-session-token";
const authRequestContractConfig = {
  loginAction: __AUTH_LOGIN_ACTION__
};
const authEntryConfig = {
  entryVariant: __AUTH_ENTRY_VARIANT__
};
const authFlowConfig = {
  sessionProbe: __AUTH_SESSION_PROBE__,
  failureModes: __AUTH_FAILURE_MODES__,
  guardBehavior: __AUTH_GUARD_BEHAVIOR__,
  successBehavior: __AUTH_SUCCESS_BEHAVIOR__,
  failureFeedback: __AUTH_FAILURE_FEEDBACK__
};
const authShellConfig = {
  showBrand: __LOGIN_SHOW_BRAND__,
  showGuardMessage: __LOGIN_SHOW_GUARD__,
  showReturnHint: __LOGIN_SHOW_RETURN_HINT__,
  showSecondaryAction: __LOGIN_SHOW_SECONDARY__,
  guardMessage: __LOGIN_GUARD__,
  failureMessage: __LOGIN_FAILURE__,
  expiredMessage: __LOGIN_EXPIRED__,
  cancelMessage: __LOGIN_CANCEL__,
  reauthMessage: __LOGIN_REAUTH__
};
const pageShellConfig = {
  workspaceShell: __WORKSPACE_SHELL_PAGES__,
  standaloneShell: __STANDALONE_SHELL_PAGES__,
  layoutRuntime: {
    workspaceShell: __WORKSPACE_LAYOUT_RUNTIME__,
    standaloneShell: __STANDALONE_LAYOUT_RUNTIME__
  }
};
const loginStyleConfig = {
  containerVariant: __LOGIN_CONTAINER_VARIANT__,
  density: __LOGIN_DENSITY__,
  actionEmphasis: __LOGIN_ACTION_EMPHASIS__,
  headerAlignment: __LOGIN_HEADER_ALIGNMENT__,
  styleProfile: __LOGIN_STYLE_PROFILE__,
  actionProfile: __LOGIN_ACTION_PROFILE__,
  motionProfile: __LOGIN_MOTION_PROFILE__,
  titleHierarchyProfile: __LOGIN_TITLE_HIERARCHY_PROFILE__,
  subtitleToneProfile: __LOGIN_SUBTITLE_TONE_PROFILE__
};

function buildLoginStyles() {
  const dense = loginStyleConfig.density === "compact";
  const balancedActions = loginStyleConfig.actionProfile === "balanced_actions";
  const centeredHeader = loginStyleConfig.headerAlignment === "center";
  const animated = loginStyleConfig.motionProfile === "minimal";
  const strongTitle = loginStyleConfig.titleHierarchyProfile === "title_strong";
  const mutedSubtitle = loginStyleConfig.subtitleToneProfile === "subtitle_muted";

  return {
    page: {
      maxWidth: loginStyleConfig.containerVariant === "single_card" ? "560px" : "680px",
      margin: "0 auto",
      display: "grid",
      gap: dense ? "16px" : "20px",
      paddingTop: dense ? "32px" : "48px"
    },
    header: {
      textAlign: centeredHeader ? "center" : "left"
    } as const,
    title: {
      margin: 0,
      fontSize: strongTitle ? (dense ? "32px" : "36px") : (dense ? "28px" : "30px"),
      lineHeight: strongTitle ? 1.1 : 1.15,
      fontWeight: strongTitle ? 800 : 700,
      letterSpacing: strongTitle ? "-0.03em" : "-0.01em",
      color: "#0f172a"
    },
    subtitle: {
      margin: 0,
      marginTop: dense ? "6px" : "8px",
      fontSize: dense ? "15px" : "16px",
      lineHeight: 1.5,
      fontWeight: mutedSubtitle ? 400 : 500,
      color: mutedSubtitle ? "#64748b" : "#334155"
    },
    card: {
      border: "1px solid #dbe5f1",
      borderRadius: loginStyleConfig.styleProfile === "auth_centered_card_v1" ? "24px" : "20px",
      padding: dense ? "18px" : "24px",
      display: "grid",
      gap: dense ? "12px" : "16px",
      background: "linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)",
      boxShadow: "0 18px 48px rgba(15, 23, 42, 0.08)",
      transition: animated ? "transform 160ms ease, box-shadow 160ms ease" : "none"
    },
    input: {
      width: "100%",
      boxSizing: "border-box" as const,
      border: "1px solid #cbd5e1",
      borderRadius: "14px",
      padding: dense ? "10px 12px" : "12px 14px",
      background: "#ffffff",
      color: "#0f172a"
    },
    primaryButton: {
      border: "none",
      borderRadius: "16px",
      padding: dense ? "12px 16px" : "14px 18px",
      background: loginStyleConfig.actionEmphasis === "primary_strong" ? "#0f172a" : "#1d4ed8",
      color: "#ffffff",
      fontWeight: 700,
      cursor: "pointer"
    },
    secondaryButton: {
      border: balancedActions ? "1px solid #cbd5e1" : "1px solid #e2e8f0",
      borderRadius: "16px",
      padding: dense ? "12px 16px" : "14px 18px",
      background: "#ffffff",
      color: "#334155",
      fontWeight: balancedActions ? 600 : 500,
      cursor: "pointer"
    },
    hint: {
      fontSize: "13px",
      color: "#64748b"
    }
  };
}

function apiUrl(path: string): string {
  return `${apiBaseUrl}${path}`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

function makeId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `id-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function readStoredConversations(): Conversation[] {
  try {
    const raw = window.localStorage.getItem(storageKey);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Conversation[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function persistConversations(conversations: Conversation[]): void {
  window.localStorage.setItem(storageKey, JSON.stringify(conversations));
}

function readSessionToken(): string | null {
  try {
    const value = window.localStorage.getItem(authStorageKey);
    return value && value.trim() ? value : null;
  } catch {
    return null;
  }
}

function writeSessionToken(next: string | null): void {
  if (!next) {
    window.localStorage.removeItem(authStorageKey);
    return;
  }
  window.localStorage.setItem(authStorageKey, next);
}

function authHeaders(sessionToken: string | null): Record<string, string> {
  return sessionToken ? { [endpointConfig.auth.sessionHeader]: sessionToken } : {};
}

async function requestAuthSession(sessionToken: string | null): Promise<AuthSessionResponse> {
  return requestJson<AuthSessionResponse>(endpointConfig.auth.session, {
    method: endpointConfig.auth.sessionMethod,
    headers: authHeaders(sessionToken)
  });
}

async function startAuthSession(credentials?: LoginCredentials): Promise<AuthSessionResponse> {
  return requestJson<AuthSessionResponse>(endpointConfig.auth.login, {
    method: endpointConfig.auth.loginMethod,
    body: JSON.stringify({
      login_action: authRequestContractConfig.loginAction,
      username: credentials?.username ?? "",
      password: credentials?.password ?? ""
    })
  });
}

async function endAuthSession(sessionToken: string | null): Promise<void> {
  await requestJson(endpointConfig.auth.logout, {
    method: endpointConfig.auth.logoutMethod,
    headers: authHeaders(sessionToken)
  });
}

function useKnowledgeBases() {
  const [data, setData] = useState<KnowledgeBaseSummary[]>([]);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    requestJson<KnowledgeBaseSummary[]>(endpointConfig.knowledgeBases)
      .then((payload) => {
        if (!cancelled) {
          setData(payload);
          setError("");
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setError(err.message);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return { data, error, loading };
}

function AppShell({
  signedIn,
  onSignOut,
  children
}: {
  signedIn: boolean;
  onSignOut: () => Promise<void>;
  children: React.ReactNode;
}) {
  return (
    <div style={{ minHeight: "100vh", display: "grid", gridTemplateColumns: "280px 1fr", gap: "24px", padding: "24px" }}>
      <aside style={{ background: "#0f172a", color: "white", borderRadius: "24px", padding: "24px" }}>
        <div style={{ fontSize: "12px", opacity: 0.72, textTransform: "uppercase" }}>{appText.heroKicker}</div>
        <h1>{appText.heroTitle}</h1>
        <p style={{ color: "#cbd5e1", lineHeight: 1.6 }}>{appText.heroCopy}</p>
        <div style={{ display: "grid", gap: "8px", marginTop: "24px" }}>
          <Link to={routesConfig.workbench}>Chat</Link>
          <Link to={routesConfig.knowledgeList}>Knowledge Bases</Link>
          <Link to={routesConfig.login}>Login</Link>
        </div>
        <div style={{ marginTop: "24px", display: "grid", gap: "8px" }}>
          <div style={{ fontSize: "12px", color: "#cbd5e1" }}>{signedIn ? "Session active" : appText.loginGuard}</div>
          {signedIn ? <button onClick={() => void onSignOut()}>Sign out</button> : null}
        </div>
      </aside>
      <section style={{ background: "rgba(255,255,255,0.9)", borderRadius: "28px", padding: "24px" }}>{children}</section>
    </div>
  );
}

function StandaloneLayout({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "32px" }}>
      <section
        style={{
          width: "min(720px, 100%)",
          background: "rgba(255,255,255,0.92)",
          borderRadius: "32px",
          padding: "40px 32px",
          boxShadow: "0 20px 60px rgba(15, 23, 42, 0.08)"
        }}
        data-layout-runtime={pageShellConfig.layoutRuntime.standaloneShell}
      >
        {children}
      </section>
    </div>
  );
}

function LoginPage({ onLogin }: { onLogin: (credentials?: LoginCredentials) => Promise<void> }) {
  const navigate = useNavigate();
  const location = useLocation();
  const search = new URLSearchParams(location.search);
  const nextPath = search.get("next") || routesConfig.workbench;
  const loginStyles = buildLoginStyles();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const showCredentialFields = authEntryConfig.entryVariant === "username_password";

  return (
    <main style={loginStyles.page}>
      <header id="login_header" style={loginStyles.header}>
        {authShellConfig.showBrand ? (
          <div style={{ fontSize: "12px", color: "#64748b", textTransform: "uppercase" }}>{appText.chatTitle}</div>
        ) : null}
        <h2 style={loginStyles.title}>{appText.loginTitle}</h2>
        <p style={loginStyles.subtitle}>{appText.loginSubtitle}</p>
      </header>
      <section id="login_form" style={loginStyles.card}>
        {authShellConfig.showGuardMessage ? <div style={{ fontSize: "14px", color: "#475569" }}>{authShellConfig.guardMessage}</div> : null}
        {authShellConfig.showReturnHint ? (
          <div style={loginStyles.hint}>
            {__LOGIN_RESTORE_TARGET__ ? "登录成功后会返回原目标页面。" : "登录成功后会进入默认工作台。"}
          </div>
        ) : null}
        {error ? <div style={{ color: "#b91c1c", fontSize: "14px" }}>{error}</div> : null}
        {showCredentialFields ? (
          <div style={{ display: "grid", gap: "12px" }}>
            <label style={{ display: "grid", gap: "6px", color: "#334155", fontSize: "14px" }}>
              <span>用户名</span>
              <input
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                autoComplete="username"
                placeholder="请输入用户名"
                style={loginStyles.input}
              />
            </label>
            <label style={{ display: "grid", gap: "6px", color: "#334155", fontSize: "14px" }}>
              <span>密码</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                autoComplete="current-password"
                placeholder="请输入密码"
                style={loginStyles.input}
              />
            </label>
          </div>
        ) : null}
        <button
          style={loginStyles.primaryButton}
          disabled={submitting}
          onClick={() => {
            if (showCredentialFields && (!username.trim() || !password.trim())) {
              setError(authShellConfig.failureMessage);
              return;
            }
            setSubmitting(true);
            setError("");
            void onLogin(
              showCredentialFields
                ? {
                    username: username.trim(),
                    password
                  }
                : undefined
            )
              .then(() => {
                navigate(__LOGIN_RESTORE_TARGET__ ? nextPath : routesConfig.workbench, { replace: true });
              })
              .catch((err: Error) => {
                setError(err.message || authShellConfig.failureMessage);
              })
              .finally(() => {
                setSubmitting(false);
              });
          }}
        >
          {submitting ? "登录中..." : appText.loginPrimary}
        </button>
        {authShellConfig.showSecondaryAction ? (
          <button style={loginStyles.secondaryButton} onClick={() => navigate(routesConfig.home, { replace: true })}>
            {appText.loginSecondary}
          </button>
        ) : null}
      </section>
    </main>
  );
}

function ProtectedRoute({
  signedIn,
  authReady,
  children
}: {
  signedIn: boolean;
  authReady: boolean;
  children: React.ReactNode;
}) {
  const location = useLocation();
  if (!authReady) {
    return <div style={{ padding: "48px", color: "#64748b" }}>{authFlowConfig.sessionProbe === "required_on_protected_entry" ? "Checking session..." : "Preparing access..."}</div>;
  }
  if (!signedIn) {
    const next = `${location.pathname}${location.search}${location.hash}`;
    return <Navigate to={`${routesConfig.login}?next=${encodeURIComponent(next)}`} replace />;
  }
  return <>{children}</>;
}

function WorkspaceRoute({
  signedIn,
  authReady,
  onSignOut,
  children
}: {
  signedIn: boolean;
  authReady: boolean;
  onSignOut: () => Promise<void>;
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute signedIn={signedIn} authReady={authReady}>
      <AppShell signedIn={signedIn} onSignOut={onSignOut}>
        <div data-layout-runtime={pageShellConfig.layoutRuntime.workspaceShell}>{children}</div>
      </AppShell>
    </ProtectedRoute>
  );
}

function WorkbenchPage() {
  const kb = useKnowledgeBases();
  const [input, setInput] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>(() => {
    const stored = readStoredConversations();
    return stored.length ? stored : [{ id: "default", title: "New conversation", messages: [] }];
  });
  const [activeId, setActiveId] = useState<string>(() => {
    const stored = readStoredConversations();
    return stored.length ? stored[0].id : "default";
  });

  useEffect(() => {
    persistConversations(conversations);
  }, [conversations]);

  const activeConversation = useMemo(
    () => conversations.find((item) => item.id === activeId) ?? conversations[0],
    [activeId, conversations]
  );

  function updateConversation(conversationId: string, updater: (item: Conversation) => Conversation): void {
    setConversations((current) => current.map((item) => (item.id === conversationId ? updater(item) : item)));
  }

  async function sendMessage(): Promise<void> {
    const message = input.trim();
    if (!message || !activeConversation) return;
    updateConversation(activeConversation.id, (item) => ({
      ...item,
      title: item.messages.length === 0 ? message.slice(0, 24) : item.title,
      messages: [...item.messages, { id: makeId(), role: "user", text: message }]
    }));
    setInput("");
    try {
      const payload = await requestJson<ChatTurnResponse>(endpointConfig.chatTurns, {
        method: "POST",
        body: JSON.stringify({ message, document_id: null, section_id: null })
      });
      updateConversation(activeConversation.id, (item) => ({
        ...item,
        messages: [...item.messages, { id: makeId(), role: "assistant", text: payload.answer, citations: payload.citations }]
      }));
    } catch {
      updateConversation(activeConversation.id, (item) => ({
        ...item,
        messages: [...item.messages, { id: makeId(), role: "assistant", text: "The chat request failed. Check backend availability." }]
      }));
    }
  }

  return (
    <main>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "end", borderBottom: "1px solid #dbe5f1", paddingBottom: "16px" }}>
        <div>
          <div style={{ fontSize: "12px", color: "#64748b", textTransform: "uppercase" }}>{appText.chatTitle}</div>
          <h2>{activeConversation?.title ?? appText.title}</h2>
        </div>
        <Link to={routesConfig.knowledgeList}>Browse knowledge pages</Link>
      </header>
      <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: "24px", marginTop: "24px" }}>
        <aside>
          <button
            onClick={() => {
              const next = { id: makeId(), title: "New conversation", messages: [] as Message[] };
              setConversations((current) => [next, ...current]);
              setActiveId(next.id);
            }}
          >
            + New chat
          </button>
          <div style={{ display: "grid", gap: "8px", marginTop: "16px" }}>
            {conversations.map((item) => (
              <button key={item.id} onClick={() => setActiveId(item.id)} style={{ textAlign: "left" }}>
                {item.title}
              </button>
            ))}
          </div>
          <div style={{ marginTop: "16px", color: "#64748b" }}>
            <div>{kb.data[0]?.name ?? appText.libraryName}</div>
            <div style={{ fontSize: "12px", marginTop: "8px" }}>{appText.libraryDesc}</div>
          </div>
        </aside>
        <section>
          {activeConversation?.messages.length ? (
            <div style={{ display: "grid", gap: "16px" }}>
              {activeConversation.messages.map((message) => (
                <article key={message.id}>
                  <div style={{ fontSize: "12px", color: "#64748b", textTransform: "uppercase" }}>{message.role}</div>
                  <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.7 }}>{message.text}</div>
                  {message.citations?.length ? (
                    <div style={{ marginTop: "8px", color: "#2563eb" }}>
                      {message.citations.map((item, index) => `[${index + 1}] ${item.document_title}`).join(" / ")}
                    </div>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <div>
              <div style={{ fontSize: "12px", color: "#64748b", textTransform: "uppercase" }}>{appText.emptyTitle}</div>
              <h3>{appText.heroTitle}</h3>
              <p>{appText.emptyCopy}</p>
              <div style={{ display: "grid", gap: "8px", marginTop: "16px" }}>
                {appText.welcomePrompts.map((prompt: string) => (
                  <button key={prompt} onClick={() => setInput(prompt)} style={{ textAlign: "left" }}>
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}
          <div style={{ marginTop: "24px", borderTop: "1px solid #dbe5f1", paddingTop: "16px" }}>
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder={appText.placeholder}
              rows={5}
              style={{ width: "100%" }}
            />
            <div style={{ marginTop: "12px", display: "flex", justifyContent: "space-between" }}>
              <span>{kb.data[0]?.name ?? appText.libraryName}</span>
              <button onClick={() => void sendMessage()}>Send</button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function KnowledgeBaseListPage() {
  const kb = useKnowledgeBases();
  return (
    <main>
      <h2>{appText.libraryTitle}</h2>
      {kb.loading ? <p>Loading...</p> : null}
      {kb.error ? <p>{kb.error}</p> : null}
      <div style={{ display: "grid", gap: "16px" }}>
        {kb.data.map((item) => (
          <article key={item.knowledge_base_id}>
            <h3>{item.name}</h3>
            <p>{item.description}</p>
            <Link to={routesConfig.knowledgeDetail.replace(":knowledgeBaseId", item.knowledge_base_id)}>Open detail</Link>
          </article>
        ))}
      </div>
    </main>
  );
}

function KnowledgeBaseDetailPage() {
  const params = useParams();
  const knowledgeBaseId = params.knowledgeBaseId ?? appText.knowledgeBaseId;
  const [data, setData] = useState<KnowledgeBaseDetail | null>(null);

  useEffect(() => {
    void requestJson<KnowledgeBaseDetail>(`${endpointConfig.knowledgeBaseDetailPrefix}/${knowledgeBaseId}`).then(setData);
  }, [knowledgeBaseId]);

  return (
    <main>
      <h2>{data?.name ?? appText.libraryName}</h2>
      <p>{data?.description ?? appText.libraryDesc}</p>
      <div style={{ display: "grid", gap: "16px" }}>
        {data?.documents.map((document) => (
          <article key={document.document_id}>
            <h3>{document.title}</h3>
            <p>{document.summary}</p>
            <Link to={routesConfig.documentDetail.replace(":documentId", document.document_id)}>Open document</Link>
          </article>
        ))}
      </div>
    </main>
  );
}

function DocumentDetailPage() {
  const params = useParams();
  const documentId = params.documentId ?? "";
  const [data, setData] = useState<KnowledgeDocumentDetail | null>(null);

  useEffect(() => {
    if (!documentId) return;
    void requestJson<KnowledgeDocumentDetail>(`${endpointConfig.documentDetailPrefix}/${documentId}`).then(setData);
  }, [documentId]);

  return (
    <main>
      <h2>{appText.previewTitle}</h2>
      <h3>{data?.title}</h3>
      <div style={{ display: "grid", gap: "16px" }}>
        {data?.sections.map((section) => (
          <section key={section.section_id}>
            <h4>{section.title}</h4>
            <div dangerouslySetInnerHTML={{ __html: section.html }} />
          </section>
        ))}
      </div>
    </main>
  );
}

export default function App() {
  const [sessionToken, setSessionToken] = useState<string | null>(() => readSessionToken());
  const [signedIn, setSignedIn] = useState(false);
  const [authReady, setAuthReady] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const nextToken = readSessionToken();
    if (!nextToken) {
      setSignedIn(false);
      setAuthReady(true);
      return () => {
        cancelled = true;
      };
    }
    void requestAuthSession(nextToken)
      .then((payload) => {
        if (cancelled) return;
        if (payload.signed_in && payload.session_token) {
          writeSessionToken(payload.session_token);
          setSessionToken(payload.session_token);
          setSignedIn(true);
          return;
        }
        writeSessionToken(null);
        setSessionToken(null);
        setSignedIn(false);
      })
      .catch(() => {
        if (cancelled) return;
        writeSessionToken(null);
        setSessionToken(null);
        setSignedIn(false);
      })
      .finally(() => {
        if (!cancelled) {
          setAuthReady(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleLogin(credentials?: LoginCredentials): Promise<void> {
    const payload = await startAuthSession(credentials);
    if (!payload.signed_in || !payload.session_token) {
      throw new Error("登录失败，请稍后重试。");
    }
    writeSessionToken(payload.session_token);
    setSessionToken(payload.session_token);
    setSignedIn(true);
    setAuthReady(true);
  }

  async function handleSignOut(): Promise<void> {
    try {
      await endAuthSession(sessionToken);
    } finally {
      writeSessionToken(null);
      setSessionToken(null);
      setSignedIn(false);
      setAuthReady(true);
    }
  }

  if (!authReady) {
    return <div style={{ minHeight: "100vh", display: "grid", placeItems: "center", color: "#64748b" }}>{authShellConfig.expiredMessage}</div>;
  }

  return (
    <Routes>
      <Route path={routesConfig.home} element={<Navigate to={signedIn ? routesConfig.workbench : routesConfig.login} replace />} />
      <Route
        path={routesConfig.login}
        element={
          <StandaloneLayout>
            <LoginPage onLogin={handleLogin} />
          </StandaloneLayout>
        }
      />
      <Route
        path={routesConfig.workbench}
        element={
          <WorkspaceRoute signedIn={signedIn} authReady={authReady} onSignOut={handleSignOut}>
            <WorkbenchPage />
          </WorkspaceRoute>
        }
      />
      <Route
        path={routesConfig.knowledgeList}
        element={
          <WorkspaceRoute signedIn={signedIn} authReady={authReady} onSignOut={handleSignOut}>
            <KnowledgeBaseListPage />
          </WorkspaceRoute>
        }
      />
      <Route
        path={routesConfig.knowledgeDetail}
        element={
          <WorkspaceRoute signedIn={signedIn} authReady={authReady} onSignOut={handleSignOut}>
            <KnowledgeBaseDetailPage />
          </WorkspaceRoute>
        }
      />
      <Route
        path={routesConfig.documentDetail}
        element={
          <WorkspaceRoute signedIn={signedIn} authReady={authReady} onSignOut={handleSignOut}>
            <DocumentDetailPage />
          </WorkspaceRoute>
        }
      />
    </Routes>
  );
}
"""

    for key, value in placeholders.items():
        template = template.replace(key, value)
    return template
