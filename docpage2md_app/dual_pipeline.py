from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import Any

from .artifacts import RUN_REPORT_SCHEMA_VERSION, now_iso, sha256_text
from .config import AppConfig
from .content_inventory import build_content_inventory
from .dual_ir import DUAL_ADAPTER_VERSION
from .files import merge_markdowns, write_json, write_text_atomic
from .fusion import fuse_document_irs
from .hybrid_enrichment import HYBRID_ENRICHMENT_VERSION, enrich_mineru_document_ir
from .mineru_adapter import adapt_mineru_artifacts
from .mineru_artifacts import discover_mineru_artifacts
from .mineru_pipeline import _copy_assets as _copy_mineru_assets
from .mineru_pipeline import _copy_mineru_raw, _empty_hybrid_stage, _page_assets
from .mineru_adapter import rewrite_asset_refs as rewrite_mineru_asset_refs
from .paddleocr_adapter import adapt_paddleocr_artifacts
from .paddleocr_artifacts import discover_paddleocr_artifacts
from .paddleocr_pipeline import _copy_assets as _copy_paddleocr_assets
from .paddleocr_pipeline import _copy_paddleocr_raw
from .paddleocr_adapter import rewrite_asset_refs as rewrite_paddleocr_asset_refs
from .provenance import build_page_provenance
from .renderer import RENDERER_VERSION, render_page_ir_to_markdown
from .reporting import finalize_run_report, refresh_page_suspects, summarize_blocks
from .run_logger import ProgressCallback, safe_progress
from .validators import validate_slide_markdown
from .versioning import DOCPAGE2MD_PIPELINE_VERSION


DUAL_ENGINE_MODE = "dual_hybrid"


