"""Tests for zotron.push.find_duplicate."""
from unittest.mock import MagicMock

from zotron.push import find_duplicate


def _rpc_responses(**kwargs) -> MagicMock:
    """Build a mock RPC. kwargs maps method-name → response value."""
    rpc = MagicMock()

    def call(method: str, params: dict | None = None):
        if method in kwargs:
            return kwargs[method]
        return None

    rpc.call.side_effect = call
    return rpc


def test_doi_hit():
    rpc = _rpc_responses(**{
        "search.byIdentifier": [{"key": "ITEM500", "title": "X"}],
    })
    item = {"DOI": "10.1234/foo", "title": "X"}
    assert find_duplicate(rpc, item) == "ITEM500"


def test_doi_miss_title_hit():
    def call(method: str, params: dict | None = None):
        if method == "search.byIdentifier":
            return []
        if method == "search.quick":
            return [{"key": "ITEM42", "title": "中国上市公司财务造假预测模型"}]
        return None

    rpc = MagicMock()
    rpc.call.side_effect = call
    item = {"DOI": "10.x/nope", "title": "中国上市公司财务造假预测模型"}
    assert find_duplicate(rpc, item) == "ITEM42"


def test_title_fallback_exact_match():
    def call(method: str, params: dict | None = None):
        if method == "search.byIdentifier":
            return []
        if method == "search.quick":
            return [
                {"key": "ITEM7", "title": "A very different title"},
                {"key": "ITEM9", "title": "乡村振兴水平的时空演变分析"},
            ]
        return None

    rpc = MagicMock()
    rpc.call.side_effect = call
    item = {"title": "乡村振兴水平的时空演变分析"}
    assert find_duplicate(rpc, item) == "ITEM9"


def test_title_too_short_skips_fallback():
    def call(method, params=None):
        return []
    rpc = MagicMock()
    rpc.call.side_effect = call
    item = {"title": "short"}  # < 10 chars
    assert find_duplicate(rpc, item) is None


def test_no_match_returns_none():
    def call(method, params=None):
        return []
    rpc = MagicMock()
    rpc.call.side_effect = call
    item = {"title": "Some long title with no matches"}
    assert find_duplicate(rpc, item) is None
