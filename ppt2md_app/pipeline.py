from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import perf_counter

from .artifacts import (
    build_fail_open_slide_meta,
    build_error_sidecar,
    build_raw_cache_record,
    build_slide_meta,
    sha256_text,
    stage1_fingerprint,
    stage2_fingerprint,
    validate_raw_cache_record,
    validate_slide_meta,
)
from .config import AppConfig
from .files import merge_markdowns, read_json, write_json, write_text_atomic
from .models import run_stage_1_vision, run_stage_2_brain_parallel, set_dashscope_api_key
from .refiner import refine_slide_markdown
from .renderer import render_blocks_to_markdown
from .reporting import build_run_report, finalize_run_report, refresh_page_suspects, stage_blocked, stage_failed, summarize_blocks
from .validators import first_api_error_prefix, is_api_error_text, validate_slide_markdown


def process_single_ppt_task(ppt_name, task_config, msg_queue, config: AppConfig):
    """
    双阶段流水线控制器。
    """
    set_dashscope_api_key(config)

    images_paths = task_config["images"]
    start_idx = task_config["range_start"]
    end_idx = task_config["range_end"]
    task_id = task_config["task_id"]

    target_images = images_paths[start_idx:end_idx]
    total_slides = len(target_images)

    ppt_root = Path(config.output_folder) / ppt_name
    temp_dir = ppt_root / "temp_raw_vision"
    ppt_root.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    report_path = ppt_root / "run_report.json"
    report, page_reports = build_run_report(
        ppt_name=ppt_name,
        target_images=target_images,
        start_idx=start_idx,
        config=config,
    )
    write_json(report_path, report)

    msg_queue.put(
        (
            "log",
            (
                f"[{ppt_name}] 任务启动。V10 并行版引擎 "
                f"(Vision:{config.vision_provider}:{config.model_vision}, {config.vision_batch_workers} workers / "
                f"Brain:{config.brain_provider}:{config.model_brain}, {config.brain_batch_workers} workers) 已激活。"
            ),
        )
    )
    msg_queue.put(("init_task", task_id, total_slides * 2))

    pipeline_started = perf_counter()
    target_blocks_by_slide = {}
    try:
        raw_data_map, target_blocks_by_slide = _run_vision_stage(
            ppt_name=ppt_name,
            target_images=target_images,
            start_idx=start_idx,
            temp_dir=temp_dir,
            task_id=task_id,
            msg_queue=msg_queue,
            config=config,
            page_reports=page_reports,
        )

        msg_queue.put(("log", f"[{ppt_name}] Step 1 视觉完成。开始 Step 2 并行逻辑重组..."))

        ok_slides = _run_brain_stage(
            ppt_name=ppt_name,
            total_slides=total_slides,
            start_idx=start_idx,
            ppt_root=ppt_root,
            raw_data_map=raw_data_map,
            task_id=task_id,
            msg_queue=msg_queue,
            config=config,
            page_reports=page_reports,
            target_blocks_by_slide=target_blocks_by_slide,
        )

        msg_queue.put(("status", task_id, "正在合并..."))
        merge_markdowns(ppt_root, ppt_name, allowed_slide_numbers=ok_slides)
        for slide_no in ok_slides:
            page_reports[slide_no]["final"]["included_in_full"] = True

        for slide_no, page in page_reports.items():
            refresh_page_suspects(page, target_blocks_by_slide.get(slide_no))
        finalize_run_report(report)
        write_json(report_path, report)
        msg_queue.put(("log", f"[{ppt_name}] 全部流程结束，总耗时 {perf_counter() - pipeline_started:.1f}s"))
        return f"{ppt_name} Done"
    except Exception:
        for slide_no, page in page_reports.items():
            refresh_page_suspects(page, target_blocks_by_slide.get(slide_no))
        finalize_run_report(report)
        write_json(report_path, report)
        raise


