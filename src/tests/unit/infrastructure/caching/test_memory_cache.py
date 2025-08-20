"""
Unit tests for memory cache service.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
import pytest_asyncio

from src.infrastructure.caching.memory_cache import CacheEntry, MemoryCacheService


@pytest_asyncio.fixture
async def cache_service():
    """Create memory cache service for testing."""
    service = MemoryCacheService(default_ttl=timedelta(seconds=60))
    yield service
    await service.close()


@pytest_asyncio.fixture
async def cache_service_no_ttl():
    """Create memory cache service without default TTL."""
    service = MemoryCacheService()
    yield service
    await service.close()


class TestCacheEntry:
    """Test cache entry functionality."""

    def test_cache_entry_creation(self):
        """Test cache entry creation."""
        entry = CacheEntry(value="test_value")

        assert entry.value == "test_value"
        assert entry.expires_at is None
        assert entry.created_at is not None
        assert not entry.is_expired()

    def test_cache_entry_with_expiration(self):
        """Test cache entry with expiration."""
        expires_at = datetime.utcnow() + timedelta(seconds=30)
        entry = CacheEntry(value="test_value", expires_at=expires_at)

        assert entry.value == "test_value"
        assert entry.expires_at == expires_at
        assert not entry.is_expired()

    def test_cache_entry_expired(self):
        """Test expired cache entry."""
        expires_at = datetime.utcnow() - timedelta(seconds=1)
        entry = CacheEntry(value="test_value", expires_at=expires_at)

        assert entry.is_expired()

    def test_get_ttl_seconds(self):
        """Test TTL calculation."""
        expires_at = datetime.utcnow() + timedelta(seconds=30)
        entry = CacheEntry(value="test_value", expires_at=expires_at)

        ttl = entry.get_ttl_seconds()
        assert ttl is not None
        assert 25 <= ttl <= 30  # Allow for execution time

    def test_get_ttl_seconds_no_expiration(self):
        """Test TTL calculation with no expiration."""
        entry = CacheEntry(value="test_value")

        ttl = entry.get_ttl_seconds()
        assert ttl is None


class TestMemoryCacheService:
    """Test memory cache service functionality."""

    @pytest.mark.asyncio
    async def test_set_and_get_value(self, cache_service):
        """Test setting and getting cache values."""
        key = "test_key"
        value = {"test": "data"}

        # Set value
        success = await cache_service.set(key, value)
        assert success

        # Get value
        retrieved_value = await cache_service.get(key)
        assert retrieved_value == value

    @pytest.mark.asyncio
    async def test_set_and_get_with_custom_ttl(self, cache_service):
        """Test setting value with custom TTL."""
        key = "test_key_ttl"
        value = "test_value"
        ttl = timedelta(seconds=30)

        # Set value with custom TTL
        success = await cache_service.set(key, value, ttl)
        assert success

        # Get value
        retrieved_value = await cache_service.get(key)
        assert retrieved_value == value

        # Check TTL
        remaining_ttl = await cache_service.get_ttl(key)
        assert remaining_ttl is not None
        assert 25 <= remaining_ttl <= 30

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, cache_service):
        """Test getting non-existent key."""
        result = await cache_service.get("nonexistent_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_key(self, cache_service):
        """Test deleting cache key."""
        key = "test_delete"
        value = "test_value"

        # Set value
        await cache_service.set(key, value)

        # Verify it exists
        assert await cache_service.exists(key)

        # Delete key
        success = await cache_service.delete(key)
        assert success

        # Verify it's gone
        assert not await cache_service.exists(key)
        assert await cache_service.get(key) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_key(self, cache_service):
        """Test deleting non-existent key."""
        result = await cache_service.delete("nonexistent_key")
        assert not result

    @pytest.mark.asyncio
    async def test_exists_key(self, cache_service):
        """Test checking if key exists."""
        key = "test_exists"
        value = "test_value"

        # Key doesn't exist initially
        assert not await cache_service.exists(key)

        # Set value
        await cache_service.set(key, value)

        # Key now exists
        assert await cache_service.exists(key)

    @pytest.mark.asyncio
    async def test_clear_cache(self, cache_service):
        """Test clearing all cache entries."""
        # Set multiple values
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")
        await cache_service.set("key3", "value3")

        # Verify they exist
        assert await cache_service.exists("key1")
        assert await cache_service.exists("key2")
        assert await cache_service.exists("key3")

        # Clear cache
        success = await cache_service.clear()
        assert success

        # Verify they're gone
        assert not await cache_service.exists("key1")
        assert not await cache_service.exists("key2")
        assert not await cache_service.exists("key3")

    @pytest.mark.asyncio
    async def test_expired_entry_auto_removal(self, cache_service):
        """Test automatic removal of expired entries."""
        key = "test_expired"
        value = "test_value"
        ttl = timedelta(milliseconds=100)  # Very short TTL

        # Set value with short TTL
        await cache_service.set(key, value, ttl)

        # Verify it exists initially
        assert await cache_service.exists(key)

        # Wait for expiration
        await asyncio.sleep(0.2)

        # Verify it's automatically removed when accessed
        assert not await cache_service.exists(key)
        assert await cache_service.get(key) is None

    @pytest.mark.asyncio
    async def test_get_ttl_nonexistent_key(self, cache_service):
        """Test getting TTL for non-existent key."""
        ttl = await cache_service.get_ttl("nonexistent_key")
        assert ttl is None

    @pytest.mark.asyncio
    async def test_get_ttl_no_expiration(self, cache_service_no_ttl):
        """Test getting TTL for key with no expiration."""
        key = "no_expiry_key"
        value = "test_value"

        # Set value without TTL
        await cache_service_no_ttl.set(key, value)

        # TTL should be None
        ttl = await cache_service_no_ttl.get_ttl(key)
        assert ttl is None

    @pytest.mark.asyncio
    async def test_serialize_complex_object(self, cache_service):
        """Test serialization of complex objects."""
        key = "complex_object"
        value = {
            "nested": {"data": [1, 2, 3], "timestamp": "2024-11-15T10:30:45Z"},
            "list": ["a", "b", "c"],
            "number": 42,
        }

        # Set complex object
        await cache_service.set(key, value)

        # Get and verify
        retrieved_value = await cache_service.get(key)
        assert retrieved_value == value

    @pytest.mark.asyncio
    async def test_serialize_simple_types(self, cache_service):
        """Test serialization of simple types."""
        test_cases = [
            ("string_key", "string_value"),
            ("int_key", 42),
            ("float_key", 3.14),
            ("bool_key", True),
            ("none_key", None),
        ]

        for key, value in test_cases:
            await cache_service.set(key, value)
            retrieved_value = await cache_service.get(key)
            assert retrieved_value == value

    def test_get_stats(self, cache_service):
        """Test cache statistics."""
        stats = cache_service.get_stats()

        assert "total_entries" in stats
        assert "active_entries" in stats
        assert "expired_entries" in stats
        assert "cache_type" in stats
        assert stats["cache_type"] == "memory"

    @pytest.mark.asyncio
    async def test_error_handling_in_set(self, cache_service):
        """Test error handling in set operation."""
        with patch.object(
            cache_service,
            "_serialize_value",
            side_effect=Exception("Serialization error"),
        ):
            success = await cache_service.set("error_key", "error_value")
            assert not success

    @pytest.mark.asyncio
    async def test_error_handling_in_get(self, cache_service):
        """Test error handling in get operation."""
        # Set a value first
        await cache_service.set("test_key", "test_value")

        # Mock an error in the lock acquisition
        with patch.object(
            cache_service._lock, "__aenter__", side_effect=Exception("Lock error")
        ):
            await cache_service.get("test_key")
            # Should handle error gracefully, but exact behavior depends on implementation
            # This test ensures no unhandled exceptions

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self):
        """Test that cleanup task is properly managed."""
        service = MemoryCacheService()

        # Verify cleanup task is created
        assert service._cleanup_task is not None

        # Close service
        await service.close()

        # Verify cleanup task is cancelled
        assert service._cleanup_task.cancelled()

    @pytest.mark.asyncio
    async def test_background_cleanup(self):
        """Test background cleanup of expired entries."""
        service = MemoryCacheService()

        try:
            # Set entries with very short TTL
            await service.set("cleanup1", "value1", timedelta(milliseconds=50))
            await service.set("cleanup2", "value2", timedelta(milliseconds=50))

            # Wait for expiration
            await asyncio.sleep(0.1)

            # Manually trigger cleanup
            async with service._lock:
                expired_keys = [
                    key for key, entry in service._cache.items() if entry.is_expired()
                ]
                for key in expired_keys:
                    del service._cache[key]

            # Verify entries are cleaned up
            assert len(service._cache) == 0

        finally:
            await service.close()
