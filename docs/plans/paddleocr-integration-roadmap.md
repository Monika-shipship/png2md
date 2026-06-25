# PaddleOCR Integration Roadmap

Last updated: 2026-06-25

## 背景

PaddleOCR 已作为 DocPage2MD 的正式可选解析引擎接入。它和 MinerU 一样可以承担文档 OCR、版面切分、公式/表格/图像解析等前置结构化工作，并且可能在部分扫描、屏拍、弯曲、复杂光照、异形框场景下表现更好。

当前目标不是立刻替换 MinerU，而是把工作流抽象成“解析引擎 + Markdown 精修”的组合，让用户可以按文件类型、质量、成本和速度选择。

## 当前实现状态

已完成：

- CLI 支持 `paddleocr_only`、`paddleocr_hybrid`、`--layout-engine`、`--refine-mode`。
- 默认异步 endpoint：`https://paddleocr.aistudio-app.com/api/v2/ocr/jobs`。
- 默认模型：`PaddleOCR-VL-1.6`；可通过 `--paddleocr-model` 切换。
- PaddleOCR token 默认读取 `PADDLEOCR_API_TOKEN`。
- 支持本地文件、多个本地文件、文件夹、URL 和已有 PaddleOCR artifact。
- 本地 PDF 默认按 100 页分段提交，chunk 输出会合并回同一最终文档。
- 原始结果保存到 `paddleocr_raw/`，包括 job 状态、JSONL、Markdown、图片资源和下载审计。
- Adapter 已解析 `layoutParsingResults`、`prunedResult`、`ocrResults`、`markdown.images`、`outputImages`、`inputImage`。
- PaddleOCR DocumentIR 复用现有 renderer、validator、formula/table/figure 检查和 hybrid enrichment。
- GUI 工作流已改为“解析引擎 + Markdown 精修”，PaddleOCR 作为可选解析引擎。
- GUI Provider/Key 页已包含 PaddleOCR，进度条可读取 `extractProgress.totalPages/extractedPages`。
- PaddleOCR API client 对提交、轮询和结果下载的 `429/503/504` 与网络错误按配置重试。
- 远程 URL 输入在可读取 `Content-Length` 时会阻止超过 200MB 的文件；未知大小会记录日志并继续提交。
- 离线测试覆盖 adapter、坏 JSONL、空页、client fake HTTP、pending/running/done、429/503/504 重试、结果下载重试、pipeline 渲染和 chunk merge。
- 已通过 Tkinter GUI 代码路径用 `tests/群论笔记4.1.pdf` 全量跑通 `paddleocr_only` 和 `paddleocr_hybrid`，输出分别在 `markdown_output/gui_paddleocr_real_verify_only/gui_paddleocr_4_1_only` 与 `markdown_output/gui_paddleocr_real_verify_hybrid/gui_paddleocr_4_1_hybrid`。
- 同一 PDF 的基础耗时对比已记录：`mineru_only` 约 `16.4s`，`mineru_hybrid` 约 `113.9s`，`paddleocr_only` 约 `19.1s`，`paddleocr_hybrid` 约 `106.0s`。
- `dual_hybrid` 双引擎融合已升级为候选组融合：同页 MinerU/PaddleOCR block 先按 bbox、文本相似度、垂直位置、类型和图注/图片邻近关系粗分组，再通过白名单操作生成 `fused_document_ir.json`，最后进入 DocPage2MD 精修。
- 双引擎输出会保留 `ir/mineru_document_ir.json`、`ir/paddleocr_document_ir.json`、`ir/fused_document_ir.json` 和兼容 `ir/document_ir.json`；`run_report.json["fusion"]` 记录候选组、融合决策、被拒绝操作和不确定项。
- 已用真实 `tests/群论笔记4.1.pdf` 页 1 验证 PaddleOCR API 和 `dual_hybrid`，输出分别在 `markdown_output/paddleocr_api_probe_20260625/paddleocr_api_probe_page1`、`markdown_output/dual_real_probe_20260625/dual_real_probe_page1` 和修复后复跑的 `markdown_output/dual_real_artifact_rerun_20260625/dual_real_artifact_rerun_page1`。

仍需真实验收/优化：