def _run_vision_stage(ppt_name, target_images, start_idx, temp_dir, task_id, msg_queue, config: AppConfig, page_reports):
    stage_started = perf_counter()
    msg_queue.put(("status", task_id, f"[cyan]Step 1: 视觉提取 (并发 {config.vision_batch_workers})..."))

    vision_futures = {}
    raw_data_map = {}
    blocks_by_slide = {}
    cache_hits = 0
    submitted = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=config.vision_batch_workers) as executor:
        for i, img_path in enumerate(target_images):
            actual_slide_no = start_idx + i + 1
            raw_file = temp_dir / f"Raw_{actual_slide_no:02d}.json"
            page = page_reports[actual_slide_no]
            page["stage1"]["path"] = str(raw_file)

            try:
                expected_fingerprint = stage1_fingerprint(img_path, config)
                page["image_sha256"] = expected_fingerprint["image_sha256"]
            except Exception as exc:
                message = str(exc)
                stage_failed(page, "stage1", "image_fingerprint_failed", message)
                page["stage1"]["cache"] = "miss"
                page["final"].update({"status": "failed", "reason": "stage1_image_fingerprint_failed"})
                refresh_page_suspects(page)
                write_json(
                    temp_dir / f"Raw_{actual_slide_no:02d}.error.json",
                    build_error_sidecar(actual_slide_no, "stage1", "image_fingerprint_failed", message),
                )
                failed += 1
                msg_queue.put(("advance", task_id, 1))
                continue

            if raw_file.exists():
                try:
                    data = read_json(raw_file)
                    valid, cache_status = validate_raw_cache_record(data, actual_slide_no, expected_fingerprint)
                    page["stage1"]["cache"] = cache_status
                    if valid:
                        raw_data_map[actual_slide_no] = data["raw_text"]
                        blocks_by_slide[actual_slide_no] = data.get("blocks") or []
                        page["quality"] = summarize_blocks(data.get("blocks") or [])
                        page["provenance"] = data.get("provenance") or page.get("provenance")
                        page["block_refiner"] = data.get("block_refiner") or page.get("block_refiner")
                        page["stage1"].update(
                            {
                                "status": "ok",
                                "sha256": data.get("raw_text_sha256"),
                                "blocks_count": len(data.get("blocks") or []),
                                "elapsed_seconds": 0.0,
                            }
                        )
                        refresh_page_suspects(page, blocks_by_slide.get(actual_slide_no))
                        msg_queue.put(("log", f"[{ppt_name}] P{actual_slide_no} 视觉缓存命中"))
                        msg_queue.put(("advance", task_id, 1))
                        cache_hits += 1
                        continue
                except Exception:
                    page["stage1"]["cache"] = "invalid"
            else:
                page["stage1"]["cache"] = "miss"

            future = executor.submit(
                run_stage_1_vision,
                img_path,
                actual_slide_no,
                ppt_name,
                msg_queue,
                config,
            )
            vision_futures[future] = (actual_slide_no, img_path, raw_file, perf_counter())
            submitted += 1

        for future in as_completed(vision_futures):
            slide_no, img_path, raw_file, started_at = vision_futures[future]
            page = page_reports[slide_no]
            try:
                result = future.result()
                if result.get("success"):
                    raw_text = result.get("raw_text") or ""
                    if not raw_text.strip() or is_api_error_text(raw_text):
                        message = raw_text or "Empty Stage 1 raw text."
                        stage_failed(page, "stage1", first_api_error_prefix(message) or "invalid_raw_text", message)
                        page["final"].update({"status": "failed", "reason": "stage1_invalid_raw_text"})
                        refresh_page_suspects(page)
                        write_json(
                            temp_dir / f"Raw_{slide_no:02d}.error.json",
                            build_error_sidecar(slide_no, "stage1", "invalid_raw_text", message),
                        )
                        failed += 1
                        continue

                    raw_data_map[slide_no] = raw_text
                    cache_record = build_raw_cache_record(result, img_path, config)
                    write_json(raw_file, cache_record)
                    blocks_by_slide[slide_no] = cache_record.get("blocks") or []
                    page["quality"] = summarize_blocks(cache_record.get("blocks") or [])
                    page["provenance"] = cache_record.get("provenance") or page.get("provenance")
                    page["block_refiner"] = cache_record.get("block_refiner") or page.get("block_refiner")
                    page["stage1"].update(
                        {
                            "status": "ok",
                            "sha256": cache_record.get("raw_text_sha256"),
                            "blocks_count": len(cache_record.get("blocks") or []),
                            "elapsed_seconds": round(perf_counter() - started_at, 3),
                        }
                    )
                    refresh_page_suspects(page, blocks_by_slide.get(slide_no))
                else:
                    message = result.get("error") or "Unknown Stage 1 error."
                    msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 视觉失败: {message}"))
                    stage_failed(page, "stage1", first_api_error_prefix(message) or "stage1_failed", message)
                    page["stage1"]["elapsed_seconds"] = round(perf_counter() - started_at, 3)
                    page["final"].update({"status": "failed", "reason": "stage1_failed"})
                    refresh_page_suspects(page)
                    write_json(
                        temp_dir / f"Raw_{slide_no:02d}.error.json",
                        build_error_sidecar(slide_no, "stage1", "stage1_failed", message),
                    )
                    failed += 1
            except RuntimeError as e:
                msg_queue.put(("status", task_id, "[bold red]权限拒绝!"))
                raise e
            except Exception as e:
                msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 异常: {e}"))
                stage_failed(page, "stage1", "stage1_exception", str(e))
                page["stage1"]["elapsed_seconds"] = round(perf_counter() - started_at, 3)
                page["final"].update({"status": "failed", "reason": "stage1_exception"})
                refresh_page_suspects(page)
                failed += 1
            finally:
                msg_queue.put(("advance", task_id, 1))

    msg_queue.put(
        (
            "log",
            (
                f"[{ppt_name}] Step 1 完成，耗时 {perf_counter() - stage_started:.1f}s，"
                f"缓存 {cache_hits}，提交 {submitted}，失败 {failed}"
            ),
        )
    )
    return raw_data_map, blocks_by_slide


