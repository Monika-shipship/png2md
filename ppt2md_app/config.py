from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


DEFAULT_MODEL_VISION = "qwen3-vl-plus"
DEFAULT_MODEL_BRAIN = "qwen-plus"
DEFAULT_VISION_PROVIDER = "dashscope"
DEFAULT_BRAIN_PROVIDER = "dashscope"

DEFAULT_INPUT_FOLDER = "./ppt_images"
DEFAULT_OUTPUT_FOLDER = "./markdown_output"
DEFAULT_LOG_FOLDER = "./log"
DEFAULT_MODEL_CACHE_PATH = ".cache/aliyun_model_catalog.json"

DEFAULT_MAX_PPT_WORKERS = 1
DEFAULT_VISION_BATCH_WORKERS = 60
DEFAULT_BRAIN_BATCH_WORKERS = 60

DEFAULT_THINKING_BUDGET_VISION = 2048
DEFAULT_THINKING_BUDGET_BRAIN = 2048

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

# Model verification
DEFAULT_VERIFY_LIMIT = 20
DEFAULT_VERIFY_SLEEP = 0.3


@dataclass(frozen=True)
class AppConfig:
    session_name: str = "default"
    input_folder: str = DEFAULT_INPUT_FOLDER
    output_folder: str = DEFAULT_OUTPUT_FOLDER
    log_folder: str = DEFAULT_LOG_FOLDER
    vision_provider: str = DEFAULT_VISION_PROVIDER
    brain_provider: str = DEFAULT_BRAIN_PROVIDER
    model_vision: str = DEFAULT_MODEL_VISION
    model_brain: str = DEFAULT_MODEL_BRAIN
    vision_base_url: str = DEFAULT_OPENAI_BASE_URL
    vision_api_key_env: str = DEFAULT_DASHSCOPE_API_KEY_ENV
    brain_base_url: str = DEFAULT_OPENAI_BASE_URL
    brain_api_key_env: str = DEFAULT_DASHSCOPE_API_KEY_ENV
    vision_input_price_per_million: Optional[float] = None
    vision_output_price_per_million: Optional[float] = None
    brain_input_price_per_million: Optional[float] = None
    brain_output_price_per_million: Optional[float] = None
    max_ppt_workers: int = DEFAULT_MAX_PPT_WORKERS
    vision_batch_workers: int = DEFAULT_VISION_BATCH_WORKERS
    brain_batch_workers: int = DEFAULT_BRAIN_BATCH_WORKERS
    thinking_budget_vision: int = DEFAULT_THINKING_BUDGET_VISION
    thinking_budget_brain: int = DEFAULT_THINKING_BUDGET_BRAIN
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
    def model_cache_abs_path(self) -> Path:
        return Path(self.model_cache_path)