- 与同一文件的 `mineru_only` / `mineru_hybrid` 继续做公式质量、表格质量和图片切分质量对比。
- 根据更多真实失败码继续补充更细的错误提示。
- 根据真实返回字段继续完善 PaddleOCR artifact 解析。
- 实现长 PDF 的 `dual_hybrid` chunked merge。目前双引擎模式会阻止超过 PaddleOCR chunk size 的 PDF，避免错误地只处理前一段。

## 已阅读的本地文档

重点文档：

- `docs/PaddleOCR/PaddleOCR-VL-1.5_API.md`
- `docs/PaddleOCR/PaddleOCR-VL-1.6调用代码参考.txt`
- `docs/PaddleOCR/异步API使用文档.md`

补充文档：

- `docs/PaddleOCR/PaddleOCR-VL_API.md`
- `docs/PaddleOCR/PP-StructureV3_API.md`
- `docs/PaddleOCR/PP-OCRv5_API.md`
- `docs/PaddleOCR/API 配额规则和错误码说明.md`
- `docs/PaddleOCR/PaddleOCR_MCP.md`

## API 事实摘要

PaddleOCR 同步示例通常使用模型对应接口，例如 layout parsing 或 OCR 接口：

- Header：`Authorization: token {TOKEN}`
- 输入：base64 文件内容
- PDF 的 `fileType` 为 `0`，图片的 `fileType` 为 `1`
- 返回结果可包含 `layoutParsingResults`

异步统一接口：

- Job endpoint：`https://paddleocr.aistudio-app.com/api/v2/ocr/jobs`
- Header：`Authorization: bearer {TOKEN}`
- 本地文件：multipart upload
- 远程文件：JSON `fileUrl`
- 状态：`pending`、`running`、`done`、`failed`
- 进度字段：`extractProgress.totalPages`、`extractProgress.extractedPages`
- 完成后结果：`resultUrl.jsonUrl`、`resultUrl.markdownUrl`

模型候选：

- `PaddleOCR-VL-1.6`
- `PaddleOCR-VL-1.5`
- `PaddleOCR-VL`
- `PP-StructureV3`
- `PP-OCRv5`

输出差异：

- `PaddleOCR-VL` / `PaddleOCR-VL-1.5` / `PP-StructureV3`：JSONL 中通常使用 `layoutParsingResults`，适合作为 Markdown 和结构化版面解析来源。
- `PP-OCRv5`：JSONL 中通常使用 `ocrResults`，更偏文本行 OCR 和坐标识别，不应直接等同于 Markdown 引擎。

页切分与图片切分：

- PDF 会被服务按页拆成结果数组。
- `useLayoutDetection` 启用自动版面区域检测和排序。
- `layoutShapeMode` 支持 `rect`、`quad`、`poly`、`auto`。
- `layoutMergeBboxesMode`、`layoutUnclipRatio`、`layoutThreshold`、`layoutNms` 控制区域合并、外扩、阈值和 NMS。
- `markdown.images`、`outputImages`、`inputImage` 可提供页面、裁剪图、可视化图或 Markdown 图片资源，具体形式取决于模型和接口。

限制与错误：

- 文档显示异步接口单次最大支持 1000 页 PDF。
- URL 文件大小上限 200 MB，本地上传文件大小上限 50 MB。
- 同步接口不同模型有不同页数限制；真实工作流应优先使用异步接口并做错误码提示。
- 配额文档给出的常见限制包括每日页数配额、鉴权失败、请求参数错误、文件错误、模型错误、配额不足、请求过快等。

## 密钥约束

PaddleOCR Token 统一使用环境变量：

```text
PADDLEOCR_API_TOKEN
```

约束：

- 不把真实 Token 写入 Git 跟踪文件。
- 允许本地创建被 `.gitignore` 忽略的私有文件，例如 `.env.paddleocr.local.md`。
- 日志、report、模型 registry 只记录环境变量名，不记录真实 Token。
- 测试中增加泄漏检查，确保最终 Markdown、`run_report.json` 和 `process.log` 不包含 Token 明文。

## 工作流模式

用户不应只看到孤立的 `engine_mode`。当前 GUI 已按“解析引擎”和“精修策略”分层展示，同时保留 CLI 稳定参数。

用户可理解的模式：

