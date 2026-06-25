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
_CODE_SPAN_RE = re.compile(r"`[^`\n]*`")
_MATH_SPAN_RE = re.compile(
    r"\$\$(?P<display>.*?)\$\$"
    r"|(?<!\\)(?<!\$)\$(?!\$)(?P<inline>.*?)(?<!\\)(?<!\$)\$(?!\$)"
    r"|\\\((?P<paren>.*?)\\\)"
    r"|\\\[(?P<bracket>.*?)\\\]",
    flags=re.DOTALL,
)

UNICODE_MATH_SYMBOLS_TO_LATEX = {
    "Α": r"A",
    "Β": r"B",
    "Γ": r"\Gamma",
    "Δ": r"\Delta",
    "Ε": r"E",
    "Ζ": r"Z",
    "Η": r"H",
    "Θ": r"\Theta",
    "Ι": r"I",
    "Κ": r"K",
    "Λ": r"\Lambda",
    "Μ": r"M",
    "Ν": r"N",
    "Ξ": r"\Xi",
    "Ο": r"O",
    "Π": r"\Pi",
    "Ρ": r"P",
    "Σ": r"\Sigma",
    "Τ": r"T",
    "Υ": r"\Upsilon",
    "Φ": r"\Phi",
    "Χ": r"X",
    "Ψ": r"\Psi",
    "Ω": r"\Omega",
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "δ": r"\delta",
    "ε": r"\epsilon",
    "ζ": r"\zeta",
    "η": r"\eta",
    "θ": r"\theta",
    "ι": r"\iota",
    "κ": r"\kappa",
    "λ": r"\lambda",
    "μ": r"\mu",
    "ν": r"\nu",
    "ξ": r"\xi",
    "ο": r"o",
    "π": r"\pi",
    "ρ": r"\rho",
    "σ": r"\sigma",
    "τ": r"\tau",
    "υ": r"\upsilon",
    "φ": r"\phi",
    "χ": r"\chi",
    "ψ": r"\psi",
    "ω": r"\omega",
    "ϕ": r"\phi",
    "ϑ": r"\theta",
    "ϵ": r"\epsilon",
    "≤": r"\leq",
    "≥": r"\geq",
    "≠": r"\neq",
    "≈": r"\approx",
    "≃": r"\simeq",
    "≅": r"\cong",
    "≡": r"\equiv",
    "∈": r"\in",
    "∉": r"\notin",
    "⊂": r"\subset",
    "⊃": r"\supset",
    "⊆": r"\subseteq",
    "⊇": r"\supseteq",
    "∪": r"\cup",
    "∩": r"\cap",
    "∅": r"\emptyset",
    "∀": r"\forall",
    "∃": r"\exists",
    "∄": r"\nexists",
    "∂": r"\partial",
    "∇": r"\nabla",
    "∞": r"\infty",
    "±": r"\pm",
    "∓": r"\mp",
    "×": r"\times",
    "÷": r"\div",
    "·": r"\cdot",
    "⋅": r"\cdot",
    "√": r"\sqrt",
    "∑": r"\sum",
    "∏": r"\prod",
    "∫": r"\int",
    "∮": r"\oint",
    "→": r"\to",
    "←": r"\leftarrow",
    "↔": r"\leftrightarrow",
    "⇒": r"\Rightarrow",
    "⇐": r"\Leftarrow",
    "⇔": r"\Leftrightarrow",
    "⊗": r"\otimes",
    "⊕": r"\oplus",
    "⊥": r"\perp",
    "∥": r"\parallel",
    "∝": r"\propto",
    "∴": r"\therefore",
    "∵": r"\because",
    "′": r"^{\prime}",
    "″": r"^{\prime\prime}",
}

