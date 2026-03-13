from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

from framework_ir.models import (
    FrameworkBaseIR,
    FrameworkBoundaryIR,
    FrameworkCapabilityIR,
    FrameworkModuleIR,
    FrameworkRegistryIR,
    FrameworkRuleIR,
    FrameworkUpstreamRef,
    FrameworkVerificationIR,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK_ROOT = REPO_ROOT / "framework"

FRAMEWORK_FILE_PATTERN = re.compile(r"^L(?P<level>\d+)-M(?P<module>\d+)-.+\.md$")
TITLE_PATTERN = re.compile(r"^#\s+(?P<cn>[^:]+):(?P<en>.+)$", re.MULTILINE)
CAPABILITY_LINE_PATTERN = re.compile(r"^-\s+`(?P<id>C\d+)`\s+(?P<name>[^：:]+)[：:]\s*(?P<body>.+)$")
BOUNDARY_LINE_PATTERN = re.compile(r"^-\s+`(?P<id>[A-Z0-9_]+)`\s+(?P<name>[^：:]+)[：:]\s*(?P<body>.+)$")
BASE_LINE_PATTERN = re.compile(r"^-\s+`(?P<id>B\d+)`\s+(?P<name>[^：:]+)[：:]\s*(?P<body>.+)$")
VERIFY_LINE_PATTERN = re.compile(r"^-\s+`(?P<id>V\d+)`\s+(?P<name>[^：:]+)[：:]\s*(?P<body>.+)$")
RULE_TOP_PATTERN = re.compile(r"^-\s+`(?P<id>R\d+)`\s+(?P<name>.+)$")
RULE_CHILD_PATTERN = re.compile(r"^\s*-\s+`(?P<id>R\d+\.\d+)`\s+(?P<body>.+)$")
SOURCE_EXPR_PATTERN = re.compile(r"来源[：:]\s*`(?P<expr>[^`]+)`")
INLINE_REF_PATTERN = re.compile(
    r"^(?:(?P<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?L(?P<level>\d+)\.M(?P<module>\d+)(?:\[(?P<rules>[^\]]*)\])?$"
)


def _split_sections(text: str) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line.strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line.rstrip())
    return sections


def _clean_lines(lines: Iterable[str]) -> list[str]:
    return [line.strip() for line in lines if line.strip()]


def _extract_intro(text: str) -> str:
    directive_idx = text.find("@framework")
    first_section_idx = text.find("## ")
    if directive_idx == -1 or first_section_idx == -1 or first_section_idx <= directive_idx:
        return ""
    intro = text[directive_idx + len("@framework") : first_section_idx].strip()
    return intro


def _extract_source_tokens(line: str) -> tuple[str, ...]:
    match = SOURCE_EXPR_PATTERN.search(line)
    if match is None:
        return tuple()
    expr = match.group("expr").strip()
    tokens = [token.strip() for token in expr.split("+") if token.strip()]
    return tuple(tokens)


def _extract_inline_expr(line: str) -> str:
    body = line
    if "来源" in body:
        body = re.split(r"来源[：:]", body, maxsplit=1)[0].rstrip("。")
    if "：" in body:
        body = body.split("：", 1)[1]
    elif ":" in body:
        body = body.split(":", 1)[1]
    return body.strip().rstrip("。")


def _parse_inline_refs(inline_expr: str, default_framework: str) -> tuple[FrameworkUpstreamRef, ...]:
    refs: list[FrameworkUpstreamRef] = []
    for part in inline_expr.split("+"):
        term = part.strip()
        match = INLINE_REF_PATTERN.fullmatch(term)
        if match is None:
            continue
        rules_text = (match.group("rules") or "").strip()
        rules = tuple(item.strip() for item in rules_text.split(",") if item.strip())
        refs.append(
            FrameworkUpstreamRef(
                framework=(match.group("framework") or default_framework).strip(),
                level=int(match.group("level")),
                module=int(match.group("module")),
                rules=rules,
            )
        )
    return tuple(refs)


def _parse_capabilities(lines: list[str]) -> tuple[FrameworkCapabilityIR, ...]:
    items: list[FrameworkCapabilityIR] = []
    for line in _clean_lines(lines):
        match = CAPABILITY_LINE_PATTERN.match(line)
        if match is None:
            continue
        items.append(
            FrameworkCapabilityIR(
                capability_id=match.group("id"),
                name=match.group("name").strip(),
                statement=match.group("body").strip().rstrip("。"),
            )
        )
    return tuple(items)


def _parse_boundaries(lines: list[str]) -> tuple[FrameworkBoundaryIR, ...]:
    items: list[FrameworkBoundaryIR] = []
    for line in _clean_lines(lines):
        match = BOUNDARY_LINE_PATTERN.match(line)
        if match is None:
            continue
        body = match.group("body").strip()
        statement = re.split(r"来源[：:]", body, maxsplit=1)[0].strip().rstrip("。")
        items.append(
            FrameworkBoundaryIR(
                boundary_id=match.group("id"),
                name=match.group("name").strip(),
                statement=statement,
                source_tokens=_extract_source_tokens(line),
            )
        )
    return tuple(items)


