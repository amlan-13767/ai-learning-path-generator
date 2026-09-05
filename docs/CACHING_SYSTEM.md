# 💾 File-Based Caching System

## Overview

The AI Learning Path Generator uses a **file-based caching system** to dramatically reduce API costs and improve response times. This system caches expensive OpenAI API responses to avoid paying for the same query twice.

## 🎯 Why Caching?

- **💰 Cost Savings**: Avoid paying for repeated API calls (can save $100s per month)
- **⚡ Speed**: Cached responses return instantly (0ms vs 2-5 seconds)
- **🌍 Reliability**: Works offline once cached
- **🔄 Persistence**: Survives app restarts (unlike in-memory caching)
- **🚀 Zero Dependencies**: No Redis, Memcached, or external services needed

## 📁 Architecture

### File Structure
```
cache/
├── a3f2c1b8d9e4f5a6.json    # Cached response 1
├── b7d8e9f0a1b2c3d4.json    # Cached response 2
└── ...
```

### Cache File Format
Each cache file stores:
```json
{
  "value": "The actual cached response text...",
  "expires_at": 1704067200,  // Unix timestamp
  "created_at": 1703980800   // Unix timestamp
}
```

## 🔧 Implementation

### 1. FileCache Class (`src/utils/cache.py`)

The core caching engine with these key methods:

#### **`get(key)`** - Retrieve cached value
```python
cached_value = cache.get(cache_key)
if cached_value:
    print("💰 Cache hit! Saved API call")
    return cached_value
```

#### **`set(key, value, ttl=86400)`** - Store value with expiration
```python
cache.set(cache_key, response_text, ttl=86400)  # 24 hours
```

#### **`cache_key(*args, **kwargs)`** - Generate unique cache key
```python
cache_key = cache.cache_key(
    "response",
    prompt[:200],
    model_name,
    temperature
)
```

#### **`clear()`** - Delete all cache files
```python
count = cache.clear()  # Returns number of files deleted
```

#### **`stats()`** - Get cache statistics
```python
stats = cache.stats()
# Returns: {total_files, expired_files, active_files, total_size_kb, cache_dir}
```

### 2. Integration with ModelOrchestrator

The `generate_response()` method in `src/ml/model_orchestrator.py` automatically uses caching:

```python
def generate_response(
    self, 
    prompt: str, 
    relevant_documents: Optional[List[str]] = None,
    temperature: Optional[float] = None,
    use_cache: bool = True  # ✅ Caching enabled by default
) -> str:
    # 1️⃣ Check cache first
    if use_cache:
        cache_key = cache.cache_key(
            "response",
            prompt[:200],  # First 200 chars
            str(relevant_documents)[:100] if relevant_documents else "",
            self.model_name,
            temperature or TEMPERATURE
        )
        
        cached_response = cache.get(cache_key)
        if cached_response:
            print("💰 Using cached response - $0.00 cost!")
            return cached_response
    
    # 2️⃣ Make API call if not cached
    response_text = generate_completion(...)
    
    # 3️⃣ Cache the response for future use
    if use_cache and response_text:
        cache.set(cache_key, response_text, ttl=86400)
    
    return response_text
```

## 🎨 Cache Key Generation

Cache keys are generated using **MD5 hashing** of the input parameters:

```python
def cache_key(self, *args, **kwargs) -> str:
    """Generate unique cache key from arguments"""
    key_data = str(args) + str(sorted(kwargs.items()))
    return hashlib.md5(key_data.encode()).hexdigest()
```

**Example:**
```python
cache_key = cache.cache_key(
    "response",
    "What is machine learning?",
    "gpt-4o-mini",
    0.7
)
# Result: "a3f2c1b8d9e4f5a6b7c8d9e0f1a2b3c4"
```

## ⏰ TTL (Time-To-Live) Management

### Default TTL
- **24 hours (86400 seconds)** for API responses
- Configurable per cache entry

### Expiration Handling
```python
# Check if expired
if time.time() > data['expires_at']:
    cache_path.unlink()  # Auto-delete expired cache
    return None
```

### Manual Cleanup
```python
# Clear only expired entries
expired_count = cache.clear_expired()

# Clear all cache
total_count = cache.clear()
```

## 📊 Cache Statistics

Monitor cache performance:

```python
stats = cache.stats()
print(f"Active cache files: {stats['active_files']}")
print(f"Expired files: {stats['expired_files']}")
print(f"Total size: {stats['total_size_kb']:.2f} KB")
print(f"Cache directory: {stats['cache_dir']}")
```

**Example Output:**
```
Active cache files: 45
Expired files: 3
Total size: 1234.56 KB
Cache directory: /path/to/project/cache
```

## 🎯 Usage Examples

### Basic Usage
```python
from src.utils.cache import cache

# Generate cache key
key = cache.cache_key("user_query", "What is Python?", "gpt-4o-mini")

# Try to get from cache
cached = cache.get(key)
if cached:
    return cached

# If not cached, compute and store
result = expensive_api_call()
cache.set(key, result, ttl=3600)  # Cache for 1 hour
```

