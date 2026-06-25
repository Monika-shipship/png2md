# DocPage2MD Current Status

Last updated: 2026-06-25

## Project Identity

- Product name: `DocPage2MD`
- Main entrypoint: `python docpage2md.py`
- GUI entrypoints: `python docpage2md_gui.py`, `python -m docpage2md_app.gui`
- Importable package: `docpage2md_app`
- Main branch under active work: `codex/mineru-refine-inspired`
- Legacy image-folder input directory: `doc_pages/`
- Optional local private input directory: `input_docs/`
- Primary output directory: `markdown_output/`

New work should use `docpage2md.py` and `docpage2md_app`. Historical entrypoint files have been removed from the working tree and are tracked by Git as deletions.

Internal code should use DocPage2MD naming only: `process_single_docpage_task`, `scan_docpage_folders`, `max_docpage_workers`, `doc_name`, and `doc_root`.

## Current Architecture

DocPage2MD has five processing modes:

- `mineru_only`: call or read MinerU output, render clean Markdown from MinerU layout/json/crops.
- `mineru_hybrid` / `hybrid`: MinerU layout/crops first, then crop vision + Brain JSON ops + checked refiner + deterministic renderer.
- `paddleocr_only`: call or read PaddleOCR output, adapt `layoutParsingResults` / Markdown / images to DocumentIR, then render clean Markdown.
- `paddleocr_hybrid`: PaddleOCR DocumentIR plus DocPage2MD crop Vision / Brain refinement.
- `dual_hybrid`: MinerU and PaddleOCR both parse the same input; a fusion layer aligns pages, builds bbox/text/type candidate groups, applies checked whitelist fusion ops into `fused_document_ir.json`, then DocPage2MD runs crop Vision + Brain + checked refiner on the fused IR.
- `vision_only`: legacy image-folder flow for page images.

The Tkinter GUI is the current lightweight desktop entry. It supports local single file, multiple files, folder batch, MinerU artifact, PaddleOCR artifact and URL inputs; Chinese labels/logs; progress/ETA; cost estimate; output folder opening; Vision/Brain worker controls; and model management. The run tab is split into left-side workflow/input/output controls and right-side progress/cost/log controls.

Current GUI details:

- Input is a visual file table, not a raw path box. It shows file name, suffix, size, pages, processing order and limit status.
- Main workflow text is short; detailed explanations live behind `?` help buttons.
- Advanced MinerU settings are collapsed by default and pass CLI args for OCR/formula/table/language.
- MinerU defaults to `vlm`; HTML/HTM automatically uses `MinerU-HTML`; non-HTML cannot use `MinerU-HTML`.
- Local PDF inputs can enable automatic MinerU page splitting, with final chunk merge/audit.
- Cost UI is a table and only estimates Vision/Brain token fees; MinerU/PaddleOCR are quota/limit notes.
- Model management is provider-first: Provider/Key, role binding, candidate models and third-party model library.
- PaddleOCR is selectable as a parser engine, default model `PaddleOCR-VL-1.6`, async endpoint `https://paddleocr.aistudio-app.com/api/v2/ocr/jobs`, default PDF chunk size 100 pages.
- Dual parser is selectable as `MinerU + PaddleOCR 双引擎融合`; it currently supports local files/folders and artifact pairs, not remote URLs or automatic chunked dual merge. It writes `ir/mineru_document_ir.json`, `ir/paddleocr_document_ir.json`, `ir/fused_document_ir.json` and compatibility `ir/document_ir.json`.
- Official model/price refresh is available through CLI and GUI background refresh, with provider-aware diff summary and local fallback. DashScope refresh keeps the broad official catalog but filters obvious documentation slug artifacts; GUI role binding then narrows Vision/Brain candidates by capability metadata.

The longer-term WebUI plan is tracked in `docs/plans/webui-roadmap.md`. PaddleOCR status and follow-up comparison work are tracked in `docs/plans/paddleocr-integration-roadmap.md`.

Hybrid parallelism is active:

