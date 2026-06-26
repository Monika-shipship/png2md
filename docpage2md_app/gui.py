from __future__ import annotations

import os
import queue
import re
import subprocess
import sys
import threading
import time
import urllib.parse
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable

from .aliyun_catalog import filter_brain_models, filter_vision_models, verify_openai_chat_model, vision_recommendation_tier
from .cli import MINERU_SUPPORTED_SUFFIXES
from .config import AppConfig
from .cost import calculate_image_tokens, estimate_deepseek_chat_tokens, estimate_price, estimate_text_cost
from .env import get_env_value, set_user_env_value
from .input_inspection import (
    HTML_SUFFIXES,
    IMAGE_SUFFIXES,
    MINERU_SINGLE_REQUEST_PAGE_LIMIT,
    PADDLEOCR_DAILY_PAGE_LIMIT_PER_MODEL,
    PADDLEOCR_LOCAL_FILE_LIMIT_BYTES,
    PADDLEOCR_RECOMMENDED_CHUNK_PAGES,
    PAGE_RANGE_RE,
    build_page_chunks,
    count_page_ranges as inspect_count_page_ranges,
    estimate_path_pages as inspect_estimate_path_pages,
    estimate_pdf_pages as inspect_estimate_pdf_pages,
    format_file_size,
    infer_mineru_model_version,
    validate_mineru_model_version_for_paths,
)
from .log_translate import (
    CROP_VISION_START_RE,
    DOCUMENT_READY_RE,
    HYBRID_BRAIN_LATENCY_SUMMARY_RE,
    HYBRID_BRAIN_LATENCY_WARNING_RE,
    HYBRID_PAGE_BRAIN_DONE_RE,
    HYBRID_PAGE_BRAIN_START_RE,
    HYBRID_PAGE_REFINER_DONE_RE,
    HYBRID_PAGE_START_RE,
    LOG_MESSAGE_RE,
    MINERU_BATCH_SUBMITTED_RE,
    MINERU_PROCESSED_RE,
    PADDLEOCR_DOCUMENT_READY_RE,
    PADDLEOCR_PAGE_RENDERED_RE,
    PADDLEOCR_RENDERING_PAGE_RE,
    PADDLEOCR_RUNNING_RE,
    PAGE_RENDERED_RE,
    ZH_PADDLEOCR_DOCUMENT_READY_RE,
    ZH_PADDLEOCR_PAGE_RENDERED_RE,
    ZH_PADDLEOCR_RENDERING_PAGE_RE,
    ZH_PADDLEOCR_RUNNING_RE,
    ZH_CROP_VISION_START_RE,
    ZH_DOCUMENT_READY_RE,
    ZH_HYBRID_BRAIN_LATENCY_SUMMARY_RE,
    ZH_HYBRID_BRAIN_LATENCY_WARNING_RE,
    ZH_HYBRID_PAGE_BRAIN_DONE_RE,
    ZH_HYBRID_PAGE_BRAIN_DONE_ELAPSED_RE,
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
from .paddleocr_adapter import adapt_paddleocr_artifacts
from .paddleocr_artifacts import discover_paddleocr_artifacts, resolve_artifact_image as resolve_paddleocr_artifact_image
from .third_party_models import (
    delete_third_party_model,
    discover_openai_compatible_models,
    filter_registry_models,
    load_third_party_models,
    parse_bulk_models_text,
    registry_item_to_model_record,
    update_third_party_model_verification,
    upsert_third_party_model,
)
from .secrets import check_secret_exists, set_secret_value


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
    "mineru_hybrid": "MinerU + Markdown 精修",
    "mineru_only": "仅 MinerU 解析（最快）",
    "paddleocr_hybrid": "PaddleOCR + Markdown 精修",
    "paddleocr_only": "仅 PaddleOCR 解析",
    "dual_hybrid": "MinerU + PaddleOCR 双引擎融合",
}
ENGINE_MODE_LABEL_TO_KEY = {label: key for key, label in ENGINE_MODE_LABELS.items()}
ENGINE_MODE_DESCRIPTIONS = {
    "hybrid": "先上传/读取 MinerU 结果，再对所有页和裁剪块并行调用 Vision/Brain 精修；质量更好，成本更高。",
    "mineru_hybrid": "等价于旧 hybrid：MinerU 负责版面和裁剪，DocPage2MD 继续并行精修。",
    "mineru_only": "只把 MinerU 解析结果渲染成 Markdown，不调用 Vision/Brain；速度最快，适合排版清楚的 PDF。",
    "paddleocr_hybrid": "PaddleOCR 负责 OCR/layout/Markdown 初稿，DocPage2MD 继续并行精修公式、图示、表格和结构。",
    "paddleocr_only": "只把 PaddleOCR 结果渲染为 Markdown，不调用 Vision/Brain；PaddleOCR 按平台额度管理，不计入模型 token 成本。",
    "dual_hybrid": "同时调用 MinerU 与 PaddleOCR。MinerU 作为主版面骨架，PaddleOCR 作为同页证据，再由 DocPage2MD 判断并精修；更慢但适合复杂手写公式。",
    "vision_only": "旧版图片目录流程，只在 CLI 中使用；GUI 主路径暂不启用。",
}

LAYOUT_ENGINE_LABELS = {
    "mineru": "MinerU",
    "paddleocr": "PaddleOCR",
    "dual": "MinerU + PaddleOCR 双引擎融合",
    "none": "不使用解析引擎",
}
LAYOUT_ENGINE_LABEL_TO_KEY = {label: key for key, label in LAYOUT_ENGINE_LABELS.items()}
REFINE_MODE_LABELS = {
    "docpage2md": "开启 DocPage2MD 精修",
    "none": "关闭精修",
}
REFINE_MODE_LABEL_TO_KEY = {label: key for key, label in REFINE_MODE_LABELS.items()}

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

CONCURRENCY_PRESETS = {
    "保守 3/3（稳，适合排查长尾）": (3, 3),
    "均衡 6/6（推荐对照）": (6, 6),
    "高并发 12/12": (12, 12),
    "极速 60/60（默认）": (60, 60),
    "自定义": None,
}

OUTPUT_RETENTION_LABELS = {
    "slim": "精简（推荐）",
    "standard": "标准（保留 IR）",
    "debug": "调试（保留原始数据）",
}
OUTPUT_RETENTION_LABEL_TO_KEY = {label: key for key, label in OUTPUT_RETENTION_LABELS.items()}

PADDLEOCR_EVIDENCE_LEVEL_LABELS = {
    "fast": "极速",
    "standard": "标准（推荐）",
    "debug": "调试",
    "audit": "完整审计",
}
PADDLEOCR_EVIDENCE_LEVEL_LABEL_TO_KEY = {label: key for key, label in PADDLEOCR_EVIDENCE_LEVEL_LABELS.items()}

BRAIN_THINKING_LABELS = {
    "disabled": "快速：关闭思考（推荐）",
    "enabled": "高质量：开启思考",
}
BRAIN_THINKING_LABEL_TO_KEY = {label: key for key, label in BRAIN_THINKING_LABELS.items()}
BRAIN_CONTEXT_RADIUS_LABELS = {
    "0": "仅当前页",
    "1": "前后1页",
    "2": "前后2页（推荐）",
    "3": "前后3页",
    "5": "前后5页",
    "custom": "自定义",
}
BRAIN_CONTEXT_RADIUS_LABEL_TO_KEY = {label: key for key, label in BRAIN_CONTEXT_RADIUS_LABELS.items()}

SOURCE_LABELS = {
    "input_file": "本地单个文件",
    "input_files": "本地多个文件",
    "input_folder": "本地文件夹批量",
    "mineru_artifact_dir": "MinerU artifact 目录",
    "paddleocr_artifact_dir": "PaddleOCR artifact 目录",
    "mineru_url": "远程文件 URL",
}
SOURCE_LABEL_TO_KEY = {label: key for key, label in SOURCE_LABELS.items()}

PROVIDER_PRESETS = {
    "MinerU": {
        "provider": "mineru",
        "base_url": "https://mineru.net",
        "api_key_env": "MINERU_API_TOKEN",
        "help_url": "https://mineru.net/apiManage/token",
    },
    "PaddleOCR": {
        "provider": "paddleocr",
        "base_url": "https://paddleocr.aistudio-app.com",
        "api_key_env": "PADDLEOCR_API_TOKEN",
        "help_url": "https://aistudio.baidu.com/paddleocr/task",
    },
    "DashScope": {
        "provider": "dashscope_openai",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key_env": "DASHSCOPE_API_KEY",
        "help_url": "https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key",
    },
    "DeepSeek": {
        "provider": "deepseek",
        "base_url": "https://api.deepseek.com",
        "api_key_env": "DEEPSEEK_API_KEY",
        "help_url": "https://platform.deepseek.com/api_keys",
    },
    "OpenAI-compatible": {
        "provider": "openai_compatible",
        "base_url": "https://api.openai.com/v1",
        "api_key_env": "OPENAI_API_KEY",
        "help_url": "",
    },
}

SUPPORTED_ENGINE_MODES = {"mineru_only", "hybrid", "mineru_hybrid", "paddleocr_only", "paddleocr_hybrid", "dual_hybrid"}
SUPPORTED_PROVIDERS = ["dashscope", "dashscope_openai", "deepseek", "openai_compatible", "paddleocr"]
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
class InputFileInfo:
    path: Path
    name: str
    suffix: str
    size_text: str
    pages: int | None
    limit_status: str
    order: int


@dataclass(frozen=True)
class GuiRunOptions:
    document_type: str = "handwritten_notes"
    engine_mode: str = "hybrid"
    layout_engine: str = "mineru"
    refine_mode: str = "docpage2md"
    model_profile: str = "balanced"
    source_kind: str = "input_file"
    source_value: str = ""
    output_folder: str = "./markdown_output"
    session_name: str = ""
    page_ranges: str = ""
    mineru_model_version: str = "vlm"
    mineru_is_ocr: bool = AppConfig().mineru_is_ocr
    mineru_enable_formula: bool = AppConfig().mineru_enable_formula
    mineru_enable_table: bool = AppConfig().mineru_enable_table
    mineru_language: str = AppConfig().mineru_language
    mineru_auto_split_pages: bool = True
    mineru_page_chunk_size: int | str = AppConfig().mineru_page_chunk_size
    paddleocr_model: str = AppConfig().paddleocr_model
    paddleocr_api_key_env: str = AppConfig().paddleocr_api_key_env
    paddleocr_base_url: str = AppConfig().paddleocr_base_url
    paddleocr_page_chunk_size: int | str = AppConfig().paddleocr_page_chunk_size
    paddleocr_doc_orientation: bool = AppConfig().paddleocr_doc_orientation
    paddleocr_doc_unwarping: bool = AppConfig().paddleocr_doc_unwarping
    paddleocr_chart_recognition: bool = AppConfig().paddleocr_chart_recognition
    paddleocr_layout_detection: bool = AppConfig().paddleocr_layout_detection
    paddleocr_formula_recognition: bool = AppConfig().paddleocr_formula_recognition
    paddleocr_table_recognition: bool = AppConfig().paddleocr_table_recognition
    paddleocr_evidence_level: str = AppConfig().paddleocr_evidence_level
    recursive: bool = False
    output_retention: str = AppConfig().output_retention
    parser_workers: int | str = AppConfig().parser_workers
    doc_workers: int | str = AppConfig().max_docpage_workers
    vision_workers: int | str = AppConfig().vision_batch_workers
    brain_workers: int | str = AppConfig().brain_batch_workers
    brain_context_radius: int | str = AppConfig().brain_context_radius
    brain_thinking: str = AppConfig().brain_thinking
    brain_reasoning_effort: str = AppConfig().brain_reasoning_effort
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
    vision_input_tokens: int
    vision_output_tokens: int
    vision_cost: float | None
    brain_input_tokens: int
    brain_output_tokens: int
    brain_cost: float | None
    total_cost: float | None
    confidence: str
    note: str = ""

    @property
    def input_tokens(self) -> int:
        return self.vision_input_tokens + self.brain_input_tokens

    @property
    def output_tokens(self) -> int:
        return self.vision_output_tokens + self.brain_output_tokens

    @property
    def estimated_cost(self) -> float | None:
        return self.total_cost


@dataclass(frozen=True)
class BrainWindowCostRow:
    radius: int
    label: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float | None
    confidence: str


@dataclass(frozen=True)
class CostEstimateSummary:
    rows: list[CostEstimateRow]
    total_pages: int | None
    total_input_tokens: int
    total_output_tokens: int
    total_cost: float | None
    confidence: str
    note: str
    brain_window_rows: list[BrainWindowCostRow] = field(default_factory=list)

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


def layout_engine_key(value: str) -> str:
    return LAYOUT_ENGINE_LABEL_TO_KEY.get(value, value)


def refine_mode_key(value: str) -> str:
    return REFINE_MODE_LABEL_TO_KEY.get(value, value)


def workflow_engine_mode(options: GuiRunOptions) -> str:
    layout = layout_engine_key(options.layout_engine)
    refine = refine_mode_key(options.refine_mode)
    explicit = engine_mode_key(options.engine_mode)
    if explicit in {"mineru_only", "mineru_hybrid", "paddleocr_only", "paddleocr_hybrid", "dual_hybrid"}:
        return explicit
    if explicit == "hybrid" and layout == "mineru" and refine == "docpage2md":
        return "hybrid"
    if layout == "mineru":
        return "mineru_hybrid" if refine == "docpage2md" else "mineru_only"
    if layout == "paddleocr":
        return "paddleocr_hybrid" if refine == "docpage2md" else "paddleocr_only"
    if layout == "dual":
        return "dual_hybrid"
    if explicit in SUPPORTED_ENGINE_MODES:
        return explicit
    return "vision_only"


def model_profile_key(value: str) -> str:
    return MODEL_PROFILE_LABEL_TO_KEY.get(value, value)


def model_profile_label(value: str) -> str:
    return MODEL_PROFILE_LABELS.get(model_profile_key(value), value)


def output_retention_key(value: str) -> str:
    return OUTPUT_RETENTION_LABEL_TO_KEY.get(value, value)


def paddleocr_evidence_level_key(value: str) -> str:
    return PADDLEOCR_EVIDENCE_LEVEL_LABEL_TO_KEY.get(value, value)


def source_kind_key(value: str) -> str:
    return SOURCE_LABEL_TO_KEY.get(value, value)


