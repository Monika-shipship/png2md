import hashlib
import re
from pathlib import Path
from typing import Any

from .figures import analyze_figure_description
from .formula_quality import assess_formula_text, normalize_inline_math_text
from .ir import PAGE_IR_SCHEMA_VERSION
from .mineru_artifacts import MinerUArtifacts, discover_mineru_artifacts, load_artifact_json, resolve_artifact_image
from .table_quality import assess_table


DOCUMENT_IR_SCHEMA_VERSION = "docpage2md-docir-v1"
MINERU_ADAPTER_VERSION = "mineru-adapter-2026-06-23-v1"


def load_mineru_document_ir(
    artifact_root: str | Path,
    *,
    source_path: str | None = None,
    engine_mode: str = "mineru_only",
) -> dict[str, Any]:
    artifacts = discover_mineru_artifacts(artifact_root)
    return adapt_mineru_artifacts(artifacts, source_path=source_path, engine_mode=engine_mode)


def adapt_mineru_artifacts(
    artifacts: MinerUArtifacts,
    *,
    source_path: str | None = None,
    engine_mode: str = "mineru_only",
) -> dict[str, Any]:
    content_pages = _load_content_pages(artifacts)
    block_pages = _load_block_pages(artifacts)
    page_count = max(len(content_pages), len(block_pages))
    if page_count <= 0:
        raise ValueError(f"MinerU artifact has no page blocks: {artifacts.root}")

    pages = []
    assets = []
    for page_idx in range(page_count):
        source_items = content_pages[page_idx] if page_idx < len(content_pages) and content_pages[page_idx] else []
        fallback_items = block_pages[page_idx] if page_idx < len(block_pages) else []
        if not source_items:
            source_items = [_block_list_item_to_content_item(item) for item in fallback_items]

        page_size = _page_size(fallback_items)
        used_block_indexes: set[int] = set()
        blocks = []
        for item in source_items:
            match_index, match = _match_block_list_item(item, fallback_items, used_block_indexes, page_size)
            if match_index is not None:
                used_block_indexes.add(match_index)
            block = _adapt_content_item(
                item,
                match,
                artifacts=artifacts,
                page_no=page_idx + 1,
                block_no=len(blocks) + 1,
                page_size=page_size,
            )
            if block is None:
                continue
            blocks.append(block)
            asset = _block_asset(block)
            if asset:
                assets.append(asset)

        raw_text = _blocks_to_raw_text(blocks)
        pages.append(
            {
                "schema_version": PAGE_IR_SCHEMA_VERSION,
                "source_page": page_idx + 1,
                "page_image_ref": None,
                "raw_text": raw_text,
                "raw_text_sha256": _sha256_text(raw_text),
                "blocks": blocks,
                "mineru": {
                    "page_idx": page_idx,
                    "page_size": page_size,
                    "artifact_refs": artifacts.to_manifest(),
                },
            }
        )

    input_path = source_path or _guess_source_path(artifacts)
    return {
        "schema_version": DOCUMENT_IR_SCHEMA_VERSION,
        "adapter_version": MINERU_ADAPTER_VERSION,
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


def rewrite_asset_refs(document_ir: dict[str, Any], ref_map: dict[str, str]) -> dict[str, Any]:
    """Rewrite artifact-local image refs to output-relative asset refs."""
    for page in document_ir.get("pages") or []:
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


def iter_artifact_image_refs(document_ir: dict[str, Any]) -> list[dict[str, str]]:
    refs = []
    seen = set()
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


def _load_content_pages(artifacts: MinerUArtifacts) -> list[list[dict[str, Any]]]:
    data = load_artifact_json(artifacts.content_list_v2_json)
    if data:
        pages = _coerce_pages(data)
        if pages:
            return pages
    data = load_artifact_json(artifacts.content_list_json)
    return _coerce_pages(data)


def _load_block_pages(artifacts: MinerUArtifacts) -> list[list[dict[str, Any]]]:
    data = load_artifact_json(artifacts.block_list_json)
    if isinstance(data, dict) and isinstance(data.get("pdfData"), list):
        return [[item for item in page if isinstance(item, dict)] for page in data["pdfData"]]
    return _coerce_pages(data)


def _coerce_pages(data: Any) -> list[list[dict[str, Any]]]:
    if not isinstance(data, list):
        return []
    if data and all(isinstance(page, list) for page in data):
        return [[item for item in page if isinstance(item, dict)] for page in data]
    grouped: dict[int, list[dict[str, Any]]] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        page_idx = item.get("page_idx", 0)
        if isinstance(page_idx, bool) or not isinstance(page_idx, int):
            page_idx = 0
        grouped.setdefault(page_idx, []).append(item)
    return [grouped[index] for index in sorted(grouped)]


def _block_list_item_to_content_item(item: dict[str, Any]) -> dict[str, Any]:
    block_type = item.get("type")
    text = str(item.get("text") or item.get("description") or "").strip()
    if block_type == "title":
        return {"type": "title", "content": {"title_content": [{"type": "text", "content": _strip_heading(text)}]}, "bbox": item.get("bbox")}
    if block_type == "interline_equation":
        return {"type": "equation_interline", "content": {"math_content": _strip_display_math(text)}, "bbox": item.get("bbox")}
    if block_type in {"image", "chart"}:
        return {
            "type": block_type,
            "content": {
                "content": text,
                "image_source": {"path": item.get("img_path")},
            },
            "sub_type": item.get("sub_type"),
            "bbox": item.get("bbox"),
        }
    return {"type": "paragraph", "content": {"paragraph_content": [{"type": "text", "content": text}]}, "bbox": item.get("bbox")}


def _adapt_content_item(
    item: dict[str, Any],
    match: dict[str, Any] | None,
    *,
    artifacts: MinerUArtifacts,
    page_no: int,
    block_no: int,
    page_size: list[int] | None,
) -> dict[str, Any] | None:
    mineru_type = str(item.get("type") or match.get("type") if match else item.get("type") or "").strip()
    text = normalize_inline_math_text(_content_text(item)).strip()
    image_ref = _content_image_ref(item) or (match or {}).get("img_path")
    resolved_image = resolve_artifact_image(artifacts, image_ref)
    artifact_image_ref = _artifact_image_ref(artifacts, resolved_image, image_ref)
    bbox = _bbox(item.get("bbox"), match, page_size)

    block_type = _block_type(mineru_type, text, item)
    if block_type is None:
        return None
    if not text and not artifact_image_ref and block_type not in {"figure_note", "image_ref", "table"}:
        return None

    block = {
        "id": f"p{page_no:04d}-b{block_no:03d}",
        "type": block_type,
        "text": text,
        "source_page": page_no,
        "confidence": _confidence(block_type, mineru_type, text),
        "origin": _origin(block_type),
        "evidence": {
            "raw_text": text or artifact_image_ref or mineru_type,
            "provider": "mineru",
            "mineru_type": mineru_type,
            "mineru_block_id": (match or {}).get("id"),
            "mineru_block_position": (match or {}).get("block_position"),
            "artifact_image_ref": artifact_image_ref,
            "artifact_image_path": str(resolved_image) if resolved_image else None,
        },
        "bbox": bbox,
        "page_size": page_size,
        "source_engine": "mineru",
    }

    if artifact_image_ref:
        block["crop_ref"] = artifact_image_ref
        block["image_ref"] = artifact_image_ref

    if block_type == "heading":
        block["text"] = _strip_heading(text)
    elif block_type in {"formula_inline", "formula_block"}:
        latex = _strip_display_math(text)
        quality = assess_formula_text(latex)
        block.update(
            {
                "text": quality.latex,
                "latex": quality.latex,
                "raw_text": latex,
                "formula_quality": quality.to_dict(),
                "warnings": [warning.to_dict() for warning in quality.warnings],
            }
        )
        if artifact_image_ref:
            block["formula_image_path"] = artifact_image_ref
    elif block_type == "figure_note":
        description = text
        analysis = analyze_figure_description(description)
        fields = analysis.to_block_fields()
        if mineru_type == "chart":
            fields["figure_type"] = "chart"
            fields["figure"]["figure_type"] = "chart"
        block.update(fields)
        block["description"] = description
        if not description and artifact_image_ref:
            block["type"] = "image_ref"
            block["text"] = ""
            block["origin"] = "vision_description"
            block["alt"] = _image_alt(page_no, block_no, mineru_type)
        else:
            block["alt"] = _image_alt(page_no, block_no, mineru_type)
    elif block_type == "table":
        quality = assess_table(text)
        block.update(
            {
                "table_format": quality.table_format if quality.reliable else "uncertain",
                "table_reliable": quality.reliable,
                "table_render_mode": "normalized_markdown" if quality.reliable and quality.normalized_markdown else "degraded_warning",
                "degrade_reason_codes": [issue.code for issue in quality.errors + quality.warnings] if not quality.reliable else [],
                "rows": quality.row_count,
                "columns": quality.column_counts,
                "raw_text": text,
                "table_quality": quality.to_dict(),
                "alt": _image_alt(page_no, block_no, mineru_type),
            }
        )
        if artifact_image_ref:
            block["table_image_path"] = artifact_image_ref

    return block


def _content_text(item: dict[str, Any]) -> str:
    content = item.get("content")
    if isinstance(content, dict):
        if "math_content" in content:
            return str(content.get("math_content") or "").strip()
        if "content" in content:
            return str(content.get("content") or "").strip()
        for key in ("title_content", "paragraph_content", "table_content"):
            value = content.get(key)
            if isinstance(value, list):
                return _join_content_parts(value)
        return ""
    if isinstance(content, str):
        return content.strip()
    return str(item.get("text") or item.get("description") or "").strip()


def _join_content_parts(parts: list[Any]) -> str:
    rendered = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        part_type = str(part.get("type") or "")
        value = str(part.get("content") or part.get("text") or "")
        if not value:
            continue
        if part_type in {"equation_inline", "inline_equation"}:
            rendered.append(f"${value.strip()}$")
        else:
            rendered.append(value)
    return "".join(rendered).strip()


def _content_image_ref(item: dict[str, Any]) -> str | None:
    content = item.get("content")
    if not isinstance(content, dict):
        return None
    image_source = content.get("image_source")
    if isinstance(image_source, dict):
        return image_source.get("path")
    return None


def _match_block_list_item(
    item: dict[str, Any],
    block_items: list[dict[str, Any]],
    used: set[int],
    page_size: list[int] | None,
) -> tuple[int | None, dict[str, Any] | None]:
    expected_type = _mineru_block_list_type(item)
    converted_bbox = _scaled_bbox(item.get("bbox"), page_size)
    best_index = None
    best_score = None
    for index, candidate in enumerate(block_items):
        if index in used:
            continue
        if expected_type and candidate.get("type") != expected_type:
            continue
        score = _bbox_distance(converted_bbox, candidate.get("bbox"))
        if best_score is None or score < best_score:
            best_index = index
            best_score = score
    if best_index is not None:
        return best_index, block_items[best_index]
    for index, candidate in enumerate(block_items):
        if index not in used:
            return index, candidate
    return None, None


def _mineru_block_list_type(item: dict[str, Any]) -> str | None:
    item_type = str(item.get("type") or "")
    return {
        "title": "title",
        "paragraph": "text",
        "equation_interline": "interline_equation",
        "interline_equation": "interline_equation",
        "image": "image",
        "chart": "chart",
        "table": "table",
    }.get(item_type)


def _block_type(mineru_type: str, text: str, item: dict[str, Any]) -> str | None:
    if mineru_type == "title":
        return "heading"
    if mineru_type == "paragraph":
        return "formula_inline" if "$" in text else "paragraph"
    if mineru_type in {"equation_interline", "interline_equation"}:
        return "formula_block"
    if mineru_type == "table":
        return "table"
    if mineru_type in {"image", "chart"}:
        return "figure_note"
    if text:
        return "paragraph"
    return None


def _origin(block_type: str) -> str:
    if block_type in {"formula_inline", "formula_block"}:
        return "vision_formula"
    if block_type == "table":
        return "vision_table"
    if block_type in {"figure_note", "image_ref"}:
        return "vision_description"
    if block_type == "uncertain":
        return "vision_uncertain"
    return "vision_ocr"


def _confidence(block_type: str, mineru_type: str, text: str) -> float:
    if block_type == "figure_note" and analyze_figure_description(text).unrecognizable:
        return 0.35
    if block_type == "heading":
        return 0.86
    if block_type == "paragraph":
        return 0.78
    if block_type in {"formula_inline", "formula_block"}:
        return 0.70
    if block_type == "table":
        return 0.70
    if block_type in {"figure_note", "image_ref"}:
        return 0.76 if mineru_type == "chart" else 0.72
    return 0.55


def _page_size(page_blocks: list[dict[str, Any]]) -> list[int] | None:
    for block in page_blocks:
        value = block.get("page_size")
        if isinstance(value, list) and len(value) == 2 and all(isinstance(item, (int, float)) for item in value):
            return [int(value[0]), int(value[1])]
    return None


def _bbox(value: Any, match: dict[str, Any] | None, page_size: list[int] | None) -> list[float] | None:
    if match and _valid_bbox(match.get("bbox")):
        return [float(item) for item in match["bbox"]]
    return _scaled_bbox(value, page_size)


def _scaled_bbox(value: Any, page_size: list[int] | None) -> list[float] | None:
    if not _valid_bbox(value):
        return None
    bbox = [float(item) for item in value]
    if page_size and max(bbox[0], bbox[2]) > page_size[0] * 1.05:
        bbox[0] = bbox[0] * page_size[0] / 1000
        bbox[2] = bbox[2] * page_size[0] / 1000
    if page_size and max(bbox[1], bbox[3]) > page_size[1] * 1.05:
        bbox[1] = bbox[1] * page_size[1] / 1000
        bbox[3] = bbox[3] * page_size[1] / 1000
    return [round(item, 3) for item in bbox]


def _valid_bbox(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 4 and all(isinstance(item, (int, float)) for item in value)


def _bbox_distance(left: list[float] | None, right: Any) -> float:
    if not left or not _valid_bbox(right):
        return 1_000_000.0
    return sum(abs(float(a) - float(b)) for a, b in zip(left, right))


def _artifact_image_ref(artifacts: MinerUArtifacts, resolved: Path | None, original: str | None) -> str | None:
    if resolved is not None:
        try:
            return resolved.relative_to(artifacts.root).as_posix()
        except ValueError:
            return resolved.as_posix()
    raw = str(original or "").strip().lstrip("/\\")
    if raw:
        name = Path(raw).name
        return f"images/{name}" if name else raw.replace("\\", "/")
    return None


def _block_asset(block: dict[str, Any]) -> dict[str, str] | None:
    evidence = block.get("evidence") or {}
    artifact_ref = evidence.get("artifact_image_ref")
    source_path = evidence.get("artifact_image_path")
    if not artifact_ref or not source_path:
        return None
    return {
        "block_id": block["id"],
        "page_no": str(block["source_page"]),
        "block_type": block["type"],
        "artifact_ref": artifact_ref,
        "source_path": source_path,
    }


def _blocks_to_raw_text(blocks: list[dict[str, Any]]) -> str:
    chunks = []
    for block in blocks:
        block_type = block.get("type")
        text = str(block.get("text") or block.get("description") or "").strip()
        if block_type == "formula_block":
            chunks.append(f"### Formula\n{text}")
        elif block_type == "figure_note":
            chunks.append(f"### Figure Analysis\n{text}" if text else "### Figure Analysis\n[image]")
        elif block_type == "table":
            chunks.append(f"### Table Analysis\n{text}")
        elif block_type == "image_ref":
            chunks.append(f"### Figure Analysis\n[image: {block.get('image_ref') or block.get('path') or ''}]")
        elif text:
            chunks.append(text)
    return "\n\n".join(chunks).strip()


def _strip_display_math(text: str) -> str:
    stripped = (text or "").strip()
    if stripped.startswith("$$") and stripped.endswith("$$"):
        stripped = stripped[2:-2]
    if stripped.startswith(r"\[") and stripped.endswith(r"\]"):
        stripped = stripped[2:-2]
    return stripped.strip()


def _strip_heading(text: str) -> str:
    return re.sub(r"^#{1,6}\s*", "", text or "").strip()


def _image_alt(page_no: int, block_no: int, mineru_type: str) -> str:
    label = "chart" if mineru_type == "chart" else "figure"
    return f"page {page_no} {label} {block_no}"


def _guess_source_path(artifacts: MinerUArtifacts) -> str | None:
    candidates = sorted(artifacts.root.glob("*_origin.*"))
    if candidates:
        return str(candidates[0])
    return None


def _input_type(path: str | None) -> str | None:
    if not path:
        return None
    suffix = Path(path).suffix.lower().lstrip(".")
    if suffix in {"jpg", "jpeg", "png", "webp", "bmp", "gif", "jp2"}:
        return "image"
    return suffix or None


def _file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()
