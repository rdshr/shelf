from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
from pathlib import Path
import re
from typing import Any


TITLE_ROLE = "title"
BODY_ROLE = "body"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _default_text_id(document_name: str, text: str) -> str:
    stem = Path(document_name).stem.strip()
    return stem or f"doc-{_sha256_text(text)[:12]}"

def normalize_document_text(text: str) -> str:
    normalized = text.replace("\ufeff", "").replace("\r\n", "\n").replace("\r", "\n")
    normalized_lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(normalized_lines).strip()


@dataclass(frozen=True)
class ParagraphBlock:
    block_id: str
    order_index: int
    text: str
    start_offset: int
    end_offset: int
    document_id: str
    is_document_end: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LabeledParagraphBlock:
    block_id: str
    order_index: int
    text: str
    start_offset: int
    end_offset: int
    document_id: str
    is_document_end: bool
    block_role: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChunkMatch:
    text_chunk_id: str
    chunk_id: int
    title_block_id: str
    body_block_id_set: tuple[str, ...]
    ordered_block_id_set: tuple[str, ...]
    start_order: int
    end_order: int
    closure_reason: str
    chunk_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "text_chunk_id": self.text_chunk_id,
            "chunk_id": self.chunk_id,
            "title_block_id": self.title_block_id,
            "body_block_id_set": list(self.body_block_id_set),
            "ordered_block_id_set": list(self.ordered_block_id_set),
            "start_order": self.start_order,
            "end_order": self.end_order,
            "closure_reason": self.closure_reason,
            "chunk_text": self.chunk_text,
        }


@dataclass(frozen=True)
class ChunkItem:
    chunk_id: int
    chunk_text: str
    title_block_id: str
    body_block_id_set: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "chunk_text": self.chunk_text,
            "title_block_id": self.title_block_id,
            "body_block_id_set": list(self.body_block_id_set),
        }


@dataclass(frozen=True)
class InvalidCombination:
    invalid_reason: str
    offending_object_id_set: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "invalid_reason": self.invalid_reason,
            "offending_object_id_set": list(self.offending_object_id_set),
        }


@dataclass(frozen=True)
class ValidationCheck:
    check_id: str
    passed: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    checks: tuple[ValidationCheck, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [item.to_dict() for item in self.checks],
        }


@dataclass(frozen=True)
class DocumentChunkingOutput:
    document_format: str
    text_id: str
    ordered_chunk_item_set: tuple[ChunkItem, ...]
    paragraph_block_set: tuple[ParagraphBlock, ...]
    trace_meta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_format": self.document_format,
            "text_id": self.text_id,
            "ordered_chunk_item_set": [item.to_dict() for item in self.ordered_chunk_item_set],
            "paragraph_block_set": [item.to_dict() for item in self.paragraph_block_set],
            "trace_meta": self.trace_meta,
        }


@dataclass(frozen=True)
class DocumentChunkingRunResult:
    document_name: str
    text_id: str
    normalized_text_sha256: str
    paragraph_block_set: tuple[ParagraphBlock, ...]
    labeled_paragraph_block_set: tuple[LabeledParagraphBlock, ...]
    chunk_match_set: tuple[ChunkMatch, ...]
    invalid_combination_set: tuple[InvalidCombination, ...]
    output: DocumentChunkingOutput
    validation: ValidationReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_name": self.document_name,
            "text_id": self.text_id,
            "normalized_text_sha256": self.normalized_text_sha256,
            "paragraph_block_set": [item.to_dict() for item in self.paragraph_block_set],
            "labeled_paragraph_block_set": [item.to_dict() for item in self.labeled_paragraph_block_set],
            "chunk_match_set": [item.to_dict() for item in self.chunk_match_set],
            "invalid_combination_set": [item.to_dict() for item in self.invalid_combination_set],
            "output": self.output.to_dict(),
            "validation": self.validation.to_dict(),
        }


