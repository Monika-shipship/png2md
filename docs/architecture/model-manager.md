# 模型管理器架构

## 目标

模型管理器的目标是把不同阶段用到的模型从硬编码中解耦出来，让用户可以按角色、档位和第三方 API 灵活切换。

当前固定角色：

- `layout_engine`：MinerU 精准解析 API，默认 `vlm`。
- `page_vision`：整页视觉识别。
- `crop_vision`：图、表、公式 crop 精读。
- `ocr_helper`：可选 OCR 专用模型。
- `brain`：前后页上下文纠错。
- `refiner`：局部 suspect 裁决。
- `reviewer`：可选内容正确性审查。

## 默认档位

`cheap`：

- `layout_engine`: MinerU `vlm`
- `page_vision`: `qwen3-vl-flash`
- `crop_vision`: `qwen3-vl-flash`
- `ocr_helper`: `qwen-vl-ocr-latest`
- `brain`: `deepseek-v4-flash`
- `refiner`: `deepseek-v4-flash`

`balanced`：

- `layout_engine`: MinerU `vlm`
- `page_vision`: `qwen3-vl-plus`
- `crop_vision`: `qwen3-vl-plus`
- `ocr_helper`: `qwen-vl-ocr-latest`
- `brain`: `deepseek-v4-flash`
- `refiner`: `deepseek-v4-flash`

`accurate`：

- `layout_engine`: MinerU `vlm`
- `page_vision`: `qwen3.7-plus`
- `crop_vision`: `qwen3.7-plus`
- `ocr_helper`: `qwen-vl-ocr-latest`
- `brain`: `deepseek-v4-pro`
- `refiner`: `deepseek-v4-pro`

`manual`：

- 用户逐个 role 选择 provider、model、base_url、api_key_env。
- 支持 OpenAI-compatible 第三方 API。
- 支持把视觉、Brain、refiner 全部切到第三方服务。
- GUI 启动任务时会把当前 Vision/Brain 选择写成 CLI 覆盖参数，避免子进程进入终端 `input()`。

## 数据结构

当前实现入口是 `docpage2md_app/model_profiles.py`，核心数据结构是 `RoleBinding`：

```text
role
provider
model
base_url
api_key_env
thinking_enabled
json_mode
supports_vision
note
```

后续如需扩展完整 registry，可增加：

```text
Provider
  name
  api_style
  base_url
  api_key_env
  supports_vision
  supports_json
  supports_thinking
  supports_tools

Model
  id
  provider
  roles
  context_window
  max_output
  price_ref
  quality_tier
  supports_images
  supports_reasoning_content
```

## 非交互覆盖参数

GUI 和自动化脚本可以用显式参数覆盖档位默认模型：

```powershell
python docpage2md.py --engine-mode hybrid --model-profile manual `
  --vision-provider openai_compatible `
  --vision-model "vendor/vision-model" `
  --vision-base-url "https://example.com/v1" `
  --vision-api-key-env "VENDOR_API_KEY" `
  --brain-provider deepseek `
  --brain-model "deepseek-v4-flash" `
  --brain-base-url "https://api.deepseek.com" `
  --brain-api-key-env "DEEPSEEK_API_KEY" `
  --input-file ".\input_docs\notes.pdf"
