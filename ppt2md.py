import os
import re
import time
import json
import logging
import datetime
import argparse
import sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from multiprocessing import Manager
import queue

# === 尝试导入 rich ===
try:
    from rich.progress import (
        Progress, SpinnerColumn, TextColumn, BarColumn,
        TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn
    )
    from rich.live import Live
    from rich.panel import Panel
    from rich.console import Console
except ImportError:
    print("❌ 缺少依赖库 [rich]。请运行: pip install rich")
    exit(1)

import dashscope
from dashscope import Generation, MultiModalConversation

# ================= 配置区域 =================
# 视觉模型：负责 OCR 和 读图 (Step 1)
MODEL_VISION = "qwen3-vl-plus"
# 文本模型：负责 逻辑修正 和 格式化 (Step 2)
MODEL_BRAIN = "qwen-plus"

INPUT_FOLDER = "./ppt_images"      
OUTPUT_FOLDER = "./markdown_output" 
LOG_FOLDER = "./log"

# 全局并发控制 (同时处理多少个 PPT 文件夹)
MAX_PPT_WORKERS = 5

# 【关键参数】单任务内部并发数 (Step 1 视觉提取的并发度)
# 因为 Vision 模型 TPM 很大，这里可以设高一点，比如 5-10
VISION_BATCH_WORKERS = 10

# 思考预算 (仅用于视觉模型)
THINKING_BUDGET = 1024 

# === 命令行参数解析 ===
parser = argparse.ArgumentParser(description="PPT转Markdown工具 (双阶段流水线版)")
parser.add_argument("-n", "--name", type=str, default="default", help="任务会话名称")
parser.add_argument("-o", "--output", type=str, default="./markdown_output", help="输出目录路径")
args = parser.parse_args()

SESSION_FILE = f"session_{args.name}.json"
CURRENT_SESSION_NAME = args.name
OUTPUT_FOLDER = str(Path(args.output).resolve())
INPUT_FOLDER_ABS = str(Path(INPUT_FOLDER).resolve())

# ================= Prompt 模板 (双阶段) =================

# --- 阶段一：视觉提取 Prompt ---
# 目标：精准 OCR，不要遗漏，不要过度总结。只做“眼睛”。
PROMPT_STAGE_1_VISION = r"""
任务：请对这张 PPT 图片进行详尽的视觉提取。

要求：
1. **OCR 识别**：逐字提取图片中的所有文本，包括标题、正文、角标。
2. **公式识别**：如果看到数学/物理公式，请直接转换为 LaTeX 格式（行内$...$，行间$$...$$）。
3. **视觉描述**：描述图片的布局、图表内容（如果是架构图或数据图，请详细描述数据关系）。

请直接输出提取到的内容，**不需要**整理成 Markdown 格式，**不需要**解释，保持原始信息的丰富度。
"""

# --- 阶段二：逻辑重组 Prompt ---
# 目标：清洗数据，修正 OCR 错误，维护上下文，输出最终 Markdown。
PROMPT_STAGE_2_BRAIN = r"""
你是一个专业的学术助教。你的任务是将 PPT 的“原始识别数据”重组为完美的 Markdown 笔记。

【输入信息】
1. **上一页 Context**：{context_block}
2. **当前页原始数据 (Raw Data)**：
{raw_data}

【任务要求】
1. **错误修正**：利用上下文修正 OCR 错误（例如将 Vmax 修正为 $V_{{max}}$，将错误的符号根据物理语境修正）。
2. **格式化**：将内容整理为结构清晰的 Markdown。
   - 标题：# Slide {slide_no}
   - 公式：使用标准 LaTeX。
   - 视觉描述：放在 `## Figure Description` 章节。
3. **上下文更新**：在 Markdown 的最后，生成一个新的隐藏状态块 <CTX>...</CTX>，用于传递给下一页。

【Context 更新格式 (必须严格遵守 JSON)】
<CTX>
{{
  "topic": "本页核心主题",
  "keywords": ["关键词1", "关键词2"],
  "summary": "本页知识点摘要",
  "last_formula_context": "记录最后一个公式的含义，防止下一页符号歧义"
}}
</CTX>

请直接输出最终的 Markdown 内容。
"""

