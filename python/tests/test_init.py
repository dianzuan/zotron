"""Smoke test: top-level public API surface."""

def test_citation_api_exposed():
    from zotero_bridge import (
        Citation,
        retrieve_with_citations,
        format_citation_markdown,
        format_citation_json,
    )
    assert Citation is not None
    assert callable(retrieve_with_citations)
    assert callable(format_citation_markdown)
    assert callable(format_citation_json)


def test_citation_api_in_dunder_all():
    import zotero_bridge
    for name in (
        "Citation",
        "retrieve_with_citations",
        "format_citation_markdown",
        "format_citation_json",
    ):
        assert name in zotero_bridge.__all__, f"{name} missing from __all__"
