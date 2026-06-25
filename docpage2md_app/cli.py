import argparse
import queue
import sys
import time
import urllib.parse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import replace
from multiprocessing import Manager
from pathlib import Path

from .config import AppConfig
from .eval import DEFAULT_EVAL_FIXTURE_DIR, DEFAULT_EVAL_OUTPUT_PATH
from .model_profiles import apply_model_profile
from .run_logger import RunLogger, safe_progress


MINERU_SUPPORTED_SUFFIXES = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".jp2",
    ".webp",
    ".gif",
    ".bmp",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".html",
    ".htm",
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="DocPage2MD (MinerU / vision document pages to Markdown)")
    parser.add_argument("-n", "--name", type=str, default="default", help="任务会话名称")
    parser.add_argument("-o", "--output", type=str, default="./markdown_output", help="输出目录路径")
    parser.add_argument(
        "--engine-mode",
        choices=["vision_only", "mineru_only", "hybrid"],
        default="vision_only",
        help="处理模式：vision_only=旧图片目录流程，mineru_only=MinerU 多格式解析，hybrid=MinerU layout/crop + docpage2md 后续精修",
    )
    parser.add_argument(
        "--document-type",
        choices=["handwritten_notes", "paper_pdf", "screenshot_question", "complex_ppt", "custom"],
        default="custom",
        help="文档类型，用于推荐处理模式和模型档位",
    )
    parser.add_argument(
        "--model-profile",
        choices=["cheap", "balanced", "accurate", "manual"],
        default="balanced",
        help="模型档位；hybrid 默认 balanced，复杂文档可选 accurate",
    )
    parser.add_argument("--vision-provider", type=str, default=None, help="非交互覆盖 Vision provider")
    parser.add_argument("--vision-model", type=str, default=None, help="非交互覆盖 Vision 模型 ID")
    parser.add_argument("--vision-base-url", type=str, default=None, help="非交互覆盖 Vision Base URL")
    parser.add_argument("--vision-api-key-env", type=str, default=None, help="非交互覆盖 Vision API Key 环境变量名")
    parser.add_argument("--brain-provider", type=str, default=None, help="非交互覆盖 Brain provider")
    parser.add_argument("--brain-model", type=str, default=None, help="非交互覆盖 Brain 模型 ID")
    parser.add_argument("--brain-base-url", type=str, default=None, help="非交互覆盖 Brain Base URL")
    parser.add_argument("--brain-api-key-env", type=str, default=None, help="非交互覆盖 Brain API Key 环境变量名")
    parser.add_argument("--vision-workers", type=int, default=None, help="Vision/crop Vision 并发数，默认使用配置值")
    parser.add_argument("--brain-workers", type=int, default=None, help="Brain/refiner 页级并发数，默认使用配置值")
    parser.add_argument("--input-file", type=str, default=None, help="通过 MinerU API 解析的本地 PDF/Office/图片文件")
    parser.add_argument(
        "--input-files",
        nargs="+",
        default=None,
        help="通过 MinerU API 批量解析的本地文件列表，支持 PDF/Office/图片/HTML",
    )
    parser.add_argument("--input-folder", type=str, default=None, help="通过 MinerU API 批量解析的本地文件夹")
    parser.add_argument("--recursive", action="store_true", help="配合 --input-folder 递归扫描支持的文档文件")
    parser.add_argument("--mineru-url", type=str, default=None, help="通过 MinerU 精准解析 API 解析的远程文件 URL")
    parser.add_argument("--mineru-artifact-dir", type=str, default=None, help="已存在的 MinerU zip 解压/客户端输出目录")
    parser.add_argument("--page-ranges", type=str, default=None, help="MinerU 页码范围，例如 1-10 或 2,4-6")
    parser.add_argument(
        "--mineru-model-version",
        choices=["vlm", "pipeline", "MinerU-HTML"],
        default=None,
        help="MinerU 精准解析模型版本；默认使用 vlm，HTML 可显式选择 MinerU-HTML",
    )
    parser.add_argument(
        "--eval-fixtures",
        nargs="?",
        const=DEFAULT_EVAL_FIXTURE_DIR,
        default=None,
        help=f"运行离线评测 fixtures，然后退出（默认 {DEFAULT_EVAL_FIXTURE_DIR}）",
    )
    parser.add_argument(
        "--eval-output",
        type=str,
        default=DEFAULT_EVAL_OUTPUT_PATH,
        help=f"离线评测报告输出路径（默认 {DEFAULT_EVAL_OUTPUT_PATH}）",
    )
    parser.add_argument(
        "--fix-ocr-confusion",
        action="store_true",
        help="显式启用低密度 OCR 形近字符白名单修正（默认关闭）",
    )

    # 模型目录管理
    parser.add_argument("--list-models", action="store_true", help="列出可用模型，然后退出")
    parser.add_argument("--list-all-models", action="store_true", help="列出完整缓存模型目录（包含未验证候选）")
    parser.add_argument("--refresh-models", action="store_true", help="从阿里云文档刷新候选模型列表并缓存")
    parser.add_argument("--verify-models", action="store_true", help="用 API 验证模型可用性（需要 DASHSCOPE_API_KEY）")
    parser.add_argument("--region", type=str, default="cn-beijing", help="阿里云地域（默认 cn-beijing）")
    parser.add_argument("--base-url", type=str,
                        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
                        help="OpenAI 兼容端点")
    parser.add_argument("--model-cache", type=str,
                        default=".cache/aliyun_model_catalog.json",
                        help="模型缓存文件路径")
    parser.add_argument("--verify-limit", type=int, default=20, help="最多验证 N 个模型（默认 20）")
    parser.add_argument("--verify-sleep", type=float, default=0.3, help="验证间隔秒数（默认 0.3）")

    return parser.parse_args(argv)


