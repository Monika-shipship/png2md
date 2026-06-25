import shutil
import time
from pathlib import Path
from typing import Any

from .artifacts import RUN_REPORT_SCHEMA_VERSION, now_iso, sha256_text
from .config import AppConfig
from .content_inventory import build_content_inventory
from .files import merge_markdowns, write_json, write_text_atomic
from .hybrid_enrichment import HYBRID_ENRICHMENT_VERSION, enrich_mineru_document_ir
from .mineru_adapter import (
    MINERU_ADAPTER_VERSION,
    adapt_mineru_artifacts,
    iter_artifact_image_refs,
    rewrite_asset_refs,
)
from .mineru_artifacts import MinerUArtifacts, discover_mineru_artifacts
from .provenance import build_page_provenance
from .renderer import RENDERER_VERSION, render_page_ir_to_markdown
from .reporting import finalize_run_report, refresh_page_suspects, summarize_blocks
from .run_logger import ProgressCallback, safe_progress
from .validators import validate_slide_markdown
from .versioning import DOCPAGE2MD_PIPELINE_VERSION


def process_mineru_artifact_task(
    artifact_dir: str | Path,
    config: AppConfig,
    *,
    doc_name: str | None = None,
    engine_mode: str | None = None,
    source_path: str | None = None,
    vision_backend=None,
    brain_backend=None,
    progress: ProgressCallback | None = None,
) -> dict[str, Any]:
    safe_progress(progress, f"Discovering MinerU artifacts: {artifact_dir}")
    artifacts = discover_mineru_artifacts(artifact_dir)
    mode = engine_mode or config.engine_mode or "mineru_only"
    output_name = _doc_name(doc_name, source_path, artifacts)
    output_root = Path(config.output_folder) / output_name
    output_root.mkdir(parents=True, exist_ok=True)
    safe_progress(progress, f"Output directory ready: {output_root}")

    safe_progress(progress, "Adapting MinerU artifacts to DocumentIR")
    document_ir = adapt_mineru_artifacts(artifacts, source_path=source_path, engine_mode=mode)
    pages = document_ir.get("pages") or []
    block_count = sum(len(page.get("blocks") or []) for page in pages)
    safe_progress(progress, f"DocumentIR ready: pages={len(pages)}, blocks={block_count}")
    ref_map = _copy_assets(document_ir, output_root)
    safe_progress(progress, f"Copied MinerU crop assets: count={len(ref_map)}")
    rewrite_asset_refs(document_ir, ref_map)
    _copy_mineru_raw(artifacts, output_root)
    safe_progress(progress, "Copied MinerU raw artifacts")

    enrichment = None
    if mode == "hybrid":
        safe_progress(progress, "Hybrid enrichment start: crop vision + Brain JSON ops + checked refiner")
        enrichment = enrich_mineru_document_ir(
            document_ir,
            config,
            output_root=output_root,
            vision_backend=vision_backend,
            brain_backend=brain_backend,
            progress=progress,
        )
        document_ir = enrichment["document_ir"]
        safe_progress(progress, f"Hybrid enrichment done: {enrichment.get('summary')}")

    ir_dir = output_root / "ir"
    ir_dir.mkdir(parents=True, exist_ok=True)
    write_json(ir_dir / "document_ir.json", document_ir)
    safe_progress(progress, f"Wrote document IR: {ir_dir / 'document_ir.json'}")

    report = _initial_report(output_name, mode, artifacts, config, document_ir)
    ok_slides = []
    final_pages = document_ir.get("pages") or []
    render_started = time.monotonic()
    for page_index, page_ir in enumerate(final_pages, start=1):
        slide_no = int(page_ir.get("source_page") or 0)
        if slide_no <= 0:
            continue
        safe_progress(
            progress,
            f"Rendering page {page_index}/{len(final_pages)}: slide={slide_no}, blocks={len(page_ir.get('blocks') or [])}",
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
        write_json(meta_path, _slide_meta(slide_no, markdown, validation.to_dict(), mode))
        write_json(ir_dir / f"page_{slide_no:03d}_ir.json", page_ir)
        ok_slides.append(slide_no)

        enrichment_page = (enrichment or {}).get("pages", {}).get(slide_no) if enrichment else None
        page_report = _page_report(
            page_ir,
            slide_no,
            slide_path,
            meta_path,
            markdown,
            validation.to_dict(),
            status,
            mode,
            enrichment_page=enrichment_page,
        )
        report["pages"].append(page_report)
        refresh_page_suspects(page_report, page_ir.get("blocks") or [])
        safe_progress(progress, f"Page rendered: slide={slide_no}, status={status}, markdown={slide_path.name}")
    safe_progress(progress, f"Markdown rendering done: pages={len(ok_slides)}, elapsed={time.monotonic() - render_started:.1f}s")

    safe_progress(progress, "Merging per-page Markdown into FULL document")
    merge_markdowns(output_root, output_name, allowed_slide_numbers=ok_slides)
    for page in report["pages"]:
        if int(page.get("slide_no") or 0) in ok_slides:
            page["final"]["included_in_full"] = True

    finalize_run_report(report)
    report["engine_mode"] = mode
    report["mineru"]["artifact_manifest"] = artifacts.to_manifest()
    if enrichment:
        report["hybrid_enrichment"] = {
            "version": HYBRID_ENRICHMENT_VERSION,
            "enabled": True,
            "summary": (enrichment.get("summary") or {}).get("pages") or enrichment.get("summary"),
        }
    write_json(output_root / "run_report.json", report)
    safe_progress(progress, f"Wrote run report: {output_root / 'run_report.json'}, status={report.get('status')}")
    return {
        "doc_name": output_name,
        "output_dir": str(output_root),
        "report_path": str(output_root / "run_report.json"),
        "page_count": len(document_ir.get("pages") or []),
        "status": report.get("status"),
    }


def _initial_report(
    doc_name: str,
    engine_mode: str,
    artifacts: MinerUArtifacts,
    config: AppConfig,
    document_ir: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": RUN_REPORT_SCHEMA_VERSION,
        "pipeline_version": DOCPAGE2MD_PIPELINE_VERSION,
        "adapter_version": MINERU_ADAPTER_VERSION,
        "renderer_version": RENDERER_VERSION,
        "doc_name": doc_name,
        "engine_mode": engine_mode,
        "started_at": now_iso(),
        "finished_at": None,
        "status": "running",
        "models": {
            "layout_engine": {
                "provider": "mineru",
                "model": config.mineru_model_version,
                "base_url": config.mineru_base_url,
                "api_key_env": config.mineru_api_token_env,
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
            "note": "MinerU artifact rendering does not expose token usage. Later hybrid stages record provider usage when returned.",
        },
        "mineru": {
            "artifact_manifest": artifacts.to_manifest(),
            "model_version": config.mineru_model_version,
            "source": document_ir.get("source"),
        },
        "hybrid_enrichment": {
            "version": HYBRID_ENRICHMENT_VERSION,
            "enabled": engine_mode == "hybrid",
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
    engine_mode: str,
    *,
    enrichment_page: dict[str, Any] | None = None,
) -> dict[str, Any]:
    blocks = page_ir.get("blocks") or []
    provenance = build_page_provenance(page_ir)
    op_audit = list((enrichment_page or {}).get("op_audit") or [])
    block_refiner = (enrichment_page or {}).get("block_refiner") or {
        "version": None,
        "changed": False,
        "applied_ops": [],
        "dismissed": [],
        "op_audit": [],
        "validation": None,
    }
    content_inventory = build_content_inventory(page_ir, markdown, op_audit=op_audit)
    vision_report = (enrichment_page or {}).get("vision") or _empty_hybrid_stage("vision")
    brain_report = (enrichment_page or {}).get("brain") or _empty_hybrid_stage("brain")
    return {
        "slide_no": slide_no,
        "image_path": page_ir.get("page_image_ref"),
        "image_sha256": None,
        "page_image_ref": page_ir.get("page_image_ref"),
        "stage1": {
            "status": "ok",
            "cache": "mineru_artifact",
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
            "error_message": None if status == "ok" else "Deterministic MinerU render produced validation errors.",
            "warnings": [],
        },
        "vision": vision_report,
        "brain": brain_report,
        "validation": validation,
        "quality": summarize_blocks(blocks),
        "suspects": [],
        "provenance": provenance,
        "content_inventory": content_inventory,
        "block_refiner": block_refiner,
        "op_audit": op_audit,
        "refiner": {"changed": False, "applied_ops": [], "dismissed": []},
        "assets": _page_assets(blocks),
        "mineru": page_ir.get("mineru") or {},
        "final": {
            "status": status,
            "included_in_full": False,
            "reason": None if status == "ok" else "validation_failed",
            "markdown_source": {
                "kind": "mineru_artifact" if engine_mode == "mineru_only" else "hybrid_enriched_ir",
                "source": "mineru_adapter_renderer" if engine_mode == "mineru_only" else "mineru_adapter_hybrid_enrichment_renderer",
                "renderer_version": RENDERER_VERSION,
            },
        },
    }


def _empty_hybrid_stage(stage: str) -> dict[str, Any]:
    return {
        "version": HYBRID_ENRICHMENT_VERSION,
        "status": "skipped",
        "usage": None,
        "request_id": None,
        "provider_latency": None,
        "stage": stage,
    }


def _slide_meta(slide_no: int, markdown: str, validation: dict[str, Any], engine_mode: str) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "status": "ok" if validation.get("ok") else "fail_open",
        "slide_no": slide_no,
        "markdown_sha256": sha256_text(markdown),
        "validation": validation,
        "refiner": {"changed": False, "applied_ops": [], "dismissed": []},
        "markdown_source": {
            "kind": "mineru_artifact" if engine_mode == "mineru_only" else "hybrid_enriched_ir",
            "source": "mineru_adapter_renderer" if engine_mode == "mineru_only" else "mineru_adapter_hybrid_enrichment_renderer",
            "renderer_version": RENDERER_VERSION,
        },
        "error": None if validation.get("ok") else {"code": "validation_failed", "message": "See run_report.json."},
        "metadata": {
            "created_at": now_iso(),
            "pipeline_version": DOCPAGE2MD_PIPELINE_VERSION,
            "adapter_version": MINERU_ADAPTER_VERSION,
        },
    }


def _copy_assets(document_ir: dict[str, Any], output_root: Path) -> dict[str, str]:
    assets_dir = output_root / "assets" / "crops"
    assets_dir.mkdir(parents=True, exist_ok=True)
    ref_map: dict[str, str] = {}
    for asset in iter_artifact_image_refs(document_ir):
        source = Path(asset["source_path"])
        if not source.exists() or not source.is_file():
            continue
        block_id = str(asset.get("block_id") or "").replace("-", "_")
        page_no = int(asset.get("page_no") or 0)
        prefix = f"page_{page_no:03d}_{block_id}" if page_no else block_id or "crop"
        dest = assets_dir / f"{prefix}_{source.name}"
        if not dest.exists():
            shutil.copy2(source, dest)
        ref_map[asset["artifact_ref"]] = f"assets/crops/{dest.name}"
    return ref_map


def _copy_mineru_raw(artifacts: MinerUArtifacts, output_root: Path):
    raw_dir = output_root / "mineru_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    for path in artifacts.root.iterdir():
        dest = raw_dir / path.name
        if path.is_file():
            shutil.copy2(path, dest)
        elif path.is_dir() and path.name == "images":
            shutil.copytree(path, dest, dirs_exist_ok=True)


def _page_assets(blocks: list[dict[str, Any]]) -> list[dict[str, str]]:
    assets = []
    for block in blocks:
        for key in ("crop_ref", "image_ref", "table_image_path", "formula_image_path"):
            value = str(block.get(key) or "").strip()
            if value:
                assets.append({"block_id": block.get("id"), "kind": key, "ref": value})
    return assets


def _doc_name(doc_name: str | None, source_path: str | None, artifacts: MinerUArtifacts) -> str:
    if doc_name:
        return doc_name
    if source_path:
        return Path(source_path).stem
    guessed = sorted(artifacts.root.glob("*_origin.*"))
    if guessed:
        return guessed[0].stem.replace("_origin", "")
    return artifacts.root.name
