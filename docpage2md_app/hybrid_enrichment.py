import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Dict, Iterable

from .artifacts import sha256_text
from .config import AppConfig
from .env import get_env_value
from .figures import analyze_figure_description
from .formula_quality import assess_formula_text
from .models import (
    _run_dashscope_brain,
    _run_deepseek_brain,
    _run_openai_compatible_brain,
    call_aliyun_openai_vision,
)
from .refiner import BLOCK_KNOWN_OPS, BLOCK_REFINER_VERSION, apply_block_op_checked, refine_page_ir
from .run_logger import ProgressCallback, safe_progress
from .table_quality import assess_table
from .validators import first_api_error_prefix, is_api_error_text


HYBRID_ENRICHMENT_VERSION = "hybrid-enrichment-2026-06-23-v1"

VisionBackend = Callable[[dict[str, Any], dict[str, Any], Path | None, AppConfig], dict[str, Any]]
BrainBackend = Callable[[dict[str, Any], list[dict[str, Any]], AppConfig], dict[str, Any]]

VISION_ENRICH_BLOCK_TYPES = {"figure_note", "image_ref", "table", "formula_block"}


def enrich_mineru_document_ir(
    document_ir: dict[str, Any],
    config: AppConfig,
    *,
    output_root: str | Path,
    vision_backend: VisionBackend | None = None,
    brain_backend: BrainBackend | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    """Enrich MinerU IR with crop vision, structured Brain ops, and checked refiner ops.

    The function is deliberately offline-testable: tests can inject mock backends.
    In production, missing API keys cause fail-open reports and keep the MinerU IR.
    """
    enriched = deepcopy(document_ir)
    output_root = Path(output_root)
    vision_backend = vision_backend or default_crop_vision_backend
    brain_backend = brain_backend or default_brain_backend

    pages = enriched.get("pages") or []
    safe_progress(
        progress,
        (
            f"Hybrid enrichment workers: pages={len(pages)}, "
            f"vision={config.vision_batch_workers}, brain={config.brain_batch_workers}"
        ),
    )
    vision_reports = _run_document_crop_vision_enrichment(
        pages,
        config,
        output_root,
        vision_backend,
        progress=progress,
    )
    context_pages = deepcopy(pages)
    brain_reports = _run_document_brain_refinement(
        pages,
        context_pages,
        config,
        brain_backend,
        progress=progress,
    )

    page_results: dict[int, dict[str, Any]] = {}
    for page_index, page_ir in enumerate(pages):
        slide_no = int(page_ir.get("source_page") or page_index + 1)
        page_brain = brain_reports[slide_no]
        op_audit = list((page_brain["brain"] or {}).get("op_audit") or []) + list(
            (page_brain["block_refiner"] or {}).get("op_audit") or []
        )
        page_results[slide_no] = {
            "version": HYBRID_ENRICHMENT_VERSION,
            "vision": vision_reports[slide_no],
            "brain": page_brain["brain"],
            "block_refiner": page_brain["block_refiner"],
            "op_audit": op_audit,
        }

    metadata = enriched.setdefault("metadata", {})
    metadata["hybrid_enrichment"] = {
        "version": HYBRID_ENRICHMENT_VERSION,
        "pages": _enrichment_summary(page_results.values()),
    }
    return {"document_ir": enriched, "pages": page_results, "summary": metadata["hybrid_enrichment"]}


def _run_document_crop_vision_enrichment(
    pages: list[dict[str, Any]],
    config: AppConfig,
    output_root: Path,
    vision_backend: VisionBackend,
    *,
    progress: ProgressCallback | None = None,
) -> dict[int, dict[str, Any]]:
    reports_by_slide: dict[int, dict[str, Any]] = {}
    jobs: list[tuple[int, dict[str, Any], dict[str, Any], Path]] = []
    for page_index, page_ir in enumerate(pages):
        slide_no = int(page_ir.get("source_page") or page_index + 1)
        safe_progress(
            progress,
            f"Hybrid page {page_index + 1}/{len(pages)} start: slide={slide_no}, blocks={len(page_ir.get('blocks') or [])}",
        )
        reports_by_slide[slide_no] = _empty_vision_report()
        for block in page_ir.get("blocks") or []:
            if block.get("type") not in VISION_ENRICH_BLOCK_TYPES:
                continue
            image_path = _resolve_block_image_path(block, output_root)
            if image_path is None:
                continue
            jobs.append((slide_no, page_ir, block, image_path))

    if not jobs:
        return reports_by_slide

    workers = _worker_count(config.vision_batch_workers, len(jobs))
    safe_progress(progress, f"Hybrid crop vision batch start: blocks={len(jobs)}, workers={workers}")
    started = time.monotonic()
    results_by_slide: dict[int, list[dict[str, Any]]] = {slide_no: [] for slide_no in reports_by_slide}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_run_single_crop_vision_job, slide_no, page_ir, block, image_path, config, vision_backend, progress): slide_no
            for slide_no, page_ir, block, image_path in jobs
        }
        for future in as_completed(futures):
            slide_no = futures[future]
            try:
                results_by_slide.setdefault(slide_no, []).append(future.result())
            except Exception as exc:
                safe_progress(progress, f"Crop vision failed: slide={slide_no}, block=<thread>, code=vision_thread_exception")
                results_by_slide.setdefault(slide_no, []).append(
                    {
                        "block_id": None,
                        "type": None,
                        "status": "failed",
                        "error_code": "vision_thread_exception",
                        "error_message": _safe_model_error(str(exc)),
                    }
                )

    for slide_no, block_results in results_by_slide.items():
        reports_by_slide[slide_no] = _vision_report_from_results(block_results)
        report = reports_by_slide[slide_no]
        safe_progress(
            progress,
            (
                f"Hybrid page {slide_no} crop vision: status={report.get('status')}, "
                f"attempted={report.get('attempted_blocks')}, "
                f"succeeded={report.get('succeeded_blocks')}, failed={report.get('failed_blocks')}"
            ),
        )
    elapsed = time.monotonic() - started
    attempted = sum(report.get("attempted_blocks") or 0 for report in reports_by_slide.values())
    succeeded = sum(report.get("succeeded_blocks") or 0 for report in reports_by_slide.values())
    failed = sum(report.get("failed_blocks") or 0 for report in reports_by_slide.values())
    safe_progress(
        progress,
        f"Hybrid crop vision batch done: blocks={attempted}, succeeded={succeeded}, failed={failed}, elapsed={elapsed:.1f}s",
    )
    return reports_by_slide


