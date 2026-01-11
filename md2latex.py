import os
import re
import json
import time
import random
import logging
import argparse
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Generator, Tuple, Set

# === 依赖库检查 ===
try:
    from rich.progress import (
        Progress, SpinnerColumn, TextColumn, BarColumn,
        TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn,
        MofNCompleteColumn
    )
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    from rich.live import Live
except ImportError:
    print("❌ 缺少依赖库 [rich]。请运行: pip install rich")
    exit(1)

try:
    import dashscope
    from dashscope import Generation
except ImportError:
    print("❌ 缺少依赖库 [dashscope]。请运行: pip install dashscope")
    exit(1)

# ================= 配置区域 =================

DEFAULT_INPUT = "./markdown_output"
DEFAULT_OUTPUT = "./latex_output"

# 模型注册表 (单位: 元/1k tokens)
# RPM (Requests Per Minute) 用于计算平滑发射速率
MODEL_REGISTRY = {
    # === Qwen3-Max 系列 ===
    "1": { 
        "id": "qwen3-max", 
        "name": "Qwen3-Max (Stability)", 
        "desc": "稳定版，Batch半价，支持Agent", 
        "price_in": 0.0032, 
        "price_out": 0.0128,
        "rpm": 600,
        "tpm": 1000000 
    },
    "1b": { 
        "id": "qwen3-max-2025-09-23", 
        "name": "Qwen3-Max (09-23)", 
        "desc": "快照版", 
        "price_in": 0.006, 
        "price_out": 0.024,
        "rpm": 60,
        "tpm": 100000
    },
    "1c": { 
        "id": "qwen3-max-preview", 
        "name": "Qwen3-Max (Preview)", 
        "desc": "具备深度思考能力", 
        "price_in": 0.006, 
        "price_out": 0.024,
        "rpm": 600,
        "tpm": 100000 # 预览版通常较严格，保守估计
    },

    # === Qwen-Plus 系列 ===
    "2": { 
        "id": "qwen-plus", 
        "name": "Qwen-Plus (Stability)", 
        "desc": "能力同 07-28", 
        "price_in": 0.0008, 
        "price_out": 0.002,
        "rpm": 15000, 
        "tpm": 5000000
    },
    "2a": { 
        "id": "qwen-plus-latest", 
        "name": "Qwen-Plus (Latest)", 
        "desc": "能力同 12-01", 
        "price_in": 0.0008, 
        "price_out": 0.002,
        "rpm": 15000,
        "tpm": 1200000
    },
    "2b": { 
        "id": "qwen-plus-2025-12-01", 
        "name": "Qwen-Plus (12-01)", 
        "desc": "12月快照 (高TPM)", 
        "price_in": 0.0008, 
        "price_out": 0.002,
        "rpm": 60,
        "tpm": 1000000
    },
    "2c": { 
        "id": "qwen-plus-2025-09-11", 
        "name": "Qwen-Plus (09-11)", 
        "desc": "9月快照 (高TPM)", 
        "price_in": 0.0008, 
        "price_out": 0.002,
        "rpm": 60,
        "tpm": 1000000
    },
    "2d": { 
        "id": "qwen-plus-2025-07-28", 
        "name": "Qwen-Plus (07-28)", 
        "desc": "7月快照 (高TPM)", 
        "price_in": 0.0008, 
        "price_out": 0.002,
        "rpm": 60,
        "tpm": 1000000
    },

    # === DeepSeek 系列 (DashScope) ===
    "3": { 
        "id": "deepseek-v3.2", 
        "name": "DeepSeek-V3.2", 
        "desc": "685B 满血版", 
        "price_in": 0.002, 
        "price_out": 0.003,
        "rpm": 15000,
        "tpm": 1200000
    },
    "3a": { 
        "id": "deepseek-v3.2-exp", 
        "name": "DeepSeek-V3.2 Exp", 
        "desc": "实验版", 
        "price_in": 0.002, 
        "price_out": 0.003,
        "rpm": 15000
    },
}

DEFAULT_MODEL_KEY = "1" # 默认选 Qwen3-Max

INPUT_INFLATION_RATE = 1.2  # 输入膨胀系数 (Context + System Prompt)
OUTPUT_RATIO = 0.8          # 输出/输入 长度比例预估

# 分块配置
CHUNK_TOKEN_SIZE = 2500     
CHUNK_CHAR_SIZE = 4000      # 单次处理的 Markdown 字符数 (涵盖跨页长推导)
LOOK_AHEAD_CHARS = 800      # 上下文预览长度

# 并发配置 (参考 ppt2md.py)
MAX_CHAPTER_WORKERS = 1     # 全局：同时处理多少个章节 (建议 1，避免电脑卡顿)
MAX_CHUNK_WORKERS = 60      # 局部：每个章节内部开启多少并发 (全并发模式，配合限流器使用)

# ================= System Prompt =================

