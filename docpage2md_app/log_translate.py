from __future__ import annotations

import re


LOG_MESSAGE_RE = re.compile(r"\+\s*(\d+(?:\.\d+)?)s\s+\|\s+(.*)$")
DOCUMENT_READY_RE = re.compile(r"DocumentIR ready: pages=(\d+)")
HYBRID_WORKERS_RE = re.compile(r"Hybrid enrichment workers: pages=(\d+), vision=(\d+), brain=(\d+)")
HYBRID_CROP_BATCH_RE = re.compile(r"Hybrid crop vision batch start: blocks=(\d+), workers=(\d+)")
HYBRID_CROP_BATCH_DONE_RE = re.compile(
    r"Hybrid crop vision batch done: blocks=(\d+), succeeded=(\d+), failed=(\d+), elapsed=([\d.]+)s"
)
HYBRID_BRAIN_BATCH_RE = re.compile(r"Hybrid Brain batch start: pages=(\d+), workers=(\d+)")
HYBRID_BRAIN_BATCH_DONE_RE = re.compile(r"Hybrid Brain batch done: pages=(\d+), statuses=([^,]+), elapsed=([\d.]+)s")
HYBRID_PAGE_START_RE = re.compile(r"Hybrid page (\d+)/(\d+) start")
HYBRID_PAGE_REFINER_DONE_RE = re.compile(r"Hybrid page (\d+) refiner done")
HYBRID_PAGE_BRAIN_START_RE = re.compile(r"Hybrid page (\d+) Brain start")
HYBRID_PAGE_BRAIN_DONE_RE = re.compile(
    r"Hybrid page (\d+) Brain done: status=([^,]+), ops_requested=(\d+), applied=(\d+), rejected=(\d+)"
)
HYBRID_PAGE_CROP_RE = re.compile(
    r"Hybrid page (\d+) crop vision: status=([^,]+), attempted=(\d+), succeeded=(\d+), failed=(\d+)"
)
CROP_VISION_START_RE = re.compile(r"Crop vision start: slide=(\d+), block=([^,]+)")
CROP_VISION_OK_RE = re.compile(r"Crop vision ok: slide=(\d+), block=([^,]+), changed=(.+)")
CROP_VISION_FAILED_RE = re.compile(r"Crop vision failed: slide=(\d+), block=([^,]+), code=(.+)")
PAGE_RENDERED_RE = re.compile(r"Page rendered: slide=(\d+), status=([^,]+)")
RENDERING_PAGE_RE = re.compile(r"Rendering page (\d+)/(\d+): slide=(\d+), blocks=(\d+)")
MINERU_PROCESSED_RE = re.compile(r"MinerU (?:API|artifact) processed: (\d+) pages -> (.+)")
MINERU_BATCH_SUBMITTED_RE = re.compile(r"MinerU batch submitted: .*files=(\d+)")

ZH_DOCUMENT_READY_RE = re.compile(r"文档结构已就绪：共\s*(\d+)\s*页")
ZH_HYBRID_PAGE_START_RE = re.compile(r"准备第\s*(\d+)/(\d+)\s*页精修")
ZH_CROP_VISION_START_RE = re.compile(r"Vision 正在识别：第\s*(\d+)\s*页，块=([^，]+)")
ZH_CROP_VISION_OK_RE = re.compile(r"Vision 识别完成：第\s*(\d+)\s*页，块=([^，]+)")
ZH_CROP_VISION_FAILED_RE = re.compile(r"Vision 识别失败：第\s*(\d+)\s*页，块=([^，]+)")
ZH_HYBRID_PAGE_BRAIN_START_RE = re.compile(r"Brain 正在精修第\s*(\d+)\s*页")
ZH_HYBRID_PAGE_REFINER_DONE_RE = re.compile(r"校验器完成第\s*(\d+)\s*页")
ZH_PAGE_RENDERED_RE = re.compile(r"Markdown 已生成：第\s*(\d+)\s*页，状态=([^，]+)")
ZH_MINERU_PROCESSED_RE = re.compile(r"文件处理完成：共\s*(\d+)\s*页，输出目录=(.+)")
ZH_MINERU_BATCH_SUBMITTED_RE = re.compile(r"MinerU 批量任务已提交：batch_id=.*文件数=(\d+)")