def _run_single_crop_vision_job(
    slide_no: int,
    page_ir: dict[str, Any],
    block: dict[str, Any],
    image_path: Path,
    config: AppConfig,
    vision_backend: VisionBackend,
    progress: ProgressCallback | None,
) -> dict[str, Any]:
    safe_progress(progress, f"Crop vision start: slide={slide_no}, block={block.get('id')}, type={block.get('type')}")
    response = vision_backend(page_ir, block, image_path, config)
    normalized = _normalize_backend_response(response)
    if normalized.get("success"):
        changed_fields = _apply_vision_result(block, normalized)
        safe_progress(
            progress,
            f"Crop vision ok: slide={slide_no}, block={block.get('id')}, changed={','.join(changed_fields) or 'none'}",
        )
        return {
            "block_id": block.get("id"),
            "type": block.get("type"),
            "status": "ok",
            "changed_fields": changed_fields,
            "content_sha256": _response_content_sha256(normalized),
            **_provider_fields(normalized),
        }

    safe_progress(progress, f"Crop vision failed: slide={slide_no}, block={block.get('id')}, code={normalized.get('error_code')}")
    return {
        "block_id": block.get("id"),
        "type": block.get("type"),
        "status": "failed",
        "error_code": normalized.get("error_code"),
        "error_message": _safe_model_error(normalized.get("error_message") or "Vision enrichment failed."),
        **_provider_fields(normalized),
    }


