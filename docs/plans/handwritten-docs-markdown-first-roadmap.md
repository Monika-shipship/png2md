# png2md 下一阶段改进计划：面向手写笔记的 Markdown-first 文档识别

## 1. 核心约束

最终用户产物仍然必须是 Markdown：

- 单页输出：`Slide_XX.md`
- 汇总输出：`{doc_name}_FULL.md`
- 图片、手绘图、表格截图等辅助资产可以作为相对链接被 Markdown 引用
- `Raw_XX.json`、`page_ir`、`run_report.json`、provenance、validator 结果只作为内部中间层和审计材料，不替代 Markdown

换句话说，后续所有 IR、renderer、refiner、表格结构、公式检查的目的，都是让最终 Markdown 更可信、更可读、更方便复制和二次利用。

## 2. 项目定位修正

当前项目不应只按“PPT 截图转 Markdown”优化，而应按“通用文档页图片转 Markdown”优化，重点输入包括：

- 手写课堂笔记
- 扫描讲义
- PDF/PPT 导出的页面图片
- 含大量数学/物理公式的页面
- 手绘示意图、流程图、坐标图、结构图
- 表格、半结构化列表、实验记录表
- 中英文混排、符号密集页面

这意味着后续质量目标不是“排版像 PPT”，而是：

- 尽量完整保留文字内容
- 尽量准确转写公式为 LaTeX
- 对手绘图给出可用的 Markdown 引用块说明
- 对表格给出可读 Markdown/HTML 表格，无法可靠转写时保留图片引用
- 所有不确定内容在 Markdown 中显式标注，而不是假装确定

## 3. 从 mineru-refine 迁移的关键原则

### 3.1 Markdown 是最终派生产物

mineru-refine 的 Markdown 来自结构化 item 渲染，而不是让 LLM 自由写最终文档。png2md 后续也应逐步迁移到：

```text
image -> Vision OCR/understanding -> Page IR -> renderer -> Markdown
                                      -> refiner/report
```

短期仍可保留 Brain 阶段，但 Brain 应逐步从“直接写整页 Markdown”降权为：

- 修正 block 类型
- 建议标题层级
- 判断疑点是否执行有限 op
- 整理 Figure 描述
- 对表格结构给出候选，但必须过结构闸门

### 3.2 内部结构不改变用户产物

内部可以使用：

- `PageIR`
- `BlockIR`
- `FormulaBlock`
- `FigureBlock`
- `TableBlock`
- provenance
- validation report

但默认用户主要打开和使用的仍是 `.md`。内部结构应帮助 renderer 稳定生成 Markdown。

### 3.3 分层保真

不能把 mineru 的 “no new char” 机械套到 png2md，因为 png2md 输入是图片，视觉描述本来会生成文本。应分层：

- OCR 文本：不应无来源新增正文；允许空白清理、少量白名单 OCR 纠错
- 公式：允许视觉转 LaTeX，但必须保留 raw/evidence，做 delimiter 和基本语法检查
- 手绘图：允许自然语言描述，但必须标记 `origin: vision_description`
- 表格：优先结构化；不确定时保留图像引用，不输出看似正确的假表格
- renderer 模板：页标题、admonition 标记等不参与 OCR 覆盖率

## 4. 下一阶段里程碑

## M1：Markdown-first Renderer 强化

目标：让最终 Markdown 格式稳定、可读，并覆盖手写笔记核心元素。

涉及模块：

- `ppt2md_app/ir.py`
- 新增或拆分 `ppt2md_app/renderer.py`
- `ppt2md_app/validators.py`
- `tests/test_ir.py`

任务：

1. 将当前 `ir.py` 中 renderer 独立成 `renderer.py`。
2. 明确支持 block 类型：
   - `heading`
   - `paragraph`
   - `list`
   - `formula_inline`
   - `formula_block`
   - `figure_note`
   - `table`
   - `image_ref`
   - `uncertain`
