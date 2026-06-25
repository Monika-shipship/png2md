import hashlib
import re
from typing import Any, Dict, Iterable

from .formula_quality import normalize_text_for_math_coverage


CONTENT_INVENTORY_SCHEMA_VERSION = 1


VISUAL_EVIDENCE_BLOCK_TYPES = {"figure_note", "image_ref", "table", "formula_block"}


def build_content_inventory(
    page_ir: Dict[str, Any],
    markdown: str,
    *,
    op_audit: Iterable[Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    blocks = page_ir.get("blocks") or []
    audits = list(op_audit or [])
    audit_by_block = _audit_by_block_id(audits)
    entries = []
    for block in blocks:
        block_id = str(block.get("id") or "")
        block_type = str(block.get("type") or "unknown")
        audit_entries = audit_by_block.get(block_id, [])
        action = _inventory_action(block, markdown, audit_entries)
        evidence_refs = _evidence_refs(block)
        entries.append(
            {
                "block_id": block_id,
                "type": block_type,
                "source_engine": block.get("source_engine") or block.get("origin") or "unknown",
                "status": action,
                "rendered": action in {"rendered", "degraded", "merged", "replaced"},
                "degraded": action == "degraded" or _is_degraded_block(block),
                "has_visual_evidence": bool(evidence_refs),
                "requires_visual_evidence": block_type in VISUAL_EVIDENCE_BLOCK_TYPES,
                "evidence_refs": evidence_refs,
                "text_sha256": _block_text_sha256(block),
                "audit_ops": [entry.get("op") for entry in audit_entries if entry.get("op")],
            }
        )
    return {
        "schema_version": CONTENT_INVENTORY_SCHEMA_VERSION,
        "source_block_count": len(blocks),
        "entries": entries,
        "summary": summarize_content_inventory(entries),
    }


def summarize_content_inventory(entries: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    entries = list(entries)
    status_counts: Dict[str, int] = {}
    type_counts: Dict[str, int] = {}
    rendered_count = 0
    degraded_count = 0
    missing_visual_evidence_count = 0
    for entry in entries:
        status = str(entry.get("status") or "unknown")
        block_type = str(entry.get("type") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        type_counts[block_type] = type_counts.get(block_type, 0) + 1
        if entry.get("rendered"):
            rendered_count += 1
        if entry.get("degraded"):
            degraded_count += 1
        if entry.get("requires_visual_evidence") and not entry.get("has_visual_evidence"):
            missing_visual_evidence_count += 1
    return {
        "source_block_count": len(entries),
        "rendered_count": rendered_count,
        "unrendered_count": len(entries) - rendered_count,
        "accounted_count": len(entries) - status_counts.get("unrendered", 0),
        "unaccounted_count": status_counts.get("unrendered", 0),
        "degraded_count": degraded_count,
        "missing_visual_evidence_count": missing_visual_evidence_count,
        "status_counts": status_counts,
        "type_counts": type_counts,
    }


def merge_content_inventory_summaries(pages: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    total = {
        "source_block_count": 0,
        "rendered_count": 0,
        "unrendered_count": 0,
        "accounted_count": 0,
        "unaccounted_count": 0,
        "degraded_count": 0,
        "missing_visual_evidence_count": 0,
        "status_counts": {},
        "type_counts": {},
    }
    for page in pages:
        summary = (page.get("content_inventory") or {}).get("summary") or {}
        for key in (
            "source_block_count",
            "rendered_count",
            "unrendered_count",
            "accounted_count",
            "unaccounted_count",
            "degraded_count",
            "missing_visual_evidence_count",
        ):
            total[key] += int(summary.get(key) or 0)
        _add_counts(total["status_counts"], summary.get("status_counts") or {})
        _add_counts(total["type_counts"], summary.get("type_counts") or {})
    return total


def _inventory_action(block: Dict[str, Any], markdown: str, audits: list[Dict[str, Any]]) -> str:
    if _audit_has_op(audits, {"drop_block", "drop_page_number"}):
        return "dropped"
    if _audit_has_op(audits, {"merge_blocks"}):
        return "merged"
    if _audit_has_op(audits, {"replace_text_span_checked", "normalize_formula_tag", "normalize_formula", "fix_ocr_confusion"}):
        return "replaced"
    if _is_degraded_block(block) or _audit_has_op(audits, {"mark_uncertain", "degrade_table_to_image"}):
        return "degraded" if _block_has_markdown_evidence(block, markdown) else "failed_open"
    if _block_has_markdown_evidence(block, markdown):
        return "rendered"
    return "unrendered"


def _block_has_markdown_evidence(block: Dict[str, Any], markdown: str) -> bool:
    for ref in _evidence_refs(block):
        if ref and ref in markdown:
            return True
    text = _block_text(block)
    if not text:
        return False
    candidates = _text_candidates(text)
    if any(candidate and candidate in markdown for candidate in candidates):
        return True
    normalized_markdown = _normalize_text(markdown)
    return any(candidate and candidate in normalized_markdown for candidate in candidates)


def _text_candidates(text: str) -> list[str]:
    normalized = _normalize_text(text)
    if not normalized:
        return []
    if len(normalized) <= 32:
        return [normalized]
    return [normalized[:32], normalized[-32:]]


def _normalize_text(text: str) -> str:
    text = re.sub(r"^#+\s*", "", text.strip())
    text = text.strip("` \n\r\t")
    text = normalize_text_for_math_coverage(text)
    return re.sub(r"[^\w]+", "", text.lower(), flags=re.UNICODE).replace("_", "")


def _block_text(block: Dict[str, Any]) -> str:
    for key in ("latex", "text", "description", "raw_text"):
        value = str(block.get(key) or "").strip()
        if value:
            return value
    evidence = block.get("evidence") if isinstance(block.get("evidence"), dict) else {}
    return str(evidence.get("raw_text") or "").strip()


def _block_text_sha256(block: Dict[str, Any]) -> str | None:
    text = _block_text(block)
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _evidence_refs(block: Dict[str, Any]) -> list[str]:
    refs = []
    for key in (
        "crop_ref",
        "image_ref",
        "image_path",
        "path",
        "table_image_path",
        "formula_image_path",
        "page_image_ref",
    ):
        value = str(block.get(key) or "").strip()
        if value and value not in refs:
            refs.append(value)
    return refs


def _is_degraded_block(block: Dict[str, Any]) -> bool:
    if block.get("type") == "uncertain":
        return True
    if block.get("table_render_mode") == "degraded_warning":
        return True
    if block.get("table_format") in {"image_only", "uncertain"}:
        return True
    if block.get("unrecognizable"):
        return True
    return False


def _audit_by_block_id(audits: list[Dict[str, Any]]) -> dict[str, list[Dict[str, Any]]]:
    grouped: dict[str, list[Dict[str, Any]]] = {}
    for audit in audits:
        block_ids = []
        for key in ("target_block_ids", "created_block_ids"):
            value = audit.get(key)
            if isinstance(value, list):
                block_ids.extend(str(item) for item in value if item)
        for span in audit.get("removed_spans") or []:
            if isinstance(span, dict) and span.get("block_id"):
                block_ids.append(str(span["block_id"]))
        for block_id in set(block_ids):
            grouped.setdefault(block_id, []).append(audit)
    return grouped


def _audit_has_op(audits: list[Dict[str, Any]], ops: set[str]) -> bool:
    return any(
        str(audit.get("op") or "") in ops and _audit_counts_as_effect(audit)
        for audit in audits
    )


def _audit_counts_as_effect(audit: Dict[str, Any]) -> bool:
    status = str(audit.get("status") or "").strip().lower()
    return status in {"", "applied"}


def _add_counts(target: Dict[str, int], source: Dict[str, Any]):
    for key, value in source.items():
        target[str(key)] = target.get(str(key), 0) + int(value or 0)
