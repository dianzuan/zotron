"""Section-aware text chunking for Chinese academic papers."""

from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Section heading patterns
# ---------------------------------------------------------------------------

_HEADING_PATTERNS: list[re.Pattern] = [
    re.compile(r"^#{1,3}\s+(.+)$", re.MULTILINE),
    re.compile(r"^([一二三四五六七八九十]+、.+)$", re.MULTILINE),
    re.compile(r"^(\d+[\.\s]+.{2,})$", re.MULTILINE),
    # 第X章/节 pattern: the chapter/section word must immediately end the heading
    # or be followed by whitespace + a short title (≤20 chars) to avoid
    # matching content lines like "第一节的内容在这里，描述研究方法。"
    re.compile(r"^(第[一二三四五六七八九十\d]+[章节部分](?:\s+.{0,20})?)$", re.MULTILINE),
]


def _split_into_sections(text: str) -> list[tuple[str, str]]:
    """Split text at heading positions.

    Returns a list of (section_title, section_body) pairs.
    Text before the first heading is returned with an empty title.
    """
    # Collect all heading match positions: (start, end, title)
    headings: list[tuple[int, int, str]] = []
    for pattern in _HEADING_PATTERNS:
        for m in pattern.finditer(text):
            title = m.group(1) if m.lastindex and m.lastindex >= 1 else m.group(0)
            headings.append((m.start(), m.end(), title.strip()))

    if not headings:
        return [("", text)]

    # Sort by position, deduplicate overlapping matches (keep longest)
    headings.sort(key=lambda h: h[0])
    deduped: list[tuple[int, int, str]] = []
    for h in headings:
        if deduped and h[0] < deduped[-1][1]:
            # overlapping with previous — keep whichever ends later
            if h[1] > deduped[-1][1]:
                deduped[-1] = h
        else:
            deduped.append(h)

    sections: list[tuple[str, str]] = []
    # Text before first heading
    pre = text[: deduped[0][0]].strip()
    if pre:
        sections.append(("", pre))

    for i, (start, end, title) in enumerate(deduped):
        next_start = deduped[i + 1][0] if i + 1 < len(deduped) else len(text)
        body = text[end:next_start].strip()
        sections.append((title, body))

    return sections


# ---------------------------------------------------------------------------
# Recursive splitting
# ---------------------------------------------------------------------------

def _recursive_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split *text* into chunks of at most *chunk_size* characters.

    Tries paragraph boundaries first, then sentence boundaries.
    Carries *overlap* characters from the end of the previous chunk.
    """
    if len(text) <= chunk_size:
        return [text] if text else []

    # Try splitting on paragraph boundaries
    para_sep = re.compile(r"\n\n+")
    paragraphs = para_sep.split(text)

    if len(paragraphs) > 1:
        return _merge_splits(paragraphs, chunk_size, overlap)

    # Fall back to sentence boundaries
    sent_sep = re.compile(r"(?<=[。！？.!?\n])")
    sentences = [s for s in sent_sep.split(text) if s]

    if len(sentences) > 1:
        return _merge_splits(sentences, chunk_size, overlap)

    # Hard split as last resort
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def _merge_splits(splits: list[str], chunk_size: int, overlap: int) -> list[str]:
    """Greedily merge *splits* into chunks up to *chunk_size*, with *overlap*."""
    chunks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for part in splits:
        part_len = len(part)
        if current_len + part_len > chunk_size and current_parts:
            chunk_text = "\n\n".join(current_parts)
            chunks.append(chunk_text)
            # Build overlap from end of current chunk
            tail = chunk_text[-overlap:] if overlap else ""
            current_parts = [tail, part] if tail else [part]
            current_len = len(tail) + part_len
        else:
            current_parts.append(part)
            current_len += part_len

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
) -> list[dict]:
    """Split *text* into section-aware chunks.

    Parameters
    ----------
    text:
        Full document text (Markdown or plain).
    chunk_size:
        Maximum characters per chunk.
    overlap:
        Characters of overlap carried from the previous chunk.

    Returns
    -------
    list[dict]
        Each element has keys ``"text"``, ``"section"``, and ``"chunk_index"``.
    """
    if not text or not text.strip():
        return []

    sections = _split_into_sections(text)
    results: list[dict] = []
    idx = 0

    for section_title, body in sections:
        if not body:
            continue
        sub_chunks = _recursive_split(body, chunk_size, overlap)
        for chunk in sub_chunks:
            if chunk.strip():
                results.append(
                    {
                        "text": chunk,
                        "section": section_title,
                        "chunk_index": idx,
                    }
                )
                idx += 1

    return results