def process_dual_artifact_task(
    mineru_artifact_dir: str | Path,
    paddleocr_artifact_dir: str | Path,
    config: AppConfig,
    *,
    doc_name: str | None = None,
    source_path: str | None = None,
    vision_backend=None,
    brain_backend=None,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    safe_progress(progress, f"Discovering dual artifacts: mineru={mineru_artifact_dir}, paddleocr={paddleocr_artifact_dir}")
    mineru_artifacts = discover_mineru_artifacts(mineru_artifact_dir)
    paddleocr_artifacts = discover_paddleocr_artifacts(paddleocr_artifact_dir)
    output_name = doc_name or _doc_name(source_path, mineru_artifacts.root)
    output_root = Path(config.output_folder) / output_name
    output_root.mkdir(parents=True, exist_ok=True)
    safe_progress(progress, f"Dual output directory ready: {output_root}")

    safe_progress(progress, "Adapting MinerU artifact to DocumentIR")
    mineru_ir = adapt_mineru_artifacts(mineru_artifacts, source_path=source_path, engine_mode=DUAL_ENGINE_MODE)
    mineru_ref_map = _copy_mineru_assets(mineru_ir, output_root)
    rewrite_mineru_asset_refs(mineru_ir, mineru_ref_map)
    _copy_mineru_raw(mineru_artifacts, output_root)
    safe_progress(progress, f"MinerU evidence ready: pages={len(mineru_ir.get('pages') or [])}, assets={len(mineru_ref_map)}")

    safe_progress(progress, "Adapting PaddleOCR artifact to DocumentIR")
    paddleocr_ir = adapt_paddleocr_artifacts(paddleocr_artifacts, source_path=source_path, engine_mode=DUAL_ENGINE_MODE)
    paddle_ref_map = _copy_paddleocr_assets(paddleocr_ir, output_root)
    rewrite_paddleocr_asset_refs(paddleocr_ir, paddle_ref_map)
    _copy_paddleocr_raw(paddleocr_artifacts, output_root)
    safe_progress(progress, f"PaddleOCR evidence ready: pages={len(paddleocr_ir.get('pages') or [])}, assets={len(paddle_ref_map)}")

    safe_progress(progress, "Fusing MinerU + PaddleOCR candidate groups")
    fusion_result = fuse_document_irs(
        mineru_ir,
        paddleocr_ir,
        document_type=config.document_type,
        engine_mode=DUAL_ENGINE_MODE,
    )
    fusion_report = fusion_result.report
    document_ir = fusion_result.document_ir
    pages = document_ir.get("pages") or []
    block_count = sum(len(page.get("blocks") or []) for page in pages)
    safe_progress(
        progress,
        (
            "Dual fused DocumentIR ready: "
            f"pages={len(pages)}, blocks={block_count}, "
            f"candidate_groups={(fusion_report.get('summary') or {}).get('candidate_groups')}"
        ),
    )

    safe_progress(progress, "Dual hybrid enrichment start: crop vision + Brain evidence selection")
    enrichment = enrich_mineru_document_ir(
        document_ir,
        config,
        output_root=output_root,
        vision_backend=vision_backend,
        brain_backend=brain_backend,
        progress=progress,
    )
    document_ir = enrichment["document_ir"]
    safe_progress(progress, f"Dual hybrid enrichment done: {enrichment.get('summary')}")

    ir_dir = output_root / "ir"
    ir_dir.mkdir(parents=True, exist_ok=True)
    write_json(ir_dir / "mineru_document_ir.json", mineru_ir)
    write_json(ir_dir / "paddleocr_document_ir.json", paddleocr_ir)
    write_json(ir_dir / "fused_document_ir.json", document_ir)
    write_json(ir_dir / "document_ir.json", document_ir)
    safe_progress(progress, f"Wrote dual fusion IR files: {ir_dir}")

    report = _initial_report(output_name, config, document_ir, mineru_artifacts, paddleocr_artifacts, source_path)
    report["fusion"] = fusion_report
    report["dual_parser"]["strategy"] = fusion_report.get("strategy") or "candidate_group_checked_ops"
    report["hybrid_enrichment"] = {
        "version": HYBRID_ENRICHMENT_VERSION,
        "enabled": True,
        "summary": (enrichment.get("summary") or {}).get("pages") or enrichment.get("summary"),
    }
    ok_slides: list[int] = []
    render_started = time.monotonic()
    for page_index, page_ir in enumerate(document_ir.get("pages") or [], start=1):
        slide_no = int(page_ir.get("source_page") or 0)
        if slide_no <= 0:
            continue
        safe_progress(
            progress,
            f"Rendering dual page {page_index}/{len(document_ir.get('pages') or [])}: slide={slide_no}, blocks={len(page_ir.get('blocks') or [])}",
        )
        markdown = render_page_ir_to_markdown(page_ir, slide_no)
        validation = validate_slide_markdown(
            markdown,
            slide_no,
            target_raw=page_ir.get("raw_text"),
            target_blocks=page_ir.get("blocks") or [],
        )
        status = "ok" if validation.ok else "fail_open"
        slide_path = output_root / f"Slide_{slide_no:02d}.md"
        meta_path = output_root / f"Slide_{slide_no:02d}.meta.json"
        write_text_atomic(slide_path, markdown)
        write_json(meta_path, _slide_meta(slide_no, markdown, validation.to_dict()))
        write_json(ir_dir / f"page_{slide_no:03d}_ir.json", page_ir)
        ok_slides.append(slide_no)

        enrichment_page = (enrichment or {}).get("pages", {}).get(slide_no) if enrichment else None
        page_report = _page_report(page_ir, slide_no, slide_path, meta_path, markdown, validation.to_dict(), status, enrichment_page)
        report["pages"].append(page_report)
        refresh_page_suspects(page_report, page_ir.get("blocks") or [])
        safe_progress(progress, f"Dual page rendered: slide={slide_no}, status={status}, markdown={slide_path.name}")
    safe_progress(progress, f"Dual Markdown rendering done: pages={len(ok_slides)}, elapsed={time.monotonic() - render_started:.1f}s")

    safe_progress(progress, "Merging per-page Markdown into FULL document")
    merge_markdowns(output_root, output_name, allowed_slide_numbers=ok_slides)
    for page in report["pages"]:
        if int(page.get("slide_no") or 0) in ok_slides:
            page["final"]["included_in_full"] = True
    finalize_run_report(report)
    report["engine_mode"] = DUAL_ENGINE_MODE
    write_json(output_root / "run_report.json", report)
    safe_progress(progress, f"Wrote dual run report: {output_root / 'run_report.json'}, status={report.get('status')}")
    return {
        "doc_name": output_name,
        "output_dir": str(output_root),
        "report_path": str(output_root / "run_report.json"),
        "page_count": len(document_ir.get("pages") or []),
        "status": report.get("status"),
    }


def _initial_report(
    doc_name: str,
    config: AppConfig,
    document_ir: dict[str, Any],
    mineru_artifacts,
    paddleocr_artifacts,
    source_path: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": RUN_REPORT_SCHEMA_VERSION,
        "pipeline_version": DOCPAGE2MD_PIPELINE_VERSION,
        "adapter_version": DUAL_ADAPTER_VERSION,
        "renderer_version": RENDERER_VERSION,
        "doc_name": doc_name,
        "engine_mode": DUAL_ENGINE_MODE,
        "started_at": now_iso(),
        "finished_at": None,
        "status": "running",
        "models": {
            "layout_engine": {
                "provider": "mineru+paddleocr",
                "model": f"{config.mineru_model_version}+{config.paddleocr_model}",
                "base_url": f"{config.mineru_base_url} | {config.paddleocr_base_url}",
                "api_key_env": f"{config.mineru_api_token_env},{config.paddleocr_api_key_env}",
            },
            "mineru_layout": {
                "provider": "mineru",
                "model": config.mineru_model_version,
                "base_url": config.mineru_base_url,
                "api_key_env": config.mineru_api_token_env,
            },
            "paddleocr_layout": {
                "provider": "paddleocr",
                "model": config.paddleocr_model,
                "base_url": config.paddleocr_base_url,
                "api_key_env": config.paddleocr_api_key_env,
            },
            "vision": {
                "provider": config.vision_provider,
                "model": config.model_vision,
                "base_url": config.vision_base_url,
                "api_key_env": config.vision_api_key_env,
            },
            "crop_vision": {
                "provider": config.vision_provider,
                "model": config.model_vision,
                "base_url": config.vision_base_url,
                "api_key_env": config.vision_api_key_env,
            },
            "brain": {
                "provider": config.brain_provider,
                "model": config.model_brain,
                "base_url": config.brain_base_url,
                "api_key_env": config.brain_api_key_env,
            },
        },
        "prompts": {},
        "summary": {},
        "cost": {
            "estimated": None,
            "actual_tokens": None,
            "note": "MinerU/PaddleOCR are quota-based parser stages; Vision/Brain token usage is recorded when providers return usage.",
        },
        "dual_parser": {
            "version": DUAL_ADAPTER_VERSION,
            "strategy": "candidate_group_checked_ops",
            "source": document_ir.get("source"),
            "mineru": {
                "artifact_manifest": mineru_artifacts.to_manifest(),
                "model_version": config.mineru_model_version,
            },
            "paddleocr": {
                "artifact_manifest": paddleocr_artifacts.to_manifest(),
                "model": config.paddleocr_model,
            },
            "input_path": source_path,
        },
        "mineru": {
            "artifact_manifest": mineru_artifacts.to_manifest(),
            "model_version": config.mineru_model_version,
        },
        "paddleocr": {
            "artifact_manifest": paddleocr_artifacts.to_manifest(),
            "model": config.paddleocr_model,
        },
        "hybrid_enrichment": {
            "version": HYBRID_ENRICHMENT_VERSION,
            "enabled": True,
        },
        "pages": [],
    }


def _page_report(
    page_ir: dict[str, Any],
    slide_no: int,
    slide_path: Path,
    meta_path: Path,
    markdown: str,
    validation: dict[str, Any],
    status: str,
    enrichment_page: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blocks = page_ir.get("blocks") or []
    op_audit = list((enrichment_page or {}).get("op_audit") or [])
    block_refiner = (enrichment_page or {}).get("block_refiner") or {
        "version": None,
        "changed": False,
        "applied_ops": [],
        "dismissed": [],
        "op_audit": [],
        "validation": None,
    }
    return {
        "slide_no": slide_no,
        "image_path": page_ir.get("page_image_ref"),
        "image_sha256": None,
        "page_image_ref": page_ir.get("page_image_ref"),
        "stage1": {
            "status": "ok",
            "cache": "dual_parser_artifact",
            "path": str(meta_path),
            "elapsed_seconds": 0.0,
            "sha256": page_ir.get("raw_text_sha256"),
            "usage": None,
            "request_id": None,
            "provider_latency": None,
            "error_code": None,
            "error_message": None,
            "warnings": [],
            "blocks_count": len(blocks),
        },
        "stage2": {
            "status": "ok" if status == "ok" else "failed",
            "cache": "deterministic_render",
            "path": str(slide_path),
            "meta_path": str(meta_path),
            "elapsed_seconds": 0.0,
            "sha256": sha256_text(slide_path.read_text(encoding="utf-8")) if slide_path.exists() else None,
            "usage": None,
            "request_id": None,
            "provider_latency": None,
            "error_code": None if status == "ok" else "validation_failed",
            "error_message": None if status == "ok" else "Dual render produced validation errors.",
            "warnings": [],
        },
        "vision": (enrichment_page or {}).get("vision") or _empty_hybrid_stage("vision"),
        "brain": (enrichment_page or {}).get("brain") or _empty_hybrid_stage("brain"),
        "validation": validation,
        "quality": summarize_blocks(blocks),
        "suspects": [],
        "provenance": build_page_provenance(page_ir),
        "content_inventory": build_content_inventory(page_ir, markdown, op_audit=op_audit),
        "block_refiner": block_refiner,
        "op_audit": op_audit,
        "refiner": {"changed": False, "applied_ops": [], "dismissed": []},
        "assets": _page_assets(blocks),
        "dual_evidence": _dual_evidence_summary(page_ir),
        "fusion": _fusion_summary(page_ir),
        "mineru": page_ir.get("mineru") or {},
        "paddleocr": (page_ir.get("dual_evidence") or {}).get("paddleocr") or {},
        "final": {
            "status": status,
            "included_in_full": False,
            "reason": None if status == "ok" else "validation_failed",
            "markdown_source": {
                "kind": "dual_hybrid_enriched_ir",
                "source": "dual_parser_hybrid_enrichment_renderer",
                "renderer_version": RENDERER_VERSION,
            },
        },
    }


def _slide_meta(slide_no: int, markdown: str, validation: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "status": "ok" if validation.get("ok") else "fail_open",
        "slide_no": slide_no,
        "markdown_sha256": sha256_text(markdown),
        "validation": validation,
        "refiner": {"changed": False, "applied_ops": [], "dismissed": []},
        "markdown_source": {
            "kind": "dual_hybrid_enriched_ir",
            "source": "dual_parser_hybrid_enrichment_renderer",
            "renderer_version": RENDERER_VERSION,
        },
        "error": None if validation.get("ok") else {"code": "validation_failed", "message": "See run_report.json."},
        "metadata": {
            "created_at": now_iso(),
            "pipeline_version": DOCPAGE2MD_PIPELINE_VERSION,
            "adapter_version": DUAL_ADAPTER_VERSION,
        },
    }


def _dual_evidence_summary(page_ir: dict[str, Any]) -> dict[str, Any]:
    evidence = page_ir.get("dual_evidence") or {}
    mineru = evidence.get("mineru") or {}
    paddle = evidence.get("paddleocr") or {}
    return {
        "mineru_available": bool(mineru.get("available")),
        "paddleocr_available": bool(paddle.get("available")),
        "mineru_block_count": mineru.get("block_count"),
        "paddleocr_block_count": paddle.get("block_count"),
    }


def _fusion_summary(page_ir: dict[str, Any]) -> dict[str, Any]:
    fusion = page_ir.get("fusion") if isinstance(page_ir.get("fusion"), dict) else {}
    return {
        "version": fusion.get("version"),
        "candidate_group_count": len(fusion.get("candidate_groups") or []),
        "decision_count": len(fusion.get("decisions") or []),
        "rejected_op_count": len(fusion.get("rejected_ops") or []),
        "uncertain_count": len(fusion.get("uncertain_items") or []),
        "backend": fusion.get("backend"),
    }


def _doc_name(source_path: str | None, artifact_root: Path) -> str:
    if source_path:
        stem = Path(str(source_path)).stem
        if stem:
            return stem
    return artifact_root.name or "dual_hybrid_task"
