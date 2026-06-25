# DocPage2MD

DocPage2MD 把 PDF、Office、图片、HTML 或旧版页面图片目录转换成结构化 Markdown 笔记。它适合处理课堂手写笔记、论文 PDF、课件、截图题目、复杂公式和图表材料。

当前推荐入口是桌面 GUI：

```powershell
python docpage2md_gui.py
```

也可以使用命令行：

```powershell
python docpage2md.py --engine-mode hybrid --input-file ".\input_docs\我的手写笔记.pdf"
```

## 它做什么

DocPage2MD 不是简单地“看图写 Markdown”。主流程会先用 MinerU 或 PaddleOCR 解析文档版面、页面、公式、表格和图片，再把结果转换成内部结构，最后按需要用 Vision/Brain 模型精修并生成 Markdown。默认仍推荐 MinerU `vlm`；PaddleOCR 已作为可选主路径接入，适合和 MinerU 对比 OCR/layout 效果。

常见输出：

```text
markdown_output/
└── 我的文档/
    ├── Slide_01.md
    ├── Slide_02.md
    ├── 我的文档_FULL.md
    ├── run_report.json
    ├── process.log
    ├── assets/
    ├── ir/
    └── mineru_raw/ 或 paddleocr_raw/，双引擎模式会同时包含两者
```

日常阅读主要看 `Slide_XX.md` 和 `{文档名}_FULL.md`。排查问题时再看 `run_report.json`、`process.log`、`ir/` 和 `mineru_raw/` / `paddleocr_raw/`。

## 从 0 开始

### 1. 安装 Python

需要 Python 3.10 或更高版本。先在 PowerShell 里检查：

```powershell
python --version
```

如果提示找不到命令，请安装 Python，并在安装时勾选 `Add python.exe to PATH`。

### 2. 进入项目目录

```powershell
cd D:\Repos\lab-python\docpage2md
```

如果你的项目在别的位置，把路径换成自己的项目目录。

### 3. 安装依赖

```powershell
pip install -U -r requirements.txt
```

主要依赖：

- `dashscope`：调用阿里云百炼 / 通义千问。
- `rich`：终端进度和日志显示。
- `Pillow`：读取图片尺寸，用于成本估算。

DeepSeek V3 tokenizer 已内置在 `docpage2md_app/deepseek_v3_tokenizer/`，成本估算不需要额外安装 `transformers`。

### 4. 准备 API Key

如果只读取已有 MinerU/PaddleOCR artifact，可以先不配置对应平台 Token。

如果要让程序直接上传 PDF、Office、图片或 HTML 到解析平台，需要：

- MinerU：`MINERU_API_TOKEN`
- PaddleOCR：`PADDLEOCR_API_TOKEN`

如果要使用 `hybrid` 混合精修，还需要：

- DashScope / 阿里云百炼：`DASHSCOPE_API_KEY`
- DeepSeek：`DEEPSEEK_API_KEY`

最省事的方式是在 GUI 的“模型管理 / Provider 与 Key”里保存和检查 Key。GUI 会保存 Key 到本地 ignored 文件、Windows 用户环境变量，或可用时保存到 Windows Credential Manager；日志、命令预览和报告只显示 Key 名称，不显示真实值。

也可以手动设置 Windows 用户环境变量：

```powershell
[Environment]::SetEnvironmentVariable("MINERU_API_TOKEN", "你的 MinerU Token", "User")
[Environment]::SetEnvironmentVariable("PADDLEOCR_API_TOKEN", "你的 PaddleOCR Token", "User")
[Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY", "sk-你的阿里云Key", "User")
[Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-你的DeepSeekKey", "User")
```

设置后重新打开 PowerShell 更稳妥。

API Key 获取入口：

- MinerU Token：<https://mineru.net/apiManage/token>
- PaddleOCR Token：<https://aistudio.baidu.com/paddleocr/task>
- DashScope API Key：<https://help.aliyun.com/zh/model-studio/developer-reference/get-api-key>
- DeepSeek API Key：<https://platform.deepseek.com/api_keys>

### 5. 启动 GUI

```powershell
python docpage2md_gui.py
```

包入口也可以：

```powershell
python -m docpage2md_app.gui
```

推荐第一次这样跑：

