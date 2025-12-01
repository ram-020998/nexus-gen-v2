"""
Caching Utilities

Provides caching for frequently accessed objects to improve performance.
Uses simple in-memory caching with TTL (Time To Live).
"""

from typing import Optional, Any, Dict, Callable
from datetime import datetime, timedelta
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """
    Simple in-memory cache with TTL support.
    
    Thread-safe for single-process applications.
    For multi-process deployments, consider Redis or Memcached.
    """
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        if key not in self._cache:
            self.misses += 1
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if datetime.utcnow() > entry['expires_at']:
            del self._cache[key]
            self.misses += 1
            return None
        
        self.hits += 1
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        ttl = ttl or self.default_ttl
        expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at
        }
    
    def delete(self, key: str) -> None:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats (size, hits, misses, hit_rate)
        """
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'size': len(self._cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.2f}%"
        }
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.
        
        Returns:
            Number of entries removed
        """
        now = datetime.utcnow()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)


# Global cache instance
_global_cache = SimpleCache()


def get_cache() -> SimpleCache:
    """Get global cache instance."""
    return _global_cache


def cached(ttl: Optional[int] = None, key_prefix: str = ''):
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds (uses cache default if not specified)
        key_prefix: Prefix for cache key
        
    Example:
        >>> @cached(ttl=300, key_prefix='object')
        ... def get_object_by_uuid(uuid: str):
        ...     return db.query(ObjectLookup).filter_by(uuid=uuid).first()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cache = get_cache()
            cached_value = cache.get(cache_key)
            
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value
            
            # Call function and cache result
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


class ObjectLookupCache:
    """
    Specialized cache for ObjectLookup entities.
    
    Provides caching by UUID with automatic invalidation.
    """
    
    def __init__(self, cache: Optional[SimpleCache] = None):
        """
        Initialize ObjectLookup cache.
        
        Args:
            cache: Cache instance (uses global cache if not provided)
        """
        self.cache = cache or get_cache()
        self.key_prefix = 'object_lookup'
    
    def get_by_uuid(self, uuid: str) -> Optional[Any]:
        """
        Get ObjectLookup by UUID from cache.
        
        Args:
            uuid: Object UUID
            
        Returns:
            ObjectLookup if cached, None otherwise
        """
        key = f"{self.key_prefix}:uuid:{uuid}"
        return self.cache.get(key)
    
    def set_by_uuid(self, uuid: str, obj: Any, ttl: int = 300) -> None:
        """
        Cache ObjectLookup by UUID.
        
        Args:
            uuid: Object UUID
            obj: ObjectLookup object
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        key = f"{self.key_prefix}:uuid:{uuid}"
        self.cache.set(key, obj, ttl)
    
    def invalidate_by_uuid(self, uuid: str) -> None:
        """
        Invalidate cached ObjectLookup by UUID.
        
        Args:
            uuid: Object UUID
        """
        key = f"{self.key_prefix}:uuid:{uuid}"
        self.cache.delete(key)
    
    def clear(self) -> None:
        """Clear all ObjectLookup cache entries."""
        # Note: This clears the entire cache, not just ObjectLookup entries
        # For production, implement prefix-based clearing
        self.cache.clear()


class SessionCache:
    """
    Specialized cache for MergeSession data.
    
    Caches session metadata and statistics.
    """
    
    def __init__(self, cache: Optional[SimpleCache] = None):
        """
        Initialize Session cache.
        
        Args:
            cache: Cache instance (uses global cache if not provided)
        """
        self.cache = cache or get_cache()
        self.key_prefix = 'session'
    
    def get_session(self, reference_id: str) -> Optional[Any]:
        """
        Get session by reference_id from cache.
        
        Args:
            reference_id: Session reference ID
            
        Returns:
            MergeSession if cached, None otherwise
        """
        key = f"{self.key_prefix}:ref:{reference_id}"
        return self.cache.get(key)
    
    def set_session(self, reference_id: str, session: Any, ttl: int = 600) -> None:
        """
        Cache session by reference_id.
        
        Args:
            reference_id: Session reference ID
            session: MergeSession object
            ttl: Time-to-live in seconds (default: 10 minutes)
        """
        key = f"{self.key_prefix}:ref:{reference_id}"
        self.cache.set(key, session, ttl)
    
    def get_statistics(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cached session statistics.
        
        Args:
            session_id: Session ID
            
        Returns:
            Statistics dict if cached, None otherwise
        """
        key = f"{self.key_prefix}:stats:{session_id}"
        return self.cache.get(key)
    
    def set_statistics(self, session_id: int, stats: Dict[str, Any], ttl: int = 300) -> None:
        """
        Cache session statistics.
        
        Args:
            session_id: Session ID
            stats: Statistics dictionary
            ttl: Time-to-live in seconds (default: 5 minutes)
        """
        key = f"{self.key_prefix}:stats:{session_id}"
        self.cache.set(key, stats, ttl)
    
    def invalidate_session(self, reference_id: str) -> None:
        """
        Invalidate cached session.
        
        Args:
            reference_id: Session reference ID
        """
        key = f"{self.key_prefix}:ref:{reference_id}"
        self.cache.delete(key)
    
    def invalidate_statistics(self, session_id: int) -> None:
        """
        Invalidate cached statistics.
        
        Args:
            session_id: Session ID
        """
        key = f"{self.key_prefix}:stats:{session_id}"
        self.cache.delete(key)
