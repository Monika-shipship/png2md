# Changelog

## 2026-06-26

### Added

- 新增输出保留模式：
  - CLI 增加 `--output-retention slim|standard|debug`。
  - 默认 `slim` 只保留 Markdown、必要 assets、meta、日志和 `run_report.json`，并在成功后清理生成的解析 cache。
  - `standard` 额外保留 IR；`debug` 额外保留 `mineru_raw/`、`paddleocr_raw/` 和解析 cache。
  - GUI “输出与并发”区增加保留模式选择。
- 新增多文件解析调度参数：
  - CLI 增加 `--parser-workers`，控制多文件上传/等待 MinerU/PaddleOCR 的并发，默认 `8`。
  - CLI 增加 `--doc-workers`，控制多文件文档级融合/精修并发，默认 `1`。
  - GUI 增加“解析/文档”并发输入，和 Vision/Brain 并发分开。
- 新增 first-class `findings` 架构：
  - 新报告使用 `pages[].findings.initial`、`brain_decisions`、`brain_discovered` 和 `summary.findings`。
  - 旧 `suspects` 输出不再写入新的 run report。
  - Brain 审阅输出升级为三段式 JSON：`decisions`、`new_findings`、`op_candidates`。
  - Initial findings 现在明确包含 `deterministic_detector`、`validator_precheck`、`dual_engine_diff` 和 `vision_crop_evidence` 来源。
- 新增可配置 Brain 上下文窗口：
  - CLI 增加 `--brain-context-radius`，默认 `2`，`0` 表示只看当前页。
  - GUI “并发”区域增加 Brain 上下文选择和自定义半径。
  - `process.log` / Brain report 记录配置半径、实际上下文页和截断说明。
- GUI 成本估算拆分 Vision 与 Brain：
  - 主成本表显示 Vision 输入/输出/费用、Brain 输入/输出/费用和总费用。
  - 新增 Brain 窗口成本对比表，默认比较 `0/1/2/3/5`。
  - CLI 成本表同步显示 Vision/Brain 费用分项，并尊重 Brain 上下文窗口。

### Verified

- 使用既有 `群论笔记4.1` MinerU/PaddleOCR artifacts 真实验证 `dual_hybrid`：
  - 输出：`markdown_output/findings_brain_window_verify/dual_4_1_findings_window_v3`。
  - 配置：balanced，Vision workers `60`，Brain workers `60`，`--brain-context-radius 2`，Brain thinking disabled。
  - 结果：`status=ok`，11/11 页，`summary.findings.total=224`，`brain_discovered_count=22`。
  - `summary.findings.by_source`: `validator_precheck=36`、`dual_engine_diff=138`、`vision_crop_evidence=48`、`deterministic_detector=2`。
  - Brain report 记录 `configured_radius=2`，实际上下文页数为 `3/4/5`。
  - `run_report.json` 不再包含 `summary.suspects` 或 `pages[].suspects`。
  - 最终 FULL Markdown 未发现 `[mineru]` / `[paddleocr]`、Traceback、reasoning、validator 文本或 `<details open>`。
  - 本次耗时约 `96.8s`：48 个 crop Vision 请求约 `34.2s`，Brain 11 页约 `61.2s`；长尾来自 provider 响应，不是并发被移除。

### Fixed

- 修复扫描 PDF 页数识别失败：
  - `estimate_pdf_pages()` 现在优先尝试 `pypdf/PyPDF2`，再尝试系统 `pdfinfo`，再 fallback 到直接 `/Page` marker 和压缩 object stream 解码。
  - 已验证 `D:\大学学习\课程资料\lz毛概\2009年马原期末考试（A B）.pdf` 可识别为 9 页。
- 优化双引擎本地多文件处理：
  - 旧流程按文件串行：一个文件完成 MinerU/PaddleOCR 解析和后续融合精修后，才开始下一个文件。
  - 新流程先跨文件并发准备解析 artifact；某个文件的 MinerU/PaddleOCR artifact 都就绪后，立即进入文档处理队列。
  - 日志会显示解析并发、文档并发、Vision 并发和 Brain 并发。
