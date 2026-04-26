"""Typed exception hierarchy for zotero_bridge."""
from __future__ import annotations


class ZoteroBridgeError(Exception):
    """Base class for all zotero-bridge errors."""


class ZoteroUnavailable(ZoteroBridgeError):
    """Zotero not running, or zotero-bridge XPI not installed/active."""


class CollectionNotFound(ZoteroBridgeError):
    """Requested collection (by name or ID) does not exist."""


class CollectionAmbiguous(ZoteroBridgeError):
    """Multiple collections matched the fuzzy name query."""

    def __init__(self, message: str, candidates: list[dict]) -> None:
        super().__init__(message)
        self.candidates = candidates


class InvalidPDF(ZoteroBridgeError):
    """File does not start with %PDF- magic bytes."""
