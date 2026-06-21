import re
from dataclasses import dataclass
from typing import Literal


Severity = Literal["error", "warning"]

ERROR_TEXT_PREFIXES = (
    "[Vision Failed]",
    "Image read error:",
    "OpenAI Stream Error:",
    "OpenAI Sync Error:",
    "Brain Error:",
    "Brain Exception:",
    "OpenAI Brain Error:",
    "Error:",
    "Error: Model generated thinking but no content",
    "Error: OpenAI Brain generated no content",
    "DeepSeek Error:",
    "DeepSeek HTTP Error:",
    "DeepSeek Exception:",
    "Stream Error:",
    "Empty response",
    "重试失败:",
)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    severity: Severity
    message: str
    slide_no: int
    line: int | None = None
    evidence: str | None = None

    def to_dict(self):
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "slide_no": self.slide_no,
            "line": self.line,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class ValidationResult:
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self):
        return {
            "ok": self.ok,
            "errors": [issue.to_dict() for issue in self.errors],
            "warnings": [issue.to_dict() for issue in self.warnings],
        }


def is_api_error_text(text: str | None) -> bool:
    normalized = (text or "").strip()
    return any(normalized.startswith(prefix) for prefix in ERROR_TEXT_PREFIXES)


def first_api_error_prefix(text: str | None) -> str | None:
    normalized = (text or "").strip()
    for prefix in ERROR_TEXT_PREFIXES:
        if normalized.startswith(prefix):
            return prefix.rstrip(":")
    return None


def validate_slide_markdown(
    markdown: str,
    slide_no: int,
    *,
    raw_response: str | None = None,
    target_raw: str | None = None,
    neighbor_raw: dict[int, str] | None = None,
) -> ValidationResult:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    text = markdown or ""
    stripped = text.strip()

    if is_api_error_text(raw_response) or is_api_error_text(stripped):
        errors.append(_issue("api_error_text", "error", "模型/API 错误文本不能写成正常 Markdown。", slide_no, stripped[:160]))

    if target_raw is not None and is_api_error_text(target_raw):
        errors.append(_issue("vision_failed_target", "error", "当前页 Vision 阶段失败，Brain 阶段不能生成正常 Slide。", slide_no))

    if not stripped:
        errors.append(_issue("empty_markdown", "error", "Markdown 输出为空。", slide_no))
        return ValidationResult(errors=errors, warnings=warnings)

    if raw_response and _is_whole_document_fenced(raw_response):
        warnings.append(_issue("whole_document_code_fence_raw", "warning", "模型原始响应使用代码围栏包裹全文，已尝试清理。", slide_no))

    first_line = stripped.splitlines()[0].strip()
    heading = re.match(r"^#\s*Slide\s+0*(\d+)\b", first_line, flags=re.IGNORECASE)
    if not heading:
        errors.append(_issue("heading_missing_or_mismatch", "error", f"Markdown 必须以 # Slide {slide_no} 开头。", slide_no, first_line))
    elif int(heading.group(1)) != slide_no:
        errors.append(_issue("heading_missing_or_mismatch", "error", f"Markdown 标题页码应为 {slide_no}。", slide_no, first_line))

    slide_headings = re.findall(r"(?m)^#\s*Slide\s+\d+\b", text, flags=re.IGNORECASE)
    if len(slide_headings) > 1:
        errors.append(_issue("multiple_slide_headings", "error", "输出中出现多个 Slide 标题，可能混入其他页。", slide_no, "; ".join(slide_headings[:3])))

    if re.search(r"</?CTX>", text, flags=re.IGNORECASE) or re.search(r"\[(?:P-\d|N\+\d|Target)\]", text):
        errors.append(_issue("ctx_marker_leak", "error", "输出泄漏了内部上下文标记。", slide_no))

    if _is_whole_document_fenced(stripped):
        errors.append(_issue("whole_document_code_fence", "error", "最终 Markdown 仍被代码围栏包裹全文。", slide_no))

    if _fence_count(text) % 2:
        errors.append(_issue("unclosed_code_fence", "error", "Markdown 代码围栏数量不平衡。", slide_no))

    code_free = _strip_code_regions(text)
    if code_free.count("$$") % 2:
        errors.append(_issue("display_math_unbalanced", "error", "行间公式 $$ 分隔符数量不成对。", slide_no))

    body = "\n".join(stripped.splitlines()[1:]).strip()
    if not body:
        errors.append(_issue("empty_body", "error", "Markdown 只有标题，没有正文。", slide_no))
    elif target_raw and len(target_raw.strip()) > 120 and len(body) < 20:
        warnings.append(_issue("short_body", "warning", "当前页 Raw Data 较长，但 Markdown 正文很短，可能遗漏内容。", slide_no))

    if "### Figure Analysis" in text:
        warnings.append(_issue("unrendered_figure_analysis", "warning", "Figure Analysis 未整理为 Figure 描述引用块。", slide_no))

    if target_raw and "### Figure Analysis" in target_raw and not _has_figure_note(text):
        warnings.append(_issue("figure_note_missing", "warning", "当前页 Raw Data 含 Figure Analysis，但输出没有 Figure 描述引用块。", slide_no))

    leak_evidence = _find_possible_neighbor_leak(text, target_raw or "", neighbor_raw or {})
    if leak_evidence:
        warnings.append(_issue("possible_neighbor_leak", "warning", "输出疑似包含邻页独有长片段。", slide_no, leak_evidence))

    if re.search(r"(?m)^\s*(好的|当然|以下是|下面是|根据您提供|基于您提供|我将|我已经)", text):
        warnings.append(_issue("chatter_residue", "warning", "输出中仍有模型寒暄或处理说明。", slide_no))

    if "\x00" in text:
        warnings.append(_issue("control_chars", "warning", "输出包含异常控制字符。", slide_no))

    if re.search(r"\\[\[\]]", code_free):
        warnings.append(_issue("inline_math_suspicious", "warning", "输出包含 \\[ 或 \\]，建议统一为 $$。", slide_no))

    return ValidationResult(errors=errors, warnings=warnings)


