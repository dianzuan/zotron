import pytest
from zotero_bridge.rag.search import VectorStore


def make_store() -> VectorStore:
    return VectorStore(collection="TestCol", collection_id=1, model="test-model")


def test_save_and_load(tmp_path):
    store = make_store()
    store.add_chunk("item1", "Title A", "Author A", "intro", 0, "text one", [1.0, 0.0])
    store.add_chunk("item2", "Title B", "Author B", "method", 0, "text two", [0.0, 1.0])

    path = tmp_path / "store.json"
    store.save(path)

    loaded = VectorStore.load(path)
    assert loaded.collection == "TestCol"
    assert loaded.collection_id == 1
    assert loaded.model == "test-model"
    assert len(loaded.chunks) == 2
    assert loaded.chunks[0]["item_id"] == "item1"
    assert loaded.chunks[1]["text"] == "text two"
    assert loaded.chunks[0]["vector"] == [1.0, 0.0]


def test_search_cosine_similarity():
    store = make_store()
    # chunk 0: close to query [1, 0, 0]
    store.add_chunk("i1", "T1", "A1", "s1", 0, "close", [1.0, 0.0, 0.0])
    # chunk 1: orthogonal
    store.add_chunk("i2", "T2", "A2", "s2", 0, "ortho", [0.0, 1.0, 0.0])
    # chunk 2: opposite
    store.add_chunk("i3", "T3", "A3", "s3", 0, "far", [-1.0, 0.0, 0.0])

    results = store.search([1.0, 0.0, 0.0], top_k=3)
    assert len(results) == 3
    assert results[0]["item_id"] == "i1"
    assert results[0]["score"] > results[1]["score"]
    assert results[1]["score"] > results[2]["score"]


def test_search_top_k():
    store = make_store()
    for i in range(20):
        store.add_chunk(f"item{i}", f"T{i}", f"A{i}", "s", i, f"text {i}", [float(i), 1.0])

    results = store.search([1.0, 0.0], top_k=5)
    assert len(results) == 5


def test_search_empty_store():
    store = make_store()
    results = store.search([1.0, 0.0, 0.0])
    assert results == []


def test_clear_item():
    store = make_store()
    store.add_chunk("item1", "T1", "A1", "s1", 0, "chunk 1a", [1.0, 0.0])
    store.add_chunk("item1", "T1", "A1", "s1", 1, "chunk 1b", [0.5, 0.5])
    store.add_chunk("item2", "T2", "A2", "s2", 0, "chunk 2a", [0.0, 1.0])

    store.clear_item("item1")

    assert len(store.chunks) == 1
    assert store.chunks[0]["item_id"] == "item2"


def test_search_includes_attachment_id_and_chunk_index():
    """Search results expose attachment_id and chunk_index for citation provenance."""
    from zotero_bridge.rag.search import VectorStore
    store = VectorStore(collection="test", collection_id=1, model="m")
    store.add_chunk(
        item_id="ITEM_A",
        title="Title A",
        authors="Author A",
        section="Intro",
        chunk_index=3,
        text="alpha beta",
        vector=[1.0, 0.0],
        attachment_id=99,
    )
    results = store.search([1.0, 0.0], top_k=1)
    assert len(results) == 1
    r = results[0]
    assert r["attachment_id"] == 99
    assert r["chunk_index"] == 3
    assert r["item_id"] == "ITEM_A"
