from __future__ import annotations

import unittest

from project_runtime.knowledge_base_contract import load_knowledge_base_template_contract


class KnowledgeBaseContractTest(unittest.TestCase):
    def test_style_profile_contract_resolves_visual_tokens(self) -> None:
        contract = load_knowledge_base_template_contract()

        tokens = contract.style_profiles.resolve_visual_tokens(
            surface_preset="light",
            radius_scale="md",
            shadow_level="md",
            font_scale="md",
            sidebar_width="md",
            density="comfortable",
            accent="#2563eb",
            brand="Shelf",
            preview_mode="drawer",
            preview_variant="citation_drawer",
        )

        self.assertEqual(tokens["bg"], "#f6f7fb")
        self.assertEqual(tokens["radius"], "18px")
        self.assertEqual(tokens["drawer_width"], "370px")
        self.assertEqual(tokens["message_width"], "820px")
        self.assertEqual(tokens["preview_variant"], "citation_drawer")


if __name__ == "__main__":
    unittest.main()