def render_document_chunking_output_markdown(
    result: DocumentChunkingRunResult,
    *,
    document_format_field: str = "document_format",
    document_format_value: str | None = None,
    document_format_scope: str = "document_level",
    text_id_field: str = "text_id",
    chunk_id_field: str = "chunk_id",
    chunk_text_field: str = "chunk_text",
) -> str:
    if document_format_scope != "document_level":
        raise ValueError(f"unsupported document_format_scope: {document_format_scope}")

    resolved_document_format = document_format_value or result.output.document_format
    lines = [
        f"{document_format_field}: {resolved_document_format}",
        f"{text_id_field}: {result.output.text_id}",
        "",
    ]
    for chunk_item in result.output.ordered_chunk_item_set:
        lines.append(f"{chunk_id_field}: {chunk_item.chunk_id}")
        lines.append(f"{chunk_text_field}:")
        lines.extend(chunk_item.chunk_text.splitlines())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_paragraph_blocks(
    text: str,
    *,
    document_id: str,
    max_block_chars: int,
) -> tuple[ParagraphBlock, ...]:
    blocks: list[ParagraphBlock] = []
    position = 0
    block_start: int | None = None
    last_content_end: int | None = None
    order_index = 1

    for raw_line in text.splitlines(keepends=True):
        line_start = position
        position += len(raw_line)
        if raw_line.strip():
            if block_start is None:
                block_start = line_start
            last_content_end = position
            continue

        if block_start is None or last_content_end is None:
            continue

        end_offset = last_content_end
        while end_offset > block_start and text[end_offset - 1] == "\n":
            end_offset -= 1
        block_text = text[block_start:end_offset]
        if not block_text:
            block_start = None
            last_content_end = None
            continue
        if len(block_text) > max_block_chars:
            raise ValueError(
                f"paragraph block length exceeds max_block_chars={max_block_chars}: {len(block_text)}"
            )
        blocks.append(
            ParagraphBlock(
                block_id=f"{document_id}-pb-{order_index:04d}",
                order_index=order_index,
                text=block_text,
                start_offset=block_start,
                end_offset=end_offset,
                document_id=document_id,
                is_document_end=False,
            )
        )
        order_index += 1
        block_start = None
        last_content_end = None

    if block_start is not None and last_content_end is not None:
        end_offset = last_content_end
        while end_offset > block_start and text[end_offset - 1] == "\n":
            end_offset -= 1
        block_text = text[block_start:end_offset]
        if block_text:
            if len(block_text) > max_block_chars:
                raise ValueError(
                    f"paragraph block length exceeds max_block_chars={max_block_chars}: {len(block_text)}"
                )
            blocks.append(
                ParagraphBlock(
                    block_id=f"{document_id}-pb-{order_index:04d}",
                    order_index=order_index,
                    text=block_text,
                    start_offset=block_start,
                    end_offset=end_offset,
                    document_id=document_id,
                    is_document_end=False,
                )
            )

    if blocks:
        blocks[-1] = replace(blocks[-1], is_document_end=True)
    return tuple(blocks)


def label_paragraph_blocks(
    blocks: tuple[ParagraphBlock, ...],
    *,
    heading_pattern: str,
) -> tuple[LabeledParagraphBlock, ...]:
    compiled_heading_pattern = re.compile(heading_pattern)
    labeled_blocks: list[LabeledParagraphBlock] = []
    for block in blocks:
        first_line = block.text.splitlines()[0].strip() if block.text else ""
        block_role = TITLE_ROLE if compiled_heading_pattern.match(first_line) else BODY_ROLE
        labeled_blocks.append(
            LabeledParagraphBlock(
                block_id=block.block_id,
                order_index=block.order_index,
                text=block.text,
                start_offset=block.start_offset,
                end_offset=block.end_offset,
                document_id=block.document_id,
                is_document_end=block.is_document_end,
                block_role=block_role,
            )
        )
    return tuple(labeled_blocks)


def compose_text_chunks(
    labeled_blocks: tuple[LabeledParagraphBlock, ...],
    *,
    text_id: str,
) -> tuple[tuple[ChunkMatch, ...], tuple[InvalidCombination, ...]]:
    chunk_matches: list[ChunkMatch] = []
    invalids: list[InvalidCombination] = []
    current_title: LabeledParagraphBlock | None = None
    current_bodies: list[LabeledParagraphBlock] = []
    chunk_id = 1

    def close_current_chunk(closure_reason: str) -> None:
        nonlocal chunk_id, current_title, current_bodies
        if current_title is None:
            return
        ordered_blocks = [current_title, *current_bodies]
        chunk_matches.append(
            ChunkMatch(
                text_chunk_id=f"{text_id}-chunk-{chunk_id:04d}",
                chunk_id=chunk_id,
                title_block_id=current_title.block_id,
                body_block_id_set=tuple(item.block_id for item in current_bodies),
                ordered_block_id_set=tuple(item.block_id for item in ordered_blocks),
                start_order=current_title.order_index,
                end_order=ordered_blocks[-1].order_index,
                closure_reason=closure_reason,
                chunk_text="\n\n".join(item.text for item in ordered_blocks),
            )
        )
        chunk_id += 1
        current_title = None
        current_bodies = []

    for block in labeled_blocks:
        if block.block_role == TITLE_ROLE:
            if current_title is not None:
                close_current_chunk("next_title")
            current_title = block
            current_bodies = []
            continue

        if current_title is None:
            invalids.append(
                InvalidCombination(
                    invalid_reason="body block cannot form a chunk before the first title block",
                    offending_object_id_set=(block.block_id,),
                )
            )
            continue

        current_bodies.append(block)

    if current_title is not None:
        close_current_chunk("document_end")

    return tuple(chunk_matches), tuple(invalids)


