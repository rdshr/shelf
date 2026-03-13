from __future__ import annotations

import unittest

from project_runtime.knowledge_base_contract import load_knowledge_base_template_contract
from project_runtime.repository_policy import load_repository_validation_policy
from scripts import validate_strict_mapping


class RepositoryPolicyTest(unittest.TestCase):
    def test_repository_validation_policy_loads(self) -> None:
        policy = load_repository_validation_policy()

        self.assertEqual(policy.public_repo_slug, "xueyu888/shelf")
        self.assertIn("product_spec.toml", policy.allowed_project_root_files)
        self.assertIn("docs", policy.portability.text_scan_roots)

    def test_knowledge_base_template_contract_loads(self) -> None:
        contract = load_knowledge_base_template_contract()

        self.assertEqual(contract.template_id, "knowledge_base_workbench")
        self.assertIn("citation_drawer", contract.required_return_targets)
        self.assertIn("knowledge_chat_client_v1", contract.supported_frontend_renderers)

    def test_repository_portability_validation_passes(self) -> None:
        issues = validate_strict_mapping.validate_repository_portability()
        self.assertEqual([], issues)


if __name__ == "__main__":
    unittest.main()
