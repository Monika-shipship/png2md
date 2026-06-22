import hashlib
import re
from dataclasses import dataclass
from copy import deepcopy
from typing import Any, Dict, List

from .figures import analyze_figure_description
from .formula_quality import assess_formula_text, normalize_formula_text
from .renderer import render_page_ir_to_markdown
from .validators import ValidationIssue, is_api_error_text, validate_slide_markdown


KNOWN_OPS = {
    "strip_chatter",
    "fix_heading",
    "drop_empty",
    "merge_broken_line",
    "mark_failed_page",
}

SAFE_OPS = {
    "strip_chatter",
    "fix_heading",
    "drop_empty",
    "merge_broken_line",
}

BLOCK_REFINER_VERSION = "block-refiner-2026-06-21"

BLOCK_KNOWN_OPS = {
    "merge_block",
    "drop_block",
    "promote_heading",
    "demote_heading",
    "convert_figure_note",
    "mark_uncertain",
    "normalize_formula",
}

BLOCK_SAFE_OPS = set(BLOCK_KNOWN_OPS)

BLOCK_ALLOWED_ORIGINS = {
    "vision_ocr",
    "vision_formula",
    "vision_description",
    "vision_table",
    "vision_uncertain",
    "brain_refine",
    "renderer_template",
    "refiner_op",
}

BLOCK_ALLOWED_TYPES = {
    "heading",
    "paragraph",
    "list",
    "formula_inline",
    "formula_block",
    "figure_note",
    "table",
    "image_ref",
    "uncertain",
}

BLOCK_VISION_ORIGINS = {
    "vision_ocr",
    "vision_formula",
    "vision_description",
    "vision_table",
    "vision_uncertain",
}


@dataclass(frozen=True)
class Suspect:
    id: str
    code: str
    op: str
    reason: str
    evidence: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "op": self.op,
            "reason": self.reason,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class RefineResult:
    markdown: str
    applied_ops: List[Dict[str, Any]]
    dismissed: List[Dict[str, Any]]
    validation: Dict[str, Any]

    @property
    def changed(self) -> bool:
        return bool(self.applied_ops)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "changed": self.changed,
            "applied_ops": self.applied_ops,
            "dismissed": self.dismissed,
            "validation": self.validation,
        }


@dataclass(frozen=True)
class BlockSuspect:
    id: str
    code: str
    op: Dict[str, Any]
    reason: str
    evidence: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "op": self.op,
            "reason": self.reason,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class BlockRefineResult:
    page_ir: Dict[str, Any]
    applied_ops: List[Dict[str, Any]]
    dismissed: List[Dict[str, Any]]
    validation: Dict[str, Any]

    @property
    def changed(self) -> bool:
        return bool(self.applied_ops)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": BLOCK_REFINER_VERSION,
            "changed": self.changed,
            "applied_ops": self.applied_ops,
            "dismissed": self.dismissed,
            "validation": self.validation,
        }


def detect_markdown_suspects(markdown: str, slide_no: int) -> List[Suspect]:
    text = markdown or ""
    suspects: List[Suspect] = []
    lines = text.splitlines()
    first_nonempty = next((line.strip() for line in lines if line.strip()), "")

    if first_nonempty and _is_chatter_line(first_nonempty):
        suspects.append(
            Suspect(
                id=f"p{slide_no:04d}-s001",
                code="leading_chatter",
                op="strip_chatter",
                reason="输出开头包含模型寒暄或处理说明。",
                evidence=first_nonempty,
            )
        )

    heading = re.match(r"^#\s*Slide\s+0*(\d+)\b", first_nonempty, flags=re.IGNORECASE)
    if not heading or int(heading.group(1)) != slide_no:
        suspects.append(
            Suspect(
                id=f"p{slide_no:04d}-s002",
                code="heading_missing_or_mismatch",
                op="fix_heading",
                reason=f"输出没有以 # Slide {slide_no} 作为第一页标题。",
                evidence=first_nonempty,
            )
        )

    if re.search(r"\n{3,}", text):
        suspects.append(
            Suspect(
                id=f"p{slide_no:04d}-s003",
                code="excess_blank_lines",
                op="drop_empty",
                reason="输出包含连续空行，可压缩为空白段落。",
            )
        )

    if re.search(r"(?m)[A-Za-z]-\n[A-Za-z]", text):
        suspects.append(
            Suspect(
                id=f"p{slide_no:04d}-s004",
                code="broken_hyphenated_line",
                op="merge_broken_line",
                reason="英文单词疑似被换行断开。",
            )
        )

    return suspects


