from dataclasses import dataclass
import re
from typing import Dict, Iterable, List, Optional, Tuple
import urllib.request


ROLE_VISION = "vision"
ROLE_BRAIN = "brain"


@dataclass(frozen=True)
class ModelPrice:
    input_per_million: Optional[float] = None
    output_per_million: Optional[float] = None
    cached_input_per_million: Optional[float] = None
    currency: str = "CNY"
    source: str = "local"
    note: str = ""


@dataclass(frozen=True)
class ModelSpec:
    provider: str
    model_id: str
    display_name: str
    roles: Tuple[str, ...]
    supports_vision: bool
    supports_thinking: bool
    price: ModelPrice
    context_tokens: Optional[int] = None
    max_output_tokens: Optional[int] = None
    rpm: Optional[int] = None
    tpm: Optional[int] = None
    note: str = ""

    @property
    def key(self):
        return make_model_key(self.provider, self.model_id)


def make_model_key(provider, model_id):
    return f"{provider}:{model_id}"


def get_default_catalog():
    specs = [
        ModelSpec(
            provider="dashscope",
            model_id="qwen3-vl-plus",
            display_name="Qwen3-VL-Plus",
            roles=(ROLE_VISION,),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(1.0, 10.0, 0.2, source="百炼控制台粘贴文本"),
            context_tokens=256_000,
            max_output_tokens=32_000,
            rpm=3000,
            tpm=5_000_000,
            note="当前默认视觉模型，适合 OCR/图形分析。",
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3-vl-flash-2026-01-22",
            display_name="Qwen3-VL-Flash",
            roles=(ROLE_VISION,),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(0.15, 1.5, 0.03, source="百炼控制台粘贴文本"),
            context_tokens=256_000,
            max_output_tokens=32_000,
            rpm=3000,
            tpm=5_000_000,
            note="便宜快速；控制台文本提示将于 2026-09-08 下线。",
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.7-plus",
            display_name="Qwen3.7-Plus",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(2.0, 8.0, 0.4, source="百炼控制台粘贴文本", note="控制台显示有限时折扣，估算按原价保守计算。"),
            context_tokens=1_000_000,
            max_output_tokens=64_000,
            rpm=30_000,
            tpm=5_000_000,
            note="多模态智能体基座，精度和价格折中。",
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.7-plus-2026-05-26",
            display_name="Qwen3.7-Plus 2026-05-26",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(2.0, 8.0, 0.4, source="参考价格文档/视觉OCR模型价格整理_2026-06-12.md", note="按 qwen3.7-plus 原价阶梯估算，未扣除限时折扣。"),
            context_tokens=1_000_000,
            max_output_tokens=64_000,
            rpm=30_000,
            tpm=5_000_000,
            note="Qwen3.7-Plus 最新快照，模型卡标注支持视觉理解。",
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.7-max-2026-06-08",
            display_name="Qwen3.7-Max 2026-06-08",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(12.0, 36.0, 2.4, source="百炼控制台粘贴文本"),
            context_tokens=1_000_000,
            max_output_tokens=64_000,
            rpm=600,
            tpm=1_000_000,
            note="最高档多模态快照；成本明显更高。",
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.7-max",
            display_name="Qwen3.7-Max",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(12.0, 36.0, 2.4, source="百炼控制台粘贴文本", note="控制台显示有限时折扣，估算按原价保守计算。"),
            context_tokens=1_000_000,
            max_output_tokens=64_000,
            rpm=30_000,
            tpm=5_000_000,
            note="模型卡标注视觉理解；如果账号实际只开放文本，请改用 qwen3.7-max-2026-06-08 或 qwen3.7-plus。",
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.6-plus",
            display_name="Qwen3.6-Plus",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(2.0, 12.0, source="百炼控制台粘贴文本"),
            context_tokens=1_000_000,
            max_output_tokens=64_000,
            rpm=30_000,
            tpm=5_000_000,
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.6-plus-2026-04-02",
            display_name="Qwen3.6-Plus 2026-04-02",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(2.0, 12.0, source="参考价格文档/视觉OCR模型价格整理_2026-06-12.md"),
            context_tokens=1_000_000,
            max_output_tokens=64_000,
            rpm=30_000,
            tpm=5_000_000,
            note="Qwen3.6-Plus 快照，模型卡标注支持视觉理解。",
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.6-flash",
            display_name="Qwen3.6-Flash",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(1.2, 7.2, source="百炼控制台粘贴文本"),
            context_tokens=1_000_000,
            max_output_tokens=64_000,
            rpm=30_000,
            tpm=10_000_000,
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.6-27b",
            display_name="Qwen3.6-27B",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(3.0, 18.0, source="参考价格文档/视觉OCR模型价格整理_2026-06-12.md"),
            context_tokens=256_000,
            max_output_tokens=64_000,
            note="Qwen3.6 开源视觉语言模型；价格不如 35B-A3B 划算，但可作为可选视觉模型。",
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.5-plus",
            display_name="Qwen3.5-Plus",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(0.8, 4.8, source="百炼控制台粘贴文本"),
            context_tokens=1_000_000,
            max_output_tokens=64_000,
            rpm=30_000,
            tpm=5_000_000,
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.5-plus-2026-04-20",
            display_name="Qwen3.5-Plus 2026-04-20",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(0.8, 4.8, source="参考价格文档/视觉OCR模型价格整理_2026-06-12.md"),
            context_tokens=1_000_000,
            max_output_tokens=64_000,
            rpm=30_000,
            tpm=5_000_000,
            note="Qwen3.5-Plus 快照，模型卡标注支持视觉理解。",
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.5-flash",
            display_name="Qwen3.5-Flash",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(0.2, 2.0, source="百炼控制台粘贴文本"),
            context_tokens=1_000_000,
            max_output_tokens=64_000,
            rpm=30_000,
            tpm=10_000_000,
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen3.5-27b",
            display_name="Qwen3.5-27B",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(0.6, 4.8, source="参考价格文档/视觉OCR模型价格整理_2026-06-12.md"),
            context_tokens=256_000,
            max_output_tokens=64_000,
            note="Qwen3.5 开源视觉语言模型，可作为中低价视觉候选。",
        ),
        ModelSpec(
            provider="dashscope_openai",
            model_id="kimi-k2.6",
            display_name="Kimi-K2.6",
            roles=(ROLE_VISION, ROLE_BRAIN),
            supports_vision=True,
            supports_thinking=True,
            price=ModelPrice(6.5, 27.0, 1.3, source="用户提供的百炼模型卡价格"),
            context_tokens=256_000,
            max_output_tokens=None,
            rpm=500,
            note="Kimi 最新多模态模型，支持文本、图片与视频输入；通过 DashScope OpenAI 兼容路径调用。",
        ),
        ModelSpec(
            provider="dashscope",
            model_id="qwen-plus",
            display_name="Qwen-Plus",
            roles=(ROLE_BRAIN,),
            supports_vision=False,
            supports_thinking=True,
            price=ModelPrice(0.8, 8.0, source="参考价格文档/价格.md"),
            note="原默认 Brain 模型；本程序开启思考模式，按思考输出价估算。",
        ),
        ModelSpec(
            provider="deepseek",
            model_id="deepseek-v4-flash",
            display_name="DeepSeek V4 Flash",
            roles=(ROLE_BRAIN,),
            supports_vision=False,
            supports_thinking=True,
            price=ModelPrice(1.0, 2.0, 0.02, source="DeepSeek 官方价格页"),
            context_tokens=1_000_000,
            max_output_tokens=384_000,
            rpm=2500,
            note="便宜、并发高；推荐作为 Brain。",
        ),
        ModelSpec(
            provider="deepseek",
            model_id="deepseek-v4-pro",
            display_name="DeepSeek V4 Pro",
            roles=(ROLE_BRAIN,),
            supports_vision=False,
            supports_thinking=True,
            price=ModelPrice(3.0, 6.0, 0.025, source="DeepSeek 官方价格页"),
            context_tokens=1_000_000,
            max_output_tokens=384_000,
            rpm=500,
            note="更强但更贵，适合高质量重组。",
        ),
    ]
    return {spec.key: spec for spec in specs}


