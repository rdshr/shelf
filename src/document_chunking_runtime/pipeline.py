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
    rule_id: str
    capability_ids: tuple[str, ...]
    boundary: str
    passed: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "rule_id": self.rule_id,
            "capability_ids": list(self.capability_ids),
            "boundary": self.boundary,
            "passed": self.passed,
            "reason": self.reason,
            "conclusion": f"{self.rule_id} -> {'通过' if self.passed else '失败'} / {self.boundary} / {self.reason}",
        }


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


def _validation_reason(*, passed: bool, success: str, failures: list[str]) -> str:
    if passed:
        return success
    return "；".join(failures) if failures else "未满足当前验证要求"


def validate_document_chunking_result(
    result: DocumentChunkingRunResult,
    *,
    normalized_text: str,
    heading_pattern: str,
    max_block_chars: int,
    expected_document_format: str = "markdown",
    max_chunk_items: int,
) -> ValidationReport:
    paragraph_blocks = result.paragraph_block_set
    labeled_blocks = result.labeled_paragraph_block_set
    chunk_matches = result.chunk_match_set
    ordered_chunk_items = result.output.ordered_chunk_item_set
    replayed_paragraph_blocks = build_paragraph_blocks(
        normalized_text,
        document_id=result.text_id,
        max_block_chars=max_block_chars,
    )
    replayed_labeled_blocks = label_paragraph_blocks(
        replayed_paragraph_blocks,
        heading_pattern=heading_pattern,
    )
    replayed_chunk_matches, replayed_invalids = compose_text_chunks(
        replayed_labeled_blocks,
        text_id=result.text_id,
    )

    checks: list[ValidationCheck] = []

    unique_order_indexes = {item.order_index for item in paragraph_blocks}
    terminal_flags = [item.is_document_end for item in paragraph_blocks]
    paragraph_block_failures: list[str] = []
    paragraph_blocks_are_valid = (
        bool(paragraph_blocks)
        and len(unique_order_indexes) == len(paragraph_blocks)
        and all(item.start_offset >= 0 and item.end_offset > item.start_offset for item in paragraph_blocks)
        and all(bool(item.text.strip()) for item in paragraph_blocks)
        and terminal_flags.count(True) == 1
        and terminal_flags[-1]
        and replayed_paragraph_blocks == paragraph_blocks
    )
    if not paragraph_blocks:
        paragraph_block_failures.append("R1 未产出任何段落块")
    if len(unique_order_indexes) != len(paragraph_blocks):
        paragraph_block_failures.append("段落块顺序索引不唯一")
    if any(item.start_offset < 0 or item.end_offset <= item.start_offset for item in paragraph_blocks):
        paragraph_block_failures.append("段落块起止范围非法")
    if any(not item.text.strip() for item in paragraph_blocks):
        paragraph_block_failures.append("存在空段落块")
    if terminal_flags.count(True) != 1 or (terminal_flags and not terminal_flags[-1]):
        paragraph_block_failures.append("文档结束标识不稳定")
    if replayed_paragraph_blocks != paragraph_blocks:
        paragraph_block_failures.append("同一输入文档复跑后未得到相同的 ParagraphBlock_set")
    checks.append(
        ValidationCheck(
            check_id="V1",
            rule_id="R1",
            capability_ids=("C1",),
            boundary="NORMDOC/CUTRELY/BLOCKNUM",
            passed=paragraph_blocks_are_valid,
            reason=_validation_reason(
                passed=paragraph_blocks_are_valid,
                success=f"同一输入文档稳定产出 {len(paragraph_blocks)} 个段落块，R1 兑现了 C1。",
                failures=paragraph_block_failures,
            ),
        )
    )

    role_failures: list[str] = []
    roles_are_valid = (
        len(labeled_blocks) == len(paragraph_blocks)
        and all(item.block_role in {TITLE_ROLE, BODY_ROLE} for item in labeled_blocks)
        and all(
            labeled_blocks[index].is_document_end == paragraph_blocks[index].is_document_end
            for index in range(len(paragraph_blocks))
        )
        and replayed_labeled_blocks == labeled_blocks
    )
    if len(labeled_blocks) != len(paragraph_blocks):
        role_failures.append("角色判型后的段落块数量与输入段落块数量不一致")
    if any(item.block_role not in {TITLE_ROLE, BODY_ROLE} for item in labeled_blocks):
        role_failures.append("存在超出 title/body 的角色值")
    if any(
        labeled_blocks[index].is_document_end != paragraph_blocks[index].is_document_end
        for index in range(min(len(paragraph_blocks), len(labeled_blocks)))
    ):
        role_failures.append("角色判型破坏了段落结束标识")
    if replayed_labeled_blocks != labeled_blocks:
        role_failures.append("同一段落块序列复跑后未得到相同的 title/body 判型结果")
    checks.append(
        ValidationCheck(
            check_id="V2",
            rule_id="R2",
            capability_ids=("C2",),
            boundary="ROLEJUDGE/ROLETYPE",
            passed=roles_are_valid,
            reason=_validation_reason(
                passed=roles_are_valid,
                success=f"同一段落块序列稳定得到 {len(labeled_blocks)} 个角色判型结果，R2 兑现了 C2。",
                failures=role_failures,
            ),
        )
    )

    chunk_failures: list[str] = []
    labeled_by_id = {item.block_id: item for item in labeled_blocks}
    used_block_ids: set[str] = set()
    chunk_membership_covers_all_blocks = True
    for match in chunk_matches:
        ordered_block_ids = list(match.ordered_block_id_set)
        expected_block_ids = [match.title_block_id, *match.body_block_id_set]
        if not ordered_block_ids:
            chunk_failures.append(f"{match.text_chunk_id} 未包含任何段落块")
            continue
        if match.title_block_id != ordered_block_ids[0]:
            chunk_failures.append(f"{match.text_chunk_id} 的标题锚点不是首段落块")
        if ordered_block_ids != expected_block_ids:
            chunk_failures.append(f"{match.text_chunk_id} 的 ordered_block_id_set 与 title/body 归属不一致")
        if match.start_order > match.end_order:
            chunk_failures.append(f"{match.text_chunk_id} 的顺序范围反转")
        block_orders = [labeled_by_id[item].order_index for item in ordered_block_ids if item in labeled_by_id]
        if len(block_orders) != len(ordered_block_ids):
            chunk_failures.append(f"{match.text_chunk_id} 引用了不存在的段落块")
            continue
        if block_orders != list(range(match.start_order, match.end_order + 1)):
            chunk_failures.append(f"{match.text_chunk_id} 未按连续顺序吸收正文块")
        overlap_ids = [item for item in ordered_block_ids if item in used_block_ids]
        if overlap_ids:
            chunk_failures.append(f"{match.text_chunk_id} 与其他文本块发生段落块重叠: {', '.join(overlap_ids)}")
        used_block_ids.update(ordered_block_ids)
    all_labeled_block_ids = {item.block_id for item in labeled_blocks}
    if used_block_ids != all_labeled_block_ids:
        chunk_membership_covers_all_blocks = False
        missing_ids = sorted(all_labeled_block_ids - used_block_ids)
        if missing_ids:
            chunk_failures.append(f"仍有段落块未被文本块归组: {', '.join(missing_ids[:5])}")
    if result.invalid_combination_set:
        chunk_failures.append("存在未被消化的非法组合")
    if replayed_chunk_matches != chunk_matches or replayed_invalids != result.invalid_combination_set:
        chunk_failures.append("同一输入复跑后未得到相同的文本块打包结果")
    chunk_matches_are_valid = (
        bool(chunk_matches)
        and not result.invalid_combination_set
        and chunk_membership_covers_all_blocks
        and not chunk_failures
    )
    checks.append(
        ValidationCheck(
            check_id="V3",
            rule_id="R3",
            capability_ids=("C3",),
            boundary="ROLEJUDGE/ROLETYPE/BLOCKCOMBINE",
            passed=chunk_matches_are_valid,
            reason=_validation_reason(
                passed=chunk_matches_are_valid,
                success=f"稳定产出 {len(chunk_matches)} 个满足 1 标题 + n 正文 的文本块，R3 兑现了 C3。",
                failures=chunk_failures,
            ),
        )
    )

    output_failures: list[str] = []
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
    if not result.output.document_format.strip():
        output_failures.append("结果文档缺少 document_format")
    if result.output.document_format != expected_document_format:
        output_failures.append("结果文档的 document_format 与产品承诺不一致")
    if not result.output.text_id:
        output_failures.append("结果文档缺少 text_id")
    if len(ordered_chunk_items) > max_chunk_items:
        output_failures.append("输出文本块数量超出产品上限")
    if len(ordered_chunk_items) != len(chunk_matches):
        output_failures.append("ordered_chunk_item_set 与 chunk_match_set 数量不一致")
    if [item.chunk_id for item in ordered_chunk_items] != list(range(1, len(ordered_chunk_items) + 1)):
        output_failures.append("chunk_id 序列不稳定")
    if any(item.chunk_id < 1 or not item.chunk_text.strip() for item in ordered_chunk_items):
        output_failures.append("存在空文本块或非法 chunk_id")
    if any(
        chunk_item.chunk_id != chunk_match.chunk_id
        or chunk_item.chunk_text != chunk_match.chunk_text
        or chunk_item.title_block_id != chunk_match.title_block_id
        or chunk_item.body_block_id_set != chunk_match.body_block_id_set
        for chunk_item, chunk_match in zip(ordered_chunk_items, chunk_matches)
    ):
        output_failures.append("输出文本块与组合阶段结果不一致")
    checks.append(
        ValidationCheck(
            check_id="V4",
            rule_id="R4",
            capability_ids=("C4", "C5"),
            boundary="OUTPUT/BLOCKNUM/BLOCKCOMBINE/ROLETYPE",
            passed=output_is_valid,
            reason=_validation_reason(
                passed=output_is_valid,
                success=f"结果文档稳定封装了 {len(ordered_chunk_items)} 个文本块单元，R4 兑现了 C4 + C5。",
                failures=output_failures,
            ),
        )
    )

    trace_failures: list[str] = []
    paragraph_block_ids = {item.block_id for item in paragraph_blocks}
    trace_chunk_match_set = result.output.trace_meta.get("chunk_match_set", [])
    trace_invalid_set = result.output.trace_meta.get("invalid_combination_set", [])
    trace_labeled_blocks = result.output.trace_meta.get("labeled_paragraph_block_set", [])
    trace_is_valid = (
        result.output.trace_meta.get("document_name") == result.document_name
        and result.output.paragraph_block_set == paragraph_blocks
        and len(result.output.paragraph_block_set) == len(paragraph_blocks)
        and trace_chunk_match_set == [item.to_dict() for item in chunk_matches]
        and trace_invalid_set == [item.to_dict() for item in result.invalid_combination_set]
        and trace_labeled_blocks == [item.to_dict() for item in labeled_blocks]
        and all(item.title_block_id in paragraph_block_ids for item in ordered_chunk_items)
        and all(block_id in paragraph_block_ids for item in ordered_chunk_items for block_id in item.body_block_id_set)
    )
    if result.output.trace_meta.get("document_name") != result.document_name:
        trace_failures.append("trace_meta.document_name 未回连到当前输入文档")
    if result.output.paragraph_block_set != paragraph_blocks:
        trace_failures.append("输出结果未保留完整的 paragraph_block_set")
    if trace_chunk_match_set != [item.to_dict() for item in chunk_matches]:
        trace_failures.append("trace_meta.chunk_match_set 未完整保留中间组合状态")
    if trace_invalid_set != [item.to_dict() for item in result.invalid_combination_set]:
        trace_failures.append("trace_meta.invalid_combination_set 未完整保留非法组合状态")
    if trace_labeled_blocks != [item.to_dict() for item in labeled_blocks]:
        trace_failures.append("trace_meta.labeled_paragraph_block_set 未完整保留角色判型状态")
    if any(item.title_block_id not in paragraph_block_ids for item in ordered_chunk_items):
        trace_failures.append("存在无法回连到 paragraph_block_set 的 title_block_id")
    if any(block_id not in paragraph_block_ids for item in ordered_chunk_items for block_id in item.body_block_id_set):
        trace_failures.append("存在无法回连到 paragraph_block_set 的 body_block_id")
    checks.append(
        ValidationCheck(
            check_id="V5",
            rule_id="R4",
            capability_ids=("C6",),
            boundary="OUTPUT/BLOCKNUM/BLOCKCOMBINE/ROLETYPE",
            passed=trace_is_valid,
            reason=_validation_reason(
                passed=trace_is_valid,
                success="结果对象保留了段落块、角色判型、文本块归组与非法组合痕迹，R4 兑现了 C6。",
                failures=trace_failures,
            ),
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
        normalized_text=normalized_text,
        heading_pattern=heading_pattern,
        max_block_chars=max_block_chars,
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