- 修复双引擎 `paddleocr` origin 触发 Brain op 合同校验失败的问题：
  - `paddleocr` 现在是合法 block origin / vision evidence origin。
  - PaddleOCR Markdown fallback block 补齐 `bbox`。
  - 已用既有 `群论笔记4.1` MinerU/PaddleOCR artifact 验证 `ir/document_ir.json` 无 page IR contract error。
- Brain 审阅从提示词约束升级为本地硬约束：
  - 每个 Brain op 必须携带 `decision`、`evidence_type`、`confidence` 和具体目标。
  - 低置信正文替换、缺少目标 block、缺少 checked span、整页 Markdown 改写会被本地拒绝。
  - `op_audit` / summary 记录拒绝原因和 contract error code。
- 修复空文本 `image_ref` / `figure_note` 被 deterministic refiner 当作空块删除的问题。只要 block 带图片路径或结构化图示信息，就保留给 renderer。
- 图示说明 renderer 会把 Vision 返回的 JSON/近似 JSON 转成中文字段，不再把 `figure_type`、`relations`、`uncertainties` 等原始英文键名输出到用户 Markdown。

### Verified

- 真实双引擎验证输出：`markdown_output/real_contract_fix_smoke/real_contract_fix_4_1_v3`。
- 配置：既有 MinerU/PaddleOCR artifact，`dual_hybrid`，balanced，Vision workers `60`，Brain workers `60`，Brain thinking disabled。
- 结果：`status=ok`，11/11 页，`contract_error_codes={}`，`brain_discovered_count=27`。
- 最终 Markdown 扫描未发现 API Key、Traceback、模型推理内容、validator 文本、provider 错误、`[mineru]` / `[paddleocr]` 候选标签、`<details open>` 或原始图示 JSON 键名。
- 页面 3 图示保留为默认关闭的中文 `<details>` 块。
- 本次耗时主要来自 Vision provider 长尾：48 个 crop Vision 请求约 `65.9s`，Brain 11 页约 `20.7s`。

## 2026-06-25

### Added

- 新增 Brain 并发长尾诊断：
  - 每页 Brain 精修报告记录 `elapsed_seconds`。
  - `process.log` 现在会写出 Brain p50/p90/max、最慢页和长尾系数。
  - 当最慢页明显慢于中位页时，日志会用中文提示尝试 Brain 并发 `6` 或 `3` 做同文件对照。
- GUI “输出与并发”区新增并发预设：
  - `保守 3/3`
  - `均衡 6/6`
  - `高并发 12/12`
  - `极速 60/60`
  - `自定义`
  - 保留原来的 Vision/Brain 数字输入，预设只负责快速填值，不移除高并发能力。
- 新增 Brain 快速/高质量模式：
  - CLI 增加 `--brain-thinking enabled|disabled` 和 `--brain-reasoning-effort high|max`。
  - GUI “并发”区增加 `Brain 模式`，默认 `快速：关闭思考（推荐）`，疑难页可手动改为 `高质量：开启思考`。
  - `run_report.json` / fingerprint 会记录 Brain thinking mode，日志会显示实际并发、配置上限和当前模式。
- 升级 `dual_hybrid` 双引擎融合层：
  - 新增 `docpage2md_app/fusion.py` 和 `docpage2md_app/fusion_prompt.py`。
  - 同页 MinerU/PaddleOCR block 会先按 bbox 重叠、文本相似度、垂直位置、类型相似度和图注/图片邻近关系构建候选组。
  - 程序只接受白名单融合操作：`choose_block`、`merge_blocks`、`keep_both`、`mark_uncertain`、`attach_image`、`replace_formula`、`convert_text_to_formula`、`convert_text_to_figure_note`。
  - 双引擎输出新增 `ir/mineru_document_ir.json`、`ir/paddleocr_document_ir.json`、`ir/fused_document_ir.json`，并保留兼容 `ir/document_ir.json`。
  - `run_report.json["fusion"]` 记录候选组、融合决策、被拒绝操作和不确定项。
