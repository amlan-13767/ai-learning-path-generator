"""
Semantic caching layer using Redis for fast query result retrieval.

Semantic caching stores query embeddings and their results, allowing instant
responses for similar queries without re-running the expensive RAG pipeline.
"""
import os
import json
import hashlib
from typing import Optional, Any, Dict
import numpy as np

# Optional imports
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis not installed. Install with: pip install redis")

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from src.utils.config import EMBEDDING_MODEL
except Exception:
    EMBEDDING_MODEL = "text-embedding-3-small"

class SemanticCache:
    """
    Redis-based semantic cache for RAG queries.
    
    Instead of exact string matching, this cache uses embedding similarity
    to find semantically similar queries and return cached results.
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        redis_password: Optional[str] = None,
        redis_db: int = 0,
        ttl: int = 3600,
        similarity_threshold: float = 0.95,
        openai_api_key: Optional[str] = None
    ):
        """
        Initialize semantic cache.
        
        Args:
            redis_url: Full Redis URL (e.g., redis://... or rediss://... for SSL)
            redis_host: Redis server host (used if redis_url not provided)
            redis_port: Redis server port (used if redis_url not provided)
            redis_password: Redis password (used if redis_url not provided)
            redis_db: Redis database number (used if redis_url not provided)
            ttl: Time-to-live for cached entries (seconds)
            similarity_threshold: Minimum cosine similarity for cache hit
            openai_api_key: OpenAI API key for embeddings
        """
        self.ttl = ttl
        self.similarity_threshold = similarity_threshold
        self.redis_client = None
        self.openai_client = None
        self.enabled = False
        
        # Initialize Redis
        if REDIS_AVAILABLE:
            try:
                # Prefer REDIS_URL if provided and valid (for Upstash, Render, etc.)
                if redis_url and redis_url.strip() and redis_url.startswith(('redis://', 'rediss://', 'unix://')):
                    self.redis_client = redis.from_url(
                        redis_url,
                        decode_responses=False,
                        ssl_cert_reqs=None  # Accept self-signed certs for Upstash
                    )
                    print(f"✅ Connecting to Redis via URL...")
                else:
                    self.redis_client = redis.Redis(
                        host=redis_host,
                        port=redis_port,
                        password=redis_password if redis_password else None,
                        db=redis_db,
                        decode_responses=False
                    )
                    print(f"✅ Connecting to Redis at {redis_host}:{redis_port}...")
                
                # Test connection
                self.redis_client.ping()
                self.enabled = True
                print(f"✅ Semantic cache initialized successfully")
            except Exception as e:
                print(f"⚠️  Redis connection failed: {e}. Caching disabled.")
                self.redis_client = None
        else:
            print("⚠️  Redis not available. Caching disabled.")
        
        # Initialize OpenAI for embeddings
        if OPENAI_AVAILABLE:
            api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
        
        if not self.openai_client:
            print("⚠️  OpenAI not available. Semantic caching disabled.")
            self.enabled = False
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Get embedding vector for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        if not self.openai_client:
            return None
        
        try:
            response = self.openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=text
            )
            embedding = np.array(response.data[0].embedding)
            return embedding
        except Exception as e:
            print(f"⚠️  Embedding generation failed: {e}")
            return None
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity (0-1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def get(self, query: str, threshold: Optional[float] = None) -> Optional[Any]:
        """
        Get cached result for a query.

        Args:
            query: Search query text
            threshold: Optional override for similarity threshold

        Returns:
            Cached result or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None

        current_threshold = threshold if threshold is not None else self.similarity_threshold

        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)
            if query_embedding is None:
                return None

            best_similarity = 0.0
            best_result = None

            # Iterate using SCAN to avoid blocking Redis on large keyspaces
            for key in self.redis_client.scan_iter(match="semantic_cache:*"):
                try:
                    cached_data = self.redis_client.get(key)
                    if not cached_data:
                        continue

                    cached_dict = json.loads(cached_data.decode("utf-8"))
                    cached_embedding = np.array(cached_dict["embedding"])

                    similarity = self._cosine_similarity(query_embedding, cached_embedding)

                    if similarity > best_similarity and similarity >= current_threshold:
                        best_similarity = similarity
                        best_result = cached_dict["result"]

                except Exception:
                    continue

            if best_result is not None:
                print(f"💰 Cache hit! Similarity: {best_similarity:.3f}")
                return best_result

            return None

        except Exception as e:
            print(f"⚠️  Cache get failed: {e}")
            return None
    
    def set(self, query: str, result: Any) -> bool:
        """
        Cache a query result.
        
        Args:
            query: Search query
            result: Result to cache
            
        Returns:
            Success status
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            # Get query embedding
            query_embedding = self._get_embedding(query)
            if query_embedding is None:
                return False
            
            # Create cache key (hash of query for uniqueness)
            query_hash = hashlib.md5(query.encode()).hexdigest()
            cache_key = f"semantic_cache:{query_hash}"
            
            # Prepare cache data
            cache_data = {
                'query': query,
                'embedding': query_embedding.tolist(),
                'result': result
            }
            
            # Store in Redis with TTL
            self.redis_client.setex(
                cache_key,
                self.ttl,
                json.dumps(cache_data).encode('utf-8')
            )
            
            print(f"💾 Cached query: '{query}' (TTL: {self.ttl}s)")
            return True
            
        except Exception as e:
            print(f"⚠️  Cache set failed: {e}")
            return False
    
    def clear(self) -> int:
        """
        Clear all cached entries.
        
        Returns:
            Number of entries cleared
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys("semantic_cache:*")
            if keys:
                count = self.redis_client.delete(*keys)
                print(f"🗑️  Cleared {count} cache entries")
                return count
            return 0
        except Exception as e:
            print(f"⚠️  Cache clear failed: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            keys = self.redis_client.keys("semantic_cache:*")
            return {
                "enabled": True,
                "entries": len(keys),
                "ttl": self.ttl,
                "similarity_threshold": self.similarity_threshold
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}