def _run_document_brain_refinement(
    pages: list[dict[str, Any]],
    context_pages: list[dict[str, Any]],
    config: AppConfig,
    brain_backend: BrainBackend,
    *,
    progress: ProgressCallback | None = None,
) -> dict[int, dict[str, Any]]:
    if not pages:
        return {}
    workers = _worker_count(config.brain_batch_workers, len(pages))
    safe_progress(progress, f"Hybrid Brain batch start: pages={len(pages)}, workers={workers}")
    started = time.monotonic()
    reports_by_slide: dict[int, dict[str, Any]] = {}
    page_jobs = []
    for page_index, page_ir in enumerate(pages):
        slide_no = int(page_ir.get("source_page") or page_index + 1)
        page_jobs.append((page_index, slide_no, page_ir))

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(
                _run_single_brain_refinement_job,
                page_index,
                slide_no,
                deepcopy(page_ir),
                context_pages,
                config,
                brain_backend,
                progress,
            ): (page_index, slide_no)
            for page_index, slide_no, page_ir in page_jobs
        }
        for future in as_completed(futures):
            page_index, slide_no = futures[future]
            try:
                refined_page, report = future.result()
            except Exception as exc:
                safe_progress(progress, f"Hybrid page {slide_no} Brain failed: code=brain_thread_exception, error={_safe_model_error(str(exc))}")
                refined_page = pages[page_index]
                brain_report = {
                    "version": HYBRID_ENRICHMENT_VERSION,
                    "status": "failed",
                    "ops_requested": 0,
                    "ops_applied": 0,
                    "ops_rejected": 0,
                    "warnings": [],
                    "op_audit": [],
                    "error_code": "brain_thread_exception",
                    "error_message": _safe_model_error(str(exc)),
                }
                block_refiner = {
                    "changed": False,
                    "applied_ops": [],
                    "dismissed": [],
                    "validation": {},
                    "op_audit": [],
                }
                report = {"brain": brain_report, "block_refiner": block_refiner}
            pages[page_index] = refined_page
            reports_by_slide[slide_no] = report
    elapsed = time.monotonic() - started
    statuses = {}
    for report in reports_by_slide.values():
        status = ((report.get("brain") or {}).get("status") or "unknown")
        statuses[status] = statuses.get(status, 0) + 1
    status_text = ";".join(f"{key}:{value}" for key, value in sorted(statuses.items())) or "none"
    safe_progress(progress, f"Hybrid Brain batch done: pages={len(pages)}, statuses={status_text}, elapsed={elapsed:.1f}s")
    return reports_by_slide