- 正式接入 PaddleOCR 主路径：
  - 新增 `paddleocr_only` 和 `paddleocr_hybrid`。
  - 新增 `--layout-engine mineru|paddleocr|dual|none` 和 `--refine-mode none|docpage2md`。
  - 新增 PaddleOCR 参数：`--paddleocr-model`、`--paddleocr-api-key-env`、`--paddleocr-base-url`、`--paddleocr-artifact-dir`、`--paddleocr-url`、`--paddleocr-page-chunk-size` 和 optional payload 开关。
  - 默认模型为 `PaddleOCR-VL-1.6`，默认异步接口为 `https://paddleocr.aistudio-app.com/api/v2/ocr/jobs`。
  - 本地 PDF 默认按 100 页分段，输出保留 `paddleocr_raw/`、`ir/`、`assets/`、`Slide_XX.md`、`*_FULL.md` 和 `run_report.json`。
- 新增 `dual_hybrid` 双引擎融合首版：
  - CLI 支持 `--engine-mode dual_hybrid` 和 `--layout-engine dual`。
  - 同一输入先走 MinerU 和 PaddleOCR，MinerU 作为主版面/crop 骨架，PaddleOCR 作为同页交叉证据，再复用现有 crop Vision、Brain JSON ops、checked refiner 和 renderer。
  - 支持本地单文件、多文件、文件夹，以及同时提供 `--mineru-artifact-dir` + `--paddleocr-artifact-dir` 的 artifact 融合。
  - 输出同时保留 `mineru_raw/`、`paddleocr_raw/`、融合后的 `ir/document_ir.json`、`Slide_XX.md`、`*_FULL.md` 和 `run_report.json`。
- 新增 PaddleOCR client / artifact / adapter / pipeline：
  - 支持解析 `layoutParsingResults`、`prunedResult`、`ocrResults`、Markdown 图片、`outputImages` 和 `inputImage`。
  - PaddleOCR artifact 先转换为现有 DocumentIR，再复用 renderer、validator 和 hybrid enrichment。
  - 运行日志补充中文 PaddleOCR 阶段：提交任务、排队、解析页数、下载结果、转换 IR、精修、渲染和合并。
- “刷新官方模型/价格”升级为 provider-aware 刷新系统：
  - `--refresh-models`
  - `--refresh-prices`
  - `--providers dashscope,deepseek,openai-compatible`
  - `--show-model-diff`
  - `--import-pricing-md`
  - DashScope 使用官方文档/parser，DeepSeek 使用 `/models` + 官方价格页解析，OpenAI-compatible 只自动发现模型列表且不猜价格。
- 重构 README 为 GUI-first 用户首页：
  - 开头直接说明项目用途、GUI 入口和从 0 开始配置流程。
  - CLI、输入格式、模式、模型、成本、安全和排错按用户使用顺序重排。
  - 长篇原理说明改为链接到 `docs/architecture/*`，避免 README 再变成大杂烩。
- 新增 GUI 输入文件表：
  - 显示文件名、后缀、大小、页数、限制状态和处理顺序。
  - 支持添加文件、添加文件夹、删除、清空、上移/下移、打开文件、打开目录和预览占位。
  - 旧的分号路径串保留为内部 CLI 兼容层，不再作为主要用户操作面。
- 新增 MinerU 高级参数的 GUI/CLI 非交互能力：
  - `--mineru-is-ocr`
  - `--mineru-enable-formula`
  - `--mineru-enable-table`
  - `--mineru-language`
  - `--auto-split-pages`
  - `--mineru-page-chunk-size`
- 新增本地 PDF 超页自动分段基础能力：
  - 默认按 200 页规划 chunk，例如 `1-200`、`201-400`、`401-401`。
  - 每段先写独立 chunk 输出目录，再合并成最终 `Slide_XX.md`、`*_FULL.md` 和 `run_report.json`。
  - `run_report.json` 记录 `mineru.chunks` 和 `mineru.chunked_merge` 审计信息。
- 新增统一 secrets 读取/写入层 `docpage2md_app/secrets.py`：
  - 支持进程环境变量、本地 ignored `.env.local.json`、Windows 用户环境变量和 Windows Credential Manager。
  - GUI Key 检查只读本机 secret，不联网；模型验证才发轻量 API 请求。
