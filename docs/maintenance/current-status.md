# DocPage2MD Current Status

Last updated: 2026-06-26

## Project Identity

- Product name: `DocPage2MD`
- Main entrypoint: `python docpage2md.py`
- GUI entrypoints: `python docpage2md_gui.py`, `python -m docpage2md_app.gui`
- Importable package: `docpage2md_app`
- Main branch under active work: `main`
- App version: `0.1.0`
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

The Tkinter GUI is the current lightweight desktop entry. It supports local single file, multiple files, folder batch, MinerU artifact, PaddleOCR artifact and URL inputs; Chinese labels/logs; progress/ETA; cost estimate; output folder opening; Vision/Brain worker controls; and model management. The run tab is a scrollable workbench split into left-side workflow/input/output controls and right-side progress/cost/log controls.

Current GUI details:

- Input is a visual file table, not a raw path box. It shows file name, suffix, size, pages, processing order and limit status.
- Main workflow text is short; detailed explanations live behind `?` help buttons.
- Advanced MinerU settings are collapsed by default and pass CLI args for OCR/formula/table/language.
- MinerU defaults to `vlm`; HTML/HTM automatically uses `MinerU-HTML`; non-HTML cannot use `MinerU-HTML`.
- Local PDF inputs can enable automatic MinerU page splitting, with final chunk merge/audit.
- Cost UI is a table and only estimates Vision/Brain token fees; MinerU/PaddleOCR are quota/limit notes. The table splits Vision and Brain input/output/cost, and includes a Brain context-window comparison for radii `0/1/2/3/5`.
- The run tab remains usable in non-fullscreen windows: the page scrolls vertically, the cost table scrolls horizontally, and command preview supports horizontal scrolling plus copy/full-command actions.
- Model management is provider-first: Provider/Key, role binding, candidate models and third-party model library.
- PaddleOCR is selectable as a parser engine, default model `PaddleOCR-VL-1.6`, async endpoint `https://paddleocr.aistudio-app.com/api/v2/ocr/jobs`, default PDF chunk size 100 pages.
- Dual parser is selectable as `MinerU + PaddleOCR 双引擎融合`; it supports local files/folders, artifact pairs, and automatic local PDF chunked merge. Remote URL dual mode is still not supported directly. It writes `ir/mineru_document_ir.json`, `ir/paddleocr_document_ir.json`, `ir/fused_document_ir.json` and compatibility `ir/document_ir.json` only in `standard` / `debug` retention.
- Default output retention is `slim`: keep Markdown, referenced assets, `.meta.json`, `process.log` and `run_report.json`; skip raw artifact copies, skip IR, and clean generated parser cache after success. `standard` keeps IR; `debug` keeps raw artifacts/cache.
- Dual local multi-file mode now schedules parser work across files: `parser_workers` controls concurrent file submissions/waits, each file still submits MinerU and PaddleOCR concurrently, and `doc_workers` controls how many ready documents enter fusion/enrichment at once. Long local PDFs auto-split by `min(mineru_page_chunk_size, paddleocr_page_chunk_size)`, defaulting to 100 pages, then merge chunk outputs back into one final document.
- The run tab exposes concurrency presets: `保守 3/3`, `均衡 6/6`, `高并发 12/12`, `极速 60/60` and `自定义`. The raw Parser/Document/Vision/Brain worker fields remain visible for exact control; presets only change Vision/Brain.
- The run tab exposes `Brain 模式`: default fast mode disables model thinking for Brain JSON ops; high-quality mode can enable thinking for difficult pages.
- The run tab exposes `Brain 上下文`: default radius `2` reads the current page plus two pages on each side; users can choose current-page-only or larger windows. CLI uses `--brain-context-radius`.
- Official model/price refresh is available through CLI and GUI background refresh, with provider-aware diff summary and local fallback. DashScope refresh keeps the broad official catalog but filters obvious documentation slug artifacts; GUI role binding then narrows Vision/Brain candidates by capability metadata.
- Windows one-dir packaging is prepared through `python scripts\build_windows_exe.py`. The script builds `dist/DocPage2MD/DocPage2MD.exe` on a fresh build, falls back to a timestamped `dist/DocPage2MD_.../DocPage2MD.exe` when the default output already exists, keeps PyInstaller work/spec caches in `%TEMP%\docpage2md_pyinstaller`, smokes the frozen CLI marker, excludes dev/Notebook packages, and refuses release artifacts containing local secrets, private input/output folders or tests.

The longer-term WebUI plan is tracked in `docs/plans/webui-roadmap.md`. PaddleOCR status and follow-up comparison work are tracked in `docs/plans/paddleocr-integration-roadmap.md`.

Hybrid parallelism is active:

