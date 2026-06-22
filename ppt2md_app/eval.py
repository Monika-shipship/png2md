import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .files import write_json, write_text_atomic
from .ir import attach_page_image_evidence, build_page_ir, render_page_ir_to_markdown
from .provenance import build_page_provenance
from .refiner import refine_page_ir
from .reporting import summarize_blocks
from .validators import validate_slide_markdown


EVAL_REPORT_SCHEMA_VERSION = 1
DEFAULT_EVAL_FIXTURE_DIR = "tests/fixtures/eval_cases"
DEFAULT_EVAL_OUTPUT_PATH = "markdown_output/eval_report.json"
REQUIRED_CASE_FIELDS = {
    "name",
    "slide_no",
    "tags",
    "expected_warning_codes",
    "allow_warning_codes",
}


@dataclass(frozen=True)
class EvalCase:
    name: str
    slide_no: int
    tags: list[str]
    expected_warning_codes: list[str]
    allow_warning_codes: list[str]
    case_dir: Path
    raw_text: str
    expected_markdown: str
    page_image_path: Path | None = None


def load_eval_cases(fixture_dir: str | Path) -> list[EvalCase]:
    root = Path(fixture_dir)
    if not root.exists():
        raise FileNotFoundError(f"eval fixture dir not found: {root}")
    cases = []
    for case_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        cases.append(load_eval_case(case_dir))
    if not cases:
        raise ValueError(f"eval fixture dir has no case directories: {root}")
    return cases


def load_eval_case(case_dir: str | Path) -> EvalCase:
    path = Path(case_dir)
    case_path = path / "case.json"
    raw_path = path / "raw_stage1.txt"
    expected_path = path / "expected.md"
    if not case_path.exists():
        raise ValueError(f"missing case.json: {path}")
    if not raw_path.exists():
        raise ValueError(f"missing raw_stage1.txt: {path}")
    if not expected_path.exists():
        raise ValueError(f"missing expected.md: {path}")

    spec = json.loads(case_path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_CASE_FIELDS - set(spec))
    if missing:
        raise ValueError(f"{case_path} missing fields: {', '.join(missing)}")

    name = str(spec["name"])
    slide_no = int(spec["slide_no"])
    tags = _string_list(spec["tags"], "tags", case_path)
    expected_warning_codes = _string_list(spec["expected_warning_codes"], "expected_warning_codes", case_path)
    allow_warning_codes = _string_list(spec["allow_warning_codes"], "allow_warning_codes", case_path)
    page_image_path = path / "page.png"
    return EvalCase(
        name=name,
        slide_no=slide_no,
        tags=tags,
        expected_warning_codes=expected_warning_codes,
        allow_warning_codes=allow_warning_codes,
        case_dir=path,
        raw_text=raw_path.read_text(encoding="utf-8"),
        expected_markdown=expected_path.read_text(encoding="utf-8"),
        page_image_path=page_image_path if page_image_path.exists() else None,
    )


def run_offline_eval(fixture_dir: str | Path, output_path: str | Path) -> dict[str, Any]:
    cases = load_eval_cases(fixture_dir)
    report_path = Path(output_path)
    artifacts_dir = report_path.with_suffix("")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    results = [_run_case(case, artifacts_dir) for case in cases]
    report = {
        "schema_version": EVAL_REPORT_SCHEMA_VERSION,
        "fixture_dir": str(Path(fixture_dir)),
        "output_path": str(report_path),
        "artifacts_dir": str(artifacts_dir),
        "summary": _summarize_results(results),
        "cases": results,
    }
    write_json(report_path, report)
    return report


