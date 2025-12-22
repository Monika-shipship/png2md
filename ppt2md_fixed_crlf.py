import os
import re
import time
import json
import logging
import datetime
import argparse
import sys
from http import HTTPStatus
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


# 视觉模型增强设置
VL_HIGH_RESOLUTION_IMAGES = True  # 提升小字/坐标轴标签识别效果（成本/耗时会增加）
STAGE1_USE_STREAM = True         # 使用流式输出，降低长输出超时风险
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
PROMPT_STAGE_1_VISION = r"""你是一个严谨的“PPT图片内容提取器（Raw Extractor）”，输入是一张PPT页面截图（可能含中文/英文混排、公式、图表、示意图、照片等）。你的目标是为后续“整理成 Markdown 笔记 + 复刻 TikZ/LaTeX 图”提供**尽可能准确且可复用**的原始信息。

请严格遵循：

## 总原则
1) **不翻译、不改写、不总结**：保持原文语言与表述；只做“识别与描述”。
2) **尽量完整**：标题、正文、项目符号、注释、脚注、图注、页眉页脚、角落小字都要尽量提取。
3) **不编造**：看不清/无法确定的内容请标注“(无法辨认)”或“(不确定)”，不要猜测。
4) **输出为结构化纯文本（非 Markdown 文章）**：用下面的固定分区标签输出，便于后续程序与模型二次处理。

## 你需要提取的内容
### A. 文本（TEXT）
- 按页面**阅读顺序**输出（从上到下、从左到右）。
- 保留换行与层级（例如标题、二级标题、项目符号列表）。
- 如果页面有多栏布局，请先输出左栏再右栏，或按明显阅读路径组织。

### B. 公式（EQUATIONS）
- 将公式转为 LaTeX（尽量还原原始符号与下标/上标）。
- 行内公式用 `$...$`，行间公式用
  $$
  ...
  $$
- 若公式与正文混排，请在 TEXT 中保留原位置，同时在 EQUATIONS 中再汇总一份（可带简短定位信息，如“位于第二行末”）。

### C. 表格（TABLES）
- 以 Markdown 表格形式输出（仅此处允许 Markdown 表格），保持行列结构与单元格文本。
- 若表格过宽，可用合理的换行，但不要丢字段。

### D. 关键图像/图形（FIGURES）
你的任务不是描述所有图片，而是**只对“对内容理解有帮助”的 figure 进行详细描述**，以便后续用 TikZ/LaTeX 复刻或在笔记中保留关键信息。

请先在心里判断图像是否“信息性 figure”：
- **需要详细描述（信息性 figure）**：折线/柱状/散点/饼图等图表；结构示意图；流程图；几何图；电路/实验装置图；带关键标注的照片/截屏；任何承载概念或数据的插图。
- **不需要详细描述（装饰性图片）**：纯背景纹理/渐变；装饰图标；Logo；无信息的配图（仅美观、无标注、与正文无强关联）；页面版式框线。

对每个“信息性 figure”，给出可复刻的细节描述（越像“画图说明书”越好）：
- **类型**：图表/流程图/示意图/照片/几何图/其他
- **在页面的位置**：例如“右上角”“左侧占半页”等
- **构成元素与相对关系**：形状（矩形/圆/箭头/曲线）、相对位置（上下左右、对齐方式、间距大致比例）、连接关系（箭头指向、连线）
- **文本标注**：所有可见标签、图例、轴标题、单位、注释、编号（Figure 1 等）
- **图表细节（若为坐标图）**：x/y 轴名称与刻度范围、曲线/柱子数量与颜色/线型（若可见）、趋势与关键拐点（避免编造精确数值；只在清晰可读时给大致读数）
- **复刻建议**：如果图是典型结构（例如“两块区域 + 中间箭头 + 注释框”），可用一句话给出 TikZ 复刻策略（例如“可用 nodes + arrows + label”）

对于“装饰性图片”，**不要**在 FIGURES 中展开描述；如确有必要，仅在 DECORATION 中用一句话记录“存在装饰性背景/Logo（可忽略）”。

## 输出格式（必须严格使用这些分区标签）
[TEXT]
...（按顺序输出文本）
[/TEXT]

[EQUATIONS]
...（LaTeX 公式）
[/EQUATIONS]

[TABLES]
...（Markdown 表格，或写 (None)）
[/TABLES]

[FIGURES]
...（仅信息性 figure 的详细描述；若无则写 (None)）
[/FIGURES]

[DECORATION]
...（可忽略的装饰性元素；若无则写 (None)）
[/DECORATION]
"""

