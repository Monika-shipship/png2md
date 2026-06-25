from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .aliyun_catalog import (
    ModelRecord,
    fetch_model_ids_from_docs,
    load_cache,
    records_from_cache_dict,
    records_to_cache_dict,
    save_cache,
)
from .model_catalog import static_to_records
from .secrets import get_secret_value


DEFAULT_PROVIDERS = ("dashscope", "deepseek")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_PRICING_URL = "https://api-docs.deepseek.com/zh-cn/quick_start/pricing"


@dataclass(frozen=True)
class CatalogRefreshResult:
    records: list[ModelRecord]
    cache_data: dict[str, Any]
    diff: dict[str, Any]
    errors: list[dict[str, str]]
    cache_path: str

    def summary_text(self) -> str:
        changed_prices = len(self.diff.get("price_changed") or [])
        return (
            f"官方模型/价格刷新完成：模型 {len(self.records)} 个，"
            f"新增 {len(self.diff.get('added') or [])}，消失 {len(self.diff.get('removed') or [])}，"
            f"价格变化 {changed_prices}，错误 {len(self.errors)}。"
        )


def refresh_official_catalog(
    *,
    providers: list[str] | tuple[str, ...] = DEFAULT_PROVIDERS,
    cache_path: str = ".cache/aliyun_model_catalog.json",
    region: str = "cn-beijing",
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    import_pricing_md: str | None = None,
    openai_base_url: str | None = None,
    openai_api_key_env: str = "OPENAI_API_KEY",
) -> CatalogRefreshResult:
    old_cache = load_cache(cache_path) or {}
    old_records = records_from_cache_dict(old_cache) if old_cache else []
    records: list[ModelRecord] = []
    errors: list[dict[str, str]] = []
    normalized = [provider.strip().lower() for provider in providers if provider.strip()]

    if "dashscope" in normalized:
        try:
            records.extend(fetch_model_ids_from_docs())
        except Exception as exc:
            errors.append({"provider": "dashscope", "stage": "fetch", "error": str(exc)[:500]})

    if "deepseek" in normalized:
        try:
            records.extend(fetch_deepseek_official_records())
        except Exception as exc:
            errors.append({"provider": "deepseek", "stage": "fetch", "error": str(exc)[:500]})

    if "openai-compatible" in normalized or "openai_compatible" in normalized:
        try:
            discovered = fetch_openai_compatible_models(openai_base_url or base_url, api_key_env=openai_api_key_env)
            records.extend(discovered)
        except Exception as exc:
            errors.append({"provider": "openai_compatible", "stage": "fetch", "error": str(exc)[:500]})

    if import_pricing_md:
        try:
            pricing_text = _read_text_or_literal(import_pricing_md)
            records = merge_markdown_pricing(records, pricing_text, source=import_pricing_md)
        except Exception as exc:
            errors.append({"provider": "pricing_md", "stage": "parse", "error": str(exc)[:500]})

    records = _merge_with_static_fallback(records)
    diff = diff_model_records(old_records, records)
    cache_data = records_to_cache_dict(records, source_urls=_source_urls_for(normalized), region=region, base_url=base_url)
    cache_data["schema_version"] = 2
    cache_data["providers"] = normalized
    cache_data["refresh"] = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "errors": errors,
        "diff": diff,
        "price_refresh": True,
        "provider_aware": True,
    }
    save_cache(cache_path, cache_data)
    return CatalogRefreshResult(records=records, cache_data=cache_data, diff=diff, errors=errors, cache_path=cache_path)


def fetch_deepseek_official_records(*, api_key_env: str = "DEEPSEEK_API_KEY", base_url: str = DEEPSEEK_BASE_URL) -> list[ModelRecord]:
    pricing = fetch_deepseek_pricing()
    model_ids = fetch_openai_compatible_model_ids(base_url, api_key_env=api_key_env)
    if not model_ids:
        model_ids = sorted(pricing) or ["deepseek-v4-flash", "deepseek-v4-pro"]
    records: list[ModelRecord] = []
    for model_id in model_ids:
        price = pricing.get(model_id, {})
        records.append(
            ModelRecord(
                model_id=model_id,
                provider="deepseek",
                family="text",
                stage_suitable=["brain"],
                supports_vision=False,
                supports_openai_chat=True,
                supports_dashscope_native=False,
                context_window=price.get("context_tokens") or 1_000_000 if model_id.startswith("deepseek-v4") else None,
                max_output_tokens=price.get("max_output_tokens") or 384_000 if model_id.startswith("deepseek-v4") else None,
                input_price=price.get("input_price"),
                output_price=price.get("output_price"),
                cached_input_price=price.get("cached_input_price"),
                price_unit=price.get("price_unit") or "CNY_per_1M_tokens",
                price_source=price.get("price_source") or "DeepSeek /models",
                price_region="global",
                region="global",
                source_urls=[DEEPSEEK_PRICING_URL, f"{base_url.rstrip('/')}/models"],
                openai_text_status="unknown",
                openai_vision_status="skipped",
                dashscope_multimodal_status="skipped",
                note=price.get("note") or "",
            )
        )
    return records