SYSTEM_PROMPT_TEMPLATE = r"""
你是一个专业的学术排版专家。你的任务是将结构化的 Markdown 课堂笔记重写为高质量、符合严格学术排版规范的 LaTeX 文档。并且对于文中出现的推导过程，如果原来的过程是非常详细的，则你必须保留详细的推导过程，不许省略过程，不许偷懒
对于原文，你只能非常少量地增加一些叙述性文字，来让文章更通顺，但是不要改变原意，完全无关的叙述性文字可以不写，宁缺毋滥
现在你正在处理一个长文档的第 {index} 部分（共 {total} 部分）。

【上下文指令】
1. **上文 Markdown**：仅供参考，帮助你理解前文定义的变量、环境或未完成的句子。**不要翻译上文**。
2. **当前 Markdown**：这是你**唯一需要翻译**并输出的内容。
3. **下文 Markdown**：仅供参考，用于逻辑连贯性判断。**不要翻译下文**。

【内容勘误与修正】
如果发现 Markdown 原始内容存在明显的OCR识别错误、公式符号不一致或语义矛盾：
1. 尽量推测文章的原意，不要乱修改。
2. 如果有重大的错误，请你在注释中写出错误
3. 尽量按照文章的原意来，不要乱修改！
4. 勘察错误只能放在注释里，不能放在正文中
正文中绝对不能出现勘察错误几个字

【LaTeX 格式核心规范 - 必须严格遵守】

### A. 数学公式
对于文中出现的推导过程，如果原来的过程是非常详细的，则你必须保留详细的推导过程，不许省略过程，不许偷懒
行内公式：使用 `$..$` ，比如 `$123$` ，不能使用`\(`
1. **唯一行间公式环境**：
   - **绝对禁止**使用 `\[ ... \]` 或 `$$ ... $$`。
   - **必须**使用 `\begin{equation} ... \end{equation}`。
2. **多行公式**：
   - 必须在 `equation` 环境中嵌套 `aligned` 环境。
   - 示例：
     \begin{equation}
       \begin{aligned}
         A &= B + C \\
           &= D
       \end{aligned}
     \end{equation}
3. **公式引用**：
   - 不是每个公式都需要标签，当你在上下文中需要引用时，才给被引用的公式添加标签 `\label{eq:xxx}`。
   - 或者你认为这个公式是比较重要的步骤，结果，结论，可能在后文被引用时，才给公式添加标签 `\label{eq:xxx}`。
   - 引用时**必须**使用 `\eqref{eq:xxx}` 命令。
4. 推导过程，如果原来的过程是非常详细的，则你必须保留详细的推导过程，不许省略过程
5. 你必须保留详细的你必须保留详细的推导过程！
### B. 定理与定义环境 (自定义环境)
遇到定义、定理、例题等，**必须**优先使用用户自定义环境。格式为 `\begin{env}{标题}{label}`。

**环境列表**：
- 定义: `\begin{definition}{标题}{label}` (引用前缀 `def:`)
- 定理: `\begin{theorem}{标题}{label}` (引用前缀 `thm:`)
- 引理: `\begin{lemma}{标题}{label}` (引用前缀 `lem:`)
- 推论: `\begin{corollary}{标题}{label}` (引用前缀 `cor:`)
- 命题: `\begin{proposition}{标题}{label}` (引用前缀 `pro:`)
- 性质: `\begin{property}{标题}{label}`
- 例子: `\begin{example} ... \end{example}`
- 证明: `\begin{proof} ... \end{proof}`
- 笔记: `\begin{note} ... \end{note}`
- 习题: `\begin{problem} ... \end{problem}` (作业模式)
- 解答: `\begin{solution} ... \end{solution}` (作业模式)

**引用规则**：
- 引用上述环境时，使用 `\ref{prefix:labelname}`。
- label 建议使用连字符 `-` 或驼峰命名，避免使用下划线 `_`。
- 如果没有标题，第二个参数留空 `{}`。如果没有标签，第三个参数留空 `{}` 或省略。

**One-Shot 示例**：
\begin{definition}{群的线性表示}{def:linear-rep}
    假设 $G=\{g_i\}$ 是一个抽象群...
\end{definition}
如\ref{def:linear-rep}所示...

### C. 图形与插图
1. **占位符**：读取 Markdown 中的 `> [!NOTE] 🖼️ Figure 描述`，转换为 LaTeX 占位符。
2. **详细描述**：必须在 `% AI绘图提示:` 后用中文详细描述图片内容（形状、布局、文字），并提示使用 TikZ 格式。
3. **格式要求**：
注意，这里的tikz代码的占位部分，是需要你自己来写一个版本的，同时ai绘图的文字描述也要保留，方便我后期修改
   ```latex
   % AI绘图提示词: (此处详细描述图像中是什么东西，具体是什么东西，给出ai的提示词，提示另一个ai用tikz格式来画图)
   \begin{figure}[H]
       \centering
       % TODO: 请在此处插入 TikZ 代码（不是等后来者插入，你现在就写一个）
       % \begin{tikzpicture} ... \end{tikzpicture}
       \caption{图片标题}
       \label{fig:label-name}
   \end{figure}
   ```
4. **引用命令**：
   - 文中引用图片时，**必须**使用自定义命令 `\figref{fig:label-name}`。
   - 示例：在\figref{fig:task4-action-potential}中...

### D. 文本格式
1. **强调**：严禁使用 `**...**`，**必须**使用 `\textbf{...}`。
2. **列表**：使用 `itemize` (无序) 或 `enumerate` (有序)。**严禁**手动编号。

### E. 文档结构自动重建 (极重要)
原 Markdown 文档可能由多张 PPT 识别而来，结构可能破碎或缺失。作为学术排版专家，你需要**重建层级**：
1. **显式标题转换**：
   - Markdown `#` (一级标题) -> LaTeX `\section{...}`
   - Markdown `##` (二级标题) -> LaTeX `\subsection{...}`
    - Markdown `###` (三级标题) -> LaTeX `\subsubsection{...}`
    - 若原 Markdown 中存在 `# Slide N` 之类的占位标题，请将其视作位置标记，转换为注释或忽略，优先遵循架构师指令给出的章节层级。
2. **隐式结构补全 (自动总结)**：
   - 绝大多数情况下，原 MD 缺少标题。你**必须**根据【本章全局目录】和内容语义，主动构建文档层级。
   - **分层策略 (Sectioning Strategy - 极其重要)**：
     - **多用 \\section**：参考【本章全局目录】，如果当前 Slides (e.g. Slide 10-15) 进入了一个新的主要讨论对象（例如从“定义”转到“性质”，或从“理论”转到“例题”），**必须**开启新的 `\section{...}`。
     - **避免过度嵌套**：不要把整章几十页内容都放在同一个 `\section` 下。通常每 5-10 页 PPT 就应该对应一个 `\section`。
     - **层级逻辑**：
       - `\section{...}`: 主要话题 (e.g. "协变导数的定义")
       - `\subsection{...}`: 子话题 (e.g. "标量场的协变导数")
       - `\subsubsection{...}`: 具体细节/推导步骤
         - **禁止**生成长篇大论而没有任何 `\subsection` 的正文。
     - 章节层级必须以架构师指令为最高优先级；如有冲突，以指令为准。
3. **上下文连贯性**：
   - 利用【上文 Markdown】判断当前是否已经处于某个 Section/Subsection 中。
   - 如果当前内容是上文的延续，**不要**重复生成标题。
   - 如果当前内容开启了新的话题（例如从定义转入性质，或开始新的证明），**必须**插入新的子标题。

【输入数据】
这里是当前需要处理的 Markdown 片段（Look-ahead 包含在末尾用于参考）：
"""

# ================= 外部导入标准 Prompt 模板 =================

EXTERNAL_MAP_PROMPT_TEMPLATE = r"""
# Role
你是一位专业的学术教材主编。

# Context
我将上传一份课堂笔记的“页面摘要清单”（toc_source.txt），其中包含了每一页 PPT (Slide) 的编号、关键词和内容摘要。

# Task
请分析这份摘要流的逻辑连贯性，将其重构为一份结构严谨、层级清晰的 LaTeX 目录结构数据。

# Requirements
1. **聚合与归纳**：
     - 不要为每一页都生成标题。
     - 请识别连续讨论同一话题的多个 Slide（例如 Slide 5-10），将其合并为一个 `section`。
     - 只有在话题发生显著转变时，才开启新的 `section`。
     - 适当使用 `subsection` 来处理大章节下的细分话题。

2. **完整性**：
     - 你的结构必须覆盖从 Slide 1 到 Slide {last_slide} 的所有页面，不能遗漏。
     - `start_slide` 和 `end_slide` 必须连续且不重叠。
    - 在 meta 中填写 `total_slides`: {last_slide}。

3. **Output Format (Strict JSON)**
     请直接输出 JSON 代码，不要包含 Markdown 代码块标记（```json），格式如下：

{
    "meta": {
        "mode": "chapter", 
        "title": "请根据内容拟定一个总标题",
        "total_slides": {last_slide}
    },
    "structure": [
        {
            "level": "section",
            "title": "第一节的标题",
            "start_slide": 1,
            "end_slide": 10,
            "subsections": [
                 {
                     "level": "subsection",
                     "title": "子节标题",
                     "start_slide": 1,
                     "end_slide": 5
                 },
                 {
                     "level": "subsection",
                     "title": "子节标题",
                     "start_slide": 6,
                     "end_slide": 10
                 }
            ]
        },
        {
            "level": "section",
            "title": "第二节标题",
            "start_slide": 11,
            "end_slide": 20
        }
    ]
}
"""

# ================= 工具类 =================

class APIRateLimiter:
    """全局API速率限制器 - 同时考量 RPM 和 TPM"""
    def __init__(self, rpm, tpm=None):
        self.rpm = rpm
        self.tpm = tpm
        
        # 估算每请求 Token (Input ~4k + Output ~2k = 6k conservative)
        avg_tokens_per_req = 6000 
        
        # 计算基于 RPM 的 RPS
        rps_by_rpm = rpm / 60.0
        
        # 计算基于 TPM 的 RPS (如果有 TPM 限制)
        rps_by_tpm = 999999
        if tpm:
            # TPM / 60 = Tokens per second
            # T/s / AvgTokens = RPS
            rps_by_tpm = (tpm / 60.0) / avg_tokens_per_req
            
        # 取两者较小值作为安全 RPS，并留 10% 余量
        safe_rps = min(rps_by_rpm, rps_by_tpm) * 0.9
        
        self.interval = 1.0 / safe_rps if safe_rps > 0 else 1.0
        self.last_req_time = 0
        self.lock = threading.Lock()
        
        # Log 初始计算结果
        print(f"    [RateLimiter] RPM={rpm}, TPM={tpm or 'Inf'}")
        print(f"    [RateLimiter] Safe RPS={safe_rps:.2f} (Interval={self.interval:.2f}s)")
        
    def wait_for_slot(self):
        """阻塞当前线程直到获得发送许可"""
        with self.lock:
            now = time.time()
            # 如果距离上次请求时间太短，强制睡眠
            elapsed = now - self.last_req_time
            if elapsed < self.interval:
                sleep_time = self.interval - elapsed
                time.sleep(sleep_time)
            
            self.last_req_time = time.time()

