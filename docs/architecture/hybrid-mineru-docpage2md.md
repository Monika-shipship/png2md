# Hybrid MinerU + docpage2md 架构

## 目标

`hybrid` 是 docpage2md 的新主路径，目标是直接处理 PDF、图片、Doc/Docx、Ppt/PPTx、Xls/Xlsx 等多格式文档，尤其是手写矢量笔记 PDF。

核心分工：

- MinerU：负责多格式解析、layout、bbox、图表定位和 crop。
- docpage2md Vision：负责整页或 crop 精读，补强文字、公式、图表内容。
- Brain：结合前后页窗口修正文公式和明显 OCR 错误。
- Refiner：用有限 op 做局部修复，失败时 fail-open。
- Renderer：最终输出干净 Markdown。

## 流程

```text
单文件 / 远程 URL / 文件夹 / 多文件批处理
-> 选择 mineru_only / vision_only / hybrid
-> MinerU precise API, model_version=vlm
   - 本地单文件和多文件：/api/v4/file-urls/batch
   - 远程 URL：/api/v4/extract/task
-> 下载/读取 artifact: full.md, layout.json, content_list*.json, model.json, images/
-> MinerU adapter 转 DocumentIR/PageIR/BlockIR
-> assets/crops 复制 crop，Markdown 使用相对路径
-> hybrid_enrichment 并行读取所有 crop，补充 figure/table/formula block
-> Brain 并行处理所有页面，输出 JSON ops，用默认 deepseek-v4-flash，复杂模式 deepseek-v4-pro
-> apply_block_op_checked 执行受限 op，再跑 checked refiner
-> validator + content_inventory + run_report
-> Slide_XX.md + FULL.md
```

当前实现入口是 `docpage2md_app/hybrid_enrichment.py`。它是可离线测试的薄层：

- `vision_backend(page_ir, block, image_path, config)`：读取 MinerU crop，返回图示说明、公式 LaTeX 或表格文本。
- `brain_backend(page_ir, context_pages, config)`：读取当前页和前后页摘要，只返回 JSON ops。
- 生产默认 backend 会读取 `DASHSCOPE_API_KEY` / `DEEPSEEK_API_KEY`；没有 key 时快速 fail-open，不把错误写进 Markdown。
- 测试可以注入 mock backend，不需要真实 API。

## 并行和速度

`hybrid` 对单个 PDF 的处理是阶段式并行：

1. MinerU 先一次性解析整份 PDF，返回所有页面、layout、json 和 crop。
2. crop Vision 阶段把所有可精读的 crop block 放进同一个线程池，默认并发上限 `60`。
3. Brain 阶段等 crop Vision 完成后，把所有页面放进同一个线程池，默认并发上限 `60`。
4. 实际 worker 数取 `min(job_count, configured_workers)`，所以 `49` 个 crop 会用 `49` 个 worker，`11` 页 Brain 会用 `11` 个 worker。

阶段之间不交错，是为了让 Brain 看到完整的当前页和前后页上下文；阶段内部不是串行。

运行日志会写入阶段耗时汇总：

```text
开始并行识别裁剪块：裁剪块=49，并发=49
裁剪块并行识别完成：总数=49，成功=49，失败=0，耗时=27.2秒
开始并行 Brain 精修：页数=11，并发=11
Brain 并行精修完成：页数=11，状态=正常:9；部分完成:2，耗时=75.0秒
Markdown 渲染完成：页数=11，耗时=0.1秒
```

`tests\群论笔记4.1.pdf` 的一次完整 `hybrid + balanced` 日志显示，总耗时约 `108.4s`，其中 MinerU 约 `6.1s`，crop Vision 约 `27.2s`，Brain 约 `75.0s`。瓶颈是 Brain provider 延迟和长尾页面复杂度，不是缺少页级并行。

Brain prompt 已做上下文压缩：目标页保留更多 raw text 和 block 细节，相邻页只保留摘要。以 `群论笔记4.1` 的已有 IR 测算，Brain prompt 字符数从约 `147,652` 降到约 `110,388`，减少约 `25%`。这能降低 token 和延迟，但最终速度仍取决于 provider 响应。

## 三种模式

- `mineru_only`：只使用 MinerU artifact/API，适合论文 PDF、排版规整材料、低成本快速转 Markdown。
- `vision_only`：旧版图片目录流程，适合截图/屏拍小题或 MinerU 定位效果不好的单页图片。
- `hybrid`：默认主力模式，适合手写笔记、复杂公式图表 PPT、需要 crop 证据和 Brain 纠错的材料。

## 输入入口

- `--input-file`：通过 MinerU 精准 API 处理单个本地 PDF、Office、图片或 HTML 文件。
- `--input-files`：通过 MinerU batch 上传接口处理多个本地文件。
- `--input-folder`：扫描一个文件夹里的支持格式文件；配合 `--recursive` 递归扫描子目录。
- `--mineru-url`：通过 MinerU URL 任务处理远程文件。
- `--mineru-artifact-dir`：读取已经解压好的 MinerU 客户端/API 输出目录，适合离线调试和回归测试。

## Markdown 输出契约

最终 Markdown 必须干净：

- 不写模型思考过程。
- 不写 API 错误堆栈。
- 不写覆盖率解释。
- 不写 validator 诊断。
- 失败或不确定详情进入 `run_report.json`。
- 内容库存检查进入 `run_report.json` 的 `content_inventory`，用于说明每个 source block 是 rendered、merged、replaced、degraded、dropped 还是 unrendered；不会把这些诊断写进正文 Markdown。

`run_report.json` 在 hybrid 模式下额外记录：

- `vision`：每页 crop vision 的尝试 block 数、成功/失败数、usage、request id。
- `brain`：每页 Brain 请求的 op 数、应用/拒绝数、usage、request id。
- `op_audit`：Brain ops 和 block refiner ops 的统一审计记录。
- `hybrid_enrichment`：本轮 enrichment 版本和汇总计数。

模型的 `reasoning_content`、API 错误详情、validator 诊断只允许进入 report 的安全摘要字段，绝不写入 `Slide_XX.md` 或 FULL Markdown。

图示输出固定为：

```markdown
![page 1 figure 3](assets/crops/page_001_p0001_b003_xxx.jpg)

<details>
<summary>图示识别内容</summary>

- 类型：coordinate_plot
- 说明：...
- 可见标签：...
- 主要关系：...
- 不确定点：...

</details>
```

## 密钥

代码只读取环境变量名，不持久化真实密钥：

- `MINERU_API_TOKEN`
- `DASHSCOPE_API_KEY`
- `DEEPSEEK_API_KEY`

`run_report.json` 只记录 provider、model、base_url 和 env var 名，不记录密钥值。