def _issue(code: str, severity: Severity, message: str, slide_no: int, evidence: str | None = None) -> ValidationIssue:
    return ValidationIssue(
        code=code,
        severity=severity,
        message=message,
        slide_no=slide_no,
        evidence=evidence,
    )


def _is_whole_document_fenced(text: str) -> bool:
    return bool(re.fullmatch(r"```(?:markdown|md)?\s*.*?\s*```", text.strip(), flags=re.DOTALL | re.IGNORECASE))


def _fence_count(text: str) -> int:
    return len(re.findall(r"(?m)^```", text))


def _strip_code_regions(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    return re.sub(r"`[^`\n]*`", "", text)


def _has_figure_note(text: str) -> bool:
    return "> [!NOTE] Figure 描述" in text or "> [!NOTE] 图示说明" in text


def _find_possible_neighbor_leak(markdown: str, target_raw: str, neighbor_raw: dict[int, str]) -> str | None:
    normalized_output = _normalize_for_leak(markdown)
    normalized_target = _normalize_for_leak(target_raw)
    if not normalized_output or not neighbor_raw:
        return None

    for page_no, raw in neighbor_raw.items():
        for snippet in _candidate_snippets(raw):
            normalized_snippet = _normalize_for_leak(snippet)
            if len(normalized_snippet) < 18:
                continue
            if normalized_snippet in normalized_target:
                continue
            if normalized_snippet in normalized_output:
                return f"neighbor={page_no}: {snippet[:120]}"
    return None


def _candidate_snippets(text: str) -> list[str]:
    snippets = []
    for line in (text or "").splitlines():
        line = line.strip()
        if len(line) >= 18:
            snippets.append(line)
    if snippets:
        return snippets
    compact = " ".join((text or "").split())
    if len(compact) >= 40:
        return [compact[:80]]
    return []


def _normalize_for_leak(text: str) -> str:
    return re.sub(r"\s+", "", text or "").lower()
