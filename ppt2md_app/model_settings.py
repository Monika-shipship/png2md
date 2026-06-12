import json
from dataclasses import replace
from typing import Dict, List

from .config import AppConfig
from .env import get_deepseek_api_key, get_env_value, set_user_env_value
from .model_catalog import (
    ROLE_BRAIN,
    ROLE_VISION,
    ModelPrice,
    load_model_catalog,
)
from .aliyun_catalog import (
    ModelRecord,
    filter_brain_models,
    filter_vision_models,
    verify_openai_chat_model,
    vision_recommendation_tier,
)


def configure_models(console, config: AppConfig):
    """交互式模型配置入口。使用动态+静态合并目录。"""
    console.print("[dim]正在加载模型目录（缓存优先，不联网）...[/]")
    records = load_model_catalog(
        prefer_cache=True,
        cache_path=config.model_cache_path,
    )
    console.print(f"[dim]已加载 {len(records)} 个模型。[/]")

    saved = load_model_settings(config)
    if saved:
        saved_config = apply_model_settings(config, saved)
        console.print(
            "[bold cyan]模型配置[/]: "
            f"Vision={saved_config.model_vision} | "
            f"Brain={saved_config.brain_provider}:{saved_config.model_brain}"
        )
        choice = input("👉 是否沿用上次模型配置？(y/n) [默认为 y]: ").strip().lower()
        if choice != "n":
            _ensure_api_keys_for_config(console, saved_config)
            return saved_config

    vision_config = choose_model(
        console=console,
        config=config,
        records=records,
        role=ROLE_VISION,
        title="Step 1 视觉模型",
        default_provider=config.vision_provider,
        default_model=config.model_vision,
    )
    final_config = choose_model(
        console=console,
        config=vision_config,
        records=records,
        role=ROLE_BRAIN,
        title="Step 2 Brain 模型",
        default_provider="deepseek" if get_deepseek_api_key() else config.brain_provider,
        default_model="deepseek-v4-flash" if get_deepseek_api_key() else config.model_brain,
    )

    if final_config.brain_provider == "deepseek" and not get_env_value(final_config.brain_api_key_env):
        console.print("[bold yellow]未检测到 DEEPSEEK_API_KEY，DeepSeek Brain 会失败。[/]")
        save_key = input("👉 是否现在粘贴并保存 DeepSeek API Key？(y/n) [默认为 y]: ").strip().lower()
        if save_key != "n":
            _prompt_and_save_api_key(console, final_config.brain_api_key_env)

    if final_config.brain_provider == "deepseek" and not get_env_value(final_config.brain_api_key_env):
        fallback = input("👉 改用 qwen-plus 吗？(y/n) [默认为 y]: ").strip().lower()
        if fallback != "n":
            final_config = replace(
                final_config,
                brain_provider="dashscope",
                model_brain="qwen-plus",
                brain_input_price_per_million=None,
                brain_output_price_per_million=None,
            )

    _ensure_api_keys_for_config(console, final_config)
    save_model_settings(config, final_config)
    return final_config


def choose_model(
    console,
    config: AppConfig,
    records: List[ModelRecord],
    role: str,
    title: str,
    default_provider: str,
    default_model: str,
):
    """紧凑版模型选择：每行一行，适合窄终端。"""
    from .aliyun_catalog import vision_recommendation_tier

    # 按角色过滤
    if role == ROLE_VISION:
        candidates = filter_vision_models(records)
        candidates.sort(key=lambda r: (vision_recommendation_tier(r), r.model_id))
        _print_vision_candidates(console, candidates, title, default_provider, default_model)
    else:
        candidates = [
            r for r in filter_brain_models(records)
            if ROLE_BRAIN in getattr(r, "stage_suitable", []) or r.openai_text_status == "ok"
        ]
        _print_brain_candidates(console, candidates, title, default_provider, default_model)

    display = candidates[:80]
    default_index = _find_record_index(display, default_provider, default_model)

    selected = input(f">> 选择 [默认 {default_index}, c=自定义]: ").strip().lower()
    if not selected:
        selected = str(default_index)

    if selected == "c":
        return _custom_model_config_enhanced(console, config, role)

    try:
        index = int(selected)
    except ValueError:
        index = default_index
    if not 1 <= index <= len(display):
        index = default_index

    return _apply_record(config, role, display[index - 1])


