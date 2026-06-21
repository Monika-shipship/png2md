import hashlib
import re
from typing import Any, Dict, List

from .renderer import (
    render_blocks_to_markdown,
    render_page_ir_to_markdown,
    render_page_record_to_markdown,
)

PAGE_IR_SCHEMA_VERSION = 2


def build_page_ir(raw_text: str, slide_no: int) -> Dict[str, Any]:
    """Build a weakly structured, deterministic IR from Stage 1 raw text."""
    blocks = raw_text_to_blocks(raw_text, slide_no)
    return {
        "schema_version": PAGE_IR_SCHEMA_VERSION,
        "source_page": slide_no,
        "raw_text_sha256": _sha256_text(raw_text or ""),
        "blocks": blocks,
    }


def raw_text_to_blocks(raw_text: str, slide_no: int) -> List[Dict[str, Any]]:
    text = (raw_text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not text:
        return []

    paragraphs = _split_paragraphs(text)
    blocks = []
    for paragraph in paragraphs:
        block_type = _section_block_type(paragraph) or _infer_block_type(_strip_section_heading(paragraph))
        block_text = _strip_section_heading(paragraph)
        if not block_text:
            continue
        blocks.append(
            {
                "id": f"p{slide_no:04d}-b{len(blocks) + 1:03d}",
                "type": block_type,
                "text": block_text,
                "source_page": slide_no,
                "confidence": _confidence_for_type(block_type),
                "origin": _origin_for_type(block_type),
                "evidence": {"raw_text": paragraph},
                "bbox": None,
            }
        )
    return blocks


def _split_paragraphs(text: str) -> List[str]:
    paragraphs = []
    current = []
    in_section = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if current:
                paragraphs.append("\n".join(current).strip())
                current = []
            in_section = False
            continue

        if _is_section_heading(stripped):
            if current:
                paragraphs.append("\n".join(current).strip())
                current = []
            current.append(stripped)
            in_section = True
            continue

        if in_section:
            current.append(stripped)
            continue

        if _is_list_line(stripped):
            if current and not all(_is_list_line(item.strip()) for item in current):
                paragraphs.append("\n".join(current).strip())
                current = []
            current.append(stripped)
            continue

        if current and all(_is_list_line(item.strip()) for item in current):
            paragraphs.append("\n".join(current).strip())
            current = []
        current.append(stripped)

    if current:
        paragraphs.append("\n".join(current).strip())
    return paragraphs


def _infer_block_type(text: str) -> str:
    stripped = text.strip()
    lower = stripped.lower()
    if re.match(r"^#{1,6}\s+", stripped) or (len(stripped) <= 80 and stripped.endswith(":")):
        return "heading"
    if all(_is_list_line(line.strip()) for line in stripped.splitlines() if line.strip()):
        return "list"
    if re.search(r"\\\(|\\\[|[$][^$]+[$]", stripped):
        return "formula_inline"
    if _looks_like_formula_block(stripped):
        return "formula_block"
    if "|" in stripped and "\n" in stripped:
        return "table"
    return "paragraph"


def _confidence_for_type(block_type: str) -> float:
    if block_type in {"figure_note", "list"}:
        return 0.72
    if block_type in {"heading", "formula_inline", "formula_block", "table"}:
        return 0.62
    if block_type == "uncertain":
        return 0.25
    return 0.55


def _origin_for_type(block_type: str) -> str:
    if block_type in {"formula_inline", "formula_block"}:
        return "vision_formula"
    if block_type == "figure_note":
        return "vision_description"
    if block_type == "uncertain":
        return "vision_uncertain"
    if block_type == "table":
        return "vision_table"
    return "vision_ocr"


def _is_list_line(line: str) -> bool:
    return bool(re.match(r"^([-*+]\s+|\d+[.)]\s+)", line))


def _is_section_heading(line: str) -> bool:
    lower = line.lower()
    return (
        lower.startswith("### ocr text")
        or lower.startswith("### ocr")
        or lower.startswith("### 正文")
        or lower.startswith("### figure analysis")
        or lower.startswith("### formula")
        or lower.startswith("### table analysis")
        or lower.startswith("### uncertain")
        or lower.startswith("### illegible")
        or lower.startswith("### 公式")
        or lower.startswith("### 表格")
        or lower.startswith("### 不确定")
    )


def _section_block_type(text: str) -> str | None:
    first = (text.strip().splitlines() or [""])[0].strip().lower()
    if first.startswith("### figure analysis"):
        return "figure_note"
    if first.startswith("### formula") or first.startswith("### 公式"):
        return "formula_block"
    if first.startswith("### table analysis") or first.startswith("### 表格"):
        return "table"
    if first.startswith("### uncertain") or first.startswith("### illegible") or first.startswith("### 不确定"):
        return "uncertain"
    return None


def _strip_section_heading(text: str) -> str:
    lines = text.strip().splitlines()
    if lines and _is_section_heading(lines[0].strip()):
        lines = lines[1:]
    return "\n".join(line.strip() for line in lines).strip()


def _looks_like_formula_block(text: str) -> bool:
    stripped = text.strip()
    if "$$" in stripped:
        return True
    if re.search(r"[\u4e00-\u9fff]", stripped):
        return False
    if len(stripped.splitlines()) <= 3 and re.search(r"(\\frac|\\sum|\\int|\\lim|\\begin\{|=|≈|≤|≥)", stripped):
        math_chars = sum(1 for ch in stripped if ch in "=+-*/^_{}\\")
        return math_chars >= 2
    return False


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