1. 在“运行”页选择“本地多个文件”。
2. 点击“添加文件”，选择一个或多个 PDF。
3. 文档类型选“手写矢量笔记”。
4. 解析引擎保持默认 `MinerU`，或按需要选择 `PaddleOCR` / 双引擎融合。
5. Markdown 精修选“开启 DocPage2MD 精修”。
6. 模型档位选“均衡（推荐）”。
7. MinerU 模型保持默认 `vlm`。
8. 页码范围先填 `1-3` 做小样本测试；确认效果后留空跑全量。
9. 点击“刷新估算”，查看 Vision/Brain 费用估算。
10. 点击“开始处理”。

GUI 支持：

- 单文件、多文件、文件夹、MinerU artifact、PaddleOCR artifact、远程 URL。
- 文件列表、页数/大小/限制状态、处理顺序。
- 文档类型预设、解析引擎、Markdown 精修开关、模型档位、MinerU/PaddleOCR 模型版本。
- 高级 MinerU 参数、页码范围、输出目录、并发数。
- 成本估算、完整命令预览、中文日志、进度条、ETA、放大日志、打开输出目录。
- Provider、模型、API Key、第三方模型管理。

运行页可以垂直滚动；在窗口没有全屏时，“输出与并发”不会消失在首屏下方。成本表和命令预览支持横向滚动，命令也可以一键复制或打开完整命令窗口。

## 输入文件

文件不需要放在固定目录。你可以用 GUI 选择任意路径，也可以放进项目里的 `input_docs/`：

```text
input_docs/
├── 我的手写笔记.pdf
├── 论文.pdf
└── 课件.pptx
```

`input_docs/` 被 Git 忽略，适合放私人临时输入。

支持的主路径输入：

- PDF：`.pdf`
- 图片：`.png`、`.jpg`、`.jpeg`、`.webp`、`.bmp`、`.gif`
- Word：`.doc`、`.docx`
- PowerPoint：`.ppt`、`.pptx`
- Excel：`.xls`、`.xlsx`
- HTML：`.html`、`.htm`
- 已解压的 MinerU artifact 目录
- 已解压/下载好的 PaddleOCR artifact 目录
- 远程文件 URL

旧版 `vision_only` 还支持页面图片目录：

```text
doc_pages/
└── 我的课件/
    ├── 001.png
    ├── 002.png
    └── 003.png
```

只有旧版 `vision_only` 需要自己把 PDF/PPT 导出成图片。新主路径会直接处理原文件。

## 处理模式

| 模式 | 适合场景 | 是否调用 Vision/Brain |
| --- | --- | --- |
| `hybrid` / `mineru_hybrid` | MinerU + DocPage2MD 精修；适合手写笔记、复杂公式、图表 | 是 |
| `mineru_only` 仅 MinerU | 排版清楚的论文、电子 PDF、大批量快速转换 | 否 |
| `paddleocr_hybrid` | PaddleOCR + DocPage2MD 精修；适合和 MinerU 对比复杂 OCR/layout | 是 |
| `paddleocr_only` | 只用 PaddleOCR 解析并渲染 Markdown | 否 |
| `dual_hybrid` | MinerU + PaddleOCR 双引擎融合，再由 DocPage2MD 精修；适合复杂手写公式页做交叉核验 | 是 |
| `vision_only` 纯视觉旧流程 | 已经拆成页面图片的旧任务 | 是 |

GUI 当前主推 MinerU/PaddleOCR 解析主路径，并把选择拆成“解析引擎 + Markdown 精修”：解析引擎决定先用 MinerU、PaddleOCR 还是双引擎取版面/OCR；Markdown 精修决定是否再调用 Vision/Brain 改公式、图示、表格和结构。`vision_only` 保留在 CLI 中。

文档类型只是推荐预设，不会锁死旁边选项。你可以先选“手写矢量笔记”，再手动改解析引擎、Markdown 精修、模型档位、MinerU 模型版本或具体模型。

## MinerU 模型版本

| 版本 | 适合输入 | 建议 |
| --- | --- | --- |
| `vlm` | PDF、Office、图片 | 默认推荐，适合手写、扫描、公式、图表、复杂版面 |
| `pipeline` | PDF、Office、图片 | 适合清晰论文或电子 PDF，通常更快更稳 |
| `MinerU-HTML` | HTML/HTM | 只用于 HTML，不要用于 PDF/Office/图片 |

