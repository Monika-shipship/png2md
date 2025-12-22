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

# 视觉模型：负责 OCR 和 读图 (Step 1) - 使用 Qwen3-VL-Plus
MODEL_VISION = "qwen3-vl-plus" # 或者是 "qwen-vl-max" / "qwen2.5-vl-7b-instruct"

# 文本模型：负责 逻辑重组、滑动窗口分析、原文勘误 (Step 2)
MODEL_BRAIN = "qwen-plus"

INPUT_FOLDER = "./ppt_images"        
OUTPUT_FOLDER = "./markdown_output" 
LOG_FOLDER = "./log"

# 全局并发控制 (同时处理多少个 PPT 文件夹)
MAX_PPT_WORKERS = 5

# 【关键参数 1】Step 1 视觉提取并发数 (建议 5-15)
VISION_BATCH_WORKERS = 20  

# 【关键参数 2】Step 2 逻辑重组并发数 (解耦后可火力全开，建议 10-20)
#  警告：设置过高可能会触发 API Rate Limit (429 Too Many Requests)
BRAIN_BATCH_WORKERS = 50 

# 思考预算 (Token)
THINKING_BUDGET_VISION = 2048 
THINKING_BUDGET_BRAIN = 2048 

# === 命令行参数解析 ===
parser = argparse.ArgumentParser(description="PPT2MD-V10 (Parallel Brain & Stream Fixed)")
parser.add_argument("-n", "--name", type=str, default="default", help="任务会话名称")
parser.add_argument("-o", "--output", type=str, default="./markdown_output", help="输出目录路径")
args = parser.parse_args()

SESSION_FILE = f"session_{args.name}.json"
CURRENT_SESSION_NAME = args.name
OUTPUT_FOLDER = str(Path(args.output).resolve())
INPUT_FOLDER_ABS = str(Path(INPUT_FOLDER).resolve())

# ================= Prompt 模板 (并行版) =================

# --- 阶段一：视觉提取 Prompt (TikZ-Ready) ---
PROMPT_STAGE_1_VISION = r"""
任务：请对这张 PPT 图片进行详尽的视觉提取。

【思考要求】
1. **Figure 价值判断**：首先扫视全图，判断是否存在**具有信息量的 Figure**（如架构图、流程图、物理模型图、函数曲线、分子结构等）。
   - **忽略**：页码、纯装饰性背景线条、无意义的库存图片、简单的排版框。
   - **关注**：任何承载知识逻辑的图示。
2. **TikZ 预备分析**：对于有价值的 Figure，请在脑海中解构其几何拓扑（节点形状、位置关系、箭头流向）。

【提取要求】
1. **OCR 识别**：逐字提取文本，保留原始换行结构。
2. **公式识别**：所有数学/物理公式转换为 LaTeX 格式。
3. **[重要] Figure 深度描述**：
   - 如果发现有价值的 Figure，请单独输出一个 `### Figure Analysis` 区块。
   - **描述粒度**：请用自然语言详细描述，以便我稍后能根据你的描述画出 TikZ 代码。
   - **包含要素**：
     * **布局**：例如“左侧是A，右侧是B”，“呈环形分布”，“分层结构”。
     * **节点**：形状（圆/矩形/菱形）、颜色、包含的文字。
     * **连接**：箭头方向（A指向B）、线型（实线/虚线）、连线上的标签。
   - 如果图片仅为纯文本或无意义装饰，则**不要**输出此区块。

请直接输出提取到的内容，保持原意，**不需要**整理成 Markdown 格式。
"""