- 只用 MinerU：MinerU 解析后直接渲染 Markdown。
- 只用 PaddleOCR：PaddleOCR 解析后直接渲染 Markdown。
- MinerU + Markdown 精修：MinerU 负责版面/裁剪，DocPage2MD 使用 Vision/Brain 做公式、图表和正文修正。
- PaddleOCR + Markdown 精修：PaddleOCR 负责版面/裁剪，DocPage2MD 使用 Vision/Brain 做公式、图表和正文修正。
- 只用多模态：跳过 MinerU/PaddleOCR，用 Vision 模型直接做页面 Markdown 转换，保留为小题、截图、屏拍和极端失败 fallback。

建议内部模式名：

```text
mineru_only
paddleocr_only
mineru_hybrid
paddleocr_hybrid
dual_hybrid
vision_only
```

兼容策略：

- 现有 `hybrid` 继续等价于 `mineru_hybrid`，避免破坏旧脚本。
- 现有 `mineru_only` 保持不变。
- 新增 PaddleOCR/双引擎时优先增加显式 CLI 参数，例如 `--layout-engine mineru|paddleocr|dual|none` 与 `--refine-mode none|docpage2md`，再映射到旧 `engine_mode`。

## 输出适配设计

新增 PaddleOCR adapter，不让 renderer 直接消费第三方原始 JSON：

```text
PaddleOCR async job
  -> download jsonl / markdown / images
  -> preserve raw files under paddleocr_raw/
  -> PaddleOCRArtifact
  -> PageIR / BlockIR
  -> renderer
  -> optional crop Vision + Brain refinement
  -> validator + run_report.json
```

输出目录建议：

```text
paddleocr_raw/
  job.json
  result.jsonl
  result.md
  images/
assets/
  pages/
  crops/
  paddleocr/
ir/
run_report.json
process.log
Slide_XX.md
{doc_name}_FULL.md
```

Adapter 任务：

- 读取 `layoutParsingResults[]`，提取 `markdown.text`、`markdown.images`、`prunedResult`、`outputImages`、`inputImage`。
- 读取 `ocrResults[]`，保留文本行、坐标和 OCR 可视化图，作为较低层 OCR evidence。
- 把 PaddleOCR Markdown 拆为 PageIR blocks，而不是直接拼到最终 Markdown。
- 保留 bbox、置信度、类别、页面图片和裁剪图引用。
- 对公式、表格、图示说明继续走 DocPage2MD 的 Markdown contract 和 validator。

## MinerU + PaddleOCR 双引擎融合

`mineru_hybrid` 和 `paddleocr_hybrid` 是两条可选解析路径：同一文件要么以 MinerU 为前置解析，要么以 PaddleOCR 为前置解析。`dual_hybrid` 是首版双引擎融合路径：同一文件同时跑 MinerU 与 PaddleOCR，把两者共同输出作为候选证据，融合后得到更准确的 Markdown。

当前内部模式名：

```text
dual_hybrid
```

GUI 上显示为：

```text
MinerU + PaddleOCR 双引擎融合精修
```

首版已完成的范围：

- 本地文件、本地多文件、文件夹。
- 已有 artifact pair：`--mineru-artifact-dir` + `--paddleocr-artifact-dir`。
- MinerU 作为 primary layout/crop backbone，PaddleOCR 写入 `dual_evidence`。
- Brain prompt 接收 compact dual evidence，只允许 checked ops 局部修正。
- 输出保留 `mineru_raw/`、`paddleocr_raw/`、融合后的 `ir/document_ir.json` 和 `run_report.json`。

当前限制：

- 远程 URL 暂不直接支持双引擎，可先分别生成 artifact 后融合。
- 长 PDF 暂不做双引擎自动分段合并；超过 PaddleOCR chunk size 时阻止运行。
- 融合决策默认是离线保守策略；AI 结构化裁决的 prompt 和白名单边界已准备好，但真实 Brain 裁决还需要更多质量回归后再打开。

### 核心原则

- 同一个 PDF 的页码天然对齐，页级对齐由程序确定。
- block 不保证一一对应，不能强行按 block index 对齐。
- MinerU 和 PaddleOCR 任一方独有的内容都应默认保留为候选证据，不能因为另一方没有识别到就删除。
- AI 可以做裁决与融合，但程序必须负责候选打包、结果应用和校验。
- 最终 Markdown 仍必须通过现有 contract：公式 LaTeX 化、无裸 Unicode 数学符号、无 API Key、无 traceback、无 reasoning、无 validator 诊断文本。