- 模型管理 GUI 增加 Provider-first 页面：
  - Provider：MinerU、PaddleOCR、DashScope、DeepSeek、OpenAI-compatible。
  - 角色绑定：Vision / Brain 分别绑定到 Provider + 模型。
  - 增加获取 API Key 链接、Key 保存位置、检查 Key 和验证模型按钮。
- 成本 UI 改为表格，按文件显示页数、估计裁剪块、输入/输出 tokens、费用和可信度；MinerU/PaddleOCR 显示为平台额度/限制，不计入模型费用。
- 新增 PaddleOCR 集成路线图：`docs/plans/paddleocr-integration-roadmap.md`。
  - 已纳入 `PaddleOCR-VL-1.5`、`PaddleOCR-VL-1.6`、异步 API、`PP-StructureV3`、`PP-OCRv5` 等本地文档结论。
  - 规划后续模式：`mineru_only`、`paddleocr_only`、`mineru_hybrid`、`paddleocr_hybrid`、`vision_only`。
  - 规划 `tests/test-PaddleOCR/` 作为 ignored 私有真实测试目录，并要求 PaddleOCR Token 只通过 `PADDLEOCR_API_TOKEN` 或 ignored 本地文件保存。
- 优化 Tkinter GUI 信息架构：
  - 运行页改为左侧工作流/输入/输出并发、右侧进度/成本命令/日志/操作的工作台布局。
  - 模型页拆成“当前配置”“候选模型”“第三方模型库”。
  - 候选模型支持筛选，第三方模型库支持列表化管理和 OpenAI-compatible `/models` 自动发现。
  - `hybrid` 启动前会检查 Vision/Brain 模型配置完整性、Key 环境变量和明显错误组合。

### Changed

- 加速 `dual_hybrid` 本地单文件前置解析：
  - 同一输入文件的 MinerU 和 PaddleOCR 提交、等待、artifact 下载现在并行执行。
  - 解析前置等待从约 `MinerU + PaddleOCR` 降为约 `max(MinerU, PaddleOCR)`，后续融合、crop Vision 和 Brain 精修流程不变。
  - `RunLogger` 增加线程锁，避免双解析并行时日志行交错。
- 默认 Brain 精修关闭 DeepSeek/DashScope 思考模式：
  - 过去 balanced Brain 请求会进入高延迟思考路径，11 页文档容易被 provider 长尾拖到 90 秒以上。
  - 新默认更适合 JSON ops / Markdown 结构修正；用户仍可在 CLI/GUI 中开启高质量思考。
- GUI 进度条现在能从 Brain 批处理完成日志推进页进度，并在状态区显示 Brain p50/p90/max 长尾摘要。
- 修复 Windows 受限目录中的写入兼容性：`write_text_atomic()` 在目录允许创建但拒绝 rename/delete 时，会降级为直接写入，并尽量清理临时文件，避免 MinerU cache/report 写入中断。
- 修复 PaddleOCR `paddleocr_hybrid` 的置信度兼容问题：
  - PaddleOCR adapter 现在把 `block.confidence` 写为 `0.0-1.0` 浮点数。
  - `high/medium/low` 人类可读标签保存在 `confidence_label`，避免精修器把字符串转成 float 时失败。
- 加强 PaddleOCR API 稳定性和限额提示：
  - 提交、轮询和结果下载在 `429/503/504` 或网络错误时按配置重试。
  - 远程 URL 输入会尽量用 HEAD 检查 `Content-Length`，可判定超过 200MB 时提前阻止。
- 官方模型/价格缓存新增 provider 级刷新状态：
  - `refresh.provider_status` 记录每个 Provider 的状态、来源 URL、模型数量和失败原因。
  - OpenAI-compatible 继续只发现 `/models`，价格保持 `user_required`，不自动猜测。
  - DashScope 官方文档抓取会过滤明显的文档 slug 伪模型，例如 `qwen-false`、`qwen-usage-list` 和 `qwen-vl-compatible-with-openai`。
