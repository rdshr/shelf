from __future__ import annotations
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from document_chunking_runtime.app import build_document_chunking_app
from project_runtime.document_chunking import (
    DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE,
    load_document_chunking_project,
    materialize_document_chunking_project,
    run_document_chunking_file,
)


class DocumentChunkingRuntimeTest(unittest.TestCase):
    def test_load_document_chunking_project_matches_current_framework_contract(self) -> None:
        project = load_document_chunking_project(DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE)

        self.assertEqual(project.metadata.project_id, "document_chunking_basic")
        self.assertEqual(project.metadata.template, "document_chunking_pipeline")
        self.assertEqual(project.domain_ir.module_id, "document_chunking.L1.M0")
        self.assertEqual(project.product.composition.group_shape, "1_title_plus_zero_or_more_body")
        self.assertEqual(project.product.output.document_format_field, "document_format")
        self.assertEqual(project.product.output.document_format_value, "markdown")
        self.assertEqual(project.product.output.document_format_scope, "document_level")
        self.assertTrue(project.product.output.expose_paragraph_block_projection)
        self.assertEqual(project.product.output.paragraph_block_projection_name, "paragraph_block_set")
        self.assertEqual(project.product.output.paragraph_block_projection_fence_scope, "document_level")
        self.assertTrue(project.product.output.expose_chunk_membership_projection)
        self.assertEqual(project.product.output.chunk_membership_projection_name, "chunk_membership_set")
        self.assertFalse(project.product.output.chunk_membership_include_ordered_block_ids)
        self.assertEqual(project.product.output.title_block_id_field, "title_block_id")
        self.assertEqual(project.product.output.body_block_id_set_field, "body_block_id_set")
        self.assertTrue(project.product.output.include_paragraph_blocks)
        self.assertTrue(project.product.output.include_trace_meta)
        self.assertEqual(project.implementation.runtime.app_builder, "document_chunking_api_v1")
        self.assertEqual(project.implementation.runtime.api_prefix, "/api/document-chunking")
        self.assertTrue(project.implementation.runtime.write_auxiliary_output_files)
        self.assertEqual(project.implementation.runtime.paragraph_block_output_suffix, ".paragraph_blocks.md")
        self.assertEqual(project.implementation.runtime.chunk_membership_output_suffix, ".chunk_membership.md")

    def test_materialize_document_chunking_project_writes_generated_artifacts(self) -> None:
        project = materialize_document_chunking_project(DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE)

        self.assertIsNotNone(project.generated_artifacts)
        assert project.generated_artifacts is not None
        for rel_path in project.generated_artifacts.to_dict().values():
            self.assertTrue((Path.cwd() / rel_path).exists(), rel_path)

    def test_document_chunking_app_and_cli_use_default_validation_input(self) -> None:
        project = load_document_chunking_project(DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE)
        client = TestClient(build_document_chunking_app(project))

        summary_response = client.get(project.implementation.evidence.product_spec_endpoint)
        self.assertEqual(summary_response.status_code, 200)
        self.assertEqual(summary_response.json()["project"]["project_id"], "document_chunking_basic")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "document_chunking_output.md"
            payload = run_document_chunking_file(
                product_spec_file=DEFAULT_DOCUMENT_CHUNKING_PRODUCT_SPEC_FILE,
                input_file=project.implementation.evidence.default_validation_input,
                output_file=output_file,
            )

            self.assertTrue(payload["validation"]["passed"])
            self.assertEqual(payload["output"]["document_format"], "markdown")
            self.assertGreaterEqual(len(payload["output"]["ordered_chunk_item_set"]), 1)
            first_item = payload["output"]["ordered_chunk_item_set"][0]
            self.assertIn("title_block_id", first_item)
            self.assertIn("body_block_id_set", first_item)
            self.assertTrue(output_file.exists())
            output_text = output_file.read_text(encoding="utf-8")
            self.assertTrue(output_text.startswith("document_format: markdown\ntext_id: default_input\n"))
            self.assertNotIn("```markdown", output_text)

            paragraph_block_file = output_file.with_name(f"{output_file.stem}.paragraph_blocks.md")
            chunk_membership_file = output_file.with_name(f"{output_file.stem}.chunk_membership.md")
            self.assertTrue(paragraph_block_file.exists())
            self.assertTrue(chunk_membership_file.exists())

            paragraph_block_text = paragraph_block_file.read_text(encoding="utf-8")
            self.assertTrue(paragraph_block_text.startswith("```markdown\n"))
            self.assertIn("text_id: default_input", paragraph_block_text)
            self.assertIn("projection_name: paragraph_block_set", paragraph_block_text)
            self.assertIn("block_id: default_input-pb-0001", paragraph_block_text)

            chunk_membership_text = chunk_membership_file.read_text(encoding="utf-8")
            self.assertIn("text_id: default_input", chunk_membership_text)
            self.assertIn("projection_name: chunk_membership_set", chunk_membership_text)
            self.assertNotIn("ordered_block_id_set:", chunk_membership_text)


if __name__ == "__main__":
    unittest.main()