### 推荐流程

```text
same PDF
  -> MinerU parse -> mineru_document_ir.json + mineru_raw/
  -> PaddleOCR parse -> paddleocr_document_ir.json + paddleocr_raw/
  -> page-level alignment by page number
  -> candidate grouping inside each page
  -> Brain decides choose / merge / keep-both / mark-uncertain
  -> program applies checked ops into fused_document_ir.json
  -> renderer + validator
  -> optional region/full-page visual recovery
  -> Slide_XX.md + *_FULL.md + run_report.json
```

建议输出目录：

```text
mineru_raw/
paddleocr_raw/
assets/
  mineru/
  paddleocr/
ir/
  mineru_document_ir.json
  paddleocr_document_ir.json
  fused_document_ir.json
run_report.json
process.log
Slide_XX.md
{doc_name}_FULL.md
```

### block 粗分组，而不是强行对齐

每页先构建一个候选池：

```text
page 4
  MinerU blocks: M1, M2, M3...
  PaddleOCR blocks: P1, P2, P3...
```

程序只做低风险粗分组：

- bbox 重叠度高的归为同组。
- 文本相似度高的归为同组。
- 垂直位置接近、类型相近的归为同组。
- 疑似 caption 与图片区域靠近时归为同组。
- 无法匹配的 block 单独成组，标为 `unmatched_from_mineru` 或 `unmatched_from_paddleocr`。

候选组示例：

```json
{
  "group_id": "p0004-g003",
  "type_hint": "formula",
  "candidates": [
    {"source": "mineru", "block_id": "M7", "text": "...", "bbox": [120, 310, 500, 360]},
    {"source": "paddleocr", "block_id": "P5", "text": "...", "bbox": [118, 308, 505, 365]}
  ],
  "warnings": ["mineru_has_raw_unicode_math", "paddleocr_latex_balanced"]
}
```

### AI 的职责边界

不建议让 AI 自己从整页原始 JSON 中自由寻找所有对应关系。更稳的方式是：程序给出候选组，AI 在组内或相邻组内裁决。

AI 输出应是结构化操作，而不是直接重写整页 Markdown：

```json
{
  "ops": [
    {
      "action": "choose_block",
      "target_group": "p0004-g003",
      "source": "paddleocr",
      "reason": "PaddleOCR 候选是完整 LaTeX，MinerU 候选含裸 Unicode 符号。"
    },
    {
      "action": "merge_blocks",
      "target_group": "p0004-g006",
      "sources": ["mineru:M9", "paddleocr:P12"],
      "text": "..."
    },
    {
      "action": "keep_both",
      "target_group": "p0004-g008",
      "reason": "一方是图像区域，一方是图注文本，二者互补。"
    }
  ]
}
```

程序只接受白名单操作，并在应用后重新运行 validator。若 AI 给出的操作降低覆盖率、破坏 LaTeX、丢失图片引用或引入诊断文本，应拒绝该操作并保留原候选。

### 漏公式、漏图片和图片拆分的处理

漏公式：

- 如果一方有 `formula_block`，另一方没有，先单独保留为候选组。
- 如果公式被识别成普通 text，程序用公式检测器标记 suspect，再交给 AI 裁决。
- 选择标准包括：LaTeX 是否平衡、是否含裸 Unicode 数学符号、formula validator 警告数量、与上下文是否一致。

漏图片：

- 图片和图示区域不能只依赖 OCR 文本。
- 同页保留 MinerU crop、PaddleOCR `markdown.images`、`outputImages`、`inputImage` 和 page image 作为候选 evidence。
- 如果只有一边有图片，默认保留，不因另一边缺失而删除。

图片被拆太多：

- 程序用 bbox 几何规则识别碎片：多个小图距离很近、位于同一大区域、周围无独立标题时，标记为 `possible_fragmented_figure`。
- 若另一边给出完整图，则把完整图和碎片组放入同一候选组。
- AI 决定保留整体图、保留多个局部图，或整体图加局部说明。

核心策略：宁可多保留并在 `run_report.json` 记录不确定，也不要误删。

### figure 描述上下文必须加强