### Using the Decorator
```python
from src.utils.cache import cached

@cached(ttl=3600)  # Cache for 1 hour
def expensive_function(param1, param2):
    """This function's results will be automatically cached"""
    return compute_expensive_result(param1, param2)

# First call: computes and caches
result1 = expensive_function("a", "b")  # Takes 5 seconds

# Second call: returns from cache
result2 = expensive_function("a", "b")  # Takes 0.001 seconds
```

### Disabling Cache for Specific Calls
```python
# Disable caching when you need fresh data
response = orchestrator.generate_response(
    prompt="What's the latest news?",
    use_cache=False  # ❌ Skip cache for real-time data
)
```

## 💡 Best Practices

### ✅ DO:
- **Use caching for repeated queries** (e.g., "What is Python?" asked by multiple users)
- **Set appropriate TTLs** (24h for stable content, 1h for changing content)
- **Monitor cache stats** regularly to optimize storage
- **Clear expired entries** periodically with `cache.clear_expired()`

### ❌ DON'T:
- **Cache user-specific data** without including user ID in cache key
- **Cache real-time data** (news, stock prices, weather)
- **Cache streaming responses** (not supported)
- **Set TTL too long** for frequently changing content

## 🔍 Debugging

### Enable Verbose Logging
The cache system includes built-in logging:

```
📁 Cache initialized at: /path/to/cache
✅ Cache hit! Saved API call cost (cached 2.3h ago)
💾 Cached response (TTL: 24.0h)
🗑️  Cache expired, deleted: a3f2c1b8...
```

### Check Cache Files Manually
```bash
# List all cache files
ls -lh cache/

# View a cache file
cat cache/a3f2c1b8d9e4f5a6b7c8d9e0f1a2b3c4.json
```

### Clear Cache for Testing
```python
from src.utils.cache import cache

# Clear all cache
cache.clear()

# Or clear only expired
cache.clear_expired()
```

## 📈 Performance Impact

### Before Caching:
- **API Call**: 2-5 seconds
- **Cost**: $0.002 per request
- **100 requests/day**: $0.20/day = $6/month

### After Caching (80% hit rate):
- **Cached Response**: 0.001 seconds
- **Cost**: $0.00 for cached requests
- **100 requests/day**: $0.04/day = $1.20/month
- **💰 Savings**: ~$4.80/month (80% reduction)

## 🚀 Production Considerations

### Storage Management
- **Monitor disk space**: Cache files accumulate over time
- **Set up cron job**: Run `cache.clear_expired()` daily
- **Implement size limits**: Delete oldest files if cache exceeds threshold

### Scaling
- **Shared cache**: Use network file system for multi-server deployments
- **Cache warming**: Pre-populate cache with common queries
- **Cache invalidation**: Clear specific keys when data changes

### Security
- **No sensitive data**: Don't cache user credentials or PII
- **File permissions**: Ensure cache directory has proper permissions
- **Input validation**: Sanitize cache keys to prevent path traversal

## 🔧 Configuration

### Environment Variables
```bash
# Set custom cache directory
CACHE_DIR=./custom_cache

# Set default TTL (in seconds)
CACHE_DEFAULT_TTL=43200  # 12 hours
```

### Programmatic Configuration
```python
from src.utils.cache import FileCache

# Create custom cache instance
custom_cache = FileCache(
    cache_dir="./my_cache",
    default_ttl=3600  # 1 hour
)
```

## 📚 API Reference

### FileCache Class

| Method | Parameters | Returns | Description |
|--------|-----------|---------|-------------|
| `get(key)` | `key: str` | `Any \| None` | Retrieve cached value |
| `set(key, value, ttl)` | `key: str, value: Any, ttl: int` | `bool` | Store value with expiration |
| `cache_key(*args, **kwargs)` | `*args, **kwargs` | `str` | Generate MD5 cache key |
| `clear()` | - | `int` | Delete all cache files |
| `clear_expired()` | - | `int` | Delete expired files only |
| `stats()` | - | `Dict` | Get cache statistics |

### Decorator

```python
@cached(ttl: int = 86400)
```
Automatically cache function results.

## 🎓 How It Works - Step by Step

1. **Request comes in** → User asks "What is Python?"
2. **Generate cache key** → MD5 hash of (prompt + model + temperature)
3. **Check cache** → Look for `{hash}.json` in cache directory
4. **Cache hit?**
   - ✅ **Yes**: Return cached response instantly (0ms, $0.00)
   - ❌ **No**: Continue to step 5
5. **Make API call** → Call OpenAI API (2-5s, $0.002)
6. **Store in cache** → Save response as JSON with expiration
7. **Return response** → Send to user

## 🆘 Troubleshooting

### Cache Not Working?
```python
# Check if cache directory exists
import os
print(os.path.exists("cache"))  # Should be True

# Check cache stats
from src.utils.cache import cache
print(cache.stats())
```

### Cache Files Growing Too Large?
```python
# Clear old cache
cache.clear_expired()

# Or clear everything
cache.clear()
```

### Permission Errors?
```bash
# Fix cache directory permissions
chmod 755 cache/
```

## 🎉 Summary

The file-based caching system provides:
- ✅ **Zero-cost** repeated queries
- ✅ **Instant** response times
- ✅ **Simple** implementation
- ✅ **Reliable** persistence
- ✅ **Production-ready** error handling

**Result**: Faster app + Lower costs + Happier users! 🚀

---

**Built with ❤️ for the AI Learning Path Generator**
