from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_runtime import DEFAULT_PROJECT_FILE, materialize_project_runtime


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the four-layer canonical output for the selected project."
    )
    parser.add_argument(
        "--project-file",
        default=str(DEFAULT_PROJECT_FILE.relative_to(REPO_ROOT)),
        help="path to the project.toml file",
    )
    parser.add_argument(
        "--check-changes",
        action="store_true",
        help="kept for editor workflows; validation still recompiles the canonical output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable validation output",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    assembly = materialize_project_runtime(args.project_file)
    payload = {
        "passed": assembly.validation_reports.passed,
        "passed_count": assembly.validation_reports.passed_count,
        "rule_count": assembly.validation_reports.rule_count,
        "project_id": assembly.metadata.project_id,
        "canonical_json": (
            assembly.generated_artifacts.canonical_json if assembly.generated_artifacts else ""
        ),
        "scopes": assembly.validation_reports.summary_by_scope(),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            "[validate] "
            f"passed={payload['passed']} "
            f"rules={payload['passed_count']}/{payload['rule_count']} "
            f"canonical={payload['canonical_json']}"
        )
    return 0 if assembly.validation_reports.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
