# Hybrid Region Revision Roadmap

Last updated: 2026-06-24

## Background

The current `hybrid` pipeline uses MinerU layout/content/crop outputs as the primary visual evidence. Crop Vision only re-checks blocks that already have image evidence and whose block type is one of:

- `formula_block`
- `table`
- `figure_note`
- `image_ref`

This is useful, but incomplete. Some formulas, figures, charts or tables can be classified by MinerU as ordinary text, or can have incomplete crop images. In those cases, the current pipeline may detect a downstream warning, but it does not automatically re-read the wider page area.

## Current Gap

The current implementation does not yet provide a full closed loop for visual recovery:

- It does not reliably keep a full page image for each MinerU page.
- It does not crop a new image from a block `bbox`.
- It does not expand a suspicious crop with padding and retry Vision.
- It does not fall back to full-page Vision when local region evidence is insufficient.
- Validator warnings such as `target_formula_block_missing`, `target_table_block_missing`, `target_figure_block_missing`, or `target_image_ref_block_missing` do not trigger an automatic second-pass visual repair.

The validator can warn that content was lost, and fail-open can keep conservative Markdown, but the pipeline does not yet use that warning to fetch better visual evidence.

## Goal

Add a second-pass visual recovery layer to `hybrid`:

```text
MinerU initial parse
  -> build PageIR/BlockIR with bbox and crop refs
  -> normal crop Vision
  -> Brain JSON ops + checked refiner
  -> renderer + validator
  -> if visual/content coverage is suspicious:
       1. crop a wider region from the full page image
       2. retry Vision on the expanded region
       3. if still unresolved, ask Vision to inspect the full page around the target bbox
       4. re-run safe refinement and validation
```

The goal is not to let Vision rewrite the whole page. The goal is to obtain better local evidence for blocks that MinerU likely missed, clipped or misclassified.

## Required Concepts

- **Full page image**: a rendered image of the entire PDF page, stored in output assets and referenced by `page_image_ref`.
- **bbox**: bounding box coordinates for a block, usually `[x0, y0, x1, y1]`.
- **Expanded region crop**: a new crop generated from the full page image by expanding the block bbox with a configurable margin.
- **Region retry**: a second Vision call using the expanded region.
- **Full-page targeted retry**: a fallback Vision call using the full page image and explicit instructions to inspect only the target bbox neighborhood.

## Proposed Design

### 1. Store Full Page Evidence

Ensure each MinerU page has a stable full-page image reference:

- `page_image_ref`
- `assets/pages/page_001.png`
- image dimensions
- coordinate transform between MinerU page coordinates and rendered image pixels

If MinerU artifact already contains page images, reuse them. If not, render PDF pages locally in a controlled way.

### 2. Preserve and Normalize Block Coordinates

Keep normalized block coordinates in every block:

- original MinerU bbox
- page size
- pixel bbox after coordinate transform
- source of bbox: `layout`, `content_list`, or `block_list`

Reject invalid bbox values early and record diagnostics in `run_report.json`.

### 3. Generate Expanded Region Crops

Add a local crop helper:

```text
expanded_bbox = bbox + padding
padding = max(absolute pixels, percentage of bbox size)
expanded_bbox is clipped to page bounds
```

Suggested defaults:

- formula: 20% horizontal and 35% vertical padding
- table: 10% padding
- figure/chart: 15% padding
- suspicious paragraph: 10% padding

Generated files should live under:

```text
assets/regions/
```

### 4. Detect Recovery Candidates

Candidate signals:

- crop image is missing for a visual block
- crop image exists but is very small
- formula block has uncertain formula warnings
- table block is unreliable or degraded
- paragraph/list text looks formula-heavy
- paragraph/list text looks like figure description
- validator reports missing formula/table/figure/image-ref blocks
- Brain requested `mark_uncertain` for a block that has bbox evidence

### 5. Retry Vision With Better Evidence

Retry order:

1. Existing MinerU crop, current behavior.
2. Expanded region crop from full page image.
3. Full-page targeted retry with bbox and nearby text.

The prompt must forbid whole-page rewriting. It should return structured JSON only, with block id, confidence and evidence source.

### 6. Re-apply Through Checked Refinement

Results from region Vision should update PageIR only through checked operations:

- replace formula text
- convert paragraph to formula/table/figure when evidence is strong
- attach image reference when text extraction is unreliable
- mark uncertain when the region is visible but not confidently readable

The renderer and validator must run again after recovery.

## Report Fields

Add audit details to `run_report.json`:

- recovery candidates
- trigger reason
- bbox before and after expansion
- region crop path
- full-page fallback used or not
- Vision model and request id
- accepted/rejected updates
- validator before/after

Do not write debug diagnostics into user Markdown.

## Implementation Phases

### Phase 1: Evidence Plumbing

- Preserve `page_image_ref`.
- Add full-page image assets.
- Add coordinate conversion helpers.
- Add tests for bbox conversion and clipping.

### Phase 2: Expanded Crop Generation

- Add `assets/regions/`.
- Generate expanded crops from bbox.
- Add tests with synthetic page images.

### Phase 3: Recovery Candidate Detection

- Convert validator warnings and block quality warnings into recovery candidates.
- Keep recovery disabled by default behind a config flag until tested.

### Phase 4: Region Vision Retry

- Add expanded-region Vision backend.
- Add structured JSON parser and evidence fields.
- Keep operations white-listed and checked.

### Phase 5: Full-Page Targeted Fallback

- Add full-page targeted retry only when region retry fails or evidence is missing.
- Control cost with max retries per page and per document.

## Acceptance Criteria

- A formula misclassified as text but with a valid bbox can be retried as an expanded region.
- A clipped formula crop can be retried with a wider bbox.
- A missing table image can fall back to bbox-based region Vision.
- Recovery never lets AI directly rewrite a full page Markdown.
- If recovery fails, Markdown remains conservative and `run_report.json` explains why.
- Existing `mineru_only` behavior remains unchanged.
- `markdown_output/已归档` remains untouched.
