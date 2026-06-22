import functools
import json
import logging
import re
import time
import urllib.error
import urllib.request

import dashscope
from dashscope import Generation, MultiModalConversation

from .config import AppConfig
from .env import get_dashscope_api_key, get_deepseek_api_key, get_env_value
from .prompts import PROMPT_STAGE_1_VISION, PROMPT_STAGE_2_BRAIN
from .validators import first_api_error_prefix, is_api_error_text

_logger = logging.getLogger("DocPage2MD.models")


# ==========================================================================
# Retry / Backoff
# ==========================================================================
_RETRYABLE_CODES = {429, 500, 502, 503, 504}
_RETRYABLE_EXCEPTIONS = (urllib.error.URLError, ConnectionError, TimeoutError, OSError)


def retry_with_backoff(
    max_retries: int = 3,
    base_sleep: float = 2.0,
    max_sleep: float = 60.0,
):
    """装饰器 / 手动包装器：对可重试的 HTTP 错误和网络异常做指数退避。

    用法：
        @retry_with_backoff(max_retries=3)
        def my_api_call(...): ...

    或手动：
        result = retry_with_backoff(max_retries=3)(my_api_call)(...)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except urllib.error.HTTPError as e:
                    last_exc = e
                    if e.code not in _RETRYABLE_CODES:
                        raise
                except _RETRYABLE_EXCEPTIONS as e:
                    last_exc = e

                if attempt < max_retries:
                    delay = min(base_sleep * (2 ** attempt), max_sleep)
                    _logger.info(
                        "API retry %d/%d, sleeping %.1fs, error: %s",
                        attempt + 1, max_retries, delay,
                        _safe_error_str(last_exc),
                    )
                    time.sleep(delay)

            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


def _safe_error_str(exc: BaseException) -> str:
    """提取错误信息，避免泄漏 API Key。"""
    msg = str(exc)
    # 截断过长的消息
    if len(msg) > 300:
        msg = msg[:300] + "..."
    return msg


def _model_payload(content="", reasoning="", usage=None, request_id=None, provider_latency=None):
    return {
        "content": content or "",
        "reasoning": reasoning or "",
        "usage": usage,
        "request_id": request_id,
        "provider_latency": provider_latency,
    }


def _unpack_model_payload(value):
    if isinstance(value, dict):
        return _model_payload(
            content=value.get("content") or "",
            reasoning=value.get("reasoning") or "",
            usage=value.get("usage"),
            request_id=value.get("request_id"),
            provider_latency=value.get("provider_latency"),
        )
    if isinstance(value, tuple):
        content = value[0] if len(value) > 0 else ""
        reasoning = value[1] if len(value) > 1 else ""
        usage = value[2] if len(value) > 2 else None
        request_id = value[3] if len(value) > 3 else None
        provider_latency = value[4] if len(value) > 4 else None
        return _model_payload(content, reasoning, usage, request_id, provider_latency)
    return _model_payload(str(value or ""))


# ==========================================================================
# OpenAI 兼容调用路径（DashScope 原生之外的可选路径）
# ==========================================================================

def call_aliyun_openai_chat(
    model_id: str,
    messages: list,
    api_key: str,
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    stream: bool = True,
    thinking_budget: int = 0,
    enable_thinking: bool = False,
    timeout: int = 900,
):
    """通过 OpenAI 兼容接口调用纯文本 Chat 模型。

    Returns:
        (full_content, full_reasoning) 或错误字符串。
    """
    payload: dict = {
        "model": model_id,
        "messages": messages,
    }
    if stream:
        payload["stream"] = True

    if enable_thinking and thinking_budget and thinking_budget > 0:
        payload["thinking"] = {"type": "enabled"}
        payload["reasoning_effort"] = "medium"

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    endpoint = f"{base_url.rstrip('/')}/chat/completions"

    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    if stream:
        return _collect_openai_stream(req, timeout)
    return _collect_openai_sync(req, timeout)


def call_aliyun_openai_vision(
    model_id: str,
    image_path: str,
    prompt_text: str,
    api_key: str,
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    stream: bool = True,
    timeout: int = 900,
):
    """通过 OpenAI 兼容 Vision 接口调用视觉模型。

    Args:
        model_id: 模型 ID。
        image_path: 本地图片路径（file:// 格式或绝对路径）。
        prompt_text: prompt 文本。
        api_key: DashScope API Key。
        base_url: OpenAI 兼容端点。
        stream: 是否流式。
        timeout: 超时秒数。

    Returns:
        (full_content, full_reasoning) 或错误字符串元组。
    """
    import base64 as b64

    # 读取图片并编码
    path = image_path.replace("file://", "")
    try:
        with open(path, "rb") as f:
            img_data = b64.b64encode(f.read()).decode("ascii")
    except Exception as e:
        return (f"Image read error: {e}", "")

    # 推断 MIME 类型
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else "png"
    mime_map = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp", "bmp": "bmp"}
    mime = mime_map.get(ext, "png")

    data_url = f"data:image/{mime};base64,{img_data}"

    payload: dict = {
        "model": model_id,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
    }
    if stream:
        payload["stream"] = True

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    endpoint = f"{base_url.rstrip('/')}/chat/completions"

    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    if stream:
        return _collect_openai_stream(req, timeout)
    return _collect_openai_sync(req, timeout)


def _collect_openai_stream(req: urllib.request.Request, timeout: int):
    """收集 OpenAI 兼容流式响应。"""
    full_content = ""
    full_reasoning = ""
    request_id = None
    started_at = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            request_id = resp.headers.get("x-request-id") or resp.headers.get("request-id")
            for raw_line in resp:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue
                choices = event.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                full_reasoning += delta.get("reasoning_content") or ""
                full_content += delta.get("content") or ""
    except Exception as e:
        return (f"OpenAI Stream Error: {_safe_error_str(e)}", full_reasoning)
    return _model_payload(
        full_content,
        full_reasoning,
        usage=None,
        request_id=request_id,
        provider_latency=round(time.perf_counter() - started_at, 3),
    )


def _collect_openai_sync(req: urllib.request.Request, timeout: int):
    """收集 OpenAI 兼容非流式响应。"""
    started_at = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            request_id = resp.headers.get("x-request-id") or resp.headers.get("request-id")
            body = json.loads(resp.read().decode("utf-8"))
        choices = body.get("choices") or []
        if choices:
            msg = choices[0].get("message") or {}
            return _model_payload(
                msg.get("content") or "",
                msg.get("reasoning_content") or "",
                usage=body.get("usage"),
                request_id=body.get("id") or request_id,
                provider_latency=round(time.perf_counter() - started_at, 3),
            )
        return _model_payload(
            "",
            "",
            usage=body.get("usage"),
            request_id=body.get("id") or request_id,
            provider_latency=round(time.perf_counter() - started_at, 3),
        )
    except Exception as e:
        return (f"OpenAI Sync Error: {_safe_error_str(e)}", "")


# ==========================================================================
# Stage 1 & Stage 2 (原有逻辑保留)
# ==========================================================================

def run_stage_1_vision(img_path, slide_no, ppt_name, msg_queue, config: AppConfig):
    """
    Step 1 Worker: 调用 VL 模型提取 Raw Data。
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if config.vision_provider in ("dashscope_openai", "openai_compatible"):
                return _run_openai_compatible_vision(img_path, slide_no, config)

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"image": f"file://{img_path}"},
                        {"text": PROMPT_STAGE_1_VISION},
                    ],
                }
            ]

            responses = MultiModalConversation.call(
                model=config.model_vision,
                messages=messages,
                enable_thinking=True,
                thinking_budget=config.thinking_budget_vision,
                stream=True,
                incremental_output=True,
            )

            full_content = ""
            full_reasoning = ""

            for chunk in responses:
                if chunk.status_code == 200:
                    try:
                        if not hasattr(chunk.output, "choices") or not chunk.output.choices:
                            continue

                        message = chunk.output.choices[0].message

                        r_content = None
                        if hasattr(message, "get"):
                            r_content = message.get("reasoning_content")
                        else:
                            try:
                                r_content = message.reasoning_content
                            except (AttributeError, KeyError):
                                r_content = None

                        if r_content:
                            full_reasoning += r_content

                        c_content = None
                        if hasattr(message, "get"):
                            c_content = message.get("content")
                        else:
                            try:
                                c_content = message.content
                            except (AttributeError, KeyError):
                                c_content = None

                        if c_content:
                            if isinstance(c_content, list):
                                for item in c_content:
                                    if isinstance(item, dict) and "text" in item:
                                        full_content += item["text"]
                            elif isinstance(c_content, str):
                                full_content += c_content

                    except Exception:
                        continue

                else:
                    if "AccessDenied" in str(chunk.code):
                        raise RuntimeError("AccessDenied")
                    return {
                        "success": False,
                        "slide_no": slide_no,
                        "error": f"Stream Error: {chunk.code}",
                    }

            if not full_content:
                if full_reasoning:
                    return {
                        "success": False,
                        "slide_no": slide_no,
                        "error": f"Model only returned reasoning. Trace: {full_reasoning[:200]}...",
                    }
                return {
                    "success": False,
                    "slide_no": slide_no,
                    "error": "Empty response (Stream failed).",
                }

            return {"success": True, "slide_no": slide_no, "raw_text": full_content}

        except Exception as e:
            if "AccessDenied" in str(e):
                raise e
            if attempt == max_retries - 1:
                return {
                    "success": False,
                    "slide_no": slide_no,
                    "error": f"重试失败: {str(e)}",
                }
            time.sleep((attempt + 1) * 2)


