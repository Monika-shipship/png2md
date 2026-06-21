import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Literal


Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class TableQualityIssue:
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
class TableQualityResult:
    reliable: bool
    table_format: str
    row_count: int
    column_counts: list[int]
    errors: list[TableQualityIssue]
    warnings: list[TableQualityIssue]
    normalized_markdown: str | None = None

    def to_dict(self):
        return {
            "reliable": self.reliable,
            "table_format": self.table_format,
            "row_count": self.row_count,
            "column_counts": self.column_counts,
            "errors": [issue.to_dict() for issue in self.errors],
            "warnings": [issue.to_dict() for issue in self.warnings],
            "normalized_markdown": self.normalized_markdown,
        }


def assess_table(text: str) -> TableQualityResult:
    stripped = (text or "").strip()
    if _looks_like_html_table(stripped):
        return _assess_html_table(stripped)
    if is_probably_markdown_table(stripped):
        return assess_table_markdown(stripped)
    if is_probably_aligned_text_table(stripped):
        return _assess_aligned_text_table(stripped)
    return _unrecognized_table_result(stripped)


def normalize_table_text(text: str) -> str:
    result = assess_table(text)
    return result.normalized_markdown or (text or "").strip()


def assess_table_markdown(text: str) -> TableQualityResult:
    rows = _table_rows(text)
    errors: list[TableQualityIssue] = []
    warnings: list[TableQualityIssue] = []
    if not rows:
        errors.append(_issue("table_empty", "error", "表格 block 没有可解析的行。"))
        return TableQualityResult(False, "markdown", 0, [], errors, warnings)

    cells = [_split_cells(row) for row in rows]
    column_counts = [len(row_cells) for row_cells in cells]
    separator_index = _separator_row_index(cells)

    if separator_index is None:
        errors.append(_issue("table_separator_missing", "error", "Markdown 表格缺少分隔行。", rows[0]))
    elif separator_index != 1:
        warnings.append(_issue("table_separator_position", "warning", "Markdown 表格分隔行不在表头之后。", rows[separator_index]))

    expected_columns = column_counts[0] if column_counts else 0
    if expected_columns < 2:
        errors.append(_issue("table_too_few_columns", "error", "表格列数少于 2，无法可靠确认行列关系。", rows[0]))

    if any(count != expected_columns for count in column_counts):
        errors.append(
            _issue(
                "table_column_mismatch",
                "error",
                "Markdown 表格行列数不一致。",
                ", ".join(str(count) for count in column_counts),
            )
        )

    if separator_index is not None:
        body_rows = cells[separator_index + 1 :]
        if not body_rows:
            warnings.append(_issue("table_shell", "warning", "表格只有表头和分隔行，没有数据行。"))
        if _header_missing(cells[0]):
            warnings.append(_issue("table_header_missing", "warning", "表格表头为空或缺失。", rows[0]))
        if _mostly_empty_body(body_rows):
            warnings.append(_issue("table_body_empty", "warning", "表格主体大多为空。"))

    garbled_ratio = _garbled_ratio(rows)
    if garbled_ratio >= 0.25:
        warnings.append(
            _issue(
                "table_garbled_text",
                "warning",
                "表格疑似包含较多乱码或不确定字符。",
                f"garbled_ratio={garbled_ratio:.2f}",
            )
        )

    reliable = not errors and not any(
        issue.code in {"table_shell", "table_body_empty", "table_garbled_text"} for issue in warnings
    )
    return TableQualityResult(reliable, "markdown", len(rows), column_counts, errors, warnings, "\n".join(rows) if reliable else None)


def is_probably_markdown_table(text: str) -> bool:
    rows = _table_rows(text)
    return len(rows) >= 2 and any(_is_separator_cells(_split_cells(row)) for row in rows)


def is_probably_aligned_text_table(text: str) -> bool:
    rows = _aligned_text_rows(text)
    if len(rows) < 2:
        return False
    return all(len(row) >= 2 for row in rows)


def _assess_aligned_text_table(text: str) -> TableQualityResult:
    rows = _aligned_text_rows(text)
    errors: list[TableQualityIssue] = []
    warnings: list[TableQualityIssue] = []
    if not rows:
        errors.append(_issue("table_empty", "error", "文本对齐表格没有可解析的行。"))
        return TableQualityResult(False, "aligned_text", 0, [], errors, warnings)

    column_counts = [len(row) for row in rows]
    expected_columns = column_counts[0]
    if expected_columns < 2:
        errors.append(_issue("table_too_few_columns", "error", "表格列数少于 2，无法可靠确认行列关系。"))
    if any(count != expected_columns for count in column_counts):
        errors.append(
            _issue(
                "table_column_mismatch",
                "error",
                "文本对齐表格行列数不一致。",
                ", ".join(str(count) for count in column_counts),
            )
        )
    if _header_missing(rows[0]):
        warnings.append(_issue("table_header_missing", "warning", "文本对齐表格表头为空或缺失。"))
    if len(rows) == 1:
        warnings.append(_issue("table_shell", "warning", "表格只有表头，没有数据行。"))
    garbled_ratio = _garbled_ratio(["|".join(row) for row in rows])
    if garbled_ratio >= 0.25:
        warnings.append(
            _issue(
                "table_garbled_text",
                "warning",
                "文本对齐表格疑似包含较多乱码或不确定字符。",
                f"garbled_ratio={garbled_ratio:.2f}",
            )
        )

    reliable = not errors and not any(issue.code in {"table_shell", "table_garbled_text"} for issue in warnings)
    return TableQualityResult(
        reliable,
        "aligned_text",
        len(rows),
        column_counts,
        errors,
        warnings,
        _aligned_rows_to_markdown(rows) if reliable else None,
    )


