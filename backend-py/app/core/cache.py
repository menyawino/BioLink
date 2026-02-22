"""
Caching utilities using Redis.
"""
import json
import pickle
from typing import Optional, Any, Union
from functools import wraps
from datetime import timedelta

import redis
from app.config import settings

# Initialize Redis client
redis_client: Optional[redis.Redis] = None

def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client."""
    global redis_client
    if redis_client is None:
        try:
            redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
            redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            redis_client.ping()
        except (redis.ConnectionError, redis.ResponseError):
            # Redis not available, return None
            redis_client = None
    return redis_client


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        value = client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except (json.JSONDecodeError, redis.RedisError):
        return None


def cache_set(
    key: str, 
    value: Any, 
    ttl: Optional[int] = None
) -> bool:
    """Set value in cache with optional TTL."""
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        serialized = json.dumps(value, default=str)
        if ttl:
            client.setex(key, ttl, serialized)
        else:
            default_ttl = getattr(settings, 'redis_cache_ttl', 300)
            client.setex(key, default_ttl, serialized)
        return True
    except (TypeError, redis.RedisError):
        return False


def cache_delete(key: str) -> bool:
    """Delete value from cache."""
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.delete(key)
        return True
    except redis.RedisError:
        return False


def cache_delete_pattern(pattern: str) -> bool:
    """Delete all keys matching pattern."""
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
        return True
    except redis.RedisError:
        return False


def cached(
    prefix: str = "",
    ttl: Optional[int] = None,
    key_func: Optional[callable] = None
):
    """
    Decorator to cache function results.
    
    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds
        key_func: Function to generate cache key from arguments
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = f"{prefix}:{key_func(*args, **kwargs)}"
            else:
                # Default key from function name and arguments
                key_parts = [prefix, func.__name__]
                if args:
                    key_parts.append(str(args))
                if kwargs:
                    key_parts.append(str(sorted(kwargs.items())))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            cache_set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = f"{prefix}:{key_func(*args, **kwargs)}"
            else:
                key_parts = [prefix, func.__name__]
                if args:
                    key_parts.append(str(args))
                if kwargs:
                    key_parts.append(str(sorted(kwargs.items())))
                cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache_set(cache_key, result, ttl)
            return result
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


# Import asyncio here to avoid circular import
import asyncio


class CacheKeys:
    """Predefined cache key patterns."""
    
    PATIENT = "patient:{dna_id}"
    PATIENTS_LIST = "patients:list:{hash}"
    ANALYTICS = "analytics:{type}"
    COHORT = "cohort:{hash}"
    CHART = "chart:{type}:{hash}"
    
    @staticmethod
    def patient(dna_id: str) -> str:
        return CacheKeys.PATIENT.format(dna_id=dna_id)
    
    @staticmethod
    def patients_list(**filters) -> str:
        import hashlib
        filter_str = json.dumps(filters, sort_keys=True, default=str)
        hash_val = hashlib.md5(filter_str.encode()).hexdigest()[:12]
        return CacheKeys.PATIENTS_LIST.format(hash=hash_val)
    
    @staticmethod
    def analytics(analytics_type: str) -> str:
        return CacheKeys.ANALYTICS.format(type=analytics_type)
    
    @staticmethod
    def cohort(**params) -> str:
        import hashlib
        param_str = json.dumps(params, sort_keys=True, default=str)
        hash_val = hashlib.md5(param_str.encode()).hexdigest()[:12]
        return CacheKeys.COHORT.format(hash=hash_val)


def invalidate_patient_cache(dna_id: str) -> None:
    """Invalidate all caches related to a patient."""
    cache_delete(CacheKeys.patient(dna_id))
    cache_delete_pattern("patients:list:*")
    cache_delete_pattern("analytics:*")
    cache_delete_pattern("cohort:*")


def invalidate_analytics_cache() -> None:
    """Invalidate all analytics caches."""
    cache_delete_pattern("analytics:*")
    cache_delete_pattern("chart:*")
