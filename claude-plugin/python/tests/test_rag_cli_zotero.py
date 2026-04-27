"""CLI tests for Zotero XPI-backed retrieval hits."""

from __future__ import annotations

import json
import sys
from unittest.mock import MagicMock, patch

from zotron.rag.cli import main as rag_main


def test_rag_hits_zotero_backend_calls_search_hits_rpc(capsys):
    rpc = MagicMock()
    rpc.call.return_value = {
        "hits": [
            {
                "item_key": "ITEM1",
                "title": "Paper",
                "text": "matched span",
                "chunk_id": "ITEM1:c1",
                "query": "trade risk",
                "score": 1.0,
            }
        ],
        "total": 1,
    }

    cfg = {"zotero": {"rpc_url": "http://zotero.test/rpc"}}
    with patch("zotron.rag.cli.load_config", return_value=cfg), \
         patch("zotron.rag.cli.ZoteroRPC", return_value=rpc) as rpc_cls, \
         patch.object(sys, "argv", [
             "zotron-rag",
             "hits",
             "trade risk",
             "--collection",
             "中国工业经济",
             "--zotero",
             "--limit",
             "5",
             "--top-spans-per-item",
             "2",
             "--include-fulltext-spans",
             "--output",
             "jsonl",
         ]):
        rag_main()

    rpc_cls.assert_called_once_with("http://zotero.test/rpc")
    rpc.call.assert_called_once_with(
        "rag.searchHits",
        {
            "query": "trade risk",
            "collection": "中国工业经济",
            "limit": 5,
            "top_spans_per_item": 2,
            "include_fulltext_spans": True,
        },
    )
    rows = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert rows == [
        {
            "item_key": "ITEM1",
            "title": "Paper",
            "text": "matched span",
            "chunk_id": "ITEM1:c1",
            "query": "trade risk",
            "score": 1.0,
        }
    ]


def test_rag_hits_zotero_backend_requires_collection(capsys):
    with patch("zotron.rag.cli.load_config", return_value={}), \
         patch("zotron.rag.cli.ZoteroRPC") as rpc_cls, \
         patch.object(sys, "argv", [
             "zotron-rag",
             "hits",
             "trade risk",
             "--zotero",
         ]):
        try:
            rag_main()
        except SystemExit as exc:
            assert exc.code == 2
        else:  # pragma: no cover - documents expected CLI exit behavior
            raise AssertionError("--zotero without collection should exit non-zero")

    rpc_cls.assert_not_called()
    assert "--collection is required" in capsys.readouterr().err
