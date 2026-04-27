"""Typed exception hierarchy for zotron."""
from __future__ import annotations


class ZotronError(Exception):
    """Base class for all zotron errors."""


class ZoteroUnavailable(ZotronError):
    """Zotero not running, or zotron XPI not installed/active."""


class CollectionNotFound(ZotronError):
    """Requested collection (by name or ID) does not exist."""


class CollectionAmbiguous(ZotronError):
    """Multiple collections matched the fuzzy name query."""

    def __init__(self, message: str, candidates: list[dict]) -> None:
        super().__init__(message)
        self.candidates = candidates


class InvalidPDF(ZotronError):
    """File does not start with %PDF- magic bytes."""