def detect_block_suspects(page_ir: Dict[str, Any]) -> List[BlockSuspect]:
    blocks = page_ir.get("blocks") or []
    suspects: List[BlockSuspect] = []
    for index, block in enumerate(blocks):
        block_id = block.get("id")
        block_type = block.get("type")
        text = (block.get("text") or block.get("description") or "").strip()
        if not block_id:
            continue
        suspect_no = len(suspects) + 1

        if not text:
            suspects.append(
                _block_suspect(
                    page_ir,
                    suspect_no,
                    "empty_block",
                    {"op": "drop_block", "id": block_id, "reason": "empty"},
                    "block 内容为空，应删除。",
                )
            )
            continue

        if block_type == "heading" and _looks_like_body_text(text):
            suspects.append(
                _block_suspect(
                    page_ir,
                    suspect_no,
                    "heading_looks_like_body",
                    {"op": "demote_heading", "id": block_id},
                    "heading block 更像正文，应降级为 paragraph。",
                    text,
                )
            )
            continue

        if block_type == "paragraph" and _looks_like_heading_text(text):
            suspects.append(
                _block_suspect(
                    page_ir,
                    suspect_no,
                    "paragraph_looks_like_heading",
                    {"op": "promote_heading", "id": block_id},
                    "paragraph block 更像标题，应升级为 heading。",
                    text,
                )
            )
            continue

        if block_type == "paragraph" and _looks_like_figure_description(text):
            suspects.append(
                _block_suspect(
                    page_ir,
                    suspect_no,
                    "paragraph_looks_like_figure",
                    {"op": "convert_figure_note", "id": block_id},
                    "paragraph block 更像图示说明，应转为 figure_note。",
                    text,
                )
            )
            continue

        if block_type in {"paragraph", "list"} and _has_uncertain_marker(text):
            suspects.append(
                _block_suspect(
                    page_ir,
                    suspect_no,
                    "text_contains_uncertain_marker",
                    {"op": "mark_uncertain", "id": block_id},
                    "block 含不确定识别标记，应转为 uncertain。",
                    text,
                )
            )
            continue

        if block_type in {"formula_inline", "formula_block"} and _formula_needs_normalize(text):
            suspects.append(
                _block_suspect(
                    page_ir,
                    suspect_no,
                    "formula_needs_normalize",
                    {"op": "normalize_formula", "id": block_id},
                    "公式 block 含外层公式分隔符，应规范为内部 LaTeX 文本。",
                    text,
                )
            )
            continue

        if index + 1 < len(blocks) and block_type == "paragraph":
            next_block = blocks[index + 1]
            if next_block.get("type") == "paragraph" and text.endswith("-"):
                suspects.append(
                    _block_suspect(
                        page_ir,
                        suspect_no,
                        "broken_hyphenated_block",
                        {"op": "merge_block", "a": block_id, "b": next_block.get("id")},
                        "相邻 paragraph 疑似英文单词被跨 block 断开。",
                        text,
                    )
                )
    return suspects