_ENGINE_MODE_LABELS = {
    "hybrid": "混合精修",
    "mineru_only": "仅 MinerU 解析",
    "vision_only": "纯视觉旧流程",
}
_MODEL_PROFILE_LABELS = {
    "cheap": "省钱",
    "balanced": "均衡",
    "accurate": "高精度",
    "manual": "自定义",
}
_STATE_LABELS = {
    "waiting-file": "等待文件上传",
    "waiting": "等待解析",
    "running": "解析中",
    "done": "完成",
    "failed": "失败",
    "unknown": "未知",
}
_STATUS_LABELS = {
    "ok": "正常",
    "partial": "部分完成",
    "failed": "失败",
    "skipped": "跳过",
    "fail_open": "保守回退",
}
_BLOCK_TYPE_LABELS = {
    "formula_block": "公式块",
    "image_ref": "图片块",
    "figure_note": "图示说明",
    "table": "表格",
}
_FIELD_LABELS = {
    "formula_quality": "公式质量",
    "latex": "LaTeX",
    "text": "文本",
    "description": "说明",
    "type": "类型",
    "none": "无",
}


def translate_log_line(line: str) -> str:
    stripped = line.rstrip("\n")
    match = LOG_MESSAGE_RE.search(stripped)
    if match:
        return f"{stripped[:match.start(2)]}{translate_progress_message(match.group(2).strip())}\n"
    return translate_progress_message(stripped) + ("\n" if line.endswith("\n") else "")