def refresh_catalog_best_effort(catalog):
    refreshed = dict(catalog)
    try:
        refreshed.update(_fetch_deepseek_pricing())
    except Exception:
        pass
    return refreshed


def _fetch_deepseek_pricing():
    url = "https://api-docs.deepseek.com/zh-cn/quick_start/pricing"
    with urllib.request.urlopen(url, timeout=5) as response:
        html = response.read().decode("utf-8", errors="replace")

    hit_prices = re.search(r"缓存命中[^0-9]*(0\.\d+)\s*元\s*(0\.\d+)\s*元", html)
    miss_prices = re.search(r"缓存未命中[^0-9]*(\d+(?:\.\d+)?)\s*元\s*(\d+(?:\.\d+)?)\s*元", html)
    output_prices = re.search(r"tokens输出[^0-9]*(\d+(?:\.\d+)?)\s*元\s*(\d+(?:\.\d+)?)\s*元", html)
    concurrency = re.search(r"并发限制(?:\(\d+\))?[^0-9]*(\d+)\s*(\d+)", html)

    if not (hit_prices and miss_prices and output_prices):
        return {}

    flash = _deepseek_spec(
        model_id="deepseek-v4-flash",
        display_name="DeepSeek V4 Flash",
        input_price=float(miss_prices.group(1)),
        output_price=float(output_prices.group(1)),
        cached_price=float(hit_prices.group(1)),
        rpm=int(concurrency.group(1)) if concurrency else 2500,
    )
    pro = _deepseek_spec(
        model_id="deepseek-v4-pro",
        display_name="DeepSeek V4 Pro",
        input_price=float(miss_prices.group(2)),
        output_price=float(output_prices.group(2)),
        cached_price=float(hit_prices.group(2)),
        rpm=int(concurrency.group(2)) if concurrency else 500,
    )
    return {flash.key: flash, pro.key: pro}


