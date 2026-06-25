from __future__ import annotations

import os
import queue
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable

from .aliyun_catalog import filter_brain_models, filter_vision_models, verify_openai_chat_model, vision_recommendation_tier
from .cli import MINERU_SUPPORTED_SUFFIXES
from .config import AppConfig
from .cost import calculate_image_tokens, estimate_deepseek_chat_tokens, estimate_price, estimate_text_cost
from .env import get_env_value, set_user_env_value
from .log_translate import (
    CROP_VISION_START_RE,
    DOCUMENT_READY_RE,
    HYBRID_PAGE_BRAIN_START_RE,
    HYBRID_PAGE_REFINER_DONE_RE,
    HYBRID_PAGE_START_RE,
    LOG_MESSAGE_RE,
    MINERU_BATCH_SUBMITTED_RE,
    MINERU_PROCESSED_RE,
    PAGE_RENDERED_RE,
    ZH_CROP_VISION_START_RE,
    ZH_DOCUMENT_READY_RE,
    ZH_HYBRID_PAGE_BRAIN_START_RE,
    ZH_HYBRID_PAGE_REFINER_DONE_RE,
    ZH_HYBRID_PAGE_START_RE,
    ZH_MINERU_BATCH_SUBMITTED_RE,
    ZH_MINERU_PROCESSED_RE,
    ZH_PAGE_RENDERED_RE,
    translate_log_line,
)
from .model_catalog import ROLE_BRAIN, ROLE_VISION, load_model_catalog
from .model_profiles import apply_model_profile
from .model_settings import apply_model_settings, load_model_settings, save_model_settings
from .mineru_adapter import adapt_mineru_artifacts
from .mineru_artifacts import discover_mineru_artifacts, resolve_artifact_image
from .third_party_models import (
    delete_third_party_model,
    filter_registry_models,
    load_third_party_models,
    parse_bulk_models_text,
    registry_item_to_model_record,
    update_third_party_model_verification,
    upsert_third_party_model,
)


DOCUMENT_PRESETS = {
    "handwritten_notes": ("手写矢量笔记", "hybrid", "balanced"),
    "paper_pdf": ("论文 PDF", "mineru_only", "balanced"),
    "screenshot_question": ("截图/屏拍小题", "hybrid", "balanced"),
    "complex_ppt": ("复杂公式图表 PPT", "hybrid", "accurate"),
    "custom": ("自定义", "hybrid", "balanced"),
}
DOCUMENT_LABEL_TO_KEY = {label: key for key, (label, _mode, _profile) in DOCUMENT_PRESETS.items()}

DOCUMENT_PRESET_DESCRIPTIONS = {
    "handwritten_notes": "适合课堂板书、手写/半手写 PDF。会推荐混合精修，先用 MinerU 解析版面，再并行用 Vision/Brain 修图示、公式和结构。",
    "paper_pdf": "适合排版清楚的论文或电子书。默认只跑 MinerU，速度最快；需要图表和公式精修时可以手动改成混合精修。",
    "screenshot_question": "适合截图、屏拍小题。GUI 当前走 MinerU/混合链路；旧版纯视觉 vision_only 仍保留在 CLI。",
    "complex_ppt": "适合公式、图表、PPT 较复杂的文件。推荐高精度档位，成本和耗时会更高。",
    "custom": "不套推荐值，适合你自己指定处理模式、模型档位和模型。",
}

ENGINE_MODE_LABELS = {
    "hybrid": "混合精修（推荐）",
    "mineru_only": "仅 MinerU 解析（最快）",
}
ENGINE_MODE_LABEL_TO_KEY = {label: key for key, label in ENGINE_MODE_LABELS.items()}
ENGINE_MODE_DESCRIPTIONS = {
    "hybrid": "先上传/读取 MinerU 结果，再对所有页和裁剪块并行调用 Vision/Brain 精修；质量更好，成本更高。",
    "mineru_only": "只把 MinerU 解析结果渲染成 Markdown，不调用 Vision/Brain；速度最快，适合排版清楚的 PDF。",
    "vision_only": "旧版图片目录流程，只在 CLI 中使用；GUI 主路径暂不启用。",
}

MODEL_PROFILE_LABELS = {
    "cheap": "省钱",
    "balanced": "均衡（推荐）",
    "accurate": "高精度",
    "manual": "自定义",
}
MODEL_PROFILE_LABEL_TO_KEY = {label: key for key, label in MODEL_PROFILE_LABELS.items()}
MODEL_PROFILE_DESCRIPTIONS = {
    "cheap": "使用更便宜的 Vision/Brain 组合，适合清晰文档或大批量低成本处理。",
    "balanced": "默认推荐组合：Qwen3-VL-Plus 负责视觉，DeepSeek V4 Flash 负责 Brain。",
    "accurate": "更强模型组合，适合复杂公式、图表和版式；成本、耗时都更高。",
    "manual": "完全使用模型管理页当前选中的 Vision/Brain，不再自动跟随档位。",
}

SOURCE_LABELS = {
    "input_file": "本地单个文件",
    "input_files": "本地多个文件",
    "input_folder": "本地文件夹批量",
    "mineru_artifact_dir": "MinerU artifact 目录",
    "mineru_url": "远程文件 URL",
}
SOURCE_LABEL_TO_KEY = {label: key for key, label in SOURCE_LABELS.items()}

PAGE_RANGE_RE = re.compile(r"^\d+(-\d+)?(,\d+(-\d+)?)*$")
SUPPORTED_ENGINE_MODES = {"mineru_only", "hybrid"}
SUPPORTED_PROVIDERS = ["dashscope", "dashscope_openai", "deepseek", "openai_compatible"]
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".jp2", ".webp", ".gif", ".bmp"}
VISION_COST_BLOCK_TYPES = {"figure_note", "image_ref", "table", "formula_block"}
ROUGH_PDF_CROP_BLOCKS_PER_PAGE = 3
ROUGH_CROP_IMAGE_TOKENS = 1800
ROUGH_VISION_PROMPT_TOKENS = 450
ROUGH_VISION_OUTPUT_TOKENS = 450
ROUGH_BRAIN_INPUT_TOKENS_PER_PAGE = 3500
ROUGH_BRAIN_OUTPUT_TOKENS_PER_PAGE = 800


@dataclass(frozen=True)
class SelectedModel:
    provider: str
    model: str
    base_url: str
    api_key_env: str


@dataclass(frozen=True)
class GuiRunOptions:
    document_type: str = "handwritten_notes"
    engine_mode: str = "hybrid"
    model_profile: str = "balanced"
    source_kind: str = "input_file"
    source_value: str = ""
    output_folder: str = "./markdown_output"
    session_name: str = ""
    page_ranges: str = ""
    mineru_model_version: str = "vlm"
    recursive: bool = False
    vision_workers: int | str = AppConfig().vision_batch_workers
    brain_workers: int | str = AppConfig().brain_batch_workers
    vision: SelectedModel | None = None
    brain: SelectedModel | None = None
    extra_args: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProgressSnapshot:
    percent: float
    stage: str
    detail: str
    eta: str
    elapsed: str


@dataclass(frozen=True)
class CostEstimateRow:
    name: str
    pages: int | None
    crop_blocks: int | None
    input_tokens: int
    output_tokens: int
    estimated_cost: float | None
    confidence: str
    note: str = ""


@dataclass(frozen=True)
class CostEstimateSummary:
    rows: list[CostEstimateRow]
    total_pages: int | None
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float | None
    confidence: str
    note: str

    def format_brief(self) -> str:
        page_text = "未知页数" if self.total_pages is None else f"{self.total_pages} 页"
        token_text = f"输入 {self.total_input_tokens / 1_000_000:.3f}M / 输出 {self.total_output_tokens / 1_000_000:.3f}M tokens"
        cost_text = "价格未知" if self.total_cost is None else f"约 ¥{self.total_cost:.2f}"
        return f"{page_text}，{token_text}，{cost_text}（{self.confidence}）。{self.note}"


def split_multi_paths(raw: str) -> list[str]:
    return [item.strip().strip('"') for item in raw.split(";") if item.strip()]


def document_type_key(value: str) -> str:
    return DOCUMENT_LABEL_TO_KEY.get(value, value)


def engine_mode_key(value: str) -> str:
    return ENGINE_MODE_LABEL_TO_KEY.get(value, value)


def engine_mode_label(value: str) -> str:
    return ENGINE_MODE_LABELS.get(engine_mode_key(value), value)


def model_profile_key(value: str) -> str:
    return MODEL_PROFILE_LABEL_TO_KEY.get(value, value)


def model_profile_label(value: str) -> str:
    return MODEL_PROFILE_LABELS.get(model_profile_key(value), value)


def source_kind_key(value: str) -> str:
    return SOURCE_LABEL_TO_KEY.get(value, value)


def default_model_selection(profile: str = "balanced", base_config: AppConfig | None = None) -> tuple[SelectedModel, SelectedModel]:
    profile = model_profile_key(profile)
    config = apply_model_profile(base_config or AppConfig(), profile)
    saved = load_model_settings(config)
    if saved and profile == "manual":
        config = apply_model_settings(config, saved)
    return (
        SelectedModel(config.vision_provider, config.model_vision, config.vision_base_url, config.vision_api_key_env),
        SelectedModel(config.brain_provider, config.model_brain, config.brain_base_url, config.brain_api_key_env),
    )