def _run_openai_compatible_vision(img_path, slide_no, config: AppConfig):
    api_key = get_env_value(config.vision_api_key_env)
    if not api_key:
        return {
            "success": False,
            "slide_no": slide_no,
            "error": f"missing {config.vision_api_key_env}",
        }

    payload = _unpack_model_payload(
        call_aliyun_openai_vision(
        model_id=config.model_vision,
        image_path=img_path,
        prompt_text=PROMPT_STAGE_1_VISION,
        api_key=api_key,
        base_url=config.vision_base_url,
        stream=True,
        )
    )
    content = payload["content"]
    reasoning = payload["reasoning"]
    if content.startswith("OpenAI") or is_api_error_text(content):
        return {"success": False, "slide_no": slide_no, "error": content}
    if not content:
        if reasoning:
            return {
                "success": False,
                "slide_no": slide_no,
                "error": f"Model only returned reasoning. Trace: {reasoning[:200]}...",
            }
        return {"success": False, "slide_no": slide_no, "error": "Empty response."}
    return {
        "success": True,
        "slide_no": slide_no,
        "raw_text": content,
        "usage": payload.get("usage"),
        "request_id": payload.get("request_id"),
        "provider_latency": payload.get("provider_latency"),
    }


def get_raw_content(raw_data_map, slide_no):
    """安全获取 Raw Data，并截断过长内容以节省 token。"""
    content = raw_data_map.get(slide_no, "(No Data / Out of Range)")
    if len(content) > 3000:
        return content[:3000] + "...(truncated)"
    return content


