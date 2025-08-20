"""
File: carrier_verification_service.py
Description: Carrier verification service with FMCSA API integration and fallback logic
Author: HappyRobot Team
Created: 2024-11-15
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from src.core.ports.services.fmcsa_service import FMCSAServicePort
from src.core.ports.repositories.carrier_repository import ICarrierRepository
from src.core.domain.value_objects import MCNumber
from src.infrastructure.caching.fmcsa_cache import FMCSACacheService
from src.infrastructure.external_services.fmcsa.exceptions import (
    FMCSATimeoutError,
    FMCSAAuthenticationError,
    FMCSARateLimitError,
    FMCSAServiceUnavailableError,
)

logger = logging.getLogger(__name__)


class CarrierVerificationService:
    """
    Service for carrier verification with FMCSA API integration.

    Implements a multi-tier verification strategy:
    1. Check cache for recent data
    2. Call FMCSA API if cache miss or expired
    3. Fallback to database if API fails
    4. Cache successful API responses
    """

    def __init__(
        self,
        fmcsa_service: FMCSAServicePort,
        carrier_repository: ICarrierRepository,
        cache_service: FMCSACacheService,
        enable_cache: bool = True,
        database_fallback_max_age_days: int = 7,
    ):
        """
        Initialize carrier verification service.

        Args:
            fmcsa_service: FMCSA API service
            carrier_repository: Carrier repository for database fallback
            cache_service: Cache service for FMCSA data
            enable_cache: Whether to use caching
            database_fallback_max_age_days: Max age for database fallback data
        """
        self.fmcsa_service = fmcsa_service
        self.carrier_repository = carrier_repository
        self.cache_service = cache_service
        self.enable_cache = enable_cache
        self.database_fallback_max_age_days = database_fallback_max_age_days

    async def verify_carrier(
        self,
        mc_number: str
    ) -> Dict[str, Any]:
        """
        Verify carrier with multi-tier strategy.

        Args:
            mc_number: Motor Carrier number

        Returns:
            Carrier verification result with source indication
        """
        # Clean MC number
        clean_mc = ''.join(filter(str.isdigit, mc_number))

        if not clean_mc:
            return self._create_error_response(
                mc_number,
                "Invalid MC number format",
                "The provided MC number contains no digits"
            )

        logger.info(f"Starting carrier verification for MC {clean_mc}")

        # Step 1: Check cache if enabled
        if self.enable_cache:
            cached_result = await self._get_from_cache(clean_mc)
            if cached_result:
                logger.info(f"Returning cached data for MC {clean_mc}")
                return cached_result

        # Step 2: Try FMCSA API
        api_result = await self._get_from_api(clean_mc)
        if api_result:
            logger.info(f"Successfully retrieved data from FMCSA API for MC {clean_mc}")

            # Cache successful API response
            if self.enable_cache:
                await self._cache_api_response(clean_mc, api_result)

            return api_result

        # Step 3: Fallback to database
        db_result = await self._get_from_database(clean_mc)
        if db_result:
            logger.info(f"Using database fallback for MC {clean_mc}")
            return db_result

        # Step 4: No data found anywhere
        return self._create_not_found_response(clean_mc)

    async def get_carrier_snapshot(self, mc_number: str) -> Dict[str, Any]:
        """
        Get comprehensive carrier snapshot.

        Args:
            mc_number: Motor Carrier number

        Returns:
            Complete carrier snapshot with all available data
        """
        clean_mc = ''.join(filter(str.isdigit, mc_number))

        if not clean_mc:
            return self._create_error_response(
                mc_number,
                "Invalid MC number format",
                "The provided MC number contains no digits"
            )

        logger.info(f"Getting carrier snapshot for MC {clean_mc}")

        # Check cache for full snapshot
        if self.enable_cache:
            cached_snapshot = await self.cache_service.get_full_snapshot(clean_mc)
            if cached_snapshot:
                logger.info(f"Returning cached snapshot for MC {clean_mc}")
                cached_snapshot["cached"] = True
                return cached_snapshot

        # Get full data from API
        try:
            api_data = await self.fmcsa_service.get_carrier_snapshot(clean_mc)
            if api_data:
                result = {
                    "mc_number": clean_mc,
                    "eligible": True,
                    "carrier_info": api_data.get("snapshot", {}).get("carrier_info"),
                    "safety_score": api_data.get("snapshot", {}).get("safety_scores"),
                    "insurance_info": api_data.get("snapshot", {}).get("insurance_info"),
                    "verification_source": "FMCSA_API",
                    "cached": False,
                    "verification_timestamp": datetime.utcnow().isoformat(),
                    "reason": "Complete carrier snapshot retrieved",
                    "details": "All available data from FMCSA API"
                }

                # Cache the snapshot
                if self.enable_cache:
                    await self.cache_service.set_full_snapshot(clean_mc, result)

                return result

        except Exception as e:
            logger.error(f"Error getting carrier snapshot from API: {e}")

        # Fallback to database
        db_result = await self._get_from_database(clean_mc)
        if db_result:
            return db_result

        # Return not found response
        return self._create_not_found_response(clean_mc)

    async def check_service_health(self) -> Dict[str, Any]:
        """
        Check health of all verification services.

        Returns:
            Health status of FMCSA API, cache, and database
        """
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "healthy",
            "services": {}
        }

        # Check FMCSA API health
        try:
            fmcsa_healthy = await self.fmcsa_service.health_check()
            health_status["services"]["fmcsa_api"] = {
                "status": "healthy" if fmcsa_healthy else "unhealthy",
                "available": fmcsa_healthy
            }
        except Exception as e:
            health_status["services"]["fmcsa_api"] = {
                "status": "error",
                "available": False,
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"

        # Check cache health (if enabled)
        if self.enable_cache:
            try:
                # Simple cache health check
                test_key = "health_check_test"
                await self.cache_service.cache_service.set(test_key, "test", timedelta(seconds=1))
                cache_test = await self.cache_service.cache_service.get(test_key)
                await self.cache_service.cache_service.delete(test_key)

                health_status["services"]["cache"] = {
                    "status": "healthy" if cache_test == "test" else "unhealthy",
                    "available": cache_test == "test"
                }
            except Exception as e:
                health_status["services"]["cache"] = {
                    "status": "error",
                    "available": False,
                    "error": str(e)
                }

        # Check database health
        try:
            # Simple database health check - test database connectivity
            # Use a harmless query to check if database is accessible
            from sqlalchemy import text
            await self.carrier_repository.session.execute(text("SELECT 1"))
            health_status["services"]["database"] = {
                "status": "healthy",
                "available": True
            }
        except Exception as e:
            health_status["services"]["database"] = {
                "status": "error",
                "available": False,
                "error": str(e)
            }
            if health_status["overall_status"] == "healthy":
                health_status["overall_status"] = "degraded"

        return health_status

    async def invalidate_carrier_cache(self, mc_number: str) -> bool:
        """
        Invalidate cached data for a carrier.

        Args:
            mc_number: Motor Carrier number

        Returns:
            True if successful, False otherwise
        """
        if not self.enable_cache:
            return True

        clean_mc = ''.join(filter(str.isdigit, mc_number))
        return await self.cache_service.invalidate_carrier(clean_mc)

    async def _get_from_cache(
        self,
        mc_number: str
    ) -> Optional[Dict[str, Any]]:
        """Get carrier data from cache."""
        try:
            cached_data = await self.cache_service.get_carrier_data(mc_number)
            if cached_data:
                cached_data["verification_source"] = "CACHE"
                return cached_data

        except Exception as e:
            logger.warning(f"Error retrieving from cache for MC {mc_number}: {e}")

        return None

    async def _get_from_api(
        self,
        mc_number: str
    ) -> Optional[Dict[str, Any]]:
        """Get carrier data from FMCSA API."""
        try:
            api_data = await self.fmcsa_service.verify_carrier(
                mc_number
            )

            if api_data:
                return {
                    "mc_number": mc_number,
                    "eligible": True,
                    "carrier_info": api_data.get("carrier_info"),
                    "insurance_info": api_data.get("insurance_info"),
                    "verification_source": "FMCSA_API",
                    "cached": False,
                    "verification_timestamp": datetime.utcnow().isoformat(),
                    "reason": "Valid and active carrier",
                    "details": "Verification completed successfully via FMCSA API"
                }

        except FMCSAAuthenticationError as e:
            logger.error(f"FMCSA authentication error for MC {mc_number}: {e}")
            # Don't fallback for auth errors - this needs to be fixed
            raise

        except FMCSARateLimitError as e:
            logger.warning(f"FMCSA rate limit exceeded for MC {mc_number}: {e}")
            # Continue to fallback for rate limits

        except (FMCSATimeoutError, FMCSAServiceUnavailableError) as e:
            logger.warning(f"FMCSA service unavailable for MC {mc_number}: {e}")
            # Continue to fallback for service issues

        except Exception as e:
            logger.error(f"Unexpected error calling FMCSA API for MC {mc_number}: {e}")
            # Continue to fallback for unexpected errors

        return None

    async def _get_from_database(
        self,
        mc_number: str
    ) -> Optional[Dict[str, Any]]:
        """Get carrier data from database as fallback."""
        try:
            mc_number_obj = MCNumber.from_string(mc_number)
            carrier = await self.carrier_repository.get_by_mc_number(mc_number_obj)

            if carrier:
                # Check if data is too old for fallback
                if carrier.updated_at:
                    age_days = (datetime.utcnow() - carrier.updated_at).days
                    if age_days > self.database_fallback_max_age_days:
                        logger.warning(
                            f"Database data for MC {mc_number} is {age_days} days old, "
                            f"exceeds max age of {self.database_fallback_max_age_days} days"
                        )

                warning_msg = (
                    f"FMCSA API unavailable, using database data from "
                    f"{carrier.updated_at.strftime('%Y-%m-%d') if carrier.updated_at else 'unknown date'}"
                )

                return {
                    "mc_number": mc_number,
                    "eligible": carrier.is_eligible,
                    "carrier_info": {
                        "legal_name": carrier.legal_name,
                        "dba_name": carrier.dba_name or carrier.legal_name,
                        "physical_address": (
                            f"{carrier.address.city}, {carrier.address.state}"
                            if carrier.address else "Address not available"
                        ),
                        "phone": (
                            carrier.primary_contact.get('phone', 'Phone not available')
                            if carrier.primary_contact else "Phone not available"
                        ),
                        "entity_type": carrier.entity_type,
                        "operating_status": carrier.operating_status,
                        "out_of_service_date": None,
                        "mcs_150_date": carrier.last_verified_at.strftime('%Y-%m-%d') if carrier.last_verified_at else None,
                        "mcs_150_mileage": None
                    },
                    "verification_source": "DATABASE_FALLBACK",
                    "cached": False,
                    "verification_timestamp": datetime.utcnow().isoformat(),
                    "warning": warning_msg,
                    "reason": "Valid and active carrier" if carrier.is_eligible else "Carrier eligibility check failed",
                    "details": "Retrieved from database fallback due to FMCSA API unavailability"
                }

        except Exception as e:
            logger.error(f"Error retrieving from database for MC {mc_number}: {e}")

        return None

    async def _cache_api_response(self, mc_number: str, response_data: Dict[str, Any]):
        """Cache successful API response."""
        try:
            # Cache main carrier data
            await self.cache_service.set_carrier_data(mc_number, response_data)

            # Cache insurance data separately if available
            if response_data.get("insurance_info"):
                await self.cache_service.set_insurance_data(
                    mc_number,
                    response_data["insurance_info"]
                )

        except Exception as e:
            logger.error(f"Error caching API response for MC {mc_number}: {e}")

    def _create_error_response(
        self,
        mc_number: str,
        reason: str,
        details: str
    ) -> Dict[str, Any]:
        """Create error response."""
        return {
            "mc_number": mc_number,
            "eligible": False,
            "carrier_info": None,
            "verification_source": "VALIDATION_ERROR",
            "cached": False,
            "verification_timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "details": details
        }

    def _create_not_found_response(self, mc_number: str) -> Dict[str, Any]:
        """Create not found response."""
        return {
            "mc_number": mc_number,
            "eligible": False,
            "carrier_info": None,
            "verification_source": "NOT_FOUND",
            "cached": False,
            "verification_timestamp": datetime.utcnow().isoformat(),
            "reason": "MC number not found",
            "details": (
                "The provided MC number was not found in FMCSA records or local database. "
                "Please ensure carrier is registered and active."
            )
        }