def translate_progress_message(message: str) -> str:
    """Translate backend progress events to Chinese while preserving ids, paths and counts."""
    if match := re.search(
        r"MinerU mode start: mode=([^,]+), profile=([^,]+), mineru_model=([^,]+), page_ranges=([^,]+), token_env=(.+)",
        message,
    ):
        mode, profile, mineru_model, page_ranges, token_env = match.groups()
        pages = "全量" if page_ranges == "all" else page_ranges
        return (
            f"开始 MinerU 主流程：处理模式={_engine_mode_label(mode)}，模型档位={_model_profile_label(profile)}，"
            f"MinerU模型={mineru_model}，页码={pages}，Token环境变量={token_env}"
        )
    if match := re.search(r"Models: vision=([^ ]+) brain=(.+)", message):
        return f"当前模型：Vision={match.group(1)}；Brain={match.group(2)}"
    if match := re.search(r"MinerU client ready: base_url=([^,]+), token_env=(.+)", message):
        return f"MinerU 客户端已就绪：服务地址={match.group(1)}，Token环境变量={match.group(2)}"
    if match := re.search(r"Submitting local files to MinerU: (.+)", message):
        return f"正在上传本地文件到 MinerU：{_translate_file_sizes(match.group(1))}"
    if match := re.search(r"MinerU request upload URLs: files=(\d+), page_ranges=([^,]+), model=(.+)", message):
        pages = "全量" if match.group(2) == "all" else match.group(2)
        return f"正在向 MinerU 申请上传地址：文件数={match.group(1)}，页码={pages}，模型={match.group(3)}"
    if match := re.search(r"MinerU HTTP ([A-Z]+) (.+?) ok: elapsed=([\d.]+)s, trace_id=(.*)", message):
        trace = match.group(4) or "-"
        return f"MinerU 接口请求成功：{match.group(1)} {match.group(2)}，耗时={match.group(3)}秒，trace_id={trace}"
    if match := re.search(r"Uploading file to MinerU signed URL: name=([^,]+), bytes=(\d+)", message):
        return f"正在上传文件：{match.group(1)}，大小={_format_bytes(int(match.group(2)))}"
    if match := re.search(r"Upload complete: name=(.+)", message):
        return f"文件上传完成：{match.group(1)}"
    if match := re.search(r"MinerU local upload submitted: batch_id=([^,]+), files=(\d+)", message):
        return f"本地文件已提交给 MinerU：batch_id={match.group(1)}，文件数={match.group(2)}"
    if match := re.search(r"MinerU batch submitted: batch_id=([^,]+), files=(\d+)", message):
        return f"MinerU 批量任务已提交：batch_id={match.group(1)}，文件数={match.group(2)}"
    if match := re.search(r"Query MinerU batch: batch_id=(.+)", message):
        return f"正在查询 MinerU 批量任务：batch_id={match.group(1)}"
    if match := re.search(r"MinerU batch poll #(\d+): batch_id=([^,]+), states=(.+)", message):
        return f"等待 MinerU 解析：第 {match.group(1)} 次查询，状态={_translate_state_text(match.group(3))}"
    if match := re.search(r"MinerU batch poll #(\d+): batch_id=([^,]+), no results yet", message):
        return f"等待 MinerU 解析：第 {match.group(1)} 次查询，暂未返回结果"
    if match := re.search(r"MinerU batch done: batch_id=([^,]+), files=(\d+)", message):
        return f"MinerU 批量解析完成：batch_id={match.group(1)}，文件数={match.group(2)}"
    if match := re.search(r"Submitting remote URL to MinerU: (.+)", message):
        return f"正在提交远程 URL 到 MinerU：{match.group(1)}"
    if match := re.search(r"MinerU submit URL task: model=([^,]+), page_ranges=(.+)", message):
        pages = "全量" if match.group(2) == "all" else match.group(2)
        return f"正在提交 MinerU 远程文件解析任务：模型={match.group(1)}，页码={pages}"
    if match := re.search(r"MinerU task submitted: task_id=(.+)", message):
        return f"MinerU 任务已提交：task_id={match.group(1)}"
    if match := re.search(r"Query MinerU task: task_id=(.+)", message):
        return f"正在查询 MinerU 单文件任务：task_id={match.group(1)}"
    if match := re.search(r"MinerU task poll #(\d+): task_id=([^,]+), state=(.+)", message):
        return f"等待 MinerU 解析：第 {match.group(1)} 次查询，状态={_state_label(match.group(3))}"
    if match := re.search(r"MinerU task done: task_id=(.+)", message):
        return f"MinerU 单文件解析完成：task_id={match.group(1)}"
    if match := re.search(r"Downloading MinerU zip: source=([^,]+), cache_key=(.+)", message):
        return f"正在下载 MinerU 结果压缩包：来源={match.group(1)}，缓存键={match.group(2)}"
    if match := re.search(r"Downloading MinerU result zip: dest=(.+)", message):
        return f"正在下载 MinerU 结果文件：保存到={match.group(1)}"
    if match := re.search(r"MinerU result zip saved: dest=([^,]+), bytes=(\d+)", message):
        return f"MinerU 结果文件已保存：{match.group(1)}，大小={_format_bytes(int(match.group(2)))}"
    if match := re.search(r"MinerU zip downloaded: (.+) \((\d+) bytes\)", message):
        return f"MinerU 结果压缩包已下载：{match.group(1)}，大小={_format_bytes(int(match.group(2)))}"
    if match := re.search(r"Unzipping MinerU result: (.+)", message):
        return f"正在解压 MinerU 结果：{match.group(1)}"
    if message == "Writing MinerU task manifest":
        return "正在写入 MinerU 任务清单"
    if match := re.search(r"Processing existing MinerU artifact: (.+)", message):
        return f"正在处理已有 MinerU artifact：{match.group(1)}"
    if match := re.search(r"Processing MinerU artifact into Markdown: (.+)", message):
        return f"正在把 MinerU artifact 转成 Markdown：{match.group(1)}"
    if match := re.search(r"Discovering MinerU artifacts: (.+)", message):
        return f"正在扫描 MinerU artifact：{match.group(1)}"
    if match := re.search(r"Output directory ready: (.+)", message):
        return f"输出目录已准备：{match.group(1)}"
    if message == "Adapting MinerU artifacts to DocumentIR":
        return "正在把 MinerU 结果转换为内部文档结构"
    if match := DOCUMENT_READY_RE.search(message):
        block_count = re.search(r"blocks=(\d+)", message)
        return f"文档结构已就绪：共 {match.group(1)} 页，块数={block_count.group(1) if block_count else '?'}"
    if match := re.search(r"Copied MinerU crop assets: count=(\d+)", message):
        return f"已复制 MinerU 裁剪素材：{match.group(1)} 个"
    if message == "Copied MinerU raw artifacts":
        return "已复制 MinerU 原始结果"
    if message.startswith("Hybrid enrichment start"):
        return "开始混合精修：裁剪图 Vision 识别 + Brain 结构修正 + 校验渲染"
    if match := HYBRID_WORKERS_RE.search(message):
        return f"混合精修并发配置：页数={match.group(1)}，Vision并发={match.group(2)}，Brain并发={match.group(3)}"
    if match := HYBRID_PAGE_START_RE.search(message):
        return f"准备第 {match.group(1)}/{match.group(2)} 页精修：{message.split(':', 1)[-1].strip()}"
    if match := HYBRID_CROP_BATCH_RE.search(message):
        return f"开始并行识别裁剪块：裁剪块={match.group(1)}，并发={match.group(2)}"
    if match := HYBRID_CROP_BATCH_DONE_RE.search(message):
        return (
            f"裁剪块并行识别完成：总数={match.group(1)}，成功={match.group(2)}，"
            f"失败={match.group(3)}，耗时={match.group(4)}秒"
        )
    if match := CROP_VISION_START_RE.search(message):
        block_type = re.search(r"type=([^,]+)", message)
        type_text = _block_type_label(block_type.group(1)) if block_type else "未知"
        return f"Vision 正在识别：第 {match.group(1)} 页，块={match.group(2)}，类型={type_text}"
    if match := CROP_VISION_OK_RE.search(message):
        return f"Vision 识别完成：第 {match.group(1)} 页，块={match.group(2)}，更新={_translate_fields(match.group(3))}"
    if match := CROP_VISION_FAILED_RE.search(message):
        return f"Vision 识别失败：第 {match.group(1)} 页，块={match.group(2)}，原因={match.group(3)}"
    if match := HYBRID_PAGE_CROP_RE.search(message):
        return (
            f"第 {match.group(1)} 页裁剪块识别汇总：状态={_status_label(match.group(2))}，"
            f"尝试={match.group(3)}，成功={match.group(4)}，失败={match.group(5)}"
        )
    if match := HYBRID_BRAIN_BATCH_RE.search(message):
        return f"开始并行 Brain 精修：页数={match.group(1)}，并发={match.group(2)}"
    if match := HYBRID_BRAIN_BATCH_DONE_RE.search(message):
        return (
            f"Brain 并行精修完成：页数={match.group(1)}，状态={_translate_status_counts(match.group(2))}，"
            f"耗时={match.group(3)}秒"
        )
    if match := HYBRID_PAGE_BRAIN_START_RE.search(message):
        context = re.search(r"context_pages=(\d+)", message)
        return f"Brain 正在精修第 {match.group(1)} 页：上下文页数={context.group(1) if context else '?'}"
    if match := HYBRID_PAGE_BRAIN_DONE_RE.search(message):
        return (
            f"Brain 完成第 {match.group(1)} 页：状态={_status_label(match.group(2))}，请求操作={match.group(3)}，"
            f"应用={match.group(4)}，拒绝={match.group(5)}"
        )
    if match := re.search(r"Hybrid page (\d+) Brain failed: code=([^,]+), error=(.+)", message):
        return f"Brain 精修第 {match.group(1)} 页失败：错误码={match.group(2)}，错误={match.group(3)}"
    if match := HYBRID_PAGE_REFINER_DONE_RE.search(message):
        changed = re.search(r"changed=([^,]+)", message)
        applied = re.search(r"applied=(\d+)", message)
        dismissed = re.search(r"dismissed=(\d+)", message)
        return (
            f"校验器完成第 {match.group(1)} 页：是否改动={_bool_label(changed.group(1) if changed else '?')}，"
            f"应用={applied.group(1) if applied else '?'}，拒绝={dismissed.group(1) if dismissed else '?'}"
        )
    if message.startswith("Hybrid enrichment done:"):
        return f"混合精修完成：{message.split(':', 1)[1].strip()}"
    if match := re.search(r"Wrote document IR: (.+)", message):
        return f"已写入内部文档结构：{match.group(1)}"
    if match := RENDERING_PAGE_RE.search(message):
        return f"正在渲染 Markdown：第 {match.group(1)}/{match.group(2)} 页，slide={match.group(3)}，块数={match.group(4)}"
    if match := PAGE_RENDERED_RE.search(message):
        markdown = re.search(r"markdown=([^,]+)", message)
        return f"Markdown 已生成：第 {match.group(1)} 页，状态={_status_label(match.group(2))}，文件={markdown.group(1) if markdown else '?'}"
    if message == "Merging per-page Markdown into FULL document":
        return "正在合并每页 Markdown 为 FULL 文档"
    if match := re.search(r"Markdown rendering done: pages=(\d+), elapsed=([\d.]+)s", message):
        return f"Markdown 渲染完成：页数={match.group(1)}，耗时={match.group(2)}秒"
    if match := re.search(r"Wrote run report: (.+), status=(.+)", message):
        return f"运行报告已写入：{match.group(1)}，状态={_status_label(match.group(2))}"
    if match := MINERU_PROCESSED_RE.search(message):
        return f"文件处理完成：共 {match.group(1)} 页，输出目录={match.group(2)}"
    if match := re.search(r"MinerU batch complete: (\d+)/(\d+) files", message):
        return f"MinerU 批量任务完成：{match.group(1)}/{match.group(2)} 个文件"
    if message.startswith("MinerU API failed:"):
        return f"MinerU API 失败：{message.split(':', 1)[1].strip()}"
    if message.startswith("MinerU mode requires "):
        return "MinerU 主流程缺少输入来源：请指定 artifact、URL、本地文件、本地多文件或文件夹。"
    return message


