"""Tests for zotero_bridge.errors."""
from zotero_bridge.errors import (
    ZoteroBridgeError,
    ZoteroUnavailable,
    CollectionNotFound,
    CollectionAmbiguous,
    InvalidPDF,
)


def test_all_subclass_base():
    for cls in (
        ZoteroUnavailable, CollectionNotFound, CollectionAmbiguous, InvalidPDF,
    ):
        assert issubclass(cls, ZoteroBridgeError)


def test_collection_ambiguous_carries_candidates():
    err = CollectionAmbiguous("ambiguous", candidates=[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}])
    assert err.candidates == [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