def fetch_deepseek_pricing(url: str = DEEPSEEK_PRICING_URL) -> dict[str, dict[str, Any]]:
    html = _fetch_text(url, timeout=10)
    parsed = parse_deepseek_pricing_text(html, source=url)
    if parsed:
        return parsed
    local = Path("docs/deepseek-api/模型 & 价格 _ DeepSeek API Docs.md")
    if local.exists():
        return parse_deepseek_pricing_text(local.read_text(encoding="utf-8"), source=str(local))
    return {}


def parse_deepseek_pricing_text(text: str, *, source: str = "DeepSeek official pricing") -> dict[str, dict[str, Any]]:
    compact = re.sub(r"\s+", " ", text or "")
    models = re.findall(r"(deepseek-[a-z0-9.\-_]+)", compact, flags=re.IGNORECASE)
    ordered_models: list[str] = []
    for model in models:
        model = model.lower().strip()
        if model not in ordered_models and ("flash" in model or "pro" in model or "chat" in model or "reasoner" in model):
            ordered_models.append(model)
    # Current Chinese docs often present two columns: flash/pro with cache-hit, cache-miss, output rows.
    hit = re.search(r"缓存命中[^0-9$¥]*(?:[$¥￥])?\s*(\d+(?:\.\d+)?)\s*(?:元|美元|USD|\$)?[^0-9]*(?:[$¥￥])?\s*(\d+(?:\.\d+)?)", compact, re.IGNORECASE)
    miss = re.search(r"缓存未命中[^0-9$¥]*(?:[$¥￥])?\s*(\d+(?:\.\d+)?)\s*(?:元|美元|USD|\$)?[^0-9]*(?:[$¥￥])?\s*(\d+(?:\.\d+)?)", compact, re.IGNORECASE)
    out = re.search(r"(?:tokens输出|输出)[^0-9$¥]*(?:[$¥￥])?\s*(\d+(?:\.\d+)?)\s*(?:元|美元|USD|\$)?[^0-9]*(?:[$¥￥])?\s*(\d+(?:\.\d+)?)", compact, re.IGNORECASE)
    concurrency = re.search(r"并发限制[^0-9]*(\d+)\s*(\d+)", compact)
    currency = "USD" if "$" in compact or "美元" in compact or "USD" in compact.upper() else "CNY"
    unit = f"{currency}_per_1M_tokens"
    if not (miss and out):
        return {}
    if not ordered_models:
        ordered_models = ["deepseek-v4-flash", "deepseek-v4-pro"]
    first = ordered_models[0]
    second = ordered_models[1] if len(ordered_models) > 1 else None
    result: dict[str, dict[str, Any]] = {
        first: {
            "input_price": float(miss.group(1)),
            "output_price": float(out.group(1)),
            "cached_input_price": float(hit.group(1)) if hit else None,
            "price_unit": unit,
            "price_source": source,
            "context_tokens": 1_000_000,
            "max_output_tokens": 384_000,
            "rpm": int(concurrency.group(1)) if concurrency else None,
        }
    }
    if second:
        result[second] = {
            "input_price": float(miss.group(2)),
            "output_price": float(out.group(2)),
            "cached_input_price": float(hit.group(2)) if hit else None,
            "price_unit": unit,
            "price_source": source,
            "context_tokens": 1_000_000,
            "max_output_tokens": 384_000,
            "rpm": int(concurrency.group(2)) if concurrency else None,
        }
    return result


def fetch_openai_compatible_models(base_url: str, *, api_key_env: str = "OPENAI_API_KEY") -> list[ModelRecord]:
    return [
        ModelRecord(
            model_id=model_id,
            provider="openai_compatible",
            family="text",
            stage_suitable=["brain"],
            supports_vision=None,
            supports_openai_chat=True,
            supports_dashscope_native=False,
            price_source="user_required",
            source_urls=[f"{base_url.rstrip('/')}/models"],
            note="通过 /models 自动发现；价格必须由用户手动填写。",
        )
        for model_id in fetch_openai_compatible_model_ids(base_url, api_key_env=api_key_env)
    ]