class CostEstimator:
    """负责扫描目录，交互选择，计算Token，展示价格"""
    def __init__(self, root_dir: str, model_config: dict):
        self.root_dir = Path(root_dir)
        self.model_config = model_config
        self.console = Console()
        self.all_tasks = {}

    def scan(self) -> dict:
        """扫描所有可用章节"""
        if not self.root_dir.exists():
            self.console.print(f"[bold red]❌ 输入目录不存在: {self.root_dir}[/]")
            return {}

        # === 交互询问扫描深度 ===
        self.console.print(Panel("📂 目录扫描设置", style="bold blue"))
        depth_input = input("👉 请输入扫描深度 (层级数, 默认为 1, 0 表示无限递归): ").strip()
        max_depth = 1
        if depth_input.isdigit():
            max_depth = int(depth_input)
            if max_depth == 0: max_depth = 99

        tasks = {}
        base_depth = len(self.root_dir.parts)
        
        self.console.print(f"[dim]正在扫描目录 (深度: {max_depth})...[/]")

        # 扫描 Chapter 文件夹
        for root, dirs, files in os.walk(self.root_dir):
            root_path = Path(root)
            current_depth = len(root_path.parts) - base_depth
            
            # 1. 深度控制：如果到达 max_depth，停止向下遍历 (修剪 dirs)
            # 例如 max_depth=1: current_depth=0 是 root, current_depth=1 是 chapter. 
            # 当我们处在 depth=1 时，如果不修剪，下次会进入 depth=2。
            # 所以在 current_depth >= max_depth 时，不再允许进入子目录。
            if current_depth >= max_depth:
                del dirs[:]
            
            # 2. 根目录本身通常不视为 Chapter，除非它直接包含 Slide
            # 但按惯例，我们通常跳过 root 本身，只看子文件夹
            if current_depth < 1:
                continue

            # 3. 检查当前目录是否包含 Slide 文件
            if root_path.name.startswith('.'): continue
            
            # 查找 Slide_*.md
            md_files = []
            for f_name in files:
                if f_name.startswith("Slide_") and f_name.endswith(".md"):
                     if "_FULL" in f_name or "merged" in f_name.lower():
                        continue
                     md_files.append(root_path / f_name)
            
            if not md_files:
                continue
                
            md_files.sort(key=lambda p: self._extract_slide_num(p.name))
            
            # 4. 生成任务 Key (使用相对路径)
            try:
                chap_name = str(root_path.relative_to(self.root_dir))
            except:
                chap_name = root_path.name

            tasks[chap_name] = {
                "files": md_files,
                "char_count": -1 # 待计算
            }
            
        self.all_tasks = tasks
        return tasks

    def interactive_select(self) -> dict:
        """交互式选择要处理的章节 (支持页码过滤)"""
        if not self.all_tasks:
            self.console.print("[yellow]⚠️ 未找到任何 Slide_*.md 文件[/]")
            return {}
            
        # 排序章节名
        sorted_names = sorted(self.all_tasks.keys(), key=lambda x: (len(x), x))
        
        self.console.print(Panel(f"📂 发现 {len(sorted_names)} 个章节", style="bold blue"))
        for i, name in enumerate(sorted_names):
             self.console.print(f"  [[bold cyan]{i+1}[/]] {name} ({len(self.all_tasks[name]['files'])} slides)")

        selection = input("\n👉 请选择要处理的章节 (例如: 1,3-5 | a=全选): ").strip()
        
        selected_tasks = {}
        if selection.lower() == 'a':
            # 使用浅拷贝，避免修改原始数据
            selected_tasks = {k: v.copy() for k, v in self.all_tasks.items()}
        else:
            try:
                # 解析范围 1,3-5
                indices = set()
                parts = selection.split(',')
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        indices.update(range(start, end + 1))
                    elif part:
                        indices.add(int(part))
                
                for idx in indices:
                    if 1 <= idx <= len(sorted_names):
                        name = sorted_names[idx-1]
                        selected_tasks[name] = self.all_tasks[name].copy()
            except Exception as e:
                self.console.print(f"[red]❌ 选择解析错误: {e}[/]")
                return {}
        
        if not selected_tasks:
            self.console.print("[yellow]未选择任何任务[/]")
            return {}

        # === 高级选项: 页码过滤 ===
        self.console.print("\n[bold cyan]🔧 高级选项[/]")
        enable_filter = input("👉 是否需要指定每一章的 Slide 页码范围? (y/N): ").strip().lower()
        
        if enable_filter == 'y':
            for name in list(selected_tasks.keys()):
                info = selected_tasks[name]
                all_files = info['files']
                if not all_files: continue
                
                # 获取首尾页码供参考
                first_num = self._extract_slide_num(all_files[0].name)
                last_num = self._extract_slide_num(all_files[-1].name)
                
                self.console.print(f"\n  📖 [bold]{name}[/] (Slide {first_num}-{last_num}, 共 {len(all_files)} 页)")
                range_str = input(f"     请输入页码范围 (例如 1-5,10 | 回车=保留全部): ").strip()
                
                if range_str:
                    filtered = self._filter_files(all_files, range_str)
                    if filtered:
                        count_diff = len(all_files) - len(filtered)
                        selected_tasks[name]['files'] = filtered
                        selected_tasks[name]['char_count'] = -1 # 标记重算
                        self.console.print(f"     ✅ 已过滤，选中 {len(filtered)} 页 (排除 {count_diff} 页)")
                    else:
                        self.console.print(f"     [red]⚠️ 范围无效或未命中，保留全部[/]")
            
        return selected_tasks

    def _filter_files(self, files: List[Path], range_str: str) -> List[Path]:
        """根据 1,3-5 格式过滤文件列表"""
        try:
            target_indices = set()
            parts = range_str.split(',')
            for part in parts:
                part = part.strip()
                if '-' in part:
                    s, e = map(int, part.split('-'))
                    target_indices.update(range(s, e + 1))
                elif part:
                    target_indices.add(int(part))
            
            filtered = []
            for f in files:
                num = self._extract_slide_num(f.name)
                if num in target_indices:
                    filtered.append(f)
            return filtered
        except:
            return []

    def estimate(self, tasks: dict) -> bool:
        """计算选中任务的成本"""
        total_chars = 0
        self.console.print("\n[bold green]正在分析选中章节...[/]")
        
        for name, info in tasks.items():
            if info['char_count'] == -1:
                c_count = 0
                for md in info['files']:
                    try:
                        content = md.read_text(encoding='utf-8')
                        clean_content = self._clean_content_for_est(content)
                        c_count += len(clean_content)
                    except: pass
                info['char_count'] = c_count
            total_chars += info['char_count']

        # 计算成本
        total_tokens_est = total_chars / 1.5
        input_tokens_billed = total_tokens_est * INPUT_INFLATION_RATE
        output_tokens_billed = input_tokens_billed * OUTPUT_RATIO
        
        p_in = self.model_config['price_in']
        p_out = self.model_config['price_out']
        
        est_cost = (input_tokens_billed / 1000 * p_in) + \
                   (output_tokens_billed / 1000 * p_out)

        self._show_table(tasks, total_chars, total_tokens_est, est_cost)
        return True

    def _clean_content_for_est(self, text):
        return re.sub(r'<CTX>.*?</CTX>', '', text, flags=re.DOTALL)

    def _extract_slide_num(self, filename):
        m = re.search(r'(\d+)', filename)
        return int(m.group(1)) if m else 9999

    def _show_table(self, tasks, chars, tokens, cost):
        table = Table(title=f"💰 成本预估 ({len(tasks)} 章节)", show_header=True)
        table.add_column("Chapter", style="cyan")
        table.add_column("页数", justify="right")
        table.add_column("字符数", justify="right")
        table.add_column("预估成本", justify="right", style="green")

        # 只显示前10个及汇总，避免刷屏
        keys = list(tasks.keys())
        limit = 15
        for name in keys[:limit]:
            info = tasks[name]
            table.add_row(name, str(len(info['files'])), str(info['char_count']), "-")
        
        if len(tasks) > limit:
            table.add_row(f"... 以及其他 {len(tasks)-limit} 个章节 ...", "", "", "")

        table.add_row("TOTAL", "", f"{chars:,}", f"¥ {cost:.2f}", style="bold red")
        self.console.print(table)
        
        m_name = self.model_config['name']
        p_in_million = self.model_config['price_in'] * 1000
        p_out_million = self.model_config['price_out'] * 1000
        
        self.console.print(f"[dim]Total Est. Tokens: {tokens/1000:.1f}k[/]")
        self.console.print(f"[bold purple]Model: {m_name}[/] [dim](In: ¥{p_in_million:.1f}/1M | Out: ¥{p_out_million:.1f}/1M)[/]")