def ensure_dependencies():
    required = [
        ("rich", "rich"),
        ("PIL", "Pillow"),
        ("dashscope", "dashscope"),
    ]
    for module_name, package_name in required:
        try:
            __import__(module_name)
        except ImportError:
            print(f"❌ 缺少依赖库 [{package_name}]。请运行: pip install {package_name}")
            return False
    return True


def build_config(args):
    vision_workers = _positive_optional_int(args.vision_workers, "--vision-workers") or AppConfig().vision_batch_workers
    brain_workers = _positive_optional_int(args.brain_workers, "--brain-workers") or AppConfig().brain_batch_workers
    config = AppConfig(
        session_name=args.name,
        output_folder=str(Path(args.output).resolve()),
        engine_mode=args.engine_mode,
        document_type=args.document_type,
        model_profile=args.model_profile,
        mineru_artifact_dir=args.mineru_artifact_dir,
        mineru_page_ranges=args.page_ranges,
        mineru_model_version=args.mineru_model_version or AppConfig().mineru_model_version,
        region=args.region,
        openai_base_url=args.base_url,
        model_cache_path=args.model_cache,
        verify_limit=args.verify_limit,
        verify_sleep=args.verify_sleep,
        vision_batch_workers=vision_workers,
        brain_batch_workers=brain_workers,
        list_models=args.list_models,
        list_all_models=args.list_all_models,
        refresh_models=args.refresh_models,
        verify_models=args.verify_models,
        fix_ocr_confusion=args.fix_ocr_confusion,
    )
    config = apply_model_profile(config, args.model_profile)
    return _apply_explicit_model_overrides(config, args)


def _positive_optional_int(value: int | None, label: str) -> int | None:
    if value is None:
        return None
    if value < 1:
        raise ValueError(f"{label} must be a positive integer.")
    return value


