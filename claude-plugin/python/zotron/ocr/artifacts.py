"""Compatibility layer for OCR artifact helpers.

The canonical OCR/RAG artifact API lives in :mod:`zotron.artifacts`.  This
module intentionally re-exports the legacy OCR names so older callers can keep
importing ``zotron.ocr.artifacts`` while sharing the same implementation.
"""
from __future__ import annotations

from zotron.artifacts import (
    BLOCKS_SUFFIX,
    CHUNKS_SUFFIX,
    EMBEDDING_SUFFIX,
    OCR_RAW_SUFFIX,
    ProviderRawArtifact,
    artifact_path,
    is_metadata_stale,
    metadata_for_chunks,
    read_blocks_jsonl,
    read_chunks_jsonl,
    read_embedding_npz,
    text_sha256,
    write_blocks_jsonl,
    write_chunks_jsonl,
    write_embedding_npz,
    write_provider_raw_zip,
)

__all__ = [
    "BLOCKS_SUFFIX",
    "CHUNKS_SUFFIX",
    "EMBEDDING_SUFFIX",
    "OCR_RAW_SUFFIX",
    "ProviderRawArtifact",
    "artifact_path",
    "is_metadata_stale",
    "metadata_for_chunks",
    "read_blocks_jsonl",
    "read_chunks_jsonl",
    "read_embedding_npz",
    "text_sha256",
    "write_blocks_jsonl",
    "write_chunks_jsonl",
    "write_embedding_npz",
    "write_provider_raw_zip",
]
