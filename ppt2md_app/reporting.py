from pathlib import Path
from typing import Any, Dict, Iterable

from .artifacts import (
    RUN_REPORT_SCHEMA_VERSION,
    now_iso,
    report_model_identity,
    report_prompt_identity,
)
from .config import AppConfig
from .provenance import merge_provenance_summaries
from .table_quality import assess_table_markdown
from .versioning import PNG2MD_PIPELINE_VERSION


def build_run_report(
    ppt_name: str,
    target_images: Iterable[str],
    start_idx: int,
    config: AppConfig,
) -> tuple[Dict[str, Any], Dict[int, Dict[str, Any]]]:
    pages = []
    for offset, image_path in enumerate(target_images):
        slide_no = start_idx + offset + 1
        pages.append(
            {
                "slide_no": slide_no,
                "image_path": str(Path(image_path)),
                "image_sha256": None,
                "stage1": _stage_state(),
                "stage2": _stage_state(),
                "validation": {"ok": None, "errors": [], "warnings": []},
                "quality": _empty_quality_summary(),
                "provenance": {"schema_version": None, "entries": [], "summary": {}},
                "block_refiner": {"version": None, "changed": False, "applied_ops": [], "dismissed": [], "validation": None},
                "refiner": {"changed": False, "applied_ops": [], "dismissed": []},
                "final": {
                    "status": "pending",
                    "included_in_full": False,
                    "reason": None,
                },
            }
        )

    report = {
        "schema_version": RUN_REPORT_SCHEMA_VERSION,
        "pipeline_version": PNG2MD_PIPELINE_VERSION,
        "ppt_name": ppt_name,
        "started_at": now_iso(),
        "finished_at": None,
        "status": "running",
        "models": report_model_identity(config),
        "prompts": report_prompt_identity(),
        "summary": {},
        "cost": {
            "estimated": None,
            "actual_tokens": None,
            "note": "Per-request token usage is not available from the current streaming API wrappers.",
        },
        "pages": pages,
    }
    return report, {page["slide_no"]: page for page in pages}


def finalize_run_report(report: Dict[str, Any]) -> Dict[str, Any]:
    report["finished_at"] = now_iso()
    pages = report.get("pages") or []
    pages_ok = sum(1 for page in pages if page.get("final", {}).get("status") == "ok")
    pages_failed = sum(1 for page in pages if page.get("final", {}).get("status") in ("failed", "fail_open"))
    stage1_cache_hits = sum(1 for page in pages if page.get("stage1", {}).get("cache") == "hit")
    stage2_cache_hits = sum(1 for page in pages if page.get("stage2", {}).get("cache") == "hit")
    warnings = sum(len(page.get("validation", {}).get("warnings") or []) for page in pages)
    block_refiner_applied_ops = sum(len(page.get("block_refiner", {}).get("applied_ops") or []) for page in pages)
    formula_warning_count = sum(
        _count_validation_codes(page, ("formula_", "latex_"))
        + int(page.get("quality", {}).get("formula_warning_count") or 0)
        for page in pages
    )
    table_warning_count = sum(
        _count_validation_codes(page, ("table_",)) + int(page.get("quality", {}).get("table_warning_count") or 0)
        for page in pages
    )
    block_counts = _sum_block_counts(pages)
    provenance_summary = merge_provenance_summaries(pages)

    report["summary"] = {
        "pages_total": len(pages),
        "pages_ok": pages_ok,
        "pages_failed": pages_failed,
        "stage1_cache_hits": stage1_cache_hits,
        "stage2_cache_hits": stage2_cache_hits,
        "fail_open_pages": sum(1 for page in pages if page.get("final", {}).get("status") == "fail_open"),
        "validation_warnings": warnings,
        "block_refiner_changed_pages": sum(1 for page in pages if page.get("block_refiner", {}).get("changed")),
        "block_refiner_applied_ops": block_refiner_applied_ops,
        "block_counts": block_counts,
        "provenance": provenance_summary,
        "uncertain_block_count": block_counts.get("uncertain", 0),
        "figure_count": block_counts.get("figure_note", 0),
        "figure_warning_count": sum(int(page.get("quality", {}).get("figure_warning_count") or 0) for page in pages),
        "formula_warning_count": formula_warning_count,
        "table_warning_count": table_warning_count,
    }
    if pages_ok == len(pages):
        report["status"] = "ok"
    elif pages_ok > 0:
        report["status"] = "partial_failed"
    else:
        report["status"] = "failed"
    return report


def stage_failed(page: Dict[str, Any], stage: str, code: str, message: str):
    page[stage].update(
        {
            "status": "failed",
            "error_code": code,
            "error_message": message,
        }
    )


def stage_blocked(page: Dict[str, Any], stage: str, code: str, message: str):
    page[stage].update(
        {
            "status": "blocked",
            "error_code": code,
            "error_message": message,
        }
    )


def summarize_blocks(blocks: Iterable[Dict[str, Any]] | None) -> Dict[str, Any]:
    summary = _empty_quality_summary()
    for block in blocks or []:
        block_type = block.get("type") or "unknown"
        summary["block_counts"][block_type] = summary["block_counts"].get(block_type, 0) + 1
        if block_type == "uncertain":
            summary["uncertain_block_count"] += 1
        elif block_type == "figure_note":
            summary["figure_count"] += 1
            if block.get("unrecognizable"):
                summary["figure_warning_count"] += 1
                summary["warnings"].append(
                    {
                        "code": "figure_unrecognizable",
                        "message": "图示 block 标记为不可可靠识别。",
                        "figure_type": block.get("figure_type"),
                    }
                )
        elif block_type in {"formula_inline", "formula_block"}:
            warning = _formula_block_warning(block.get("text") or "")
            if warning:
                summary["formula_warning_count"] += 1
                summary["warnings"].append(warning)
        elif block_type == "table":
            quality = assess_table_markdown(block.get("text") or "")
            if not quality.reliable:
                summary["table_warning_count"] += 1
                summary["warnings"].append(
                    {
                        "code": "table_quality_warning",
                        "message": "表格结构不可靠。",
                        "details": quality.to_dict(),
                    }
                )
    return summary


def _stage_state():
    return {
        "status": "pending",
        "cache": None,
        "path": None,
        "elapsed_seconds": None,
        "sha256": None,
        "error_code": None,
        "error_message": None,
        "warnings": [],
    }


def _empty_quality_summary() -> Dict[str, Any]:
    return {
        "block_counts": {},
        "uncertain_block_count": 0,
        "figure_count": 0,
        "figure_warning_count": 0,
        "formula_warning_count": 0,
        "table_warning_count": 0,
        "warnings": [],
    }


def _count_validation_codes(page: Dict[str, Any], prefixes: tuple[str, ...]) -> int:
    warnings = page.get("validation", {}).get("warnings") or []
    return sum(1 for issue in warnings if str(issue.get("code") or "").startswith(prefixes))


def _sum_block_counts(pages: list[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for page in pages:
        for block_type, count in (page.get("quality", {}).get("block_counts") or {}).items():
            counts[block_type] = counts.get(block_type, 0) + count
    return counts


def _formula_block_warning(text: str) -> Dict[str, Any] | None:
    lower = (text or "").lower()
    if (
        "[?]" in text
        or "？" in text
        or "无法确定" in text
        or "看不清" in text
        or "不确定" in text
        or "uncertain" in lower
        or "illegible" in lower
    ):
        return {"code": "formula_uncertain_marker", "message": "公式 block 包含不确定识别标记。"}
    return None
