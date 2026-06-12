"""
阿里云百炼模型目录自动刷新 + 可用性验证 + 本地缓存。

功能：
- 从阿里云官方文档页面抓取候选模型 ID + 价格（仅公开页面，不爬控制台）
- 用正则提取 qwen/deepseek/kimi/glm/minimax 系列模型 ID
- 自动推断模型 family 与视觉能力（保守规则，max ≠ vision）
- 三条验证路径：OpenAI text / OpenAI vision / DashScope 原生 multimodal
- 能力矩阵替代单一 verified_status
- 定价解析（从 model-pricing 页面表格）
- 本地 JSON 缓存，启动时不联网
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 候选文档页面（公开可访问，无需登录）
# ---------------------------------------------------------------------------
ALIYUN_DOC_URLS = [
    "https://help.aliyun.com/zh/model-studio/models",
    "https://help.aliyun.com/zh/model-studio/model-pricing",
    "https://help.aliyun.com/zh/model-studio/newly-released-models",
    "https://help.aliyun.com/zh/model-studio/qwen-api-reference/",
    "https://help.aliyun.com/zh/model-studio/qwen-api-via-openai-chat-completions",
    "https://help.aliyun.com/zh/model-studio/qwen-vl-compatible-with-openai",
    "https://help.aliyun.com/zh/model-studio/qwen-api-via-dashscope",
]

# 价格页单独列表
_PRICING_URL = "https://help.aliyun.com/zh/model-studio/model-pricing"

# 模型 ID 匹配正则（按优先级）
_MODEL_ID_PATTERNS = [
    re.compile(r"qwen[\w.\-]+", re.IGNORECASE),
    re.compile(r"deepseek[\w.\-]+", re.IGNORECASE),
    re.compile(r"kimi[\w.\-]+", re.IGNORECASE),
    re.compile(r"glm[\w.\-]+", re.IGNORECASE),
    re.compile(r"minimax[\w.\-]+", re.IGNORECASE),
]

# 已知非模型的误匹配（会被过滤）
_IGNORE_PATTERNS = [
    re.compile(r"qwen[-_]?api", re.IGNORECASE),
    re.compile(r"qwen[-_]?sdk", re.IGNORECASE),
    re.compile(r"qwen[-_]?agent", re.IGNORECASE),
]

# 不参与 Chat 验证的 family
_SKIP_VERIFY_FAMILIES = {"embedding", "rerank", "audio", "image_gen", "video_gen"}


# ==========================================================================
# 探针图片生成（32×32 PNG，满足阿里云 >10px 要求）
# ==========================================================================
def make_probe_png_base64(size: int = 32) -> str:
    """生成 size×size 纯白 PNG 的 base64 data URL。"""
    from PIL import Image

    img = Image.new("RGB", (size, size), (255, 255, 255))
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _probe_data_url() -> str:
    """惰性生成探针图片（仅首次调用时创建）。"""
    if not hasattr(_probe_data_url, "_cached"):
        _probe_data_url._cached = make_probe_png_base64(32)  # type: ignore[attr-defined]
    return _probe_data_url._cached  # type: ignore[attr-defined]


# ==========================================================================
# Family / 视觉能力推断（保守规则）
# ==========================================================================

# 明确支持视觉的模型前缀
_VISION_MODEL_PREFIXES = (
    "qwen3-vl", "qwen-vl", "qwen2.5-vl", "qwen2-vl",
    "qwen-omni", "qwen3-omni", "qwen2.5-omni",
    "qwen3.5-omni",
)

# 明确支持视觉的精确模型名
_VISION_EXACT_MODELS = {
    "qwen3.7-plus",      # 官方"图像与视频理解"分类
    "qwen3.7-max",       # 模型卡标注支持视觉理解
    "qwen3.6-plus",       # 支持视觉
    "qwen3.6-flash",      # 支持视觉
    "qwen3.6-27b",        # 开源视觉语言模型
    "qwen3.5-plus",       # 支持视觉
    "qwen3.5-flash",      # 支持视觉
    "qwen3.5-27b",        # 开源视觉语言模型
    "kimi-k2.6",          # Kimi 多模态模型，支持图片输入
}

# 明确纯文本的模型（即使名字含 "plus" 也不是 vision）
_TEXT_ONLY_EXACT_MODELS = {
    "qwen3-max",
    "qwen-max",
    "qwen-plus",
    "qwen-turbo",
}

def infer_family(model_id: str) -> str:
    """根据模型 ID 推断 family。"""
    lid = model_id.lower()

    # 明确的多模态 / 视觉模型（vl / omni 前缀）
    if any(lid.startswith(p) for p in _VISION_MODEL_PREFIXES):
        return "multimodal"

    # 明确视觉的精确模型
    if lid in _VISION_EXACT_MODELS or lid.rstrip("-0123456789.") in _VISION_EXACT_MODELS:
        return "multimodal"
    # 匹配带日期的变体 (如 qwen3.7-plus-2026-05-15)
    for exact in _VISION_EXACT_MODELS:
        if lid.startswith(exact + "-"):
            return "multimodal"

    if "coder" in lid:
        return "coder"
    if "math" in lid:
        return "math"
    if "embedding" in lid:
        return "embedding"
    if "rerank" in lid:
        return "rerank"
    if any(k in lid for k in ("audio", "asr", "tts", "speech", "voice")):
        return "audio"
    if any(k in lid for k in ("image", "wan", "flux", "stable")):
        return "image_gen"
    if "video" in lid:
        return "video_gen"

    return "text"


def _infer_supports_vision(model_id: str, family: str) -> Optional[bool]:
    """推断是否支持视觉输入（保守规则）。"""
    lid = model_id.lower()

    # family 已经是 multimodal
    if family == "multimodal":
        return True

    # vl / omni 前缀
    if any(lid.startswith(p) for p in _VISION_MODEL_PREFIXES):
        return True

    # 精确匹配的视觉模型
    if lid in _VISION_EXACT_MODELS or lid.rstrip("-0123456789.") in _VISION_EXACT_MODELS:
        return True
    for exact in _VISION_EXACT_MODELS:
        if lid.startswith(exact + "-"):
            return True

    # 明确纯文本
    if lid in _TEXT_ONLY_EXACT_MODELS or lid.rstrip("-0123456789.") in _TEXT_ONLY_EXACT_MODELS:
        return False
    for exact in _TEXT_ONLY_EXACT_MODELS:
        if lid.startswith(exact + "-"):
            return False

    # 特殊家族一律不支持
    if family in ("embedding", "rerank", "audio", "image_gen", "video_gen", "math", "coder"):
        return False

    # deepseek / glm / minimax 默认不支持视觉；Kimi 只把已知多模态型号列为视觉候选
    if any(lid.startswith(p) for p in ("deepseek", "glm", "minimax")):
        return False
    if lid.startswith("kimi"):
        return False

    return None  # 不确定


def _infer_provider(model_id: str) -> str:
    lid = model_id.lower()
    if lid.startswith("deepseek"):
        return "deepseek"
    if lid.startswith("kimi"):
        return "dashscope_openai"
    if lid.startswith("glm"):
        return "zhipu"
    if lid.startswith("minimax"):
        return "minimax"
    return "dashscope"


def _infer_context(model_id: str, family: str) -> Optional[int]:
    lid = model_id.lower()
    if "kimi-k2.6" in lid:
        return 256_000
    if any(k in lid for k in ("qwen3.7", "deepseek-v4")):
        return 1_000_000
    if any(k in lid for k in ("qwen3.6-27b", "qwen3.5-27b")):
        return 256_000
    if any(k in lid for k in ("qwen3.6", "qwen3.5")):
        return 1_000_000
    if "qwen3-vl" in lid or "qwen3-omni" in lid:
        return 256_000
    if "qwen-plus" in lid or "qwen-turbo" in lid:
        return 131_072
    if "qwen-max" in lid and "qwen3" not in lid:
        return 32_768
    return None


# ==========================================================================
# 数据结构：能力矩阵
# ==========================================================================
@dataclass
class ModelRecord:
    """统一的模型记录，能力矩阵替代单一 verified_status。"""
    model_id: str
    provider: str = "dashscope"
    family: str = "text"
    stage_suitable: List[str] = field(default_factory=list)
    supports_vision: Optional[bool] = None
    supports_openai_chat: Optional[bool] = None
    supports_dashscope_native: Optional[bool] = None
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    input_price: Optional[float] = None
    output_price: Optional[float] = None
    cached_input_price: Optional[float] = None
    price_unit: str = "CNY_per_1M_tokens"
    price_tiers: List[dict] = field(default_factory=list)
    price_source: str = ""
    price_region: str = ""
    region: str = "cn-beijing"
    source_urls: List[str] = field(default_factory=list)

    # ── 能力矩阵 ──
    openai_text_status: str = "unknown"       # ok / failed / skipped / unknown
    openai_text_error: Optional[str] = None
    openai_vision_status: str = "unknown"
    openai_vision_error: Optional[str] = None
    dashscope_multimodal_status: str = "unknown"
    dashscope_multimodal_error: Optional[str] = None
    verified_at: Optional[str] = None

    # 兼容字段
    @property
    def verified_status(self) -> str:
        """兼容旧代码：任一验证通过即视为 ok。"""
        if "ok" in (self.openai_text_status, self.openai_vision_status, self.dashscope_multimodal_status):
            return "ok"
        if "failed" in (self.openai_text_status, self.openai_vision_status, self.dashscope_multimodal_status):
            return "failed"
        return "unknown"

    error: Optional[str] = None  # compat
    note: str = ""


# ==========================================================================
# 文档抓取
# ==========================================================================
def fetch_model_ids_from_docs(
    urls: Optional[List[str]] = None,
    timeout: int = 10,
) -> List[ModelRecord]:
    """从阿里云文档页面抓取候选模型 ID，返回去重后的 ModelRecord 列表。"""
    if urls is None:
        urls = ALIYUN_DOC_URLS

    seen: Dict[str, ModelRecord] = {}

    for url in urls:
        try:
            html = _fetch_page(url, timeout=timeout)
            if not html:
                continue
            for model_id in _extract_model_ids(html):
                if model_id in seen:
                    seen[model_id].source_urls.append(url)
                    continue
                if _is_ignored(model_id):
                    continue
                family = infer_family(model_id)
                record = ModelRecord(
                    model_id=model_id,
                    provider=_infer_provider(model_id),
                    family=family,
                    supports_vision=_infer_supports_vision(model_id, family),
                    supports_openai_chat=(family not in _SKIP_VERIFY_FAMILIES),
                    supports_dashscope_native=(_infer_provider(model_id) == "dashscope"),
                    context_window=_infer_context(model_id, family),
                    source_urls=[url],
                    region="cn-beijing",
                )
                seen[model_id] = record
        except Exception:
            continue

    # 从定价页解析价格并合并
    try:
        _parse_and_merge_pricing(list(seen.values()))
    except Exception:
        pass

    return list(seen.values())


def _fetch_page(url: str, timeout: int = 10) -> Optional[str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PPT2MD-ModelCatalog/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw.decode("utf-8", errors="replace")
    except Exception:
        return None


def _extract_model_ids(html: str) -> Iterable[str]:
    clean = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    clean = re.sub(r"<script[^>]*>.*?</script>", "", clean, flags=re.DOTALL | re.IGNORECASE)
    clean = re.sub(r"<style[^>]*>.*?</style>", "", clean, flags=re.DOTALL | re.IGNORECASE)
    for pattern in _MODEL_ID_PATTERNS:
        for match in pattern.finditer(clean):
            mid = match.group(0).strip().rstrip(".")
            if len(mid) < 5:
                continue
            yield mid


def _is_ignored(model_id: str) -> bool:
    for pat in _IGNORE_PATTERNS:
        if pat.search(model_id):
            return True
    if re.match(r"^[a-z]+[\d]*$", model_id, re.IGNORECASE) and len(model_id) < 5:
        return True
    return False


# ==========================================================================
# 定价解析（从 model-pricing 页面表格）
# ==========================================================================
def _parse_and_merge_pricing(records: List[ModelRecord]) -> None:
    """从定价页 HTML 解析价格并合并到 records。"""
    html = _fetch_page(_PRICING_URL, timeout=15)
    if not html:
        return

    # 先定位"北京"区域
    beijing_section = _extract_region_section(html, "北京")
    if not beijing_section:
        return

    # 匹配定价表格行
    rows = _extract_pricing_rows(beijing_section)
    by_model: Dict[str, List[dict]] = {}
    for row in rows:
        mid = row.get("model_id", "")
        if not mid:
            continue
        by_model.setdefault(mid, []).append(row)

    # 合并到 records
    for rec in records:
        tiers = by_model.get(rec.model_id)
        if tiers:
            rec.price_tiers = tiers
            # 取最低档作为 summary 价格
            lowest = tiers[0]
            rec.input_price = lowest.get("input")
            rec.output_price = lowest.get("output")
            rec.price_source = "dynamic"
            rec.price_region = "cn-beijing"


def _extract_region_section(html: str, region_label: str) -> Optional[str]:
    """从 HTML 中提取指定区域的价格区块。"""
    # 找包含"北京"或 region 名称的表格区域
    pattern = re.compile(
        r'(?:<h[234][^>]*>[^<]*' + re.escape(region_label) + r'[^<]*</h[234]>|'
        r'<table[^>]*>.*?' + re.escape(region_label) + r'.*?</table>)',
        re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(html)
    if match:
        start = max(0, match.start() - 2000)
        end = min(len(html), match.end() + 8000)
        return html[start:end]
    # fallback: 取包含 pricing 表格的整个区域
    table_match = re.search(r'<table[^>]*>.*?</table>', html, re.DOTALL)
    if table_match:
        return html[max(0, table_match.start()-1000):min(len(html), table_match.end()+1000)]
    return html[:30000]  # 最后兜底


def _extract_pricing_rows(html: str) -> List[dict]:
    """从 HTML 区块中解析定价行。"""
    rows = []
    # 尝试多种解析策略

    # Strategy 1: 找所有 qwen 模型名 + 附近数字
    model_blocks = re.findall(
        r'(qwen[\w.\-]{3,60})'
        r'[\s\S]{0,600}?'
        r'(\d+\.?\d*)\s*元',
        html, re.IGNORECASE,
    )
    for mid, price_str in model_blocks:
        try:
            price = float(price_str)
            rows.append({"model_id": mid, "input": price, "output": None, "max_tokens": 32000})
        except ValueError:
            pass

    # Strategy 2: 标准表格行（model | mode | price | ...）
    tr_blocks = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
    for tr in tr_blocks:
        tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.DOTALL | re.IGNORECASE)
        if len(tds) < 3:
            continue
        # 提取模型 ID
        mid = None
        for td in tds[:2]:
            m = re.search(r'(qwen[\w.\-]{3,60})', td, re.IGNORECASE)
            if m:
                mid = m.group(1)
                break
        if not mid:
            continue
        # 提取数字价格
        prices = re.findall(r'(\d+\.?\d*)\s*(?:元|/)', " ".join(tds), re.IGNORECASE)
        if len(prices) >= 2:
            try:
                inp = float(prices[0])
                out = float(prices[1])
            except ValueError:
                continue
        elif len(prices) == 1:
            try:
                inp = float(prices[0])
                out = None
            except ValueError:
                continue
        else:
            continue
        # 提取 token 区间
        tier = {"model_id": mid, "input": inp, "output": out}
        range_match = re.search(r'(\d+)\s*[Kk]', " ".join(tds))
        if range_match:
            tier["max_tokens"] = int(range_match.group(1)) * 1000
        else:
            tier["max_tokens"] = 32000
        rows.append(tier)

    # Strategy 3: 从页面文本中提取"输入"和"输出"价格行
    if len(rows) < 5:
        text_rows = _parse_pricing_from_text(html)
        rows.extend(text_rows)

    return rows


def _parse_pricing_from_text(html: str) -> List[dict]:
    """从纯文本中解析价格行（备用策略）。"""
    rows = []
    # 清理 HTML 标签
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text)

    # 匹配类似 "qwen3-vl-plus  0≤输入≤32K  1.0元/百万tokens  10.0元/百万tokens"
    pricing_pattern = re.compile(
        r'(qwen[\w.\-]{3,60})'
        r'[\s\S]{0,300}?'
        r'(\d+\.?\d*)\s*元[^\d]*'
        r'(\d+\.?\d*)\s*元',
        re.IGNORECASE,
    )
    for match in pricing_pattern.finditer(text):
        mid = match.group(1)
        try:
            inp = float(match.group(2))
            out = float(match.group(3))
        except ValueError:
            continue
        rows.append({"model_id": mid, "input": inp, "output": out, "max_tokens": 32000})

    return rows


# ==========================================================================
# 验证函数
# ==========================================================================

# ── OpenAI 兼容 Chat 验证 ──

def verify_openai_chat_model(
    model_id: str,
    api_key: str,
    base_url: str,
    is_vision: bool = False,
    timeout: int = 10,
) -> Tuple[str, str]:
    """通过 OpenAI 兼容 Chat Completions 验证模型可用性。

    视觉模型使用 32×32 PNG base64 验证。
    返回 (status, error_summary)。
    """
    try:
        payload = _build_verify_payload(model_id, is_vision)
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        endpoint = f"{base_url.rstrip('/')}/chat/completions"
        req = urllib.request.Request(
            endpoint, data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return ("ok", "")
    except urllib.error.HTTPError as e:
        body = _safe_read_body(e)
        return (_extract_error_type(body, str(e.code)), body)
    except Exception as e:
        return (_error_code_from_exception(e), str(e)[:500])


def _build_verify_payload(model_id: str, is_vision: bool) -> dict:
    if is_vision:
        return {
            "model": model_id,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "ping"},
                    {"type": "image_url", "image_url": {"url": _probe_data_url()}},
                ],
            }],
            "max_tokens": 1,
        }
    return {
        "model": model_id,
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 1,
    }


# ── DashScope 原生 Multimodal 验证 ──

def verify_dashscope_multimodal_model(
    model_id: str,
    api_key: str,
    timeout: int = 15,
) -> Tuple[str, str]:
    """通过 DashScope 原生 MultiModalConversation 接口验证视觉模型。

    使用 32×32 探针 PNG，不消耗用户图片。
    """
    import dashscope
    from dashscope import MultiModalConversation

    dashscope.api_key = api_key

    try:
        messages = [{
            "role": "user",
            "content": [
                {"image": _probe_data_url()},
                {"text": "ping"},
            ],
        }]
        response = MultiModalConversation.call(
            model=model_id,
            messages=messages,
            stream=False,
        )
        if response.status_code == 200:
            return ("ok", "")
        code = getattr(response, "code", str(response.status_code))
        msg = getattr(response, "message", "")[:500]
        return (str(code), msg)
    except Exception as e:
        return (_error_code_from_exception(e), str(e)[:500])


# ── 批量验证 ──

def verify_all_capabilities(
    record: ModelRecord,
    api_key: str,
    base_url: str,
    timeout: int = 15,
    console=None,
) -> ModelRecord:
    """对单个模型跑全部相关验证路径并更新能力矩阵。"""
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record.verified_at = now_utc

    # 跳过特殊 family
    if record.family in _SKIP_VERIFY_FAMILIES:
        record.openai_text_status = "skipped"
        record.openai_vision_status = "skipped"
        record.dashscope_multimodal_status = "skipped"
        return record

    is_vision_candidate = bool(record.supports_vision)
    is_dashscope = (record.provider == "dashscope")

    # 1) OpenAI 文本验证（所有非特殊模型）
    _log_verify(console, record.model_id, "OpenAI text")
    status, err = verify_openai_chat_model(
        record.model_id, api_key, base_url, is_vision=False, timeout=timeout,
    )
    record.openai_text_status = "ok" if status == "ok" else "failed"
    record.openai_text_error = err if status != "ok" else None
    _log_verify_result(console, status, err)

    # 2) OpenAI 视觉验证（仅视觉候选）
    if is_vision_candidate:
        _log_verify(console, record.model_id, "OpenAI vision")
        status, err = verify_openai_chat_model(
            record.model_id, api_key, base_url, is_vision=True, timeout=timeout,
        )
        record.openai_vision_status = "ok" if status == "ok" else "failed"
        record.openai_vision_error = err if status != "ok" else None
        _log_verify_result(console, status, err)

    # 3) DashScope 原生 multimodal 验证（仅 DashScope 视觉候选）
    if is_vision_candidate and is_dashscope:
        _log_verify(console, record.model_id, "DashScope multimodal")
        status, err = verify_dashscope_multimodal_model(
            record.model_id, api_key, timeout=timeout,
        )
        record.dashscope_multimodal_status = "ok" if status == "ok" else "failed"
        record.dashscope_multimodal_error = err if status != "ok" else None
        _log_verify_result(console, status, err)

    return record


def verify_models(
    records: List[ModelRecord],
    api_key: str,
    base_url: str,
    limit: Optional[int] = None,
    sleep_interval: float = 0.3,
    timeout: int = 15,
    console=None,
) -> List[ModelRecord]:
    """批量验证模型，使用能力矩阵。"""
    candidates = [
        r for r in records
        if r.family not in _SKIP_VERIFY_FAMILIES and r.supports_openai_chat is not False
    ]
    if limit is not None:
        candidates = candidates[:limit]

    total = len(candidates)
    for i, record in enumerate(candidates):
        if console:
            console.print(f"  [dim][{i+1}/{total}][/] {record.model_id}")

        verify_all_capabilities(record, api_key, base_url, timeout=timeout,
                                console=console)

        if i < total - 1:
            time.sleep(sleep_interval)

    # 未验证的标记 skipped
    verified_ids = {r.model_id for r in candidates}
    for r in records:
        if r.family in _SKIP_VERIFY_FAMILIES:
            r.openai_text_status = "skipped"
            r.openai_vision_status = "skipped"
            r.dashscope_multimodal_status = "skipped"
        elif r.model_id not in verified_ids:
            pass

    return records


def _log_verify(console, model_id: str, path: str) -> None:
    if console:
        console.print(f"    [dim]{path} ...[/]", end=" ")


def _log_verify_result(console, status: str, err: Optional[str]) -> None:
    if not console:
        return
    if status == "ok":
        console.print("[green]OK[/]")
    else:
        summary = (err or "")[:100].replace("\n", " ")
        console.print(f"[red]FAILED[/] {summary}")


# ── 辅助函数 ──

def _safe_read_body(http_error: urllib.error.HTTPError) -> str:
    try:
        return http_error.read().decode("utf-8", errors="replace")[:500]
    except Exception:
        return "(无法读取响应体)"


def _extract_error_type(body: str, status_code: str) -> str:
    try:
        info = json.loads(body)
        if isinstance(info, dict):
            return str(info.get("code", info.get("type", status_code)))
    except Exception:
        pass
    return str(status_code)


def _error_code_from_exception(exc: Exception) -> str:
    name = type(exc).__name__
    msg = str(exc).lower()
    if "timeout" in msg or "timed out" in msg:
        return "timeout"
    if "connection" in msg or "resolve" in msg:
        return "connection_error"
    return name


# ==========================================================================
# 缓存
# ==========================================================================
def load_cache(cache_path: str) -> Optional[Dict[str, Any]]:
    p = Path(cache_path)
    if not p.exists():
        return None
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if "models" in data:
            return data
    except Exception:
        pass
    return None


def save_cache(cache_path: str, data: Dict[str, Any]) -> None:
    p = Path(cache_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def records_to_cache_dict(
    records: List[ModelRecord],
    source_urls: List[str],
    region: str,
    base_url: str,
) -> Dict[str, Any]:
    return {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_urls": source_urls,
        "region": region,
        "base_url": base_url,
        "model_count": len(records),
        "models": [asdict(r) for r in records],
    }


def records_from_cache_dict(data: Dict[str, Any]) -> List[ModelRecord]:
    records = []
    for item in data.get("models", []):
        try:
            records.append(ModelRecord(**item))
        except Exception:
            continue
    return records


# ==========================================================================
# 过滤辅助
# ==========================================================================
def filter_vision_models(records: List[ModelRecord]) -> List[ModelRecord]:
    """视觉候选模型（supports_vision=True 或 family=multimodal）。"""
    result = []
    for r in records:
        if r.supports_vision is True or r.family == "multimodal":
            result.append(r)
    return result


def filter_vision_verified(records: List[ModelRecord]) -> List[ModelRecord]:
    """视觉模型中被至少一种视觉路径验证通过的。"""
    result = []
    for r in records:
        if r.supports_vision is not True and r.family != "multimodal":
            continue
        if "ok" in (r.openai_vision_status, r.dashscope_multimodal_status):
            result.append(r)
    return result


def filter_brain_models(records: List[ModelRecord]) -> List[ModelRecord]:
    """Brain 候选（文本 + 多模态，排除特殊 family）。"""
    return [
        r for r in records
        if r.family not in ("embedding", "rerank", "audio", "image_gen", "video_gen")
    ]


def vision_recommendation_tier(record: ModelRecord) -> int:
    """返回视觉模型的推荐等级：0=已验证可用, 1=官方候选未验证, 2=验证失败。"""
    if record.supports_vision is not True and record.family != "multimodal":
        return 3  # 不推荐
    if record.openai_vision_status == "ok" or record.dashscope_multimodal_status == "ok":
        return 0
    if record.openai_vision_status == "failed" or record.dashscope_multimodal_status == "failed":
        return 2
    return 1