def brain_context_radius_value(value: int | str, custom_value: int | str | None = None) -> int:
    key = BRAIN_CONTEXT_RADIUS_LABEL_TO_KEY.get(str(value), str(value))
    if key == "custom":
        return _non_negative_count(custom_value if custom_value is not None else AppConfig().brain_context_radius, "Brain 上下文窗口")
    return _non_negative_count(key, "Brain 上下文窗口")


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
    if engine_mode_key(options.engine_mode) == "vision_only":
        raise ValueError("GUI 目前不支持 vision_only；旧版纯视觉流程请继续使用 CLI。")
    engine_mode = workflow_engine_mode(options)
    layout_engine = layout_engine_key(options.layout_engine)
    refine_mode = refine_mode_key(options.refine_mode)
    if layout_engine == "dual":
        refine_mode = "docpage2md"
    model_profile = model_profile_key(options.model_profile)
    if engine_mode not in SUPPORTED_ENGINE_MODES:
        raise ValueError("GUI 目前支持 MinerU/PaddleOCR 解析主路径。旧版 vision_only 请继续使用 CLI。")
    document_type = document_type_key(options.document_type)
    source_kind = source_kind_key(options.source_kind)
    if document_type not in DOCUMENT_PRESETS:
        raise ValueError(f"未知文档类型: {options.document_type}")
    if model_profile not in {"cheap", "balanced", "accurate", "manual"}:
        raise ValueError(f"未知模型档位: {options.model_profile}")
    output_retention = output_retention_key(options.output_retention)
    if output_retention not in OUTPUT_RETENTION_LABELS:
        raise ValueError(f"未知输出保留模式: {options.output_retention}")
    paddleocr_evidence_level = paddleocr_evidence_level_key(options.paddleocr_evidence_level)
    if paddleocr_evidence_level not in PADDLEOCR_EVIDENCE_LEVEL_LABELS:
        raise ValueError(f"未知 PaddleOCR 证据保存档位: {options.paddleocr_evidence_level}")
    if source_kind not in SOURCE_LABELS:
        raise ValueError(f"未知输入来源: {options.source_kind}")
    if source_kind == "mineru_artifact_dir" and layout_engine != "mineru":
        raise ValueError("MinerU artifact 目录只能配合 MinerU 解析引擎使用。")
    if source_kind == "paddleocr_artifact_dir" and layout_engine != "paddleocr":
        raise ValueError("PaddleOCR artifact 目录只能配合 PaddleOCR 解析引擎使用。")
    if layout_engine == "dual" and source_kind not in {"input_file", "input_files", "input_folder"}:
        raise ValueError("双引擎融合当前 GUI 支持本地文件、多个本地文件和文件夹。已有双 artifact 组合请使用 CLI。")

    page_ranges = options.page_ranges.strip().replace(" ", "")
    if page_ranges and not PAGE_RANGE_RE.match(page_ranges):
        raise ValueError("页码范围格式应类似 1-10 或 2,4-6。")

    source_value = options.source_value.strip()
    if not source_value:
        raise ValueError("请选择或填写输入来源。")
    mineru_model_version = effective_mineru_model_version(options) if layout_engine in {"mineru", "dual"} else ((options.mineru_model_version or "vlm").strip() or "vlm")

    argv = [
        "--engine-mode",
        engine_mode,
        "--layout-engine",
        layout_engine,
        "--refine-mode",
        refine_mode,
        "--document-type",
        document_type,
        "--model-profile",
        model_profile,
        "--output-retention",
        output_retention,
        "--output",
        options.output_folder,
    ]
    if options.session_name.strip():
        argv.extend(["--name", options.session_name.strip()])
    if page_ranges:
        argv.extend(["--page-ranges", page_ranges])
    argv.extend(
        [
            "--mineru-model-version",
            mineru_model_version,
            "--mineru-is-ocr",
            _bool_arg(options.mineru_is_ocr),
            "--mineru-enable-formula",
            _bool_arg(options.mineru_enable_formula),
            "--mineru-enable-table",
            _bool_arg(options.mineru_enable_table),
            "--mineru-language",
            (options.mineru_language or "ch").strip() or "ch",
        ]
    )
    if options.mineru_auto_split_pages:
        chunk_size = _positive_worker_count(options.mineru_page_chunk_size, "MinerU 分段页数")
        argv.extend(["--auto-split-pages", "--mineru-page-chunk-size", str(chunk_size)])
    argv.extend(
        [
            "--paddleocr-model",
            (options.paddleocr_model or "PaddleOCR-VL-1.6").strip() or "PaddleOCR-VL-1.6",
            "--paddleocr-api-key-env",
            (options.paddleocr_api_key_env or "PADDLEOCR_API_TOKEN").strip() or "PADDLEOCR_API_TOKEN",
            "--paddleocr-base-url",
            (options.paddleocr_base_url or "https://paddleocr.aistudio-app.com").strip() or "https://paddleocr.aistudio-app.com",
            "--paddleocr-page-chunk-size",
            str(_positive_worker_count(options.paddleocr_page_chunk_size, "PaddleOCR 分段页数")),
            "--paddleocr-evidence-level",
            paddleocr_evidence_level,
            "--paddleocr-doc-orientation",
            _bool_arg(options.paddleocr_doc_orientation),
            "--paddleocr-doc-unwarping",
            _bool_arg(options.paddleocr_doc_unwarping),
            "--paddleocr-chart-recognition",
            _bool_arg(options.paddleocr_chart_recognition),
            "--paddleocr-layout-detection",
            _bool_arg(options.paddleocr_layout_detection),
            "--paddleocr-formula-recognition",
            _bool_arg(options.paddleocr_formula_recognition),
            "--paddleocr-table-recognition",
            _bool_arg(options.paddleocr_table_recognition),
        ]
    )
    vision_workers = _positive_worker_count(options.vision_workers, "Vision 并发数")
    brain_workers = _positive_worker_count(options.brain_workers, "Brain 并发数")
    parser_workers = _positive_worker_count(options.parser_workers, "解析并发数")
    doc_workers = _positive_worker_count(options.doc_workers, "文档并发数")
    brain_context_radius = brain_context_radius_value(options.brain_context_radius)
    brain_thinking = BRAIN_THINKING_LABEL_TO_KEY.get(options.brain_thinking, options.brain_thinking or AppConfig().brain_thinking)
    if brain_thinking not in {"enabled", "disabled"}:
        raise ValueError("Brain 思考模式必须是 enabled 或 disabled。")
    brain_reasoning_effort = (options.brain_reasoning_effort or AppConfig().brain_reasoning_effort).strip() or AppConfig().brain_reasoning_effort
    if brain_reasoning_effort not in {"high", "max"}:
        raise ValueError("Brain 思考强度必须是 high 或 max。")
    argv.extend(
        [
            "--vision-workers",
            str(vision_workers),
            "--brain-workers",
            str(brain_workers),
            "--parser-workers",
            str(parser_workers),
            "--doc-workers",
            str(doc_workers),
            "--brain-context-radius",
            str(brain_context_radius),
            "--brain-thinking",
            brain_thinking,
            "--brain-reasoning-effort",
            brain_reasoning_effort,
        ]
    )

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
    elif source_kind == "paddleocr_artifact_dir":
        argv.extend(["--paddleocr-artifact-dir", source_value.strip('"')])
    elif source_kind == "mineru_url":
        if layout_engine == "paddleocr":
            argv.extend(["--paddleocr-url", source_value])
        else:
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


def _non_negative_count(value: int | str, label: str) -> int:
    try:
        count = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValueError(f"{label}必须是 0 或正整数。") from None
    if count < 0:
        raise ValueError(f"{label}必须是 0 或正整数。")
    return count


def _bool_arg(value: bool) -> str:
    return "true" if bool(value) else "false"


def effective_mineru_model_version(options: GuiRunOptions) -> str:
    selected = (options.mineru_model_version or "vlm").strip() or "vlm"
    source_kind = source_kind_key(options.source_kind)
    paths = local_input_paths_for_options(options, require_exists=False)
    if paths:
        inferred = infer_mineru_model_version(paths, selected)
        validate_mineru_model_version_for_paths(paths, inferred)
        return inferred
    if source_kind == "mineru_url":
        parsed_path = urllib.parse.urlsplit(options.source_value.strip()).path
        suffix = Path(parsed_path).suffix.lower()
        if suffix in HTML_SUFFIXES:
            return "MinerU-HTML"
    return selected


def local_input_paths_for_options(options: GuiRunOptions, *, require_exists: bool) -> list[Path]:
    source_kind = source_kind_key(options.source_kind)
    if source_kind == "input_file":
        paths = [Path(options.source_value.strip().strip('"'))]
    elif source_kind == "input_files":
        paths = [Path(item) for item in split_multi_paths(options.source_value)]
    elif source_kind == "input_folder":
        folder = Path(options.source_value.strip().strip('"'))
        if not folder.exists() or not folder.is_dir():
            return [] if not require_exists else [folder]
        iterator = folder.rglob("*") if options.recursive else folder.glob("*")
        layout_engine = layout_engine_key(options.layout_engine)
        if layout_engine == "paddleocr":
            allowed = IMAGE_SUFFIXES | {".pdf"}
        elif layout_engine == "dual":
            allowed = (IMAGE_SUFFIXES | {".pdf"}) & MINERU_SUPPORTED_SUFFIXES
        else:
            allowed = MINERU_SUPPORTED_SUFFIXES
        paths = sorted(
            [path for path in iterator if path.is_file() and path.suffix.lower() in allowed],
            key=lambda path: str(path).lower(),
        )
    else:
        paths = []
    if require_exists:
        return paths
    return paths


def validate_selected_models(vision: SelectedModel | None, brain: SelectedModel | None) -> list[str]:
    issues: list[str] = []
    issues.extend(_validate_selected_model("Vision", vision, requires_vision=True))
    issues.extend(_validate_selected_model("Brain", brain, requires_vision=False))
    return issues


def _validate_selected_model(role_label: str, selected: SelectedModel | None, *, requires_vision: bool) -> list[str]:
    if selected is None:
        return [f"{role_label} 模型未配置。"]
    issues: list[str] = []
    provider = selected.provider.strip()
    model = selected.model.strip()
    base_url = selected.base_url.strip()
    api_key_env = selected.api_key_env.strip()
    if not provider:
        issues.append(f"{role_label} provider 不能为空。")
    elif provider not in SUPPORTED_PROVIDERS:
        issues.append(f"{role_label} provider 不支持: {provider}。")
    if not model:
        issues.append(f"{role_label} 模型 ID 不能为空。")
    if provider not in {"dashscope"} and not base_url:
        issues.append(f"{role_label} Base URL 不能为空。")
    if not api_key_env:
        issues.append(f"{role_label} Key 环境变量名不能为空。")
    if requires_vision and provider == "deepseek":
        issues.append("Vision 不能使用 DeepSeek；DeepSeek 当前只用于 Brain 文本精修。")
    return issues


def missing_model_key_messages(vision: SelectedModel | None, brain: SelectedModel | None) -> list[str]:
    messages: list[str] = []
    seen: set[str] = set()
    for role_label, selected in (("Vision", vision), ("Brain", brain)):
        if selected is None:
            continue
        env_name = selected.api_key_env.strip()
        if not env_name or env_name in seen:
            continue
        seen.add(env_name)
        if not get_env_value(env_name):
            messages.append(f"{role_label} 需要环境变量 {env_name}，当前未检测到。")
    return messages


def build_process_command(options: GuiRunOptions, repo_root: Path | None = None) -> list[str]:
    root = repo_root or Path(__file__).resolve().parent.parent
    if getattr(sys, "frozen", False):
        return [sys.executable, "--docpage2md-cli", *build_cli_argv(options)]
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
    return inspect_count_page_ranges(page_ranges, total_pages)


def estimate_pdf_pages(path: Path) -> int | None:
    return inspect_estimate_pdf_pages(path)


def estimate_path_pages(path: Path, page_ranges: str = "") -> int | None:
    return inspect_estimate_path_pages(path, page_ranges)


def source_paths_for_estimate(options: GuiRunOptions) -> list[Path]:
    return local_input_paths_for_options(options, require_exists=False)


def describe_input_files(paths: list[Path], page_ranges: str = "") -> list[InputFileInfo]:
    infos: list[InputFileInfo] = []
    for index, path in enumerate(paths, start=1):
        suffix = path.suffix.lower()
        try:
            size = path.stat().st_size if path.exists() else None
        except OSError:
            size = None
        pages = estimate_path_pages(path, page_ranges) if path.exists() else None
        infos.append(
            InputFileInfo(
                path=path,
                name=path.name or str(path),
                suffix=suffix,
                size_text=format_file_size(size),
                pages=pages,
                limit_status=input_limit_status(path, pages, size),
                order=index,
            )
        )
    return infos


def input_limit_status(path: Path, pages: int | None, size_bytes: int | None) -> str:
    suffix = path.suffix.lower()
    if suffix in HTML_SUFFIXES:
        return "HTML：自动使用 MinerU-HTML"
    notes: list[str] = []
    if suffix == ".pdf":
        if pages is None:
            notes.append("页数未知")
        elif pages > MINERU_SINGLE_REQUEST_PAGE_LIMIT:
            chunks = len(build_page_chunks(pages, chunk_size=MINERU_SINGLE_REQUEST_PAGE_LIMIT))
            notes.append(f"MinerU 将分 {chunks} 段")
        else:
            notes.append("MinerU 单次可处理")
        if pages is not None and pages > PADDLEOCR_RECOMMENDED_CHUNK_PAGES:
            notes.append("PaddleOCR 建议分段")
    if size_bytes is not None and size_bytes > PADDLEOCR_LOCAL_FILE_LIMIT_BYTES:
        notes.append("PaddleOCR 本地上传超 50MB")
    return "；".join(notes) if notes else "正常"


def _input_summary(infos: list[InputFileInfo], source_kind: str, source_value: str) -> str:
    if source_kind == "mineru_url":
        return f"远程 URL：{source_value or '未填写'}。页数未知，运行后以平台返回为准。"
    if source_kind == "mineru_artifact_dir":
        return f"MinerU artifact 目录：{source_value or '未选择'}。"
    if source_kind == "paddleocr_artifact_dir":
        return f"PaddleOCR artifact 目录：{source_value or '未选择'}。"
    if source_kind == "input_folder" and not infos:
        return f"文件夹：{source_value or '未选择'}。未扫描到支持的文件。"
    if not infos:
        return "还没有选择输入文件。"
    known_pages = [info.pages for info in infos if info.pages is not None]
    page_text = f"{sum(known_pages)} 页" if len(known_pages) == len(infos) else "部分页数未知"
    split_count = sum(1 for info in infos if "分" in info.limit_status)
    split_text = f"，{split_count} 个文件将自动分段" if split_count else ""
    return f"已选择 {len(infos)} 个文件，{page_text}{split_text}。处理顺序按表格从上到下。"


def selected_config_from_options(options: GuiRunOptions, base_config: AppConfig | None = None) -> AppConfig:
    config = apply_model_profile(base_config or AppConfig(), model_profile_key(options.model_profile))
    engine_mode = workflow_engine_mode(options)
    layout_engine = layout_engine_key(options.layout_engine)
    refine_mode = refine_mode_key(options.refine_mode)
    if layout_engine == "dual":
        refine_mode = "docpage2md"
    config = replace(
        config,
        engine_mode=engine_mode,
        layout_engine=layout_engine,
        refine_mode=refine_mode,
        document_type=document_type_key(options.document_type),
        model_profile=model_profile_key(options.model_profile),
        output_folder=options.output_folder,
        mineru_model_version=effective_mineru_model_version(options) if layout_engine in {"mineru", "dual"} else ((options.mineru_model_version or "vlm").strip() or "vlm"),
        mineru_page_ranges=options.page_ranges or None,
        mineru_is_ocr=options.mineru_is_ocr,
        mineru_enable_formula=options.mineru_enable_formula,
        mineru_enable_table=options.mineru_enable_table,
        mineru_language=(options.mineru_language or "ch").strip() or "ch",
        mineru_auto_split_pages=options.mineru_auto_split_pages,
        mineru_page_chunk_size=_positive_worker_count(options.mineru_page_chunk_size, "MinerU 分段页数"),
        paddleocr_model=(options.paddleocr_model or "PaddleOCR-VL-1.6").strip() or "PaddleOCR-VL-1.6",
        paddleocr_api_key_env=(options.paddleocr_api_key_env or "PADDLEOCR_API_TOKEN").strip() or "PADDLEOCR_API_TOKEN",
        paddleocr_base_url=(options.paddleocr_base_url or "https://paddleocr.aistudio-app.com").strip() or "https://paddleocr.aistudio-app.com",
        paddleocr_page_chunk_size=_positive_worker_count(options.paddleocr_page_chunk_size, "PaddleOCR 分段页数"),
        paddleocr_doc_orientation=options.paddleocr_doc_orientation,
        paddleocr_doc_unwarping=options.paddleocr_doc_unwarping,
        paddleocr_chart_recognition=options.paddleocr_chart_recognition,
        paddleocr_layout_detection=options.paddleocr_layout_detection,
        paddleocr_formula_recognition=options.paddleocr_formula_recognition,
        paddleocr_table_recognition=options.paddleocr_table_recognition,
        paddleocr_evidence_level=paddleocr_evidence_level_key(options.paddleocr_evidence_level),
        output_retention=output_retention_key(options.output_retention),
        parser_workers=_positive_worker_count(options.parser_workers, "解析并发数"),
        max_docpage_workers=_positive_worker_count(options.doc_workers, "文档并发数"),
        vision_batch_workers=_positive_worker_count(options.vision_workers, "Vision 并发数"),
        brain_batch_workers=_positive_worker_count(options.brain_workers, "Brain 并发数"),
        brain_context_radius=brain_context_radius_value(options.brain_context_radius),
        brain_thinking=BRAIN_THINKING_LABEL_TO_KEY.get(options.brain_thinking, options.brain_thinking or AppConfig().brain_thinking),
        brain_reasoning_effort=(options.brain_reasoning_effort or AppConfig().brain_reasoning_effort).strip()
        or AppConfig().brain_reasoning_effort,
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
    engine_mode = workflow_engine_mode(options)
    rows: list[CostEstimateRow] = []
    source_kind = source_kind_key(options.source_kind)
    note_parts = ["只估算 Vision/Brain 模型 token 费用，不含 MinerU/PaddleOCR 平台费用。"]

    if engine_mode in {"mineru_only", "paddleocr_only"}:
        pages = _estimate_total_pages(options)
        engine_label = "PaddleOCR" if engine_mode == "paddleocr_only" else "MinerU"
        return CostEstimateSummary(
            rows=[],
            total_pages=pages,
            total_input_tokens=0,
            total_output_tokens=0,
            total_cost=0.0,
            confidence="高",
            note=f"仅 {engine_label} 模式不会调用 Vision/Brain；这里只显示模型精修成本为 ¥0，不含平台额度/限制。",
            brain_window_rows=[],
        )

    if source_kind in {"mineru_artifact_dir", "paddleocr_artifact_dir"}:
        rows = [_estimate_artifact_cost_row(Path(options.source_value.strip().strip('"')), options, config)]
        note_parts.append("artifact 已存在，可按实际页数、裁剪块和图片尺寸估算，仍不含模型输出长度波动。")
    elif source_kind in {"input_file", "input_files", "input_folder"}:
        paths = source_paths_for_estimate(options)
        for path in paths:
            rows.append(_estimate_path_cost_row(path, options, config))
        if not rows:
            rows = [_empty_cost_row("待选择文件", None, None, "低", "还没有可估算的本地文件。")]
        note_parts.append("本地文件在解析引擎返回裁剪块前只能按页数和经验 crop 数粗估。")
    else:
        rows = [_empty_cost_row("远程 URL", None, None, "低", "远程文件运行前无法读取页数。")]
        note_parts.append("远程 URL 运行前无法读取页数，等解析引擎返回后进度会按真实页数更新。")

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
        brain_window_rows=_estimate_brain_window_cost_rows(total_pages, config),
    )


def _estimate_total_pages(options: GuiRunOptions) -> int | None:
    units, _files = estimate_work_units(options)
    if units and all(unit is not None for unit in units):
        return sum(unit for unit in units if unit is not None)
    return None


