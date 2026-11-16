"""Embedding backends.

The project ships with a dependency-free hashing embedder so the whole stack can
be cloned, run and tested without an API key. When ``OPENAI_API_KEY`` is set the
production embedder from ``langchain-openai`` is used instead. Because both
implement the same one-method interface, nothing else in the codebase changes.
"""

from __future__ import annotations

import hashlib
import re

import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+")


class HashEmbedder:
    """Deterministic bag-of-words hashing embedder used as the offline fallback."""

    dim = 384

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(text) for text in texts]

    def _embed_one(self, text: str) -> list[float]:
        vector = np.zeros(self.dim, dtype=np.float32)
        for token in _TOKEN.findall(text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % self.dim
            sign = 1.0 if digest[4] & 1 else -1.0
            vector[index] += sign
        norm = float(np.linalg.norm(vector))
        if norm:
            vector /= norm
        return vector.tolist()


class OpenAIEmbedder:
    """Production embedder backed by the OpenAI embeddings API."""

    def __init__(self, model: str, api_key: str) -> None:
        from langchain_openai import OpenAIEmbeddings

        self._client = OpenAIEmbeddings(model=model, api_key=api_key)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return await self._client.aembed_documents(texts)


def build_embedder(settings) -> HashEmbedder | OpenAIEmbedder:
    if settings.offline:
        return HashEmbedder()
    return OpenAIEmbedder(settings.embedding_model, settings.openai_api_key)