def _run_single_brain_refinement_job(
    page_index: int,
    slide_no: int,
    page_ir: dict[str, Any],
    pages: list[dict[str, Any]],
    config: AppConfig,
    brain_backend: BrainBackend,
    progress: ProgressCallback | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    context_window = _context_window(pages, page_index)
    safe_progress(progress, f"Hybrid page {slide_no} Brain start: context_pages={len(context_window)}")
    page_after_brain, brain_report = _run_brain_ops(page_ir, context_window, config, brain_backend)
    safe_progress(
        progress,
        (
            f"Hybrid page {slide_no} Brain done: status={brain_report.get('status')}, "
            f"ops_requested={brain_report.get('ops_requested')}, "
            f"applied={brain_report.get('ops_applied')}, rejected={brain_report.get('ops_rejected')}"
        ),
    )

    block_refine_result = refine_page_ir(
        page_after_brain,
        slide_no=slide_no,
        target_raw=page_after_brain.get("raw_text"),
    )
    safe_progress(
        progress,
        (
            f"Hybrid page {slide_no} refiner done: changed={block_refine_result.changed}, "
            f"applied={len(block_refine_result.applied_ops)}, dismissed={len(block_refine_result.dismissed)}"
        ),
    )
    return block_refine_result.page_ir, {
        "brain": brain_report,
        "block_refiner": block_refine_result.to_dict(),
    }


def _empty_vision_report() -> dict[str, Any]:
    return {
        "version": HYBRID_ENRICHMENT_VERSION,
        "status": "skipped",
        "attempted_blocks": 0,
        "succeeded_blocks": 0,
        "failed_blocks": 0,
        "blocks": [],
        "usage": None,
        "request_id": None,
        "provider_latency": None,
    }


def _vision_report_from_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    attempted = len(results)
    succeeded = sum(1 for item in results if item.get("status") == "ok")
    failed = attempted - succeeded
    return {
        "version": HYBRID_ENRICHMENT_VERSION,
        "status": _stage_status(attempted, succeeded, failed),
        "attempted_blocks": attempted,
        "succeeded_blocks": succeeded,
        "failed_blocks": failed,
        "blocks": results,
        "usage": _aggregate_usage(results),
        "request_id": _first_value(results, "request_id"),
        "provider_latency": _sum_provider_latency(results),
    }


def _worker_count(configured: int, jobs: int) -> int:
    try:
        workers = int(configured)
    except (TypeError, ValueError):
        workers = 1
    return max(1, min(max(1, jobs), workers if workers > 0 else 1))


def default_crop_vision_backend(
    page_ir: dict[str, Any],
    block: dict[str, Any],
    image_path: Path | None,
    config: AppConfig,
) -> dict[str, Any]:
    if image_path is None or not image_path.exists():
        return _backend_error("missing_crop_image", "Crop image is not available.")
    api_key = get_env_value(config.vision_api_key_env)
    if not api_key:
        return _backend_error("missing_api_key", f"Missing API key env: {config.vision_api_key_env}.")
    if config.vision_provider not in {"dashscope", "dashscope_openai", "openai_compatible"}:
        return _backend_error("unsupported_vision_provider", f"Unsupported vision provider: {config.vision_provider}.")

    payload = _model_payload(
        call_aliyun_openai_vision(
            model_id=config.model_vision,
            image_path=str(image_path),
            prompt_text=_crop_vision_prompt(block),
            api_key=api_key,
            base_url=config.vision_base_url,
            stream=True,
        )
    )
    content = payload["content"].strip()
    if is_api_error_text(content) or content.startswith("OpenAI"):
        return _backend_error(first_api_error_prefix(content) or "vision_api_error", _safe_model_error(content), payload)
    if not content:
        return _backend_error("empty_vision_output", "Vision model returned no content.", payload)

    parsed = _parse_json_object(content) or {"content": content}
    return {"success": True, **parsed, **_provider_fields(payload)}


def default_brain_backend(
    page_ir: dict[str, Any],
    context_pages: list[dict[str, Any]],
    config: AppConfig,
) -> dict[str, Any]:
    if not get_env_value(config.brain_api_key_env):
        return _backend_error("missing_api_key", f"Missing API key env: {config.brain_api_key_env}.")

    prompt = _brain_ops_prompt(page_ir, context_pages)
    last_error = None
    for attempt in range(2):
        raw = _call_brain_model(prompt, config)
        payload = _model_payload(raw)
        content = payload["content"].strip()
        if is_api_error_text(content):
            return _backend_error(first_api_error_prefix(content) or "brain_api_error", _safe_model_error(content), payload)
        if not content:
            last_error = _backend_error("empty_brain_output", "Brain model returned no JSON content.", payload)
            continue

        parsed = _parse_json_object(content)
        if not isinstance(parsed, dict):
            last_error = _backend_error("invalid_brain_json", "Brain output was not valid JSON.", payload)
            continue
        ops = parsed.get("ops") or parsed.get("operations") or []
        if not isinstance(ops, list):
            return _backend_error("invalid_brain_ops", "Brain JSON field 'ops' must be a list.", payload)
        return {
            "success": True,
            "ops": [op for op in ops if isinstance(op, dict)],
            "warnings": parsed.get("warnings") if isinstance(parsed.get("warnings"), list) else [],
            "retry_count": attempt,
            **_provider_fields(payload),
        }
    if last_error is not None:
        last_error["retry_count"] = 1
        return last_error
    return _backend_error("empty_brain_output", "Brain model returned no JSON content.")


def _call_brain_model(prompt: str, config: AppConfig):
    if config.brain_provider == "deepseek":
        return _run_deepseek_brain(prompt, config)
    if config.brain_provider in {"dashscope_openai", "openai_compatible"}:
        return _run_openai_compatible_brain(prompt, config)
    return _run_dashscope_brain(prompt, config)


def _run_crop_vision_enrichment(
    page_ir: dict[str, Any],
    config: AppConfig,
    output_root: Path,
    vision_backend: VisionBackend,
    *,
    progress: ProgressCallback | None = None,
    slide_no: int | None = None,
) -> dict[str, Any]:
    blocks = page_ir.get("blocks") or []
    results = []
    attempted = 0
    succeeded = 0
    failed = 0
    for block in blocks:
        if block.get("type") not in VISION_ENRICH_BLOCK_TYPES:
            continue
        image_path = _resolve_block_image_path(block, output_root)
        if image_path is None:
            continue
        attempted += 1
        safe_progress(
            progress,
            f"Crop vision start: slide={slide_no or page_ir.get('source_page')}, block={block.get('id')}, type={block.get('type')}",
        )
        response = vision_backend(page_ir, block, image_path, config)
        normalized = _normalize_backend_response(response)
        if normalized.get("success"):
            changed_fields = _apply_vision_result(block, normalized)
            succeeded += 1
            safe_progress(
                progress,
                (
                    f"Crop vision ok: slide={slide_no or page_ir.get('source_page')}, "
                    f"block={block.get('id')}, changed={','.join(changed_fields) or 'none'}"
                ),
            )
            results.append(
                {
                    "block_id": block.get("id"),
                    "type": block.get("type"),
                    "status": "ok",
                    "changed_fields": changed_fields,
                    "content_sha256": _response_content_sha256(normalized),
                    **_provider_fields(normalized),
                }
            )
        else:
            failed += 1
            safe_progress(
                progress,
                (
                    f"Crop vision failed: slide={slide_no or page_ir.get('source_page')}, "
                    f"block={block.get('id')}, code={normalized.get('error_code')}"
                ),
            )
            results.append(
                {
                    "block_id": block.get("id"),
                    "type": block.get("type"),
                    "status": "failed",
                    "error_code": normalized.get("error_code"),
                    "error_message": _safe_model_error(normalized.get("error_message") or "Vision enrichment failed."),
                    **_provider_fields(normalized),
                }
            )
    return {
        "version": HYBRID_ENRICHMENT_VERSION,
        "status": _stage_status(attempted, succeeded, failed),
        "attempted_blocks": attempted,
        "succeeded_blocks": succeeded,
        "failed_blocks": failed,
        "blocks": results,
        "usage": _aggregate_usage(results),
        "request_id": _first_value(results, "request_id"),
        "provider_latency": _sum_provider_latency(results),
    }


def _run_brain_ops(
    page_ir: dict[str, Any],
    context_pages: list[dict[str, Any]],
    config: AppConfig,
    brain_backend: BrainBackend,
) -> tuple[dict[str, Any], dict[str, Any]]:
    response = _normalize_backend_response(brain_backend(page_ir, context_pages, config))
    if not response.get("success"):
        return page_ir, {
            "version": HYBRID_ENRICHMENT_VERSION,
            "status": "failed",
            "ops_requested": 0,
            "ops_applied": 0,
            "ops_rejected": 0,
            "warnings": [],
            "op_audit": [],
            "error_code": response.get("error_code"),
            "error_message": _safe_model_error(response.get("error_message") or "Brain enrichment failed."),
            **_provider_fields(response),
        }

    current = page_ir
    audits = []
    ops = [op for op in response.get("ops") or [] if isinstance(op, dict)]
    applied = 0
    rejected = 0
    slide_no = int(page_ir.get("source_page") or 0)
    for op in ops:
        if op.get("op") not in BLOCK_KNOWN_OPS:
            rejected += 1
            audits.append(_brain_op_audit(op, "rejected", {"reason": "unknown_or_unsafe_op"}))
            continue
        current, ok, detail = apply_block_op_checked(
            current,
            op,
            slide_no=slide_no,
            target_raw=page_ir.get("raw_text"),
        )
        if ok:
            applied += 1
            audits.append(_brain_op_audit(op, "applied", detail))
        else:
            rejected += 1
            audits.append(_brain_op_audit(op, "rejected", detail))

    return current, {
        "version": HYBRID_ENRICHMENT_VERSION,
        "status": "ok" if rejected == 0 else "partial",
        "ops_requested": len(ops),
        "ops_applied": applied,
        "ops_rejected": rejected,
        "warnings": response.get("warnings") if isinstance(response.get("warnings"), list) else [],
        "op_audit": audits,
        **_provider_fields(response),
    }


def _apply_vision_result(block: dict[str, Any], result: dict[str, Any]) -> list[str]:
    changed = []
    block_type = block.get("type")
    evidence = block.setdefault("evidence", {})
    evidence["vision_enrichment"] = {
        "version": HYBRID_ENRICHMENT_VERSION,
        "content_sha256": _response_content_sha256(result),
        "model_request_id": result.get("request_id"),
    }

    if block_type in {"figure_note", "image_ref"}:
        description = _first_text(result, "description", "vision_summary", "content", "text")
        if description:
            if block.get("type") == "image_ref":
                block["type"] = "figure_note"
                changed.append("type")
            block["description"] = description
            block["text"] = description
            figure = block.setdefault("figure", {})
            figure["vision_summary"] = description
            for key in ("figure_type", "labels", "relations", "linked_blocks", "uncertainties"):
                if key in result and result.get(key) not in (None, ""):
                    if key == "figure_type":
                        block["figure_type"] = result[key]
                    else:
                        block[key] = result[key]
                    figure[key] = result[key]
            analysis = analyze_figure_description(description)
            fields = analysis.to_block_fields()
            figure.update({key: value for key, value in fields.get("figure", {}).items() if key not in figure or not figure[key]})
            changed.append("description")
        block["origin"] = "vision_description"
        block["source_engine"] = "vision"

    elif block_type == "formula_block":
        latex = _first_text(result, "latex", "formula", "content", "text")
        if latex:
            quality = assess_formula_text(latex)
            block["text"] = quality.latex
            block["latex"] = quality.latex
            block["raw_text"] = result.get("raw_text") or latex
            block["formula_quality"] = quality.to_dict()
            block["warnings"] = [warning.to_dict() for warning in quality.warnings]
            block["origin"] = "vision_formula"
            block["source_engine"] = "vision"
            changed.extend(["text", "latex", "formula_quality"])

    elif block_type == "table":
        table_text = _first_text(result, "markdown", "table_markdown", "raw_text", "content", "text")
        if table_text:
            quality = assess_table(table_text)
            block["text"] = quality.normalized_markdown or table_text
            block["raw_text"] = table_text
            block["table_format"] = quality.table_format if quality.reliable else "uncertain"
            block["table_reliable"] = quality.reliable
            block["table_render_mode"] = "normalized_markdown" if quality.reliable else "degraded_warning"
            block["degrade_reason_codes"] = [issue.code for issue in quality.errors + quality.warnings] if not quality.reliable else []
            block["rows"] = quality.row_count
            block["columns"] = quality.column_counts
            block["table_quality"] = quality.to_dict()
            block["origin"] = "vision_table"
            block["source_engine"] = "vision"
            changed.extend(["text", "table_quality"])

    return sorted(set(changed))


def _brain_op_audit(op: dict[str, Any], status: str, detail: dict[str, Any]) -> dict[str, Any]:
    return {
        "op": op.get("op"),
        "target_block_ids": _op_target_block_ids(op),
        "before_block_ids": detail.get("before_block_ids", []),
        "after_block_ids": detail.get("after_block_ids", []),
        "before_blocks": detail.get("before_blocks", []),
        "after_blocks": detail.get("after_blocks", []),
        "before_text_sha256": detail.get("before_text_sha256"),
        "after_text_sha256": detail.get("after_text_sha256"),
        "removed_spans": detail.get("removed_spans", []),
        "removed_text_hashes": detail.get("removed_text_hashes", []),
        "created_block_ids": detail.get("created_block_ids", []),
        "degraded": bool(detail.get("degraded") or op.get("op") == "mark_uncertain"),
        "reason": detail.get("reason") or op.get("reason"),
        "status": status,
        "validator_before": detail.get("validator_before"),
        "validator_after": detail.get("validator_after") or detail.get("validation"),
    }


def _op_target_block_ids(op: dict[str, Any]) -> list[str]:
    ids = []
    for key in ("id", "a", "b", "table_id", "title_block_id", "caption_block_id"):
        value = op.get(key)
        if value and value not in ids:
            ids.append(str(value))
    value = op.get("target_block_ids")
    if isinstance(value, list):
        for item in value:
            if item and str(item) not in ids:
                ids.append(str(item))
    return ids


def _resolve_block_image_path(block: dict[str, Any], output_root: Path) -> Path | None:
    for key in ("crop_ref", "image_ref", "table_image_path", "formula_image_path", "path", "image_path"):
        value = str(block.get(key) or "").strip()
        if not value:
            continue
        path = Path(value)
        if not path.is_absolute():
            path = output_root / path
        return path
    return None


def _context_window(pages: list[dict[str, Any]], page_index: int, radius: int = 2) -> list[dict[str, Any]]:
    start = max(0, page_index - radius)
    end = min(len(pages), page_index + radius + 1)
    return [pages[index] for index in range(start, end)]


def _crop_vision_prompt(block: dict[str, Any]) -> str:
    block_type = block.get("type")
    if block_type in {"figure_note", "image_ref"}:
        task = "识别这个图示或手绘图。返回图类型、可见标签、主要关系、与正文或公式的可能关联、不确定点。"
    elif block_type == "table":
        task = "识别这个表格。优先返回可靠 Markdown 表格；如果结构不可靠，返回 raw_text 并说明不确定。"
    elif block_type == "formula_block":
        task = "识别这个公式裁剪图。返回可渲染 LaTeX，不要把 \\tag{} 放进 aligned 环境内部。"
    else:
        task = "识别这个文档裁剪块。"
    return (
        f"{task}\n"
        "只返回 JSON，不要返回思考过程，不要返回 Markdown 代码围栏。可用字段："
        "description, figure_type, labels, relations, uncertainties, latex, markdown, raw_text, warnings。"
    )


def _brain_ops_prompt(page_ir: dict[str, Any], context_pages: list[dict[str, Any]]) -> str:
    page_no = int(page_ir.get("source_page") or 0)
    context = [_brain_context_page(page, target_page_no=page_no) for page in context_pages]
    return (
        "你是 DocPage2MD 的 Brain 纠错器。只能输出 JSON，不得输出 Markdown，不得输出思考过程。\n"
        "任务：结合前后页上下文，修正明显 OCR/LaTeX 识别错误。不要自由重写整页，不要删除大段内容。\n"
        "公式和数学符号必须使用 LaTeX；即使符号混在 paragraph/text block 中，也要改成 $...$ 内的 \\phi、\\theta、\\omega 等命令，不能保留裸 φ、θ、ω。\n"
        "允许 ops：replace_text_span_checked, normalize_formula, mark_uncertain, merge_block, promote_heading, demote_heading。\n"
        "replace_text_span_checked 格式："
        '{"op":"replace_text_span_checked","id":"p0001-b001","old_text":"...","new_text":"...","field":"text","reason":"..."}\n'
        f"当前页：{page_no}\n"
        f"上下文 JSON：{json.dumps(context, ensure_ascii=False)}\n"
        '返回格式：{"ops":[],"warnings":[]}'
    )


def _brain_context_page(page: dict[str, Any], *, target_page_no: int) -> dict[str, Any]:
    page_no = int(page.get("source_page") or 0)
    is_target = page_no == target_page_no
    block_limit = 80 if is_target else 32
    raw_limit = 1600 if is_target else 360
    text_limit = 420 if is_target else 120
    return {
        "page": page.get("source_page"),
        "role": "target" if is_target else "neighbor",
        "raw_text": _truncate(page.get("raw_text") or "", raw_limit),
        "blocks": [
            {
                "id": block.get("id"),
                "type": block.get("type"),
                "text": _truncate(block.get("latex") or block.get("text") or block.get("description") or "", text_limit),
            }
            for block in (page.get("blocks") or [])[:block_limit]
            if _brain_context_block_text(block)
        ],
    }


def _brain_context_block_text(block: dict[str, Any]) -> str:
    return str(block.get("latex") or block.get("text") or block.get("description") or "").strip()


def _parse_json_object(text: str) -> dict[str, Any] | None:
    stripped = (text or "").strip()
    if not stripped:
        return None
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        stripped = fence.group(1).strip()
    try:
        value = json.loads(stripped)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start >= 0 and end > start:
        try:
            value = json.loads(stripped[start : end + 1])
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _model_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {
            "content": str(value.get("content") or ""),
            "reasoning": str(value.get("reasoning") or value.get("reasoning_content") or ""),
            "usage": value.get("usage"),
            "request_id": value.get("request_id"),
            "provider_latency": value.get("provider_latency"),
        }
    if isinstance(value, tuple):
        return {
            "content": str(value[0] if len(value) > 0 else ""),
            "reasoning": str(value[1] if len(value) > 1 else ""),
            "usage": value[2] if len(value) > 2 else None,
            "request_id": value[3] if len(value) > 3 else None,
            "provider_latency": value[4] if len(value) > 4 else None,
        }
    return {"content": str(value or ""), "reasoning": "", "usage": None, "request_id": None, "provider_latency": None}


def _normalize_backend_response(response: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(response, dict):
        return _backend_error("invalid_backend_response", "Backend did not return a dict.")
    if response.get("success") is True:
        return response
    if response.get("success") is False:
        return response
    if "ops" in response or any(key in response for key in ("description", "latex", "markdown", "content")):
        response["success"] = True
        return response
    return _backend_error("invalid_backend_response", "Backend response lacked success/content fields.", response)


def _backend_error(code: str, message: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload or {}
    return {
        "success": False,
        "error_code": code,
        "error_message": _safe_model_error(message),
        **_provider_fields(payload),
    }


def _provider_fields(source: dict[str, Any]) -> dict[str, Any]:
    return {
        "usage": source.get("usage"),
        "request_id": source.get("request_id"),
        "provider_latency": source.get("provider_latency"),
    }


def _safe_model_error(message: Any) -> str:
    text = str(message or "")
    text = re.sub(r"Trace:\s*.*$", "Trace omitted.", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"reasoning_content\s*[:=]\s*.*$", "reasoning_content omitted.", text, flags=re.DOTALL | re.IGNORECASE)
    return _truncate(text.strip(), 300)


def _first_text(source: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = source.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _response_content_sha256(source: dict[str, Any]) -> str | None:
    content = _first_text(source, "description", "vision_summary", "latex", "markdown", "table_markdown", "raw_text", "content", "text")
    return sha256_text(content) if content else None


def _stage_status(attempted: int, succeeded: int, failed: int) -> str:
    if attempted == 0:
        return "skipped"
    if succeeded and not failed:
        return "ok"
    if succeeded and failed:
        return "partial"
    return "failed"


def _aggregate_usage(items: Iterable[dict[str, Any]]) -> dict[str, int] | None:
    total_prompt = 0
    total_completion = 0
    total = 0
    seen = False
    for item in items:
        usage = item.get("usage")
        if not isinstance(usage, dict):
            continue
        prompt = _first_int(usage, "input_tokens", "prompt_tokens", "promptTokenCount")
        completion = _first_int(usage, "output_tokens", "completion_tokens", "completionTokenCount")
        usage_total = _first_int(usage, "total_tokens", "totalTokenCount")
        if prompt is None and completion is None and usage_total is None:
            continue
        seen = True
        total_prompt += int(prompt or 0)
        total_completion += int(completion or 0)
        total += int(usage_total if usage_total is not None else int(prompt or 0) + int(completion or 0))
    if not seen:
        return None
    return {"prompt_tokens": total_prompt, "completion_tokens": total_completion, "total_tokens": total}


def _first_int(source: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = source.get(key)
        if value is None:
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _first_value(items: Iterable[dict[str, Any]], key: str):
    for item in items:
        value = item.get(key)
        if value:
            return value
    return None


def _sum_provider_latency(items: Iterable[dict[str, Any]]) -> float | None:
    total = 0.0
    seen = False
    for item in items:
        value = item.get("provider_latency")
        if value is None:
            continue
        try:
            total += float(value)
            seen = True
        except (TypeError, ValueError):
            continue
    return round(total, 3) if seen else None


def _enrichment_summary(page_results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    results = list(page_results)
    return {
        "page_count": len(results),
        "vision_attempted_blocks": sum(int((item.get("vision") or {}).get("attempted_blocks") or 0) for item in results),
        "vision_succeeded_blocks": sum(int((item.get("vision") or {}).get("succeeded_blocks") or 0) for item in results),
        "brain_ops_requested": sum(int((item.get("brain") or {}).get("ops_requested") or 0) for item in results),
        "brain_ops_applied": sum(int((item.get("brain") or {}).get("ops_applied") or 0) for item in results),
        "refiner_ops_applied": sum(len((item.get("block_refiner") or {}).get("applied_ops") or []) for item in results),
    }


def _truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 3)].rstrip() + "..."