def _deepseek_spec(model_id, display_name, input_price, output_price, cached_price, rpm):
    return ModelSpec(
        provider="deepseek",
        model_id=model_id,
        display_name=display_name,
        roles=(ROLE_BRAIN,),
        supports_vision=False,
        supports_thinking=True,
        price=ModelPrice(
            input_per_million=input_price,
            output_per_million=output_price,
            cached_input_per_million=cached_price,
            source="DeepSeek 官方价格页（启动时刷新）",
        ),
        context_tokens=1_000_000,
        max_output_tokens=384_000,
        rpm=rpm,
    )


def models_for_role(catalog: Dict[str, ModelSpec], role: str) -> Iterable[ModelSpec]:
    return [spec for spec in catalog.values() if role in spec.roles]


def get_model(catalog: Dict[str, ModelSpec], provider: str, model_id: str) -> Optional[ModelSpec]:
    return catalog.get(make_model_key(provider, model_id))


def price_label(spec: ModelSpec):
    price = spec.price
    if price.input_per_million is None or price.output_per_million is None:
        return "价格未知"
    return f"¥{price.input_per_million:g}/M in, ¥{price.output_per_million:g}/M out"


# ==========================================================================
# 静态 → ModelRecord 转换 & 动态/静态合并
# ==========================================================================

def static_to_records() -> "List":
    """将现有静态 ModelSpec 目录转换为 aliyun_catalog.ModelRecord 列表。

    延迟导入以避免循环依赖（aliyun_catalog 可能反过来引用 model_catalog）。
    """
    from .aliyun_catalog import ModelRecord, infer_family

    records = []
    for spec in get_default_catalog().values():
        family = infer_family(spec.model_id)
        records.append(ModelRecord(
            model_id=spec.model_id,
            provider=spec.provider,
            family=family,
            stage_suitable=list(spec.roles),
            supports_vision=spec.supports_vision,
            supports_openai_chat=(spec.provider in ("dashscope", "dashscope_openai", "deepseek")),
            supports_dashscope_native=(spec.provider == "dashscope"),
            context_window=spec.context_tokens,
            max_output_tokens=spec.max_output_tokens,
            input_price=spec.price.input_per_million,
            output_price=spec.price.output_per_million,
            cached_input_price=spec.price.cached_input_per_million,
            price_unit="CNY_per_1M_tokens",
            price_source=spec.price.source or "static",
            price_tiers=_static_price_tiers(spec.model_id),
            note=spec.note or "",
        ))
    return records