def _assess_html_table(text: str) -> TableQualityResult:
    errors: list[TableQualityIssue] = []
    warnings: list[TableQualityIssue] = []
    parsed = _parse_html_table(text)
    rows = parsed["rows"]
    if not rows:
        errors.append(_issue("html_table_no_rows", "error", "HTML table 没有 tr 行。"))
        return TableQualityResult(False, "html", 0, [], errors, warnings)

    column_counts = [len(row) for row in rows]
    if any(count == 0 for count in column_counts):
        errors.append(_issue("html_table_empty_row", "error", "HTML table 存在空行。"))
    if len(set(column_counts)) > 1:
        warnings.append(_issue("html_table_ragged", "warning", "HTML table 行列数不一致，可能包含 rowspan/colspan 或复杂结构。"))
    if parsed["complex"]:
        warnings.append(_issue("html_table_complex_span", "warning", "HTML table 包含 rowspan/colspan，保留原始 HTML 以避免错误拍平。"))
    if not re.search(r"</table>", text, flags=re.IGNORECASE):
        errors.append(_issue("html_table_unclosed", "error", "HTML table 缺少结束标签。"))

    reliable = not errors
    normalized = _aligned_rows_to_markdown(rows) if reliable and not parsed["complex"] and len(set(column_counts)) == 1 else text.strip()
    return TableQualityResult(reliable, "html", len(rows), column_counts, errors, warnings, normalized if reliable else None)


def _unrecognized_table_result(text: str) -> TableQualityResult:
    errors = [_issue("table_unrecognized_format", "error", "表格 block 不是可靠的 Markdown、HTML 或文本对齐表格。", text[:120])]
    return TableQualityResult(False, "unknown", 0, [], errors, [])


def _table_rows(text: str) -> list[str]:
    rows = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):
            continue
        if "|" in stripped:
            rows.append(stripped)
    return rows


def _aligned_text_rows(text: str) -> list[list[str]]:
    rows = []
    for line in (text or "").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(">"):
            continue
        if "|" in stripped or "<table" in stripped.lower():
            return []
        cells = [cell.strip() for cell in re.split(r"\s{2,}|\t+", stripped) if cell.strip()]
        if len(cells) >= 2:
            rows.append(cells)
    return rows


def _aligned_rows_to_markdown(rows: list[list[str]]) -> str:
    header = rows[0]
    separator = ["---"] * len(header)
    rendered = [_markdown_row(header), _markdown_row(separator)]
    rendered.extend(_markdown_row(row) for row in rows[1:])
    return "\n".join(rendered)


def _markdown_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _looks_like_html_table(text: str) -> bool:
    return bool(re.search(r"<table\b", text or "", flags=re.IGNORECASE))


class _SimpleTableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None
        self._in_table = False
        self._complex = False

    @property
    def complex(self) -> bool:
        return self._complex

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        if tag == "table":
            self._in_table = True
            return
        if not self._in_table:
            return
        if tag == "tr":
            self._current_row = []
        elif tag in {"td", "th"} and self._current_row is not None:
            attr_names = {name.lower() for name, _ in attrs}
            if attr_names & {"rowspan", "colspan"}:
                self._complex = True
            self._current_cell = []
        elif tag == "br" and self._current_cell is not None:
            self._current_cell.append(" ")

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag in {"td", "th"} and self._current_row is not None and self._current_cell is not None:
            self._current_row.append(_normalize_cell_text("".join(self._current_cell)))
            self._current_cell = None
        elif tag == "tr" and self._current_row is not None:
            self.rows.append(self._current_row)
            self._current_row = None
        elif tag == "table":
            self._in_table = False

    def handle_data(self, data: str):
        if self._current_cell is not None:
            self._current_cell.append(data)


def _parse_html_table(text: str) -> dict:
    parser = _SimpleTableParser()
    parser.feed(text or "")
    return {
        "rows": [[cell for cell in row] for row in parser.rows],
        "complex": parser.complex,
    }


def _normalize_cell_text(text: str) -> str:
    return re.sub(r"\s+", " ", unescape(text or "")).strip()


def _split_cells(row: str) -> list[str]:
    stripped = row.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def _separator_row_index(rows: list[list[str]]) -> int | None:
    for index, row in enumerate(rows):
        if _is_separator_cells(row):
            return index
    return None


def _is_separator_cells(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells)


def _header_missing(cells: list[str]) -> bool:
    return not any(cell.strip() for cell in cells)


def _mostly_empty_body(rows: list[list[str]]) -> bool:
    if not rows:
        return False
    total = sum(len(row) for row in rows)
    empty = sum(1 for row in rows for cell in row if not cell.strip())
    return total > 0 and empty / total >= 0.75


def _garbled_ratio(rows: list[str]) -> float:
    text = "".join(rows)
    meaningful = [ch for ch in text if not ch.isspace() and ch not in "|:-"]
    if not meaningful:
        return 0.0
    garbled = sum(1 for ch in meaningful if ch in "?？�□" or ch == "\ufffd")
    return garbled / len(meaningful)


def _issue(code: str, severity: Severity, message: str, evidence: str | None = None) -> TableQualityIssue:
    return TableQualityIssue(code=code, severity=severity, message=message, evidence=evidence)
