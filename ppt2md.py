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

# === 依赖库检查 ===
try:
    from rich.progress import (
        Progress, SpinnerColumn, TextColumn, BarColumn,
        TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn
    )
    from rich.live import Live
    from rich.panel import Panel
    from rich.console import Console
    from rich.markdown import Markdown
except ImportError:
    print("❌ 缺少依赖库 [rich]。请运行: pip install rich")
    exit(1)

import dashscope
from dashscope import Generation, MultiModalConversation

# ================= 配置区域 =================

# 视觉模型：负责 OCR 和 读图 (Step 1)
MODEL_VISION = "qwen3-vl-plus"

# 文本模型：负责 逻辑重组、滑动窗口分析、原文勘误 (Step 2)
MODEL_BRAIN = "qwen-plus"

INPUT_FOLDER = "./ppt_images"       
OUTPUT_FOLDER = "./markdown_output" 
LOG_FOLDER = "./log"

# 全局并发控制 (同时处理多少个 PPT 文件夹)
MAX_PPT_WORKERS = 5

# 【关键参数】单任务内部并发数 (Step 1 视觉提取的并发度)
VISION_BATCH_WORKERS = 15  # 建议保持在 5 以避免 SSL 握手失败

# 思考预算 (Token)
THINKING_BUDGET_VISION = 1024 
THINKING_BUDGET_BRAIN = 2048 

# === 命令行参数解析 ===
parser = argparse.ArgumentParser(description="PPT2MD-V9.3 (5-Page Sliding Window)")
parser.add_argument("-n", "--name", type=str, default="default", help="任务会话名称")
parser.add_argument("-o", "--output", type=str, default="./markdown_output", help="输出目录路径")
args = parser.parse_args()

SESSION_FILE = f"session_{args.name}.json"
CURRENT_SESSION_NAME = args.name
OUTPUT_FOLDER = str(Path(args.output).resolve())
INPUT_FOLDER_ABS = str(Path(INPUT_FOLDER).resolve())

# ================= Prompt 模板 (5页窗口 + 深度思考) =================

# --- 阶段一：视觉提取 Prompt ---
PROMPT_STAGE_1_VISION = r"""
任务：请对这张 PPT 图片进行详尽的视觉提取。

【思考要求】
在输出结果前，请先观察图片的整体结构、公式的角标逻辑以及图表的数据趋势。

【提取要求】
1. **OCR 识别**：逐字提取文本，保留原始换行结构。
2. **公式识别**：看到数学/物理公式，必须转换为 LaTeX 格式。
   - 区分 $v$ (速度) 和 $\nu$ (频率)。
   - 区分 $P$ (功率) 和 $\rho$ (密度)。
3. **视觉描述**：详细描述图表内容、数据关系、流程图逻辑。

请直接输出提取到的内容，**不需要**整理成 Markdown 格式。
"""

