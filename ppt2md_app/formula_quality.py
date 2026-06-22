import re
from dataclasses import dataclass
from typing import Literal


FORMULA_QUALITY_SCHEMA_VERSION = 1
Severity = Literal["warning"]
_ALIGNMENT_ENV_RE = re.compile(
    r"\\begin\{(?P<env>aligned|alignedat|align\*?|split|gathered)\}"
    r"(?P<args>(?:\{[^{}]*\})?)"
    r"(?P<body>.*?)\\end\{(?P=env)\}",
    flags=re.DOTALL,
)
_TAG_RE = re.compile(r"\\tag\*?\s*\{[^{}]+\}")
_TRAILING_QUAD_NUMBER_RE = re.compile(
    r"(?P<body>.*?)(?:\s*\\(?:quad|qquad)\s*)\((?P<number>[^()\n]{1,24})\)\s*$",
    flags=re.DOTALL,
)
_DISPLAY_MATH_RE = re.compile(r"\$\$(.*?)\$\$", flags=re.DOTALL)
_BRACKET_DISPLAY_RE = re.compile(r"\\\[(.*?)\\\]", flags=re.DOTALL)
_CODE_FENCE_RE = re.compile(r"```.*?```", flags=re.DOTALL)


@dataclass(frozen=True)
class FormulaQualityIssue:
    code: str
    severity: Severity
    message: str
    evidence: str | None = None

    def to_dict(self):
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class FormulaQualityResult:
    latex: str
    warnings: list[FormulaQualityIssue]
    uncertain: bool

    @property
    def ok(self) -> bool:
        return not self.warnings

    def to_dict(self):
        return {
            "schema_version": FORMULA_QUALITY_SCHEMA_VERSION,
            "ok": self.ok,
            "latex": self.latex,
            "warnings": [warning.to_dict() for warning in self.warnings],
            "uncertain": self.uncertain,
        }


def assess_formula_text(text: str) -> FormulaQualityResult:
    latex = normalize_formula_text(text)
    warnings: list[FormulaQualityIssue] = []
    if not latex:
        warnings.append(_issue("formula_empty", "公式 block 为空。"))
        return FormulaQualityResult(latex, warnings, False)

    if _unbalanced_pair(latex, "{", "}"):
        warnings.append(_issue("formula_brace_unbalanced", "公式中的花括号数量不平衡。", latex[:120]))
    if _unbalanced_pair(latex, "(", ")"):
        warnings.append(_issue("formula_parenthesis_unbalanced", "公式中的圆括号数量不平衡。", latex[:120]))
    if _unbalanced_pair(latex, "[", "]"):
        warnings.append(_issue("formula_bracket_unbalanced", "公式中的方括号数量不平衡。", latex[:120]))
    if len(re.findall(r"\\left\b", latex)) != len(re.findall(r"\\right\b", latex)):
        warnings.append(_issue("latex_left_right_unbalanced", "\\left 与 \\right 数量不匹配。", latex[:120]))
    if re.search(r"\\frac(?!\s*\{)", latex):
        warnings.append(_issue("latex_frac_missing_braces", "\\frac 后缺少花括号参数。", latex[:120]))
    if _looks_truncated(latex):
        warnings.append(_issue("formula_truncated", "公式疑似在运算符或未完成命令处截断。", latex[:120]))
    if _is_isolated_operator_formula(latex):
        warnings.append(_issue("formula_isolated_operator", "公式只有孤立运算符或关系符，无法可靠使用。", latex[:120]))
    if _looks_like_reasoning_without_formula(latex):
        warnings.append(_issue("formula_reasoning_without_latex", "公式 block 疑似包含模型思考说明而不是公式。", latex[:120]))

    uncertain = has_uncertain_formula_marker(latex)
    if uncertain:
        warnings.append(_issue("formula_uncertain_marker", "公式中包含不确定识别标记。", latex[:120]))
    return FormulaQualityResult(latex, _dedupe_issues(warnings), uncertain)


def normalize_formula_text(text: str) -> str:
    stripped = (text or "").strip()
    stripped = _strip_outer_formula_delimiters(stripped)
    stripped = _normalize_alignment_environments(stripped)
    stripped = _normalize_trailing_equation_number(stripped)
    return stripped.strip()


def normalize_markdown_formula_blocks(markdown: str) -> str:
    """Normalize display-math blocks without touching fenced raw text."""
    if not markdown:
        return ""

    parts = _CODE_FENCE_RE.split(markdown)
    fences = _CODE_FENCE_RE.findall(markdown)
    rendered = []
    for index, part in enumerate(parts):
        rendered.append(_normalize_markdown_formula_segment(part))
        if index < len(fences):
            rendered.append(fences[index])
    return "".join(rendered)


def formula_markup_needs_normalize(text: str) -> bool:
    stripped = (text or "").strip()
    return normalize_formula_text(stripped) != stripped


def markdown_formula_markup_needs_normalize(markdown: str) -> bool:
    return normalize_markdown_formula_blocks(markdown or "") != (markdown or "")


