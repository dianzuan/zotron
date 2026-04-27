from __future__ import annotations

from zotron.ocr.normalize import blocks_from_provider_payload, chunks_from_blocks


def test_blocks_from_structured_provider_payload_keeps_page_bbox_and_source_ref():
    payload = {
        "pages": [
            {
                "page": 2,
                "blocks": [
                    {
                        "type": "paragraph",
                        "text": "研究设计内容",
                        "bbox": [72, 210, 510, 286],
                        "confidence": 0.94,
                    }
                ],
            }
        ]
    }

    blocks = blocks_from_provider_payload(
        payload,
        item_key="ITEM1",
        attachment_key="ATT1",
        provider="mineru",
    )

    assert blocks == [
        {
            "block_id": "ATT1:p2:b0",
            "attachment_key": "ATT1",
            "item_key": "ITEM1",
            "type": "paragraph",
            "page": 2,
            "bbox": [72, 210, 510, 286],
            "reading_order": 0,
            "section_heading": "",
            "text": "研究设计内容",
            "caption": "",
            "image_ref": "",
            "source_provider": "mineru",
            "source_ref": "pages[0].blocks[0]",
            "confidence": 0.94,
            "provenance_strength": "structured",
        }
    ]


def test_blocks_from_markdown_payload_is_fallback_not_sole_truth():
    payload = {"markdown": "# 方法\n\n第一段。\n\n第二段。"}

    blocks = blocks_from_provider_payload(
        payload,
        item_key="ITEM1",
        attachment_key="ATT1",
        provider="glm",
    )

    assert [b["type"] for b in blocks] == ["heading", "paragraph", "paragraph"]
    assert blocks[0]["text"] == "方法"
    assert blocks[1]["section_heading"] == "方法"
    assert blocks[1]["source_ref"] == "markdown:1"


def test_chunks_from_blocks_preserves_block_ids_pages_and_section():
    blocks = [
        {"block_id": "ATT1:p1:b0", "item_key": "ITEM1", "attachment_key": "ATT1", "type": "paragraph", "page": 1, "section_heading": "Intro", "text": "Alpha"},
        {"block_id": "ATT1:p1:b1", "item_key": "ITEM1", "attachment_key": "ATT1", "type": "paragraph", "page": 1, "section_heading": "Intro", "text": "Beta"},
        {"block_id": "ATT1:p2:b0", "item_key": "ITEM1", "attachment_key": "ATT1", "type": "paragraph", "page": 2, "section_heading": "Methods", "text": "Gamma"},
    ]

    chunks = chunks_from_blocks(blocks, max_chars=20)

    assert chunks[0]["chunk_id"] == "ATT1:c0"
    assert chunks[0]["block_ids"] == ["ATT1:p1:b0", "ATT1:p1:b1"]
    assert chunks[0]["section_heading"] == "Intro"
    assert chunks[0]["page_start"] == 1
    assert chunks[0]["page_end"] == 1
    assert chunks[0]["text"] == "Alpha\n\nBeta"
    assert chunks[1]["section_heading"] == "Methods"


def test_structure_first_blocks_preserve_non_text_evidence_without_image_copies():
    payload = {
        "pages": [
            {
                "page": 3,
                "blocks": [
                    {"type": "heading", "text": "结果"},
                    {
                        "type": "figure",
                        "caption": "图1 机制示意图",
                        "image_ref": "page3-fig1.png",
                        "bbox": [10, 20, 300, 240],
                    },
                    {
                        "type": "table",
                        "text": "变量&均值\\nX&1.0",
                        "caption": "表1 描述统计",
                        "bbox": [40, 260, 520, 410],
                    },
                    {"type": "equation", "text": "y = \\alpha + \\beta x"},
                    {"type": "caption", "text": "注：括号内为稳健标准误。"},
                ],
            }
        ]
    }

    blocks = blocks_from_provider_payload(
        payload,
        item_key="ITEM1",
        attachment_key="ATT1",
        provider="mineru",
    )

    assert [block["type"] for block in blocks] == ["heading", "figure", "table", "equation", "caption"]
    assert blocks[1]["text"] == "图1 机制示意图"
    assert blocks[1]["caption"] == "图1 机制示意图"
    assert blocks[1]["image_ref"] == "page3-fig1.png"
    assert "image_bytes" not in blocks[1]
    assert blocks[1]["bbox"] == [10, 20, 300, 240]
    assert all(block["section_heading"] == "结果" for block in blocks[1:])
    assert {block["provenance_strength"] for block in blocks} == {"structured"}


def test_chunks_do_not_cross_heading_boundaries_and_keep_evidence_policy_metadata():
    blocks = [
        {"block_id": "ATT1:p1:b0", "item_key": "ITEM1", "attachment_key": "ATT1", "type": "heading", "page": 1, "section_heading": "", "text": "引言"},
        {"block_id": "ATT1:p1:b1", "item_key": "ITEM1", "attachment_key": "ATT1", "type": "paragraph", "page": 1, "bbox": [1, 2, 3, 4], "section_heading": "引言", "text": "Alpha"},
        {"block_id": "ATT1:p1:b2", "item_key": "ITEM1", "attachment_key": "ATT1", "type": "table", "page": 1, "bbox": [5, 6, 7, 8], "section_heading": "引言", "text": "A|B", "caption": "表1"},
        {"block_id": "ATT1:p2:b0", "item_key": "ITEM1", "attachment_key": "ATT1", "type": "heading", "page": 2, "section_heading": "", "text": "方法"},
        {"block_id": "ATT1:p2:b1", "item_key": "ITEM1", "attachment_key": "ATT1", "type": "figure", "page": 2, "bbox": [9, 10, 11, 12], "section_heading": "方法", "text": "图1", "caption": "图1", "image_ref": "fig1.png"},
        {"block_id": "ATT1:p2:b2", "item_key": "ITEM1", "attachment_key": "ATT1", "type": "equation", "page": 2, "section_heading": "方法", "text": "y=x"},
    ]

    chunks = chunks_from_blocks(blocks, max_chars=1000)

    assert len(chunks) == 2
    assert chunks[0]["section_heading"] == "引言"
    assert chunks[0]["block_ids"] == ["ATT1:p1:b1", "ATT1:p1:b2"]
    assert chunks[0]["block_types"] == ["paragraph", "table"]
    assert chunks[0]["page_start"] == 1
    assert chunks[0]["page_end"] == 1
    assert chunks[1]["section_heading"] == "方法"
    assert chunks[1]["block_ids"] == ["ATT1:p2:b1", "ATT1:p2:b2"]
    assert chunks[1]["block_types"] == ["figure", "equation"]
    assert chunks[1]["evidence_refs"][0] == {
        "block_id": "ATT1:p2:b1",
        "type": "figure",
        "page": 2,
        "bbox": [9, 10, 11, 12],
        "caption": "图1",
        "image_ref": "fig1.png",
    }


def test_markdown_fallback_blocks_and_chunks_are_marked_weaker_provenance():
    blocks = blocks_from_provider_payload(
        "# 摘要\n\n这是一段纯 Markdown。",
        item_key="ITEM1",
        attachment_key="ATT1",
        provider="custom",
    )

    assert {block["provenance_strength"] for block in blocks} == {"markdown_fallback"}
    chunks = chunks_from_blocks(blocks)
    assert chunks[0]["provenance_strength"] == "markdown_fallback"
