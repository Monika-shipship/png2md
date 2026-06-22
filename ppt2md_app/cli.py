import argparse
import queue
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Manager
from pathlib import Path

from .config import AppConfig
from .eval import DEFAULT_EVAL_FIXTURE_DIR, DEFAULT_EVAL_OUTPUT_PATH


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="DocPage2MD (document-page images to Markdown)")
    parser.add_argument("-n", "--name", type=str, default="default", help="任务会话名称")
    parser.add_argument("-o", "--output", type=str, default="./markdown_output", help="输出目录路径")
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
    return AppConfig(
        session_name=args.name,
        output_folder=str(Path(args.output).resolve()),
        region=args.region,
        openai_base_url=args.base_url,
        model_cache_path=args.model_cache,
        verify_limit=args.verify_limit,
        verify_sleep=args.verify_sleep,
        list_models=args.list_models,
        list_all_models=args.list_all_models,
        refresh_models=args.refresh_models,
        verify_models=args.verify_models,
        fix_ocr_confusion=args.fix_ocr_confusion,
    )


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
    from .pipeline import process_single_ppt_task
    from .session import interactive_setup

    config = build_config(args)
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
        TextColumn("[bold blue]{task.fields[ppt_name]}", justify="right"),
        BarColumn(),
        TaskProgressColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        TextColumn("{task.fields[status]}"),
    )

    print("\n")

    with Live(progress, console=console, refresh_per_second=10):
        for ppt_name in tasks_config:
            task_id = progress.add_task(
                "waiting...",
                total=100,
                ppt_name=ppt_name,
                status="准备中...",
            )
            tasks_config[ppt_name]["task_id"] = task_id

        with ProcessPoolExecutor(max_workers=config.max_ppt_workers) as executor:
            futures = [
                executor.submit(process_single_ppt_task, ppt_name, task_config, msg_queue, config)
                for ppt_name, task_config in tasks_config.items()
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
