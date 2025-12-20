import os
import re
import time
import json
import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
from dashscope import MultiModalConversation
import dashscope

# ================= 配置区域 =================
# 建议配置环境变量，或者在此处填入
# dashscope.api_key = "sk-xxxxxxxxxxxx"

MODEL_NAME = "qwen3-vl-plus"
INPUT_FOLDER = "./ppt_images"      
OUTPUT_FOLDER = "./markdown_output" 
SESSION_FILE = "session_state.json" # 用于存储任务配置的中间文件

# 并发控制 (建议 3-5)
MAX_WORKERS = 3  
THINKING_BUDGET = 2048 

# === Prompt 模板 ===
USER_PROMPT_TEMPLATE = r"""
你是一个专业的 PPT 转 Markdown 助手。你将收到一张 PPT 页面截图（单页）。

【上一页传递的知识状态 Context】:
{context_block}

---
【当前任务】
请分析当前 PPT 图片，将其转换为 Markdown。

【硬性格式要求】
1. **公式**：行内用 $...$；行间用 $$...$$。禁止使用 \(...\) 或 \[...\]。
2. **表格**：使用 Markdown 表格。
3. **视觉描述**：必须包含二级标题 `## Figure & Layout Description`，详细描述图片的视觉元素（布局、颜色、形状、层级），描述应细致到可指导复刻。
4. **OCR**：精确识别文字、符号下标。
5. **真实性**：不确定的内容标记为“[无法辨认]”。

【输出结构（必须严格遵守）】
输出必须包含以下三部分，顺序不能乱：

1. **幻灯片头部**
   # Slide {slide_no}

2. **正文内容**
   (这里是识别出的 PPT 文本内容，保持原级结构)

3. **视觉描述**
   ## Figure & Layout Description
   (这里是视觉描述)

4. **上下文更新 (Hidden Block)**
   请根据“上一页的知识状态”和“当前页内容”，生成一个新的、扁平的 JSON 状态块。
   *注意*：不要把上一页的 JSON 直接嵌套进来！你需要消化信息，输出合并后的当前状态。
   
   格式必须如下（必须包含在 <CTX> 标签中）：
   <CTX>
   {{
      "topic": "当前页的核心主题",
      "keywords": ["关键词1", "关键词2"],
      "summary": "一句话概括本页对于整体课程的知识增量",
      "pending_concepts": ["尚未解释清楚的概念..."]
   }}
   </CTX>
"""

# ================= 辅助函数 =================

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s.name)]

def scan_ppt_folders(root_folder):
    """扫描子文件夹"""
    root = Path(root_folder)
    if not root.exists():
        os.makedirs(root, exist_ok=True)
        return {}
    tasks = {}
    exts = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
    for entry in root.iterdir():
        if entry.is_dir():
            images = [f for f in entry.iterdir() if f.suffix.lower() in exts]
            if images:
                images.sort(key=natural_sort_key)
                tasks[entry.name] = [str(img.absolute()) for img in images] # 存绝对路径方便序列化
    return tasks

def extract_context(text):
    pattern = r"<CTX>(.*?)</CTX>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).replace("```json", "").replace("```", "").strip()
    return "No context from previous page."

