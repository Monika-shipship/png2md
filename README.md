# PPT2MD-V10

把一组 PPT 截图、扫描页、论文图片批量转换成结构化 Markdown 笔记。

它不是读取 `.pptx` 文件，而是读取图片目录，例如：

```text
ppt_images/
└── 我的课件/
    ├── slide_01.png
    ├── slide_02.png
    └── ...
```

然后输出：

```text
markdown_output/
└── 我的课件/
    ├── Slide_01.md
    ├── Slide_02.md
    ├── temp_raw_vision/
    └── 我的课件_FULL.md
```

## 从 0 开始

### 1. 安装 Python

如果你完全不熟悉电脑，先确认电脑里有没有 Python：

```powershell
python --version
```

如果提示找不到命令，请安装 Python 3.10 或更高版本。Windows 用户可以从 Python 官网下载安装包，安装时勾选 `Add python.exe to PATH`。

### 2. 进入项目目录

打开 PowerShell，进入本项目目录：

```powershell
cd C:\Projects\png2md
```

如果你的项目放在其他位置，请把上面的路径替换成你自己的项目文件夹路径。

### 3. 安装依赖

```powershell
pip install -U -r requirements.txt
```

如果网络慢，可以多试一次。依赖主要是：

- `dashscope`：调用阿里云百炼 / 通义千问
- `rich`：终端 UI
- `Pillow`：读取图片尺寸，用于成本估算

### 4. 设置 API Key

默认配置使用阿里云 DashScope 做 Step 1 视觉识别，所以新手建议先准备一个 `DASHSCOPE_API_KEY`。

临时设置，只对当前 PowerShell 窗口有效：

```powershell
$env:DASHSCOPE_API_KEY="sk-你的阿里云Key"
```

长期设置，推荐：

```powershell
[Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY", "sk-你的阿里云Key", "User")
```

如果 Step 2 选择 DeepSeek，还需要 `DEEPSEEK_API_KEY`：

```powershell
[Environment]::SetEnvironmentVariable("DEEPSEEK_API_KEY", "sk-你的DeepSeekKey", "User")
```

设置后重新打开 PowerShell 更稳妥。

如果你使用 One API、OpenRouter、LiteLLM、自建转发等 OpenAI 兼容服务，也可以先不手动设置。运行程序后在模型选择界面输入 `c`，选择 `openai_compatible`，程序会提示你填写 Base URL、模型 ID、环境变量名，并可把 Key 保存到当前 Windows 用户环境变量。

本项目不会把 API Key 写入仓库文件。模型设置只保存环境变量名，例如 `DASHSCOPE_API_KEY`，不会保存密钥值。

### 5. 准备图片

在 `ppt_images` 下新建一个文件夹，文件夹名就是任务名：

```text
ppt_images/
└── 3.2点群/
    ├── 001.png
    ├── 002.png
    └── 003.png
```

支持的图片格式：

- `.png`
- `.jpg`
- `.jpeg`
- `.bmp`
- `.webp`

文件名建议带数字，程序会自然排序。

建议使用 PDF-XChange Editor 导出 PDF 文件的图片，这样会自带数字排序。

### 6. 启动

```powershell
python ppt2md.py
```

如果需要指定会话名和输出目录：

```powershell
python ppt2md.py -n my_session -o .\markdown_output
```

程序会先检查 `ppt_images` 是否存在，再让你选择模型，最后选择要处理的图片文件夹和页码范围。

## 使用流程

启动后大致会经历这些步骤：

1. 加载模型目录
2. 选择 Step 1 视觉模型
3. 选择 Step 2 Brain 模型
4. 扫描 `ppt_images`
5. 选择 PPT 图片文件夹
6. 选择页码范围
7. 显示成本预估
8. 确认开始
9. 生成单页 Markdown 和汇总 Markdown

页码范围支持：

```text
回车 / all    全部
1-10          第 1 到 10 页
50-end        第 50 页到最后
8             只处理第 8 页
```

## 两阶段架构

### Step 1: 视觉提取

对每张图片做 OCR、公式识别、图形结构描述，输出 Raw Data。

默认模型：

```text
dashscope:qwen3-vl-plus
```

也可以选择 Qwen3.7-Plus、Qwen3.6-Flash、Qwen3.5-Flash 等视觉模型，或配置自定义 OpenAI-compatible 视觉 API。

### Step 2: Brain 重组

使用前后各 2 页 Raw Data，也就是 5 页滑动窗口，把当前页整理成 Markdown。

推荐模型：

```text
deepseek:deepseek-v4-flash
```

它便宜、上下文长，适合做 Markdown 清洗、公式修正、跨页上下文判断。

## 并行是否真实

当前程序是真实并行，但要注意它是“两阶段并行”，不是两个阶段同时交错跑。