def _apply_explicit_model_overrides(config: AppConfig, args) -> AppConfig:
    updates = {}
    mapping = {
        "vision_provider": "vision_provider",
        "vision_model": "model_vision",
        "vision_base_url": "vision_base_url",
        "vision_api_key_env": "vision_api_key_env",
        "brain_provider": "brain_provider",
        "brain_model": "model_brain",
        "brain_base_url": "brain_base_url",
        "brain_api_key_env": "brain_api_key_env",
    }
    for arg_name, config_name in mapping.items():
        value = getattr(args, arg_name, None)
        if value:
            updates[config_name] = value
    if not updates:
        return config
    return replace(config, **updates)


def configure_stdio():
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _handle_model_commands(console, config: AppConfig):
    """处理 --list-models / --refresh-models / --verify-models 命令。"""
    from rich.panel import Panel
    from rich.table import Table

    from .aliyun_catalog import (
        fetch_model_ids_from_docs,
        records_to_cache_dict,
        save_cache,
        verify_models,
    )
    from .env import get_dashscope_api_key
    from .model_catalog import load_model_catalog, static_to_records

    # Step 1: 刷新（联网抓取文档）
    if config.refresh_models:
        console.print("[bold cyan]🔍 正在从阿里云文档抓取候选模型 ...[/]")
        dynamic = fetch_model_ids_from_docs()
        console.print(f"   从文档提取到 {len(dynamic)} 个候选模型")

        # 写入缓存
        cache_data = records_to_cache_dict(
            dynamic,
            source_urls=[],  # 由 fetch 内部记录
            region=config.region,
            base_url=config.openai_base_url,
        )
        save_cache(config.model_cache_path, cache_data)
        console.print(f"   [green]✅ 缓存已写入 {config.model_cache_abs_path}[/]")

    # Step 2: 验证
    if config.verify_models:
        api_key = get_dashscope_api_key()
        if not api_key:
            console.print("[bold red]❌ 验证模型需要 DASHSCOPE_API_KEY 环境变量。[/]")
            return

        records = load_model_catalog(
            prefer_cache=True,
            cache_path=config.model_cache_path,
            curated=not config.list_all_models,
        )
        console.print(
            f"[bold cyan]🧪 验证模型可用性（最多 {config.verify_limit} 个，间隔 {config.verify_sleep}s）...[/]"
        )
        console.print(f"   Base URL: {config.openai_base_url}")
        verify_models(
            records,
            api_key=api_key,
            base_url=config.openai_base_url,
            limit=config.verify_limit,
            sleep_interval=config.verify_sleep,
            console=console,
        )
        # 回写缓存（更新验证状态）
        cache_data = records_to_cache_dict(
            records,
            source_urls=[],
            region=config.region,
            base_url=config.openai_base_url,
        )
        save_cache(config.model_cache_path, cache_data)
        console.print(f"   [green]✅ 验证结果已写入缓存[/]")

    # Step 3: 列出
    if config.list_models or config.list_all_models:
        records = load_model_catalog(
            prefer_cache=True,
            cache_path=config.model_cache_path,
            curated=not config.list_all_models,
        )
        _display_models_table(console, records)


