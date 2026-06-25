# DocPage2MD Agent Notes

Last updated: 2026-06-25

## Current Goal

DocPage2MD converts PDF, Office, images or legacy page-image folders into clean Markdown. The active user-facing work is making the lightweight GUI usable while keeping CLI stable.

Current entrypoints:

- CLI: `python docpage2md.py`
- GUI: `python docpage2md_gui.py`
- GUI package entry: `python -m docpage2md_app.gui`
- Package help: `python -m docpage2md_app --help`

## Do Not Touch

- Do not read, rewrite, move or delete `markdown_output/已归档`. It is deprecated output kept by user request.
- Do not delete private PDFs under `tests/` or local output folders.
- Do not save API Key values into files. Save only environment variable names.

Expected secrets:

- `MINERU_API_TOKEN`
- `DASHSCOPE_API_KEY`
- `DEEPSEEK_API_KEY`

## Processing Modes

- `mineru_only`: MinerU artifact/API -> deterministic Markdown.
- `hybrid`: MinerU layout/crop -> crop Vision -> Brain JSON ops -> checked refiner -> deterministic Markdown.
- `vision_only`: legacy image-folder flow under `doc_pages/`.

GUI supports the main MinerU paths: local single file, local multiple files, folder batch, MinerU artifact and URL. `vision_only` remains CLI-only for now.

## Parallelism

Hybrid parallelism is required behavior:

- MinerU parses a PDF once and returns all pages/crops.
- Crop Vision runs all eligible crop blocks in one thread pool, default `vision_batch_workers = 60`.
- Brain runs all pages in one thread pool after crop Vision completes, default `brain_batch_workers = 60`.
- Actual worker count is `min(job_count, configured_workers)`.

Do not serialize page Brain calls unless explicitly debugging a provider limit. If provider throttling becomes a problem, expose throttling as a user setting instead of removing parallelism.

## Latest Real Performance Finding

Existing full verification output:

- `markdown_output/gui_parallel_full_verify/群论笔记3.1`: 13 pages, `hybrid`, `qwen3-vl-plus`, `deepseek-v4-flash`, status `ok`.
- `markdown_output/gui_parallel_full_verify/群论笔记4.1`: 11 pages, `hybrid`, `qwen3-vl-plus`, `deepseek-v4-flash`, status `ok`.
- Latest final real verification after GUI/model/cost/formula changes:
  - Source PDF: `tests/群论笔记4.1.pdf`.
  - Final output: `markdown_output/git_verify_20260625_final2/git_verify_4_1_final2`.
  - Full 11 pages, `hybrid`, `balanced`, `vision_batch_workers=60`, `brain_batch_workers=60`.
  - Models: Vision `dashscope:qwen3-vl-plus`, Brain `deepseek:deepseek-v4-flash`.
  - Status: `ok`; pages ok: `11/11`.
  - Crop Vision: 49 blocks, succeeded 49, elapsed about `14.0s`.
  - Brain: 11 pages, workers 11, elapsed about `109.8s`.
  - Total elapsed from process log: about `124.2s`.

Direct `群论笔记4.1.pdf` run breakdown from `markdown_output/群论笔记4.1/群论笔记4.1/process.log`:

- Total: about `108.4s`.
- MinerU upload/wait/download/unzip/adapt: about `6.1s`.
- Crop Vision: `49` blocks, workers=`49`, about `27.2s`.
- Brain: `11` pages, workers=`11`, about `75.0s`.
- Render/report: about `0.1s`.

Bottleneck is Brain provider latency and long-tail page complexity, not missing page-level parallelism.

Brain prompt context now keeps full detail for the target page and compresses neighboring pages. On existing `群论笔记4.1` IR this reduced Brain prompt characters by about 25%.

## Logging

`RunLogger` writes translated Chinese progress messages to stdout and per-output `process.log`. Old logs remain English; new tasks write Chinese.

Important stage logs to preserve:

