import re
from typing import Any, Dict, List

from .provenance import provenance_comment, renderer_template_block
from .formula_quality import format_display_math
from .table_quality import assess_table, normalize_table_text


RENDERER_VERSION = "markdown-first-renderer-2026-06-22-handwritten-quality"


def render_page_ir_to_markdown(
    page_ir: Dict[str, Any],
    slide_no: int | None = None,
    *,
    include_provenance_comments: bool = False,
) -> str:
    slide = slide_no or page_ir.get("source_page") or 0
    blocks = page_ir.get("blocks") or []
    if blocks:
        return render_blocks_to_markdown(blocks, slide, include_provenance_comments=include_provenance_comments)
    raw_text = page_ir.get("raw_text") or ""
    return render_raw_text_fallback(raw_text, slide)


def render_page_record_to_markdown(
    record: Dict[str, Any],
    slide_no: int | None = None,
    *,
    include_provenance_comments: bool = False,
) -> str:
    slide = slide_no or record.get("slide_no") or record.get("page_ir", {}).get("source_page") or 0
    blocks = record.get("blocks") or record.get("page_ir", {}).get("blocks") or []
    if blocks:
        return render_blocks_to_markdown(blocks, slide, include_provenance_comments=include_provenance_comments)
    return render_raw_text_fallback(record.get("raw_text") or "", slide)


def render_blocks_to_markdown(
    blocks: List[Dict[str, Any]],
    slide_no: int,
    *,
    include_provenance_comments: bool = False,
) -> str:
    heading = f"# Slide {slide_no}"
    if include_provenance_comments:
        heading = f"{provenance_comment(renderer_template_block(slide_no))}\n{heading}"
    chunks = [heading]
    skip_indexes = set()
    for index, block in enumerate(blocks):
        if index in skip_indexes:
            continue
        next_block = blocks[index + 1] if index + 1 < len(blocks) else None
        if _is_table_caption_block(block) and _is_reliable_table_block(next_block):
            rendered = _render_table_with_caption(block, next_block)
            skip_indexes.add(index + 1)
            if include_provenance_comments:
                rendered = f"{provenance_comment(block)}\n{provenance_comment(next_block)}\n{rendered}"
            chunks.append(rendered)
            continue
        rendered = render_block(block)
        if rendered:
            if include_provenance_comments:
                rendered = f"{provenance_comment(block)}\n{rendered}"
            chunks.append(rendered)
    return "\n\n".join(chunks).rstrip() + "\n"


def render_block(block: Dict[str, Any]) -> str:
    text = (block.get("text") or block.get("description") or "").strip()
    if not text and block.get("type") not in {"image_ref", "figure_note", "table"}:
        return ""

    rendered = _render_block_body(block, text)
    if block.get("semantic_role") and block.get("semantic_role_source") == "section":
        label = (block.get("semantic_role_label") or block.get("semantic_role") or "段落").strip()
        return f"**{label}：**\n\n{rendered}" if rendered else f"**{label}：**"
    return rendered


def _render_block_body(block: Dict[str, Any], text: str) -> str:
    block_type = block.get("type")
    if block_type == "heading":
        return f"## {_strip_heading_marks(text)}"
    if block_type in ("paragraph", "formula_inline", "list"):
        return _strip_known_section_heading(text)
    if block_type == "table":
        return _render_table(block)
    if block_type == "formula_block":
        return _render_formula_block(block, text)
    if block_type == "figure_note":
        return _render_figure_note(block)
    if block_type == "image_ref":
        return _render_image_ref(block)
    if block_type == "uncertain":
        return _render_uncertain(text)
    return text


def render_raw_text_fallback(raw_text: str, slide_no: int) -> str:
    text = (raw_text or "").strip()
    if not text:
        return f"# Slide {slide_no}\n"
    return f"# Slide {slide_no}\n\n{text}\n"


def _strip_heading_marks(text: str) -> str:
    stripped = text.strip()
    while stripped.startswith("#"):
        stripped = stripped[1:].lstrip()
    return stripped.rstrip(":").strip()