# ================= 辅助函数 =================

def setup_logger(session_name):
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_FOLDER, f"log_{session_name}_{timestamp}.log")
    logger = logging.getLogger(f"PPT2MD_{session_name}")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - [%(processName)s] - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger, log_file

def check_env():
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key and dashscope.api_key is None:
        return None, "❌ 未检测到 API Key。请设置环境变量 DASHSCOPE_API_KEY。"
    final_key = api_key if api_key else dashscope.api_key
    if not os.path.exists(INPUT_FOLDER):
        try:
            os.makedirs(INPUT_FOLDER)
            return None, f"⚠️ 输入文件夹 {INPUT_FOLDER} 不存在，已创建。"
        except:
            return None, f"❌ 无法创建文件夹 {INPUT_FOLDER}。"
    return final_key, "环境检查通过"

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s.name)]

def scan_ppt_folders(root_folder):
    root = Path(root_folder)
    if not root.exists(): return {}
    tasks = {}
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    for entry in root.iterdir():
        if entry.is_dir():
            images = [f for f in entry.iterdir() if f.suffix.lower() in exts]
            if images:
                images.sort(key=natural_sort_key)
                tasks[entry.name] = [str(img.absolute()) for img in images]
    return tasks

def extract_context(text):
    pattern = r"<CTX>(.*?)</CTX>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).replace("```json", "").replace("```", "").strip()
    return "No context from previous page."

def read_context_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            ctx = extract_context(content)
            if "No context" not in ctx: return ctx
    except: pass
    return "Resumed session. Context lost."

def merge_markdowns(ppt_output_dir, ppt_name):
    p = Path(ppt_output_dir)
    final_path = p / f"{ppt_name}_FULL.md"
    md_files = sorted(p.glob("Slide_*.md"), key=natural_sort_key)
    if not md_files: return
    with open(final_path, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# {ppt_name} 汇总\n\n> 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for md_file in md_files:
            with open(md_file, 'r', encoding='utf-8') as infile:
                outfile.write(infile.read())
                outfile.write("\n\n---\n\n")

# ================= 交互与状态管理 =================

def load_session():
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return None
    return None

def save_session(tasks_config):
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks_config, f, indent=2, ensure_ascii=False)

def parse_range_string(range_str, max_len):
    if not range_str or range_str.lower() == 'all': return 0, max_len
    try:
        if '-' in range_str:
            start, end = range_str.split('-')
            start = int(start) - 1 
            if end.lower() == 'end': end = max_len
            else: end = int(end)
            return max(0, start), min(end, max_len)
        else:
            idx = int(range_str) - 1
            return max(0, idx), min(idx + 1, max_len)
    except: return 0, max_len

def interactive_setup(console, api_key):
    console.print(Panel.fit(f"🔍 扫描中... (会话: [bold magenta]{CURRENT_SESSION_NAME}[/])", style="bold blue"))
    all_tasks = scan_ppt_folders(INPUT_FOLDER)
    if not all_tasks:
        console.print(f"[bold red]❌ 未在 {INPUT_FOLDER} 中发现子文件夹。[/]")
        return None

    ppt_names = list(all_tasks.keys())
    old_session = load_session()
    if old_session:
        console.print("\n[bold yellow]📢 发现断点记录！[/]")
        choice = input("👉 是否继续？(y/n) [默认为 y]: ").strip().lower()
        if choice != 'n':
            for k in old_session: old_session[k]["api_key"] = api_key
            return old_session

    console.print("\n[bold green]📂 发现以下 PPT:[/]")
    for i, name in enumerate(ppt_names):
        count = len(all_tasks[name])
        console.print(f"  [[bold cyan]{i+1}[/]] {name} ([yellow]{count} 页[/])")
    
    selection = input("\n👉 选择 PPT (如 1,3 | a): ").strip()
    selected_names = []
    if selection.lower() == 'a':
        selected_names = ppt_names
    else:
        try:
            for idx in [int(x) for x in selection.split(',') if x.strip()]:
                if 1 <= idx <= len(ppt_names): selected_names.append(ppt_names[idx-1])
        except: return None

    if not selected_names: return None
    final_config = {}
    console.print("\n⚙️  [bold]配置范围 (回车=全选):[/]")
    for name in selected_names:
        total = len(all_tasks[name])
        range_input = input(f"   📘 [{name}] (共{total}页): ").strip()
        start, end = parse_range_string(range_input, total)
        final_config[name] = {
            "images": all_tasks[name],
            "range_start": start,
            "range_end": end,
            "task_id": None,
            "api_key": api_key
        }
    
    save_session(final_config)
    return final_config

