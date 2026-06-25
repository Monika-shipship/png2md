# MinerU API 配置

## 用途

MinerU 是新主路径的 layout 引擎，负责多格式解析、bbox、图表定位和 crop。`hybrid` 模式固定优先使用 MinerU 精准解析 API，默认：

```text
model_version=vlm
enable_formula=true
enable_table=true
language=ch
is_ocr=true
```

这些默认值现在也可以通过 CLI/GUI 非交互覆盖：

```powershell
python docpage2md.py --engine-mode hybrid --input-file ".\notes.pdf" `
  --mineru-model-version vlm `
  --mineru-is-ocr true `
  --mineru-enable-formula true `
  --mineru-enable-table true `
  --mineru-language ch
```

GUI 默认隐藏“高级 MinerU 设置”，但实际运行命令会显式传递这些参数，避免 GUI 子进程进入交互式配置。

## 获取 token

在 MinerU 控制台获取 token：

<https://mineru.net/apiManage/token>

不要把 token 写进仓库、README、测试 fixture、缓存或 report。程序只读取环境变量名：

```text
MINERU_API_TOKEN
```

## Windows PowerShell 永久配置

```powershell
[Environment]::SetEnvironmentVariable("MINERU_API_TOKEN", "你的 MinerU Token", "User")
```

重新打开 PowerShell 后验证：

```powershell
[Environment]::GetEnvironmentVariable("MINERU_API_TOKEN", "User") -ne $null
```

不要在公共终端、截图、提交记录里打印真实 token。

## CMD 永久配置

```cmd
setx MINERU_API_TOKEN "你的 MinerU Token"
```

## Linux / macOS 临时配置

```bash
export MINERU_API_TOKEN="你的 MinerU Token"
```

## 本地文件解析

文件不需要放在固定目录。可以直接传绝对路径，也可以放到项目根目录的 `input_docs/`。`input_docs/` 是本地私人输入目录，已被 Git 忽略。

单文件：

```powershell
python docpage2md.py --engine-mode hybrid --input-file ".\input_docs\我的手写笔记.pdf" --page-ranges 1-3
```

推荐给个人 PDF 使用：

```powershell
python docpage2md.py --engine-mode hybrid --input-file ".\input_docs\我的手写笔记.pdf" --page-ranges 1-10
python docpage2md.py --engine-mode hybrid --input-file "D:\Notes\我的手写笔记.pdf" --page-ranges 1-10
```

多文件：

```powershell
python docpage2md.py --engine-mode mineru_only --input-files ".\a.pdf" ".\b.pptx"
```

文件夹：

```powershell
python docpage2md.py --engine-mode hybrid --input-folder ".\待处理文档" --recursive
```

程序会按支持后缀筛选 PDF、Office、图片和 HTML 文件。日常手动选择文件可启动轻量 GUI：

```powershell
python docpage2md_gui.py
```

也可以从 Windows 资源管理器复制文件路径，再粘贴到 CLI 的 `--input-file` 后面。

远程 URL：

```powershell
python docpage2md.py --engine-mode mineru_only --mineru-url "https://example.com/paper.pdf"
```

## 已下载 artifact

如果已经有 MinerU 客户端或 API 解压目录，可以不需要 token，直接跑：

```powershell
python docpage2md.py --engine-mode hybrid --mineru-artifact-dir ".\tests\fixtures\mineru_public\minimal_artifact"
```

这种路径适合离线调试和回归测试。

## MinerU 模型版本怎么选

`--mineru-model-version` 对应 MinerU 精准解析 API 的 `model_version`，不是 DocPage2MD 自己的 Vision/Brain 模型。GUI 里的“MinerU 模型”也是这个参数。

| 选项 | 适用输入 | 特点 | 建议场景 |
| --- | --- | --- | --- |
| `vlm` | PDF、Office、图片 | VLM 路线，官方文档标为推荐；通常更适合复杂版面、公式、图表、手写/扫描类内容。 | 默认建议；手写矢量笔记、复杂公式 PDF、扫描或屏拍文档优先选它。 |
| `pipeline` | PDF、Office、图片 | 传统多模块 pipeline，速度和稳定性较好，幻觉风险低，适合清晰版面。 | 排版清楚的论文、电子 PDF、大批量快速处理，或想先低成本快速跑一遍时使用。 |
| `MinerU-HTML` | HTML/HTM | 专门处理 HTML 主体内容抽取，过滤导航、广告、元数据等网页噪声。 | 只有解析 HTML 文件或网页导出的 HTML 时使用；不要用于 PDF。 |

注意事项：

- HTML 文件必须使用 `MinerU-HTML`。GUI 会对 `.html/.htm` 自动切换。
- 非 HTML 文件只应在 `pipeline` 和 `vlm` 之间选择；如果选择 `MinerU-HTML`，GUI/CLI 会阻止运行。
- HTML/HTM 不应和 PDF/Office/图片混在同一批提交，因为 `MinerU-HTML` 是独立解析流程。
- `is_ocr`、`enable_formula`、`enable_table`、`language` 这些 MinerU 参数只对 `pipeline` / `vlm` 有效。
- MinerU 文档特别说明：对 `vlm` 来说，`enable_formula` 只影响行内公式解析。
- DocPage2MD 当前默认使用 `vlm`，因为项目主场景是手写/半手写笔记和复杂公式 PDF。

推荐决策：

- 不确定且输入是 PDF/Office/图片：先选 `vlm`。
- 清晰论文 PDF 且追求速度：试 `pipeline`。
- HTML/HTM：选 `MinerU-HTML`。

## 支持格式

按 MinerU 能力，当前入口接受：

- PDF
- PNG/JPG/JPEG/WebP/GIF/BMP/JP2
- Doc/Docx
- PPT/PPTX
- Xls/Xlsx
- HTML/HTM

HTML 应显式使用 `--mineru-model-version MinerU-HTML`。

## 单次页数限制和自动分段

GUI 会按本地 PDF 页数提示 MinerU 单次页数限制风险。默认按 200 页作为单次阈值：

- 本地 PDF 页数可识别且超过阈值：自动规划 `1-200`、`201-400`、`401-401` 这类 page ranges。
- 每个 chunk 单独提交 MinerU。
- 每段先写入独立 chunk 输出目录，例如 `{doc_name}__chunk_002`。
- 最终合并到 `{doc_name}` 输出目录，生成统一的 `Slide_XX.md`、`{doc_name}_FULL.md` 和 `run_report.json`。
- `run_report.json` 的 `mineru.chunks` / `mineru.chunked_merge` 记录 chunk 页码、task_id、batch_id、输出目录和合并状态。

CLI 参数：

```powershell
python docpage2md.py --engine-mode hybrid --input-file ".\big.pdf" `
  --auto-split-pages `
  --mineru-page-chunk-size 200
```

远程 URL、Office 或页数未知文件不会盲目拆分；运行前只提示风险，失败后按平台错误码排查。

## 安全审计

`run_report.json` 只记录：

- provider: `mineru`
- model_version
- base_url
- api_key_env: `MINERU_API_TOKEN`
- task_id / batch_id
- artifact manifest

不得记录真实 token。
