from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from .aliyun_catalog import ModelRecord
from .deepseek_tokenizer import count_chat_tokens, count_text_tokens, heuristic_text_tokens


QWEN_VISION_FACTOR = 32
QWEN_VISION_TOKEN_PIXELS = QWEN_VISION_FACTOR * QWEN_VISION_FACTOR
QWEN_VISION_MIN_PIXELS = 4 * QWEN_VISION_TOKEN_PIXELS
QWEN_VISION_DEFAULT_MAX_PIXELS = 2560 * QWEN_VISION_TOKEN_PIXELS
QWEN_VISION_HIGH_RES_MAX_PIXELS = 16384 * QWEN_VISION_TOKEN_PIXELS


@dataclass(frozen=True)
class ImageTokenEstimate:
    width: int
    height: int
    resized_width: int
    resized_height: int
    tokens: int
    factor: int = QWEN_VISION_FACTOR
    token_pixels: int = QWEN_VISION_TOKEN_PIXELS
    max_pixels: int = QWEN_VISION_DEFAULT_MAX_PIXELS
    min_pixels: int = QWEN_VISION_MIN_PIXELS
    source: str = "qwen_vl_smart_resize"


def calculate_image_tokens(
    image_path,
    *,
    max_pixels: int = QWEN_VISION_DEFAULT_MAX_PIXELS,
    min_pixels: int = QWEN_VISION_MIN_PIXELS,
    factor: int = QWEN_VISION_FACTOR,
    vl_high_resolution_images: bool = False,
    fallback_tokens: int = 2000,
) -> int:
    """
    按 Qwen3-VL/Qwen3.5/3.6/3.7 官方 smart resize 规则估算图像 token。

    图像 Token = resized_h * resized_w / (factor * factor) + 2。
    实际账单仍以 API usage 为准。
    """
    try:
        return estimate_image_tokens(
            image_path,
            max_pixels=max_pixels,
            min_pixels=min_pixels,
            factor=factor,
            vl_high_resolution_images=vl_high_resolution_images,
        ).tokens
    except Exception:
        return fallback_tokens


def estimate_image_tokens(
    image_path,
    *,
    max_pixels: int = QWEN_VISION_DEFAULT_MAX_PIXELS,
    min_pixels: int = QWEN_VISION_MIN_PIXELS,
    factor: int = QWEN_VISION_FACTOR,
    vl_high_resolution_images: bool = False,
) -> ImageTokenEstimate:
    from PIL import Image

    image_path = Path(image_path)
    with Image.open(image_path) as img:
        width, height = img.width, img.height
    resized_h, resized_w, effective_max = smart_resize_dimensions(
        height,
        width,
        max_pixels=max_pixels,
        min_pixels=min_pixels,
        factor=factor,
        vl_high_resolution_images=vl_high_resolution_images,
    )
    tokens = int((resized_h * resized_w) / (factor * factor)) + 2
    return ImageTokenEstimate(
        width=width,
        height=height,
        resized_width=resized_w,
        resized_height=resized_h,
        tokens=tokens,
        factor=factor,
        token_pixels=factor * factor,
        max_pixels=effective_max,
        min_pixels=min_pixels,
    )


def smart_resize_dimensions(
    height: int,
    width: int,
    *,
    max_pixels: int = QWEN_VISION_DEFAULT_MAX_PIXELS,
    min_pixels: int = QWEN_VISION_MIN_PIXELS,
    factor: int = QWEN_VISION_FACTOR,
    vl_high_resolution_images: bool = False,
) -> tuple[int, int, int]:
    """Return `(resized_height, resized_width, effective_max_pixels)`."""
    if height <= 0 or width <= 0:
        raise ValueError("image width and height must be positive")
    if factor <= 0:
        raise ValueError("factor must be positive")
    if min_pixels <= 0 or max_pixels <= 0:
        raise ValueError("pixel limits must be positive")
    effective_max = 16384 * factor * factor if vl_high_resolution_images else max_pixels

    h_bar = _round_by_factor(height, factor)
    w_bar = _round_by_factor(width, factor)

    if h_bar * w_bar > effective_max:
        beta = math.sqrt((height * width) / effective_max)
        h_bar = _floor_by_factor(height / beta, factor)
        w_bar = _floor_by_factor(width / beta, factor)
    elif h_bar * w_bar < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        h_bar = _ceil_by_factor(height * beta, factor)
        w_bar = _ceil_by_factor(width * beta, factor)
    return max(factor, h_bar), max(factor, w_bar), effective_max


def _round_by_factor(number: float, factor: int) -> int:
    return int(round(number / factor) * factor)