def build_cli_argv(options: GuiRunOptions) -> list[str]:
    engine_mode = engine_mode_key(options.engine_mode)
    model_profile = model_profile_key(options.model_profile)
    if engine_mode not in SUPPORTED_ENGINE_MODES:
        raise ValueError("GUI 目前支持 mineru_only / hybrid 主路径。旧版 vision_only 请继续使用 CLI。")
    document_type = document_type_key(options.document_type)
    source_kind = source_kind_key(options.source_kind)
    if document_type not in DOCUMENT_PRESETS:
        raise ValueError(f"未知文档类型: {options.document_type}")
    if model_profile not in {"cheap", "balanced", "accurate", "manual"}:
        raise ValueError(f"未知模型档位: {options.model_profile}")
    if source_kind not in SOURCE_LABELS:
        raise ValueError(f"未知输入来源: {options.source_kind}")

    page_ranges = options.page_ranges.strip().replace(" ", "")
    if page_ranges and not PAGE_RANGE_RE.match(page_ranges):
        raise ValueError("页码范围格式应类似 1-10 或 2,4-6。")

    argv = [
        "--engine-mode",
        engine_mode,
        "--document-type",
        document_type,
        "--model-profile",
        model_profile,
        "--output",
        options.output_folder,
    ]
    if options.session_name.strip():
        argv.extend(["--name", options.session_name.strip()])
    if page_ranges:
        argv.extend(["--page-ranges", page_ranges])
    if options.mineru_model_version:
        argv.extend(["--mineru-model-version", options.mineru_model_version])
    vision_workers = _positive_worker_count(options.vision_workers, "Vision 并发数")
    brain_workers = _positive_worker_count(options.brain_workers, "Brain 并发数")
    argv.extend(["--vision-workers", str(vision_workers), "--brain-workers", str(brain_workers)])

    if options.vision:
        argv.extend(
            [
                "--vision-provider",
                options.vision.provider,
                "--vision-model",
                options.vision.model,
                "--vision-base-url",
                options.vision.base_url,
                "--vision-api-key-env",
                options.vision.api_key_env,
            ]
        )
    if options.brain:
        argv.extend(
            [
                "--brain-provider",
                options.brain.provider,
                "--brain-model",
                options.brain.model,
                "--brain-base-url",
                options.brain.base_url,
                "--brain-api-key-env",
                options.brain.api_key_env,
            ]
        )

    source_value = options.source_value.strip()
    if not source_value:
        raise ValueError("请选择或填写输入来源。")
    if source_kind == "input_file":
        argv.extend(["--input-file", source_value.strip('"')])
    elif source_kind == "input_files":
        paths = split_multi_paths(source_value)
        if not paths:
            raise ValueError("请至少选择一个本地文件。")
        argv.append("--input-files")
        argv.extend(paths)
    elif source_kind == "input_folder":
        argv.extend(["--input-folder", source_value.strip('"')])
        if options.recursive:
            argv.append("--recursive")
    elif source_kind == "mineru_artifact_dir":
        argv.extend(["--mineru-artifact-dir", source_value.strip('"')])
    elif source_kind == "mineru_url":
        argv.extend(["--mineru-url", source_value])

    argv.extend(options.extra_args)
    return argv


def _positive_worker_count(value: int | str, label: str) -> int:
    try:
        count = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{label}必须是正整数。") from None
    if count < 1:
        raise ValueError(f"{label}必须是正整数。")
    return count


def build_process_command(options: GuiRunOptions, repo_root: Path | None = None) -> list[str]:
    root = repo_root or Path(__file__).resolve().parent.parent
    return [sys.executable, str(root / "docpage2md.py"), *build_cli_argv(options)]


def shell_quote_for_preview(parts: Iterable[str]) -> str:
    quoted: list[str] = []
    for part in parts:
        if not part:
            quoted.append('""')
        elif re.search(r"\s|[;&()]", part):
            quoted.append('"' + part.replace('"', '\\"') + '"')
        else:
            quoted.append(part)
    return " ".join(quoted)


def count_page_ranges(page_ranges: str, total_pages: int | None = None) -> int | None:
    text = page_ranges.strip().replace(" ", "")
    if not text:
        return total_pages
    if not PAGE_RANGE_RE.match(text):
        return None
    selected: set[int] = set()
    for part in text.split(","):
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text)
            end = int(end_text)
        else:
            start = end = int(part)
        if end < start:
            return None
        if total_pages is not None:
            end = min(end, total_pages)
        selected.update(range(start, end + 1))
    if total_pages is not None:
        selected = {page for page in selected if 1 <= page <= total_pages}
    return len(selected)


def estimate_pdf_pages(path: Path) -> int | None:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    count = len(re.findall(rb"/Type\s*/Page(?!s)\b", data))
    return count or None


def estimate_path_pages(path: Path, page_ranges: str = "") -> int | None:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        pages = estimate_pdf_pages(path)
        return count_page_ranges(page_ranges, pages) if pages else None
    if suffix in IMAGE_SUFFIXES:
        return 1
    return None


def source_paths_for_estimate(options: GuiRunOptions) -> list[Path]:
    source_kind = source_kind_key(options.source_kind)
    if source_kind == "input_file":
        return [Path(options.source_value.strip().strip('"'))]
    if source_kind == "input_files":
        return [Path(item) for item in split_multi_paths(options.source_value)]
    if source_kind == "input_folder":
        folder = Path(options.source_value.strip().strip('"'))
        if not folder.exists() or not folder.is_dir():
            return []
        iterator = folder.rglob("*") if options.recursive else folder.glob("*")
        return sorted(
            [path for path in iterator if path.is_file() and path.suffix.lower() in MINERU_SUPPORTED_SUFFIXES],
            key=lambda path: str(path).lower(),
        )
    return []


def selected_config_from_options(options: GuiRunOptions, base_config: AppConfig | None = None) -> AppConfig:
    config = apply_model_profile(base_config or AppConfig(), model_profile_key(options.model_profile))
    config = replace(
        config,
        engine_mode=engine_mode_key(options.engine_mode),
        document_type=document_type_key(options.document_type),
        model_profile=model_profile_key(options.model_profile),
        output_folder=options.output_folder,
        mineru_model_version=options.mineru_model_version,
        mineru_page_ranges=options.page_ranges or None,
        vision_batch_workers=_positive_worker_count(options.vision_workers, "Vision 并发数"),
        brain_batch_workers=_positive_worker_count(options.brain_workers, "Brain 并发数"),
    )
    if options.vision:
        config = replace(
            config,
            vision_provider=options.vision.provider,
            model_vision=options.vision.model,
            vision_base_url=options.vision.base_url,
            vision_api_key_env=options.vision.api_key_env,
        )
    if options.brain:
        config = replace(
            config,
            brain_provider=options.brain.provider,
            model_brain=options.brain.model,
            brain_base_url=options.brain.base_url,
            brain_api_key_env=options.brain.api_key_env,
        )
    return config


def estimate_gui_cost(options: GuiRunOptions, base_config: AppConfig | None = None) -> CostEstimateSummary:
    config = selected_config_from_options(options, base_config)
    engine_mode = engine_mode_key(options.engine_mode)
    rows: list[CostEstimateRow] = []
    source_kind = source_kind_key(options.source_kind)
    note_parts = ["只估算 Vision/Brain 模型 token 费用，不含 MinerU 平台费用。"]

    if engine_mode == "mineru_only":
        pages = _estimate_total_pages(options)
        return CostEstimateSummary(
            rows=[],
            total_pages=pages,
            total_input_tokens=0,
            total_output_tokens=0,
            total_cost=0.0,
            confidence="高",
            note="仅 MinerU 模式不会调用 Vision/Brain；这里只显示模型精修成本为 ¥0，不含 MinerU 平台费用。",
        )

    if source_kind == "mineru_artifact_dir":
        rows = [_estimate_artifact_cost_row(Path(options.source_value.strip().strip('"')), options, config)]
        note_parts.append("artifact 已存在，可按实际页数、裁剪块和图片尺寸估算，仍不含模型输出长度波动。")
    elif source_kind in {"input_file", "input_files", "input_folder"}:
        paths = source_paths_for_estimate(options)
        for path in paths:
            rows.append(_estimate_path_cost_row(path, options, config))
        if not rows:
            rows = [CostEstimateRow("待选择文件", None, None, 0, 0, None, "低", "还没有可估算的本地文件。")]
        note_parts.append("本地文件在 MinerU 返回裁剪块前只能按页数和经验 crop 数粗估。")
    else:
        rows = [CostEstimateRow("远程 URL", None, None, 0, 0, None, "低", "远程文件运行前无法读取页数。")]
        note_parts.append("远程 URL 运行前无法读取页数，等 MinerU 返回后进度会按真实页数更新。")

    known_pages = [row.pages for row in rows if row.pages is not None]
    total_pages = sum(known_pages) if len(known_pages) == len(rows) else None
    total_input = sum(row.input_tokens for row in rows)
    total_output = sum(row.output_tokens for row in rows)
    known_costs = [row.estimated_cost for row in rows if row.estimated_cost is not None]
    total_cost = sum(known_costs) if len(known_costs) == len(rows) else None
    confidence = _combine_confidence(row.confidence for row in rows)
    return CostEstimateSummary(
        rows=rows,
        total_pages=total_pages,
        total_input_tokens=total_input,
        total_output_tokens=total_output,
        total_cost=total_cost,
        confidence=confidence,
        note=" ".join(note_parts),
    )


def _estimate_total_pages(options: GuiRunOptions) -> int | None:
    units, _files = estimate_work_units(options)
    if units and all(unit is not None for unit in units):
        return sum(unit for unit in units if unit is not None)
    return None


def _estimate_path_cost_row(path: Path, options: GuiRunOptions, config: AppConfig) -> CostEstimateRow:
    pages = estimate_path_pages(path, options.page_ranges)
    if pages is None:
        return CostEstimateRow(path.name, None, None, 0, 0, None, "低", "无法在运行前确认页数。")
    if path.suffix.lower() in IMAGE_SUFFIXES:
        return _estimate_cost_from_counts(
            name=path.name,
            pages=pages,
            crop_blocks=1,
            image_tokens=[calculate_image_tokens(path)],
            config=config,
            confidence="中",
            note="本地图片按原图尺寸精确估算视觉 token；MinerU 若额外拆出裁剪块，实际费用会变化。",
        )
    crop_blocks = max(1, pages * ROUGH_PDF_CROP_BLOCKS_PER_PAGE)
    return _estimate_cost_from_counts(
        name=path.name,
        pages=pages,
        crop_blocks=crop_blocks,
        image_tokens=[ROUGH_CROP_IMAGE_TOKENS] * crop_blocks,
        config=config,
        confidence="中",
        note=f"MinerU 解析前无法知道真实裁剪块，按每页约 {ROUGH_PDF_CROP_BLOCKS_PER_PAGE} 个裁剪块粗估。",
    )