- `开始并行识别裁剪块`
- `裁剪块并行识别完成`
- `开始并行 Brain 精修`
- `Brain 并行精修完成`
- `Markdown 渲染完成`

These make speed bottlenecks readable without manually subtracting timestamps.

## Markdown Contract

User Markdown must not contain:

- API keys
- Python tracebacks
- provider raw errors
- validator diagnostics
- model reasoning or `reasoning_content`

Typora-compatible figure details are default-closed:

```markdown
<details>
<summary>图示识别内容</summary>

- 说明：...

</details>
```

Do not use `<details open>`.

Formula and math-symbol output must be LaTeX-first:

- Inline or display formulas embedded in `paragraph` / `text` blocks still need `$...$` or `$$...$$`.
- Do not leave raw Unicode math symbols such as `φ`, `θ`, `ω`, `α`, `β`, `≤`, `≥`, `→` in final Markdown.
- Use LaTeX commands such as `$\phi$`, `$\theta$`, `$\omega$`, `$\alpha$`, `$\beta$`, `$\leq$`, `$\geq$`, `$\to$`.
- Validator warning `unicode_math_symbol_outside_latex` means the output is not contract-clean.
- Arrow chains such as `k→g→?` must be rendered as one inline formula, for example `($k \to g \to ?$)`, not as overlapping `$...$` fragments.

## Model Management

Default profiles:

- `cheap`: `qwen3-vl-flash` + `deepseek-v4-flash`
- `balanced`: `qwen3-vl-plus` + `deepseek-v4-flash`
- `accurate`: `qwen3.7-plus` + `deepseek-v4-pro`
- `manual`: explicit provider/model/base_url/api_key_env

GUI writes selected models into CLI override parameters:

- `--vision-provider`
- `--vision-model`
- `--vision-base-url`
- `--vision-api-key-env`
- `--brain-provider`
- `--brain-model`
- `--brain-base-url`
- `--brain-api-key-env`

Third-party models live in `log/third_party_models.json`. Store env var names only, never key values.

## Cost Estimation

- DeepSeek V3 tokenizer resources are bundled under `docpage2md_app/deepseek_v3_tokenizer/`.
- Use `docpage2md_app.cost.estimate_deepseek_text_tokens()` / `estimate_deepseek_chat_tokens()` for offline DeepSeek token estimates; do not require `transformers` for GUI cost estimation.
- Qwen image token estimates use the Aliyun smart-resize rule for Qwen3-VL/Qwen3.5/3.6/3.7: `32x32` pixels per visual token, plus the two vision boundary tokens, with `min_pixels/max_pixels`.
- Local PDF/Office cost before MinerU is still approximate because true crop blocks and Brain prompt text do not exist yet. Existing MinerU artifact cost can use real crop image dimensions and real Brain prompts.
- Real-time price table refresh is future WebUI/model-manager work, not part of the current offline estimator.

## WebUI Direction

Keep Tkinter as a lightweight usable entry. Do not keep piling complex workflow UI into it forever.

Planned direction: local WebUI with FastAPI backend, React/Svelte/Vue frontend, SSE/WebSocket progress, virtualized logs, model settings page, output preview and history. Roadmap: `docs/plans/webui-roadmap.md`.

## Verification

Run after code changes:

```powershell
python docpage2md.py --help
python -m docpage2md_app --help
python -m pytest -q
git diff --check
```

Most recent regression on 2026-06-25:

- `python docpage2md.py --help`: passed.
- `python -m docpage2md_app --help`: passed.
- `python -m pytest -q`: `248 passed`.
- `git diff --check`: passed, with only CRLF conversion warnings.

Focused smoke used during GUI/log work:

```powershell
python -m pytest tests/test_cli.py tests/test_gui.py tests/test_hybrid_enrichment.py tests/test_mineru_pipeline.py tests/test_files_and_session.py tests/test_run_logger.py -q
```
