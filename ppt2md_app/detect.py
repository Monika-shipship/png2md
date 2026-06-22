from dataclasses import dataclass
from typing import Any, Iterable, Literal

from .table_quality import assess_table


Severity = Literal["error", "warning", "info"]


VALIDATION_OP_HINTS = {
    "api_error_text": "mark_failed_page",
    "vision_failed_target": "mark_failed_page",
    "empty_markdown": "mark_failed_page",
    "heading_missing_or_mismatch": "fix_heading",
    "multiple_slide_headings": "mark_uncertain",
    "ctx_marker_leak": "mark_failed_page",
    "whole_document_code_fence": "strip_fence",
    "whole_document_code_fence_raw": "strip_fence",
    "unclosed_code_fence": "mark_uncertain",
    "display_math_unbalanced": "mark_uncertain",
    "inline_math_unbalanced": "mark_uncertain",
    "formula_brace_unbalanced": "normalize_formula",
    "formula_parenthesis_unbalanced": "normalize_formula",
    "formula_bracket_unbalanced": "normalize_formula",
    "latex_left_right_unbalanced": "normalize_formula",
    "latex_frac_missing_braces": "normalize_formula",
    "formula_markup_needs_normalize": "normalize_formula",
    "formula_uncertain_marker": "mark_uncertain",
    "table_structure_warning": "mark_uncertain",
    "short_body": "inspect_ocr_coverage",
    "ocr_coverage_low": "inspect_ocr_coverage",
    "unrendered_figure_analysis": "convert_figure_note",
    "figure_note_missing": "convert_figure_note",
    "possible_neighbor_leak": "mark_uncertain",
    "chatter_residue": "strip_chatter",
    "control_chars": "strip_control_chars",
    "inline_math_suspicious": "normalize_formula",
}


QUALITY_OP_HINTS = {
    "figure_unrecognizable": "mark_uncertain",
    "formula_empty": "mark_uncertain",
    "formula_brace_unbalanced": "normalize_formula",
    "formula_parenthesis_unbalanced": "normalize_formula",
    "formula_bracket_unbalanced": "normalize_formula",
    "latex_left_right_unbalanced": "normalize_formula",
    "latex_frac_missing_braces": "normalize_formula",
    "formula_uncertain_marker": "mark_uncertain",
    "table_quality_warning": "mark_uncertain",
}


@dataclass(frozen=True)
class Suspect:
    id: str
    slide_no: int
    source: str
    code: str
    severity: Severity
    message: str
    evidence: Any = None
    block_id: str | None = None
    block_type: str | None = None
    op_hint: str | None = None
    op: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "slide_no": self.slide_no,
            "source": self.source,
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "evidence": self.evidence,
            "block_id": self.block_id,
            "block_type": self.block_type,
            "op_hint": self.op_hint,
            "op": self.op,
        }