def _run_brain_stage(
    ppt_name,
    total_slides,
    start_idx,
    ppt_root,
    raw_data_map,
    task_id,
    msg_queue,
    config: AppConfig,
    page_reports,
    target_blocks_by_slide=None,
):
    stage_started = perf_counter()
    msg_queue.put(("status", task_id, f"[green]Step 2: 并行思考 (并发 {config.brain_batch_workers})..."))

    brain_futures = {}
    skipped = 0
    submitted = 0
    failed = 0
    ok_slides = []
    target_blocks_by_slide = target_blocks_by_slide or {}

    with ThreadPoolExecutor(max_workers=config.brain_batch_workers) as executor:
        for i in range(total_slides):
            actual_slide_no = start_idx + i + 1
            output_path = ppt_root / f"Slide_{actual_slide_no:02d}.md"
            meta_path = ppt_root / f"Slide_{actual_slide_no:02d}.meta.json"
            page = page_reports[actual_slide_no]
            page["stage2"]["path"] = str(output_path)
            page["stage2"]["meta_path"] = str(meta_path)

            if page["stage1"]["status"] != "ok" or actual_slide_no not in raw_data_map:
                message = "Stage 1 没有可用 Raw Data。"
                stage_blocked(page, "stage2", "stage1_not_ok", message)
                page["final"].update({"status": "failed", "reason": "stage1_not_ok"})
                refresh_page_suspects(page)
                _write_stage2_failure(ppt_root, actual_slide_no, "stage1_not_ok", message)
                msg_queue.put(("advance", task_id, 1))
                failed += 1
                continue

            expected_fingerprint = stage2_fingerprint(actual_slide_no, raw_data_map, config)
            if output_path.exists() and meta_path.exists():
                try:
                    markdown = output_path.read_text(encoding="utf-8")
                    meta = read_json(meta_path)
                    valid, cache_status = validate_slide_meta(meta, actual_slide_no, markdown, expected_fingerprint)
                    page["stage2"]["cache"] = cache_status
                    if valid:
                        validation = validate_slide_markdown(
                            markdown,
                            actual_slide_no,
                            target_raw=raw_data_map.get(actual_slide_no),
                            target_blocks=target_blocks_by_slide.get(actual_slide_no),
                            neighbor_raw=_neighbor_raw_map(raw_data_map, actual_slide_no),
                        )
                        page["validation"] = validation.to_dict()
                        refresh_page_suspects(page, target_blocks_by_slide.get(actual_slide_no))
                        if validation.ok:
                            page["stage2"].update(
                                {
                                    "status": "ok",
                                    "sha256": sha256_text(markdown),
                                    "elapsed_seconds": 0.0,
                                }
                            )
                            page["final"].update({"status": "ok", "reason": None})
                            msg_queue.put(("advance", task_id, 1))
                            skipped += 1
                            ok_slides.append(actual_slide_no)
                            continue
                        page["stage2"]["cache"] = "invalid"
                except Exception:
                    page["stage2"]["cache"] = "invalid"
            elif output_path.exists() or meta_path.exists():
                page["stage2"]["cache"] = "legacy_miss"
            else:
                page["stage2"]["cache"] = "miss"

            future = executor.submit(
                run_stage_2_brain_parallel,
                actual_slide_no,
                raw_data_map,
                config,
            )
            brain_futures[future] = (actual_slide_no, output_path, meta_path, perf_counter())
            submitted += 1

        for future in as_completed(brain_futures):
            slide_no, output_path, meta_path, started_at = brain_futures[future]
            page = page_reports[slide_no]
            try:
                result = future.result()
                if not isinstance(result, dict):
                    result = {"success": True, "slide_no": slide_no, "markdown": str(result), "raw_response": str(result)}

                if result.get("success"):
                    final_markdown = result.get("markdown") or ""
                    refine_result = refine_slide_markdown(
                        final_markdown,
                        slide_no,
                        raw_response=result.get("raw_response"),
                        target_raw=raw_data_map.get(slide_no),
                        target_blocks=target_blocks_by_slide.get(slide_no),
                    )
                    final_markdown = refine_result.markdown
                    page["refiner"] = refine_result.to_dict()
                    validation = validate_slide_markdown(
                        final_markdown,
                        slide_no,
                        raw_response=result.get("raw_response"),
                        target_raw=raw_data_map.get(slide_no),
                        target_blocks=target_blocks_by_slide.get(slide_no),
                        neighbor_raw=_neighbor_raw_map(raw_data_map, slide_no),
                    )
                    page["validation"] = validation.to_dict()
                    refresh_page_suspects(page, target_blocks_by_slide.get(slide_no))
                    if not validation.ok:
                        message = "; ".join(issue.message for issue in validation.errors)
                        page["stage2"]["elapsed_seconds"] = round(perf_counter() - started_at, 3)
                        if _write_stage2_fail_open_markdown(
                            ppt_root=ppt_root,
                            slide_no=slide_no,
                            code="validation_failed",
                            message=message,
                            raw_data_map=raw_data_map,
                            target_blocks=target_blocks_by_slide.get(slide_no),
                            config=config,
                            page=page,
                            raw_response=result.get("raw_response"),
                            source_validation=validation.to_dict(),
                        ):
                            ok_slides.append(slide_no)
                            refresh_page_suspects(page, target_blocks_by_slide.get(slide_no))
                            msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 重组失败，已写入保守 Markdown fallback"))
                            continue
                        stage_failed(page, "stage2", "validation_failed", message)
                        page["final"].update({"status": "failed", "reason": "stage2_validation_failed"})
                        refresh_page_suspects(page, target_blocks_by_slide.get(slide_no))
                        _write_stage2_failure(ppt_root, slide_no, "validation_failed", message, validation=validation.to_dict())
                        failed += 1
                        continue
                    fallback_issue = _stage2_warning_fallback_issue(
                        validation.to_dict(),
                        slide_no=slide_no,
                        raw_data_map=raw_data_map,
                        target_blocks=target_blocks_by_slide.get(slide_no),
                    )
                    if fallback_issue and _write_stage2_fail_open_markdown(
                        ppt_root=ppt_root,
                        slide_no=slide_no,
                        code=fallback_issue["code"],
                        message=fallback_issue["message"],
                        raw_data_map=raw_data_map,
                        target_blocks=target_blocks_by_slide.get(slide_no),
                        config=config,
                        page=page,
                        raw_response=result.get("raw_response"),
                        source_validation=validation.to_dict(),
                    ):
                        ok_slides.append(slide_no)
                        refresh_page_suspects(page, target_blocks_by_slide.get(slide_no))
                        msg_queue.put(("log", f"[{ppt_name}] P{slide_no} {fallback_issue['code']}，已写入保守 Markdown fallback"))
                        continue

                    write_text_atomic(output_path, final_markdown)
                    meta = build_slide_meta(
                        slide_no,
                        final_markdown,
                        validation.to_dict(),
                        raw_data_map,
                        config,
                        refiner=refine_result.to_dict(),
                    )
                    write_json(meta_path, meta)
                    page["stage2"].update(
                        {
                            "status": "ok",
                            "sha256": meta.get("markdown_sha256"),
                            "elapsed_seconds": round(perf_counter() - started_at, 3),
                        }
                    )
                    page["final"].update({"status": "ok", "reason": None})
                    ok_slides.append(slide_no)
                    msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 重组完成"))
                else:
                    message = result.get("error") or "Unknown Stage 2 error."
                    code = result.get("error_code") or first_api_error_prefix(message) or "stage2_failed"
                    page["stage2"]["elapsed_seconds"] = round(perf_counter() - started_at, 3)
                    if _write_stage2_fail_open_markdown(
                        ppt_root=ppt_root,
                        slide_no=slide_no,
                        code=code,
                        message=message,
                        raw_data_map=raw_data_map,
                        target_blocks=target_blocks_by_slide.get(slide_no),
                        config=config,
                        page=page,
                        raw_response=result.get("raw_response"),
                    ):
                        ok_slides.append(slide_no)
                        refresh_page_suspects(page, target_blocks_by_slide.get(slide_no))
                        msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 重组失败，已写入保守 Markdown fallback"))
                        continue
                    stage_failed(page, "stage2", code, message)
                    page["final"].update({"status": "failed", "reason": "stage2_failed"})
                    refresh_page_suspects(page, target_blocks_by_slide.get(slide_no))
                    _write_stage2_failure(ppt_root, slide_no, code, message, raw_response=result.get("raw_response"))
                    failed += 1
            except Exception as e:
                msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 重组异常: {e}"))
                page["stage2"]["elapsed_seconds"] = round(perf_counter() - started_at, 3)
                if _write_stage2_fail_open_markdown(
                    ppt_root=ppt_root,
                    slide_no=slide_no,
                    code="stage2_exception",
                    message=str(e),
                    raw_data_map=raw_data_map,
                    target_blocks=target_blocks_by_slide.get(slide_no),
                    config=config,
                    page=page,
                ):
                    ok_slides.append(slide_no)
                    refresh_page_suspects(page, target_blocks_by_slide.get(slide_no))
                    msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 重组异常，已写入保守 Markdown fallback"))
                    continue
                stage_failed(page, "stage2", "stage2_exception", str(e))
                page["final"].update({"status": "failed", "reason": "stage2_exception"})
                refresh_page_suspects(page, target_blocks_by_slide.get(slide_no))
                _write_stage2_failure(ppt_root, slide_no, "stage2_exception", str(e))
                failed += 1
            finally:
                msg_queue.put(("advance", task_id, 1))

    msg_queue.put(
        (
            "log",
            (
                f"[{ppt_name}] Step 2 完成，耗时 {perf_counter() - stage_started:.1f}s，"
                f"跳过 {skipped}，提交 {submitted}，失败 {failed}"
            ),
        )
    )
    return sorted(set(ok_slides))