默认是 `vlm`。HTML/HTM 会自动使用 `MinerU-HTML`。非 HTML 文件如果选了 `MinerU-HTML`，程序会阻止运行并提示原因。

高级 MinerU 设置默认按最佳方案开启：

- `is_ocr=true`
- `enable_formula=true`
- `enable_table=true`
- `language=ch`

MinerU 不按本项目的 Vision/Brain token 费用计入成本，但有平台页数、文件大小和额度限制。PDF 超过 MinerU 单次页数限制时，GUI/CLI 会提示并自动按页码分段提交，然后合并最终 Markdown。

更多细节见 [MinerU API 配置](docs/architecture/mineru-api-setup.md)。

## PaddleOCR 主路径

PaddleOCR 已接入正式主路径，默认模型为 `PaddleOCR-VL-1.6`。可选模型包括：

- `PaddleOCR-VL-1.6`
- `PaddleOCR-VL-1.5`
- `PaddleOCR-VL`
- `PP-StructureV3`
- `PP-OCRv5`

PaddleOCR 默认使用异步接口：

```text
https://paddleocr.aistudio-app.com/api/v2/ocr/jobs
```

本地文件大小按平台文档限制为 50 MB；URL 文件按 200 MB 提示；每日按每模型 3000 页额度提示。PDF 默认按 100 页分段提交，避免超过平台建议范围后只解析前 100 页。PaddleOCR 和 MinerU 一样在成本估算里只显示平台额度/限制，不计入 Vision/Brain token 费用。

CLI 示例：

```powershell
python docpage2md.py --engine-mode paddleocr_only --layout-engine paddleocr --refine-mode none --input-file ".\input_docs\我的手写笔记.pdf"
python docpage2md.py --engine-mode paddleocr_hybrid --layout-engine paddleocr --refine-mode docpage2md --input-file ".\input_docs\我的手写笔记.pdf"
python docpage2md.py --engine-mode paddleocr_only --paddleocr-artifact-dir ".\paddleocr_artifact"
```

PaddleOCR 输出会包含 `paddleocr_raw/`、`ir/`、`assets/`、`Slide_XX.md`、`*_FULL.md` 和 `run_report.json`。更详细的 API 输出结构和后续对比计划见 [PaddleOCR 接入计划](docs/plans/paddleocr-integration-roadmap.md)。

## 双引擎融合

`dual_hybrid` 会对同一个本地文件同时调用 MinerU 和 PaddleOCR。程序先按页码对齐，再用 bbox 重叠、文本相似度、垂直位置和类型相似度构建候选组；每组只接受白名单融合操作，例如选择、合并、保留两边、标记不确定和公式替换。融合后的 `fused_document_ir.json` 会再进入 DocPage2MD 精修。它更慢、会占用两个解析平台额度，但适合手写公式、复杂 OCR 或两套解析结果差异明显的页面。

当前首版支持：

- 本地单文件、多文件、文件夹。
- 已有 artifact：同时提供 `--mineru-artifact-dir` 和 `--paddleocr-artifact-dir`。
- 输出同时保留 `mineru_raw/`、`paddleocr_raw/`、`ir/mineru_document_ir.json`、`ir/paddleocr_document_ir.json`、`ir/fused_document_ir.json` 和 `run_report.json`。
- `run_report.json` 记录候选组、融合决策、被拒绝操作和不确定项。

当前限制：

- 不直接支持远程 URL 双引擎；可先分别生成 artifact 后再融合。
- 超过 PaddleOCR 分段页数的 PDF 暂不自动做双引擎 chunk merge；先用 `--page-ranges` 分段运行。

CLI 示例：

```powershell
python docpage2md.py --engine-mode dual_hybrid --input-file ".\input_docs\我的手写笔记.pdf" --page-ranges 1-3

python docpage2md.py --engine-mode dual_hybrid `
  --mineru-artifact-dir ".\mineru_artifact" `
  --paddleocr-artifact-dir ".\paddleocr_artifact" `
  --output ".\markdown_output\dual_smoke" `
  --name "dual_smoke"
```

## 模型和 Key 管理

默认模型档位：

| 档位 | Vision | Brain |
| --- | --- | --- |
| 省钱 | `qwen3-vl-flash` | `deepseek-v4-flash` |
| 均衡（推荐） | `qwen3-vl-plus` | `deepseek-v4-flash` |
| 高精度 | `qwen3.7-plus` | `deepseek-v4-pro` |
| 自定义 | 用户手动绑定 | 用户手动绑定 |

