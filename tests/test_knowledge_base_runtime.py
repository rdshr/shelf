from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from knowledge_base_runtime.app import build_knowledge_base_runtime_app


class KnowledgeBaseRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(build_knowledge_base_runtime_app())

    def test_frontend_page_contains_chat_first_regions(self) -> None:
        response = self.client.get("/knowledge-base")
        self.assertEqual(response.status_code, 200)
        self.assertIn("今天想了解什么？", response.text)
        self.assertIn("历史会话", response.text)
        self.assertIn("切换知识库", response.text)
        self.assertIn("浏览知识库与文档", response.text)
        self.assertIn('button.dataset.navId = "conversation-item";', response.text)
        self.assertNotIn('button.id = "conversation-item";', response.text)
        self.assertIn("gap: var(--shell-gap);", response.text)

    def test_auxiliary_pages_exist(self) -> None:
        list_response = self.client.get("/knowledge-bases")
        self.assertEqual(list_response.status_code, 200)
        self.assertIn("知识库列表", list_response.text)
        self.assertIn("用此知识库开始聊天", list_response.text)

        detail_response = self.client.get("/knowledge-bases/details/research-and-standards")
        self.assertEqual(detail_response.status_code, 200)
        self.assertIn("研发规范知识库", detail_response.text)
        self.assertIn("查看文档详情", detail_response.text)

        document_response = self.client.get("/knowledge-bases/details/documents/chat-client-principles")
        self.assertEqual(document_response.status_code, 200)
        self.assertIn("Chat Client Principles", document_response.text)
        self.assertIn("Chat First", document_response.text)

    def test_root_exposes_project_summary(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["project"]["project"]["project_id"], "knowledge_base_basic")
        self.assertEqual(payload["frontend"], "/knowledge-base")
        self.assertEqual(payload["product_spec"], "/api/knowledge/product-spec")
        self.assertIn("chat_home", payload["project"]["ui_spec_summary"]["page_ids"])
        self.assertEqual(payload["project"]["backend_spec_summary"]["answer_policy"]["citation_style"], "inline_refs")

    def test_knowledge_base_endpoints_exist(self) -> None:
        response = self.client.get("/api/knowledge/knowledge-bases")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["knowledge_base_id"], "research-and-standards")

        detail_response = self.client.get("/api/knowledge/knowledge-bases/research-and-standards")
        self.assertEqual(detail_response.status_code, 200)
        detail = detail_response.json()
        self.assertEqual(detail["knowledge_base_id"], "research-and-standards")
        self.assertGreaterEqual(len(detail["documents"]), 1)

    def test_list_documents_supports_filtering(self) -> None:
        response = self.client.get("/api/knowledge/documents", params={"tag": "framework"})
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertGreaterEqual(len(payload), 1)
        self.assertTrue(all("framework" in item["tags"] for item in payload))

    def test_get_document_detail_and_section(self) -> None:
        response = self.client.get("/api/knowledge/documents/framework-compilation-chain")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["document_id"], "framework-compilation-chain")
        self.assertGreaterEqual(len(payload["sections"]), 2)

        section_response = self.client.get(
            "/api/knowledge/documents/framework-compilation-chain/sections/generated-runtime"
        )
        self.assertEqual(section_response.status_code, 200)
        section = section_response.json()
        self.assertEqual(section["section_id"], "generated-runtime")
        self.assertIn("generated bundle", section["plain_text"])

    def test_create_and_delete_document(self) -> None:
        create_response = self.client.post(
            "/api/knowledge/documents",
            json={
                "title": "Uploaded Source",
                "summary": "A source added from the chat-first client should become searchable, citeable, and visible in detail pages.",
                "tags": ["upload", "knowledge-base"],
                "body_markdown": "## Source Contract\\nUploaded files become previewable and citeable.\\n\\n## Return Path\\nCitations still reopen source context and document detail pages.",
            },
        )
        self.assertEqual(create_response.status_code, 201)
        created = create_response.json()
        self.assertEqual(created["title"], "Uploaded Source")

        list_response = self.client.get("/api/knowledge/documents", params={"query": "uploaded"})
        self.assertEqual(list_response.status_code, 200)
        listed = list_response.json()
        self.assertEqual(listed[0]["document_id"], created["document_id"])

        delete_response = self.client.delete(f"/api/knowledge/documents/{created['document_id']}")
        self.assertEqual(delete_response.status_code, 200)
        deleted = delete_response.json()
        self.assertTrue(deleted["deleted"])

        missing_response = self.client.get(f"/api/knowledge/documents/{created['document_id']}")
        self.assertEqual(missing_response.status_code, 404)

    def test_chat_turn_returns_citations_with_return_paths(self) -> None:
        response = self.client.post(
            "/api/knowledge/chat/turns",
            json={
                "message": "Explain the generated runtime and citation drawer.",
                "document_id": "framework-compilation-chain",
                "section_id": "generated-runtime",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("[1]", payload["answer"])
        self.assertGreaterEqual(len(payload["citations"]), 1)
        self.assertEqual(payload["citations"][0]["document_id"], "framework-compilation-chain")
        self.assertIn("/knowledge-base?document=framework-compilation-chain", payload["citations"][0]["return_path"])
        self.assertIn(
            "/knowledge-bases/details/documents/framework-compilation-chain",
            payload["citations"][0]["document_path"],
        )

    def test_product_spec_endpoint_exposes_compiled_product_truth(self) -> None:
        response = self.client.get("/api/knowledge/product-spec")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["product"]["project_id"], "knowledge_base_basic")
        self.assertEqual(payload["navigation"]["pages"]["chat_home"], "/knowledge-base")
        self.assertEqual(payload["library"]["knowledge_base_id"], "research-and-standards")
        self.assertEqual(payload["chat"]["citation_style"], "inline_refs")
        self.assertEqual(payload["interaction_model"]["workspace_flow"][0]["stage_id"], "knowledge_base_select")
        self.assertEqual(payload["interaction_model"]["citation_return"]["query_keys"], ["document", "section", "citation"])
        self.assertNotIn("ui_spec", payload)
        self.assertNotIn("backend_spec", payload)


if __name__ == "__main__":
    unittest.main()