- Crop Vision runs all eligible crop blocks in a thread pool, default `vision_batch_workers = 60`.
- Brain refinement runs all pages in a thread pool after crop Vision completes, default `brain_batch_workers = 60`.
- Actual workers are capped by job count, so an 11-page PDF uses 11 Brain workers even if the configured limit is 60.

User-facing Markdown remains:

- `Slide_XX.md`
- `{doc_name}_FULL.md`

Diagnostics and audit data belong in:

- `run_report.json`
- `process.log`
- `ir/`
- `mineru_raw/`
- `paddleocr_raw/`

Do not put stack traces, API errors, model reasoning, coverage diagnostics, or validator dumps into user Markdown.

Local output directories are useful user assets, not disposable trash:

- Keep `markdown_output/` and `latex_output/` out of Git.
- Do not automatically delete them during cleanup.
- `log/` can be rotated or compressed by an explicit command, but should not be silently deleted.

Recommended future log cleanup behavior:

- Add an explicit command such as `python docpage2md.py --cleanup-logs`.
- Compress logs older than 7 days into `log/archive/`.
- Delete archived logs only when they are older than a documented threshold, such as 60 or 90 days.
- Never delete `markdown_output/`, `latex_output/`, `input_docs/` or user-provided source files from cleanup code.

## Key Docs

- User quickstart: `README.md`
- Pipeline explanation: `docs/architecture/docpage-to-markdown-pipeline.md`
- Hybrid design: `docs/architecture/hybrid-mineru-docpage2md.md`
- Model management: `docs/architecture/model-manager.md`
- Markdown contract: `docs/architecture/markdown-output-contract.md`
- MinerU setup: `docs/architecture/mineru-api-setup.md`
- Hybrid region recovery plan: `docs/plans/hybrid-region-revision-roadmap.md`
- WebUI plan: `docs/plans/webui-roadmap.md`
- PaddleOCR integration plan: `docs/plans/paddleocr-integration-roadmap.md`
- Change history: `docs/changelog.md`
- Research comparison: `docs/research/comparison-and-docpage2md-roadmap.md`

## Secrets

API keys and tokens must stay out of the repository.

Expected environment variables:

- `MINERU_API_TOKEN`
- `DASHSCOPE_API_KEY`
- `DEEPSEEK_API_KEY`
- `PADDLEOCR_API_TOKEN`

Logs and reports may record env var names, providers, models, task IDs and trace IDs. They must not record actual token values.

Local PaddleOCR real samples should live under ignored `tests/test-PaddleOCR/`. Local PaddleOCR token notes may live in ignored `.env.paddleocr.local.md`; never commit token values.

GUI model management checks provider/model/base_url/api_key_env completeness and missing Vision/Brain environment variables before starting hybrid modes. Third-party model auto-discovery uses OpenAI-compatible `/models` and imports only model metadata plus env var names. Official refresh covers DashScope, DeepSeek and OpenAI-compatible providers; OpenAI-compatible prices are never guessed.

Secret lookup is centralized in `docpage2md_app/secrets.py`. Supported storage:

- process/Windows user environment variables
- local ignored `.env.local.json`
- Windows Credential Manager when available

Logs, command previews and reports must only show key names.

## Verification Commands

Run these after code changes:

```powershell
python docpage2md.py --help
python -m docpage2md_app --help
python -m pytest
git diff --check
```

Useful offline smoke using an existing MinerU artifact:

```powershell
python docpage2md.py --engine-mode mineru_only --mineru-artifact-dir ".\tests\fixtures\mineru_public\minimal_artifact" --output ".\markdown_output\smoke" --name "public_mineru_fixture"
```

Useful real API smoke, when keys are configured and cost/time are acceptable:

```powershell
python docpage2md.py --engine-mode hybrid --model-profile cheap --input-file ".\input_docs\我的手写笔记.pdf" --page-ranges 1-2 --output ".\markdown_output\real_smoke" --name "private_api_smoke_1_2"
```

## Latest Verified Results

