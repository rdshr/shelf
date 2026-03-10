from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_runtime import materialize_registered_project


def discover_product_spec_files() -> list[Path]:
    return sorted((REPO_ROOT / "projects").glob("*/product_spec.toml"))


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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