def _display_models_table(console, records, max_rows=120):
    """以 Rich 表格展示模型目录（含能力矩阵）。"""
    from rich.table import Table

    from .aliyun_catalog import filter_brain_models, filter_vision_models

    table = Table(title="📋 当前模型目录", show_header=True, header_style="bold magenta")
    table.add_column("Model ID", width=28)
    table.add_column("Provider", width=10)
    table.add_column("Vision", width=6, justify="center")
    table.add_column("OAI Txt", width=7)
    table.add_column("OAI Vis", width=7)
    table.add_column("DS Mul", width=7)
    table.add_column("Input ¥/M", justify="right", width=10)
    table.add_column("Output ¥/M", justify="right", width=10)
    table.add_column("Price Src", width=12)
    table.add_column("Region", width=10)

    def _cap_icon(status: str) -> str:
        return {"ok": "✅", "failed": "❌", "skipped": "⏭"}.get(status, "·")

    display_records = records[:max_rows]
    for rec in display_records:
        vis = "✅" if rec.supports_vision is True else ("❌" if rec.supports_vision is False else "?")
        inp = f"{rec.input_price:.3g}" if rec.input_price is not None else "?"
        out = f"{rec.output_price:.3g}" if rec.output_price is not None else "?"
        src = rec.price_source or "-"
        region = rec.price_region or "-"

        table.add_row(
            rec.model_id,
            rec.provider,
            vis,
            _cap_icon(rec.openai_text_status),
            _cap_icon(rec.openai_vision_status),
            _cap_icon(rec.dashscope_multimodal_status),
            inp,
            out,
            src,
            region,
        )

    console.print(table)

    # 分类统计
    visions = filter_vision_models(records)
    brains = filter_brain_models(records)
    vision_ok = sum(1 for r in visions if r.openai_vision_status == "ok" or r.dashscope_multimodal_status == "ok")
    text_ok = sum(1 for r in brains if r.openai_text_status == "ok")
    priced = sum(1 for r in records if r.input_price is not None)
    console.print(
        f"[dim]共 {len(records)} 个模型 | "
        f"当前显示: {len(display_records)} | "
        f"Vision 候选: {len(visions)} (可用: {vision_ok}) | "
        f"Brain 候选: {len(brains)} (文本通: {text_ok}) | "
        f"有价格: {priced}[/]"
    )
    if len(records) > len(display_records):
        console.print("[dim]完整目录保存在模型缓存 JSON 中；交互 UI 默认只使用精选目录。[/]")


def main(argv=None):
    configure_stdio()
    args = parse_args(argv)
    if args.eval_fixtures:
        from .eval import run_offline_eval

        report = run_offline_eval(args.eval_fixtures, args.eval_output)
        summary = report["summary"]
        print(
            f"offline eval: {summary['cases_passed']}/{summary['cases_total']} passed, "
            f"report={report['output_path']}"
        )
        return 0 if summary["cases_failed"] == 0 else 1

    config = build_config(args)
    args = _maybe_prompt_initial_mode(args)
    config = build_config(args)
    if _is_mineru_cli_mode(args):
        return _run_mineru_cli(args, config)

    if not ensure_dependencies():
        return 1

    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )

    from .cost import show_cost_estimation
    from .files import check_runtime_env, ensure_input_folder, setup_logger
    from .model_settings import configure_models
    from .pipeline import process_single_docpage_task
    from .session import interactive_setup

    console = Console()

    # ── 模型目录管理模式 ──
    any_model_cmd = config.list_models or config.list_all_models or config.refresh_models or config.verify_models
    if any_model_cmd:
        _handle_model_commands(console, config)
        return 0

    input_ready, msg = ensure_input_folder(config)
    if not input_ready:
        console.print(msg)
        return 1

    config = configure_models(console, config)
    final_key, msg = check_runtime_env(config)
    if not final_key:
        console.print(msg)
        return 1

    logger, log_file_path = setup_logger(config)
    console.print(
        Panel(
            f"""[bold]V10 终极版 (Parallel Brain / Raw Context)[/]
    工具: [cyan]DocPage2MD[/]
    会话: [magenta]{config.session_name}[/] | API Key: 已设置
    -------------------------------------------------------
    Step 1 引擎: [cyan]{config.vision_provider}:{config.model_vision}[/] (并发: {config.vision_batch_workers})
    Step 2 引擎: [green]{config.brain_provider}:{config.model_brain}[/] (并发: {config.brain_batch_workers})
    -------------------------------------------------------
    输出: {config.output_folder}
    日志: {log_file_path}
    """,
            title="配置确认",
            border_style="green",
        )
    )

    tasks_config = interactive_setup(console, final_key, config)
    if not tasks_config:
        return 0

    show_cost_estimation(console, tasks_config, config)
    console.print("[dim]说明：终端 ETA 由 Rich 根据当前进度估算，API 延迟波动较大；准确耗时请以 log 中的 Stage 耗时为准。[/]")
    if input("👉 确认开始任务吗？(y/n) [默认为 y]: ").strip().lower() == "n":
        print("已取消。")
        return 0

    msg_manager = Manager()
    msg_queue = msg_manager.Queue()

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.fields[doc_name]}", justify="right"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        TextColumn("{task.fields[status]}"),
    )

    print("\n")

    with Live(progress, console=console, refresh_per_second=10):
        for doc_name in tasks_config:
            task_id = progress.add_task(
                "waiting...",
                total=100,
                doc_name=doc_name,
                status="准备中...",
            )
            tasks_config[doc_name]["task_id"] = task_id

        with ProcessPoolExecutor(max_workers=config.max_docpage_workers) as executor:
            futures = [
                executor.submit(process_single_docpage_task, doc_name, task_config, msg_queue, config)
                for doc_name, task_config in tasks_config.items()
            ]

            finished_tasks = 0
            total_tasks = len(tasks_config)

            while finished_tasks < total_tasks:
                try:
                    while not msg_queue.empty():
                        msg_type, *message_args = msg_queue.get_nowait()

                        if msg_type == "init_task":
                            task_id, total = message_args
                            progress.update(task_id, total=total)
                        elif msg_type == "advance":
                            task_id, steps = message_args
                            progress.advance(task_id, steps)
                        elif msg_type == "status":
                            task_id, text = message_args
                            progress.update(task_id, status=text)
                        elif msg_type == "log":
                            logger.info(message_args[0])

                    done_count = sum(1 for future in futures if future.done())
                    if done_count > finished_tasks:
                        finished_tasks = done_count
                    if finished_tasks == total_tasks and msg_queue.empty():
                        break
                    time.sleep(0.1)
                except queue.Empty:
                    pass
                except Exception as e:
                    logger.error(f"Main Loop Error: {e}")
                    break

    console.print(Panel("[bold green]✨ 所有双阶段思考任务处理完毕！[/]", expand=False))
    return 0


