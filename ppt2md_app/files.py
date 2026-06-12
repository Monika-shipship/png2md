import datetime
import json
import logging
import os
import re
import time
from pathlib import Path

from .config import AppConfig
from .env import get_env_value


def setup_logger(config: AppConfig):
    config.log_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = config.log_path / f"log_{config.session_name}_{timestamp}.log"

    logger = logging.getLogger(f"PPT2MD_{config.session_name}")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s - [%(processName)s] - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger, str(log_file)


def ensure_input_folder(config: AppConfig):
    if not config.input_path.exists():
        try:
            config.input_path.mkdir(parents=True, exist_ok=True)
            return False, f"⚠️ 输入文件夹 {config.input_folder} 不存在，已创建。请把图片放进去后重新运行。"
        except OSError:
            return False, f"❌ 无法创建文件夹 {config.input_folder}。"

    return True, "输入文件夹检查通过"


def check_runtime_env(config: AppConfig):
    required = _required_api_envs(config)
    if not required:
        return "set", "环境检查通过"

    missing = []
    first_key = None
    for role, provider, env_name in required:
        value = get_env_value(env_name)
        if value:
            first_key = first_key or value
            continue

        if provider == "dashscope":
            try:
                import dashscope

                if dashscope.api_key:
                    first_key = first_key or dashscope.api_key
                    continue
            except ImportError:
                pass

        missing.append((role, provider, env_name))

    if missing:
        lines = [
            "❌ 未检测到所选模型需要的 API Key 环境变量：",
            *[f"  - {role}: {provider} 需要 {env_name}" for role, provider, env_name in missing],
            "请在模型选择的自定义 API 流程中粘贴保存，或手动设置系统环境变量后重新运行。",
        ]
        return None, "\n".join(lines)

    return first_key or "set", "环境检查通过"


def _required_api_envs(config: AppConfig):
    items = [
        ("Step 1 Vision", config.vision_provider, config.vision_api_key_env),
        ("Step 2 Brain", config.brain_provider, config.brain_api_key_env),
    ]
    required = []
    seen = set()
    for role, provider, env_name in items:
        if not env_name:
            continue
        key = (provider, env_name)
        if key in seen:
            continue
        if provider in ("dashscope", "dashscope_openai", "deepseek", "openai_compatible"):
            required.append((role, provider, env_name))
            seen.add(key)
    return required


def check_env(config: AppConfig):
    ok, msg = ensure_input_folder(config)
    if not ok:
        return None, msg
    return check_runtime_env(config)


def check_dashscope_env(config: AppConfig):
    """Backward-compatible alias for callers that only need DashScope defaults."""
    import dashscope

    api_key = get_env_value("DASHSCOPE_API_KEY")
    if not api_key and dashscope.api_key is None:
        return None, "❌ 未检测到 API Key。请设置环境变量 DASHSCOPE_API_KEY。"

    final_key = api_key if api_key else dashscope.api_key
    return final_key, "环境检查通过"


def natural_sort_key(s):
    name = s.name if hasattr(s, "name") else str(s)
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", name)]


def scan_ppt_folders(root_folder):
    root = Path(root_folder)
    if not root.exists():
        return {}

    tasks = {}
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    for entry in root.iterdir():
        if entry.is_dir():
            images = [f for f in entry.iterdir() if f.suffix.lower() in exts]
            if images:
                images.sort(key=natural_sort_key)
                tasks[entry.name] = [str(img.absolute()) for img in images]
    return tasks


def extract_context(text):
    pattern = r"<CTX>(.*?)</CTX>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return match.group(1).replace("```json", "").replace("```", "").strip()
        except Exception:
            return "Context parse error."
    return "No context from previous page."


def merge_markdowns(ppt_output_dir, ppt_name):
    output_dir = Path(ppt_output_dir)
    final_path = output_dir / f"{ppt_name}_FULL.md"
    md_files = sorted(output_dir.glob("Slide_*.md"), key=natural_sort_key)
    if not md_files:
        return

    with final_path.open("w", encoding="utf-8") as outfile:
        outfile.write(
            f"# {ppt_name} 汇总笔记\n\n"
            f"> 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            "> 引擎: V10 (Parallel Brain)\n\n"
        )
        for md_file in md_files:
            with md_file.open("r", encoding="utf-8") as infile:
                outfile.write(infile.read())
                outfile.write("\n\n---\n\n")


def read_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    with Path(path).open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
