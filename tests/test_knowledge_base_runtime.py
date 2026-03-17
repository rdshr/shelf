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

    def test_correspondence_endpoints_expose_stable_protocol(self) -> None:
        response = self.client.get("/api/knowledge/correspondence")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["correspondence_schema_version"], 1)
        self.assertIn("objects", payload)
        self.assertIn("tree", payload)
        self.assertIn("validation_summary", payload)

        tree_response = self.client.get("/api/knowledge/correspondence/tree")
        self.assertEqual(tree_response.status_code, 200)
        tree_payload = tree_response.json()
        self.assertEqual(tree_payload["correspondence_schema_version"], 1)
        self.assertIn("tree", tree_payload)
        self.assertIn("validation_summary", tree_payload)

        module_response = self.client.get("/api/knowledge/correspondence/object/knowledge_base.L2.M0")
        self.assertEqual(module_response.status_code, 200)
        module_payload = module_response.json()
        self.assertEqual(module_payload["object_kind"], "module")
        self.assertEqual(module_payload["object_id"], "knowledge_base.L2.M0")

        not_found = self.client.get("/api/knowledge/correspondence/object/not-existing")
        self.assertEqual(not_found.status_code, 404)

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
