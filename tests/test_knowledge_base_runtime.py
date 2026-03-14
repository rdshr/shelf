from __future__ import annotations

import unittest
from unittest import mock

from fastapi.testclient import TestClient

from project_runtime.runtime_app import build_project_runtime_app


class KnowledgeBaseRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(build_project_runtime_app())

    def test_root_and_project_config_endpoint_exist(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["project"]["project"]["project_id"], "knowledge_base_basic")
        self.assertEqual(payload["frontend"], "/knowledge-base")
        self.assertEqual(payload["project_config"], "/api/knowledge/project-config")

        config_response = self.client.get("/api/knowledge/project-config")
        self.assertEqual(config_response.status_code, 200)
        config_payload = config_response.json()
        self.assertEqual(config_payload["project"]["project_id"], "knowledge_base_basic")
        self.assertIn("communication", config_payload)
        self.assertIn("exact", config_payload)

    def test_chat_surface_and_api_contract_exist(self) -> None:
        page = self.client.get("/knowledge-base")
        self.assertEqual(page.status_code, 200)
        self.assertIn("今天想了解什么？", page.text)
        self.assertIn("新建对话", page.text)

        knowledge_bases = self.client.get("/api/knowledge/knowledge-bases")
        self.assertEqual(knowledge_bases.status_code, 200)
        payload = knowledge_bases.json()
        self.assertEqual(payload[0]["knowledge_base_id"], "research-and-standards")

    @mock.patch("project_runtime.runtime_app.load_project_runtime")
    def test_runtime_app_builds_from_loaded_assembly_without_materialization_side_effect(self, load_project_runtime: mock.Mock) -> None:
        from project_runtime import load_project_runtime as load_runtime

        assembly = load_runtime()
        load_project_runtime.return_value = assembly

        app = build_project_runtime_app()

        self.assertEqual(app.title, assembly.metadata.display_name)
        load_project_runtime.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