- Multi-file parser scheduling is active for dual local mode: default `parser_workers=8`, default `doc_workers=1`.
- Crop Vision runs all eligible crop blocks in a thread pool, default `vision_batch_workers = 60`.
- Brain refinement runs all pages in a thread pool after crop Vision completes, default `brain_batch_workers = 60`.
- Actual workers are capped by job count, so an 11-page PDF uses 11 Brain workers even if the configured limit is 60.
- Brain logs now include actual workers, configured worker limit, context radius, thinking mode, per-page elapsed time plus p50/p90/max and a long-tail warning. If high concurrency is slower, compare the same PDF with Brain workers `60`, `12`, `6` and `3`.

Brain review / audit status:

- New reports use first-class `findings` instead of `suspects`.
- Initial findings come from deterministic checks, validator precheck, quality checks, dual-engine evidence and Vision evidence.
- Brain outputs must use `decisions`, `new_findings` and `op_candidates`.
- Final mutations still go only through checked ops and Validator; Brain cannot write final Markdown directly.

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

PaddleOCR evidence retention is separate from global output retention:

- `--paddleocr-evidence-level standard` is the default and does not request visualization images.
- `debug` / `audit` request PaddleOCR `visualize=true` and preserve final `paddleocr_raw/` even when global output retention is `slim`.
- `audit` additionally writes download audit metadata for PaddleOCR artifacts.
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
- `python docpage2md.py --version`: passed.
- `python -m pytest -q`: 372 passed.
- `python scripts\build_windows_exe.py --dry-run`: passed.
- `python scripts\build_windows_exe.py --distpath %TEMP%\docpage2md_dist_...`: passed; frozen `--docpage2md-cli --version` smoke passed, one-dir size about 68.5 MB after excluding dev/Notebook packages.
- Windows release package now includes `使用说明.md` next to `DocPage2MD.exe`; users should unzip the whole `DocPage2MD` folder instead of copying the exe alone.
- `git diff --check`: passed, with only CRLF conversion warnings.
- GUI construction smoke passed: `DocPage2MdGui()` can construct, update idle tasks and destroy cleanly after the input table/provider/cost redesign.
- Live `dual_hybrid` upload validation for `tests/热统笔记.pdf` now requires explicit user approval because it uploads private pages to MinerU/PaddleOCR/model APIs. After approval on 2026-06-26, real validation ran successfully:
  - `markdown_output/live_dual_range_verify_20260626/热统笔记_p001_020_dual_live`: page range `1-20`, single selected chunk, `status=ok`, `pages=20`.
  - `markdown_output/live_dual_chunk_verify_20260626/热统笔记_p001_020_dual_chunk_live`: page range `1-20`, forced chunk size `10`, real chunks `1-10` and `11-20`; final merge produced 20 slides and FULL Markdown, cleaned temporary chunk dirs, and exposed a generic figure-details math delimiter bug on page 4.
  - `markdown_output/live_dual_page4_fix_verify_20260626/热统笔记_p001_005_page4_fix`: page range `1-5` after renderer/formula fix, `status=ok`, `pages_failed=0`, `fail_open_pages=0`.
  - `markdown_output/live_dual_chunk_final_verify_20260626/热统笔记_p001_005_dual_chunk_final`: page range `1-5`, forced chunk size `3`, real chunks `1-3` and `4-5`; final merge produced 5 slides and FULL Markdown, cleaned temporary chunk dirs, and final Markdown scan found no `[mineru]` / `[paddleocr]`, Traceback, token, `<details open>` or adjacent `$\Sigma$$...` math fragments.
- Safe local validation for the same 122-page PDF passed: page count was readable, `--page-ranges 1-20` produced a single selected chunk `1-20`, and all-pages dual planning produced `1-100`, `101-122`; this proves the local range/chunk planning no longer rejects a short selected range from a long PDF.
- Pseudo long-document acceptance is covered by `test_cli_run_chunked_dual_pdf_pseudo_long_document_merge`: a 10-page fixture is forced into two 5-page chunks, fake MinerU/PaddleOCR artifacts are returned for each chunk, and the real `_run_chunked_dual_pdf()` path verifies slide renumbering, FULL merge, `dual_parser.chunks`, `chunked_merge`, asset rewriting and slim-mode chunk cleanup without uploading private documents.
- Figure details renderer and dual chunk merge now repair adjacent inline math delimiters such as `$\\Sigma$$J \\neq 0$` before final Markdown validation/output, including multiline fragments created during chunk merge.
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
- Latest GUI dual full smoke:
  - Output: `markdown_output/gui_full_pdf_smoke`.
  - `群论笔记3.1`: crop Vision 70 blocks about `38.9s`; Brain 13 pages about `124.1s`.
  - `群论笔记4.1`: crop Vision 47 blocks about `12.8s`; Brain 11 pages about `91.6s`.
  - `群论笔记4.1` Brain per-page durations were roughly min `34.9s`, median `52.6s`, max `91.6s`; `群论笔记3.1` was roughly min `25.1s`, median `58.9s`, max `124.1s`.
  - Conclusion: page-level parallelism is present, but high provider concurrency can create long-tail latency. Use the GUI presets for controlled A/B tests.
