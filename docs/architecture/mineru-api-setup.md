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

## 支持格式

按 MinerU 能力，当前入口接受：

- PDF
- PNG/JPG/JPEG/WebP/GIF/BMP/JP2
- Doc/Docx
- PPT/PPTX
- Xls/Xlsx
- HTML/HTM

HTML 可显式使用 `--mineru-model-version MinerU-HTML`。

## 安全审计

`run_report.json` 只记录：

- provider: `mineru`
- model_version
- base_url
- api_key_env: `MINERU_API_TOKEN`
- task_id / batch_id
- artifact manifest

不得记录真实 token。
