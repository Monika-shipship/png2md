import hashlib
from typing import Any, Dict, Iterable


PROVENANCE_SCHEMA_VERSION = 1


def build_page_provenance(page_ir: Dict[str, Any]) -> Dict[str, Any]:
    blocks = page_ir.get("blocks") or []
    entries = [_block_entry(block, index) for index, block in enumerate(blocks, start=1)]
    return {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "source_page": page_ir.get("source_page"),
        "entries": entries,
        "summary": summarize_provenance(entries),
    }


def summarize_provenance(entries: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    origin_counts: Dict[str, int] = {}
    type_counts: Dict[str, int] = {}
    generated_description_count = 0
    refiner_op_count = 0
    renderer_template_count = 1
    for entry in entries:
        origin = entry.get("origin") or "unknown"
        block_type = entry.get("type") or "unknown"
        origin_counts[origin] = origin_counts.get(origin, 0) + 1
        type_counts[block_type] = type_counts.get(block_type, 0) + 1
        if origin == "vision_description":
            generated_description_count += 1
        if origin == "refiner_op":
            refiner_op_count += 1
    return {
        "origin_counts": origin_counts,
        "type_counts": type_counts,
        "generated_description_count": generated_description_count,
        "refiner_op_count": refiner_op_count,
        "renderer_template_count": renderer_template_count,
    }


def merge_provenance_summaries(pages: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    origin_counts: Dict[str, int] = {}
    type_counts: Dict[str, int] = {}
    generated_description_count = 0
    refiner_op_count = 0
    renderer_template_count = 0
    for page in pages:
        summary = page.get("provenance", {}).get("summary") or {}
        _add_counts(origin_counts, summary.get("origin_counts") or {})
        _add_counts(type_counts, summary.get("type_counts") or {})
        generated_description_count += int(summary.get("generated_description_count") or 0)
        refiner_op_count += int(summary.get("refiner_op_count") or 0)
        renderer_template_count += int(summary.get("renderer_template_count") or 0)
    return {
        "origin_counts": origin_counts,
        "type_counts": type_counts,
        "generated_description_count": generated_description_count,
        "refiner_op_count": refiner_op_count,
        "renderer_template_count": renderer_template_count,
    }


def provenance_comment(block: Dict[str, Any]) -> str:
    block_id = str(block.get("id") or "")
    block_type = str(block.get("type") or "unknown")
    origin = str(block.get("origin") or "unknown")
    source_page = block.get("source_page")
    confidence = block.get("confidence")
    parts = [
        "png2md-provenance",
        f"id={_escape_comment_value(block_id)}",
        f"type={_escape_comment_value(block_type)}",
        f"origin={_escape_comment_value(origin)}",
    ]
    if source_page is not None:
        parts.append(f"source_page={source_page}")
    if confidence is not None:
        parts.append(f"confidence={confidence}")
    return "<!-- " + " ".join(parts) + " -->"


def _block_entry(block: Dict[str, Any], index: int) -> Dict[str, Any]:
    evidence = block.get("evidence") if isinstance(block.get("evidence"), dict) else {}
    raw_text = evidence.get("raw_text") or ""
    entry = {
        "index": index,
        "id": block.get("id"),
        "type": block.get("type"),
        "origin": block.get("origin") or "unknown",
        "source_page": block.get("source_page"),
        "confidence": block.get("confidence"),
        "bbox": block.get("bbox"),
        "raw_text_sha256": evidence.get("raw_text_sha256") or _sha256_text(raw_text) if raw_text else None,
        "has_raw_text": bool(raw_text),
        "refiner_op": evidence.get("refiner_op"),
    }
    if block.get("type") == "figure_note":
        entry["generated_description"] = True
        entry["figure_type"] = block.get("figure_type")
    elif block.get("type") == "formula_block":
        entry["formula_origin"] = block.get("origin")
    elif block.get("type") == "table":
        entry["table_origin"] = block.get("origin")
    return entry


def _add_counts(target: Dict[str, int], source: Dict[str, int]):
    for key, value in source.items():
        target[key] = target.get(key, 0) + int(value or 0)


def _escape_comment_value(value: str) -> str:
    return value.replace("--", "- -").replace('"', "'")


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