UNICODE_MATH_SYMBOL_RE = re.compile("[" + re.escape("".join(UNICODE_MATH_SYMBOLS_TO_LATEX)) + "]")
_BINARY_UNICODE_MATH_OPERATORS = {
    "≤",
    "≥",
    "≠",
    "≈",
    "≃",
    "≅",
    "≡",
    "∈",
    "∉",
    "⊂",
    "⊃",
    "⊆",
    "⊇",
    "→",
    "←",
    "↔",
    "⇒",
    "⇐",
    "⇔",
}
_MATH_ATOM_RE = r"(?:[A-Za-z0-9_{}^\\]+|[" + re.escape("".join(UNICODE_MATH_SYMBOLS_TO_LATEX)) + r"])"
_MATH_CHAIN_TERM_RE = r"(?:[A-Za-z0-9_{}^\\]+|\?)"
_UNICODE_MATH_CHAIN_RE = re.compile(
    r"(?<![A-Za-z0-9_\\$])"
    r"(?P<expr>"
    + _MATH_CHAIN_TERM_RE
    + r"(?:\s*[" + re.escape("".join(_BINARY_UNICODE_MATH_OPERATORS)) + r"]\s*" + _MATH_CHAIN_TERM_RE + r"){2,}"
    r")"
    r"(?![A-Za-z0-9_\\$])"
)
_COMPACT_BINARY_UNICODE_MATH_RE = re.compile(
    r"(?<![A-Za-z0-9_\\$])"
    r"(?P<left>" + _MATH_ATOM_RE + r")"
    r"\s*(?P<op>[" + re.escape("".join(_BINARY_UNICODE_MATH_OPERATORS)) + r"])\s*"
    r"(?P<right>" + _MATH_ATOM_RE + r")"
    r"(?![A-Za-z0-9_\\$])"
)
_SINGLE_UNICODE_MATH_SYMBOL_RE = re.compile(
    r"(?<![A-Za-z0-9_\\$])"
    r"(?P<symbol>[" + re.escape("".join(UNICODE_MATH_SYMBOLS_TO_LATEX)) + r"])"
    r"(?![A-Za-z0-9_\\$])"
)
_NATURAL_LANGUAGE_FRAGMENT_RE = re.compile(
    r"\b(?:and|or|possible|typo|might|could|would|should|maybe|text|figure|label|arrow)\b",
    flags=re.IGNORECASE,
)
_INLINE_MATHISH_FRAGMENT_RE = re.compile(
    r"(?<![A-Za-z\\])"
    r"(?P<expr>[A-Za-z0-9_{}^()\\+\-*/=<>|, \t"
    + re.escape("".join(UNICODE_MATH_SYMBOLS_TO_LATEX))
    + r"]{0,80}"
    + r"["
    + re.escape("".join(UNICODE_MATH_SYMBOLS_TO_LATEX))
    + r"]"
    + r"[A-Za-z0-9_{}^()\\+\-*/=<>|, \t"
    + re.escape("".join(UNICODE_MATH_SYMBOLS_TO_LATEX))
    + r"]{0,80})"
)


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
    stripped = normalize_unicode_math_symbols(stripped)
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


def normalize_unicode_math_symbols(text: str) -> str:
    if not text:
        return ""
    if not contains_unicode_math_symbols(text):
        return text
    normalized = UNICODE_MATH_SYMBOL_RE.sub(lambda match: _latex_symbol_replacement(match.group(0)), text)
    normalized = _format_basic_latex_operators(normalized)
    return _cleanup_latex_symbol_spacing(normalized)


def contains_unicode_math_symbols(text: str) -> bool:
    return bool(UNICODE_MATH_SYMBOL_RE.search(text or ""))


def unicode_math_symbols_in_text(text: str) -> list[str]:
    seen = []
    for match in UNICODE_MATH_SYMBOL_RE.finditer(text or ""):
        symbol = match.group(0)
        if symbol not in seen:
            seen.append(symbol)
    return seen


def normalize_inline_math_text(text: str) -> str:
    """Normalize obvious inline math while leaving code spans/fences untouched."""
    if not text:
        return ""
    return normalize_markdown_formula_blocks(text)


def strip_math_and_code_regions(text: str) -> str:
    if not text:
        return ""
    without_fences = _CODE_FENCE_RE.sub("", text)
    without_code = _CODE_SPAN_RE.sub("", without_fences)
    return _MATH_SPAN_RE.sub("", without_code)