def _run_case(case: EvalCase, artifacts_dir: Path) -> dict[str, Any]:
    page_ir = build_page_ir(case.raw_text, case.slide_no)
    if case.page_image_path:
        page_ir = attach_page_image_evidence(page_ir, str(case.page_image_path))
    refine_result = refine_page_ir(page_ir, slide_no=case.slide_no, target_raw=case.raw_text)
    page_ir = refine_result.page_ir
    markdown = render_page_ir_to_markdown(page_ir, case.slide_no)
    validation = validate_slide_markdown(
        markdown,
        case.slide_no,
        target_raw=case.raw_text,
        target_blocks=page_ir.get("blocks") or [],
    ).to_dict()
    provenance = build_page_provenance(page_ir)
    quality = summarize_blocks(page_ir.get("blocks") or [])
    actual_path = artifacts_dir / f"{case.name}.actual.md"
    write_text_atomic(actual_path, markdown)

    warning_codes = _issue_codes(validation.get("warnings") or [])
    error_codes = _issue_codes(validation.get("errors") or [])
    failures = _case_failures(
        expected_markdown=case.expected_markdown,
        actual_markdown=markdown,
        expected_warning_codes=case.expected_warning_codes,
        allow_warning_codes=case.allow_warning_codes,
        warning_codes=warning_codes,
        error_codes=error_codes,
    )
    return {
        "name": case.name,
        "slide_no": case.slide_no,
        "tags": case.tags,
        "status": "passed" if not failures else "failed",
        "failures": failures,
        "actual_markdown_path": str(actual_path),
        "warning_codes": warning_codes,
        "error_codes": error_codes,
        "validation": validation,
        "quality": quality,
        "provenance": provenance,
        "block_refiner": refine_result.to_dict(),
        "op_audit": refine_result.op_audit,
    }


def _case_failures(
    *,
    expected_markdown: str,
    actual_markdown: str,
    expected_warning_codes: list[str],
    allow_warning_codes: list[str],
    warning_codes: list[str],
    error_codes: list[str],
) -> list[dict[str, Any]]:
    failures = []
    if _normalize_lf(expected_markdown) != _normalize_lf(actual_markdown):
        failures.append({"code": "markdown_golden_mismatch", "message": "actual Markdown does not match expected.md"})
    for code in error_codes:
        failures.append({"code": "validation_error", "message": code})
    missing_expected = [code for code in expected_warning_codes if code not in warning_codes]
    if missing_expected:
        failures.append({"code": "expected_warning_missing", "message": ", ".join(missing_expected)})
    unexpected = [
        code
        for code in warning_codes
        if code not in expected_warning_codes and code not in allow_warning_codes
    ]
    if unexpected:
        failures.append({"code": "unexpected_warning", "message": ", ".join(unexpected)})
    return failures


def _summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for result in results if result["status"] == "passed")
    failed = len(results) - passed
    validation_error_count = sum(len(result.get("error_codes") or []) for result in results)
    validation_warning_count = sum(len(result.get("warning_codes") or []) for result in results)
    block_counts: dict[str, int] = {}
    op_audit_counts: dict[str, int] = {}
    formula_warning_count = 0
    table_warning_count = 0
    figure_warning_count = 0
    for result in results:
        quality = result.get("quality") or {}
        for block_type, count in (quality.get("block_counts") or {}).items():
            block_counts[block_type] = block_counts.get(block_type, 0) + int(count or 0)
        formula_warning_count += int(quality.get("formula_warning_count") or 0)
        table_warning_count += int(quality.get("table_warning_count") or 0)
        figure_warning_count += int(quality.get("figure_warning_count") or 0)
        for audit in result.get("op_audit") or []:
            status = str(audit.get("status") or "unknown")
            op_audit_counts[status] = op_audit_counts.get(status, 0) + 1
    return {
        "cases_total": len(results),
        "cases_passed": passed,
        "cases_failed": failed,
        "validation_errors": validation_error_count,
        "validation_warnings": validation_warning_count,
        "block_counts": block_counts,
        "formula_warning_count": formula_warning_count,
        "table_warning_count": table_warning_count,
        "figure_warning_count": figure_warning_count,
        "op_audit": {
            "total": sum(op_audit_counts.values()),
            "by_status": op_audit_counts,
        },
        "actual_tokens": None,
    }


def _issue_codes(issues: list[dict[str, Any]]) -> list[str]:
    return [str(issue.get("code")) for issue in issues if isinstance(issue, dict) and issue.get("code")]


def _string_list(value: Any, field_name: str, case_path: Path) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{case_path} field {field_name} must be a list of strings")
    return value


def _normalize_lf(text: str) -> str:
    return (text or "").replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"
