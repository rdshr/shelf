from __future__ import annotations

from pathlib import Path
import re
from typing import Iterable

from framework_ir.models import (
    FrameworkBase,
    FrameworkBoundary,
    FrameworkCapability,
    FrameworkSourceRef,
    FrameworkModule,
    FrameworkNonResponsibility,
    FrameworkCatalog,
    FrameworkRule,
    FrameworkUpstreamLink,
    FrameworkVerification,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FRAMEWORK_ROOT = REPO_ROOT / "framework"

FRAMEWORK_FILE_PATTERN = re.compile(r"^L(?P<level>\d+)-M(?P<module>\d+)-.+\.md$")
TITLE_PATTERN = re.compile(r"^#\s+(?P<cn>[^:]+):(?P<en>.+)$", re.MULTILINE)
CAPABILITY_LINE_PATTERN = re.compile(r"^-\s+`(?P<id>C\d+)`\s+(?P<name>[^：:]+)[：:]\s*(?P<body>.+)$")
NON_RESPONSIBILITY_LINE_PATTERN = re.compile(r"^-\s+`(?P<id>N\d+)`\s+(?P<name>[^：:]+)[：:]\s*(?P<body>.+)$")
BOUNDARY_LINE_PATTERN = re.compile(r"^-\s+`(?P<id>[A-Z0-9_]+)`\s+(?P<name>[^：:]+)[：:]\s*(?P<body>.+)$")
BASE_LINE_PATTERN = re.compile(r"^-\s+`(?P<id>B\d+)`\s+(?P<name>[^：:]+)[：:]\s*(?P<body>.+)$")
VERIFY_LINE_PATTERN = re.compile(r"^-\s+`(?P<id>V\d+)`\s+(?P<name>[^：:]+)[：:]\s*(?P<body>.+)$")
RULE_TOP_PATTERN = re.compile(r"^-\s+`(?P<id>R\d+)`\s+(?P<name>.+)$")
RULE_CHILD_PATTERN = re.compile(r"^\s*-\s+`(?P<id>R\d+\.\d+)`\s+(?P<body>.+)$")
SOURCE_EXPR_PATTERN = re.compile(r"来源[：:]\s*`(?P<expr>[^`]+)`")
INLINE_REF_PATTERN = re.compile(
    r"^(?:(?P<framework>[A-Za-z][A-Za-z0-9_-]*)\.)?L(?P<level>\d+)\.M(?P<module>\d+)(?:\[(?P<rules>[^\]]*)\])?$"
)
PARAMETER_SECTION_TITLES = (
    "## 2. 参数定义（Parameter）",
    "## 2. 边界定义（Boundary / 参数）",
)
RULE_PARAMETER_BINDING_PREFIXES = ("参数绑定：", "边界绑定：")


def _split_sections(text: str) -> dict[str, list[tuple[int, str]]]:
    sections: dict[str, list[tuple[int, str]]] = {}
    current: str | None = None
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## "):
            current = line.strip()
            sections[current] = []
            continue
        if current is not None:
            sections[current].append((line_number, line.rstrip()))
    return sections


def _clean_lines(lines: Iterable[tuple[int, str]]) -> list[tuple[int, str]]:
    return [(line_number, line.strip()) for line_number, line in lines if line.strip()]


def _extract_intro(text: str) -> str:
    directive_idx = text.find("@framework")
    first_section_idx = text.find("## ")
    if directive_idx == -1 or first_section_idx == -1 or first_section_idx <= directive_idx:
        return ""
    intro = text[directive_idx + len("@framework") : first_section_idx].strip()
    return intro


def _source_ref(
    relative_file: str,
    *,
    line: int,
    section: str,
    anchor: str,
    token: str | None = None,
) -> FrameworkSourceRef:
    return FrameworkSourceRef(
        file_path=relative_file,
        line=line,
        section=section,
        anchor=anchor,
        token=token,
    )


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


def _parse_inline_refs(inline_expr: str, default_framework: str) -> tuple[FrameworkUpstreamLink, ...]:
    refs: list[FrameworkUpstreamLink] = []
    for part in inline_expr.split("+"):
        term = part.strip()
        match = INLINE_REF_PATTERN.fullmatch(term)
        if match is None:
            continue
        rules_text = (match.group("rules") or "").strip()
        rules = tuple(item.strip() for item in rules_text.split(",") if item.strip())
        refs.append(
            FrameworkUpstreamLink(
                framework=(match.group("framework") or default_framework).strip(),
                level=int(match.group("level")),
                module=int(match.group("module")),
                rules=rules,
            )
        )
    return tuple(refs)


def _parse_capabilities(
    lines: list[tuple[int, str]],
    *,
    relative_file: str,
) -> tuple[FrameworkCapability, ...]:
    items: list[FrameworkCapability] = []
    for line_number, line in _clean_lines(lines):
        match = CAPABILITY_LINE_PATTERN.match(line)
        if match is None:
            continue
        items.append(
            FrameworkCapability(
                capability_id=match.group("id"),
                name=match.group("name").strip(),
                statement=match.group("body").strip().rstrip("。"),
                source_ref=_source_ref(
                    relative_file,
                    line=line_number,
                    section="capability",
                    anchor=f"capability:{match.group('id').lower()}",
                    token=match.group("id"),
                ),
            )
        )
    return tuple(items)


def _parse_non_responsibilities(
    lines: list[tuple[int, str]],
    *,
    relative_file: str,
) -> tuple[FrameworkNonResponsibility, ...]:
    items: list[FrameworkNonResponsibility] = []
    for line_number, line in _clean_lines(lines):
        match = NON_RESPONSIBILITY_LINE_PATTERN.match(line)
        if match is None:
            continue
        items.append(
            FrameworkNonResponsibility(
                responsibility_id=match.group("id"),
                name=match.group("name").strip(),
                statement=match.group("body").strip().rstrip("。"),
                source_ref=_source_ref(
                    relative_file,
                    line=line_number,
                    section="non_responsibility",
                    anchor=f"non-responsibility:{match.group('id').lower()}",
                    token=match.group("id"),
                ),
            )
        )
    return tuple(items)


def _parse_boundaries(
    lines: list[tuple[int, str]],
    *,
    relative_file: str,
) -> tuple[FrameworkBoundary, ...]:
    items: list[FrameworkBoundary] = []
    for line_number, line in _clean_lines(lines):
        match = BOUNDARY_LINE_PATTERN.match(line)
        if match is None:
            continue
        body = match.group("body").strip()
        statement = re.split(r"来源[：:]", body, maxsplit=1)[0].strip().rstrip("。")
        items.append(
            FrameworkBoundary(
                boundary_id=match.group("id"),
                name=match.group("name").strip(),
                statement=statement,
                source_tokens=_extract_source_tokens(line),
                source_ref=_source_ref(
                    relative_file,
                    line=line_number,
                    section="boundary",
                    anchor=f"boundary:{match.group('id').lower()}",
                    token=match.group("id"),
                ),
            )
        )
    return tuple(items)


def _parse_bases(
    lines: list[tuple[int, str]],
    framework: str,
    *,
    relative_file: str,
) -> tuple[FrameworkBase, ...]:
    items: list[FrameworkBase] = []
    for line_number, line in _clean_lines(lines):
        match = BASE_LINE_PATTERN.match(line)
        if match is None:
            continue
        body = match.group("body").strip()
        statement = re.split(r"来源[：:]", body, maxsplit=1)[0].strip().rstrip("。")
        inline_expr = _extract_inline_expr(line)
        items.append(
            FrameworkBase(
                base_id=match.group("id"),
                name=match.group("name").strip(),
                statement=statement,
                inline_expr=inline_expr,
                source_tokens=_extract_source_tokens(line),
                upstream_links=_parse_inline_refs(inline_expr, framework),
                source_ref=_source_ref(
                    relative_file,
                    line=line_number,
                    section="base",
                    anchor=f"base:{match.group('id').lower()}",
                    token=match.group("id"),
                ),
            )
        )
    return tuple(items)


def _parse_rules(
    lines: list[tuple[int, str]],
    *,
    relative_file: str,
) -> tuple[FrameworkRule, ...]:
    current_id: str | None = None
    current_name = ""
    current_line = 1
    participants: tuple[str, ...] = tuple()
    combination = ""
    outputs: tuple[str, ...] = tuple()
    invalids: tuple[str, ...] = tuple()
    bindings: tuple[str, ...] = tuple()
    items: list[FrameworkRule] = []

    def flush() -> None:
        nonlocal current_id, current_name, current_line, participants, combination, outputs, invalids, bindings
        if current_id is None:
            return
        items.append(
            FrameworkRule(
                rule_id=current_id,
                name=current_name,
                participant_bases=participants,
                combination=combination,
                output_capabilities=outputs,
                invalid_conclusions=invalids,
                boundary_bindings=bindings,
                source_ref=_source_ref(
                    relative_file,
                    line=current_line,
                    section="rule",
                    anchor=f"rule:{current_id.lower()}",
                    token=current_id,
                ),
            )
        )
        current_id = None
        current_name = ""
        current_line = 1
        participants = tuple()
        combination = ""
        outputs = tuple()
        invalids = tuple()
        bindings = tuple()

    for line_number, raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            continue
        top_match = RULE_TOP_PATTERN.match(stripped)
        if top_match is not None:
            flush()
            current_id = top_match.group("id")
            current_name = top_match.group("name").strip()
            current_line = line_number
            continue
        child_match = RULE_CHILD_PATTERN.match(raw_line)
        if child_match is None or current_id is None:
            continue
        body = child_match.group("body").strip().rstrip("。")
        if body.startswith("参与基："):
            participants = tuple(item.strip() for item in body.split("：", 1)[1].replace("`", "").split("+"))
        elif body.startswith("组合方式："):
            combination = body.split("：", 1)[1].strip()
        elif body.startswith("输出能力："):
            outputs = tuple(item.strip() for item in body.split("：", 1)[1].replace("`", "").split("+"))
        elif body.startswith("失效结论："):
            invalids = tuple(item.strip() for item in body.split("：", 1)[1].replace("`", "").split("+"))
        elif any(body.startswith(prefix) for prefix in RULE_PARAMETER_BINDING_PREFIXES):
            bindings = tuple(item.strip() for item in body.split("：", 1)[1].replace("`", "").split("+"))
    flush()
    return tuple(items)


def _section_lines(
    sections: dict[str, list[tuple[int, str]]],
    *titles: str,
) -> list[tuple[int, str]]:
    for title in titles:
        lines = sections.get(title)
        if lines is not None:
            return lines
    return []


def _parse_verifications(
    lines: list[tuple[int, str]],
    *,
    relative_file: str,
) -> tuple[FrameworkVerification, ...]:
    items: list[FrameworkVerification] = []
    for line_number, line in _clean_lines(lines):
        match = VERIFY_LINE_PATTERN.match(line)
        if match is None:
            continue
        items.append(
            FrameworkVerification(
                verification_id=match.group("id"),
                name=match.group("name").strip(),
                statement=match.group("body").strip().rstrip("。"),
                source_ref=_source_ref(
                    relative_file,
                    line=line_number,
                    section="verification",
                    anchor=f"verification:{match.group('id').lower()}",
                    token=match.group("id"),
                ),
            )
        )
    return tuple(items)


def parse_framework_module(path: str | Path) -> FrameworkModule:
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = (REPO_ROOT / file_path).resolve()
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title_match = TITLE_PATTERN.search(text)
    if title_match is None:
        raise ValueError(f"framework title is invalid: {file_path}")
    file_match = FRAMEWORK_FILE_PATTERN.fullmatch(file_path.name)
    if file_match is None:
        raise ValueError(f"framework filename is invalid: {file_path}")
    framework = file_path.parent.name
    relative_file = file_path.relative_to(REPO_ROOT).as_posix()
    sections = _split_sections(text)
    title_line = 1
    title_text = title_match.group(0)
    for line_number, line in enumerate(lines, start=1):
        if line.strip() == title_text.strip():
            title_line = line_number
            break
    return FrameworkModule(
        framework=framework,
        level=int(file_match.group("level")),
        module=int(file_match.group("module")),
        path=relative_file,
        title_cn=title_match.group("cn").strip(),
        title_en=title_match.group("en").strip(),
        intro=_extract_intro(text),
        capabilities=_parse_capabilities(
            sections.get("## 1. 能力声明（Capability Statement）", []),
            relative_file=relative_file,
        ),
        non_responsibilities=_parse_non_responsibilities(
            sections.get("## 1. 能力声明（Capability Statement）", []),
            relative_file=relative_file,
        ),
        boundaries=_parse_boundaries(
            _section_lines(sections, *PARAMETER_SECTION_TITLES),
            relative_file=relative_file,
        ),
        bases=_parse_bases(
            sections.get("## 3. 最小可行基（Minimum Viable Bases）", []),
            framework,
            relative_file=relative_file,
        ),
        rules=_parse_rules(
            sections.get("## 4. 基组合原则（Base Combination Principles）", []),
            relative_file=relative_file,
        ),
        verifications=_parse_verifications(
            sections.get("## 5. 验证（Verification）", []),
            relative_file=relative_file,
        ),
        source_ref=_source_ref(
            relative_file,
            line=title_line,
            section="module",
            anchor="module:title",
        ),
    )


def load_framework_catalog(root: Path = FRAMEWORK_ROOT) -> FrameworkCatalog:
    modules: list[FrameworkModule] = []
    for framework_dir in sorted(root.iterdir()):
        if not framework_dir.is_dir():
            continue
        for markdown_file in sorted(framework_dir.glob("L*-M*-*.md")):
            modules.append(parse_framework_module(markdown_file))
    return FrameworkCatalog(modules=tuple(modules))
