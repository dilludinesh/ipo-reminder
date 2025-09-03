"""Enterprise-grade caching layer with Redis and in-memory fallbacks."""
import json
import logging
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from functools import wraps
import redis
import hashlib

logger = logging.getLogger(__name__)

class CacheManager:
    """Enterprise-grade caching with Redis and memory fallbacks."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_client = None
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'errors': 0
        }

        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory cache: {e}")
            self.redis_client = None

    def _get_cache_key(self, key: str, namespace: str = "") -> str:
        """Generate consistent cache key with optional namespace."""
        if namespace:
            key = f"{namespace}:{key}"
        return hashlib.md5(key.encode()).hexdigest()

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            return pickle.dumps(value)
        except Exception as e:
            logger.warning(f"Pickle serialization failed, using JSON: {e}")
            return json.dumps(value, default=str).encode('utf-8')

    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            return pickle.loads(value)
        except Exception:
            try:
                return json.loads(value.decode('utf-8'))
            except Exception as e:
                logger.error(f"Deserialization failed: {e}")
                return None

    def get(self, key: str, namespace: str = "") -> Optional[Any]:
        """Get value from cache."""
        cache_key = self._get_cache_key(key, namespace)

        try:
            # Try Redis first
            if self.redis_client:
                value = self.redis_client.get(cache_key)
                if value is not None:
                    self.cache_stats['hits'] += 1
                    return self._deserialize_value(value)

            # Fallback to memory cache
            if cache_key in self.memory_cache:
                entry = self.memory_cache[cache_key]
                if datetime.now() < entry['expires_at']:
                    self.cache_stats['hits'] += 1
                    return entry['value']
                else:
                    # Expired, remove it
                    del self.memory_cache[cache_key]

            self.cache_stats['misses'] += 1
            return None

        except Exception as e:
            self.cache_stats['errors'] += 1
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600, namespace: str = "") -> bool:
        """Set value in cache with TTL."""
        cache_key = self._get_cache_key(key, namespace)
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

        try:
            serialized_value = self._serialize_value(value)

            # Set in Redis
            if self.redis_client:
                self.redis_client.setex(cache_key, ttl_seconds, serialized_value)

            # Also set in memory cache
            self.memory_cache[cache_key] = {
                'value': value,
                'expires_at': expires_at
            }

            self.cache_stats['sets'] += 1
            return True

        except Exception as e:
            self.cache_stats['errors'] += 1
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str, namespace: str = "") -> bool:
        """Delete value from cache."""
        cache_key = self._get_cache_key(key, namespace)

        try:
            deleted = False

            # Delete from Redis
            if self.redis_client:
                if self.redis_client.delete(cache_key):
                    deleted = True

            # Delete from memory cache
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
                deleted = True

            if deleted:
                self.cache_stats['deletes'] += 1

            return deleted

        except Exception as e:
            self.cache_stats['errors'] += 1
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    def clear_namespace(self, namespace: str) -> int:
        """Clear all keys in a namespace."""
        try:
            cleared = 0

            # Clear Redis namespace
            if self.redis_client:
                pattern = f"{namespace}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    cleared += len(keys)

            # Clear memory cache namespace
            keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(f"{namespace}:")]
            for key in keys_to_delete:
                del self.memory_cache[key]
                cleared += 1

            return cleared

        except Exception as e:
            logger.error(f"Cache clear namespace error for {namespace}: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            **self.cache_stats,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'memory_cache_size': len(self.memory_cache),
            'redis_connected': self.redis_client is not None
        }

    def health_check(self) -> Dict[str, Any]:
        """Check cache health status."""
        health = {
            'status': 'healthy',
            'redis': False,
            'memory': True,
            'errors': []
        }

        # Check Redis
        if self.redis_client:
            try:
                self.redis_client.ping()
                health['redis'] = True
            except Exception as e:
                health['errors'].append(f"Redis: {e}")
                health['status'] = 'degraded'

        # Check memory cache
        try:
            # Clean expired entries
            now = datetime.now()
            expired_keys = [k for k, v in self.memory_cache.items() if now >= v['expires_at']]
            for key in expired_keys:
                del self.memory_cache[key]
        except Exception as e:
            health['errors'].append(f"Memory cache: {e}")
            health['memory'] = False
            health['status'] = 'unhealthy'

        return health

# Global cache instance
cache_manager = CacheManager()

def cached(ttl_seconds: int = 3600, namespace: str = ""):
    """Decorator for caching function results."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key_parts = [func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
            cache_key = "|".join(key_parts)

            # Try to get from cache first
            cached_result = cache_manager.get(cache_key, namespace)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            if result is not None:
                cache_manager.set(cache_key, result, ttl_seconds, namespace)
                logger.debug(f"Cached result for {func.__name__}")

            return result
        return wrapper
    return decorator

def cache_ipo_data(ttl_seconds: int = 1800):  # 30 minutes default
    """Decorator specifically for IPO data caching."""
    return cached(ttl_seconds=ttl_seconds, namespace="ipo_data")

def cache_recommendations(ttl_seconds: int = 3600):  # 1 hour default
    """Decorator for recommendation caching."""
    return cached(ttl_seconds=ttl_seconds, namespace="recommendations")