def _is_mineru_cli_mode(args) -> bool:
    return bool(
        args.mineru_artifact_dir
        or args.mineru_url
        or args.input_files
        or args.input_folder
        or (args.input_file and args.engine_mode in {"mineru_only", "hybrid"})
    )


def _maybe_prompt_initial_mode(args):
    if not sys.stdin.isatty():
        return args
    if args.mineru_artifact_dir or args.mineru_url or args.input_file or args.input_files or args.input_folder:
        return args
    if args.engine_mode != "vision_only" or args.list_models or args.list_all_models or args.refresh_models or args.verify_models:
        return args

    print("\n处理模式选择")
    print("  1. 手写矢量笔记（推荐 hybrid：MinerU layout/crop + docpage2md/Brain 精修）")
    print("  2. 论文 PDF（推荐 mineru_only 或 hybrid 轻精修）")
    print("  3. 截图/屏拍小题（推荐 vision_only）")
    print("  4. 复杂公式图表 PPT（推荐 hybrid，可选 accurate 模型档位）")
    print("  5. 自定义")
    doc_choice = input(">> 文档类型 [默认 1]: ").strip() or "1"
    doc_type, recommended_mode, recommended_profile = {
        "1": ("handwritten_notes", "hybrid", "balanced"),
        "2": ("paper_pdf", "mineru_only", "balanced"),
        "3": ("screenshot_question", "vision_only", "balanced"),
        "4": ("complex_ppt", "hybrid", "accurate"),
        "5": ("custom", "vision_only", args.model_profile),
    }.get(doc_choice, ("handwritten_notes", "hybrid", "balanced"))

    mode = input(f">> 处理模式 mineru_only / vision_only / hybrid [默认 {recommended_mode}]: ").strip() or recommended_mode
    if mode not in {"mineru_only", "vision_only", "hybrid"}:
        mode = recommended_mode
    profile = input(f">> 模型档位 cheap / balanced / accurate / manual [默认 {recommended_profile}]: ").strip() or recommended_profile
    if profile not in {"cheap", "balanced", "accurate", "manual"}:
        profile = recommended_profile

    updated = argparse.Namespace(**vars(args))
    updated.document_type = doc_type
    updated.engine_mode = mode
    updated.model_profile = profile
    if mode == "vision_only":
        return updated

    print("\nMinerU 输入来源")
    print("  1. 已解压/客户端输出的 MinerU artifact 目录")
    print("  2. 本地 PDF/Office/图片文件，通过 MinerU API 上传解析")
    print("  3. 远程文件 URL，通过 MinerU API 解析")
    print("  4. 本地文件夹，批量通过 MinerU API 上传解析")
    print("  5. 多个本地文件，批量通过 MinerU API 上传解析")
    source_choice = input(">> 输入来源 [默认 2]: ").strip() or "2"
    if source_choice == "1":
        updated.mineru_artifact_dir = input(">> MinerU artifact 目录路径: ").strip() or None
    elif source_choice == "3":
        updated.mineru_url = input(">> 远程文件 URL: ").strip() or None
    elif source_choice == "4":
        updated.input_folder = input(">> 本地文件夹路径: ").strip() or None
        recursive = input(">> 是否递归扫描子文件夹？(y/n) [默认 n]: ").strip().lower()
        updated.recursive = recursive == "y"
    elif source_choice == "5":
        raw_files = input(">> 多个本地文件路径，用英文分号 ; 分隔: ").strip()
        updated.input_files = [item.strip() for item in raw_files.split(";") if item.strip()] or None
    else:
        updated.input_file = input(">> 本地文件路径: ").strip() or None
    page_ranges = input(">> 页码范围 [回车=全部，例如 1-10 或 2,4-6]: ").strip()
    if page_ranges:
        updated.page_ranges = page_ranges
    return updated


