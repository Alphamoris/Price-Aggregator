from typing import Any, Generic, TypeVar

from cachetools import TTLCache

from app.config import get_settings
from app.utils.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

T = TypeVar("T")


class CacheService(Generic[T]):
    def __init__(self, maxsize: int | None = None, ttl: int | None = None):
        self._cache: TTLCache = TTLCache(
            maxsize=maxsize or settings.cache_max_size,
            ttl=ttl or settings.cache_ttl_seconds
        )
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> T | None:
        value = self._cache.get(key)
        if value is not None:
            self._hits += 1
            logger.debug("cache_hit", key=key)
        else:
            self._misses += 1
            logger.debug("cache_miss", key=key)
        return value

    def set(self, key: str, value: T) -> None:
        self._cache[key] = value
        logger.debug("cache_set", key=key)

    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            logger.debug("cache_delete", key=key)
            return True
        return False

    def clear(self) -> None:
        self._cache.clear()
        logger.info("cache_cleared")

    def invalidate_pattern(self, pattern: str) -> int:
        keys_to_delete = [k for k in self._cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self._cache[key]
        logger.info("cache_pattern_invalidated", pattern=pattern, count=len(keys_to_delete))
        return len(keys_to_delete)

    @property
    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(hit_rate, 2),
            "size": len(self._cache),
            "maxsize": self._cache.maxsize,
            "ttl": self._cache.ttl,
        }


asset_cache: CacheService[list[dict]] = CacheService()
