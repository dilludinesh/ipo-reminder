"""Tests for the cache module."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta

class TestCacheManager:
    """Test cases for the CacheManager class."""
    
    @pytest.mark.asyncio
    async def test_initialize(self, mock_cache):
        """Test cache initialization."""
        cache_manager = mock_cache.return_value
        cache_manager.redis = AsyncMock()
        cache_manager.redis.ping.return_value = True
        
        await cache_manager.initialize()
        
        assert cache_manager.is_available is True
        cache_manager.redis.ping.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_set_get(self, mock_cache):
        """Test setting and getting cache values."""
        cache_manager = mock_cache.return_value
        cache_manager.redis = AsyncMock()
        cache_manager.is_available = True
        
        # Test successful set and get
        await cache_manager.set("test_key", "test_value", 300)
        cache_manager.redis.set.assert_awaited_once_with("test_key", "test_value", ex=300)
        
        # Test successful get
        cache_manager.redis.get.return_value = "test_value"
        value = await cache_manager.get("test_key")
        assert value == "test_value"
        cache_manager.redis.get.assert_awaited_once_with("test_key")
        
        # Test get with default
        cache_manager.redis.get.return_value = None
        value = await cache_manager.get("nonexistent_key", default="default")
        assert value == "default"
        
    @pytest.mark.asyncio
    async def test_cache_fallback(self, mock_cache):
        """Test cache fallback to memory when Redis is unavailable."""
        cache_manager = mock_cache.return_value
        cache_manager.is_available = False
        
        # Set value in memory cache
        await cache_manager.set("test_key", "test_value", 300)
        
        # Get value from memory cache
        value = await cache_manager.get("test_key")
        assert value == "test_value"
        
        # Test expiration
        cache_manager._memory_cache["test_key"] = ("test_value", datetime.now() - timedelta(seconds=600))
        value = await cache_manager.get("test_key")
        assert value is None
        
    @pytest.mark.asyncio
    async def test_delete(self, mock_cache):
        """Test deleting cache values."""
        cache_manager = mock_cache.return_value
        cache_manager.redis = AsyncMock()
        cache_manager.is_available = True
        
        await cache_manager.delete("test_key")
        cache_manager.redis.delete.assert_awaited_once_with("test_key")
        
    @pytest.mark.asyncio
    async def test_clear(self, mock_cache):
        """Test clearing the cache."""
        cache_manager = mock_cache.return_value
        cache_manager.redis = AsyncMock()
        cache_manager.is_available = True
        
        await cache_manager.clear()
        cache_manager.redis.flushdb.assert_awaited_once()
        
    @pytest.mark.asyncio
    async def test_cache_serialization(self, mock_cache):
        """Test JSON serialization/deserialization of cache values."""
        cache_manager = mock_cache.return_value
        cache_manager.redis = AsyncMock()
        cache_manager.is_available = True
        
        test_data = {"key": "value", "nested": {"a": 1, "b": [1, 2, 3]}}
        
        # Test set with complex object
        await cache_manager.set("complex_key", test_data, 300)
        cache_manager.redis.set.assert_awaited_once_with("complex_key", '{"key": "value", "nested": {"a": 1, "b": [1, 2, 3]}}', ex=300)
        
        # Test get with complex object
        cache_manager.redis.get.return_value = '{"key": "value", "nested": {"a": 1, "b": [1, 2, 3]}}'
        value = await cache_manager.get("complex_key")
        assert value == test_data
