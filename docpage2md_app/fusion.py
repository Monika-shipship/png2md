from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Any, Callable

from .artifacts import sha256_text
from .figures import analyze_figure_description
from .formula_quality import assess_formula_text, contains_unicode_math_symbols, normalize_inline_math_text
from .fusion_prompt import build_figure_context_payload
from .fusion_prompt import FUSION_ALLOWED_ACTIONS
from .ir import PAGE_IR_SCHEMA_VERSION
from .renderer import render_page_ir_to_markdown
from .table_quality import assess_table
from .validators import is_api_error_text, validate_slide_markdown


FUSION_VERSION = "fusion-2026-06-25-v1"
FUSION_ENGINE_MODE = "dual_hybrid"
FusionDecisionBackend = Callable[[dict[str, Any], list[dict[str, Any]], dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class FusionResult:
    document_ir: dict[str, Any]
    report: dict[str, Any]


def fuse_document_irs(
    mineru_ir: dict[str, Any],
    paddleocr_ir: dict[str, Any],
    *,
    decision_backend: FusionDecisionBackend | None = None,
    document_type: str = "custom",
    engine_mode: str = FUSION_ENGINE_MODE,
) -> FusionResult:
    """Fuse two DocumentIR objects through page alignment and checked ops.

    The offline default is conservative and deterministic. If a decision backend
    is supplied, its structured ops are still validated by this module.
    """
    mineru_pages = _pages_by_no(mineru_ir)
    paddle_pages = _pages_by_no(paddleocr_ir)
    page_numbers = sorted(set(mineru_pages) | set(paddle_pages))
    pages: list[dict[str, Any]] = []
    page_reports: dict[str, Any] = {}
    all_groups: list[dict[str, Any]] = []
    all_decisions: list[dict[str, Any]] = []
    all_rejected: list[dict[str, Any]] = []
    uncertain_items: list[dict[str, Any]] = []

    for page_no in page_numbers:
        mineru_page = mineru_pages.get(page_no)
        paddle_page = paddle_pages.get(page_no)
        groups = build_candidate_groups(mineru_page, paddle_page, page_no=page_no)
        public_groups = _public_groups(groups)
        default_ops = propose_default_fusion_ops(groups)
        backend_ops: list[dict[str, Any]] = []
        backend_warnings: list[Any] = []
        backend_error = None
        if decision_backend is not None:
            try:
                response = decision_backend(
                    {"page_no": page_no, "document_type": document_type},
                    groups,
                    {"mineru": mineru_page, "paddleocr": paddle_page},
                )
                if isinstance(response, dict):
                    backend_ops = [item for item in (response.get("ops") or []) if isinstance(item, dict)]
                    backend_warnings = response.get("warnings") if isinstance(response.get("warnings"), list) else []
            except Exception as exc:
                backend_error = _safe_text(str(exc), 240)
        ops = backend_ops or default_ops
        page_ir, apply_report = apply_fusion_ops(
            mineru_page,
            paddle_page,
            groups,
            ops,
            page_no=page_no,
            engine_mode=engine_mode,
        )
        page_ir["fusion"] = {
            "version": FUSION_VERSION,
            "document_type": document_type,
            "candidate_groups": public_groups,
            "decisions": apply_report["decisions"],
            "rejected_ops": apply_report["rejected_ops"],
            "uncertain_items": apply_report["uncertain_items"],
            "backend": "custom" if decision_backend else "deterministic_default",
            "backend_warnings": backend_warnings,
            "backend_error": backend_error,
        }
        page_ir["dual_evidence"] = _dual_evidence(mineru_page, paddle_page)
        _attach_figure_contexts(page_ir, document_type=document_type)
        page_ir["raw_text"] = _combined_raw_text(mineru_page, paddle_page)
        page_ir["raw_text_sha256"] = sha256_text(page_ir.get("raw_text") or "")
        pages.append(page_ir)
        page_reports[str(page_no)] = {
            "page_no": page_no,
            "mineru_available": mineru_page is not None,
            "paddleocr_available": paddle_page is not None,
            "candidate_groups": public_groups,
            "decisions": apply_report["decisions"],
            "rejected_ops": apply_report["rejected_ops"],
            "uncertain_items": apply_report["uncertain_items"],
            "backend_warnings": backend_warnings,
            "backend_error": backend_error,
            "validation": apply_report["validation"],
        }
        all_groups.extend(public_groups)
        all_decisions.extend(apply_report["decisions"])
        all_rejected.extend(apply_report["rejected_ops"])
        uncertain_items.extend(apply_report["uncertain_items"])

    fused_ir = {
        "schema_version": _first_value(mineru_ir.get("schema_version"), paddleocr_ir.get("schema_version"), "docpage2md-docir-v1"),
        "adapter_version": FUSION_VERSION,
        "engine_mode": engine_mode,
        "source": _source(mineru_ir, paddleocr_ir),
        "pages": pages,
        "assets": list(mineru_ir.get("assets") or []) + _namespaced_assets(paddleocr_ir, "paddleocr"),
        "metadata": {
            "fusion": {
                "version": FUSION_VERSION,
                "strategy": "candidate_group_checked_ops",
                "document_type": document_type,
                "page_count": len(pages),
                "candidate_group_count": len(all_groups),
                "decision_count": len(all_decisions),
                "rejected_op_count": len(all_rejected),
                "uncertain_count": len(uncertain_items),
            },
            "mineru": mineru_ir.get("metadata") or {},
            "paddleocr": paddleocr_ir.get("metadata") or {},
        },
    }
    report = {
        "version": FUSION_VERSION,
        "strategy": "candidate_group_checked_ops",
        "document_type": document_type,
        "summary": {
            "pages": len(pages),
            "candidate_groups": len(all_groups),
            "decisions": len(all_decisions),
            "rejected_ops": len(all_rejected),
            "uncertain_items": len(uncertain_items),
        },
        "pages": page_reports,
        "candidate_groups": all_groups,
        "decisions": all_decisions,
        "rejected_ops": all_rejected,
        "uncertain_items": uncertain_items,
    }
    return FusionResult(fused_ir, report)


def build_candidate_groups(mineru_page: dict[str, Any] | None, paddleocr_page: dict[str, Any] | None, *, page_no: int) -> list[dict[str, Any]]:
    mineru_candidates = [_candidate("mineru", block, page_no, index) for index, block in enumerate((mineru_page or {}).get("blocks") or [], start=1)]
    paddle_candidates = [_candidate("paddleocr", block, page_no, index) for index, block in enumerate((paddleocr_page or {}).get("blocks") or [], start=1)]
    groups: list[dict[str, Any]] = []
    used_paddle: set[int] = set()
    group_index = 1

    for mineru_candidate in mineru_candidates:
        match_index, score, reason = _best_match(mineru_candidate, paddle_candidates, used_paddle)
        candidates = [mineru_candidate]
        match_reason = "unmatched_from_mineru"
        if match_index is not None:
            used_paddle.add(match_index)
            candidates.append(paddle_candidates[match_index])
            match_reason = reason
        group = _group(page_no, group_index, candidates, match_reason=match_reason, score=score)
        groups.append(group)
        group_index += 1

    for index, paddle_candidate in enumerate(paddle_candidates):
        if index in used_paddle:
            continue
        groups.append(_group(page_no, group_index, [paddle_candidate], match_reason="unmatched_from_paddleocr", score=0.0))
        group_index += 1

    return groups


def propose_default_fusion_ops(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    for group in groups:
        candidates = _group_candidates(group)
        group_id = group.get("group_id")
        if not candidates or not group_id:
            continue
        if len(candidates) == 1:
            ops.append({"action": "keep_both", "target_group": group_id, "reason": group.get("match_reason") or "single_candidate"})
            continue
        best = _best_candidate(candidates)
        if best and _candidate_is_clearly_better(best, candidates):
            action = "choose_block"
            if best.get("type") == "formula_block" and any(candidate.get("type") != "formula_block" for candidate in candidates):
                action = "replace_formula"
            ops.append({"action": action, "target_group": group_id, "source": best.get("source"), "reason": "candidate_quality_score"})
            continue
        if _complementary_visual_text(candidates):
            ops.append({"action": "keep_both", "target_group": group_id, "reason": "visual_text_complementary"})
            continue
        if _type_hint(candidates) == "formula_block":
            preferred_formula = _best_formula_candidate(candidates) or best
            if preferred_formula:
                ops.append(
                    {
                        "action": "choose_block",
                        "target_group": group_id,
                        "source": preferred_formula.get("source"),
                        "reason": "formula_conflict_choose_best_renderable",
                    }
                )
                continue
        if _text_conflict(candidates):
            ops.append({"action": "mark_uncertain", "target_group": group_id, "reason": "candidate_text_conflict"})
            continue
        preferred = best or candidates[0]
        ops.append({"action": "choose_block", "target_group": group_id, "source": preferred.get("source"), "reason": "minor_difference"})
    return ops


def apply_fusion_ops(
    mineru_page: dict[str, Any] | None,
    paddleocr_page: dict[str, Any] | None,
    groups: list[dict[str, Any]],
    ops: list[dict[str, Any]],
    *,
    page_no: int,
    engine_mode: str = FUSION_ENGINE_MODE,
) -> tuple[dict[str, Any], dict[str, Any]]:
    group_map = {str(group.get("group_id")): group for group in groups if group.get("group_id")}
    by_group_ops: dict[str, list[dict[str, Any]]] = {}
    for op in ops:
        if isinstance(op, dict):
            by_group_ops.setdefault(str(op.get("target_group") or ""), []).append(op)

    blocks: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    rejected_ops: list[dict[str, Any]] = []
    uncertain_items: list[dict[str, Any]] = []
    next_index = 1

    for group in groups:
        group_id = str(group.get("group_id") or "")
        selected_ops = by_group_ops.get(group_id) or [{"action": "keep_both", "target_group": group_id, "reason": "no_op_for_group"}]
        applied_for_group = False
        for op in selected_ops:
            normalized = _normalize_op(op)
            if normalized.get("action") not in FUSION_ALLOWED_ACTIONS:
                rejected_ops.append(_rejected(op, group_id, "unknown_or_unsafe_action"))
                continue
            if group_id not in group_map:
                rejected_ops.append(_rejected(op, group_id, "target_group_not_found"))
                continue
            result_blocks, detail = _apply_group_op(group, normalized, page_no=page_no)
            if result_blocks is None:
                rejected_ops.append(_rejected(op, group_id, detail.get("reason") or "op_rejected"))
                continue
            candidate_page = _base_page(mineru_page, paddleocr_page, page_no=page_no, blocks=blocks + result_blocks, engine_mode=engine_mode)
            validation = validate_slide_markdown(
                render_page_ir_to_markdown(candidate_page, page_no),
                page_no,
                target_raw=_combined_raw_text(mineru_page, paddleocr_page),
                target_blocks=candidate_page.get("blocks") or [],
            )
            if validation.errors:
                rejected_ops.append(_rejected(op, group_id, "validation_would_fail", validation=validation.to_dict()))
                continue
            for block in result_blocks:
                _assign_fused_block_id(block, page_no, next_index, group)
                next_index += 1
            blocks.extend(result_blocks)
            decision = {
                "group_id": group_id,
                "action": normalized.get("action"),
                "status": "applied",
                "source": normalized.get("source"),
                "sources": normalized.get("sources"),
                "reason": normalized.get("reason"),
                "created_block_ids": [block.get("id") for block in result_blocks],
                    "candidate_block_ids": [candidate.get("candidate_id") for candidate in _group_candidates(group)],
            }
            decisions.append(decision)
            if normalized.get("action") == "mark_uncertain":
                uncertain_items.append({"group_id": group_id, "reason": normalized.get("reason"), "block_ids": decision["created_block_ids"]})
            applied_for_group = True
            break
        if not applied_for_group:
            fallback_blocks = [_block_from_candidate(candidate, page_no=page_no) for candidate in _group_candidates(group)]
            for block in fallback_blocks:
                _assign_fused_block_id(block, page_no, next_index, group)
                next_index += 1
            blocks.extend(fallback_blocks)
            decisions.append(
                {
                    "group_id": group_id,
                    "action": "keep_both",
                    "status": "fallback_applied",
                    "reason": "all_ops_rejected",
                    "created_block_ids": [block.get("id") for block in fallback_blocks],
                }
            )

    page_ir = _base_page(mineru_page, paddleocr_page, page_no=page_no, blocks=blocks, engine_mode=engine_mode)
    validation = validate_slide_markdown(
        render_page_ir_to_markdown(page_ir, page_no),
        page_no,
        target_raw=page_ir.get("raw_text"),
        target_blocks=page_ir.get("blocks") or [],
    )
    return page_ir, {
        "decisions": decisions,
        "rejected_ops": rejected_ops,
        "uncertain_items": uncertain_items,
        "validation": validation.to_dict(),
    }


def _group_candidates(group: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = group.get("_candidates")
    if isinstance(candidates, list):
        return [candidate for candidate in candidates if isinstance(candidate, dict)]
    return [candidate for candidate in (group.get("candidates") or []) if isinstance(candidate, dict)]


def _public_groups(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    public = []
    for group in groups:
        public.append(
            {
                "group_id": group.get("group_id"),
                "page_no": group.get("page_no"),
                "type_hint": group.get("type_hint"),
                "match_reason": group.get("match_reason"),
                "match_score": group.get("match_score"),
                "candidates": [_public_candidate(candidate) for candidate in _group_candidates(group)],
                "warnings": group.get("warnings") or [],
            }
        )
    return public


def _candidate(source: str, block: dict[str, Any], page_no: int, index: int) -> dict[str, Any]:
    text = _text_of(block)
    warnings = _candidate_warnings(block, text)
    return {
        "candidate_id": f"{source}:{block.get('id') or f'p{page_no:04d}-b{index:03d}'}",
        "source": source,
        "block_id": block.get("id"),
        "type": block.get("type"),
        "text": text,
        "bbox": block.get("bbox"),
        "confidence": _confidence(block),
        "image_ref": _first_ref(block),
        "warnings": warnings,
        "quality_score": _candidate_quality_score(block, text, warnings),
        "block": copy.deepcopy(block),
    }


def _group(page_no: int, group_index: int, candidates: list[dict[str, Any]], *, match_reason: str, score: float | None) -> dict[str, Any]:
    warnings: list[str] = []
    for candidate in candidates:
        for warning in candidate.get("warnings") or []:
            scoped = f"{candidate.get('source')}_{warning}"
            if scoped not in warnings:
                warnings.append(scoped)
    if len(candidates) > 1 and _text_conflict(candidates):
        warnings.append("candidate_text_conflict")
    return {
        "group_id": f"p{page_no:04d}-g{group_index:03d}",
        "page_no": page_no,
        "type_hint": _type_hint(candidates),
        "match_reason": match_reason,
        "match_score": round(float(score or 0.0), 4),
        "candidates": [_public_candidate(candidate) for candidate in candidates],
        "_candidates": candidates,
        "warnings": warnings,
    }


def _public_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate.get("candidate_id"),
        "source": candidate.get("source"),
        "block_id": candidate.get("block_id"),
        "type": candidate.get("type"),
        "text": _safe_text(candidate.get("text"), 800),
        "bbox": candidate.get("bbox"),
        "confidence": candidate.get("confidence"),
        "image_ref": candidate.get("image_ref"),
        "quality_score": round(float(candidate.get("quality_score") or 0.0), 4),
        "warnings": candidate.get("warnings") or [],
    }


def _best_match(candidate: dict[str, Any], pool: list[dict[str, Any]], used: set[int]) -> tuple[int | None, float, str]:
    best_index = None
    best_score = 0.0
    best_reason = "none"
    for index, other in enumerate(pool):
        if index in used:
            continue
        score, reason = _match_score(candidate, other)
        if score > best_score:
            best_index = index
            best_score = score
            best_reason = reason
    if best_index is None or best_score < 0.56:
        return None, 0.0, "unmatched"
    return best_index, best_score, best_reason


def _match_score(left: dict[str, Any], right: dict[str, Any]) -> tuple[float, str]:
    bbox_score = _bbox_overlap_score(left.get("bbox"), right.get("bbox"))
    text_score = _text_similarity(left.get("text") or "", right.get("text") or "")
    type_score = 1.0 if left.get("type") == right.get("type") else (0.72 if _types_compatible(left.get("type"), right.get("type")) else 0.0)
    vertical_score = _vertical_position_score(left.get("bbox"), right.get("bbox"))
    caption_score = _caption_image_score(left, right)
    score = max(
        bbox_score * 0.70 + type_score * 0.20 + text_score * 0.10,
        text_score * 0.72 + type_score * 0.18 + vertical_score * 0.10,
        vertical_score * 0.48 + type_score * 0.30 + text_score * 0.22,
        caption_score,
    )
    reason = "bbox_overlap" if bbox_score >= 0.45 else "text_similarity" if text_score >= 0.72 else "vertical_type_similarity"
    if caption_score >= score and caption_score >= 0.56:
        reason = "caption_image_proximity"
    return score, reason


def _apply_group_op(group: dict[str, Any], op: dict[str, Any], *, page_no: int) -> tuple[list[dict[str, Any]] | None, dict[str, Any]]:
    candidates = _group_candidates(group)
    action = op.get("action")
    if action in {"choose_block", "replace_formula"}:
        chosen = _candidate_by_source(candidates, op.get("source"))
        if chosen is None:
            return None, {"reason": "source_candidate_not_found"}
        block = _block_from_candidate(chosen, page_no=page_no)
        if action == "replace_formula" and block.get("type") != "formula_block":
            block = _convert_block_to_formula(block, op.get("text") or chosen.get("text") or "")
        return [block], {"reason": "ok"}
    if action == "keep_both":
        return [_block_from_candidate(candidate, page_no=page_no) for candidate in candidates], {"reason": "ok"}
    if action == "mark_uncertain":
        chosen = _best_uncertain_render_candidate(candidates)
        if chosen is None:
            return None, {"reason": "no_renderable_uncertain_candidate"}
        block = _block_from_candidate(chosen, page_no=page_no)
        evidence = block.setdefault("evidence", {})
        evidence["fusion_action"] = "mark_uncertain"
        evidence["uncertain_resolution"] = {
            "chosen_source": chosen.get("source"),
            "reason": op.get("reason") or "candidate_text_conflict",
            "candidate_ids": [candidate.get("candidate_id") for candidate in candidates],
            "candidates": [_audit_candidate(candidate) for candidate in candidates],
        }
        block["confidence"] = min(_valid_confidence(block.get("confidence"), default=0.55), 0.62)
        block["source_engine"] = chosen.get("source")
        return [block], {"reason": "ok"}
    if action == "merge_blocks":
        text = _safe_model_text(op.get("text"))
        if not text:
            text = "\n".join(_candidate_by_id(candidates, item).get("text") for item in op.get("sources") or [] if _candidate_by_id(candidates, item))
        if not text:
            return None, {"reason": "missing_merge_text"}
        block_type = _type_hint(candidates)
        block = _new_block_from_group(group, text, block_type=block_type, page_no=page_no, action="merge_blocks")
        return [block], {"reason": "ok"}
    if action == "attach_image":
        chosen = _candidate_by_source(candidates, op.get("source")) or _first_image_candidate(candidates)
        if chosen is None:
            return None, {"reason": "image_candidate_not_found"}
        block = _block_from_candidate(chosen, page_no=page_no)
        image_ref = op.get("image_ref") or chosen.get("image_ref")
        if image_ref:
            block["image_ref"] = image_ref
            block["path"] = image_ref
            if block.get("type") not in {"figure_note", "image_ref", "table", "formula_block"}:
                block["type"] = "image_ref"
        return [block], {"reason": "ok"}
    if action == "convert_text_to_formula":
        chosen = _candidate_by_source(candidates, op.get("source")) or _best_candidate(candidates)
        if chosen is None:
            return None, {"reason": "candidate_not_found"}
        return [_convert_block_to_formula(_block_from_candidate(chosen, page_no=page_no), op.get("latex") or chosen.get("text") or "")], {"reason": "ok"}
    if action == "convert_text_to_figure_note":
        chosen = _candidate_by_source(candidates, op.get("source")) or _best_candidate(candidates)
        if chosen is None:
            return None, {"reason": "candidate_not_found"}
        block = _block_from_candidate(chosen, page_no=page_no)
        text = _safe_model_text(op.get("description")) or block.get("description") or block.get("text") or ""
        block["type"] = "figure_note"
        block["text"] = normalize_inline_math_text(text)
        block["description"] = block["text"]
        block["origin"] = "vision_description"
        block["confidence"] = max(float(block.get("confidence") or 0.0), 0.55)
        block.update(analyze_figure_description(block["description"]).to_block_fields())
        return [block], {"reason": "ok"}
    return None, {"reason": "unsupported_action"}


def _block_from_candidate(candidate: dict[str, Any], *, page_no: int) -> dict[str, Any]:
    block = copy.deepcopy(candidate.get("block") or {})
    block.pop("id", None)
    block["source_page"] = page_no
    block["text"] = normalize_inline_math_text(block.get("latex") or block.get("text") or block.get("description") or candidate.get("text") or "")
    if block.get("type") in {"formula_block", "formula_inline"}:
        _update_formula_fields(block, block["text"])
    if block.get("type") == "table":
        _update_table_fields(block, block.get("text") or "")
    if block.get("type") == "figure_note":
        block["description"] = normalize_inline_math_text(block.get("description") or block.get("text") or "")
        block["text"] = block["description"]
    block["origin"] = block.get("origin") or _origin_for_type(block.get("type"))
    block["confidence"] = _valid_confidence(block.get("confidence"), default=candidate.get("confidence") or 0.55)
    block["bbox"] = block.get("bbox") if _valid_bbox(block.get("bbox")) else candidate.get("bbox")
    block["source_engine"] = candidate.get("source")
    evidence = block.setdefault("evidence", {})
    evidence["fusion_source"] = candidate.get("source")
    evidence["fusion_candidate_id"] = candidate.get("candidate_id")
    evidence.setdefault("raw_text", candidate.get("text") or candidate.get("image_ref") or "")
    evidence.setdefault("provider", candidate.get("source") or "dual_fusion")
    return block


def _new_block_from_group(group: dict[str, Any], text: str, *, block_type: str, page_no: int, action: str) -> dict[str, Any]:
    text = normalize_inline_math_text(text)
    block = {
        "type": block_type if block_type in _allowed_block_types() else "paragraph",
        "text": text,
        "source_page": page_no,
        "confidence": 0.72,
        "origin": _origin_for_type(block_type),
        "evidence": {
            "raw_text": text,
            "provider": "dual_fusion",
            "fusion_action": action,
            "candidate_ids": [candidate.get("candidate_id") for candidate in _group_candidates(group)],
        },
        "bbox": _union_bbox([candidate.get("bbox") for candidate in _group_candidates(group)]),
        "source_engine": "dual_fusion",
    }
    if block["type"] == "formula_block":
        _update_formula_fields(block, text)
    if block["type"] == "table":
        _update_table_fields(block, text)
    if block["type"] == "figure_note":
        block["description"] = text
        block.update(analyze_figure_description(text).to_block_fields())
    return block


def _convert_block_to_formula(block: dict[str, Any], latex: str) -> dict[str, Any]:
    text = _safe_model_text(latex) or block.get("text") or ""
    block["type"] = "formula_block"
    block["text"] = text
    block["origin"] = "vision_formula"
    _update_formula_fields(block, text)
    evidence = block.setdefault("evidence", {})
    evidence["fusion_action"] = "convert_text_to_formula"
    return block


def _assign_fused_block_id(block: dict[str, Any], page_no: int, index: int, group: dict[str, Any]) -> None:
    old_id = block.get("id")
    group_id = str(group.get("group_id") or "")
    sources = sorted({str(candidate.get("source")) for candidate in _group_candidates(group) if candidate.get("source")})
    block["id"] = f"p{page_no:04d}-b{index:03d}"
    block["source_page"] = page_no
    block["schema_version"] = block.get("schema_version")
    block.pop("schema_version", None)
    evidence = block.setdefault("evidence", {})
    evidence["fusion"] = {
        "version": FUSION_VERSION,
        "group_id": group_id,
        "previous_block_id": old_id,
    }
    evidence["dual_parser"] = {
        "primary": "mineru",
        "secondary": "paddleocr",
        "primary_available": "mineru" in sources,
        "secondary_available": "paddleocr" in sources,
        "sources": sources,
    }


def _base_page(
    mineru_page: dict[str, Any] | None,
    paddleocr_page: dict[str, Any] | None,
    *,
    page_no: int,
    blocks: list[dict[str, Any]],
    engine_mode: str,
) -> dict[str, Any]:
    base = copy.deepcopy(mineru_page or paddleocr_page or {})
    base["schema_version"] = PAGE_IR_SCHEMA_VERSION
    base["source_page"] = page_no
    base["page_image_ref"] = _first_value((mineru_page or {}).get("page_image_ref"), (paddleocr_page or {}).get("page_image_ref"))
    base["blocks"] = blocks
    base["source_engine"] = "dual_fusion"
    base["parser_priority"] = ["mineru", "paddleocr"] if mineru_page else ["paddleocr"]
    base["engine_mode"] = engine_mode
    base["raw_text"] = _combined_raw_text(mineru_page, paddleocr_page)
    base["raw_text_sha256"] = sha256_text(base.get("raw_text") or "")
    return base


def _dual_evidence(mineru_page: dict[str, Any] | None, paddle_page: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "version": FUSION_VERSION,
        "mineru": _page_evidence(mineru_page, "mineru"),
        "paddleocr": _page_evidence(paddle_page, "paddleocr"),
    }


def _page_evidence(page: dict[str, Any] | None, source: str) -> dict[str, Any]:
    blocks = (page or {}).get("blocks") or []
    return {
        "available": page is not None,
        "raw_text": (page or {}).get("raw_text") or "",
        "block_count": len(blocks),
        "blocks": [
            {
                "id": block.get("id"),
                "type": block.get("type"),
                "text": _safe_text(_text_of(block), 360),
                "confidence": block.get("confidence"),
                "bbox": block.get("bbox"),
                "source_engine": source,
                "image_ref": _first_ref(block),
            }
            for block in blocks
        ],
    }


def _attach_figure_contexts(page_ir: dict[str, Any], *, document_type: str) -> None:
    for block in page_ir.get("blocks") or []:
        if block.get("type") not in {"figure_note", "image_ref", "table"}:
            continue
        evidence = block.setdefault("evidence", {})
        evidence["figure_context"] = build_figure_context_payload(page_ir, block, document_type=document_type)


def _source(mineru_ir: dict[str, Any], paddleocr_ir: dict[str, Any]) -> dict[str, Any]:
    return {
        "input_path": _first_value((mineru_ir.get("source") or {}).get("input_path"), (paddleocr_ir.get("source") or {}).get("input_path")),
        "input_hash": _first_value((mineru_ir.get("source") or {}).get("input_hash"), (paddleocr_ir.get("source") or {}).get("input_hash")),
        "input_type": _first_value((mineru_ir.get("source") or {}).get("input_type"), (paddleocr_ir.get("source") or {}).get("input_type")),
        "mineru_artifact_root": (mineru_ir.get("source") or {}).get("artifact_root"),
        "paddleocr_artifact_root": (paddleocr_ir.get("source") or {}).get("artifact_root"),
    }


def _namespaced_assets(document_ir: dict[str, Any], namespace: str) -> list[dict[str, Any]]:
    assets = []
    for index, asset in enumerate(document_ir.get("assets") or [], start=1):
        item = dict(asset)
        item["asset_id"] = f"{namespace}::{item.get('asset_id') or item.get('artifact_ref') or index}"
        item["source_engine"] = namespace
        assets.append(item)
    return assets


def _pages_by_no(document_ir: dict[str, Any]) -> dict[int, dict[str, Any]]:
    pages: dict[int, dict[str, Any]] = {}
    for index, page in enumerate(document_ir.get("pages") or [], start=1):
        try:
            page_no = int(page.get("source_page") or index)
        except (TypeError, ValueError):
            page_no = index
        pages[page_no] = page
    return pages


def _candidate_warnings(block: dict[str, Any], text: str) -> list[str]:
    warnings = []
    if contains_unicode_math_symbols(text):
        warnings.append("has_raw_unicode_math")
    if block.get("type") in {"formula_block", "formula_inline"}:
        quality = assess_formula_text(text)
        for warning in quality.warnings:
            warnings.append(warning.code)
    if block.get("type") == "table":
        quality = assess_table(text)
        if not quality.reliable:
            warnings.append("table_unreliable")
    if _has_uncertain_marker(text):
        warnings.append("uncertain_marker")
    if not text and not _first_ref(block):
        warnings.append("empty_candidate")
    return sorted(set(warnings))


def _candidate_quality_score(block: dict[str, Any], text: str, warnings: list[str]) -> float:
    score = _valid_confidence(block.get("confidence"), default=0.55)
    if block.get("type") == "formula_block" and text:
        score += 0.20
    elif block.get("type") == "formula_inline" and text:
        score += 0.06
        quality = assess_formula_text(text)
        score -= min(0.35, len(quality.warnings) * 0.08)
    if block.get("type") in {"figure_note", "image_ref"} and _first_ref(block):
        score += 0.14
    if block.get("type") == "table" and assess_table(text).reliable:
        score += 0.16
    if text:
        score += min(0.10, len(text) / 1200)
    if warnings:
        score -= min(0.45, len(warnings) * 0.09)
    return max(0.0, min(1.0, score))


def _best_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    score_best = max(candidates, key=lambda item: float(item.get("quality_score") or 0.0))
    richness_best = _richer_similar_candidate(candidates, score_best)
    return richness_best or score_best


def _best_formula_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    formula_candidates = [
        candidate
        for candidate in candidates
        if candidate.get("type") == "formula_block" and str(candidate.get("text") or "").strip()
    ]
    if not formula_candidates:
        return None
    return max(
        formula_candidates,
        key=lambda item: (
            -_severe_warning_count(item),
            float(item.get("quality_score") or 0.0),
            len(_normalize_match_text(item.get("text") or "")),
        ),
    )


def _best_uncertain_render_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not candidates:
        return None
    if _type_hint(candidates) == "formula_block":
        formula = _best_formula_candidate(candidates)
        if formula is not None:
            return formula
    text_candidates = [candidate for candidate in candidates if str(candidate.get("text") or "").strip()]
    if text_candidates:
        return _best_candidate(text_candidates)
    return _first_image_candidate(candidates) or _best_candidate(candidates)


def _audit_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "candidate_id": candidate.get("candidate_id"),
        "source": candidate.get("source"),
        "block_id": candidate.get("block_id"),
        "type": candidate.get("type"),
        "text": _safe_text(candidate.get("text"), 800),
        "image_ref": candidate.get("image_ref"),
        "quality_score": round(float(candidate.get("quality_score") or 0.0), 4),
        "confidence": candidate.get("confidence"),
        "warnings": candidate.get("warnings") or [],
    }


def _candidate_is_clearly_better(best: dict[str, Any], candidates: list[dict[str, Any]]) -> bool:
    others = [candidate for candidate in candidates if candidate is not best]
    if not others:
        return True
    return all(float(best.get("quality_score") or 0.0) >= float(candidate.get("quality_score") or 0.0) + 0.12 for candidate in others)


def _richer_similar_candidate(candidates: list[dict[str, Any]], score_best: dict[str, Any]) -> dict[str, Any] | None:
    text_candidates = [candidate for candidate in candidates if str(candidate.get("text") or "").strip()]
    if len(text_candidates) < 2:
        return None
    longest = max(text_candidates, key=lambda item: len(_normalize_match_text(item.get("text") or "")))
    shortest = min(text_candidates, key=lambda item: len(_normalize_match_text(item.get("text") or "")))
    longest_norm = _normalize_match_text(longest.get("text") or "")
    shortest_norm = _normalize_match_text(shortest.get("text") or "")
    if len(shortest_norm) < 16 or len(longest_norm) < len(shortest_norm) * 1.22:
        return None
    if _text_similarity(longest.get("text") or "", score_best.get("text") or "") < 0.52:
        return None
    if _severe_warning_count(longest) > _severe_warning_count(score_best):
        return None
    if float(longest.get("quality_score") or 0.0) + 0.24 < float(score_best.get("quality_score") or 0.0):
        return None
    return longest


def _severe_warning_count(candidate: dict[str, Any]) -> int:
    severe = {
        "has_raw_unicode_math",
        "formula_empty",
        "formula_uncertain_marker",
        "formula_truncated",
        "formula_isolated_operator",
        "formula_brace_unbalanced",
        "latex_left_right_unbalanced",
        "latex_frac_missing_braces",
        "table_unreliable",
        "empty_candidate",
    }
    return sum(1 for warning in candidate.get("warnings") or [] if warning in severe)


def _complementary_visual_text(candidates: list[dict[str, Any]]) -> bool:
    has_image = any(candidate.get("image_ref") and candidate.get("type") in {"image_ref", "figure_note", "table"} for candidate in candidates)
    has_text = any(candidate.get("text") and candidate.get("type") in {"paragraph", "figure_note", "heading"} for candidate in candidates)
    return has_image and has_text


def _text_conflict(candidates: list[dict[str, Any]]) -> bool:
    texts = [str(candidate.get("text") or "").strip() for candidate in candidates if str(candidate.get("text") or "").strip()]
    if len(texts) < 2:
        return False
    if min(len(text) for text in texts) < 8:
        return False
    return _text_similarity(texts[0], texts[1]) < 0.42


def _type_hint(candidates: list[dict[str, Any]]) -> str:
    types = [str(candidate.get("type") or "") for candidate in candidates if candidate.get("type")]
    if "formula_block" in types:
        return "formula_block"
    if "table" in types:
        return "table"
    if "figure_note" in types:
        return "figure_note"
    if "image_ref" in types:
        return "image_ref"
    return types[0] if types else "paragraph"


def _candidate_by_source(candidates: list[dict[str, Any]], source: Any) -> dict[str, Any] | None:
    source_text = str(source or "").strip()
    if not source_text:
        return None
    for candidate in candidates:
        if candidate.get("source") == source_text:
            return candidate
    return None


def _candidate_by_id(candidates: list[dict[str, Any]], candidate_id: Any) -> dict[str, Any] | None:
    wanted = str(candidate_id or "")
    if ":" in wanted:
        wanted = wanted.split(":", 1)[1]
    for candidate in candidates:
        if wanted in {str(candidate.get("candidate_id") or ""), str(candidate.get("block_id") or "")}:
            return candidate
    return None


def _first_image_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((candidate for candidate in candidates if candidate.get("image_ref")), None)


def _normalize_op(op: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(op)
    if "action" not in normalized and "op" in normalized:
        normalized["action"] = normalized.get("op")
    if normalized.get("action") == "choose":
        normalized["action"] = "choose_block"
    return normalized


def _rejected(op: dict[str, Any], group_id: str, reason: str, *, validation: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "group_id": group_id,
        "action": op.get("action") or op.get("op"),
        "status": "rejected",
        "reason": reason,
        "validation": validation,
    }


def _text_of(block: dict[str, Any]) -> str:
    return str(block.get("latex") or block.get("text") or block.get("description") or "").strip()


def _first_ref(block: dict[str, Any]) -> str | None:
    for key in ("crop_ref", "image_ref", "image_path", "path", "table_image_path", "formula_image_path", "page_image_ref"):
        value = str(block.get(key) or "").strip()
        if value:
            return value
    return None


def _text_similarity(left: str, right: str) -> float:
    left_norm = _normalize_match_text(left)
    right_norm = _normalize_match_text(right)
    if not left_norm or not right_norm:
        return 0.0
    if left_norm in right_norm or right_norm in left_norm:
        return min(len(left_norm), len(right_norm)) / max(len(left_norm), len(right_norm))
    return SequenceMatcher(None, left_norm, right_norm, autojunk=False).ratio()


def _normalize_match_text(text: str) -> str:
    text = re.sub(r"\s+", "", normalize_inline_math_text(text or "").lower())
    return re.sub(r"[^\w\\]+", "", text, flags=re.UNICODE)


def _bbox_overlap_score(left: Any, right: Any) -> float:
    if not _valid_bbox(left) or not _valid_bbox(right):
        return 0.0
    x0 = max(float(left[0]), float(right[0]))
    y0 = max(float(left[1]), float(right[1]))
    x1 = min(float(left[2]), float(right[2]))
    y1 = min(float(left[3]), float(right[3]))
    if x1 <= x0 or y1 <= y0:
        return 0.0
    inter = (x1 - x0) * (y1 - y0)
    area_left = abs((float(left[2]) - float(left[0])) * (float(left[3]) - float(left[1])))
    area_right = abs((float(right[2]) - float(right[0])) * (float(right[3]) - float(right[1])))
    denom = min(area_left, area_right) or max(area_left, area_right) or 1.0
    return max(0.0, min(1.0, inter / denom))


def _vertical_position_score(left: Any, right: Any) -> float:
    if not _valid_bbox(left) or not _valid_bbox(right):
        return 0.0
    left_center = (float(left[1]) + float(left[3])) / 2.0
    right_center = (float(right[1]) + float(right[3])) / 2.0
    height = max(abs(float(left[3]) - float(left[1])), abs(float(right[3]) - float(right[1])), 1.0)
    distance = abs(left_center - right_center) / height
    return max(0.0, 1.0 - min(distance, 1.0))


def _caption_image_score(left: dict[str, Any], right: dict[str, Any]) -> float:
    types = {left.get("type"), right.get("type")}
    if not (types & {"image_ref", "figure_note", "table"}):
        return 0.0
    texts = f"{left.get('text') or ''} {right.get('text') or ''}"
    if not re.search(r"(图|figure|caption|表|table)", texts, flags=re.IGNORECASE):
        return 0.0
    return _vertical_position_score(left.get("bbox"), right.get("bbox")) * 0.82


def _types_compatible(left: Any, right: Any) -> bool:
    pair = {str(left or ""), str(right or "")}
    compatible = [
        {"paragraph", "formula_inline"},
        {"paragraph", "formula_block"},
        {"image_ref", "figure_note"},
        {"table", "figure_note"},
        {"heading", "paragraph"},
    ]
    return any(pair <= item for item in compatible)


def _union_bbox(values: list[Any]) -> list[float] | None:
    boxes = [value for value in values if _valid_bbox(value)]
    if not boxes:
        return None
    return [
        min(float(value[0]) for value in boxes),
        min(float(value[1]) for value in boxes),
        max(float(value[2]) for value in boxes),
        max(float(value[3]) for value in boxes),
    ]


def _valid_bbox(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 4 and all(isinstance(item, (int, float)) for item in value)


def _confidence(block: dict[str, Any]) -> float:
    return _valid_confidence(block.get("confidence"), default=0.55)


def _valid_confidence(value: Any, *, default: float) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, score))


def _update_formula_fields(block: dict[str, Any], text: str) -> None:
    quality = assess_formula_text(text)
    block["text"] = quality.latex
    block["latex"] = quality.latex
    block["raw_text"] = text
    block["formula_quality"] = quality.to_dict()
    block["warnings"] = [warning.to_dict() for warning in quality.warnings]


def _update_table_fields(block: dict[str, Any], text: str) -> None:
    quality = assess_table(text)
    block["table_format"] = quality.table_format if quality.reliable else "uncertain"
    block["table_reliable"] = quality.reliable
    block["table_render_mode"] = "normalized_markdown" if quality.reliable else "degraded_warning"
    block["table_quality"] = quality.to_dict()


def _origin_for_type(block_type: Any) -> str:
    if block_type in {"formula_block", "formula_inline"}:
        return "vision_formula"
    if block_type == "table":
        return "vision_table"
    if block_type in {"figure_note", "image_ref"}:
        return "vision_description"
    if block_type == "uncertain":
        return "vision_uncertain"
    return "vision_ocr"


def _allowed_block_types() -> set[str]:
    return {"heading", "paragraph", "list", "formula_inline", "formula_block", "figure_note", "table", "image_ref", "uncertain"}


def _combined_raw_text(mineru_page: dict[str, Any] | None, paddle_page: dict[str, Any] | None) -> str:
    mineru_text = ((mineru_page or {}).get("raw_text") or "").strip()
    paddle_text = ((paddle_page or {}).get("raw_text") or "").strip()
    if mineru_text and paddle_text:
        return f"[MinerU]\n{mineru_text}\n\n[PaddleOCR]\n{paddle_text}"
    return mineru_text or paddle_text


def _first_value(*values):
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _safe_text(value: Any, limit: int = 500) -> str:
    text = str(value or "").strip()
    text = re.sub(r"reasoning_content\s*[:=]\s*.*$", "reasoning_content omitted.", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"Traceback\s*\(most recent call last\).*", "Traceback omitted.", text, flags=re.IGNORECASE | re.DOTALL)
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _safe_model_text(value: Any) -> str:
    text = str(value or "").strip()
    if not text or is_api_error_text(text):
        return ""
    if re.search(r"(reasoning_content|Traceback|思考过程|推理过程)", text, flags=re.IGNORECASE):
        return ""
    if re.search(r"(?im)^\s*\[(?:mineru|paddleocr)\]\s+", text):
        return ""
    return text


def _has_uncertain_marker(text: str) -> bool:
    lower = (text or "").lower()
    return (
        "[?]" in text
        or "？" in text
        or "无法确定" in text
        or "看不清" in text
        or "不确定" in text
        or "uncertain" in lower
        or "illegible" in lower
    )