生成 figure 描述时，不能只给 crop 图片。建议 Vision/Brain 的 figure prompt 至少包含：

- 当前页标题或小节标题。
- 图前后 1-2 个文本 block。
- 图附近公式。
- caption 或疑似 caption。
- 图像 bbox、来源引擎和 block 类型。
- 如果启用双引擎融合，提供另一引擎在同一区域的候选文本、候选图像或候选 caption。
- 文档类型，例如“手写群论笔记”“论文 PDF”“复杂公式图表 PPT”。

推荐上下文包：

```json
{
  "page": 4,
  "document_type": "手写群论笔记",
  "figure_block": {
    "id": "p0004-b006",
    "source": "mineru",
    "bbox": [120, 300, 580, 720],
    "nearby_text_before": ["令 G 为群，考虑其在集合 X 上的作用。"],
    "nearby_text_after": ["因此轨道分解给出等价类。"],
    "nearby_formulas": ["G \\curvearrowright X", "Gx = \\{gx: g \\in G\\}"],
    "caption_candidates": ["图示：群作用下的轨道"],
    "other_engine_candidates": [
      {"source": "paddleocr", "text": "...", "image_ref": "assets/paddleocr/..."}
    ]
  }
}
```

模型输出应是结构化 JSON，例如：

```json
{
  "description": "...",
  "labels": ["G", "X", "orbit"],
  "relations": ["箭头表示群元素作用"],
  "latex": ["G \\curvearrowright X"],
  "uncertainties": []
}
```

这些 figure 描述最后仍应渲染为 Typora 兼容且默认关闭的 `<details>` 块。

## CLI 与 GUI 交互

CLI 当前已支持：

- `--layout-engine mineru|paddleocr|dual|none`。
- `--refine-mode none|docpage2md`。
- `--paddleocr-model PaddleOCR-VL-1.6|PaddleOCR-VL-1.5|PaddleOCR-VL|PP-StructureV3|PP-OCRv5`。
- `--paddleocr-api-key-env PADDLEOCR_API_TOKEN`，默认读取 `PADDLEOCR_API_TOKEN`。
- PaddleOCR optional payload 参数，先覆盖文档中确认的稳定开关：
  - `--paddleocr-doc-orientation`
  - `--paddleocr-doc-unwarping`
  - `--paddleocr-chart-recognition`
  - `--paddleocr-layout-detection`
  - `--paddleocr-formula-recognition`
  - `--paddleocr-table-recognition`
- 当前默认优先异步接口，没有单独暴露同步接口开关。

GUI 当前已实现：

- “文档类型”只作为推荐预设，不和模式冲突。
- “解析引擎”单独选择：MinerU、PaddleOCR、MinerU + PaddleOCR 双引擎融合。
- “Markdown 精修”单独选择：关闭、开启 DocPage2MD 精修。
- “处理模式”显示成中文组合结果，例如“PaddleOCR + Markdown 精修”。
- 在模式旁边显示中文说明，明确速度、成本和适用场景。
- PaddleOCR 运行时使用异步进度字段显示真实页数进度和 ETA。
- 日志使用中文，例如“PaddleOCR 任务已提交”“等待 PaddleOCR 解析”“PaddleOCR Markdown 已生成”。

WebUI 后续应把 PaddleOCR 纳入同一工作台：

- 输入页选择文件/URL/artifact。
- 解析页选择 MinerU / PaddleOCR / 多模态。
- 精修页选择是否启用 Vision/Brain。
- 运行页显示 PDF 总进度、PaddleOCR 已解析页数、DocPage2MD 已精修页数、并发数和 ETA。
- 输出页显示 PaddleOCR 原始 Markdown、DocPage2MD 最终 Markdown、页面图、assets 和 report。

## 模型与参数管理

PaddleOCR 不是 Vision/Brain 模型，但应纳入模型管理器的 provider registry：

- provider：`paddleocr`
- role：`layout_engine`
- api_key_env：`PADDLEOCR_API_TOKEN`
- models：
  - `PaddleOCR-VL-1.6`
  - `PaddleOCR-VL-1.5`
  - `PaddleOCR-VL`
  - `PP-StructureV3`
  - `PP-OCRv5`

默认推荐：

