#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 - "${SCRIPT_DIR}" <<'PY'
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


script_dir = Path(sys.argv[1]).resolve()
package = load_json(script_dir / "package.json", {})
publisher = package["publisher"]
name = package["name"]
version = package["version"]
extension_id = f"{publisher}.{name}"

copy_items = ["package.json"]
for item in package.get("files", []):
    if item.endswith("/**"):
        copy_items.append(item[:-3])
    else:
        copy_items.append(item)

targets = []
seen_targets = set()


def add_target(label: str, root: Path, suffix: str) -> None:
    if not root.is_dir():
        return
    key = root.resolve()
    if key in seen_targets:
        return
    seen_targets.add(key)
    targets.append({"label": label, "root": root, "suffix": suffix})


for root in [
    Path.home() / ".vscode-server" / "extensions",
    Path.home() / ".trae-server" / "extensions",
    Path.home() / ".trae-cn-server" / "extensions",
]:
    label = root.parts[-2]
    add_target(label, root, "")

windows_users_root = Path("/mnt/c/Users")
if windows_users_root.is_dir():
    for user_home in sorted(path for path in windows_users_root.iterdir() if path.is_dir()):
        add_target(f"{user_home.name}:.vscode", user_home / ".vscode" / "extensions", "")
        add_target(f"{user_home.name}:.trae", user_home / ".trae" / "extensions", "-universal")
        add_target(f"{user_home.name}:.trae-cn", user_home / ".trae-cn" / "extensions", "-universal")

if not targets:
    raise SystemExit("No VS Code or Trae extension directories found in WSL or /mnt/c/Users.")


def build_location(path: Path) -> dict[str, object]:
    posix_path = path.as_posix()
    parts = path.parts
    if len(parts) >= 4 and parts[1] == "mnt" and len(parts[2]) == 1:
        drive = parts[2].upper()
        rest = list(parts[3:])
        windows_path = drive + ":\\" + "\\".join(rest)
        encoded = "/".join(rest)
        return {
            "$mid": 1,
            "fsPath": windows_path,
            "_sep": 1,
            "external": f"file:///{drive}%3A/{encoded}",
            "path": f"/{drive.lower()}:/{encoded}",
            "scheme": "file",
        }
    return {
        "$mid": 1,
        "fsPath": posix_path,
        "external": f"file://{posix_path}",
        "path": posix_path,
        "scheme": "file",
    }

installed = []

for target in targets:
    root = target["root"]
    suffix = target["suffix"]
    stale_dirs = []
    for old in sorted(root.glob(f"{extension_id}-*")):
        if old.is_dir():
            stale_dirs.append(old.name)
            shutil.rmtree(old)
    for old in sorted(root.glob("local.archsync-*")):
        if old.is_dir():
            stale_dirs.append(old.name)
            shutil.rmtree(old)

    target_name = f"{extension_id}-{version}{suffix}"
    target_dir = root / target_name
    target_dir.mkdir(parents=True, exist_ok=True)

    for rel in copy_items:
        src_path = script_dir / rel
        dst_path = target_dir / rel
        if src_path.is_dir():
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        elif src_path.is_file():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)

    extensions_json = root / "extensions.json"
    entries = load_json(extensions_json, [])
    entries = [
        entry
        for entry in entries
        if entry.get("identifier", {}).get("id") not in {extension_id, "local.archsync"}
    ]
    metadata = {
        "installedTimestamp": int(time.time() * 1000),
        "source": "vsix",
    }
    if suffix:
        metadata["targetPlatform"] = suffix.removeprefix("-")
    entries.append(
        {
            "identifier": {"id": extension_id},
            "version": version,
            "location": build_location(target_dir),
            "relativeLocation": target_name,
            "metadata": metadata,
        }
    )
    write_json(extensions_json, entries)

    obsolete_path = root / ".obsolete"
    obsolete = load_json(obsolete_path, {})
    changed = False
    for stale in stale_dirs:
        if stale in obsolete:
            obsolete.pop(stale, None)
            changed = True
    if changed:
        write_json(obsolete_path, obsolete)

    installed.append(f"{target['label']}: {target_dir}")

print("\n".join(installed))
PY