def _ceil_by_factor(number: float, factor: int) -> int:
    return int(math.ceil(number / factor) * factor)


def _floor_by_factor(number: float, factor: int) -> int:
    return int(math.floor(number / factor) * factor)


def estimate_deepseek_text_tokens(text: str, *, fallback: bool = True) -> int:
    """Estimate DeepSeek text tokens using the bundled official tokenizer."""
    try:
        return count_text_tokens(text or "")
    except Exception:
        if not fallback:
            raise
        return heuristic_text_tokens(text or "")


def estimate_deepseek_chat_tokens(messages: list[dict], *, fallback: bool = True) -> int:
    """Estimate DeepSeek chat prompt tokens with the app's simple user-message calls."""
    try:
        return count_chat_tokens(messages, add_generation_prompt=True)
    except Exception:
        if not fallback:
            raise
        return heuristic_text_tokens("\n".join(str(message.get("content") or "") for message in messages))


def estimate_price(model_type, input_tokens, output_tokens):
    """
    根据阶梯计费估算价格，单位为元。
    保留作为旧代码兼容（当 ModelRecord 不存在时作为 fallback）。
    """
    cost = 0.0

    if model_type == "qwen3-vl-plus":
        if input_tokens <= 32000:
            cost += (input_tokens / 1000) * 0.001
        elif input_tokens <= 128000:
            cost += (input_tokens / 1000) * 0.0015
        else:
            cost += (input_tokens / 1000) * 0.003

        if output_tokens <= 32000:
            cost += (output_tokens / 1000) * 0.01
        elif output_tokens <= 128000:
            cost += (output_tokens / 1000) * 0.015
        else:
            cost += (output_tokens / 1000) * 0.03

    elif model_type == "qwen-plus":
        if input_tokens <= 128000:
            cost += (input_tokens / 1000) * 0.0008
        elif input_tokens <= 256000:
            cost += (input_tokens / 1000) * 0.0024
        else:
            cost += (input_tokens / 1000) * 0.0048

        cost += (output_tokens / 1000) * 0.002

    return cost


def estimate_text_cost(
    input_tokens: int,
    output_tokens: int,
    model_record=None,
    cache_hit_tokens: int = 0,
) -> float | None:
    """根据 ModelRecord 估算文本成本，支持阶梯价格和上下文缓存。

    Args:
        input_tokens: 输入 token 数。
        output_tokens: 输出 token 数。
        model_record: 来自 aliyun_catalog 的 ModelRecord（必须有价格信息）。
        cache_hit_tokens: 上下文缓存命中的输入 token 数。

    Returns:
        预估成本（元），如果价格信息缺失则返回 None。
    """
    if model_record is None:
        return None

    inp_price = model_record.input_price
    out_price = model_record.output_price
    cached_price = model_record.cached_input_price

    if inp_price is None and out_price is None:
        return None

    # 阶梯价格（如果存在 price_tiers）
    inp_price = _resolve_tier_price(input_tokens, model_record.price_tiers, "input", inp_price)
    # 这些价格表的档位按“输入 token 范围”确定；输出单价也随同一输入档位变化。
    out_price = _resolve_tier_price(input_tokens, model_record.price_tiers, "output", out_price)

    if inp_price is None:
        inp_price = 0.0
    if out_price is None:
        out_price = 0.0

    # 单位转换：ModelRecord 价格为 元/百万tokens
    cost = 0.0

    # 缓存命中的输入
    if cache_hit_tokens > 0 and cached_price is not None:
        cost += (cache_hit_tokens / 1_000_000) * cached_price
        remaining_input = max(0, input_tokens - cache_hit_tokens)
        cost += (remaining_input / 1_000_000) * inp_price
    else:
        cost += (input_tokens / 1_000_000) * inp_price

    cost += (output_tokens / 1_000_000) * out_price

    return cost


def _resolve_tier_price(
    tokens: int,
    tiers: list,
    field: str,
    default: float | None,
) -> float | None:
    """从阶梯价格表中选择适用的单价。

    阶梯规则：整次请求按输入 token 所在区间的价格计费（非分段累加）。
    tiers 格式：[{"max_tokens": 32000, "input": 1.0, "output": 10.0}, ...]
    """
    if not tiers:
        return default
    for tier in sorted(tiers, key=lambda t: t.get("max_tokens", 0)):
        if tokens <= tier.get("max_tokens", float("inf")):
            return tier.get(field, default)
    # 超出所有阶梯 → 用最后一档
    return tiers[-1].get(field, default) if tiers else default