def _run_mineru_cli(args, config: AppConfig) -> int:
    from .mineru_cache import cache_key_for_source, task_cache_dir, unzip_mineru_result, write_task_manifest
    from .mineru_client import MinerUError, MinerUClient
    from .mineru_pipeline import process_mineru_artifact_task

    mode = args.engine_mode if args.engine_mode in {"mineru_only", "hybrid"} else "mineru_only"
    config = replace(config, engine_mode=mode)
    doc_name = None if args.name == "default" else args.name
    run_logger = RunLogger(_mineru_process_log_path(config, args, doc_name), echo=True)
    safe_progress(
        run_logger,
        (
            f"MinerU mode start: mode={mode}, profile={config.model_profile}, "
            f"mineru_model={config.mineru_model_version}, page_ranges={args.page_ranges or 'all'}, "
            f"token_env={config.mineru_api_token_env}"
        ),
    )
    safe_progress(
        run_logger,
        (
            f"Models: vision={config.vision_provider}:{config.model_vision} "
            f"brain={config.brain_provider}:{config.model_brain}"
        ),
    )

    if args.mineru_artifact_dir:
        safe_progress(run_logger, f"Processing existing MinerU artifact: {args.mineru_artifact_dir}")
        result = process_mineru_artifact_task(
            args.mineru_artifact_dir,
            config,
            doc_name=doc_name,
            engine_mode=mode,
            source_path=args.input_file,
            progress=run_logger,
        )
        print(f"MinerU artifact 处理完成：共 {result['page_count']} 页 -> {result['output_dir']}")
        return 0

    try:
        local_files = _resolve_mineru_local_files(args)
    except ValueError as exc:
        print(str(exc))
        return 2

    if not args.mineru_url and not local_files:
        print("MinerU 主流程缺少输入来源：请指定 --mineru-artifact-dir、--mineru-url、--input-file、--input-files 或 --input-folder。")
        return 2
    try:
        client = MinerUClient(config, progress=run_logger)

        if args.mineru_url:
            safe_progress(run_logger, f"Submitting remote URL to MinerU: {_safe_source_label(args.mineru_url)}")
            submit = client.submit_url(args.mineru_url, page_ranges=args.page_ranges)
            task_id = submit["data"]["task_id"]
            safe_progress(run_logger, f"MinerU task submitted: task_id={task_id}")
            result = client.wait_for_task(task_id)
            processed = _download_and_process_mineru_result(
                client,
                result,
                source=args.mineru_url,
                config=config,
                args=args,
                mode=mode,
                doc_name=doc_name,
                task_ref={"task_id": task_id, "batch_id": None},
                progress=run_logger,
            )
            print(f"MinerU API 处理完成：共 {processed['page_count']} 页 -> {processed['output_dir']}")
            return 0

        safe_progress(
            run_logger,
            "Submitting local files to MinerU: "
            + ", ".join(f"{path.name} ({path.stat().st_size} bytes)" for path in local_files),
        )
        batch_id = client.submit_local_files(local_files, page_ranges=args.page_ranges)
        safe_progress(run_logger, f"MinerU batch submitted: batch_id={batch_id}, files={len(local_files)}")
        results = client.wait_for_batch_results(batch_id, expected_count=len(local_files))
        source_by_result = _match_batch_results_to_sources(results, local_files)
        processed_count = 0
        for index, result in enumerate(results):
            source = source_by_result[index]
            processed = _download_and_process_mineru_result(
                client,
                result,
                source=str(source),
                config=config,
                args=args,
                mode=mode,
                doc_name=doc_name if len(local_files) == 1 else None,
                task_ref={"task_id": result.task_id, "batch_id": batch_id},
                progress=run_logger,
            )
            processed_count += 1
            print(f"MinerU API 处理完成：共 {processed['page_count']} 页 -> {processed['output_dir']}")
        print(f"MinerU 批量任务完成：{processed_count}/{len(local_files)} 个文件")
        return 0
    except MinerUError as exc:
        safe_progress(run_logger, f"MinerU API failed: {exc}")
        print(f"MinerU API 失败：{exc}")
        return 1