def _write_stage2_failure(ppt_root, slide_no, code, message, validation=None, raw_response=None):
    payload = build_error_sidecar(
        slide_no,
        "stage2",
        code,
        message,
        validation=validation,
        raw_response=raw_response,
    )
    write_json(ppt_root / f"Slide_{slide_no:02d}.error.json", payload)
    write_json(
        ppt_root / f"Slide_{slide_no:02d}.meta.json",
        {
            "schema_version": 1,
            "status": "failed",
            "slide_no": slide_no,
            "error": {"code": code, "message": message},
            "validation": validation,
        },
    )


def _write_stage2_fail_open_markdown(
    *,
    ppt_root,
    slide_no,
    code,
    message,
    raw_data_map,
    target_blocks,
    config: AppConfig,
    page,
    raw_response=None,
    source_validation=None,
) -> bool:
    fallback = _build_stage2_fallback_markdown(
        slide_no=slide_no,
        code=code,
        message=message,
        raw_data_map=raw_data_map,
        target_blocks=target_blocks,
    )
    if not fallback:
        return False
    markdown, validation = fallback
    if not validation.ok:
        return False

    output_path = ppt_root / f"Slide_{slide_no:02d}.md"
    meta_path = ppt_root / f"Slide_{slide_no:02d}.meta.json"
    write_text_atomic(output_path, markdown)
    write_json(
        meta_path,
        build_fail_open_slide_meta(
            slide_no,
            markdown,
            validation.to_dict(),
            raw_data_map,
            config,
            code=code,
            message=message,
            fallback_source="stage1_page_ir",
        ),
    )
    write_json(
        ppt_root / f"Slide_{slide_no:02d}.error.json",
        build_error_sidecar(
            slide_no,
            "stage2",
            code,
            message,
            validation=source_validation,
            raw_response=raw_response,
            fallback={"source": "stage1_page_ir", "markdown_path": str(output_path)},
        ),
    )

    stage_failed(page, "stage2", code, message)
    page["stage2"].update(
        {
            "sha256": sha256_text(markdown),
            "fallback": "stage1_page_ir",
        }
    )
    page["validation"] = validation.to_dict()
    page["refiner"] = {"changed": False, "applied_ops": [], "dismissed": []}
    page["final"].update({"status": "fail_open", "reason": code})
    return True


