from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


PAGE_RANGE_RE = re.compile(r"^\d+(-\d+)?(,\d+(-\d+)?)*$")

IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".jp2", ".webp", ".gif", ".bmp"}
HTML_SUFFIXES = {".html", ".htm"}

MINERU_SINGLE_REQUEST_PAGE_LIMIT = 200
PADDLEOCR_LOCAL_FILE_LIMIT_BYTES = 50 * 1024 * 1024
PADDLEOCR_URL_FILE_LIMIT_BYTES = 200 * 1024 * 1024
PADDLEOCR_DAILY_PAGE_LIMIT_PER_MODEL = 3000
PADDLEOCR_RECOMMENDED_CHUNK_PAGES = 100


@dataclass(frozen=True)
class PageChunk:
    index: int
    page_ranges: str
    page_count: int
    first_page: int
    last_page: int


def count_page_ranges(page_ranges: str, total_pages: int | None = None) -> int | None:
    pages = parse_page_selection(page_ranges, total_pages=total_pages)
    if pages is None:
        return None
    if not page_ranges.strip():
        return total_pages
    return len(pages)


def parse_page_selection(page_ranges: str, *, total_pages: int | None = None) -> list[int] | None:
    text = page_ranges.strip().replace(" ", "")
    if not text:
        if total_pages is None:
            return []
        return list(range(1, total_pages + 1))
    if not PAGE_RANGE_RE.match(text):
        return None
    selected: set[int] = set()
    for part in text.split(","):
        if "-" in part:
            start_text, end_text = part.split("-", 1)
            start = int(start_text)
            end = int(end_text)
        else:
            start = end = int(part)
        if end < start:
            return None
        if total_pages is not None:
            end = min(end, total_pages)
        selected.update(range(start, end + 1))
    if total_pages is not None:
        selected = {page for page in selected if 1 <= page <= total_pages}
    return sorted(selected)


def compact_pages_to_ranges(pages: list[int]) -> str:
    if not pages:
        return ""
    sorted_pages = sorted(set(pages))
    ranges: list[str] = []
    start = prev = sorted_pages[0]
    for page in sorted_pages[1:]:
        if page == prev + 1:
            prev = page
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = page
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(ranges)


def build_page_chunks(
    total_pages: int,
    page_ranges: str = "",
    *,
    chunk_size: int = MINERU_SINGLE_REQUEST_PAGE_LIMIT,
) -> list[PageChunk]:
    if total_pages < 1:
        return []
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive.")
    selected = parse_page_selection(page_ranges, total_pages=total_pages)
    if selected is None:
        raise ValueError("页码范围格式应类似 1-10 或 2,4-6。")
    if not selected:
        selected = list(range(1, total_pages + 1))
    chunks: list[PageChunk] = []
    for offset in range(0, len(selected), chunk_size):
        chunk_pages = selected[offset : offset + chunk_size]
        chunk_range = compact_pages_to_ranges(chunk_pages)
        if len(chunk_pages) == 1:
            chunk_range = f"{chunk_pages[0]}-{chunk_pages[0]}"
        chunks.append(
            PageChunk(
                index=len(chunks) + 1,
                page_ranges=chunk_range,
                page_count=len(chunk_pages),
                first_page=chunk_pages[0],
                last_page=chunk_pages[-1],
            )
        )
    return chunks


def estimate_pdf_pages(path: Path) -> int | None:
    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(path))
        return len(reader.pages) or None
    except Exception:
        pass
    try:
        data = path.read_bytes()
    except OSError:
        return None
    count = len(re.findall(rb"/Type\s*/Page(?!s)\b", data))
    return count or None


def estimate_path_pages(path: Path, page_ranges: str = "") -> int | None:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        pages = estimate_pdf_pages(path)
        return count_page_ranges(page_ranges, pages) if pages else None
    if suffix in IMAGE_SUFFIXES:
        return 1
    return None


def format_file_size(size_bytes: int | None) -> str:
    if size_bytes is None:
        return "未知"
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{value:.1f} GB"


def infer_mineru_model_version(paths: list[Path], selected: str) -> str:
    suffixes = {path.suffix.lower() for path in paths}
    if suffixes and suffixes <= HTML_SUFFIXES:
        return "MinerU-HTML"
    return selected or "vlm"


def validate_mineru_model_version_for_paths(paths: list[Path], model_version: str) -> None:
    suffixes = {path.suffix.lower() for path in paths}
    if not suffixes:
        return
    has_html = bool(suffixes & HTML_SUFFIXES)
    has_non_html = bool(suffixes - HTML_SUFFIXES)
    if has_html and has_non_html:
        raise ValueError("HTML/HTM 文件必须单独运行，因为 MinerU-HTML 不能和 PDF/Office/图片混在同一批。")
    if has_html and model_version != "MinerU-HTML":
        raise ValueError("HTML/HTM 输入必须使用 MinerU-HTML。")
    if has_non_html and model_version == "MinerU-HTML":
        raise ValueError("MinerU-HTML 只适合 HTML/HTM；PDF、Office、图片请使用 vlm 或 pipeline。")