def _download_and_process_mineru_result(
    client,
    result,
    *,
    source: str,
    config: AppConfig,
    args,
    mode: str,
    doc_name: str | None,
    task_ref: dict[str, str | None],
    progress=None,
) -> dict:
    from .mineru_cache import cache_key_for_source, task_cache_dir, unzip_mineru_result, write_task_manifest
    from .mineru_pipeline import process_mineru_artifact_task

    progress = _per_document_progress(config, args, source, doc_name, progress)
    cache_key = cache_key_for_source(source, page_ranges=args.page_ranges, model_version=config.mineru_model_version)
    cache_dir = task_cache_dir(config.output_folder, cache_key)
    zip_path = cache_dir / "mineru_result.zip"
    artifact_dir = cache_dir / "artifact"
    cache_dir.mkdir(parents=True, exist_ok=True)

    safe_progress(progress, f"Downloading MinerU zip: source={_safe_source_label(source)}, cache_key={cache_key[:12]}")
    client.download_zip(result.full_zip_url or "", zip_path)
    safe_progress(progress, f"MinerU zip downloaded: {zip_path} ({zip_path.stat().st_size} bytes)")
    safe_progress(progress, f"Unzipping MinerU result: {artifact_dir}")
    unzip_mineru_result(zip_path, artifact_dir)
    safe_progress(progress, "Writing MinerU task manifest")
    write_task_manifest(
        artifact_dir,
        source=source,
        page_ranges=args.page_ranges,
        model_version=config.mineru_model_version,
        full_zip_url=result.full_zip_url,
        file_name=getattr(result, "file_name", None),
        data_id=getattr(result, "data_id", None),
        **task_ref,
    )
    safe_progress(progress, f"Processing MinerU artifact into Markdown: {artifact_dir}")
    return process_mineru_artifact_task(
        artifact_dir,
        config,
        doc_name=doc_name,
        engine_mode=mode,
        source_path=source,
        progress=progress,
    )