# ================= 阶段一：原子任务 (视觉提取) =================

# ================= 阶段一：原子任务 (视觉提取) =================

def run_stage_1_vision(img_path, slide_no, ppt_name, msg_queue):
    """
    Step 1 Worker: 调用 VL 模型提取 Raw Data (带强力重试机制)
    """
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            messages = [{
                "role": "user",
                "content": [
                    {"image": f"file://{img_path}"},
                    {"text": PROMPT_STAGE_1_VISION}
                ]
            }]
            
            # 调用 VL 模型
            response = MultiModalConversation.call(
                model=MODEL_VISION,
                messages=messages,
                enable_thinking=True,
                thinking_budget=THINKING_BUDGET
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                if isinstance(content, list):
                    text_content = "".join([c['text'] for c in content if 'text' in c])
                else:
                    text_content = content
                
                return {
                    "success": True, 
                    "slide_no": slide_no, 
                    "raw_text": text_content,
                    "msg": "Vision OK"
                }
            else:
                # 遇到 AccessDenied 直接死，不重试
                if "AccessDenied" in str(response.code):
                    raise RuntimeError("AccessDenied")
                
                # 其他 API 错误，抛出异常以触发 retry
                raise Exception(f"API Code {response.code}: {response.message}")
                
        except Exception as e:
            err_msg = str(e)
            if "AccessDenied" in err_msg:
                # 致命错误，透传出去
                raise e
            
            # 如果是最后一次尝试，返回失败
            if attempt == max_retries - 1:
                return {"success": False, "slide_no": slide_no, "error": f"重试3次失败: {err_msg}"}
            
            # 否则，打印日志并等待 (指数退避: 2秒, 4秒...)
            wait_time = (attempt + 1) * 3
            msg_queue.put(("log", f"[{ppt_name}] P{slide_no} 网络波动({attempt+1}/{max_retries})，等待 {wait_time}s..."))
            time.sleep(wait_time)

# ================= 阶段二：原子任务 (逻辑重组) =================

def run_stage_2_brain(raw_data, context, slide_no):
    """
    Step 2 Worker: 调用 Text 模型 (qwen-plus) 进行重组
    """
    try:
        filled_prompt = PROMPT_STAGE_2_BRAIN.format(
            context_block=context,
            raw_data=raw_data,
            slide_no=slide_no
        )
        
        messages = [{'role': 'user', 'content': filled_prompt}]
        
        # 调用 文本模型 (qwen-plus) - 极速且便宜
        response = Generation.call(
            model=MODEL_BRAIN,
            messages=messages,
            result_format='message'
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            return f"Brain Error: {response.code}"
            
    except Exception as e:
        return f"Brain Exception: {str(e)}"

# ================= 核心流水线控制 =================

def process_single_ppt_task(ppt_name, config, msg_queue):
    """
    双阶段流水线控制器
    """
    # 1. 注入 Key
    task_key = config.get("api_key")
    if task_key: dashscope.api_key = task_key
    else: dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    
    images_paths = config["images"]
    start_idx = config["range_start"]
    end_idx = config["range_end"]
    task_id = config["task_id"]
    
    target_images = images_paths[start_idx:end_idx]
    total_slides = len(target_images)
    
    # 目录准备
    ppt_root = Path(OUTPUT_FOLDER) / ppt_name
    temp_dir = ppt_root / "temp_raw_vision" # 存放 Step 1 的中间结果
    os.makedirs(ppt_root, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    msg_queue.put(("log", f"[{ppt_name}] 双阶段任务启动。图片: {total_slides}张"))
    msg_queue.put(("init_task", task_id, total_slides)) # UI 显示总页数

    # === Step 1: 暴力并发视觉提取 (Concurrent Vision) ===
    msg_queue.put(("status", task_id, f"[cyan]Step 1: 视觉提取 (并发{VISION_BATCH_WORKERS})..."))
    
    # 使用 ThreadPoolExecutor 在进程内实现高并发 I/O
    vision_futures = {}
    completed_vision = 0
    
    # 用于 Step 2 的数据缓存
    raw_data_map = {} 
    
    with ThreadPoolExecutor(max_workers=VISION_BATCH_WORKERS) as executor:
        # 提交所有 Step 1 任务
        for i, img_path in enumerate(target_images):
            actual_slide_no = start_idx + i + 1
            raw_file = temp_dir / f"Raw_{actual_slide_no:02d}.json"
            
            # 断点检查：如果 Raw 数据已存在，直接读取
            if raw_file.exists():
                try:
                    with open(raw_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        raw_data_map[actual_slide_no] = data['raw_text']
                        completed_vision += 1
                        msg_queue.put(("log", f"[{ppt_name}] P{actual_slide_no} 视觉缓存命中"))
                        continue # 跳过 API 调用
                except: pass

            # 提交新任务
            future = executor.submit(run_stage_1_vision, img_path, actual_slide_no, ppt_name, msg_queue)
            vision_futures[future] = actual_slide_no

        # 等待所有视觉任务完成 (或者我们也可以做成流式，但为了 Context 简单，先做成批处理)
        # 这里为了 UI 友好，我们实时收集完成情况
        for future in as_completed(vision_futures):
            s_no = vision_futures[future]
            try:
                res = future.result()
                if res['success']:
                    raw_text = res['raw_text']
                    raw_data_map[s_no] = raw_text
                    # 保存中间结果，方便下次断点
                    raw_file = temp_dir / f"Raw_{s_no:02d}.json"
                    with open(raw_file, 'w', encoding='utf-8') as f:
                        json.dump(res, f, ensure_ascii=False)
                    
                    # msg_queue.put(("log", f"[{ppt_name}] P{s_no} 视觉完成"))
                else:
                    msg_queue.put(("log", f"[{ppt_name}] P{s_no} 视觉失败: {res.get('error')}"))
                    raw_data_map[s_no] = "[Vision Failed]" # 占位，防止 Step 2 崩溃
            except RuntimeError as e:
                # 捕获致命错误
                msg_queue.put(("status", task_id, "[bold red]权限拒绝!"))
                raise e
            except Exception as e:
                msg_queue.put(("log", f"[{ppt_name}] P{s_no} 异常: {e}"))

    msg_queue.put(("log", f"[{ppt_name}] Step 1 视觉提取全部完成。开始 Step 2..."))

    # === Step 2: 串行逻辑重组 (Serial Brain) ===
    # 这一步必须按顺序，因为要维护 Context
    
    current_context = "Starting processing. No prior context."
    # 尝试读取第一页之前的 Context (如果是中间续传)
    if start_idx > 0:
        prev_md = ppt_root / f"Slide_{start_idx:02d}.md"
        if prev_md.exists():
            current_context = read_context_from_file(prev_md)

    for i in range(total_slides):
        actual_slide_no = start_idx + i + 1
        output_path = ppt_root / f"Slide_{actual_slide_no:02d}.md"
        
        # UI 更新
        msg_queue.put(("status", task_id, f"[green]Step 2: 逻辑重组 P{actual_slide_no}..."))
        
        # 断点检测 Step 2
        if output_path.exists() and output_path.stat().st_size > 100:
            current_context = read_context_from_file(output_path)
            msg_queue.put(("advance", task_id, 1)) # 进度+1
            continue

        # 获取对应的 Raw Data
        raw_text = raw_data_map.get(actual_slide_no, "No vision data.")
        
        # 调用大脑
        final_markdown = run_stage_2_brain(raw_text, current_context, actual_slide_no)
        
        # 保存
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_markdown)
        
        # 更新 Context
        ctx = extract_context(final_markdown)
        if "No context" not in ctx:
            current_context = ctx
            
        msg_queue.put(("log", f"[{ppt_name}] P{actual_slide_no} 最终完成"))
        msg_queue.put(("advance", task_id, 1)) # 进度+1

    msg_queue.put(("status", task_id, "正在合并..."))
    merge_markdowns(ppt_root, ppt_name)
    msg_queue.put(("log", f"[{ppt_name}] 全部流程结束"))
    return f"{ppt_name} Done"

# ================= 主程序入口 =================
def main():
    console = Console()
    final_key, msg = check_env()
    if not final_key:
        console.print(msg)
        return

    logger, log_file_path = setup_logger(CURRENT_SESSION_NAME)
    console.print(Panel(f"""[bold]V8.0 双阶段流水线 (Twin-Engine)[/]
    会话: [magenta]{CURRENT_SESSION_NAME}[/] | API Key: {final_key[:8]}...
    -------------------------------------------------------
    Step 1 引擎: [cyan]{MODEL_VISION}[/] (并发数: {VISION_BATCH_WORKERS})
    Step 2 引擎: [green]{MODEL_BRAIN}[/] (串行逻辑修正)
    -------------------------------------------------------
    输出: {OUTPUT_FOLDER}
    日志: {log_file_path}
    """, title="配置确认", border_style="green"))

    tasks_config = interactive_setup(console, final_key)
    if not tasks_config: return

    m = Manager()
    msg_queue = m.Queue()

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.fields[ppt_name]}", justify="right"),
        BarColumn(),
        TaskProgressColumn(),      
        MofNCompleteColumn(),      
        TimeElapsedColumn(),       
        TimeRemainingColumn(),     
        TextColumn("{task.fields[status]}"), # 状态栏留宽一点
    )

    print("\n")
    
    with Live(progress, console=console, refresh_per_second=10):
        for ppt_name in tasks_config:
            tid = progress.add_task(
                f"waiting...", 
                total=100, 
                ppt_name=ppt_name, 
                status="准备中..."
            )
            tasks_config[ppt_name]["task_id"] = tid

        # 进程池：控制同时处理几个 PPT
        with ProcessPoolExecutor(max_workers=MAX_PPT_WORKERS) as executor:
            futures = []
            for ppt_name, config in tasks_config.items():
                futures.append(executor.submit(process_single_ppt_task, ppt_name, config, msg_queue))
            
            finished_tasks = 0
            total_tasks = len(tasks_config)
            
            while finished_tasks < total_tasks:
                try:
                    while not msg_queue.empty():
                        msg_type, *args = msg_queue.get_nowait()
                        
                        if msg_type == "init_task":
                            tid, total = args
                            progress.update(tid, total=total)
                        elif msg_type == "advance":
                            tid, steps = args
                            progress.advance(tid, steps)
                        elif msg_type == "status":
                            tid, text = args
                            progress.update(tid, status=text)
                        elif msg_type == "log":
                            log_msg = args[0]
                            logger.info(log_msg)
                            
                    done_count = sum(1 for f in futures if f.done())
                    if done_count > finished_tasks: finished_tasks = done_count
                    if finished_tasks == total_tasks and msg_queue.empty(): break
                    time.sleep(0.1)
                except queue.Empty: pass
                except Exception as e:
                    logger.error(f"Main Loop Error: {e}")
                    break

    console.print(Panel(f"[bold green]✨ 所有双阶段任务处理完毕！[/]", expand=False))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断。")