def _engine_mode_label(value: str) -> str:
    return _ENGINE_MODE_LABELS.get(value, value)


def _model_profile_label(value: str) -> str:
    return _MODEL_PROFILE_LABELS.get(value, value)


def _state_label(value: str) -> str:
    return _STATE_LABELS.get(value, value)


def _status_label(value: str) -> str:
    return _STATUS_LABELS.get(value, value)


def _bool_label(value: str) -> str:
    return {"True": "是", "False": "否", "true": "是", "false": "否"}.get(value, value)


def _block_type_label(value: str) -> str:
    return _BLOCK_TYPE_LABELS.get(value, value)


def _translate_fields(value: str) -> str:
    return "、".join(_FIELD_LABELS.get(item.strip(), item.strip()) for item in value.split(",") if item.strip())


def _translate_file_sizes(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return f"{match.group(1)}（{_format_bytes(int(match.group(2)))}）"

    return re.sub(r"([^,]+?) \((\d+) bytes\)", repl, value)


def _translate_state_text(value: str) -> str:
    translated = value
    for raw, label in _STATE_LABELS.items():
        translated = re.sub(rf"\b{re.escape(raw)}\b", label, translated)
    return translated


def _translate_status_counts(value: str) -> str:
    parts = []
    for part in value.split(";"):
        if ":" not in part:
            parts.append(_status_label(part.strip()))
            continue
        key, count = part.split(":", 1)
        parts.append(f"{_status_label(key.strip())}:{count.strip()}")
    return "；".join(part for part in parts if part)


def _format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f}{unit}" if unit != "B" else f"{int(size)}B"
        size /= 1024
    return f"{value}B"
