from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .formula_quality import assess_formula_text, normalize_inline_math_text
from .ir import PAGE_IR_SCHEMA_VERSION
from .paddleocr_artifacts import PaddleOCRArtifacts, discover_paddleocr_artifacts, load_artifact_json, resolve_artifact_image
from .table_quality import assess_table


DOCUMENT_IR_SCHEMA_VERSION = "docpage2md-docir-v1"
PADDLEOCR_ADAPTER_VERSION = "paddleocr-adapter-2026-06-25-v1"


def load_paddleocr_document_ir(
    artifact_root: str | Path,
    *,
    source_path: str | None = None,
    engine_mode: str = "paddleocr_only",
) -> dict[str, Any]:
    artifacts = discover_paddleocr_artifacts(artifact_root)
    return adapt_paddleocr_artifacts(artifacts, source_path=source_path, engine_mode=engine_mode)


def adapt_paddleocr_artifacts(
    artifacts: PaddleOCRArtifacts,
    *,
    source_path: str | None = None,
    engine_mode: str = "paddleocr_only",
) -> dict[str, Any]:
    page_results = _load_layout_results(artifacts)
    if not page_results:
        raise ValueError(f"PaddleOCR artifact has no layout results: {artifacts.root}")

    image_manifest = _load_image_manifest(artifacts)
    pages: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    for page_index, page_result in enumerate(page_results, start=1):
        blocks = _adapt_page_blocks(page_result, artifacts=artifacts, image_manifest=image_manifest, page_no=page_index)
        if not blocks:
            text = _markdown_text(page_result)
            if text:
                blocks = [_paragraph_block(text, page_index, 1, page_result)]
        raw_text = _blocks_to_raw_text(blocks) or _markdown_text(page_result)
        page_assets = [_block_asset(block) for block in blocks]
        assets.extend(asset for asset in page_assets if asset)
        page_image_ref = _page_image_ref(page_result, artifacts, image_manifest)
        if page_image_ref:
            assets.append(
                {
                    "asset_id": f"p{page_index:04d}-page-image",
                    "page_no": page_index,
                    "block_id": None,
                    "block_type": "page_image",
                    "artifact_ref": page_image_ref,
                    "source_path": str(resolve_artifact_image(artifacts, page_image_ref) or ""),
                }
            )
        pages.append(
            {
                "schema_version": PAGE_IR_SCHEMA_VERSION,
                "source_page": page_index,
                "page_image_ref": page_image_ref,
                "raw_text": raw_text,
                "raw_text_sha256": _sha256_text(raw_text),
                "blocks": blocks,
                "paddleocr": {
                    "page_idx": page_index - 1,
                    "model_settings": (page_result.get("prunedResult") or {}).get("model_settings"),
                    "artifact_refs": artifacts.to_manifest(),
                },
            }
        )

    input_path = source_path or _guess_source_path(artifacts)
    return {
        "schema_version": DOCUMENT_IR_SCHEMA_VERSION,
        "adapter_version": PADDLEOCR_ADAPTER_VERSION,
        "source": {
            "input_path": input_path,
            "input_hash": _file_sha256(input_path) if input_path and Path(input_path).is_file() else None,
            "input_type": _input_type(input_path),
            "artifact_root": str(artifacts.root),
        },
        "engine_mode": engine_mode,
        "pages": pages,
        "assets": assets,
        "metadata": {
            "artifact_manifest": artifacts.to_manifest(),
            "page_count": len(pages),
        },
    }


