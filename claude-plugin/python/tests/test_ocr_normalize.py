"""Tests for provider raw -> normalized blocks/chunks conversion."""

from zotron.ocr.normalize import build_chunks_from_blocks, normalize_provider_raw


def test_normalize_structured_provider_blocks_preserves_provenance_not_markdown_only():
    raw = {
        "markdown": "# Ignored fallback\n\nThis should not be the only truth.",
        "blocks": [
            {
                "type": "paragraph",
                "page": 12,
                "bbox": [72, 210, 510, 286],
                "text": "本文利用世界投入产出表和金融风险指标...",
                "section_heading": "三、研究设计",
                "reading_order": 8,
                "confidence": 0.94,
                "source_ref": "content_list_v2.json:42",
            }
        ],
    }

    blocks = normalize_provider_raw(
        provider="mineru", raw=raw, item_key="ITEM", attachment_key="ATT"
    )

    assert len(blocks) == 1
    block = blocks[0]
    assert block["block_id"] == "ATT:p12:b08"
    assert block["item_key"] == "ITEM"
    assert block["attachment_key"] == "ATT"
    assert block["bbox"] == [72, 210, 510, 286]
    assert block["source_provider"] == "mineru"
    assert block["source_ref"] == "content_list_v2.json:42"
    assert block["text"].startswith("本文利用")


def test_markdown_pages_are_fallback_blocks_with_page_provenance():
    blocks = normalize_provider_raw(
        provider="glm",
        raw={"pages": [{"page": 3, "markdown": "# 方法\n\n第一段。\n\n第二段。"}]},
        item_key="ITEM",
        attachment_key="ATT",
    )

    assert [b["type"] for b in blocks] == ["heading", "paragraph", "paragraph"]
    assert {b["page"] for b in blocks} == {3}
    assert all(b["source_provider"] == "glm" for b in blocks)


def test_build_chunks_from_blocks_keeps_section_boundaries_and_block_ids():
    blocks = [
        {"block_id": "ATT:p1:b01", "item_key": "ITEM", "attachment_key": "ATT", "type": "heading", "page": 1, "text": "一、引言", "section_heading": "一、引言"},
        {"block_id": "ATT:p1:b02", "item_key": "ITEM", "attachment_key": "ATT", "type": "paragraph", "page": 1, "text": "引言正文", "section_heading": "一、引言"},
        {"block_id": "ATT:p2:b01", "item_key": "ITEM", "attachment_key": "ATT", "type": "heading", "page": 2, "text": "二、方法", "section_heading": "二、方法"},
        {"block_id": "ATT:p2:b02", "item_key": "ITEM", "attachment_key": "ATT", "type": "paragraph", "page": 2, "text": "方法正文", "section_heading": "二、方法"},
    ]

    chunks = build_chunks_from_blocks(blocks, max_chars=1000)

    assert len(chunks) == 2
    assert chunks[0]["chunk_id"] == "ATT:c000001"
    assert chunks[0]["section_heading"] == "一、引言"
    assert chunks[0]["block_ids"] == ["ATT:p1:b01", "ATT:p1:b02"]
    assert chunks[0]["page_start"] == 1
    assert chunks[0]["page_end"] == 1
    assert chunks[1]["section_heading"] == "二、方法"
