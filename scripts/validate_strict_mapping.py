from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from framework_ir import load_framework_registry
from framework_packages import load_builtin_package_registry
from project_runtime import (
    build_project_discovery_audit,
    discover_framework_driven_projects,
    materialize_knowledge_base_project,
    render_project_discovery_audit_markdown,
)
from workspace_governance import (
    DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON,
    DEFAULT_PROJECT_DISCOVERY_AUDIT_MD,
    DEFAULT_WORKSPACE_GOVERNANCE_JSON,
    build_workspace_governance_payload,
)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must decode into object")
    return payload


def _compare_json(expected: dict[str, Any], actual_path: Path) -> str | None:
    if not actual_path.exists():
        return f"missing file: {actual_path.relative_to(REPO_ROOT)}"
    actual = _read_json(actual_path)
    if actual != expected:
        return f"stale file: {actual_path.relative_to(REPO_ROOT)}"
    return None


def validate_registry_bindings() -> list[str]:
    framework_registry = load_framework_registry()
    package_registry = load_builtin_package_registry()
    issues: list[str] = []
    try:
        package_registry.validate_against_framework(framework_registry)
    except ValueError as exc:
        issues.append(str(exc))
    return issues


def validate_project_materialization() -> list[str]:
    issues: list[str] = []
    for record in discover_framework_driven_projects():
        project_file = REPO_ROOT / record.project_file
        generated_dir = REPO_ROOT / record.generated_dir
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_output = Path(temp_dir) / "generated"
                materialize_knowledge_base_project(project_file, output_dir=temp_output)
                for file_name in record.artifact_contract.values():
                    repo_file = generated_dir / file_name
                    temp_file = temp_output / file_name
                    if not repo_file.exists():
                        issues.append(f"missing generated artifact: {repo_file.relative_to(REPO_ROOT)}")
                        continue
                    if repo_file.read_text(encoding="utf-8") != temp_file.read_text(encoding="utf-8"):
                        issues.append(f"stale generated artifact: {repo_file.relative_to(REPO_ROOT)}")
        except Exception as exc:
            issues.append(f"materialization failed for {record.project_file}: {exc}")
            continue

        canonical_path = generated_dir / record.artifact_contract["canonical_graph_json"]
        if not canonical_path.exists():
            issues.append(f"missing canonical graph: {canonical_path.relative_to(REPO_ROOT)}")
            continue
        canonical = _read_json(canonical_path)
        layers = canonical.get("layers", {})
        if set(layers) != {"framework", "config", "code", "evidence"}:
            issues.append(f"canonical layers are invalid in {canonical_path.relative_to(REPO_ROOT)}")
        derived_views = layers.get("evidence", {}).get("derived_views", {})
        if not isinstance(derived_views, dict):
            issues.append(f"derived view metadata missing in {canonical_path.relative_to(REPO_ROOT)}")
        else:
            canonical_rel = str(canonical_path.relative_to(REPO_ROOT))
            for view_name, view_data in derived_views.items():
                if not isinstance(view_data, dict) or view_data.get("derived_from") != canonical_rel:
                    issues.append(
                        f"derived view {view_name} does not point back to canonical graph in {canonical_path.relative_to(REPO_ROOT)}"
                    )
    return issues


def validate_workspace_views() -> list[str]:
    issues: list[str] = []
    governance_payload = build_workspace_governance_payload()
    maybe_issue = _compare_json(governance_payload, DEFAULT_WORKSPACE_GOVERNANCE_JSON)
    if maybe_issue is not None:
        issues.append(maybe_issue)

    discovery_payload = build_project_discovery_audit()
    maybe_issue = _compare_json(discovery_payload, DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON)
    if maybe_issue is not None:
        issues.append(maybe_issue)

    expected_markdown = render_project_discovery_audit_markdown(discovery_payload)
    if not DEFAULT_PROJECT_DISCOVERY_AUDIT_MD.exists():
        issues.append(f"missing file: {DEFAULT_PROJECT_DISCOVERY_AUDIT_MD.relative_to(REPO_ROOT)}")
    elif DEFAULT_PROJECT_DISCOVERY_AUDIT_MD.read_text(encoding="utf-8") != expected_markdown:
        issues.append(f"stale file: {DEFAULT_PROJECT_DISCOVERY_AUDIT_MD.relative_to(REPO_ROOT)}")
    return issues


def validate_change_context() -> list[str]:
    try:
        output = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        return [f"failed to inspect git status: {exc}"]

    changed_files = [line[3:] for line in output.stdout.splitlines() if len(line) >= 4]
    if not changed_files:
        return []

    known_projects = {record.project_file for record in discover_framework_driven_projects()}
    issues: list[str] = []
    for changed_file in changed_files:
        if changed_file.startswith("projects/") and changed_file.endswith("/project.toml"):
            if changed_file not in known_projects:
                issues.append(f"unknown project file changed but not discoverable: {changed_file}")
        if changed_file.startswith("framework/"):
            framework_registry = load_framework_registry()
            if changed_file not in {module.path for module in framework_registry.modules}:
                issues.append(f"changed framework file is not loadable: {changed_file}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate framework-package registry, canonical graphs, and derived views.")
    parser.add_argument("--check-changes", action="store_true", help="validate git change context instead of full materialization")
    args = parser.parse_args()

    issues = validate_change_context() if args.check_changes else (
        validate_registry_bindings() + validate_project_materialization() + validate_workspace_views()
    )
    if issues:
        for issue in issues:
            print("[FAIL]", issue)
        return 1
    print("[OK] strict validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
