from __future__ import annotations

from pathlib import Path
import tempfile
import textwrap
import unittest

from project_runtime.project_governance import (
    RequiredRole,
    StructuralObject,
    classify_candidates,
    fingerprint,
    resolve_role_bindings,
    scan_python_structural_candidates,
)


def _object_with_role(
    *,
    object_id: str,
    file_hint: str,
    locator: str,
    candidate_kinds: tuple[str, ...],
    classification: str = "governed",
) -> StructuralObject:
    role = RequiredRole(
        role_id=f"{object_id}:{locator}",
        role_kind="test_role",
        description=f"test role for {object_id}",
        candidate_kinds=candidate_kinds,
        locator_patterns=(locator,),
        file_hints=(file_hint,),
        classification=classification,
        min_count=1,
        max_count=1,
    )
    empty = {}
    return StructuralObject(
        object_id=object_id,
        project_id="scanner_test",
        kind="test_object",
        title=object_id,
        risk_level="high",
        cardinality="exactly_one",
        status="required",
        semantic=empty,
        required_roles=(role,),
        expected_evidence=empty,
        expected_fingerprint=fingerprint(empty),
        actual_evidence=empty,
        actual_fingerprint=fingerprint(empty),
        comparator="exact.v1",
        extractor="test.v1",
        origin_categories=("scanner-discovered",),
    )


class PythonCandidateScannerTest(unittest.TestCase):
    def test_scanner_hits_route_schema_builder_behavior_and_evidence_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "sample.py"
            source.write_text(
                textwrap.dedent(
                    """
                    from dataclasses import dataclass
                    from fastapi import APIRouter
                    from pydantic import BaseModel

                    router = APIRouter()

                    class RequestPayload(BaseModel):
                        message: str

                    @dataclass
                    class ContractView:
                        value: str

                    @router.get("/health")
                    def healthcheck() -> dict[str, str]:
                        return {"ok": "yes"}

                    def build_router():
                        local_router = APIRouter()
                        local_router.add_api_route("/items", healthcheck, methods=["GET"])
                        return local_router

                    def answer_question():
                        return "ok"

                    def build_manifest():
                        path = "governance_manifest.json"
                        return path
                    """
                ),
                encoding="utf-8",
            )
            candidates = scan_python_structural_candidates(project_id="scanner_test", search_roots=(root,))
            kinds = {(item.kind, item.locator) for item in candidates}
            self.assertIn(("python_route_handler", "function:healthcheck"), kinds)
            self.assertIn(("python_route_builder", "function:build_router"), kinds)
            self.assertIn(("python_behavior_orchestrator", "function:answer_question"), kinds)
            self.assertIn(("python_evidence_builder", "function:build_manifest"), kinds)
            self.assertIn(("python_schema_carrier", "class:RequestPayload"), kinds)
            self.assertIn(("python_schema_carrier", "class:ContractView"), kinds)

    def test_scanner_skips_plain_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "helpers.py"
            source.write_text(
                textwrap.dedent(
                    """
                    def helper():
                        return 1

                    class PlainObject:
                        pass
                    """
                ),
                encoding="utf-8",
            )
            candidates = scan_python_structural_candidates(project_id="scanner_test", search_roots=(root,))
            self.assertEqual(candidates, ())

    def test_candidate_classification_covers_governed_attached_and_internal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            governed_file = root / "governed.py"
            internal_file = root / "internal.py"
            governed_file.write_text(
                textwrap.dedent(
                    """
                    from pydantic import BaseModel

                    class RequestPayload(BaseModel):
                        message: str

                    def build_contract():
                        return {"ok": True}
                    """
                ),
                encoding="utf-8",
            )
            internal_file.write_text(
                textwrap.dedent(
                    """
                    def build_misc():
                        return {"note": "internal"}
                    """
                ),
                encoding="utf-8",
            )
            candidates = scan_python_structural_candidates(project_id="scanner_test", search_roots=(root,))
            governed_rel = str(governed_file)
            internal_rel = str(internal_file)
            objects = (
                _object_with_role(
                    object_id="scanner.contract",
                    file_hint=governed_rel,
                    locator="function:build_contract",
                    candidate_kinds=("python_builder",),
                ),
            )
            bindings = resolve_role_bindings(objects, candidates)
            classified = classify_candidates(objects, candidates, bindings)
            by_locator = {item.locator: item for item in classified}
            self.assertEqual(by_locator["function:build_contract"].classification, "governed")
            self.assertEqual(by_locator["class:RequestPayload"].classification, "attached")
            self.assertEqual(by_locator["function:build_misc"].classification, "internal")
            self.assertEqual(by_locator["function:build_misc"].file, internal_rel)


if __name__ == "__main__":
    unittest.main()