def _build_stage2_fallback_markdown(*, slide_no, code, message, raw_data_map, target_blocks):
    if not target_blocks:
        return None

    body = _strip_slide_heading(render_blocks_to_markdown(target_blocks, slide_no), slide_no)
    markdown = (
        f"# Slide {slide_no}\n\n"
        "> [!WARNING] Stage 2 重组失败，已使用 Stage 1 确定性 Markdown fallback。\n"
        f"> 原因：{_one_line_error(code, message)}\n\n"
        f"{body}"
    ).rstrip() + "\n"

    validation = validate_slide_markdown(
        markdown,
        slide_no,
        raw_response=None,
        target_raw=raw_data_map.get(slide_no),
        target_blocks=target_blocks,
        neighbor_raw=_neighbor_raw_map(raw_data_map, slide_no),
    )
    return markdown, validation


def _strip_slide_heading(markdown: str, slide_no: int) -> str:
    lines = (markdown or "").splitlines()
    if lines and lines[0].strip().lower() == f"# slide {slide_no}".lower():
        return "\n".join(lines[1:]).strip() + "\n"
    return (markdown or "").strip() + "\n"


def _one_line_error(code: str, message: str) -> str:
    text = " ".join(str(message or "").split())
    if len(text) > 180:
        text = text[:177].rstrip() + "..."
    return f"{code}: {text}" if text else str(code)


