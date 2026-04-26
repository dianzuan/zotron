"""Tests for zotero_bridge._paginate.paginate."""
from unittest.mock import MagicMock

import pytest

from zotero_bridge._paginate import paginate


def test_paginate_list_response_loops_until_short_page():
    rpc = MagicMock()
    pages = [
        [{"id": 1}, {"id": 2}, {"id": 3}],  # full page
        [{"id": 4}, {"id": 5}, {"id": 6}],  # full page
        [{"id": 7}],                          # short — stop
    ]
    rpc.call.side_effect = pages
    result = paginate(rpc, "items.list", {}, page_size=3)
    assert [r["id"] for r in result] == [1, 2, 3, 4, 5, 6, 7]
    # Verify offsets passed correctly
    calls = rpc.call.call_args_list
    assert calls[0].args == ("items.list", {"offset": 0, "limit": 3})
    assert calls[1].args == ("items.list", {"offset": 3, "limit": 3})
    assert calls[2].args == ("items.list", {"offset": 6, "limit": 3})


def test_paginate_dict_response_with_items_key():
    rpc = MagicMock()
    rpc.call.side_effect = [
        {"items": [{"id": 1}, {"id": 2}], "total": 3},
        {"items": [{"id": 3}], "total": 3},
    ]
    result = paginate(rpc, "items.list", {}, page_size=2)
    assert [r["id"] for r in result] == [1, 2, 3]


def test_paginate_preserves_user_params():
    """User-supplied params (e.g. collection filter) must be passed every page."""
    rpc = MagicMock()
    rpc.call.side_effect = [[{"id": 1}]]  # short page, stop after 1
    paginate(rpc, "items.list", {"collection": 42}, page_size=10)
    # User param + injected pagination param both present
    args = rpc.call.call_args_list[0].args[1]
    assert args == {"collection": 42, "offset": 0, "limit": 10}


def test_paginate_safety_cap_at_10000():
    """Even if XPI keeps returning full pages, stop at 10k items."""
    rpc = MagicMock()
    # Return a distinct full page each call so the no-progress detector
    # doesn't trip — we want to specifically exercise SAFETY_CAP.
    counter = {"n": 0}

    def call(method, params=None):
        n = counter["n"]
        counter["n"] += 1
        return [{"id": n * 1000 + i} for i in range(1000)]

    rpc.call.side_effect = call
    result = paginate(rpc, "items.list", {}, page_size=1000)
    # Hits cap at 10k items (10 pages)
    assert len(result) == 10000
    assert rpc.call.call_count == 10


def test_paginate_dict_without_recognized_key_returns_as_is():
    """First-call dict response without items/tags/results/data is single-shot."""
    rpc = MagicMock()
    rpc.call.return_value = {"status": "ok", "timestamp": "2026-04-26"}
    result = paginate(rpc, "system.ping", {}, page_size=10)
    assert result == {"status": "ok", "timestamp": "2026-04-26"}
    assert rpc.call.call_count == 1


def test_paginate_scalar_response_returns_as_is():
    """First-call scalar (e.g. an int from a counter method) returns as-is."""
    rpc = MagicMock()
    rpc.call.return_value = 42
    result = paginate(rpc, "system.count", {}, page_size=10)
    assert result == 42
    assert rpc.call.call_count == 1


def test_paginate_mid_stream_shape_change_raises():
    """If response shape becomes non-paginatable mid-loop, raise rather than truncate."""
    rpc = MagicMock()
    rpc.call.side_effect = [
        [{"id": 1}, {"id": 2}],     # full page
        {"error": "rate limited"},   # mid-stream non-list dict
    ]
    with pytest.raises(RuntimeError, match="non-paginated"):
        paginate(rpc, "items.list", {}, page_size=2)


def test_paginate_all_list_keys_work():
    """All four _LIST_KEYS (items, tags, results, data) are recognized."""
    for key in ("items", "tags", "results", "data"):
        rpc = MagicMock()
        rpc.call.side_effect = [{key: [{"x": 1}]}]  # short page → stop
        result = paginate(rpc, f"some.{key}", {}, page_size=10)
        assert result == [{"x": 1}], f"key={key} failed"


def test_paginate_detects_method_ignoring_offset():
    """If consecutive pages are identical, method is ignoring offset.
    Raise RuntimeError rather than silently spin to SAFETY_CAP."""
    rpc = MagicMock()
    # Same first 3 tags returned regardless of offset — simulates XPI bug
    # like the real tags.list at HEAD.
    rpc.call.return_value = [
        {"tag": "a", "type": 1},
        {"tag": "b", "type": 1},
        {"tag": "c", "type": 1},
    ]
    with pytest.raises(RuntimeError, match="ignores offset"):
        paginate(rpc, "tags.list", {}, page_size=3)