def _parse_bases(lines: list[str], framework: str) -> tuple[FrameworkBaseIR, ...]:
    items: list[FrameworkBaseIR] = []
    for line in _clean_lines(lines):
        match = BASE_LINE_PATTERN.match(line)
        if match is None:
            continue
        body = match.group("body").strip()
        statement = re.split(r"来源[：:]", body, maxsplit=1)[0].strip().rstrip("。")
        inline_expr = _extract_inline_expr(line)
        items.append(
            FrameworkBaseIR(
                base_id=match.group("id"),
                name=match.group("name").strip(),
                statement=statement,
                inline_expr=inline_expr,
                source_tokens=_extract_source_tokens(line),
                upstream_refs=_parse_inline_refs(inline_expr, framework),
            )
        )
    return tuple(items)


def _parse_rules(lines: list[str]) -> tuple[FrameworkRuleIR, ...]:
    current_id: str | None = None
    current_name = ""
    participants: tuple[str, ...] = tuple()
    combination = ""
    outputs: tuple[str, ...] = tuple()
    bindings: tuple[str, ...] = tuple()
    items: list[FrameworkRuleIR] = []

    def flush() -> None:
        nonlocal current_id, current_name, participants, combination, outputs, bindings
        if current_id is None:
            return
        items.append(
            FrameworkRuleIR(
                rule_id=current_id,
                name=current_name,
                participant_bases=participants,
                combination=combination,
                output_capabilities=outputs,
                boundary_bindings=bindings,
            )
        )
        current_id = None
        current_name = ""
        participants = tuple()
        combination = ""
        outputs = tuple()
        bindings = tuple()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        top_match = RULE_TOP_PATTERN.match(stripped)
        if top_match is not None:
            flush()
            current_id = top_match.group("id")
            current_name = top_match.group("name").strip()
            continue
        child_match = RULE_CHILD_PATTERN.match(line)
        if child_match is None or current_id is None:
            continue
        body = child_match.group("body").strip().rstrip("。")
        if body.startswith("参与基："):
            participants = tuple(item.strip() for item in body.split("：", 1)[1].replace("`", "").split("+"))
        elif body.startswith("组合方式："):
            combination = body.split("：", 1)[1].strip()
        elif body.startswith("输出能力："):
            outputs = tuple(item.strip() for item in body.split("：", 1)[1].replace("`", "").split("+"))
        elif body.startswith("边界绑定："):
            bindings = tuple(item.strip() for item in body.split("：", 1)[1].replace("`", "").split("+"))
    flush()
    return tuple(items)


def _parse_verifications(lines: list[str]) -> tuple[FrameworkVerificationIR, ...]:
    items: list[FrameworkVerificationIR] = []
    for line in _clean_lines(lines):
        match = VERIFY_LINE_PATTERN.match(line)
        if match is None:
            continue
        items.append(
            FrameworkVerificationIR(
                verification_id=match.group("id"),
                name=match.group("name").strip(),
                statement=match.group("body").strip().rstrip("。"),
            )
        )
    return tuple(items)


def parse_framework_module(path: str | Path) -> FrameworkModuleIR:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = (REPO_ROOT / file_path).resolve()
    text = file_path.read_text(encoding="utf-8")
    title_match = TITLE_PATTERN.search(text)
    if title_match is None:
        raise ValueError(f"framework title is invalid: {file_path}")
    file_match = FRAMEWORK_FILE_PATTERN.fullmatch(file_path.name)
    if file_match is None:
        raise ValueError(f"framework filename is invalid: {file_path}")
    framework = file_path.parent.name
    sections = _split_sections(text)
    return FrameworkModuleIR(
        framework=framework,
        level=int(file_match.group("level")),
        module=int(file_match.group("module")),
        path=file_path.relative_to(REPO_ROOT).as_posix(),
        title_cn=title_match.group("cn").strip(),
        title_en=title_match.group("en").strip(),
        intro=_extract_intro(text),
        capabilities=_parse_capabilities(sections.get("## 1. 能力声明（Capability Statement）", [])),
        boundaries=_parse_boundaries(sections.get("## 2. 边界定义（Boundary / 参数）", [])),
        bases=_parse_bases(sections.get("## 3. 最小可行基（Minimum Viable Bases）", []), framework),
        rules=_parse_rules(sections.get("## 4. 基组合原则（Base Combination Principles）", [])),
        verifications=_parse_verifications(sections.get("## 5. 验证（Verification）", [])),
    )


def load_framework_registry(root: Path = FRAMEWORK_ROOT) -> FrameworkRegistryIR:
    modules: list[FrameworkModuleIR] = []
    for framework_dir in sorted(root.iterdir()):
        if not framework_dir.is_dir():
            continue
        for markdown_file in sorted(framework_dir.glob("L*-M*-*.md")):
            modules.append(parse_framework_module(markdown_file))
    return FrameworkRegistryIR(modules=tuple(modules))