def _render_formula_block(block: Dict[str, Any], text: str) -> str:
    stripped = _strip_known_section_heading(block.get("latex") or text)
    quality = block.get("formula_quality")
    warnings = quality.get("warnings") if isinstance(quality, dict) else block.get("warnings")
    if _has_uncertain_marker(stripped) or _has_blocking_formula_warning(warnings):
        raw = block.get("raw_text") or block.get("text") or stripped
        return _render_uncertain_formula(block, raw, warnings if isinstance(warnings, list) else [])
    if stripped.startswith("$$") and stripped.endswith("$$"):
        return stripped
    return format_display_math(stripped)


def _render_figure_note(block: Dict[str, Any]) -> str:
    text = block.get("description") or block.get("text") or ""
    lines = [line.strip() for line in _strip_known_section_heading(text).splitlines() if line.strip()]
    figure = block.get("figure") if isinstance(block.get("figure"), dict) else {}
    labels = block.get("labels") or figure.get("labels") or []
    relations = block.get("relations") or figure.get("relations") or []
    path = (
        block.get("path")
        or block.get("image_path")
        or block.get("crop_ref")
        or block.get("image_ref")
        or ""
    ).strip()
    rendered = []
    if path:
        alt = (block.get("alt") or "figure").strip()
        rendered.append(f"![{alt}]({path})")

    detail_lines = lines[:]
    if not detail_lines and labels:
        detail_lines.append("可见标签：" + "，".join(str(label) for label in labels[:12]))
    if not detail_lines and relations:
        detail_lines.append("关系：" + "；".join(str(relation) for relation in relations[:6]))

    if block.get("unrecognizable") or figure.get("unrecognizable") or _has_figure_uncertain_marker(text):
        body = lines or ["图示不可可靠识别。"]
        rendered.extend(body)
    elif detail_lines:
        rendered.append("> [!NOTE] 图示说明\n" + "\n".join(f"> {line}" for line in detail_lines))
    else:
        rendered.append("图示说明缺失。")
    return "\n\n".join(rendered)


def _render_uncertain(text: str) -> str:
    return _strip_known_section_heading(text)


def _render_uncertain_formula(block: Dict[str, Any], text: str, warnings: list | None = None) -> str:
    image = _formula_image_reference(block)
    body = (text or "").strip()
    return f"{image}\n\n{body}" if image else body


def _formula_image_reference(block: Dict[str, Any]) -> str:
    path = (
        block.get("formula_image_path")
        or block.get("crop_path")
        or block.get("crop_ref")
        or block.get("image_ref")
        or block.get("image_path")
        or block.get("page_image_ref")
        or ""
    )
    path = str(path).strip()
    if not path:
        return ""
    alt = str(block.get("alt") or "formula").strip()
    return f"![{alt}]({path})"


def _has_blocking_formula_warning(warnings) -> bool:
    blocking_codes = {
        "formula_empty",
        "formula_uncertain_marker",
        "formula_truncated",
        "formula_isolated_operator",
        "formula_reasoning_without_latex",
        "formula_brace_unbalanced",
        "latex_left_right_unbalanced",
        "latex_frac_missing_braces",
    }
    for warning in warnings or []:
        if isinstance(warning, dict) and warning.get("code") in blocking_codes:
            return True
    return False


def _render_table(block: Dict[str, Any]) -> str:
    text = (block.get("text") or "").strip()
    stripped = _strip_known_section_heading(text)
    quality = assess_table(stripped)
    table_format = str(block.get("table_format") or quality.table_format)
    if table_format == "image_only":
        image = _table_image_reference(block)
        return image
    if quality.reliable:
        return normalize_table_text(stripped)

    image = _table_image_reference(block)
    raw = _fenced_plain_text(stripped) if stripped else ""
    body = raw or stripped
    return f"{image}\n\n{body}" if image else body


def _is_table_caption_block(block: Dict[str, Any] | None) -> bool:
    if not isinstance(block, dict) or block.get("type") != "table":
        return False
    text = _strip_known_section_heading(block.get("text") or "")
    if not text or assess_table(text).reliable:
        return False
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return bool(lines) and not any("|" in line for line in lines)


def _is_reliable_table_block(block: Dict[str, Any] | None) -> bool:
    if not isinstance(block, dict) or block.get("type") != "table":
        return False
    text = _strip_known_section_heading(block.get("text") or "")
    return assess_table(text).reliable


def _render_table_with_caption(caption_block: Dict[str, Any], table_block: Dict[str, Any]) -> str:
    caption = _table_caption_text(caption_block)
    table = _render_table(table_block)
    return f"{caption}\n\n{table}" if caption else table


