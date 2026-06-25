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

当前 Tkinter GUI 的模型页提供：

- 当前生效 Vision / Brain 模型编辑。
- 官方模型候选列表，来自 `load_model_catalog()`。
- 第三方模型新增、编辑、删除、选择和批量导入。
- API Key 环境变量检查。
- Windows 用户环境变量写入。
- 第三方模型验证，并把验证状态写回 `log/third_party_models.json`。

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

## 安全约束

- 配置文件、缓存、report 只允许保存环境变量名，不保存 key 值。
- `run_report.json` 只记录 provider、model、base_url、api_key_env。
- 如果用户误把疑似 token 写入模型配置，启动时应提示迁移到环境变量。
- 模型 `reasoning_content` 不写入 Markdown；默认也不持久化原始思考过程。

## 价格来源

默认不联网刷新价格。价格优先来自本地文档：

- `docs/deepseek-api/模型 & 价格 _ DeepSeek API Docs.md`
- `docs/reference-pricing/模型调用计费2026.6.23.md`

联网刷新或导入复制版价格页应作为显式命令，不在主流程自动执行。

GUI 成本估算使用模型目录里的离线价格和用户录入的第三方价格。对于本地 PDF/Office 文件，MinerU 返回前只能按页数和经验 crop 数估算；已有 MinerU artifact 可以读取真实 crop 图片尺寸，估算更可靠。