def estimate_flat_price(input_tokens, output_tokens, input_price_per_million, output_price_per_million):
    if input_price_per_million is None or output_price_per_million is None:
        return None
    return (
        (input_tokens / 1_000_000) * input_price_per_million
        + (output_tokens / 1_000_000) * output_price_per_million
    )


def show_cost_estimation(console, tasks_config, config):
    from rich.table import Table
    from .model_catalog import load_model_catalog

    table = Table(title="💰 任务成本预估 (仅供参考)", show_header=True, header_style="bold magenta")
    table.add_column("文档页任务", style="cyan")
    table.add_column("页数", justify="right")
    table.add_column("图片Token均值/范围", justify="right")
    table.add_column("输入Token(M)", justify="right")
    table.add_column("输出Token(M)", justify="right")
    table.add_column("预估费用 (元)", justify="right", style="green")

    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    catalog_records = load_model_catalog(prefer_cache=True, cache_path=config.model_cache_path, curated=True)
    vision_record = _find_model_record(
        catalog_records,
        provider=config.vision_provider,
        model_id=config.model_vision,
        input_price=config.vision_input_price_per_million,
        output_price=config.vision_output_price_per_million,
    )
    brain_record = _find_model_record(
        catalog_records,
        provider=config.brain_provider,
        model_id=config.model_brain,
        input_price=config.brain_input_price_per_million,
        output_price=config.brain_output_price_per_million,
    )

    with console.status("[bold green]正在计算成本预估...[/]"):
        for doc_name, task_config in tasks_config.items():
            images = task_config["images"]
            start = task_config["range_start"]
            end = task_config["range_end"]
            target_images = images[start:end]

            num_slides = len(target_images)
            image_tokens = [calculate_image_tokens(img) for img in target_images]
            avg_img_tokens = int(sum(image_tokens) / len(image_tokens)) if image_tokens else 2000
            min_img_tokens = min(image_tokens) if image_tokens else 2000
            max_img_tokens = max(image_tokens) if image_tokens else 2000

            s1_prompt_tokens = 300
            s1_output = 500
            s1_input_total = 0
            s1_output_total = 0
            s1_cost = 0.0
            for img_tokens in image_tokens:
                page_input = img_tokens + s1_prompt_tokens
                s1_input_total += page_input
                s1_output_total += s1_output
                page_cost = estimate_text_cost(page_input, s1_output, vision_record)
                if page_cost is None:
                    page_cost = estimate_price(config.model_vision, page_input, s1_output)
                s1_cost += page_cost

            # Brain 阶段输入来自 5 页 Raw Data 窗口。真实 token 要等 Stage 1 完成后才知道，
            # 这里使用当前 prompt 设计的保守经验值。
            s2_input = 3500
            s2_output = 800
            s2_unit_cost = estimate_text_cost(s2_input, s2_output, brain_record)
            if s2_unit_cost is None:
                s2_unit_cost = estimate_price(config.model_brain, s2_input, s2_output)
            s2_cost = s2_unit_cost * num_slides
            s2_input_total = s2_input * num_slides
            s2_output_total = s2_output * num_slides

            doc_cost = s1_cost + s2_cost
            doc_input_tokens = s1_input_total + s2_input_total
            doc_output_tokens = s1_output_total + s2_output_total

            total_cost += doc_cost
            total_input_tokens += doc_input_tokens
            total_output_tokens += doc_output_tokens

            table.add_row(
                doc_name,
                str(num_slides),
                f"{avg_img_tokens} / {min_img_tokens}-{max_img_tokens}",
                f"{doc_input_tokens / 1_000_000:.3f}",
                f"{doc_output_tokens / 1_000_000:.3f}",
                f"¥ {doc_cost:.2f}",
            )

    table.add_row(
        "总计",
        "",
        "",
        f"{total_input_tokens / 1_000_000:.3f}",
        f"{total_output_tokens / 1_000_000:.3f}",
        f"¥ {total_cost:.2f}",
        style="bold red",
    )
    console.print(table)
    console.print(
        "[dim]"
        f"注：预估基于当前选择 Vision={config.vision_provider}:{config.model_vision}, "
        f"Brain={config.brain_provider}:{config.model_brain} 的本地价格表或自定义价格。"
        "图片输入按每张图片尺寸逐页估算；输出 token、思考 token 和服务商活动折扣只能近似，实际计费以服务商账单为准。"
        "[/]\n"
    )


def _find_model_record(records, provider, model_id, input_price, output_price):
    for record in records:
        if record.provider == provider and record.model_id == model_id:
            return record

    if input_price is None and output_price is None:
        return None

    return ModelRecord(
        model_id=model_id,
        provider=provider,
        input_price=input_price,
        output_price=output_price,
        price_source="custom",
    )
