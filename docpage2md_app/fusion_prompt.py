from __future__ import annotations

import json
from typing import Any


FUSION_ALLOWED_ACTIONS = {
    "choose_block",
    "merge_blocks",
    "keep_both",
    "mark_uncertain",
    "attach_image",
    "replace_formula",
    "convert_text_to_formula",
    "convert_text_to_figure_note",
}


def build_fusion_decision_prompt(candidate_groups: list[dict[str, Any]], *, document_type: str = "custom") -> str:
    """Build a constrained prompt for future Brain-based candidate fusion.

    The fusion layer should pass candidate groups, not raw whole-page JSON. The
    model may only return whitelisted structured ops; program code applies and
    validates them.
    """
    public_groups = [_public_group(group) for group in candidate_groups]
    return (
        "你是 DocPage2MD 的双引擎融合裁决器。只能输出 JSON，不得输出 Markdown，不得输出思考过程。\n"
        "输入已经由程序按页码、bbox、文本相似度和类型相似度粗分为候选组；不要自己重建整页对应关系。\n"
        "任务：在每个候选组内做保守裁决。宁可 keep_both 或 mark_uncertain，也不要误删任一引擎独有内容。\n"
        "公式必须 LaTeX 化；不要保留裸 φ、θ、ω、α、β、≤、≥、→ 等 Unicode 数学符号。\n"
        "允许 action："
        + ", ".join(sorted(FUSION_ALLOWED_ACTIONS))
        + "\n"
        "返回格式：{\"ops\":[{\"action\":\"choose_block\",\"target_group\":\"p0001-g001\",\"source\":\"mineru\",\"reason\":\"...\"}],\"warnings\":[]}\n"
        f"文档类型：{document_type}\n"
        f"候选组 JSON：{json.dumps(public_groups, ensure_ascii=False)}"
    )


def build_figure_context_payload(page_ir: dict[str, Any], block: dict[str, Any], *, document_type: str = "custom") -> dict[str, Any]:
    """Build structured local context for figure/table/formula crop prompts."""
    blocks = page_ir.get("blocks") or []
    block_id = block.get("id")
    index = next((idx for idx, item in enumerate(blocks) if item.get("id") == block_id), -1)
    before = [_compact_block(item) for item in blocks[max(0, index - 2) : index] if _text_of(item)] if index >= 0 else []
    after = [_compact_block(item) for item in blocks[index + 1 : index + 3] if _text_of(item)] if index >= 0 else []
    formulas = [
        _compact_block(item)
        for item in blocks
        if item.get("type") in {"formula_block", "formula_inline"} and _nearby_bbox(block.get("bbox"), item.get("bbox"))
    ][:6]
    headings = [
        _text_of(item)
        for item in blocks[: index if index >= 0 else len(blocks)]
        if item.get("type") == "heading" and _text_of(item)
    ]
    fusion_candidates = []
    fusion = page_ir.get("fusion")
    if isinstance(fusion, dict):
        group_id = ((block.get("evidence") or {}).get("fusion") or {}).get("group_id")
        for group in fusion.get("candidate_groups") or []:
            if group.get("group_id") == group_id:
                fusion_candidates = group.get("candidates") or []
                break
    dual_evidence = page_ir.get("dual_evidence") if isinstance(page_ir.get("dual_evidence"), dict) else {}
    return {
        "page": page_ir.get("source_page"),
        "document_type": document_type,
        "page_title": headings[-1] if headings else None,
        "figure_block": {
            "id": block.get("id"),
            "source": block.get("source_engine") or block.get("origin"),
            "type": block.get("type"),
            "bbox": block.get("bbox"),
            "nearby_text_before": before,
            "nearby_text_after": after,
            "nearby_formulas": formulas,
            "caption_candidates": _caption_candidates(blocks, index),
            "other_engine_candidates": _other_engine_candidates(block, fusion_candidates, dual_evidence),
        },
    }


def _public_group(group: dict[str, Any]) -> dict[str, Any]:
    return {
        "group_id": group.get("group_id"),
        "page_no": group.get("page_no"),
        "type_hint": group.get("type_hint"),
        "match_reason": group.get("match_reason"),
        "candidates": [
            {
                "source": candidate.get("source"),
                "block_id": candidate.get("block_id"),
                "type": candidate.get("type"),
                "text": candidate.get("text"),
                "bbox": candidate.get("bbox"),
                "confidence": candidate.get("confidence"),
                "warnings": candidate.get("warnings") or [],
            }
            for candidate in group.get("candidates") or []
        ],
        "warnings": group.get("warnings") or [],
    }


def _compact_block(block: dict[str, Any], *, limit: int = 220) -> dict[str, Any]:
    text = _text_of(block)
    return {
        "id": block.get("id"),
        "type": block.get("type"),
        "text": text if len(text) <= limit else text[: limit - 3].rstrip() + "...",
        "bbox": block.get("bbox"),
    }


def _text_of(block: dict[str, Any]) -> str:
    return str(block.get("latex") or block.get("text") or block.get("description") or "").strip()


def _caption_candidates(blocks: list[dict[str, Any]], index: int) -> list[str]:
    if index < 0:
        return []
    candidates = []
    for item in blocks[max(0, index - 2) : min(len(blocks), index + 3)]:
        text = _text_of(item)
        if text and ("图" in text or "Figure" in text or "caption" in text.lower()):
            candidates.append(text[:240])
    return candidates[:4]


def _other_engine_candidates(block: dict[str, Any], fusion_candidates: list[dict[str, Any]], dual_evidence: dict[str, Any]) -> list[dict[str, Any]]:
    source = block.get("source_engine") or block.get("origin")
    candidates = []
    for candidate in fusion_candidates:
        if candidate.get("source") and candidate.get("source") != source:
            candidates.append(
                {
                    "source": candidate.get("source"),
                    "block_id": candidate.get("block_id"),
                    "type": candidate.get("type"),
                    "text": candidate.get("text"),
                    "image_ref": candidate.get("image_ref"),
                }
            )
    if candidates:
        return candidates[:8]
    for engine in ("mineru", "paddleocr"):
        payload = dual_evidence.get(engine) if isinstance(dual_evidence.get(engine), dict) else {}
        for item in payload.get("blocks") or []:
            if item.get("id") != block.get("id") and _nearby_bbox(block.get("bbox"), item.get("bbox")):
                candidates.append({"source": engine, "block_id": item.get("id"), "type": item.get("type"), "text": item.get("text")})
    return candidates[:8]


def _nearby_bbox(left: Any, right: Any) -> bool:
    if not _valid_bbox(left) or not _valid_bbox(right):
        return False
    ly = (float(left[1]) + float(left[3])) / 2.0
    ry = (float(right[1]) + float(right[3])) / 2.0
    height = max(abs(float(left[3]) - float(left[1])), abs(float(right[3]) - float(right[1])), 1.0)
    return abs(ly - ry) <= height * 2.5


def _valid_bbox(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 4 and all(isinstance(item, (int, float)) for item in value)
