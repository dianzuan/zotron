"""Tests for OCRProcessor — collection traversal, note detection, HTML output."""

from __future__ import annotations

from unittest.mock import MagicMock


from zotero_bridge.ocr.processor import OCRProcessor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_processor() -> tuple[OCRProcessor, MagicMock, MagicMock]:
    rpc = MagicMock()
    engine = MagicMock()
    processor = OCRProcessor(rpc=rpc, engine=engine)
    return processor, rpc, engine


# ---------------------------------------------------------------------------
# find_collection_id
# ---------------------------------------------------------------------------


def test_find_collection_id():
    """Flat tree — finds the collection by name and returns its id."""
    processor, rpc, _ = _make_processor()
    rpc.call.return_value = [
        {"id": 1, "name": "Alpha", "children": []},
        {"id": 2, "name": "Beta", "children": []},
        {"id": 3, "name": "Gamma", "children": []},
    ]
    result = processor.find_collection_id("Beta")
    assert result == 2
    rpc.call.assert_called_once_with("collections.tree")


def test_find_collection_id_nested():
    """Nested tree — finds the collection inside children."""
    processor, rpc, _ = _make_processor()
    rpc.call.return_value = [
        {
            "id": 10,
            "name": "Parent",
            "children": [
                {"id": 11, "name": "Child A", "children": []},
                {
                    "id": 12,
                    "name": "Child B",
                    "children": [
                        {"id": 13, "name": "Grandchild", "children": []}
                    ],
                },
            ],
        }
    ]
    result = processor.find_collection_id("Grandchild")
    assert result == 13


def test_find_collection_not_found():
    """Empty tree — returns None when collection does not exist."""
    processor, rpc, _ = _make_processor()
    rpc.call.return_value = []
    result = processor.find_collection_id("Missing")
    assert result is None


# ---------------------------------------------------------------------------
# has_ocr_note
# ---------------------------------------------------------------------------


def test_has_ocr_note_true():
    """Note with 'ocr' tag exists — returns True."""
    processor, rpc, _ = _make_processor()
    rpc.call.return_value = [
        {"id": 100, "note": "<p>some content</p>", "tags": ["ocr", "imported"]},
    ]
    assert processor.has_ocr_note(42) is True
    rpc.call.assert_called_once_with("notes.get", {"parentId": 42})


def test_has_ocr_note_false():
    """Note exists but no 'ocr' tag — returns False."""
    processor, rpc, _ = _make_processor()
    rpc.call.return_value = [
        {"id": 101, "note": "<p>manual note</p>", "tags": ["manual"]},
    ]
    assert processor.has_ocr_note(42) is False


def test_has_ocr_note_no_notes():
    """No notes at all — returns False."""
    processor, rpc, _ = _make_processor()
    rpc.call.return_value = []
    assert processor.has_ocr_note(42) is False


# ---------------------------------------------------------------------------
# format_note_html
# ---------------------------------------------------------------------------


def test_format_note_html():
    """HTML output contains title, provider, and markdown-converted content."""
    processor, _, _ = _make_processor()
    markdown_input = "## Section\n\nHello **world**."
    html = processor.format_note_html(
        title="My Paper",
        markdown=markdown_input,
        provider="GLMEngine",
        page_count=12,
    )
    assert "<h1>OCR: My Paper</h1>" in html
    assert "GLMEngine" in html
    assert "12 pages" in html
    # markdown library converts ## → <h2> and **word** → <strong>
    assert "<h2>" in html
    assert "<strong>world</strong>" in html
    assert "<hr/>" in html