def normalize_text_for_math_coverage(text: str) -> str:
    normalized = normalize_unicode_math_symbols(text or "")
    return normalized.replace("\\", "")


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
            split = _split_multi_tag_alignment_body(body)
            if split:
                return "\n\n".join(
                    _render_tagged_aligned_part(part_body, tag.group(0).strip(), output_env, args)
                    for part_body, tag in split
                )
            if output_env == env:
                return match.group(0)

        if not moved_tag and output_env == env:
            return match.group(0)
        normalized_body = _clean_alignment_body(normalized_body)
        rendered = f"\\begin{{{output_env}}}{args}{normalized_body}\\end{{{output_env}}}"
        return f"{rendered}\n{moved_tag}" if moved_tag else rendered

    return _ALIGNMENT_ENV_RE.sub(replace, text)


def _split_multi_tag_alignment_body(body: str) -> list[tuple[str, re.Match]]:
    matches = list(_TAG_RE.finditer(body))
    if len(matches) <= 1:
        return []

    parts = []
    previous_end = 0
    for index, tag in enumerate(matches):
        segment = body[previous_end : tag.start()]
        segment = re.sub(r"^\s*(?:\\\\\s*)?&?\s*", "", segment)
        segment = re.sub(r"\s*\\\\\s*$", "", segment, flags=re.DOTALL)
        segment = segment.strip()
        if not segment:
            return []
        parts.append((segment, tag))
        previous_end = tag.end()

    trailing = body[previous_end:].strip()
    if trailing and re.sub(r"\\\\", "", trailing).strip():
        return []
    return parts


def _render_tagged_aligned_part(body: str, tag: str, output_env: str, args: str) -> str:
    cleaned = _clean_alignment_body(f"\n{body}\n")
    return f"\\begin{{{output_env}}}{args}{cleaned}\\end{{{output_env}}}\n{tag}"


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
    text = _DISPLAY_MATH_RE.sub(lambda match: _normalize_display_match(match), text)
    return _normalize_inline_math_segment(text)


def _normalize_display_match(match: re.Match) -> str:
    original = match.group(1)
    normalized = normalize_formula_text(original)
    if normalized == original.strip():
        return match.group(0)
    return _format_display_math(normalized)


def _normalize_inline_math_segment(text: str) -> str:
    if not text:
        return ""
    pieces = _CODE_SPAN_RE.split(text)
    code_spans = _CODE_SPAN_RE.findall(text)
    rendered = []
    for index, piece in enumerate(pieces):
        rendered.append(_normalize_inline_math_piece(piece))
        if index < len(code_spans):
            rendered.append(code_spans[index])
    return "".join(rendered)


def _normalize_inline_math_piece(text: str) -> str:
    normalized_math = _MATH_SPAN_RE.sub(_normalize_math_delimited_match, text)
    return _wrap_bare_unicode_math_fragments(normalized_math)


def _normalize_math_delimited_match(match: re.Match) -> str:
    if match.group("display") is not None:
        return match.group(0)
    if match.group("inline") is not None:
        return f"${normalize_formula_text(match.group('inline'))}$"
    if match.group("paren") is not None:
        return f"\\({normalize_formula_text(match.group('paren'))}\\)"
    return _format_display_math(normalize_formula_text(match.group("bracket") or ""))


def _wrap_bare_unicode_math_fragments(text: str) -> str:
    if not contains_unicode_math_symbols(text):
        return text
    text = _wrap_unicode_math_chains(text)
    if not contains_unicode_math_symbols(text):
        return text
    text = _wrap_compact_binary_unicode_math_fragments(text)
    if not contains_unicode_math_symbols(text):
        return text

    def replace(match: re.Match) -> str:
        expr = match.group("expr")
        if not _looks_like_bare_math_fragment(expr):
            return expr
        leading = expr[: len(expr) - len(expr.lstrip())]
        trailing = expr[len(expr.rstrip()) :]
        core = expr.strip()
        return f"{leading}${normalize_unicode_math_symbols(core).strip()}${trailing}"

    text = _INLINE_MATHISH_FRAGMENT_RE.sub(replace, text)
    if not contains_unicode_math_symbols(text):
        return text
    return _wrap_single_unicode_math_symbols(text)


