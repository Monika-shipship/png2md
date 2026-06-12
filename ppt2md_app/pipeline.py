from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from time import perf_counter

from .config import AppConfig
from .files import merge_markdowns, read_json, write_json
from .models import run_stage_1_vision, run_stage_2_brain_parallel, set_dashscope_api_key


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
    raw_data_map = _run_vision_stage(
        ppt_name=ppt_name,
        target_images=target_images,
        start_idx=start_idx,
        temp_dir=temp_dir,
        task_id=task_id,
        msg_queue=msg_queue,
        config=config,
    )

    msg_queue.put(("log", f"[{ppt_name}] Step 1 视觉完成。开始 Step 2 并行逻辑重组..."))

    _run_brain_stage(
        ppt_name=ppt_name,
        total_slides=total_slides,
        start_idx=start_idx,
        ppt_root=ppt_root,
        raw_data_map=raw_data_map,
        task_id=task_id,
        msg_queue=msg_queue,
        config=config,
    )

    msg_queue.put(("status", task_id, "正在合并..."))
    merge_markdowns(ppt_root, ppt_name)
    msg_queue.put(("log", f"[{ppt_name}] 全部流程结束，总耗时 {perf_counter() - pipeline_started:.1f}s"))
    return f"{ppt_name} Done"


def _run_vision_stage(ppt_name, target_images, start_idx, temp_dir, task_id, msg_queue, config: AppConfig):
    stage_started = perf_counter()
    msg_queue.put(("status", task_id, f"[cyan]Step 1: 视觉提取 (并发 {config.vision_batch_workers})..."))

    vision_futures = {}
    raw_data_map = {}
    cache_hits = 0
    submitted = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=config.vision_batch_workers) as executor:
        for i, img_path in enumerate(target_images):
            actual_slide_no = start_idx + i + 1
            raw_file = temp_dir / f"Raw_{actual_slide_no:02d}.json"

            if raw_file.exists():
                try:
                    data = read_json(raw_file)
                    raw_data_map[actual_slide_no] = data["raw_text"]
                    msg_queue.put(("log", f"[{ppt_name}] P{actual_slide_no} 视觉缓存命中"))
                    msg_queue.put(("advance", task_id, 1))
                    cache_hits += 1
                    continue
                except Exception:
                    pass

            future = executor.submit(
                run_stage_1_vision,
                img_path,
                actual_slide_no,
                ppt_name,
                msg_queue,
                config,
            )
            vision_futures[future] = actual_slide_no
            submitted += 1

        for future in as_completed(vision_futures):
            slide_no = vision_futures[future]
            try:
                result = future.result()
                if result["success"]:
                    raw_data_map[slide_no] = result["raw_text"]
                    write_json(temp_dir / f"Raw_{slide_no:02d}.json", result)
                else:
                    msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 视觉失败: {result.get('error')}"))
                    raw_data_map[slide_no] = "[Vision Failed]"
                    failed += 1
            except RuntimeError as e:
                msg_queue.put(("status", task_id, "[bold red]权限拒绝!"))
                raise e
            except Exception as e:
                msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 异常: {e}"))
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
    return raw_data_map


def _run_brain_stage(
    ppt_name,
    total_slides,
    start_idx,
    ppt_root,
    raw_data_map,
    task_id,
    msg_queue,
    config: AppConfig,
):
    stage_started = perf_counter()
    msg_queue.put(("status", task_id, f"[green]Step 2: 并行思考 (并发 {config.brain_batch_workers})..."))

    brain_futures = {}
    skipped = 0
    submitted = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=config.brain_batch_workers) as executor:
        for i in range(total_slides):
            actual_slide_no = start_idx + i + 1
            output_path = ppt_root / f"Slide_{actual_slide_no:02d}.md"

            if output_path.exists() and output_path.stat().st_size > 100:
                msg_queue.put(("advance", task_id, 1))
                skipped += 1
                continue

            future = executor.submit(
                run_stage_2_brain_parallel,
                actual_slide_no,
                raw_data_map,
                config,
            )
            brain_futures[future] = (actual_slide_no, output_path)
            submitted += 1

        for future in as_completed(brain_futures):
            slide_no, output_path = brain_futures[future]
            try:
                final_markdown = future.result()
                with output_path.open("w", encoding="utf-8") as f:
                    f.write(final_markdown)

                msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 重组完成"))
            except Exception as e:
                msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 重组异常: {e}"))
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
