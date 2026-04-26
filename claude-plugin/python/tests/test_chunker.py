"""Tests for section-aware text chunker."""

from zotero_bridge.rag.chunker import chunk_text


def test_short_text_single_chunk():
    """Short text that fits in one chunk returns a single chunk with empty section."""
    result = chunk_text("Hello world", chunk_size=512, overlap=50)
    assert len(result) == 1
    assert result[0]["text"] == "Hello world"
    assert result[0]["section"] == ""
    assert result[0]["chunk_index"] == 0


def test_section_aware_split():
    """Text with two Markdown headings produces chunks with correct section labels."""
    text = (
        "# 一、引言\n\n"
        "引言内容在这里，讨论研究背景和动机。\n\n"
        "# 二、文献综述\n\n"
        "文献综述内容，回顾相关研究成果。"
    )
    result = chunk_text(text, chunk_size=512, overlap=50)
    assert len(result) == 2
    sections = [r["section"] for r in result]
    assert "一、引言" in sections
    assert "二、文献综述" in sections


def test_chinese_numbered_sections():
    """Chinese numbered section headings split into the correct number of chunks."""
    text = (
        "一、第一节\n\n"
        "第一节的内容在这里，描述研究方法。\n\n"
        "二、第二节\n\n"
        "第二节的内容在这里，展示实验结果。"
    )
    result = chunk_text(text, chunk_size=512, overlap=50)
    # Should produce at least 2 chunks (one per section)
    assert len(result) >= 2
    sections = [r["section"] for r in result]
    assert any("一、第一节" in s for s in sections)
    assert any("二、第二节" in s for s in sections)


def test_long_section_recursive_split():
    """A very long section body is split into multiple chunks, all with the same section."""
    # Create text longer than chunk_size by repeating sentences
    sentence = "这是一个测试句子，用于验证长文本的分割功能是否正常工作。"
    long_body = "\n\n".join([sentence] * 20)
    text = f"# 引言\n\n{long_body}"
    result = chunk_text(text, chunk_size=200, overlap=20)
    assert len(result) > 1
    for chunk in result:
        assert chunk["section"] == "引言"


def test_chunk_indices_sequential():
    """chunk_index values are sequential starting from 0."""
    sentence = "内容句子用于测试分块索引的连续性和正确性。"
    long_body = "\n\n".join([sentence] * 20)
    text = f"# 第一节\n\n{long_body}\n\n# 第二节\n\n{long_body}"
    result = chunk_text(text, chunk_size=200, overlap=20)
    assert len(result) > 1
    indices = [r["chunk_index"] for r in result]
    assert indices == list(range(len(result)))


def test_empty_text():
    """Empty string returns an empty list."""
    assert chunk_text("") == []
    assert chunk_text("   ") == []
    assert chunk_text("\n\n") == []