def _estimate_artifact_cost_row(path: Path, options: GuiRunOptions, config: AppConfig) -> CostEstimateRow:
    try:
        artifacts = discover_mineru_artifacts(path)
        document_ir = adapt_mineru_artifacts(artifacts, source_path=None, engine_mode=engine_mode_key(options.engine_mode))
    except Exception as exc:
        return CostEstimateRow(path.name, None, None, 0, 0, None, "低", f"无法读取 artifact：{exc}")
    pages = document_ir.get("pages") or []
    page_count = count_page_ranges(options.page_ranges, len(pages))
    if page_count is None:
        page_count = len(pages)
    selected_pages = _select_pages_by_range(pages, options.page_ranges)
    image_tokens: list[int] = []
    crop_blocks = 0
    for page in selected_pages:
        for block in page.get("blocks") or []:
            if block.get("type") not in VISION_COST_BLOCK_TYPES:
                continue
            image_path = resolve_artifact_image(
                artifacts,
                block.get("crop_ref") or block.get("image_path") or block.get("path") or block.get("image_ref"),
            )
            crop_blocks += 1
            image_tokens.append(calculate_image_tokens(image_path) if image_path else ROUGH_CROP_IMAGE_TOKENS)
    brain_input, brain_note = _estimate_brain_input_tokens_from_pages(selected_pages, config)
    return _estimate_cost_from_counts(
        name=path.name,
        pages=page_count,
        crop_blocks=crop_blocks,
        image_tokens=image_tokens,
        config=config,
        brain_input_tokens=brain_input,
        confidence="高",
        note="按已有 artifact 的实际块、图片尺寸和 Brain prompt 估算。" + (f" {brain_note}" if brain_note else ""),
    )


def _select_pages_by_range(pages: list[dict], page_ranges: str) -> list[dict]:
    text = page_ranges.strip().replace(" ", "")
    if not text or not PAGE_RANGE_RE.match(text):
        return pages
    wanted: set[int] = set()
    for part in text.split(","):
        if "-" in part:
            start, end = [int(value) for value in part.split("-", 1)]
        else:
            start = end = int(part)
        if start <= end:
            wanted.update(range(start, end + 1))
    return [
        page for index, page in enumerate(pages, start=1)
        if int(page.get("source_page") or index) in wanted
    ]


def _estimate_cost_from_counts(
    *,
    name: str,
    pages: int,
    crop_blocks: int,
    image_tokens: list[int],
    config: AppConfig,
    confidence: str,
    note: str,
    brain_input_tokens: int | None = None,
) -> CostEstimateRow:
    vision_record = _find_catalog_model(config.vision_provider, config.model_vision, config)
    brain_record = _find_catalog_model(config.brain_provider, config.model_brain, config)
    vision_input = sum(token + ROUGH_VISION_PROMPT_TOKENS for token in image_tokens)
    vision_output = crop_blocks * ROUGH_VISION_OUTPUT_TOKENS
    brain_input = brain_input_tokens if brain_input_tokens is not None else pages * ROUGH_BRAIN_INPUT_TOKENS_PER_PAGE
    brain_output = pages * ROUGH_BRAIN_OUTPUT_TOKENS_PER_PAGE
    vision_cost = estimate_text_cost(vision_input, vision_output, vision_record)
    if vision_cost is None:
        vision_cost = estimate_price(config.model_vision, vision_input, vision_output)
    brain_cost = estimate_text_cost(brain_input, brain_output, brain_record)
    if brain_cost is None:
        brain_cost = estimate_price(config.model_brain, brain_input, brain_output)
    cost = None if vision_cost is None or brain_cost is None else vision_cost + brain_cost
    return CostEstimateRow(
        name=name,
        pages=pages,
        crop_blocks=crop_blocks,
        input_tokens=vision_input + brain_input,
        output_tokens=vision_output + brain_output,
        estimated_cost=cost,
        confidence=confidence,
        note=note,
    )


def _estimate_brain_input_tokens_from_pages(pages: list[dict], config: AppConfig) -> tuple[int | None, str]:
    if config.brain_provider != "deepseek":
        return None, "Brain 非 DeepSeek，文本 token 仍按经验值估算。"
    if not pages:
        return 0, "DeepSeek 输入 token 使用内置 tokenizer 估算。"
    try:
        from .hybrid_enrichment import _brain_ops_prompt
    except Exception:
        return None, "DeepSeek tokenizer 可用，但 Brain prompt 构造器不可用，已退回经验值。"

    total = 0
    for index, page in enumerate(pages):
        prompt = _brain_ops_prompt(page, _context_window_for_cost(pages, index))
        total += estimate_deepseek_chat_tokens([{"role": "user", "content": prompt}])
    return total, "DeepSeek 输入 token 使用内置 tokenizer 按真实 Brain prompt 估算。"


def _context_window_for_cost(pages: list[dict], page_index: int, radius: int = 2) -> list[dict]:
    start = max(0, page_index - radius)
    end = min(len(pages), page_index + radius + 1)
    return [pages[index] for index in range(start, end)]


def _find_catalog_model(provider: str, model_id: str, config: AppConfig):
    records = load_model_catalog(prefer_cache=True, cache_path=config.model_cache_path, curated=True)
    for item in load_third_party_models(config):
        records.append(registry_item_to_model_record(item))
    for record in records:
        if record.provider == provider and record.model_id == model_id:
            return record
    return None


def _combine_confidence(values: Iterable[str]) -> str:
    order = {"低": 0, "中": 1, "高": 2}
    seen = list(values)
    if not seen:
        return "低"
    return min(seen, key=lambda value: order.get(value, 0))


def estimate_work_units(options: GuiRunOptions) -> tuple[list[int | None], int]:
    source_kind = source_kind_key(options.source_kind)
    if source_kind in {"mineru_url", "mineru_artifact_dir"}:
        return [None], 1
    paths = source_paths_for_estimate(options)
    units = [estimate_path_pages(path, options.page_ranges) for path in paths]
    return units, max(len(paths), 1)


