# Zotron RAG/OCR TDD Tasklist

Date: 2026-04-27

This tasklist turns the roadmap into executable TDD lanes. The current target is to make OCR/RAG a real artifact pipeline, not just docs or note preview.

## Current Baseline

- `zotron ping` works in the local environment.
- Codex plugin packaging now lives in the same `claude-plugin/` root as Claude Code packaging.
- `zotron-rag hits` exists, but still reads the legacy JSON vector store.
- OCR provider classes currently return markdown/text and do not preserve raw provider results as first-class artifacts.
- `OCRProcessor` still writes an HTML note as the main output.
- Artifact helpers exist but are split across `zotron/artifacts.py` and `zotron/ocr/artifacts.py`.

## TDD Lanes

### Lane 1: Artifact API Consolidation

Goal: one stable artifact API for OCR/RAG.

Tests first:

- Existing `test_artifacts.py`, `test_artifacts_storage.py`, and `test_storage_artifacts.py` continue to pass.
- New tests cover one canonical API for:
  - provider raw zip round trip;
  - blocks JSONL round trip;
  - chunks JSONL round trip;
  - embedding NPZ round trip;
  - stale metadata detection.

Implementation:

- Consolidate duplicate artifact helpers.
- Keep backward-compatible aliases where existing tests or callers use them.
- Prefer a single source of truth in `zotron/artifacts.py`; keep `zotron/ocr/artifacts.py` as a thin compatibility layer if needed.

### Lane 2: OCR Result Contract and Provider Registry

Goal: providers return raw evidence, not only markdown.

Tests first:

- `create_engine("glm")`, `create_engine("qwen")`, `create_engine("custom")` still work.
- Add mock-response tests proving each provider returns an `OCRResult` with:
  - `provider`;
  - `model`;
  - `raw_payload`;
  - `markdown` or `text`;
  - optional `files`;
  - provenance strength marker.
- Unknown provider and missing credential errors remain explicit.

Implementation:

- Introduce `OCRResult` and provider registry/spec.
- Convert GLM/Qwen/custom wrappers to return `OCRResult`.
- Add scaffold adapters for roadmap providers where API details are not fully stable yet, with mockable parser functions:
  - MinerU;
  - PaddleOCR-VL;
  - Mistral OCR.

### Lane 3: OCR Processor Artifact Pipeline

Goal: OCR writes Zotero-native artifacts and keeps notes as preview only.

Tests first:

- Mock Zotero RPC verifies processing one item writes:
  - `<item-key>.zotron-ocr.raw.zip`;
  - `<item-key>.zotron-blocks.jsonl`;
  - `<item-key>.zotron-chunks.jsonl`.
- Temporary files are cleaned or staged predictably.
- Existing OCR note behavior remains optional/compatible.
- `zotron-ocr run --collection`, `zotron-ocr rebuild --item`, and legacy `--collection/--item` paths are covered.

Implementation:

- Update `OCRProcessor.process_item` pipeline:
  - locate PDF;
  - run provider;
  - write raw zip;
  - normalize blocks;
  - build chunks;
  - attach artifacts to Zotero;
  - optionally write preview note.
- Add `run` and `rebuild` subcommands while keeping old CLI flags as compatibility.

### Lane 4: Structure-First Chunk Quality

Goal: chunks are evidence spans suitable for academic retrieval.

Tests first:

- Chunking does not cross section boundaries.
- Heading, paragraph, table, figure, equation, caption blocks have predictable policy.
- Every chunk has `chunk_id`, `block_ids`, `section_heading`, page range, and text.

Implementation:

- Strengthen `blocks_from_provider_payload` and `chunks_from_blocks`.
- Preserve image refs/captions/bboxes without copying all images by default.
- Keep fallback markdown chunking clearly marked as weaker provenance.

## Out of Scope for This Team Iteration

- Full embedding provider registry.
- Real network integration tests against MinerU/Paddle/Mistral services.
- `rag.searchHits` JSON-RPC method.
- `zotron-rag migrate-to-zotero`.

These remain roadmap items after the OCR artifact pipeline lands.

## Verification Contract

- Python focused tests for changed OCR/RAG/artifact modules.
- Full Python suite: `cd claude-plugin/python && uv run pytest -q`.
- Node suite: `npm test`.
- TypeScript: `npx tsc --noEmit`.
- Codex plugin manifest and marketplace JSON parse.
- No invalid SKILL frontmatter.
