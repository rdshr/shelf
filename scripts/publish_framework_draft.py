from __future__ import annotations

import argparse
from pathlib import Path
import shutil


REPO_ROOT = Path(__file__).resolve().parent.parent
DRAFT_ROOT = REPO_ROOT / "framework_drafts"
PUBLISHED_ROOT = REPO_ROOT / "framework"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Publish a framework draft into the canonical framework/ tree."
    )
    parser.add_argument(
        "--draft",
        required=True,
        help="Draft markdown file under framework_drafts/, e.g. framework_drafts/frontend/L2-M1-xxx.md",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing published framework file.",
    )
    parser.add_argument(
        "--keep-draft",
        action="store_true",
        help="Copy instead of move, so the draft file remains in framework_drafts/.",
    )
    return parser.parse_args()


def resolve_draft_path(draft_arg: str) -> Path:
    candidate = Path(draft_arg)
    if not candidate.is_absolute():
        candidate = (REPO_ROOT / candidate).resolve()
    return candidate


def publish_framework_draft(draft_path: Path, *, force: bool, keep_draft: bool) -> tuple[Path, Path]:
    draft_path = draft_path.resolve()
    if not draft_path.exists() or not draft_path.is_file():
        raise FileNotFoundError(f"draft file not found: {draft_path}")
    try:
        rel_path = draft_path.relative_to(DRAFT_ROOT)
    except ValueError as exc:
        raise ValueError("draft file must live under framework_drafts/") from exc

    target_path = (PUBLISHED_ROOT / rel_path).resolve()
    if target_path.exists() and not force:
        raise ValueError(f"published framework file already exists: {target_path}")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if keep_draft:
        shutil.copy2(draft_path, target_path)
    else:
        shutil.move(draft_path, target_path)
    return draft_path, target_path


def main() -> int:
    args = parse_args()
    _, target_path = publish_framework_draft(
        resolve_draft_path(args.draft),
        force=args.force,
        keep_draft=args.keep_draft,
    )
    print(f"[OK] published {target_path.relative_to(REPO_ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
