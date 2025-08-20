"""
File: fmcsa_cache.py
Description: FMCSA-specific caching service with intelligent key management
Author: HappyRobot Team
Created: 2024-11-15
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.core.ports.services.cache_service import CacheServicePort

logger = logging.getLogger(__name__)


class FMCSACacheService:
    """FMCSA-specific caching service with intelligent key management."""

    def __init__(self, cache_service: CacheServicePort, default_ttl: timedelta):
        """
        Initialize FMCSA cache service.

        Args:
            cache_service: Underlying cache service implementation
            default_ttl: Default time to live for FMCSA data
        """
        self.cache_service = cache_service
        self.default_ttl = default_ttl

    def _get_carrier_key(self, mc_number: str) -> str:
        """Generate cache key for carrier data."""
        return f"fmcsa:carrier:{mc_number}"

    def _get_safety_key(self, mc_number: str) -> str:
        """Generate cache key for safety scores."""
        return f"fmcsa:safety:{mc_number}"

    def _get_insurance_key(self, mc_number: str) -> str:
        """Generate cache key for insurance data."""
        return f"fmcsa:insurance:{mc_number}"

    def _get_snapshot_key(self, mc_number: str) -> str:
        """Generate cache key for full carrier snapshot."""
        return f"fmcsa:snapshot:{mc_number}"

    async def get_carrier_data(self, mc_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached carrier data.

        Args:
            mc_number: Motor Carrier number

        Returns:
            Cached carrier data or None if not found
        """
        try:
            key = self._get_carrier_key(mc_number)
            data = await self.cache_service.get(key)

            if data:
                logger.debug(f"Cache hit for carrier {mc_number}")
                # Add cache metadata
                data["cached"] = True
                data["cache_key"] = key

            return data
        except Exception as e:
            logger.error(f"Error retrieving cached carrier data for {mc_number}: {e}")
            return None

    async def set_carrier_data(
        self,
        mc_number: str,
        data: Dict[str, Any],
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        Cache carrier data.

        Args:
            mc_number: Motor Carrier number
            data: Carrier data to cache
            ttl: Custom TTL, uses default if None

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._get_carrier_key(mc_number)
            cache_ttl = ttl or self.default_ttl

            # Add cache metadata
            cache_data = data.copy()
            cache_data.update({
                "cached_at": datetime.utcnow().isoformat(),
                "cache_ttl_seconds": int(cache_ttl.total_seconds()),
                "cache_source": "fmcsa_api"
            })

            success = await self.cache_service.set(key, cache_data, cache_ttl)

            if success:
                logger.debug(f"Cached carrier data for {mc_number} (TTL: {cache_ttl})")

            return success
        except Exception as e:
            logger.error(f"Error caching carrier data for {mc_number}: {e}")
            return False

    async def get_safety_scores(self, mc_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached safety scores.

        Args:
            mc_number: Motor Carrier number

        Returns:
            Cached safety scores or None if not found
        """
        try:
            key = self._get_safety_key(mc_number)
            data = await self.cache_service.get(key)

            if data:
                logger.debug(f"Cache hit for safety scores {mc_number}")

            return data
        except Exception as e:
            logger.error(f"Error retrieving cached safety scores for {mc_number}: {e}")
            return None

    async def set_safety_scores(
        self,
        mc_number: str,
        data: Dict[str, Any],
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        Cache safety scores.

        Args:
            mc_number: Motor Carrier number
            data: Safety scores to cache
            ttl: Custom TTL, uses default if None

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._get_safety_key(mc_number)
            cache_ttl = ttl or self.default_ttl

            # Add cache metadata
            cache_data = data.copy()
            cache_data.update({
                "cached_at": datetime.utcnow().isoformat(),
                "cache_ttl_seconds": int(cache_ttl.total_seconds())
            })

            success = await self.cache_service.set(key, cache_data, cache_ttl)

            if success:
                logger.debug(f"Cached safety scores for {mc_number}")

            return success
        except Exception as e:
            logger.error(f"Error caching safety scores for {mc_number}: {e}")
            return False

    async def get_insurance_data(self, mc_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached insurance data.

        Args:
            mc_number: Motor Carrier number

        Returns:
            Cached insurance data or None if not found
        """
        try:
            key = self._get_insurance_key(mc_number)
            data = await self.cache_service.get(key)

            if data:
                logger.debug(f"Cache hit for insurance data {mc_number}")

            return data
        except Exception as e:
            logger.error(f"Error retrieving cached insurance data for {mc_number}: {e}")
            return None

    async def set_insurance_data(
        self,
        mc_number: str,
        data: Dict[str, Any],
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        Cache insurance data.

        Args:
            mc_number: Motor Carrier number
            data: Insurance data to cache
            ttl: Custom TTL, uses default if None

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._get_insurance_key(mc_number)
            cache_ttl = ttl or self.default_ttl

            # Add cache metadata
            cache_data = data.copy()
            cache_data.update({
                "cached_at": datetime.utcnow().isoformat(),
                "cache_ttl_seconds": int(cache_ttl.total_seconds())
            })

            success = await self.cache_service.set(key, cache_data, cache_ttl)

            if success:
                logger.debug(f"Cached insurance data for {mc_number}")

            return success
        except Exception as e:
            logger.error(f"Error caching insurance data for {mc_number}: {e}")
            return False

    async def get_full_snapshot(self, mc_number: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached full carrier snapshot.

        Args:
            mc_number: Motor Carrier number

        Returns:
            Cached full snapshot or None if not found
        """
        try:
            key = self._get_snapshot_key(mc_number)
            data = await self.cache_service.get(key)

            if data:
                logger.debug(f"Cache hit for full snapshot {mc_number}")

            return data
        except Exception as e:
            logger.error(f"Error retrieving cached snapshot for {mc_number}: {e}")
            return None

    async def set_full_snapshot(
        self,
        mc_number: str,
        data: Dict[str, Any],
        ttl: Optional[timedelta] = None
    ) -> bool:
        """
        Cache full carrier snapshot.

        Args:
            mc_number: Motor Carrier number
            data: Full snapshot data to cache
            ttl: Custom TTL, uses default if None

        Returns:
            True if successful, False otherwise
        """
        try:
            key = self._get_snapshot_key(mc_number)
            cache_ttl = ttl or self.default_ttl

            # Add cache metadata
            cache_data = data.copy()
            cache_data.update({
                "cached_at": datetime.utcnow().isoformat(),
                "cache_ttl_seconds": int(cache_ttl.total_seconds()),
                "cache_type": "full_snapshot"
            })

            success = await self.cache_service.set(key, cache_data, cache_ttl)

            if success:
                logger.debug(f"Cached full snapshot for {mc_number}")

            return success
        except Exception as e:
            logger.error(f"Error caching full snapshot for {mc_number}: {e}")
            return False

    async def invalidate_carrier(self, mc_number: str) -> bool:
        """
        Invalidate all cached data for a carrier.

        Args:
            mc_number: Motor Carrier number

        Returns:
            True if successful, False otherwise
        """
        try:
            keys = [
                self._get_carrier_key(mc_number),
                self._get_safety_key(mc_number),
                self._get_insurance_key(mc_number),
                self._get_snapshot_key(mc_number),
            ]

            success = True
            for key in keys:
                if not await self.cache_service.delete(key):
                    success = False

            if success:
                logger.debug(f"Invalidated all cache entries for carrier {mc_number}")

            return success
        except Exception as e:
            logger.error(f"Error invalidating cache for carrier {mc_number}: {e}")
            return False

    async def check_cache_freshness(self, mc_number: str) -> Dict[str, Any]:
        """
        Check cache freshness for all carrier data types.

        Args:
            mc_number: Motor Carrier number

        Returns:
            Dict with cache status for each data type
        """
        result = {
            "mc_number": mc_number,
            "cache_status": {}
        }

        data_types = [
            ("carrier", self._get_carrier_key(mc_number)),
            ("safety", self._get_safety_key(mc_number)),
            ("insurance", self._get_insurance_key(mc_number)),
            ("snapshot", self._get_snapshot_key(mc_number)),
        ]

        for data_type, key in data_types:
            try:
                exists = await self.cache_service.exists(key)
                ttl = await self.cache_service.get_ttl(key) if exists else None

                result["cache_status"][data_type] = {
                    "cached": exists,
                    "ttl_seconds": ttl,
                    "expires_in": f"{ttl}s" if ttl else None
                }
            except Exception as e:
                logger.error(f"Error checking cache status for {data_type}: {e}")
                result["cache_status"][data_type] = {
                    "cached": False,
                    "error": str(e)
                }

        return result