def _print_vision_candidates(console, candidates, title, default_provider, default_model):
    """紧凑版 Vision 模型列表。"""
    from .aliyun_catalog import vision_recommendation_tier

    tier_labels = {0: "REC", 1: "CAN", 2: "FAIL"}
    console.print(f"\n[bold cyan]{title}[/] [dim](REC=已验证推荐 CAN=候选 FAIL=验证失败)[/]")
    console.print(f"[dim]{'':>3} {'Tier':4} {'Model ID':30} {'Vision':8} {'Price(in/out)/M':18} {'Source':10}[/]")
    console.print("[dim]" + "-" * 86 + "[/]")

    default_index = _find_record_index(candidates, default_provider, default_model)

    for i, rec in enumerate(candidates[:80], start=1):
        marker = "*" if i == default_index else " "
        tier = vision_recommendation_tier(rec)
        tier_label = tier_labels.get(tier, "   ")

        ov = _cap_icon(rec.openai_vision_status)
        dm = _cap_icon(rec.dashscope_multimodal_status)
        vis_status = f"{ov}/{dm}"

        inp = f"{rec.input_price:.3g}" if rec.input_price is not None else "?"
        out = f"{rec.output_price:.3g}" if rec.output_price is not None else "?"
        price = f"{inp}/{out}"
        src = (rec.price_source or "-")[:10]

        line = f"{marker}{i:>2d}  {tier_label:4} {rec.model_id:30} {vis_status:8} {price:18} {src:10}"
        style = ""
        if tier == 0:
            style = "green"
        elif tier == 2:
            style = "red"
        elif tier == 1:
            style = "dim"

        if style:
            console.print(f"[{style}]{line}[/]")
        else:
            console.print(line)

    console.print(f"[dim]{'c':>3}  {'CUS':4} {'自定义模型':30}[/]")
    console.print()


def _print_brain_candidates(console, candidates, title, default_provider, default_model):
    """紧凑版 Brain 模型列表。"""
    console.print(f"\n[bold cyan]{title}[/] [dim](文本模型 + 多模态，多模态用于 Brain 成本可能更高)[/]")
    console.print(f"[dim]{'':>3} {'':4} {'Model ID':30} {'Text':6} {'Price(in/out)/M':18} {'Source':10} {'Provider':10}[/]")
    console.print("[dim]" + "-" * 86 + "[/]")

    default_index = _find_record_index(candidates, default_provider, default_model)

    for i, rec in enumerate(candidates[:80], start=1):
        marker = "*" if i == default_index else " "
        txt = _cap_icon(rec.openai_text_status)

        inp = f"{rec.input_price:.3g}" if rec.input_price is not None else "?"
        out = f"{rec.output_price:.3g}" if rec.output_price is not None else "?"
        price = f"{inp}/{out}"
        src = (rec.price_source or "-")[:10]
        prov = rec.provider[:10]

        # 高亮已通过文本验证的模型
        style = "green" if rec.openai_text_status == "ok" else ""
        line = f"{marker}{i:>2d}  {'':4} {rec.model_id:30} {txt:6} {price:18} {src:10} {prov:10}"
        if style:
            console.print(f"[{style}]{line}[/]")
        else:
            console.print(line)

    console.print(f"[dim]{'c':>3}  {'CUS':4} {'自定义模型':30}[/]")
    console.print()


def _cap_icon(status: str) -> str:
    """能力矩阵图标。"""
    if status == "ok":
        return "✅"
    if status == "failed":
        return "❌"
    if status == "skipped":
        return "⏭"
    return "·"


def _find_record_index(records, provider, model_id):
    for i, rec in enumerate(records, start=1):
        if rec.provider == provider and rec.model_id == model_id:
            return i
    return 1


def _apply_record(config: AppConfig, role: str, rec: ModelRecord):
    """将 ModelRecord 应用到 AppConfig。"""
    base_url, api_key_env = _provider_defaults(rec.provider, role, config)
    if role == ROLE_VISION:
        return replace(
            config,
            vision_provider=rec.provider,
            model_vision=rec.model_id,
            vision_base_url=base_url,
            vision_api_key_env=api_key_env,
            vision_input_price_per_million=rec.input_price,
            vision_output_price_per_million=rec.output_price,
        )
    return replace(
        config,
        brain_provider=rec.provider,
        model_brain=rec.model_id,
        brain_base_url=base_url,
        brain_api_key_env=api_key_env,
        brain_input_price_per_million=rec.input_price,
        brain_output_price_per_million=rec.output_price,
    )