def _stage2_warning_fallback_issue(validation: dict, *, slide_no, raw_data_map, target_blocks) -> dict | None:
    fallback_codes = {
        "ocr_coverage_low",
        "figure_note_missing",
        "unrendered_figure_analysis",
        "table_structure_warning",
    }
    formula_codes = {
        "formula_brace_unbalanced",
        "formula_parenthesis_unbalanced",
        "formula_bracket_unbalanced",
        "latex_left_right_unbalanced",
        "latex_frac_missing_braces",
        "formula_uncertain_marker",
        "inline_math_suspicious",
    }
    for issue in validation.get("warnings") or []:
        if not isinstance(issue, dict):
            continue
        code = str(issue.get("code") or "")
        if code in fallback_codes:
            message = issue.get("message") or code
            evidence = issue.get("evidence")
            return {"code": code, "message": f"{message} {evidence}".strip()}
        if code in formula_codes and _fallback_reduces_formula_warnings(
            validation,
            slide_no=slide_no,
            raw_data_map=raw_data_map,
            target_blocks=target_blocks,
        ):
            message = issue.get("message") or code
            evidence = issue.get("evidence")
            return {"code": code, "message": f"{message} {evidence}".strip()}
    return None


def _fallback_reduces_formula_warnings(validation: dict, *, slide_no, raw_data_map, target_blocks) -> bool:
    current = _warning_count(validation, ("formula_", "latex_", "inline_math_suspicious"))
    if current <= 0:
        return False
    fallback = _build_stage2_fallback_markdown(
        slide_no=slide_no,
        code="formula_quality_warning",
        message="Stage 2 公式质量低于 PageIR fallback。",
        raw_data_map=raw_data_map,
        target_blocks=target_blocks,
    )
    if not fallback:
        return False
    _, fallback_validation = fallback
    if not fallback_validation.ok:
        return False
    return _warning_count(fallback_validation.to_dict(), ("formula_", "latex_", "inline_math_suspicious")) < current


def _warning_count(validation: dict, codes_or_prefixes: tuple[str, ...]) -> int:
    count = 0
    for issue in validation.get("warnings") or []:
        if not isinstance(issue, dict):
            continue
        code = str(issue.get("code") or "")
        if any(code == item or code.startswith(item) for item in codes_or_prefixes):
            count += 1
    return count


def _neighbor_raw_map(raw_data_map, slide_no):
    return {
        page_no: raw_data_map[page_no]
        for page_no in range(slide_no - 2, slide_no + 3)
        if page_no != slide_no and page_no in raw_data_map
    }
