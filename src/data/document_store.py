"""
Vector database interface for the AI Learning Path Generator.
Handles document storage, retrieval, and semantic search.

Optimizations:
- Singleton pattern for connection pooling
- Batch operations for efficiency
- Query optimization and caching
- Relevance score filtering (>0.7)
- Performance logging
"""
import os
import time
import hashlib
import sqlite3
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import threading

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from langchain.schema import Document

from src.utils.config import (
    VECTOR_DB_PATH, 
    OPENAI_API_KEY,
    EMBEDDING_MODEL,
    # Advanced RAG config
    ENABLE_SEMANTIC_CACHE,
    QUERY_REWRITE_ENABLED,
    RERANK_ENABLED,
    CONTEXTUAL_COMPRESSION_ENABLED,
    USE_LOCAL_RERANKER,
    COHERE_API_KEY,
    COHERE_RERANK_MODEL,
    LOCAL_RERANKER_MODEL,
    QUERY_REWRITE_MODEL,
    QUERY_REWRITE_MAX_TOKENS,
    COMPRESSION_MODEL,
    COMPRESSION_MAX_TOKENS,
    RERANK_TOP_K,
    HYBRID_TOP_K,
    BM25_K1,
    BM25_B,
    REDIS_URL,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_PASSWORD,
    REDIS_DB,
    SEMANTIC_CACHE_TTL,
    SEMANTIC_CACHE_THRESHOLD
)
from src.utils.cache import cache


# Singleton instance and lock for thread-safe initialization
_instance = None
_lock = threading.Lock()