3. Markdown 输出规则：
   - 每页固定以 `# Slide N` 开头
   - 内容标题从 `##` 起
   - 行间公式统一 `$$...$$`
   - 手绘图统一输出：
     ```markdown
     > [!NOTE] 图示说明
     > ...
     ```
   - 不确定识别输出：
     ```markdown
     > [!WARNING] 识别不确定
     > ...
     ```
   - 表格可靠时输出 Markdown table；复杂表格可输出 HTML table；不可靠时输出截图链接和说明

验收：

- golden PageIR -> Markdown 测试
- 手写笔记 fixture 至少包含文字、公式、图示、表格四类 block
- `python -m pytest` 通过

## M2：面向手写笔记的 Page IR 解析增强

目标：Stage 1 Raw 不再只是自然语言，而能拆出手写文档常见结构。

涉及模块：

- `ppt2md_app/ir.py`
- `ppt2md_app/artifacts.py`
- `ppt2md_app/prompts.py`
- `tests/test_ir.py`

任务：

1. 从 Raw Text 程序化识别：
   - `### Figure Analysis`
   - `### Formula` 或公式密集段
   - Markdown/纯文本表格候选
   - 编号列表、证明步骤、例题/解题段
2. 为 block 增加字段：
   - `id`
   - `type`
   - `text`
   - `source_page`
   - `origin`
   - `confidence`
   - `evidence`
   - `bbox` 预留，可为空
3. 调整 Stage 1 prompt，要求 Vision 明确分区输出：
   - OCR Text
   - Formula Notes
   - Figure Analysis
   - Table Analysis
   - Uncertain / Illegible
4. 仍保留 `raw_text`，任何结构化解析失败都不能丢原文。

验收：

- Raw-only 仍可 fallback 到 Markdown
- Figure Analysis 能稳定转为 `figure_note`
- 公式密集段能标为 formula block
- 表格候选能标为 table block 或 uncertain table

## M3：公式质量闸门

目标：提升手写公式转 LaTeX 的可靠性。

涉及模块：

- `ppt2md_app/validators.py`
- `ppt2md_app/renderer.py`
- `ppt2md_app/reporting.py`
- `tests/test_validators.py`

任务：

1. 增强公式检测：
   - `$$` 成对
   - `$` 行内公式基础配对
   - 括号 `{}`、`()`, `[]` 基础平衡
   - 常见非法 LaTeX 片段 warning
2. 对公式 block 记录：
   - 原 Raw 片段
   - 渲染后 LaTeX
   - confidence
   - warning
3. Markdown 中对不确定公式显式标注：
   ```markdown
   > [!WARNING] 公式识别不确定
   > 原始识别：...
   ```

验收：

- 不平衡公式阻断正常成功或写入 warning
- 合法复杂公式不被误杀
- 公式 warning 进入 `run_report.json`

## M4：手绘图像与图示说明

目标：把手绘图从“普通文本描述”升级为独立 Figure block，并在 Markdown 中可读。

涉及模块：

- `ppt2md_app/ir.py`
- `ppt2md_app/renderer.py`
- `ppt2md_app/prompts.py`
- `ppt2md_app/reporting.py`

任务：

1. Stage 1 prompt 强化手绘图分析：
   - 图类型：坐标图、流程图、结构图、装置图、几何图、示意图
   - 节点/箭头/标签/坐标轴/曲线
   - 是否与正文公式相关
2. Figure block 字段：
   - `figure_type`
   - `description`
   - `labels`
   - `relations`
   - `origin: vision_description`
3. Markdown 渲染：
   - 用 note block 输出图示说明
   - 如果后续有 crop，则附图片链接
   - 如果图示不可识别，输出 warning，而不是编造

验收：

- 手绘图 fixture 能稳定输出 note block
- Figure 描述不混入 OCR 正文覆盖率
- 无 Figure 时不生成空 Figure block

## M5：表格结构与降级策略