def _strip_outer_formula_delimiters(text: str) -> str:
    stripped = text.strip()
    changed = True
    while changed:
        changed = False
        if stripped.startswith("$$") and stripped.endswith("$$"):
            stripped = stripped[2:-2].strip()
            changed = True
        if stripped.startswith(r"\[") and stripped.endswith(r"\]"):
            stripped = stripped[2:-2].strip()
            changed = True
        if stripped.startswith(r"\(") and stripped.endswith(r"\)"):
            stripped = stripped[2:-2].strip()
            changed = True
    return stripped


def _normalize_alignment_environments(text: str) -> str:
    def replace(match: re.Match) -> str:
        env = match.group("env")
        args = match.group("args") or ""
        body = match.group("body")
        tag_matches = list(_TAG_RE.finditer(body))
        output_env = "aligned" if env in {"align", "align*"} else env
        moved_tag = None
        normalized_body = body

        if len(tag_matches) == 1:
            moved_tag = tag_matches[0].group(0).strip()
            normalized_body = body[: tag_matches[0].start()] + body[tag_matches[0].end() :]
        elif len(tag_matches) == 0:
            quad_match = _TRAILING_QUAD_NUMBER_RE.match(body)
            if quad_match:
                moved_tag = f"\\tag{{{quad_match.group('number').strip()}}}"
                normalized_body = quad_match.group("body")
        else:
            if output_env == env:
                return match.group(0)

        if not moved_tag and output_env == env:
            return match.group(0)
        normalized_body = _clean_alignment_body(normalized_body)
        rendered = f"\\begin{{{output_env}}}{args}{normalized_body}\\end{{{output_env}}}"
        return f"{rendered}\n{moved_tag}" if moved_tag else rendered

    return _ALIGNMENT_ENV_RE.sub(replace, text)


def _clean_alignment_body(body: str) -> str:
    cleaned = re.sub(r"[ \t]+(?=\n)", "", body)
    cleaned = re.sub(r"\n[ \t]*\n(?=\s*$)", "\n", cleaned)
    if cleaned and not cleaned.endswith("\n"):
        cleaned = cleaned.rstrip() + "\n"
    return cleaned


def _normalize_trailing_equation_number(text: str) -> str:
    if _TAG_RE.search(text):
        return text
    match = _TRAILING_QUAD_NUMBER_RE.match(text)
    if not match:
        return text
    body = match.group("body").rstrip()
    number = match.group("number").strip()
    if not body or not number:
        return text
    separator = "\n" if re.search(r"\\end\{(?:aligned|align\*?|split)\}\s*$", body) else " "
    return f"{body}{separator}\\tag{{{number}}}"


def _normalize_markdown_formula_segment(markdown: str) -> str:
    text = _BRACKET_DISPLAY_RE.sub(lambda match: _format_display_math(normalize_formula_text(match.group(1))), markdown)
    return _DISPLAY_MATH_RE.sub(lambda match: _normalize_display_match(match), text)


def _normalize_display_match(match: re.Match) -> str:
    original = match.group(1)
    normalized = normalize_formula_text(original)
    if normalized == original.strip():
        return match.group(0)
    return _format_display_math(normalized)


def _format_display_math(latex: str) -> str:
    return f"$$\n{latex.strip()}\n$$"


def has_uncertain_formula_marker(text: str) -> bool:
    lower = (text or "").lower()
    return (
        "[?]" in text
        or "？" in text
        or "无法确定" in text
        or "看不清" in text
        or "不确定" in text
        or "uncertain" in lower
        or "illegible" in lower
    )


def _looks_truncated(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped:
        return False
    if re.search(r"(?:[=+\-*/^_,]|\\frac|\\sqrt|\\sum|\\int|\\lim)\s*$", stripped):
        return True
    return bool(re.search(r"\\[A-Za-z]+\\?$", stripped))


def _is_isolated_operator_formula(text: str) -> bool:
    stripped = re.sub(r"\s+", "", text or "")
    if not stripped:
        return False
    return bool(re.fullmatch(r"[=≈≤≥<>+\-*/^_{}()[\],.;:|]+", stripped))


def _looks_like_reasoning_without_formula(text: str) -> bool:
    lower = (text or "").lower()
    markers = (
        "thinking",
        "reasoning",
        "analysis:",
        "思考",
        "推理过程",
        "我将",
        "我们需要",
    )
    has_math_signal = bool(re.search(r"(\\[A-Za-z]+|[=≈≤≥+\-*/^_{}]|\d)", text or ""))
    return any(marker in lower for marker in markers) and not has_math_signal


def _unbalanced_pair(text: str, left: str, right: str) -> bool:
    escaped_left = re.escape(left)
    escaped_right = re.escape(right)
    return len(re.findall(rf"(?<!\\){escaped_left}", text)) != len(re.findall(rf"(?<!\\){escaped_right}", text))


def _dedupe_issues(issues: list[FormulaQualityIssue]) -> list[FormulaQualityIssue]:
    seen = set()
    deduped = []
    for issue in issues:
        key = (issue.code, issue.evidence)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped


def _issue(code: str, message: str, evidence: str | None = None) -> FormulaQualityIssue:
    return FormulaQualityIssue(code=code, severity="warning", message=message, evidence=evidence)
