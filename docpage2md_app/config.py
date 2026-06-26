from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_MODEL_VISION = "qwen3-vl-plus"
DEFAULT_MODEL_BRAIN = "deepseek-v4-flash"
DEFAULT_VISION_PROVIDER = "dashscope"
DEFAULT_BRAIN_PROVIDER = "deepseek"
DEFAULT_ENGINE_MODE = "vision_only"
DEFAULT_DOCUMENT_TYPE = "custom"
DEFAULT_MODEL_PROFILE = "balanced"
DEFAULT_MINERU_MODEL_VERSION = "vlm"
DEFAULT_MINERU_IS_OCR = True
DEFAULT_MINERU_ENABLE_FORMULA = True
DEFAULT_MINERU_ENABLE_TABLE = True
DEFAULT_MINERU_LANGUAGE = "ch"
DEFAULT_MINERU_PAGE_CHUNK_SIZE = 200

DEFAULT_INPUT_FOLDER = "./doc_pages"
DEFAULT_OUTPUT_FOLDER = "./markdown_output"
DEFAULT_LOG_FOLDER = "./log"
DEFAULT_MODEL_CACHE_PATH = ".cache/aliyun_model_catalog.json"
DEFAULT_OUTPUT_RETENTION = "slim"
OUTPUT_RETENTION_MODES = ("slim", "standard", "debug")

DEFAULT_MAX_DOCPAGE_WORKERS = 1
DEFAULT_PARSER_WORKERS = 8
DEFAULT_VISION_BATCH_WORKERS = 60
DEFAULT_BRAIN_BATCH_WORKERS = 60
DEFAULT_BRAIN_CONTEXT_RADIUS = 2

DEFAULT_THINKING_BUDGET_VISION = 2048
DEFAULT_THINKING_BUDGET_BRAIN = 2048
DEFAULT_BRAIN_THINKING = "disabled"
DEFAULT_BRAIN_REASONING_EFFORT = "high"

# API retry / backoff
DEFAULT_API_MAX_RETRIES = 3
DEFAULT_API_RETRY_BASE_SLEEP = 2.0
DEFAULT_API_RETRY_MAX_SLEEP = 60.0

# Aliyun OpenAI-compatible endpoint
DEFAULT_REGION = "cn-beijing"
DEFAULT_OPENAI_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEFAULT_DASHSCOPE_API_KEY_ENV = "DASHSCOPE_API_KEY"
DEFAULT_DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"
DEFAULT_MINERU_API_TOKEN_ENV = "MINERU_API_TOKEN"
DEFAULT_PADDLEOCR_API_TOKEN_ENV = "PADDLEOCR_API_TOKEN"
DEFAULT_PADDLEOCR_BASE_URL = "https://paddleocr.aistudio-app.com"
DEFAULT_PADDLEOCR_MODEL = "PaddleOCR-VL-1.6"
DEFAULT_PADDLEOCR_PAGE_CHUNK_SIZE = 100

# Model verification
DEFAULT_VERIFY_LIMIT = 20
DEFAULT_VERIFY_SLEEP = 0.3