def _provider_defaults(provider, role, config: AppConfig):
    if provider == "deepseek":
        return "https://api.deepseek.com", "DEEPSEEK_API_KEY"
    if provider in ("dashscope", "dashscope_openai"):
        return config.openai_base_url, "DASHSCOPE_API_KEY"
    return (
        config.vision_base_url if role == ROLE_VISION else config.brain_base_url,
        config.vision_api_key_env if role == ROLE_VISION else config.brain_api_key_env,
    )


def _custom_model_config_enhanced(console, config: AppConfig, role: str):
    """增强版自定义模型输入，支持可选 API 验证。"""
    provider, base_url, api_key_env = _read_custom_provider(console, config, role)

    model_id = input("   模型 ID: ").strip()
    if not model_id:
        model_id = config.model_vision if role == ROLE_VISION else config.model_brain

    input_price = _read_optional_float("   输入价格 元/百万 tokens (未知可回车): ")
    output_price = _read_optional_float("   输出价格 元/百万 tokens (未知可回车): ")

    # 可选 API 验证
    verify_choice = input("   要立即用 API 验证该模型吗？(y/n/skip) [默认 skip]: ").strip().lower()
    verified_status = "unknown"
    if verify_choice in ("y", "yes"):
        api_key = get_env_value(api_key_env)
        if not api_key:
            console.print(f"   [bold yellow]未检测到 {api_key_env}，跳过验证。[/]")
        else:
            is_vis = (role == ROLE_VISION)
            console.print(f"   [dim]正在验证 {model_id} ...[/]", end="")
            status, error = verify_openai_chat_model(
                model_id, api_key, base_url, is_vision=is_vis,
            )
            verified_status = "ok" if status == "ok" else "failed"
            icon = "✅" if status == "ok" else "❌"
            summary = (error or "OK")[:120].replace("\n", " ")
            console.print(f" {icon} [{verified_status}] {summary}")

    if role == ROLE_VISION:
        return replace(
            config,
            vision_provider=provider,
            model_vision=model_id,
            vision_base_url=base_url,
            vision_api_key_env=api_key_env,
            vision_input_price_per_million=input_price,
            vision_output_price_per_million=output_price,
        )
    return replace(
        config,
        brain_provider=provider,
        model_brain=model_id,
        brain_base_url=base_url,
        brain_api_key_env=api_key_env,
        brain_input_price_per_million=input_price,
        brain_output_price_per_million=output_price,
    )


def _read_custom_provider(console, config: AppConfig, role: str):
    console.print("\n[bold]自定义 API 类型[/]")
    options = [
        ("1", "dashscope", "阿里云 DashScope 原生接口，适合 Vision 默认路径"),
        ("2", "dashscope_openai", "阿里云 OpenAI 兼容接口"),
        ("3", "deepseek", "DeepSeek OpenAI 兼容接口，适合 Brain"),
        ("4", "openai_compatible", "其他 OpenAI 兼容服务，例如 One API、OpenRouter、LiteLLM、自建转发"),
    ]
    for key, provider, desc in options:
        console.print(f"   [{key}] {provider} - {desc}")

    default_choice = "1" if role == ROLE_VISION else "3"
    choice = input(f"   选择 API 类型 [默认 {default_choice}]: ").strip() or default_choice
    provider = next((p for key, p, _ in options if key == choice), None) or choice.strip().lower()

    if role == ROLE_VISION and provider == "deepseek":
        console.print("   [yellow]DeepSeek 当前不支持图片输入，Vision 已改为 openai_compatible。[/]")
        provider = "openai_compatible"

    default_base, default_env = _provider_defaults(provider, role, config)
    base_url = default_base
    if provider != "dashscope":
        base_url = input(f"   Base URL [默认 {default_base}]: ").strip() or default_base
    elif role == ROLE_VISION:
        console.print("   DashScope 原生 Vision 不需要填写 Base URL。")

    api_key_env = input(f"   API Key 环境变量名 [默认 {default_env}]: ").strip() or default_env
    if not get_env_value(api_key_env):
        console.print(f"   [yellow]当前未检测到环境变量 {api_key_env}。[/]")
        save_key = input("   是否现在粘贴 API Key 并保存到当前用户环境变量？(y/n) [默认 n]: ").strip().lower()
        if save_key == "y":
            _prompt_and_save_api_key(console, api_key_env, indent="   ")

    return provider, base_url, api_key_env


