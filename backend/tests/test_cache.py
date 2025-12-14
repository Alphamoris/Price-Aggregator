import pytest
from app.services.cache import CacheService


def test_cache_set_and_get():
    cache = CacheService[str](maxsize=100, ttl=60)
    
    cache.set("key1", "value1")
    
    result = cache.get("key1")
    
    assert result == "value1"


def test_cache_miss():
    cache = CacheService[str](maxsize=100, ttl=60)
    
    result = cache.get("nonexistent")
    
    assert result is None


def test_cache_delete():
    cache = CacheService[str](maxsize=100, ttl=60)
    
    cache.set("key1", "value1")
    deleted = cache.delete("key1")
    
    assert deleted is True
    assert cache.get("key1") is None


def test_cache_clear():
    cache = CacheService[str](maxsize=100, ttl=60)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.clear()
    
    assert cache.get("key1") is None
    assert cache.get("key2") is None


def test_cache_stats():
    cache = CacheService[str](maxsize=100, ttl=60)
    
    cache.set("key1", "value1")
    cache.get("key1")
    cache.get("key1")
    cache.get("nonexistent")
    
    stats = cache.stats
    
    assert stats["hits"] == 2
    assert stats["misses"] == 1
    assert stats["size"] == 1


def test_cache_invalidate_pattern():
    cache = CacheService[str](maxsize=100, ttl=60)
    
    cache.set("assets:crypto:1", "value1")
    cache.set("assets:crypto:2", "value2")
    cache.set("assets:stock:1", "value3")
    
    count = cache.invalidate_pattern("crypto")
    
    assert count == 2
    assert cache.get("assets:crypto:1") is None
    assert cache.get("assets:stock:1") == "value3"
