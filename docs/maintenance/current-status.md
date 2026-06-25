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

DocPage2MD has three processing modes:

- `mineru_only`: call or read MinerU output, render clean Markdown from MinerU layout/json/crops.
- `vision_only`: legacy image-folder flow for page images.
- `hybrid`: MinerU layout/crops first, then crop vision + Brain JSON ops + checked refiner + deterministic renderer.

The Tkinter GUI is the current lightweight desktop entry. It supports local single file, multiple files, folder batch, MinerU artifact and URL inputs; Chinese labels/logs; progress/ETA; cost estimate; output folder opening; Vision/Brain worker controls; and model management. The longer-term WebUI plan is tracked in `docs/plans/webui-roadmap.md`.

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
- Change history: `docs/changelog.md`
- Research comparison: `docs/research/comparison-and-docpage2md-roadmap.md`

## Secrets

API keys and tokens must stay out of the repository.

Expected environment variables:

- `MINERU_API_TOKEN`
- `DASHSCOPE_API_KEY`
- `DEEPSEEK_API_KEY`

Logs and reports may record env var names, providers, models, task IDs and trace IDs. They must not record actual token values.

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
- `python -m pytest -q`: 248 passed.
- `git diff --check`: passed, with only CRLF conversion warnings.
- `python -m pytest tests/test_cli.py tests/test_gui.py tests/test_hybrid_enrichment.py tests/test_mineru_pipeline.py tests/test_files_and_session.py tests/test_run_logger.py -q`: 41 passed during GUI/log/performance work.
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
- `群论笔记4.1.pdf` performance from existing full log: total about 114s in `gui_parallel_full_verify`, and about 108s in the later direct run. Breakdown from the later direct run: MinerU about 6.1s, crop Vision 49 blocks about 27.2s, Brain 11 pages about 75.0s, render/report about 0.1s. Bottleneck is Brain provider latency and long-tail page complexity, not missing page-level parallelism.
- New `process.log` output is translated to Chinese by `RunLogger`; old logs generated before this change remain English.
- Brain prompt context now keeps full detail for the target page and compresses neighboring pages, reducing the measured `群论笔记4.1` Brain prompt characters by about 25% before another real API rerun.

## Handoff Notes

- Keep README, architecture docs, changelog and this status file synchronized with code changes.
- If a public command changes, update README and `docs/maintenance/current-status.md`.
- If schema names, output layout or report fields change, update architecture docs and tests together.
- If a real API smoke reveals a quality issue, summarize it in `docs/changelog.md` and keep detailed diagnostics in `run_report.json`, not Markdown.
- Do not read, rewrite, move or delete `markdown_output/已归档`; it is deprecated output retained by user request.