- 修复 Tkinter GUI 自动化/关闭时可能残留 `_drain_output_queue` after 回调并打印 Tcl 噪声的问题。
- 修复 Tkinter GUI 非全屏窗口下的信息截断问题：
  - 运行页改为可垂直滚动，避免“输出与并发”被首屏高度挤出。
  - 成本摘要动态换行，成本表支持横向滚动。
  - 命令预览支持横向滚动、一键复制和完整命令窗口。
- 继续加强最终 Markdown 的数学符号规范化：
  - 单个裸 Unicode 数学符号会包成 LaTeX inline math。
  - `G→S`、`k→g→?` 这类箭头表达式会作为完整公式片段处理，避免生成重叠 `$...$`。
  - 修复图示说明中的箭头链触发 `display_math_unbalanced` / `inline_math_unbalanced` 的问题。
- 渲染器新增相邻短标题去重保护：
  - 当 Brain 把后一块 OCR 标题修正后与上一块短标题完全重复时，只渲染一次标题，保留后一块正文/公式。
  - 真实 `dual_hybrid` 页 1 中重复的 `(2)结合律：` 已修复。

### Verified

- `python docpage2md.py --help`：通过。
- `python -m docpage2md_app --help`：通过。
- `python -m pytest -q`：307 passed。
- `git diff --check`：无 whitespace error，仅有 CRLF 提示。
- Tkinter GUI 构建 smoke 通过：`DocPage2MdGui()` 能创建、刷新 idle tasks 并销毁；运行页滚动容器、成本表横向滚动和命令预览横向滚动存在。
- 聚焦 GUI/CLI/MinerU/secrets 测试：54 passed。
- 聚焦 PaddleOCR/official catalog 测试：45 passed。
- 聚焦 PaddleOCR hardening 测试：30 passed，覆盖坏 JSONL/空页、`429/503/504` 重试、下载重试、URL 200MB 限制和 provider 状态缓存。
- 使用真实 `tests/群论笔记4.1.pdf` 对当前版本做全量 hybrid 验证：
  - 输出目录：`markdown_output/git_verify_20260625_final2/git_verify_4_1_final2`。
  - 11 页全量，`hybrid + balanced`，Vision `qwen3-vl-plus`，Brain `deepseek-v4-flash`。
  - 并发：Vision `60`、Brain `60`；实际裁剪块 worker 49，实际 Brain worker 11。
  - `run_report.json`：`status=ok`，`engine_mode=hybrid`，`pages_ok=11/11`。
  - 49 个 crop Vision block 全部成功；Brain 11 页并行完成。
  - 最终用户 Markdown 未发现 API Key、Python traceback、`reasoning_content`、validator 诊断文本、`<details open>` 或 `> [!NOTE]`。
- 使用真实 `tests/群论笔记4.1.pdf` 通过 Tkinter GUI 路径做 PaddleOCR 双模式验收：
  - `paddleocr_only` 输出目录：`markdown_output/gui_paddleocr_real_verify_only/gui_paddleocr_4_1_only`，11 页全量，`status=ok`，最终页 `ok=11/11`，约 `19.1s`。
  - `paddleocr_hybrid` 输出目录：`markdown_output/gui_paddleocr_real_verify_hybrid/gui_paddleocr_4_1_hybrid`，11 页全量，`status=ok`，最终页 `ok=11/11`，Brain `partial=11/11`，约 `106.0s`。
  - 两个输出都包含 `paddleocr_raw/`、`ir/`、`assets/`、`Slide_XX.md`、`*_FULL.md`、`run_report.json` 和中文 `process.log`。
  - 最终用户 Markdown 未发现 API Key、Python traceback、validator 文本、模型思考过程或置信度转换错误。