def run_stage_2_brain_parallel(slide_no, raw_data_map, config: AppConfig):
    """
    Step 2 Worker: 组装 5 页 Raw Data，并调用 Brain 模型。
    """
    filled_prompt = PROMPT_STAGE_2_BRAIN.format(
        prev_2_raw=get_raw_content(raw_data_map, slide_no - 2),
        prev_1_raw=get_raw_content(raw_data_map, slide_no - 1),
        target_raw=get_raw_content(raw_data_map, slide_no),
        next_1_raw=get_raw_content(raw_data_map, slide_no + 1),
        next_2_raw=get_raw_content(raw_data_map, slide_no + 2),
        slide_no=slide_no,
    )

    if config.brain_provider == "deepseek":
        raw_response = _run_deepseek_brain(filled_prompt, config)
    elif config.brain_provider in ("dashscope_openai", "openai_compatible"):
        raw_response = _run_openai_compatible_brain(filled_prompt, config)
    else:
        raw_response = _run_dashscope_brain(filled_prompt, config)
    payload = _unpack_model_payload(raw_response)
    raw_text = payload["content"]

    if is_api_error_text(raw_text):
        return {
            "success": False,
            "slide_no": slide_no,
            "error": raw_text,
            "error_code": first_api_error_prefix(raw_text) or "api_error_text",
            "raw_response": raw_text,
            "usage": payload.get("usage"),
            "request_id": payload.get("request_id"),
            "provider_latency": payload.get("provider_latency"),
        }

    final_markdown = sanitize_stage_2_markdown(raw_text, slide_no)
    if not final_markdown.strip():
        return {
            "success": False,
            "slide_no": slide_no,
            "error": "Empty Stage 2 markdown after sanitize.",
            "error_code": "empty_markdown",
            "raw_response": raw_text,
            "usage": payload.get("usage"),
            "request_id": payload.get("request_id"),
            "provider_latency": payload.get("provider_latency"),
        }

    return {
        "success": True,
        "slide_no": slide_no,
        "markdown": final_markdown,
        "raw_response": raw_text,
        "usage": payload.get("usage"),
        "request_id": payload.get("request_id"),
        "provider_latency": payload.get("provider_latency"),
    }