def build_output(
    *,
    document_name: str,
    document_format: str,
    text_id: str,
    paragraph_blocks: tuple[ParagraphBlock, ...],
    labeled_blocks: tuple[LabeledParagraphBlock, ...],
    chunk_matches: tuple[ChunkMatch, ...],
    invalids: tuple[InvalidCombination, ...],
) -> DocumentChunkingOutput:
    trace_meta = {
        "document_name": document_name,
        "labeled_paragraph_block_set": [item.to_dict() for item in labeled_blocks],
        "chunk_match_set": [item.to_dict() for item in chunk_matches],
        "invalid_combination_set": [item.to_dict() for item in invalids],
    }
    return DocumentChunkingOutput(
        document_format=document_format,
        text_id=text_id,
        ordered_chunk_item_set=tuple(
            ChunkItem(
                chunk_id=item.chunk_id,
                chunk_text=item.chunk_text,
                title_block_id=item.title_block_id,
                body_block_id_set=item.body_block_id_set,
            )
            for item in chunk_matches
        ),
        paragraph_block_set=paragraph_blocks,
        trace_meta=trace_meta,
    )


def validate_document_chunking_result(
    result: DocumentChunkingRunResult,
    *,
    expected_document_format: str = "markdown",
    max_chunk_items: int,
) -> ValidationReport:
    paragraph_blocks = result.paragraph_block_set
    labeled_blocks = result.labeled_paragraph_block_set
    chunk_matches = result.chunk_match_set
    ordered_chunk_items = result.output.ordered_chunk_item_set

    checks: list[ValidationCheck] = []

    unique_order_indexes = {item.order_index for item in paragraph_blocks}
    terminal_flags = [item.is_document_end for item in paragraph_blocks]
    paragraph_blocks_are_valid = (
        bool(paragraph_blocks)
        and len(unique_order_indexes) == len(paragraph_blocks)
        and all(item.start_offset >= 0 and item.end_offset > item.start_offset for item in paragraph_blocks)
        and all(bool(item.text.strip()) for item in paragraph_blocks)
        and terminal_flags.count(True) == 1
        and terminal_flags[-1]
    )
    checks.append(
        ValidationCheck(
            check_id="V1",
            passed=paragraph_blocks_are_valid,
            detail="paragraph blocks keep unique order indexes, valid offsets, non-empty text, and one terminal block marker",
        )
    )

    roles_are_valid = (
        len(labeled_blocks) == len(paragraph_blocks)
        and all(item.block_role in {TITLE_ROLE, BODY_ROLE} for item in labeled_blocks)
        and all(
            labeled_blocks[index].is_document_end == paragraph_blocks[index].is_document_end
            for index in range(len(paragraph_blocks))
        )
    )
    checks.append(
        ValidationCheck(
            check_id="V2",
            passed=roles_are_valid,
            detail="labeled paragraph blocks only use title/body role values and preserve terminal-block identity",
        )
    )

    chunk_matches_are_valid = bool(chunk_matches) and not result.invalid_combination_set and all(
        match.ordered_block_id_set
        and match.title_block_id == match.ordered_block_id_set[0]
        and match.start_order <= match.end_order
        and list(match.ordered_block_id_set) == [match.title_block_id, *match.body_block_id_set]
        for match in chunk_matches
    )
    checks.append(
        ValidationCheck(
            check_id="V3",
            passed=chunk_matches_are_valid,
            detail="each chunk match starts with one title block and then zero or more ordered body blocks",
        )
    )

    output_is_valid = (
        bool(result.output.document_format.strip())
        and result.output.document_format == expected_document_format
        and bool(result.output.text_id)
        and len(ordered_chunk_items) <= max_chunk_items
        and len(ordered_chunk_items) == len(chunk_matches)
        and all(item.chunk_id >= 1 and bool(item.chunk_text.strip()) for item in ordered_chunk_items)
        and [item.chunk_id for item in ordered_chunk_items] == list(range(1, len(ordered_chunk_items) + 1))
        and all(
            chunk_item.chunk_id == chunk_match.chunk_id
            and chunk_item.chunk_text == chunk_match.chunk_text
            and chunk_item.title_block_id == chunk_match.title_block_id
            and chunk_item.body_block_id_set == chunk_match.body_block_id_set
            for chunk_item, chunk_match in zip(ordered_chunk_items, chunk_matches)
        )
    )
    checks.append(
        ValidationCheck(
            check_id="V4",
            passed=output_is_valid,
            detail="output keeps one document-level format declaration and preserves ordered chunk items with title/body block references",
        )
    )

    trace_is_valid = (
        result.output.trace_meta.get("document_name") == result.document_name
        and len(result.output.paragraph_block_set) == len(paragraph_blocks)
        and len(result.output.trace_meta.get("chunk_match_set", [])) == len(chunk_matches)
        and len(result.output.trace_meta.get("invalid_combination_set", [])) == len(result.invalid_combination_set)
    )
    checks.append(
        ValidationCheck(
            check_id="V5",
            passed=trace_is_valid,
            detail="output remains traceable back to paragraph blocks, chunk matches, and invalid combinations",
        )
    )

    passed = all(item.passed for item in checks)
    return ValidationReport(passed=passed, checks=tuple(checks))


