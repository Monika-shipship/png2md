from typing import Any, Dict, List

from .provenance import provenance_comment
from .table_quality import assess_table, normalize_table_text


RENDERER_VERSION = "markdown-first-renderer-2026-06-22-fallback-evidence"


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
    chunks = [f"# Slide {slide_no}"]
    for block in blocks:
        rendered = render_block(block)
        if rendered:
            if include_provenance_comments:
                rendered = f"{provenance_comment(block)}\n{rendered}"
            chunks.append(rendered)
    return "\n\n".join(chunks).rstrip() + "\n"


def render_block(block: Dict[str, Any]) -> str:
    text = (block.get("text") or block.get("description") or "").strip()
    if not text and block.get("type") != "image_ref":
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
        return _render_formula_block(block.get("latex") or text)
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


def _render_formula_block(text: str) -> str:
    stripped = _strip_known_section_heading(text)
    if _has_uncertain_marker(stripped):
        return _render_uncertain_formula(stripped)
    if stripped.startswith("$$") and stripped.endswith("$$"):
        return stripped
    return f"$$\n{stripped}\n$$"


def _render_figure_note(block: Dict[str, Any]) -> str:
    text = block.get("description") or block.get("text") or ""
    lines = [line.strip() for line in _strip_known_section_heading(text).splitlines() if line.strip()]
    path = (block.get("path") or block.get("image_path") or "").strip()
    rendered = []
    if path:
        alt = (block.get("alt") or "figure").strip()
        rendered.append(f"![{alt}]({path})")

    if block.get("unrecognizable") or _has_uncertain_marker(text):
        body = lines or ["图示不可可靠识别。"]
        rendered.append("> [!WARNING] 图示识别不确定\n" + "\n".join(f"> {line}" for line in body))
    elif lines:
        rendered.append("> [!NOTE] 图示说明\n" + "\n".join(f"> {line}" for line in lines))
    else:
        rendered.append("> [!WARNING] 图示识别不确定\n> Figure Analysis 为空。")
    return "\n\n".join(rendered)


def _render_uncertain(text: str) -> str:
    stripped = _strip_known_section_heading(text)
    return "> [!WARNING] 识别不确定\n" + "\n".join(f"> {line}" for line in stripped.splitlines())


def _render_uncertain_formula(text: str) -> str:
    rendered = ["> [!WARNING] 公式识别不确定", "> 原始识别："]
    rendered.extend(f"> {line}" for line in text.splitlines())
    return "\n".join(rendered)


def _render_table(block: Dict[str, Any]) -> str:
    text = (block.get("text") or "").strip()
    stripped = _strip_known_section_heading(text)
    quality = assess_table(stripped)
    if quality.reliable:
        return normalize_table_text(stripped)

    issue_lines = [issue.message for issue in quality.errors + quality.warnings]
    image = _table_image_reference(block)
    rendered = ["> [!WARNING] 表格识别不确定"]
    for message in issue_lines[:3]:
        rendered.append(f"> {message}")
    if image:
        rendered.append("> 已保留表格截图引用。")
    rendered.append(">")
    rendered.append("> 原始识别：")
    rendered.extend(f"> {line}" for line in stripped.splitlines())
    warning = "\n".join(rendered)
    return f"{image}\n\n{warning}" if image else warning


def _table_image_reference(block: Dict[str, Any]) -> str:
    path = (
        block.get("table_image_path")
        or block.get("crop_path")
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