def iter_artifact_image_refs(document_ir: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    seen: set[str] = set()
    for asset in document_ir.get("assets") or []:
        artifact_ref = str(asset.get("artifact_ref") or "").strip()
        source_path = str(asset.get("source_path") or "").strip()
        if not artifact_ref or not source_path or artifact_ref in seen:
            continue
        seen.add(artifact_ref)
        refs.append(
            {
                "artifact_ref": artifact_ref,
                "source_path": source_path,
                "block_id": str(asset.get("block_id") or ""),
                "page_no": str(asset.get("page_no") or ""),
                "block_type": str(asset.get("block_type") or ""),
            }
        )
    return refs


def rewrite_asset_refs(document_ir: dict[str, Any], ref_map: dict[str, str]) -> dict[str, Any]:
    for page in document_ir.get("pages") or []:
        page_ref = str(page.get("page_image_ref") or "").strip()
        if page_ref in ref_map:
            page["page_image_ref"] = ref_map[page_ref]
        for block in page.get("blocks") or []:
            for key in ("crop_ref", "image_ref", "image_path", "path", "table_image_path", "formula_image_path"):
                value = str(block.get(key) or "").strip()
                if value and value in ref_map:
                    block[key] = ref_map[value]
            evidence = block.get("evidence")
            if isinstance(evidence, dict):
                value = str(evidence.get("artifact_image_ref") or "").strip()
                if value and value in ref_map:
                    evidence["output_image_ref"] = ref_map[value]
    for asset in document_ir.get("assets") or []:
        value = str(asset.get("artifact_ref") or "").strip()
        if value and value in ref_map:
            asset["output_ref"] = ref_map[value]
    return document_ir


def _load_layout_results(artifacts: PaddleOCRArtifacts) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if artifacts.result_jsonl and artifacts.result_jsonl.exists():
        for line in artifacts.result_jsonl.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            results.extend(_extract_layout_results(payload))
    data = load_artifact_json(artifacts.result_json)
    results.extend(_extract_layout_results(data))
    if results:
        return results
    md = artifacts.result_md.read_text(encoding="utf-8") if artifacts.result_md and artifacts.result_md.exists() else ""
    if md.strip():
        return [{"markdown": {"text": md.strip(), "images": {}}}]
    return []


def _extract_layout_results(payload: Any) -> list[dict[str, Any]]:
    if payload in (None, "", [], {}):
        return []
    if isinstance(payload, list):
        extracted: list[dict[str, Any]] = []
        for item in payload:
            extracted.extend(_extract_layout_results(item))
        return extracted
    if not isinstance(payload, dict):
        return []
    if isinstance(payload.get("layoutParsingResults"), list):
        return [item for item in payload["layoutParsingResults"] if isinstance(item, dict)]
    if isinstance(payload.get("result"), dict):
        return _extract_layout_results(payload["result"])
    if isinstance(payload.get("data"), dict):
        return _extract_layout_results(payload["data"])
    if "prunedResult" in payload or "markdown" in payload or "ocrResults" in payload:
        return [payload]
    return []


def _adapt_page_blocks(
    page_result: dict[str, Any],
    *,
    artifacts: PaddleOCRArtifacts,
    image_manifest: dict[str, str],
    page_no: int,
) -> list[dict[str, Any]]:
    pruned = page_result.get("prunedResult") if isinstance(page_result.get("prunedResult"), dict) else {}
    items = pruned.get("parsing_res_list") or pruned.get("parsingResList") or []
    blocks: list[dict[str, Any]] = []
    if isinstance(items, list):
        for item in items:
            if not isinstance(item, dict):
                continue
            block = _adapt_layout_item(
                item,
                artifacts=artifacts,
                image_manifest=image_manifest,
                page_no=page_no,
                block_no=len(blocks) + 1,
            )
            if block:
                blocks.append(block)
    if blocks:
        return blocks

    ocr_results = page_result.get("ocrResults")
    if isinstance(ocr_results, list):
        lines = []
        for item in ocr_results:
            if isinstance(item, dict):
                text = str(item.get("text") or item.get("recText") or item.get("content") or "").strip()
                if text:
                    lines.append(text)
        if lines:
            return [_paragraph_block("\n".join(lines), page_no, 1, page_result, source_label="ocrResults")]
    return []


def _adapt_layout_item(
    item: dict[str, Any],
    *,
    artifacts: PaddleOCRArtifacts,
    image_manifest: dict[str, str],
    page_no: int,
    block_no: int,
) -> dict[str, Any] | None:
    label = str(item.get("block_label") or item.get("label") or item.get("type") or "").strip()
    raw_text = str(item.get("block_content") or item.get("text") or item.get("content") or "").strip()
    text = normalize_inline_math_text(_strip_html_image(raw_text)).strip()
    image_ref = _first_image_ref(raw_text)
    if image_ref:
        image_ref = image_manifest.get(image_ref, image_ref)
    resolved_image = resolve_artifact_image(artifacts, image_ref)
    block_type = _block_type(label, text, image_ref)
    if block_type is None:
        return None
    if not text and not image_ref and block_type not in {"image_ref", "figure_note"}:
        return None
    confidence = _confidence(item, block_type)
    block = {
        "id": f"p{page_no:04d}-b{block_no:03d}",
        "type": block_type,
        "text": text,
        "source_page": page_no,
        "confidence": confidence,
        "confidence_label": _confidence_label(confidence),
        "origin": "paddleocr",
        "evidence": {
            "raw_text": raw_text or image_ref or label,
            "provider": "paddleocr",
            "paddleocr_label": label,
            "paddleocr_block_id": item.get("block_id"),
            "artifact_image_ref": image_ref,
            "artifact_image_path": str(resolved_image) if resolved_image else None,
        },
        "bbox": item.get("block_bbox") or item.get("bbox"),
        "polygon": item.get("block_polygon_points") or item.get("polygon_points"),
        "source_engine": "paddleocr",
    }
    if image_ref:
        block["image_ref"] = image_ref
        block["path"] = image_ref
    if block_type == "formula_block":
        quality = assess_formula_text(text)
        block["text"] = quality.latex
        block["latex"] = quality.latex
        block["formula_quality"] = quality.to_dict()
    elif block_type == "table":
        quality = assess_table(text)
        block["table_quality"] = quality.to_dict()
    elif block_type in {"figure_note", "image_ref"}:
        block["description"] = text
        block["figure"] = {"vision_summary": text} if text else {}
    return block


def _paragraph_block(text: str, page_no: int, block_no: int, page_result: dict[str, Any], *, source_label: str = "markdown") -> dict[str, Any]:
    text = normalize_inline_math_text(text).strip()
    return {
        "id": f"p{page_no:04d}-b{block_no:03d}",
        "type": "paragraph",
        "text": text,
        "source_page": page_no,
        "confidence": 0.62,
        "confidence_label": "medium",
        "origin": "paddleocr",
        "evidence": {
            "raw_text": text,
            "provider": "paddleocr",
            "paddleocr_label": source_label,
        },
        "source_engine": "paddleocr",
    }


def _block_type(label: str, text: str, image_ref: str | None) -> str | None:
    normalized = label.strip().lower()
    if normalized in {"number", "footnote", "header", "header_image", "footer", "footer_image", "aside_text"}:
        return None
    if normalized in {"title", "heading"}:
        return "heading"
    if normalized in {"formula", "display_formula", "equation", "interline_equation"}:
        return "formula_block"
    if normalized in {"inline_formula"}:
        return "formula_inline"
    if normalized in {"table", "table_body"}:
        return "table"
    if normalized in {"image", "figure", "chart"}:
        return "figure_note" if text else "image_ref"
    if image_ref and not text:
        return "image_ref"
    return "paragraph"


def _confidence(item: dict[str, Any], block_type: str) -> float:
    raw_score = item.get("score")
    if raw_score is None:
        raw_score = item.get("confidence")
    try:
        score = float(raw_score)
    except (TypeError, ValueError):
        return 0.62 if block_type != "image_ref" else 0.35
    if score > 1.0 and score <= 100.0:
        score = score / 100.0
    return max(0.0, min(1.0, score))


def _confidence_label(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    return "low"


def _markdown_text(page_result: dict[str, Any]) -> str:
    markdown = page_result.get("markdown")
    if isinstance(markdown, dict):
        return str(markdown.get("text") or "").strip()
    return ""


def _load_image_manifest(artifacts: PaddleOCRArtifacts) -> dict[str, str]:
    data = load_artifact_json(artifacts.image_manifest_json)
    if not isinstance(data, dict):
        return {}
    return {str(key): str(value) for key, value in data.items() if isinstance(value, str)}


def _first_image_ref(text: str) -> str | None:
    match = re.search(r'<img\s+[^>]*src=["\']([^"\']+)["\']', text or "", flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    match = re.search(r'!\[[^\]]*]\(([^)]+)\)', text or "")
    if match:
        return match.group(1).strip()
    return None


def _strip_html_image(text: str) -> str:
    text = re.sub(r"<div[^>]*>\s*</div>", "", text or "", flags=re.IGNORECASE)
    text = re.sub(r"<div[^>]*>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</div>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"<img\b[^>]*>", "", text, flags=re.IGNORECASE)
    return text.strip()


def _page_image_ref(page_result: dict[str, Any], artifacts: PaddleOCRArtifacts, image_manifest: dict[str, str]) -> str | None:
    raw = page_result.get("inputImage")
    if isinstance(raw, str) and raw.strip():
        ref = image_manifest.get("inputImage", "images/inputImage.jpg")
        if resolve_artifact_image(artifacts, ref):
            return ref
    output_images = page_result.get("outputImages")
    if isinstance(output_images, dict):
        for key in ("layout_det_res", "page", "input"):
            ref = image_manifest.get(str(key))
            if ref and resolve_artifact_image(artifacts, ref):
                return ref
    return None


def _block_asset(block: dict[str, Any]) -> dict[str, Any] | None:
    ref = str(block.get("image_ref") or block.get("crop_ref") or "").strip()
    source_path = str((block.get("evidence") or {}).get("artifact_image_path") or "").strip()
    if not ref or not source_path:
        return None
    return {
        "asset_id": f"{block.get('id')}-image",
        "page_no": block.get("source_page"),
        "block_id": block.get("id"),
        "block_type": block.get("type"),
        "artifact_ref": ref,
        "source_path": source_path,
    }


def _blocks_to_raw_text(blocks: list[dict[str, Any]]) -> str:
    return "\n\n".join(str(block.get("text") or "").strip() for block in blocks if str(block.get("text") or "").strip()).strip()


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _file_sha256(path: str | Path) -> str | None:
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def _guess_source_path(artifacts: PaddleOCRArtifacts) -> str | None:
    data = load_artifact_json(artifacts.job_json)
    if isinstance(data, dict):
        for key in ("source", "fileUrl", "file_name", "input_path"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return None


def _input_type(path: str | None) -> str | None:
    if not path:
        return None
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        return "pdf"
    if suffix in {".png", ".jpg", ".jpeg", ".jp2", ".webp", ".gif", ".bmp"}:
        return "image"
    return suffix.lstrip(".") or None
