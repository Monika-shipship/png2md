# 文档到 Markdown 的生成原理

本文说明 DocPage2MD 从文档生成 Markdown 的核心流程。新主路径是 MinerU 多格式解析：PDF、PPTX、Docx、Excel、图片等文件先经 MinerU 获取 layout/json/crop，再进入 docpage2md 的 IR、renderer、validator 和后续 Brain 精修。旧版 PNG/JPG 图片目录流程仍保留为 `vision_only` 兼容路径。

这里的重点不是让模型自由“看图写作文”，而是把识别、结构化、重组、校验和保守回退拆成可审计的流水线，尽量避免公式、图表、手写文字等内容被静默遗漏。

## 目标

输入可以是 PDF/Office/图片等原文件，也可以是旧版文档页图片目录。输出仍然是用户直接使用的 Markdown：

```text
markdown_output/任务名/
├── Slide_01.md
├── Slide_02.md
├── 任务名_FULL.md
├── run_report.json
├── assets/
│   └── crops/
├── ir/
├── mineru_raw/
└── temp_raw_vision/
    └── Raw_01.json   # vision_only 兼容路径
```

内部的 Raw JSON、Page IR、validator 和 report 不是最终阅读产物，而是为了保证最终 Markdown 更可靠、更可追溯。

## 总览

```text
PDF / Office / 图片 / MinerU artifact / PNG 页面目录
  -> 模式选择：mineru_only / vision_only / hybrid
  -> MinerU precise API 或本地 artifact 读取 layout/json/crop
  -> DocumentIR / PageIR / BlockIR
  -> crop 图片复制到 assets/crops
  -> 确定性 Markdown renderer
  -> Validator / run_report 审计
  -> Slide_XX.md + FULL.md + assets + run_report.json

vision_only 兼容路径：
PNG/JPG 页面图片
  -> Stage 1 Vision 识别
  -> Raw text
  -> PageIR / BlockIR
  -> 缓存、证据、provenance、质量摘要
  -> Stage 2 Brain 重组
  -> Markdown refiner
  -> Validator 内容覆盖检查
  -> 正常写入 Markdown，或 fail-open 回退到 PageIR 渲染
  -> Slide_XX.md + FULL.md + run_report.json
```

## MinerU 解析：多格式入口

MinerU 负责处理 PDF、PPTX、Docx、Excel、图片等原文件，输出 `full.md`、`layout.json`、`content_list.json/content_list_v2.json`、`model.json` 和 `images/` 裁剪图。docpage2md 不把 MinerU Markdown 当作唯一真相，而是优先读取结构化 JSON 和 crop：

- text/title -> heading/paragraph block
- equation -> formula block
- image/chart -> figure block，并保留 crop
- table -> table block，并保留 crop 或 raw text

这样做的核心原因是：MinerU 的图表定位和裁剪强，docpage2md/Brain 更擅长对文字、公式和上下文做纠错。

## Stage 1：视觉识别（vision_only / hybrid 后续精读）

Stage 1 调用视觉模型读取每张图片，输出尽量完整的 Raw Data。它负责识别：

- 普通手写/印刷文字
- 行内公式和行间公式
- 表格
- 坐标图、流程图、几何图、手绘示意图等 Figure
- 看不清或不确定的区域

Stage 1 的结果会写入：

```text
markdown_output/任务名/temp_raw_vision/Raw_XX.json
```

Raw cache 里不仅有原始文本，还包含图片 hash、模型身份、prompt 版本、pipeline 版本、PageIR、block 列表、page image evidence、provenance 和质量摘要。缓存命中前会校验这些指纹，避免旧 prompt 或旧 pipeline 生成的结果混入新流程。

## PageIR / BlockIR：结构化中间层

Raw text 会被确定性解析成弱结构化的 PageIR。每个页面包含多个 BlockIR，常见类型包括：

- `heading`
- `paragraph`
- `list`
- `formula_inline`
- `formula_block`
- `table`
- `figure_note`
- `image_ref`
- `uncertain`

每个 block 都有稳定 ID，例如：

```text
p0003-b002
```

稳定 ID 的作用是让校验、refiner、provenance 和 report 都能指向同一个内容块。这样后续如果发生删除、合并、降级或 fallback，报告可以说明“哪个 block 受影响”，而不是只给出一段模糊文字。

## Stage 2：Brain 重组

Stage 2 使用当前页和前后各 2 页的 Raw Data 组成 5 页上下文窗口，让文本整理模型把当前页重组为 Markdown。它主要负责：

- 合并断行
- 调整段落顺序
- 清理模型寒暄和多余说明
- 利用邻页上下文判断标题、编号、公式连续性
- 生成更易读的 Markdown

