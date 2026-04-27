from __future__ import annotations

import json
from pathlib import Path

import numpy as np


class VectorStore:
    def __init__(self, collection: str, collection_id: int, model: str):
        self.collection = collection
        self.collection_id = collection_id
        self.model = model
        self.chunks: list[dict] = []

    def add_chunk(
        self,
        item_id: str,
        title: str,
        authors: str,
        section: str,
        chunk_index: int,
        text: str,
        vector: list[float],
        attachment_id: int | None = None,
    ) -> None:
        self.chunks.append(
            {
                "item_id": item_id,
                "title": title,
                "authors": authors,
                "section": section,
                "chunk_index": chunk_index,
                "text": text,
                "vector": vector,
                "attachment_id": attachment_id,
            }
        )

    def clear_item(self, item_id: str) -> None:
        self.chunks = [c for c in self.chunks if c["item_id"] != item_id]

    def search(self, query_vector: list[float], top_k: int = 10) -> list[dict]:
        if not self.chunks:
            return []

        q = np.array(query_vector, dtype=np.float32)
        q = q / np.linalg.norm(q)

        vectors = np.array([c["vector"] for c in self.chunks], dtype=np.float32)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        vectors = vectors / norms
        scores = vectors @ q

        top_indices = np.argsort(scores)[::-1][:top_k]

        return [
            {
                "item_id": self.chunks[i]["item_id"],
                "title": self.chunks[i]["title"],
                "authors": self.chunks[i]["authors"],
                "section": self.chunks[i]["section"],
                "chunk_index": self.chunks[i]["chunk_index"],
                "text": self.chunks[i]["text"],
                "score": float(scores[i]),
                "attachment_id": self.chunks[i].get("attachment_id"),
            }
            for i in top_indices
        ]

    def save(self, path: Path) -> None:
        data = {
            "collection": self.collection,
            "collection_id": self.collection_id,
            "model": self.model,
            "chunks": self.chunks,
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "VectorStore":
        data = json.loads(path.read_text(encoding="utf-8"))
        store = cls(
            collection=data["collection"],
            collection_id=data["collection_id"],
            model=data["model"],
        )
        store.chunks = data["chunks"]
        return store