def apply_block_op_checked(
    page_ir: Dict[str, Any],
    op: Dict[str, Any],
    *,
    slide_no: int | None = None,
    target_raw: str | None = None,
) -> tuple[Dict[str, Any], bool, Dict[str, Any]]:
    op_name = op.get("op")
    if op_name not in BLOCK_SAFE_OPS:
        return page_ir, False, {"reason": "unknown_or_unsafe_op"}

    slide = slide_no or int(page_ir.get("source_page") or 0)
    before_validation = validate_slide_markdown(
        render_page_ir_to_markdown(page_ir, slide),
        slide,
        target_raw=target_raw,
    )
    before_ids = _block_ids(page_ir)
    candidate = deepcopy(page_ir)
    changed = _apply_block_op(candidate, op)
    if not changed:
        return page_ir, False, {"reason": "no_change", "before_block_ids": before_ids, "after_block_ids": before_ids}

    contract_errors = _page_ir_contract_errors(candidate)
    if contract_errors:
        return page_ir, False, {
            "reason": "page_ir_contract_failed",
            "errors": contract_errors,
            "before_block_ids": before_ids,
            "after_block_ids": _block_ids(candidate),
        }

    after_markdown = render_page_ir_to_markdown(candidate, slide)
    after_validation = validate_slide_markdown(after_markdown, slide, target_raw=target_raw)
    if not _is_no_worse(before_validation.errors, after_validation.errors):
        return page_ir, False, {
            "reason": "validation_would_get_worse",
            "validation": after_validation.to_dict(),
            "before_block_ids": before_ids,
            "after_block_ids": _block_ids(candidate),
        }

    return candidate, True, {
        "validation": after_validation.to_dict(),
        "before_block_ids": before_ids,
        "after_block_ids": _block_ids(candidate),
    }


def refine_page_ir(
    page_ir: Dict[str, Any],
    *,
    slide_no: int | None = None,
    target_raw: str | None = None,
) -> BlockRefineResult:
    current = deepcopy(page_ir)
    applied = []
    dismissed = []
    for suspect in detect_block_suspects(current):
        current, ok, detail = apply_block_op_checked(
            current,
            suspect.op,
            slide_no=slide_no,
            target_raw=target_raw,
        )
        item = suspect.to_dict()
        if ok:
            item.update(detail)
            applied.append(item)
        else:
            item["dismissed"] = detail
            dismissed.append(item)

    slide = slide_no or int(current.get("source_page") or 0)
    validation = validate_slide_markdown(render_page_ir_to_markdown(current, slide), slide, target_raw=target_raw)
    return BlockRefineResult(current, applied, dismissed, validation.to_dict())


def apply_op_checked(
    markdown: str,
    suspect: Suspect,
    slide_no: int,
    *,
    raw_response: str | None = None,
    target_raw: str | None = None,
    target_blocks: list[dict] | None = None,
) -> tuple[str, bool, Dict[str, Any]]:
    if suspect.op not in SAFE_OPS or is_api_error_text(raw_response) or is_api_error_text(markdown):
        return markdown, False, {"reason": "unsafe_or_error_text"}

    before = validate_slide_markdown(
        markdown,
        slide_no,
        raw_response=raw_response,
        target_raw=target_raw,
        target_blocks=target_blocks,
    )
    candidate = _apply_op(markdown, suspect.op, slide_no)
    if candidate == markdown:
        return markdown, False, {"reason": "no_change"}

    after = validate_slide_markdown(
        candidate,
        slide_no,
        raw_response=raw_response,
        target_raw=target_raw,
        target_blocks=target_blocks,
    )
    if _is_no_worse(before.errors, after.errors):
        return candidate, True, after.to_dict()
    return markdown, False, {"reason": "validation_would_get_worse", "validation": after.to_dict()}


def refine_slide_markdown(
    markdown: str,
    slide_no: int,
    *,
    raw_response: str | None = None,
    target_raw: str | None = None,
    target_blocks: list[dict] | None = None,
) -> RefineResult:
    current = markdown
    applied = []
    dismissed = []
    for suspect in detect_markdown_suspects(current, slide_no):
        current, ok, validation = apply_op_checked(
            current,
            suspect,
            slide_no,
            raw_response=raw_response,
            target_raw=target_raw,
            target_blocks=target_blocks,
        )
        if ok:
            item = suspect.to_dict()
            item["validation"] = validation
            applied.append(item)
        else:
            item = suspect.to_dict()
            item["dismissed"] = validation
            dismissed.append(item)

    final_validation = validate_slide_markdown(
        current,
        slide_no,
        raw_response=raw_response,
        target_raw=target_raw,
        target_blocks=target_blocks,
    )
    return RefineResult(
        markdown=current,
        applied_ops=applied,
        dismissed=dismissed,
        validation=final_validation.to_dict(),
    )