- Controlled Brain concurrency A/B:
  - Output: `markdown_output/concurrency_ab_4_1_brain6/dual_4_1_brain6`.
  - Reused existing `群论笔记4.1` MinerU/PaddleOCR artifacts, so the comparison targets Vision/Brain refinement rather than parser upload/parse time.
  - With Vision workers `60` and Brain workers `6`, Brain total was about `94.7s`, p50 `39.2s`, p90 `50.8s`, max `53.6s`, tail ratio `1.37`.
  - The previous workers `11` run had Brain total about `91.6s`, median about `52.6s`, max about `91.6s`. Lower concurrency reduced the worst single-page tail but did not reduce total wall time in this sample.
  - Final Markdown uses default-closed `<details>` blocks and passed the no-key/no-traceback/no-reasoning/no-validator-diagnostics checks.
- Controlled Brain thinking A/B:
  - Output: `markdown_output/concurrency_ab_4_1_fast_brain/dual_4_1_fast_brain`.
  - Reused the same `群论笔记4.1` MinerU/PaddleOCR artifacts, `dual_hybrid`, balanced profile, Vision workers `60`, Brain workers `60`.
  - Actual Brain workers were `11` because the PDF has 11 pages; configured limit stayed `60`.
  - With default fast mode (`brain_thinking=disabled`), Brain total was about `12.2s`, p50 `8.4s`, p90 `11.9s`, max `12.1s`.
  - This replaced the old thinking path that took about `91.6s`; the major single-PDF speed fix is disabling Brain thinking by default, not lowering concurrency.
  - Output report status `ok`, `engine_mode=dual_hybrid`, `models.brain.thinking.mode=disabled`; final Markdown scan found no key names, tracebacks, validator text or reasoning text.
- Contract/evidence-review verification:
  - Output: `markdown_output/real_contract_fix_smoke/real_contract_fix_4_1_v3`.
  - Reused existing `群论笔记4.1` MinerU/PaddleOCR artifacts, `dual_hybrid`, balanced profile, Vision workers `60`, Brain workers `60`, Brain thinking disabled.
  - `paddleocr` origin is accepted by PageIR contract; `run_report.json` has `contract_error_codes={}` and no bad page IR contract errors.
  - Brain remains context-aware but local policy now rejects missing evidence fields, low-confidence replacements, missing target blocks/spans and whole Markdown rewrites.
  - Final Markdown scan found no API key, traceback, reasoning text, validator text, provider error, `[mineru]` / `[paddleocr]` candidate labels, `<details open>` or raw figure JSON keys.
  - Page 3 figure is preserved as a default-closed Chinese `<details>` block.
  - Performance note: this run took longer because crop Vision had provider long-tail latency. 48 crop Vision blocks took about `65.9s`; Brain 11 pages took about `20.7s`.
- Findings/context-window verification:
  - Output: `markdown_output/findings_brain_window_verify/dual_4_1_findings_window_v3`.
  - Reused existing `群论笔记4.1` MinerU/PaddleOCR artifacts, `dual_hybrid`, balanced profile, Vision workers `60`, Brain workers `60`, `--brain-context-radius 2`, Brain thinking disabled.
  - `run_report.json` has `summary.findings.by_source = {validator_precheck:36, dual_engine_diff:138, vision_crop_evidence:48, deterministic_detector:2}`.
  - `summary.suspects` and `pages[].suspects` are absent; Brain context windows record configured radius `2` and actual context pages `3/4/5`.
  - Final Markdown scan found no `[mineru]` / `[paddleocr]`, Traceback, reasoning text, validator text or `<details open>`.
  - Runtime about `96.8s`: crop Vision 48 blocks about `34.2s`; Brain 11 pages about `61.2s`. This confirms the latest bottleneck is provider long-tail latency, not missing thread parallelism.
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
- Latest GUI dual full smoke:
  - Output: `markdown_output/gui_full_pdf_smoke`.
  - Inputs: `tests/群论笔记3.1.pdf` and `tests/群论笔记4.1.pdf`.
  - Mode: `dual_hybrid`, `vlm+PaddleOCR-VL-1.6`, Vision `qwen3-vl-plus`, Brain `deepseek-v4-flash`.
  - Total batch wall time: about `347.2s`.
  - `群论笔记3.1`: parser prep about `53.5s`, crop Vision `70` blocks about `38.9s`, Brain `13` pages about `124.1s`.
  - `群论笔记4.1`: crop Vision `47` blocks about `12.8s`, Brain `11` pages about `91.6s`.
  - Main bottlenecks: Brain provider long-tail latency and dual parser/PaddleOCR artifact download.
  - Implemented follow-up optimization: same-file dual parser prep now runs MinerU and PaddleOCR concurrently.
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
- Continue real long-PDF validation for `dual_hybrid` chunked merge, including quality/time comparison against `mineru_hybrid` and `paddleocr_hybrid`.