- 使用真实 `tests/群论笔记4.1.pdf` 验证 PaddleOCR API 与早期 `dual_hybrid`：
  - PaddleOCR-only API 探针输出：`markdown_output/paddleocr_api_probe_20260625/paddleocr_api_probe_page1`，1 页，`status=ok`，确认真实返回包含 `layoutParsingResults/prunedResult/markdown/outputImages/inputImage/dataInfo`。
  - 双引擎真实页 1 输出：`markdown_output/dual_real_probe_20260625/dual_real_probe_page1`，`status=ok`，`engine_mode=dual_hybrid`，历史策略为 `mineru_primary_paddleocr_evidence`。
  - 修复重复标题后，用真实 artifact 复跑输出：`markdown_output/dual_real_artifact_rerun_20260625/dual_real_artifact_rerun_page1`，`status=ok`，1/1 页，layout model `vlm+PaddleOCR-VL-1.6`，Vision `qwen3-vl-plus`，Brain `deepseek-v4-flash`。
  - 最终用户 Markdown 未发现 API Key、Python traceback、provider 原始错误、validator 诊断文本或模型思考过程。
- 使用最新 GUI `dual_hybrid` 全量 smoke 分析耗时：
  - 输出目录：`markdown_output/gui_full_pdf_smoke`。
  - 两份 PDF 总 wall time 约 `347.2s`。
  - `群论笔记3.1`：parser prep 约 `53.5s`，crop Vision `70` blocks 约 `38.9s`，Brain `13` pages 约 `124.1s`。
  - `群论笔记4.1`：crop Vision `47` blocks 约 `12.8s`，Brain `11` pages 约 `91.6s`。
  - 结论：主要瓶颈是 Brain 长尾和双解析/PaddleOCR artifact 下载，不是页面 Brain 并发被删。
- 使用已有 `群论笔记4.1` 双引擎 artifact 做 Brain 并发对照：
  - 输出目录：`markdown_output/concurrency_ab_4_1_brain6/dual_4_1_brain6`。
  - Vision `60`、Brain `6`，不重复 MinerU/PaddleOCR 上传解析。
  - Brain total 约 `94.7s`，p50 `39.2s`，p90 `50.8s`，max `53.6s`，长尾系数 `1.37`。
  - 对比上一轮 Brain workers `11` 的 total 约 `91.6s`、max 约 `91.6s`：降低并发能压低最慢页，但不一定降低总 wall time。
- 使用同一 `群论笔记4.1` 双引擎 artifact 验证 Brain 快速模式：
  - 输出目录：`markdown_output/concurrency_ab_4_1_fast_brain/dual_4_1_fast_brain`。
  - Vision `60`、Brain `60`，实际 Brain worker `11`，`--brain-thinking disabled`。
  - Crop Vision `47` blocks 约 `20.9s`。
  - Brain total 约 `12.2s`，p50 `8.4s`，p90 `11.9s`，max `12.1s`。
  - 对比旧 thinking 路径 `91.6s`：耗时长的主因是 Brain 思考模式长尾，不是并发被删除。
  - 最终用户 Markdown 未发现 API Key、Traceback、validator 文本或模型思考过程。
- 双引擎候选组融合离线验证：
  - `python -m pytest tests/test_fusion.py tests/test_dual_pipeline.py tests/test_hybrid_enrichment.py tests/test_mineru_pipeline.py tests/test_paddleocr_pipeline.py tests/test_validators.py -q`：46 passed。
  - 覆盖页级对齐、bbox/text 粗分组、未匹配 block 保留、公式候选替换、坏操作拒绝、prompt 不暴露内部 block 对象和 pipeline 写出 `fused_document_ir.json`。
- 同一 PDF 主路径耗时对比已记录：
  - `mineru_only`：约 `16.4s`。
  - `mineru_hybrid` / `hybrid`：约 `113.9s`。
  - `paddleocr_only`：约 `19.1s`。
  - `paddleocr_hybrid`：约 `106.0s`。

## 2026-06-24

### Changed

- README now has a beginner-oriented quick start for single PDF conversion, explains where to put private input files, and documents the Tkinter GUI entrypoints.
- 新增/完善轻量 GUI：
  - 入口：`python docpage2md_gui.py` 和 `python -m docpage2md_app.gui`。
  - 支持本地单文件、多文件、文件夹、MinerU artifact、远程 URL。
  - 支持中文文档类型、处理模式、模型档位、页码范围、输出目录、命令预览、成本估算、进度条、ETA、放大日志窗口和打开输出目录。
  - 支持 Vision/Brain 并发数设置，默认 `60/60`。
  - 支持官方模型选择、第三方模型 CRUD/批量导入/API Key 环境变量检查和验证。
