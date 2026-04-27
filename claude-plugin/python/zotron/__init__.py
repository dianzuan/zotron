"""Zotron — Python client + CLI for the Zotron XPI.

Exposes a source-agnostic `push_item()` API that any scholar-database
plugin (cnki-plugin, arxiv-plugin, ...) can use to push item metadata +
PDF attachments into Zotero via JSON-RPC over localhost:23119.
"""

from zotron.rpc import ZoteroRPC
from zotron.push import (
    PushResult,
    check_pdf_magic,
    find_duplicate,
    push_item,
    resolve_collection,
)
from zotron.errors import (
    ZotronError,
    ZoteroUnavailable,
    CollectionNotFound,
    CollectionAmbiguous,
    InvalidPDF,
)
from zotron.rag.citation import (
    Citation,
    retrieve_with_citations,
    format_citation_markdown,
    format_citation_json,
)

__all__ = [
    "ZoteroRPC",
    "PushResult",
    "push_item",
    "resolve_collection",
    "find_duplicate",
    "check_pdf_magic",
    "ZotronError",
    "ZoteroUnavailable",
    "CollectionNotFound",
    "CollectionAmbiguous",
    "InvalidPDF",
    "Citation",
    "retrieve_with_citations",
    "format_citation_markdown",
    "format_citation_json",
]