具体是：

1. Step 1 对同一个 PPT 的所有目标图片用 `ThreadPoolExecutor` 并发调用视觉模型。
2. 等 Step 1 全部完成或命中缓存后，Step 2 再对所有目标页并发调用 Brain 模型。
3. 多个 PPT 文件夹之间还可以用进程池并行，但默认 `MAX_PPT_WORKERS = 1`，避免同时处理多个大任务导致 API 限流。

这样设计是为了让 Step 2 能看到完整的前后页 Raw Data。

## ETA 是否准确

终端里的剩余时间来自 Rich 进度条，它根据当前完成速度估算。

它不是 API 级精确预测，因为：

- 每页图片大小不同
- 模型响应时间波动很大
- API 可能限流或重试
- 有些页面命中缓存会瞬间完成
- 输出长度不可提前准确知道

所以 ETA 只能作为粗略参考。真实耗时会写入日志，例如：

```text
Step 1 完成，耗时 62.4s，缓存 3，提交 20，失败 0
Step 2 完成，耗时 41.8s，跳过 0，提交 23，失败 0
全部流程结束，总耗时 105.2s
```

## 日志和缓存

日志文件：

```text
log/log_default_YYYYMMDD_HHMMSS.log
```

会话文件：

```text
log/sessions/session_default.json
```

模型偏好：

```text
log/model_settings.json
```

模型目录缓存：

```text
.cache/aliyun_model_catalog.json
```

中间视觉缓存：

```text
markdown_output/任务名/temp_raw_vision/Raw_01.json
```

如果任务中断，直接重新运行。程序会跳过已有的 Raw Data 和已有的 `Slide_XX.md`。

## 模型选择

交互 UI 默认只展示精选主力模型，避免把阿里云文档里抓到的大量旧版、快照、弃用候选都显示出来。

常用选择：

| 阶段 | 便宜 | 平衡 | 强力 |
| --- | --- | --- | --- |
| Step 1 视觉 | qwen3.5-flash / qwen3.5-27b / qwen3-vl-flash | qwen3-vl-plus / qwen3.6-flash / qwen3.7-plus | qwen3.7-max-2026-06-08 / qwen3.7-max / kimi-k2.6 |
| Step 2 Brain | deepseek-v4-flash | deepseek-v4-pro / qwen3.7-plus | qwen3.7-max / kimi-k2.6 |

当前精选 Vision 目录包含：

```text
qwen3-vl-plus
qwen3-vl-flash-2026-01-22
qwen3.7-plus
qwen3.7-plus-2026-05-26
qwen3.7-max
qwen3.7-max-2026-06-08
qwen3.6-plus
qwen3.6-plus-2026-04-02
qwen3.6-flash
qwen3.6-27b
qwen3.5-plus
qwen3.5-plus-2026-04-20
qwen3.5-flash
qwen3.5-27b
kimi-k2.6
```

模型目录命令：

```powershell
# 查看精选模型
python ppt2md.py --list-models

# 从阿里云文档抓取完整候选目录
python ppt2md.py --refresh-models

# 用 API 探针验证模型能力
python ppt2md.py --verify-models --verify-limit 20

# 查看完整缓存目录，仅用于诊断
python ppt2md.py --list-all-models
```

说明：

- DeepSeek 价格可以从官方文档页尽力刷新。
- 阿里云百炼控制台页面是前端渲染页面，不是稳定公开 JSON API，所以 Qwen 价格主要采用本地维护的精选价格表。
- Kimi-K2.6 按 DashScope OpenAI 兼容路径调用，价格采用模型卡中的 `6.5/27 元/百万 tokens`。
- 新模型可以用“自定义模型”录入。

## 自定义 API

在模型选择时输入 `c` 可以配置自定义模型。

支持的 API 类型：

```text
dashscope          阿里云 DashScope 原生接口
dashscope_openai   阿里云 OpenAI 兼容接口
deepseek           DeepSeek OpenAI 兼容接口
openai_compatible  其他 OpenAI 兼容接口
```

自定义 OpenAI-compatible API 需要填写：

```text
Base URL
API Key 环境变量名
模型 ID
输入价格 元/百万 tokens
输出价格 元/百万 tokens
```

示例：OpenRouter

```text
Provider: openai_compatible
Base URL: https://openrouter.ai/api/v1
API Key 环境变量名: OPENROUTER_API_KEY
模型 ID: qwen/qwen3-vl-32b-instruct
```

然后设置环境变量：

```powershell
[Environment]::SetEnvironmentVariable("OPENROUTER_API_KEY", "你的Key", "User")
```

程序也可以在交互过程中帮你把 key 写入当前用户环境变量，但不会写入仓库文件。

## 成本估算

成本估算现在按每张图片逐页计算，不再只抽样前几张。