def _apply_op(markdown: str, op: str, slide_no: int) -> str:
    if op == "strip_chatter":
        return _strip_leading_chatter(markdown)
    if op == "fix_heading":
        return _fix_heading(markdown, slide_no)
    if op == "drop_empty":
        return re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"
    if op == "merge_broken_line":
        return re.sub(r"(?m)([A-Za-z])-\n([A-Za-z])", r"\1\2", markdown).strip() + "\n"
    return markdown


def _strip_leading_chatter(markdown: str) -> str:
    lines = markdown.splitlines()
    while lines and (not lines[0].strip() or _is_chatter_line(lines[0])):
        lines.pop(0)
    return "\n".join(lines).strip() + "\n"


def _fix_heading(markdown: str, slide_no: int) -> str:
    text = markdown.strip()
    lines = text.splitlines()
    if lines and re.match(r"^#\s*Slide\s+\d+\b", lines[0], flags=re.IGNORECASE):
        lines[0] = f"# Slide {slide_no}"
        return "\n".join(lines).strip() + "\n"
    return f"# Slide {slide_no}\n\n{text}".strip() + "\n"


def _is_chatter_line(line: str) -> bool:
    normalized = line.strip().lstrip("> ").strip()
    prefixes = (
        "好的",
        "当然",
        "以下是",
        "下面是",
        "根据您提供",
        "基于您提供",
        "我将",
        "我已经",
    )
    return normalized.startswith(prefixes)


def _is_no_worse(before: List[ValidationIssue], after: List[ValidationIssue]) -> bool:
    before_codes = {issue.code for issue in before}
    after_codes = {issue.code for issue in after}
    return after_codes.issubset(before_codes)


def _block_suspect(
    page_ir: Dict[str, Any],
    suspect_no: int,
    code: str,
    op: Dict[str, Any],
    reason: str,
    evidence: str | None = None,
) -> BlockSuspect:
    page = int(page_ir.get("source_page") or 0)
    return BlockSuspect(
        id=f"p{page:04d}-bs{suspect_no:03d}",
        code=code,
        op=op,
        reason=reason,
        evidence=evidence,
    )


def _apply_block_op(page_ir: Dict[str, Any], op: Dict[str, Any]) -> bool:
    op_name = op.get("op")
    if op_name == "merge_block":
        return _op_merge_block(page_ir, op.get("a"), op.get("b"))
    if op_name == "drop_block":
        return _op_drop_block(page_ir, op.get("id"), op.get("reason"))
    if op_name == "promote_heading":
        return _op_set_block_type(page_ir, op.get("id"), "heading")
    if op_name == "demote_heading":
        return _op_set_block_type(page_ir, op.get("id"), "paragraph")
    if op_name == "convert_figure_note":
        return _op_convert_figure_note(page_ir, op.get("id"))
    if op_name == "mark_uncertain":
        return _op_mark_uncertain(page_ir, op.get("id"))
    if op_name == "normalize_formula":
        return _op_normalize_formula(page_ir, op.get("id"))
    return False


def _op_merge_block(page_ir: Dict[str, Any], a_id: str | None, b_id: str | None) -> bool:
    blocks = page_ir.get("blocks") or []
    a_index = _find_block_index(blocks, a_id)
    b_index = _find_block_index(blocks, b_id)
    if a_index is None or b_index is None or b_index != a_index + 1:
        return False
    a = blocks[a_index]
    b = blocks[b_index]
    if a.get("type") != b.get("type"):
        return False
    a_text = (a.get("text") or "").rstrip()
    b_text = (b.get("text") or "").lstrip()
    if not a_text and not b_text:
        return False
    if a_text.endswith("-") and b_text:
        merged_text = a_text[:-1] + b_text
    else:
        merged_text = f"{a_text}\n{b_text}".strip()
    before_ids = [a.get("id"), b.get("id")]
    a["text"] = merged_text
    _mark_refiner_origin(a, "merge_block", before_ids=before_ids)
    del blocks[b_index]
    return True


