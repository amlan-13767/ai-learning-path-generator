"""Opt-in indexing utility for the additive Sentence Transformer collections.

This module does not run during application startup. Invoke ``index_documents``
explicitly after reviewing the source corpus and backing up vector_db.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional

import chromadb
from chromadb.config import Settings

from src.ml.local_embeddings import SentenceTransformerEmbeddingFunction
from src.utils.config import (
    SENTENCE_TRANSFORMER_MODEL,
    SENTENCE_TRANSFORMER_RESOURCES_COLLECTION,
    VECTOR_DB_PATH,
)


def index_documents(
    source_directory: str = "vector_db/documents",
    db_path: Optional[str] = None,
    collection_name: str = SENTENCE_TRANSFORMER_RESOURCES_COLLECTION,
    model_name: str = SENTENCE_TRANSFORMER_MODEL,
) -> int:
    """Add local text files to a separate Sentence Transformer Chroma collection.

    Existing IDs are skipped, so rerunning this function does not overwrite
    previously indexed documents. It never deletes existing collections.
    """
    source_path = Path(source_directory)
    if not source_path.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source_path}")

    client = chromadb.Client(
        Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=db_path or VECTOR_DB_PATH,
            anonymized_telemetry=False,
            allow_reset=True,
        )
    )
    embedding_function = SentenceTransformerEmbeddingFunction(model_name)
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={
            "description": "Sentence Transformer migration collection",
            "embedding_provider": "sentence-transformers",
            "embedding_model": model_name,
        },
    )

    existing_ids = set(collection.get().get("ids") or [])
    files = sorted(source_path.glob("*.txt"))
    pending_files = [path for path in files if str(path) not in existing_ids]
    if not pending_files:
        return 0

    collection.add(
        ids=[str(path) for path in pending_files],
        documents=[path.read_text(encoding="utf-8") for path in pending_files],
        metadatas=[{"source": str(path)} for path in pending_files],
    )
    return len(pending_files)


if __name__ == "__main__":
    added = index_documents()
    print(f"Indexed {added} new Sentence Transformer documents.")