def format_duration(seconds: float | None) -> str:
    if seconds is None:
        return "--"
    seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class GuiProgressTracker:
    def __init__(self) -> None:
        self.reset()

    def reset(self, options: GuiRunOptions | None = None) -> ProgressSnapshot:
        self.started_at = time.monotonic()
        self.last_elapsed = 0.0
        self.stage = "就绪"
        self.detail = "等待开始"
        self.files_total = 1
        self.file_units: list[int | None] = [None]
        self.total_units: int | None = None
        self.current_file_index = -1
        self.completed_files = 0
        self.completed_units_before_current = 0
        self.current_estimated_units: int | None = None
        self.current_pages_total: int | None = None
        self.current_pages_done = 0
        self.current_page = 0
        self.current_doc_name = ""
        self.current_doc_started = False
        self.current_doc_start_elapsed: float | None = None
        self.page_started_elapsed: dict[int, float] = {}
        self.completed_pages: set[int] = set()
        self.page_duration_samples: list[float] = []
        self.saw_hybrid_pages = False
        self.done = False
        self.failed = False
        if options:
            self.file_units, self.files_total = estimate_work_units(options)
            if self.file_units and all(unit is not None for unit in self.file_units):
                self.total_units = sum(unit for unit in self.file_units if unit is not None)
            self.stage = "准备运行"
            if self.total_units:
                self.detail = f"预计 {self.files_total} 个文件，{self.total_units} 页"
            else:
                self.detail = f"预计 {self.files_total} 个文件，等待 MinerU 返回页数"
        return self.snapshot()

    def observe_line(self, line: str) -> ProgressSnapshot:
        elapsed, message = self._parse_line(line)
        self.last_elapsed = elapsed

        if (
            "Submitting local files to MinerU" in message
            or "Uploading file to MinerU" in message
            or "正在上传本地文件到 MinerU" in message
            or "正在上传文件" in message
        ):
            self.stage = "上传到 MinerU"
            self.detail = _compact_message(message)
        elif "MinerU batch submitted" in message or "MinerU 批量任务已提交" in message:
            match = MINERU_BATCH_SUBMITTED_RE.search(message) or ZH_MINERU_BATCH_SUBMITTED_RE.search(message)
            if match:
                self.files_total = max(self.files_total, int(match.group(1)))
            self.stage = "等待 MinerU 解析"
            self.detail = _compact_message(message)
        elif (
            "MinerU batch poll" in message
            or "Query MinerU batch" in message
            or "等待 MinerU 解析" in message
            or "正在查询 MinerU" in message
        ):
            self.stage = "等待 MinerU 解析"
            self.detail = _compact_message(message)
        elif (
            message.startswith("Downloading MinerU zip:")
            or message.startswith("Processing existing MinerU artifact:")
            or message.startswith("正在下载 MinerU 结果压缩包")
            or message.startswith("正在处理已有 MinerU artifact")
        ):
            self._begin_document(message)
            self.stage = "下载 MinerU 结果" if ("Downloading" in message or "下载" in message) else "处理 artifact"
            self.detail = _compact_message(message)
        elif message.startswith("Processing MinerU artifact into Markdown:") or message.startswith("正在把 MinerU artifact 转成 Markdown"):
            if not self.current_doc_started:
                self._begin_document(message)
            self.stage = "解析 MinerU artifact"
            self.detail = _compact_message(message)
        elif message.startswith("Output directory ready:") or message.startswith("输出目录已准备："):
            self.current_doc_name = Path(_message_value_after_colon(message)).name
            self.stage = "准备输出目录"
            self.detail = self._document_detail()
        elif match := (DOCUMENT_READY_RE.search(message) or ZH_DOCUMENT_READY_RE.search(message)):
            if not self.current_doc_started:
                self._begin_document(message)
            pages = int(match.group(1))
            self._set_current_total_pages(pages)
            self.stage = "DocumentIR 已就绪"
            self.detail = self._document_detail()
        elif "Hybrid enrichment start" in message or "开始混合精修" in message:
            self.stage = "Hybrid 精修"
            self.detail = self._document_detail()
        elif match := (HYBRID_PAGE_START_RE.search(message) or ZH_HYBRID_PAGE_START_RE.search(message)):
            if not self.current_doc_started:
                self._begin_document(message)
            page = int(match.group(1))
            total = int(match.group(2))
            self.saw_hybrid_pages = True
            self._set_current_total_pages(total)
            self.current_page = page
            self.page_started_elapsed[page] = elapsed
            self.stage = f"Hybrid 第 {page}/{total} 页"
            self.detail = "Crop Vision / Brain 精修中"
        elif match := (CROP_VISION_START_RE.search(message) or ZH_CROP_VISION_START_RE.search(message)):
            slide = int(match.group(1))
            block_id = match.group(2)
            total = self.current_pages_total or "?"
            self.stage = f"第 {slide}/{total} 页 Vision"
            self.detail = f"裁剪块 {block_id}"
        elif match := (HYBRID_PAGE_BRAIN_START_RE.search(message) or ZH_HYBRID_PAGE_BRAIN_START_RE.search(message)):
            slide = int(match.group(1))
            total = self.current_pages_total or "?"
            self.stage = f"第 {slide}/{total} 页 Brain"
            self.detail = "上下文精修中"
        elif match := (HYBRID_PAGE_REFINER_DONE_RE.search(message) or ZH_HYBRID_PAGE_REFINER_DONE_RE.search(message)):
            slide = int(match.group(1))
            self._complete_page(slide, elapsed)
            total = self.current_pages_total or "?"
            self.stage = f"第 {slide}/{total} 页完成"
            self.detail = self._document_detail()
        elif match := (PAGE_RENDERED_RE.search(message) or ZH_PAGE_RENDERED_RE.search(message)):
            slide = int(match.group(1))
            status = match.group(2)
            if not self.saw_hybrid_pages:
                self._complete_page(slide, elapsed)
            self.stage = f"渲染第 {slide} 页"
            self.detail = f"Markdown status={status}"
        elif "Merging per-page Markdown" in message or "正在合并每页 Markdown" in message:
            self.stage = "合并 Markdown"
            self.detail = self._document_detail()
        elif message.startswith("Wrote run report:") or message.startswith("运行报告已写入："):
            if self.current_pages_total:
                self.current_pages_done = self.current_pages_total
            self.stage = "写入报告"
            self.detail = self._document_detail()
        elif match := (MINERU_PROCESSED_RE.search(message) or ZH_MINERU_PROCESSED_RE.search(message)):
            pages = int(match.group(1))
            self._set_current_total_pages(pages)
            self._finish_document()
            self.stage = "文件处理完成"
            self.detail = f"{self.completed_files}/{self.files_total} 个文件完成"
        elif message.startswith("MinerU batch complete:") or message.startswith("MinerU 批量任务完成："):
            self.completed_files = self.files_total
            self.done = True
            self.stage = "全部完成"
            self.detail = message
        elif "failed" in message.lower() or "error" in message.lower() or "失败" in message:
            self.stage = "运行异常"
            self.detail = _compact_message(message)
        return self.snapshot()

    def finish(self, ok: bool) -> ProgressSnapshot:
        self.done = ok
        self.failed = not ok
        if ok:
            self.completed_files = self.files_total
            if self.total_units is not None:
                self.completed_units_before_current = self.total_units
            self.current_pages_done = self.current_pages_total or self.current_pages_done
            self.stage = "完成"
            self.detail = "所有任务已结束"
        else:
            self.stage = "失败"
            self.detail = "进程已退出，请查看日志"
        return self.snapshot()

    def snapshot(self) -> ProgressSnapshot:
        elapsed = self._elapsed_now()
        percent = self._percent()
        return ProgressSnapshot(
            percent=percent,
            stage=self.stage,
            detail=self.detail,
            eta=f"剩余 {format_duration(self._eta_seconds())}",
            elapsed=f"已用 {format_duration(elapsed)}",
        )

    def _parse_line(self, line: str) -> tuple[float, str]:
        match = LOG_MESSAGE_RE.search(line)
        if match:
            return float(match.group(1)), match.group(2).strip()
        return self._elapsed_now(), line.strip()

    def _elapsed_now(self) -> float:
        return self.last_elapsed or (time.monotonic() - self.started_at)

    def _begin_document(self, message: str) -> None:
        if self.current_doc_started and self.current_pages_total and self.current_pages_done >= self.current_pages_total:
            self._finish_document()
        if not self.current_doc_started or self.current_pages_total:
            self.current_file_index = min(self.current_file_index + 1, self.files_total - 1)
        self.current_doc_started = True
        self.current_doc_start_elapsed = self.last_elapsed
        self.current_pages_total = None
        self.current_pages_done = 0
        self.current_page = 0
        self.page_started_elapsed = {}
        self.completed_pages = set()
        self.saw_hybrid_pages = False
        if 0 <= self.current_file_index < len(self.file_units):
            self.current_estimated_units = self.file_units[self.current_file_index]
        else:
            self.current_estimated_units = None
        self.current_doc_name = _source_name_from_message(message)

    def _set_current_total_pages(self, pages: int) -> None:
        if pages <= 0:
            return
        if self.current_file_index < 0:
            self.current_file_index = 0
        old_estimate = self.current_estimated_units
        self.current_pages_total = pages
        self.current_estimated_units = pages
        if self.total_units is not None and old_estimate is not None:
            self.total_units += pages - old_estimate

    def _complete_page(self, page: int, elapsed: float) -> None:
        started = self.page_started_elapsed.pop(page, None)
        if started is not None and elapsed >= started:
            duration = elapsed - started
            if duration > 0:
                self.page_duration_samples.append(duration)
        self.completed_pages.add(page)
        self.current_pages_done = len(self.completed_pages)
        self.current_page = max(self.current_page, page)

    def _finish_document(self) -> None:
        if not self.current_doc_started:
            return
        units = self.current_pages_total or self.current_estimated_units or max(self.current_pages_done, 1)
        self.completed_units_before_current += units
        self.completed_files = min(self.files_total, max(self.completed_files, self.current_file_index + 1))
        self.current_doc_started = False
        self.current_pages_done = 0
        self.current_pages_total = None
        self.current_estimated_units = None
        self.current_doc_start_elapsed = None
        self.page_started_elapsed = {}
        self.completed_pages = set()

    def _percent(self) -> float:
        if self.done:
            return 100.0
        if self.total_units:
            completed = self.completed_units_before_current
            if self.current_doc_started:
                completed += min(self.current_pages_done, self.current_pages_total or self.current_pages_done)
            return _clamp_percent(100.0 * completed / self.total_units)
        if self.current_doc_started and self.current_pages_total:
            current_fraction = min(self.current_pages_done, self.current_pages_total) / self.current_pages_total
            return _clamp_percent(100.0 * (self.completed_files + current_fraction) / max(self.files_total, 1))
        return _clamp_percent(100.0 * self.completed_files / max(self.files_total, 1))

    def _eta_seconds(self) -> float | None:
        if self.done:
            return 0.0
        if self.failed:
            return None
        if not self.page_duration_samples:
            return None
        if self.current_doc_started and self.current_pages_total and self.current_pages_done > 0 and self.current_doc_start_elapsed is not None:
            elapsed_in_doc = max(0.0, self.last_elapsed - self.current_doc_start_elapsed)
            remaining_pages = max(0, self.current_pages_total - self.current_pages_done)
            return max(0.0, elapsed_in_doc / self.current_pages_done * remaining_pages)

        avg = sum(self.page_duration_samples) / len(self.page_duration_samples)
        if self.total_units:
            completed_units = self.completed_units_before_current
            if self.current_doc_started:
                completed_units += self.current_pages_done
            remaining_units = max(0, self.total_units - completed_units)
        elif self.current_doc_started and self.current_pages_total:
            remaining_units = max(0, self.current_pages_total - self.current_pages_done)
        else:
            return None
        remaining = avg * remaining_units
        for started in self.page_started_elapsed.values():
            remaining -= min(max(0.0, self.last_elapsed - started), avg)
        return max(0.0, remaining)

    def _document_detail(self) -> str:
        file_part = f"文件 {max(self.current_file_index + 1, 1)}/{self.files_total}"
        page_part = ""
        if self.current_pages_total:
            page_part = f"，页 {self.current_pages_done}/{self.current_pages_total}"
        name_part = f"，{self.current_doc_name}" if self.current_doc_name else ""
        return f"{file_part}{page_part}{name_part}"


def _clamp_percent(value: float) -> float:
    return max(0.0, min(100.0, value))


def _source_name_from_message(message: str) -> str:
    if "source=" in message:
        source = message.split("source=", 1)[1].split(",", 1)[0].strip()
        return Path(source).name or source
    if ":" in message or "：" in message:
        value = _message_value_after_colon(message)
        return Path(value).name or value
    return ""


def _message_value_after_colon(message: str) -> str:
    if "：" in message:
        return message.split("：", 1)[1].strip()
    if ":" in message:
        return message.split(":", 1)[1].strip()
    return message.strip()


def _compact_message(message: str, limit: int = 120) -> str:
    message = " ".join(message.split())
    return message if len(message) <= limit else message[: limit - 3] + "..."


class ModelCatalogView:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.records = load_model_catalog(prefer_cache=True, cache_path=config.model_cache_path)

    def official_models(self, role: str) -> list[dict]:
        if role == ROLE_VISION:
            records = filter_vision_models(self.records)
            records.sort(key=lambda rec: (vision_recommendation_tier(rec), rec.model_id))
        else:
            records = [
                rec for rec in filter_brain_models(self.records)
                if ROLE_BRAIN in getattr(rec, "stage_suitable", []) or rec.openai_text_status == "ok"
            ]
        result = []
        for rec in records[:120]:
            result.append(
                {
                    "source": "official",
                    "name": rec.model_id,
                    "provider": rec.provider,
                    "model": rec.model_id,
                    "base_url": self._provider_base_url(rec.provider, role),
                    "api_key_env": self._provider_api_key_env(rec.provider, role),
                    "input_price": rec.input_price,
                    "output_price": rec.output_price,
                    "supports_vision": rec.supports_vision,
                }
            )
        return result

    def third_party_models(self, role: str) -> list[dict]:
        return [
            {
                "source": "third_party",
                "name": item.get("name") or item.get("model_id"),
                "provider": item.get("provider") or "openai_compatible",
                "model": item.get("model_id") or "",
                "base_url": item.get("base_url") or "",
                "api_key_env": item.get("api_key_env") or "OPENAI_API_KEY",
                "input_price": item.get("input_price"),
                "output_price": item.get("output_price"),
                "supports_vision": item.get("supports_vision"),
                "id": item.get("id"),
            }
            for item in filter_registry_models(load_third_party_models(self.config), role)
        ]

    def all_models(self, role: str) -> list[dict]:
        return self.official_models(role) + self.third_party_models(role)

    def _provider_base_url(self, provider: str, role: str) -> str:
        if provider == "deepseek":
            return "https://api.deepseek.com"
        if provider in {"dashscope", "dashscope_openai"}:
            return self.config.openai_base_url
        return self.config.vision_base_url if role == ROLE_VISION else self.config.brain_base_url

    def _provider_api_key_env(self, provider: str, role: str) -> str:
        if provider == "deepseek":
            return "DEEPSEEK_API_KEY"
        if provider in {"dashscope", "dashscope_openai"}:
            return "DASHSCOPE_API_KEY"
        return self.config.vision_api_key_env if role == ROLE_VISION else self.config.brain_api_key_env


