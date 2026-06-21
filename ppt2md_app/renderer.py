from typing import Any, Dict, List


RENDERER_VERSION = "markdown-first-renderer-2026-06-21"


def render_page_ir_to_markdown(page_ir: Dict[str, Any], slide_no: int | None = None) -> str:
    slide = slide_no or page_ir.get("source_page") or 0
    blocks = page_ir.get("blocks") or []
    if blocks:
        return render_blocks_to_markdown(blocks, slide)
    raw_text = page_ir.get("raw_text") or ""
    return render_raw_text_fallback(raw_text, slide)


def render_page_record_to_markdown(record: Dict[str, Any], slide_no: int | None = None) -> str:
    slide = slide_no or record.get("slide_no") or record.get("page_ir", {}).get("source_page") or 0
    blocks = record.get("blocks") or record.get("page_ir", {}).get("blocks") or []
    if blocks:
        return render_blocks_to_markdown(blocks, slide)
    return render_raw_text_fallback(record.get("raw_text") or "", slide)


def render_blocks_to_markdown(blocks: List[Dict[str, Any]], slide_no: int) -> str:
    chunks = [f"# Slide {slide_no}"]
    for block in blocks:
        rendered = render_block(block)
        if rendered:
            chunks.append(rendered)
    return "\n\n".join(chunks).rstrip() + "\n"


def render_block(block: Dict[str, Any]) -> str:
    text = (block.get("text") or "").strip()
    if not text and block.get("type") != "image_ref":
        return ""

    block_type = block.get("type")
    if block_type == "heading":
        return f"## {_strip_heading_marks(text)}"
    if block_type in ("paragraph", "formula_inline", "list", "table"):
        return _strip_known_section_heading(text)
    if block_type == "formula_block":
        return _render_formula_block(text)
    if block_type == "figure_note":
        return _render_figure_note(text)
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
    if stripped.startswith("$$") and stripped.endswith("$$"):
        return stripped
    return f"$$\n{stripped}\n$$"


def _render_figure_note(text: str) -> str:
    lines = [line.strip() for line in _strip_known_section_heading(text).splitlines() if line.strip()]
    if not lines:
        return "> [!NOTE] 图示说明"
    return "> [!NOTE] 图示说明\n" + "\n".join(f"> {line}" for line in lines)


def _render_uncertain(text: str) -> str:
    stripped = _strip_known_section_heading(text)
    return "> [!WARNING] 识别不确定\n" + "\n".join(f"> {line}" for line in stripped.splitlines())


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
    ):
        lines = lines[1:]
    return "\n".join(line.strip() for line in lines).strip()
