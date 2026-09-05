"""
Reranking module for improving retrieval relevance.

Rerankers use more sophisticated models to re-score and re-order initial retrieval
results, significantly improving relevance at the cost of additional computation.
"""
import os
from typing import List, Dict, Any, Optional
from langchain.schema import Document

# Optional imports (graceful degradation if not available)
try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    print("⚠️  Cohere not installed. Install with: pip install cohere")

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    print("⚠️  sentence-transformers not installed. Install with: pip install sentence-transformers")


class Reranker:
    """
    Document reranker using Cohere API or local cross-encoder models.
    
    Reranking is a two-stage retrieval process:
    1. Initial retrieval (BM25 + semantic) gets ~20-50 candidates
    2. Reranker scores each candidate against the query for final ranking
    """
    
    def __init__(
        self,
        use_local: bool = False,
        cohere_api_key: Optional[str] = None,
        cohere_model: str = "rerank-english-v3.0",
        local_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        """
        Initialize reranker.
        
        Args:
            use_local: Use local cross-encoder instead of Cohere API
            cohere_api_key: Cohere API key (if using Cohere)
            cohere_model: Cohere rerank model name
            local_model: Local cross-encoder model name
        """
        self.use_local = use_local
        self.cohere_client = None
        self.cross_encoder = None
        self.cohere_model = cohere_model
        
        if use_local:
            self._init_local_reranker(local_model)
        else:
            self._init_cohere_reranker(cohere_api_key)
    
    def _init_cohere_reranker(self, api_key: Optional[str]) -> None:
        """Initialize Cohere reranker."""
        if not COHERE_AVAILABLE:
            print("❌ Cohere not available. Falling back to local reranker.")
            self.use_local = True
            self._init_local_reranker()
            return
        
        api_key = api_key or os.getenv("COHERE_API_KEY")
        if not api_key:
            print("❌ COHERE_API_KEY not set. Falling back to local reranker.")
            self.use_local = True
            self._init_local_reranker()
            return
        
        try:
            self.cohere_client = cohere.Client(api_key)
            print(f"✅ Cohere reranker initialized (model: {self.cohere_model})")
        except Exception as e:
            print(f"❌ Failed to initialize Cohere: {e}")
            print("Falling back to local reranker.")
            self.use_local = True
            self._init_local_reranker()
    
    def _init_local_reranker(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2") -> None:
        """Initialize local cross-encoder reranker."""
        if not CROSS_ENCODER_AVAILABLE:
            print("❌ sentence-transformers not available. Reranking disabled.")
            return
        
        try:
            self.cross_encoder = CrossEncoder(model_name)
            print(f"✅ Local cross-encoder initialized (model: {model_name})")
        except Exception as e:
            print(f"❌ Failed to initialize cross-encoder: {e}")
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents based on relevance to query.
        
        Args:
            query: Search query
            documents: List of Document objects to rerank
            top_k: Number of top results to return
            
        Returns:
            Reranked list of documents with scores
        """
        if not documents:
            return []
        
        # Use appropriate reranker
        if self.use_local and self.cross_encoder:
            return self._rerank_local(query, documents, top_k)
        elif self.cohere_client:
            return self._rerank_cohere(query, documents, top_k)
        else:
            # No reranker available, return original order
            print("⚠️  No reranker available. Returning original order.")
            return [
                {
                    'document': doc,
                    'score': doc.metadata.get('relevance_score', 0.5),
                    'rank': i + 1
                }
                for i, doc in enumerate(documents[:top_k])
            ]
    
    def _rerank_cohere(
        self,
        query: str,
        documents: List[Document],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Rerank using Cohere API."""
        try:
            # Prepare documents for Cohere
            doc_texts = [doc.page_content for doc in documents]
            
            # Call Cohere rerank API
            results = self.cohere_client.rerank(
                model=self.cohere_model,
                query=query,
                documents=doc_texts,
                top_n=top_k
            )
            
            # Build reranked results
            reranked = []
            for result in results.results:
                reranked.append({
                    'document': documents[result.index],
                    'score': result.relevance_score,
                    'rank': len(reranked) + 1
                })
            
            print(f"✅ Cohere reranked {len(documents)} → {len(reranked)} documents")
            return reranked
            
        except Exception as e:
            print(f"❌ Cohere reranking failed: {e}")
            # Fallback to original order
            return [
                {
                    'document': doc,
                    'score': doc.metadata.get('relevance_score', 0.5),
                    'rank': i + 1
                }
                for i, doc in enumerate(documents[:top_k])
            ]
    
    def _rerank_local(
        self,
        query: str,
        documents: List[Document],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Rerank using local cross-encoder."""
        try:
            # Prepare query-document pairs
            pairs = [[query, doc.page_content] for doc in documents]
            
            # Get relevance scores
            scores = self.cross_encoder.predict(pairs)
            
            # Sort by score
            scored_docs = list(zip(documents, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # Build results
            reranked = []
            for doc, score in scored_docs[:top_k]:
                reranked.append({
                    'document': doc,
                    'score': float(score),
                    'rank': len(reranked) + 1
                })
            
            print(f"✅ Local reranked {len(documents)} → {len(reranked)} documents")
            return reranked
            
        except Exception as e:
            print(f"❌ Local reranking failed: {e}")
            # Fallback to original order
            return [
                {
                    'document': doc,
                    'score': doc.metadata.get('relevance_score', 0.5),
                    'rank': i + 1
                }
                for i, doc in enumerate(documents[:top_k])
            ]
