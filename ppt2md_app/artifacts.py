import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .config import AppConfig
from .ir import PAGE_IR_SCHEMA_VERSION, build_page_ir
from .prompts import (
    PROMPT_STAGE_1_VERSION,
    PROMPT_STAGE_1_VISION,
    PROMPT_STAGE_2_VERSION,
    PROMPT_STAGE_2_BRAIN,
)
from .provenance import PROVENANCE_SCHEMA_VERSION, build_page_provenance
from .refiner import BLOCK_REFINER_VERSION, refine_page_ir
from .versioning import PNG2MD_PIPELINE_VERSION


RAW_CACHE_SCHEMA_VERSION = 1
SLIDE_META_SCHEMA_VERSION = 1
RUN_REPORT_SCHEMA_VERSION = 1


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stage1_fingerprint(image_path: str | Path, config: AppConfig) -> Dict[str, Any]:
    path = Path(image_path)
    return {
        "stage": "stage1",
        "image_sha256": sha256_file(path),
        "image_size_bytes": path.stat().st_size,
        "pipeline_version": PNG2MD_PIPELINE_VERSION,
        "prompt_version": PROMPT_STAGE_1_VERSION,
        "prompt_sha256": sha256_text(PROMPT_STAGE_1_VISION),
        "model": _model_identity(
            provider=config.vision_provider,
            model=config.model_vision,
            base_url=config.vision_base_url,
            api_key_env=config.vision_api_key_env,
            thinking_budget=config.thinking_budget_vision,
        ),
    }


def stage2_fingerprint(slide_no: int, raw_data_map: Dict[int, str], config: AppConfig) -> Dict[str, Any]:
    window = {}
    for page in range(slide_no - 2, slide_no + 3):
        raw = raw_data_map.get(page, "")
        window[str(page)] = sha256_text(raw) if raw else None

    return {
        "stage": "stage2",
        "slide_no": slide_no,
        "raw_window_sha256": window,
        "pipeline_version": PNG2MD_PIPELINE_VERSION,
        "prompt_version": PROMPT_STAGE_2_VERSION,
        "prompt_sha256": sha256_text(PROMPT_STAGE_2_BRAIN),
        "model": _model_identity(
            provider=config.brain_provider,
            model=config.model_brain,
            base_url=config.brain_base_url,
            api_key_env=config.brain_api_key_env,
            thinking_budget=config.thinking_budget_brain,
        ),
    }


def build_raw_cache_record(result: Dict[str, Any], image_path: str | Path, config: AppConfig) -> Dict[str, Any]:
    raw_text = result.get("raw_text") or ""
    slide_no = int(result.get("slide_no") or 0)
    fingerprint = stage1_fingerprint(image_path, config)
    block_refine_result = refine_page_ir(build_page_ir(raw_text, slide_no), slide_no=slide_no, target_raw=raw_text)
    page_ir = block_refine_result.page_ir
    provenance = build_page_provenance(page_ir)
    return {
        "schema_version": RAW_CACHE_SCHEMA_VERSION,
        "status": "ok",
        "success": True,
        "slide_no": slide_no,
        "raw_text": raw_text,
        "blocks": page_ir["blocks"],
        "page_ir": page_ir,
        "block_refiner": block_refine_result.to_dict(),
        "provenance": provenance,
        "raw_text_sha256": sha256_text(raw_text),
        "error": None,
        "metadata": {
            "created_at": now_iso(),
            "image_sha256": fingerprint["image_sha256"],
            "image_size_bytes": fingerprint["image_size_bytes"],
            "pipeline_version": PNG2MD_PIPELINE_VERSION,
            "prompt": {
                "stage": "stage1",
                "version": PROMPT_STAGE_1_VERSION,
                "sha256": fingerprint["prompt_sha256"],
            },
            "ir_schema_version": PAGE_IR_SCHEMA_VERSION,
            "block_refiner_version": BLOCK_REFINER_VERSION,
            "provenance_schema_version": PROVENANCE_SCHEMA_VERSION,
            "model": fingerprint["model"],
        },
        "fingerprint": fingerprint,
    }


def build_slide_meta(
    slide_no: int,
    markdown: str,
    validation: Dict[str, Any],
    raw_data_map: Dict[int, str],
    config: AppConfig,
    refiner: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    fingerprint = stage2_fingerprint(slide_no, raw_data_map, config)
    return {
        "schema_version": SLIDE_META_SCHEMA_VERSION,
        "status": "ok",
        "slide_no": slide_no,
        "markdown_sha256": sha256_text(markdown),
        "validation": validation,
        "refiner": refiner or {"changed": False, "applied_ops": [], "dismissed": []},
        "error": None,
        "metadata": {
            "created_at": now_iso(),
            "pipeline_version": PNG2MD_PIPELINE_VERSION,
            "prompt": {
                "stage": "stage2",
                "version": PROMPT_STAGE_2_VERSION,
                "sha256": fingerprint["prompt_sha256"],
            },
            "model": fingerprint["model"],
        },
        "fingerprint": fingerprint,
    }


def build_fail_open_slide_meta(
    slide_no: int,
    markdown: str,
    validation: Dict[str, Any],
    raw_data_map: Dict[int, str],
    config: AppConfig,
    *,
    code: str,
    message: str,
    fallback_source: str,
) -> Dict[str, Any]:
    fingerprint = stage2_fingerprint(slide_no, raw_data_map, config)
    return {
        "schema_version": SLIDE_META_SCHEMA_VERSION,
        "status": "fail_open",
        "slide_no": slide_no,
        "markdown_sha256": sha256_text(markdown),
        "validation": validation,
        "refiner": {"changed": False, "applied_ops": [], "dismissed": []},
        "error": {"code": code, "message": message},
        "fallback": {
            "source": fallback_source,
            "note": "Markdown was generated from Stage 1 Page IR because Stage 2 did not produce a trusted result.",
        },
        "metadata": {
            "created_at": now_iso(),
            "pipeline_version": PNG2MD_PIPELINE_VERSION,
            "prompt": {
                "stage": "stage2",
                "version": PROMPT_STAGE_2_VERSION,
                "sha256": fingerprint["prompt_sha256"],
            },
            "model": fingerprint["model"],
        },
        "fingerprint": fingerprint,
    }


def build_error_sidecar(slide_no: int, stage: str, code: str, message: str, **extra) -> Dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "failed",
        "slide_no": slide_no,
        "stage": stage,
        "error": {
            "code": code,
            "message": message,
        },
        "created_at": now_iso(),
        **extra,
    }