def _static_price_tiers(model_id):
    tiers_by_model = {
        "qwen3-vl-plus": [
            {"max_tokens": 32_000, "input": 1.0, "output": 10.0},
            {"max_tokens": 128_000, "input": 1.5, "output": 15.0},
            {"max_tokens": 256_000, "input": 3.0, "output": 30.0},
        ],
        "qwen3-vl-flash-2026-01-22": [
            {"max_tokens": 32_000, "input": 0.15, "output": 1.5},
            {"max_tokens": 128_000, "input": 0.3, "output": 3.0},
            {"max_tokens": 256_000, "input": 0.6, "output": 6.0},
        ],
        "qwen3.5-flash": [
            {"max_tokens": 128_000, "input": 0.2, "output": 2.0},
            {"max_tokens": 256_000, "input": 0.8, "output": 8.0},
            {"max_tokens": 1_000_000, "input": 1.2, "output": 12.0},
        ],
        "qwen3.5-plus": [
            {"max_tokens": 128_000, "input": 0.8, "output": 4.8},
            {"max_tokens": 256_000, "input": 2.0, "output": 12.0},
            {"max_tokens": 1_000_000, "input": 4.0, "output": 24.0},
        ],
        "qwen3.5-plus-2026-04-20": [
            {"max_tokens": 128_000, "input": 0.8, "output": 4.8},
            {"max_tokens": 256_000, "input": 2.0, "output": 12.0},
            {"max_tokens": 1_000_000, "input": 4.0, "output": 24.0},
        ],
        "qwen3.5-27b": [
            {"max_tokens": 128_000, "input": 0.6, "output": 4.8},
            {"max_tokens": 256_000, "input": 1.8, "output": 14.4},
        ],
        "qwen3.6-flash": [
            {"max_tokens": 256_000, "input": 1.2, "output": 7.2},
            {"max_tokens": 1_000_000, "input": 4.8, "output": 28.8},
        ],
        "qwen3.6-plus": [
            {"max_tokens": 256_000, "input": 2.0, "output": 12.0},
            {"max_tokens": 1_000_000, "input": 8.0, "output": 48.0},
        ],
        "qwen3.6-plus-2026-04-02": [
            {"max_tokens": 256_000, "input": 2.0, "output": 12.0},
            {"max_tokens": 1_000_000, "input": 8.0, "output": 48.0},
        ],
        "qwen3.6-27b": [
            {"max_tokens": 256_000, "input": 3.0, "output": 18.0},
        ],
        "qwen3.7-plus": [
            {"max_tokens": 256_000, "input": 2.0, "output": 8.0},
            {"max_tokens": 1_000_000, "input": 6.0, "output": 24.0},
        ],
        "qwen3.7-plus-2026-05-26": [
            {"max_tokens": 256_000, "input": 2.0, "output": 8.0},
            {"max_tokens": 1_000_000, "input": 6.0, "output": 24.0},
        ],
        "qwen3.7-max": [
            {"max_tokens": 1_000_000, "input": 12.0, "output": 36.0},
        ],
        "qwen3.7-max-2026-06-08": [
            {"max_tokens": 1_000_000, "input": 12.0, "output": 36.0},
        ],
        "kimi-k2.6": [
            {"max_tokens": 256_000, "input": 6.5, "output": 27.0},
        ],
        "qwen-plus": [
            {"max_tokens": 128_000, "input": 0.8, "output": 8.0},
            {"max_tokens": 256_000, "input": 2.4, "output": 24.0},
            {"max_tokens": 1_000_000, "input": 4.8, "output": 64.0},
        ],
    }
    return tiers_by_model.get(model_id, [])