def _per_document_progress(config: AppConfig, args, source: str, doc_name: str | None, progress):
    output_name = doc_name or _source_output_name(source)
    doc_log_path = Path(config.output_folder) / output_name / "process.log"
    shared_log_path = _mineru_process_log_path(config, args, doc_name)
    if progress is None or doc_log_path.resolve() == shared_log_path.resolve():
        return progress
    doc_logger = RunLogger(doc_log_path, echo=False)

    def tee(message: str) -> None:
        safe_progress(progress, message)
        safe_progress(doc_logger, message)

    return tee


def _resolve_mineru_local_files(args) -> list[Path]:
    files: list[Path] = []
    if args.input_file:
        files.append(_validate_explicit_mineru_file(args.input_file))
    if args.input_files:
        files.extend(_validate_explicit_mineru_file(item) for item in args.input_files)
    if args.input_folder:
        folder = Path(args.input_folder)
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"MinerU input folder does not exist: {folder}")
        iterator = folder.rglob("*") if args.recursive else folder.glob("*")
        files.extend(path for path in iterator if path.is_file() and _is_mineru_supported_file(path))
    deduped: dict[str, Path] = {}
    for path in files:
        deduped[str(path.resolve()).lower()] = path.resolve()
    return sorted(deduped.values(), key=lambda path: str(path).lower())


def _validate_explicit_mineru_file(path: str | Path) -> Path:
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        raise ValueError(f"MinerU input file does not exist: {file_path}")
    if not _is_mineru_supported_file(file_path):
        suffixes = ", ".join(sorted(MINERU_SUPPORTED_SUFFIXES))
        raise ValueError(f"Unsupported MinerU input file type: {file_path.suffix}. Supported: {suffixes}")
    return file_path.resolve()


def _is_mineru_supported_file(path: Path) -> bool:
    return path.suffix.lower() in MINERU_SUPPORTED_SUFFIXES


def _match_batch_results_to_sources(results, source_files: list[Path]) -> list[Path]:
    remaining_by_name: dict[str, list[Path]] = {}
    for path in source_files:
        remaining_by_name.setdefault(path.name.lower(), []).append(path)
    matched: list[Path] = []
    for index, result in enumerate(results):
        file_name = str(getattr(result, "file_name", "") or "").lower()
        candidates = remaining_by_name.get(file_name)
        if candidates:
            matched.append(candidates.pop(0))
            continue
        matched.append(source_files[min(index, len(source_files) - 1)])
    return matched


def _mineru_process_log_path(config: AppConfig, args, doc_name: str | None) -> Path:
    return Path(config.output_folder) / _mineru_log_output_name(args, doc_name) / "process.log"


def _mineru_log_output_name(args, doc_name: str | None) -> str:
    if doc_name:
        return doc_name
    if args.input_file:
        return Path(args.input_file).stem
    if args.mineru_artifact_dir:
        return Path(args.mineru_artifact_dir).name
    if args.mineru_url:
        path = urllib.parse.urlsplit(args.mineru_url).path
        stem = Path(path).stem
        return stem or "mineru_url_task"
    if args.input_folder:
        return f"{Path(args.input_folder).name}_batch"
    if args.input_files:
        return "mineru_batch"
    return "mineru_task"


def _source_output_name(source: str) -> str:
    parsed = urllib.parse.urlsplit(str(source))
    if parsed.scheme and parsed.netloc:
        stem = Path(parsed.path).stem
        return stem or "mineru_url_task"
    return Path(str(source)).stem or "mineru_task"


def _safe_source_label(source: str) -> str:
    parsed = urllib.parse.urlsplit(str(source))
    if parsed.scheme and parsed.netloc:
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, "", ""))
    return str(source)
