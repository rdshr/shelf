from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_runtime import DEFAULT_PROJECT_FILE, materialize_project_runtime


def _discover_project_files(repo_root: Path) -> list[Path]:
    return sorted((repo_root / "projects").glob("*/project.toml"))


def _resolve_project_file(repo_root: Path, project_file: str | None) -> Path | None:
    if project_file is None:
        discovered = _discover_project_files(repo_root)
        return discovered[0] if discovered else None
    candidate = Path(project_file)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    return candidate


def _bootstrap_skip_payload(project_file: str | None) -> dict[str, Any]:
    return {
        "passed": True,
        "passed_count": 0,
        "rule_count": 0,
        "project_id": "",
        "canonical_json": "",
        "scopes": {},
        "bootstrap_mode": True,
        "message": (
            "skip check-changes: no projects/*/project.toml found; "
            "allow bootstrap generation from framework first"
        ),
        "project_file": project_file or "",
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the four-layer canonical output for the selected project."
    )
    parser.add_argument(
        "--project-file",
        default=(
            str(DEFAULT_PROJECT_FILE.relative_to(REPO_ROOT))
            if DEFAULT_PROJECT_FILE is not None
            else None
        ),
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
    resolved_project_file = _resolve_project_file(REPO_ROOT, args.project_file)
    if args.check_changes and (resolved_project_file is None or not resolved_project_file.is_file()):
        discovered_projects = _discover_project_files(REPO_ROOT)
        if not discovered_projects:
            payload = _bootstrap_skip_payload(args.project_file)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False))
            else:
                print(f"[validate] passed=True bootstrap_mode=True project={payload['project_file']}")
                print(f"- {payload['message']}")
            return 0
    if resolved_project_file is None:
        message = (
            "no projects/*/project.toml found; "
            "specify --project-file or create a project config first"
        )
        if args.json:
            print(
                json.dumps(
                    {
                        "passed": False,
                        "message": message,
                        "project_file": args.project_file or "",
                    },
                    ensure_ascii=False,
                )
            )
        else:
            print(f"[validate] passed=False")
            print(f"- {message}")
        return 1

    assembly = materialize_project_runtime(args.project_file or resolved_project_file)
    failed_rules = [
        outcome
        for summary in assembly.validation_reports.scopes.values()
        for outcome in summary.rules
        if not outcome.passed
    ]
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
        for outcome in failed_rules:
            for reason in outcome.reasons:
                print(f"- {reason}")
    return 0 if assembly.validation_reports.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
