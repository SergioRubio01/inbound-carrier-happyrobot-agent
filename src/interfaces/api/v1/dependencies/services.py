"""
File: services.py
Description: Service dependency injection for API endpoints
Author: HappyRobot Team
Created: 2024-11-15
"""

from datetime import timedelta
from functools import lru_cache

from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import settings
from src.infrastructure.external_services.fmcsa.client import FMCSAAPIClient
from src.infrastructure.database.postgres import PostgresCarrierRepository
from src.infrastructure.caching.memory_cache import MemoryCacheService
from src.infrastructure.caching.fmcsa_cache import FMCSACacheService
from src.core.application.services.carrier_verification_service import CarrierVerificationService


@lru_cache()
def get_fmcsa_api_client() -> FMCSAAPIClient:
    """
    Get FMCSA API client singleton.

    Returns:
        Configured FMCSA API client
    """
    return FMCSAAPIClient(
        api_key=settings.fmcsa_api_key,
        base_url=settings.fmcsa_api_base_url,
        timeout=settings.fmcsa_api_timeout,
        max_retries=settings.fmcsa_max_retries,
        backoff_factor=settings.fmcsa_backoff_factor,
    )


@lru_cache()
def get_cache_service() -> MemoryCacheService:
    """
    Get cache service singleton.

    Returns:
        Configured cache service
    """
    default_ttl = timedelta(seconds=settings.fmcsa_cache_ttl)
    return MemoryCacheService(default_ttl=default_ttl)


@lru_cache()
def get_fmcsa_cache_service() -> FMCSACacheService:
    """
    Get FMCSA cache service singleton.

    Returns:
        Configured FMCSA cache service
    """
    cache_service = get_cache_service()
    default_ttl = timedelta(seconds=settings.fmcsa_cache_ttl)
    return FMCSACacheService(cache_service, default_ttl)


def create_carrier_verification_service(session: AsyncSession) -> CarrierVerificationService:
    """
    Create carrier verification service with all dependencies.

    Args:
        session: Database session

    Returns:
        Configured carrier verification service
    """
    fmcsa_client = get_fmcsa_api_client()
    carrier_repository = PostgresCarrierRepository(session)
    fmcsa_cache = get_fmcsa_cache_service()

    return CarrierVerificationService(
        fmcsa_service=fmcsa_client,
        carrier_repository=carrier_repository,
        cache_service=fmcsa_cache,
        enable_cache=settings.fmcsa_enable_cache,
        database_fallback_max_age_days=7,
    )
