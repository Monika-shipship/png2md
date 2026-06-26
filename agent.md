# DocPage2MD Agent Notes

Last updated: 2026-06-26

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
- `PADDLEOCR_API_TOKEN`

## Processing Modes

- `mineru_only`: MinerU artifact/API -> deterministic Markdown.
- `hybrid`: legacy alias for MinerU layout/crop -> crop Vision -> Brain JSON ops -> checked refiner -> deterministic Markdown.
- `mineru_hybrid`: explicit MinerU + DocPage2MD refinement mode.
- `paddleocr_only`: PaddleOCR async artifact/API -> DocumentIR -> deterministic Markdown.
- `paddleocr_hybrid`: PaddleOCR async artifact/API -> DocumentIR -> crop Vision + Brain JSON ops -> checked refiner -> deterministic Markdown.
- `dual_hybrid`: MinerU and PaddleOCR both parse the same input; a fusion layer aligns pages, builds bbox/text/type candidate groups, applies checked whitelist fusion ops into `fused_document_ir.json`, then the existing crop Vision + Brain + checked refiner path runs on the fused IR.
- `vision_only`: legacy image-folder flow under `doc_pages/`.

GUI supports the main MinerU and PaddleOCR paths: local single file, local multiple files, folder batch, MinerU artifact, PaddleOCR artifact and URL. `vision_only` remains CLI-only for now. The run tab is a scrollable two-column workbench:

- Left: workflow presets, visual input file table, output/concurrency, advanced MinerU settings.
- Right: progress/ETA, cost table, command preview, Chinese logs, actions.

Keep the run tab usable in non-fullscreen windows. The page-level canvas provides vertical scrolling, the cost table has horizontal scrolling, and command preview has copy/full-command affordances.

Input UI should not expose a raw semicolon path string to normal users. Keep it as internal CLI compatibility only.

PaddleOCR implementation notes:

- Roadmap/status: `docs/plans/paddleocr-integration-roadmap.md`.
- Local docs: `docs/PaddleOCR/`.
- Future private real samples: `tests/test-PaddleOCR/`, ignored by Git.
- Existing `hybrid` should remain compatible with `mineru_hybrid`.
- Default model: `PaddleOCR-VL-1.6`.
- Default async endpoint: `https://paddleocr.aistudio-app.com/api/v2/ocr/jobs`.
- Local PDF/page processing defaults to 100-page chunks.
- Generated artifacts are saved under `.paddleocr_cache/.../artifact` during processing. Default `output_retention=slim` cleans generated parser cache after successful processing and does not copy final `paddleocr_raw/`; `debug` preserves raw artifacts/cache.
- Do not commit PaddleOCR token values. Local ignored token note may be `.env.paddleocr.local.md`.
- Adapter `block.confidence` must stay numeric (`0.0-1.0`). Store human labels such as `high` / `medium` / `low` in `confidence_label`, otherwise hybrid refiner float conversion can fail.

Dual engine implementation notes:

- User-facing mode: `dual_hybrid`; GUI label: `MinerU + PaddleOCR 双引擎融合`.
- CLI supports local file(s)/folder and the artifact pair `--mineru-artifact-dir` + `--paddleocr-artifact-dir`.
- Remote URL dual mode is not supported yet; generate both artifacts first, then run artifact fusion.
- Dual mode currently blocks PDFs that exceed the PaddleOCR chunk size because chunked dual merge is not implemented.
- Fusion code lives in `docpage2md_app/fusion.py`, `docpage2md_app/fusion_prompt.py`, `docpage2md_app/dual_ir.py` and `docpage2md_app/dual_pipeline.py`.
- The fusion layer writes `ir/mineru_document_ir.json`, `ir/paddleocr_document_ir.json`, `ir/fused_document_ir.json` and compatibility `ir/document_ir.json` only in `standard` / `debug` retention. Default `slim` keeps final Markdown, assets, metadata, logs and report.
- Fusion uses candidate groups and whitelist actions only: `choose_block`, `merge_blocks`, `keep_both`, `mark_uncertain`, `attach_image`, `replace_formula`, `convert_text_to_formula`, `convert_text_to_figure_note`.
- `dual_ir` is a compatibility wrapper; new behavior should go through `fusion.py`.
- Keep existing hybrid parallelism intact after fusion. Do not let Brain freely rewrite full Markdown.
- Dual local multi-file mode now uses parser scheduling: `parser_workers` controls how many files are submitted/waited concurrently, and each file still runs MinerU and PaddleOCR concurrently. `doc_workers` controls how many ready documents enter fusion/enrichment at once. Keep this scheduler; do not regress to file-by-file serial parser submission.
- `paddleocr` is a legal IR block origin. Do not remove it from `BLOCK_ALLOWED_ORIGINS` / `BLOCK_VISION_ORIGINS`; otherwise Brain checked ops in dual mode will be rejected by page IR contract validation.
- PaddleOCR blocks must carry `source_engine`, numeric `confidence`, `bbox` (or `None`) and `evidence.raw_text`.

