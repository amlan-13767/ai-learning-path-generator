"""
BM25 Retriever for keyword-based document search.

BM25 (Best Matching 25) is a probabilistic ranking function used for keyword-based
document retrieval. It's particularly effective for exact keyword matches that
semantic search might miss.
"""
from typing import List, Dict, Any, Optional
import numpy as np
from rank_bm25 import BM25Okapi
from langchain.schema import Document


class BM25Retriever:
    """
    BM25-based keyword retriever for hybrid search.
    
    BM25 uses term frequency (TF) and inverse document frequency (IDF) to rank
    documents based on keyword relevance.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 retriever.
        
        Args:
            k1: Term frequency saturation parameter (default: 1.5)
                Higher values give more weight to term frequency
            b: Length normalization parameter (default: 0.75)
                0 = no normalization, 1 = full normalization
        """
        self.k1 = k1
        self.b = b
        self.bm25 = None
        self.documents = []
        self.tokenized_corpus = []
        
    def index_documents(self, documents: List[Document]) -> None:
        """
        Index documents for BM25 search.
        
        Args:
            documents: List of Document objects to index
        """
        if not documents:
            return
            
        self.documents = documents
        
        # Tokenize documents (simple whitespace tokenization)
        self.tokenized_corpus = [
            doc.page_content.lower().split() 
            for doc in documents
        ]
        
        # Create BM25 index
        self.bm25 = BM25Okapi(self.tokenized_corpus, k1=self.k1, b=self.b)
        
        print(f"✅ BM25 index created with {len(documents)} documents")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents using BM25 keyword matching.
        
        Args:
            query: Search query
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries with 'document' and 'score' keys
        """
        if not self.bm25 or not self.documents:
            return []
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        # Build results
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include documents with non-zero scores
                results.append({
                    'document': self.documents[idx],
                    'score': float(scores[idx]),
                    'rank': len(results) + 1
                })
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the indexed corpus.
        
        Returns:
            Dictionary with corpus statistics
        """
        if not self.bm25:
            return {"indexed": False}
        
        return {
            "indexed": True,
            "document_count": len(self.documents),
            "avg_doc_length": np.mean([len(doc) for doc in self.tokenized_corpus]),
            "k1": self.k1,
            "b": self.b
        }


def reciprocal_rank_fusion(
    results_list: List[List[Dict[str, Any]]], 
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    Combine multiple ranked lists using Reciprocal Rank Fusion (RRF).
    
    RRF is a simple but effective method for combining rankings from different
    retrieval systems. It gives higher scores to documents that appear in
    multiple result lists and/or appear higher in those lists.
    
    Formula: RRF_score(d) = Σ(1 / (k + rank(d)))
    
    Args:
        results_list: List of result lists from different retrievers
        k: Constant to prevent division by zero (default: 60)
        
    Returns:
        Fused and re-ranked results
    """
    # Track scores for each unique document
    doc_scores = {}
    doc_objects = {}
    
    for results in results_list:
        for result in results:
            doc = result['document']
            rank = result.get('rank', result.get('score', 1))
            
            # Use document content as key (hash for uniqueness)
            doc_key = hash(doc.page_content)
            
            # Calculate RRF score
            rrf_score = 1.0 / (k + rank)
            
            # Accumulate scores
            if doc_key in doc_scores:
                doc_scores[doc_key] += rrf_score
            else:
                doc_scores[doc_key] = rrf_score
                doc_objects[doc_key] = doc
    
    # Sort by RRF score
    sorted_docs = sorted(
        doc_scores.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    # Build final results
    fused_results = []
    for doc_key, score in sorted_docs:
        fused_results.append({
            'document': doc_objects[doc_key],
            'score': score,
            'rank': len(fused_results) + 1
        })
    
    return fused_results