def _estimate_path_cost_row(path: Path, options: GuiRunOptions, config: AppConfig) -> CostEstimateRow:
    pages = estimate_path_pages(path, options.page_ranges)
    if pages is None:
        return _empty_cost_row(path.name, None, None, "低", "无法在运行前确认页数。")
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
        if source_kind_key(options.source_kind) == "paddleocr_artifact_dir":
            artifacts = discover_paddleocr_artifacts(path)
            document_ir = adapt_paddleocr_artifacts(artifacts, source_path=None, engine_mode=workflow_engine_mode(options))
            image_resolver = resolve_paddleocr_artifact_image
        else:
            artifacts = discover_mineru_artifacts(path)
            document_ir = adapt_mineru_artifacts(artifacts, source_path=None, engine_mode=workflow_engine_mode(options))
            image_resolver = resolve_artifact_image
    except Exception as exc:
        return _empty_cost_row(path.name, None, None, "低", f"无法读取 artifact：{exc}")
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
            image_path = image_resolver(
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
    brain_input = brain_input_tokens if brain_input_tokens is not None else pages * _rough_brain_input_tokens_per_page(config.brain_context_radius)
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
        vision_input_tokens=vision_input,
        vision_output_tokens=vision_output,
        vision_cost=vision_cost,
        brain_input_tokens=brain_input,
        brain_output_tokens=brain_output,
        brain_cost=brain_cost,
        total_cost=cost,
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
        prompt = _brain_ops_prompt(page, _context_window_for_cost(pages, index, radius=config.brain_context_radius))
        total += estimate_deepseek_chat_tokens([{"role": "user", "content": prompt}])
    return total, "DeepSeek 输入 token 使用内置 tokenizer 按真实 Brain prompt 估算。"


def _context_window_for_cost(pages: list[dict], page_index: int, radius: int = 2) -> list[dict]:
    start = max(0, page_index - radius)
    end = min(len(pages), page_index + radius + 1)
    return [pages[index] for index in range(start, end)]


def _rough_brain_input_tokens_per_page(radius: int | str) -> int:
    try:
        value = max(0, int(radius))
    except (TypeError, ValueError):
        value = AppConfig().brain_context_radius
    return ROUGH_BRAIN_INPUT_TOKENS_PER_PAGE + value * 1600


def _estimate_brain_window_cost_rows(total_pages: int | None, config: AppConfig) -> list[BrainWindowCostRow]:
    if total_pages is None or total_pages <= 0:
        return []
    brain_record = _find_catalog_model(config.brain_provider, config.model_brain, config)
    rows: list[BrainWindowCostRow] = []
    for radius in (0, 1, 2, 3, 5):
        input_tokens = total_pages * _rough_brain_input_tokens_per_page(radius)
        output_tokens = total_pages * ROUGH_BRAIN_OUTPUT_TOKENS_PER_PAGE
        cost = estimate_text_cost(input_tokens, output_tokens, brain_record)
        if cost is None:
            cost = estimate_price(config.model_brain, input_tokens, output_tokens)
        rows.append(
            BrainWindowCostRow(
                radius=radius,
                label="仅当前页" if radius == 0 else f"前后{radius}页",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost=cost,
                confidence="中",
            )
        )
    return rows


def _empty_cost_row(
    name: str,
    pages: int | None,
    crop_blocks: int | None,
    confidence: str,
    note: str,
) -> CostEstimateRow:
    return CostEstimateRow(
        name=name,
        pages=pages,
        crop_blocks=crop_blocks,
        vision_input_tokens=0,
        vision_output_tokens=0,
        vision_cost=None,
        brain_input_tokens=0,
        brain_output_tokens=0,
        brain_cost=None,
        total_cost=None,
        confidence=confidence,
        note=note,
    )


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
            or "Submitting one local file to MinerU" in message
            or "Uploading file to MinerU" in message
            or "MinerU chunked PDF start" in message
            or "MinerU chunk " in message and " submit:" in message
            or "正在上传本地文件到 MinerU" in message
            or "正在上传文件" in message
            or "正在提交 MinerU 分段" in message
            or "开始 MinerU 自动分段" in message
        ):
            self.stage = "上传到 MinerU"
            self.detail = _compact_message(message)
        elif (
            "Submitting remote URL to PaddleOCR" in message
            or "Submitting local file to PaddleOCR" in message
            or "Submitting one local file to PaddleOCR" in message
            or "PaddleOCR submit local file" in message
            or "PaddleOCR submit URL" in message
            or "正在提交远程 URL 到 PaddleOCR" in message
            or "正在提交本地文件到 PaddleOCR" in message
            or "正在提交单个本地文件到 PaddleOCR" in message
            or "PaddleOCR 正在上传文件" in message
            or "PaddleOCR 正在提交 URL" in message
        ):
            self._begin_document(message)
            self.stage = "提交到 PaddleOCR"
            self.detail = _compact_message(message)
        elif (
            "PaddleOCR task submitted" in message
            or "PaddleOCR chunk submitted" in message
            or "PaddleOCR 任务已提交" in message
        ):
            self.stage = "等待 PaddleOCR 排队"
            self.detail = _compact_message(message)
        elif "PaddleOCR job pending" in message or "等待 PaddleOCR 排队" in message:
            self.stage = "等待 PaddleOCR 排队"
            self.detail = _compact_message(message)
        elif match := (PADDLEOCR_RUNNING_RE.search(message) or ZH_PADDLEOCR_RUNNING_RE.search(message)):
            if not self.current_doc_started:
                self._begin_document(message)
            extracted = int(match.group(2))
            total = int(match.group(3))
            self._set_current_total_pages(total)
            self._set_current_done_pages(extracted)
            self.stage = f"PaddleOCR 解析 {extracted}/{total} 页"
            self.detail = f"job_id={match.group(1)}"
        elif "PaddleOCR job running" in message or "等待 PaddleOCR 解析" in message:
            self.stage = "等待 PaddleOCR 解析"
            self.detail = _compact_message(message)
        elif "PaddleOCR job done" in message or "PaddleOCR 解析完成" in message:
            self.stage = "下载 PaddleOCR 结果"
            self.detail = _compact_message(message)
        elif (
            "PaddleOCR downloading JSONL result" in message
            or "PaddleOCR downloading Markdown result" in message
            or "正在下载 PaddleOCR JSONL 结果" in message
            or "正在下载 PaddleOCR Markdown 结果" in message
            or "Downloading PaddleOCR artifact" in message
        ):
            self.stage = "下载 PaddleOCR 结果"
            self.detail = _compact_message(message)
        elif "Processing PaddleOCR artifact into Markdown" in message or "正在处理已有 PaddleOCR artifact" in message:
            if not self.current_doc_started:
                self._begin_document(message)
            self.stage = "解析 PaddleOCR artifact"
            self.detail = _compact_message(message)
        elif "PaddleOCR chunked PDF start" in message or "开始 PaddleOCR 自动分段" in message:
            self.stage = "PaddleOCR 自动分段"
            self.detail = _compact_message(message)
        elif "PaddleOCR chunk " in message and " submit:" in message or "正在提交 PaddleOCR 分段" in message:
            self.stage = "提交 PaddleOCR 分段"
            self.detail = _compact_message(message)
        elif "PaddleOCR mixed local processing start" in message or "开始处理 PaddleOCR 本地文件" in message:
            self.stage = "PaddleOCR 批量处理"
            self.detail = _compact_message(message)
        elif "MinerU batch submitted" in message or "MinerU 批量任务已提交" in message or "MinerU 分段任务已提交" in message:
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
            or "MinerU chunk batch submitted" in message
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
        elif match := (PADDLEOCR_DOCUMENT_READY_RE.search(message) or ZH_PADDLEOCR_DOCUMENT_READY_RE.search(message)):
            if not self.current_doc_started:
                self._begin_document(message)
            pages = int(match.group(1))
            self._set_current_total_pages(pages)
            self.stage = "PaddleOCR DocumentIR 已就绪"
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
            self.page_started_elapsed.setdefault(slide, elapsed)
            self.stage = f"第 {slide}/{total} 页 Brain"
            self.detail = "上下文精修中"
        elif match := (
            HYBRID_PAGE_BRAIN_DONE_RE.search(message)
            or ZH_HYBRID_PAGE_BRAIN_DONE_ELAPSED_RE.search(message)
            or ZH_HYBRID_PAGE_BRAIN_DONE_RE.search(message)
        ):
            slide = int(match.group(1))
            self._complete_page(slide, elapsed)
            total = self.current_pages_total or "?"
            if match.re is HYBRID_PAGE_BRAIN_DONE_RE:
                elapsed_value = match.group(6)
            elif match.re is ZH_HYBRID_PAGE_BRAIN_DONE_ELAPSED_RE:
                elapsed_value = match.group(2)
            else:
                elapsed_value = None
            elapsed_text = f"，耗时 {elapsed_value} 秒" if elapsed_value else ""
            self.stage = f"第 {slide}/{total} 页 Brain 完成"
            self.detail = f"Brain 精修完成{elapsed_text}"
        elif match := (HYBRID_PAGE_REFINER_DONE_RE.search(message) or ZH_HYBRID_PAGE_REFINER_DONE_RE.search(message)):
            slide = int(match.group(1))
            self._complete_page(slide, elapsed)
            total = self.current_pages_total or "?"
            self.stage = f"第 {slide}/{total} 页完成"
            self.detail = self._document_detail()
        elif match := (HYBRID_BRAIN_LATENCY_SUMMARY_RE.search(message) or ZH_HYBRID_BRAIN_LATENCY_SUMMARY_RE.search(message)):
            self.stage = "Brain 耗时分析"
            tail_ratio = match.group(6) if match.re is HYBRID_BRAIN_LATENCY_SUMMARY_RE else match.group(5)
            self.detail = f"p50 {match.group(2)}秒，p90 {match.group(3)}秒，最慢 {match.group(4)}秒，长尾系数 {tail_ratio}"
        elif HYBRID_BRAIN_LATENCY_WARNING_RE.search(message) or ZH_HYBRID_BRAIN_LATENCY_WARNING_RE.search(message):
            self.stage = "Brain 长尾提示"
            self.detail = "建议用 Brain 并发 6 或 3 做同文件对照。"
        elif match := (PAGE_RENDERED_RE.search(message) or ZH_PAGE_RENDERED_RE.search(message)):
            slide = int(match.group(1))
            status = match.group(2)
            if not self.saw_hybrid_pages:
                self._complete_page(slide, elapsed)
            self.stage = f"渲染第 {slide} 页"
            self.detail = f"Markdown status={status}"
        elif match := (PADDLEOCR_RENDERING_PAGE_RE.search(message) or ZH_PADDLEOCR_RENDERING_PAGE_RE.search(message)):
            page = int(match.group(1))
            total = int(match.group(2))
            self._set_current_total_pages(total)
            self.current_page = page
            self.page_started_elapsed[page] = elapsed
            self.stage = f"PaddleOCR 渲染第 {page}/{total} 页"
            self.detail = f"slide={match.group(3)}"
        elif match := (PADDLEOCR_PAGE_RENDERED_RE.search(message) or ZH_PADDLEOCR_PAGE_RENDERED_RE.search(message)):
            slide = int(match.group(1))
            status = match.group(2)
            self._complete_page(slide, elapsed)
            self.stage = f"PaddleOCR 第 {slide} 页完成"
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
        elif match := re.search(r"PaddleOCR 文件处理完成：共\s*(\d+)\s*页，输出目录=(.+)", message):
            pages = int(match.group(1))
            self._set_current_total_pages(pages)
            self._finish_document()
            self.stage = "PaddleOCR 文件处理完成"
            self.detail = f"{self.completed_files}/{self.files_total} 个文件完成"
        elif match := re.search(r"PaddleOCR (?:API|artifact) processed: (\d+) pages -> (.+)", message):
            pages = int(match.group(1))
            self._set_current_total_pages(pages)
            self._finish_document()
            self.stage = "PaddleOCR 文件处理完成"
            self.detail = f"{self.completed_files}/{self.files_total} 个文件完成"
        elif message.startswith("MinerU batch complete:") or message.startswith("MinerU 批量任务完成："):
            self.completed_files = self.files_total
            self.done = True
            self.stage = "全部完成"
            self.detail = message
        elif message.startswith("PaddleOCR local batch complete:") or message.startswith("PaddleOCR 本地任务完成："):
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

    def _set_current_done_pages(self, pages_done: int) -> None:
        if pages_done < 0:
            return
        total = self.current_pages_total or pages_done
        capped = min(pages_done, total)
        self.completed_pages.update(range(1, capped + 1))
        self.current_pages_done = max(self.current_pages_done, capped)
        self.current_page = max(self.current_page, capped)

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
        self.root.geometry("1360x900")
        self.root.minsize(1120, 760)

        self.repo_root = Path(__file__).resolve().parent.parent
        self.base_config = AppConfig(output_folder=str((self.repo_root / "markdown_output").resolve()))
        self.catalog = ModelCatalogView(self.base_config)
        self._tree_item_data: dict[str, dict] = {}
        self.input_files: list[Path] = []
        self._syncing_input = False
        self.output_queue: queue.Queue[tuple[str, str | int]] = queue.Queue()
        self.process: subprocess.Popen[str] | None = None
        self.reader_thread: threading.Thread | None = None
        self.progress_tracker = GuiProgressTracker()
        self._drain_after_id: str | None = None
        self.log_window = None
        self.log_window_text = None
        self.log_buffer: list[str] = []
        self._syncing_models = False
        self._syncing_concurrency = False
        self._debounce_after_ids: dict[str, str] = {}
        self._page_count_cache: dict[str, dict[str, int | float | None]] = {}
        self._page_count_loading: set[str] = set()
        self._input_refresh_generation = 0

        default_vision, default_brain = default_model_selection("balanced", self.base_config)
        self.document_type = tk.StringVar(value=DOCUMENT_PRESETS["handwritten_notes"][0])
        self.engine_mode = tk.StringVar(value=ENGINE_MODE_LABELS["hybrid"])
        self.layout_engine = tk.StringVar(value=LAYOUT_ENGINE_LABELS["mineru"])
        self.refine_mode = tk.StringVar(value=REFINE_MODE_LABELS["docpage2md"])
        self.model_profile = tk.StringVar(value=MODEL_PROFILE_LABELS["balanced"])
        self.source_kind = tk.StringVar(value=SOURCE_LABELS["input_files"])
        self.source_value = tk.StringVar(value="")
        self.output_folder = tk.StringVar(value=str((self.repo_root / "markdown_output" / "gui_full_pdf_smoke").resolve()))
        self.session_name = tk.StringVar(value="")
        self.page_ranges = tk.StringVar(value="")
        self.mineru_model_version = tk.StringVar(value="vlm")
        self.mineru_is_ocr = tk.BooleanVar(value=self.base_config.mineru_is_ocr)
        self.mineru_enable_formula = tk.BooleanVar(value=self.base_config.mineru_enable_formula)
        self.mineru_enable_table = tk.BooleanVar(value=self.base_config.mineru_enable_table)
        self.mineru_language = tk.StringVar(value=self.base_config.mineru_language)
        self.mineru_auto_split_pages = tk.BooleanVar(value=True)
        self.mineru_page_chunk_size = tk.StringVar(value=str(self.base_config.mineru_page_chunk_size))
        self.paddleocr_model = tk.StringVar(value=self.base_config.paddleocr_model)
        self.paddleocr_api_key_env = tk.StringVar(value=self.base_config.paddleocr_api_key_env)
        self.paddleocr_base_url = tk.StringVar(value=self.base_config.paddleocr_base_url)
        self.paddleocr_page_chunk_size = tk.StringVar(value=str(self.base_config.paddleocr_page_chunk_size))
        self.paddleocr_doc_orientation = tk.BooleanVar(value=self.base_config.paddleocr_doc_orientation)
        self.paddleocr_doc_unwarping = tk.BooleanVar(value=self.base_config.paddleocr_doc_unwarping)
        self.paddleocr_chart_recognition = tk.BooleanVar(value=self.base_config.paddleocr_chart_recognition)
        self.paddleocr_layout_detection = tk.BooleanVar(value=self.base_config.paddleocr_layout_detection)
        self.paddleocr_formula_recognition = tk.BooleanVar(value=self.base_config.paddleocr_formula_recognition)
        self.paddleocr_table_recognition = tk.BooleanVar(value=self.base_config.paddleocr_table_recognition)
        self.paddleocr_evidence_level = tk.StringVar(
            value=PADDLEOCR_EVIDENCE_LEVEL_LABELS.get(self.base_config.paddleocr_evidence_level, PADDLEOCR_EVIDENCE_LEVEL_LABELS["standard"])
        )
        self.show_mineru_advanced = tk.BooleanVar(value=False)
        self.show_paddleocr_advanced = tk.BooleanVar(value=False)
        self.recursive = tk.BooleanVar(value=False)
        self.output_retention = tk.StringVar(value=OUTPUT_RETENTION_LABELS[self.base_config.output_retention])
        self.parser_workers = tk.StringVar(value=str(self.base_config.parser_workers))
        self.doc_workers = tk.StringVar(value=str(self.base_config.max_docpage_workers))
        self.concurrency_preset = tk.StringVar(value="极速 60/60（默认）")
        self.vision_workers = tk.StringVar(value=str(self.base_config.vision_batch_workers))
        self.brain_workers = tk.StringVar(value=str(self.base_config.brain_batch_workers))
        self.brain_context_radius = tk.StringVar(value=BRAIN_CONTEXT_RADIUS_LABELS[str(self.base_config.brain_context_radius)])
        self.brain_context_custom = tk.StringVar(value=str(self.base_config.brain_context_radius))
        self.brain_thinking = tk.StringVar(value=BRAIN_THINKING_LABELS.get(self.base_config.brain_thinking, BRAIN_THINKING_LABELS["disabled"]))
        self.brain_reasoning_effort = tk.StringVar(value=self.base_config.brain_reasoning_effort)
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
        self.input_summary_text = tk.StringVar(value="还没有选择输入文件。")
        self.model_summary_text = tk.StringVar(value="")
        self.vision_filter = tk.StringVar(value="")
        self.brain_filter = tk.StringVar(value="")
        self.secret_store = tk.StringVar(value="local")
        self.provider_kind = tk.StringVar(value="DashScope")
        self.provider_base_url = tk.StringVar(value=self.base_config.openai_base_url)
        self.provider_key_name = tk.StringVar(value="DASHSCOPE_API_KEY")
        self.provider_status = tk.StringVar(value="选择 Provider 后可检查 Key 或验证模型。")

        self._configure_style()
        self._build_ui()
        self._bind_updates()
        self._apply_preset()
        self._refresh_model_status()
        self._refresh_command_preview()
        self._refresh_runtime_summary()
        self._refresh_cost_estimate(silent=True)
        self._drain_after_id = self.root.after(100, self._drain_output_queue)

    def run(self) -> int:
        try:
            self.root.mainloop()
        finally:
            self.destroy()
        return 0

    def destroy(self) -> None:
        for after_id in list(self._debounce_after_ids.values()):
            try:
                self.root.after_cancel(after_id)
            except self.tk.TclError:
                pass
        self._debounce_after_ids.clear()
        if self._drain_after_id:
            try:
                self.root.after_cancel(self._drain_after_id)
            except self.tk.TclError:
                pass
            self._drain_after_id = None
        try:
            if self.root.winfo_exists():
                self.root.destroy()
        except self.tk.TclError:
            pass

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
        parent.rowconfigure(0, weight=1)

        canvas = tk.Canvas(parent, highlightthickness=0, borderwidth=0, background=self.root.cget("background"))
        run_scroll = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=run_scroll.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        run_scroll.grid(row=0, column=1, sticky="ns")

        content = ttk.Frame(canvas)
        content_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def _refresh_scroll_region(_event=None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _fit_content_width(event) -> None:
            canvas.itemconfigure(content_id, width=event.width)

        def _scroll_run_tab(event) -> None:
            widget_class = event.widget.winfo_class()
            if widget_class in {"Text", "Treeview", "Entry", "TEntry", "TCombobox"}:
                return
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        content.bind("<Configure>", _refresh_scroll_region)
        canvas.bind("<Configure>", _fit_content_width)
        def _bind_run_mousewheel(_event) -> None:
            canvas.bind_all("<MouseWheel>", _scroll_run_tab)

        def _unbind_run_mousewheel(_event) -> None:
            canvas.unbind_all("<MouseWheel>")

        content.bind("<Enter>", _bind_run_mousewheel)
        content.bind("<Leave>", _unbind_run_mousewheel)
        self.run_canvas = canvas

        content.columnconfigure(0, weight=3, minsize=540)
        content.columnconfigure(1, weight=2, minsize=520)
        content.rowconfigure(0, weight=1)

        left = ttk.Frame(content)
        right = ttk.Frame(content)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        right.grid(row=0, column=1, sticky="nsew")
        left.columnconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        workflow = ttk.LabelFrame(left, text="工作流", padding=12)
        workflow.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        workflow.columnconfigure(1, weight=1)

        ttk.Label(workflow, text="文档类型").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            workflow,
            textvariable=self.document_type,
            values=[item[0] for item in DOCUMENT_PRESETS.values()],
            state="readonly",
        ).grid(row=0, column=1, sticky="ew", pady=4)
        self._help_button(workflow, "document_type").grid(row=0, column=2, padx=(6, 0), pady=4)
        ttk.Label(workflow, text="解析引擎").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            workflow,
            textvariable=self.layout_engine,
            values=[LAYOUT_ENGINE_LABELS["mineru"], LAYOUT_ENGINE_LABELS["paddleocr"], LAYOUT_ENGINE_LABELS["dual"]],
            state="readonly",
        ).grid(row=1, column=1, sticky="ew", pady=4)
        self._help_button(workflow, "engine_mode").grid(row=1, column=2, padx=(6, 0), pady=4)
        ttk.Label(workflow, text="Markdown 精修").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            workflow,
            textvariable=self.refine_mode,
            values=[REFINE_MODE_LABELS["docpage2md"], REFINE_MODE_LABELS["none"]],
            state="readonly",
        ).grid(row=2, column=1, sticky="ew", pady=4)
        self._help_button(workflow, "engine_mode").grid(row=2, column=2, padx=(6, 0), pady=4)
        ttk.Label(workflow, text="模型档位").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            workflow,
            textvariable=self.model_profile,
            values=[MODEL_PROFILE_LABELS[key] for key in ("cheap", "balanced", "accurate", "manual")],
            state="readonly",
        ).grid(row=3, column=1, sticky="ew", pady=4)
        self._help_button(workflow, "model_profile").grid(row=3, column=2, padx=(6, 0), pady=4)
        ttk.Label(workflow, text="MinerU 模型").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            workflow,
            textvariable=self.mineru_model_version,
            values=["vlm", "pipeline", "MinerU-HTML"],
            state="readonly",
        ).grid(row=4, column=1, sticky="ew", pady=4)
        self._help_button(workflow, "mineru_model").grid(row=4, column=2, padx=(6, 0), pady=4)
        ttk.Label(workflow, text="PaddleOCR 模型").grid(row=5, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            workflow,
            textvariable=self.paddleocr_model,
            values=["PaddleOCR-VL-1.6", "PaddleOCR-VL-1.5", "PaddleOCR-VL", "PP-StructureV3", "PP-OCRv5"],
            state="readonly",
        ).grid(row=5, column=1, sticky="ew", pady=4)
        self._help_button(workflow, "paddleocr").grid(row=5, column=2, padx=(6, 0), pady=4)
        ttk.Label(
            workflow,
            textvariable=self.run_summary_text,
            wraplength=460,
            justify="left",
        ).grid(row=6, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        source = ttk.LabelFrame(left, text="输入", padding=12)
        source.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        source.columnconfigure(0, weight=1)
        source.rowconfigure(3, weight=1)
        source_top = ttk.Frame(source)
        source_top.grid(row=0, column=0, sticky="ew")
        source_top.columnconfigure(1, weight=1)
        ttk.Label(source_top, text="来源").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(source_top, textvariable=self.source_kind, values=list(SOURCE_LABELS.values()), state="readonly").grid(
            row=0, column=1, sticky="ew", pady=4
        )
        self._help_button(source_top, "input").grid(row=0, column=2, padx=(6, 0), pady=4)
        toolbar = ttk.Frame(source)
        toolbar.grid(row=1, column=0, sticky="ew", pady=(4, 6))
        toolbar.columnconfigure(8, weight=1)
        ttk.Button(toolbar, text="添加文件", command=self._add_input_files).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(toolbar, text="添加文件夹", command=self._add_input_folder).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(toolbar, text="浏览来源", command=self._browse_source).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(toolbar, text="删除", command=self._remove_selected_inputs).grid(row=0, column=3, padx=(0, 6))
        ttk.Button(toolbar, text="清空", command=self._clear_inputs).grid(row=0, column=4, padx=(0, 6))
        ttk.Button(toolbar, text="上移", command=lambda: self._move_selected_input(-1)).grid(row=0, column=5, padx=(0, 6))
        ttk.Button(toolbar, text="下移", command=lambda: self._move_selected_input(1)).grid(row=0, column=6, padx=(0, 6))
        ttk.Button(toolbar, text="预览", command=self._preview_selected_input).grid(row=0, column=7, padx=(0, 6))
        columns = ("order", "name", "type", "size", "pages", "status")
        self.input_tree = ttk.Treeview(source, columns=columns, show="headings", height=6)
        for col, label, width in [
            ("order", "#", 36),
            ("name", "文件名", 150),
            ("type", "类型", 58),
            ("size", "大小", 76),
            ("pages", "页数", 60),
            ("status", "限制状态", 150),
        ]:
            self.input_tree.heading(col, text=label)
            self.input_tree.column(col, width=width, anchor="w", stretch=col in {"name", "status"})
        self.input_tree.grid(row=2, column=0, sticky="nsew")
        input_scroll = ttk.Scrollbar(source, orient="vertical", command=self.input_tree.yview)
        input_scroll.grid(row=2, column=1, sticky="ns")
        self.input_tree.configure(yscrollcommand=input_scroll.set)
        input_bottom = ttk.Frame(source)
        input_bottom.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        input_bottom.columnconfigure(0, weight=1)
        ttk.Label(input_bottom, textvariable=self.input_summary_text, wraplength=420).grid(row=0, column=0, sticky="w")
        ttk.Button(input_bottom, text="打开文件", command=self._open_selected_input).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(input_bottom, text="打开目录", command=self._open_selected_input_folder).grid(row=0, column=2, padx=(6, 0))
        ttk.Checkbutton(source, text="文件夹输入时递归扫描", variable=self.recursive).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(6, 0)
        )

        out = ttk.LabelFrame(left, text="输出与并发", padding=12)
        out.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        out.columnconfigure(1, weight=1)
        ttk.Label(out, text="输出目录").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(out, textvariable=self.output_folder).grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Button(out, text="选择", command=self._browse_output).grid(row=0, column=2, padx=(8, 0), pady=4)
        ttk.Label(out, text="任务名").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(out, textvariable=self.session_name).grid(row=1, column=1, columnspan=2, sticky="ew", pady=4)
        ttk.Label(out, text="页码范围").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Entry(out, textvariable=self.page_ranges).grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Label(out, text="空=全量").grid(row=2, column=2, sticky="w", padx=(8, 0), pady=4)
        ttk.Label(out, text="保留模式").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=4)
        ttk.Combobox(
            out,
            textvariable=self.output_retention,
            values=[OUTPUT_RETENTION_LABELS[key] for key in ("slim", "standard", "debug")],
            state="readonly",
        ).grid(row=3, column=1, sticky="ew", pady=4)
        self._help_button(out, "output_retention").grid(row=3, column=2, padx=(8, 0), pady=4)
        advanced_toggle = ttk.Frame(out)
        advanced_toggle.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        advanced_toggle.columnconfigure(1, weight=1)
        ttk.Checkbutton(
            advanced_toggle,
            text="显示高级 MinerU 设置",
            variable=self.show_mineru_advanced,
            command=self._toggle_mineru_advanced,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(advanced_toggle, text="默认已开启 OCR、公式、表格、中文。").grid(row=0, column=1, sticky="w", padx=(8, 0))
        self._help_button(advanced_toggle, "mineru_advanced").grid(row=0, column=2, padx=(6, 0))
        self.mineru_advanced_frame = ttk.Frame(out)
        self.mineru_advanced_frame.columnconfigure(1, weight=1)
        ttk.Checkbutton(self.mineru_advanced_frame, text="OCR", variable=self.mineru_is_ocr).grid(row=0, column=0, sticky="w", pady=3)
        ttk.Checkbutton(self.mineru_advanced_frame, text="公式识别", variable=self.mineru_enable_formula).grid(row=0, column=1, sticky="w", pady=3)
        ttk.Checkbutton(self.mineru_advanced_frame, text="表格识别", variable=self.mineru_enable_table).grid(row=0, column=2, sticky="w", pady=3)
        ttk.Label(self.mineru_advanced_frame, text="语言").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(self.mineru_advanced_frame, textvariable=self.mineru_language, width=10).grid(row=1, column=1, sticky="w", pady=3)
        ttk.Checkbutton(self.mineru_advanced_frame, text="超过单次页数限制时自动分段", variable=self.mineru_auto_split_pages).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=3
        )
        ttk.Label(self.mineru_advanced_frame, text="每段页数").grid(row=2, column=2, sticky="e", padx=(8, 4), pady=3)
        ttk.Entry(self.mineru_advanced_frame, textvariable=self.mineru_page_chunk_size, width=8).grid(row=2, column=3, sticky="w", pady=3)

        paddle_toggle = ttk.Frame(out)
        paddle_toggle.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(4, 0))
        paddle_toggle.columnconfigure(1, weight=1)
        ttk.Checkbutton(
            paddle_toggle,
            text="显示高级 PaddleOCR 设置",
            variable=self.show_paddleocr_advanced,
            command=self._toggle_paddleocr_advanced,
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(paddle_toggle, text="默认 100 页分段，开启版面/公式/表格识别。").grid(row=0, column=1, sticky="w", padx=(8, 0))
        self._help_button(paddle_toggle, "paddleocr").grid(row=0, column=2, padx=(6, 0))
        self.paddleocr_advanced_frame = ttk.Frame(out)
        ttk.Label(self.paddleocr_advanced_frame, text="Token 名").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(self.paddleocr_advanced_frame, textvariable=self.paddleocr_api_key_env, width=22).grid(row=0, column=1, sticky="w", pady=3)
        ttk.Label(self.paddleocr_advanced_frame, text="每段页数").grid(row=0, column=2, sticky="e", padx=(8, 4), pady=3)
        ttk.Entry(self.paddleocr_advanced_frame, textvariable=self.paddleocr_page_chunk_size, width=8).grid(row=0, column=3, sticky="w", pady=3)
        ttk.Checkbutton(self.paddleocr_advanced_frame, text="方向矫正", variable=self.paddleocr_doc_orientation).grid(row=1, column=0, sticky="w", pady=3)
        ttk.Checkbutton(self.paddleocr_advanced_frame, text="扭曲矫正", variable=self.paddleocr_doc_unwarping).grid(row=1, column=1, sticky="w", pady=3)
        ttk.Checkbutton(self.paddleocr_advanced_frame, text="图表识别", variable=self.paddleocr_chart_recognition).grid(row=1, column=2, sticky="w", pady=3)
        ttk.Checkbutton(self.paddleocr_advanced_frame, text="版面检测", variable=self.paddleocr_layout_detection).grid(row=2, column=0, sticky="w", pady=3)
        ttk.Checkbutton(self.paddleocr_advanced_frame, text="公式识别", variable=self.paddleocr_formula_recognition).grid(row=2, column=1, sticky="w", pady=3)
        ttk.Checkbutton(self.paddleocr_advanced_frame, text="表格识别", variable=self.paddleocr_table_recognition).grid(row=2, column=2, sticky="w", pady=3)
        ttk.Label(self.paddleocr_advanced_frame, text="证据档位").grid(row=3, column=0, sticky="w", pady=3)
        ttk.Combobox(
            self.paddleocr_advanced_frame,
            textvariable=self.paddleocr_evidence_level,
            values=[PADDLEOCR_EVIDENCE_LEVEL_LABELS[key] for key in ("fast", "standard", "debug", "audit")],
            state="readonly",
            width=14,
        ).grid(row=3, column=1, columnspan=2, sticky="ew", pady=3)
        self._help_button(self.paddleocr_advanced_frame, "paddleocr_evidence").grid(row=3, column=3, sticky="w", padx=(6, 0), pady=3)

        concurrency = ttk.LabelFrame(out, text="并发", padding=8)
        concurrency.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        concurrency.columnconfigure(1, weight=1)
        ttk.Label(concurrency, text="档位").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Combobox(
            concurrency,
            textvariable=self.concurrency_preset,
            values=list(CONCURRENCY_PRESETS),
            state="readonly",
        ).grid(row=0, column=1, columnspan=3, sticky="ew", pady=3)
        self._help_button(concurrency, "concurrency").grid(row=0, column=4, padx=(6, 0), pady=3)
        ttk.Label(concurrency, text="解析").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Entry(concurrency, textvariable=self.parser_workers, width=8).grid(row=1, column=1, sticky="w", pady=3)
        ttk.Label(concurrency, text="文档").grid(row=1, column=2, sticky="w", padx=(14, 8), pady=3)
        ttk.Entry(concurrency, textvariable=self.doc_workers, width=8).grid(row=1, column=3, sticky="w", pady=3)
        ttk.Label(concurrency, text="Vision").grid(row=2, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Entry(concurrency, textvariable=self.vision_workers, width=8).grid(row=2, column=1, sticky="w", pady=3)
        ttk.Label(concurrency, text="Brain").grid(row=2, column=2, sticky="w", padx=(14, 8), pady=3)
        ttk.Entry(concurrency, textvariable=self.brain_workers, width=8).grid(row=2, column=3, sticky="w", pady=3)
        ttk.Label(concurrency, text="Brain 模式").grid(row=3, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Combobox(
            concurrency,
            textvariable=self.brain_thinking,
            values=list(BRAIN_THINKING_LABELS.values()),
            state="readonly",
            width=22,
        ).grid(row=3, column=1, sticky="w", pady=3)
        ttk.Label(concurrency, text="强度").grid(row=3, column=2, sticky="w", padx=(14, 8), pady=3)
        ttk.Combobox(
            concurrency,
            textvariable=self.brain_reasoning_effort,
            values=["high", "max"],
            state="readonly",
            width=8,
        ).grid(row=3, column=3, sticky="w", pady=3)
        ttk.Label(concurrency, text="上下文").grid(row=4, column=0, sticky="w", padx=(0, 8), pady=3)
        ttk.Combobox(
            concurrency,
            textvariable=self.brain_context_radius,
            values=list(BRAIN_CONTEXT_RADIUS_LABELS.values()),
            state="readonly",
            width=18,
        ).grid(row=4, column=1, sticky="w", pady=3)
        ttk.Label(concurrency, text="自定义").grid(row=4, column=2, sticky="w", padx=(14, 8), pady=3)
        ttk.Entry(concurrency, textvariable=self.brain_context_custom, width=8).grid(row=4, column=3, sticky="w", pady=3)
        self._help_button(concurrency, "brain_context").grid(row=4, column=4, padx=(6, 0), pady=3)
        self.concurrency_hint_label = ttk.Label(
            concurrency,
            text="极速 60/60 保留原来的高并发；Brain 默认读取前后2页上下文。窗口越大越利于上下文纠错，也越贵、越慢。",
            wraplength=420,
            justify="left",
        )
        self.concurrency_hint_label.grid(row=5, column=0, columnspan=5, sticky="ew", pady=(4, 0))

        def _resize_concurrency_hint(event) -> None:
            self.concurrency_hint_label.configure(wraplength=max(260, event.width - 16))

        concurrency.bind("<Configure>", _resize_concurrency_hint)
        self._toggle_mineru_advanced()
        self._toggle_paddleocr_advanced()

        progress = ttk.LabelFrame(right, text="运行状态", padding=12)
        progress.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        progress.columnconfigure(0, weight=1)
        ttk.Progressbar(progress, variable=self.progress_percent, maximum=100).grid(row=0, column=0, columnspan=4, sticky="ew")
        ttk.Label(progress, textvariable=self.progress_stage).grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(progress, textvariable=self.progress_elapsed).grid(row=1, column=1, sticky="e", padx=(8, 0), pady=(6, 0))
        ttk.Label(progress, textvariable=self.progress_eta).grid(row=1, column=2, sticky="e", padx=(8, 0), pady=(6, 0))
        self.progress_percent_label = self.tk.StringVar(value="0%")
        ttk.Label(progress, textvariable=self.progress_percent_label).grid(row=1, column=3, sticky="e", padx=(8, 0), pady=(6, 0))
        ttk.Label(progress, textvariable=self.progress_detail).grid(row=2, column=0, columnspan=4, sticky="w", pady=(4, 0))

        command = ttk.LabelFrame(right, text="成本与命令", padding=12)
        command.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        command.columnconfigure(0, weight=1)
        cost_header = ttk.Frame(command)
        cost_header.grid(row=0, column=0, sticky="ew")
        cost_header.columnconfigure(0, weight=1)
        self.cost_summary_label = ttk.Label(
            cost_header,
            textvariable=self.cost_summary_text,
            wraplength=520,
            justify="left",
        )
        self.cost_summary_label.grid(row=0, column=0, sticky="ew")

        def _resize_cost_summary(event) -> None:
            self.cost_summary_label.configure(wraplength=max(260, event.width - 8))

        cost_header.bind("<Configure>", _resize_cost_summary)

        cost_actions = ttk.Frame(command)
        cost_actions.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        cost_actions.columnconfigure(4, weight=1)
        self._help_button(cost_actions, "cost").grid(row=0, column=0, sticky="w")
        ttk.Button(cost_actions, text="刷新估算", command=self._refresh_cost_estimate).grid(row=0, column=1, sticky="w", padx=(8, 0))
        ttk.Button(cost_actions, text="刷新官方模型/价格", command=self._refresh_official_models_and_prices).grid(
            row=0, column=2, sticky="w", padx=(8, 0)
        )
        cost_columns = ("file", "pages", "crops", "v_in", "v_out", "v_cost", "b_in", "b_out", "b_cost", "cost", "confidence")
        cost_table = ttk.Frame(command)
        cost_table.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        cost_table.columnconfigure(0, weight=1)
        self.cost_tree = ttk.Treeview(cost_table, columns=cost_columns, show="headings", height=4)
        for col, label, width in [
            ("file", "文件", 220),
            ("pages", "页数", 70),
            ("crops", "裁剪块", 70),
            ("v_in", "Vision输入", 96),
            ("v_out", "Vision输出", 96),
            ("v_cost", "Vision费用", 90),
            ("b_in", "Brain输入", 96),
            ("b_out", "Brain输出", 96),
            ("b_cost", "Brain费用", 90),
            ("cost", "总费用", 84),
            ("confidence", "可信度", 84),
        ]:
            self.cost_tree.heading(col, text=label)
            self.cost_tree.column(col, width=width, minwidth=width, anchor="w", stretch=False)
        self.cost_tree.grid(row=0, column=0, sticky="ew")
        cost_y_scroll = ttk.Scrollbar(cost_table, orient="vertical", command=self.cost_tree.yview)
        cost_y_scroll.grid(row=0, column=1, sticky="ns")
        cost_x_scroll = ttk.Scrollbar(cost_table, orient="horizontal", command=self.cost_tree.xview)
        cost_x_scroll.grid(row=1, column=0, sticky="ew")
        self.cost_tree.configure(yscrollcommand=cost_y_scroll.set, xscrollcommand=cost_x_scroll.set)

        window_columns = ("window", "input", "output", "cost", "confidence")
        window_table = ttk.Frame(command)
        window_table.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        window_table.columnconfigure(0, weight=1)
        ttk.Label(window_table, text="Brain 窗口成本对比").grid(row=0, column=0, sticky="w")
        self.brain_window_cost_tree = ttk.Treeview(window_table, columns=window_columns, show="headings", height=3)
        for col, label, width in [
            ("window", "窗口", 120),
            ("input", "输入tokens", 110),
            ("output", "输出tokens", 110),
            ("cost", "Brain费用", 100),
            ("confidence", "可信度", 84),
        ]:
            self.brain_window_cost_tree.heading(col, text=label)
            self.brain_window_cost_tree.column(col, width=width, minwidth=width, anchor="w", stretch=False)
        self.brain_window_cost_tree.grid(row=1, column=0, sticky="ew")
        window_x_scroll = ttk.Scrollbar(window_table, orient="horizontal", command=self.brain_window_cost_tree.xview)
        window_x_scroll.grid(row=2, column=0, sticky="ew")
        self.brain_window_cost_tree.configure(xscrollcommand=window_x_scroll.set)

        command_preview_frame = ttk.Frame(command)
        command_preview_frame.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        command_preview_frame.columnconfigure(0, weight=1)
        command_tools = ttk.Frame(command_preview_frame)
        command_tools.grid(row=0, column=0, sticky="ew")
        command_tools.columnconfigure(0, weight=1)
        ttk.Label(command_tools, text="命令预览").grid(row=0, column=0, sticky="w")
        ttk.Button(command_tools, text="复制命令", command=self._copy_command_preview).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(command_tools, text="查看完整命令", command=self._open_command_preview_window).grid(row=0, column=2, padx=(6, 0))
        self.command_preview_entry = ttk.Entry(command_preview_frame, textvariable=self.command_preview, state="readonly")
        self.command_preview_entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        command_x_scroll = ttk.Scrollbar(command_preview_frame, orient="horizontal", command=self.command_preview_entry.xview)
        command_x_scroll.grid(row=2, column=0, sticky="ew")
        self.command_preview_entry.configure(xscrollcommand=command_x_scroll.set)

        log_frame = ttk.LabelFrame(right, text="运行日志", padding=12)
        log_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)
        log_tools = ttk.Frame(log_frame)
        log_tools.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))
        log_tools.columnconfigure(0, weight=1)
        ttk.Label(log_tools, text="中文进度日志；完整日志写入输出目录 process.log。").grid(row=0, column=0, sticky="w")
        ttk.Button(log_tools, text="放大日志", command=self._open_log_window).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(log_tools, text="清空显示", command=self._clear_log).grid(row=0, column=2, padx=(8, 0))
        self.log_text = tk.Text(log_frame, wrap="word", height=12, state="disabled", font=("Consolas", 10))
        self.log_text.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scroll.set)

        bottom = ttk.Frame(right)
        bottom.grid(row=3, column=0, sticky="ew")
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
        parent.rowconfigure(0, weight=1)

        self.vision_status = self.tk.StringVar(value="")
        self.brain_status = self.tk.StringVar(value="")
        self.model_message = self.tk.StringVar(value="")

        notebook = ttk.Notebook(parent)
        notebook.grid(row=0, column=0, sticky="nsew")

        provider_tab = ttk.Frame(notebook, padding=12)
        current_tab = ttk.Frame(notebook, padding=12)
        catalog_tab = ttk.Frame(notebook, padding=12)
        third_party_tab = ttk.Frame(notebook, padding=12)
        notebook.add(provider_tab, text="Provider 与 Key")
        notebook.add(current_tab, text="角色绑定")
        notebook.add(catalog_tab, text="候选模型")
        notebook.add(third_party_tab, text="第三方模型库")

        provider_tab.columnconfigure(0, weight=1)
        current_tab.columnconfigure(0, weight=1)
        catalog_tab.columnconfigure(0, weight=1)
        catalog_tab.columnconfigure(1, weight=1)
        catalog_tab.rowconfigure(0, weight=1)
        third_party_tab.columnconfigure(0, weight=1)

        self._build_provider_tab(provider_tab)

        current = ttk.LabelFrame(current_tab, text="当前运行会使用的模型", padding=12)
        current.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        current.columnconfigure(0, weight=1)
        current.columnconfigure(1, weight=1)
        vision_card = ttk.LabelFrame(current, text="Vision：图片、裁剪块、图表识别", padding=12)
        brain_card = ttk.LabelFrame(current, text="Brain：页面结构精修、上下文修正", padding=12)
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
        ttk.Button(controls, text="检查 Key", command=self._check_bound_keys).grid(row=0, column=2, padx=(8, 0))
        ttk.Button(controls, text="验证模型", command=self._verify_bound_models).grid(row=0, column=3, padx=(8, 0))
        ttk.Button(controls, text="设置 Key", command=self._prompt_save_key).grid(row=0, column=4, padx=(8, 0))
        ttk.Button(controls, text="保存为默认", command=self._save_selected_models).grid(row=0, column=5, padx=(8, 0))
        ttk.Label(current_tab, textvariable=self.model_message, wraplength=1100).grid(row=1, column=0, sticky="ew")

        vision_box = ttk.LabelFrame(catalog_tab, text="Vision 候选", padding=12)
        brain_box = ttk.LabelFrame(catalog_tab, text="Brain 候选", padding=12)
        vision_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        brain_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.vision_list = self._build_model_list(vision_box, ROLE_VISION, self.vision_filter)
        self.brain_list = self._build_model_list(brain_box, ROLE_BRAIN, self.brain_filter)
        ttk.Label(catalog_tab, textvariable=self.model_message, wraplength=1100).grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0)
        )

        self._build_third_party_editor(third_party_tab)

    def _build_provider_tab(self, parent) -> None:
        ttk = self.ttk
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        editor = ttk.LabelFrame(parent, text="Provider 配置", padding=12)
        editor.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        editor.columnconfigure(1, weight=1)
        editor.columnconfigure(3, weight=1)

        ttk.Label(editor, text="Provider").grid(row=0, column=0, sticky="w", padx=(0, 6), pady=4)
        provider_combo = ttk.Combobox(editor, textvariable=self.provider_kind, values=list(PROVIDER_PRESETS), state="readonly")
        provider_combo.grid(row=0, column=1, sticky="ew", pady=4)
        ttk.Label(editor, text="Key 保存").grid(row=0, column=2, sticky="w", padx=(10, 6), pady=4)
        stores = ["local", "env"]
        if os.name == "nt":
            stores.append("credential")
        ttk.Combobox(editor, textvariable=self.secret_store, values=stores, state="readonly").grid(row=0, column=3, sticky="ew", pady=4)

        ttk.Label(editor, text="Base URL").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Entry(editor, textvariable=self.provider_base_url).grid(row=1, column=1, columnspan=3, sticky="ew", pady=4)
        ttk.Label(editor, text="Key 名称").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Entry(editor, textvariable=self.provider_key_name).grid(row=2, column=1, sticky="ew", pady=4)
        ttk.Button(editor, text="检查 Key", command=self._check_provider_key).grid(row=2, column=2, padx=(10, 0), pady=4)
        ttk.Button(editor, text="验证模型", command=self._verify_provider_model).grid(row=2, column=3, padx=(8, 0), pady=4, sticky="w")

        actions = ttk.Frame(editor)
        actions.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(8, 0))
        actions.columnconfigure(0, weight=1)
        ttk.Label(actions, textvariable=self.provider_status, wraplength=760).grid(row=0, column=0, sticky="w")
        ttk.Button(actions, text="保存 Key", command=self._prompt_save_provider_key).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(actions, text="获取 API Key", command=self._open_provider_key_url).grid(row=0, column=2, padx=(8, 0))

        table_frame = ttk.LabelFrame(parent, text="常用 Provider", padding=12)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)
        columns = ("provider", "base", "key", "status", "note")
        self.provider_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=10)
        for col, label, width in [
            ("provider", "Provider", 140),
            ("base", "Base URL", 300),
            ("key", "Key 名称", 170),
            ("status", "Key 状态", 120),
            ("note", "说明", 300),
        ]:
            self.provider_tree.heading(col, text=label)
            self.provider_tree.column(col, width=width, anchor="w", stretch=col in {"base", "note"})
        self.provider_tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.provider_tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        self.provider_tree.configure(yscrollcommand=scroll.set)
        self.provider_tree.bind("<<TreeviewSelect>>", lambda _event: self._load_provider_from_tree())
        provider_combo.bind("<<ComboboxSelected>>", lambda _event: self._load_provider_preset())
        self._populate_provider_tree()

    def _help_button(self, parent, topic: str):
        return self.ttk.Button(parent, text="?", width=3, command=lambda: self._show_help(topic))

    def _show_help(self, topic: str) -> None:
        from tkinter import messagebox

        help_texts = {
            "document_type": (
                "文档类型只负责填推荐值，不会和处理模式、模型档位冲突。\n\n"
                "手写矢量笔记：推荐 hybrid + balanced + MinerU vlm。\n"
                "论文 PDF：清晰电子版可用 mineru_only；需要图表公式精修可改 hybrid。\n"
                "截图/屏拍小题：当前 GUI 仍走 MinerU/hybrid 主路径；旧 vision_only 保留在 CLI。\n"
                "复杂公式图表 PPT：推荐 hybrid，可考虑高精度档位。\n"
                "自定义：不按预设自动推荐。"
            ),
            "engine_mode": (
                "工作流由两层组成：解析引擎 + Markdown 精修。\n\n"
                "MinerU：默认解析引擎，适合 PDF/Office/图片/HTML，vlm 默认适合手写和复杂版面。\n"
                "PaddleOCR：正式可选解析引擎，适合扫描、屏拍、弯曲、复杂光照、公式表格等场景；默认 PaddleOCR-VL-1.6。\n\n"
                "开启 DocPage2MD 精修：解析后再并行调用 Vision/Brain 修公式、图示、表格和页面结构，会产生 Vision/Brain token 费用。\n"
                "关闭精修：只使用解析引擎结果，不调用 Vision/Brain，速度更快，模型费用为 0。"
            ),
            "model_profile": (
                "模型档位说明：\n\n"
                "省钱：更便宜，适合清晰材料或大批量粗转。\n"
                "均衡：默认推荐，Vision=qwen3-vl-plus，Brain=deepseek-v4-flash。\n"
                "高精度：适合复杂公式、图表和难页，成本和耗时更高。\n"
                "自定义：使用模型管理页手动绑定的 Vision/Brain。"
            ),
            "mineru_model": (
                "MinerU 模型版本是 MinerU 精准解析 API 的 model_version，不是 Vision/Brain 模型。\n\n"
                "vlm：默认推荐。适合手写、扫描、复杂公式、图表、复杂版面。\n"
                "pipeline：适合清晰电子 PDF 或论文，通常更快、更稳。\n"
                "MinerU-HTML：只用于 .html/.htm。HTML 会自动切到它，非 HTML 不允许使用它。"
            ),
            "mineru_advanced": (
                "高级 MinerU 设置默认按最佳方案开启：\n"
                "is_ocr=true、enable_formula=true、enable_table=true、language=ch。\n\n"
                "这些参数不增加本项目的 Vision/Brain token 成本。MinerU 本身按平台额度/限制管理。\n"
                "本地 PDF 超过单次页数限制时，程序会按页码拆成多段提交并合并最终 Markdown。"
            ),
            "input": (
                "输入区说明：\n\n"
                "添加文件：可多选 PDF/Office/图片/HTML。\n"
                "添加文件夹：扫描文件夹内支持的文档；可勾选递归。\n"
                "页数：PDF 优先读取真实页数；缺依赖时用轻量 marker 估算。\n"
                "限制状态：提示 MinerU/PaddleOCR 是否需要自动分段，以及 PaddleOCR 50MB 本地上传、100 页建议分段、每日 3000 页/模型额度风险。"
            ),
            "paddleocr": (
                "PaddleOCR 设置说明：\n\n"
                "默认模型 PaddleOCR-VL-1.6。它会通过异步 API 返回每页 Markdown、layout JSON 和图片资源。\n"
                "本地上传文件限制 50MB，URL 文件限制约 200MB；每个模型每日约 3000 页额度。\n"
                "为避免超过 100 页只解析前 100 页，GUI/CLI 默认按 100 页拆分 PDF 并自动合并输出。\n\n"
                "高级开关会写入 optionalPayload。默认开启版面、公式、表格识别；方向/扭曲/图表识别默认关闭，遇到屏拍、倾斜或图表文档可手动开启。"
            ),
            "paddleocr_evidence": (
                "PaddleOCR 证据保存档位说明：\n\n"
                "极速：不请求可视化图，只保存转换必需的 JSONL/Markdown 和 Markdown 引用图片，适合大量文件快速跑。\n"
                "标准（推荐）：不请求可视化图，保存结构化结果摘要、JSONL、Markdown、layout/prunedResult 和必要图片资源，足够复现大多数问题。\n"
                "调试：请求并保存 PaddleOCR outputImages/inputImage，可在输出目录的 paddleocr_raw/ 中查看画框图，适合排查切分和识别错误。\n"
                "完整审计：在调试基础上额外保存下载审计和字段摘要，适合真实样本验收和回归对比，会更慢、更占空间。\n\n"
                "注意：PaddleOCR 官方 API 只有 visualize=true/false；这里的四档是 DocPage2MD 封装的保存策略。"
            ),
            "cost": (
                "成本估算只估 Vision/Brain 模型费用。\n\n"
                "MinerU：不计入人民币费用，只提示页数/平台限制。\n"
                "PaddleOCR：按额度/限制显示，不计入模型 token 成本。\n\n"
                "主表会拆开 Vision 与 Brain 的输入、输出和费用。Brain 窗口成本对比只比较不同上下文半径下 Brain 阶段的费用，不会改变当前运行设置。\n\n"
                "可信度：\n"
                "高=已有 artifact，可按真实 crop 和 prompt 估算。\n"
                "中=本地 PDF/图片，可读页数/尺寸，但不知道 MinerU 真实 crop。\n"
                "低=URL、Office 或页数未知。"
            ),
            "output_retention": (
                "输出保留模式决定最终目录里保存多少中间文件。\n\n"
                "精简：默认推荐。保留 Slide_XX.md、FULL.md、Markdown 引用到的 assets、meta、process.log 和 run_report.json；不复制 raw artifact，不保留解析缓存，体积最小。\n"
                "标准：在精简基础上额外保留 ir/document_ir.json 和每页 IR，方便排查结构化内容。\n"
                "调试：完整保留 MinerU/PaddleOCR 原始 artifact、IR 和解析缓存，最适合定位 API 返回内容，但会明显占用磁盘。\n\n"
                "保留模式不会删除用户手动指定的 artifact 目录，也不会碰 markdown_output/已归档。"
            ),
            "brain_context": (
                "Brain 上下文窗口决定每页审阅时能看到多少相邻页。\n\n"
                "仅当前页：最省 token，适合页面相互独立的材料。\n"
                "前后1页：适合普通论文、讲义。\n"
                "前后2页：默认推荐，兼顾上下文纠错和费用。\n"
                "前后3/5页：适合术语前后呼应强、跨页推导多的手写笔记，但 prompt 更长、费用和延迟更高。\n\n"
                "窗口不会让 Brain 自由改整页。Brain 只能提出绑定 block/span 的 op，最后仍要经过 checked ops 和 Validator。"
            ),
            "concurrency": (
                "并发分成四类：解析、文档、Vision、Brain。\n\n"
                "解析并发：多个本地文件同时提交/等待 MinerU 和 PaddleOCR。双引擎时，每个文件内部还会同时提交 MinerU 与 PaddleOCR。\n"
                "文档并发：已有解析结果后，同时处理多少份文档。每份文档内部还会继续开 Vision/Brain 并发；调太高会放大 API 请求数。\n"
                "Vision 并发：同时识别多少个裁剪图、公式图、表格图。\n"
                "Brain 并发：同时精修多少页 Markdown 结构。当前 Brain 任务粒度是“每页一个请求”，所以实际 Brain 并发=min(页数, Brain worker 上限)。11 页 PDF 最多只有 11 个 Brain 请求，不会用满 100/200。\n\n"
                "Brain 模式：默认“快速：关闭思考”。它会关闭 DeepSeek/DashScope Brain 的深度思考参数，适合 JSON/Markdown 结构修正，通常能减少长尾耗时和输出 token。遇到疑难公式、复杂推理页时，可改为“高质量：开启思考”。\n\n"
                "极速 60/60：保留原来的高并发能力，任务数少时实际并发=min(页数或块数, 60)。如果想真正用满 100/200，需要后续把 Brain 拆成更细粒度的小任务，而不是只调 worker 数。\n"
                "均衡 6/6、保守 3/3：适合排查服务端排队、网络抖动或 DeepSeek 长尾。\n\n"
                "如果日志出现“Brain 出现明显长尾”，说明最慢页明显慢于中位页。此时高并发不一定最快，建议用同一个 PDF 分别跑 60、12、6、3，对比 process.log 里的 Brain p50/p90/max。"
            ),
        }
        messagebox.showinfo("说明", help_texts.get(topic, "暂无说明。"))

    def _toggle_mineru_advanced(self) -> None:
        if self.show_mineru_advanced.get():
            self.mineru_advanced_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(6, 6))
        else:
            self.mineru_advanced_frame.grid_remove()

    def _toggle_paddleocr_advanced(self) -> None:
        if self.show_paddleocr_advanced.get():
            self.paddleocr_advanced_frame.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(6, 6))
        else:
            self.paddleocr_advanced_frame.grid_remove()

    def _populate_provider_tree(self) -> None:
        if not hasattr(self, "provider_tree"):
            return
        for item_id in self.provider_tree.get_children():
            self.provider_tree.delete(item_id)
        notes = {
            "MinerU": "文档解析，按平台额度/页数限制。",
            "PaddleOCR": (
                f"文档解析主路径；本地 {format_file_size(PADDLEOCR_LOCAL_FILE_LIMIT_BYTES)}，"
                f"建议每段 {PADDLEOCR_RECOMMENDED_CHUNK_PAGES} 页，约 {PADDLEOCR_DAILY_PAGE_LIMIT_PER_MODEL} 页/日/模型。"
            ),
            "DashScope": "主要用于 Vision，也可用于 OpenAI-compatible 文本模型。",
            "DeepSeek": "默认 Brain 精修模型。",
            "OpenAI-compatible": "OpenRouter、One API、LiteLLM、自建转发等。",
        }
        for name, preset in PROVIDER_PRESETS.items():
            ok, where = check_secret_exists(preset["api_key_env"], repo_root=self.repo_root)
            self.provider_tree.insert(
                "",
                "end",
                iid=name,
                values=(
                    name,
                    preset["base_url"],
                    preset["api_key_env"],
                    "已设置" if ok else "未设置",
                    f"{notes.get(name, '')} Key来源：{where}",
                ),
            )

    def _load_provider_preset(self) -> None:
        preset = PROVIDER_PRESETS.get(self.provider_kind.get())
        if not preset:
            return
        self.provider_base_url.set(preset["base_url"])
        self.provider_key_name.set(preset["api_key_env"])
        self.provider_status.set(f"已载入 {self.provider_kind.get()}。")

    def _load_provider_from_tree(self) -> None:
        selected = self.provider_tree.selection()
        if not selected:
            return
        self.provider_kind.set(selected[0])
        self._load_provider_preset()

    def _check_provider_key(self) -> None:
        env_name = self.provider_key_name.get().strip()
        if not env_name:
            self.provider_status.set("请先填写 Key 名称。")
            return
        ok, where = check_secret_exists(env_name, repo_root=self.repo_root)
        self.provider_status.set(f"{env_name}: {'已找到' if ok else '未找到'}（{where}）。检查 Key 不联网。")
        self._populate_provider_tree()
        self._refresh_model_status()

    def _prompt_save_provider_key(self) -> None:
        from tkinter import simpledialog

        env_name = self.provider_key_name.get().strip()
        if not env_name:
            self.provider_status.set("请先填写 Key 名称。")
            return
        key_value = simpledialog.askstring("保存 API Key", f"粘贴 {env_name} 的值（不会写入 Git）:", show="*")
        if not key_value:
            return
        ok = set_secret_value(env_name, key_value, store=self.secret_store.get(), repo_root=self.repo_root)
        self.provider_status.set(
            f"{env_name}: {'已保存' if ok else '保存失败'}，位置={self.secret_store.get()}。日志和报告只记录 Key 名称。"
        )
        self._populate_provider_tree()
        self._refresh_model_status()

    def _open_provider_key_url(self) -> None:
        import webbrowser

        preset = PROVIDER_PRESETS.get(self.provider_kind.get()) or {}
        url = preset.get("help_url") or ""
        if not url:
            self.provider_status.set("OpenAI-compatible Provider 请到对应服务商后台获取 Key。")
            return
        webbrowser.open(url)

    def _verify_provider_model(self) -> None:
        provider_name = self.provider_kind.get()
        env_name = self.provider_key_name.get().strip()
        api_key = get_env_value(env_name)
        if not api_key:
            self.provider_status.set(f"未检测到 {env_name}，请先保存或设置 Key。")
            return
        if provider_name in {"MinerU", "PaddleOCR"}:
            self.provider_status.set(f"{provider_name} Key 已读取。解析 API 联网验证会在正式任务中完成。")
            return
        model = self.vision_model.get() if provider_name != "DeepSeek" else self.brain_model.get()
        base_url = self.provider_base_url.get().strip()
        try:
            status, error = verify_openai_chat_model(model, api_key, base_url, is_vision=provider_name != "DeepSeek")
        except Exception as exc:
            self.provider_status.set(f"验证失败：{exc}")
            return
        self.provider_status.set(f"验证结果：{model} -> {status} {(error or '')[:160]}")

    def _check_bound_keys(self) -> None:
        self._refresh_model_status()
        messages = []
        layout = layout_engine_key(self.layout_engine.get())
        if layout == "mineru":
            parser_keys = [("解析引擎", "MINERU_API_TOKEN")]
        elif layout == "paddleocr":
            parser_keys = [("解析引擎", self.paddleocr_api_key_env.get())]
        elif layout == "dual":
            parser_keys = [("MinerU", "MINERU_API_TOKEN"), ("PaddleOCR", self.paddleocr_api_key_env.get())]
        else:
            parser_keys = []
        for label, env_name in parser_keys:
            ok, where = check_secret_exists(env_name, repo_root=self.repo_root)
            messages.append(f"{label}: {env_name} {'已找到' if ok else '未找到'}（{where}）")
        for label, env_name in (("Vision", self.vision_api_key_env.get()), ("Brain", self.brain_api_key_env.get())):
            ok, where = check_secret_exists(env_name, repo_root=self.repo_root)
            messages.append(f"{label}: {env_name} {'已找到' if ok else '未找到'}（{where}）")
        self.model_message.set("；".join(messages) + "。检查 Key 不联网。")

    def _verify_bound_models(self) -> None:
        results = []
        for label, provider, model, base_url, env_name, is_vision in (
            ("Vision", self.vision_provider.get(), self.vision_model.get(), self.vision_base_url.get(), self.vision_api_key_env.get(), True),
            ("Brain", self.brain_provider.get(), self.brain_model.get(), self.brain_base_url.get(), self.brain_api_key_env.get(), False),
        ):
            api_key = get_env_value(env_name)
            if not api_key:
                results.append(f"{label}: 未检测到 {env_name}")
                continue
            try:
                status, error = verify_openai_chat_model(model, api_key, base_url, is_vision=is_vision)
            except Exception as exc:
                results.append(f"{label}: 验证失败 {exc}")
                continue
            results.append(f"{label}: {provider}:{model} -> {status}{(' ' + error[:80]) if error else ''}")
        self.model_message.set("；".join(results))

    def _refresh_official_models_and_prices(self) -> None:
        self.cost_summary_text.set("正在后台刷新官方模型/价格，请稍候...")

        def worker() -> None:
            try:
                from .official_catalog import refresh_official_catalog

                result = refresh_official_catalog(
                    providers=["dashscope", "deepseek", "openai-compatible"],
                    cache_path=self.base_config.model_cache_path,
                    region=self.base_config.region,
                    base_url=self.base_config.openai_base_url,
                )
                self.output_queue.put(("catalog", result.summary_text() + "\n" + _catalog_diff_brief(result.diff, result.errors)))
            except Exception as exc:
                self.output_queue.put(("catalog", f"刷新官方模型/价格失败，继续使用本地价格表：{exc}"))

        threading.Thread(target=worker, daemon=True).start()

    def _build_third_party_editor(self, parent) -> None:
        ttk = self.ttk
        parent.columnconfigure(0, weight=1)

        editor = ttk.LabelFrame(parent, text="第三方模型资料", padding=12)
        editor.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        editor.columnconfigure(1, weight=1)
        editor.columnconfigure(3, weight=1)
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
        ttk.Combobox(editor, textvariable=self.tp_provider, values=SUPPORTED_PROVIDERS, state="readonly").grid(
            row=0, column=3, sticky="ew", pady=4
        )
        ttk.Label(editor, text="模型 ID").grid(row=1, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Entry(editor, textvariable=self.tp_model).grid(row=1, column=1, columnspan=3, sticky="ew", pady=4)
        ttk.Label(editor, text="Base URL").grid(row=2, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Entry(editor, textvariable=self.tp_base_url).grid(row=2, column=1, columnspan=3, sticky="ew", pady=4)
        ttk.Label(editor, text="Key 环境变量").grid(row=3, column=0, sticky="w", padx=(0, 6), pady=4)
        ttk.Entry(editor, textvariable=self.tp_api_key_env).grid(row=3, column=1, sticky="ew", pady=4)
        ttk.Label(editor, text="角色").grid(row=3, column=2, sticky="w", padx=(8, 6), pady=4)
        ttk.Combobox(editor, textvariable=self.tp_roles, values=["vision", "brain", "both"], state="readonly").grid(
            row=3, column=3, sticky="ew", pady=4
        )
        ttk.Checkbutton(editor, text="支持图片输入", variable=self.tp_supports_vision).grid(row=4, column=0, sticky="w", pady=4)
        ttk.Label(editor, text="输入价 元/M").grid(row=4, column=1, sticky="e", padx=(8, 6), pady=4)
        ttk.Entry(editor, textvariable=self.tp_input_price, width=12).grid(row=4, column=2, sticky="w", pady=4)
        ttk.Label(editor, text="输出价 元/M").grid(row=4, column=3, sticky="w", padx=(8, 6), pady=4)
        ttk.Entry(editor, textvariable=self.tp_output_price, width=12).grid(row=4, column=4, sticky="w", pady=4)
        actions = ttk.Frame(editor)
        actions.grid(row=5, column=0, columnspan=5, sticky="ew", pady=(10, 0))
        actions.columnconfigure(0, weight=1)
        ttk.Label(actions, text="只保存环境变量名，不保存 API Key 明文。验证结果会写回 log/third_party_models.json。").grid(row=0, column=0, sticky="w")
        ttk.Button(actions, text="保存/更新", command=self._save_third_party_model).grid(row=0, column=1, padx=(8, 0))
        ttk.Button(actions, text="验证", command=self._verify_third_party_model).grid(row=0, column=2, padx=(8, 0))
        ttk.Button(actions, text="自动发现", command=self._discover_third_party_models).grid(row=0, column=3, padx=(8, 0))
        ttk.Button(actions, text="批量导入", command=self._bulk_import_dialog).grid(row=0, column=4, padx=(8, 0))
        ttk.Button(actions, text="清空表单", command=self._clear_third_party_form).grid(row=0, column=5, padx=(8, 0))
        ttk.Button(actions, text="删除选中", command=self._delete_selected_third_party_model).grid(row=0, column=6, padx=(8, 0))

        library = ttk.LabelFrame(parent, text="已保存第三方模型", padding=12)
        library.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        parent.rowconfigure(1, weight=1)
        library.columnconfigure(0, weight=1)
        library.rowconfigure(0, weight=1)
        self.third_party_tree = self._build_third_party_library(library)
        ttk.Label(parent, textvariable=self.model_message, wraplength=1100).grid(row=2, column=0, sticky="ew")

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

    def _build_model_list(self, parent, role: str, filter_var):
        ttk = self.ttk
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        toolbar = ttk.Frame(parent)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        toolbar.columnconfigure(1, weight=1)
        ttk.Label(toolbar, text="筛选").grid(row=0, column=0, sticky="w", padx=(0, 6))
        ttk.Entry(toolbar, textvariable=filter_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(toolbar, text="清空", command=lambda: filter_var.set("")).grid(row=0, column=2, padx=(8, 0))
        columns = ("source", "provider", "model", "price", "key")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=18)
        for col, label, width in [
            ("source", "来源", 80),
            ("provider", "提供商", 110),
            ("model", "模型", 240),
            ("price", "价格 元/M", 120),
            ("key", "Key 状态", 170),
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width, anchor="w")
        tree.grid(row=1, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        scroll.grid(row=1, column=1, sticky="ns")
        tree.configure(yscrollcommand=scroll.set)
        ttk.Button(parent, text="选择为 Vision" if role == ROLE_VISION else "选择为 Brain", command=lambda: self._choose_model_from_tree(role, tree)).grid(
            row=2, column=0, sticky="e", pady=(8, 0)
        )
        self._populate_model_tree(tree, role)
        filter_var.trace_add("write", lambda *_args, t=tree, r=role: self._populate_model_tree(t, r))
        tree.bind("<Double-1>", lambda _event: self._choose_model_from_tree(role, tree))
        tree.bind("<<TreeviewSelect>>", lambda _event: self._load_third_party_editor_from_tree(role, tree))
        return tree

    def _populate_model_tree(self, tree, role: str) -> None:
        for item_id in tree.get_children():
            tree.delete(item_id)
        filter_text = self.vision_filter.get() if role == ROLE_VISION else self.brain_filter.get()
        items = _filter_model_items(self.catalog.all_models(role), filter_text)
        for index, item in enumerate(items, start=1):
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
                    _key_status_brief(item["api_key_env"]),
                ),
            )

    def _build_third_party_library(self, parent):
        ttk = self.ttk
        columns = ("name", "provider", "model", "roles", "price", "key", "verify")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        for col, label, width in [
            ("name", "名称", 180),
            ("provider", "提供商", 120),
            ("model", "模型 ID", 260),
            ("roles", "角色", 110),
            ("price", "价格 元/M", 110),
            ("key", "Key 状态", 170),
            ("verify", "验证", 130),
        ]:
            tree.heading(col, text=label)
            tree.column(col, width=width, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scroll.set)
        tree.bind("<<TreeviewSelect>>", lambda _event: self._load_third_party_editor_from_library(tree))
        self._populate_third_party_tree(tree)
        return tree

    def _populate_third_party_tree(self, tree) -> None:
        for item_id in tree.get_children():
            tree.delete(item_id)
        for index, item in enumerate(load_third_party_models(self.base_config), start=1):
            iid = f"third-party-{index}"
            self._tree_item_data[iid] = {
                "source": "third_party",
                "id": item.get("id"),
                "name": item.get("name") or item.get("model_id"),
                "provider": item.get("provider") or "openai_compatible",
                "model": item.get("model_id") or "",
                "base_url": item.get("base_url") or "",
                "api_key_env": item.get("api_key_env") or "OPENAI_API_KEY",
                "input_price": item.get("input_price"),
                "output_price": item.get("output_price"),
                "supports_vision": item.get("supports_vision"),
                "roles": item.get("roles") or [],
                "verification": item.get("verification") or {},
            }
            tree.insert(
                "",
                "end",
                iid=iid,
                values=(
                    item.get("name") or item.get("model_id"),
                    item.get("provider") or "openai_compatible",
                    item.get("model_id") or "",
                    "/".join(item.get("roles") or []),
                    _price_brief(item.get("input_price"), item.get("output_price")),
                    _key_status_brief(item.get("api_key_env") or "OPENAI_API_KEY"),
                    _verification_brief(item.get("verification") or {}),
                ),
            )

    def _bind_updates(self) -> None:
        for var in (
            self.engine_mode,
            self.layout_engine,
            self.refine_mode,
            self.model_profile,
            self.source_kind,
            self.source_value,
            self.output_folder,
            self.session_name,
            self.page_ranges,
            self.mineru_model_version,
            self.mineru_is_ocr,
            self.mineru_enable_formula,
            self.mineru_enable_table,
            self.mineru_language,
            self.mineru_auto_split_pages,
            self.mineru_page_chunk_size,
            self.paddleocr_model,
            self.paddleocr_api_key_env,
            self.paddleocr_base_url,
            self.paddleocr_page_chunk_size,
            self.paddleocr_doc_orientation,
            self.paddleocr_doc_unwarping,
            self.paddleocr_chart_recognition,
            self.paddleocr_layout_detection,
            self.paddleocr_formula_recognition,
            self.paddleocr_table_recognition,
            self.paddleocr_evidence_level,
            self.recursive,
            self.output_retention,
            self.parser_workers,
            self.doc_workers,
            self.concurrency_preset,
            self.vision_workers,
            self.brain_workers,
            self.brain_context_radius,
            self.brain_context_custom,
            self.brain_thinking,
            self.brain_reasoning_effort,
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
        self.source_kind.trace_add("write", lambda *_args: self._on_source_kind_changed())
        self.source_value.trace_add("write", lambda *_args: self._sync_input_table_from_source_value())
        self.page_ranges.trace_add("write", lambda *_args: self._on_page_ranges_changed())
        self.model_profile.trace_add("write", lambda *_args: self._on_profile_changed())
        self.concurrency_preset.trace_add("write", lambda *_args: self._apply_concurrency_preset())
        self.vision_workers.trace_add("write", lambda *_args: self._sync_concurrency_preset_from_workers())
        self.brain_workers.trace_add("write", lambda *_args: self._sync_concurrency_preset_from_workers())
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
        self._schedule_debounced("options_changed", 300, self._refresh_options_dependents)

    def _refresh_options_dependents(self) -> None:
        self._refresh_command_preview()
        self._refresh_runtime_summary()

    def _on_page_ranges_changed(self) -> None:
        self._schedule_debounced("input_table", 300, self._refresh_input_table)

    def _schedule_debounced(self, key: str, delay_ms: int, callback) -> None:
        existing = self._debounce_after_ids.pop(key, None)
        if existing:
            try:
                self.root.after_cancel(existing)
            except self.tk.TclError:
                pass

        def _run() -> None:
            self._debounce_after_ids.pop(key, None)
            callback()

        self._debounce_after_ids[key] = self.root.after(delay_ms, _run)

    def _on_profile_changed(self) -> None:
        profile = model_profile_key(self.model_profile.get())
        if profile in {"cheap", "balanced", "accurate"} and not self._syncing_models:
            self._set_models_from_profile(profile)
        self._refresh_model_status()

    def _apply_concurrency_preset(self) -> None:
        if self._syncing_concurrency:
            return
        preset = CONCURRENCY_PRESETS.get(self.concurrency_preset.get())
        if preset is None:
            return
        self._syncing_concurrency = True
        try:
            vision_workers, brain_workers = preset
            self.vision_workers.set(str(vision_workers))
            self.brain_workers.set(str(brain_workers))
        finally:
            self._syncing_concurrency = False
        self._refresh_runtime_summary()

    def _sync_concurrency_preset_from_workers(self) -> None:
        if self._syncing_concurrency:
            return
        current = (self.vision_workers.get().strip(), self.brain_workers.get().strip())
        matched_label = None
        for label, preset in CONCURRENCY_PRESETS.items():
            if preset and current == (str(preset[0]), str(preset[1])):
                matched_label = label
                break
        target = matched_label or "自定义"
        if self.concurrency_preset.get() == target:
            return
        self._syncing_concurrency = True
        try:
            self.concurrency_preset.set(target)
        finally:
            self._syncing_concurrency = False

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
        if mode in {"hybrid", "mineru_hybrid"}:
            self.layout_engine.set(LAYOUT_ENGINE_LABELS["mineru"])
            self.refine_mode.set(REFINE_MODE_LABELS["docpage2md"])
        elif mode == "mineru_only":
            self.layout_engine.set(LAYOUT_ENGINE_LABELS["mineru"])
            self.refine_mode.set(REFINE_MODE_LABELS["none"])
        elif mode == "paddleocr_hybrid":
            self.layout_engine.set(LAYOUT_ENGINE_LABELS["paddleocr"])
            self.refine_mode.set(REFINE_MODE_LABELS["docpage2md"])
        elif mode == "paddleocr_only":
            self.layout_engine.set(LAYOUT_ENGINE_LABELS["paddleocr"])
            self.refine_mode.set(REFINE_MODE_LABELS["none"])
        elif mode == "dual_hybrid":
            self.layout_engine.set(LAYOUT_ENGINE_LABELS["dual"])
            self.refine_mode.set(REFINE_MODE_LABELS["docpage2md"])
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
        elif kind in {"input_folder", "mineru_artifact_dir", "paddleocr_artifact_dir"}:
            value = filedialog.askdirectory(title="选择文件夹")
        else:
            value = ""
        if value:
            if kind in {"input_file", "input_files"}:
                paths = [Path(item) for item in split_multi_paths(value)] if kind == "input_files" else [Path(value)]
                self._set_input_files(paths, source_kind=kind)
            else:
                self.source_value.set(value)
                self.input_files = []
                self._refresh_input_table()

    def _add_input_files(self) -> None:
        from tkinter import filedialog

        suffixes = sorted(MINERU_SUPPORTED_SUFFIXES)
        values = filedialog.askopenfilenames(
            title="添加本地文件",
            filetypes=[("支持的文档", " ".join(f"*{suffix}" for suffix in suffixes)), ("所有文件", "*.*")],
        )
        if not values:
            return
        self.source_kind.set(SOURCE_LABELS["input_files"])
        self._set_input_files([*self.input_files, *(Path(value) for value in values)], source_kind="input_files")

    def _add_input_folder(self) -> None:
        from tkinter import filedialog

        value = filedialog.askdirectory(title="添加文件夹")
        if not value:
            return
        self.source_kind.set(SOURCE_LABELS["input_folder"])
        self.source_value.set(value)
        self.input_files = source_paths_for_estimate(self._options())
        self._refresh_input_table()

    def _set_input_files(self, paths: list[Path], *, source_kind: str) -> None:
        deduped: dict[str, Path] = {}
        for path in paths:
            if not str(path).strip():
                continue
            deduped[str(path).lower()] = path
        self.input_files = list(deduped.values())
        if source_kind == "input_file" and len(self.input_files) <= 1:
            self.source_kind.set(SOURCE_LABELS["input_file"])
        else:
            self.source_kind.set(SOURCE_LABELS["input_files"])
        self._set_source_value_from_input_files()
        self._refresh_input_table()

    def _set_source_value_from_input_files(self) -> None:
        self._syncing_input = True
        try:
            kind = source_kind_key(self.source_kind.get())
            if kind == "input_file":
                self.source_value.set(str(self.input_files[0]) if self.input_files else "")
            elif kind == "input_files":
                self.source_value.set(";".join(str(path) for path in self.input_files))
        finally:
            self._syncing_input = False

    def _sync_input_table_from_source_value(self) -> None:
        if self._syncing_input:
            return
        kind = source_kind_key(self.source_kind.get())
        if kind == "input_file":
            raw = self.source_value.get().strip().strip('"')
            self.input_files = [Path(raw)] if raw else []
        elif kind == "input_files":
            self.input_files = [Path(item) for item in split_multi_paths(self.source_value.get())]
        elif kind == "input_folder":
            self.input_files = source_paths_for_estimate(self._options())
        else:
            self.input_files = []
        self._refresh_input_table()

    def _on_source_kind_changed(self) -> None:
        kind = source_kind_key(self.source_kind.get())
        if kind in {"input_file", "input_files"} and self.input_files:
            self._set_source_value_from_input_files()
        elif kind == "input_folder" and self.source_value.get():
            self.input_files = source_paths_for_estimate(self._options())
        else:
            self.input_files = []
        self._refresh_input_table()

    def _refresh_input_table(self) -> None:
        if not hasattr(self, "input_tree"):
            return
        self._input_refresh_generation += 1
        generation = self._input_refresh_generation
        infos = self._describe_input_files_cached(self.input_files, self.page_ranges.get(), generation)
        existing_ids = set(self.input_tree.get_children())
        wanted_ids: set[str] = set()
        for info in infos:
            item_id = str(info.order - 1)
            wanted_ids.add(item_id)
            values = (
                info.order,
                info.name,
                info.suffix or "-",
                info.size_text,
                "未知" if info.pages is None else str(info.pages),
                info.limit_status,
            )
            if item_id in existing_ids:
                self.input_tree.item(item_id, values=values)
            else:
                self.input_tree.insert("", "end", iid=item_id, values=values)
        for stale_id in existing_ids - wanted_ids:
            self.input_tree.delete(stale_id)
        self.input_summary_text.set(_input_summary(infos, source_kind_key(self.source_kind.get()), self.source_value.get()))
        self._auto_adjust_mineru_model_for_inputs()

    def _describe_input_files_cached(self, paths: list[Path], page_ranges: str, generation: int) -> list[InputFileInfo]:
        infos: list[InputFileInfo] = []
        for index, path in enumerate(paths, start=1):
            suffix = path.suffix.lower()
            size = self._safe_file_size(path)
            pages, loading = self._cached_selected_page_count(path, page_ranges, generation)
            limit_status = "页数读取中" if loading else input_limit_status(path, pages, size)
            infos.append(
                InputFileInfo(
                    path=path,
                    name=path.name or str(path),
                    suffix=suffix,
                    size_text=format_file_size(size),
                    pages=pages,
                    limit_status=limit_status,
                    order=index,
                )
            )
        return infos

    def _safe_file_size(self, path: Path) -> int | None:
        try:
            return path.stat().st_size if path.exists() else None
        except OSError:
            return None

    def _cached_selected_page_count(self, path: Path, page_ranges: str, generation: int) -> tuple[int | None, bool]:
        suffix = path.suffix.lower()
        if not path.exists():
            return None, False
        if suffix in IMAGE_SUFFIXES:
            return 1, False
        if suffix != ".pdf":
            return None, False
        try:
            stat = path.stat()
        except OSError:
            return None, False
        key = self._page_count_cache_key(path)
        cached = self._page_count_cache.get(key)
        if cached and cached.get("size") == stat.st_size and cached.get("mtime") == stat.st_mtime:
            total_pages = cached.get("pages")
            pages = count_page_ranges(page_ranges, int(total_pages)) if isinstance(total_pages, int) else None
            return pages, False
        if key not in self._page_count_loading:
            self._page_count_loading.add(key)
            thread = threading.Thread(
                target=self._load_pdf_page_count_worker,
                args=(path, key, stat.st_size, stat.st_mtime, generation),
                daemon=True,
            )
            thread.start()
        return None, True

    def _page_count_cache_key(self, path: Path) -> str:
        try:
            return str(path.resolve()).lower()
        except OSError:
            return str(path).lower()

    def _load_pdf_page_count_worker(self, path: Path, key: str, size: int, mtime: float, generation: int) -> None:
        pages = estimate_pdf_pages(path)

        def _complete() -> None:
            self._page_count_loading.discard(key)
            try:
                current = path.stat()
            except OSError:
                return
            if current.st_size != size or current.st_mtime != mtime:
                return
            self._page_count_cache[key] = {"size": size, "mtime": mtime, "pages": pages}
            if generation <= self._input_refresh_generation and any(self._page_count_cache_key(item) == key for item in self.input_files):
                self._refresh_input_table()

        try:
            self.root.after(0, _complete)
        except self.tk.TclError:
            pass

    def _selected_input_index(self) -> int | None:
        if not hasattr(self, "input_tree"):
            return None
        selected = self.input_tree.selection()
        if not selected:
            return None
        try:
            return int(selected[0])
        except ValueError:
            return None

    def _remove_selected_inputs(self) -> None:
        index = self._selected_input_index()
        if index is None or not (0 <= index < len(self.input_files)):
            return
        del self.input_files[index]
        self.source_kind.set(SOURCE_LABELS["input_files"] if len(self.input_files) != 1 else SOURCE_LABELS["input_file"])
        self._set_source_value_from_input_files()
        self._refresh_input_table()

    def _clear_inputs(self) -> None:
        self.input_files = []
        self.source_value.set("")
        self._refresh_input_table()

    def _move_selected_input(self, delta: int) -> None:
        index = self._selected_input_index()
        if index is None:
            return
        new_index = index + delta
        if not (0 <= index < len(self.input_files)) or not (0 <= new_index < len(self.input_files)):
            return
        self.input_files[index], self.input_files[new_index] = self.input_files[new_index], self.input_files[index]
        self._set_source_value_from_input_files()
        self._refresh_input_table()
        self.input_tree.selection_set(str(new_index))

    def _selected_input_path(self) -> Path | None:
        index = self._selected_input_index()
        if index is None or not (0 <= index < len(self.input_files)):
            return None
        return self.input_files[index]

    def _open_selected_input(self) -> None:
        path = self._selected_input_path()
        if not path or not path.exists():
            return
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])

    def _open_selected_input_folder(self) -> None:
        path = self._selected_input_path()
        if not path:
            return
        folder = path.parent if path.suffix else path
        if not folder.exists():
            return
        if os.name == "nt":
            os.startfile(folder)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(folder)])
        else:
            subprocess.Popen(["xdg-open", str(folder)])

    def _preview_selected_input(self) -> None:
        from tkinter import messagebox

        path = self._selected_input_path()
        if not path:
            messagebox.showinfo("预览", "请先选中一个输入文件。")
            return
        pages = estimate_path_pages(path, self.page_ranges.get())
        size = format_file_size(path.stat().st_size) if path.exists() else "未知"
        messagebox.showinfo("输入预览", f"文件：{path.name}\n路径：{path}\n大小：{size}\n页数：{pages or '未知'}\n\n缩略图预览将在后续版本接入。")

    def _auto_adjust_mineru_model_for_inputs(self) -> None:
        if layout_engine_key(self.layout_engine.get()) != "mineru" or not self.input_files:
            return
        suffixes = {path.suffix.lower() for path in self.input_files}
        if suffixes and suffixes <= HTML_SUFFIXES:
            if self.mineru_model_version.get() != "MinerU-HTML":
                self.mineru_model_version.set("MinerU-HTML")
        elif self.mineru_model_version.get() == "MinerU-HTML":
            self.mineru_model_version.set("vlm")

    def _browse_output(self) -> None:
        from tkinter import filedialog

        value = filedialog.askdirectory(title="选择输出目录")
        if value:
            self.output_folder.set(value)

    def _options(self) -> GuiRunOptions:
        layout = layout_engine_key(self.layout_engine.get())
        refine = refine_mode_key(self.refine_mode.get())
        if layout == "mineru":
            engine = "mineru_hybrid" if refine == "docpage2md" else "mineru_only"
        elif layout == "paddleocr":
            engine = "paddleocr_hybrid" if refine == "docpage2md" else "paddleocr_only"
        elif layout == "dual":
            engine = "dual_hybrid"
            refine = "docpage2md"
        else:
            engine = "vision_only"
        return GuiRunOptions(
            document_type=document_type_key(self.document_type.get()),
            engine_mode=engine,
            layout_engine=self.layout_engine.get(),
            refine_mode=REFINE_MODE_LABELS["docpage2md"] if layout == "dual" else self.refine_mode.get(),
            model_profile=self.model_profile.get(),
            source_kind=source_kind_key(self.source_kind.get()),
            source_value=self.source_value.get(),
            output_folder=self.output_folder.get(),
            session_name=self.session_name.get(),
            page_ranges=self.page_ranges.get(),
            mineru_model_version=self.mineru_model_version.get(),
            mineru_is_ocr=self.mineru_is_ocr.get(),
            mineru_enable_formula=self.mineru_enable_formula.get(),
            mineru_enable_table=self.mineru_enable_table.get(),
            mineru_language=self.mineru_language.get(),
            mineru_auto_split_pages=self.mineru_auto_split_pages.get(),
            mineru_page_chunk_size=self.mineru_page_chunk_size.get(),
            paddleocr_model=self.paddleocr_model.get(),
            paddleocr_api_key_env=self.paddleocr_api_key_env.get(),
            paddleocr_base_url=self.paddleocr_base_url.get(),
            paddleocr_page_chunk_size=self.paddleocr_page_chunk_size.get(),
            paddleocr_doc_orientation=self.paddleocr_doc_orientation.get(),
            paddleocr_doc_unwarping=self.paddleocr_doc_unwarping.get(),
            paddleocr_chart_recognition=self.paddleocr_chart_recognition.get(),
            paddleocr_layout_detection=self.paddleocr_layout_detection.get(),
            paddleocr_formula_recognition=self.paddleocr_formula_recognition.get(),
            paddleocr_table_recognition=self.paddleocr_table_recognition.get(),
            paddleocr_evidence_level=self.paddleocr_evidence_level.get(),
            recursive=self.recursive.get(),
            output_retention=self.output_retention.get(),
            parser_workers=self.parser_workers.get(),
            doc_workers=self.doc_workers.get(),
            vision_workers=self.vision_workers.get(),
            brain_workers=self.brain_workers.get(),
            brain_context_radius=(
                self.brain_context_custom.get()
                if BRAIN_CONTEXT_RADIUS_LABEL_TO_KEY.get(self.brain_context_radius.get(), self.brain_context_radius.get()) == "custom"
                else self.brain_context_radius.get()
            ),
            brain_thinking=self.brain_thinking.get(),
            brain_reasoning_effort=self.brain_reasoning_effort.get(),
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

    def _copy_command_preview(self) -> None:
        command = self.command_preview.get()
        self.root.clipboard_clear()
        self.root.clipboard_append(command)
        self.status_text.set("已复制命令预览")

    def _open_command_preview_window(self) -> None:
        window = self.tk.Toplevel(self.root)
        window.title("DocPage2MD 完整命令")
        window.geometry("1100x360")
        window.minsize(720, 280)
        window.columnconfigure(0, weight=1)
        window.rowconfigure(1, weight=1)

        toolbar = self.ttk.Frame(window, padding=8)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        toolbar.columnconfigure(0, weight=1)
        self.ttk.Label(toolbar, text="这里显示完整命令，可横向滚动或复制。").grid(row=0, column=0, sticky="w")
        self.ttk.Button(toolbar, text="复制命令", command=self._copy_command_preview).grid(row=0, column=1, padx=(8, 0))

        text = self.tk.Text(window, wrap="none", font=("Consolas", 10), height=8)
        text.grid(row=1, column=0, sticky="nsew")
        y_scroll = self.ttk.Scrollbar(window, orient="vertical", command=text.yview)
        y_scroll.grid(row=1, column=1, sticky="ns")
        x_scroll = self.ttk.Scrollbar(window, orient="horizontal", command=text.xview)
        x_scroll.grid(row=2, column=0, sticky="ew")
        text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        text.insert("1.0", self.command_preview.get())
        text.configure(state="disabled")

    def _refresh_runtime_summary(self) -> None:
        document_key = document_type_key(self.document_type.get())
        mode_key = workflow_engine_mode(self._options())
        layout = layout_engine_key(self.layout_engine.get())
        refine = refine_mode_key(self.refine_mode.get())
        profile_key = model_profile_key(self.model_profile.get())
        try:
            mineru_model = effective_mineru_model_version(self._options()) if layout in {"mineru", "dual"} and self.source_value.get().strip() else self.mineru_model_version.get()
        except ValueError as exc:
            mineru_model = f"配置需调整：{exc}"
        if layout == "mineru":
            parser_model = f"MinerU {mineru_model}"
        elif layout == "paddleocr":
            parser_model = f"PaddleOCR {self.paddleocr_model.get()}"
        elif layout == "dual":
            parser_model = f"MinerU {mineru_model} + PaddleOCR {self.paddleocr_model.get()}"
        else:
            parser_model = layout
        try:
            brain_radius = brain_context_radius_value(self._options().brain_context_radius)
            brain_context_text = f"前后{brain_radius}页" if brain_radius else "仅当前页"
        except ValueError:
            brain_context_text = "配置需调整"
        self.run_summary_text.set(
            "文档类型只设置推荐值，可手动覆盖模式、档位和模型。\n"
            f"当前：{DOCUMENT_PRESETS.get(document_key, DOCUMENT_PRESETS['custom'])[0]} / "
            f"{ENGINE_MODE_LABELS.get(mode_key, mode_key)} / {LAYOUT_ENGINE_LABELS.get(layout, layout)} / "
            f"{REFINE_MODE_LABELS.get(refine, refine)} / {MODEL_PROFILE_LABELS.get(profile_key, profile_key)} / {parser_model}\n"
            f"保留={self.output_retention.get()}，解析并发={self.parser_workers.get() or '?'}，文档并发={self.doc_workers.get() or '?'}，"
            f"Vision={self.vision_workers.get() or '?'}，Brain={self.brain_workers.get() or '?'}，"
            f"Brain窗口={brain_context_text}，Brain模式={self.brain_thinking.get()}"
        )

    def _refresh_cost_estimate(self, silent: bool = False) -> None:
        try:
            summary = estimate_gui_cost(self._options(), self.base_config)
        except Exception as exc:
            if not silent:
                self.cost_summary_text.set(f"成本估算失败：{exc}")
            return
        self.cost_summary_text.set(f"模型成本估算：{summary.format_brief()}\nMinerU/PaddleOCR 显示为平台额度/限制，不计入人民币费用。")
        if hasattr(self, "cost_tree"):
            for item_id in self.cost_tree.get_children():
                self.cost_tree.delete(item_id)
            rows = summary.rows or [_empty_cost_row("平台解析", summary.total_pages, 0, summary.confidence, summary.note)]
            for index, row in enumerate(rows, start=1):
                self.cost_tree.insert(
                    "",
                    "end",
                    iid=f"cost-{index}",
                    values=(
                        row.name,
                        "未知" if row.pages is None else row.pages,
                        "未知" if row.crop_blocks is None else row.crop_blocks,
                        _format_token_count(row.vision_input_tokens),
                        _format_token_count(row.vision_output_tokens),
                        "未知" if row.vision_cost is None else f"¥{row.vision_cost:.2f}",
                        _format_token_count(row.brain_input_tokens),
                        _format_token_count(row.brain_output_tokens),
                        "未知" if row.brain_cost is None else f"¥{row.brain_cost:.2f}",
                        "未知" if row.total_cost is None else f"¥{row.total_cost:.2f}",
                        row.confidence,
                    ),
                )
        if hasattr(self, "brain_window_cost_tree"):
            for item_id in self.brain_window_cost_tree.get_children():
                self.brain_window_cost_tree.delete(item_id)
            for index, row in enumerate(summary.brain_window_rows, start=1):
                self.brain_window_cost_tree.insert(
                    "",
                    "end",
                    iid=f"brain-window-cost-{index}",
                    values=(
                        row.label,
                        _format_token_count(row.input_tokens),
                        _format_token_count(row.output_tokens),
                        "未知" if row.estimated_cost is None else f"¥{row.estimated_cost:.2f}",
                        row.confidence,
                    ),
                )

    def _validate_before_run(self, options: GuiRunOptions) -> None:
        build_cli_argv(options)
        engine_mode = workflow_engine_mode(options)
        layout_engine = layout_engine_key(options.layout_engine)
        if engine_mode in {"hybrid", "mineru_hybrid", "paddleocr_hybrid", "dual_hybrid"}:
            model_issues = validate_selected_models(options.vision, options.brain)
            model_issues.extend(missing_model_key_messages(options.vision, options.brain))
            if model_issues:
                raise ValueError("模型配置不完整：\n- " + "\n- ".join(model_issues))
        source_kind = source_kind_key(options.source_kind)
        if source_kind == "mineru_url":
            if not re.match(r"^https?://", options.source_value.strip(), flags=re.IGNORECASE):
                raise ValueError("远程 URL 需要以 http:// 或 https:// 开头。")
            if layout_engine == "paddleocr":
                if not get_env_value(options.paddleocr_api_key_env):
                    raise ValueError(f"远程 URL 通过 PaddleOCR 解析需要 {options.paddleocr_api_key_env}，当前未检测到。")
            elif not get_env_value("MINERU_API_TOKEN"):
                raise ValueError("远程 URL 解析需要 MINERU_API_TOKEN，当前未检测到。")
            Path(options.output_folder).mkdir(parents=True, exist_ok=True)
            return
        paths = split_multi_paths(options.source_value) if source_kind == "input_files" else [options.source_value.strip().strip('"')]
        local_paths: list[Path] = []
        for raw_path in paths:
            path = Path(raw_path)
            if source_kind in {"input_folder", "mineru_artifact_dir", "paddleocr_artifact_dir"}:
                if not path.exists() or not path.is_dir():
                    raise ValueError(f"目录不存在: {path}")
            else:
                if not path.exists() or not path.is_file():
                    raise ValueError(f"文件不存在: {path}")
                if layout_engine == "paddleocr":
                    if path.suffix.lower() != ".pdf" and path.suffix.lower() not in IMAGE_SUFFIXES:
                        raise ValueError(f"PaddleOCR 当前支持 PDF 和图片，不支持: {path.suffix}")
                    if path.stat().st_size > PADDLEOCR_LOCAL_FILE_LIMIT_BYTES:
                        raise ValueError(f"PaddleOCR 本地上传单文件限制为 50MB：{path.name}")
                elif layout_engine == "dual":
                    if path.suffix.lower() != ".pdf" and path.suffix.lower() not in IMAGE_SUFFIXES:
                        raise ValueError(f"双引擎融合当前支持 PDF 和图片，不支持: {path.suffix}")
                    if path.suffix.lower() not in MINERU_SUPPORTED_SUFFIXES:
                        supported = ", ".join(sorted(MINERU_SUPPORTED_SUFFIXES))
                        raise ValueError(f"双引擎融合要求 MinerU 也支持该文件类型: {path.suffix}。MinerU 支持: {supported}")
                    if path.stat().st_size > PADDLEOCR_LOCAL_FILE_LIMIT_BYTES:
                        raise ValueError(f"PaddleOCR 本地上传单文件限制为 50MB：{path.name}")
                else:
                    if path.suffix.lower() not in MINERU_SUPPORTED_SUFFIXES:
                        supported = ", ".join(sorted(MINERU_SUPPORTED_SUFFIXES))
                        raise ValueError(f"不支持的文件类型: {path.suffix}。支持: {supported}")
                local_paths.append(path)
        if local_paths and layout_engine in {"mineru", "dual"}:
            validate_mineru_model_version_for_paths(local_paths, effective_mineru_model_version(options))
        if layout_engine == "paddleocr" and source_kind != "paddleocr_artifact_dir" and not get_env_value(options.paddleocr_api_key_env):
            raise ValueError(f"本地文件/文件夹通过 PaddleOCR API 解析需要 {options.paddleocr_api_key_env}，当前未检测到。")
        if layout_engine == "dual" and not get_env_value(options.paddleocr_api_key_env):
            raise ValueError(f"双引擎融合需要 PaddleOCR Token 环境变量 {options.paddleocr_api_key_env}，当前未检测到。")
        if layout_engine == "mineru" and source_kind != "mineru_artifact_dir" and not get_env_value("MINERU_API_TOKEN"):
            raise ValueError("本地文件/文件夹通过 MinerU API 解析需要 MINERU_API_TOKEN，当前未检测到。")
        if layout_engine == "dual" and not get_env_value("MINERU_API_TOKEN"):
            raise ValueError("双引擎融合需要 MINERU_API_TOKEN，当前未检测到。")
        Path(options.output_folder).mkdir(parents=True, exist_ok=True)

    def _start_process(self) -> None:
        from tkinter import messagebox

        if self.process and self.process.poll() is None:
            return
        options = self._options()
        try:
            self._validate_before_run(options)
            if not self._confirm_chunked_run_if_needed(options):
                return
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

    def _confirm_chunked_run_if_needed(self, options: GuiRunOptions) -> bool:
        from tkinter import messagebox

        layout_engine = layout_engine_key(options.layout_engine)
        source_kind = source_kind_key(options.source_kind)
        if source_kind not in {"input_file", "input_files"}:
            return True
        paths = local_input_paths_for_options(options, require_exists=False)
        chunk_lines: list[str] = []
        if layout_engine == "dual":
            chunk_size = min(
                _positive_worker_count(options.mineru_page_chunk_size, "MinerU 分段页数"),
                _positive_worker_count(options.paddleocr_page_chunk_size, "PaddleOCR 分段页数"),
            )
        elif layout_engine == "paddleocr":
            chunk_size = _positive_worker_count(options.paddleocr_page_chunk_size, "PaddleOCR 分段页数")
        else:
            chunk_size = _positive_worker_count(options.mineru_page_chunk_size, "MinerU 分段页数")
        if layout_engine == "mineru" and not options.mineru_auto_split_pages:
            return True
        for path in paths:
            if path.suffix.lower() != ".pdf" or not path.exists():
                continue
            pages = estimate_pdf_pages(path)
            if not pages:
                continue
            chunks = build_page_chunks(pages, options.page_ranges, chunk_size=chunk_size)
            if len(chunks) > 1:
                ranges = "，".join(chunk.page_ranges for chunk in chunks[:4])
                if len(chunks) > 4:
                    ranges += "，..."
                chunk_lines.append(f"{path.name}: 共 {pages} 页，将拆成 {len(chunks)} 段（{ranges}）")
        if not chunk_lines:
            return True
        return messagebox.askyesno(
            "确认自动分段",
            f"以下 PDF 将按页码分段提交 {LAYOUT_ENGINE_LABELS.get(layout_engine, layout_engine)}，并在结束后自动合并 FULL Markdown：\n\n"
            + "\n".join(chunk_lines)
            + "\n\n是否继续？",
        )

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
                elif kind == "catalog":
                    self._reload_model_catalog()
                    self.cost_summary_text.set(str(payload))
        except queue.Empty:
            pass
        try:
            if self.root.winfo_exists():
                self._drain_after_id = self.root.after(100, self._drain_output_queue)
        except self.tk.TclError:
            self._drain_after_id = None

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

    def _load_third_party_editor_from_library(self, tree) -> None:
        selected = tree.selection()
        if not selected:
            return
        item = self._tree_item_data.get(selected[0])
        if not item:
            return
        self._load_third_party_item_into_editor(item)

    def _load_third_party_item_into_editor(self, item: dict) -> None:
        self.third_party_id.set(item.get("id") or "")
        self.tp_name.set(item.get("name") or item.get("model") or "")
        self.tp_provider.set(item.get("provider") or "openai_compatible")
        self.tp_model.set(item.get("model") or "")
        self.tp_base_url.set(item.get("base_url") or "")
        self.tp_api_key_env.set(item.get("api_key_env") or "OPENAI_API_KEY")
        roles = item.get("roles") or []
        if ROLE_VISION in roles and ROLE_BRAIN in roles:
            self.tp_roles.set("both")
        elif ROLE_VISION in roles:
            self.tp_roles.set("vision")
        else:
            self.tp_roles.set("brain")
        self.tp_supports_vision.set(bool(item.get("supports_vision")))
        self.tp_input_price.set("" if item.get("input_price") is None else str(item.get("input_price")))
        self.tp_output_price.set("" if item.get("output_price") is None else str(item.get("output_price")))

    def _clear_third_party_form(self) -> None:
        self.third_party_id.set("")
        self.tp_name.set("")
        self.tp_provider.set("openai_compatible")
        self.tp_model.set("")
        self.tp_base_url.set("https://api.openai.com/v1")
        self.tp_api_key_env.set("OPENAI_API_KEY")
        self.tp_roles.set("both")
        self.tp_supports_vision.set(True)
        self.tp_input_price.set("")
        self.tp_output_price.set("")
        self.model_message.set("已清空第三方模型表单。")

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
        issues = validate_selected_models(
            SelectedModel(self.vision_provider.get(), self.vision_model.get(), self.vision_base_url.get(), self.vision_api_key_env.get()),
            SelectedModel(self.brain_provider.get(), self.brain_model.get(), self.brain_base_url.get(), self.brain_api_key_env.get()),
        )
        missing_keys = missing_model_key_messages(
            SelectedModel(self.vision_provider.get(), self.vision_model.get(), self.vision_base_url.get(), self.vision_api_key_env.get()),
            SelectedModel(self.brain_provider.get(), self.brain_model.get(), self.brain_base_url.get(), self.brain_api_key_env.get()),
        )
        health = "模型配置完整。" if not issues and not missing_keys else "模型配置需要处理：" + "；".join(issues + missing_keys)
        self.model_summary_text.set(
            f"当前档位：{model_profile_label(profile)}。"
            f"Vision={self.vision_provider.get()}:{self.vision_model.get()}；"
            f"Brain={self.brain_provider.get()}:{self.brain_model.get()}。"
            "在这里手动改模型后，运行命令会自动带上覆盖参数。\n"
            f"{health}"
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
            roles_to_update = [ROLE_VISION, ROLE_BRAIN] if self.tp_roles.get() == "both" else [ROLE_VISION if is_vision else ROLE_BRAIN]
            try:
                for role in roles_to_update:
                    update_third_party_model_verification(self.base_config, item_id, role, status, error or "")
                self._reload_model_catalog()
            except ValueError as exc:
                self.model_message.set(f"验证完成但写回失败: {exc}")
                return
        self.model_message.set(f"验证结果: {status} {(error or '')[:160]}")

    def _discover_third_party_models(self) -> None:
        api_key = get_env_value(self.tp_api_key_env.get())
        if not api_key:
            self.model_message.set(f"未检测到环境变量 {self.tp_api_key_env.get()}，无法自动发现模型。")
            return
        if self.tp_provider.get() != "openai_compatible":
            self.model_message.set("自动发现当前只支持 OpenAI-compatible Provider。")
            return
        try:
            discovered = discover_openai_compatible_models(self.tp_base_url.get(), api_key)
        except Exception as exc:
            self.model_message.set(f"自动发现失败: {exc}")
            return
        if not discovered:
            self.model_message.set("自动发现没有返回可导入模型。")
            return
        imported = 0
        try:
            for item in discovered:
                item["base_url"] = self.tp_base_url.get()
                item["api_key_env"] = self.tp_api_key_env.get()
                if self.tp_roles.get() != "both":
                    item["roles"] = self.tp_roles.get()
                upsert_third_party_model(self.base_config, item)
                imported += 1
        except ValueError as exc:
            self.model_message.set(str(exc))
            return
        self._reload_model_catalog()
        self.model_message.set(f"自动发现并导入 {imported} 个模型。")

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
        try:
            for item in items:
                upsert_third_party_model(self.base_config, item)
        except ValueError as exc:
            self.model_message.set(str(exc))
            return
        self._reload_model_catalog()
        self.model_message.set(f"已导入 {len(items)} 个第三方模型。")

    def _reload_model_catalog(self) -> None:
        self.catalog = ModelCatalogView(self.base_config)
        self._populate_model_tree(self.vision_list, ROLE_VISION)
        self._populate_model_tree(self.brain_list, ROLE_BRAIN)
        if hasattr(self, "third_party_tree"):
            self._populate_third_party_tree(self.third_party_tree)


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


def _format_token_count(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.3f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return str(value)


def _catalog_diff_brief(diff: dict, errors: list[dict]) -> str:
    added = len(diff.get("added") or [])
    removed = len(diff.get("removed") or [])
    changed = len(diff.get("price_changed") or [])
    parts = [f"新增 {added}", f"消失 {removed}", f"价格变化 {changed}"]
    if errors:
        parts.append("错误：" + "；".join(f"{item.get('provider')}:{item.get('stage')}" for item in errors[:4]))
    return "差异摘要：" + "，".join(parts)


def _key_status_brief(env_name: str) -> str:
    env_name = (env_name or "").strip()
    if not env_name:
        return "未配置"
    return f"{env_name} {'已设置' if get_env_value(env_name) else '未设置'}"


def _verification_brief(verification: dict) -> str:
    if not verification:
        return "未验证"
    parts = []
    for key, label in (("vision", "Vision"), ("text", "文本"), ("dashscope", "DashScope")):
        value = verification.get(key)
        if value:
            parts.append(f"{label}:{'通过' if value == 'ok' else '失败'}")
    return "；".join(parts) if parts else "未验证"


def _filter_model_items(items: list[dict], filter_text: str) -> list[dict]:
    needle = (filter_text or "").strip().lower()
    if not needle:
        return items
    result = []
    for item in items:
        haystack = " ".join(
            str(item.get(key) or "")
            for key in ("source", "name", "provider", "model", "api_key_env")
        ).lower()
        if needle in haystack:
            result.append(item)
    return result


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
