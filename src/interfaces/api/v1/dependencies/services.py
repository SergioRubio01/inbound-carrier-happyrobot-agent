"""
File: services.py
Description: Service dependency injection for API endpoints
Author: HappyRobot Team
Created: 2024-11-15
"""

from datetime import timedelta
from functools import lru_cache

from src.infrastructure.caching.memory_cache import MemoryCacheService


@lru_cache()
def get_cache_service() -> MemoryCacheService:
    """
    Get cache service singleton.

    Returns:
        Configured cache service
    """
    default_ttl = timedelta(minutes=30)  # Default 30 minute cache
    return MemoryCacheService(default_ttl=default_ttl)