目标：表格宁可保守，也不要输出错得像真的 Markdown 表格。

涉及模块：

- `ppt2md_app/ir.py`
- `ppt2md_app/renderer.py`
- `ppt2md_app/validators.py`
- 新增 `ppt2md_app/table_quality.py`

任务：

1. 识别 table block：
   - Markdown table
   - 文本对齐表格
   - 实验记录表
   - 手写数据表
2. 表格质量检查：
   - 行列数一致性
   - 空表/壳表
   - 单元格乱码比例
   - 表头缺失 warning
3. 渲染策略：
   - 简单表格 -> Markdown table
   - 复杂表格 -> HTML table
   - 不可靠表格 -> 保留 raw + warning；未来有 crop 时链接图片
4. 借鉴 mineru 的 garbled table 思路：
   - 视觉重转写必须 opt-in
   - 结构闸门失败则回退
   - 无 crop 时不能启用视觉表格重写

验收：

- 表格行列不一致 warning
- 视觉表格 mock 坏结构 reject
- 不可靠表格不会被渲染成正常成功表格

## M6：Block 级 Refiner

目标：把 refiner 从 Markdown 行级升级为 Block IR 级。

涉及模块：

- `ppt2md_app/refiner.py`
- `ppt2md_app/ir.py`
- `ppt2md_app/renderer.py`
- `tests/test_refiner.py`

任务：

1. op 改为引用 block id：
   - `merge_block(a, b)`
   - `drop_block(id, reason)`
   - `promote_heading(id)`
   - `demote_heading(id)`
   - `convert_figure_note(id)`
   - `mark_uncertain(id)`
   - `normalize_formula(id)`
2. `apply_op_checked()`：
   - 修改 PageIR
   - 运行 invariant
   - 重新 renderer
   - 运行 validator
   - 失败回滚
3. report 记录：
   - suspect
   - applied op
   - rejected op
   - before/after block ids

验收：

- op 不直接调用 LLM
- op 不直接改最终 Markdown
- 二次运行 refiner 应 no-op 或只产生相同结果

## M7：面向文档识别的 Provenance

目标：让每段 Markdown 可追溯来源。

涉及模块：

- `ppt2md_app/reporting.py`
- `ppt2md_app/artifacts.py`
- `ppt2md_app/ir.py`

任务：

1. block provenance：
   - `vision_ocr`
   - `vision_formula`
   - `vision_description`
   - `brain_refine`
   - `renderer_template`
   - `refiner_op`
2. report 中新增：
   - block count by type
   - uncertain block count
   - formula warning count
   - table warning count
   - figure count
3. Markdown 可选输出 provenance 注释：
   - 默认不污染正文
   - debug 模式可输出 HTML comment

验收：

- 每个 block 都有 origin
- generated description 不计入 OCR 覆盖率
- report 能说明每页识别质量

## 5. 不建议现在做的事

- 不建议把最终输出改成 JSON 或数据库格式；JSON 只做 sidecar。
- 不建议直接引入 Rust core；当前 Python 项目先把契约和测试做扎实。
- 不建议默认开启 OCR confusion 或视觉表格重写。
- 不建议让 LLM 直接润色整页手写笔记。
- 不建议为了美观自动补全看不清的公式或图示含义。

## 6. 下一轮建议先做的代码任务

优先实现 M1 + M2 的一小步：

1. 新增 `ppt2md_app/renderer.py`，把 Markdown renderer 从 `ir.py` 中拆出来。
2. 扩展 BlockIR 类型：`formula_block`、`figure_note`、`table`、`uncertain`。
3. 更新 Stage 1 prompt，明确手写笔记、公式、手绘图、表格的分区输出。
4. 加 fixtures：
   - 手写文字 + 公式
   - 手绘图 Figure Analysis
   - 简单表格
   - 不确定/看不清区域
5. 保持最终输出仍为 `Slide_XX.md` 和 `{doc_name}_FULL.md`。

