"""Local Sentence Transformer embeddings for ChromaDB."""

from __future__ import annotations

from typing import List, Sequence

import numpy as np
from sentence_transformers import SentenceTransformer


class SentenceTransformerEmbeddingFunction:
    """Chroma-compatible embedding function backed by a local model."""

    _models = {}

    def __init__(self, model_name: str = "all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        if model_name not in self._models:
            self._models[model_name] = SentenceTransformer(model_name)
        self.model = self._models[model_name]

    def __call__(self, texts: Sequence[str]) -> List[List[float]]:
        if isinstance(texts, str):
            texts = [texts]
        vectors = self.model.encode(
            list(texts),
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return np.asarray(vectors, dtype=np.float32).tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """LangChain-compatible document embedding method."""
        return self(texts)

    def embed_query(self, text: str) -> List[float]:
        """LangChain-compatible query embedding method."""
        return self([text])[0]