它考虑了：

- 每张图片的尺寸不同
- Qwen3-VL 的图像 token 估算
- 输入 token 和输出 token 单价不同
- 本地价格表中的阶梯计费：按输入 token 所在区间选择输入价和输出价
- 自定义模型价格

仍然只能近似，因为：

- 输出 token 数在调用前未知
- 思考 token 数在调用前未知
- 服务商活动折扣、缓存命中、Batch 价格可能变化
- 阿里云控制台价格页不是稳定公开 API

成本表中的 `图片Token均值/范围` 可以帮你判断图片是否过大。如果图片 token 很高，通常说明分辨率很高，成本和耗时都会上升。

## 推荐工作流

### 低成本批处理

```text
Vision: qwen3.5-flash、qwen3.5-27b 或 qwen3-vl-flash
Brain: deepseek-v4-flash
```

适合清晰教材页、普通 PPT。

### 质量优先

```text
Vision: qwen3.7-plus、qwen3.6-flash 或 qwen3-vl-plus
Brain: deepseek-v4-pro
```

适合公式较多、图表较复杂的材料。

### 疑难页兜底

```text
Vision: qwen3.7-max-2026-06-08、qwen3.7-max 或 kimi-k2.6
Brain: deepseek-v4-pro、qwen3.7-max 或 kimi-k2.6
```

只建议少量页使用，成本明显更高。

## 常见问题

### 未检测到 API Key

先看报错里提示的是哪个环境变量。默认阿里云是：

```powershell
echo $env:DASHSCOPE_API_KEY
```

DeepSeek 是：

```powershell
echo $env:DEEPSEEK_API_KEY
```

其他自定义服务则检查你在模型选择里填写的环境变量名。如果为空，重新设置，例如：

```powershell
[Environment]::SetEnvironmentVariable("DASHSCOPE_API_KEY", "sk-你的Key", "User")
```

重新打开 PowerShell 后再运行。

### 输出目录里已经有文件，会不会重复扣费

程序会跳过：

- 已存在的 `temp_raw_vision/Raw_XX.json`
- 已存在且大小超过 100 字节的 `Slide_XX.md`

所以中断后可以直接重跑。

### 为什么 Step 2 要等 Step 1 全部完成

因为 Step 2 需要前后各 2 页 Raw Data。如果边识别边重组，后文窗口可能不完整，会降低符号一致性和上下文判断质量。

### 能不能直接处理 PPTX

当前不能。请先把 PPT 导出为图片，再放入 `ppt_images/任务名/`。

### 为什么日志里显示失败，但最终还有 Markdown

如果某页视觉失败，程序会把该页 Raw Data 标为 `[Vision Failed]`，Step 2 仍会继续尝试生成。请优先查看日志和对应 `Slide_XX.md`。

## 公开发布前检查

如果你准备把仓库公开到 GitHub，请先确认不要提交以下内容：

- API Key、`.env`、任何包含密钥的本地配置文件
- `ppt_images/` 里的原始课件、截图、论文图片
- `markdown_output/`、`markdown_output_*/` 里的生成笔记
- `log/`、`log/sessions/`、`.cache/`、`session_*.json`
- 临时 Raw Data，例如 `Raw_01.json`
- 私人路径、邮箱、学校/公司内部材料、未授权课件内容

本仓库的 `.gitignore` 已默认忽略这些常见本地文件，但公开前仍建议运行：

```powershell
git status --short
git ls-files
git grep -n -I -E "sk-[A-Za-z0-9_-]{16,}|C:\\Users|D:\\Repos|Administrator|@"
```

如果这些内容曾经被提交过，只从当前文件里删除还不够，Git 历史里仍然可能保留。公开前应重新创建一个干净仓库，或使用 `git filter-repo` / BFG 清理历史；已经暴露过的 API Key 应在服务商控制台吊销并重新生成。

另外，项目目前没有附带开源许可证。公开 GitHub 仓库前建议根据你的意愿添加 `LICENSE`，例如 MIT、Apache-2.0 或其他许可证。

## 目录结构

```text
ProjectRoot/
├── ppt2md.py
├── ppt2md_app/
│   ├── aliyun_catalog.py
│   ├── cli.py
│   ├── config.py
│   ├── cost.py
│   ├── env.py
│   ├── files.py
│   ├── model_catalog.py
│   ├── model_settings.py
│   ├── models.py
│   ├── pipeline.py
│   ├── prompts.py
│   └── session.py
├── ppt_images/
├── markdown_output/
├── log/
├── .cache/
└── requirements.txt
```

## 费用声明

本工具会调用阿里云 DashScope、DeepSeek 或你配置的第三方 API。运行会产生 token 费用。任务开始前请认真查看成本预估，实际账单以服务商为准。