def merge_static_and_dynamic(
    dynamic_records: "List",
    curated: bool = True,
) -> "List":
    """合并动态目录与静态 fallback。

    规则：
    默认 curated=True：
    1. 静态精选主力模型优先，保证价格和排序稳定。
    2. 动态缓存只用于补充能力验证状态，或加入已验证通过的新模型。
    3. 未验证/无价的 400+ 文档候选不进入交互 UI。

    curated=False：
    返回完整动态目录 + 静态补充，供诊断命令使用。
    """
    static = static_to_records()
    static_by_id: dict = {r.model_id: r for r in static}
    dynamic_by_id: dict = {r.model_id: r for r in dynamic_records}

    if curated:
        merged = []
        for static_rec in static:
            dyn = dynamic_by_id.get(static_rec.model_id)
            if dyn:
                merged.append(_merge_record(static_rec, dyn, prefer_static_price=True))
            else:
                merged.append(static_rec)

        seen = {r.model_id for r in merged}
        verified_extras = [
            rec for rec in dynamic_records
            if rec.model_id not in seen and _is_useful_verified_extra(rec)
        ]
        verified_extras.sort(key=_record_sort_key)
        merged.extend(verified_extras[:20])
        return sorted(merged, key=_record_sort_key)

    merged: dict = {}
    for rec in dynamic_records:
        static_rec = static_by_id.get(rec.model_id)
        merged[rec.model_id] = _merge_record(static_rec, rec, prefer_static_price=True) if static_rec else rec

    for sid, srec in static_by_id.items():
        if sid not in merged:
            merged[sid] = srec

    return sorted(merged.values(), key=_record_sort_key)


def _merge_record(static_rec, dynamic_rec, prefer_static_price=True):
    """把动态验证状态并入静态记录，价格默认以人工维护静态表为准。"""
    if static_rec is None:
        return dynamic_rec

    merged = static_rec
    merged.openai_text_status = dynamic_rec.openai_text_status
    merged.openai_text_error = dynamic_rec.openai_text_error
    merged.openai_vision_status = dynamic_rec.openai_vision_status
    merged.openai_vision_error = dynamic_rec.openai_vision_error
    merged.dashscope_multimodal_status = dynamic_rec.dashscope_multimodal_status
    merged.dashscope_multimodal_error = dynamic_rec.dashscope_multimodal_error
    merged.verified_at = dynamic_rec.verified_at
    merged.source_urls = dynamic_rec.source_urls or merged.source_urls
    merged.region = dynamic_rec.region or merged.region

    if not prefer_static_price or merged.input_price is None:
        if dynamic_rec.input_price is not None:
            merged.input_price = dynamic_rec.input_price
            merged.output_price = dynamic_rec.output_price
            merged.cached_input_price = dynamic_rec.cached_input_price
            merged.price_tiers = dynamic_rec.price_tiers
            merged.price_source = dynamic_rec.price_source or merged.price_source
            merged.price_region = dynamic_rec.price_region

    return merged


def _is_useful_verified_extra(record):
    if record.family in ("embedding", "rerank", "audio", "image_gen", "video_gen"):
        return False
    if record.provider != "dashscope":
        return False
    if record.input_price is None and record.output_price is None:
        return False
    if "ok" in (
        record.openai_text_status,
        record.openai_vision_status,
        record.dashscope_multimodal_status,
    ):
        return True
    return False


def _record_sort_key(record):
    family_rank = {
        "multimodal": 0,
        "text": 1,
        "coder": 2,
        "math": 3,
    }.get(record.family, 9)
    provider_rank = {"dashscope": 0, "deepseek": 1}.get(record.provider, 5)
    return (provider_rank, family_rank, record.model_id)


def load_model_catalog(
    prefer_cache: bool = True,
    cache_path: str = ".cache/aliyun_model_catalog.json",
    curated: bool = True,
) -> "List":
    """加载模型目录的统一入口。

    优先级：缓存 + 静态价格合并 > 纯静态

    始终将静态表的价格信息合并到缓存记录中（缓存中的动态模型通常无价格）。

    Args:
        prefer_cache: True 时优先读缓存文件。
        cache_path: 缓存 JSON 文件路径。
        curated: True 时返回精选可选目录；False 返回完整缓存目录。

    Returns:
        list[ModelRecord]
    """
    from .aliyun_catalog import load_cache, records_from_cache_dict

    if prefer_cache:
        data = load_cache(cache_path)
        if data:
            dynamic = records_from_cache_dict(data)
            return merge_static_and_dynamic(dynamic, curated=curated)

    # 缓存未命中 → 纯静态 fallback
    return sorted(static_to_records(), key=_record_sort_key)
