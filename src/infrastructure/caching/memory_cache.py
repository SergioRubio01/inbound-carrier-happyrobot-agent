"""
File: memory_cache.py
Description: In-memory cache implementation for development
Author: HappyRobot Team
Created: 2024-11-15
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from src.core.ports.services.cache_service import CacheServicePort

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with value and expiration time."""

    value: Any
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    def get_ttl_seconds(self) -> Optional[int]:
        """Get remaining TTL in seconds."""
        if self.expires_at is None:
            return None
        remaining = (self.expires_at - datetime.utcnow()).total_seconds()
        return max(0, int(remaining))


class MemoryCacheService(CacheServicePort):
    """In-memory cache implementation with TTL support."""

    def __init__(self, default_ttl: Optional[timedelta] = None):
        """
        Initialize memory cache service.

        Args:
            default_ttl: Default time to live for cache entries
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()

    def _start_cleanup_task(self):
        """Start background task to clean up expired entries."""
        self._cleanup_task = asyncio.create_task(self._cleanup_expired())

    async def _cleanup_expired(self):
        """Background task to periodically clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                async with self._lock:
                    expired_keys = [
                        key for key, entry in self._cache.items() if entry.is_expired()
                    ]
                    for key in expired_keys:
                        del self._cache[key]

                    if expired_keys:
                        logger.debug(
                            f"Cleaned up {len(expired_keys)} expired cache entries"
                        )
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during cache cleanup: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found or expired
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                return None

            logger.debug(f"Cache hit for key: {key}")
            return entry.value

    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live for the cached value

        Returns:
            True if successful, False otherwise
        """
        try:
            async with self._lock:
                expires_at = None
                if ttl is not None:
                    expires_at = datetime.utcnow() + ttl
                elif self.default_ttl is not None:
                    expires_at = datetime.utcnow() + self.default_ttl

                # Serialize complex objects to JSON to simulate Redis behavior
                serialized_value = self._serialize_value(value)

                self._cache[key] = CacheEntry(
                    value=serialized_value, expires_at=expires_at
                )

                logger.debug(f"Cache set for key: {key} (TTL: {ttl})")
                return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        try:
            async with self._lock:
                if key in self._cache:
                    del self._cache[key]
                    logger.debug(f"Cache deleted for key: {key}")
                    return True
                return False
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists, False otherwise
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return False

            if entry.is_expired():
                del self._cache[key]
                return False

            return True

    async def clear(self) -> bool:
        """
        Clear all cached values.

        Returns:
            True if successful, False otherwise
        """
        try:
            async with self._lock:
                self._cache.clear()
                logger.debug("Cache cleared")
                return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Get remaining time to live for a key.

        Args:
            key: Cache key

        Returns:
            Remaining TTL in seconds, None if key doesn't exist or no TTL
        """
        async with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self._cache[key]
                return None

            return entry.get_ttl_seconds()

    def _serialize_value(self, value: Any) -> Any:
        """
        Serialize value to simulate Redis JSON serialization.

        Args:
            value: Value to serialize

        Returns:
            Serialized value
        """
        try:
            if isinstance(value, (str, int, float, bool, type(None))):
                return value

            # For complex objects, serialize to JSON and back to simulate Redis
            json_str = json.dumps(value, default=str)
            return json.loads(json_str)
        except Exception as e:
            logger.warning(f"Failed to serialize cache value: {e}")
            return value

    async def close(self):
        """Close the cache service and cleanup resources."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self._cache)
        expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())

        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "cache_type": "memory",
        }