- 手写矢量笔记：先对比 MinerU 与 `PaddleOCR-VL-1.6`。
- 扫描/屏拍/弯曲/复杂光照：优先试 `PaddleOCR-VL-1.6` 或 `PaddleOCR-VL-1.5`。
- 表格/结构化文档：对比 `PP-StructureV3`。
- 纯 OCR 文本：可试 `PP-OCRv5`，但不默认作为 Markdown 引擎。

## 测试计划

真实私有测试目录：

```text
tests/test-PaddleOCR/
```

该目录已被 `.gitignore` 忽略，用于后续放置真实 PDF、图片和输出对照，不提交到 Git。

离线测试：

- 增加 `tests/fixtures/paddleocr/`，放脱敏的 JSONL、Markdown 和图片元数据 fixture。
- 测试 `layoutParsingResults` -> PageIR。
- 测试 `ocrResults` -> OCR evidence。
- 测试 `markdown.images` / `outputImages` 资产落盘与相对链接。
- 测试坏 JSONL、缺字段、空页、部分失败页。
- 测试 Token 泄漏检查。

HTTP 假服务测试：

- 提交 job 成功。
- `pending` / `running` / `done` 状态轮询。
- `extractProgress.totalPages` / `extractedPages` 进度和 ETA。
- `failed` 状态错误码进入 `run_report.json`，不污染用户 Markdown。
- 下载 `jsonUrl`、`markdownUrl` 失败时的重试和错误提示。

真实验收：

- 使用 `tests/test-PaddleOCR/` 中的真实文件。
- 至少跑：
  - `paddleocr_only`
  - `paddleocr_hybrid`
  - 与同一文件的 `mineru_only` / `mineru_hybrid` 对比
- 验收输出包含 `Slide_XX.md`、`*_FULL.md`、`run_report.json`、`ir/`、`paddleocr_raw/`、`assets/`。
- Markdown 不包含 API Key、Python traceback、provider 原始错误、validator 诊断文本或模型思考过程。

## 分阶段实施

### Phase 1：PaddleOCR Client 与 Artifact

- 新增异步 API client。
- 支持本地文件和 URL。
- 保存 job 状态、JSONL、Markdown、图片资源。
- 中文日志与真实页数进度。
- 离线 fake HTTP 测试。

### Phase 2：PaddleOCR Adapter

- 将 `layoutParsingResults` 转为 PageIR。
- 将 `ocrResults` 转为 OCR evidence。
- 将图片资源落到 `assets/`，并保持相对链接稳定。
- 将原始数据保存在 `paddleocr_raw/`。

### Phase 3：处理模式接入

- 新增 `paddleocr_only`。
- 新增 `paddleocr_hybrid`。
- 新增 `dual_hybrid` 首版。
- 保持 `hybrid` 对旧用户等价于 `mineru_hybrid`。
- 更新 CLI help、README、GUI 模式说明和 tests。

### Phase 4：GUI/WebUI 交互优化

- Tkinter 先做可用的引擎选择和中文说明。
- WebUI 原型中实现更清晰的“解析引擎 + 精修策略”工作台。
- PaddleOCR 进度接入总进度条和 ETA。

### Phase 5：质量对比与默认策略

- 用 `tests/test-PaddleOCR/` 私有真实样本对比 MinerU 和 PaddleOCR。
- 记录不同文档类型下的速度、成本、公式质量、表格质量、图片切分质量。
- 决定默认推荐策略，不用一次性替换 MinerU。

### Phase 6：双引擎融合升级

- 已实现 bbox/text/type candidate grouping，而不是只把 PaddleOCR 作为整页证据。
- 已记录每个候选组的 choose/merge/keep-both/mark-uncertain 审计。
- 待实现 `dual_hybrid` 自动 chunked merge。
- 待在更多真实样本上评估是否启用 Brain 结构化融合裁决。
- 用真实长 PDF 和复杂公式页比较 `mineru_hybrid`、`paddleocr_hybrid`、`dual_hybrid` 的质量和耗时。

## 不做的事

- 不把 PaddleOCR 原始 Markdown 无检查地直接作为最终产物。
- 不把 Token 写进 registry、report、日志或 Git 跟踪文件。
- 不为了接 PaddleOCR 重构 renderer、validator 或 hybrid 核心契约。
- 不读取、不删除 `markdown_output/已归档`。
