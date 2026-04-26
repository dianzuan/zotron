"""Tests for RAG embedding backends."""
import pytest
import httpx

from zotero_bridge.rag.embedder import (
    OllamaEmbedder,
    CloudEmbedder,
    create_embedder,
)


def _ollama_client(responses: list[dict]) -> httpx.Client:
    idx = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal idx
        data = responses[idx] if idx < len(responses) else {}
        idx += 1
        return httpx.Response(200, json=data)

    return httpx.Client(transport=httpx.MockTransport(handler))


def _cloud_client(response: dict) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=response)

    return httpx.Client(transport=httpx.MockTransport(handler))


# --- factory ---

def test_create_ollama_embedder():
    emb = create_embedder("ollama", "nomic-embed-text")
    assert isinstance(emb, OllamaEmbedder)
    assert emb.model == "nomic-embed-text"


def test_create_cloud_embedder():
    emb = create_embedder("zhipu", "embedding-3", api_key="key123")
    assert isinstance(emb, CloudEmbedder)
    assert emb.model == "embedding-3"


def test_create_unknown_embedder():
    with pytest.raises(ValueError, match="Unknown provider"):
        create_embedder("nonexistent", "some-model")


# --- OllamaEmbedder ---

def test_ollama_embed():
    client = _ollama_client([{"embedding": [0.1, 0.2, 0.3]}])
    emb = OllamaEmbedder(model="nomic-embed-text", api_url="http://localhost:11434", client=client)
    result = emb.embed("hello world")
    assert result == [0.1, 0.2, 0.3]


def test_ollama_embed_batch():
    client = _ollama_client([
        {"embedding": [0.1, 0.2, 0.3]},
        {"embedding": [0.4, 0.5, 0.6]},
    ])
    emb = OllamaEmbedder(model="nomic-embed-text", api_url="http://localhost:11434", client=client)
    results = emb.embed_batch(["foo", "bar"])
    assert results == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]


# --- CloudEmbedder ---

def test_cloud_embed():
    client = _cloud_client({"data": [{"embedding": [0.5, 0.6, 0.7]}]})
    emb = CloudEmbedder(
        provider="zhipu",
        model="embedding-3",
        api_key="key123",
        client=client,
    )
    result = emb.embed("test text")
    assert result == [0.5, 0.6, 0.7]
