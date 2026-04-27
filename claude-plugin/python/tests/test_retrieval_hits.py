"""Tests for academic-zh retrieval hit contract."""

import json
import sys
from unittest.mock import MagicMock, patch

from zotron.rag.search import VectorStore, results_to_hits


def test_results_to_hits_emits_minimum_and_recommended_fields():
    rows = [
        {
            "item_id": "ITEM",
            "item_key": "Wang_2022_trade_risk",
            "title": "产业贸易中心性、贸易外向度与金融风险",
            "authors": ["王姝黛", "杨子荣"],
            "year": 2022,
            "venue": "中国工业经济",
            "doi": "",
            "section": "三、研究设计",
            "chunk_id": "ATT:c42",
            "block_ids": ["ATT:p12:b08"],
            "text": "本文利用世界投入产出表和金融风险指标...",
            "score": 0.82,
        }
    ]

    hits = results_to_hits(rows, query="贸易中心性 金融风险 识别策略")

    assert hits == [
        {
            "item_key": "Wang_2022_trade_risk",
            "title": "产业贸易中心性、贸易外向度与金融风险",
            "text": "本文利用世界投入产出表和金融风险指标...",
            "authors": ["王姝黛", "杨子荣"],
            "year": 2022,
            "venue": "中国工业经济",
            "doi": "",
            "zotero_uri": "zotero://select/library/items/Wang_2022_trade_risk",
            "section_heading": "三、研究设计",
            "chunk_id": "ATT:c42",
            "block_ids": ["ATT:p12:b08"],
            "query": "贸易中心性 金融风险 识别策略",
            "score": 0.82,
        }
    ]


def test_vector_store_search_can_return_academic_zh_hits():
    store = VectorStore(collection="test", collection_id=1, model="m")
    store.add_chunk(
        item_id="legacy-id",
        title="Title",
        authors="Author A",
        section="Methods",
        chunk_index=0,
        text="answer span",
        vector=[1.0, 0.0],
        item_key="ITEMKEY",
        chunk_id="ATT:c000001",
        block_ids=["ATT:p1:b01"],
        year=2026,
    )

    hits = store.search_hits([1.0, 0.0], query="answer", top_k=1)

    assert hits[0]["item_key"] == "ITEMKEY"
    assert hits[0]["title"] == "Title"
    assert hits[0]["text"] == "answer span"
    assert hits[0]["section_heading"] == "Methods"
    assert hits[0]["block_ids"] == ["ATT:p1:b01"]


def test_rag_hits_cli_outputs_jsonl(tmp_path, capsys):
    from zotron.rag.cli import main as rag_main

    store = VectorStore(collection="test", collection_id=1, model="m")
    store.add_chunk(
        item_id="legacy-id", title="Title", authors="Author A", section="Methods",
        chunk_index=0, text="answer span", vector=[1.0, 0.0], item_key="ITEMKEY",
    )
    store_path = tmp_path / "test.json"
    store.save(store_path)

    with patch("zotron.rag.cli._store_path", return_value=store_path), \
         patch("zotron.rag.cli._build_embedder") as mock_eb:
        mock_emb = MagicMock()
        mock_emb.embed.return_value = [1.0, 0.0]
        mock_eb.return_value = mock_emb
        with patch.object(sys, "argv", [
            "zotron-rag", "hits", "answer", "--collection", "test", "--output", "jsonl"
        ]):
            rag_main()

    lines = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(lines) == 1
    assert lines[0]["item_key"] == "ITEMKEY"
    assert lines[0]["title"] == "Title"
    assert lines[0]["text"] == "answer span"