def sanitize_stage_2_markdown(markdown: str, slide_no: int) -> str:
    """Remove model chatter and internal metadata before writing a Slide_XX.md file."""
    if not markdown:
        return markdown

    text = markdown.strip()

    code_fence = re.fullmatch(r"```(?:markdown|md)?\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if code_fence:
        text = code_fence.group(1).strip()

    text = re.sub(r"<CTX>.*?</CTX>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()

    heading_pattern = re.compile(rf"(?m)^#\s*Slide\s+0*{slide_no}\b.*$")
    heading_match = heading_pattern.search(text)
    if heading_match:
        text = text[heading_match.start():].strip()
    else:
        lines = text.splitlines()
        while lines and _is_stage_2_chatter_line(lines[0]):
            lines.pop(0)
        text = "\n".join(lines).strip()
        if not text.startswith("#"):
            text = f"# Slide {slide_no}\n\n{text}".strip()

    text = _remove_user_invisible_diagnostics(text).strip()
    return text.rstrip() + "\n"


def sanitize_user_invisible_diagnostics(markdown: str) -> str:
    """Remove diagnostics from already assembled Markdown without changing structure."""
    if not markdown:
        return markdown
    return _remove_user_invisible_diagnostics(markdown).rstrip() + "\n"


def _is_stage_2_chatter_line(line: str) -> bool:
    normalized = line.strip().lstrip("> ").strip()
    if not normalized:
        return True
    chatter_prefixes = (
        "好的",
        "当然",
        "以下是",
        "下面是",
        "作为",
        "我已经",
        "我将",
        "根据您提供",
        "基于您提供",
        "已根据",
    )
    return normalized.startswith(chatter_prefixes)


def _remove_user_invisible_diagnostics(markdown: str) -> str:
    lines = (markdown or "").splitlines()
    cleaned = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if _is_diagnostic_admonition_start(stripped):
            index += 1
            while index < len(lines):
                candidate = lines[index]
                if not candidate.strip():
                    index += 1
                    break
                if candidate.lstrip().startswith(">"):
                    index += 1
                    continue
                break
            continue
        if _is_standalone_diagnostic_line(stripped):
            index += 1
            continue
        cleaned.append(line)
        index += 1
    return _strip_inline_diagnostic_parentheticals("\n".join(cleaned))


def _is_diagnostic_admonition_start(stripped: str) -> bool:
    if not stripped.startswith(">"):
        return False
    normalized = stripped.lstrip("> ").strip()
    return bool(
        re.match(r"\[!WARNING\]\s*(原文勘误|识别不确定|公式识别不确定|表格识别不确定|图示识别不确定|Stage\s*2\s*重组失败|质量警告)", normalized, flags=re.IGNORECASE)
    )


def _is_standalone_diagnostic_line(stripped: str) -> bool:
    if not stripped:
        return False
    normalized = stripped.lstrip("> ").strip()
    diagnostic_prefixes = (
        "注：手写看似",
        "注: 手写看似",
        "根据数学逻辑",
        "根据上下文逻辑",
        "根据上下文推测",
        "质量警告：",
        "原始识别：",
        "原始识别已按纯文本保留",
        "Stage 2 重组失败",
        "原因：",
    )
    return normalized.startswith(diagnostic_prefixes)


def _strip_inline_diagnostic_parentheticals(text: str) -> str:
    diagnostic_terms = (
        "手写看似",
        "根据数学逻辑",
        "根据上下文逻辑",
        "根据上下文推测",
        "模型",
        "OCR",
        "识别",
        "推测",
        "应理解",
    )

    def keep_or_drop(match):
        body = match.group(1)
        if body.startswith(("注：", "注:")) and any(term in body for term in diagnostic_terms):
            return ""
        return match.group(0)

    text = re.sub(r"（([^（）]{0,220})）", keep_or_drop, text)
    return re.sub(r"\(([^()]{0,220})\)", keep_or_drop, text)


def _run_dashscope_brain(filled_prompt, config: AppConfig):
    """DashScope 原生文本 API（默认稳定路径）。"""
    try:
        responses = Generation.call(
            model=config.model_brain,
            messages=[{"role": "user", "content": filled_prompt}],
            result_format="message",
            enable_thinking=True,
            thinking_budget=config.thinking_budget_brain,
            stream=True,
            incremental_output=True,
        )

        full_reasoning = ""
        full_content = ""

        for chunk in responses:
            if chunk.status_code == 200:
                choice = chunk.output.choices[0]

                if hasattr(choice.message, "reasoning_content") and choice.message.reasoning_content:
                    full_reasoning += choice.message.reasoning_content

                if hasattr(choice.message, "content") and choice.message.content:
                    full_content += choice.message.content
            else:
                return f"Brain Error: {chunk.code} - {chunk.message}"

        if not full_content:
            return f"Error: Model generated thinking but no content. Trace: {full_reasoning[:100]}..."

        return full_content

    except Exception as e:
        return f"Brain Exception: {str(e)}"


def _run_openai_compatible_brain(filled_prompt, config: AppConfig):
    """OpenAI 兼容文本路径（DashScope compatible / OpenRouter / One API / LiteLLM 等）。"""
    api_key = get_env_value(config.brain_api_key_env)
    if not api_key:
        return f"OpenAI Brain Error: missing {config.brain_api_key_env}."

    payload = _unpack_model_payload(
        call_aliyun_openai_chat(
        model_id=config.model_brain,
        messages=[{"role": "user", "content": filled_prompt}],
        api_key=api_key,
        base_url=config.brain_base_url,
        stream=True,
        thinking_budget=config.thinking_budget_brain,
        enable_thinking=(config.brain_provider == "dashscope_openai"),
        )
    )
    content = payload["content"]
    reasoning = payload["reasoning"]

    if content.startswith("OpenAI") or content.startswith("Error"):
        return content

    if not content:
        return f"Error: OpenAI Brain generated no content. Trace: {reasoning[:100]}..."
    return payload


def _run_deepseek_brain(filled_prompt, config: AppConfig):
    api_key = get_env_value(config.brain_api_key_env) or get_deepseek_api_key()
    if not api_key:
        return f"DeepSeek Error: missing {config.brain_api_key_env}."

    payload = {
        "model": config.model_brain,
        "messages": [{"role": "user", "content": filled_prompt}],
        "thinking": {"type": "enabled"},
        "reasoning_effort": "high",
        "stream": True,
    }
    request = urllib.request.Request(
        f"{config.brain_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        full_reasoning = ""
        full_content = ""
        with urllib.request.urlopen(request, timeout=900) as response:
            for raw_line in response:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line or line.startswith(":"):
                    continue
                if not line.startswith("data:"):
                    continue

                data = line[5:].strip()
                if data == "[DONE]":
                    break

                try:
                    event = json.loads(data)
                except json.JSONDecodeError:
                    continue

                choices = event.get("choices") or []
                if not choices:
                    continue

                delta = choices[0].get("delta") or {}
                full_reasoning += delta.get("reasoning_content") or ""
                full_content += delta.get("content") or ""

        if not full_content:
            return f"DeepSeek Error: model generated no content. Trace: {full_reasoning[:100]}..."
        return full_content

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return f"DeepSeek HTTP Error: {e.code} {e.reason} {body[:500]}"
    except Exception as e:
        return f"DeepSeek Exception: {str(e)}"


def set_dashscope_api_key(config: AppConfig = None, task_key=None):
    if task_key:
        dashscope.api_key = task_key
    else:
        key = None
        if config is not None:
            if config.vision_provider == "dashscope":
                key = get_env_value(config.vision_api_key_env)
            if not key and config.brain_provider == "dashscope":
                key = get_env_value(config.brain_api_key_env)
        dashscope.api_key = key or get_dashscope_api_key()