- `python docpage2md.py --help`: passed.
- `python -m docpage2md_app --help`: passed.
- `python -m pytest -q`: 292 passed.
- `git diff --check`: passed, with only CRLF conversion warnings.
- GUI construction smoke passed: `DocPage2MdGui()` can construct, update idle tasks and destroy cleanly after the input table/provider/cost redesign.
- `python -m pytest tests/test_cli.py tests/test_gui.py tests/test_hybrid_enrichment.py tests/test_mineru_pipeline.py tests/test_files_and_session.py tests/test_run_logger.py -q`: 41 passed during GUI/log/performance work.
- `python -m pytest tests/test_paddleocr_client.py tests/test_paddleocr_adapter.py tests/test_paddleocr_pipeline.py tests/test_official_catalog.py tests/test_cli.py -q`: 30 passed during PaddleOCR hardening work.
- PaddleOCR offline tests cover adapter, bad JSONL/empty pages, client fake HTTP, pending/running/done states, 429/503/504 retry, result download retry, pipeline rendering and chunk merge.
- PaddleOCR adapter confidence values are numeric floats in `0.0-1.0`; human confidence labels are stored separately as `confidence_label`. This is required because the hybrid refiner treats `block.confidence` as numeric.
- PaddleOCR remote URL inputs perform a HEAD `Content-Length` check when available and block files over 200 MB; unknown length is logged and allowed to proceed.
- Official catalog refresh cache includes `refresh.provider_status` with per-provider status, source URLs, record counts and failure reasons. A live DashScope/DeepSeek refresh smoke produced 340 records after documentation artifact filtering and no obvious fake IDs such as `qwen-false` or `qwen-usage-list`.
- Historical alias search: no working-tree matches.
- Public fixture artifact smoke can run without network or private data.
- Private real API smoke should use ignored files under `input_docs/` or another local path; do not commit those inputs or outputs.
- Existing full real GUI verification outputs:
  - `markdown_output/gui_parallel_full_verify/群论笔记3.1`: 13 pages, `hybrid`, `qwen3-vl-plus`, `deepseek-v4-flash`, status `ok`.
  - `markdown_output/gui_parallel_full_verify/群论笔记4.1`: 11 pages, `hybrid`, `qwen3-vl-plus`, `deepseek-v4-flash`, status `ok`.
- Latest final real verification:
  - Source: `tests/群论笔记4.1.pdf`.
  - Output: `markdown_output/git_verify_20260625_final2/git_verify_4_1_final2`.
  - Full 11 pages, `hybrid + balanced`, Vision `qwen3-vl-plus`, Brain `deepseek-v4-flash`.
  - `run_report.json`: `status=ok`, `engine_mode=hybrid`, `pages_ok=11/11`.
  - Parallelism confirmed in Chinese `process.log`: crop Vision 49 blocks in about 14.0s, Brain 11 pages in about 109.8s, total about 124.2s.
  - Final Markdown uses default-closed `<details>` blocks and passed the no-key/no-traceback/no-reasoning/no-validator-diagnostics checks.
- Latest PaddleOCR GUI real verification:
  - Source: `tests/群论笔记4.1.pdf`.
  - GUI path was driven through `DocPage2MdGui._options()` / `_validate_before_run()` / `_start_process()` and its subprocess command preview.
  - `paddleocr_only` output: `markdown_output/gui_paddleocr_real_verify_only/gui_paddleocr_4_1_only`.
    - Full 11 pages, `status=ok`, `engine_mode=paddleocr_only`, layout model `PaddleOCR-VL-1.6`, final pages `ok=11/11`, Brain `skipped=11/11`, total about `19.1s`.
  - `paddleocr_hybrid` output: `markdown_output/gui_paddleocr_real_verify_hybrid/gui_paddleocr_4_1_hybrid`.
    - Full 11 pages, `status=ok`, `engine_mode=paddleocr_hybrid`, layout model `PaddleOCR-VL-1.6`, Vision `qwen3-vl-plus`, Brain `deepseek-v4-flash`, final pages `ok=11/11`, Brain `partial=11/11`, total about `106.0s`.
  - Both outputs contain `paddleocr_raw/`, `ir/`, `assets/`, `Slide_XX.md`, `*_FULL.md`, `run_report.json` and Chinese `process.log`.
  - Final Markdown for both modes passed no-key/no-traceback/no-confidence-error/no-validator-text/no-reasoning checks.
