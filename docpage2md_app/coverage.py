import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Iterable

from .formula_quality import normalize_text_for_math_coverage


OCR_COVERAGE_SCHEMA_VERSION = 1
OCR_COVERAGE_MIN_RATIO = 0.62
OCR_COVERAGE_MIN_CHARS = 16
OCR_BLOCK_ORIGINS = {"vision_ocr", "refiner_op"}
OCR_BLOCK_TYPES = {"heading", "paragraph", "list", "formula_inline"}


@dataclass(frozen=True)
class CoverageResult:
    checked: bool
    ratio: float | None
    source_chars: int
    matched_chars: int
    missing_snippets: list[str]
    reason: str | None = None

    @property
    def warning(self) -> bool:
        return self.checked and self.ratio is not None and self.ratio < OCR_COVERAGE_MIN_RATIO

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": OCR_COVERAGE_SCHEMA_VERSION,
            "checked": self.checked,
            "ratio": self.ratio,
            "source_chars": self.source_chars,
            "matched_chars": self.matched_chars,
            "missing_snippets": self.missing_snippets,
            "warning": self.warning,
            "reason": self.reason,
        }


def assess_ocr_coverage(markdown: str, blocks: Iterable[dict[str, Any]] | None) -> CoverageResult:
    source_segments = _ocr_text_segments(blocks)
    if not source_segments:
        return CoverageResult(False, None, 0, 0, [], "no_ocr_segments")

    markdown_norm = _normalize_text(_markdown_content_for_coverage(markdown))
    source_norm = "".join(_normalize_text(segment) for segment in source_segments)
    source_chars = len(source_norm)
    if source_chars < OCR_COVERAGE_MIN_CHARS:
        return CoverageResult(False, None, source_chars, 0, [], "source_too_short")

    matched_chars = _matched_char_count(source_norm, markdown_norm)
    ratio = round(matched_chars / source_chars, 4) if source_chars else None
    missing = _missing_snippets(markdown_norm, source_segments)
    return CoverageResult(True, ratio, source_chars, matched_chars, missing)


def _ocr_text_segments(blocks: Iterable[dict[str, Any]] | None) -> list[str]:
    segments = []
    for block in blocks or []:
        block_type = block.get("type")
        origin = block.get("origin")
        if block_type not in OCR_BLOCK_TYPES:
            continue
        if origin not in OCR_BLOCK_ORIGINS:
            continue
        text = (block.get("text") or "").strip()
        if text:
            segments.extend(_line_segments(text))
    return segments


def _line_segments(text: str) -> list[str]:
    segments = []
    for line in text.splitlines():
        stripped = _strip_markdown_prefix(line)
        if len(_normalize_text(stripped)) >= 8:
            segments.append(stripped)
    if segments:
        return segments
    stripped = _strip_markdown_prefix(text)
    return [stripped] if len(_normalize_text(stripped)) >= 8 else []


def _matched_char_count(source_norm: str, markdown_norm: str) -> int:
    matcher = SequenceMatcher(None, source_norm, markdown_norm, autojunk=False)
    return sum(block.size for block in matcher.get_matching_blocks())


def _missing_snippets(markdown_norm: str, source_segments: list[str]) -> list[str]:
    snippets = []
    for segment in source_segments:
        normalized = _normalize_text(segment)
        if not normalized or normalized in markdown_norm:
            continue
        snippets.append(segment.strip()[:120])
        if len(snippets) >= 5:
            break
    return snippets


def _strip_markdown_prefix(text: str) -> str:
    stripped = (text or "").strip()
    stripped = re.sub(r"^#{1,6}\s+", "", stripped)
    stripped = re.sub(r"^[-*+]\s+", "", stripped)
    stripped = re.sub(r"^\d+[.)]\s+", "", stripped)
    return stripped.strip()


def _markdown_content_for_coverage(markdown: str) -> str:
    text = re.sub(r"<!--.*?-->", "\n", markdown or "", flags=re.DOTALL)
    kept = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if re.match(r"^#\s*Slide\s+\d+\b", stripped, flags=re.IGNORECASE):
            continue
        if re.match(r"^!\[[^\]]*\]\([^)]+\)\s*$", stripped):
            continue
        if stripped.startswith(">"):
            stripped = stripped.lstrip("> ").strip()
        if re.match(r"^\[!(NOTE|WARNING|TIP|IMPORTANT|CAUTION)\]", stripped, flags=re.IGNORECASE):
            continue
        if stripped in {"原始识别：", "原始识别:", "图示说明", "Figure 描述"}:
            continue
        kept.append(stripped)
    return "\n".join(kept)


def _normalize_text(text: str) -> str:
    normalized = normalize_text_for_math_coverage(text or "").lower()
    return re.sub(r"[^\w]+", "", normalized, flags=re.UNICODE).replace("_", "")