# --- 阶段二：逻辑重组 Prompt (集成 5 页滑动窗口) ---
PROMPT_STAGE_2_BRAIN = r"""
你是一个具备深度批判性思维的学术助教。请利用提供的“五页滑动窗口”信息，将 PPT 重组为 Markdown。

【五页滑动窗口信息】
--------------------------------------------------
[P-2] 前前页 (Markdown 成品 - 用于定义锚定):
{prev_2_md}
--------------------------------------------------
[P-1] 前一页 (Markdown 成品 - 用于直接语境):
{prev_1_md}
--------------------------------------------------
[Target] **当前页 (Raw OCR Data - 处理对象)**:
{target_raw}
--------------------------------------------------
[N+1] 后一页 (Raw OCR Data - 用于断句预判):
{next_1_raw}
--------------------------------------------------
[N+2] 后两页 (Raw OCR Data - 用于逻辑走向):
{next_2_raw}
--------------------------------------------------

【任务流程】
请在后台进行深度思考 (Chain of Thought)：
1. **跨页逻辑分析**：
   - 查看 [P-1] 的结尾是否句子未完？如果是，[Target] 开头应紧密衔接。
   - 查看 [Target] 结尾是否句子未完？结合 [N+1] 预判是否需要添加连接符。
2. **符号一致性**：检查 [P-2] 和 [P-1] 中定义的符号，确保当前页使用相同的 LaTeX 表达。
3. **原文勘误 (Fact-Check)**：检查 [Target] 原文是否存在笔误或事实错误（非OCR错误，而是PPT作者写错的）。

【输出要求】
输出当前页的 Markdown，只能包含以下结构：（注意不要把思考内容放进来了！）

1. **正文**：
   - 标题：# Slide {slide_no}
   - 内容：修正后的流畅文本和 LaTeX 公式。
   - 视觉描述：放在 `## Figure Description`。

2. **原文勘误 (仅在发现原文错误时生成)**：
   > [!WARNING] 🛡️ 原文勘误
   > - **原文**: ...
   > - **疑点**: ...
   > - **修正**: ...

3. **Context Anchor (用于传递给下一轮)**：
   <CTX>
   {{ "summary": "本页摘要", "keywords": ["..."] }}
   </CTX>
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
    name = s.name if hasattr(s, 'name') else str(s)
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', name)]

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
        try:
            json_str = match.group(1).replace("```json", "").replace("```", "").strip()
            return json_str
        except:
            return "Context parse error."
    return "No context from previous page."

def merge_markdowns(ppt_output_dir, ppt_name):
    p = Path(ppt_output_dir)
    final_path = p / f"{ppt_name}_FULL.md"
    md_files = sorted(p.glob("Slide_*.md"), key=natural_sort_key)
    if not md_files: return
    with open(final_path, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# {ppt_name} 汇总笔记\n\n> 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n> 引擎: V9.3 (5-Page Window + Thinking)\n\n")
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

def run_stage_1_vision(img_path, slide_no, ppt_name, msg_queue):
    """
    Step 1 Worker: 调用 VL 模型提取 Raw Data
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            messages = [{"role": "user", "content": [{"image": f"file://{img_path}"}, {"text": PROMPT_STAGE_1_VISION}]}]
            response = MultiModalConversation.call(
                model=MODEL_VISION,
                messages=messages,
                enable_thinking=True,              # <--- 开启思考
                thinking_budget=THINKING_BUDGET_VISION
            )
            
            if response.status_code == 200:
                content = response.output.choices[0].message.content
                if isinstance(content, list):
                    text_content = "".join([c['text'] for c in content if 'text' in c])
                else:
                    text_content = content
                
                return {"success": True, "slide_no": slide_no, "raw_text": text_content}
            else:
                if "AccessDenied" in str(response.code): raise RuntimeError("AccessDenied")
                raise Exception(f"API Code {response.code}")
                
        except Exception as e:
            if "AccessDenied" in str(e): raise e
            if attempt == max_retries - 1:
                return {"success": False, "slide_no": slide_no, "error": f"重试失败: {str(e)}"}
            time.sleep((attempt + 1) * 2)

# ================= 阶段二：大脑 (5页滑动窗口逻辑) =================

def get_raw_content(raw_data_map, slide_no):
    """安全获取 Raw Data，处理越界"""
    return raw_data_map.get(slide_no, "(No Data / Out of Range)")

def get_md_content(ppt_root, slide_no):
    """安全获取已生成的 MD 文件，处理越界"""
    p = ppt_root / f"Slide_{slide_no:02d}.md"
    if p.exists():
        try:
            with open(p, 'r', encoding='utf-8') as f: 
                content = f.read()
                # 截取前 2000 字防止 Token 溢出，通常足够覆盖上下文
                return content[:2500] 
        except: return "(File Read Error)"
    return "(Start of Document / No Previous Slide)"

def run_stage_2_brain_5window(slide_no, ppt_root, raw_data_map):
    """
    Step 2 Worker: 组装 5 页数据 -> 调用 Brain
    此函数实现了真正的 P-2, P-1, Target, N+1, N+2 注入
    """
    # 1. 准备 5 页数据
    prev_2_md = get_md_content(ppt_root, slide_no - 2)
    prev_1_md = get_md_content(ppt_root, slide_no - 1)
    target_raw = get_raw_content(raw_data_map, slide_no)
    next_1_raw = get_raw_content(raw_data_map, slide_no + 1)
    next_2_raw = get_raw_content(raw_data_map, slide_no + 2)

    # 2. 填充 Prompt
    filled_prompt = PROMPT_STAGE_2_BRAIN.format(
        prev_2_md=prev_2_md,
        prev_1_md=prev_1_md,
        target_raw=target_raw,
        next_1_raw=next_1_raw,
        next_2_raw=next_2_raw,
        slide_no=slide_no
    )

    try:
        response = Generation.call(
            model=MODEL_BRAIN,
            messages=[{'role': 'user', 'content': filled_prompt}],
            result_format='message',
            enable_thinking=True,              # <--- 开启思考
            thinking_budget=THINKING_BUDGET_BRAIN
        )
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            return f"Brain Error: {response.code} - {response.message}"
    except Exception as e:
        return f"Brain Exception: {str(e)}"

# ================= 核心流水线控制 =================