Brain evidence-review contract:

- Brain is an evidence reviewer, not a free Markdown rewriter.
- It may read the current page plus a configurable compressed neighbor-page window and may discover new issues beyond initial findings.
- Default Brain context radius is `2`; CLI/GUI expose `--brain-context-radius` / `Brain 上下文`, where `0` means current page only.
- Initial rule/diff/validator/vision questions are first-class `findings`, not `suspects`, in new reports. Current initial sources include `deterministic_detector`, `validator_precheck`, `dual_engine_diff` and `vision_crop_evidence`.
- Brain must return `decisions`, `new_findings` and `op_candidates`; accepted ops must be checked block ops with `finding_id` or `new_finding_id`, `decision`, `evidence_type`, `confidence` and a concrete target block/span.
- `replace_text_span_checked` requires high confidence and short span evidence. Whole-page Markdown rewrites, code fences and `[mineru]` / `[paddleocr]` alternatives must be rejected locally.
- Keep initial findings as priority signals, not the only allowed review range.

## Parallelism

Hybrid parallelism is required behavior:

- MinerU parses a PDF once and returns all pages/crops.
- Crop Vision runs all eligible crop blocks in one thread pool, default `vision_batch_workers = 60`.
- Brain runs all pages in one thread pool after crop Vision completes, default `brain_batch_workers = 60`.
- Actual worker count is `min(job_count, configured_workers)`.
- Brain defaults to fast non-thinking mode (`brain_thinking=disabled`) for JSON ops / Markdown structure refinement. Users can enable high-quality thinking for difficult pages through the GUI or `--brain-thinking enabled`.
- Brain context radius is configurable independently from worker count; larger windows can improve cross-page corrections but increase Brain prompt tokens, cost and latency.

Do not serialize page Brain calls unless explicitly debugging a provider limit. If provider throttling becomes a problem, expose throttling as a user setting instead of removing parallelism.

Current GUI exposes concurrency presets:

- `保守 3/3`
- `均衡 6/6`
- `高并发 12/12`
- `极速 60/60`
- `自定义`

GUI also exposes parser/document workers separately from Vision/Brain workers. Presets intentionally affect only Vision/Brain so parser scheduling is not changed implicitly during A/B runs.

The processor logs Brain per-page elapsed time plus p50/p90/max and a long-tail warning. If a real run is slow with no 429/retry, first compare the same PDF with Brain workers `60`, `12`, `6` and `3` before changing the core pipeline.
New Brain logs include actual worker count, configured worker limit and fast/high-quality thinking mode, so `actual=11, limit=60` on an 11-page PDF is expected and does not mean parallelism was removed.

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

Latest PaddleOCR real verification:

- Source PDF: `tests/群论笔记4.1.pdf`.
- Output: `markdown_output/paddleocr_real_verify_4_1_hybrid_fixed/paddleocr_4_1_hybrid_fixed`.
- Mode: `paddleocr_hybrid`, layout `PaddleOCR-VL-1.6`, balanced Vision `qwen3-vl-plus`, Brain `deepseek-v4-flash`.
- Status: `ok`; final pages `11/11`; Brain pages `partial=11/11`; no Brain thread failures.
- Total elapsed about `124.9s`: PaddleOCR submit/parse about `1.4s`, artifact download/cache about `21.3s`, Brain enrichment about `102.0s`, render/report about `0.1s`.
- This run validates the numeric PaddleOCR confidence fix; no `could not convert string to float` error appeared.

Latest dual engine real verification:

- Real PaddleOCR API was confirmed with `tests/群论笔记4.1.pdf`, page range `1`, using `PADDLEOCR_API_TOKEN` from the process environment.
- PaddleOCR-only probe output: `markdown_output/paddleocr_api_probe_20260625/paddleocr_api_probe_page1`, `status=ok`, `engine_mode=paddleocr_only`, with `paddleocr_raw/result.jsonl`, `ir/`, `assets/`, `Slide_01.md` and `run_report.json`.
- Dual real probe output: `markdown_output/dual_real_probe_20260625/dual_real_probe_page1`, `status=ok`, `engine_mode=dual_hybrid`; it was generated before the candidate-group fusion upgrade and used the old `mineru_primary_paddleocr_evidence` strategy.
- After renderer duplicate-prefix protection, artifact rerun output: `markdown_output/dual_real_artifact_rerun_20260625/dual_real_artifact_rerun_page1`.
  - `status=ok`, pages `1/1`, layout model `vlm+PaddleOCR-VL-1.6`.
  - Vision `qwen3-vl-plus`, Brain `deepseek-v4-flash`.
  - The duplicated `(2)结合律：` line from the first real probe is fixed in final Markdown.
  - Final Markdown scan found no token, traceback, reasoning content, provider raw error or validator text.