Stage 2 的目标不是自由改写整页内容。它输出的 Markdown 还必须通过后续 refiner 和 validator。

## Markdown Refiner

Stage 2 输出后会经过轻量 refiner。refiner 只做有限、可解释的修复，例如：

- 补齐 `# Slide N` 标题
- 去掉包裹全文的代码围栏
- 清理模型寒暄
- 规范公式环境
- 把 `align/align*` 转成更适合 Markdown 渲染的 `aligned`
- 把 `\tag{n}` 移到 `aligned` 环境外

这些修复是有限操作，不允许 refiner 随意重写整页 Markdown。

## Validator：防遗漏与质量闸门

Validator 会检查最终 Markdown 是否可信。它包含两类检查。

第一类是格式和错误检查：

- 是否以 `# Slide N` 开头
- 是否泄漏内部上下文标记
- 是否把 API 错误文本写成正常 Markdown
- 代码围栏和公式分隔符是否平衡
- 公式括号、`\left...\right`、`\frac` 是否明显异常
- 表格结构是否可靠

第二类是内容覆盖检查，这是防遗漏的核心：

- Stage 1 识别到的重要文字块是否出现在最终 Markdown 中
- 短公式和长公式是否都被保留
- 表格是否被保留，或不可靠时是否降级为 warning + raw text / image ref
- 图示说明是否渲染为图示说明或不确定图示 warning
- `uncertain` 内容是否被显式保留为不确定块
- 图片引用是否仍能在 Markdown 中追溯

如果 Stage 2 把 Stage 1 已识别出的重要内容漏掉，validator 会产生类似这些 warning：

```text
target_text_block_missing
target_formula_block_missing
target_table_block_missing
target_figure_block_missing
target_uncertain_block_missing
target_image_ref_block_missing
```

这些 warning 会触发 fail-open 回退。

## Fail-open：宁可保守，不静默漏内容

当 Stage 2 输出不可信时，系统不会把坏结果当成正常 Markdown 写入。只要 PageIR 可用，就会用确定性 renderer 从 Stage 1 blocks 生成保守 Markdown。

回退后的 Markdown 不会输出错误堆栈、覆盖率解释、模型思考过程或长篇诊断。详细原因写入 `run_report.json` 和 `.error.json`；用户可见 Markdown 只保留可读内容和必要图片证据。例如：

```markdown
# Slide 7

![page evidence](evidence/Slide_07.png)

原始 PageIR 中可安全渲染的正文、公式、图表或 crop 引用。
```

这种结果可能没有 Stage 2 整理得漂亮，但它优先保证 Stage 1 已识别到的内容不被静默删掉。

## Renderer：确定性 Markdown 输出

PageIR renderer 会把不同 block 渲染成稳定 Markdown：

- 文字 block 渲染为普通段落、标题或列表
- 可靠公式渲染为 Markdown LaTeX
- 不可靠公式保守保留原始识别；有 crop 时保留图片引用，详细 warning 写入 report
- 可靠表格渲染为 Markdown table
- 不可靠表格渲染为 fenced raw text，有图片证据时保留图片引用，详细 warning 写入 report
- 图示渲染为图片引用 + 默认折叠的 Typora 兼容 `<details>` 块；`<details>` 和 `<summary>` 分行，不加 `open` 属性
- 不确定内容保守保留正文或图片证据，详细原因写入 report

最终用户仍然打开 `Slide_XX.md` 和 `{任务名}_FULL.md`，不需要直接读 IR。

## Run Report

每个任务会生成：

```text
run_report.json
```

它记录：

- 每页 Stage 1 / Stage 2 状态
- 缓存命中情况
- 模型身份和 usage 信息
- validator errors / warnings
- block counts
- formula/table/figure warning 数
- suspects 和建议 op
- provenance summary
- 是否进入 fail-open

当用户发现某页缺公式、缺图表或内容异常时，`run_report.json` 是第一入口。

## 当前边界

当前系统能保证的是：Stage 1 已识别进 Raw/PageIR 的内容，不应在最终 Markdown 中被静默遗漏。若 Stage 1 视觉模型一开始没有从图片里识别出某个符号、图表或文字，后续 validator 无法凭空知道它存在。

因此真实疑难样本仍需要继续加强：

- 更强的视觉模型
- 页面/crop 证据
- 更细的图示结构表达
- 更可靠的表格检测
- 多模型或 OCR 交叉校验
- 针对手写公式的专门评测集

项目当前方向是 Markdown-first：最终产物保持 Markdown，但内部用 IR、validator、provenance 和 fail-open 来提高可靠性。