class DocPage2MdGui:
    def __init__(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        self.tk = tk
        self.ttk = ttk
        self.root = tk.Tk()
        self.root.title("DocPage2MD 工作台")
        self.root.geometry("1240x900")
        self.root.minsize(1040, 760)

        self.repo_root = Path(__file__).resolve().parent.parent
        self.base_config = AppConfig(output_folder=str((self.repo_root / "markdown_output").resolve()))
        self.catalog = ModelCatalogView(self.base_config)
        self._tree_item_data: dict[str, dict] = {}
        self.output_queue: queue.Queue[tuple[str, str | int]] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None
        self.reader_thread: threading.Thread | None = None
        self.progress_tracker = GuiProgressTracker()
        self.log_window = None
        self.log_window_text = None
        self.log_buffer: list[str] = []
        self._syncing_models = False

        default_vision, default_brain = default_model_selection("balanced", self.base_config)
        self.document_type = tk.StringVar(value=DOCUMENT_PRESETS["handwritten_notes"][0])
        self.engine_mode = tk.StringVar(value=ENGINE_MODE_LABELS["hybrid"])
        self.model_profile = tk.StringVar(value=MODEL_PROFILE_LABELS["balanced"])
        self.source_kind = tk.StringVar(value=SOURCE_LABELS["input_files"])
        self.source_value = tk.StringVar(value="")
        self.output_folder = tk.StringVar(value=str((self.repo_root / "markdown_output" / "gui_full_pdf_smoke").resolve()))
        self.session_name = tk.StringVar(value="")
        self.page_ranges = tk.StringVar(value="")
        self.mineru_model_version = tk.StringVar(value="vlm")
        self.recursive = tk.BooleanVar(value=False)
        self.vision_workers = tk.StringVar(value=str(self.base_config.vision_batch_workers))
        self.brain_workers = tk.StringVar(value=str(self.base_config.brain_batch_workers))
        self.vision_provider = tk.StringVar(value=default_vision.provider)
        self.vision_model = tk.StringVar(value=default_vision.model)
        self.vision_base_url = tk.StringVar(value=default_vision.base_url)
        self.vision_api_key_env = tk.StringVar(value=default_vision.api_key_env)
        self.brain_provider = tk.StringVar(value=default_brain.provider)
        self.brain_model = tk.StringVar(value=default_brain.model)
        self.brain_base_url = tk.StringVar(value=default_brain.base_url)
        self.brain_api_key_env = tk.StringVar(value=default_brain.api_key_env)
        self.status_text = tk.StringVar(value="就绪")
        self.progress_percent = tk.DoubleVar(value=0.0)
        self.progress_stage = tk.StringVar(value="就绪")
        self.progress_detail = tk.StringVar(value="等待开始")
        self.progress_eta = tk.StringVar(value="剩余 --")
        self.progress_elapsed = tk.StringVar(value="已用 00:00")
        self.command_preview = tk.StringVar(value="")
        self.run_summary_text = tk.StringVar(value="")
        self.cost_summary_text = tk.StringVar(value="成本估算：点击“刷新成本估算”后显示。")
        self.model_summary_text = tk.StringVar(value="")

        self._configure_style()
        self._build_ui()
        self._bind_updates()
        self._apply_preset()
        self._refresh_model_status()
        self._refresh_command_preview()
        self._refresh_runtime_summary()
        self._refresh_cost_estimate(silent=True)
        self.root.after(100, self._drain_output_queue)

    def run(self) -> int:
        self.root.mainloop()
        return 0

    def _build_ui(self) -> None:
        tk = self.tk
        ttk = self.ttk

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        notebook = ttk.Notebook(self.root)
        notebook.grid(row=0, column=0, sticky="nsew")

        run_tab = ttk.Frame(notebook, padding=12)
        model_tab = ttk.Frame(notebook, padding=12)
        notebook.add(run_tab, text="运行")
        notebook.add(model_tab, text="模型管理")
        self._build_run_tab(run_tab)
        self._build_model_tab(model_tab)

    def _configure_style(self) -> None:
        style = self.ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except self.tk.TclError:
            pass
        style.configure(".", font=("Microsoft YaHei UI", 10))
        style.configure("TNotebook.Tab", padding=(16, 8))
        style.configure("TLabelframe", padding=8)
        style.configure("TLabelframe.Label", font=("Microsoft YaHei UI", 10, "bold"))
        style.configure("Primary.TButton", font=("Microsoft YaHei UI", 10, "bold"))

    def _build_run_tab(self, parent) -> None:
        tk = self.tk
        ttk = self.ttk
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(6, weight=1)

        top = ttk.LabelFrame(parent, text="1. 任务预设", padding=10)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top.columnconfigure(1, weight=1)
        top.columnconfigure(3, weight=1)

        ttk.Label(top, text="文档类型").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            top,
            textvariable=self.document_type,
            values=[item[0] for item in DOCUMENT_PRESETS.values()],
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(top, text="处理模式").grid(row=0, column=2, sticky="w", padx=(14, 8), pady=4)
        ttk.Combobox(
            top,
            textvariable=self.engine_mode,
            values=[ENGINE_MODE_LABELS["hybrid"], ENGINE_MODE_LABELS["mineru_only"]],
            state="readonly",
        ).grid(row=0, column=3, sticky="ew", pady=4)
        ttk.Label(top, text="模型档位").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            top,
            textvariable=self.model_profile,
            values=[MODEL_PROFILE_LABELS[key] for key in ("cheap", "balanced", "accurate", "manual")],
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(top, text="MinerU 模型").grid(row=1, column=2, sticky="w", padx=(14, 8), pady=4)
        ttk.Combobox(
            top,
            textvariable=self.mineru_model_version,
            values=["vlm", "pipeline", "MinerU-HTML"],
            state="readonly",
        ).grid(row=1, column=3, sticky="ew", pady=4)
        ttk.Label(
            top,
            textvariable=self.run_summary_text,
            wraplength=1080,
            justify="left",
        ).grid(row=2, column=0, columnspan=4, sticky="ew", pady=(8, 0))

        source = ttk.LabelFrame(parent, text="2. 输入来源", padding=10)
        source.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        source.columnconfigure(1, weight=1)
        ttk.Label(source, text="来源").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(source, textvariable=self.source_kind, values=list(SOURCE_LABELS.values()), state="readonly").grid(
            row=0, column=1, sticky="ew", pady=4
        )
        ttk.Button(source, text="选择文件/目录", command=self._browse_source).grid(row=0, column=2, padx=(8, 0), pady=4)
        ttk.Entry(source, textvariable=self.source_value).grid(row=1, column=0, columnspan=3, sticky="ew", pady=4)
        ttk.Checkbutton(source, text="文件夹输入时递归扫描子文件夹", variable=self.recursive).grid(
            row=2, column=0, columnspan=3, sticky="w"
        )

        out = ttk.LabelFrame(parent, text="3. 输出、页码、并发", padding=10)
        out.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        out.columnconfigure(1, weight=1)
        out.columnconfigure(3, weight=1)
        ttk.Label(out, text="输出目录").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(out, textvariable=self.output_folder).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(out, text="选择", command=self._browse_output).grid(row=0, column=2, padx=(8, 0), pady=4)
        ttk.Label(out, text="任务名").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(out, textvariable=self.session_name).grid(row=1, column=1, sticky="ew", pady=4)
        ttk.Label(out, text="页码范围").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(out, textvariable=self.page_ranges).grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(out, text="空=全量，例如 1-10 或 2,4-6").grid(row=2, column=2, sticky="w", padx=(8, 0), pady=4)
        ttk.Label(out, text="Vision 并发").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(out, textvariable=self.vision_workers, width=10).grid(row=3, column=1, sticky="w", pady=4)
        ttk.Label(out, text="Brain 并发").grid(row=3, column=2, sticky="w", padx=(8, 8), pady=4)
        ttk.Entry(out, textvariable=self.brain_workers, width=10).grid(row=3, column=3, sticky="w", pady=4)
        ttk.Label(out, text="默认 60/60，会对 MinerU 返回后的裁剪块和页面精修并行执行。").grid(
            row=4, column=0, columnspan=4, sticky="w", pady=(4, 0)
        )

        command = ttk.LabelFrame(parent, text="4. 成本估算与命令预览", padding=10)
        command.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        command.columnconfigure(0, weight=1)
        ttk.Label(command, textvariable=self.cost_summary_text, wraplength=1080, justify="left").grid(
            row=0, column=0, sticky="ew"
        )
        command_buttons = ttk.Frame(command)
        command_buttons.grid(row=0, column=1, sticky="ne", padx=(8, 0))
        ttk.Button(command_buttons, text="刷新成本估算", command=self._refresh_cost_estimate).grid(row=0, column=0)
        ttk.Entry(command, textvariable=self.command_preview, state="readonly").grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(8, 0)
        )

        progress = ttk.LabelFrame(parent, text="5. 运行进度", padding=10)
        progress.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        progress.columnconfigure(0, weight=1)
        ttk.Progressbar(progress, variable=self.progress_percent, maximum=100).grid(row=0, column=0, columnspan=4, sticky="ew")
        ttk.Label(progress, textvariable=self.progress_stage).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(progress, textvariable=self.progress_elapsed).grid(row=1, column=1, sticky="e", padx=(8, 0), pady=(6, 0))
        ttk.Label(progress, textvariable=self.progress_eta).grid(row=1, column=2, sticky="e", padx=(8, 0), pady=(6, 0))
        self.progress_percent_label = self.tk.StringVar(value="0%")
        ttk.Label(progress, textvariable=self.progress_percent_label).grid(row=1, column=3, sticky="e", padx=(8, 0), pady=(6, 0))
        ttk.Label(progress, textvariable=self.progress_detail).grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))

        log_frame = ttk.LabelFrame(parent, text="运行日志", padding=10)
        log_frame.grid(row=5, column=0, sticky="nsew", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)
        log_tools = ttk.Frame(log_frame)
        log_tools.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        log_tools.columnconfigure(0, weight=1)
        ttk.Label(log_tools, text="GUI 显示中文进度；完整中文日志会写入输出目录的 process.log。").grid(row=0, column=0, sticky="w")
        ttk.Button(log_tools, text="放大日志", command=self._open_log_window).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(log_tools, text="清空显示", command=self._clear_log).grid(row=0, column=2, padx=(8, 0))
        self.log_text = tk.Text(log_frame, wrap="word", height=14, state="disabled", font=("Consolas", 10))
        self.log_text.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)

        bottom = ttk.Frame(parent)
        bottom.grid(row=6, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        ttk.Label(bottom, textvariable=self.status_text).grid(row=0, column=0, sticky="w")
        self.run_button = ttk.Button(bottom, text="开始处理", command=self._start_process, style="Primary.TButton")
        self.run_button.grid(row=0, column=1, padx=(8, 0))
        self.stop_button = ttk.Button(bottom, text="停止", command=self._stop_process, state="disabled")
        self.stop_button.grid(row=0, column=2, padx=(8, 0))
        ttk.Button(bottom, text="打开输出目录", command=self._open_output_folder).grid(row=0, column=3, padx=(8, 0))

    def _build_model_tab(self, parent) -> None:
        ttk = self.ttk
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(3, weight=1)

        self.vision_status = self.tk.StringVar(value="")
        self.brain_status = self.tk.StringVar(value="")

        current = ttk.LabelFrame(parent, text="当前生效模型", padding=10)
        current.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        current.columnconfigure(0, weight=1)
        current.columnconfigure(1, weight=1)
        vision_card = ttk.LabelFrame(current, text="Vision：图片、裁剪块、图表识别", padding=10)
        brain_card = ttk.LabelFrame(current, text="Brain：页面结构精修、上下文修正", padding=10)
        vision_card.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        brain_card.grid(row=0, column=1, sticky="ew", padx=(6, 0))
        self._build_current_model_editor(
            vision_card,
            provider_var=self.vision_provider,
            model_var=self.vision_model,
            base_url_var=self.vision_base_url,
            api_key_env_var=self.vision_api_key_env,
            status_var=self.vision_status,
        )
        self._build_current_model_editor(
            brain_card,
            provider_var=self.brain_provider,
            model_var=self.brain_model,
            base_url_var=self.brain_base_url,
            api_key_env_var=self.brain_api_key_env,
            status_var=self.brain_status,
        )
        controls = ttk.Frame(current)
        controls.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        controls.columnconfigure(0, weight=1)
        ttk.Label(
            controls,
            textvariable=self.model_summary_text,
            wraplength=820,
            justify="left",
        ).grid(row=0, column=0, sticky="w")
        ttk.Button(controls, text="按当前档位重置", command=self._reset_models_from_profile).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(controls, text="检查 Key", command=self._refresh_model_status).grid(row=0, column=2, padx=(8, 0))
        ttk.Button(controls, text="设置 Key", command=self._prompt_save_key).grid(row=0, column=3, padx=(8, 0))
        ttk.Button(controls, text="保存为默认", command=self._save_selected_models).grid(row=0, column=4, padx=(8, 0))

        vision_box = ttk.LabelFrame(parent, text="官方/第三方 Vision 候选", padding=10)
        brain_box = ttk.LabelFrame(parent, text="官方/第三方 Brain 候选", padding=10)
        vision_box.grid(row=1, column=0, sticky="nsew", padx=(0, 5), pady=(0, 10))
        brain_box.grid(row=1, column=1, sticky="nsew", padx=(5, 0), pady=(0, 10))
        self.vision_list = self._build_model_list(vision_box, ROLE_VISION)
        self.brain_list = self._build_model_list(brain_box, ROLE_BRAIN)

        editor = ttk.LabelFrame(parent, text="第三方模型管理", padding=10)
        editor.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        for i in range(7):
            editor.columnconfigure(i, weight=1 if i in (1, 3, 5) else 0)
        self.third_party_id = self.tk.StringVar(value="")
        self.tp_name = self.tk.StringVar(value="")
        self.tp_provider = self.tk.StringVar(value="openai_compatible")
        self.tp_model = self.tk.StringVar(value="")
        self.tp_base_url = self.tk.StringVar(value="https://api.openai.com/v1")
        self.tp_api_key_env = self.tk.StringVar(value="OPENAI_API_KEY")
        self.tp_roles = self.tk.StringVar(value="both")
        self.tp_supports_vision = self.tk.BooleanVar(value=True)
        self.tp_input_price = self.tk.StringVar(value="")
        self.tp_output_price = self.tk.StringVar(value="")
        ttk.Label(editor, text="名称").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Entry(editor, textvariable=self.tp_name).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(editor, text="提供商").grid(row=0, column=2, sticky="w", padx=(8, 6), pady=4)
        ttk.Combobox(editor, textvariable=self.tp_provider, values=SUPPORTED_PROVIDERS, state="readonly").grid(row=0, column=3, sticky="ew", pady=4)
        ttk.Label(editor, text="模型 ID").grid(row=0, column=4, sticky="w", padx=(8, 6), pady=4)
        ttk.Entry(editor, textvariable=self.tp_model).grid(row=0, column=5, sticky="ew", pady=4)
        ttk.Label(editor, text="Base URL").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Entry(editor, textvariable=self.tp_base_url).grid(row=1, column=1, columnspan=3, sticky="ew", pady=4)
        ttk.Label(editor, text="Key 环境变量").grid(row=1, column=4, sticky="w", padx=(8, 6), pady=4)
        ttk.Entry(editor, textvariable=self.tp_api_key_env).grid(row=1, column=5, sticky="ew", pady=4)
        ttk.Label(editor, text="角色").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Combobox(editor, textvariable=self.tp_roles, values=["vision", "brain", "both"], state="readonly").grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Checkbutton(editor, text="支持图片输入", variable=self.tp_supports_vision).grid(row=2, column=2, sticky="w", pady=4)
        ttk.Label(editor, text="输入价 元/M").grid(row=2, column=3, sticky="w", padx=(8, 6), pady=4)
        ttk.Entry(editor, textvariable=self.tp_input_price).grid(row=2, column=4, sticky="ew", pady=4)
        ttk.Label(editor, text="输出价 元/M").grid(row=2, column=5, sticky="w", padx=(8, 6), pady=4)
        ttk.Entry(editor, textvariable=self.tp_output_price).grid(row=2, column=6, sticky="ew", pady=4)
        actions = ttk.Frame(editor)
        actions.grid(row=3, column=0, columnspan=7, sticky="ew", pady=(8, 0))
        actions.columnconfigure(0, weight=1)
        ttk.Label(actions, text="只保存环境变量名，不保存 API Key 明文。验证结果会写回 log/third_party_models.json。").grid(row=0, column=0, sticky="w")
        ttk.Button(actions, text="保存/更新", command=self._save_third_party_model).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(actions, text="验证", command=self._verify_third_party_model).grid(row=0, column=2, padx=(8, 0))
        ttk.Button(actions, text="批量导入", command=self._bulk_import_dialog).grid(row=0, column=3, padx=(8, 0))
        ttk.Button(actions, text="删除选中", command=self._delete_selected_third_party_model).grid(row=0, column=4, padx=(8, 0))

        self.model_message = self.tk.StringVar(value="")
        ttk.Label(parent, textvariable=self.model_message).grid(row=3, column=0, columnspan=2, sticky="nw")

    def _build_current_model_editor(self, parent, *, provider_var, model_var, base_url_var, api_key_env_var, status_var) -> None:
        ttk = self.ttk
        parent.columnconfigure(1, weight=1)
        ttk.Label(parent, text="提供商").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=3)
        ttk.Combobox(parent, textvariable=provider_var, values=SUPPORTED_PROVIDERS, state="readonly").grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Label(parent, text="模型 ID").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=3)
        ttk.Entry(parent, textvariable=model_var).grid(row=1, column=1, sticky="ew", pady=3)
        ttk.Label(parent, text="Base URL").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=3)
        ttk.Entry(parent, textvariable=base_url_var).grid(row=2, column=1, sticky="ew", pady=3)
        ttk.Label(parent, text="Key 环境变量").grid(row=3, column=0, sticky="w", padx=(0, 6), pady=3)
        ttk.Entry(parent, textvariable=api_key_env_var).grid(row=3, column=1, sticky="ew", pady=3)
        ttk.Label(parent, textvariable=status_var, foreground="#0f766e").grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

    def _build_model_list(self, parent, role: str):
        ttk = self.ttk
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        columns = ("source", "provider", "model", "price", "key")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=11)
        for col, label, width in [
            ("source", "来源", 80),
            ("provider", "提供商", 110),
            ("model", "模型", 240),
            ("price", "价格 元/M", 120),
            ("key", "Key 环境变量", 130),
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scroll.set)
        ttk.Button(parent, text="选择", command=lambda: self._choose_model_from_tree(role, tree)).grid(row=1, column=0, sticky="e", pady=(8, 0))
        self._populate_model_tree(tree, role)
        tree.bind("<Double-1>", lambda _event: self._choose_model_from_tree(role, tree))
        tree.bind("<<TreeviewSelect>>", lambda _event: self._load_third_party_editor_from_tree(role, tree))
        return tree

    def _populate_model_tree(self, tree, role: str) -> None:
        for item_id in tree.get_children():
            tree.delete(item_id)
        for index, item in enumerate(self.catalog.all_models(role), start=1):
            iid = f"{role}-{index}"
            self._tree_item_data[iid] = item
            tree.insert(
                "",
                "end",
                iid=iid,
                values=(
                    "官方" if item["source"] == "official" else "第三方",
                    item["provider"],
                    item["model"],
                    _price_brief(item.get("input_price"), item.get("output_price")),
                    item["api_key_env"],
                ),
            )

    def _bind_updates(self) -> None:
        for var in (
            self.engine_mode,
            self.model_profile,
            self.source_kind,
            self.source_value,
            self.output_folder,
            self.session_name,
            self.page_ranges,
            self.mineru_model_version,
            self.recursive,
            self.vision_workers,
            self.brain_workers,
            self.vision_provider,
            self.vision_model,
            self.vision_base_url,
            self.vision_api_key_env,
            self.brain_provider,
            self.brain_model,
            self.brain_base_url,
            self.brain_api_key_env,
        ):
            var.trace_add("write", lambda *_args: self._on_options_changed())
        self.document_type.trace_add("write", lambda *_args: self._apply_preset())
        self.model_profile.trace_add("write", lambda *_args: self._on_profile_changed())
        for var in (
            self.vision_provider,
            self.vision_model,
            self.vision_base_url,
            self.vision_api_key_env,
            self.brain_provider,
            self.brain_model,
            self.brain_base_url,
            self.brain_api_key_env,
        ):
            var.trace_add("write", lambda *_args: self._refresh_model_status())
            var.trace_add("write", lambda *_args: self._mark_manual_model_selection())

    def _on_options_changed(self) -> None:
        self._refresh_command_preview()
        self._refresh_runtime_summary()

    def _on_profile_changed(self) -> None:
        profile = model_profile_key(self.model_profile.get())
        if profile in {"cheap", "balanced", "accurate"} and not self._syncing_models:
            self._set_models_from_profile(profile)
        self._refresh_model_status()

    def _mark_manual_model_selection(self) -> None:
        if self._syncing_models:
            return
        if model_profile_key(self.model_profile.get()) != "manual":
            self.model_profile.set(MODEL_PROFILE_LABELS["manual"])

    def _apply_preset(self) -> None:
        key = document_type_key(self.document_type.get())
        if key not in DOCUMENT_PRESETS:
            key = "handwritten_notes"
            self.document_type.set(DOCUMENT_PRESETS[key][0])
        label, mode, profile = DOCUMENT_PRESETS[key]
        if self.document_type.get() != label:
            self.document_type.set(label)
        self.engine_mode.set(ENGINE_MODE_LABELS[mode])
        if model_profile_key(self.model_profile.get()) != profile:
            self.model_profile.set(MODEL_PROFILE_LABELS[profile])
        self._on_options_changed()

    def _browse_source(self) -> None:
        from tkinter import filedialog

        kind = source_kind_key(self.source_kind.get())
        suffixes = sorted(MINERU_SUPPORTED_SUFFIXES)
        filetypes = [
            ("支持的文档", " ".join(f"*{suffix}" for suffix in suffixes)),
            ("所有文件", "*.*"),
        ]
        if kind == "input_file":
            value = filedialog.askopenfilename(title="选择本地文件", filetypes=filetypes)
        elif kind == "input_files":
            values = filedialog.askopenfilenames(title="选择多个本地文件", filetypes=filetypes)
            value = ";".join(values)
        elif kind in {"input_folder", "mineru_artifact_dir"}:
            value = filedialog.askdirectory(title="选择文件夹")
        else:
            value = ""
        if value:
            self.source_value.set(value)

    def _browse_output(self) -> None:
        from tkinter import filedialog

        value = filedialog.askdirectory(title="选择输出目录")
        if value:
            self.output_folder.set(value)

    def _options(self) -> GuiRunOptions:
        return GuiRunOptions(
            document_type=document_type_key(self.document_type.get()),
            engine_mode=self.engine_mode.get(),
            model_profile=self.model_profile.get(),
            source_kind=source_kind_key(self.source_kind.get()),
            source_value=self.source_value.get(),
            output_folder=self.output_folder.get(),
            session_name=self.session_name.get(),
            page_ranges=self.page_ranges.get(),
            mineru_model_version=self.mineru_model_version.get(),
            recursive=self.recursive.get(),
            vision_workers=self.vision_workers.get(),
            brain_workers=self.brain_workers.get(),
            vision=SelectedModel(
                self.vision_provider.get(),
                self.vision_model.get(),
                self.vision_base_url.get(),
                self.vision_api_key_env.get(),
            ),
            brain=SelectedModel(
                self.brain_provider.get(),
                self.brain_model.get(),
                self.brain_base_url.get(),
                self.brain_api_key_env.get(),
            ),
        )

    def _refresh_command_preview(self) -> None:
        try:
            command = build_process_command(self._options(), self.repo_root)
            self.command_preview.set(shell_quote_for_preview(command))
        except ValueError as exc:
            self.command_preview.set(str(exc))

    def _refresh_runtime_summary(self) -> None:
        document_key = document_type_key(self.document_type.get())
        mode_key = engine_mode_key(self.engine_mode.get())
        profile_key = model_profile_key(self.model_profile.get())
        self.run_summary_text.set(
            "文档类型只负责填推荐预设，不会锁死旁边选项；你可以手动覆盖处理模式和模型档位。\n"
            f"文档类型：{DOCUMENT_PRESET_DESCRIPTIONS.get(document_key, '')}\n"
            f"处理模式：{ENGINE_MODE_DESCRIPTIONS.get(mode_key, '')}\n"
            f"模型档位：{MODEL_PROFILE_DESCRIPTIONS.get(profile_key, '')}"
        )

    def _refresh_cost_estimate(self, silent: bool = False) -> None:
        try:
            summary = estimate_gui_cost(self._options(), self.base_config)
        except Exception as exc:
            if not silent:
                self.cost_summary_text.set(f"成本估算失败：{exc}")
            return
        row_bits = []
        for row in summary.rows[:3]:
            pages = "未知页数" if row.pages is None else f"{row.pages} 页"
            crops = "未知裁剪块" if row.crop_blocks is None else f"{row.crop_blocks} 个裁剪块"
            cost = "价格未知" if row.estimated_cost is None else f"¥{row.estimated_cost:.2f}"
            row_bits.append(f"{row.name}: {pages}, {crops}, {cost}, {row.confidence}可信")
        if len(summary.rows) > 3:
            row_bits.append(f"另有 {len(summary.rows) - 3} 个文件未展开")
        detail = "；".join(row_bits)
        self.cost_summary_text.set(f"成本估算：{summary.format_brief()}" + (f"\n{detail}" if detail else ""))

    def _validate_before_run(self, options: GuiRunOptions) -> None:
        build_cli_argv(options)
        source_kind = source_kind_key(options.source_kind)
        if source_kind == "mineru_url":
            if not re.match(r"^https?://", options.source_value.strip(), flags=re.IGNORECASE):
                raise ValueError("远程 URL 需要以 http:// 或 https:// 开头。")
            return
        paths = split_multi_paths(options.source_value) if source_kind == "input_files" else [options.source_value.strip().strip('"')]
        for raw_path in paths:
            path = Path(raw_path)
            if source_kind in {"input_folder", "mineru_artifact_dir"}:
                if not path.exists() or not path.is_dir():
                    raise ValueError(f"目录不存在: {path}")
            else:
                if not path.exists() or not path.is_file():
                    raise ValueError(f"文件不存在: {path}")
                if path.suffix.lower() not in MINERU_SUPPORTED_SUFFIXES:
                    supported = ", ".join(sorted(MINERU_SUPPORTED_SUFFIXES))
                    raise ValueError(f"不支持的文件类型: {path.suffix}。支持: {supported}")
        Path(options.output_folder).mkdir(parents=True, exist_ok=True)

    def _start_process(self) -> None:
        from tkinter import messagebox

        if self.process and self.process.poll() is None:
            return
        options = self._options()
        try:
            self._validate_before_run(options)
            command = build_process_command(options, self.repo_root)
        except ValueError as exc:
            messagebox.showerror("无法开始", str(exc))
            return
        self._clear_log()
        self._apply_progress_snapshot(self.progress_tracker.reset(options))
        self._append_log("启动命令：\n" + shell_quote_for_preview(command) + "\n\n", already_translated=True)
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self.process = subprocess.Popen(
            command,
            cwd=self.repo_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=flags,
        )
        self.run_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status_text.set("运行中")
        self.reader_thread = threading.Thread(target=self._read_process_output, daemon=True)
        self.reader_thread.start()

    def _read_process_output(self) -> None:
        assert self.process is not None
        if self.process.stdout:
            for line in self.process.stdout:
                self.output_queue.put(("line", line))
        return_code = self.process.wait()
        self.output_queue.put(("done", return_code))

    def _drain_output_queue(self) -> None:
        try:
            while True:
                kind, payload = self.output_queue.get_nowait()
                if kind == "line":
                    line = str(payload)
                    self._append_log(line)
                    self._apply_progress_snapshot(self.progress_tracker.observe_line(line))
                elif kind == "done":
                    self._on_process_done(int(payload))
        except queue.Empty:
            pass
        self.root.after(100, self._drain_output_queue)

    def _on_process_done(self, return_code: int) -> None:
        self.run_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.status_text.set("完成" if return_code == 0 else f"失败，退出码 {return_code}")
        self._apply_progress_snapshot(self.progress_tracker.finish(return_code == 0))
        self._append_log(f"\n进程退出码: {return_code}\n")
        self.process = None

    def _apply_progress_snapshot(self, snapshot: ProgressSnapshot) -> None:
        self.progress_percent.set(snapshot.percent)
        self.progress_percent_label.set(f"{snapshot.percent:.0f}%")
        self.progress_stage.set(snapshot.stage)
        self.progress_detail.set(snapshot.detail)
        self.progress_eta.set(snapshot.eta)
        self.progress_elapsed.set(snapshot.elapsed)

    def _stop_process(self) -> None:
        if self.process and self.process.poll() is None:
            self.status_text.set("正在停止")
            self.process.terminate()

    def _open_output_folder(self) -> None:
        path = Path(self.output_folder.get())
        path.mkdir(parents=True, exist_ok=True)
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def _clear_log(self) -> None:
        self.log_buffer.clear()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        if self.log_window_text is not None:
            self.log_window_text.configure(state="normal")
            self.log_window_text.delete("1.0", "end")
            self.log_window_text.configure(state="disabled")

    def _append_log(self, text: str, *, already_translated: bool = False) -> None:
        display_text = text if already_translated else "".join(translate_log_line(line) for line in text.splitlines(keepends=True))
        self.log_buffer.append(display_text)
        if len(self.log_buffer) > 5000:
            del self.log_buffer[: len(self.log_buffer) - 5000]
        self.log_text.configure(state="normal")
        self.log_text.insert("end", display_text)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        if self.log_window_text is not None:
            self.log_window_text.configure(state="normal")
            self.log_window_text.insert("end", display_text)
            self.log_window_text.see("end")
            self.log_window_text.configure(state="disabled")

    def _open_log_window(self) -> None:
        if self.log_window is not None and self.log_window.winfo_exists():
            self.log_window.deiconify()
            self.log_window.lift()
            return
        window = self.tk.Toplevel(self.root)
        window.title("DocPage2MD 放大日志")
        window.geometry("1100x720")
        window.minsize(760, 480)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)
        toolbar = self.ttk.Frame(window, padding=8)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.columnconfigure(0, weight=1)
        self.ttk.Label(toolbar, text="中文进度日志，可滚动、复制。完整日志也会写入输出目录 process.log。").grid(row=0, column=0, sticky="w")
        self.ttk.Button(toolbar, text="清空显示", command=self._clear_log).grid(row=0, column=1, padx=(8, 0))
        text = self.tk.Text(window, wrap="word", state="disabled", font=("Consolas", 11))
        text.grid(row=1, column=0, sticky="nsew")
        scroll = self.ttk.Scrollbar(window, orient="vertical", command=text.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        text.configure(yscrollcommand=scroll.set)
        self.log_window = window
        self.log_window_text = text
        text.configure(state="normal")
        text.insert("end", "".join(self.log_buffer))
        text.see("end")
        text.configure(state="disabled")

        def _on_close() -> None:
            self.log_window = None
            self.log_window_text = None
            window.destroy()

        window.protocol("WM_DELETE_WINDOW", _on_close)

    def _reset_models_from_profile(self) -> None:
        self._set_models_from_profile(model_profile_key(self.model_profile.get()))
        self._refresh_model_status()

    def _set_models_from_profile(self, profile: str) -> None:
        vision, brain = default_model_selection(profile, self.base_config)
        self._syncing_models = True
        try:
            self._set_vision(vision)
            self._set_brain(brain)
        finally:
            self._syncing_models = False

    def _set_vision(self, model: SelectedModel) -> None:
        self.vision_provider.set(model.provider)
        self.vision_model.set(model.model)
        self.vision_base_url.set(model.base_url)
        self.vision_api_key_env.set(model.api_key_env)

    def _set_brain(self, model: SelectedModel) -> None:
        self.brain_provider.set(model.provider)
        self.brain_model.set(model.model)
        self.brain_base_url.set(model.base_url)
        self.brain_api_key_env.set(model.api_key_env)

    def _choose_model_from_tree(self, role: str, tree) -> None:
        selected = tree.selection()
        if not selected:
            return
        item = self._tree_item_data.get(selected[0])
        if not item:
            return
        model = SelectedModel(item["provider"], item["model"], item["base_url"], item["api_key_env"])
        if role == ROLE_VISION:
            self._set_vision(model)
        else:
            self._set_brain(model)
        self.model_profile.set(MODEL_PROFILE_LABELS["manual"])
        self._refresh_model_status()

    def _load_third_party_editor_from_tree(self, role: str, tree) -> None:
        selected = tree.selection()
        if not selected:
            return
        item = self._tree_item_data.get(selected[0])
        if not item:
            return
        if item.get("source") != "third_party":
            return
        self.third_party_id.set(item.get("id") or "")
        self.tp_name.set(item.get("name") or item.get("model") or "")
        self.tp_provider.set(item.get("provider") or "openai_compatible")
        self.tp_model.set(item.get("model") or "")
        self.tp_base_url.set(item.get("base_url") or "")
        self.tp_api_key_env.set(item.get("api_key_env") or "OPENAI_API_KEY")
        self.tp_roles.set("vision" if role == ROLE_VISION else "brain")
        self.tp_supports_vision.set(bool(item.get("supports_vision")))
        self.tp_input_price.set("" if item.get("input_price") is None else str(item.get("input_price")))
        self.tp_output_price.set("" if item.get("output_price") is None else str(item.get("output_price")))

    def _save_selected_models(self) -> None:
        selected = AppConfig(
            vision_provider=self.vision_provider.get(),
            model_vision=self.vision_model.get(),
            vision_base_url=self.vision_base_url.get(),
            vision_api_key_env=self.vision_api_key_env.get(),
            brain_provider=self.brain_provider.get(),
            model_brain=self.brain_model.get(),
            brain_base_url=self.brain_base_url.get(),
            brain_api_key_env=self.brain_api_key_env.get(),
        )
        save_model_settings(self.base_config, selected)
        self.model_message.set("已保存当前 Vision / Brain 模型为默认配置。")

    def _refresh_model_status(self) -> None:
        vision_ok = bool(get_env_value(self.vision_api_key_env.get()))
        brain_ok = bool(get_env_value(self.brain_api_key_env.get()))
        self.vision_status.set(
            f"Key：{self.vision_api_key_env.get()} {'已设置' if vision_ok else '未设置'}；"
            f"价格：{_model_price_for_selection(self.vision_provider.get(), self.vision_model.get(), self.base_config)}"
        )
        self.brain_status.set(
            f"Key：{self.brain_api_key_env.get()} {'已设置' if brain_ok else '未设置'}；"
            f"价格：{_model_price_for_selection(self.brain_provider.get(), self.brain_model.get(), self.base_config)}"
        )
        profile = model_profile_key(self.model_profile.get())
        self.model_summary_text.set(
            f"当前档位：{model_profile_label(profile)}。"
            f"Vision={self.vision_provider.get()}:{self.vision_model.get()}；"
            f"Brain={self.brain_provider.get()}:{self.brain_model.get()}。"
            "在这里手动改模型后，运行命令会自动带上覆盖参数。"
        )

    def _prompt_save_key(self) -> None:
        from tkinter import simpledialog

        env_name = simpledialog.askstring("API Key 环境变量", "要设置哪个环境变量？", initialvalue=self.brain_api_key_env.get())
        if not env_name:
            return
        key_value = simpledialog.askstring("API Key", f"粘贴 {env_name} 的值（不会写入仓库文件）:", show="*")
        if not key_value:
            return
        set_user_env_value(env_name, key_value)
        self._refresh_model_status()
        self.model_message.set(f"已保存环境变量 {env_name}。")

    def _save_third_party_model(self) -> None:
        try:
            item = {
                "id": self.third_party_id.get() or None,
                "name": self.tp_name.get() or self.tp_model.get(),
                "provider": self.tp_provider.get(),
                "base_url": self.tp_base_url.get(),
                "api_key_env": self.tp_api_key_env.get(),
                "model_id": self.tp_model.get(),
                "roles": self.tp_roles.get(),
                "supports_vision": self.tp_supports_vision.get(),
                "input_price": _optional_float(self.tp_input_price.get()),
                "output_price": _optional_float(self.tp_output_price.get()),
            }
            saved = upsert_third_party_model(self.base_config, item)
        except ValueError as exc:
            self.model_message.set(str(exc))
            return
        self.third_party_id.set(saved["id"])
        self._reload_model_catalog()
        self.model_message.set(f"已保存第三方模型: {saved['name']}")

    def _delete_selected_third_party_model(self) -> None:
        item_id = self.third_party_id.get()
        if not item_id:
            self.model_message.set("请先选中一个第三方模型。")
            return
        if delete_third_party_model(self.base_config, item_id):
            self.third_party_id.set("")
            self._reload_model_catalog()
            self.model_message.set("已删除第三方模型。")
        else:
            self.model_message.set("未找到要删除的第三方模型。")

    def _verify_third_party_model(self) -> None:
        api_key = get_env_value(self.tp_api_key_env.get())
        if not api_key:
            self.model_message.set(f"未检测到环境变量 {self.tp_api_key_env.get()}。")
            return
        is_vision = self.tp_roles.get() in {"vision", "both"} or self.tp_supports_vision.get()
        try:
            status, error = verify_openai_chat_model(
                self.tp_model.get(),
                api_key,
                self.tp_base_url.get(),
                is_vision=is_vision,
            )
        except Exception as exc:
            self.model_message.set(f"验证失败: {exc}")
            return
        item_id = self.third_party_id.get()
        if item_id:
            role = ROLE_VISION if is_vision else ROLE_BRAIN
            try:
                update_third_party_model_verification(self.base_config, item_id, role, status, error or "")
                self._reload_model_catalog()
            except ValueError as exc:
                self.model_message.set(f"验证完成但写回失败: {exc}")
                return
        self.model_message.set(f"验证结果: {status} {(error or '')[:160]}")

    def _bulk_import_dialog(self) -> None:
        from tkinter import simpledialog

        raw = simpledialog.askstring("批量导入", "输入 JSON 数组，或每行一个模型：model_id, 名称, roles, input_price, output_price")
        if not raw:
            return
        items = parse_bulk_models_text(
            raw,
            defaults={
                "provider": self.tp_provider.get(),
                "base_url": self.tp_base_url.get(),
                "api_key_env": self.tp_api_key_env.get(),
                "roles": self.tp_roles.get(),
            },
        )
        for item in items:
            upsert_third_party_model(self.base_config, item)
        self._reload_model_catalog()
        self.model_message.set(f"已导入 {len(items)} 个第三方模型。")

    def _reload_model_catalog(self) -> None:
        self.catalog = ModelCatalogView(self.base_config)
        self._populate_model_tree(self.vision_list, ROLE_VISION)
        self._populate_model_tree(self.brain_list, ROLE_BRAIN)


def _optional_float(raw: str):
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _price_brief(input_price, output_price) -> str:
    if input_price is None and output_price is None:
        return "未知"
    inp = "?" if input_price is None else f"{float(input_price):g}"
    out = "?" if output_price is None else f"{float(output_price):g}"
    return f"{inp}/{out}"


def _model_price_for_selection(provider: str, model_id: str, config: AppConfig) -> str:
    record = _find_catalog_model(provider, model_id, config)
    if record is None:
        return "未知"
    return _price_brief(record.input_price, record.output_price)


def main() -> int:
    app = DocPage2MdGui()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
