from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_runtime.knowledge_base import materialize_knowledge_base_project


def discover_instance_files() -> list[Path]:
    return sorted((REPO_ROOT / "projects").glob("*/instance.toml"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize generated project artifacts from framework markdown and instance config."
    )
    parser.add_argument(
        "--project",
        action="append",
        dest="projects",
        help="project instance file to materialize; repeatable. Defaults to every projects/*/instance.toml.",
    )
    args = parser.parse_args()

    requested = args.projects or []
    instance_files = [
        (REPO_ROOT / item).resolve() if not Path(item).is_absolute() else Path(item).resolve()
        for item in requested
    ]
    if not instance_files:
        instance_files = [path.resolve() for path in discover_instance_files()]

    if not instance_files:
        print("[FAIL] no project instance files found")
        return 1

    for instance_file in instance_files:
        project = materialize_knowledge_base_project(instance_file)
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