def _ensure_api_keys_for_config(console, config: AppConfig):
    required = [
        ("Step 1 Vision", config.vision_provider, config.vision_api_key_env),
        ("Step 2 Brain", config.brain_provider, config.brain_api_key_env),
    ]
    seen = set()
    for role, provider, env_name in required:
        if not env_name or env_name in seen:
            continue
        seen.add(env_name)
        if provider not in ("dashscope", "dashscope_openai", "deepseek", "openai_compatible"):
            continue
        if get_env_value(env_name):
            continue

        console.print(f"[yellow]{role} 需要环境变量 {env_name}，当前未检测到。[/]")
        save_key = input(f"👉 是否现在粘贴并保存 {env_name}？(y/n) [默认 n]: ").strip().lower()
        if save_key == "y":
            _prompt_and_save_api_key(console, env_name)


def _prompt_and_save_api_key(console, env_name: str, indent: str = ""):
    key_value = input(f"{indent}粘贴 API Key（不会写入仓库文件）: ").strip()
    if not key_value:
        return
    if set_user_env_value(env_name, key_value):
        console.print(f"{indent}[green]已写入用户环境变量 {env_name}。新开终端也可以读取。[/]")
    else:
        console.print(
            f"{indent}[yellow]已写入当前进程环境变量 {env_name}；"
            "若下次启动读不到，请手动设置系统环境变量。[/]"
        )


# ---- 以下函数保持不变（兼容旧 ModelSpec 的路径） ----

def load_model_settings(config: AppConfig):
    if not config.model_settings_path.exists():
        return None
    try:
        with config.model_settings_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_model_settings(base_config: AppConfig, selected_config: AppConfig):
    base_config.log_path.mkdir(parents=True, exist_ok=True)
    data = {
        "vision_provider": selected_config.vision_provider,
        "model_vision": selected_config.model_vision,
        "vision_base_url": selected_config.vision_base_url,
        "vision_api_key_env": selected_config.vision_api_key_env,
        "vision_input_price_per_million": selected_config.vision_input_price_per_million,
        "vision_output_price_per_million": selected_config.vision_output_price_per_million,
        "brain_provider": selected_config.brain_provider,
        "model_brain": selected_config.model_brain,
        "brain_base_url": selected_config.brain_base_url,
        "brain_api_key_env": selected_config.brain_api_key_env,
        "brain_input_price_per_million": selected_config.brain_input_price_per_million,
        "brain_output_price_per_million": selected_config.brain_output_price_per_million,
    }
    with base_config.model_settings_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def apply_model_settings(config: AppConfig, settings: Dict):
    return replace(
        config,
        vision_provider=settings.get("vision_provider", config.vision_provider),
        model_vision=settings.get("model_vision", config.model_vision),
        vision_base_url=settings.get("vision_base_url", config.vision_base_url),
        vision_api_key_env=settings.get("vision_api_key_env", config.vision_api_key_env),
        vision_input_price_per_million=settings.get("vision_input_price_per_million"),
        vision_output_price_per_million=settings.get("vision_output_price_per_million"),
        brain_provider=settings.get("brain_provider", config.brain_provider),
        model_brain=settings.get("model_brain", config.model_brain),
        brain_base_url=settings.get("brain_base_url", config.brain_base_url),
        brain_api_key_env=settings.get("brain_api_key_env", config.brain_api_key_env),
        brain_input_price_per_million=settings.get("brain_input_price_per_million"),
        brain_output_price_per_million=settings.get("brain_output_price_per_million"),
    )


def _read_optional_float(prompt):
    raw = input(prompt).strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def get_configured_price(config: AppConfig, role: str):
    if role == ROLE_VISION:
        return ModelPrice(
            input_per_million=config.vision_input_price_per_million,
            output_per_million=config.vision_output_price_per_million,
        )
    return ModelPrice(
        input_per_million=config.brain_input_price_per_million,
        output_per_million=config.brain_output_price_per_million,
    )