def process_single_ppt_task(ppt_name, config, msg_queue):
    """
    双阶段流水线控制器
    """
    task_key = config.get("api_key")
    if task_key: dashscope.api_key = task_key
    else: dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    
    images_paths = config["images"]
    start_idx = config["range_start"]
    end_idx = config["range_end"]
    task_id = config["task_id"]
    
    # 修正范围，获取实际要处理的图片列表
    target_images = images_paths[start_idx:end_idx]
    total_slides = len(target_images)
    
    ppt_root = Path(OUTPUT_FOLDER) / ppt_name
    temp_dir = ppt_root / "temp_raw_vision"
    os.makedirs(ppt_root, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    msg_queue.put(("log", f"[{ppt_name}] 任务启动。V9.3 5页窗口引擎已激活。"))
    msg_queue.put(("init_task", task_id, total_slides))

    # === Step 1: 暴力并发视觉提取 ===
    msg_queue.put(("status", task_id, f"[cyan]Step 1: 视觉提取 (并发{VISION_BATCH_WORKERS})..."))
    
    vision_futures = {}
    raw_data_map = {} 
    
    # 使用 ThreadPoolExecutor 并发处理图片
    with ThreadPoolExecutor(max_workers=VISION_BATCH_WORKERS) as executor:
        for i, img_path in enumerate(target_images):
            actual_slide_no = start_idx + i + 1
            raw_file = temp_dir / f"Raw_{actual_slide_no:02d}.json"
            
            # 断点续传检查
            if raw_file.exists():
                try:
                    with open(raw_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        raw_data_map[actual_slide_no] = data['raw_text']
                        msg_queue.put(("log", f"[{ppt_name}] P{actual_slide_no} 视觉缓存命中"))
                        continue 
                except: pass

            future = executor.submit(run_stage_1_vision, img_path, actual_slide_no, ppt_name, msg_queue)
            vision_futures[future] = actual_slide_no

        # 等待所有视觉任务完成
        # 注意：为了 Step 2 的 N+1/N+2 预判，必须等待大部分/全部视觉任务完成
        for future in as_completed(vision_futures):
            s_no = vision_futures[future]
            try:
                res = future.result()
                if res['success']:
                    raw_text = res['raw_text']
                    raw_data_map[s_no] = raw_text
                    # 落盘保存
                    raw_file = temp_dir / f"Raw_{s_no:02d}.json"
                    with open(raw_file, 'w', encoding='utf-8') as f:
                        json.dump(res, f, ensure_ascii=False)
                else:
                    msg_queue.put(("log", f"[{ppt_name}] P{s_no} 视觉失败: {res.get('error')}"))
                    raw_data_map[s_no] = "[Vision Failed]"
            except RuntimeError as e:
                msg_queue.put(("status", task_id, "[bold red]权限拒绝!"))
                raise e
            except Exception as e:
                msg_queue.put(("log", f"[{ppt_name}] P{s_no} 异常: {e}"))

    msg_queue.put(("log", f"[{ppt_name}] Step 1 视觉完成。开始 Step 2 滑动窗口逻辑重组..."))

    # === Step 2: 串行逻辑重组 (Brain + 5-Page Window) ===
    # 必须串行，因为要按顺序生成 Markdown 供下一页读取 [P-1]
    
    for i in range(total_slides):
        actual_slide_no = start_idx + i + 1
        output_path = ppt_root / f"Slide_{actual_slide_no:02d}.md"
        
        msg_queue.put(("status", task_id, f"[green]Step 2: 深度思考 P{actual_slide_no}..."))
        
        # 断点检测
        if output_path.exists() and output_path.stat().st_size > 100:
            msg_queue.put(("advance", task_id, 1))
            continue

        # 调用核心函数 (包含 5 页数据注入)
        final_markdown = run_stage_2_brain_5window(actual_slide_no, ppt_root, raw_data_map)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_markdown)
        
        msg_queue.put(("log", f"[{ppt_name}] P{actual_slide_no} 完成"))
        msg_queue.put(("advance", task_id, 1))

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
    console.print(Panel(f"""[bold]V9.3 终极版 (5-Page Window + Deep Thinking)[/]
    会话: [magenta]{CURRENT_SESSION_NAME}[/] | API Key: {final_key[:8]}...
    -------------------------------------------------------
    Step 1 引擎: [cyan]{MODEL_VISION}[/] (并发读取 Raw Data)
    Step 2 引擎: [green]{MODEL_BRAIN}[/] (5页滑动窗口 + 勘误)
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
        TextColumn("{task.fields[status]}"), 
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

    console.print(Panel(f"[bold green]✨ 所有双阶段思考任务处理完毕！[/]", expand=False))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n用户中断。")