def run_document_chunking_pipeline(
    *,
    document_name: str,
    text: str,
    text_id: str | None = None,
    document_format: str = "markdown",
    heading_pattern: str = r"^(#{1,6})\s+.+$",
    max_block_chars: int = 8000,
    max_chunk_items: int = 2000,
) -> DocumentChunkingRunResult:
    normalized_text = normalize_document_text(text)
    resolved_text_id = text_id or _default_text_id(document_name, normalized_text)
    paragraph_blocks = build_paragraph_blocks(
        normalized_text,
        document_id=resolved_text_id,
        max_block_chars=max_block_chars,
    )
    labeled_blocks = label_paragraph_blocks(
        paragraph_blocks,
        heading_pattern=heading_pattern,
    )
    chunk_matches, invalids = compose_text_chunks(
        labeled_blocks,
        text_id=resolved_text_id,
    )
    output = build_output(
        document_name=document_name,
        document_format=document_format,
        text_id=resolved_text_id,
        paragraph_blocks=paragraph_blocks,
        labeled_blocks=labeled_blocks,
        chunk_matches=chunk_matches,
        invalids=invalids,
    )
    provisional_result = DocumentChunkingRunResult(
        document_name=document_name,
        text_id=resolved_text_id,
        normalized_text_sha256=_sha256_text(normalized_text),
        paragraph_block_set=paragraph_blocks,
        labeled_paragraph_block_set=labeled_blocks,
        chunk_match_set=chunk_matches,
        invalid_combination_set=invalids,
        output=output,
        validation=ValidationReport(passed=False, checks=()),
    )
    validation = validate_document_chunking_result(
        provisional_result,
        expected_document_format=document_format,
        max_chunk_items=max_chunk_items,
    )
    return DocumentChunkingRunResult(
        document_name=document_name,
        text_id=resolved_text_id,
        normalized_text_sha256=_sha256_text(normalized_text),
        paragraph_block_set=paragraph_blocks,
        labeled_paragraph_block_set=labeled_blocks,
        chunk_match_set=chunk_matches,
        invalid_combination_set=invalids,
        output=output,
        validation=validation,
    )


def run_document_chunking_pipeline_on_file(
    input_file: str | Path,
    *,
    text_id: str | None = None,
    document_format: str = "markdown",
    heading_pattern: str = r"^(#{1,6})\s+.+$",
    max_block_chars: int = 8000,
    max_chunk_items: int = 2000,
) -> DocumentChunkingRunResult:
    resolved_file = Path(input_file).resolve()
    text = resolved_file.read_text(encoding="utf-8")
    return run_document_chunking_pipeline(
        document_name=resolved_file.name,
        text=text,
        text_id=text_id or resolved_file.stem,
        document_format=document_format,
        heading_pattern=heading_pattern,
        max_block_chars=max_block_chars,
        max_chunk_items=max_chunk_items,
    )