def validate_raw_cache_record(
    data: Dict[str, Any],
    slide_no: int,
    expected_fingerprint: Dict[str, Any],
) -> tuple[bool, str]:
    if not isinstance(data, dict):
        return False, "invalid"
    if data.get("schema_version") != RAW_CACHE_SCHEMA_VERSION:
        return False, "legacy_miss"
    if data.get("status") != "ok" or data.get("success") is not True:
        return False, "invalid"
    if data.get("slide_no") != slide_no:
        return False, "invalid"
    raw_text = data.get("raw_text")
    if not isinstance(raw_text, str) or not raw_text.strip():
        return False, "invalid"
    if not isinstance(data.get("blocks"), list):
        return False, "invalid"
    page_ir = data.get("page_ir")
    if not isinstance(page_ir, dict) or page_ir.get("schema_version") != PAGE_IR_SCHEMA_VERSION:
        return False, "invalid"
    block_refiner = data.get("block_refiner")
    if not isinstance(block_refiner, dict) or block_refiner.get("version") != BLOCK_REFINER_VERSION:
        return False, "invalid"
    provenance = data.get("provenance")
    if not isinstance(provenance, dict) or provenance.get("schema_version") != PROVENANCE_SCHEMA_VERSION:
        return False, "invalid"
    if data.get("raw_text_sha256") != sha256_text(raw_text):
        return False, "invalid"
    if data.get("fingerprint") != expected_fingerprint:
        return False, "invalid"
    return True, "hit"


def validate_slide_meta(
    meta: Dict[str, Any],
    slide_no: int,
    markdown: str,
    expected_fingerprint: Dict[str, Any],
) -> tuple[bool, str]:
    if not isinstance(meta, dict):
        return False, "invalid"
    if meta.get("schema_version") != SLIDE_META_SCHEMA_VERSION:
        return False, "legacy_miss"
    if meta.get("status") != "ok":
        return False, "invalid"
    if meta.get("slide_no") != slide_no:
        return False, "invalid"
    if meta.get("markdown_sha256") != sha256_text(markdown):
        return False, "invalid"
    if meta.get("fingerprint") != expected_fingerprint:
        return False, "invalid"
    return True, "hit"


def report_model_identity(config: AppConfig) -> Dict[str, Any]:
    return {
        "vision": _model_identity(
            provider=config.vision_provider,
            model=config.model_vision,
            base_url=config.vision_base_url,
            api_key_env=config.vision_api_key_env,
            thinking_budget=config.thinking_budget_vision,
            input_price_per_million=config.vision_input_price_per_million,
            output_price_per_million=config.vision_output_price_per_million,
        ),
        "brain": _model_identity(
            provider=config.brain_provider,
            model=config.model_brain,
            base_url=config.brain_base_url,
            api_key_env=config.brain_api_key_env,
            thinking_budget=config.thinking_budget_brain,
            input_price_per_million=config.brain_input_price_per_million,
            output_price_per_million=config.brain_output_price_per_million,
        ),
    }


def report_prompt_identity() -> Dict[str, Any]:
    return {
        "stage1": {
            "version": PROMPT_STAGE_1_VERSION,
            "sha256": sha256_text(PROMPT_STAGE_1_VISION),
        },
        "stage2": {
            "version": PROMPT_STAGE_2_VERSION,
            "sha256": sha256_text(PROMPT_STAGE_2_BRAIN),
        },
    }


def _model_identity(
    *,
    provider: str,
    model: str,
    base_url: str,
    api_key_env: str,
    thinking_budget: int,
    input_price_per_million=None,
    output_price_per_million=None,
) -> Dict[str, Any]:
    identity = {
        "provider": provider,
        "model": model,
        "base_url": _canonical_base_url(provider, base_url),
        "api_key_env": api_key_env,
        "thinking_budget": thinking_budget,
    }
    if input_price_per_million is not None or output_price_per_million is not None:
        identity["pricing"] = {
            "input_per_million": input_price_per_million,
            "output_per_million": output_price_per_million,
        }
    return identity


def _canonical_base_url(provider: str, base_url: str) -> str:
    if provider == "dashscope":
        return ""
    return (base_url or "").strip().rstrip("/")