class DocumentStore:
    """
    Enhanced document retrieval using ChromaDB vector database with connection pooling.
    
    Features:
    - Singleton pattern for connection reuse
    - Batch operations for efficiency
    - Query optimization and caching
    - Relevance score filtering (>0.7)
    - Performance logging
    """
    
    # Class-level client for connection pooling
    _shared_client = None
    _shared_embedding_function = None
    
    def __new__(cls, db_path: Optional[str] = None):
        """Singleton pattern: ensure only one instance exists."""
        global _instance
        if _instance is None:
            with _lock:
                if _instance is None:
                    _instance = super(DocumentStore, cls).__new__(cls)
                    _instance._initialized = False
        return _instance
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the document store with connection pooling.
        
        Args:
            db_path: Optional path to the vector database
        """
        # Skip if already initialized (singleton pattern)
        if self._initialized:
            return
            
        print(f"--- DocumentStore.__init__ started (db_path: {db_path or VECTOR_DB_PATH}) ---")
        self.db_path = db_path or VECTOR_DB_PATH
        
        # Performance tracking
        self.search_count = 0
        self.cache_hits = 0
        
        # Ensure the directory exists
        os.makedirs(self.db_path, exist_ok=True)
        print(f"--- DocumentStore.__init__: Ensured directory exists: {self.db_path} ---")
        
        # Initialize shared client (connection pooling)
        if DocumentStore._shared_client is None:
            print("--- DocumentStore.__init__: Initializing shared chromadb.Client ---")
            try:
                DocumentStore._shared_client = chromadb.Client(
                    Settings(
                        chroma_db_impl="duckdb+parquet",
                        persist_directory=self.db_path,
                        anonymized_telemetry=False,
                        allow_reset=True
                    )
                )
                print("✅ Shared ChromaDB client initialized (connection pooling active)")
            except Exception as e:
                print(f"⚠️  Failed to initialize ChromaDB client: {e}")
                raise
        
        self.client = DocumentStore._shared_client
        
        # Initialize shared embedding function (reuse across requests)
        if DocumentStore._shared_embedding_function is None:
            print(f"--- DocumentStore.__init__: Initializing custom embedding function ---")
            try:
                # Create custom embedding function compatible with OpenAI v1.x
                from openai import OpenAI
                
                class CustomOpenAIEmbedding:
                    def __init__(self, api_key, model_name="text-embedding-ada-002"):
                        self.client = OpenAI(api_key=api_key)
                        self.model_name = model_name
                    
                    def __call__(self, texts):
                        """Generate embeddings for a list of texts."""
                        if isinstance(texts, str):
                            texts = [texts]
                        
                        response = self.client.embeddings.create(
                            input=texts,
                            model=self.model_name
                        )
                        return [item.embedding for item in response.data]
                
                DocumentStore._shared_embedding_function = CustomOpenAIEmbedding(
                    api_key=OPENAI_API_KEY,
                    model_name=EMBEDDING_MODEL
                )
                print("✅ Shared embedding function initialized")
            except Exception as e:
                print(f"⚠️  Failed to initialize embedding function: {e}")
                raise
        
        self.embedding_function = DocumentStore._shared_embedding_function
        
        # Create or get the collections
        print("--- DocumentStore.__init__: Getting/creating 'learning_resources' collection ---")
        self.resources_collection = self._initialize_collection(
            name="learning_resources",
            metadata={"description": "Educational resources and materials"}
        )
        print("--- DocumentStore.__init__: 'learning_resources' collection obtained ---")
        
        print("--- DocumentStore.__init__: Getting/creating 'learning_paths' collection ---")
        self.paths_collection = self._initialize_collection(
            name="learning_paths",
            metadata={"description": "Generated learning paths"}
        )
        print("--- DocumentStore.__init__: 'learning_paths' collection obtained ---")
        
        # Mark as initialized
        self._initialized = True
        print("--- DocumentStore.__init__ finished ---")
    
    def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        collection_name: str = "learning_resources",
        document_id: Optional[str] = None
    ) -> str:
        """
        Add a document to the vector database.
        
        Args:
            content: Document content
            metadata: Document metadata
            collection_name: Name of the collection to add to
            document_id: Optional ID for the document
            
        Returns:
            ID of the added document
        """
        # Generate a document ID if not provided
        doc_id = document_id or f"doc_{len(content) % 10000}_{hash(content) % 1000000}"
        
        # Get the appropriate collection
        collection = self._initialize_collection(name=collection_name)
        
        # Add the document
        collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def add_documents(
        self, 
        documents: List[Document],
        collection_name: str = "learning_resources"
    ) -> List[str]:
        """
        Add multiple documents to the vector database.
        
        Args:
            documents: List of Document objects
            collection_name: Name of the collection to add to
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        
        # Get the appropriate collection
        collection = self._initialize_collection(name=collection_name)
        
        # Prepare document data
        contents = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        ids = [f"doc_{i}_{hash(doc.page_content) % 1000000}" for i, doc in enumerate(documents)]
        
        # Add documents in batches (ChromaDB has limits)
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            batch_end = min(i + batch_size, len(documents))
            collection.add(
                documents=contents[i:batch_end],
                metadatas=metadatas[i:batch_end],
                ids=ids[i:batch_end]
            )
        
        return ids
    
    def search_documents(
        self,
        query: str,
        collection_name: str = "learning_resources",
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        offset: int = 0
    ) -> List[Document]:
        """
        Search for documents using semantic similarity with pagination.
        
        Args:
            query: Search query
            collection_name: Collection to search in
            filters: Optional metadata filters
            top_k: Number of results to return (default: 5)
            offset: Number of results to skip for pagination (default: 0)
            
        Returns:
            List of relevant Document objects
        """
        # Get the collection
        try:
            collection = self._initialize_collection(name=collection_name)
        except Exception:
            # Collection doesn't exist
            return []

        # Prepare filter if provided
        where = {}
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    # For list values, we need to use the $in operator
                    where[key] = {"$in": value}
                else:
                    where[key] = value
        
        # Execute the search (get more results for pagination)
        try:
            result = collection.query(
                query_texts=[query],
                n_results=top_k + offset,  # Get enough results for pagination
                where=where if where else None
            )
        except Exception as e:
            print(f"⚠️  Search failed: {e}")
            print(f"🔧 Attempting schema repair for error: {type(e).__name__}")
            # Try to repair schema and retry once
            if self._try_repair_collection_schema(e):
                print(f"🔄 Schema repaired, retrying query...")
                try:
                    result = collection.query(
                        query_texts=[query],
                        n_results=top_k + offset,
                        where=where if where else None
                    )
                    print(f"✅ Query retry successful after schema repair")
                except Exception as retry_error:
                    print(f"⚠️  Search retry failed: {retry_error}")
                    return []
            else:
                print(f"❌ Schema repair not applicable for this error")
                return []
        
        # Convert results to Document objects
        documents = []
        if result and result.get("documents"):
            # Apply offset for pagination
            start_idx = offset
            end_idx = offset + top_k
            
            for i in range(start_idx, min(end_idx, len(result["documents"][0]))):
                content = result["documents"][0][i]
                metadata = result["metadatas"][0][i] if result.get("metadatas") and result["metadatas"][0] else {}
                distance = result["distances"][0][i] if result.get("distances") and result["distances"][0] else 1.0
                
                # Add relevance score to metadata
                metadata["relevance_score"] = 1.0 - (distance / 2.0)  # Convert distance to relevance (0-1)
                
                documents.append(Document(
                    page_content=content,
                    metadata=metadata
                ))
        
        return documents
    
    def hybrid_search(
        self,
        query: str,
        collection_name: str = "learning_resources",
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        min_relevance: float = 0.7,
        use_cache: bool = True
    ) -> List[Document]:
        """
        Perform optimized hybrid search with caching and relevance filtering.
        
        Optimizations:
        - Query truncation to 500 chars
        - Stop word removal
        - Result caching (1 hour)
        - Relevance score filtering (>0.7)
        - Performance logging
        
        Args:
            query: Search query
            collection_name: Collection to search in
            filters: Optional metadata filters
            top_k: Number of results to return (default: 5)
            min_relevance: Minimum relevance score (default: 0.7)
            use_cache: Whether to use cached results (default: True)
            
        Returns:
            List of relevant Document objects
        """
        start_time = time.time()
        self.search_count += 1
        
        # Optimize query: truncate to 500 chars
        optimized_query = query[:500] if len(query) > 500 else query
        
        # Remove common stop words to focus on meaningful keywords
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        query_words = optimized_query.lower().split()
        filtered_words = [w for w in query_words if w not in stop_words]
        optimized_query = ' '.join(filtered_words) if filtered_words else optimized_query
        
        # Check cache first
        if use_cache:
            cache_key = cache.cache_key(
                "hybrid_search",
                optimized_query,
                collection_name,
                str(filters),
                top_k,
                min_relevance
            )
            
            cached_results = cache.get(cache_key)
            if cached_results:
                self.cache_hits += 1
                elapsed = time.time() - start_time
                print(f"💰 Cache hit! Search completed in {elapsed*1000:.1f}ms (saved API call)")
                return cached_results
        
        # Perform semantic search
        semantic_results = self.search_documents(
            query=optimized_query,
            collection_name=collection_name,
            filters=filters,
            top_k=top_k * 2  # Get more results for reranking
        )
        
        # Prepare keyword results for simple matching
        keyword_docs = []
        try:
            # Get all documents matching the filters
            collection = self._initialize_collection(name=collection_name)
            
            # Prepare filter for keyword search
            where = {}
            if filters:
                where.update(filters)
            
            # Get documents matching the filter
            result = collection.get(where=where if where else None)
            
            if result and result.get("documents"):
                # Simple keyword matching
                query_terms = set(query.lower().split())
                
                for i, content in enumerate(result["documents"]):
                    # Count matching terms in content
                    content_lower = content.lower()
                    match_count = sum(1 for term in query_terms if term in content_lower)
                    
                    if match_count > 0:
                        metadata = result["metadatas"][i] if result.get("metadatas") else {}
                        # Score based on ratio of matching terms
                        metadata["relevance_score"] = match_count / len(query_terms)
                        
                        keyword_docs.append(Document(
                            page_content=content,
                            metadata=metadata
                        ))
        except Exception:
            # Keyword search failed, continue with semantic results only
            pass
        
        # Combine results, removing duplicates
        all_docs = {}
        
        # Add semantic results
        for doc in semantic_results:
            doc_key = hash(doc.page_content)
            all_docs[doc_key] = doc
        
        # Add keyword results that don't duplicate semantic results
        for doc in keyword_docs:
            doc_key = hash(doc.page_content)
            if doc_key not in all_docs:
                all_docs[doc_key] = doc
        
        # Sort by relevance score
        sorted_docs = sorted(
            all_docs.values(),
            key=lambda x: x.metadata.get("relevance_score", 0),
            reverse=True
        )
        
        # Filter by minimum relevance score
        filtered_docs = [
            doc for doc in sorted_docs 
            if doc.metadata.get("relevance_score", 0) >= min_relevance
        ]
        
        # Take top_k results
        results = filtered_docs[:top_k]
        
        # Performance logging
        elapsed = time.time() - start_time
        print(f"🔍 Search completed in {elapsed*1000:.1f}ms - Found {len(results)}/{len(sorted_docs)} results (min_relevance={min_relevance})")
        
        # Cache the results for 1 hour
        if use_cache and results:
            cache.set(cache_key, results, ttl=3600)
        
        return results
    
    def delete_document(
        self,
        document_id: str,
        collection_name: str = "learning_resources"
    ) -> bool:
        """
        Delete a document from the vector database.
        
        Args:
            document_id: ID of the document to delete
            collection_name: Collection to delete from
            
        Returns:
            Success status
        """
        try:
            collection = self._initialize_collection(name=collection_name)
            
            collection.delete(ids=[document_id])
            return True
        except Exception:
            return False
    
    def clear_collection(self, collection_name: str) -> bool:
        """
        Clear all documents from a collection.
        
        Args:
            collection_name: Collection to clear
            
        Returns:
            Success status
        """
        try:
            self.client.delete_collection(collection_name)
            self._initialize_collection(name=collection_name)
            return True
        except Exception:
            return False
    
    def add_documents_batch(
        self,
        documents: List[Document],
        collection_name: str = "learning_resources",
        batch_size: int = 100
    ) -> List[str]:
        """
        Add documents in batches to avoid memory issues.
        
        Args:
            documents: List of Document objects
            collection_name: Collection to add to
            batch_size: Number of documents per batch (default: 100)
            
        Returns:
            List of document IDs
        """
        if not documents:
            return []
        print(f"📦 Adding {len(documents)} documents in batches of {batch_size}")
        start_time = time.time()
        
        try:
            collection = self._initialize_collection(name=collection_name)
            
            all_ids = []
            
            for i in range(0, len(documents), batch_size):
                batch_end = min(i + batch_size, len(documents))
                batch = documents[i:batch_end]
                
                # Prepare batch data
                contents = [doc.page_content for doc in batch]
                metadatas = [doc.metadata for doc in batch]
                ids = [f"doc_{i+j}_{hash(doc.page_content) % 1000000}" for j, doc in enumerate(batch)]
                
                # Add batch
                collection.add(
                    documents=contents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                all_ids.extend(ids)
                print(f"  ✅ Batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1} added ({len(batch)} docs)")
            
            elapsed = time.time() - start_time
            print(f"✅ Added {len(documents)} documents in {elapsed:.2f}s ({len(documents)/elapsed:.1f} docs/sec)")
            
            return all_ids
            
        except Exception as e:
            print(f"⚠️  Batch add failed: {e}")
            return []
    
    def get_collection_stats(self, collection_name: str = "learning_resources") -> Dict[str, Any]:
        """
        Get statistics about a collection.
        
        Args:
            collection_name: Collection to get stats for
            
        Returns:
            Dictionary with collection statistics
        """
        try:
            collection = self._initialize_collection(name=collection_name)
            
            # Get collection count
            count = collection.count()
            
            # Get sample documents to estimate size
            sample = collection.get(limit=10)
            avg_doc_size = 0
            if sample and sample.get("documents"):
                total_size = sum(len(doc) for doc in sample["documents"])
                avg_doc_size = total_size / len(sample["documents"])
            
            return {
                "collection_name": collection_name,
                "document_count": count,
                "avg_document_size_bytes": avg_doc_size,
                "estimated_total_size_kb": (count * avg_doc_size) / 1024,
                "search_count": self.search_count,
                "cache_hits": self.cache_hits,
                "cache_hit_rate": f"{(self.cache_hits / self.search_count * 100):.1f}%" if self.search_count > 0 else "0%"
            }
        except Exception as e:
            print(f"⚠️  Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    def cleanup_old_embeddings(
        self,
        collection_name: str = "learning_resources",
        days_old: int = 30
    ) -> int:
        """
        Clean up old or unused embeddings to save space.
        
        Args:
            collection_name: Collection to clean up
            days_old: Delete documents older than this many days
            
        Returns:
            Number of documents deleted
        """
        try:
            collection = self._initialize_collection(name=collection_name)
            
            # Get all documents
            result = collection.get()
            
            if not result or not result.get("metadatas"):
                return 0
            
            # Find old documents
            import datetime
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            old_ids = []
            
            for i, metadata in enumerate(result["metadatas"]):
                created_at = metadata.get("created_at", time.time())
                if created_at < cutoff_time:
                    old_ids.append(result["ids"][i])
            
            # Delete old documents
            if old_ids:
                collection.delete(ids=old_ids)
                print(f"🗑️  Cleaned up {len(old_ids)} old documents from {collection_name}")
            
            return len(old_ids)
            
        except Exception as e:
            print(f"⚠️  Cleanup failed: {e}")
            return 0
    
    def advanced_rag_search(
        self,
        query: str,
        collection_name: str = "learning_resources",
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5,
        use_cache: bool = True
    ) -> List[Document]:
        """
        Advanced RAG pipeline with all optimizations.
        
        Pipeline:
        1. Semantic cache check (Redis)
        2. Query rewriting (LLM)
        3. Hybrid retrieval (BM25 + Semantic)
        4. Reciprocal rank fusion
        5. Reranking (Cohere/Cross-encoder)
        6. Contextual compression (LLM)
        
        Args:
            query: Search query
            collection_name: Collection to search
            filters: Optional metadata filters
            top_k: Final number of results
            use_cache: Whether to use semantic caching
            
        Returns:
            Optimized, relevant documents
        """
        print(f"\n🚀 Advanced RAG Pipeline Started")
        print(f"Query: '{query}'")
        
        # Step 1: Check semantic cache
        cached_result = None
        if ENABLE_SEMANTIC_CACHE and use_cache:
            try:
                from src.utils.semantic_cache import SemanticCache
                cache_client = SemanticCache(
                    redis_url=REDIS_URL,
                    redis_host=REDIS_HOST,
                    redis_port=REDIS_PORT,
                    redis_password=REDIS_PASSWORD,
                    redis_db=REDIS_DB,
                    ttl=SEMANTIC_CACHE_TTL,
                    similarity_threshold=SEMANTIC_CACHE_THRESHOLD
                )
                cached_result = cache_client.get(query)
                if cached_result:
                    print("💰 Cache hit! Returning cached results")
                    return cached_result
            except Exception as e:
                print(f"⚠️  Semantic cache check failed: {e}")
        
        # Step 2: Query rewriting
        original_query = query
        if QUERY_REWRITE_ENABLED:
            try:
                from src.ml.query_rewriter import QueryRewriter
                rewriter = QueryRewriter(
                    model=QUERY_REWRITE_MODEL,
                    max_tokens=QUERY_REWRITE_MAX_TOKENS
                )
                query = rewriter.rewrite_if_needed(query)
            except Exception as e:
                print(f"⚠️  Query rewriting failed: {e}")
        
        # Step 3: Hybrid retrieval
        try:
            from src.data.bm25_retriever import BM25Retriever, reciprocal_rank_fusion
            
            # Get all documents for BM25 indexing
            try:
                collection = self.client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function
                )
                all_docs_result = collection.get()
                
                if all_docs_result and all_docs_result.get("documents"):
                    all_documents = [
                        Document(
                            page_content=doc,
                            metadata=all_docs_result["metadatas"][i] if all_docs_result.get("metadatas") else {}
                        )
                        for i, doc in enumerate(all_docs_result["documents"])
                    ]
                else:
                    all_documents = []
            except Exception:
                all_documents = []
            
            # BM25 search
            bm25_results = []
            if all_documents:
                bm25 = BM25Retriever(k1=BM25_K1, b=BM25_B)
                bm25.index_documents(all_documents)
                bm25_results = bm25.search(query, top_k=HYBRID_TOP_K)
            
            # Semantic search
            semantic_docs = self.search_documents(
                query=query,
                collection_name=collection_name,
                filters=filters,
                top_k=HYBRID_TOP_K
            )
            semantic_results = [
                {
                    'document': doc,
                    'score': doc.metadata.get('relevance_score', 0.5),
                    'rank': i + 1
                }
                for i, doc in enumerate(semantic_docs)
            ]
            
            # Fusion
            if bm25_results and semantic_results:
                fused_results = reciprocal_rank_fusion([bm25_results, semantic_results])
                print(f"🔀 Fused {len(bm25_results)} BM25 + {len(semantic_results)} semantic results")
            elif bm25_results:
                fused_results = bm25_results
            else:
                fused_results = semantic_results
            
            # Extract documents from fused results
            candidate_docs = [r['document'] for r in fused_results[:HYBRID_TOP_K]]
            
        except Exception as e:
            print(f"⚠️  Hybrid retrieval failed: {e}. Falling back to semantic only.")
            candidate_docs = self.search_documents(
                query=query,
                collection_name=collection_name,
                filters=filters,
                top_k=HYBRID_TOP_K
            )
        
        # Step 4: Reranking
        if RERANK_ENABLED and candidate_docs:
            try:
                from src.ml.reranker import Reranker
                reranker = Reranker(
                    use_local=USE_LOCAL_RERANKER,
                    cohere_api_key=COHERE_API_KEY,
                    cohere_model=COHERE_RERANK_MODEL,
                    local_model=LOCAL_RERANKER_MODEL
                )
                reranked_results = reranker.rerank(query, candidate_docs, top_k=RERANK_TOP_K)
                candidate_docs = [r['document'] for r in reranked_results]
            except Exception as e:
                print(f"⚠️  Reranking failed: {e}")
                candidate_docs = candidate_docs[:RERANK_TOP_K]
        else:
            candidate_docs = candidate_docs[:top_k]
        
        # Step 5: Contextual compression
        final_docs = candidate_docs
        if CONTEXTUAL_COMPRESSION_ENABLED and candidate_docs:
            try:
                from src.ml.context_compressor import ContextCompressor
                compressor = ContextCompressor(
                    model=COMPRESSION_MODEL,
                    max_tokens=COMPRESSION_MAX_TOKENS
                )
                final_docs = compressor.compress(query, candidate_docs)
            except Exception as e:
                print(f"⚠️  Compression failed: {e}")
        
        # Cache the results
        if ENABLE_SEMANTIC_CACHE and use_cache and final_docs:
            try:
                cache_client.set(original_query, final_docs)
            except Exception as e:
                print(f"⚠️  Cache set failed: {e}")
        
        print(f"✅ Advanced RAG Complete: {len(final_docs)} optimized documents\n")
        return final_docs
    
    def _initialize_collection(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Safely get or create a Chroma collection, repairing schema if needed."""
        try:
            return self.client.get_or_create_collection(
                name=name,
                embedding_function=self.embedding_function,
                metadata=metadata
            )
        except Exception as exc:
            if self._try_repair_collection_schema(exc):
                return self.client.get_or_create_collection(
                    name=name,
                    embedding_function=self.embedding_function,
                    metadata=metadata
                )
            raise

    def _try_repair_collection_schema(self, error: Exception) -> bool:
        """Attempt to repair missing columns in any Chroma table."""
        message = str(error)
        missing_prefix = "no such column: "
        if missing_prefix not in message:
            return False
        
        # Extract table name and column name from error message
        # Format: "no such column: table_name.column_name"
        try:
            parts = message.split(missing_prefix, 1)[1].split()[0].strip('"`[]')
            if '.' not in parts:
                return False
            table_name, column_name = parts.split('.', 1)
        except (IndexError, ValueError):
            return False
        
        # Validate table and column names (only alphanumeric and underscore)
        safe_table = ''.join(ch for ch in table_name if ch.isalnum() or ch == '_')
        safe_column = ''.join(ch for ch in column_name if ch.isalnum() or ch == '_')
        if safe_table != table_name or safe_column != column_name:
            return False
        
        db_file = Path(self.db_path) / "chroma.sqlite3"
        if not db_file.exists():
            return False
        
        try:
            with sqlite3.connect(str(db_file)) as conn:
                conn.execute(f"ALTER TABLE {safe_table} ADD COLUMN {safe_column} TEXT")
                conn.commit()
                print(f"✅ Added missing '{safe_table}.{safe_column}' column to Chroma DB")
            return True
        except sqlite3.OperationalError as alter_err:
            print(f"⚠️  Failed to add column {safe_table}.{safe_column}: {alter_err}")
            return False
    
    def get_cached_path(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a cached learning path from Redis."""
        try:
            import redis
            # Use REDIS_URL if available and valid (for Upstash, Render, etc.)
            if REDIS_URL and REDIS_URL.strip() and REDIS_URL.startswith(('redis://', 'rediss://', 'unix://')):
                redis_client = redis.from_url(
                    REDIS_URL,
                    decode_responses=True,
                    ssl_cert_reqs=None
                )
            else:
                # Build Redis connection params
                redis_params = {
                    'host': REDIS_HOST,
                    'port': REDIS_PORT,
                    'db': REDIS_DB,
                    'decode_responses': True
                }
                # Only add password if it's not empty (strip whitespace)
                password = (REDIS_PASSWORD or '').strip()
                if password:
                    redis_params['password'] = password
                
                redis_client = redis.Redis(**redis_params)
            
            cached_data = redis_client.get(f"path_cache:{key}")
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            print(f"⚠️  Path cache GET failed: {e}")
            return None

    def cache_path(self, key: str, path: Dict[str, Any], ttl: int = 3600):
        """Cache a learning path in Redis."""
        try:
            import redis
            # Use REDIS_URL if available and valid (for Upstash, Render, etc.)
            if REDIS_URL and REDIS_URL.strip() and REDIS_URL.startswith(('redis://', 'rediss://', 'unix://')):
                redis_client = redis.from_url(
                    REDIS_URL,
                    decode_responses=True,
                    ssl_cert_reqs=None
                )
            else:
                # Build Redis connection params
                redis_params = {
                    'host': REDIS_HOST,
                    'port': REDIS_PORT,
                    'db': REDIS_DB,
                    'decode_responses': True
                }
                # Only add password if it's not empty (strip whitespace)
                password = (REDIS_PASSWORD or '').strip()
                if password:
                    redis_params['password'] = password
                
                redis_client = redis.Redis(**redis_params)
            
            redis_client.setex(f"path_cache:{key}", ttl, json.dumps(path))
            print(f"💾 Cached learning path: {key[:8]}... (TTL: {ttl}s)")
        except Exception as e:
            print(f"⚠️  Path cache SET failed: {e}")

    @classmethod
    def shutdown(cls):
        """Gracefully shutdown the shared client connection."""
        if cls._shared_client is not None:
            print("🔌 Shutting down ChromaDB connection...")
            cls._shared_client = None
            cls._shared_embedding_function = None
            print("✅ Connection closed")
