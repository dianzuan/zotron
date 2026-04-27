"""Normalize provider OCR payloads into Zotron blocks and RAG chunks."""
from __future__ import annotations

import re
from typing import Any

_BLOCK_TYPES = {
    "heading", "paragraph", "table", "figure", "equation", "caption",
    "footnote", "header", "footer", "reference", "unknown",
}
_EVIDENCE_TYPES = {"table", "figure", "equation", "caption"}


def _coerce_type(value: Any) -> str:
    text = str(value or "paragraph").lower()
    aliases = {"text": "paragraph", "title": "heading", "image": "figure"}
    return aliases.get(text, text if text in _BLOCK_TYPES else "unknown")


def _block_text(block: dict[str, Any]) -> str:
    """Return retrieval text for a provider block without embedding binary data."""
    text = block.get("text") or block.get("content") or block.get("markdown")
    if text is None:
        text = block.get("caption") or block.get("label") or block.get("alt_text")
    return str(text or "").strip()


def _evidence_ref(block: dict[str, Any]) -> dict[str, Any]:
    """Return compact chunk-level evidence metadata for a normalized block."""
    ref: dict[str, Any] = {
        "block_id": block.get("block_id"),
        "type": block.get("type"),
        "page": block.get("page"),
    }
    if block.get("bbox") is not None:
        ref["bbox"] = block.get("bbox")
    if block.get("caption"):
        ref["caption"] = block.get("caption")
    if block.get("image_ref"):
        ref["image_ref"] = block.get("image_ref")
    return ref


def _iter_structured_blocks(payload: Any):
    if not isinstance(payload, dict):
        return
    pages = payload.get("pages")
    if isinstance(pages, list):
        for p_idx, page in enumerate(pages):
            page_no = page.get("page") or page.get("page_number") or p_idx + 1
            blocks = page.get("blocks") or page.get("elements") or page.get("layout") or []
            for b_idx, block in enumerate(blocks):
                if isinstance(block, dict):
                    yield p_idx, b_idx, int(page_no), block, f"pages[{p_idx}].blocks[{b_idx}]"
    blocks = payload.get("blocks") or payload.get("elements") or payload.get("layout")
    if isinstance(blocks, list):
        for b_idx, block in enumerate(blocks):
            if isinstance(block, dict):
                page_no = block.get("page") or block.get("page_number") or 1
                yield 0, b_idx, int(page_no), block, f"blocks[{b_idx}]"


def _markdown_blocks(markdown: str):
    section = ""
    order = 0
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", markdown) if p.strip()]
    for idx, para in enumerate(paragraphs):
        heading = re.match(r"^#{1,6}\s+(.+)$", para)
        if heading:
            section = heading.group(1).strip()
            yield idx, order, "heading", section, section
        else:
            yield idx, order, "paragraph", para, section
        order += 1


def blocks_from_provider_payload(
    payload: Any,
    *,
    item_key: str,
    attachment_key: str,
    provider: str,
) -> list[dict[str, Any]]:
    """Return normalized Zotron block dictionaries from provider raw data.

    Structured provider fields are preferred. Markdown is only a fallback when
    the provider exposes no block/page structure.
    """
    blocks: list[dict[str, Any]] = []
    structured = list(_iter_structured_blocks(payload) or [])
    section = ""
    for _p_idx, b_idx, page_no, block, source_ref in structured:
        block_type = _coerce_type(block.get("type") or block.get("category"))
        text = _block_text(block)
        if not text:
            continue
        caption = str(block.get("caption") or (text if block_type in {"figure", "caption"} else ""))
        if block_type == "heading":
            section = text
        blocks.append({
            "block_id": f"{attachment_key}:p{page_no}:b{b_idx}",
            "attachment_key": attachment_key,
            "item_key": item_key,
            "type": block_type,
            "page": page_no,
            "bbox": block.get("bbox") or block.get("box"),
            "reading_order": int(block.get("reading_order", b_idx)),
            "section_heading": block.get("section_heading") or section,
            "text": text,
            "caption": caption,
            "image_ref": block.get("image_ref") or block.get("image") or block.get("image_path") or "",
            "source_provider": provider,
            "source_ref": source_ref,
            "confidence": block.get("confidence"),
            "provenance_strength": "structured",
        })
    if blocks:
        return blocks

    markdown = ""
    if isinstance(payload, dict):
        markdown = str(payload.get("markdown") or payload.get("md_results") or payload.get("result") or "")
    elif isinstance(payload, str):
        markdown = payload
    for para_idx, order, block_type, text, section in _markdown_blocks(markdown):
        blocks.append({
            "block_id": f"{attachment_key}:p0:b{order}",
            "attachment_key": attachment_key,
            "item_key": item_key,
            "type": block_type,
            "page": None,
            "bbox": None,
            "reading_order": order,
            "section_heading": "" if block_type == "heading" else section,
            "text": text,
            "caption": "",
            "image_ref": "",
            "source_provider": provider,
            "source_ref": f"markdown:{para_idx}",
            "confidence": None,
            "provenance_strength": "markdown_fallback",
        })
    return blocks


def chunks_from_blocks(blocks: list[dict[str, Any]], *, max_chars: int = 1000) -> list[dict[str, Any]]:
    """Build section-aware RAG chunks from normalized blocks."""
    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_section = None
    current_len = 0
    attachment_key = str(blocks[0].get("attachment_key", "att")) if blocks else "att"

    def flush() -> None:
        nonlocal current, current_len
        if not current:
            return
        text = "\n\n".join(str(b.get("text", "")) for b in current).strip()
        pages: list[int] = []
        for block in current:
            page = block.get("page")
            if isinstance(page, int):
                pages.append(page)
        chunk_index = len(chunks)
        strengths = {str(b.get("provenance_strength") or "structured") for b in current}
        provenance_strength = strengths.pop() if len(strengths) == 1 else "mixed"
        chunks.append({
            "chunk_id": f"{attachment_key}:c{chunk_index}",
            "item_key": current[0].get("item_key"),
            "attachment_key": current[0].get("attachment_key"),
            "block_ids": [b.get("block_id") for b in current],
            "block_types": [str(b.get("type") or "unknown") for b in current],
            "section_heading": current[0].get("section_heading", ""),
            "page_start": min(pages) if pages else None,
            "page_end": max(pages) if pages else None,
            "text": text,
            "char_start": 0,
            "char_end": len(text),
            "level": "chunk",
            "evidence_refs": [_evidence_ref(b) for b in current],
            "provenance_strength": provenance_strength,
        })
        current = []
        current_len = 0

    for block in blocks:
        if block.get("type") == "heading":
            flush()
            current_section = block.get("text")
            continue
        section = block.get("section_heading") or current_section or ""
        block = {**block, "section_heading": section}
        text_len = len(str(block.get("text", "")))
        if current and (section != current_section or current_len + text_len > max_chars):
            flush()
        current_section = section
        current.append(block)
        current_len += text_len
    flush()
    return chunks
