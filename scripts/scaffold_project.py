from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from project_runtime import scaffold_registered_project


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a framework-driven project scaffold from a registered template."
    )
    parser.add_argument(
        "--project-dir",
        required=True,
        help="Target project directory, e.g. projects/my_project",
    )
    parser.add_argument(
        "--template",
        required=True,
        help="Registered project template id, e.g. knowledge_base_workbench",
    )
    parser.add_argument(
        "--display-name",
        help="Optional display name used in the generated product spec scaffold.",
    )
    parser.add_argument(
        "--product-spec-style",
        choices=("modular", "single"),
        default="modular",
        help="Whether product spec is scaffolded into product_spec/*.toml or kept in one file.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite scaffold target files if they already exist.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir)
    if not project_dir.is_absolute():
        project_dir = (REPO_ROOT / project_dir).resolve()

    written = scaffold_registered_project(
        project_dir,
        template_id=args.template,
        display_name=args.display_name,
        modular_product_spec=args.product_spec_style == "modular",
        force=args.force,
    )
    print(f"[OK] scaffolded {project_dir.relative_to(REPO_ROOT).as_posix()}")
    for rel_path in written:
        print(f"  - {rel_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
