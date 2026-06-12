from .aliyun_catalog import ModelRecord


def calculate_image_tokens(image_path):
    """
    根据 Qwen3-VL 官方规则计算图像 Token:
    Token = (H_bar * W_bar) / (32 * 32) + 2
    """
    from PIL import Image

    try:
        with Image.open(image_path) as img:
            height = img.height
            width = img.width

            h_bar = round(height / 32) * 32
            w_bar = round(width / 32) * 32

            return int((h_bar * w_bar) / 1024) + 2
    except Exception:
        return 2000


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
    table.add_column("PPT 任务", style="cyan")
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
        for ppt_name, task_config in tasks_config.items():
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

            ppt_cost = s1_cost + s2_cost
            ppt_input_tokens = s1_input_total + s2_input_total
            ppt_output_tokens = s1_output_total + s2_output_total

            total_cost += ppt_cost
            total_input_tokens += ppt_input_tokens
            total_output_tokens += ppt_output_tokens

            table.add_row(
                ppt_name,
                str(num_slides),
                f"{avg_img_tokens} / {min_img_tokens}-{max_img_tokens}",
                f"{ppt_input_tokens / 1_000_000:.3f}",
                f"{ppt_output_tokens / 1_000_000:.3f}",
                f"¥ {ppt_cost:.2f}",
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