def _op_drop_block(page_ir: Dict[str, Any], block_id: str | None, reason: str | None) -> bool:
    blocks = page_ir.get("blocks") or []
    index = _find_block_index(blocks, block_id)
    if index is None:
        return False
    block = blocks[index]
    text = (block.get("text") or block.get("description") or "").strip()
    if text and reason not in {"empty", "page_artifact"}:
        return False
    del blocks[index]
    return True


def _op_set_block_type(page_ir: Dict[str, Any], block_id: str | None, block_type: str) -> bool:
    block = _find_block(page_ir.get("blocks") or [], block_id)
    if not block or block.get("type") == block_type:
        return False
    block["type"] = block_type
    if block_type == "heading":
        block["confidence"] = max(float(block.get("confidence") or 0.0), 0.62)
    _mark_refiner_origin(block, f"set_{block_type}")
    return True


def _op_convert_figure_note(page_ir: Dict[str, Any], block_id: str | None) -> bool:
    block = _find_block(page_ir.get("blocks") or [], block_id)
    if not block or block.get("type") == "figure_note":
        return False
    text = (block.get("text") or "").strip()
    if not text:
        return False
    analysis = analyze_figure_description(text)
    block["type"] = "figure_note"
    block.update(analysis.to_block_fields())
    block["confidence"] = 0.25 if analysis.unrecognizable else max(float(block.get("confidence") or 0.0), 0.72)
    _mark_refiner_origin(block, "convert_figure_note")
    return True


def _op_mark_uncertain(page_ir: Dict[str, Any], block_id: str | None) -> bool:
    block = _find_block(page_ir.get("blocks") or [], block_id)
    if not block or block.get("type") == "uncertain":
        return False
    block["type"] = "uncertain"
    block["confidence"] = min(float(block.get("confidence") or 0.25), 0.25)
    _mark_refiner_origin(block, "mark_uncertain")
    return True


def _op_normalize_formula(page_ir: Dict[str, Any], block_id: str | None) -> bool:
    block = _find_block(page_ir.get("blocks") or [], block_id)
    if not block or block.get("type") not in {"formula_inline", "formula_block"}:
        return False
    text = (block.get("text") or "").strip()
    normalized = _normalize_formula_text(text)
    if normalized == text:
        return False
    block["text"] = normalized
    block["type"] = "formula_block"
    _update_formula_fields(block)
    _mark_refiner_origin(block, "normalize_formula")
    return True


def _mark_refiner_origin(block: Dict[str, Any], op: str, *, before_ids: list[str | None] | None = None):
    evidence = block.setdefault("evidence", {})
    evidence["refiner_op"] = op
    if before_ids:
        evidence["before_block_ids"] = before_ids
    block["origin"] = "refiner_op"


def _update_formula_fields(block: Dict[str, Any]):
    quality = assess_formula_text(block.get("text") or "")
    block["latex"] = quality.latex
    block["formula_quality"] = quality.to_dict()


def _find_block(blocks: List[Dict[str, Any]], block_id: str | None) -> Dict[str, Any] | None:
    index = _find_block_index(blocks, block_id)
    return blocks[index] if index is not None else None


def _find_block_index(blocks: List[Dict[str, Any]], block_id: str | None) -> int | None:
    if not block_id:
        return None
    for index, block in enumerate(blocks):
        if block.get("id") == block_id:
            return index
    return None


def _block_ids(page_ir: Dict[str, Any]) -> list[str]:
    return [str(block.get("id")) for block in page_ir.get("blocks") or [] if block.get("id")]


