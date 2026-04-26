"""Zotero Bridge — Python client + CLI for the Zotero Bridge XPI.

Exposes a source-agnostic `push_item()` API that any scholar-database
plugin (cnki-plugin, arxiv-plugin, ...) can use to push item metadata +
PDF attachments into Zotero via JSON-RPC over localhost:23119.
"""

from zotero_bridge.rpc import ZoteroRPC
from zotero_bridge.push import (
    PushResult,
    check_pdf_magic,
    find_duplicate,
    push_item,
    resolve_collection,
)
from zotero_bridge.errors import (
    ZoteroBridgeError,
    ZoteroUnavailable,
    CollectionNotFound,
    CollectionAmbiguous,
    InvalidPDF,
)
from zotero_bridge.rag.citation import (
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
    "ZoteroBridgeError",
    "ZoteroUnavailable",
    "CollectionNotFound",
    "CollectionAmbiguous",
    "InvalidPDF",
    "Citation",
    "retrieve_with_citations",
    "format_citation_markdown",
    "format_citation_json",
]