- 新增 CLI 非交互模型覆盖参数：
  - `--vision-provider`
  - `--vision-model`
  - `--vision-base-url`
  - `--vision-api-key-env`
  - `--brain-provider`
  - `--brain-model`
  - `--brain-base-url`
  - `--brain-api-key-env`
  - 显式覆盖在 `--model-profile` 后应用，`manual` 档位也可完整运行。
- Added `input_docs/` as the recommended local ignored directory for private PDFs, Office files and images.
- Clarified that `markdown_output/` and `latex_output/` are local user assets and must not be automatically deleted by cleanup work.
- 统一项目命名为 `DocPage2MD`：
  - 正式入口为 `docpage2md.py`。
  - 正式 Python 包名为 `docpage2md_app`。
  - 历史入口文件已从工作树移除，删除记录由 Git 跟踪。
  - 默认文档页图片目录为 `doc_pages/`。
- 文档、测试、schema、provenance 和版本常量统一改为 `docpage2md` 命名：
  - `DOCPAGE2MD_PIPELINE_VERSION`
  - `docpage2md-docir-v1`
  - `docpage2md-provenance`
- 清理内部历史命名残留：
  - `process_single_docpage_task`
  - `scan_docpage_folders`
  - `DEFAULT_MAX_DOCPAGE_WORKERS`
  - `max_docpage_workers`
  - `doc_name` / `doc_root`
- 增强 MinerU / hybrid 运行日志：
  - 终端实时输出关键阶段，并由 `RunLogger` 统一翻译成中文。
  - 每个任务输出目录写入 `process.log`。
  - 日志覆盖提交、上传、轮询、下载、解压、IR 适配、crop 复制、crop vision、Brain、refiner、逐页渲染和 report 写入。
  - 新增 crop Vision、Brain、Markdown 渲染阶段耗时汇总，方便定位速度瓶颈。
  - 日志只记录环境变量名，不记录真实 token。
- 明确并保留 hybrid 并行：
  - MinerU 一次解析整份 PDF。
  - crop Vision 对所有裁剪块并行，默认并发上限 `60`。
  - Brain 对所有页面并行，默认并发上限 `60`。
  - 实际 worker 数取任务数和配置上限的较小值。
- Brain prompt 压缩相邻页上下文：目标页保留更多细节，相邻页只保留摘要。以 `群论笔记4.1` 现有 IR 测算，Brain prompt 字符数减少约 `25%`。
- Typora 折叠块格式固定为默认关闭：
  - `<details>`
  - `<summary>图示识别内容</summary>`
  - 空行、内容、空行
  - `</details>`
  - 不使用 `<details open>`。
- 修正 `content_inventory` 的误报：
  - 不再把全页 `before_block_ids` / `after_block_ids` 误归因到每个 block。
  - inline formula 因空白规范化造成的假 `unrendered` 已修正。
- 新增接手状态文档：`docs/maintenance/current-status.md`。
- 新增根目录接手说明：`agent.md`。
- 新增 WebUI 中期路线：`docs/plans/webui-roadmap.md`。当前 Tkinter GUI 保持轻量可用，后续推荐 FastAPI + 前端 + SSE/WebSocket。
- 加强公式输出规范：
  - 渲染器会把 paragraph/list/heading/figure note/fallback raw text 中明显的裸 Unicode 数学符号转成 LaTeX 片段。
  - `φ`、`θ`、`ω`、`α`、`β`、`≤`、`≥`、`→` 等不应裸露在最终 Markdown 中。
  - validator 新增 `unicode_math_symbol_outside_latex` warning，旧 `vision_only` Brain 输出绕过自动修复时会触发保守 PageIR fallback。
  - 覆盖率和 content inventory 会把 `φ` 与 `\phi` 等价比较，避免 LaTeX 化后产生误报。