class ContextManager:
    """负责切分Markdown，生成并行任务包"""
    def __init__(self, output_file: Path):
        self.output_file = output_file
        
    def load_and_merge_files(self, md_files: List[Path]) -> Tuple[str, List[dict]]:
        """读取并线性化所有 MD 文件，同时构建 Slide 索引"""
        full_text = ""
        slide_map = [] # [{start: 0, end: 100, num: 1, info: {...}}]
        
        current_pos = 0
        
        for f in md_files:
            text = f.read_text(encoding='utf-8')
            
            # 提取 CTX 信息
            ctx_match = re.search(r'<CTX>(.*?)</CTX>', text, flags=re.DOTALL)
            ctx_info = {}
            if ctx_match:
                try:
                    ctx_info = json.loads(ctx_match.group(1))
                except:
                    pass
            
            # 提取 Slide 编号
            m = re.search(r'(?:^|\n)# Slide (\d+)', text)
            slide_num = int(m.group(1)) if m else 999
            
            # 移除 CTX (但保留 info 在内存)
            text_clean = re.sub(r'<CTX>.*?</CTX>', '', text, flags=re.DOTALL)
            
            # 转义 Slide 标记
            text_clean = re.sub(r'(^|\n)# Slide (\d+)', r'\1<!-- Slide \2 -->', text_clean)
            
            text_len = len(text_clean)
            slide_map.append({
                "start": current_pos,
                "end": current_pos + text_len,
                "num": slide_num,
                "info": ctx_info,
                "original_obj": f
            })
            
            full_text += text_clean + "\n\n"
            current_pos += text_len + 2 # \n\n
            
        return full_text, slide_map

    def generate_chapter_toc(self, slide_map: List[dict]) -> str:
        """生成全章 Slide 结构目录"""
        toc = "【本章全局目录 (Global Chapter Outline)】\n"
        last_kw = ""
        
        # 为了节省 token，我们将目录简化。只记录有显著关键词变化的 slide
        for s in slide_map:
            s_num = s['num']
            keywords = s['info'].get('keywords', [])
            summary = s['info'].get('summary', 'No Summary')
            kw_str = ", ".join(keywords[:2]) if keywords else ""
            
            # 记录条件: 
            # 1. 第一页
            # 2. 关键词与上一条不同 (Topic Shift)
            # 3. 每隔 10 页强制记录一次 (Keep Track)
            should_record = False
            if s_num == 1: should_record = True
            elif kw_str and kw_str != last_kw: should_record = True
            elif s_num % 10 == 0: should_record = True
            
            if should_record:
                # 截断 summary
                summ_short = summary[:30].replace('\n', ' ')
                toc += f"- Slide {s_num}: [{kw_str}] {summ_short}...\n"
                last_kw = kw_str
                
        return toc

    def create_smart_chunks(self, full_text: str, slide_map: List[dict], instruction_lookup: dict | None = None) -> List[dict]:
        """智能切分并构建带结构感知的任务（查表逻辑优先）"""
        chunks = self._smart_split(full_text)
        tasks = []
        total = len(chunks)
        
        # 生成全局目录
        global_toc = self.generate_chapter_toc(slide_map)

        # 辅助函数：根据字符位置找 Slide 信息
        def get_overlapping_slides(chunk_start, chunk_end):
            overlaps = []
            for s in slide_map:
                # 检查区间重叠: max(start1, start2) < min(end1, end2)
                if max(chunk_start, s['start']) < min(chunk_end, s['end']):
                    overlaps.append(s)
            return overlaps

        current_char_ptr = 0
        for i, chunk in enumerate(chunks):
            chunk_len = len(chunk)
            chunk_start = current_char_ptr
            chunk_end = current_char_ptr + chunk_len
            
            # 获取上下文
            prev_ctx = chunks[i-1][-LOOK_AHEAD_CHARS:] if i > 0 else ""
            next_ctx = chunks[i+1][:LOOK_AHEAD_CHARS] if i < total - 1 else ""
            
            # 获取结构信息
            related_slides = get_overlapping_slides(chunk_start, chunk_end)
            
            # 判断 Section 连续性
            # 获取当前块第一个 Slide 的前一个 Slide 的信息 (用于判断 title 变化)
            prev_slide_info = None
            first_slide_idx = -1
            
            if related_slides:
                # 找到 related_slides[0] 在 slide_map 中的 index
                try:
                    first_slide_idx = slide_map.index(related_slides[0])
                    if first_slide_idx > 0:
                        prev_slide_info = slide_map[first_slide_idx - 1]
                except: pass
            
            # 如果提供了查表指令，则根据第一个覆盖的 Slide 生成架构师指令
            structure_hint = ""
            map_directive: list[dict] = []
            if instruction_lookup and related_slides:
                # 若当前块覆盖多个 slide，优先选择其中最小编号且有指令的 slide
                directive_slide = None
                directive_list = None
                for s in sorted(related_slides, key=lambda x: x['num']):
                    maybe = instruction_lookup.get(s['num'])
                    if maybe:
                        directive_slide = s['num']
                        directive_list = maybe
                        break
                if directive_list:
                    # 附带 slide 编号，便于后续提示
                    map_directive = [{ **d, 'slide': directive_slide } for d in directive_list]
                    lines = ["【架构师指令】"]
                    for d in directive_list:
                        if d['type'] == 'START_SECTION':
                            lines.append(
                                f"- 当前是新章节《{d['title']}》的起始页（Slide {directive_slide}）。请在开头插入 \\section{{{d['title']}}}。"
                            )
                        elif d['type'] == 'START_SUBSECTION':
                            lines.append(
                                f"- 当前是子章节《{d['title']}》的起始页（Slide {directive_slide}），父章节《{d.get('parent','')}》。请在开头插入 \\subsection{{{d['title']}}}。"
                            )
                        elif d['type'] == 'NO_HEADER':
                            lines.append(
                                f"- 当前处于章节《{d.get('parent','')}》内部（Slide {directive_slide}）。请勿生成章节或子章节标题，只输出正文。"
                            )
                    structure_hint = "\n".join(lines)
            if not structure_hint:
                structure_hint = self._generate_structure_hint(related_slides, prev_slide_info)

            tasks.append({
                "index": i,
                "total": total,
                "current": chunk,
                "prev": prev_ctx,
                "next": next_ctx,
                "structure_hint": structure_hint,
                "chapter_toc": global_toc,
                "map_directive": map_directive
            })
            current_char_ptr += chunk_len
            
        return tasks

    def _generate_structure_hint(self, current_slides, prev_slide_global):
        """生成给模型的结构提示，利用 ctx 避免 section 重复"""
        if not current_slides:
            return "当前内容无法定位到具体 Slide。"
            
        hint = "【文档结构映射 (Structure Mapping)】\n"
        
        # 获取当前块覆盖的主要 Summary/Title
        for idx, s in enumerate(current_slides):
            s_num = s['num']
            summary = s['info'].get('summary', '无摘要')
            # 尝试提取 keywords 作为潜在标题
            keywords = s['info'].get('keywords', [])
            kw_str = ", ".join(keywords[:2]) if keywords else ""
            
            hint += f"- Slide {s_num}: {summary[:50]}... (Keywords: {kw_str})\n"
            
        # 关键逻辑：判断是否是新的一章
        first_current = current_slides[0]
        
        start_new_section = True
        if prev_slide_global:
            # 比较摘要或关键词相似度，这里简单粗暴比较前 10 个字
            curr_sum = first_current['info'].get('summary', '')
            prev_sum = prev_slide_global['info'].get('summary', '')
            
            # 如果摘要开头高度相似，或 explicit keywords 包含 "Continued" 之类的逻辑
            # 这里简化逻辑：如果两张 Slide 的 CTX 极其相似，大概率是同一个 PPT section 的拆分
            if curr_sum[:10] == prev_sum[:10]:
                 start_new_section = False
                 hint += f"\n[指令] Slide {first_current['num']} 的内容似乎是上一页 Slide {prev_slide_global['num']} 的接续 (摘要相似)。\n"
                 hint += "**请勿重复生成 \\section{} 标题**，除非内容有明显的逻辑转折。\n"
            else:
                 hint += f"\n[指令] Slide {first_current['num']} 开始了新的话题 (与前一页摘要不同)。\n"
                 hint += "**请根据 Slide 内容和 Keywords 生成适当的 \\section{} 或 \\subsection{} 标题**。\n"
        else:
             hint += "\n[指令] 这是文档开头，请根据内容生成并置顶 \\section{}。\n"
             
        return hint

    def _smart_split(self, text: str) -> List[str]:
        """按长度切分，优先在段落或标题处断开"""
        chunks = []
        length = len(text)
        start = 0
        
        while start < length:
            # 目标切分点
            target_end = min(start + CHUNK_CHAR_SIZE, length)
            
            # 如果到达末尾，直接切
            if target_end >= length:
                chunks.append(text[start:])
                break
                
            # 向回搜寻最佳切分点 (段落空行 或 标题)
            search_window = text[start:target_end]
            best_split = -1
            
            # 1. 标题 (### ) - 优先
            header_match = list(re.finditer(r'\n#{1,3} ', search_window))
            if header_match:
                # 只考虑位于窗口后半部分的标题，避免切太碎
                valid_headers = [m for m in header_match if m.start() > CHUNK_CHAR_SIZE * 0.5]
                if valid_headers:
                    best_split = valid_headers[-1].start()
            
            # 2. 段落 (\n\n)
            if best_split == -1:
                idx = search_window.rfind('\n\n')
                if idx != -1 and idx > CHUNK_CHAR_SIZE * 0.5:
                     best_split = idx
            
            # 3. 换行 (\n) - 只有当找不到段落时才稍微退而求其次
            if best_split == -1:
                idx = search_window.rfind('\n')
                if idx != -1 and idx > CHUNK_CHAR_SIZE * 0.8: 
                     best_split = idx
            
            if best_split != -1:
                end = start + best_split
            else:
                end = target_end # 没找到合适点，强制切分
                
            chunks.append(text[start:end])
            start = end 
            
        return chunks