def detect_page_suspects(
    *,
    slide_no: int,
    stage1: dict[str, Any] | None = None,
    stage2: dict[str, Any] | None = None,
    validation: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
    block_refiner: dict[str, Any] | None = None,
    blocks: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    suspects: list[Suspect] = []
    suspects.extend(_stage_suspects(slide_no, "stage1", stage1 or {}, len(suspects)))
    suspects.extend(_stage_suspects(slide_no, "stage2", stage2 or {}, len(suspects)))
    suspects.extend(_validation_suspects(slide_no, validation or {}, len(suspects)))
    block_suspects = _block_suspects(slide_no, blocks or [], len(suspects))
    suspects.extend(block_suspects)
    if not blocks:
        suspects.extend(_quality_suspects(slide_no, quality or {}, len(suspects)))
    suspects.extend(_block_refiner_suspects(slide_no, block_refiner or {}, len(suspects)))
    return [suspect.to_dict() for suspect in suspects]


def summarize_suspects(pages: Iterable[dict[str, Any]]) -> dict[str, Any]:
    by_code: dict[str, int] = {}
    by_op: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    total = 0
    actionable_total = 0
    for page in pages:
        for suspect in page.get("suspects") or []:
            total += 1
            code = str(suspect.get("code") or "unknown")
            severity = str(suspect.get("severity") or "unknown")
            by_code[code] = by_code.get(code, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
            op = suspect.get("op") if isinstance(suspect.get("op"), dict) else None
            op_name = str((op or {}).get("op") or suspect.get("op_hint") or "")
            if op_name:
                actionable_total += 1
                by_op[op_name] = by_op.get(op_name, 0) + 1
    return {
        "total": total,
        "actionable_total": actionable_total,
        "by_code": by_code,
        "by_op": by_op,
        "by_severity": by_severity,
    }


def _stage_suspects(slide_no: int, stage: str, state: dict[str, Any], offset: int) -> list[Suspect]:
    status = state.get("status")
    if status not in {"failed", "blocked"}:
        return []
    code = str(state.get("error_code") or f"{stage}_{status}")
    message = str(state.get("error_message") or status)
    return [
        Suspect(
            id=_suspect_id(slide_no, offset + 1),
            slide_no=slide_no,
            source=stage,
            code=code,
            severity="error",
            message=message,
            evidence={"status": status, "path": state.get("path")},
            op_hint="mark_failed_page",
        )
    ]


def _validation_suspects(slide_no: int, validation: dict[str, Any], offset: int) -> list[Suspect]:
    suspects = []
    issues = list(validation.get("errors") or []) + list(validation.get("warnings") or [])
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        code = str(issue.get("code") or "validation_issue")
        severity = _severity(issue.get("severity") or "warning")
        suspects.append(
            Suspect(
                id=_suspect_id(slide_no, offset + len(suspects) + 1),
                slide_no=slide_no,
                source="validation",
                code=code,
                severity=severity,
                message=str(issue.get("message") or code),
                evidence=issue.get("evidence"),
                op_hint=VALIDATION_OP_HINTS.get(code),
            )
        )
    return suspects


def _quality_suspects(slide_no: int, quality: dict[str, Any], offset: int) -> list[Suspect]:
    suspects = []
    for warning in quality.get("warnings") or []:
        if not isinstance(warning, dict):
            continue
        code = str(warning.get("code") or "quality_warning")
        suspects.append(
            Suspect(
                id=_suspect_id(slide_no, offset + len(suspects) + 1),
                slide_no=slide_no,
                source="block_quality",
                code=code,
                severity="warning",
                message=str(warning.get("message") or code),
                evidence=_quality_evidence(warning),
                op_hint=QUALITY_OP_HINTS.get(code),
            )
        )
    return suspects


def _block_suspects(slide_no: int, blocks: list[dict[str, Any]], offset: int) -> list[Suspect]:
    suspects = []
    for block in blocks:
        block_id = block.get("id")
        block_type = block.get("type")
        if not block_id or not block_type:
            continue
        if block_type in {"formula_inline", "formula_block"}:
            suspects.extend(_formula_block_suspects(slide_no, block, offset + len(suspects)))
        elif block_type == "table":
            suspect = _table_block_suspect(slide_no, block, offset + len(suspects) + 1)
            if suspect:
                suspects.append(suspect)
        elif block_type == "figure_note" and block.get("unrecognizable"):
            suspects.append(
                Suspect(
                    id=_suspect_id(slide_no, offset + len(suspects) + 1),
                    slide_no=slide_no,
                    source="block",
                    code="figure_unrecognizable",
                    severity="warning",
                    message="图示 block 标记为不可可靠识别。",
                    evidence={"figure_type": block.get("figure_type")},
                    block_id=str(block_id),
                    block_type=str(block_type),
                    op_hint="mark_uncertain",
                    op={"op": "mark_uncertain", "id": block_id},
                )
            )
    return suspects


def _formula_block_suspects(slide_no: int, block: dict[str, Any], offset: int) -> list[Suspect]:
    quality = block.get("formula_quality") if isinstance(block.get("formula_quality"), dict) else {}
    warnings = quality.get("warnings") or []
    suspects = []
    for warning in warnings:
        if not isinstance(warning, dict):
            continue
        code = str(warning.get("code") or "formula_quality_warning")
        block_id = str(block.get("id"))
        suspects.append(
            Suspect(
                id=_suspect_id(slide_no, offset + len(suspects) + 1),
                slide_no=slide_no,
                source="block",
                code=code,
                severity="warning",
                message=str(warning.get("message") or code),
                evidence={"latex": quality.get("latex"), "warning": warning.get("evidence")},
                block_id=block_id,
                block_type=str(block.get("type") or "formula_block"),
                op_hint="mark_uncertain",
                op={"op": "mark_uncertain", "id": block_id},
            )
        )
    return suspects


def _table_block_suspect(slide_no: int, block: dict[str, Any], index: int) -> Suspect | None:
    quality = assess_table(block.get("text") or "")
    if quality.reliable:
        return None
    block_id = str(block.get("id"))
    return Suspect(
        id=_suspect_id(slide_no, index),
        slide_no=slide_no,
        source="block",
        code="table_quality_warning",
        severity="warning",
        message="表格结构不可靠。",
        evidence=quality.to_dict(),
        block_id=block_id,
        block_type=str(block.get("type") or "table"),
        op_hint="mark_uncertain",
        op={"op": "mark_uncertain", "id": block_id},
    )


def _block_refiner_suspects(slide_no: int, block_refiner: dict[str, Any], offset: int) -> list[Suspect]:
    suspects = []
    for item in block_refiner.get("dismissed") or []:
        if not isinstance(item, dict):
            continue
        code = str(item.get("code") or "block_refiner_dismissed")
        op = item.get("op") if isinstance(item.get("op"), dict) else {}
        suspects.append(
            Suspect(
                id=_suspect_id(slide_no, offset + len(suspects) + 1),
                slide_no=slide_no,
                source="block_refiner",
                code=code,
                severity="info",
                message=str(item.get("reason") or code),
                evidence=item.get("dismissed"),
                block_id=op.get("id") or op.get("a"),
                op_hint=op.get("op"),
                op=op or None,
            )
        )
    return suspects


def _quality_evidence(warning: dict[str, Any]) -> Any:
    if "details" in warning:
        return warning.get("details")
    if "latex" in warning:
        return {"latex": warning.get("latex")}
    return None


def _severity(value: str) -> Severity:
    if value == "error":
        return "error"
    if value == "info":
        return "info"
    return "warning"


def _suspect_id(slide_no: int, index: int) -> str:
    return f"p{slide_no:04d}-sus{index:03d}"
