# MD2LaTeX Pro 📚

> **学术级 Markdown 转 LaTeX 排版引擎**
> 专为处理由 `ppt2md` 生成的长篇课堂笔记 Markdown 设计，能够智能重构文档结构、修正 OCR 错误并输出符合严格学术规范的 LaTeX 源码。

## 🌟 核心特性

*   **⚡ 智能分块并行 (Smart Chunk Parallelism)**：
    *   **Context-Aware**: 自动将长 Markdown 拆分为适合 LLM 处理的 Chunks（~4000 字符），同时保留 **前文** 和 **后文** 上下文，确保逻辑连贯。
    *   **Nested Concurrency**: 采用 **Nested Parallel** 模式，单章节内部支持 **60+ 并发**，极速完成转录。

*   **🏗️ 文档结构自动重建 (Structure Reconstruction)**：
    *   **Structure Mapping**: 自动分析 Markdown 中的 Slide 边界和摘要信息。
    *   **Intelligent Heading**: 能够识别“内容接续”还是“新话题开始”，自动插入丢失的 `\section`、`\subsection` 标记，拒绝扁平化文档。

*   **💾 断点续传与缓存 (Resume & Cache)**：
    *   **Intermediate Storage**: 所有中间分块结果即时保存到 `latex_output/intermediates/`。
    *   **Metadata Tracking**: 自动提取并保存每个分块中定义的 **公式 Label**、**符号定义** 到 JSON 文件，方便后续索引。
    *   程序中断后，再次运行将自动加载缓存，仅处理未完成的 Chunks。

*   **🔍 交互式过滤 (Interactive Filter)**：
    *   支持按 **章节** 选择，也支持 **精确到页码** (例如: `Slide 1-10, 50-60`) 的细粒度过滤。
    *   内置 **成本预估 (Cost Estimator)**，在运行前自动计算字符数与预估 Token 费用。

## 🛠️ 使用指南

### 1. 启动

```bash
# 默认读取 ./markdown_output 输出到 ./latex_output
python md2latex.py

# 自定义路径
python md2latex.py -i ./my_markdown -o ./my_tex
```

### 2. 交互流程

1.  **扫描目录**: 程序会自动列出 `markdown_output` 下所有可用的章节。
2.  **选择任务**:
    *   `a`: 全选
    *   `1,3-5`: 选择特定章节
3.  **高级过滤 (可选)**:
    *   输入 `y` 进入页码筛选模式。
    *   针对选中的章节，输入范围 (如 `10-20`) 仅重做该部分，或回车处理整章。
4.  **成本确认**: 确认预估价格后开始执行。

## 📂 输出结构

```text
latex_output/
├── 广相笔记第五章.tex         # 最终合并的完整 LaTeX 文件 (Clean, No Markdown fences)
└── intermediates/            # 中间缓存目录 (不要轻易删除)
    └── 广相笔记第五章/
        ├── chunk_000.tex     # 第 1 部分 LaTeX 源码
        ├── chunk_000.json    # 第 1 部分 Metadata (Labels/Terms)
        ├── chunk_001.tex
        └── ...
```

## 🧠 技术细节

*   **上下文窗口**: 每个 Prompt 包含 `Pre-Chunk` (800 chars) + `Current-Chunk` (4000 chars) + `Next-Chunk` (800 chars)。
*   **结构感知**: 利用 `Slide_XX.md` 中的 `<CTX>` 元数据，构建全局目录树，防止在 PPT 分页处重复生成 Section 标题。
*   **Prompt Engineering**: 包含严格的 LaTeX 约束（禁 `$$`，强制 `equation`，强制 `\label`），并内置了 `TikZ` 绘图提示保留逻辑。

---
**依赖**: 需要 `rich` 和 `dashscope` 库。
**模型**: 默认使用 `qwen3-max-preview` (Logic Strong) 以确保 LaTeX 语法准确性。

## 🤝 外部导入 (External Import)

*   **架构师-施工队模式**：支持由外部更强模型（Gemini 3 Pro, GPT5.2 等）生成结构地图 `structure_map.json`，本工具作为施工队严格按地图插入 `\section/\subsection`。
*   **自动辅助**：当选择“外部导入”但缺少 `structure_map.json` 时，系统会自动生成 `toc_source.txt`（汇总每页关键词与摘要），并在控制台打印标准 Prompt 模板，方便直接复制到外部模型。
*   **闭环步骤**：
        1. 运行本程序，选择章节并选择“外部导入”。
        2. 系统生成 `latex_output/intermediates/<章节>/toc_source.txt` 并打印标准 Prompt。
        3. 将该文件与提示词交给外部模型生成严格 JSON，保存为 `structure_map.json`。
        4. 重新运行本程序，开始施工生成 LaTeX。

### 标准 Prompt 模板（节选）

```
# Role
你是一位专业的学术教材主编。

# Context
我将上传一份课堂笔记的“页面摘要清单”（toc_source.txt），其中包含了每一页 PPT (Slide) 的编号、关键词和内容摘要。

# Task
请分析这份摘要流的逻辑连贯性，将其重构为一份结构严谨、层级清晰的 LaTeX 目录结构数据。

# Requirements
1. 聚合与归纳：识别连续话题为同一 `section`，适当使用 `subsection`。
2. 完整性：覆盖从 Slide 1 到最后一页，范围连续且不重叠。
3. 输出严格 JSON，无 Markdown 代码块标记。
```

### 结构 JSON Schema（示例）

```json
{
    "meta": { "mode": "chapter", "title": "章节标题" },
    "structure": [
        { "level": "section", "title": "第一节", "start_slide": 1, "end_slide": 10,
            "subsections": [
                { "level": "subsection", "title": "子节 A", "start_slide": 1, "end_slide": 5 },
                { "level": "subsection", "title": "子节 B", "start_slide": 6, "end_slide": 10 }
            ]
        },
        { "level": "section", "title": "第二节", "start_slide": 11, "end_slide": 20 }
    ]
}
```