class LatexGenerator:
    """负责与DashScope API交互"""
    def __init__(self, model_name, api_key=None):
        self.model = model_name
        self.api_key = api_key
        if not self.api_key:
             self.api_key = os.getenv("DASHSCOPE_API_KEY")
        dashscope.api_key = self.api_key

    def generate_stream(self, prompt: str) -> Generator[str, None, None]:
        """流式生成，过滤 content"""
        try:
            responses = Generation.call(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                result_format='message',
                enable_thinking=True,
                incremental_output=True,
                stream=True
            )
            
            for chunk in responses:
                if chunk.status_code == 200:
                    delta = chunk.output.choices[0].message
                    # Safely access content
                    content = getattr(delta, 'content', None)
                    if content:
                        yield content
                    
                    # Safely access reasoning_content
                    # Handle potential KeyError from AttrDict.__getattr__ if attribute missing
                    try:
                        reasoning = getattr(delta, 'reasoning_content', None)
                        if reasoning:
                            pass # 忽略思考过程
                    except (AttributeError, KeyError):
                        pass
                else:
                    raise Exception(f"API Error: {chunk.code} - {chunk.message}")

        except Exception as e:
            raise e


class MapGenerator:
    """使用 LLM (默认 Qwen-Plus) 生成结构地图"""
    def __init__(self, model_name="qwen-plus", api_key=None):
        self.model = model_name
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        dashscope.api_key = self.api_key

    def _build_prompt(self, toc_text: str, last_slide: int, mode: str, title: str = "") -> str:
        tmpl = EXTERNAL_MAP_PROMPT_TEMPLATE.replace('{last_slide}', str(last_slide or '最后一页'))
        extra = f"\n# Extra\n请确保 meta.mode = \"{mode}\"，meta.total_slides = {last_slide}，meta.title 可填写 \"{title}\"。"
        return f"{tmpl}\n\n{toc_text}\n{extra}"

    def _parse_json(self, text: str) -> dict:
        """尝试解析 JSON，去除围栏并做简单修复"""
        cleaned = text.strip()
        cleaned = re.sub(r'^```json\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'^```\s*', '', cleaned)
        cleaned = re.sub(r'```\s*$', '', cleaned)
        # 截取最外层大括号
        m = re.search(r'\{[\s\S]*\}$', cleaned)
        if m:
            cleaned = m.group(0)
        try:
            return json.loads(cleaned)
        except Exception:
            # 简单补全引号类错误可在此扩展；当前失败则抛出
            raise

    def generate_structure(self, toc_text: str, last_slide: int, mode: str = "chapter", title: str = "") -> dict:
        prompt = self._build_prompt(toc_text, last_slide, mode, title)
        resp = Generation.call(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            result_format='message',
            enable_thinking=False,
            stream=False
        )
        if resp.status_code != 200:
            raise Exception(f"MapGenerator API Error: {resp.code} - {resp.message}")
        content = resp.output.choices[0].message.content if resp.output.choices else ""
        data = self._parse_json(content)
        # 补充或纠正 meta 信息
        meta = data.setdefault('meta', {})
        meta.setdefault('mode', mode)
        meta.setdefault('total_slides', last_slide)
        meta.setdefault('title', title or "")
        return data

# ================= 主控制器 =================

class WorkflowController:
    def __init__(self, input_dir, output_dir, model_arg=None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.console = Console()
        
        # 选择模型
        self.selected_model_config = self._select_model(model_arg)
        self.model_name = self.selected_model_config['id']
        # 架构师模型（单独选择，默认 qwen-plus）
        self.architect_model = 'qwen-plus'
        
        # 初始化限流器 (支持 TPM 约束)
        rpm = self.selected_model_config.get('rpm', 600)
        tpm = self.selected_model_config.get('tpm', None) # 获取 TPM 配置
        
        self.rate_limiter = APIRateLimiter(rpm, tpm)
        self.console.print(f"[dim]⚡ 限流器已启动: Limit ~ {rpm} RPM / {tpm if tpm else 'Inf'} TPM[/]")

        self._setup_logger()

        # 运行时范围模式：chapter/book
        self.scope_mode = None
        # 结构地图来源：internal/external
        self.map_source = None

    def _detect_scope_mode(self, tasks: dict) -> str:
        """根据所选任务判断范围模式（单章/书籍）"""
        # 如果选择了多个不同子目录，则认为是 book 模式
        if len(tasks) > 1:
            return 'book'
        # 单个任务但路径包含子层级也可能是 book 的某章，此处统一为 chapter
        return 'chapter'

    def generate_toc_source_file(self, chap_name: str, md_files: List[Path], out_dir: Path) -> Path:
        """遍历 Slide 提取 <CTX> summary/keywords，生成 toc_source.txt"""
        lines, last_slide = self._collect_toc_source(md_files)

        # 输出路径：输出目录/intermediates/chap_name/toc_source.txt
        inter_dir = out_dir / 'intermediates' / chap_name
        inter_dir.mkdir(parents=True, exist_ok=True)
        toc_path = inter_dir / 'toc_source.txt'
        toc_path.write_text("\n".join(lines), encoding='utf-8')

        # 打印标准 Prompt 模板
        tmpl = EXTERNAL_MAP_PROMPT_TEMPLATE.replace('{last_slide}', str(last_slide or '最后一页'))
        self.console.print(Panel("[bold]外部导入 - 标准 Prompt 模板[/]", style="bold cyan"))
        self.console.print(Markdown(tmpl))
        self.console.print(f"\n已生成摘要源文件: [green]{toc_path}[/] \n请上传给外部模型并将生成的 JSON 保存为 structure_map.json 后重新运行。")
        return toc_path

    def _collect_toc_source(self, md_files: List[Path]) -> tuple[list[str], int]:
        lines = []
        last_slide = 0
        for f in md_files:
            try:
                text = f.read_text(encoding='utf-8')
            except Exception:
                continue
            ctx_match = re.search(r'<CTX>(.*?)</CTX>', text, flags=re.DOTALL)
            ctx_info = {}
            if ctx_match:
                try:
                    ctx_info = json.loads(ctx_match.group(1))
                except Exception:
                    ctx_info = {}
            m = re.search(r'(?:^|\n)# Slide (\d+)', text)
            slide_num = int(m.group(1)) if m else 999
            last_slide = max(last_slide, slide_num)
            keywords = ctx_info.get('keywords', [])
            summary = ctx_info.get('summary', '').replace('\n', ' ').strip()
            kw_str = ", ".join(keywords)
            lines.append(f"Slide {slide_num}: [{kw_str}] {summary}")
        return lines, last_slide

    def _load_structure_map(self, chap_name: str, input_dir: Path, out_dir: Path) -> dict | None:
        """尝试加载 structure_map.json（优先输出中间目录，其次输入章节目录）"""
        candidates = [
            out_dir / 'intermediates' / chap_name / 'structure_map.json',
        ]
        # 输入章节目录
        in_chap_dir = Path(input_dir) / chap_name
        candidates.append(in_chap_dir / 'structure_map.json')
        for p in candidates:
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding='utf-8'))
                except Exception:
                    pass
        return None

    def _build_instruction_lookup(self, structure_map: dict) -> dict:
        """将结构 JSON 转换为查表：slide_num -> 指令列表（按层级优先级排序）"""
        if not structure_map:
            return {}

        lookup: dict[int, list] = {}
        nodes = structure_map.get('structure', [])

        def add_directive(slide_num: int, directive: dict, priority: int):
            if slide_num not in lookup:
                lookup[slide_num] = []
            lookup[slide_num].append({ **directive, 'priority': priority })

        for sec in nodes:
            sec_title = sec.get('title', '')
            s = int(sec.get('start_slide', 0))
            e = int(sec.get('end_slide', 0))
            if s:
                add_directive(s, { 'type': 'START_SECTION', 'title': sec_title }, priority=1)
            # 中间页标记 NO_HEADER（低优先级）
            for num in range(s+1, e+1):
                add_directive(num, { 'type': 'NO_HEADER', 'parent': sec_title }, priority=99)

            for sub in sec.get('subsections', []) or []:
                sub_title = sub.get('title', '')
                ss = int(sub.get('start_slide', 0))
                se = int(sub.get('end_slide', 0))
                if ss:
                    add_directive(ss, { 'type': 'START_SUBSECTION', 'title': sub_title, 'parent': sec_title }, priority=2)
                for num in range(ss+1, se+1):
                    add_directive(num, { 'type': 'NO_HEADER', 'parent': sec_title }, priority=99)

        # 将每个 slide 的指令按 priority 排序
        for k, v in lookup.items():
            lookup[k] = sorted(v, key=lambda x: x.get('priority', 50))
        return lookup

    def _validate_structure_map(self, data: dict) -> None:
        """校验外部/内部生成的 structure_map.json 合法性"""
        if not isinstance(data, dict):
            raise ValueError("structure_map 需为对象")
        meta = data.get('meta', {})
        mode = meta.get('mode')
        if mode not in ('chapter', 'book'):
            raise ValueError("meta.mode 必须是 'chapter' 或 'book'")
        if 'title' not in meta:
            raise ValueError("meta.title 缺失")

        structure = data.get('structure')
        if not isinstance(structure, list) or not structure:
            raise ValueError("structure 必须是非空列表")

        def _check_block(block, level_expected):
            if block.get('level') != level_expected:
                raise ValueError(f"{level_expected} 缺失或 level 非 {level_expected}")
            if 'title' not in block:
                raise ValueError(f"{level_expected} 缺少 title")
            s = block.get('start_slide')
            e = block.get('end_slide')
            if not (isinstance(s, int) and isinstance(e, int) and 1 <= s <= e):
                raise ValueError(f"{level_expected} 的 start/end 非法")

        prev_end = 0
        max_end = 0
        for sec in structure:
            _check_block(sec, 'section')
            if sec['start_slide'] <= prev_end:
                raise ValueError("section 的页码存在重叠或未递增")
            prev_end = sec['end_slide']
            max_end = max(max_end, sec['end_slide'])
            for sub in sec.get('subsections', []) or []:
                _check_block(sub, 'subsection')
                if not (sec['start_slide'] <= sub['start_slide'] <= sub['end_slide'] <= sec['end_slide']):
                    raise ValueError("subsection 的页码不在所属 section 范围内")
                max_end = max(max_end, sub['end_slide'])

        # 容错：若 total_slides 缺失或非法，则用最大 end_slide 回填
        total_slides = meta.get('total_slides')
        if not (isinstance(total_slides, int) and total_slides > 0):
            meta['total_slides'] = max_end if max_end > 0 else 1

    def _select_model(self, model_arg):
        """交互式或参数式选择模型"""
        # 如果命令行指定了有效的ID，直接使用
        if model_arg:
            # 尝试通过ID反查
            for key, cfg in MODEL_REGISTRY.items():
                if cfg['id'] == model_arg:
                    return cfg
            # 或者是Key
            if model_arg in MODEL_REGISTRY:
                return MODEL_REGISTRY[model_arg]
        
        # 否则进入交互选择
        self.console.print(Panel("🤖 请选择推理模型 (Model Selection)", style="bold purple"))
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Key", style="cyan", justify="center")
        table.add_column("Model ID", style="green")
        table.add_column("Description")
        table.add_column("Price (In/Out per 1M)", justify="right")
        
        for key, cfg in MODEL_REGISTRY.items():
            p_in = cfg['price_in'] * 1000
            p_out = cfg['price_out'] * 1000
            table.add_row(
                f"[{key}]", 
                cfg['id'], 
                cfg['desc'], 
                f"¥{p_in:.1f} / ¥{p_out:.1f}"
            )
            
        self.console.print(table)
        
        choice = input(f"\n👉 请输入序号 (默认 {DEFAULT_MODEL_KEY}): ").strip()
        if not choice:
            choice = DEFAULT_MODEL_KEY
            
        if choice in MODEL_REGISTRY:
            cfg = MODEL_REGISTRY[choice]
            self.console.print(f"✅ 已选择: [bold green]{cfg['name']}[/]\n")
            return cfg
        else:
            self.console.print(f"[red]❌ 无效选择，使用默认: {MODEL_REGISTRY[DEFAULT_MODEL_KEY]['name']}[/]\n")
            return MODEL_REGISTRY[DEFAULT_MODEL_KEY]

    def _setup_logger(self):
        log_path = Path("./log/md2latex")
        log_path.mkdir(parents=True, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        self.log_file = log_path / f"md2latex_{timestamp}.log"
        
        self.logger = logging.getLogger("MD2LaTeX")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers.clear() # 防止重复
        
        # 显式添加 FileHandler，确保不受 basicConfig 影响
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def run(self):
        global MAX_CHUNK_WORKERS
        self.console.print(Panel(f"MD2LaTeX Pro ({self.model_name})", style="bold purple"))
        self.console.print(f"Input: {self.input_dir}")
        self.console.print(f"Output: {self.output_dir}")
        
        # === 允许用户调整并发数 ===
        self.console.print(f"Default Inner Workers: {MAX_CHUNK_WORKERS}")
        w_input = input(f"👉 按回车使用默认并发 ({MAX_CHUNK_WORKERS}), 或输入新数值 (建议 5-10): ").strip()
        if w_input.isdigit() and int(w_input) > 0:
            MAX_CHUNK_WORKERS = int(w_input)
            self.console.print(f"🔧 并发数已调整为: [bold green]{MAX_CHUNK_WORKERS}[/]")
        
        # 1. 扫描与交互选择
        estimator = CostEstimator(self.input_dir, self.selected_model_config)
        estimator.scan()
        tasks = estimator.interactive_select()
        
        if not tasks:
            return

        # 范围模式交互（自动/单章/书籍）
        self.console.print(Panel("📚 请选择处理范围", style="bold blue"))
        self.console.print("[1] 自动检测 (默认)\n[2] 单章模式 (chapter)\n[3] 书籍模式 (book)")
        scope_choice = input("👉 请输入 1/2/3 (默认 1): ").strip()
        if scope_choice == '2':
            self.scope_mode = 'chapter'
        elif scope_choice == '3':
            self.scope_mode = 'book'
        else:
            self.scope_mode = self._detect_scope_mode(tasks)
        self.console.print(f"[dim]Scope Mode: {self.scope_mode}[/]")

        # 2. 成本预估
        estimator.estimate(tasks)

        # 3. 地图来源交互（优先确定是否外部导入）
        self.console.print(Panel("🗺️ 请选择文档结构分析（架构师）的方式", style="bold blue"))
        self.console.print("[1] 内部自动生成 (推荐)\n[2] 外部导入 (高级)")
        map_choice = input("👉 请输入 1 或 2 (默认 1): ").strip()
        self.map_source = 'internal' if (map_choice == '' or map_choice == '1') else 'external'

        # 4. 架构师模型交互（仅在内部模式下询问，并允许自定义 ID）
        if self.map_source == 'internal':
            self.console.print(Panel("🤖 请选择架构师模型", style="bold blue"))
            self.console.print("[1] qwen-plus (默认)\n[2] qwen3-max\n[3] 手动输入模型 ID")
            arch_choice = input("👉 请输入 1/2/3 (默认 1): ").strip()
            if arch_choice == '2':
                self.architect_model = 'qwen3-max'
            elif arch_choice == '3':
                custom_id = input("请输入模型 ID (例如 qwen-plus-xxx): ").strip()
                if custom_id:
                    self.architect_model = custom_id
                else:
                    self.architect_model = 'qwen-plus'
            else:
                self.architect_model = 'qwen-plus'

        # 外部导入模式：若缺少 JSON，则为每个选中章节生成 toc_source.txt 并退出
        if self.map_source == 'external':
            need_exit = False
            for chap_name, info in tasks.items():
                structure_map = self._load_structure_map(chap_name, Path(self.input_dir), Path(self.output_dir))
                if not structure_map:
                    self.console.print(f"[yellow]⚠️ 未发现 {chap_name} 的 structure_map.json，将生成 toc_source.txt 与标准 Prompt。[/]")
                    self.generate_toc_source_file(chap_name, info['files'], Path(self.output_dir))
                    need_exit = True
                else:
                    # 外部 JSON 校验
                    try:
                        self._validate_structure_map(structure_map)
                    except Exception as e:
                        self.console.print(f"[red]❌ {chap_name} 的 structure_map.json 非法: {e}")
                        need_exit = True
            if need_exit:
                self.console.print("\n[bold yellow]请完成外部模型生成 JSON 并保存后重新运行本程序。[/]")
                return

        confirm = input("\n👉 是否继续生成 LaTeX? (Y/n): ").strip().lower()
        if confirm != 'y' and confirm != '':
            self.console.print("已取消。")
            return

        latex_out_dir = Path(self.output_dir)
        latex_out_dir.mkdir(parents=True, exist_ok=True)
        
        # 若内部生成模式，先为各章节生成结构地图（LLM 架构师）
        if self.map_source == 'internal':
            map_gen = MapGenerator(model_name=self.architect_model)
            for chap_name, info in tasks.items():
                lines, last_slide = self._collect_toc_source(info['files'])
                toc_text = "\n".join(lines)
                structure_map = map_gen.generate_structure(toc_text, last_slide, mode=self.scope_mode, title=chap_name)
                inter_dir = latex_out_dir / 'intermediates' / chap_name
                inter_dir.mkdir(parents=True, exist_ok=True)
                (inter_dir / 'structure_map.json').write_text(json.dumps(structure_map, ensure_ascii=False, indent=2), encoding='utf-8')

        # 3. 准备生成
        self.console.print("\n[bold green]🚀 任务开始 (Nested Parallel Mode)...[/]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(), # 新增预估剩余时间
            TextColumn("[cyan]{task.fields[info]}"),
            console=self.console
        ) as progress:
            
            main_task_id = progress.add_task(
                f"[bold green]Total Progress ({len(tasks)} Chapters)", 
                total=len(tasks), 
                info="Starting..."
            )

            # 全局并发 (Max Chapter Workers)
            with ThreadPoolExecutor(max_workers=MAX_CHAPTER_WORKERS) as executor:
                futures = {}
                for chap_name, task_info in tasks.items():
                    f = executor.submit(
                        self.process_chapter,
                        chap_name,
                        task_info,
                        latex_out_dir,
                        progress,
                        main_task_id
                    )
                    futures[f] = chap_name
                
                for future in as_completed(futures):
                    chap = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        progress.console.print(f"[red]❌ Chapter {chap} Failed: {e}[/]")
                        self.logger.error(f"Chapter {chap} failed: {e}", exc_info=True)
                    finally:
                        progress.advance(main_task_id)

            progress.update(main_task_id, info="[bold green]All Done![/]")

        self.console.print(Panel(f"[bold green]✨ 所有文档处理完毕！[/]\n输出目录: {self.output_dir}", expand=False))

    def process_chapter(self, chap_name, task_info, latex_out_dir, progress, main_task_id):
        """单个章节的处理逻辑 (Smart Chunk Parallelism + Resume Capability)"""
        try:
            output_tex_path = latex_out_dir / f"{chap_name}.tex"
            
            # === 新增: 中间文件存储路径 (支持断点续传) ===
            intermediate_dir = latex_out_dir / "intermediates" / chap_name
            intermediate_dir.mkdir(parents=True, exist_ok=True)
            
            ctx_mgr = ContextManager(output_tex_path)
            
            # 1. 准备数据: 合并 -> 智能切分
            self.logger.info(f"[{chap_name}] Loading files...")
            full_md, slide_map = ctx_mgr.load_and_merge_files(task_info['files']) # 获取 slide_map
            # 加载结构地图并构建查表
            structure_map = self._load_structure_map(chap_name, Path(self.input_dir), latex_out_dir)
            if structure_map:
                self._validate_structure_map(structure_map)
            instruction_lookup = self._build_instruction_lookup(structure_map) if structure_map else {}
            chunk_tasks = ctx_mgr.create_smart_chunks(full_md, slide_map, instruction_lookup) # 查表优先
            total_chunks = len(chunk_tasks)
            
            self.logger.info(f"[{chap_name}] Split into {total_chunks} chunks. Checking local cache in {intermediate_dir}...")

            if total_chunks == 0: return

            # 2. 并发执行
            task_id = progress.add_task(f"  > {chap_name} ({total_chunks} parts)", total=total_chunks, info="Checking cache...")
            
            results = {} # index -> latex
            
            # 使用全局配置的 Worker 数 (全并发模式)
            with ThreadPoolExecutor(max_workers=MAX_CHUNK_WORKERS) as executor:
                futures = {}
                
                # A. 提交任务前先检查缓存
                for item in chunk_tasks:
                    idx = item['index']
                    cache_file = intermediate_dir / f"chunk_{idx:03d}.tex" # 使用 padding 方便排序查看
                    
                    if cache_file.exists() and cache_file.stat().st_size > 10: # 简单的非空检查
                        try:
                            # 命中缓存
                            content = cache_file.read_text(encoding='utf-8')
                            results[idx] = content
                            progress.advance(task_id)
                            self.logger.info(f"[{chap_name}] Chunk {idx} found in cache, skipping API call.")
                            continue
                        except Exception as e:
                            self.logger.warning(f"[{chap_name}] Read cache failed for chunk {idx}: {e}")
                    
                    # 未命中，提交任务
                    f = executor.submit(self.process_single_chunk, item)
                    futures[f] = idx
                
                if len(results) > 0:
                    progress.update(task_id, info=f"[yellow]Resumed {len(results)} chunks[/]")

                # B. 等待剩余任务
                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        res = future.result()
                        results[idx] = res
                        
                        # === 立即写入中间文件 ===
                        cache_file = intermediate_dir / f"chunk_{idx:03d}.tex"
                        cache_file.write_text(res, encoding='utf-8')
                        
                        # === 提取并保存 Metadata ===
                        meta_match = re.search(r'<!-- METADATA\s*({.*?})\s*-->', res, flags=re.DOTALL)
                        if meta_match:
                            try:
                                meta_json = meta_match.group(1)
                                meta_file = intermediate_dir / f"chunk_{idx:03d}.json"
                                meta_file.write_text(meta_json, encoding='utf-8')
                            except: pass
                        
                        progress.advance(task_id)
                        progress.update(task_id, info=f"[green]Done {idx+1}/{total_chunks}[/]")
                        self.logger.info(f"[{chap_name}] Chunk {idx+1}/{total_chunks} completed & saved.")
                    except Exception as e:
                        self.logger.error(f"[{chap_name}] Chunk {idx} failed: {e}")
                        progress.console.print(f"[red]Chunk {idx} Failed: {e}[/]")
                        
            # 3. 顺序组装写入
            if len(results) == total_chunks:
                with open(output_tex_path, 'w', encoding='utf-8') as f:
                    f.write(f"% Chapter: {chap_name}\n% Generated by MD2LaTeX Pro\n\n")
                    # 按索引顺序写入
                    for i in range(total_chunks):
                        if i in results:
                            content = results[i]
                            
                            # === 清理: 移除 Metadata 块 (最终输出不需要) ===
                            content = re.sub(r'<!-- METADATA[\s\S]*?-->', '', content)
                            # === 清理: 移除所有 Markdown 代码围栏与架构师提示语 ===
                            content = re.sub(r'^\s*```(latex)?\s*\n', '', content, flags=re.IGNORECASE | re.MULTILINE)
                            content = re.sub(r'\n\s*```\s*\n?', '\n', content)
                            content = re.sub(r'^.*架构师指令.*\n?', '', content, flags=re.MULTILINE)
                            # 若仍有残留三反引号，整体剔除
                            content = content.replace('```', '')
                            
                            f.write(f"% --- Part {i+1}/{total_chunks} ---\n")
                            f.write(content.strip())
                            f.write("\n\n")
                self.logger.info(f"[{chap_name}] Final output written to {output_tex_path}")
            else:
                 progress.console.print(f"[red]⚠️ {chap_name} 只有 {len(results)}/{total_chunks} 完成，跳过最终合并。中间文件已保存至 intermediates 目录。[/]")
                 self.logger.warning(f"[{chap_name}] Incomplete generation: {len(results)}/{total_chunks} chunks done.")
            
            progress.update(task_id, visible=False)

        except Exception as e:
            self.logger.error(f"Process Chapter Error: {e}", exc_info=True)
            raise e

    def process_single_chunk(self, item):
        """原子任务：将单个 Chunk 转 LaTeX，带重试"""
        total = item.get('total', '?')
        index = item.get('index', 0) + 1
        map_directive = item.get('map_directive', '') or ""
        
        # [RateLimit] 申请发射令牌 (阻断过快的请求)
        self.rate_limiter.wait_for_slot()
        
        # [Debug] 记录线程启动时间，证明并发正在发生
        self.logger.info(f"[Thread-Start] Chunk {index}/{total} 正在开始处理...")

        gen = LatexGenerator(model_name=self.model_name)
        
        prompt = self._build_prompt(
            item['current'], 
            item['prev'], 
            item['next'], 
            index, 
            total,
            item.get('structure_hint', ''), # 传入 structure_hint
            item.get('chapter_toc', ''),
            item.get('map_directive', '')
        )
        
        max_retries = 5
        last_error = None
        
        for attempt in range(max_retries):
            try:
                full_response = ""
                # 注意：generate_stream 是 generator
                for text_delta in gen.generate_stream(prompt):
                    full_response += text_delta
                
                if not full_response:
                    raise Exception("Empty response from API")
                    
                return full_response
            except Exception as e:
                last_error = e
                err_str = str(e)
                
                # 计算等待时间 (指数退避 + 抖动)
                base_wait = (attempt + 1) * 2
                
                # 针对限流错误大幅增加等待时间
                if "AllocationQuota" in err_str:
                    # TPM/Quota 超限通常需要等待较久才能恢复 (例如一分钟窗口重置)
                    base_wait = 20 + (attempt * 10) # 20s, 30s, 40s...
                elif "Throttling" in err_str:
                    base_wait = (attempt + 1) * 5 + 5 # 10s, 15s...
                else:
                    base_wait = (attempt + 1) * 2 
                
                wait_time = base_wait + random.uniform(1, 5) # 增加 1-5s 随机抖动避免惊群效应
                
                self.logger.warning(f"Chunk {index} failed (Attempt {attempt+1}/{max_retries}): {e}. Retry in {wait_time:.1f}s...")
                time.sleep(wait_time)
        
        raise Exception(f"Failed after {max_retries} retries: {last_error}")

    def _build_prompt(self, chunk, prev_md, next_md, index=None, total=None, structure_hint="", chapter_toc="", map_directive = None):
        # 移除过多的 CTX 标记干扰
        chunk = re.sub(r'<CTX>.*?</CTX>', '', chunk, flags=re.DOTALL)
        if prev_md: prev_md = re.sub(r'<CTX>.*?</CTX>', '', prev_md, flags=re.DOTALL)
        if next_md: next_md = re.sub(r'<CTX>.*?</CTX>', '', next_md, flags=re.DOTALL)

        # 动态替换 System Prompt 中的变量
        idx_str = str(index) if index else "某"
        ttl_str = str(total) if total else "若干"
        
        prompt = SYSTEM_PROMPT_TEMPLATE.replace("{index}", idx_str).replace("{total}", ttl_str)
        
        # 插入全局目录 (新增)
        if chapter_toc:
            prompt += f"\n{chapter_toc}\n"

        # 插入结构信息
        if structure_hint:
             prompt += f"\n\n{structure_hint}\n"

        if map_directive:
            prompt += "\n【架构师地图指令（必须遵守）】\n"
            directives = map_directive if isinstance(map_directive, list) else [map_directive]
            for d in directives:
                if isinstance(d, str):
                    # 兼容旧格式
                    if d.startswith('START_SECTION_AND_SUBSECTION'):
                        parts = d.split('::')
                        if len(parts) >= 4:
                            prompt += (
                                f"- 当前是新章节《{parts[1]}》及其子章节《{parts[2]}》的起始页（{parts[3]}）。"
                                f"请在本段开头依次输出 \\section{{{parts[1]}}} 与 \\subsection{{{parts[2]}}}，后续本段内不要重复生成章节/子章节标题。\n"
                            )
                    elif d.startswith('START_SECTION'):
                        parts = d.split('::')
                        if len(parts) >= 3:
                            prompt += f"- 当前是新章节《{parts[1]}》的起始页（{parts[2]}）。请在本段开头输出一次 \\section{{{parts[1]}}}，后续本段内不要重复生成章节标题。\n"
                    elif d.startswith('START_SUBSECTION'):
                        parts = d.split('::')
                        if len(parts) >= 3:
                            prompt += f"- 当前是子章节《{parts[1]}》的起始页（{parts[2]}）。请在本段开头输出一次 \\subsection{{{parts[1]}}}，后续本段内不要重复生成子章节标题。\n"
                    elif d.startswith('NO_HEADER'):
                        parts = d.split('::')
                        if len(parts) >= 3:
                            prompt += f"- 当前处于章节《{parts[1]}》内部（{parts[2]}）。请勿生成章节或子章节标题，只输出正文。\n"
                elif isinstance(d, dict):
                    d_type = d.get('type','')
                    if d_type == 'START_SECTION':
                        prompt += f"- 请在本段开头输出一次 \\section{{{d.get('title','')}}}（对应 Slide {d.get('slide','?')}）。\n"
                    elif d_type == 'START_SUBSECTION':
                        prompt += f"- 请在本段开头输出一次 \\subsection{{{d.get('title','')}}}（对应 Slide {d.get('slide','?')}），父章节《{d.get('parent','')}》。\n"
                    elif d_type == 'NO_HEADER':
                        prompt += f"- 当前处于章节《{d.get('parent','')}》内部（Slide {d.get('slide','?')}）。请勿生成章节或子章节标题，只输出正文。\n"

        if prev_md:
            prompt += f"\n\n【上文 Markdown (仅供衔接参考)】\n{prev_md}...\n"
        else:
            prompt += "\n\n【这是章节的开头】\n"
            
        prompt += f"\n【当前 Markdown 片段 (需要翻译)】\n```markdown\n{chunk}\n```\n"

        # 增加 Metadata 输出请求
        prompt += """
\n
【额外输出要求】
在 LaTeX 代码结束后，请务必附带一个 Metadata 块，记录你在本片段中定义或使用的重要符号、公式标签和图标标签。
格式如下：
<!-- METADATA
{
  "labels": ["eq:newton-2nd", "fig:setup"],
  "terms": ["$F$: force", "$m$: mass"]
}
-->
"""
        
        if next_md:
            prompt += f"\n【待预读 Markdown (仅供逻辑参考)】\n{next_md}...\n"
            
        return prompt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MD2LaTeX Pro")
    parser.add_argument("-i", "--input", default=DEFAULT_INPUT, help="Markdown Input Folder")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT, help="LaTeX Output Folder")
    parser.add_argument("-m", "--model", default=None, help="Model Key or ID (e.g. 1, qwen-max)")
    
    args = parser.parse_args()
    
    controller = WorkflowController(args.input, args.output, args.model)
    controller.run()