def _wrap_unicode_math_chains(text: str) -> str:
    def replace(match: re.Match) -> str:
        return f"${_normalize_unicode_operator_chain(match.group('expr'))}$"

    return _UNICODE_MATH_CHAIN_RE.sub(replace, text)


def _wrap_compact_binary_unicode_math_fragments(text: str) -> str:
    def replace(match: re.Match) -> str:
        left = normalize_unicode_math_symbols(match.group("left")).strip()
        operator = UNICODE_MATH_SYMBOLS_TO_LATEX.get(match.group("op"), match.group("op")).strip()
        right = normalize_unicode_math_symbols(match.group("right")).strip()
        return f"${left} {operator} {right}$"

    return _COMPACT_BINARY_UNICODE_MATH_RE.sub(replace, text)


def _normalize_unicode_operator_chain(expr: str) -> str:
    parts = re.split(r"([" + re.escape("".join(_BINARY_UNICODE_MATH_OPERATORS)) + r"])", expr)
    rendered: list[str] = []
    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        if stripped in UNICODE_MATH_SYMBOLS_TO_LATEX:
            rendered.append(UNICODE_MATH_SYMBOLS_TO_LATEX[stripped])
        else:
            rendered.append(normalize_unicode_math_symbols(stripped).strip())
    return " ".join(rendered)


def _wrap_single_unicode_math_symbols(text: str) -> str:
    def replace(match: re.Match) -> str:
        symbol = match.group("symbol")
        return f"${normalize_unicode_math_symbols(symbol).strip()}$"

    return _SINGLE_UNICODE_MATH_SYMBOL_RE.sub(replace, text)


def _looks_like_bare_math_fragment(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped or not contains_unicode_math_symbols(stripped):
        return False
    if len(stripped) > 96:
        return False
    if re.search(r"[\u4e00-\u9fff]", stripped):
        return False
    if _NATURAL_LANGUAGE_FRAGMENT_RE.search(stripped):
        return False
    return bool(
        re.search(r"[=+\-*/^_{}()<>|]", stripped)
        or len(UNICODE_MATH_SYMBOL_RE.findall(stripped)) >= 2
        or re.fullmatch(r"[A-Za-z0-9_{}^()\\+\-*/=<>|, \t" + re.escape("".join(UNICODE_MATH_SYMBOLS_TO_LATEX)) + r"]+", stripped)
    )


def _latex_symbol_replacement(symbol: str) -> str:
    latex = UNICODE_MATH_SYMBOLS_TO_LATEX.get(symbol, symbol)
    if not latex.startswith("\\"):
        return latex
    return f"{latex} "


def _cleanup_latex_symbol_spacing(text: str) -> str:
    cleaned = re.sub(r"(\\[A-Za-z]+)\s+([_^{}.,;:，。；：)\]])", r"\1\2", text)
    cleaned = re.sub(r"(\\[A-Za-z]+)\s+([+\-*/=<>|])", r"\1 \2", cleaned)
    return cleaned


def _format_basic_latex_operators(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"(?<![&])\s*\+\s*", " + ", text)
    text = re.sub(r"(?<![&])\s*=\s*", " = ", text)
    return text.strip()


def format_display_math(latex: str) -> str:
    return "\n\n".join(f"$$\n{part}\n$$" for part in _display_math_parts(latex))


def _format_display_math(latex: str) -> str:
    return format_display_math(latex)


def _display_math_parts(latex: str) -> list[str]:
    stripped = (latex or "").strip()
    parts = [part.strip() for part in re.split(r"\n\s*\n", stripped) if part.strip()]
    if len(parts) > 1 and all(_TAG_RE.search(part) for part in parts):
        return parts
    return [stripped]


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