def _page_ir_contract_errors(page_ir: Dict[str, Any]) -> list[str]:
    errors = []
    if not isinstance(page_ir, dict):
        return ["page_ir_not_dict"]
    raw_text = page_ir.get("raw_text")
    if "raw_text" not in page_ir:
        errors.append("raw_text_missing")
    elif not isinstance(raw_text, str):
        errors.append("raw_text_not_string")
    if "raw_text_sha256" not in page_ir:
        errors.append("raw_text_sha256_missing")
    elif not isinstance(page_ir.get("raw_text_sha256"), str):
        errors.append("raw_text_sha256_not_string")
    elif isinstance(raw_text, str) and page_ir.get("raw_text_sha256") != _sha256_text(raw_text):
        errors.append("raw_text_sha256_mismatch")
    blocks = page_ir.get("blocks")
    if not isinstance(blocks, list):
        return ["blocks_not_list"]
    seen = set()
    for index, block in enumerate(blocks):
        block_id = block.get("id")
        if not block_id:
            errors.append(f"block_{index}_missing_id")
        elif block_id in seen:
            errors.append(f"block_{index}_duplicate_id")
        seen.add(block_id)
        block_type = block.get("type")
        if not block_type:
            errors.append(f"block_{index}_missing_type")
        elif block_type not in BLOCK_ALLOWED_TYPES:
            errors.append(f"block_{index}_unknown_type")
        if "text" not in block and block_type != "image_ref":
            errors.append(f"block_{index}_missing_text")
        if block.get("source_page") != page_ir.get("source_page"):
            errors.append(f"block_{index}_source_page_mismatch")
        if "confidence" not in block:
            errors.append(f"block_{index}_missing_confidence")
        elif not _valid_confidence(block.get("confidence")):
            errors.append(f"block_{index}_invalid_confidence")
        if "bbox" not in block:
            errors.append(f"block_{index}_missing_bbox")
        elif not _valid_bbox(block.get("bbox")):
            errors.append(f"block_{index}_invalid_bbox")
        origin = block.get("origin")
        if not origin:
            errors.append(f"block_{index}_missing_origin")
        elif origin not in BLOCK_ALLOWED_ORIGINS:
            errors.append(f"block_{index}_unknown_origin")
        if "evidence" not in block:
            errors.append(f"block_{index}_missing_evidence")
        elif not isinstance(block.get("evidence"), dict):
            errors.append(f"block_{index}_invalid_evidence")
        else:
            errors.extend(_block_evidence_errors(index, block))
    return errors


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _valid_bbox(value) -> bool:
    if value is None:
        return True
    if not isinstance(value, list) or len(value) != 4:
        return False
    return all(isinstance(item, (int, float)) for item in value)


def _valid_confidence(value) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return 0.0 <= float(value) <= 1.0


def _block_evidence_errors(index: int, block: Dict[str, Any]) -> list[str]:
    evidence = block.get("evidence") or {}
    origin = block.get("origin")
    errors = []
    if origin in BLOCK_VISION_ORIGINS and not isinstance(evidence.get("raw_text"), str):
        errors.append(f"block_{index}_missing_raw_text_evidence")
    if origin == "refiner_op" and not isinstance(evidence.get("refiner_op"), str):
        errors.append(f"block_{index}_missing_refiner_op_evidence")
    return errors


def _looks_like_body_text(text: str) -> bool:
    stripped = text.strip()
    return len(stripped) > 120 or bool(re.search(r"[。.!?]\s*$", stripped))


def _looks_like_heading_text(text: str) -> bool:
    stripped = text.strip()
    return 1 <= len(stripped) <= 80 and stripped.endswith(":")


def _looks_like_figure_description(text: str) -> bool:
    stripped = text.strip()
    return (
        ("图示" in stripped or "图中" in stripped or "坐标图" in stripped or "流程图" in stripped)
        and ("左侧" in stripped or "右侧" in stripped or "节点" in stripped or "箭头" in stripped or "坐标轴" in stripped)
    )


def _formula_needs_normalize(text: str) -> bool:
    stripped = text.strip()
    return (
        stripped.startswith("$$")
        or stripped.endswith("$$")
        or stripped.startswith(r"\[")
        or stripped.endswith(r"\]")
        or stripped.startswith(r"\(")
        or stripped.endswith(r"\)")
    )


def _normalize_formula_text(text: str) -> str:
    return normalize_formula_text(text)


def _has_uncertain_marker(text: str) -> bool:
    lower = text.lower()
    return (
        "[?]" in text
        or "？" in text
        or "无法确定" in text
        or "看不清" in text
        or "不确定" in text
        or "uncertain" in lower
        or "illegible" in lower
    )