# --- 阶段二：逻辑重组 Prompt (并行化 - 基于 Raw Data 窗口) ---
# [修改注]：输入源已从 prev_md 改为 prev_raw，并增加了符号一致性强指令。
PROMPT_STAGE_2_BRAIN = r"""
你是一个专业的编辑，你的责任是将图书内容纠错，并且尽量还原作者的原义，不要瞎编乱造，尽量遵守作者的原意，尽量还原作者的意图。请利用提供的“五页 Raw Data 滑动窗口”信息，将 PPT 重组为 Markdown。

【五页滑动窗口信息 (全 Raw Data)】
--------------------------------------------------
[P-2] 前前页 (Raw OCR Data):
{prev_2_raw}
--------------------------------------------------
[P-1] 前一页 (Raw OCR Data):
{prev_1_raw}
--------------------------------------------------
[Target] **当前页 (Raw OCR Data - 包含详细的 Figure 描述)**:
{target_raw}
--------------------------------------------------
[N+1] 后一页 (Raw OCR Data):
{next_1_raw}
--------------------------------------------------
[N+2] 后两页 (Raw OCR Data):
{next_2_raw}
--------------------------------------------------

【任务流程】
请在后台进行深度思考 (Chain of Thought)：
1. **逻辑衔接**：即便前两页是 Raw Data，也请分析其语义流向，确保[Target]的正文与前文逻辑连贯，但是要尽量还原尽量还原作者的原义。
2. **符号一致性 (Crucial)**：
   - **强指令**：请仔细对比前后页 Raw Data 中的公式上下文。如果发现 [P-1] 中使用了特定符号（如 $v$ 表示速度），而 [Target] 中识别不够准确（如识别为 $\nu$），请智能推断并统一为最佳 LaTeX 符号定义。
   - 必须使用 LaTeX 格式：行内公式 $...$，行间公式 $$...$$，你不能使用\[和\]，你的行间公式必须用$$123$$。
3. **Figure 整合**：检查 [Target] 中是否有 `### Figure Analysis` 区块。
   - 如果有，请在 Markdown 中将其整理为 `> [!NOTE] 🖼️ Figure 描述` 引用块。

【输出要求】
输出当前页的 Markdown，结构如下：

1. **正文**：
   - 标题：# Slide {slide_no}
   - 内容：修正后的流畅文本和 LaTeX 公式。
   - **图像描述**（如果有）：
     > [!NOTE] 🖼️ Figure 描述
     > (在此处放入整理后的图像几何描述，方便后续 TikZ 绘图)

2. **原文勘误** (可选)：
   - 如果发现 OCR 明显的错别字或逻辑矛盾，请修正并在下方标注：
   > [!WARNING] 🛡️ 原文勘误
   > ...

3. **Context Anchor**：
   <CTX>
   {{ "summary": "本页核心摘要...", "keywords": ["关键词1", "关键词2"] }}
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
        outfile.write(f"# {ppt_name} 汇总笔记\n\n> 生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n> 引擎: V10 (Parallel Brain)\n\n")
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
    Step 1 Worker: 调用 VL 模型提取 Raw Data (流式版)
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            messages = [{"role": "user", "content": [{"image": f"file://{img_path}"}, {"text": PROMPT_STAGE_1_VISION}]}]
            
            responses = MultiModalConversation.call(
                model=MODEL_VISION,
                messages=messages,
                enable_thinking=True,              
                thinking_budget=THINKING_BUDGET_VISION,
                stream=True,                       
                incremental_output=True            
            )
            
            full_content = ""
            full_reasoning = ""
            
            for chunk in responses:
                if chunk.status_code == 200:
                    try:
                        if not hasattr(chunk.output, 'choices') or not chunk.output.choices:
                            continue
                            
                        message = chunk.output.choices[0].message
                        
                        r_content = None
                        if hasattr(message, 'get'):
                            r_content = message.get('reasoning_content')
                        else:
                            try:
                                r_content = message.reasoning_content
                            except (AttributeError, KeyError):
                                r_content = None
                        
                        if r_content:
                            full_reasoning += r_content
                        
                        c_content = None
                        if hasattr(message, 'get'):
                            c_content = message.get('content')
                        else:
                            try:
                                c_content = message.content
                            except (AttributeError, KeyError):
                                c_content = None

                        if c_content:
                            if isinstance(c_content, list):
                                for item in c_content:
                                    if isinstance(item, dict) and 'text' in item:
                                        full_content += item['text']
                            elif isinstance(c_content, str):
                                full_content += c_content
                                
                    except Exception as parse_err:
                        continue
                            
                else:
                    if "AccessDenied" in str(chunk.code): raise RuntimeError("AccessDenied")
                    return {"success": False, "slide_no": slide_no, "error": f"Stream Error: {chunk.code}"}

            if not full_content:
                if full_reasoning:
                    return {"success": True, "slide_no": slide_no, "raw_text": f"[Model only returned reasoning]\n\nReasoning Trace:\n{full_reasoning[:500]}..."}
                else:
                    return {"success": False, "slide_no": slide_no, "error": "Empty response (Stream failed)."}
            
            return {"success": True, "slide_no": slide_no, "raw_text": full_content}
                
        except Exception as e:
            if "AccessDenied" in str(e): raise e
            if attempt == max_retries - 1:
                return {"success": False, "slide_no": slide_no, "error": f"重试失败: {str(e)}"}
            time.sleep((attempt + 1) * 2)

# ================= 阶段二：大脑 (并行版 - 全 Raw Data 窗口) =================

def get_raw_content(raw_data_map, slide_no):
    """安全获取 Raw Data，处理越界"""
    # 截断过长的 Raw Data 以节省 token
    content = raw_data_map.get(slide_no, "(No Data / Out of Range)")
    if len(content) > 3000:
        return content[:3000] + "...(truncated)"
    return content

def run_stage_2_brain_parallel(slide_no, ppt_root, raw_data_map):
    """
    Step 2 Worker: 组装 5 页 Raw Data -> 调用 Brain (流式版)
    [重要变更]：输入全部来自 raw_data_map，不读取磁盘 MD，从而允许完全并行。
    """
    # 1. 准备 5 页数据 (全 Raw)
    prev_2_raw = get_raw_content(raw_data_map, slide_no - 2)
    prev_1_raw = get_raw_content(raw_data_map, slide_no - 1)
    target_raw = get_raw_content(raw_data_map, slide_no)
    next_1_raw = get_raw_content(raw_data_map, slide_no + 1)
    next_2_raw = get_raw_content(raw_data_map, slide_no + 2)

    # 2. 填充 Prompt (使用新版 Prompt)
    filled_prompt = PROMPT_STAGE_2_BRAIN.format(
        prev_2_raw=prev_2_raw,
        prev_1_raw=prev_1_raw,
        target_raw=target_raw,
        next_1_raw=next_1_raw,
        next_2_raw=next_2_raw,
        slide_no=slide_no
    )

    try:
        responses = Generation.call(
            model=MODEL_BRAIN,
            messages=[{'role': 'user', 'content': filled_prompt}],
            result_format='message',
            enable_thinking=True,              
            thinking_budget=THINKING_BUDGET_BRAIN,
            stream=True,                       
            incremental_output=True            
        )
        
        full_reasoning = ""
        full_content = ""
        
        for chunk in responses:
            if chunk.status_code == 200:
                choice = chunk.output.choices[0]
                
                # 1. 收集思考过程
                if hasattr(choice.message, 'reasoning_content') and choice.message.reasoning_content:
                    full_reasoning += choice.message.reasoning_content
                
                # 2. 收集正文回答
                if hasattr(choice.message, 'content') and choice.message.content:
                    full_content += choice.message.content
            else:
                 return f"Brain Error: {chunk.code} - {chunk.message}"
        
        if not full_content:
             return f"Error: Model generated thinking but no content. Trace: {full_reasoning[:100]}..."
            
        return full_content

    except Exception as e:
        return f"Brain Exception: {str(e)}"

# ================= 核心流水线控制 =================

def process_single_ppt_task(ppt_name, config, msg_queue):
    """
    双阶段流水线控制器 (V10 并行增强版)
    """
    task_key = config.get("api_key")
    if task_key: dashscope.api_key = task_key
    else: dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")
    
    images_paths = config["images"]
    start_idx = config["range_start"]
    end_idx = config["range_end"]
    task_id = config["task_id"]
    
    target_images = images_paths[start_idx:end_idx]
    total_slides = len(target_images)
    
    ppt_root = Path(OUTPUT_FOLDER) / ppt_name
    temp_dir = ppt_root / "temp_raw_vision"
    os.makedirs(ppt_root, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    msg_queue.put(("log", f"[{ppt_name}] 任务启动。V10 并行版引擎 (Vision:{VISION_BATCH_WORKERS} / Brain:{BRAIN_BATCH_WORKERS}) 已激活。"))
    msg_queue.put(("init_task", task_id, total_slides * 2)) # 进度条总数 * 2 (Step 1 + Step 2)

    # === Step 1: 暴力并发视觉提取 ===
    msg_queue.put(("status", task_id, f"[cyan]Step 1: 视觉提取 (并发 {VISION_BATCH_WORKERS})..."))
    
    vision_futures = {}
    raw_data_map = {} 
    
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
                        msg_queue.put(("advance", task_id, 1)) # 缓存命中也推进度
                        continue 
                except: pass

            future = executor.submit(run_stage_1_vision, img_path, actual_slide_no, ppt_name, msg_queue)
            vision_futures[future] = actual_slide_no

        # 等待所有视觉任务完成
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
            finally:
                msg_queue.put(("advance", task_id, 1))

    msg_queue.put(("log", f"[{ppt_name}] Step 1 视觉完成。开始 Step 2 并行逻辑重组..."))

    # === Step 2: 并行逻辑重组 (Brain + 5-Page Raw Window) ===
    # [修改点]：这里不再是串行 for 循环，而是使用 ThreadPoolExecutor 进行并行
    
    msg_queue.put(("status", task_id, f"[green]Step 2: 并行思考 (并发 {BRAIN_BATCH_WORKERS})..."))
    
    brain_futures = {}
    
    with ThreadPoolExecutor(max_workers=BRAIN_BATCH_WORKERS) as executor:
        for i in range(total_slides):
            actual_slide_no = start_idx + i + 1
            output_path = ppt_root / f"Slide_{actual_slide_no:02d}.md"
            
            # 断点检测
            if output_path.exists() and output_path.stat().st_size > 100:
                msg_queue.put(("advance", task_id, 1))
                continue

            # 提交任务到线程池
            # 注意：raw_data_map 在此时已经由 Step 1 完全填充完毕，可以安全地并发读取
            future = executor.submit(run_stage_2_brain_parallel, actual_slide_no, ppt_root, raw_data_map)
            brain_futures[future] = (actual_slide_no, output_path)

        # 等待 Step 2 任务完成
        for future in as_completed(brain_futures):
            s_no, out_path = brain_futures[future]
            try:
                final_markdown = future.result()
                
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(final_markdown)
                
                msg_queue.put(("log", f"[{ppt_name}] P{s_no} 重组完成"))
            except Exception as e:
                msg_queue.put(("log", f"[{ppt_name}] P{s_no} 重组异常: {e}"))
            finally:
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
    console.print(Panel(f"""[bold]V10 终极版 (Parallel Brain / Raw Context)[/]
    会话: [magenta]{CURRENT_SESSION_NAME}[/] | API Key: {final_key[:8]}...
    -------------------------------------------------------
    Step 1 引擎: [cyan]{MODEL_VISION}[/] (并发: {VISION_BATCH_WORKERS})
    Step 2 引擎: [green]{MODEL_BRAIN}[/] (并发: {BRAIN_BATCH_WORKERS})
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