def read_context_from_file(file_path):
    """从已存在的 Markdown 文件中读取上下文"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            ctx = extract_context(content)
            if "No context" not in ctx:
                return ctx
    except:
        pass
    return "Resumed session. Context lost from previous file."

def safe_get_content(choice):
    text = ""
    msg = choice.get('message', {}) if isinstance(choice, dict) else getattr(choice, 'message', None)
    if not msg: return ""
    content = msg.get('content') if isinstance(msg, dict) else getattr(msg, 'content', None)
    if content:
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict): text += item.get('text', '')
                elif isinstance(item, str): text += item
        elif isinstance(content, str): text = content
    return text

def check_is_thinking(choice):
    msg = choice.get('message', {}) if isinstance(choice, dict) else getattr(choice, 'message', None)
    if not msg: return False
    return bool(msg.get('reasoning_content') if isinstance(msg, dict) else getattr(msg, 'reasoning_content', False))

def format_time(seconds):
    return str(datetime.timedelta(seconds=int(seconds)))

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
            with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def save_session(tasks_config):
    with open(SESSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(tasks_config, f, indent=2, ensure_ascii=False)

def parse_range_string(range_str, max_len):
    """解析 1-5, 10-end 等格式"""
    if not range_str or range_str.lower() == 'all':
        return 0, max_len
    
    try:
        if '-' in range_str:
            start, end = range_str.split('-')
            start = int(start) - 1 # 转为0-based索引
            if end.lower() == 'end':
                end = max_len
            else:
                end = int(end)
            return max(0, start), min(end, max_len)
        else:
            # 单页也是一种范围
            idx = int(range_str) - 1
            return max(0, idx), min(idx + 1, max_len)
    except:
        print("  ⚠️ 范围格式错误，默认全选")
        return 0, max_len

def interactive_setup():
    print("\n🔄 正在扫描 PPT 文件夹...")
    all_tasks = scan_ppt_folders(INPUT_FOLDER)
    
    if not all_tasks:
        print(f"❌ 未在 {INPUT_FOLDER} 中发现子文件夹。")
        return None

    ppt_names = list(all_tasks.keys())
    
    # 1. 检查断点
    old_session = load_session()
    if old_session:
        print("\n" + "="*40)
        print("📢 发现上次未完成的任务记录！")
        print(f"   包含任务: {', '.join(old_session.keys())}")
        choice = input("👉 是否继续上次的任务？(y/n) [默认为 y]: ").strip().lower()
        if choice != 'n':
            print("✅ 已加载上次进度。")
            return old_session

    # 2. 新任务选择
    print("\n" + "="*40)
    print("📂 发现以下 PPT:")
    for i, name in enumerate(ppt_names):
        count = len(all_tasks[name])
        print(f"  [{i+1}] {name} ({count} 页)")
    
    print("\n👉 请选择要处理的 PPT:")
    print("   输入序号(如 1,3) | 输入 'a' 全选")
    
    selection = input("   您的选择: ").strip()
    
    selected_names = []
    if selection.lower() == 'a':
        selected_names = ppt_names
    else:
        try:
            indices = [int(x.strip()) for x in selection.split(',') if x.strip()]
            for idx in indices:
                if 1 <= idx <= len(ppt_names):
                    selected_names.append(ppt_names[idx-1])
        except:
            print("❌ 输入无效，退出。")
            return None

    if not selected_names: return None

    # 3. 配置页码范围
    final_config = {}
    print("\n⚙️  配置页码范围 (直接回车 = 全选):")
    print("   格式示例: '1-10' (前10页) | '5-end' (第5页到最后) | 'all'")
    
    for name in selected_names:
        total = len(all_tasks[name])
        range_input = input(f"   📘 [{name}] (共{total}页) 处理范围: ").strip()
        start, end = parse_range_string(range_input, total)
        
        # 存储配置
        final_config[name] = {
            "images": all_tasks[name], # 全部图片路径
            "range_start": start,      # 处理起始索引
            "range_end": end           # 处理结束索引
        }
    
    # 保存新会话
    save_session(final_config)
    return final_config

# ================= 核心工作线程 =================

def process_single_ppt_task(ppt_name, config):
    """
    处理单个 PPT，支持断点续传
    """
    images_paths = config["images"]
    start_idx = config["range_start"]
    end_idx = config["range_end"]
    
    # 只处理指定范围的图片
    target_images = images_paths[start_idx:end_idx]
    total_slides = len(target_images)
    
    ppt_output_dir = Path(OUTPUT_FOLDER) / ppt_name
    os.makedirs(ppt_output_dir, exist_ok=True)
    
    prefix = f"[{ppt_name}]"
    
    # --- 断点续传：上下文初始化 ---
    # 如果我们要从第 5 页开始处理，尝试去读取第 4 页生成的 md 文件来获取 Context
    current_context = "Starting processing. No prior context."
    
    # 计算实际的 PPT 页码（从1开始）
    first_target_slide_no = start_idx + 1 
    
    if first_target_slide_no > 1:
        prev_slide_no = first_target_slide_no - 1
        prev_md_path = ppt_output_dir / f"Slide_{prev_slide_no:02d}.md"
        if prev_md_path.exists():
            print(f"{prefix} 正在读取上一页 (P{prev_slide_no}) 的上下文以恢复连贯性...")
            current_context = read_context_from_file(prev_md_path)
    
    print(f"{prefix} 任务启动! 范围: P{first_target_slide_no}-P{end_idx} (共{total_slides}页)")
    task_start_time = time.time()

    for i, img_path_str in enumerate(target_images):
        actual_slide_no = start_idx + i + 1
        save_name = f"Slide_{actual_slide_no:02d}.md"
        output_path = ppt_output_dir / save_name
        
        # --- 断点检测：跳过已完成 ---
        if output_path.exists() and output_path.stat().st_size > 100:
            print(f"{prefix} P{actual_slide_no} 已存在，跳过 (断点续传)")
            # 即使跳过，也要更新一下 Context，供下一页使用
            current_context = read_context_from_file(output_path)
            continue

        # --- 计时逻辑 ---
        elapsed_total = time.time() - task_start_time
        processed_count = i
        time_info = ""
        if processed_count > 0:
            avg = elapsed_total / processed_count
            rem = avg * (total_slides - i)
            time_info = f"| 剩: {format_time(rem)}"

        print(f"\n{prefix} 处理 P{actual_slide_no}: {Path(img_path_str).name} {time_info}")

        filled_prompt = USER_PROMPT_TEMPLATE.format(
            slide_no=actual_slide_no,
            context_block=current_context
        )
        
        messages = [{
            "role": "user",
            "content": [
                {"image": f"file://{img_path_str}"},
                {"text": filled_prompt}
            ]
        }]

        full_text = ""
        is_thinking_printed = False
        
        for attempt in range(3):
            try:
                responses = MultiModalConversation.call(
                    model=MODEL_NAME,
                    messages=messages,
                    stream=True,
                    incremental_output=True,
                    enable_thinking=True,        
                    thinking_budget=THINKING_BUDGET 
                )
                
                print(f"{prefix} P{actual_slide_no} >> 生成: ", end="", flush=True)
                
                for chunk in responses:
                    if chunk.status_code != 200: continue
                    if not chunk.output or not chunk.output.choices: continue
                    choice = chunk.output.choices[0]
                    
                    if check_is_thinking(choice):
                        if not is_thinking_printed:
                            print("(思考中...)", end="", flush=True)
                            is_thinking_printed = True
                        continue 
                    
                    text_chunk = safe_get_content(choice)
                    if text_chunk:
                        print(".", end="", flush=True) 
                        full_text += text_chunk
                
                print(" OK")
                break 
            except Exception as e:
                print(f"\n{prefix} !! 异常 (重试 {attempt+1}): {e}")
                time.sleep(2)

        if full_text:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            
            ctx = extract_context(full_text)
            if "No context" not in ctx:
                current_context = ctx
        else:
            print(f"{prefix} !!警告: P{actual_slide_no} 生成为空")

    merge_markdowns(ppt_output_dir, ppt_name)
    total_time = time.time() - task_start_time
    return f"{ppt_name} 完成 (耗时 {format_time(total_time)})"

# ================= 主入口 =================
def main():
    # 1. 交互式获取任务配置
    tasks_config = interactive_setup()
    if not tasks_config:
        print("程序退出。")
        return

    print("\n🚀 开始执行任务队列...")
    print("=========================================")
    
    # 2. 并发执行
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for ppt_name, config in tasks_config.items():
            futures.append(executor.submit(process_single_ppt_task, ppt_name, config))
        
        for future in futures:
            try:
                res = future.result()
                print(f"系统消息: {res}")
            except Exception as e:
                print(f"系统消息: 任务失败 - {e}")
    
    # 3. 任务全部完成后，可以选择删除 session 文件，或者保留以便下次追加
    print("\n✨ 所有任务已结束。")

if __name__ == "__main__":
    main()