- 改进成本估算：
  - 将 DeepSeek 官方 V3 tokenizer 资源内置到 `docpage2md_app/deepseek_v3_tokenizer/`。
  - 新增不依赖 `transformers` 的离线 DeepSeek token 计数封装，用于 GUI/artifact Brain prompt 输入估算。
  - Qwen 视觉图片 token 改为按阿里云 smart-resize 规则估算，支持 `min_pixels/max_pixels` 和高分辨率上限。
  - 本地图片按真实尺寸估算；本地 PDF/Office 在 MinerU 返回前仍标记为粗估；已有 artifact 会按真实 crop 图片和 Brain prompt 估算。
  - 实时价格表刷新加入 WebUI 后续计划，当前版本继续使用本地精选价格表。

### Verified

- `python -m pytest tests/test_cli.py tests/test_gui.py tests/test_hybrid_enrichment.py tests/test_mineru_pipeline.py tests/test_files_and_session.py tests/test_run_logger.py -q`：41 passed。
- 旧入口、旧包名、旧项目别名和旧内部函数/变量名搜索无匹配；删除记录由 Git 跟踪。
- 使用正式入口对公开 MinerU fixture 做无网络 smoke，确认 artifact adapter、IR、Markdown、assets 和 report 输出路径可用。
- 真实 GUI 全量验收输出已存在于 `markdown_output/gui_parallel_full_verify/`：
  - `群论笔记3.1`：13 页，`hybrid`，`qwen3-vl-plus` + `deepseek-v4-flash`，status `ok`。
  - `群论笔记4.1`：11 页，`hybrid`，`qwen3-vl-plus` + `deepseek-v4-flash`，status `ok`。
  - Markdown 未发现 API Key、Python traceback、`reasoning_content` 或 validator 诊断文本。

### Known Gaps

- 旧 `process.log` 不会自动重写为中文；新任务会写中文日志。
- Tkinter GUI 仍是轻量入口，复杂模型管理和历史任务更适合后续 WebUI。

## 2026-06-23

### Added

- 新增 MinerU 多格式主路径设计和实现，支持通过 MinerU artifact/API 将 PDF、Office、图片等输入转换为内部 IR。
- 新增 MinerU artifact 读取、图片 crop 复制、`assets/crops` 相对路径渲染。
- 新增 `mineru_only` / `vision_only` / `hybrid` 处理模式。
- 新增模型档位 `cheap`、`balanced`、`accurate`、`manual`，Brain 默认 `deepseek-v4-flash`，accurate 使用 `deepseek-v4-pro`。
- 新增 `hybrid_enrichment.py`，支持 crop vision enrichment、Brain JSON ops、受限 refiner、op audit，并可通过 mock backend 离线测试。
- 新增 `replace_text_span_checked` block op，用于 Brain 做局部 OCR/公式识别修正。
- 新增 `content_inventory`，记录每个 source block 是否 rendered、replaced、merged、degraded、dropped 或 unrendered。
- 新增 `run_report.json` 中的 `vision`、`brain`、`op_audit`、`content_inventory` 汇总。
- 新增架构文档：
  - `docs/architecture/hybrid-mineru-docpage2md.md`
  - `docs/architecture/model-manager.md`
  - `docs/architecture/markdown-output-contract.md`
  - `docs/architecture/mineru-api-setup.md`

### Changed

- README 定位从“图片目录转 Markdown”调整为“MinerU 多格式文档输入 -> Markdown-first 输出”，PDF 是核心输入。
- `vision_only` 被保留为旧图片目录兼容路径，不再是项目主定位。
- 图示 Markdown 输出改为 crop 图片 + 默认折叠 `<details>` 说明。
- 公式规范化要求 `\tag{}` 位于 `aligned` 环境外。
- 不再把 coverage、validator 诊断、API 错误、模型思考过程写进用户 Markdown。

### Verified

- `python -m pytest`：193 passed。
- `python -m docpage2md_app --help`：通过。
- `git diff --check`：无 whitespace error，仅有 CRLF 提示。

### Known Gaps

- `hybrid` 的默认 production backend 已接入接口形态；真实模型效果需要用本地私有手写 PDF 样本持续验证。
- 完整的第三方 provider/model registry 仍可继续扩展；当前已有 profile/role binding 基础。