GUI 的模型管理按两层组织：

1. Provider：管理 MinerU、PaddleOCR、DashScope、DeepSeek、OpenAI-compatible 的 Base URL、Key 名称和 Key 保存位置。
2. 角色绑定：把 Vision / Brain 分别绑定到某个 Provider 的某个模型。

第三方模型保存在 `log/third_party_models.json`，只保存模型 ID、Base URL、角色、价格和 Key 名称，不保存 Key 明文。

按钮含义：

- `检查 Key`：只检查本机能否读到 Key，不联网。
- `验证模型`：对模型发轻量 API 请求，确认模型是否可用。

模型管理设计见 [模型管理器架构](docs/architecture/model-manager.md)。

## 成本估算

成本估算只计算 Vision/Brain token 费用：

- MinerU：显示平台额度/限制，不计入人民币费用。
- PaddleOCR：显示平台额度/限制，不计入人民币费用。
- Vision/Brain：按输入 tokens、输出 tokens 和本地价格表估算。

可信度说明：

- 高：已有 MinerU artifact，可读取真实页数、crop 图片和 Brain prompt。
- 中：本地 PDF/图片，可读取页数或尺寸，但还不知道 MinerU 会切出多少 crop。
- 低：远程 URL、Office 或页数未知。

DeepSeek 输入 token 使用内置 tokenizer 离线估算。图片 token 会按模型规则和图片尺寸估算。实际费用仍以服务商账单为准，因为输出 token、思考 token、缓存、折扣和 provider 延迟都可能变化。

“刷新官方模型/价格”现在是显式功能，不会在普通处理任务里自动联网。DashScope 会抓官方模型/定价文档，DeepSeek 会读取 `/models` 并解析官方价格页，OpenAI-compatible 只发现 `/models`，价格必须用户手动填写或导入 Markdown。当前价格逻辑见 [模型管理器架构](docs/architecture/model-manager.md)。

## CLI 用法

查看帮助：

```powershell
python docpage2md.py --help
python -m docpage2md_app --help
```

处理单个 PDF：

```powershell
python docpage2md.py --engine-mode hybrid --input-file ".\input_docs\我的手写笔记.pdf" --page-ranges 1-10
```

只用 MinerU 快速转换：

```powershell
python docpage2md.py --engine-mode mineru_only --input-file ".\input_docs\论文.pdf"
```

双引擎融合一页或少量页：

```powershell
python docpage2md.py --engine-mode dual_hybrid --input-file ".\input_docs\我的手写笔记.pdf" --page-ranges 1-3
```

处理多个文件：

```powershell
python docpage2md.py --engine-mode hybrid --input-files ".\a.pdf" ".\b.pptx" ".\c.docx"
```

处理文件夹：

```powershell
python docpage2md.py --engine-mode hybrid --input-folder ".\待处理文档" --recursive
```

处理 MinerU artifact：

```powershell
python docpage2md.py --engine-mode hybrid --mineru-artifact-dir ".\tests\fixtures\mineru_public\minimal_artifact"
```

处理远程 URL：

```powershell
python docpage2md.py --engine-mode mineru_only --mineru-url "https://example.com/paper.pdf"
```

覆盖模型：

```powershell
python docpage2md.py --engine-mode hybrid --input-file ".\notes.pdf" `
  --vision-provider dashscope_openai `
  --vision-model qwen3-vl-plus `
  --vision-base-url "https://dashscope.aliyuncs.com/compatible-mode/v1" `
  --vision-api-key-env DASHSCOPE_API_KEY `
  --brain-provider deepseek `
  --brain-model deepseek-v4-flash `
  --brain-base-url "https://api.deepseek.com" `
  --brain-api-key-env DEEPSEEK_API_KEY
```

MinerU 高级参数：

```powershell
python docpage2md.py --engine-mode hybrid --input-file ".\notes.pdf" `
  --mineru-model-version vlm `
  --mineru-is-ocr true `
  --mineru-enable-formula true `
  --mineru-enable-table true `
  --mineru-language ch `
  --auto-split-pages
```

模型目录命令：