```

构造顺序是：先应用 `--model-profile`，再应用这些显式覆盖。这样 `cheap / balanced / accurate` 可以被局部覆盖，`manual` 也能完整构造 `AppConfig`。

## GUI 模型管理

当前 Tkinter GUI 的模型页按“先 Provider，再绑定角色”的结构组织：

- “Provider 与 Key”页：MinerU、PaddleOCR、DashScope、DeepSeek、OpenAI-compatible 的 Base URL、Key 名称、Key 保存位置和获取 Key 链接。
- “角色绑定”页：当前生效 Vision / Brain 模型编辑、Key 状态、价格摘要、按档位重置、保存为默认。
- “候选模型”页：官方模型和第三方模型合并展示，候选来自 `load_model_catalog()` 与 `log/third_party_models.json`，支持按模型/provider/env 筛选。
- “第三方模型库”页：第三方模型新增、编辑、删除、选择、批量导入和 OpenAI-compatible `/models` 自动发现。
- API Key 检查。
- API Key 保存到 Windows 用户环境变量、本地 ignored `.env.local.json`，或 Windows Credential Manager。
- 第三方模型验证，并把验证状态写回 `log/third_party_models.json`。
- 运行前完整性检查：`hybrid` 任务会检查 Vision/Brain provider、model、base_url、api_key_env、Key 是否存在，并阻止明显错误的组合，例如 Vision 误选 DeepSeek。

按钮语义：

- `检查 Key`：只读取本机 secret，不联网。
- `验证模型`：发轻量 API 请求验证模型可用性。

第三方模型 registry 只保存：

```text
provider
model_id
base_url
api_key_env
roles
supports_vision
input_price
output_price
verification
```

不保存真实 API Key。坏 registry 文件不会被静默覆盖，必须先人工修复。

GUI 只把已选模型写成 CLI 覆盖参数；不会让 GUI 子进程进入交互式模型选择，也不会把 Key 明文传入命令行。

## Secret 读取

统一入口：`docpage2md_app/secrets.py`。

读取顺序：

1. 当前进程环境变量。
2. 本地 ignored `.env.local.json`。
3. Windows 用户环境变量。
4. Windows Credential Manager。

本地 `.env.local.json` 被 `.gitignore` 覆盖，适合 GUI 用户保存 Key。命令预览、日志、report 只显示 Key 名称，不显示真实值。

## 安全约束

- 配置文件、缓存、report 只允许保存环境变量名，不保存 key 值。
- `run_report.json` 只记录 provider、model、base_url、api_key_env。
- 如果用户误把疑似 token 写入模型配置，启动时应提示迁移到环境变量。
- 模型 `reasoning_content` 不写入 Markdown；默认也不持久化原始思考过程。

## 官方模型/价格刷新

默认不在普通处理任务里联网刷新价格。刷新必须由用户显式点击 GUI 按钮，或运行 CLI 命令：

```powershell
python docpage2md.py --refresh-models --refresh-prices --providers dashscope,deepseek --show-model-diff
python docpage2md.py --refresh-models --providers openai-compatible --base-url "https://example.com/v1"
python docpage2md.py --refresh-prices --import-pricing-md ".\docs\reference-pricing\价格.md" --show-model-diff
```

刷新服务入口是 `docpage2md_app/official_catalog.py`，缓存仍写入 `--model-cache` 指定文件，默认 `.cache/aliyun_model_catalog.json`。缓存 schema v2 会记录：

- provider 列表
- fetched_at
- source URL
- price unit / currency
- parser errors
- added / removed / price_changed diff

Provider 行为：

- DashScope：读取官方模型页、定价页和现有阿里云 parser；失败时保留本地精选模型。
- DeepSeek：优先调用 `/models` 获取可用模型，再解析官方价格页；失败时回退本地 DeepSeek 文档价格。
- OpenAI-compatible：只调用 `/models` 自动发现模型 ID；价格必须用户手动填写或用 `--import-pricing-md` 导入，程序不会猜价格。

本地 fallback 价格优先来自：

- `docs/deepseek-api/模型 & 价格 _ DeepSeek API Docs.md`
- `docs/reference-pricing/模型调用计费2026.6.23.md`

GUI 成本估算使用模型目录里的离线价格和用户录入的第三方价格。对于本地 PDF/Office 文件，MinerU 返回前只能按页数和经验 crop 数估算；已有 MinerU artifact 可以读取真实 crop 图片尺寸，估算更可靠。

成本 UI 当前按文件表展示：

- 文件
- 页数
- 估计裁剪块
- 输入 tokens
- 输出 tokens
- Vision/Brain 费用
- 可信度

MinerU 和 PaddleOCR 在 GUI 中显示为平台额度/限制，不计入人民币模型费用。
