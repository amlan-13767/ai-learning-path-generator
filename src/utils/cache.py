"""
Simple file-based cache for API responses.
Why: Avoid paying for the same API call twice!

How it works:
1. Hash the prompt to create a unique cache key
2. Check if cached response exists and is fresh
3. Return cached response OR make API call and cache it

Benefits:
- FREE (no Redis/Memcached needed)
- Survives app restarts
- Works on any platform
- Saves money on repeated queries
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Any, Dict
import os


class FileCache:
    """
    File-based cache with TTL (time-to-live) expiration.
    
    Perfect for caching expensive API responses without needing Redis.
    """
    
    def __init__(self, cache_dir: str = "cache", default_ttl: int = 86400):
        """
        Initialize file-based cache.
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds (24 hours default)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        self.default_ttl = default_ttl
        print(f"📁 Cache initialized at: {self.cache_dir.absolute()}")
    
    def _make_key(self, *args, **kwargs) -> str:
        """
        Create a unique cache key from arguments.
        
        Uses MD5 hash to create short, consistent keys.
        """
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{key}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache if it exists and hasn't expired.
        
        Returns:
            Cached value or None if not found/expired
        """
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if expired
            if time.time() > data['expires_at']:
                cache_path.unlink()  # Delete expired cache
                print(f"🗑️  Cache expired, deleted: {key[:8]}...")
                return None
            
            # Calculate time saved
            age_hours = (time.time() - data['created_at']) / 3600
            print(f"✅ Cache hit! Saved API call cost (cached {age_hours:.1f}h ago)")
            return data['value']
        
        except Exception as e:
            print(f"⚠️  Cache read error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Store value in cache with expiration.
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl: Time-to-live in seconds (optional)
        
        Returns:
            Success status
        """
        cache_path = self._get_cache_path(key)
        ttl = ttl or self.default_ttl
        
        data = {
            'value': value,
            'expires_at': time.time() + ttl,
            'created_at': time.time()
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            print(f"💾 Cached response (TTL: {ttl/3600:.1f}h)")
            return True
        except Exception as e:
            print(f"⚠️  Cache write error: {e}")
            return False
    
    def clear(self) -> int:
        """
        Clear all cache files.
        
        Returns:
            Number of files deleted
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            count += 1
        print(f"🗑️  Cleared {count} cache files")
        return count
    
    def clear_expired(self) -> int:
        """
        Clear only expired cache files.
        
        Returns:
            Number of expired files deleted
        """
        count = 0
        current_time = time.time()
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if current_time > data['expires_at']:
                    cache_file.unlink()
                    count += 1
            except Exception:
                # If we can't read it, delete it
                cache_file.unlink()
                count += 1
        
        if count > 0:
            print(f"🗑️  Cleared {count} expired cache files")
        return count
    
    def cache_key(self, *args, **kwargs) -> str:
        """Public method to generate cache key."""
        return self._make_key(*args, **kwargs)
    
    def stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_files = len(cache_files)
        total_size = sum(f.stat().st_size for f in cache_files)
        
        expired_count = 0
        current_time = time.time()
        
        for cache_file in cache_files:
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if current_time > data['expires_at']:
                    expired_count += 1
            except Exception:
                expired_count += 1
        
        return {
            'total_files': total_files,
            'expired_files': expired_count,
            'active_files': total_files - expired_count,
            'total_size_kb': total_size / 1024,
            'cache_dir': str(self.cache_dir.absolute())
        }


# Global cache instance
# 24 hour cache by default - adjust based on your needs
cache = FileCache(cache_dir="cache", default_ttl=86400)


def cached(ttl: int = 86400):
    """
    Decorator to cache function results.
    
    Usage:
        @cached(ttl=3600)  # Cache for 1 hour
        def expensive_function(param):
            return result
    
    Args:
        ttl: Time-to-live in seconds
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = cache.cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator
