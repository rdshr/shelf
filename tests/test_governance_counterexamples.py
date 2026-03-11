from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator
from unittest.mock import patch
import unittest

from fastapi.routing import APIRoute

from project_runtime.governance import build_governance_tree, compare_project_to_tree, validate_tree_closure
from project_runtime.knowledge_base import DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE, KnowledgeBaseProject, load_knowledge_base_project


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_FILE = REPO_ROOT / "src/knowledge_base_runtime/app.py"


@contextmanager
def _temporary_file_text(path: Path, new_text: str) -> Iterator[None]:
    original = path.read_text(encoding="utf-8")
    path.write_text(new_text, encoding="utf-8")
    try:
        yield
    finally:
        path.write_text(original, encoding="utf-8")


class GovernanceCounterexampleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)
        self.tree_payload = build_governance_tree(self.project)

    def test_route_path_drift_fails_with_expectation_mismatch(self) -> None:
        import knowledge_base_runtime.app as runtime_app_module

        original_builder = runtime_app_module.build_knowledge_base_runtime_app

        def drifted_builder(project: KnowledgeBaseProject | None = None):
            app = original_builder(project)
            for route in app.routes:
                if isinstance(route, APIRoute) and route.endpoint.__name__ == "root":
                    route.path = "/drifted-home"
                    route.path_format = "/drifted-home"
                    break
            return app

        with patch.object(runtime_app_module, "build_knowledge_base_runtime_app", drifted_builder):
            issues = compare_project_to_tree(self.project, self.tree_payload)
        self.assertTrue(
            any(
                issue["code"] == "EXPECTATION_MISMATCH"
                and issue.get("symbol_id") == "kb.runtime.page_routes"
                for issue in issues
            )
        )

    def test_response_contract_drift_fails_with_expectation_mismatch(self) -> None:
        import knowledge_base_runtime.backend as backend_module

        original_builder = backend_module.build_knowledge_base_router

        def drifted_builder(project=None, repository=None):
            router = original_builder(project, repository)
            for route in router.routes:
                if isinstance(route, APIRoute) and route.endpoint.__name__ == "create_chat_turn":
                    route.response_model = backend_module.KnowledgeDocumentDeleteResponse
                    break
            return router

        with patch.object(backend_module, "build_knowledge_base_router", drifted_builder):
            issues = compare_project_to_tree(self.project, self.tree_payload)
        self.assertTrue(
            any(
                issue["code"] == "EXPECTATION_MISMATCH"
                and issue.get("symbol_id") == "kb.api.chat_contract"
                for issue in issues
            )
        )

    def test_answer_behavior_drift_fails_with_expectation_mismatch(self) -> None:
        import knowledge_base_runtime.backend as backend_module

        def drifted_answer_question(self, message: str, document_id: str | None = None, section_id: str | None = None):
            citation = backend_module.KnowledgeCitationResponse(
                citation_id="1",
                document_id="framework-compilation-chain",
                document_title="Framework Compilation Chain",
                section_id="generated-runtime",
                section_title="Generated Runtime",
                snippet="drifted snippet",
                return_path="/broken-path",
                document_path="/broken-document",
            )
            return backend_module.KnowledgeChatTurnResponse(
                answer="No inline refs here.",
                citations=[citation],
                context_document_id=None,
                context_section_id=None,
            )

        with patch.object(backend_module.KnowledgeRepository, "answer_question", drifted_answer_question):
            issues = compare_project_to_tree(self.project, self.tree_payload)
        self.assertTrue(
            any(
                issue["code"] == "EXPECTATION_MISMATCH"
                and issue.get("symbol_id") == "kb.answer.behavior"
                for issue in issues
            )
        )

    def test_new_high_risk_route_without_binding_fails(self) -> None:
        original = APP_FILE.read_text(encoding="utf-8")
        injected = original.replace(
            "    return app\n",
            "\n    @app.get('/ai-drift-probe', include_in_schema=False)\n"
            "    def ai_drift_probe() -> dict[str, str]:\n"
            "        return {'status': 'drift'}\n\n"
            "    return app\n",
        )
        with _temporary_file_text(APP_FILE, injected):
            issues = compare_project_to_tree(self.project, self.tree_payload)
        self.assertTrue(any(issue["code"] == "MISSING_BINDING" for issue in issues))

    def test_dead_config_effect_fails(self) -> None:
        original_runtime_bundle = KnowledgeBaseProject.to_runtime_bundle_dict

        def drifted_runtime_bundle(self: KnowledgeBaseProject):
            payload = original_runtime_bundle(self)
            backend_spec = dict(payload["backend_spec"])
            transport = dict(backend_spec["transport"])
            transport["mode"] = "broken_transport"
            backend_spec["transport"] = transport
            payload["backend_spec"] = backend_spec
            return payload

        with patch.object(KnowledgeBaseProject, "to_runtime_bundle_dict", drifted_runtime_bundle):
            issues = compare_project_to_tree(self.project, self.tree_payload)
        self.assertTrue(
            any(
                issue["code"] == "DEAD_CONFIG_EFFECT"
                and issue.get("symbol_id") == "knowledge_base_basic.config_effect.backend.transport"
                for issue in issues
            )
        )

    def test_generated_provenance_drift_fails(self) -> None:
        payload = build_governance_tree(self.project)
        payload["upstream_closure"][0]["digest"] = "sha256:deadbeef"
        issues = validate_tree_closure(payload)
        self.assertTrue(any(issue["code"] == "STALE_EVIDENCE" for issue in issues))


if __name__ == "__main__":
    unittest.main()