# --- 阶段二：逻辑重组 Prompt (集成 5 页滑动窗口) ---
PROMPT_STAGE_2_BRAIN = r"""你是“PPT 笔记整理器（Brain）”。你将获得一个 5 页滑动窗口的上下文：

- [N-2]：上一页之前的 Markdown（已整理）
- [N-1]：上一页的 Markdown（已整理）
- [N]：当前页的 Raw Data（由视觉模型提取，包含 [TEXT]/[EQUATIONS]/[TABLES]/[FIGURES] 等分区）
- [N+1]：下一页的 Raw Data
- [N+2]：下两页的 Raw Data

你的任务：**只输出第 N 页的最终 Markdown 笔记**，并利用上下文保证术语、符号、叙述与定义的一致性（必要时纠正 N 页中由于 OCR/识别导致的明显断裂，但不能凭空添加不存在的内容）。

## 规则
1) 仅输出 Markdown 正文，不要输出任何解释、思考过程、或“我将如何做”之类的文字。
2) 不翻译：保持原文语言（中英混排就按原样保留）。
3) 结构清晰：建议使用标题、列表、分段；对关键信息用加粗；公式用 LaTeX。
4) 表格：若 N 页 Raw Data 的 [TABLES] 有内容，尽量原样保留为 Markdown 表格。
5) 图形：若 N 页 Raw Data 的 [FIGURES] 有内容，请在 Markdown 中保留一个“Figure / 图示”小节（或合适位置），**完整拷贝并整理 figure 描述**（保持细节，便于后续 TikZ 复刻）。装饰性图片不需要写入。
6) 禁止编造：Raw Data 中看不清的内容如果标了“(无法辨认)/(不确定)”，在 Markdown 中也要如实保留或略去，不要猜测补全。

## 输入
[N-2 Markdown]
{prev_2_md}

[N-1 Markdown]
{prev_1_md}

[N Raw Data]
{target_raw}

[N+1 Raw Data]
{next_1_raw}

[N+2 Raw Data]
{next_2_raw}

## 输出
现在开始，只输出第 N 页的 Markdown：
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


# ================= 深度思考输出隔离（关键修复） =================
# 说明：
# - 百炼“混合思考模式”会在 message.reasoning_content 字段返回思考过程，
#   在 message.content 字段返回最终回复。若不做隔离，思考文本可能混入 Markdown。
# - 本项目只将“最终回复”写入 Slide_XX.md；思考过程（如需）单独落盘。

# 若为 True：将 Step 2 的 reasoning_content 单独保存到 temp_reasoning_brain/，便于调试
SAVE_REASONING_TO_FILES = False

def _msg_get(msg, field, default=""):
    """兼容 message 为对象或 dict 的两种情况。"""
    try:
        if isinstance(msg, dict):
            return msg.get(field, default) or default
        return getattr(msg, field, default) or default
    except Exception:
        return default

def _collect_generation_stream(model, messages, enable_thinking=True, thinking_budget=None):
    """按官方示例用流式方式收集 reasoning_content 与 content，确保二者不混淆。"""
    kwargs = dict(
        model=model,
        messages=messages,
        result_format='message',
        enable_thinking=enable_thinking,
        stream=True,
        incremental_output=True
    )
    if thinking_budget is not None:
        kwargs["thinking_budget"] = thinking_budget

    completion = Generation.call(**kwargs)

    reasoning_parts = []
    answer_parts = []
    for chunk in completion:
        try:
            msg = chunk.output.choices[0].message
        except Exception:
            continue

        rc = _msg_get(msg, "reasoning_content", "")
        c = _msg_get(msg, "content", "")

        # 思考阶段：reasoning_content 有值而 content 为空（官方示例的典型形态）
        if rc and not c:
            reasoning_parts.append(rc)

        # 回复阶段：content 有值
        if c:
            answer_parts.append(c)

    return "".join(reasoning_parts), "".join(answer_parts)


def _collect_multimodal_stream(responses) -> tuple[str, str, object]:
    """
    Collect streaming chunks from dashscope.MultiModalConversation.call(stream=True).
    Returns: (answer_text, reasoning_text, last_response)
    """
    answer_parts: list[str] = []
    reasoning_parts: list[str] = []
    last_resp = None

    for resp in responses:
        last_resp = resp
        # Most error cases surface as a non-OK status_code.
        if getattr(resp, "status_code", None) != HTTPStatus.OK:
            break

        try:
            choice = resp.output.choices[0]
            msg = choice.message
        except Exception:
            continue

        # reasoning_content may be present when enable_thinking=True
        reasoning = getattr(msg, "reasoning_content", None)
        if reasoning:
            reasoning_parts.append(reasoning)

        content = getattr(msg, "content", None)
        if content:
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    answer_parts.append(item["text"])

        if getattr(choice, "finish_reason", None) == "stop":
            break

    return "".join(answer_parts), "".join(reasoning_parts), last_resp
def _strip_thinking_from_output(text):
    """二次保险：若模型把“思考过程”打印进 content，这里做最小化剥离。"""
    if not text:
        return ""

    t = str(text)

    # 1) 常见的 think 标签
    t = re.sub(r"<think>.*?</think>", "", t, flags=re.DOTALL | re.IGNORECASE)
    t = re.sub(r"</?analysis>", "", t, flags=re.IGNORECASE)

    # 2) “思考过程/完整回复”分段（常见于示例输出）
    #    若存在“完整回复/回复内容”分隔符，则只保留其后内容
    m = re.search(r"=+\s*(完整回复|回复内容)\s*=+\s*", t)
    if m:
        t = t[m.end():]

    # 3) 强制从首个 Markdown 标题开始（通常是 # Slide N）
    m2 = re.search(r"(?m)^#\s*Slide\b", t)
    if m2:
        t = t[m2.start():]

    return t.strip()

def _is_md_polluted(md_text):
    """用于断点续传：识别旧版本里可能混入的思考片段。"""
    if not md_text:
        return False
    head = md_text[:2000]
    markers = [
        "<think>", "</think>",
        "思考过程", "完整回复", "回复内容",
        "Chain of Thought", "reasoning_content",
        "Token 消耗"
    ]
    return any(m in head for m in markers)

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
            messages = [{"role": "user", "content": [{"image": f"file://{img_path}"}, {"text": f"[PPT] {ppt_name}\n[SLIDE] {slide_no}\n\n{PROMPT_STAGE_1_VISION}"}]}]
            # 使用高分辨率与流式输出，提升小字/图表识别稳定性
            if STAGE1_USE_STREAM:
                responses = MultiModalConversation.call(
                    model=MODEL_VISION,
                    messages=messages,
                    enable_thinking=True,
                    thinking_budget=THINKING_BUDGET_VISION,
                    vl_high_resolution_images=VL_HIGH_RESOLUTION_IMAGES,
                    stream=True,
                    incremental_output=True,
                )
                text_content, reasoning_content, last_resp = _collect_multimodal_stream(responses)
                response = last_resp
            else:
                response = MultiModalConversation.call(
                    model=MODEL_VISION,
                    messages=messages,
                    enable_thinking=True,
                    thinking_budget=THINKING_BUDGET_VISION,
                    vl_high_resolution_images=VL_HIGH_RESOLUTION_IMAGES,
                )
                reasoning_content = getattr(response.output.choices[0].message, "reasoning_content", "") or ""
            
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

                # 二次保险：避免旧版本的“思考过程”污染后续滑动窗口上下文
                content = _strip_thinking_from_output(content)

                # 截取前 2500 字防止 Token 溢出，通常足够覆盖上下文
                return content[:2500]
        except:
            return "(File Read Error)"
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

    messages = [{'role': 'user', 'content': filled_prompt}]

    # 3) 按官方文档推荐的方式：使用流式输出隔离 reasoning_content 与 content
    try:
        reasoning, answer = _collect_generation_stream(
            model=MODEL_BRAIN,
            messages=messages,
            enable_thinking=True,
            thinking_budget=THINKING_BUDGET_BRAIN
        )

        # 可选：将思考过程单独落盘（不写入 Markdown）
        if SAVE_REASONING_TO_FILES and reasoning:
            reasoning_dir = Path(ppt_root) / "temp_reasoning_brain"
            os.makedirs(reasoning_dir, exist_ok=True)
            r_path = reasoning_dir / f"Reasoning_{slide_no:02d}.txt"
            with open(r_path, "w", encoding="utf-8") as f:
                f.write(reasoning)

        answer = _strip_thinking_from_output(answer)
        return answer if answer else "(Empty Answer)"

    except Exception as e_stream:
        # 4) 兜底：若流式在当前 SDK/网络环境不可用，则退回非流式，并做字段隔离与二次剥离
        try:
            response = Generation.call(
                model=MODEL_BRAIN,
                messages=messages,
                result_format='message',
                enable_thinking=True,
                thinking_budget=THINKING_BUDGET_BRAIN
            )
            if response.status_code == 200:
                msg = response.output.choices[0].message
                # 只取最终回复 content；reasoning_content 若存在则忽略/可选落盘
                reasoning = _msg_get(msg, "reasoning_content", "")
                answer = _msg_get(msg, "content", "")
                if SAVE_REASONING_TO_FILES and reasoning:
                    reasoning_dir = Path(ppt_root) / "temp_reasoning_brain"
                    os.makedirs(reasoning_dir, exist_ok=True)
                    r_path = reasoning_dir / f"Reasoning_{slide_no:02d}.txt"
                    with open(r_path, "w", encoding="utf-8") as f:
                        f.write(reasoning)

                answer = _strip_thinking_from_output(answer)
                return answer if answer else "(Empty Answer)"
            else:
                return f"Brain Error: {response.code} - {response.message} (stream fallback failed: {str(e_stream)})"
        except Exception as e:
            return f"Brain Exception: {str(e)} (stream failed: {str(e_stream)})"


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

        # 断点检测（保留原功能：已生成则跳过；新增：若检测到思考污染则强制重建）
        if output_path.exists() and output_path.stat().st_size > 100:
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    head = f.read(2000)
                if not _is_md_polluted(head):
                    msg_queue.put(("advance", task_id, 1))
                    continue
                else:
                    msg_queue.put(("log", f"[{ppt_name}] P{actual_slide_no} 检测到旧版本“思考过程”污染，已强制重建"))
            except Exception:
                # 读文件失败时，为避免卡住断点续传，沿用原逻辑：直接跳过
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