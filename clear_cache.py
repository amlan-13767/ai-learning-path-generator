"""
Simple script to clear the Redis cache.
Run this when you need to reset all cached learning paths.
"""
import redis
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '').strip()  # Strip whitespace
REDIS_DB = int(os.getenv('REDIS_DB', 0))

print(f"🔍 Connecting to Redis at {REDIS_HOST}:{REDIS_PORT} (password: {'set' if REDIS_PASSWORD else 'none'})")

try:
    # Build Redis connection params
    redis_params = {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'db': REDIS_DB,
        'decode_responses': True
    }
    # Only add password if it's not empty
    if REDIS_PASSWORD:
        redis_params['password'] = REDIS_PASSWORD
        print("🔐 Using password authentication")
    
    redis_client = redis.Redis(**redis_params)
    
    # Get all cache keys
    path_keys = list(redis_client.scan_iter(match="path_cache:*"))
    semantic_keys = list(redis_client.scan_iter(match="semantic_cache:*"))
    
    total_keys = len(path_keys) + len(semantic_keys)
    
    if total_keys == 0:
        print("✅ Cache is already empty!")
    else:
        # Delete all cache keys
        if path_keys:
            redis_client.delete(*path_keys)
            print(f"🗑️  Deleted {len(path_keys)} learning path cache entries")
        
        if semantic_keys:
            redis_client.delete(*semantic_keys)
            print(f"🗑️  Deleted {len(semantic_keys)} semantic cache entries")
        
        print(f"✅ Successfully cleared {total_keys} total cache entries!")

except Exception as e:
    print(f"❌ Error clearing cache: {e}")
    print("Make sure Redis is running and your .env file is configured correctly.")