- Latest dual engine real verification:
  - Source: `tests/群论笔记4.1.pdf`, page range `1`.
  - PaddleOCR-only API probe output: `markdown_output/paddleocr_api_probe_20260625/paddleocr_api_probe_page1`.
    - `status=ok`, `engine_mode=paddleocr_only`, 1 page, and real API result contained `layoutParsingResults`, `prunedResult`, `markdown`, `outputImages`, `inputImage` and `dataInfo`.
  - Dual real probe output: `markdown_output/dual_real_probe_20260625/dual_real_probe_page1`.
    - `status=ok`, `engine_mode=dual_hybrid`, old strategy `mineru_primary_paddleocr_evidence`, layout model `vlm+PaddleOCR-VL-1.6`.
  - Post-fix artifact rerun output: `markdown_output/dual_real_artifact_rerun_20260625/dual_real_artifact_rerun_page1`.
    - `status=ok`, pages `1/1`, Vision `qwen3-vl-plus`, Brain `deepseek-v4-flash`.
    - Final Markdown no longer repeats `(2)结合律：` and passed no-key/no-traceback/no-provider-error/no-validator-text/no-reasoning checks.
- Latest dual fusion offline upgrade:
  - New files: `docpage2md_app/fusion.py`, `docpage2md_app/fusion_prompt.py`, `tests/test_fusion.py`.
  - Strategy: `candidate_group_checked_ops`.
  - Candidate grouping uses bbox overlap, text similarity, vertical/type similarity and caption/image proximity; unmatched MinerU/PaddleOCR blocks are preserved.
  - Fusion report records candidate groups, decisions, rejected ops and uncertain items under `run_report.json["fusion"]`.
  - Tests cover page alignment, unmatched preservation, formula replacement, bad op rejection, prompt public fields and pipeline IR emission.
- Same-file parser comparison for `tests/群论笔记4.1.pdf`:
  - `mineru_only`: `markdown_output/mineru_real_compare_4_1_only/mineru_4_1_only_compare`, 11 pages, `status=ok`, final pages `ok=11/11`, about `16.4s`.
  - `mineru_hybrid` / legacy `hybrid`: `markdown_output/gui_parallel_full_verify/群论笔记4.1`, 11 pages, `status=ok`, final pages `ok=11/11`, about `113.9s`.
  - `paddleocr_only`: `markdown_output/gui_paddleocr_real_verify_only/gui_paddleocr_4_1_only`, 11 pages, `status=ok`, final pages `ok=11/11`, about `19.1s`.
  - `paddleocr_hybrid`: `markdown_output/gui_paddleocr_real_verify_hybrid/gui_paddleocr_4_1_hybrid`, 11 pages, `status=ok`, final pages `ok=11/11`, about `106.0s`.
- `群论笔记4.1.pdf` performance from existing full log: total about 114s in `gui_parallel_full_verify`, and about 108s in the later direct run. Breakdown from the later direct run: MinerU about 6.1s, crop Vision 49 blocks about 27.2s, Brain 11 pages about 75.0s, render/report about 0.1s. Bottleneck is Brain provider latency and long-tail page complexity, not missing page-level parallelism.
- New `process.log` output is translated to Chinese by `RunLogger`; old logs generated before this change remain English.
- Brain prompt context now keeps full detail for the target page and compresses neighboring pages, reducing the measured `群论笔记4.1` Brain prompt characters by about 25% before another real API rerun.

## Handoff Notes

- Keep README, architecture docs, changelog and this status file synchronized with code changes.
- If a public command changes, update README and `docs/maintenance/current-status.md`.
- If schema names, output layout or report fields change, update architecture docs and tests together.
- If a real API smoke reveals a quality issue, summarize it in `docs/changelog.md` and keep detailed diagnostics in `run_report.json`, not Markdown.
- Do not read, rewrite, move or delete `markdown_output/已归档`; it is deprecated output retained by user request.
- PaddleOCR docs are local under `docs/PaddleOCR/`; read them before changing request payloads, limits or artifact parsing.
- For `dual_hybrid`, implement chunked dual merge before allowing long PDFs to auto-split; current guard intentionally blocks PDFs beyond the PaddleOCR chunk size.
