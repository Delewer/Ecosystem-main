"""
Simple caching helpers to centralize cache usage.
"""
from typing import Callable, TypeVar

from django.core.cache import cache

T = TypeVar("T")


def cached_get(key: str, builder: Callable[[], T], *, ttl: int = 300) -> T:
    """
    Return cached value if present; otherwise build and store.
    """
    value = cache.get(key)
    if value is not None:
        return value
    value = builder()
    cache.set(key, value, ttl)
    return value


def invalidate_prefix(prefix: str) -> None:
    """
    Invalidate cache keys by prefix when backend supports `keys`.
    """
    try:
        keys = cache.keys(f"{prefix}*")  # type: ignore[attr-defined]
        for key in keys:
            cache.delete(key)
    except Exception:
        # Safe fallback when backend does not expose keys
        cache.delete(prefix)