@dataclass(frozen=True)
class AppConfig:
    session_name: str = "default"
    input_folder: str = DEFAULT_INPUT_FOLDER
    output_folder: str = DEFAULT_OUTPUT_FOLDER
    log_folder: str = DEFAULT_LOG_FOLDER
    engine_mode: str = DEFAULT_ENGINE_MODE
    document_type: str = DEFAULT_DOCUMENT_TYPE
    model_profile: str = DEFAULT_MODEL_PROFILE
    vision_provider: str = DEFAULT_VISION_PROVIDER
    brain_provider: str = DEFAULT_BRAIN_PROVIDER
    model_vision: str = DEFAULT_MODEL_VISION
    model_brain: str = DEFAULT_MODEL_BRAIN
    vision_base_url: str = DEFAULT_OPENAI_BASE_URL
    vision_api_key_env: str = DEFAULT_DASHSCOPE_API_KEY_ENV
    brain_base_url: str = DEFAULT_DEEPSEEK_BASE_URL
    brain_api_key_env: str = DEFAULT_DEEPSEEK_API_KEY_ENV
    mineru_api_token_env: str = DEFAULT_MINERU_API_TOKEN_ENV
    mineru_model_version: str = DEFAULT_MINERU_MODEL_VERSION
    mineru_base_url: str = "https://mineru.net"
    mineru_artifact_dir: Optional[str] = None
    mineru_page_ranges: Optional[str] = None
    mineru_is_ocr: bool = DEFAULT_MINERU_IS_OCR
    mineru_enable_formula: bool = DEFAULT_MINERU_ENABLE_FORMULA
    mineru_enable_table: bool = DEFAULT_MINERU_ENABLE_TABLE
    mineru_language: str = DEFAULT_MINERU_LANGUAGE
    mineru_auto_split_pages: bool = False
    mineru_page_chunk_size: int = DEFAULT_MINERU_PAGE_CHUNK_SIZE
    layout_engine: str = "mineru"
    refine_mode: str = "none"
    paddleocr_api_key_env: str = DEFAULT_PADDLEOCR_API_TOKEN_ENV
    paddleocr_base_url: str = DEFAULT_PADDLEOCR_BASE_URL
    paddleocr_model: str = DEFAULT_PADDLEOCR_MODEL
    paddleocr_artifact_dir: Optional[str] = None
    paddleocr_page_chunk_size: int = DEFAULT_PADDLEOCR_PAGE_CHUNK_SIZE
    paddleocr_doc_orientation: bool = False
    paddleocr_doc_unwarping: bool = False
    paddleocr_chart_recognition: bool = False
    paddleocr_layout_detection: bool = True
    paddleocr_formula_recognition: bool = True
    paddleocr_table_recognition: bool = True
    paddleocr_visualize: bool = False
    output_retention: str = DEFAULT_OUTPUT_RETENTION
    vision_input_price_per_million: Optional[float] = None
    vision_output_price_per_million: Optional[float] = None
    brain_input_price_per_million: Optional[float] = None
    brain_output_price_per_million: Optional[float] = None
    max_docpage_workers: int = DEFAULT_MAX_DOCPAGE_WORKERS
    parser_workers: int = DEFAULT_PARSER_WORKERS
    vision_batch_workers: int = DEFAULT_VISION_BATCH_WORKERS
    brain_batch_workers: int = DEFAULT_BRAIN_BATCH_WORKERS
    brain_context_radius: int = DEFAULT_BRAIN_CONTEXT_RADIUS
    thinking_budget_vision: int = DEFAULT_THINKING_BUDGET_VISION
    thinking_budget_brain: int = DEFAULT_THINKING_BUDGET_BRAIN
    brain_thinking: str = DEFAULT_BRAIN_THINKING
    brain_reasoning_effort: str = DEFAULT_BRAIN_REASONING_EFFORT
    # API retry
    api_max_retries: int = DEFAULT_API_MAX_RETRIES
    api_retry_base_sleep: float = DEFAULT_API_RETRY_BASE_SLEEP
    api_retry_max_sleep: float = DEFAULT_API_RETRY_MAX_SLEEP
    # Model catalog
    model_cache_path: str = DEFAULT_MODEL_CACHE_PATH
    region: str = DEFAULT_REGION
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL
    verify_limit: int = DEFAULT_VERIFY_LIMIT
    verify_sleep: float = DEFAULT_VERIFY_SLEEP
    # Operation mode flags (not persisted, only for CLI dispatch)
    list_models: bool = False
    list_all_models: bool = False
    refresh_models: bool = False
    verify_models: bool = False
    refresh_providers: str = "dashscope,deepseek"
    show_model_diff: bool = False
    import_pricing_md: Optional[str] = None
    fix_ocr_confusion: bool = False

    @property
    def session_file_name(self) -> str:
        return f"session_{self.session_name}.json"

    @property
    def session_dir(self) -> Path:
        return self.log_path / "sessions"

    @property
    def session_path(self) -> Path:
        return self.session_dir / self.session_file_name

    @property
    def legacy_session_path(self) -> Path:
        return Path(self.session_file_name)

    @property
    def input_path(self) -> Path:
        return Path(self.input_folder)

    @property
    def output_path(self) -> Path:
        return Path(self.output_folder)

    @property
    def log_path(self) -> Path:
        return Path(self.log_folder)

    @property
    def model_settings_path(self) -> Path:
        return self.log_path / "model_settings.json"

    @property
    def third_party_models_path(self) -> Path:
        return self.log_path / "third_party_models.json"

    @property
    def model_cache_abs_path(self) -> Path:
        return Path(self.model_cache_path)
