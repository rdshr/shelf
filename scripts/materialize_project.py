from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from generate_module_hierarchy_html import load_hierarchy, render_html
from generate_framework_tree_hierarchy import (
    DEFAULT_FRAMEWORK_DIR,
    DEFAULT_OUTPUT_HTML as DEFAULT_FRAMEWORK_TREE_HTML,
    DEFAULT_OUTPUT_JSON as DEFAULT_FRAMEWORK_TREE_JSON,
    build_payload_from_framework,
    render_html as render_framework_tree_html,
)
from project_runtime import discover_framework_driven_projects, materialize_registered_project
from project_runtime.project_governance import (
    build_project_discovery_audit,
    render_project_discovery_audit_markdown,
)
from workspace_governance import (
    DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON,
    DEFAULT_PROJECT_DISCOVERY_AUDIT_MD,
    DEFAULT_WORKSPACE_GOVERNANCE_HTML,
    DEFAULT_WORKSPACE_GOVERNANCE_JSON,
    build_workspace_governance_payload,
)


def discover_product_spec_files() -> list[Path]:
    return [
        (REPO_ROOT / item.product_spec_file).resolve()
        for item in discover_framework_driven_projects()
    ]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize generated project artifacts from framework markdown, product spec, and implementation config."
    )
    parser.add_argument(
        "--project",
        action="append",
        dest="projects",
        help="product spec file to materialize; repeatable. Defaults to every projects/*/product_spec.toml.",
    )
    args = parser.parse_args()

    requested = args.projects or []
    product_spec_files = [
        (REPO_ROOT / item).resolve() if not Path(item).is_absolute() else Path(item).resolve()
        for item in requested
    ]
    if not product_spec_files:
        product_spec_files = [path.resolve() for path in discover_product_spec_files()]

    if not product_spec_files:
        print("[FAIL] no product spec files found")
        return 1

    for product_spec_file in product_spec_files:
        project = materialize_registered_project(product_spec_file)
        assert project.generated_artifacts is not None
        print(
            "[OK] materialized",
            project.metadata.project_id,
            "->",
            project.generated_artifacts.directory,
        )

    framework_payload, framework_warnings = build_payload_from_framework(DEFAULT_FRAMEWORK_DIR)
    DEFAULT_FRAMEWORK_TREE_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_FRAMEWORK_TREE_JSON.write_text(
        json.dumps(framework_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    render_framework_tree_html(
        DEFAULT_FRAMEWORK_TREE_JSON,
        DEFAULT_FRAMEWORK_TREE_HTML,
        width=1680,
        height=1180,
    )
    for warning in framework_warnings:
        print("[WARN] framework tree ->", warning)
    print("[OK] framework tree ->", DEFAULT_FRAMEWORK_TREE_JSON.relative_to(REPO_ROOT))
    print("[OK] framework tree ->", DEFAULT_FRAMEWORK_TREE_HTML.relative_to(REPO_ROOT))

    governance_payload = build_workspace_governance_payload()
    discovery_audit_payload = build_project_discovery_audit()
    DEFAULT_WORKSPACE_GOVERNANCE_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_WORKSPACE_GOVERNANCE_JSON.write_text(
        json.dumps(governance_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON.write_text(
        json.dumps(discovery_audit_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    DEFAULT_PROJECT_DISCOVERY_AUDIT_MD.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_PROJECT_DISCOVERY_AUDIT_MD.write_text(
        render_project_discovery_audit_markdown(discovery_audit_payload),
        encoding="utf-8",
    )
    graph = load_hierarchy(DEFAULT_WORKSPACE_GOVERNANCE_JSON)
    render_html(graph, DEFAULT_WORKSPACE_GOVERNANCE_HTML, width=1680, height=1080)
    print("[OK] governance tree ->", DEFAULT_WORKSPACE_GOVERNANCE_JSON.relative_to(REPO_ROOT))
    print("[OK] governance tree ->", DEFAULT_WORKSPACE_GOVERNANCE_HTML.relative_to(REPO_ROOT))
    print("[OK] project discovery audit ->", DEFAULT_PROJECT_DISCOVERY_AUDIT_JSON.relative_to(REPO_ROOT))
    print("[OK] project discovery audit ->", DEFAULT_PROJECT_DISCOVERY_AUDIT_MD.relative_to(REPO_ROOT))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