def fetch_openai_compatible_model_ids(base_url: str, *, api_key_env: str = "OPENAI_API_KEY") -> list[str]:
    api_key = get_secret_value(api_key_env)
    if not api_key:
        return []
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/models",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, json.JSONDecodeError):
        return []
    items = data.get("data") if isinstance(data, dict) else None
    if not isinstance(items, list):
        return []
    model_ids = []
    for item in items:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            model_ids.append(item["id"])
    return sorted(set(model_ids))


def merge_markdown_pricing(records: list[ModelRecord], text: str, *, source: str = "imported markdown") -> list[ModelRecord]:
    by_id = {record.model_id: record for record in records}
    prices = parse_simple_markdown_prices(text)
    for model_id, price in prices.items():
        record = by_id.get(model_id)
        if record is None:
            record = ModelRecord(model_id=model_id, provider=_infer_provider_from_model_id(model_id), family="text")
            by_id[model_id] = record
        record.input_price = price.get("input")
        record.output_price = price.get("output")
        record.cached_input_price = price.get("cached_input")
        record.price_unit = price.get("unit") or "CNY_per_1M_tokens"
        record.price_source = source
    return list(by_id.values())


def parse_simple_markdown_prices(text: str) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line in (text or "").splitlines():
        if "|" not in line:
            continue
        cells = [cell.strip(" `") for cell in line.strip().strip("|").split("|")]
        joined = " ".join(cells)
        model_match = re.search(r"((?:qwen|deepseek|kimi)[\w.\-]+)", joined, flags=re.IGNORECASE)
        if not model_match:
            continue
        numbers = [float(item) for item in re.findall(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w.])", joined)]
        if len(numbers) < 2:
            continue
        currency = "USD" if "$" in joined or "美元" in joined or "USD" in joined.upper() else "CNY"
        rows[model_match.group(1).lower()] = {
            "input": numbers[0],
            "output": numbers[1],
            "cached_input": numbers[2] if len(numbers) > 2 else None,
            "unit": f"{currency}_per_1M_tokens",
        }
    return rows


def diff_model_records(old_records: list[ModelRecord], new_records: list[ModelRecord]) -> dict[str, Any]:
    old = {_record_key(record): record for record in old_records}
    new = {_record_key(record): record for record in new_records}
    added = sorted(key for key in new if key not in old)
    removed = sorted(key for key in old if key not in new)
    price_changed = []
    for key in sorted(set(old) & set(new)):
        before = old[key]
        after = new[key]
        before_price = (before.input_price, before.output_price, before.cached_input_price, before.price_unit)
        after_price = (after.input_price, after.output_price, after.cached_input_price, after.price_unit)
        if before_price != after_price:
            price_changed.append({"model": key, "before": before_price, "after": after_price})
    return {"added": added, "removed": removed, "price_changed": price_changed}


def _merge_with_static_fallback(dynamic_records: list[ModelRecord]) -> list[ModelRecord]:
    by_key = {_record_key(record): record for record in dynamic_records}
    for record in static_to_records():
        by_key.setdefault(_record_key(record), record)
    return sorted(by_key.values(), key=lambda record: (_provider_rank(record.provider), record.family, record.model_id))


def _record_key(record: ModelRecord) -> str:
    return f"{record.provider}:{record.model_id}"


def _provider_rank(provider: str) -> int:
    return {"dashscope": 0, "dashscope_openai": 1, "deepseek": 2, "openai_compatible": 3}.get(provider, 9)


def _fetch_text(url: str, *, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "DocPage2MD-OfficialCatalog/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _read_text_or_literal(value: str) -> str:
    path = Path(value)
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8")
    return value


def _source_urls_for(providers: list[str]) -> list[str]:
    urls = []
    if "dashscope" in providers:
        urls.extend(["https://help.aliyun.com/zh/model-studio/models", "https://help.aliyun.com/zh/model-studio/model-pricing"])
    if "deepseek" in providers:
        urls.extend([DEEPSEEK_PRICING_URL, f"{DEEPSEEK_BASE_URL}/models"])
    return urls


def _infer_provider_from_model_id(model_id: str) -> str:
    lowered = model_id.lower()
    if lowered.startswith("deepseek"):
        return "deepseek"
    if lowered.startswith("kimi"):
        return "dashscope_openai"
    return "dashscope"