- Latest GUI dual full smoke: `markdown_output/gui_full_pdf_smoke` processed `群论笔记3.1.pdf` and `群论笔记4.1.pdf` in `dual_hybrid` sequentially by file.
  - Total wall time in `dual_batch/process.log`: about `347.2s`.
  - `群论笔记3.1`: parser prep about `53.5s`, crop Vision `70` blocks about `38.9s`, Brain `13` pages about `124.1s`, total document phase about `164.0s`.
  - `群论笔记4.1`: crop Vision `47` blocks about `12.8s`, Brain `11` pages about `91.6s`, total document phase after parser prep about `105.2s`.
  - `群论笔记4.1` Brain page durations were roughly min `34.9s`, median `52.6s`, max `91.6s`; `群论笔记3.1` was roughly min `25.1s`, median `58.9s`, max `124.1s`.
  - Bottlenecks are Brain long-tail latency and dual parser/PaddleOCR artifact download, not missing page-level Brain parallelism. High Brain concurrency may still increase provider-side tail latency, so use the new GUI presets for A/B runs.
  - Follow-up optimization implemented after this run: same-file dual parser prep now runs MinerU and PaddleOCR concurrently.
- Controlled artifact rerun for `群论笔记4.1` with `dual_hybrid`, Vision workers `60`, Brain workers `6`:
  - Output: `markdown_output/concurrency_ab_4_1_brain6/dual_4_1_brain6`.
  - No parser upload/parse was repeated; reused the latest MinerU/PaddleOCR artifacts.
  - Crop Vision `47` blocks about `9.8s`.
  - Brain `11` pages with workers `6`: total about `94.7s`, p50 `39.2s`, p90 `50.8s`, max `53.6s`, tail ratio `1.37`.
  - Compared with workers `11`, lower Brain concurrency reduced the slowest single-page tail substantially but did not reduce total Brain wall time in this run because pages ran in two waves. Do not blindly lower defaults; use presets for per-provider A/B tests.
- Controlled artifact rerun for `群论笔记4.1` after disabling Brain thinking by default:
  - Output: `markdown_output/concurrency_ab_4_1_fast_brain/dual_4_1_fast_brain`.
  - Same existing MinerU/PaddleOCR artifacts, `dual_hybrid`, balanced profile, Vision workers `60`, Brain workers `60`.
  - Actual Brain workers were `11` because the PDF has 11 pages; configured limit remained `60`.
  - Crop Vision `47` blocks about `20.9s`.
  - Brain `11` pages in fast mode: total about `12.2s`, p50 `8.4s`, p90 `11.9s`, max `12.1s`, tail ratio `1.45`.
  - Compared with the earlier thinking-enabled run (`91.6s` Brain total), the main bottleneck was DeepSeek Brain thinking latency, not missing thread parallelism.
- Contract/evidence-review artifact rerun after allowing `paddleocr` origin and adding local Brain op policy:
  - Output: `markdown_output/real_contract_fix_smoke/real_contract_fix_4_1_v3`.
  - Same existing MinerU/PaddleOCR artifacts, `dual_hybrid`, balanced profile, Vision workers `60`, Brain workers `60`, Brain thinking disabled.
  - Status `ok`, pages `11/11`, `contract_error_codes={}`, no bad page IR contract errors.
  - Final Markdown scan found no API key, traceback, reasoning text, validator text, provider error, `[mineru]` / `[paddleocr]` labels, `<details open>` or raw figure JSON keys.
  - Figure block on page 3 is preserved as a default-closed Chinese `<details>` section.
  - This run was slow because crop Vision had provider long-tail latency: 48 crops completed in about `65.9s`; Brain 11 pages completed in about `20.7s`.
