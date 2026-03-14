from __future__ import annotations

import importlib
from pathlib import Path
import tempfile
import textwrap
import unittest

from fastapi.testclient import TestClient

from project_runtime import (
    get_default_project_template_registration,
    iter_project_template_registrations,
    resolve_project_template_registration,
)
from project_runtime.app_factory import build_project_app
from project_runtime.knowledge_base import (
    DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE,
    load_knowledge_base_project,
)


DEFAULT_IMPLEMENTATION_CONFIG = textwrap.dedent(
    """
    [frontend]
    renderer = "knowledge_chat_client_v1"
    style_profile = "knowledge_chat_web_v1"
    script_profile = "knowledge_chat_browser_v1"

    [backend]
    renderer = "knowledge_chat_backend_v1"
    transport = "http_json"
    retrieval_strategy = "retrieval_stub"

    [evidence]
    product_spec_endpoint = "/api/public-knowledge/product-spec"

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
).strip()


class ProjectRuntimeTest(unittest.TestCase):
    def test_src_package_import_keeps_template_registry_idempotent(self) -> None:
        before = iter_project_template_registrations()

        importlib.import_module("src.project_runtime")

        after = iter_project_template_registrations()
        self.assertEqual(len(before), len(after))
        self.assertEqual(tuple(item.template_id for item in before), tuple(item.template_id for item in after))

    def test_template_registry_resolves_default_project(self) -> None:
        default_registration = get_default_project_template_registration()
        resolved_registration = resolve_project_template_registration(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)

        self.assertEqual(default_registration.template_id, "knowledge_base_workbench")
        self.assertEqual(resolved_registration.template_id, default_registration.template_id)
        self.assertEqual(
            resolved_registration.default_product_spec_file.resolve(),
            DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE.resolve(),
        )
        self.assertIn("project", resolved_registration.product_spec_layout.required_top_level_keys)
        self.assertIn("showcase_page", resolved_registration.product_spec_layout.required_top_level_keys)
        self.assertIn("frontend", resolved_registration.implementation_config_layout.required_top_level_keys)

    def test_load_default_product_spec(self) -> None:
        project = load_knowledge_base_project(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE)

        self.assertEqual(project.metadata.project_id, "knowledge_base_basic")
        self.assertEqual(project.metadata.template, "knowledge_base_workbench")
        self.assertEqual(project.template_contract.template_id, project.metadata.template)
        self.assertEqual(project.route.workbench, "/knowledge-base")
        self.assertEqual(project.route.basketball_showcase, "/knowledge-base/cxk-basketball")
        self.assertEqual(project.route.knowledge_list, "/knowledge-bases")
        self.assertEqual(project.route.api_prefix, "/api/knowledge")
        self.assertEqual(project.surface.layout_variant, "chatgpt_knowledge_client")
        self.assertIn(project.implementation.frontend.renderer, project.template_contract.supported_frontend_renderers)
        self.assertEqual(project.visual.brand, "Shelf")
        self.assertEqual(len(project.documents), 3)
        self.assertTrue(project.features.upload)
        self.assertEqual(project.frontend_ir.module_id, "frontend.L2.M0")
        self.assertEqual(project.domain_ir.module_id, "knowledge_base.L2.M0")
        self.assertEqual(project.backend_ir.module_id, "backend.L2.M0")
        self.assertGreaterEqual(len(project.resolved_modules), 3)
        self.assertEqual(project.frontend_contract["shell"], "conversation_sidebar_shell")
        self.assertEqual(project.workbench_contract["flow"][0]["stage_id"], "knowledge_base_select")
        self.assertEqual(project.ui_spec["pages"]["knowledge_list"]["title"], project.surface.copy.library_title)
        self.assertEqual(project.ui_spec["components"]["chat_composer"]["submit_label"], "发送")
        self.assertEqual(project.backend_spec["return_policy"]["chat_path"], "/knowledge-base")
        self.assertEqual(project.backend_spec["interaction_copy"]["loading_text"], "正在检索知识库并整理回答…")
        self.assertEqual(project.visual_tokens["bg"], project.template_contract.style_profiles.surface_presets["light"].bg)
        self.assertEqual(project.visual_tokens["message_width"], project.template_contract.style_profiles.message_width)
        self.assertTrue(project.validation_reports.passed)

        product_spec = project.to_product_spec_dict()
        self.assertEqual(product_spec["product"]["project_id"], "knowledge_base_basic")
        self.assertEqual(product_spec["navigation"]["pages"]["chat_home"], "/knowledge-base")
        self.assertEqual(product_spec["showcase_page"]["title"], "蔡徐坤打球特别页")
        self.assertNotIn("ui_spec", product_spec)
        self.assertNotIn("backend_spec", product_spec)

        runtime_bundle = project.to_runtime_bundle_dict()
        self.assertEqual(runtime_bundle["product_spec"]["product"]["project_id"], "knowledge_base_basic")
        self.assertEqual(runtime_bundle["routes"]["api"]["knowledge_bases"], "/api/knowledge/knowledge-bases")
        self.assertIn("ui_spec", runtime_bundle)
        self.assertIn("backend_spec", runtime_bundle)

    def test_generic_project_app_factory_materializes_generated_artifacts(self) -> None:
        client = TestClient(build_project_app(DEFAULT_KNOWLEDGE_BASE_PRODUCT_SPEC_FILE))

        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["project"]["project"]["project_id"], "knowledge_base_basic")
        self.assertEqual(payload["frontend"], "/knowledge-base")
        self.assertEqual(payload["product_spec"], "/api/knowledge/product-spec")
        self.assertEqual(payload["project"]["routes"]["api"]["knowledge_bases"], "/api/knowledge/knowledge-bases")
        self.assertEqual(payload["project"]["routes"]["pages"]["knowledge_list"], "/knowledge-bases")
        generated = payload["project"]["generated_artifacts"]
        self.assertIsNotNone(generated)
        assert generated is not None
        self.assertTrue(payload["project"]["validation_reports"]["overall"]["passed"])
        for rel_path in generated.values():
            self.assertTrue((Path.cwd() / rel_path).exists())

    def test_custom_product_spec_changes_routes_theme_and_generated_bundle(self) -> None:
        product_spec_toml = textwrap.dedent(
            """
            [project]
            project_id = "knowledge_base_public"
            template = "knowledge_base_workbench"
            display_name = "Knowledge Base Public"
            description = "A public knowledge chat product compiled from the same framework."
            version = "0.3.0"

            [framework]
            frontend = "framework/frontend/L2-M0-前端框架标准模块.md"
            domain = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"
            backend = "framework/backend/L2-M0-知识库接口框架标准模块.md"
            preset = "document_chat_workbench"

            [surface]
            shell = "conversation_sidebar_shell"
            layout_variant = "chatgpt_knowledge_client"
            sidebar_width = "compact"
            preview_mode = "drawer"
            density = "comfortable"

            [surface.copy]
            hero_kicker = "Public Product"
            hero_title = "Knowledge Base Public"
            hero_copy = "A public knowledge chat client compiled from the same framework."
            library_title = "Knowledge Bases"
            preview_title = "Citation Sources"
            toc_title = "Source Sections"
            chat_title = "Public Chat"
            empty_state_title = "Start a public conversation"
            empty_state_copy = "Ask directly in the composer. Sources open only when requested."

            [visual]
            brand = "Public KB"
            accent = "#1357be"
            surface_preset = "light"
            radius_scale = "lg"
            shadow_level = "md"
            font_scale = "md"

            [route]
            home = "/"
            workbench = "/public-knowledge"
            basketball_showcase = "/public-knowledge/cxk-basketball"
            knowledge_list = "/public-knowledge/bases"
            knowledge_detail = "/public-knowledge/bases/details"
            document_detail_prefix = "/public-knowledge/bases/details/documents"
            api_prefix = "/api/public-knowledge"

            [showcase_page]
            title = "Public Showcase"
            kicker = "Public Highlight"
            headline = "Public Basketball Showcase"
            intro = "A lightweight themed page that still stays inside the same governed knowledge-base tree."
            back_to_chat_label = "Back to chat"
            browse_knowledge_label = "Browse knowledge bases"

            [a11y]
            reading_order = ["conversation_sidebar", "chat_header", "message_stream", "chat_composer", "citation_drawer"]
            keyboard_nav = ["new-chat", "conversation-item", "chat-input", "citation-ref", "citation-drawer-close"]
            announcements = ["current knowledge base", "active conversation", "citation source opened"]

            [library]
            knowledge_base_id = "public-guidance"
            knowledge_base_name = "Public Guidance"
            knowledge_base_description = "A public knowledge base rendered through the same chat-first framework."
            enabled = true
            source_types = ["markdown"]
            metadata_fields = ["title", "tags", "updated_at"]
            default_focus = "current_knowledge_base"
            list_variant = "conversation_companion"
            allow_create = false
            allow_delete = false

            [library.copy]
            search_placeholder = "Search public files"

            [preview]
            enabled = true
            renderers = ["markdown"]
            anchor_mode = "heading"
            show_toc = true
            preview_variant = "citation_drawer"

            [chat]
            enabled = true
            citations_enabled = true
            mode = "retrieval_stub"
            citation_style = "inline_refs"
            bubble_variant = "assistant_soft"
            composer_variant = "chatgpt_compact"
            system_prompt = "Answer from the current public knowledge base and cite concrete sections."
            welcome_prompts = ["Explain the return path", "Summarize the framework chain"]

            [chat.copy]
            placeholder = "Ask the public knowledge base"
            welcome = "Ask a question and expect inline citations."

            [context]
            selection_mode = "knowledge_base_default"
            max_citations = 2
            max_preview_sections = 8
            sticky_document = false

            [return]
            enabled = true
            targets = ["citation_drawer", "document_detail"]
            anchor_restore = true
            citation_card_variant = "chips"

            [[documents]]
            document_id = "public-guidance"
            title = "Public Guidance"
            summary = "A public product still uses the same framework chain and source return loop."
            tags = ["public", "framework"]
            updated_at = "2026-03-08"
            body_markdown = \"\"\"
            ## Public Contract
            The public client keeps one conversation sidebar, one chat main region, and one citation drawer.

            ## Return Path
            Citations still reopen source context and document detail pages.
            \"\"\"
            """
        ).strip()

        with tempfile.TemporaryDirectory() as temp_dir:
            product_spec_file = Path(temp_dir) / "product_spec.toml"
            implementation_config_file = Path(temp_dir) / "implementation_config.toml"
            product_spec_file.write_text(product_spec_toml, encoding="utf-8")
            implementation_config_file.write_text(DEFAULT_IMPLEMENTATION_CONFIG, encoding="utf-8")

            project = load_knowledge_base_project(product_spec_file)
            self.assertEqual(project.visual.brand, "Public KB")
            self.assertEqual(project.route.workbench, "/public-knowledge")
            self.assertEqual(project.route.basketball_showcase, "/public-knowledge/cxk-basketball")
            self.assertEqual(project.route.knowledge_list, "/public-knowledge/bases")
            self.assertEqual(len(project.documents), 1)
            self.assertEqual(project.ui_spec["pages"]["chat_home"]["title"], "Knowledge Base Public")
            self.assertEqual(project.ui_spec["pages"]["basketball_showcase"]["title"], "Public Showcase")
            self.assertEqual(
                project.backend_spec["return_policy"]["document_detail_path"],
                "/public-knowledge/bases/details/documents/{document_id}",
            )
            self.assertTrue(project.validation_reports.passed)

            client = TestClient(build_project_app(product_spec_file))

            root_response = client.get("/")
            self.assertEqual(root_response.status_code, 200)
            root_payload = root_response.json()
            self.assertEqual(root_payload["frontend"], "/public-knowledge")
            self.assertEqual(root_payload["product_spec"], "/api/public-knowledge/product-spec")
            generated = root_payload["project"]["generated_artifacts"]
            self.assertIsNotNone(generated)
            assert generated is not None
            self.assertTrue((product_spec_file.parent / "generated" / "implementation_bundle.py").exists())

            page_response = client.get("/public-knowledge")
            self.assertEqual(page_response.status_code, 200)
            self.assertIn("今天想了解什么？", page_response.text)
            self.assertIn("Knowledge Base Public", page_response.text)

            showcase_response = client.get("/public-knowledge/cxk-basketball")
            self.assertEqual(showcase_response.status_code, 200)
            self.assertIn("Public Showcase", showcase_response.text)

            knowledge_base_response = client.get("/api/public-knowledge/knowledge-bases")
            self.assertEqual(knowledge_base_response.status_code, 200)
            self.assertEqual(knowledge_base_response.json()[0]["knowledge_base_id"], "public-guidance")

            documents_response = client.get("/api/public-knowledge/documents")
            self.assertEqual(documents_response.status_code, 200)
            documents = documents_response.json()
            self.assertEqual(len(documents), 1)
            self.assertEqual(documents[0]["document_id"], "public-guidance")

            chat_response = client.post(
                "/api/public-knowledge/chat/turns",
                json={
                    "message": "How does the return path work?",
                    "document_id": "public-guidance",
                    "section_id": "return-path",
                },
            )
            self.assertEqual(chat_response.status_code, 200)
            chat_payload = chat_response.json()
            self.assertTrue(chat_payload["citations"])
            self.assertIn("/public-knowledge?document=public-guidance&section=return-path", chat_payload["citations"][0]["return_path"])
            self.assertIn(
                "/public-knowledge/bases/details/documents/public-guidance",
                chat_payload["citations"][0]["document_path"],
            )

    def test_rule_validation_rejects_non_conforming_product_values(self) -> None:
        invalid_product_spec = textwrap.dedent(
            """
            [project]
            project_id = "knowledge_base_invalid"
            template = "knowledge_base_workbench"
            display_name = "Knowledge Base Invalid"
            description = "A product spec that violates the framework rule chain."
            version = "0.3.0"

            [framework]
            frontend = "framework/frontend/L2-M0-前端框架标准模块.md"
            domain = "framework/knowledge_base/L2-M0-知识库工作台场景模块.md"
            backend = "framework/backend/L2-M0-知识库接口框架标准模块.md"
            preset = "document_chat_workbench"

            [surface]
            shell = "conversation_sidebar_shell"
            layout_variant = "chatgpt_knowledge_client"
            sidebar_width = "md"
            preview_mode = "drawer"
            density = "comfortable"

            [surface.copy]
            hero_kicker = "Invalid Product"
            hero_title = "Knowledge Base Invalid"
            hero_copy = "A product spec that violates the framework rule chain."
            library_title = "Knowledge Bases"
            preview_title = "Citation Sources"
            toc_title = "Source Sections"
            chat_title = "Knowledge Chat"
            empty_state_title = "Start a conversation"
            empty_state_copy = "Sources open only on demand."

            [visual]
            brand = "Invalid KB"
            accent = "#880000"
            surface_preset = "light"
            radius_scale = "md"
            shadow_level = "md"
            font_scale = "md"

            [route]
            home = "/"
            workbench = "/invalid"
            basketball_showcase = "/invalid/cxk-basketball"
            knowledge_list = "/invalid/bases"
            knowledge_detail = "/invalid/bases/details"
            document_detail_prefix = "/invalid/bases/details/documents"
            api_prefix = "/api/invalid"

            [showcase_page]
            title = "Invalid Showcase"
            kicker = "Invalid Highlight"
            headline = "Invalid Basketball Showcase"
            intro = "Even the invalid fixture must still declare the product-facing themed page."
            back_to_chat_label = "Back to chat"
            browse_knowledge_label = "Browse knowledge bases"

            [a11y]
            reading_order = ["conversation_sidebar", "chat_header", "message_stream", "chat_composer", "citation_drawer"]
            keyboard_nav = ["new-chat", "conversation-item", "chat-input", "citation-ref", "citation-drawer-close"]
            announcements = ["current knowledge base", "active conversation", "citation source opened"]

            [library]
            knowledge_base_id = "invalid-doc"
            knowledge_base_name = "Invalid KB"
            knowledge_base_description = "Invalid configuration."
            enabled = true
            source_types = ["markdown"]
            metadata_fields = ["title", "tags", "updated_at"]
            default_focus = "current_knowledge_base"
            list_variant = "conversation_companion"
            allow_create = false
            allow_delete = false

            [library.copy]
            search_placeholder = "Search files"

            [preview]
            enabled = true
            renderers = ["markdown"]
            anchor_mode = "heading"
            show_toc = true
            preview_variant = "citation_drawer"

            [chat]
            enabled = true
            citations_enabled = true
            mode = "retrieval_stub"
            citation_style = "inline_refs"
            bubble_variant = "assistant_soft"
            composer_variant = "chatgpt_compact"
            system_prompt = "Answer from the selected document."
            welcome_prompts = ["Explain the invalid setup"]

            [chat.copy]
            placeholder = "Ask the selected document"
            welcome = "Ask a question and expect citations."

            [context]
            selection_mode = "knowledge_base_default"
            max_citations = 2
            max_preview_sections = 8
            sticky_document = false

            [return]
            enabled = true
            targets = ["citation_drawer", "document_detail"]
            anchor_restore = true
            citation_card_variant = "orbit"

            [[documents]]
            document_id = "invalid-doc"
            title = "Invalid Doc"
            summary = "This document still has anchors and citations but the return variant is unsupported."
            tags = ["invalid", "framework"]
            updated_at = "2026-03-08"
            body_markdown = \"\"\"
            ## Wrong Return
            The document body still has headings.

            ## Context
            Citations still return to anchors.
            \"\"\"
            """
        ).strip()

        with tempfile.TemporaryDirectory() as temp_dir:
            product_spec_file = Path(temp_dir) / "product_spec.toml"
            implementation_config_file = Path(temp_dir) / "implementation_config.toml"
            product_spec_file.write_text(invalid_product_spec, encoding="utf-8")
            implementation_config_file.write_text(DEFAULT_IMPLEMENTATION_CONFIG.replace("/api/public-knowledge", "/api/invalid"), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "knowledge_base\\.R4"):
                load_knowledge_base_project(product_spec_file)


if __name__ == "__main__":
    unittest.main()
