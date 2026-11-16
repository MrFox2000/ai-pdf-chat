"""A minimal in-memory vector store.

Deliberately small: the interesting part of this project is the retrieval
pipeline, not persistence. Replacing it with pgvector means implementing the
same three methods (``add``, ``get``, ``search``) against a real database.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Chunk:
    id: str
    page: int
    text: str


@dataclass
class Document:
    id: str
    filename: str
    pages: int
    chunks: list[Chunk] = field(default_factory=list)
    matrix: np.ndarray | None = None


class DocumentStore:
    """Holds one embedding matrix per document and answers cosine queries."""

    def __init__(self) -> None:
        self._documents: dict[str, Document] = {}

    def __len__(self) -> int:
        return len(self._documents)

    def add(self, document: Document, vectors: list[list[float]]) -> Document:
        document.matrix = np.asarray(vectors, dtype=np.float32)
        self._documents[document.id] = document
        return document

    def get(self, doc_id: str) -> Document | None:
        return self._documents.get(doc_id)

    def search(self, doc_id: str, query: list[float], k: int = 5) -> list[tuple[Chunk, float]]:
        document = self._documents.get(doc_id)
        if document is None or document.matrix is None or not document.chunks:
            return []

        query_vector = np.asarray(query, dtype=np.float32)
        scores = document.matrix @ query_vector
        top = np.argsort(-scores)[:k]
        return [(document.chunks[int(i)], float(scores[int(i)])) for i in top]