```powershell
python docpage2md.py --list-models
python docpage2md.py --refresh-models --refresh-prices --providers dashscope,deepseek --show-model-diff
python docpage2md.py --refresh-models --providers openai-compatible --base-url "https://example.com/v1"
python docpage2md.py --refresh-prices --import-pricing-md ".\docs\reference-pricing\价格.md" --show-model-diff
python docpage2md.py --verify-models --verify-limit 20
python docpage2md.py --list-all-models
```

## 并行和速度

`hybrid` 是真实并行：

1. MinerU 解析一个 PDF 后会一次返回整份文档的页面、layout 和 crop。
2. crop Vision 阶段会把所有可识别裁剪块放进线程池，默认并发 `60`。
3. Brain 阶段会把所有页面放进线程池，默认并发 `60`。
4. 实际 worker 数为 `min(任务数, 配置并发数)`。

如果某次任务慢，通常瓶颈在 provider 响应、复杂页面长尾、API 限流或重试，不是页面被强制串行。每个输出目录的 `process.log` 会用中文记录各阶段耗时。

## 日志、缓存和安全

常见本地文件：

```text
markdown_output/     # 输出，不进 Git
log/                 # 日志、模型设置、第三方模型 registry，不进 Git
.cache/              # 模型目录缓存，不进 Git
.env.local.json      # GUI 本地 Key 保存文件，不进 Git
input_docs/          # 可选私人输入，不进 Git
```

安全约束：

- 不要提交私人 PDF、Office 文件或输出目录。
- 不要把 API Key 写进 README、代码、测试或文档。
- `run_report.json`、日志和命令预览只记录环境变量名，不记录真实 Key。
- 不要删除 `markdown_output/已归档`；这是保留的废弃输出目录。

Markdown 输出不应包含：

- API Key
- Python 堆栈
- provider 原始错误
- validator 诊断文本
- 模型思考过程或 `reasoning_content`

Markdown 输出契约见 [Markdown 输出契约](docs/architecture/markdown-output-contract.md)。

## 故障排查

### GUI 启动不了

先确认依赖已安装：

```powershell
pip install -U -r requirements.txt
python docpage2md_gui.py
```

### 未检测到 API Key

GUI 里点击“检查 Key”。命令行可检查：

```powershell
echo $env:MINERU_API_TOKEN
echo $env:DASHSCOPE_API_KEY
echo $env:DEEPSEEK_API_KEY
```

如果刚用 `[Environment]::SetEnvironmentVariable(...)` 设置过，请重新打开 PowerShell。

### 先小范围试跑

第一次不要直接跑几百页，先用页码范围：

```powershell
python docpage2md.py --engine-mode hybrid --input-file ".\input_docs\我的手写笔记.pdf" --page-ranges 1-3
```

确认输出质量、成本和速度后，再留空页码范围跑全量。

### 中断后能不能重跑

可以。程序会尽量复用已有中间结果和缓存。对于 MinerU/hybrid 输出，优先查看输出目录下的 `process.log` 和 `run_report.json`。

### 为什么最终还有 Markdown，但日志里有失败

程序采用 fail-open 策略：某些识别或精修失败时，会尽量用已有结构化结果保守渲染 Markdown，避免完全没有输出。质量排查请看 `run_report.json`。

## 开发与验证

常用回归命令：

```powershell
python docpage2md.py --help
python -m docpage2md_app --help
python -m pytest -q
git diff --check
```

离线 smoke：

```powershell
python docpage2md.py --engine-mode mineru_only `
  --mineru-artifact-dir ".\tests\fixtures\mineru_public\minimal_artifact" `
  --output ".\markdown_output\smoke" `
  --name "public_mineru_fixture"
```

## 文档

- [当前状态](docs/maintenance/current-status.md)
- [Changelog](docs/changelog.md)
- [文档到 Markdown 管线](docs/architecture/docpage-to-markdown-pipeline.md)
- [Hybrid MinerU + DocPage2MD 架构](docs/architecture/hybrid-mineru-docpage2md.md)
- [MinerU API 配置](docs/architecture/mineru-api-setup.md)
- [模型管理器架构](docs/architecture/model-manager.md)
- [Markdown 输出契约](docs/architecture/markdown-output-contract.md)
- [WebUI 路线图](docs/plans/webui-roadmap.md)
- [PaddleOCR 接入计划](docs/plans/paddleocr-integration-roadmap.md)

## 许可证

MIT License，详见 [LICENSE](LICENSE)。