def _table_caption_text(block: Dict[str, Any]) -> str:
    text = _strip_known_section_heading(block.get("text") or "")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    title = None
    details = []
    for line in lines:
        stripped = re.sub(r"^[-*+]\s+", "", line).strip()
        if re.match(r"^\*\*?数据内容\*\*?[：:]\s*$", stripped) or stripped in {"数据内容：", "数据内容:"}:
            continue
        if title is None:
            title = _extract_table_title(stripped) or stripped
            continue
        details.append(f"- {stripped}")
    rendered = []
    if title:
        rendered.append(f"**{title.rstrip('。.：:')}**")
    rendered.extend(details)
    return "\n".join(rendered)


def _extract_table_title(text: str) -> str | None:
    match = re.search(r"展示了群\s*(?P<title>\$[^$]+\$|[^，。,；;]+)", text)
    if match:
        title = match.group("title").strip()
        suffix = " 特征标表" if "特征标" in text else ""
        return f"{title}{suffix}".strip()
    return None


def _table_image_reference(block: Dict[str, Any]) -> str:
    path = (
        block.get("table_image_path")
        or block.get("crop_path")
        or block.get("crop_ref")
        or block.get("image_ref")
        or block.get("image_path")
        or block.get("path")
        or ""
    )
    path = str(path).strip()
    if not path:
        return ""
    alt = str(block.get("alt") or "table").strip()
    return f"![{alt}]({path})"


def _render_image_ref(block: Dict[str, Any]) -> str:
    path = (block.get("path") or block.get("image_path") or "").strip()
    alt = (block.get("alt") or "image").strip()
    if not path:
        return _render_uncertain(block.get("text") or "图片引用缺少路径。")
    caption = (block.get("caption") or "").strip()
    image = f"![{alt}]({path})"
    return f"{image}\n\n{caption}" if caption else image


def _fenced_plain_text(text: str) -> str:
    fence = "```"
    while fence in text:
        fence += "`"
    return f"{fence}text\n{text}\n{fence}"


def _strip_known_section_heading(text: str) -> str:
    lines = text.strip().splitlines()
    if not lines:
        return ""
    first = lines[0].strip().lower()
    if (
        first.startswith("### ocr text")
        or first.startswith("### ocr")
        or first.startswith("### 正文")
        or first.startswith("### formula")
        or first.startswith("### 公式")
        or first.startswith("### figure analysis")
        or first.startswith("### table analysis")
        or first.startswith("### 表格")
        or first.startswith("### uncertain")
        or first.startswith("### illegible")
        or first.startswith("### 不确定")
        or first.startswith("### proof")
        or first.startswith("### example")
        or first.startswith("### exercise")
        or first.startswith("### problem")
        or first.startswith("### solution")
        or first.startswith("### answer")
        or first.startswith("### definition")
        or first.startswith("### theorem")
        or first.startswith("### lemma")
        or first.startswith("### corollary")
        or first.startswith("### proposition")
        or first.startswith("### remark")
        or first.startswith("### note")
        or first.startswith("### observation")
        or first.startswith("### 证明")
        or first.startswith("### 例")
        or first.startswith("### 练习")
        or first.startswith("### 习题")
        or first.startswith("### 解")
        or first.startswith("### 定义")
        or first.startswith("### 定理")
        or first.startswith("### 引理")
        or first.startswith("### 推论")
        or first.startswith("### 命题")
        or first.startswith("### 备注")
        or first.startswith("### 注")
    ):
        lines = lines[1:]
    return "\n".join(line.strip() for line in lines).strip()


def _has_uncertain_marker(text: str) -> bool:
    lower = text.lower()
    return (
        "[?]" in text
        or "？" in text
        or "无法确定" in text
        or "看不清" in text
        or "不确定" in text
        or "uncertain" in lower
        or "illegible" in lower
    )


def _has_figure_uncertain_marker(text: str) -> bool:
    kept = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if (
            ("正文关联" in stripped or "关联" in stripped)
            and ("不确定" in stripped or "无法确定" in stripped or "无明确关联" in stripped)
        ):
            continue
        kept.append(stripped)
    return _has_uncertain_marker("\n".join(kept))