- Findings/context-window artifact rerun after adding explicit dual-engine and Vision finding sources:
  - Output: `markdown_output/findings_brain_window_verify/dual_4_1_findings_window_v3`.
  - Same existing MinerU/PaddleOCR artifacts, `dual_hybrid`, balanced profile, Vision workers `60`, Brain workers `60`, `--brain-context-radius 2`, Brain thinking disabled.
  - Status `ok`, pages `11/11`, `summary.suspects` absent and no `pages[].suspects`.
  - `summary.findings.by_source`: `validator_precheck=36`, `dual_engine_diff=138`, `vision_crop_evidence=48`, `deterministic_detector=2`.
  - Brain context windows recorded radius `2` with actual context page counts `3/4/5`.
  - Final Markdown scan found no `[mineru]` / `[paddleocr]`, Traceback, reasoning text, validator text or `<details open>`.
  - Runtime about `96.8s`: crop Vision 48 blocks about `34.2s`; Brain 11 pages about `61.2s`. The latest bottleneck was Vision/Brain provider long-tail latency, not missing thread parallelism.

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
- dual-engine candidate labels such as `[mineru] ...` or `[paddleocr] ...`; those belong only in IR/report evidence, never final Markdown.

Typora-compatible figure details are default-closed:

```markdown
<details>
    - 说明：...
<summary>图示识别内容</summary>

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

Current GUI model management:

- Tabs: Provider/Key, role binding, candidate models, third-party model library.
- Provider-first UI covers MinerU, PaddleOCR, DashScope, DeepSeek and OpenAI-compatible services.
- Key storage options: Windows user env, local ignored `.env.local.json`, and Windows Credential Manager when available.
- `检查 Key` is local only and must not call the network.
- `验证模型` may call a lightweight API probe and report/write verification status.
- Candidate lists merge official catalog and third-party registry and support text filtering.
- Third-party library supports add/edit/delete, bulk import, validation and OpenAI-compatible `/models` discovery.
- Starting `hybrid` checks model completeness and missing Vision/Brain env vars before spawning the CLI subprocess.

CLI/GUIs can override MinerU document options non-interactively:

- `--mineru-is-ocr`
- `--mineru-enable-formula`
- `--mineru-enable-table`
- `--mineru-language`
- `--auto-split-pages`
- `--mineru-page-chunk-size`

HTML/HTM must use `MinerU-HTML`; non-HTML must use `vlm` or `pipeline`.

## Cost Estimation

- DeepSeek V3 tokenizer resources are bundled under `docpage2md_app/deepseek_v3_tokenizer/`.
- Use `docpage2md_app.cost.estimate_deepseek_text_tokens()` / `estimate_deepseek_chat_tokens()` for offline DeepSeek token estimates; do not require `transformers` for GUI cost estimation.
- Qwen image token estimates use the Aliyun smart-resize rule for Qwen3-VL/Qwen3.5/3.6/3.7: `32x32` pixels per visual token, plus the two vision boundary tokens, with `min_pixels/max_pixels`.
- Local PDF/Office cost before MinerU is still approximate because true crop blocks and Brain prompt text do not exist yet. Existing MinerU artifact cost can use real crop image dimensions and real Brain prompts.
- GUI cost UI is a per-file table split by Vision input/output/cost and Brain input/output/cost, plus a Brain context-window comparison table for radii `0/1/2/3/5`.
- MinerU and PaddleOCR are displayed as platform quota/limit items, not as RMB model cost.
- Official model/price refresh is explicit: `--refresh-models`, `--refresh-prices`, `--providers`, `--show-model-diff`, `--import-pricing-md`.
- DashScope uses official docs/parsers; DeepSeek uses `/models` plus official pricing parser with local fallback; OpenAI-compatible only discovers `/models` and never guesses prices.

## README Shape

README is a user-facing landing page and quickstart. Keep it ordered as:

1. What the project does.
2. From-zero setup.
3. GUI-first usage.
4. Input/modes/model/cost basics.
5. CLI examples.
6. Safety and troubleshooting.
7. Links to docs for architecture details.

Do not move long pipeline explanations back into README; link to `docs/architecture/*` instead. A temporary ignored backup of the pre-restructure README may exist at `tmp/README.before-restructure.md` during this work.

## WebUI Direction

Keep Tkinter as a lightweight usable entry. Do not keep piling complex workflow UI into it forever.

Planned direction: local WebUI with FastAPI backend, React/Svelte/Vue frontend, SSE/WebSocket progress, virtualized logs, model settings page, output preview and history. Roadmap: `docs/plans/webui-roadmap.md`.

WebUI should split user choices into document preset, parser engine, refinement mode and model selection. PaddleOCR async progress can use real `totalPages/extractedPages` for progress and ETA.

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
- `python -m pytest -q`: `301 passed`.
- `git diff --check`: passed, with only CRLF conversion warnings.

Focused smoke used during GUI/log work:

```powershell
python -m pytest tests/test_cli.py tests/test_gui.py tests/test_hybrid_enrichment.py tests/test_mineru_pipeline.py tests/test_files_and_session.py tests/test_run_logger.py -q
```
