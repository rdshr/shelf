from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib
from typing import Any


SECTION_HEADER_PREFIXES = ("[", "[[")
PRODUCT_SPEC_SPLIT_DIR = "product_spec"
PRODUCT_SPEC_ROOT_ONLY_SECTIONS = frozenset({"project", "framework"})


class ProjectConfigLoadError(ValueError):
    def __init__(self, message: str, file_path: Path) -> None:
        super().__init__(message)
        self.file_path = file_path


def _require_dict(value: Any, *, file_path: Path) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProjectConfigLoadError(f"{file_path.name} must decode into a table", file_path)
    return value


def _read_toml_file(file_path: Path) -> tuple[str, dict[str, Any]]:
    try:
        text = file_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ProjectConfigLoadError(f"missing project config: {file_path}", file_path) from exc
    try:
        payload = tomllib.loads(text)
    except Exception as exc:
        raise ProjectConfigLoadError(f"failed to parse TOML: {exc}", file_path) from exc
    return text, _require_dict(payload, file_path=file_path)


def _find_section_line(text: str, section_name: str) -> int:
    targets = (f"[{section_name}]", f"[[{section_name}]]")
    for index, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if any(stripped.startswith(target) for target in targets):
            return index
    return 1


@dataclass(frozen=True)
class ComposedTomlDocument:
    entry_file: Path
    entry_text: str
    entry_data: dict[str, Any]
    merged_data: dict[str, Any]
    section_files: dict[str, Path]
    file_texts: dict[Path, str]

    def source_file_for_section(self, section_name: str) -> Path:
        if section_name in self.section_files:
            return self.section_files[section_name]
        return self.entry_file

    def line_for_section(self, section_name: str) -> int:
        source_file = self.source_file_for_section(section_name)
        source_text = self.file_texts.get(source_file, self.entry_text)
        return _find_section_line(source_text, section_name)

    def line_for_nested_section(self, parent: str, child: str) -> int:
        source_file = self.source_file_for_section(parent)
        source_text = self.file_texts.get(source_file, self.entry_text)
        return _find_section_line(source_text, f"{parent}.{child}")

    @property
    def top_level_keys(self) -> frozenset[str]:
        return frozenset(self.merged_data)


def load_composed_toml_document(
    entry_file: Path,
    *,
    split_dir_name: str | None = None,
    root_only_sections: frozenset[str] = frozenset(),
) -> ComposedTomlDocument:
    entry_path = entry_file.resolve()
    entry_text, entry_data = _read_toml_file(entry_path)
    merged_data = dict(entry_data)
    section_files: dict[str, Path] = {}
    file_texts: dict[Path, str] = {entry_path: entry_text}

    if split_dir_name:
        split_dir = entry_path.parent / split_dir_name
        if split_dir.exists():
            if not split_dir.is_dir():
                raise ProjectConfigLoadError(
                    f"expected section directory to be a folder: {split_dir.name}",
                    split_dir,
                )
            for section_file in sorted(split_dir.glob("*.toml")):
                section_text, section_data = _read_toml_file(section_file)
                file_texts[section_file.resolve()] = section_text
                top_level_keys = list(section_data)
                if len(top_level_keys) != 1:
                    raise ProjectConfigLoadError(
                        "split config section file must define exactly one top-level section",
                        section_file,
                    )
                section_name = top_level_keys[0]
                if section_file.stem != section_name:
                    raise ProjectConfigLoadError(
                        f"split config file name must match top-level section: expected {section_name}.toml",
                        section_file,
                    )
                if section_name in root_only_sections and section_name not in entry_data:
                    raise ProjectConfigLoadError(
                        f"section {section_name} must stay in {entry_path.name}",
                        section_file,
                    )
                if section_name in entry_data:
                    raise ProjectConfigLoadError(
                        f"duplicate top-level section across {entry_path.name} and split section file: {section_name}",
                        section_file,
                    )
                if section_name in merged_data:
                    raise ProjectConfigLoadError(
                        f"duplicate top-level section across split section files: {section_name}",
                        section_file,
                    )
                merged_data[section_name] = section_data[section_name]
                section_files[section_name] = section_file.resolve()

    return ComposedTomlDocument(
        entry_file=entry_path,
        entry_text=entry_text,
        entry_data=entry_data,
        merged_data=merged_data,
        section_files=section_files,
        file_texts=file_texts,
    )


def load_product_spec_document(product_spec_file: Path) -> ComposedTomlDocument:
    return load_composed_toml_document(
        product_spec_file,
        split_dir_name=PRODUCT_SPEC_SPLIT_DIR,
        root_only_sections=PRODUCT_SPEC_ROOT_ONLY_SECTIONS,
    )


def product_spec_section_file(product_spec_file: Path, section_name: str) -> Path:
    document = load_product_spec_document(product_spec_file)
    return document.source_file_for_section(section_name)
